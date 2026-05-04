# Tasks

## Task 1: Create registry parser, data structures, and validator

- [x] 1.1 Create `senzing-bootcamp/scripts/data_sources.py` with `RegistryEntry` and `Registry` dataclasses, including `by_load_status()`, `by_mapping_status()`, `low_quality_sources()`, `average_quality()`, and `total_records()` methods
- [x] 1.2 Implement `parse_registry_yaml(content: str) -> dict` that parses the restricted YAML subset (version string, sources mapping with nested scalar fields and optional issues list) into a Python dict
- [x] 1.3 Implement `serialize_registry_yaml(data: dict) -> str` that serializes a registry dict back to valid YAML string preserving field order and null representation
- [x] 1.4 Implement `validate_registry(raw: dict) -> list[str]` that checks version is `"1"`, sources keys match `^[A-Z][A-Z0-9_]*$`, each entry has all required fields, and enum fields (`format`, `mapping_status`, `load_status`) contain only valid values — returning a list of specific error strings

## Task 2: Implement rendering functions

- [x] 2.1 Implement `render_table(registry: Registry) -> str` that produces a formatted table with DATA_SOURCE, record count, quality score, mapping status, and load status columns — showing `-` for null values and `⚠` for low-quality sources
- [x] 2.2 Implement `render_detail(entry: RegistryEntry) -> str` that displays all fields for a single entry including optional `issues` list
- [x] 2.3 Implement `render_summary(registry: Registry) -> str` that displays total sources, counts by mapping status, counts by load status, average quality score (when available), and total record count

## Task 3: Implement recommendation engine and status integration

- [x] 3.1 Implement `recommend_actions(registry: Registry) -> list[str]` that generates warnings for sources with quality below 70 and `not_loaded` status, warnings for sources with `pending` mapping and `not_loaded` status, and a recommended load order sorted by quality score descending
- [x] 3.2 Implement `render_data_sources_section(registry_path: str) -> str | None` that reads the registry file, validates it, and returns a formatted "Data Sources" section string with load status counts and quality warnings — returning `None` if the file does not exist
- [x] 3.3 Integrate `render_data_sources_section` into `senzing-bootcamp/scripts/status.py` by calling it after the "Project Health" section and printing the result when non-None

## Task 4: Implement CLI entry point

- [x] 4.1 Implement `main(argv)` in `data_sources.py` with argparse supporting no-args (table view), `--detail <DATA_SOURCE>`, and `--summary` — handling missing registry (exit 0 with message), validation errors (exit 1), and unknown DATA_SOURCE (exit 1 listing available names)

## Task 5: Update steering files for registry maintenance

- [x] 5.1 Update `senzing-bootcamp/steering/module-04-data-collection.md` to add agent instructions for creating/updating Registry_Entries when data source files are collected — including creating the registry file if it doesn't exist
- [x] 5.2 Update `senzing-bootcamp/steering/module-05-data-quality-mapping.md` to add agent instructions for updating `quality_score` after Phase 1 assessment (with `issues` list when below 70) and `mapping_status` during Phase 2 mapping workflow
- [x] 5.3 Update `senzing-bootcamp/steering/module-06-single-source.md` to add agent instructions for updating `load_status` to `loading` when loading begins, `loaded` on success (with updated `record_count`), and `failed` on failure (with `issues`)
- [x] 5.4 Update `senzing-bootcamp/steering/module-07-multi-source.md` to add agent instructions for reading the registry to determine load order (quality-first) and updating `load_status` for each source during orchestration

## Task 6: Update POWER.md documentation

- [x] 6.1 Add data source registry mention to the "What's New" section of `senzing-bootcamp/POWER.md`
- [x] 6.2 Add `data_sources.py` to the "Useful Commands" section with usage examples for default view, `--detail`, and `--summary`
- [x] 6.3 Add `config/data_sources.yaml` description to the "Project Directory Structure" section

## Task 7: Property-based tests

- [x] 7.1 Create `senzing-bootcamp/scripts/test_data_sources.py` with Hypothesis strategies for `RegistryEntry`, `Registry`, valid/invalid registry dicts, DATA_SOURCE key strings, and enum field values
- [x] 7.2 PBT: Property 1 — YAML round-trip preserves registry data (Req 1.1, 1.2, 1.3, 1.4)
- [x] 7.3 PBT: Property 2 — Registry validation accepts valid registries and rejects invalid ones (Req 1.2, 1.3, 1.4, 1.6, 11.1, 11.2, 11.3, 11.4)
- [x] 7.4 PBT: Property 3 — Table rendering contains all source data (Req 6.1, 7.2)
- [x] 7.5 PBT: Property 4 — Detail rendering contains all entry fields (Req 7.3)
- [x] 7.6 PBT: Property 5 — Summary statistics are correctly computed (Req 7.4)
- [x] 7.7 PBT: Property 6 — Recommendations correctly identify issues and load order (Req 6.2, 6.3, 6.4)
- [x] 7.8 PBT: Property 7 — Status integration section contains correct counts and warnings (Req 8.1, 8.2)

## Task 8: Unit tests for edge cases and integration points

- [x] 8.1 Unit test: CLI argument parsing — no args, --detail with valid/invalid source, --summary, --detail with no argument (Req 7.1–7.6)
- [x] 8.2 Unit test: missing registry file → message + exit 0; missing registry in status.py → no section (Req 7.5, 8.3)
- [x] 8.3 Unit test: validation error → descriptive message + exit 1; empty sources → empty table / zero summary (Req 11.4)
- [x] 8.4 Unit test: default entry values (null quality, pending mapping, not_loaded); issues field absent treated as empty (Req 1.5)
