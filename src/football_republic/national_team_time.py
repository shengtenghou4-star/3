"""Adaptive-time responsibility gates for national-team match windows."""

from __future__ import annotations


def install_into(adaptive_time_module) -> None:
    if getattr(adaptive_time_module, "_national_team_command_installed", False):
        return

    original_assess_attention = adaptive_time_module.assess_attention

    def assess_attention(game, current_date):
        signals = list(original_assess_attention(game, current_date))
        runtime = getattr(game, "national_team_command", None)
        if runtime is None or not game.can_act:
            return tuple(signals)

        additions = []
        pending = runtime.pending_review
        if pending is not None:
            additions.append(
                adaptive_time_module.AttentionSignal(
                    f"match-review:{pending.match_id}",
                    5,
                    "国家队赛后问责尚未完成",
                    f"{pending.venue}对阵{pending.opponent_name}，比分{pending.scoreline}。主席必须决定教练组去留与复盘方式。",
                    True,
                    "国家队技术总监",
                )
            )

        fixture = runtime.next_fixture(game)
        if (
            fixture is not None
            and adaptive_time_module._days_to_next_month(current_date) <= 7
            and runtime.directive_for_global_month(fixture["global_month"]) is None
        ):
            additions.append(
                adaptive_time_module.AttentionSignal(
                    f"match-directive:g{fixture['global_month']}",
                    5,
                    "国家队赛前主席口径尚未确定",
                    f"预选赛第{fixture['round_number']}轮将{fixture['venue']}对阵{fixture['opponent_name']}。需要明确主席公开姿态与资源协调重点。",
                    True,
                    "国家队技术总监",
                )
            )

        if additions:
            signals = [
                item
                for item in signals
                if item.code != "routine-administration"
            ]
            signals.extend(additions)
        return tuple(sorted(signals, key=lambda item: (-item.level, item.code)))

    adaptive_time_module.assess_attention = assess_attention
    adaptive_time_module._national_team_command_installed = True
