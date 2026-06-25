# Bugfix Design Document

## Overview

The fix is a one-line deletion in a single steering file. Section "5. Track Selection" of
`senzing-bootcamp/steering/onboarding-phase2-track-setup.md` currently contains a standalone
sentence describing Module 2 auto-insertion mechanics between the track options and the response
interpretation guidance:

```markdown
- **Advanced Topics** *(not recommended for bootcamp)* — Modules 1–11. ...

Module 2 is automatically inserted before any module that needs the SDK.

Interpreting responses: "core"/"core_bootcamp"→start at Module 1, ...
```

The fix removes that sentence (and its surrounding blank line) so track selection presents only
what the bootcamper needs to make the choice. The auto-insertion behavior is unchanged, and the
explanation that already lives in `onboarding-flow.md` (delivered when Module 2 is actually
reached) is retained as the single, well-timed place that information appears.

## Glossary

- **Track_Setup_File**: `senzing-bootcamp/steering/onboarding-phase2-track-setup.md`.
- **Auto_Insertion_Note**: The standalone line "Module 2 is automatically inserted before any module that needs the SDK." in Section 5 of the Track_Setup_File.
- **F**: The original Track_Setup_File content (with the Auto_Insertion_Note).
- **F'**: The fixed content (Auto_Insertion_Note removed; everything else preserved).

## Bug Details

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  RETURN X.file_path = "senzing-bootcamp/steering/onboarding-phase2-track-setup.md"
         AND containsLine(X.body, "Module 2 is automatically inserted before any module that needs the SDK.")
END FUNCTION
```

### Examples

- **Track setup with note (BUG)**: the file's Section 5 contains the Auto_Insertion_Note.
  *Expected:* the note is removed in F'. **Must not contain it after the fix.**
- **`onboarding-flow.md` SDK-check explanation (NOT a bug)**: the auto-insertion explanation at
  the point Module 2 is reached. **Preserved.**
- **`module-dependencies.yaml` sequencing (NOT a bug)**: the data that drives auto-insertion.
  **Preserved.**

## Hypothesized Root Cause

The auto-insertion mechanics were surfaced too early — at track selection — when they are only
relevant once an SDK-dependent module begins. The single sentence is informational only; removing
it has no behavioral effect because module sequencing is driven by `config/module-dependencies.yaml`
and the SDK-check explanation in `onboarding-flow.md`, neither of which depends on this prose.

## Expected Behavior

### Preservation Requirements

All inputs where `isBugCondition(X)` is false must be completely unaffected by this fix:

- The track options (Core Bootcamp, Advanced Topics), the "Authoritative source" note, the
  response-interpretation guidance, and the ⛔ mandatory stop gate in the Track_Setup_File remain
  present and unchanged.
- The `onboarding-flow.md` auto-insertion explanation (delivered when Module 2 is reached) is
  retained.
- `config/module-dependencies.yaml` (which drives the actual auto-insertion behavior) is untouched.
- All other steering files, hooks, scripts, and configs are untouched.

The only changed behavior: the standalone Auto_Insertion_Note line is removed from the
track-selection step. The correct behavior for the buggy input is defined in Property 1 below.

## Correctness Properties

### Property 1: Bug Condition — Note removed from track selection

_For any_ Track_Setup_File content where the Auto_Insertion_Note is present (`isBugCondition(X)`
true), the fixed content SHALL NOT contain the Auto_Insertion_Note line.

**Validates: Requirements 2.1**

### Property 2: Preservation — Everything else unchanged

_For any_ content where the bug condition does not hold, the fix SHALL produce identical content
(`F'(X) = F(X)`). Within the Track_Setup_File, the track options, the "Authoritative source"
note, the response-interpretation guidance, and the ⛔ mandatory stop gate SHALL remain present and
unchanged; the `onboarding-flow.md` auto-insertion explanation and `module-dependencies.yaml`
SHALL remain untouched.

**Validates: Requirements 2.2, 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Change Required

Edit `senzing-bootcamp/steering/onboarding-phase2-track-setup.md` Section "5. Track Selection":

- Remove the line `Module 2 is automatically inserted before any module that needs the SDK.` and
  the now-redundant adjacent blank line so the track options flow directly into the "Interpreting
  responses:" guidance.

No other surface changes. CommonMark validity and the file's `steering-index.yaml` token budget
are re-verified (the change only reduces token count).

## Testing Strategy

### Validation Approach

A single new test module `senzing-bootcamp/tests/test_track_selection_drop_module2_note.py`
(stdlib + pytest, per `python-conventions.md`), authored against the unfixed file so the
fix-checking test FAILS before the edit and PASSES after.

### Fix Checking

- **test_track_selection_omits_auto_insertion_note** (Property 1): read the Track_Setup_File and
  assert it does NOT contain the string "Module 2 is automatically inserted before any module that
  needs the SDK." Authored to FAIL on unfixed content, PASS after the fix.

### Preservation Checking

- **test_track_options_present** (Property 2): assert "Core Bootcamp" and "Advanced Topics" track
  options remain in the file.
- **test_mandatory_stop_gate_present** (Property 2): assert the ⛔ mandatory stop gate text remains.
- **test_response_interpretation_present** (Property 2): assert the "Interpreting responses:" line
  remains.
- **test_onboarding_flow_explanation_retained** (Property 2): read `onboarding-flow.md` and assert
  the "explicitly or auto-inserted" explanation is still present.

All preservation tests are authored to PASS on unfixed content (baseline) and continue to PASS
after the fix.

### Integration Tests

- Run `python senzing-bootcamp/scripts/validate_commonmark.py` — confirms the edited file remains
  valid CommonMark.
- Run `python senzing-bootcamp/scripts/measure_steering.py --check` — confirms the token budget
  still passes (token count only decreases).
