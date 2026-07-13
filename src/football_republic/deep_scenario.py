"""Expanded 2026 scenario with a two-level professional club pyramid."""

from __future__ import annotations

from .domain import Club, NationalFootballSystem
from .scenario import build_2026_scenario


PREMIER_CLUB_IDS = (
    "harbor",
    "phoenix",
    "forge",
    "tigers",
    "northern",
    "miners",
)

SECOND_DIVISION_CLUB_IDS = (
    "dockers",
    "bluewings",
    "railway",
    "scholars",
    "wolves",
    "riverplate",
    "rangers",
    "pioneers",
)


def _club(
    club_id: str,
    name: str,
    region_id: str,
    *,
    cash: float,
    debt: float,
    revenue: float,
    wages: float,
    academy: float,
    compliance: float,
    integrity: float,
    patience: float,
    supporters: float,
    youth_minutes: float,
) -> Club:
    return Club(
        id=club_id,
        name=name,
        region_id=region_id,
        cash=cash,
        debt=debt,
        monthly_revenue=revenue,
        monthly_wage_bill=wages,
        academy_quality=academy,
        licensing_compliance=compliance,
        integrity=integrity,
        owner_patience=patience,
        supporter_base=supporters,
        youth_minutes_share=youth_minutes,
    )


def build_deep_2026_scenario() -> NationalFootballSystem:
    state = build_2026_scenario()
    state.clubs.update(
        {
            "dockers": _club(
                "dockers", "Haicheng Dockers", "coast",
                cash=2_400_000, debt=1_300_000, revenue=820_000, wages=760_000,
                academy=0.59, compliance=0.72, integrity=0.63, patience=0.66,
                supporters=0.48, youth_minutes=0.31,
            ),
            "bluewings": _club(
                "bluewings", "East Bay Bluewings", "coast",
                cash=900_000, debt=3_600_000, revenue=690_000, wages=770_000,
                academy=0.67, compliance=0.58, integrity=0.52, patience=0.43,
                supporters=0.41, youth_minutes=0.38,
            ),
            "railway": _club(
                "railway", "Zhongyuan Railway", "heartland",
                cash=1_700_000, debt=1_800_000, revenue=720_000, wages=690_000,
                academy=0.54, compliance=0.69, integrity=0.61, patience=0.71,
                supporters=0.46, youth_minutes=0.34,
            ),
            "scholars": _club(
                "scholars", "Central Scholars", "heartland",
                cash=1_100_000, debt=900_000, revenue=610_000, wages=570_000,
                academy=0.74, compliance=0.81, integrity=0.78, patience=0.76,
                supporters=0.32, youth_minutes=0.48,
            ),
            "wolves": _club(
                "wolves", "Western Wolves", "heartland",
                cash=420_000, debt=4_200_000, revenue=590_000, wages=760_000,
                academy=0.42, compliance=0.39, integrity=0.35, patience=0.29,
                supporters=0.52, youth_minutes=0.17,
            ),
            "riverplate": _club(
                "riverplate", "Long River Athletic", "heartland",
                cash=1_450_000, debt=2_100_000, revenue=680_000, wages=650_000,
                academy=0.61, compliance=0.64, integrity=0.57, patience=0.62,
                supporters=0.39, youth_minutes=0.36,
            ),
            "rangers": _club(
                "rangers", "Beiling Rangers", "frontier",
                cash=1_050_000, debt=650_000, revenue=510_000, wages=470_000,
                academy=0.56, compliance=0.76, integrity=0.73, patience=0.79,
                supporters=0.35, youth_minutes=0.43,
            ),
            "pioneers": _club(
                "pioneers", "Frontier Pioneers", "frontier",
                cash=330_000, debt=2_700_000, revenue=420_000, wages=560_000,
                academy=0.47, compliance=0.48, integrity=0.44, patience=0.34,
                supporters=0.37, youth_minutes=0.29,
            ),
        }
    )
    state.refresh_league_health()
    return state
