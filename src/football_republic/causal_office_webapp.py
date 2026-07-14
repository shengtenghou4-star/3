"""Causal presidential office: meetings and words persist beyond the current screen."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from football_republic.campaign import Strategy
from football_republic.causal_president_career import CausalPresidentCareerGame
from football_republic.president_office_webapp import (
    STRATEGY_LABELS,
    _agenda_column,
    _archive_tab,
    _css,
    _dossier_tab,
    _followup_tab,
    _header,
    _inbox_column,
    _legacy_tab,
)
from football_republic.presidential_office import OfficePacket, build_office_packet


ANSWER_LABELS = {
    "rules_first": "强调规则与正式程序",
    "support_sector": "承诺帮助行业渡过困难",
    "transparent_uncertainty": "公开承认仍有未知事实",
    "no_comment": "暂不评论",
}


def _session() -> CausalPresidentCareerGame:
    if "causal_president_career" not in st.session_state:
        st.session_state.causal_president_career = CausalPresidentCareerGame(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.causal_president_career


def _rerun() -> None:
    st.rerun()


def _office_state(packet: OfficePacket) -> dict:
    key = f"causal-office-state-{packet.packet_id}"
    if key not in st.session_state:
        st.session_state[key] = {"presidential_note": ""}
    return st.session_state[key]


def _sidebar(game: CausalPresidentCareerGame) -> None:
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
            st.info("会见、记者答复和内部泄密已经进入长期政治记忆。")
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
                restored = CausalPresidentCareerGame.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.causal_president_career = restored
                st.success("主席身份、办公室行动和历史世界验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "重开时的执政路线",
            options=list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=1,
        )
        if st.button("开始新的主席生涯", use_container_width=True):
            st.session_state.causal_president_career = CausalPresidentCareerGame(
                reset_strategy,
                max_terms=10,
            )
            _rerun()


def _department_reports(game: CausalPresidentCareerGame) -> None:
    st.markdown("### 今日进入主席桌面的部门报告")
    st.caption(
        "报告是部门加工后的版本。可信度反映材料覆盖，不代表部门没有立场；被延迟或省略的内容可能从媒体、俱乐部或调查渠道绕回来。"
    )
    reports = game.visible_office_reports()
    if not reports:
        st.info("今天没有新的部门报告进入主席桌面。")
        return
    for report in reports:
        st.markdown(
            f"""
            <div class="tray-card">
              <div class="kicker">{report.urgency} · {report.office} · 可信度{report.confidence}</div>
              <h4>{report.headline}</h4>
              <div>{report.summary}</div>
              <div class="small-note" style="margin-top:8px">报送人：{report.official_name} · 依据：{report.information_basis}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _media_panel(
    game: CausalPresidentCareerGame,
    packet: OfficePacket,
) -> None:
    st.markdown("### 媒体联络官：需要决定怎么回答")
    existing = {item.id: item for item in game.office.statements}
    for index, clip in enumerate(packet.press_clippings):
        clipping_id = f"{packet.packet_id}-press-{index}"
        with st.expander(f"{clip.outlet} · {clip.headline}", expanded=index == 0):
            st.write(clip.angle)
            st.markdown(f"**记者预计追问：** {clip.question_for_president}")
            statement = existing.get(clipping_id)
            if statement is not None:
                st.success(f"主席公开答复：“{statement.quote}”")
                st.caption(
                    f"当前状态：{statement.status}"
                    + (
                        f" · 审查至G{statement.due_month}"
                        if statement.due_month is not None
                        else " · 未形成可核验承诺"
                    )
                )
                continue
            answer_style = st.radio(
                "选择公开口径",
                list(ANSWER_LABELS),
                format_func=lambda item: ANSWER_LABELS[item],
                key=f"answer-{clipping_id}",
            )
            if st.button("确认对媒体答复", key=f"send-{clipping_id}"):
                game.answer_media(
                    clipping_id=clipping_id,
                    outlet=clip.outlet,
                    question=clip.question_for_president,
                    answer_style=answer_style,
                    topic=clip.headline,
                )
                _rerun()


