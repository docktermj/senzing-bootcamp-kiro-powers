# Module Artifacts Schema

The `config/module-artifacts.yaml` manifest declares what each bootcamp module produces and what it requires from earlier modules. The agent uses this at module start to verify prerequisite outputs exist on disk before proceeding.

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version (currently `"1"`) |
| `modules` | mapping | Top-level map keyed by module number (integer) |
| `modules.<N>.produces` | list | Artifacts this module creates on disk |
| `modules.<N>.produces[].path` | string | Relative path from project root (trailing `/` = directory) |
| `modules.<N>.produces[].type` | string | Either `"file"` or `"directory"` |
| `modules.<N>.produces[].description` | string | Human-readable description of the artifact |
| `modules.<N>.produces[].required` | boolean | Whether the artifact is mandatory for downstream modules |
| `modules.<N>.requires_from` | mapping | Map of source module number to list of artifact paths needed |

## Validation Rules

- Module numbers must be integers between 1 and 11.
- `requires_from` may only reference modules with a lower number (no circular dependencies).
- All `path` values must be relative (no leading `/`).
- Directory paths end with `/`; file paths do not.
- For directory artifacts, the check verifies the directory exists and is non-empty (contains at least one file).
- For file artifacts, the check verifies the file exists.

## Example (Modules 4-7)

```yaml
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
      - path: "data/transformed/"
        type: directory
        description: "Transformed data files"
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
      5: ["data/transformed/"]
  7:
    produces:
      - path: "src/query/"
        type: directory
        description: "Query scripts"
        required: true
    requires_from:
      6: ["src/load/"]
```

## CLI Usage

Check artifact dependencies for a specific module:

```text
python3 scripts/validate_module.py --artifacts 6
```

Output shows a summary table with each dependency's path, source module, and status (present or missing). Exit code is 0 when all required artifacts are present, 1 when any are missing.

## Agent Behavior

At module start (Modules 4-11), the agent reads `config/module-artifacts.yaml` and checks `requires_from` entries. If all artifacts are present, it proceeds silently. If any are missing, it reports which files are absent and from which module, then offers three options:

1. Go back to complete the prerequisite module
2. Skip the check and proceed anyway
3. Run rollback to reset state

The check is advisory — the bootcamper can always skip.
