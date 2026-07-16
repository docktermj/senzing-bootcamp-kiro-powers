# Implementation Plan

This plan follows the exploratory bugfix workflow: **explore** the bug with
tests that fail on the unfixed code, **preserve** existing behavior with tests
that pass on the unfixed code, **implement** the two-part fix (durable
command-backed capture + loud graduation validation), then **validate**. Tasks
are mapped to the 8 correctness properties in `design.md` and to the requirement
clauses in `bugfix.md`.

Property → design mapping (hover status uses `**Property N:**`):

- Property 1 — Bug Condition: Durable Write-Through Capture (Req 2.1, 2.2)
- Property 2 — Bug Condition: Loud Graduation Validation (Req 2.3, 2.4)
- Property 3 — Preservation: Non-Blocking Capture (Req 3.2)
- Property 4 — Preservation: Idempotent Question Logging (Req 3.3)
- Property 5 — Preservation: Answer-to-Question Pairing and Self-Heal (Req 3.4)
- Property 6 — Preservation: Byte-for-Byte Append-Around (Req 3.5)
- Property 7 — Preservation: Real-Q&A Rendering Unchanged (Req 3.1)
- Property 8 — Preservation: Standard Library Only (Req 3.6)

Environment: Python 3.11+ standard library only. Tests use pytest + Hypothesis
with the repo's registered profiles (`fast` locally, `thorough` in CI) — do NOT
hand-set `@settings(max_examples=...)` to restate the baseline. Power tests live
in `senzing-bootcamp/tests/`; hook-prompt validation tests live in repo-root
`tests/`.

---

## Exploration (write BEFORE the fix — these MUST FAIL / expose the gap on unfixed code)

- [x] 1. Write bug condition exploration test for durable capture
  - **Property 1: Bug Condition** - Durable Write-Through Capture
  - **CRITICAL**: This test MUST FAIL on unfixed wiring - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails** at this stage
  - **NOTE**: This test encodes the expected durable-capture behavior - it will validate the fix once it passes after implementation
  - **GOAL**: Surface counterexamples showing Q&A events are lost when the agent does not voluntarily run `log_qa_event.py`
  - **Scoped PBT Approach**: Generate arbitrary Q&A cadence sequences (question presented, answer submitted); simulate the boundary/compaction/restart case where the agent never invokes the helper. For the deterministic reported case, scope to the concrete "Modules 1-3 completed with no Q&A events" fixture for reproducibility.
  - Bug condition from design: `isBugCondition(input)` — `input.isQACadenceEvent AND NOT persistedDeterministically(input) AND eventMissingFrom("config/session_log.jsonl", input)`
  - Test cases from design "Exploratory Bug Condition Checking": (1) agent-skip capture — present question, submit answer, never call helper, assert `config/session_log.jsonl` has NO matching `question`/`answer` events; (2) cross-session loss — reproduce Modules 1-3 completed with no Q&A, assert events absent
  - Place in `senzing-bootcamp/tests/test_durable_qa_capture_exploration.py`
  - Run test on UNFIXED wiring
  - **EXPECTED OUTCOME**: Test FAILS (events are missing - proves capture rode on the agent-voluntary hook)
  - Document counterexamples found (e.g., "cadence event produced no durable event because capture was agent-voluntary")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Write bug condition exploration test for loud graduation validation
  - **Property 2: Bug Condition** - Loud Graduation Validation
  - **CRITICAL**: This test MUST demonstrate the silent-placeholder behavior on unfixed code
  - **DO NOT attempt to fix the test or the code when it exposes the gap** at this stage
  - **NOTE**: This test encodes the expected fail-loudly behavior - it will validate the fix once graduation halts and names the missing module
  - **GOAL**: Surface the silent placeholder masking a real Q&A gap at graduation
  - **Scoped PBT Approach**: Generate arbitrary `(modules_completed, session_log)` states where at least one completed module has no real Q&A; for the deterministic case, scope to "Module 2 completed, no real Q&A" for reproducibility
  - Graduation bug condition from design: `isGraduationBugCondition(state)` — `renderingBegun(state) AND EXISTS module IN state.modulesCompleted SUCH THAT NOT hasRealQA(...) AND rendersPlaceholderInsteadOfHalting(state, module)`
  - Test case from design: given a completed module with no real Q&A, run the graduation render; assert the recap contains the placeholder `N/A (section backfilled at track completion; original session content unavailable)` AND graduation reports success (the behavior we will make fail loudly)
  - Also capture the edge case: a legitimately question-free module (with an explicit "no substantive questions" marker) to confirm the current path does not distinguish gap-vs-empty (informs the fix)
  - Place in `senzing-bootcamp/tests/test_graduation_qa_gate_exploration.py`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test confirms the recap silently renders placeholder text while graduation reports success (proves the missing pre-render gate)
  - Document counterexamples found
  - Mark task complete when test is written, run, and the silent-placeholder behavior is documented
  - _Requirements: 1.3, 1.4, 2.3, 2.4_

