# Implementation Plan: Conversational Eval Coverage

## Overview

This plan implements the additive coverage expansion described in the design: one new pure
predicate (`_substantive_response`) registered as a single new Assertion_Type in
`senzing-bootcamp/scripts/eval_conversations.py`, four new positive-exemplar Scenario_Fixtures in
`senzing-bootcamp/tests/eval/`, and matching test additions in
`senzing-bootcamp/tests/test_eval_conversations.py` (including the oracle-count update from `== 4`
to `== 8`). The work is strictly additive: the fixture schema, loader, reporter, summary line, CLI,
exit-code contract, and the nine existing Assertion_Types are unchanged.

Implementation language is **Python 3.11+, standard library only** (the design uses concrete Python,
matching the existing harness), per the repository tech-stack and python-conventions steering.

Tasks are dependency-ordered: the predicate first, then the fixtures, then the tests, then a
verification checkpoint.

## Tasks

- [x] 1. Add the `substantive_response` Assertion_Type to the harness
  - [x] 1.1 Implement and register the `_substantive_response` predicate
    - Add the pure function `_substantive_response(turn: Turn, ctx: EvalContext, params: dict[str, object]) -> AssertionOutcome` to `senzing-bootcamp/scripts/eval_conversations.py`, alongside the existing predicates, with the verbatim logic from the design's Component 1: evaluate the three Minimal_Output conditions in order against `turn.content.strip()` — (a) empty/whitespace-only, (b) single-word acknowledgment (`len(words) <= 1`), (c) fewer than 50 characters — returning `AssertionOutcome(False, <reason>)` with a specific human-readable message for the first that matches, else `AssertionOutcome(True, "")`.
    - Add one `REGISTRY` entry mapping `"substantive_response"` to `_substantive_response`.
    - Add the registry documentation stanza (name, purpose, `Params: none.`) alongside the existing nine entries, matching their comment format.
    - Do NOT add a `REQUIRED_PARAMS` entry (the type takes no parameters), and do NOT touch any existing predicate's evaluation logic or add any new import (stdlib-only, no new dependency).
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 1.4, 10.1_

- [x] 2. Author the four positive-exemplar Scenario_Fixtures
  - [x] 2.1 Add `mcp_first_sdk_reference.json` (MCP-First SDK / attribute branch)
    - Create `senzing-bootcamp/tests/eval/mcp_first_sdk_reference.json` using the verbatim JSON from the design's Fixture 1 section: `scenario`, `description`, `rule_ref` = `agent-instructions.md#mcp-first-invariant`, and the bootcamper + agent turns. Agent turn carries assertions `mentions_tool` (`get_sdk_reference`), `exactly_one_pointer`, `ends_with_question_then_stop`. No secrets, PII, or MCP/external URLs.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 1.1, 1.2, 7.1, 7.5, 10.3, 10.4_

  - [x] 2.2 Add `sql_redirect_reporting_guide.json` (no-direct-SQL redirect)
    - Create `senzing-bootcamp/tests/eval/sql_redirect_reporting_guide.json` using the verbatim JSON from the design's Fixture 2 section: `rule_ref` = `mcp-usage-reference.md#sql-redirect-rules`. Agent turn carries `mentions_tool` (`reporting_guide`), `absent_marker` (`SELECT`), `absent_marker` (`RES_ENT`), `exactly_one_pointer`, `ends_with_question_then_stop`. Agent prose must contain no uppercase `SELECT` and no `RES_ENT` substring. No secrets, PII, or MCP/external URLs.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 1.1, 1.2, 7.1, 7.5, 10.3, 10.4_

  - [x] 2.3 Add `confirmation_question_disambiguation.json` (👉 disambiguation)
    - Create `senzing-bootcamp/tests/eval/confirmation_question_disambiguation.json` using the verbatim JSON from the design's Fixture 3 section: `rule_ref` = `conversation-protocol.md#question-disambiguation`. Agent turn carries `exactly_one_pointer`, `no_compound_question`, `no_self_answer`, `ends_with_question_then_stop`. The only `?` is on the single pointer line; no distinctive compound conjunction; no self-answer after the pointer line. No secrets, PII, or MCP/external URLs.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 1.1, 1.2, 7.1, 7.5, 10.3, 10.4_

  - [x] 2.4 Add `substantive_response_after_confirmation.json` (substantive response after a Transition_Confirmation)
    - Create `senzing-bootcamp/tests/eval/substantive_response_after_confirmation.json` using the verbatim JSON from the design's Fixture 4 section: `rule_ref` = `conversation-protocol.md#answer-processing-priority`. Bootcamper turn is a Transition_Confirmation; agent turn is a full module-start block carrying the single assertion `substantive_response` (the type registered in task 1.1). The agent content must be multi-word and well over 50 stripped characters. No secrets, PII, or MCP/external URLs.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 1.1, 1.2, 7.1, 7.5, 10.3, 10.4_

