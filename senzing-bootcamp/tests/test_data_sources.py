"""Property-based and unit tests for data_sources.py.

Uses Hypothesis to verify correctness properties across randomly generated
registries, plus pytest unit tests for CLI edge cases and integration points.
"""

from __future__ import annotations

import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from data_sources import (
    DATA_SOURCE_KEY_RE,
    QUALITY_THRESHOLD,
    REQUIRED_ENTRY_FIELDS,
    VALID_FORMATS,
    VALID_LOAD_STATUSES,
    VALID_MAPPING_STATUSES,
    VALID_TEST_LOAD_STATUSES,
    Registry,
    RegistryEntry,
    _dict_to_registry,
    _registry_to_dict,
    main,
    parse_registry_yaml,
    recommend_actions,
    render_data_sources_section,
    render_detail,
    render_summary,
    render_table,
    serialize_registry_yaml,
    validate_registry,
)


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.1 — Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════


def _data_source_keys():
    """Strategy producing valid DATA_SOURCE key strings: ^[A-Z][A-Z0-9_]*$."""
    first = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    rest = st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=0, max_size=12
    )
    return st.tuples(first, rest).map(lambda t: t[0] + t[1])


def _format_values():
    """Strategy producing valid format enum values."""
    return st.sampled_from(sorted(VALID_FORMATS))


def _mapping_status_values():
    """Strategy producing valid mapping_status enum values."""
    return st.sampled_from(sorted(VALID_MAPPING_STATUSES))


def _load_status_values():
    """Strategy producing valid load_status enum values."""
    return st.sampled_from(sorted(VALID_LOAD_STATUSES))


