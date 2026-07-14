"""Streamlit national-team command centre for the association chairman."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .national_team_command import DIRECTIVE_OPTIONS, REVIEW_OPTIONS


def inject_national_team_theme() -> None:
    st.markdown(
        """
        <style>
        .nt-command {
            border: 1px solid rgba(199, 166, 96, .32);
            border-radius: 22px;
            padding: 1.25rem 1.35rem;
            background:
                radial-gradient(circle at 82% 8%, rgba(204, 164, 81, .14), transparent 32%),
                linear-gradient(135deg, rgba(13, 36, 45, .98), rgba(8, 22, 29, .98));
            box-shadow: 0 18px 50px rgba(0, 0, 0, .24);
            margin-bottom: 1rem;
        }
        .nt-eyebrow {
            color: #d6b66d;
            font-size: .68rem;
            font-weight: 800;
            letter-spacing: .15em;
            text-transform: uppercase;
        }
        .nt-score {
            font-size: 2.1rem;
            font-weight: 900;
            letter-spacing: .03em;
            color: #f4f1e8;
            margin: .2rem 0;
        }
        .nt-subtle { color: #9fb1bb; font-size: .82rem; }
        .nt-pressure {
            border-left: 4px solid #bc4c48;
            padding: .72rem .9rem;
            background: rgba(126, 33, 35, .16);
            border-radius: 0 12px 12px 0;
            margin: .65rem 0;
        }
        .nt-order {
            border: 1px solid rgba(216, 185, 112, .34);
            background: rgba(232, 222, 191, .06);
            border-radius: 14px;
            padding: .85rem 1rem;
            margin: .5rem 0 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fixture_header(game, fixture: dict) -> None:
    international = game.current_campaign.football.international
    position = international.user_position
    runtime = game.national_team_command
    st.markdown(
        f"""
        <div class="nt-command">
          <div class="nt-eyebrow">NATIONAL TEAM OPERATIONS ROOM</div>
          <div class="nt-score">预选赛第{fixture['round_number']}轮 · {fixture['venue']}对阵{fixture['opponent_name']}</div>
          <div class="nt-subtle">
            当前排名第{position}位 · 对手公开强度评估{fixture['opponent_strength']:.1f}
            · 主教练{runtime.coach_name}（{runtime.coach_status}）
          </div>
          <div class="nt-pressure">
            主席负责公开姿态、跨俱乐部协调、资源保障和赛后问责。
            排阵型、首发和临场换人仍由教练组承担。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _directive_panel(game, fixture: dict) -> None:
    runtime = game.national_team_command
    directive = runtime.directive_for_global_month(fixture["global_month"])
    st.markdown("#### 赛前主席指令")
    if directive is not None:
        st.markdown(
            f"""
            <div class="nt-order">
              <b>{directive.option_title}</b><br>
              {directive.summary}<br><br>
              <span class="nt-subtle">对外口径：{directive.public_line}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if directive.applied:
            st.success("指令已进入执行，不能在赛后倒改赛前口径。")
        else:
            st.info("指令已经签署，将在本次比赛月结前进入技术与保障流程。")
        return

    option_id = st.radio(
        "选择主席在本窗口的公开姿态和协调重点",
        list(DIRECTIVE_OPTIONS),
        format_func=lambda value: DIRECTIVE_OPTIONS[value]["label"],
        key=f"national-directive-{fixture['global_month']}",
    )
    option = DIRECTIVE_OPTIONS[option_id]
    st.caption(option["summary"])
    st.info(f"拟定公开口径：{option['public_line']}")
    if st.button(
        "签发国家队比赛窗口指令",
        type="primary",
        use_container_width=True,
        key=f"sign-national-directive-{fixture['global_month']}",
    ):
        game.choose_match_directive(option_id=option_id)
        st.rerun()


def _pending_review_panel(game) -> None:
    runtime = game.national_team_command
    review = runtime.pending_review
    if review is None:
        return

    st.divider()
    st.markdown("### 赛后主席问责")
    st.markdown(
        f"""
        <div class="nt-command">
          <div class="nt-eyebrow">POST-MATCH PRESIDENTIAL REVIEW</div>
          <div class="nt-score">{review.venue}对阵{review.opponent_name} · {review.scoreline}</div>
          <div class="nt-subtle">
            结果：{review.result_label} · 预期进球{review.xg_summary}
            · 赛后排名第{review.table_position}位
          </div>
          <div class="nt-pressure">
            赛前主席指令：{review.directive_title}<br>
            当前主教练：{review.coach_name}。时间将在主席作出问责决定前停止。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    option_id = st.radio(
        "决定教练组和复盘方式",
        list(REVIEW_OPTIONS),
        format_func=lambda value: REVIEW_OPTIONS[value]["label"],
        key=f"national-review-{review.id}",
    )
    st.caption(REVIEW_OPTIONS[option_id]["summary"])
    if st.button(
        "签署赛后处理决定",
        type="primary",
        use_container_width=True,
        key=f"resolve-national-review-{review.id}",
    ):
        game.resolve_match_review(review_id=review.id, option_id=option_id)
        st.rerun()


def _latest_review(game) -> None:
    resolved = [
        item
        for item in game.national_team_command.reviews
        if item.status == "resolved"
    ]
    if not resolved:
        return
    review = resolved[-1]
    st.markdown("#### 上一次主席处理")
    st.success(f"{review.resolution_title}：{review.public_line}")
    for effect in review.effects:
        st.write(f"• {effect}")


def _competition_table(game) -> None:
    international = game.current_campaign.football.international
    rows = []
    for index, item in enumerate(international.sorted_table(), start=1):
        rows.append(
            {
                "排名": index,
                "球队": item.team_name,
                "场次": item.played,
                "胜": item.won,
                "平": item.drawn,
                "负": item.lost,
                "净胜球": item.goal_difference,
                "积分": item.points,
                "近况": "".join(item.form) or "—",
            }
        )
    st.markdown("#### 预选赛形势")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _recent_matches(game) -> None:
    international = game.current_campaign.football.international
    user_code = international.user_code
    matches = [
        item
        for item in international.results
        if user_code in {item.home_id, item.away_id}
    ][-5:]
    st.markdown("#### 最近国家队比赛")
    if not matches:
        st.info("本届预选赛尚未开赛。")
        return
    for item in reversed(matches):
        user_home = item.home_id == user_code
        opponent = item.away_name if user_home else item.home_name
        goals_for = item.home_goals if user_home else item.away_goals
        goals_against = item.away_goals if user_home else item.home_goals
        venue = "主场" if user_home else "客场"
        st.markdown(
            f"**第{item.round_number}轮 · {venue}对阵{opponent}　{goals_for}-{goals_against}**  "
            f"预期进球 {item.home_xg if user_home else item.away_xg:.2f}-"
            f"{item.away_xg if user_home else item.home_xg:.2f}"
        )


def _squad_availability(game) -> None:
    squad = game.current_campaign.football.current_squad
    rows = []
    for member in squad.members:
        fitness_label = (
            "充足"
            if member.fitness >= 82
            else "可用"
            if member.fitness >= 70
            else "偏低"
        )
        rows.append(
            {
                "球员": member.player_name,
                "位置": member.position,
                "俱乐部": member.club_name,
                "年龄": member.age,
                "体能判断": fitness_label,
                "俱乐部出场": member.appearances,
            }
        )
    st.markdown("#### 当前26人名单与可用性")
    st.caption("名单来自技术部门和真实俱乐部球员库；主席不能亲自点选首发，只能协调与问责。")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=430)


def render_national_team_command(game) -> None:
    inject_national_team_theme()
    runtime = game.national_team_command
    fixture = runtime.next_fixture(game)

    if fixture is not None:
        _fixture_header(game, fixture)
        _directive_panel(game, fixture)
    else:
        international = game.current_campaign.football.international
        st.markdown(
            f"""
            <div class="nt-command">
              <div class="nt-eyebrow">NATIONAL TEAM OPERATIONS ROOM</div>
              <div class="nt-score">国家队常态监控</div>
              <div class="nt-subtle">
                当前排名第{international.user_position}位 · 主教练{runtime.coach_name}
                （{runtime.coach_status}）
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("下一次月结不是国家队比赛窗口，技术部门继续跟踪球员状态和俱乐部负荷。")

    _pending_review_panel(game)
    _latest_review(game)

    left, right = st.columns([1.0, 1.0], gap="large")
    with left:
        _competition_table(game)
        _recent_matches(game)
    with right:
        _squad_availability(game)

    if runtime.coaching_changes:
        st.divider()
        st.markdown("#### 主教练更迭记录")
        frame = pd.DataFrame(
            [
                {
                    "月份": item.global_month,
                    "离任": item.outgoing_name,
                    "接任": item.incoming_name,
                    "原因": item.reason,
                    "成本": f"¥{item.cost / 1_000_000:.1f}M",
                }
                for item in reversed(runtime.coaching_changes)
            ]
        )
        st.dataframe(frame, hide_index=True, use_container_width=True)
