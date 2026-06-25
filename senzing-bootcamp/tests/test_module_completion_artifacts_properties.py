"""Property-based tests for the module-completion-artifacts planner.

Feature: module-completion-artifacts (BUGFIX) — task 4.

Hypothesis-driven coverage of the correctness properties from the design's
Correctness Properties section, exercised against the deterministic planner in
``senzing-bootcamp/scripts/completion_artifacts.py``:

    Property 1 / 6  plan_backfill always yields a set-difference-only plan that
                    completes the artifact set with no duplicates.
    Property 3      compute_module_duration returns a parseable elapsed time
                    exactly when the bounding timestamps are valid and ordered,
                    and None otherwise.
    Property 4      compute_total_duration is monotonically non-decreasing as
                    modules are added and omits (returns None) rather than
                    emitting a placeholder when timing is unreliable.
    Property 5      the backfill plan applies certificates uniformly — every
                    completed module gets one or none at all (never a partial
                    subset).
    Property 2      (preservation) when is_bug_condition is false the planner
                    proposes no changes (an empty plan), so non-buggy inputs are
                    left unchanged.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6, 3.5
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

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
is_placeholder = planner.is_placeholder

MAX_EXAMPLES = 200

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNIT_SECONDS = {"d": 86_400, "h": 3_600, "m": 60, "s": 1}


def _duration_to_seconds(text: str | None) -> float:
    """Convert a formatted Duration string (e.g. ``2d 3h 5m``) back to seconds.

    Args:
        text: A Duration string produced by the planner, or ``None``.

    Returns:
        The total number of seconds the string represents (0.0 for ``None``).
    """
    if text is None:
        return 0.0
    total = 0.0
    for token in text.split():
        total += int(token[:-1]) * _UNIT_SECONDS[token[-1]]
    return total


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Bootcamp modules are numbered 1..12.
st_module = st.integers(min_value=1, max_value=12)

# Clearly-unparseable timestamp values (none parse via datetime.fromisoformat).
_INVALID_TIMESTAMPS = [
    "",
    "   ",
    "not-a-timestamp",
    "Module 3 session",
    "garbage",
    "2025-13-40T99:99:99",
    "yesterday",
]


def st_modules_completed(min_size: int = 0, max_size: int = 12):
    """Strategy: a sorted list of unique completed module numbers."""
    return st.lists(st_module, min_size=min_size, max_size=max_size, unique=True).map(sorted)


@st.composite
def st_timestamp(draw):
    """Strategy: a ``(raw, parsed)`` pair for a single timestamp slot.

    ``raw`` is what gets stored in ``step_history``/``started_at``; ``parsed`` is
    the corresponding ``datetime`` oracle (``None`` when the raw value is missing
    or unparseable).
    """
    kind = draw(st.sampled_from(["valid", "invalid", "missing"]))
    if kind == "valid":
        moment = draw(
            st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2030, 1, 1),
            )
        )
        return moment.isoformat(), moment
    if kind == "invalid":
        return draw(st.sampled_from(_INVALID_TIMESTAMPS)), None
    return None, None


@st.composite
def st_state_and_inventory(draw):
    """Strategy: a ProgressState plus an ArtifactInventory of partial coverage.

    The inventory's recap/journal/certificate sets are arbitrary subsets of the
    completed modules, optionally polluted with extra modules that were never
    completed (to confirm extras never leak into the plan).
    """
    completed = draw(st_modules_completed(min_size=0, max_size=12))

    def _subset() -> set[int]:
        if not completed:
            return set()
        return set(draw(st.lists(st.sampled_from(completed), unique=True)))

    extras = set(draw(st.lists(st_module, unique=True))) - set(completed)

    recap = _subset()
    journal = _subset()
    certs = _subset()
    # Occasionally include artifacts for never-completed modules.
    if draw(st.booleans()):
        recap |= extras
    if draw(st.booleans()):
        journal |= extras
    if draw(st.booleans()):
        certs |= extras

    progress = ProgressState(modules_completed=list(completed), step_history={}, started_at=None)
    inventory = ArtifactInventory(
        recap_sections=recap, journal_entries=journal, certificates=certs
    )
    return progress, inventory, set(completed)


@st.composite
def st_ascending_timeline(draw):
    """Strategy: ``(started_at, step_history, modules)`` with non-decreasing time.

    Each successive module's ``updated_at`` is at or after the previous one's, so
    every per-module elapsed time is non-negative and the cumulative total is
    monotonically non-decreasing.
    """
    n = draw(st.integers(min_value=1, max_value=8))
    base = draw(
        st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2026, 1, 1))
    )
    gaps = draw(
        st.lists(
            st.integers(min_value=0, max_value=200_000),
            min_size=n,
            max_size=n,
        )
    )
    started_at = base.isoformat()
    step_history: dict[str, dict[str, object]] = {}
    current = base
    for index, gap in enumerate(gaps, start=1):
        current = current + timedelta(seconds=gap)
        step_history[str(index)] = {"updated_at": current.isoformat()}
    return started_at, step_history, list(range(1, n + 1))


# ===========================================================================
# Property 1 / 6 — set-difference-only backfill with no duplicates
# ===========================================================================


class TestBackfillCompletesSetWithoutDuplication:
    """plan_backfill completes coverage as a pure set difference.

    Validates: Requirements 2.1, 2.6
    """

    @settings(max_examples=MAX_EXAMPLES)
    @given(st_state_and_inventory())
    def test_plan_is_set_difference_with_no_duplicates(self, case) -> None:
        """The plan is exactly the missing modules, deduplicated, and disjoint
        from what already exists on disk; applying it completes the set."""
        progress, inventory, completed = case
        plan = plan_backfill(progress, inventory)

        expected_recap = sorted(completed - inventory.recap_sections)
        expected_journal = sorted(completed - inventory.journal_entries)
        if inventory.certificates:
            expected_cert = sorted(completed - inventory.certificates)
        else:
            expected_cert = []

        # Set-difference correctness.
        assert plan.recap_modules == expected_recap
        assert plan.journal_modules == expected_journal
        assert plan.certificate_modules == expected_cert

        # No duplicates within any plan list.
        assert len(plan.recap_modules) == len(set(plan.recap_modules))
        assert len(plan.journal_modules) == len(set(plan.journal_modules))
        assert len(plan.certificate_modules) == len(set(plan.certificate_modules))

        # Never re-emit an artifact that already exists.
        assert set(plan.recap_modules).isdisjoint(inventory.recap_sections)
        assert set(plan.journal_modules).isdisjoint(inventory.journal_entries)
        assert set(plan.certificate_modules).isdisjoint(inventory.certificates)

        # Applying the plan completes coverage for every completed module.
        assert (inventory.recap_sections & completed) | set(plan.recap_modules) == completed
        assert (inventory.journal_entries & completed) | set(plan.journal_modules) == completed

    @settings(max_examples=MAX_EXAMPLES)
    @given(st_state_and_inventory())
    def test_replanning_after_backfill_is_idempotent(self, case) -> None:
        """Re-running the planner once the plan is applied yields an empty plan."""
        progress, inventory, completed = case
        plan = plan_backfill(progress, inventory)

        # Simulate applying the plan to the on-disk inventory.
        applied = ArtifactInventory(
            recap_sections=set(inventory.recap_sections) | set(plan.recap_modules),
            journal_entries=set(inventory.journal_entries) | set(plan.journal_modules),
            certificates=set(inventory.certificates) | set(plan.certificate_modules),
        )
        replan = plan_backfill(progress, applied)
        assert replan.is_empty


# ===========================================================================
# Property 3 — real per-module Duration iff bounds valid and ordered
# ===========================================================================


class TestModuleDurationValidity:
    """compute_module_duration returns a value exactly when timing is reliable.

    Validates: Requirements 2.2
    """

    @settings(max_examples=MAX_EXAMPLES)
    @given(lower=st_timestamp(), upper=st_timestamp())
    def test_value_iff_valid_and_ordered_via_prior(self, lower, upper) -> None:
        """With a prior timestamp as the lower bound, a value is returned exactly
        when both bounds parse and end >= start."""
        lower_raw, lower_dt = lower
        upper_raw, upper_dt = upper
        module = 5
        step_history = {str(module): {"updated_at": upper_raw}}

        result = compute_module_duration(step_history, None, module, lower_raw)

        valid = lower_dt is not None and upper_dt is not None and upper_dt >= lower_dt
        if valid:
            assert result is not None
            assert not is_placeholder(result)
        else:
            assert result is None

    @settings(max_examples=MAX_EXAMPLES)
    @given(started=st_timestamp(), upper=st_timestamp())
    def test_first_module_uses_started_at_lower_bound(self, started, upper) -> None:
        """For the first module (prior_timestamp None), started_at is the lower
        bound; a value appears exactly when both bounds parse and are ordered."""
        started_raw, started_dt = started
        upper_raw, upper_dt = upper
        module = 1
        step_history = {str(module): {"updated_at": upper_raw}}

        result = compute_module_duration(step_history, started_raw, module, None)

        valid = started_dt is not None and upper_dt is not None and upper_dt >= started_dt
        if valid:
            assert result is not None
            assert not is_placeholder(result)
        else:
            assert result is None


# ===========================================================================
# Property 4 — monotonic Total Duration, omission over placeholder
# ===========================================================================


class TestTotalDurationMonotonicAndOmits:
    """compute_total_duration is monotonic and never emits a placeholder.

    Validates: Requirements 2.3
    """

    @settings(max_examples=MAX_EXAMPLES)
    @given(st_ascending_timeline())
    def test_total_is_monotonically_non_decreasing(self, timeline) -> None:
        """Adding modules in ascending order never decreases the rolled-up total,
        and any value returned reads as a real duration (never a placeholder)."""
        started_at, step_history, modules = timeline

        previous_seconds = -1.0
        for upto in range(1, len(modules) + 1):
            prefix = modules[:upto]
            total = compute_total_duration(step_history, started_at, prefix)
            if total is not None:
                assert not is_placeholder(total)
            current_seconds = _duration_to_seconds(total)
            assert current_seconds >= previous_seconds
            previous_seconds = current_seconds

    @settings(max_examples=MAX_EXAMPLES)
    @given(
        modules=st_modules_completed(min_size=1, max_size=8),
        timestamps=st.lists(st_timestamp(), min_size=1, max_size=8),
    )
    def test_omits_rather_than_placeholder_when_unreliable(self, modules, timestamps) -> None:
        """The result is either None (omission) or a real duration — never a
        placeholder — regardless of how many timestamps are invalid/missing."""
        step_history: dict[str, dict[str, object]] = {}
        for module, (raw, _parsed) in zip(modules, timestamps):
            step_history[str(module)] = {"updated_at": raw}

        result = compute_total_duration(step_history, None, modules)
        assert result is None or not is_placeholder(result)

    @settings(max_examples=MAX_EXAMPLES)
    @given(modules=st_modules_completed(min_size=1, max_size=8))
    def test_all_invalid_timing_returns_none(self, modules) -> None:
        """When no bound parses, the total is omitted (None), not a placeholder."""
        step_history = {str(m): {"updated_at": "not-a-timestamp"} for m in modules}
        assert compute_total_duration(step_history, None, modules) is None


# ===========================================================================
# Property 5 — uniform certificate application
# ===========================================================================


class TestUniformCertificateApplication:
    """The backfill plan applies certificates uniformly (all or none).

    Validates: Requirements 2.4
    """

    @settings(max_examples=MAX_EXAMPLES)
    @given(data=st.data())
    def test_non_uniform_certs_backfill_to_full_coverage(self, data) -> None:
        """Given some-but-not-all certificates, the plan covers every remaining
        completed module so the applied set is complete — never a partial subset."""
        completed = data.draw(st_modules_completed(min_size=2, max_size=12))
        assume(len(completed) >= 2)
        # A non-empty proper subset of completed modules has certificates.
        present = set(
            data.draw(
                st.lists(
                    st.sampled_from(completed),
                    min_size=1,
                    max_size=len(completed) - 1,
                    unique=True,
                )
            )
        )
        assume(0 < len(present) < len(completed))

        progress = ProgressState(modules_completed=list(completed))
        inventory = ArtifactInventory(
            recap_sections=set(completed),
            journal_entries=set(completed),
            certificates=set(present),
        )

        # This state is a bug condition via the non-uniform-certificate clause.
        assert is_bug_condition(progress, inventory, {}, None)

        plan = plan_backfill(progress, inventory)
        applied = present | set(plan.certificate_modules)
        # Uniform: every completed module ends up with a certificate.
        assert applied == set(completed)

    @settings(max_examples=MAX_EXAMPLES)
    @given(completed=st_modules_completed(min_size=1, max_size=12))
    def test_no_certificates_anywhere_requires_none(self, completed) -> None:
        """When no certificates exist at all, the plan requests none (uniform=none)."""
        progress = ProgressState(modules_completed=list(completed))
        inventory = ArtifactInventory(
            recap_sections=set(completed),
            journal_entries=set(completed),
            certificates=set(),
        )
        plan = plan_backfill(progress, inventory)
        assert plan.certificate_modules == []


# ===========================================================================
# Property 2 — preservation: non-buggy inputs are left unchanged
# ===========================================================================


class TestPreservationNonBuggyInputsUnchanged:
    """When is_bug_condition is false, the planner proposes no changes.

    Validates: Requirements 3.5
    """

    @settings(max_examples=MAX_EXAMPLES)
    @given(
        completed=st_modules_completed(min_size=0, max_size=12),
        certs_full=st.booleans(),
        recap_total=st.one_of(st.none(), st.text(max_size=12)),
    )
    def test_no_bug_condition_implies_empty_plan(
        self, completed, certs_full, recap_total
    ) -> None:
        """A complete, uniform, no-derivable-timing state is not a bug condition,
        and the planner therefore yields an empty (no-change) plan."""
        completed_set = set(completed)
        # Complete recap/journal coverage + uniform certificates (full or none),
        # with no derivable timing so duration clauses cannot fire.
        certs = set(completed_set) if certs_full else set()
        progress = ProgressState(
            modules_completed=list(completed), step_history={}, started_at=None
        )
        inventory = ArtifactInventory(
            recap_sections=set(completed_set),
            journal_entries=set(completed_set),
            certificates=certs,
        )

        # Constructed to be non-buggy; confirm before asserting preservation.
        assume(not is_bug_condition(progress, inventory, {}, recap_total))

        plan = plan_backfill(progress, inventory)
        assert plan.is_empty
        assert plan.recap_modules == []
        assert plan.journal_modules == []
        assert plan.certificate_modules == []
