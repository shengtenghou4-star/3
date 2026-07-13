# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president controls regulation, funding, club licensing, youth development, transfer policy and national teams, while clubs, owners, local associations, players, media and ministries react through their own incentives and constraints.

## Playable modes

### Standard presidential campaign

```bash
python -m pip install -e '.[dev,ui]'
football-republic-web
```

The original 24-month vertical slice: six top-flight clubs, national policy programs, cabinet decisions, transfers, World Cup qualifying and a board-confidence review.

### Deep professional ecosystem

```bash
python -m pip install -e '.[dev,ui]'
football-republic-deep
```

The deep mode connects:

- fourteen professional clubs across two divisions;
- complete league seasons, promotion, relegation and a play-off;
- a fourteen-club national knockout cup;
- an eight-club continental champions competition;
- central media-rights distributions;
- administration, points deductions and licence withdrawal;
- persistent club owners with bailout memory;
- contracts, free agency and development loans;
- schedule congestion, travel fatigue and injury risk;
- a twenty-six-player national squad selected from the club database.

The standard mode remains available and unchanged.

## Domestic league pyramid

The National Premier League contains six clubs and the National Championship contains eight. Both play full double round-robin seasons.

Promotion is not decided by points alone. A club must also pass:

- professional licensing;
- solvency requirements;
- wage-arrears checks.

A second-division champion can therefore be denied promotion if its finances are fraudulent or its players remain unpaid.

## National FA Cup

All fourteen clubs enter the cup in each season. The two highest-seeded clubs receive first-round byes, followed by quarterfinals, semifinals and a final.

Cup ties are played through the same player, fitness and match engine as league games. Drawn knockout ties are resolved by penalties. Prize money enters the winning club's real cash balance.

## Continental Champions Cup

Two domestic clubs qualify for an eight-club continental competition containing two groups of four, semifinals and a final.

The first-season representatives are chosen from opening club strength. The second-season representatives come from the previous Premier League table. Clubs receive appearance and progression payments, while away fixtures create extra travel fatigue.

```text
continental qualification
  -> extra prize and gate income
  -> more matches and travel
  -> lower fitness and higher injury risk
  -> deeper squad becomes more valuable
```

## Schedule congestion

Every match already reduces the fitness of the players who took part. When a club plays more than two matches in a month, the system adds congestion costs. Continental away matches add travel strain.

High-load months can create:

- extra fitness loss;
- additional injuries;
- reduced tactical cohesion;
- weaker league performance after cup or continental games;
- club-versus-country tension when selected players return tired.

## Contracts, free agents and loans

Players now leave clubs when contracts expire unless a renewal is agreed. Clubs decide whether to make an offer based on player importance, age, financial health and wage arrears. Players consider morale, club stability and the proposed salary.

Possible outcomes include:

- multi-year renewal;
- release into free agency;
- emergency three-month extension when a club would fall below the minimum squad size;
- free-agent signing without a transfer fee;
- development loan from a Premier League club to a second-division club.

Loans move the real player object, split wages between the two clubs and return the player at the end of the registration period. The first registration cycle happens after the president's month-six transfer-policy decision, not before it.

## Media-rights system

Each season distributes:

- Premier League pool: 18M;
- National Championship pool: 5M.

Each pool is split into:

- 55% equal share;
- 25% sporting-merit share;
- 20% audience-value share.

## Club-owner behaviour

Owners are persistent agents with:

- wealth;
- ambition;
- patience;
- relationship with the football association;
- public reputation;
- cumulative injections;
- bailout memory;
- broken promises.

An unconditional rescue teaches the owner that the association may protect the club again. Refusing support damages the relationship. Conditional rescue creates a different long-run incentive.

## National-team selection

Every international window selects twenty-six eligible Longhua players from the shared club database. Selection considers:

- ability;
- fitness and injury status;
- morale;
- club appearances;
- club form;
- division level;
- homegrown status;
- positional quotas.

The match engine combines squad quality with association-level coaching and preparation. A president cannot permanently buy national-team strength if the domestic player pool remains weak.

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

## Command line

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

The design rule is unchanged: important outcomes must remain traceable through money, capacity, incentives, delay, compliance, player quality, ownership behaviour, contracts, workload, governance decisions and match events. No scripted champions, protected clubs or unexplained score jumps.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/M1_STATUS.md`](docs/M1_STATUS.md).
