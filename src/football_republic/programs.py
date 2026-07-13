"""Policy programs available to the football association president."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import NationalFootballSystem


@dataclass(frozen=True, slots=True)
class ScheduledCoachCohort:
    due_month: int
    region_id: str
    graduates: int
    public_spend: float
    leaked_or_wasted_spend: float


@dataclass(frozen=True, slots=True)
class ProgramReport:
    program: str
    approved_trainees: int
    expected_graduates: int
    public_spend: float
    leaked_or_wasted_spend: float
    unspent_budget: float


@dataclass(frozen=True, slots=True)
class CoachEducationGrant:
    """National grant for producing licensed youth coaches.

    Delivery is constrained by money, national training slots, regional
    execution capacity, and integrity. Graduates arrive after a policy lag.
    """

    budget: float
    cost_per_trainee: float
    national_training_slots: int
    requested_trainees: dict[str, int]
    training_months: int = 9

    def schedule(
        self,
        state: NationalFootballSystem,
    ) -> tuple[ProgramReport, list[ScheduledCoachCohort]]:
        if self.budget < 0:
            raise ValueError("budget cannot be negative")
        if self.cost_per_trainee <= 0:
            raise ValueError("cost_per_trainee must be positive")
        if self.national_training_slots < 0:
            raise ValueError("national_training_slots cannot be negative")
        if self.training_months <= 0:
            raise ValueError("training_months must be positive")
        if self.budget > state.treasury:
            raise ValueError("program budget exceeds the association treasury")

        affordable_slots = int(self.budget // self.cost_per_trainee)
        remaining_slots = min(self.national_training_slots, affordable_slots)
        remaining_budget = self.budget
        cohorts: list[ScheduledCoachCohort] = []

        total_requested = sum(max(0, value) for value in self.requested_trainees.values())
        if total_requested == 0 or remaining_slots == 0:
            return (
                ProgramReport(
                    program="coach_education_grant",
                    approved_trainees=0,
                    expected_graduates=0,
                    public_spend=0.0,
                    leaked_or_wasted_spend=0.0,
                    unspent_budget=self.budget,
                ),
                cohorts,
            )

        # Allocate scarce slots proportionally, then hand out leftovers by
        # largest unmet request. This avoids map-order favoritism.
        allocations: dict[str, int] = {}
        for region_id, request in self.requested_trainees.items():
            request = max(0, request)
            share = int(remaining_slots * request / total_requested)
            allocations[region_id] = min(request, share)

        leftover = remaining_slots - sum(allocations.values())
        ranked = sorted(
            self.requested_trainees,
            key=lambda rid: self.requested_trainees[rid] - allocations.get(rid, 0),
            reverse=True,
        )
        while leftover > 0:
            progressed = False
            for region_id in ranked:
                request = max(0, self.requested_trainees[region_id])
                if allocations.get(region_id, 0) < request:
                    allocations[region_id] = allocations.get(region_id, 0) + 1
                    leftover -= 1
                    progressed = True
                    if leftover == 0:
                        break
            if not progressed:
                break

        approved = 0
        graduates = 0
        spend = 0.0
        waste = 0.0

        for region_id, trainee_count in allocations.items():
            if trainee_count == 0:
                continue
            region = state.regions.get(region_id)
            if region is None:
                raise KeyError(f"unknown region: {region_id}")

            region_spend = trainee_count * self.cost_per_trainee
            delivery_rate = region.execution_capacity * (0.65 + 0.35 * region.integrity)
            completion_rate = min(0.95, 0.55 + 0.30 * region.average_coach_quality)
            expected_graduates = int(trainee_count * delivery_rate * completion_rate)
            useful_spend = region_spend * delivery_rate
            region_waste = region_spend - useful_spend

            approved += trainee_count
            graduates += expected_graduates
            spend += region_spend
            waste += region_waste
            remaining_budget -= region_spend

            cohorts.append(
                ScheduledCoachCohort(
                    due_month=state.month + self.training_months,
                    region_id=region_id,
                    graduates=expected_graduates,
                    public_spend=region_spend,
                    leaked_or_wasted_spend=region_waste,
                )
            )

        return (
            ProgramReport(
                program="coach_education_grant",
                approved_trainees=approved,
                expected_graduates=graduates,
                public_spend=spend,
                leaked_or_wasted_spend=waste,
                unspent_budget=max(0.0, remaining_budget),
            ),
            cohorts,
        )
