"""Tests for the CORD Mapping Fast-Path feature.

Feature: cord-mapping-fast-path

This module is shared across several spec tasks (registry schema, readiness
classification, bounded-sample, unavailable-schema, lineage invariant, and the
helper-script conventions). Each task contributes its own test class; module
level only holds the shared imports and the ``scripts/`` path setup so the
helper script can be imported directly.
"""

from __future__ import annotations

import ast
import json
import string
import sys
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Absolute path to the script under test, used for AST/source inspection.
_CHECK_CORD_READINESS_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "check_cord_readiness.py"
)

from check_cord_readiness import (  # noqa: E402  (path manipulated above)
    ReadinessResult,
    check_readiness,
    main,
)
from data_sources import (  # noqa: E402  (path manipulated above)
    REQUIRED_ENTRY_FIELDS,
    VALID_FORMATS,
    VALID_LOAD_STATUSES,
    VALID_MAPPING_STATUSES,
    validate_registry,
)

# Schema keys a Senzing-loadable record is expected to carry at the top level.
# These are supplied by the caller (from the MCP Entity Specification) and are
# only used here to build representative fixtures -- never as a Senzing fact.
_SENZING_SCHEMA_KEYS = "DATA_SOURCE,RECORD_ID,FEATURES"


def _top_level_import_modules(source: str) -> set[str]:
    """Collect the top-level module names imported by a Python source string.

    Parses the source into an AST and records the first dotted component of
    every absolute ``import`` and ``from ... import`` statement. Relative
    imports (``from . import x``) are ignored because they reference sibling
    modules, not distributable packages.

    Args:
        source: The full Python source text to analyze.

    Returns:
        The set of top-level module names the source imports.
    """
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split(".", 1)[0])
    return modules


def _write_jsonl(path: Path, records: list[str]) -> Path:
    """Write ``records`` as newline-delimited JSON lines to ``path``.

    Args:
        path: Destination file path.
        records: Pre-serialized JSON strings, one per record.

    Returns:
        The path that was written (for convenient chaining).
    """
    path.write_text("\n".join(records) + "\n", encoding="utf-8")
    return path


