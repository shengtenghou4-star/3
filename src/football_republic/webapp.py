"""Streamlit presidential command centre for Football Republic."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from football_republic.campaign import Campaign, STRATEGIES, Strategy


PAGE_TITLE = "Football Republic · 主席指挥中心"


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
          --ink: #eaf2ff; --muted: #94a6bf; --gold: #efc75e;
          --cyan: #62d8ff; --green: #65e0a3; --red: #ff727f;
        }
        .stApp {
          background:
            radial-gradient(circle at 12% 8%, rgba(26,96,139,.24), transparent 28rem),
            radial-gradient(circle at 85% 15%, rgba(150,112,26,.18), transparent 28rem),
            linear-gradient(145deg, #050b14 0%, #091424 46%, #06101c 100%);
          color: var(--ink);
        }
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {max-width: 1500px; padding-top: 1.1rem; padding-bottom: 3rem;}
        .hero {
          position: relative; overflow: hidden;
          border: 1px solid rgba(239,199,94,.32); border-radius: 24px;
          padding: 28px 30px; margin-bottom: 18px;
          background: linear-gradient(110deg, rgba(10,30,50,.95), rgba(13,30,47,.82));
          box-shadow: 0 20px 70px rgba(0,0,0,.34);
        }
        .hero:after {
          content: ""; position: absolute; width: 280px; height: 280px;
          right: -70px; top: -145px; border: 34px solid rgba(98,216,255,.08);
          border-radius: 50%;
        }
        .hero-kicker {color: var(--gold); letter-spacing: .18em; font-size: .72rem; font-weight: 800;}
        .hero-title {font-size: 2.25rem; line-height: 1.05; font-weight: 850; margin: 8px 0 7px;}
        .hero-sub {color: var(--muted); max-width: 880px; font-size: .98rem;}
        [data-testid="stMetric"] {
          background: linear-gradient(165deg, rgba(18,34,57,.94), rgba(8,18,31,.94));
          border: 1px solid rgba(130,163,198,.18); padding: 16px 18px;
          border-radius: 18px; box-shadow: 0 10px 35px rgba(0,0,0,.22);
        }
        [data-testid="stMetricLabel"] {color: #9fb0c8;}
        [data-testid="stMetricValue"] {color: #f3f7ff; font-weight: 800;}
        .section-card {
          background: rgba(11,22,39,.82); border: 1px solid rgba(130,163,198,.17);
          border-radius: 18px; padding: 17px 19px; margin: 8px 0 14px;
        }
        .fixture {
          display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
          gap: 16px; padding: 13px 16px; margin: 8px 0; border-radius: 15px;
          background: linear-gradient(90deg, rgba(17,32,53,.88), rgba(9,20,35,.88));
          border: 1px solid rgba(126,158,190,.14);
        }
        .fixture .home {text-align: right; font-weight: 750;}
        .fixture .away {text-align: left; font-weight: 750;}
        .fixture .score {font-size: 1.1rem; color: var(--gold); font-weight: 900;}
        .pill {
          display: inline-block; padding: 5px 9px; border-radius: 999px;
          background: rgba(98,216,255,.11); color: #a9eaff;
          border: 1px solid rgba(98,216,255,.21); font-size: .75rem; margin-right: 5px;
        }
        .status-good {color: var(--green); font-weight: 800;}
        .status-warn {color: var(--gold); font-weight: 800;}
        .status-bad {color: var(--red); font-weight: 800;}
        .stTabs [data-baseweb="tab-list"] {gap: 8px;}
        .stTabs [data-baseweb="tab"] {
          background: rgba(14,29,49,.72); border-radius: 12px;
          padding: 8px 15px; border: 1px solid rgba(130,163,198,.12);
        }
        .stTabs [aria-selected="true"] {
          color: var(--gold); border-color: rgba(239,199,94,.35);
          background: rgba(61,49,19,.35);
        }
        [data-testid="stDataFrame"] {
          border: 1px solid rgba(130,163,198,.16); border-radius: 14px; overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _new_campaign(strategy: Strategy) -> Campaign:
    campaign = Campaign()
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
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">NATIONAL FOOTBALL GOVERNANCE SIMULATOR</div>
          <div class="hero-title">足球共和国 · 主席指挥中心</div>
          <div class="hero-sub">
            任期第 <b>{state.month}</b> / 24 个月 · 世界杯预选赛：
            <span class="status-{status_class}">{qualifier.qualification_status}</span>
            · 当前战略：{st.session_state.strategy.value}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_controls(campaign: Campaign) -> None:
    with st.sidebar:
        st.markdown("## 主席办公室")
        selected = st.selectbox(
            "执政路线",
            options=list(Strategy),
            format_func=lambda item: {
                Strategy.FOUNDATIONS: "基层筑基",
                Strategy.BALANCED: "均衡执政",
                Strategy.QUICK_RESULTS: "国家队速成",
            }[item],
            index=list(Strategy).index(st.session_state.strategy),
        )
        if selected != st.session_state.strategy:
            st.session_state.strategy = selected
            st.session_state.campaign = _new_campaign(selected)
            st.rerun()

        st.caption("推进月份会同时结算俱乐部现金流、联赛赛程、国家队窗口和政策交付。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "推进 1 月",
                use_container_width=True,
                disabled=campaign.engine.state.month >= 24,
            ):
                campaign.advance(1)
                st.rerun()
        with col2:
            if st.button(
                "推进 3 月",
                use_container_width=True,
                disabled=campaign.engine.state.month >= 24,
            ):
                campaign.advance(3)
                st.rerun()
        if st.button(
            "推演至任期结束",
            type="primary",
            use_container_width=True,
            disabled=campaign.engine.state.month >= 24,
        ):
            campaign.advance(24 - campaign.engine.state.month)
            st.rerun()
        if st.button("重新开局", use_container_width=True):
            st.session_state.campaign = _new_campaign(st.session_state.strategy)
            st.rerun()

        st.divider()
        st.markdown("### 任期进度")
        st.progress(campaign.engine.state.month / 24)
        st.caption(f"{campaign.engine.state.month}/24 个月")


def _metric_row(campaign: Campaign) -> None:
    state = campaign.engine.state
    qualifier = campaign.football.international
    cols = st.columns(6)
    cols[0].metric("足协国库", _money(state.treasury))
    cols[1].metric("球迷信任", _percent(state.fan_trust))
    cols[2].metric("联赛健康", _percent(state.league_financial_health))
    cols[3].metric("国家队实力", f"{state.national_team_strength:.1f}")
    cols[4].metric("预选赛排名", f"{qualifier.user_position}/6")
    cols[5].metric("青训环境", f"{state.youth_development_environment:.1f}")


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
    <div class="fixture">
      <div class="home">{result.home_name}</div>
      <div class="score">{result.home_goals} — {result.away_goals}</div>
      <div class="away">{result.away_name}</div>
    </div>
    """


