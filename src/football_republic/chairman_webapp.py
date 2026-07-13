"""Player-facing Streamlit office for one fixed football-association chairman."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.campaign import Strategy
from football_republic.chairman_career import ChairmanCareer
from football_republic.pyramid_webapp import _css


STRATEGY_LABELS = {
    Strategy.FOUNDATIONS: "基层筑基",
    Strategy.BALANCED: "均衡治理",
    Strategy.QUICK_RESULTS: "短期成绩",
}


def _money(value: float) -> str:
    return f"¥{value / 1_000_000:,.2f}M" if abs(value) >= 1_000_000 else f"¥{value:,.0f}"


def _session() -> ChairmanCareer:
    if "chairman_strategy" not in st.session_state:
        st.session_state.chairman_strategy = Strategy.BALANCED
    if "chairman_career" not in st.session_state:
        st.session_state.chairman_career = ChairmanCareer(
            strategy=st.session_state.chairman_strategy,
            max_terms=10,
        )
    return st.session_state.chairman_career


def _sidebar(career: ChairmanCareer) -> None:
    with st.sidebar:
        st.markdown("## 主席办公室")
        st.markdown(f"**{career.player_name}**  \n{STRATEGY_LABELS[career.player_strategy]}")
        if career.player_active:
            st.success("你仍在任")
            st.caption(
                f"第{career.term_index}届制度任期 · 第{career.local_month}/24月 · 全球第{career.global_month}月"
            )
            blocked = career.player_decision is not None
            if blocked:
                st.warning("存在待签文件，时间已经冻结。")
            left, right = st.columns(2)
            if left.button("推进1月", use_container_width=True, disabled=blocked):
                career.advance(1, interactive=True)
                st.rerun()
            if right.button("推进3月", use_container_width=True, disabled=blocked):
                career.advance(3, interactive=True)
                st.rerun()
            if st.button("推进至下一份待签文件", type="primary", use_container_width=True, disabled=blocked):
                career.advance(24, interactive=True)
                st.rerun()
        else:
            st.error("你的主席生涯已经结束")
            st.caption(career.career_end_reason or "已离任")
            if career.can_observe:
                left, right = st.columns(2)
                if left.button("旁观6月", use_container_width=True):
                    career.observe(6)
                    st.rerun()
                if right.button("旁观1年", use_container_width=True):
                    career.observe(12)
                    st.rerun()
                if st.button("旁观至历史终点", use_container_width=True):
                    career.observe(career.max_terms * 24)
                    st.rerun()

        st.divider()
        st.download_button(
            "下载主席生涯存档",
            data=career.to_json(),
            file_name=f"football-republic-chairman-m{career.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入主席生涯JSON", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = ChairmanCareer.from_json(uploaded.getvalue().decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.chairman_career = restored
                st.success("主席身份、任期和国家足球状态验证通过。")
                st.rerun()

        st.divider()
        strategy = st.selectbox(
            "重开时选择路线",
            list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=list(Strategy).index(st.session_state.chairman_strategy),
        )
        if st.button("重开主席生涯", use_container_width=True):
            st.session_state.chairman_strategy = strategy
            st.session_state.chairman_career = ChairmanCareer(strategy=strategy, max_terms=10)
            st.rerun()


def _header(career: ChairmanCareer) -> None:
    status = "在任主席" if career.player_active else "已离任 · 旁观模式"
    st.markdown(
        f"""
        <div class="hero">
          <div class="kicker">FOOTBALL ASSOCIATION CHAIRMAN CAREER</div>
          <div class="title">国家足协主席模拟器</div>
          <div class="sub">你始终扮演 <b>{career.player_name}</b> · {status} · 其他人物均为自主行动的NPC</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _metrics(career: ChairmanCareer) -> None:
    state = career.current_campaign.engine.state
    cols = st.columns(7)
    values = (
        ("足协国库", _money(state.treasury)),
        ("政治资本", f"{state.political_capital:.0%}"),
        ("球迷信任", f"{state.fan_trust:.0%}"),
        ("廉洁声誉", f"{state.integrity_reputation:.0%}"),
        ("联赛健康", f"{state.league_financial_health:.0%}"),
        ("青训环境", f"{state.youth_development_environment:.1f}"),
        ("国家队实力", f"{state.national_team_strength:.1f}"),
    )
    for column, (label, value) in zip(cols, values):
        column.metric(label, value)


