"""Streamlit presidential command centre for Football Republic."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from football_republic.campaign import Campaign, STRATEGIES, Strategy


PAGE_TITLE = "Football Republic · 主席指挥中心"
STRATEGY_LABELS = {
    Strategy.FOUNDATIONS: "基层筑基",
    Strategy.BALANCED: "均衡执政",
    Strategy.QUICK_RESULTS: "国家队速成",
}


def _money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"¥{value / 1_000_000:,.1f}M"
    return f"¥{value:,.0f}"


def _percent(value: float) -> str:
    return f"{value:.0%}"


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink:#edf5ff; --muted:#94a8c3; --gold:#efc75e;
          --cyan:#62d8ff; --green:#62e0a1; --red:#ff7785;
        }
        .stApp {
          background:
            radial-gradient(circle at 12% 8%,rgba(22,94,140,.25),transparent 28rem),
            radial-gradient(circle at 88% 15%,rgba(155,111,22,.17),transparent 30rem),
            linear-gradient(145deg,#050b14 0%,#091425 48%,#06101c 100%);
          color:var(--ink);
        }
        #MainMenu,footer,header{visibility:hidden}.block-container{max-width:1500px;padding-top:1.05rem;padding-bottom:3rem}
        .hero{position:relative;overflow:hidden;border:1px solid rgba(239,199,94,.32);border-radius:24px;padding:27px 30px;margin-bottom:18px;background:linear-gradient(110deg,rgba(10,30,50,.96),rgba(13,30,47,.84));box-shadow:0 20px 70px rgba(0,0,0,.34)}
        .hero:after{content:"";position:absolute;width:280px;height:280px;right:-70px;top:-145px;border:34px solid rgba(98,216,255,.08);border-radius:50%}
        .hero-kicker{color:var(--gold);letter-spacing:.18em;font-size:.72rem;font-weight:800}.hero-title{font-size:2.3rem;line-height:1.05;font-weight:850;margin:8px 0 7px}.hero-sub{color:var(--muted);font-size:.98rem}
        [data-testid="stMetric"]{background:linear-gradient(165deg,rgba(18,34,57,.94),rgba(8,18,31,.94));border:1px solid rgba(130,163,198,.18);padding:15px 17px;border-radius:18px;box-shadow:0 10px 35px rgba(0,0,0,.22)}
        [data-testid="stMetricLabel"]{color:#9fb0c8}[data-testid="stMetricValue"]{color:#f3f7ff;font-weight:800}
        .card{background:rgba(11,22,39,.84);border:1px solid rgba(130,163,198,.17);border-radius:18px;padding:17px 19px;margin:8px 0 14px}
        .decision{background:linear-gradient(130deg,rgba(64,45,13,.53),rgba(14,27,45,.95));border:1px solid rgba(239,199,94,.38);border-radius:19px;padding:19px 20px;margin:10px 0 16px;box-shadow:0 14px 42px rgba(0,0,0,.23)}
        .decision-kicker{color:var(--gold);font-size:.72rem;letter-spacing:.12em;font-weight:900}.decision-title{font-size:1.25rem;font-weight:900;margin:6px 0}.muted{color:var(--muted)}
        .fixture{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:16px;padding:12px 15px;margin:7px 0;border-radius:15px;background:linear-gradient(90deg,rgba(17,32,53,.88),rgba(9,20,35,.88));border:1px solid rgba(126,158,190,.14)}
        .fixture .home{text-align:right;font-weight:750}.fixture .away{text-align:left;font-weight:750}.fixture .score{font-size:1.08rem;color:var(--gold);font-weight:900}
        .pill{display:inline-block;padding:5px 9px;border-radius:999px;background:rgba(98,216,255,.11);color:#a9eaff;border:1px solid rgba(98,216,255,.21);font-size:.75rem;margin:3px 5px 3px 0}
        .status-good{color:var(--green);font-weight:800}.status-warn{color:var(--gold);font-weight:800}.status-bad{color:var(--red);font-weight:800}
        .stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{background:rgba(14,29,49,.72);border-radius:12px;padding:8px 14px;border:1px solid rgba(130,163,198,.12)}.stTabs [aria-selected="true"]{color:var(--gold);border-color:rgba(239,199,94,.35);background:rgba(61,49,19,.35)}
        [data-testid="stDataFrame"]{border:1px solid rgba(130,163,198,.16);border-radius:14px;overflow:hidden}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _new_campaign(strategy: Strategy) -> Campaign:
    campaign = Campaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    return campaign


def _ensure_session() -> None:
    if "strategy" not in st.session_state:
        st.session_state.strategy = Strategy.BALANCED
    if "campaign" not in st.session_state:
        st.session_state.campaign = _new_campaign(st.session_state.strategy)


def _render_header(campaign: Campaign) -> None:
    state = campaign.engine.state
    qualifier = campaign.football.international
    status_class = (
        "good" if qualifier.user_position <= 2
        else "warn" if qualifier.user_position == 3
        else "bad"
    )
    pending = " · 有待决事项" if campaign.current_decision else ""
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">NATIONAL FOOTBALL GOVERNANCE SIMULATOR</div>
          <div class="hero-title">足球共和国 · 主席指挥中心</div>
          <div class="hero-sub">任期第 <b>{state.month}</b> / 24 个月 · 世界杯预选赛：
          <span class="status-{status_class}">{qualifier.qualification_status}</span>
          · 当前战略：{STRATEGY_LABELS[campaign.strategy]}{pending}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_decision_controls(campaign: Campaign) -> None:
    decision = campaign.current_decision
    if decision is None:
        return
    st.markdown("### ⚠️ 主席必须拍板")
    st.markdown(
        f"""
        <div class="decision">
          <div class="decision-kicker">MONTH {decision.month} · CABINET DECISION</div>
          <div class="decision-title">{decision.title}</div>
          <div class="muted">{decision.narrative}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    option_id = st.radio(
        "处理方案",
        options=[option.id for option in decision.options],
        format_func=lambda item: next(
            option.title for option in decision.options if option.id == item
        ),
        key=f"decision_{decision.id}",
    )
    option = next(item for item in decision.options if item.id == option_id)
    st.caption(option.summary)
    st.warning("风险：" + option.risk)
    if st.button("签署主席决定", type="primary", use_container_width=True):
        campaign.resolve_decision(option_id)
        st.rerun()


