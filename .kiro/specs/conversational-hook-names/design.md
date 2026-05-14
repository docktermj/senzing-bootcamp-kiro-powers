# Design: Conversational Hook Names

## 1. Overview

The Kiro UI renders hook names as "Ask Kiro Hook {name}". Current hook `name` fields use jargony implementation labels (e.g., "Ask Bootcamper", "Code Style Check") or inconsistent phrasing ("I will make sure the file is in the project directory"), producing awkward UI strings like "Ask Kiro Hook Ask Bootcamper". The fix rewrites every hook's `name` field to follow the pattern `"to {verb phrase}"` so the UI reads naturally as "Ask Kiro Hook to {do something}". Only the `name` field changes — all other hook fields (`id`, `version`, `description`, `when`, `then`) remain untouched.

## 2. Glossary

| Term | Definition |
|------|-----------|
| Bug_Condition | A formal specification of the defect: WHEN a hook fires, the UI displays a jargony or inconsistent label because the `name` field does not follow the conversational "to {verb phrase}" pattern. |
| Property | An invariant that must hold after the fix: every hook `name` starts with "to " followed by a lowercase verb phrase, producing a natural sentence when prefixed with "Ask Kiro Hook". |
| Preservation | Behavior that must remain unchanged after the fix: hook IDs, versions, descriptions, event types, prompts, file patterns, CI validation, and JSON structural validity. |

## 3. Bug Details

### Bug Condition

```
GIVEN a .kiro.hook file in senzing-bootcamp/hooks/
WHEN the Kiro framework renders the hook in the UI
THEN it displays "Ask Kiro Hook {name}"
AND the current {name} values are implementation labels or inconsistent phrases
RESULTING IN awkward, jargony UI strings that break conversational tone
```

### Examples of the Defect

| Hook ID | Current `name` | UI Renders As |
|---------|---------------|---------------|
| ask-bootcamper | `Ask Bootcamper` | "Ask Kiro Hook Ask Bootcamper" |
| review-bootcamper-input | `Review Bootcamper Input` | "Ask Kiro Hook Review Bootcamper Input" |
| enforce-file-path-policies | `I will make sure the file is in the project directory` | "Ask Kiro Hook I will make sure the file is in the project directory" |
| code-style-check | `Code Style Check` | "Ask Kiro Hook Code Style Check" |
| data-quality-check | `Senzing Data Quality Check` | "Ask Kiro Hook Senzing Data Quality Check" |

### Pattern Violations

1. **Title Case labels** — Most hooks use noun-phrase labels ("Code Style Check", "Validate Business Problem") that read as menu items, not conversational continuations.
2. **First-person future tense** — `enforce-file-path-policies` uses "I will make sure…" which is a promise, not a description of what is happening.
3. **Object-oriented phrasing** — "Ask Bootcamper" and "Review Bootcamper Input" treat the user as a data object rather than addressing them as a person.
4. **Inconsistent naming** — Some hooks append context ("Backup Database Before Loading", "Run Tests After Code Change", "Verify Generated Code Runs") while others use bare labels ("Security Scan on Save").

## 4. Expected Behavior

### After the Fix

Every hook `name` field follows the pattern `"to {lowercase verb phrase}"` such that:

```
"Ask Kiro Hook" + " " + name → natural English sentence
```

Example: `"to wait for your answer"` → "Ask Kiro Hook to wait for your answer"

### Preservation Requirements

| Aspect | Must Remain Unchanged |
|--------|----------------------|
| Hook file names | `{hook-id}.kiro.hook` — no renames |
| `id` field (in registry) | Unchanged |
| `version` field | Unchanged |
| `description` field | Unchanged |
| `when` block | Unchanged (event type, patterns, toolTypes) |
| `then` block | Unchanged (type, prompt) |
| JSON validity | All files must remain valid JSON |
| CI validation | `sync_hook_registry.py --verify` must pass |
| Hook behavior | Identical runtime behavior |

### Scope of Change

1. **24 `.kiro.hook` files** — update `name` field only
2. **`senzing-bootcamp/steering/hook-registry.md`** — update `name:` lines to match new names
3. **`senzing-bootcamp/hooks/README.md`** — add style guide line for the `name` field
4. **`senzing-bootcamp/steering/onboarding-flow.md`** — update any inline hook name references to match new names (references are via `#[[file:...]]` include of hook-registry.md, so changes propagate automatically)

## 5. Hypothesized Root Cause

The hook names were written from a developer's perspective during initial implementation. The naming convention prioritized internal identification (what the hook *does* technically) over user experience (how the name *reads* in the UI). No style guide existed to enforce a consistent pattern, so each hook author chose their own convention — Title Case labels, first-person promises, or bare noun phrases. The Kiro UI's "Ask Kiro Hook {name}" rendering pattern was not considered when naming hooks.

