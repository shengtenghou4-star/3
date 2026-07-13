"""Football Republic public package API."""

from .campaign import Campaign, PresidentialPlan, Strategy, run_strategy
from .domain import Club, NationalFootballSystem, Region
from .engine import SimulationEngine
from .football import (
    ClubRoster,
    DomesticLeague,
    FootballWorld,
    InternationalQualifiers,
    MatchResult,
    Player,
    Standing,
)
from .programs import CoachEducationGrant, YouthMatchGrant
from .scenario import build_2026_scenario

__all__ = [
    "Campaign",
    "Club",
    "ClubRoster",
    "CoachEducationGrant",
    "DomesticLeague",
    "FootballWorld",
    "InternationalQualifiers",
    "MatchResult",
    "NationalFootballSystem",
    "Player",
    "PresidentialPlan",
    "Region",
    "SimulationEngine",
    "Standing",
    "Strategy",
    "YouthMatchGrant",
    "build_2026_scenario",
    "run_strategy",
]
