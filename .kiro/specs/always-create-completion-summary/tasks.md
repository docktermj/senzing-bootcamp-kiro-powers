# Implementation Plan

## Overview

This is a steering-contract-only fix: the post-completion flow is reworked so `docs/completion_summary.md` is always generated during the stopping-point/graduation flow, with the yes/no offer re-scoped to govern only the shareable PDF/share (render and surface the PDF on "yes", skip just the PDF/share on "no"). The bug — declining the offer currently suppressed creation of the summary file entirely — is corrected in the steering contracts (`completion-summary-offer.md`, with anchor notes in `graduation.md` and `module-completion.md`); `generate_completion_summary.py` requires no behavioral change, since `main()` already writes the markdown unconditionally and gates only the PDF behind `--pdf`.

## Tasks

- [x] 1. Write bug condition exploration suite (BEFORE implementing fix)
  - **Property 1: Bug Condition** — Completion-summary creation is gated behind the yes/no answer
  - **CRITICAL**: This suite MUST FAIL on the unfixed steering files — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: These assertions encode the fixed contract — they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples demonstrating that `completion-summary-offer.md` gates artifact creation on the answer, and confirm the root cause lives in the steering contract (not the script)
  - **Scoped PBT Approach**: The bug is deterministic in steering text, so scope the content assertions to the concrete `completion-summary-offer.md` sections; use Hypothesis only to enumerate the bug-condition input space (`offerAnswer != "yes"`)
  - Create test file `senzing-bootcamp/tests/test_always_create_completion_summary_exploration.py` using pytest + Hypothesis (stdlib + Hypothesis only, class-based, type hints, `@settings(max_examples=20)`, `st_`-prefixed strategies)
  - Import the script via `sys.path` manipulation (`_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"`); read the steering file from `senzing-bootcamp/steering/completion-summary-offer.md`
  - Bug Condition from design: `isBugCondition(X) = X.stoppingPointDetected AND X.offerAnswer != "yes"`
  - **Test 1 — Decline does not gate creation (steering, FAILS on unfixed)**: assert `completion-summary-offer.md` does **NOT** contain the gating clause `"without generating any summary file"`
  - **Test 2 — Unconditional generation step present (steering, FAILS on unfixed)**: assert the file contains an unconditional generation step (e.g. a `## Always Generate the Summary Document` heading) that references running `generate_completion_summary.py` (markdown, no `--pdf`) before/independent of the yes/no answer
  - **Test 3 — Offer re-scoped to PDF/share (steering, FAILS on unfixed)**: assert the `## Prompt Format` section ties `"yes"` to `--pdf`/surfacing and `"no"` to skipping **only** PDF/share (not file creation)
  - **Test 4 — Markdown always written (script, PASSES on unfixed)**: in a temp dir, write a valid `session_log.jsonl`, progress JSON, and preferences YAML, run `main([...])` with no `--pdf` (point `--output`/`--log`/`--progress`/`--preferences` at the temp paths) and assert `completion_summary.md` is created — confirms Change 4's "no script change" claim and pins the behavior the contract relies on
  - **PBT — Bug condition enumeration**: use `st_offer_answer()` (drawing `"no"` and other non-`"yes"` strings) and `st_stopping_point_type()` (Module 7 / Module 11 / explicit stop / track switch) to assert `isBugCondition` holds for every `offerAnswer != "yes"` at a detected stopping point
  - Run the suite on the UNFIXED files
  - **EXPECTED OUTCOME**: Tests 1–3 FAIL (prove the creation gate); Test 4 PASSES (confirms root cause is the steering contract, not the script)
  - Document counterexamples found (unfixed file still contains `"without generating any summary file"` and ties creation to `"yes"`)
  - Mark task complete when the suite is written, run, and the failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** — Surrounding behavior and the published steering contract are unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe UNFIXED behavior, snapshot it, then assert
  - Create test file `senzing-bootcamp/tests/test_always_create_completion_summary_preservation.py` using pytest + Hypothesis (stdlib + Hypothesis only, class-based, type hints, `@settings(max_examples=20)`, `st_`-prefixed strategies)
  - **Observation phase**: snapshot the UNFIXED `## Stopping Point Detection Rules`, `## False Positive Guards`, `## Ordering Rules`, and `## Repeat Policy` sections of `completion-summary-offer.md`; snapshot `graduation.md` `## Step 0: Recap PDF Generation` and `## Graduation Report`; snapshot `module-completion.md` `## Path Completion Celebration` ordering
  - **Test — Published contract tokens preserved (re-assert existing `TestSteeringFileContent` checks)**: assert `completion-summary-offer.md` still has YAML frontmatter, the four content categories (`questions asked`, `answers given`, `actions taken`, `artifacts created`), the literal `Completion Summary PDF`, the `yes/no` phrasing, the celebration/🎉 reference, and the `export` reference
  - **Test — Detection / ordering / repeat policy unchanged**: assert the four detection rules, the false-positive guards, the track-completion + mid-session + simultaneous ordering, and the repeat policy text are byte-identical to the snapshot
  - **Test — graduation.md Step 0 + Graduation Report untouched**: assert the recap-PDF attempt (Step 0a/0b/0c) and the "Always generate `production/GRADUATION_REPORT.md`" behavior are unchanged
  - **Test — module-completion.md celebration ordering unchanged**: assert the celebration → completion-summary offer → export → record export → analytics → certificate → graduation offer → feedback reminder ordering is preserved
  - **Test — existing suites still pass**: assert (and re-run) `test_completion_summary_unit.py`, `test_completion_summary_properties.py`, and `test_completion_summary_integration.py` continue to pass unchanged
  - **PBT — Non-bug-condition equivalence (`F(X) = F'(X)`)**: use `st_offer_answer()` restricted to `"yes"` plus a "no stopping point" case to assert the preserved sections drive identical behavior under both F and F'
  - Run on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 3. Write the always-create property suite (BEFORE implementing fix)
  - Create test file `senzing-bootcamp/tests/test_always_create_completion_summary_properties.py` using pytest + Hypothesis (stdlib + Hypothesis only, class-based, type hints, `@settings(max_examples=20)`, `st_`-prefixed strategies)
  - These properties exercise the **script contract** the steering relies on; because no script change is required, they PASS on the current script and pin the behavior the fix depends on
  - Add `st_session_log()` generating varied multi-module session logs (reuse `st_completion_entry` / `st_completion_entry_inputs` patterns from `test_completion_summary_properties.py`); write each generated log to a temp `session_log.jsonl` alongside minimal progress JSON and preferences YAML
  - **Property 3: Fix — Markdown always created regardless of answer** (design Property 1): for varied logs, run `main([...])` with no `--pdf` and assert `completion_summary.md` exists with per-module `## Module N:` sections — the markdown's existence is independent of any yes/no answer. _Requirements: 2.1, 2.2, 2.4_
  - **Property 4: Fix — Answer governs only the PDF** (design Property 2): for the same logs, `main([..., "--pdf"])` creates both the markdown and the PDF, while `main([...])` creates only the markdown — modeling that the secondary concern (PDF/share) is the only thing the yes/no toggles. Guard the PDF assertion on `ensure_fpdf2()` (skip if fpdf2 unavailable). _Requirements: 2.2, 2.3, 2.6_
  - **Property 5: Fix — Graceful degradation on empty/whitespace log** (design Property 3): with a generated empty/whitespace `session_log.jsonl`, `main([...])` still produces markdown with the "Session log was unavailable" rendering and does not crash. _Requirements: 2.5, 3.9_
  - **Property 6: Preservation — Script invariants unchanged** (design Property 4): reuse `st_completion_entry` / `st_completion_entry_inputs` to re-assert module-ascending section ordering, the four-subsection presence per module, and metadata completeness via `build_narrative` / `render_markdown`. _Requirements: 3.8_
  - Run on the UNFIXED script
  - **EXPECTED OUTCOME**: All properties PASS on the current script (confirms "no script change needed" and pins the contract)
  - Mark task complete when the suite is written, run, and passing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.8, 3.9_