## 6. Correctness Properties

### P1: Conversational Pattern Compliance

Every hook `name` field MUST start with the literal string `"to "` followed by one or more lowercase words forming a verb phrase.

```
∀ hook ∈ hooks: hook.name matches /^to [a-z]/
```

### P2: Natural Sentence Formation

When prefixed with "Ask Kiro Hook ", every hook name MUST form a grammatically natural English sentence fragment.

```
∀ hook ∈ hooks: "Ask Kiro Hook " + hook.name reads as natural English
```

### P3: Structural Preservation

For every hook file, the fix MUST change ONLY the `name` field. All other JSON keys (`version`, `description`, `when`, `then`) MUST have identical values before and after the fix.

```
∀ hook ∈ hooks: hook_after.version == hook_before.version
                ∧ hook_after.description == hook_before.description
                ∧ hook_after.when == hook_before.when
                ∧ hook_after.then == hook_before.then
```

### P4: JSON Validity

Every `.kiro.hook` file MUST remain valid JSON after the fix.

```
∀ file ∈ *.kiro.hook: json.loads(file.read()) succeeds
```

### P5: Registry Consistency

The `name` value in each hook file MUST match the corresponding `name:` line in `hook-registry.md`.

```
∀ hook ∈ hooks: hook_file.name == registry_entry.name
```

### P6: No ID Mutation

No hook file may be renamed, and no `id` field in the registry may change.

```
∀ hook ∈ hooks: hook_after.filename == hook_before.filename
                ∧ registry_after.id == registry_before.id
```

### P7: CI Validation Passes

After all changes, `sync_hook_registry.py --verify` MUST exit with code 0.

```
exit_code(sync_hook_registry.py --verify) == 0
```

## 7. Fix Implementation

### 7.1 Hook Name Changes (24 files)

| # | Hook ID | Current `name` | New `name` |
|---|---------|---------------|------------|
| 1 | ask-bootcamper | `Ask Bootcamper` | `to wait for your answer` |
| 2 | review-bootcamper-input | `Review Bootcamper Input` | `to review what you said` |
| 3 | code-style-check | `Code Style Check` | `to check code style` |
| 4 | commonmark-validation | `CommonMark Validation` | `to check Markdown style` |
| 5 | enforce-file-path-policies | `I will make sure the file is in the project directory` | `to make sure the file is in the project directory` |
| 6 | validate-business-problem | `Validate Business Problem` | `to validate your business problem` |
| 7 | verify-sdk-setup | `Verify SDK Setup` | `to verify SDK setup` |
| 8 | verify-demo-results | `Verify Demo Results` | `to verify demo results` |
| 9 | validate-data-files | `Validate Data Files` | `to validate data files` |
| 10 | data-quality-check | `Senzing Data Quality Check` | `to check data quality` |
| 11 | analyze-after-mapping | `Analyze After Mapping` | `to analyze mapped data` |
| 12 | enforce-mapping-spec | `Enforce Mapping Specification` | `to enforce the mapping specification` |
| 13 | backup-before-load | `Backup Database Before Loading` | `to remind you to back up before loading` |
| 14 | run-tests-after-change | `Run Tests After Code Change` | `to remind you to run tests` |
| 15 | verify-generated-code | `Verify Generated Code Runs` | `to verify generated code` |
| 16 | enforce-visualization-offers | `Enforce Visualization Offers` | `to offer visualizations` |
| 17 | validate-benchmark-results | `Validate Benchmark Results` | `to validate benchmark results` |
| 18 | security-scan-on-save | `Security Scan on Save` | `to run a security scan` |
| 19 | validate-alert-config | `Validate Alert Configuration` | `to validate alert configuration` |
| 20 | deployment-phase-gate | `Deployment Phase Gate` | `to check the deployment phase gate` |
| 21 | backup-project-on-request | `Backup Project on Request` | `to back up your project` |
| 22 | error-recovery-context | `Auto-Load Error Recovery Context` | `to help recover from errors` |
| 23 | git-commit-reminder | `Git Commit Reminder` | `to remind you to commit` |
| 24 | module-completion-celebration | `Module Completion Celebration` | `to celebrate module completion` |

### 7.2 Registry Update (`senzing-bootcamp/steering/hook-registry.md`)

Update every `- name:` line in the Hook Registry to match the new names from the table above. The `id`, `description`, and `Prompt` sections remain unchanged.

### 7.3 README Style Guide (`senzing-bootcamp/hooks/README.md`)

Add the following style guide section after the introductory paragraph:

