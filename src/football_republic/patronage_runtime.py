"""Runtime ordering safeguards for political careers and justice cases."""

from __future__ import annotations

from .long_term import PresidentProfile
from .patronage_justice import CareerJusticeHistory as _CareerJusticeCore


class CareerJusticeHistory(_CareerJusticeCore):
    """Career/justice history with ordering and office-transition safeguards."""

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        was_justice = bool(
            decision is not None
            and self._pending_justice
            and decision.id == self._pending_justice[0].id
        )
        record = super().resolve_decision(option_id)
        if not was_justice and self.current_decision is None:
            # Months 6/12/18/24 already contain ordinary presidential business.
            # Re-run the checkpoint after that business is resolved so credible
            # evidence is not silently skipped for an entire term.
            self._maybe_open_case()
        return record

    def _start_caretaker(self, reason: str) -> None:
        outgoing_name = self.current_president.name.replace("（看守）", "")
        super()._start_caretaker(reason)
        self._close_presidential_career(outgoing_name, reason)
        caretaker_name = self.current_president.name.replace("（看守）", "")
        person = next(
            (item for item in self.people.values() if item.name == caretaker_name),
            None,
        )
        if person is not None:
            self._post_person(
                person,
                "国家足球协会",
                "代理主席",
                reason,
                "caretaker accession",
            )

    def _install_snap_winner(self, candidate, agreement) -> None:
        caretaker_name = self.current_president.name.replace("（看守）", "")
        super()._install_snap_winner(candidate, agreement)
        self._close_presidential_career(caretaker_name, "snap election completed")

    def _rollover(self, bundle, president: PresidentProfile) -> None:
        outgoing_name = self.current_president.name.replace("（看守）", "")
        changed = president.name != self.current_president.name
        if changed:
            self._close_presidential_career(outgoing_name, "scheduled succession")
        super()._rollover(bundle, president)

    def _close_presidential_career(self, name: str, reason: str) -> None:
        person = next(
            (
                item for item in self.people.values()
                if item.name == name and item.status == "president"
            ),
            None,
        )
        if person is None:
            return
        self._post_person(
            person,
            "国家足球治理委员会",
            "前主席",
            reason,
            "left presidency",
        )