- [x] 4. Fix — always create the completion-summary document; re-scope the yes/no to PDF/share

  - [x] 4.1 Add the unconditional generation step to `completion-summary-offer.md`
    - Add a new `## Always Generate the Summary Document` subsection placed **before** `## Summary Offer Message Format`
    - Instruct that when a stopping point is detected, the agent runs `python3 senzing-bootcamp/scripts/generate_completion_summary.py` (markdown, no `--pdf`) **unconditionally**, **before** presenting the offer — this always writes `docs/completion_summary.md`
    - Make it **non-blocking**: on non-zero exit or raise (e.g. missing/unreadable `config/session_log.jsonl` → `parse_session_log` raises and `main()` returns 1), log a warning (`⚠️ Completion summary generation skipped: <reason>. Continuing.`) and continue the post-completion flow
    - Note that an empty-but-present session log still produces a valid markdown file with per-module "Session log was unavailable for this module." rendering, so it is not an error path
    - _Bug_Condition: isBugCondition(X) = X.stoppingPointDetected AND X.offerAnswer != "yes" — decline currently skips creation_
    - _Expected_Behavior: docs/completion_summary.md is created at every stopping point regardless of the yes/no answer_
    - _Preservation: detection / ordering / repeat-policy sections untouched_
    - _Requirements: 2.1, 2.4, 2.5, 3.9_

  - [x] 4.2 Rewrite `## Prompt Format` in `completion-summary-offer.md`
    - Reframe so the binary yes/no governs **only** the secondary concern:
      - `"yes"` → render the shareable PDF by running `python3 senzing-bootcamp/scripts/generate_completion_summary.py --pdf` (→ `docs/completion_summary.pdf`) and surface the path(s) to the bootcamper
      - `"no"` → skip **only** the PDF render + surfacing/sharing, then proceed to the next post-completion step without re-prompting for the same stopping point; `docs/completion_summary.md` remains created either way
    - Remove the clause `"without generating any summary file"`
    - Keep the literal `yes/no` phrasing intact (required by `test_steering_file_binary_prompt`)
    - _Bug_Condition: the decline branch suppressed BOTH the primary artifact AND the secondary concern_
    - _Expected_Behavior: yes/no governs only PDF rendering / surfacing of the always-created summary_
    - _Preservation: `yes/no` token retained for `test_steering_file_binary_prompt`_
    - _Requirements: 2.2, 2.3, 2.6_

  - [x] 4.3 Reframe `## Summary Offer Message Format` in `completion-summary-offer.md`
    - Rewrite the offer message so it states the summary is already captured at `docs/completion_summary.md` and the choice is about the shareable PDF
    - PRESERVE the literal string `Completion Summary PDF`, all four content categories (questions asked, answers given, actions taken, artifacts created), and the "organized by module" statement (asserted by `test_steering_file_names_deliverable` and `test_steering_file_mentions_four_categories`)
    - _Expected_Behavior: offer message reframed to PDF/share of the always-created summary_
    - _Preservation: existing `TestSteeringFileContent` tokens preserved_
    - _Requirements: 2.6_

  - [x] 4.4 Leave the remaining `completion-summary-offer.md` sections unchanged
    - Do **NOT** modify `## Stopping Point Detection Rules`, `## False Positive Guards`, `## Ordering Rules`, `## Repeat Policy`, or the frontmatter (`inclusion: manual`, triggers, priority)
    - _Preservation: stopping-point detection, ordering, and repeat policy unchanged_
    - _Requirements: 3.1, 3.4, 3.5, 3.7_

  - [x] 4.5 Anchor the always-create note in `graduation.md`
    - In/near `## Step 0: Recap PDF Generation`, add a short note stating that — independent of the recap PDF — the completion-summary document (`docs/completion_summary.md`) is **always** generated during the post-completion/graduation flow via `generate_completion_summary.py`, non-blocking, in the same spirit as the recap PDF and `GRADUATION_REPORT.md`
    - Do **NOT** alter Step 0a/0b/0c, Steps 1–5, or `## Graduation Report`
    - _Bug_Condition: no unconditional always-create step was anchored in the graduation flow_
    - _Expected_Behavior: graduation flow documents the always-created, non-blocking completion summary_
    - _Preservation: recap PDF + GRADUATION_REPORT.md behavior verbatim_
    - _Requirements: 2.1, 2.5, 3.3_

  - [x] 4.6 Clarify the celebration ordering note in `module-completion.md`
    - In `## Path Completion Celebration`, add a one-line clarification that the completion-summary document is always created at track completion, with the offer in its existing position governing only the PDF/share
    - Keep the existing ordering (celebration → completion-summary offer → export results → record export → analytics → certificate → graduation offer → feedback reminder) unchanged
    - _Expected_Behavior: celebration ordering text stays consistent with the re-scoped offer_
    - _Preservation: ordering unchanged_
    - _Requirements: 2.6, 3.4_

  - [x] 4.7 Confirm NO behavioral change to `generate_completion_summary.py`
    - Verify `main()` always parses → builds → renders → calls `write_narrative(args.output, ...)`, and that the PDF is produced only inside the `if args.pdf:` branch — so `main([])` writes `docs/completion_summary.md` without `--pdf`
    - Do **NOT** modify the script's internals; the missing/unreadable-log hard-failure path is handled at the steering layer (task 4.1), not in the script
    - This behavior is pinned by exploration Test 4 (task 1) and property suite Property 3 (task 3) — no new code change
    - _Expected_Behavior: script already supports unconditional markdown generation; PDF stays gated behind `--pdf`_
    - _Preservation: script internals and existing unit/property/integration coverage unchanged_
    - _Requirements: 2.1, 3.8_

  - [x] 4.8 Refresh steering token budgets
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to refresh `token_count`/`size_category` in `steering/steering-index.yaml` for the edited steering files (`completion-summary-offer.md`, `graduation.md`, `module-completion.md`)
    - _Preservation: CI `measure_steering.py --check` stays green_
    - _Requirements: 3.8_

  - [x] 4.9 Verify bug condition exploration suite now passes
    - **Property 1: Expected Behavior** — Completion summary always created; yes/no governs only PDF/share
    - **IMPORTANT**: Re-run the SAME suite from task 1 (`test_always_create_completion_summary_exploration.py`) — do NOT write a new test
    - Run: `python -m pytest senzing-bootcamp/tests/test_always_create_completion_summary_exploration.py -v`
    - **EXPECTED OUTCOME**: All pass — Tests 1–3 now PASS (gate removed; unconditional step + re-scoped prompt present); Test 4 still PASSES
    - _Requirements: 2.1, 2.2, 2.3, 2.6_

  - [x] 4.10 Verify preservation + always-create property suites still pass
    - **Property 2: Preservation** — Surrounding behavior and published contract unchanged
    - **IMPORTANT**: Re-run the SAME tests from tasks 2 and 3 — do NOT write new tests
    - Run: `python -m pytest senzing-bootcamp/tests/test_always_create_completion_summary_preservation.py senzing-bootcamp/tests/test_always_create_completion_summary_properties.py senzing-bootcamp/tests/test_completion_summary_unit.py senzing-bootcamp/tests/test_completion_summary_properties.py senzing-bootcamp/tests/test_completion_summary_integration.py -v`
    - **EXPECTED OUTCOME**: Tests PASS — existing `TestSteeringFileContent` checks still satisfied (frontmatter, four categories, `Completion Summary PDF`, `yes/no`, celebration, export); graduation Step 0 / `GRADUATION_REPORT.md` untouched; no regressions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

