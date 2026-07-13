from football_republic.advanced_ecosystem import AdvancedClubWorld
from football_republic.campaign import STRATEGIES, Strategy
from football_republic.deep_campaign import DeepCampaign
from football_republic.deep_scenario import build_deep_2026_scenario
from football_republic.ecosystem import ClubPyramidWorld
from football_republic.football import MatchResult
from football_republic.generational_economy import (
    AcademyLifecycleSystem,
    InsolvencySystem,
    SponsorshipSystem,
    StadiumSystem,
)
from football_republic.policy_registration import StrictRegistrationSystem


def started_campaign() -> DeepCampaign:
    campaign = DeepCampaign(strategy=Strategy.BALANCED)
    campaign.enact_plan(STRATEGIES[Strategy.BALANCED])
    return campaign


def advance_to_transfer_policy(campaign: DeepCampaign) -> None:
    campaign.advance(24, interactive=True)
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "agenda_governance_compact"
    campaign.resolve_decision("federal_compact")
    campaign.advance(24, interactive=True)
    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "youth_safety_crisis"
    campaign.resolve_decision("transparent_reform")
    campaign.advance(24, interactive=True)


def test_strict_registration_enforces_foreign_and_squad_limits() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    registration = StrictRegistrationSystem()
    registration.configure("homegrown_priority")

    registration.register(1, state.clubs, world.rosters)

    assert registration.audit_history
    for audit in registration.audit_history:
        assert audit.registered_players <= 25
        assert audit.registered_players >= 18
        assert audit.registered_foreign <= 4
        assert len(registration.registered_ids[audit.club_id]) == audit.registered_players


def test_presidential_transfer_choice_changes_registration_law() -> None:
    campaign = started_campaign()
    advance_to_transfer_policy(campaign)

    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "transfer_policy"
    campaign.resolve_decision("open_market")

    rules = campaign.football.economy.registration
    assert rules.policy_name == "open market"
    assert rules.squad_limit == 27
    assert rules.foreign_limit == 7
    assert rules.homegrown_minimum == 6


def test_post_market_registration_includes_new_loan_player() -> None:
    campaign = started_campaign()
    advance_to_transfer_policy(campaign)
    campaign.resolve_decision("financial_control")

    campaign.advance(1, interactive=True)

    assert campaign.engine.state.month == 7
    assert campaign.football.contracts.active_loans
    loan = next(iter(campaign.football.contracts.active_loans.values()))
    registered = campaign.football.economy.registration.registered_ids[
        loan.borrower_id
    ]
    assert loan.player.id in registered


def test_sponsorship_becomes_revenue_and_morality_clause_can_suspend_it() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    stadiums = StadiumSystem(state.clubs)
    sponsors = SponsorshipSystem()
    club_id = "harbor"
    revenue_before = state.clubs[club_id].monthly_revenue

    sponsors.renew_season(
        1,
        state.clubs,
        world.rosters,
        set(world.pyramid.premier_ids),
        stadiums.profiles,
    )

    contract = sponsors.contracts[club_id]
    assert contract.status == "active"
    assert contract.annual_value > 0
    assert state.clubs[club_id].monthly_revenue > revenue_before

    state.clubs[club_id].integrity = 0.0
    sponsors.monitor_morality(2, state.clubs)

    assert contract.status == "suspended"
    assert any(
        event.club_id == club_id and event.action == "morality clause triggered"
        for event in sponsors.history
    )


def test_stadium_capacity_caps_attendance_and_reprices_gate_income() -> None:
    state = build_deep_2026_scenario()
    stadiums = StadiumSystem(state.clubs)
    club = state.clubs["harbor"]
    profile = stadiums.profiles[club.id]
    cash_before = club.cash
    result = MatchResult(
        competition="Stadium Test",
        season=1,
        round_number=1,
        month=1,
        home_id=club.id,
        away_id="phoenix",
        home_name=club.name,
        away_name=state.clubs["phoenix"].name,
        home_goals=2,
        away_goals=1,
        home_xg=1.8,
        away_xg=0.9,
        possession_home=55.0,
        attendance=profile.capacity * 2,
        gate_receipts=100_000.0,
    )

    stadiums.settle_matches(1, [result], state.clubs)

    record = stadiums.match_history[-1]
    assert record.attendance == profile.capacity
    assert record.utilization == 1.0
    assert record.gross_revenue > result.gate_receipts
    assert club.cash > cash_before


def test_old_player_retires_and_academy_replaces_the_generation() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    lifecycle = AcademyLifecycleSystem(seed=6100)
    club_id = "harbor"
    roster = world.rosters[club_id]
    veteran = max(roster.players, key=lambda player: player.age)
    veteran.age = 39
    size_before = len(roster.players)

    lifecycle.settle_season(
        12,
        state,
        world.rosters,
        [],
    )

    assert veteran not in roster.players
    assert any(record.player_id == veteran.id for record in lifecycle.retirement_history)
    graduates = [
        record for record in lifecycle.intake_history if record.club_id == club_id
    ]
    assert graduates
    assert all(record.age in (17, 18) for record in graduates)
    assert all(record.potential >= record.ability for record in graduates)
    assert len(roster.players) >= size_before


def test_failed_company_is_replaced_by_a_phoenix_club() -> None:
    state = build_deep_2026_scenario()
    world = AdvancedClubWorld.build(state, seed=3033)
    insolvency = InsolvencySystem()
    club = state.clubs["miners"]
    old_name = club.name
    club.license_status = "excluded"
    club.debt = 30_000_000.0
    club.cash = 0.0
    club.wage_arrears_months = 6

    insolvency.monitor(10, world)
    insolvency.monitor(11, world)
    insolvency.monitor(12, world)

    assert club.name != old_name
    assert club.name.endswith("Community FC")
    assert club.license_status == "conditional"
    assert club.debt < 30_000_000.0
    assert club.wage_arrears_months == 0
    assert insolvency.history[-1].points_deduction == 9
    assert world.pyramid.owners[club.id].name.endswith("Supporters Trust")


def test_full_term_runs_sponsors_stadiums_registration_and_academies() -> None:
    campaign = started_campaign()

    campaign.run(24)

    economy = campaign.football.economy
    assert len(economy.sponsors.contracts) == 14
    assert len(
        [event for event in economy.sponsors.history if event.action == "contract signed"]
    ) == 28
    assert economy.stadiums.match_history
    assert len(economy.registration.audit_history) >= 70
    assert len(economy.lifecycle.intake_history) >= 56
    assert set(campaign.football.monthly_industry_events) == set(range(1, 25))


def test_player_ids_remain_unique_after_two_academy_intakes() -> None:
    campaign = started_campaign()
    campaign.run(24)

    player_ids = [
        player.id
        for roster in campaign.football.rosters.values()
        for player in roster.players
    ] + [player.id for player in campaign.football.contracts.free_agents]

    assert len(player_ids) == len(set(player_ids))
    assert all(len(roster.players) >= 18 for roster in campaign.football.rosters.values())
