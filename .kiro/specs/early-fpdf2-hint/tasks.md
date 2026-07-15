# Implementation Plan: Early fpdf2 Hint

- [x] 1. Add the Module 1 early-hint step
  - In `module-01-*.md`, at the module-completion recap (a non-interrupting
    point), run `python3 senzing-bootcamp/scripts/fpdf2_preflight.py`; if it
    prints a hint (fpdf2 absent), surface a one-line message that installing
    `fpdf2` upgrades the final recap PDF and that a valid PDF is produced either
    way. Silent when fpdf2 is present.
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Make it one-time (no nagging)
  - Guard on a `fpdf2_hint_shown` flag in `config/bootcamp_preferences.yaml`:
    skip if already set; set it after surfacing. Bounded to at most once per
    project across resumes/revisits.
  - _Requirements: 2.2_

- [x] 3. Non-blocking / optional / lazy-import guarantees
  - No 👉 question, no gate, no required action, no auto-install during Module 1;
    a preflight failure degrades to a silent no-op. No top-level `import fpdf`;
    graduation-time tiered render + late preflight unchanged.
  - _Requirements: 2.1, 2.3, 2.4, 3.1, 3.2_

- [x] 4*. (Optional) Tests
  - Steering-content: Module 1 invokes fpdf2_preflight at a non-interrupting
    point, frames the hint as an upgrade (not a requirement), guards on
    `fpdf2_hint_shown`, adds no 👉/gate. Optional preference-flag round-trip.
    Follow repo pytest conventions.
  - _Requirements: 1.x, 2.x, 3.x_
