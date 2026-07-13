import pytest

from football_republic.campaign import Strategy
from football_republic.chairman_career import ChairmanCareer


def advance_to_month(career: ChairmanCareer, target: int) -> None:
    guard = 0
    while career.global_month < target and career.player_active:
        if career.player_decision is not None:
            career._auto_resolve_current()
        else:
            career.advance(1, interactive=True)
        guard += 1
        if guard > 400:
            raise AssertionError("career did not reach target month")


def advance_until_justice(career: ChairmanCareer, limit: int = 8) -> None:
    guard = 0
    while career.player_active and career.global_month <= limit:
        decision = career.player_decision
        if decision is not None and decision.id.startswith("justice_referral_"):
            return
        if decision is not None:
            career._auto_resolve_current()
        else:
            career.advance(1, interactive=True)
        guard += 1
        if guard > 400:
            break
    raise AssertionError("justice referral did not become reachable")


def resigning_career() -> ChairmanCareer:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=4)
    career.force_crisis(severity=0.93)
    career.resolve_decision("submit_resignation")
    return career


def test_player_is_bound_to_opening_chairman() -> None:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=4)

    assert career.player_active
    assert career.current_president.id == career.player_president_id
    assert career.player_name == career.current_president.name
    assert not career.observer_mode


def test_resignation_ends_playable_career_immediately() -> None:
    career = resigning_career()

    assert not career.player_active
    assert career.caretaker_active
    assert career.current_president.id != career.player_president_id
    assert career.player_decision is None
    assert career.career_end_reason is not None
    assert career.legacy_report is not None


def test_player_cannot_resolve_successor_decisions() -> None:
    career = resigning_career()
    career.observe(4)

    if career.current_decision is None:
        career.observe(2)
    assert not career.player_active
    with pytest.raises(RuntimeError, match="left office"):
        career.resolve_decision("anything")


def test_observer_mode_continues_world_without_restoring_control() -> None:
    career = resigning_career()
    start_month = career.global_month
    player_id = career.player_president_id

    career.observe(8)

    assert career.global_month > start_month
    assert career.player_president_id == player_id
    assert not career.player_active
    assert career.observer_mode
    assert career.player_decision is None


def test_normal_advance_is_frozen_after_career_end() -> None:
    career = resigning_career()
    start_month = career.global_month

    career.advance(12, interactive=False)

    assert career.global_month == start_month


def test_stakeholder_signals_expose_posture_not_hidden_scores() -> None:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=2)
    signals = career.stakeholder_signals()

    assert len(signals) == 9
    assert all(item.posture for item in signals)
    assert all(item.confidence in {"高", "中", "低"} for item in signals)
    assert not hasattr(signals[0], "support")
    assert not hasattr(signals[0], "trust")
    assert not hasattr(signals[0], "power")


def test_official_assessments_hide_integrity_and_network_numbers() -> None:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=2)
    assessments = career.official_assessments()

    assert len(assessments) == 5
    assert all(item.delivery for item in assessments)
    assert all(item.public_integrity_signal for item in assessments)
    assert not hasattr(assessments[0], "integrity")
    assert not hasattr(assessments[0], "network_power")
    assert not hasattr(assessments[0], "loyalty")


def test_public_case_docket_omits_hidden_probability_fields() -> None:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=3)
    subject = career.people["central-fa-chair"]
    subject.integrity = 0.05
    subject.network_power = 0.98
    for tie in career._ties_for(subject.id):
        tie.strength = max(tie.strength, 0.90)
    advance_until_justice(career)
    career.resolve_decision("independent_referral")

    docket = career.public_case_docket()

    assert docket
    assert "evidence" not in docket[0]
    assert "independence" not in docket[0]
    assert "related_ties" not in docket[0]


def test_legacy_report_is_personal_not_successor_history() -> None:
    career = resigning_career()
    report = career.legacy_report
    assert report is not None

    assert report.chairman_name == career.player_name
    assert report.end_global_month == career.career_end_month
    assert report.months_in_office == career.career_end_month
    assert report.exit_reason == career.career_end_reason
    assert report.legacy_grade


def test_json_replay_preserves_career_end_and_observer_state() -> None:
    career = resigning_career()
    career.observe(9)
    payload = career.to_json()

    restored = ChairmanCareer.from_json(payload)

    assert restored.fingerprint() == career.fingerprint()
    assert restored.player_president_id == career.player_president_id
    assert restored.player_active is False
    assert restored.observer_mode is True
    assert restored.career_end_month == career.career_end_month
    assert restored.career_end_reason == career.career_end_reason


def test_strong_incumbent_can_continue_as_same_player_after_renewal() -> None:
    career = ChairmanCareer(strategy=Strategy.FOUNDATIONS, max_terms=4)
    advance_to_month(career, 23)
    state = career.current_campaign.engine.state
    state.fan_trust = 0.92
    state.integrity_reputation = 0.92
    state.league_financial_health = 0.88
    state.national_team_strength = 72.0
    state.political_capital = 0.90
    for actor in career.current_campaign.politics.stakeholders.values():
        actor.support = 0.90
        actor.trust = 0.90
        actor.mobilization = 0.05

    while career.term_index == 1 and career.player_active:
        if career.player_decision is not None:
            career._auto_resolve_current()
        else:
            career.advance(1, interactive=True)

    assert career.player_active
    assert career.term_index == 2
    assert career.current_president.id == career.player_president_id


def test_failed_renewal_ends_career_instead_of_transferring_control() -> None:
    career = ChairmanCareer(strategy=Strategy.BALANCED, max_terms=4)
    advance_to_month(career, 23)
    state = career.current_campaign.engine.state
    state.fan_trust = 0.08
    state.integrity_reputation = 0.12
    state.league_financial_health = 0.15
    state.national_team_strength = 35.0
    state.political_capital = 0.05
    for actor in career.current_campaign.politics.stakeholders.values():
        actor.support = 0.08
        actor.trust = 0.10
        actor.mobilization = 0.90

    while career.term_index == 1 and career.player_active:
        if career.player_decision is not None:
            career._auto_resolve_current()
        else:
            career.advance(1, interactive=True)

    assert not career.player_active
    assert career.current_president.id != career.player_president_id
    assert career.player_decision is None
