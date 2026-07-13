"""Core state for Football Republic."""

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
        if self.registered_youth_players == 0:
            return 1.0
        return min(1.0, (20 * self.licensed_youth_coaches) / self.registered_youth_players)

    @property
    def pitch_access(self) -> float:
        if self.registered_youth_players == 0:
            return 1.0
        weekly_player_slots = self.full_size_pitches * 240 + self.small_sided_pitches * 80
        return min(1.0, weekly_player_slots / self.registered_youth_players)

    @property
    def match_environment(self) -> float:
        return min(1.0, self.annual_matches_per_player / 30.0)

    @property
    def development_environment(self) -> float:
        score = (
            0.30 * self.coach_coverage
            + 0.25 * self.average_coach_quality
            + 0.20 * self.match_environment
            + 0.15 * self.pitch_access
            + 0.10 * self.parent_support
        )
        return 100.0 * score


@dataclass(slots=True)
class Club:
    """A professional club with finances, academy capacity and rule incentives."""

    id: str
    name: str
    region_id: str
    cash: float
    debt: float
    monthly_revenue: float
    monthly_wage_bill: float
    academy_quality: float
    licensing_compliance: float
    integrity: float
    owner_patience: float
    supporter_base: float
    youth_minutes_share: float
    wage_arrears_months: int = 0
    license_status: str = "licensed"
    response_to_reform: str = "pending"

    def __post_init__(self) -> None:
        for name in ("cash", "debt", "monthly_revenue", "monthly_wage_bill"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        for name in (
            "academy_quality",
            "licensing_compliance",
            "integrity",
            "owner_patience",
            "supporter_base",
            "youth_minutes_share",
        ):
            _unit_interval(name, getattr(self, name))

    @property
    def monthly_operating_result(self) -> float:
        return self.monthly_revenue - self.monthly_wage_bill

    @property
    def financial_health(self) -> float:
        debt_pressure = self.debt / max(self.monthly_revenue * 12.0, 1.0)
        liquidity = self.cash / max(self.monthly_wage_bill * 3.0, 1.0)
        arrears_penalty = min(1.0, self.wage_arrears_months / 4.0)
        return max(0.0, min(1.0, 0.45 * liquidity + 0.45 * (1.0 - debt_pressure) + 0.10 * (1.0 - arrears_penalty)))

    def close_month(self) -> None:
        result = self.monthly_operating_result
        if result >= 0:
            self.cash += result
            if self.wage_arrears_months > 0 and self.cash >= self.monthly_wage_bill:
                self.wage_arrears_months -= 1
        else:
            loss = -result
            if self.cash >= loss:
                self.cash -= loss
            else:
                shortfall = loss - self.cash
                self.cash = 0.0
                self.debt += shortfall
                self.wage_arrears_months += 1


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
    clubs: dict[str, Club] = field(default_factory=dict)

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

    @property
    def solvent_club_share(self) -> float:
        if not self.clubs:
            return 1.0
        solvent = sum(
            club.license_status != "excluded" and club.wage_arrears_months < 3
            for club in self.clubs.values()
        )
        return solvent / len(self.clubs)

    def refresh_league_health(self) -> None:
        if not self.clubs:
            self.league_financial_health = 1.0
            return
        health = sum(club.financial_health for club in self.clubs.values()) / len(self.clubs)
        self.league_financial_health = max(0.0, min(1.0, health))
