"""Tests for the Module 4 SQLite Load_Time_Warning trigger and wording.

Feature: module4-sqlite-load-time-warning
"""

from __future__ import annotations

import inspect
import os
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import (  # noqa: E402  (path manipulated above)
    VALID_FORMATS,
    Registry,
    RegistryEntry,
)
from record_count_backfill import (  # noqa: E402  (path manipulated above)
    compute_collected_count,
)
from volume_utils import (  # noqa: E402
    LOAD_WARNING_THRESHOLD,
    TimingGuidance,
    build_load_time_warning,
    should_warn_load_time,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Junk strings that never normalize to "sqlite" — exercise the non-SQLite and
# unrecognized-engine branches of the predicate.
_JUNK_STRINGS = ["", "  ", "SQLITE_DB", "mysql", "postgres", "unknown", "xyz", "123"]


@st.composite
def st_total(draw) -> int | bool | None:
    """Draw a candidate Collected_Record_Total.

    Covers ordinary integers across a wide range, the exact 75,000 threshold
    boundary and its immediate neighbours, negatives and zero, booleans (an
    ``int`` subclass the predicate must reject), and ``None`` (the indeterminate
    / uncomputable case).
    """
    return draw(
        st.one_of(
            st.integers(min_value=-1_000, max_value=200_000),
            st.integers(),
            st.sampled_from(
                [
                    LOAD_WARNING_THRESHOLD,       # exactly at threshold -> no warning
                    LOAD_WARNING_THRESHOLD - 1,   # just below
                    LOAD_WARNING_THRESHOLD + 1,   # just above -> warning (on sqlite)
                    0,
                    -1,
                    -LOAD_WARNING_THRESHOLD,
                ]
            ),
            st.booleans(),
            st.none(),
        )
    )


@st.composite
def st_db_type(draw) -> str | None:
    """Draw a candidate active database type.

    Covers ``sqlite`` in mixed case and with surrounding whitespace (all of which
    normalize to SQLite), ``postgresql``, the empty string, ``None``, and junk
    strings that must never normalize to SQLite.
    """
    sqlite_variants = ["sqlite", "SQLite", "SQLITE", " sqlite ", "  SqLiTe\t", "sqlite\n"]
    return draw(
        st.one_of(
            st.sampled_from(sqlite_variants),
            st.just("postgresql"),
            st.just(""),
            st.none(),
            st.sampled_from(_JUNK_STRINGS),
            st.text(max_size=12),
        )
    )


class TestLoadTimeWarningTrigger:
    """Property and example tests for ``should_warn_load_time``.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.5, 7.1, 7.2
    """

    # Feature: module4-sqlite-load-time-warning, Property 1: Trigger fires
    # exactly on (total > threshold) AND SQLite — for any collected_total drawn
    # from integers (incl. the 75,000 boundary and negatives), booleans, and
    # None, and any db_type drawn from sqlite in mixed case / with whitespace,
    # postgresql, "", None, and junk strings, should_warn_load_time returns True
    # iff collected_total is a real int (not bool) strictly greater than
    # LOAD_WARNING_THRESHOLD AND normalized db_type == "sqlite"; in every other
    # case it returns False and never raises.
    # Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.5, 7.1, 7.2
    @given(collected_total=st_total(), db_type=st_db_type())
    def test_trigger_truth_table(
        self, collected_total: int | bool | None, db_type: str | None
    ) -> None:
        result = should_warn_load_time(collected_total, db_type)

        # A real int total (bool is an int subclass and must be rejected).
        is_real_int = isinstance(collected_total, int) and not isinstance(
            collected_total, bool
        )
        over_threshold = is_real_int and collected_total > LOAD_WARNING_THRESHOLD
        normalized_sqlite = (
            isinstance(db_type, str) and db_type.strip().lower() == "sqlite"
        )
        expected = over_threshold and normalized_sqlite

        # Returns a bool exactly matching the truth table, and never raises.
        assert result is expected

    def test_predicate_independent_of_tier_and_license(self) -> None:
        """The trigger takes no tier and no license argument (Req 2.5, 7.1, 7.2).

        Independence from the production tier and the Effective_License_Limit is
        structural: the predicate's signature exposes only the collected total
        and the active database type, so no tier/license value can influence the
        verdict.
        """
        params = list(inspect.signature(should_warn_load_time).parameters)

        assert params == ["collected_total", "db_type"]
        for name in params:
            assert "tier" not in name
            assert "license" not in name

    # Boundary / indeterminate cells of the trigger truth table (Req 8.1) — the
    # specific corners the property test's generators cover in aggregate, pinned
    # here as explicit, self-documenting examples.
    #   (75_001, "sqlite")     -> True  : one record past the threshold on SQLite (Req 1.1)
    #   (75_000, "sqlite")     -> False : exactly at the threshold, "at or below" (Req 1.2)
    #   (100_000, "postgresql")-> False : large total but a non-SQLite engine (Req 1.3)
    #   (None, "sqlite")       -> False : indeterminate collected total (Req 1.4)
    #   (100_000, None)        -> False : indeterminate database type (Req 1.4)
    # Validates: Requirements 1.2, 1.3, 1.4, 8.1
    @pytest.mark.parametrize(
        ("collected_total", "db_type", "expected"),
        [
            (75_001, "sqlite", True),
            (75_000, "sqlite", False),
            (100_000, "postgresql", False),
            (None, "sqlite", False),
            (100_000, None, False),
        ],
    )
    def test_trigger_boundary_and_indeterminate_cells(
        self, collected_total: int | None, db_type: str | None, expected: bool
    ) -> None:
        assert should_warn_load_time(collected_total, db_type) is expected


# ---------------------------------------------------------------------------
# Property 2 — the collected-total lower bound feeding the trigger
# ---------------------------------------------------------------------------
#
# compute_collected_count(registry, row_count=True).known_total is the
# determinate lower bound handed to should_warn_load_time. The strategies below
# generate a *plan* for a registry that mixes the three interesting kinds of
# source, and the test body materializes the countable fixture files under a
# fresh temp directory (fixtures must exist on disk for the row-count fallback,
# and Hypothesis strategies must stay side-effect free). All fixtures are
# synthetic and PII-free.

# Formats data_sources treats as row-countable vs. not (VALID_FORMATS minus the
# two countable formats). count_file_rows only tallies csv/jsonl.
_UNCOUNTABLE_FORMATS = sorted(VALID_FORMATS - {"csv", "jsonl"})


def _st_data_source_keys():
    """Strategy producing valid DATA_SOURCE key strings: ``^[A-Z][A-Z0-9_]*$``."""
    first = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    rest = st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=0, max_size=10
    )
    return st.tuples(first, rest).map(lambda t: t[0] + t[1])


