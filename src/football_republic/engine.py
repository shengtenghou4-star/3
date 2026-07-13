"""Deterministic simulation engine for policy execution and delayed effects."""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain import NationalFootballSystem
from .programs import (
    CoachEducationGrant,
    ProgramReport,
    ScheduledCoachCohort,
    ScheduledMatchExpansion,
    ScheduledSchoolAgreement,
    YouthMatchGrant,
)


@dataclass(slots=True)
class SimulationEngine:
    state: NationalFootballSystem
    coach_pipeline: list[ScheduledCoachCohort] = field(default_factory=list)
    match_pipeline: list[ScheduledMatchExpansion] = field(default_factory=list)
    school_pipeline: list[ScheduledSchoolAgreement] = field(default_factory=list)
    audit_log: list[str] = field(default_factory=list)

    def enact_coach_education_grant(self, program: CoachEducationGrant) -> ProgramReport:
        report, cohorts = program.schedule(self.state)
        self.state.treasury -= report.public_spend
        self.coach_pipeline.extend(cohorts)
        self.audit_log.append(
            f"M{self.state.month}: coach grant spent {report.public_spend:.0f}; expected graduates {report.expected_graduates}"
        )
        return report

    def enact_youth_match_grant(self, program: YouthMatchGrant) -> ProgramReport:
        report, expansions = program.schedule(self.state)
        self.state.treasury -= report.public_spend
        self.match_pipeline.extend(expansions)
        self.audit_log.append(
            f"M{self.state.month}: match grant spent {report.public_spend:.0f}; scheduled match gain {report.expected_output:.2f}"
        )
        return report

    def negotiate_school_football_agreement(self, cofunding: float, political_cost: float = 0.08) -> bool:
        if cofunding < 0:
            raise ValueError("cofunding cannot be negative")
        if cofunding > self.state.treasury:
            raise ValueError("cofunding exceeds the association treasury")
        leverage = self.state.political_capital + 0.35 * self.state.integrity_reputation
        required = 0.72 - min(0.16, cofunding / 40_000_000)
        success = leverage >= required and self.state.political_capital >= political_cost
        if not success:
            self.state.political_capital = max(0.0, self.state.political_capital - political_cost * 0.35)
            self.audit_log.append(f"M{self.state.month}: school agreement failed")
            return False

        self.state.treasury -= cofunding
        self.state.political_capital = max(0.0, self.state.political_capital - political_cost)
        total_youth = sum(region.youth_population for region in self.state.regions.values())
        for region in self.state.regions.values():
            share = region.youth_population / max(total_youth, 1)
            programs = max(1, int(180 * share * region.execution_capacity))
            players = int(programs * 22 * region.parent_support)
            self.school_pipeline.append(
                ScheduledSchoolAgreement(
                    due_month=self.state.month + 6,
                    region_id=region.id,
                    added_school_programs=programs,
                    added_registered_players=players,
                )
            )
        self.audit_log.append(f"M{self.state.month}: school agreement signed; cofunding {cofunding:.0f}")
        return True

    def impose_club_licensing_reform(self, strictness: float, audit_budget: float) -> dict[str, str]:
        if not 0.0 <= strictness <= 1.0:
            raise ValueError("strictness must be between 0 and 1")
        if audit_budget < 0 or audit_budget > self.state.treasury:
            raise ValueError("invalid audit budget")
        self.state.treasury -= audit_budget
        audit_strength = min(1.0, audit_budget / max(len(self.state.clubs) * 400_000, 1.0))
        outcomes: dict[str, str] = {}

        for club in self.state.clubs.values():
            readiness = 0.40 * club.financial_health + 0.35 * club.licensing_compliance + 0.25 * club.integrity
            pressure = strictness - readiness
            detection = audit_strength * (0.55 + 0.45 * self.state.integrity_reputation)
            if pressure <= -0.05:
                outcome = "complied"
                club.licensing_compliance = min(1.0, club.licensing_compliance + 0.05 * strictness)
            elif club.integrity + detection >= 0.95:
                outcome = "restructured"
                club.monthly_wage_bill *= max(0.76, 1.0 - 0.22 * strictness)
                owner_injection = 1_000_000 * club.owner_patience * strictness
                club.cash += owner_injection
                club.licensing_compliance = min(1.0, club.licensing_compliance + 0.16)
                club.owner_patience = max(0.0, club.owner_patience - 0.05)
            elif detection >= 0.58:
                outcome = "sanctioned"
                club.license_status = "conditional"
                club.cash = max(0.0, club.cash - 150_000 * strictness)
                club.licensing_compliance = min(1.0, club.licensing_compliance + 0.08)
            else:
                outcome = "gamed_rules"
                club.licensing_compliance = min(1.0, club.licensing_compliance + 0.02)
                self.state.integrity_reputation = max(0.0, self.state.integrity_reputation - 0.015 * strictness)
            club.response_to_reform = outcome
            outcomes[club.id] = outcome

        self.audit_log.append(
            f"M{self.state.month}: licensing reform strictness {strictness:.2f}; audits {audit_budget:.0f}"
        )
        return outcomes

    def invest_in_senior_team(self, amount: float) -> None:
        if amount < 0 or amount > self.state.treasury:
            raise ValueError("invalid senior-team investment")
        self.state.treasury -= amount
        gain = min(8.0, amount / 4_000_000)
        self.state.national_team_strength = min(100.0, self.state.national_team_strength + gain)
        self.state.fan_trust = min(1.0, self.state.fan_trust + amount / 100_000_000)
        self.audit_log.append(f"M{self.state.month}: senior team investment {amount:.0f}; strength +{gain:.2f}")

    def advance_months(self, months: int = 1) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            self.state.month += 1
            self._deliver_due_programs()
            for club in self.state.clubs.values():
                club.close_month()
                if club.wage_arrears_months >= 4:
                    club.license_status = "excluded"
                    self.state.fan_trust = max(0.0, self.state.fan_trust - 0.01 * club.supporter_base)
            self.state.refresh_league_health()
            self._update_public_mood()

    def _deliver_due_programs(self) -> None:
        due_coaches = [item for item in self.coach_pipeline if item.due_month <= self.state.month]
        self.coach_pipeline = [item for item in self.coach_pipeline if item.due_month > self.state.month]
        for cohort in due_coaches:
            self.state.regions[cohort.region_id].licensed_youth_coaches += cohort.graduates
            self.audit_log.append(
                f"M{self.state.month}: {cohort.region_id} graduated {cohort.graduates} youth coaches"
            )

        due_matches = [item for item in self.match_pipeline if item.due_month <= self.state.month]
        self.match_pipeline = [item for item in self.match_pipeline if item.due_month > self.state.month]
        for expansion in due_matches:
            region = self.state.regions[expansion.region_id]
            region.annual_matches_per_player += expansion.added_matches_per_player
            region.registered_youth_players = min(
                region.youth_population,
                region.registered_youth_players + expansion.added_registered_players,
            )
            self.audit_log.append(
                f"M{self.state.month}: {expansion.region_id} match environment +{expansion.added_matches_per_player:.2f}"
            )

        due_schools = [item for item in self.school_pipeline if item.due_month <= self.state.month]
        self.school_pipeline = [item for item in self.school_pipeline if item.due_month > self.state.month]
        for agreement in due_schools:
            region = self.state.regions[agreement.region_id]
            region.school_programs += agreement.added_school_programs
            region.registered_youth_players = min(
                region.youth_population,
                region.registered_youth_players + agreement.added_registered_players,
            )
            self.audit_log.append(
                f"M{self.state.month}: {agreement.region_id} added {agreement.added_school_programs} school programs"
            )

    def _update_public_mood(self) -> None:
        league_signal = self.state.league_financial_health - 0.5
        trust_delta = 0.006 * league_signal
        if self.state.month % 6 == 0:
            trust_delta += 0.002 * ((self.state.national_team_strength - 50.0) / 10.0)
        self.state.fan_trust = max(0.0, min(1.0, self.state.fan_trust + trust_delta))
