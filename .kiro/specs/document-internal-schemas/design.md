# Design Document: Document Internal Schemas

## Overview

This feature adds three schema guide documents to `senzing-bootcamp/docs/guides/` and updates the guides README to index them. The guides document the structure, field definitions, types, valid values, complete examples, and script interactions for three internal configuration files:

1. **PROGRESS_FILE_SCHEMA.md** — documents `config/bootcamp_progress.json`
2. **DATA_SOURCE_REGISTRY.md** — documents `config/data_sources.yaml`
3. **STEERING_INDEX.md** — documents `senzing-bootcamp/steering/steering-index.yaml`

Each guide follows the established documentation style in `docs/guides/`, matching the structure and tone of existing guides like `QUALITY_SCORING_METHODOLOGY.md` and `PERFORMANCE_BASELINES.md`.

### Design Rationale

- **Static Markdown files only** — no code changes, no new scripts, no new validation logic. The guides are pure documentation that reference existing scripts and schemas.
- **Style consistency** — all three guides follow the same section ordering (introduction → field definitions → example → Read By → Written By) to match Requirement 7.
- **Single source of truth** — field definitions, enum values, and validation rules are derived directly from the existing scripts (`progress_utils.py`, `data_sources.py`, `measure_steering.py`, `lint_steering.py`) and the actual config files.

## Architecture

This feature has no runtime architecture. It produces four file changes:

```text
senzing-bootcamp/docs/guides/
├── PROGRESS_FILE_SCHEMA.md   ← NEW (Req 1, 2, 7)
├── DATA_SOURCE_REGISTRY.md   ← NEW (Req 3, 4, 7)
├── STEERING_INDEX.md         ← NEW (Req 5, 6, 7)
└── README.md                 ← MODIFIED (Req 8)
```

All files live under the `senzing-bootcamp/` distributed power directory, consistent with the repository organization rules.

### Document Structure Pattern

Each schema guide follows this consistent structure (per Requirement 7):

```text
# [Guide Title]                          ← Level-1 heading
[Introductory paragraph]                  ← What the file is and why it matters

## Field Definitions                      ← Markdown table with columns:
                                            Field, Type, Required, Valid Values, Description

## [Nested Structure] (if applicable)     ← Sub-object documentation

## Complete Example                       ← Fenced code block (json or yaml)

## Read By                                ← Bulleted list of scripts/steering files

## Written By                             ← Bulleted list of scripts/agents
```

## Components and Interfaces

### Component 1: PROGRESS_FILE_SCHEMA.md

**Purpose**: Documents the JSON schema for `config/bootcamp_progress.json`.

**Content sections**:
- **Field Definitions table**: 7 top-level fields (`modules_completed`, `current_module`, `current_step`, `step_history`, `data_sources`, `database_type`, `language`) with JSON type, required/optional, valid values, and description.
- **Step History Structure**: Nested documentation for the `step_history` object — keys are string integers "1" through "11", values contain `last_completed_step` (integer) and `updated_at` (ISO 8601 UTC string). Documents that `current_step` accepts integers, null, and sub-step string identifiers (e.g., "5.3", "7a").
- **Validation Rules**: Documents the rules enforced by `progress_utils.validate_progress_schema`: `current_step` must be int or null, `step_history` keys must be string integers in range 1–12, each entry must contain `last_completed_step` (int) and `updated_at` (valid ISO 8601).
- **Complete Example**: A valid JSON progress file with at least two completed modules, an active current step, populated step_history entries, and at least one data source.
- **Read By**: `status.py`, `validate_module.py`, `repair_progress.py`, `export_results.py`, `rollback_module.py`, `session-resume.md`, `agent-instructions.md`.
- **Written By**: `progress_utils.py` (step checkpoints), `repair_progress.py --fix` (reconstruction), the agent during onboarding and module transitions.

**Source of truth**: `progress_utils.py` (validation logic), `repair_progress.py` (field population).

### Component 2: DATA_SOURCE_REGISTRY.md

**Purpose**: Documents the YAML schema for `config/data_sources.yaml`.

**Content sections**:
- **Top-Level Structure**: `version` (string, currently "2") and `sources` (mapping of DATA_SOURCE keys to entry objects).
- **Key Constraint**: DATA_SOURCE keys must match `^[A-Z][A-Z0-9_]*$`.
- **Entry Field Definitions table**: 13 fields (`name`, `file_path`, `format`, `record_count`, `file_size_bytes`, `quality_score`, `mapping_status`, `load_status`, `test_load_status`, `test_entity_count`, `added_at`, `updated_at`, `issues`) with YAML type, required/optional, valid enum values, and description.
- **Enum Values**: `format` (csv, json, jsonl, xlsx, parquet, xml, other), `mapping_status` (pending, in_progress, complete), `load_status` (not_loaded, loading, loaded, failed), `test_load_status` (complete, skipped).
- **Complete Example**: A valid registry with version "2" and at least two data source entries showing different status combinations.
- **Schema Migration**: Version "1" registries are automatically migrated to version "2" by `data_sources.py --migrate`, backfilling `test_load_status` and `test_entity_count` as null.
- **Read By**: `data_sources.py`, `status.py` (via `render_data_sources_section`), the agent during Modules 4–7.
- **Written By**: The agent during data source registration (Modules 4–5), `data_sources.py --migrate`, the agent during loading status updates (Module 6).

