"""Strict squad registration that enforces policy without loopholes."""

from __future__ import annotations

import hashlib
import random

from .domain import Club
from .football import ClubRoster, FIRST_NAMES, LAST_NAMES, Player
from .generational_economy import RegistrationAudit, RegistrationSystem, _clamp


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


class StrictRegistrationSystem(RegistrationSystem):
    """Register a playable squad while enforcing foreign and homegrown limits."""

    def register(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id, roster in rosters.items():
            club = clubs[club_id]
            self._promote_emergency_reserves(month, club, roster)
            players = list(roster.players)
            selected: list[Player] = []

            def foreign_count() -> int:
                return sum(
                    player.nationality != "Longhua" for player in selected
                )

            def add(player: Player) -> bool:
                if player in selected or len(selected) >= self.squad_limit:
                    return False
                if (
                    player.nationality != "Longhua"
                    and foreign_count() >= self.foreign_limit
                ):
                    return False
                selected.append(player)
                return True

            goalkeepers = sorted(
                (player for player in players if player.position == "GK"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in goalkeepers:
                if sum(item.position == "GK" for item in selected) >= 2:
                    break
                add(player)

            homegrown = sorted(
                (player for player in players if player.homegrown),
                key=lambda player: (player.match_readiness, player.potential),
                reverse=True,
            )
            for player in homegrown[: self.homegrown_minimum]:
                add(player)

            under_23 = sorted(
                (player for player in players if player.age <= 23),
                key=lambda player: (player.potential, player.match_readiness),
                reverse=True,
            )
            for player in under_23:
                if sum(item.age <= 23 for item in selected) >= 3:
                    break
                add(player)

            foreign = sorted(
                (player for player in players if player.nationality != "Longhua"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in foreign:
                if foreign_count() >= self.foreign_limit:
                    break
                add(player)

            domestic = sorted(
                (player for player in players if player.nationality == "Longhua"),
                key=lambda player: player.match_readiness,
                reverse=True,
            )
            for player in domestic:
                add(player)
            for player in sorted(
                players,
                key=lambda player: player.match_readiness,
                reverse=True,
            ):
                add(player)

            if len(selected) < 18:
                raise RuntimeError(
                    f"{club.name} cannot register the minimum 18 players "
                    f"after emergency reserve promotion"
                )

            selected_ids = {player.id for player in selected}
            self.registered_ids[club_id] = selected_ids
            registered_foreign = foreign_count()
            registered_homegrown = sum(player.homegrown for player in selected)
            missing_homegrown = max(
                0,
                self.homegrown_minimum - registered_homegrown,
            )
            fine = missing_homegrown * 140_000.0
            if fine > 0:
                if club.cash >= fine:
                    club.cash -= fine
                else:
                    club.debt += fine - club.cash
                    club.cash = 0.0
                club.licensing_compliance = _clamp(
                    club.licensing_compliance - 0.015 * missing_homegrown,
                    0.0,
                    1.0,
                )
            unregistered = tuple(
                player.name
                for player in players
                if player.id not in selected_ids
            )
            self.audit_history.append(
                RegistrationAudit(
                    month,
                    club_id,
                    club.name,
                    self.squad_limit,
                    self.foreign_limit,
                    self.homegrown_minimum,
                    len(selected),
                    registered_foreign,
                    registered_homegrown,
                    unregistered,
                    fine,
                    missing_homegrown == 0,
                )
            )

    def _promote_emergency_reserves(
        self,
        month: int,
        club: Club,
        roster: ClubRoster,
    ) -> None:
        domestic_count = sum(
            player.nationality == "Longhua" for player in roster.players
        )
        foreign_count = len(roster.players) - domestic_count
        eligible_capacity = domestic_count + min(
            foreign_count,
            self.foreign_limit,
        )
        shortage = max(0, 18 - eligible_capacity)
        if shortage == 0:
            return

        existing_ids = {player.id for player in roster.players}
        target_counts = {"GK": 3, "DEF": 8, "MID": 8, "ATT": 6}
        for index in range(shortage):
            position = min(
                target_counts,
                key=lambda item: sum(
                    player.position == item for player in roster.players
                )
                / target_counts[item],
            )
            rng = random.Random(
                _seed(f"emergency:{club.id}:{month}:{index}")
            )
            player_id = f"{club.id}-reserve-m{month}-{index + 1:02d}"
            suffix = 1
            while player_id in existing_ids:
                suffix += 1
                player_id = (
                    f"{club.id}-reserve-m{month}-{index + 1:02d}-{suffix}"
                )
            ability = _clamp(
                31.0
                + 14.0 * club.academy_quality
                + rng.uniform(-2.0, 3.0),
                30.0,
                49.0,
            )
            potential = _clamp(
                ability
                + 10.0
                + 12.0 * club.academy_quality
                + rng.uniform(0.0, 6.0),
                ability + 5.0,
                78.0,
            )
            wage = 3_000.0 + ability * 70.0
            player = Player(
                id=player_id,
                name=(
                    f"{rng.choice(FIRST_NAMES[:10])} "
                    f"{rng.choice(LAST_NAMES[:10])}"
                ),
                position=position,
                age=rng.choice((18, 19, 20)),
                ability=ability,
                potential=potential,
                fitness=rng.uniform(76.0, 94.0),
                morale=rng.uniform(52.0, 68.0),
                monthly_wage=wage,
                contract_months=18,
                homegrown=True,
                nationality="Longhua",
            )
            roster.players.append(player)
            club.monthly_wage_bill += wage
            registration_cost = 18_000.0
            if club.cash >= registration_cost:
                club.cash -= registration_cost
            else:
                club.debt += registration_cost - club.cash
                club.cash = 0.0
            existing_ids.add(player_id)
