# Bugfix Requirements Document

## Introduction

The `detect_missing_capture_hooks()` function in `capture_hook_safeguard.py` checks for hook files using the legacy `<id>.kiro.hook` filename pattern. Since power version 0.2.0 migrated hooks to the Kiro 1.0 v1 format (`<id>.json`), the detector always reports false positives — surfacing a misleading "capture hooks missing — session deliverables will degrade" Soft_Block at every module-completion boundary even when the hooks are present and firing correctly.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN capture-critical hooks are installed as v1 `<id>.json` files in `.kiro/hooks/` THEN the system reports them as missing because it only checks for `<id>.kiro.hook` files

1.2 WHEN a module-completion boundary is reached and capture-critical hooks exist only in v1 `.json` format THEN the system emits a false-positive Soft_Block warning "capture hooks missing — session deliverables will degrade"

1.3 WHEN the `.kiro/hooks/` directory contains both v1 `<id>.json` and no legacy `<id>.kiro.hook` for the same hook id THEN the system treats that hook as absent

### Expected Behavior (Correct)

2.1 WHEN capture-critical hooks are installed as v1 `<id>.json` files in `.kiro/hooks/` THEN the system SHALL recognize them as present

2.2 WHEN a module-completion boundary is reached and capture-critical hooks exist in v1 `.json` format THEN the system SHALL produce a silent no-op (no Soft_Block)

2.3 WHEN capture-critical hooks are installed in either legacy `<id>.kiro.hook` format OR v1 `<id>.json` format THEN the system SHALL recognize them as present (backward-compatible detection)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN capture-critical hooks are installed in legacy `<id>.kiro.hook` format THEN the system SHALL CONTINUE TO recognize them as present

3.2 WHEN a capture-critical hook has no file in either format (`<id>.kiro.hook` or `<id>.json`) THEN the system SHALL CONTINUE TO report it as missing and emit the Soft_Block warning

3.3 WHEN the `.kiro/hooks/` directory is missing or unreadable THEN the system SHALL CONTINUE TO treat all capture-critical hooks as absent

3.4 WHEN unrelated hook files exist in `.kiro/hooks/` THEN the system SHALL CONTINUE TO ignore them (they never affect detection of capture-critical hooks)

3.5 WHEN all capture-critical hooks are present (in either format) THEN the system SHALL CONTINUE TO produce a silent no-op plan with `is_noop=True` and `is_soft_block=False`

---

### Bug Condition (Formal)

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type HooksDirState
  OUTPUT: boolean

  // Returns true when a capture-critical hook exists ONLY as <id>.json
  // (not as <id>.kiro.hook) — the condition the old detector misses.
  RETURN EXISTS hook_id IN CAPTURE_CRITICAL WHERE
    (hooks_dir / f"{hook_id}.json").is_file() AND
    NOT (hooks_dir / f"{hook_id}.kiro.hook").is_file()
END FUNCTION
```

### Fix Property (Fix Checking)

```pascal
// Property: Fix Checking — v1 JSON hooks are recognized as present
FOR ALL X WHERE isBugCondition(X) DO
  result ← detect_missing_capture_hooks'(X.hooks_dir)
  ASSERT hook_id NOT IN result
    FOR EACH hook_id WHERE (X.hooks_dir / f"{hook_id}.json").is_file()
END FOR
```

### Preservation Property (Preservation Checking)

```pascal
// Property: Preservation Checking — non-buggy inputs behave identically
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT detect_missing_capture_hooks(X.hooks_dir) = detect_missing_capture_hooks'(X.hooks_dir)
END FOR
```

This ensures that for all inputs where the bug condition does not apply (hooks exist as `.kiro.hook`, or truly do not exist in either format), the fixed function behaves identically to the original.
