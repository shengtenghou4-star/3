"""Deep professional ecosystem: two divisions, owners, media and national selection."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random

from .deep_scenario import PREMIER_CLUB_IDS, SECOND_DIVISION_CLUB_IDS
from .domain import Club, NationalFootballSystem
from .football import (
    ClubRoster,
    InternationalQualifiers,
    MatchResult,
    MatchSimulator,
    Player,
    Standing,
    generate_roster,
)


def _stable_seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
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
            if "BYE" in (left, right):
                continue
            pairs.append((right, left) if round_index % 2 else (left, right))
        rounds.append(pairs)
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
    return rounds


def _month_round_map(round_count: int, months: list[int]) -> dict[int, list[int]]:
    mapping = {month: [] for month in months}
    if round_count <= 1:
        mapping[months[0]].append(0)
        return mapping
    for round_index in range(round_count):
        month_index = round(round_index * (len(months) - 1) / (round_count - 1))
        mapping[months[month_index]].append(round_index)
    return mapping


@dataclass(frozen=True, slots=True)
class MediaDistribution:
    season: int
    division: int
    club_id: str
    club_name: str
    equal_share: float
    merit_share: float
    audience_share: float
    total: float


@dataclass(frozen=True, slots=True)
class PromotionMovement:
    season: int
    promoted_id: str
    promoted_name: str
    relegated_id: str
    relegated_name: str
    route: str
    note: str


@dataclass(frozen=True, slots=True)
class AdministrationRecord:
    month: int
    club_id: str
    club_name: str
    action: str
    points_deduction: int
    owner_injection: float
    note: str


@dataclass(slots=True)
class OwnerProfile:
    club_id: str
    name: str
    wealth: float
    ambition: float
    patience: float
    relationship_with_fa: float
    reputation: float
    bailout_memory: int = 0
    promises_broken: int = 0
    cumulative_injection: float = 0.0
    last_injection_month: int = -99

    def update_after_month(
        self,
        club: Club,
        position_ratio: float,
    ) -> None:
        financial_signal = club.financial_health - 0.45
        sporting_signal = 0.5 - position_ratio
        self.patience = _clamp(
            self.patience + 0.018 * financial_signal + 0.012 * sporting_signal
        )
        if club.wage_arrears_months > 0:
            self.reputation = _clamp(self.reputation - 0.008 * club.wage_arrears_months)

    def injection_capacity(self, club: Club) -> float:
        leverage_penalty = min(
            0.75,
            club.debt / max(club.monthly_revenue * 20.0, 1.0),
        )
        return self.wealth * self.patience * (1.0 - 0.55 * leverage_penalty)


@dataclass(frozen=True, slots=True)
class SquadMember:
    player_id: str
    player_name: str
    club_id: str
    club_name: str
    position: str
    age: int
    ability: float
    fitness: float
    morale: float
    appearances: int
    selection_score: float


@dataclass(frozen=True, slots=True)
class NationalSquad:
    month: int
    members: tuple[SquadMember, ...]
    strength: float
    average_age: float
    premier_share: float
    homegrown_share: float


class DivisionLeague:
    """One season of a domestic division with a variable number of rounds per month."""

    def __init__(
        self,
        *,
        competition: str,
        level: int,
        season: int,
        club_ids: list[str],
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        months: list[int],
        seed: int,
    ) -> None:
        self.competition = competition
        self.level = level
        self.season = season
        self.club_ids = list(club_ids)
        self.clubs = clubs
        self.rosters = rosters
        self.months = list(months)
        self.simulator = MatchSimulator(seed + season * 100 + level * 11)
        first_half = _round_robin(self.club_ids)
        second_half = [[(away, home) for home, away in round_] for round_ in first_half]
        self.schedule = first_half + second_half
        self.month_rounds = _month_round_map(len(self.schedule), self.months)
        self.table: dict[str, Standing] = {
            club_id: Standing(club_id, clubs[club_id].name)
            for club_id in self.club_ids
        }
        self.results: list[MatchResult] = []
        self.points_deductions: dict[str, int] = {club_id: 0 for club_id in self.club_ids}
        self.completed_rounds: set[int] = set()

    def advance_month(self, month: int) -> list[MatchResult]:
        results: list[MatchResult] = []
        for round_index in self.month_rounds.get(month, []):
            if round_index in self.completed_rounds:
                continue
            for home_id, away_id in self.schedule[round_index]:
                result = self.simulator.play_club_match(
                    competition=self.competition,
                    season=self.season,
                    round_number=round_index + 1,
                    month=month,
                    home=self.clubs[home_id],
                    away=self.clubs[away_id],
                    home_roster=self.rosters[home_id],
                    away_roster=self.rosters[away_id],
                )
                self.table[home_id].record(result.home_goals, result.away_goals)
                self.table[away_id].record(result.away_goals, result.home_goals)
                results.append(result)
            self.completed_rounds.add(round_index)
        self.results.extend(results)
        return results

    def deduct_points(self, club_id: str, points: int) -> None:
        if club_id not in self.table or points <= 0:
            return
        self.points_deductions[club_id] += points
        self.table[club_id].points -= points

    @property
    def completed(self) -> bool:
        return len(self.completed_rounds) == len(self.schedule)

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

    def position_of(self, club_id: str) -> int:
        for index, row in enumerate(self.sorted_table(), start=1):
            if row.team_id == club_id:
                return index
        return len(self.club_ids)


class NationalSquadSelector:
    QUOTAS = {"GK": 3, "DEF": 8, "MID": 8, "ATT": 7}

    def select(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
    ) -> NationalSquad:
        candidates: dict[str, list[tuple[float, Player, str]]] = {
            position: [] for position in self.QUOTAS
        }
        for club_id, roster in rosters.items():
            club = clubs[club_id]
            division_bonus = 3.0 if club_id in premier_ids else 0.0
            for player in roster.players:
                if player.nationality != "Longhua" or player.injury_months > 0:
                    continue
                minutes_signal = min(1.0, player.appearances / 12.0) * 100.0
                score = (
                    0.60 * player.ability
                    + 0.14 * player.fitness
                    + 0.10 * player.morale
                    + 0.08 * minutes_signal
                    + 6.0 * roster.form
                    + division_bonus
                    + (1.2 if player.homegrown else 0.0)
                )
                candidates[player.position].append((score, player, club_id))

        selected: list[SquadMember] = []
        for position, quota in self.QUOTAS.items():
            ranked = sorted(candidates[position], key=lambda item: item[0], reverse=True)
            if len(ranked) < quota:
                raise RuntimeError(f"not enough eligible national players at {position}")
            for score, player, club_id in ranked[:quota]:
                selected.append(
                    SquadMember(
                        player_id=player.id,
                        player_name=player.name,
                        club_id=club_id,
                        club_name=clubs[club_id].name,
                        position=player.position,
                        age=player.age,
                        ability=player.ability,
                        fitness=player.fitness,
                        morale=player.morale,
                        appearances=player.appearances,
                        selection_score=score,
                    )
                )

        starters: list[SquadMember] = []
        for position, count in {"GK": 1, "DEF": 4, "MID": 3, "ATT": 3}.items():
            group = sorted(
                (member for member in selected if member.position == position),
                key=lambda member: member.selection_score,
                reverse=True,
            )
            starters.extend(group[:count])
        bench = sorted(selected, key=lambda member: member.selection_score, reverse=True)[11:18]
        starter_quality = sum(member.selection_score for member in starters) / 11
        depth_quality = sum(member.selection_score for member in bench) / max(1, len(bench))
        strength = _clamp(0.84 * starter_quality + 0.16 * depth_quality, 25.0, 92.0)
        average_age = sum(member.age for member in selected) / len(selected)
        premier_share = sum(member.club_id in premier_ids for member in selected) / len(selected)
        selected_ids = {member.player_id for member in selected}
        player_lookup = {
            player.id: player
            for roster in rosters.values()
            for player in roster.players
            if player.id in selected_ids
        }
        homegrown_share = sum(player_lookup[member.player_id].homegrown for member in selected) / len(selected)
        return NationalSquad(
            month=month,
            members=tuple(selected),
            strength=strength,
            average_age=average_age,
            premier_share=premier_share,
            homegrown_share=homegrown_share,
        )


class ClubPyramid:
    """Two domestic levels with promotion, licensing, media and owner behaviour."""

    def __init__(
        self,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        seed: int = 2026,
    ) -> None:
        self.clubs = clubs
        self.rosters = rosters
        self.seed = seed
        self.season = 1
        self.premier_ids = list(PREMIER_CLUB_IDS)
        self.second_ids = list(SECOND_DIVISION_CLUB_IDS)
        self.media_history: list[MediaDistribution] = []
        self.movement_history: list[PromotionMovement] = []
        self.administration_history: list[AdministrationRecord] = []
        self.owner_event_log: list[str] = []
        self.all_results: list[MatchResult] = []
        self._settled_seasons: set[int] = set()
        self._media_seasons: set[int] = set()
        self._administered: set[str] = set()
        self.owners = self._build_owners()
        self.premier = self._build_league(level=1, season=1)
        self.second = self._build_league(level=2, season=1)

    def _build_owners(self) -> dict[str, OwnerProfile]:
        owners: dict[str, OwnerProfile] = {}
        surnames = (
            "Gu", "Han", "Lin", "Qiao", "Ren", "Shen", "Tang",
            "Xu", "Yan", "Zhao", "Luo", "Jiang", "Fang", "Wei",
        )
        for index, club in enumerate(self.clubs.values()):
            rng = random.Random(self.seed + _stable_seed(f"owner:{club.id}"))
            owners[club.id] = OwnerProfile(
                club_id=club.id,
                name=f"Chairman {surnames[index % len(surnames)]}",
                wealth=_clamp(0.30 + 0.58 * club.supporter_base + rng.uniform(-0.10, 0.12)),
                ambition=_clamp(0.35 + 0.45 * club.supporter_base + rng.uniform(-0.08, 0.16)),
                patience=club.owner_patience,
                relationship_with_fa=_clamp(0.35 + 0.35 * club.licensing_compliance + rng.uniform(-0.12, 0.12)),
                reputation=_clamp(0.30 + 0.45 * club.integrity + rng.uniform(-0.08, 0.12)),
            )
        return owners

    def _season_months(self, season: int) -> list[int]:
        return list(range(2, 12)) if season == 1 else list(range(14, 24))

    def _build_league(self, level: int, season: int) -> DivisionLeague:
        ids = self.premier_ids if level == 1 else self.second_ids
        name = "National Premier League" if level == 1 else "National Championship"
        return DivisionLeague(
            competition=name,
            level=level,
            season=season,
            club_ids=ids,
            clubs=self.clubs,
            rosters=self.rosters,
            months=self._season_months(season),
            seed=self.seed,
        )

    def advance_month(self, month: int) -> list[MatchResult]:
        if month in (1, 13):
            self._distribute_media_rights(self.season)
        results = self.premier.advance_month(month) + self.second.advance_month(month)
        self.all_results.extend(results)
        self._manage_financial_distress(month)
        self._update_owner_memory()
        if month == 12 and 1 not in self._settled_seasons:
            results += self._settle_season(1, month)
            self.all_results.extend(results)
            self.season = 2
            self.premier = self._build_league(level=1, season=2)
            self.second = self._build_league(level=2, season=2)
        elif month == 24 and 2 not in self._settled_seasons:
            results += self._settle_season(2, month)
            self.all_results.extend(results)
        return results

    def _eligible_for_promotion(self, club_id: str) -> tuple[bool, str]:
        club = self.clubs[club_id]
        if club.license_status == "excluded":
            return False, "excluded from professional competition"
        if club.licensing_compliance < 0.45:
            return False, "failed licensing compliance threshold"
        if club.financial_health < 0.18:
            return False, "failed financial viability threshold"
        if club.wage_arrears_months >= 3:
            return False, "unresolved wage arrears"
        return True, "eligible"

    def _settle_season(self, season: int, month: int) -> list[MatchResult]:
        self._settled_seasons.add(season)
        top_order = self.premier.sorted_table()
        second_order = self.second.sorted_table()
        used_promoted: set[str] = set()
        used_relegated: set[str] = set()
        playoff_results: list[MatchResult] = []

        promoted_row = next(
            (row for row in second_order if self._eligible_for_promotion(row.team_id)[0]),
            None,
        )
        relegated_row = next(
            (
                row for row in reversed(top_order)
                if row.team_id not in used_relegated
            ),
            None,
        )
        if promoted_row and relegated_row:
            self._swap_clubs(
                season,
                promoted_row.team_id,
                relegated_row.team_id,
                "automatic",
                "league position subject to financial and licensing eligibility",
            )
            used_promoted.add(promoted_row.team_id)
            used_relegated.add(relegated_row.team_id)

        playoff_promoted = next(
            (
                row for row in second_order
                if row.team_id not in used_promoted
                and self._eligible_for_promotion(row.team_id)[0]
            ),
            None,
        )
        playoff_top = next(
            (
                row for row in reversed(top_order)
                if row.team_id not in used_relegated
            ),
            None,
        )
        if playoff_promoted and playoff_top:
            result = MatchSimulator(self.seed + 8800).play_club_match(
                competition="Promotion Play-off",
                season=season,
                round_number=1,
                month=month,
                home=self.clubs[playoff_top.team_id],
                away=self.clubs[playoff_promoted.team_id],
                home_roster=self.rosters[playoff_top.team_id],
                away_roster=self.rosters[playoff_promoted.team_id],
            )
            playoff_results.append(result)
            away_won = result.away_goals > result.home_goals
            if result.away_goals == result.home_goals:
                away_won = (
                    self.rosters[playoff_promoted.team_id].overall
                    > self.rosters[playoff_top.team_id].overall + 2.0
                )
            if away_won:
                self._swap_clubs(
                    season,
                    playoff_promoted.team_id,
                    playoff_top.team_id,
                    "play-off",
                    f"won promotion play-off {result.scoreline}",
                )

        self._pay_prize_money(top_order, level=1)
        self._pay_prize_money(second_order, level=2)
        return playoff_results

    def _swap_clubs(
        self,
        season: int,
        promoted_id: str,
        relegated_id: str,
        route: str,
        note: str,
    ) -> None:
        if promoted_id not in self.second_ids or relegated_id not in self.premier_ids:
            return
        self.second_ids.remove(promoted_id)
        self.premier_ids.remove(relegated_id)
        self.premier_ids.append(promoted_id)
        self.second_ids.append(relegated_id)
        self.movement_history.append(
            PromotionMovement(
                season=season,
                promoted_id=promoted_id,
                promoted_name=self.clubs[promoted_id].name,
                relegated_id=relegated_id,
                relegated_name=self.clubs[relegated_id].name,
                route=route,
                note=note,
            )
        )
        self.owners[promoted_id].patience = _clamp(self.owners[promoted_id].patience + 0.08)
        self.owners[relegated_id].patience = _clamp(self.owners[relegated_id].patience - 0.10)
        self.clubs[promoted_id].monthly_revenue *= 1.22
        self.clubs[relegated_id].monthly_revenue *= 0.76

    def _pay_prize_money(self, order: list[Standing], level: int) -> None:
        pool = 9_000_000 if level == 1 else 3_200_000
        weights = list(range(len(order), 0, -1))
        total_weight = sum(weights)
        for row, weight in zip(order, weights):
            self.clubs[row.team_id].cash += pool * weight / total_weight

    def _distribute_media_rights(self, season: int) -> None:
        if season in self._media_seasons:
            return
        self._media_seasons.add(season)
        for level, ids, pool, league in (
            (1, self.premier_ids, 18_000_000.0, self.premier),
            (2, self.second_ids, 5_000_000.0, self.second),
        ):
            equal_pool = pool * 0.55
            merit_pool = pool * 0.25
            audience_pool = pool * 0.20
            audience_total = sum(max(0.05, self.clubs[club_id].supporter_base) for club_id in ids)
            if season == 1 or not league.table or not any(row.played for row in league.table.values()):
                merit_order = sorted(ids, key=lambda club_id: self.clubs[club_id].supporter_base, reverse=True)
            else:
                merit_order = [row.team_id for row in league.sorted_table()]
            merit_weights = {club_id: len(ids) - index for index, club_id in enumerate(merit_order)}
            merit_total = sum(merit_weights.values())
            for club_id in ids:
                equal = equal_pool / len(ids)
                merit = merit_pool * merit_weights[club_id] / merit_total
                audience = audience_pool * max(0.05, self.clubs[club_id].supporter_base) / audience_total
                total = equal + merit + audience
                self.clubs[club_id].cash += total
                self.media_history.append(
                    MediaDistribution(
                        season=season,
                        division=level,
                        club_id=club_id,
                        club_name=self.clubs[club_id].name,
                        equal_share=equal,
                        merit_share=merit,
                        audience_share=audience,
                        total=total,
                    )
                )

    def _current_league(self, club_id: str) -> DivisionLeague | None:
        if club_id in self.premier.club_ids:
            return self.premier
        if club_id in self.second.club_ids:
            return self.second
        return None

    def _manage_financial_distress(self, month: int) -> None:
        for club_id, club in self.clubs.items():
            owner = self.owners[club_id]
            annual_revenue = max(club.monthly_revenue * 12.0, 1.0)
            overleveraged = club.debt > annual_revenue * 1.35
            distressed = club.wage_arrears_months >= 3 or overleveraged
            league = self._current_league(club_id)

            if distressed and club_id not in self._administered and club.license_status != "excluded":
                club.license_status = "administration"
                self._administered.add(club_id)
                if league:
                    league.deduct_points(club_id, 6)
                self.administration_history.append(
                    AdministrationRecord(
                        month=month,
                        club_id=club_id,
                        club_name=club.name,
                        action="entered administration",
                        points_deduction=6,
                        owner_injection=0.0,
                        note="triggered by arrears or unsustainable leverage",
                    )
                )

            if club.license_status == "administration":
                capacity = owner.injection_capacity(club)
                can_inject = month - owner.last_injection_month >= 6
                if capacity >= 0.23 and can_inject:
                    injection = 450_000 + 2_600_000 * capacity
                    club.cash += injection
                    club.debt = max(0.0, club.debt - injection * 0.35)
                    club.wage_arrears_months = max(0, club.wage_arrears_months - 2)
                    owner.cumulative_injection += injection
                    owner.last_injection_month = month
                    owner.patience = _clamp(owner.patience - 0.07)
                    self.administration_history.append(
                        AdministrationRecord(
                            month=month,
                            club_id=club_id,
                            club_name=club.name,
                            action="owner rescue injection",
                            points_deduction=0,
                            owner_injection=injection,
                            note=f"{owner.name} injected funds under restructuring pressure",
                        )
                    )
                    if club.wage_arrears_months == 0 and club.financial_health >= 0.22:
                        club.license_status = "conditional"
                elif club.wage_arrears_months >= 4 or club.financial_health < 0.08:
                    club.license_status = "excluded"
                    owner.promises_broken += 1
                    owner.reputation = _clamp(owner.reputation - 0.12)
                    self.administration_history.append(
                        AdministrationRecord(
                            month=month,
                            club_id=club_id,
                            club_name=club.name,
                            action="professional licence withdrawn",
                            points_deduction=0,
                            owner_injection=0.0,
                            note="restructuring failed to restore minimum solvency",
                        )
                    )

    def _update_owner_memory(self) -> None:
        for club_id, owner in self.owners.items():
            league = self._current_league(club_id)
            if league is None:
                continue
            position = league.position_of(club_id)
            position_ratio = position / max(1, len(league.club_ids))
            owner.update_after_month(self.clubs[club_id], position_ratio)

    def register_bailout_response(self, club_id: str, option_id: str) -> None:
        owner = self.owners[club_id]
        if option_id == "blank_cheque":
            owner.bailout_memory += 2
            owner.relationship_with_fa = _clamp(owner.relationship_with_fa + 0.08)
            owner.reputation = _clamp(owner.reputation - 0.06)
        elif option_id == "conditional_rescue":
            owner.bailout_memory += 1
            owner.relationship_with_fa = _clamp(owner.relationship_with_fa + 0.03)
            owner.patience = _clamp(owner.patience - 0.03)
        else:
            owner.relationship_with_fa = _clamp(owner.relationship_with_fa - 0.10)
            owner.patience = _clamp(owner.patience - 0.08)


@dataclass(slots=True)
class ClubPyramidWorld:
    state: NationalFootballSystem
    rosters: dict[str, ClubRoster]
    pyramid: ClubPyramid
    international: InternationalQualifiers
    selector: NationalSquadSelector
    current_squad: NationalSquad
    current_effective_strength: float
    squad_history: list[NationalSquad] = field(default_factory=list)
    monthly_events: dict[int, list[MatchResult]] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        state: NationalFootballSystem,
        seed: int = 2026,
    ) -> "ClubPyramidWorld":
        rosters = {
            club_id: generate_roster(club, seed=seed)
            for club_id, club in state.clubs.items()
        }
        pyramid = ClubPyramid(state.clubs, rosters, seed=seed)
        selector = NationalSquadSelector()
        opening_squad = selector.select(
            0,
            state.clubs,
            rosters,
            set(pyramid.premier_ids),
        )
        return cls(
            state=state,
            rosters=rosters,
            pyramid=pyramid,
            international=InternationalQualifiers(seed=seed + 1),
            selector=selector,
            current_squad=opening_squad,
            current_effective_strength=opening_squad.strength,
            squad_history=[opening_squad],
        )

    @property
    def domestic_league(self) -> DivisionLeague:
        return self.pyramid.premier

    @property
    def second_division(self) -> DivisionLeague:
        return self.pyramid.second

    def advance_month(self, month: int) -> list[MatchResult]:
        for roster in self.rosters.values():
            roster.advance_month(month)
        results = self.pyramid.advance_month(month)
        if month in self.international.round_months:
            self.current_squad = self.selector.select(
                month,
                self.state.clubs,
                self.rosters,
                set(self.pyramid.premier_ids),
            )
            self.squad_history.append(self.current_squad)
            institutional_strength = self.state.national_team_strength
            effective = _clamp(
                0.74 * self.current_squad.strength
                + 0.26 * institutional_strength,
                25.0,
                92.0,
            )
            self.current_effective_strength = effective
            self.state.national_team_strength = effective
            international_results = self.international.advance_month(month, self.state)
            post_match_effective = self.state.national_team_strength
            self.current_effective_strength = post_match_effective
            self.state.national_team_strength = _clamp(
                0.45 * institutional_strength + 0.55 * post_match_effective,
                20.0,
                95.0,
            )
            results += international_results
        self.monthly_events[month] = results
        return results

    @property
    def recent_results(self) -> list[MatchResult]:
        combined = self.pyramid.all_results + self.international.results
        return sorted(
            combined,
            key=lambda result: (
                result.month,
                result.competition,
                result.round_number,
            ),
        )[-16:]