@st.composite
def _st_source_plan(draw, key: str) -> dict:
    """Draw a per-source plan for one of the interesting source kinds.

    The five kinds cover the whole resolvability space:

    - ``metadata``: a stated ``record_count`` (resolved from metadata; the file
      is never read, so any valid format is allowed).
    - ``rowcount_csv`` / ``rowcount_jsonl``: no stated count but a countable
      format backed by a fixture file with a known number of rows (resolved via
      the row-count fallback).
    - ``uncountable``: no stated count and an uncountable format (unresolvable ->
      unknown).
    - ``missing_countable``: no stated count, a countable format, but *no* file
      on disk (unresolvable -> unknown).

    Args:
        draw: The Hypothesis draw callable.
        key: The DATA_SOURCE key this plan describes.

    Returns:
        A plan dict the test body materializes into a :class:`RegistryEntry`.
    """
    kind = draw(
        st.sampled_from(
            ["metadata", "rowcount_csv", "rowcount_jsonl", "uncountable", "missing_countable"]
        )
    )
    if kind == "metadata":
        count = draw(st.integers(min_value=0, max_value=120_000))
        fmt = draw(st.sampled_from(sorted(VALID_FORMATS)))
        return {"key": key, "kind": kind, "record_count": count, "format": fmt, "rows": None}
    if kind == "rowcount_csv":
        rows = draw(st.integers(min_value=0, max_value=300))
        return {"key": key, "kind": kind, "record_count": None, "format": "csv", "rows": rows}
    if kind == "rowcount_jsonl":
        rows = draw(st.integers(min_value=0, max_value=300))
        return {"key": key, "kind": kind, "record_count": None, "format": "jsonl", "rows": rows}
    if kind == "uncountable":
        fmt = draw(st.sampled_from(_UNCOUNTABLE_FORMATS))
        return {"key": key, "kind": kind, "record_count": None, "format": fmt, "rows": None}
    # missing_countable: countable format but the file is never created on disk.
    fmt = draw(st.sampled_from(["csv", "jsonl"]))
    return {"key": key, "kind": kind, "record_count": None, "format": fmt, "rows": None}


