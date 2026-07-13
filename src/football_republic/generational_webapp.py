"""Full deep dashboard including the generational football economy."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import (
    _competition_tab,
    _contracts_tab,
    _money,
    _workload_tab,
)
from football_republic.deep_campaign import DeepCampaign
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


def _commercial_tab(campaign: DeepCampaign) -> None:
    economy = campaign.football.economy
    sponsors = economy.sponsors
    stadiums = economy.stadiums
    st.markdown("### 商业赞助与球场资产")
    sponsor_rows = []
    for club_id, contract in sponsors.contracts.items():
        club = campaign.engine.state.clubs[club_id]
        sponsor_rows.append(
            {
                "俱乐部": club.name,
                "赞助商": contract.sponsor_name,
                "状态": contract.status,
                "年价值(M)": contract.annual_value / 1_000_000,
                "月收入": _money(contract.monthly_component),
                "成绩奖金率": contract.performance_bonus_rate,
                "道德门槛": contract.morality_threshold,
            }
        )
    if sponsor_rows:
        st.dataframe(
            pd.DataFrame(sponsor_rows),
            hide_index=True,
            use_container_width=True,
            height=360,
        )
    else:
        st.info("首批商业合同将在第1个月签署。")

    stadium_rows = []
    for club_id, profile in stadiums.profiles.items():
        recent = [
            record
            for record in stadiums.match_history
            if record.club_id == club_id
        ]
        utilization = (
            sum(record.utilization for record in recent[-5:])
            / len(recent[-5:])
            if recent
            else 0.0
        )
        stadium_rows.append(
            {
                "俱乐部": campaign.engine.state.clubs[club_id].name,
                "球场": profile.stadium_name,
                "容量": profile.capacity,
                "质量": profile.quality * 100,
                "商务设施": profile.hospitality * 100,
                "票价": profile.ticket_price,
                "近5场利用率": utilization * 100,
                "月维护": profile.monthly_maintenance,
                "扩建完成": profile.expansion_completion_month or "—",
            }
        )
    stadium_frame = pd.DataFrame(stadium_rows)
    left, right = st.columns([1.35, 1])
    with left:
        st.dataframe(
            stadium_frame,
            hide_index=True,
            use_container_width=True,
            height=430,
        )
    with right:
        fig = px.scatter(
            stadium_frame,
            x="容量",
            y="近5场利用率",
            size="票价",
            color="质量",
            hover_name="俱乐部",
            template="plotly_dark",
            size_max=38,
        )
        fig.add_hline(y=90, line_dash="dash")
        fig.update_layout(
            height=420,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 商业事件")
    if sponsors.history:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "月份": event.month,
                        "俱乐部": event.club_name,
                        "赞助商": event.sponsor_name,
                        "动作": event.action,
                        "金额": _money(event.amount),
                        "说明": event.note,
                    }
                    for event in reversed(sponsors.history)
                ]
            ),
            hide_index=True,
            use_container_width=True,
            height=290,
        )
    if stadiums.investment_history:
        st.markdown("### 球场投资")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "月份": item.month,
                        "俱乐部": item.club_name,
                        "动作": item.action,
                        "成本": _money(item.cost),
                        "新增容量": item.capacity_change,
                        "质量变化": item.quality_change,
                        "完成月份": item.completion_month,
                    }
                    for item in reversed(stadiums.investment_history)
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )


def _registration_tab(campaign: DeepCampaign) -> None:
    registration = campaign.football.economy.registration
    st.markdown("### 职业球员注册监管")
    columns = st.columns(4)
    columns[0].metric("当前制度", registration.policy_name)
    columns[1].metric("一线队上限", str(registration.squad_limit))
    columns[2].metric("外援上限", str(registration.foreign_limit))
    columns[3].metric("本土培养最低", str(registration.homegrown_minimum))

    if not registration.audit_history:
        st.info("注册审查尚未开始。")
        return
    latest_month = max(item.month for item in registration.audit_history)
    latest = [
        item for item in registration.audit_history if item.month == latest_month
    ]
    rows = [
        {
            "俱乐部": item.club_name,
            "注册人数": item.registered_players,
            "外援": item.registered_foreign,
            "本土培养": item.registered_homegrown,
            "未注册": len(item.unregistered_players),
            "罚款": _money(item.fine),
            "合规": "是" if item.compliant else "否",
            "未注册球员": "、".join(item.unregistered_players) or "—",
        }
        for item in latest
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
        height=470,
    )
    st.caption(
        "未注册球员仍有合同并继续训练，但不能参加联赛、杯赛、洲际赛事或国家队征召。注册期为第1、7、13、19个月。"
    )


def _lifecycle_tab(campaign: DeepCampaign) -> None:
    lifecycle = campaign.football.economy.lifecycle
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### 青训毕业生")
        if lifecycle.intake_history:
            rows = [
                {
                    "月份": item.month,
                    "俱乐部": item.club_name,
                    "球员": item.player_name,
                    "位置": item.position,
                    "年龄": item.age,
                    "能力": round(item.ability, 1),
                    "潜力": round(item.potential, 1),
                    "地区环境": round(item.development_environment, 1),
                }
                for item in reversed(lifecycle.intake_history)
            ]
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
                height=480,
            )
        else:
            st.info("首批青训毕业将在第12个月产生。")
    with right:
        st.markdown("### 退役记录")
        if lifecycle.retirement_history:
            rows = [
                {
                    "月份": item.month,
                    "俱乐部": item.club_name,
                    "球员": item.player_name,
                    "年龄": item.age,
                    "能力": round(item.ability, 1),
                    "出场": item.career_appearances,
                    "原因": item.reason,
                }
                for item in reversed(lifecycle.retirement_history)
            ]
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
                height=330,
            )
        else:
            st.caption("目前尚无职业球员退役。")

        if lifecycle.intake_history:
            frame = pd.DataFrame([asdict(item) for item in lifecycle.intake_history])
            fig = px.scatter(
                frame,
                x="ability",
                y="potential",
                color="position",
                hover_name="player_name",
                template="plotly_dark",
                labels={"ability": "当前能力", "potential": "潜力"},
            )
            fig.update_layout(
                height=330,
                margin=dict(l=8, r=8, t=25, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,13,23,.35)",
            )
            st.plotly_chart(fig, use_container_width=True)


def _insolvency_tab(campaign: DeepCampaign) -> None:
    economy = campaign.football.economy
    insolvency = economy.insolvency
    st.markdown("### 公司清算与足球牌照重组")
    if insolvency.history:
        rows = [
            {
                "月份": item.month,
                "旧俱乐部": item.old_name,
                "继承者": item.new_name,
                "措施": item.action,
                "原债务": _money(item.debt_before),
                "重组后债务": _money(item.debt_after),
                "释放球员": item.players_released,
                "扣分": item.points_deduction,
                "说明": item.note,
            }
            for item in reversed(insolvency.history)
        ]
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            height=350,
        )
    else:
        st.info("尚无俱乐部连续三个月达到清算条件。")

    rows = []
    for club_id, streak in insolvency.distress_streak.items():
        club = campaign.engine.state.clubs[club_id]
        rows.append(
            {
                "俱乐部": club.name,
                "连续危机月": streak,
                "牌照": club.license_status,
                "欠薪月": club.wage_arrears_months,
                "财务健康": club.financial_health * 100,
                "债务": club.debt / 1_000_000,
            }
        )
    if rows:
        st.markdown("### 清算风险雷达")
        st.dataframe(
            pd.DataFrame(rows).sort_values(
                ["连续危机月", "财务健康"],
                ascending=[False, True],
            ),
            hide_index=True,
            use_container_width=True,
            height=390,
        )
    st.caption(
        "连续严重资不抵债不会无限续命：旧公司清算、债务削减、昂贵合同释放，牌照转给球迷信托支持的继承俱乐部，并以扣分方式重新进入职业体系。"
    )


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
        _pyramid_tab(campaign)
    with tabs[1]:
        _competition_tab(campaign)
    with tabs[2]:
        _commercial_tab(campaign)
    with tabs[3]:
        _registration_tab(campaign)
    with tabs[4]:
        _finance_tab(campaign)
    with tabs[5]:
        _contracts_tab(campaign)
    with tabs[6]:
        _lifecycle_tab(campaign)
    with tabs[7]:
        _insolvency_tab(campaign)
    with tabs[8]:
        _workload_tab(campaign)
    with tabs[9]:
        _media_tab(campaign)
    with tabs[10]:
        _owners_tab(campaign)
    with tabs[11]:
        _squad_tab(campaign)
    with tabs[12]:
        _events_tab(campaign)


if __name__ == "__main__":
    main()
