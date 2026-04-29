"""Unit and integration tests for registry schema versioning.

Feature: registry-schema-versioning
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_CHAIN,
    apply_migrations,
    main,
    migrate_v1_to_v2,
    parse_registry_yaml,
    serialize_registry_yaml,
    validate_registry,
)


# ---------------------------------------------------------------------------
# Sample v1 registry YAML for tests
# ---------------------------------------------------------------------------

V1_REGISTRY_YAML = """\
version: "1"
sources:
  CUSTOMERS:
    name: Customer Records
    file_path: data/customers.csv
    format: csv
    record_count: 1000
    file_size_bytes: 50000
    quality_score: 85
    mapping_status: complete
    load_status: loaded
    added_at: 2024-01-15
    updated_at: 2024-01-20
  WATCHLIST:
    name: Watchlist Entries
    file_path: data/watchlist.json
    format: json
    record_count: 500
    file_size_bytes: 25000
    quality_score: 90
    mapping_status: complete
    load_status: not_loaded
    added_at: 2024-02-01
    updated_at: 2024-02-10
    issues:
      - "Missing phone numbers"
"""

V2_REGISTRY_YAML = """\
version: "2"
sources:
  CUSTOMERS:
    name: Customer Records
    file_path: data/customers.csv
    format: csv
    record_count: 1000
    file_size_bytes: 50000
    quality_score: 85
    mapping_status: complete
    load_status: loaded
    test_load_status: complete
    test_entity_count: 950
    added_at: 2024-01-15
    updated_at: 2024-01-20
