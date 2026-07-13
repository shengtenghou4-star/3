from football_republic import Strategy, build_2026_scenario, run_strategy
from football_republic.football import FootballWorld, generate_roster


def test_rosters_are_deterministic_and_position_complete() -> None:
    state = build_2026_scenario()
    first = generate_roster(state.clubs["harbor"], seed=2033)
    second = generate_roster(state.clubs["harbor"], seed=2033)

    assert len(first.players) == 25
    assert {position: sum(p.position == position for p in first.players) for position in ("GK", "DEF", "MID", "ATT")} == {
        "GK": 3,
        "DEF": 8,
        "MID": 8,
        "ATT": 6,
    }
    assert [
        (player.name, player.age, round(player.ability, 6))
        for player in first.players
    ] == [
        (player.name, player.age, round(player.ability, 6))
        for player in second.players
    ]


def test_domestic_season_is_double_round_robin() -> None:
    state = build_2026_scenario()
    world = FootballWorld.build(state, seed=2033)

    for month in range(1, 12):
        world.advance_month(month)

    assert len(world.domestic_league.results) == 30
    assert all(row.played == 10 for row in world.domestic_league.sorted_table())
    assert sum(row.points for row in world.domestic_league.sorted_table()) <= 90
    assert sum(result.gate_receipts for result in world.domestic_league.results) > 0


def test_world_cup_qualifying_group_plays_all_thirty_matches() -> None:
    state = build_2026_scenario()
    world = FootballWorld.build(state, seed=2033)

    for month in range(1, 24):
        world.advance_month(month)

    assert len(world.international.results) == 30
    assert all(row.played == 10 for row in world.international.sorted_table())
    assert 1 <= world.international.user_position <= 6


def test_excluded_club_forfeits_its_fixture() -> None:
    state = build_2026_scenario()
    state.clubs["harbor"].license_status = "excluded"
    world = FootballWorld.build(state, seed=2033)

    results = world.domestic_league.advance_month(2)
    harbor_match = next(
        result
        for result in results
        if "harbor" in (result.home_id, result.away_id)
    )

    if harbor_match.home_id == "harbor":
        assert (harbor_match.home_goals, harbor_match.away_goals) == (0, 3)
    else:
        assert (harbor_match.home_goals, harbor_match.away_goals) == (3, 0)
    assert harbor_match.attendance == 0


def test_presidential_strategy_changes_qualification_outcome() -> None:
    outcomes = {}
    for strategy in Strategy:
        campaign, review = run_strategy(strategy)
        outcomes[strategy] = (
            review.qualifier_position,
            review.national_team_strength,
            len(campaign.football.domestic_league.results),
            len(campaign.football.international.results),
        )

    assert outcomes[Strategy.QUICK_RESULTS][0] < outcomes[Strategy.FOUNDATIONS][0]
    assert outcomes[Strategy.QUICK_RESULTS][1] > outcomes[Strategy.FOUNDATIONS][1]
    assert outcomes[Strategy.BALANCED][2:] == (60, 30)