class TestHelperScriptConventions:
    """Smoke tests for script structure and conventions.

    Covers the helper-script surface for task 5.2:

    - ``test_helper_script_cli`` (Validates: Requirements 8.3) -- the script
      exposes a ``main()`` entry point behind an argparse CLI and returns exit
      code 0 when ready and 1 when not ready.
    - ``test_helper_stdlib_only`` (Validates: Requirements 2.8) -- the script
      imports only Python standard-library modules.
    - Example CLI runs over valid CORD-like, legacy-structure, and mixed JSONL.
    """

    def test_helper_script_cli(self, tmp_path: Path, capsys) -> None:
        """Script has a callable main(), an argparse CLI, and exits 0/1 correctly.

        Validates: Requirements 8.3
        """
        # main() is present and callable.
        assert callable(main)

        # The CLI is built with argparse: invoking --help prints usage and
        # exits 0 (argparse's standard behavior), confirming an argparse parser.
        with pytest.raises(SystemExit) as help_exit:
            main(["--help"])
        assert help_exit.value.code == 0
        help_output = capsys.readouterr().out
        assert "--file" in help_output
        assert "--schema-keys" in help_output
        assert "--max-records" in help_output

        # Ready input -> exit code 0.
        ready_file = _write_jsonl(
            tmp_path / "ready.jsonl",
            ['{"DATA_SOURCE": "TEST", "RECORD_ID": "1", "FEATURES": [{"NAME_FULL": "A"}]}'],
        )
        ready_code = main(
            ["--file", str(ready_file), "--schema-keys", _SENZING_SCHEMA_KEYS]
        )
        assert ready_code == 0

        # Not-ready input -> exit code 1.
        not_ready_file = _write_jsonl(
            tmp_path / "not_ready.jsonl",
            ['{"id": "1", "name": "A"}'],
        )
        not_ready_code = main(
            ["--file", str(not_ready_file), "--schema-keys", _SENZING_SCHEMA_KEYS]
        )
        assert not_ready_code == 1

    def test_cli_requires_file_and_schema_keys(self, capsys) -> None:
        """The argparse CLI rejects invocation without its required arguments.

        Validates: Requirements 8.3
        """
        with pytest.raises(SystemExit) as exc_info:
            main([])
        # argparse exits with a non-zero code (2) on a usage error.
        assert exc_info.value.code != 0
        assert "--file" in capsys.readouterr().err

    def test_helper_stdlib_only(self) -> None:
        """The helper script imports only Python standard-library modules.

        Validates: Requirements 2.8
        """
        source = _CHECK_CORD_READINESS_PATH.read_text(encoding="utf-8")
        imported = _top_level_import_modules(source)

        # sys.stdlib_module_names (Python 3.11+) is the authoritative set of
        # stdlib top-level module names for the running interpreter, so no
        # hand-maintained allow-list is needed.
        stdlib = sys.stdlib_module_names
        non_stdlib = {name for name in imported if name not in stdlib}

        assert not non_stdlib, (
            f"check_cord_readiness.py must import stdlib only; "
            f"found non-stdlib import(s): {sorted(non_stdlib)}"
        )

    def test_cli_valid_cord_jsonl_is_ready(self, tmp_path: Path, capsys) -> None:
        """Valid CORD-like JSONL (all schema keys present) -> ready, exit 0.

        Validates: Requirements 8.3
        """
        data_file = _write_jsonl(
            tmp_path / "cord-las-vegas.jsonl",
            [
                '{"DATA_SOURCE": "CORD_LV", "RECORD_ID": "1", '
                '"FEATURES": [{"NAME_FULL": "Alice"}]}',
                '{"DATA_SOURCE": "CORD_LV", "RECORD_ID": "2", '
                '"FEATURES": [{"NAME_FULL": "Bob"}]}',
                '{"DATA_SOURCE": "CORD_LV", "RECORD_ID": "3", '
                '"FEATURES": [{"NAME_FULL": "Carol"}]}',
            ],
        )

        exit_code = main(
            ["--file", str(data_file), "--schema-keys", _SENZING_SCHEMA_KEYS]
        )

        assert exit_code == 0
        stdout = capsys.readouterr().out
        assert '"ready": true' in stdout

    def test_cli_legacy_structure_is_not_ready(self, tmp_path: Path, capsys) -> None:
        """Legacy flat/sub-list structure JSONL -> not ready, exit 1.

        Validates: Requirements 8.3
        """
        data_file = _write_jsonl(
            tmp_path / "cord-legacy.jsonl",
            [
                '{"id": "1", "name": "Alice", "addresses": [{"city": "Vegas"}]}',
                '{"id": "2", "name": "Bob", "addresses": [{"city": "Reno"}]}',
            ],
        )

        exit_code = main(
            ["--file", str(data_file), "--schema-keys", _SENZING_SCHEMA_KEYS]
        )

        assert exit_code == 1
        stdout = capsys.readouterr().out
        assert '"ready": false' in stdout

    def test_cli_mixed_records_is_not_ready(self, tmp_path: Path, capsys) -> None:
        """Mixed valid and invalid records -> not ready, exit 1 (all must pass).

        Validates: Requirements 8.3
        """
        data_file = _write_jsonl(
            tmp_path / "cord-mixed.jsonl",
            [
                '{"DATA_SOURCE": "CORD_MX", "RECORD_ID": "1", '
                '"FEATURES": [{"NAME_FULL": "Alice"}]}',
                # Second record is missing FEATURES -> whole file is not ready.
                '{"DATA_SOURCE": "CORD_MX", "RECORD_ID": "2"}',
            ],
        )

        exit_code = main(
            ["--file", str(data_file), "--schema-keys", _SENZING_SCHEMA_KEYS]
        )

        assert exit_code == 1
        stdout = capsys.readouterr().out
        assert '"ready": false' in stdout

    def test_check_readiness_returns_dataclass(self, tmp_path: Path) -> None:
        """check_readiness returns a ReadinessResult with consistent counts.

        Validates: Requirements 8.3
        """
        data_file = _write_jsonl(
            tmp_path / "cord-counts.jsonl",
            [
                '{"DATA_SOURCE": "CORD_CT", "RECORD_ID": "1", "FEATURES": []}',
                '{"DATA_SOURCE": "CORD_CT", "RECORD_ID": "2"}',
            ],
        )

        result = check_readiness(
            str(data_file), ["DATA_SOURCE", "RECORD_ID", "FEATURES"]
        )

        assert isinstance(result, ReadinessResult)
        assert result.ready is False
        assert result.records_checked == 2
        assert result.records_passed == 1
        assert result.records_failed == 1
        assert result.records_passed + result.records_failed == result.records_checked


# ---------------------------------------------------------------------------
# Registry-schema strategies (Property 1: backward compatibility)
# ---------------------------------------------------------------------------
#
# A "valid registry entry" is modeled against the existing data-source-registry
# validator (``data_sources.validate_registry``), so the property is checked
# against the real schema rules rather than a re-implementation. The three
# fast-path fields (``provenance``, ``senzing_ready``, ``fast_pathed``) are
# additive optional fields; adding or omitting them must never invalidate an
# otherwise-valid entry nor mutate a pre-existing field value.

# The fast-path optional fields introduced by this feature.
_OPTIONAL_FAST_PATH_FIELDS: tuple[str, ...] = (
    "provenance",
    "senzing_ready",
    "fast_pathed",
)

