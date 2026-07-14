"""Cinematic executive presidential office with adaptive time and named delivery."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from football_republic.adaptive_time_web import (
    inject_timeflow_css,
    render_sidebar_clock,
    render_time_console,
    timed_office_packet,
)
from football_republic.campaign import Strategy
from football_republic.causal_office_webapp import (
    ANSWER_LABELS,
    STRATEGY_LABELS,
    _archive_tab,
    _department_reports,
    _dossier_tab,
    _followup_causal_tab,
    _legacy_tab,
    _leak_and_quote_alerts,
    _media_panel,
)
from football_republic.executive_followup import ExecutiveFollowupRuntime
from football_republic.executive_president_career import ExecutivePresidentCareerGame
from football_republic.office_visuals import (
    inject_cinematic_theme,
    render_cinematic_header,
    render_desk_scene,
    render_mandate_lifecycle,
    render_meeting_room,
    render_official_portrait,
    render_press_exchange,
    render_press_stage,
    render_report_document,
)
from football_republic.president_office_webapp import (
    _agenda_column,
    _css as _base_css,
    _inbox_column,
)
from football_republic.presidential_office import build_office_packet


STATUS_LABELS = {
    "awaiting_assignment": "等待主席指定责任人",
    "unassigned": "无人承担最终责任",
    "assigned": "已完成授权",
    "on_track": "按节点推进",
    "delayed": "执行延误",
    "narrowed": "执行口径被缩窄",
    "completed": "完成",
    "partial": "部分完成",
    "failed": "执行失败",
    "withdrawn": "已撤回",
}


def _session() -> ExecutivePresidentCareerGame:
    if "executive_president_career" not in st.session_state:
        st.session_state.executive_president_career = ExecutivePresidentCareerGame(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.executive_president_career


def _rerun() -> None:
    st.rerun()


def _office_state(packet_id: str) -> dict:
    key = f"executive-office-state-{packet_id}"
    if key not in st.session_state:
        st.session_state[key] = {"presidential_note": ""}
    return st.session_state[key]


def _sidebar(game: ExecutivePresidentCareerGame) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:10px 2px 16px">
              <div style="font-size:.68rem;letter-spacing:.14em;color:#d9b96d;font-weight:800">PRESIDENTIAL OFFICE</div>
              <div style="font-size:1.45rem;font-weight:800;color:#f1f5f7;margin-top:4px">主席办公室</div>
              <div style="color:#91a4b3;font-size:.78rem;margin-top:5px">{game.player_name} · 第{game.term_index}届任期</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if game.can_act:
            st.success(f"现任主席 · {game.player_name}")
            st.caption(f"国家足球治理第{game.global_year}年 · 制度月M{game.local_month}")
            render_sidebar_clock(game)

            unassigned = sum(
                item.status in {"awaiting_assignment", "unassigned"}
                for item in game.executive.mandates
            )
            delayed = sum(
                item.status in {"delayed", "narrowed"}
                for item in game.executive.mandates
            )
            if unassigned:
                st.error(f"{unassigned}项主席决定尚无具名责任人。")
            if delayed:
                st.warning(f"{delayed}项实施任务正在延误或缩水。")
            st.info("时间速度由真实事件决定：重大事项自动减速，平稳时期自动跨周推进。")
        else:
            st.error("你的主席生涯已经结束")
            st.markdown(
                f"**离任原因：** {game.career_end_reason or '—'}  \n"
                f"**现任主席：** {game.successor_name}"
            )
            st.caption("后续只能旁观，不能替继任者分配任务或回答记者。")
            left, right = st.columns(2)
            if left.button("旁观3月", use_container_width=True, disabled=game.history_finished):
                game.observe(3)
                _rerun()
            if right.button("旁观1年", use_container_width=True, disabled=game.history_finished):
                game.observe_years(1)
                _rerun()

        st.divider()
        st.download_button(
            "下载主席生涯存档",
            data=game.to_json(),
            file_name=f"football-republic-president-{game.calendar.current_date.isoformat()}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入主席生涯存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = ExecutivePresidentCareerGame.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.executive_president_career = restored
                st.success("主席身份、真实日历、办公室行动和实施责任验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "重开时的执政路线",
            options=list(Strategy),
            format_func=lambda item: STRATEGY_LABELS[item],
            index=1,
        )
        if st.button("开始新的主席生涯", use_container_width=True):
            st.session_state.executive_president_career = ExecutivePresidentCareerGame(
                reset_strategy,
                max_terms=10,
            )
            _rerun()


def _visual_desk_tab(game: ExecutivePresidentCareerGame, packet) -> None:
    render_desk_scene(game, packet)
    left, middle, right = st.columns([1.0, 1.28, 1.12], gap="large")
    with left:
        _agenda_column(packet)
    with middle:
        _inbox_column(game, packet)
        _department_reports(game)
    with right:
        _media_panel(game, packet)
    _leak_and_quote_alerts(game)


def _mandate_card(mandate) -> None:
    status = STATUS_LABELS.get(mandate.status, mandate.status)
    owner = (
        f"{mandate.assigned_official_name}（{mandate.assigned_office}）"
        if mandate.assigned_official_name
        else "尚未指定"
    )
    deadline = f"G{mandate.due_month}" if mandate.due_month is not None else "尚未设定"
    st.markdown(
        f"""
        <div class="paper">
          <div class="registry">主席督办令 · {mandate.id}</div>
          <h3>{mandate.option_title}</h3>
          <div class="muted">来源：{mandate.subject}</div>
          <hr>
          <p><b>当前状态：</b>{status}</p>
          <p><b>具名负责人：</b>{owner}</p>
          <p><b>复核期限：</b>{deadline}</p>
          <p><b>督查室最新判断：</b>{mandate.public_update}</p>
          <span class="red-stamp">主席督办</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_mandate_lifecycle(mandate, status)
    if mandate.assigned_official_name and mandate.assigned_office:
        render_official_portrait(
            mandate.assigned_office,
            mandate.assigned_official_name,
            mandate.public_update,
        )


