from football_republic.campaign import Strategy
from football_republic.patronage_runtime import CareerJusticeHistory


def high_risk_history() -> tuple[CareerJusticeHistory, str]:
    history = CareerJusticeHistory(strategy=Strategy.BALANCED, max_terms=4)
    subject_id = "central-fa-chair"
    subject = history.people[subject_id]
    subject.integrity = 0.05
    subject.network_power = 0.98
    for tie in history._ties_for(subject_id):
        if not tie.disclosed:
            tie.strength = max(tie.strength, 0.90)
    return history, subject_id


def advance_until_justice(history: CareerJusticeHistory, limit: int = 8) -> None:
    guard = 0
    while guard < 80:
        decision = history.current_decision
        if decision is not None and decision.id.startswith("justice_referral_"):
            return
        if decision is not None:
            history._auto_resolve_current()
        else:
            history.advance(1, interactive=True)
        guard += 1
        if history.global_month > limit:
            break
    raise AssertionError("justice referral did not open at the expected checkpoint")


def test_named_people_and_hidden_patronage_exist_at_start() -> None:
    history = CareerJusticeHistory(max_terms=2)

    assert len(history.people) >= 20
    assert len(history.patronage_ties) >= 10
    assert any(not item.disclosed for item in history.patronage_ties.values())
    assert any(item.status == "cabinet" for item in history.people.values())
    assert any(item.status == "president" for item in history.people.values())


def test_cabinet_appointment_uses_a_persistent_person_and_writes_career() -> None:
    history = CareerJusticeHistory(max_terms=2)

    official = history._replace_official(
        "财务与准入总监",
        "technocrat",
        "test merit appointment",
    )

    assert official.id in history.people
    person = history.people[official.id]
    assert person.role == "财务与准入总监"
    assert person.status == "cabinet"
    assert any(
        item.person_id == person.id and item.event_type == "cabinet appointment"
        for item in history.career_history
    )


def test_presidential_candidates_come_from_real_career_pool() -> None:
    history = CareerJusticeHistory(max_terms=2)

    candidates = history._generate_candidates("career-test")

    assert len(candidates) == 3
    assert len({item.name for item in candidates}) == 3
    assert {item.name for item in candidates} <= {
        person.name for person in history.people.values()
    }
    assert all(item.id in history._candidate_people for item in candidates)


def test_independent_referral_suspends_subject_and_discloses_network() -> None:
    history, subject_id = high_risk_history()
    advance_until_justice(history)

    history.resolve_decision("independent_referral")

    case = history.justice_cases[-1]
    assert case.subject_id == subject_id
    assert case.stage == "investigation"
    assert history.people[subject_id].status == "suspended"
    assert all(
        history.patronage_ties[tie_id].disclosed
        for tie_id in case.related_ties
    )
    assert history.justice_independence > 0.62


def test_case_progresses_through_charge_trial_and_appeal() -> None:
    history, subject_id = high_risk_history()
    advance_until_justice(history)
    history.resolve_decision("independent_referral")

    history.advance(6, interactive=False)

    case = history.justice_cases[0]
    assert case.stage == "final"
    assert case.outcome in {
        "conviction upheld",
        "sanction reduced",
        "conviction reversed",
        "acquitted at trial",
    }
    assert case.closed_global_month is not None
    stages = [
        item.stage for item in history.justice_history
        if item.case_id == case.id
    ]
    assert "charged" in stages
    assert any(stage in {"appeal", "final"} for stage in stages)
    assert history.people[subject_id].status in {"banned", "active"}


def test_suppressed_case_can_leak_and_restart() -> None:
    history, subject_id = high_risk_history()
    advance_until_justice(history)
    history.resolve_decision("shield_network")

    history.advance(4, interactive=False)

    case = history.justice_cases[0]
    assert case.route == "leaked after suppression"
    assert case.stage == "investigation"
    assert all(tie.disclosed for tie in history._ties_for(subject_id))


def test_banned_person_cannot_return_as_a_presidential_candidate() -> None:
    history, subject_id = high_risk_history()
    subject = history.people[subject_id]
    subject.network_power = 0.05
    advance_until_justice(history)
    history.resolve_decision("independent_referral")
    history.advance(6, interactive=False)

    assert history.people[subject_id].status == "banned"
    candidates = history._generate_candidates("post-conviction")
    assert subject.name not in {item.name for item in candidates}


def test_resignation_writes_outgoing_and_caretaker_careers() -> None:
    history = CareerJusticeHistory(max_terms=3)
    outgoing_name = history.current_president.name
    history.force_crisis(severity=0.92)

    history.resolve_decision("submit_resignation")

    outgoing = next(item for item in history.people.values() if item.name == outgoing_name)
    caretaker_name = history.current_president.name.replace("（看守）", "")
    caretaker = next(item for item in history.people.values() if item.name == caretaker_name)
    assert outgoing.role == "前主席"
    assert outgoing.status == "active"
    assert caretaker.role == "代理主席"
    assert caretaker.status == "president"
    assert any(
        item.person_name == outgoing_name and item.event_type == "left presidency"
        for item in history.career_history
    )


def test_json_replay_preserves_people_networks_and_justice_cases() -> None:
    history = CareerJusticeHistory(strategy=Strategy.BALANCED, max_terms=4)
    advance_until_justice(history)
    history.resolve_decision("internal_review")
    history.advance(5, interactive=False)
    payload = history.to_json()

    restored = CareerJusticeHistory.from_json(payload)

    assert restored.global_month == history.global_month
    assert restored.fingerprint() == history.fingerprint()
    assert len(restored.people) == len(history.people)
    assert len(restored.justice_cases) == len(history.justice_cases)
    assert len(restored.career_history) == len(history.career_history)


def test_ten_year_history_preserves_careers_cases_and_football_continuity() -> None:
    history = CareerJusticeHistory(
        strategy=Strategy.QUICK_RESULTS,
        max_terms=5,
    )

    history.run_years(10)

    assert history.finished
    assert history.global_month == 120
    assert len(history.term_records) == 5
    assert len(history.season_history) == 10
    assert history.career_history
    assert history.justice_cases
    assert history.election_history
    assert all(person.age >= 41 for person in history.people.values())
    assert len({player.id for roster in history.current_campaign.football.rosters.values() for player in roster.players}) > 0
