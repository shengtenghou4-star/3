"""National-team match windows from the football-association president's perspective.

The chairman controls governance, resources, club-release arbitration, public targets and
post-match accountability.  The head coach retains squad and tactical authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import random
from typing import Any

from .adaptive_time import month_start
from .football import MatchResult, Player


MATCHDAY_RUNTIME_VERSION = 1


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _label(value: float, *, strong: float = 0.68, steady: float = 0.48) -> str:
    if value >= strong:
        return "稳固"
    if value >= steady:
        return "尚可"
    return "承压"


@dataclass(slots=True)
class HeadCoachProfile:
    id: str
    name: str
    philosophy: str
    appointed_global_month: int
    contract_end_global_month: int
    public_reputation: float
    chairman_trust: float
    job_security: float
    media_pressure: float
    wins: int = 0
    draws: int = 0
    losses: int = 0
    status: str = "serving"

    @property
    def public_reputation_label(self) -> str:
        return _label(self.public_reputation)

    @property
    def relationship_label(self) -> str:
        return _label(self.chairman_trust)

    @property
    def job_security_label(self) -> str:
        return _label(self.job_security, strong=0.62, steady=0.42)

    @property
    def pressure_label(self) -> str:
        if self.media_pressure >= 0.68:
            return "舆论高压"
        if self.media_pressure >= 0.45:
            return "持续受关注"
        return "外部压力有限"


@dataclass(frozen=True, slots=True)
class SquadMember:
    player_id: str
    player_name: str
    club_id: str
    club_name: str
    position: str
    age: int
    fitness: float
    role: str
    medical_status: str


@dataclass(slots=True)
class ClubReleaseDispute:
    id: str
    club_id: str
    club_name: str
    player_ids: tuple[str, ...]
    player_names: tuple[str, ...]
    severity: str
    public_reason: str
    status: str = "open"
    resolution: str = ""


@dataclass(slots=True)
class MatchWindow:
    id: str
    term_index: int
    round_number: int
    local_match_month: int
    global_match_month: int
    match_date: str
    opponent_code: str
    opponent_name: str
    venue: str
    table_stakes: str
    stage: str
    coach_id: str
    squad: tuple[SquadMember, ...]
    omitted_players: tuple[str, ...]
    disputes: list[ClubReleaseDispute]
    camp_choice: str = ""
    release_choice: str = ""
    mandate_choice: str = ""
    review_choice: str = ""
    unavailable_player_ids: list[str] = field(default_factory=list)
    readiness_modifier: float = 0.0
    injury_risk: float = 0.0
    public_expectation: float = 0.5
    treasury_cost: float = 0.0
    result: dict[str, Any] | None = None
    result_summary: str = ""
    notes: list[str] = field(default_factory=list)
    temporary_modifier_applied: float = 0.0

    @property
    def is_open(self) -> bool:
        return self.stage != "closed"

    @property
    def required_action(self) -> bool:
        return self.stage in {"briefing", "release", "pre_match", "review"}

    @property
    def available_squad(self) -> tuple[SquadMember, ...]:
        unavailable = set(self.unavailable_player_ids)
        return tuple(item for item in self.squad if item.player_id not in unavailable)


class NationalTeamCommandRuntime:
    CAMP_CHOICES = {
        "recovery": {
            "label": "恢复优先集训",
            "cost": 1_200_000.0,
            "readiness": 1.4,
            "injury": -0.05,
            "trust": 0.02,
            "note": "减少训练负荷，把体能恢复和伤病筛查放在首位。",
        },
        "balanced": {
            "label": "标准国家队营地",
            "cost": 700_000.0,
            "readiness": 0.8,
            "injury": 0.0,
            "trust": 0.01,
            "note": "按技术团队原计划组织训练、住宿和差旅。",
        },
        "performance": {
            "label": "高强度封闭备战",
            "cost": 2_100_000.0,
            "readiness": 2.7,
            "injury": 0.07,
            "trust": 0.03,
            "note": "增加训练和分析资源，但对疲劳球员形成额外风险。",
        },
    }
    RELEASE_CHOICES = {
        "enforce": {
            "label": "依法要求俱乐部完整放人",
            "readiness": 1.0,
            "trust": 0.03,
            "cost_each": 0.0,
            "owner_delta": -0.05,
        },
        "compensate": {
            "label": "协商保险与负荷补偿",
            "readiness": 0.7,
            "trust": 0.02,
            "cost_each": 280_000.0,
            "owner_delta": 0.01,
        },
        "concede": {
            "label": "接受俱乐部医疗豁免",
            "readiness": -1.1,
            "trust": -0.06,
            "cost_each": 0.0,
            "owner_delta": 0.04,
        },
    }
    MANDATE_CHOICES = {
        "back_coach": {
            "label": "公开支持主教练并尊重技术权力",
            "trust": 0.05,
            "pressure": -0.04,
            "readiness": 0.5,
            "expectation": 0.52,
        },
        "demand_result": {
            "label": "公开提出必须拿分的硬目标",
            "trust": -0.03,
            "pressure": 0.10,
            "readiness": 0.3,
            "expectation": 0.72,
        },
        "private_target": {
            "label": "内部明确目标，对外不设比分承诺",
            "trust": 0.02,
            "pressure": 0.01,
            "readiness": 0.4,
            "expectation": 0.58,
        },
    }
    REVIEW_CHOICES = {
        "public_backing": "公开承担协会责任并继续支持教练组",
        "technical_review": "启动技术复盘但不预设人事结论",
        "dismiss_coach": "解除主教练职务并启动紧急遴选",
    }

    COACH_ROTATION = (
        ("Lin Shaoyuan", "位置纪律与快速转换"),
        ("Mateo Rivas", "控球组织与高位压迫"),
        ("Han Joon-seok", "紧凑防守与定位球"),
        ("Ivan Petrov", "年轻化与直接进攻"),
    )

    def __init__(self) -> None:
        self.coach = self._new_coach(0, 0)
        self.coach_history: list[HeadCoachProfile] = []
        self.windows: list[MatchWindow] = []
        self.active_window_id: str | None = None

    @property
    def active_window(self) -> MatchWindow | None:
        if self.active_window_id is None:
            return None
        return next(
            (item for item in self.windows if item.id == self.active_window_id),
            None,
        )

    def sync(self, game) -> MatchWindow | None:
        """Open the next match window once the visible calendar reaches preparation week."""
        active = self.active_window
        if active is not None and active.is_open:
            return active
        candidate = self._next_fixture(game)
        if candidate is None:
            return None
        round_number, local_month, global_month, opponent_code, opponent_name, venue = candidate
        preparation_date = month_start(global_month)
        preparation_date = preparation_date.replace(day=1)
        from datetime import timedelta

        preparation_date -= timedelta(days=7)
        if game.calendar.current_date < preparation_date:
            return None
        window_id = f"t{game.term_index}-r{round_number}-g{global_month}"
        existing = next((item for item in self.windows if item.id == window_id), None)
        if existing is not None:
            self.active_window_id = existing.id if existing.is_open else None
            return existing if existing.is_open else None

        squad, omitted = self._select_squad(game, window_id)
        disputes = self._build_disputes(game, window_id, squad)
        window = MatchWindow(
            id=window_id,
            term_index=game.term_index,
            round_number=round_number,
            local_match_month=local_month,
            global_match_month=global_month,
            match_date=month_start(global_month).isoformat(),
            opponent_code=opponent_code,
            opponent_name=opponent_name,
            venue=venue,
            table_stakes=self._table_stakes(game),
            stage="briefing",
            coach_id=self.coach.id,
            squad=squad,
            omitted_players=omitted,
            disputes=disputes,
        )
        window.notes.append(
            f"主教练{self.coach.name}独立提交{len(squad)}人名单；主席办公室未参与具体人选。"
        )
        self.windows.append(window)
        self.active_window_id = window.id
        return window

    def resolve_camp(self, game, choice: str) -> MatchWindow:
        window = self._require_stage(game, "briefing")
        if choice not in self.CAMP_CHOICES:
            raise ValueError(f"unknown camp choice {choice!r}")
        policy = self.CAMP_CHOICES[choice]
        state = game.current_campaign.engine.state
        affordable = min(float(policy["cost"]), max(0.0, state.treasury))
        scale = affordable / max(float(policy["cost"]), 1.0)
        state.treasury -= affordable
        window.treasury_cost += affordable
        window.camp_choice = choice
        window.readiness_modifier += float(policy["readiness"]) * (0.55 + 0.45 * scale)
        window.injury_risk = _clamp(window.injury_risk + float(policy["injury"]), -0.08, 0.20)
        self.coach.chairman_trust = _clamp(
            self.coach.chairman_trust + float(policy["trust"]) * (0.6 + 0.4 * scale)
        )
        if scale < 0.99:
            window.notes.append("国库不足，集训计划被财务部门按可用资金缩减。")
        window.notes.append(str(policy["note"]))
        window.stage = "release" if window.disputes else "pre_match"
        return window

    def resolve_release(self, game, choice: str) -> MatchWindow:
        window = self._require_stage(game, "release")
        if choice not in self.RELEASE_CHOICES:
            raise ValueError(f"unknown release choice {choice!r}")
        policy = self.RELEASE_CHOICES[choice]
        state = game.current_campaign.engine.state
        total_cost = float(policy["cost_each"]) * len(window.disputes)
        affordable = min(total_cost, max(0.0, state.treasury))
        state.treasury -= affordable
        window.treasury_cost += affordable
        window.release_choice = choice
        window.readiness_modifier += float(policy["readiness"])
        self.coach.chairman_trust = _clamp(
            self.coach.chairman_trust + float(policy["trust"])
        )
        owners = game.current_campaign.football.pyramid.owners
        for dispute in window.disputes:
            owner = owners.get(dispute.club_id)
            if owner is not None:
                owner.relationship_with_fa = _clamp(
                    owner.relationship_with_fa + float(policy["owner_delta"])
                )
            dispute.status = "resolved"
            dispute.resolution = str(policy["label"])
            if choice == "concede":
                candidates = [
                    item for item in window.squad
                    if item.club_id == dispute.club_id
                    and item.player_id not in window.unavailable_player_ids
                ]
                if candidates:
                    player = min(candidates, key=lambda item: item.fitness)
                    window.unavailable_player_ids.append(player.player_id)
                    window.notes.append(
                        f"接受{dispute.club_name}医疗豁免，{player.player_name}退出本期名单。"
                    )
        if total_cost > affordable:
            window.readiness_modifier -= 0.4
            window.notes.append("补偿预算未能足额兑现，部分俱乐部只接受最低保障方案。")
        window.stage = "pre_match"
        return window

    def set_match_mandate(self, game, choice: str) -> MatchWindow:
        window = self._require_stage(game, "pre_match")
        if choice not in self.MANDATE_CHOICES:
            raise ValueError(f"unknown match mandate {choice!r}")
        policy = self.MANDATE_CHOICES[choice]
        window.mandate_choice = choice
        window.readiness_modifier += float(policy["readiness"])
        window.public_expectation = float(policy["expectation"])
        self.coach.chairman_trust = _clamp(
            self.coach.chairman_trust + float(policy["trust"])
        )
        self.coach.media_pressure = _clamp(
            self.coach.media_pressure + float(policy["pressure"])
        )
        self._settle_medical_uncertainty(window)
        window.stage = "awaiting_match"
        window.notes.append(str(policy["label"]))
        return window

    def prepare_month(self, game, target_local_month: int) -> float:
        """Return a one-match temporary strength modifier before monthly settlement."""
        active = self.active_window
        if active is None or active.local_match_month != target_local_month:
            candidate = self._next_fixture(game)
            if candidate and candidate[1] == target_local_month:
                active = self._auto_prepare(game)
        if active is None or active.local_match_month != target_local_month:
            return 0.0
        if active.stage != "awaiting_match":
            active = self._auto_prepare(game)
        unavailable_penalty = 0.45 * len(active.unavailable_player_ids)
        fit_bonus = self._fitness_modifier(active)
        coach_bonus = 1.2 * (self.coach.chairman_trust - 0.5)
        modifier = max(-4.0, min(5.0, active.readiness_modifier + fit_bonus + coach_bonus - unavailable_penalty))
        active.temporary_modifier_applied = modifier
        return modifier

    def settle_month(self, game, settled_local_month: int, base_strength: float) -> None:
        active = self.active_window
        if active is None or active.local_match_month != settled_local_month:
            return
        if active.temporary_modifier_applied:
            state = game.current_campaign.engine.state
            state.national_team_strength = max(
                20.0,
                min(95.0, state.national_team_strength - active.temporary_modifier_applied),
            )
        result = self._find_result(game, active)
        active.temporary_modifier_applied = 0.0
        if result is None:
            active.stage = "review"
            active.result_summary = "比赛结算未找到国家队正式结果，竞赛部门必须复核数据链。"
            return
        active.result = asdict(result)
        outcome, goals_for, goals_against = self._result_for_user(game, result)
        if outcome == "win":
            self.coach.wins += 1
            self.coach.job_security = _clamp(self.coach.job_security + 0.08)
            self.coach.public_reputation = _clamp(self.coach.public_reputation + 0.04)
            self.coach.media_pressure = _clamp(self.coach.media_pressure - 0.05)
            label = "取胜"
        elif outcome == "draw":
            self.coach.draws += 1
            self.coach.job_security = _clamp(self.coach.job_security + 0.01)
            self.coach.media_pressure = _clamp(self.coach.media_pressure + 0.01)
            label = "战平"
        else:
            self.coach.losses += 1
            self.coach.job_security = _clamp(self.coach.job_security - 0.11)
            self.coach.public_reputation = _clamp(self.coach.public_reputation - 0.05)
            self.coach.media_pressure = _clamp(self.coach.media_pressure + 0.10)
            label = "失利"
        active.result_summary = (
            f"Longhua {goals_for}-{goals_against} {active.opponent_name}，国家队{label}。"
        )
        active.stage = "review"
        active.notes.append(
            f"本场治理准备对临时比赛实力形成{active.readiness_modifier:+.1f}的基础影响。"
        )

    def resolve_review(self, game, choice: str) -> MatchWindow:
        window = self._require_stage(game, "review")
        if choice not in self.REVIEW_CHOICES:
            raise ValueError(f"unknown review choice {choice!r}")
        state = game.current_campaign.engine.state
        outcome = self._window_outcome(game, window)
        window.review_choice = choice
        if choice == "public_backing":
            self.coach.chairman_trust = _clamp(self.coach.chairman_trust + 0.04)
            if outcome == "loss":
                state.fan_trust = _clamp(state.fan_trust - 0.008)
            else:
                state.fan_trust = _clamp(state.fan_trust + 0.006)
            window.notes.append("主席公开承担协会层面的准备责任，技术团队继续工作。")
        elif choice == "technical_review":
            self.coach.chairman_trust = _clamp(self.coach.chairman_trust - 0.01)
            self.coach.job_security = _clamp(
                self.coach.job_security + (0.01 if outcome == "win" else -0.02)
            )
            window.notes.append("技术委员会收到比赛数据、医疗记录和征调争议材料。")
        else:
            termination_cost = min(2_400_000.0, max(0.0, state.treasury))
            state.treasury -= termination_cost
            old = self.coach
            old.status = "dismissed"
            old.job_security = 0.0
            self.coach_history.append(old)
            self.coach = self._new_coach(game.global_month, len(self.coach_history))
            state.fan_trust = _clamp(
                state.fan_trust + (0.012 if outcome == "loss" else -0.018)
            )
            window.notes.append(
                f"{old.name}被解除职务，解约与遴选支出¥{termination_cost / 1_000_000:.2f}M。"
            )
        window.stage = "closed"
        self.active_window_id = None
        return window

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": MATCHDAY_RUNTIME_VERSION,
            "coach": asdict(self.coach),
            "coach_history": [asdict(item) for item in self.coach_history],
            "windows": [self._window_to_dict(item) for item in self.windows],
            "active_window_id": self.active_window_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NationalTeamCommandRuntime":
        if int(data.get("version", 0)) != MATCHDAY_RUNTIME_VERSION:
            raise ValueError("unsupported national-team command format")
        runtime = cls.__new__(cls)
        runtime.coach = HeadCoachProfile(**data["coach"])
        runtime.coach_history = [HeadCoachProfile(**item) for item in data.get("coach_history", [])]
        runtime.windows = [runtime._window_from_dict(item) for item in data.get("windows", [])]
        runtime.active_window_id = data.get("active_window_id")
        return runtime

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _next_fixture(self, game):
        international = game.current_campaign.football.international
        for index, local_month in enumerate(international.round_months):
            window_id_prefix = f"t{game.term_index}-r{index + 1}-"
            if any(item.id.startswith(window_id_prefix) for item in self.windows):
                continue
            if local_month < game.local_month:
                continue
            pair = next(
                (
                    (home, away)
                    for home, away in international.schedule[index]
                    if international.user_code in {home, away}
                ),
                None,
            )
            if pair is None:
                continue
            home, away = pair
            opponent_code = away if home == international.user_code else home
            opponent = international.teams[opponent_code]
            venue = "主场" if home == international.user_code else "客场"
            global_month = game.global_month + (local_month - game.local_month)
            return index + 1, local_month, global_month, opponent_code, opponent.name, venue
        return None

    def _select_squad(self, game, window_id: str) -> tuple[tuple[SquadMember, ...], tuple[str, ...]]:
        pool: list[tuple[str, str, Player]] = []
        football = game.current_campaign.football
        for club_id, roster in football.rosters.items():
            club = game.current_campaign.engine.state.clubs[club_id]
            for player in roster.players:
                if player.nationality != "Longhua":
                    continue
                pool.append((club_id, club.name, player))
        rng = random.Random(_seed(f"squad:{window_id}:{self.coach.id}"))
        counts = {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}
        selected: list[SquadMember] = []
        omitted: list[str] = []
        for position, count in counts.items():
            candidates = [item for item in pool if item[2].position == position]
            candidates.sort(
                key=lambda item: (
                    item[2].match_readiness
                    + 0.05 * item[2].potential
                    + rng.uniform(-0.35, 0.35)
                ),
                reverse=True,
            )
            for club_id, club_name, player in candidates[:count]:
                medical = (
                    "伤停"
                    if player.injury_months > 0
                    else "出场成疑"
                    if player.fitness < 70
                    else "需要负荷管理"
                    if player.fitness < 79
                    else "可正常训练"
                )
                role = (
                    "核心候选"
                    if player.ability >= 72
                    else "轮换竞争"
                    if player.ability >= 62
                    else "阵容深度"
                )
                selected.append(
                    SquadMember(
                        player.id,
                        player.name,
                        club_id,
                        club_name,
                        position,
                        player.age,
                        player.fitness,
                        role,
                        medical,
                    )
                )
            omitted.extend(player.name for _, _, player in candidates[count : count + 3])
        return tuple(selected), tuple(omitted)

    def _build_disputes(
        self,
        game,
        window_id: str,
        squad: tuple[SquadMember, ...],
    ) -> list[ClubReleaseDispute]:
        by_club: dict[str, list[SquadMember]] = {}
        for member in squad:
            by_club.setdefault(member.club_id, []).append(member)
        disputes: list[ClubReleaseDispute] = []
        for club_id, members in sorted(by_club.items()):
            low_fitness = [item for item in members if item.fitness < 78]
            if len(members) < 4 and not low_fitness:
                continue
            club = game.current_campaign.engine.state.clubs[club_id]
            severity = "高" if len(members) >= 5 or low_fitness else "中"
            reason = (
                f"俱乐部要求对{len(low_fitness)}名疲劳或医疗观察球员进行联合复核。"
                if low_fitness
                else f"俱乐部认为同期征调{len(members)}人将影响联赛备战。"
            )
            disputes.append(
                ClubReleaseDispute(
                    id=f"release-{window_id}-{club_id}",
                    club_id=club_id,
                    club_name=club.name,
                    player_ids=tuple(item.player_id for item in members),
                    player_names=tuple(item.player_name for item in members),
                    severity=severity,
                    public_reason=reason,
                )
            )
        return disputes

    def _table_stakes(self, game) -> str:
        international = game.current_campaign.football.international
        row = international.table[international.user_code]
        position = international.user_position
        if row.played == 0:
            return "预选赛尚未开始；首场结果将建立整个周期的舆论基线。"
        if position <= 2:
            return f"当前第{position}位，处于直接出线区，但领先优势仍可能被一轮结果抹平。"
        if position == 3:
            return "当前处于附加赛位置，本场拿分关系到能否重新进入直接出线区。"
        return f"当前第{position}位并位于出线区外，本场已具有明显的职位与舆论压力。"

    def _settle_medical_uncertainty(self, window: MatchWindow) -> None:
        risk = max(0.0, window.injury_risk)
        doubts = [
            item for item in window.squad
            if item.medical_status in {"出场成疑", "需要负荷管理"}
            and item.player_id not in window.unavailable_player_ids
        ]
        if not doubts or risk <= 0:
            return
        rng = random.Random(_seed(f"medical:{window.id}:{window.camp_choice}"))
        if rng.random() < min(0.75, 0.18 + risk * 3.2):
            player = min(doubts, key=lambda item: item.fitness)
            window.unavailable_player_ids.append(player.player_id)
            window.notes.append(
                f"赛前医学复核未通过，{player.player_name}退出比赛名单。"
            )

    def _fitness_modifier(self, window: MatchWindow) -> float:
        available = window.available_squad
        if not available:
            return -4.0
        average = sum(item.fitness for item in available) / len(available)
        return max(-1.5, min(1.5, (average - 82.0) / 8.0))

    def _auto_prepare(self, game) -> MatchWindow | None:
        window = self.sync(game)
        if window is None:
            candidate = self._next_fixture(game)
            if candidate is None:
                return None
            game.calendar.current_date = month_start(candidate[2])
            window = self.sync(game)
        if window is None:
            return None
        if window.stage == "briefing":
            self.resolve_camp(game, "balanced")
        if window.stage == "release":
            self.resolve_release(game, "compensate")
        if window.stage == "pre_match":
            self.set_match_mandate(game, "private_target")
        return window

    def _require_stage(self, game, stage: str) -> MatchWindow:
        if not game.can_act:
            raise RuntimeError("successor-government national-team choices are not player-controlled")
        window = self.sync(game)
        if window is None or window.stage != stage:
            raise RuntimeError(f"national-team window is not at stage {stage!r}")
        return window

    def _find_result(self, game, window: MatchWindow) -> MatchResult | None:
        international = game.current_campaign.football.international
        for result in reversed(international.results):
            if (
                result.month == window.local_match_month
                and international.user_code in {result.home_id, result.away_id}
            ):
                return result
        return None

    def _result_for_user(self, game, result: MatchResult) -> tuple[str, int, int]:
        code = game.current_campaign.football.international.user_code
        if result.home_id == code:
            goals_for, goals_against = result.home_goals, result.away_goals
        else:
            goals_for, goals_against = result.away_goals, result.home_goals
        outcome = "win" if goals_for > goals_against else "draw" if goals_for == goals_against else "loss"
        return outcome, goals_for, goals_against

    def _window_outcome(self, game, window: MatchWindow) -> str:
        if not window.result:
            return "unknown"
        code = game.current_campaign.football.international.user_code
        home = window.result["home_id"] == code
        goals_for = window.result["home_goals"] if home else window.result["away_goals"]
        goals_against = window.result["away_goals"] if home else window.result["home_goals"]
        return "win" if goals_for > goals_against else "draw" if goals_for == goals_against else "loss"

    def _new_coach(self, global_month: int, index: int) -> HeadCoachProfile:
        name, philosophy = self.COACH_ROTATION[index % len(self.COACH_ROTATION)]
        return HeadCoachProfile(
            id=f"head-coach-{index + 1}",
            name=name,
            philosophy=philosophy,
            appointed_global_month=global_month,
            contract_end_global_month=global_month + 24,
            public_reputation=0.56 + 0.03 * (index % 3),
            chairman_trust=0.56,
            job_security=0.58,
            media_pressure=0.36,
        )

    @staticmethod
    def _window_to_dict(window: MatchWindow) -> dict[str, Any]:
        payload = asdict(window)
        payload["squad"] = [asdict(item) for item in window.squad]
        payload["disputes"] = [asdict(item) for item in window.disputes]
        return payload

    @staticmethod
    def _window_from_dict(data: dict[str, Any]) -> MatchWindow:
        payload = dict(data)
        payload["squad"] = tuple(SquadMember(**item) for item in payload.get("squad", []))
        payload["omitted_players"] = tuple(payload.get("omitted_players", []))
        payload["disputes"] = [ClubReleaseDispute(**item) for item in payload.get("disputes", [])]
        payload["unavailable_player_ids"] = list(payload.get("unavailable_player_ids", []))
        payload["notes"] = list(payload.get("notes", []))
        return MatchWindow(**payload)
