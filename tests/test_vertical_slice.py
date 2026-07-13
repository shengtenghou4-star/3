from football_republic import (
    CoachEducationGrant,
    NationalFootballSystem,
    Region,
    SimulationEngine,
)


def region(region_id: str, *, execution: float, integrity: float) -> Region:
    return Region(
        id=region_id,
        name=region_id.upper(),
        population=10_000_000,
        youth_population=1_500_000,
        registered_youth_players=30_000,
        licensed_youth_coaches=600,
        average_coach_quality=0.55,
        full_size_pitches=180,
        small_sided_pitches=500,
        annual_matches_per_player=18,
        club_academies=20,
        school_programs=200,
        execution_capacity=execution,
        integrity=integrity,
        parent_support=0.60,
    )


def state() -> NationalFootballSystem:
    return NationalFootballSystem(
        month=0,
        treasury=10_000_000,
        political_capital=0.65,
        fan_trust=0.45,
        integrity_reputation=0.40,
        league_financial_health=0.50,
        national_team_strength=48.0,
        regions={
            "strong": region("strong", execution=0.90, integrity=0.90),
            "weak": region("weak", execution=0.45, integrity=0.45),
        },
    )


def test_grant_respects_budget_and_training_capacity() -> None:
    engine = SimulationEngine(state())
    report = engine.enact_coach_education_grant(
        CoachEducationGrant(
            budget=1_000_000,
            cost_per_trainee=10_000,
            national_training_slots=60,
            requested_trainees={"strong": 100, "weak": 100},
        )
    )

    assert report.approved_trainees == 60
    assert report.public_spend == 600_000
    assert engine.state.treasury == 9_400_000


def test_implementation_quality_changes_real_output() -> None:
    engine = SimulationEngine(state())
    report = engine.enact_coach_education_grant(
        CoachEducationGrant(
            budget=2_000_000,
            cost_per_trainee=10_000,
            national_training_slots=200,
            requested_trainees={"strong": 100, "weak": 100},
        )
    )

    strong = next(c for c in engine.coach_pipeline if c.region_id == "strong")
    weak = next(c for c in engine.coach_pipeline if c.region_id == "weak")
    assert strong.graduates > weak.graduates
    assert strong.leaked_or_wasted_spend < weak.leaked_or_wasted_spend
    assert report.expected_graduates == strong.graduates + weak.graduates


def test_policy_effect_is_delayed() -> None:
    engine = SimulationEngine(state())
    before = engine.state.licensed_youth_coaches
    report = engine.enact_coach_education_grant(
        CoachEducationGrant(
            budget=1_000_000,
            cost_per_trainee=10_000,
            national_training_slots=100,
            requested_trainees={"strong": 50, "weak": 50},
            training_months=9,
        )
    )

    engine.advance_months(8)
    assert engine.state.licensed_youth_coaches == before

    engine.advance_months(1)
    assert engine.state.licensed_youth_coaches == before + report.expected_graduates


def test_national_development_metric_is_player_weighted() -> None:
    system = state()
    expected = sum(
        r.development_environment * r.registered_youth_players
        for r in system.regions.values()
    ) / system.registered_youth_players
    assert system.youth_development_environment == expected
