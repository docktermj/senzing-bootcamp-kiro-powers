"""End-state verification tests for the test-suite-debrittling feature.

Feature: test-suite-debrittling

These are example/integration (SMOKE) tests that assert the post-remediation end
state directly on the REAL repository test files under
``senzing-bootcamp/tests/`` and the repo-root ``tests/``. They codify the
design's "Whole-Suite / End-State Checks" Testing-Strategy section.

Covered concerns:

- Zero brittle findings (Requirements 4.5, 5.6): running :func:`scan` over both
  real test roots reports zero non-allowlisted findings in every brittle
  category, and the scan completes over all files (no parse errors). Allowlisted
  exemptions are permitted and not asserted to be zero.
- Regression coverage non-decrease (Requirements 6.1, 6.5): the inventory of
  Exploration_Tests / historical bug conditions did not shrink after
  remediation. This is enforced as a NON-REGRESSION FLOOR on the count of
  exploration / bug-condition coverage, measured at two granularities (test
  files and test symbols).

Adjacent: the full-suite-passes intent (Requirements 6.3, 6.4) is exercised by
the suite running green; this module's scan check guards the debrittled end
state that remediation produced.
"""

import ast
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from scan_brittle_assertions import (  # noqa: E402
    BrittleCategory,
    scan,
)

# ---------------------------------------------------------------------------
# Real repository paths
#
# Resolve the scan roots relative to the REPO ROOT (two levels up from this
# file: ``<repo>/senzing-bootcamp/tests/test_debrittling_end_state.py``) and
# build absolute paths so the tests pass regardless of pytest's cwd.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
POWER_TESTS_DIR = REPO_ROOT / "senzing-bootcamp" / "tests"
REPO_TESTS_DIR = REPO_ROOT / "tests"
SCAN_ROOTS = [POWER_TESTS_DIR, REPO_TESTS_DIR]

# ---------------------------------------------------------------------------
# Regression-coverage floors (non-regression guards)
#
# These floors are the COUNTS OBSERVED at the time remediation completed. They
# act as a one-directional ratchet: removing Exploration_Test / bug-condition
# coverage drops a count below its floor and FAILS the test, while adding more
# coverage keeps the test green. They must never be lowered to make the suite
# pass — a drop is exactly the regression Requirements 6.1 and 6.5 forbid. If
# coverage is legitimately added, these floors may be raised to match.
#
# Markers that identify exploration / historical-bug-condition coverage.
_COVERAGE_MARKERS = ("exploration", "bug_condition")

# Floor 1 — test FILES whose name matches the Exploration_Test file convention
# (``*_exploration.py`` reproduces a bug scenario; ``*_bug.py`` pins a specific
# historical bug condition). Per the requirements glossary, Exploration_Tests
# typically live in these files.
_EXPLORATION_BUG_FILE_FLOOR = 20

# Floor 2 — test SYMBOLS (functions/classes) whose name contains an
# exploration / bug-condition marker, across ALL test files (catches
# bug-condition coverage embedded in otherwise-named files).
_EXPLORATION_BUG_SYMBOL_FLOOR = 45


def _is_exploration_or_bug_file(path: Path) -> bool:
    """Return True when a test file follows the Exploration_Test file convention.

    Args:
        path: The ``test_*.py`` file path.

    Returns:
        True if the filename ends in ``_exploration.py`` or ``_bug.py``.
    """
    return path.name.endswith("_exploration.py") or path.name.endswith("_bug.py")


def _count_coverage(roots: list[Path]) -> tuple[int, int]:
    """Count exploration / bug-condition coverage across the given roots.

    Walks every ``test_*.py`` file under the roots and measures coverage at two
    granularities: matching files and matching test symbols.

    Args:
        roots: Directories to search recursively for ``test_*.py`` files.

    Returns:
        A ``(file_count, symbol_count)`` tuple where ``file_count`` is the number
        of files following the Exploration_Test file convention and
        ``symbol_count`` is the number of function/class definitions whose name
        contains an exploration / bug-condition marker.
    """
    file_count = 0
    symbol_count = 0
    for root in roots:
        for path in sorted(root.rglob("test_*.py")):
            if _is_exploration_or_bug_file(path):
                file_count += 1
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    name = node.name.lower()
                    if any(marker in name for marker in _COVERAGE_MARKERS):
                        symbol_count += 1
    return file_count, symbol_count


class TestScanRootsExist:
    """Sanity checks that the real test roots are present."""

    def test_both_scan_roots_exist(self):
        """Both real test roots are on disk before the end-state checks run."""
        assert POWER_TESTS_DIR.is_dir(), f"missing power tests dir: {POWER_TESTS_DIR}"
        assert REPO_TESTS_DIR.is_dir(), f"missing repo tests dir: {REPO_TESTS_DIR}"


class TestDebrittledEndState:
    """The remediated suite has zero brittle findings (Req 4.5, 5.6)."""

    def test_scan_reports_zero_non_allowlisted_findings(self):
        """``scan`` over both real roots reports zero non-allowlisted findings.

        Allowlisted exemptions are an explicit, reviewed decision and are
        therefore permitted (not asserted to be zero). A non-empty
        ``parse_errors`` would mean the scan did not complete over every file, so
        it is asserted empty to guarantee the zero-findings result is total.
        """
        result = scan(SCAN_ROOTS)

        assert result.parse_errors == [], (
            "scan did not complete over all files; parse errors: "
            f"{result.parse_errors}"
        )

        # Zero NON-allowlisted findings across ALL categories.
        detail = "\n".join(
            f"  {f.file_path}:{f.line_number} {f.category.value}"
            for f in result.findings
        )
        assert result.findings == [], (
            "expected zero non-allowlisted brittle findings, found "
            f"{len(result.findings)}:\n{detail}"
        )

        # Belt-and-suspenders: every per-category count is zero.
        counts = result.findings_by_category
        for category in BrittleCategory:
            assert counts[category] == 0, (
                f"category {category.value} has {counts[category]} "
                "non-allowlisted findings (expected 0)"
            )


class TestRegressionCoverageNonDecrease:
    """Exploration / bug-condition coverage did not decrease (Req 6.1, 6.5)."""

    def test_exploration_bug_file_count_at_or_above_floor(self):
        """The count of Exploration_Test files stays at or above the floor.

        Guards Requirement 6.1 (retain every Exploration_Test): deleting an
        ``*_exploration.py`` / ``*_bug.py`` file drops the count below the
        recorded floor and fails this test.
        """
        file_count, _ = _count_coverage(SCAN_ROOTS)
        assert file_count >= _EXPLORATION_BUG_FILE_FLOOR, (
            f"exploration/bug test file count regressed: {file_count} < floor "
            f"{_EXPLORATION_BUG_FILE_FLOOR}; remediation must not remove "
            "historical bug-condition coverage (Req 6.1, 6.5)"
        )

    def test_exploration_bug_symbol_count_at_or_above_floor(self):
        """The count of exploration / bug-condition test symbols stays >= floor.

        Guards Requirement 6.5 (do not reduce the set of detected historical bug
        conditions): removing a test function/class whose name marks it as
        exploration or bug-condition coverage drops the count below the recorded
        floor and fails this test.
        """
        _, symbol_count = _count_coverage(SCAN_ROOTS)
        assert symbol_count >= _EXPLORATION_BUG_SYMBOL_FLOOR, (
            f"exploration/bug-condition test symbol count regressed: "
            f"{symbol_count} < floor {_EXPLORATION_BUG_SYMBOL_FLOOR}; "
            "remediation must not reduce detected bug conditions (Req 6.5)"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
