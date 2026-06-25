"""Property tests for the test-suite-debrittling remediation invariants.

This module property-tests the *general* invariant behind the remediated
Exact_Count_Assertions (Task 7.1): a non-regression threshold check. Task 7.1
replaced whole-suite/total count equality checks (e.g.
``_PASSING_BASELINE == 4648``) in ``test_onboarding_split_preservation.py`` with
a threshold of the form ``observed >= FLOOR``. This file validates the
*remediation pattern itself* — not the specific constant — so that the
debrittling guarantee is locked down:

- Adding or splitting tests (observed grows >= floor) never fails the check.
- A genuine regression / coverage drop (observed < floor) always fails it.

The threshold semantics are modelled here as a trivial pure predicate
``passes(observed, floor) == (observed >= floor)`` that represents the
remediation pattern. A live spot-check also confirms the remediation in
``test_onboarding_split_preservation.py`` satisfies the invariant.

**Validates: Requirements 4.1, 4.3, 4.4**
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Threshold semantics under test (the remediation pattern, as a pure predicate)
# ---------------------------------------------------------------------------


def passes(observed: int, floor: int) -> bool:
    """Return the non-regression threshold result.

    Models the remediated count assertion: the check passes if and only if the
    observed total/passing test count is at or above the recorded floor.

    Args:
        observed: The total/passing test count measured on the current tree.
        floor: The recorded non-regression floor.

    Returns:
        True when ``observed >= floor`` (no regression), False otherwise.
    """
    return observed >= floor


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Floors span small and realistic whole-suite counts; bounded so generation is
# cheap while still covering zero, small, and large baselines.
st_floor = st.integers(min_value=0, max_value=10_000)

# A non-negative slack representing tests added or split out (observed grows).
st_delta = st.integers(min_value=0, max_value=10_000)


# ---------------------------------------------------------------------------
# Property 7: Remediated count assertion is a non-regression threshold
# ---------------------------------------------------------------------------


class TestRemediatedCountThreshold:
    """The remediated count assertion is a non-regression threshold.

    **Validates: Requirements 4.1, 4.3, 4.4**

    Requirement 4.1/4.3: replacing an Exact_Count_Assertion with
    ``observed >= FLOOR`` keeps the check green when tests are added or an
    existing file is split into more tests. Requirement 4.4: the check fails
    when the observed count drops below the recorded floor.
    """

    # Feature: test-suite-debrittling, Property 7: For any observed
    # total/passing test count, the remediated count assertion passes if and
    # only if the observed count is greater than or equal to the recorded floor.
    @given(observed=st.integers(min_value=0, max_value=20_000), floor=st_floor)
    @settings(max_examples=100)
    def test_passes_iff_observed_at_least_floor(
        self, observed: int, floor: int
    ) -> None:
        """The threshold passes iff observed >= floor (the core biconditional)."""
        assert passes(observed, floor) == (observed >= floor)

    # Feature: test-suite-debrittling, Property 7: Adding or splitting tests
    # (observed = floor + delta, delta >= 0) never fails the check.
    @given(floor=st_floor, delta=st_delta)
    @settings(max_examples=100)
    def test_adding_or_splitting_tests_never_fails(
        self, floor: int, delta: int
    ) -> None:
        """observed at or above the floor (tests added/split) always passes (Req 4.1, 4.3)."""
        observed = floor + delta
        assert passes(observed, floor) is True

    # Feature: test-suite-debrittling, Property 7: A count below the floor (a
    # real regression / coverage drop) always fails the check.
    @given(floor=st.integers(min_value=1, max_value=10_000), drop=st_delta)
    @settings(max_examples=100)
    def test_below_floor_always_fails(self, floor: int, drop: int) -> None:
        """observed below the floor (a genuine drop) always fails (Req 4.4)."""
        # observed = floor - (drop + 1), clamped at 0 so it stays a valid count
        # while remaining strictly below the floor.
        observed = max(0, floor - (drop + 1))
        assert observed < floor
        assert passes(observed, floor) is False


# ---------------------------------------------------------------------------
# Live remediation spot-check: the shipped threshold satisfies the invariant
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)


class TestLiveRemediationSatisfiesInvariant:
    """The remediation in test_onboarding_split_preservation.py is a threshold.

    **Validates: Requirements 4.1, 4.3, 4.4**

    Confirms the live remediation uses a recorded baseline at or above its
    non-regression floor and that the threshold predicate accepts it — tying the
    general Property 7 invariant to the concrete remediated assertion.
    """

    def test_passing_baseline_satisfies_floor(self) -> None:
        """The shipped _PASSING_BASELINE/_PASSING_FLOOR pass the threshold."""
        from test_onboarding_split_preservation import (  # noqa: E402
            _PASSING_BASELINE,
            _PASSING_FLOOR,
        )

        assert passes(_PASSING_BASELINE, _PASSING_FLOOR) is True
        assert _PASSING_BASELINE >= _PASSING_FLOOR


# ---------------------------------------------------------------------------
# Property 8: Remediated snapshot assertion is a marker-membership check
# ---------------------------------------------------------------------------
#
# Tasks 8.1/8.2 replaced whole-file and section SHA-256 snapshot assertions with
# structural marker checks. The general remediation invariant is: "assert every
# required marker is PRESENT in the content (membership), tolerating arbitrary
# unrelated additions; fail if a required marker is removed." This is modelled
# here as the pure predicate ``markers_present``.


def markers_present(content: str, required: list[str]) -> bool:
    """Return whether every required marker is present in the content.

    Models the remediated whole-file/section snapshot assertion: the check
    passes if and only if every required marker is a substring of the content,
    regardless of any unrelated additions.

    Args:
        content: The (possibly edited) file/section text under test.
        required: The required markers the remediated snapshot protects.

    Returns:
        True when every marker in ``required`` is present in ``content``.
    """
    return all(m in content for m in required)


# A required marker is wrapped in unique sentinels (``@@MARKER_{i}@@``) so it is
# unambiguous and cannot accidentally substring-collide with extra content.
st_required_markers = st.lists(
    st.integers(min_value=0, max_value=10_000),
    min_size=1,
    max_size=8,
    unique=True,
).map(lambda ids: [f"@@MARKER_{i}@@" for i in ids])

# Arbitrary unrelated additions (benign edits). Restricted to an alphabet that
# excludes ``@`` so generated text can never contain a sentinel-wrapped marker.
st_extra_content = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z", "S"),
        blacklist_characters="@",
    ),
    max_size=40,
)


class TestRemediatedSnapshotMarkerCheck:
    """The remediated snapshot assertion is a marker-membership check.

    **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

    Requirement 5.1/5.2: a whole-file/section content-hash snapshot is replaced
    by Structural_Assertions that verify the required markers are present.
    Requirement 5.4: a benign, unrelated edit (arbitrary additions) leaves the
    remediated assertion passing. Requirement 5.5: removing a required marker
    causes the remediated assertion to fail.
    """

    # Feature: test-suite-debrittling, Property 8: For any required-marker set,
    # content built from all markers plus arbitrary unrelated additions (in any
    # arrangement) still satisfies the membership check (tolerates additions).
    @given(
        markers=st_required_markers,
        extras=st.lists(st_extra_content, max_size=10),
        seed=st.integers(min_value=0, max_value=2**32 - 1),
    )
    @settings(max_examples=100)
    def test_all_markers_plus_additions_pass(
        self, markers: list[str], extras: list[str], seed: int
    ) -> None:
        """All markers present + arbitrary additions in any order pass (Req 5.1, 5.2, 5.4)."""
        # Interleave markers and benign extra content in a shuffled arrangement.
        pieces = list(markers) + list(extras)
        # Deterministic shuffle driven by the generated seed.
        rng = random.Random(seed)
        rng.shuffle(pieces)
        content = "\n".join(pieces)
        assert markers_present(content, markers) is True

    # Feature: test-suite-debrittling, Property 8: Removing a required marker
    # from the content causes the membership check to fail (removal detected).
    @given(
        markers=st_required_markers,
        extras=st.lists(st_extra_content, max_size=10),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_removing_a_marker_fails(
        self, markers: list[str], extras: list[str], data: st.DataObject
    ) -> None:
        """Content missing a required marker fails the check (Req 5.5)."""
        # Pick one required marker to omit from the assembled content.
        omitted = data.draw(st.sampled_from(markers))
        remaining = [m for m in markers if m != omitted]
        content = "\n".join(remaining + list(extras))
        # The omitted marker (with its unique sentinel) is absent, so the
        # membership check must report failure.
        assert markers_present(content, markers) is False


# ---------------------------------------------------------------------------
# Property 9: Remediated sequence assertion is an ordered-subsequence check
# ---------------------------------------------------------------------------
#
# Task 9.1 replaced full heading/line-list equality checks (e.g.
# ``_extract_headings(content) == _HEADINGS_*``) with ordered-subsequence
# assertions: the REQUIRED headings must appear in the actual list in the
# required relative order, tolerating arbitrary interleaved/unrelated additions;
# the check fails if a required heading is removed OR if two required headings
# are reordered. The general remediation invariant is modelled here as the pure
# predicate ``is_ordered_subsequence`` (the standard subsequence check that
# walks ``actual`` with a single shared iterator, which also handles duplicates
# correctly).


def is_ordered_subsequence(actual: list[str], required: list[str]) -> bool:
    """Return whether ``required`` appears as an ordered subsequence of ``actual``.

    Models the remediated heading/line-sequence assertion: the check passes if
    and only if every required heading appears in ``actual`` in the required
    relative order, regardless of any unrelated additions interleaved between
    them. Uses a single shared iterator so each ``required`` element consumes
    ``actual`` left-to-right (correctly handling duplicates).

    Args:
        actual: The (possibly edited) extracted heading/line list under test.
        required: The required headings in their required relative order.

    Returns:
        True when ``required`` is an ordered subsequence of ``actual``.
    """
    it = iter(actual)
    return all(req in it for req in required)


def _interleave_keep_order(
    required: list[str], extras: list[str], rng: random.Random
) -> list[str]:
    """Insert ``extras`` at arbitrary positions while preserving required order.

    Args:
        required: Headings whose relative order must be preserved.
        extras: Unrelated headings to interleave at arbitrary positions.
        rng: Seeded RNG driving the insertion positions (deterministic).

    Returns:
        A new list containing all of ``required`` (in their original relative
        order) with ``extras`` inserted at arbitrary positions.
    """
    result = list(required)
    for extra in extras:
        pos = rng.randint(0, len(result))
        result.insert(pos, extra)
    return result


# Required headings are distinct, unique sentinel tokens (``@@HEADING_{i}@@``) so
# a removed or reordered required token cannot be satisfied elsewhere in the
# actual list.
st_required_headings = st.lists(
    st.integers(min_value=0, max_value=10_000),
    min_size=1,
    max_size=8,
    unique=True,
).map(lambda ids: [f"@@HEADING_{i}@@" for i in ids])

# Unrelated "extra" headings, drawn from a disjoint namespace (``@@EXTRA_{i}@@``)
# so they can never collide with a required heading sentinel.
st_extra_headings = st.lists(
    st.integers(min_value=0, max_value=10_000).map(lambda i: f"@@EXTRA_{i}@@"),
    max_size=10,
)


class TestRemediatedSequenceOrderedSubsequence:
    """The remediated sequence assertion is an ordered-subsequence check.

    **Validates: Requirements 5.3, 5.4, 5.5**

    Requirement 5.3: a full heading/line-list equality snapshot is replaced by a
    Structural_Assertion that verifies the required headings are present in the
    required relative order. Requirement 5.4: a benign, unrelated edit (arbitrary
    interleaved additions) leaves the remediated assertion passing. Requirement
    5.5: removing a required heading OR reordering two required headings causes
    the remediated assertion to fail.
    """

    # Feature: test-suite-debrittling, Property 9: For any required headings in a
    # chosen order, an actual list built from those headings (in order) plus
    # arbitrary interleaved unrelated additions satisfies the ordered-subsequence
    # check (tolerates additions).
    @given(
        required=st_required_headings,
        extras=st_extra_headings,
        seed=st.integers(min_value=0, max_value=2**32 - 1),
    )
    @settings(max_examples=100)
    def test_required_in_order_plus_additions_pass(
        self, required: list[str], extras: list[str], seed: int
    ) -> None:
        """Required headings in order + arbitrary interleaved extras pass (Req 5.3, 5.4)."""
        rng = random.Random(seed)
        actual = _interleave_keep_order(required, extras, rng)
        assert is_ordered_subsequence(actual, required) is True

    # Feature: test-suite-debrittling, Property 9: Removing a required heading
    # from the actual list causes the ordered-subsequence check to fail (removal
    # detected), even with arbitrary interleaved additions present.
    @given(
        required=st_required_headings,
        extras=st_extra_headings,
        seed=st.integers(min_value=0, max_value=2**32 - 1),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_removing_a_required_heading_fails(
        self,
        required: list[str],
        extras: list[str],
        seed: int,
        data: st.DataObject,
    ) -> None:
        """An actual list missing a required heading fails the check (Req 5.5)."""
        omitted = data.draw(st.sampled_from(required))
        remaining = [h for h in required if h != omitted]
        rng = random.Random(seed)
        actual = _interleave_keep_order(remaining, extras, rng)
        # The omitted required heading (a unique sentinel) is absent, so the
        # ordered-subsequence check must report failure.
        assert is_ordered_subsequence(actual, required) is False

    # Feature: test-suite-debrittling, Property 9: Swapping two adjacent required
    # headings out of their required relative order (with each required heading
    # still present exactly once, plus optional unrelated additions) causes the
    # ordered-subsequence check to fail (reordering detected).
    @given(
        required=st.lists(
            st.integers(min_value=0, max_value=10_000),
            min_size=2,
            max_size=8,
            unique=True,
        ).map(lambda ids: [f"@@HEADING_{i}@@" for i in ids]),
        extras=st_extra_headings,
        seed=st.integers(min_value=0, max_value=2**32 - 1),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_reordering_two_required_headings_fails(
        self,
        required: list[str],
        extras: list[str],
        seed: int,
        data: st.DataObject,
    ) -> None:
        """Two required headings swapped out of order fail the check (Req 5.5)."""
        # Swap an adjacent pair so their required relative order is genuinely
        # violated; each required heading still appears exactly once, so the
        # swapped pair cannot be satisfied elsewhere in the actual list.
        i = data.draw(st.integers(min_value=0, max_value=len(required) - 2))
        reordered = list(required)
        reordered[i], reordered[i + 1] = reordered[i + 1], reordered[i]
        rng = random.Random(seed)
        # Interleave unrelated additions while preserving the (swapped) order so
        # the only ordering of the required headings is the reordered one.
        actual = _interleave_keep_order(reordered, extras, rng)
        assert is_ordered_subsequence(actual, required) is False