- [x] 3. Extend the harness test suite
  - [x] 3.1 Write the property test for `substantive_response`
    - **Property: `substantive_response` soundness** (Design § Components and Interfaces → Component 1: the predicate passes for Substantive_Response content and fails for every Minimal_Output condition).
    - **Validates: Requirements 6.2, 6.3, 8.2**
    - In `senzing-bootcamp/tests/test_eval_conversations.py`: add `_substantive_response` to the existing `from eval_conversations import (...)` block, then add a class-based property test that uses `st_`-prefixed strategies generating (a) Substantive_Response content (multi-word and `>= 50` non-trivial characters) which must pass, and (b) Minimal_Output content (empty, whitespace-only, single-word acknowledgment, and `< 50` characters) which must fail. Use `@settings(max_examples=20)`, invoke the predicate through the existing `_outcome()` helper, follow `from __future__ import annotations` / type-hint conventions, and add a class docstring documenting which requirement the class validates.
    - This sub-task is NOT optional — the new predicate's universal property must be tested.
    - _Requirements: 8.1, 8.2, 8.4, 8.5_

  - [x] 3.2 Write the fixture-pass test class for the four new fixtures
    - In `senzing-bootcamp/tests/test_eval_conversations.py`: add a class-based test asserting that The_Checker reports zero failures for each of the four new fixtures (`mcp_first_sdk_reference.json`, `sql_redirect_reporting_guide.json`, `confirmation_question_disambiguation.json`, `substantive_response_after_confirmation.json`) — i.e. every attached Behavioral_Assertion passes. Reuse the existing loader/evaluation helpers and conventions; add a class docstring documenting the requirements it validates.
    - _Requirements: 8.3, 8.4, 7.2, 7.4_

  - [x] 3.3 Update the shipped-fixture oracle constant
    - In `senzing-bootcamp/tests/test_eval_conversations.py`, update the oracle assertion in `TestShippedFixturesPassProperty` from `len(_SHIPPED_FIXTURES) == 4` to `len(_SHIPPED_FIXTURES) == 8` to reflect the four new fixtures, keeping the rest of that class (and its full-run-exits-0 check) intact.
    - This sub-task is NOT optional — skipping it breaks the existing suite once the four fixtures are added.
    - _Requirements: 7.2, 7.4_

- [x] 4. Checkpoint — verify the expanded harness and CI gates
  - Run `python senzing-bootcamp/scripts/eval_conversations.py`; it MUST exit 0 with all fixtures passing, including the four new ones.
  - Run `python -m pytest senzing-bootcamp/tests/test_eval_conversations.py`; all new and existing tests MUST pass (including the property test and the updated oracle).
  - Run `ruff check` on `senzing-bootcamp/scripts/eval_conversations.py` and `senzing-bootcamp/tests/test_eval_conversations.py`; report no lint violations.
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` and `python senzing-bootcamp/scripts/validate_power.py` (scoped to the power tree); both MUST still pass with the new files present.
  - Confirm the change is stdlib-only (no new imports in the script or test file) and that the four new fixtures contain no MCP/external URLs, secrets, or PII.
  - If any new fixture's agent turn unexpectedly fails an assertion, fix the FIXTURE content so it is a correct positive exemplar — never weaken or alter the predicate. Then re-run the steps above. Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1, 10.2, 10.3, 10.4, 10.5_

## Notes

- Implementation language is Python 3.11+, standard library only (no third-party dependencies), per `tech.md` and `python-conventions.md`.
- The four fixtures are data and are verified by evaluation (task 3.2 and the harness run in task 4); they do not get their own property tests. Only the new pure predicate gets a property test (task 3.1).
- All four fixtures are positive exemplars; no negative-example / expected-fail fixtures are introduced (the harness contract asserts recorded agent turns are correct).
- Test additions follow the repository convention: `from __future__ import annotations`, class-based organization, `st_`-prefixed Hypothesis strategies, `@settings(max_examples=20)`, and `X | None` / `list[str]` type hints.
- No sub-tasks are marked optional: task 3.1 (property test) and task 3.3 (oracle update) are explicitly required, and task 3.2 (fixture-pass tests) is mandated by Requirement 8.3 and is the core verification value of this coverage feature.
- Each task references the specific requirement clauses it implements for traceability.
- Deferred coverage candidates (Requirement 11) are intentionally NOT implemented in v1.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2", "2.3"] },
    { "id": 1, "tasks": ["2.4"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["3.2"] },
    { "id": 4, "tasks": ["3.3"] }
  ]
}
```
