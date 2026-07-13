# Football Republic

**A National Football Governance Simulator**

Football Republic is a simulation game about running an entire country's football system as a powerful association president. The player can reshape professional leagues, club regulation, youth development, coaching, national teams, integrity systems, football finance and cross-government policy.

The central challenge is implementation. A regulation can be evaded. A subsidy can be wasted. A new academy can lack coaches and matches. A World Cup qualification can hide a collapsing league. The simulator therefore tracks the institutions and causal chains between a presidential decision and what actually happens to clubs, coaches, children and players years later.

## First playable target

The first vertical slice will simulate 24 months in a fictionalized large East Asian football nation beginning in 2026. It will include regional associations, clubs, youth development, constrained budgets, delayed reforms and a board confidence review.

## Current vertical slice

The codebase already contains the first end-to-end policy chain:

`national coach-education grant -> regional execution and leakage -> delayed licensed-coach graduates -> improved youth-development conditions`

This is deliberately narrow. It proves the architecture before the project adds leagues, clubs, players, politics and national teams.

## Repository structure

```text
src/football_republic/   simulation domain and engine
tests/                   deterministic model tests
docs/GAME_DESIGN.md      project constitution
docs/ROADMAP.md          delivery sequence
```

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Design standard

No unexplained magic outcomes. Every important result must be traceable through explicit capacity, incentives, money, delay, compliance and measurable football conditions.
