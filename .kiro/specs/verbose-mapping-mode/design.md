# Design Document: Verbose Mapping Mode

## Overview

This bugfix adds a mapping-specific verbosity prompt at the start of Module 5 Phase 2 (Data Mapping). Currently, the agent jumps straight into `mapping_workflow` without asking the bootcamper whether they want verbose mode (detailed step-by-step mapping output) or concise mode (quick mapping with minimal output). The fix introduces a single 👉 question before the first `mapping_workflow` call, persists the choice as `mapping_verbosity` in `config/bootcamp_preferences.yaml`, and adjusts the agent's presentation of mapping results accordingly.

### Design Rationale

The existing verbosity control system (`verbosity-control.md`) handles general output categories (explanations, code walkthroughs, etc.) but doesn't address the mapping-specific workflow where intermediate results (field detection, attribute mapping decisions, transformation previews) are either shown in full or collapsed. A mapping-specific verbosity key is needed because:

- The mapping workflow has its own distinct intermediate outputs that don't map cleanly to the general verbosity categories
- Users who want detailed general output may still want quick mapping, and vice versa
- The `mapping_verbosity` key is additive — it doesn't replace or conflict with the general `verbosity` system
- The fix is entirely a steering file change — no new Python scripts or runtime code needed

The implementation modifies one steering file (`module-05-phase2-data-mapping.md`) and adds one new key to the preferences schema. No new files are created.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│ module-05-phase2-data-mapping.md (steering)             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ NEW: Pre-mapping verbosity prompt (before Step 1)│   │
│  │ - Check for existing mapping_verbosity pref      │   │
│  │ - If none: ask 👉 verbose or concise?            │   │
│  │ - If exists: acknowledge and offer switch        │   │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ MODIFIED: Steps 2, 3, 4, 5, 7, 8 presentation   │   │
│  │ - Verbose: show all intermediate details         │   │
│  │ - Concise: show only final results + warnings    │   │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ NEW: Mid-mapping switch instruction              │   │
│  │ - Honor "switch to verbose/concise" at any time  │   │
│  │ - Update mapping_verbosity in preferences        │   │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ config/bootcamp_preferences.yaml                        │
│                                                         │
│  mapping_verbosity: verbose | concise | null            │
│  (new key, additive to existing verbosity system)       │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **module-05-phase2-data-mapping.md** — The only steering file modified. Gains a pre-mapping verbosity prompt section and per-step presentation rules conditioned on the `mapping_verbosity` preference.

2. **config/bootcamp_preferences.yaml** — Gains a new `mapping_verbosity` key (values: `verbose`, `concise`, or `null`). This key is independent of the general `verbosity` system.

## Components and Interfaces

### 1. Pre-Mapping Verbosity Prompt (new section in steering)

Inserted before Step 1 ("Start") in `module-05-phase2-data-mapping.md`. The agent:

1. Reads `config/bootcamp_preferences.yaml` and checks for `mapping_verbosity` key
2. If `mapping_verbosity` is `null` or absent: presents a single 👉 question offering verbose or concise mode with brief descriptions of each
3. If `mapping_verbosity` is already set: acknowledges the existing preference briefly ("Using your verbose mapping preference — say 'switch to concise' if you'd prefer less detail") and proceeds
4. Persists the choice to `mapping_verbosity` in the preferences file

### 2. Per-Step Presentation Rules (modifications to existing steps)

Each mapping step that produces intermediate output gains conditional presentation instructions:

**Verbose mode shows:**
- Step 2 (Profile): Full column table with types, sample values, completeness %, and what each means
- Step 3 (Plan): Entity type decision rationale, field-by-field mapping/skip reasoning
- Step 4 (Map): Full mapping table with per-field rationale and confidence scores
- Step 5 (Generate): Sample target JSON record with annotations
- Step 7 (Test): Pass/fail details, sample record, observations
- Step 8 (Quality): Per-feature coverage breakdown with matching implications

