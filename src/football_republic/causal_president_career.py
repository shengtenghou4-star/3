"""Fixed-player president career with persistent office behaviour."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .campaign import Strategy
from .office_causality import OfficeCausality
from .president_career import PresidentCareerGame


CAUSAL_PRESIDENT_SAVE_VERSION = 7


class CausalPresidentCareerGame(PresidentCareerGame):
    """The default president career with meetings, statements, filtering and leaks."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        super().__init__(strategy=strategy, max_terms=max_terms)
        self.office = OfficeCausality()
        self.office.bootstrap(self)

    def advance(self, months: int = 1, *, interactive: bool = True) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            before = self.global_month
            super().advance(1, interactive=interactive)
            if self.global_month > before:
                self.office.advance_month(self)
            if interactive and self.current_decision is not None:
                break

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no presidential decision pending")
        option = next(item for item in decision.options if item.id == option_id)
        record = super().resolve_decision(option_id)
        self.office.note_formal_decision(
            self,
            decision_id=decision.id,
            option_id=option_id,
            option_title=option.title,
        )
        return record

    def observe(self, months: int = 1) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            before = self.global_month
            super().observe(1)
            if self.global_month > before:
                self.office.advance_month(self)
            if self.history_finished:
                break

    def record_meeting(
        self,
        *,
        meeting_id: str,
        visitor: str,
        institution: str,
        subject: str,
        choice: str,
        sensitivity: str = "normal",
    ):
        if not self.can_act:
            raise RuntimeError("successor-government meetings are not controlled by the player")
        return self.office.record_meeting(
            self,
            meeting_id=meeting_id,
            visitor=visitor,
            institution=institution,
            subject=subject,
            choice=choice,
            sensitivity=sensitivity,
        )

    def answer_media(
        self,
        *,
        clipping_id: str,
        outlet: str,
        question: str,
        answer_style: str,
        topic: str,
    ):
        if not self.can_act:
            raise RuntimeError("successor-government media answers are not controlled by the player")
        return self.office.record_media_answer(
            self,
            clipping_id=clipping_id,
            outlet=outlet,
            question=question,
            answer_style=answer_style,
            topic=topic,
        )

    def visible_office_reports(self):
        return self.office.visible_reports(self.global_month)

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = CAUSAL_PRESIDENT_SAVE_VERSION
        payload["base_fingerprint"] = PresidentCareerGame.fingerprint(self)
        payload["office"] = self.office.to_dict()
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CausalPresidentCareerGame":
        if data.get("format_version") != CAUSAL_PRESIDENT_SAVE_VERSION:
            raise ValueError("unsupported causal-president save format")
        base_payload = dict(data)
        base_payload["format_version"] = 6
        base_payload["fingerprint"] = data.get("base_fingerprint")
        base_payload.pop("base_fingerprint", None)
        base_payload.pop("office", None)
        base = PresidentCareerGame.from_dict(base_payload)
        game = cls.__new__(cls)
        game.__dict__.update(base.__dict__)
        game.office = OfficeCausality.from_dict(data["office"])
        expected = data.get("fingerprint")
        if expected and game.fingerprint() != expected:
            raise ValueError("causal-president replay fingerprint mismatch")
        return game

    @classmethod
    def from_json(cls, content: str) -> "CausalPresidentCareerGame":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    def fingerprint(self) -> str:
        payload = {
            "base": PresidentCareerGame.fingerprint(self),
            "office": self.office.fingerprint(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