def _safe_text():
    """Strategy producing simple printable text without YAML-breaking chars."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "Pd"),
            whitelist_characters=" _/.",
        ),
        min_size=1,
        max_size=30,
    ).filter(lambda s: s.strip() != "")


def _iso_timestamps():
    """Strategy producing ISO 8601 timestamp strings."""
    return st.datetimes(
        min_value=__import__("datetime").datetime(2020, 1, 1),
        max_value=__import__("datetime").datetime(2030, 12, 31),
    ).map(
        lambda dt: dt.replace(
            tzinfo=__import__("datetime").timezone.utc
        ).isoformat()
    )


def _test_load_status_values():
    """Strategy producing valid test_load_status values (including None)."""
    return st.one_of(st.none(), st.sampled_from(sorted(VALID_TEST_LOAD_STATUSES)))


def _registry_entries(key_strategy=None):
    """Strategy producing valid RegistryEntry instances."""
    if key_strategy is None:
        key_strategy = _data_source_keys()
    return st.builds(
        RegistryEntry,
        data_source=key_strategy,
        name=_safe_text(),
        file_path=st.builds(
            lambda n: f"data/raw/{n}.csv",
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        ),
        format=_format_values(),
        record_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        file_size_bytes=st.one_of(st.none(), st.integers(min_value=0, max_value=10_000_000_000)),
        quality_score=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
        mapping_status=_mapping_status_values(),
        load_status=_load_status_values(),
        added_at=_iso_timestamps(),
        updated_at=_iso_timestamps(),
        test_load_status=_test_load_status_values(),
        test_entity_count=st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000)),
        issues=st.one_of(
            st.none(),
            st.lists(_safe_text(), min_size=0, max_size=3),
        ),
    )


def _registries(min_sources=0, max_sources=8):
    """Strategy producing valid Registry instances with unique DATA_SOURCE keys."""
    # Generate a list of unique keys, then build entries for each
    keys = st.lists(
        _data_source_keys(), min_size=min_sources, max_size=max_sources, unique=True
    )

    @st.composite
    def _build(draw):
        ks = draw(keys)
        entries = []
        for k in ks:
            entry = draw(_registry_entries(key_strategy=st.just(k)))
            entries.append(entry)
        return Registry(version="1", sources=entries)

    return _build()


def _valid_registry_dicts():
    """Strategy producing valid registry dicts (version='1', valid sources)."""
    return _registries().map(_registry_to_dict)


def _invalid_registry_dicts():
    """Strategy producing invalid registry dicts with known violations."""
    @st.composite
    def _build(draw):
        kind = draw(st.sampled_from([
            "bad_version", "missing_version", "bad_key", "missing_field",
            "bad_format", "bad_mapping_status", "bad_load_status",
        ]))
        # Start from a valid dict
        base = draw(_valid_registry_dicts())

        if kind == "bad_version":
            base["version"] = draw(st.sampled_from(["0", "99", "abc", ""]))
        elif kind == "missing_version":
            base.pop("version", None)
        elif kind == "bad_key":
            # Add an entry with an invalid key
            bad_key = draw(st.sampled_from(["lowercase", "123NUM", "_UNDER", "a"]))
            base["sources"][bad_key] = {
                "name": "bad", "file_path": "x", "format": "csv",
                "record_count": None, "quality_score": None,
                "mapping_status": "pending", "load_status": "not_loaded",
                "added_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        elif kind == "missing_field":
            if base["sources"]:
                first_key = next(iter(base["sources"]))
                field = draw(st.sampled_from(sorted(REQUIRED_ENTRY_FIELDS)))
                base["sources"][first_key].pop(field, None)
            else:
                # No sources to corrupt — fall back to bad version
                base["version"] = "99"
        elif kind == "bad_format":
            if base["sources"]:
                first_key = next(iter(base["sources"]))
                base["sources"][first_key]["format"] = "invalid_fmt"
            else:
                base["version"] = "99"
        elif kind == "bad_mapping_status":
            if base["sources"]:
                first_key = next(iter(base["sources"]))
                base["sources"][first_key]["mapping_status"] = "unknown_ms"
            else:
                base["version"] = "99"
        elif kind == "bad_load_status":
            if base["sources"]:
                first_key = next(iter(base["sources"]))
                base["sources"][first_key]["load_status"] = "unknown_ls"
            else:
                base["version"] = "99"
        return base

    return _build()



# ═══════════════════════════════════════════════════════════════════════════
# Task 7.2 — Property 1: YAML round-trip preserves registry data
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty1YAMLRoundTrip:
    """Feature: data-source-registry, Property 1: YAML round-trip preserves registry data

    For any valid Registry, serializing to YAML and parsing back SHALL produce
    an equivalent Registry — all DATA_SOURCE keys, field values, and issues
    lists are preserved.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(registry=_registries(min_sources=0, max_sources=8))
    @settings(max_examples=100)
    def test_round_trip_preserves_data(self, registry):
        """Feature: data-source-registry, Property 1: YAML round-trip preserves registry data"""
        # Registry → dict → YAML → dict → Registry
        original_dict = _registry_to_dict(registry)
        yaml_str = serialize_registry_yaml(original_dict)
        parsed_dict = parse_registry_yaml(yaml_str)
        restored = _dict_to_registry(parsed_dict)

        # Same number of sources
        assert len(restored.sources) == len(registry.sources)

        # Build lookup by data_source key
        orig_by_key = {e.data_source: e for e in registry.sources}
        rest_by_key = {e.data_source: e for e in restored.sources}

        assert set(orig_by_key.keys()) == set(rest_by_key.keys())

        for key in orig_by_key:
            orig = orig_by_key[key]
            rest = rest_by_key[key]
            assert rest.name == orig.name
            assert rest.file_path == orig.file_path
            assert rest.format == orig.format
            assert rest.record_count == orig.record_count
            assert rest.file_size_bytes == orig.file_size_bytes
            assert rest.quality_score == orig.quality_score
            assert rest.mapping_status == orig.mapping_status
            assert rest.load_status == orig.load_status
            assert rest.added_at == orig.added_at
            assert rest.updated_at == orig.updated_at
            assert rest.test_load_status == orig.test_load_status
            assert rest.test_entity_count == orig.test_entity_count
            # Issues: None vs empty list both mean "no issues"
            orig_issues = orig.issues if orig.issues else []
            rest_issues = rest.issues if rest.issues else []
            assert rest_issues == orig_issues


# ═══════════════════════════════════════════════════════════════════════════
# Task 1.2 — Property: Registry schema round-trip with test_load_status
# ═══════════════════════════════════════════════════════════════════════════


