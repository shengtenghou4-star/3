"""Runtime ordering safeguards for political careers and justice cases."""

from __future__ import annotations

from .patronage_justice import CareerJusticeHistory as _CareerJusticeCore


class CareerJusticeHistory(_CareerJusticeCore):
    """Career/justice history with same-month referral checkpoint recovery."""

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