def _decision(career: ChairmanCareer) -> None:
    decision = career.player_decision
    if decision is None:
        return
    st.markdown(
        f"""
        <div class="decision">
          <div class="kicker">PRESIDENTIAL FILE · G{career.global_month}</div>
          <h3>{decision.title}</h3>
          <div class="muted">{decision.narrative}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    option_id = st.radio(
        "主席批示",
        [item.id for item in decision.options],
        format_func=lambda value: next(item.title for item in decision.options if item.id == value),
        key=f"chairman-{decision.id}",
    )
    option = next(item for item in decision.options if item.id == option_id)
    st.caption(option.summary)
    st.warning("风险：" + option.risk)
    if st.button("签署主席决定", type="primary"):
        career.resolve_decision(option_id)
        st.rerun()


def _office_tab(career: ChairmanCareer) -> None:
    st.markdown("### 今日待办与主席简报")
    _decision(career)
    latest = list(reversed(career.briefings[-30:]))
    if not latest:
        st.info("秘书处暂时没有新增简报。")
        return
    for item in latest:
        badge = "🔴" if item.urgency in {"最高", "高"} else "🟠" if item.urgency == "中" else "⚪"
        st.markdown(
            f"""
            <div class="card">
              <div class="kicker">{badge} {item.category} · G{item.global_month} · 可信度{item.confidence}</div>
              <h4>{item.title}</h4>
              <div>{item.summary}</div>
              <div class="muted" style="margin-top:8px">来源：{item.source}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _overview_tab(career: ChairmanCareer) -> None:
    state = career.current_campaign.engine.state
    st.markdown("### 国家足球全景")
    rows = []
    for region in state.regions.values():
        rows.append(
            {
                "地区": region.name,
                "注册青少年": region.registered_youth_players,
                "持证教练": region.licensed_youth_coaches,
                "人均年比赛": round(region.annual_matches_per_player, 1),
                "发展环境": round(region.development_environment, 1),
                "执行能力": f"{region.execution_capacity:.0%}",
                "家长支持": f"{region.parent_support:.0%}",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    frame = pd.DataFrame(
        {
            "指标": ["青训环境", "国家队实力", "联赛健康", "廉洁声誉", "球迷信任"],
            "数值": [
                state.youth_development_environment,
                state.national_team_strength,
                state.league_financial_health * 100,
                state.integrity_reputation * 100,
                state.fan_trust * 100,
            ],
        }
    )
    fig = px.bar(frame, x="指标", y="数值", template="plotly_dark")
    fig.update_layout(
        height=330,
        yaxis_range=[0, 100],
        margin=dict(l=8, r=8, t=25, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,13,23,.35)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _national_team_tab(career: ChairmanCareer) -> None:
    football = career.current_campaign.football
    squad = football.current_squad
    cols = st.columns(4)
    cols[0].metric("预选赛排名", f"{football.international.user_position}/6")
    cols[1].metric("当前阵容强度", f"{squad.strength:.1f}")
    cols[2].metric("平均年龄", f"{squad.average_age:.1f}")
    cols[3].metric("一级联赛球员", f"{squad.premier_share:.0%}")

    st.markdown("### 当前26人名单")
    members = pd.DataFrame(
        [
            {
                "球员": item.player_name,
                "俱乐部": item.club_name,
                "位置": item.position,
                "年龄": item.age,
                "能力": round(item.ability, 1),
                "体能": round(item.fitness),
                "出场": item.appearances,
            }
            for item in squad.members
        ]
    )
    st.dataframe(members, hide_index=True, use_container_width=True, height=430)

    st.markdown("### 最近国家队比赛")
    results = [item for item in football.international.results[-10:]]
    if results:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "月份": item.month,
                        "主队": item.home_name,
                        "比分": item.scoreline,
                        "客队": item.away_name,
                    }
                    for item in reversed(results)
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )


def _league_tab(career: ChairmanCareer) -> None:
    pyramid = career.current_campaign.football.pyramid
    left, right = st.columns(2)
    for column, league, title in (
        (left, pyramid.premier, "国家超级联赛"),
        (right, pyramid.second, "国家冠军联赛"),
    ):
        with column:
            st.markdown(f"### {title}")
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
                for index, row in enumerate(league.sorted_table(), start=1)
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("### 俱乐部监管摘要")
    state = career.current_campaign.engine.state
    club_rows = []
    for club in state.clubs.values():
        condition = (
            "失去牌照"
            if club.license_status == "excluded"
            else "托管中"
            if club.license_status == "administration"
            else "严重欠薪"
            if club.wage_arrears_months >= 3
            else "存在压力"
            if club.financial_health < 0.35
            else "基本稳定"
        )
        club_rows.append(
            {
                "俱乐部": club.name,
                "现金": _money(club.cash),
                "债务": _money(club.debt),
                "工资/收入": round(club.monthly_wage_bill / max(club.monthly_revenue, 1), 2),
                "欠薪月": club.wage_arrears_months,
                "监管状态": condition,
            }
        )
    st.dataframe(pd.DataFrame(club_rows), hide_index=True, use_container_width=True, height=430)


def _grassroots_tab(career: ChairmanCareer) -> None:
    state = career.current_campaign.engine.state
    cols = st.columns(4)
    cols[0].metric("注册青少年", f"{state.registered_youth_players:,}")
    cols[1].metric("持证教练", f"{state.licensed_youth_coaches:,}")
    cols[2].metric("青训环境", f"{state.youth_development_environment:.1f}")
    cols[3].metric(
        "本季毕业生",
        str(len(career.current_campaign.football.economy.lifecycle.intake_history)),
    )
    st.markdown("### 地区青训执行")
    rows = [
        {
            "地区": region.name,
            "青少年覆盖": f"{region.youth_access_rate:.1%}",
            "教练覆盖": f"{region.coach_coverage:.1%}",
            "场地覆盖": f"{region.pitch_access:.1%}",
            "人均比赛": round(region.annual_matches_per_player, 1),
            "学校项目": region.school_programs,
            "俱乐部青训": region.club_academies,
        }
        for region in state.regions.values()
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    intake = career.current_campaign.football.economy.lifecycle.intake_history
    if intake:
        st.markdown("### 最近青训毕业生")
        st.dataframe(
            pd.DataFrame([asdict(item) for item in reversed(intake[-20:])]),
            hide_index=True,
            use_container_width=True,
        )


def _finance_people_tab(career: ChairmanCareer) -> None:
    state = career.current_campaign.engine.state
    top = st.columns(4)
    top[0].metric("国库", _money(state.treasury))
    top[1].metric("健康俱乐部", f"{state.solvent_club_share:.0%}")
    top[2].metric("公开案件", str(len(career.public_case_docket())))
    top[3].metric("内阁职位", str(len(career.cabinet)))

    st.markdown("### 主席可获得的人事评估")
    st.dataframe(
        pd.DataFrame([asdict(item) for item in career.official_assessments()]),
        hide_index=True,
        use_container_width=True,
    )
    st.caption("页面不显示官员隐藏廉洁度、私人关系网强度或定罪概率。")

    docket = career.public_case_docket()
    st.markdown("### 公开案件程序")
    if docket:
        st.dataframe(pd.DataFrame(docket), hide_index=True, use_container_width=True, height=360)
    else:
        st.info("目前没有进入公开程序的案件。")


def _politics_tab(career: ChairmanCareer) -> None:
    st.markdown("### 政治支持与连任判断")
    signals = pd.DataFrame([asdict(item) for item in career.stakeholder_signals()])
    st.dataframe(signals, hide_index=True, use_container_width=True, height=410)
    st.caption("这是主席团队根据接触、公开表态和近期行动形成的判断，不是集团后台真实数值。")

    stability = career.coalition_stability
    label = (
        "稳固多数"
        if stability >= 0.64
        else "基本可控"
        if stability >= 0.50
        else "脆弱联盟"
        if stability >= 0.36
        else "接近破裂"
    )
    cols = st.columns(4)
    cols[0].metric("当前任期", f"第{career.term_index}届")
    cols[1].metric("本届进度", f"{career.local_month}/24月")
    cols[2].metric("连续任期", str(career.current_president.terms_served))
    cols[3].metric("联盟判断", label)
    st.info(
        "连任不是自动发生：足球董事会表现、联盟支持、治理能力和连续三届上限会共同决定你能否继续执政。"
    )


def _legacy_tab(career: ChairmanCareer) -> None:
    if career.player_active:
        st.markdown("### 进行中的主席生涯")
        st.info("你的最终遗产将在辞职、罢免、败选、任期上限或历史终点时生成。")
        st.metric("已执政月份", str(career.global_month - career.player_start_month))
        st.metric("已签重大决定", str(len(career._decision_log)))
        return
    report = career.legacy_report
    if report is None:
        return
    st.markdown(f"## {report.legacy_grade}")
    st.error(f"离任原因：{report.exit_reason}")
    cols = st.columns(5)
    cols[0].metric("执政月份", str(report.months_in_office))
    cols[1].metric("完整任期", str(report.completed_terms))
    cols[2].metric("董事会评分", f"{report.board_score:.1f}")
    cols[3].metric("政治评分", f"{report.political_score:.1f}")
    cols[4].metric("重大决定", str(report.decisions_taken))

    st.markdown("### 离任时国家足球状态")
    st.dataframe(
        pd.DataFrame(
            [
                {"指标": "国库", "结果": _money(report.treasury)},
                {"指标": "球迷信任", "结果": f"{report.fan_trust:.0%}"},
                {"指标": "廉洁声誉", "结果": f"{report.integrity_reputation:.0%}"},
                {"指标": "国家队实力", "结果": f"{report.national_team_strength:.1f}"},
                {"指标": "预选赛排名", "结果": f"{report.qualifier_position}/6"},
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.markdown("### 后续历史")
    st.caption(
        "你可以继续旁观继任者，但旁观模式不会向你提供任何主席决策按钮。"
    )
    if career.term_records:
        st.dataframe(
            pd.DataFrame([asdict(item) for item in career.term_records]),
            hide_index=True,
            use_container_width=True,
            height=360,
        )


def main() -> None:
    st.set_page_config(
        page_title="Football Republic Chairman",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    career = _session()
    _sidebar(career)
    _header(career)
    _metrics(career)
    tabs = st.tabs(
        [
            "主席办公室",
            "国家足球全景",
            "国家队与竞赛",
            "职业联赛与俱乐部",
            "青训与基层",
            "财政、审计与人事",
            "政治支持与连任",
            "主席生涯与遗产",
        ]
    )
    with tabs[0]:
        _office_tab(career)
    with tabs[1]:
        _overview_tab(career)
    with tabs[2]:
        _national_team_tab(career)
    with tabs[3]:
        _league_tab(career)
    with tabs[4]:
        _grassroots_tab(career)
    with tabs[5]:
        _finance_people_tab(career)
    with tabs[6]:
        _politics_tab(career)
    with tabs[7]:
        _legacy_tab(career)


if __name__ == "__main__":
    main()
