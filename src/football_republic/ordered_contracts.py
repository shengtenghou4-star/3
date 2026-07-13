"""Policy-ordered registration windows for the deep campaign."""

from __future__ import annotations

from .advanced_ecosystem import ActiveLoan, ContractMarket, LoanRecord
from .domain import Club
from .football import ClubRoster, Player


class OrderedContractMarket(ContractMarket):
    """Run club registrations after the president has set transfer policy."""

    def advance_month(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
        second_ids: set[str],
    ) -> None:
        self._return_due_loans(month, clubs, rosters)
        self._renew_expiring(month, clubs, rosters)
        self._release_expired(month, clubs, rosters)
        if month in (7, 19):
            self._sign_free_agents(month, clubs, rosters)
            self._arrange_loans_ordered(
                month,
                clubs,
                rosters,
                premier_ids,
                second_ids,
            )

    def _arrange_loans_ordered(
        self,
        month: int,
        clubs: dict[str, Club],
        rosters: dict[str, ClubRoster],
        premier_ids: set[str],
        second_ids: set[str],
    ) -> None:
        return_month = 12 if month == 7 else 24
        available: list[tuple[Player, str]] = []
        for parent_id in premier_ids:
            roster = rosters[parent_id]
            if len(roster.players) <= 20:
                continue
            top_ids = {
                player.id
                for player in sorted(
                    roster.players,
                    key=lambda item: item.match_readiness,
                    reverse=True,
                )[:18]
            }
            for player in roster.players:
                if (
                    player.age <= 22
                    and player.id not in top_ids
                    and player.id not in self.active_loans
                    and player.contract_months > return_month - month
                ):
                    available.append((player, parent_id))

        borrowers = sorted(second_ids, key=lambda club_id: rosters[club_id].overall)
        for borrower_id in borrowers:
            if not available:
                break
            borrower = rosters[borrower_id]
            if len(borrower.players) >= 27:
                continue
            weakest_position = min(
                ("GK", "DEF", "MID", "ATT"),
                key=lambda position: borrower.line_rating(
                    position,
                    {"GK": 1, "DEF": 4, "MID": 3, "ATT": 3}[position],
                ),
            )
            candidates = [
                item
                for item in available
                if item[0].position == weakest_position
                and len(rosters[item[1]].players) > 20
            ]
            if not candidates:
                continue
            player, parent_id = max(candidates, key=lambda item: item[0].potential)
            parent = rosters[parent_id]
            parent.players.remove(player)
            borrower.players.append(player)
            wage_share = 0.50
            clubs[parent_id].monthly_wage_bill -= player.monthly_wage * wage_share
            clubs[borrower_id].monthly_wage_bill += player.monthly_wage * wage_share
            self.active_loans[player.id] = ActiveLoan(
                player,
                parent_id,
                borrower_id,
                return_month,
                wage_share,
            )
            self.loan_history.append(
                LoanRecord(
                    month,
                    return_month,
                    player.id,
                    player.name,
                    parent_id,
                    clubs[parent_id].name,
                    borrower_id,
                    clubs[borrower_id].name,
                    wage_share,
                    "active",
                )
            )
            available.remove((player, parent_id))