def _implementation_tab(game: ExecutivePresidentCareerGame) -> None:
    st.markdown("### 主席决定实施簿")
    st.caption(
        "正式文件不会自动成功。主席必须指定一名具体官员承担最终责任；画面只展示公开责任链，不显示隐藏执行分数。"
    )
    if not game.executive.mandates:
        st.info("尚无已签署决定进入实施阶段。完成第一份呈签后，这里会出现待授权任务。")
        return
    mandate = st.selectbox(
        "选择一项主席决定",
        list(reversed(game.executive.mandates)),
        format_func=lambda item: (
            f"G{item.created_month} · {STATUS_LABELS.get(item.status, item.status)} · {item.option_title}"
        ),
    )
    _mandate_card(mandate)

    terminal = mandate.status in {"completed", "partial", "failed", "withdrawn"}
    if not terminal and game.can_act:
        st.markdown("#### 指定或调整具名责任人")
        offices = list(game.world.cabinet)
        default_index = (
            offices.index(mandate.assigned_office)
            if mandate.assigned_office in offices
            else offices.index(mandate.recommended_offices[0])
            if mandate.recommended_offices[0] in offices
            else 0
        )
        left, right = st.columns([.9, 1.1])
        with left:
            office = st.selectbox(
                "牵头办公室",
                offices,
                index=default_index,
                format_func=lambda value: f"{value} · {game.world.cabinet[value].name}",
                key=f"office-{mandate.id}",
            )
            selected_official = game.world.cabinet[office]
            render_official_portrait(
                office,
                selected_official.name,
                "主席正在考虑将本项决定交由其承担最终执行责任。",
            )
            st.caption("秘书处建议归口：" + "、".join(mandate.recommended_offices))
        with right:
            style = st.radio(
                "主席授权方式",
                list(ExecutiveFollowupRuntime.INSTRUCTION_STYLES),
                format_func=lambda value: ExecutiveFollowupRuntime.INSTRUCTION_STYLES[value]["label"],
                key=f"style-{mandate.id}",
            )
            style_copy = {
                "tight": "边界最清楚，最不容易被悄悄改写，但面对复杂政治环境时弹性较低。",
                "outcome": "由主席规定结果，部门决定路径；速度可能更快，也更容易重定义成功。",
                "coalition": "允许负责人边执行边谈判；外部阻力较低，但原方案更可能在协商中缩水。",
            }[style]
            st.info(style_copy)
        if st.button(
            "签署具名实施授权",
            type="primary",
            key=f"assign-{mandate.id}",
        ):
            game.assign_implementation(
                mandate_id=mandate.id,
                office=office,
                instruction_style=style,
            )
            _rerun()

    if mandate.effects:
        st.markdown("#### 授权与督办记录")
        for effect in mandate.effects:
            st.write(f"• {effect}")


def _competing_reports_tab(game: ExecutivePresidentCareerGame) -> None:
    st.markdown("### 同一事项的竞争报告")
    st.caption("三份文件来自不同责任体系。颜色代表部门身份，不代表哪份报告更正确。")
    if not game.executive.mandates:
        st.info("尚无实施事项可供部门会签。")
        return
    mandate = st.selectbox(
        "调阅哪项决定的会签材料",
        list(reversed(game.executive.mandates)),
        format_func=lambda item: item.option_title,
        key="competing-report-mandate",
    )
    reports = game.executive.visible_reports(mandate_id=mandate.id)
    if not reports:
        st.info("目前没有新的部门意见进入主席办公室。")
        return
    columns = st.columns(len(reports), gap="large")
    for column, report in zip(columns, reports):
        with column:
            render_report_document(report)
    st.warning("主席需要自己判断：分歧来自专业视角、部门自保、材料缺口，还是牵头人真的在缩减执行。")


