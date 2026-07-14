"""Adaptive, event-driven time flow for the presidential career.

The football, finance and political simulation remains authoritative at monthly
settlement boundaries.  This module adds a player-facing calendar that moves in days or
weeks, slows before consequential public events and re-evaluates after every settlement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any, Iterable


ADAPTIVE_TIME_VERSION = 1
CALENDAR_EPOCH = date(2026, 1, 5)


@dataclass(frozen=True, slots=True)
class AttentionSignal:
    code: str
    level: int
    headline: str
    detail: str
    blocking: bool = False
    source: str = "公开状态"


@dataclass(frozen=True, slots=True)
class TimeRecommendation:
    pace: str
    days: int
    button_label: str
    rationale: str
    attention_label: str
    next_checkpoint: str
    signals: tuple[AttentionSignal, ...]


@dataclass(frozen=True, slots=True)
class TimeAdvanceResult:
    mode: str
    pace: str
    start_date: str
    end_date: str
    days_elapsed: int
    world_months_elapsed: int
    stopped_reason: str
    changes: tuple[str, ...]
    signals_after: tuple[AttentionSignal, ...]


@dataclass(slots=True)
class AdaptiveCalendar:
    current_date: date = CALENDAR_EPOCH
    last_result: TimeAdvanceResult | None = None
    history: list[TimeAdvanceResult] = field(default_factory=list)

    @classmethod
    def from_world_month(cls, global_month: int) -> "AdaptiveCalendar":
        return cls(CALENDAR_EPOCH if global_month == 0 else month_start(global_month))

    @property
    def date_label(self) -> str:
        return self.current_date.strftime("%Y年%m月%d日")

    @property
    def weekday_label(self) -> str:
        return ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")[
            self.current_date.weekday()
        ]

    @property
    def next_month_boundary(self) -> date:
        return _next_month_start(self.current_date)

    def sync_to_world(self, global_month: int) -> None:
        """Keep the visible calendar from lagging behind authoritative settlement time."""
        target = month_start(global_month)
        if self.current_date < target:
            self.current_date = target

    def attention(self, game) -> tuple[AttentionSignal, ...]:
        return assess_attention(game, self.current_date)

    def recommendation(self, game) -> TimeRecommendation:
        self.sync_to_world(game.global_month)
        signals = self.attention(game)
        level = _highest_level(signals)
        checkpoint = next_public_checkpoint(game, self.current_date)

        if any(item.blocking for item in signals):
            days, pace, button = 0, "暂停", "先处理当前事项"
            rationale = next(item.detail for item in signals if item.blocking)
        elif level >= 4:
            days, pace, button = 1, "危机日", "推进到明天"
            rationale = "当前事项可能在极短时间内改变主席责任或制度后果。"
        elif level == 3:
            days, pace, button = 3, "高压节奏", "推进3天"
            rationale = "关键窗口临近，办公室需要频繁复核而不是整月跳过。"
        elif level == 2:
            days, pace, button = 7, "关注节奏", "推进1周"
            rationale = "存在需要跟踪的公开风险，但尚未要求主席逐日坐镇。"
        elif level == 1:
            days, pace, button = 21, "常规行政", "推进3周"
            rationale = "当前以部门执行和常规协调为主，可以较快推进。"
        else:
            days, pace, button = 45, "平稳期", "按节奏推进"
            rationale = "没有重大事项占据主席注意力；系统会跨周推进并在新风险出现时停下。"

        if checkpoint is not None and days > 0:
            checkpoint_date, checkpoint_label = checkpoint
            distance = (checkpoint_date - self.current_date).days
            if 0 < distance < days:
                days = distance
                button = _days_button_label(days)
                rationale = f"先推进到“{checkpoint_label}”的准备节点。"

        return TimeRecommendation(
            pace=pace,
            days=max(0, days),
            button_label=button,
            rationale=rationale,
            attention_label=_attention_label(level),
            next_checkpoint=(
                f"{checkpoint[0].strftime('%m月%d日')} · {checkpoint[1]}"
                if checkpoint is not None
                else "暂无已知硬节点"
            ),
            signals=signals,
        )

    def advance(self, game, mode: str = "adaptive") -> TimeAdvanceResult:
        """Move visible time without allowing consequential events to be skipped.

        ``deliberate`` moves one day, ``week`` moves at most seven days, ``adaptive``
        follows the recommended pace, and ``fast`` searches for the next meaningful
        checkpoint for at most 120 days.  Every crossed month is settled independently.
        """
        if mode not in {"deliberate", "week", "adaptive", "fast"}:
            raise ValueError(f"unsupported time mode {mode!r}")
        self.sync_to_world(game.global_month)
        start = self.current_date
        initial_signals = self.attention(game)
        initial_level = _highest_level(initial_signals)

        if any(item.blocking for item in initial_signals):
            result = TimeAdvanceResult(
                mode,
                "暂停",
                start.isoformat(),
                start.isoformat(),
                0,
                0,
                next(item.headline for item in initial_signals if item.blocking),
                (),
                initial_signals,
            )
            self._record(result)
            return result

        recommendation = self.recommendation(game)
        requested = {
            "deliberate": 1,
            "week": 7,
            "adaptive": recommendation.days,
            "fast": 120,
        }[mode]
        cap = {0: 120, 1: 21, 2: 7, 3: 3, 4: 1, 5: 0}[initial_level]
        budget = requested if mode == "adaptive" else min(requested, cap)
        planned_stop: tuple[date, str] | None = None

        if mode in {"week", "adaptive", "fast"}:
            checkpoint = next_public_checkpoint(game, self.current_date)
            if checkpoint is not None:
                distance = (checkpoint[0] - self.current_date).days
                if 0 < distance <= budget:
                    budget = distance
                    planned_stop = checkpoint

        remaining = max(0, budget)
        months_elapsed = 0
        changes: list[str] = []
        stopped_reason = "按选定节奏完成推进"
        initial_codes = {item.code for item in initial_signals if item.level >= 2}

        while remaining > 0 and game.can_act:
            boundary = _next_month_start(self.current_date)
            days_to_boundary = (boundary - self.current_date).days
            step = min(remaining, days_to_boundary)
            previous_date = self.current_date
            self.current_date += timedelta(days=step)
            remaining -= step

            if self.current_date != boundary:
                continue

            before_month = game.global_month
            before = _public_snapshot(game)
            game.advance(1, interactive=True)
            if game.global_month == before_month:
                self.current_date = previous_date
                stopped_reason = "时间在未处理的主席事项前停止"
                break

            months_elapsed += game.global_month - before_month
            self.sync_to_world(game.global_month)
            after = _public_snapshot(game)
            changes.extend(_summarize_changes(before, after, game.global_month))
            new_signals = self.attention(game)
            new_level = _highest_level(new_signals)
            new_codes = {item.code for item in new_signals if item.level >= 2}

            if game.current_decision is not None:
                stopped_reason = "新的主席亲签事项已经进入办公室"
                break
            if any(item.blocking for item in new_signals):
                stopped_reason = next(item.headline for item in new_signals if item.blocking)
                break
            if _settlement_requires_review(before, after):
                stopped_reason = "比赛、案件或执行状态在本次月结中发生重要变化"
                break
            if mode == "fast" and (new_level >= 2 or new_codes - initial_codes):
                stopped_reason = "发现新的关注事项，快进自动停止"
                break
            if mode == "adaptive" and (new_level >= 3 or new_level > initial_level):
                stopped_reason = "办公室压力上升，系统自动降低时间速度"
                break

            if remaining > 0 and mode in {"adaptive", "fast"}:
                checkpoint = next_public_checkpoint(game, self.current_date)
                if checkpoint is not None:
                    distance = (checkpoint[0] - self.current_date).days
                    if 0 < distance < remaining:
                        remaining = distance
                        planned_stop = checkpoint

        if planned_stop is not None and self.current_date == planned_stop[0]:
            stopped_reason = f"已进入“{planned_stop[1]}”的准备期"

        after_signals = self.attention(game)
        result = TimeAdvanceResult(
            mode=mode,
            pace=self.recommendation(game).pace,
            start_date=start.isoformat(),
            end_date=self.current_date.isoformat(),
            days_elapsed=(self.current_date - start).days,
            world_months_elapsed=months_elapsed,
            stopped_reason=stopped_reason,
            changes=tuple(changes[-12:]),
            signals_after=after_signals,
        )
        self._record(result)
        return result

    def _record(self, result: TimeAdvanceResult) -> None:
        self.last_result = result
        self.history.append(result)
        self.history = self.history[-40:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": ADAPTIVE_TIME_VERSION,
            "current_date": self.current_date.isoformat(),
            "last_result": _result_to_dict(self.last_result),
            "history": [_result_to_dict(item) for item in self.history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdaptiveCalendar":
        if int(data.get("version", 0)) != ADAPTIVE_TIME_VERSION:
            raise ValueError("unsupported adaptive calendar format")
        calendar = cls(date.fromisoformat(str(data["current_date"])))
        calendar.history = [_result_from_dict(item) for item in data.get("history", [])]
        last = data.get("last_result")
        calendar.last_result = _result_from_dict(last) if last else None
        return calendar


def assess_attention(game, current_date: date) -> tuple[AttentionSignal, ...]:
    signals: list[AttentionSignal] = []
    if not game.can_act:
        return (
            AttentionSignal(
                "career-ended",
                5,
                "主席生涯已经结束",
                "后续时间只能以观察者身份推进。",
                True,
            ),
        )

    if game.current_decision is not None:
        signals.append(
            AttentionSignal(
                "pending-signature",
                5,
                "主席亲签文件尚未处理",
                game.current_decision.title,
                True,
                "主席办公室呈签件",
            )
        )

    executive = getattr(game, "executive", None)
    if executive is not None:
        if any(item.status == "open" for item in executive.press_sessions):
            signals.append(
                AttentionSignal(
                    "open-press-conference",
                    5,
                    "发布会仍在直播",
                    "记者正在等待主席回答，不能把公开答辩跳过。",
                    True,
                    "媒体联络官",
                )
            )
        for mandate in executive.mandates:
            terminal = mandate.status in {"completed", "partial", "failed", "withdrawn"}
            if mandate.status in {"awaiting_assignment", "unassigned"}:
                signals.append(
                    AttentionSignal(
                        f"unassigned:{mandate.id}",
                        5,
                        "已签决定尚无具名负责人",
                        mandate.option_title,
                        True,
                        "秘书处督查组",
                    )
                )
            elif mandate.status in {"delayed", "narrowed"}:
                signals.append(
                    AttentionSignal(
                        f"delivery-risk:{mandate.id}",
                        4,
                        "执行正在延误或缩水",
                        mandate.public_update,
                        False,
                        "秘书处督查组",
                    )
                )
            if mandate.due_month is not None and not terminal:
                due_delta = mandate.due_month - game.global_month
                if due_delta <= 0:
                    signals.append(
                        AttentionSignal(
                            f"overdue:{mandate.id}",
                            4,
                            "主席督办事项已到复核期限",
                            mandate.option_title,
                            False,
                            "秘书处督查组",
                        )
                    )
                elif due_delta == 1 and _days_to_next_month(current_date) <= 10:
                    signals.append(
                        AttentionSignal(
                            f"review-window:{mandate.id}",
                            3,
                            "实施复核窗口临近",
                            mandate.option_title,
                            False,
                            "秘书处督查组",
                        )
                    )

    world = game.world
    campaign = game.current_campaign
    state = campaign.engine.state
    politics = campaign.politics

    distressed = [
        club
        for club in state.clubs.values()
        if club.license_status in {"administration", "excluded"}
        or club.wage_arrears_months >= 2
    ]
    if distressed:
        signals.append(
            AttentionSignal(
                "club-distress",
                4,
                "职业联赛出现正式准入或欠薪危机",
                "、".join(club.name for club in distressed[:3]),
                False,
                "财务与准入总监",
            )
        )

    coalition = float(politics.coalition_support)
    if coalition < 0.38:
        signals.append(
            AttentionSignal(
                "coalition-danger",
                4,
                "执政联盟进入危险区",
                "重要投票、泄密或辞职都可能改变主席地位。",
                False,
                "秘书长",
            )
        )
    elif coalition < 0.48:
        signals.append(
            AttentionSignal(
                "coalition-fragile",
                3,
                "执政联盟明显不稳",
                "需要缩短政治复核间隔。",
                False,
                "秘书长",
            )
        )

    urgent_cases = [
        case
        for case in getattr(world, "active_cases", ())
        if case.next_global_month <= game.global_month + 1
        or case.stage in {"charging", "trial", "appeal"}
    ]
    if urgent_cases:
        case = urgent_cases[0]
        signals.append(
            AttentionSignal(
                f"justice:{case.id}",
                4 if case.stage in {"trial", "appeal"} else 3,
                "正式案件进入关键程序节点",
                f"{case.subject_name} · {case.stage}",
                False,
                "廉洁与纪律专员",
            )
        )

    international = campaign.football.international
    # Before the first match, an all-zero table is ordered alphabetically.  It is not a
    # real sporting signal and must never slow the calendar.
    if international.results:
        position = int(international.user_position)
        if position >= 4:
            signals.append(
                AttentionSignal(
                    "national-team-danger",
                    3,
                    "国家队已跌出附加赛区域",
                    f"当前预选赛排名第{position}位。",
                    False,
                    "国家队技术总监",
                )
            )
        elif position == 3:
            signals.append(
                AttentionSignal(
                    "national-team-playoff",
                    2,
                    "国家队处于附加赛位置",
                    "技术部门建议保持比赛窗口前的高频复核。",
                    False,
                    "国家队技术总监",
                )
            )

    if _days_to_next_month(current_date) <= 10:
        signals.extend(_next_month_schedule_signals(game))

    if not signals:
        signals.append(
            AttentionSignal(
                "routine-administration",
                0,
                "没有需要主席逐日坐镇的事项",
                "部门可以按既定授权继续工作。",
                False,
                "秘书长晨间判断",
            )
        )
    return tuple(sorted(signals, key=lambda item: (-item.level, item.code)))


def next_public_checkpoint(game, current_date: date) -> tuple[date, str] | None:
    candidates: list[tuple[date, str]] = []
    executive = getattr(game, "executive", None)
    if executive is not None:
        for mandate in executive.mandates:
            if mandate.due_month is None or mandate.status in {
                "completed",
                "partial",
                "failed",
                "withdrawn",
            }:
                continue
            checkpoint = month_start(mandate.due_month) - timedelta(days=7)
            if checkpoint > current_date:
                candidates.append((checkpoint, f"“{mandate.option_title}”实施复核"))

    for case in getattr(game.world, "active_cases", ()):
        checkpoint = month_start(case.next_global_month) - timedelta(days=7)
        if checkpoint > current_date:
            candidates.append((checkpoint, f"{case.subject_name}案件程序更新"))

    schedule = _next_month_schedule_signals(game)
    if schedule:
        checkpoint = month_start(game.global_month + 1) - timedelta(days=7)
        if checkpoint > current_date:
            candidates.append((checkpoint, schedule[0].headline))

    return min(candidates, key=lambda item: item[0]) if candidates else None


def month_start(global_month: int) -> date:
    if global_month < 0:
        raise ValueError("global month cannot be negative")
    return date(2026 + global_month // 12, global_month % 12 + 1, 1)


def _next_month_start(value: date) -> date:
    return date(value.year + 1, 1, 1) if value.month == 12 else date(value.year, value.month + 1, 1)


def _days_to_next_month(value: date) -> int:
    return (_next_month_start(value) - value).days


def _next_month_schedule_signals(game) -> tuple[AttentionSignal, ...]:
    next_month = game.local_month + 1
    football = game.current_campaign.football
    signals: list[AttentionSignal] = []

    international = football.international
    if next_month in international.round_months:
        round_number = international.round_months.index(next_month) + 1
        signals.append(
            AttentionSignal(
                f"international-window:{next_month}",
                3,
                "国家队比赛窗口进入最后准备期",
                f"预选赛第{round_number}轮将在下次月结进行。",
                False,
                "国家队技术总监",
            )
        )

    cup = football.domestic_cup
    for season, stages in cup.MONTHS.items():
        stage = next((name for name, month in stages.items() if month == next_month), None)
        if stage is None:
            continue
        label = {
            "round_of_16": "足协杯首轮",
            "quarterfinal": "足协杯八强战",
            "semifinal": "足协杯半决赛",
            "final": "足协杯决赛",
        }[stage]
        signals.append(
            AttentionSignal(
                f"domestic-cup:{season}:{stage}",
                3 if stage in {"semifinal", "final"} else 2,
                f"{label}临近",
                "赛程、安保、转播和俱乐部负荷需要提前确认。",
                False,
                "赛事运行中心",
            )
        )

    continental = football.continental
    if next_month in continental.GROUP_MONTHS[continental.season]:
        signals.append(
            AttentionSignal(
                f"continental-group:{next_month}",
                2,
                "洲际冠军杯比赛周临近",
                "本国俱乐部将进入洲际比赛与长途旅行窗口。",
                False,
                "赛事运行中心",
            )
        )
    if next_month == continental.SEMIFINAL_MONTH[continental.season]:
        signals.append(
            AttentionSignal(
                f"continental-semi:{next_month}",
                3,
                "洲际冠军杯半决赛临近",
                "竞技声誉、奖金和联赛赛程压力将在同一窗口集中。",
                False,
                "赛事运行中心",
            )
        )
    if next_month == continental.FINAL_MONTH[continental.season]:
        signals.append(
            AttentionSignal(
                f"continental-final:{next_month}",
                3,
                "洲际冠军杯决赛临近",
                "主席办公室需要准备赛前协调与赛后公开回应。",
                False,
                "赛事运行中心",
            )
        )

    if next_month in {1, 7, 13, 19}:
        signals.append(
            AttentionSignal(
                f"registration-window:{next_month}",
                2,
                "注册与转会窗口即将结算",
                "俱乐部阵容、自由球员与准入争议可能集中出现。",
                False,
                "财务与准入总监",
            )
        )
    if next_month in {12, 24}:
        signals.append(
            AttentionSignal(
                f"season-settlement:{next_month}",
                3,
                "赛季与年度结算临近",
                "冠军、升降级、退役、青训毕业和年度政治审查将在同一节点发生。",
                False,
                "秘书长",
            )
        )
    if next_month in {2, 6, 8, 10, 12, 14, 16, 20, 22, 24}:
        signals.append(
            AttentionSignal(
                f"governance-window:{next_month}",
                2,
                "重大治理议程准备期",
                "秘书处正在汇总跨部门材料和利益集团立场。",
                False,
                "秘书长",
            )
        )
    return tuple(signals)


def _public_snapshot(game) -> dict[str, Any]:
    campaign = game.current_campaign
    state = campaign.engine.state
    executive = getattr(game, "executive", None)
    mandates = executive.mandates if executive is not None else []
    return {
        "treasury": round(float(state.treasury), 2),
        "fan_trust": round(float(state.fan_trust), 6),
        "national_position": int(campaign.football.international.user_position),
        "coalition": round(float(campaign.politics.coalition_support), 6),
        "distressed": sum(
            club.license_status in {"administration", "excluded"}
            or club.wage_arrears_months >= 2
            for club in state.clubs.values()
        ),
        "active_cases": len(getattr(game.world, "active_cases", ())),
        "case_stages": tuple(
            sorted((case.id, case.stage) for case in getattr(game.world, "active_cases", ()))
        ),
        "mandate_states": tuple(sorted((item.id, item.status) for item in mandates)),
        "results_total": _result_count(campaign.football),
    }


def _result_count(football) -> int:
    total = len(getattr(getattr(football, "international", None), "results", ()))
    pyramid = getattr(football, "pyramid", None)
    if pyramid is not None:
        total += len(getattr(pyramid, "all_results", ()))
    cup = getattr(football, "domestic_cup", None)
    if cup is not None:
        total += len(getattr(cup, "results", ()))
    continental = getattr(football, "continental", None)
    if continental is not None:
        total += len(getattr(continental, "group_results", ()))
        total += len(getattr(continental, "knockout_results", ()))
    return total


def _summarize_changes(before: dict[str, Any], after: dict[str, Any], global_month: int) -> list[str]:
    changes = [f"完成国家足球治理第{global_month}月结算。"]
    if after["results_total"] > before["results_total"]:
        changes.append(f"本次结算完成{after['results_total'] - before['results_total']}场正式比赛。")
    if after["national_position"] != before["national_position"]:
        changes.append(f"国家队排名由第{before['national_position']}位变为第{after['national_position']}位。")
    if after["distressed"] != before["distressed"]:
        direction = "增至" if after["distressed"] > before["distressed"] else "降至"
        changes.append(f"正式财务或准入风险俱乐部{direction}{after['distressed']}家。")
    if after["active_cases"] != before["active_cases"]:
        changes.append(f"正式程序中的案件现为{after['active_cases']}宗。")
    if after["case_stages"] != before["case_stages"]:
        changes.append("廉洁案件的公开程序阶段发生变化。")
    if after["mandate_states"] != before["mandate_states"]:
        changes.append("至少一项主席督办决定进入新的实施状态。")
    if abs(after["fan_trust"] - before["fan_trust"]) >= 0.01:
        changes.append("球迷信任在本月明显上升。" if after["fan_trust"] > before["fan_trust"] else "球迷信任在本月明显下降。")
    if abs(after["coalition"] - before["coalition"]) >= 0.02:
        changes.append("执政联盟稳定度改善。" if after["coalition"] > before["coalition"] else "执政联盟稳定度恶化。")
    if abs(after["treasury"] - before["treasury"]) >= 1_000_000:
        changes.append("足协可支配国库较月初增加超过¥1M。" if after["treasury"] > before["treasury"] else "足协可支配国库较月初减少超过¥1M。")
    return changes


def _settlement_requires_review(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return any(
        (
            after["results_total"] != before["results_total"],
            after["national_position"] != before["national_position"],
            after["distressed"] != before["distressed"],
            after["active_cases"] != before["active_cases"],
            after["case_stages"] != before["case_stages"],
            after["mandate_states"] != before["mandate_states"],
        )
    )


def _highest_level(signals: Iterable[AttentionSignal]) -> int:
    return max((item.level for item in signals), default=0)


def _attention_label(level: int) -> str:
    return {
        5: "必须停下",
        4: "危机节奏",
        3: "高压节奏",
        2: "重点关注",
        1: "常规工作",
        0: "平稳行政期",
    }.get(level, "平稳行政期")


def _days_button_label(days: int) -> str:
    if days <= 1:
        return "推进到明天"
    if days < 7:
        return f"推进{days}天"
    if days == 7:
        return "推进1周"
    if days < 28:
        return f"推进约{max(1, round(days / 7))}周"
    return "推进到准备节点"


def _result_to_dict(result: TimeAdvanceResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    payload = asdict(result)
    payload["signals_after"] = [asdict(item) for item in result.signals_after]
    return payload


def _result_from_dict(data: dict[str, Any]) -> TimeAdvanceResult:
    return TimeAdvanceResult(
        mode=str(data["mode"]),
        pace=str(data["pace"]),
        start_date=str(data["start_date"]),
        end_date=str(data["end_date"]),
        days_elapsed=int(data["days_elapsed"]),
        world_months_elapsed=int(data["world_months_elapsed"]),
        stopped_reason=str(data["stopped_reason"]),
        changes=tuple(str(item) for item in data.get("changes", [])),
        signals_after=tuple(
            AttentionSignal(
                code=str(item["code"]),
                level=int(item["level"]),
                headline=str(item["headline"]),
                detail=str(item["detail"]),
                blocking=bool(item.get("blocking", False)),
                source=str(item.get("source", "公开状态")),
            )
            for item in data.get("signals_after", [])
        ),
    )
