# Continuous National Football History

`football-republic-history` runs one persistent football nation for up to twenty years.

```bash
python -m pip install -e '.[dev,ui]'
football-republic-history
```

## Time structure

- One presidential term lasts 24 months.
- One term contains two domestic and continental seasons.
- A maximum history contains ten terms and twenty seasons.
- A president can serve no more than three consecutive terms.

At a term boundary, the game rebuilds future schedules but does not rebuild the nation. The following state survives:

- club identities and division membership;
- cash, debt, arrears and professional licences;
- all contracted players and free agents;
- player age, development, fitness, morale and career appearances;
- club owners, wealth, patience, reputation and bailout memory;
- stadium capacity, quality and investment;
- sponsorship contracts and recurring commercial revenue;
- registration law and player-welfare rules;
- stakeholder support, trust, patience, mobilization and memory;
- phoenix-club ownership and prior insolvency consequences.

## Succession

At month 24, the ordinary football board review and the political coalition review are evaluated together.

An incumbent can:

- win a clear coalition renewal;
- survive a contested convention;
- lose office through coalition collapse;
- lose office after the football board withdraws confidence;
- leave after reaching the three-term consecutive limit.

A successor inherits the actual state rather than receiving a clean scenario. Debt, weak academies, restrictive laws, damaged sponsor relationships and hostile stakeholders remain in place.

## Transition finance

Each new term receives a transition grant derived from:

- stakeholder support;
- institutional integrity;
- league financial health;
- national-team strength.

The incoming president's opening programme is automatically scaled to the treasury that actually exists. A bankrupt association cannot announce the same programme as a wealthy one.

## Global historical records

The long-term controller stores:

- every completed presidential term;
- every league and cup champion;
- continental performance by season;
- club financial and division snapshots;
- stadium capacity and owner history;
- academy graduations and retirements;
- sponsorship and insolvency events;
- presidential succession reasons.

Academy cohorts use global season numbers, so player IDs remain unique beyond the original two seasons.

## Safe deterministic saves

Save files are UTF-8 JSON. They do not contain pickled Python objects or executable code.

A save contains:

- the initial strategy;
- the option selected for every reached decision;
- completed-term strategies;
- the current term and month;
- a deterministic state fingerprint.

Loading a save reconstructs the original scenario and replays the decision history. The reconstructed football nation must match the stored fingerprint. A mismatch rejects the save instead of silently loading a corrupted or incompatible state.

This design makes save files reviewable, portable and safe while preserving exact deterministic outcomes.

## Current boundary

Version 0.9 provides one persistent fictional nation for twenty years. It does not yet include:

- multiple national starting scenarios;
- player agents and overseas careers;
- named ministers and governors with appointment mechanics;
- club relocation and ownership sales;
- fully modeled coaching careers;
- scenario editing or mod packages;
- histories longer than twenty years.