def _render_controls(campaign: Campaign) -> None:
    with st.sidebar:
        st.markdown("## 主席办公室")
        selected = st.selectbox(
            "执政路线",
            options=list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=list(Strategy).index(st.session_state.strategy),
        )
        if selected != st.session_state.strategy:
            st.session_state.strategy = selected
            st.session_state.campaign = _new_campaign(selected)
            st.rerun()

        if campaign.current_decision:
            st.error("当前存在待决事项，必须先拍板才能推进时间。")
        st.caption("每月同时结算政策交付、俱乐部财务、转会、联赛和国家队窗口。")
        disabled = campaign.engine.state.month >= 24 or campaign.current_decision is not None
        left, right = st.columns(2)
        with left:
            if st.button("推进 1 月", use_container_width=True, disabled=disabled):
                campaign.advance(1, interactive=True)
                st.rerun()
        with right:
            if st.button("推进 3 月", use_container_width=True, disabled=disabled):
                campaign.advance(3, interactive=True)
                st.rerun()
        if st.button("推进至下一决策", type="primary", use_container_width=True, disabled=disabled):
            campaign.advance(24 - campaign.engine.state.month, interactive=True)
            st.rerun()
        if st.button("重新开局", use_container_width=True):
            st.session_state.campaign = _new_campaign(st.session_state.strategy)
            st.rerun()

        st.divider()
        st.markdown("### 任期进度")
        st.progress(campaign.engine.state.month / 24)
        st.caption(f"{campaign.engine.state.month}/24 个月")
        st.metric("第二年度新增收入", _money(campaign.annual_income_received))
        st.metric("已完成转会", str(len(campaign.transfer_market.history)))


