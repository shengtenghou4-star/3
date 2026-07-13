"""Core state for the national football system.

The first vertical slice intentionally models one causal chain in detail:
public money -> regional implementation -> trained coaches -> better youth
training conditions. More systems will plug into the same state later.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


@dataclass(slots=True)
class Region:
    """A province/state-level football ecosystem."""

    id: str
    name: str
    population: int
    youth_population: int
    registered_youth_players: int
    licensed_youth_coaches: int
    average_coach_quality: float
    full_size_pitches: int
    small_sided_pitches: int
    annual_matches_per_player: float
    club_academies: int
    school_programs: int
    execution_capacity: float
    integrity: float
    parent_support: float

    def __post_init__(self) -> None:
        for name in (
            "population",
            "youth_population",
            "registered_youth_players",
            "licensed_youth_coaches",
            "full_size_pitches",
            "small_sided_pitches",
            "club_academies",
            "school_programs",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.registered_youth_players > self.youth_population:
            raise ValueError("registered_youth_players cannot exceed youth_population")
        for name in (
            "average_coach_quality",
            "execution_capacity",
            "integrity",
            "parent_support",
        ):
            _unit_interval(name, getattr(self, name))
        if self.annual_matches_per_player < 0:
            raise ValueError("annual_matches_per_player cannot be negative")

    @property
    def youth_access_rate(self) -> float:
        if self.youth_population == 0:
            return 0.0
        return self.registered_youth_players / self.youth_population

    @property
    def players_per_coach(self) -> float:
        if self.licensed_youth_coaches == 0:
            return float("inf")
        return self.registered_youth_players / self.licensed_youth_coaches

    @property
    def coach_coverage(self) -> float:
        """Coverage reaches 1.0 at 20 registered players per licensed coach."""

        if self.registered_youth_players == 0:
            return 1.0
        return min(1.0, (20 * self.licensed_youth_coaches) / self.registered_youth_players)

    @property
    def pitch_access(self) -> float:
        """Approximate weekly access using different capacities by pitch type."""

        if self.registered_youth_players == 0:
            return 1.0
        weekly_player_slots = self.full_size_pitches * 240 + self.small_sided_pitches * 80
        return min(1.0, weekly_player_slots / self.registered_youth_players)

    @property
    def match_environment(self) -> float:
        """Thirty meaningful matches per year counts as a complete pathway."""

        return min(1.0, self.annual_matches_per_player / 30.0)

    @property
    def development_environment(self) -> float:
        """A decomposable 0-100 score for the youth development environment."""

        score = (
            0.30 * self.coach_coverage
            + 0.25 * self.average_coach_quality
            + 0.20 * self.match_environment
            + 0.15 * self.pitch_access
            + 0.10 * self.parent_support
        )
        return 100.0 * score


@dataclass(slots=True)
class NationalFootballSystem:
    """Top-level state controlled or influenced by the association president."""

    month: int
    treasury: float
    political_capital: float
    fan_trust: float
    integrity_reputation: float
    league_financial_health: float
    national_team_strength: float
    regions: dict[str, Region] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.month < 0:
            raise ValueError("month cannot be negative")
        if self.treasury < 0:
            raise ValueError("treasury cannot be negative")
        for name in (
            "political_capital",
            "fan_trust",
            "integrity_reputation",
            "league_financial_health",
        ):
            _unit_interval(name, getattr(self, name))
        if not 0.0 <= self.national_team_strength <= 100.0:
            raise ValueError("national_team_strength must be between 0 and 100")

    @property
    def registered_youth_players(self) -> int:
        return sum(region.registered_youth_players for region in self.regions.values())

    @property
    def licensed_youth_coaches(self) -> int:
        return sum(region.licensed_youth_coaches for region in self.regions.values())

    @property
    def youth_development_environment(self) -> float:
        total_players = self.registered_youth_players
        if total_players == 0:
            return 0.0
        return sum(
            region.development_environment * region.registered_youth_players
            for region in self.regions.values()
        ) / total_players
