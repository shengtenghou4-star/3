"""Replayable scenario injections for constitutional football history.

Normal gameplay uses endogenous crisis checkpoints. Scenario designers and tests can inject
an explicit crisis; this wrapper records the injection itself so JSON replay remains exact.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .campaign import Strategy
from .constitutional import ConstitutionalLongTermCampaign, _clamp


SCENARIO_HISTORY_SAVE_VERSION = 3


class ReplayableConstitutionalHistory(ConstitutionalLongTermCampaign):
    """Constitutional history with deterministic external event injections."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        super().__init__(strategy=strategy, max_terms=max_terms)
        self._injected_crises: list[dict[str, Any]] = []

    def force_crisis(
        self,
        *,
        office: str = "廉洁与纪律专员",
        severity: float = 0.86,
        allegation: str = "审计文件显示利益输送与隐瞒关联交易",
        _record_injection: bool = True,
    ):
        if _record_injection:
            self._injected_crises.append(
                {
                    "global_month": self.global_month,
                    "term": self.term_index,
                    "local_month": self.local_month,
                    "office": office,
                    "severity": _clamp(severity),
                    "allegation": allegation,
                }
            )
        return super().force_crisis(
            office=office,
            severity=severity,
            allegation=allegation,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = SCENARIO_HISTORY_SAVE_VERSION
        payload["injected_crises"] = list(self._injected_crises)
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReplayableConstitutionalHistory":
        if data.get("format_version") != SCENARIO_HISTORY_SAVE_VERSION:
            raise ValueError("unsupported replayable scenario-history format")
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        target_month = int(data.get("global_month", 0))
        commands = list(data.get("decision_log", []))
        injections = list(data.get("injected_crises", []))
        command_index = 0
        injection_index = 0

        while (
            campaign.global_month < target_month
            or command_index < len(commands)
            or injection_index < len(injections)
        ):
            if injection_index < len(injections):
                injection = injections[injection_index]
                injection_month = int(injection["global_month"])
                if injection_month < campaign.global_month:
                    raise ValueError("scenario injection was not reachable during replay")
                if injection_month == campaign.global_month:
                    if campaign.current_decision is not None:
                        # The original run injected constitutional business ahead of an
                        # ordinary pending decision, which is supported by the live game.
                        pass
                    campaign.force_crisis(
                        office=injection["office"],
                        severity=float(injection["severity"]),
                        allegation=injection["allegation"],
                        _record_injection=True,
                    )
                    injection_index += 1
                    continue

            if campaign.current_decision is not None:
                if command_index >= len(commands):
                    if campaign.global_month >= target_month:
                        break
                    raise ValueError("save omits a decision required before target month")
                command = commands[command_index]
                if int(command["global_month"]) != campaign.global_month:
                    raise ValueError("save decision reached at a different month")
                if command["decision_id"] != campaign.current_decision.id:
                    raise ValueError("save replay reached a different decision")
                campaign.resolve_decision(command["option_id"])
                command_index += 1
                continue

            if campaign.global_month >= target_month:
                break
            campaign.advance(1, interactive=True)

        if command_index != len(commands):
            raise ValueError("save contains unreachable decisions")
        if injection_index != len(injections):
            raise ValueError("save contains unreachable scenario injections")
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("scenario-history replay fingerprint mismatch")
        return campaign

    @classmethod
    def from_json(cls, content: str) -> "ReplayableConstitutionalHistory":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "ReplayableConstitutionalHistory":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "injected_crises": self._injected_crises,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