## Preservation (write BEFORE the fix — observe unfixed behavior; these MUST PASS on unfixed code)

- [x] 3. Write preservation property tests for existing capture semantics (BEFORE implementing fix)
  - **Property 3: Preservation** - Non-Blocking Capture
  - **IMPORTANT**: Follow observation-first methodology - observe the UNFIXED behavior, then encode it
  - Property-based testing generates many cases across the input domain for stronger preservation guarantees; use `@given` with the active Hypothesis profile (no inline `max_examples` restating the baseline)
  - Observe on UNFIXED `log_qa_event.py`: feed error-inducing inputs (missing/unreadable `config/.question_pending`, absent `config/session_log.jsonl`, malformed `config/.qa_capture.json` sidecar); observe the helper exits 0 and raises nothing
  - Write property test: for all error-inducing inputs, `log_qa_event.py` (both `record-question` and `record-answer`) exits 0 and raises nothing (from Preservation Requirements in design, Property 3)
  - Place in `senzing-bootcamp/tests/test_durable_qa_capture_preservation.py`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms the non-blocking baseline to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.2_

- [x] 4. Write preservation property tests for idempotency, pairing/self-heal, and append-around (BEFORE implementing fix)
  - **Property 4: Preservation** - Idempotent Question Logging
  - **Property 5: Preservation** - Answer-to-Question Pairing and Self-Heal
  - **Property 6: Preservation** - Byte-for-Byte Append-Around
  - **IMPORTANT**: Follow observation-first methodology - observe the UNFIXED behavior first
  - Property 4 — Observe: present the same pending question N times (Hypothesis-generated N and question text) across turns/session boundaries; assert exactly ONE `question` event is logged (de-duplicated via the `config/.qa_capture.json` sidecar)
  - Property 5 — Observe: generate `(question, answer)` pairs including the self-heal case where no question was logged first; assert each `answer` event carries the correct `question_id` and the question is logged first when absent
  - Property 6 — Observe: generate arbitrary pre-existing `config/session_log.jsonl` content and existing `docs/bootcamp_recap.md` sections; assert prior bytes are byte-for-byte unchanged after capture (append-around, no overwrite)
  - Write property-based tests capturing each observed behavior pattern (from Preservation Requirements in design)
  - Place in `senzing-bootcamp/tests/test_durable_qa_capture_preservation.py`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline idempotency, pairing, and append-around behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.3, 3.4, 3.5_

- [x] 5. Write preservation tests for real-Q&A rendering and stdlib-only (BEFORE implementing fix)
  - **Property 7: Preservation** - Real-Q&A Rendering Unchanged
  - **Property 8: Preservation** - Standard Library Only
  - **IMPORTANT**: Follow observation-first methodology - observe the UNFIXED renderer output first
  - Property 7 — Observe: generate modules with durably captured Q&A; assert the recap renders the same real question/answer pairs in ascending ask order, each response paired to its own question, identical to the original renderer (`completion_artifacts.py` real-Q&A path)
  - Property 8 — Assert the new/modified capture and validation code imports only Python 3.11+ standard library (no third-party runtime dependency); scan `validate_qa_capture.py` and `log_qa_event.py` imports and confirm no pip dependency is introduced
  - Place Property 7 in `senzing-bootcamp/tests/test_durable_qa_capture_preservation.py`; place Property 8 as an import/stdlib-only assertion in the same suite
  - Run tests on UNFIXED code (Property 7 baseline) and confirm stdlib-only holds
  - **EXPECTED OUTCOME**: Tests PASS (confirms real-Q&A rendering baseline and stdlib-only constraint)
  - Mark task complete when tests are written, run, and passing
  - _Requirements: 3.1, 3.6_

