"""Policy-ordered generational world with post-market registration windows."""

from __future__ import annotations

from .advanced_ecosystem import AdvancedClubWorld
from .domain import NationalFootballSystem
from .football import MatchResult
from .generational_economy import GenerationalEconomy, GenerationalWorld


class PolicyAwareGenerationalWorld(GenerationalWorld):
    """Run registration after transfers in months 7 and 19."""

    @classmethod
    def build(
        cls,
        state: NationalFootballSystem,
        seed: int = 2026,
    ) -> "PolicyAwareGenerationalWorld":
        base = AdvancedClubWorld.build(state, seed=seed)
        economy = GenerationalEconomy.build(state.clubs)
        economy.registration.register(0, state.clubs, base.rosters)
        return cls(base=base, economy=economy)

    def advance_month(self, month: int) -> list[MatchResult]:
        events: list[str] = []
        if month in (1, 13):
            self.economy.sponsors.renew_season(
                month,
                self.state.clubs,
                self.rosters,
                set(self.pyramid.premier_ids),
                self.economy.stadiums.profiles,
            )
            self.economy.registration.register(
                month,
                self.state.clubs,
                self.rosters,
            )
            events.append("commercial sponsorship cycle renewed")
            events.append(
                f"squads registered under {self.economy.registration.policy_name}"
            )

        reserves = self.economy.registration.suspend_unregistered(self.rosters)
        results = self.base.advance_month(month)
        self.economy.registration.restore_and_advance_reserves(
            month,
            reserves,
            self.rosters,
            self.state.clubs,
            self.contracts.free_agents,
        )

        if month in (7, 19):
            self.economy.registration.register(
                month,
                self.state.clubs,
                self.rosters,
            )
            events.append(
                f"post-market squads registered under "
                f"{self.economy.registration.policy_name}"
            )

        self.economy.stadiums.settle_matches(
            month,
            results,
            self.state.clubs,
        )
        self.economy.stadiums.settle_month(
            month,
            self.state.clubs,
            self.pyramid.owners,
        )
        self.economy.sponsors.monitor_morality(month, self.state.clubs)
        self.economy.sponsors.pay_performance_bonuses(month, self.base)
        self.economy.insolvency.monitor(month, self.base)
        self.economy.lifecycle.settle_season(
            month,
            self.state,
            self.rosters,
            self.contracts.free_agents,
        )
        if month in (12, 24):
            events.append("retirements and academy graduation completed")
        if (
            self.economy.insolvency.history
            and self.economy.insolvency.history[-1].month == month
        ):
            events.append(
                "a failed club was replaced by a community phoenix club"
            )
        self.monthly_industry_events[month] = events
        return results