def _leak_and_quote_alerts(game: CausalPresidentCareerGame) -> None:
    recent_leaks = game.office.leaks[-4:]
    recent_quotes = game.office.quote_history[-4:]
    if not recent_leaks and not recent_quotes:
        return
    st.markdown("### 政治后果与舆情追责")
    for leak in reversed(recent_leaks):
        st.error(
            f"**G{leak.global_month}｜{leak.headline}**\n\n"
            f"{leak.public_summary}\n\n内部判断的可能动机：{leak.motive}"
        )
    for quote in reversed(recent_quotes):
        st.warning(
            f"**G{quote.global_month}｜{quote.headline}**\n\n"
            f"媒体重新引用：“{quote.original_quote}”\n\n"
            f"触发决定：{quote.triggering_decision}"
        )


def _desk_tab(
    game: CausalPresidentCareerGame,
    packet: OfficePacket,
) -> None:
    left, middle, right = st.columns([1.0, 1.25, 1.15], gap="large")
    with left:
        _agenda_column(packet)
    with middle:
        _inbox_column(game, packet)
        _department_reports(game)
    with right:
        _media_panel(game, packet)
    _leak_and_quote_alerts(game)


def _meetings_tab(
    game: CausalPresidentCareerGame,
    packet: OfficePacket,
) -> None:
    st.markdown("### 会见申请")
    st.caption(
        "会见会改变接触渠道、信任和未来施压方式。连续只见同一集团，也会引发‘谁能进入主席办公室’的公平争议。"
    )
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

    existing = next(
        (item for item in game.office.meetings if item.id == meeting.id),
        None,
    )
    if existing is not None:
        st.info(existing.access_message)
        st.markdown(f"**办公室承诺：** {existing.commitment}")
        st.caption(
            f"长期状态：{existing.status}"
            + (f" · 跟进期限G{existing.due_month}" if existing.due_month else "")
        )
        for effect in existing.effects:
            st.write(f"• {effect}")
    else:
        columns = st.columns(4)
        choices = (
            ("president", "主席亲自会见"),
            ("secretary", "秘书长先谈"),
            ("written", "先交书面材料"),
            ("decline", "拒绝会见"),
        )
        for column, (choice, label) in zip(columns, choices):
            if column.button(label, use_container_width=True, key=f"meeting-{meeting.id}-{choice}"):
                sensitivity = (
                    "urgent"
                    if meeting.priority == "紧急"
                    else "sensitive"
                    if meeting.priority == "敏感"
                    else "normal"
                )
                game.record_meeting(
                    meeting_id=meeting.id,
                    visitor=meeting.visitor,
                    institution=meeting.institution,
                    subject=meeting.subject,
                    choice=choice,
                    sensitivity=sensitivity,
                )
                _rerun()

    st.divider()
    st.markdown("### 会见和接触记录")
    if game.office.meetings:
        frame = pd.DataFrame([asdict(item) for item in reversed(game.office.meetings)])
        frame["effects"] = frame["effects"].apply(lambda value: "；".join(value))
        st.dataframe(frame, hide_index=True, use_container_width=True, height=360)
    else:
        st.info("尚无主席办公室会见决定。")


def _followup_causal_tab(game: CausalPresidentCareerGame) -> None:
    _followup_tab(game)
    st.divider()
    st.markdown("### 公开表态追踪")
    if game.office.statements:
        frame = pd.DataFrame([asdict(item) for item in reversed(game.office.statements)])
        frame["contradiction_options"] = frame["contradiction_options"].apply(
            lambda value: "、".join(value)
        )
        st.dataframe(frame, hide_index=True, use_container_width=True, height=360)
    else:
        st.info("尚无主席公开答复进入长期审查。")
    st.markdown("### 信息治理内部状态")
    profiles = game.office.staff_profiles(game)
    st.caption(
        "以下不向玩家显示隐藏分值，只显示部门的制度性偏向。具体过滤程度只通过实际报送延迟、措辞和外部交叉信息体现。"
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "部门": item.office,
                    "负责人": item.official_name,
                    "主要视角": item.departmental_bias,
                }
                for item in profiles
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )


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
            "会见与接触",
            "督查与公开承诺",
            "档案柜",
            "生涯遗产",
        ]
    )
    with tabs[0]:
        _desk_tab(game, packet)
    with tabs[1]:
        _dossier_tab(game, packet, office_state)
    with tabs[2]:
        _meetings_tab(game, packet)
    with tabs[3]:
        _followup_causal_tab(game)
    with tabs[4]:
        _archive_tab(game)
    with tabs[5]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