"""


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


class TestCurrentSchemaVersionConstant:
    """Verify CURRENT_SCHEMA_VERSION constant (Req 1.1)."""

    def test_value_is_2(self):
        assert CURRENT_SCHEMA_VERSION == "2"

    def test_is_string(self):
        assert isinstance(CURRENT_SCHEMA_VERSION, str)


class TestNoHardcodedVersionComparisons:
    """Verify no hardcoded '1' in version comparison logic (Req 1.2).

    Parses the AST of data_sources.py and checks that validate_registry
    does not compare version against a literal "1" string without also
    referencing CURRENT_SCHEMA_VERSION.
    """

    def test_validate_registry_uses_constant(self):
        source_path = Path(_SCRIPTS_DIR) / "data_sources.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Find the validate_registry function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "validate_registry":
                # Check that the function body doesn't have a standalone
                # comparison like `str(version) != "1"` without also
                # mentioning CURRENT_SCHEMA_VERSION or "2"
                func_source = ast.get_source_segment(source, node)
                assert func_source is not None
                # The version check should reference CURRENT_SCHEMA_VERSION
                assert "CURRENT_SCHEMA_VERSION" in func_source, (
                    "validate_registry should use CURRENT_SCHEMA_VERSION "
                    "instead of hardcoded version strings"
                )
                break


class TestMigrateV1ToV2:
    """Unit tests for migrate_v1_to_v2 function (Req 2)."""

    def test_upgrades_version(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        result = migrate_v1_to_v2(raw)
        assert result["version"] == "2"

    def test_adds_missing_fields(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        result = migrate_v1_to_v2(raw)
        for key, entry in result["sources"].items():
            assert "test_load_status" in entry, f"{key}: missing test_load_status"
            assert "test_entity_count" in entry, f"{key}: missing test_entity_count"
            assert entry["test_load_status"] is None
            assert entry["test_entity_count"] is None

    def test_preserves_existing_fields(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        original_customers = dict(raw["sources"]["CUSTOMERS"])
        result = migrate_v1_to_v2(raw)
        for field, value in original_customers.items():
            assert result["sources"]["CUSTOMERS"][field] == value

    def test_preserves_issues(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        result = migrate_v1_to_v2(raw)
        assert result["sources"]["WATCHLIST"]["issues"] == ["Missing phone numbers"]

    def test_preserves_existing_test_fields(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        # Manually set version to "1" to test migration preserves existing values
        raw["version"] = "1"
        result = migrate_v1_to_v2(raw)
        assert result["sources"]["CUSTOMERS"]["test_load_status"] == "complete"
        assert result["sources"]["CUSTOMERS"]["test_entity_count"] == 950


class TestApplyMigrations:
    """Unit tests for apply_migrations function (Req 3)."""

    def test_v1_migrated_to_current(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        result = apply_migrations(raw)
        assert result["version"] == CURRENT_SCHEMA_VERSION

    def test_current_version_unchanged(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        result = apply_migrations(raw)
        assert result["version"] == CURRENT_SCHEMA_VERSION
        assert result["sources"]["CUSTOMERS"]["test_load_status"] == "complete"

    def test_unrecognized_version_raises(self):
        raw = {"version": "99", "sources": {}}
        with pytest.raises(ValueError, match="Unrecognized schema version"):
            apply_migrations(raw)


class TestValidateRegistry:
    """Unit tests for updated validate_registry (Req 5)."""

    def test_accepts_v2(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        errors = validate_registry(raw)
        assert errors == []

    def test_accepts_v1(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        errors = validate_registry(raw)
        assert errors == []

    def test_accepts_migrated_v1(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        migrated = migrate_v1_to_v2(raw)
        errors = validate_registry(migrated)
        assert errors == []

    def test_rejects_invalid_test_load_status(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        raw["sources"]["CUSTOMERS"]["test_load_status"] = "invalid"
        errors = validate_registry(raw)
        assert any("test_load_status" in e for e in errors)

    def test_rejects_negative_test_entity_count(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        raw["sources"]["CUSTOMERS"]["test_entity_count"] = -5
        errors = validate_registry(raw)
        assert any("test_entity_count" in e for e in errors)

    def test_accepts_null_test_fields(self):
        raw = parse_registry_yaml(V2_REGISTRY_YAML)
        raw["sources"]["CUSTOMERS"]["test_load_status"] = None
        raw["sources"]["CUSTOMERS"]["test_entity_count"] = None
        errors = validate_registry(raw)
        assert errors == []

    def test_accepts_absent_test_fields(self):
        raw = parse_registry_yaml(V1_REGISTRY_YAML)
        # v1 entries don't have test fields — should still validate
        errors = validate_registry(raw)
        assert errors == []


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestCLIMigrateFlag:
    """Integration tests for --migrate CLI flag (Req 4)."""

    def test_migrate_writes_file(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        original_content = registry_file.read_text(encoding="utf-8")

        # Run with --migrate
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--migrate"])
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0
        new_content = registry_file.read_text(encoding="utf-8")
        assert new_content != original_content
        # Verify the written file is v2
        parsed = parse_registry_yaml(new_content)
        assert parsed["version"] == "2"

    def test_summary_does_not_modify_file(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        original_content = registry_file.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--summary"])
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0
        assert registry_file.read_text(encoding="utf-8") == original_content

    def test_default_table_does_not_modify_file(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        original_content = registry_file.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main([])
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0
        assert registry_file.read_text(encoding="utf-8") == original_content

    def test_detail_does_not_modify_file(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        original_content = registry_file.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--detail", "CUSTOMERS"])
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0
        assert registry_file.read_text(encoding="utf-8") == original_content


class TestCLIWithV1Registry:
    """Integration: full CLI run with v1 registry (Req 4)."""

    def test_summary_with_v1_succeeds(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            exit_code = main(["--summary"])
        finally:
            os.chdir(old_cwd)

        assert exit_code == 0

    def test_migrate_then_summary(self, tmp_path):
        registry_file = tmp_path / "config" / "data_sources.yaml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(V1_REGISTRY_YAML, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # First migrate
            exit_code = main(["--migrate"])
            assert exit_code == 0
            # Then summary on the migrated file
            exit_code = main(["--summary"])
            assert exit_code == 0
        finally:
            os.chdir(old_cwd)

        # Verify file is now v2
        parsed = parse_registry_yaml(
            registry_file.read_text(encoding="utf-8")
        )
        assert parsed["version"] == "2"
        # Verify all entries have the new fields
        for key, entry in parsed["sources"].items():
            assert "test_load_status" in entry
            assert "test_entity_count" in entry
