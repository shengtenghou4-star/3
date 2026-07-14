"""Replay-safe stadium matchday scenes from the association chairman's seat.

The official football engine still owns the result. This layer controls protocol, guests,
public presence and the chairman's conduct before and after the match.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
import hashlib
import json
import random
from typing import Any

from .matchday_replay import ReplayableNationalTeamCommandRuntime
from .national_team_command import HeadCoachProfile, MatchWindow, _seed


STADIUM_RUNTIME_VERSION = 2


@dataclass(frozen=True, slots=True)
class ChairmanBoxGuest:
    name: str
    role: str
    constituency: str
    posture: str


@dataclass(frozen=True, slots=True)
class MatchMoment:
    minute: int
    phase: str
    kind: str
    headline: str
    detail: str
    score_for: int
    score_against: int


@dataclass(slots=True)
class StadiumScene:
    window_id: str
    stage: str = "planned"
    arrival_choice: str = ""
    arrival_label: str = ""
    arrival_note: str = ""
    guest_list: tuple[ChairmanBoxGuest, ...] = ()
    camera_focus: str = ""
    atmosphere: str = ""
    moments: tuple[MatchMoment, ...] = ()
    halftime_score: str = ""
    final_score: str = ""
    xg_line: str = ""
    post_whistle_choice: str = ""
    post_whistle_label: str = ""
    mixed_zone_choice: str = ""
    mixed_zone_label: str = ""
    media_frame: str = ""
    notes: list[str] = field(default_factory=list)


class StadiumNationalTeamCommandRuntime(ReplayableNationalTeamCommandRuntime):
    ARRIVAL_CHOICES: dict[str, dict[str, Any]] = {
        "institutional": {
            "label": "按国家队正式礼宾方案入场",
            "cost": 180_000.0,
            "fan_delta": 0.0,
            "coach_trust": 0.01,
            "pressure": 0.0,
            "expectation": 0.0,
            "note": "主席与对方足协主席、体育主管部门代表和前国脚共同进入包厢，保持正常礼宾距离。",
        },
        "grassroots": {
            "label": "把包厢中心位置让给青训与球迷代表",
            "cost": 260_000.0,
            "fan_delta": 0.006,
            "coach_trust": 0.01,
            "pressure": -0.01,
            "expectation": -0.02,
            "note": "削减商业嘉宾席位，邀请基层教练、女足少年队和长期客场球迷进入主席包厢。",
        },
        "showcase": {
            "label": "把比赛办成高规格国家体育展示",
            "cost": 850_000.0,
            "fan_delta": -0.003,
            "coach_trust": -0.02,
            "pressure": 0.06,
            "expectation": 0.08,
            "note": "高级别官员、主要赞助商与转播方集中入席，镜头和结果压力明显上升。",
        },
    }

    POST_WHISTLE_CHOICES: dict[str, str] = {
        "stay_visible": "留在包厢前排，完成握手并面对终场镜头",
        "go_tunnel": "终场后进入球员通道，只做慰问不谈战术",
        "early_exit": "从内部通道离场，由新闻官先行处理媒体",
    }

    MIXED_ZONE_CHOICES: dict[str, str] = {
        "own_result": "公开承担协会层面的结果与准备责任",
        "protect_coach": "明确维护主教练的技术权力和更衣室秩序",
        "announce_review": "宣布连夜启动数据、医疗与征调专项复盘",
    }

    def __init__(self) -> None:
        super().__init__()
        self.stadium_scenes: dict[str, StadiumScene] = {}

    def scene_for_window(self, window_id: str) -> StadiumScene | None:
        return self.stadium_scenes.get(window_id)

    def sync(self, game) -> MatchWindow | None:
        window = super().sync(game)
        if window is None:
            return None
        if window.stage == "awaiting_match":
            arrival_date = date.fromisoformat(window.match_date) - timedelta(days=1)
            if game.calendar.current_date >= arrival_date:
                scene = self._ensure_scene(window)
                if not scene.arrival_choice:
                    window.stage = "stadium_arrival"
                    scene.stage = "arrival"
        return window

    def resolve_stadium_arrival(self, game, choice: str) -> MatchWindow:
        window = self._require_stadium_stage(game, "stadium_arrival")
        if choice not in self.ARRIVAL_CHOICES:
            raise ValueError(f"unknown stadium arrival choice {choice!r}")
        policy = self.ARRIVAL_CHOICES[choice]
        state = game.current_campaign.engine.state
        cost = min(float(policy["cost"]), max(0.0, float(state.treasury)))
        game.world.apply_external_action(
            "stadium_arrival_protocol",
            {
                "state_deltas": {
                    "treasury": -cost,
                    "fan_trust": float(policy["fan_delta"]),
                },
                "audit_note": (
                    f"stadium protocol approved for {window.id} — {policy['label']}; "
                    f"cost {cost:.0f}"
                ),
            },
        )
        self.coach.chairman_trust = self._clamp(
            self.coach.chairman_trust + float(policy["coach_trust"])
        )
        self.coach.media_pressure = self._clamp(
            self.coach.media_pressure + float(policy["pressure"])
        )
        window.public_expectation = self._clamp(
            window.public_expectation + float(policy["expectation"])
        )
        window.treasury_cost += cost
        scene = self._ensure_scene(window)
        scene.arrival_choice = choice
        scene.arrival_label = str(policy["label"])
        scene.arrival_note = str(policy["note"])
        scene.guest_list = self._build_guest_list(window, choice)
        scene.camera_focus = self._camera_focus(choice)
        scene.atmosphere = self._atmosphere(window, choice)
        scene.stage = "seated"
        scene.notes.append(f"主席包厢礼宾与座次支出¥{cost / 1_000_000:.2f}M。")
        window.stage = "awaiting_match"
        window.notes.append(str(policy["note"]))
        return window

    def prepare_month(self, game, target_local_month: int) -> float:
        active = self.active_window
        if active is not None and active.stage == "stadium_arrival":
            self.resolve_stadium_arrival(game, "institutional")
        return super().prepare_month(game, target_local_month)

    def settle_month(self, game, settled_local_month: int, base_strength: float) -> None:
        active = self.active_window
        super().settle_month(game, settled_local_month, base_strength)
        if active is None or active.local_match_month != settled_local_month:
            return
        if not active.result:
            return
        scene = self._ensure_scene(active)
        scene.moments = self._build_match_moments(game, active)
        scene.halftime_score = self._score_at(scene.moments, 45)
        scene.final_score = self._score_at(scene.moments, 90)
        scene.xg_line = self._xg_line(game, active)
        scene.stage = "post_whistle"
        active.stage = "post_whistle"
        active.notes.append("正式赛果已经进入主席包厢终场流程，尚未完成公开露面与混合采访区回应。")

    def resolve_box_reaction(self, game, choice: str) -> MatchWindow:
        window = self._require_stadium_stage(game, "post_whistle")
        if choice not in self.POST_WHISTLE_CHOICES:
            raise ValueError(f"unknown post-whistle choice {choice!r}")
        outcome = self._window_outcome(game, window)
        fan_delta = 0.0
        trust_delta = 0.0
        pressure_delta = 0.0
        if choice == "stay_visible":
            fan_delta = 0.007 if outcome == "loss" else 0.003
            trust_delta = 0.015
            frame = "终场镜头完整记录主席留在前排、与客队代表握手并向看台致意。"
        elif choice == "go_tunnel":
            fan_delta = 0.002 if outcome == "loss" else 0.0
            trust_delta = 0.025
            pressure_delta = 0.01
            frame = "主席在球员通道短暂停留，只表达支持与慰问，没有进入技战术讨论。"
        else:
            fan_delta = -0.012 if outcome == "loss" else -0.004
            trust_delta = -0.015
            pressure_delta = 0.05
            frame = "主席从内部通道离场的画面迅速成为赛后报道中心。"
        game.world.apply_external_action(
            "stadium_post_whistle_presence",
            {
                "state_deltas": {"fan_trust": fan_delta},
                "audit_note": f"post-whistle presidential presence — {self.POST_WHISTLE_CHOICES[choice]}",
            },
        )
        self.coach.chairman_trust = self._clamp(self.coach.chairman_trust + trust_delta)
        self.coach.media_pressure = self._clamp(self.coach.media_pressure + pressure_delta)
        scene = self._ensure_scene(window)
        scene.post_whistle_choice = choice
        scene.post_whistle_label = self.POST_WHISTLE_CHOICES[choice]
        scene.media_frame = frame
        scene.stage = "mixed_zone"
        scene.notes.append(frame)
        window.stage = "mixed_zone"
        return window

    def resolve_mixed_zone(self, game, choice: str) -> MatchWindow:
        window = self._require_stadium_stage(game, "mixed_zone")
        if choice not in self.MIXED_ZONE_CHOICES:
            raise ValueError(f"unknown mixed-zone choice {choice!r}")
        outcome = self._window_outcome(game, window)
        fan_delta = 0.0
        if choice == "own_result":
            fan_delta = 0.009 if outcome == "loss" else 0.003
            self.coach.chairman_trust = self._clamp(self.coach.chairman_trust + 0.01)
            frame = "主席先承担协会准备、保障和任命责任，没有把结果立即推给球员。"
        elif choice == "protect_coach":
            fan_delta = -0.003 if outcome == "loss" else 0.002
            self.coach.chairman_trust = self._clamp(self.coach.chairman_trust + 0.04)
            self.coach.media_pressure = self._clamp(self.coach.media_pressure - 0.02)
            frame = "主席公开确认主教练仍拥有完整技术权力，赛后不接受临场越权追问。"
        else:
            fan_delta = 0.006 if outcome == "loss" else -0.002
            self.coach.job_security = self._clamp(self.coach.job_security - 0.03)
            self.coach.media_pressure = self._clamp(self.coach.media_pressure + 0.03)
            frame = "主席宣布专项复盘，媒体立即把注意力转向技术团队与后续人事。"
        game.world.apply_external_action(
            "stadium_mixed_zone_statement",
            {
                "state_deltas": {"fan_trust": fan_delta},
                "audit_note": f"mixed-zone statement — {self.MIXED_ZONE_CHOICES[choice]}",
            },
        )
        scene = self._ensure_scene(window)
        scene.mixed_zone_choice = choice
        scene.mixed_zone_label = self.MIXED_ZONE_CHOICES[choice]
        scene.media_frame = frame
        scene.stage = "office_review"
        scene.notes.append(frame)
        window.stage = "review"
        window.notes.append(frame)
        return window

    def to_dict(self) -> dict[str, Any]:
        payload = self._legacy_payload()
        payload["version"] = STADIUM_RUNTIME_VERSION
        payload["stadium_scenes"] = {
            key: self._scene_to_dict(scene)
            for key, scene in sorted(self.stadium_scenes.items())
        }
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StadiumNationalTeamCommandRuntime":
        version = int(data.get("version", 0))
        if version not in {1, STADIUM_RUNTIME_VERSION}:
            raise ValueError("unsupported stadium matchday format")
        runtime = cls.__new__(cls)
        runtime.coach = HeadCoachProfile(**data["coach"])
        runtime.coach_history = [
            HeadCoachProfile(**item) for item in data.get("coach_history", [])
        ]
        runtime.windows = [
            runtime._window_from_dict(item) for item in data.get("windows", [])
        ]
        runtime.active_window_id = data.get("active_window_id")
        runtime.stadium_scenes = (
            {
                key: runtime._scene_from_dict(value)
                for key, value in data.get("stadium_scenes", {}).items()
            }
            if version == STADIUM_RUNTIME_VERSION
            else {}
        )
        return runtime

    def legacy_fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self._legacy_payload(), ensure_ascii=False, sort_keys=True
            ).encode("utf-8")
        ).hexdigest()

    def fingerprint(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _legacy_payload(self) -> dict[str, Any]:
        return {
            "version": 1,
            "coach": asdict(self.coach),
            "coach_history": [asdict(item) for item in self.coach_history],
            "windows": [self._window_to_dict(item) for item in self.windows],
            "active_window_id": self.active_window_id,
        }

    def _require_stadium_stage(self, game, stage: str) -> MatchWindow:
        if not game.can_act:
            raise RuntimeError("successor-government stadium choices are not player-controlled")
        window = self.sync(game)
        if window is None or window.stage != stage:
            raise RuntimeError(f"stadium matchday is not at stage {stage!r}")
        return window

    def _ensure_scene(self, window: MatchWindow) -> StadiumScene:
        scene = self.stadium_scenes.get(window.id)
        if scene is None:
            scene = StadiumScene(window_id=window.id)
            self.stadium_scenes[window.id] = scene
        return scene

    def _build_guest_list(
        self, window: MatchWindow, choice: str
    ) -> tuple[ChairmanBoxGuest, ...]:
        common = [
            ChairmanBoxGuest(
                "顾明川",
                "国家体育委员会副主任",
                "政府体育主管部门",
                "关注国家队形象与赛场秩序",
            ),
            ChairmanBoxGuest(
                "周启和",
                f"{window.opponent_name}足协主席",
                "来访代表团",
                "礼貌观察并维护本方竞赛利益",
            ),
            ChairmanBoxGuest(
                "韩立涛",
                "国家队前队长",
                "退役国脚与技术共同体",
                "支持球队但不愿替现任教练背书",
            ),
        ]
        if choice == "grassroots":
            common.extend(
                [
                    ChairmanBoxGuest(
                        "林雪岚",
                        "全国球迷联络会代表",
                        "长期主客场球迷",
                        "要求足协面对普通支持者",
                    ),
                    ChairmanBoxGuest(
                        "马敬源",
                        "县级青训中心教练",
                        "基层青训网络",
                        "关注国家队是否真正回馈培养体系",
                    ),
                ]
            )
        elif choice == "showcase":
            common.extend(
                [
                    ChairmanBoxGuest(
                        "陆承泽",
                        "国家队首席合作伙伴董事长",
                        "商业赞助体系",
                        "期待高曝光与可控的品牌画面",
                    ),
                    ChairmanBoxGuest(
                        "宋岚清",
                        "国家电视体育频道总监",
                        "转播与公共舆论",
                        "关注终场镜头和主席公开反应",
                    ),
                ]
            )
        else:
            common.append(
                ChairmanBoxGuest(
                    "许闻达",
                    "联赛俱乐部代表",
                    "职业俱乐部理事会",
                    "观察征调政策和球员保护承诺",
                )
            )
        return tuple(common)

    def _build_match_moments(
        self, game, window: MatchWindow
    ) -> tuple[MatchMoment, ...]:
        result = window.result or {}
        code = game.current_campaign.football.international.user_code
        user_home = result.get("home_id") == code
        goals_for = int(result.get("home_goals", 0) if user_home else result.get("away_goals", 0))
        goals_against = int(result.get("away_goals", 0) if user_home else result.get("home_goals", 0))
        rng = random.Random(_seed(f"stadium-timeline:{window.id}:{goals_for}:{goals_against}"))
        total_goals = goals_for + goals_against
        minute_pool = list(range(7, 90))
        goal_minutes = sorted(rng.sample(minute_pool, k=min(total_goals, len(minute_pool))))
        sides = ["for"] * goals_for + ["against"] * goals_against
        rng.shuffle(sides)
        scorers = [
            item.player_name
            for item in window.available_squad
            if item.position in {"ATT", "MID"}
        ] or [item.player_name for item in window.available_squad]
        moments: list[MatchMoment] = [
            MatchMoment(
                1,
                "上半场",
                "kickoff",
                "比赛开始",
                "主席包厢全体起立，正式比赛由既定技术团队接管。",
                0,
                0,
            )
        ]
        running_for = 0
        running_against = 0
        for index, (minute, side) in enumerate(zip(goal_minutes, sides)):
            if side == "for":
                running_for += 1
                actor = scorers[index % len(scorers)] if scorers else "国家队前锋"
                headline = f"{actor}为Longhua进球"
                detail = "包厢内先短暂屏息，随后主场声浪压过现场播报。"
            else:
                running_against += 1
                headline = f"{window.opponent_name}取得进球"
                detail = "来访代表席起身鼓掌，转播镜头立即切向主席与主教练席。"
            moments.append(
                MatchMoment(
                    minute,
                    "上半场" if minute <= 45 else "下半场",
                    "goal",
                    headline,
                    detail,
                    running_for,
                    running_against,
                )
            )
        halftime_for, halftime_against = self._running_score(moments, 45)
        moments.append(
            MatchMoment(
                45,
                "中场",
                "halftime",
                "中场休息",
                "技术人员只向主席办公室通报医疗、安保与赛场秩序；没有提供临场换人按钮。",
                halftime_for,
                halftime_against,
            )
        )
        xg_for, xg_against = self._xg_for_user(game, window)
        if xg_for > goals_for + 0.35:
            minute = rng.choice([18, 33, 58, 72, 84])
            before_for, before_against = self._running_score(moments, minute)
            moments.append(
                MatchMoment(
                    minute,
                    "上半场" if minute <= 45 else "下半场",
                    "chance",
                    "Longhua错失明显机会",
                    "包厢内的反应无法改变教练组已经作出的技术决定。",
                    before_for,
                    before_against,
                )
            )
        if xg_against > goals_against + 0.35:
            minute = rng.choice([14, 29, 55, 69, 82])
            before_for, before_against = self._running_score(moments, minute)
            moments.append(
                MatchMoment(
                    minute,
                    "上半场" if minute <= 45 else "下半场",
                    "chance",
                    f"{window.opponent_name}制造重大险情",
                    "安保和礼宾人员保持沉默，客队包厢已经准备庆祝。",
                    before_for,
                    before_against,
                )
            )
        moments.sort(key=lambda item: (item.minute, self._moment_order(item.kind)))
        moments.append(
            MatchMoment(
                90,
                "终场",
                "fulltime",
                "终场哨响",
                "正式赛果锁定，比赛无法通过赛后决定重写。",
                goals_for,
                goals_against,
            )
        )
        return tuple(moments)

    def _xg_for_user(self, game, window: MatchWindow) -> tuple[float, float]:
        result = window.result or {}
        code = game.current_campaign.football.international.user_code
        if result.get("home_id") == code:
            return float(result.get("home_xg", 0.0)), float(result.get("away_xg", 0.0))
        return float(result.get("away_xg", 0.0)), float(result.get("home_xg", 0.0))

    def _xg_line(self, game, window: MatchWindow) -> str:
        xg_for, xg_against = self._xg_for_user(game, window)
        return f"{xg_for:.2f}-{xg_against:.2f}"

    @staticmethod
    def _running_score(
        moments: list[MatchMoment] | tuple[MatchMoment, ...], minute: int
    ) -> tuple[int, int]:
        score_for = 0
        score_against = 0
        for item in moments:
            if item.minute <= minute and item.kind == "goal":
                score_for = item.score_for
                score_against = item.score_against
        return score_for, score_against

    @classmethod
    def _score_at(
        cls, moments: list[MatchMoment] | tuple[MatchMoment, ...], minute: int
    ) -> str:
        score_for, score_against = cls._running_score(moments, minute)
        return f"{score_for}-{score_against}"

    @staticmethod
    def _moment_order(kind: str) -> int:
        return {"kickoff": 0, "chance": 1, "goal": 2, "halftime": 3, "fulltime": 4}.get(kind, 9)

    @staticmethod
    def _camera_focus(choice: str) -> str:
        if choice == "grassroots":
            return "转播不断捕捉青训教练、少年球员与长期客场球迷的反应。"
        if choice == "showcase":
            return "国家级转播机位把主席、官员和赞助商置于持续近景。"
        return "镜头按正式礼宾方案在主席、来访代表和看台之间切换。"

    @staticmethod
    def _atmosphere(window: MatchWindow, choice: str) -> str:
        base = "主场看台逐渐形成压迫声浪" if window.venue == "主场" else "客场安保把来访代表团与主队看台严格隔离"
        if choice == "showcase":
            return base + "，仪式规格越高，任何失误都更像公共事件。"
        if choice == "grassroots":
            return base + "，包厢中的基层代表让现场气氛更接近普通支持者。"
        return base + "，礼宾部门维持克制、正式的比赛秩序。"

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _scene_to_dict(scene: StadiumScene) -> dict[str, Any]:
        payload = asdict(scene)
        payload["guest_list"] = [asdict(item) for item in scene.guest_list]
        payload["moments"] = [asdict(item) for item in scene.moments]
        return payload

    @staticmethod
    def _scene_from_dict(data: dict[str, Any]) -> StadiumScene:
        payload = dict(data)
        payload["guest_list"] = tuple(
            ChairmanBoxGuest(**item) for item in payload.get("guest_list", [])
        )
        payload["moments"] = tuple(
            MatchMoment(**item) for item in payload.get("moments", [])
        )
        payload["notes"] = list(payload.get("notes", []))
        return StadiumScene(**payload)
