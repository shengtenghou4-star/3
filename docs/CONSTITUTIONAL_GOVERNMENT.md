# Constitutional Government and Association Appointments

Version 0.10 turns the continuous football history into an irregular political history. A two-year institutional term still determines budgets, competition calendars and ordinary congress dates, but the president who began that term is no longer guaranteed to finish it.

## Senior association cabinet

Every government appoints five named senior officials:

1. secretary-general;
2. finance and licensing director;
3. integrity and discipline commissioner;
4. national-team technical director;
5. grassroots and school-football commissioner.

Each official has four independent political-administrative attributes:

- competence;
- integrity;
- loyalty to the president;
- network power.

The three appointment styles create genuine trade-offs:

```text
technocrat
  -> high competence and integrity
  -> weaker personal loyalty and political network

loyalist
  -> strong presidential control
  -> weaker integrity and higher capture risk

coalition broker
  -> strong relationships and acceptable competence
  -> ambiguous accountability and internal bargaining costs
```

## Monthly administrative effects

Cabinet members are not decorative portraits. Their attributes alter the simulation every month.

- The secretary-general affects political capital and regional implementation capacity.
- The finance director affects treasury leakage and league financial governance.
- The integrity commissioner affects association integrity.
- The technical director affects national-team preparation.
- The grassroots commissioner affects parental and regional support for youth football.

Low-integrity officials with both strong loyalty and strong networks accumulate scandal exposure. This creates an endogenous relationship:

```text
president selects loyal networked official
  -> short-term control and implementation
  -> unreported relationships expand
  -> scandal exposure accumulates
  -> sponsors, finance ministry and supporters demand action
```

## Constitutional crisis checkpoints

Crisis assessments occur in local months 5, 9, 13, 17 and 21. The system combines:

- presidential integrity;
- the riskiest official's integrity and network power;
- accumulated scandal exposure;
- coalition support;
- national integrity reputation;
- previous constitutional strikes.

A crisis therefore emerges from appointments and political conditions rather than an isolated random event.

## Player choices during a crisis

The president may:

- suspend the official and refer the case to an independent inquiry;
- conduct a coalition cabinet reshuffle;
- protect the inner circle;
- resign when the crisis is severe enough.

An independent inquiry can restore integrity and sponsor trust but costs political capital and administrative continuity. A reshuffle can stabilize the coalition without fully resolving the allegations. Protecting a loyalist preserves short-term control but can form a no-confidence majority.

## Caretaker administration

A resignation or successful no-confidence vote creates a caretaker government. The secretary-general becomes acting president and major political discretion is restricted. The caretaker period lasts no more than three months.

Crucially, the football nation does not reset:

- leagues and cups continue;
- clubs continue paying wages and servicing debt;
- contracts continue to expire;
- injuries and player ageing continue;
- sponsorship and licensing consequences continue;
- existing laws and collective agreements remain in force.

The caretaker government therefore inherits the immediate operational consequences of the failed presidency rather than starting a new scenario.

## Snap election

At the end of the caretaker period, a snap football convention selects a new president. The successful route responds to the inherited system:

- low integrity favors an institutional-reform candidate;
- weak national-team performance and low fan trust favor a quick-results candidate;
- otherwise a balanced coalition candidate is more likely.

The new president appoints a cabinet but receives no artificial season reset or duplicate opening budget. The same players, clubs, owners, debts, stadiums, sponsors and stakeholder relationships continue.

## Historical records

The twenty-year dashboard now records:

- every senior appointment and replacement;
- every administration's exact start and end month;
- normal succession, resignation, caretaker government and snap election;
- allegations, crisis choices and material consequences;
- the same long-term sporting, club, player and industry records introduced in version 0.9.

This allows one formal two-year institutional term to contain multiple governments while the competition calendar remains intact.

## Safe saves

Constitutional saves remain UTF-8 JSON. They store the initial strategy, target month and every decision in chronological order. Loading replays the entire history deterministically and validates a state fingerprint that includes:

- football state;
- current president;
- cabinet members and scandal exposure;
- appointments;
- administration spans;
- constitutional events;
- caretaker timing;
- pending crisis decisions.

A modified or incompatible save is rejected instead of being loaded silently.

## Remaining depth

This release does not yet include:

- multi-round coalition bargaining over each appointment;
- personal careers for ministers and regional executives;
- family and patronage networks spanning several institutions;
- criminal trials or court appeals;
- club relocation and forced ownership sales;
- overseas leagues and international football labor markets.
