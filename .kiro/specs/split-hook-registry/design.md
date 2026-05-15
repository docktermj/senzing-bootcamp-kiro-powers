# Design: Split hook-registry.md Below Token Threshold

## Overview

Split the monolithic `hook-registry.md` (8,307 tokens) into two files to comply with the 5,000-token split threshold in `steering-index.yaml`. The summary file provides quick reference for hook creation; the detail file preserves full prompts for when the agent needs exact prompt text.

## Architecture

### Current State

```text
steering/hook-registry.md (8,307 tokens, manual inclusion)
├── Frontmatter + intro
├── Critical Hooks (5 hooks with full prompts)
└── Module Hooks (19 hooks with full prompts)
```

### Target State

```text
steering/hook-registry.md (summary, ~2,000 tokens, manual inclusion)
├── Frontmatter + intro
├── Critical Hooks table (ID, event type, one-line description)
├── Module Hooks table (ID, module, event type, one-line description)
└── Cross-reference to hook-registry-detail.md

steering/hook-registry-detail.md (detail, ~6,500 tokens, manual inclusion)
├── Frontmatter + intro
├── Critical Hooks (full prompts + createHook parameters)
└── Module Hooks (full prompts + createHook parameters)
```

### Split Strategy

The summary file contains everything the agent needs to **decide which hooks to create** — hook IDs, event types, descriptions, and categories. This is what gets loaded via keyword routing (`hook`/`hooks`).

The detail file contains the **full prompt text** needed to actually call `createHook`. It's loaded only when the agent is actively creating hooks (during onboarding or module start).

## Summary File Format

```markdown
---
inclusion: manual
---

# Hook Registry

24 bootcamp hooks organized by category. Load `hook-registry-detail.md` for full prompt text when creating hooks.

## Critical Hooks (created during onboarding)

| Hook ID | Event Type | Description |
|---------|-----------|-------------|
| ask-bootcamper | agentStop → askAgent | Silence-first hook: recap + closing question when no question pending; feedback reminder at track completion |
| code-style-check | fileEdited → askAgent | Checks source code for language-appropriate coding standards |
| commonmark-validation | fileEdited → askAgent | Validates Markdown files for CommonMark compliance |
| enforce-file-path-policies | preToolUse → askAgent | Enforces feedback path and working directory policies on write operations |
| review-bootcamper-input | promptSubmit → askAgent | Detects feedback/status trigger phrases and initiates workflows |

## Module Hooks (created when module starts)

| Hook ID | Module | Event Type | Description |
|---------|--------|-----------|-------------|
| validate-business-problem | 1 | postTaskExecution → askAgent | Validates business problem definition completeness |
| verify-sdk-setup | 2 | fileEdited → askAgent | Re-verifies SDK setup after config changes |
| gate-module3-visualization | 3 | preToolUse → askAgent | Gates Module 3 completion on visualization step |
| verify-demo-results | 3 | postTaskExecution → askAgent | Verifies system verification results match TruthSet |
| validate-data-files | 4 | fileCreated → askAgent | Validates new data files for format and readability |
| analyze-after-mapping | 5 | fileCreated → askAgent | Validates transformed data quality via analyze_record |
| data-quality-check | 5 | fileEdited → askAgent | Suggests quality validation after transform program changes |
| enforce-mapping-spec | 5 | fileCreated → askAgent | Enforces per-source mapping specification creation |
| backup-before-load | 6 | fileEdited → askAgent | Reminds to backup before running loading programs |
| run-tests-after-change | 6 | fileEdited → askAgent | Reminds to run tests after source code changes |
| verify-generated-code | 6 | fileCreated → askAgent | Verifies generated code runs on sample data |
| enforce-visualization-offers | 3,5,7,8 | agentStop → askAgent | Ensures visualization offers are made in capable modules |
| validate-benchmark-results | 8 | fileEdited → askAgent | Validates benchmark scripts produce parseable metrics |
| security-scan-on-save | 9 | fileEdited → askAgent | Reminds to run vulnerability scanning after security file changes |
| validate-alert-config | 10 | fileCreated → askAgent | Validates monitoring alert rule syntax and completeness |
| deployment-phase-gate | 11 | postTaskExecution → askAgent | Phase gate between packaging and deployment |
| backup-project-on-request | any | userTriggered → askAgent | Manual project backup trigger |
| error-recovery-context | any | postToolUse → askAgent | Provides error context and recovery guidance on shell failures |
| module-completion-celebration | any | postTaskExecution → askAgent | Celebrates module completion with summary |

## Hook Creation

To create hooks, load `hook-registry-detail.md` for the full prompt text and `createHook` parameters.
```

## Detail File Format

