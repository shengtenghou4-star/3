"""Runtime safeguards for executive implementation."""

from __future__ import annotations

from .executive_followup import ExecutiveFollowupRuntime


class ExecutiveGovernmentRuntime(ExecutiveFollowupRuntime):
    """Use the latest same-month report after a chairman changes an assignment."""

    def visible_reports(self, *, mandate_id: str | None = None):
        reports = self.reports
        if mandate_id is not None:
            reports = [item for item in reports if item.mandate_id == mandate_id]
        latest = {}
        for report in reports:
            key = (report.mandate_id, report.office)
            current = latest.get(key)
            if current is None or report.global_month >= current.global_month:
                latest[key] = report
        return tuple(
            sorted(
                latest.values(),
                key=lambda item: (
                    item.mandate_id,
                    item.urgency != "紧急",
                    item.office,
                ),
            )
        )

    @classmethod
    def from_dict(cls, data):
        base = ExecutiveFollowupRuntime.from_dict(data)
        runtime = cls()
        runtime.mandates = base.mandates
        runtime.reports = base.reports
        runtime.press_sessions = base.press_sessions
        runtime._processed_months = base._processed_months
        runtime._report_keys = base._report_keys
        return runtime
