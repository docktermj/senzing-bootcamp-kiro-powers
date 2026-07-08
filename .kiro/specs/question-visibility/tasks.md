# Implementation Plan: Question Visibility (Bold Question Text)

## Overview

This plan layers a bold-emphasis cue onto every 👉 leading question across the senzing-bootcamp power. Because the extended `validate_behavior_rules.py` will flag *any* 👉 question whose text is not bold, the work is strictly ordered to keep CI green at every step:

1. Document the rule in the four authoritative steering files and update the canonical examples.
2. Convert every question-bearing steering file so no 👉 question is left un-bolded.
3. Make the `write-policy-gate.json` CHECK 2 strip bold markers before counting, then re-sync the hook registry.
4. Only *after* all content is converted, extend `validate_behavior_rules.py` to enforce the rule and add deterministic tests.
5. Re-sync `steering-index.yaml` token counts with `measure_steering.py`.
6. Run the full CI pipeline green.

All scripts are Python 3.11+ stdlib only. Tests are deterministic (example-based) and live in `senzing-bootcamp/tests/` as class-based pytest suites. The design has **no Correctness Properties section**, so there are no property-based (Hypothesis) tests for the bold rule — R10.4/R10.5 mandate no dependence on randomness.

## Tasks

- [x] 1. Document the bold-question rule in the four authoritative steering files
  - [x] 1.1 Add the bold clause to `agent-behavior-rules.md` Rule 4
    - Extend Rule 4 (Consistent Pointer Indicator) prose to state that the question text of every leading question is wrapped in bold **in addition to** the 👉 pointer, never as a replacement
    - Do not change the `## Rule 1`–`## Rule 4` heading structure (unit test `test_file_has_four_rule_sections` depends on it)
    - _Requirements: R2.1, R4.1_

  - [x] 1.2 Add the bold clause to `agent-instructions.md` Communication section
    - Update the Communication bullet so every input-requiring prompt is prefixed with 👉 **and** has its question text wrapped in bold
    - Keep the addition minimal; this file is `inclusion: always` and budget-sensitive
    - _Requirements: R4.2_

  - [x] 1.3 Add the bold rule, checklist item, and self-check item to `conversation-protocol.md`
    - Add a distinct, separately identifiable rule (e.g. `## Bold Question Text`): question text is bold; bold is additive to and does not replace 👉; in a choice question only the lead question is bold while numbered options stay plain; bold is presentational and does not alter the One Question Rule; question count per turn is driven by 👉 occurrences and is unaffected by bold markers; the 🛑 STOP marker stays plain
    - Add a Pre-Output Validation Checklist item confirming the closing question's text is bold before output
    - Add a Self-Check item verifying the closing question renders its text in bold
    - Update embedded CORRECT examples (Sub-Step Completion, Choice Formatting, Rewrite Examples) to show bold on the lead/question text; keep 🛑 STOP plain
    - _Requirements: R1.1, R1.3, R2.2, R3.4, R3.5, R4.3, R4.4, R4.5, R5.2, R7.1, R7.3, R7.5_

  - [x] 1.4 Update `conversation-examples.md` canonical examples
    - Bold the question text of every CORRECT non-choice example, keeping 👉 on the same line and outside the bold span
    - Bold the lead question of CORRECT choice examples; keep numbered options plain
    - Add a Missing-Bold example pair (`## Missing-Bold (WRONG)` with an un-bolded 👉 question, `## Missing-Bold (CORRECT)` with the same wording bolded) that differ *only* in the presence of `**`
    - Leave all WRONG examples intentionally un-bolded
    - _Requirements: R5.1, R5.3, R5.4_

  - [x] 1.5 Write deterministic content-assertion tests for the four authoritative files
    - New file `senzing-bootcamp/tests/test_bold_question_steering.py` (class-based, no randomness): assert `agent-behavior-rules.md` Rule 4 bold clause, `agent-instructions.md` Communication bold clause, `conversation-protocol.md` distinct bold rule + checklist item + self-check item, and `conversation-examples.md` bold CORRECT examples + a Missing-Bold pair that differs only by `**`
    - Assert `conversation-protocol.md` and `conversation-examples.md` render `🛑 STOP` plain (no bold)
    - _Requirements: R4.1, R4.2, R4.3, R4.4, R4.5, R5.1, R5.3, R5.4, R7.5_

