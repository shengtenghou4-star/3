# Football Republic

**A National Football Governance Simulator**

Football Republic puts the player in charge of an entire national football system. The president controls regulation, funding, club licensing, youth development, transfer policy and national teams, but ministries, local associations, club owners, players, broadcasters, sponsors and supporters pursue their own interests.

## Playable modes

### Standard presidential campaign

```bash
python -m pip install -e '.[dev,ui]'
football-republic-web
```

The original 24-month vertical slice: six top-flight clubs, national programmes, cabinet decisions, transfers, World Cup qualifying and a board-confidence review.

### Deep professional and political ecosystem

```bash
python -m pip install -e '.[dev,ui]'
football-republic-deep
```

The deep mode connects:

- nine persistent political stakeholder blocs;
- four national football congress agendas with coalition voting;
- measurable public promises and long-term relationship memory;
- political pressure, cooperation, protests, labor conflict and delayed grants;
- fourteen professional clubs across two divisions;
- complete league seasons, promotion, relegation and a play-off;
- a fourteen-club national knockout cup;
- an eight-club continental champions competition;
- central media-rights distributions;
- stadium capacity, ticket pricing, maintenance and expansion;
- commercial sponsorship contracts and morality clauses;
- administration, points deductions, liquidation and phoenix clubs;
- persistent club owners with bailout memory;
- contracts, free agency and development loans;
- squad registration, foreign-player limits and homegrown quotas;
- annual academy graduations and player retirement;
- schedule congestion, travel fatigue and injury risk;
- a twenty-six-player national squad selected from the club database;
- annual political and sporting history plus a second-term coalition review.

### Continuous twenty-year government history

```bash
python -m pip install -e '.[dev,ui]'
football-republic-history
```

The history mode chains up to ten two-year institutional terms and twenty seasons without resetting the nation. Schedules are rebuilt at formal term boundaries, while clubs, players, owners, debt, stadiums, sponsorships, laws and stakeholder relationships persist.

The long-term government mode adds:

- five named senior association officials with competence, integrity, loyalty and network power;
- cabinet quality affecting administration, finance, integrity, grassroots work and national-team preparation every month;
- endogenous scandal risk from loyal, networked and low-integrity appointments;
- independent inquiries, cabinet reshuffles and protection of political loyalists;
- voluntary resignation and no-confidence removal before a formal term ends;
- caretaker administrations and snap elections while competitions continue;
- multiple governments inside one formal two-year institutional cycle;
- incumbent renewal, contested conventions and coalition-driven scheduled succession;
- a maximum of three consecutive presidential terms;
- successors who inherit the actual institutional and financial state;
- globally unique academy cohorts beyond season two;
- global administration, appointment, constitutional, club, player, champion, stadium, sponsorship and insolvency archives;
- safe UTF-8 JSON saves based on deterministic chronological decision-log replay;
- fingerprint verification that rejects corrupted or incompatible saves.

The standard and two-year deep modes remain available and unchanged.

## Stakeholder political economy

The president does not receive automatic obedience. Nine blocs have distinct power, support, trust, patience, mobilization and policy preferences:

- national sports authorities;
- the finance ministry;
- the education ministry;
- provincial football associations and local governments;
- the professional club owners' council;
- the players' union;
- broadcasters and digital platforms;
- the major sponsor council;
- the national supporters federation.

Every existing crisis decision now changes persistent relationships. A transparent investigation may strengthen sponsors and supporters while angering local administrators. An unconditional club bailout may please owners while damaging the finance ministry and integrity coalition.

Low-support, high-power blocs can create material pressure:

```text
finance ministry opposition
  -> grant payments delayed

players' union opposition
  -> player morale falls and labor action escalates

sponsor opposition
  -> a real sponsorship contract is suspended
  -> monthly club revenue is removed

local-government opposition
  -> implementation capacity falls
```

Strong, trusted allies can also deliver grants, school access, owner cooperation, medical programmes and public endorsements.

## National football congress

Four major institutional agendas appear during the term:

1. central versus local governance authority;
2. player welfare versus commercial calendar freedom;
3. solidarity distribution versus star-club growth;
4. independent integrity enforcement versus protected delivery.

