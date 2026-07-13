from football_republic.campaign import Strategy
from football_republic.long_term import LongTermCampaign


def all_player_ids(campaign: LongTermCampaign) -> list[str]:
    football = campaign.current_campaign.football
    return [
        player.id
        for roster in football.rosters.values()
        for player in roster.players
    ] + [player.id for player in football.contracts.free_agents]


def test_two_terms_create_four_continuous_seasons() -> None:
    campaign = LongTermCampaign(max_terms=2)

    campaign.run_terms(2)

    assert campaign.finished
    assert campaign.global_month == 48
    assert len(campaign.term_records) == 2
    assert [item.global_season for item in campaign.season_history] == [1, 2, 3, 4]
    assert len(campaign.club_history) == 28


def test_club_divisions_players_owners_and_stadiums_survive_rollover() -> None:
    campaign = LongTermCampaign(max_terms=2)
    campaign.advance(23)
    football = campaign.current_campaign.football
    owner = football.pyramid.owners["harbor"]
    stadium = football.economy.stadiums.profiles["harbor"]
    owner.promises_broken = 7
    stadium.capacity = 55_555
    club_ids = set(campaign.current_campaign.engine.state.clubs)

    campaign.advance(1)

    assert campaign.term_index == 2
    assert set(campaign.current_campaign.engine.state.clubs) == club_ids
    assert campaign.current_campaign.football.pyramid.owners["harbor"].promises_broken == 7
    assert campaign.current_campaign.football.economy.stadiums.profiles["harbor"].capacity == 55_555
    assert len(campaign.current_campaign.football.pyramid.premier_ids) == 6
    assert len(campaign.current_campaign.football.pyramid.second_ids) == 8


def test_academy_player_ids_remain_unique_across_six_seasons() -> None:
    campaign = LongTermCampaign(max_terms=3)

    campaign.run_terms(3)

    ids = all_player_ids(campaign)
    academy_ids = [item.player_id for item in campaign.player_history if item.event == "academy graduation"]
    assert len(ids) == len(set(ids))
    assert len(academy_ids) == len(set(academy_ids))
    assert any("-s5-" in player_id or "-s6-" in player_id for player_id in academy_ids)


def test_low_coalition_support_triggers_a_successor() -> None:
    campaign = LongTermCampaign(max_terms=2)
    first_id = campaign.current_president.id
    campaign.advance(23)
    for actor in campaign.current_campaign.politics.stakeholders.values():
        actor.support = 0.0
        actor.trust = 0.0
        actor.patience = 0.10
        actor.mobilization = 1.0

    campaign.advance(1)

    assert campaign.term_index == 2
    assert campaign.current_president.id != first_id
    assert "succession" in campaign.term_records[0].succession_reason


def test_three_term_limit_forces_rotation_even_with_total_support() -> None:
    campaign = LongTermCampaign(max_terms=4)
    first_id = campaign.current_president.id
    for _ in range(3):
        campaign.advance(23)
        for actor in campaign.current_campaign.politics.stakeholders.values():
            actor.support = 1.0
            actor.trust = 1.0
            actor.patience = 1.0
            actor.mobilization = 0.0
        campaign.current_campaign.engine.state.fan_trust = 0.90
        campaign.current_campaign.engine.state.integrity_reputation = 0.90
        campaign.advance(1)

    assert campaign.term_index == 4
    assert campaign.current_president.id != first_id
    assert campaign.term_records[2].succession_reason == "constitutional consecutive-term limit"


def test_mid_term_json_save_replays_to_identical_fingerprint() -> None:
    campaign = LongTermCampaign(strategy=Strategy.FOUNDATIONS, max_terms=3)
    campaign.advance(9)

    restored = LongTermCampaign.from_json(campaign.to_json())

    assert restored.global_month == campaign.global_month
    assert restored.term_index == campaign.term_index
    assert restored.fingerprint() == campaign.fingerprint()


def test_post_rollover_json_save_replays_completed_terms() -> None:
    campaign = LongTermCampaign(strategy=Strategy.BALANCED, max_terms=3)
    campaign.run_terms(2)
    campaign.advance(5)

    restored = LongTermCampaign.from_json(campaign.to_json())

    assert restored.term_index == 3
    assert len(restored.term_records) == 2
    assert restored.global_month == campaign.global_month
    assert restored.fingerprint() == campaign.fingerprint()


def test_ten_year_history_finishes_five_terms() -> None:
    campaign = LongTermCampaign(max_terms=5)

    campaign.run_years(10)

    assert campaign.finished
    assert campaign.global_month == 120
    assert len(campaign.term_records) == 5
    assert len(campaign.season_history) == 10
    assert {record.global_season for record in campaign.season_history} == set(range(1, 11))
