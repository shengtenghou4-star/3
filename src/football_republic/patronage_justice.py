"""Persistent political careers, patronage networks and formal justice cases.

The coalition layer models organizations. This layer gives those organizations named
people with careers, relationships and legal exposure. Presidents can decide how a
credible allegation is referred, but evidence, institutional independence and network
interference determine charging, trial and appeal outcomes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy
from .coalition_elections import ElectionCandidate
from .coalition_runtime import CoalitionElectionHistory
from .constitutional import ConstitutionalEvent, OfficialProfile, _clamp
from .governance import DecisionOption, DecisionRecord, GovernanceDecision
from .long_term import PresidentProfile


CAREER_JUSTICE_SAVE_VERSION = 5


@dataclass(frozen=True, slots=True)
class CareerPosting:
    global_month: int
    institution: str
    role: str
    reason: str


@dataclass(slots=True)
class PoliticalPerson:
    id: str
    name: str
    bloc: str
    home_region: str
    institution: str
    role: str
    age: int
    competence: float
    integrity: float
    ambition: float
    loyalty: float
    network_power: float
    status: str = "active"
    exposure: float = 0.0
    terms_in_high_office: int = 0
    career: list[CareerPosting] = field(default_factory=list)


@dataclass(slots=True)
class PatronageTie:
    id: str
    source_id: str
    target_id: str
    kind: str
    strength: float
    disclosed: bool
    created_global_month: int
    status: str = "active"


@dataclass(slots=True)
class JusticeCase:
    id: str
    subject_id: str
    subject_name: str
    allegation: str
    opened_global_month: int
    route: str
    evidence: float
    independence: float
    stage: str
    next_global_month: int
    outcome: str = "pending"
    appeal_status: str = "not filed"
    closed_global_month: int | None = None
    related_ties: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class JusticeEvent:
    global_month: int
    case_id: str
    subject_name: str
    stage: str
    headline: str
    evidence: float
    independence: float
    effects: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CareerEvent:
    global_month: int
    person_id: str
    person_name: str
    event_type: str
    institution: str
    role: str
    reason: str


class CareerJusticeHistory(CoalitionElectionHistory):
    """Long history with named careers, patronage ties and appealable cases."""

    BLOC_TO_INSTITUTION = {
        "sports_ministry": "国家体育主管部门",
        "finance_ministry": "财政监督署",
        "education_ministry": "全国学校体育司",
        "provincial_fas": "地方足协联盟",
        "club_owners": "职业俱乐部投资人理事会",
        "players_union": "职业球员工会",
        "broadcaster": "全国转播与数字平台联盟",
        "sponsor_council": "主要赞助商委员会",
        "supporters_federation": "全国球迷联合会",
    }
    OFFICE_BLOC = {
        "秘书长": "provincial_fas",
        "财务与准入总监": "finance_ministry",
        "廉洁与纪律专员": "sponsor_council",
        "国家队技术总监": "sports_ministry",
        "青训与校园足球专员": "education_ministry",
    }
    EXTERNAL_SPECS = (
        ("sports-deputy", "赵彦成", "sports_ministry", "首都", "副主任", 52, .78, .71, .66, .58, .70),
        ("finance-supervisor", "顾文秀", "finance_ministry", "东海", "足球财政监察主任", 49, .82, .84, .61, .50, .54),
        ("education-director", "沈启岳", "education_ministry", "江南", "校园足球司长", 47, .80, .79, .68, .55, .57),
        ("east-fa-chair", "魏冬岚", "provincial_fas", "东海", "东海足协主席", 55, .69, .61, .74, .69, .81),
        ("central-fa-chair", "彭知远", "provincial_fas", "中原", "中原足协主席", 53, .72, .57, .78, .72, .84),
        ("west-fa-chair", "马子琛", "provincial_fas", "西岭", "西岭足协主席", 50, .67, .66, .71, .64, .76),
        ("league-chief", "陆景松", "club_owners", "首都", "职业联盟首席执行官", 48, .83, .60, .82, .67, .79),
        ("owners-secretary", "韩奕诚", "club_owners", "江南", "投资人理事会秘书长", 46, .73, .48, .86, .79, .88),
        ("broadcast-chief", "苏婉清", "broadcaster", "东海", "体育内容总裁", 44, .81, .67, .79, .58, .74),
        ("sponsor-chair", "乔臻", "sponsor_council", "首都", "赞助商委员会主席", 51, .77, .74, .73, .62, .72),
        ("union-chair", "唐凯", "players_union", "北原", "球员工会主席", 43, .74, .76, .69, .66, .68),
        ("supporters-chair", "林秋禾", "supporters_federation", "江南", "球迷联合会主席", 41, .70, .85, .72, .54, .63),
        ("stadium-director", "何承岳", "provincial_fas", "中原", "市政球场发展署长", 50, .75, .58, .70, .68, .80),
        ("academy-director", "周宁川", "education_ministry", "西岭", "全国青训网络主任", 45, .84, .81, .64, .57, .55),
        ("discipline-scholar", "方至衡", "supporters_federation", "北原", "独立纪律学者", 56, .86, .91, .55, .42, .40),
    )
    TIE_SPECS = (
        ("central-fa-chair", "owners-secretary", "business", .82, False),
        ("east-fa-chair", "broadcast-chief", "family", .68, False),
        ("west-fa-chair", "academy-director", "alumni", .55, True),
        ("sports-deputy", "league-chief", "mentor", .62, True),
        ("finance-supervisor", "discipline-scholar", "professional", .58, True),
        ("sponsor-chair", "broadcast-chief", "commercial", .71, True),
        ("stadium-director", "central-fa-chair", "patronage", .77, False),
        ("union-chair", "supporters-chair", "campaign", .49, True),
        ("education-director", "academy-director", "mentor", .66, True),
        ("owners-secretary", "league-chief", "patronage", .74, False),
    )

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        self.people: dict[str, PoliticalPerson] = {}
        self.patronage_ties: dict[str, PatronageTie] = {}
        self.justice_cases: list[JusticeCase] = []
        self.justice_history: list[JusticeEvent] = []
        self.career_history: list[CareerEvent] = []
        self.justice_independence = 0.62
        self.prosecutor_capacity = 0.60
        self._pending_justice: list[GovernanceDecision] = []
        self._justice_context: dict[str, str] = {}
        self._justice_checkpoints: set[int] = set()
        self._candidate_people: dict[str, str] = {}
        super().__init__(strategy=strategy, max_terms=max_terms)
        self._seed_people()
        self._seed_ties()
        self._bind_initial_cabinet()
        self._register_current_president("founding president")

    @property
    def current_decision(self):
        if self._pending_justice:
            return self._pending_justice[0]
        return super().current_decision

    @property
    def active_cases(self) -> tuple[JusticeCase, ...]:
        return tuple(
            case for case in self.justice_cases
            if case.stage not in {"closed", "final"}
        )

    @property
    def undisclosed_network_strength(self) -> float:
        return sum(
            tie.strength for tie in self.patronage_ties.values()
            if tie.status == "active" and not tie.disclosed
        )

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
            before = self.global_month
            super().advance(1, interactive=True)
            elapsed = self.global_month - before
            if elapsed == 0:
                if self.current_decision is not None and not interactive:
                    self._auto_resolve_current()
                    continue
                break
            remaining -= elapsed
            self._advance_people_month()
            self._progress_cases()
            self._maybe_open_case()
            if interactive and self.current_decision is not None:
                break

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no pending decision")
        if self._pending_justice and decision.id == self._pending_justice[0].id:
            record = self._resolve_justice_decision(decision, option_id)
            self._append_decision_command(decision.id, option_id)
            return record
        return super().resolve_decision(option_id)

    def _auto_resolve_current(self) -> None:
        decision = self.current_decision
        if decision is None:
            return
        if decision.id.startswith("justice_referral_"):
            option = {
                Strategy.FOUNDATIONS: "independent_referral",
                Strategy.BALANCED: "internal_review",
                Strategy.QUICK_RESULTS: "shield_network",
            }[self.current_president.strategy]
            self.resolve_decision(option)
            return
        super()._auto_resolve_current()

    def _seed_people(self) -> None:
        for spec in self.EXTERNAL_SPECS:
            (
                person_id, name, bloc, region, role, age, competence, integrity,
                ambition, loyalty, network,
            ) = spec
            institution = self.BLOC_TO_INSTITUTION[bloc]
            self.people[person_id] = PoliticalPerson(
                person_id,
                name,
                bloc,
                region,
                institution,
                role,
                age,
                competence,
                integrity,
                ambition,
                loyalty,
                network,
                career=[CareerPosting(0, institution, role, "opening political landscape")],
            )

    def _seed_ties(self) -> None:
        for index, (source, target, kind, strength, disclosed) in enumerate(
            self.TIE_SPECS, start=1
        ):
            tie_id = f"tie-{index}-{source}-{target}"
            self.patronage_ties[tie_id] = PatronageTie(
                tie_id,
                source,
                target,
                kind,
                strength,
                disclosed,
                0,
            )

    def _bind_initial_cabinet(self) -> None:
        for office, official in self.cabinet.items():
            if official.id in self.people:
                continue
            bloc = self.OFFICE_BLOC[office]
            person = PoliticalPerson(
                official.id,
                official.name,
                bloc,
                "首都",
                "国家足球协会",
                office,
                46 + len(self.people) % 9,
                official.competence,
                official.integrity,
                .62,
                official.loyalty,
                official.network_power,
                status="cabinet",
                career=[CareerPosting(0, "国家足球协会", office, "founding cabinet")],
            )
            self.people[person.id] = person

    def _register_current_president(self, reason: str) -> None:
        person = next(
            (item for item in self.people.values() if item.name == self.current_president.name),
            None,
        )
        if person is None:
            person = PoliticalPerson(
                f"career-{self.current_president.id}",
                self.current_president.name,
                "sports_ministry",
                "首都",
                "国家足球协会",
                "主席",
                52,
                self.current_president.administrative_skill,
                self.current_president.integrity,
                .78,
                .72,
                self.current_president.coalition_skill,
                status="president",
                career=[],
            )
            self.people[person.id] = person
        self._post_person(person, "国家足球协会", "主席", reason, "presidential accession")

    def _post_person(
        self,
        person: PoliticalPerson,
        institution: str,
        role: str,
        reason: str,
        event_type: str,
    ) -> None:
        person.institution = institution
        person.role = role
        person.status = "president" if role == "主席" else "cabinet" if role in self.OFFICES else "active"
        if role in self.OFFICES or role == "主席":
            person.terms_in_high_office += 1
        posting = CareerPosting(self.global_month, institution, role, reason)
        person.career.append(posting)
        self.career_history.append(
            CareerEvent(
                self.global_month,
                person.id,
                person.name,
                event_type,
                institution,
                role,
                reason,
            )
        )

    def _replace_official(self, office: str, style: str, reason: str) -> OfficialProfile:
        outgoing = self.cabinet.get(office) if hasattr(self, "cabinet") else None
        official = super()._replace_official(office, style, reason)
        if not self.people:
            return official
        if outgoing is not None and outgoing.id in self.people and outgoing.id != official.id:
            former = self.people[outgoing.id]
            if former.status not in {"convicted", "banned", "retired", "president"}:
                self._post_person(
                    former,
                    self.BLOC_TO_INSTITUTION[former.bloc],
                    "资深政策顾问",
                    f"left {office}: {reason}",
                    "left cabinet",
                )
        incoming = self.people.get(official.id)
        if incoming is not None:
            self._post_person(
                incoming,
                "国家足球协会",
                office,
                reason,
                "cabinet appointment",
            )
        return official

    def _candidate(self, office: str, style: str) -> OfficialProfile:
        if not self.people:
            return super()._candidate(office, style)
        preferred_bloc = self.OFFICE_BLOC[office]
        serving_ids = {item.id for item in self.cabinet.values()} if hasattr(self, "cabinet") else set()
        eligible = [
            person for person in self.people.values()
            if person.status not in {"convicted", "banned", "retired", "president"}
            and person.id not in serving_ids
            and person.age < 68
        ]
        if not eligible:
            return super()._candidate(office, style)

        def score(person: PoliticalPerson) -> tuple[float, float, str]:
            bloc_bonus = .14 if person.bloc == preferred_bloc else 0.0
            if style == "technocrat":
                value = .44 * person.competence + .42 * person.integrity + bloc_bonus
            elif style == "loyalist":
                value = .38 * person.loyalty + .34 * person.network_power + .18 * person.competence + bloc_bonus
            else:
                value = .36 * person.network_power + .30 * person.competence + .18 * person.loyalty + bloc_bonus
            return value, person.ambition, person.id

        person = max(eligible, key=score)
        return OfficialProfile(
            id=person.id,
            name=person.name,
            office=office,
            style=style,
            competence=person.competence,
            integrity=person.integrity,
            loyalty=person.loyalty,
            network_power=person.network_power,
            appointed_global_month=self.global_month,
            appointed_by=self.current_president.name,
        )

    def _generate_candidates(self, election_id: str) -> tuple[ElectionCandidate, ...]:
        if not self.people:
            return super()._generate_candidates(election_id)
        used: set[str] = set()
        candidates: list[ElectionCandidate] = []
        current_name = self.current_president.name.replace("（看守）", "")
        for strategy in (Strategy.FOUNDATIONS, Strategy.BALANCED, Strategy.QUICK_RESULTS):
            eligible = [
                person for person in self.people.values()
                if person.id not in used
                and person.name != current_name
                and person.status not in {"convicted", "banned", "retired", "president"}
                and person.age < 70
            ]
            if not eligible:
                return super()._generate_candidates(election_id)

            def score(person: PoliticalPerson) -> tuple[float, float, str]:
                if strategy == Strategy.FOUNDATIONS:
                    value = .38 * person.integrity + .24 * person.competence + .18 * person.ambition + .10 * (1.0 - person.network_power)
                elif strategy == Strategy.BALANCED:
                    value = .31 * person.competence + .24 * person.integrity + .22 * person.network_power + .13 * person.loyalty
                else:
                    value = .31 * person.ambition + .28 * person.network_power + .22 * person.competence + .10 * person.loyalty
                sponsor_bonus = .10 if person.bloc == self.SPONSOR_BY_STRATEGY[strategy] else 0.0
                return value + sponsor_bonus, person.exposure * -1.0, person.id

            person = max(eligible, key=score)
            used.add(person.id)
            candidate_id = f"{election_id}-{person.id}-{strategy.value}"
            self._candidate_people[candidate_id] = person.id
            candidates.append(
                ElectionCandidate(
                    id=candidate_id,
                    name=person.name,
                    strategy=strategy,
                    sponsor_bloc=person.bloc,
                    coalition_skill=_clamp(.42 * person.network_power + .33 * person.competence + .25 * person.loyalty),
                    administrative_skill=person.competence,
                    integrity=person.integrity,
                    charisma=_clamp(.48 * person.ambition + .32 * person.network_power + .20 * person.competence),
                    platform=dict(self.PLATFORM[strategy]),
                )
            )
        return tuple(candidates)

    def _candidate_to_president(
        self,
        candidate: ElectionCandidate,
        prefix: str,
    ) -> PresidentProfile:
        president = super()._candidate_to_president(candidate, prefix)
        person_id = self._candidate_people.get(candidate.id)
        if person_id and person_id in self.people:
            person = self.people[person_id]
            president.id = f"{prefix}-{self.term_index}-{self.global_month}-{person.id}"
            self._post_person(
                person,
                "国家足球协会",
                "主席",
                f"won {candidate.strategy.value} coalition convention",
                "elected president",
            )
        return president

    def _advance_people_month(self) -> None:
        self._sync_cabinet_people()
        hidden_capture = 0.0
        for person in self.people.values():
            if person.status in {"convicted", "banned", "retired"}:
                continue
            ties = self._ties_for(person.id)
            hidden = sum(tie.strength for tie in ties if not tie.disclosed and tie.status == "active")
            person.exposure = _clamp(
                .42 * (1.0 - person.integrity)
                + .24 * person.network_power
                + .16 * hidden
                + .10 * max(0, person.terms_in_high_office - 1)
            )
            hidden_capture += person.exposure * hidden
        state = self.current_campaign.engine.state
        state.integrity_reputation = _clamp(
            state.integrity_reputation - hidden_capture * 0.000035
        )
        if self.global_month % 12 == 0:
            self._annual_career_cycle()

    def _sync_cabinet_people(self) -> None:
        for official in self.cabinet.values():
            person = self.people.get(official.id)
            if person is None:
                continue
            person.competence = .65 * person.competence + .35 * official.competence
            person.integrity = .70 * person.integrity + .30 * official.integrity
            person.loyalty = .65 * person.loyalty + .35 * official.loyalty
            person.network_power = .65 * person.network_power + .35 * official.network_power
            person.exposure = _clamp(person.exposure + .08 * official.scandal_points)

    def _annual_career_cycle(self) -> None:
        for person in self.people.values():
            person.age += 1
            if person.status in {"convicted", "banned", "retired"}:
                continue
            learning = .006 * person.competence * (1.0 - person.competence)
            person.competence = _clamp(person.competence + learning - max(0, person.age - 63) * .0015)
            person.network_power = _clamp(
                person.network_power + .004 * person.ambition + .003 * person.terms_in_high_office
            )
            if person.age >= 68 and person.status not in {"president", "cabinet"}:
                person.status = "retired"
                self.career_history.append(
                    CareerEvent(
                        self.global_month,
                        person.id,
                        person.name,
                        "retirement",
                        person.institution,
                        person.role,
                        "age and career-cycle retirement",
                    )
                )
        eligible = [
            person for person in self.people.values()
            if person.status == "active" and person.age < 64
        ]
        if eligible:
            promoted = max(
                eligible,
                key=lambda item: (
                    .40 * item.competence + .31 * item.ambition + .29 * item.network_power,
                    item.id,
                ),
            )
            if promoted.role not in {"全国政策委员会委员", "国家足球治理委员"}:
                new_role = (
                    "国家足球治理委员"
                    if promoted.network_power + promoted.ambition >= 1.45
                    else "全国政策委员会委员"
                )
                self._post_person(
                    promoted,
                    "国家足球治理委员会",
                    new_role,
                    "annual elite-career promotion",
                    "career promotion",
                )

    def _ties_for(self, person_id: str) -> list[PatronageTie]:
        return [
            tie for tie in self.patronage_ties.values()
            if tie.source_id == person_id or tie.target_id == person_id
        ]

    def _maybe_open_case(self) -> None:
        if (
            self.current_decision is not None
            or self.caretaker_active
            or self.global_month % 6 != 0
            or self.global_month in self._justice_checkpoints
        ):
            return
        self._justice_checkpoints.add(self.global_month)
        active_subjects = {
            case.subject_id for case in self.active_cases
        }
        candidates = [
            person for person in self.people.values()
            if person.status in {"active", "cabinet"}
            and person.id not in active_subjects
            and person.name != self.current_president.name.replace("（看守）", "")
        ]
        if not candidates:
            return
        subject = max(candidates, key=lambda item: (item.exposure, item.network_power, item.id))
        if subject.exposure < 0.45:
            return
        decision_id = f"justice_referral_{self.global_month}_{subject.id}"
        allegation = self._allegation_for(subject)
        self._justice_context[decision_id] = subject.id
        self._pending_justice.append(
            GovernanceDecision(
                id=decision_id,
                month=self.local_month,
                title=f"关系网案件：{subject.name}被举报",
                narrative=(
                    f"审计和媒体材料指向{subject.name}在担任{subject.role}期间，"
                    f"可能通过未申报关系网影响项目、任命或商业合同。主席只能决定案件如何移送，"
                    "不能决定最终罪责。"
                ),
                options=(
                    DecisionOption(
                        "independent_referral",
                        "移送独立检察与公开调查",
                        "暂停相关公职，公开关系申报，并由独立检察团队固定证据。",
                        "联盟伙伴可能反弹，短期行政效率下降",
                    ),
                    DecisionOption(
                        "internal_review",
                        "内部纪律审查",
                        "保留组织控制，由内部合规部门调查并决定是否移送。",
                        "证据独立性较弱，可能被质疑为自己查自己",
                    ),
                    DecisionOption(
                        "shield_network",
                        "压下案件并保护联盟关系",
                        "否认举报可信度，维持当事人与其关系网络。",
                        "一旦材料外泄，案件会以更高烈度重启",
                    ),
                ),
            )
        )
        self.justice_history.append(
            JusticeEvent(
                self.global_month,
                decision_id,
                subject.name,
                "referral pending",
                f"针对{subject.name}的关系网材料进入主席办公室",
                subject.exposure,
                self.justice_independence,
                (allegation,),
            )
        )

    def _allegation_for(self, subject: PoliticalPerson) -> str:
        hidden = [tie for tie in self._ties_for(subject.id) if not tie.disclosed]
        if hidden:
            strongest = max(hidden, key=lambda item: item.strength)
            other_id = strongest.target_id if strongest.source_id == subject.id else strongest.source_id
            other = self.people[other_id]
            return (
                f"未申报的{strongest.kind}关系连接{subject.name}与{other.name}，"
                "并与审批、转播或建设合同时间线重合"
            )
        return "财产申报、项目评分与任命记录之间存在无法解释的利益冲突"

    def _resolve_justice_decision(
        self,
        decision: GovernanceDecision,
        option_id: str,
    ) -> DecisionRecord:
        if option_id not in {"independent_referral", "internal_review", "shield_network"}:
            raise ValueError(f"unknown justice option {option_id!r}")
        subject_id = self._justice_context[decision.id]
        subject = self.people[subject_id]
        ties = sorted(self._ties_for(subject_id), key=lambda item: item.strength, reverse=True)
        related = tuple(item.id for item in ties[:3])
        state = self.current_campaign.engine.state
        effects: list[str] = []
        if option_id == "independent_referral":
            for tie in ties:
                tie.disclosed = True
            evidence = _clamp(.24 + .56 * subject.exposure + .08 * self.prosecutor_capacity)
            independence = _clamp(.72 + .18 * self.justice_independence)
            stage = "investigation"
            next_month = self.global_month + 2
            subject.status = "suspended"
            state.integrity_reputation = _clamp(state.integrity_reputation + .025)
            state.political_capital = _clamp(state.political_capital - .025)
            self.justice_independence = _clamp(self.justice_independence + .025)
            if subject_id in {official.id for official in self.cabinet.values()}:
                office = next(
                    office for office, official in self.cabinet.items()
                    if official.id == subject_id
                )
                self._replace_official(office, "technocrat", "subject suspended for independent case")
            effects.extend((
                "关系网络和利益申报被公开，独立检察团队接管证据。",
                "当事人暂停公职，案件将在两个月后决定是否起诉。",
            ))
        elif option_id == "internal_review":
            if ties:
                ties[0].disclosed = True
            evidence = _clamp(.18 + .43 * subject.exposure + .06 * self.prosecutor_capacity)
            independence = _clamp(.44 + .15 * self.justice_independence)
            stage = "internal review"
            next_month = self.global_month + 3
            subject.loyalty = _clamp(subject.loyalty + .025)
            state.integrity_reputation = _clamp(state.integrity_reputation - .008)
            effects.extend((
                "内部合规部门接管材料，但当事人暂不离职。",
                "审查独立性有限，三个月后决定是否移送检察。",
            ))
        else:
            evidence = _clamp(.10 + .24 * subject.exposure)
            independence = _clamp(.28 + .10 * self.justice_independence)
            stage = "suppressed"
            next_month = self.global_month + 4
            subject.loyalty = _clamp(subject.loyalty + .07)
            subject.network_power = _clamp(subject.network_power + .05)
            state.integrity_reputation = _clamp(state.integrity_reputation - .045)
            state.political_capital = _clamp(state.political_capital + .020)
            effects.extend((
                "主席办公室否认材料可信度，案件未被正式立案。",
                "被保护的关系网更忠诚也更强大，但泄露风险继续积累。",
            ))
        case = JusticeCase(
            id=f"case-{len(self.justice_cases)+1}-{self.global_month}-{subject.id}",
            subject_id=subject.id,
            subject_name=subject.name,
            allegation=self._allegation_for(subject),
            opened_global_month=self.global_month,
            route=option_id,
            evidence=evidence,
            independence=independence,
            stage=stage,
            next_global_month=next_month,
            related_ties=related,
        )
        self.justice_cases.append(case)
        self._pending_justice.pop(0)
        self.justice_history.append(
            JusticeEvent(
                self.global_month,
                case.id,
                subject.name,
                stage,
                f"{decision.title}—{option_id}",
                evidence,
                independence,
                tuple(effects),
            )
        )
        self.constitutional_history.append(
            ConstitutionalEvent(
                self.global_month,
                self.local_month,
                self.term_index,
                "justice referral decision",
                decision.title,
                subject.exposure,
                tuple(effects),
            )
        )
        option = next(item for item in decision.options if item.id == option_id)
        return DecisionRecord(
            decision.id,
            self.local_month,
            decision.title,
            option_id,
            option.title,
            tuple(effects),
        )

    def _progress_cases(self) -> None:
        for case in list(self.active_cases):
            if self.global_month < case.next_global_month:
                continue
            subject = self.people[case.subject_id]
            if case.stage in {"investigation", "internal review"}:
                gain = (
                    .16 * case.independence
                    + .12 * self.prosecutor_capacity
                    + .08 * sum(
                        self.patronage_ties[tie_id].disclosed
                        for tie_id in case.related_ties
                        if tie_id in self.patronage_ties
                    )
                    - .10 * subject.network_power
                )
                case.evidence = _clamp(case.evidence + gain)
                threshold = .58 if case.stage == "investigation" else .68
                if case.evidence >= threshold:
                    case.stage = "charged"
                    case.next_global_month = self.global_month + 2
                    headline = f"检方以{case.evidence:.0%}证据强度正式起诉{subject.name}"
                    effects = ("案件进入公开审理。", "联盟关系网开始游说证人和申诉渠道。")
                else:
                    case.stage = "closed"
                    case.outcome = "insufficient evidence"
                    case.closed_global_month = self.global_month
                    if subject.status == "suspended":
                        subject.status = "active"
                    headline = f"{subject.name}案件因证据不足结案"
                    effects = ("没有形成刑事指控。", "政治责任与关系披露记录仍然保留。")
                self._record_case_event(case, headline, effects)
                continue
            if case.stage == "charged":
                verdict_score = (
                    .62 * case.evidence
                    + .28 * case.independence
                    + .12 * self.justice_independence
                    - .20 * subject.network_power
                )
                if verdict_score >= .62:
                    case.stage = "appeal"
                    case.outcome = "convicted at trial"
                    case.appeal_status = "filed"
                    case.next_global_month = self.global_month + 2
                    subject.status = "convicted"
                    headline = f"{subject.name}一审被判有责并提起申诉"
                    effects = (
                        "当事人被解除全部公职并暂时禁止参与足球治理。",
                        "两个月后由独立申诉庭复核证据与程序。",
                    )
                    self._remove_convicted_official(subject)
                else:
                    case.stage = "final"
                    case.outcome = "acquitted at trial"
                    case.appeal_status = "not applicable"
                    case.closed_global_month = self.global_month
                    if subject.status in {"suspended", "convicted"}:
                        subject.status = "active"
                    headline = f"{subject.name}一审获判无责"
                    effects = ("刑事责任不成立。", "公开关系记录继续影响其政治信誉。")
                self._record_case_event(case, headline, effects)
                continue
            if case.stage == "appeal":
                appeal_score = (
                    .66 * case.evidence
                    + .24 * self.justice_independence
                    - .16 * subject.network_power
                )
                case.stage = "final"
                case.closed_global_month = self.global_month
                if appeal_score >= .62:
                    case.outcome = "conviction upheld"
                    case.appeal_status = "upheld"
                    subject.status = "banned"
                    headline = f"申诉庭维持对{subject.name}的有责裁决"
                    effects = ("五年治理禁入生效。", "相关未申报关系被永久公开。")
                    self._sanction_network(case)
                elif appeal_score >= .52:
                    case.outcome = "sanction reduced"
                    case.appeal_status = "partially allowed"
                    subject.status = "active"
                    subject.network_power = _clamp(subject.network_power - .14)
                    headline = f"申诉庭减轻{subject.name}制裁"
                    effects = ("刑事定性被缩减为严重治理失当。", "当事人可回归非公职岗位。")
                else:
                    case.outcome = "conviction reversed"
                    case.appeal_status = "allowed"
                    subject.status = "active"
                    headline = f"申诉庭撤销对{subject.name}的原裁决"
                    effects = ("程序或证据缺陷导致原判撤销。", "检察独立性和主席处理方式受到重新审视。")
                self._record_case_event(case, headline, effects)
                continue
            if case.stage == "suppressed":
                hidden = sum(
                    tie.strength for tie in self._ties_for(subject.id)
                    if not tie.disclosed and tie.status == "active"
                )
                leak_score = .55 * subject.exposure + .35 * hidden + .20 * (1.0 - self.current_campaign.engine.state.integrity_reputation)
                if leak_score >= .62:
                    for tie in self._ties_for(subject.id):
                        tie.disclosed = True
                    case.stage = "investigation"
                    case.route = "leaked after suppression"
                    case.evidence = _clamp(case.evidence + .30)
                    case.independence = _clamp(.70 + .16 * self.justice_independence)
                    case.next_global_month = self.global_month + 2
                    self.current_campaign.engine.state.integrity_reputation = _clamp(
                        self.current_campaign.engine.state.integrity_reputation - .035
                    )
                    headline = f"被压下的{subject.name}案件材料外泄并重启"
                    effects = ("全部相关关系被公开。", "主席此前的干预成为新的调查对象。")
                else:
                    case.stage = "closed"
                    case.outcome = "suppression held"
                    case.closed_global_month = self.global_month
                    headline = f"{subject.name}案件暂时沉寂"
                    effects = ("没有形成正式案件。", "关系网与政治风险仍然存在。")
                self._record_case_event(case, headline, effects)

    def _record_case_event(
        self,
        case: JusticeCase,
        headline: str,
        effects: tuple[str, ...],
    ) -> None:
        self.justice_history.append(
            JusticeEvent(
                self.global_month,
                case.id,
                case.subject_name,
                case.stage,
                headline,
                case.evidence,
                case.independence,
                effects,
            )
        )
        self.current_campaign.engine.audit_log.append(
            f"G{self.global_month}: justice — {headline}"
        )

    def _remove_convicted_official(self, subject: PoliticalPerson) -> None:
        match = next(
            (
                (office, official)
                for office, official in self.cabinet.items()
                if official.id == subject.id
            ),
            None,
        )
        if match is not None:
            office, _ = match
            self._replace_official(office, "technocrat", "court-ordered removal")
        self.career_history.append(
            CareerEvent(
                self.global_month,
                subject.id,
                subject.name,
                "removed by court",
                subject.institution,
                subject.role,
                "convicted at first-instance trial",
            )
        )

    def _sanction_network(self, case: JusticeCase) -> None:
        state = self.current_campaign.engine.state
        state.integrity_reputation = _clamp(state.integrity_reputation + .035)
        self.justice_independence = _clamp(self.justice_independence + .018)
        for tie_id in case.related_ties:
            tie = self.patronage_ties.get(tie_id)
            if tie is None:
                continue
            tie.disclosed = True
            tie.strength *= .55
            if tie.strength < .25:
                tie.status = "dissolved"

    def _rollover(self, bundle, president: PresidentProfile) -> None:
        previous_name = self.current_president.name
        super()._rollover(bundle, president)
        if president.name != previous_name:
            self._register_current_president("scheduled succession")

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = CAREER_JUSTICE_SAVE_VERSION
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CareerJusticeHistory":
        if data.get("format_version") != CAREER_JUSTICE_SAVE_VERSION:
            raise ValueError("unsupported career-justice history format")
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
            raise ValueError("save contains unreachable career-justice decisions")
        if injection_index != len(injections):
            raise ValueError("save contains unreachable scenario injections")
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("career-justice replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "CareerJusticeHistory":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "CareerJusticeHistory":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "people": [asdict(item) for item in sorted(self.people.values(), key=lambda value: value.id)],
            "ties": [asdict(item) for item in sorted(self.patronage_ties.values(), key=lambda value: value.id)],
            "cases": [asdict(item) for item in self.justice_cases],
            "justice_history": [asdict(item) for item in self.justice_history],
            "career_history": [asdict(item) for item in self.career_history],
            "justice_independence": self.justice_independence,
            "prosecutor_capacity": self.prosecutor_capacity,
            "pending_justice": self._pending_justice[0].id if self._pending_justice else None,
            "candidate_people": dict(sorted(self._candidate_people.items())),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
