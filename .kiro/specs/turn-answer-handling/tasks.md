# Implementation Plan

## Overview

This bugfix follows the exploratory bug-condition workflow: write failing exploration tests first to confirm the bug, capture preservation behavior on the UNFIXED code, then apply the fix and validate. Tests use pytest + Hypothesis, stdlib-only, and live in `senzing-bootcamp/tests/`.

The two coordinated parts of the fix are:
- **Item 2 (answer binding):** a new pure, stdlib-only helper `senzing-bootcamp/scripts/answer_binding.py` (`parse_option_token`, `bind_option`, `is_bare_matching_token`), wired into Module 6 Step 1 to bind-first before falling through to the unchanged `volume_utils.parse_volume_input`.
- **Item 1 (protocol ordering):** make the "exactly one live 👉 pending question as the final message" invariant explicit in `conversation-protocol.md`, and require recap/confirmation to run before (or re-surface after) the forward transition question in the module-completion steering.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - One Live Pending Question, Answers Bound
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists (confirm/refute root-cause analysis; re-hypothesize if refuted)
  - **Scoped PBT Approach**: Item 2 binding is deterministic — scope the property to concrete presented option lists (the four-tier volume options and a generic a/b/c list) and generate bare tokens across the option range. Item 1 is a steering-invariant check against the actual steering files.
  - Create `senzing-bootcamp/tests/test_answer_binding.py` with a class-based suite; import `scripts/` via `sys.path`; prefix Hypothesis strategies with `st_`; use `@settings(max_examples=...)`; docstrings name the validated requirements.
  - Item 2 — Bare numeric option bind: for the four-tier volume options, assert `bind_option("3", four_volume_options)` returns `3` (→ medium tier), and as a property, for any bare numeric token `n` within the option-list length, `bind_option(str(n), options) == n`. From the Bug Condition: `unboundMatchingTokenAnswer ← priorQuestionHasOptionList AND isBareMatchingToken(reply, options) AND NOT replyBoundToPendingQuestion`.
  - Item 2 — Bare lettered option bind: assert `bind_option("b", ["a-opt","b-opt","c-opt"])` returns `2`; property: any bare letter within range maps case-insensitively to its 1-based position.
  - Item 2 — Mis-parse documentation: assert `parse_volume_input("3") == 3` is classified as the demo tier, documenting the wrong literal interpretation the binding step must override for an Option_List question.
  - Item 1 — Final-message invariant absent: assert `senzing-bootcamp/steering/conversation-protocol.md` contains an explicit "live 👉 pending question must be the final message of an input-expecting turn" rule.
  - Item 1 — Completion ordering rule absent: assert `module-completion.md` / `module-completion-next-steps.md` contain the recap-before-transition (or re-surface-forward-question) rule.
  - The test assertions match the Expected Behavior Properties (Property 1): for input-expecting turns the turn ends with exactly one live 👉 pending question and writes `config/.question_pending`; for an Option_List prior question a bare matching token binds, is consumed, advances the workflow, and is not re-asked.
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists; e.g., no `answer_binding` helper to import, and the steering invariants are absent)
  - Document counterexamples found (e.g., "no binding helper exists so a bare `3` is parsed as literal 3 → demo tier instead of option 3 → medium"; "conversation-protocol.md has no final-message invariant"; "completion steering has no recap/transition ordering rule")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Buggy Turns Unchanged
  - **IMPORTANT**: Follow observation-first methodology — run the UNFIXED code/steering for non-buggy inputs, record actual outputs, then write tests asserting those outputs hold across the input domain
  - Create `senzing-bootcamp/tests/test_turn_handling_preservation.py` (class-based, `sys.path` import of `scripts/`, `st_`-prefixed strategies, `@settings`, requirement-naming docstrings)
  - Observe + assert: `parse_volume_input` invariance — for any reply that is NOT a bare matching Option_Token (free text, number-with-units like `"3 million"`, `"around 3"`, out-of-range numbers, whitespace, empty), the Module 6 outcome equals the pre-fix `parse_volume_input` → `classify_tier` result. Capture pre-fix outputs across a generated corpus and assert byte-for-byte equality (Req 3.4).
  - Observe + assert: clarifying-follow-up preserved — an unparseable reply still triggers the numbered-list clarifying question and then defaults to the demo tier if still unparseable (Req 3.4).
  - Observe + assert: affirmative transition preserved — the steering still requires immediate module start (start banner, journey map, before/after framing, Step 1 introduction, ≥50 chars) on affirmative confirmation (Req 3.1).
  - Observe + assert: One Question Rule + `.question_pending` lifecycle preserved — exactly one 👉 per yielding turn, and the write / treat-next-message-as-answer / delete-before-processing lifecycle is unchanged (Req 3.2, 3.3).
  - Observe + assert: completion fixed-step order + artifacts preserved — the five-step order (progress_update, recap_append, journal_entry, completion_certificate, next_step_options) and per-module artifacts, plus defer-when-pending and no-op-when-nothing-new, are unchanged (Req 3.6).
  - Observe + assert: pure-work-turn closing preserved — a turn that does NOT end with a 👉 question still recaps and ends with a contextual 👉 closing question (Req 3.5).
  - Property (boundary): for any reply that is NOT a bare matching token, `bind_option(...) is None` AND the Module 6 result equals the unchanged `parse_volume_input` outcome.
  - Property: for any volume input string, `parse_volume_input` output is identical pre- and post-fix.
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for turn answer handling (binding-first + final-message invariant)

  - [x] 3.1 Add the `answer_binding` helper (Item 2 core logic)
    - Create `senzing-bootcamp/scripts/answer_binding.py` (new, stdlib-only) following script conventions: shebang, `from __future__ import annotations`, module docstring, type hints, `main(argv=None)` / argparse entry point.
    - `parse_option_token(reply: str) -> str | None`: return the normalized bare Option_Token (single number `"3"`, `"3."`, `"(3)"`, `" 3 "`; single letter `"b"`, `"B)"`, `"b."`), or `None` when the reply carries additional free-text meaning (`"3 million"`, `"around 3"`, `"option three please ..."`, `""`, whitespace).
    - `bind_option(reply: str, options: list[str]) -> int | None`: using `parse_option_token`, return the 1-based index of the bound option, or `None` when not a bare token or the token is out of range; letters map case-insensitively (`a`→1, `b`→2, …).
    - `is_bare_matching_token(reply: str, options: list[str]) -> bool`: `bind_option(...) is not None`, mirroring `isBareMatchingToken` in the bug condition.
    - _Bug_Condition: isBugCondition(turn) — unboundMatchingTokenAnswer branch (priorQuestionHasOptionList AND isBareMatchingToken AND NOT replyBoundToPendingQuestion)_
    - _Expected_Behavior: bind a bare matching token to the presented option, consume it, advance without re-ask (Property 1, Item 2)_
    - _Preservation: leave `volume_utils.parse_volume_input` and the clarifying-follow-up path untouched (Property 2)_
    - _Requirements: 2.3, 2.4_

  - [x] 3.2 Wire Module 6 Step 1 to bind-first (Item 2 steering)
    - Edit `senzing-bootcamp/steering/module-06-phaseA-build-loading.md`, Phase A Step 1 "Assess production record volume" Volume Classification instruction.
    - Add binding-first instruction: when the volume question (or its clarifying follow-up) presented the numbered option list, FIRST attempt `answer_binding.bind_option` against that list; provide the option→tier map (1→demo, 2→small, 3→medium, 4→large) so a bound index selects the tier directly.
    - Only when `bind_option` returns `None` fall through to the existing `volume_utils.parse_volume_input` → `classify_tier` path (preserves clarifying-follow-up + demo-default).
    - After a successful bind, persist via the existing `volume_utils.persist_volume_selection` and advance; do NOT re-present the Module 6 banner or volume question.
    - _Bug_Condition: isBugCondition(turn) — unboundMatchingTokenAnswer branch_
    - _Expected_Behavior: bound index selects tier, persists, advances without re-ask (Property 1, Item 2)_
    - _Preservation: fall-through to unchanged parse_volume_input for non-matching replies (Property 2, Req 3.4)_
    - _Requirements: 2.3, 2.4_

  - [x] 3.3 Make the final-message invariant explicit + fix completion ordering (Item 1 steering)
    - Edit `senzing-bootcamp/steering/conversation-protocol.md`: state explicitly that every input-expecting turn ends with exactly one **live** 👉 pending question as the **final message**, with `config/.question_pending` written for it; a recap/confirmation emission must never be the final message of an input-expecting turn.
    - Edit `senzing-bootcamp/steering/module-completion.md` and `module-completion-next-steps.md`: require the per-module recap/confirmation to run **before** the forward transition question, OR that the forward 👉 "Ready for Module X?" question is **re-surfaced as the final message** after any recap/confirmation, with `config/.question_pending` (re)written for it. Keep the fixed completion step order and the defer-when-pending / no-op trigger rules intact.
    - Reaffirm (no behavioral change) the affirmative-transition commitment so this part does not weaken the immediate module-start requirement.
    - _Bug_Condition: isBugCondition(turn) — endsWithoutLivePendingQuestion branch (expectsInput AND NOT lastMessageIsLivePendingQuestion)_
    - _Expected_Behavior: input-expecting turn ends with exactly one live 👉 pending question and writes config/.question_pending (Property 1, Item 1)_
    - _Preservation: One Question Rule, .question_pending lifecycle, completion fixed-step order/artifacts unchanged (Property 2, Req 3.2, 3.3, 3.6)_
    - _Requirements: 2.1, 2.2_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - One Live Pending Question, Answers Bound
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes it confirms the expected behavior is satisfied
    - Run the bug condition exploration test from task 1 (binding asserts + steering-invariant asserts)
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed — bare tokens bind to options; steering invariants present)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy Turns Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run the preservation property tests from task 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — `parse_volume_input` invariant, clarifying path, affirmative transition, One Question Rule + lifecycle, completion order/artifacts all unchanged)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Add focused unit and integration tests
  - Unit — `parse_option_token`: numbers (`"3"`, `"3."`, `"(3)"`), letters (`"b"`, `"B)"`), and `None` for free-text/mixed (`"3 million"`, `"around 3"`, `""`, whitespace).
  - Unit — `bind_option`: in-range numeric/lettered binds (1-based), out-of-range → `None`, non-token → `None`, case-insensitive letters.
  - Unit — Module 6 option→tier mapping: bound index 1/2/3/4 → demo/small/medium/large.
  - Unit — steering presence checks: final-message invariant in `conversation-protocol.md`; recap-before-transition / re-surface rule in completion steering.
  - Integration — Module 6 Step 1 end-to-end: present options 1–4, reply `3` binds to medium, persists via `persist_volume_selection`, advances without re-asking (Property 1).
  - Integration — Module-completion turn end-to-end: a completion turn that expects input ends with the forward 👉 "Ready for Module X?" as the final message with `config/.question_pending` written, even when a recap/confirmation is emitted (Property 1, Item 1).
  - Integration — Affirmative-transition flow: confirming "Ready for Module X?" still starts Module X immediately with all required start content (Property 2 preservation).
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Run the full power test suite (`pytest` in `senzing-bootcamp/tests/`) plus the binding/preservation/integration tests added here.
  - Confirm CI checks remain green (`validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest).
  - Ensure all tests pass; ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": ["1"],
      "description": "Bug Condition exploration test — must FAIL on unfixed code (confirms the bug)."
    },
    {
      "wave": 2,
      "tasks": ["2"],
      "description": "Preservation property tests — must PASS on unfixed code (baseline to preserve)."
    },
    {
      "wave": 3,
      "tasks": ["3.1", "3.3"],
      "description": "Implementation that can proceed in parallel: the answer_binding helper (3.1) and the steering invariant + completion ordering fix (3.3)."
    },
    {
      "wave": 4,
      "tasks": ["3.2"],
      "description": "Module 6 Step 1 bind-first wiring — depends on the helper from 3.1."
    },
    {
      "wave": 5,
      "tasks": ["3.4", "3.5"],
      "description": "Validation: re-run task 1 (now PASSES) and task 2 (still PASSES) after implementation (3.1–3.3)."
    },
    {
      "wave": 6,
      "tasks": ["4"],
      "description": "Focused unit + integration tests — depend on the implementation (3.1–3.3)."
    },
    {
      "wave": 7,
      "tasks": ["5"],
      "description": "Checkpoint — full suite + CI; depends on everything."
    }
  ]
}
```

**Ordering rules:**
- Tasks 1 and 2 MUST precede any fix work (exploration-first, observation-first).
- 3.2 depends on 3.1 (wiring consumes the helper). 3.3 is independent and can proceed in parallel with 3.1.
- 3.4 and 3.5 run only after the implementation sub-tasks (3.1–3.3) are complete.
- Task 4 depends on the implementation (3.1–3.3); Task 5 depends on everything.

## Notes

- All tests are stdlib-only (pytest + Hypothesis); no third-party dependencies are introduced.
- Property 1 (Bug Condition, Requirements 2.1–2.4) is encoded by the task 1 exploration test: it FAILS on unfixed code and PASSES after the fix.
- Property 2 (Preservation, Requirements 3.1–3.6) is encoded by the task 2 tests: they PASS on unfixed code and MUST still PASS after the fix.
- For the deterministic Item 2 binding bug, the property is scoped to concrete presented option lists (four-tier volume options and a generic a/b/c list) with bare tokens generated across the option range.
- `volume_utils.parse_volume_input` is unchanged; it is only the fall-through path for replies that are not a bare matching Option_Token.
- Steering edits must keep external URLs out of steering files and the MCP URL confined to `mcp.json`, per workspace security rules.
