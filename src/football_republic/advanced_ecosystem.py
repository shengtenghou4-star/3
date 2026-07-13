"""Cups, continental football, workload and player-contract realism."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random

from .domain import Club, NationalFootballSystem
from .ecosystem import (
    ClubPyramid,
    NationalSquad,
    NationalSquadSelector,
)
from .football import (
    ClubRoster,
    InternationalQualifiers,
    MatchResult,
    MatchSimulator,
    Player,
    Standing,
    generate_roster,
)


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round_robin(team_ids: list[str]) -> list[list[tuple[str, str]]]:
    rotation = list(team_ids)
    if len(rotation) % 2:
        rotation.append("BYE")
    rounds: list[list[tuple[str, str]]] = []
    for round_index in range(len(rotation) - 1):
        pairs: list[tuple[str, str]] = []
        half = len(rotation) // 2
        for index in range(half):
            left = rotation[index]
            right = rotation[-1 - index]
            if "BYE" not in (left, right):
                pairs.append((right, left) if round_index % 2 else (left, right))
        rounds.append(pairs)
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
    return rounds


@dataclass(frozen=True, slots=True)
class KnockoutResult:
    competition: str
    season: int
    stage: str
    match: MatchResult
    winner_id: str
    winner_name: str
    decided_by: str


@dataclass(frozen=True, slots=True)
class WorkloadReport:
    month: int
    club_id: str
    club_name: str
    matches: int
    continental_away_matches: int
    extra_fitness_cost: float
    injuries: int
    congestion_level: str


@dataclass(frozen=True, slots=True)
class ContractRecord:
    month: int
    player_id: str
    player_name: str
    club_id: str
    club_name: str
    action: str
    old_wage: float
    new_wage: float
    months: int
    note: str


@dataclass(frozen=True, slots=True)
class LoanRecord:
    start_month: int
    return_month: int
    player_id: str
    player_name: str
    parent_id: str
    parent_name: str
    borrower_id: str
    borrower_name: str
    wage_share: float
    status: str


@dataclass(slots=True)
class ActiveLoan:
    player: Player
    parent_id: str
    borrower_id: str
    return_month: int
    wage_share: float


@dataclass(frozen=True, slots=True)
class ContinentalSummary:
    season: int
    champion_id: str | None
    champion_name: str | None
    domestic_clubs: tuple[str, ...]
    domestic_best_stage: str
    domestic_prize_money: float


class DomesticCup:
    """Four-round national knockout cup containing all fourteen clubs."""

    MONTHS = {
        1: {"round_of_16": 4, "quarterfinal": 7, "semifinal": 10, "final": 12},
        2: {"round_of_16": 16, "quarterfinal": 19, "semifinal": 22, "final": 24},
    }
    PRIZES = {
        "round_of_16": 120_000.0,
        "quarterfinal": 240_000.0,
        "semifinal": 480_000.0,
        "final": 900_000.0,
        "champion": 1_500_000.0,
    }

    def __init__(
        self,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        seed: int = 6200,
    ) -> None:
        self.clubs = clubs
        self.rosters = rosters
        self.seed = seed
        self.results: list[KnockoutResult] = []
        self.champions: dict[int, str] = {}
        self._alive: dict[int, list[str]] = {}
        self._byes: dict[int, list[str]] = {}
        self._played: set[tuple[int, str]] = set()

    def advance_month(self, month: int, season: int) -> list[MatchResult]:
        stage = next(
            (
                name
                for name, stage_month in self.MONTHS[season].items()
                if stage_month == month
            ),
            None,
        )
        if stage is None or (season, stage) in self._played:
            return []
        self._played.add((season, stage))
        if stage == "round_of_16":
            seeded = sorted(
                self.clubs,
                key=lambda club_id: self.rosters[club_id].overall,
                reverse=True,
            )
            self._byes[season] = seeded[:2]
            participants = seeded[2:]
        else:
            participants = list(self._alive.get(season, []))
        pairs = self._pair(participants, season, stage)
        winners: list[str] = []
        matches: list[MatchResult] = []
        for index, (home_id, away_id) in enumerate(pairs, start=1):
            result = MatchSimulator(self.seed + season * 100).play_club_match(
                competition="National FA Cup",
                season=season,
                round_number=index,
                month=month,
                home=self.clubs[home_id],
                away=self.clubs[away_id],
                home_roster=self.rosters[home_id],
                away_roster=self.rosters[away_id],
            )
            winner_id, decided_by = self._winner(result, season, stage, index)
            winner = self.clubs[winner_id]
            winner.cash += self.PRIZES[stage]
            winners.append(winner_id)
            matches.append(result)
            self.results.append(
                KnockoutResult(
                    competition="National FA Cup",
                    season=season,
                    stage=stage,
                    match=result,
                    winner_id=winner_id,
                    winner_name=winner.name,
                    decided_by=decided_by,
                )
            )
        if stage == "round_of_16":
            winners += self._byes[season]
        self._alive[season] = winners
        if stage == "final" and winners:
            self.champions[season] = winners[0]
            self.clubs[winners[0]].cash += self.PRIZES["champion"]
        return matches

    def _pair(
        self,
        participants: list[str],
        season: int,
        stage: str,
    ) -> list[tuple[str, str]]:
        rng = random.Random(self.seed + _seed(f"cup:{season}:{stage}"))
        shuffled = list(participants)
        rng.shuffle(shuffled)
        return list(zip(shuffled[::2], shuffled[1::2]))

    def _winner(
        self,
        result: MatchResult,
        season: int,
        stage: str,
        index: int,
    ) -> tuple[str, str]:
        if result.home_goals > result.away_goals:
            return result.home_id, "90 minutes"
        if result.away_goals > result.home_goals:
            return result.away_id, "90 minutes"
        rng = random.Random(self.seed + _seed(f"tie:{season}:{stage}:{index}"))
        home_score = self.rosters[result.home_id].overall + rng.uniform(-5.0, 5.0)
        away_score = self.rosters[result.away_id].overall + rng.uniform(-5.0, 5.0)
        return (
            (result.home_id, "penalties")
            if home_score >= away_score
            else (result.away_id, "penalties")
        )


class ContinentalChampionsCup:
    """Eight-club continental competition: two groups, semifinals and final."""

    GROUP_MONTHS = {1: [3, 3, 5, 7, 9, 9], 2: [15, 15, 17, 19, 21, 21]}
    SEMIFINAL_MONTH = {1: 10, 2: 22}
    FINAL_MONTH = {1: 11, 2: 23}

    def __init__(
        self,
        domestic_clubs: dict[str, Club],
        domestic_rosters: dict[str, ClubRoster],
        qualifiers: list[str],
        season: int,
        seed: int = 7400,
    ) -> None:
        self.domestic_clubs = domestic_clubs
        self.domestic_rosters = domestic_rosters
        self.qualifiers = list(qualifiers[:2])
        self.season = season
        self.seed = seed
        self.external_clubs, self.external_rosters = self._build_external_clubs()
        self.clubs = {**domestic_clubs, **self.external_clubs}
        self.rosters = {**domestic_rosters, **self.external_rosters}
        participants = self.qualifiers + list(self.external_clubs)
        self.groups = {
            "A": participants[::2],
            "B": participants[1::2],
        }
        self.tables = {
            group: {
                club_id: Standing(club_id, self.clubs[club_id].name)
                for club_id in club_ids
            }
            for group, club_ids in self.groups.items()
        }
        self.schedules = {
            group: _round_robin(club_ids) + [
                [(away, home) for home, away in round_]
                for round_ in _round_robin(club_ids)
            ]
            for group, club_ids in self.groups.items()
        }
        self.group_results: list[MatchResult] = []
        self.knockout_results: list[KnockoutResult] = []
        self._group_rounds_played: set[int] = set()
        self._semifinalists: list[str] = []
        self._finalists: list[str] = []
        self.champion_id: str | None = None
        self.domestic_prize_money = 0.0
        self._semis_played = False
        self._final_played = False

    def advance_month(self, month: int) -> list[MatchResult]:
        matches: list[MatchResult] = []
        for round_index, round_month in enumerate(self.GROUP_MONTHS[self.season]):
            if round_month != month or round_index in self._group_rounds_played:
                continue
            self._group_rounds_played.add(round_index)
            for group, schedule in self.schedules.items():
                for home_id, away_id in schedule[round_index]:
                    result = self._play(home_id, away_id, month, round_index + 1, "Continental Champions Cup")
                    self.tables[group][home_id].record(result.home_goals, result.away_goals)
                    self.tables[group][away_id].record(result.away_goals, result.home_goals)
                    self.group_results.append(result)
                    matches.append(result)
                    for club_id in (home_id, away_id):
                        if club_id in self.domestic_clubs:
                            self.domestic_clubs[club_id].cash += 110_000.0
                            self.domestic_prize_money += 110_000.0
        if month == self.SEMIFINAL_MONTH[self.season] and not self._semis_played:
            self._semis_played = True
            self._prepare_semifinals()
            pairs = [
                (self._semifinalists[0], self._semifinalists[3]),
                (self._semifinalists[2], self._semifinalists[1]),
            ]
            for index, (home_id, away_id) in enumerate(pairs, start=1):
                result = self._play(home_id, away_id, month, index, "Continental Champions Cup")
                winner_id, decided_by = self._knockout_winner(result, f"semi:{index}")
                self._finalists.append(winner_id)
                self.knockout_results.append(
                    KnockoutResult(
                        "Continental Champions Cup",
                        self.season,
                        "semifinal",
                        result,
                        winner_id,
                        self.clubs[winner_id].name,
                        decided_by,
                    )
                )
                if winner_id in self.domestic_clubs:
                    self.domestic_clubs[winner_id].cash += 750_000.0
                    self.domestic_prize_money += 750_000.0
                matches.append(result)
        if month == self.FINAL_MONTH[self.season] and not self._final_played:
            self._final_played = True
            if len(self._finalists) == 2:
                result = self._play(
                    self._finalists[0],
                    self._finalists[1],
                    month,
                    1,
                    "Continental Champions Cup Final",
                )
                winner_id, decided_by = self._knockout_winner(result, "final")
                self.champion_id = winner_id
                self.knockout_results.append(
                    KnockoutResult(
                        "Continental Champions Cup",
                        self.season,
                        "final",
                        result,
                        winner_id,
                        self.clubs[winner_id].name,
                        decided_by,
                    )
                )
                if winner_id in self.domestic_clubs:
                    self.domestic_clubs[winner_id].cash += 2_500_000.0
                    self.domestic_prize_money += 2_500_000.0
                matches.append(result)
        return matches

    def _build_external_clubs(self) -> tuple[dict[str, Club], dict[str, ClubRoster]]:
        specs = (
            ("yamato_crown", "Yamato Crown", 0.83, 0.80),
            ("hanseong_united", "Hanseong United", 0.78, 0.76),
            ("arvania_royal", "Arvania Royal", 0.72, 0.68),
            ("nusantara_city", "Nusantara City", 0.66, 0.61),
            ("steppe_nomads", "Steppe Nomads", 0.57, 0.52),
            ("pacific_athletic", "Pacific Athletic", 0.63, 0.59),
        )
        clubs: dict[str, Club] = {}
        rosters: dict[str, ClubRoster] = {}
        for club_id, name, strength, supporters in specs:
            club = Club(
                club_id,
                name,
                "international",
                20_000_000,
                2_000_000,
                2_200_000 * strength,
                1_700_000 * strength,
                strength,
                0.82,
                0.72,
                0.75,
                supporters,
                0.24,
            )
            clubs[club_id] = club
            rosters[club_id] = generate_roster(club, seed=self.seed + self.season * 100)
        return clubs, rosters

    def _play(
        self,
        home_id: str,
        away_id: str,
        month: int,
        round_number: int,
        competition: str,
    ) -> MatchResult:
        return MatchSimulator(self.seed + self.season * 100).play_club_match(
            competition=competition,
            season=self.season,
            round_number=round_number,
            month=month,
            home=self.clubs[home_id],
            away=self.clubs[away_id],
            home_roster=self.rosters[home_id],
            away_roster=self.rosters[away_id],
        )

    def _prepare_semifinals(self) -> None:
        ordered: dict[str, list[Standing]] = {}
        for group, table in self.tables.items():
            ordered[group] = sorted(
                table.values(),
                key=lambda row: (row.points, row.goal_difference, row.goals_for),
                reverse=True,
            )
        self._semifinalists = [
            ordered["A"][0].team_id,
            ordered["A"][1].team_id,
            ordered["B"][0].team_id,
            ordered["B"][1].team_id,
        ]

    def _knockout_winner(self, result: MatchResult, key: str) -> tuple[str, str]:
        if result.home_goals > result.away_goals:
            return result.home_id, "90 minutes"
        if result.away_goals > result.home_goals:
            return result.away_id, "90 minutes"
        rng = random.Random(self.seed + _seed(f"continental:{self.season}:{key}"))
        home = self.rosters[result.home_id].overall + rng.uniform(-4.0, 4.0)
        away = self.rosters[result.away_id].overall + rng.uniform(-4.0, 4.0)
        return (result.home_id, "penalties") if home >= away else (result.away_id, "penalties")

    def sorted_group(self, group: str) -> list[Standing]:
        return sorted(
            self.tables[group].values(),
            key=lambda row: (row.points, row.goal_difference, row.goals_for),
            reverse=True,
        )

    @property
    def domestic_best_stage(self) -> str:
        domestic_ids = set(self.qualifiers)
        if self.champion_id in domestic_ids:
            return "champion"
        if any(result.winner_id in domestic_ids for result in self.knockout_results if result.stage == "semifinal"):
            return "final or semifinal"
        semifinal_ids = set(self._semifinalists)
        if domestic_ids & semifinal_ids:
            return "semifinal"
        return "group stage"

    @property
    def summary(self) -> ContinentalSummary:
        return ContinentalSummary(
            season=self.season,
            champion_id=self.champion_id,
            champion_name=self.clubs[self.champion_id].name if self.champion_id else None,
            domestic_clubs=tuple(self.qualifiers),
            domestic_best_stage=self.domestic_best_stage,
            domestic_prize_money=self.domestic_prize_money,
        )


class WorkloadManager:
    def __init__(self, seed: int = 8800) -> None:
        self.seed = seed
        self.history: list[WorkloadReport] = []

    def settle_month(
        self,
        month: int,
        results: list[MatchResult],
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> list[WorkloadReport]:
        match_counts = {club_id: 0 for club_id in clubs}
        away_travel = {club_id: 0 for club_id in clubs}
        for result in results:
            if result.home_id in match_counts:
                match_counts[result.home_id] += 1
            if result.away_id in match_counts:
                match_counts[result.away_id] += 1
                if "Continental" in result.competition:
                    away_travel[result.away_id] += 1
        reports: list[WorkloadReport] = []
        for club_id, matches in match_counts.items():
            if matches == 0:
                continue
            extra = max(0, matches - 2) * 2.8 + away_travel[club_id] * 1.8
            injuries = 0
            roster = rosters[club_id]
            rng = random.Random(self.seed + _seed(f"load:{month}:{club_id}"))
            if extra > 0:
                for player in roster.players:
                    if player.appearances <= 0 or player.injury_months > 0:
                        continue
                    player.fitness = _clamp(player.fitness - extra, 20.0, 100.0)
                    risk = 0.004 * max(0, matches - 2) + 0.003 * away_travel[club_id]
                    if rng.random() < risk:
                        player.injury_months = max(player.injury_months, rng.choice((1, 1, 2)))
                        injuries += 1
                roster.tactical_cohesion = _clamp(
                    roster.tactical_cohesion - 0.006 * max(0, matches - 3),
                    0.0,
                    1.0,
                )
            level = "extreme" if matches >= 6 else "high" if matches >= 4 else "normal"
            report = WorkloadReport(
                month,
                club_id,
                clubs[club_id].name,
                matches,
                away_travel[club_id],
                extra,
                injuries,
                level,
            )
            reports.append(report)
            self.history.append(report)
        return reports

    def settle_international_release(
        self,
        month: int,
        squad: NationalSquad,
        rosters: dict[str, ClubRoster],
    ) -> None:
        lookup = {
            player.id: player
            for roster in rosters.values()
            for player in roster.players
        }
        rng = random.Random(self.seed + _seed(f"international:{month}"))
        for member in squad.members:
            player = lookup.get(member.player_id)
            if player is None:
                continue
            player.fitness = _clamp(player.fitness - 4.5, 20.0, 100.0)
            if rng.random() < 0.008:
                player.injury_months = max(player.injury_months, 1)


class ContractMarket:
    """Contract expiry, renewals, free agents and development loans."""

    def __init__(self, seed: int = 9300) -> None:
        self.seed = seed
        self.free_agents: list[Player] = []
        self.contract_history: list[ContractRecord] = []
        self.loan_history: list[LoanRecord] = []
        self.active_loans: dict[str, ActiveLoan] = {}

    def advance_month(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
        second_ids: set[str],
    ) -> None:
        self._return_due_loans(month, clubs, rosters)
        self._renew_expiring(month, clubs, rosters)
        self._release_expired(month, clubs, rosters)
        if month in (6, 18):
            self._sign_free_agents(month, clubs, rosters)
            self._arrange_loans(month, clubs, rosters, premier_ids, second_ids)

    def _renew_expiring(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id, roster in rosters.items():
            club = clubs[club_id]
            for player in list(roster.players):
                if player.id in self.active_loans or not 0 < player.contract_months <= 3:
                    continue
                importance = player.ability + 0.35 * max(0.0, player.potential - player.ability)
                affordable = club.financial_health >= 0.22 and club.wage_arrears_months < 3
                should_offer = importance >= roster.overall - 5.0 and affordable
                if not should_offer:
                    continue
                age_factor = 1.10 if player.age <= 26 else 1.03 if player.age <= 30 else 0.94
                performance_factor = 1.0 + min(0.15, player.appearances / 100.0)
                new_wage = player.monthly_wage * age_factor * performance_factor
                rng = random.Random(self.seed + _seed(f"renew:{month}:{player.id}"))
                acceptance = (
                    0.46
                    + 0.20 * player.morale / 100.0
                    + 0.16 * club.financial_health
                    + 0.10 * (new_wage / max(player.monthly_wage, 1.0) - 1.0)
                )
                if rng.random() <= acceptance:
                    old_wage = player.monthly_wage
                    player.monthly_wage = new_wage
                    player.contract_months = 24 if player.age >= 30 else 36
                    club.monthly_wage_bill += new_wage - old_wage
                    self.contract_history.append(
                        ContractRecord(
                            month,
                            player.id,
                            player.name,
                            club_id,
                            club.name,
                            "renewed",
                            old_wage,
                            new_wage,
                            player.contract_months,
                            "club and player agreed before free agency",
                        )
                    )

    def _release_expired(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id, roster in rosters.items():
            club = clubs[club_id]
            expired = [
                player
                for player in roster.players
                if player.contract_months == 0 and player.id not in self.active_loans
            ]
            for player in expired:
                if len(roster.players) <= 18:
                    player.contract_months = 3
                    self.contract_history.append(
                        ContractRecord(
                            month,
                            player.id,
                            player.name,
                            club_id,
                            club.name,
                            "emergency extension",
                            player.monthly_wage,
                            player.monthly_wage,
                            3,
                            "minimum professional squad protection",
                        )
                    )
                    continue
                roster.players.remove(player)
                club.monthly_wage_bill = max(0.0, club.monthly_wage_bill - player.monthly_wage)
                self.free_agents.append(player)
                self.contract_history.append(
                    ContractRecord(
                        month,
                        player.id,
                        player.name,
                        club_id,
                        club.name,
                        "released",
                        player.monthly_wage,
                        0.0,
                        0,
                        "contract expired without renewal",
                    )
                )

    def _sign_free_agents(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id in sorted(clubs, key=lambda key: rosters[key].overall):
            club = clubs[club_id]
            roster = rosters[club_id]
            if club.license_status == "excluded" or club.financial_health < 0.18:
                continue
            signings = 0
            while self.free_agents and len(roster.players) < 25 and signings < 2:
                needs = {
                    position: sum(player.position == position for player in roster.players)
                    for position in ("GK", "DEF", "MID", "ATT")
                }
                target_position = min(needs, key=lambda position: needs[position] / {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}[position])
                candidates = [player for player in self.free_agents if player.position == target_position]
                if not candidates:
                    break
                player = max(candidates, key=lambda item: item.ability - item.monthly_wage / 30_000.0)
                wage = player.monthly_wage * (0.88 + 0.20 * club.supporter_base)
                if club.cash < wage * 6:
                    break
                self.free_agents.remove(player)
                old_wage = player.monthly_wage
                player.monthly_wage = wage
                player.contract_months = 18 if player.age >= 30 else 30
                player.morale = _clamp(player.morale + 5.0, 0.0, 100.0)
                roster.players.append(player)
                club.monthly_wage_bill += wage
                self.contract_history.append(
                    ContractRecord(
                        month,
                        player.id,
                        player.name,
                        club_id,
                        club.name,
                        "free-agent signing",
                        old_wage,
                        wage,
                        player.contract_months,
                        "signed without a transfer fee",
                    )
                )
                signings += 1

    def _arrange_loans(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
        second_ids: set[str],
    ) -> None:
        return_month = 12 if month == 6 else 24
        available: list[tuple[Player, str]] = []
        for parent_id in premier_ids:
            roster = rosters[parent_id]
            top_ids = {
                player.id
                for player in sorted(roster.players, key=lambda item: item.match_readiness, reverse=True)[:18]
            }
            for player in roster.players:
                if (
                    player.age <= 22
                    and player.id not in top_ids
                    and player.id not in self.active_loans
                    and player.contract_months > return_month - month
                ):
                    available.append((player, parent_id))
        borrowers = sorted(second_ids, key=lambda club_id: rosters[club_id].overall)
        for borrower_id in borrowers:
            if not available:
                break
            borrower = rosters[borrower_id]
            if len(borrower.players) >= 27:
                continue
            weakest_position = min(
                ("GK", "DEF", "MID", "ATT"),
                key=lambda position: borrower.line_rating(position, {"GK": 1, "DEF": 4, "MID": 3, "ATT": 3}[position]),
            )
            candidates = [item for item in available if item[0].position == weakest_position]
            if not candidates:
                continue
            player, parent_id = max(candidates, key=lambda item: item[0].potential)
            parent = rosters[parent_id]
            parent.players.remove(player)
            borrower.players.append(player)
            wage_share = 0.50
            clubs[parent_id].monthly_wage_bill -= player.monthly_wage * wage_share
            clubs[borrower_id].monthly_wage_bill += player.monthly_wage * wage_share
            self.active_loans[player.id] = ActiveLoan(
                player,
                parent_id,
                borrower_id,
                return_month,
                wage_share,
            )
            self.loan_history.append(
                LoanRecord(
                    month,
                    return_month,
                    player.id,
                    player.name,
                    parent_id,
                    clubs[parent_id].name,
                    borrower_id,
                    clubs[borrower_id].name,
                    wage_share,
                    "active",
                )
            )
            available.remove((player, parent_id))

    def _return_due_loans(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        due = [loan for loan in self.active_loans.values() if loan.return_month <= month]
        for loan in due:
            if loan.player in rosters[loan.borrower_id].players:
                rosters[loan.borrower_id].players.remove(loan.player)
                rosters[loan.parent_id].players.append(loan.player)
            clubs[loan.parent_id].monthly_wage_bill += loan.player.monthly_wage * loan.wage_share
            clubs[loan.borrower_id].monthly_wage_bill = max(
                0.0,
                clubs[loan.borrower_id].monthly_wage_bill - loan.player.monthly_wage * loan.wage_share,
            )
            self.loan_history.append(
                LoanRecord(
                    loan.return_month,
                    loan.return_month,
                    loan.player.id,
                    loan.player.name,
                    loan.parent_id,
                    clubs[loan.parent_id].name,
                    loan.borrower_id,
                    clubs[loan.borrower_id].name,
                    loan.wage_share,
                    "returned",
                )
            )
            del self.active_loans[loan.player.id]


@dataclass(slots=True)
class AdvancedClubWorld:
    state: NationalFootballSystem
    rosters: dict[str, ClubRoster]
    pyramid: ClubPyramid
    international: InternationalQualifiers
    selector: NationalSquadSelector
    current_squad: NationalSquad
    current_effective_strength: float
    domestic_cup: DomesticCup
    continental: ContinentalChampionsCup
    workload: WorkloadManager
    contracts: ContractMarket
    squad_history: list[NationalSquad] = field(default_factory=list)
    continental_history: list[ContinentalSummary] = field(default_factory=list)
    monthly_events: dict[int, list[MatchResult]] = field(default_factory=dict)
    _next_continental_qualifiers: list[str] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        state: NationalFootballSystem,
        seed: int = 2026,
    ) -> "AdvancedClubWorld":
        rosters = {
            club_id: generate_roster(club, seed=seed)
            for club_id, club in state.clubs.items()
        }
        pyramid = ClubPyramid(state.clubs, rosters, seed=seed)
        selector = NationalSquadSelector()
        squad = selector.select(0, state.clubs, rosters, set(pyramid.premier_ids))
        opening_qualifiers = sorted(
            pyramid.premier_ids,
            key=lambda club_id: rosters[club_id].overall,
            reverse=True,
        )[:2]
        return cls(
            state=state,
            rosters=rosters,
            pyramid=pyramid,
            international=InternationalQualifiers(seed=seed + 1),
            selector=selector,
            current_squad=squad,
            current_effective_strength=squad.strength,
            domestic_cup=DomesticCup(state.clubs, rosters, seed=seed + 200),
            continental=ContinentalChampionsCup(
                state.clubs,
                rosters,
                opening_qualifiers,
                season=1,
                seed=seed + 300,
            ),
            workload=WorkloadManager(seed=seed + 400),
            contracts=ContractMarket(seed=seed + 500),
            squad_history=[squad],
            _next_continental_qualifiers=opening_qualifiers,
        )

    @property
    def domestic_league(self):
        return self.pyramid.premier

    @property
    def second_division(self):
        return self.pyramid.second

    def advance_month(self, month: int) -> list[MatchResult]:
        for roster in self.rosters.values():
            roster.advance_month(month)
        if month == 12:
            self._next_continental_qualifiers = [
                row.team_id for row in self.pyramid.premier.sorted_table()[:2]
            ]
        results = self.pyramid.advance_month(month)
        season = 1 if month <= 12 else 2
        if month == 13:
            self.continental_history.append(self.continental.summary)
            self.continental = ContinentalChampionsCup(
                self.state.clubs,
                self.rosters,
                self._next_continental_qualifiers,
                season=2,
                seed=2326,
            )
        results += self.domestic_cup.advance_month(month, season)
        results += self.continental.advance_month(month)
        if month in self.international.round_months:
            self.current_squad = self.selector.select(
                month,
                self.state.clubs,
                self.rosters,
                set(self.pyramid.premier_ids),
            )
            self.squad_history.append(self.current_squad)
            institutional = self.state.national_team_strength
            effective = _clamp(
                0.74 * self.current_squad.strength + 0.26 * institutional,
                25.0,
                92.0,
            )
            self.current_effective_strength = effective
            self.state.national_team_strength = effective
            results += self.international.advance_month(month, self.state)
            post_match = self.state.national_team_strength
            self.current_effective_strength = post_match
            self.state.national_team_strength = _clamp(
                0.45 * institutional + 0.55 * post_match,
                20.0,
                95.0,
            )
            self.workload.settle_international_release(
                month,
                self.current_squad,
                self.rosters,
            )
        self.workload.settle_month(
            month,
            results,
            self.state.clubs,
            self.rosters,
        )
        self.contracts.advance_month(
            month,
            self.state.clubs,
            self.rosters,
            set(self.pyramid.premier_ids),
            set(self.pyramid.second_ids),
        )
        if month == 24:
            self.continental_history.append(self.continental.summary)
        self.monthly_events[month] = results
        return results

    @property
    def recent_results(self) -> list[MatchResult]:
        combined = (
            self.pyramid.all_results
            + [item.match for item in self.domestic_cup.results]
            + self.continental.group_results
            + [item.match for item in self.continental.knockout_results]
            + self.international.results
        )
        return sorted(
            combined,
            key=lambda result: (result.month, result.competition, result.round_number),
        )[-20:]
