# Implementation Plan: Write-Gate Momentum Preservation

## Overview

This plan locks in the target state for two independently shippable outcomes by editing the live artifacts and guarding them with property-based and example tests against drift:

- **Outcome A (steering):** Edit `senzing-bootcamp/steering/conversation-protocol.md` and `agent-behavior-rules.md` so every yielding turn ends with exactly one `👉` leading question — including intercept-reissued writes — owned by the agent, not a hook.
- **Outcome B (hook):** Extend the `write-policy-gate.kiro.hook` INTERNAL-FILE PASS-THROUGH set with `config/data_sources.yaml` and `config/visualization_tracker.json`, preserving every NOT-guard and the hook's structural integrity.

Implementation language: **Python 3.11+** (stdlib only for scripts; pytest + Hypothesis for tests), per repo tech stack. Tests reuse `tests/gate_decision_model.py` and `tests/hook_test_helpers.py` and live in repo-root `tests/`. Steering edits must stay within the token budgets in `steering-index.yaml`, verified by `measure_steering.py --check`.

## Tasks

- [x] 1. Capture hook baseline and confirm test harness wiring
  - [x] 1.1 Capture the pre-change baseline of the live hook prompt sections
    - Read `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` and snapshot the rule-delimited sections (FAST PATH GATE and CHECK 1–4) for byte-for-byte comparison in later tests
    - Add a baseline fixture/helper in `tests/` (or extend `tests/hook_test_helpers.py`) that reconstructs the pre-extension enumeration and exposes the captured baseline section text
    - Confirm `tests/gate_decision_model.py` (`WriteOperation`, `GateDecision`, `gate(op, prompt)`) and `tests/hook_test_helpers.py` (hook loading, schema validation, Hypothesis strategies) expose the interfaces this feature needs; do not modify their public contracts
    - _Requirements: 4.5, 6.4_