The detail file retains the current `hook-registry.md` structure (full prompts in fenced code blocks, id/name/description metadata) but with a different frontmatter intro:

```markdown
---
inclusion: manual
---

# Hook Registry — Full Prompts

Complete hook definitions with prompt text for use with the `createHook` tool. Load this file when actively creating hooks during onboarding or module start.

For a quick reference of all hooks, see `hook-registry.md`.

## Critical Hooks (created during onboarding)

[... full prompt entries as they exist today ...]

## Module Hooks (created when module starts)

[... full prompt entries as they exist today ...]
```

## Changes Required

### 1. Generate Summary File (`hook-registry.md`)

Replace the current `hook-registry.md` with the summary-only format. The `sync_hook_registry.py` script will be updated to generate this file.

### 2. Generate Detail File (`hook-registry-detail.md`)

Create the new detail file containing all full prompts. The `sync_hook_registry.py` script will generate this alongside the summary.

### 3. Update `sync_hook_registry.py`

Modify the script to generate two files:
- Add a `generate_registry_summary()` function that produces the table-based summary
- Rename the existing `generate_registry()` to `generate_registry_detail()` (or keep it and add the summary generator)
- Update `main()` to write both files
- Update `--verify` mode to check both files
- Add `--output-detail` argument for the detail file path (default: `senzing-bootcamp/steering/hook-registry-detail.md`)

### 4. Update `steering-index.yaml`

```yaml
# In file_metadata:
hook-registry.md:
  token_count: <measured>
  size_category: medium
hook-registry-detail.md:
  token_count: <measured>
  size_category: large

# Keywords remain pointing to summary:
hook: hook-registry.md
hooks: hook-registry.md
```

### 5. Update `#[[file:]]` Reference in `onboarding-flow.md`

The current reference at line 475:
```markdown
#[[file:senzing-bootcamp/steering/hook-registry.md]]
```

Change to reference the detail file (since onboarding needs full prompts for `createHook`):
```markdown
#[[file:senzing-bootcamp/steering/hook-registry-detail.md]]
```

### 6. Update Tests

Tests that read `hook-registry.md` and check for prompt content need to be updated to read `hook-registry-detail.md` instead. Tests that check for hook IDs can use either file.

Affected test files:
- `senzing-bootcamp/tests/test_silent_hook_architecture.py` — reads registry for prompt content
- `senzing-bootcamp/tests/test_silent_hook_processing.py` — reads registry for prompt content
- `senzing-bootcamp/tests/test_conversational_hook_names.py` — reads registry for name matching
- `senzing-bootcamp/tests/test_track_selection_gate_bug.py` — reads registry for prompt content
- `senzing-bootcamp/scripts/test_hooks.py` — reads registry for hook ID validation
- `senzing-bootcamp/scripts/lint_steering.py` — reads registry for hook consistency

### 7. Update Documentation References

- `docs/guides/HOOKS_INSTALLATION_GUIDE.md` — update reference path
- `hooks/README.md` — update reference to mention both files

## Token Budget Analysis

| File | Estimated Tokens | Under Threshold? |
|------|-----------------|------------------|
| `hook-registry.md` (summary) | ~2,000 | ✅ (< 5,000) |
| `hook-registry-detail.md` (detail) | ~6,500 | ❌ (> 5,000) |

The detail file at ~6,500 tokens exceeds the threshold, but this is acceptable because:
1. It uses `inclusion: manual` — only loaded when actively creating hooks
2. It's loaded once during onboarding and once per module start (not repeatedly)
3. Splitting it further would fragment hook definitions across 3+ files, reducing usability

If strict compliance is required, the detail file could be split into `hook-registry-detail-critical.md` (~2,500 tokens) and `hook-registry-detail-modules.md` (~4,000 tokens). This is left as a future optimization.

## Correctness Properties

1. **Summary completeness**: Every hook in `hook-categories.yaml` appears in the summary table.
2. **Detail completeness**: Every hook in `hook-categories.yaml` has a full entry in the detail file.
3. **Bidirectional sync**: `sync_hook_registry.py --verify` validates both files against actual `.kiro.hook` files.
4. **Keyword routing preserved**: `hook`/`hooks` keywords still route to the summary file.
5. **Hook creation still works**: The `#[[file:]]` reference in `onboarding-flow.md` points to the detail file, so `createHook` still has access to full prompts.
6. **No functional regression**: All existing tests pass after updating file paths.

## Constraints

- `sync_hook_registry.py` must remain the single source of truth generator for both files
- Both files must pass `validate_commonmark.py`
- The summary file must be self-contained (readable without loading the detail file)
- The detail file must be self-contained (usable for hook creation without the summary)
- No third-party dependencies added to `sync_hook_registry.py`
