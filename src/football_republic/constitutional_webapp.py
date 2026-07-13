"""Streamlit dashboard for appointments, crises and irregular administrations."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import _competition_tab
from football_republic.campaign import Strategy
from football_republic.constitutional import ConstitutionalLongTermCampaign
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


def _session() -> ConstitutionalLongTermCampaign:
    if "constitutional_history" not in st.session_state:
        st.session_state.constitutional_history = ConstitutionalLongTermCampaign(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.constitutional_history


def _rerun() -> None:
    st.rerun()


def _sidebar(history: ConstitutionalLongTermCampaign) -> None:
    with st.sidebar:
        st.markdown("## 国家足球政府史")
        st.caption("联赛连续20年，但政府可能辞职、看守或提前改选。")
        st.metric("全球月份", str(history.global_month))
        st.metric("当前年份", f"第{history.global_year}年")
        st.metric("制度任期", f"第{history.term_index}届 · M{history.local_month}")
        status = "看守政府" if history.caretaker_active else "正式政府"
        st.markdown(
            f"**主席：{history.current_president.name}**  \n"
            f"状态：{status}  \n"
            f"路线：{history.current_president.strategy.value}"
        )
        if history.caretaker_active:
            st.warning("看守政府只维持日常运行，提前选举将在三个月内举行。")

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
            st.success("二十年国家足球政府史已经完成。")

        st.divider()
        st.download_button(
            "下载宪政JSON存档",
            data=history.to_json(),
            file_name=f"football-republic-government-m{history.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入宪政JSON存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = ConstitutionalLongTermCampaign.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.constitutional_history = restored
                st.success("决策日志和状态指纹验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "新历史初始路线",
            options=[item.value for item in Strategy],
            index=1,
        )
        if st.button("重开20年政府史", use_container_width=True):
            st.session_state.constitutional_history = ConstitutionalLongTermCampaign(
                Strategy(reset_strategy),
                max_terms=10,
            )
            _rerun()


def _header(history: ConstitutionalLongTermCampaign) -> None:
    state = history.current_campaign.engine.state
    politics = history.current_campaign.politics
    government = "看守" if history.caretaker_active else "正式"
    st.markdown(
        f"# 足球共和国 · 第{history.global_year}年  "
        f"<span style='font-size:.55em;opacity:.68'>第{history.term_index}届 · {government}政府</span>",
        unsafe_allow_html=True,
    )
    top = st.columns(7)
    top[0].metric("现任主席", history.current_president.name)
    top[1].metric("政府状态", government)
    top[2].metric("内阁能力", f"{history.cabinet_quality:.0%}")
    top[3].metric("权力俘获风险", f"{history.capture_risk:.0%}")
    top[4].metric("联盟支持", f"{politics.coalition_support:.0%}")
    top[5].metric("国库", f"¥{state.treasury / 1_000_000:,.1f}M")
    top[6].metric("国家队", f"{state.national_team_strength:.1f}")


def _cabinet_tab(history: ConstitutionalLongTermCampaign) -> None:
    st.markdown("### 现任足协内阁")
    rows = [
        {
            "职位": actor.office,
            "姓名": actor.name,
            "类型": actor.style,
            "能力": actor.competence * 100,
            "廉洁": actor.integrity * 100,
            "忠诚": actor.loyalty * 100,
            "关系网": actor.network_power * 100,
            "丑闻积累": actor.scandal_points * 100,
            "任命者": actor.appointed_by,
            "上任月份": actor.appointed_global_month,
            "状态": actor.status,
        }
        for actor in history.cabinet.values()
    ]
    frame = pd.DataFrame(rows)
    left, right = st.columns([1.35, 1])
    with left:
        st.dataframe(
            frame.sort_values("职位"),
            hide_index=True,
            use_container_width=True,
            height=390,
        )
    with right:
        fig = px.scatter(
            frame,
            x="能力",
            y="廉洁",
            size="关系网",
            color="类型",
            hover_name="姓名",
            hover_data=["职位", "忠诚", "丑闻积累"],
            template="plotly_dark",
            size_max=45,
        )
        fig.update_layout(
            height=380,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 历次任免")
    if history.appointment_history:
        records = pd.DataFrame(
            [asdict(item) for item in reversed(history.appointment_history)]
        ).rename(
            columns={
                "global_month": "月份",
                "term": "制度任期",
                "president_name": "主席",
                "office": "职位",
                "outgoing_name": "离任",
                "incoming_name": "新任",
                "style": "类型",
                "reason": "原因",
            }
        )
        st.dataframe(records, hide_index=True, use_container_width=True, height=380)
    st.caption(
        "高忠诚内阁执行更稳定，但如果忠诚、关系网和低廉洁同时出现，寻租与制度俘获风险会逐月积累。"
    )


def _constitutional_tab(history: ConstitutionalLongTermCampaign) -> None:
    st.markdown("### 历届政府与非正常交接")
    if history.administration_history:
        rows = []
        for item in history.administration_history:
            rows.append(
                {
                    "制度任期": item.term,
                    "主席": item.president_name,
                    "路线": item.strategy,
                    "上台月份": item.start_global_month,
                    "离任月份": item.end_global_month,
                    "上台原因": item.entry_reason,
                    "状态": item.status,
                    "离任原因": item.exit_reason or "仍在任",
                    "执政时长": (
                        (item.end_global_month or history.global_month)
                        - item.start_global_month
                    ),
                }
            )
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            height=330,
        )

    st.markdown("### 宪政危机时间线")
    if history.constitutional_history:
        events = pd.DataFrame(
            [asdict(item) for item in reversed(history.constitutional_history)]
        ).rename(
            columns={
                "global_month": "全球月份",
                "local_month": "任期月份",
                "term": "制度任期",
                "event_type": "类型",
                "headline": "事件",
                "severity": "严重度",
                "effects": "后果",
            }
        )
        events["严重度"] = events["严重度"] * 100
        events["后果"] = events["后果"].apply(lambda value: "；".join(value))
        st.dataframe(events, hide_index=True, use_container_width=True, height=430)
    else:
        st.info(
            "危机检查发生在任期第5、9、13、17和21个月。低廉洁、高关系网、联盟流失与既有丑闻会共同提高爆发概率。"
        )
    st.caption(
        "主席下台只改变政府，不重置联赛。看守期内俱乐部继续发工资、比赛照常举行、球员继续老化，提前选举后新主席继承全部后果。"
    )


def main() -> None:
    st.set_page_config(
        page_title="Football Republic Government History",
        page_icon="🏛️",
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
        _cabinet_tab(history)
    with tabs[1]:
        _constitutional_tab(history)
    with tabs[2]:
        _mandates_tab(history)
    with tabs[3]:
        _seasons_tab(history)
    with tabs[4]:
        _clubs_tab(history)
    with tabs[5]:
        _players_tab(history)
    with tabs[6]:
        _stakeholders_tab(campaign)
    with tabs[7]:
        _congress_tab(campaign)
    with tabs[8]:
        _pyramid_tab(campaign)
    with tabs[9]:
        _competition_tab(campaign)
    with tabs[10]:
        _commercial_tab(campaign)
        _lifecycle_tab(campaign)
        _insolvency_tab(campaign)
    with tabs[11]:
        _finance_tab(campaign)
        _owners_tab(campaign)
        _squad_tab(campaign)
        _events_tab(campaign)


if __name__ == "__main__":
    main()
