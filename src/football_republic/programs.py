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
class ScheduledMatchExpansion:
    due_month: int
    region_id: str
    added_matches_per_player: float
    added_registered_players: int
    public_spend: float
    leaked_or_wasted_spend: float


@dataclass(frozen=True, slots=True)
class ScheduledSchoolAgreement:
    due_month: int
    region_id: str
    added_school_programs: int
    added_registered_players: int


@dataclass(frozen=True, slots=True)
class ProgramReport:
    program: str
    approved_units: int
    expected_output: float
    public_spend: float
    leaked_or_wasted_spend: float
    unspent_budget: float

    @property
    def approved_trainees(self) -> int:
        return self.approved_units

    @property
    def expected_graduates(self) -> int:
        return int(self.expected_output)


@dataclass(frozen=True, slots=True)
class CoachEducationGrant:
    budget: float
    cost_per_trainee: float
    national_training_slots: int
    requested_trainees: dict[str, int]
    training_months: int = 9

    def schedule(self, state: NationalFootballSystem) -> tuple[ProgramReport, list[ScheduledCoachCohort]]:
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
        capacity = min(self.national_training_slots, affordable_slots)
        allocations = _proportional_allocation(self.requested_trainees, capacity)
        cohorts: list[ScheduledCoachCohort] = []
        approved = graduates = 0
        spend = waste = 0.0

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
            region_waste = region_spend * (1.0 - delivery_rate)
            approved += trainee_count
            graduates += expected_graduates
            spend += region_spend
            waste += region_waste
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
                approved_units=approved,
                expected_output=float(graduates),
                public_spend=spend,
                leaked_or_wasted_spend=waste,
                unspent_budget=max(0.0, self.budget - spend),
            ),
            cohorts,
        )


@dataclass(frozen=True, slots=True)
class YouthMatchGrant:
    budget: float
    cost_per_player_slot: float
    requested_player_slots: dict[str, int]
    delivery_months: int = 4

    def schedule(self, state: NationalFootballSystem) -> tuple[ProgramReport, list[ScheduledMatchExpansion]]:
        if self.budget < 0:
            raise ValueError("budget cannot be negative")
        if self.cost_per_player_slot <= 0:
            raise ValueError("cost_per_player_slot must be positive")
        if self.delivery_months <= 0:
            raise ValueError("delivery_months must be positive")
        if self.budget > state.treasury:
            raise ValueError("program budget exceeds the association treasury")

        capacity = int(self.budget // self.cost_per_player_slot)
        allocations = _proportional_allocation(self.requested_player_slots, capacity)
        scheduled: list[ScheduledMatchExpansion] = []
        approved = 0
        output = spend = waste = 0.0

        for region_id, slots in allocations.items():
            if slots == 0:
                continue
            region = state.regions.get(region_id)
            if region is None:
                raise KeyError(f"unknown region: {region_id}")
            region_spend = slots * self.cost_per_player_slot
            delivery_rate = region.execution_capacity * (0.72 + 0.28 * region.integrity)
            effective_slots = int(slots * delivery_rate)
            match_gain = min(8.0, 8.0 * effective_slots / max(region.registered_youth_players, 1))
            player_gain = int(effective_slots * 0.08 * region.parent_support)
            region_waste = region_spend * (1.0 - delivery_rate)
            approved += slots
            output += match_gain
            spend += region_spend
            waste += region_waste
            scheduled.append(
                ScheduledMatchExpansion(
                    due_month=state.month + self.delivery_months,
                    region_id=region_id,
                    added_matches_per_player=match_gain,
                    added_registered_players=player_gain,
                    public_spend=region_spend,
                    leaked_or_wasted_spend=region_waste,
                )
            )

        return (
            ProgramReport(
                program="youth_match_grant",
                approved_units=approved,
                expected_output=output,
                public_spend=spend,
                leaked_or_wasted_spend=waste,
                unspent_budget=max(0.0, self.budget - spend),
            ),
            scheduled,
        )


def _proportional_allocation(requests: dict[str, int], capacity: int) -> dict[str, int]:
    if capacity < 0:
        raise ValueError("capacity cannot be negative")
    clean = {key: max(0, value) for key, value in requests.items()}
    total_requested = sum(clean.values())
    if total_requested == 0 or capacity == 0:
        return {key: 0 for key in clean}
    capacity = min(capacity, total_requested)
    allocations = {key: min(request, int(capacity * request / total_requested)) for key, request in clean.items()}
    leftover = capacity - sum(allocations.values())
    ranked = sorted(clean, key=lambda key: (clean[key] - allocations[key], key), reverse=True)
    while leftover > 0:
        progressed = False
        for key in ranked:
            if allocations[key] < clean[key]:
                allocations[key] += 1
                leftover -= 1
                progressed = True
                if leftover == 0:
                    break
        if not progressed:
            break
    return allocations
