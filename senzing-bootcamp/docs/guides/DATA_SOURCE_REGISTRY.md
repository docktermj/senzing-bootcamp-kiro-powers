# Data Source Registry

The file `config/data_sources.yaml` is the bootcamp's data source registry. It tracks every data source you register during the bootcamp — file path, format, record count, quality score, mapping status, and load status. The agent creates this file when you add your first data source in Module 4 or 5, and updates it as you progress through data quality assessment, mapping, and loading. Scripts like `data_sources.py` read the registry to show you a dashboard of your sources and recommend next steps. If you want to understand what each field means, what values are valid, or how the registry evolves as you work through the bootcamp, this is the reference.

## Top-Level Structure

The registry has two top-level fields:

| Field | YAML Type | Description |
|-------|-----------|-------------|
| `version` | string | Schema version identifier. Currently `"2"`. Used to trigger automatic migrations when the schema evolves. |
| `sources` | mapping | A mapping of DATA_SOURCE keys to entry objects. Each key identifies a registered data source. |

**Key constraint:** Every DATA_SOURCE key in the `sources` mapping must match the pattern `^[A-Z][A-Z0-9_]*$` — uppercase letters, digits, and underscores only, starting with a letter. Examples: `CUSTOMERS`, `WATCHLIST`, `VENDOR_CRM`. Keys like `customers`, `3PD_DATA`, or `my-source` are rejected by validation.

## Entry Field Definitions

Each entry under `sources` contains up to 13 fields describing the data source:

| Field | YAML Type | Required / Optional | Valid Values | Description |
|-------|-----------|---------------------|--------------|-------------|
| `name` | string | Required | Any descriptive string | Human-readable name for the data source (e.g. `"Customer CRM Export"`) |
| `file_path` | string | Required | Relative file path | Path to the source data file relative to the workspace root (e.g. `"data/raw/customers.csv"`) |
| `format` | string | Required | `csv`, `json`, `jsonl`, `xlsx`, `parquet`, `xml`, `other` | File format of the source data; see [Enum Values](#enum-values) |
| `record_count` | integer or null | Required | Non-negative integer or `null` | Number of records in the source file; `null` if not yet counted |
| `file_size_bytes` | integer or null | Optional | Non-negative integer or `null` | Size of the source file in bytes; `null` or omitted if not measured |
| `quality_score` | integer or null | Required | `0` through `100`, or `null` | Quality score assigned by Module 5 assessment; `null` before assessment |
| `mapping_status` | string | Required | `pending`, `in_progress`, `complete` | Current state of the data mapping process; see [Enum Values](#enum-values) |
| `load_status` | string | Required | `not_loaded`, `loading`, `loaded`, `failed` | Current state of loading into the Senzing engine; see [Enum Values](#enum-values) |
| `test_load_status` | string or null | Optional | `complete`, `skipped`, or `null` | Result of the test load step; `null` or omitted if test load has not been run |
| `test_entity_count` | integer or null | Optional | Non-negative integer or `null` | Number of resolved entities from the test load; `null` if not yet available |
| `added_at` | string | Required | ISO 8601 timestamp | When the data source was first registered (e.g. `"2026-04-15T10:00:00Z"`) |
| `updated_at` | string | Required | ISO 8601 timestamp | When the entry was last modified (e.g. `"2026-04-18T14:30:00Z"`) |
| `issues` | list of strings or null | Optional | List of issue descriptions, or `null` | Known problems with this data source; `null` or omitted if no issues |

## Enum Values

Four fields use constrained value sets. The validation in `data_sources.py` rejects any value not in these sets.

**`format`** — the file format of the source data:

| Value | Meaning |
|-------|---------|
| `csv` | Comma-separated values |
| `json` | JSON file (single object or array) |
| `jsonl` | JSON Lines (one JSON object per line) |
| `xlsx` | Microsoft Excel spreadsheet |
| `parquet` | Apache Parquet columnar format |
| `xml` | XML document |
| `other` | Any format not listed above |

**`mapping_status`** — tracks progress through the data mapping phase:

| Value | Meaning |
|-------|---------|
| `pending` | Mapping has not started |
| `in_progress` | Mapping is underway but not yet finished |
| `complete` | Mapping is finished and ready for loading |

**`load_status`** — tracks progress through the Senzing engine loading phase:

| Value | Meaning |
|-------|---------|
| `not_loaded` | Data has not been loaded into the engine |
| `loading` | Load is currently in progress |
| `loaded` | Data has been successfully loaded |
| `failed` | Load was attempted but failed |

**`test_load_status`** — result of the test load step (added in schema version 2):

| Value | Meaning |
|-------|---------|
| `complete` | Test load finished successfully |
| `skipped` | Test load was skipped |

## Schema Migration

The registry schema has evolved over time. Version `"1"` registries are automatically migrated to version `"2"` when read by `data_sources.py`.

**What changed from version 1 to version 2:**

- Two new optional fields were added: `test_load_status` and `test_entity_count`.
- Existing entries that lack these fields get them backfilled as `null` during migration.

**How to migrate:**

Run `data_sources.py --migrate` to read the registry, apply the migration chain, and write the updated file back to disk. The migration is idempotent — running it on a version `"2"` registry has no effect.

**Migration behavior (`migrate_v1_to_v2`):**

1. For each source entry, adds `test_load_status: null` if the field is missing.
2. For each source entry, adds `test_entity_count: null` if the field is missing.
3. Sets the top-level `version` to `"2"`.
4. Preserves all existing fields including `issues`.

## Complete Example

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
    updated_at: "2026-04-20T16:45:00Z"
    issues: []
  WATCHLIST:
    name: Government Watchlist
    file_path: data/raw/watchlist.jsonl
    format: jsonl
    record_count: 12000
    file_size_bytes: null
    quality_score: 62
    mapping_status: pending
    load_status: not_loaded
    test_load_status: null
    test_entity_count: null
    added_at: "2026-04-18T09:30:00Z"
    updated_at: "2026-04-18T09:30:00Z"
    issues:
      - "Quality score below 70% threshold"
      - "Mapping not started"
```

This example shows two data sources in different states. `CUSTOMERS` has been fully mapped, loaded, and test-loaded with 4800 resolved entities. `WATCHLIST` was recently registered but has a low quality score and has not started mapping — the `issues` list flags both problems.

## Read By

- `data_sources.py` — provides CLI views (`--detail`, `--summary`, default table) and generates recommendations based on quality scores, mapping status, and load status
- `status.py` — reads the registry via `render_data_sources_section` to include data source load status counts and quality warnings in the bootcamp dashboard
- The agent during Modules 4–7 — references the registry to determine which data sources are registered, their current status, and what actions to recommend next

## Written By

- The agent during data source registration (Modules 4–5) — creates the registry file and adds entries as the bootcamper registers data sources
- `data_sources.py --migrate` — applies schema migrations and writes the updated registry back to disk
- The agent during loading status updates (Module 6) — updates `load_status`, `test_load_status`, `test_entity_count`, and `updated_at` as data sources are loaded into the Senzing engine