@st.composite
def st_registry(draw):
    """Draw a *plan* for a registry mixing all three resolvability kinds.

    Returns a list of per-source plan dicts (never touching the filesystem). The
    test body materializes the countable fixture files under a temp directory
    and builds the real :class:`Registry`, so the strategy stays side-effect
    free while the row-count fallback still has real files to read.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A list of per-source plan dicts (possibly empty).
    """
    keys = draw(
        st.lists(_st_data_source_keys(), min_size=0, max_size=6, unique=True)
    )
    return [draw(_st_source_plan(key)) for key in keys]


def _entry(
    key: str,
    *,
    record_count: int | None,
    fmt: str,
    file_path: str,
    name: str | None = None,
) -> RegistryEntry:
    """Build a synthetic, PII-free :class:`RegistryEntry`.

    The ``name`` defaults to the (unique) DATA_SOURCE key so the per-source and
    ``unknown_sources`` breakdown carries only source names — never row content.

    Args:
        key: The DATA_SOURCE key.
        record_count: The stated record count, or ``None`` when unknown.
        fmt: The source format.
        file_path: The (possibly non-existent) collected-file path.
        name: Optional display name (defaults to ``key``).

    Returns:
        A fully-populated :class:`RegistryEntry`.
    """
    return RegistryEntry(
        data_source=key,
        name=name or key,
        file_path=file_path,
        format=fmt,
        record_count=record_count,
        file_size_bytes=None,
        quality_score=None,
        mapping_status="pending",
        load_status="not_loaded",
        added_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        test_load_status=None,
        test_entity_count=None,
        issues=None,
    )


def _write_data_file(path: str, fmt: str, rows: int) -> None:
    """Write a synthetic, PII-free countable fixture with a known row count.

    A ``csv`` file gets a header line plus ``rows`` data lines (so
    ``count_file_rows`` -> ``rows`` after subtracting the header); a ``jsonl``
    file gets ``rows`` non-empty lines.

    Args:
        path: Destination path for the fixture file.
        fmt: ``csv`` or ``jsonl``.
        rows: The number of records the file should resolve to.
    """
    if fmt == "csv":
        lines = ["h1,h2"] + [f"v{i}a,v{i}b" for i in range(rows)]
        content = "\n".join(lines) + "\n"
    else:  # jsonl
        content = "".join(f'{{"n": {i}}}\n' for i in range(rows))
    Path(path).write_text(content, encoding="utf-8")


