from dataclasses import asdict

from football_republic.campaign import Strategy
from football_republic.president_career import PresidentCareerGame
from football_republic.presidential_office import build_office_packet


def test_office_packet_is_deterministic_for_same_world_state() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)

    first = build_office_packet(game)
    second = build_office_packet(game)

    assert first == second
    assert first.packet_id == second.packet_id
    assert first.agenda
    assert first.correspondence
    assert first.press_clippings
    assert first.meeting_requests


def test_office_packet_reads_like_a_workday_not_a_dashboard() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    packet = build_office_packet(game)

    assert packet.office_location == "国家足球协会总部 · 主席办公区"
    assert packet.date_label.endswith("日")
    assert any(item.time == "08:20" for item in packet.agenda)
    assert any("秘书长" in item.title for item in packet.agenda)
    assert any(item.time == "18:00" for item in packet.agenda)
    assert all(item.purpose for item in packet.agenda)


def test_pending_presidential_decision_becomes_a_real_dossier() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    game.advance(4, interactive=True)
    assert game.current_decision is not None

    packet = build_office_packet(game)
    dossier = packet.dossier

    assert dossier is not None
    assert dossier.title == game.current_decision.title
    assert dossier.registry_number.startswith("足协主呈")
    assert "主席亲签" in dossier.classification
    assert len(dossier.staff_positions) == 5
    assert len(dossier.option_briefs) == len(game.current_decision.options)
    assert {item.option_id for item in dossier.option_briefs} == {
        item.id for item in game.current_decision.options
    }


def test_dossier_contains_disagreement_and_implementation_accountability() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    game.advance(4, interactive=True)
    dossier = build_office_packet(game).dossier
    assert dossier is not None

    recommendations = {item.recommendation for item in dossier.staff_positions}
    assert len(recommendations) >= 2
    assert all(item.reasoning for item in dossier.staff_positions)
    assert all(item.concern for item in dossier.staff_positions)
    assert all(item.implementation_owner for item in dossier.option_briefs)
    assert all(
        "三十" in item.first_thirty_days or "30" in item.first_thirty_days
        for item in dossier.option_briefs
    )
    assert all(item.failure_mode for item in dossier.option_briefs)


def test_financial_distress_creates_people_pressure_not_only_a_number() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    club = next(iter(game.current_campaign.engine.state.clubs.values()))
    club.wage_arrears_months = 3
    club.license_status = "administration"

    packet = build_office_packet(game)

    assert "俱乐部触发财务或准入预警" in packet.situation_line
    assert any(club.name in item.subject for item in packet.correspondence)
    assert any(club.name in item.subject for item in packet.meeting_requests)
    assert any(club.name in item.headline for item in packet.press_clippings)
    meeting = next(item for item in packet.meeting_requests if club.name in item.subject)
    assert meeting.concrete_ask
    assert meeting.what_they_offer
    assert meeting.what_they_avoid
    assert len(meeting.chairman_questions) == 3


def test_public_case_creates_procedural_meeting_without_hidden_evidence() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    subject = game.world.people["central-fa-chair"]
    subject.integrity = 0.05
    subject.network_power = 0.98
    for tie in game.world._ties_for(subject.id):
        tie.strength = max(tie.strength, 0.90)
    while game.global_month < 6 and game.can_act:
        if game.current_decision is not None:
            game.world._auto_resolve_current()
            game._refresh_career_state()
        else:
            game.advance(1, interactive=True)
    while (
        game.current_decision is not None
        and not game.current_decision.id.startswith("justice_referral_")
    ):
        game.world._auto_resolve_current()
        game._refresh_career_state()
    if (
        game.current_decision is not None
        and game.current_decision.id.startswith("justice_referral_")
    ):
        game.resolve_decision("independent_referral")

    packet = build_office_packet(game)
    serialized = str(asdict(packet)).lower()

    assert any("程序" in item.subject for item in packet.meeting_requests)
    assert "evidence" not in serialized
    assert "independence" not in serialized
    assert "network_power" not in serialized
    assert "integrity" not in serialized


def test_office_packet_does_not_expose_exact_stakeholder_scores() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    game.advance(4, interactive=True)
    dossier = build_office_packet(game).dossier
    assert dossier is not None

    payload = asdict(dossier)
    stakeholder_rows = payload["stakeholder_positions"]

    assert stakeholder_rows
    assert all("support" not in row for row in stakeholder_rows)
    assert all("trust" not in row for row in stakeholder_rows)
    assert all("power" not in row for row in stakeholder_rows)
    assert all(row["known_position"] for row in stakeholder_rows)
    assert all(row["confidence"] for row in stakeholder_rows)


def test_packet_changes_when_the_real_world_advances() -> None:
    game = PresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    first = build_office_packet(game)

    game.advance(1, interactive=True)
    second = build_office_packet(game)

    assert second.packet_id != first.packet_id
    assert second.date_label != first.date_label


def test_every_press_clipping_contains_a_question_the_president_may_face() -> None:
    game = PresidentCareerGame(strategy=Strategy.QUICK_RESULTS, max_terms=3)
    packet = build_office_packet(game)

    assert packet.press_clippings
    assert all(item.outlet for item in packet.press_clippings)
    assert all(item.angle for item in packet.press_clippings)
    assert all(
        item.question_for_president.endswith("？")
        for item in packet.press_clippings
    )
