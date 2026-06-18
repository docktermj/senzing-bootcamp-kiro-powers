# Implementation Plan: Leading-Question Continuity

## Overview

This plan implements two independent outcomes from the design, each in a different artifact class, plus the property-based tests and CI/verification steps that guard them:

- **Outcome A (steering Markdown):** Add an Intercept-Recovery Continuity rule to `senzing-bootcamp/steering/conversation-protocol.md` and a minimal reinforcement to `senzing-bootcamp/steering/agent-behavior-rules.md`, guaranteeing every yielding turn ends with exactly one pointing-hand leading question and `config/.question_pending` is written — including intercept-recovery turns.
- **Outcome B (hook JSON prompt):** Add exactly two exact-match entries (`config/data_sources.yaml`, `config/visualization_tracker.json`) to the INTERNAL-FILE PASS-THROUGH enumeration in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`'s `then.prompt`, preserving all NOT-guards, the FAST PATH GATE, and CHECK 1–4 byte-for-byte.

Ordering is incremental: the hook prompt edit lands before its property tests; steering edits land before their property tests; CI/verification steps run after the artifacts they validate. All test code follows repo Python conventions (Python 3.11+, stdlib-only helpers, type hints, Google-style docstrings, pytest + Hypothesis, class-based, strategies prefixed `st_`, ≥100 iterations for property tests, each property-test class tagged `# Feature: leading-question-continuity, Property N`).

## Tasks

