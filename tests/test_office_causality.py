from dataclasses import asdict

from football_republic.campaign import Strategy
from football_republic.causal_president_career import CausalPresidentCareerGame


def resolve_until(
    game: CausalPresidentCareerGame,
    decision_id: str,
    *,
    limit: int = 30,
) -> None:
    guard = 0
    while game.can_act and game.global_month <= limit:
        decision = game.current_decision
        if decision is not None:
            if decision.id == decision_id:
                return
            game.resolve_decision(decision.options[0].id)
        else:
            game.advance(1, interactive=True)
        guard += 1
        if guard > 400:
            break
    raise AssertionError(f"decision {decision_id!r} was not reached")


def advance_with_first_options(
    game: CausalPresidentCareerGame,
    target_month: int,
) -> None:
    guard = 0
    while game.can_act and game.global_month < target_month:
        if game.current_decision is not None:
            game.resolve_decision(game.current_decision.options[0].id)
        else:
            game.advance(1, interactive=True)
        guard += 1
        if guard > 500:
            raise AssertionError("game did not reach target month")


def test_direct_meeting_changes_real_stakeholder_memory_and_support() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    actor = game.current_campaign.politics.stakeholders["club_owners"]
    support_before = actor.support
    trust_before = actor.trust

    record = game.record_meeting(
        meeting_id="owners-meeting-1",
        visitor="陆景松",
        institution="职业联盟",
        subject="俱乐部准入协调",
        choice="president",
        sensitivity="urgent",
    )

    assert actor.support > support_before
    assert actor.trust > trust_before
    assert actor.last_contact_month == game.local_month
    assert record.due_month == game.global_month + 2
    assert any("主席亲自会见" in item for item in actor.memory)
    assert game.world.external_actions[-1]["action_type"] == "meeting"


def test_repeated_access_for_one_bloc_creates_fairness_cost() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    supporters = game.current_campaign.politics.stakeholders["supporters_federation"]
    trust_before = supporters.trust

    for index in range(3):
        game.record_meeting(
            meeting_id=f"owners-access-{index}",
            visitor="陆景松",
            institution="职业联盟",
            subject=f"商业协调第{index + 1}次",
            choice="president",
        )

    assert supporters.trust < trust_before
    assert any("接触渠道过度集中" in item for item in supporters.memory)


def test_public_office_reports_hide_internal_filter_scores() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    public = game.visible_office_reports()

    assert public
    row = asdict(public[0])
    assert "hidden_truth_severity" not in row
    assert "hidden_coverage" not in row
    assert "hidden_omission" not in row
    assert row["summary"]
    assert row["confidence"] in {"高", "中", "有限"}


def test_low_transparency_official_delays_and_softens_bad_news() -> None:
    transparent = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    filtered = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    for game in (transparent, filtered):
        club = next(iter(game.current_campaign.engine.state.clubs.values()))
        club.wage_arrears_months = 4
        club.license_status = "administration"

    good = transparent.world.cabinet["财务与准入总监"]
    good.competence = 0.95
    good.integrity = 0.96
    good.loyalty = 0.35
    good.network_power = 0.10

    bad = filtered.world.cabinet["财务与准入总监"]
    bad.competence = 0.55
    bad.integrity = 0.22
    bad.loyalty = 0.94
    bad.network_power = 0.88

    transparent.advance(1, interactive=True)
    filtered.advance(1, interactive=True)

    good_report = next(
        item for item in transparent.office.reports
        if item.created_month == 1 and item.topic == "club_finance"
    )
    bad_report = next(
        item for item in filtered.office.reports
        if item.created_month == 1 and item.topic == "club_finance"
    )
    assert good_report.hidden_coverage > bad_report.hidden_coverage
    assert good_report.visible_month <= bad_report.visible_month
    assert "内部协调" in bad_report.summary or "审慎措辞" in bad_report.summary


