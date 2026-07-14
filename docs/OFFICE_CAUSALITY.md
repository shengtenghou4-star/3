# Presidential Office Causality

Football Republic 0.14 makes office behaviour part of the long-term simulation rather than temporary interface flavour.

## Meetings

A meeting choice changes access, trust and future behaviour.

```text
president meets personally
-> stronger support and trust
-> written follow-up expectation
-> possible fairness criticism if one bloc receives repeated direct access

secretary-general meets first
-> formal channel remains open
-> smaller political benefit
-> president retains distance

written submission required
-> higher procedural credibility
-> lower immediate access satisfaction

meeting declined
-> support and patience fall
-> mobilization and alternative pressure channels rise
```

Meeting records persist through saves. Follow-up deadlines are evaluated later.

## Information filtering

The world contains a true state, but the president receives departmental reports.

Every senior official filters information through:

- competence;
- integrity;
- loyalty to the president;
- network position;
- risk tolerance;
- departmental interest;
- current grievance toward the administration.

Low-quality filtering can delay or soften bad news. It does not create arbitrary random lies. A finance official may focus on payment capacity and omit investor-enforcement risk; a technical director may accurately describe player fatigue while underestimating public impatience.

The player-facing report contains only:

- office and responsible official;
- headline and summary;
- source basis;
- confidence category;
- urgency.

Hidden coverage, omission and smoothing scores remain internal.

## Public statements

Media answers create exact quotations. Some answers create reviewable commitments.

A statement can become:

- `pending` while the future policy record is evaluated;
- `kept` if no formal contradiction occurs during the review period;
- `contradicted` if a later formal decision reverses it;
- `noncommitment` if the president refused to make a testable claim.

A quotation that was initially kept can still be cited years later if the president subsequently reverses policy. Short-term consistency does not erase the public record.

## Internal leaks

Leaks require both source material and motive.

Sensitive source material can include:

- direct or rejected presidential meetings;
- internal preparation for a later-contradicted media statement.

Leak risk depends on:

- official loyalty;
- integrity;
- network power;
- scandal exposure;
- accumulated grievance;
- the existence of material worth leaking.

Possible motives include procedural whistleblowing, factional self-protection and retaliation against the president's handling of an issue.

## Deterministic replay

Office actions are stored in the political world's external-action log with:

- global month;
- exact action sequence;
- number of formal decisions already resolved;
- state, stakeholder and official effects.

During loading, meetings, statements and leaks are replayed between the same formal decisions and at the same months. They are not applied as a final adjustment after the world has already evolved.

## Player authority

These systems do not expand the player's formal powers.

The player still cannot:

- force a stakeholder to support a policy;
- dictate club decisions;
- choose a court verdict;
- control a successor government;
- see hidden information-filter scores.

The office layer changes what the president hears, whom the president grants access to and what the president can later be held accountable for.
