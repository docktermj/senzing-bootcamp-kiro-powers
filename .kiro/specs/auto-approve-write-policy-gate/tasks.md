# Implementation Plan

## Overview

This plan implements the auto-approve offer as steering content and a preference key — no new runtime scripts or hook changes. Work order: add the preference key, author the onboarding offer step, align Section 0a, re-sync the steering token budget, add tests, then run the full CI gate. The `write-policy-gate.kiro.hook` file is intentionally left untouched.

## Tasks

- [x] 1. Add the `write_policy_gate_auto_approve` preference key to the template
  - Add the key (default `null`, with an explanatory comment and the `accepted`/`declined` value legend) to `senzing-bootcamp/config/bootcamp_preferences.yaml.example`
  - Place it near the other onboarding-set keys, preserving existing entries
  - _Requirements: 4.1, 4.2_

- [x] 2. Author onboarding Step 1.2a (Auto-Approve Offer) in `onboarding-flow.md`
- [x] 2.1 Add the Step 1.2a section with preconditions and idempotency guard
  - Insert a new `### 1.2a` subsection directly after Step 1.2 (Install Critical Hooks) in `senzing-bootcamp/steering/onboarding-flow.md`
  - Gate presentation on `write-policy-gate` being confirmed installed; skip the step entirely if it was not installed
  - Before presenting, read `config/bootcamp_preferences.yaml` and skip the offer if `write_policy_gate_auto_approve` already holds a decision
  - _Requirements: 1.1, 1.5, 4.4_
- [x] 2.2 Write the offer block content
  - State that auto-approving removes the visible intercept ("Rejected"/"Accepted") cycle
  - Enumerate exactly the four safety checks (Senzing SQL blocking, single-question enforcement, file-path policy, root-placement policy) and state all remain active
  - State that any safety-check violation is still detected and blocked after auto-approval
  - Present exactly two selectable choices (accept / decline) and no others; mark the step as a ⛔ mandatory gate that stops for explicit input
  - _Requirements: 1.2, 1.3, 1.4, 3.1, 3.3_
- [x] 2.3 Write the response-branching instructions
  - Accept: provide ordered Agent Hooks panel steps to auto-approve `write-policy-gate` ("Ask Kiro Hook to process your response"), then record `accepted`
  - Decline: continue onboarding unchanged, tell the bootcamper it can be enabled later from the Agent Hooks panel, then record `declined`
  - Unrecognized response: re-present the offer and keep waiting without changing state
  - Awaiting / no selection: stay on the step, keep the intercept cycle active, make no auto-approve change
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 1.6_
- [x] 2.4 Write the preference-recording instructions (merge + failure handling)
  - Record the decision under `write_policy_gate_auto_approve` merging only that key and preserving all other content
  - File missing → create with only the new key; write failure → preserve existing content and inform the bootcamper it could not be saved; unparseable YAML → do not overwrite and inform the bootcamper
  - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 4.7_

- [x] 3. Align Section 0a with the offer in `onboarding-flow.md`
  - Update `## 0a. Why You May See "Rejected"/"Accepted" Messages` to reference the `Auto_Approve_Offer` by that exact term and state accepting it removes the visible messages for all subsequent `write-policy-gate` operations during onboarding
  - Frame the intercept cycle conditionally: suppressed for the remainder of onboarding when accepted, ongoing expected behavior when not
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 4. Re-sync steering token budget
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py` (update mode) so `steering/steering-index.yaml` `file_metadata` and `budget.total_tokens` reflect the edited `onboarding-flow.md`
  - Confirm `python3 senzing-bootcamp/scripts/measure_steering.py --check` passes
  - _Requirements: 1.1, 5.1_

- [x] 5. Add tests for onboarding content and the preference key
- [x] 5.1 Extend onboarding-structure tests
  - In `senzing-bootcamp/tests/test_onboarding_question_ownership.py` (or a new sibling test module), assert the Step 1.2a heading exists, names all four safety checks, and presents exactly two choices
  - Assert Section 0a contains the exact string `Auto_Approve_Offer` and references removal of the visible messages
  - _Requirements: 1.2, 1.3, 1.4, 5.1, 5.4_
- [x] 5.2 Add the hook-immutability test
  - Assert the SHA-256 of `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` matches a pinned baseline, following the pattern in `test_steering_index_token_count_sync_preservation.py`
  - _Requirements: 3.2_
- [x] 5.3 Add the preferences template test
  - Assert `bootcamp_preferences.yaml.example` contains `write_policy_gate_auto_approve` defaulting to `null`
  - _Requirements: 4.1, 4.2_
- [x] 5.4 Add the property-based preferences-merge test
  - Using Hypothesis over arbitrary valid preference maps, assert that setting `write_policy_gate_auto_approve` preserves all other keys/values and sets exactly the target value; cover the missing-file (create) and malformed-YAML (no clobber) cases
  - _Requirements: 4.3, 4.5, 4.7_

- [x] 6. Verify the full CI gate locally
  - Run `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then `pytest senzing-bootcamp/tests/` and confirm all pass
  - _Requirements: 3.2, 5.1_

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1"], "dependsOn": [] },
    { "wave": 2, "tasks": ["2.1", "5.2", "5.3"], "dependsOn": ["1"] },
    { "wave": 3, "tasks": ["2.2", "2.3", "2.4", "5.4"], "dependsOn": ["2.1"] },
    { "wave": 4, "tasks": ["3"], "dependsOn": ["2.2", "2.3", "2.4"] },
    { "wave": 5, "tasks": ["4", "5.1"], "dependsOn": ["3"] },
    { "wave": 6, "tasks": ["6"], "dependsOn": ["4", "5.1", "5.2", "5.3", "5.4"] }
  ]
}
```

- Task 1 is foundational (defines the key that Tasks 2.4 and 5.3/5.4 depend on).
- Task 2 sub-tasks are sequential (2.1 → 2.2 → 2.3 → 2.4).
- Task 3 follows Task 2 (Section 0a references the offer authored in Task 2).
- Task 4 follows all `onboarding-flow.md` edits (Tasks 2 and 3).
- Task 5 sub-tasks can run once their targets exist (5.1 after Tasks 2–3; 5.2 anytime; 5.3/5.4 after Task 1).
- Task 6 is last and gates on everything.

## Notes

- No changes to `write-policy-gate.kiro.hook`, `hook-registry*.md`, or `governance-rules.yaml` — keeping them untouched preserves `sync_hook_registry.py --verify` and governance assertions.
- The preferences write path is already on the hook's internal-file pass-through allowlist, so recording the decision produces no intercept cycle.
- Keep steering additions concise; Task 4 must re-sync `steering-index.yaml` or the CI `measure_steering.py --check` gate will fail.
- All new/edited Markdown must be valid CommonMark (`validate_commonmark.py` gate).