class TestPropertyTestLoadStatusRoundTrip:
    """Feature: mapping-workflow-integration, Property 1: Registry schema round-trip with test_load_status

    For any valid data source registry entry that includes a test_load_status
    field (one of complete, skipped, or None) and an optional test_entity_count
    field (non-negative integer or None), serializing the registry to YAML and
    parsing it back SHALL produce an equivalent registry with the
    test_load_status and test_entity_count values preserved.

    **Validates: Requirements 8.1**
    """

    @given(registry=_registries(min_sources=1, max_sources=8))
    @settings(max_examples=100)
    def test_round_trip_preserves_test_load_status(self, registry):
        """Feature: mapping-workflow-integration, Property 1: Registry schema round-trip with test_load_status"""
        # Registry → dict → YAML → dict → Registry
        original_dict = _registry_to_dict(registry)
        yaml_str = serialize_registry_yaml(original_dict)
        parsed_dict = parse_registry_yaml(yaml_str)
        restored = _dict_to_registry(parsed_dict)

        # Same number of sources
        assert len(restored.sources) == len(registry.sources)

        # Build lookup by data_source key
        orig_by_key = {e.data_source: e for e in registry.sources}
        rest_by_key = {e.data_source: e for e in restored.sources}

        assert set(orig_by_key.keys()) == set(rest_by_key.keys())

        for key in orig_by_key:
            orig = orig_by_key[key]
            rest = rest_by_key[key]
            # Verify test_load_status round-trips correctly
            assert rest.test_load_status == orig.test_load_status, (
                f"{key}: test_load_status mismatch: "
                f"{rest.test_load_status!r} != {orig.test_load_status!r}"
            )
            # Verify test_entity_count round-trips correctly
            assert rest.test_entity_count == orig.test_entity_count, (
                f"{key}: test_entity_count mismatch: "
                f"{rest.test_entity_count!r} != {orig.test_entity_count!r}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.3 — Property 2: Validation accepts valid, rejects invalid
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty2Validation:
    """Feature: data-source-registry, Property 2: Registry validation accepts valid and rejects invalid

    Valid registries produce empty error lists; invalid ones produce non-empty
    error lists with messages identifying each specific violation.

    **Validates: Requirements 1.2, 1.3, 1.4, 1.6, 11.1, 11.2, 11.3, 11.4**
    """

    @given(data=_valid_registry_dicts())
    @settings(max_examples=100)
    def test_valid_registry_accepted(self, data):
        """Feature: data-source-registry, Property 2: valid registries accepted"""
        errors = validate_registry(data)
        assert errors == [], f"Valid registry rejected: {errors}"

    @given(data=_invalid_registry_dicts())
    @settings(max_examples=100)
    def test_invalid_registry_rejected(self, data):
        """Feature: data-source-registry, Property 2: invalid registries rejected"""
        errors = validate_registry(data)
        assert len(errors) > 0, "Invalid registry was accepted"


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.4 — Property 3: Table rendering contains all source data
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty3TableRendering:
    """Feature: data-source-registry, Property 3: Table rendering contains all source data

    For any valid Registry with entries, render_table output SHALL contain
    every DATA_SOURCE key, mapping_status, load_status, and non-null
    quality_score and record_count values.

    **Validates: Requirements 6.1, 7.2**
    """

    @given(registry=_registries(min_sources=1, max_sources=8))
    @settings(max_examples=100)
    def test_table_contains_all_source_data(self, registry):
        """Feature: data-source-registry, Property 3: Table rendering contains all source data"""
        output = render_table(registry)

        for entry in registry.sources:
            assert entry.data_source in output
            assert entry.mapping_status in output
            assert entry.load_status in output

            if entry.quality_score is not None:
                assert f"{entry.quality_score}%" in output

            if entry.record_count is not None:
                assert f"{entry.record_count:,}" in output


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.5 — Property 4: Detail rendering contains all entry fields
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty4DetailRendering:
    """Feature: data-source-registry, Property 4: Detail rendering contains all entry fields

    For any valid RegistryEntry, render_detail output SHALL contain all
    field values including optional issues.

    **Validates: Requirements 7.3**
    """

    @given(entry=_registry_entries())
    @settings(max_examples=100)
    def test_detail_contains_all_fields(self, entry):
        """Feature: data-source-registry, Property 4: Detail rendering contains all entry fields"""
        output = render_detail(entry)

        assert entry.data_source in output
        assert entry.name in output
        assert entry.file_path in output
        assert entry.format in output
        assert entry.mapping_status in output
        assert entry.load_status in output
        assert entry.added_at in output
        assert entry.updated_at in output

        if entry.quality_score is not None:
            assert f"{entry.quality_score}%" in output

        if entry.record_count is not None:
            assert f"{entry.record_count:,}" in output

        if entry.issues:
            for issue in entry.issues:
                assert issue in output



# ═══════════════════════════════════════════════════════════════════════════
# Task 7.6 — Property 5: Summary statistics correctly computed
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty5SummaryStatistics:
    """Feature: data-source-registry, Property 5: Summary statistics correctly computed

    For any valid Registry, render_summary SHALL contain total sources count,
    counts per mapping_status and load_status, total records, and average
    quality when applicable.

    **Validates: Requirements 7.4**
    """

    @given(registry=_registries(min_sources=0, max_sources=8))
    @settings(max_examples=100)
    def test_summary_statistics_correct(self, registry):
        """Feature: data-source-registry, Property 5: Summary statistics correctly computed"""
        output = render_summary(registry)

        # Total sources
        total = len(registry.sources)
        assert f"Total sources:     {total}" in output

        # Mapping status counts
        for ms in ("pending", "in_progress", "complete"):
            count = len(registry.by_mapping_status(ms))
            assert f"{ms}: {count}" in output

        # Load status counts
        for ls in ("not_loaded", "loading", "loaded", "failed"):
            count = len(registry.by_load_status(ls))
            assert f"{ls}: {count}" in output

        # Total records
        total_rec = registry.total_records()
        assert f"Total records:     {total_rec:,}" in output

        # Average quality (when at least one source has a score)
        avg_q = registry.average_quality()
        if avg_q is not None:
            assert f"Avg quality score: {round(avg_q)}%" in output


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.7 — Property 6: Recommendations identify issues and load order
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty6Recommendations:
    """Feature: data-source-registry, Property 6: Recommendations correctly identify issues and load order

    recommend_actions SHALL flag low-quality not_loaded sources, pending-mapping
    not_loaded sources, and produce a quality-descending load order.

    **Validates: Requirements 6.2, 6.3, 6.4**
    """

    @given(registry=_registries(min_sources=0, max_sources=8))
    @settings(max_examples=100)
    def test_recommendations_correct(self, registry):
        """Feature: data-source-registry, Property 6: Recommendations identify issues and load order"""
        recs = recommend_actions(registry)
        recs_text = "\n".join(recs)

        # Low quality + not_loaded → recommendation referencing name and score
        for entry in registry.sources:
            if (
                entry.quality_score is not None
                and entry.quality_score < QUALITY_THRESHOLD
                and entry.load_status == "not_loaded"
            ):
                assert entry.data_source in recs_text, (
                    f"Missing low-quality recommendation for {entry.data_source}"
                )
                assert str(entry.quality_score) in recs_text

        # Pending mapping + not_loaded → recommendation
        for entry in registry.sources:
            if entry.mapping_status == "pending" and entry.load_status == "not_loaded":
                # Should have a recommendation mentioning this source
                matching = [r for r in recs if entry.data_source in r and "mapping" in r.lower()]
                assert len(matching) > 0, (
                    f"Missing pending-mapping recommendation for {entry.data_source}"
                )

        # Load order: when multiple scored sources, order is quality descending
        scored = [e for e in registry.sources if e.quality_score is not None]
        if len(scored) > 1:
            order_recs = [r for r in recs if "Recommended load order" in r]
            assert len(order_recs) == 1, "Expected exactly one load order recommendation"
            order_line = order_recs[0]
            ordered = sorted(scored, key=lambda e: e.quality_score, reverse=True)
            for entry in ordered:
                assert entry.data_source in order_line
            # Verify ordering: use full "NAME (score%)" tokens to avoid
            # substring collisions (e.g. "A" matching inside "A0").
            # Use rfind with separator awareness to handle cases like
            # "B (0%)" being a substring of "AB (0%)".
            tokens = [f"{e.data_source} ({e.quality_score}%)" for e in ordered]
            # Verify tokens appear in the correct relative order by checking
            # each consecutive pair
            for i in range(len(tokens) - 1):
                tok_a = tokens[i]
                tok_b = tokens[i + 1]
                # Find the position of each token preceded by start-of-line or ", "
                pos_a = order_line.find(tok_a)
                pos_b = order_line.find(tok_b, pos_a + len(tok_a))
                if pos_b == -1:
                    # tok_b might appear before tok_a due to substring issues;
                    # fall back to checking the comma-separated list directly
                    parts = order_line.split(": ", 1)[1] if ": " in order_line else order_line
                    part_list = [p.strip() for p in parts.split(", ")]
                    idx_a = part_list.index(tok_a) if tok_a in part_list else -1
                    idx_b = part_list.index(tok_b) if tok_b in part_list else -1
                    assert idx_a < idx_b, "Load order not sorted by quality descending"
                else:
                    assert pos_a < pos_b, "Load order not sorted by quality descending"


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.8 — Property 7: Status integration section correct counts/warnings
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty7StatusIntegration:
    """Feature: data-source-registry, Property 7: Status integration section correct counts and warnings

    render_data_sources_section SHALL contain load status counts and quality
    warnings for sources below threshold.

    **Validates: Requirements 8.1, 8.2**
    """

    @given(registry=_registries(min_sources=1, max_sources=8))
    @settings(max_examples=100)
    def test_status_section_counts_and_warnings(self, registry):
        """Feature: data-source-registry, Property 7: Status integration section correct counts and warnings"""
        # Serialize to YAML, then use _read_file injection
        reg_dict = _registry_to_dict(registry)
        yaml_content = serialize_registry_yaml(reg_dict)

        def fake_read(path):
            return yaml_content

        section = render_data_sources_section(
            registry_path="fake.yaml", _read_file=fake_read
        )
        assert section is not None

        # Load status counts
        loaded = len(registry.by_load_status("loaded"))
        not_loaded = len(registry.by_load_status("not_loaded"))
        loading = len(registry.by_load_status("loading"))
        failed = len(registry.by_load_status("failed"))

        assert f"loaded: {loaded}" in section
        assert f"not_loaded: {not_loaded}" in section
        assert f"loading: {loading}" in section
        assert f"failed: {failed}" in section

        # Quality warnings
        low_q = registry.low_quality_sources()
        if low_q:
            assert "Low quality" in section
            for entry in low_q:
                assert entry.data_source in section
        else:
            assert "Low quality" not in section



# ═══════════════════════════════════════════════════════════════════════════
# Task 8.1 — Unit test: CLI argument parsing
# ═══════════════════════════════════════════════════════════════════════════


def _write_registry_file(tmp_dir: Path, content: str):
    """Helper: write a registry YAML file inside tmp_dir/config/."""
    config_dir = tmp_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "data_sources.yaml").write_text(content, encoding="utf-8")


