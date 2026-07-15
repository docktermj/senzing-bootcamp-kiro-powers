# Implementation Plan: Conversational Self-Audit Hook

- [x] 1. Define the precise 👉 leading-question counting rule
  - Codify the counting rule from the design (first non-whitespace,
    non-blockquote, non-bold content begins with 👉; exclude code fences, inline
    code, quoted prior-turn examples, and the internal `🛑`/`⛔` markers).
  - Specify the `config/.question_pending` cross-check.
  - _Requirements: 1.1, 1.5_

- [x] 2. Add the Leading-Question Count Audit phase to `ask-bootcamper`
  - Insert a new phase after Phase 1 (Closing Question): count leading questions;
    exactly one → silent pass; zero on a substantive turn → missing-question
    self-correction; two-plus → multiple-questions self-correction (re-render to
    one; fold alternatives into a numbered list).
  - Ensure the phase produces no output for non-yielding turns, silent
    pass-throughs, and the DEFAULT-OUTPUT period (Req 1.5, 2.x).
  - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.3_

- [x] 3. Keep it lightweight and off the write path
  - Default cadence: every Yielding_Turn. Add an optional `sampling_rate` knob
    in `config/bootcamp_preferences.yaml` for reduced cadence.
  - Confirm no per-write / PostToolUse-on-write coupling is introduced.
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Non-blocking / never-worsen guarantees
  - The audit is a Soft_Block at most; errors degrade to a silent no-op; the
    self-correction output carries at most one 👉 and no compound question.
  - _Requirements: 2.2, 2.4, 3.x_

- [x] 5. Regenerate registry + lock and re-sync steering budget
  - `sync_hook_registry.py --write` (then `--verify` = 0); re-sync
    `steering-index.yaml` counts + budget total (`measure_steering.py --check` = 0).
  - _Requirements: 4.1, 4.2_

- [x] 6*. (Optional) Property/example tests for the counting rule and phases
  - Synthetic rendered turns (zero/one/many 👉, code-fenced 👉, quoted examples,
    blockquote/bold-wrapped 👉) asserting P1-P4. Follow repo pytest + Hypothesis
    conventions.
  - _Requirements: 1.x, 2.x_