- [x] 2. Convert every question-bearing steering file so no 👉 question is left un-bolded
  - [x] 2.1 Convert module 01–03 steering files
    - Bold the question text of every literal 👉 leading question in `module-01-*`, `module-02-sdk-setup.md`, `module-03-*`; keep 👉 on the same line and outside the span
    - For choice questions bold only the lead question; keep numbered options plain
    - For soft-wrapped questions use a single balanced `**...**` span that opens after 👉 and closes on the last line without crossing a blank line or numbered-list boundary
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.2 Convert module 04–06 steering files
    - Apply the same bold transformation to `module-04-*`, `module-05-*`, `module-06-*`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.3 Convert module 07–08 steering files
    - Apply the same bold transformation to `module-07-*`, `module-08-*`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.4 Convert module 09–11 steering files
    - Apply the same bold transformation to `module-09-*`, `module-10-*`, `module-11-*`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.5 Convert onboarding steering files
    - Apply the bold transformation to `onboarding-flow.md`, `onboarding-phase1b-intro-language.md`, `onboarding-phase2-track-setup.md`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.6 Convert session-resume steering files
    - Apply the bold transformation to `session-resume.md`, `session-resume-phase2-mapping.md`, `session-resume-phase2-setup-recovery.md`, `session-resume-phase2-state-repair.md`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.7 Convert feedback, visualization, and deployment steering files
    - Apply the bold transformation to `feedback-workflow.md`, `visualization-guide.md`, `deployment-aws.md`, `deployment-azure.md`, `deployment-gcp.md`, `deployment-kubernetes.md`, `deployment-onpremises.md`
    - _Requirements: R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

  - [x] 2.8 Sweep and convert any remaining question-bearing steering files
    - Search `senzing-bootcamp/steering/*.md` for lines that start with 👉 (after stripping blockquote `>` / list markers / whitespace) and bold any still-un-bolded question text (e.g. `module-transitions.md`, `module-completion*.md`, `module-prerequisites.md`, `track-switching.md`, `graduation.md`, `common-pitfalls.md`, `recovery-from-mistakes.md`, `skip-step-protocol.md`)
    - Leave inline `👉` mentions inside quotes/prose and `(WRONG)` examples untouched
    - _Requirements: R1.2, R2.3, R3.1, R3.2, R3.3, R11.1, R11.2, R11.3_

- [x] 3. Checkpoint - all question-bearing content converted before enforcement is activated
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Make the write-policy-gate compatible with bold markers
  - [x] 4.1 Update `write-policy-gate.json` CHECK 2 to strip bold markers before counting
    - Add an instruction at the top of CHECK 2 to remove all `**` bold-emphasis markers from the question content before evaluating rules 1–5 (single question mark, no joining conjunctions, no appended alternatives, unambiguous yes/no, no follow-up-after-confirmation)
    - Leave the schema (`version`, `hooks[].name/trigger/matcher/action`) and the existing `⚠️ COMPOUND QUESTION DETECTED` output format unchanged
    - _Requirements: R6.1, R6.2, R6.3, R6.4_

  - [x] 4.2 Re-sync the hook registry after the prompt edit
    - Run `python senzing-bootcamp/scripts/sync_hook_registry.py` so the registry reflects the changed prompt text and `sync_hook_registry.py --verify` (a CI step) stays green
    - _Requirements: R6.1_

  - [x] 4.3 Write deterministic hook-content tests for the gate
    - New file `senzing-bootcamp/tests/test_write_gate_bold_strip.py` (class-based, no randomness): assert CHECK 2 instructs stripping `**` before counting question marks / detecting conjunctions, and that rules 1–5 plus the `⚠️ COMPOUND QUESTION DETECTED` output format remain present
    - _Requirements: R6.1, R6.2, R6.4_

