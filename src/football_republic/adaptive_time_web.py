"""Streamlit presentation for the adaptive presidential calendar."""

from __future__ import annotations

from dataclasses import replace
from html import escape

import streamlit as st


_LEVEL_TONE = {
    "必须停下": "red",
    "危机节奏": "red",
    "高压节奏": "amber",
    "重点关注": "amber",
    "常规工作": "blue",
    "平稳行政期": "green",
}


def timed_office_packet(game, packet):
    """Use the real player-facing date without changing the monthly simulation packet."""
    return replace(
        packet,
        packet_id=f"{packet.packet_id}-{game.calendar.current_date.isoformat()}",
        date_label=game.calendar.date_label,
        weekday_label=game.calendar.weekday_label,
    )


def inject_timeflow_css() -> None:
    st.markdown(
        """
        <style>
        .time-console {
          position:relative;overflow:hidden;margin:0 0 18px;padding:18px 21px;
          border:1px solid rgba(145,169,189,.18);border-radius:17px;
          background:linear-gradient(105deg,rgba(13,29,42,.94),rgba(8,19,29,.96));
          box-shadow:0 18px 42px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.035);
        }
        .time-console::after {
          content:"";position:absolute;left:28px;right:28px;top:72px;height:1px;
          background:linear-gradient(90deg,rgba(217,185,109,.45),rgba(116,149,175,.18),transparent);
        }
        .time-head {position:relative;z-index:1;display:grid;grid-template-columns:190px minmax(0,1fr) minmax(220px,.7fr);gap:22px;align-items:start;}
        .time-eyebrow {color:#d9b96d;font-size:.65rem;font-weight:850;letter-spacing:.14em;text-transform:uppercase;}
        .time-date {margin-top:4px;color:#f1f5f7;font-size:1.35rem;font-weight:820;letter-spacing:-.03em;}
        .time-weekday {margin-top:2px;color:#8fa3b2;font-size:.75rem;}
        .time-pace {display:inline-flex;align-items:center;gap:7px;margin-top:7px;padding:5px 9px;border-radius:999px;border:1px solid rgba(139,164,184,.23);color:#c2d0da;background:rgba(255,255,255,.035);font-size:.72rem;}
        .time-pace::before {content:"";width:8px;height:8px;border-radius:50%;background:#6fa8d5;box-shadow:0 0 0 5px rgba(111,168,213,.10);}
        .time-pace.red::before {background:#d56761;box-shadow:0 0 0 5px rgba(213,103,97,.11);}
        .time-pace.amber::before {background:#d4ad59;box-shadow:0 0 0 5px rgba(212,173,89,.11);}
        .time-pace.green::before {background:#65b98b;box-shadow:0 0 0 5px rgba(101,185,139,.11);}
        .time-copy {position:relative;z-index:1;padding-top:4px;}
        .time-copy h4 {margin:0 0 6px;color:#eef4f7;font-size:1.04rem;}
        .time-copy p {margin:0;color:#91a4b3;font-size:.8rem;line-height:1.55;}
        .time-checkpoint {position:relative;z-index:1;padding:12px 14px;border-left:3px solid #d9b96d;background:rgba(217,185,109,.045);}
        .time-checkpoint b {display:block;color:#e9d18f;font-size:.74rem;margin-bottom:5px;}
        .time-checkpoint span {color:#dfe7ec;font-size:.82rem;line-height:1.45;}
        .time-signals {position:relative;z-index:1;display:flex;flex-wrap:wrap;gap:7px;margin-top:23px;}
        .time-signal {padding:6px 9px;border:1px solid rgba(138,162,181,.18);border-radius:9px;background:rgba(255,255,255,.025);color:#aebdc8;font-size:.72rem;}
        .time-signal strong {color:#e6edf1;font-weight:760;}
        .time-last {position:relative;z-index:1;margin-top:12px;padding-top:11px;border-top:1px solid rgba(132,156,176,.15);color:#8fa2b1;font-size:.75rem;}
        .time-last b {color:#dfe7ec;}
        .time-change {display:inline-block;margin:5px 6px 0 0;padding:4px 7px;border-radius:7px;background:rgba(255,255,255,.035);color:#9fb0bc;}
        .sidebar-clock {margin:0 0 10px;padding:12px 13px;border:1px solid rgba(217,185,109,.18);border-radius:12px;background:rgba(255,255,255,.03);}
        .sidebar-clock .date {color:#f1f5f7;font-size:1.02rem;font-weight:800;}
        .sidebar-clock .meta {margin-top:3px;color:#8fa3b2;font-size:.72rem;line-height:1.5;}
        @media (max-width:900px) {
          .time-head {grid-template-columns:1fr 1fr;}
          .time-checkpoint {grid-column:1/-1;}
        }
        @media (max-width:620px) {
          .time-head {grid-template-columns:1fr;gap:14px;}
          .time-console::after {display:none;}
          .time-signals {margin-top:15px;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_time_console(game) -> None:
    recommendation = game.time_recommendation()
    tone = _LEVEL_TONE.get(recommendation.attention_label, "blue")
    signals = "".join(
        f'<span class="time-signal"><strong>{escape(item.headline)}</strong> · {escape(item.source)}</span>'
        for item in recommendation.signals[:5]
    )
    last = game.calendar.last_result
    last_html = ""
    if last is not None:
        changes = "".join(
            f'<span class="time-change">{escape(item)}</span>' for item in last.changes[:6]
        )
        last_html = (
            '<div class="time-last"><b>上次时间推进：</b>'
            f'{escape(last.start_date)} → {escape(last.end_date)} · '
            f'{last.days_elapsed}天 / {last.world_months_elapsed}次月结<br>'
            f'<b>停止原因：</b>{escape(last.stopped_reason)}<br>{changes}</div>'
        )
    st.markdown(
        f"""
        <section class="time-console">
          <div class="time-head">
            <div>
              <div class="time-eyebrow">Presidential Calendar</div>
              <div class="time-date">{escape(game.calendar.date_label)}</div>
              <div class="time-weekday">{escape(game.calendar.weekday_label)} · 制度月M{game.local_month}</div>
              <div class="time-pace {escape(tone)}">{escape(recommendation.attention_label)} · {escape(recommendation.pace)}</div>
            </div>
            <div class="time-copy">
              <h4>{escape(recommendation.button_label)}</h4>
              <p>{escape(recommendation.rationale)}</p>
            </div>
            <div class="time-checkpoint">
              <b>下一已知硬节点</b>
              <span>{escape(recommendation.next_checkpoint)}</span>
            </div>
          </div>
          <div class="time-signals">{signals}</div>
          {last_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_clock(game) -> None:
    recommendation = game.time_recommendation()
    st.markdown(
        f"""
        <div class="sidebar-clock">
          <div class="date">{escape(game.calendar.date_label)}</div>
          <div class="meta">{escape(game.calendar.weekday_label)} · {escape(recommendation.attention_label)}<br>
          下一节点：{escape(recommendation.next_checkpoint)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    blocked = recommendation.days == 0
    if st.button(
        recommendation.button_label,
        type="primary",
        use_container_width=True,
        disabled=blocked,
        key="adaptive-time-primary",
    ):
        game.advance_time("adaptive")
        st.rerun()
    left, right = st.columns(2)
    if left.button(
        "细看1天",
        use_container_width=True,
        disabled=blocked,
        key="adaptive-time-day",
    ):
        game.advance_time("deliberate")
        st.rerun()
    if right.button(
        "快进至关注点",
        use_container_width=True,
        disabled=blocked,
        key="adaptive-time-fast",
    ):
        game.advance_time("fast")
        st.rerun()
    st.caption(recommendation.rationale)
    if blocked:
        st.error(recommendation.signals[0].detail)
