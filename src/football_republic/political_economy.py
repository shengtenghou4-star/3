"""Persistent stakeholders, coalition politics and presidential legacy records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .domain import NationalFootballSystem
from .governance import DecisionOption, DecisionRecord, GovernanceDecision


ISSUES = (
    "integrity",
    "grassroots",
    "market",
    "fiscal",
    "labor",
    "local_autonomy",
    "national_team",
    "competitive_balance",
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _average(values: list[float]) -> float:
    return sum(values) / max(1, len(values))


@dataclass(slots=True)
class StakeholderProfile:
    id: str
    name: str
    bloc: str
    power: float
    support: float
    trust: float
    patience: float
    preferences: dict[str, float]
    mobilization: float = 0.0
    promises_kept: int = 0
    promises_broken: int = 0
    last_contact_month: int = 0
    memory: list[str] = field(default_factory=list)

    def compatibility(self, signal: dict[str, float]) -> float:
        denominator = sum(abs(value) for value in self.preferences.values()) or 1.0
        score = sum(
            self.preferences.get(issue, 0.0) * signal.get(issue, 0.0)
            for issue in ISSUES
        ) / denominator
        return max(-1.0, min(1.0, score))

    def react(
        self,
        *,
        month: int,
        signal: dict[str, float],
        reliability: float,
        intensity: float,
        note: str,
    ) -> None:
        compatibility = self.compatibility(signal)
        delta = intensity * (0.72 * compatibility + 0.28 * reliability)
        self.support = _clamp(self.support + delta)
        self.trust = _clamp(
            self.trust + intensity * (0.58 * reliability + 0.18 * compatibility)
        )
        self.patience = _clamp(
            self.patience + intensity * (0.20 * compatibility + 0.10 * reliability)
        )
        self.mobilization = _clamp(
            0.35 * self.power + 0.65 * max(0.0, 0.55 - self.support)
        )
        self.last_contact_month = month
        self.memory.append(
            f"M{month}: {note}; compatibility {compatibility:+.2f}; "
            f"support {self.support:.2f}; trust {self.trust:.2f}"
        )
        self.memory = self.memory[-10:]

    @property
    def stance(self) -> str:
        if self.support >= 0.72:
            return "committed ally"
        if self.support >= 0.57:
            return "supportive"
        if self.support >= 0.43:
            return "transactional"
        if self.support >= 0.28:
            return "opposition"
        return "mobilized opposition"


@dataclass(frozen=True, slots=True)
class PoliticalEvent:
    month: int
    actor_id: str
    actor_name: str
    event_type: str
    headline: str
    effects: tuple[str, ...]


@dataclass(slots=True)
class PoliticalPromise:
    id: str
    created_month: int
    due_month: int
    title: str
    metric: str
    baseline: float
    target: float
    beneficiaries: tuple[str, ...]
    status: str = "pending"
    resolved_month: int | None = None
    actual_value: float | None = None


@dataclass(frozen=True, slots=True)
class AgendaOutcome:
    month: int
    agenda_id: str
    agenda_title: str
    option_id: str
    option_title: str
    passed: bool
    coalition_support: float
    yes_power: float
    total_power: float
    supporters: tuple[str, ...]
    opponents: tuple[str, ...]
    effects: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class YearArchive:
    year: int
    month: int
    coalition_support: float
    governability: float
    treasury: float
    fan_trust: float
    integrity: float
    youth_environment: float
    national_team_strength: float
    solvent_club_share: float
    premier_champion: str
    cup_champion: str
    continental_best_stage: str
    strongest_ally: str
    opposition_leader: str
    decisions: tuple[str, ...]
    political_events: int
    promises_kept: int
    promises_broken: int


@dataclass(frozen=True, slots=True)
class PoliticalReview:
    score: float
    verdict: str
    coalition_support: float
    governability: float
    strongest_ally: str
    opposition_leader: str
    promises_kept: int
    promises_broken: int
    explanation: tuple[str, ...]


AGENDA_DECISIONS: dict[int, GovernanceDecision] = {
    2: GovernanceDecision(
        id="agenda_governance_compact",
        month=2,
        title="国家足球治理权力重组",
        narrative=(
            "体育主管部门要求加强中央准入权，地方足协要求保留执行自主权，"
            "俱乐部则担心监管重复。主席必须决定国家足球体系究竟如何分权。"
        ),
        options=(
            DecisionOption(
                "central_command",
                "建立中央职业足球监管局",
                "将准入、审计和重大纪律权集中到国家层面。",
                "地方抵制、执行放缓和行政成本上升",
            ),
            DecisionOption(
                "federal_compact",
                "签署中央—地方治理契约",
                "中央制定底线，地方承担执行，资金与绩效挂钩。",
                "改革速度不快，双方都需要持续让步",
            ),
            DecisionOption(
                "local_devolution",
                "扩大地方足协自主权",
                "让地方根据人口、财政和足球文化自行设计项目。",
                "地区差距、寻租和标准碎片化风险",
            ),
        ),
    ),
    10: GovernanceDecision(
        id="agenda_calendar_compact",
        month=10,
        title="球员劳动与赛历集体协议",
        narrative=(
            "三线作战和国家队征召导致伤病增加。球员工会要求强制休息期，"
            "俱乐部和转播商则希望保留黄金时段与商业赛事。"
        ),
        options=(
            DecisionOption(
                "player_welfare_compact",
                "签署球员福利协议",
                "建立休息期、医疗审查和高负荷月保护规则。",
                "俱乐部与转播商损失部分赛历自由",
            ),
            DecisionOption(
                "managed_flexibility",
                "受监管的弹性赛历",
                "保留商业赛程，但增加医疗监测和补偿机制。",
                "劳资双方都认为让步不够彻底",
            ),
            DecisionOption(
                "club_calendar_primacy",
                "俱乐部商业赛历优先",
                "允许俱乐部和转播商最大化比赛与曝光。",
                "伤病、罢赛和国家队放人冲突风险",
            ),
        ),
    ),
    14: GovernanceDecision(
        id="agenda_commercial_model",
        month=14,
        title="职业联赛商业增长模式",
        narrative=(
            "豪门要求把更多商业资源集中到头部俱乐部，二级联赛和地方足协要求团结分配。"
            "主席必须选择增长优先、均衡优先或折中监管。"
        ),
        options=(
            DecisionOption(
                "solidarity_distribution",
                "团结分配与二级联赛保障",
                "将新增商业收益更多投向弱队、青训和地区市场。",
                "头部俱乐部威胁另组商业联盟",
            ),
            DecisionOption(
                "star_club_growth",
                "头部俱乐部增长引擎",
                "允许豪门凭球迷、赞助和洲际成绩获得更大商业份额。",
                "贫富差距扩大，联赛竞争失衡",
            ),
            DecisionOption(
                "regulated_balance",
                "受监管的市场化平衡",
                "保留头部激励，同时设立最低分成和财务护栏。",
                "改革不够激进，增长和公平都有限",
            ),
        ),
    ),
    22: GovernanceDecision(
        id="agenda_integrity_constitution",
        month=22,
        title="足协廉洁与问责宪章",
        narrative=(
            "地方回扣案后，赞助商、球迷和体育主管部门要求永久化调查机制。"
            "地方体系和部分俱乐部担心独立机构会让项目长期停摆。"
        ),
        options=(
            DecisionOption(
                "independent_integrity_unit",
                "独立廉洁委员会",
                "建立独立调查、财产申报和公开处罚机制。",
                "政治成本高，短期执行速度下降",
            ),
            DecisionOption(
                "internal_compliance_office",
                "强化内部合规办公室",
                "在足协内部扩充审计、纪律和举报保护。",
                "独立性不足，仍可能受到主席干预",
            ),
            DecisionOption(
                "protect_delivery",
                "以项目交付为优先",
                "限制调查范围，避免地方项目和联赛运营被打断。",
                "下一次泄露可能造成系统性信任崩塌",
            ),
        ),
    ),
}


AGENDA_SIGNALS: dict[str, dict[str, dict[str, float]]] = {
    "agenda_governance_compact": {
        "central_command": {
            "integrity": 0.85,
            "fiscal": -0.20,
            "local_autonomy": -1.00,
            "market": -0.20,
        },
        "federal_compact": {
            "integrity": 0.40,
            "grassroots": 0.35,
            "fiscal": 0.20,
            "local_autonomy": 0.35,
        },
        "local_devolution": {
            "local_autonomy": 1.00,
            "grassroots": 0.25,
            "integrity": -0.45,
            "fiscal": 0.15,
        },
    },
    "agenda_calendar_compact": {
        "player_welfare_compact": {
            "labor": 1.00,
            "integrity": 0.25,
            "market": -0.45,
            "fiscal": -0.25,
            "national_team": 0.30,
        },
        "managed_flexibility": {
            "labor": 0.35,
            "market": 0.30,
            "fiscal": 0.20,
            "national_team": 0.15,
        },
        "club_calendar_primacy": {
            "market": 0.95,
            "labor": -1.00,
            "national_team": -0.25,
            "fiscal": 0.25,
        },
    },
    "agenda_commercial_model": {
        "solidarity_distribution": {
            "competitive_balance": 1.00,
            "grassroots": 0.65,
            "market": -0.65,
            "fiscal": -0.10,
        },
        "star_club_growth": {
            "market": 1.00,
            "national_team": 0.20,
            "competitive_balance": -0.90,
            "grassroots": -0.35,
        },
        "regulated_balance": {
            "market": 0.35,
            "competitive_balance": 0.45,
            "fiscal": 0.35,
            "integrity": 0.20,
        },
    },
    "agenda_integrity_constitution": {
        "independent_integrity_unit": {
            "integrity": 1.00,
            "fiscal": -0.30,
            "local_autonomy": -0.45,
        },
        "internal_compliance_office": {
            "integrity": 0.50,
            "fiscal": 0.15,
            "local_autonomy": -0.10,
        },
        "protect_delivery": {
            "integrity": -1.00,
            "fiscal": 0.30,
            "local_autonomy": 0.25,
        },
    },
}


DECISION_SIGNALS: dict[str, dict[str, float]] = {
    "transparent_reform": {"integrity": 0.90, "labor": 0.55, "fiscal": -0.25},
    "quiet_settlement": {"integrity": -0.40, "fiscal": 0.25},
    "blame_local": {"integrity": -0.65, "local_autonomy": -0.80, "fiscal": 0.25},
    "homegrown_priority": {"grassroots": 0.90, "national_team": 0.35, "market": -0.55},
    "open_market": {"market": 1.00, "grassroots": -0.55, "fiscal": -0.45},
    "financial_control": {"fiscal": 0.95, "integrity": 0.30, "market": -0.20},
    "conditional_rescue": {"fiscal": 0.35, "labor": 0.30, "integrity": 0.20},
    "refuse_bailout": {"fiscal": 0.85, "integrity": 0.45, "competitive_balance": -0.15},
    "blank_cheque": {"market": 0.45, "fiscal": -1.00, "integrity": -0.85},
    "grassroots_acceleration": {"grassroots": 1.00, "integrity": 0.35, "national_team": -0.20},
    "balanced_renewal": {"grassroots": 0.45, "fiscal": 0.45, "national_team": 0.35},
    "qualification_surge": {"national_team": 1.00, "grassroots": -0.65, "fiscal": -0.20},
    "protect_coach": {"national_team": 0.45, "fiscal": 0.25},
    "replace_coach": {"national_team": 0.65, "fiscal": -0.35},
    "media_offensive": {"integrity": -0.45, "national_team": 0.20},
    "independent_probe": {"integrity": 1.00, "local_autonomy": -0.55, "fiscal": -0.20},
    "internal_discipline": {"integrity": 0.45, "fiscal": 0.25},
    "bury_case": {"integrity": -1.00, "local_autonomy": 0.25, "fiscal": 0.20},
}


AUTO_AGENDA_CHOICES: dict[str, dict[str, str]] = {
    "foundations": {
        "agenda_governance_compact": "federal_compact",
        "agenda_calendar_compact": "player_welfare_compact",
        "agenda_commercial_model": "solidarity_distribution",
        "agenda_integrity_constitution": "independent_integrity_unit",
    },
    "balanced": {
        "agenda_governance_compact": "federal_compact",
        "agenda_calendar_compact": "managed_flexibility",
        "agenda_commercial_model": "regulated_balance",
        "agenda_integrity_constitution": "internal_compliance_office",
    },
    "quick-results": {
        "agenda_governance_compact": "local_devolution",
        "agenda_calendar_compact": "club_calendar_primacy",
        "agenda_commercial_model": "star_club_growth",
        "agenda_integrity_constitution": "protect_delivery",
    },
}


class PoliticalEconomy:
    """A persistent coalition layer around the football simulation."""

    def __init__(self) -> None:
        self.stakeholders = self._build_stakeholders()
        self.agenda_history: list[AgendaOutcome] = []
        self.event_history: list[PoliticalEvent] = []
        self.promises: list[PoliticalPromise] = []
        self.year_archives: list[YearArchive] = []
        self.triggered_agendas: set[str] = set()

    @staticmethod
    def _build_stakeholders() -> dict[str, StakeholderProfile]:
        specs = (
            (
                "sports_ministry",
                "国家体育主管部门",
                "central government",
                0.95,
                0.62,
                0.64,
                0.62,
                {"national_team": 1.00, "integrity": 0.55, "fiscal": 0.25, "local_autonomy": -0.20},
            ),
            (
                "finance_ministry",
                "财政部门",
                "central government",
                0.88,
                0.54,
                0.58,
                0.58,
                {"fiscal": 1.00, "integrity": 0.40, "market": 0.20, "grassroots": -0.10},
            ),
            (
                "education_ministry",
                "教育部门",
                "public institutions",
                0.76,
                0.57,
                0.58,
                0.64,
                {"grassroots": 1.00, "integrity": 0.35, "local_autonomy": 0.20, "labor": 0.15},
            ),
            (
                "provincial_fas",
                "地方足协与地方政府联盟",
                "local government",
                0.84,
                0.52,
                0.50,
                0.55,
                {"local_autonomy": 1.00, "grassroots": 0.45, "fiscal": 0.15, "integrity": -0.10},
            ),
            (
                "club_owners",
                "职业俱乐部投资人理事会",
                "clubs",
                0.90,
                0.48,
                0.46,
                0.50,
                {"market": 1.00, "local_autonomy": 0.35, "labor": -0.45, "competitive_balance": -0.65, "fiscal": -0.20},
            ),
            (
                "players_union",
                "职业球员工会",
                "labor",
                0.68,
                0.46,
                0.48,
                0.52,
                {"labor": 1.00, "integrity": 0.45, "fiscal": -0.15, "market": -0.10},
            ),
            (
                "broadcaster",
                "全国转播与数字平台联盟",
                "media",
                0.72,
                0.55,
                0.53,
                0.50,
                {"market": 0.90, "national_team": 0.45, "competitive_balance": -0.25, "labor": -0.20},
            ),
            (
                "sponsor_council",
                "主要赞助商委员会",
                "commercial",
                0.70,
                0.58,
                0.60,
                0.62,
                {"integrity": 0.90, "market": 0.50, "national_team": 0.35, "fiscal": 0.25},
            ),
            (
                "supporters_federation",
                "全国球迷与社区俱乐部联合会",
                "public",
                0.74,
                0.56,
                0.55,
                0.57,
                {"integrity": 0.85, "competitive_balance": 0.75, "grassroots": 0.45, "labor": 0.25, "market": -0.15},
            ),
        )
        return {
            item[0]: StakeholderProfile(
                id=item[0],
                name=item[1],
                bloc=item[2],
                power=item[3],
                support=item[4],
                trust=item[5],
                patience=item[6],
                preferences=item[7],
            )
            for item in specs
        }

    @property
    def coalition_support(self) -> float:
        total_power = sum(actor.power for actor in self.stakeholders.values())
        return sum(
            actor.power * actor.support for actor in self.stakeholders.values()
        ) / max(total_power, 1e-9)

    @property
    def governability(self) -> float:
        total_power = sum(actor.power for actor in self.stakeholders.values())
        return sum(
            actor.power
            * (0.50 * actor.support + 0.30 * actor.trust + 0.20 * actor.patience)
            for actor in self.stakeholders.values()
        ) / max(total_power, 1e-9)

    @property
    def strongest_ally(self) -> StakeholderProfile:
        return max(
            self.stakeholders.values(),
            key=lambda actor: actor.power * actor.support,
        )

    @property
    def opposition_leader(self) -> StakeholderProfile:
        return max(
            self.stakeholders.values(),
            key=lambda actor: actor.power * (1.0 - actor.support),
        )

    def agenda_for_month(self, month: int) -> GovernanceDecision | None:
        decision = AGENDA_DECISIONS.get(month)
        if decision is None or decision.id in self.triggered_agendas:
            return None
        self.triggered_agendas.add(decision.id)
        return decision

    def auto_choice(self, decision_id: str, strategy: str) -> str:
        return AUTO_AGENDA_CHOICES[strategy][decision_id]

    def advance_month(
        self,
        month: int,
        state: NationalFootballSystem,
        football: Any,
    ) -> None:
        self._evaluate_promises(month, state, football)
        if month not in (3, 5, 7, 9, 11, 15, 17, 19, 21, 23):
            return
        weakest = self.opposition_leader
        strongest = self.strongest_ally
        if weakest.support < 0.39 and weakest.mobilization >= 0.45:
            self._apply_pressure(month, weakest, state, football)
        elif strongest.support > 0.68 and strongest.trust > 0.56:
            self._apply_cooperation(month, strongest, state, football)

    def react_to_decision(
        self,
        record: DecisionRecord,
    ) -> None:
        signal = DECISION_SIGNALS.get(record.option_id)
        if signal is None:
            return
        reliability = 0.25 if record.option_id in {
            "quiet_settlement",
            "blame_local",
            "blank_cheque",
            "media_offensive",
            "bury_case",
        } else 0.62
        for actor in self.stakeholders.values():
            actor.react(
                month=record.month,
                signal=signal,
                reliability=reliability,
                intensity=0.055,
                note=f"presidential decision {record.option_title}",
            )

    def resolve_agenda(
        self,
        decision: GovernanceDecision,
        option_id: str,
        state: NationalFootballSystem,
        football: Any,
    ) -> tuple[AgendaOutcome, tuple[str, ...]]:
        option = next(item for item in decision.options if item.id == option_id)
        signal = AGENDA_SIGNALS[decision.id][option_id]
        yes: list[StakeholderProfile] = []
        no: list[StakeholderProfile] = []
        for actor in self.stakeholders.values():
            compatibility = (actor.compatibility(signal) + 1.0) / 2.0
            vote_score = (
                0.43 * actor.support
                + 0.24 * actor.trust
                + 0.27 * compatibility
                + 0.06 * actor.patience
            )
            (yes if vote_score >= 0.51 else no).append(actor)
        yes_power = sum(actor.power for actor in yes)
        total_power = sum(actor.power for actor in self.stakeholders.values())
        ratio = yes_power / max(total_power, 1e-9)
        forced = False
        passed = ratio >= 0.50
        if not passed and ratio >= 0.44 and state.political_capital >= 0.18:
            passed = True
            forced = True
            state.political_capital = _clamp(state.political_capital - 0.045)
        scale = 1.0 if passed else 0.22
        effects = list(
            self._apply_agenda_effects(
                decision.id,
                option_id,
                scale,
                state,
                football,
            )
        )
        if passed:
            capital_delta = 0.035 * (ratio - 0.50)
            state.political_capital = _clamp(state.political_capital + capital_delta)
            effects.append(
                f"Coalition vote passed with {ratio:.0%} of stakeholder power."
            )
            if forced:
                effects.append("The president forced passage by spending political capital.")
        else:
            state.political_capital = _clamp(state.political_capital - 0.030)
            effects.append(
                f"Coalition vote failed with only {ratio:.0%} of stakeholder power."
            )
            effects.append("Only a limited executive directive took effect.")
        reliability = 0.72 if passed and not forced else 0.48 if passed else -0.20
        for actor in self.stakeholders.values():
            actor.react(
                month=decision.month,
                signal=signal,
                reliability=reliability,
                intensity=0.095,
                note=f"agenda vote {option.title}",
            )
        if passed:
            promise = self._create_promise(
                decision.id,
                option_id,
                decision.month,
                state,
                football,
            )
            self.promises.append(promise)
            effects.append(
                f"A public promise was recorded: {promise.title} by month {promise.due_month}."
            )
        outcome = AgendaOutcome(
            month=decision.month,
            agenda_id=decision.id,
            agenda_title=decision.title,
            option_id=option_id,
            option_title=option.title,
            passed=passed,
            coalition_support=ratio,
            yes_power=yes_power,
            total_power=total_power,
            supporters=tuple(actor.name for actor in yes),
            opponents=tuple(actor.name for actor in no),
            effects=tuple(effects),
        )
        self.agenda_history.append(outcome)
        return outcome, tuple(effects)

    def record_year(
        self,
        month: int,
        state: NationalFootballSystem,
        football: Any,
        decision_history: list[DecisionRecord],
    ) -> YearArchive:
        year = 1 if month <= 12 else 2
        if any(item.year == year for item in self.year_archives):
            return next(item for item in self.year_archives if item.year == year)
        champion_id = getattr(football.pyramid, "champion_history", {}).get(year)
        premier_champion = (
            state.clubs[champion_id].name if champion_id in state.clubs else "not recorded"
        )
        cup_id = football.domestic_cup.champions.get(year)
        cup_champion = state.clubs[cup_id].name if cup_id in state.clubs else "not completed"
        continental = next(
            (
                summary
                for summary in football.continental_history
                if summary.season == year
            ),
            None,
        )
        if continental is None and football.continental.season == year:
            continental = football.continental.summary
        best_stage = continental.domestic_best_stage if continental else "not completed"
        start_month = 1 if year == 1 else 13
        decisions = tuple(
            f"{record.title}: {record.option_title}"
            for record in decision_history
            if start_month <= record.month <= month
        )
        archive = YearArchive(
            year=year,
            month=month,
            coalition_support=self.coalition_support,
            governability=self.governability,
            treasury=state.treasury,
            fan_trust=state.fan_trust,
            integrity=state.integrity_reputation,
            youth_environment=state.youth_development_environment,
            national_team_strength=state.national_team_strength,
            solvent_club_share=state.solvent_club_share,
            premier_champion=premier_champion,
            cup_champion=cup_champion,
            continental_best_stage=best_stage,
            strongest_ally=self.strongest_ally.name,
            opposition_leader=self.opposition_leader.name,
            decisions=decisions,
            political_events=sum(
                start_month <= event.month <= month for event in self.event_history
            ),
            promises_kept=sum(promise.status == "kept" for promise in self.promises),
            promises_broken=sum(promise.status == "broken" for promise in self.promises),
        )
        self.year_archives.append(archive)
        return archive

    def review(self, board_score: float) -> PoliticalReview:
        kept = sum(item.status == "kept" for item in self.promises)
        broken = sum(item.status == "broken" for item in self.promises)
        promise_score = 0.55 if kept + broken == 0 else kept / (kept + broken)
        score = (
            0.55 * board_score
            + 25.0 * self.coalition_support
            + 12.0 * self.governability
            + 8.0 * promise_score
        )
        if score >= 72:
            verdict = "second term secured with a governing coalition"
        elif score >= 61:
            verdict = "second term secured after coalition bargaining"
        elif score >= 51:
            verdict = "renominated but politically constrained"
        else:
            verdict = "coalition collapsed; succession contest begins"
        explanation = (
            f"Stakeholder coalition support finished at {self.coalition_support:.0%}.",
            f"Governability finished at {self.governability:.0%}.",
            f"Public promises kept/broken: {kept}/{broken}.",
            f"Strongest ally: {self.strongest_ally.name}.",
            f"Opposition leader: {self.opposition_leader.name}.",
        )
        return PoliticalReview(
            score=score,
            verdict=verdict,
            coalition_support=self.coalition_support,
            governability=self.governability,
            strongest_ally=self.strongest_ally.name,
            opposition_leader=self.opposition_leader.name,
            promises_kept=kept,
            promises_broken=broken,
            explanation=explanation,
        )

    def _apply_pressure(
        self,
        month: int,
        actor: StakeholderProfile,
        state: NationalFootballSystem,
        football: Any,
    ) -> None:
        effects: list[str] = []
        if actor.id == "sports_ministry":
            state.political_capital = _clamp(state.political_capital - 0.010)
            effects.append("central political capital -1.0pp")
        elif actor.id == "finance_ministry":
            withheld = min(state.treasury, 350_000.0)
            state.treasury -= withheld
            effects.append(f"¥{withheld:,.0f} grant payment delayed")
        elif actor.id == "education_ministry":
            for region in state.regions.values():
                region.parent_support = _clamp(region.parent_support - 0.006)
            effects.append("school-football cooperation weakened")
        elif actor.id == "provincial_fas":
            region = min(state.regions.values(), key=lambda item: item.execution_capacity)
            region.execution_capacity = _clamp(region.execution_capacity - 0.012)
            effects.append(f"{region.name} slowed implementation")
        elif actor.id == "club_owners":
            for owner in football.pyramid.owners.values():
                owner.relationship_with_fa = _clamp(owner.relationship_with_fa - 0.010)
            effects.append("club-owner cooperation weakened")
        elif actor.id == "players_union":
            for roster in football.rosters.values():
                for player in roster.players:
                    player.morale = max(0.0, player.morale - 0.7)
            effects.append("player morale fell amid labor action")
        elif actor.id == "broadcaster":
            state.fan_trust = _clamp(state.fan_trust - 0.006)
            effects.append("broadcast scheduling dispute damaged fan trust")
        elif actor.id == "sponsor_council":
            active = [
                contract
                for contract in football.economy.sponsors.contracts.values()
                if contract.status == "active"
            ]
            if active:
                contract = min(active, key=lambda item: item.annual_value)
                contract.status = "under review"
                effects.append(f"{contract.sponsor_name} placed a contract under review")
        else:
            state.fan_trust = _clamp(state.fan_trust - 0.012)
            effects.append("supporter demonstrations reduced fan trust")
        actor.mobilization = _clamp(actor.mobilization + 0.05)
        event = PoliticalEvent(
            month=month,
            actor_id=actor.id,
            actor_name=actor.name,
            event_type="pressure",
            headline=f"{actor.name} escalated pressure on the presidency",
            effects=tuple(effects),
        )
        self.event_history.append(event)

    def _apply_cooperation(
        self,
        month: int,
        actor: StakeholderProfile,
        state: NationalFootballSystem,
        football: Any,
    ) -> None:
        effects: list[str] = []
        if actor.id in {"sports_ministry", "finance_ministry"}:
            grant = 250_000.0 + 250_000.0 * actor.power
            state.treasury += grant
            effects.append(f"¥{grant:,.0f} cooperation grant received")
        elif actor.id == "education_ministry":
            for region in state.regions.values():
                region.parent_support = _clamp(region.parent_support + 0.006)
            effects.append("school-football access expanded")
        elif actor.id == "provincial_fas":
            region = min(state.regions.values(), key=lambda item: item.execution_capacity)
            region.execution_capacity = _clamp(region.execution_capacity + 0.010)
            effects.append(f"{region.name} accelerated implementation")
        elif actor.id == "club_owners":
            for owner in football.pyramid.owners.values():
                owner.relationship_with_fa = _clamp(owner.relationship_with_fa + 0.008)
            effects.append("owners accepted coordinated investment guidance")
        elif actor.id == "players_union":
            for roster in football.rosters.values():
                roster.medical_quality = _clamp(roster.medical_quality + 0.004)
            effects.append("joint medical programme improved club standards")
        elif actor.id == "broadcaster":
            state.fan_trust = _clamp(state.fan_trust + 0.005)
            effects.append("free-to-air showcase improved public access")
        elif actor.id == "sponsor_council":
            state.treasury += 300_000.0
            effects.append("sponsors funded a national community campaign")
        else:
            state.fan_trust = _clamp(state.fan_trust + 0.008)
            effects.append("supporter federation endorsed the reform programme")
        actor.mobilization = _clamp(actor.mobilization - 0.04)
        self.event_history.append(
            PoliticalEvent(
                month=month,
                actor_id=actor.id,
                actor_name=actor.name,
                event_type="cooperation",
                headline=f"{actor.name} delivered a cooperation dividend",
                effects=tuple(effects),
            )
        )

    def _apply_agenda_effects(
        self,
        agenda_id: str,
        option_id: str,
        scale: float,
        state: NationalFootballSystem,
        football: Any,
    ) -> tuple[str, ...]:
        effects: list[str] = []

        def spend(amount: float) -> float:
            actual = min(state.treasury, amount * scale)
            state.treasury -= actual
            return actual

        if agenda_id == "agenda_governance_compact":
            if option_id == "central_command":
                cost = spend(2_000_000.0)
                for region in state.regions.values():
                    region.integrity = _clamp(region.integrity + 0.050 * scale)
                    region.execution_capacity = _clamp(region.execution_capacity - 0.018 * scale)
                for club in state.clubs.values():
                    club.licensing_compliance = _clamp(club.licensing_compliance + 0.030 * scale)
                effects.append(f"Central regulator established at a cost of ¥{cost:,.0f}.")
                effects.append("Integrity and licensing improved; local execution slowed.")
            elif option_id == "federal_compact":
                cost = spend(1_300_000.0)
                for region in state.regions.values():
                    region.integrity = _clamp(region.integrity + 0.022 * scale)
                    region.execution_capacity = _clamp(region.execution_capacity + 0.025 * scale)
                effects.append(f"Performance compact funded with ¥{cost:,.0f}.")
                effects.append("Local execution and accountability improved together.")
            else:
                for region in state.regions.values():
                    region.execution_capacity = _clamp(region.execution_capacity + 0.042 * scale)
                    region.integrity = _clamp(region.integrity - 0.015 * scale)
                state.political_capital = _clamp(state.political_capital + 0.018 * scale)
                effects.append("Local implementation accelerated under devolved authority.")
                effects.append("Audit consistency and national standards weakened.")

        elif agenda_id == "agenda_calendar_compact":
            if option_id == "player_welfare_compact":
                cost = spend(1_800_000.0)
                football.workload.congestion_multiplier = 0.72
                football.workload.international_release_cost = 3.4
                for roster in football.rosters.values():
                    roster.medical_quality = _clamp(roster.medical_quality + 0.045 * scale)
                effects.append(f"Player welfare programme cost ¥{cost:,.0f}.")
                effects.append("Congestion and international-release fatigue were reduced.")
            elif option_id == "managed_flexibility":
                cost = spend(800_000.0)
                football.workload.congestion_multiplier = 0.90
                football.workload.international_release_cost = 4.0
                for roster in football.rosters.values():
                    roster.medical_quality = _clamp(roster.medical_quality + 0.020 * scale)
                effects.append(f"Medical monitoring and compensation cost ¥{cost:,.0f}.")
                effects.append("Commercial flexibility remained with moderate safety gains.")
            else:
                football.workload.congestion_multiplier = 1.14
                football.workload.international_release_cost = 5.2
                for club in state.clubs.values():
                    club.monthly_revenue *= 1.0 + 0.012 * scale
                effects.append("Commercial match inventory and club revenue increased.")
                effects.append("Congestion, injury and national-team release pressure increased.")

        elif agenda_id == "agenda_commercial_model":
            premier_ids = set(football.pyramid.premier_ids)
            if option_id == "solidarity_distribution":
                cost = spend(1_200_000.0)
                for club_id, club in state.clubs.items():
                    club.monthly_revenue *= 1.0 + (0.038 if club_id not in premier_ids else -0.010) * scale
                state.fan_trust = _clamp(state.fan_trust + 0.014 * scale)
                effects.append(f"Solidarity fund received ¥{cost:,.0f} from the association.")
                effects.append("Second-division revenues rose while top-flight growth slowed.")
            elif option_id == "star_club_growth":
                ranked = sorted(
                    state.clubs.values(),
                    key=lambda club: club.supporter_base,
                    reverse=True,
                )
                star_ids = {club.id for club in ranked[:3]}
                for club in state.clubs.values():
                    club.monthly_revenue *= 1.0 + (0.060 if club.id in star_ids else -0.008) * scale
                state.fan_trust = _clamp(state.fan_trust - 0.010 * scale)
                effects.append("Three star clubs received accelerated commercial rights.")
                effects.append("League revenue inequality and supporter tension increased.")
            else:
                for club_id, club in state.clubs.items():
                    club.monthly_revenue *= 1.0 + (0.020 if club_id not in premier_ids else 0.010) * scale
                    club.licensing_compliance = _clamp(club.licensing_compliance + 0.008 * scale)
                effects.append("Commercial growth was shared under financial guardrails.")
                effects.append("Both divisions received moderate recurring revenue growth.")

        elif agenda_id == "agenda_integrity_constitution":
            if option_id == "independent_integrity_unit":
                cost = spend(2_200_000.0)
                state.integrity_reputation = _clamp(state.integrity_reputation + 0.075 * scale)
                state.political_capital = _clamp(state.political_capital - 0.035 * scale)
                for region in state.regions.values():
                    region.integrity = _clamp(region.integrity + 0.065 * scale)
                    region.execution_capacity = _clamp(region.execution_capacity - 0.018 * scale)
                for club in state.clubs.values():
                    club.integrity = _clamp(club.integrity + 0.035 * scale)
                effects.append(f"Independent integrity unit cost ¥{cost:,.0f}.")
                effects.append("Integrity rose sharply while investigations slowed delivery.")
            elif option_id == "internal_compliance_office":
                cost = spend(650_000.0)
                state.integrity_reputation = _clamp(state.integrity_reputation + 0.035 * scale)
                for club in state.clubs.values():
                    club.licensing_compliance = _clamp(club.licensing_compliance + 0.018 * scale)
                effects.append(f"Internal compliance expansion cost ¥{cost:,.0f}.")
                effects.append("Audit coverage improved without an independent prosecutor.")
            else:
                state.political_capital = _clamp(state.political_capital + 0.022 * scale)
                state.integrity_reputation = _clamp(state.integrity_reputation - 0.060 * scale)
                for region in state.regions.values():
                    region.execution_capacity = _clamp(region.execution_capacity + 0.012 * scale)
                effects.append("Local delivery accelerated and political control tightened.")
                effects.append("Integrity reputation deteriorated sharply.")
        return tuple(effects)

    def _create_promise(
        self,
        agenda_id: str,
        option_id: str,
        month: int,
        state: NationalFootballSystem,
        football: Any,
    ) -> PoliticalPromise:
        specifications = {
            "central_command": ("integrity", 0.040, ("sports_ministry", "sponsor_council", "supporters_federation"), "Raise national integrity"),
            "federal_compact": ("execution", 0.022, ("education_ministry", "provincial_fas"), "Improve regional execution"),
            "local_devolution": ("execution", 0.035, ("provincial_fas",), "Deliver faster local implementation"),
            "player_welfare_compact": ("medical", 0.035, ("players_union",), "Raise club medical standards"),
            "managed_flexibility": ("league_finance", 0.015, ("club_owners", "finance_ministry"), "Improve league finances without labor breakdown"),
            "club_calendar_primacy": ("commercial", 0.025, ("club_owners", "broadcaster"), "Deliver commercial growth"),
            "solidarity_distribution": ("second_revenue", 0.022, ("provincial_fas", "supporters_federation"), "Grow second-division recurring revenue"),
            "star_club_growth": ("top_revenue", 0.035, ("club_owners", "broadcaster"), "Grow star-club commercial revenue"),
            "regulated_balance": ("league_finance", 0.018, ("finance_ministry", "supporters_federation"), "Improve league financial health"),
            "independent_integrity_unit": ("integrity", 0.055, ("sponsor_council", "supporters_federation"), "Deliver a measurable integrity recovery"),
            "internal_compliance_office": ("integrity", 0.025, ("sports_ministry", "sponsor_council"), "Improve integrity through internal compliance"),
            "protect_delivery": ("political_capital", 0.012, ("provincial_fas",), "Preserve delivery capacity and political control"),
        }
        metric, delta, beneficiaries, title = specifications[option_id]
        baseline = self._metric(metric, state, football)
        return PoliticalPromise(
            id=f"{agenda_id}:{month}",
            created_month=month,
            due_month=min(24, month + 8),
            title=title,
            metric=metric,
            baseline=baseline,
            target=baseline + delta,
            beneficiaries=beneficiaries,
        )

    def _evaluate_promises(
        self,
        month: int,
        state: NationalFootballSystem,
        football: Any,
    ) -> None:
        for promise in self.promises:
            if promise.status != "pending" or month < promise.due_month:
                continue
            actual = self._metric(promise.metric, state, football)
            promise.actual_value = actual
            promise.resolved_month = month
            promise.status = "kept" if actual >= promise.target else "broken"
            for actor_id in promise.beneficiaries:
                actor = self.stakeholders[actor_id]
                if promise.status == "kept":
                    actor.promises_kept += 1
                    actor.support = _clamp(actor.support + 0.035)
                    actor.trust = _clamp(actor.trust + 0.055)
                    note = f"promise kept: {promise.title}"
                else:
                    actor.promises_broken += 1
                    actor.support = _clamp(actor.support - 0.055)
                    actor.trust = _clamp(actor.trust - 0.080)
                    actor.mobilization = _clamp(actor.mobilization + 0.060)
                    note = f"promise broken: {promise.title}"
                actor.memory.append(
                    f"M{month}: {note}; target {promise.target:.3f}, actual {actual:.3f}"
                )
                actor.memory = actor.memory[-10:]
            self.event_history.append(
                PoliticalEvent(
                    month=month,
                    actor_id="presidency",
                    actor_name="主席办公室",
                    event_type="promise",
                    headline=f"Public promise {promise.status}: {promise.title}",
                    effects=(
                        f"Target {promise.target:.3f}; actual {actual:.3f}.",
                        "Beneficiary trust adjusted through persistent memory.",
                    ),
                )
            )

    @staticmethod
    def _metric(
        metric: str,
        state: NationalFootballSystem,
        football: Any,
    ) -> float:
        if metric == "integrity":
            return state.integrity_reputation
        if metric == "execution":
            return _average([region.execution_capacity for region in state.regions.values()])
        if metric == "medical":
            return _average([roster.medical_quality for roster in football.rosters.values()])
        if metric == "league_finance":
            return state.league_financial_health
        if metric == "commercial":
            return _average([club.monthly_revenue for club in state.clubs.values()]) / 10_000_000.0
        if metric == "second_revenue":
            return _average([
                state.clubs[club_id].monthly_revenue
                for club_id in football.pyramid.second_ids
            ]) / 10_000_000.0
        if metric == "top_revenue":
            ranked = sorted(
                state.clubs.values(),
                key=lambda club: club.supporter_base,
                reverse=True,
            )[:3]
            return _average([club.monthly_revenue for club in ranked]) / 10_000_000.0
        if metric == "political_capital":
            return state.political_capital
        raise ValueError(f"unknown political promise metric: {metric}")