SAMPLE_YAML = """\
version: "1"
sources:
  CUSTOMERS:
    name: Customers
    file_path: data/raw/customers.csv
    format: csv
    record_count: 1000
    file_size_bytes: 50000
    quality_score: 85
    mapping_status: complete
    load_status: loaded
    added_at: "2025-07-01T10:00:00Z"
    updated_at: "2025-07-01T10:00:00Z"
  VENDORS:
    name: Vendors
    file_path: data/raw/vendors.csv
    format: csv
    record_count: 200
    file_size_bytes: 10000
    quality_score: 45
    mapping_status: pending
    load_status: not_loaded
    added_at: "2025-07-01T10:00:00Z"
    updated_at: "2025-07-01T10:00:00Z"
"""


class TestCLIArgumentParsing:
    """Unit tests for CLI argument parsing (no args, --detail, --summary).

    **Validates: Requirements 7.1–7.6**
    """

    def test_no_args_shows_table(self):
        """No arguments → table view with DATA_SOURCE names."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, SAMPLE_YAML)
            buf = StringIO()
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main([])
            assert rc == 0
            output = buf.getvalue()
            assert "CUSTOMERS" in output
            assert "VENDORS" in output

    def test_detail_valid_source(self):
        """--detail CUSTOMERS → detail view for that source."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, SAMPLE_YAML)
            buf = StringIO()
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main(["--detail", "CUSTOMERS"])
            assert rc == 0
            output = buf.getvalue()
            assert "CUSTOMERS" in output
            assert "Customers" in output
            assert "complete" in output

    def test_detail_invalid_source(self):
        """--detail NONEXISTENT → error listing available names, exit 1."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, SAMPLE_YAML)
            err_buf = StringIO()
            with mock.patch.object(sys, "stderr", err_buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main(["--detail", "NONEXISTENT"])
            assert rc == 1
            err_output = err_buf.getvalue()
            assert "NONEXISTENT" in err_output
            assert "CUSTOMERS" in err_output

    def test_summary_view(self):
        """--summary → aggregate statistics."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, SAMPLE_YAML)
            buf = StringIO()
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main(["--summary"])
            assert rc == 0
            output = buf.getvalue()
            assert "Total sources:" in output
            assert "2" in output

    def test_detail_no_argument_exits_nonzero(self):
        """--detail with no argument → argparse error, exit non-zero."""
        err_buf = StringIO()
        with mock.patch.object(sys, "stderr", err_buf), \
             pytest.raises(SystemExit) as exc_info:
            main(["--detail"])
        assert exc_info.value.code != 0


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.2 — Unit test: missing registry file
# ═══════════════════════════════════════════════════════════════════════════