**Source of truth**: `data_sources.py` (constants, `RegistryEntry` dataclass, `validate_registry`, `migrate_v1_to_v2`).

### Component 3: STEERING_INDEX.md

**Purpose**: Documents the YAML schema for `senzing-bootcamp/steering/steering-index.yaml`.

**Content sections**:
- **Top-Level Sections**: `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget`.
- **Module Entry Formats**: Simple format (module number → filename string) and split format (module number → object with `root` key and `phases` mapping, where each phase has `file`, `token_count`, `size_category`, `step_range`).
- **Keywords Section**: Mapping of trigger words to steering filenames for context-relevant file loading.
- **Languages and Deployment Sections**: Mappings of language names or deployment targets to steering filenames.
- **File Metadata Section**: Each key is a steering filename, each value contains `token_count` (integer, characters ÷ 4) and `size_category` ("small", "medium", or "large").
- **Budget Section**: `total_tokens`, `reference_window`, `warn_threshold_pct`, `critical_threshold_pct`, `split_threshold_tokens`.
- **Complete Example**: A valid steering index with one simple module, one split module with phases, keyword entries, language entry, deployment entry, file_metadata entries, and budget section.
- **Read By**: The agent (module steering selection, keyword lookup, context budget tracking), `validate_power.py`, `measure_steering.py --check`, `lint_steering.py`.
- **Written By**: `measure_steering.py` (updates file_metadata and budget), `split_steering.py` (adds phase entries), maintainers (manual edits to modules, keywords, languages, deployment).

**Source of truth**: `steering-index.yaml` (actual structure), `measure_steering.py`, `lint_steering.py`, `split_steering.py`.

### Component 4: README.md Update

**Purpose**: Add entries for the three new guides to the existing `docs/guides/README.md`.

**Changes**:
- Add entries under the "Reference Documentation" section with Markdown links, bold titles, and 2–3 line descriptions.
- Add the three filenames to the Documentation Structure tree under `guides/`.

## Data Models

No runtime data models are introduced. The feature documents existing data models:

### Progress File (JSON)

```json
{
  "modules_completed": [1, 2, 3],
  "current_module": 4,
  "current_step": 3,
  "step_history": {
    "1": { "last_completed_step": 10, "updated_at": "2026-04-20T14:30:00+00:00" }
  },
  "data_sources": ["CUSTOMERS"],
  "database_type": "sqlite",
  "language": "python"
}
```

### Data Source Registry (YAML)

```yaml
version: "2"
sources:
  CUSTOMERS:
    name: Customer CRM Export
    file_path: data/raw/customers.csv
    format: csv
    record_count: 5000
    file_size_bytes: 1048576
    quality_score: 85
    mapping_status: complete
    load_status: loaded
    test_load_status: complete
    test_entity_count: 4800
    added_at: "2026-04-15T10:00:00Z"
    updated_at: "2026-04-18T14:30:00Z"
    issues: []
```

### Steering Index (YAML)

Top-level keys: `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget`. Structure documented in Component 3 above.

## Error Handling

Not applicable. This feature produces static Markdown files with no runtime behavior. Errors in the documentation content are prevented by:

- Deriving field definitions directly from the source code (`progress_utils.py`, `data_sources.py`)
- Deriving enum values from the script constants (`VALID_FORMATS`, `VALID_MAPPING_STATUSES`, etc.)
- Using the actual `steering-index.yaml` as the reference for the steering index guide
- Following the existing guide style established in `QUALITY_SCORING_METHODOLOGY.md`

## Testing Strategy

**Property-based testing does not apply to this feature.** The deliverables are static Markdown documentation files — there are no functions, data transformations, parsers, or business logic to test with PBT. The feature produces no executable code.

**Verification approach**:

- **Manual review**: Each guide is reviewed against the requirements acceptance criteria to confirm all required sections, fields, and examples are present.
- **Existing CI validation**: The `validate_commonmark.py` script in CI validates Markdown formatting for all files in the repository, which will cover the new guides.
- **Cross-reference checks**: `validate_power.py` performs cross-reference validation that can catch broken internal links.
- **Completeness check**: Verify the README.md update includes all three new guides in both the listing and the documentation structure tree.