def test_media_quote_is_cited_when_formal_policy_contradicts_it() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    statement = game.answer_media(
        clipping_id="club-rules-interview",
        outlet="足球财经网",
        question="足协会不会为困难俱乐部修改规则？",
        answer_style="rules_first",
        topic="俱乐部准入",
    )

    resolve_until(game, "club_bailout")
    trust_before = game.current_campaign.politics.stakeholders[
        "supporters_federation"
    ].trust
    game.resolve_decision("blank_cheque")

    assert statement.status == "contradicted"
    assert statement.cited_month == game.global_month
    assert game.office.quote_history
    assert "无条件保住豪门" in game.office.quote_history[-1].triggering_decision
    assert (
        game.current_campaign.politics.stakeholders["supporters_federation"].trust
        < trust_before
    )


def test_consistent_public_statement_earns_later_trust() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    statement = game.answer_media(
        clipping_id="uncertainty-interview",
        outlet="公共事务频道",
        question="您能否保证调查一定会定罪？",
        answer_style="transparent_uncertainty",
        topic="廉洁调查",
    )
    trust_before = game.current_campaign.politics.stakeholders["broadcaster"].trust

    advance_with_first_options(game, statement.due_month or 5)

    assert statement.status == "kept"
    assert statement.resolved_month == statement.due_month
    assert game.current_campaign.politics.stakeholders["broadcaster"].trust > trust_before


def test_leak_requires_sensitive_material_and_internal_motive() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    assert game.office.evaluate_leaks(game, force=True) is None

    game.record_meeting(
        meeting_id="sensitive-owner-meeting",
        visitor="陆景松",
        institution="职业联盟",
        subject="非公开准入缓冲",
        choice="president",
        sensitivity="sensitive",
    )
    for office, official in game.world.cabinet.items():
        official.loyalty = 0.98
        official.integrity = 0.98
        official.network_power = 0.02
        official.scandal_points = 0.0
        game.office.staff_grievance[office] = 0.0
    source = game.world.cabinet["秘书长"]
    source.loyalty = 0.03
    source.integrity = 0.20
    source.network_power = 0.96
    source.scandal_points = 0.90
    game.office.staff_grievance["秘书长"] = 1.0
    trust_before = game.current_campaign.engine.state.fan_trust

    leak = game.office.evaluate_leaks(game, force=True)

    assert leak is not None
    assert leak.source_office == "秘书长"
    assert leak.leaked_record_id == "sensitive-owner-meeting"
    assert game.current_campaign.engine.state.fan_trust < trust_before
    assert game.world.external_actions[-1]["action_type"] == "office_leak"


def test_causal_office_save_replays_actions_in_original_order() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    game.record_meeting(
        meeting_id="save-meeting",
        visitor="陆景松",
        institution="职业联盟",
        subject="准入政策",
        choice="secretary",
    )
    game.answer_media(
        clipping_id="save-interview",
        outlet="全国体育晨报",
        question="足协会不会公开已确认事实？",
        answer_style="transparent_uncertainty",
        topic="信息公开",
    )
    game.advance(1, interactive=True)
    payload = game.to_json()

    restored = CausalPresidentCareerGame.from_json(payload)

    assert restored.fingerprint() == game.fingerprint()
    assert restored.world.fingerprint() == game.world.fingerprint()
    assert restored.office.fingerprint() == game.office.fingerprint()
    assert len(restored.world.external_actions) == len(game.world.external_actions)
    assert restored.office.meetings[0].id == "save-meeting"
    assert restored.office.statements[0].id == "save-interview"


def test_office_actions_remain_locked_after_player_leaves_office() -> None:
    game = CausalPresidentCareerGame(strategy=Strategy.BALANCED, max_terms=3)
    game.world.force_crisis(severity=0.95)
    game.resolve_decision("submit_resignation")

    assert not game.can_act
    try:
        game.record_meeting(
            meeting_id="successor-meeting",
            visitor="陆景松",
            institution="职业联盟",
            subject="继任政府事务",
            choice="president",
        )
    except RuntimeError as exc:
        assert "successor-government" in str(exc)
    else:
        raise AssertionError("player controlled a successor meeting")
