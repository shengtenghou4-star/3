"""Install national-team match-window signals into adaptive presidential time."""

from __future__ import annotations

from datetime import date, timedelta

from .adaptive_time import AttentionSignal, month_start


_STAGE_SIGNAL = {
    "briefing": (
        5,
        "国家队集训方案等待主席批准",
        "后勤、医疗与训练资源尚未获得协会授权。",
        True,
        "国家队技术总监",
    ),
    "release": (
        5,
        "俱乐部征调争议等待主席处理",
        "至少一家俱乐部要求医疗复核、保险安排或减少征调人数。",
        True,
        "国家队管理部",
    ),
    "pre_match": (
        5,
        "赛前主席—主教练会议尚未完成",
        "主教练需要明确自己获得的公开支持、内部目标与技术权力边界。",
        True,
        "主席办公室",
    ),
    "awaiting_match": (
        3,
        "国家队已经进入比赛日倒计时",
        "名单和准备方案已经确定，时间应按数日而不是整月推进。",
        False,
        "国家队竞赛中心",
    ),
    "stadium_arrival": (
        5,
        "主席代表团已经抵达体育场",
        "包厢座次、来宾构成、安保和公开露面方式必须在开赛前确定。",
        True,
        "主席礼宾与安保组",
    ),
    "post_whistle": (
        5,
        "终场镜头正在等待主席反应",
        "正式赛果已经产生，主席必须决定留在包厢、进入通道或提前离场。",
        True,
        "主席随行新闻组",
    ),
    "mixed_zone": (
        5,
        "混合采访区等待主席口径",
        "媒体已经掌握比分和现场画面，主席必须先完成公开回应再进入人事问责。",
        True,
        "足协新闻发言人",
    ),
    "review": (
        5,
        "国家队赛后问责尚未完成",
        "现场流程已经结束，主席必须决定公开承担、技术复盘或更换主教练。",
        True,
        "主席办公室",
    ),
}

_REQUIRED_STAGES = {
    "briefing",
    "release",
    "pre_match",
    "stadium_arrival",
    "post_whistle",
    "mixed_zone",
    "review",
}


def install_into(adaptive_time_module) -> None:
    if getattr(adaptive_time_module, "_matchday_time_installed", False):
        return
    original_assess = adaptive_time_module.assess_attention
    original_checkpoint = adaptive_time_module.next_public_checkpoint

    def assess_attention(game, current_date: date):
        signals = list(original_assess(game, current_date))
        runtime = getattr(game, "matchday", None)
        if runtime is None:
            return tuple(signals)
        window = runtime.sync(game)
        if window is None or window.stage not in _STAGE_SIGNAL:
            return tuple(signals)
        level, headline, detail, blocking, source = _STAGE_SIGNAL[window.stage]
        signals = [item for item in signals if item.code != "routine-administration"]
        signals.append(
            AttentionSignal(
                code=f"matchday:{window.id}:{window.stage}",
                level=level,
                headline=headline,
                detail=f"{window.venue}对阵{window.opponent_name}。{detail}",
                blocking=blocking,
                source=source,
            )
        )
        return tuple(sorted(signals, key=lambda item: (-item.level, item.code)))

    def next_public_checkpoint(game, current_date: date):
        candidates: list[tuple[date, str]] = []
        base = original_checkpoint(game, current_date)
        if base is not None:
            candidates.append(base)
        runtime = getattr(game, "matchday", None)
        if runtime is None:
            return min(candidates, key=lambda item: item[0]) if candidates else None
        window = runtime.sync(game)
        if window is not None:
            match_date = date.fromisoformat(window.match_date)
            if window.stage == "awaiting_match" and match_date > current_date:
                arrival_date = match_date - timedelta(days=1)
                checkpoint = arrival_date if arrival_date > current_date else match_date
                candidates.append(
                    (checkpoint, f"国家队{window.venue}对阵{window.opponent_name}的比赛现场")
                )
            elif window.stage in _REQUIRED_STAGES:
                candidates.append((current_date, f"国家队比赛窗口：{window.stage}"))
        else:
            candidate = runtime._next_fixture(game)
            if candidate is not None:
                preparation = month_start(candidate[2]) - timedelta(days=7)
                if preparation > current_date:
                    candidates.append(
                        (preparation, f"国家队对阵{candidate[4]}的准备周")
                    )
        return min(candidates, key=lambda item: item[0]) if candidates else None

    adaptive_time_module.assess_attention = assess_attention
    adaptive_time_module.next_public_checkpoint = next_public_checkpoint
    adaptive_time_module._matchday_time_installed = True
