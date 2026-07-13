"""Streamlit dashboard for political careers, patronage and justice cases."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import _competition_tab
from football_republic.campaign import Strategy
from football_republic.coalition_webapp import (
    _agreements_tab,
    _election_tab,
    _header,
)
from football_republic.constitutional_webapp import (
    _cabinet_tab,
    _constitutional_tab,
)
from football_republic.generational_webapp import (
    _commercial_tab,
    _insolvency_tab,
    _lifecycle_tab,
)
from football_republic.history_webapp import (
    _clubs_tab,
    _decision,
    _mandates_tab,
    _players_tab,
    _seasons_tab,
)
from football_republic.patronage_runtime import CareerJusticeHistory
from football_republic.political_webapp import (
    _congress_tab,
    _stakeholders_tab,
)
from football_republic.pyramid_webapp import (
    _css,
    _events_tab,
    _finance_tab,
    _owners_tab,
    _pyramid_tab,
    _squad_tab,
)


def _session() -> CareerJusticeHistory:
    if "career_justice_history" not in st.session_state:
        st.session_state.career_justice_history = CareerJusticeHistory(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.career_justice_history


def _rerun() -> None:
    st.rerun()


def _sidebar(history: CareerJusticeHistory) -> None:
    with st.sidebar:
        st.markdown("## 国家足球人物史")
        st.caption("官员会流动、关系会暴露、案件会起诉和申诉。")
        st.metric("全球月份", str(history.global_month))
        st.metric("当前年份", f"第{history.global_year}年")
        st.metric("制度任期", f"第{history.term_index}届 · M{history.local_month}")
        status = (
            "选举大会"
            if history.election_active
            else "看守政府"
            if history.caretaker_active
            else "正式政府"
        )
        st.markdown(
            f"**主席：{history.current_president.name}**  \n"
            f"状态：{status}  \n"
            f"路线：{history.current_president.strategy.value}"
        )
        st.metric("司法独立", f"{history.justice_independence:.0%}")
        st.metric("未披露网络", f"{history.undisclosed_network_strength:.2f}")
        st.metric("活跃案件", str(len(history.active_cases)))

        if not history.finished:
            left, right = st.columns(2)
            if left.button("推进1月", use_container_width=True):
                history.advance(1, interactive=True)
                _rerun()
            if right.button("推进至决策", use_container_width=True):
                history.advance(24, interactive=True)
                _rerun()
            if st.button("完成本届制度任期", use_container_width=True):
                history.finish_current_term()
                _rerun()
            if st.button("自动推进2年", use_container_width=True):
                history.run_years(2)
                _rerun()
        else:
            st.success("二十年国家足球人物史已经完成。")

        st.divider()
        st.download_button(
            "下载人物史JSON存档",
            data=history.to_json(),
            file_name=f"football-republic-careers-m{history.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入人物史JSON存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = CareerJusticeHistory.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.career_justice_history = restored
                st.success("人物、关系、案件和足球状态指纹验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "新历史初始路线",
            options=[item.value for item in Strategy],
            index=1,
        )
        if st.button("重开20年人物史", use_container_width=True):
            st.session_state.career_justice_history = CareerJusticeHistory(
                Strategy(reset_strategy),
                max_terms=10,
            )
            _rerun()


def _people_tab(history: CareerJusticeHistory) -> None:
    st.markdown("### 跨机构政治人物库")
    rows = [
        {
            "姓名": person.name,
            "集团": history.current_campaign.politics.stakeholders[person.bloc].name,
            "籍贯": person.home_region,
            "机构": person.institution,
            "职位": person.role,
            "年龄": person.age,
            "能力": person.competence * 100,
            "廉洁": person.integrity * 100,
            "野心": person.ambition * 100,
            "忠诚": person.loyalty * 100,
            "关系网": person.network_power * 100,
            "法律暴露": person.exposure * 100,
            "状态": person.status,
        }
        for person in history.people.values()
    ]
    frame = pd.DataFrame(rows)
    left, right = st.columns([1.45, 1])
    with left:
        st.dataframe(
            frame.sort_values(["状态", "关系网"], ascending=[True, False]),
            hide_index=True,
            use_container_width=True,
            height=470,
        )
    with right:
        fig = px.scatter(
            frame,
            x="能力",
            y="廉洁",
            size="关系网",
            color="状态",
            hover_name="姓名",
            hover_data=["机构", "职位", "野心", "法律暴露"],
            template="plotly_dark",
            size_max=46,
        )
        fig.update_layout(
            height=450,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 履历时间线")
    if history.career_history:
        career = pd.DataFrame(
            [asdict(item) for item in reversed(history.career_history)]
        ).rename(
            columns={
                "global_month": "月份",
                "person_name": "姓名",
                "event_type": "事件",
                "institution": "机构",
                "role": "职位",
                "reason": "原因",
            }
        )
        st.dataframe(career, hide_index=True, use_container_width=True, height=430)


def _network_tab(history: CareerJusticeHistory) -> None:
    st.markdown("### 亲属、商业、师生与派系网络")
    rows = []
    for tie in history.patronage_ties.values():
        rows.append(
            {
                "关系ID": tie.id,
                "甲方": history.people[tie.source_id].name,
                "乙方": history.people[tie.target_id].name,
                "类型": tie.kind,
                "强度": tie.strength * 100,
                "已披露": tie.disclosed,
                "建立月份": tie.created_global_month,
                "状态": tie.status,
            }
        )
    frame = pd.DataFrame(rows)
    top = st.columns(4)
    top[0].metric("关系总数", str(len(frame)))
    top[1].metric("未披露", str(int((~frame["已披露"]).sum())))
    top[2].metric("强关系", str(int((frame["强度"] >= 70).sum())))
    top[3].metric("隐蔽网络强度", f"{history.undisclosed_network_strength:.2f}")
    st.dataframe(
        frame.sort_values(["已披露", "强度"], ascending=[True, False]),
        hide_index=True,
        use_container_width=True,
        height=480,
    )
    st.caption(
        "关系本身不等于违法。风险来自强关系、未披露、低廉洁和掌握审批权同时出现。"
    )


def _justice_tab(history: CareerJusticeHistory) -> None:
    st.markdown("### 调查、起诉、审理与申诉")
    metrics = st.columns(5)
    metrics[0].metric("司法独立", f"{history.justice_independence:.0%}")
    metrics[1].metric("检察能力", f"{history.prosecutor_capacity:.0%}")
    metrics[2].metric("案件总数", str(len(history.justice_cases)))
    metrics[3].metric("活跃案件", str(len(history.active_cases)))
    metrics[4].metric(
        "最终禁入",
        str(sum(person.status == "banned" for person in history.people.values())),
    )

    if history.justice_cases:
        case_rows = [
            {
                "案件": case.id,
                "当事人": case.subject_name,
                "立案月份": case.opened_global_month,
                "路线": case.route,
                "阶段": case.stage,
                "证据": case.evidence * 100,
                "独立性": case.independence * 100,
                "结果": case.outcome,
                "申诉": case.appeal_status,
                "结案月份": case.closed_global_month,
                "指控": case.allegation,
            }
            for case in reversed(history.justice_cases)
        ]
        st.dataframe(pd.DataFrame(case_rows), hide_index=True, use_container_width=True, height=420)
    else:
        st.info("案件检查每六个月进行一次。低廉洁、高关系网和未披露利益关系会提高暴露概率。")

    if history.justice_history:
        st.markdown("### 案件卷宗事件")
        events = pd.DataFrame(
            [asdict(item) for item in reversed(history.justice_history)]
        ).rename(
            columns={
                "global_month": "月份",
                "subject_name": "当事人",
                "stage": "阶段",
                "headline": "事件",
                "evidence": "证据",
                "independence": "独立性",
                "effects": "后果",
            }
        )
        events["证据"] = events["证据"] * 100
        events["独立性"] = events["独立性"] * 100
        events["后果"] = events["后果"].apply(lambda value: "；".join(value))
        st.dataframe(events, hide_index=True, use_container_width=True, height=460)


def main() -> None:
    st.set_page_config(
        page_title="Football Republic Career History",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    history = _session()
    _sidebar(history)
    _header(history)
    _decision(history)
    campaign = history.current_campaign
    tabs = st.tabs(
        [
            "政治人物库",
            "关系网络",
            "调查与申诉",
            "候选人与投票",
            "组阁协议",
            "内阁与任免",
            "宪政危机",
            "历届主席",
            "冠军历史",
            "俱乐部兴衰",
            "球员代际",
            "当前利益集团",
            "当前议会",
            "当前联赛",
            "当前杯赛",
            "产业与球场",
            "财务与审计",
        ]
    )
    with tabs[0]:
        _people_tab(history)
    with tabs[1]:
        _network_tab(history)
    with tabs[2]:
        _justice_tab(history)
    with tabs[3]:
        _election_tab(history)
    with tabs[4]:
        _agreements_tab(history)
    with tabs[5]:
        _cabinet_tab(history)
    with tabs[6]:
        _constitutional_tab(history)
    with tabs[7]:
        _mandates_tab(history)
    with tabs[8]:
        _seasons_tab(history)
    with tabs[9]:
        _clubs_tab(history)
    with tabs[10]:
        _players_tab(history)
    with tabs[11]:
        _stakeholders_tab(campaign)
    with tabs[12]:
        _congress_tab(campaign)
    with tabs[13]:
        _pyramid_tab(campaign)
    with tabs[14]:
        _competition_tab(campaign)
    with tabs[15]:
        _commercial_tab(campaign)
        _lifecycle_tab(campaign)
        _insolvency_tab(campaign)
    with tabs[16]:
        _finance_tab(campaign)
        _owners_tab(campaign)
        _squad_tab(campaign)
        _events_tab(campaign)


if __name__ == "__main__":
    main()