def _materialize(specs: list[dict], tmp: str) -> tuple[list[RegistryEntry], int, list[str]]:
    """Materialize a registry plan into entries + the independently-expected totals.

    Creates a fixture file for each countable row-count source, points every
    other source at a non-existent path, and computes the expected
    ``known_total`` (sum of only resolved counts) and expected
    ``unknown_sources`` (the uncountable / missing-file source keys) from first
    principles so the test never mirrors the implementation.

    Args:
        specs: The per-source plans from :func:`st_registry`.
        tmp: A temp directory the fixture files are written under.

    Returns:
        A ``(entries, expected_known_total, expected_unknown_sources)`` tuple.
    """
    entries: list[RegistryEntry] = []
    expected_known = 0
    expected_unknown: list[str] = []

    for i, spec in enumerate(specs):
        key = spec["key"]
        kind = spec["kind"]
        fmt = spec["format"]

        if kind == "metadata":
            expected_known += spec["record_count"]
            file_path = os.path.join(tmp, f"{key}_{i}_absent.{fmt}")
            entries.append(
                _entry(key, record_count=spec["record_count"], fmt=fmt, file_path=file_path)
            )
        elif kind in ("rowcount_csv", "rowcount_jsonl"):
            rows = spec["rows"]
            file_path = os.path.join(tmp, f"{key}_{i}.{fmt}")
            _write_data_file(file_path, fmt, rows)
            expected_known += rows
            entries.append(_entry(key, record_count=None, fmt=fmt, file_path=file_path))
        else:  # uncountable or missing_countable -> unresolvable -> unknown
            expected_unknown.append(key)
            file_path = os.path.join(tmp, f"{key}_{i}_absent.{fmt}")
            entries.append(_entry(key, record_count=None, fmt=fmt, file_path=file_path))

    return entries, expected_known, expected_unknown


class TestCollectedTotalLowerBound:
    """Property and example tests for the collected-total lower bound.

    Validates: Requirements 2.1, 2.2, 2.3
    """

    # Feature: module4-sqlite-load-time-warning, Property 2: Collected total sums
    # only resolved counts and is a sound lower bound — for any registry mixing
    # sources with record_count metadata, sources missing a count in countable
    # formats (csv/jsonl), and sources missing a count in uncountable formats,
    # compute_collected_count(registry, row_count=True) produces a known_total
    # equal to the sum of only the resolved counts, lists every unresolved source
    # in unknown_sources (never counting it as zero into the total), and — because
    # unknown sources can only increase the true total — whenever known_total
    # strictly exceeds LOAD_WARNING_THRESHOLD, should_warn_load_time(known_total,
    # "sqlite") is True even while unknown sources remain.
    # Validates: Requirements 2.1, 2.2, 2.3
    @given(specs=st_registry())
    def test_collected_total_is_sound_lower_bound(self, specs: list[dict]) -> None:
        # Each example materializes its fixtures in a fresh temp dir so examples
        # never bleed state into one another.
        with tempfile.TemporaryDirectory() as tmp:
            entries, expected_known, expected_unknown = _materialize(specs, tmp)
            registry = Registry(version="2", sources=entries)

            collected = compute_collected_count(registry, row_count=True)

            # known_total sums only the resolved counts (metadata + row-count),
            # exactly matching the independently-computed expectation (Req 2.1).
            assert collected.known_total == expected_known
            # Every unresolved source is listed in unknown_sources (Req 2.2).
            assert sorted(collected.unknown_sources) == sorted(expected_unknown)

            # No unknown source is counted as zero *into* the total: the total is
            # exactly the sum over the resolved per-source counts, and every
            # unknown source is carried with a None count (never 0) (Req 2.2).
            resolved_sum = sum(sc.count for sc in collected.sources if sc.count is not None)
            assert collected.known_total == resolved_sum
            for sc in collected.sources:
                if sc.name in expected_unknown:
                    assert sc.count is None
                    assert sc.counted_from == "unknown"

            # Sound lower bound: because unknown sources can only *increase* the
            # true total, a known_total already above the threshold arms the
            # warning on SQLite even while unknown sources remain (Req 2.3).
            if collected.known_total > LOAD_WARNING_THRESHOLD:
                assert should_warn_load_time(collected.known_total, "sqlite") is True

    def test_lower_bound_fires_with_unknowns_remaining(self) -> None:
        """A resolved total over the threshold arms the warning despite unknowns.

        Deterministic corner of Property 2 (Req 2.3): one large metadata source
        pushes ``known_total`` just past the threshold while an uncountable
        source stays unresolved. The unknown source is tracked (never zeroed),
        and the warning still fires because the resolved total is a sound lower
        bound of the true total.
        """
        entries = [
            _entry(
                "BIG_META",
                record_count=LOAD_WARNING_THRESHOLD + 1,
                fmt="csv",
                file_path="/nonexistent/big_meta.csv",
            ),
            _entry(
                "UNCOUNTABLE_SRC",
                record_count=None,
                fmt="json",
                file_path="/nonexistent/uncountable.json",
            ),
        ]
        registry = Registry(version="2", sources=entries)

        collected = compute_collected_count(registry, row_count=True)

        # The unresolved source is tracked as unknown, never counted as zero.
        assert collected.unknown_sources == ["UNCOUNTABLE_SRC"]
        assert collected.known_total == LOAD_WARNING_THRESHOLD + 1
        # The lower bound already exceeds the threshold -> warn, unknowns and all.
        assert should_warn_load_time(collected.known_total, "sqlite") is True


