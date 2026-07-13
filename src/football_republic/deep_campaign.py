"""Deep campaign variant using the full club pyramid ecosystem."""

from __future__ import annotations

from .campaign import (
    BoardReview,
    Campaign,
    PresidentialPlan,
    STRATEGIES,
    Strategy,
)
from .deep_scenario import build_deep_2026_scenario
from .ecosystem import ClubPyramidWorld
from .engine import SimulationEngine


class DeepCampaign(Campaign):
    """Campaign with two divisions, owner memory and database-driven national squads."""

    def __init__(
        self,
        engine: SimulationEngine | None = None,
        strategy: Strategy = Strategy.BALANCED,
    ) -> None:
        deep_engine = engine or SimulationEngine(build_deep_2026_scenario())
        super().__init__(engine=deep_engine, strategy=strategy)
        self.football = ClubPyramidWorld.build(self.engine.state, seed=3033)
        opening = self.dashboard()
        self.dashboards = [opening]
        self.monthly_history = [opening]

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        bailout_target = None
        if decision and decision.id == "club_bailout":
            bailout_target = min(
                self.engine.state.clubs.values(),
                key=lambda club: club.financial_health,
            ).id
        record = super().resolve_decision(option_id)
        if bailout_target is not None:
            self.football.pyramid.register_bailout_response(
                bailout_target,
                option_id,
            )
            owner = self.football.pyramid.owners[bailout_target]
            self.engine.audit_log.append(
                f"M{self.engine.state.month}: owner memory — {owner.name} "
                f"relationship {owner.relationship_with_fa:.2f}, "
                f"bailout memory {owner.bailout_memory}"
            )
        return record

    @property
    def total_domestic_matches(self) -> int:
        return len(self.football.pyramid.all_results)

    @property
    def clubs_in_administration(self) -> int:
        return sum(
            club.license_status == "administration"
            for club in self.engine.state.clubs.values()
        )

    @property
    def excluded_clubs(self) -> int:
        return sum(
            club.license_status == "excluded"
            for club in self.engine.state.clubs.values()
        )


def run_deep_strategy(
    strategy: Strategy,
) -> tuple[DeepCampaign, BoardReview]:
    campaign = DeepCampaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    review = campaign.run(24)
    return campaign, review
