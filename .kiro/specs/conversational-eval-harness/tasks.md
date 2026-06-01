# Implementation Plan: Conversational Eval Harness

## Overview

This plan builds the stdlib-only conversational-eval harness in dependency order:
the single-file checker skeleton with detection heuristics and data models first, then
the assertion predicates + registry, then the loader/validator, then evaluation +
reporting + CLI. The four starter fixtures follow, and the oracle is verified by running
the checker over them (exit 0). Property and example tests (pytest + Hypothesis) are added
after the components they validate, with one property test per design Property P1–P17.
CI wiring is optional and added last, followed by a final verification checkpoint.

Language: **Python 3.11+, stdlib only** (per the design and `tech.md`). Tests use pytest +
Hypothesis. All paths are relative to the repository root.

## Tasks

- [x] 1. Create checker skeleton, data models, and detection heuristics
  - [x] 1.1 Scaffold `eval_conversations.py` with module header and data models
    - Create `senzing-bootcamp/scripts/eval_conversations.py` with `#!/usr/bin/env python3`, `from __future__ import annotations`, a module docstring with usage examples that explicitly states the "steering SAYS the rule vs a recorded conversation HONORS the rule" distinction, and stdlib imports only (`argparse`, `json`, `re`, `sys`, `pathlib`, `dataclasses`, `collections`)
    - Define dataclasses `AssertionSpec`, `Turn`, `Scenario`, `AssertionOutcome`, `EvalFailure` (frozen, with `X | None` / `list[str]` type hints) and the exception hierarchy `EvalError`, `ParseError`, `EmptyDirError`, `SchemaError`
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 11.1, 11.2, 9.3, 9.4_

  - [x] 1.2 Implement detection heuristics (pure helpers + constants)
    - Add module constants `POINTER`, `HARD_STOP`, and `CONJUNCTION_PATTERNS` (copied from `validate_behavior_rules.py` with a documented lineage comment, not imported, per R9.3) and the helper functions `count_pointers`, `pointer_question_line`, `has_conjunction`, `count_question_marks`, `text_after`
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 11.2, 9.3, 3.1, 3.2, 3.3_

  - [x] 1.3 Write unit tests for detection heuristics
    - Set up `senzing-bootcamp/tests/test_eval_conversations.py` with `from __future__ import annotations`, the `sys.path` import shim for `eval_conversations`, and class-based tests covering `count_pointers`, `pointer_question_line`, `has_conjunction`, `count_question_marks`, `text_after` edge cases
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`
    - _Requirements: 12.5, 3.1, 3.3_

- [x] 2. Implement assertion predicates and registry
  - [x] 2.1 Implement the nine assertion predicates
    - Implement `_exactly_one_pointer`, `_ends_with_question_then_stop`, `_no_compound_question`, `_no_self_answer`, `_contains_marker`, `_absent_marker`, `_mentions_tool`, `_transition_response_completeness`, `_gate_not_bypassed` matching the design predicate detail, each returning `AssertionOutcome(passed, message)` with an empty message on pass and a specific reason on fail
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 6.4_

  - [x] 2.2 Implement the registry, REQUIRED_PARAMS, and resolve()
    - Add `REGISTRY` mapping type names to predicates, `REQUIRED_PARAMS` for parameterized types, and `resolve(type_name)` that raises `SchemaError` (naming scenario, turn index, unknown type) on a miss; ensure adding a new type needs only a registry entry without touching existing predicate evaluation
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 2.3 Write property test for `exactly_one_pointer`
    - **Property 3: `exactly_one_pointer` soundness** (passes iff pointer count == 1; fails for zero or more than one)
    - **Validates: Requirements 3.1, 12.3**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.4 Write property test for `ends_with_question_then_stop`
    - **Property 4: `ends_with_question_then_stop` soundness** (passes when a pointer question is followed only by whitespace/hard-stop; fails when substantive prose or a simulated reply is appended)
    - **Validates: Requirements 3.2**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.5 Write property test for `no_compound_question`
    - **Property 5: `no_compound_question` soundness** (passes for a single question with no conjunction; fails for two alternatives joined by a prose conjunction)
    - **Validates: Requirements 3.3, 12.4**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.6 Write property test for `no_self_answer`
    - **Property 6: `no_self_answer` soundness** (passes for a pointer question followed only by a hard-stop boundary; fails when a declarative answering sentence is appended)
    - **Validates: Requirements 3.4**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.7 Write property test for marker presence (`contains_marker` / `absent_marker`)
    - **Property 7: Marker-presence soundness** (`contains_marker` passes iff marker is a substring; `absent_marker` is its exact complement)
    - **Validates: Requirements 3.5, 3.6**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.8 Write property test for `mentions_tool`
    - **Property 8: `mentions_tool` soundness** (passes iff the tool name occurs as a token in the text)
    - **Validates: Requirements 3.7**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.9 Write property test for `transition_response_completeness`
    - **Property 9: `transition_response_completeness` soundness** (passes with all four markers and length > 50; fails when a marker is dropped or length <= 50)
    - **Validates: Requirements 3.8**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 2.10 Write property test for `gate_not_bypassed`
    - **Property 10: `gate_not_bypassed` soundness** (passes with execution evidence and no skip/bypass offer; fails when a skip offer is added or all execution evidence is removed)
    - **Validates: Requirements 3.9**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement fixture loading and validation
  - [x] 4.1 Implement `parse_scenario` and `load_scenarios`
    - Implement `parse_scenario(raw, source)` mapping the JSON object to `Scenario` (collecting non-`type` assertion fields into `AssertionSpec.params`) and `load_scenarios(target)` that loads one file or every `*.json` in a directory; raise `ParseError` on `json.JSONDecodeError` (naming the file), `EmptyDirError` when a directory has no fixtures, and `SchemaError` for missing `role`/`content`, invalid `role`, bootcamper turns carrying assertions, unknown assertion types, and missing required params — running validation before any evaluation
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 1.2, 1.3, 1.4, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 4.2 Write property test for valid-fixture round-trip
    - **Property 1: Valid fixtures round-trip into a Scenario** (parsed `Scenario` fields equal input; turns and assertions preserved in order)
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.6, 2.1, 2.2, 2.3**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 4.3 Write property test for schema rejection
    - **Property 2: Structurally invalid fixtures are rejected with an attributed schema error** (missing field / bad role / bootcamper-with-assertions / unknown type raise `SchemaError` naming scenario, turn index, and unknown type; no assertions evaluated)
    - **Validates: Requirements 2.4, 2.7, 4.1, 4.2, 5.5**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 4.4 Write example tests for loading behavior and the R12.6 negatives
    - Cover load-all (no path), single-path loading, and empty-directory error; add the explicit R12.6 negative cases: an unknown assertion type and a malformed (non-JSON) fixture each cause an error and exit 1
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`
    - _Requirements: 5.1, 5.2, 5.4, 12.6_

