"""Cinematic stadium matchday interface for the football-association chairman."""

from __future__ import annotations

from html import escape

import streamlit as st

from .matchday_web import (
    _authority_boundary,
    _camp_stage,
    _coach_card,
    _history,
    _mandate_stage,
    _release_stage,
    _review_stage,
    _squad_board,
    inject_matchday_css,
)


_STAGE_LABELS = {
    "briefing": "集训授权",
    "release": "俱乐部征调",
    "pre_match": "主席—主教练会议",
    "awaiting_match": "比赛日倒计时",
    "stadium_arrival": "主席抵达体育场",
    "post_whistle": "终场包厢反应",
    "mixed_zone": "混合采访区",
    "review": "主席办公室问责",
    "closed": "窗口结束",
}


def inject_stadium_css() -> None:
    st.markdown(
        """
        <style>
        .stadium-shell {position:relative;overflow:hidden;margin:0 0 18px;padding:25px;border:1px solid rgba(205,180,111,.28);border-radius:20px;background:linear-gradient(180deg,rgba(8,26,36,.98),rgba(5,15,23,.99));box-shadow:0 24px 70px rgba(0,0,0,.34);}
        .stadium-shell::before {content:"";position:absolute;inset:0;background:radial-gradient(ellipse at 50% 100%,rgba(63,139,91,.19),transparent 48%),linear-gradient(90deg,transparent 49.7%,rgba(255,255,255,.035) 50%,transparent 50.3%);pointer-events:none;}
        .stadium-top {position:relative;z-index:1;display:grid;grid-template-columns:1fr auto 1fr;gap:20px;align-items:center;text-align:center;}
        .stadium-team {color:#f0f4f5;font-size:1.25rem;font-weight:850;}.stadium-role {color:#7f95a4;font-size:.72rem;}.stadium-round {color:#d8ba70;font-size:.7rem;font-weight:850;letter-spacing:.13em;}.stadium-vs {margin:7px 0;color:#f5f5ef;font-size:1.85rem;font-weight:950;}.stadium-meta {color:#9aadb8;font-size:.76rem;line-height:1.55;}
        .stadium-stage {position:relative;z-index:1;margin-top:18px;padding:11px 14px;border-left:4px solid #d8ba70;background:rgba(255,255,255,.035);color:#dce5e9;font-size:.82rem;}
        .box-room {margin:13px 0;padding:18px;border:1px solid rgba(196,170,105,.24);border-radius:16px;background:linear-gradient(135deg,rgba(34,40,43,.88),rgba(13,28,37,.9));}
        .box-room h4 {margin:0 0 5px;color:#f1e7c7;}.box-room p {margin:0;color:#aebcc4;font-size:.78rem;line-height:1.55;}
        .guest-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:10px 0 18px;}.guest-card {padding:13px;border:1px solid rgba(137,162,181,.18);border-radius:12px;background:rgba(255,255,255,.028);}.guest-card b {color:#edf2f4;}.guest-card span {display:block;margin-top:3px;color:#d5b96e;font-size:.72rem;}.guest-card small {display:block;margin-top:7px;color:#8fa2ae;line-height:1.45;}
        .live-board {margin:15px 0;padding:24px;text-align:center;border:1px solid rgba(216,185,109,.3);border-radius:17px;background:radial-gradient(circle at 50% 0,rgba(216,185,109,.13),rgba(7,20,29,.96));}.live-board .score {color:#f6f5ef;font-size:3rem;font-weight:950;letter-spacing:-.06em;}.live-board .minor {color:#9db0bb;font-size:.78rem;}.live-board .label {color:#d8ba70;font-size:.77rem;font-weight:820;letter-spacing:.1em;text-transform:uppercase;}
        .moment {display:grid;grid-template-columns:48px 1fr;gap:12px;margin:7px 0;padding:11px 12px;border:1px solid rgba(124,151,169,.14);border-radius:11px;background:rgba(255,255,255,.023);}.moment.goal {border-color:rgba(216,185,109,.28);background:rgba(216,185,109,.055);}.moment.fulltime {border-color:rgba(100,180,129,.27);}.moment .minute {color:#d8ba70;font-weight:900;text-align:center;}.moment b {color:#eaf0f2;font-size:.86rem;}.moment p {margin:3px 0 0;color:#91a4af;font-size:.73rem;line-height:1.45;}
        .camera-note {margin:10px 0;padding:12px 14px;border:1px solid rgba(204,112,102,.2);border-radius:12px;background:rgba(117,45,42,.08);color:#c7d0d5;font-size:.8rem;line-height:1.55;}
        @media (max-width:760px) {.stadium-top {grid-template-columns:1fr 80px 1fr;gap:7px;}.stadium-shell {padding:18px 12px;}.stadium-vs {font-size:1.35rem;}.live-board .score {font-size:2.35rem;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_stadium_matchday_center(game) -> None:
    runtime = game.matchday
    window = runtime.sync(game)
    st.markdown("### 国家队比赛日指挥中心")
    st.caption("主席负责保障、礼宾、俱乐部协调和公开责任；主教练独立决定名单、阵型、首发、换人和临场指令。")
    _coach_card(runtime)

    if window is None:
        candidate = runtime._next_fixture(game)
        if candidate is None:
            st.info("当前任期的国家队预选赛赛程已经结束。")
        else:
            st.info(
                f"下一场：第{candidate[0]}轮，{candidate[5]}对阵{candidate[4]}。"
                "系统会先进入准备周，并在开赛前一天把主席带到体育场。"
            )
        _history(runtime)
        return

    _stadium_fixture_header(window)
    _authority_boundary()
    scene = runtime.scene_for_window(window.id)

    if window.stage in {"briefing", "release", "pre_match"}:
        _squad_board(window)
    if window.stage == "briefing":
        _camp_stage(game, runtime, window)
    elif window.stage == "release":
        _release_stage(game, runtime, window)
    elif window.stage == "pre_match":
        _mandate_stage(game, runtime, window)
    elif window.stage == "stadium_arrival":
        _arrival_stage(game, runtime, window, scene)
    elif window.stage == "awaiting_match":
        _awaiting_match_stage(window, scene)
    elif window.stage == "post_whistle":
        _timeline(window, scene)
        _post_whistle_stage(game, runtime, window, scene)
    elif window.stage == "mixed_zone":
        _timeline(window, scene)
        _mixed_zone_stage(game, runtime, window, scene)
    elif window.stage == "review":
        _timeline(window, scene)
        if scene is not None and scene.media_frame:
            st.markdown(
                f'<div class="camera-note"><b>现场形成的媒体画面：</b>{escape(scene.media_frame)}</div>',
                unsafe_allow_html=True,
            )
        _review_stage(game, runtime, window)

    if window.notes:
        st.markdown("#### 本窗口工作记录")
        for note in window.notes:
            st.caption("• " + note)
    _history(runtime)


def _stadium_fixture_header(window) -> None:
    stage = _STAGE_LABELS.get(window.stage, window.stage)
    st.markdown(
        f"""
        <section class="stadium-shell">
          <div class="stadium-top">
            <div><div class="stadium-team">Longhua</div><div class="stadium-role">国家代表队</div></div>
            <div><div class="stadium-round">预选赛第{window.round_number}轮</div><div class="stadium-vs">VS</div><div class="stadium-meta">{escape(window.match_date)}<br>{escape(window.venue)}<br>{escape(stage)}</div></div>
            <div><div class="stadium-team">{escape(window.opponent_name)}</div><div class="stadium-role">对手代表队</div></div>
          </div>
          <div class="stadium-stage"><b>本场政治与竞赛含义：</b>{escape(window.table_stakes)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _arrival_stage(game, runtime, window, scene) -> None:
    st.markdown("#### 主席代表团抵达体育场")
    st.warning("开赛前礼宾、座次和来宾构成会被摄像机完整记录；这不是装饰性选择。")
    choice = st.radio(
        "主席以什么方式进入比赛现场？",
        list(runtime.ARRIVAL_CHOICES),
        format_func=lambda key: runtime.ARRIVAL_CHOICES[key]["label"],
        key=f"stadium-arrival-{window.id}",
    )
    policy = runtime.ARRIVAL_CHOICES[choice]
    st.markdown(
        f"""
        <div class="box-room">
          <h4>{escape(policy['label'])}</h4>
          <p>{escape(policy['note'])}<br>礼宾与安保预算约¥{policy['cost'] / 1_000_000:.2f}M。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("确认主席包厢与入场方案", type="primary", key=f"stadium-arrival-submit-{window.id}"):
        game.resolve_stadium_arrival(choice)
        st.rerun()


def _awaiting_match_stage(window, scene) -> None:
    st.success("主席代表团已经入席。下一次时间推进将进入正式比赛结算；主席不能在包厢里点选首发或要求换人。")
    if scene is not None:
        _box_scene(scene)
    st.markdown(
        f"**当前可用名单：** {len(window.available_squad)}人　"
        f"**本窗口累计支出：** ¥{window.treasury_cost / 1_000_000:.2f}M"
    )


def _box_scene(scene) -> None:
    st.markdown(
        f"""
        <div class="box-room">
          <h4>{escape(scene.arrival_label or '主席包厢')}</h4>
          <p>{escape(scene.arrival_note)}<br>{escape(scene.atmosphere)}<br>{escape(scene.camera_focus)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if scene.guest_list:
        st.markdown("#### 主席包厢来宾")
        cards = "".join(
            f'<div class="guest-card"><b>{escape(item.name)}</b><span>{escape(item.role)}</span><small>{escape(item.constituency)}<br>{escape(item.posture)}</small></div>'
            for item in scene.guest_list
        )
        st.markdown(f'<div class="guest-grid">{cards}</div>', unsafe_allow_html=True)


def _timeline(window, scene) -> None:
    if scene is None or not scene.moments:
        st.info("正式赛场时间线尚未生成。")
        return
    _box_scene(scene)
    st.markdown(
        f"""
        <div class="live-board">
          <div class="label">FULL TIME · OFFICIAL RESULT</div>
          <div class="score">{escape(scene.final_score)}</div>
          <div class="minor">Longhua — {escape(window.opponent_name)} · 半场 {escape(scene.halftime_score)} · xG {escape(scene.xg_line)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("#### 比赛现场时间线")
    for moment in scene.moments:
        score = f"{moment.score_for}-{moment.score_against}" if moment.kind in {"goal", "halftime", "fulltime"} else ""
        st.markdown(
            f"""
            <div class="moment {escape(moment.kind)}">
              <div class="minute">{moment.minute}'</div>
              <div><b>{escape(moment.headline)} {escape(score)}</b><p>{escape(moment.detail)}</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _post_whistle_stage(game, runtime, window, scene) -> None:
    st.markdown("#### 终场后的主席镜头")
    st.warning("比赛已经结束，任何选择都不能改写比分。现在决定的是主席如何承担公共角色。")
    choice = st.radio(
        "终场哨响后，主席先去哪里？",
        list(runtime.POST_WHISTLE_CHOICES),
        format_func=lambda key: runtime.POST_WHISTLE_CHOICES[key],
        key=f"post-whistle-{window.id}",
    )
    if st.button("确认终场公开行动", type="primary", key=f"post-whistle-submit-{window.id}"):
        game.resolve_box_reaction(choice)
        st.rerun()


def _mixed_zone_stage(game, runtime, window, scene) -> None:
    st.markdown("#### 混合采访区")
    if scene is not None and scene.media_frame:
        st.markdown(
            f'<div class="camera-note"><b>媒体已经掌握的画面：</b>{escape(scene.media_frame)}</div>',
            unsafe_allow_html=True,
        )
    choice = st.radio(
        "主席面对第一轮赛后追问时采用什么口径？",
        list(runtime.MIXED_ZONE_CHOICES),
        format_func=lambda key: runtime.MIXED_ZONE_CHOICES[key],
        key=f"mixed-zone-{window.id}",
    )
    if st.button("完成混合采访区回应", type="primary", key=f"mixed-zone-submit-{window.id}"):
        game.resolve_mixed_zone(choice)
        st.rerun()
