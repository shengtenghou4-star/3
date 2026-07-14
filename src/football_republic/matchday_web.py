"""Streamlit national-team command center for the association president."""

from __future__ import annotations

from dataclasses import asdict
from html import escape

import pandas as pd
import streamlit as st

from .national_team_command import NationalTeamCommandRuntime


_STAGE_LABELS = {
    "briefing": "集训授权",
    "release": "俱乐部征调协调",
    "pre_match": "赛前主席—主教练会议",
    "awaiting_match": "比赛日倒计时",
    "review": "赛后问责",
    "closed": "窗口已结束",
}


def inject_matchday_css() -> None:
    st.markdown(
        """
        <style>
        .match-hq {
          position:relative;overflow:hidden;margin:0 0 18px;padding:24px 26px;
          border:1px solid rgba(119,163,193,.23);border-radius:19px;
          background:linear-gradient(120deg,rgba(10,35,51,.98),rgba(7,20,31,.98) 58%,rgba(18,34,42,.98));
          box-shadow:0 24px 60px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04);
        }
        .match-hq::before {content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(circle at 78% 12%,rgba(101,185,139,.13),transparent 24%),linear-gradient(90deg,transparent 49.8%,rgba(255,255,255,.025) 50%,transparent 50.2%);}
        .match-scoreboard {position:relative;z-index:1;display:grid;grid-template-columns:1fr 170px 1fr;gap:22px;align-items:center;text-align:center;}
        .team-mark {width:84px;height:84px;margin:0 auto 9px;display:grid;place-items:center;border:1px solid rgba(221,198,132,.5);border-radius:50%;color:#ecd591;background:radial-gradient(circle,rgba(217,185,109,.15),rgba(8,24,35,.5));font-family:Georgia,serif;font-size:1.45rem;font-weight:900;box-shadow:0 14px 30px rgba(0,0,0,.25);}
        .team-name {color:#f1f5f7;font-size:1.18rem;font-weight:820;}.team-role {color:#8499a8;font-size:.72rem;}
        .fixture-center {padding:13px 10px;border-left:1px solid rgba(217,185,109,.16);border-right:1px solid rgba(217,185,109,.16);}
        .fixture-round {color:#d9b96d;font-size:.67rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase;}
        .fixture-vs {margin:7px 0;color:#eef4f7;font-size:1.65rem;font-weight:900;}.fixture-meta {color:#91a4b2;font-size:.76rem;line-height:1.55;}
        .match-stage {position:relative;z-index:1;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:22px;}
        .stage-chip {padding:6px 10px;border:1px solid rgba(130,156,176,.18);border-radius:999px;color:#758a99;background:rgba(255,255,255,.025);font-size:.7rem;}
        .stage-chip.done {color:#9dbbaa;border-color:rgba(101,185,139,.24);}.stage-chip.current {color:#101820;border-color:#d9b96d;background:#d9b96d;font-weight:850;box-shadow:0 8px 18px rgba(217,185,109,.22);}
        .stakes-line {position:relative;z-index:1;margin-top:19px;padding:13px 16px;border-left:4px solid #d9b96d;background:rgba(255,255,255,.035);color:#dfe7eb;font-size:.84rem;line-height:1.55;}
        .coach-room {display:grid;grid-template-columns:92px 1fr;gap:17px;align-items:center;margin:9px 0 17px;padding:17px;border:1px solid rgba(137,162,181,.17);border-radius:15px;background:linear-gradient(145deg,rgba(18,39,54,.88),rgba(9,22,32,.88));}
        .coach-avatar {width:86px;height:96px;display:grid;place-items:center;border-radius:12px 12px 30px 30px;color:#e8d08b;background:linear-gradient(180deg,#294a61,#102837);font-family:Georgia,serif;font-size:1.45rem;font-weight:900;box-shadow:inset 0 -18px 30px rgba(0,0,0,.18),0 12px 24px rgba(0,0,0,.22);}
        .coach-copy h4 {margin:0;color:#eef4f6;font-size:1.18rem;}.coach-philosophy {color:#d9b96d;font-size:.75rem;margin-top:2px;}.coach-public {display:flex;flex-wrap:wrap;gap:7px;margin-top:9px;}.coach-public span {padding:5px 8px;border:1px solid rgba(137,162,181,.18);border-radius:8px;color:#9eb0bc;background:rgba(255,255,255,.025);font-size:.7rem;}
        .authority-note {margin:9px 0 17px;padding:13px 15px;border:1px solid rgba(111,168,213,.2);border-radius:12px;color:#b8c8d2;background:rgba(111,168,213,.055);font-size:.8rem;line-height:1.55;}
        .dispute-card {margin:9px 0;padding:14px 15px;border:1px solid rgba(213,103,97,.23);border-radius:13px;background:rgba(119,44,42,.09);}.dispute-card h4 {margin:0 0 5px;color:#f0d8d6;font-size:.96rem;}.dispute-card p {margin:0;color:#aebbc4;font-size:.76rem;line-height:1.5;}
        .result-board {margin:13px 0;padding:22px;text-align:center;border:1px solid rgba(217,185,109,.27);border-radius:16px;background:radial-gradient(circle at 50% 0,rgba(217,185,109,.11),rgba(8,21,31,.92));box-shadow:0 18px 38px rgba(0,0,0,.22);}.result-board .score {color:#f2f5f6;font-size:2.6rem;font-weight:900;letter-spacing:-.06em;}.result-board .summary {color:#d9b96d;font-size:.9rem;font-weight:760;}.result-board .data {margin-top:8px;color:#91a4b2;font-size:.76rem;}
        .window-note {display:block;margin:5px 0;padding:6px 9px;border-radius:8px;background:rgba(255,255,255,.03);color:#9fb0bc;font-size:.73rem;}
        @media (max-width:760px) {.match-scoreboard {grid-template-columns:1fr 92px 1fr;gap:8px;}.team-mark {width:64px;height:64px;}.fixture-center {padding:9px 4px;}.coach-room {grid-template-columns:70px 1fr;}.coach-avatar {width:66px;height:76px;}.match-hq {padding:19px 13px;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_matchday_center(game) -> None:
    runtime = game.matchday
    window = runtime.sync(game)
    st.markdown("### 国家队比赛日指挥中心")
    st.caption("主席负责协会资源、俱乐部协调和政治后果；名单、阵型与临场换人属于主教练。")
    _coach_card(runtime)

    if window is None:
        candidate = runtime._next_fixture(game)
        if candidate is None:
            st.info("当前任期的国家队预选赛赛程已经结束。")
        else:
            st.info(
                f"下一场：第{candidate[0]}轮，{candidate[5]}对阵{candidate[4]}。"
                "自适应日历会在比赛前一周自动进入国家队准备期。"
            )
        _history(runtime)
        return

    _fixture_header(window)
    _authority_boundary()
    _squad_board(window)

    if window.stage == "briefing":
        _camp_stage(game, runtime, window)
    elif window.stage == "release":
        _release_stage(game, runtime, window)
    elif window.stage == "pre_match":
        _mandate_stage(game, runtime, window)
    elif window.stage == "awaiting_match":
        st.success("名单、集训和主席授权已经确定。使用时间控制推进到比赛日；系统不会跳过正式结果。")
        st.markdown(
            f"**当前可用名单：** {len(window.available_squad)}人　"
            f"**本窗口支出：** ¥{window.treasury_cost / 1_000_000:.2f}M"
        )
    elif window.stage == "review":
        _review_stage(game, runtime, window)

    if window.notes:
        st.markdown("#### 窗口工作记录")
        for note in window.notes:
            st.markdown(f'<span class="window-note">{escape(note)}</span>', unsafe_allow_html=True)
    _history(runtime)


def _fixture_header(window) -> None:
    stages = ("briefing", "release", "pre_match", "awaiting_match", "review")
    current = stages.index(window.stage) if window.stage in stages else len(stages)
    labels = ("集训", "征调", "赛前会", "比赛日", "赛后复盘")
    chips = "".join(
        f'<span class="stage-chip {"done" if index < current else "current" if index == current else ""}">{label}</span>'
        for index, label in enumerate(labels)
    )
    st.markdown(
        f"""
        <section class="match-hq">
          <div class="match-scoreboard">
            <div><div class="team-mark">LON</div><div class="team-name">Longhua</div><div class="team-role">国家代表队</div></div>
            <div class="fixture-center"><div class="fixture-round">预选赛第{window.round_number}轮</div><div class="fixture-vs">VS</div><div class="fixture-meta">{escape(window.venue)}<br>{escape(window.match_date)}<br>{escape(_STAGE_LABELS[window.stage])}</div></div>
            <div><div class="team-mark">{escape(window.opponent_code)}</div><div class="team-name">{escape(window.opponent_name)}</div><div class="team-role">对手代表队</div></div>
          </div>
          <div class="match-stage">{chips}</div>
          <div class="stakes-line"><b>积分与政治含义：</b>{escape(window.table_stakes)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _coach_card(runtime: NationalTeamCommandRuntime) -> None:
    coach = runtime.coach
    initials = "".join(part[:1] for part in coach.name.split()[:2])
    st.markdown(
        f"""
        <div class="coach-room">
          <div class="coach-avatar">{escape(initials)}</div>
          <div class="coach-copy">
            <h4>{escape(coach.name)} · 国家队主教练</h4>
            <div class="coach-philosophy">{escape(coach.philosophy)}</div>
            <div class="coach-public">
              <span>公众声誉：{escape(coach.public_reputation_label)}</span>
              <span>与主席关系：{escape(coach.relationship_label)}</span>
              <span>职位安全：{escape(coach.job_security_label)}</span>
              <span>{escape(coach.pressure_label)}</span>
              <span>战绩 {coach.wins}胜{coach.draws}平{coach.losses}负</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _authority_boundary() -> None:
    st.markdown(
        '<div class="authority-note"><b>权力边界：</b>主教练独立决定征召名单、阵型、首发和换人。'
        '主席可以要求解释、设定协会目标和保障资源，但不能在这个界面直接排兵布阵。越过边界会在后续版本作为政治干预事件，而不是正常操作。</div>',
        unsafe_allow_html=True,
    )


def _squad_board(window) -> None:
    st.markdown("#### 主教练提交的国家队名单")
    frame = pd.DataFrame([asdict(item) for item in window.squad])
    if not frame.empty:
        frame["availability"] = frame["player_id"].apply(
            lambda value: "退出本期名单" if value in window.unavailable_player_ids else "在队"
        )
        frame = frame.rename(
            columns={
                "player_name": "球员",
                "club_name": "俱乐部",
                "position": "位置",
                "age": "年龄",
                "role": "教练组定位",
                "medical_status": "医疗状态",
                "availability": "当前状态",
            }
        )
        st.dataframe(
            frame[["球员", "俱乐部", "位置", "年龄", "教练组定位", "医疗状态", "当前状态"]],
            hide_index=True,
            use_container_width=True,
            height=390,
        )
    if window.omitted_players:
        st.caption("技术部门重点落选观察：" + "、".join(window.omitted_players[:8]))


def _camp_stage(game, runtime, window) -> None:
    st.markdown("#### 主席决定：集训和保障标准")
    choice = st.radio(
        "协会为本期国家队提供什么级别的准备条件？",
        list(runtime.CAMP_CHOICES),
        format_func=lambda key: runtime.CAMP_CHOICES[key]["label"],
        key=f"camp-{window.id}",
    )
    policy = runtime.CAMP_CHOICES[choice]
    st.info(
        f"预算约¥{policy['cost'] / 1_000_000:.2f}M。{policy['note']}"
    )
    if st.button("批准本期集训方案", type="primary", key=f"camp-submit-{window.id}"):
        game.resolve_match_camp(choice)
        st.rerun()


def _release_stage(game, runtime, window) -> None:
    st.markdown("#### 俱乐部放人与医疗争议")
    for dispute in window.disputes:
        st.markdown(
            f"""
            <div class="dispute-card">
              <h4>{escape(dispute.club_name)} · {escape(dispute.severity)}优先级</h4>
              <p>{escape(dispute.public_reason)}<br>涉及：{escape('、'.join(dispute.player_names))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    choice = st.radio(
        "主席采用哪种统一协调口径？",
        list(runtime.RELEASE_CHOICES),
        format_func=lambda key: runtime.RELEASE_CHOICES[key]["label"],
        key=f"release-{window.id}",
    )
    if st.button("形成征调协调决定", type="primary", key=f"release-submit-{window.id}"):
        game.resolve_club_release(choice)
        st.rerun()


def _mandate_stage(game, runtime, window) -> None:
    st.markdown("#### 赛前主席—主教练会议")
    st.warning(
        f"{runtime.coach.name}已经提交名单和内部比赛计划。主席需要决定公开支持程度和结果目标，但不能修改阵型。"
    )
    choice = st.radio(
        "主席向教练组和公众释放什么信号？",
        list(runtime.MANDATE_CHOICES),
        format_func=lambda key: runtime.MANDATE_CHOICES[key]["label"],
        key=f"mandate-{window.id}",
    )
    if st.button("结束赛前会议", type="primary", key=f"mandate-submit-{window.id}"):
        game.set_match_mandate(choice)
        st.rerun()


def _review_stage(game, runtime, window) -> None:
    result = window.result or {}
    st.markdown("#### 比赛结果与主席问责")
    st.markdown(
        f"""
        <div class="result-board">
          <div class="summary">{escape(window.result_summary)}</div>
          <div class="score">{result.get('home_goals', '—')} — {result.get('away_goals', '—')}</div>
          <div class="data">xG {result.get('home_xg', 0):.2f} — {result.get('away_xg', 0):.2f} · 到场 {result.get('attendance', 0):,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    choice = st.radio(
        "主席如何处理本场比赛后的责任？",
        list(runtime.REVIEW_CHOICES),
        format_func=lambda key: runtime.REVIEW_CHOICES[key],
        key=f"review-{window.id}",
    )
    if choice == "dismiss_coach":
        st.error("解雇会产生解约和紧急遴选成本；即使赢球后解雇，也可能被视为政治干预。")
    if st.button("签署赛后处理意见", type="primary", key=f"review-submit-{window.id}"):
        game.resolve_match_review(choice)
        st.rerun()


def _history(runtime: NationalTeamCommandRuntime) -> None:
    closed = [item for item in reversed(runtime.windows) if item.stage == "closed"]
    if not closed:
        return
    with st.expander("历次国家队比赛窗口档案"):
        rows = []
        for item in closed:
            rows.append(
                {
                    "轮次": item.round_number,
                    "对手": item.opponent_name,
                    "主客场": item.venue,
                    "结果": item.result_summary,
                    "集训": runtime.CAMP_CHOICES.get(item.camp_choice, {}).get("label", item.camp_choice),
                    "征调": runtime.RELEASE_CHOICES.get(item.release_choice, {}).get("label", item.release_choice or "无争议"),
                    "赛后": runtime.REVIEW_CHOICES.get(item.review_choice, item.review_choice),
                    "支出": item.treasury_cost,
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
