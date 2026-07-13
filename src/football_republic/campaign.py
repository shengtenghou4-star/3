"""Playable 24-month presidential campaign."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .engine import SimulationEngine
from .football import FootballWorld
from .governance import (
    AnnualFinanceReport,
    DecisionRecord,
    GovernanceDecision,
    calculate_annual_finance,
    decision_for_month,
)
from .market import TransferMarket, TransferPolicy
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
    pending_decisions: int
    transfers_completed: int
    annual_income_received: float


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


_AUTO_CHOICES: dict[Strategy, dict[str, str]] = {
    Strategy.FOUNDATIONS: {
        "youth_safety_crisis": "transparent_reform",
        "transfer_policy": "homegrown_priority",
        "club_bailout": "conditional_rescue",
        "year_two_budget": "grassroots_acceleration",
        "national_team_media_crisis": "protect_coach",
        "regional_corruption_leak": "independent_probe",
    },
    Strategy.BALANCED: {
        "youth_safety_crisis": "transparent_reform",
        "transfer_policy": "financial_control",
        "club_bailout": "conditional_rescue",
        "year_two_budget": "balanced_renewal",
        "national_team_media_crisis": "protect_coach",
        "regional_corruption_leak": "internal_discipline",
    },
    Strategy.QUICK_RESULTS: {
        "youth_safety_crisis": "quiet_settlement",
        "transfer_policy": "open_market",
        "club_bailout": "blank_cheque",
        "year_two_budget": "qualification_surge",
        "national_team_media_crisis": "replace_coach",
        "regional_corruption_leak": "bury_case",
    },
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class Campaign:
    def __init__(
        self,
        engine: SimulationEngine | None = None,
        strategy: Strategy = Strategy.BALANCED,
    ) -> None:
        self.engine = engine or SimulationEngine(build_2026_scenario())
        self.strategy = strategy
        self.football = FootballWorld.build(self.engine.state, seed=2033)
        self.transfer_market = TransferMarket(seed=7070)
        self.initial_youth_environment = (
            self.engine.state.youth_development_environment
        )
        self.pending_decisions: list[GovernanceDecision] = []
        self.decision_history: list[DecisionRecord] = []
        self.finance_reports: list[AnnualFinanceReport] = []
        self.triggered_decisions: set[str] = set()
        self.plan_enacted = False
        opening = self.dashboard()
        self.dashboards: list[Dashboard] = [opening]
        self.monthly_history: list[Dashboard] = [opening]

    @property
    def current_decision(self) -> GovernanceDecision | None:
        return self.pending_decisions[0] if self.pending_decisions else None

    @property
    def annual_income_received(self) -> float:
        return sum(report.total_income for report in self.finance_reports)

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
        self._refresh_latest_snapshot()
        return {
            "coach_report": coach_report,
            "match_report": match_report,
            "school_success": school_success,
            "licensing_outcomes": licensing_outcomes,
        }

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        if interactive and self.pending_decisions:
            return
        if not interactive:
            self._auto_resolve_all()
        if self.engine.state.month + months > 24:
            months = 24 - self.engine.state.month

        for _ in range(months):
            if interactive and self.pending_decisions:
                break
            self.engine.advance_months(1)
            month = self.engine.state.month
            results = self.football.advance_month(month)
            for result in results:
                self.engine.audit_log.append(
                    f"M{month}: {result.competition} — "
                    f"{result.home_name} {result.scoreline} {result.away_name}"
                )
            if month == 18:
                self._run_transfer_window(month)
            self._trigger_governance_decision(month)
            snapshot = self.dashboard()
            self.monthly_history.append(snapshot)
            if month % 6 == 0:
                self.dashboards.append(snapshot)
            if self.pending_decisions:
                if interactive:
                    break
                self._auto_resolve_all()

    def run(self, months: int = 24) -> BoardReview:
        self.advance(months, interactive=False)
        return self.board_review()

    def resolve_decision(self, option_id: str) -> DecisionRecord:
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no pending governance decision")
        option = next(
            (item for item in decision.options if item.id == option_id), None
        )
        if option is None:
            raise ValueError(
                f"unknown option {option_id!r} for decision {decision.id!r}"
            )
        effects = self._apply_decision(decision.id, option.id)
        record = DecisionRecord(
            decision_id=decision.id,
            month=self.engine.state.month,
            title=decision.title,
            option_id=option.id,
            option_title=option.title,
            effects=effects,
        )
        self.pending_decisions.pop(0)
        self.decision_history.append(record)
        self.engine.audit_log.append(
            f"M{self.engine.state.month}: decision {decision.title} — {option.title}"
        )
        self._refresh_latest_snapshot()
        return record

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
            pending_decisions=len(self.pending_decisions),
            transfers_completed=len(self.transfer_market.history),
            annual_income_received=self.annual_income_received,
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

    def _trigger_governance_decision(self, month: int) -> None:
        decision = decision_for_month(month)
        if decision is None or decision.id in self.triggered_decisions:
            return
        if decision.id == "year_two_budget":
            report = calculate_annual_finance(
                self.engine.state,
                self.football.international.user_position,
            )
            self.engine.state.treasury += report.total_income
            self.finance_reports.append(report)
            self.engine.audit_log.append(
                f"M{month}: year-two football income {report.total_income:.0f} received"
            )
        self.pending_decisions.append(decision)
        self.triggered_decisions.add(decision.id)

    def _auto_resolve_all(self) -> None:
        while self.pending_decisions:
            decision = self.pending_decisions[0]
            choice = _AUTO_CHOICES[self.strategy][decision.id]
            self.resolve_decision(choice)

    def _apply_decision(
        self,
        decision_id: str,
        option_id: str,
    ) -> tuple[str, ...]:
        state = self.engine.state
        effects: list[str] = []

        if decision_id == "youth_safety_crisis":
            if option_id == "transparent_reform":
                spend = self._spend_up_to(2_000_000)
                state.fan_trust = _clamp(state.fan_trust + 0.035)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation + 0.050
                )
                state.political_capital = _clamp(
                    state.political_capital - 0.010
                )
                for region in state.regions.values():
                    region.parent_support = _clamp(
                        region.parent_support + 0.020
                    )
                for roster in self.football.rosters.values():
                    roster.medical_quality = _clamp(
                        roster.medical_quality + 0.045
                    )
                effects.extend(
                    (
                        f"Medical reform cost {spend:.0f}.",
                        "Fan trust +3.5pp; integrity +5.0pp.",
                        "Parent support and club medical standards improved.",
                    )
                )
            elif option_id == "quiet_settlement":
                spend = self._spend_up_to(800_000)
                state.fan_trust = _clamp(state.fan_trust + 0.008)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation - 0.012
                )
                effects.extend(
                    (
                        f"Settlement cost {spend:.0f}.",
                        "The immediate media cycle cooled.",
                        "Integrity reputation -1.2pp.",
                    )
                )
            else:
                state.political_capital = _clamp(
                    state.political_capital + 0.015
                )
                state.fan_trust = _clamp(state.fan_trust - 0.025)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation - 0.020
                )
                weakest = min(
                    state.regions.values(),
                    key=lambda region: region.execution_capacity,
                )
                weakest.execution_capacity = _clamp(
                    weakest.execution_capacity - 0.030
                )
                effects.extend(
                    (
                        "Central political capital +1.5pp.",
                        "Fan trust -2.5pp; integrity -2.0pp.",
                        f"{weakest.name} execution capacity weakened.",
                    )
                )

        elif decision_id == "transfer_policy":
            self.transfer_market.policy = TransferPolicy(option_id)
            if option_id == "homegrown_priority":
                state.political_capital = _clamp(
                    state.political_capital + 0.015
                )
                for club in state.clubs.values():
                    club.youth_minutes_share = _clamp(
                        club.youth_minutes_share + 0.030
                    )
                effects.append("Homegrown and U23 players receive a market premium.")
            elif option_id == "open_market":
                state.fan_trust = _clamp(state.fan_trust + 0.020)
                state.political_capital = _clamp(
                    state.political_capital - 0.015
                )
                for club in state.clubs.values():
                    club.youth_minutes_share = _clamp(
                        club.youth_minutes_share - 0.025
                    )
                effects.append("Mature and foreign players receive priority.")
            else:
                state.integrity_reputation = _clamp(
                    state.integrity_reputation + 0.012
                )
                for club in state.clubs.values():
                    club.licensing_compliance = _clamp(
                        club.licensing_compliance + 0.025
                    )
                effects.append("High-risk spending is constrained.")
            transfers = self._run_transfer_window(self.engine.state.month)
            effects.append(f"{len(transfers)} transfers completed in the window.")

        elif decision_id == "club_bailout":
            target = min(
                state.clubs.values(), key=lambda club: club.financial_health
            )
            if option_id == "conditional_rescue":
                spend = self._spend_up_to(4_000_000)
                target.cash += spend * 0.75
                target.monthly_wage_bill *= 0.90
                target.licensing_compliance = _clamp(
                    target.licensing_compliance + 0.120
                )
                target.owner_patience = _clamp(target.owner_patience - 0.080)
                state.fan_trust = _clamp(state.fan_trust + 0.008)
                effects.extend(
                    (
                        f"{target.name} received a conditional rescue.",
                        f"Association cost {spend:.0f}; wage bill cut 10%.",
                        "Licensing compliance improved.",
                    )
                )
            elif option_id == "refuse_bailout":
                state.integrity_reputation = _clamp(
                    state.integrity_reputation + 0.022
                )
                state.political_capital = _clamp(
                    state.political_capital - 0.025
                )
                state.fan_trust = _clamp(
                    state.fan_trust - 0.018 * target.supporter_base
                )
                effects.extend(
                    (
                        f"No public money was given to {target.name}.",
                        "Market discipline and integrity improved.",
                        "Political and supporter backlash increased.",
                    )
                )
            else:
                spend = self._spend_up_to(8_000_000)
                target.cash += spend
                target.owner_patience = _clamp(target.owner_patience + 0.100)
                state.fan_trust = _clamp(state.fan_trust + 0.015)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation - 0.045
                )
                effects.extend(
                    (
                        f"{target.name} received an unconditional rescue of {spend:.0f}.",
                        "Immediate supporter pressure eased.",
                        "Integrity reputation -4.5pp; moral hazard increased.",
                    )
                )

        elif decision_id == "year_two_budget":
            effects.extend(self._apply_year_two_budget(option_id))

        elif decision_id == "national_team_media_crisis":
            position = self.football.international.user_position
            if option_id == "protect_coach":
                state.national_team_strength = min(
                    100.0, state.national_team_strength + 0.60
                )
                state.political_capital = _clamp(
                    state.political_capital - 0.012
                )
                trust_delta = 0.010 if position <= 3 else -0.018
                state.fan_trust = _clamp(state.fan_trust + trust_delta)
                effects.extend(
                    (
                        "Tactical continuity preserved; team strength +0.6.",
                        f"Fan-trust reaction {trust_delta:+.1%}.",
                        "The president personally owns the next results.",
                    )
                )
            elif option_id == "replace_coach":
                spend = self._spend_up_to(3_000_000)
                state.national_team_strength = min(
                    100.0, state.national_team_strength + 1.40
                )
                state.fan_trust = _clamp(state.fan_trust + 0.025)
                state.political_capital = _clamp(
                    state.political_capital - 0.025
                )
                effects.extend(
                    (
                        f"Coaching change cost {spend:.0f}.",
                        "Short-term team strength +1.4; fan trust +2.5pp.",
                        "Political capital fell and tactical continuity reset.",
                    )
                )
            else:
                spend = self._spend_up_to(1_000_000)
                state.fan_trust = _clamp(state.fan_trust + 0.012)
                state.political_capital = _clamp(
                    state.political_capital + 0.010
                )
                state.integrity_reputation = _clamp(
                    state.integrity_reputation - 0.018
                )
                effects.extend(
                    (
                        f"Communications campaign cost {spend:.0f}.",
                        "Fan trust and political control improved temporarily.",
                        "Integrity reputation -1.8pp.",
                    )
                )

        elif decision_id == "regional_corruption_leak":
            weakest = min(
                state.regions.values(), key=lambda region: region.integrity
            )
            if option_id == "independent_probe":
                spend = self._spend_up_to(2_000_000)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation + 0.080
                )
                state.political_capital = _clamp(
                    state.political_capital - 0.055
                )
                weakest.integrity = _clamp(weakest.integrity + 0.100)
                weakest.execution_capacity = _clamp(
                    weakest.execution_capacity - 0.040
                )
                effects.extend(
                    (
                        f"Independent investigation cost {spend:.0f}.",
                        "National integrity +8.0pp.",
                        f"{weakest.name} projects slowed during the investigation.",
                    )
                )
            elif option_id == "internal_discipline":
                spend = self._spend_up_to(500_000)
                state.integrity_reputation = _clamp(
                    state.integrity_reputation + 0.035
                )
                state.political_capital = _clamp(
                    state.political_capital - 0.015
                )
                weakest.integrity = _clamp(weakest.integrity + 0.045)
                effects.extend(
                    (
                        f"Internal discipline cost {spend:.0f}.",
                        "Integrity improved without stopping the full programme.",
                        "External transparency remains limited.",
                    )
                )
            else:
                state.political_capital = _clamp(
                    state.political_capital + 0.020
                )
                state.integrity_reputation = _clamp(
                    state.integrity_reputation - 0.080
                )
                state.fan_trust = _clamp(state.fan_trust - 0.045)
                weakest.execution_capacity = _clamp(
                    weakest.execution_capacity + 0.020
                )
                effects.extend(
                    (
                        "Local projects continued without interruption.",
                        "Political capital +2.0pp.",
                        "Integrity -8.0pp; fan trust -4.5pp.",
                    )
                )

        return tuple(effects)

    def _apply_year_two_budget(self, option_id: str) -> tuple[str, ...]:
        packages = {
            "grassroots_acceleration": {
                "coach": 9_000_000,
                "match": 8_000_000,
                "school": 3_000_000,
                "audit": 2_000_000,
                "senior": 2_000_000,
                "strictness": 0.76,
            },
            "balanced_renewal": {
                "coach": 6_000_000,
                "match": 5_000_000,
                "school": 3_000_000,
                "audit": 2_000_000,
                "senior": 7_000_000,
                "strictness": 0.62,
            },
            "qualification_surge": {
                "coach": 2_000_000,
                "match": 2_000_000,
                "school": 1_000_000,
                "audit": 1_000_000,
                "senior": 16_000_000,
                "strictness": 0.42,
            },
        }
        package = dict(packages[option_id])
        desired = sum(
            package[key]
            for key in ("coach", "match", "school", "audit", "senior")
        )
        scale = min(1.0, self.engine.state.treasury / max(desired, 1.0))
        for key in ("coach", "match", "school", "audit", "senior"):
            package[key] *= scale

        coach_report = self.engine.enact_coach_education_grant(
            CoachEducationGrant(
                budget=package["coach"],
                cost_per_trainee=20_000,
                national_training_slots=600,
                requested_trainees={
                    "coast": 220,
                    "heartland": 360,
                    "frontier": 220,
                },
                training_months=8,
            )
        )
        match_report = self.engine.enact_youth_match_grant(
            YouthMatchGrant(
                budget=package["match"],
                cost_per_player_slot=100,
                requested_player_slots={
                    "coast": 45_000,
                    "heartland": 65_000,
                    "frontier": 35_000,
                },
                delivery_months=4,
            )
        )
        school_success = self.engine.negotiate_school_football_agreement(
            package["school"], political_cost=0.045
        )
        self.engine.impose_club_licensing_reform(
            package["strictness"], package["audit"]
        )
        self.engine.invest_in_senior_team(package["senior"])
        return (
            f"Second-year package spent {desired * scale:.0f}.",
            f"Expected new licensed coaches: {coach_report.expected_graduates}.",
            f"Scheduled match-environment output: {match_report.expected_output:.2f}.",
            f"Second school agreement {'signed' if school_success else 'failed'}.",
            f"Senior-team investment: {package['senior']:.0f}.",
        )

    def _run_transfer_window(self, month: int):
        records = self.transfer_market.run_window(
            month,
            self.engine.state.clubs,
            self.football.rosters,
        )
        for record in records:
            self.engine.audit_log.append(
                f"M{month}: transfer — {record.player_name}, "
                f"{record.seller_name} to {record.buyer_name}, fee {record.fee:.0f}"
            )
        self.engine.state.refresh_league_health()
        return records

    def _spend_up_to(self, amount: float) -> float:
        spend = min(amount, self.engine.state.treasury)
        self.engine.state.treasury -= spend
        return spend

    def _refresh_latest_snapshot(self) -> None:
        snapshot = self.dashboard()
        month = self.engine.state.month
        if self.monthly_history and self.monthly_history[-1].month == month:
            self.monthly_history[-1] = snapshot
        if self.dashboards and self.dashboards[-1].month == month:
            self.dashboards[-1] = snapshot


def run_strategy(strategy: Strategy) -> tuple[Campaign, BoardReview]:
    campaign = Campaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    review = campaign.run(24)
    return campaign, review