- [x] 5. Implement evaluation, reporting, and CLI
  - [x] 5.1 Implement evaluation, runner, and `main`
    - Implement `evaluate_turn(turn, ctx)` and `evaluate_scenario(scenario)` using collect-all (evaluate every assertion on every agent turn, accumulating `EvalFailure`s with `scenario_id`, `turn_index`, `assertion_type`, `message`); implement `run(target)` returning the exit code, a `main(argv=None)` argparse entry point (`--fixtures-dir` + optional `path`), the stdout summary (scenarios / assertions / failures), per-failure output to stderr, exit 0 on all-pass and exit 1 on any failure or parse/schema error, plus the `if __name__ == "__main__"` guard
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 11.2_

  - [x] 5.2 Write property test for evaluation completeness
    - **Property 11: Evaluation completeness** (number of assertion results equals total assertions across all agent turns)
    - **Validates: Requirements 6.1, 6.2**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 5.3 Write property test for failure attribution
    - **Property 12: Failure attribution** (each `EvalFailure` carries correct scenario id, turn index, failing type, and a non-empty message)
    - **Validates: Requirements 6.3, 6.4**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 5.4 Write property test for the exit-code contract
    - **Property 13: Exit-code contract** (exit 0 iff zero assertions fail, exit 1 if at least one fails, for fixtures that load successfully)
    - **Validates: Requirements 7.1, 7.2**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 5.5 Write property test for determinism
    - **Property 14: Determinism** (running the same fixtures twice yields identical results, failures, and exit code)
    - **Validates: Requirements 3.10, 8.4**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 5.6 Write property test for malformed-fixture parse error
    - **Property 16: Malformed fixtures raise a parse error** (non-JSON bytes raise `ParseError` naming the file and exit 1)
    - **Validates: Requirements 5.3, 7.3, 12.6**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 5.7 Write example tests for summary output and the `main(argv=None)` entry point
    - Assert the stdout summary reports scenarios/assertions/failures and that `main(argv=None)` is invokable and returns the documented exit codes
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`
    - _Requirements: 6.5, 7.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create the four starter scenario fixtures
  - [x] 7.1 Create `single_question_stop.json`
    - Create the fixture exactly as in the design, encoding the expected-behavior oracle with assertions `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`, `contains_marker`; no MCP URL or secrets
    - Files: `senzing-bootcamp/tests/eval/single_question_stop.json`
    - _Requirements: 10.1, 10.6, 11.4_

  - [x] 7.2 Create `module3_gate_not_bypassed.json`
    - Create the fixture exactly as in the design, encoding the expected-behavior oracle with assertions `gate_not_bypassed` (`step="3.9"`), `absent_marker`, `exactly_one_pointer`, `ends_with_question_then_stop`; no MCP URL or secrets
    - Files: `senzing-bootcamp/tests/eval/module3_gate_not_bypassed.json`
    - _Requirements: 10.2, 10.6, 11.4_

  - [x] 7.3 Create `module_transition_completeness.json`
    - Create the fixture exactly as in the design, encoding the expected-behavior oracle with the `transition_response_completeness` assertion; no MCP URL or secrets
    - Files: `senzing-bootcamp/tests/eval/module_transition_completeness.json`
    - _Requirements: 10.3, 10.6, 11.4_

  - [x] 7.4 Create `license_insufficient_search_docs.json`
    - Create the fixture exactly as in the design, encoding the expected-behavior oracle with assertions `mentions_tool` (`tool="search_docs"`), `exactly_one_pointer`, `ends_with_question_then_stop`; no MCP URL or secrets
    - Files: `senzing-bootcamp/tests/eval/license_insufficient_search_docs.json`
    - _Requirements: 10.4, 10.6, 11.4_

- [x] 8. Verify the oracle over the shipped fixtures
  - [x] 8.1 Run the checker over the starter set and confirm exit 0
    - Run `python3 senzing-bootcamp/scripts/eval_conversations.py` and confirm every assertion passes and the process exits 0 over the four shipped fixtures; fix any predicate/fixture mismatch so the shipped oracle is self-consistent
    - Files: `senzing-bootcamp/scripts/eval_conversations.py`, `senzing-bootcamp/tests/eval/*.json`
    - _Requirements: 10.5, 10.6_

  - [x] 8.2 Write property test for shipped-fixtures-pass oracle
    - **Property 15: Shipped fixtures pass (self-consistency oracle)** (every shipped fixture's assertions pass and a full run exits 0)
    - **Validates: Requirements 10.5, 10.6, 12.1**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 8.3 Write property test for no MCP URL / secrets in fixtures
    - **Property 17: Fixtures contain no MCP URL or secrets** (enumerated fixtures contain no MCP server URL and no secret/credential/PII pattern)
    - **Validates: Requirements 11.4**
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`

  - [x] 8.4 Write the stdlib-only import-audit example test
    - Assert `eval_conversations` imports only standard-library modules and performs no network/LLM/MCP calls
    - Files: `senzing-bootcamp/tests/test_eval_conversations.py`
    - _Requirements: 8.1, 8.2, 11.1_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Optional CI wiring
  - [x] 10.1 Add the eval-harness step to the CI workflow
    - Add a step running `python senzing-bootcamp/scripts/eval_conversations.py` to `.github/workflows/validate-power.yml` before the pytest step (CI integration is recommended/optional per the design, and Property 15 also runs via pytest)
    - Files: `.github/workflows/validate-power.yml`
    - _Requirements: 7.1, 7.2_

- [x] 11. Final checkpoint - Verify the harness end to end
  - Run `python -m pytest senzing-bootcamp/tests/test_eval_conversations.py -v` and confirm all tests pass
  - Run `python3 senzing-bootcamp/scripts/eval_conversations.py` and confirm exit 0
  - Confirm the checker is stdlib-only (no third-party import, no network/LLM/MCP), no MCP URL appears in any fixture, and nothing else in the power was modified
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; they are the test sub-tasks (property tests P1–P17, example/negative tests, and CI wiring).
- Each task references specific requirement sub-clauses for traceability; test tasks name the design Property number they validate.
- Checkpoints (tasks 3, 6, 9, 11) ensure incremental validation as components are completed.
- Property tests validate the universal correctness properties (P1–P17); example and negative tests (R12.6) cover loading, summary, the `main` entry point, the shipped-fixture oracle, and the stdlib-only audit.
- Per `tech.md`, the checker is Python stdlib-only; tests use pytest + Hypothesis with `@settings(max_examples=20)`, `st_`-prefixed strategies, `from __future__ import annotations`, and class-based organization.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "2.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10"] },
    { "id": 4, "tasks": ["4.1"] },
    { "id": 5, "tasks": ["4.2", "4.3", "4.4"] },
    { "id": 6, "tasks": ["5.1"] },
    { "id": 7, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7"] },
    { "id": 8, "tasks": ["7.1", "7.2", "7.3", "7.4"] },
    { "id": 9, "tasks": ["8.1"] },
    { "id": 10, "tasks": ["8.2", "8.3", "8.4"] },
    { "id": 11, "tasks": ["10.1"] }
  ]
}
```