# Allowed provenance values per Requirements 1.1, 1.2, 1.5.
_PROVENANCE_VALUES: tuple[str, ...] = (
    "cord",
    "own",
    "free_data",
    "synthesized",
    "unknown",
)


@st.composite
def st_data_source_key(draw) -> str:
    """Draw a DATA_SOURCE key matching the registry key rule ``^[A-Z][A-Z0-9_]*$``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A registry key with an uppercase-letter head and an
        uppercase/digit/underscore tail.
    """
    head = draw(st.sampled_from(string.ascii_uppercase))
    tail = draw(
        st.text(
            alphabet=string.ascii_uppercase + string.digits + "_",
            min_size=0,
            max_size=15,
        )
    )
    return head + tail


@st.composite
def st_iso_timestamp(draw) -> str:
    """Draw an ISO 8601 UTC timestamp string such as ``2025-07-15T14:30:00Z``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``%Y-%m-%dT%H:%M:%SZ`` formatted timestamp string.
    """
    moment = draw(
        st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2035, 12, 31))
    )
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@st.composite
def st_v1_registry_entry(draw) -> dict:
    """Draw a valid pre-fast-path ("v1") data-source registry entry.

    The entry carries exactly the fields the data-source-registry validator
    requires for a schema-version-2 registry and none of the fast-path optional
    fields, so it represents an entry created before this feature existed. Enum
    fields are drawn from the validator's own allowed value sets so the entry is
    genuinely valid under ``validate_registry``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A registry-entry mapping with the required fields populated.
    """
    return {
        "name": draw(st.text(min_size=1, max_size=40)),
        "file_path": draw(st.text(min_size=1, max_size=60)),
        "format": draw(st.sampled_from(sorted(VALID_FORMATS))),
        "record_count": draw(
            st.one_of(st.none(), st.integers(min_value=0, max_value=10_000_000))
        ),
        "quality_score": draw(
            st.one_of(st.none(), st.integers(min_value=0, max_value=100))
        ),
        "mapping_status": draw(st.sampled_from(sorted(VALID_MAPPING_STATUSES))),
        "load_status": draw(st.sampled_from(sorted(VALID_LOAD_STATUSES))),
        "added_at": draw(st_iso_timestamp()),
        "updated_at": draw(st_iso_timestamp()),
    }


@st.composite
def st_optional_fast_path_fields(draw) -> dict:
    """Draw an arbitrary subset of the fast-path optional fields with valid values.

    Each of ``provenance``, ``senzing_ready`` and ``fast_pathed`` is included
    independently, so the drawn mapping ranges from empty (all fields omitted)
    to all three present. This lets a single property exercise both the "add"
    and "omit" halves of the backward-compatibility guarantee.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A mapping containing zero to three of the fast-path optional fields.
    """
    optional: dict = {}
    if draw(st.booleans()):
        optional["provenance"] = draw(st.sampled_from(_PROVENANCE_VALUES))
    if draw(st.booleans()):
        optional["senzing_ready"] = draw(st.booleans())
    if draw(st.booleans()):
        optional["fast_pathed"] = draw(st.booleans())
    return optional


class TestRegistrySchemaProperties:
    """Property: Registry schema backward compatibility."""

    # Feature: cord-mapping-fast-path, Property 1

    @given(
        data_source=st_data_source_key(),
        base_entry=st_v1_registry_entry(),
        optional=st_optional_fast_path_fields(),
    )
    def test_registry_schema_backward_compatible(
        self, data_source: str, base_entry: dict, optional: dict
    ) -> None:
        """Adding or omitting the optional fast-path fields keeps validity and values.

        For a valid pre-feature registry entry, adding any subset of the
        additive optional fields (``provenance``, ``senzing_ready``,
        ``fast_pathed``) -- or omitting them entirely -- yields an entry that is
        still valid under the data-source-registry validator and leaves every
        pre-existing field value unchanged. Removing the optional fields again
        recovers the original entry exactly.

        Validates: Requirements 1.3, 6.6
        """
        # Feature: cord-mapping-fast-path, Property 1: for any valid registry
        # entry, adding/omitting provenance/senzing_ready/fast_pathed yields a
        # valid entry that preserves all existing field values unchanged.

        # A base entry without the optional fields is valid to begin with.
        base_registry = {"version": "2", "sources": {data_source: dict(base_entry)}}
        assert validate_registry(base_registry) == []

        # Adding an arbitrary subset of the optional fields keeps it valid.
        augmented_entry = dict(base_entry)
        augmented_entry.update(optional)
        augmented_registry = {
            "version": "2",
            "sources": {data_source: augmented_entry},
        }
        assert validate_registry(augmented_registry) == []

        # Every pre-existing field value is preserved unchanged.
        for field, value in base_entry.items():
            assert augmented_entry[field] == value

        # The required-field set and the existing status value sets are intact.
        assert REQUIRED_ENTRY_FIELDS.issubset(augmented_entry.keys())
        assert augmented_entry["mapping_status"] in VALID_MAPPING_STATUSES
        assert augmented_entry["load_status"] in VALID_LOAD_STATUSES

        # Omitting the optional fields again recovers the original entry exactly.
        reduced_entry = {
            key: val
            for key, val in augmented_entry.items()
            if key not in _OPTIONAL_FAST_PATH_FIELDS
        }
        assert reduced_entry == base_entry
        reduced_registry = {"version": "2", "sources": {data_source: reduced_entry}}
        assert validate_registry(reduced_registry) == []


