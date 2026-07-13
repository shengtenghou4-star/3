"""Multi-round nominations, coalition bargains and fragile governments.

The constitutional layer can remove a president mid-term. This module makes the
replacement contest playable: candidates need weighted stakeholder support, may
trade offices, policy promises and budget concessions, and must later live with
the resulting coalition agreement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy, _AUTO_CHOICES
from .constitutional import ConstitutionalEvent, ConstitutionalLongTermCampaign, _clamp
from .governance import DecisionOption, DecisionRecord, GovernanceDecision
from .long_term import PresidentProfile
from .scenario_history import ReplayableConstitutionalHistory


COALITION_SAVE_VERSION = 4


@dataclass(frozen=True, slots=True)
class ElectionCandidate:
    id: str
    name: str
    strategy: Strategy
    sponsor_bloc: str
    coalition_skill: float
    administrative_skill: float
    integrity: float
    charisma: float
    platform: dict[str, float]


@dataclass(frozen=True, slots=True)
class BlocVote:
    actor_id: str
    actor_name: str
    candidate_id: str | None
    candidate_name: str
    score: float
    weight: float
    reason: str


@dataclass(frozen=True, slots=True)
class ElectionRoundRecord:
    election_id: str
    global_month: int
    term: int
    round_number: int
    trigger: str
    selected_candidate_id: str
    selected_package: str
    shares: tuple[tuple[str, float], ...]
    votes: tuple[BlocVote, ...]
    eliminated_candidate_id: str | None
    winner_candidate_id: str | None
    minority_government: bool


@dataclass(slots=True)
class CoalitionCommitment:
    id: str
    actor_id: str
    actor_name: str
    commitment_type: str
    title: str
    office: str | None
    metric: str | None
    baseline: float | None
    target: float | None
    cost: float
    created_global_month: int
    due_global_month: int
    status: str = "pending"
    resolved_global_month: int | None = None


@dataclass(slots=True)
class GovernmentAgreement:
    id: str
    president_id: str
    president_name: str
    trigger: str
    start_global_month: int
    majority_share: float
    coalition_blocs: tuple[str, ...]
    commitments: list[CoalitionCommitment]
    overpromise_index: float
    stability: float
    status: str = "active"
    crises: int = 0


@dataclass(frozen=True, slots=True)
class CoalitionCrisisRecord:
    global_month: int
    term: int
    president_name: str
    agreement_id: str
    stability_before: float
    option_id: str
    outcome: str


@dataclass(slots=True)
class ElectionConvention:
    id: str
    trigger: str
    started_global_month: int
    candidates: dict[str, ElectionCandidate]
    active_candidate_ids: list[str]
    round_number: int = 1
    selected_candidate_id: str | None = None
    previous_shares: dict[str, float] = field(default_factory=dict)
    accumulated_commitments: dict[str, list[CoalitionCommitment]] = field(
        default_factory=dict
    )


class CoalitionElectionHistory(ReplayableConstitutionalHistory):
    """Constitutional history with playable nomination and coalition formation."""

    OFFICE_BY_BLOC = {
        "sports_ministry": "国家队技术总监",
        "finance_ministry": "财务与准入总监",
        "education_ministry": "青训与校园足球专员",
        "provincial_fas": "秘书长",
        "club_owners": "国家队技术总监",
        "players_union": "青训与校园足球专员",
        "broadcaster": "秘书长",
        "sponsor_council": "廉洁与纪律专员",
        "supporters_federation": "廉洁与纪律专员",
    }
    PLATFORM = {
        Strategy.FOUNDATIONS: {
            "integrity": 0.90,
            "grassroots": 1.00,
            "market": -0.35,
            "fiscal": -0.05,
            "labor": 0.45,
            "local_autonomy": 0.15,
            "national_team": 0.20,
            "competitive_balance": 0.65,
        },
        Strategy.BALANCED: {
            "integrity": 0.35,
            "grassroots": 0.35,
            "market": 0.35,
            "fiscal": 0.55,
            "labor": 0.20,
            "local_autonomy": 0.25,
            "national_team": 0.45,
            "competitive_balance": 0.30,
        },
        Strategy.QUICK_RESULTS: {
            "integrity": -0.25,
            "grassroots": -0.35,
            "market": 1.00,
            "fiscal": -0.25,
            "labor": -0.45,
            "local_autonomy": 0.50,
            "national_team": 1.00,
            "competitive_balance": -0.55,
        },
    }
    SPONSOR_BY_STRATEGY = {
        Strategy.FOUNDATIONS: "education_ministry",
        Strategy.BALANCED: "sports_ministry",
        Strategy.QUICK_RESULTS: "club_owners",
    }

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        super().__init__(strategy=strategy, max_terms=max_terms)
        self.election_history: list[ElectionRoundRecord] = []
        self.government_agreements: list[GovernmentAgreement] = []
        self.coalition_crises: list[CoalitionCrisisRecord] = []
        self._pending_election: list[GovernanceDecision] = []
        self._pending_coalition: list[GovernanceDecision] = []
        self._election: ElectionConvention | None = None
        self._active_agreement: GovernmentAgreement | None = None
        self._scheduled_agreement: GovernmentAgreement | None = None
        self._fracture_checked: set[str] = set()

    @property
    def current_decision(self):
        if self._pending_election:
            return self._pending_election[0]
        if self._pending_coalition:
            return self._pending_coalition[0]
        return super().current_decision

    @property
    def election_active(self) -> bool:
        return self._election is not None

    @property
    def active_agreement(self) -> GovernmentAgreement | None:
        return self._active_agreement

    @property
    def coalition_stability(self) -> float:
        agreement = self._active_agreement
        if agreement is None:
            return self.current_campaign.politics.coalition_support
        return self._calculate_agreement_stability(agreement)

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        remaining = months
        while remaining > 0 and not self.finished:
            if self.current_decision is not None:
                if interactive:
                    break
                self._auto_resolve_current()
                continue
            if (
                self.caretaker_active
                and self._caretaker_until is not None
                and self.global_month >= self._caretaker_until
                and not self.election_active
            ):
                self._hold_snap_election()
                if self.current_decision is not None:
                    if interactive:
                        break
                    self._auto_resolve_current()
                    continue
            before = self.global_month
            super().advance(1, interactive=True)
            elapsed = self.global_month - before
            if elapsed == 0:
                if self.current_decision is not None and not interactive:
                    self._auto_resolve_current()
                    continue
                break
            remaining -= elapsed
            self._settle_coalition_commitments()
            self._maybe_trigger_coalition_breakdown()
            if interactive and self.current_decision is not None:
                break

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no pending decision")
        if self._pending_election and decision.id == self._pending_election[0].id:
            record = self._resolve_election_decision(decision, option_id)
            self._append_decision_command(decision.id, option_id)
            return record
        if self._pending_coalition and decision.id == self._pending_coalition[0].id:
            record = self._resolve_coalition_crisis(decision, option_id)
            self._append_decision_command(decision.id, option_id)
            return record
        return super().resolve_decision(option_id)

    def _append_decision_command(self, decision_id: str, option_id: str) -> None:
        self._decision_log.append(
            {
                "global_month": self.global_month,
                "term": self.term_index,
                "decision_id": decision_id,
                "option_id": option_id,
            }
        )

    def _auto_resolve_current(self) -> None:
        decision = self.current_decision
        if decision is None:
            return
        if decision.id.startswith("election_nomination_"):
            candidate = self._preferred_candidate()
            self.resolve_decision(f"nominate::{candidate.id}")
            return
        if decision.id.startswith("election_bargain_"):
            package = "coalition" if self._election and self._election.round_number == 1 else "grand"
            self.resolve_decision(f"package::{package}")
            return
        if decision.id.startswith("coalition_breakdown_"):
            agreement = self._active_agreement
            if agreement and agreement.stability >= 0.30:
                self.resolve_decision("renegotiate_compact")
            else:
                self.resolve_decision("confidence_vote")
            return
        super()._auto_resolve_current()

    def _hold_snap_election(self) -> None:
        if not self.caretaker_active or self.election_active:
            return
        self._begin_election("snap election after caretaker government")

    def _begin_election(self, trigger: str) -> None:
        election_id = f"election-{self.term_index}-{self.global_month}-{len(self.election_history)}"
        candidates = self._generate_candidates(election_id)
        self._election = ElectionConvention(
            id=election_id,
            trigger=trigger,
            started_global_month=self.global_month,
            candidates={item.id: item for item in candidates},
            active_candidate_ids=[item.id for item in candidates],
            accumulated_commitments={item.id: [] for item in candidates},
        )
        self._queue_nomination_decision()
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "election convention opened",
                "三路线候选人进入提前主席选举",
                0.55,
                tuple(
                    f"{item.name}由{self.current_campaign.politics.stakeholders[item.sponsor_bloc].name}率先提名"
                    for item in candidates
                ),
            )
        )

    def _generate_candidates(self, election_id: str) -> tuple[ElectionCandidate, ...]:
        candidates: list[ElectionCandidate] = []
        used_names = {item.name.replace("（看守）", "") for item in self.presidents}
        base_index = self.global_month + self.term_index + len(self.election_history)
        for offset, strategy in enumerate(
            (Strategy.FOUNDATIONS, Strategy.BALANCED, Strategy.QUICK_RESULTS)
        ):
            index = (base_index + offset * 3) % len(self.PRESIDENT_NAMES)
            for shift in range(len(self.PRESIDENT_NAMES)):
                name = self.PRESIDENT_NAMES[(index + shift) % len(self.PRESIDENT_NAMES)]
                if name not in used_names:
                    break
            used_names.add(name)
            candidates.append(
                ElectionCandidate(
                    id=f"{election_id}-{strategy.value}",
                    name=name,
                    strategy=strategy,
                    sponsor_bloc=self.SPONSOR_BY_STRATEGY[strategy],
                    coalition_skill=0.58 + 0.025 * ((index + offset) % 5),
                    administrative_skill=0.55 + 0.025 * ((index + 2 * offset) % 5),
                    integrity=(
                        0.78
                        if strategy == Strategy.FOUNDATIONS
                        else 0.65
                        if strategy == Strategy.BALANCED
                        else 0.51
                    ),
                    charisma=0.56 + 0.03 * ((index + 1) % 5),
                    platform=dict(self.PLATFORM[strategy]),
                )
            )
        return tuple(candidates)

    def _queue_nomination_decision(self) -> None:
        election = self._require_election()
        options = tuple(
            DecisionOption(
                f"nominate::{candidate.id}",
                f"支持{candidate.name} · {candidate.strategy.value}",
                self._candidate_summary(candidate),
                "若候选人首轮出局，必须转而背书其他路线",
            )
            for candidate_id in election.active_candidate_ids
            for candidate in (election.candidates[candidate_id],)
        )
        self._pending_election.append(
            GovernanceDecision(
                id=f"election_nomination_{election.id}_{election.round_number}",
                month=self.local_month,
                title=f"主席选举第{election.round_number}轮：选择主推候选人",
                narrative=(
                    "九个集团将按权力加权投票。你可以主推一名候选人，但仍需在下一步决定"
                    "以廉洁授权、有限交易还是大联合协议争取多数。"
                ),
                options=options,
            )
        )

    def _candidate_summary(self, candidate: ElectionCandidate) -> str:
        sponsor = self.current_campaign.politics.stakeholders[candidate.sponsor_bloc]
        return (
            f"首倡集团：{sponsor.name}；联盟能力{candidate.coalition_skill:.0%}，"
            f"行政能力{candidate.administrative_skill:.0%}，廉洁{candidate.integrity:.0%}。"
        )

    def _queue_bargain_decision(self) -> None:
        election = self._require_election()
        candidate = election.candidates[election.selected_candidate_id or ""]
        round_number = election.round_number
        self._pending_election.append(
            GovernanceDecision(
                id=f"election_bargain_{election.id}_{round_number}_{candidate.id}",
                month=self.local_month,
                title=f"第{round_number}轮组阁：为{candidate.name}选择谈判强度",
                narrative=(
                    "清洁授权不交换职位；有限联盟向两个摇摆集团作出承诺；大联合可争取四个集团，"
                    "但将制造预算、职位和政策债务。所有承诺都会在上台后验收。"
                ),
                options=(
                    DecisionOption(
                        "package::clean",
                        "坚持清洁授权",
                        "只依靠路线、能力和公信力争取支持，不定向许诺职位或预算。",
                        "可能无法跨过多数门槛",
                    ),
                    DecisionOption(
                        "package::coalition",
                        "有限联盟协议",
                        "向两个关键摇摆集团提供一项职位或政策承诺。",
                        "联盟伙伴将在六个月内验收承诺",
                    ),
                    DecisionOption(
                        "package::grand",
                        "大联合组阁交易",
                        "向四个集团提供职位、专项预算和政策保证，最大化当轮票数。",
                        "国库压力、寻租风险和未来违约成本显著上升",
                    ),
                ),
            )
        )

    def _resolve_election_decision(
        self,
        decision: GovernanceDecision,
        option_id: str,
    ) -> DecisionRecord:
        election = self._require_election()
        if decision.id.startswith("election_nomination_"):
            prefix = "nominate::"
            if not option_id.startswith(prefix):
                raise ValueError(f"unknown election option {option_id!r}")
            candidate_id = option_id[len(prefix) :]
            if candidate_id not in election.active_candidate_ids:
                raise ValueError("candidate is not active in this round")
            election.selected_candidate_id = candidate_id
            self._pending_election.pop(0)
            self._queue_bargain_decision()
            candidate = election.candidates[candidate_id]
            return DecisionRecord(
                decision_id=decision.id,
                month=self.local_month,
                title=decision.title,
                option_id=option_id,
                option_title=f"主推{candidate.name}",
                effects=(f"{candidate.name}成为本轮主推候选人。",),
            )

        if not option_id.startswith("package::"):
            raise ValueError(f"unknown election option {option_id!r}")
        package = option_id.split("::", 1)[1]
        if package not in {"clean", "coalition", "grand"}:
            raise ValueError(f"unknown coalition package {package!r}")
        selected_id = election.selected_candidate_id
        if selected_id is None:
            raise RuntimeError("bargaining began without a selected candidate")
        self._pending_election.pop(0)
        record = self._conduct_election_round(election, selected_id, package)
        winner_id = record.winner_candidate_id
        if winner_id is not None:
            agreement = self._agreement_from_winner(election, record)
            winner = election.candidates[winner_id]
            self._install_snap_winner(winner, agreement)
            self._election = None
            effects = (
                f"{winner.name}以{record.shares_dict[winner_id]:.1%}加权票组成政府。"
                if isinstance(record, _RoundOutcome)
                else f"{winner.name}完成组阁。"
            )
        else:
            if record.eliminated_candidate_id:
                election.active_candidate_ids.remove(record.eliminated_candidate_id)
            election.round_number += 1
            election.selected_candidate_id = None
            self._queue_nomination_decision()
            effects = (
                f"本轮无人过半；{election.candidates[record.eliminated_candidate_id].name}出局。"
                if record.eliminated_candidate_id
                else "本轮无人过半，谈判进入下一轮。"
            )
        return DecisionRecord(
            decision_id=decision.id,
            month=self.local_month,
            title=decision.title,
            option_id=option_id,
            option_title={
                "clean": "清洁授权",
                "coalition": "有限联盟协议",
                "grand": "大联合组阁交易",
            }[package],
            effects=effects,
        )

    def _conduct_election_round(
        self,
        election: ElectionConvention,
        selected_id: str,
        selected_package: str,
    ) -> "_RoundOutcome":
        packages: dict[str, str] = {}
        for candidate_id in election.active_candidate_ids:
            if candidate_id == selected_id:
                packages[candidate_id] = selected_package
            elif election.round_number == 1:
                packages[candidate_id] = (
                    "clean"
                    if election.candidates[candidate_id].strategy == Strategy.FOUNDATIONS
                    else "coalition"
                )
            else:
                packages[candidate_id] = "grand"

        targeted: dict[str, set[str]] = {}
        for candidate_id, package in packages.items():
            commitments = self._build_commitments(
                election.candidates[candidate_id],
                package,
                election.round_number,
            )
            election.accumulated_commitments[candidate_id].extend(commitments)
            targeted[candidate_id] = {item.actor_id for item in commitments}

        votes: list[BlocVote] = []
        weighted = {candidate_id: 0.0 for candidate_id in election.active_candidate_ids}
        total_power = sum(
            actor.power
            for actor in self.current_campaign.politics.stakeholders.values()
        )
        for actor in self.current_campaign.politics.stakeholders.values():
            scored: list[tuple[float, str, str]] = []
            for candidate_id in election.active_candidate_ids:
                candidate = election.candidates[candidate_id]
                package = packages[candidate_id]
                compatibility = actor.compatibility(candidate.platform)
                target_bonus = (
                    0.18
                    if package == "coalition" and actor.id in targeted[candidate_id]
                    else 0.29
                    if package == "grand" and actor.id in targeted[candidate_id]
                    else 0.0
                )
                sponsor_bonus = 0.12 if actor.id == candidate.sponsor_bloc else 0.0
                momentum = 0.10 * election.previous_shares.get(candidate_id, 0.0)
                overpromise_penalty = 0.07 if package == "grand" else 0.025 if package == "coalition" else 0.0
                integrity_fit = (
                    candidate.integrity
                    if actor.preferences.get("integrity", 0.0) >= 0
                    else 1.0 - candidate.integrity
                )
                score = (
                    0.24
                    + 0.20 * candidate.coalition_skill
                    + 0.10 * candidate.charisma
                    + 0.08 * actor.trust
                    + 0.06 * actor.support
                    + 0.18 * compatibility
                    + 0.08 * integrity_fit
                    + target_bonus
                    + sponsor_bonus
                    + momentum
                    - overpromise_penalty
                    - 0.018 * actor.promises_broken
                )
                reason = (
                    f"路线兼容{compatibility:+.2f}，"
                    f"{'获得定向承诺' if actor.id in targeted[candidate_id] else '无定向承诺'}"
                )
                scored.append((score, candidate_id, reason))
            score, candidate_id, reason = max(scored, key=lambda item: item[0])
            if score < 0.53:
                votes.append(
                    BlocVote(
                        actor.id,
                        actor.name,
                        None,
                        "弃权",
                        score,
                        actor.power,
                        "所有方案均未达到最低可信度",
                    )
                )
                continue
            candidate = election.candidates[candidate_id]
            weighted[candidate_id] += actor.power
            votes.append(
                BlocVote(
                    actor.id,
                    actor.name,
                    candidate_id,
                    candidate.name,
                    score,
                    actor.power,
                    reason,
                )
            )

        shares = {
            candidate_id: weighted[candidate_id] / max(total_power, 1e-9)
            for candidate_id in election.active_candidate_ids
        }
        election.previous_shares = dict(shares)
        ranked = sorted(shares, key=lambda item: shares[item], reverse=True)
        top_id = ranked[0]
        winner_id: str | None = top_id if shares[top_id] > 0.50 else None
        minority = False
        eliminated: str | None = None
        if winner_id is None and election.round_number >= 3:
            winner_id = top_id
            minority = True
        elif winner_id is None and len(ranked) > 2:
            eliminated = ranked[-1]

        public_record = ElectionRoundRecord(
            election.id,
            self.global_month,
            self.term_index,
            election.round_number,
            election.trigger,
            selected_id,
            selected_package,
            tuple(sorted(shares.items())),
            tuple(votes),
            eliminated,
            winner_id,
            minority,
        )
        self.election_history.append(public_record)
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "election round",
                f"{election.id}第{election.round_number}轮完成",
                0.35 + 0.10 * election.round_number,
                tuple(
                    f"{election.candidates[candidate_id].name}: {share:.1%}"
                    for candidate_id, share in sorted(
                        shares.items(), key=lambda item: item[1], reverse=True
                    )
                ),
            )
        )
        return _RoundOutcome(public_record, shares)

    def _build_commitments(
        self,
        candidate: ElectionCandidate,
        package: str,
        round_number: int,
    ) -> list[CoalitionCommitment]:
        if package == "clean":
            return []
        actors = self.current_campaign.politics.stakeholders
        ranked = sorted(
            actors.values(),
            key=lambda actor: (
                actor.power
                * (0.72 - actor.support)
                * (1.10 - max(-0.5, actor.compatibility(candidate.platform)))
            ),
            reverse=True,
        )
        count = 2 if package == "coalition" else 4
        selected = ranked[:count]
        commitments: list[CoalitionCommitment] = []
        kinds = (
            ("office", "policy")
            if package == "coalition"
            else ("office", "budget", "policy", "budget")
        )
        for index, actor in enumerate(selected):
            kind = kinds[index]
            office = self.OFFICE_BY_BLOC[actor.id] if kind == "office" else None
            metric, baseline, target = self._commitment_metric(actor.id, kind)
            cost = (
                0.0
                if kind == "office"
                else 550_000.0
                if kind == "policy"
                else 950_000.0
            )
            commitments.append(
                CoalitionCommitment(
                    id=(
                        f"commit-{candidate.id}-{round_number}-{actor.id}-{kind}-"
                        f"{len(self.election_history)}"
                    ),
                    actor_id=actor.id,
                    actor_name=actor.name,
                    commitment_type=kind,
                    title=self._commitment_title(actor.id, kind, office),
                    office=office,
                    metric=metric,
                    baseline=baseline,
                    target=target,
                    cost=cost,
                    created_global_month=self.global_month,
                    due_global_month=self.global_month + (1 if kind in {"office", "budget"} else 6),
                )
            )
        return commitments

    def _commitment_title(self, actor_id: str, kind: str, office: str | None) -> str:
        if kind == "office":
            return f"向{self.current_campaign.politics.stakeholders[actor_id].name}开放{office}提名权"
        if kind == "budget":
            return {
                "sports_ministry": "国家队备战专项预算",
                "finance_ministry": "俱乐部财务整顿基金",
                "education_ministry": "校园足球联合专项",
                "provincial_fas": "地方执行配套资金",
                "club_owners": "职业联赛商业开发基金",
                "players_union": "球员医疗和休息补偿基金",
                "broadcaster": "数字转播基础设施补贴",
                "sponsor_council": "品牌廉洁认证计划",
                "supporters_federation": "社区球迷与票价保障基金",
            }[actor_id]
        return {
            "sports_ministry": "六个月内提升国家队竞争力",
            "finance_ministry": "六个月内改善联赛财务健康",
            "education_ministry": "六个月内改善青训环境",
            "provincial_fas": "六个月内提升地方执行能力",
            "club_owners": "六个月内改善职业俱乐部健康度",
            "players_union": "六个月内降低赛程伤病负荷",
            "broadcaster": "六个月内提高职业联赛商业收入",
            "sponsor_council": "六个月内提高廉洁声誉",
            "supporters_federation": "六个月内提高球迷信任",
        }[actor_id]

    def _commitment_metric(
        self,
        actor_id: str,
        kind: str,
    ) -> tuple[str | None, float | None, float | None]:
        if kind in {"office", "budget"}:
            return None, None, None
        metric = {
            "sports_ministry": "national_team",
            "finance_ministry": "league_health",
            "education_ministry": "youth_environment",
            "provincial_fas": "regional_execution",
            "club_owners": "solvent_clubs",
            "players_union": "injury_policy",
            "broadcaster": "club_revenue",
            "sponsor_council": "integrity",
            "supporters_federation": "fan_trust",
        }[actor_id]
        baseline = self._metric_value(metric)
        increment = {
            "national_team": 0.45,
            "league_health": 0.012,
            "youth_environment": 0.010,
            "regional_execution": 0.010,
            "solvent_clubs": 0.012,
            "injury_policy": 0.025,
            "club_revenue": 55_000.0,
            "integrity": 0.015,
            "fan_trust": 0.018,
        }[metric]
        return metric, baseline, baseline + increment

    def _metric_value(self, metric: str) -> float:
        state = self.current_campaign.engine.state
        if metric == "national_team":
            return state.national_team_strength
        if metric == "league_health":
            return state.league_financial_health
        if metric == "youth_environment":
            return state.youth_development_environment
        if metric == "regional_execution":
            return sum(item.execution_capacity for item in state.regions.values()) / max(1, len(state.regions))
        if metric == "solvent_clubs":
            return state.solvent_club_share
        if metric == "injury_policy":
            return 1.0 - self.current_campaign.football.workload.injury_multiplier
        if metric == "club_revenue":
            return sum(item.monthly_revenue for item in state.clubs.values())
        if metric == "integrity":
            return state.integrity_reputation
        if metric == "fan_trust":
            return state.fan_trust
        raise ValueError(f"unknown coalition metric {metric}")

    def _agreement_from_winner(
        self,
        election: ElectionConvention,
        outcome: "_RoundOutcome",
    ) -> GovernmentAgreement:
        winner_id = outcome.record.winner_candidate_id
        if winner_id is None:
            raise RuntimeError("cannot form agreement without a winner")
        winner = election.candidates[winner_id]
        votes = [
            item.actor_id
            for item in outcome.record.votes
            if item.candidate_id == winner_id
        ]
        commitments = self._deduplicate_commitments(
            election.accumulated_commitments[winner_id]
        )
        overpromise = _clamp(
            0.08 * sum(item.commitment_type == "office" for item in commitments)
            + 0.10 * sum(item.commitment_type == "budget" for item in commitments)
            + 0.06 * sum(item.commitment_type == "policy" for item in commitments)
        )
        return GovernmentAgreement(
            id=f"agreement-{election.id}-{winner_id}",
            president_id=winner_id,
            president_name=winner.name,
            trigger=election.trigger,
            start_global_month=self.global_month,
            majority_share=outcome.shares_dict[winner_id],
            coalition_blocs=tuple(votes),
            commitments=commitments,
            overpromise_index=overpromise,
            stability=0.0,
            status="minority" if outcome.record.minority_government else "active",
        )

    def _deduplicate_commitments(
        self,
        commitments: list[CoalitionCommitment],
    ) -> list[CoalitionCommitment]:
        selected: dict[tuple[str, str], CoalitionCommitment] = {}
        for item in commitments:
            key = (item.actor_id, item.commitment_type)
            if key not in selected or item.cost > selected[key].cost:
                selected[key] = item
        return list(selected.values())

    def _install_snap_winner(
        self,
        candidate: ElectionCandidate,
        agreement: GovernmentAgreement,
    ) -> None:
        self._close_administration("coalition convention completed", "caretaker ended")
        caretaker = self.current_president
        caretaker.status = "left office"
        successor = self._candidate_to_president(candidate, "snap")
        self.presidents.append(successor)
        self.current_president = successor
        self.current_campaign.strategy = successor.strategy
        state = self.current_campaign.engine.state
        state.political_capital = _clamp(
            0.24 + 0.34 * agreement.majority_share - 0.12 * agreement.overpromise_index
        )
        self._caretaker_until = None
        self._constitutional_strikes = 0
        self.cabinet = {}
        self._appoint_full_cabinet("coalition-election mandate")
        self._activate_agreement(agreement)
        self._start_administration("coalition-election victory")
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "coalition government formed",
                f"{successor.name}完成多轮组阁并出任主席",
                0.48 + 0.20 * agreement.overpromise_index,
                (
                    f"加权支持率{agreement.majority_share:.1%}。",
                    f"执政联盟包含{len(agreement.coalition_blocs)}个集团。",
                    f"政府承担{len(agreement.commitments)}项组阁承诺。",
                ),
            )
        )

    def _candidate_to_president(
        self,
        candidate: ElectionCandidate,
        prefix: str,
    ) -> PresidentProfile:
        return PresidentProfile(
            id=f"{prefix}-{self.term_index}-{self.global_month}-{candidate.strategy.value}",
            name=candidate.name,
            strategy=candidate.strategy,
            coalition_skill=candidate.coalition_skill,
            administrative_skill=candidate.administrative_skill,
            integrity=candidate.integrity,
            first_term=self.term_index,
            terms_served=1,
            status="incumbent",
        )

    def _activate_agreement(self, agreement: GovernmentAgreement) -> None:
        self._active_agreement = agreement
        self.government_agreements.append(agreement)
        for commitment in agreement.commitments:
            self._apply_commitment(commitment)
        self._refresh_blocs_after_election(agreement)
        agreement.stability = self._calculate_agreement_stability(agreement)

    def _apply_commitment(self, commitment: CoalitionCommitment) -> None:
        actor = self.current_campaign.politics.stakeholders[commitment.actor_id]
        if commitment.commitment_type == "office":
            if commitment.office is None:
                raise RuntimeError("office commitment omitted the office")
            style = (
                "technocrat"
                if commitment.actor_id in {"finance_ministry", "sponsor_council", "supporters_federation"}
                else "broker"
            )
            self._replace_official(
                commitment.office,
                style,
                f"coalition allocation to {actor.name}",
            )
            commitment.status = "kept"
            commitment.resolved_global_month = self.global_month
            actor.promises_kept += 1
            return
        if commitment.commitment_type == "budget":
            state = self.current_campaign.engine.state
            if state.treasury < commitment.cost:
                return
            state.treasury -= commitment.cost
            self._apply_budget_benefit(commitment.actor_id)
            commitment.status = "kept"
            commitment.resolved_global_month = self.global_month
            actor.promises_kept += 1

    def _apply_budget_benefit(self, actor_id: str) -> None:
        state = self.current_campaign.engine.state
        if actor_id == "sports_ministry":
            state.national_team_strength = min(100.0, state.national_team_strength + 0.35)
        elif actor_id == "finance_ministry":
            state.league_financial_health = _clamp(state.league_financial_health + 0.008)
        elif actor_id == "education_ministry":
            state.youth_development_environment = _clamp(state.youth_development_environment + 0.007)
        elif actor_id == "provincial_fas":
            for region in state.regions.values():
                region.execution_capacity = _clamp(region.execution_capacity + 0.006)
        elif actor_id == "club_owners":
            for club in state.clubs.values():
                club.cash += 40_000.0
        elif actor_id == "players_union":
            workload = self.current_campaign.football.workload
            workload.injury_multiplier = max(0.70, workload.injury_multiplier - 0.025)
        elif actor_id == "broadcaster":
            for club in state.clubs.values():
                club.monthly_revenue += 5_000.0
        elif actor_id == "sponsor_council":
            state.integrity_reputation = _clamp(state.integrity_reputation + 0.010)
        elif actor_id == "supporters_federation":
            state.fan_trust = _clamp(state.fan_trust + 0.012)

    def _refresh_blocs_after_election(self, agreement: GovernmentAgreement) -> None:
        coalition = set(agreement.coalition_blocs)
        for actor in self.current_campaign.politics.stakeholders.values():
            if actor.id in coalition:
                actor.support = _clamp(actor.support + 0.055)
                actor.trust = _clamp(actor.trust + 0.025 - 0.04 * agreement.overpromise_index)
                actor.mobilization *= 0.55
            else:
                actor.support = 0.88 * actor.support + 0.12 * 0.42
                actor.mobilization = _clamp(actor.mobilization + 0.025)
            actor.memory.append(
                f"G{self.global_month}: {'joined' if actor.id in coalition else 'opposed'} "
                f"the {agreement.president_name} coalition"
            )
            actor.memory = actor.memory[-10:]

    def _settle_coalition_commitments(self) -> None:
        agreement = self._active_agreement
        if agreement is None or agreement.status in {"ended", "collapsed"}:
            return
        for commitment in agreement.commitments:
            if commitment.status != "pending" or self.global_month < commitment.due_global_month:
                continue
            actor = self.current_campaign.politics.stakeholders[commitment.actor_id]
            if commitment.commitment_type == "budget":
                if self.current_campaign.engine.state.treasury >= commitment.cost:
                    self._apply_commitment(commitment)
                else:
                    self._break_commitment(commitment, actor)
                continue
            if commitment.metric is None or commitment.target is None:
                self._break_commitment(commitment, actor)
                continue
            actual = self._metric_value(commitment.metric)
            if actual >= commitment.target:
                commitment.status = "kept"
                commitment.resolved_global_month = self.global_month
                actor.promises_kept += 1
                actor.support = _clamp(actor.support + 0.035)
                actor.trust = _clamp(actor.trust + 0.050)
                actor.memory.append(
                    f"G{self.global_month}: coalition promise kept — {commitment.title}"
                )
            else:
                self._break_commitment(commitment, actor)
        agreement.stability = self._calculate_agreement_stability(agreement)

    def _break_commitment(self, commitment: CoalitionCommitment, actor) -> None:
        commitment.status = "broken"
        commitment.resolved_global_month = self.global_month
        actor.promises_broken += 1
        actor.support = _clamp(actor.support - 0.075)
        actor.trust = _clamp(actor.trust - 0.095)
        actor.mobilization = _clamp(actor.mobilization + 0.075)
        actor.memory.append(
            f"G{self.global_month}: coalition promise broken — {commitment.title}"
        )

    def _calculate_agreement_stability(self, agreement: GovernmentAgreement) -> float:
        actors = self.current_campaign.politics.stakeholders
        coalition = [actors[item] for item in agreement.coalition_blocs if item in actors]
        if not coalition:
            return 0.0
        power = sum(item.power for item in coalition)
        relationship = sum(
            item.power * (0.58 * item.support + 0.42 * item.trust)
            for item in coalition
        ) / max(power, 1e-9)
        broken = sum(item.status == "broken" for item in agreement.commitments)
        unresolved = sum(
            item.status == "pending" and self.global_month > item.due_global_month
            for item in agreement.commitments
        )
        minority_penalty = 0.10 if agreement.status == "minority" else 0.0
        return _clamp(
            relationship
            - 0.20 * agreement.overpromise_index
            - 0.055 * broken
            - 0.025 * unresolved
            - minority_penalty
        )

    def _maybe_trigger_coalition_breakdown(self) -> None:
        agreement = self._active_agreement
        if (
            agreement is None
            or self.caretaker_active
            or self.current_decision is not None
            or agreement.status in {"ended", "collapsed"}
            or agreement.id in self._fracture_checked
            or self.global_month < agreement.start_global_month + 4
        ):
            return
        agreement.stability = self._calculate_agreement_stability(agreement)
        if agreement.stability >= 0.36:
            return
        self._fracture_checked.add(agreement.id)
        agreement.crises += 1
        self._pending_coalition.append(
            GovernanceDecision(
                id=f"coalition_breakdown_{agreement.id}_{self.global_month}",
                month=self.local_month,
                title="执政联盟破裂：组阁承诺与财政现实冲突",
                narrative=(
                    "部分联盟伙伴认为职位、专项资金或政策承诺没有兑现，准备撤回支持。"
                    "主席必须追加交易、转为少数政府，或接受一次可能导致下台的信任投票。"
                ),
                options=(
                    DecisionOption(
                        "renegotiate_compact",
                        "追加预算重签联盟协议",
                        "支付紧急政治协调资金并重新分配一项内阁职位。",
                        "国库损失与制度俘获风险上升",
                    ),
                    DecisionOption(
                        "govern_minority",
                        "结束交易并转为少数政府",
                        "不再追加利益交换，依靠议题逐案争取支持。",
                        "重大法案更难通过，政治资本下降",
                    ),
                    DecisionOption(
                        "confidence_vote",
                        "接受全国足球代表大会信任投票",
                        "让全部九个集团按当前支持重新表决政府存续。",
                        "若未达到加权多数，主席立即下台",
                    ),
                ),
            )
        )

    def _resolve_coalition_crisis(
        self,
        decision: GovernanceDecision,
        option_id: str,
    ) -> DecisionRecord:
        agreement = self._active_agreement
        if agreement is None:
            raise RuntimeError("coalition crisis has no active agreement")
        before = self._calculate_agreement_stability(agreement)
        state = self.current_campaign.engine.state
        effects: list[str] = []
        if option_id == "renegotiate_compact":
            cost = min(1_200_000.0, state.treasury)
            state.treasury -= cost
            for actor_id in agreement.coalition_blocs:
                actor = self.current_campaign.politics.stakeholders[actor_id]
                actor.support = _clamp(actor.support + 0.050)
                actor.trust = _clamp(actor.trust + 0.025)
            for official in self.cabinet.values():
                official.network_power = _clamp(official.network_power + 0.012)
            agreement.overpromise_index = _clamp(agreement.overpromise_index + 0.08)
            agreement.status = "renegotiated"
            effects.append(f"政府支付{cost:.0f}协调资金，暂时恢复联盟纪律。")
        elif option_id == "govern_minority":
            agreement.status = "minority"
            state.political_capital = _clamp(state.political_capital - 0.055)
            for actor_id in agreement.coalition_blocs:
                actor = self.current_campaign.politics.stakeholders[actor_id]
                actor.support = _clamp(actor.support - 0.025)
            effects.append("政府失去稳定多数，今后议程逐案谈判。")
        elif option_id == "confidence_vote":
            yes_power = sum(
                actor.power
                for actor in self.current_campaign.politics.stakeholders.values()
                if 0.62 * actor.support + 0.38 * actor.trust >= 0.50
            )
            total = sum(
                actor.power
                for actor in self.current_campaign.politics.stakeholders.values()
            )
            share = yes_power / max(total, 1e-9)
            if share <= 0.50:
                agreement.status = "collapsed"
                effects.append(f"政府仅获{share:.1%}加权支持，信任案失败。")
                self._start_caretaker("coalition government lost a confidence vote")
            else:
                agreement.status = "confidence restored"
                state.political_capital = _clamp(state.political_capital + 0.035)
                effects.append(f"政府以{share:.1%}加权支持通过信任投票。")
        else:
            raise ValueError(f"unknown coalition-crisis option {option_id!r}")
        agreement.stability = self._calculate_agreement_stability(agreement)
        self._pending_coalition.pop(0)
        outcome = effects[0]
        self.coalition_crises.append(
            CoalitionCrisisRecord(
                self.global_month,
                self.term_index,
                self.current_president.name,
                agreement.id,
                before,
                option_id,
                outcome,
            )
        )
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "coalition crisis resolved",
                decision.title,
                1.0 - before,
                tuple(effects),
            )
        )
        return DecisionRecord(
            decision.id,
            self.local_month,
            decision.title,
            option_id,
            next(item.title for item in decision.options if item.id == option_id),
            tuple(effects),
        )

    def _preferred_candidate(self) -> ElectionCandidate:
        election = self._require_election()
        state = self.current_campaign.engine.state
        desired = (
            Strategy.FOUNDATIONS
            if state.integrity_reputation < 0.48
            else Strategy.QUICK_RESULTS
            if state.national_team_strength < 48.0 and state.fan_trust < 0.45
            else Strategy.BALANCED
        )
        return next(
            (
                election.candidates[item]
                for item in election.active_candidate_ids
                if election.candidates[item].strategy == desired
            ),
            election.candidates[election.active_candidate_ids[0]],
        )

    def _automatic_convention(self, trigger: str) -> tuple[PresidentProfile, GovernmentAgreement]:
        election_id = f"scheduled-{self.term_index}-{self.global_month}-{len(self.election_history)}"
        candidates = self._generate_candidates(election_id)
        convention = ElectionConvention(
            election_id,
            trigger,
            self.global_month,
            {item.id: item for item in candidates},
            [item.id for item in candidates],
            accumulated_commitments={item.id: [] for item in candidates},
        )
        while True:
            preferred = self._preferred_from_convention(convention)
            package = "coalition" if convention.round_number == 1 else "grand"
            outcome = self._conduct_election_round(convention, preferred.id, package)
            if outcome.record.winner_candidate_id is not None:
                agreement = self._agreement_from_winner(convention, outcome)
                candidate = convention.candidates[outcome.record.winner_candidate_id]
                return self._candidate_to_president(candidate, "scheduled"), agreement
            if outcome.record.eliminated_candidate_id:
                convention.active_candidate_ids.remove(outcome.record.eliminated_candidate_id)
            convention.round_number += 1

    def _preferred_from_convention(self, convention: ElectionConvention) -> ElectionCandidate:
        state = self.current_campaign.engine.state
        desired = (
            Strategy.FOUNDATIONS
            if state.integrity_reputation < 0.48
            else Strategy.QUICK_RESULTS
            if state.national_team_strength < 48.0 and state.fan_trust < 0.45
            else Strategy.BALANCED
        )
        return next(
            (
                convention.candidates[item]
                for item in convention.active_candidate_ids
                if convention.candidates[item].strategy == desired
            ),
            convention.candidates[convention.active_candidate_ids[0]],
        )

    def _select_successor(self, board_score: float, political_score: float):
        proposed, reason = ConstitutionalLongTermCampaign._select_successor(
            self, board_score, political_score
        )
        if proposed.id == self.current_president.id:
            return proposed, reason
        successor, agreement = self._automatic_convention("scheduled succession convention")
        self._scheduled_agreement = agreement
        return successor, f"{reason}; successor selected through a weighted coalition convention"

    def _rollover(self, bundle, president: PresidentProfile) -> None:
        if self._active_agreement is not None:
            self._active_agreement.status = "ended"
            self._active_agreement.stability = self._calculate_agreement_stability(
                self._active_agreement
            )
        super()._rollover(bundle, president)
        if self._scheduled_agreement is not None:
            agreement = self._scheduled_agreement
            agreement.president_id = president.id
            agreement.president_name = president.name
            agreement.start_global_month = self.global_month
            self._activate_agreement(agreement)
            self._scheduled_agreement = None

    def _require_election(self) -> ElectionConvention:
        if self._election is None:
            raise RuntimeError("there is no active election convention")
        return self._election

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = COALITION_SAVE_VERSION
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoalitionElectionHistory":
        if data.get("format_version") != COALITION_SAVE_VERSION:
            raise ValueError("unsupported coalition-history format")
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        target_month = int(data.get("global_month", 0))
        commands = list(data.get("decision_log", []))
        injections = list(data.get("injected_crises", []))
        command_index = 0
        injection_index = 0
        while (
            campaign.global_month < target_month
            or command_index < len(commands)
            or injection_index < len(injections)
        ):
            if injection_index < len(injections):
                injection = injections[injection_index]
                injection_month = int(injection["global_month"])
                if injection_month < campaign.global_month:
                    raise ValueError("scenario injection was not reachable during replay")
                if injection_month == campaign.global_month:
                    campaign.force_crisis(
                        office=injection["office"],
                        severity=float(injection["severity"]),
                        allegation=injection["allegation"],
                        _record_injection=True,
                    )
                    injection_index += 1
                    continue
            if campaign.current_decision is not None:
                if command_index >= len(commands):
                    if campaign.global_month >= target_month:
                        break
                    raise ValueError("save omits a decision required before target month")
                command = commands[command_index]
                if int(command["global_month"]) != campaign.global_month:
                    raise ValueError("save decision reached at a different month")
                if command["decision_id"] != campaign.current_decision.id:
                    raise ValueError("save replay reached a different decision")
                campaign.resolve_decision(command["option_id"])
                command_index += 1
                continue
            if campaign.global_month >= target_month:
                break
            campaign.advance(1, interactive=True)
        if command_index != len(commands):
            raise ValueError("save contains unreachable coalition decisions")
        if injection_index != len(injections):
            raise ValueError("save contains unreachable scenario injections")
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("coalition-history replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "CoalitionElectionHistory":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "CoalitionElectionHistory":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "elections": [asdict(item) for item in self.election_history],
            "agreements": [asdict(item) for item in self.government_agreements],
            "coalition_crises": [asdict(item) for item in self.coalition_crises],
            "pending_election": (
                self._pending_election[0].id if self._pending_election else None
            ),
            "pending_coalition": (
                self._pending_coalition[0].id if self._pending_coalition else None
            ),
            "active_election": asdict(self._election) if self._election else None,
            "active_agreement": (
                self._active_agreement.id if self._active_agreement else None
            ),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class _RoundOutcome:
    record: ElectionRoundRecord
    shares_dict: dict[str, float]

    @property
    def winner_candidate_id(self) -> str | None:
        return self.record.winner_candidate_id

    @property
    def eliminated_candidate_id(self) -> str | None:
        return self.record.eliminated_candidate_id
