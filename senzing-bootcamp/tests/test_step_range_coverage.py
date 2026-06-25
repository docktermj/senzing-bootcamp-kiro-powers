"""Property-based tests for the step-range coverage/contiguity checker.

Feature: module-router-standardization, Property 5: For any sequence of module
steps (including lettered sub-steps) partitioned into ordered phase step_ranges,
the step-range checker accepts the partition iff the ranges are contiguous and
non-overlapping under the sub-step-aware (parent_integer, suffix) key ordering
and together cover exactly the module's full step set; introducing a gap, an
overlap, or an uncovered step causes the checker to reject.
"""

import sys
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import check_step_range_coverage, step_sort_key

_LETTERS = "abcdefgh"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_ordered_steps(draw):
    """Generate a module's full step set as an ordered list of step tokens.

    Each parent integer is either a plain integer step (e.g. ``3``) or is split
    into lettered sub-steps (e.g. ``"3a"``, ``"3b"``, ``"3d"``). Parent integers
    are drawn as a sorted distinct set that need not be contiguous (e.g.
    ``1, 2, 5``), exercising the checker's rule that a missing integer which is
    not a real step is not treated as a gap. The returned list is already in
    canonical ``(parent_integer, suffix)`` order.

    Returns:
        list of step tokens (``int`` for plain steps, ``str`` for sub-steps),
        ordered by ``step_sort_key``.
    """
    parents = sorted(draw(st.sets(st.integers(min_value=1, max_value=20),
                                  min_size=1, max_size=8)))
    steps: list = []
    for parent in parents:
        use_substeps = draw(st.booleans())
        if use_substeps:
            n_letters = draw(st.integers(min_value=1, max_value=5))
            # A sorted distinct subset of letters keeps the sub-steps ordered.
            chosen = sorted(draw(st.sets(st.sampled_from(_LETTERS),
                                         min_size=1, max_size=n_letters)),
                            key=lambda c: c)
            for letter in chosen:
                steps.append(f"{parent}{letter}")
        else:
            steps.append(parent)
    return steps


@st.composite
def st_steps_and_partition(draw, min_segments=1):
    """Generate a full step set and a valid ordered partition of it.

    The partition divides the ordered step set into consecutive, contiguous,
    non-overlapping segments. Each phase ``step_range`` is the ``(first, last)``
    pair of a segment, so the partition is a correct cover by construction.

    Args:
        min_segments: Minimum number of phases (segments) to produce. When the
            step set is large enough this forces at least that many cuts.

    Returns:
        tuple ``(steps, segments, step_ranges)`` where ``segments`` is the list
        of contiguous step slices and ``step_ranges`` is the list of
        ``(start, end)`` pairs in document order.
    """
    steps = draw(st_ordered_steps())
    assume(len(steps) >= min_segments)

    n = len(steps)
    # Choose cut positions among the n-1 gaps between consecutive steps.
    gap_count = n - 1
    needed_cuts = max(0, min_segments - 1)
    if gap_count == 0:
        cut_positions: set[int] = set()
    else:
        cuts = draw(st.sets(st.integers(min_value=1, max_value=gap_count),
                            min_size=needed_cuts, max_size=gap_count))
        cut_positions = set(cuts)

    segments: list[list] = []
    current: list = [steps[0]]
    for i in range(1, n):
        if i in cut_positions:
            segments.append(current)
            current = []
        current.append(steps[i])
    segments.append(current)

    step_ranges = [(seg[0], seg[-1]) for seg in segments]
    return steps, segments, step_ranges


# ---------------------------------------------------------------------------
# Property 5: Step-range contiguity and coverage
# ---------------------------------------------------------------------------


class TestProperty5StepRangeContiguityAndCoverage:
    """Feature: module-router-standardization, Property 5: Step-range contiguity and coverage

    For any sequence of module steps (including lettered sub-steps) partitioned
    into ordered phase step_ranges, the step-range checker accepts the partition
    if and only if the ranges are contiguous and non-overlapping under the
    sub-step-aware (parent_integer, suffix) key ordering and together cover
    exactly the module's full step set; introducing a gap, an overlap, or an
    uncovered step causes the checker to reject.

    **Validates: Requirements 3.2, 3.3, 3.4, 5.4**
    """

    @given(data=st_steps_and_partition())
    @settings(max_examples=200)
    def test_accept_contiguous_non_overlapping_full_cover(self, data):
        """A correct contiguous, non-overlapping, full-covering partition is accepted."""
        steps, _segments, step_ranges = data

        violations = check_step_range_coverage(step_ranges, steps, module_label="ModX")

        assert violations == [], (
            f"expected acceptance for ranges={step_ranges!r} over steps={steps!r}, "
            f"but got {[v.message for v in violations]}"
        )

    @given(data=st_steps_and_partition(min_segments=2),
           drop_index=st.integers(min_value=0, max_value=7))
    @settings(max_examples=150)
    def test_reject_on_injected_gap(self, data, drop_index):
        """Dropping a phase range leaves its steps uncovered, so the checker rejects."""
        steps, segments, step_ranges = data
        assume(len(step_ranges) >= 2)

        drop = drop_index % len(step_ranges)
        injured = step_ranges[:drop] + step_ranges[drop + 1:]

        # The dropped segment's steps are now covered by no remaining range
        # (the partition was non-overlapping), so a gap must be reported.
        violations = check_step_range_coverage(injured, steps, module_label="ModGap")

        assert violations, (
            f"expected rejection after dropping range {step_ranges[drop]!r}; "
            f"remaining={injured!r} over steps={steps!r}"
        )

    @given(data=st_steps_and_partition(min_segments=1),
           dup_index=st.integers(min_value=0, max_value=7))
    @settings(max_examples=150)
    def test_reject_on_injected_overlap(self, data, dup_index):
        """Duplicating a phase range double-covers its steps, so the checker rejects."""
        steps, segments, step_ranges = data

        dup = dup_index % len(step_ranges)
        # Appending a duplicate range makes its steps covered twice (overlap).
        injured = step_ranges + [step_ranges[dup]]

        violations = check_step_range_coverage(injured, steps, module_label="ModOverlap")

        assert violations, (
            f"expected rejection after duplicating range {step_ranges[dup]!r}; "
            f"ranges={injured!r} over steps={steps!r}"
        )
        assert any("overlap" in v.message for v in violations), (
            f"expected an overlap violation, got {[v.message for v in violations]}"
        )

    @given(data=st_steps_and_partition())
    @settings(max_examples=150)
    def test_reject_on_uncovered_step(self, data):
        """A step in the full set beyond every range is uncovered, so the checker rejects."""
        steps, _segments, step_ranges = data

        # Add an extra step ordered after all existing steps; the valid partition
        # of the original steps cannot cover it.
        max_parent = max(step_sort_key(s)[0] for s in steps)
        extra = max_parent + 1
        full_with_extra = steps + [extra]

        violations = check_step_range_coverage(
            step_ranges, full_with_extra, module_label="ModUncovered"
        )

        assert violations, (
            f"expected rejection: step {extra!r} uncovered by ranges={step_ranges!r} "
            f"over steps={full_with_extra!r}"
        )
        assert any("gap/uncovered" in v.message for v in violations), (
            f"expected an uncovered violation, got {[v.message for v in violations]}"
        )
