# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president controls regulation, funding, club licensing, youth development, transfer policy and national teams, while clubs, owners, local associations, players, media and ministries react through their own incentives and constraints.

The project now has two playable modes.

## Standard presidential campaign

```bash
python -m pip install -e '.[dev,ui]'
football-republic-web
```

This is the original 24-month vertical slice: six top-flight clubs, national policy programs, cabinet decisions, transfers, World Cup qualifying and a board-confidence review.

## Deep professional ecosystem

```bash
python -m pip install -e '.[dev,ui]'
football-republic-deep
```

The deep mode expands the same 24-month presidency into a connected national club pyramid:

- fourteen professional clubs across two divisions;
- six-club National Premier League and eight-club National Championship;
- full double round-robin schedules at both levels;
- automatic promotion, relegation and a promotion play-off;
- promotion eligibility constrained by licensing, solvency and wage arrears;
- central media-rights distributions split into equal, merit and audience shares;
- administration, six-point deductions, owner rescue injections and licence withdrawal;
- persistent club owners with wealth, ambition, patience, reputation and memory of FA bailouts;
- a twenty-six-player national squad selected from the shared club-player database;
- national selection based on ability, fitness, morale, club appearances, form and division level;
- a dedicated regulatory dashboard for the pyramid, owners, media money, administration and national-team selection.

The old mode remains available and unchanged. Deep mode is an additional simulation rather than a replacement.

## Why the pyramid matters

A club cannot be promoted simply because it finishes first. It must also pass financial and licensing tests. A second-division champion with unpaid wages can be denied promotion, allowing the next eligible club to move up.

A struggling club can enter formal administration, receive a points deduction and face several possible paths:

```text
financial distress
  -> administration and points deduction
  -> owner capacity and willingness to inject money
  -> conditional recovery or licence withdrawal
  -> sporting damage, relegation and revenue loss
```

Promotion and relegation feed back into club economics:

```text
promotion
  -> higher recurring revenue and media exposure
  -> stronger transfer demand and wage pressure

relegation
  -> revenue shock
  -> owner patience falls
  -> greater debt and insolvency risk
```

## Media-rights system

Each season distributes two central pools:

- Premier League: 18M;
- National Championship: 5M.

Each pool is divided as follows:

- 55% equal share;
- 25% sporting-merit share;
- 20% audience-value share.

This produces a genuine policy trade-off. A more equal system protects competitive balance; a more audience-heavy system strengthens large clubs and can widen the gap.

## Club-owner behaviour

Owners are persistent agents rather than one-off random events. Each owner has:

- financial capacity;
- sporting ambition;
- patience;
- relationship with the football association;
- public reputation;
- cumulative injections;
- bailout memory;
- broken promises.

An unconditional rescue teaches the owner that the association may protect the club again. Refusing support damages the relationship and can reduce future willingness to cooperate. Conditional rescue produces a different long-term relationship.

## National-team selection

The deep mode no longer treats the national team as a free-standing rating. Every international window selects twenty-six eligible Longhua players from all club rosters.

The selection process considers:

- ability;
- fitness and injury status;
- morale;
- club appearances;
- club form;
- division level;
- homegrown status;
- positional quotas.

The match engine then combines squad quality with association-level preparation and coaching investment. A president cannot permanently buy national-team strength if the domestic player pool remains weak.

## Governance systems

Both modes include:

- opening and second-year football budgets;
- coach education and youth-match funding;
- school-football negotiations;
- club licensing reform;
- a youth-safety crisis;
- transfer-market regulation;
- club bailout pressure;
- national-team coaching controversy;
- regional corruption investigations;
- monthly club finances and wage arrears;
- explainable audit logs;
- a month-24 board-confidence review.

## Command-line campaign

```bash
python -m pip install -e '.[dev]'
football-republic --strategy foundations
football-republic --strategy balanced
football-republic --strategy quick-results
football-republic --interactive
```

## Development

```bash
pytest -q
```

The design rule is unchanged: important outcomes must remain traceable through money, capacity, incentives, delay, compliance, player quality, ownership behaviour, governance decisions and match events. No scripted champions, protected clubs or unexplained score jumps.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/M1_STATUS.md`](docs/M1_STATUS.md).
