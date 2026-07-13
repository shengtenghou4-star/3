# Football Republic

**A fixed-player national football association chairman simulator**

Football Republic puts the player in one office: the chair of a national football association.

You can sign budgets, appoint association officials, propose competition and registration rules, negotiate with ministries and clubs, manage the national-team strategy, refer allegations for investigation and fight for renewal. You do not directly control club transfers, player contracts, stakeholder votes, sponsor decisions, prosecutors, courts or successor governments.

The simulation underneath the office remains deep and persistent. Clubs, owners, players, officials, ministries, regional associations, broadcasters, sponsors, unions and supporters pursue their own interests.

## Main chairman career

```bash
python -m pip install -e '.[dev,ui]'
football-republic-history
```

This is the main long-term mode.

The player remains the same opening chairman throughout the playable career:

```text
renewed in office
  -> continue as the same chairman

resignation, removal, electoral defeat or term limit
  -> playable career ends
  -> personal legacy report
  -> optional observer mode
```

Observer mode continues the football world, but successor governments make their own decisions. The player cannot select their candidates, bargain for their coalitions or sign their files.

The chairman office contains:

1. chairman briefings and pending files;
2. national football overview;
3. national team and competitions;
4. professional leagues and clubs;
5. youth and grassroots football;
6. finance, audit and personnel;
7. political support and renewal;
8. personal career and legacy.

## Information is limited to the chairman's perspective

The simulation tracks exact private attributes for NPCs, including competence, integrity, loyalty, network power, evidence and stakeholder support. The player does not see those raw values.

The chairman receives:

- official reports;
- public records;
- work-delivery assessments;
- broad political signals;
- confidence-rated intelligence;
- unverified rumors;
- formal investigation updates.

A rumor can indicate a possible relationship but cannot prove misconduct. A public case docket shows procedural stage and outcome, not hidden conviction probability or evidence calculations.

See [`docs/PLAYER_PERSPECTIVE.md`](docs/PLAYER_PERSPECTIVE.md).

## Other playable modes

### Standard 24-month campaign

```bash
football-republic-web
```

The original vertical slice with six top-flight clubs, national programmes, transfers, World Cup qualifying and a board-confidence review.

### Two-year deep ecosystem

```bash
football-republic-deep
```

A two-year version of the full professional and political ecosystem without the long personal-career wrapper.

## Football ecosystem

The deep simulation includes:

- fourteen professional clubs across two divisions;
- complete double round-robin seasons;
- promotion, relegation and a play-off;
- a fourteen-club national cup;
- an eight-club continental champions competition;
- central media-rights distribution;
- stadium capacity, ticket pricing, maintenance and expansion;
- commercial sponsorship and morality clauses;
- administration, points deductions, liquidation and phoenix clubs;
- persistent owners with bailout memory;
- contracts, free agency and development loans;
- squad registration, foreign-player limits and homegrown quotas;
- academy graduation and player retirement;
- congestion, travel fatigue and injury risk;
- national-team selection from the shared club-player database.

### Promotion and licensing

A second-division club cannot be promoted by points alone. It must also satisfy professional licensing, solvency and wage-arrears requirements.

```text
league position
+ licence compliance
+ financial viability
+ paid players
= promotion eligibility
```

### Club finance

Clubs receive gate income, media distributions, sponsorship, prize money and commercial revenue. They pay wages, stadium maintenance, debt costs and transfer expenditure.

Sustained failure can lead to:

```text
wage arrears
-> administration
-> points deduction
-> owner rescue or failed restructuring
-> licence withdrawal
-> liquidation
-> supporter-backed phoenix club
```

### Contracts and registration

Players can renew, reject offers, reach free agency or move on development loans. Registration law changes according to the chairman's transfer-policy decision.

Unregistered players remain under contract but cannot play league, cup or continental matches and cannot be selected for the national team.

### Academy and retirement

Every season produces academy graduates and possible retirements. School football, coach coverage, match volume, facilities and regional execution influence the future player pool.

## Political economy

Nine persistent stakeholder blocs influence the association:

- national sports authorities;
- finance authorities;
- education authorities;
- provincial associations and local governments;
- professional club owners;
- the players' union;
- broadcasters and digital platforms;
- sponsors;
- supporters and community clubs.

They have distinct interests and are not automatically obedient.

The chairman can propose legislation, negotiate support and make public promises. Failed legislation receives only a limited executive version. Broken promises damage support, trust and future coalition building.

## Cabinet and constitutional government

The association has five senior offices:

- secretary-general;
- finance and licensing director;
- integrity and discipline commissioner;
- national-team technical director;
- grassroots and school-football commissioner.

Officials have persistent careers. Governments can face scandal, resignation, no-confidence removal, caretaker administration and snap elections while football competitions continue.

The player does not control a successor after leaving office.

## Elections and coalition government

Stakeholder blocs cast weighted votes. Candidates may seek clean mandates or exchange offices, budgets and policy commitments for support.

Coalition agreements create real obligations. Overpromising can produce broken commitments, minority government, confidence votes and collapse.

For the player, these systems matter only while the opening chairman remains in office. A failed renewal ends the playable career instead of transferring control to the winner.

## Political people and justice

Named NPCs can move between ministries, regional associations, league organizations, the national association and presidential candidacy.

Relationships may be family, professional, commercial, alumni, mentor or patronage ties. A relationship is not itself wrongdoing. Legal exposure rises when strong undisclosed relationships overlap with appointments, contracts or licensing authority.

The chairman chooses only the referral route:

- independent investigation;
- internal disciplinary review;
- no formal referral or political suppression.

Evidence, prosecutor capacity, institutional independence and interference determine charging, trial and appeal outcomes. The chairman cannot choose guilt.

## Long-term continuity

The football nation can continue for twenty seasons without resetting:

- clubs retain money, debt, licences and identities;
- players retain age, contracts, form and career history;
- owners retain wealth, patience and bailout memory;
- stadiums and sponsorships persist;
- stakeholder relationships and promises persist;
- officials retain careers and legal history;
- competitions receive new schedules without recreating the world.

## Safe saves

The chairman career uses UTF-8 JSON saves and deterministic chronological replay.

The fingerprint covers:

- the fixed player-chairman identity;
- career end and observer state;
- clubs, players, finances and competitions;
- political relationships and coalition agreements;
- cabinet appointments and government transitions;
- people, patronage ties, cases, trials and appeals.

A save cannot restore player control after the chairman has left office.

## Development

```bash
pytest -q
```

The design rule is simple: important outcomes must be traceable through money, facilities, political power, information limits, appointments, trust, promises, capacity, incentives, delay, compliance, player quality, ownership, contracts, registration, workload, governance decisions and match events.

No scripted champions, protected clubs, omniscient player dashboards or unexplained score jumps.

See:

- [`docs/PLAYER_PERSPECTIVE.md`](docs/PLAYER_PERSPECTIVE.md)
- [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md)
- [`docs/LONG_TERM.md`](docs/LONG_TERM.md)
- [`docs/CONSTITUTIONAL_GOVERNMENT.md`](docs/CONSTITUTIONAL_GOVERNMENT.md)
- [`docs/POLITICAL_CAREERS_JUSTICE.md`](docs/POLITICAL_CAREERS_JUSTICE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
