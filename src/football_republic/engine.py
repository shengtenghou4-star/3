"""Deterministic simulation engine for policy execution and delayed effects."""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain import NationalFootballSystem
from .programs import CoachEducationGrant, ProgramReport, ScheduledCoachCohort


@dataclass(slots=True)
class SimulationEngine:
    state: NationalFootballSystem
    coach_pipeline: list[ScheduledCoachCohort] = field(default_factory=list)

    def enact_coach_education_grant(self, program: CoachEducationGrant) -> ProgramReport:
        report, cohorts = program.schedule(self.state)
        self.state.treasury -= report.public_spend
        self.coach_pipeline.extend(cohorts)
        return report

    def advance_months(self, months: int = 1) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            self.state.month += 1
            due = [cohort for cohort in self.coach_pipeline if cohort.due_month <= self.state.month]
            self.coach_pipeline = [
                cohort for cohort in self.coach_pipeline if cohort.due_month > self.state.month
            ]
            for cohort in due:
                self.state.regions[cohort.region_id].licensed_youth_coaches += cohort.graduates
