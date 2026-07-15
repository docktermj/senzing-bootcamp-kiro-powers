# Implementation Plan: Mandatory Question Answers

## Overview

Make "every question must be answered by the bootcamper; the agent never assumes or silently defaults" a universal, enforced guarantee. Remove the two Assumed_Answer paths (verbosity silent default, skippable comprehension check), add one normative Answer_Required_Rule, express optionality as an Explicit_Default_Choice, align the existing hooks, and update tests. Preserve the legitimate load-time preference fallback.

## Tasks

- [x] 1. Add the normative Answer_Required_Rule
  - Add a single normative rule to `steering/conversation-protocol.md`: every `👉` question requires a Real_Answer before advancing; the agent never fabricates, assumes, or silently defaults; the only exits are a Real_Answer or the question staying outstanding; optionality is an Explicit_Default_Choice.
  - Reference the rule from `steering/agent-behavior-rules.md` and `steering/agent-instructions.md`.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1_

- [x] 2. Remove the verbosity silent default
  - In the Detail_Level_Step (onboarding verbosity step), delete the "if the bootcamper skips without answering, apply the `standard` preset as the default" instruction.
  - Mark the step as a mandatory gate (⛔) and keep the `🛑 STOP` wait directive.
  - Keep "standard *(recommended)*" as an Explicit_Default_Choice; persist `standard` to `config/bootcamp_preferences.yaml` only when the bootcamper selects it.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Make the comprehension check require a response
  - Reword the Any_Questions_Step so it requires a Real_Answer; keep the clarification→answer→re-present loop until the bootcamper signals readiness.
  - Remove "not a gate / can skip it" phrasing that would authorize advancing with no answer.
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Sweep the corpus for Assumed_Answer phrasings
  - [x] 4.1 Find and reword remaining silent-default / proceed-without-answer phrasings
    - Grep `steering/` for "apply … default", "skips without answering", "proceed without", "not a gate … skip" tied to `👉` questions; reword each to require a Real_Answer or an Explicit_Default_Choice.
    - Explicitly preserve the load-time missing-preference fallback in `verbosity-control.md` (annotate it as a load-time fallback, not an unanswered-question path).
    - _Requirements: 4.2, 4.5, 5.4_
  - [x] 4.2 Resolve the Advanced_Knowledge_Check ambiguity
    - Either require a Real_Answer to its `👉` question, or reword it to not present a `👉` question if it is truly skippable — the agent must never answer it for the bootcamper.
    - _Requirements: 5.3_

- [x] 5. Align enforcement hooks
  - [x] 5.1 Extend `write-policy-gate`
    - Add a check to the hook prompt: block/rewrite a write that marks a question-owning step complete (progress/preferences) without a recorded Real_Answer for that step.
    - _Requirements: 4.4_
  - [x] 5.2 Reaffirm `ask-bootcamper`
    - Confirm its prompt forbids emitting content that advances past an unanswered `👉` question; preserve the `.question_pending` deferral.
    - _Requirements: 4.3_
  - [x] 5.3 Sync the hook registry
    - Update hook registry entries and run `sync_hook_registry.py --verify`.
    - _Requirements: 4.4_

- [x] 6. Tests
  - [x] 6.1 Update onboarding tests
    - Update `test_comprehension_check.py`, `test_onboarding_question_ownership.py`, `test_onboarding_session_ux.py`, and any verbosity-onboarding test to assert the mandatory/no-silent-default behavior.
    - _Requirements: 6.1, 6.2_
  - [x] 6.2 Add corpus-sweep and rule-presence tests
    - Assert `conversation-protocol.md` contains the Answer_Required_Rule; assert no `👉`-tied Assumed_Answer phrasing remains outside the allowlisted load-time fallback; assert `write-policy-gate.json` contains the new check.
    - _Requirements: 6.3_
  - [x] 6.3 Consistency cross-check
    - Verify no contradiction with `self-answering-prevention-v2`, `mandatory-gate-enforcement`, `eula-answer-skipped`, `agent-skips-git-question`, `skip-reflection-questions`.
    - _Requirements: 5.1, 5.2_

- [x] 7. Checkpoint - Verify
  - Run `python -m pytest senzing-bootcamp/tests/ tests/` green.
  - Run `sync_hook_registry.py --verify` and `validate_commonmark.py` on edited Markdown.
  - Manual trace: verbosity step with no input → agent waits (no default); "use standard" → persists standard and proceeds.
  - _Requirements: 1.2, 6.4_

## Notes

- Optionality is preserved via Explicit_Default_Choice — the default stays one keystroke away, but the bootcamper must pick it.
- The load-time "missing verbosity key → standard" fallback is intentionally kept; it is not an unanswered question.
- This spec generalizes "no self-answering" to also forbid silent defaults; it pairs with `single-ask-question-guarantee` (a question with a recorded answer is neither re-asked nor assumed).
