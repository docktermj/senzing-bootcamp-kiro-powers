# Progress File Schema

The file `config/bootcamp_progress.json` is the bootcamp's session state. It tracks which modules you have completed, which module and step you are currently working on, your step-level checkpoint history, registered data sources, database type, and chosen programming language. Every time you finish a step, the agent writes a checkpoint here so your progress survives across sessions. If this file is missing or corrupted, the agent cannot resume where you left off — `repair_progress.py` can reconstruct it from your workspace artifacts.

## Field Definitions

The progress file contains seven top-level fields:

| Field | JSON Type | Required / Optional | Valid Values | Description |
|-------|-----------|---------------------|--------------|-------------|
| `modules_completed` | array of integers | Required | `[1]`, `[1, 2, 3]`, etc. | Module numbers the bootcamper has finished, in completion order |
| `current_module` | integer or null | Required | `1` through `11`, or `null` | The module currently in progress; `null` when no module is active |
| `current_step` | integer, null, or string | Required | Any positive integer, `null`, or a sub-step identifier like `"5.3"` or `"7a"` | The active step within the current module; `null` after module completion |
| `step_history` | object | Optional | See [Step History Structure](#step-history-structure) | Per-module checkpoint records keyed by string module number |
| `data_sources` | array of strings | Optional | DATA_SOURCE keys, e.g. `["CUSTOMERS", "WATCHLIST"]` | Registered data source identifiers added during Modules 4–7 |
| `database_type` | string | Required | `"sqlite"` or `"postgresql"` | The database engine chosen during onboarding |
| `language` | string | Required | `"python"`, `"java"`, `"csharp"`, `"rust"`, `"typescript"` | The programming language chosen during onboarding |

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

## Validation Rules

The function `progress_utils.validate_progress_schema` enforces the following rules. Legacy files that lack `current_step` or `step_history` pass validation (backward compatible).

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
