from datetime import date, timedelta
from pathlib import Path

from football_republic.executive_president_career import ExecutivePresidentCareerGame


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "src" / "football_republic" / "stadium_runtime.py"
WEB = ROOT / "src" / "football_republic" / "stadium_web.py"
APP = ROOT / "src" / "football_republic" / "matchday_office_webapp.py"


def _clear_unrelated_business(game: ExecutivePresidentCareerGame) -> None:
    for _ in range(16):
        decision = game.world.current_decision
        if decision is None:
            return
        game.world.resolve_decision(decision.options[0].id)
    raise AssertionError("unrelated presidential business did not clear")


def _reach_arrival(game: ExecutivePresidentCareerGame):
    game.advance(2, interactive=False)
    _clear_unrelated_business(game)
    game.calendar.current_date = date(2026, 3, 25)
    game.time_recommendation()
    window = game.matchday.active_window
    assert window is not None
    game.resolve_match_camp("balanced")
    if window.stage == "release":
        game.resolve_club_release("compensate")
    game.set_match_mandate("private_target")
    game.calendar.current_date = date.fromisoformat(window.match_date) - timedelta(days=1)
    game.matchday.sync(game)
    assert window.stage == "stadium_arrival"
    return window


def _settle_official_match(game: ExecutivePresidentCareerGame, arrival: str = "institutional"):
    window = _reach_arrival(game)
    game.resolve_stadium_arrival(arrival)
    _clear_unrelated_business(game)
    game.advance(1, interactive=True)
    assert window.result is not None
    assert window.stage == "post_whistle"
    return window


def test_stadium_arrival_is_a_hard_stop_with_named_box_guests() -> None:
    game = ExecutivePresidentCareerGame()
    window = _reach_arrival(game)

    recommendation = game.time_recommendation()
    assert recommendation.days == 0
    assert any("主席代表团已经抵达体育场" in item.headline for item in recommendation.signals)

    game.resolve_stadium_arrival("grassroots")
    scene = game.matchday.scene_for_window(window.id)

    assert window.stage == "awaiting_match"
    assert scene is not None
    assert scene.arrival_choice == "grassroots"
    assert any(item.role == "全国球迷联络会代表" for item in scene.guest_list)
    assert any(
        item["action_type"] == "stadium_arrival_protocol"
        for item in game.world.external_actions
    )


def test_official_result_generates_a_consistent_stadium_timeline() -> None:
    game = ExecutivePresidentCareerGame()
    window = _settle_official_match(game)
    scene = game.matchday.scene_for_window(window.id)
    result = window.result or {}
    international = game.current_campaign.football.international
    user_home = result.get("home_id") == international.user_code
    goals_for = result.get("home_goals", 0) if user_home else result.get("away_goals", 0)
    goals_against = result.get("away_goals", 0) if user_home else result.get("home_goals", 0)

    assert scene is not None
    assert scene.final_score == f"{goals_for}-{goals_against}"
    assert sum(item.kind == "goal" for item in scene.moments) == goals_for + goals_against
    assert scene.moments[-1].kind == "fulltime"
    assert scene.moments[-1].score_for == goals_for
    assert scene.moments[-1].score_against == goals_against
    assert not hasattr(game, "choose_formation")
    assert not hasattr(game, "order_substitution")


def test_post_whistle_and_mixed_zone_must_finish_before_coach_review() -> None:
    game = ExecutivePresidentCareerGame()
    window = _settle_official_match(game, "showcase")

    blocked = game.advance_time("fast")
    assert blocked.days_elapsed == 0
    assert any("终场镜头" in item.headline for item in blocked.signals_after)

    game.resolve_box_reaction("stay_visible")
    assert window.stage == "mixed_zone"
    assert game.time_recommendation().days == 0

    game.resolve_mixed_zone("own_result")
    assert window.stage == "review"
    game.resolve_match_review("technical_review")
    assert window.stage == "closed"


def test_stadium_scene_survives_save_reload_mid_sequence() -> None:
    game = ExecutivePresidentCareerGame()
    window = _settle_official_match(game, "grassroots")
    game.resolve_box_reaction("go_tunnel")
    scene = game.matchday.scene_for_window(window.id)
    assert scene is not None

    restored = ExecutivePresidentCareerGame.from_json(game.to_json())
    restored_scene = restored.matchday.scene_for_window(window.id)

    assert restored.matchday.active_window is not None
    assert restored.matchday.active_window.stage == "mixed_zone"
    assert restored_scene == scene
    assert restored.fingerprint() == game.fingerprint()


def test_version_ten_save_upgrades_without_inventing_old_stadium_scenes() -> None:
    game = ExecutivePresidentCareerGame()
    game.advance_time("deliberate")
    payload = game.to_dict()
    payload["format_version"] = 10
    payload["matchday"] = game.matchday._legacy_payload()
    payload["fingerprint"] = game._v10_fingerprint()

    restored = ExecutivePresidentCareerGame.from_dict(payload)

    assert restored.matchday.stadium_scenes == {}
    assert restored._v10_fingerprint() == game._v10_fingerprint()


def test_stadium_sources_compile_and_preserve_the_chairman_role() -> None:
    for path in (RUNTIME, WEB, APP):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")

    web_source = WEB.read_text(encoding="utf-8")
    app_source = APP.read_text(encoding="utf-8")
    assert "render_stadium_matchday_center(game)" in app_source
    assert "主教练独立决定名单、阵型、首发、换人和临场指令" in web_source
    assert "不能在包厢里点选首发或要求换人" in web_source
    assert "st.metric(" not in web_source
