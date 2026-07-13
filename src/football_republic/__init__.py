"""Football Republic public package API."""

from .campaign import Campaign, PresidentialPlan, STRATEGIES, Strategy, run_strategy
from .deep_campaign import DeepCampaign, run_deep_strategy
from .deep_scenario import build_deep_2026_scenario
from .domain import Club, NationalFootballSystem, Region
from .ecosystem import (
    AdministrationRecord,
    ClubPyramid,
    ClubPyramidWorld,
    DivisionLeague,
    MediaDistribution,
    NationalSquad,
    NationalSquadSelector,
    OwnerProfile,
    PromotionMovement,
    SquadMember,
)
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
    "AdministrationRecord",
    "AnnualFinanceReport",
    "Campaign",
    "Club",
    "ClubPyramid",
    "ClubPyramidWorld",
    "ClubRoster",
    "CoachEducationGrant",
    "DecisionOption",
    "DecisionRecord",
    "DeepCampaign",
    "DivisionLeague",
    "DomesticLeague",
    "FootballWorld",
    "GovernanceDecision",
    "InternationalQualifiers",
    "MatchResult",
    "MediaDistribution",
    "NationalFootballSystem",
    "NationalSquad",
    "NationalSquadSelector",
    "OwnerProfile",
    "Player",
    "PresidentialPlan",
    "PromotionMovement",
    "Region",
    "STRATEGIES",
    "SimulationEngine",
    "SquadMember",
    "Standing",
    "Strategy",
    "TransferMarket",
    "TransferPolicy",
    "TransferRecord",
    "YouthMatchGrant",
    "build_2026_scenario",
    "build_deep_2026_scenario",
    "run_deep_strategy",
    "run_strategy",
]
