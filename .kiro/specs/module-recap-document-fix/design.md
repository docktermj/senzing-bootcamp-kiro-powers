# Design Document

## Overview

This design addresses a bug where the `module-recap-append` and `module-completion-celebration` hooks use `postTaskExecution` as their event type, which never fires during normal conversational bootcamp flow. The fix changes both hooks to use `agentStop` while preserving all existing prompt logic, boundary detection, and schema integrity.

## Architecture

The fix is a minimal, surgical change to two JSON hook files. No new components are introduced. The existing architecture remains unchanged:

```
senzing-bootcamp/hooks/
├── module-recap-append.kiro.hook        ← change when.type
├── module-completion-celebration.kiro.hook  ← change when.type
└── hook-categories.yaml                 (unchanged)
```

The `agentStop` event fires each time the agent finishes responding in a conversation turn. Both hooks already contain boundary detection logic that silently exits when no module completion has occurred, making `agentStop` a safe replacement — the hooks only produce output when `modules_completed` in `config/bootcamp_progress.json` has grown.

## Components and Interfaces

### Component 1: Hook File Modification

**Files:**
- `senzing-bootcamp/hooks/module-recap-append.kiro.hook`
- `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`

**Change:** In each file, replace `"type": "postTaskExecution"` with `"type": "agentStop"` inside the `when` object.

**Constraints:**
- No other fields are modified
- The `then.prompt` content remains byte-for-byte identical
- The `version` field remains `"1.0.0"` (this is a bug fix to the trigger, not a feature change to the hook's behavior)

### Component 2: Integration Test Suite

**File:** `tests/test_module_recap_document_fix.py`

**Purpose:** Validate the corrected trigger condition and ensure no regression in prompt content.

**Approach:**
- Load both hook files and assert structural correctness
- Use Hypothesis to generate arbitrary progress states and verify boundary detection logic
- Assert that using `postTaskExecution` would be caught by the test suite

### Hook JSON Schema (unchanged)

```json
{
  "name": "<string>",
  "version": "<semver>",
  "description": "<string>",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<string>"
  }
}
```

### Boundary Detection Contract

Both hook prompts implement the same boundary detection pattern:

1. Read `config/bootcamp_progress.json`
2. Check if `modules_completed` array has grown
3. If unchanged → produce no output (silent exit)
4. If new module detected → execute hook-specific behavior

## Data Models

### Progress File Structure (`config/bootcamp_progress.json`)

```json
{
  "modules_completed": [1, 2, 3],
  "current_module": 4
}
```

### Boundary Detection Model

```python
def has_new_completion(before: list[int], after: list[int]) -> bool:
    """Return True if after contains at least one module not in before."""
    return bool(set(after) - set(before))
```

This pure function is the core logic that the property-based tests validate.

## Error Handling

- **Invalid JSON:** If a hook file is malformed, `json.load()` raises `JSONDecodeError`. The test suite catches this and reports a clear failure.
- **Missing fields:** The `validate_required_fields()` helper from `hook_test_helpers.py` reports exactly which fields are absent.
- **Wrong event type:** Tests assert `when.type == "agentStop"` with a descriptive message naming the expected vs actual value.

## Testing Strategy

### Unit Tests (Example-Based)

- Celebration hook references `config/bootcamp_preferences.yaml`
- Recap hook prompt contains session content gathering instructions
- Celebration hook prompt contains congratulatory banner instructions
- `"agentStop"` is in `VALID_EVENT_TYPES`

### Property-Based Tests (Hypothesis)

All property tests use `@settings(max_examples=100)` minimum.

| Property | What varies | What's verified |
|----------|-------------|-----------------|
| Event type correctness | Hook selection from affected set | `when.type == "agentStop"` |
| Schema integrity | Subset of required fields | Missing fields reported exactly |
| Boundary detection correctness | Random progress states (before/after) | Detection iff new module present |
| Wrong event type rejection | Random non-agentStop event types | Validation rejects them |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Event type is agentStop for all affected hooks

*For any* hook in the set {module-recap-append, module-completion-celebration}, the `when.type` field SHALL equal `"agentStop"`.

**Validates: Requirements 1.1, 1.2**

### Property 2: Schema integrity preserved after modification

*For any* hook in the set {module-recap-append, module-completion-celebration}, all required fields (`name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`) SHALL be present and the `then.type` value SHALL equal `"askAgent"`.

**Validates: Requirements 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.5, 3.6**

### Property 3: Version field is valid semver

*For any* hook in the set {module-recap-append, module-completion-celebration}, the `version` field SHALL match semantic versioning format (MAJOR.MINOR.PATCH with no leading zeros).

**Validates: Requirements 3.3, 3.4**

### Property 4: Boundary detection prompt integrity

*For any* hook in the set {module-recap-append, module-completion-celebration}, the `then.prompt` SHALL contain a reference to `config/bootcamp_progress.json`, a reference to `modules_completed`, and a silent-exit instruction for the no-change case.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 5: Prompt references module-dependencies.yaml

*For any* hook in the set {module-recap-append, module-completion-celebration}, the `then.prompt` SHALL contain a reference to `config/module-dependencies.yaml`.

**Validates: Requirements 4.1, 4.2**

### Property 6: Execution constraints present in prompts

*For any* hook in the set {module-recap-append, module-completion-celebration}, the `then.prompt` SHALL contain constraint language preventing script execution and file-system scans.

**Validates: Requirements 4.7, 4.8**

### Property 7: Boundary detection correctness for arbitrary progress states

*For any* pair of valid progress states (before: `list[int]`, after: `list[int]`) representing `modules_completed` arrays, boundary detection SHALL return `True` if and only if `after` contains at least one module number not present in `before`.

**Validates: Requirements 5.4**

### Property 8: Wrong event type causes test failure

*For any* event type string that is not `"agentStop"`, validating it against the expected event type for these hooks SHALL produce a failure with a clear assertion message.

**Validates: Requirements 5.6**
