from datetime import date, timedelta
from pathlib import Path

from football_republic.adaptive_time import CALENDAR_EPOCH, month_start
from football_republic.executive_president_career import ExecutivePresidentCareerGame


ROOT = Path(__file__).resolve().parents[1]
TIME_SOURCE = ROOT / "src" / "football_republic" / "adaptive_time.py"
TIME_WEB_SOURCE = ROOT / "src" / "football_republic" / "adaptive_time_web.py"
OFFICE_WEB_SOURCE = ROOT / "src" / "football_republic" / "executive_office_webapp.py"


def _open_first_presidential_decision(game: ExecutivePresidentCareerGame) -> None:
    for _ in range(24):
        if game.current_decision is not None:
            return
        game.advance(1, interactive=True)
    raise AssertionError("no presidential decision opened")


def test_deliberate_time_moves_one_day_without_fake_monthly_settlement() -> None:
    game = ExecutivePresidentCareerGame()

    result = game.advance_time("deliberate")

    assert game.calendar.current_date == CALENDAR_EPOCH + timedelta(days=1)
    assert game.global_month == 0
    assert result.days_elapsed == 1
    assert result.world_months_elapsed == 0


def test_quiet_opening_period_moves_to_a_public_preparation_checkpoint() -> None:
    game = ExecutivePresidentCareerGame()
    recommendation = game.time_recommendation()

    assert recommendation.days > 7
    assert "注册" in recommendation.next_checkpoint
    assert not any(item.code.startswith("national-team") for item in recommendation.signals)

    result = game.advance_time("adaptive")

    assert game.calendar.current_date == date(2026, 1, 25)
    assert game.global_month == 0
    assert "准备期" in result.stopped_reason


def test_pending_presidential_signature_freezes_visible_time() -> None:
    game = ExecutivePresidentCareerGame()
    _open_first_presidential_decision(game)
    before = game.calendar.current_date

    result = game.advance_time("fast")

    assert result.days_elapsed == 0
    assert game.calendar.current_date == before
    assert any(item.code == "pending-signature" for item in result.signals_after)


def test_open_press_conference_cannot_be_skipped_by_fast_forward() -> None:
    game = ExecutivePresidentCareerGame()
    game.start_press_conference(topic="国家队治理")

    result = game.advance_time("fast")

    assert result.days_elapsed == 0
    assert any(item.code == "open-press-conference" for item in result.signals_after)


def test_signed_but_unassigned_decision_stops_time_until_responsibility_is_named() -> None:
    game = ExecutivePresidentCareerGame()
    _open_first_presidential_decision(game)
    decision = game.current_decision
    assert decision is not None
    game.resolve_decision(decision.options[0].id)

    result = game.advance_time("adaptive")

    assert result.days_elapsed == 0
    assert any(item.code.startswith("unassigned:") for item in result.signals_after)


def test_fast_forward_rechecks_each_settlement_and_never_skips_governance() -> None:
    game = ExecutivePresidentCareerGame()
    game.calendar.current_date = date(2026, 1, 25)

    registration = game.advance_time("fast")
    assert game.global_month == 1
    assert game.calendar.current_date == date(2026, 2, 1)
    assert registration.world_months_elapsed == 1

    preparation = game.advance_time("fast")
    assert game.global_month == 1
    assert game.calendar.current_date == date(2026, 2, 22)
    assert preparation.world_months_elapsed == 0
    assert "准备期" in preparation.stopped_reason

    decision_stop = game.advance_time("fast")
    assert game.global_month == 2
    assert game.current_decision is not None
    assert decision_stop.world_months_elapsed == 1
    assert "亲签" in decision_stop.stopped_reason


def test_calendar_save_reload_preserves_partial_month_and_fingerprint() -> None:
    game = ExecutivePresidentCareerGame()
    game.advance_time("deliberate")
    saved = game.to_json()

    restored = ExecutivePresidentCareerGame.from_json(saved)

    assert restored.calendar.current_date == game.calendar.current_date
    assert restored.calendar.last_result == game.calendar.last_result
    assert restored.fingerprint() == game.fingerprint()


def test_version_eight_save_is_upgraded_without_losing_world_state() -> None:
    game = ExecutivePresidentCareerGame()
    game.advance(1, interactive=True)
    payload = game.to_dict()
    payload["format_version"] = 8
    payload.pop("calendar")
    payload["fingerprint"] = game._legacy_fingerprint()

    restored = ExecutivePresidentCareerGame.from_dict(payload)

    assert restored.global_month == game.global_month
    assert restored.calendar.current_date >= month_start(restored.global_month)
    assert restored._legacy_fingerprint() == game._legacy_fingerprint()


def test_time_logic_uses_only_public_states_and_known_schedules() -> None:
    source = TIME_SOURCE.read_text(encoding="utf-8")

    assert "current_decision" in source
    assert "wage_arrears_months" in source
    assert "coalition_support" in source
    assert "active_cases" in source
    assert "round_months" in source
    assert "DomesticCup" not in source
    assert "competence" not in source
    assert "loyalty" not in source
    assert "network_power" not in source
    assert "hidden_delivery_quality" not in source


def test_web_controls_remove_rigid_twenty_four_month_jump() -> None:
    time_web = TIME_WEB_SOURCE.read_text(encoding="utf-8")
    office_web = OFFICE_WEB_SOURCE.read_text(encoding="utf-8")

    compile(time_web, str(TIME_WEB_SOURCE), "exec")
    compile(office_web, str(OFFICE_WEB_SOURCE), "exec")
    assert "快进至关注点" in time_web
    assert "细看1天" in time_web
    assert "time_recommendation" in office_web
    assert "game.advance(24" not in office_web
    assert "结束今日" not in office_web
    assert "推进至文件" not in office_web
