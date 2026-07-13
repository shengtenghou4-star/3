"""Football Republic public package API."""

from .campaign import Campaign, PresidentialPlan, Strategy, run_strategy
from .domain import Club, NationalFootballSystem, Region
from .engine import SimulationEngine
from .programs import CoachEducationGrant, YouthMatchGrant
from .scenario import build_2026_scenario

__all__ = [
    "Campaign",
    "Club",
    "CoachEducationGrant",
    "NationalFootballSystem",
    "PresidentialPlan",
    "Region",
    "SimulationEngine",
    "Strategy",
    "YouthMatchGrant",
    "build_2026_scenario",
    "run_strategy",
]
