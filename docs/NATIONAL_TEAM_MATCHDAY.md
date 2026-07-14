# National-Team Matchday Command

Version 0.18 turns each important national-team qualifier into a presidential episode while preserving the constitutional boundary between the football-association chairman and the head coach.

## 1. The player is not the head coach

The head coach independently decides:

- the call-up list;
- formation and tactical approach;
- starting eleven;
- substitutions and in-match instructions.

The president can see the submitted squad, medical status, club concentration and important omissions. The president cannot directly replace a player, set a formation or pick the starting eleven through the normal interface.

The president controls the association responsibilities surrounding the team:

- camp funding and logistics;
- training and recovery standards;
- medical governance;
- arbitration when clubs resist releasing players;
- insurance or compensation arrangements;
- the public and private performance mandate;
- post-match accountability and the head coach's employment.

This is deliberately different from a football-manager game. The player is responsible for the institution that enables or constrains the coach.

## 2. Named head-coach career

The national team has one named serving head coach with persistent public records:

- philosophy;
- public reputation;
- relationship with the current chairman;
- job security;
- media pressure;
- wins, draws and losses;
- appointment and contract dates.

These public labels are visible. Hidden tactical calculations are not exposed as exact ratings.

A coach can survive bad results if the chairman continues to support a credible process, or lose the job after political pressure and repeated failure. Dismissal creates a real termination and emergency-selection cost and adds the outgoing coach to history.

## 3. Real player pool and squad announcement

Each match window draws from the existing domestic club-player database. The coach submits a deterministic 25-player squad:

- 3 goalkeepers;
- 8 defenders;
- 8 midfielders;
- 6 attackers.

Selection considers player readiness and development value with a small coach-specific uncertainty term. Every squad member retains:

- real player identity;
- club;
- position and age;
- fitness;
- medical status;
- broad coach-role description.

The chairman sees important omitted players but does not receive a hidden statement that an omission is objectively correct or incorrect.

## 4. Preparation stages

A qualifier enters the presidential calendar roughly seven days before the authoritative monthly match settlement.

### Stage A: camp authorization

The chairman chooses among:

- recovery-first camp;
- standard national-team camp;
- high-intensity closed preparation.

The choices trade money, readiness and medical risk. If the treasury cannot fully fund the selected plan, the finance office scales it down rather than creating money.

### Stage B: club-release arbitration

Disputes arise when one club supplies many players or called-up players have questionable fitness.

The chairman may:

- enforce full release under association rules;
- negotiate insurance and workload compensation;
- accept club medical exemptions.

These choices change real club-owner relationships, national-team availability, costs and coach trust.

### Stage C: chairman–coach meeting

The president sets the political mandate without taking over tactics:

- publicly back the coach and technical autonomy;
- publicly demand points;
- set a private target without a public score promise.

The mandate changes public expectation, coach pressure and the working relationship.

### Stage D: matchday

Once the preparation chain is complete, adaptive time can move toward the official match. The match itself remains part of the authoritative football engine.

### Stage E: post-match review

After the result, time freezes again. The chairman must choose:

- public institutional responsibility and continued backing;
- a technical review without a predetermined personnel outcome;
- immediate coach dismissal and emergency succession.

The result cannot be rewritten by the review decision.

## 5. Temporary match preparation

Camp, club release, squad availability, fitness and the chairman–coach relationship can create a temporary readiness modifier for one match.

The modifier is applied through the ordered presidential-action history before the monthly match settlement and removed through another ordered action after the result.

This guarantees:

- better preparation can influence the current match;
- expensive camps do not permanently manufacture national-team strength;
- save/reload reconstructs the same preparation and result state;
- the permanent national-team trajectory still comes from the football engine, player development and match outcomes.

The regression suite verifies that the preparation and restoration deltas sum to zero in the authoritative replay stream.

## 6. Adaptive-time integration

The following match-window stages are hard stops:

- camp authorization;
- unresolved club-release dispute;
- unfinished chairman–coach meeting;
- post-match accountability.

The completed preparation stage is not a hard stop. Time moves in short increments toward the match and cannot silently jump past the result.

A legacy save already at or beyond a fixture's match month does not reopen that completed fixture.

## 7. Replay and save compatibility

Presidential save format 10 adds:

- serving coach and coach history;
- every national-team match window;
- coach-selected squads;
- club-release disputes and resolutions;
- preparation choices and costs;
- temporary match modifiers;
- official results;
- post-match decisions.

Version-9 adaptive-time saves and version-8 executive-office saves remain loadable. They receive a fresh matchday runtime after their existing fingerprints are verified.

Matchday changes to treasury, supporter trust and club-owner relationships are written into the same ordered external-action stream as other presidential office decisions. They are not one-off in-memory mutations.

## 8. Player-facing information boundary

The command center displays institutional facts and public assessments. It does not reveal:

- exact hidden coaching ability;
- a secret objectively optimal formation;
- private player-selection probability;
- hidden club-owner motives;
- the exact deterministic match probability.

The purpose is to make national-team responsibility feel real, not to give the chairman omniscient control over football.