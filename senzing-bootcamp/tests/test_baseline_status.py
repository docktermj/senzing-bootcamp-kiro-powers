"""Property-based and unit tests for baseline_status.py using Hypothesis.

Feature: er-baseline-status-summary

This module validates the ER Baseline Status Summary script. Property tests are
tagged with the correctness property they cover and the requirement clause each
validates. All fixtures are synthetic and PII-free (Requirement 5.2): the
generated ERStatistics objects carry only non-negative integer counts and
ISO-ish timestamp strings, never row-level data.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

# Speed override: these property tests each materialize a temp workspace on disk
# per example, so we run fewer examples than the ``fast`` baseline (5) for quicker
# local iteration. This is an intentional non-baseline count, not a restatement of
# the profile default.
_REDUCED_EXAMPLES = 3

# Make scripts importable (scripts are not a package).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import compare_results  # noqa: E402 — patched to prove accept_baseline is never called
from baseline_status import (  # noqa: E402
    BaselineStatus,
    BaselineSummary,
    baseline_path,
    build_status,
    build_summary,
    main,
    read_baseline_metadata,
    render_summary,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Fields that make up the light-metadata contract surfaced by a present row.
_LIGHT_FIELDS = ("captured_at", "record_count", "entity_count")

# Baseline fields that must never be surfaced by the light-metadata reader.
_HEAVY_FIELDS = ("match_count", "possible_match_count", "relationship_count")


def st_data_source_key() -> st.SearchStrategy[str]:
    """Generate valid registry keys matching ``^[A-Z][A-Z0-9_]*$``."""
    return st.from_regex(r"[A-Z][A-Z0-9_]{0,29}", fullmatch=True)


@st.composite
def st_captured_at(draw) -> str:
    """Generate a synthetic ISO-ish acceptance timestamp string (no real PII)."""
    year = draw(st.integers(min_value=2000, max_value=2099))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"


@st.composite
def st_er_statistics(draw) -> dict:
    """Generate a synthetic, valid ERStatistics JSON object (PII-free).

    Produces the full ERStatistics shape written by the Phase 3 flow /
    ``accept_baseline``: a datasource key, non-negative integer counts for every
    count field, and an ISO-ish ``captured_at`` timestamp. All content is
    synthetic — counts and a timestamp only, never row-level data.
    """
    count = st.integers(min_value=0, max_value=1_000_000)
    return {
        "datasource": draw(st_data_source_key()),
        "entity_count": draw(count),
        "record_count": draw(count),
        "match_count": draw(count),
        "possible_match_count": draw(count),
        "relationship_count": draw(count),
        "captured_at": draw(st_captured_at()),
    }


# Valid, minimal registry entry values (synthetic, PII-free). Every entry uses
# the same fixed field values so the generated document always satisfies
# ``data_sources.validate_registry`` (required fields present, enum values valid);
# only the set of source keys and the present/absent subset vary per example.
def _registry_entry_yaml(key: str) -> str:
    """Render one valid ``sources`` entry (all required fields, valid enums)."""
    return (
        f"  {key}:\n"
        f'    name: "Synthetic Source {key}"\n'
        f'    file_path: "data/raw/{key.lower()}.csv"\n'
        f"    format: csv\n"
        f"    record_count: 100\n"
        f"    quality_score: 90\n"
        f"    mapping_status: complete\n"
        f"    load_status: loaded\n"
        f'    added_at: "2025-01-01T00:00:00Z"\n'
        f'    updated_at: "2025-01-01T00:00:00Z"\n'
    )


@st.composite
def st_registry(draw, sources=None):
    """Generate a valid, minimal-YAML registry document plus a baseline subset.

    Builds a registry document using only the restricted YAML subset understood
    by ``data_sources.parse_registry_yaml`` (so it round-trips through the parser)
    with every source carrying all required fields and valid enum values, so the
    document always passes ``data_sources.validate_registry``. Also chooses a
    subset of the source keys that are flagged as having a materialized baseline.

    Args:
        draw: Hypothesis draw callable (supplied by ``@st.composite``).
        sources: Optional explicit list of source keys to use; when ``None`` a
            unique list of keys is generated.

    Returns:
        A ``(keys, present, yaml_text)`` tuple where ``keys`` is the ordered list
        of registered source keys, ``present`` is the set of keys flagged as
        having a baseline, and ``yaml_text`` is the registry document. All content
        is synthetic and PII-free.
    """
    if sources is None:
        keys = draw(
            st.lists(st_data_source_key(), min_size=0, max_size=6, unique=True)
        )
    else:
        keys = list(sources)

    present = {key for key in keys if draw(st.booleans())}

    lines = ['version: "2"', "sources:"]
    for key in keys:
        lines.append(_registry_entry_yaml(key).rstrip("\n"))
    yaml_text = "\n".join(lines) + "\n"

    return keys, present, yaml_text


@st.composite
def st_malformed_baseline(draw) -> str:
    """Generate adversarial baseline file contents that are not a JSON object.

    Covers the malformed cases named by Property 5 — each is either invalid JSON
    or valid JSON that is not an object, so ``read_baseline_metadata`` returns
    ``None`` and the source is classified ``unreadable``. All content is
    synthetic and PII-free.

    Returns:
        A string to write as a baseline file: an empty string, non-JSON text, a
        JSON array, a JSON scalar, or a truncated (invalid) JSON object.
    """
    kind = draw(
        st.sampled_from(
            ["empty", "non_json", "json_array", "json_scalar", "truncated_object"]
        )
    )
    if kind == "empty":
        # Empty file exists but json.loads fails -> unreadable.
        return ""
    if kind == "non_json":
        # Arbitrary text with no '{' can never parse as a JSON object; whatever it
        # parses to (nothing, or a scalar) is not a dict -> unreadable.
        return draw(
            st.text(
                alphabet=st.characters(
                    blacklist_characters="{", blacklist_categories=("Cs",)
                ),
                max_size=40,
            )
        )
    if kind == "json_array":
        # Valid JSON but not an object.
        return json.dumps(draw(st.lists(st.integers(), max_size=5)))
    if kind == "json_scalar":
        # Valid JSON but not an object (number / string / bool / null).
        scalar = draw(
            st.one_of(st.integers(), st.text(max_size=10), st.booleans(), st.none())
        )
        return json.dumps(scalar)
    # truncated_object: syntactically invalid JSON object.
    return '{"datasource": "X", "record_count":'


@st.composite
def st_invalid_registry(draw) -> tuple[bool, str | None]:
    """Generate an absent, empty, or invalid registry for Property 6.

    Each variant reliably drives ``read_registry_sources`` to ``None`` (and thus
    ``build_summary`` to ``registry_present=False``): an absent file raises
    ``FileNotFoundError``, and every written variant either fails to parse or
    fails ``data_sources.validate_registry`` (missing ``version``, unknown
    ``version``, or missing/invalid ``sources``). All content is synthetic and
    PII-free.

    Returns:
        A ``(should_write, content)`` tuple. When ``should_write`` is ``False``
        no registry file is created (the absent case) and ``content`` is ``None``;
        otherwise ``content`` is the invalid text to write to the registry path.
    """
    kind = draw(
        st.sampled_from(
            [
                "absent",
                "empty",
                "non_yaml_garbage",
                "missing_version",
                "wrong_version",
                "missing_sources",
            ]
        )
    )
    if kind == "absent":
        # No file on disk -> FileNotFoundError -> registry_present=False.
        return False, None
    if kind == "empty":
        # Empty document -> no 'version'/'sources' -> validation error.
        return True, ""
    if kind == "non_yaml_garbage":
        # Arbitrary prose with no top-level 'version'/'sources' keys.
        return True, "this is not a registry document at all\n"
    if kind == "missing_version":
        # Has sources but no version -> "Missing required field: 'version'".
        return True, "sources:\n"
    if kind == "wrong_version":
        # Unknown schema version -> version enum error.
        version = draw(st.integers(min_value=3, max_value=999))
        return True, f'version: "{version}"\nsources:\n'
    # missing_sources: has version but no sources -> "Missing required field: 'sources'".
    return True, 'version: "2"\n'


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestBaselineStatus:
    """Property and unit tests for baseline_status.py.

    Validates:
    - Requirement 1.2 (Property 2): present rows carry light metadata
      (``captured_at``, ``record_count``, ``entity_count``) equal to the file's
      values and surface none of the other baseline fields.
    - Requirement 1.3 (Property 3): missing sources are marked ``present=False``
      and carry a non-empty ``remediation`` string that references the existing
      ``accept_baseline`` path.
    """

    # Feature: er-baseline-status-summary, Property 2: Present rows carry light
    # metadata and never the full contents — for any baseline written as a valid
    # ERStatistics JSON object, the present row carries captured_at, record_count,
    # and entity_count equal to the file's values, and surfaces none of the other
    # baseline fields (match_count, possible_match_count, relationship_count).
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(stats=st_er_statistics())
    def test_present_row_carries_light_metadata_only(self, stats: dict) -> None:
        """Property 2: light-metadata contract. Validates: Requirements 1.2."""
        raw = json.dumps(stats)
        # Drive the light-metadata reader with an injectable reader so the
        # property is validated without touching disk.
        metadata = read_baseline_metadata(
            Path("config/er_baseline_synthetic.json"),
            read_text=lambda _path: raw,
        )

        assert metadata is not None

        # The three light fields equal the file's values.
        assert metadata["captured_at"] == stats["captured_at"]
        assert metadata["record_count"] == stats["record_count"]
        assert metadata["entity_count"] == stats["entity_count"]

        # None of the other baseline fields are surfaced.
        assert set(metadata.keys()) == set(_LIGHT_FIELDS)
        for heavy_field in _HEAVY_FIELDS:
            assert heavy_field not in metadata

    # Feature: er-baseline-status-summary, Property 3: Missing sources are marked
    # and carry a remediation hint — for any registered Data_Source that has no
    # baseline file, its row has present false and a non-empty remediation string
    # that references the existing accept_baseline path for creating one.
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(data_source=st_data_source_key())
    def test_missing_source_marked_with_remediation(self, data_source: str) -> None:
        """Property 3: missing-source remediation. Validates: Requirements 1.3."""
        # Inject a read_text that raises FileNotFoundError for any path, so every
        # source appears to have no baseline file (no disk access).
        def _missing(_path) -> str:
            raise FileNotFoundError(_path)

        status = build_status(data_source, read_text=_missing)

        assert status.present is False
        assert isinstance(status.remediation, str)
        assert status.remediation != ""
        assert "accept_baseline" in status.remediation

    # Feature: er-baseline-status-summary, Property 1: Every registered source
    # appears exactly once with a correct presence flag — for any registry and any
    # subset of sources whose baselines exist at baseline_path, build_summary
    # produces exactly one row per registered source, in registry order, with
    # present true iff that source's baseline_path file exists and reads as a JSON
    # object.
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(registry=st_registry(), stats=st_er_statistics())
    def test_every_source_appears_once_with_correct_presence(
        self, registry: tuple, stats: dict
    ) -> None:
        """Property 1: completeness + presence flags. Validates: Requirements 1.1, 3.1, 3.2."""
        keys, present, yaml_text = registry

        # Materialize a real temp workspace on disk and drive build_summary against
        # it so the location convention (baseline_path) and the registry-derived
        # source list are exercised for real. A raw tempdir + os.chdir in
        # try/finally keeps the property free of a function-scoped tmp_path fixture
        # (which Hypothesis's @given would flag), mirroring the repo's other
        # filesystem property tests.
        original_cwd = os.getcwd()
        workspace = tempfile.mkdtemp()
        try:
            os.chdir(workspace)
            config_dir = Path("config")
            config_dir.mkdir()
            (config_dir / "data_sources.yaml").write_text(yaml_text, encoding="utf-8")

            # Materialize a valid ERStatistics baseline at baseline_path(key) for
            # exactly the chosen present subset; leave the rest absent.
            for key in present:
                baseline_path(key).write_text(json.dumps(stats), encoding="utf-8")

            summary = build_summary()
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(workspace, ignore_errors=True)

        # The registry was present and parseable.
        assert summary.registry_present is True

        # Exactly one row per registered source, in registry order.
        assert [row.data_source for row in summary.statuses] == keys

        # Each row's present flag is true iff its baseline file was materialized.
        for row in summary.statuses:
            assert row.present is (row.data_source in present)

    # Feature: er-baseline-status-summary, Property 5: Missing or malformed
    # baselines degrade without raising — for any registered source whose baseline
    # is missing, empty, non-JSON, JSON-but-not-an-object, or unreadable,
    # build_summary never raises, marks that source as missing or unreadable, and
    # still reports every other source correctly.
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(registry=st_registry(), data=st.data())
    def test_malformed_or_missing_baselines_degrade_without_raising(
        self, registry: tuple, data: st.DataObject
    ) -> None:
        """Property 5: degrade-without-raising. Validates: Requirements 4.1."""
        keys, _present, yaml_text = registry

        # Assign each registered source to exactly one category: a valid baseline,
        # a malformed baseline, or no baseline at all. Draw the per-source choices
        # with st.data() so the partition and the adversarial contents are shrinkable.
        categories = {
            key: data.draw(
                st.sampled_from(["valid", "malformed", "absent"]),
                label=f"category:{key}",
            )
            for key in keys
        }
        valid_stats = {
            key: data.draw(st_er_statistics(), label=f"valid:{key}")
            for key, category in categories.items()
            if category == "valid"
        }
        malformed_content = {
            key: data.draw(st_malformed_baseline(), label=f"malformed:{key}")
            for key, category in categories.items()
            if category == "malformed"
        }

        # Materialize a real temp workspace and drive build_summary against it so
        # the location convention (baseline_path) is exercised for real. A raw
        # tempdir + os.chdir in try/finally keeps the property free of a
        # function-scoped tmp_path fixture, mirroring the other filesystem tests.
        original_cwd = os.getcwd()
        workspace = tempfile.mkdtemp()
        try:
            os.chdir(workspace)
            config_dir = Path("config")
            config_dir.mkdir()
            (config_dir / "data_sources.yaml").write_text(yaml_text, encoding="utf-8")

            for key, stats in valid_stats.items():
                baseline_path(key).write_text(json.dumps(stats), encoding="utf-8")
            for key, content in malformed_content.items():
                baseline_path(key).write_text(content, encoding="utf-8")
            # 'absent' sources: no file written.

            # Never raises (implicit — any exception fails the test).
            summary = build_summary()
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(workspace, ignore_errors=True)

        # The registry parsed, and every registered source is reported once, in order.
        assert summary.registry_present is True
        assert [row.data_source for row in summary.statuses] == keys

        # Each source is classified correctly and independently of the others.
        for row in summary.statuses:
            category = categories[row.data_source]
            if category == "valid":
                assert row.present is True
                assert row.unreadable is False
            elif category == "malformed":
                # Malformed baseline exists but cannot be parsed as a JSON object.
                assert row.present is False
                assert row.unreadable is True
            else:  # absent
                assert row.present is False
                assert row.unreadable is False
                assert isinstance(row.remediation, str) and row.remediation != ""

    # Feature: er-baseline-status-summary, Property 4: The summary is read-only —
    # for any registry and any mix of present, missing, and malformed baseline
    # files, running the summary leaves the workspace byte-for-byte unchanged: no
    # file is created, modified, or deleted, and accept_baseline is never invoked.
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(registry=st_registry(), data=st.data())
    def test_summary_is_read_only(
        self, registry: tuple, data: st.DataObject
    ) -> None:
        """Property 4: read-only guarantee. Validates: Requirements 2.3."""
        keys, _present, yaml_text = registry

        # Assign each registered source to exactly one category: a valid baseline,
        # a malformed baseline, or no baseline at all, so the run exercises the
        # present / missing / unreadable paths together (as Property 4 requires).
        categories = {
            key: data.draw(
                st.sampled_from(["valid", "malformed", "absent"]),
                label=f"category:{key}",
            )
            for key in keys
        }
        valid_stats = {
            key: data.draw(st_er_statistics(), label=f"valid:{key}")
            for key, category in categories.items()
            if category == "valid"
        }
        malformed_content = {
            key: data.draw(st_malformed_baseline(), label=f"malformed:{key}")
            for key, category in categories.items()
            if category == "malformed"
        }

        def _snapshot(root: Path) -> dict[str, bytes]:
            """Map every file path under ``root`` to its exact bytes."""
            snapshot: dict[str, bytes] = {}
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    snapshot[str(path.relative_to(root))] = path.read_bytes()
            return snapshot

        # Materialize a real temp workspace and run the summary against it. A raw
        # tempdir + os.chdir in try/finally keeps the property free of a
        # function-scoped tmp_path fixture, mirroring the other filesystem tests.
        original_cwd = os.getcwd()
        workspace = tempfile.mkdtemp()
        try:
            os.chdir(workspace)
            root = Path(workspace)
            config_dir = Path("config")
            config_dir.mkdir()
            (config_dir / "data_sources.yaml").write_text(yaml_text, encoding="utf-8")

            for key, stats in valid_stats.items():
                baseline_path(key).write_text(json.dumps(stats), encoding="utf-8")
            for key, content in malformed_content.items():
                baseline_path(key).write_text(content, encoding="utf-8")
            # 'absent' sources: no file written.

            # Snapshot the whole workspace before running the summary.
            before = _snapshot(root)

            # Patch accept_baseline so any invocation fails the test: a read-only
            # summary must never call it.
            def _fail_if_called(*_args, **_kwargs):
                raise AssertionError(
                    "accept_baseline was invoked; the summary must be read-only"
                )

            with patch.object(
                compare_results, "accept_baseline", side_effect=_fail_if_called
            ):
                exit_code = main(["--registry", "config/data_sources.yaml"])

            # Snapshot again after the run.
            after = _snapshot(root)
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(workspace, ignore_errors=True)

        # Clean run, and the workspace is byte-for-byte unchanged: same set of
        # files, same contents (nothing created, modified, or deleted).
        assert exit_code == 0
        assert set(after.keys()) == set(before.keys())
        assert after == before

    # Feature: er-baseline-status-summary, Property 6: A missing or invalid
    # registry yields no sources and a clean result — for any absent, empty, or
    # invalid registry content, build_summary returns registry_present false with
    # an empty statuses list, and main returns cleanly without raising.
    @settings(max_examples=_REDUCED_EXAMPLES)
    @given(invalid_registry=st_invalid_registry())
    def test_missing_or_invalid_registry_yields_clean_empty_result(
        self, invalid_registry: tuple
    ) -> None:
        """Property 6: missing/invalid registry path. Validates: Requirements 4.2."""
        should_write, content = invalid_registry
        registry_rel = "config/data_sources.yaml"

        # Materialize a real temp workspace so build_summary and main resolve the
        # relative registry path exactly as they would in a real run. For the
        # absent case no registry file is written; for the invalid cases the bad
        # content is written to config/data_sources.yaml. A raw tempdir +
        # os.chdir in try/finally mirrors the other filesystem property tests.
        original_cwd = os.getcwd()
        workspace = tempfile.mkdtemp()
        try:
            os.chdir(workspace)
            config_dir = Path("config")
            config_dir.mkdir()
            if should_write:
                (config_dir / "data_sources.yaml").write_text(
                    content, encoding="utf-8"
                )
            # else: absent registry — write no file at all.

            # build_summary never raises and degrades to an empty, absent report.
            summary = build_summary(registry_rel)

            # main returns cleanly (0) without raising for the no-sources case.
            exit_code = main(["--registry", registry_rel])
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(workspace, ignore_errors=True)

        # No sources and a clean, absent-registry result (Req 4.2).
        assert summary.registry_present is False
        assert summary.statuses == []
        assert exit_code == 0


# ---------------------------------------------------------------------------
# Example (concrete, non-property) tests
# ---------------------------------------------------------------------------


def _write_registry(config_dir: Path, keys: list[str]) -> None:
    """Write a valid, minimal registry document for ``keys`` under ``config_dir``.

    Args:
        config_dir: The ``config`` directory to write ``data_sources.yaml`` into.
        keys: Ordered list of synthetic, PII-free source keys to register.
    """
    lines = ['version: "2"', "sources:"]
    for key in keys:
        lines.append(_registry_entry_yaml(key).rstrip("\n"))
    yaml_text = "\n".join(lines) + "\n"
    (config_dir / "data_sources.yaml").write_text(yaml_text, encoding="utf-8")


def _write_baseline(key: str, stats: dict) -> None:
    """Materialize a valid ERStatistics baseline at ``baseline_path(key)``.

    Args:
        key: The registered data-source key the baseline belongs to.
        stats: A synthetic, PII-free ERStatistics dict to serialize as JSON.
    """
    baseline_path(key).write_text(json.dumps(stats), encoding="utf-8")


def _stats(datasource: str, *, entities: int, records: int, captured_at: str) -> dict:
    """Build a synthetic, PII-free ERStatistics object for a fixture baseline.

    Args:
        datasource: The data-source key the statistics describe.
        entities: The resolved entity count.
        records: The loaded record count.
        captured_at: The ISO-ish acceptance timestamp.

    Returns:
        A full ERStatistics dict (counts and a timestamp only, no row-level data).
    """
    return {
        "datasource": datasource,
        "entity_count": entities,
        "record_count": records,
        "match_count": 10,
        "possible_match_count": 2,
        "relationship_count": 5,
        "captured_at": captured_at,
    }


class TestBaselineStatusExamples:
    """Concrete example tests for the Requirement 5.1 scenarios.

    These pin the exact scenarios Requirement 5.1 names with fixed, synthetic
    (PII-free) inputs rather than generated ones:

    - Requirement 5.1 / 5.2: all sources have baselines; a mix of present and
      missing; an unreadable baseline; a missing registry.
    - Requirement 2.1: an on-demand CLI run via ``main([...])``.
    - Requirement 4.2: the missing-registry render and clean return.
    """

    def test_all_sources_have_baselines(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """All registered sources have a baseline — every row present with metadata.

        Validates: Requirements 5.1, 5.2.
        """
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        keys = ["CUSTOMERS_CRM", "VENDORS_ERP"]
        _write_registry(config_dir, keys)
        _write_baseline(
            "CUSTOMERS_CRM",
            _stats("CUSTOMERS_CRM", entities=812, records=1000, captured_at="2025-07-01T10:00:00Z"),
        )
        _write_baseline(
            "VENDORS_ERP",
            _stats("VENDORS_ERP", entities=340, records=400, captured_at="2025-08-15T12:30:00Z"),
        )

        summary = build_summary()

        assert summary.registry_present is True
        assert [row.data_source for row in summary.statuses] == keys
        for row in summary.statuses:
            assert row.present is True
            assert row.unreadable is False
            assert row.remediation is None

        crm = summary.statuses[0]
        assert crm.captured_at == "2025-07-01T10:00:00Z"
        assert crm.record_count == 1000
        assert crm.entity_count == 812

        erp = summary.statuses[1]
        assert erp.captured_at == "2025-08-15T12:30:00Z"
        assert erp.record_count == 400
        assert erp.entity_count == 340

    def test_mix_of_present_and_missing(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A mix of present and missing — correct classification and remediation.

        Validates: Requirements 5.1, 5.2.
        """
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        keys = ["CUSTOMERS_CRM", "VENDORS_ERP", "PARTNERS_API"]
        _write_registry(config_dir, keys)
        # Only the first source gets a baseline; the other two are missing.
        _write_baseline(
            "CUSTOMERS_CRM",
            _stats("CUSTOMERS_CRM", entities=812, records=1000, captured_at="2025-07-01T10:00:00Z"),
        )

        summary = build_summary()

        assert summary.registry_present is True
        assert [row.data_source for row in summary.statuses] == keys

        present_row = summary.statuses[0]
        assert present_row.present is True
        assert present_row.record_count == 1000

        for missing_row in summary.statuses[1:]:
            assert missing_row.present is False
            assert missing_row.unreadable is False
            assert isinstance(missing_row.remediation, str)
            assert missing_row.remediation != ""
            assert "accept_baseline" in missing_row.remediation

    def test_unreadable_baseline_keeps_siblings_correct(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A corrupt file yields an unreadable row while siblings stay correct.

        Validates: Requirements 5.1, 5.2.
        """
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        keys = ["CUSTOMERS_CRM", "VENDORS_ERP", "PARTNERS_API"]
        _write_registry(config_dir, keys)
        # A valid baseline, a corrupt (truncated JSON) baseline, and a missing one.
        _write_baseline(
            "CUSTOMERS_CRM",
            _stats("CUSTOMERS_CRM", entities=812, records=1000, captured_at="2025-07-01T10:00:00Z"),
        )
        baseline_path("VENDORS_ERP").write_text(
            '{"datasource": "VENDORS_ERP", "record_count":', encoding="utf-8"
        )

        summary = build_summary()

        assert summary.registry_present is True
        assert [row.data_source for row in summary.statuses] == keys

        valid_row, corrupt_row, missing_row = summary.statuses

        assert valid_row.present is True
        assert valid_row.unreadable is False
        assert valid_row.record_count == 1000

        assert corrupt_row.present is False
        assert corrupt_row.unreadable is True

        assert missing_row.present is False
        assert missing_row.unreadable is False
        assert "accept_baseline" in (missing_row.remediation or "")

    def test_missing_registry_renders_clean_message(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A missing registry renders the no-sources message and returns cleanly.

        Validates: Requirements 4.2, 5.1.
        """
        monkeypatch.chdir(tmp_path)
        # No config/data_sources.yaml is created — the registry is absent.

        summary = build_summary()

        assert summary.registry_present is False
        assert summary.statuses == []
        assert render_summary(summary) == "No data sources have been registered yet."

    def test_on_demand_cli_run_prints_summary(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """An on-demand CLI run returns 0 and prints the rendered summary.

        Validates: Requirements 2.1, 5.1.
        """
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        keys = ["CUSTOMERS_CRM", "VENDORS_ERP"]
        _write_registry(config_dir, keys)
        _write_baseline(
            "CUSTOMERS_CRM",
            _stats("CUSTOMERS_CRM", entities=812, records=1000, captured_at="2025-07-01T10:00:00Z"),
        )
        # VENDORS_ERP intentionally has no baseline.

        exit_code = main(["--registry", "config/data_sources.yaml"])

        assert exit_code == 0

        printed = capsys.readouterr().out
        expected = render_summary(build_summary("config/data_sources.yaml"))
        assert printed.strip() == expected.strip()

        # The rendered output surfaces both sources with the right markers.
        assert "CUSTOMERS_CRM: present" in printed
        assert "captured_at=2025-07-01T10:00:00Z" in printed
        assert "VENDORS_ERP: MISSING" in printed


# ---------------------------------------------------------------------------
# Rendering unit tests (pure, in-memory)
# ---------------------------------------------------------------------------


class TestRenderSummary:
    """Unit tests for ``render_summary`` (Task 11.2).

    These are pure, in-memory tests that construct ``BaselineSummary`` /
    ``BaselineStatus`` objects directly (no disk, no ``build_summary``) to
    isolate the rendering contract:

    - Requirement 1.1: one line per registered source with the correct
      present/missing/unreadable marker.
    - Requirement 1.2: present rows surface only counts and a timestamp — never
      row-level data.
    - Requirement 1.3: missing rows carry a ``MISSING`` marker and the
      remediation hint.
    """

    def test_present_row_shows_present_marker_and_light_metadata(self) -> None:
        """A present row renders the present marker with its timestamp/counts.

        Validates: Requirements 1.1, 1.2.
        """
        summary = BaselineSummary(
            registry_present=True,
            statuses=[
                BaselineStatus(
                    data_source="CUSTOMERS_CRM",
                    present=True,
                    captured_at="2025-07-01T10:00:00Z",
                    record_count=1000,
                    entity_count=812,
                )
            ],
        )

        rendered = render_summary(summary)
        lines = rendered.splitlines()

        # Exactly one source line follows the two-line header.
        source_lines = [line for line in lines if line.startswith("CUSTOMERS_CRM")]
        assert len(source_lines) == 1

        line = source_lines[0]
        assert "CUSTOMERS_CRM: present" in line
        assert "captured_at=2025-07-01T10:00:00Z" in line
        assert "records=1000" in line
        assert "entities=812" in line

    def test_missing_row_shows_missing_marker_and_remediation(self) -> None:
        """A missing row renders the MISSING marker plus the remediation text.

        Validates: Requirements 1.1, 1.3.
        """
        summary = BaselineSummary(
            registry_present=True,
            statuses=[
                BaselineStatus(
                    data_source="VENDORS_ERP",
                    present=False,
                    remediation="run accept_baseline to create one",
                )
            ],
        )

        rendered = render_summary(summary)
        source_lines = [
            line for line in rendered.splitlines() if line.startswith("VENDORS_ERP")
        ]

        assert len(source_lines) == 1
        line = source_lines[0]
        assert "VENDORS_ERP: MISSING" in line
        assert "run accept_baseline to create one" in line

    def test_unreadable_row_shows_unreadable_marker(self) -> None:
        """An unreadable row renders the UNREADABLE marker.

        Validates: Requirements 1.1.
        """
        summary = BaselineSummary(
            registry_present=True,
            statuses=[
                BaselineStatus(
                    data_source="PARTNERS_API",
                    present=False,
                    unreadable=True,
                )
            ],
        )

        rendered = render_summary(summary)
        source_lines = [
            line for line in rendered.splitlines() if line.startswith("PARTNERS_API")
        ]

        assert len(source_lines) == 1
        assert source_lines[0] == "PARTNERS_API: UNREADABLE"

    def test_empty_registry_renders_single_no_sources_line(self) -> None:
        """An absent registry renders exactly the no-sources sentinel line.

        Validates: Requirements 1.1.
        """
        summary = BaselineSummary(registry_present=False, statuses=[])

        assert render_summary(summary) == "No data sources have been registered yet."

    def test_one_line_per_source_for_mixed_summary(self) -> None:
        """A mixed summary renders exactly one line per registered source.

        Validates: Requirements 1.1, 1.2, 1.3.
        """
        summary = BaselineSummary(
            registry_present=True,
            statuses=[
                BaselineStatus(
                    data_source="CUSTOMERS_CRM",
                    present=True,
                    captured_at="2025-07-01T10:00:00Z",
                    record_count=1000,
                    entity_count=812,
                ),
                BaselineStatus(
                    data_source="VENDORS_ERP",
                    present=False,
                    remediation="run accept_baseline to create one",
                ),
                BaselineStatus(
                    data_source="PARTNERS_API",
                    present=False,
                    unreadable=True,
                ),
            ],
        )

        rendered = render_summary(summary)
        lines = rendered.splitlines()

        # Two header lines plus exactly one line per registered source.
        assert len(lines) == 2 + 3

        # Each source name appears on exactly one rendered line, with the marker
        # matching its classification.
        for data_source, marker in (
            ("CUSTOMERS_CRM", "present"),
            ("VENDORS_ERP", "MISSING"),
            ("PARTNERS_API", "UNREADABLE"),
        ):
            matches = [line for line in lines if line.startswith(f"{data_source}:")]
            assert len(matches) == 1
            assert marker in matches[0]

    def test_render_emits_no_row_level_or_heavy_fields(self) -> None:
        """Rendering surfaces only counts + timestamp, never heavy/row-level data.

        A present row is constructed from the light-metadata contract only, so
        the rendered text must not contain any of the heavy baseline fields
        (match/possible-match/relationship counts) or their values.

        Validates: Requirements 1.2.
        """
        summary = BaselineSummary(
            registry_present=True,
            statuses=[
                BaselineStatus(
                    data_source="CUSTOMERS_CRM",
                    present=True,
                    captured_at="2025-07-01T10:00:00Z",
                    record_count=1000,
                    entity_count=812,
                )
            ],
        )

        rendered = render_summary(summary)

        for heavy_field in _HEAVY_FIELDS:
            assert heavy_field not in rendered


# ---------------------------------------------------------------------------
# Architecture-guardrail tests (Task 10.2)
# ---------------------------------------------------------------------------

# Resolve the power root once (senzing-bootcamp/) relative to this test file so
# the guardrails locate the script, hooks, and steering files without touching
# the current working directory.
_POWER_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _POWER_ROOT / "scripts" / "baseline_status.py"
_HOOKS_DIR = _POWER_ROOT / "hooks"
_STEERING_DIR = _POWER_ROOT / "steering"

# The only non-stdlib modules baseline_status.py is allowed to import: the two
# sibling scripts it reuses unmodified (Req 3.3 — stdlib-only, no third-party).
_ALLOWED_SIBLING_MODULES = frozenset({"compare_results", "data_sources"})

# The two steering files that (optionally) surface the summary at natural
# checkpoints; their additions must be Markdown prose, never hook config.
_STEERING_FILES = (
    _STEERING_DIR / "module-05-phase3-test-load.md",
    _STEERING_DIR / "session-resume.md",
)


def _hook_is_write_tool_trigger(hook: dict) -> bool:
    """Return True iff a v1 hook definition fires on a write-tool interception.

    A write-tool hook is a ``PreToolUse``/``PostToolUse`` hook — the 1.0 tool
    triggers that intercept tool calls (the legacy ``preToolUse``/``postToolUse``
    ``when.type`` maps to the ``trigger`` field of a v1 hook definition). This is
    the interception shape the design deliberately avoids for this read-only
    feature.

    Args:
        hook: A single parsed v1 hook definition (``data["hooks"][i]``).

    Returns:
        True when the hook's ``trigger`` is ``"PreToolUse"`` or ``"PostToolUse"``.
    """
    return hook.get("trigger") in {"PreToolUse", "PostToolUse"}


def _top_level_imported_modules(source: str) -> set[str]:
    """Collect the top-level module names imported at a module's top level.

    Parses ``source`` with :mod:`ast` and returns the first path component of
    every module referenced by a module-level ``import``/``from ... import``
    statement (e.g. ``import a.b`` and ``from a.b import c`` both contribute
    ``"a"``). Nested imports inside functions are ignored — top-level imports are
    what determine the module's hard dependencies.

    Args:
        source: The Python source text to parse.

    Returns:
        The set of top-level (first-component) module names imported at module
        scope.
    """
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in tree.body:  # module-level statements only
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # Skip relative imports (node.level > 0); scripts use absolute imports.
            if node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


class TestBaselineStatusArchitecture:
    """Architecture guardrails for the ER Baseline Status Summary feature.

    These pin the design's structural claims so they cannot silently regress:

    - Requirement 2.3: the feature is surfaced by prose only — it adds no
      ``PostToolUse`` write-tool hook, and no hook references ``baseline_status``.
    - Requirement 3.3: the script is stdlib-only — every top-level import is a
      standard-library module or one of the two allowed sibling scripts
      (``compare_results`` / ``data_sources``); no third-party package.
    """

    def test_no_write_tool_hook_references_baseline_status(self) -> None:
        """The feature adds no write-tool hook that surfaces the summary.

        Confirms the design's prose-only claim: no hook file references
        ``baseline_status`` at all, and in particular none does so from a
        ``PreToolUse``/``PostToolUse`` write-tool trigger.

        Validates: Requirements 2.3.
        """
        hook_files = sorted(_HOOKS_DIR.glob("*.json"))
        assert hook_files, "expected at least one hook file to inspect"

        referencing_hooks: list[str] = []
        write_tool_hooks_referencing: list[str] = []
        for hook_file in hook_files:
            raw = hook_file.read_text(encoding="utf-8")
            if "baseline_status" in raw:
                referencing_hooks.append(hook_file.name)
                # v1 wrapper: the hook definition lives under data["hooks"][0].
                hook = json.loads(raw)["hooks"][0]
                if _hook_is_write_tool_trigger(hook):
                    write_tool_hooks_referencing.append(hook_file.name)

        # No write-tool hook surfaces the summary (the specific design claim).
        assert write_tool_hooks_referencing == [], (
            "feature must add no write-tool hook referencing baseline_status; "
            f"found: {write_tool_hooks_referencing}"
        )
        # And, more strongly, no hook references baseline_status at all — the
        # surfacing is prose-only, with no hook introduced by this feature.
        assert referencing_hooks == [], (
            "surfacing must be prose-only (no hook references baseline_status); "
            f"found: {referencing_hooks}"
        )

    def test_script_imports_are_stdlib_or_allowed_siblings(self) -> None:
        """Every top-level import is stdlib or an allowed sibling script.

        Parses ``baseline_status.py`` and asserts each top-level imported module
        is either in :data:`sys.stdlib_module_names` (Python 3.11+ standard
        library) or one of the two reused sibling scripts. No third-party package
        may leak in.

        Validates: Requirements 3.3.
        """
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        imported = _top_level_imported_modules(source)

        # Sanity check: the parser found the reused siblings and some stdlib.
        assert imported, "expected baseline_status.py to have top-level imports"

        allowed = set(sys.stdlib_module_names) | _ALLOWED_SIBLING_MODULES
        disallowed = imported - allowed
        assert disallowed == set(), (
            "baseline_status.py may import only stdlib modules plus the sibling "
            f"scripts {sorted(_ALLOWED_SIBLING_MODULES)}; found disallowed "
            f"imports: {sorted(disallowed)}"
        )

        # The two reused siblings are actually imported (Req 3.1/3.2 wiring).
        assert _ALLOWED_SIBLING_MODULES <= imported, (
            "baseline_status.py must reuse both sibling scripts; missing: "
            f"{sorted(_ALLOWED_SIBLING_MODULES - imported)}"
        )

    def test_steering_surfacing_is_prose_only(self) -> None:
        """The steering surfacing is Markdown prose, not hook config.

        Asserts both steering files exist, surface the summary via an advisory
        shell-command reference to ``baseline_status.py``, and that this feature's
        additions are prose only — no hook JSON (``"trigger"``/``"action"``/
        ``"matcher"``/``Pre``/``PostToolUse``) is attached to the
        ``baseline_status`` reference. (An unrelated pre-existing mention of the
        generic hook-install workflow elsewhere in a file is not this feature's
        surfacing and is deliberately not matched.)

        Validates: Requirements 2.3.
        """
        # Markers that would indicate an executable hook config rather than prose.
        hook_config_markers = (
            '"trigger"',
            '"action"',
            '"matcher"',
            "PostToolUse",
            "PreToolUse",
            ".json",
        )

        for steering_file in _STEERING_FILES:
            assert steering_file.is_file(), f"missing steering file: {steering_file}"
            text = steering_file.read_text(encoding="utf-8")

            # The summary is surfaced as an advisory shell command (prose), which
            # is exactly the prose-only surfacing the design specifies — not a hook.
            assert (
                "python3 senzing-bootcamp/scripts/baseline_status.py" in text
            ), (
                f"{steering_file.name} must surface baseline_status.py as an "
                "advisory shell command"
            )

            # This feature's additions are prose: the baseline_status reference is
            # never carried inside a hook-config construct. Check per line so an
            # unrelated hook-install section elsewhere in the file is not matched.
            for line in text.splitlines():
                if "baseline_status" not in line:
                    continue
                for marker in hook_config_markers:
                    assert marker not in line, (
                        f"{steering_file.name}: baseline_status surfacing must be "
                        f"prose-only; found hook-config marker {marker!r} on a line "
                        "referencing baseline_status"
                    )

        # No new hook file was introduced for this feature (belt-and-suspenders
        # with the write-tool guardrail above): no hook filename mentions it.
        baseline_hook_files = [
            path.name
            for path in _HOOKS_DIR.glob("*.json")
            if "baseline_status" in path.name or "baseline-status" in path.name
        ]
        assert baseline_hook_files == [], (
            f"feature must add no hook file; found: {baseline_hook_files}"
        )