Stakeholders vote according to their preferences, current support, trust and patience. A proposal can fail. If support is close to half and the president has enough political capital, it can be forced through at a political cost.

Failed legislation does not receive full effects. Only a limited executive directive—22% of the intended reform—takes effect.

## Public promises and political memory

A passed agenda creates a measurable public promise with:

- a baseline;
- a target metric;
- a due month;
- named beneficiary groups.

Promises can concern integrity, regional execution, medical quality, league finances or commercial growth. When the deadline arrives, the system compares the actual result with the target.

```text
promise kept
  -> beneficiary support and trust rise
  -> future coalition building becomes easier

promise broken
  -> support and trust fall
  -> mobilization rises
  -> the breach remains in stakeholder memory
```

## Player welfare is a real bargaining outcome

The month-ten labor agreement changes the workload engine itself.

A player-welfare compact reduces:

- congestion fitness losses;
- injury exposure;
- international-release fatigue.

A club-first commercial calendar increases match inventory and recurring revenue, but also increases congestion, injuries and club-versus-country conflict. If the legislation fails, those changes are scaled down rather than applied in full.

## Annual archives and second-term review

At months 12 and 24, the game writes an annual archive containing:

- coalition support and governability;
- treasury, fan trust and integrity;
- youth and national-team development;
- club solvency;
- league and cup champions;
- continental performance;
- strongest ally and opposition leader;
- promises kept and broken;
- all major decisions and political events.

The ordinary board review remains, but the deep mode also calculates a political renewal result. Strong sporting numbers are not enough if the governing coalition has collapsed or the president repeatedly broke public promises.

## Continuous terms and succession

At the end of every 24-month institutional term, football performance and political governability are evaluated together.

An incumbent can win a clear renewal, survive a contested convention, lose office through coalition collapse, lose the football board, or leave after three consecutive terms. The incoming president receives a transition grant based on coalition support, integrity, league health and national-team strength, then scales the opening programme to the treasury that actually exists.

```text
formal term ends
  -> football board review
  -> political coalition review
  -> renewal or scheduled succession
  -> future schedules reset
  -> nation, players, clubs, debt and relationships persist
```

## Cabinet appointments and constitutional crises

The formal competition term no longer guarantees that one president remains in office for all twenty-four months.

Every administration appoints:

- a secretary-general;
- a finance and licensing director;
- an integrity and discipline commissioner;
- a national-team technical director;
- a grassroots and school-football commissioner.

Officials are technocrats, loyalists or coalition brokers. Competence can improve administration and sporting delivery, while high loyalty and network power can improve short-term control. When those strengths are combined with low integrity, institutional-capture and scandal exposure accumulate.

Crisis assessments in months 5, 9, 13, 17 and 21 combine presidential integrity, official integrity, network power, accumulated scandal, coalition support and national integrity reputation.

```text
scandal breaks
  -> independent inquiry, reshuffle, protection or resignation
  -> possible no-confidence majority
  -> caretaker government for up to three months
  -> snap election
  -> same leagues, players, contracts, clubs and debts continue
```

A government can therefore fall in month nine while the current league season continues through month twelve. The new president inherits the existing calendar and cannot claim a duplicate opening budget.

JSON saves store every ordinary and constitutional choice rather than executable objects. Loading reconstructs the original scenario, replays the complete history and verifies a deterministic fingerprint covering the cabinet, caretaker state and football nation before accepting the save.

## Domestic league pyramid

The National Premier League contains six clubs and the National Championship contains eight. Both play full double round-robin seasons.

Promotion is not decided by points alone. A club must also pass:

- professional licensing;
- solvency requirements;
- wage-arrears checks.

A second-division champion can therefore be denied promotion if its finances are fraudulent or its players remain unpaid.

## National FA Cup

All fourteen clubs enter the cup in each season. The two highest-seeded clubs receive first-round byes, followed by quarterfinals, semifinals and a final.

Cup ties use the same player, fitness and match engine as league games. Drawn knockout ties are resolved by penalties. Prize money enters the winning club's real cash balance.