def _press_room_tab(game: ExecutivePresidentCareerGame) -> None:
    st.markdown("### 主席发布会")
    st.caption("记者会根据你的上一句话继续追问。发布会未结束时，时间系统会冻结。")
    if game.can_act:
        active = game.executive.active_mandates()
        default_topic = active[-1].option_title if active else "国家足球治理"
        topic = st.text_input("本次发布会主题", value=default_topic)
        if st.button("召开发布会", disabled=not topic.strip()):
            game.start_press_conference(topic=topic.strip())
            _rerun()

    if not game.executive.press_sessions:
        st.info("尚未召开连续追问式发布会。")
        return
    session = st.selectbox(
        "选择发布会记录",
        list(reversed(game.executive.press_sessions)),
        format_func=lambda item: f"G{item.global_month} · {item.status} · {item.topic}",
    )
    render_press_stage(session)
    for exchange in session.exchanges:
        render_press_exchange(exchange)
        if exchange.reporter_followup:
            st.caption(f"记者下一轮追问：{exchange.reporter_followup}")

    if session.status == "open" and game.can_act:
        st.error(f"**当前追问：** {session.current_question}")
        style = st.radio(
            "选择这一次回答方式",
            list(ANSWER_LABELS),
            format_func=lambda item: ANSWER_LABELS[item],
            key=f"press-style-{session.id}-{len(session.exchanges)}",
        )
        if st.button(
            "回答并接受下一轮追问",
            type="primary",
            key=f"press-answer-{session.id}-{len(session.exchanges)}",
        ):
            game.answer_press_conference(
                session_id=session.id,
                answer_style=style,
            )
            _rerun()
    elif session.status == "closed":
        st.info("本场发布会已经结束，全部原话进入公开档案。")


def _visual_meetings_tab(game: ExecutivePresidentCareerGame, packet) -> None:
    st.markdown("### 第三会客室")
    st.caption("会见决定谁能直接进入主席的信息圈。连续只见同一集团，也会让其他人怀疑权力通道是否公平。")
    meeting = st.selectbox(
        "选择一份会见申请",
        packet.meeting_requests,
        format_func=lambda item: f"{item.priority} · {item.visitor} · {item.subject}",
    )
    render_meeting_room(game, meeting)

    ask, offer = st.columns(2, gap="large")
    with ask:
        st.markdown("#### 对方真正希望得到")
        st.warning(meeting.concrete_ask)
        st.markdown("#### 对方不愿主动说")
        st.error(meeting.what_they_avoid)
    with offer:
        st.markdown("#### 对方愿意交换或承诺")
        st.success(meeting.what_they_offer)
        st.markdown("#### 主席应该当面追问")
        for question in meeting.chairman_questions:
            st.write(f"• {question}")

    existing = next((item for item in game.office.meetings if item.id == meeting.id), None)
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


def _executive_history_tab(game: ExecutivePresidentCareerGame) -> None:
    _followup_causal_tab(game)
    st.divider()
    st.markdown("### 具名实施结果")
    if game.executive.mandates:
        frame = pd.DataFrame([asdict(item) for item in reversed(game.executive.mandates)])
        frame["recommended_offices"] = frame["recommended_offices"].apply(
            lambda value: "、".join(value)
        )
        frame["effects"] = frame["effects"].apply(lambda value: "；".join(value))
        hidden = [
            "progress",
            "hidden_delivery_quality",
            "hidden_distortion",
            "penalty_applied",
            "outcome_applied",
        ]
        st.dataframe(
            frame.drop(columns=[column for column in hidden if column in frame]),
            hide_index=True,
            use_container_width=True,
            height=400,
        )
    else:
        st.info("尚无具名实施记录。")


def main() -> None:
    st.set_page_config(
        page_title="Football Republic President",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _base_css()
    inject_cinematic_theme()
    inject_timeflow_css()
    game = _session()
    packet = timed_office_packet(game, build_office_packet(game))
    office_state = _office_state(packet.packet_id)
    _sidebar(game)
    render_cinematic_header(game, packet)
    render_time_console(game)

    tabs = st.tabs(
        [
            "主席桌面",
            "今日呈签",
            "具名实施",
            "竞争报告",
            "主席发布会",
            "会见与接触",
            "督查与公开承诺",
            "档案柜",
            "生涯遗产",
        ]
    )
    with tabs[0]:
        _visual_desk_tab(game, packet)
    with tabs[1]:
        _dossier_tab(game, packet, office_state)
    with tabs[2]:
        _implementation_tab(game)
    with tabs[3]:
        _competing_reports_tab(game)
    with tabs[4]:
        _press_room_tab(game)
    with tabs[5]:
        _visual_meetings_tab(game, packet)
    with tabs[6]:
        _executive_history_tab(game)
    with tabs[7]:
        _archive_tab(game)
    with tabs[8]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
