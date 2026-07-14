# Adaptive Presidential Time

Version 0.17 replaces rigid monthly button presses with a player-facing calendar that can move by days, weeks or guarded fast-forward.

## One authoritative world clock

Football Republic still settles the actual simulation once per month. Club finances, league matches, contracts, player development, political reactions and justice cases are not duplicated in a second daily engine.

The adaptive calendar sits above that monthly settlement clock:

```text
visible presidential date
        ↓ crosses month boundary
one authoritative world settlement
        ↓
attention is reassessed
        ↓
continue, slow down or stop
```

This preserves determinism while allowing the player to experience quiet administration, preparation weeks and crisis days at different speeds.

## Available pacing

### Deliberate

Moves one calendar day. This is useful during negotiations, public controversy, an approaching match window or the final days before an implementation review.

### Adaptive

Uses the office's current attention assessment:

- crisis or overdue accountability: one day;
- high-pressure window: three days;
- meaningful but non-critical risk: one week;
- routine administration: about three weeks;
- quiet period: up to roughly six weeks.

The recommendation can be shortened when a known preparation checkpoint is closer.

### Guarded fast-forward

Searches for the next meaningful public checkpoint for at most 120 days. It never blindly runs the full horizon. The system re-evaluates after every monthly settlement and stops when a new decision, match result, justice stage, club crisis or implementation change appears.

## Hard stops

Time cannot move while the president still has direct responsibility for:

- an unsigned presidential decision;
- an open live press conference;
- a signed decision without a named implementation owner.

These are not optional notifications. Skipping them would erase the player's responsibility, so the calendar remains frozen until the action is completed.

## Slow-down signals

The calendar uses public or institutionally reported information only.

High-pressure signals include:

- delayed or narrowed implementation;
- overdue supervision reviews;
- formal justice cases approaching charging, trial or appeal;
- clubs in administration, exclusion or serious wage arrears;
- coalition support entering a dangerous range;
- the national team falling outside qualification places after matches have actually begun.

An all-zero preseason table is not treated as a national-team crisis. Before the first match, alphabetical table order has no sporting meaning.

## Known preparation checkpoints

The calendar begins slowing roughly one week before publicly known hard nodes:

- national-team qualifier rounds;
- domestic cup rounds;
- continental group and knockout rounds;
- registration and transfer settlement;
- season settlement and annual review;
- major governance agenda months;
- implementation review deadlines;
- scheduled justice procedure updates.

The player reaches the preparation week before the event instead of learning about the event only after the monthly result appears.

## Why time stopped

Every time jump records:

- start and end date;
- calendar days elapsed;
- monthly settlements crossed;
- the reason progression stopped;
- major public changes during settlement.

Examples include:

- a presidential dossier entered the office;
- the national-team ranking changed;
- formal matches were completed;
- a club entered or left distress;
- a justice case changed stage;
- an implementation mandate changed status;
- coalition stability or fan trust moved materially.

## Save compatibility

Version-9 presidential saves include:

- current visible date;
- last time-advance result;
- recent time-flow history.

Version-8 saves from Football Republic 0.16 remain loadable. Their calendar is reconstructed from the saved authoritative world month, and their legacy fingerprint is verified before upgrading.

## Information boundary

The pacing model does not read or display hidden competence, loyalty, network power, private evidence probability or hidden delivery-quality scores. Time slows because of visible responsibilities and public events, not because the game secretly reveals an NPC's true nature.