## Continental Champions Cup

Two domestic clubs qualify for an eight-club continental competition containing two groups of four, semifinals and a final.

The first-season representatives are chosen from opening club strength. Later representatives come from prior Premier League results. Clubs receive appearance and progression payments, while away fixtures create extra travel fatigue.

```text
continental qualification
  -> extra prize and gate income
  -> more matches and travel
  -> lower fitness and higher injury risk
  -> deeper squad becomes more valuable
```

## Stadiums and ticket economics

Every club owns a distinct stadium profile with:

- physical capacity;
- facility quality;
- hospitality revenue;
- dynamic ticket pricing;
- monthly maintenance costs;
- possible expansion projects.

Attendance cannot exceed capacity. High utilization raises ticket prices and can encourage an ambitious owner to approve an expansion. Poor maintenance damages stadium quality and pushes costs into debt.

## Sponsorship market

Every season, each club negotiates a commercial contract. Value depends on division level, squad quality, supporter base, integrity and stadium quality.

Sponsorship becomes recurring monthly revenue. League, cup and continental success can trigger bonuses. A serious integrity failure, licence withdrawal or political sponsor revolt can suspend revenue and force a clawback.

## Squad registration policy

The president's month-six transfer-policy choice changes the registration law itself.

```text
homegrown priority
  -> 25-player squad
  -> maximum 4 foreign players
  -> minimum 10 homegrown players

open market
  -> 27-player squad
  -> maximum 7 foreign players
  -> minimum 6 homegrown players

financial control
  -> 24-player squad
  -> maximum 5 foreign players
  -> minimum 8 homegrown players
```

Unregistered players remain under contract and continue training, but cannot play league, cup or continental matches and cannot be selected for the national team. Registration audits occur in months 1, 7, 13 and 19 of each term.

## Contracts, free agents and loans

Players leave clubs when contracts expire unless a renewal is agreed. Clubs decide whether to make an offer based on player importance, age, financial health and wage arrears. Players consider morale, club stability and salary.

Possible outcomes include:

- multi-year renewal;
- release into free agency;
- emergency short extension when a club would fall below minimum squad size;
- free-agent signing without a transfer fee;
- development loan from a Premier League club to a second-division club.

Loans move the real player object, split wages and return the player at the end of the registration period.

## Academy graduation and retirement

The player database is not static. At the end of each season:

- older players can retire based on age and physical decline;
- clubs graduate new seventeen- and eighteen-year-old players;
- academy quality and regional development determine ability and potential;
- new players receive real contracts and wages;
- squad registration decides whether they reach the first team.

This creates a delayed causal chain from school football, coaching and regional infrastructure to future club and national-team quality. In history mode, academy cohort IDs use the global season number and remain unique across twenty seasons.

## Insolvency and phoenix clubs

A club that remains excluded or severely insolvent for three consecutive months can no longer survive as an immortal shell.

```text
sustained insolvency
  -> company liquidation
  -> expensive contracts released
  -> debt haircut
  -> professional licence transferred
  -> supporter-backed community successor
  -> conditional licence and points deduction
```

The successor keeps the football community alive but does not erase the sporting cost of collapse. The phoenix club and supporter trust persist into later presidencies.

## National-team selection

Every international window selects twenty-six eligible Longhua players from the shared club database. Selection considers ability, fitness, injuries, morale, appearances, form, division, registration eligibility, homegrown status and positional quotas.

The match engine combines squad quality with association-level preparation. A president cannot permanently buy national-team strength if the domestic player pool remains weak.

## Development

```bash
pytest -q
```

The design rule is unchanged: important outcomes must remain traceable through money, facilities, political power, appointments, trust, promises, capacity, incentives, delay, compliance, player quality, ownership, contracts, registration, workload, governance decisions and match events. No scripted champions, protected clubs or unexplained score jumps.

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), [`docs/LONG_TERM.md`](docs/LONG_TERM.md), [`docs/CONSTITUTIONAL_GOVERNMENT.md`](docs/CONSTITUTIONAL_GOVERNMENT.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/M1_STATUS.md`](docs/M1_STATUS.md).
