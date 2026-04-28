# Design Document: Reorder Modules

## Overview

This design covers the renumbering of the Senzing Bootcamp's 12 modules from a 0-based scheme (0–11) to a 1-based scheme (1–12), with Business Problem moved to position 1. The change is purely documentation and configuration — no application code, SDK logic, or data transformations are modified.

The mapping is:

| New # | Module Name                | Old # | Old Filename Prefix        | New Filename Prefix         |
|-------|----------------------------|-------|----------------------------|-----------------------------|
| 1     | Business Problem           | 2     | `MODULE_2_` / `module-02-` | `MODULE_1_` / `module-01-`  |
| 2     | SDK Setup                  | 0     | `MODULE_0_` / `module-00-` | `MODULE_2_` / `module-02-`  |
| 3     | Quick Demo                 | 1     | `MODULE_1_` / `module-01-` | `MODULE_3_` / `module-03-`  |
| 4     | Data Collection            | 3     | `MODULE_3_` / `module-03-` | `MODULE_4_` / `module-04-`  |
| 5     | Data Quality and Mapping   | 4     | `MODULE_4_` / `module-04-` | `MODULE_5_` / `module-05-`  |
| 6     | Single Source Loading      | 5     | `MODULE_5_` / `module-05-` | `MODULE_6_` / `module-06-`  |
| 7     | Multi-Source Orchestration | 6     | `MODULE_6_` / `module-06-` | `MODULE_7_` / `module-07-`  |
| 8     | Query Validation           | 7     | `MODULE_7_` / `module-07-` | `MODULE_8_` / `module-08-`  |
| 9     | Performance Testing        | 8     | `MODULE_8_` / `module-08-` | `MODULE_9_` / `module-09-`  |
| 10    | Security Hardening         | 9     | `MODULE_9_` / `module-09-` | `MODULE_10_` / `module-10-` |
| 11    | Monitoring & Observability | 10    | `MODULE_10_` / `module-10-`| `MODULE_11_` / `module-11-` |
| 12    | Deployment & Packaging     | 11    | `MODULE_11_` / `module-11-`| `MODULE_12_` / `module-12-` |

Key constraint: because old and new numbers overlap (e.g., old `module-01` is Quick Demo, new `module-01` is Business Problem), renames must use a temporary intermediate name or be carefully ordered to avoid collisions.

## Architecture

This change has no runtime architecture. It is a batch find-and-replace across documentation, steering, hooks, and scripts within the `senzing-bootcamp/` power directory.

### Rename Collision Strategy

Direct renames will collide because old and new numbers overlap. The safest approach is a **two-phase rename**:

1. **Phase 1 — Rename all files to temporary names** using a `_TEMP_` prefix (e.g., `MODULE_2_BUSINESS_PROBLEM.md` → `MODULE_TEMP_1_BUSINESS_PROBLEM.md`).
2. **Phase 2 — Rename temporary names to final names** (e.g., `MODULE_TEMP_1_BUSINESS_PROBLEM.md` → `MODULE_1_BUSINESS_PROBLEM.md`).

This applies to both module doc files (`MODULE_N_*.md`) and steering files (`module-NN-*.md`).

### Content Update Strategy

After all files are renamed, content updates proceed file-by-file. Each file is updated to replace old module numbers with new ones in:
- Headings and titles
- Cross-reference links (file paths and module numbers)
- Navigation links (previous/next module)
- Prerequisite references
- Learning path definitions
- Dependency diagrams
- Code constants (Python dicts, argument ranges)

## Components and Interfaces

No new components are introduced. The affected file categories are:

### 1. Module Documentation Files (`senzing-bootcamp/docs/modules/`)

12 markdown files to rename and update internally. Plus `README.md` index to rewrite.

**Files:**
- `MODULE_0_SDK_SETUP.md` → `MODULE_2_SDK_SETUP.md`
- `MODULE_1_QUICK_DEMO.md` → `MODULE_3_QUICK_DEMO.md`
- `MODULE_2_BUSINESS_PROBLEM.md` → `MODULE_1_BUSINESS_PROBLEM.md`
- `MODULE_3_DATA_COLLECTION.md` → `MODULE_4_DATA_COLLECTION.md`
- `MODULE_4_DATA_QUALITY_AND_MAPPING.md` → `MODULE_5_DATA_QUALITY_AND_MAPPING.md`
- `MODULE_5_SINGLE_SOURCE_LOADING.md` → `MODULE_6_SINGLE_SOURCE_LOADING.md`
- `MODULE_6_MULTI_SOURCE_ORCHESTRATION.md` → `MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`
- `MODULE_7_QUERY_VALIDATION.md` → `MODULE_8_QUERY_VALIDATION.md`
- `MODULE_8_PERFORMANCE_TESTING.md` → `MODULE_9_PERFORMANCE_TESTING.md`
- `MODULE_9_SECURITY_HARDENING.md` → `MODULE_10_SECURITY_HARDENING.md`
- `MODULE_10_MONITORING_OBSERVABILITY.md` → `MODULE_11_MONITORING_OBSERVABILITY.md`
- `MODULE_11_DEPLOYMENT_PACKAGING.md` → `MODULE_12_DEPLOYMENT_PACKAGING.md`

### 2. Steering Files (`senzing-bootcamp/steering/`)

