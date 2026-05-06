# Design: Cross-Module Artifact Dependency Tracking

## Overview

A lightweight artifact readiness check runs at module start (Modules 4–11) to verify that prerequisite module outputs exist on disk. Missing artifacts are reported with recovery options before the bootcamper hits failures mid-step.

## Artifact Manifest

```yaml
# config/module-artifacts.yaml
version: "1"

modules:
  4:
    produces:
      - path: "data/raw/"
        type: directory
        description: "Raw data source files"
        required: true
      - path: "config/data_sources.yaml"
        type: file
        description: "Data source registry"
        required: true

  5:
    produces:
      - path: "config/mapping_spec.json"
        type: file
        description: "Senzing mapping specification"
        required: true
    requires_from:
      4: ["data/raw/", "config/data_sources.yaml"]

  6:
    produces:
      - path: "src/load/"
        type: directory
        description: "Loading scripts"
        required: true
    requires_from:
      5: ["config/mapping_spec.json"]

  7:
    produces:
      - path: "src/query/"
        type: directory
        description: "Query scripts"
        required: true
    requires_from:
      6: ["src/load/"]
```

### Design Decisions

1. **File existence only** — The check validates that paths exist, not that content is correct. Content validation is the module's responsibility.
2. **Advisory, not blocking** — The bootcamper can always skip the check and proceed.
3. **Directory checks** — For directory artifacts, check that the directory exists and is non-empty.
4. **Dynamic artifacts** — Some artifacts depend on the bootcamper's language choice (e.g., `src/load/load.py` vs `src/load/Load.java`). The manifest uses directory-level checks for these.
5. **Data source registry integration** — If `config/data_sources.yaml` exists, cross-reference registered sources against files in `data/raw/`.

## Check Flow

```console
Module Start
    │
    ├─ Read module-artifacts.yaml
    ├─ Get current module's requires_from
    ├─ For each required artifact:
    │   ├─ Check existence on disk
    │   └─ Record: present / missing
    │
    ├─ All present? → Proceed silently
    └─ Any missing? → Report + offer options
```

## Agent Behavior on Missing Artifacts

```console
⚠️ Some prerequisite artifacts are missing for Module 6:

| Missing | From Module | Description |
|---------|-------------|-------------|
| config/mapping_spec.json | Module 5 | Senzing mapping specification |

👉 How would you like to proceed?
(a) Go back to Module 5 to complete the mapping step
(b) Skip this check and proceed anyway
(c) Run rollback to reset to a clean state
```

## validate_module.py Extension

```console
$ python validate_module.py --artifacts 6
Checking artifacts for Module 6...
✅ config/mapping_spec.json (from Module 5)
✅ src/load/ (from Module 6 — already started)
All prerequisites satisfied.
```

## Files Created/Modified

- `senzing-bootcamp/config/module-artifacts.yaml` — new artifact manifest
- `senzing-bootcamp/scripts/validate_module.py` — add `--artifacts` flag
- `senzing-bootcamp/steering/agent-instructions.md` — add artifact check instruction at module start
- `senzing-bootcamp/docs/guides/MODULE_ARTIFACTS.md` — document the manifest schema

## Testing

- Property test: all modules in manifest have valid module numbers (1-11)
- Property test: requires_from references only modules with lower numbers
- Unit test: missing file detection works correctly
- Unit test: directory non-empty check works correctly
- Unit test: --artifacts flag accepted by validate_module.py
