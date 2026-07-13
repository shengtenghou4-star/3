from football_republic.campaign import Strategy
from football_republic.constitutional import ConstitutionalLongTermCampaign
from football_republic.scenario_history import ReplayableConstitutionalHistory


def test_initial_cabinet_has_five_named_offices() -> None:
    history = ConstitutionalLongTermCampaign(max_terms=2)

    assert set(history.cabinet) == set(history.OFFICES)
    assert len(history.appointment_history) == 5
    assert all(item.status == "serving" for item in history.cabinet.values())
    assert history.administration_history[0].president_name == history.current_president.name


def test_cabinet_monthly_effects_are_auditable() -> None:
    history = ConstitutionalLongTermCampaign(max_terms=1)

    history.advance(1, interactive=True)

    assert history.global_month == 1
    assert any("cabinet quality" in line for line in history.current_campaign.engine.audit_log)
    assert history.cabinet_quality > 0.5
    assert 0.0 <= history.capture_risk <= 1.0


def test_independent_inquiry_replaces_implicated_official() -> None:
    history = ConstitutionalLongTermCampaign(
        strategy=Strategy.FOUNDATIONS,
        max_terms=1,
    )
    old = history.cabinet["廉洁与纪律专员"]
    integrity_before = history.current_campaign.engine.state.integrity_reputation
    history.force_crisis(severity=0.84)

    record = history.resolve_decision("independent_inquiry")

    new = history.cabinet["廉洁与纪律专员"]
    assert record.option_id == "independent_inquiry"
    assert old.status == "suspended and referred"
    assert new.id != old.id
    assert new.style == "technocrat"
    assert history.current_campaign.engine.state.integrity_reputation > integrity_before


def test_protecting_inner_circle_can_force_no_confidence_resignation() -> None:
    history = ConstitutionalLongTermCampaign(
        strategy=Strategy.QUICK_RESULTS,
        max_terms=2,
    )
    outgoing = history.current_president
    history.force_crisis(severity=0.82)

    history.resolve_decision("protect_inner_circle")

    assert outgoing.status == "resigned"
    assert history.caretaker_active
    assert history.current_president.status == "caretaker"
    assert history.administration_history[0].exit_reason is not None
    assert any(item.event_type == "caretaker government" for item in history.constitutional_history)


def test_snap_election_changes_government_without_resetting_football_nation() -> None:
    history = ConstitutionalLongTermCampaign(max_terms=2)
    state = history.current_campaign.engine.state
    club_ids = tuple(sorted(state.clubs))
    player_ids = {
        player.id
        for roster in history.current_campaign.football.rosters.values()
        for player in roster.players
    }
    history.force_crisis(severity=0.90)
    history.resolve_decision("submit_resignation")
    caretaker_id = history.current_president.id

    history.advance(4, interactive=False)

    assert history.current_president.id != caretaker_id
    assert history.current_president.status == "incumbent"
    assert history.current_campaign.engine.state is state
    assert tuple(sorted(state.clubs)) == club_ids
    assert {
        player.id
        for roster in history.current_campaign.football.rosters.values()
        for player in roster.players
    } == player_ids
    assert history.local_month == 4
    assert any(item.event_type == "snap election" for item in history.constitutional_history)


def test_scheduled_rollover_preserves_or_replaces_cabinet_consistently() -> None:
    history = ConstitutionalLongTermCampaign(
        strategy=Strategy.BALANCED,
        max_terms=2,
    )
    original_president = history.current_president.id
    original_officials = {office: actor.id for office, actor in history.cabinet.items()}

    history.finish_current_term()

    assert history.term_index == 2
    if history.current_president.id == original_president:
        assert {office: actor.id for office, actor in history.cabinet.items()} == original_officials
    else:
        assert {office: actor.id for office, actor in history.cabinet.items()} != original_officials
    assert history.administration_history[-1].start_global_month == 24


def test_constitutional_save_replay_survives_midterm_transition() -> None:
    history = ReplayableConstitutionalHistory(max_terms=3)
    history.advance(4, interactive=False)
    history.force_crisis(severity=0.91)
    history.resolve_decision("submit_resignation")
    history.advance(5, interactive=False)
    payload = history.to_json()

    restored = ReplayableConstitutionalHistory.from_json(payload)

    assert restored.global_month == history.global_month
    assert restored.fingerprint() == history.fingerprint()
    assert restored.current_president.name == history.current_president.name
    assert [item.event_type for item in restored.constitutional_history] == [
        item.event_type for item in history.constitutional_history
    ]
    assert restored.to_dict()["injected_crises"] == history.to_dict()["injected_crises"]


def test_ten_year_history_allows_irregular_administrations() -> None:
    history = ConstitutionalLongTermCampaign(
        strategy=Strategy.QUICK_RESULTS,
        max_terms=5,
    )

    history.run_years(10)

    assert history.finished
    assert history.global_month == 120
    assert len(history.term_records) == 5
    assert len(history.administration_history) >= 5
    assert len(history.season_history) == 10
    assert all(item.end_global_month is not None for item in history.administration_history)
