import pytest

from football_republic import Campaign, STRATEGIES, Strategy, build_2026_scenario
from football_republic.football import FootballWorld
from football_republic.market import TransferMarket, TransferPolicy


def started_campaign(strategy: Strategy = Strategy.BALANCED) -> Campaign:
    campaign = Campaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    return campaign


def test_interactive_time_stops_for_presidential_decision() -> None:
    campaign = started_campaign()

    campaign.advance(24, interactive=True)

    assert campaign.engine.state.month == 4
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "youth_safety_crisis"

    campaign.resolve_decision("transparent_reform")
    campaign.advance(24, interactive=True)

    assert campaign.engine.state.month == 6
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "transfer_policy"


def test_transparent_safety_reform_changes_real_capacity() -> None:
    campaign = started_campaign()
    campaign.advance(4, interactive=True)
    before_integrity = campaign.engine.state.integrity_reputation
    before_support = {
        key: region.parent_support
        for key, region in campaign.engine.state.regions.items()
    }
    before_medical = {
        key: roster.medical_quality
        for key, roster in campaign.football.rosters.items()
    }

    record = campaign.resolve_decision("transparent_reform")

    assert record.decision_id == "youth_safety_crisis"
    assert campaign.engine.state.integrity_reputation > before_integrity
    assert all(
        campaign.engine.state.regions[key].parent_support > value
        for key, value in before_support.items()
    )
    assert all(
        campaign.football.rosters[key].medical_quality > value
        for key, value in before_medical.items()
    )


def test_year_two_income_is_received_once_and_then_allocated() -> None:
    campaign = started_campaign()

    campaign.advance(24, interactive=True)
    campaign.resolve_decision("transparent_reform")
    campaign.advance(24, interactive=True)
    campaign.resolve_decision("financial_control")
    campaign.advance(24, interactive=True)
    campaign.resolve_decision("conditional_rescue")
    campaign.advance(24, interactive=True)

    assert campaign.engine.state.month == 12
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "year_two_budget"
    assert len(campaign.finance_reports) == 1
    report = campaign.finance_reports[0]
    assert report.total_income == pytest.approx(
        report.public_grant
        + report.commercial_distribution
        + report.performance_bonus
        + report.integrity_bonus
    )
    treasury_before_budget = campaign.engine.state.treasury

    campaign.resolve_decision("balanced_renewal")

    assert campaign.engine.state.treasury < treasury_before_budget
    campaign.run(24)
    assert len(campaign.finance_reports) == 1


def test_transfer_window_preserves_players_and_internal_cash() -> None:
    state = build_2026_scenario()
    world = FootballWorld.build(state, seed=2033)
    for club in state.clubs.values():
        club.cash = max(club.cash, 20_000_000)
    market = TransferMarket(
        policy=TransferPolicy.OPEN_MARKET,
        seed=7070,
    )
    players_before = sum(len(roster.players) for roster in world.rosters.values())
    cash_before = sum(club.cash for club in state.clubs.values())

    records = market.run_window(6, state.clubs, world.rosters)

    assert records
    assert sum(len(roster.players) for roster in world.rosters.values()) == players_before
    assert sum(club.cash for club in state.clubs.values()) == pytest.approx(cash_before)
    for record in records:
        assert record.fee > 0
        assert any(
            player.id == record.player_id
            for player in world.rosters[record.buyer_id].players
        )
        assert all(
            player.id != record.player_id
            for player in world.rosters[record.seller_id].players
        )


def test_full_strategies_resolve_all_six_governance_decisions() -> None:
    outcomes = {}
    for strategy in Strategy:
        campaign = started_campaign(strategy)
        review = campaign.run(24)
        outcomes[strategy] = (
            review.qualifier_position,
            round(review.youth_change, 3),
            round(campaign.engine.state.integrity_reputation, 3),
            len(campaign.transfer_market.history),
        )
        assert campaign.engine.state.month == 24
        assert campaign.current_decision is None
        assert len(campaign.decision_history) == 6
        assert len(campaign.finance_reports) == 1

    assert len(set(outcomes.values())) == 3
