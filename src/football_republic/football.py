"""Sporting layer: player rosters, domestic league and international qualifiers."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import random

from .domain import Club, NationalFootballSystem


POSITIONS = ("GK", "DEF", "MID", "ATT")
POSITION_COUNTS = {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}
FIRST_NAMES = (
    "Jian", "Wei", "Bo", "Kai", "Jun", "Ming", "Tao", "Chen", "Rui", "Hao",
    "Leo", "Mateo", "Noah", "Luka", "Elias", "Ivan", "Sami", "Omar", "Diego", "Ren",
)
LAST_NAMES = (
    "Lin", "Zhao", "Han", "Xu", "Qin", "Song", "Lu", "Deng", "Shen", "Gu",
    "Silva", "Kovacs", "Tanaka", "Kim", "Rossi", "Santos", "Haddad", "Petrov", "Costa", "Nakamura",
)


def _stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _poisson(rng: random.Random, mean: float) -> int:
    mean = max(0.01, min(mean, 6.0))
    limit = math.exp(-mean)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


@dataclass(slots=True)
class Player:
    id: str
    name: str
    position: str
    age: int
    ability: float
    potential: float
    fitness: float
    morale: float
    monthly_wage: float
    contract_months: int
    homegrown: bool
    nationality: str
    appearances: int = 0
    goals: int = 0
    injury_months: int = 0

    def __post_init__(self) -> None:
        if self.position not in POSITIONS:
            raise ValueError(f"unsupported position: {self.position}")
        if not 15 <= self.age <= 45:
            raise ValueError("age must be between 15 and 45")
        for name in ("ability", "potential", "fitness", "morale"):
            value = getattr(self, name)
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
        if self.monthly_wage < 0 or self.contract_months < 0:
            raise ValueError("wage and contract length cannot be negative")

    @property
    def match_readiness(self) -> float:
        if self.injury_months > 0:
            return 0.0
        return self.ability * (
            0.72 + 0.18 * self.fitness / 100.0 + 0.10 * self.morale / 100.0
        )

    def advance_month(self, rng: random.Random, academy_quality: float) -> None:
        self.contract_months = max(0, self.contract_months - 1)
        self.injury_months = max(0, self.injury_months - 1)
        self.fitness = _clamp(self.fitness + rng.uniform(2.0, 7.0), 35.0, 100.0)
        self.morale = _clamp(
            self.morale + (55.0 - self.morale) * 0.08, 0.0, 100.0
        )
        if self.age <= 23 and self.ability < self.potential:
            growth = (self.potential - self.ability) * (
                0.008 + 0.012 * academy_quality
            )
            self.ability = _clamp(self.ability + growth, 0.0, self.potential)
        elif self.age >= 31:
            self.ability = _clamp(
                self.ability - 0.05 * (self.age - 30), 20.0, 100.0
            )


@dataclass(slots=True)
class ClubRoster:
    club_id: str
    players: list[Player]
    tactical_cohesion: float
    medical_quality: float
    form: float = 0.0

    def __post_init__(self) -> None:
        if len(self.players) < 18:
            raise ValueError("a professional roster needs at least 18 players")
        self.tactical_cohesion = _clamp(self.tactical_cohesion, 0.0, 1.0)
        self.medical_quality = _clamp(self.medical_quality, 0.0, 1.0)

    def line_rating(self, position: str, count: int) -> float:
        candidates = sorted(
            (
                player.match_readiness
                for player in self.players
                if player.position == position
            ),
            reverse=True,
        )
        if not candidates:
            return 20.0
        selected = candidates[:count]
        if len(selected) < count:
            selected += [selected[-1] * 0.70] * (count - len(selected))
        return sum(selected) / count

    @property
    def attack(self) -> float:
        return 0.68 * self.line_rating("ATT", 3) + 0.32 * self.line_rating("MID", 3)

    @property
    def midfield(self) -> float:
        return 0.82 * self.line_rating("MID", 3) + 0.18 * self.line_rating("DEF", 4)

    @property
    def defense(self) -> float:
        return 0.78 * self.line_rating("DEF", 4) + 0.22 * self.line_rating("GK", 1)

    @property
    def goalkeeper(self) -> float:
        return self.line_rating("GK", 1)

    @property
    def overall(self) -> float:
        base = (
            0.30 * self.attack
            + 0.30 * self.midfield
            + 0.30 * self.defense
            + 0.10 * self.goalkeeper
        )
        return base * (0.88 + 0.12 * self.tactical_cohesion)

    @property
    def depth(self) -> float:
        readiness = sorted(
            (player.match_readiness for player in self.players), reverse=True
        )
        return sum(readiness[11:18]) / max(1, len(readiness[11:18]))

    @property
    def average_age(self) -> float:
        return sum(player.age for player in self.players) / len(self.players)

    @property
    def homegrown_share(self) -> float:
        return sum(player.homegrown for player in self.players) / len(self.players)

    @property
    def monthly_wage_bill(self) -> float:
        return sum(player.monthly_wage for player in self.players)

    def advance_month(self, month: int) -> None:
        rng = random.Random(_stable_seed(f"{self.club_id}:month:{month}"))
        for player in self.players:
            player.advance_month(rng, self.tactical_cohesion)
            if player.injury_months == 0:
                injury_risk = (
                    0.003
                    + max(0.0, 74.0 - player.fitness) / 1800.0
                    + (1.0 - self.medical_quality) * 0.005
                )
                if rng.random() < injury_risk:
                    player.injury_months = rng.choice((1, 1, 2, 3))
        if month % 12 == 0:
            for player in self.players:
                player.age += 1
        self.tactical_cohesion = _clamp(
            self.tactical_cohesion + 0.003, 0.0, 1.0
        )

    def apply_match(self, goals_for: int, goals_against: int) -> None:
        if goals_for > goals_against:
            morale_delta, form_delta = 4.5, 0.18
        elif goals_for == goals_against:
            morale_delta, form_delta = 0.8, 0.02
        else:
            morale_delta, form_delta = -3.0, -0.15
        self.form = _clamp(
            self.form * 0.72 + form_delta, -1.0, 1.0
        )
        starters = sorted(
            self.players, key=lambda player: player.match_readiness, reverse=True
        )[:11]
        for player in starters:
            player.appearances += 1
            player.fitness = _clamp(
                player.fitness - (7.5 - 2.5 * self.medical_quality),
                20.0,
                100.0,
            )
            player.morale = _clamp(
                player.morale + morale_delta, 0.0, 100.0
            )


@dataclass(frozen=True, slots=True)
class MatchResult:
    competition: str
    season: int
    round_number: int
    month: int
    home_id: str
    away_id: str
    home_name: str
    away_name: str
    home_goals: int
    away_goals: int
    home_xg: float
    away_xg: float
    possession_home: float
    attendance: int
    gate_receipts: float

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}-{self.away_goals}"


@dataclass(slots=True)
class Standing:
    team_id: str
    team_name: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    form: list[str] = field(default_factory=list)

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def record(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
            self.points += 3
            marker = "W"
        elif goals_for == goals_against:
            self.drawn += 1
            self.points += 1
            marker = "D"
        else:
            self.lost += 1
            marker = "L"
        self.form = (self.form + [marker])[-5:]


class MatchSimulator:
    def __init__(self, seed: int = 2026) -> None:
        self.seed = seed

    def play_club_match(
        self,
        *,
        competition: str,
        season: int,
        round_number: int,
        month: int,
        home: Club,
        away: Club,
        home_roster: ClubRoster,
        away_roster: ClubRoster,
    ) -> MatchResult:
        rng = random.Random(
            self.seed
            + _stable_seed(
                f"{competition}:{season}:{round_number}:{home.id}:{away.id}"
            )
        )
        if home.license_status == "excluded":
            return self._forfeit(
                competition, season, round_number, month, home, away, 0, 3
            )
        if away.license_status == "excluded":
            return self._forfeit(
                competition, season, round_number, month, home, away, 3, 0
            )

        home_attack = home_roster.attack + 3.0 + 2.5 * home_roster.form
        away_attack = away_roster.attack + 2.0 * away_roster.form
        home_xg = _clamp(
            1.18
            + (home_attack - away_roster.defense) / 18.0
            + (home_roster.midfield - away_roster.midfield) / 35.0,
            0.18,
            4.2,
        )
        away_xg = _clamp(
            0.96
            + (away_attack - home_roster.defense) / 18.0
            + (away_roster.midfield - home_roster.midfield) / 35.0,
            0.15,
            3.8,
        )
        home_goals = _poisson(rng, home_xg)
        away_goals = _poisson(rng, away_xg)
        possession = _clamp(
            50.0
            + (home_roster.midfield - away_roster.midfield) * 0.42
            + rng.uniform(-3.0, 3.0),
            32.0,
            68.0,
        )
        capacity = int(18_000 + 42_000 * home.supporter_base)
        demand = (
            0.52
            + 0.28 * home.supporter_base
            + 0.12 * max(-0.5, home_roster.form)
        )
        attendance = int(
            capacity
            * _clamp(demand + rng.uniform(-0.04, 0.04), 0.25, 0.98)
        )
        ticket_price = 18.0 + 22.0 * home.supporter_base
        gate = attendance * ticket_price
        home.cash += gate

        home_roster.apply_match(home_goals, away_goals)
        away_roster.apply_match(away_goals, home_goals)
        return MatchResult(
            competition=competition,
            season=season,
            round_number=round_number,
            month=month,
            home_id=home.id,
            away_id=away.id,
            home_name=home.name,
            away_name=away.name,
            home_goals=home_goals,
            away_goals=away_goals,
            home_xg=home_xg,
            away_xg=away_xg,
            possession_home=possession,
            attendance=attendance,
            gate_receipts=gate,
        )

    def _forfeit(
        self,
        competition: str,
        season: int,
        round_number: int,
        month: int,
        home: Club,
        away: Club,
        home_goals: int,
        away_goals: int,
    ) -> MatchResult:
        return MatchResult(
            competition,
            season,
            round_number,
            month,
            home.id,
            away.id,
            home.name,
            away.name,
            home_goals,
            away_goals,
            float(home_goals),
            float(away_goals),
            50.0,
            0,
            0.0,
        )

    def play_national_match(
        self,
        *,
        competition: str,
        round_number: int,
        month: int,
        home: "NationalTeam",
        away: "NationalTeam",
    ) -> MatchResult:
        rng = random.Random(
            self.seed
            + _stable_seed(
                f"{competition}:{round_number}:{home.code}:{away.code}"
            )
        )
        home_xg = _clamp(
            1.14 + (home.strength - away.strength) / 13.0, 0.15, 4.3
        )
        away_xg = _clamp(
            0.92 + (away.strength - home.strength) / 13.0, 0.12, 3.9
        )
        home_goals = _poisson(rng, home_xg)
        away_goals = _poisson(rng, away_xg)
        possession = _clamp(
            50.0
            + (home.strength - away.strength) * 0.34
            + rng.uniform(-4.0, 4.0),
            30.0,
            70.0,
        )
        attendance = int(
            42_000
            * _clamp(
                0.72 + max(home.strength, away.strength) / 260.0,
                0.55,
                0.99,
            )
        )
        return MatchResult(
            competition,
            1,
            round_number,
            month,
            home.code,
            away.code,
            home.name,
            away.name,
            home_goals,
            away_goals,
            home_xg,
            away_xg,
            possession,
            attendance,
            attendance * 24.0,
        )


def _round_robin(team_ids: list[str]) -> list[list[tuple[str, str]]]:
    if len(team_ids) % 2:
        team_ids = team_ids + ["BYE"]
    rotation = list(team_ids)
    rounds: list[list[tuple[str, str]]] = []
    for round_index in range(len(rotation) - 1):
        pairs: list[tuple[str, str]] = []
        half = len(rotation) // 2
        for index in range(half):
            left = rotation[index]
            right = rotation[-1 - index]
            if "BYE" not in (left, right):
                if round_index % 2:
                    pairs.append((right, left))
                else:
                    pairs.append((left, right))
        rounds.append(pairs)
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
    return rounds


class DomesticLeague:
    def __init__(
        self,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        seed: int = 2026,
    ) -> None:
        self.clubs = clubs
        self.rosters = rosters
        self.simulator = MatchSimulator(seed)
        self.season = 1
        self.round_number = 0
        self.table: dict[str, Standing] = {
            club.id: Standing(club.id, club.name) for club in clubs.values()
        }
        self.results: list[MatchResult] = []
        self.season_history: list[dict[str, Standing]] = []
        first_half = _round_robin(list(clubs))
        second_half = [
            [(away, home) for home, away in round_] for round_ in first_half
        ]
        self.schedule = first_half + second_half
        self.months_by_season = {
            1: list(range(2, 12)),
            2: list(range(14, 24)),
        }

    def advance_month(self, month: int) -> list[MatchResult]:
        if month == 14 and self.season == 1:
            self._finish_season()
            self.season = 2
            self.round_number = 0
            self.table = {
                club.id: Standing(club.id, club.name)
                for club in self.clubs.values()
            }
        months = self.months_by_season.get(self.season, [])
        if month not in months:
            return []
        index = months.index(month)
        if index >= len(self.schedule):
            return []
        self.round_number = index + 1
        round_results: list[MatchResult] = []
        for home_id, away_id in self.schedule[index]:
            result = self.simulator.play_club_match(
                competition="National Premier League",
                season=self.season,
                round_number=self.round_number,
                month=month,
                home=self.clubs[home_id],
                away=self.clubs[away_id],
                home_roster=self.rosters[home_id],
                away_roster=self.rosters[away_id],
            )
            self._record(result)
            round_results.append(result)
        self.results.extend(round_results)
        if month == months[-1]:
            self._finish_season()
        return round_results

    def _record(self, result: MatchResult) -> None:
        self.table[result.home_id].record(
            result.home_goals, result.away_goals
        )
        self.table[result.away_id].record(
            result.away_goals, result.home_goals
        )

    def sorted_table(self) -> list[Standing]:
        return sorted(
            self.table.values(),
            key=lambda row: (
                row.points,
                row.goal_difference,
                row.goals_for,
                row.team_name,
            ),
            reverse=True,
        )

    def _finish_season(self) -> None:
        if not any(row.played for row in self.table.values()):
            return
        ordered = self.sorted_table()
        prizes = [
            3_000_000,
            2_200_000,
            1_600_000,
            1_200_000,
            900_000,
            650_000,
        ]
        for position, row in enumerate(ordered):
            club = self.clubs[row.team_id]
            club.cash += prizes[min(position, len(prizes) - 1)]
            performance_factor = (len(ordered) - position) / len(ordered)
            club.monthly_revenue *= 0.96 + 0.08 * performance_factor
        snapshot = {
            row.team_id: Standing(
                team_id=row.team_id,
                team_name=row.team_name,
                played=row.played,
                won=row.won,
                drawn=row.drawn,
                lost=row.lost,
                goals_for=row.goals_for,
                goals_against=row.goals_against,
                points=row.points,
                form=list(row.form),
            )
            for row in ordered
        }
        if not self.season_history or self.season_history[-1] != snapshot:
            self.season_history.append(snapshot)


@dataclass(slots=True)
class NationalTeam:
    code: str
    name: str
    strength: float


class InternationalQualifiers:
    def __init__(self, user_code: str = "LON", seed: int = 4040) -> None:
        self.user_code = user_code
        self.teams = {
            "LON": NationalTeam("LON", "Longhua", 47.5),
            "YAM": NationalTeam("YAM", "Yamato", 62.0),
            "HAN": NationalTeam("HAN", "Hanseong", 59.0),
            "ARV": NationalTeam("ARV", "Arvania", 53.0),
            "NUS": NationalTeam("NUS", "Nusantara", 48.0),
            "STP": NationalTeam("STP", "Steppe Union", 43.0),
        }
        self.table = {
            team.code: Standing(team.code, team.name)
            for team in self.teams.values()
        }
        first_half = _round_robin(list(self.teams))
        second_half = [
            [(away, home) for home, away in round_] for round_ in first_half
        ]
        self.schedule = first_half + second_half
        self.round_months = [3, 5, 7, 9, 11, 15, 17, 19, 21, 23]
        self.results: list[MatchResult] = []
        self.simulator = MatchSimulator(seed)

    def advance_month(
        self,
        month: int,
        state: NationalFootballSystem,
    ) -> list[MatchResult]:
        if month not in self.round_months:
            return []
        round_index = self.round_months.index(month)
        self.teams[self.user_code].strength = state.national_team_strength
        round_results: list[MatchResult] = []
        for home_code, away_code in self.schedule[round_index]:
            home = self.teams[home_code]
            away = self.teams[away_code]
            expected_home = 1.0 / (
                1.0 + 10 ** ((away.strength - home.strength) / 18.0)
            )
            result = self.simulator.play_national_match(
                competition="Continental World Cup Qualifiers",
                round_number=round_index + 1,
                month=month,
                home=home,
                away=away,
            )
            self.table[home_code].record(
                result.home_goals, result.away_goals
            )
            self.table[away_code].record(
                result.away_goals, result.home_goals
            )
            actual_home = (
                1.0
                if result.home_goals > result.away_goals
                else 0.5
                if result.home_goals == result.away_goals
                else 0.0
            )
            shift = 1.6 * (actual_home - expected_home)
            home.strength = _clamp(home.strength + shift, 20.0, 95.0)
            away.strength = _clamp(away.strength - shift, 20.0, 95.0)
            if self.user_code in (home_code, away_code):
                user_home = home_code == self.user_code
                expected = expected_home if user_home else 1.0 - expected_home
                actual = actual_home if user_home else 1.0 - actual_home
                state.fan_trust = _clamp(
                    state.fan_trust + 0.035 * (actual - expected),
                    0.0,
                    1.0,
                )
                state.national_team_strength = self.teams[
                    self.user_code
                ].strength
            round_results.append(result)
        self.results.extend(round_results)
        return round_results

    def sorted_table(self) -> list[Standing]:
        return sorted(
            self.table.values(),
            key=lambda row: (
                row.points,
                row.goal_difference,
                row.goals_for,
                row.team_name,
            ),
            reverse=True,
        )

    @property
    def user_position(self) -> int:
        for index, row in enumerate(self.sorted_table(), start=1):
            if row.team_id == self.user_code:
                return index
        return len(self.teams)

    @property
    def qualification_status(self) -> str:
        position = self.user_position
        if position <= 2:
            return "direct qualification place"
        if position == 3:
            return "play-off place"
        return "outside qualification places"


@dataclass(slots=True)
class FootballWorld:
    state: NationalFootballSystem
    rosters: dict[str, ClubRoster]
    domestic_league: DomesticLeague
    international: InternationalQualifiers
    monthly_events: dict[int, list[MatchResult]] = field(default_factory=dict)

    @classmethod
    def build(
        cls, state: NationalFootballSystem, seed: int = 2026
    ) -> "FootballWorld":
        rosters = {
            club_id: generate_roster(club, seed=seed)
            for club_id, club in state.clubs.items()
        }
        return cls(
            state=state,
            rosters=rosters,
            domestic_league=DomesticLeague(
                state.clubs, rosters, seed=seed
            ),
            international=InternationalQualifiers(seed=seed + 1),
        )

    def advance_month(self, month: int) -> list[MatchResult]:
        for roster in self.rosters.values():
            roster.advance_month(month)
        results = self.domestic_league.advance_month(month)
        results += self.international.advance_month(month, self.state)
        self.monthly_events[month] = results
        return results

    @property
    def recent_results(self) -> list[MatchResult]:
        all_results = (
            self.domestic_league.results + self.international.results
        )
        return sorted(
            all_results,
            key=lambda item: (
                item.month,
                item.competition,
                item.round_number,
            ),
        )[-12:]


def generate_roster(club: Club, seed: int = 2026) -> ClubRoster:
    rng = random.Random(seed + _stable_seed(club.id))
    resource_score = (
        0.30 * club.academy_quality
        + 0.25 * club.supporter_base
        + 0.25 * club.financial_health
        + 0.20 * club.licensing_compliance
    )
    base_ability = 43.0 + 27.0 * resource_score
    foreign_share = _clamp(
        0.14 + 0.26 * club.supporter_base, 0.10, 0.42
    )
    players: list[Player] = []
    index = 0
    for position, count in POSITION_COUNTS.items():
        for _ in range(count):
            index += 1
            age = rng.randint(17, 34)
            age_curve = 5.0 - abs(age - 27) * 0.55
            position_bonus = {
                "GK": -0.5,
                "DEF": 0.0,
                "MID": 0.8,
                "ATT": 1.2,
            }[position]
            ability = _clamp(
                base_ability
                + age_curve
                + position_bonus
                + rng.gauss(0.0, 4.8),
                35.0,
                84.0,
            )
            potential = _clamp(
                ability
                + max(0.0, (24 - age) * 1.15)
                + rng.uniform(0.0, 8.0),
                ability,
                91.0,
            )
            foreign = rng.random() < foreign_share
            nationality = (
                rng.choice(
                    (
                        "Yamato",
                        "Hanseong",
                        "Arvania",
                        "Nusantara",
                        "Steppe Union",
                    )
                )
                if foreign
                else "Longhua"
            )
            wage_weight = (ability / 60.0) ** 2
            wage = max(
                5_000.0,
                club.monthly_wage_bill * wage_weight / 35.0,
            )
            players.append(
                Player(
                    id=f"{club.id}-{index:02d}",
                    name=(
                        f"{rng.choice(FIRST_NAMES)} "
                        f"{rng.choice(LAST_NAMES)}"
                    ),
                    position=position,
                    age=age,
                    ability=ability,
                    potential=potential,
                    fitness=rng.uniform(76.0, 98.0),
                    morale=rng.uniform(45.0, 72.0),
                    monthly_wage=wage,
                    contract_months=rng.randint(8, 42),
                    homegrown=(
                        not foreign
                        and rng.random()
                        < (0.48 + 0.38 * club.academy_quality)
                    ),
                    nationality=nationality,
                )
            )
    return ClubRoster(
        club_id=club.id,
        players=players,
        tactical_cohesion=_clamp(
            0.42 + 0.40 * club.licensing_compliance, 0.0, 1.0
        ),
        medical_quality=_clamp(
            0.35 + 0.45 * club.financial_health, 0.0, 1.0
        ),
    )
