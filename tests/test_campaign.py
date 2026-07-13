import pytest

from football_republic import Campaign, PresidentialPlan, Strategy, build_2026_scenario, run_strategy


def test_scenario_contains_three_regions_and_six_clubs() -> None:
    state = build_2026_scenario()
    assert len(state.regions) == 3
    assert len(state.clubs) == 6
    assert {club.region_id for club in state.clubs.values()} == set(state.regions)


def test_school_agreement_is_delayed_and_requires_political_leverage() -> None:
    campaign = Campaign()
    before = sum(region.school_programs for region in campaign.engine.state.regions.values())
    assert campaign.engine.negotiate_school_football_agreement(5_000_000)
    campaign.engine.advance_months(5)
    assert sum(region.school_programs for region in campaign.engine.state.regions.values()) == before
    campaign.engine.advance_months(1)
    assert sum(region.school_programs for region in campaign.engine.state.regions.values()) > before


def test_strict_licensing_produces_multiple_club_responses() -> None:
    campaign = Campaign()
    outcomes = campaign.engine.impose_club_licensing_reform(0.75, 3_000_000)
    assert len(outcomes) == 6
    assert len(set(outcomes.values())) >= 2


def test_presidential_plan_cannot_exceed_treasury() -> None:
    campaign = Campaign()
    plan = PresidentialPlan(30_000_000, 30_000_000, 10_000_000, 0.5, 2_000_000, 10_000_000)
    with pytest.raises(ValueError):
        campaign.enact_plan(plan)


def test_three_strategies_create_distinct_outcomes() -> None:
    results = {}
    for strategy in Strategy:
        campaign, review = run_strategy(strategy)
        results[strategy] = (
            round(review.score, 4),
            round(review.youth_change, 4),
            round(review.national_team_strength, 4),
            campaign.engine.state.registered_youth_players,
        )
    assert len(set(results.values())) == 3
    assert results[Strategy.FOUNDATIONS][1] > results[Strategy.QUICK_RESULTS][1]
    assert results[Strategy.QUICK_RESULTS][2] > results[Strategy.FOUNDATIONS][2]


def test_campaign_emits_six_month_dashboards_and_board_review() -> None:
    campaign, review = run_strategy(Strategy.BALANCED)
    assert [dashboard.month for dashboard in campaign.dashboards] == [0, 6, 12, 18, 24]
    assert 0 <= review.score <= 100
    assert review.verdict
    assert campaign.engine.audit_log
