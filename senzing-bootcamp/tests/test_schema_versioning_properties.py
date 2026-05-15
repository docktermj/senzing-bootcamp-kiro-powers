"""Property-based tests for registry schema versioning using Hypothesis.

Feature: registry-schema-versioning
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_CHAIN,
    VALID_FORMATS,
    VALID_LOAD_STATUSES,
    VALID_MAPPING_STATUSES,
    VALID_TEST_LOAD_STATUSES,
    apply_migrations,
    migrate_v1_to_v2,
    parse_registry_yaml,
    serialize_registry_yaml,
    validate_registry,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_data_source_key():
    """Generate valid DATA_SOURCE keys (uppercase letters/digits/underscores)."""
    return st.from_regex(r"[A-Z][A-Z0-9_]{1,10}", fullmatch=True)


def st_date_string():
    """Generate date-like strings."""
    return st.from_regex(r"2024-\d{2}-\d{2}", fullmatch=True)


def st_file_path():
    """Generate plausible file paths."""
    return st.from_regex(r"data/[a-z_]{3,10}\.[a-z]{2,4}", fullmatch=True)


def st_source_entry_v1(
    include_test_load_status: bool | None = None,
    include_test_entity_count: bool | None = None,
    include_issues: bool | None = None,
):
    """Generate a valid v1 source entry dict.

    Args:
        include_test_load_status: If True, always include; if False, never; if None, random.
        include_test_entity_count: If True, always include; if False, never; if None, random.
        include_issues: If True, always include; if False, never; if None, random.
    """

    @st.composite
    def _build(draw):
        entry = {
            "name": draw(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz ")),
            "file_path": draw(st_file_path()),
            "format": draw(st.sampled_from(sorted(VALID_FORMATS))),
            "record_count": draw(st.integers(min_value=0, max_value=100000)),
            "file_size_bytes": draw(st.integers(min_value=0, max_value=10000000)),
            "quality_score": draw(st.integers(min_value=0, max_value=100)),
            "mapping_status": draw(st.sampled_from(sorted(VALID_MAPPING_STATUSES))),
            "load_status": draw(st.sampled_from(sorted(VALID_LOAD_STATUSES))),
            "added_at": draw(st_date_string()),
            "updated_at": draw(st_date_string()),
        }

        do_tls = draw(st.booleans()) if include_test_load_status is None else include_test_load_status
        if do_tls:
            entry["test_load_status"] = draw(
                st.sampled_from([None] + sorted(VALID_TEST_LOAD_STATUSES))
            )

        do_tec = draw(st.booleans()) if include_test_entity_count is None else include_test_entity_count
        if do_tec:
            entry["test_entity_count"] = draw(
                st.one_of(st.none(), st.integers(min_value=0, max_value=100000))
            )

        do_issues = draw(st.booleans()) if include_issues is None else include_issues
        if do_issues:
            entry["issues"] = draw(
                st.lists(
                    st.text(min_size=1, max_size=40, alphabet="abcdefghijklmnopqrstuvwxyz "),
                    min_size=0,
                    max_size=3,
                )
            )

        return entry

    return _build()


def st_v1_registry(
    include_test_load_status: bool | None = None,
    include_test_entity_count: bool | None = None,
    include_issues: bool | None = None,
):
    """Generate a valid v1 registry dict with 1-5 source entries."""

    @st.composite
    def _build(draw):
        keys = draw(
            st.lists(st_data_source_key(), min_size=1, max_size=5, unique=True)
        )
        sources = {}
        for key in keys:
            sources[key] = draw(
                st_source_entry_v1(
                    include_test_load_status=include_test_load_status,
                    include_test_entity_count=include_test_entity_count,
                    include_issues=include_issues,
                )
            )
        return {"version": "1", "sources": sources}

    return _build()


# ---------------------------------------------------------------------------
# Property 1: Migration Version Upgrade
# ---------------------------------------------------------------------------


class TestProperty1MigrationVersionUpgrade:
    """Feature: registry-schema-versioning, Property 1: Migration Version Upgrade

    For any valid version "1" registry dict, applying migrate_v1_to_v2
    shall produce a dict with version equal to "2".

    **Validates: Requirements 2.1**
    """

    @given(registry=st_v1_registry())
    @settings(max_examples=10)
    def test_version_upgraded_to_2(self, registry):
        result = migrate_v1_to_v2(copy.deepcopy(registry))
        assert result["version"] == "2"


# ---------------------------------------------------------------------------
# Property 2: Missing Fields Backfilled with Null
# ---------------------------------------------------------------------------


class TestProperty2MissingFieldsBackfilled:
    """Feature: registry-schema-versioning, Property 2: Missing Fields Backfilled with Null

    For any valid version "1" registry dict where source entries lack
    test_load_status or test_entity_count, applying migrate_v1_to_v2
    shall add both fields with value None to every source entry that
    was missing them.

    **Validates: Requirements 2.2, 2.3**
    """

    @given(
        registry=st_v1_registry(
            include_test_load_status=False,
            include_test_entity_count=False,
        )
    )
    @settings(max_examples=10)
    def test_missing_fields_set_to_none(self, registry):
        result = migrate_v1_to_v2(copy.deepcopy(registry))
        for key, entry in result["sources"].items():
            assert "test_load_status" in entry, f"{key}: test_load_status not added"
            assert entry["test_load_status"] is None, f"{key}: test_load_status not None"
            assert "test_entity_count" in entry, f"{key}: test_entity_count not added"
            assert entry["test_entity_count"] is None, f"{key}: test_entity_count not None"


# ---------------------------------------------------------------------------
# Property 3: Existing Fields Preserved
# ---------------------------------------------------------------------------


class TestProperty3ExistingFieldsPreserved:
    """Feature: registry-schema-versioning, Property 3: Existing Fields Preserved

    For any valid version "1" registry dict, applying migrate_v1_to_v2
    shall preserve every field that existed in each original source entry
    (including issues, test_load_status, and test_entity_count if already
    present) without modification.

    **Validates: Requirements 2.4, 2.5, 7.1, 7.3**
    """

    @given(
        registry=st_v1_registry(
            include_test_load_status=True,
            include_test_entity_count=True,
            include_issues=True,
        )
    )
    @settings(max_examples=10)
    def test_existing_fields_unchanged(self, registry):
        original = copy.deepcopy(registry)
        result = migrate_v1_to_v2(copy.deepcopy(registry))
        for key in original["sources"]:
            orig_entry = original["sources"][key]
            migrated_entry = result["sources"][key]
            for field, value in orig_entry.items():
                assert field in migrated_entry, f"{key}: field {field!r} lost"
                assert migrated_entry[field] == value, (
                    f"{key}: field {field!r} changed from {value!r} "
                    f"to {migrated_entry[field]!r}"
                )


# ---------------------------------------------------------------------------
# Property 4: Migration Chain Reaches Current Version
# ---------------------------------------------------------------------------


class TestProperty4MigrationChainReachesCurrent:
    """Feature: registry-schema-versioning, Property 4: Migration Chain Reaches Current Version

    For any valid registry dict with a version present in the migration
    chain, applying apply_migrations shall produce a dict with version
    equal to CURRENT_SCHEMA_VERSION.

    **Validates: Requirements 3.2**
    """

    @given(registry=st_v1_registry())
    @settings(max_examples=10)
    def test_chain_reaches_current_version(self, registry):
        result = apply_migrations(copy.deepcopy(registry))
        assert result["version"] == CURRENT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Property 5: Unrecognized Version Raises Error
# ---------------------------------------------------------------------------


class TestProperty5UnrecognizedVersionError:
    """Feature: registry-schema-versioning, Property 5: Unrecognized Version Raises Error

    For any version string that is not in the migration chain and not
    equal to CURRENT_SCHEMA_VERSION, calling apply_migrations shall
    raise a ValueError.

    **Validates: Requirements 3.4**
    """

    @given(
        version=st.text(min_size=1, max_size=5, alphabet="0123456789abc")
    )
    @settings(max_examples=10)
    def test_unrecognized_version_raises(self, version):
        assume(version not in MIGRATION_CHAIN)
        assume(version != CURRENT_SCHEMA_VERSION)
        raw = {"version": version, "sources": {}}
        with pytest.raises(ValueError, match="Unrecognized schema version"):
            apply_migrations(raw)


# ---------------------------------------------------------------------------
# Property 6: Migration Idempotence
# ---------------------------------------------------------------------------


class TestProperty6MigrationIdempotence:
    """Feature: registry-schema-versioning, Property 6: Migration Idempotence

    For any valid version "1" registry dict, migrating to version "2",
    serializing, then migrating again shall produce a byte-identical
    serialized output.

    **Validates: Requirements 6.1, 6.2**
    """

    @given(registry=st_v1_registry())
    @settings(max_examples=10)
    def test_migration_is_idempotent(self, registry):
        # First migration + serialize
        migrated1 = apply_migrations(copy.deepcopy(registry))
        serialized1 = serialize_registry_yaml(migrated1)

        # Parse back, migrate again, serialize
        parsed = parse_registry_yaml(serialized1)
        migrated2 = apply_migrations(parsed)
        serialized2 = serialize_registry_yaml(migrated2)

        assert serialized1 == serialized2


# ---------------------------------------------------------------------------
# Property 7: Serialization Round-Trip After Migration
# ---------------------------------------------------------------------------


class TestProperty7SerializationRoundTrip:
    """Feature: registry-schema-versioning, Property 7: Serialization Round-Trip After Migration

    For any valid version "1" registry dict, migrating to version "2",
    serializing with serialize_registry_yaml, and parsing back with
    parse_registry_yaml shall produce a dict with identical source data.

    **Validates: Requirements 7.2**
    """

    @given(registry=st_v1_registry())
    @settings(max_examples=10)
    def test_round_trip_preserves_source_data(self, registry):
        migrated = migrate_v1_to_v2(copy.deepcopy(registry))
        serialized = serialize_registry_yaml(migrated)
        parsed = parse_registry_yaml(serialized)

        assert parsed["version"] == migrated["version"]
        assert set(parsed["sources"].keys()) == set(migrated["sources"].keys())

        for key in migrated["sources"]:
            orig = migrated["sources"][key]
            rt = parsed["sources"][key]
            for field in orig:
                assert field in rt, f"{key}: field {field!r} lost in round-trip"
                assert rt[field] == orig[field], (
                    f"{key}.{field}: {orig[field]!r} != {rt[field]!r} after round-trip"
                )


# ---------------------------------------------------------------------------
# Property 8: Validation Accepts Migrated Registries
# ---------------------------------------------------------------------------


class TestProperty8ValidationAcceptsMigrated:
    """Feature: registry-schema-versioning, Property 8: Validation Accepts Migrated Registries

    For any valid version "1" registry dict, after applying migrate_v1_to_v2,
    calling validate_registry shall return zero errors.

    **Validates: Requirements 5.1, 5.4**
    """

    @given(registry=st_v1_registry())
    @settings(max_examples=10)
    def test_migrated_registry_passes_validation(self, registry):
        migrated = migrate_v1_to_v2(copy.deepcopy(registry))
        errors = validate_registry(migrated)
        assert errors == [], f"Validation errors after migration: {errors}"


# ---------------------------------------------------------------------------
# Property 9: Validation Rejects Invalid Field Values
# ---------------------------------------------------------------------------


class TestProperty9ValidationRejectsInvalid:
    """Feature: registry-schema-versioning, Property 9: Validation Rejects Invalid Field Values

    For any registry dict where a source entry has test_load_status set to
    a value not in {complete, skipped, null} or test_entity_count set to a
    negative integer or non-integer, validate_registry shall return one or
    more errors.

    **Validates: Requirements 5.2, 5.3**
    """

    @given(
        registry=st_v1_registry(),
        invalid_tls=st.text(
            min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"
        ),
    )
    @settings(max_examples=10)
    def test_invalid_test_load_status_rejected(self, registry, invalid_tls):
        assume(invalid_tls not in VALID_TEST_LOAD_STATUSES)
        migrated = migrate_v1_to_v2(copy.deepcopy(registry))
        # Set invalid test_load_status on first entry
        first_key = next(iter(migrated["sources"]))
        migrated["sources"][first_key]["test_load_status"] = invalid_tls
        errors = validate_registry(migrated)
        assert any("test_load_status" in e for e in errors), (
            f"Expected validation error for invalid test_load_status {invalid_tls!r}"
        )

    @given(
        registry=st_v1_registry(),
        negative_count=st.integers(max_value=-1),
    )
    @settings(max_examples=10)
    def test_negative_test_entity_count_rejected(self, registry, negative_count):
        migrated = migrate_v1_to_v2(copy.deepcopy(registry))
        first_key = next(iter(migrated["sources"]))
        migrated["sources"][first_key]["test_entity_count"] = negative_count
        errors = validate_registry(migrated)
        assert any("test_entity_count" in e for e in errors), (
            f"Expected validation error for negative test_entity_count {negative_count}"
        )
