from football_republic.advanced_ecosystem import WorkloadManager
from football_republic.campaign import STRATEGIES, Strategy
from football_republic.deep_campaign import DeepCampaign
from football_republic.deep_scenario import build_deep_2026_scenario
from football_republic.ecosystem import ClubPyramidWorld
from football_republic.football import MatchResult
from football_republic.ordered_contracts import OrderedContractMarket


def started_campaign() -> DeepCampaign:
    campaign = DeepCampaign(strategy=Strategy.BALANCED)
    campaign.enact_plan(STRATEGIES[Strategy.BALANCED])
    return campaign


def test_national_cup_completes_a_full_four_round_bracket() -> None:
    campaign = started_campaign()
    campaign.run(12)

    cup = campaign.football.domestic_cup
    assert len(cup.results) == 13
    assert 1 in cup.champions
    assert cup.champions[1] in campaign.engine.state.clubs
    assert [item.stage for item in cup.results].count("final") == 1


def test_continental_competition_plays_groups_semifinals_and_final() -> None:
    campaign = started_campaign()
    campaign.run(12)

    competition = campaign.football.continental
    assert len(competition.group_results) == 24
    assert len(competition.knockout_results) == 3
    assert competition.champion_id is not None
    assert all(
        row.played == 6
        for table in competition.tables.values()
        for row in table.values()
    )


def test_congested_calendar_creates_extra_fitness_cost() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    club_id = "harbor"
    roster = world.rosters[club_id]
    for player in sorted(
        roster.players,
        key=lambda item: item.match_readiness,
        reverse=True,
    )[:18]:
        player.appearances = 1
    fitness_before = sum(player.fitness for player in roster.players)
    opponent = "phoenix"
    results = [
        MatchResult(
            "Calendar Test",
            1,
            index,
            5,
            club_id,
            opponent,
            state.clubs[club_id].name,
            state.clubs[opponent].name,
            1,
            0,
            1.2,
            0.7,
            53.0,
            20_000,
            300_000.0,
        )
        for index in range(1, 6)
    ]
    manager = WorkloadManager(seed=1)

    reports = manager.settle_month(5, results, state.clubs, world.rosters)

    report = next(item for item in reports if item.club_id == club_id)
    assert report.matches == 5
    assert report.congestion_level == "high"
    assert report.extra_fitness_cost > 0
    assert sum(player.fitness for player in roster.players) < fitness_before


def test_expired_contract_releases_a_nonessential_player() -> None:
    campaign = started_campaign()
    club_id = "harbor"
    roster = campaign.football.rosters[club_id]
    player = min(roster.players, key=lambda item: item.ability)
    player.contract_months = 1
    player.ability = 35.0
    player.potential = 35.0
    player.morale = 0.0

    campaign.advance(1, interactive=True)

    assert player not in roster.players
    assert player in campaign.football.contracts.free_agents
    assert any(
        item.player_id == player.id and item.action == "released"
        for item in campaign.football.contracts.contract_history
    )


def test_registration_window_occurs_after_month_six_policy_decision() -> None:
    campaign = started_campaign()
    campaign.advance(24, interactive=True)
    campaign.resolve_decision("transparent_reform")
    campaign.advance(24, interactive=True)

    assert campaign.engine.state.month == 6
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "transfer_policy"
    assert campaign.active_loans == 0

    campaign.resolve_decision("financial_control")
    campaign.advance(1, interactive=True)

    assert campaign.engine.state.month == 7
    assert campaign.football.contracts.loan_history
    assert all(
        item.start_month == 7
        for item in campaign.football.contracts.loan_history
        if item.status == "active"
    )


def test_development_loan_returns_to_parent_and_restores_roster() -> None:
    state = build_deep_2026_scenario()
    base_world = ClubPyramidWorld.build(state, seed=3033)
    market = OrderedContractMarket(seed=3533)
    for parent_id in base_world.pyramid.premier_ids:
        weakest = min(
            base_world.rosters[parent_id].players,
            key=lambda item: item.match_readiness,
        )
        weakest.age = 20
        weakest.potential = max(weakest.ability + 10.0, weakest.potential)
        weakest.contract_months = 24
    roster_counts = {
        club_id: len(roster.players)
        for club_id, roster in base_world.rosters.items()
    }

    market.advance_month(
        7,
        state.clubs,
        base_world.rosters,
        set(base_world.pyramid.premier_ids),
        set(base_world.pyramid.second_ids),
    )

    assert market.active_loans
    player_id, loan = next(iter(market.active_loans.items()))
    assert loan.player not in base_world.rosters[loan.parent_id].players
    assert loan.player in base_world.rosters[loan.borrower_id].players

    market.advance_month(
        12,
        state.clubs,
        base_world.rosters,
        set(base_world.pyramid.premier_ids),
        set(base_world.pyramid.second_ids),
    )

    assert loan.player in base_world.rosters[loan.parent_id].players
    assert player_id not in market.active_loans
    assert len(base_world.rosters[loan.parent_id].players) == roster_counts[loan.parent_id]


def test_full_term_preserves_all_domestic_player_objects() -> None:
    campaign = started_campaign()
    initial_ids = {
        player.id
        for roster in campaign.football.rosters.values()
        for player in roster.players
    }

    campaign.run(24)

    final_ids = {
        player.id
        for roster in campaign.football.rosters.values()
        for player in roster.players
    } | {player.id for player in campaign.football.contracts.free_agents}
    assert final_ids == initial_ids
    assert campaign.active_loans == 0


def test_full_term_contains_both_cups_and_continental_seasons() -> None:
    campaign = started_campaign()
    campaign.run(24)

    assert len(campaign.football.domestic_cup.results) == 26
    assert set(campaign.football.domestic_cup.champions) == {1, 2}
    assert len(campaign.football.continental_history) == 2
    assert sum(
        len(summary.domestic_clubs)
        for summary in campaign.football.continental_history
    ) == 4
    assert any(
        report.matches >= 3 and report.extra_fitness_cost > 0
        for report in campaign.football.workload.history
    )
    assert campaign.football.contracts.contract_history
