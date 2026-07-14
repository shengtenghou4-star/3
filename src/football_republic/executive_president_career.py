"""Fixed-player career with executive government, adaptive time and matchday command."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import adaptive_time as _adaptive_time_module
from .adaptive_time import AdaptiveCalendar, TimeAdvanceResult, TimeRecommendation
from .adaptive_time_significance import install_into as _install_time_significance
from .campaign import Strategy
from .causal_president_career import (
    CAUSAL_PRESIDENT_SAVE_VERSION,
    CausalPresidentCareerGame,
)
from .executive_runtime import ExecutiveGovernmentRuntime
from .matchday_time_integration import install_into as _install_matchday_time
from .national_team_command import NationalTeamCommandRuntime


_install_time_significance(_adaptive_time_module)
_install_matchday_time(_adaptive_time_module)

EXECUTIVE_PRESIDENT_SAVE_VERSION = 10
LEGACY_TIME_SAVE_VERSION = 9
LEGACY_EXECUTIVE_SAVE_VERSION = 8


class ExecutivePresidentCareerGame(CausalPresidentCareerGame):
    """Default game: one chairman governs, assigns, supervises and answers publicly."""

    def __init__(
        self,
        strategy: Strategy = Strategy.BALANCED,
        *,
        max_terms: int = 10,
    ) -> None:
        super().__init__(strategy=strategy, max_terms=max_terms)
        self.executive = ExecutiveGovernmentRuntime()
        self.calendar = AdaptiveCalendar.from_world_month(self.global_month)
        self.matchday = NationalTeamCommandRuntime()

    def advance(self, months: int = 1, *, interactive: bool = True) -> None:
        """Advance authoritative monthly settlements.

        The national-team command layer can add a temporary one-match readiness modifier.
        It is removed after the result so logistics cannot permanently inflate national
        strength. Player-facing controls should normally call :meth:`advance_time`.
        """
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            before_global = self.global_month
            target_local_month = self.local_month + 1
            state = self.current_campaign.engine.state
            base_strength = float(state.national_team_strength)
            modifier = 0.0
            if hasattr(self, "matchday"):
                self.matchday.sync(self)
                modifier = self.matchday.prepare_month(self, target_local_month)
                state.national_team_strength = max(
                    20.0,
                    min(95.0, base_strength + modifier),
                )
            super().advance(1, interactive=interactive)
            if self.global_month > before_global:
                self.executive.advance_month(self)
                if hasattr(self, "matchday"):
                    self.matchday.settle_month(
                        self,
                        target_local_month,
                        base_strength,
                    )
                if hasattr(self, "calendar"):
                    self.calendar.sync_to_world(self.global_month)
            elif modifier:
                state.national_team_strength = base_strength
                active = self.matchday.active_window
                if active is not None:
                    active.temporary_modifier_applied = 0.0
            if interactive and self.current_decision is not None:
                break

    def advance_time(self, mode: str = "adaptive") -> TimeAdvanceResult:
        if not self.can_act:
            raise RuntimeError("the player's presidential career has ended")
        self.matchday.sync(self)
        return self.calendar.advance(self, mode=mode)

    def time_recommendation(self) -> TimeRecommendation:
        self.matchday.sync(self)
        return self.calendar.recommendation(self)

    def observe(self, months: int = 1) -> None:
        if months < 0:
            raise ValueError("months cannot be negative")
        for _ in range(months):
            before = self.global_month
            super().observe(1)
            if self.global_month > before:
                self.executive.advance_month(self)
                if hasattr(self, "calendar"):
                    self.calendar.sync_to_world(self.global_month)
            if self.history_finished:
                break

    def resolve_decision(self, option_id: str):
        decision = self.current_decision
        if decision is None:
            raise RuntimeError("there is no presidential decision pending")
        option = next(item for item in decision.options if item.id == option_id)
        record = super().resolve_decision(option_id)
        if self.can_act and option_id != "submit_resignation":
            self.executive.open_mandate(
                self,
                decision_id=decision.id,
                option_id=option_id,
                option_title=option.title,
                subject=f"{decision.title}：{decision.narrative}",
            )
        return record

    def resolve_match_camp(self, choice: str):
        return self.matchday.resolve_camp(self, choice)

    def resolve_club_release(self, choice: str):
        return self.matchday.resolve_release(self, choice)

    def set_match_mandate(self, choice: str):
        return self.matchday.set_match_mandate(self, choice)

    def resolve_match_review(self, choice: str):
        return self.matchday.resolve_review(self, choice)

    def assign_implementation(
        self,
        *,
        mandate_id: str,
        office: str,
        instruction_style: str,
    ):
        if not self.can_act:
            raise RuntimeError("successor-government implementation is not player-controlled")
        return self.executive.assign_mandate(
            self,
            mandate_id=mandate_id,
            office=office,
            instruction_style=instruction_style,
        )

    def start_press_conference(
        self,
        *,
        topic: str,
        outlet: str = "全国媒体联合采访",
    ):
        if not self.can_act:
            raise RuntimeError("successor-government press conferences are not player-controlled")
        return self.executive.start_press_conference(
            self,
            topic=topic,
            outlet=outlet,
        )

    def answer_press_conference(
        self,
        *,
        session_id: str,
        answer_style: str,
    ):
        if not self.can_act:
            raise RuntimeError("successor-government press conferences are not player-controlled")
        return self.executive.answer_press_conference(
            self,
            session_id=session_id,
            answer_style=answer_style,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["format_version"] = EXECUTIVE_PRESIDENT_SAVE_VERSION
        payload["causal_fingerprint"] = CausalPresidentCareerGame.fingerprint(self)
        payload["executive"] = self.executive.to_dict()
        payload["calendar"] = self.calendar.to_dict()
        payload["matchday"] = self.matchday.to_dict()
        payload["fingerprint"] = self.fingerprint()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutivePresidentCareerGame":
        version = int(data.get("format_version", 0))
        if version not in {
            EXECUTIVE_PRESIDENT_SAVE_VERSION,
            LEGACY_TIME_SAVE_VERSION,
            LEGACY_EXECUTIVE_SAVE_VERSION,
        }:
            raise ValueError("unsupported executive-president save format")
        causal_payload = dict(data)
        causal_payload["format_version"] = CAUSAL_PRESIDENT_SAVE_VERSION
        causal_payload["fingerprint"] = data.get("causal_fingerprint")
        for key in ("causal_fingerprint", "executive", "calendar", "matchday"):
            causal_payload.pop(key, None)
        base = CausalPresidentCareerGame.from_dict(causal_payload)
        game = cls.__new__(cls)
        game.__dict__.update(base.__dict__)
        game.executive = ExecutiveGovernmentRuntime.from_dict(data["executive"])
        game.calendar = (
            AdaptiveCalendar.from_dict(data["calendar"])
            if version >= LEGACY_TIME_SAVE_VERSION and data.get("calendar")
            else AdaptiveCalendar.from_world_month(game.global_month)
        )
        game.matchday = (
            NationalTeamCommandRuntime.from_dict(data["matchday"])
            if version == EXECUTIVE_PRESIDENT_SAVE_VERSION and data.get("matchday")
            else NationalTeamCommandRuntime()
        )
        game.calendar.sync_to_world(game.global_month)
        expected = data.get("fingerprint")
        if version == EXECUTIVE_PRESIDENT_SAVE_VERSION:
            actual = game.fingerprint()
        elif version == LEGACY_TIME_SAVE_VERSION:
            actual = game._v9_fingerprint()
        else:
            actual = game._v8_fingerprint()
        if expected and actual != expected:
            raise ValueError("executive-president replay fingerprint mismatch")
        return game

    @classmethod
    def from_json(cls, content: str) -> "ExecutivePresidentCareerGame":
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("save root must be a JSON object")
        return cls.from_dict(payload)

    def _v8_fingerprint(self) -> str:
        payload = {
            "causal": CausalPresidentCareerGame.fingerprint(self),
            "executive": self.executive.fingerprint(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    def _v9_fingerprint(self) -> str:
        payload = {
            "causal": CausalPresidentCareerGame.fingerprint(self),
            "executive": self.executive.fingerprint(),
            "calendar": self.calendar.to_dict(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    def fingerprint(self) -> str:
        payload = {
            "causal": CausalPresidentCareerGame.fingerprint(self),
            "executive": self.executive.fingerprint(),
            "calendar": self.calendar.to_dict(),
            "matchday": self.matchday.fingerprint(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
