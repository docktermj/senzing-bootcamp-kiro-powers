# Implementation Plan: SQLite to PostgreSQL Database Migration Guide

## Overview

Create a comprehensive database migration guide as documentation within the senzing-bootcamp power. The implementation involves creating the main guide document, adding cross-references from existing steering and guide files, extending the preferences schema, and writing a structural validation test suite. All paths are relative to `senzing-bootcamp/`.

## Tasks

- [x] 1. Create the main migration guide document
  - [x] 1.1 Create `docs/guides/DATABASE_MIGRATION.md` with all required sections
    - Create the guide with these sections: Overview, Prerequisites, Why Migrate (SQLite limitations vs PostgreSQL advantages), Step 1: Create PostgreSQL Database, Step 2: Initialize Senzing Schema (with `sdk_guide` MCP tool block), Step 3: Re-load Data (with `search_docs` MCP tool block), Step 4: Verify Migration, Rollback, Update Preferences, Related Resources
    - Include agent instruction blocks calling `sdk_guide(topic='configure', language='<chosen_language>')` for PostgreSQL engine configuration
    - Include agent instruction blocks calling `search_docs(query='PostgreSQL database setup', version='current')` for authoritative guidance
    - Explain SQLite limitations: single-writer, no network access, performance ceiling at ~100K records
    - Explain PostgreSQL advantages: concurrent access, production-grade, required for multi-process loading
    - Document re-loading from existing Senzing JSON files (NOT re-mapping)
    - Include rollback section explaining SQLite database remains intact
    - Document `database_type` preference field with valid values (`sqlite`, `postgresql`)
    - Follow the same format as existing guides (no YAML frontmatter)
    - _Requirements: 1, 2, 3, 4, 5, 8, 9, 10_

- [x] 2. Add cross-references and index entries
  - [x] 2.1 Add cross-reference from Module 8 Phase C steering file
    - Add a callout in Step 8 (Database Tuning) of `steering/module-08-phaseC-optimization.md` directing users to the migration guide when SQLite performance is insufficient
    - Use relative path link: `../../docs/guides/DATABASE_MIGRATION.md`
    - _Requirements: 6_

  - [x] 2.2 Add entry to `docs/guides/README.md`
    - Add DATABASE_MIGRATION.md entry in the Reference Documentation section
    - Include brief description: step-by-step SQLite to PostgreSQL migration, prerequisites, schema initialization, data re-loading, verification, rollback path, MCP tool integration
    - _Requirements: 7_

- [x] 3. Extend preferences configuration schema
  - [x] 3.1 Add `database_type` field to `config/bootcamp_preferences.yaml`
    - Add `database_type: sqlite` as the default value
    - Place it logically near other infrastructure fields (`deployment_target`, `cloud_provider`)
    - Valid values: `sqlite` (default), `postgresql`
    - _Requirements: 10_

- [x] 4. Checkpoint - Verify documentation artifacts
  - Ensure all documentation files are created and cross-references are correct, ask the user if questions arise.

- [x] 5. Create test suite for structural validation
  - [x] 5.1 Create `tests/test_database_migration_guide.py` with full test class
    - Create `TestDatabaseMigrationGuide` class with pytest
    - Use `Path(__file__).resolve()` for path constants at module level
    - Use only stdlib (`pathlib`, `re`) — no external dependencies
    - Implement these test methods:
      - `test_guide_file_exists` — assert guide exists at expected path (Req 1)
      - `test_required_sections_present` — extract `## ` headings, verify all required sections (Req 2)
      - `test_sqlite_limitations_explained` — case-insensitive substring checks for key terms (Req 3)
      - `test_postgresql_advantages_explained` — case-insensitive substring checks for PostgreSQL benefits (Req 3)
      - `test_sdk_guide_mcp_reference` — verify `sdk_guide` with `configure` topic appears (Req 4)
      - `test_search_docs_mcp_reference` — verify `search_docs` with PostgreSQL query appears (Req 5)
      - `test_module8_cross_reference` — read Phase C file, verify DATABASE_MIGRATION reference (Req 6)
      - `test_guides_readme_entry` — read README.md, verify DATABASE_MIGRATION entry (Req 7)
      - `test_no_remapping_instructions` — verify guide does NOT instruct re-mapping; DOES mention re-loading from JSON (Req 8)
      - `test_rollback_section_present` — verify rollback section exists and mentions SQLite preservation (Req 9)
      - `test_database_type_preference_documented` — verify guide mentions `database_type` field and valid values (Req 10)
    - Each test method should have a docstring referencing the requirement it validates
    - Use descriptive assertion messages
    - _Requirements: 11_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No property-based tests are needed — this feature creates static documentation with structural validation only
- All paths are relative to `senzing-bootcamp/` (the distributed power root)
- The guide follows the same format as existing guides like `PERFORMANCE_BASELINES.md` (no YAML frontmatter)
- Tests use the same pattern as `test_entity_resolution_intro_structure.py` and `test_mcp_tool_decision_tree.py`
- Python 3.11+ stdlib only for test code (pathlib, re); pytest as test runner
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["5.1"] }
  ]
}
```
