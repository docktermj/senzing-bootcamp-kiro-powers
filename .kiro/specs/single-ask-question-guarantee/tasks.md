# Implementation Plan: Single-Ask Question Guarantee

## Overview

Make "ask each question at most once, unless the bootcamper requests a repeat" a durable, enforced guarantee. Add a persisted Question_Ledger and a stdlib helper, consolidate the scattered "do not re-ask" steering notes into one normative rule, teach the `ask-bootcamper` and `review-bootcamper-input` hooks to use the ledger and honor repeat requests, and cover it with tests.

## Tasks

- [x] 1. Build the ledger helper script
  - [x] 1.1 Implement `scripts/question_ledger.py`
    - Stdlib-only, argparse `main(argv=None)`, `record-asked` / `mark-answered` / `is-answered` / `get-pending` subcommands; `LedgerEntry` dataclass; JSONL read/write; per-member path resolution (`config/question_ledger.jsonl` or `_{member_id}`).
    - Idempotent `record-asked`; `mark-answered` upsert; missing/malformed file tolerated as empty.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 1.3, 1.4, 1.5_
  - [x] 1.2 Property-based tests `test_question_ledger.py`
    - `st_question_key()` strategy; idempotency, answer-supersedes, malformed-tolerance, round-trip properties.
    - _Requirements: 6.1_

- [x] 2. Wire the ledger into the question lifecycle (steering)
  - [x] 2.1 Add the normative Ask-Once Guarantee rule
    - Add the single normative rule to `steering/conversation-protocol.md` (consult ledger before asking; never re-ask answered questions; ledger authoritative across compaction/resume; repeat only via Repeat_Request).
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 4.2_
  - [x] 2.2 Record/mark ledger entries at question boundaries
    - Update `steering/agent-instructions.md` and `steering/module-transitions.md` (checkpoint emission) so presenting a `👉` question records its Question_Key as `asked` and processing an answer marks it `answered`, alongside the existing `current_step`/`step_history` checkpoints.
    - Define the Question_Key scheme (`onboarding.<step>`, `module.<N>.<step>`, `global.<name>`) and have step-owning files name their keys.
    - _Requirements: 1.1, 1.2, 2.2_
  - [x] 2.3 Consolidate the scattered "do not re-ask" notes
    - Reframe the Module 8 hardware-question note (`module-09-phaseA-assessment.md`, `module-11-phase1-packaging.md`) and the session-resume preference-field note (`session-resume.md`) as instances of the general guarantee, cross-referencing the normative rule. Assign `global.hardware_target` and `onboarding.*` keys.
    - _Requirements: 4.3, 2.4_

- [x] 3. Enforce via hooks
  - [x] 3.1 Update `ask-bootcamper` hook
    - Add a ledger-consult step to the hook prompt: do not emit a closing question that duplicates an already-answered Question_Key for the current step; advance using the stored answer. Preserve the `.question_pending` deferral.
    - _Requirements: 4.1_
  - [x] 3.2 Update `review-bootcamper-input` hook
    - Add Repeat_Request trigger phrases and route them to re-present the current Pending_Question verbatim with no new ledger entry and unchanged answered status; handle the no-pending-question case.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 3.3 Keep the hook registry in sync
    - Update the hook registry steering entries for both hooks and run `sync_hook_registry.py --verify`.
    - _Requirements: 4.1, 4.2_

- [x] 4. Tests and safety net
  - [x] 4.1 Content/hook tests
    - Assert the normative rule exists in `conversation-protocol.md`; assert referencing (not duplicating) in the other two rule files; assert both hook prompts contain the ledger-consult / repeat-phrase instructions.
    - _Requirements: 6.2, 6.3_
  - [x] 4.2 Degrade-safely assertion
    - Test that when the ledger is unavailable but the answer exists in preferences, the guidance still forbids re-asking (documented behavior / helper fallback).
    - _Requirements: 4.4_

- [x] 5. Checkpoint - Verify
  - Run `python -m pytest senzing-bootcamp/tests/ tests/` and confirm green.
  - Run `sync_hook_registry.py --verify` and confirm hook JSON schema validity.
  - Trace a resume scenario on paper: ledger has `onboarding.language_selection = answered` → resumed session does not re-ask language.
  - _Requirements: 2.4, 2.5, 6.4_

## Notes

- This spec governs the "how many times" dimension only; it defers question *shape* and *self-answering* to `single-question-format`, `self-answering-prevention-v2`, and `leading-question-enforcement`.
- The ledger is the source of truth across context compaction; conversational memory is not relied upon.
- `config/.question_pending` remains the marker for the single currently-outstanding question; the ledger adds durable answered-history.
