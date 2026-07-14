"""Named implementation, competing advice and live press follow-ups.

A presidential signature opens an administrative mandate; it does not magically finish
policy. The chairman must choose a named office-holder, decide how tightly to instruct
that person and then judge implementation through incomplete, competing reports.

The player never receives hidden competence formulas or distortion scores. Those values
exist only to make named officials causal rather than decorative.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .executive_president_career import ExecutivePresidentCareerGame


EXECUTIVE_FOLLOWUP_VERSION = 1


@dataclass(slots=True)
class ImplementationMandate:
    id: str
    created_month: int
    decision_id: str
    option_id: str
    option_title: str
    subject: str
    recommended_offices: tuple[str, ...]
    assigned_office: str | None = None
    assigned_official_id: str | None = None
    assigned_official_name: str | None = None
    instruction_style: str | None = None
    due_month: int | None = None
    progress: float = 0.0
    status: str = "awaiting_assignment"
    public_update: str = "主席已经签署决定，但尚未指定一名具名负责人。"
    hidden_delivery_quality: float = 0.0
    hidden_distortion: float = 0.0
    penalty_applied: bool = False
    outcome_applied: bool = False
    effects: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CompetingImplementationReport:
    id: str
    global_month: int
    mandate_id: str
    office: str
    official_name: str
    headline: str
    recommendation: str
    evidence: str
    blind_spot: str
    confidence: str
    urgency: str


@dataclass(frozen=True, slots=True)
class PressExchange:
    round_number: int
    question: str
    answer_style: str
    quote: str
    reporter_followup: str | None
    consequence: str


@dataclass(slots=True)
class PressConferenceSession:
    id: str
    global_month: int
    outlet: str
    topic: str
    current_question: str
    max_rounds: int = 3
    status: str = "open"
    exchanges: list[PressExchange] = field(default_factory=list)


class ExecutiveFollowupRuntime:
    """Long-lived implementation and press-conference layer."""

    INSTRUCTION_STYLES = {
        "tight": {
            "label": "严格照批示执行",
            "clarity": 0.95,
            "speed": 0.05,
            "distortion": -0.05,
            "political_flexibility": -0.08,
        },
        "outcome": {
            "label": "只规定结果，授权部门选择手段",
            "clarity": 0.68,
            "speed": 0.08,
            "distortion": 0.04,
            "political_flexibility": 0.04,
        },
        "coalition": {
            "label": "边执行边与相关集团协商",
            "clarity": 0.56,
            "speed": -0.02,
            "distortion": 0.08,
            "political_flexibility": 0.12,
        },
    }

    OFFICE_KEYWORDS = {
        "秘书长": ("协调", "联盟", "承诺", "治理", "代表大会", "媒体"),
        "财务与准入总监": ("预算", "救助", "俱乐部", "财务", "准入", "转会", "工资"),
        "廉洁与纪律专员": ("调查", "廉洁", "纪律", "腐败", "审计", "程序"),
        "国家队技术总监": ("国家队", "教练", "预选赛", "成绩", "集训", "球员"),
        "青训与校园足球专员": ("青训", "校园", "基层", "本土", "教练培养", "地方"),
    }

    OFFICE_ARGUMENTS = {
        "秘书长": (
            "强调跨部门口径、政治可执行性和代表大会支持。",
            "可能把维持协调权包装成维护主席稳定。",
        ),
        "财务与准入总监": (
            "强调付款来源、停止条件、监管一致性和俱乐部偿付能力。",
            "可能低估社会与竞技后果，把问题缩成资产负债表。",
        ),
        "廉洁与纪律专员": (
            "强调留痕、独立程序、利益冲突隔离和未来审计。",
            "可能高估程序纯度，低估足球系统立即运行的现实压力。",
        ),
        "国家队技术总监": (
            "强调竞技窗口、教练稳定、球员负荷和技术连续性。",
            "可能把成绩部门的资源需求描述成整个国家足球的唯一优先级。",
        ),
        "青训与校园足球专员": (
            "强调地方能力、教练质量、人才周期和长期机会成本。",
            "可能把任何短期调整都解释为对长期建设的挤压。",
        ),
    }

    PRESS_LABELS = {
        "rules_first": "规则与程序",
        "support_sector": "行业支持",
        "transparent_uncertainty": "承认未知",
        "no_comment": "不评论",
    }

    def __init__(self) -> None:
        self.mandates: list[ImplementationMandate] = []
        self.reports: list[CompetingImplementationReport] = []
        self.press_sessions: list[PressConferenceSession] = []
        self._processed_months: set[int] = set()
        self._report_keys: set[str] = set()

    def open_mandate(
        self,
        game: "ExecutivePresidentCareerGame",
        *,
        decision_id: str,
        option_id: str,
        option_title: str,
        subject: str,
    ) -> ImplementationMandate:
        mandate_id = _stable_id(
            "mandate",
            str(game.global_month),
            decision_id,
            option_id,
        )
        existing = next((item for item in self.mandates if item.id == mandate_id), None)
        if existing is not None:
            return existing
        recommended = self._recommended_offices(f"{subject} {option_title}")
        mandate = ImplementationMandate(
            id=mandate_id,
            created_month=game.global_month,
            decision_id=decision_id,
            option_id=option_id,
            option_title=option_title,
            subject=subject,
            recommended_offices=recommended,
        )
        self.mandates.append(mandate)
        game.world.apply_external_action(
            "implementation_mandate_opened",
            {
                "audit_note": (
                    f"implementation mandate {mandate_id} opened for "
                    f"{decision_id}/{option_id}; chairman must name an owner"
                )
            },
        )
        self._generate_competing_reports(game, mandate)
        return mandate

    def assign_mandate(
        self,
        game: "ExecutivePresidentCareerGame",
        *,
        mandate_id: str,
        office: str,
        instruction_style: str,
    ) -> ImplementationMandate:
        mandate = self._mandate(mandate_id)
        if mandate.status in {"completed", "partial", "failed", "withdrawn"}:
            raise ValueError("completed implementation mandates cannot be reassigned")
        if office not in game.world.cabinet:
            raise ValueError(f"unknown cabinet office {office!r}")
        if instruction_style not in self.INSTRUCTION_STYLES:
            raise ValueError(f"unknown instruction style {instruction_style!r}")

        official = game.world.cabinet[office]
        previous_office = mandate.assigned_office
        fit = 1.0 if office in mandate.recommended_offices else 0.48
        mandate.assigned_office = office
        mandate.assigned_official_id = official.id
        mandate.assigned_official_name = official.name
        mandate.instruction_style = instruction_style
        mandate.due_month = game.global_month + (3 if instruction_style != "coalition" else 4)
        mandate.status = "assigned"
        mandate.public_update = (
            f"{official.name}已接受牵头责任；主席要求其"
            f"{self.INSTRUCTION_STYLES[instruction_style]['label']}。"
        )
        mandate.effects.append(
            f"G{game.global_month}：主席将“{mandate.option_title}”交由{official.name}牵头。"
        )

        official_deltas: list[dict[str, Any]] = [
            {
                "official_id": official.id,
                "loyalty": 0.012 if fit >= 0.9 else -0.006,
                "scandal_points": 0.004 if instruction_style == "coalition" else 0.0,
            }
        ]
        if previous_office and previous_office != office:
            old = game.world.cabinet.get(previous_office)
            if old is not None:
                official_deltas.append(
                    {
                        "official_id": old.id,
                        "loyalty": -0.016,
                        "network_power": 0.004,
                    }
                )
                game.office.staff_grievance[previous_office] = _clamp(
                    game.office.staff_grievance.get(previous_office, 0.0) + 0.08
                )
        if office not in mandate.recommended_offices:
            mandate.effects.append("责任人与事项专业归口不完全匹配，秘书处已标记执行风险。")

        game.world.apply_external_action(
            "implementation_assignment",
            {
                "official_deltas": official_deltas,
                "audit_note": (
                    f"mandate {mandate_id} assigned to {official.id}/{office} "
                    f"with {instruction_style} instruction"
                ),
            },
        )
        self._generate_competing_reports(game, mandate, force=True)
        return mandate

    def advance_month(self, game: "ExecutivePresidentCareerGame") -> None:
        if game.global_month in self._processed_months:
            return
        self._processed_months.add(game.global_month)
        for mandate in self.mandates:
            if mandate.status in {"completed", "partial", "failed", "withdrawn"}:
                continue
            if mandate.assigned_office is None:
                self._advance_unassigned(game, mandate)
                self._generate_competing_reports(game, mandate)
                continue
            self._advance_assigned(game, mandate)
            self._generate_competing_reports(game, mandate)

    def visible_reports(
        self,
        *,
        mandate_id: str | None = None,
    ) -> tuple[CompetingImplementationReport, ...]:
        reports = self.reports
        if mandate_id is not None:
            reports = [item for item in reports if item.mandate_id == mandate_id]
        latest: dict[tuple[str, str], CompetingImplementationReport] = {}
        for report in reports:
            key = (report.mandate_id, report.office)
            current = latest.get(key)
            if current is None or report.global_month > current.global_month:
                latest[key] = report
        return tuple(
            sorted(
                latest.values(),
                key=lambda item: (item.mandate_id, item.urgency != "紧急", item.office),
            )
        )

    def start_press_conference(
        self,
        game: "ExecutivePresidentCareerGame",
        *,
        topic: str,
        outlet: str = "全国媒体联合采访",
    ) -> PressConferenceSession:
        session_id = _stable_id(
            "press-conference",
            str(game.global_month),
            topic,
            str(len(self.press_sessions)),
        )
        session = PressConferenceSession(
            id=session_id,
            global_month=game.global_month,
            outlet=outlet,
            topic=topic,
            current_question=self._opening_question(game, topic),
        )
        self.press_sessions.append(session)
        return session

    def answer_press_conference(
        self,
        game: "ExecutivePresidentCareerGame",
        *,
        session_id: str,
        answer_style: str,
    ) -> PressConferenceSession:
        session = self._session(session_id)
        if session.status != "open":
            raise ValueError("press conference is already closed")
        if answer_style not in self.PRESS_LABELS:
            raise ValueError(f"unknown press answer style {answer_style!r}")

        round_number = len(session.exchanges) + 1
        statement = game.answer_media(
            clipping_id=f"{session.id}-round-{round_number}",
            outlet=session.outlet,
            question=session.current_question,
            answer_style=answer_style,
            topic=session.topic,
        )
        consequence = "回答进入公开档案，今后的正式决定可能被拿来核对。"
        previous_styles = [item.answer_style for item in session.exchanges]
        if self._is_internal_contradiction(previous_styles, answer_style):
            consequence = "记者当场指出前后口径存在张力，发布会焦点从政策转向主席可信度。"
            game.world.apply_external_action(
                "press_conference_contradiction",
                {
                    "stakeholder_deltas": [
                        {
                            "actor_id": "broadcaster",
                            "trust": -0.016,
                            "mobilization": 0.015,
                            "note": "记者在同一场发布会上指出主席前后口径冲突",
                        },
                        {
                            "actor_id": "supporters_federation",
                            "trust": -0.012,
                            "note": "主席在连续追问中给出互相拉扯的承诺",
                        },
                    ],
                    "state_deltas": {
                        "fan_trust": -0.010,
                        "political_capital": -0.008,
                    },
                    "audit_note": f"press conference {session.id} contained contradictory answers",
                },
            )
        no_comment_count = sum(
            item.answer_style == "no_comment" for item in session.exchanges
        ) + (1 if answer_style == "no_comment" else 0)
        if no_comment_count >= 2:
            consequence = "连续拒绝回答让记者将沉默本身写成新闻，外部猜测进一步上升。"
            game.world.apply_external_action(
                "press_conference_evasion",
                {
                    "stakeholder_deltas": [
                        {
                            "actor_id": "broadcaster",
                            "trust": -0.014,
                            "mobilization": 0.020,
                            "note": "主席在同一发布会连续拒绝回答核心问题",
                        }
                    ],
                    "state_deltas": {"fan_trust": -0.006},
                    "audit_note": f"press conference {session.id} repeated no comment",
                },
            )

        next_question = self._followup_question(
            game,
            session,
            answer_style,
            round_number,
        )
        session.exchanges.append(
            PressExchange(
                round_number=round_number,
                question=session.current_question,
                answer_style=answer_style,
                quote=statement.quote,
                reporter_followup=next_question,
                consequence=consequence,
            )
        )
        if round_number >= session.max_rounds or next_question is None:
            session.status = "closed"
            session.current_question = "发布会结束"
        else:
            session.current_question = next_question
        return session

    def active_mandates(self) -> tuple[ImplementationMandate, ...]:
        return tuple(
            item
            for item in self.mandates
            if item.status not in {"completed", "partial", "failed", "withdrawn"}
        )

    def _advance_unassigned(
        self,
        game: "ExecutivePresidentCareerGame",
        mandate: ImplementationMandate,
    ) -> None:
        age = game.global_month - mandate.created_month
        if age <= 0:
            return
        mandate.status = "unassigned"
        mandate.public_update = (
            "文件已经签署，但没有一名官员被明确指定为最终责任人；各部门正在等待彼此先行动。"
        )
        if not mandate.penalty_applied:
            mandate.penalty_applied = True
            mandate.effects.append(
                f"G{game.global_month}：主席办公室未及时指定责任人，实施窗口开始流失。"
            )
            game.world.apply_external_action(
                "unassigned_implementation_delay",
                {
                    "stakeholder_deltas": [
                        {
                            "actor_id": "sports_ministry",
                            "trust": -0.008,
                            "note": "主席签署决定后没有指定具名执行责任人",
                        },
                        {
                            "actor_id": "supporters_federation",
                            "trust": -0.007,
                            "note": "公开决定迟迟没有出现可识别的执行负责人",
                        },
                    ],
                    "state_deltas": {"political_capital": -0.006},
                    "audit_note": f"mandate {mandate.id} remained unassigned",
                },
            )

    def _advance_assigned(
        self,
        game: "ExecutivePresidentCareerGame",
        mandate: ImplementationMandate,
    ) -> None:
        assert mandate.assigned_office is not None
        assert mandate.instruction_style is not None
        official = game.world.cabinet.get(mandate.assigned_office)
        if official is None or official.id != mandate.assigned_official_id:
            mandate.status = "delayed"
            mandate.public_update = "原责任人已经离开该岗位，秘书处要求主席重新指定执行负责人。"
            return

        active_for_office = sum(
            item.assigned_office == mandate.assigned_office
            and item.status not in {"completed", "partial", "failed", "withdrawn"}
            for item in self.mandates
        )
        fit = 1.0 if mandate.assigned_office in mandate.recommended_offices else 0.45
        style = self.INSTRUCTION_STYLES[mandate.instruction_style]
        grievance = game.office.staff_grievance.get(mandate.assigned_office, 0.0)
        workload_penalty = max(0, active_for_office - 1) * 0.10
        jitter = _deterministic_jitter(mandate.id, game.global_month)
        delivery = _clamp(
            0.26 * official.competence
            + 0.18 * official.loyalty
            + 0.15 * official.integrity
            + 0.18 * fit
            + 0.13 * style["clarity"]
            + 0.10 * (1.0 - official.scandal_points)
            + style["speed"]
            - workload_penalty
            - 0.10 * grievance
            + jitter,
        )
        distortion_pressure = _clamp(
            0.34 * (1.0 - official.integrity)
            + 0.19 * official.network_power
            + 0.18 * (1.0 - official.loyalty)
            + 0.12 * grievance
            + style["distortion"]
            + (0.08 if fit < 0.8 else 0.0)
        )
        increment = 0.16 + 0.24 * delivery
        mandate.progress = _clamp(mandate.progress + increment)
        mandate.hidden_delivery_quality = delivery
        if mandate.progress >= 0.42 and distortion_pressure >= 0.48:
            mandate.hidden_distortion = _clamp(
                mandate.hidden_distortion + 0.08 + 0.10 * distortion_pressure
            )

        if mandate.hidden_distortion >= 0.24:
            mandate.status = "narrowed"
            mandate.public_update = (
                f"{official.name}报告大部分程序节点已经启动，但执行口径正在被缩窄；"
                "部分原始目标被解释为‘条件成熟后再实施’。"
            )
        elif delivery < 0.54:
            mandate.status = "delayed"
            mandate.public_update = (
                f"{official.name}称跨部门材料仍不齐全，当前进度落后于主席办公室预期。"
            )
        else:
            mandate.status = "on_track"
            mandate.public_update = (
                f"{official.name}已完成本月节点，并提交下一阶段责任清单；"
                "督查室尚未确认最终效果。"
            )

        due = mandate.due_month is not None and game.global_month >= mandate.due_month
        if mandate.progress >= 0.96 or due:
            self._finalize_mandate(game, mandate)

    def _finalize_mandate(
        self,
        game: "ExecutivePresidentCareerGame",
        mandate: ImplementationMandate,
    ) -> None:
        if mandate.outcome_applied:
            return
        mandate.outcome_applied = True
        effective_quality = _clamp(
            0.64 * mandate.progress
            + 0.36 * mandate.hidden_delivery_quality
            - mandate.hidden_distortion
        )
        if effective_quality >= 0.72:
            mandate.status = "completed"
            mandate.public_update = (
                f"{mandate.assigned_official_name}完成了主席授权的主要目标，"
                "督查室确认结果与原批示基本一致。"
            )
            mandate.effects.append("具名责任人按期交付，主席签字转化为可核验结果。")
            payload = {
                "stakeholder_deltas": [
                    {
                        "actor_id": "sports_ministry",
                        "trust": 0.014,
                        "support": 0.008,
                        "note": "主席通过具名责任制完成重大决定",
                    },
                    {
                        "actor_id": "supporters_federation",
                        "trust": 0.010,
                        "note": "主席公布的责任人与时间表得到落实",
                    },
                ],
                "state_deltas": {"political_capital": 0.010},
                "official_deltas": [
                    {
                        "official_id": mandate.assigned_official_id,
                        "loyalty": 0.012,
                        "network_power": 0.006,
                    }
                ],
                "audit_note": f"mandate {mandate.id} completed",
            }
        elif effective_quality >= 0.48:
            mandate.status = "partial"
            mandate.public_update = (
                f"{mandate.assigned_official_name}交付了部分结果，但督查室确认"
                "若干关键目标被延期或缩窄。"
            )
            mandate.effects.append("表面节点完成，但政策范围与主席原始批示存在明显差距。")
            payload = {
                "stakeholder_deltas": [
                    {
                        "actor_id": "supporters_federation",
                        "trust": -0.008,
                        "note": "主席决定只得到部分执行",
                    }
                ],
                "state_deltas": {"political_capital": -0.004},
                "official_deltas": [
                    {
                        "official_id": mandate.assigned_official_id,
                        "loyalty": -0.006,
                        "scandal_points": 0.010,
                    }
                ],
                "audit_note": f"mandate {mandate.id} partially delivered",
            }
        else:
            mandate.status = "failed"
            mandate.public_update = (
                f"{mandate.assigned_official_name}未能在期限内交付可核验结果；"
                "部门之间开始争论失败责任究竟来自资源、授权还是执行。"
            )
            mandate.effects.append("正式决定执行失败，主席必须决定是否换人、收回授权或承担政治责任。")
            payload = {
                "stakeholder_deltas": [
                    {
                        "actor_id": "sports_ministry",
                        "trust": -0.014,
                        "support": -0.008,
                        "note": "主席重大决定在具名责任制下仍执行失败",
                    },
                    {
                        "actor_id": "supporters_federation",
                        "trust": -0.018,
                        "support": -0.010,
                        "mobilization": 0.012,
                        "note": "主席签字没有转化为实际结果",
                    },
                ],
                "state_deltas": {
                    "political_capital": -0.016,
                    "fan_trust": -0.010,
                },
                "official_deltas": [
                    {
                        "official_id": mandate.assigned_official_id,
                        "loyalty": -0.018,
                        "scandal_points": 0.018,
                    }
                ],
                "audit_note": f"mandate {mandate.id} failed",
            }
        game.world.apply_external_action("implementation_outcome", payload)

    def _generate_competing_reports(
        self,
        game: "ExecutivePresidentCareerGame",
        mandate: ImplementationMandate,
        *,
        force: bool = False,
    ) -> None:
        selected = self._reporting_offices(mandate)
        for office in selected:
            key = f"{game.global_month}|{mandate.id}|{office}"
            if key in self._report_keys and not force:
                continue
            self._report_keys.add(key)
            official = game.world.cabinet.get(office)
            if official is None:
                continue
            argument, blind_spot = self.OFFICE_ARGUMENTS[office]
            fit = office in mandate.recommended_offices
            if office == mandate.assigned_office:
                headline = f"牵头部门称“{mandate.option_title}”仍可按授权推进"
                recommendation = (
                    "维持现有授权，并允许负责人先完成下一个节点再接受政治评价。"
                )
                evidence = mandate.public_update
            elif fit:
                headline = f"{office}认为牵头方案遗漏了本部门掌握的关键约束"
                recommendation = "要求主席增加联合会签或设置一个不可绕过的停止条件。"
                evidence = f"该部门从事项专业归口出发，指出：{argument}"
            else:
                headline = f"{office}要求把“{mandate.option_title}”放回更大的政治成本中评估"
                recommendation = "不反对继续执行，但要求在下一次主席办公会上复核外部影响。"
                evidence = argument

            coverage = _clamp(
                0.46 * official.competence
                + 0.34 * official.integrity
                + 0.20 * (1.0 - official.scandal_points)
            )
            confidence = "高" if coverage >= 0.72 else "中" if coverage >= 0.52 else "有限"
            urgency = (
                "紧急"
                if mandate.status in {"unassigned", "delayed", "failed"}
                or (
                    mandate.due_month is not None
                    and mandate.due_month - game.global_month <= 1
                )
                else "关注"
            )
            report = CompetingImplementationReport(
                id=_stable_id("implementation-report", key),
                global_month=game.global_month,
                mandate_id=mandate.id,
                office=office,
                official_name=official.name,
                headline=headline,
                recommendation=recommendation,
                evidence=evidence,
                blind_spot=blind_spot,
                confidence=confidence,
                urgency=urgency,
            )
            self.reports.append(report)

    def _reporting_offices(self, mandate: ImplementationMandate) -> tuple[str, ...]:
        offices: list[str] = []
        if mandate.assigned_office:
            offices.append(mandate.assigned_office)
        for office in mandate.recommended_offices:
            if office not in offices:
                offices.append(office)
        for office in ("秘书长", "财务与准入总监", "廉洁与纪律专员"):
            if office not in offices:
                offices.append(office)
            if len(offices) >= 3:
                break
        return tuple(offices[:3])

    def _recommended_offices(self, context: str) -> tuple[str, ...]:
        scores: list[tuple[int, str]] = []
        lowered = context.lower()
        for office, keywords in self.OFFICE_KEYWORDS.items():
            score = sum(keyword.lower() in lowered for keyword in keywords)
            scores.append((score, office))
        scores.sort(key=lambda item: (-item[0], item[1]))
        selected = [office for score, office in scores if score > 0][:2]
        if not selected:
            selected = ["秘书长"]
        if "秘书长" not in selected and len(selected) == 1:
            selected.append("秘书长")
        return tuple(selected)

    def _opening_question(
        self,
        game: "ExecutivePresidentCareerGame",
        topic: str,
    ) -> str:
        active = self.active_mandates()
        if active:
            mandate = active[-1]
            return (
                f"主席，您已经签署“{mandate.option_title}”，但目前执行状态是"
                f"“{mandate.status}”。究竟由谁对结果负责？"
            )
        if game.office.leaks:
            return "主席，内部材料已经外泄。您是否承认办公室的信息治理已经失控？"
        return f"主席，关于“{topic}”，公众今天最需要您作出什么可以核验的承诺？"

    def _followup_question(
        self,
        game: "ExecutivePresidentCareerGame",
        session: PressConferenceSession,
        answer_style: str,
        round_number: int,
    ) -> str | None:
        if round_number >= session.max_rounds:
            return None
        if answer_style == "rules_first":
            return "您强调规则。那么如果规则导致豪门退出、联赛停摆，您也绝不干预吗？"
        if answer_style == "support_sector":
            return "您说要帮助行业。请明确资金从哪里来，哪些机构有资格获得帮助？"
        if answer_style == "transparent_uncertainty":
            return "既然事实尚未核实，为什么主席办公室已经作出政治表态，而不是等待正式报告？"
        if answer_style == "no_comment":
            return "您拒绝回答，是否意味着内部掌握的信息比公开情况更严重？"
        return "请您给出一个可以在三个月后核验的具体标准。"

    def _is_internal_contradiction(
        self,
        previous_styles: list[str],
        current_style: str,
    ) -> bool:
        if not previous_styles:
            return False
        previous = previous_styles[-1]
        return {previous, current_style} == {"rules_first", "support_sector"}

    def _mandate(self, mandate_id: str) -> ImplementationMandate:
        try:
            return next(item for item in self.mandates if item.id == mandate_id)
        except StopIteration as exc:
            raise ValueError(f"unknown implementation mandate {mandate_id!r}") from exc

    def _session(self, session_id: str) -> PressConferenceSession:
        try:
            return next(item for item in self.press_sessions if item.id == session_id)
        except StopIteration as exc:
            raise ValueError(f"unknown press conference {session_id!r}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": EXECUTIVE_FOLLOWUP_VERSION,
            "mandates": [asdict(item) for item in self.mandates],
            "reports": [asdict(item) for item in self.reports],
            "press_sessions": [asdict(item) for item in self.press_sessions],
            "processed_months": sorted(self._processed_months),
            "report_keys": sorted(self._report_keys),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutiveFollowupRuntime":
        if data.get("format_version") != EXECUTIVE_FOLLOWUP_VERSION:
            raise ValueError("unsupported executive-followup format")
        runtime = cls()
        runtime.mandates = [
            ImplementationMandate(
                **{
                    **item,
                    "recommended_offices": tuple(item["recommended_offices"]),
                    "effects": list(item.get("effects", [])),
                }
            )
            for item in data.get("mandates", [])
        ]
        runtime.reports = [
            CompetingImplementationReport(**item)
            for item in data.get("reports", [])
        ]
        runtime.press_sessions = []
        for item in data.get("press_sessions", []):
            runtime.press_sessions.append(
                PressConferenceSession(
                    id=item["id"],
                    global_month=int(item["global_month"]),
                    outlet=item["outlet"],
                    topic=item["topic"],
                    current_question=item["current_question"],
                    max_rounds=int(item.get("max_rounds", 3)),
                    status=item.get("status", "open"),
                    exchanges=[PressExchange(**exchange) for exchange in item.get("exchanges", [])],
                )
            )
        runtime._processed_months = {int(item) for item in data.get("processed_months", [])}
        runtime._report_keys = set(data.get("report_keys", []))
        return runtime

    def fingerprint(self) -> str:
        payload = self.to_dict()
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"executive-{digest}"


def _deterministic_jitter(identifier: str, month: int) -> float:
    digest = hashlib.sha256(f"{identifier}|{month}".encode("utf-8")).digest()
    raw = int.from_bytes(digest[:2], "big") / 65535.0
    return (raw - 0.5) * 0.08


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
