# Implementation Plan: Entity Resolution Intro Interactive Illustration

- [x] 1. Add the Illustration_Offer to `entity-resolution-intro.md`
  - In the "Explore Further" area, before/at the Exploration_Gate, add a single
    non-compound 👉 offer to view a two-record match / non-match example.
  - Preserve the ⛔ gate wait semantics and the once-only ER_Concepts_Banner.
  - _Requirements: 1.1, 2.2, 2.3_

- [x] 2. Author the ER_Illustration content (MCP-first, self-contained)
  - On accept, render a **match** pair and a **non-match/possible-match** pair
    with 1-2 lines of reasoning each, tied to name-variation / address-over-time
    / false-positive-vs-false-negative.
  - Source example records/reasoning from `find_examples` / `search_docs`;
    fall back to a clearly-generic pair when MCP examples are unavailable.
  - No SDK, database, loaded data, or code execution.
  - _Requirements: 1.2, 1.3, 1.4, 2.4_

- [x] 3. Frame as a preview; do not duplicate Module 3
  - Point forward to the Module 3 hands-on visualization; render no interactive
    graph and start no web service in the preface.
  - _Requirements: 3.1, 3.2_

- [x] 4. Re-sync steering budget
  - If the intro file grows, re-sync `steering-index.yaml` token count + budget
    total and confirm `measure_steering.py --check` = 0; keep it within its
    token band (trim agent-only comments if needed).
  - _Requirements: (build hygiene)_

- [x] 5*. (Optional) Steering-content tests
  - Assert: single non-compound 👉 offer; illustration has a match and a
    non-match/possible-match pair; MCP-first sourcing with generic fallback; no
    server/graph rendering instructions; gate wording + once-only banner
    preserved. Follow repo pytest conventions.
  - _Requirements: 1.x, 2.x, 3.x_
