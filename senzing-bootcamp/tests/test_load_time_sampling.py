"""Tests for the Module 4 SQLite Load_Time_Warning sampling helpers.

Feature: module4-sqlite-load-time-warning

This module holds the ``TestSampling`` class covering the pure sampling helpers
in ``load_time_warning`` (target validation, count-based selection, and the
ER-demonstrating selection). Later tasks append their property and example tests
(count-based selection, ER-demonstrating selection, and sample I/O) to the same
``TestSampling`` class; the strategy section below is the shared home for their
``st_``-prefixed generators.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from load_time_warning import (  # noqa: E402
    SAMPLE_MANIFEST_NAME,
    STRATEGY_DESCRIBED,
    STRATEGY_ER_DEMONSTRATING,
    STRATEGY_FIRST_N,
    STRATEGY_RANDOM_N,
    VALID_SAMPLING_STRATEGIES,
    SampleTargetValidation,
    SampleWriteResult,
    select_er_demonstrating,
    select_first_n,
    select_random_n,
    validate_sample_target,
    write_sample,
    write_sample_manifest,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_target(draw) -> int | bool | None:
    """Draw a candidate sampling target record count.

    Covers ordinary integers across a wide range, the positive/zero/negative
    boundary values that straddle the ``target > 0`` rule, booleans (an ``int``
    subclass the validator must reject), and ``None`` (the "not supplied yet"
    case).
    """
    return draw(
        st.one_of(
            st.integers(min_value=-10, max_value=2_000),
            st.integers(),
            st.sampled_from([0, 1, -1, 2_000]),
            st.booleans(),
            st.none(),
        )
    )


@st.composite
def st_total(draw) -> int | None:
    """Draw a candidate Collected_Record_Total for sampling validation.

    Covers ordinary integers (including values above, at, and below plausible
    targets so the ``target < collected_total`` boundary is exercised), zero and
    negatives, and ``None`` (the uncomputable / indeterminate case).
    """
    return draw(
        st.one_of(
            st.integers(min_value=-10, max_value=2_000),
            st.integers(),
            st.sampled_from([0, 1, -1, 1_000, 2_000]),
            st.none(),
        )
    )


@st.composite
def st_total_and_target(draw) -> tuple[int, int]:
    """Draw a ``(total, target)`` pair with ``total > 0`` and ``0 < target < total``.

    Property 5 is stated over valid sampling sizes only. Since ``target`` must be
    a positive integer strictly below ``total``, ``total`` is at least 2 (so a
    strictly-smaller positive target exists), and ``target`` is then drawn from
    ``[1, total)``.
    """
    total = draw(st.integers(min_value=2, max_value=2_000))
    target = draw(st.integers(min_value=1, max_value=total - 1))
    return total, target


@st.composite
def st_seed(draw) -> int:
    """Draw a seed for the deterministic random selector (``select_random_n``)."""
    return draw(st.integers(min_value=-1_000_000, max_value=1_000_000))


@st.composite
def st_clusters_singletons_target(draw) -> tuple[list[list[int]], list[int], int]:
    """Draw ``(clusters, singletons, target)`` over a partitioned index space.

    Generates a partition of a small index space into match clusters and
    singletons so every record index is distinct across all clusters and the
    singleton pool -- making each index's cluster membership unambiguous, which
    is what lets the "never split a cluster" property be checked exactly.

    Cluster sizes range over 1..5 (so some clusters have 2+ members, the case
    where splitting is observable), and the target ranges from 0 up to just
    beyond the total record count so the partial-fill boundary (where the next
    whole cluster would exceed the budget) and the fill-from-singletons path are
    both exercised.
    """
    cluster_sizes = draw(
        st.lists(st.integers(min_value=1, max_value=5), min_size=0, max_size=6)
    )
    num_singletons = draw(st.integers(min_value=0, max_value=6))

    # Assign consecutive, distinct indices to each cluster, then to singletons.
    next_index = 0
    clusters: list[list[int]] = []
    for size in cluster_sizes:
        clusters.append(list(range(next_index, next_index + size)))
        next_index += size
    singletons = list(range(next_index, next_index + num_singletons))
    total = next_index + num_singletons

    target = draw(st.integers(min_value=0, max_value=total + 2))
    return clusters, singletons, target


class TestSampling:
    """Property and example tests for the sampling helpers.

    Validates: Requirements 5.5, 5.6, 5.2, 5.4
    """

    # Feature: module4-sqlite-load-time-warning, Property 4: Sampling target is
    # valid exactly when it is a positive integer below the total — for any
    # target drawn from integers, booleans, and None, and any collected_total
    # drawn from integers and None, validate_sample_target(target,
    # collected_total) reports valid iff target is a real int (not bool) with
    # target > 0, collected_total is a real int, and target < collected_total;
    # every other case is reported invalid with a non-empty, PII-free reason. It
    # never raises.
    # Validates: Requirements 5.5, 5.6
    @given(target=st_target(), collected_total=st_total())
    def test_target_valid_iff_positive_int_below_total(
        self, target: int | bool | None, collected_total: int | None
    ) -> None:
        result = validate_sample_target(target, collected_total)

        # Always a SampleTargetValidation, and the call never raises.
        assert isinstance(result, SampleTargetValidation)

        # A real int (bool is an int subclass and must be rejected).
        target_is_real_int = isinstance(target, int) and not isinstance(target, bool)
        total_is_real_int = isinstance(collected_total, int) and not isinstance(
            collected_total, bool
        )
        expected_valid = (
            target_is_real_int
            and target > 0
            and total_is_real_int
            and target < collected_total
        )

        assert result.valid is expected_valid

        # When invalid, a non-empty reason lets the steering re-ask (Req 5.6).
        assert isinstance(result.reason, str)
        if not expected_valid:
            assert result.reason != ""

    # Feature: module4-sqlite-load-time-warning, Property 5: Count-based
    # selection returns exactly target distinct in-range indices — for any
    # total > 0, any target with 0 < target < total, and any seed, both
    # select_first_n(total, target) and select_random_n(total, target, seed)
    # return exactly target distinct indices, all within [0, total);
    # select_random_n is deterministic for a fixed seed. Neither raises.
    # Validates: Requirements 5.2, 5.4
    @given(total_and_target=st_total_and_target(), seed=st_seed())
    def test_count_based_selection_returns_target_distinct_in_range(
        self, total_and_target: tuple[int, int], seed: int
    ) -> None:
        total, target = total_and_target

        # Both selectors: exactly target results, all distinct, all in [0, total).
        for selection in (
            select_first_n(total, target),
            select_random_n(total, target, seed),
        ):
            assert len(selection) == target
            assert len(set(selection)) == target
            assert all(0 <= index < total for index in selection)

        # select_random_n is deterministic for a fixed seed.
        assert select_random_n(total, target, seed) == select_random_n(
            total, target, seed
        )

    # Feature: module4-sqlite-load-time-warning, Property 6: ER-demonstrating
    # selection never splits a match cluster — for any set of match clusters
    # (each a list of record indices), any singletons, any target, and any seed,
    # the index set returned by select_er_demonstrating(clusters, singletons,
    # target, seed) contains, for every cluster, either all of that cluster's
    # members or none of them — never a strict subset — so cross-source overlaps
    # and known match clusters are preserved. It never raises.
    # Validates: Requirements 5.7
    @given(clusters_singletons_target=st_clusters_singletons_target(), seed=st_seed())
    def test_er_demonstrating_never_splits_a_cluster(
        self,
        clusters_singletons_target: tuple[list[list[int]], list[int], int],
        seed: int,
    ) -> None:
        clusters, singletons, target = clusters_singletons_target

        result = select_er_demonstrating(clusters, singletons, target, seed)
        result_set = set(result)

        # Core property: every cluster is all-or-none — never a strict subset.
        # Because indices are distinct across clusters and singletons, cluster
        # membership is unambiguous, so we can count each cluster's members.
        for cluster in clusters:
            present = sum(1 for index in cluster if index in result_set)
            assert present == 0 or present == len(cluster)

        # The result draws only from known indices (cluster members + singletons)
        # and never contains duplicates.
        known_indices: set[int] = set(singletons)
        for cluster in clusters:
            known_indices.update(cluster)
        assert result_set <= known_indices
        assert len(result) == len(result_set)

    # ------------------------------------------------------------------
    # Example tests: sample I/O and sampling vocabulary (Task 5.8)
    # Requirements: 5.2, 5.3, 5.4, 7.5
    #
    # These are example/unit tests (not property tests) exercising the sample
    # writer, the manifest writer, and the strategy vocabulary with real file
    # I/O against pytest's tmp_path. All fixtures are synthetic and PII-free.
    # ------------------------------------------------------------------

    def test_write_sample_csv_keeps_header_plus_selected_rows(
        self, tmp_path: Path
    ) -> None:
        """CSV: the header is always kept; only data rows in keep_indices follow.

        The header is excluded from the 0-based data-record index space, so
        keeping indices [0, 2] yields the header plus the first and third data
        rows (Requirements 5.2, 5.4).
        """
        source = tmp_path / "source.csv"
        source.write_text(
            "COL_A,COL_B\n"
            "rec0,val0\n"
            "rec1,val1\n"
            "rec2,val2\n"
            "rec3,val3\n",
            encoding="utf-8",
        )
        dest = tmp_path / "samples" / "sample.csv"

        result = write_sample(str(source), str(dest), "csv", [0, 2])

        assert isinstance(result, SampleWriteResult)
        assert result.success is True
        assert dest.exists()
        written = dest.read_text(encoding="utf-8").splitlines()
        # Header always kept; data records at indices 0 and 2 kept, 1 and 3 dropped.
        assert written == ["COL_A,COL_B", "rec0,val0", "rec2,val2"]

    def test_write_sample_jsonl_keeps_selected_lines(self, tmp_path: Path) -> None:
        """JSONL: every non-empty line is a 0-based record; keep selected lines.

        Keeping indices [1, 3] yields exactly the second and fourth lines
        (Requirements 5.2, 5.4).
        """
        source = tmp_path / "source.jsonl"
        source.write_text(
            '{"RECORD_ID": "0"}\n'
            '{"RECORD_ID": "1"}\n'
            '{"RECORD_ID": "2"}\n'
            '{"RECORD_ID": "3"}\n',
            encoding="utf-8",
        )
        dest = tmp_path / "samples" / "sample.jsonl"

        result = write_sample(str(source), str(dest), "jsonl", [1, 3])

        assert result.success is True
        assert dest.exists()
        written = dest.read_text(encoding="utf-8").splitlines()
        assert written == ['{"RECORD_ID": "1"}', '{"RECORD_ID": "3"}']

    def test_write_sample_unreadable_source_fails_without_raising(
        self, tmp_path: Path
    ) -> None:
        """A nonexistent source yields success=False and never raises (Req 7.5)."""
        missing = tmp_path / "does_not_exist.csv"
        dest = tmp_path / "samples" / "sample.csv"

        result = write_sample(str(missing), str(dest), "csv", [0])

        assert isinstance(result, SampleWriteResult)
        assert result.success is False
        assert result.reason != ""

    def test_write_sample_uncountable_format_fails_without_raising(
        self, tmp_path: Path
    ) -> None:
        """An unsupported format yields success=False and never raises (Req 7.5)."""
        source = tmp_path / "source.json"
        source.write_text('{"records": []}\n', encoding="utf-8")
        dest = tmp_path / "samples" / "sample.json"

        result = write_sample(str(source), str(dest), "json", [0])

        assert isinstance(result, SampleWriteResult)
        assert result.success is False
        assert result.reason != ""
        # Nothing was written for an unsampleable format.
        assert not dest.exists()

    def test_write_sample_manifest_records_strategy_and_target(
        self, tmp_path: Path
    ) -> None:
        """The manifest sidecar records strategy, target, and kept count (Req 5.4)."""
        dest_dir = tmp_path / "samples"

        result = write_sample_manifest(
            str(dest_dir), STRATEGY_RANDOM_N, target=100, kept=100
        )

        assert isinstance(result, SampleWriteResult)
        assert result.success is True

        manifest_path = dest_dir / SAMPLE_MANIFEST_NAME
        assert manifest_path.exists()
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert payload["strategy"] == STRATEGY_RANDOM_N
        assert payload["target"] == 100
        assert payload["kept"] == 100

    def test_valid_sampling_strategies_vocabulary(self) -> None:
        """VALID_SAMPLING_STRATEGIES covers all four Sampling_Strategy options.

        first-N, random-N, ER-demonstrating, and bootcamper-described
        (Requirements 5.2, 5.3).
        """
        assert STRATEGY_FIRST_N in VALID_SAMPLING_STRATEGIES
        assert STRATEGY_RANDOM_N in VALID_SAMPLING_STRATEGIES
        assert STRATEGY_ER_DEMONSTRATING in VALID_SAMPLING_STRATEGIES
        assert STRATEGY_DESCRIBED in VALID_SAMPLING_STRATEGIES