- [x] 5. Extend the behavior-rules validator to enforce the bold-question rule
  - [x] 5.1 Add bold-detection helper functions to `validate_behavior_rules.py`
    - Add `strip_bold(text)`, `question_text_is_bold(question_text)` (True iff a single balanced `**...**` span covers the whole trimmed text; italic/partial/unbalanced return False), `extract_question_block(lines, index)` (reconstruct a possibly soft-wrapped 👉 question, stripping blockquote/list markers), and `is_negative_example_context(lines, index)` (True when the nearest preceding heading contains `WRONG`)
    - Stdlib only, type-hinted, Google-style docstrings; reuse the existing `has_pointer_prefix()` helper and `Violation` dataclass
    - _Requirements: R10.1, R10.2, R10.3_

  - [x] 5.2 Extend `validate_steering_file` to flag 👉 questions lacking bold
    - Track fenced-code-block state and skip fenced content; for each 👉 line not in a negative-example context, call `extract_question_block()` then `question_text_is_bold()`, appending `Violation(rule=4, line_number=..., message=...)` with the offending question snippet on failure
    - Only lines that carry 👉 at start-of-line (after stripping blockquote/list markers) are candidates; prose, headings, numbered options, and inline `👉` mentions are never flagged; keep the existing CLI (`--check`, exit 0/1, per-file `path:` then `Line N [Rule 4]: <message>`)
    - _Requirements: R10.1, R10.2, R10.3_

  - [x] 5.3 Write deterministic unit tests for the bold detector
    - New file `senzing-bootcamp/tests/test_bold_question_validation_unit.py` (class-based, fixed input strings, no randomness): flags missing bold (no markers, italic-only, unbalanced, partial); accepts bold (plain, quoted question, choice lead with plain options, soft-wrapped span); scope (non-👉 lines, headings, options, inline mentions, fenced content never flagged); negative-example exemption (`(WRONG)` not flagged, `(CORRECT)` required bold); direct assertions on `strip_bold` / `question_text_is_bold`
    - _Requirements: R10.4, R10.5, R10.1, R10.2, R10.3_

  - [x] 5.4 Write a deterministic integration test over the real steering directory
    - In `senzing-bootcamp/tests/test_bold_question_steering.py`, run `validate_steering_file()` (or the `--check` CLI) over the actual `steering/` directory and assert zero Rule 4 violations now that conversion is complete
    - _Requirements: R11.1, R11.2, R11.3, R1.2, R1.4, R1.5, R2.3, R3.1, R3.2, R3.3_

- [x] 6. Re-sync token counts and validate the budget
  - [x] 6.1 Regenerate `steering-index.yaml` with `measure_steering.py`
    - Run `python senzing-bootcamp/scripts/measure_steering.py` (update mode) to refresh each modified file's `token_count`/`size_category` and the `budget.total_tokens` block after all steering edits
    - _Requirements: R9.1, R9.2, R9.3, R9.4, R9.5_

  - [x] 6.2 Assert the budget check passes on the synced index
    - Add a deterministic test (mirroring existing `test_measure_steering.py` / token-sync patterns) asserting `measure_steering.py --check` exits 0: per-file counts match, `budget.total_tokens` equals the sum, and the always-loaded footprint stays under the ceiling
    - _Requirements: R9.1, R9.2, R9.3_

- [x] 7. Final checkpoint - run the full CI pipeline green
  - Run the pipeline from `.github/workflows/validate-power.yml` in order — `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py` (R8.1, R8.2, R8.3, R8.4), `sync_hook_registry.py --verify`, then `pytest` — with the extended validator active and all question-bearing files converted
    - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Tests are deterministic and example-based (class-based pytest in `senzing-bootcamp/tests/`). There are no property-based/Hypothesis tests for the bold rule — R10.4/R10.5 require no dependence on randomness, wall-clock time, or external state.
- Ordering is a hard constraint: all question-bearing content (tasks 1–2) must be converted before the validator enforcement (task 5) is activated, or CI goes red. Task 3 is a checkpoint guarding that boundary.
- Each task references the specific requirement IDs (R-notation from the design/requirements) it satisfies.
- Scripts stay Python 3.11+ stdlib only; steering files stay valid CommonMark with balanced `**...**` spans.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "4.1"] },
    { "id": 1, "tasks": ["1.5", "4.2", "4.3", "5.1", "6.1"] },
    { "id": 2, "tasks": ["5.2", "6.2"] },
    { "id": 3, "tasks": ["5.3", "5.4"] }
  ]
}
```
