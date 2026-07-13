from football_republic.campaign import Strategy
from football_republic.coalition_elections import CoalitionElectionHistory


def open_snap_election(
    strategy: Strategy = Strategy.BALANCED,
    *,
    max_terms: int = 3,
) -> CoalitionElectionHistory:
    history = CoalitionElectionHistory(strategy=strategy, max_terms=max_terms)
    history.force_crisis(severity=0.92)
    history.resolve_decision("submit_resignation")
    history.advance(3, interactive=True)
    history.advance(1, interactive=True)
    assert history.election_active
    return history


def finish_election(history: CoalitionElectionHistory) -> None:
    guard = 0
    while history.election_active and guard < 20:
        decision = history.current_decision
        assert decision is not None
        if decision.id.startswith("election_nomination_"):
            candidate = history._preferred_candidate()
            history.resolve_decision(f"nominate::{candidate.id}")
        elif decision.id.startswith("election_bargain_"):
            package = "coalition" if not history.election_history else "grand"
            history.resolve_decision(f"package::{package}")
        else:
            raise AssertionError(f"unexpected decision during election: {decision.id}")
        guard += 1
    assert guard < 20
    assert not history.election_active


def test_snap_convention_opens_with_three_distinct_routes() -> None:
    history = open_snap_election()
    election = history._election

    assert election is not None
    assert len(election.candidates) == 3
    assert {item.strategy for item in election.candidates.values()} == {
        Strategy.FOUNDATIONS,
        Strategy.BALANCED,
        Strategy.QUICK_RESULTS,
    }
    assert history.current_decision is not None
    assert history.current_decision.id.startswith("election_nomination_")


def test_nomination_is_separate_from_bargaining_package() -> None:
    history = open_snap_election()
    election = history._election
    assert election is not None
    candidate = next(iter(election.candidates.values()))

    history.resolve_decision(f"nominate::{candidate.id}")

    assert history.current_decision is not None
    assert history.current_decision.id.startswith("election_bargain_")
    assert {item.id for item in history.current_decision.options} == {
        "package::clean",
        "package::coalition",
        "package::grand",
    }


def test_bigger_bargain_creates_more_real_commitments() -> None:
    history = open_snap_election()
    election = history._election
    assert election is not None
    candidate = next(iter(election.candidates.values()))

    clean = history._build_commitments(candidate, "clean", 1)
    coalition = history._build_commitments(candidate, "coalition", 1)
    grand = history._build_commitments(candidate, "grand", 1)

    assert len(clean) == 0
    assert len(coalition) == 2
    assert len(grand) == 4
    assert {item.commitment_type for item in grand} >= {"office", "budget", "policy"}


def test_multi_round_election_forms_a_government_agreement() -> None:
    history = open_snap_election()

    finish_election(history)

    assert history.current_president.status == "incumbent"
    assert not history.caretaker_active
    assert history.government_agreements
    agreement = history.active_agreement
    assert agreement is not None
    assert agreement.president_name == history.current_president.name
    assert agreement.majority_share > 0
    assert history.election_history
    assert max(item.round_number for item in history.election_history) <= 3
    assert history.administration_history[-1].entry_reason == "coalition-election victory"


def test_coalition_promises_change_cabinet_and_treasury() -> None:
    history = open_snap_election()
    treasury_before = history.current_campaign.engine.state.treasury

    finish_election(history)

    agreement = history.active_agreement
    assert agreement is not None
    kept = [item for item in agreement.commitments if item.status == "kept"]
    assert kept
    assert any(item.commitment_type == "office" for item in kept)
    if any(item.commitment_type == "budget" for item in kept):
        assert history.current_campaign.engine.state.treasury < treasury_before
    promised_offices = {
        item.office
        for item in agreement.commitments
        if item.commitment_type == "office" and item.office
    }
    assert promised_offices <= set(history.cabinet)
    assert any("coalition allocation" in item.reason for item in history.appointment_history)


def test_broken_election_promise_hurts_the_sponsoring_bloc() -> None:
    history = open_snap_election()
    finish_election(history)
    agreement = history.active_agreement
    assert agreement is not None
    policy = next(
        (item for item in agreement.commitments if item.commitment_type == "policy"),
        None,
    )
    if policy is None:
        # A clean first-round majority is possible but uncommon; inject one measurable
        # policy commitment through the same generator rather than weakening the test.
        candidate = history._generate_candidates("test-promise")[0]
        policy = next(
            item
            for item in history._build_commitments(candidate, "grand", 1)
            if item.commitment_type == "policy"
        )
        agreement.commitments.append(policy)
    actor = history.current_campaign.politics.stakeholders[policy.actor_id]
    trust_before = actor.trust
    policy.target = 10**9
    policy.due_global_month = history.global_month

    history._settle_coalition_commitments()

    assert policy.status == "broken"
    assert actor.trust < trust_before
    assert actor.promises_broken >= 1


def test_collapsed_coalition_can_lose_confidence_vote() -> None:
    history = open_snap_election()
    finish_election(history)
    agreement = history.active_agreement
    assert agreement is not None
    agreement.start_global_month = history.global_month - 5
    for actor_id in agreement.coalition_blocs:
        actor = history.current_campaign.politics.stakeholders[actor_id]
        actor.support = 0.05
        actor.trust = 0.05
    agreement.stability = history._calculate_agreement_stability(agreement)

    history._maybe_trigger_coalition_breakdown()

    assert history.current_decision is not None
    assert history.current_decision.id.startswith("coalition_breakdown_")
    history.resolve_decision("confidence_vote")
    assert history.caretaker_active
    assert agreement.status == "collapsed"
    assert history.coalition_crises[-1].option_id == "confidence_vote"


def test_scheduled_open_succession_uses_weighted_convention() -> None:
    history = CoalitionElectionHistory(max_terms=2)

    successor, agreement = history._automatic_convention("test scheduled succession")

    assert successor.status == "incumbent"
    assert agreement.president_name == successor.name
    assert history.election_history
    assert agreement.coalition_blocs


def test_save_replay_preserves_election_and_coalition_state() -> None:
    history = open_snap_election(max_terms=4)
    finish_election(history)
    history.advance(2, interactive=False)
    payload = history.to_json()

    restored = CoalitionElectionHistory.from_json(payload)

    assert restored.global_month == history.global_month
    assert restored.current_president.name == history.current_president.name
    assert restored.fingerprint() == history.fingerprint()
    assert len(restored.election_history) == len(history.election_history)
    assert len(restored.government_agreements) == len(history.government_agreements)


def test_ten_year_history_survives_elections_and_coalition_governments() -> None:
    history = CoalitionElectionHistory(
        strategy=Strategy.QUICK_RESULTS,
        max_terms=5,
    )

    history.run_years(10)

    assert history.finished
    assert history.global_month == 120
    assert len(history.term_records) == 5
    assert len(history.season_history) == 10
    assert history.election_history
    assert history.government_agreements
    assert all(item.round_number <= 3 for item in history.election_history)
