"""Full deep dashboard with stakeholder politics and mandate history."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import (
    _competition_tab,
    _contracts_tab,
    _workload_tab,
)
from football_republic.deep_campaign import DeepCampaign
from football_republic.generational_webapp import (
    _commercial_tab,
    _insolvency_tab,
    _lifecycle_tab,
    _registration_tab,
)
from football_republic.political_economy import AGENDA_DECISIONS
from football_republic.pyramid_webapp import (
    _controls,
    _css,
    _decision,
    _events_tab,
    _finance_tab,
    _header,
    _media_tab,
    _metrics,
    _owners_tab,
    _pyramid_tab,
    _session,
    _squad_tab,
)


def _percentage(value: float) -> str:
    return f"{value:.0%}"


def _stakeholders_tab(campaign: DeepCampaign) -> None:
    politics = campaign.politics
    top = st.columns(4)
    top[0].metric("执政联盟支持", _percentage(politics.coalition_support))
    top[1].metric("体系可治理性", _percentage(politics.governability))
    top[2].metric("最强盟友", politics.strongest_ally.name)
    top[3].metric("反对派领袖", politics.opposition_leader.name)

    rows = [
        {
            "利益集团": actor.name,
            "阵营": actor.bloc,
            "权力": actor.power * 100,
            "支持": actor.support * 100,
            "信任": actor.trust * 100,
            "耐心": actor.patience * 100,
            "动员": actor.mobilization * 100,
            "立场": actor.stance,
            "承诺兑现": actor.promises_kept,
            "承诺违约": actor.promises_broken,
        }
        for actor in politics.stakeholders.values()
    ]
    frame = pd.DataFrame(rows)
    left, right = st.columns([1.3, 1])
    with left:
        st.dataframe(
            frame.sort_values(["权力", "支持"], ascending=[False, False]),
            hide_index=True,
            use_container_width=True,
            height=475,
        )
    with right:
        fig = px.scatter(
            frame,
            x="支持",
            y="权力",
            size="动员",
            color="阵营",
            hover_name="利益集团",
            hover_data=["信任", "耐心", "立场"],
            template="plotly_dark",
            size_max=42,
        )
        fig.add_vline(x=50, line_dash="dash")
        fig.update_layout(
            height=465,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)

    actor_names = {
        actor.name: actor for actor in politics.stakeholders.values()
    }
    selected_name = st.selectbox(
        "查看集团记忆",
        options=list(actor_names),
        key="political_actor_memory",
    )
    selected = actor_names[selected_name]
    st.caption(
        "集团不会在下个月清空态度。危机处理、法案投票、承诺兑现与违约都会写入长期记忆。"
    )
    if selected.memory:
        st.code("\n".join(reversed(selected.memory)), language=None)
    else:
        st.info("该集团尚未形成可记录的政治记忆。")


def _congress_tab(campaign: DeepCampaign) -> None:
    politics = campaign.politics
    st.markdown("### 国家足球代表大会")
    agenda_schedule = []
    completed = {item.agenda_id: item for item in politics.agenda_history}
    for month, decision in AGENDA_DECISIONS.items():
        outcome = completed.get(decision.id)
        agenda_schedule.append(
            {
                "月份": month,
                "议程": decision.title,
                "状态": (
                    "通过" if outcome and outcome.passed
                    else "否决" if outcome
                    else "待召开" if campaign.engine.state.month < month
                    else "待表决"
                ),
                "路线": outcome.option_title if outcome else "—",
                "支持权力": outcome.coalition_support * 100 if outcome else None,
                "支持方": "、".join(outcome.supporters) if outcome else "—",
                "反对方": "、".join(outcome.opponents) if outcome else "—",
            }
        )
    st.dataframe(
        pd.DataFrame(agenda_schedule),
        hide_index=True,
        use_container_width=True,
        height=310,
    )

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("### 法案结果")
        if politics.agenda_history:
            rows = [
                {
                    "月份": item.month,
                    "议程": item.agenda_title,
                    "选择": item.option_title,
                    "结果": "通过" if item.passed else "否决",
                    "联盟支持": item.coalition_support * 100,
                    "支持权力": item.yes_power,
                    "总权力": item.total_power,
                    "主要效果": "；".join(item.effects),
                }
                for item in reversed(politics.agenda_history)
            ]
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
                height=430,
            )
        else:
            st.info("首场治理权力议程将在第2个月召开。")
    with right:
        st.markdown("### 公开政治承诺")
        if politics.promises:
            rows = [
                {
                    "承诺": item.title,
                    "提出": item.created_month,
                    "到期": item.due_month,
                    "指标": item.metric,
                    "基线": round(item.baseline, 3),
                    "目标": round(item.target, 3),
                    "实际": round(item.actual_value, 3) if item.actual_value is not None else None,
                    "状态": item.status,
                    "受益集团": "、".join(
                        politics.stakeholders[actor_id].name
                        for actor_id in item.beneficiaries
                    ),
                }
                for item in politics.promises
            ]
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
                height=430,
            )
        else:
            st.caption("通过制度议程后，主席会公开承诺一个可量化结果。")
    st.caption(
        "法案不是按钮必过：利益集团按自身偏好、现有支持、信任与耐心投票。接近半数时可强推，但会消耗政治资本。"
    )


def _history_tab(campaign: DeepCampaign) -> None:
    politics = campaign.politics
    st.markdown("### 任期历史档案")
    if politics.year_archives:
        rows = [
            {
                "年度": item.year,
                "联盟支持": item.coalition_support * 100,
                "可治理性": item.governability * 100,
                "财政(M)": item.treasury / 1_000_000,
                "球迷信任": item.fan_trust * 100,
                "廉洁": item.integrity * 100,
                "青训环境": item.youth_environment,
                "国家队": item.national_team_strength,
                "健康俱乐部": item.solvent_club_share * 100,
                "联赛冠军": item.premier_champion,
                "杯赛冠军": item.cup_champion,
                "洲际最佳": item.continental_best_stage,
                "最强盟友": item.strongest_ally,
                "反对派": item.opposition_leader,
                "兑现/违约": f"{item.promises_kept}/{item.promises_broken}",
            }
            for item in politics.year_archives
        ]
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            height=260,
        )
        archive_frame = pd.DataFrame([asdict(item) for item in politics.year_archives])
        chart_rows = []
        for item in politics.year_archives:
            chart_rows.extend(
                [
                    {"年度": item.year, "指标": "联盟支持", "数值": item.coalition_support * 100},
                    {"年度": item.year, "指标": "球迷信任", "数值": item.fan_trust * 100},
                    {"年度": item.year, "指标": "廉洁声誉", "数值": item.integrity * 100},
                    {"年度": item.year, "指标": "俱乐部健康", "数值": item.solvent_club_share * 100},
                ]
            )
        if chart_rows:
            fig = px.line(
                pd.DataFrame(chart_rows),
                x="年度",
                y="数值",
                color="指标",
                markers=True,
                template="plotly_dark",
            )
            fig.update_layout(
                height=330,
                margin=dict(l=8, r=8, t=25, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,13,23,.35)",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("第12个月结束后形成第一份年度档案。")

    if campaign.engine.state.month >= 24:
        review = campaign.political_review
        top = st.columns(4)
        top[0].metric("续任综合分", f"{review.score:.1f}")
        top[1].metric("最终联盟", _percentage(review.coalition_support))
        top[2].metric("兑现承诺", str(review.promises_kept))
        top[3].metric("违约承诺", str(review.promises_broken))
        st.success(review.verdict)
        st.write(" · ".join(review.explanation))

    st.markdown("### 政治事件时间线")
    if politics.event_history:
        rows = [
            {
                "月份": item.month,
                "主体": item.actor_name,
                "类型": item.event_type,
                "事件": item.headline,
                "后果": "；".join(item.effects),
            }
            for item in reversed(politics.event_history)
        ]
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            height=420,
        )
    else:
        st.caption("随着联盟合作、抗议、罢赛威胁、拨款延迟和承诺考核，这里会形成完整任期时间线。")


def main() -> None:
    st.set_page_config(
        page_title="Football Republic Deep",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    campaign: DeepCampaign = _session()
    _controls(campaign)
    _header(campaign)
    _metrics(campaign)
    if campaign.current_decision:
        _decision(campaign)
    tabs = st.tabs(
        [
            "利益集团",
            "国家足球议会",
            "任期历史",
            "联赛金字塔",
            "杯赛与洲际",
            "产业与球场",
            "注册监管",
            "财务监管",
            "合同与租借",
            "青训与退役",
            "破产与重组",
            "赛程负荷",
            "转播分成",
            "俱乐部老板",
            "国家队征召",
            "比赛与审计",
        ]
    )
    with tabs[0]:
        _stakeholders_tab(campaign)
    with tabs[1]:
        _congress_tab(campaign)
    with tabs[2]:
        _history_tab(campaign)
    with tabs[3]:
        _pyramid_tab(campaign)
    with tabs[4]:
        _competition_tab(campaign)
    with tabs[5]:
        _commercial_tab(campaign)
    with tabs[6]:
        _registration_tab(campaign)
    with tabs[7]:
        _finance_tab(campaign)
    with tabs[8]:
        _contracts_tab(campaign)
    with tabs[9]:
        _lifecycle_tab(campaign)
    with tabs[10]:
        _insolvency_tab(campaign)
    with tabs[11]:
        _workload_tab(campaign)
    with tabs[12]:
        _media_tab(campaign)
    with tabs[13]:
        _owners_tab(campaign)
    with tabs[14]:
        _squad_tab(campaign)
    with tabs[15]:
        _events_tab(campaign)


if __name__ == "__main__":
    main()
