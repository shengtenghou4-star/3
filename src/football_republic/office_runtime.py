"""Calibration safeguards for the causal presidential office."""

from __future__ import annotations

from dataclasses import replace

from .office_causality import OfficeCausality, QuoteConsequence


class CausalOfficeRuntime(OfficeCausality):
    """Office engine with severity floors and durable public quotations."""

    def _generate_reports(self, game) -> None:
        super()._generate_reports(game)
        distress_scores = []
        for club in game.current_campaign.engine.state.clubs.values():
            if club.license_status == "excluded":
                distress_scores.append(1.0)
            elif club.license_status == "administration":
                distress_scores.append(0.86)
            elif club.wage_arrears_months >= 3:
                distress_scores.append(0.76)
            elif club.wage_arrears_months >= 2:
                distress_scores.append(0.62)
            elif club.financial_health < 0.28:
                distress_scores.append(0.58)
        if not distress_scores:
            return
        severity_floor = max(distress_scores)
        for index, report in enumerate(self.reports):
            if report.created_month != game.global_month or report.topic != "club_finance":
                continue
            severity = max(report.hidden_truth_severity, severity_floor)
            if severity == report.hidden_truth_severity:
                return
            delay = (
                1
                if severity >= 0.68 and report.hidden_coverage < 0.58
                else max(0, report.visible_month - report.created_month)
            )
            if report.hidden_coverage < 0.50:
                framing = (
                    "部门称风险仍可通过内部协调控制，但没有提供最坏情景、"
                    "现金断裂日期或明确停止条件。"
                )
            else:
                framing = (
                    "部门要求主席准备跨部门干预，并明确指出拖延会增加欠薪、"
                    "比赛完整性和准入成本。"
                )
            self.reports[index] = replace(
                report,
                visible_month=report.created_month + delay,
                summary=(
                    f"{report.headline}。{framing}报告主要从“现金来源、债务和规则一致性”角度解释问题。"
                ),
                urgency="紧急",
                hidden_truth_severity=severity,
            )
            return

    def note_formal_decision(
        self,
        game,
        *,
        decision_id: str,
        option_id: str,
        option_title: str,
    ) -> None:
        late_contradictions = [
            statement
            for statement in self.statements
            if statement.status == "kept"
            and option_id in statement.contradiction_options
        ]
        super().note_formal_decision(
            game,
            decision_id=decision_id,
            option_id=option_id,
            option_title=option_title,
        )
        for statement in late_contradictions:
            statement.status = "contradicted"
            statement.resolved_month = game.global_month
            statement.cited_month = game.global_month
            effects = (
                "媒体重新播放主席此前已经被视为兑现的原话。",
                "政策反转被解释为撤回承诺，短期守约记录不能抵消新的矛盾。",
            )
            game.world.apply_external_action(
                "late_quoted_contradiction",
                {
                    "stakeholder_deltas": [
                        {
                            "actor_id": "broadcaster",
                            "trust": -0.024,
                            "mobilization": 0.020,
                            "note": "媒体引用主席旧话质疑后续政策反转",
                        },
                        {
                            "actor_id": "supporters_federation",
                            "trust": -0.026,
                            "support": -0.014,
                            "note": "主席已兑现的公开表态后来被正式决定推翻",
                        },
                        {
                            "actor_id": "sponsor_council",
                            "trust": -0.017,
                            "note": "主席已兑现的公开表态后来被正式决定推翻",
                        },
                    ],
                    "state_deltas": {
                        "fan_trust": -0.019,
                        "integrity_reputation": -0.013,
                        "political_capital": -0.015,
                    },
                    "audit_note": (
                        f"previously kept quote contradicted by {decision_id}/{option_id}"
                    ),
                },
            )
            self.quote_history.append(
                QuoteConsequence(
                    game.global_month,
                    statement.id,
                    statement.quote,
                    option_title,
                    f"媒体再次引用主席原话，追问“{option_title}”为何推翻此前承诺",
                    effects,
                )
            )

    @classmethod
    def from_dict(cls, data):
        base = OfficeCausality.from_dict(data)
        engine = cls()
        engine.reports = base.reports
        engine.meetings = base.meetings
        engine.statements = base.statements
        engine.quote_history = base.quote_history
        engine.leaks = base.leaks
        engine.staff_grievance = base.staff_grievance
        engine._report_keys = base._report_keys
        engine._processed_months = base._processed_months
        return engine
