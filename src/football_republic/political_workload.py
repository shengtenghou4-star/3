"""Workload rules that can be changed through collective bargaining."""

from __future__ import annotations

import random

from .advanced_ecosystem import WorkloadManager, WorkloadReport, _clamp, _seed
from .domain import Club
from .ecosystem import NationalSquad
from .football import ClubRoster, MatchResult


class PolicyWorkloadManager(WorkloadManager):
    """A workload manager whose safety parameters are controlled by policy."""

    def __init__(self, seed: int = 8800) -> None:
        super().__init__(seed=seed)
        self.congestion_multiplier = 1.0
        self.international_release_cost = 4.5
        self.injury_multiplier = 1.0

    def settle_month(
        self,
        month: int,
        results: list[MatchResult],
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> list[WorkloadReport]:
        match_counts = {club_id: 0 for club_id in clubs}
        away_travel = {club_id: 0 for club_id in clubs}
        for result in results:
            if result.home_id in match_counts:
                match_counts[result.home_id] += 1
            if result.away_id in match_counts:
                match_counts[result.away_id] += 1
                if "Continental" in result.competition:
                    away_travel[result.away_id] += 1
        reports: list[WorkloadReport] = []
        for club_id, matches in match_counts.items():
            if matches == 0:
                continue
            raw_extra = max(0, matches - 2) * 2.8 + away_travel[club_id] * 1.8
            extra = raw_extra * self.congestion_multiplier
            injuries = 0
            roster = rosters[club_id]
            rng = random.Random(self.seed + _seed(f"load:{month}:{club_id}"))
            if extra > 0:
                for player in roster.players:
                    if player.appearances <= 0 or player.injury_months > 0:
                        continue
                    player.fitness = _clamp(player.fitness - extra, 20.0, 100.0)
                    risk = self.injury_multiplier * (
                        0.004 * max(0, matches - 2)
                        + 0.003 * away_travel[club_id]
                    )
                    if rng.random() < risk:
                        player.injury_months = max(
                            player.injury_months,
                            rng.choice((1, 1, 2)),
                        )
                        injuries += 1
                roster.tactical_cohesion = _clamp(
                    roster.tactical_cohesion
                    - 0.006 * max(0, matches - 3) * self.congestion_multiplier,
                    0.0,
                    1.0,
                )
            level = (
                "extreme"
                if matches >= 6
                else "high"
                if matches >= 4
                else "normal"
            )
            report = WorkloadReport(
                month,
                club_id,
                clubs[club_id].name,
                matches,
                away_travel[club_id],
                extra,
                injuries,
                level,
            )
            reports.append(report)
            self.history.append(report)
        return reports

    def settle_international_release(
        self,
        month: int,
        squad: NationalSquad,
        rosters: dict[str, ClubRoster],
    ) -> None:
        lookup = {
            player.id: player
            for roster in rosters.values()
            for player in roster.players
        }
        rng = random.Random(self.seed + _seed(f"international:{month}"))
        for member in squad.members:
            player = lookup.get(member.player_id)
            if player is None:
                continue
            player.fitness = _clamp(
                player.fitness - self.international_release_cost,
                20.0,
                100.0,
            )
            if rng.random() < 0.008 * self.injury_multiplier:
                player.injury_months = max(player.injury_months, 1)
