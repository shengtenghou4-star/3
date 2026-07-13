"""Fictional 2026 starting scenario for the first playable campaign."""

from __future__ import annotations

from .domain import Club, NationalFootballSystem, Region


def build_2026_scenario() -> NationalFootballSystem:
    regions = {
        "coast": Region(
            id="coast", name="Haicheng", population=48_000_000, youth_population=6_800_000,
            registered_youth_players=112_000, licensed_youth_coaches=3_900, average_coach_quality=0.66,
            full_size_pitches=620, small_sided_pitches=2_400, annual_matches_per_player=21.0,
            club_academies=34, school_programs=940, execution_capacity=0.88, integrity=0.74,
            parent_support=0.67,
        ),
        "heartland": Region(
            id="heartland", name="Zhongyuan", population=72_000_000, youth_population=10_500_000,
            registered_youth_players=93_000, licensed_youth_coaches=2_250, average_coach_quality=0.51,
            full_size_pitches=410, small_sided_pitches=1_650, annual_matches_per_player=14.0,
            club_academies=21, school_programs=1_120, execution_capacity=0.63, integrity=0.56,
            parent_support=0.54,
        ),
        "frontier": Region(
            id="frontier", name="Beiling", population=19_000_000, youth_population=2_900_000,
            registered_youth_players=37_000, licensed_youth_coaches=820, average_coach_quality=0.47,
            full_size_pitches=190, small_sided_pitches=530, annual_matches_per_player=11.0,
            club_academies=10, school_programs=360, execution_capacity=0.49, integrity=0.42,
            parent_support=0.58,
        ),
    }
    clubs = {
        "harbor": Club("harbor", "Haicheng Harbor", "coast", 5_000_000, 2_000_000, 2_200_000, 2_050_000, 0.76, 0.78, 0.71, 0.70, 0.85, 0.19),
        "phoenix": Club("phoenix", "South Coast Phoenix", "coast", 1_200_000, 8_000_000, 1_500_000, 1_850_000, 0.61, 0.55, 0.43, 0.44, 0.68, 0.12),
        "forge": Club("forge", "Zhongyuan Forge", "heartland", 2_200_000, 3_500_000, 1_300_000, 1_270_000, 0.57, 0.63, 0.66, 0.61, 0.62, 0.23),
        "tigers": Club("tigers", "Capital Tigers", "heartland", 800_000, 10_500_000, 1_650_000, 2_100_000, 0.48, 0.46, 0.38, 0.32, 0.79, 0.08),
        "northern": Club("northern", "Beiling Northern", "frontier", 1_800_000, 1_100_000, 900_000, 880_000, 0.52, 0.68, 0.70, 0.73, 0.51, 0.28),
        "miners": Club("miners", "Frontier Miners", "frontier", 350_000, 4_800_000, 620_000, 910_000, 0.39, 0.41, 0.33, 0.27, 0.44, 0.07),
    }
    state = NationalFootballSystem(
        month=0,
        treasury=60_000_000,
        political_capital=0.64,
        fan_trust=0.39,
        integrity_reputation=0.43,
        league_financial_health=0.50,
        national_team_strength=47.5,
        regions=regions,
        clubs=clubs,
    )
    state.refresh_league_health()
    return state
