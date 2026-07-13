"""Command-line interface for the first Football Republic campaign."""

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
        licensing_strictness=float(input("Club licensing strictness 0-1 [0.58]: ").strip() or "0.58"),
        audit_budget=_ask_millions("Licensing audit budget", 2.5),
        senior_team_budget=_ask_millions("Senior national team", 14.0),
    )
    if plan.total_budget > 60_000_000:
        raise ValueError(f"plan costs {_money(plan.total_budget)}, above the 60.0m treasury")
    return plan


def _print_campaign(label: str, plan: PresidentialPlan, campaign: Campaign, review: object) -> None:
    print(f"FOOTBALL REPUBLIC — 2026 PRESIDENTIAL TERM ({label})")
    print(
        "Opening plan: "
        f"coaches {_money(plan.coach_budget)}, matches {_money(plan.match_budget)}, "
        f"schools {_money(plan.school_cofunding)}, audits {_money(plan.audit_budget)}, "
        f"senior team {_money(plan.senior_team_budget)}, licensing {plan.licensing_strictness:.0%}"
    )
    print()
    print("MONTH  TREASURY  TRUST  LEAGUE  YOUTH ENV  PLAYERS  COACHES  SOLVENT CLUBS")
    for dash in campaign.dashboards:
        print(
            f"{dash.month:>5}  {_money(dash.treasury):>8}  {dash.fan_trust:>5.0%}  "
            f"{dash.league_financial_health:>6.0%}  {dash.youth_environment:>9.2f}  "
            f"{dash.registered_youth_players:>7}  {dash.licensed_youth_coaches:>7}  "
            f"{dash.solvent_club_share:>13.0%}"
        )
    print()
    print(f"BOARD SCORE: {review.score:.1f}/100 — {review.verdict.upper()}")
    for line in review.explanation:
        print(f"- {line}")
    print("\nLAST IMPLEMENTATION EVENTS")
    for line in campaign.engine.audit_log[-8:]:
        print(f"- {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a 24-month Football Republic campaign")
    parser.add_argument(
        "--strategy",
        choices=[item.value for item in Strategy],
        default=Strategy.BALANCED.value,
        help="presidential governing strategy",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="build a custom opening budget instead of using a preset strategy",
    )
    args = parser.parse_args()

    if args.interactive:
        plan = _interactive_plan()
        campaign = Campaign()
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
