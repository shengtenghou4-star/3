# Fixed Chairman Player Perspective

Implemented as the default long-term player contract in Football Republic 0.13.0.

Football Republic is a football-association chairman simulator. The player controls one person: the opening national-association chairman.

## Player identity

The player's identity never transfers to another politician.

```text
renewed in office
-> continue playing the same chairman

resignation, removal, electoral defeat or consecutive-term limit
-> playable career ends
-> personal legacy report
-> optional observer mode
```

Observer mode allows the football world to continue. Successor governments make their own decisions automatically. The player cannot sign documents, choose their candidates or negotiate their coalition agreements.

## Chairman powers

The player can:

- appoint and dismiss national-association officials;
- sign budgets and association programs;
- propose licensing, competition, transfer and youth-development policy;
- negotiate with ministries, regional associations, clubs, broadcasters, sponsors, players and supporters;
- decide whether credible allegations go to independent investigation, internal review or no formal referral;
- choose national-team strategy and respond to coaching crises;
- campaign for renewal and manage the incumbent governing coalition.

The player cannot directly:

- order a club to buy, sell or select a player;
- force a player to accept a contract;
- decide stakeholder votes;
- make a sponsor continue funding;
- dictate a prosecutor's charging decision or a court verdict;
- select or bargain on behalf of a successor after leaving office.

## Information boundary

The underlying simulation continues to track exact competence, integrity, loyalty, network power, evidence and stakeholder support. These values are not displayed directly to the player.

The chairman receives:

- official reports;
- public records;
- broad relationship signals;
- work-delivery assessments;
- confidence-rated intelligence;
- unverified rumors;
- formal investigation updates.

A rumor may reveal a possible relationship, but not its hidden numerical strength or whether an allegation is true. A public case docket shows the procedural stage and public outcome, not conviction probability or hidden evidence calculations.

## Chairman office interface

The main history command opens eight player-facing areas:

1. chairman office and pending files;
2. national football overview;
3. national team and competitions;
4. professional leagues and clubs;
5. youth and grassroots football;
6. finance, audit and personnel;
7. political support and renewal;
8. personal career and legacy.

The raw political-person database, hidden patronage graph and justice-engine probabilities remain internal simulation tools rather than player dashboards.

## Career end

A career ending is a game result, not a character switch. The legacy report records:

- months and complete terms in office;
- exit reason;
- board and political performance;
- treasury, trust, integrity and national-team state;
- major decisions;
- championships during the player's tenure;
- an overall historical legacy grade.

A saved game preserves the opening chairman identity, career-end month and reason, and observer state. Loading a save cannot restore player control after the chairman has left office.
