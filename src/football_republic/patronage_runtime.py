"""Runtime ordering safeguards for political careers, justice and office actions."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any

from .campaign import Strategy
from .long_term import PresidentProfile
from .patronage_justice import (
    CAREER_JUSTICE_SAVE_VERSION,
    CareerJusticeHistory as _CareerJusticeCore,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class CareerJusticeHistory(_CareerJusticeCore):
    """Career/justice history with ordered, replayable external office effects."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        self._external_actions: list[dict[str, Any]] = []
        super().__init__(strategy=strategy, max_terms=max_terms)

    @property
    def external_actions(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._external_actions)

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

    def apply_external_action(
        self,
        action_type: str,
        payload: dict[str, Any],
        *,
        record: bool = True,
    ) -> dict[str, Any]:
        """Apply a deterministic office action and optionally add it to replay history."""
        entry = {
            "sequence": len(self._external_actions),
            "global_month": self.global_month,
            "decision_count": len(self._decision_log),
            "action_type": action_type,
            "payload": json.loads(json.dumps(payload, ensure_ascii=False)),
        }
        if record:
            self._external_actions.append(entry)
        self._apply_external_effects(action_type, entry["payload"])
        return entry

    def _replay_external_action(self, entry: dict[str, Any]) -> None:
        normalized = {
            "sequence": int(entry["sequence"]),
            "global_month": int(entry["global_month"]),
            "decision_count": int(entry["decision_count"]),
            "action_type": str(entry["action_type"]),
            "payload": json.loads(json.dumps(entry["payload"], ensure_ascii=False)),
        }
        self._external_actions.append(normalized)
        self._apply_external_effects(
            normalized["action_type"],
            normalized["payload"],
        )

    def _apply_external_effects(
        self,
        action_type: str,
        payload: dict[str, Any],
    ) -> None:
        state = self.current_campaign.engine.state
        politics = self.current_campaign.politics

        for delta in payload.get("stakeholder_deltas", []):
            actor = politics.stakeholders.get(delta["actor_id"])
            if actor is None:
                continue
            actor.support = _clamp(actor.support + float(delta.get("support", 0.0)))
            actor.trust = _clamp(actor.trust + float(delta.get("trust", 0.0)))
            actor.patience = _clamp(actor.patience + float(delta.get("patience", 0.0)))
            actor.mobilization = _clamp(
                actor.mobilization + float(delta.get("mobilization", 0.0))
            )
            if delta.get("contact", False):
                actor.last_contact_month = self.local_month
            note = str(delta.get("note", action_type))
            actor.memory.append(
                f"M{self.local_month}: presidential office — {note}; "
                f"support {actor.support:.2f}; trust {actor.trust:.2f}"
            )
            actor.memory = actor.memory[-10:]

        bounded_state_fields = {
            "fan_trust",
            "integrity_reputation",
            "political_capital",
            "league_financial_health",
            "parent_support",
        }
        for field, raw_delta in payload.get("state_deltas", {}).items():
            if not hasattr(state, field):
                continue
            value = getattr(state, field) + float(raw_delta)
            if field in bounded_state_fields:
                value = _clamp(value)
            setattr(state, field, value)

        for delta in payload.get("official_deltas", []):
            official = None
            if "office" in delta:
                official = self.cabinet.get(delta["office"])
            elif "official_id" in delta:
                official = next(
                    (
                        item for item in self.cabinet.values()
                        if item.id == delta["official_id"]
                    ),
                    None,
                )
            if official is None:
                continue
            official.loyalty = _clamp(
                official.loyalty + float(delta.get("loyalty", 0.0))
            )
            official.integrity = _clamp(
                official.integrity + float(delta.get("integrity", 0.0))
            )
            official.network_power = _clamp(
                official.network_power + float(delta.get("network_power", 0.0))
            )
            official.scandal_points = _clamp(
                official.scandal_points + float(delta.get("scandal_points", 0.0))
            )
            person = self.people.get(official.id)
            if person is not None:
                person.loyalty = official.loyalty
                person.integrity = official.integrity
                person.network_power = official.network_power
                person.exposure = _clamp(
                    person.exposure + float(delta.get("exposure", 0.0))
                )

        audit_note = payload.get("audit_note")
        if audit_note:
            self.current_campaign.engine.audit_log.append(
                f"G{self.global_month}: office — {audit_note}"
            )

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
            person.status = "president"

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

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["external_actions"] = list(self._external_actions)
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CareerJusticeHistory":
        if data.get("format_version") != CAREER_JUSTICE_SAVE_VERSION:
            raise ValueError("unsupported career-justice history format")
        campaign = cls(
            strategy=Strategy(data["initial_strategy"]),
            max_terms=int(data["max_terms"]),
        )
        target_month = int(data.get("global_month", 0))
        commands = list(data.get("decision_log", []))
        injections = list(data.get("injected_crises", []))
        actions = sorted(
            list(data.get("external_actions", [])),
            key=lambda item: int(item["sequence"]),
        )
        command_index = 0
        injection_index = 0
        action_index = 0

        while (
            campaign.global_month < target_month
            or command_index < len(commands)
            or injection_index < len(injections)
            or action_index < len(actions)
        ):
            if injection_index < len(injections):
                injection = injections[injection_index]
                injection_month = int(injection["global_month"])
                if injection_month < campaign.global_month:
                    raise ValueError("scenario injection was not reachable during replay")
                if injection_month == campaign.global_month:
                    campaign.force_crisis(
                        office=injection["office"],
                        severity=float(injection["severity"]),
                        allegation=injection["allegation"],
                        _record_injection=True,
                    )
                    injection_index += 1
                    continue

            if action_index < len(actions):
                action = actions[action_index]
                action_month = int(action["global_month"])
                expected_decisions = int(action["decision_count"])
                if action_month < campaign.global_month:
                    raise ValueError("office action was not reachable during replay")
                if (
                    action_month == campaign.global_month
                    and expected_decisions == command_index
                ):
                    campaign._replay_external_action(action)
                    action_index += 1
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
                if action_index < len(actions):
                    action = actions[action_index]
                    if int(action["global_month"]) == campaign.global_month:
                        raise ValueError(
                            "office action ordering did not match the decision timeline"
                        )
                break
            campaign.advance(1, interactive=True)

        if command_index != len(commands):
            raise ValueError("save contains unreachable career-justice decisions")
        if injection_index != len(injections):
            raise ValueError("save contains unreachable scenario injections")
        if action_index != len(actions):
            raise ValueError("save contains unreachable presidential-office actions")
        expected = data.get("fingerprint")
        if expected and campaign.fingerprint() != expected:
            raise ValueError("career-justice replay fingerprint mismatch")
        return campaign

    def fingerprint(self) -> str:
        payload = {
            "base": super().fingerprint(),
            "external_actions": self._external_actions,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
