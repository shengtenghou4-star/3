"""Generational football economy: stadiums, sponsors, registration and renewal."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random

from .advanced_ecosystem import AdvancedClubWorld
from .domain import Club, NationalFootballSystem
from .football import ClubRoster, FIRST_NAMES, LAST_NAMES, MatchResult, Player


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(slots=True)
class StadiumProfile:
    club_id: str
    club_name: str
    stadium_name: str
    capacity: int
    quality: float
    hospitality: float
    ticket_price: float
    monthly_maintenance: float
    expansion_completion_month: int | None = None
    expansion_capacity: int = 0
    cumulative_investment: float = 0.0


@dataclass(frozen=True, slots=True)
class StadiumFinanceRecord:
    month: int
    club_id: str
    club_name: str
    competition: str
    attendance: int
    capacity: int
    utilization: float
    ticket_price: float
    gross_revenue: float
    engine_revenue: float
    cash_adjustment: float


@dataclass(frozen=True, slots=True)
class StadiumInvestmentRecord:
    month: int
    club_id: str
    club_name: str
    action: str
    cost: float
    capacity_change: int
    quality_change: float
    completion_month: int | None


@dataclass(slots=True)
class SponsorshipContract:
    club_id: str
    club_name: str
    sponsor_name: str
    signed_month: int
    annual_value: float
    monthly_component: float
    performance_bonus_rate: float
    morality_threshold: float
    status: str = "active"


@dataclass(frozen=True, slots=True)
class SponsorshipEvent:
    month: int
    club_id: str
    club_name: str
    sponsor_name: str
    action: str
    amount: float
    note: str


@dataclass(frozen=True, slots=True)
class RegistrationAudit:
    month: int
    club_id: str
    club_name: str
    squad_limit: int
    foreign_limit: int
    homegrown_minimum: int
    registered_players: int
    registered_foreign: int
    registered_homegrown: int
    unregistered_players: tuple[str, ...]
    fine: float
    compliant: bool


@dataclass(frozen=True, slots=True)
class AcademyIntakeRecord:
    month: int
    club_id: str
    club_name: str
    player_id: str
    player_name: str
    position: str
    age: int
    ability: float
    potential: float
    development_environment: float


@dataclass(frozen=True, slots=True)
class RetirementRecord:
    month: int
    club_id: str
    club_name: str
    player_id: str
    player_name: str
    age: int
    ability: float
    career_appearances: int
    reason: str


@dataclass(frozen=True, slots=True)
class InsolvencyRecord:
    month: int
    club_id: str
    old_name: str
    new_name: str
    action: str
    debt_before: float
    debt_after: float
    players_released: int
    points_deduction: int
    note: str


class StadiumSystem:
    """Physical grounds constrain attendance and create capital expenditure choices."""

    def __init__(self, clubs: dict[str, Club], seed: int = 4100) -> None:
        self.seed = seed
        self.profiles: dict[str, StadiumProfile] = {}
        self.match_history: list[StadiumFinanceRecord] = []
        self.investment_history: list[StadiumInvestmentRecord] = []
        for club_id, club in clubs.items():
            rng = random.Random(seed + _seed(f"stadium:{club_id}"))
            capacity = int(
                10_000
                + 43_000 * club.supporter_base
                + rng.randint(-2_500, 3_000)
            )
            quality = _clamp(
                0.35
                + 0.35 * club.financial_health
                + 0.20 * club.supporter_base
                + rng.uniform(-0.08, 0.08),
                0.25,
                0.92,
            )
            hospitality = _clamp(
                0.18 + 0.45 * club.supporter_base + rng.uniform(-0.06, 0.06),
                0.08,
                0.78,
            )
            ticket_price = 15.0 + 25.0 * club.supporter_base + 6.0 * quality
            monthly_maintenance = capacity * (1.25 + 1.35 * quality)
            self.profiles[club_id] = StadiumProfile(
                club_id=club_id,
                club_name=club.name,
                stadium_name=f"{club.name.split()[0]} National Stadium",
                capacity=max(8_000, capacity),
                quality=quality,
                hospitality=hospitality,
                ticket_price=ticket_price,
                monthly_maintenance=monthly_maintenance,
            )

    def settle_matches(
        self,
        month: int,
        results: list[MatchResult],
        clubs: dict[str, Club],
    ) -> None:
        for result in results:
            if result.home_id not in self.profiles:
                continue
            profile = self.profiles[result.home_id]
            club = clubs[result.home_id]
            actual_attendance = min(
                profile.capacity,
                int(result.attendance * (0.82 + 0.28 * profile.quality)),
            )
            utilization = actual_attendance / max(profile.capacity, 1)
            gross = actual_attendance * profile.ticket_price * (
                1.0 + 0.24 * profile.hospitality
            )
            adjustment = gross - result.gate_receipts
            if adjustment >= 0:
                club.cash += adjustment
            elif club.cash >= -adjustment:
                club.cash += adjustment
            else:
                club.debt += -adjustment - club.cash
                club.cash = 0.0
            self.match_history.append(
                StadiumFinanceRecord(
                    month=month,
                    club_id=club.id,
                    club_name=club.name,
                    competition=result.competition,
                    attendance=actual_attendance,
                    capacity=profile.capacity,
                    utilization=utilization,
                    ticket_price=profile.ticket_price,
                    gross_revenue=gross,
                    engine_revenue=result.gate_receipts,
                    cash_adjustment=adjustment,
                )
            )

    def settle_month(
        self,
        month: int,
        clubs: dict[str, Club],
        owner_profiles: dict[str, object],
    ) -> None:
        for club_id, profile in self.profiles.items():
            club = clubs[club_id]
            maintenance = profile.monthly_maintenance
            if club.cash >= maintenance:
                club.cash -= maintenance
            else:
                club.debt += maintenance - club.cash
                club.cash = 0.0
                profile.quality = _clamp(profile.quality - 0.006, 0.15, 1.0)

            if (
                profile.expansion_completion_month is not None
                and month >= profile.expansion_completion_month
            ):
                profile.capacity += profile.expansion_capacity
                profile.quality = _clamp(profile.quality + 0.04, 0.0, 1.0)
                self.investment_history.append(
                    StadiumInvestmentRecord(
                        month,
                        club_id,
                        club.name,
                        "expansion completed",
                        0.0,
                        profile.expansion_capacity,
                        0.04,
                        month,
                    )
                )
                profile.expansion_completion_month = None
                profile.expansion_capacity = 0
                profile.monthly_maintenance = profile.capacity * (
                    1.25 + 1.35 * profile.quality
                )

            recent = [
                item
                for item in self.match_history
                if item.club_id == club_id and month - 5 <= item.month <= month
            ]
            if recent:
                utilization = sum(item.utilization for item in recent) / len(recent)
                if utilization > 0.90:
                    profile.ticket_price *= 1.025
                elif utilization < 0.52:
                    profile.ticket_price *= 0.975
            else:
                utilization = 0.0

            owner = owner_profiles[club_id]
            can_invest = (
                month in (6, 18)
                and profile.expansion_completion_month is None
                and utilization > 0.82
                and club.cash > 4_500_000
                and getattr(owner, "ambition", 0.0) > 0.52
            )
            if can_invest:
                expansion = 3_000 + int(5_000 * getattr(owner, "ambition", 0.5))
                cost = 2_200_000 + expansion * 310.0
                if club.cash >= cost:
                    club.cash -= cost
                    profile.cumulative_investment += cost
                    profile.expansion_completion_month = month + 6
                    profile.expansion_capacity = expansion
                    self.investment_history.append(
                        StadiumInvestmentRecord(
                            month,
                            club_id,
                            club.name,
                            "expansion approved",
                            cost,
                            expansion,
                            0.04,
                            month + 6,
                        )
                    )


class SponsorshipSystem:
    """Commercial contracts respond to audience, results and integrity."""

    SPONSORS = (
        "Apex Telecom",
        "Dragon River Bank",
        "Northstar Motors",
        "Unity Insurance",
        "Golden Grain Foods",
        "Orbital Technology",
        "National Rail Logistics",
        "Harbor Energy",
        "Civic Air",
        "BluePeak Sportswear",
        "Grand Canal Commerce",
        "Pioneer Construction",
        "Horizon Media",
        "Eastern Beverage",
    )

    def __init__(self, seed: int = 5100) -> None:
        self.seed = seed
        self.contracts: dict[str, SponsorshipContract] = {}
        self.history: list[SponsorshipEvent] = []

    def renew_season(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
        stadiums: dict[str, StadiumProfile],
    ) -> None:
        season = 1 if month == 1 else 2
        for index, (club_id, club) in enumerate(clubs.items()):
            old = self.contracts.get(club_id)
            if old and old.status == "active":
                club.monthly_revenue = max(
                    0.0,
                    club.monthly_revenue - old.monthly_component,
                )
            division_multiplier = 1.30 if club_id in premier_ids else 0.72
            sporting = rosters[club_id].overall / 70.0
            commercial = 0.55 + 0.85 * club.supporter_base
            integrity = 0.72 + 0.36 * club.integrity
            facility = 0.82 + 0.30 * stadiums[club_id].quality
            annual = (
                1_000_000
                * division_multiplier
                * sporting
                * commercial
                * integrity
                * facility
            )
            rng = random.Random(self.seed + _seed(f"sponsor:{season}:{club_id}"))
            annual *= rng.uniform(0.88, 1.14)
            sponsor = self.SPONSORS[(index + season * 3) % len(self.SPONSORS)]
            contract = SponsorshipContract(
                club_id=club_id,
                club_name=club.name,
                sponsor_name=sponsor,
                signed_month=month,
                annual_value=annual,
                monthly_component=annual / 12.0,
                performance_bonus_rate=0.10 + 0.12 * club.supporter_base,
                morality_threshold=0.34 + rng.uniform(-0.04, 0.08),
            )
            self.contracts[club_id] = contract
            club.monthly_revenue += contract.monthly_component
            self.history.append(
                SponsorshipEvent(
                    month,
                    club_id,
                    club.name,
                    sponsor,
                    "contract signed",
                    annual,
                    "annual value becomes recurring club revenue",
                )
            )

    def monitor_morality(
        self,
        month: int,
        clubs: dict[str, Club],
    ) -> None:
        for club_id, contract in self.contracts.items():
            club = clubs[club_id]
            breach = (
                club.integrity < contract.morality_threshold
                or club.license_status == "excluded"
            )
            if breach and contract.status == "active":
                contract.status = "suspended"
                club.monthly_revenue = max(
                    0.0,
                    club.monthly_revenue - contract.monthly_component,
                )
                clawback = contract.monthly_component * 2.0
                if club.cash >= clawback:
                    club.cash -= clawback
                else:
                    club.debt += clawback - club.cash
                    club.cash = 0.0
                self.history.append(
                    SponsorshipEvent(
                        month,
                        club_id,
                        club.name,
                        contract.sponsor_name,
                        "morality clause triggered",
                        -clawback,
                        "sponsorship revenue suspended after integrity or licensing breach",
                    )
                )

    def pay_performance_bonuses(
        self,
        month: int,
        world: AdvancedClubWorld,
    ) -> None:
        if month not in (12, 24):
            return
        table = world.pyramid.premier.sorted_table()
        rank = {row.team_id: index for index, row in enumerate(table, start=1)}
        cup_champion = world.domestic_cup.champions.get(1 if month == 12 else 2)
        continental_champion = world.continental.champion_id
        for club_id, contract in self.contracts.items():
            if contract.status != "active":
                continue
            bonus_factor = 0.0
            if club_id in rank:
                bonus_factor += max(0.0, (4 - rank[club_id]) / 3.0)
            if club_id == cup_champion:
                bonus_factor += 0.75
            if club_id == continental_champion:
                bonus_factor += 1.25
            bonus = contract.annual_value * contract.performance_bonus_rate * bonus_factor
            if bonus <= 0:
                continue
            world.state.clubs[club_id].cash += bonus
            self.history.append(
                SponsorshipEvent(
                    month,
                    club_id,
                    world.state.clubs[club_id].name,
                    contract.sponsor_name,
                    "performance bonus",
                    bonus,
                    "league, cup and continental achievements activated bonuses",
                )
            )


class RegistrationSystem:
    """Select match-eligible squads and keep contracted reserves off the pitch."""

    def __init__(self) -> None:
        self.squad_limit = 25
        self.foreign_limit = 5
        self.homegrown_minimum = 8
        self.registered_ids: dict[str, set[str]] = {}
        self.audit_history: list[RegistrationAudit] = []
        self.policy_name = "balanced registration"

    def configure(self, option_id: str) -> None:
        if option_id == "homegrown_priority":
            self.squad_limit = 25
            self.foreign_limit = 4
            self.homegrown_minimum = 10
            self.policy_name = "homegrown priority"
        elif option_id == "open_market":
            self.squad_limit = 27
            self.foreign_limit = 7
            self.homegrown_minimum = 6
            self.policy_name = "open market"
        else:
            self.squad_limit = 24
            self.foreign_limit = 5
            self.homegrown_minimum = 8
            self.policy_name = "financial control"

    def register(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id, roster in rosters.items():
            players = list(roster.players)
            selected: list[Player] = []

            def add(player: Player) -> None:
                if player not in selected and len(selected) < self.squad_limit:
                    selected.append(player)

            goalkeepers = sorted(
                (player for player in players if player.position == "GK"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in goalkeepers[:2]:
                add(player)

            homegrown = sorted(
                (player for player in players if player.homegrown),
                key=lambda player: (player.match_readiness, player.potential),
                reverse=True,
            )
            for player in homegrown[: self.homegrown_minimum]:
                add(player)

            under_23 = sorted(
                (player for player in players if player.age <= 23),
                key=lambda player: (player.potential, player.match_readiness),
                reverse=True,
            )
            for player in under_23[:3]:
                add(player)

            foreign = sorted(
                (player for player in players if player.nationality != "Longhua"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in foreign[: self.foreign_limit]:
                add(player)

            domestic = sorted(
                (player for player in players if player.nationality == "Longhua"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in domestic:
                add(player)
            for player in sorted(players, key=lambda player: player.match_readiness, reverse=True):
                if player.nationality == "Longhua" or sum(
                    item.nationality != "Longhua" for item in selected
                ) < self.foreign_limit:
                    add(player)
            if len(selected) < 18:
                for player in sorted(players, key=lambda player: player.match_readiness, reverse=True):
                    add(player)
                    if len(selected) >= 18:
                        break

            selected_ids = {player.id for player in selected}
            self.registered_ids[club_id] = selected_ids
            registered_foreign = sum(
                player.nationality != "Longhua" for player in selected
            )
            registered_homegrown = sum(player.homegrown for player in selected)
            missing_homegrown = max(0, self.homegrown_minimum - registered_homegrown)
            fine = missing_homegrown * 140_000.0
            club = clubs[club_id]
            if fine > 0:
                if club.cash >= fine:
                    club.cash -= fine
                else:
                    club.debt += fine - club.cash
                    club.cash = 0.0
                club.licensing_compliance = _clamp(
                    club.licensing_compliance - 0.015 * missing_homegrown,
                    0.0,
                    1.0,
                )
            unregistered = tuple(
                player.name for player in players if player.id not in selected_ids
            )
            self.audit_history.append(
                RegistrationAudit(
                    month,
                    club_id,
                    club.name,
                    self.squad_limit,
                    self.foreign_limit,
                    self.homegrown_minimum,
                    len(selected),
                    registered_foreign,
                    registered_homegrown,
                    unregistered,
                    fine,
                    missing_homegrown == 0 and registered_foreign <= self.foreign_limit,
                )
            )

    def suspend_unregistered(
        self,
        rosters: dict[str, ClubRoster],
    ) -> dict[str, list[Player]]:
        reserves: dict[str, list[Player]] = {}
        for club_id, roster in rosters.items():
            registered = self.registered_ids.get(
                club_id,
                {player.id for player in roster.players},
            )
            reserve = [player for player in roster.players if player.id not in registered]
            reserves[club_id] = reserve
            if reserve:
                roster.players = [
                    player for player in roster.players if player.id in registered
                ]
        return reserves

    def restore_and_advance_reserves(
        self,
        month: int,
        reserves: dict[str, list[Player]],
        rosters: dict[str, ClubRoster],
        clubs: dict[str, Club],
        free_agents: list[Player],
    ) -> None:
        for club_id, players in reserves.items():
            roster = rosters[club_id]
            rng = random.Random(_seed(f"reserve:{club_id}:{month}"))
            for player in players:
                player.advance_month(rng, clubs[club_id].academy_quality)
                if month % 12 == 0:
                    player.age += 1
                if player.contract_months == 0:
                    clubs[club_id].monthly_wage_bill = max(
                        0.0,
                        clubs[club_id].monthly_wage_bill - player.monthly_wage,
                    )
                    free_agents.append(player)
                else:
                    roster.players.append(player)


class AcademyLifecycleSystem:
    """Ageing, retirement and academy graduation replace one-off static rosters."""

    def __init__(self, seed: int = 6100) -> None:
        self.seed = seed
        self.intake_history: list[AcademyIntakeRecord] = []
        self.retirement_history: list[RetirementRecord] = []

    def settle_season(
        self,
        month: int,
        state: NationalFootballSystem,
        rosters: dict[str, ClubRoster],
        free_agents: list[Player],
    ) -> None:
        if month not in (12, 24):
            return
        season = 1 if month == 12 else 2
        for club_id, roster in rosters.items():
            club = state.clubs[club_id]
            self._retire_players(month, club, roster)
            region = state.regions[club.region_id]
            environment = region.development_environment
            base_count = 2 + int(2.2 * club.academy_quality)
            minimum_needed = max(0, 21 - len(roster.players))
            intake_count = max(base_count, minimum_needed)
            for index in range(intake_count):
                player = self._generate_graduate(
                    season,
                    index,
                    club,
                    roster,
                    environment,
                )
                roster.players.append(player)
                club.monthly_wage_bill += player.monthly_wage
                club.cash = max(0.0, club.cash - 35_000.0)
                self.intake_history.append(
                    AcademyIntakeRecord(
                        month,
                        club_id,
                        club.name,
                        player.id,
                        player.name,
                        player.position,
                        player.age,
                        player.ability,
                        player.potential,
                        environment,
                    )
                )

    def _retire_players(
        self,
        month: int,
        club: Club,
        roster: ClubRoster,
    ) -> None:
        for player in list(roster.players):
            rng = random.Random(self.seed + _seed(f"retire:{month}:{player.id}"))
            probability = (
                1.0
                if player.age >= 39
                else 0.72
                if player.age >= 37
                else 0.38
                if player.age >= 35
                else 0.12
                if player.age >= 34
                else 0.0
            )
            if len(roster.players) <= 18 or rng.random() >= probability:
                continue
            roster.players.remove(player)
            club.monthly_wage_bill = max(
                0.0,
                club.monthly_wage_bill - player.monthly_wage,
            )
            self.retirement_history.append(
                RetirementRecord(
                    month,
                    club.id,
                    club.name,
                    player.id,
                    player.name,
                    player.age,
                    player.ability,
                    player.appearances,
                    "age and physical decline",
                )
            )

    def _generate_graduate(
        self,
        season: int,
        index: int,
        club: Club,
        roster: ClubRoster,
        environment: float,
    ) -> Player:
        rng = random.Random(
            self.seed + _seed(f"academy:{club.id}:{season}:{index}")
        )
        target_counts = {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}
        position = min(
            target_counts,
            key=lambda item: sum(player.position == item for player in roster.players)
            / target_counts[item],
        )
        age = rng.choice((17, 17, 18))
        ability = _clamp(
            29.0
            + 17.0 * club.academy_quality
            + 0.13 * environment
            + rng.gauss(0.0, 3.5),
            30.0,
            59.0,
        )
        potential = _clamp(
            ability
            + 8.0
            + 20.0 * club.academy_quality
            + 0.10 * environment
            + rng.uniform(-4.0, 7.0),
            ability + 4.0,
            92.0,
        )
        return Player(
            id=f"{club.id}-academy-s{season}-{index + 1:02d}",
            name=f"{rng.choice(FIRST_NAMES[:10])} {rng.choice(LAST_NAMES[:10])}",
            position=position,
            age=age,
            ability=ability,
            potential=potential,
            fitness=rng.uniform(78.0, 96.0),
            morale=rng.uniform(55.0, 74.0),
            monthly_wage=3_200.0 + ability * 85.0,
            contract_months=36,
            homegrown=True,
            nationality="Longhua",
        )


class InsolvencySystem:
    """Excluded clubs can be liquidated and replaced by community successors."""

    def __init__(self) -> None:
        self.distress_streak: dict[str, int] = {}
        self.history: list[InsolvencyRecord] = []
        self.reconstituted: set[str] = set()

    def monitor(
        self,
        month: int,
        world: AdvancedClubWorld,
    ) -> None:
        for club_id, club in world.state.clubs.items():
            distressed = (
                club.license_status == "excluded"
                or (club.financial_health < 0.06 and club.wage_arrears_months >= 4)
            )
            self.distress_streak[club_id] = (
                self.distress_streak.get(club_id, 0) + 1 if distressed else 0
            )
        if month not in (12, 24):
            return
        for club_id, streak in list(self.distress_streak.items()):
            if streak < 3 or club_id in self.reconstituted:
                continue
            self._create_phoenix(month, club_id, world)

    def _create_phoenix(
        self,
        month: int,
        club_id: str,
        world: AdvancedClubWorld,
    ) -> None:
        club = world.state.clubs[club_id]
        roster = world.rosters[club_id]
        old_name = club.name
        debt_before = club.debt
        released = 0
        while (
            club.monthly_wage_bill > max(420_000.0, club.monthly_revenue * 0.82)
            and len(roster.players) > 18
        ):
            player = max(roster.players, key=lambda item: item.monthly_wage)
            roster.players.remove(player)
            world.contracts.free_agents.append(player)
            club.monthly_wage_bill = max(
                0.0,
                club.monthly_wage_bill - player.monthly_wage,
            )
            released += 1
        region = world.state.regions[club.region_id]
        club.name = f"{region.name.split()[0]} Community FC"
        club.debt *= 0.18
        club.cash = 550_000.0 + 650_000.0 * club.supporter_base
        club.monthly_revenue = max(430_000.0, club.monthly_revenue * 0.58)
        club.wage_arrears_months = 0
        club.license_status = "conditional"
        club.licensing_compliance = max(0.66, club.licensing_compliance)
        club.integrity = max(0.70, club.integrity)
        club.owner_patience = 0.68
        owner = world.pyramid.owners[club_id]
        owner.name = f"{region.name.split()[0]} Supporters Trust"
        owner.wealth = 0.34
        owner.ambition = 0.42
        owner.patience = 0.72
        owner.relationship_with_fa = 0.61
        owner.reputation = 0.76
        owner.bailout_memory = 0
        owner.promises_broken = 0
        owner.cumulative_injection = 0.0
        league = world.pyramid.premier if club_id in world.pyramid.premier.club_ids else world.pyramid.second
        deduction = 9 if month == 12 else 0
        if deduction:
            league.deduct_points(club_id, deduction)
        if club_id in league.table:
            league.table[club_id].team_name = club.name
        self.reconstituted.add(club_id)
        self.history.append(
            InsolvencyRecord(
                month,
                club_id,
                old_name,
                club.name,
                "liquidated and reconstituted",
                debt_before,
                club.debt,
                released,
                deduction,
                "old company failed; licence transferred to a supporter-backed successor",
            )
        )


@dataclass(slots=True)
class GenerationalEconomy:
    stadiums: StadiumSystem
    sponsors: SponsorshipSystem
    registration: RegistrationSystem
    lifecycle: AcademyLifecycleSystem
    insolvency: InsolvencySystem

    @classmethod
    def build(cls, clubs: dict[str, Club]) -> "GenerationalEconomy":
        return cls(
            stadiums=StadiumSystem(clubs),
            sponsors=SponsorshipSystem(),
            registration=RegistrationSystem(),
            lifecycle=AcademyLifecycleSystem(),
            insolvency=InsolvencySystem(),
        )


@dataclass(slots=True)
class GenerationalWorld:
    """Composition wrapper that adds long-run industry systems to AdvancedClubWorld."""

    base: AdvancedClubWorld
    economy: GenerationalEconomy
    monthly_industry_events: dict[int, list[str]] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        state: NationalFootballSystem,
        seed: int = 2026,
    ) -> "GenerationalWorld":
        base = AdvancedClubWorld.build(state, seed=seed)
        economy = GenerationalEconomy.build(state.clubs)
        economy.registration.register(0, state.clubs, base.rosters)
        return cls(base=base, economy=economy)

    def __getattr__(self, name: str):
        return getattr(self.base, name)

    def configure_registration_policy(self, option_id: str) -> None:
        self.economy.registration.configure(option_id)

    def advance_month(self, month: int) -> list[MatchResult]:
        events: list[str] = []
        if month in (1, 13):
            self.economy.sponsors.renew_season(
                month,
                self.state.clubs,
                self.rosters,
                set(self.pyramid.premier_ids),
                self.economy.stadiums.profiles,
            )
            events.append("commercial sponsorship cycle renewed")
        if month in (1, 7, 13, 19):
            self.economy.registration.register(
                month,
                self.state.clubs,
                self.rosters,
            )
            events.append(
                f"squads registered under {self.economy.registration.policy_name}"
            )

        reserves = self.economy.registration.suspend_unregistered(self.rosters)
        results = self.base.advance_month(month)
        self.economy.registration.restore_and_advance_reserves(
            month,
            reserves,
            self.rosters,
            self.state.clubs,
            self.contracts.free_agents,
        )
        self.economy.stadiums.settle_matches(
            month,
            results,
            self.state.clubs,
        )
        self.economy.stadiums.settle_month(
            month,
            self.state.clubs,
            self.pyramid.owners,
        )
        self.economy.sponsors.monitor_morality(month, self.state.clubs)
        self.economy.sponsors.pay_performance_bonuses(month, self.base)
        self.economy.insolvency.monitor(month, self.base)
        self.economy.lifecycle.settle_season(
            month,
            self.state,
            self.rosters,
            self.contracts.free_agents,
        )
        if month in (12, 24):
            events.append("retirements and academy graduation completed")
        if self.economy.insolvency.history and self.economy.insolvency.history[-1].month == month:
            events.append("a failed club was replaced by a community phoenix club")
        self.monthly_industry_events[month] = events
        return results

    @property
    def recent_results(self) -> list[MatchResult]:
        return self.base.recent_results
