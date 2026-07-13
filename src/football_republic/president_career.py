"""Player-perspective career mode for the national football association president.

The simulation world remains rich and autonomous, but the player controls exactly one
president. Losing office ends the playable career. The same world may continue in an
observer mode, where successor governments are resolved by their own AI doctrines.

This module also exposes deliberately incomplete presidential briefings. Hidden NPC
attributes, undisclosed relationships and exact evidentiary probabilities remain inside
the simulation and are not part of the player-facing API.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy
from .patronage_runtime import CareerJusticeHistory


PRESIDENT_CAREER_SAVE_VERSION = 6


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _support_label(value: float) -> str:
    if value >= 0.66:
        return "稳固支持"
    if value >= 0.54:
        return "倾向支持"
    if value >= 0.44:
        return "立场摇摆"
    if value >= 0.32:
        return "倾向反对"
    return "强烈反对"


def _trust_label(value: float) -> str:
    if value >= 0.67:
        return "信任较高"
    if value >= 0.48:
        return "信任有限"
    return "信任较低"


def _influence_label(value: float) -> str:
    if value >= 0.80:
        return "关键否决力量"
    if value >= 0.65:
        return "高影响力"
    if value >= 0.48:
        return "中等影响力"
    return "有限影响力"


@dataclass(frozen=True, slots=True)
class PresidentialBriefing:
    category: str
    priority: str
    title: str
    summary: str
    source: str
    confidence: str


@dataclass(frozen=True, slots=True)
class PublicPersonBrief:
    person_id: str
    name: str
    institution: str
    role: str
    public_status: str
    performance_assessment: str
    integrity_assessment: str
    disclosed_connections: int
    information_basis: str


@dataclass(frozen=True, slots=True)
class DisclosedConnectionBrief:
    connection_id: str
    first_person: str
    second_person: str
    connection_type: str
    public_description: str
    status: str


@dataclass(frozen=True, slots=True)
class PublicCaseBrief:
    case_id: str
    subject_name: str
    allegation: str
    route: str
    public_stage: str
    public_outcome: str
    next_step: str


@dataclass(frozen=True, slots=True)
class StakeholderEstimate:
    actor_id: str
    actor_name: str
    influence: str
    support_estimate: str
    trust_estimate: str
    latest_known_position: str


@dataclass(frozen=True, slots=True)
class PresidentLegacyReport:
    president_id: str
    president_name: str
    start_global_month: int
    end_global_month: int
    tenure_months: int
    terms_served: int
    exit_reason: str
    successor_name: str
    board_score: float
    political_score: float
    legacy_score: float
    verdict: str
    trophies: tuple[str, ...]
    achievements: tuple[str, ...]
    failures: tuple[str, ...]
    major_decisions: int
    promises_kept: int
    promises_broken: int
    treasury_end: float
    fan_trust_end: float
    integrity_end: float
    league_health_end: float
    national_team_strength_end: float


class PresidentCareerGame:
    """One fixed player's political career inside a persistent football world."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        self.world = CareerJusticeHistory(strategy=strategy, max_terms=max_terms)
        self.player_id = self.world.current_president.id
        self.player_name = self.world.current_president.name
        self.career_status = "serving"
        self.observer_mode = False
        self.career_end_global_month: int | None = None
        self.career_end_reason: str | None = None
        self.legacy_report: PresidentLegacyReport | None = None
        state = self.world.current_campaign.engine.state
        self._opening_state = {
            "treasury": state.treasury,
            "fan_trust": state.fan_trust,
            "integrity": state.integrity_reputation,
            "league_health": state.league_financial_health,
            "national_team": state.national_team_strength,
            "youth": state.youth_development_environment,
        }

    @property
    def current_campaign(self):
        return self.world.current_campaign

    @property
    def current_president(self):
        return self.world.current_president

    @property
    def global_month(self) -> int:
        return self.world.global_month

    @property
    def global_year(self) -> int:
        return self.world.global_year

    @property
    def local_month(self) -> int:
        return self.world.local_month

    @property
    def term_index(self) -> int:
        return self.world.term_index

    @property
    def history_finished(self) -> bool:
        return self.world.finished

    @property
    def player_in_office(self) -> bool:
        return (
            self.career_status == "serving"
            and self.world.current_president.id == self.player_id
            and not self.world.caretaker_active
            and self.world.current_president.status == "incumbent"
        )

    @property
    def can_act(self) -> bool:
        return self.player_in_office and not self.world.finished

    @property
    def current_decision(self):
        return self.world.current_decision if self.can_act else None

    @property
    def successor_name(self) -> str:
        if self.player_in_office:
            return "—"
        return self.world.current_president.name

    def advance(self, months: int = 1, *, interactive: bool = True) -> None:
        if not self.can_act:
            raise RuntimeError("the player's presidential career has ended")
        if months < 0:
            raise ValueError("months cannot be negative")
        self.world.advance(months, interactive=interactive)
        self._refresh_career_state()

    def resolve_decision(self, option_id: str):
        if not self.can_act:
            raise RuntimeError("successor-government decisions are not controlled by the player")
        decision = self.world.current_decision
        if decision is None:
            raise RuntimeError("there is no presidential decision pending")
        if decision.id.startswith("election_"):
            raise RuntimeError("the player cannot choose a successor after leaving office")
        record = self.world.resolve_decision(option_id)
        self._refresh_career_state()
        return record

    def observe(self, months: int = 1) -> None:
        if self.career_status == "serving":
            raise RuntimeError("observer mode is available only after leaving office")
        if months < 0:
            raise ValueError("months cannot be negative")
        self.observer_mode = True
        self.world.advance(months, interactive=False)

    def observe_years(self, years: int = 1) -> None:
        if years < 0:
            raise ValueError("years cannot be negative")
        self.observe(years * 12)

    def observe_to_end(self) -> None:
        if self.career_status == "serving":
            raise RuntimeError("observer mode is available only after leaving office")
        self.observer_mode = True
        while not self.world.finished:
            self.world.advance(24, interactive=False)

    def executive_briefings(self) -> tuple[PresidentialBriefing, ...]:
        state = self.current_campaign.engine.state
        football = self.current_campaign.football
        politics = self.current_campaign.politics
        briefings: list[PresidentialBriefing] = []

        distressed = [
            club for club in state.clubs.values()
            if club.license_status in {"administration", "excluded"}
            or club.wage_arrears_months >= 2
        ]
        if distressed:
            names = "、".join(club.name for club in distressed[:4])
            briefings.append(
                PresidentialBriefing(
                    "职业联赛",
                    "紧急",
                    f"{len(distressed)}家俱乐部进入财务或准入风险区",
                    f"重点名单：{names}。需要关注欠薪、牌照与比赛完整性。",
                    "财务与准入总监月报",
                    "高",
                )
            )
        else:
            briefings.append(
                PresidentialBriefing(
                    "职业联赛",
                    "正常",
                    "职业俱乐部暂未出现重大准入警报",
                    "当前没有俱乐部达到正式托管、牌照撤销或两个月欠薪警戒线。",
                    "财务与准入总监月报",
                    "高",
                )
            )

        position = football.international.user_position
        briefings.append(
            PresidentialBriefing(
                "国家队",
                "关注" if position > 2 else "正常",
                f"国家队当前预选赛排名第{position}位",
                f"技术部门评估的综合比赛准备度为{state.national_team_strength:.1f}。",
                "国家队技术总监竞赛简报",
                "高",
            )
        )

        support = politics.coalition_support
        briefings.append(
            PresidentialBriefing(
                "政治",
                "紧急" if support < 0.38 else "关注" if support < 0.50 else "正常",
                f"执政联盟估计为{_support_label(support)}",
                "秘书长建议关注承诺兑现、地方执行和下一次代表大会投票。",
                "秘书长政治形势简报",
                "中",
            )
        )

        integrity = state.integrity_reputation
        active_cases = len(self.world.active_cases)
        briefings.append(
            PresidentialBriefing(
                "审计",
                "关注" if active_cases or integrity < 0.50 else "正常",
                f"当前有{active_cases}宗正式程序中的案件",
                "这里只反映已经立案或公开的事项；未核实举报不会被当作事实呈报。",
                "廉洁与纪律专员正式报告",
                "高",
            )
        )

        if state.treasury < 8_000_000:
            briefings.append(
                PresidentialBriefing(
                    "财政",
                    "紧急",
                    "足协可支配国库进入低位",
                    f"当前余额约¥{state.treasury / 1_000_000:.1f}M，新增计划需要缩减或寻找共同出资方。",
                    "财务与准入总监现金流预测",
                    "高",
                )
            )

        if self.current_decision is not None:
            briefings.insert(
                0,
                PresidentialBriefing(
                    "主席待办",
                    "立即决定",
                    self.current_decision.title,
                    self.current_decision.narrative,
                    "主席办公室呈签件",
                    "正式文件",
                ),
            )
        return tuple(briefings)

    def public_people(self) -> tuple[PublicPersonBrief, ...]:
        cabinet_ids = {official.id for official in self.world.cabinet.values()}
        public_case_subjects = {case.subject_id for case in self.world.justice_cases}
        visible_ids = cabinet_ids | public_case_subjects | {self.player_id}
        visible_ids |= {
            person.id for person in self.world.people.values()
            if person.role.endswith("主席")
            or person.role in {"职业联盟首席执行官", "体育内容总裁"}
            or person.status in {"banned", "convicted"}
        }
        briefs: list[PublicPersonBrief] = []
        for person_id in sorted(visible_ids):
            person = self.world.people.get(person_id)
            if person is None:
                continue
            disclosed = sum(
                tie.disclosed and tie.status == "active"
                for tie in self.world._ties_for(person.id)
            )
            if person.status == "banned":
                integrity = "已被最终裁决禁止参与足球治理"
            elif person.status == "convicted":
                integrity = "存在尚待申诉终结的一审有责裁决"
            elif any(
                case.subject_id == person.id and case.stage not in {"closed", "final"}
                for case in self.world.justice_cases
            ):
                integrity = "存在公开调查或审理，尚无最终结论"
            elif disclosed:
                integrity = "存在已公开关联，暂未形成最终负面裁决"
            else:
                integrity = "公开资料中未见正式负面结论"

            if person.id in cabinet_ids:
                official = next(item for item in self.world.cabinet.values() if item.id == person.id)
                if official.competence >= 0.78:
                    performance = "部门交付评价较好"
                elif official.competence >= 0.62:
                    performance = "部门交付基本合格"
                else:
                    performance = "部门交付受到质疑"
                basis = "内阁绩效考核、公开申报与正式案件材料"
            else:
                performance = "仅掌握公开履历，缺少直接绩效考核"
                basis = "公开履历、机构公告与已披露材料"
            briefs.append(
                PublicPersonBrief(
                    person.id,
                    person.name,
                    person.institution,
                    person.role,
                    person.status,
                    performance,
                    integrity,
                    disclosed,
                    basis,
                )
            )
        return tuple(briefs)

    def disclosed_connections(self) -> tuple[DisclosedConnectionBrief, ...]:
        rows: list[DisclosedConnectionBrief] = []
        for tie in self.world.patronage_ties.values():
            if not tie.disclosed:
                continue
            first = self.world.people[tie.source_id]
            second = self.world.people[tie.target_id]
            rows.append(
                DisclosedConnectionBrief(
                    tie.id,
                    first.name,
                    second.name,
                    tie.kind,
                    f"{first.name}与{second.name}之间的{tie.kind}关系已进入公开申报或案件材料。",
                    tie.status,
                )
            )
        return tuple(rows)

    def public_cases(self) -> tuple[PublicCaseBrief, ...]:
        stage_labels = {
            "referral pending": "等待主席决定移送路径",
            "investigation": "独立调查中",
            "internal review": "内部纪律审查中",
            "suppressed": "未正式立案；存在争议",
            "charged": "已正式起诉",
            "appeal": "一审后申诉中",
            "closed": "程序已经结案",
            "final": "最终裁决已经作出",
        }
        rows: list[PublicCaseBrief] = []
        for case in reversed(self.world.justice_cases):
            if case.stage in {"investigation", "internal review"}:
                next_step = "调查机构将在后续月份决定是否达到起诉标准"
            elif case.stage == "charged":
                next_step = "等待一审裁决"
            elif case.stage == "appeal":
                next_step = "等待独立申诉庭复核"
            else:
                next_step = "无待定程序" if case.closed_global_month else "等待程序更新"
            rows.append(
                PublicCaseBrief(
                    case.id,
                    case.subject_name,
                    case.allegation,
                    case.route,
                    stage_labels.get(case.stage, case.stage),
                    case.outcome,
                    next_step,
                )
            )
        return tuple(rows)

    def stakeholder_estimates(self) -> tuple[StakeholderEstimate, ...]:
        rows: list[StakeholderEstimate] = []
        for actor in self.current_campaign.politics.stakeholders.values():
            latest = actor.memory[-1] if actor.memory else "尚无近期公开表态"
            rows.append(
                StakeholderEstimate(
                    actor.id,
                    actor.name,
                    _influence_label(actor.power),
                    _support_label(actor.support),
                    _trust_label(actor.trust),
                    latest,
                )
            )
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "format_version": PRESIDENT_CAREER_SAVE_VERSION,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "career_status": self.career_status,
            "observer_mode": self.observer_mode,
            "career_end_global_month": self.career_end_global_month,
            "career_end_reason": self.career_end_reason,
            "opening_state": dict(self._opening_state),
            "legacy_report": asdict(self.legacy_report) if self.legacy_report else None,
            "world": self.world.to_dict(),
        }
        payload["fingerprint"] = self.fingerprint()
        return payload

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
    def from_dict(cls, data: dict[str, Any]) -> "PresidentCareerGame":
        if data.get("format_version") != PRESIDENT_CAREER_SAVE_VERSION:
            raise ValueError("unsupported president-career save format")
        game = cls.__new__(cls)
        game.world = CareerJusticeHistory.from_dict(data["world"])
        game.player_id = str(data["player_id"])
        game.player_name = str(data["player_name"])
        game.career_status = str(data["career_status"])
        game.observer_mode = bool(data.get("observer_mode", False))
        game.career_end_global_month = data.get("career_end_global_month")
        game.career_end_reason = data.get("career_end_reason")
        game._opening_state = dict(data["opening_state"])
        legacy = data.get("legacy_report")
        if legacy is None:
            game.legacy_report = None
        else:
            legacy = dict(legacy)
            legacy["trophies"] = tuple(legacy.get("trophies", ()))
            legacy["achievements"] = tuple(legacy.get("achievements", ()))
            legacy["failures"] = tuple(legacy.get("failures", ()))
            game.legacy_report = PresidentLegacyReport(**legacy)
        if not any(item.id == game.player_id for item in game.world.presidents):
            raise ValueError("save no longer contains the player's president identity")
        expected = data.get("fingerprint")
        if expected and game.fingerprint() != expected:
            raise ValueError("president-career replay fingerprint mismatch")
        return game

    @classmethod
    def from_json(cls, content: str) -> "PresidentCareerGame":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "PresidentCareerGame":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "world": self.world.fingerprint(),
            "player_id": self.player_id,
            "player_name": self.player_name,
            "career_status": self.career_status,
            "observer_mode": self.observer_mode,
            "career_end_global_month": self.career_end_global_month,
            "career_end_reason": self.career_end_reason,
            "opening_state": self._opening_state,
            "legacy_report": asdict(self.legacy_report) if self.legacy_report else None,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def _refresh_career_state(self) -> None:
        if self.career_status != "serving":
            return
        player = next(
            (item for item in self.world.presidents if item.id == self.player_id),
            None,
        )
        still_current = self.world.current_president.id == self.player_id
        if still_current and player is not None and player.status == "incumbent" and not self.world.finished:
            return
        if still_current and self.world.finished:
            reason = "二十年历史观察期结束"
        else:
            reason = self._derive_exit_reason(player)
        self.career_status = "ended"
        self.career_end_global_month = self.world.global_month
        self.career_end_reason = reason
        self.legacy_report = self._build_legacy_report(reason)

    def _derive_exit_reason(self, player) -> str:
        for record in reversed(self.world.term_records):
            if record.president_id == self.player_id:
                return record.succession_reason
        for span in reversed(self.world.administration_history):
            if span.president_id == self.player_id and span.exit_reason:
                return span.exit_reason
        if player is not None:
            return player.status
        return "失去主席职位"

    def _build_legacy_report(self, reason: str) -> PresidentLegacyReport:
        state = self.current_campaign.engine.state
        player_records = [
            item for item in self.world.term_records
            if item.president_id == self.player_id
        ]
        if player_records:
            board_score = sum(item.board_score for item in player_records) / len(player_records)
            political_score = sum(item.political_score for item in player_records) / len(player_records)
            promises_kept = sum(item.promises_kept for item in player_records)
            promises_broken = sum(item.promises_broken for item in player_records)
        else:
            board_score = self.current_campaign.board_review().score
            political = self.current_campaign.political_review
            political_score = political.score
            promises_kept = political.promises_kept
            promises_broken = political.promises_broken

        player = next(
            (item for item in self.world.presidents if item.id == self.player_id),
            None,
        )
        terms_served = player.terms_served if player is not None else max(1, len(player_records))
        trophies = tuple(
            f"第{item.global_season}赛季：联赛冠军{item.premier_champion}，足协杯冠军{item.cup_champion}"
            for item in self.world.season_history
            if item.president_name == self.player_name
        )
        achievements: list[str] = []
        failures: list[str] = []
        if state.national_team_strength >= self._opening_state["national_team"] + 3.0:
            achievements.append("国家队综合实力显著提升")
        elif state.national_team_strength <= self._opening_state["national_team"] - 2.0:
            failures.append("国家队实力较上任时下降")
        if state.integrity_reputation >= self._opening_state["integrity"] + 0.04:
            achievements.append("足协廉洁声誉得到明显改善")
        elif state.integrity_reputation <= self._opening_state["integrity"] - 0.04:
            failures.append("足协廉洁声誉恶化")
        if state.league_financial_health >= self._opening_state["league_health"] + 0.04:
            achievements.append("职业联赛财务健康改善")
        elif state.league_financial_health <= self._opening_state["league_health"] - 0.04:
            failures.append("职业联赛财务风险加重")
        if state.youth_development_environment >= self._opening_state["youth"] + 0.04:
            achievements.append("青训与基层环境形成长期改善")
        if promises_broken > promises_kept:
            failures.append("政治与政策承诺违约多于兑现")
        if not achievements:
            achievements.append("维持国家足球体系连续运转")
        if not failures:
            failures.append("未形成被历史普遍视为灾难性的单一失败")

        legacy_score = _clamp(
            0.28 * board_score
            + 0.22 * political_score
            + 18.0 * state.integrity_reputation
            + 12.0 * state.fan_trust
            + 10.0 * state.league_financial_health
            + 0.10 * state.national_team_strength
        )
        if legacy_score >= 72:
            verdict = "改革型成功主席"
        elif legacy_score >= 60:
            verdict = "总体成功但留下明显代价"
        elif legacy_score >= 48:
            verdict = "功过相抵的争议主席"
        elif legacy_score >= 36:
            verdict = "未能兑现主要执政目标"
        else:
            verdict = "被视为国家足球危机的重要责任人"

        decision_count = sum(
            int(command["global_month"]) <= (self.career_end_global_month or self.global_month)
            for command in self.world._decision_log
        )
        successor = self.world.current_president.name if not self.player_in_office else "—"
        return PresidentLegacyReport(
            self.player_id,
            self.player_name,
            0,
            self.career_end_global_month or self.global_month,
            self.career_end_global_month or self.global_month,
            terms_served,
            reason,
            successor,
            board_score,
            political_score,
            legacy_score,
            verdict,
            trophies,
            tuple(achievements),
            tuple(failures),
            decision_count,
            promises_kept,
            promises_broken,
            state.treasury,
            state.fan_trust,
            state.integrity_reputation,
            state.league_financial_health,
            state.national_team_strength,
        )
