"""Public significance policy for adaptive time settlements.

Routine domestic league rounds remain visible in the monthly record but do not force the
president to stop.  National-team matches, knockout football, season settlement and
institutional changes do require a review.
"""

from __future__ import annotations

from typing import Any


def public_snapshot(game) -> dict[str, Any]:
    campaign = game.current_campaign
    state = campaign.engine.state
    football = campaign.football
    executive = getattr(game, "executive", None)
    mandates = executive.mandates if executive is not None else []
    pyramid = getattr(football, "pyramid", None)
    cup = getattr(football, "domestic_cup", None)
    continental = getattr(football, "continental", None)
    international = getattr(football, "international", None)

    league_results = len(getattr(pyramid, "all_results", ())) if pyramid is not None else 0
    international_results = len(getattr(international, "results", ())) if international is not None else 0
    cup_results = len(getattr(cup, "results", ())) if cup is not None else 0
    continental_group_results = (
        len(getattr(continental, "group_results", ())) if continental is not None else 0
    )
    continental_knockout_results = (
        len(getattr(continental, "knockout_results", ())) if continental is not None else 0
    )
    season_records = 0
    if pyramid is not None:
        season_records += len(getattr(pyramid, "season_history", ()))
        season_records += len(getattr(pyramid, "champion_history", {}))

    return {
        "treasury": round(float(state.treasury), 2),
        "fan_trust": round(float(state.fan_trust), 6),
        "national_position": int(international.user_position) if international is not None else 0,
        "coalition": round(float(campaign.politics.coalition_support), 6),
        "distressed": sum(
            club.license_status in {"administration", "excluded"}
            or club.wage_arrears_months >= 2
            for club in state.clubs.values()
        ),
        "active_cases": len(getattr(game.world, "active_cases", ())),
        "case_stages": tuple(
            sorted((case.id, case.stage) for case in getattr(game.world, "active_cases", ()))
        ),
        "mandate_states": tuple(sorted((item.id, item.status) for item in mandates)),
        "results_total": (
            league_results
            + international_results
            + cup_results
            + continental_group_results
            + continental_knockout_results
        ),
        "league_results": league_results,
        "international_results": international_results,
        "cup_results": cup_results,
        "continental_group_results": continental_group_results,
        "continental_knockout_results": continental_knockout_results,
        "season_records": season_records,
    }


def settlement_requires_review(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Return whether a monthly settlement deserves presidential interruption.

    A routine league or continental group round can pass inside a quiet fast-forward.
    Knockout football and national-team matches carry national political or institutional
    consequences and therefore stop the clock.
    """
    return any(
        (
            after["international_results"] != before["international_results"],
            after["cup_results"] != before["cup_results"],
            after["continental_knockout_results"]
            != before["continental_knockout_results"],
            after["season_records"] != before["season_records"],
            after["national_position"] != before["national_position"],
            after["distressed"] != before["distressed"],
            after["active_cases"] != before["active_cases"],
            after["case_stages"] != before["case_stages"],
            after["mandate_states"] != before["mandate_states"],
        )
    )


def install_into(adaptive_time_module) -> None:
    """Install the significance policy into the generic adaptive clock module."""
    adaptive_time_module._public_snapshot = public_snapshot
    adaptive_time_module._settlement_requires_review = settlement_requires_review
