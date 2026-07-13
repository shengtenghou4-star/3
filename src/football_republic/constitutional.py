"""Appointments, constitutional crises and mid-term presidential transitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy, _AUTO_CHOICES
from .governance import DecisionOption, DecisionRecord, GovernanceDecision
from .long_term import LongTermCampaign, PresidentProfile


CONSTITUTIONAL_SAVE_VERSION = 2


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(slots=True)
class OfficialProfile:
    id: str
    name: str
    office: str
    style: str
    competence: float
    integrity: float
    loyalty: float
    network_power: float
    appointed_global_month: int
    appointed_by: str
    status: str = "serving"
    scandal_points: float = 0.0


@dataclass(frozen=True, slots=True)
class AppointmentRecord:
    global_month: int
    term: int
    president_name: str
    office: str
    outgoing_name: str
    incoming_name: str
    style: str
    reason: str


@dataclass(frozen=True, slots=True)
class ConstitutionalEvent:
    global_month: int
    local_month: int
    term: int
    event_type: str
    headline: str
    severity: float
    effects: tuple[str, ...]


@dataclass(slots=True)
class AdministrationSpan:
    term: int
    president_id: str
    president_name: str
    strategy: str
    start_global_month: int
    entry_reason: str
    status: str = "active"
    end_global_month: int | None = None
    exit_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CrisisContext:
    decision_id: str
    official_id: str
    severity: float
    allegation: str


class ConstitutionalLongTermCampaign(LongTermCampaign):
    """Long history where cabinets, scandals and governments can change mid-term."""

    OFFICES = (
        "秘书长",
        "财务与准入总监",
        "廉洁与纪律专员",
        "国家队技术总监",
        "青训与校园足球专员",
    )
    CANDIDATE_NAMES = {
        "秘书长": ("许闻达", "罗敬之", "秦闻韬", "苏立言", "谢明川"),
        "财务与准入总监": ("顾廷川", "叶清远", "唐惟实", "赵珩", "沈砺"),
        "廉洁与纪律专员": ("林若衡", "乔谨言", "周砚秋", "方正仪", "韩肃"),
        "国家队技术总监": ("蒋云锋", "陆启航", "温绍钧", "严北辰", "贺远山"),
        "青训与校园足球专员": ("陶知行", "程雨生", "孟新野", "梁嘉禾", "宋望川"),
    }
    CHECKPOINTS = (5, 9, 13, 17, 21)

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        super().__init__(strategy=strategy, max_terms=max_terms)
        self.cabinet: dict[str, OfficialProfile] = {}
        self.appointment_history: list[AppointmentRecord] = []
        self.constitutional_history: list[ConstitutionalEvent] = []
        self.administration_history: list[AdministrationSpan] = []
        self._pending_constitutional: list[GovernanceDecision] = []
        self._crisis_context: dict[str, CrisisContext] = {}
        self._triggered_checkpoints: set[tuple[int, int]] = set()
        self._constitutional_strikes = 0
        self._caretaker_until: int | None = None
        self._decision_log: list[dict[str, Any]] = []
        self._appoint_full_cabinet("founding administration")
        self._start_administration("inaugural mandate")

    @property
    def current_decision(self):
        if self._pending_constitutional:
            return self._pending_constitutional[0]
        return super().current_decision

    @property
    def caretaker_active(self) -> bool:
        return self.current_president.status == "caretaker"

    @property
    def cabinet_quality(self) -> float:
        if not self.cabinet:
            return 0.0
        return sum(item.competence for item in self.cabinet.values()) / len(self.cabinet)

    @property
    def cabinet_integrity(self) -> float:
        if not self.cabinet:
            return 0.0
        return sum(item.integrity for item in self.cabinet.values()) / len(self.cabinet)

    @property
    def capture_risk(self) -> float:
        if not self.cabinet:
            return 0.0
        return sum(
            item.network_power * item.loyalty * (1.0 - item.integrity)
            for item in self.cabinet.values()
        ) / len(self.cabinet)

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
            if self.caretaker_active and self._caretaker_until is not None:
                if self.global_month >= self._caretaker_until:
                    self._hold_snap_election()
            before_global = self.global_month
            before_term = self.term_index
            self._apply_monthly_cabinet_effects(self.global_month + 1)
            super().advance(1, interactive=True)
            elapsed = self.global_month - before_global
            if elapsed == 0:
                break
            remaining -= elapsed
            if self.term_index == before_term:
                self._maybe_trigger_crisis()
            if interactive and self.current_decision is not None:
                break

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no pending decision")
        if self._pending_constitutional and decision.id == self._pending_constitutional[0].id:
            record = self._resolve_constitutional(decision, option_id)
        else:
            record = super().resolve_decision(option_id)
        self._decision_log.append(
            {
                "global_month": self.global_month,
                "term": self.term_index,
                "decision_id": decision.id,
                "option_id": option_id,
            }
        )
        return record

    def force_crisis(
        self,
        *,
        office: str = "廉洁与纪律专员",
        severity: float = 0.86,
        allegation: str = "审计文件显示利益输送与隐瞒关联交易",
    ) -> GovernanceDecision:
        if office not in self.cabinet:
            raise ValueError(f"unknown office: {office}")
        return self._open_crisis(self.cabinet[office], _clamp(severity), allegation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": CONSTITUTIONAL_SAVE_VERSION,
            "max_terms": self.max_terms,
            "initial_strategy": self.initial_strategy.value,
            "global_month": self.global_month,
            "decision_log": list(self._decision_log),
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
    def from_dict(cls, data: dict[str, Any]) -> "ConstitutionalLongTermCampaign":
        if data.get("format_version") != CONSTITUTIONAL_SAVE_VERSION:
            raise ValueError("unsupported constitutional save format")
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        target_month = int(data.get("global_month", 0))
        commands = list(data.get("decision_log", []))
        command_index = 0
        while campaign.global_month < target_month or command_index < len(commands):
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
            raise ValueError("save contains unreachable constitutional decisions")
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("constitutional save replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "ConstitutionalLongTermCampaign":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "ConstitutionalLongTermCampaign":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "cabinet": [
                asdict(item)
                for item in sorted(self.cabinet.values(), key=lambda actor: actor.office)
            ],
            "appointments": [asdict(item) for item in self.appointment_history],
            "constitutional_events": [asdict(item) for item in self.constitutional_history],
            "administrations": [asdict(item) for item in self.administration_history],
            "caretaker_until": self._caretaker_until,
            "strikes": self._constitutional_strikes,
            "pending_constitutional": (
                self._pending_constitutional[0].id if self._pending_constitutional else None
            ),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def _auto_resolve_current(self) -> None:
        decision = self.current_decision
        if decision is None:
            return
        if decision.id.startswith("constitutional_crisis_"):
            context = self._crisis_context[decision.id]
            if self.current_president.strategy == Strategy.FOUNDATIONS:
                option = "independent_inquiry"
            elif self.current_president.strategy == Strategy.QUICK_RESULTS:
                option = (
                    "submit_resignation"
                    if context.severity >= 0.86
                    else "protect_inner_circle"
                )
            else:
                option = "cabinet_reshuffle"
        elif decision.id.startswith("agenda_"):
            option = self.current_campaign.politics.auto_choice(
                decision.id,
                self.current_president.strategy.value,
            )
        else:
            option = _AUTO_CHOICES[self.current_president.strategy][decision.id]
        self.resolve_decision(option)

    def _apply_monthly_cabinet_effects(self, target_global_month: int) -> None:
        if not self.cabinet:
            return
        state = self.current_campaign.engine.state
        secretary = self.cabinet["秘书长"]
        finance = self.cabinet["财务与准入总监"]
        integrity = self.cabinet["廉洁与纪律专员"]
        technical = self.cabinet["国家队技术总监"]
        grassroots = self.cabinet["青训与校园足球专员"]

        admin_delta = (secretary.competence - 0.62) * 0.0018
        state.political_capital = _clamp(state.political_capital + admin_delta)
        for region in state.regions.values():
            region.execution_capacity = _clamp(
                region.execution_capacity + admin_delta * 0.45
            )

        fiscal_gain = 22_000.0 * (finance.competence - 0.52)
        leakage = 16_000.0 * finance.network_power * (1.0 - finance.integrity)
        state.treasury = max(0.0, state.treasury + fiscal_gain - leakage)
        state.league_financial_health = _clamp(
            state.league_financial_health
            + 0.0008 * (finance.competence - 0.55)
        )

        integrity_delta = 0.0014 * (integrity.integrity - 0.58)
        state.integrity_reputation = _clamp(
            state.integrity_reputation + integrity_delta
        )
        state.national_team_strength = _clamp(
            state.national_team_strength
            + 0.025 * (technical.competence - 0.58),
            0.0,
            100.0,
        )
        for region in state.regions.values():
            region.parent_support = _clamp(
                region.parent_support
                + 0.0008 * (grassroots.competence - 0.55)
            )

        for official in self.cabinet.values():
            official.scandal_points = _clamp(
                official.scandal_points
                + 0.012 * (1.0 - official.integrity)
                + 0.008 * max(
                    0.0,
                    official.network_power + official.loyalty - 1.25,
                ),
                0.0,
                1.0,
            )
        self.current_campaign.engine.audit_log.append(
            f"G{target_global_month}: cabinet quality {self.cabinet_quality:.2f}; "
            f"capture risk {self.capture_risk:.2f}"
        )

    def _maybe_trigger_crisis(self) -> None:
        if self.caretaker_active or self.current_decision is not None:
            return
        local_month = self.local_month
        key = (self.term_index, local_month)
        if local_month not in self.CHECKPOINTS or key in self._triggered_checkpoints:
            return
        self._triggered_checkpoints.add(key)
        official = max(
            self.cabinet.values(),
            key=lambda actor: (
                actor.scandal_points
                + actor.network_power * actor.loyalty * (1.0 - actor.integrity)
            ),
        )
        politics = self.current_campaign.politics
        state = self.current_campaign.engine.state
        severity = _clamp(
            0.28 * (1.0 - self.current_president.integrity)
            + 0.25 * (1.0 - official.integrity)
            + 0.16 * official.network_power
            + 0.13 * (1.0 - politics.coalition_support)
            + 0.10 * (1.0 - state.integrity_reputation)
            + 0.18 * official.scandal_points
            + 0.07 * self._constitutional_strikes
        )
        threshold = (
            0.57
            if self.current_president.strategy == Strategy.QUICK_RESULTS
            else 0.65
            if self.current_president.strategy == Strategy.BALANCED
            else 0.70
        )
        if severity < threshold:
            return
        allegation = (
            f"媒体披露{official.name}利用{official.office}的审批权，"
            "与地方项目和俱乐部投资人形成未申报关系网"
        )
        self._open_crisis(official, severity, allegation)

    def _open_crisis(
        self,
        official: OfficialProfile,
        severity: float,
        allegation: str,
    ) -> GovernanceDecision:
        decision_id = (
            f"constitutional_crisis_{self.term_index}_{self.local_month}_{official.id}"
        )
        options = [
            DecisionOption(
                "independent_inquiry",
                "停职并交独立调查",
                "暂停涉事官员职务，由外部调查组接管证据和利益申报。",
                "忠诚派反弹、短期行政停滞和更多材料外泄",
            ),
            DecisionOption(
                "cabinet_reshuffle",
                "内阁改组并政治止损",
                "更换涉事官员，以跨派系人选修复联盟，但保留内部处置空间。",
                "可能被批评为换人不换制度",
            ),
            DecisionOption(
                "protect_inner_circle",
                "保护核心班底",
                "否认系统性问题并维持原班人马，确保短期执行和忠诚。",
                "廉洁声誉、赞助和议会信任可能继续恶化",
            ),
        ]
        if severity >= 0.76:
            options.append(
                DecisionOption(
                    "submit_resignation",
                    "承担政治责任并辞职",
                    "主席辞职，由看守政府维持运行并在三个月内提前选举。",
                    "权力真空、政策冻结和继任路线不可控",
                )
            )
        decision = GovernanceDecision(
            id=decision_id,
            month=self.local_month,
            title=f"宪政危机：{official.office}关系网曝光",
            narrative=(
                f"{allegation}。反对派要求主席解释是否知情，赞助商和财政部门"
                "要求立即处理。若联盟继续流失，主席可能无法完成本届任期。"
            ),
            options=tuple(options),
        )
        self._pending_constitutional.append(decision)
        self._crisis_context[decision_id] = CrisisContext(
            decision_id,
            official.id,
            severity,
            allegation,
        )
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "scandal exposed",
                decision.title,
                severity,
                (allegation,),
            )
        )
        return decision

    def _resolve_constitutional(
        self,
        decision: GovernanceDecision,
        option_id: str,
    ) -> DecisionRecord:
        option = next((item for item in decision.options if item.id == option_id), None)
        if option is None:
            raise ValueError(f"unknown option {option_id!r}")
        context = self._crisis_context[decision.id]
        official = next(
            actor for actor in self.cabinet.values() if actor.id == context.official_id
        )
        state = self.current_campaign.engine.state
        politics = self.current_campaign.politics
        effects: list[str] = []

        if option_id == "independent_inquiry":
            old_name = official.name
            official.status = "suspended and referred"
            self._replace_official(official.office, "technocrat", "independent inquiry")
            state.integrity_reputation = _clamp(state.integrity_reputation + 0.045)
            state.political_capital = _clamp(state.political_capital - 0.030)
            self.current_president.integrity = _clamp(
                self.current_president.integrity + 0.018
            )
            self._react_blocs(
                positive=("sponsor_council", "supporters_federation", "finance_ministry"),
                negative=("club_owners", "provincial_fas"),
                amount=0.045,
            )
            self._constitutional_strikes = max(0, self._constitutional_strikes - 1)
            effects.extend(
                (
                    f"{old_name} was suspended and replaced by an independent technocrat.",
                    "Integrity and sponsor confidence improved, while administrative continuity weakened.",
                )
            )
            if context.severity >= 0.90 and politics.coalition_support < 0.30:
                effects.append("The inquiry could not restore a collapsed governing majority.")
                self._start_caretaker("coalition collapsed during independent inquiry")

        elif option_id == "cabinet_reshuffle":
            old_name = official.name
            official.status = "removed in reshuffle"
            self._replace_official(official.office, "broker", "coalition reshuffle")
            state.integrity_reputation = _clamp(state.integrity_reputation + 0.014)
            state.political_capital = _clamp(state.political_capital - 0.012)
            self._react_blocs(
                positive=("provincial_fas", "broadcaster"),
                negative=("supporters_federation",),
                amount=0.022,
            )
            effects.extend(
                (
                    f"{old_name} left office in a negotiated cabinet reshuffle.",
                    "The coalition stabilized, but the underlying investigation remained internal.",
                )
            )

        elif option_id == "protect_inner_circle":
            official.loyalty = _clamp(official.loyalty + 0.06)
            official.network_power = _clamp(official.network_power + 0.04)
            official.scandal_points = _clamp(official.scandal_points + 0.10)
            state.integrity_reputation = _clamp(state.integrity_reputation - 0.050)
            state.political_capital = _clamp(state.political_capital + 0.025)
            self.current_president.integrity = _clamp(
                self.current_president.integrity - 0.035
            )
            self._react_blocs(
                positive=("club_owners", "provincial_fas"),
                negative=(
                    "sponsor_council",
                    "supporters_federation",
                    "finance_ministry",
                    "players_union",
                ),
                amount=0.055,
            )
            self._constitutional_strikes += 1
            effects.extend(
                (
                    "The president retained the implicated official and attacked the allegations.",
                    "Short-term control improved while capture risk and opposition mobilization increased.",
                )
            )
            if context.severity >= 0.74 or self._constitutional_strikes >= 2:
                effects.append("A no-confidence majority formed and forced the president from office.")
                self._start_caretaker("no-confidence vote after protecting the inner circle")

        elif option_id == "submit_resignation":
            effects.append("The president accepted political responsibility and resigned.")
            self._start_caretaker("voluntary resignation during constitutional crisis")

        self._pending_constitutional.pop(0)
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "crisis resolved",
                f"{decision.title} — {option.title}",
                context.severity,
                tuple(effects),
            )
        )
        record = DecisionRecord(
            decision_id=decision.id,
            month=self.local_month,
            title=decision.title,
            option_id=option.id,
            option_title=option.title,
            effects=tuple(effects),
        )
        self.current_campaign.engine.audit_log.append(
            f"G{self.global_month}: constitutional decision — {option.title}"
        )
        return record

    def _start_caretaker(self, reason: str) -> None:
        if self.caretaker_active:
            return
        self._close_administration(reason, "resigned")
        outgoing = self.current_president
        outgoing.status = "resigned"
        secretary = self.cabinet["秘书长"]
        caretaker = PresidentProfile(
            id=f"caretaker-{self.term_index}-{self.global_month}",
            name=f"{secretary.name}（看守）",
            strategy=Strategy.BALANCED,
            coalition_skill=0.48 + 0.22 * secretary.competence,
            administrative_skill=secretary.competence,
            integrity=secretary.integrity,
            first_term=self.term_index,
            terms_served=0,
            status="caretaker",
        )
        self.presidents.append(caretaker)
        self.current_president = caretaker
        self.current_campaign.strategy = Strategy.BALANCED
        state = self.current_campaign.engine.state
        state.political_capital = min(state.political_capital, 0.28)
        self._caretaker_until = min(self.term_index * 24, self.global_month + 3)
        self._start_administration(reason)
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "caretaker government",
                f"{caretaker.name} formed a caretaker administration",
                0.82,
                (
                    "Major discretionary appointments were frozen.",
                    f"A snap election was scheduled by global month {self._caretaker_until}.",
                ),
            )
        )

    def _hold_snap_election(self) -> None:
        if not self.caretaker_active:
            return
        self._close_administration("snap election completed", "caretaker ended")
        caretaker = self.current_president
        caretaker.status = "left office"
        successor = self._snap_successor()
        self.presidents.append(successor)
        self.current_president = successor
        self.current_campaign.strategy = successor.strategy
        state = self.current_campaign.engine.state
        state.political_capital = _clamp(
            0.38 + 0.22 * self.current_campaign.politics.coalition_support
        )
        for actor in self.current_campaign.politics.stakeholders.values():
            actor.support = 0.64 * actor.support + 0.36 * 0.50
            actor.trust = 0.78 * actor.trust + 0.22 * 0.50
            actor.mobilization *= 0.58
            actor.memory.append(
                f"G{self.global_month}: snap election brought {successor.name} to office"
            )
        self._caretaker_until = None
        self._constitutional_strikes = 0
        self._appoint_full_cabinet("snap-election mandate")
        self._start_administration("snap-election victory")
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "snap election",
                f"{successor.name} won the early presidential convention",
                0.45,
                (
                    f"New governing route: {successor.strategy.value}.",
                    "The league calendar and all club obligations continued without reset.",
                ),
            )
        )

    def _snap_successor(self) -> PresidentProfile:
        state = self.current_campaign.engine.state
        if state.integrity_reputation < 0.48:
            strategy = Strategy.FOUNDATIONS
        elif state.national_team_strength < 48.0 and state.fan_trust < 0.45:
            strategy = Strategy.QUICK_RESULTS
        else:
            strategy = Strategy.BALANCED
        index = (len(self.presidents) + self.term_index) % len(self.PRESIDENT_NAMES)
        return PresidentProfile(
            id=f"snap-{self.term_index}-{self.global_month}-{strategy.value}",
            name=self.PRESIDENT_NAMES[index],
            strategy=strategy,
            coalition_skill=0.56 + 0.025 * (index % 4),
            administrative_skill=0.55 + 0.025 * ((index + 2) % 4),
            integrity=0.62 if strategy != Strategy.QUICK_RESULTS else 0.52,
            first_term=self.term_index,
            terms_served=1,
            status="incumbent",
        )

    def _appoint_full_cabinet(self, reason: str) -> None:
        if self.current_president.strategy == Strategy.FOUNDATIONS:
            default_style = "technocrat"
        elif self.current_president.strategy == Strategy.QUICK_RESULTS:
            default_style = "loyalist"
        else:
            default_style = "broker"
        for office in self.OFFICES:
            style = default_style
            if office == "廉洁与纪律专员" and default_style == "broker":
                style = "technocrat"
            if office == "财务与准入总监" and default_style == "loyalist":
                style = "broker"
            self._replace_official(office, style, reason)

    def _replace_official(self, office: str, style: str, reason: str) -> OfficialProfile:
        outgoing = self.cabinet.get(office)
        if outgoing is not None and outgoing.status == "serving":
            outgoing.status = "replaced"
        incoming = self._candidate(office, style)
        self.cabinet[office] = incoming
        self.appointment_history.append(
            AppointmentRecord(
                self.global_month,
                self.term_index,
                self.current_president.name,
                office,
                outgoing.name if outgoing else "—",
                incoming.name,
                style,
                reason,
            )
        )
        return incoming

    def _candidate(self, office: str, style: str) -> OfficialProfile:
        names = self.CANDIDATE_NAMES[office]
        index = (
            self.term_index
            + self.global_month
            + len(self.appointment_history)
            + self.OFFICES.index(office)
        ) % len(names)
        if style == "technocrat":
            competence, integrity, loyalty, network = 0.82, 0.81, 0.46, 0.38
        elif style == "loyalist":
            competence, integrity, loyalty, network = 0.63, 0.47, 0.92, 0.78
        else:
            competence, integrity, loyalty, network = 0.71, 0.64, 0.68, 0.76
        office_adjust = {
            "秘书长": (0.04, -0.02, 0.03, 0.03),
            "财务与准入总监": (0.03, 0.01, -0.01, 0.02),
            "廉洁与纪律专员": (-0.01, 0.07, -0.05, -0.08),
            "国家队技术总监": (0.05, -0.02, 0.00, 0.02),
            "青训与校园足球专员": (0.02, 0.02, -0.01, -0.03),
        }[office]
        competence = _clamp(competence + office_adjust[0])
        integrity = _clamp(integrity + office_adjust[1])
        loyalty = _clamp(loyalty + office_adjust[2])
        network = _clamp(network + office_adjust[3])
        return OfficialProfile(
            id=f"official-{self.term_index}-{self.global_month}-{office}-{index}-{style}",
            name=names[index],
            office=office,
            style=style,
            competence=competence,
            integrity=integrity,
            loyalty=loyalty,
            network_power=network,
            appointed_global_month=self.global_month,
            appointed_by=self.current_president.name,
        )

    def _react_blocs(
        self,
        *,
        positive: tuple[str, ...],
        negative: tuple[str, ...],
        amount: float,
    ) -> None:
        actors = self.current_campaign.politics.stakeholders
        for actor_id in positive:
            actor = actors[actor_id]
            actor.support = _clamp(actor.support + amount)
            actor.trust = _clamp(actor.trust + amount * 0.8)
            actor.mobilization = _clamp(actor.mobilization - amount * 0.5)
        for actor_id in negative:
            actor = actors[actor_id]
            actor.support = _clamp(actor.support - amount)
            actor.trust = _clamp(actor.trust - amount * 0.65)
            actor.mobilization = _clamp(actor.mobilization + amount * 0.7)

    def _start_administration(self, entry_reason: str) -> None:
        self.administration_history.append(
            AdministrationSpan(
                term=self.term_index,
                president_id=self.current_president.id,
                president_name=self.current_president.name,
                strategy=self.current_president.strategy.value,
                start_global_month=self.global_month,
                entry_reason=entry_reason,
            )
        )

    def _close_administration(self, exit_reason: str, status: str) -> None:
        if not self.administration_history:
            return
        active = self.administration_history[-1]
        if active.end_global_month is not None:
            return
        active.end_global_month = self.global_month
        active.exit_reason = exit_reason
        active.status = status

    def _select_successor(self, board_score: float, political_score: float):
        if self.caretaker_active:
            caretaker = self.current_president
            caretaker.status = "left office"
            successor = self._snap_successor()
            return successor, "caretaker mandate expired at scheduled term boundary"
        return super()._select_successor(board_score, political_score)

    def _finalize_and_rollover(self) -> None:
        if self.term_index not in self._finalized_terms:
            self._close_administration("scheduled term boundary", "term completed")
        super()._finalize_and_rollover()

    def _rollover(self, bundle, president: PresidentProfile) -> None:
        old_president_id = self.current_president.id
        old_cabinet = self.cabinet
        super()._rollover(bundle, president)
        same_president = president.id == old_president_id
        if same_president:
            self.cabinet = old_cabinet
            for official in self.cabinet.values():
                official.loyalty = _clamp(official.loyalty + 0.015)
                official.scandal_points *= 0.82
        else:
            self.cabinet = {}
            self._appoint_full_cabinet("new scheduled administration")
        self._caretaker_until = None
        self._constitutional_strikes = 0
        self._start_administration(
            "coalition renewal" if same_president else "scheduled succession"
        )
