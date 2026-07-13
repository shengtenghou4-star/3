"""Continuous multi-term national football history with safe deterministic saves."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .advanced_ecosystem import (
    AdvancedClubWorld,
    ContinentalChampionsCup,
    DomesticCup,
)
from .campaign import PresidentialPlan, STRATEGIES, Strategy
from .deep_campaign import DeepCampaign
from .domain import NationalFootballSystem
from .ecosystem import ClubPyramid, NationalSquadSelector, OwnerProfile
from .engine import SimulationEngine
from .football import ClubRoster, InternationalQualifiers, Player
from .generational_economy import (
    AcademyIntakeRecord,
    AcademyLifecycleSystem,
    GenerationalEconomy,
    InsolvencyRecord,
    RetirementRecord,
    SponsorshipEvent,
    StadiumFinanceRecord,
)
from .governed_politics import GovernedPoliticalEconomy
from .ordered_contracts import OrderedContractMarket
from .policy_registration import StrictRegistrationSystem
from .policy_world import PolicyAwareGenerationalWorld
from .political_economy import StakeholderProfile
from .political_workload import PolicyWorkloadManager


SAVE_FORMAT_VERSION = 1
MAX_CONSECUTIVE_TERMS = 3


@dataclass(slots=True)
class PresidentProfile:
    id: str
    name: str
    strategy: Strategy
    coalition_skill: float
    administrative_skill: float
    integrity: float
    first_term: int
    terms_served: int = 1
    status: str = "incumbent"


@dataclass(frozen=True, slots=True)
class SeasonHistoryRecord:
    global_season: int
    term: int
    local_season: int
    president_name: str
    premier_champion: str
    cup_champion: str
    continental_best_stage: str
    national_team_position: int
    national_team_strength: float


@dataclass(frozen=True, slots=True)
class ClubHistoryRecord:
    global_month: int
    term: int
    club_id: str
    club_name: str
    division: int
    cash: float
    debt: float
    financial_health: float
    wage_arrears_months: int
    license_status: str
    owner_name: str
    stadium_capacity: int
    squad_value_proxy: float


@dataclass(frozen=True, slots=True)
class PlayerHistoryRecord:
    global_month: int
    term: int
    event: str
    player_id: str
    player_name: str
    club_id: str
    club_name: str
    age: int
    ability: float
    potential: float | None


@dataclass(frozen=True, slots=True)
class TermRecord:
    term: int
    start_year: int
    end_year: int
    president_id: str
    president_name: str
    strategy: str
    board_score: float
    board_verdict: str
    political_score: float
    political_verdict: str
    coalition_support: float
    governability: float
    decisions: tuple[str, ...]
    promises_kept: int
    promises_broken: int
    treasury_end: float
    fan_trust_end: float
    integrity_end: float
    national_team_strength_end: float
    successor_name: str
    succession_reason: str


@dataclass(slots=True)
class _ContinuityBundle:
    state: NationalFootballSystem
    rosters: dict[str, ClubRoster]
    premier_ids: list[str]
    second_ids: list[str]
    owners: dict[str, OwnerProfile]
    economy: GenerationalEconomy
    free_agents: list[Player]
    registration_policy: tuple[int, int, int, str]
    workload_policy: tuple[float, float, float]
    stakeholders: dict[str, StakeholderProfile]
    continental_qualifiers: list[str]


class EraAcademyLifecycleSystem(AcademyLifecycleSystem):
    """Generate globally unique academy cohorts after the first two seasons."""

    def __init__(self, season_offset: int, seed: int) -> None:
        super().__init__(seed=seed)
        self.season_offset = season_offset

    def _generate_graduate(
        self,
        season: int,
        index: int,
        club: Any,
        roster: ClubRoster,
        environment: float,
    ) -> Player:
        return super()._generate_graduate(
            self.season_offset + season,
            index,
            club,
            roster,
            environment,
        )


class LongTermCampaign:
    """A chain of two-year presidencies sharing one persistent football nation."""

    PRESIDENT_NAMES = (
        "周正衡",
        "林启明",
        "韩锐",
        "乔文策",
        "沈岚",
        "赵允成",
        "顾清河",
        "许知远",
        "任嘉树",
        "方砚秋",
        "江维新",
    )

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        if max_terms < 1:
            raise ValueError("max_terms must be positive")
        self.max_terms = max_terms
        self.initial_strategy = strategy
        self.term_index = 1
        self.global_month = 0
        self.term_records: list[TermRecord] = []
        self.season_history: list[SeasonHistoryRecord] = []
        self.club_history: list[ClubHistoryRecord] = []
        self.player_history: list[PlayerHistoryRecord] = []
        self.stadium_history: list[dict[str, Any]] = []
        self.sponsorship_history: list[dict[str, Any]] = []
        self.insolvency_history: list[dict[str, Any]] = []
        self.presidents: list[PresidentProfile] = [
            self._initial_president(strategy)
        ]
        self.current_president = self.presidents[0]
        self.current_campaign = DeepCampaign(strategy=strategy)
        self._enact_opening_plan(self.current_campaign, strategy)
        self._finalized_terms: set[int] = set()

    @property
    def local_month(self) -> int:
        return self.current_campaign.engine.state.month

    @property
    def current_decision(self):
        return self.current_campaign.current_decision

    @property
    def terms_completed(self) -> int:
        return len(self.term_records)

    @property
    def finished(self) -> bool:
        return self.terms_completed >= self.max_terms

    @property
    def global_year(self) -> int:
        return max(1, (self.global_month + 11) // 12)

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        while months > 0 and not self.finished:
            if interactive and self.current_campaign.pending_decisions:
                break
            before = self.local_month
            available = 24 - before
            if available <= 0:
                self._finalize_and_rollover()
                continue
            step = min(months, available)
            self.current_campaign.advance(step, interactive=interactive)
            elapsed = self.local_month - before
            self.global_month += elapsed
            months -= elapsed
            if interactive and self.current_campaign.pending_decisions:
                break
            if self.local_month == 24 and not self.current_campaign.pending_decisions:
                self._finalize_and_rollover()
            if elapsed == 0:
                break

    def resolve_decision(self, option_id: str):
        return self.current_campaign.resolve_decision(option_id)

    def finish_current_term(self) -> None:
        start_term = self.term_index
        while self.term_index == start_term and not self.finished:
            if self.current_decision is not None:
                decision = self.current_decision
                if decision.id.startswith("agenda_"):
                    option = self.current_campaign.politics.auto_choice(
                        decision.id,
                        self.current_president.strategy.value,
                    )
                else:
                    from .campaign import _AUTO_CHOICES

                    option = _AUTO_CHOICES[self.current_president.strategy][decision.id]
                self.resolve_decision(option)
            else:
                self.advance(24 - self.local_month, interactive=True)

    def run_terms(self, count: int) -> None:
        target = min(self.max_terms, self.terms_completed + count)
        while self.terms_completed < target:
            self.finish_current_term()

    def run_years(self, years: int) -> None:
        if years < 0:
            raise ValueError("years cannot be negative")
        target_month = min(self.max_terms * 24, self.global_month + years * 12)
        while self.global_month < target_month and not self.finished:
            remaining = target_month - self.global_month
            self.advance(remaining, interactive=False)

    def to_dict(self) -> dict[str, Any]:
        completed = [
            {
                "strategy": record.strategy,
                "choices": list(record.decisions),
            }
            for record in self.term_records
        ]
        current = {
            "strategy": self.current_president.strategy.value,
            "month": self.local_month,
            "choices": [
                record.option_id for record in self.current_campaign.decision_history
            ],
            "pending_decision": (
                self.current_decision.id if self.current_decision is not None else None
            ),
        }
        return {
            "format_version": SAVE_FORMAT_VERSION,
            "max_terms": self.max_terms,
            "initial_strategy": self.initial_strategy.value,
            "completed_terms": completed,
            "current_term": current,
            "fingerprint": self.fingerprint(),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            indent=indent,
        )

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.write_text(self.to_json(), encoding="utf-8")
        return target

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LongTermCampaign":
        if data.get("format_version") != SAVE_FORMAT_VERSION:
            raise ValueError("unsupported save format")
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        for command in data.get("completed_terms", []):
            campaign._replay_term(
                choices=list(command.get("choices", [])),
                target_month=24,
            )
        current = data.get("current_term", {})
        if not campaign.finished:
            expected_strategy = current.get(
                "strategy",
                campaign.current_president.strategy.value,
            )
            if campaign.current_president.strategy.value != expected_strategy:
                raise ValueError("save replay produced a different successor strategy")
            campaign._replay_term(
                choices=list(current.get("choices", [])),
                target_month=int(current.get("month", 0)),
            )
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("save replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "LongTermCampaign":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "LongTermCampaign":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        state = self.current_campaign.engine.state
        football = self.current_campaign.football
        payload = {
            "global_month": self.global_month,
            "term": self.term_index,
            "terms_completed": self.terms_completed,
            "president": asdict(self.current_president),
            "state": {
                "month": state.month,
                "treasury": round(state.treasury, 4),
                "political_capital": round(state.political_capital, 6),
                "fan_trust": round(state.fan_trust, 6),
                "integrity": round(state.integrity_reputation, 6),
                "league_health": round(state.league_financial_health, 6),
                "national_team": round(state.national_team_strength, 6),
            },
            "clubs": [
                (
                    club.id,
                    club.name,
                    round(club.cash, 3),
                    round(club.debt, 3),
                    round(club.monthly_revenue, 3),
                    round(club.monthly_wage_bill, 3),
                    club.wage_arrears_months,
                    club.license_status,
                )
                for club in sorted(state.clubs.values(), key=lambda item: item.id)
            ],
            "players": [
                (
                    club_id,
                    player.id,
                    player.age,
                    round(player.ability, 5),
                    round(player.potential, 5),
                    round(player.fitness, 5),
                    round(player.morale, 5),
                    player.contract_months,
                    player.appearances,
                    player.goals,
                    player.injury_months,
                )
                for club_id in sorted(football.rosters)
                for player in sorted(
                    football.rosters[club_id].players,
                    key=lambda item: item.id,
                )
            ],
            "free_agents": sorted(player.id for player in football.contracts.free_agents),
            "premier": tuple(football.pyramid.premier_ids),
            "second": tuple(football.pyramid.second_ids),
            "stakeholders": [
                (
                    actor.id,
                    round(actor.support, 6),
                    round(actor.trust, 6),
                    round(actor.patience, 6),
                    round(actor.mobilization, 6),
                    actor.promises_kept,
                    actor.promises_broken,
                )
                for actor in sorted(
                    self.current_campaign.politics.stakeholders.values(),
                    key=lambda item: item.id,
                )
            ],
            "pending": self.current_decision.id if self.current_decision else None,
            "seasons": [asdict(item) for item in self.season_history],
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _replay_term(self, *, choices: list[str], target_month: int) -> None:
        start_term = self.term_index
        index = 0
        while self.term_index == start_term and not self.finished:
            if self.current_decision is not None:
                if index >= len(choices):
                    break
                self.resolve_decision(choices[index])
                index += 1
                continue
            if self.local_month >= target_month:
                break
            self.advance(target_month - self.local_month, interactive=True)
        if target_month == 24 and self.term_index == start_term and not self.finished:
            if self.current_decision is not None:
                if index >= len(choices):
                    raise ValueError("completed term save omits a decision")
                while self.current_decision is not None and index < len(choices):
                    self.resolve_decision(choices[index])
                    index += 1
            if self.local_month < 24:
                self.advance(24 - self.local_month, interactive=True)
        if index != len(choices):
            raise ValueError("save contains decisions that were not reachable")

    def _finalize_and_rollover(self) -> None:
        if self.term_index in self._finalized_terms:
            if not self.finished:
                self._rollover(self._capture_continuity(), self.current_president)
            return
        campaign = self.current_campaign
        board = campaign.board_review()
        political = campaign.political_review
        next_president, reason = self._select_successor(board.score, political.score)
        self._record_term_histories(next_president, reason)
        self._finalized_terms.add(self.term_index)
        if self.terms_completed >= self.max_terms:
            return
        bundle = self._capture_continuity()
        self._rollover(bundle, next_president)

    def _record_term_histories(
        self,
        next_president: PresidentProfile,
        succession_reason: str,
    ) -> None:
        campaign = self.current_campaign
        state = campaign.engine.state
        board = campaign.board_review()
        political = campaign.political_review
        president = self.current_president
        choices = tuple(record.option_id for record in campaign.decision_history)
        self.term_records.append(
            TermRecord(
                term=self.term_index,
                start_year=(self.term_index - 1) * 2 + 1,
                end_year=self.term_index * 2,
                president_id=president.id,
                president_name=president.name,
                strategy=president.strategy.value,
                board_score=board.score,
                board_verdict=board.verdict,
                political_score=political.score,
                political_verdict=political.verdict,
                coalition_support=political.coalition_support,
                governability=political.governability,
                decisions=choices,
                promises_kept=political.promises_kept,
                promises_broken=political.promises_broken,
                treasury_end=state.treasury,
                fan_trust_end=state.fan_trust,
                integrity_end=state.integrity_reputation,
                national_team_strength_end=state.national_team_strength,
                successor_name=next_president.name,
                succession_reason=succession_reason,
            )
        )
        self._record_seasons()
        self._record_clubs()
        self._record_player_events()
        self._record_industry_events()

    def _record_seasons(self) -> None:
        campaign = self.current_campaign
        state = campaign.engine.state
        for local_season in (1, 2):
            global_season = (self.term_index - 1) * 2 + local_season
            champion_id = campaign.football.pyramid.champion_history.get(local_season)
            cup_id = campaign.football.domestic_cup.champions.get(local_season)
            continental = next(
                (
                    item
                    for item in campaign.football.continental_history
                    if item.season == local_season
                ),
                None,
            )
            if continental is None and campaign.football.continental.season == local_season:
                continental = campaign.football.continental.summary
            self.season_history.append(
                SeasonHistoryRecord(
                    global_season=global_season,
                    term=self.term_index,
                    local_season=local_season,
                    president_name=self.current_president.name,
                    premier_champion=(
                        state.clubs[champion_id].name
                        if champion_id in state.clubs
                        else "not recorded"
                    ),
                    cup_champion=(
                        state.clubs[cup_id].name
                        if cup_id in state.clubs
                        else "not completed"
                    ),
                    continental_best_stage=(
                        continental.domestic_best_stage
                        if continental is not None
                        else "not completed"
                    ),
                    national_team_position=campaign.football.international.user_position,
                    national_team_strength=state.national_team_strength,
                )
            )

    def _record_clubs(self) -> None:
        campaign = self.current_campaign
        state = campaign.engine.state
        premier = set(campaign.football.pyramid.premier_ids)
        for club_id, club in state.clubs.items():
            owner = campaign.football.pyramid.owners[club_id]
            stadium = campaign.football.economy.stadiums.profiles[club_id]
            self.club_history.append(
                ClubHistoryRecord(
                    global_month=self.global_month,
                    term=self.term_index,
                    club_id=club_id,
                    club_name=club.name,
                    division=1 if club_id in premier else 2,
                    cash=club.cash,
                    debt=club.debt,
                    financial_health=club.financial_health,
                    wage_arrears_months=club.wage_arrears_months,
                    license_status=club.license_status,
                    owner_name=owner.name,
                    stadium_capacity=stadium.capacity,
                    squad_value_proxy=sum(
                        player.ability * max(player.monthly_wage, 1.0)
                        for player in campaign.football.rosters[club_id].players
                    ),
                )
            )

    def _record_player_events(self) -> None:
        lifecycle = self.current_campaign.football.economy.lifecycle
        for item in lifecycle.intake_history:
            self.player_history.append(
                PlayerHistoryRecord(
                    global_month=(self.term_index - 1) * 24 + item.month,
                    term=self.term_index,
                    event="academy graduation",
                    player_id=item.player_id,
                    player_name=item.player_name,
                    club_id=item.club_id,
                    club_name=item.club_name,
                    age=item.age,
                    ability=item.ability,
                    potential=item.potential,
                )
            )
        for item in lifecycle.retirement_history:
            self.player_history.append(
                PlayerHistoryRecord(
                    global_month=(self.term_index - 1) * 24 + item.month,
                    term=self.term_index,
                    event="retirement",
                    player_id=item.player_id,
                    player_name=item.player_name,
                    club_id=item.club_id,
                    club_name=item.club_name,
                    age=item.age,
                    ability=item.ability,
                    potential=None,
                )
            )

    def _record_industry_events(self) -> None:
        economy = self.current_campaign.football.economy
        offset = (self.term_index - 1) * 24
        self.stadium_history.extend(
            {
                **asdict(item),
                "global_month": offset + item.month,
                "term": self.term_index,
            }
            for item in economy.stadiums.match_history
        )
        self.sponsorship_history.extend(
            {
                **asdict(item),
                "global_month": offset + item.month,
                "term": self.term_index,
            }
            for item in economy.sponsors.history
        )
        self.insolvency_history.extend(
            {
                **asdict(item),
                "global_month": offset + item.month,
                "term": self.term_index,
            }
            for item in economy.insolvency.history
        )

    def _capture_continuity(self) -> _ContinuityBundle:
        football = self.current_campaign.football
        registration = football.economy.registration
        workload = football.workload
        qualifiers = [
            row.team_id for row in football.pyramid.premier.sorted_table()[:2]
        ]
        return _ContinuityBundle(
            state=football.state,
            rosters=football.rosters,
            premier_ids=list(football.pyramid.premier_ids),
            second_ids=list(football.pyramid.second_ids),
            owners=football.pyramid.owners,
            economy=football.economy,
            free_agents=football.contracts.free_agents,
            registration_policy=(
                registration.squad_limit,
                registration.foreign_limit,
                registration.homegrown_minimum,
                registration.policy_name,
            ),
            workload_policy=(
                workload.congestion_multiplier,
                workload.international_release_cost,
                workload.injury_multiplier,
            ),
            stakeholders=self.current_campaign.politics.stakeholders,
            continental_qualifiers=qualifiers,
        )

    def _rollover(
        self,
        bundle: _ContinuityBundle,
        president: PresidentProfile,
    ) -> None:
        same_president = president.id == self.current_president.id
        self.term_index += 1
        self.current_president = president
        if not same_president:
            self.presidents.append(president)
        state = bundle.state
        state.month = 0
        transition_grant = self._transition_grant(state, bundle.stakeholders)
        state.treasury += transition_grant
        if same_president:
            state.political_capital = min(1.0, state.political_capital * 0.90 + 0.05)
        else:
            state.political_capital = min(
                1.0,
                0.42 + 0.20 * self._weighted_support(bundle.stakeholders),
            )
        campaign = DeepCampaign(
            engine=SimulationEngine(state),
            strategy=president.strategy,
        )
        campaign.football = self._build_continuity_world(bundle)
        campaign.politics = self._build_continuity_politics(
            bundle.stakeholders,
            same_president=same_president,
        )
        campaign.initial_youth_environment = state.youth_development_environment
        opening = campaign.dashboard()
        campaign.dashboards = [opening]
        campaign.monthly_history = [opening]
        campaign.engine.audit_log.append(
            f"M0: term {self.term_index} opened under {president.name}; "
            f"transition grant {transition_grant:.0f}"
        )
        self.current_campaign = campaign
        self._enact_opening_plan(campaign, president.strategy)

    def _build_continuity_world(
        self,
        bundle: _ContinuityBundle,
    ) -> PolicyAwareGenerationalWorld:
        seed = 3033 + self.term_index * 1000
        state = bundle.state
        rosters = bundle.rosters
        pyramid = ClubPyramid(state.clubs, rosters, seed=seed)
        pyramid.premier_ids = list(bundle.premier_ids)
        pyramid.second_ids = list(bundle.second_ids)
        pyramid.owners = bundle.owners
        pyramid.premier = pyramid._build_league(level=1, season=1)
        pyramid.second = pyramid._build_league(level=2, season=1)
        selector = NationalSquadSelector()
        squad = selector.select(0, state.clubs, rosters, set(pyramid.premier_ids))

        workload = PolicyWorkloadManager(seed=seed + 400)
        (
            workload.congestion_multiplier,
            workload.international_release_cost,
            workload.injury_multiplier,
        ) = bundle.workload_policy
        contracts = OrderedContractMarket(seed=seed + 500)
        contracts.free_agents = bundle.free_agents
        base = AdvancedClubWorld(
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
                bundle.continental_qualifiers,
                season=1,
                seed=seed + 300,
            ),
            workload=workload,
            contracts=contracts,
            squad_history=[squad],
            continental_history=[],
            monthly_events={},
            _next_continental_qualifiers=list(bundle.continental_qualifiers),
        )

        stadiums = deepcopy(bundle.economy.stadiums)
        stadiums.match_history = []
        stadiums.investment_history = []
        for club_id, profile in stadiums.profiles.items():
            profile.club_name = state.clubs[club_id].name
            if profile.expansion_completion_month is not None:
                profile.expansion_completion_month = max(
                    1,
                    profile.expansion_completion_month - 24,
                )
        sponsors = deepcopy(bundle.economy.sponsors)
        sponsors.history = []
        sponsors.seed = 5100 + self.term_index * 1000
        registration = StrictRegistrationSystem()
        (
            registration.squad_limit,
            registration.foreign_limit,
            registration.homegrown_minimum,
            registration.policy_name,
        ) = bundle.registration_policy
        lifecycle = EraAcademyLifecycleSystem(
            season_offset=(self.term_index - 1) * 2,
            seed=6100 + self.term_index * 1000,
        )
        insolvency = deepcopy(bundle.economy.insolvency)
        insolvency.history = []
        economy = GenerationalEconomy(
            stadiums=stadiums,
            sponsors=sponsors,
            registration=registration,
            lifecycle=lifecycle,
            insolvency=insolvency,
        )
        registration.register(0, state.clubs, rosters)
        return PolicyAwareGenerationalWorld(base=base, economy=economy)

    def _build_continuity_politics(
        self,
        previous: dict[str, StakeholderProfile],
        *,
        same_president: bool,
    ) -> GovernedPoliticalEconomy:
        politics = GovernedPoliticalEconomy()
        carry = 0.90 if same_president else 0.58
        for actor_id, actor in politics.stakeholders.items():
            old = previous[actor_id]
            actor.support = carry * old.support + (1.0 - carry) * 0.50
            actor.trust = (0.86 if same_president else 0.72) * old.trust + (
                0.14 if same_president else 0.28
            ) * 0.50
            actor.patience = 0.82 * old.patience + 0.18 * 0.55
            actor.mobilization = old.mobilization * (0.72 if same_president else 0.48)
            actor.promises_kept = old.promises_kept
            actor.promises_broken = old.promises_broken
            actor.memory = list(old.memory[-8:])
            actor.memory.append(
                f"Term {self.term_index}: "
                + ("incumbent renewed" if same_president else "new president inherited relationship")
            )
            actor.last_contact_month = 0
        return politics

    def _select_successor(
        self,
        board_score: float,
        political_score: float,
    ) -> tuple[PresidentProfile, str]:
        incumbent = self.current_president
        eligible = incumbent.terms_served < MAX_CONSECUTIVE_TERMS
        clear_renewal = political_score >= 61.0 and board_score >= 48.0
        constrained_renewal = (
            political_score >= 53.0
            and board_score >= 57.0
            and self.current_campaign.politics.coalition_support >= 0.50
        )
        if eligible and (clear_renewal or constrained_renewal):
            incumbent.terms_served += 1
            reason = (
                "incumbent renewed by governing coalition"
                if clear_renewal
                else "incumbent survived a contested convention"
            )
            return incumbent, reason
        incumbent.status = "left office"
        if not eligible:
            reason = "constitutional consecutive-term limit"
        elif political_score < 53.0:
            reason = "coalition collapse triggered succession"
        else:
            reason = "football board withdrew confidence"
        return self._generate_successor(reason), reason

    def _generate_successor(self, reason: str) -> PresidentProfile:
        index = min(self.term_index, len(self.PRESIDENT_NAMES) - 1)
        state = self.current_campaign.engine.state
        if state.youth_development_environment < 50.0:
            strategy = Strategy.FOUNDATIONS
        elif state.national_team_strength < 49.0 and state.fan_trust < 0.46:
            strategy = Strategy.QUICK_RESULTS
        else:
            strategy = Strategy.BALANCED
        identifier = f"president-{self.term_index + 1}-{strategy.value}"
        return PresidentProfile(
            id=identifier,
            name=self.PRESIDENT_NAMES[index],
            strategy=strategy,
            coalition_skill=0.55 + 0.03 * ((index + 1) % 4),
            administrative_skill=0.54 + 0.025 * ((index + 2) % 5),
            integrity=0.58 + 0.03 * (index % 4),
            first_term=self.term_index + 1,
            terms_served=1,
            status="incumbent",
        )

    def _initial_president(self, strategy: Strategy) -> PresidentProfile:
        name = {
            Strategy.FOUNDATIONS: "林启明",
            Strategy.BALANCED: "周正衡",
            Strategy.QUICK_RESULTS: "韩锐",
        }[strategy]
        return PresidentProfile(
            id=f"founder-{strategy.value}",
            name=name,
            strategy=strategy,
            coalition_skill=0.62,
            administrative_skill=0.64,
            integrity=0.66 if strategy != Strategy.QUICK_RESULTS else 0.53,
            first_term=1,
        )

    def _transition_grant(
        self,
        state: NationalFootballSystem,
        stakeholders: dict[str, StakeholderProfile],
    ) -> float:
        return (
            18_000_000.0
            + 8_000_000.0 * self._weighted_support(stakeholders)
            + 5_000_000.0 * state.integrity_reputation
            + 4_000_000.0 * state.league_financial_health
            + max(0.0, state.national_team_strength - 45.0) * 180_000.0
        )

    @staticmethod
    def _weighted_support(stakeholders: dict[str, StakeholderProfile]) -> float:
        total = sum(actor.power for actor in stakeholders.values())
        return sum(actor.power * actor.support for actor in stakeholders.values()) / max(total, 1e-9)

    @staticmethod
    def _affordable_plan(
        plan: PresidentialPlan,
        treasury: float,
    ) -> PresidentialPlan:
        scale = min(1.0, treasury / max(plan.total_budget, 1.0))
        return PresidentialPlan(
            coach_budget=plan.coach_budget * scale,
            match_budget=plan.match_budget * scale,
            school_cofunding=plan.school_cofunding * scale,
            licensing_strictness=plan.licensing_strictness,
            audit_budget=plan.audit_budget * scale,
            senior_team_budget=plan.senior_team_budget * scale,
        )

    def _enact_opening_plan(
        self,
        campaign: DeepCampaign,
        strategy: Strategy,
    ) -> None:
        plan = self._affordable_plan(
            STRATEGIES[strategy],
            campaign.engine.state.treasury,
        )
        campaign.enact_plan(plan)
