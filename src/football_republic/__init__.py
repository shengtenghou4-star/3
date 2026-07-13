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
from .governance import (
    AnnualFinanceReport,
    DecisionOption,
    DecisionRecord,
    GovernanceDecision,
)
from .market import TransferMarket, TransferPolicy, TransferRecord
from .programs import CoachEducationGrant, YouthMatchGrant
from .scenario import build_2026_scenario

__all__ = [
    "AnnualFinanceReport",
    "Campaign",
    "Club",
    "ClubRoster",
    "CoachEducationGrant",
    "DecisionOption",
    "DecisionRecord",
    "DomesticLeague",
    "FootballWorld",
    "GovernanceDecision",
    "InternationalQualifiers",
    "MatchResult",
    "NationalFootballSystem",
    "Player",
    "PresidentialPlan",
    "Region",
    "SimulationEngine",
    "Standing",
    "Strategy",
    "TransferMarket",
    "TransferPolicy",
    "TransferRecord",
    "YouthMatchGrant",
    "build_2026_scenario",
    "run_strategy",
]