# ---------------------------------------------------------------------------
# Readiness-check strategies (Property 2: classification correctness)
# ---------------------------------------------------------------------------
#
# The readiness check classifies a JSONL file as ready iff every sampled record
# is a JSON object carrying all caller-supplied schema keys as top-level keys.
# These strategies build that input space directly: a non-empty set of schema
# keys plus a small list of JSON-object records, each of which either carries
# every schema key or is missing at least one. Keys avoid leading/trailing
# whitespace so they survive check_readiness's key normalization unchanged,
# letting the test compute the expected classification straight from the
# generated dicts.

# Keys are drawn without whitespace so ``check_readiness``'s ``str.strip``
# normalization is a no-op and the generated dict keys match the schema keys
# exactly.
_JSON_KEY_ALPHABET = string.ascii_letters + string.digits + "_"

# Values never influence the top-level-key check, so a small JSON-clean set of
# scalars keeps generation fast without weakening the property.
st_json_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1000, max_value=1000),
    st.text(alphabet=_JSON_KEY_ALPHABET + " -.", max_size=8),
)


def st_json_key() -> st.SearchStrategy[str]:
    """Return a strategy for non-empty JSON object keys without surrounding space.

    Returns:
        A strategy producing identifier-like strings safe to use as both schema
        keys and record keys, so they round-trip through JSON and survive the
        readiness check's key normalization unchanged.
    """
    return st.text(alphabet=_JSON_KEY_ALPHABET, min_size=1, max_size=12)


def st_json_value() -> st.SearchStrategy[object]:
    """Return a strategy for arbitrary JSON-serializable record values.

    Values never influence the top-level-key classification; a scalar, a short
    list, or a shallow object is enough to keep records representative.

    Returns:
        A strategy producing JSON-serializable values.
    """
    return st.one_of(
        st_json_scalar,
        st.lists(st_json_scalar, max_size=3),
        st.dictionaries(st_json_key(), st_json_scalar, max_size=3),
    )


@st.composite
def st_schema_keys(draw) -> list[str]:
    """Draw a non-empty list of unique top-level schema keys.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A list of 1-5 unique key strings the readiness check must find in every
        record for a ready classification.
    """
    return draw(st.lists(st_json_key(), min_size=1, max_size=5, unique=True))


@st.composite
def st_record_dict(draw, schema_keys: list[str]) -> dict:
    """Draw a JSON-object record that either carries all schema keys or omits some.

    Roughly half the time the record is drawn "conforming" (every schema key
    present); otherwise at least one schema key is deliberately dropped. In both
    cases arbitrary extra keys may be added. The caller computes the expected
    classification from the returned dict, so incidental overlap between extra
    keys and schema keys never desynchronizes the expectation.

    Args:
        draw: The Hypothesis draw callable.
        schema_keys: The required schema keys for the enclosing case.

    Returns:
        A record dict with JSON-serializable values.
    """
    if draw(st.booleans()):
        # Conforming: include every schema key as a top-level key.
        record = {key: draw(st_json_value()) for key in schema_keys}
    else:
        # Non-conforming: drop a non-empty subset of the schema keys.
        dropped = draw(st.lists(st.sampled_from(schema_keys), min_size=1, unique=True))
        record = {
            key: draw(st_json_value()) for key in schema_keys if key not in dropped
        }
    # Optionally sprinkle in extra, non-required keys with arbitrary values.
    extra = draw(st.dictionaries(st_json_key(), st_json_value(), max_size=3))
    record.update(extra)
    return record


@st.composite
def st_readiness_case(draw) -> tuple[list[str], list[dict]]:
    """Draw a ``(schema_keys, records)`` readiness case for classification testing.

    The record count is kept at or below the readiness check's default sample
    bound (100) so every record participates in the classification and the
    expected outcome is simply "all records conform".

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A tuple of the required schema keys and a non-empty list of record dicts.
    """
    schema_keys = draw(st_schema_keys())
    records = draw(st.lists(st_record_dict(schema_keys), min_size=1, max_size=8))
    return schema_keys, records