# ---------------------------------------------------------------------------
# Property 3 — the warning-text builder (build_load_time_warning)
# ---------------------------------------------------------------------------
#
# build_load_time_warning is a pure text builder. Its output must always name
# the collected total, state the three fixed qualitative concerns, include each
# MCP timing figure exactly when it is present (and state "currently unavailable
# from the MCP server" for each figure that is None, with no substituted value),
# offer all three options while naming the migration guide, and never emit the
# Mandatory_Gate marker (⛔). All timing figures are generated with a distinctive
# "FIGVAL_" prefix so a present figure's string can never be a substring of the
# builder's fixed wording — making the presence/omission assertions meaningful.

# A single timing figure: either omitted (None) or a distinctively-prefixed,
# non-empty display string that cannot collide with the builder's fixed text.
_st_figure = st.one_of(
    st.none(),
    st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        min_size=1,
        max_size=16,
    ).map(lambda s: "FIGVAL_" + s),
)


@st.composite
def st_timing(draw) -> TimingGuidance:
    """Draw a :class:`TimingGuidance` with four independent figures.

    Each of the four figures (``expected_throughput``, ``throughput_degradation``,
    ``expected_load_duration``, ``redo_phase_duration``) is drawn independently as
    either ``None`` (the MCP server did not return it) or a distinctively-prefixed
    display string (``FIGVAL_...``) that cannot appear inside the builder's fixed
    wording, so presence/omission can be asserted without false positives.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`TimingGuidance` value covering the full present/omitted space.
    """
    return TimingGuidance(
        expected_throughput=draw(_st_figure),
        throughput_degradation=draw(_st_figure),
        expected_load_duration=draw(_st_figure),
        redo_phase_duration=draw(_st_figure),
    )


# The four MCP figures, keyed by their TimingGuidance attribute, mapped to the
# exact bold label the builder renders for each. Used to reconstruct the exact
# present / "currently unavailable" line the builder emits per figure.
_FIGURE_LABELS: dict[str, str] = {
    "expected_throughput": "**Expected load throughput:**",
    "throughput_degradation": "**Throughput degradation:**",
    "expected_load_duration": "**Expected initial-load duration:**",
    "redo_phase_duration": "**Expected redo-phase duration:**",
}


