# Progress File Schema

The file `config/bootcamp_progress.json` is the bootcamp's session state. It tracks which modules you have completed, which module and step you are currently working on, your step-level checkpoint history, registered data sources, database type, and chosen programming language. Every time you finish a step, the agent writes a checkpoint here so your progress survives across sessions. If this file is missing or corrupted, the agent cannot resume where you left off — `repair_progress.py` can reconstruct it from your workspace artifacts.

## Field Definitions

The progress file contains nine top-level fields:

| Field | JSON Type | Required / Optional | Valid Values | Description |
|-------|-----------|---------------------|--------------|-------------|
| `modules_completed` | array of integers | Required | `[1]`, `[1, 2, 3]`, etc. | Module numbers the bootcamper has finished, in completion order |
| `current_module` | integer or null | Required | `1` through `11`, or `null` | The module currently in progress; `null` when no module is active |
| `current_step` | integer, null, or string | Required | Any positive integer, `null`, or a sub-step identifier like `"5.3"` or `"7a"` | The active step within the current module; `null` after module completion |
| `step_history` | object | Optional | See [Step History Structure](#step-history-structure) | Per-module checkpoint records keyed by string module number |
| `data_sources` | array of strings | Optional | DATA_SOURCE keys, e.g. `["CUSTOMERS", "WATCHLIST"]` | Registered data source identifiers added during Modules 4–7 |
| `database_type` | string | Required | `"sqlite"` or `"postgresql"` | The database engine chosen during onboarding |
| `language` | string | Required | `"python"`, `"java"`, `"csharp"`, `"rust"`, `"typescript"` | The programming language chosen during onboarding |
| `license_record_limit` | integer or null | Optional | `null`, `0`, or any positive integer | The active Senzing license's record cap, detected in Module 2 and reused by the capacity/sampling decisions in Modules 1, 4, 6, and 8. See [License Record Limit](#license-record-limit) |
| `setup_summary` | object | Optional | See [Setup Summary](#setup-summary) | A snapshot of what the administrative setup phase (onboarding Steps 0b–2) actually did — MCP reachability, power version, directories, hooks, steering, and the preflight verdict — persisted so session resume can replay it. Secret-free. |

## Step History Structure

The `step_history` object records the last checkpoint reached in each module. Keys are string representations of module numbers (`"1"` through `"11"`), and each value is an object with two fields:

| Field | JSON Type | Description |
|-------|-----------|-------------|
| `last_completed_step` | integer | The highest step number completed in this module |
| `updated_at` | string | ISO 8601 UTC timestamp of when the checkpoint was written (e.g. `"2026-04-20T14:30:00+00:00"`) |

A module only appears in `step_history` after its first step checkpoint is written. Modules that have not been started have no entry.

The `current_step` field works together with `step_history` to track position within a module:

- **Integer values** represent whole-step checkpoints written by `progress_utils.write_checkpoint`.
- **`null`** means the current module has been completed and `current_step` was cleared by `progress_utils.clear_step`.
- **Sub-step string identifiers** such as `"5.3"` or `"7a"` are supported by the mid-module session persistence feature, allowing finer-grained resume points within a step.

## License Record Limit

The optional `license_record_limit` field records the record cap of the active Senzing license so the capacity and sampling decisions in Modules 1, 4, 6, and 8 can reuse it without re-querying the SDK. It is detected in Module 2 after the license is configured (via `SzProduct.get_license()`, whose semantics come from the Senzing MCP server) and persisted here.

The field has three meaningful states:

- **`null` or absent** — the active license limit has not been detected yet. Callers fall back to the built-in evaluation capacity (confirmed via the Senzing MCP server). A legacy progress file written before this field existed is treated exactly like `null`, so it remains valid and behaves as before.
- **`0`** — the license imposes no record cap (unlimited). No sampling is recommended for license reasons regardless of dataset size.
- **positive integer** — the license caps loading at that many records. Sampling is recommended only when the dataset total genuinely exceeds this value.

## Setup Summary

The optional `setup_summary` object is a durable, structured snapshot of what the quiet administrative setup phase actually did during onboarding (Steps 0b–2, presented once at the end of the preface in the Administrative Setup Summary). Persisting it lets `session-resume.md` replay a concise "your environment already has…" recap on resume instead of re-narrating or re-checking work that was already done.

Every value is derived from the **real** outcomes of onboarding Steps 0b–2 — never hardcoded. The `hooks_installed` record mirrors the authoritative `hooks_installed` key already written to `config/bootcamp_preferences.yaml` (single source of truth preserved; `setup_summary` is the resume-facing snapshot, not a divergent duplicate). In team mode, `setup_summary` is written to the member-specific progress file, consistent with the rest of progress tracking.

The object contains the following fields:

| Field | JSON Type | Required / Optional | Valid Values | Description |
|-------|-----------|---------------------|--------------|-------------|
| `captured_at` | string | Required | ISO 8601 timestamp (e.g. `"2026-07-14T13:49:00-05:00"`) | When the summary was captured and written |
| `power_version` | string | Required | A version string, e.g. `"1.4.0"` | The senzing-bootcamp power version detected during onboarding (Step 0c) |
| `mcp_reachable` | boolean | Required | `true` or `false` | Whether the Senzing MCP server health check succeeded (Step 0b) |
| `directories_created` | boolean | Required | `true` or `false` | Whether the Senzing project directories were created (Step 1) |
| `hooks_installed` | object | Required | See below | The background quality-check hooks installed (Step 1); mirrors `bootcamp_preferences.yaml` |
| `steering_generated` | array of strings | Required | Foundational steering filenames, e.g. `["product.md", "tech.md", "structure.md"]` | The foundational steering files generated during setup (Step 1) |
| `preflight_verdict` | string | Required | `"PASS"`, `"WARN"`, or `"FAIL"` | The overall verdict of the Step 2 preflight environment check |
| `preflight_warnings` | array of strings | Optional | Human-readable warning messages | Any non-fatal preflight findings (empty or absent when there are none) |
| `deferrals` | array of strings | Optional | Human-readable deferral notes | Items the bootcamper deferred during setup (e.g. a declined runtime install), noting where they are revisited |

The nested `hooks_installed` object has two fields:

| Field | JSON Type | Description |
|-------|-----------|-------------|
| `count` | integer | The verified number of hooks installed |
| `names` | array of strings | The installed hook IDs (e.g. `["ask-bootcamper", "review-bootcamper-input", "code-style-check"]`) |

**Secret-free by contract:** `setup_summary` records only names, counts, versions, and verdicts. It SHALL NOT contain secrets, credentials, tokens, or connection strings. This keeps the block safe to persist in the workspace and to replay on resume.

**Backward compatible:** the entire `setup_summary` block is optional. Older projects (and sessions where the write was skipped or failed) simply have no block; its absence is valid and is never an error. Resume proceeds unchanged when it is missing.

### Setup Summary Example

```json
{
  "setup_summary": {
    "captured_at": "2026-07-14T13:49:00-05:00",
    "power_version": "1.4.0",
    "mcp_reachable": true,
    "directories_created": true,
    "hooks_installed": {
      "count": 3,
      "names": ["ask-bootcamper", "review-bootcamper-input", "code-style-check"]
    },
    "steering_generated": ["product.md", "tech.md", "structure.md"],
    "preflight_verdict": "WARN",
    "preflight_warnings": ["Senzing SDK not installed — Module 2 will cover it"],
    "deferrals": ["runtime install declined (revisit in Module 2)"]
  }
}
```

## Validation Rules

The function `progress_utils.validate_progress_schema` enforces the following rules. Legacy files that lack `current_step`, `step_history`, `license_record_limit`, or `setup_summary` pass validation (backward compatible).

**`license_record_limit`** (if present):

- Must be an `int` (`0` or positive) or `null`.
- A negative integer produces a validation error (a limit is either `0` for unlimited or a positive cap).
- A boolean or any other non-int, non-null type produces a validation error.

**`current_step`** (if present):

- Must be an `int` or `null`.
- Any other type (string, float, boolean) produces a validation error.

**`step_history`** (if present):

- Must be a `dict` (JSON object).
- Each key must be a string representation of an integer in the range 1–12 (e.g. `"1"`, `"12"`). Keys outside this range or non-integer strings are rejected.
- Each value must be an object containing both:
  - `last_completed_step` — must be an `int`.
  - `updated_at` — must be a string that parses as a valid ISO 8601 datetime.
- Missing either required field, or providing the wrong type for either field, produces a validation error.

**`setup_summary`** (if present):

- Must be a `dict` (JSON object). An absent block is valid (backward compatible).
- `captured_at`, `power_version`, and `preflight_verdict` — must be strings when present; `preflight_verdict` must be one of `"PASS"`, `"WARN"`, or `"FAIL"`.
- `mcp_reachable` and `directories_created` — must be booleans when present.
- `steering_generated`, `preflight_warnings`, and `deferrals` — must be arrays of strings when present.
- `hooks_installed` — must be an object with an integer `count` and a `names` array of strings when present.
- No secret-like fields are permitted: the block must contain only names, counts, versions, and verdicts — never secrets, credentials, tokens, or connection strings.

## Complete Example

```json
{
  "modules_completed": [1, 2, 3],
  "current_module": 4,
  "current_step": 3,
  "step_history": {
    "1": {
      "last_completed_step": 10,
      "updated_at": "2026-04-15T09:12:00+00:00"
    },
    "2": {
      "last_completed_step": 8,
      "updated_at": "2026-04-16T11:45:00+00:00"
    },
    "3": {
      "last_completed_step": 6,
      "updated_at": "2026-04-18T14:30:00+00:00"
    },
    "4": {
      "last_completed_step": 3,
      "updated_at": "2026-04-20T10:05:00+00:00"
    }
  },
  "data_sources": ["CUSTOMERS"],
  "database_type": "sqlite",
  "language": "python"
}
```

This example shows a bootcamper who has completed Modules 1–3, is currently on step 3 of Module 4, has registered one data source (`CUSTOMERS`), and is using SQLite with Python.

## Read By

- `status.py` — renders the progress dashboard shown to the bootcamper
- `validate_module.py` — checks prerequisites before starting a new module
- `repair_progress.py` — reads the file to detect corruption or missing fields
- `export_results.py` — includes progress data in exported bootcamp results
- `rollback_module.py` — reads progress to revert a module to its previous state
- `session-resume.md` — steering file that guides the agent to restore session context on startup
- `agent-instructions.md` — steering file that references progress state for module routing decisions

## Written By

- `progress_utils.py` — writes step-level checkpoints via `write_checkpoint` and clears the current step via `clear_step` on module completion
- `repair_progress.py --fix` — reconstructs a valid progress file from workspace artifacts when the original is missing or corrupted
- The agent during onboarding (creates the initial file with `database_type`, `language`, and empty module state) and module transitions (updates `modules_completed`, `current_module`, and `data_sources`)
