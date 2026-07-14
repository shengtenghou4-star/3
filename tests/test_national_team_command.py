from collections import Counter
from datetime import date
from pathlib import Path

from football_republic.executive_president_career import ExecutivePresidentCareerGame
from football_republic.national_team_command import ClubReleaseDispute


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "src" / "football_republic" / "national_team_command.py"
REPLAY = ROOT / "src" / "football_republic" / "matchday_replay.py"
TIME_INTEGRATION = ROOT / "src" / "football_republic" / "matchday_time_integration.py"
WEB = ROOT / "src" / "football_republic" / "matchday_web.py"
APP = ROOT / "src" / "football_republic" / "matchday_office_webapp.py"
LAUNCH = ROOT / "src" / "football_republic" / "launch_history.py"


def _clear_unrelated_presidential_business(game: ExecutivePresidentCareerGame) -> None:
    """Resolve other month-two business directly so tests isolate national-team power."""
    for _ in range(12):
        decision = game.world.current_decision
        if decision is None:
            return
        game.world.resolve_decision(decision.options[0].id)
    raise AssertionError("unrelated governance business did not clear")


def _open_first_window(game: ExecutivePresidentCareerGame):
    game.advance(2, interactive=False)
    _clear_unrelated_presidential_business(game)
    game.calendar.current_date = date(2026, 3, 25)
    recommendation = game.time_recommendation()
    window = game.matchday.active_window
    assert game.current_decision is None
    assert window is not None
    assert recommendation.days == 0
    return window


def _complete_preparation(game: ExecutivePresidentCareerGame):
    window = _open_first_window(game)
    game.resolve_match_camp("balanced")
    if window.stage == "release":
        game.resolve_club_release("compensate")
    game.set_match_mandate("private_target")
    assert window.stage == "awaiting_match"
    return window


def test_coach_selects_a_balanced_squad_without_presidential_lineup_control() -> None:
    game = ExecutivePresidentCareerGame()
    window = _open_first_window(game)
    counts = Counter(item.position for item in window.squad)

    assert len(window.squad) == 25
    assert counts == {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}
    assert window.notes
    assert "主席办公室未参与具体人选" in window.notes[0]
    assert not hasattr(game, "choose_formation")
    assert not hasattr(game, "select_starting_eleven")
    assert not hasattr(game.matchday, "choose_tactics")


def test_match_window_freezes_time_until_each_presidential_stage_is_resolved() -> None:
    game = ExecutivePresidentCareerGame()
    window = _open_first_window(game)

    assert window.stage == "briefing"
    assert game.time_recommendation().attention_label == "必须停下"
    blocked = game.advance_time("fast")
    assert blocked.days_elapsed == 0

    game.resolve_match_camp("recovery")
    if window.stage == "release":
        assert game.time_recommendation().days == 0
        game.resolve_club_release("compensate")
    assert window.stage == "pre_match"
    assert game.time_recommendation().days == 0

    game.set_match_mandate("back_coach")
    assert window.stage == "awaiting_match"
    assert game.time_recommendation().days > 0


def test_release_arbitration_changes_real_club_relationships() -> None:
    game = ExecutivePresidentCareerGame()
    window = _open_first_window(game)
    game.resolve_match_camp("balanced")
    if not window.disputes:
        member = window.squad[0]
        window.disputes.append(
            ClubReleaseDispute(
                id="test-release",
                club_id=member.club_id,
                club_name=member.club_name,
                player_ids=(member.player_id,),
                player_names=(member.player_name,),
                severity="中",
                public_reason="俱乐部申请联合医疗复核。",
            )
        )
        window.stage = "release"
    dispute = window.disputes[0]
    owner = game.current_campaign.football.pyramid.owners[dispute.club_id]
    before = owner.relationship_with_fa

    game.resolve_club_release("enforce")

    assert owner.relationship_with_fa < before
    assert all(item.status == "resolved" for item in window.disputes)
    assert window.stage == "pre_match"


def test_performance_camp_has_more_readiness_and_risk_than_recovery() -> None:
    recovery = ExecutivePresidentCareerGame()
    performance = ExecutivePresidentCareerGame()
    recovery_window = _open_first_window(recovery)
    performance_window = _open_first_window(performance)

    recovery.resolve_match_camp("recovery")
    performance.resolve_match_camp("performance")

    assert performance_window.readiness_modifier > recovery_window.readiness_modifier
    assert performance_window.injury_risk > recovery_window.injury_risk
    assert performance_window.treasury_cost > recovery_window.treasury_cost


def test_match_readiness_is_temporary_and_result_enters_review() -> None:
    game = ExecutivePresidentCareerGame()
    window = _complete_preparation(game)
    base_strength = game.current_campaign.engine.state.national_team_strength

    game.advance(1, interactive=True)

    final_strength = game.current_campaign.engine.state.national_team_strength
    assert window.result is not None
    assert window.stage == "review"
    assert window.temporary_modifier_applied == 0.0
    assert abs(final_strength - base_strength) <= 1.7
    assert game.time_recommendation().days == 0
    assert any("赛后问责" in item.headline for item in game.time_recommendation().signals)


def test_post_match_review_can_replace_the_coach_but_not_rewrite_the_result() -> None:
    game = ExecutivePresidentCareerGame()
    window = _complete_preparation(game)
    game.advance(1, interactive=True)
    old_coach = game.matchday.coach.name
    result_before = dict(window.result or {})

    game.resolve_match_review("dismiss_coach")

    assert window.stage == "closed"
    assert game.matchday.coach.name != old_coach
    assert game.matchday.coach_history[-1].status == "dismissed"
    assert window.result == result_before


def test_matchday_save_reload_preserves_window_coach_and_fingerprint() -> None:
    game = ExecutivePresidentCareerGame()
    window = _open_first_window(game)
    game.resolve_match_camp("balanced")
    saved = game.to_json()

    restored = ExecutivePresidentCareerGame.from_json(saved)

    assert restored.matchday.coach == game.matchday.coach
    assert restored.matchday.active_window == window
    assert restored.fingerprint() == game.fingerprint()


def test_version_nine_save_upgrades_with_a_fresh_matchday_runtime() -> None:
    game = ExecutivePresidentCareerGame()
    game.advance_time("deliberate")
    payload = game.to_dict()
    payload["format_version"] = 9
    payload.pop("matchday")
    payload["fingerprint"] = game._v9_fingerprint()

    restored = ExecutivePresidentCareerGame.from_dict(payload)

    assert restored.global_month == game.global_month
    assert restored.calendar.current_date == game.calendar.current_date
    assert restored.matchday.windows == []
    assert restored._v9_fingerprint() == game._v9_fingerprint()


def test_matchday_sources_compile_and_default_launcher_uses_command_center() -> None:
    for path in (RUNTIME, REPLAY, TIME_INTEGRATION, WEB, APP):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    app_source = APP.read_text(encoding="utf-8")
    web_source = WEB.read_text(encoding="utf-8")
    launch_source = LAUNCH.read_text(encoding="utf-8")
    assert '"国家队指挥中心"' in app_source
    assert "render_matchday_center(game)" in app_source
    assert "主教练独立决定征召名单、阵型、首发和换人" in web_source
    assert "matchday_office_webapp.py" in launch_source
    assert "st.metric(" not in web_source
