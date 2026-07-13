"""Command-line interface for Football Republic."""

from __future__ import annotations

import argparse

from .campaign import Campaign, PresidentialPlan, STRATEGIES, Strategy, run_strategy


def _money(value: float) -> str:
    return f"{value / 1_000_000:.1f}m"


def _ask_millions(label: str, default: float) -> float:
    raw = input(f"{label} [{default:.1f}m]: ").strip()
    return (float(raw) if raw else default) * 1_000_000


def _interactive_plan() -> PresidentialPlan:
    print("You control a 60m association treasury. Enter allocations in millions.")
    plan = PresidentialPlan(
        coach_budget=_ask_millions("Coach education", 12.0),
        match_budget=_ask_millions("Youth match programme", 10.0),
        school_cofunding=_ask_millions("Education-ministry cofunding", 7.0),
        licensing_strictness=float(
            input("Club licensing strictness 0-1 [0.58]: ").strip() or "0.58"
        ),
        audit_budget=_ask_millions("Licensing audit budget", 2.5),
        senior_team_budget=_ask_millions("Senior national team", 14.0),
    )
    if plan.total_budget > 60_000_000:
        raise ValueError(
            f"plan costs {_money(plan.total_budget)}, above the 60.0m treasury"
        )
    return plan


def _print_campaign(
    label: str,
    plan: PresidentialPlan,
    campaign: Campaign,
    review: object,
) -> None:
    print(f"FOOTBALL REPUBLIC — 2026 PRESIDENTIAL TERM ({label})")
    print(
        "Opening plan: "
        f"coaches {_money(plan.coach_budget)}, matches {_money(plan.match_budget)}, "
        f"schools {_money(plan.school_cofunding)}, audits {_money(plan.audit_budget)}, "
        f"senior team {_money(plan.senior_team_budget)}, "
        f"licensing {plan.licensing_strictness:.0%}"
    )
    print()
    print(
        "MONTH  TREASURY  TRUST  INTEGRITY  LEAGUE  YOUTH ENV  "
        "SOLVENT  WC POS/PTS  TRANSFERS"
    )
    for dash in campaign.dashboards:
        print(
            f"{dash.month:>5}  {_money(dash.treasury):>8}  "
            f"{dash.fan_trust:>5.0%}  {dash.integrity_reputation:>9.0%}  "
            f"{dash.league_financial_health:>6.0%}  "
            f"{dash.youth_environment:>9.2f}  "
            f"{dash.solvent_club_share:>7.0%}  "
            f"{dash.qualifier_position:>2}/6 {dash.qualifier_points:>2}  "
            f"{dash.transfers_completed:>9}"
        )
    print()
    print(
        f"BOARD SCORE: {review.score:.1f}/100 — {review.verdict.upper()}"
    )
    for line in review.explanation:
        print(f"- {line}")

    print("\nPRESIDENTIAL DECISIONS")
    for record in campaign.decision_history:
        print(f"M{record.month}: {record.title} -> {record.option_title}")
        for effect in record.effects:
            print(f"  - {effect}")

    print("\nYEAR-TWO FOOTBALL FINANCE")
    if campaign.finance_reports:
        for report in campaign.finance_reports:
            print(
                f"M{report.month}: public {_money(report.public_grant)}, "
                f"commercial {_money(report.commercial_distribution)}, "
                f"performance {_money(report.performance_bonus)}, "
                f"integrity {_money(report.integrity_bonus)}, "
                f"total {_money(report.total_income)}"
            )
    else:
        print("No annual funding cycle completed.")

    print("\nTRANSFER MARKET")
    if campaign.transfer_market.history:
        for record in campaign.transfer_market.history:
            print(
                f"M{record.month}: {record.player_name} "
                f"({record.position}, {record.ability:.1f}) — "
                f"{record.seller_name} -> {record.buyer_name}, "
                f"fee {_money(record.fee)}"
            )
    else:
        print("No transfers completed.")

    print("\nWORLD CUP QUALIFYING TABLE")
    for position, row in enumerate(
        campaign.football.international.sorted_table(), start=1
    ):
        print(
            f"{position}. {row.team_name:<14} "
            f"P{row.played} W{row.won} D{row.drawn} L{row.lost} "
            f"GD{row.goal_difference:+} PTS{row.points}"
        )

    print("\nDOMESTIC LEAGUE TABLE")
    for position, row in enumerate(
        campaign.football.domestic_league.sorted_table(), start=1
    ):
        print(
            f"{position}. {row.team_name:<22} "
            f"P{row.played} W{row.won} D{row.drawn} L{row.lost} "
            f"GD{row.goal_difference:+} PTS{row.points}"
        )

    print("\nLAST IMPLEMENTATION AND MATCH EVENTS")
    for line in campaign.engine.audit_log[-16:]:
        print(f"- {line}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a 24-month Football Republic campaign"
    )
    parser.add_argument(
        "--strategy",
        choices=[item.value for item in Strategy],
        default=Strategy.BALANCED.value,
        help="presidential governing strategy",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="build a custom opening budget; mid-term decisions use the balanced doctrine",
    )
    args = parser.parse_args()

    if args.interactive:
        plan = _interactive_plan()
        campaign = Campaign(strategy=Strategy.BALANCED)
        campaign.enact_plan(plan)
        review = campaign.run(24)
        _print_campaign("custom", plan, campaign, review)
        return

    strategy = Strategy(args.strategy)
    plan = STRATEGIES[strategy]
    campaign, review = run_strategy(strategy)
    _print_campaign(strategy.value, plan, campaign, review)


if __name__ == "__main__":
    main()