- [x] 5. Checkpoint — Ensure all tests pass
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to confirm token budgets are in sync
  - Run `python3 senzing-bootcamp/scripts/validate_power.py` and `python3 senzing-bootcamp/scripts/lint_steering.py` to confirm power structure and steering linting pass
  - Run the full suite: `python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short`
  - Ensure all tests pass; ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2", "3"] },
    { "id": 2, "tasks": ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7"] },
    { "id": 3, "tasks": ["4.8"] },
    { "id": 4, "tasks": ["4.9"] },
    { "id": 5, "tasks": ["4.10"] },
    { "id": 6, "tasks": ["5"] }
  ]
}
```

Task 1 (bug condition exploration suite) must complete first so the failures are documented on unfixed code. Tasks 2 and 3 (preservation tests and the always-create property suite) can be authored in parallel against the unfixed baseline. The steering/script edits 4.1–4.7 can proceed in parallel once the baseline is captured (4.7 is a verify-only no-op confirming the script needs no change). Task 4.8 (token refresh) runs after the steering edits land. Task 4.9 (re-run exploration suite — now passing) depends on the steering edits. Task 4.10 (re-run preservation + property suites) depends on 4.8 and 4.9. Task 5 (final checkpoint) depends on 4.10.

## Notes

- The fix is realized **entirely in the steering contracts** (`completion-summary-offer.md` primary, with anchor notes in `graduation.md` and `module-completion.md`). `generate_completion_summary.py` needs **no behavioral change** — `main()` already writes `docs/completion_summary.md` unconditionally and gates only the PDF behind `--pdf`.
- The bug condition is `C(X) = X.stoppingPointDetected AND X.offerAnswer != "yes"`. Fix checking asserts the markdown is always created for `C(X)`; preservation checking asserts `F(X) = F'(X)` for the accepted path and non-stopping situations.
- Because the bug lives in steering text, the exploration suite asserts on the **contract content** of `completion-summary-offer.md` and on the **script behavior** it relies on; only the steering-content assertions fail on unfixed code, while the script assertion passes (confirming the root cause is the contract, not the script).
- PDF-dependent assertions (Property 4) must guard on `ensure_fpdf2()` so the suite degrades gracefully where fpdf2 is unavailable, consistent with the existing integration test's skip behavior.
