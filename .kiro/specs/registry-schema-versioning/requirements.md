# Requirements Document

## Introduction

The data source registry (`config/data_sources.yaml`) was recently extended with `test_load_status` and `test_entity_count` fields. The registry has a `version` field (currently `"1"`) but no migration logic — if more fields are added later, older registries created before the change will lack them, causing validation failures or silent data loss. This feature adds schema versioning with migration: bump the schema to version `"2"` when new fields are added, and provide a migration function that upgrades version `"1"` registries to version `"2"` by adding missing fields with sensible default values.

## Glossary

- **Registry**: The `config/data_sources.yaml` file parsed and managed by `scripts/data_sources.py`
- **Registry_Module**: The `scripts/data_sources.py` Python module that contains parsing, validation, serialization, and CLI logic for the Registry
- **Schema_Version**: The `version` field at the top level of the Registry, a string representing the schema revision (e.g., `"1"`, `"2"`)
- **Migration_Function**: A callable in the Registry_Module that takes a raw parsed registry dict at one Schema_Version and returns a dict upgraded to the next Schema_Version
- **Migration_Chain**: The ordered sequence of Migration_Functions applied to bring a Registry from any older Schema_Version to the current Schema_Version
- **Current_Schema_Version**: The latest Schema_Version that the Registry_Module supports (will be `"2"` after this feature)
- **Source_Entry**: A single data source record within the `sources` mapping of the Registry
- **Default_Value**: The value assigned to a missing field during migration (e.g., `null` for optional fields)

## Requirements

### Requirement 1: Schema Version Constant

**User Story:** As a developer, I want a single constant defining the current schema version, so that version checks and migrations reference one authoritative value.

#### Acceptance Criteria

1. THE Registry_Module SHALL define a module-level constant `CURRENT_SCHEMA_VERSION` with the string value `"2"`
2. THE Registry_Module SHALL use `CURRENT_SCHEMA_VERSION` in all version comparison logic instead of hardcoded string literals
3. WHEN a new Registry is created by the agent, THE Registry_Module SHALL set the `version` field to `CURRENT_SCHEMA_VERSION`

### Requirement 2: Version 1 to Version 2 Migration

**User Story:** As a bootcamp user, I want my existing version `"1"` registry to be automatically upgraded to version `"2"` when the script runs, so that I do not lose data or encounter validation errors.

#### Acceptance Criteria

1. THE Registry_Module SHALL provide a Migration_Function named `migrate_v1_to_v2` that accepts a raw registry dict with `version` equal to `"1"` and returns a dict with `version` equal to `"2"`
2. WHEN a Source_Entry in a version `"1"` registry lacks the `test_load_status` field, THE `migrate_v1_to_v2` function SHALL add `test_load_status` with a Default_Value of `null`
3. WHEN a Source_Entry in a version `"1"` registry lacks the `test_entity_count` field, THE `migrate_v1_to_v2` function SHALL add `test_entity_count` with a Default_Value of `null`
4. WHEN a Source_Entry in a version `"1"` registry already contains `test_load_status` or `test_entity_count`, THE `migrate_v1_to_v2` function SHALL preserve the existing values
5. THE `migrate_v1_to_v2` function SHALL preserve all other existing fields in each Source_Entry without modification

### Requirement 3: Migration Chain Execution

**User Story:** As a developer, I want migrations to chain automatically from any older version to the current version, so that adding future versions (3, 4, ...) requires only writing the incremental migration.

#### Acceptance Criteria

1. THE Registry_Module SHALL maintain an ordered Migration_Chain mapping each Schema_Version to the Migration_Function that upgrades it to the next version (e.g., `{"1": migrate_v1_to_v2}`)
2. WHEN a Registry is loaded with a Schema_Version older than Current_Schema_Version, THE Registry_Module SHALL apply each Migration_Function in the Migration_Chain sequentially until the version equals Current_Schema_Version
3. WHEN a Registry is loaded with a Schema_Version equal to Current_Schema_Version, THE Registry_Module SHALL skip migration entirely
4. IF a Registry is loaded with a Schema_Version that is not present in the Migration_Chain and is not equal to Current_Schema_Version, THEN THE Registry_Module SHALL report an error identifying the unrecognized version

### Requirement 4: Automatic Migration on Load

**User Story:** As a bootcamp user, I want the registry to be migrated transparently when I run any data-sources command, so that I do not need to run a separate migration step.

#### Acceptance Criteria

1. WHEN the Registry_Module loads a Registry file, THE Registry_Module SHALL check the Schema_Version before validation
2. WHEN the Schema_Version is older than Current_Schema_Version, THE Registry_Module SHALL apply the Migration_Chain to upgrade the raw dict in memory before proceeding to validation
3. THE Registry_Module SHALL not write the migrated Registry back to disk during a read-only operation (e.g., `--summary`, `--detail`, default table view)
4. WHEN the `--migrate` flag is passed, THE Registry_Module SHALL write the migrated Registry back to disk after successful migration and validation

### Requirement 5: Validation Update

**User Story:** As a developer, I want the validator to accept the new schema version and validate the new fields, so that version `"2"` registries are checked correctly.

#### Acceptance Criteria

1. THE `validate_registry` function SHALL accept `version` values of `"1"` or `"2"` (after migration, only `"2"` registries reach validation)
2. WHEN a Source_Entry contains a `test_load_status` field, THE `validate_registry` function SHALL verify the value is one of the valid test load statuses (`complete`, `skipped`) or `null`
3. WHEN a Source_Entry contains a `test_entity_count` field, THE `validate_registry` function SHALL verify the value is a non-negative integer or `null`
4. THE `validate_registry` function SHALL accept registries where `test_load_status` and `test_entity_count` are absent (they are optional fields)

### Requirement 6: Migration Idempotence

**User Story:** As a developer, I want running migration on an already-migrated registry to produce no changes, so that repeated runs are safe.

#### Acceptance Criteria

1. WHEN the `migrate_v1_to_v2` function is applied to a registry that already has `version` equal to `"2"`, THE Migration_Chain SHALL skip the function and return the dict unchanged
2. FOR ALL valid version `"1"` registries, migrating to version `"2"` and then migrating again SHALL produce a byte-identical serialized output (idempotent migration)

### Requirement 7: Round-Trip Preservation

**User Story:** As a developer, I want migration to preserve all existing data so that no information is lost during the upgrade.

#### Acceptance Criteria

1. FOR ALL valid version `"1"` registries, THE `migrate_v1_to_v2` function SHALL preserve every field that existed in the original Source_Entry
2. FOR ALL valid version `"1"` registries, serializing the migrated registry and then parsing it back SHALL produce a Registry with identical source data (round-trip property)
3. THE `migrate_v1_to_v2` function SHALL preserve the `issues` list in each Source_Entry without modification
