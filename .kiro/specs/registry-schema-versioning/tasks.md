# Tasks

## Task 1: Add schema version constant and migration infrastructure

- [x] 1.1 Add `CURRENT_SCHEMA_VERSION = "2"` constant to `senzing-bootcamp/scripts/data_sources.py` near the existing constants section, and replace all hardcoded `"1"` version comparisons in `validate_registry` and any other version-checking logic with references to `CURRENT_SCHEMA_VERSION`
- [x] 1.2 Implement `migrate_v1_to_v2(raw: dict) -> dict` function that: (a) iterates over all entries in `raw["sources"]`, (b) adds `test_load_status: None` to entries missing it, (c) adds `test_entity_count: None` to entries missing it, (d) preserves all existing fields including `issues`, and (e) sets `raw["version"]` to `"2"` and returns the dict
- [x] 1.3 Implement `MIGRATION_CHAIN` dict mapping `{"1": migrate_v1_to_v2}` and `apply_migrations(raw: dict) -> dict` function that: (a) if version equals `CURRENT_SCHEMA_VERSION`, returns the dict unchanged, (b) sequentially applies migration functions from the chain until version reaches `CURRENT_SCHEMA_VERSION`, (c) raises `ValueError` for unrecognized versions not in the chain

## Task 2: Update load flow and validation for schema versioning

- [x] 2.1 Update the registry loading logic in `data_sources.py` to call `apply_migrations(raw)` after parsing YAML and before calling `validate_registry`, so that v1 registries are transparently upgraded in memory
- [x] 2.2 Update `validate_registry` to accept `version` values of `"1"` or `"2"` (using `CURRENT_SCHEMA_VERSION`), add validation for `test_entity_count` (must be non-negative integer or `None`), and ensure `test_load_status` and `test_entity_count` are treated as optional fields that pass validation when absent
- [x] 2.3 Add `--migrate` flag to the CLI `argparse` in `main()` that, when passed, writes the migrated registry back to disk using `serialize_registry_yaml` after successful migration and validation; ensure read-only operations (`--summary`, `--detail`, default table view) do not write to disk

## Task 3: Property-based tests for migration correctness

- [x] 3.1 Create `senzing-bootcamp/tests/test_schema_versioning_properties.py` with Hypothesis strategies for generating random valid v1 registry dicts (with random source entries containing all required fields, optional `test_load_status`/`test_entity_count`/`issues` fields, and valid enum values)
- [x] 3.2 PBT: Property 1 — Migration Version Upgrade: for any valid v1 registry dict, `migrate_v1_to_v2` produces a dict with version `"2"` (Req 2.1)
- [x] 3.3 PBT: Property 2 — Missing Fields Backfilled with Null: for any v1 registry where entries lack `test_load_status` or `test_entity_count`, migration adds both as `None` (Req 2.2, 2.3)
- [x] 3.4 PBT: Property 3 — Existing Fields Preserved: for any v1 registry, all original source entry fields (including `issues`) are unchanged after migration (Req 2.4, 2.5, 7.1, 7.3)
- [x] 3.5 PBT: Property 4 — Migration Chain Reaches Current Version: for any v1 registry, `apply_migrations` produces version equal to `CURRENT_SCHEMA_VERSION` (Req 3.2)
- [x] 3.6 PBT: Property 5 — Unrecognized Version Raises Error: for any version string not in chain and not equal to current, `apply_migrations` raises `ValueError` (Req 3.4)
- [x] 3.7 PBT: Property 6 — Migration Idempotence: for any v1 registry, migrate → serialize → migrate → serialize produces byte-identical output (Req 6.1, 6.2)
- [x] 3.8 PBT: Property 7 — Serialization Round-Trip After Migration: for any v1 registry, migrate → serialize → parse produces identical source data (Req 7.2)
- [x] 3.9 PBT: Property 8 — Validation Accepts Migrated Registries: for any v1 registry, `validate_registry` returns zero errors after migration (Req 5.1, 5.4)
- [x] 3.10 PBT: Property 9 — Validation Rejects Invalid Field Values: for any registry with invalid `test_load_status` or negative `test_entity_count`, `validate_registry` returns errors (Req 5.2, 5.3)

## Task 4: Example-based unit tests and integration tests

- [x] 4.1 Create `senzing-bootcamp/tests/test_schema_versioning_unit.py` with unit tests: (a) `CURRENT_SCHEMA_VERSION` equals `"2"`, (b) no hardcoded `"1"` in version comparison logic, (c) new registry creation sets version to `CURRENT_SCHEMA_VERSION`, (d) `--migrate` flag writes file to disk, (e) read-only operations don't modify file on disk
- [x] 4.2 Add integration test: full CLI run with a v1 registry file and `--summary` flag completes without error and does not modify the file; full CLI run with `--migrate` flag updates the file to v2
- [x] 4.3 Run all tests (`pytest senzing-bootcamp/tests/test_schema_versioning_properties.py senzing-bootcamp/tests/test_schema_versioning_unit.py`) and verify they pass
