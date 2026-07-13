"""Runtime safeguards for coalition elections.

Caretaker administrations cannot use a political vacuum for major discretionary
reforms. Ordinary pending business is resolved through the lowest-change balanced
continuity option so time can reach the snap convention without resetting or
freezing the football calendar.
"""

from __future__ import annotations

from .campaign import Strategy, _AUTO_CHOICES
from .coalition_elections import CoalitionElectionHistory as _CoalitionElectionCore
from .constitutional import ConstitutionalEvent
from .governance import DecisionRecord


class CoalitionElectionHistory(_CoalitionElectionCore):
    """Playable coalition history with caretaker and record-shape safeguards."""

    def advance(self, months: int = 1, *, interactive: bool = False) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        remaining = months
        while remaining > 0 and not self.finished:
            if self._caretaker_must_resolve_continuity():
                self._resolve_caretaker_continuity()
                continue
            before = self.global_month
            super().advance(1, interactive=interactive)
            elapsed = self.global_month - before
            if elapsed == 0:
                # A nomination, bargaining round or other playable decision has opened.
                break
            remaining -= elapsed

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        caretaker_continuity = (
            self.caretaker_active
            and decision is not None
            and not self._pending_election
            and not self._pending_coalition
            and not decision.id.startswith("constitutional_crisis_")
        )
        record = super().resolve_decision(option_id)
        if caretaker_continuity and decision is not None:
            self.constitutional_history.append(
                ConstitutionalEvent(
                    self.global_month,
                    self.local_month,
                    self.term_index,
                    "caretaker continuity decision",
                    f"看守政府以最低变更原则处理：{decision.title}",
                    0.22,
                    (
                        "The caretaker could not negotiate a new political mandate.",
                        "A balanced continuity option kept competitions and administration moving.",
                    ),
                )
            )
        return record

    def _caretaker_must_resolve_continuity(self) -> bool:
        decision = self.current_decision
        if not self.caretaker_active or decision is None:
            return False
        if self._pending_election or self._pending_coalition:
            return False
        if decision.id.startswith("constitutional_crisis_"):
            return False
        return True

    def _resolve_caretaker_continuity(self) -> None:
        decision = self.current_decision
        if decision is None:
            return
        if decision.id.startswith("agenda_"):
            option_id = self.current_campaign.politics.auto_choice(
                decision.id,
                Strategy.BALANCED.value,
            )
        else:
            option_id = _AUTO_CHOICES[Strategy.BALANCED][decision.id]
        self.resolve_decision(option_id)

    def _install_snap_winner(self, candidate, agreement) -> None:
        super()._install_snap_winner(candidate, agreement)
        # Candidate IDs describe a convention ticket; the installed president receives
        # a constitutional office ID. Keep the agreement tied to the actual office-holder.
        agreement.president_id = self.current_president.id
        agreement.president_name = self.current_president.name

    def _resolve_election_decision(self, decision, option_id: str) -> DecisionRecord:
        record = super()._resolve_election_decision(decision, option_id)
        if isinstance(record.effects, str):
            return DecisionRecord(
                decision_id=record.decision_id,
                month=record.month,
                title=record.title,
                option_id=record.option_id,
                option_title=record.option_title,
                effects=(record.effects,),
            )
        return record
