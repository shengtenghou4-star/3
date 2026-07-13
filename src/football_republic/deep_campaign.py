"""Deep campaign variant using the full club pyramid ecosystem."""

from __future__ import annotations

from .campaign import (
    BoardReview,
    Campaign,
    STRATEGIES,
    Strategy,
    _AUTO_CHOICES,
)
from .deep_scenario import build_deep_2026_scenario
from .engine import SimulationEngine
from .governed_politics import GovernedPoliticalEconomy
from .governance import DecisionRecord
from .ordered_contracts import OrderedContractMarket
from .policy_registration import StrictRegistrationSystem
from .policy_world import PolicyAwareGenerationalWorld
from .political_economy import PoliticalReview
from .political_workload import PolicyWorkloadManager


class DeepCampaign(Campaign):
    """Campaign with the full pyramid, economy and stakeholder politics."""

    def __init__(
        self,
        engine: SimulationEngine | None = None,
        strategy: Strategy = Strategy.BALANCED,
    ) -> None:
        deep_engine = engine or SimulationEngine(build_deep_2026_scenario())
        super().__init__(engine=deep_engine, strategy=strategy)
        self.football = PolicyAwareGenerationalWorld.build(
            self.engine.state,
            seed=3033,
        )
        self.football.base.contracts = OrderedContractMarket(seed=3533)
        self.football.base.workload = PolicyWorkloadManager(seed=3433)
        self.football.economy.registration = StrictRegistrationSystem()
        self.football.economy.registration.register(
            0,
            self.engine.state.clubs,
            self.football.rosters,
        )
        self.politics = GovernedPoliticalEconomy()
        opening = self.dashboard()
        self.dashboards = [opening]
        self.monthly_history = [opening]

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        super().advance(months, interactive=interactive)
        if self.engine.state.month in (12, 24) and not self.pending_decisions:
            self.politics.record_year(
                self.engine.state.month,
                self.engine.state,
                self.football,
                self.decision_history,
            )

    def _trigger_governance_decision(self, month: int) -> None:
        self.politics.advance_month(
            month,
            self.engine.state,
            self.football,
        )
        super()._trigger_governance_decision(month)
        agenda = self.politics.agenda_for_month(month)
        if agenda is not None:
            self.pending_decisions.append(agenda)
            self.triggered_decisions.add(agenda.id)
            self.engine.audit_log.append(
                f"M{month}: national football congress opened — {agenda.title}"
            )

    def _auto_resolve_all(self) -> None:
        while self.pending_decisions:
            decision = self.pending_decisions[0]
            if decision.id.startswith("agenda_"):
                choice = self.politics.auto_choice(
                    decision.id,
                    self.strategy.value,
                )
            else:
                choice = _AUTO_CHOICES[self.strategy][decision.id]
            self.resolve_decision(choice)

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no pending governance decision")

        if decision.id.startswith("agenda_"):
            option = next(
                (item for item in decision.options if item.id == option_id),
                None,
            )
            if option is None:
                raise ValueError(
                    f"unknown option {option_id!r} for decision {decision.id!r}"
                )
            outcome, effects = self.politics.resolve_agenda(
                decision,
                option_id,
                self.engine.state,
                self.football,
            )
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
                f"M{self.engine.state.month}: congress agenda {decision.title} — "
                f"{option.title}; {'passed' if outcome.passed else 'failed'} "
                f"with {outcome.coalition_support:.0%} power"
            )
            self._refresh_latest_snapshot()
            if self.engine.state.month in (12, 24) and not self.pending_decisions:
                self.politics.record_year(
                    self.engine.state.month,
                    self.engine.state,
                    self.football,
                    self.decision_history,
                )
            return record

        bailout_target = None
        transfer_policy_decision = decision.id == "transfer_policy"
        if decision.id == "club_bailout":
            bailout_target = min(
                self.engine.state.clubs.values(),
                key=lambda club: club.financial_health,
            ).id
        record = super().resolve_decision(option_id)
        self.politics.react_to_decision(record)
        if transfer_policy_decision:
            self.football.configure_registration_policy(option_id)
            registration = self.football.economy.registration
            self.engine.audit_log.append(
                f"M{self.engine.state.month}: registration policy — "
                f"{registration.policy_name}, squad {registration.squad_limit}, "
                f"foreign {registration.foreign_limit}, "
                f"homegrown {registration.homegrown_minimum}"
            )
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
        if self.engine.state.month in (12, 24) and not self.pending_decisions:
            self.politics.record_year(
                self.engine.state.month,
                self.engine.state,
                self.football,
                self.decision_history,
            )
        return record

    @property
    def political_review(self) -> PoliticalReview:
        return self.politics.review(super().board_review().score)

    @property
    def total_domestic_matches(self) -> int:
        return len(self.football.pyramid.all_results) + len(
            self.football.domestic_cup.results
        )

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

    @property
    def active_loans(self) -> int:
        return len(self.football.contracts.active_loans)

    @property
    def free_agents(self) -> int:
        return len(self.football.contracts.free_agents)


def run_deep_strategy(
    strategy: Strategy,
) -> tuple[DeepCampaign, BoardReview]:
    campaign = DeepCampaign(strategy=strategy)
    campaign.enact_plan(STRATEGIES[strategy])
    review = campaign.run(24)
    return campaign, review