12 per-module steering files to rename and update, plus 1 reference file:
- `module-00-sdk-setup.md` → `module-02-sdk-setup.md`
- `module-01-quick-demo.md` → `module-03-quick-demo.md`
- `module-02-business-problem.md` → `module-01-business-problem.md`
- `module-03-data-collection.md` → `module-04-data-collection.md`
- `module-04-data-quality-mapping.md` → `module-05-data-quality-mapping.md`
- `module-05-single-source.md` → `module-06-single-source.md`
- `module-06-multi-source.md` → `module-07-multi-source.md`
- `module-06-reference.md` → `module-07-reference.md`
- `module-07-query-validation.md` → `module-08-query-validation.md`
- `module-08-performance.md` → `module-09-performance.md`
- `module-09-security.md` → `module-10-security.md`
- `module-10-monitoring.md` → `module-11-monitoring.md`
- `module-11-deployment.md` → `module-12-deployment.md`

Cross-cutting steering files to update content (no rename):
- `agent-instructions.md` — module steering mapping (`0→module-00-...` through `11→module-11-...`)
- `onboarding-flow.md` — track definitions, module table, hook registry
- `module-transitions.md` — journey map example
- `module-completion.md` — path completion table
- `module-prerequisites.md` — dependency table, blocker table
- `session-resume.md` — module references
- `steering-index.yaml` — module-to-file mapping

### 3. POWER.md (`senzing-bootcamp/POWER.md`)

Update: overview (Modules 0-11 → 1-12), module table, steering file list, learning tracks, skip-ahead guidance, hook references, troubleshooting, useful commands.

### 4. Diagram Files (`senzing-bootcamp/docs/diagrams/`)

- `module-flow.md` — ASCII flow diagram, learning paths, dependencies, skip conditions, outputs
- `module-prerequisites.md` — Mermaid graph, learning paths table, skip points

### 5. Guide Files (`senzing-bootcamp/docs/guides/`)

All 15 guide files need scanning for module number references and file path references. Key files likely affected:
- `QUICK_START.md`, `ONBOARDING_CHECKLIST.md`, `PROGRESS_TRACKER.md`, `COMMON_MISTAKES.md`, `FAQ.md`, `AFTER_BOOTCAMP.md`, `GETTING_HELP.md`, `HOOKS_INSTALLATION_GUIDE.md`

### 6. Hook Files (`senzing-bootcamp/hooks/`)

- `module11-phase-gate.kiro.hook` → rename to `module12-phase-gate.kiro.hook`, update content references from Module 11 to Module 12
- All other hook files: scan for module number references and update

### 7. Script Files (`senzing-bootcamp/scripts/`)

- `status.py` — `MODULE_NAMES` dict (keys 0-11 → 1-12), `NEXT_STEPS` dict, `sync_progress_tracker` range, progress bar total
- `validate_module.py` — `VALIDATORS` dict (keys 0-11 → 1-12), `MODULE_NAMES` dict, `--module` choices range, `--next` choices range, validator function names and docstrings
- `repair_progress.py` — `NAMES` dict (keys 0-12 → 1-12), detection logic, range references
- Other scripts: scan for module number references

### 8. Module README (`senzing-bootcamp/docs/modules/README.md`)

Complete rewrite: module listing order, file links, dependency diagram, quick reference table.

### 9. Hooks README (`senzing-bootcamp/hooks/README.md`)

Scan for module number references.

### 10. Docs README (`senzing-bootcamp/docs/README.md`)

Scan for module number references.

## Data Models

No data models are affected. The `config/bootcamp_progress.json` schema is not changed by this spec — it is a runtime file created by the agent during bootcamp sessions. The renumbering only affects the static power distribution files.

Note: After this change, new bootcamp sessions will use module numbers 1-12 in `bootcamp_progress.json`. Existing sessions with 0-11 numbering would need manual migration, but that is outside the scope of this change (the power is pre-release).

## Error Handling

### Rename Collisions

The two-phase rename strategy (via temporary names) prevents file overwrites. If a temporary file already exists, the rename should fail loudly rather than silently overwrite.

### Stale References

After all changes, a grep-based validation pass should confirm zero remaining references to:
- `Module 0` as a module identifier
- Old steering filenames (`module-00-`, etc.)
- Old module doc filenames (`MODULE_0_`, etc.)

### Script Argument Ranges

Scripts that accept `--module N` or `--next N` must update their `choices=range(0, 12)` to `choices=range(1, 13)` to accept 1-12 and reject 0.

## Testing Strategy

Property-based testing does not apply to this feature. The change is purely documentation and configuration — there are no functions, data transformations, parsers, or serializers to test with generated inputs.

### Why PBT Does Not Apply

- All changes are static text replacements in markdown, YAML, JSON, and Python files
- There is no input/output behavior that varies meaningfully with generated inputs
- The "correctness" of this change is verified by exhaustive grep-based validation, not by testing functions

### Validation Approach

1. **Grep-based stale reference check**: After all changes, search the entire `senzing-bootcamp/` directory for any remaining references to old numbering (e.g., `Module 0`, `module-00-`, `MODULE_0_`). Zero matches expected.
2. **File existence check**: Verify all 12 module doc files exist with new names (1-12) and no files exist with old names.
3. **File existence check**: Verify all 13 steering files exist with new names and no files exist with old names.
4. **Link integrity**: Verify all markdown links to module files and steering files resolve to existing files.
5. **Script smoke test**: Run `python senzing-bootcamp/scripts/validate_power.py` to confirm power integrity.
6. **Manual review**: Spot-check a sample of updated files for correct module numbers in headings, navigation links, and cross-references.
