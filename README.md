# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president can rewrite club licensing, fund youth coaching and competitions, negotiate with ministries, reshape national-team spending and then live with delayed implementation, local leakage, owner resistance and public pressure.

This is not a club-management game. It models the chain from national policy to regional associations, professional clubs, schools, coaches and registered youth players.

## Play the current 24-month vertical slice

```bash
python -m pip install -e '.[dev]'
football-republic --strategy foundations
football-republic --strategy balanced
football-republic --strategy quick-results
football-republic --interactive
```

The three presets create different political legacies:

- `foundations` spends heavily on coaches, matches and strict club reform;
- `balanced` protects both development and short-term results;
- `quick-results` concentrates money on the senior national team and accepts deeper structural risk.

Interactive mode lets the player allocate the opening 60m treasury and choose licensing strictness directly.

## What is simulated now

- Three contrasting regional football associations;
- six professional clubs with revenue, wages, debt, owners and academy quality;
- coach education with nine-month delays and regional completion rates;
- youth match grants with implementation leakage;
- a cross-ministry school-football agreement;
- club licensing reform, restructuring, sanctions and rule-gaming;
- monthly club finances, arrears and exclusion;
- six-month presidential dashboards;
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
```

## Development

```bash
pytest -q
```

The project standard is simple: no unexplained score jumps. Important outcomes must remain traceable through money, capacity, incentives, delay, compliance and measurable football conditions.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) for the project constitution and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the long-run build sequence.
