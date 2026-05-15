# Design Document

## Overview

This design describes a pure rename of Module 6 from "Load Data" to "Data Processing" across the senzing-bootcamp Kiro Power. The change touches file names, headings, config values, script strings, test strings, and cross-references — but introduces no behavioral changes to the module workflow.

## Architecture

### Approach

The rename is executed as a batch find-and-replace operation across three categories:

1. **File renames** — 3 files get new names (steering root, reference file, docs file)
2. **Content updates** — ~20 files get string replacements for the module name and filename references
3. **Verification** — existing tests are run to confirm nothing broke

No new files, modules, or abstractions are introduced. The phase sub-files (`module-06-phaseA-build-loading.md`, etc.) retain their names because they describe sub-phases of the module, not the module title itself.

### Files Changed

```text
senzing-bootcamp/
├── steering/
│   ├── module-06-load-data.md          → module-06-data-processing.md (RENAME)
│   ├── load-data-reference.md          → data-processing-reference.md (RENAME)
│   ├── steering-index.yaml             (UPDATE references + file_metadata keys)
│   ├── module-prerequisites.md         (UPDATE "Load Data" → "Data Processing")
│   ├── module-transitions.md           (UPDATE example journey map if present)
│   ├── common-pitfalls.md              (UPDATE section heading)
│   └── module-06-phaseD-validation.md  (UPDATE #[[file:]] include path)
├── config/
│   └── module-dependencies.yaml        (UPDATE name field for module 6)
├── scripts/
│   ├── validate_module.py              (UPDATE module name string)
│   ├── rollback_module.py              (UPDATE module name string)
│   ├── status.py                       (UPDATE module name string + hint text)
│   ├── visualize_dependencies.py       (UPDATE module name string)
│   └── split_steering.py              (UPDATE filename string)
├── docs/
│   ├── modules/
│   │   ├── MODULE_6_LOAD_DATA.md       → MODULE_6_DATA_PROCESSING.md (RENAME)
│   │   └── README.md                   (UPDATE heading, file link, steering ref)
│   └── guides/
│       └── ARCHITECTURE.md             (UPDATE module name references)
├── hooks/
│   └── README.md                       (UPDATE module name reference)
├── tests/
│   ├── test_track_switcher_properties.py  (UPDATE module name string)
│   ├── test_track_switcher_unit.py        (UPDATE module name string)
│   ├── test_rollback_module.py            (UPDATE comment string)
│   ├── test_module_closing_question_ownership.py (UPDATE heading + filename)
│   ├── test_split_steering.py             (UPDATE filename references)
│   └── test_mapping_workflow_integration.py (UPDATE filename reference)
├── POWER.md                            (UPDATE module table, steering list, modules table)
└── CHANGELOG.md                        (UPDATE historical reference if needed)
```

### Rename Strategy

1. **Rename files first** — Move the 3 files to their new names
2. **Update all content** — Replace strings in all affected files
3. **Run tests** — Verify the existing test suite passes
4. **Clean up** — Delete `.hypothesis/constants/` if tests fail due to cached data (they will regenerate)

### String Replacements

| Old String | New String | Context |
|---|---|---|
| `"Load Data"` | `"Data Processing"` | Module name in scripts, tests, configs |
| `Module 6: Load Data` | `Module 6: Data Processing` | Headings in steering/docs |
| `MODULE 6: LOAD DATA` | `MODULE 6: DATA PROCESSING` | Banner text in docs |
| `module-06-load-data.md` | `module-06-data-processing.md` | Filename references |
| `load-data-reference.md` | `data-processing-reference.md` | Filename references |
| `MODULE_6_LOAD_DATA.md` | `MODULE_6_DATA_PROCESSING.md` | Documentation filename references |
| `MODULE_6_LOAD_DATA` | `MODULE_6_DATA_PROCESSING` | Link targets |
| `6 — Load Data` | `6 — Data Processing` | POWER.md table entries |
| `Module 6 (Load Data)` | `Module 6 (Data Processing)` | Hooks README |
| `Start Module 6: Load Data` | `Start Module 6: Data Processing` | status.py hint |