- [x] 2. Outcome B — Extend the INTERNAL-FILE PASS-THROUGH set (hook)
  - [x] 2.1 Add the two new exact-match entries to the pass-through enumeration
    - Edit `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`: add `config/data_sources.yaml` and `config/visualization_tracker.json` as exact-match entries in the INTERNAL-FILE PASS-THROUGH enumeration within `then.prompt`
    - Preserve all pre-existing entries (`config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `config/progress_{id}.json`, `config/preferences_{id}.yaml`, recap-log pattern)
    - Keep the block evaluated BEFORE the FAST PATH GATE; reuse the identical zero-token silent outcome and introduce NO new output strings; leave FAST PATH GATE and CHECK 1–4 text byte-for-byte unchanged
    - Keep the four NOT-guard conditions intact and evaluated before the pass-through applies
    - Verify the file remains well-formed JSON with non-empty `name`, `version`, `when`, `then`, `when.type == preToolUse`, and `toolTypes == ["write"]`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3_

  - [x] 2.2 Write property test: new routine config files pass through silently
    - **Property 1: New routine config files pass through silently on first attempt**
    - **Validates: Requirements 4.1, 4.2**
    - In repo-root `tests/test_write_gate_momentum_passthrough_properties.py`, drive the live prompt via `gate_decision_model.gate` over the two new exact paths × {`fs_write`, `fs_append`, `str_replace`} with NOT-guard-clean content; assert `PASS_SILENT`, `intercepted=False`, and each literal path is present in the enumeration of `then.prompt`
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 1`; add `@example` seeds for both new paths

  - [x] 2.3 Write property test: existing pass-through entries still pass silently
    - **Property 2: Existing pass-through entries still pass silently**
    - **Validates: Requirements 4.3**
    - Generate clean writes over the exact pre-existing entries, member-scoped `config/progress_{id}.json` / `config/preferences_{id}.yaml` instances, and `docs/progress/MODULE_*_COMPLETE.md` recap logs × 3 tools; assert `PASS_SILENT`, `intercepted=False` (no regression)
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 2`

  - [x] 2.4 Write property test: pass-through membership is exact-match only
    - **Property 3: Pass-through membership is exact-match only**
    - **Validates: Requirements 4.6**
    - Generate near-miss mutations of the exact entries (changed extension, added suffix `.bak`, extra parent dir, case change); assert the gate does NOT grant silent pass-through — write is held (`intercepted=True`) and routed to the four checks
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 3`; add `@example` seeds for `config/data_sources.yml`, `config/data_sources.yaml.bak`, `sub/config/data_sources.yaml`, `config/DATA_SOURCES.yaml`

  - [x] 2.5 Write property test: NOT-guard failure declines pass-through with one matching corrective
    - **Property 4: Any NOT-guard failure declines pass-through and yields exactly one matching corrective**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.5**
    - For candidate pass-through paths violating exactly one NOT-guard (Senzing SQL content; compound question to `config/.question_pending`; `fs_write`/`str_replace` overwrite of the feedback file; root-blocked placement), assert `INTERCEPT_CORRECTIVE`, `intercepted=True`, and exactly one `category` matching the violated guard (`senzing_sql`, `single_question`, `feedback_append_only`, `root_placement`) with no extra content
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 4`

  - [x] 2.6 Write property test: extension introduces no new output strings, preserves silent outcome
    - **Property 5: The pass-through extension introduces no new output strings and preserves the silent outcome**
    - **Validates: Requirements 4.5, 6.4**
    - Assert each baseline section (FAST PATH GATE, CHECK 1–4) in the live prompt is byte-for-byte identical to the captured baseline (task 1.1); assert the INTERNAL-FILE PASS-THROUGH block adds no new corrective/STOP marker; assert a clean non-pass-through write that passes all four checks yields `PASS_SILENT`, `intercepted=True`, `category=None`
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 5`

- [x] 3. Outcome B — Hook example/unit tests (non-PBT)
  - [x] 3.1 Write hook schema conformance example test
    - In `tests/test_write_gate_momentum_hook_schema.py`, load and parse the hook; assert `when.type == "preToolUse"`, `toolTypes == ["write"]`, presence and non-emptiness of `name`/`version`/`when`/`then`, and `then.type == "askAgent"` with non-empty `then.prompt`
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.2 Write pass-through ordering and enumeration-diff example tests
    - Split `then.prompt` into rule-delimited sections; assert the INTERNAL-FILE PASS-THROUGH block precedes the FAST PATH GATE section (Requirement 4.4)
    - Assert the enumeration gained exactly the two new exact-match lines relative to the reconstructed baseline, with every prior entry preserved (Requirements 4.1, 5.3)
    - _Requirements: 4.4, 4.1, 5.3_

  - [x] 3.3 Write OUTPUT FORMAT integrity example test
    - Assert the prompt's OUTPUT FORMAT section forbids extra content and lists the forbidden narration strings (e.g., "Proceeding", "All checks pass"); confirm a violation emits exactly one corrective and nothing else
    - _Requirements: 6.5_

- [x] 4. Checkpoint — hook layer verified
  - Run `python scripts/validate_power.py`, `python scripts/sync_hook_registry.py --verify`, and `pytest tests/ -k write_gate_momentum`; ensure all tests pass, ask the user if questions arise.

- [x] 5. Outcome A — Steering governance edits
  - [x] 5.1 Lock in leading-question governance in `conversation-protocol.md`
    - Edit `senzing-bootcamp/steering/conversation-protocol.md` so it explicitly states: (a) every Yielding_Turn ends with exactly one `👉` Leading_Question; (b) Intercept-Recovery Continuity — a write re-issued after a `write-policy-gate` intercept is not complete until exactly one `👉` question is appended and `config/.question_pending` is written, and ending on bare tool activity or a bare `.` is a violation; (c) the agent owns the closing question and does not rely on hooks; (d) the One Question Rule (exactly one per yielding turn; zero or two-plus violates); plus Mandatory `question_pending` structured format (type on line 1, text on subsequent lines)
    - Keep wording consistent with `agent-behavior-rules.md` (no conflicts); stay within the token budget tracked in `steering-index.yaml`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 5.2 Lock in leading-question governance in `agent-behavior-rules.md`
    - Edit `senzing-bootcamp/steering/agent-behavior-rules.md` (Rule 4: Consistent Pointer Indicator + intercept paragraph) so the same four Requirement 3 governance statements appear here, phrased consistently with `conversation-protocol.md`: prefix every input-requiring prompt with `👉`; a re-issued write after an intercept still requires a closing `👉` call-to-action before yielding; cross-reference "Intercept-Recovery Continuity"
    - Stay within the token budget tracked in `steering-index.yaml`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.3 Update steering token budgets if needed
    - If edits in 5.1/5.2 change token counts, update `senzing-bootcamp/steering/steering-index.yaml` budgets accordingly and confirm `python senzing-bootcamp/scripts/measure_steering.py --check` passes
    - _Requirements: 3.5_

  - [x] 5.4 Write property test: steering governs the leading-question guarantee in both files without conflict
    - **Property 6: Steering governs the leading-question guarantee in both files without conflict**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5**
    - In `tests/test_write_gate_momentum_steering_properties.py`, over the cross-product of {`conversation-protocol.md`, `agent-behavior-rules.md`} × {the four required governance statements (a)–(d)}, assert each statement is present in each on-disk file and that the two files contain no conflicting wording
    - `@settings(max_examples>=100)`; tag class `Feature: write-gate-momentum-preservation, Property 6`

- [x] 6. Final checkpoint — full verification
  - Run `pytest tests/`, `python senzing-bootcamp/scripts/measure_steering.py --check`, `python scripts/validate_commonmark.py`, and `python scripts/validate_power.py`; ensure all tests and CI checks pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks (1.1, 2.1, 5.1, 5.2, 5.3) are never optional.
- Each task references specific granular requirements for traceability.
- Outcome A (tasks 5.x) and Outcome B (tasks 1–3) are independently shippable; checkpoints (4, 6) validate each layer.
- Property tests drive the *live* on-disk artifacts via `gate_decision_model.py`, so drift fails the build. Each correctness property maps to exactly one property-based test with `@example` seeds for the adversarial/edge cases.
- The hook edit reuses the existing zero-token silent outcome and adds no new output strings; baseline byte-for-byte comparison (Property 5) guards the safety surface.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "5.1", "5.2"] },
    { "id": 1, "tasks": ["2.1", "5.3", "5.4"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "3.1", "3.2", "3.3"] }
  ]
}
```
