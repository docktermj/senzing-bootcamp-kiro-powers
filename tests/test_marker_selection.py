"""Marker-selection tests validating the ``slow``/``property`` taxonomy.

Feature: test-suite-parallelization

Verifies that a developer can run selective subsets of the suite by marker
expression (Requirement 3.4). The ``slow`` and ``property`` markers are applied
to tests in two different ways:

- ``property`` is applied dynamically at collection time via a
  ``pytest_collection_modifyitems`` hook in both conftests, which tags every
  Hypothesis ``@given`` test.
- ``slow`` is applied via class-level ``@pytest.mark.slow`` decorators.

Because the application is partly dynamic, these tests run *real* pytest
subprocesses with ``--collect-only`` over both discovery roots and compare the
collected node-id sets for three selections:

- ``-m "slow or property"``         → the selected set (must be non-empty)
- ``-m "not slow and not property"``→ the complementary excluded set
- (no marker filter)                → the full set

and assert the two marker selections are disjoint and partition the full set
(``selected ∪ excluded == total`` and ``selected ∩ excluded == ∅``). That
partition is exactly the behavioral guarantee of Requirement 3.4: selecting by
a registered marker expression runs only the matching tests.

Subprocesses use ``sys.executable -m pytest`` from the project root so the
configured ``addopts`` (which carries ``-v``) apply; an extra ``-q -q`` nets the
verbosity to a flat one-node-id-per-line listing that is straightforward to
parse, and ``-p no:cacheprovider`` keeps runs side-effect free.

Validates: Requirements 3.4
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECT_ROOTS = ["senzing-bootcamp/tests", "tests"]

SELECTED_EXPR = "slow or property"
EXCLUDED_EXPR = "not slow and not property"

# Matches the pytest collect-only summary line, e.g.
#   "5922 tests collected in 2.21s"
#   "1362/5922 tests collected (4560 deselected) in 2.23s"
_SUMMARY_RE = re.compile(r"(\d+)(?:/(\d+))?\s+tests?\s+collected")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_collect(marker_expr: str | None) -> subprocess.CompletedProcess:
    """Run ``pytest --collect-only`` over both roots, optionally marker-filtered.

    Args:
        marker_expr: A ``-m`` marker expression, or ``None`` for no filter.

    Returns:
        The completed subprocess (captured stdout/stderr, text mode).
    """
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *COLLECT_ROOTS,
        "--collect-only",
        # addopts carries -v; two -q net the verbosity below zero so pytest
        # emits a flat "<file>::<class>::<test>" node id per line.
        "-q",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if marker_expr is not None:
        cmd += ["-m", marker_expr]
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )


def _parse_node_ids(stdout: str) -> set[str]:
    """Extract the set of collected node ids from flat collect-only output.

    Node id lines contain ``::`` (``file::Class::test``). pytest may wrap very
    long lines in the captured output, so lines are rejoined on the leading
    path token before filtering.

    Args:
        stdout: The captured stdout of a ``--collect-only -q -q`` run.

    Returns:
        The set of node id strings.
    """
    node_ids: set[str] = set()
    current = ""
    for raw in stdout.splitlines():
        line = raw.rstrip("\n")
        if not line:
            continue
        # A fresh node id line starts with a known root and contains "::".
        if ("::" in line) and any(
            line.startswith(root) for root in COLLECT_ROOTS
        ):
            if current:
                node_ids.add(current)
            current = line.strip()
        elif current and "tests collected" not in line:
            # Continuation of a wrapped node id line.
            current += line.strip()
    if current:
        node_ids.add(current)
    # Drop any accidental capture of the summary line.
    return {nid for nid in node_ids if "tests collected" not in nid}


def _parse_summary_count(stdout: str) -> int | None:
    """Parse the collected (selected) count from the pytest summary line.

    For a filtered run the line looks like ``1362/5922 tests collected
    (4560 deselected) ...`` and the *first* number is the selected count. For an
    unfiltered run it is ``5922 tests collected ...``.

    Args:
        stdout: The captured stdout of a ``--collect-only`` run.

    Returns:
        The selected/collected count, or ``None`` if no summary was found.
    """
    match = None
    for m in _SUMMARY_RE.finditer(stdout):
        match = m  # keep the last match (the summary line is at the end)
    if match is None:
        return None
    return int(match.group(1))


# ===========================================================================
# Tests: marker-based selective collection
# Validates: Requirements 3.4
# ===========================================================================


class TestMarkerSelection:
    """Selecting by ``slow``/``property`` marker expressions partitions the suite.

    Runs real ``--collect-only`` subprocesses and asserts the selected and
    excluded sets are disjoint, non-trivial, and together equal the full set.

    Validates: Requirements 3.4
    """

    def test_marker_selection_partitions_suite(self):
        """``slow or property`` and its complement disjointly cover the suite.

        Collects three node-id sets (selected, excluded, total) and asserts:

        - the selected set is non-empty (the markers actually match tests),
        - the excluded set is non-empty (the complement matches tests too),
        - the two selections are disjoint,
        - their union equals the full collected set, and
        - their sizes sum to the full count.

        **Validates: Requirements 3.4**
        """
        selected = _run_collect(SELECTED_EXPR)
        excluded = _run_collect(EXCLUDED_EXPR)
        total = _run_collect(None)

        for label, result in (
            ("slow or property", selected),
            ("not slow and not property", excluded),
            ("unfiltered", total),
        ):
            assert result.returncode == 0, (
                f"Collection for selection '{label}' should exit 0, but it "
                f"failed (exit {result.returncode}).\n"
                f"STDOUT tail:\n{result.stdout[-2000:]}\n"
                f"STDERR tail:\n{result.stderr[-2000:]}"
            )

        selected_ids = _parse_node_ids(selected.stdout)
        excluded_ids = _parse_node_ids(excluded.stdout)
        total_ids = _parse_node_ids(total.stdout)

        # The selection must actually match tests (markers are applied).
        assert selected_ids, (
            "Expected '-m \"slow or property\"' to select at least one test, "
            "but the collected set was empty."
        )
        # The complement must also match tests (the suite is not all-slow).
        assert excluded_ids, (
            "Expected '-m \"not slow and not property\"' to select at least "
            "one test, but the collected set was empty."
        )

        # The two marker selections must be disjoint: no test is both included
        # and excluded by complementary expressions.
        overlap = selected_ids & excluded_ids
        assert not overlap, (
            "The 'slow or property' and 'not slow and not property' selections "
            f"must be disjoint, but {len(overlap)} node id(s) appear in both, "
            f"e.g. {sorted(overlap)[:5]}"
        )

        # Together they must partition the full suite exactly.
        assert selected_ids | excluded_ids == total_ids, (
            "The two complementary selections must together equal the full "
            "collected set. Missing from union: "
            f"{sorted(total_ids - (selected_ids | excluded_ids))[:5]}; "
            "extra in union: "
            f"{sorted((selected_ids | excluded_ids) - total_ids)[:5]}"
        )
        assert len(selected_ids) + len(excluded_ids) == len(total_ids), (
            f"Selected ({len(selected_ids)}) + excluded ({len(excluded_ids)}) "
            f"should equal total ({len(total_ids)})."
        )

    def test_summary_counts_are_complementary(self):
        """The reported collected counts confirm the disjoint partition.

        Cross-checks the parsed node-id sets against pytest's own summary-line
        counts: the selected count is positive and selected + excluded equals
        the unfiltered total. This guards against parser drift independent of
        the node-id set comparison.

        **Validates: Requirements 3.4**
        """
        selected_count = _parse_summary_count(_run_collect(SELECTED_EXPR).stdout)
        excluded_count = _parse_summary_count(_run_collect(EXCLUDED_EXPR).stdout)
        total_count = _parse_summary_count(_run_collect(None).stdout)

        assert selected_count is not None, "Could not parse the selected summary."
        assert excluded_count is not None, "Could not parse the excluded summary."
        assert total_count is not None, "Could not parse the total summary."

        assert selected_count > 0, (
            "Expected a positive number of tests selected by "
            f"'-m \"{SELECTED_EXPR}\"', got {selected_count}."
        )
        assert selected_count + excluded_count == total_count, (
            f"Selected ({selected_count}) + excluded ({excluded_count}) should "
            f"equal total ({total_count})."
        )