### What Does NOT Change

- Phase sub-file names (`module-06-phaseA-build-loading.md`, etc.)
- Module 6 workflow steps, gate conditions, prerequisites, skip conditions
- The `"Data already loaded"` skip_if condition (describes user state, not module name)
- References to "loading" as a verb (e.g., "loading programs", "load data into Senzing")
- The `DATABASE_MIGRATION.md` "Re-load Data" heading (describes an action, not the module)
- The `MODULE_5_DATA_QUALITY_AND_MAPPING.md` "LOAD DATA" step (describes a transformation step, not Module 6)
- `.hypothesis/constants/` cached test data (regenerates automatically)
- Historical references in `.kiro/specs/` (existing spec documents are historical records)

## Correctness Properties

### Property 1: No Remaining Module 6 "Load Data" References

After the rename, no file in the distributed power (excluding `.hypothesis/constants/`, `.history/`, and `.kiro/specs/` historical documents) should contain the string "Load Data" when used as the name of Module 6. Specifically:

- The pattern `6: "Load Data"` must not appear in any Python file
- The pattern `Module 6: Load Data` must not appear in any markdown file
- The pattern `module-06-load-data.md` must not appear in any file
- The pattern `load-data-reference.md` must not appear in any file
- The pattern `MODULE_6_LOAD_DATA` must not appear in any file

**Verification:** A grep-based scan of the codebase after all changes.

### Property 2: File Existence Consistency

After the rename:
- `senzing-bootcamp/steering/module-06-data-processing.md` exists
- `senzing-bootcamp/steering/data-processing-reference.md` exists
- `senzing-bootcamp/docs/modules/MODULE_6_DATA_PROCESSING.md` exists
- `senzing-bootcamp/steering/module-06-load-data.md` does NOT exist
- `senzing-bootcamp/steering/load-data-reference.md` does NOT exist
- `senzing-bootcamp/docs/modules/MODULE_6_LOAD_DATA.md` does NOT exist

### Property 3: Phase Sub-Files Unchanged

The following files must still exist with their original names:
- `senzing-bootcamp/steering/module-06-phaseA-build-loading.md`
- `senzing-bootcamp/steering/module-06-phaseB-load-first-source.md`
- `senzing-bootcamp/steering/module-06-phaseC-multi-source.md`
- `senzing-bootcamp/steering/module-06-phaseD-validation.md`

### Property 4: Steering Index Internal Consistency

The `steering-index.yaml` file must satisfy:
- `modules.6.root` equals `module-06-data-processing.md`
- `file_metadata` contains key `module-06-data-processing.md` (not `module-06-load-data.md`)
- `file_metadata` contains key `data-processing-reference.md` (not `load-data-reference.md`)
- Token counts for renamed entries match their pre-rename values (1496 and 1172 respectively)

### Property 5: Module Dependencies Consistency

The `module-dependencies.yaml` file must satisfy:
- `modules.6.name` equals `"Data Processing"`
- `modules.6.requires` equals `[2, 5]` (unchanged)
- `modules.6.skip_if` equals `"Data already loaded"` (unchanged — describes user state)

### Property 6: Test Suite Passes

After all changes, running `pytest senzing-bootcamp/tests/` must produce no failures attributable to the rename. Tests that reference the old module name in assertions must be updated to reference the new name.

## Alternatives Considered

1. **Rename phase sub-files too** — Rejected because the phase names describe sub-activities (build-loading, load-first-source, multi-source, validation) which are still accurate descriptions of what happens within the module. Renaming them would be unnecessary churn.

2. **Update .kiro/specs/ historical documents** — Rejected because spec documents are historical records of past decisions. Updating them would rewrite history and provide no functional benefit.

3. **Update CHANGELOG.md historical entries** — The CHANGELOG reference to "load-data-reference.md" in a historical entry will be left as-is since it describes what happened at that point in time. Only forward-looking references are updated.
