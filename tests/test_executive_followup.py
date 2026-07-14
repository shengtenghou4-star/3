from dataclasses import asdict

import pytest

from football_republic.campaign import Strategy
from football_republic.executive_president_career import ExecutivePresidentCareerGame


def _reach_decision(game: ExecutivePresidentCareerGame) -> None:
    for _ in range(12):
        if game.current_decision is not None:
            return
        game.advance(1, interactive=True)
    raise AssertionError("no presidential decision appeared")


def _sign_first_option(game: ExecutivePresidentCareerGame):
    _reach_decision(game)
    decision = game.current_decision
    assert decision is not None
    option = decision.options[0]
    game.resolve_decision(option.id)
    return game.executive.mandates[-1]


def _advance_without_manual_choices(
    game: ExecutivePresidentCareerGame,
    months: int,
) -> None:
    target = game.global_month + months
    while game.global_month < target and game.can_act:
        if game.current_decision is not None:
            option = game.current_decision.options[0]
            game.resolve_decision(option.id)
        else:
            game.advance(1, interactive=True)


def test_signed_decision_opens_unassigned_implementation_mandate() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)

    mandate = _sign_first_option(game)

    assert mandate.status == "awaiting_assignment"
    assert mandate.assigned_office is None
    assert mandate.recommended_offices
    assert mandate.decision_id
    assert mandate.option_title
    assert any(
        item["action_type"] == "implementation_mandate_opened"
        for item in game.world.external_actions
    )


def test_unassigned_mandate_becomes_a_presidential_office_failure() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    capital_before = game.current_campaign.engine.state.political_capital

    game.advance(1, interactive=True)

    assert mandate.status == "unassigned"
    assert mandate.penalty_applied is True
    assert "没有一名官员" in mandate.public_update
    assert game.current_campaign.engine.state.political_capital < capital_before


def test_chairman_assigns_a_named_official_and_instruction_style() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    office = mandate.recommended_offices[0]
    official = game.world.cabinet[office]

    assigned = game.assign_implementation(
        mandate_id=mandate.id,
        office=office,
        instruction_style="tight",
    )

    assert assigned.assigned_office == office
    assert assigned.assigned_official_id == official.id
    assert assigned.assigned_official_name == official.name
    assert assigned.instruction_style == "tight"
    assert assigned.due_month == game.global_month + 3
    assert official.name in assigned.public_update


def test_professional_fit_outperforms_an_obvious_office_mismatch() -> None:
    fitted = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mismatched = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    fitted_mandate = _sign_first_option(fitted)
    mismatch_mandate = _sign_first_option(mismatched)

    fitted_office = fitted_mandate.recommended_offices[0]
    wrong_office = next(
        office
        for office in mismatched.world.cabinet
        if office not in mismatch_mandate.recommended_offices
    )
    fitted.assign_implementation(
        mandate_id=fitted_mandate.id,
        office=fitted_office,
        instruction_style="tight",
    )
    mismatched.assign_implementation(
        mandate_id=mismatch_mandate.id,
        office=wrong_office,
        instruction_style="tight",
    )

    fitted.advance(1, interactive=True)
    mismatched.advance(1, interactive=True)

    assert fitted_mandate.progress > mismatch_mandate.progress
    assert any("专业归口" in item for item in mismatch_mandate.effects)


def test_overloading_one_official_slows_a_second_mandate() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    first = _sign_first_option(game)
    office = first.recommended_offices[0]
    game.assign_implementation(
        mandate_id=first.id,
        office=office,
        instruction_style="outcome",
    )
    second = game.executive.open_mandate(
        game,
        decision_id="test-second-decision",
        option_id="test-second-option",
        option_title="第二项跨部门改革",
        subject="治理协调与预算执行",
    )
    game.assign_implementation(
        mandate_id=second.id,
        office=office,
        instruction_style="outcome",
    )

    game.advance(1, interactive=True)

    assert first.progress < 0.45
    assert second.progress < 0.45
    assert first.assigned_official_id == second.assigned_official_id


def test_same_issue_produces_competing_reports_with_visible_blind_spots() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    game.assign_implementation(
        mandate_id=mandate.id,
        office=mandate.recommended_offices[0],
        instruction_style="coalition",
    )

    reports = game.executive.visible_reports(mandate_id=mandate.id)
    payloads = [asdict(item) for item in reports]

    assert len(reports) == 3
    assert len({item.office for item in reports}) == 3
    assert len({item.recommendation for item in reports}) >= 2
    assert all(item.blind_spot for item in reports)
    assert all(item.evidence for item in reports)
    assert all("hidden" not in key for row in payloads for key in row)
    assert all("score" not in key for row in payloads for key in row)


