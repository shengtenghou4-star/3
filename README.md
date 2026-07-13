# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president can rewrite club licensing, fund youth coaching and competitions, negotiate with ministries, reshape national-team spending and then live with delayed implementation, local leakage, owner resistance, match results and public pressure.

This is not a club-management game. It connects national policy to regional associations, professional clubs, individual players, domestic competitions, international qualification, schools, coaches and registered youth players.

## Launch the polished command centre

```bash
python -m pip install -e '.[dev,ui]'
football-republic-web
```

The Streamlit command centre contains six working views:

- presidential overview and national-football asset curves;
- World Cup qualifying table, results, xG, possession and attendance;
- domestic league standings, form and match-centre data;
- club finances, governance indicators and 25-player first-team rosters;
- regional youth-development comparisons;
- a combined policy and match audit trail.

The sidebar advances the simulation by one month, three months or to the end of the 24-month term.

## Command-line version

```bash
python -m pip install -e '.[dev]'
football-republic --strategy foundations
football-republic --strategy balanced
football-republic --strategy quick-results
football-republic --interactive
```

The three presets create different political and sporting legacies:

- `foundations` spends heavily on coaches, matches and strict club reform;
- `balanced` protects both development and short-term results;
- `quick-results` concentrates money on the senior national team and accepts deeper structural risk.

In the calibrated 2026 scenario, the same World Cup qualifying schedule currently produces three distinct strategic paths: the foundations strategy finishes outside the qualifying places, the balanced strategy reaches the play-off place, and the quick-results strategy can win the group. Those outcomes emerge from the shared match engine rather than scripted endings.

## Sporting systems now simulated

- Six clubs playing two complete double round-robin domestic seasons;
- 25-player rosters for every club, including position, age, ability, potential, fitness, morale, injuries, wage, contract, nationality and homegrown status;
- attack, midfield, defence, goalkeeper, depth, cohesion and form calculations;
- match simulation with expected goals, score, possession, attendance and gate receipts;
- league tables, five-match form, prize money and performance-driven revenue changes;
- club cash, debt, monthly operating losses, wage arrears, licensing and forfeits;
- a six-team, ten-round World Cup qualifying group with all 30 fixtures simulated;
- dynamic national-team strength and fan-trust reactions based on expected versus actual results.

## Governance and development systems

- Three contrasting regional football associations;
- coach education with nine-month delays and regional completion rates;
- youth match grants with implementation leakage;
- a cross-ministry school-football agreement;
- club licensing reform, restructuring, sanctions and rule-gaming;
- monthly club finances, arrears and exclusion;
- monthly history plus six-month presidential dashboards;
- a month-24 board confidence review;
- an audit log explaining how outcomes were produced.

## Core causal chains

```text
public grant
  -> regional execution and integrity
  -> useful capacity versus waste
  -> delayed coaches, matches or school programmes
  -> changed youth-development conditions

club licensing rule
  -> audit strength and club readiness
  -> compliance, restructuring, sanctions or loopholes
  -> wages, liquidity, arrears and league stability

club resources and roster quality
  -> line ratings, fitness, morale and form
  -> xG, results, attendance and league position
  -> gate receipts, prize money and future revenue

national-team investment
  -> team strength and match expectations
  -> qualification results
  -> fan trust and the president's board review
```

## Development

```bash
pytest -q
```

The project standard is simple: no unexplained score jumps. Important outcomes must remain traceable through money, capacity, incentives, delay, compliance, player quality and match events.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/M1_STATUS.md`](docs/M1_STATUS.md).
