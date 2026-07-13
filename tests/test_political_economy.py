from football_republic.campaign import STRATEGIES, Strategy
from football_republic.deep_campaign import DeepCampaign
from football_republic.political_economy import AGENDA_DECISIONS


def started_campaign(strategy: Strategy = Strategy.BALANCED) -> DeepCampaign:
    campaign = DeepCampaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    return campaign


def test_month_two_opens_a_real_governance_agenda() -> None:
    campaign = started_campaign()

    campaign.advance(2, interactive=True)

    assert campaign.engine.state.month == 2
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "agenda_governance_compact"
    assert len(campaign.politics.stakeholders) == 9


def test_agenda_vote_records_supporters_opponents_and_a_public_promise() -> None:
    campaign = started_campaign()
    campaign.advance(2, interactive=True)
    for actor in campaign.politics.stakeholders.values():
        actor.support = 0.72
        actor.trust = 0.70

    record = campaign.resolve_decision("federal_compact")

    outcome = campaign.politics.agenda_history[-1]
    assert record.option_id == "federal_compact"
    assert outcome.passed
    assert outcome.yes_power > outcome.total_power / 2
    assert outcome.supporters
    assert campaign.politics.promises
    assert campaign.politics.promises[-1].metric == "execution"


def test_foundations_strategy_negotiates_player_welfare_rules() -> None:
    campaign = started_campaign(Strategy.FOUNDATIONS)

    campaign.advance(10)

    assert any(
        outcome.option_id == "player_welfare_compact"
        for outcome in campaign.politics.agenda_history
    )
    assert campaign.football.workload.congestion_multiplier == 0.72
    assert campaign.football.workload.international_release_cost == 3.4


def test_existing_crisis_decision_changes_persistent_stakeholder_memory() -> None:
    campaign = started_campaign()
    campaign.advance(2, interactive=True)
    campaign.resolve_decision("federal_compact")
    campaign.advance(2, interactive=True)
    supporters = campaign.politics.stakeholders["supporters_federation"]
    support_before = supporters.support
    memory_before = len(supporters.memory)

    campaign.resolve_decision("transparent_reform")

    assert supporters.support > support_before
    assert len(supporters.memory) == memory_before + 1
    assert "公开调查并建立全国医疗标准" in supporters.memory[-1]


def test_mobilized_opposition_creates_material_pressure() -> None:
    campaign = started_campaign()
    actor = campaign.politics.stakeholders["supporters_federation"]
    actor.support = 0.10
    actor.mobilization = 0.90
    trust_before = campaign.engine.state.fan_trust

    campaign.politics.advance_month(
        3,
        campaign.engine.state,
        campaign.football,
    )

    event = campaign.politics.event_history[-1]
    assert event.actor_id == "supporters_federation"
    assert event.event_type == "pressure"
    assert campaign.engine.state.fan_trust < trust_before


def test_kept_promise_increases_beneficiary_trust() -> None:
    campaign = started_campaign()
    decision = AGENDA_DECISIONS[2]
    for actor in campaign.politics.stakeholders.values():
        actor.support = 0.75
        actor.trust = 0.70
    campaign.politics.resolve_agenda(
        decision,
        "federal_compact",
        campaign.engine.state,
        campaign.football,
    )
    promise = campaign.politics.promises[-1]
    promise.due_month = 3
    for region in campaign.engine.state.regions.values():
        region.execution_capacity = min(1.0, region.execution_capacity + 0.20)
    beneficiary = campaign.politics.stakeholders["provincial_fas"]
    trust_before = beneficiary.trust

    campaign.politics.advance_month(
        3,
        campaign.engine.state,
        campaign.football,
    )

    assert promise.status == "kept"
    assert beneficiary.trust > trust_before
    assert beneficiary.promises_kept == 1


def test_broken_promise_creates_memory_and_mobilization() -> None:
    campaign = started_campaign()
    decision = AGENDA_DECISIONS[2]
    for actor in campaign.politics.stakeholders.values():
        actor.support = 0.75
        actor.trust = 0.70
    campaign.politics.resolve_agenda(
        decision,
        "federal_compact",
        campaign.engine.state,
        campaign.football,
    )
    promise = campaign.politics.promises[-1]
    promise.due_month = 3
    for region in campaign.engine.state.regions.values():
        region.execution_capacity = 0.10
    beneficiary = campaign.politics.stakeholders["provincial_fas"]
    mobilization_before = beneficiary.mobilization

    campaign.politics.advance_month(
        3,
        campaign.engine.state,
        campaign.football,
    )

    assert promise.status == "broken"
    assert beneficiary.promises_broken == 1
    assert beneficiary.mobilization > mobilization_before
    assert any("promise broken" in item for item in beneficiary.memory)


def test_full_term_builds_auditable_political_and_sporting_history() -> None:
    campaign = started_campaign()

    review = campaign.run(24)
    political_review = campaign.political_review

    assert review.score > 0
    assert len(campaign.politics.agenda_history) == 4
    assert len(campaign.decision_history) == 10
    assert len(campaign.politics.year_archives) == 2
    assert set(campaign.football.pyramid.champion_history) == {1, 2}
    assert all(item.premier_champion != "not recorded" for item in campaign.politics.year_archives)
    assert political_review.score > 0
    assert political_review.strongest_ally
    assert political_review.opposition_leader


def test_strategies_choose_distinct_commercial_coalitions() -> None:
    foundations = started_campaign(Strategy.FOUNDATIONS)
    quick = started_campaign(Strategy.QUICK_RESULTS)

    foundations.advance(14)
    quick.advance(14)

    foundation_choice = next(
        item.option_id
        for item in foundations.politics.agenda_history
        if item.agenda_id == "agenda_commercial_model"
    )
    quick_choice = next(
        item.option_id
        for item in quick.politics.agenda_history
        if item.agenda_id == "agenda_commercial_model"
    )
    assert foundation_choice == "solidarity_distribution"
    assert quick_choice == "star_club_growth"
