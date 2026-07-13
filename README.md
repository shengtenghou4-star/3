# Statecraft Lab

A simulation laboratory for institutional power, resource control, and organizational decision-making.

## What this project studies

Formal rank is only one part of real power. Statecraft Lab models how authority emerges from the interaction of:

- formal office and jurisdiction;
- budget and approval limits;
- information access;
- appointment and veto rights;
- personal and institutional networks;
- implementation capacity;
- reputation, trust, and political risk;
- shocks such as leadership changes, crises, audits, and policy campaigns.

The goal is to answer questions such as:

- How much resource can an actor actually mobilize?
- Why can a lower-ranked actor sometimes outperform a nominal superior?
- What changes when a new leader, regulation, or crisis enters the system?
- Where are the real bottlenecks, veto points, and hidden dependencies?
- How stable is an actor's power if allies, budget, or legitimacy disappear?

## Design principles

1. **Mechanisms before storytelling** — every result must come from explicit rules.
2. **Formal power and effective power are separate variables.**
3. **Uncertainty is visible** — outputs should include ranges and sensitivity analysis.
4. **No magic scores** — aggregate indices must be decomposable into interpretable components.
5. **Scenario replay** — the same institution can be tested under different shocks.
6. **Evidence-ready architecture** — real-world calibration can be added without rewriting the engine.

## Initial architecture

```text
statecraft_lab/
├── core/          # actors, institutions, resources, authority graph
├── engine/        # simulation loop and decision resolution
├── metrics/       # effective power, leverage, fragility, bottlenecks
├── scenarios/     # reusable institutional scenarios
└── cli.py         # command-line entry point

tests/             # deterministic unit tests
/docs               # model specification and research notes
```

## Phase 1 target

Build a deterministic minimum viable engine that can:

- define actors and institutions;
- assign formal authority and resource pools;
- represent approval chains and veto points;
- execute a resource-mobilization request;
- calculate effective power and fragility;
- compare the result before and after a policy or leadership shock.

## Status

Project initialized. The repository is intentionally isolated from all other projects.
