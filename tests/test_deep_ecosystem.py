from collections import Counter

import pytest

from football_republic.campaign import STRATEGIES, Strategy
from football_republic.deep_campaign import DeepCampaign
from football_republic.deep_scenario import (
    PREMIER_CLUB_IDS,
    SECOND_DIVISION_CLUB_IDS,
    build_deep_2026_scenario,
)
from football_republic.ecosystem import ClubPyramidWorld


def started_campaign() -> DeepCampaign:
    campaign = DeepCampaign(strategy=Strategy.BALANCED)
    campaign.enact_plan(STRATEGIES[Strategy.BALANCED])
    return campaign


def test_deep_scenario_has_two_distinct_professional_levels() -> None:
    state = build_deep_2026_scenario()

    assert len(state.clubs) == 14
    assert len(PREMIER_CLUB_IDS) == 6
    assert len(SECOND_DIVISION_CLUB_IDS) == 8
    assert set(PREMIER_CLUB_IDS).isdisjoint(SECOND_DIVISION_CLUB_IDS)
    assert set(PREMIER_CLUB_IDS) | set(SECOND_DIVISION_CLUB_IDS) == set(state.clubs)


def test_media_rights_distribution_conserves_both_pools() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    cash_before = sum(club.cash for club in state.clubs.values())

    world.advance_month(1)

    distributions = world.pyramid.media_history
    assert len(distributions) == 14
    assert sum(item.total for item in distributions if item.division == 1) == pytest.approx(18_000_000)
    assert sum(item.total for item in distributions if item.division == 2) == pytest.approx(5_000_000)
    assert sum(club.cash for club in state.clubs.values()) - cash_before == pytest.approx(23_000_000)


def test_first_season_completes_both_divisions_and_preserves_club_count() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)

    for month in range(1, 13):
        world.advance_month(month)

    assert len([r for r in world.pyramid.all_results if r.competition == "National Premier League"]) == 30
    assert len([r for r in world.pyramid.all_results if r.competition == "National Championship"]) == 56
    assert world.pyramid.movement_history
    assert len(world.pyramid.premier_ids) == 6
    assert len(world.pyramid.second_ids) == 8
    assert set(world.pyramid.premier_ids).isdisjoint(world.pyramid.second_ids)
    assert set(world.pyramid.premier_ids) | set(world.pyramid.second_ids) == set(state.clubs)


def test_national_squad_is_selected_from_shared_player_database() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    squad = world.current_squad

    assert len(squad.members) == 26
    assert Counter(member.position for member in squad.members) == {
        "GK": 3,
        "DEF": 8,
        "MID": 8,
        "ATT": 7,
    }
    all_player_ids = {
        player.id
        for roster in world.rosters.values()
        for player in roster.players
    }
    assert {member.player_id for member in squad.members} <= all_player_ids
    assert 40.0 <= squad.strength <= 92.0
    assert 0.0 <= squad.premier_share <= 1.0


def test_administration_creates_a_real_points_deduction_and_owner_response() -> None:
    state = build_deep_2026_scenario()
    world = ClubPyramidWorld.build(state, seed=3033)
    club = state.clubs["miners"]
    club.wage_arrears_months = 3
    club.debt = club.monthly_revenue * 24

    world.advance_month(1)

    records = [item for item in world.pyramid.administration_history if item.club_id == "miners"]
    assert any(item.action == "entered administration" for item in records)
    assert world.pyramid.premier.points_deductions["miners"] == 6
    assert world.pyramid.premier.table["miners"].points == -6
    assert any(item.owner_injection > 0 for item in records) or club.license_status == "excluded"


def test_bailout_choice_is_remembered_by_the_club_owner() -> None:
    campaign = started_campaign()
    campaign.advance(24, interactive=True)
    campaign.resolve_decision("transparent_reform")
    campaign.advance(24, interactive=True)
    campaign.resolve_decision("financial_control")
    campaign.advance(24, interactive=True)

    assert campaign.current_decision is not None
    assert campaign.current_decision.id == "club_bailout"
    target = min(
        campaign.engine.state.clubs.values(),
        key=lambda club: club.financial_health,
    ).id
    owner = campaign.football.pyramid.owners[target]
    before_relationship = owner.relationship_with_fa

    campaign.resolve_decision("conditional_rescue")

    assert owner.bailout_memory == 1
    assert owner.relationship_with_fa > before_relationship


def test_full_deep_term_runs_two_seasons_and_ten_international_rounds() -> None:
    campaign = started_campaign()
    review = campaign.run(24)

    premier_matches = [
        result
        for result in campaign.football.pyramid.all_results
        if result.competition == "National Premier League"
    ]
    second_matches = [
        result
        for result in campaign.football.pyramid.all_results
        if result.competition == "National Championship"
    ]
    assert len(premier_matches) == 60
    assert len(second_matches) == 112
    assert len(campaign.football.international.results) == 30
    assert len(campaign.football.squad_history) == 11
    assert len(campaign.football.pyramid.media_history) == 28
    assert len(campaign.decision_history) == 6
    assert 1 <= review.qualifier_position <= 6