def _overview_tab(campaign: Campaign) -> None:
    frame = _history_frame(campaign)
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown("### 国家足球资产曲线")
        if len(frame) > 1:
            chart = go.Figure()
            chart.add_trace(
                go.Scatter(
                    x=frame["month"], y=frame["fan_trust"] * 100,
                    name="球迷信任", mode="lines+markers",
                )
            )
            chart.add_trace(
                go.Scatter(
                    x=frame["month"],
                    y=frame["league_financial_health"] * 100,
                    name="联赛健康", mode="lines+markers",
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
                margin=dict(l=12, r=12, t=30, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,13,23,.35)",
                legend=dict(orientation="h", y=1.12),
            )
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("推进月份后，国家足球资产变化会显示在这里。")

    with right:
        st.markdown("### 主席任期判断")
        review = campaign.board_review()
        st.markdown(
            f"""
            <div class="section-card">
              <div style="color:#94a6bf;font-size:.8rem;">动态执委会评分</div>
              <div style="font-size:2.4rem;font-weight:900;color:#efc75e;">{review.score:.1f}</div>
              <div style="font-weight:800;">{review.verdict}</div>
              <hr style="border-color:rgba(130,163,198,.13)">
              <span class="pill">青训 {review.youth_change:+.2f}</span>
              <span class="pill">俱乐部存活 {review.club_solvent_share:.0%}</span>
              <span class="pill">预选赛第 {review.qualifier_position} 名</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for line in review.explanation:
            st.caption("• " + line)

    st.markdown("### 最近发生")
    results = campaign.football.recent_results[-6:]
    if results:
        for result in reversed(results):
            st.markdown(_fixture_html(result), unsafe_allow_html=True)
    else:
        st.caption("新任主席尚未迎来正式比赛。")


def _international_tab(campaign: Campaign) -> None:
    international = campaign.football.international
    top, side = st.columns([1.4, 1])
    with top:
        st.markdown("### 世界杯亚洲区最终阶段")
        st.dataframe(
            _standings_frame(international.sorted_table()),
            hide_index=True, use_container_width=True, height=310,
        )
    with side:
        user_row = next(
            row for row in international.sorted_table()
            if row.team_id == international.user_code
        )
        st.markdown("### 龙华国家队")
        st.markdown(
            f"""
            <div class="section-card">
              <div style="font-size:1.4rem;font-weight:900;">LONGHUA · LON</div>
              <div style="margin:8px 0;color:#94a6bf;">{international.qualification_status}</div>
              <span class="pill">{user_row.points} 分</span>
              <span class="pill">{user_row.goals_for}:{user_row.goals_against}</span>
              <span class="pill">实力 {campaign.engine.state.national_team_strength:.1f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 国家队比赛中心")
    user_results = [
        result for result in international.results
        if international.user_code in (result.home_id, result.away_id)
    ]
    if user_results:
        for result in reversed(user_results):
            st.markdown(_fixture_html(result), unsafe_allow_html=True)
            st.caption(
                f"第{result.round_number}轮 · xG {result.home_xg:.2f}–{result.away_xg:.2f} · "
                f"控球 {result.possession_home:.0f}%–{100-result.possession_home:.0f}% · "
                f"现场 {result.attendance:,}"
            )
    else:
        st.info("首个国家队比赛窗口在任期第3个月。")


def _league_tab(campaign: Campaign) -> None:
    league = campaign.football.domestic_league
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown(f"### 国家超级联赛 · 第{league.season}赛季")
        st.dataframe(
            _standings_frame(league.sorted_table()),
            hide_index=True, use_container_width=True, height=340,
        )
    with right:
        club_rows = []
        for club_id, club in campaign.engine.state.clubs.items():
            roster = campaign.football.rosters[club_id]
            club_rows.append(
                {
                    "俱乐部": club.name,
                    "阵容": roster.overall,
                    "现金": club.cash / 1_000_000,
                    "债务": club.debt / 1_000_000,
                    "财务健康": club.financial_health * 100,
                    "青训": club.academy_quality * 100,
                }
            )
        frame = pd.DataFrame(club_rows)
        fig = px.scatter(
            frame, x="财务健康", y="阵容", size="现金", color="青训",
            hover_name="俱乐部", template="plotly_dark", size_max=34,
        )
        fig.update_layout(
            height=340, margin=dict(l=10, r=10, t=25, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 最近联赛")
    league_results = league.results[-6:]
    if league_results:
        for result in reversed(league_results):
            st.markdown(_fixture_html(result), unsafe_allow_html=True)
            st.caption(
                f"xG {result.home_xg:.2f}–{result.away_xg:.2f} · "
                f"控球 {result.possession_home:.0f}%–{100-result.possession_home:.0f}% · "
                f"门票收入 {_money(result.gate_receipts)}"
            )
    else:
        st.info("联赛首轮将在任期第2个月举行。")


def _clubs_tab(campaign: Campaign) -> None:
    clubs = campaign.engine.state.clubs
    club_id = st.selectbox(
        "选择俱乐部", options=list(clubs),
        format_func=lambda key: clubs[key].name,
    )
    club = clubs[club_id]
    roster = campaign.football.rosters[club_id]
    cols = st.columns(6)
    cols[0].metric("阵容评分", f"{roster.overall:.1f}")
    cols[1].metric("攻击", f"{roster.attack:.1f}")
    cols[2].metric("中场", f"{roster.midfield:.1f}")
    cols[3].metric("防守", f"{roster.defense:.1f}")
    cols[4].metric("现金", _money(club.cash))
    cols[5].metric("欠薪", f"{club.wage_arrears_months} 月")

    fin, squad = st.columns([1, 1.65])
    with fin:
        st.markdown("### 经营与治理")
        labels = [
            "财务健康", "准入合规", "廉洁度", "老板耐心", "青训质量", "本土球员时间"
        ]
        values = [
            club.financial_health * 100,
            club.licensing_compliance * 100,
            club.integrity * 100,
            club.owner_patience * 100,
            club.academy_quality * 100,
            club.youth_minutes_share * 100,
        ]
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h"))
        fig.update_layout(
            template="plotly_dark", height=360,
            margin=dict(l=8, r=8, t=20, b=8), xaxis_range=[0, 100],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"月收入 {_money(club.monthly_revenue)} · 月工资 {_money(club.monthly_wage_bill)} · "
            f"债务 {_money(club.debt)} · 改革反应 {club.response_to_reform}"
        )

    with squad:
        st.markdown("### 一线队名单")
        players = pd.DataFrame(
            [
                {
                    "球员": player.name,
                    "位置": player.position,
                    "年龄": player.age,
                    "能力": round(player.ability, 1),
                    "潜力": round(player.potential, 1),
                    "体能": round(player.fitness, 0),
                    "士气": round(player.morale, 0),
                    "伤停(月)": player.injury_months,
                    "月薪(千)": round(player.monthly_wage / 1_000, 1),
                    "合同(月)": player.contract_months,
                    "本土培养": "是" if player.homegrown else "否",
                    "国籍": player.nationality,
                }
                for player in sorted(
                    roster.players,
                    key=lambda item: (item.position, -item.ability),
                )
            ]
        )
        st.dataframe(
            players, hide_index=True, use_container_width=True, height=430
        )


def _youth_tab(campaign: Campaign) -> None:
    rows = []
    for region in campaign.engine.state.regions.values():
        rows.append(
            {
                "地区": region.name,
                "注册青少年": region.registered_youth_players,
                "持证教练": region.licensed_youth_coaches,
                "球员/教练": region.players_per_coach,
                "年均比赛": region.annual_matches_per_player,
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
        fig = px.bar(
            frame, x="地区", y=["执行力", "廉洁度", "培养环境"],
            barmode="group", template="plotly_dark",
        )
        fig.update_layout(
            height=300, margin=dict(l=8, r=8, t=20, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)


def _audit_tab(campaign: Campaign) -> None:
    st.markdown("### 政策与比赛审计日志")
    st.caption("每个结果都能回到预算、执行、比赛或俱乐部现金流，不直接凭空跳分。")
    if campaign.engine.audit_log:
        for line in reversed(campaign.engine.audit_log):
            st.markdown(f"- `{line}`")
    else:
        st.info("尚无执行记录。")


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _ensure_session()
    campaign: Campaign = st.session_state.campaign
    _render_controls(campaign)
    _render_header(campaign)
    _metric_row(campaign)

    tabs = st.tabs(
        ["总统总览", "国际比赛", "职业联赛", "俱乐部", "青训地图", "审计日志"]
    )
    with tabs[0]:
        _overview_tab(campaign)
    with tabs[1]:
        _international_tab(campaign)
    with tabs[2]:
        _league_tab(campaign)
    with tabs[3]:
        _clubs_tab(campaign)
    with tabs[4]:
        _youth_tab(campaign)
    with tabs[5]:
        _audit_tab(campaign)


if __name__ == "__main__":
    main()
