from dataclasses import asdict

import pytest

from football_republic.campaign import Strategy
from football_republic.president_career import PresidentCareerGame


def resigning_game() -> PresidentCareerGame:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=4)
    game.world.force_crisis(severity=0.94)
    assert game.current_decision is not None
    game.resolve_decision("submit_resignation")
    return game


def test_player_controls_one_fixed_president() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=4)

    assert game.player_id == game.world.current_president.id
    assert game.player_name == game.world.current_president.name
    assert game.can_act
    assert game.career_status == "serving"


def test_resignation_ends_playable_career_immediately() -> None:
    game = resigning_game()

    assert not game.can_act
    assert game.career_status == "ended"
    assert game.career_end_global_month == game.global_month
    assert game.legacy_report is not None
    assert game.world.current_president.id != game.player_id


def test_successor_decisions_are_not_exposed_to_player() -> None:
    game = resigning_game()
    game.world._begin_election("test successor convention")

    assert game.world.current_decision is not None
    assert game.current_decision is None
    with pytest.raises(RuntimeError, match="successor-government"):
        game.resolve_decision("anything")


def test_observer_mode_continues_world_without_restoring_control() -> None:
    game = resigning_game()
    legacy_before = game.legacy_report
    month_before = game.global_month

    game.observe(6)

    assert game.global_month > month_before
    assert game.observer_mode
    assert not game.can_act
    assert game.current_decision is None
    assert game.legacy_report == legacy_before


def test_observer_mode_is_unavailable_while_in_office() -> None:
    game = PresidentCareerGame(max_terms=2)

    with pytest.raises(RuntimeError, match="only after leaving office"):
        game.observe(1)


def test_public_people_hide_exact_private_attributes() -> None:
    game = PresidentCareerGame(max_terms=2)

    briefs = game.public_people()
    assert briefs
    forbidden = {"integrity", "loyalty", "network_power", "exposure", "ambition"}
    for brief in briefs:
        assert forbidden.isdisjoint(asdict(brief))


def test_only_disclosed_connections_reach_presidential_briefing() -> None:
    game = PresidentCareerGame(max_terms=2)
    assert any(not tie.disclosed for tie in game.world.patronage_ties.values())

    visible = game.disclosed_connections()

    visible_ids = {item.connection_id for item in visible}
    assert all(game.world.patronage_ties[item].disclosed for item in visible_ids)
    assert not any(
        item.id in visible_ids
        for item in game.world.patronage_ties.values()
        if not item.disclosed
    )


def test_public_case_brief_hides_evidence_probability() -> None:
    game = PresidentCareerGame(max_terms=2)
    subject = game.world.people["central-fa-chair"]
    subject.integrity = 0.05
    subject.network_power = 0.98
    subject.exposure = 0.95
    game.world.global_month = 6
    game.world._maybe_open_case()
    assert game.world.current_decision is not None
    assert game.world.current_decision.id.startswith("justice_referral_")
    game.resolve_decision("independent_referral")

    briefs = game.public_cases()
    assert briefs
    for brief in briefs:
        assert "evidence" not in asdict(brief)
        assert "independence" not in asdict(brief)


def test_stakeholder_estimates_are_categories_not_exact_scores() -> None:
    game = PresidentCareerGame(max_terms=2)

    estimates = game.stakeholder_estimates()

    assert len(estimates) == 9
    for estimate in estimates:
        payload = asdict(estimate)
        assert "support" not in payload
        assert "trust" not in payload
        assert "power" not in payload
        assert isinstance(estimate.support_estimate, str)


def test_save_replay_preserves_player_identity_and_career_end() -> None:
    game = resigning_game()
    game.observe(4)
    payload = game.to_json()

    restored = PresidentCareerGame.from_json(payload)

    assert restored.player_id == game.player_id
    assert restored.player_name == game.player_name
    assert restored.career_status == "ended"
    assert restored.observer_mode
    assert restored.legacy_report == game.legacy_report
    assert restored.fingerprint() == game.fingerprint()


def test_scheduled_defeat_ends_same_player_career() -> None:
    game = PresidentCareerGame(strategy=Strategy.QUICK_RESULTS, max_terms=3)
    state = game.current_campaign.engine.state
    state.national_team_strength = 30.0
    state.fan_trust = 0.15
    state.integrity_reputation = 0.20
    for actor in game.current_campaign.politics.stakeholders.values():
        actor.support = 0.12
        actor.trust = 0.12

    game.world.run_years(2)
    game._refresh_career_state()

    assert game.career_status == "ended"
    assert game.legacy_report is not None
    assert game.world.current_president.id != game.player_id
    assert game.career_end_reason
