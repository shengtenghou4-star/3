from datetime import date
from pathlib import Path

from football_republic.executive_president_career import ExecutivePresidentCareerGame


ROOT = Path(__file__).resolve().parents[1]
COMMAND_SOURCE = ROOT / "src" / "football_republic" / "national_team_command.py"
COMMAND_WEB_SOURCE = ROOT / "src" / "football_republic" / "national_team_web.py"
MATCHDAY_APP_SOURCE = ROOT / "src" / "football_republic" / "executive_matchday_webapp.py"
LAUNCH_SOURCE = ROOT / "src" / "football_republic" / "launch_history.py"


def _reach_first_match_preparation(game: ExecutivePresidentCareerGame) -> None:
    game.advance(2, interactive=False)
    assert game.local_month == 2
    fixture = game.national_team_command.next_fixture(game)
    assert fixture is not None
    assert fixture["round_number"] == 1


def test_match_window_requires_a_presidential_posture_and_creates_review() -> None:
    game = ExecutivePresidentCareerGame()
    _reach_first_match_preparation(game)
    game.calendar.current_date = date(2026, 3, 25)

    blocked = game.advance_time("fast")

    assert blocked.days_elapsed == 0
    assert any(
        item.code.startswith("match-directive:")
        for item in blocked.signals_after
    )

    directive = game.choose_match_directive(option_id="protect_players")
    assert directive.option_title == "优先协调放人与球员保护"

    game.advance(1, interactive=False)

    assert directive.applied is True
    review = game.national_team_command.pending_review
    assert review is not None
    assert review.round_number == 1
    assert review.directive_title == directive.option_title
    assert any(
        item["action_type"] == "national_team_match_directive_applied"
        for item in game.world.external_actions
    )


def test_post_match_review_blocks_clock_and_survives_verified_save_replay() -> None:
    game = ExecutivePresidentCareerGame()
    _reach_first_match_preparation(game)
    game.choose_match_directive(option_id="delegated")
    game.advance(1, interactive=False)
    review = game.national_team_command.pending_review
    assert review is not None

    blocked = game.advance_time("adaptive")
    assert blocked.days_elapsed == 0
    assert any(
        item.code.startswith("match-review:")
        for item in blocked.signals_after
    )

    opening_coach = game.national_team_command.coach_name
    opening_treasury = game.current_campaign.engine.state.treasury
    resolved = game.resolve_match_review(
        review_id=review.id,
        option_id="dismiss",
    )

    assert resolved.status == "resolved"
    assert game.national_team_command.coach_name != opening_coach
    assert game.current_campaign.engine.state.treasury < opening_treasury
    assert any(
        item["action_type"] == "national_team_match_review_resolved"
        for item in game.world.external_actions
    )

    restored = ExecutivePresidentCareerGame.from_json(game.to_json())

    assert restored.national_team_command.coach_name == game.national_team_command.coach_name
    assert restored.national_team_command.reviews == game.national_team_command.reviews
    assert restored.current_campaign.engine.state.treasury == game.current_campaign.engine.state.treasury
    assert restored.fingerprint() == game.fingerprint()


def test_matchday_interface_preserves_the_chairman_role_boundary() -> None:
    command_source = COMMAND_SOURCE.read_text(encoding="utf-8")
    web_source = COMMAND_WEB_SOURCE.read_text(encoding="utf-8")
    app_source = MATCHDAY_APP_SOURCE.read_text(encoding="utf-8")
    launch_source = LAUNCH_SOURCE.read_text(encoding="utf-8")

    compile(command_source, str(COMMAND_SOURCE), "exec")
    compile(web_source, str(COMMAND_WEB_SOURCE), "exec")
    compile(app_source, str(MATCHDAY_APP_SOURCE), "exec")

    assert "主席不能亲自点选首发" in web_source
    assert "排阵型、首发和临场换人仍由教练组承担" in web_source
    assert "selection_score" not in web_source
    assert "国家队指挥中心" in app_source
    assert "executive_matchday_webapp.py" in launch_source