def test_reassignment_replaces_same_month_report_with_the_new_owner_view() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    first_office = mandate.recommended_offices[0]
    second_office = next(office for office in game.world.cabinet if office != first_office)
    game.assign_implementation(
        mandate_id=mandate.id,
        office=first_office,
        instruction_style="tight",
    )
    game.assign_implementation(
        mandate_id=mandate.id,
        office=second_office,
        instruction_style="outcome",
    )

    reports = game.executive.visible_reports(mandate_id=mandate.id)
    owner_report = next(item for item in reports if item.office == second_office)

    assert "牵头部门" in owner_report.headline
    assert game.world.cabinet[second_office].name == owner_report.official_name


def test_press_conference_generates_real_followup_questions() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    _sign_first_option(game)
    session = game.start_press_conference(topic="俱乐部准入")
    opening = session.current_question

    game.answer_press_conference(
        session_id=session.id,
        answer_style="rules_first",
    )

    assert session.status == "open"
    assert len(session.exchanges) == 1
    assert session.exchanges[0].question == opening
    assert "豪门退出" in session.current_question
    assert session.exchanges[0].reporter_followup == session.current_question


def test_three_press_answers_close_the_session_and_preserve_exact_quotes() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    session = game.start_press_conference(topic="国家队备战")

    for style in ("transparent_uncertainty", "rules_first", "no_comment"):
        game.answer_press_conference(session_id=session.id, answer_style=style)

    assert session.status == "closed"
    assert len(session.exchanges) == 3
    assert all(item.quote for item in session.exchanges)
    assert len(game.office.statements) == 3


def test_same_press_conference_can_expose_an_immediate_contradiction() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    media = game.current_campaign.politics.stakeholders["broadcaster"]
    trust_before = media.trust
    session = game.start_press_conference(topic="俱乐部救助")

    game.answer_press_conference(session_id=session.id, answer_style="rules_first")
    game.answer_press_conference(session_id=session.id, answer_style="support_sector")

    assert media.trust < trust_before
    assert "口径存在张力" in session.exchanges[-1].consequence
    assert any(
        item["action_type"] == "press_conference_contradiction"
        for item in game.world.external_actions
    )


def test_repeated_no_comment_becomes_a_media_story() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    media = game.current_campaign.politics.stakeholders["broadcaster"]
    mobilization_before = media.mobilization
    session = game.start_press_conference(topic="内部泄密")

    game.answer_press_conference(session_id=session.id, answer_style="no_comment")
    game.answer_press_conference(session_id=session.id, answer_style="no_comment")

    assert media.mobilization > mobilization_before
    assert "沉默本身" in session.exchanges[-1].consequence


def test_named_implementation_reaches_a_real_outcome() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    game.assign_implementation(
        mandate_id=mandate.id,
        office=mandate.recommended_offices[0],
        instruction_style="tight",
    )

    _advance_without_manual_choices(game, 4)

    assert mandate.status in {"completed", "partial", "failed"}
    assert mandate.outcome_applied is True
    assert any(
        item["action_type"] == "implementation_outcome"
        for item in game.world.external_actions
    )


def test_executive_save_reload_preserves_assignment_reports_and_press_sequence() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    mandate = _sign_first_option(game)
    game.assign_implementation(
        mandate_id=mandate.id,
        office=mandate.recommended_offices[0],
        instruction_style="outcome",
    )
    game.advance(1, interactive=True)
    session = game.start_press_conference(topic=mandate.option_title)
    game.answer_press_conference(
        session_id=session.id,
        answer_style="transparent_uncertainty",
    )

    restored = ExecutivePresidentCareerGame.from_json(game.to_json())

    assert restored.fingerprint() == game.fingerprint()
    assert restored.executive.mandates == game.executive.mandates
    assert restored.executive.reports == game.executive.reports
    assert restored.executive.press_sessions == game.executive.press_sessions
    restored_session = restored.executive.press_sessions[-1]
    restored.answer_press_conference(
        session_id=restored_session.id,
        answer_style="rules_first",
    )
    assert len(restored_session.exchanges) == 2


def test_successor_cannot_use_the_players_implementation_or_press_authority() -> None:
    game = ExecutivePresidentCareerGame(strategy=Strategy.BALANCED, max_terms=1)
    mandate = _sign_first_option(game)
    game.can_act = False

    with pytest.raises(RuntimeError):
        game.assign_implementation(
            mandate_id=mandate.id,
            office=mandate.recommended_offices[0],
            instruction_style="tight",
        )
    with pytest.raises(RuntimeError):
        game.start_press_conference(topic="继任政府")
