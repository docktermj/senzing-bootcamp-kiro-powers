# Capture-Hook Safeguard Stale Check Bugfix Design

## Overview

The `detect_missing_capture_hooks()` function in `capture_hook_safeguard.py` only checks for legacy `<id>.kiro.hook` files when determining whether capture-critical hooks are installed. Since power version 0.2.0 migrated hooks to the Kiro 1.0 v1 format (`<id>.json`), the detector always reports false positives — emitting a misleading Soft_Block warning at every module-completion boundary even when the hooks are present and firing correctly. The fix updates the detection logic to recognize either format (`<id>.json` OR `<id>.kiro.hook`), and updates the docstring to document both filename patterns.

## Glossary

- **Bug_Condition (C)**: The state where a capture-critical hook exists only as `<id>.json` (not as `<id>.kiro.hook`) in `.kiro/hooks/` — the condition the current detector misses
- **Property (P)**: When the bug condition holds, `detect_missing_capture_hooks()` shall NOT include that hook id in its "missing" result
- **Preservation**: All inputs where the bug condition does NOT hold (hooks exist only as `.kiro.hook`, exist in both formats, or truly do not exist in either format) must produce identical results before and after the fix
- **`detect_missing_capture_hooks()`**: The function in `senzing-bootcamp/scripts/capture_hook_safeguard.py` (line ~130) that returns the sorted list of capture-critical ids whose hook file is absent
- **CAPTURE_CRITICAL**: The set `{"session-log-events", "ask-bootcamper"}` defined in `install_hooks.py` — the single source of truth for which hook ids are capture-critical
- **v1 format**: The current hook file format using `<id>.json` filenames in `.kiro/hooks/`
- **Legacy format**: The old hook file format using `<id>.kiro.hook` filenames in `.kiro/hooks/`

## Bug Details

### Bug Condition

The bug manifests when capture-critical hooks are installed in v1 `.json` format but not in legacy `.kiro.hook` format. The `detect_missing_capture_hooks()` function only checks for `<id>.kiro.hook` files in its list comprehension condition, so it never recognizes v1 hooks as present.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type HooksDirState (a .kiro/hooks/ directory)
  OUTPUT: boolean

  RETURN EXISTS hook_id IN CAPTURE_CRITICAL WHERE
    (input.hooks_dir / f"{hook_id}.json").is_file()
    AND NOT (input.hooks_dir / f"{hook_id}.kiro.hook").is_file()
END FUNCTION
```

### Examples

- **Example 1**: `.kiro/hooks/` contains `ask-bootcamper.json` but no `ask-bootcamper.kiro.hook` → current code reports `ask-bootcamper` as missing (incorrect), fixed code should report it as present
- **Example 2**: `.kiro/hooks/` contains `session-log-events.json` but no `session-log-events.kiro.hook` → current code reports `session-log-events` as missing (incorrect), fixed code should report it as present
- **Example 3**: `.kiro/hooks/` contains both `ask-bootcamper.json` AND `ask-bootcamper.kiro.hook` → current code reports it as present (correct), fixed code same behavior
- **Edge case**: `.kiro/hooks/` contains neither `ask-bootcamper.json` nor `ask-bootcamper.kiro.hook` → both current and fixed code report it as missing (correct)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Hooks present only as `<id>.kiro.hook` must continue to be recognized as present
- Hooks absent in both formats must continue to be reported as missing
- A missing or unreadable `.kiro/hooks/` directory must continue to treat all hooks as absent
- Unrelated files in `.kiro/hooks/` must continue to be ignored
- When all capture-critical hooks are present (in either format), the system must continue to produce a silent no-op plan with `is_noop=True` and `is_soft_block=False`
- The return value must remain a sorted list of missing hook id strings

**Scope:**
All inputs where the bug condition does NOT hold should be completely unaffected by this fix. This includes:
- Directories containing only legacy `.kiro.hook` files
- Directories containing both `.json` and `.kiro.hook` for the same id
- Directories where a hook truly does not exist in either format
- Missing or unreadable directories (OSError path)

## Hypothesized Root Cause

Based on the source code, the root cause is definitively identified:

1. **Hardcoded legacy filename pattern**: The list comprehension in `detect_missing_capture_hooks()` (line ~133) uses only `f"{hook_id}.kiro.hook"` in its `is_file()` check:
   ```python
   if not (hooks_dir / f"{hook_id}.kiro.hook").is_file()
   ```
   This was correct before v0.2.0 but became stale after hooks migrated to `<id>.json` format.

2. **Docstring references only the legacy pattern**: The docstring describes detection as keying on `<id>.kiro.hook` filenames, which no longer reflects the intended behavior.

No other root causes apply — the bug is a single stale filename pattern in one condition.

## Correctness Properties

Property 1: Bug Condition - v1 JSON hooks recognized as present

_For any_ hooks directory state where a capture-critical hook exists as `<id>.json` (with or without a corresponding `<id>.kiro.hook`), the fixed `detect_missing_capture_hooks()` function SHALL NOT include that hook id in its returned "missing" list.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-v1-only inputs behave identically

_For any_ hooks directory state where the bug condition does NOT hold (every capture-critical hook either exists as `<id>.kiro.hook` or does not exist in either format), the fixed `detect_missing_capture_hooks()` function SHALL produce the same sorted list as the original function, preserving legacy detection and true-absence reporting.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/scripts/capture_hook_safeguard.py`

