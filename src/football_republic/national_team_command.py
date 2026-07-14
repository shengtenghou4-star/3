"""Persistent national-team command centre for the football-association chairman.

The chairman never selects a formation or substitutes players. The runtime models the
parts of an international window that genuinely reach the association president:
public posture before the match, club-release and player-welfare emphasis, the national
political meaning of the result, and the decision to retain, review or dismiss the coach.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any


NATIONAL_TEAM_COMMAND_VERSION = 1

DIRECTIVE_OPTIONS: dict[str, dict[str, Any]] = {
    "back_staff": {
        "label": "公开支持教练组",
        "summary": "主席明确维护专业分工，不把赛前舆论压力转嫁给教练和球员。",
        "public_line": "足协尊重教练组的专业判断，主席负责保障环境与资源。",
        "strength_delta": 0.15,
        "recovery_credit": 0.6,
    },
    "set_result_target": {
        "label": "明确提出结果目标",
        "summary": "主席公开提出本场必须拿分，把政治责任和竞技压力同时压到窗口内。",
        "public_line": "这场比赛必须体现国家队的竞争力，结果将进入正式考核。",
        "strength_delta": 0.65,
        "recovery_credit": 0.0,
    },
    "protect_players": {
        "label": "优先协调放人与球员保护",
        "summary": "主席要求俱乐部完整放人，同时压缩无效训练与商业活动。",
        "public_line": "足协将保障国家队征调，也不会把球员当作可以无限透支的资源。",
        "strength_delta": 0.30,
        "recovery_credit": 2.0,
    },
    "delegated": {
        "label": "授权技术部门按既定方案执行",
        "summary": "主席不追加公开指标，只要求技术总监按程序报告风险与结果。",
        "public_line": "本窗口按既定技术方案推进，赛后依据完整材料作出评价。",
        "strength_delta": 0.0,
        "recovery_credit": 0.4,
    },
}

REVIEW_OPTIONS: dict[str, dict[str, str]] = {
    "retain_and_back": {
        "label": "继续信任并公开担责",
        "summary": "维持教练组稳定，主席对外承担用人责任。",
    },
    "retain_with_review": {
        "label": "留任并启动专项复盘",
        "summary": "不立即换帅，但要求技术、体能和选人环节提交独立复盘。",
    },
    "final_warning": {
        "label": "留任但进入最后考察期",
        "summary": "公开保留教练职位，同时把下一窗口设为明确生死线。",
    },
    "dismiss": {
        "label": "解除主教练职务",
        "summary": "支付解约与过渡成本，由技术总监启动新教练遴选。",
    },
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _bounded_delta(current: float, requested: float, low: float, high: float) -> float:
    return _clamp(current + requested, low, high) - current


def _next_local_month(local_month: int) -> int:
    return 1 if local_month >= 24 else local_month + 1


@dataclass(slots=True)
class MatchDirective:
    id: str
    global_month: int
    local_month: int
    round_number: int
    opponent_code: str
    opponent_name: str
    venue: str
    option_id: str
    option_title: str
    summary: str
    public_line: str
    strength_delta: float
    recovery_credit: float
    applied: bool = False


@dataclass(slots=True)
class MatchReview:
    id: str
    match_id: str
    global_month: int
    local_month: int
    round_number: int
    opponent_name: str
    venue: str
    scoreline: str
    result_label: str
    xg_summary: str
    table_position: int
    directive_title: str
    coach_name: str
    status: str = "pending"
    resolution_id: str = ""
    resolution_title: str = ""
    public_line: str = ""
    effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CoachingChange:
    global_month: int
    outgoing_name: str
    incoming_name: str
    reason: str
    cost: float


@dataclass(slots=True)
class NationalTeamCommandRuntime:
    coach_name: str = "梁振岳"
    coach_status: str = "在任"
    directives: list[MatchDirective] = field(default_factory=list)
    reviews: list[MatchReview] = field(default_factory=list)
    coaching_changes: list[CoachingChange] = field(default_factory=list)

    @property
    def pending_review(self) -> MatchReview | None:
        return next(
            (item for item in reversed(self.reviews) if item.status == "pending"),
            None,
        )

    def directive_for_global_month(self, global_month: int) -> MatchDirective | None:
        return next(
            (item for item in reversed(self.directives) if item.global_month == global_month),
            None,
        )

    def next_fixture(self, game) -> dict[str, Any] | None:
        football = game.current_campaign.football
        international = football.international
        local_month = _next_local_month(game.local_month)
        if local_month not in international.round_months:
            return None
        round_index = international.round_months.index(local_month)
        fixture = next(
            (
                pair
                for pair in international.schedule[round_index]
                if international.user_code in pair
            ),
            None,
        )
        if fixture is None:
            return None
        home_code, away_code = fixture
        user_home = home_code == international.user_code
        opponent_code = away_code if user_home else home_code
        opponent = international.teams[opponent_code]
        return {
            "global_month": game.global_month + 1,
            "local_month": local_month,
            "round_number": round_index + 1,
            "opponent_code": opponent_code,
            "opponent_name": opponent.name,
            "opponent_strength": float(opponent.strength),
            "venue": "主场" if user_home else "客场",
        }

    def choose_directive(self, game, option_id: str) -> MatchDirective:
        if option_id not in DIRECTIVE_OPTIONS:
            raise ValueError(f"unknown national-team directive {option_id!r}")
        fixture = self.next_fixture(game)
        if fixture is None:
            raise RuntimeError("there is no national-team fixture in the next settlement month")
        existing = self.directive_for_global_month(fixture["global_month"])
        if existing is not None and existing.applied:
            raise RuntimeError("the signed match directive has already entered execution")
        if existing is not None:
            self.directives.remove(existing)
        option = DIRECTIVE_OPTIONS[option_id]
        directive = MatchDirective(
            id=f"directive-g{fixture['global_month']}-r{fixture['round_number']}",
            global_month=fixture["global_month"],
            local_month=fixture["local_month"],
            round_number=fixture["round_number"],
            opponent_code=fixture["opponent_code"],
            opponent_name=fixture["opponent_name"],
            venue=fixture["venue"],
            option_id=option_id,
            option_title=str(option["label"]),
            summary=str(option["summary"]),
            public_line=str(option["public_line"]),
            strength_delta=float(option["strength_delta"]),
            recovery_credit=float(option["recovery_credit"]),
        )
        self.directives.append(directive)
        return directive

    def prepare_month(self, game) -> MatchDirective | None:
        fixture = self.next_fixture(game)
        if fixture is None:
            return None
        directive = self.directive_for_global_month(fixture["global_month"])
        if directive is None or directive.applied:
            return directive
        state = game.current_campaign.engine.state
        strength_delta = _bounded_delta(
            float(state.national_team_strength),
            directive.strength_delta,
            20.0,
            95.0,
        )
        game.world.apply_external_action(
            "national_team_match_directive_applied",
            {
                "state_deltas": {"national_team_strength": strength_delta},
                "audit_note": (
                    f"national-team directive {directive.id} entered execution — "
                    f"{directive.option_title}"
                ),
            },
        )
        directive.applied = True
        return directive

    def settle_month(self, game) -> MatchReview | None:
        football = game.current_campaign.football
        international = football.international
        local_month = game.local_month
        if local_month not in international.round_months:
            return None
        round_number = international.round_months.index(local_month) + 1
        match_id = f"g{game.global_month}-r{round_number}"
        if any(item.match_id == match_id for item in self.reviews):
            return None
        result = next(
            (
                item
                for item in reversed(international.results)
                if item.month == local_month
                and international.user_code in {item.home_id, item.away_id}
            ),
            None,
        )
        if result is None:
            return None

        user_home = result.home_id == international.user_code
        opponent_name = result.away_name if user_home else result.home_name
        goals_for = result.home_goals if user_home else result.away_goals
        goals_against = result.away_goals if user_home else result.home_goals
        xg_for = result.home_xg if user_home else result.away_xg
        xg_against = result.away_xg if user_home else result.home_xg
        result_label = "胜" if goals_for > goals_against else "平" if goals_for == goals_against else "负"
        directive = self.directive_for_global_month(game.global_month)

        if directive is not None and directive.recovery_credit > 0:
            state = game.current_campaign.engine.state
            continuity_delta = _bounded_delta(
                float(state.national_team_strength),
                0.05 * directive.recovery_credit,
                20.0,
                95.0,
            )
            game.world.apply_external_action(
                "national_team_window_recovery",
                {
                    "state_deltas": {"national_team_strength": continuity_delta},
                    "audit_note": (
                        f"player-welfare and release coordination completed after "
                        f"international round {round_number}"
                    ),
                },
            )

        review = MatchReview(
            id=f"review-{match_id}",
            match_id=match_id,
            global_month=game.global_month,
            local_month=local_month,
            round_number=round_number,
            opponent_name=opponent_name,
            venue="主场" if user_home else "客场",
            scoreline=f"{goals_for}-{goals_against}",
            result_label=result_label,
            xg_summary=f"{xg_for:.2f}-{xg_against:.2f}",
            table_position=int(international.user_position),
            directive_title=directive.option_title if directive is not None else "未追加主席赛前指令",
            coach_name=self.coach_name,
        )
        self.reviews.append(review)
        self.coach_status = "赛后待主席决定"
        return review

    def resolve_review(self, game, review_id: str, option_id: str) -> MatchReview:
        if option_id not in REVIEW_OPTIONS:
            raise ValueError(f"unknown match review option {option_id!r}")
        review = next((item for item in self.reviews if item.id == review_id), None)
        if review is None:
            raise ValueError(f"unknown match review {review_id!r}")
        if review.status != "pending":
            raise RuntimeError("this match review has already been resolved")

        state = game.current_campaign.engine.state
        option = REVIEW_OPTIONS[option_id]
        effects: list[str] = []
        won = review.result_label == "胜"
        lost = review.result_label == "负"
        state_deltas: dict[str, float] = {}

        if option_id == "retain_and_back":
            self.coach_status = "获主席公开支持"
            trust_delta = 0.008 if won else -0.004 if lost else 0.002
            state_deltas["fan_trust"] = trust_delta
            state_deltas["national_team_strength"] = _bounded_delta(
                float(state.national_team_strength),
                0.20,
                20.0,
                95.0,
            )
            public_line = "主教练继续带队，主席对选帅和保障体系承担责任。"
            effects.append("教练组延续性得到保护")
        elif option_id == "retain_with_review":
            self.coach_status = "专项复盘中"
            state_deltas["national_team_strength"] = _bounded_delta(
                float(state.national_team_strength),
                -0.10,
                20.0,
                95.0,
            )
            public_line = "主教练暂时留任，技术、体能和选人环节接受独立复盘。"
            effects.append("下一窗口前必须提交专项复盘")
        elif option_id == "final_warning":
            self.coach_status = "最后考察期"
            state_deltas["fan_trust"] = 0.005 if lost else -0.003
            state_deltas["national_team_strength"] = _bounded_delta(
                float(state.national_team_strength),
                -0.25,
                20.0,
                95.0,
            )
            public_line = "主教练继续履职，但下一比赛窗口将决定其去留。"
            effects.append("教练职位进入明确生死线")
        else:
            outgoing = self.coach_name
            incoming = self._next_coach_name()
            cost = min(float(state.treasury), 1_200_000.0)
            state_deltas["treasury"] = -cost
            state_deltas["national_team_strength"] = _bounded_delta(
                float(state.national_team_strength),
                -0.80,
                20.0,
                95.0,
            )
            state_deltas["fan_trust"] = 0.012 if lost else -0.010
            self.coach_name = incoming
            self.coach_status = "新任过渡期"
            self.coaching_changes.append(
                CoachingChange(
                    global_month=game.global_month,
                    outgoing_name=outgoing,
                    incoming_name=incoming,
                    reason=f"预选赛第{review.round_number}轮后解除职务",
                    cost=cost,
                )
            )
            public_line = f"{outgoing}离任，{incoming}接手国家队并进入过渡窗口。"
            effects.extend(
                [
                    f"解约与过渡成本¥{cost / 1_000_000:.1f}M",
                    "新教练短期磨合降低比赛准备度",
                ]
            )

        game.world.apply_external_action(
            "national_team_match_review_resolved",
            {
                "state_deltas": state_deltas,
                "audit_note": (
                    f"match review {review.id} resolved — {option['label']}"
                ),
            },
        )
        review.status = "resolved"
        review.resolution_id = option_id
        review.resolution_title = str(option["label"])
        review.public_line = public_line
        review.effects.extend(effects)
        return review

    def _next_coach_name(self) -> str:
        names = ("沈砺锋", "韩宗岳", "陆启明", "顾承川", "赵维新")
        return names[len(self.coaching_changes) % len(names)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": NATIONAL_TEAM_COMMAND_VERSION,
            "coach_name": self.coach_name,
            "coach_status": self.coach_status,
            "directives": [asdict(item) for item in self.directives],
            "reviews": [asdict(item) for item in self.reviews],
            "coaching_changes": [asdict(item) for item in self.coaching_changes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NationalTeamCommandRuntime":
        if int(data.get("version", 0)) != NATIONAL_TEAM_COMMAND_VERSION:
            raise ValueError("unsupported national-team command format")
        return cls(
            coach_name=str(data.get("coach_name", "梁振岳")),
            coach_status=str(data.get("coach_status", "在任")),
            directives=[MatchDirective(**item) for item in data.get("directives", [])],
            reviews=[MatchReview(**item) for item in data.get("reviews", [])],
            coaching_changes=[
                CoachingChange(**item) for item in data.get("coaching_changes", [])
            ],
        )

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
