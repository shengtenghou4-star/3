"""Immersive Streamlit office for one fixed football-association president."""

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
from football_republic.presidential_office import OfficePacket, build_office_packet
from football_republic.pyramid_webapp import (
    _finance_tab,
    _pyramid_tab,
    _squad_tab,
)


STRATEGY_LABELS = {
    Strategy.FOUNDATIONS: "基层筑基",
    Strategy.BALANCED: "均衡治理",
    Strategy.QUICK_RESULTS: "短期成绩",
}


def _session() -> PresidentCareerGame:
    if "president_career_game" not in st.session_state:
        st.session_state.president_career_game = PresidentCareerGame(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.president_career_game


def _rerun() -> None:
    st.rerun()


def _css() -> None:
    st.markdown(
        """
        <style>
        .stApp {background: #091019; color: #e9edf2;}
        [data-testid="stSidebar"] {background: #0d1722; border-right: 1px solid #263545;}
        .office-header {
            border: 1px solid #314458; border-radius: 16px; padding: 22px 26px;
            background: linear-gradient(135deg, #13202d 0%, #0b141d 72%);
            box-shadow: 0 12px 32px rgba(0,0,0,.25); margin-bottom: 14px;
        }
        .office-seal {font-size: .73rem; letter-spacing: .15em; color: #d8b765;}
        .office-title {font-size: 2rem; font-weight: 720; margin: 5px 0 7px;}
        .office-sub {color: #aebbc8; line-height: 1.55;}
        .status-strip {
            border-left: 4px solid #d8b765; background: #111d28; padding: 12px 16px;
            margin: 8px 0 18px; color: #dfe7ee;
        }
        .paper {
            background: #f3efe5; color: #1b1d1f; border-radius: 5px;
            padding: 22px 25px; box-shadow: 0 10px 28px rgba(0,0,0,.28);
            border-top: 7px solid #a32929; margin-bottom: 14px;
        }
        .paper .muted {color: #5d6267; font-size: .9rem;}
        .paper .registry {font-family: monospace; color: #8a2a2a; font-size: .82rem;}
        .tray-card {
            border: 1px solid #2d4053; border-radius: 12px; padding: 14px 16px;
            background: #101b26; margin-bottom: 10px;
        }
        .tray-card h4 {margin: 3px 0 7px;}
        .kicker {font-size: .72rem; letter-spacing: .08em; color: #d8b765;}
        .muted {color: #9caaba;}
        .agenda {
            display: grid; grid-template-columns: 58px 1fr; gap: 12px;
            border-bottom: 1px solid #263646; padding: 11px 0;
        }
        .agenda-time {font-family: monospace; color: #d8b765; font-weight: 700;}
        .meeting-quote {
            border-left: 4px solid #6f8aa3; padding: 12px 16px; margin: 12px 0;
            background: #101b26; font-size: 1.03rem;
        }
        .staff-note {
            border: 1px solid #374b5f; border-radius: 10px; padding: 13px 15px;
            background: #111d28; min-height: 185px;
        }
        .red-stamp {
            display: inline-block; border: 2px solid #a32929; color: #a32929;
            padding: 4px 9px; transform: rotate(-2deg); font-weight: 700;
        }
        .small-note {font-size:.84rem;color:#9eacb9;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _office_state(packet: OfficePacket) -> dict:
    key = f"office-state-{packet.packet_id}"
    if key not in st.session_state:
        st.session_state[key] = {
            "meeting_responses": {},
            "opened_correspondence": [],
            "presidential_note": "",
        }
    return st.session_state[key]


def _sidebar(game: PresidentCareerGame) -> None:
    with st.sidebar:
        st.markdown("## 主席办公室")
        if game.can_act:
            st.success(f"现任主席 · {game.player_name}")
            st.caption(
                f"国家足球治理第{game.global_year}年 · 制度任期第{game.term_index}届 · 本届M{game.local_month}"
            )
            if game.current_decision is not None:
                st.warning("呈签件尚未批示，时间已经冻结。")
            left, right = st.columns(2)
            if left.button(
                "结束今日",
                use_container_width=True,
                disabled=game.current_decision is not None,
            ):
                game.advance(1, interactive=True)
                _rerun()
            if right.button(
                "推进至文件",
                use_container_width=True,
                disabled=game.current_decision is not None,
            ):
                game.advance(24, interactive=True)
                _rerun()
            st.info("你处理的是主席权限内的跨部门事项；普通行政件已由秘书处分流。")
        else:
            st.error("你的主席生涯已经结束")
            st.markdown(
                f"**离任原因：** {game.career_end_reason or '—'}  \n"
                f"**现任主席：** {game.successor_name}"
            )
            st.caption("后续只能旁观，不能进入继任者办公室。")
            left, right = st.columns(2)
            if left.button("旁观3月", use_container_width=True, disabled=game.history_finished):
                game.observe(3)
                _rerun()
            if right.button("旁观1年", use_container_width=True, disabled=game.history_finished):
                game.observe_years(1)
                _rerun()
            if st.button("旁观至历史终点", use_container_width=True, disabled=game.history_finished):
                game.observe_to_end()
                _rerun()

        st.divider()
        st.download_button(
            "下载主席生涯存档",
            data=game.to_json(),
            file_name=f"football-republic-president-m{game.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入主席生涯存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = PresidentCareerGame.from_json(uploaded.getvalue().decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.president_career_game = restored
                st.success("主席身份、历史世界和权限状态验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "重开时的执政路线",
            options=list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=1,
        )
        if st.button("开始新的主席生涯", use_container_width=True):
            st.session_state.president_career_game = PresidentCareerGame(
                reset_strategy,
                max_terms=10,
            )
            _rerun()


def _header(game: PresidentCareerGame, packet: OfficePacket) -> None:
    role = (
        f"现任国家足球协会主席 · {game.player_name}"
        if game.can_act
        else f"{game.player_name}主席生涯档案 · 当前由{game.current_president.name}执政"
    )
    st.markdown(
        f"""
        <div class="office-header">
          <div class="office-seal">NATIONAL FOOTBALL ASSOCIATION · PRESIDENTIAL OFFICE</div>
          <div class="office-title">国家足协主席办公室</div>
          <div class="office-sub">{role}<br>{packet.date_label} · {packet.weekday_label} · {packet.office_location}</div>
        </div>
        <div class="status-strip"><b>秘书长晨间判断：</b>{packet.situation_line}</div>
        """,
        unsafe_allow_html=True,
    )


def _agenda_column(packet: OfficePacket) -> None:
    st.markdown("### 今日日程")
    for item in packet.agenda:
        st.markdown(
            f"""
            <div class="agenda">
              <div class="agenda-time">{item.time}</div>
              <div><b>{item.title}</b><br><span class="muted">{item.location} · {item.participants}</span><br>
              <span class="small-note">{item.purpose} · {item.status}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _inbox_column(game: PresidentCareerGame, packet: OfficePacket) -> None:
    st.markdown("### 主席收文盘")
    if packet.dossier is not None:
        st.markdown(
            f"""
            <div class="paper">
              <div class="registry">{packet.dossier.registry_number}</div>
              <h3>{packet.dossier.title}</h3>
              <div class="muted">{packet.dossier.submitting_office}<br>{packet.dossier.deadline}</div>
              <p>{packet.dossier.decision_required}</p>
              <span class="red-stamp">主席亲签</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("完整会签意见、反对理由和实施责任在“今日呈签”中。")
    else:
        st.markdown(
            """
            <div class="tray-card">
              <div class="kicker">DESK STATUS</div>
              <h4>目前没有必须由主席亲签的文件</h4>
              <div class="muted">这不代表协会没有工作，而是普通事项已按授权在部门层处理。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for briefing in game.executive_briefings()[:4]:
        st.markdown(
            f"""
            <div class="tray-card">
              <div class="kicker">{briefing.priority} · {briefing.category}</div>
              <h4>{briefing.title}</h4>
              <div>{briefing.summary}</div>
              <div class="small-note" style="margin-top:8px">来源：{briefing.source} · 可信度：{briefing.confidence}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _news_column(packet: OfficePacket) -> None:
    st.markdown("### 来电与剪报")
    for item in packet.correspondence:
        with st.expander(f"{item.channel} · {item.sender}", expanded=False):
            st.markdown(f"**{item.subject}**")
            st.write(item.message)
            st.info(item.requested_action)
            st.caption(f"敏感级别：{item.sensitivity}")
    st.markdown("#### 媒体联络官标注")
    for clip in packet.press_clippings:
        st.markdown(
            f"""
            <div class="tray-card">
              <div class="kicker">{clip.outlet} · {clip.temperature}</div>
              <h4>{clip.headline}</h4>
              <div class="muted">{clip.angle}</div>
              <div style="margin-top:8px"><b>预计追问：</b>{clip.question_for_president}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _desk_tab(game: PresidentCareerGame, packet: OfficePacket) -> None:
    left, middle, right = st.columns([1.05, 1.35, 1.05], gap="large")
    with left:
        _agenda_column(packet)
    with middle:
        _inbox_column(game, packet)
    with right:
        _news_column(packet)


def _dossier_tab(game: PresidentCareerGame, packet: OfficePacket, office_state: dict) -> None:
    dossier = packet.dossier
    if dossier is None:
        st.info("今天没有等待主席签字的正式文件。可以结束今日，或先查看会见申请和督办报告。")
        return

    st.markdown(
        f"""
        <div class="paper">
          <div class="registry">{dossier.classification} · {dossier.registry_number}</div>
          <h2 style="margin-bottom:5px">{dossier.title}</h2>
          <div class="muted">呈报单位：{dossier.submitting_office}<br>办理期限：{dossier.deadline}</div>
          <hr>
          <b>主席需要决定：</b><p>{dossier.decision_required}</p>
          <b>权限依据：</b><p>{dossier.legal_authority}</p>
          <b>秘书处摘要：</b><p>{dossier.executive_summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    facts, unknowns = st.columns(2)
    with facts:
        st.markdown("### 已核实事实")
        for item in dossier.verified_facts:
            st.success(item)
    with unknowns:
        st.markdown("### 尚有争议或无法确认")
        for item in dossier.disputed_or_unknown:
            st.warning(item)

    st.markdown("### 五人办公会：部门没有达成一致")
    columns = st.columns(5)
    for column, item in zip(columns, dossier.staff_positions):
        with column:
            st.markdown(
                f"""
                <div class="staff-note">
                  <div class="kicker">{item.office}</div>
                  <h4>{item.official_name}</h4>
                  <b>{item.recommendation}</b>
                  <p>{item.reasoning}</p>
                  <div class="small-note">保留意见：{item.concern}<br>判断把握：{item.confidence}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 外部立场：秘书处估计，不是精确票数")
    st.dataframe(
        pd.DataFrame([asdict(item) for item in dossier.stakeholder_positions]).rename(
            columns={
                "name": "集团",
                "known_position": "当前立场",
                "likely_argument": "预计论点",
                "confidence": "判断把握",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### 主席批示")
    option_ids = [item.option_id for item in dossier.option_briefs]
    selected = st.radio(
        "选择处理方向",
        option_ids,
        format_func=lambda value: next(
            item.title for item in dossier.option_briefs if item.option_id == value
        ),
        horizontal=True,
    )
    brief = next(item for item in dossier.option_briefs if item.option_id == selected)
    case_col, objection_col = st.columns(2)
    with case_col:
        st.success("**支持这一方案的最强理由**\n\n" + brief.presidential_case)
    with objection_col:
        st.error("**反对这一方案的最强理由**\n\n" + brief.strongest_objection)
    st.markdown(f"**执行牵头：** {brief.implementation_owner}")
    st.markdown(f"**首个30日：** {brief.first_thirty_days}")
    st.markdown(f"**最可能的失败方式：** {brief.failure_mode}")

    note = st.text_area(
        "主席手写批注（办公室工作记录，不替代正式选项）",
        value=office_state.get("presidential_note", ""),
        placeholder="例如：三十日后必须回报；不得向涉案人员泄露材料；救助资金进入托管账户……",
        height=100,
    )
    office_state["presidential_note"] = note
    confirm = st.checkbox("我已阅读部门分歧、反对意见和实施责任")
    if st.button("签署主席决定", type="primary", disabled=not confirm):
        game.resolve_decision(selected)
        _rerun()

    with st.expander("查看呈签附件目录"):
        for annex in dossier.annexes:
            st.write(f"• {annex}")


def _meetings_tab(packet: OfficePacket, office_state: dict) -> None:
    st.markdown("### 会见申请")
    st.caption("会见本身不是替对方作决定。它决定你听到谁的版本、当面追问什么，以及谁会认为自己获得了主席接触渠道。")
    meeting = st.selectbox(
        "选择一份会见申请",
        packet.meeting_requests,
        format_func=lambda item: f"{item.priority} · {item.visitor} · {item.subject}",
    )
    st.markdown(
        f"""
        <div class="tray-card">
          <div class="kicker">{meeting.priority} · 申请时长{meeting.requested_duration}</div>
          <h3>{meeting.visitor}</h3>
          <div class="muted">{meeting.institution} · {meeting.subject}</div>
        </div>
        <div class="meeting-quote">“{meeting.opening_line}”</div>
        """,
        unsafe_allow_html=True,
    )
    ask, offer = st.columns(2)
    with ask:
        st.markdown("**对方真正希望得到**")
        st.warning(meeting.concrete_ask)
        st.markdown("**对方不愿主动说**")
        st.error(meeting.what_they_avoid)
    with offer:
        st.markdown("**对方愿意交换或承诺**")
        st.success(meeting.what_they_offer)
        st.markdown("**主席应该追问**")
        for question in meeting.chairman_questions:
            st.write(f"• {question}")

    response = office_state["meeting_responses"].get(meeting.id)
    if response:
        st.info(f"办公室安排：{response}")
    else:
        columns = st.columns(3)
        if columns[0].button("主席亲自会见", use_container_width=True):
            office_state["meeting_responses"][meeting.id] = "主席亲自会见，秘书长和主管部门列席"
            _rerun()
        if columns[1].button("秘书长先谈", use_container_width=True):
            office_state["meeting_responses"][meeting.id] = "由秘书长摸清底线，再决定是否进主席办公室"
            _rerun()
        if columns[2].button("暂不安排", use_container_width=True):
            office_state["meeting_responses"][meeting.id] = "暂不安排会见，要求对方先提交书面材料"
            _rerun()

    st.divider()
    st.markdown("### 今日来电与机要件")
    for item in packet.correspondence:
        st.markdown(f"**{item.channel}｜{item.sender}｜{item.subject}**")
        st.write(item.message)
        st.caption(f"希望主席办公室采取：{item.requested_action} · {item.sensitivity}")
        st.divider()


def _followup_tab(game: PresidentCareerGame) -> None:
    st.markdown("### 主席批示督办簿")
    history = list(reversed(game.current_campaign.decision_history[-12:]))
    if not history:
        st.info("本届任期尚无已签署重大决定。")
    for record in history:
        with st.expander(f"M{record.month} · {record.title} · {record.option_title}"):
            st.markdown(f"**主席选择：** {record.option_title}")
            st.markdown("**已进入系统的直接效果：**")
            effects = record.effects if not isinstance(record.effects, str) else (record.effects,)
            for effect in effects:
                st.write(f"• {effect}")
            st.caption("后续结果仍会受到地方执行、俱乐部行为、财政能力和比赛偶然性影响。")

    st.markdown("### 当前需要督办的跨部门事项")
    for briefing in game.executive_briefings():
        if briefing.priority in {"紧急", "关注", "立即决定"}:
            st.markdown(f"**{briefing.category}｜{briefing.title}**")
            st.write(briefing.summary)
            st.caption(f"责任来源：{briefing.source}")


def _archive_tab(game: PresidentCareerGame) -> None:
    st.info("这里是主席按需调阅的档案柜，不是每日工作的主界面。")
    reports = st.tabs(["联赛", "国家队", "财务", "青训产业", "历史档案"])
    with reports[0]:
        _pyramid_tab(game.current_campaign)
        _clubs_tab(game.world)
    with reports[1]:
        _squad_tab(game.current_campaign)
        _competition_tab(game.current_campaign)
    with reports[2]:
        _finance_tab(game.current_campaign)
    with reports[3]:
        _lifecycle_tab(game.current_campaign)
        _commercial_tab(game.current_campaign)
        _insolvency_tab(game.current_campaign)
    with reports[4]:
        _seasons_tab(game.world)
        st.markdown("### 公开人员与案件材料")
        people = pd.DataFrame([asdict(item) for item in game.public_people()])
        if not people.empty:
            st.dataframe(people, hide_index=True, use_container_width=True)
        cases = pd.DataFrame([asdict(item) for item in game.public_cases()])
        if not cases.empty:
            st.dataframe(cases, hide_index=True, use_container_width=True)


def _legacy_tab(game: PresidentCareerGame) -> None:
    if game.legacy_report is None:
        st.markdown("### 你的主席生涯仍在继续")
        st.info("离任、败选、被罢免或达到任期上限后，这里会冻结最终评价。后任成绩不会改写你的记录。")
        return
    report = game.legacy_report
    st.markdown(f"## {report.verdict}")
    st.error(f"离任原因：{report.exit_reason}")
    st.write(
        f"{report.president_name}共在任{report.tenure_months}个月，完成{report.terms_served}个连续任期。"
        f"任内签署重大决定{report.major_decisions}项，兑现承诺{report.promises_kept}项，违约{report.promises_broken}项。"
    )
    st.markdown("### 历史评价")
    st.progress(min(1.0, max(0.0, report.legacy_score / 100.0)), text=f"综合历史评分 {report.legacy_score:.1f}")
    left, right = st.columns(2)
    with left:
        st.markdown("#### 主要遗产")
        for item in report.achievements:
            st.success(item)
    with right:
        st.markdown("#### 主要失败或争议")
        for item in report.failures:
            st.warning(item)
    if report.trophies:
        st.markdown("#### 任内冠军记录")
        for item in report.trophies:
            st.write(f"• {item}")
    if game.observer_mode or game.global_month > (game.career_end_global_month or 0):
        st.markdown("### 离任后的国家足球")
        st.info(
            f"当前全球月份G{game.global_month}，现任主席为{game.current_president.name}。你只能旁观。"
        )
        _seasons_tab(game.world)


def main() -> None:
    st.set_page_config(
        page_title="Football Republic President",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    game = _session()
    packet = build_office_packet(game)
    office_state = _office_state(packet)
    _sidebar(game)
    _header(game, packet)

    tabs = st.tabs(
        [
            "主席桌面",
            "今日呈签",
            "会见与来电",
            "督查室",
            "档案柜",
            "生涯遗产",
        ]
    )
    with tabs[0]:
        _desk_tab(game, packet)
    with tabs[1]:
        _dossier_tab(game, packet, office_state)
    with tabs[2]:
        _meetings_tab(packet, office_state)
    with tabs[3]:
        _followup_tab(game)
    with tabs[4]:
        _archive_tab(game)
    with tabs[5]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
