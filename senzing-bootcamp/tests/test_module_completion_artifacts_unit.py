"""Unit tests for the module-completion-artifacts planner.

Feature: module-completion-artifacts (BUGFIX) — task 3.5.

Example-based and edge-case coverage for the deterministic planner in
``senzing-bootcamp/scripts/completion_artifacts.py`` (created in task 3.1).
These complement the property-based suites by pinning concrete behavior:

    compute_module_duration  valid bounds -> formatted elapsed time;
                             missing/unparseable/out-of-order bounds -> None;
                             first module uses started_at as the lower bound.
    compute_total_duration   roll-up correctness; None when no reliable timing;
                             monotonic non-decrease.
    detect_artifact_gaps     correct per-type missing-module lists;
                             uniform-certificate rule.
    plan_backfill            idempotency (complete set -> empty plan);
                             set-difference only.
    is_bug_condition         each clause (coverage gap, non-uniform certificates,
                             placeholder duration, placeholder total) toggles the
                             result as specified.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts as planner  # noqa: E402

ProgressState = planner.ProgressState
ArtifactInventory = planner.ArtifactInventory
compute_module_duration = planner.compute_module_duration
compute_total_duration = planner.compute_total_duration
detect_artifact_gaps = planner.detect_artifact_gaps
plan_backfill = planner.plan_backfill
is_bug_condition = planner.is_bug_condition


# ---------------------------------------------------------------------------
# Shared fixture data.
# ---------------------------------------------------------------------------

STARTED_AT = "2025-01-10T09:00:00Z"

# Ordered ISO 8601 timestamps. Module 3 elapses 11:30 -> 12:42 == 1h 12m.
STEP_HISTORY: dict[str, dict[str, object]] = {
    "1": {"last_completed_step": 5, "updated_at": "2025-01-10T10:12:00Z"},
    "2": {"last_completed_step": 5, "updated_at": "2025-01-10T11:30:00Z"},
    "3": {"last_completed_step": 5, "updated_at": "2025-01-10T12:42:00Z"},
}


def _inventory(recap=(), journal=(), certs=()) -> ArtifactInventory:
    """Build an ArtifactInventory from iterables of module numbers."""
    return ArtifactInventory(
        recap_sections=set(recap),
        journal_entries=set(journal),
        certificates=set(certs),
    )


# ===========================================================================
# compute_module_duration
# ===========================================================================


class TestComputeModuleDuration:
    """Per-module elapsed-time computation from ISO 8601 timestamps.

    Validates: Requirements 2.2
    """

    def test_valid_bounds_format_elapsed_time(self) -> None:
        """Module 3 (11:30 -> 12:42) formats to '1h 12m'."""
        prior = STEP_HISTORY["2"]["updated_at"]
        result = compute_module_duration(STEP_HISTORY, STARTED_AT, 3, prior)
        assert result == "1h 12m"

    def test_first_module_uses_started_at_as_lower_bound(self) -> None:
        """With prior_timestamp None, started_at bounds the first module."""
        # started_at 09:00 -> module 1 updated_at 10:12 == 1h 12m.
        result = compute_module_duration(STEP_HISTORY, STARTED_AT, 1, None)
        assert result == "1h 12m"

    def test_minutes_only_elapsed_time(self) -> None:
        """A sub-hour span formats with minutes only."""
        history = {"5": {"updated_at": "2025-01-10T10:45:00Z"}}
        result = compute_module_duration(history, None, 5, "2025-01-10T10:00:00Z")
        assert result == "45m"

    def test_multi_day_elapsed_time(self) -> None:
        """A multi-day span includes the days unit."""
        history = {"6": {"updated_at": "2025-01-12T12:00:00Z"}}
        result = compute_module_duration(history, None, 6, "2025-01-10T09:00:00Z")
        assert result == "2d 3h"

    def test_missing_module_entry_returns_none(self) -> None:
        """A module absent from step_history yields None (omit Duration)."""
        result = compute_module_duration(STEP_HISTORY, STARTED_AT, 9, None)
        assert result is None

    def test_unparseable_upper_bound_returns_none(self) -> None:
        """An unparseable upper-bound timestamp yields None."""
        history = {"4": {"updated_at": "not-a-timestamp"}}
        result = compute_module_duration(history, STARTED_AT, 4, STARTED_AT)
        assert result is None

    def test_missing_lower_bound_returns_none(self) -> None:
        """A first module with no started_at lower bound yields None."""
        history = {"1": {"updated_at": "2025-01-10T10:12:00Z"}}
        result = compute_module_duration(history, None, 1, None)
        assert result is None

    def test_out_of_order_bounds_returns_none(self) -> None:
        """end < start (out-of-order bounds) yields None."""
        history = {"2": {"updated_at": "2025-01-10T10:00:00Z"}}
        # prior_timestamp is later than the module's updated_at.
        result = compute_module_duration(history, None, 2, "2025-01-10T11:00:00Z")
        assert result is None

    def test_z_suffix_is_normalized(self) -> None:
        """Trailing 'Z' is treated as +00:00 and parses successfully."""
        history = {"1": {"updated_at": "2025-01-10T10:00:00Z"}}
        result = compute_module_duration(history, "2025-01-10T09:00:00Z", 1, None)
        assert result == "1h"


# ===========================================================================
# compute_total_duration
# ===========================================================================


class TestComputeTotalDuration:
    """Cumulative roll-up of per-module elapsed times.

    Validates: Requirements 2.3
    """

    def test_roll_up_correctness(self) -> None:
        """Total sums per-module spans across modules 1-3."""
        # M1: 09:00->10:12 (1h12m), M2: 10:12->11:30 (1h18m), M3: 11:30->12:42 (1h12m).
        # Total = 3h 42m.
        result = compute_total_duration(STEP_HISTORY, STARTED_AT, [1, 2, 3])
        assert result == "3h 42m"

    def test_none_when_no_reliable_timing(self) -> None:
        """No reliable per-module timing yields None."""
        history = {"1": {"updated_at": "bad"}}
        result = compute_total_duration(history, None, [1])
        assert result is None

    def test_empty_modules_returns_none(self) -> None:
        """An empty completed set has no timing to roll up."""
        assert compute_total_duration(STEP_HISTORY, STARTED_AT, []) is None

    def test_monotonic_non_decrease_as_modules_added(self) -> None:
        """Total is monotonically non-decreasing as modules are added."""

        def _seconds(text: str | None) -> float:
            if text is None:
                return 0.0
            total = 0.0
            for token in text.split():
                unit = token[-1]
                value = int(token[:-1])
                total += value * {"d": 86_400, "h": 3_600, "m": 60, "s": 1}[unit]
            return total

        prev = -1.0
        for upto in ([1], [1, 2], [1, 2, 3]):
            current = _seconds(compute_total_duration(STEP_HISTORY, STARTED_AT, upto))
            assert current >= prev, f"Total decreased at {upto}"
            prev = current
        assert prev > 0

    def test_partial_reliable_timing_rolls_up_available(self) -> None:
        """Modules absent from history are skipped, reliable ones summed."""
        history = {
            "1": {"updated_at": "2025-01-10T10:00:00Z"},
            # Module 2 is absent from history entirely.
            "3": {"updated_at": "2025-01-10T12:00:00Z"},
        }
        # M1: 09:00->10:00 = 1h (reliable). M2 absent -> skipped and the prior
        # bound stays M1's 10:00. M3: 10:00->12:00 = 2h. Total = 3h.
        result = compute_total_duration(history, STARTED_AT, [1, 2, 3])
        assert result == "3h"


# ===========================================================================
# detect_artifact_gaps
# ===========================================================================


class TestDetectArtifactGaps:
    """Per-type missing-module lists and the uniform-certificate rule.

    Validates: Requirements 2.1, 2.4, 2.6
    """

    def test_per_type_missing_lists_are_sorted(self) -> None:
        """Each missing list reflects the set difference, sorted ascending."""
        inv = _inventory(recap={1, 2, 3, 4, 5, 6}, journal={3, 6, 7}, certs={6, 7})
        report = detect_artifact_gaps([1, 2, 3, 4, 5, 6, 7], inv)
        assert report.missing_recap == [7]
        assert report.missing_journal == [1, 2, 4, 5]
        assert report.missing_certificate == [1, 2, 3, 4, 5]

    def test_complete_set_has_no_gaps(self) -> None:
        """A fully covered, uniform set reports no missing artifacts."""
        inv = _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs={1, 2, 3})
        report = detect_artifact_gaps([1, 2, 3], inv)
        assert report.missing_recap == []
        assert report.missing_journal == []
        assert report.missing_certificate == []

    def test_no_certificates_anywhere_requires_none(self) -> None:
        """When no certificates exist at all, none are required (uniform=none)."""
        inv = _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs=set())
        report = detect_artifact_gaps([1, 2, 3], inv)
        assert report.missing_certificate == []

    def test_any_certificate_requires_all(self) -> None:
        """Once any certificate exists, every completed module requires one."""
        inv = _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs={2})
        report = detect_artifact_gaps([1, 2, 3], inv)
        assert report.missing_certificate == [1, 3]

    def test_aliases_match_primary_fields(self) -> None:
        """Alias properties mirror the primary missing-list fields."""
        inv = _inventory(recap={1}, journal={2}, certs={3})
        report = detect_artifact_gaps([1, 2, 3], inv)
        assert report.missing_recap_sections == report.missing_recap
        assert report.missing_journal_entries == report.missing_journal
        assert report.missing_certificates == report.missing_certificate
        assert report.missing_certs == report.missing_certificate


# ===========================================================================
# plan_backfill
# ===========================================================================


class TestPlanBackfill:
    """Deterministic, idempotent, set-difference-only backfill planning.

    Validates: Requirements 2.6
    """

    def test_set_difference_only(self) -> None:
        """Plan lists are exactly the missing modules; existing are never re-emitted."""
        progress = ProgressState(
            modules_completed=[1, 2, 3, 4, 5, 6, 7],
            step_history=STEP_HISTORY,
            started_at=STARTED_AT,
        )
        inv = _inventory(recap={1, 2, 3, 4, 5, 6}, journal={3, 6, 7}, certs={6, 7})
        plan = plan_backfill(progress, inv)
        assert plan.recap_modules == [7]
        assert plan.journal_modules == [1, 2, 4, 5]
        assert plan.certificate_modules == [1, 2, 3, 4, 5]
        # Nothing already on disk is in the plan.
        assert set(plan.recap_modules).isdisjoint({1, 2, 3, 4, 5, 6})
        assert set(plan.journal_modules).isdisjoint({3, 6, 7})
        assert set(plan.certificate_modules).isdisjoint({6, 7})

    def test_idempotency_complete_set_yields_empty_plan(self) -> None:
        """Re-running on a complete, consistent set yields an empty plan."""
        progress = ProgressState(
            modules_completed=[1, 2, 3],
            step_history=STEP_HISTORY,
            started_at=STARTED_AT,
        )
        inv = _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs={1, 2, 3})
        plan = plan_backfill(progress, inv)
        assert plan.recap_modules == []
        assert plan.journal_modules == []
        assert plan.certificate_modules == []
        assert plan.is_empty

    def test_plan_carries_computed_durations(self) -> None:
        """The plan exposes reliable per-module Durations and a Total Duration."""
        progress = ProgressState(
            modules_completed=[1, 2, 3],
            step_history=STEP_HISTORY,
            started_at=STARTED_AT,
        )
        plan = plan_backfill(progress, _inventory())
        assert plan.module_durations[3] == "1h 12m"
        assert plan.total_duration == "3h 42m"

    def test_unreliable_timing_omits_duration(self) -> None:
        """Modules without reliable timing are absent from module_durations."""
        history = {"1": {"updated_at": "bad"}}
        progress = ProgressState(
            modules_completed=[1],
            step_history=history,
            started_at=None,
        )
        plan = plan_backfill(progress, _inventory())
        assert 1 not in plan.module_durations
        assert plan.total_duration is None


# ===========================================================================
# is_bug_condition
# ===========================================================================


class TestIsBugCondition:
    """Each clause toggles the bug condition as specified.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4
    """

    def _clean_progress(self) -> ProgressState:
        return ProgressState(
            modules_completed=[1, 2, 3],
            step_history=STEP_HISTORY,
            started_at=STARTED_AT,
        )

    def _clean_inventory(self) -> ArtifactInventory:
        return _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs={1, 2, 3})

    def _real_durations(self) -> dict[int, str]:
        return {1: "1h 12m", 2: "1h 18m", 3: "1h 12m"}

    def test_clean_state_is_not_a_bug_condition(self) -> None:
        """A complete, uniform, real-Duration state is not a bug condition."""
        assert not is_bug_condition(
            self._clean_progress(),
            self._clean_inventory(),
            self._real_durations(),
            "3h 42m",
        )

    def test_coverage_gap_clause(self) -> None:
        """A missing artifact type for a completed module toggles the result."""
        inv = _inventory(recap={1, 2}, journal={1, 2, 3}, certs={1, 2, 3})
        assert is_bug_condition(
            self._clean_progress(), inv, self._real_durations(), "3h 42m"
        )

    def test_non_uniform_certificate_clause(self) -> None:
        """Some-but-not-all certificates present toggles the result."""
        # recap/journal complete so coverage gap is only via the certificate rule.
        inv = _inventory(recap={1, 2, 3}, journal={1, 2, 3}, certs={2})
        assert is_bug_condition(
            self._clean_progress(), inv, self._real_durations(), "3h 42m"
        )

    def test_placeholder_duration_clause(self) -> None:
        """A placeholder per-module Duration with real timing toggles the result."""
        durations = {1: "1h 12m", 2: "Module 2 session", 3: "1h 12m"}
        assert is_bug_condition(
            self._clean_progress(), self._clean_inventory(), durations, "3h 42m"
        )

    def test_placeholder_total_clause(self) -> None:
        """A placeholder Total Duration with real timing toggles the result."""
        assert is_bug_condition(
            self._clean_progress(),
            self._clean_inventory(),
            self._real_durations(),
            "Module N session",
        )

    def test_placeholder_duration_ignored_when_timing_unreliable(self) -> None:
        """A placeholder Duration does not trigger when no real timing exists."""
        progress = ProgressState(
            modules_completed=[1, 2, 3],
            step_history={},  # no timing at all
            started_at=None,
        )
        durations = {1: "Module 1 session", 2: "Module 2 session", 3: "Module 3 session"}
        # No coverage gap, uniform certs, no derivable timing -> not a bug condition.
        assert not is_bug_condition(
            progress, self._clean_inventory(), durations, "Module N session"
        )