**Function**: `detect_missing_capture_hooks()`

**Specific Changes**:

1. **Update list comprehension condition** (line ~133): Change from checking only `.kiro.hook` to checking either format:
   ```python
   # Before:
   if not (hooks_dir / f"{hook_id}.kiro.hook").is_file()

   # After:
   if not (hooks_dir / f"{hook_id}.json").is_file()
       and not (hooks_dir / f"{hook_id}.kiro.hook").is_file()
   ```
   A hook is considered missing only when NEITHER `<id>.json` NOR `<id>.kiro.hook` exists.

2. **Update docstring**: Replace references to only `<id>.kiro.hook` with documentation that both `<id>.json` (v1 format) and `<id>.kiro.hook` (legacy format) are checked. Update the Args/Returns descriptions accordingly.

3. **No other changes needed**: The function signature, return type, sorting behavior, and OSError handling remain identical. Downstream consumers (`build_reminder`, `should_reprompt`, `record_acknowledgment`, `main`) require no modification since they receive the same `list[str]` return type.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the root cause is the stale `.kiro.hook`-only check.

**Test Plan**: Create temporary directories containing only `<id>.json` files for capture-critical hooks and call `detect_missing_capture_hooks()` on the unfixed code. Observe that it incorrectly reports them as missing.

**Test Cases**:
1. **Single v1 hook test**: Create `ask-bootcamper.json` only → unfixed code reports it missing (will fail on unfixed code)
2. **All v1 hooks test**: Create both `session-log-events.json` and `ask-bootcamper.json` → unfixed code reports both missing (will fail on unfixed code)
3. **Mixed format test**: Create `ask-bootcamper.json` (no `.kiro.hook`) and `session-log-events.kiro.hook` (no `.json`) → unfixed code reports `ask-bootcamper` missing (will fail on unfixed code)

**Expected Counterexamples**:
- `detect_missing_capture_hooks()` returns hook ids that are actually present as `.json` files
- Root cause confirmed: the condition only checks `.kiro.hook` existence

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL hooks_dir WHERE isBugCondition(hooks_dir) DO
  result := detect_missing_capture_hooks_fixed(hooks_dir)
  FOR EACH hook_id WHERE (hooks_dir / f"{hook_id}.json").is_file() DO
    ASSERT hook_id NOT IN result
  END FOR
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL hooks_dir WHERE NOT isBugCondition(hooks_dir) DO
  ASSERT detect_missing_capture_hooks_original(hooks_dir) = detect_missing_capture_hooks_fixed(hooks_dir)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many hook directory configurations automatically
- It catches edge cases like empty directories, mixed formats, partial presence
- It provides strong guarantees that legacy detection behavior is unchanged

**Test Plan**: Observe behavior on UNFIXED code first for legacy-only and absent-hook inputs, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Legacy-only preservation**: Verify that hooks present as `.kiro.hook` (no `.json`) continue to be detected as present
2. **True-absence preservation**: Verify that hooks absent in both formats continue to be reported as missing
3. **Unreadable directory preservation**: Verify that OSError handling continues to treat all hooks as absent
4. **Unrelated files preservation**: Verify that non-capture-critical files in the directory have no effect

### Unit Tests

- Test `detect_missing_capture_hooks()` with only `.json` files present (bug condition)
- Test with only `.kiro.hook` files present (legacy detection)
- Test with both formats present for same hook id
- Test with neither format present (true absence)
- Test with missing/unreadable hooks directory
- Test with one hook in `.json` and another in `.kiro.hook` (mixed per-hook formats)

### Property-Based Tests

- Generate random subsets of CAPTURE_CRITICAL with random format assignments (`.json`, `.kiro.hook`, both, neither) and verify the fixed function correctly identifies only truly-absent hooks as missing
- Generate random hooks directory states where no hook exists only as `.json` (non-bug-condition) and verify the fixed function produces the same result as the original
- Generate random non-capture-critical filenames in the hooks directory and verify they never affect the result

### Integration Tests

- Test full CLI invocation (`main()`) with v1-only hooks directory → verify no Soft_Block output
- Test full CLI invocation with mixed format hooks → verify correct plan assembly
- Test `build_reminder()` receives correct (shorter) missing list after fix
- Test end-to-end: detection → reminder → render cycle with v1 hooks present produces empty output