## Implementation

- [x] 6. Fix for lost Q&A capture and silent graduation backfill

  - [x] 6.1 Add the durable, command-backed Q&A capture hook
    - Create `senzing-bootcamp/hooks/capture-qa-events.json` modeled exactly on `senzing-bootcamp/hooks/session-log-events.json` (`type: command`, non-blocking, short `timeout`)
    - Entry 1 — record question (Stop cadence): a `Stop`-triggered `type: command` hook whose `action.command` runs, only when `config/.question_pending` exists, `python3 senzing-bootcamp/scripts/log_qa_event.py record-question`
    - Entry 2 — record answer (UserPromptSubmit cadence): a `UserPromptSubmit`-triggered `type: command` hook whose `action.command` pipes the bootcamper's verbatim message on stdin to `python3 senzing-bootcamp/scripts/log_qa_event.py record-answer`
    - Follow the on-disk hook schema used by this repo: `{ "version": "v1", "hooks": [ { "name", "trigger", "action": { "type": "command", "command", "timeout" } } ] }`
    - Guard both commands so a missing script degrades gracefully (mirror the `if [ -f ... ]` pattern from `session-log-events.json`)
    - _Bug_Condition: isBugCondition(input) — QA cadence event NOT persistedDeterministically, eventMissingFrom session_log.jsonl_
    - _Expected_Behavior: persist question/answer event via deterministic command-backed hook at ask/answer time, surviving boundaries/compaction/restarts_
    - _Preservation: capture stays non-blocking, idempotent, paired, append-around (Properties 3-6)_
    - _Requirements: 2.1, 2.2_

  - [x] 6.2 Demote the agent-voluntary Q&A logging to a redundant backstop
    - In `senzing-bootcamp/hooks/ask-bootcamper.json` and `senzing-bootcamp/hooks/review-bootcamper-input.json`, reframe the Q&A logging instruction (running `log_qa_event.py`) as a best-effort, redundant backstop rather than the primary durability path — the command-backed hook now guarantees the write
    - Keep all non-Q&A behavior untouched (Phase 0 recap logic, Phases 1/1.5/2/3/4, feedback/status triggers); only the Q&A durability guarantee moves to the command hook
    - Note: this ADDS a command hook and demotes prompt text; it does NOT remove any `preToolUse`/write-backed hook, so the write-hook removal safeguard does not apply
    - _Bug_Condition: capture rode on agent-voluntary `type: agent` prompt_
    - _Expected_Behavior: durability guaranteed by command hook; agent prompt is redundant backstop_
    - _Preservation: non-Q&A hook phases unchanged_
    - _Requirements: 2.1_

  - [x] 6.3 (Optional) Harden `log_qa_event.py` stdin handling for command-hook invocation
    - No behavior change is required — `log_qa_event.py` is already deterministic, idempotent, paired, non-blocking, and stdlib-only; it simply now runs from a command hook
    - Optional hardening: ensure `record-answer` reads stdin robustly (empty/partial/no stdin) when invoked by the command hook, still exiting 0
    - Do NOT alter idempotency, pairing/self-heal, append-around, or non-blocking semantics
    - _Bug_Condition: n/a (helper already correct; invocation surface changes)_
    - _Expected_Behavior: record-answer reads stdin robustly under command-hook invocation_
    - _Preservation: Properties 3, 4, 5, 6 unchanged_
    - _Requirements: 2.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 6.4 Implement the graduation Q&A completeness validator
    - Create `senzing-bootcamp/scripts/validate_qa_capture.py` (stdlib only), following the repo script pattern (shebang, `from __future__ import annotations`, module docstring, `@dataclass` for structured data, `argparse`, `main(argv=None)`, `if __name__ == "__main__": main()`)
    - Given `config/bootcamp_progress.json` and `config/session_log.jsonl`, verify every module in `modules_completed` has at least one real `question` event (and, where a question was answered, a paired `answer`)
    - Distinguish a genuine gap from a legitimately question-free module via an explicit "no substantive questions" marker so it does not false-positive
    - Reuse `generate_transcript.read_events` and `reconcile_transcript.count_logged_questions` for counting rather than re-parsing
    - CLI: exit non-zero and name the missing module(s) on failure; `--json` for machine consumption; `--check` for verify-only; exit 0 when all completed modules have real Q&A
    - _Bug_Condition: isGraduationBugCondition(state) — completed module lacks real Q&A and placeholder is rendered instead of halting_
    - _Expected_Behavior: validate completeness before rendering; fail loudly and name missing module(s)_
    - _Preservation: real-Q&A modules and legitimately-empty modules pass (Properties 2, 7)_
    - _Requirements: 2.3, 2.4, 3.6_

  - [x] 6.5 Wire the validator into the graduation path before recap rendering
    - In `senzing-bootcamp/scripts/ensure_graduation_artifacts.py` (and/or the graduation hook path), invoke `validate_qa_capture.py` BEFORE any recap rendering / backfill
    - On validation failure: halt graduation and surface the missing module(s) to the bootcamper — do NOT reach `render_backfill_section` for a real gap
    - Ensure `render_backfill_section`'s placeholder path is only reachable for modules that legitimately have no Q&A (empty marker present), never as a silent mask for a real gap
    - _Bug_Condition: rendering begins while a completed module has no real Q&A_
    - _Expected_Behavior: halt rendering and report before any placeholder is emitted_
    - _Preservation: fully-captured tracks graduate and render real Q&A unchanged (Property 7); byte-for-byte append-around preserved (Property 6)_
    - _Requirements: 2.3, 2.4, 3.1, 3.5_

  - [x] 6.6 Register the new hook in the repo's hook inventory
    - Add `capture-qa-events` to `senzing-bootcamp/hooks/hook-categories.yaml` in the appropriate bucket
    - Regenerate/verify the hook lock/registry: run `python3 senzing-bootcamp/scripts/sync_hook_registry.py` and confirm `--verify` passes (CI runs `sync_hook_registry.py --verify`)
    - Update `senzing-bootcamp/hooks/README.md` if it enumerates hooks (kept in sync by `test_hook_readme_file_sync.py`)
    - _Preservation: existing hook registry entries preserved (Property 6-style byte stability for unrelated entries)_
    - _Requirements: 2.1_

  - [x] 6.7 Verify durable-capture exploration test now passes
    - **Property 1: Expected Behavior** - Durable Write-Through Capture
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected durable-capture behavior
    - Run the exploration test from task 1 against the fixed wiring (command-backed hook path)
    - **EXPECTED OUTCOME**: Test PASSES (confirms every cadence event is durably persisted regardless of agent narration / boundaries)
    - _Requirements: 2.1, 2.2_

  - [x] 6.8 Verify graduation-gate exploration test now passes
    - **Property 2: Expected Behavior** - Loud Graduation Validation
    - **IMPORTANT**: Re-run the SAME test from task 2 - do NOT write a new test
    - Run the exploration test from task 2 against the fixed code
    - **EXPECTED OUTCOME**: Test PASSES — graduation halts and names the missing module(s); the recap does NOT contain the "backfilled at track completion" placeholder for a real gap; a legitimately-empty module (with marker) still passes
    - _Requirements: 2.3, 2.4_

  - [x] 6.9 Verify preservation tests still pass (no regressions)
    - **Property 3: Preservation** - Non-Blocking Capture
    - **Property 4: Preservation** - Idempotent Question Logging
    - **Property 5: Preservation** - Answer-to-Question Pairing and Self-Heal
    - **Property 6: Preservation** - Byte-for-Byte Append-Around
    - **Property 7: Preservation** - Real-Q&A Rendering Unchanged
    - **Property 8: Preservation** - Standard Library Only
    - **IMPORTANT**: Re-run the SAME tests from tasks 3, 4, and 5 - do NOT write new tests
    - **EXPECTED OUTCOME**: Tests PASS (confirms non-blocking, idempotent, paired, append-around, real-Q&A rendering, and stdlib-only behavior are unchanged after the fix)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

