"""Extended Streamlit dashboard for cups, contracts and workload."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

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


def _money(value: float) -> str:
    return f"¥{value / 1_000_000:,.2f}M" if abs(value) >= 1_000_000 else f"¥{value:,.0f}"


def _competition_tab(campaign: DeepCampaign) -> None:
    cup = campaign.football.domestic_cup
    continental = campaign.football.continental
    left, right = st.columns([1.1, 1.5])
    with left:
        st.markdown("### 全国足协杯")
        if cup.champions:
            for season, club_id in sorted(cup.champions.items()):
                st.success(f"第{season}赛季冠军：{campaign.engine.state.clubs[club_id].name}")
        if cup.results:
            rows = [
                {
                    "赛季": item.season,
                    "阶段": item.stage,
                    "主队": item.match.home_name,
                    "比分": item.match.scoreline,
                    "客队": item.match.away_name,
                    "晋级": item.winner_name,
                    "决胜": item.decided_by,
                }
                for item in reversed(cup.results)
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=470)
        else:
            st.info("足协杯首轮将在第4个月进行，一级和二级全部14队参赛。")
    with right:
        st.markdown(f"### 洲际冠军杯 · 第{continental.season}赛季")
        tabs = st.tabs(["A组", "B组", "淘汰赛"])
        for tab, group in zip(tabs[:2], ("A", "B")):
            with tab:
                rows = [
                    {
                        "#": index,
                        "俱乐部": row.team_name,
                        "赛": row.played,
                        "胜": row.won,
                        "平": row.drawn,
                        "负": row.lost,
                        "净胜": row.goal_difference,
                        "积分": row.points,
                    }
                    for index, row in enumerate(continental.sorted_group(group), start=1)
                ]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=230)
        with tabs[2]:
            if continental.knockout_results:
                rows = [
                    {
                        "阶段": item.stage,
                        "主队": item.match.home_name,
                        "比分": item.match.scoreline,
                        "客队": item.match.away_name,
                        "晋级": item.winner_name,
                        "决胜": item.decided_by,
                    }
                    for item in continental.knockout_results
                ]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            else:
                st.info("小组前两名进入半决赛。")
        qualifier_names = [campaign.engine.state.clubs[club_id].name for club_id in continental.qualifiers]
        st.caption(
            "本国参赛：" + "、".join(qualifier_names)
            + f" · 已获得洲际奖金 {_money(continental.domestic_prize_money)}"
        )
        if continental.champion_id:
            st.success(f"洲际冠军：{continental.clubs[continental.champion_id].name}")


def _contracts_tab(campaign: DeepCampaign) -> None:
    market = campaign.football.contracts
    top = st.columns(4)
    top[0].metric("自由球员", str(len(market.free_agents)))
    top[1].metric("在外租借", str(len(market.active_loans)))
    top[2].metric("合同事件", str(len(market.contract_history)))
    top[3].metric("租借流水", str(len(market.loan_history)))

    left, right = st.columns([1.45, 1])
    with left:
        st.markdown("### 合同谈判与自由市场")
        if market.contract_history:
            rows = [
                {
                    "月份": item.month,
                    "球员": item.player_name,
                    "俱乐部": item.club_name,
                    "动作": item.action,
                    "旧月薪": _money(item.old_wage),
                    "新月薪": _money(item.new_wage),
                    "期限": item.months,
                    "说明": item.note,
                }
                for item in reversed(market.contract_history)
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=420)
        else:
            st.info("合同进入最后三个月后，俱乐部会按重要性和支付能力决定是否续约。")
    with right:
        st.markdown("### 当前自由球员")
        if market.free_agents:
            rows = [
                {
                    "球员": player.name,
                    "位置": player.position,
                    "年龄": player.age,
                    "能力": round(player.ability, 1),
                    "潜力": round(player.potential, 1),
                    "原月薪": _money(player.monthly_wage),
                }
                for player in sorted(market.free_agents, key=lambda item: item.ability, reverse=True)
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=260)
        else:
            st.caption("当前没有未签约职业球员。")
        st.markdown("### 租借记录")
        if market.loan_history:
            rows = [
                {
                    "开始": item.start_month,
                    "归还": item.return_month,
                    "球员": item.player_name,
                    "母队": item.parent_name,
                    "租借队": item.borrower_name,
                    "工资承担": f"{item.wage_share:.0%}",
                    "状态": item.status,
                }
                for item in reversed(market.loan_history)
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=260)
        else:
            st.caption("主席确定转会制度后，发展型租借在第7和第19个月办理。")


def _workload_tab(campaign: DeepCampaign) -> None:
    history = campaign.football.workload.history
    if not history:
        st.info("正式比赛开始后，这里会显示每家俱乐部的月度赛程压力。")
        return
    frame = pd.DataFrame([asdict(item) for item in history])
    latest_month = int(frame["month"].max())
    latest = frame[frame["month"] == latest_month].copy()
    st.markdown(f"### 第{latest_month}月赛程负荷")
    columns = st.columns(4)
    columns[0].metric("最忙俱乐部", latest.loc[latest["matches"].idxmax(), "club_name"])
    columns[1].metric("最高场次", str(int(latest["matches"].max())))
    columns[2].metric("拥堵伤病", str(int(latest["injuries"].sum())))
    columns[3].metric("洲际客场", str(int(latest["continental_away_matches"].sum())))

    left, right = st.columns([1.2, 1])
    with left:
        fig = px.scatter(
            latest,
            x="matches",
            y="extra_fitness_cost",
            size="injuries",
            color="congestion_level",
            hover_name="club_name",
            template="plotly_dark",
            labels={
                "matches": "当月比赛",
                "extra_fitness_cost": "额外体能损耗",
                "congestion_level": "拥堵等级",
            },
            size_max=34,
        )
        fig.update_layout(
            height=390,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.dataframe(
            latest[
                [
                    "club_name",
                    "matches",
                    "continental_away_matches",
                    "extra_fitness_cost",
                    "injuries",
                    "congestion_level",
                ]
            ].rename(
                columns={
                    "club_name": "俱乐部",
                    "matches": "比赛",
                    "continental_away_matches": "洲际客场",
                    "extra_fitness_cost": "额外体能损耗",
                    "injuries": "新增伤病",
                    "congestion_level": "拥堵等级",
                }
            ),
            hide_index=True,
            use_container_width=True,
            height=390,
        )
    st.caption(
        "每场比赛本身已经消耗首发体能；当月超过两场后再叠加拥堵成本，洲际客场额外增加旅行负荷和伤病概率。"
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
            "财务监管",
            "合同与租借",
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
        _finance_tab(campaign)
    with tabs[3]:
        _contracts_tab(campaign)
    with tabs[4]:
        _workload_tab(campaign)
    with tabs[5]:
        _media_tab(campaign)
    with tabs[6]:
        _owners_tab(campaign)
    with tabs[7]:
        _squad_tab(campaign)
    with tabs[8]:
        _events_tab(campaign)


if __name__ == "__main__":
    main()