class TestLoadTimeWarningContent:
    """Property test for ``build_load_time_warning``.

    Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.5
    """

    # Feature: module4-sqlite-load-time-warning, Property 3: Warning names the
    # total, states all fixed concerns, omits only unavailable figures, and
    # offers all options without gating — for any non-negative collected_total
    # and any TimingGuidance in which each of the four figures is independently
    # a display string or None, build_load_time_warning returns text that names
    # collected_total and states the SQLite load is expected to be slow; always
    # states throughput degrades, the redo phase needs additional time, and a
    # slow mostly-idle load is expected progress rather than a stall; includes
    # each figure exactly when present and, for each None figure, states it is
    # currently unavailable from the MCP server without substituting a value;
    # always offers load-all / sample / switch-database naming the migration
    # guide; and never contains ⛔. It never raises.
    # Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.5
    @given(
        collected_total=st.integers(min_value=0, max_value=10_000_000),
        timing=st_timing(),
    )
    def test_warning_content(self, collected_total: int, timing: TimingGuidance) -> None:
        text = build_load_time_warning(collected_total, timing)

        # --- Names the collected total and the "expected to be slow" framing (Req 3.1) ---
        assert str(collected_total) in text
        assert "expected to be slow" in text

        # --- Per-figure inclusion / omission (Req 3.3, 3.4) ---
        # Present  -> the figure's string appears in its "as reported" line, and
        #             the "currently unavailable" line for that figure does not.
        # None     -> the "currently unavailable" line appears, and no value is
        #             substituted (the "as reported" line for that figure is absent).
        for field, label in _FIGURE_LABELS.items():
            value = getattr(timing, field)
            unavailable_line = (
                f"- {label} currently unavailable from the MCP server, so no "
                "specific figure is shown here."
            )
            if value is not None:
                present_line = f"- {label} {value}, as reported by the Senzing MCP server."
                assert value in text  # the returned figure string is shown (Req 3.3)
                assert present_line in text
                assert unavailable_line not in text
            else:
                assert unavailable_line in text  # stated unavailable (Req 3.4)
                # No number substituted for the omitted figure: the "as reported"
                # line for this label never appears when the figure is None (in
                # particular, the literal "None" is never rendered as a figure).
                assert f"{label} None, as reported by the Senzing MCP server." not in text
                assert f"{label} 0, as reported by the Senzing MCP server." not in text

        # --- The three fixed qualitative statements (Req 3.5, 3.6, 3.7) ---
        assert "**Throughput degrades as the database grows**" in text  # Req 3.5
        assert "**The entity-resolution redo phase needs additional time**" in text  # Req 3.6
        assert "**A slow, mostly-idle load is expected, not stalled**" in text  # Req 3.7

        # --- All three options offered, naming the migration guide (Req 4.1-4.3) ---
        assert "**Load all collected records on SQLite**" in text  # Req 4.1
        assert "**Sample down to a smaller record count**" in text  # Req 4.2
        assert "**Switch to an alternative database (e.g. PostgreSQL)**" in text  # Req 4.3
        assert "database-migration-guide" in text  # Req 4.3
        assert "docs/guides/DATABASE_MIGRATION.md" in text  # Req 4.3

        # --- Never a Mandatory_Gate: no ⛔ marker anywhere (Req 4.5) ---
        assert "⛔" not in text

    # MCP-unavailable example (Req 3.4, 8.2): the all-figures-omitted corner of
    # Property 3, pinned as an explicit, self-documenting example. When the MCP
    # server returns none of the four figures, the warning must still fire,
    # state each of the four values as currently unavailable from the MCP server
    # (one line per figure -> exactly four occurrences), and never fabricate a
    # figure — in particular the literal "None" is never rendered as a value.
    # Validates: Requirements 3.4, 8.2
    def test_all_figures_unavailable_are_reported_not_fabricated(self) -> None:
        collected_total = 123_911
        timing = TimingGuidance()  # all four figures default to None

        text = build_load_time_warning(collected_total, timing)

        # The warning still fires and names the driving collected total ...
        assert str(collected_total) in text

        # ... and every one of the four MCP figures is reported as currently
        # unavailable — the builder emits exactly one "currently unavailable"
        # line per figure, so precisely four occurrences (Req 3.4, 8.2).
        unavailable_phrase = "currently unavailable from the MCP server"
        assert text.count(unavailable_phrase) == 4

        for label in _FIGURE_LABELS.values():
            unavailable_line = (
                f"- {label} currently unavailable from the MCP server, so no "
                "specific figure is shown here."
            )
            # Each figure gets its own explicit "currently unavailable" line ...
            assert unavailable_line in text
            # ... and no value is substituted for the omitted figure: the "as
            # reported" value line for this label never appears (Req 3.4).
            assert f"{label} None, as reported by the Senzing MCP server." not in text
            assert f"{label} 0, as reported by the Senzing MCP server." not in text

        # No fabricated figures: the "as reported by the Senzing MCP server"
        # value phrase (emitted only for a present figure) never appears, and
        # the literal "None" is never rendered anywhere as a figure value.
        assert "as reported by the Senzing MCP server" not in text
        assert "None" not in text
