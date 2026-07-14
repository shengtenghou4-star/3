"""Replay-safe national-team command effects.

The long-term world is reconstructed from ordered presidential actions.  Match-window
costs, supporter reactions and club-owner relationships must therefore enter that same
external-action stream rather than mutating the world only in memory.
"""

from __future__ import annotations

from .national_team_command import NationalTeamCommandRuntime


class ReplayableNationalTeamCommandRuntime(NationalTeamCommandRuntime):
    def resolve_camp(self, game, choice: str):
        state = game.current_campaign.engine.state
        treasury_before = float(state.treasury)
        window = super().resolve_camp(game, choice)
        treasury_after = float(state.treasury)
        state.treasury = treasury_before
        delta = treasury_after - treasury_before
        if delta:
            game.world.apply_external_action(
                "matchday_camp_budget",
                {
                    "state_deltas": {"treasury": delta},
                    "audit_note": (
                        f"national-team camp approved — {self.CAMP_CHOICES[choice]['label']}; "
                        f"cost {abs(delta):.0f}"
                    ),
                },
            )
        return window

    def resolve_release(self, game, choice: str):
        state = game.current_campaign.engine.state
        owners = game.current_campaign.football.pyramid.owners
        treasury_before = float(state.treasury)
        owner_before = {
            item.club_id: float(owners[item.club_id].relationship_with_fa)
            for item in self.active_window.disputes
            if item.club_id in owners
        } if self.active_window is not None else {}
        window = super().resolve_release(game, choice)
        treasury_after = float(state.treasury)
        owner_after = {
            club_id: float(owners[club_id].relationship_with_fa)
            for club_id in owner_before
        }
        state.treasury = treasury_before
        for club_id, value in owner_before.items():
            owners[club_id].relationship_with_fa = value
        game.world.apply_external_action(
            "matchday_release_arbitration",
            {
                "state_deltas": {"treasury": treasury_after - treasury_before},
                "owner_deltas": [
                    {
                        "club_id": club_id,
                        "relationship_with_fa": owner_after[club_id] - before,
                    }
                    for club_id, before in owner_before.items()
                ],
                "audit_note": (
                    f"national-team player release arbitration — "
                    f"{self.RELEASE_CHOICES[choice]['label']}"
                ),
            },
        )
        return window

    def resolve_review(self, game, choice: str):
        state = game.current_campaign.engine.state
        treasury_before = float(state.treasury)
        trust_before = float(state.fan_trust)
        window = super().resolve_review(game, choice)
        treasury_after = float(state.treasury)
        trust_after = float(state.fan_trust)
        state.treasury = treasury_before
        state.fan_trust = trust_before
        game.world.apply_external_action(
            "matchday_post_match_review",
            {
                "state_deltas": {
                    "treasury": treasury_after - treasury_before,
                    "fan_trust": trust_after - trust_before,
                },
                "audit_note": (
                    f"national-team post-match review — {self.REVIEW_CHOICES[choice]}"
                ),
            },
        )
        return window


def install_owner_replay(career_history_class) -> None:
    if getattr(career_history_class, "_matchday_owner_replay_installed", False):
        return
    original = career_history_class._apply_external_effects

    def _apply_external_effects(self, action_type, payload):
        original(self, action_type, payload)
        owners = self.current_campaign.football.pyramid.owners
        for delta in payload.get("owner_deltas", []):
            owner = owners.get(delta.get("club_id"))
            if owner is None:
                continue
            owner.relationship_with_fa = max(
                0.0,
                min(
                    1.0,
                    owner.relationship_with_fa
                    + float(delta.get("relationship_with_fa", 0.0)),
                ),
            )

    career_history_class._apply_external_effects = _apply_external_effects
    career_history_class._matchday_owner_replay_installed = True