# ---------------------------------------------------------------------------
# Bounded-sample strategy (Property 3: bounded sample invariant)
# ---------------------------------------------------------------------------
#
# The bounded-sample property only concerns how many records the check reads,
# which is independent of record content. So instead of drawing each record,
# this strategy draws a record count N and a maximum M chosen to straddle the
# sample bound from both sides. Half the cases omit max_records (signaled by
# None) to exercise the documented default of 100 with N spanning below/at/above
# 100; the other half use a small explicit M as a cheap way to cross the bound
# frequently. The test then builds N cheap, identical conforming records.


@st.composite
def st_bounded_sample_case(draw) -> tuple[list[str], int, int | None]:
    """Draw a ``(schema_keys, n_records, max_records)`` bounded-sample case.

    The case pairs a record count ``N`` with a maximum ``M`` chosen so the pair
    straddles the sample bound from both directions. When ``max_records`` is
    ``None`` the check's default of 100 applies and ``N`` spans below, at, and
    above 100; otherwise a small explicit ``M`` is drawn to cross the bound
    cheaply and often.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A tuple of the required schema keys, the number of records to write, and
        the ``max_records`` value to pass (``None`` to use the default of 100).
    """
    schema_keys = draw(st_schema_keys())
    if draw(st.booleans()):
        # Default path: max_records omitted -> defaults to 100. Span N below,
        # at, and above 100 so the bound is genuinely exercised.
        max_records: int | None = None
        n_records = draw(st.integers(min_value=0, max_value=130))
    else:
        # Explicit small max: a cheaper way to repeatedly cross the bound.
        max_records = draw(st.integers(min_value=1, max_value=15))
        n_records = draw(st.integers(min_value=0, max_value=30))
    return schema_keys, n_records, max_records


class TestReadinessCheckProperties:
    """Properties: Readiness classification, bounded sample, unavailable schema."""

    # Feature: cord-mapping-fast-path, Property 2, 3, 4

    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ]
    )
    @given(case=st_readiness_case())
    def test_readiness_classification_correctness(
        self, case: tuple[list[str], list[dict]], tmp_path: Path
    ) -> None:
        """Ready iff every sampled record carries all schema keys as top-level keys.

        For any JSONL file and non-empty set of required schema keys,
        ``check_readiness`` classifies the file as ready exactly when every
        sampled record is a JSON object containing all schema keys as top-level
        keys; if any sampled record is missing any required key, the result is
        not-ready.

        Validates: Requirements 2.3, 2.4
        """
        # Feature: cord-mapping-fast-path, Property 2: for any JSONL file and set
        # of required schema keys, the readiness check classifies the file as
        # ready if and only if every sampled record contains all specified schema
        # keys as top-level JSON keys.
        schema_keys, records = case
        data_file = _write_jsonl(
            tmp_path / "cord-readiness.jsonl",
            [json.dumps(record) for record in records],
        )

        result = check_readiness(str(data_file), schema_keys)

        # Records stay at/under the default 100-record sample bound, so every
        # record participates and the expected verdict is "all records conform".
        expected_ready = all(
            all(key in record for key in schema_keys) for record in records
        )
        assert result.ready is expected_ready

        # The pass/fail tally stays internally consistent with the verdict.
        assert result.records_checked == len(records)
        assert result.records_passed + result.records_failed == result.records_checked
        assert (result.records_failed == 0) is expected_ready

    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ]
    )
    @given(case=st_bounded_sample_case())
    def test_bounded_sample_invariant(
        self, case: tuple[list[str], int, int | None], tmp_path: Path
    ) -> None:
        """Readiness check examines exactly min(N, M) records, M defaulting to 100.

        For a JSONL file with ``N`` non-empty records and a configured maximum
        ``M`` (defaulting to 100 when ``max_records`` is omitted),
        ``check_readiness`` reports ``records_checked == min(N, M)`` -- it never
        reads past the bound and never skips available records below it.

        Validates: Requirements 2.5
        """
        # Feature: cord-mapping-fast-path, Property 3: for any JSONL file with N
        # records and a configured maximum M (default 100), the readiness check
        # examines at most min(N, M) records.
        schema_keys, n_records, max_records = case

        # Record content is irrelevant to the count, so reuse one conforming
        # record (all schema keys present) N times to keep generation cheap.
        conforming_line = json.dumps({key: "x" for key in schema_keys})
        data_file = _write_jsonl(
            tmp_path / "cord-bounded.jsonl",
            [conforming_line] * n_records,
        )

        if max_records is None:
            # Exercise the documented default maximum of 100.
            result = check_readiness(str(data_file), schema_keys)
            effective_max = 100
        else:
            result = check_readiness(str(data_file), schema_keys, max_records=max_records)
            effective_max = max_records

        # At most min(N, M) records are examined, and the bound is tight: below
        # the maximum every available record is read.
        assert result.records_checked == min(n_records, effective_max)
        assert result.records_checked <= effective_max
        assert result.records_checked <= n_records

    @settings(
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ]
    )
    @given(case=st_readiness_case())
    def test_empty_schema_defaults_not_ready(
        self, case: tuple[list[str], list[dict]], tmp_path: Path
    ) -> None:
        """Empty schema keys or undeterminable conformance always yields not-ready.

        For any CORD source file, an empty schema keys list means the readiness
        check has no structural indicators to compare against -- the MCP Entity
        Specification was unavailable, so no keys were obtained -- and the source
        is classified not-ready regardless of its contents. The companion
        "cannot determine conformance" cases (an empty file with no records and a
        missing file path) likewise default to not-ready.

        Validates: Requirements 2.7, 8.5
        """
        # Feature: cord-mapping-fast-path, Property 4: for any CORD source file,
        # if the schema keys list is empty or the check cannot determine
        # structural conformance, the readiness check returns not-ready.
        _schema_keys, records = case
        data_file = _write_jsonl(
            tmp_path / "cord-empty-schema.jsonl",
            [json.dumps(record) for record in records],
        )

        # Primary property: an empty schema keys list means conformance cannot be
        # determined, so the source is not ready no matter what the file holds.
        result = check_readiness(str(data_file), [])
        assert result.ready is False

        # Companion case: an empty file (no records) with non-empty keys also
        # leaves conformance undeterminable, so it is not ready either.
        empty_file = tmp_path / "cord-empty.jsonl"
        empty_file.write_text("", encoding="utf-8")
        assert check_readiness(str(empty_file), ["DATA_SOURCE"]).ready is False

        # Companion case: a missing file path cannot be inspected -> not ready.
        missing_file = tmp_path / "cord-missing.jsonl"
        assert check_readiness(str(missing_file), ["DATA_SOURCE"]).ready is False