- [x] 1. Outcome B — Extend the pass-through enumeration in the hook prompt
  - [x] 1.1 Add the two exact-match pass-through entries to the hook prompt
    - Edit only the `then.prompt` string value in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`
    - In the "Routine power-managed internal files (the exact set — do not over-match)" enumeration of the INTERNAL-FILE PASS-THROUGH block, add exactly two lines: `config/data_sources.yaml` and `config/visualization_tracker.json`
    - Do NOT modify any structural field (`name`, `version`, `when`, `then.type`); do NOT alter the NOT-guard block, the FAST PATH GATE, or CHECK 1–4 (must stay byte-for-byte identical)
    - Validate JSON validity with `get_diagnostics` after the edit
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 1.2 Write property test: new routine config files pass through silently
    - New file `tests/test_leading_question_continuity_passthrough_properties.py`
    - **Property 3: New routine config files pass through silently on first attempt**
    - **Validates: Requirements 3.1, 3.2, 3.4**
    - Drive `gate_decision_model.gate()` over the live prompt; `st_` strategy generates NOT-guard-clean content for the two new exact paths; assert `PASS_SILENT` with `intercepted = False` and that each literal path appears in the `then.prompt` enumeration

  - [x] 1.3 Write property test: existing pass-through entries still pass silently (preservation)
    - Add to `tests/test_leading_question_continuity_passthrough_properties.py`
    - **Property 4: Existing pass-through entries still pass through silently**
    - **Validates: Requirements 3.3**
    - `st_` strategy generates the existing exact paths, `config/progress_{id}.json` / `config/preferences_{id}.yaml` regex instances, and `docs/progress/MODULE_*_COMPLETE.md` instances with NOT-guard-clean content; assert `PASS_SILENT` with `intercepted = False`

  - [x] 1.4 Write property test: pass-through membership is exact-match only
    - Add to `tests/test_leading_question_continuity_passthrough_properties.py`
    - **Property 5: Pass-through membership is exact-match only**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - `st_` strategy generates near-miss mutations (changed extension `.yml`, added suffix `.bak`, extra parent dir `sub/config/...`, case change `DATA_SOURCES.yaml`); assert the gate does not grant silent pass-through and routes to the four security checks

- [x] 2. Outcome B — Guard the security checks and no-new-strings invariant
  - [x] 2.1 Write property test: any NOT-guard failure declines pass-through and routes to checks
    - New file `tests/test_leading_question_continuity_notguard_properties.py`
    - **Property 6: Any NOT-guard failure declines pass-through and routes to the security checks**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    - `st_` strategy pairs each pass-through path with each injected NOT-guard violation (Senzing SQL → `senzing_sql`, feedback file → `feedback_append_only`, `config/.question_pending` → `single_question`, root-blocked placement → `root_placement`); assert `INTERCEPT_CORRECTIVE` with the matching corrective category

  - [x] 2.2 Write property test: the pass-through extension introduces no new output strings
    - New file `tests/test_leading_question_continuity_baseline_properties.py`
    - **Property 7: The pass-through extension introduces no new output strings**
    - **Validates: Requirements 3.4, 5.1, 5.2, 5.3, 5.4**
    - Assert the INTERNAL-FILE PASS-THROUGH block still instructs a zero-token silent outcome and that the FAST PATH GATE and CHECK 1–4 text in the live `then.prompt` are byte-for-byte identical to the established baseline

  - [x] 2.3 Write hook schema-conformance and enumeration-diff unit tests
    - Add to `tests/test_leading_question_continuity_baseline_properties.py` (example-based assertions)
    - Assert the edited hook still has `name`, `version`, `when.type == preToolUse`, `when.toolTypes == ["write"]`, `then.type == askAgent`, non-empty `then.prompt`
    - Diff-style assertion: both new literal path strings are present AND the two new lines are the only additions to the pass-through enumeration vs. the baseline
    - _Requirements: 4.1, 5.3_

- [x] 3. Checkpoint — Outcome B gate behavior verified
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Outcome A — Add the Intercept-Recovery Continuity rule to steering
  - [x] 4.1 Add the Intercept-Recovery Continuity subsection to `conversation-protocol.md`
    - Edit `senzing-bootcamp/steering/conversation-protocol.md`
    - Add an explicit **Intercept-Recovery Continuity** subsection to the End-of-Turn Protocol: when a turn's primary action was a write re-issued after a `write-policy-gate` intercept, the turn is not complete until exactly one pointing-hand leading question reflecting the next step is appended and `config/.question_pending` is written
    - Classify a bare-acknowledgment ("." / empty) outcome on an intercept-recovery turn as a protocol violation equivalent to a dead-end response
    - Do NOT remove existing rule text; keep the One Question Rule and Question Stop Protocol intact (they govern question shape); state the closing question is the agent's responsibility and is not deferred to a hook; keep the addition minimal for token budget
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_

  - [x] 4.2 Reinforce the no-dead-end obligation in `agent-behavior-rules.md`
    - Edit `senzing-bootcamp/steering/agent-behavior-rules.md`
    - Add a short clarification cross-referencing the conversation-protocol rule: an intercept/retry cycle does not relieve the agent of the closing-question obligation; a re-issued write is "work completed in the turn" and still requires the pointing-hand call-to-action (Rule 4)
    - Keep the addition minimal to respect token budgets
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 4.3 Write property test: every yielding turn ends with exactly one leading question
    - New file `senzing-bootcamp/tests/test_leading_question_continuity_turn_properties.py`
    - **Property 1: Every yielding turn ends with exactly one leading question**
    - **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**
    - Model a turn as `(primary_action, yields, leading_question_count)`; `st_` strategy varies `primary_action` (especially `reissued_write_after_intercept`) with `yields=True`; assert `yields` implies `leading_question_count == 1`, and assert `conversation-protocol.md` content states the intercept-recovery continuity rule and `config/.question_pending` write

  - [x] 4.4 Write property test: leading questions are single and unambiguous
    - Add to `senzing-bootcamp/tests/test_leading_question_continuity_turn_properties.py`
    - **Property 2: Leading questions are single and unambiguous**
    - **Validates: Requirements 1.4**
    - `st_` strategy generates single vs. compound/ambiguous question strings; assert the single-question detector accepts exactly-one-question-mark / no-conjunction / no-appended-alternative strings and rejects compound or ambiguous ones, consistent with the One Question Rule text

  - [x] 4.5 Write example test: closing question is the agent's responsibility (not deferred to a hook)
    - Add to `senzing-bootcamp/tests/test_leading_question_continuity_turn_properties.py`
    - Example-based assertion that `conversation-protocol.md` states the closing question is owned by the agent and is not deferred to the `ask-bootcamper` hook
    - _Requirements: 2.4_

- [x] 5. Checkpoint — Outcome A steering behavior verified
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. CI / verification integration
  - [x] 6.1 Update steering token budgets and verify
    - Update the `senzing-bootcamp/steering/steering-index.yaml` token-budget entries for `conversation-protocol.md` and `agent-behavior-rules.md` to reflect the additions
    - Run `measure_steering.py --check` and confirm it passes
    - _Requirements: 1.1, 2.1_

  - [x] 6.2 Verify hook registry sync after the prompt edit
    - Run `sync_hook_registry.py --verify` and confirm the registry matches the edited `write-policy-gate.kiro.hook`
    - _Requirements: 3.1, 3.2_

  - [x] 6.3 Validate CommonMark of edited steering files
    - Run `validate_commonmark.py` on `conversation-protocol.md` and `agent-behavior-rules.md` and confirm validity
    - _Requirements: 1.2_

  - [x] 6.4 Validate overall power structure
    - Run `validate_power.py` and confirm it passes
    - _Requirements: 3.3, 4.1_

  - [x] 6.5 Run the full pytest suite (power + repo-root)
    - Run the complete pytest suite with `--run` semantics (single execution, no watch mode), including existing `test_write_policy_gate_*` and `test_consolidated_hook_properties.py`, to confirm no regression alongside the new property tests
    - _Requirements: 3.3, 4.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Final checkpoint — Ensure all tests and CI checks pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP. All property tests and the full-suite run are marked optional per repo testing conventions; core artifact edits and the deterministic CI verifications (budget, registry, CommonMark, power structure) are required.
- Each task references the specific requirements and/or design properties it implements for traceability.
- Outcome B properties (3–7) exercise the live hook prompt via `tests/gate_decision_model.py`; Outcome A properties (1–2) run against a turn model and the live steering content.
- Hook/steering validation tests live in repo-root `tests/`; power-behavior tests live in `senzing-bootcamp/tests/`.
- The hook prompt edit (1.1) precedes its property tests (1.2–2.3); steering edits (4.1–4.2) precede their property tests (4.3–4.5); CI/verification (task 6) runs after the artifacts it validates.
- Property tests use pytest + Hypothesis, class-based, `@settings(max_examples=...)` ≥ 100, `st_`-prefixed strategies, and each property-test class is tagged `# Feature: leading-question-continuity, Property N`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1", "4.2"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "2.1", "2.2", "2.3", "4.3", "4.4", "4.5", "6.1", "6.2", "6.3", "6.4"] },
    { "id": 2, "tasks": ["6.5"] }
  ]
}
```
