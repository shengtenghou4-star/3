"""A fixed-player football-association chairman career.

The simulation remains a deep multi-government world, but the player controls only the
opening chairman. Resignation, removal, electoral defeat or the term limit ends the
playable career. The world may continue in observer mode, with successor decisions
resolved by their own doctrines.

Hidden actor attributes remain in the simulation. This module exposes only briefings,
public records, confidence bands and broad political signals that a chairman could
reasonably receive.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy
from .patronage_runtime import CareerJusticeHistory


CHAIRMAN_SAVE_VERSION = 6


@dataclass(frozen=True, slots=True)
class BriefingItem:
    global_month: int
    category: str
    title: str
    summary: str
    source: str
    confidence: str
    urgency: str
    action_required: bool = False


@dataclass(frozen=True, slots=True)
class StakeholderSignal:
    actor_id: str
    actor_name: str
    posture: str
    trend: str
    confidence: str
    latest_message: str


@dataclass(frozen=True, slots=True)
class OfficialAssessment:
    office: str
    official_name: str
    delivery: str
    public_integrity_signal: str
    political_reliability: str
    information_basis: str


@dataclass(frozen=True, slots=True)
class ChairmanLegacyReport:
    chairman_name: str
    strategy: str
    start_global_month: int
    end_global_month: int
    months_in_office: int
    completed_terms: int
    exit_reason: str
    board_score: float
    political_score: float
    treasury: float
    fan_trust: float
    integrity_reputation: float
    national_team_strength: float
    qualifier_position: int
    league_champions_during_career: tuple[str, ...]
    cup_champions_during_career: tuple[str, ...]
    decisions_taken: int
    legacy_grade: str


class ChairmanCareer(CareerJusticeHistory):
    """Playable career for one fixed chairman with optional post-career observation."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        self._system_control = False
        self._briefing_history: list[BriefingItem] = []
        self._briefing_keys: set[str] = set()
        self._source_lengths: dict[str, int] = {}
        super().__init__(strategy=strategy, max_terms=max_terms)
        self.player_president_id = self.current_president.id
        self.player_name = self.current_president.name
        self.player_strategy = strategy
        self.player_start_month = self.global_month
        self.player_active = True
        self.career_end_month: int | None = None
        self.career_end_reason: str | None = None
        self.observer_mode = False
        self._legacy_report: ChairmanLegacyReport | None = None
        self._capture_briefings(opening=True)

    @property
    def player_decision(self):
        if not self.player_active:
            return None
        if self.current_president.id != self.player_president_id:
            return None
        return super().current_decision

    @property
    def briefings(self) -> tuple[BriefingItem, ...]:
        return tuple(self._briefing_history)

    @property
    def legacy_report(self) -> ChairmanLegacyReport | None:
        if self._legacy_report is None and not self.player_active:
            self._legacy_report = self._build_legacy_report()
        return self._legacy_report

    @property
    def can_observe(self) -> bool:
        return not self.player_active and not self.finished

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        if not self.player_active and not self._system_control:
            return
        remaining = months
        while remaining > 0 and not self.finished:
            if not self.player_active and not self._system_control:
                break
            before = self.global_month
            super().advance(1, interactive=interactive)
            elapsed = self.global_month - before
            self._capture_briefings()
            if elapsed == 0:
                break
            remaining -= elapsed
            if interactive and self.player_decision is not None:
                break

    def resolve_decision(self, option_id: str):
        if not self.player_active and not self._system_control:
            raise RuntimeError(
                "the playable chairman has left office; successor decisions are not controllable"
            )
        if (
            self.player_active
            and self.current_president.id != self.player_president_id
            and not self._system_control
        ):
            raise RuntimeError("the player cannot act for another president")
        record = super().resolve_decision(option_id)
        self._capture_briefings()
        return record

    def observe(self, months: int = 1) -> None:
        """Continue the football world after career end without controlling successors."""
        if self.player_active:
            raise RuntimeError("observer mode is available only after the chairman leaves office")
        if months < 0:
            raise ValueError("months cannot be negative")
        self.observer_mode = True
        self._system_control = True
        try:
            super().advance(months, interactive=False)
        finally:
            self._system_control = False
        self._capture_briefings()

    def finish_player_term(self) -> None:
        """Auto-apply the player's doctrine until the current term resolves or career ends."""
        start_term = self.term_index
        while (
            self.player_active
            and self.term_index == start_term
            and not self.finished
        ):
            decision = self.player_decision
            if decision is not None:
                self._auto_resolve_current()
            else:
                self.advance(1, interactive=True)

    def stakeholder_signals(self) -> tuple[StakeholderSignal, ...]:
        signals: list[StakeholderSignal] = []
        for actor in self.current_campaign.politics.stakeholders.values():
            relationship = 0.58 * actor.support + 0.42 * actor.trust
            posture = (
                "核心支持"
                if relationship >= 0.68
                else "倾向支持"
                if relationship >= 0.56
                else "摇摆观望"
                if relationship >= 0.44
                else "明显反对"
                if relationship >= 0.32
                else "积极施压"
            )
            trend = self._actor_trend(actor.memory)
            confidence = (
                "高"
                if actor.last_contact_month >= max(0, self.local_month - 2)
                else "中"
                if actor.last_contact_month >= max(0, self.local_month - 6)
                else "低"
            )
            message = actor.memory[-1] if actor.memory else "尚无正式表态"
            signals.append(
                StakeholderSignal(
                    actor.id,
                    actor.name,
                    posture,
                    trend,
                    confidence,
                    message,
                )
            )
        return tuple(signals)

    def official_assessments(self) -> tuple[OfficialAssessment, ...]:
        assessments: list[OfficialAssessment] = []
        for office, official in self.cabinet.items():
            person = self.people.get(official.id)
            delivery = (
                "表现突出"
                if official.competence >= 0.76
                else "基本可靠"
                if official.competence >= 0.60
                else "执行吃力"
            )
            disclosed = []
            if person is not None:
                disclosed = [
                    tie for tie in self._ties_for(person.id)
                    if tie.disclosed and tie.status == "active"
                ]
            public_risk = (
                "已出现严重公开风险"
                if official.scandal_points >= 0.55 or person and person.status in {"suspended", "convicted", "banned"}
                else "存在需要解释的公开关系"
                if disclosed or official.scandal_points >= 0.25
                else "暂无重大公开问题"
            )
            reliability = (
                "高度服从主席路线"
                if official.loyalty >= 0.76
                else "合作但保留自身立场"
                if official.loyalty >= 0.55
                else "立场独立，需持续沟通"
            )
            basis = (
                "工作交付、公开申报、审计记录与秘书处反馈；不包含未核实私人情报"
            )
            assessments.append(
                OfficialAssessment(
                    office,
                    official.name,
                    delivery,
                    public_risk,
                    reliability,
                    basis,
                )
            )
        return tuple(assessments)

    def public_case_docket(self) -> tuple[dict[str, Any], ...]:
        """Return public procedural facts, excluding hidden probability and network scores."""
        rows: list[dict[str, Any]] = []
        for case in reversed(self.justice_cases):
            rows.append(
                {
                    "case_id": case.id,
                    "subject": case.subject_name,
                    "allegation": case.allegation,
                    "route": case.route,
                    "stage": case.stage,
                    "outcome": case.outcome,
                    "appeal": case.appeal_status,
                    "opened_month": case.opened_global_month,
                    "closed_month": case.closed_global_month,
                }
            )
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = CHAIRMAN_SAVE_VERSION
        payload["player"] = {
            "president_id": self.player_president_id,
            "name": self.player_name,
            "strategy": self.player_strategy.value,
            "start_month": self.player_start_month,
            "active": self.player_active,
            "end_month": self.career_end_month,
            "end_reason": self.career_end_reason,
            "observer_mode": self.observer_mode,
        }
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChairmanCareer":
        if data.get("format_version") != CHAIRMAN_SAVE_VERSION:
            raise ValueError("unsupported chairman-career save format")
        player = data.get("player", {})
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        if player.get("president_id") != campaign.player_president_id:
            raise ValueError("save refers to a different opening chairman")
        target_month = int(data.get("global_month", 0))
        commands = list(data.get("decision_log", []))
        injections = list(data.get("injected_crises", []))
        command_index = 0
        injection_index = 0
        campaign._system_control = True
        try:
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
                CareerJusticeHistory.advance(campaign, 1, interactive=True)
                campaign._capture_briefings()
        finally:
            campaign._system_control = False
        if command_index != len(commands):
            raise ValueError("save contains unreachable chairman-career decisions")
        if injection_index != len(injections):
            raise ValueError("save contains unreachable scenario injections")
        campaign.observer_mode = bool(player.get("observer_mode", False))
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("chairman-career replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "ChairmanCareer":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "ChairmanCareer":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "player": {
                "id": getattr(self, "player_president_id", None),
                "active": getattr(self, "player_active", True),
                "end_month": getattr(self, "career_end_month", None),
                "end_reason": getattr(self, "career_end_reason", None),
                "observer": getattr(self, "observer_mode", False),
            },
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def _start_caretaker(self, reason: str) -> None:
        outgoing_id = self.current_president.id
        super()._start_caretaker(reason)
        if (
            hasattr(self, "player_president_id")
            and outgoing_id == self.player_president_id
        ):
            self._end_player_career(reason)

    def _rollover(self, bundle, president) -> None:
        incoming_id = president.id
        super()._rollover(bundle, president)
        if (
            hasattr(self, "player_president_id")
            and self.player_active
            and incoming_id != self.player_president_id
        ):
            reason = (
                self.term_records[-1].succession_reason
                if self.term_records
                else "failed to retain the presidency"
            )
            self._end_player_career(reason)

    def _end_player_career(self, reason: str) -> None:
        if not getattr(self, "player_active", False):
            return
        self.player_active = False
        self.career_end_month = self.global_month
        self.career_end_reason = reason
        self._legacy_report = self._build_legacy_report()
        self._add_briefing(
            BriefingItem(
                self.global_month,
                "生涯",
                "主席任期结束",
                f"你已不再担任国家足协主席：{reason}。此后只能旁观国家足球历史。",
                "全国足球代表大会与秘书处正式通知",
                "高",
                "最高",
                False,
            )
        )

    def _capture_briefings(self, *, opening: bool = False) -> None:
        if opening:
            self._add_briefing(
                BriefingItem(
                    0,
                    "就职",
                    "主席办公室正式启用",
                    "你将始终扮演本届足协主席。连任可继续执政；辞职、罢免、败选或任期限制将结束本局。",
                    "主席办公室",
                    "高",
                    "高",
                    False,
                )
            )
        self._capture_decision_briefing()
        self._capture_new_history_events()
        self._capture_system_warnings()
        self._capture_deterministic_rumor()

    def _capture_decision_briefing(self) -> None:
        decision = self.player_decision
        if decision is None:
            return
        self._add_briefing(
            BriefingItem(
                self.global_month,
                "待签文件",
                decision.title,
                decision.narrative,
                "秘书长呈报",
                "高",
                "最高",
                True,
            )
        )

    def _capture_new_history_events(self) -> None:
        sources = (
            ("constitutional", self.constitutional_history, "政治与制度", "秘书处与公开记录"),
            ("justice", self.justice_history, "纪律与司法", "廉洁专员公开通报"),
            ("career", self.career_history, "人事", "人事司任免公报"),
        )
        for key, items, category, source in sources:
            start = self._source_lengths.get(key, 0)
            for item in items[start:]:
                if key == "constitutional":
                    title = item.headline
                    summary = "；".join(item.effects)
                    urgency = "高" if item.severity >= 0.70 else "中"
                elif key == "justice":
                    title = item.headline
                    summary = "；".join(item.effects)
                    urgency = "高" if item.stage in {"charged", "appeal", "final"} else "中"
                else:
                    title = f"{item.person_name}：{item.event_type}"
                    summary = f"{item.institution} · {item.role}；{item.reason}"
                    urgency = "低"
                self._add_briefing(
                    BriefingItem(
                        self.global_month,
                        category,
                        title,
                        summary,
                        source,
                        "高",
                        urgency,
                        False,
                    )
                )
            self._source_lengths[key] = len(items)

    def _capture_system_warnings(self) -> None:
        state = self.current_campaign.engine.state
        distressed = [
            club for club in state.clubs.values()
            if club.wage_arrears_months >= 2 or club.license_status in {"administration", "excluded"}
        ]
        if distressed:
            names = "、".join(club.name for club in distressed[:4])
            self._add_briefing(
                BriefingItem(
                    self.global_month,
                    "职业联赛",
                    "俱乐部财务预警",
                    f"财务监管部门报告：{names}出现欠薪、托管或牌照风险。",
                    "财务与准入总监月报",
                    "高",
                    "高",
                    False,
                )
            )
        if state.treasury < 5_000_000:
            self._add_briefing(
                BriefingItem(
                    self.global_month,
                    "财政",
                    "足协可用资金进入警戒区",
                    "现有国库难以同时承担大规模救助、国家队突击投入和基层扩张。",
                    "财务与准入总监",
                    "高",
                    "高",
                    False,
                )
            )
        position = self.current_campaign.football.international.user_position
        if position >= 5:
            self._add_briefing(
                BriefingItem(
                    self.global_month,
                    "国家队",
                    "预选赛排名触发舆情风险",
                    f"国家队目前位列小组第{position}，媒体和赞助商正在提高问责压力。",
                    "国家队技术部门与媒体监测",
                    "高",
                    "高",
                    False,
                )
            )

    def _capture_deterministic_rumor(self) -> None:
        if self.global_month == 0 or self.global_month % 3 != 0:
            return
        hidden = [
            tie for tie in self.patronage_ties.values()
            if not tie.disclosed and tie.status == "active"
        ]
        if not hidden:
            return
        candidate = max(
            hidden,
            key=lambda tie: (
                tie.strength
                + self._hash_fraction(f"{self.global_month}:{tie.id}") * 0.18,
                tie.id,
            ),
        )
        reveal_score = candidate.strength + self._hash_fraction(
            f"rumor:{self.global_month}:{candidate.id}"
        ) * 0.20
        if reveal_score < 0.70:
            return
        source_person = self.people[candidate.source_id]
        target_person = self.people[candidate.target_id]
        confidence = "中" if reveal_score >= 0.84 else "低"
        self._add_briefing(
            BriefingItem(
                self.global_month,
                "非正式情报",
                "一条尚未证实的关系线索",
                f"有消息称{source_person.name}与{target_person.name}之间存在未充分申报的{candidate.kind}联系。当前材料不足以证明违法。",
                "秘书处综合记者询问与地方口风",
                confidence,
                "中",
                False,
            )
        )

    def _add_briefing(self, item: BriefingItem) -> None:
        key = hashlib.sha256(
            f"{item.global_month}|{item.category}|{item.title}|{item.summary}".encode("utf-8")
        ).hexdigest()
        if key in self._briefing_keys:
            return
        self._briefing_keys.add(key)
        self._briefing_history.append(item)

    def _build_legacy_report(self) -> ChairmanLegacyReport:
        state = self.current_campaign.engine.state
        board = self.current_campaign.board_review()
        political = self.current_campaign.political_review
        player_terms = [
            record for record in self.term_records
            if record.president_id == self.player_president_id
        ]
        decisions = sum(
            1 for command in self._decision_log
            if command["global_month"] <= (self.career_end_month or self.global_month)
        )
        league_champions = tuple(
            item.premier_champion
            for item in self.season_history
            if item.president_name == self.player_name
        )
        cup_champions = tuple(
            item.cup_champion
            for item in self.season_history
            if item.president_name == self.player_name
        )
        blended = 0.48 * board.score + 0.52 * political.score
        grade = (
            "历史级主席"
            if blended >= 78
            else "成功改革者"
            if blended >= 66
            else "有功有过"
            if blended >= 54
            else "未能稳住体系"
            if blended >= 42
            else "失败任期"
        )
        return ChairmanLegacyReport(
            chairman_name=self.player_name,
            strategy=self.player_strategy.value,
            start_global_month=self.player_start_month,
            end_global_month=self.career_end_month or self.global_month,
            months_in_office=(self.career_end_month or self.global_month) - self.player_start_month,
            completed_terms=len(player_terms),
            exit_reason=self.career_end_reason or "simulation horizon reached",
            board_score=board.score,
            political_score=political.score,
            treasury=state.treasury,
            fan_trust=state.fan_trust,
            integrity_reputation=state.integrity_reputation,
            national_team_strength=state.national_team_strength,
            qualifier_position=self.current_campaign.football.international.user_position,
            league_champions_during_career=league_champions,
            cup_champions_during_career=cup_champions,
            decisions_taken=decisions,
            legacy_grade=grade,
        )

    @staticmethod
    def _actor_trend(memory: list[str]) -> str:
        recent = " ".join(memory[-3:]).lower()
        positive = sum(word in recent for word in ("kept", "joined", "support", "兑现", "支持"))
        negative = sum(word in recent for word in ("broken", "opposed", "pressure", "违约", "反对"))
        return "改善" if positive > negative else "恶化" if negative > positive else "稳定"

    @staticmethod
    def _hash_fraction(value: str) -> float:
        raw = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        return int(raw, 16) / float(16**12 - 1)