```markdown
## Hook Name Style Guide

The `name` field is user-facing — the Kiro UI renders it as "Ask Kiro Hook {name}". Every hook's `name` MUST follow the pattern `"to {verb phrase}"` (lowercase, no trailing period) so the full UI string reads as a natural sentence. Examples:

- ✅ `"to check code style"` → "Ask Kiro Hook to check code style"
- ✅ `"to remind you to run tests"` → "Ask Kiro Hook to remind you to run tests"
- ❌ `"Code Style Check"` → "Ask Kiro Hook Code Style Check" (jargony)
- ❌ `"I will check code style"` → "Ask Kiro Hook I will check code style" (first-person)
```

### 7.4 Onboarding Flow References

The `onboarding-flow.md` file includes the Hook Registry via `#[[file:senzing-bootcamp/steering/hook-registry.md]]`. Since the registry itself is updated (§7.2), the onboarding flow's Critical Hooks section will automatically reflect the new names. No additional changes to `onboarding-flow.md` are required unless it contains inline hook name references outside the include directive.

Verify: the failure impact messages table in Step 1 of `onboarding-flow.md` references hooks by `id` (e.g., `ask-bootcamper`, `code-style-check`), not by `name`. These references are unaffected by the name change.

## 8. Testing Strategy

### 8.1 Exploratory Testing (Bug Reproduction)

Verify the bug exists before fixing:

- Read each `.kiro.hook` file and confirm the `name` field does NOT match the `^to [a-z]` pattern
- Construct the UI string "Ask Kiro Hook {name}" for each hook and confirm it reads awkwardly

### 8.2 Fix Checking (Bug Elimination)

After applying the fix:

- Read each `.kiro.hook` file and confirm the `name` field matches `^to [a-z]`
- Construct "Ask Kiro Hook {name}" for each hook and confirm natural readability
- Verify all 24 hooks have been updated (no hooks missed)

### 8.3 Preservation Checking (Regression Prevention)

After applying the fix:

- Parse each `.kiro.hook` file as JSON — must succeed (P4)
- Compare `version`, `description`, `when`, `then` fields before/after — must be identical (P3)
- Verify no hook files were renamed or deleted (P6)
- Run `sync_hook_registry.py --verify` — must exit 0 (P7)
- Verify registry `name:` lines match hook file `name` fields (P5)

### 8.4 Unit Tests

| Test | Validates |
|------|-----------|
| `test_all_hook_names_start_with_to` | P1 — every name starts with "to " |
| `test_hook_names_are_lowercase_after_to` | P1 — no Title Case after "to " |
| `test_hook_files_are_valid_json` | P4 — JSON parse succeeds |
| `test_hook_fields_unchanged_except_name` | P3 — structural preservation |
| `test_registry_names_match_hook_files` | P5 — registry consistency |
| `test_no_hook_files_renamed` | P6 — file identity preserved |
| `test_ci_validation_passes` | P7 — sync_hook_registry.py --verify |

### 8.5 Property-Based Tests (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(hook_file=st.sampled_from(ALL_HOOK_FILES))
def test_name_pattern_property(hook_file):
    """P1: Every hook name matches the conversational pattern."""
    data = json.loads(hook_file.read_text())
    name = data["name"]
    assert name.startswith("to "), f"{hook_file.name}: name must start with 'to '"
    rest = name[3:]
    assert rest[0].islower(), f"{hook_file.name}: verb must be lowercase"
    assert not rest.endswith("."), f"{hook_file.name}: no trailing period"

@given(hook_file=st.sampled_from(ALL_HOOK_FILES))
def test_structural_preservation_property(hook_file):
    """P3: Only the name field differs from the baseline."""
    current = json.loads(hook_file.read_text())
    baseline = BASELINE_DATA[hook_file.name]
    for key in ("version", "description", "when", "then"):
        assert current[key] == baseline[key], f"{hook_file.name}: {key} was mutated"

@given(hook_file=st.sampled_from(ALL_HOOK_FILES))
def test_json_validity_property(hook_file):
    """P4: Every hook file is valid JSON."""
    json.loads(hook_file.read_text())  # raises on invalid JSON

@given(hook_file=st.sampled_from(ALL_HOOK_FILES))
def test_ui_string_is_natural_sentence(hook_file):
    """P2: The UI string forms a grammatical sentence fragment."""
    data = json.loads(hook_file.read_text())
    ui_string = f"Ask Kiro Hook {data['name']}"
    # Must read as "Ask Kiro Hook to {verb}..."
    assert "Ask Kiro Hook to " in ui_string
```

### 8.6 CI Integration

The existing CI pipeline (`validate-power.yml`) runs `sync_hook_registry.py --verify` which validates that hook files and the registry are in sync. After the fix, this check must continue to pass. No new CI steps are required — the existing validation covers P5 and P7.
