"""Policy-correct political economy overrides for commercial and labor realism."""

from __future__ import annotations

from typing import Any

from .domain import NationalFootballSystem
from .political_economy import (
    PoliticalEconomy,
    PoliticalEvent,
    StakeholderProfile,
    _clamp,
)


class GovernedPoliticalEconomy(PoliticalEconomy):
    """Ensure failed bills scale down and stakeholder pressure changes cash flow."""

    def _apply_pressure(
        self,
        month: int,
        actor: StakeholderProfile,
        state: NationalFootballSystem,
        football: Any,
    ) -> None:
        if actor.id != "sponsor_council":
            super()._apply_pressure(month, actor, state, football)
            return

        effects: list[str] = []
        active = [
            contract
            for contract in football.economy.sponsors.contracts.values()
            if contract.status == "active"
        ]
        if active:
            contract = min(active, key=lambda item: item.annual_value)
            contract.status = "suspended"
            club = state.clubs[contract.club_id]
            club.monthly_revenue = max(
                0.0,
                club.monthly_revenue - contract.monthly_component,
            )
            effects.append(
                f"{contract.sponsor_name} suspended ¥{contract.monthly_component:,.0f} "
                "of monthly revenue"
            )
        else:
            effects.append("sponsors issued a collective public warning")
        actor.mobilization = _clamp(actor.mobilization + 0.05)
        self.event_history.append(
            PoliticalEvent(
                month=month,
                actor_id=actor.id,
                actor_name=actor.name,
                event_type="pressure",
                headline=f"{actor.name} escalated pressure on the presidency",
                effects=tuple(effects),
            )
        )

    def _apply_agenda_effects(
        self,
        agenda_id: str,
        option_id: str,
        scale: float,
        state: NationalFootballSystem,
        football: Any,
    ) -> tuple[str, ...]:
        if agenda_id != "agenda_calendar_compact":
            return super()._apply_agenda_effects(
                agenda_id,
                option_id,
                scale,
                state,
                football,
            )

        def spend(amount: float) -> float:
            actual = min(state.treasury, amount * scale)
            state.treasury -= actual
            return actual

        if option_id == "player_welfare_compact":
            cost = spend(1_800_000.0)
            football.workload.congestion_multiplier = 1.0 - 0.28 * scale
            football.workload.international_release_cost = 4.5 - 1.1 * scale
            football.workload.injury_multiplier = 1.0 - 0.25 * scale
            for roster in football.rosters.values():
                roster.medical_quality = _clamp(
                    roster.medical_quality + 0.045 * scale
                )
            return (
                f"Player welfare programme cost ¥{cost:,.0f}.",
                "Congestion, release fatigue and injury exposure were reduced in proportion to legislative authority.",
            )

        if option_id == "managed_flexibility":
            cost = spend(800_000.0)
            football.workload.congestion_multiplier = 1.0 - 0.10 * scale
            football.workload.international_release_cost = 4.5 - 0.5 * scale
            football.workload.injury_multiplier = 1.0 - 0.10 * scale
            for roster in football.rosters.values():
                roster.medical_quality = _clamp(
                    roster.medical_quality + 0.020 * scale
                )
            return (
                f"Medical monitoring and compensation cost ¥{cost:,.0f}.",
                "Commercial flexibility remained with proportionate safety gains.",
            )

        football.workload.congestion_multiplier = 1.0 + 0.14 * scale
        football.workload.international_release_cost = 4.5 + 0.7 * scale
        football.workload.injury_multiplier = 1.0 + 0.12 * scale
        for club in state.clubs.values():
            club.monthly_revenue *= 1.0 + 0.012 * scale
        return (
            "Commercial match inventory and club revenue increased.",
            "Congestion, injury and national-team release pressure increased in proportion to legislative authority.",
        )