# ---------------------------------------------------------------------------
# Fast-path lineage-entry helper and strategies (Property 5: lineage invariant)
# ---------------------------------------------------------------------------
#
# There is no runtime lineage-builder script for this feature -- the only script
# deliverable is check_cord_readiness.py. The fast-path lineage entry is produced
# by the agent per the Module 5 Phase 1 Step 5a steering and documented in the
# design "Component 6 / Data Models -> Fast-Path Lineage Entry". This small pure
# helper models that construction so the invariant can be property-tested; task
# 7.2 reuses it, so it is defined at module level rather than inside a class.


def build_fast_path_lineage_entry(
    data_source: str, file_path: str, record_count: int
) -> dict:
    """Build the data-lineage entry recorded when a CORD source is fast-pathed.

    Models design Component 6 / the Step 5a steering: no transformation occurs,
    so the original data/raw file is both input and output with equal counts.

    Args:
        data_source: The DATA_SOURCE key of the fast-pathed source.
        file_path: The original ``data/raw/`` file path, kept as both the input
            and output file because no transformed output is produced.
        record_count: The source's record count N; both ``records_in`` and
            ``records_out`` take this value.

    Returns:
        The fast-path lineage entry mapping matching the design data model.
    """
    return {
        "source_file": file_path,
        "transformation_script": None,
        "output_file": file_path,
        "records_in": record_count,
        "records_out": record_count,
        "records_rejected": 0,
        "quality_score": None,
        "fast_pathed": True,
        "fast_path_reason": "CORD source already in Senzing-loadable form",
    }


@st.composite
def st_raw_file_path(draw) -> str:
    """Draw a ``data/raw/`` source file path such as ``data/raw/cord-las-vegas.jsonl``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``data/raw/<stem>.<ext>`` path string with a non-empty stem.
    """
    stem = draw(
        st.text(
            alphabet=string.ascii_lowercase + string.digits + "-_",
            min_size=1,
            max_size=30,
        )
    )
    ext = draw(st.sampled_from(("jsonl", "json", "csv")))
    return f"data/raw/{stem}.{ext}"


class TestLineageProperties:
    """Property: Fast-path lineage entry invariant."""

    # Feature: cord-mapping-fast-path, Property 5

    @given(
        data_source=st_data_source_key(),
        file_path=st_raw_file_path(),
        record_count=st.integers(min_value=0, max_value=10_000_000),
    )
    def test_fast_path_lineage_entry_invariant(
        self, data_source: str, file_path: str, record_count: int
    ) -> None:
        """Fast-path lineage entry has equal in/out file and counts, zero rejects.

        For any fast-pathed source with record count N, the generated lineage
        entry has ``source_file == output_file``, ``records_in == records_out ==
        N``, and ``records_rejected == 0`` -- capturing that a fast-path performs
        no transformation and leaves the original ``data/raw/`` file untouched.

        Validates: Requirements 6.4
        """
        # Feature: cord-mapping-fast-path, Property 5: for any fast-pathed source
        # with record count N, the generated lineage entry has source_file ==
        # output_file, records_in == records_out == N, and records_rejected == 0.
        entry = build_fast_path_lineage_entry(data_source, file_path, record_count)

        # Core invariant: input and output refer to the same file with equal
        # before-and-after counts and nothing rejected.
        assert entry["source_file"] == entry["output_file"]
        assert entry["source_file"] == file_path
        assert entry["records_in"] == entry["records_out"] == record_count
        assert entry["records_rejected"] == 0

        # The no-transformation shape from the design data model holds too.
        assert entry["transformation_script"] is None
        assert entry["quality_score"] is None
        assert entry["fast_pathed"] is True
        assert isinstance(entry["fast_path_reason"], str) and entry["fast_path_reason"]