## Supporting tests (unit, schema, property, integration)

- [x] 7. Write unit tests for `log_qa_event.py` under command-hook invocation
  - `record-question` with and without `config/.question_pending`; `record-answer` from stdin with and without a `config/.qa_capture.json` sidecar
  - Assert exit code 0 in all paths and correct event shape when a question/answer is present
  - Extend or add alongside existing `senzing-bootcamp/tests/test_log_qa_event.py`
  - _Requirements: 2.1, 3.2, 3.3, 3.4_

- [x] 8. Write unit tests for `validate_qa_capture.py`
  - Completed module with real Q&A passes; completed module missing Q&A fails and names the module; legitimately-empty module (with marker) passes
  - Assert exit codes and `--json` output shape; assert `--check` verify-only behavior
  - Class-based organization in `senzing-bootcamp/tests/test_validate_qa_capture_unit.py`
  - _Requirements: 2.3, 2.4_

- [x] 9. Write hook-JSON schema validation test for the new capture hook
  - Assert `senzing-bootcamp/hooks/capture-qa-events.json` is valid: `version == "v1"`, `hooks[].name` present, `hooks[].trigger` in the allowed set (`Stop`, `UserPromptSubmit`), `action.type == "command"`, `action.command` present
  - Reuse the repo's hook-schema conformance helpers; add to repo-root `tests/` (hook-prompt/schema validation lives there, e.g. `tests/test_hook_schema_conformance.py`)
  - _Requirements: 2.1_

