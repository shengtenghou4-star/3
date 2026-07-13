"""Streamlit interface for the deep two-tier Football Republic simulation."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from football_republic.campaign import STRATEGIES, Strategy
from football_republic.deep_campaign import DeepCampaign


STRATEGY_LABELS = {
    Strategy.FOUNDATIONS: "基层筑基",
    Strategy.BALANCED: "均衡执政",
    Strategy.QUICK_RESULTS: "国家队速成",
}


def _money(value: float) -> str:
    return f"¥{value / 1_000_000:,.2f}M" if abs(value) >= 1_000_000 else f"¥{value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _css() -> None:
    st.markdown(
        """
        <style>
        :root{--gold:#ecc65e;--cyan:#65d7ff;--green:#64dfa1;--red:#ff7884;--muted:#94a8c3}
        .stApp{background:radial-gradient(circle at 8% 5%,rgba(20,92,142,.25),transparent 31rem),radial-gradient(circle at 90% 9%,rgba(161,113,20,.18),transparent 30rem),linear-gradient(145deg,#050b14,#091526 48%,#06101c);color:#edf5ff}
        #MainMenu,footer,header{visibility:hidden}.block-container{max-width:1550px;padding-top:1.05rem;padding-bottom:3rem}
        .hero{border:1px solid rgba(236,198,94,.32);border-radius:25px;padding:26px 29px;margin-bottom:17px;background:linear-gradient(110deg,rgba(10,30,51,.96),rgba(13,29,47,.85));box-shadow:0 22px 75px rgba(0,0,0,.34)}
        .kicker{color:var(--gold);letter-spacing:.17em;font-size:.72rem;font-weight:900}.title{font-size:2.2rem;font-weight:900;margin:7px 0}.sub{color:var(--muted)}
        [data-testid="stMetric"]{background:linear-gradient(165deg,rgba(18,35,58,.95),rgba(8,18,31,.95));border:1px solid rgba(130,163,198,.18);padding:14px 16px;border-radius:17px;box-shadow:0 10px 32px rgba(0,0,0,.22)}
        .card{background:rgba(11,22,39,.86);border:1px solid rgba(130,163,198,.17);border-radius:18px;padding:17px 19px;margin:8px 0 14px}
        .decision{background:linear-gradient(130deg,rgba(67,48,14,.55),rgba(13,27,45,.96));border:1px solid rgba(236,198,94,.4);border-radius:19px;padding:18px 20px;margin:10px 0 16px}
        .pill{display:inline-block;padding:5px 9px;border-radius:999px;background:rgba(101,215,255,.11);color:#aceaff;border:1px solid rgba(101,215,255,.21);font-size:.75rem;margin:3px 5px 3px 0}
        .danger{color:var(--red);font-weight:850}.good{color:var(--green);font-weight:850}.warn{color:var(--gold);font-weight:850}.muted{color:var(--muted)}
        .fixture{display:grid;grid-template-columns:1fr auto 1fr;gap:15px;align-items:center;padding:11px 14px;margin:7px 0;border-radius:14px;background:rgba(13,27,45,.88);border:1px solid rgba(130,163,198,.14)}.home{text-align:right;font-weight:750}.away{text-align:left;font-weight:750}.score{color:var(--gold);font-weight:900}
        .stTabs [data-baseweb="tab"]{background:rgba(14,29,49,.72);border-radius:12px;padding:8px 13px;border:1px solid rgba(130,163,198,.12)}.stTabs [aria-selected="true"]{color:var(--gold);border-color:rgba(236,198,94,.36);background:rgba(61,49,19,.35)}
        [data-testid="stDataFrame"]{border:1px solid rgba(130,163,198,.16);border-radius:14px;overflow:hidden}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _new_campaign(strategy: Strategy) -> DeepCampaign:
    campaign = DeepCampaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    return campaign


def _session() -> DeepCampaign:
    if "deep_strategy" not in st.session_state:
        st.session_state.deep_strategy = Strategy.BALANCED
    if "deep_campaign" not in st.session_state:
        st.session_state.deep_campaign = _new_campaign(st.session_state.deep_strategy)
    return st.session_state.deep_campaign


def _controls(campaign: DeepCampaign) -> None:
    with st.sidebar:
        st.markdown("## 足协主席办公室")
        strategy = st.selectbox(
            "执政路线",
            list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=list(Strategy).index(st.session_state.deep_strategy),
        )
        if strategy != st.session_state.deep_strategy:
            st.session_state.deep_strategy = strategy
            st.session_state.deep_campaign = _new_campaign(strategy)
            st.rerun()
        blocked = campaign.current_decision is not None
        if blocked:
            st.error("存在待决内阁事项，时间已冻结。")
        disabled = blocked or campaign.engine.state.month >= 24
        left, right = st.columns(2)
        with left:
            if st.button("推进1月", use_container_width=True, disabled=disabled):
                campaign.advance(1, interactive=True)
                st.rerun()
        with right:
            if st.button("推进3月", use_container_width=True, disabled=disabled):
                campaign.advance(3, interactive=True)
                st.rerun()
        if st.button("推进至下一决策", type="primary", use_container_width=True, disabled=disabled):
            campaign.advance(24 - campaign.engine.state.month, interactive=True)
            st.rerun()
        if st.button("重开深度档", use_container_width=True):
            st.session_state.deep_campaign = _new_campaign(st.session_state.deep_strategy)
            st.rerun()
        st.divider()
        st.progress(campaign.engine.state.month / 24)
        st.caption(f"任期 {campaign.engine.state.month}/24 月")
        st.metric("国内职业比赛", str(campaign.total_domestic_matches))
        st.metric("托管中俱乐部", str(campaign.clubs_in_administration))
        st.metric("失去牌照", str(campaign.excluded_clubs))


def _header(campaign: DeepCampaign) -> None:
    pyramid = campaign.football.pyramid
    st.markdown(
        f"""
        <div class="hero"><div class="kicker">DEEP NATIONAL FOOTBALL ECOSYSTEM</div>
        <div class="title">足球共和国 · 职业金字塔监管中心</div>
        <div class="sub">任期第 <b>{campaign.engine.state.month}</b> 月 · 第 <b>{pyramid.season}</b> 赛季 · 14家职业俱乐部 · 两级联赛 · 国家队从共享球员库征召</div></div>
        """,
        unsafe_allow_html=True,
    )


def _decision(campaign: DeepCampaign) -> None:
    decision = campaign.current_decision
    if not decision:
        return
    st.markdown(
        f"""
        <div class="decision"><div class="kicker">PRESIDENTIAL DECISION · MONTH {decision.month}</div>
        <h3>{decision.title}</h3><div class="muted">{decision.narrative}</div></div>
        """,
        unsafe_allow_html=True,
    )
    option_id = st.radio(
        "主席决定",
        [item.id for item in decision.options],
        format_func=lambda option_id: next(item.title for item in decision.options if item.id == option_id),
        key=f"deep_{decision.id}",
    )
    option = next(item for item in decision.options if item.id == option_id)
    st.caption(option.summary)
    st.warning("风险：" + option.risk)
    if st.button("签署决定", type="primary"):
        campaign.resolve_decision(option_id)
        st.rerun()


def _metrics(campaign: DeepCampaign) -> None:
    state = campaign.engine.state
    squad = campaign.football.current_squad
    columns = st.columns(8)
    values = (
        ("足协国库", _money(state.treasury)),
        ("政治资本", _pct(state.political_capital)),
        ("球迷信任", _pct(state.fan_trust)),
        ("廉洁声誉", _pct(state.integrity_reputation)),
        ("联赛健康", _pct(state.league_financial_health)),
        ("国家队26人", f"{squad.strength:.1f}"),
        ("预选赛", f"{campaign.football.international.user_position}/6"),
        ("升降级变动", str(len(campaign.football.pyramid.movement_history))),
    )
    for column, (label, value) in zip(columns, values):
        column.metric(label, value)


def _table(league, promotion: bool) -> pd.DataFrame:
    rows = []
    for position, row in enumerate(league.sorted_table(), start=1):
        club = league.clubs[row.team_id]
        if promotion:
            zone = "直接升级" if position == 1 else "附加赛" if position == 2 else ""
        else:
            count = len(league.club_ids)
            zone = "直接降级" if position == count else "保级附加赛" if position == count - 1 else ""
        eligibility = (
            "失去牌照" if club.license_status == "excluded"
            else "托管" if club.license_status == "administration"
            else "欠薪风险" if club.wage_arrears_months >= 2
            else "可参赛"
        )
        rows.append(
            {
                "#": position,
                "俱乐部": club.name,
                "赛": row.played,
                "胜": row.won,
                "平": row.drawn,
                "负": row.lost,
                "净胜": row.goal_difference,
                "积分": row.points,
                "区域": zone,
                "准入": eligibility,
                "财务健康": round(club.financial_health * 100),
            }
        )
    return pd.DataFrame(rows)


def _pyramid_tab(campaign: DeepCampaign) -> None:
    pyramid = campaign.football.pyramid
    left, right = st.columns(2)
    with left:
        st.markdown("### 一级 · 国家超级联赛")
        st.dataframe(_table(pyramid.premier, promotion=False), hide_index=True, use_container_width=True, height=330)
    with right:
        st.markdown("### 二级 · 国家冠军联赛")
        st.dataframe(_table(pyramid.second, promotion=True), hide_index=True, use_container_width=True, height=380)
    st.markdown("### 升降级裁决")
    if pyramid.movement_history:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "赛季": item.season,
                        "升级": item.promoted_name,
                        "降级": item.relegated_name,
                        "路径": item.route,
                        "依据": item.note,
                    }
                    for item in pyramid.movement_history
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("首个升降级裁决将在第12个月完成；积分之外还要通过财务与准入审查。")


def _finance_tab(campaign: DeepCampaign) -> None:
    pyramid = campaign.football.pyramid
    rows = []
    division = {club_id: 1 for club_id in pyramid.premier_ids} | {club_id: 2 for club_id in pyramid.second_ids}
    for club_id, club in campaign.engine.state.clubs.items():
        owner = pyramid.owners[club_id]
        rows.append(
            {
                "俱乐部": club.name,
                "级别": division[club_id],
                "现金(M)": club.cash / 1_000_000,
                "债务(M)": club.debt / 1_000_000,
                "月收入(M)": club.monthly_revenue / 1_000_000,
                "工资/收入": club.monthly_wage_bill / max(club.monthly_revenue, 1),
                "财务健康": club.financial_health * 100,
                "状态": club.license_status,
                "老板耐心": owner.patience * 100,
            }
        )
    frame = pd.DataFrame(rows)
    left, right = st.columns([1.25, 1])
    with left:
        st.dataframe(frame, hide_index=True, use_container_width=True, height=430)
    with right:
        fig = px.scatter(
            frame,
            x="财务健康",
            y="工资/收入",
            size="现金(M)",
            color="级别",
            hover_name="俱乐部",
            template="plotly_dark",
            size_max=36,
        )
        fig.add_hline(y=1.0, line_dash="dash")
        fig.update_layout(height=420, margin=dict(l=8, r=8, t=25, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 托管、扣分与牌照")
    if pyramid.administration_history:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "月份": item.month,
                        "俱乐部": item.club_name,
                        "措施": item.action,
                        "扣分": item.points_deduction,
                        "老板注资": _money(item.owner_injection),
                        "依据": item.note,
                    }
                    for item in reversed(pyramid.administration_history)
                ]
            ),
            hide_index=True,
            use_container_width=True,
            height=330,
        )
    else:
        st.info("目前没有俱乐部进入正式托管程序。")


def _media_tab(campaign: DeepCampaign) -> None:
    history = campaign.football.pyramid.media_history
    if not history:
        st.info("第1个月开始分配转播权收入。")
        return
    frame = pd.DataFrame([asdict(item) for item in history])
    frame["total_m"] = frame["total"] / 1_000_000
    latest = frame[frame["season"] == frame["season"].max()]
    fig = px.bar(
        latest,
        x="club_name",
        y=["equal_share", "merit_share", "audience_share"],
        facet_row="division",
        template="plotly_dark",
        labels={"club_name": "俱乐部", "value": "分成"},
    )
    fig.update_layout(height=620, margin=dict(l=8, r=8, t=30, b=80), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("一级联赛年度池18M，二级联赛5M；55%均分、25%竞技价值、20%受众价值。")


def _owners_tab(campaign: DeepCampaign) -> None:
    pyramid = campaign.football.pyramid
    division = {club_id: 1 for club_id in pyramid.premier_ids} | {club_id: 2 for club_id in pyramid.second_ids}
    rows = []
    for club_id, owner in pyramid.owners.items():
        rows.append(
            {
                "老板": owner.name,
                "俱乐部": campaign.engine.state.clubs[club_id].name,
                "级别": division[club_id],
                "财力": round(owner.wealth * 100),
                "野心": round(owner.ambition * 100),
                "耐心": round(owner.patience * 100),
                "足协关系": round(owner.relationship_with_fa * 100),
                "公众声誉": round(owner.reputation * 100),
                "被救记忆": owner.bailout_memory,
                "累计注资": _money(owner.cumulative_injection),
                "失信": owner.promises_broken,
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=470)
    st.caption("老板不是一次性事件：足协救过他、拒绝过他、逼他降薪，他都会在后续耐心、注资和关系中留下记忆。")


def _squad_tab(campaign: DeepCampaign) -> None:
    squad = campaign.football.current_squad
    left, right = st.columns([1, 1.8])
    with left:
        st.markdown("### 国家队征召画像")
        st.markdown(
            f"""
            <div class="card"><div class="muted">数据库计算阵容强度</div><div style="font-size:2.5rem;font-weight:900;color:#ecc65e">{squad.strength:.1f}</div>
            <span class="pill">平均年龄 {squad.average_age:.1f}</span><span class="pill">一级联赛 {squad.premier_share:.0%}</span><span class="pill">本土培养 {squad.homegrown_share:.0%}</span></div>
            """,
            unsafe_allow_html=True,
        )
        position_frame = pd.DataFrame(
            [
                {
                    "位置": position,
                    "平均能力": sum(member.ability for member in squad.members if member.position == position) / sum(member.position == position for member in squad.members),
                }
                for position in ("GK", "DEF", "MID", "ATT")
            ]
        )
        fig = go.Figure(go.Bar(x=position_frame["平均能力"], y=position_frame["位置"], orientation="h"))
        fig.update_layout(template="plotly_dark", height=280, xaxis_range=[35, 85], margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        rows = [
            {
                "球员": member.player_name,
                "俱乐部": member.club_name,
                "位置": member.position,
                "年龄": member.age,
                "能力": round(member.ability, 1),
                "体能": round(member.fitness),
                "士气": round(member.morale),
                "俱乐部出场": member.appearances,
                "征召评分": round(member.selection_score, 1),
            }
            for member in sorted(squad.members, key=lambda item: (item.position, -item.selection_score))
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=510)
    st.caption("征召综合球员能力、体能、士气、俱乐部出场、球队状态、联赛级别和本土培养身份。伤员不会被强行征召。")


def _events_tab(campaign: DeepCampaign) -> None:
    if campaign.current_decision:
        _decision(campaign)
    st.markdown("### 最近比赛")
    for result in reversed(campaign.football.recent_results[-10:]):
        st.markdown(
            f"<div class='fixture'><div class='home'>{result.home_name}</div><div class='score'>{result.home_goals} — {result.away_goals}</div><div class='away'>{result.away_name}</div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{result.competition} · 第{result.round_number}轮 · xG {result.home_xg:.2f}-{result.away_xg:.2f} · 现场 {result.attendance:,}")
    st.markdown("### 决策与审计")
    for line in reversed(campaign.engine.audit_log[-30:]):
        st.markdown(f"- `{line}`")


def main() -> None:
    st.set_page_config(page_title="Football Republic Deep", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")
    _css()
    campaign = _session()
    _controls(campaign)
    _header(campaign)
    _metrics(campaign)
    if campaign.current_decision:
        _decision(campaign)
    tabs = st.tabs(["联赛金字塔", "财务监管", "转播分成", "俱乐部老板", "国家队征召", "比赛与审计"])
    with tabs[0]:
        _pyramid_tab(campaign)
    with tabs[1]:
        _finance_tab(campaign)
    with tabs[2]:
        _media_tab(campaign)
    with tabs[3]:
        _owners_tab(campaign)
    with tabs[4]:
        _squad_tab(campaign)
    with tabs[5]:
        _events_tab(campaign)


if __name__ == "__main__":
    main()
