"""Deterministic club transfer market driven by finances and roster needs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import random

from .domain import Club
from .football import ClubRoster, Player


def _seed(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


class TransferPolicy(str, Enum):
    HOMEGROWN_PRIORITY = "homegrown_priority"
    OPEN_MARKET = "open_market"
    FINANCIAL_CONTROL = "financial_control"


@dataclass(frozen=True, slots=True)
class TransferRecord:
    month: int
    player_id: str
    player_name: str
    position: str
    age: int
    ability: float
    potential: float
    seller_id: str
    seller_name: str
    buyer_id: str
    buyer_name: str
    fee: float
    old_wage: float
    new_wage: float
    policy: str


class TransferMarket:
    def __init__(
        self,
        policy: TransferPolicy = TransferPolicy.FINANCIAL_CONTROL,
        seed: int = 9090,
    ) -> None:
        self.policy = policy
        self.seed = seed
        self.history: list[TransferRecord] = []

    def run_window(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        max_transfers: int = 5,
    ) -> list[TransferRecord]:
        rng = random.Random(self.seed + _seed(f"window:{month}:{self.policy.value}"))
        completed: list[TransferRecord] = []
        blocked_pairs: set[tuple[str, str]] = set()

        for _ in range(max_transfers * 3):
            if len(completed) >= max_transfers:
                break
            seller_id = self._choose_seller(clubs, rosters, rng)
            buyer_id = self._choose_buyer(clubs, rosters, seller_id, rng)
            if not seller_id or not buyer_id:
                break
            pair = (seller_id, buyer_id)
            if pair in blocked_pairs:
                continue
            blocked_pairs.add(pair)

            seller = clubs[seller_id]
            buyer = clubs[buyer_id]
            player = self._choose_player(
                rosters[seller_id], rosters[buyer_id], rng
            )
            if player is None:
                continue
            fee = self._valuation(player, seller, buyer)
            if buyer.cash < fee * 1.20:
                continue
            if len(rosters[seller_id].players) <= 20:
                continue

            old_wage = player.monthly_wage
            wage_multiplier = {
                TransferPolicy.HOMEGROWN_PRIORITY: 1.08,
                TransferPolicy.OPEN_MARKET: 1.22,
                TransferPolicy.FINANCIAL_CONTROL: 1.03,
            }[self.policy]
            new_wage = old_wage * wage_multiplier

            rosters[seller_id].players.remove(player)
            rosters[buyer_id].players.append(player)
            seller.cash += fee
            buyer.cash -= fee
            seller.monthly_wage_bill = max(
                0.0, seller.monthly_wage_bill - old_wage
            )
            buyer.monthly_wage_bill += new_wage
            player.monthly_wage = new_wage
            player.contract_months = max(24, player.contract_months)
            player.morale = min(100.0, player.morale + 6.0)

            record = TransferRecord(
                month=month,
                player_id=player.id,
                player_name=player.name,
                position=player.position,
                age=player.age,
                ability=player.ability,
                potential=player.potential,
                seller_id=seller.id,
                seller_name=seller.name,
                buyer_id=buyer.id,
                buyer_name=buyer.name,
                fee=fee,
                old_wage=old_wage,
                new_wage=new_wage,
                policy=self.policy.value,
            )
            self.history.append(record)
            completed.append(record)

        return completed

    def _choose_seller(
        self,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        rng: random.Random,
    ) -> str | None:
        candidates = [
            club
            for club in clubs.values()
            if club.license_status != "excluded"
            and len(rosters[club.id].players) > 20
        ]
        if not candidates:
            return None
        scored = []
        for club in candidates:
            pressure = (
                1.25 * (1.0 - club.financial_health)
                + 0.55 * (club.monthly_wage_bill / max(club.monthly_revenue, 1.0))
                + 0.12 * rng.random()
            )
            scored.append((pressure, club.id))
        return max(scored)[1]

    def _choose_buyer(
        self,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        seller_id: str,
        rng: random.Random,
    ) -> str | None:
        candidates = [
            club
            for club in clubs.values()
            if club.id != seller_id
            and club.license_status != "excluded"
            and club.cash > 500_000
        ]
        if not candidates:
            return None
        scored = []
        for club in candidates:
            ambition = (
                club.owner_patience
                + 0.50 * club.supporter_base
                + max(0.0, 67.0 - rosters[club.id].overall) / 22.0
                + 0.08 * rng.random()
            )
            if self.policy is TransferPolicy.FINANCIAL_CONTROL:
                ambition *= 0.70 + 0.30 * club.financial_health
            scored.append((ambition, club.id))
        return max(scored)[1]

    def _choose_player(
        self,
        seller: ClubRoster,
        buyer: ClubRoster,
        rng: random.Random,
    ) -> Player | None:
        buyer_lines = {
            "GK": buyer.goalkeeper,
            "DEF": buyer.defense,
            "MID": buyer.midfield,
            "ATT": buyer.attack,
        }
        candidates = [
            player
            for player in seller.players
            if player.injury_months == 0 and player.contract_months > 2
        ]
        if not candidates:
            return None

        def score(player: Player) -> float:
            need = max(0.0, 72.0 - buyer_lines[player.position])
            base = player.ability + 0.30 * player.potential + 0.18 * need
            if self.policy is TransferPolicy.HOMEGROWN_PRIORITY:
                base += 13.0 if player.homegrown and player.age <= 23 else -5.0
            elif self.policy is TransferPolicy.OPEN_MARKET:
                base += 9.0 if not player.homegrown else 1.0
                base += 0.35 * max(0.0, player.ability - 62.0)
            else:
                base += 8.0 if player.contract_months <= 12 else 0.0
                base -= player.monthly_wage / 25_000.0
            return base + rng.uniform(-1.5, 1.5)

        return max(candidates, key=score)

    def _valuation(self, player: Player, seller: Club, buyer: Club) -> float:
        ability_value = max(0.0, player.ability - 38.0) ** 2 * 2_700.0
        potential_value = max(0.0, player.potential - player.ability) * 52_000.0
        contract_value = min(player.contract_months, 36) * 13_000.0
        age_factor = (
            1.18 if player.age <= 23 else 1.0 if player.age <= 29 else 0.72
        )
        policy_factor = {
            TransferPolicy.HOMEGROWN_PRIORITY: (
                1.22 if player.homegrown and player.age <= 23 else 0.90
            ),
            TransferPolicy.OPEN_MARKET: 1.14 if not player.homegrown else 1.0,
            TransferPolicy.FINANCIAL_CONTROL: 0.88,
        }[self.policy]
        bargaining = 0.92 + 0.10 * seller.owner_patience + 0.06 * buyer.supporter_base
        return max(
            180_000.0,
            (ability_value + potential_value + contract_value)
            * age_factor
            * policy_factor
            * bargaining,
        )