- [x] 10. Write hook-prompt validation tests for the demoted agent hooks
  - Assert `ask-bootcamper.json` / `review-bootcamper-input.json` still preserve non-Q&A behavior (phase logic, feedback/status triggers) and that the Q&A logging text now reads as a redundant backstop, not the primary durability path
  - Place in repo-root `tests/` (hook-prompt validation), consistent with `tests/test_answer_processing_hook_prompt.py` and `tests/test_ask_once_*`
  - _Requirements: 2.1_

- [x] 11. Write property-based tests for the two bug-condition properties
  - **Property 1: Bug Condition** - Durable Write-Through Capture: generate arbitrary Q&A cadence sequences; assert every event is durably persisted when the deterministic command runs
  - **Property 2: Bug Condition** - Loud Graduation Validation: generate arbitrary `(modules_completed, session_log)` states; assert validation halts and names missing modules for every real gap, and passes when all completed modules have real Q&A
  - Use `@given` with the active Hypothesis profile (`st_`-prefixed strategies; no inline `max_examples` restating the baseline)
  - Place in `senzing-bootcamp/tests/test_durable_qa_capture_properties.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 12. Write integration tests for end-to-end durability and the graduation gate
  - Full cadence: present question -> (no agent narration) -> command hook writes -> answer submitted -> command hook writes -> assert both events present and paired (end-to-end durability)
  - Cross-session: write events in "session A", start "session B", complete the track, run graduation; assert no module ends with an unrecoverable gap
  - Graduation gate: a completed module with a real gap causes `ensure_graduation_artifacts.py` to halt and report BEFORE any placeholder is rendered; a fully-captured track graduates and renders real Q&A unchanged
  - Place in `senzing-bootcamp/tests/test_durable_qa_capture_integration.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.5_

## Checkpoint

- [x] 13. Checkpoint - Ensure all tests pass
  - Run the fast profile locally: `python -m pytest senzing-bootcamp/tests/ tests/`
  - Run the thorough profile to match CI: `HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/`
  - Confirm CI gates pass: `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest
  - Ensure all exploration tests (tasks 1-2) now pass, all preservation tests (tasks 3-5) still pass, and no regressions elsewhere
  - Ask the user if questions arise
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
