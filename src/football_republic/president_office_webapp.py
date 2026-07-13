"""Player-facing Streamlit office for one fixed football-association president."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from football_republic.advanced_webapp import _competition_tab
from football_republic.campaign import Strategy
from football_republic.generational_webapp import (
    _commercial_tab,
    _insolvency_tab,
    _lifecycle_tab,
)
from football_republic.history_webapp import _clubs_tab, _seasons_tab
from football_republic.president_career import PresidentCareerGame
from football_republic.pyramid_webapp import (
    _css,
    _finance_tab,
    _pyramid_tab,
    _squad_tab,
)


def _session() -> PresidentCareerGame:
    if "president_career_game" not in st.session_state:
        st.session_state.president_career_game = PresidentCareerGame(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.president_career_game


def _rerun() -> None:
    st.rerun()


def _sidebar(game: PresidentCareerGame) -> None:
    with st.sidebar:
        st.markdown("## 足协主席办公室")
        if game.can_act:
            st.success(f"你正在扮演：{game.player_name}")
            st.caption(
                f"第{game.global_year}年 · 制度任期第{game.term_index}届 · "
                f"本届M{game.local_month}"
            )
            left, right = st.columns(2)
            if left.button("推进1月", use_container_width=True):
                game.advance(1, interactive=True)
                _rerun()
            if right.button("推进至待办", use_container_width=True):
                game.advance(24, interactive=True)
                _rerun()
            st.info("你只能处理现任主席依法有权决定的事项。")
        else:
            st.error("你的主席政治生涯已经结束。")
            st.markdown(
                f"**离任原因：** {game.career_end_reason or '—'}  \n"
                f"**继任政府：** {game.successor_name}"
            )
            st.caption("后续可以旁观，但不能替继任主席作决定。")
            left, right = st.columns(2)
            if left.button("旁观3月", use_container_width=True, disabled=game.history_finished):
                game.observe(3)
                _rerun()
            if right.button("旁观1年", use_container_width=True, disabled=game.history_finished):
                game.observe_years(1)
                _rerun()
            if st.button("旁观至20年结束", use_container_width=True, disabled=game.history_finished):
                game.observe_to_end()
                _rerun()

        st.divider()
        st.download_button(
            "下载主席生涯JSON存档",
            data=game.to_json(),
            file_name=f"football-republic-president-m{game.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入主席生涯存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = PresidentCareerGame.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.president_career_game = restored
                st.success("主席身份、历史世界和权限状态验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "新生涯执政路线",
            options=[item.value for item in Strategy],
            index=1,
        )
        if st.button("开始新的主席生涯", use_container_width=True):
            st.session_state.president_career_game = PresidentCareerGame(
                Strategy(reset_strategy),
                max_terms=10,
            )
            _rerun()


def _header(game: PresidentCareerGame) -> None:
    state = game.current_campaign.engine.state
    politics = game.current_campaign.politics
    role = (
        f"你是现任足协主席：{game.player_name}"
        if game.can_act
        else f"{game.player_name}主席生涯档案 · 当前由{game.current_president.name}执政"
    )
    st.markdown(
        f"# 足球共和国 · 主席办公室  "
        f"<span style='font-size:.55em;opacity:.68'>{role}</span>",
        unsafe_allow_html=True,
    )
    top = st.columns(7)
    top[0].metric("生涯状态", "在任" if game.can_act else "已离任")
    top[1].metric("国库", f"¥{state.treasury / 1_000_000:,.1f}M")
    top[2].metric("国家队", f"{state.national_team_strength:.1f}")
    top[3].metric("联赛健康", f"{state.league_financial_health:.0%}")
    top[4].metric("球迷信任", f"{state.fan_trust:.0%}")
    top[5].metric("廉洁声誉", f"{state.integrity_reputation:.0%}")
    top[6].metric("联盟判断", _support_text(politics.coalition_support))


def _support_text(value: float) -> str:
    if value >= 0.66:
        return "稳固"
    if value >= 0.54:
        return "偏稳"
    if value >= 0.44:
        return "摇摆"
    if value >= 0.32:
        return "危险"
    return "濒临瓦解"


def _decision(game: PresidentCareerGame) -> None:
    decision = game.current_decision
    if decision is None:
        return
    st.warning(f"主席呈签件 · 本届M{game.local_month} · {decision.title}")
    st.write(decision.narrative)
    columns = st.columns(len(decision.options))
    for column, option in zip(columns, decision.options):
        with column:
            st.markdown(f"**{option.title}**")
            st.caption(option.summary)
            st.caption(f"已知风险：{option.risk}")
            if st.button(
                "签署此决定",
                key=f"president-{game.term_index}-{decision.id}-{option.id}",
                use_container_width=True,
            ):
                game.resolve_decision(option.id)
                _rerun()


def _briefing_tab(game: PresidentCareerGame) -> None:
    st.markdown("### 今日主席简报")
    for index, briefing in enumerate(game.executive_briefings()):
        if briefing.priority in {"紧急", "立即决定"}:
            st.error(f"{briefing.category} · {briefing.title}")
        elif briefing.priority == "关注":
            st.warning(f"{briefing.category} · {briefing.title}")
        else:
            st.info(f"{briefing.category} · {briefing.title}")
        st.write(briefing.summary)
        st.caption(f"来源：{briefing.source} · 信息可信度：{briefing.confidence}")
        if index < len(game.executive_briefings()) - 1:
            st.divider()


def _club_risk_tab(game: PresidentCareerGame) -> None:
    campaign = game.current_campaign
    state = campaign.engine.state
    premier = set(campaign.football.pyramid.premier_ids)
    rows = []
    for club_id, club in state.clubs.items():
        if club.license_status == "excluded":
            risk = "牌照撤销"
        elif club.license_status == "administration":
            risk = "正式托管"
        elif club.wage_arrears_months >= 2:
            risk = "欠薪警报"
        elif club.financial_health < 0.30:
            risk = "财务脆弱"
        else:
            risk = "正常"
        rows.append(
            {
                "俱乐部": club.name,
                "级别": 1 if club_id in premier else 2,
                "准入状态": club.license_status,
                "风险判断": risk,
                "欠薪月数": club.wage_arrears_months,
                "现金(M)": club.cash / 1_000_000,
                "债务(M)": club.debt / 1_000_000,
                "财务健康": club.financial_health * 100,
            }
        )
    frame = pd.DataFrame(rows).sort_values(
        ["风险判断", "财务健康"],
        ascending=[True, True],
    )
    st.dataframe(frame, hide_index=True, use_container_width=True, height=470)
    st.caption("主席看到的是正式财务与准入报表，不包含老板的隐藏耐心、私下动机或后台概率。")


def _personnel_tab(game: PresidentCareerGame) -> None:
    st.markdown("### 人事与公开廉洁材料")
    people = pd.DataFrame([asdict(item) for item in game.public_people()]).rename(
        columns={
            "name": "姓名",
            "institution": "机构",
            "role": "职位",
            "public_status": "公开状态",
            "performance_assessment": "履职评价",
            "integrity_assessment": "廉洁与案件信息",
            "disclosed_connections": "已披露关联数",
            "information_basis": "判断依据",
        }
    )
    if not people.empty:
        st.dataframe(
            people.drop(columns=["person_id"]),
            hide_index=True,
            use_container_width=True,
            height=420,
        )

    st.markdown("### 已披露关联")
    connections = pd.DataFrame(
        [asdict(item) for item in game.disclosed_connections()]
    ).rename(
        columns={
            "first_person": "甲方",
            "second_person": "乙方",
            "connection_type": "关系类型",
            "public_description": "公开说明",
            "status": "状态",
        }
    )
    if connections.empty:
        st.info("目前没有进入公开申报、审计结论或案件材料的关联关系。")
    else:
        st.dataframe(
            connections.drop(columns=["connection_id"]),
            hide_index=True,
            use_container_width=True,
            height=260,
        )

    st.markdown("### 正式案件简报")
    cases = pd.DataFrame([asdict(item) for item in game.public_cases()]).rename(
        columns={
            "subject_name": "当事人",
            "allegation": "公开指控",
            "route": "移送路径",
            "public_stage": "公开阶段",
            "public_outcome": "公开结果",
            "next_step": "下一程序",
        }
    )
    if cases.empty:
        st.info("当前没有已经正式立案或公开的案件。")
    else:
        st.dataframe(
            cases.drop(columns=["case_id"]),
            hide_index=True,
            use_container_width=True,
            height=320,
        )
    st.caption("证据强度、隐藏关系和司法计算仍在后台运行；主席只能看到依法送达的阶段性材料。")


def _politics_tab(game: PresidentCareerGame) -> None:
    st.markdown("### 政治支持与连任判断")
    estimates = pd.DataFrame(
        [asdict(item) for item in game.stakeholder_estimates()]
    ).rename(
        columns={
            "actor_name": "利益集团",
            "influence": "制度影响",
            "support_estimate": "支持估计",
            "trust_estimate": "信任估计",
            "latest_known_position": "最近已知立场",
        }
    )
    st.dataframe(
        estimates.drop(columns=["actor_id"]),
        hide_index=True,
        use_container_width=True,
        height=430,
    )
    st.caption("这是秘书长团队的政治估计，不是后台精确好感度。误判、隐瞒和临时倒戈仍然可能发生。")

    agreement = game.world.active_agreement
    if agreement and agreement.president_id == game.player_id:
        st.markdown("### 你的组阁承诺")
        rows = [
            {
                "对象": item.actor_name,
                "类型": item.commitment_type,
                "承诺": item.title,
                "截止月份": item.due_global_month,
                "状态": item.status,
            }
            for item in agreement.commitments
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _legacy_tab(game: PresidentCareerGame) -> None:
    if game.legacy_report is None:
        st.markdown("### 你的主席生涯仍在继续")
        st.info("离任、败选、被罢免或达到任期上限后，这里会生成最终历史评价。")
        completed = [
            item for item in game.world.term_records
            if item.president_id == game.player_id
        ]
        if completed:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "任期": item.term,
                            "足球评分": item.board_score,
                            "政治评分": item.political_score,
                            "兑现/违约": f"{item.promises_kept}/{item.promises_broken}",
                            "交接判断": item.succession_reason,
                        }
                        for item in completed
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
        return

    report = game.legacy_report
    st.markdown(f"## {report.verdict}")
    top = st.columns(5)
    top[0].metric("历史评分", f"{report.legacy_score:.1f}")
    top[1].metric("在任时间", f"{report.tenure_months}个月")
    top[2].metric("连续任期", str(report.terms_served))
    top[3].metric("足球评分", f"{report.board_score:.1f}")
    top[4].metric("政治评分", f"{report.political_score:.1f}")
    st.error(f"离任原因：{report.exit_reason}")
    st.markdown("### 主要遗产")
    for item in report.achievements:
        st.success(item)
    st.markdown("### 主要失败或争议")
    for item in report.failures:
        st.warning(item)
    if report.trophies:
        st.markdown("### 任内冠军记录")
        for item in report.trophies:
            st.write(f"- {item}")
    st.caption(
        f"任内重大决定{report.major_decisions}项；承诺兑现{report.promises_kept}项，"
        f"违约{report.promises_broken}项。"
    )

    if game.observer_mode or game.global_month > (game.career_end_global_month or 0):
        st.markdown("### 离任后的国家足球")
        st.info(
            f"当前全球月份G{game.global_month}，现任主席为{game.current_president.name}。"
            "你处于旁观状态，不能替继任政府作决定。"
        )
        _seasons_tab(game.world)
        _clubs_tab(game.world)


def main() -> None:
    st.set_page_config(
        page_title="Football Republic President",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    game = _session()
    _sidebar(game)
    _header(game)
    _decision(game)

    tabs = st.tabs(
        [
            "今日待办",
            "国家足球全景",
            "国家队与竞赛",
            "职业联赛与俱乐部",
            "青训与产业",
            "财政、审计与人事",
            "政治支持与连任",
            "生涯遗产",
        ]
    )
    with tabs[0]:
        _briefing_tab(game)
    with tabs[1]:
        _pyramid_tab(game.current_campaign)
    with tabs[2]:
        _squad_tab(game.current_campaign)
        _competition_tab(game.current_campaign)
    with tabs[3]:
        _club_risk_tab(game)
    with tabs[4]:
        _lifecycle_tab(game.current_campaign)
        _commercial_tab(game.current_campaign)
        _insolvency_tab(game.current_campaign)
    with tabs[5]:
        _finance_tab(game.current_campaign)
        _personnel_tab(game)
    with tabs[6]:
        _politics_tab(game)
    with tabs[7]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
