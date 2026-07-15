# Design Document: Entity Resolution Intro Interactive Illustration

## Overview

Add an optional, conceptual **two-record match / no-match illustration** to
`entity-resolution-intro.md`, offered before the mandatory Exploration_Gate. It
makes the false-positive/false-negative idea concrete during the preface without
the SDK, a database, or any code — a lightweight teaser that points forward to
the Module 3 hands-on "wow" visualization.

## Placement in the intro flow

`entity-resolution-intro.md` today: ER_Concepts_Banner → "what ER is / why hard /
pipeline / relationships / outputs" → ⛔ Exploration_Gate. The illustration slots
in as an **offer** in the "Explore Further" area, before/at the gate:

- After the outputs section and before (or as the first option within) the
  Exploration_Gate, present a single 👉 Illustration_Offer: "Want to see a quick
  two-record example of a match and a non-match before we move on?"
- Accept → render the ER_Illustration inline, then re-present the gate.
- Decline / readiness signal → proceed exactly as the existing gate defines.

The offer is one non-compound 👉, verbosity-aware, and does not change the
gate's wait semantics or the once-only banner rule.

## ER_Illustration content

Two record pairs, rendered inline as plain text/markdown (no graph, no server):

- **Match pair** — same real-world entity despite surface differences, e.g. a
  name variation + an address-over-time change that still resolve to one person;
  one or two lines of reasoning: "same entity — the nickname and prior address
  are consistent with one person; missing this would be a false negative."
- **Non-match / possible-match pair** — similar surface attributes, different
  entities, e.g. a shared name at a shared address (father/son); reasoning:
  "different entities — collapsing these would be a false positive; a capable
  engine keeps them apart or flags a possible match."

Sourcing (MCP-first): prefer `find_examples` / `search_docs` from the Senzing MCP
server for realistic, current example records and reasoning; when unavailable,
fall back to a clearly-generic pair (marked as illustrative). This mirrors the
intro's existing MCP-first, no-training-data sourcing discipline.

## Interaction with the Exploration_Gate

- The gate is unchanged: it still waits for a real readiness signal or a
  follow-up question, still answers follow-ups via MCP then re-presents, and the
  ER_Concepts_Banner is still shown exactly once per preface run.
- The illustration is one of the things a curious bootcamper can do at the gate;
  after viewing it (and any follow-ups), control returns to the gate.

## Relationship to Module 3

The illustration is explicitly framed as a **preview**. It must not render the
interactive entity graph, start the visualization web service, or otherwise
reproduce Module 3. The intro points forward: "In Module 3 you'll see this on
real data with an interactive visualization."

## Correctness properties

- **P1 (optional):** declining the offer proceeds with no penalty and no state
  change beyond the normal gate flow.
- **P2 (gate-preserving):** the offer/illustration never change the
  Exploration_Gate wait semantics or the once-only banner.
- **P3 (self-contained):** rendering the illustration requires no SDK, database,
  loaded data, or code execution.
- **P4 (MCP-first):** when MCP examples are available they are the source; the
  generic fallback is clearly marked generic.
- **P5 (non-duplication):** the illustration renders no interactive graph and
  starts no server; it points forward to Module 3.
- **P6 (one-question):** the offer is exactly one non-compound 👉.

## Testing notes

Steering-content tests (like the other intro/steering suites): assert the offer
text is a single 👉 non-compound question, that the illustration section is
present with a match and a non-match/possible-match pair, that it references
MCP-sourced examples with a generic fallback, that it carries no server/graph
rendering instructions, and that the Exploration_Gate wording and once-only
banner are preserved. Follow repo pytest conventions. Tests optional at spec time.
