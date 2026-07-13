"""Playable 24-month presidential campaign."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .engine import SimulationEngine
from .football import FootballWorld
from .programs import CoachEducationGrant, YouthMatchGrant
from .scenario import build_2026_scenario


class Strategy(str, Enum):
    FOUNDATIONS = "foundations"
    BALANCED = "balanced"
    QUICK_RESULTS = "quick-results"


@dataclass(frozen=True, slots=True)
class PresidentialPlan:
    coach_budget: float
    match_budget: float
    school_cofunding: float
    licensing_strictness: float
    audit_budget: float
    senior_team_budget: float

    @property
    def total_budget(self) -> float:
        return (
            self.coach_budget
            + self.match_budget
            + self.school_cofunding
            + self.audit_budget
            + self.senior_team_budget
        )


@dataclass(frozen=True, slots=True)
class Dashboard:
    month: int
    treasury: float
    political_capital: float
    fan_trust: float
    integrity_reputation: float
    league_financial_health: float
    national_team_strength: float
    youth_environment: float
    registered_youth_players: int
    licensed_youth_coaches: int
    solvent_club_share: float
    qualifier_position: int
    qualifier_points: int
    league_leader: str
    total_matches_played: int


@dataclass(frozen=True, slots=True)
class BoardReview:
    score: float
    verdict: str
    youth_change: float
    club_solvent_share: float
    fan_trust: float
    national_team_strength: float
    qualifier_position: int
    explanation: tuple[str, ...]


STRATEGIES: dict[Strategy, PresidentialPlan] = {
    Strategy.FOUNDATIONS: PresidentialPlan(
        18_000_000, 16_000_000, 8_000_000, 0.72, 3_000_000, 4_000_000
    ),
    Strategy.BALANCED: PresidentialPlan(
        12_000_000, 10_000_000, 7_000_000, 0.58, 2_500_000, 14_000_000
    ),
    Strategy.QUICK_RESULTS: PresidentialPlan(
        5_000_000, 4_000_000, 2_000_000, 0.35, 1_000_000, 32_000_000
    ),
}


class Campaign:
    def __init__(self, engine: SimulationEngine | None = None) -> None:
        self.engine = engine or SimulationEngine(build_2026_scenario())
        self.football = FootballWorld.build(self.engine.state, seed=2033)
        self.initial_youth_environment = (
            self.engine.state.youth_development_environment
        )
        opening = self.dashboard()
        self.dashboards: list[Dashboard] = [opening]
        self.monthly_history: list[Dashboard] = [opening]
        self.plan_enacted = False

    def enact_plan(self, plan: PresidentialPlan) -> dict[str, object]:
        if self.plan_enacted:
            raise RuntimeError(
                "the opening presidential plan has already been enacted"
            )
        if plan.total_budget > self.engine.state.treasury:
            raise ValueError("presidential plan exceeds available treasury")
        coach_report = self.engine.enact_coach_education_grant(
            CoachEducationGrant(
                budget=plan.coach_budget,
                cost_per_trainee=20_000,
                national_training_slots=900,
                requested_trainees={
                    "coast": 380,
                    "heartland": 520,
                    "frontier": 300,
                },
            )
        )
        match_report = self.engine.enact_youth_match_grant(
            YouthMatchGrant(
                budget=plan.match_budget,
                cost_per_player_slot=100,
                requested_player_slots={
                    "coast": 70_000,
                    "heartland": 95_000,
                    "frontier": 45_000,
                },
            )
        )
        school_success = self.engine.negotiate_school_football_agreement(
            plan.school_cofunding
        )
        licensing_outcomes = self.engine.impose_club_licensing_reform(
            plan.licensing_strictness, plan.audit_budget
        )
        self.engine.invest_in_senior_team(plan.senior_team_budget)
        self.plan_enacted = True
        return {
            "coach_report": coach_report,
            "match_report": match_report,
            "school_success": school_success,
            "licensing_outcomes": licensing_outcomes,
        }

    def advance(self, months: int = 1) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        if self.engine.state.month + months > 24:
            months = 24 - self.engine.state.month
        for _ in range(months):
            self.engine.advance_months(1)
            month = self.engine.state.month
            results = self.football.advance_month(month)
            for result in results:
                self.engine.audit_log.append(
                    f"M{month}: {result.competition} — "
                    f"{result.home_name} {result.scoreline} {result.away_name}"
                )
            snapshot = self.dashboard()
            self.monthly_history.append(snapshot)
            if month % 6 == 0:
                self.dashboards.append(snapshot)

    def run(self, months: int = 24) -> BoardReview:
        self.advance(months)
        return self.board_review()

    def dashboard(self) -> Dashboard:
        state = self.engine.state
        qualifier_rows = {
            row.team_id: row
            for row in self.football.international.sorted_table()
        }
        user_row = qualifier_rows[
            self.football.international.user_code
        ]
        league_table = self.football.domestic_league.sorted_table()
        leader = (
            league_table[0].team_name
            if league_table and league_table[0].played
            else "Pre-season"
        )
        return Dashboard(
            month=state.month,
            treasury=state.treasury,
            political_capital=state.political_capital,
            fan_trust=state.fan_trust,
            integrity_reputation=state.integrity_reputation,
            league_financial_health=state.league_financial_health,
            national_team_strength=state.national_team_strength,
            youth_environment=state.youth_development_environment,
            registered_youth_players=state.registered_youth_players,
            licensed_youth_coaches=state.licensed_youth_coaches,
            solvent_club_share=state.solvent_club_share,
            qualifier_position=self.football.international.user_position,
            qualifier_points=user_row.points,
            league_leader=leader,
            total_matches_played=(
                len(self.football.domestic_league.results)
                + len(self.football.international.results)
            ),
        )

    def board_review(self) -> BoardReview:
        state = self.engine.state
        youth_change = (
            state.youth_development_environment
            - self.initial_youth_environment
        )
        qualifier_position = self.football.international.user_position
        qualifier_points = {
            1: 12.0,
            2: 10.5,
            3: 7.5,
            4: 4.5,
            5: 2.0,
            6: 0.0,
        }[qualifier_position]
        youth_component = max(
            0.0, min(28.0, 11.0 + youth_change * 4.2)
        )
        club_component = 18.0 * state.solvent_club_share
        trust_component = 14.0 * state.fan_trust
        integrity_component = 10.0 * state.integrity_reputation
        team_component = max(
            0.0,
            min(
                12.0,
                5.0 + (state.national_team_strength - 47.5) * 1.15,
            ),
        )
        capital_component = 6.0 * state.political_capital
        score = (
            youth_component
            + club_component
            + trust_component
            + integrity_component
            + team_component
            + qualifier_points
            + capital_component
        )
        if score >= 67:
            verdict = "renewed with a strong mandate"
        elif score >= 55:
            verdict = "renewed under supervision"
        elif score >= 45:
            verdict = "survived by one vote"
        else:
            verdict = "removed from office"

        explanation = (
            f"Youth environment changed by {youth_change:+.2f} points.",
            f"{state.solvent_club_share:.0%} of clubs remained solvent and eligible.",
            f"Longhua finished {qualifier_position}/6 in the qualification group.",
            f"Fan trust finished at {state.fan_trust:.0%}.",
            f"National-team strength finished at {state.national_team_strength:.1f}/100.",
            f"Integrity reputation finished at {state.integrity_reputation:.0%}.",
        )
        return BoardReview(
            score=score,
            verdict=verdict,
            youth_change=youth_change,
            club_solvent_share=state.solvent_club_share,
            fan_trust=state.fan_trust,
            national_team_strength=state.national_team_strength,
            qualifier_position=qualifier_position,
            explanation=explanation,
        )


def run_strategy(strategy: Strategy) -> tuple[Campaign, BoardReview]:
    campaign = Campaign()
    campaign.enact_plan(STRATEGIES[strategy])
    review = campaign.run(24)
    return campaign, review