class TestMissingRegistry:
    """Unit tests for missing registry file behavior.

    **Validates: Requirements 7.5, 8.3**
    """

    def test_cli_missing_registry_message_exit_0(self):
        """Missing registry → message + exit 0."""
        with tempfile.TemporaryDirectory() as td:
            buf = StringIO()
            # Point to a non-existent file
            fake_path = os.path.join(td, "config", "data_sources.yaml")
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=fake_path):
                rc = main([])
            assert rc == 0
            output = buf.getvalue()
            assert "No data sources have been registered yet" in output

    def test_status_integration_missing_registry_returns_none(self):
        """render_data_sources_section returns None when file missing."""
        def fake_read(path):
            raise FileNotFoundError(path)

        result = render_data_sources_section(
            registry_path="nonexistent.yaml", _read_file=fake_read
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.3 — Unit test: validation error + empty sources
# ═══════════════════════════════════════════════════════════════════════════


INVALID_YAML = """\
version: "1"
sources:
  BAD:
    name: Bad
    file_path: x
    format: invalid_fmt
    record_count: null
    quality_score: null
    mapping_status: pending
    load_status: not_loaded
    added_at: "2025-01-01T00:00:00Z"
    updated_at: "2025-01-01T00:00:00Z"
"""

EMPTY_SOURCES_YAML = """\
version: "1"
sources:
"""


class TestValidationErrorAndEmptySources:
    """Unit tests for validation errors and empty sources.

    **Validates: Requirements 11.4**
    """

    def test_validation_error_exit_1(self):
        """Validation error (bad format) → descriptive message to stderr + exit 1."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, INVALID_YAML)
            err_buf = StringIO()
            with mock.patch.object(sys, "stderr", err_buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main([])
            assert rc == 1
            err_output = err_buf.getvalue()
            assert "Validation errors" in err_output
            assert "invalid" in err_output.lower()

    def test_validation_error_bad_version_exit_1(self):
        """Validation error (unrecognized version) → error to stderr + exit 1."""
        bad_version_yaml = 'version: "99"\nsources:\n'
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, bad_version_yaml)
            err_buf = StringIO()
            with mock.patch.object(sys, "stderr", err_buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main([])
            assert rc == 1
            err_output = err_buf.getvalue()
            assert "99" in err_output

    def test_validation_error_missing_field_exit_1(self):
        """Validation error (missing required field) → identifies entry + field, exit 1."""
        missing_field_yaml = (
            'version: "1"\n'
            "sources:\n"
            "  BROKEN:\n"
            "    name: Broken\n"
            "    file_path: x\n"
            "    format: csv\n"
        )
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, missing_field_yaml)
            err_buf = StringIO()
            with mock.patch.object(sys, "stderr", err_buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main([])
            assert rc == 1
            err_output = err_buf.getvalue()
            assert "Validation errors" in err_output
            assert "BROKEN" in err_output
            assert "missing" in err_output.lower()

    def test_empty_sources_table(self):
        """Empty sources → table with header but no data rows."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, EMPTY_SOURCES_YAML)
            buf = StringIO()
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main([])
            assert rc == 0
            output = buf.getvalue()
            assert "Data Source Registry" in output

    def test_empty_sources_summary_zeros(self):
        """Empty sources → summary with all zeros."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _write_registry_file(tmp, EMPTY_SOURCES_YAML)
            buf = StringIO()
            with mock.patch.object(sys, "stdout", buf), \
                 mock.patch("os.path.join", return_value=str(tmp / "config" / "data_sources.yaml")):
                rc = main(["--summary"])
            assert rc == 0
            output = buf.getvalue()
            assert "Total sources:     0" in output
            assert "Total records:     0" in output


# ═══════════════════════════════════════════════════════════════════════════
# Task 8.4 — Unit test: default entry values and absent issues
# ═══════════════════════════════════════════════════════════════════════════


class TestDefaultEntryValues:
    """Unit tests for default entry values and absent issues field.

    **Validates: Requirements 1.5**
    """

    def test_default_quality_null(self):
        """Default quality_score is null (None)."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=None,
            file_size_bytes=None,
            quality_score=None,
            mapping_status="pending",
            load_status="not_loaded",
            added_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert entry.quality_score is None

    def test_default_mapping_pending(self):
        """Default mapping_status is 'pending'."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=None,
            file_size_bytes=None,
            quality_score=None,
            mapping_status="pending",
            load_status="not_loaded",
            added_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert entry.mapping_status == "pending"

    def test_default_load_not_loaded(self):
        """Default load_status is 'not_loaded'."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=None,
            file_size_bytes=None,
            quality_score=None,
            mapping_status="pending",
            load_status="not_loaded",
            added_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert entry.load_status == "not_loaded"

    def test_issues_absent_treated_as_empty(self):
        """When issues field is absent (None), it is treated as empty."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=100,
            file_size_bytes=5000,
            quality_score=80,
            mapping_status="complete",
            load_status="loaded",
            added_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert entry.issues is None
        # Detail rendering should not show "Issues:" section
        output = render_detail(entry)
        assert "Issues:" not in output

    def test_issues_empty_list_no_issues_shown(self):
        """When issues is an empty list, no issues section in detail."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=100,
            file_size_bytes=5000,
            quality_score=80,
            mapping_status="complete",
            load_status="loaded",
            added_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            issues=[],
        )
        output = render_detail(entry)
        assert "Issues:" not in output

    def test_yaml_parse_default_entry_values(self):
        """Parsing a YAML entry with null quality, pending mapping, not_loaded produces correct defaults."""
        yaml_content = (
            'version: "2"\n'
            "sources:\n"
            "  NEW_SOURCE:\n"
            "    name: New Source\n"
            "    file_path: data/raw/new.csv\n"
            "    format: csv\n"
            "    record_count: 500\n"
            "    file_size_bytes: 25000\n"
            "    quality_score: null\n"
            "    mapping_status: pending\n"
            "    load_status: not_loaded\n"
            '    added_at: "2025-07-01T10:00:00Z"\n'
            '    updated_at: "2025-07-01T10:00:00Z"\n'
        )
        raw = parse_registry_yaml(yaml_content)
        registry = _dict_to_registry(raw)
        assert len(registry.sources) == 1
        entry = registry.sources[0]
        assert entry.quality_score is None
        assert entry.mapping_status == "pending"
        assert entry.load_status == "not_loaded"

    def test_yaml_parse_absent_issues_field(self):
        """Parsing a YAML entry without the issues field produces a RegistryEntry with issues as None."""
        yaml_content = (
            'version: "2"\n'
            "sources:\n"
            "  NO_ISSUES:\n"
            "    name: No Issues Source\n"
            "    file_path: data/raw/clean.csv\n"
            "    format: csv\n"
            "    record_count: 1000\n"
            "    file_size_bytes: 50000\n"
            "    quality_score: 90\n"
            "    mapping_status: complete\n"
            "    load_status: loaded\n"
            '    added_at: "2025-07-01T10:00:00Z"\n'
            '    updated_at: "2025-07-01T10:00:00Z"\n'
        )
        raw = parse_registry_yaml(yaml_content)
        registry = _dict_to_registry(raw)
        assert len(registry.sources) == 1
        entry = registry.sources[0]
        # issues field absent → treated as None (no crash)
        assert entry.issues is None
        # Detail rendering should not crash and should not show Issues section
        output = render_detail(entry)
        assert "Issues:" not in output

