# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president can rewrite club licensing, fund youth coaching and competitions, negotiate with ministries, manage transfer rules, survive political crises, reshape national-team spending and then live with delayed implementation, local leakage, owner resistance, match results and public pressure.

This is not a club-management game. It connects national policy to regional associations, professional clubs, individual players, domestic competitions, international qualification, schools, coaches and registered youth players.

## Launch the presidential command centre

```bash
python -m pip install -e '.[dev,ui]'
football-republic-web
```

The Streamlit command centre contains seven working views:

- presidential overview and national-football asset curves;
- cabinet decisions, year-two finance and transfer-market records;
- World Cup qualifying table, results, xG, possession and attendance;
- domestic league standings, form and match-centre data;
- club finances, governance indicators and first-team rosters;
- regional youth-development comparisons;
- a combined policy, decision, transfer and match audit trail.

The simulation stops at major presidential decisions. The player must sign a response before time can continue.

## Governing through the full term

The opening budget is no longer the player's only decision. Mandatory cabinet files arrive in months 4, 6, 8, 12, 16 and 20:

- a youth-match safety crisis;
- the national transfer-market policy;
- a politically powerful club demanding a bailout;
- the second-year football budget;
- a media campaign demanding the national-team coach's dismissal;
- evidence of regional training-fund kickbacks.

Every file has three materially different responses. Decisions change money, political capital, supporter trust, integrity, regional capacity, club finances, player movement and national-team performance.

## Year-two football finance

At month 12 the association receives a new annual funding package. It is generated from the first year's actual results:

```text
central public grant
  <- presidential political capital

commercial distribution
  <- supporter trust and league financial health

performance bonus
  <- current World Cup qualifying position

integrity bonus
  <- association integrity reputation
```

The player then chooses a grassroots acceleration package, a balanced renewal package or a World Cup qualification surge.

## Transfer market

The first transfer window opens after the month-six policy decision, with another window in month 18. Three regulatory approaches are available:

- homegrown priority: raises the value of young domestically trained players;
- open market: prioritizes established and foreign players for faster squad improvement;
- financial control: pushes clubs toward affordable and expiring contracts.

Transfers move the actual player object between club rosters. Fees move cash between clubs, and the new wage changes the buyer's monthly wage bill.

## Command-line version

```bash
python -m pip install -e '.[dev]'
football-republic --strategy foundations
football-republic --strategy balanced
football-republic --strategy quick-results
football-republic --interactive
```

The presets automatically resolve cabinet files according to their governing philosophy. The web interface allows the player to make every decision personally.

## Sporting systems simulated

- Six clubs playing two complete double round-robin domestic seasons;
- 25-player opening rosters for every club, including position, age, ability, potential, fitness, morale, injuries, wage, contract, nationality and homegrown status;
- attack, midfield, defence, goalkeeper, depth, cohesion and form calculations;
- match simulation with expected goals, score, possession, attendance and gate receipts;
- league tables, five-match form, prize money and performance-driven revenue changes;
- club cash, debt, monthly operating losses, wage arrears, licensing and forfeits;
- a six-team, ten-round World Cup qualifying group with all 30 fixtures simulated;
- dynamic national-team strength and fan-trust reactions based on expected versus actual results.

## Governance and development systems

- Three contrasting regional football associations;
- coach education with delayed delivery and regional completion rates;
- youth match grants with implementation leakage;
- cross-ministry school-football agreements;
- club licensing reform, restructuring, sanctions and rule-gaming;
- annual funding cycles linked to political, commercial, integrity and sporting outcomes;
- six mandatory mid-term presidential decisions;
- deterministic transfer windows linked to club finances and squad needs;
- monthly history, six-month snapshots and a month-24 board confidence review;
- an audit log explaining how outcomes were produced.

## Development

```bash
pytest -q
```

The project standard is simple: no unexplained score jumps. Important outcomes must remain traceable through money, capacity, incentives, delay, compliance, player quality, governance decisions and match events.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/M1_STATUS.md`](docs/M1_STATUS.md).
