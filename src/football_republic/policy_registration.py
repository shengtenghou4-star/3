"""Strict squad registration that enforces policy without loopholes."""

from __future__ import annotations

from .domain import Club
from .football import ClubRoster, Player
from .generational_economy import RegistrationAudit, RegistrationSystem, _clamp


class StrictRegistrationSystem(RegistrationSystem):
    """Register a playable squad while enforcing foreign and homegrown limits."""

    def register(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
    ) -> None:
        for club_id, roster in rosters.items():
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
                    f"{clubs[club_id].name} cannot register the minimum 18 players "
                    f"under foreign limit {self.foreign_limit}"
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
            club = clubs[club_id]
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