# ---------------------------------------------------------------------------
# Example-based tests (task 7.2): provenance and readiness scenarios
# ---------------------------------------------------------------------------
#
# Concrete, example-based unit tests (no @given) that complement the property
# classes above. They pin down the specific scenarios in the design "Testing
# Strategy -> Unit Tests" table: readiness classification on representative CORD
# files, provenance value handling, and the non-blocking fast-path lineage
# contract. Shared helpers (_write_jsonl, _SENZING_SCHEMA_KEYS,
# _PROVENANCE_VALUES, build_fast_path_lineage_entry, validate_registry) are
# reused from above rather than redefined.


def _valid_registry_entry() -> dict:
    """Build a minimal valid schema-version-2 registry entry for example tests.

    Populates exactly the fields the data-source-registry validator requires,
    with none of the fast-path optional fields, so a caller can add a single
    optional field (such as ``provenance``) and assert the entry stays valid.

    Returns:
        A registry-entry mapping with the required fields populated.
    """
    return {
        "name": "CORD Las Vegas",
        "file_path": "data/raw/cord-las-vegas.jsonl",
        "format": "jsonl",
        "record_count": 100,
        "quality_score": None,
        "mapping_status": "complete",
        "load_status": "not_loaded",
        "added_at": "2025-07-15T14:30:00Z",
        "updated_at": "2025-07-15T14:35:00Z",
    }


class TestReadinessCheckExamples:
    """Example-based tests for specific readiness scenarios."""

    def test_readiness_check_valid_cord_file(self, tmp_path: Path) -> None:
        """A well-formed CORD JSONL file with all schema keys is classified ready.

        Every sampled record is valid JSON carrying DATA_SOURCE, RECORD_ID and
        FEATURES as top-level keys, so the source is Senzing_Ready.

        Validates: Requirements 2.3
        """
        schema_keys = _SENZING_SCHEMA_KEYS.split(",")
        data_file = _write_jsonl(
            tmp_path / "cord-valid.jsonl",
            [
                '{"DATA_SOURCE": "CORD_LV", "RECORD_ID": "1", '
                '"FEATURES": [{"NAME_FULL": "Alice"}]}',
                '{"DATA_SOURCE": "CORD_LV", "RECORD_ID": "2", '
                '"FEATURES": [{"NAME_FULL": "Bob"}]}',
            ],
        )

        result = check_readiness(str(data_file), schema_keys)

        assert result.ready is True
        assert result.records_checked == 2
        assert result.records_passed == 2
        assert result.records_failed == 0

    def test_readiness_check_legacy_structure(self, tmp_path: Path) -> None:
        """A legacy flat/sub-list structure CORD file is classified not ready.

        The records use a flat ``id``/``name`` layout with a sub-list of
        addresses and carry none of the required schema keys, so the source
        still needs structural mapping.

        Validates: Requirements 2.4
        """
        schema_keys = _SENZING_SCHEMA_KEYS.split(",")
        data_file = _write_jsonl(
            tmp_path / "cord-legacy.jsonl",
            [
                '{"id": "1", "name": "Alice", "addresses": [{"city": "Vegas"}]}',
                '{"id": "2", "name": "Bob", "addresses": [{"city": "Reno"}]}',
            ],
        )

        result = check_readiness(str(data_file), schema_keys)

        assert result.ready is False
        assert result.records_checked == 2
        assert result.records_passed == 0
        assert result.records_failed == 2

    def test_readiness_check_mixed_records(self, tmp_path: Path) -> None:
        """A file mixing valid and invalid records is classified not ready.

        A single non-conforming record (missing FEATURES) is enough to make the
        whole file not ready, since all sampled records must pass.

        Validates: Requirements 2.3
        """
        schema_keys = _SENZING_SCHEMA_KEYS.split(",")
        data_file = _write_jsonl(
            tmp_path / "cord-mixed.jsonl",
            [
                '{"DATA_SOURCE": "CORD_MX", "RECORD_ID": "1", '
                '"FEATURES": [{"NAME_FULL": "Alice"}]}',
                # Missing FEATURES -> the whole file is not ready.
                '{"DATA_SOURCE": "CORD_MX", "RECORD_ID": "2"}',
                '{"DATA_SOURCE": "CORD_MX", "RECORD_ID": "3", '
                '"FEATURES": [{"NAME_FULL": "Carol"}]}',
            ],
        )

        result = check_readiness(str(data_file), schema_keys)

        assert result.ready is False
        assert result.records_checked == 3
        assert result.records_passed == 2
        assert result.records_failed == 1


