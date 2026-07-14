"""Long-term causal consequences for presidential-office behavior.

Meetings, public answers and information handling are not flavour text. They create
persistent memories, alter stakeholder behaviour, shape what reaches the president and
can become the source material for later leaks or media quotation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .president_career import PresidentCareerGame


OFFICE_CAUSALITY_VERSION = 1


@dataclass(frozen=True, slots=True)
class StaffFilterProfile:
    office: str
    official_id: str
    official_name: str
    disclosure_quality: float
    political_smoothing: float
    departmental_bias: str
    risk_tolerance: float


@dataclass(frozen=True, slots=True)
class FilteredOfficeReport:
    id: str
    created_month: int
    visible_month: int
    office: str
    official_name: str
    topic: str
    headline: str
    summary: str
    confidence: str
    urgency: str
    information_basis: str
    hidden_truth_severity: float
    hidden_coverage: float
    hidden_omission: str


@dataclass(frozen=True, slots=True)
class MeetingActionRecord:
    id: str
    global_month: int
    visitor: str
    institution: str
    stakeholder_id: str
    subject: str
    choice: str
    access_message: str
    commitment: str
    due_month: int | None
    status: str
    effects: tuple[str, ...]


@dataclass(slots=True)
class MediaStatementRecord:
    id: str
    global_month: int
    outlet: str
    question: str
    answer_style: str
    quote: str
    topic: str
    due_month: int | None
    contradiction_options: tuple[str, ...]
    status: str = "pending"
    resolved_month: int | None = None
    cited_month: int | None = None


@dataclass(frozen=True, slots=True)
class QuoteConsequence:
    global_month: int
    statement_id: str
    original_quote: str
    triggering_decision: str
    headline: str
    effects: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LeakRecord:
    id: str
    global_month: int
    source_office: str
    source_official: str
    leaked_record_id: str
    leaked_kind: str
    headline: str
    public_summary: str
    motive: str
    effects: tuple[str, ...]


class OfficeCausality:
    """Persistent office behaviour layered onto the autonomous football world."""

    INSTITUTION_ACTORS = {
        "职业联盟": "club_owners",
        "职业俱乐部投资人理事会": "club_owners",
        "国家队技术部门": "sports_ministry",
        "廉洁与纪律办公室": "sponsor_council",
        "协会秘书处": "provincial_fas",
        "青训与校园足球办公室": "education_ministry",
        "职业球员工会": "players_union",
        "全国转播与数字平台联盟": "broadcaster",
        "全国球迷联合会": "supporters_federation",
    }
    OFFICE_BIASES = {
        "秘书长": "联盟稳定与跨部门可执行性",
        "财务与准入总监": "现金来源、债务和规则一致性",
        "廉洁与纪律专员": "程序完整、公开记录和调查独立",
        "国家队技术总监": "备战连续性、球员负荷和技术自主",
        "青训与校园足球专员": "长期人才、地方能力和学校体系",
    }
    ANSWERS = {
        "rules_first": {
            "quote": "足协不会为任何机构修改已经公布的规则，处理结果将以正式程序为准。",
            "contradictions": (
                "blank_cheque",
                "quiet_settlement",
                "bury_case",
                "protect_delivery",
            ),
            "due": 6,
        },
        "support_sector": {
            "quote": "足协会帮助足球从业者和俱乐部渡过困难，不会让系统性风险无人承担。",
            "contradictions": ("refuse_bailout", "blame_local"),
            "due": 6,
        },
        "transparent_uncertainty": {
            "quote": "目前仍有关键事实没有核实，我会公布能够确认的部分，也会明确哪些仍然未知。",
            "contradictions": ("media_offensive", "bury_case"),
            "due": 5,
        },
        "no_comment": {
            "quote": "相关部门正在处理，我现在没有更多信息可以提供。",
            "contradictions": (),
            "due": None,
        },
    }

    def __init__(self) -> None:
        self.reports: list[FilteredOfficeReport] = []
        self.meetings: list[MeetingActionRecord] = []
        self.statements: list[MediaStatementRecord] = []
        self.quote_history: list[QuoteConsequence] = []
        self.leaks: list[LeakRecord] = []
        self.staff_grievance: dict[str, float] = {}
        self._report_keys: set[str] = set()
        self._processed_months: set[int] = set()

    def bootstrap(self, game: "PresidentCareerGame") -> None:
        self._generate_reports(game)

    def advance_month(self, game: "PresidentCareerGame") -> None:
        if game.global_month in self._processed_months:
            return
        self._processed_months.add(game.global_month)
        self._generate_reports(game)
        self._evaluate_statements(game)
        self.evaluate_leaks(game)
        for office in list(self.staff_grievance):
            self.staff_grievance[office] = max(
                0.0,
                self.staff_grievance[office] - 0.018,
            )

    def visible_reports(
        self,
        global_month: int,
    ) -> tuple[FilteredOfficeReport, ...]:
        latest: dict[str, FilteredOfficeReport] = {}
        for report in self.reports:
            if report.visible_month > global_month:
                continue
            current = latest.get(report.topic)
            if current is None or report.created_month > current.created_month:
                latest[report.topic] = report
        return tuple(
            sorted(latest.values(), key=lambda item: (item.urgency != "紧急", item.topic))
        )

    def staff_profiles(
        self,
        game: "PresidentCareerGame",
    ) -> tuple[StaffFilterProfile, ...]:
        profiles: list[StaffFilterProfile] = []
        for office, official in game.world.cabinet.items():
            disclosure = _clamp(
                0.42 * official.integrity
                + 0.33 * official.competence
                + 0.15 * (1.0 - official.network_power)
                + 0.10 * (1.0 - official.loyalty)
            )
            smoothing = _clamp(
                0.34 * official.loyalty
                + 0.27 * official.network_power
                + 0.22 * (1.0 - official.integrity)
                + 0.17 * self.staff_grievance.get(office, 0.0)
            )
            risk_tolerance = _clamp(
                0.38 * official.network_power
                + 0.32 * (1.0 - official.integrity)
                + 0.20 * official.loyalty
                + 0.10 * (1.0 - official.competence)
            )
            profiles.append(
                StaffFilterProfile(
                    office,
                    official.id,
                    official.name,
                    disclosure,
                    smoothing,
                    self.OFFICE_BIASES.get(office, "部门职责"),
                    risk_tolerance,
                )
            )
        return tuple(profiles)

    def record_meeting(
        self,
        game: "PresidentCareerGame",
        *,
        meeting_id: str,
        visitor: str,
        institution: str,
        subject: str,
        choice: str,
        sensitivity: str = "normal",
    ) -> MeetingActionRecord:
        if any(item.id == meeting_id for item in self.meetings):
            return next(item for item in self.meetings if item.id == meeting_id)
        if choice not in {"president", "secretary", "written", "decline"}:
            raise ValueError(f"unknown meeting choice {choice!r}")
        actor_id = self._actor_for_institution(institution)
        repeated_access = sum(
            item.stakeholder_id == actor_id
            and item.choice == "president"
            and item.global_month >= game.global_month - 6
            for item in self.meetings
        )
        effects: list[str] = []
        deltas: list[dict[str, Any]] = []
        due_month: int | None = None
        commitment = "没有形成主席个人承诺"
        if choice == "president":
            deltas.append(
                {
                    "actor_id": actor_id,
                    "support": 0.026,
                    "trust": 0.018,
                    "patience": 0.008,
                    "mobilization": -0.012,
                    "contact": True,
                    "note": f"主席亲自会见{visitor}，讨论{subject}",
                }
            )
            access_message = "主席亲自会见，对方获得最高级别接触渠道"
            commitment = "主席办公室承诺两个月内给予书面答复，但未承诺具体政策结果"
            due_month = game.global_month + 2
            effects.append("对方认为主席愿意直接承担政治责任。")
            if repeated_access >= 2:
                deltas.extend(
                    [
                        {
                            "actor_id": "supporters_federation",
                            "trust": -0.012,
                            "support": -0.006,
                            "note": "媒体和球迷质疑主席办公室接触渠道过度集中",
                        },
                        {
                            "actor_id": "provincial_fas",
                            "trust": -0.008,
                            "note": "地方体系认为主席对单一集团给予过多直接接触",
                        },
                    ]
                )
                effects.append("连续直接会见同一集团，引发接触公平性的质疑。")
        elif choice == "secretary":
            deltas.append(
                {
                    "actor_id": actor_id,
                    "support": 0.009,
                    "trust": 0.006,
                    "patience": 0.006,
                    "contact": True,
                    "note": f"秘书长受主席委托先行会见{visitor}",
                }
            )
            access_message = "由秘书长先行摸底，主席保留是否亲自介入的决定"
            commitment = "秘书处承诺一个月内提交谈判底线摘要"
            due_month = game.global_month + 1
            effects.append("对方获得正式渠道，但尚未得到主席个人背书。")
        elif choice == "written":
            deltas.append(
                {
                    "actor_id": actor_id,
                    "support": -0.003,
                    "trust": 0.008,
                    "patience": 0.004,
                    "note": f"主席要求{visitor}先提交可审计书面材料",
                }
            )
            access_message = "主席暂不安排会见，要求先进入可审计的书面程序"
            commitment = "收到完整材料后由主管部门在一个月内答复"
            due_month = game.global_month + 1
            effects.append("程序可信度提高，但对方认为政治接触被延后。")
        else:
            deltas.append(
                {
                    "actor_id": actor_id,
                    "support": -0.020,
                    "trust": -0.014,
                    "patience": -0.010,
                    "mobilization": 0.024,
                    "note": f"主席办公室拒绝{visitor}的会见申请",
                }
            )
            access_message = "主席办公室拒绝安排会见"
            effects.append("对方开始寻找媒体、上级部门或代表大会等替代渠道。")
            if sensitivity in {"urgent", "sensitive"}:
                effects.append("敏感事项被拒后，非正式施压和泄密动机上升。")
                self.staff_grievance["秘书长"] = _clamp(
                    self.staff_grievance.get("秘书长", 0.0) + 0.08
                )

        payload = {
            "stakeholder_deltas": deltas,
            "audit_note": f"meeting {meeting_id}: {access_message}",
        }
        game.world.apply_external_action("meeting", payload)
        record = MeetingActionRecord(
            meeting_id,
            game.global_month,
            visitor,
            institution,
            actor_id,
            subject,
            choice,
            access_message,
            commitment,
            due_month,
            "pending" if due_month is not None else "closed",
            tuple(effects),
        )
        self.meetings.append(record)
        return record

    def record_media_answer(
        self,
        game: "PresidentCareerGame",
        *,
        clipping_id: str,
        outlet: str,
        question: str,
        answer_style: str,
        topic: str,
    ) -> MediaStatementRecord:
        if any(item.id == clipping_id for item in self.statements):
            return next(item for item in self.statements if item.id == clipping_id)
        if answer_style not in self.ANSWERS:
            raise ValueError(f"unknown media answer {answer_style!r}")
        spec = self.ANSWERS[answer_style]
        stakeholder_deltas: list[dict[str, Any]] = []
        state_deltas: dict[str, float] = {}
        if answer_style == "rules_first":
            stakeholder_deltas.extend(
                [
                    {"actor_id": "sponsor_council", "trust": 0.016, "support": 0.008, "note": "主席公开坚持规则"},
                    {"actor_id": "supporters_federation", "trust": 0.014, "note": "主席公开坚持规则"},
                    {"actor_id": "club_owners", "support": -0.010, "patience": -0.006, "note": "主席拒绝预先承诺特殊处理"},
                ]
            )
            state_deltas = {"integrity_reputation": 0.008, "fan_trust": 0.005}
        elif answer_style == "support_sector":
            stakeholder_deltas.extend(
                [
                    {"actor_id": "club_owners", "support": 0.018, "trust": 0.010, "note": "主席公开承诺帮助行业渡过困难"},
                    {"actor_id": "finance_ministry", "trust": -0.010, "note": "主席在资金来源不明时作出支持承诺"},
                    {"actor_id": "supporters_federation", "trust": -0.006, "note": "公众担心支持承诺演变为选择性救助"},
                ]
            )
            state_deltas = {"political_capital": 0.006, "integrity_reputation": -0.004}
        elif answer_style == "transparent_uncertainty":
            stakeholder_deltas.extend(
                [
                    {"actor_id": "broadcaster", "trust": 0.010, "note": "主席明确区分已知事实与未知事项"},
                    {"actor_id": "supporters_federation", "trust": 0.012, "note": "主席承认信息边界"},
                    {"actor_id": "sponsor_council", "trust": 0.008, "note": "主席承认信息边界"},
                ]
            )
            state_deltas = {"fan_trust": 0.006, "integrity_reputation": 0.005}
        else:
            stakeholder_deltas.extend(
                [
                    {"actor_id": "broadcaster", "trust": -0.010, "mobilization": 0.008, "note": "主席拒绝回应公开追问"},
                    {"actor_id": "supporters_federation", "trust": -0.005, "note": "主席未回应公开追问"},
                ]
            )
            state_deltas = {"fan_trust": -0.004}

        game.world.apply_external_action(
            "media_statement",
            {
                "stakeholder_deltas": stakeholder_deltas,
                "state_deltas": state_deltas,
                "audit_note": f"public statement to {outlet}: {spec['quote']}",
            },
        )
        due = game.global_month + spec["due"] if spec["due"] is not None else None
        record = MediaStatementRecord(
            clipping_id,
            game.global_month,
            outlet,
            question,
            answer_style,
            spec["quote"],
            topic,
            due,
            tuple(spec["contradictions"]),
            "noncommitment" if due is None else "pending",
        )
        self.statements.append(record)
        return record

    def note_formal_decision(
        self,
        game: "PresidentCareerGame",
        *,
        decision_id: str,
        option_id: str,
        option_title: str,
    ) -> None:
        grievance_map = {
            "blank_cheque": ("财务与准入总监", "廉洁与纪律专员"),
            "bury_case": ("廉洁与纪律专员",),
            "protect_delivery": ("廉洁与纪律专员",),
            "open_market": ("青训与校园足球专员",),
            "qualification_surge": ("青训与校园足球专员", "财务与准入总监"),
            "refuse_bailout": ("秘书长",),
            "replace_coach": ("国家队技术总监",),
        }
        for office in grievance_map.get(option_id, ()):
            self.staff_grievance[office] = _clamp(
                self.staff_grievance.get(office, 0.0) + 0.14
            )

        for statement in self.statements:
            if statement.status != "pending":
                continue
            if option_id not in statement.contradiction_options:
                continue
            statement.status = "contradicted"
            statement.resolved_month = game.global_month
            statement.cited_month = game.global_month
            effects = (
                "媒体重新播放主席此前的原话。",
                "相关集团把政策转向解释为承诺违约，而不是普通调整。",
            )
            game.world.apply_external_action(
                "quoted_contradiction",
                {
                    "stakeholder_deltas": [
                        {"actor_id": "broadcaster", "trust": -0.022, "mobilization": 0.018, "note": "媒体引用主席旧话质疑政策转向"},
                        {"actor_id": "supporters_federation", "trust": -0.025, "support": -0.012, "note": "主席公开承诺与正式决定发生冲突"},
                        {"actor_id": "sponsor_council", "trust": -0.016, "note": "主席公开承诺与正式决定发生冲突"},
                    ],
                    "state_deltas": {
                        "fan_trust": -0.018,
                        "integrity_reputation": -0.012,
                        "political_capital": -0.014,
                    },
                    "audit_note": f"old quote contradicted by {decision_id}/{option_id}",
                },
            )
            self.quote_history.append(
                QuoteConsequence(
                    game.global_month,
                    statement.id,
                    statement.quote,
                    option_title,
                    f"媒体以主席原话追问“{option_title}”是否构成政策反转",
                    effects,
                )
            )

    def evaluate_leaks(
        self,
        game: "PresidentCareerGame",
        *,
        force: bool = False,
    ) -> LeakRecord | None:
        sensitive = self._sensitive_records()
        if not sensitive:
            return None
        existing_ids = {item.leaked_record_id for item in self.leaks}
        sensitive = [item for item in sensitive if item[0] not in existing_ids]
        if not sensitive:
            return None

        candidates: list[tuple[float, str, Any]] = []
        for office, official in game.world.cabinet.items():
            grievance = self.staff_grievance.get(office, 0.0)
            risk = _clamp(
                0.33 * (1.0 - official.loyalty)
                + 0.23 * official.network_power
                + 0.18 * official.scandal_points
                + 0.14 * (1.0 - official.integrity)
                + 0.12 * grievance
            )
            candidates.append((risk, office, official))
        risk, office, official = max(candidates, key=lambda item: (item[0], item[1]))
        if risk < 0.50:
            return None
        leaked_id, leaked_kind, leaked_summary = max(
            sensitive,
            key=lambda item: self._fraction(
                f"record:{game.global_month}:{item[0]}:{official.id}"
            ),
        )
        chance = _clamp((risk - 0.42) * 0.42, 0.02, 0.28)
        draw = self._fraction(
            f"leak:{game.global_month}:{official.id}:{leaked_id}"
        )
        if not force and draw > chance:
            return None

        motive = (
            "程序性举报"
            if official.integrity >= 0.72 and self.staff_grievance.get(office, 0.0) >= 0.12
            else "派系自保与政治施压"
            if official.network_power >= 0.68
            else "对主席办公室处理方式的不满"
        )
        effects = (
            "媒体获得了原本只在内部流转的材料。",
            "主席办公室开始排查信息接触记录，部门之间的信任下降。",
        )
        game.world.apply_external_action(
            "office_leak",
            {
                "stakeholder_deltas": [
                    {"actor_id": "broadcaster", "support": 0.008, "mobilization": 0.012, "note": "媒体获得主席办公室内部材料"},
                    {"actor_id": "supporters_federation", "trust": -0.014, "note": "主席办公室内部材料外泄"},
                    {"actor_id": "sponsor_council", "trust": -0.010, "note": "主席办公室内部材料外泄"},
                ],
                "state_deltas": {
                    "fan_trust": -0.012,
                    "integrity_reputation": -0.010,
                    "political_capital": -0.014,
                },
                "official_deltas": [
                    {
                        "office": office,
                        "loyalty": -0.018,
                        "scandal_points": 0.018,
                    }
                ],
                "audit_note": f"internal leak from {office}: {leaked_summary}",
            },
        )
        record = LeakRecord(
            f"leak-{len(self.leaks)+1}-{game.global_month}",
            game.global_month,
            office,
            official.name,
            leaked_id,
            leaked_kind,
            "主席办公室内部材料流入媒体",
            leaked_summary,
            motive,
            effects,
        )
        self.leaks.append(record)
        self.staff_grievance[office] = max(
            0.0,
            self.staff_grievance.get(office, 0.0) - 0.18,
        )
        return record

    def _generate_reports(self, game: "PresidentCareerGame") -> None:
        state = game.current_campaign.engine.state
        politics = game.current_campaign.politics
        football = game.current_campaign.football
        distressed = [
            club for club in state.clubs.values()
            if club.license_status in {"administration", "excluded"}
            or club.wage_arrears_months >= 2
            or club.financial_health < 0.28
        ]
        topics = {
            "财务与准入总监": (
                "club_finance",
                _clamp(0.15 + 0.13 * len(distressed) + max(0.0, 12_000_000 - state.treasury) / 24_000_000),
                f"职业联赛有{len(distressed)}家俱乐部达到重点监测标准",
                "俱乐部报表、工资支付凭证与准入系统",
            ),
            "秘书长": (
                "coalition",
                _clamp(1.0 - politics.coalition_support),
                f"代表大会支持处于{_support_band(politics.coalition_support)}",
                "集团接触、公开表态与秘书处非正式沟通",
            ),
            "廉洁与纪律专员": (
                "integrity",
                _clamp(0.18 * len(game.world.active_cases) + (1.0 - state.integrity_reputation)),
                f"当前有{len(game.world.active_cases)}宗正式程序正在推进",
                "正式案件、审计移送与公开申报",
            ),
            "国家队技术总监": (
                "national_team",
                _clamp((football.international.user_position - 1) / 5.0),
                f"国家队预选赛暂列第{football.international.user_position}位",
                "教练组比赛报告、医疗负荷与俱乐部放人情况",
            ),
            "青训与校园足球专员": (
                "grassroots",
                _clamp((58.0 - state.youth_development_environment) / 35.0),
                f"青训环境综合水平为{_development_band(state.youth_development_environment)}",
                "地方抽查、学校项目和持证教练数据",
            ),
        }
        profiles = {item.office: item for item in self.staff_profiles(game)}
        for office, (topic, severity, headline, basis) in topics.items():
            key = f"{game.global_month}:{topic}"
            if key in self._report_keys:
                continue
            self._report_keys.add(key)
            profile = profiles[office]
            bad_news = severity >= 0.48
            delay = 1 if bad_news and profile.political_smoothing > 0.61 and profile.disclosure_quality < 0.58 else 0
            coverage = _clamp(
                profile.disclosure_quality
                - 0.20 * profile.political_smoothing * severity
                + 0.10 * (1.0 - profile.risk_tolerance)
            )
            omission = self._omission_text(office, severity, coverage)
            summary = self._framed_summary(
                office,
                topic,
                severity,
                coverage,
                headline,
            )
            confidence = (
                "高"
                if coverage >= 0.72
                else "中"
                if coverage >= 0.52
                else "有限"
            )
            urgency = (
                "紧急"
                if severity >= 0.72 and coverage >= 0.48
                else "关注"
                if severity >= 0.44
                else "常规"
            )
            official = game.world.cabinet[office]
            self.reports.append(
                FilteredOfficeReport(
                    f"report-{game.global_month}-{topic}",
                    game.global_month,
                    game.global_month + delay,
                    office,
                    official.name,
                    topic,
                    headline,
                    summary,
                    confidence,
                    urgency,
                    basis,
                    severity,
                    coverage,
                    omission,
                )
            )

    def _evaluate_statements(self, game: "PresidentCareerGame") -> None:
        for statement in self.statements:
            if statement.status != "pending" or statement.due_month is None:
                continue
            if game.global_month < statement.due_month:
                continue
            statement.status = "kept"
            statement.resolved_month = game.global_month
            game.world.apply_external_action(
                "statement_kept",
                {
                    "stakeholder_deltas": [
                        {"actor_id": "broadcaster", "trust": 0.009, "note": "主席公开表态在审查期内未被正式决定推翻"},
                        {"actor_id": "supporters_federation", "trust": 0.008, "note": "主席公开表态在审查期内未被正式决定推翻"},
                    ],
                    "state_deltas": {"fan_trust": 0.004},
                    "audit_note": f"public statement {statement.id} completed its review period without contradiction",
                },
            )

        updated: list[MeetingActionRecord] = []
        for meeting in self.meetings:
            if meeting.status != "pending" or meeting.due_month is None:
                updated.append(meeting)
                continue
            if game.global_month < meeting.due_month:
                updated.append(meeting)
                continue
            actor = game.current_campaign.politics.stakeholders[meeting.stakeholder_id]
            fulfilled = actor.last_contact_month >= game.local_month - 2
            status = "fulfilled" if fulfilled else "missed"
            effects = list(meeting.effects)
            if fulfilled:
                game.world.apply_external_action(
                    "meeting_followup_kept",
                    {
                        "stakeholder_deltas": [
                            {"actor_id": meeting.stakeholder_id, "trust": 0.010, "note": "主席办公室按会见承诺完成书面跟进"}
                        ],
                        "audit_note": f"meeting follow-up completed for {meeting.id}",
                    },
                )
                effects.append("主席办公室按期完成书面跟进。")
            else:
                game.world.apply_external_action(
                    "meeting_followup_missed",
                    {
                        "stakeholder_deltas": [
                            {"actor_id": meeting.stakeholder_id, "trust": -0.022, "support": -0.008, "mobilization": 0.012, "note": "主席办公室未兑现会见后的答复承诺"}
                        ],
                        "state_deltas": {"political_capital": -0.006},
                        "audit_note": f"meeting follow-up missed for {meeting.id}",
                    },
                )
                effects.append("会见后的书面答复逾期，对方把接触解释为安抚而非解决问题。")
            updated.append(
                MeetingActionRecord(
                    meeting.id,
                    meeting.global_month,
                    meeting.visitor,
                    meeting.institution,
                    meeting.stakeholder_id,
                    meeting.subject,
                    meeting.choice,
                    meeting.access_message,
                    meeting.commitment,
                    meeting.due_month,
                    status,
                    tuple(effects),
                )
            )
        self.meetings = updated

    def _sensitive_records(self) -> list[tuple[str, str, str]]:
        records: list[tuple[str, str, str]] = []
        for meeting in self.meetings:
            if meeting.choice in {"president", "decline"}:
                records.append(
                    (
                        meeting.id,
                        "meeting",
                        f"主席办公室对{meeting.visitor}的会见安排及内部处理意见：{meeting.access_message}",
                    )
                )
        for statement in self.statements:
            if statement.status == "contradicted":
                records.append(
                    (
                        statement.id,
                        "media preparation",
                        f"内部材料显示主席团队在作出“{statement.quote}”表态时已经讨论过政策反转风险",
                    )
                )
        return records

    @staticmethod
    def _actor_for_institution(institution: str) -> str:
        for key, actor_id in OfficeCausality.INSTITUTION_ACTORS.items():
            if key in institution:
                return actor_id
        return "provincial_fas"

    @staticmethod
    def _framed_summary(
        office: str,
        topic: str,
        severity: float,
        coverage: float,
        headline: str,
    ) -> str:
        if severity >= 0.68 and coverage < 0.50:
            framing = "部门称风险仍可通过内部协调控制，但没有提供最坏情景或明确停止条件。"
        elif severity >= 0.68:
            framing = "部门要求主席准备跨部门干预，并明确指出拖延会增加后续成本。"
        elif severity >= 0.42 and coverage < 0.48:
            framing = "部门使用了审慎措辞，承认存在压力，但没有建议立即升级处理。"
        elif severity >= 0.42:
            framing = "部门建议进入重点监测，并在下一月复核趋势。"
        else:
            framing = "部门没有发现需要主席立即介入的异常。"
        return f"{headline}。{framing}报告主要从“{OfficeCausality.OFFICE_BIASES[office]}”角度解释问题。"

    @staticmethod
    def _omission_text(office: str, severity: float, coverage: float) -> str:
        if coverage >= 0.72:
            return "未发现重大结构性遗漏"
        if office == "秘书长":
            return "可能淡化公开立场与实际投票之间的差异"
        if office == "财务与准入总监":
            return "可能缺少投资人个人担保是否可执行的信息"
        if office == "廉洁与纪律专员":
            return "依法未提供尚未形成程序结论的证据判断"
        if office == "国家队技术总监":
            return "可能低估公众与赞助商对短期成绩的耐心"
        return "可能高估地方报表中的训练质量和实际执行能力"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": OFFICE_CAUSALITY_VERSION,
            "reports": [asdict(item) for item in self.reports],
            "meetings": [asdict(item) for item in self.meetings],
            "statements": [asdict(item) for item in self.statements],
            "quote_history": [asdict(item) for item in self.quote_history],
            "leaks": [asdict(item) for item in self.leaks],
            "staff_grievance": dict(self.staff_grievance),
            "report_keys": sorted(self._report_keys),
            "processed_months": sorted(self._processed_months),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OfficeCausality":
        if int(data.get("version", 0)) != OFFICE_CAUSALITY_VERSION:
            raise ValueError("unsupported office-causality format")
        engine = cls()
        engine.reports = [FilteredOfficeReport(**item) for item in data.get("reports", [])]
        engine.meetings = [
            MeetingActionRecord(
                **{
                    **item,
                    "effects": tuple(item.get("effects", ())),
                }
            )
            for item in data.get("meetings", [])
        ]
        engine.statements = [
            MediaStatementRecord(
                **{
                    **item,
                    "contradiction_options": tuple(item.get("contradiction_options", ())),
                }
            )
            for item in data.get("statements", [])
        ]
        engine.quote_history = [
            QuoteConsequence(
                **{
                    **item,
                    "effects": tuple(item.get("effects", ())),
                }
            )
            for item in data.get("quote_history", [])
        ]
        engine.leaks = [
            LeakRecord(
                **{
                    **item,
                    "effects": tuple(item.get("effects", ())),
                }
            )
            for item in data.get("leaks", [])
        ]
        engine.staff_grievance = {
            str(key): float(value)
            for key, value in data.get("staff_grievance", {}).items()
        }
        engine._report_keys = set(data.get("report_keys", []))
        engine._processed_months = {
            int(item) for item in data.get("processed_months", [])
        }
        return engine

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _fraction(value: str) -> float:
        raw = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        return int(raw, 16) / float(16**12 - 1)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _support_band(value: float) -> str:
    if value >= 0.64:
        return "稳定多数"
    if value >= 0.50:
        return "可以维持"
    if value >= 0.36:
        return "脆弱谈判状态"
    return "接近失去控制"


def _development_band(value: float) -> str:
    if value >= 64:
        return "成熟"
    if value >= 54:
        return "改善中"
    if value >= 44:
        return "基础薄弱"
    return "高风险"