# ═══════════════════════════════════════════════════════════════════════════
# Task 1.3 — Unit tests: registry validation with test_load_status fields
# ═══════════════════════════════════════════════════════════════════════════


class TestRegistryValidationTestLoadStatus:
    """Unit tests for registry validation with test_load_status and test_entity_count fields.

    **Validates: Requirements 8.1**
    """

    def _make_valid_entry(self, **overrides):
        """Helper: create a valid source entry dict with optional overrides."""
        entry = {
            "name": "Test Source",
            "file_path": "data/raw/test.csv",
            "format": "csv",
            "record_count": 1000,
            "quality_score": 85,
            "mapping_status": "complete",
            "load_status": "loaded",
            "added_at": "2025-07-01T10:00:00Z",
            "updated_at": "2025-07-01T10:00:00Z",
        }
        entry.update(overrides)
        return entry

    def test_valid_test_load_status_complete(self):
        """validate_registry accepts test_load_status='complete'."""
        raw = {
            "version": "1",
            "sources": {
                "TEST": self._make_valid_entry(test_load_status="complete", test_entity_count=950),
            },
        }
        errors = validate_registry(raw)
        assert errors == []

    def test_valid_test_load_status_skipped(self):
        """validate_registry accepts test_load_status='skipped'."""
        raw = {
            "version": "1",
            "sources": {
                "TEST": self._make_valid_entry(test_load_status="skipped"),
            },
        }
        errors = validate_registry(raw)
        assert errors == []

    def test_no_test_load_status_backward_compatible(self):
        """validate_registry accepts entries without test_load_status (backward compatible)."""
        raw = {
            "version": "1",
            "sources": {
                "TEST": self._make_valid_entry(),
            },
        }
        errors = validate_registry(raw)
        assert errors == []

    def test_invalid_test_load_status_rejected(self):
        """validate_registry rejects invalid test_load_status values."""
        raw = {
            "version": "1",
            "sources": {
                "TEST": self._make_valid_entry(test_load_status="invalid_status"),
            },
        }
        errors = validate_registry(raw)
        assert len(errors) == 1
        assert "test_load_status" in errors[0]
        assert "invalid_status" in errors[0]

    def test_render_detail_shows_test_load_status(self):
        """render_detail displays test_load_status when present."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test Source",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=1000,
            file_size_bytes=50000,
            quality_score=85,
            mapping_status="complete",
            load_status="loaded",
            added_at="2025-07-01T10:00:00Z",
            updated_at="2025-07-01T10:00:00Z",
            test_load_status="complete",
            test_entity_count=950,
        )
        output = render_detail(entry)
        assert "Test Load:" in output
        assert "complete" in output
        assert "Test Entities:" in output
        assert "950" in output

    def test_render_detail_shows_dash_when_test_fields_absent(self):
        """render_detail displays '-' for test_load_status and test_entity_count when None."""
        entry = RegistryEntry(
            data_source="TEST",
            name="Test Source",
            file_path="data/raw/test.csv",
            format="csv",
            record_count=1000,
            file_size_bytes=50000,
            quality_score=85,
            mapping_status="complete",
            load_status="loaded",
            added_at="2025-07-01T10:00:00Z",
            updated_at="2025-07-01T10:00:00Z",
        )
        output = render_detail(entry)
        assert "Test Load:      -" in output
        assert "Test Entities:  -" in output
