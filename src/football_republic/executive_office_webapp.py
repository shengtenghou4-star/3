"""Executive presidential office with named delivery and live press follow-ups."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from football_republic.campaign import Strategy
from football_republic.causal_office_webapp import (
    ANSWER_LABELS,
    STRATEGY_LABELS,
    _archive_tab,
    _css,
    _desk_tab,
    _dossier_tab,
    _followup_causal_tab,
    _header,
    _legacy_tab,
    _meetings_tab,
)
from football_republic.executive_followup import ExecutiveFollowupRuntime
from football_republic.executive_president_career import ExecutivePresidentCareerGame
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
        st.markdown("## 主席办公室")
        if game.can_act:
            st.success(f"现任主席 · {game.player_name}")
            st.caption(
                f"国家足球治理第{game.global_year}年 · 制度任期第{game.term_index}届 · 本届M{game.local_month}"
            )
            if game.current_decision is not None:
                st.warning("呈签件尚未批示，时间已经冻结。")
            unassigned = sum(
                item.status in {"awaiting_assignment", "unassigned"}
                for item in game.executive.mandates
            )
            delayed = sum(
                item.status in {"delayed", "narrowed"}
                for item in game.executive.mandates
            )
            if unassigned:
                st.error(f"有{unassigned}项主席决定尚无具名责任人。")
            if delayed:
                st.warning(f"有{delayed}项实施任务正在延误或缩水。")
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
            st.info("签字只是开始。你还要指定谁负责、如何授权，并为执行结果公开答辩。")
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
            file_name=f"football-republic-president-m{game.global_month}.json",
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
                st.success("主席身份、办公室行动、实施责任和公开答复验证通过。")
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
          <div class="registry">实施授权 · {mandate.id}</div>
          <h3>{mandate.option_title}</h3>
          <div class="muted">来源：{mandate.subject}</div>
          <hr>
          <p><b>当前状态：</b>{status}</p>
          <p><b>具名负责人：</b>{owner}</p>
          <p><b>复核期限：</b>{deadline}</p>
          <p><b>督查室最新判断：</b>{mandate.public_update}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _implementation_tab(game: ExecutivePresidentCareerGame) -> None:
    st.markdown("### 主席决定实施簿")
    st.caption(
        "正式文件不会自动成功。主席必须指定一名具体官员承担最终责任；专业归口、授权方式、个人能力、忠诚、廉洁、关系网和同时承担的任务都会影响结果。"
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
        left, right = st.columns(2)
        with left:
            office = st.selectbox(
                "牵头办公室",
                offices,
                index=default_index,
                format_func=lambda value: f"{value} · {game.world.cabinet[value].name}",
                key=f"office-{mandate.id}",
            )
            st.caption("秘书处建议归口：" + "、".join(mandate.recommended_offices))
        with right:
            style = st.radio(
                "主席授权方式",
                list(ExecutiveFollowupRuntime.INSTRUCTION_STYLES),
                format_func=lambda value: ExecutiveFollowupRuntime.INSTRUCTION_STYLES[value]["label"],
                key=f"style-{mandate.id}",
            )
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
    st.caption(
        "这里故意不给出一个系统认证的‘正确答案’。各部门基于不同责任、材料和利益给出互相冲突但可能都部分成立的判断。"
    )
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
    columns = st.columns(len(reports))
    for column, report in zip(columns, reports):
        with column:
            st.markdown(
                f"""
                <div class="staff-note">
                  <div class="kicker">{report.urgency} · {report.office}</div>
                  <h4>{report.official_name}</h4>
                  <b>{report.headline}</b>
                  <p>{report.recommendation}</p>
                  <div class="small-note">材料依据：{report.evidence}<br><br>
                  可能盲点：{report.blind_spot}<br>判断把握：{report.confidence}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.warning("主席需要自己判断：分歧来自专业视角、部门自保、材料缺口，还是牵头人真的在缩减执行。")


def _press_room_tab(game: ExecutivePresidentCareerGame) -> None:
    st.markdown("### 主席发布会")
    st.caption(
        "记者会根据你的上一句话继续追问。强调规则后会追问规则造成的代价；承诺帮助行业后会追问钱从哪里来；连续不评论也会成为新闻。"
    )
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
    st.markdown(f"**媒体：** {session.outlet}  \n**主题：** {session.topic}")
    for exchange in session.exchanges:
        st.markdown(f"#### 第{exchange.round_number}轮")
        st.write(f"**记者：** {exchange.question}")
        st.success(f"**主席：** “{exchange.quote}”")
        st.caption(exchange.consequence)
        if exchange.reporter_followup:
            st.write(f"**记者继续追问：** {exchange.reporter_followup}")

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
    _css()
    game = _session()
    packet = build_office_packet(game)
    office_state = _office_state(packet.packet_id)
    _sidebar(game)
    _header(game, packet)

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
        _desk_tab(game, packet)
    with tabs[1]:
        _dossier_tab(game, packet, office_state)
    with tabs[2]:
        _implementation_tab(game)
    with tabs[3]:
        _competing_reports_tab(game)
    with tabs[4]:
        _press_room_tab(game)
    with tabs[5]:
        _meetings_tab(game, packet)
    with tabs[6]:
        _executive_history_tab(game)
    with tabs[7]:
        _archive_tab(game)
    with tabs[8]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