**Concise mode shows:**
- Step 2 (Profile): Summary line (N columns, X% overall completeness, key issues)
- Step 3 (Plan): Entity type + count of mapped/skipped fields
- Step 4 (Map): Final mapping table without rationale column
- Step 5 (Generate): File path and format only
- Step 7 (Test): Pass/fail + output file path
- Step 8 (Quality): Overall score + count of mapped vs. unmapped fields + warnings only

### 3. Mid-Mapping Switch Instruction (new section in steering)

A new instruction block tells the agent to honor inline verbosity changes:
- If the bootcamper says "switch to verbose" or "switch to concise" (or natural variants), update `mapping_verbosity` in preferences and apply immediately
- Confirm the switch briefly without interrupting workflow

### 4. Preferences Schema Addition

New key in `config/bootcamp_preferences.yaml`:

```yaml
# Mapping-specific verbosity (set during Module 5 Phase 2)
# Values: verbose, concise, or null (not yet asked)
mapping_verbosity: null
```

## Data Models

### Mapping Verbosity Preference

| Key | Type | Values | Default |
|-----|------|--------|---------|
| `mapping_verbosity` | string or null | `verbose`, `concise`, `null` | `null` |

This key is:
- Independent of the general `verbosity` preset system
- Only consulted during Module 5 Phase 2 mapping workflow
- Persisted across sessions (re-read on session resume)
- Changeable mid-mapping via natural language

### Presentation Rules by Mode

| Step | Verbose Output | Concise Output |
|------|---------------|----------------|
| 2 (Profile) | Full column table: types, samples, completeness %, meaning | Summary: N columns, X% completeness, key issues |
| 3 (Plan) | Entity type rationale, per-field mapping/skip reasoning | Entity type + mapped/skipped field counts |
| 4 (Map) | Mapping table with rationale and confidence per field | Mapping table without rationale |
| 5 (Generate) | Sample JSON record with annotations | File path and format statement |
| 7 (Test) | Pass/fail, sample record, output path, observations | Pass/fail + output path |
| 8 (Quality) | Per-feature coverage, matching implications, issues | Overall score + mapped/unmapped counts + warnings |

## Unchanged Behavior (Regression Prevention)

- The general `verbosity` system (presets, categories, NL adjustments) continues to work for all non-mapping output
- The `mapping_workflow` MCP tool calls are identical regardless of verbosity mode — only the agent's presentation changes
- Modules other than Module 5 are unaffected
- The `state` parameter passed to `mapping_workflow` is never modified by verbosity mode
- Inline "switch to verbose/concise" continues to work as before (this fix formalizes it for mapping specifically)

## Error Handling

### Missing Preferences File

If `config/bootcamp_preferences.yaml` doesn't exist when the agent reaches Phase 2, the agent creates it with `mapping_verbosity: null` and proceeds to ask the question. This shouldn't happen in practice (the file is created during Module 2) but handles edge cases.

### Invalid mapping_verbosity Value

If the `mapping_verbosity` key contains an unexpected value (not `verbose`, `concise`, or `null`), the agent treats it as `null` and re-asks the question.

### Bootcamper Skips the Question

If the bootcamper doesn't answer the verbosity question (e.g., says "just start" or ignores it), the agent defaults to `verbose` (since the mapping workflow is educational and first-time users benefit from seeing the details) and notes: "Defaulting to verbose mode — say 'switch to concise' anytime if you want less detail."

## Testing Strategy

This is a steering-only change. Testing validates:

1. **Steering file structure** — The modified `module-05-phase2-data-mapping.md` contains the verbosity prompt section, per-step conditional presentation rules, and mid-mapping switch instructions
2. **Preferences schema** — The `bootcamp_preferences.yaml` template includes the `mapping_verbosity` key with `null` default
3. **No regression** — The general verbosity system files are unchanged; the `mapping_verbosity` key doesn't interfere with existing `verbosity` key

Test file: `senzing-bootcamp/tests/test_mapping_verbosity.py`

Tests verify:
- The steering file contains the verbosity prompt section marker
- The steering file contains verbose-mode and concise-mode conditional blocks
- The preferences file contains the `mapping_verbosity` key
- The steering file preserves all existing step content (no steps removed)
- The mid-mapping switch instruction is present