def _metric_row(campaign: Campaign) -> None:
    state = campaign.engine.state
    qualifier = campaign.football.international
    cols = st.columns(7)
    cols[0].metric("足协国库", _money(state.treasury))
    cols[1].metric("政治资本", _percent(state.political_capital))
    cols[2].metric("球迷信任", _percent(state.fan_trust))
    cols[3].metric("廉洁声誉", _percent(state.integrity_reputation))
    cols[4].metric("联赛健康", _percent(state.league_financial_health))
    cols[5].metric("国家队实力", f"{state.national_team_strength:.1f}")
    cols[6].metric("预选赛排名", f"{qualifier.user_position}/6")


def _history_frame(campaign: Campaign) -> pd.DataFrame:
    return pd.DataFrame([asdict(item) for item in campaign.monthly_history])


def _standings_frame(rows: list[object]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "#": index,
                "球队": row.team_name,
                "赛": row.played,
                "胜": row.won,
                "平": row.drawn,
                "负": row.lost,
                "进球": row.goals_for,
                "失球": row.goals_against,
                "净胜": row.goal_difference,
                "积分": row.points,
                "近5场": " ".join(row.form),
            }
            for index, row in enumerate(rows, start=1)
        ]
    )


def _fixture_html(result: object) -> str:
    return f"""
    <div class="fixture"><div class="home">{result.home_name}</div>
    <div class="score">{result.home_goals} — {result.away_goals}</div>
    <div class="away">{result.away_name}</div></div>
    """


def _overview_tab(campaign: Campaign) -> None:
    if campaign.current_decision:
        _render_decision_controls(campaign)
    frame = _history_frame(campaign)
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown("### 国家足球资产曲线")
        if len(frame) > 1:
            chart = go.Figure()
            for column, name in (
                ("fan_trust", "球迷信任"),
                ("integrity_reputation", "廉洁声誉"),
                ("league_financial_health", "联赛健康"),
            ):
                chart.add_trace(
                    go.Scatter(
                        x=frame["month"], y=frame[column] * 100,
                        name=name, mode="lines+markers",
                    )
                )
            chart.add_trace(
                go.Scatter(
                    x=frame["month"], y=frame["youth_environment"],
                    name="青训环境", mode="lines+markers",
                )
            )
            chart.update_layout(
                template="plotly_dark", height=390,
                margin=dict(l=10, r=10, t=28, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,13,23,.35)",
                legend=dict(orientation="h", y=1.12),
            )
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("推进月份后，资产变化会显示在这里。")
    with right:
        review = campaign.board_review()
        st.markdown("### 动态执委会判断")
        st.markdown(
            f"""
            <div class="card"><div class="muted">当前留任评分</div>
            <div style="font-size:2.5rem;font-weight:900;color:#efc75e">{review.score:.1f}</div>
            <div style="font-weight:850">{review.verdict}</div><hr style="border-color:rgba(130,163,198,.13)">
            <span class="pill">青训 {review.youth_change:+.2f}</span>
            <span class="pill">俱乐部存活 {review.club_solvent_share:.0%}</span>
            <span class="pill">预选赛第 {review.qualifier_position} 名</span></div>
            """,
            unsafe_allow_html=True,
        )
        for line in review.explanation:
            st.caption("• " + line)

    st.markdown("### 最近发生")
    recent = campaign.football.recent_results[-6:]
    if recent:
        for result in reversed(recent):
            st.markdown(_fixture_html(result), unsafe_allow_html=True)
    else:
        st.caption("正式比赛尚未开始。")


