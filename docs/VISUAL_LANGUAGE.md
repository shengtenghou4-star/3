# Presidential Office Visual Language

Version 0.16 improves the visual appeal of the fixed-player football-association president simulator without changing the player's authority or exposing hidden simulation values.

## Design principle

Every visual object must represent a real state or action.

- A red folder appears because a presidential dossier is pending.
- The red-line telephone reflects current correspondence and contact pressure.
- The media screen reflects current press clippings and questions.
- The supervision folder reflects active named implementation mandates.
- Pressure lights reflect pending signatures, unassigned mandates, delayed delivery, leaks or open press conferences.

The interface does not invent ornamental crises or display fake completion percentages.

## Presidential office

The main header is staged as a working presidential office rather than a generic application banner. It contains:

- the association seal;
- the fixed player's name and role;
- date, term and office location;
- the secretary-general's current situation line;
- state-driven pressure lights.

The scene remains readable on mobile and removes decorative motion when the user prefers reduced motion.

## Chairman's desk

The desk contains four physical objects:

1. presidential in-tray;
2. red-line telephone;
3. media screen;
4. supervision folder.

Their badges are counts of real dossiers, correspondence, press items and active mandates. They are not abstract performance metrics.

## Named implementation

Each mandate is presented as a stamped supervision order followed by a four-stage lifecycle:

```text
presidential signature
-> named assignment
-> departmental delivery
-> supervision review
```

The highlighted phase is derived from the public mandate status. Delay, narrowing and failure use warning states, but the player still cannot see hidden delivery quality or distortion calculations.

Named officials receive role sigils and public-status cards. These cards identify responsibility; they do not reveal competence, loyalty, integrity or network scores.

## Competing reports

Reports are shown as separate institutional documents with different visual identities for the secretariat, finance, integrity, technical and grassroots offices.

Color identifies the submitting institution, not truth. Every report still exposes its recommendation, evidence, confidence and blind spot. The game never marks one document as the correct answer.

## Meeting room

The meeting page stages the chairman and visitor across a conference table. The visitor's ask, offer, avoided subject and the chairman's questions remain the substantive core.

The scene does not imply that a meeting has occurred until the player chooses an access decision and the causal meeting record is written.

## Press room

Press conferences are displayed with a podium, microphones, reporter seats and alternating reporter/president transcript blocks.

The scene is generated from the actual press session. Exact quotes and follow-up questions remain part of the long-term media-accountability system.

## Technical limits

- No external image or CDN dependency.
- No tracking or analytics.
- No reintroduction of a metric wall.
- No hidden official or stakeholder scores in visual components.
- Responsive layouts at desktop, tablet and mobile widths.
- Reduced-motion support.
- Existing saves, decisions and causal systems remain authoritative.