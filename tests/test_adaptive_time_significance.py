from pathlib import Path

import football_republic.adaptive_time as adaptive_time
from football_republic.adaptive_time_significance import (
    public_snapshot,
    settlement_requires_review,
)
from football_republic.executive_president_career import ExecutivePresidentCareerGame


ROOT = Path(__file__).resolve().parents[1]
SIGNIFICANCE_SOURCE = (
    ROOT / "src" / "football_republic" / "adaptive_time_significance.py"
)


def _snapshot(**changes):
    base = {
        "treasury": 100.0,
        "fan_trust": 0.5,
        "national_position": 3,
        "coalition": 0.55,
        "distressed": 0,
        "active_cases": 0,
        "case_stages": (),
        "mandate_states": (),
        "results_total": 0,
        "league_results": 0,
        "international_results": 0,
        "cup_results": 0,
        "continental_group_results": 0,
        "continental_knockout_results": 0,
        "season_records": 0,
    }
    base.update(changes)
    return base


def test_routine_domestic_league_round_does_not_force_a_presidential_stop() -> None:
    before = _snapshot()
    after = _snapshot(results_total=3, league_results=3)

    assert settlement_requires_review(before, after) is False


def test_continental_group_round_does_not_force_a_presidential_stop() -> None:
    before = _snapshot()
    after = _snapshot(results_total=4, continental_group_results=4)

    assert settlement_requires_review(before, after) is False


def test_national_team_match_requires_review() -> None:
    before = _snapshot()
    after = _snapshot(results_total=3, international_results=3, national_position=4)

    assert settlement_requires_review(before, after) is True


def test_domestic_knockout_round_requires_review() -> None:
    before = _snapshot()
    after = _snapshot(results_total=6, cup_results=6)

    assert settlement_requires_review(before, after) is True


def test_continental_knockout_and_season_settlement_require_review() -> None:
    before = _snapshot()

    assert settlement_requires_review(
        before,
        _snapshot(results_total=1, continental_knockout_results=1),
    )
    assert settlement_requires_review(before, _snapshot(season_records=1))


def test_institutional_change_still_stops_even_without_a_match() -> None:
    before = _snapshot()

    assert settlement_requires_review(before, _snapshot(distressed=1))
    assert settlement_requires_review(before, _snapshot(active_cases=1))
    assert settlement_requires_review(
        before,
        _snapshot(mandate_states=(("m1", "delayed"),)),
    )


def test_executive_career_installs_the_significance_policy() -> None:
    game = ExecutivePresidentCareerGame()
    snapshot = adaptive_time._public_snapshot(game)

    assert adaptive_time._public_snapshot is public_snapshot
    assert adaptive_time._settlement_requires_review is settlement_requires_review
    assert "league_results" in snapshot
    assert "continental_knockout_results" in snapshot


def test_significance_module_compiles_without_ui_dependencies() -> None:
    source = SIGNIFICANCE_SOURCE.read_text(encoding="utf-8")

    compile(source, str(SIGNIFICANCE_SOURCE), "exec")
    assert "streamlit" not in source
    assert "hidden_delivery_quality" not in source
    assert "competence" not in source