def _cabinet_tab(campaign: Campaign) -> None:
    if campaign.current_decision:
        _render_decision_controls(campaign)
    finance, history = st.columns([1, 1.4])
    with finance:
        st.markdown("### 年度足球财政")
        if campaign.finance_reports:
            rows = [
                {
                    "月份": item.month,
                    "中央拨款": item.public_grant / 1_000_000,
                    "商业分成": item.commercial_distribution / 1_000_000,
                    "成绩奖金": item.performance_bonus / 1_000_000,
                    "廉洁奖金": item.integrity_bonus / 1_000_000,
                    "合计": item.total_income / 1_000_000,
                }
                for item in campaign.finance_reports
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.info("第二年度收入将在第12个月结算。")
    with history:
        st.markdown("### 主席决定记录")
        if campaign.decision_history:
            rows = [
                {
                    "月份": item.month,
                    "事项": item.title,
                    "决定": item.option_title,
                    "主要后果": "；".join(item.effects),
                }
                for item in campaign.decision_history
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=290)
        else:
            st.info("首个重大决策将在第4个月出现。")

    st.markdown("### 转会市场流水")
    if campaign.transfer_market.history:
        rows = [
            {
                "月份": item.month,
                "球员": item.player_name,
                "位置": item.position,
                "年龄": item.age,
                "能力/潜力": f"{item.ability:.1f}/{item.potential:.1f}",
                "卖方": item.seller_name,
                "买方": item.buyer_name,
                "转会费": _money(item.fee),
                "新月薪": _money(item.new_wage),
                "政策": item.policy,
            }
            for item in reversed(campaign.transfer_market.history)
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=330)
    else:
        st.info("第6个月确定转会政策后开启首个转会窗。")


def _international_tab(campaign: Campaign) -> None:
    international = campaign.football.international
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("### 世界杯亚洲区最终阶段")
        st.dataframe(_standings_frame(international.sorted_table()), hide_index=True, use_container_width=True, height=310)
    with right:
        user_row = next(row for row in international.sorted_table() if row.team_id == international.user_code)
        st.markdown("### 龙华国家队")
        st.markdown(
            f"""
            <div class="card"><div style="font-size:1.4rem;font-weight:900">LONGHUA · LON</div>
            <div class="muted" style="margin:8px 0">{international.qualification_status}</div>
            <span class="pill">{user_row.points} 分</span><span class="pill">{user_row.goals_for}:{user_row.goals_against}</span>
            <span class="pill">实力 {campaign.engine.state.national_team_strength:.1f}</span></div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("### 国家队比赛中心")
    results = [result for result in international.results if international.user_code in (result.home_id, result.away_id)]
    if results:
        for result in reversed(results):
            st.markdown(_fixture_html(result), unsafe_allow_html=True)
            st.caption(
                f"第{result.round_number}轮 · xG {result.home_xg:.2f}–{result.away_xg:.2f} · "
                f"控球 {result.possession_home:.0f}%–{100-result.possession_home:.0f}% · 现场 {result.attendance:,}"
            )
    else:
        st.info("首个国家队比赛窗口在第3个月。")


def _league_tab(campaign: Campaign) -> None:
    league = campaign.football.domestic_league
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown(f"### 国家超级联赛 · 第{league.season}赛季")
        st.dataframe(_standings_frame(league.sorted_table()), hide_index=True, use_container_width=True, height=340)
    with right:
        rows = []
        for club_id, club in campaign.engine.state.clubs.items():
            roster = campaign.football.rosters[club_id]
            rows.append(
                {
                    "俱乐部": club.name,
                    "阵容": roster.overall,
                    "现金": club.cash / 1_000_000,
                    "财务健康": club.financial_health * 100,
                    "青训": club.academy_quality * 100,
                }
            )
        frame = pd.DataFrame(rows)
        fig = px.scatter(
            frame, x="财务健康", y="阵容", size="现金", color="青训",
            hover_name="俱乐部", template="plotly_dark", size_max=34,
        )
        fig.update_layout(height=340, margin=dict(l=8, r=8, t=22, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 最近联赛")
    for result in reversed(league.results[-6:]):
        st.markdown(_fixture_html(result), unsafe_allow_html=True)
        st.caption(
            f"xG {result.home_xg:.2f}–{result.away_xg:.2f} · 控球 {result.possession_home:.0f}%–{100-result.possession_home:.0f}% · 门票 {_money(result.gate_receipts)}"
        )


def _clubs_tab(campaign: Campaign) -> None:
    clubs = campaign.engine.state.clubs
    club_id = st.selectbox("选择俱乐部", options=list(clubs), format_func=lambda key: clubs[key].name)
    club = clubs[club_id]
    roster = campaign.football.rosters[club_id]
    cols = st.columns(7)
    for column, label, value in zip(
        cols,
        ("阵容", "攻击", "中场", "防守", "现金", "债务", "欠薪"),
        (f"{roster.overall:.1f}", f"{roster.attack:.1f}", f"{roster.midfield:.1f}", f"{roster.defense:.1f}", _money(club.cash), _money(club.debt), f"{club.wage_arrears_months}月"),
    ):
        column.metric(label, value)
    left, right = st.columns([1, 1.65])
    with left:
        labels = ["财务健康", "准入合规", "廉洁度", "老板耐心", "青训质量", "本土时间"]
        values = [club.financial_health * 100, club.licensing_compliance * 100, club.integrity * 100, club.owner_patience * 100, club.academy_quality * 100, club.youth_minutes_share * 100]
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h"))
        fig.update_layout(template="plotly_dark", height=360, margin=dict(l=8, r=8, t=20, b=8), xaxis_range=[0, 100], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"月收入 {_money(club.monthly_revenue)} · 月工资 {_money(club.monthly_wage_bill)} · 改革反应 {club.response_to_reform}")
    with right:
        players = pd.DataFrame(
            [
                {
                    "球员": player.name,
                    "位置": player.position,
                    "年龄": player.age,
                    "能力": round(player.ability, 1),
                    "潜力": round(player.potential, 1),
                    "体能": round(player.fitness),
                    "士气": round(player.morale),
                    "伤停(月)": player.injury_months,
                    "月薪(千)": round(player.monthly_wage / 1_000, 1),
                    "合同(月)": player.contract_months,
                    "本土培养": "是" if player.homegrown else "否",
                    "国籍": player.nationality,
                }
                for player in sorted(roster.players, key=lambda item: (item.position, -item.ability))
            ]
        )
        st.dataframe(players, hide_index=True, use_container_width=True, height=430)


def _youth_tab(campaign: Campaign) -> None:
    rows = []
    for region in campaign.engine.state.regions.values():
        rows.append(
            {
                "地区": region.name,
                "注册青少年": region.registered_youth_players,
                "持证教练": region.licensed_youth_coaches,
                "球员/教练": round(region.players_per_coach, 1),
                "年均比赛": round(region.annual_matches_per_player, 1),
                "学校项目": region.school_programs,
                "执行力": region.execution_capacity * 100,
                "廉洁度": region.integrity * 100,
                "培养环境": region.development_environment,
            }
        )
    frame = pd.DataFrame(rows)
    left, right = st.columns([1.35, 1])
    with left:
        st.dataframe(frame, hide_index=True, use_container_width=True, height=250)
    with right:
        fig = px.bar(frame, x="地区", y=["执行力", "廉洁度", "培养环境"], barmode="group", template="plotly_dark")
        fig.update_layout(height=300, margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,13,23,.35)")
        st.plotly_chart(fig, use_container_width=True)


def _audit_tab(campaign: Campaign) -> None:
    st.markdown("### 政策、交易与比赛审计日志")
    st.caption("每个结果都能回到预算、决策、俱乐部现金流、球员交易或比赛事件。")
    if campaign.engine.audit_log:
        for line in reversed(campaign.engine.audit_log):
            st.markdown(f"- `{line}`")
    else:
        st.info("尚无执行记录。")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="⚽", layout="wide", initial_sidebar_state="expanded")
    _inject_css()
    _ensure_session()
    campaign: Campaign = st.session_state.campaign
    _render_controls(campaign)
    _render_header(campaign)
    _metric_row(campaign)

    tabs = st.tabs(["总统总览", "内阁与转会", "国际比赛", "职业联赛", "俱乐部", "青训地图", "审计日志"])
    with tabs[0]:
        _overview_tab(campaign)
    with tabs[1]:
        _cabinet_tab(campaign)
    with tabs[2]:
        _international_tab(campaign)
    with tabs[3]:
        _league_tab(campaign)
    with tabs[4]:
        _clubs_tab(campaign)
    with tabs[5]:
        _youth_tab(campaign)
    with tabs[6]:
        _audit_tab(campaign)


if __name__ == "__main__":
    main()