class TestProvenanceExamples:
    """Example-based tests for provenance field behavior and fast-path lineage.

    Covers the concrete provenance and lineage scenarios from the design
    "Testing Strategy -> Unit Tests" table:

    - ``test_provenance_valid_values`` (Validates: Requirements 1.1, 1.2)
    - ``test_provenance_unknown_not_eligible`` (Validates: Requirements 1.5)
    - ``test_fast_path_lineage_no_transform`` (Validates: Requirements 6.4)
    - ``test_lineage_failure_non_blocking`` (Validates: Requirements 6.8)
    """

    def test_provenance_valid_values(self) -> None:
        """Each allowed provenance value is accepted by the value set and schema.

        "Accepted" is modeled as membership in the allowed provenance value set,
        and each value is additionally attached to a registry entry to confirm
        that ``provenance`` is an additive optional field which keeps an
        otherwise-valid entry valid under the real data-source-registry schema.

        Validates: Requirements 1.1, 1.2
        """
        for provenance in ("cord", "own", "free_data", "synthesized", "unknown"):
            # Accepted == a member of the allowed provenance value set.
            assert provenance in _PROVENANCE_VALUES

            # The value rides on a registry entry as an additive optional field
            # without invalidating the entry.
            entry = _valid_registry_entry()
            entry["provenance"] = provenance
            registry = {"version": "2", "sources": {"CORD_SOURCE": entry}}
            assert validate_registry(registry) == []

    def test_provenance_unknown_not_eligible(self) -> None:
        """A source with provenance=unknown is never eligible for the fast-path.

        Fast-path eligibility is modeled as ``provenance == "cord" and
        senzing_ready is True``. ``unknown`` is treated as non-CORD, so it is
        never eligible -- even when the source is otherwise ready.

        Validates: Requirements 1.5
        """

        def _fast_path_eligible(provenance: str, senzing_ready: bool) -> bool:
            """Return whether a source qualifies for the CORD fast-path offer."""
            return provenance == "cord" and senzing_ready is True

        # unknown is not eligible regardless of readiness.
        assert _fast_path_eligible("unknown", True) is False
        assert _fast_path_eligible("unknown", False) is False

        # Only CORD provenance with a ready source is eligible; every non-cord
        # value (including unknown) is withheld from the offer.
        assert _fast_path_eligible("cord", True) is True
        for provenance in ("own", "free_data", "synthesized", "unknown"):
            assert _fast_path_eligible(provenance, True) is False

    def test_fast_path_lineage_no_transform(self) -> None:
        """A fast-path lineage entry records that no transformation occurred.

        The entry has a null ``transformation_script`` and ``fast_pathed`` true,
        with the original file as both input and output and equal record counts.

        Validates: Requirements 6.4
        """
        entry = build_fast_path_lineage_entry(
            "CORD_LAS_VEGAS", "data/raw/cord-las-vegas.jsonl", 8421
        )

        assert entry["transformation_script"] is None
        assert entry["fast_pathed"] is True
        assert entry["source_file"] == entry["output_file"]
        assert entry["records_in"] == entry["records_out"] == 8421
        assert entry["records_rejected"] == 0

    def test_lineage_failure_non_blocking(self) -> None:
        """A lineage write failure does not block routing a fast-pathed source.

        Models the non-blocking contract: the fast-path routine attempts the
        lineage write inside a guard and proceeds to route the source to Module 6
        whether or not the write raised.

        Validates: Requirements 6.8
        """

        def route_fast_path(record_writer) -> str:
            """Attempt the lineage write, then route to Module 6 regardless.

            A lineage write failure is swallowed (logged for later retry in the
            real workflow) so the fast-path still proceeds.

            Args:
                record_writer: A zero-argument callable performing the write.

            Returns:
                The routing result, always "routed_to_module_6".
            """
            try:
                record_writer()
            except Exception:  # noqa: BLE001 - failure is non-blocking by contract
                pass  # Non-blocking: log for later retry, then proceed.
            return "routed_to_module_6"

        def _failing_writer() -> None:
            """Simulate a lineage write that raises."""
            raise OSError("simulated lineage write failure")

        def _succeeding_writer() -> None:
            """Simulate a lineage write that succeeds."""
            return None

        # (a) A raising writer does not propagate; the source is still routed.
        assert route_fast_path(_failing_writer) == "routed_to_module_6"

        # (b) A succeeding writer also routes the source.
        assert route_fast_path(_succeeding_writer) == "routed_to_module_6"
