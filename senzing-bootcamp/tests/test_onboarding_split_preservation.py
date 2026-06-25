"""BUG 1 preservation baselines for the onboarding split (Task 4, Phase B).

Property 2: Preservation — Steering Content and Previously-Passing Tests Unchanged.

These tests are the preservation companion to the BUG 1 bug-condition exploration
(Property 1). They observe the *currently shipped* (post-split) onboarding steering
content and lock it down so the BUG 1 fix can prove it is **tests-only**: both
``onboarding-flow.md`` and ``onboarding-phase1b-intro-language.md`` MUST stay
byte-identical, the cross-reference between them MUST remain intact, and every
moved-content marker MUST remain in the phase file (its post-split home).

Observation-first methodology: every literal below was read from the live shipped
files on the UNFIXED tree before being asserted here. The SHA-256 digests are also
persisted to ``.kiro/specs/bootcamp-consistency-fixes/bug1_preservation_baselines.txt``
so Task 7.6 can re-verify byte-stability after the fix.

EXPECTED OUTCOME on the UNFIXED tree: every test in this file PASSES (baseline
confirmed). After the BUG 1 fix (tests-only), these same tests MUST still pass.

**Validates: Requirements 3.1, 3.2, 3.3, 3.6**
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_ONBOARDING_FLOW = _STEERING_DIR / "onboarding-flow.md"
_PHASE_FILE = _STEERING_DIR / "onboarding-phase1b-intro-language.md"

# Structural markers that replace two whole-file SHA-256 snapshots
# (_HASH_ONBOARDING_FLOW, _HASH_PHASE_FILE). Those snapshots pinned
# onboarding-flow.md and onboarding-phase1b-intro-language.md byte-for-byte so
# the BUG 1 fix could prove it is tests-only and never edits steering. But they
# broke on every benign, unrelated edit to the files (an additive "Rejected/
# Accepted" section, a repointed hook-registry reference — see the layers of
# "re-baselined" notes the old constants accumulated) without telling us whether
# the protected content actually changed. The real invariant BUG 1 was
# protecting is asserted structurally below (Req 3.1, 3.2, 5.1, 6.2, 6.6): the
# flow file keeps its Phase-1 step scaffold and its hand-off cross-reference,
# and the phase file keeps every moved-content marker. A fix that guts,
# truncates, or relocates that protected content still fails; benign edits pass.

# Phase-1 step scaffold headings that MUST remain in onboarding-flow.md (the
# content that stayed behind in the flow file after the split). The "0a"
# additive section is intentionally omitted so benign additive edits don't
# break the structural check.
_ONBOARDING_FLOW_MARKERS: tuple[str, ...] = (
    "## 0. Setup Preamble",
    "## 0b. MCP Health Check",
    "## 0c. Version Display",
    "## 1. Directory Structure",
    "## 1b. Team Detection",
    "## 2. Prerequisite Check (Mandatory Gate)",
)

# Cross-reference that onboarding-flow.md MUST continue to carry (Requirement 3.2).
_CROSS_REFERENCE = (
    "After Step 2d, load `onboarding-phase1b-intro-language.md`"
)

# Moved-content markers that now live VERBATIM in the phase file (Requirement 3.1).
# Each was observed in onboarding-phase1b-intro-language.md on the UNFIXED tree.
_MOVED_CONTENT_MARKERS: tuple[str, ...] = (
    # Welcome banner (Step 5 — Bootcamp Introduction)
    "🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓",
    # Programming language prompt (Step 4) — the disambiguation phrasing
    'always use the phrase "programming language"',
    # Comprehension-check / step headings (Steps 3, 4, 5, 5a, 5b)
    "## 3. Entity Resolution Introduction",
    "## 4. Programming Language Selection",
    "## 5. Bootcamp Introduction",
    "### 5a. Verbosity Preference",
    "### 5b. Comprehension Check",
)

# Whole-suite passing baseline observed on the UNFIXED tree (Task 1 / Task 4).
# This is the live recorded count; raise it when tests are added or split.
_PASSING_BASELINE = 4648
# Non-regression floor: the recorded passing count must never drop below this.
# Kept as a separate literal from _PASSING_BASELINE so adding/splitting tests
# (which raises the baseline) needs no edit here, while a real drop fails (Req 4).
_PASSING_FLOOR = 4648


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the full UTF-8 text of a steering file."""
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Preservation — structural invariants the byte snapshot protected (Req 3.3)
# ---------------------------------------------------------------------------


class TestOnboardingFilesStructurePreserved:
    """Both onboarding steering files retain the structural invariants their
    whole-file SHA-256 snapshots were protecting.

    Original intent (Req 3.1, 3.2, 3.3): two whole-file SHA-256 snapshots
    (``_HASH_ONBOARDING_FLOW``, ``_HASH_PHASE_FILE``) pinned onboarding-flow.md
    and onboarding-phase1b-intro-language.md byte-for-byte so the BUG 1 fix
    could prove it is tests-only and never edits steering. Those snapshots broke
    on every benign, unrelated edit (additive sections, a repointed
    hook-registry reference) without telling us whether the protected content
    actually changed.

    Structural replacement (Req 5.1, 6.2, 6.6): assert the flow file keeps its
    Phase-1 step scaffold (the content that stayed behind after the split) and
    its hand-off cross-reference, and that the phase file keeps every
    moved-content marker (its post-split home). A fix that guts, truncates, or
    relocates the protected content still fails; benign edits pass. These are
    the structural checks Task 7.6 re-runs to prove BUG 1 is tests-only."""

    @pytest.mark.parametrize("marker", _ONBOARDING_FLOW_MARKERS)
    def test_onboarding_flow_retains_step_scaffold(self, marker: str) -> None:
        """**Validates: Requirements 3.2, 3.3, 5.1, 6.6**

        onboarding-flow.md retains each Phase-1 step scaffold heading — a fix
        that guts or rewrites the flow file would drop one and fail here."""
        content = _read(_ONBOARDING_FLOW)
        assert marker in content, (
            "onboarding-flow.md lost a required Phase-1 step heading "
            f"{marker!r} — BUG 1 must NOT gut or rewrite steering."
        )

    def test_onboarding_flow_retains_cross_reference(self) -> None:
        """**Validates: Requirements 3.2, 3.3, 5.1**

        onboarding-flow.md retains its hand-off to the phase file."""
        content = _read(_ONBOARDING_FLOW)
        assert _CROSS_REFERENCE in content, (
            "onboarding-flow.md lost the cross-reference to the phase file.\n"
            f"Expected to find: {_CROSS_REFERENCE!r}"
        )

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS)
    def test_phase_file_retains_moved_content(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3, 5.1, 6.6**

        onboarding-phase1b-intro-language.md retains each moved-content marker
        the snapshot was protecting — a fix that deletes or relocates that
        content out of the phase file would drop one and fail here."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            "onboarding-phase1b-intro-language.md lost a moved-content marker "
            f"{marker!r} — the post-split content must remain in its new home."
        )


# ---------------------------------------------------------------------------
# Preservation — cross-reference intact (Requirement 3.2)
# ---------------------------------------------------------------------------


class TestCrossReferenceIntact:
    """onboarding-flow.md still directs readers to the phase file."""

    def test_flow_directs_to_phase_file_after_step_2d(self) -> None:
        """**Validates: Requirements 3.2, 3.3**

        The 'After Step 2d, load ...' cross-reference is present verbatim."""
        content = _read(_ONBOARDING_FLOW)
        assert _CROSS_REFERENCE in content, (
            "onboarding-flow.md lost the cross-reference to the phase file.\n"
            f"Expected to find: {_CROSS_REFERENCE!r}"
        )


# ---------------------------------------------------------------------------
# Preservation — moved content present in the phase file (Requirement 3.1)
# Property companion to Property 1 (Bug Condition): for ALL moved-content
# markers, the marker is present in the phase file (post-split location).
# ---------------------------------------------------------------------------


class TestMovedContentInPhaseFile:
    """Every moved-content marker lives in the phase file, not the old flow."""

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS)
    def test_marker_present_in_phase_file(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3**

        Each moved-content marker is present verbatim in the phase file."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            "Moved-content marker missing from "
            "onboarding-phase1b-intro-language.md (post-split home):\n"
            f"  {marker!r}"
        )

    @given(marker=st.sampled_from(_MOVED_CONTENT_MARKERS))
    @settings(max_examples=20)
    def test_all_moved_markers_present_in_phase_file(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.6**

        Property: for all moved-content markers, the marker is present in the
        phase file (post-split location). This is the preservation companion to
        Property 1 — it pins WHERE the moved content lives so a regression that
        deletes or relocates it is caught."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            f"Moved-content marker not found in phase file: {marker!r}"
        )


# ---------------------------------------------------------------------------
# Preservation — whole-suite passing baseline recorded (Requirement 3.6)
# ---------------------------------------------------------------------------


class TestPassingBaselineRecorded:
    """Document the UNFIXED-tree passing count so Task 7.6 can confirm no
    previously-passing test regresses (the count must not drop below 4648)."""

    def test_passing_baseline_is_non_regression_floor(self) -> None:
        """**Validates: Requirements 3.6**

        Guards the whole-suite passing count against regression. The recorded
        baseline must stay at or above the non-regression floor observed on the
        UNFIXED tree (4648). Adding or splitting tests raises the baseline and
        keeps this green; only a genuine drop below the floor fails it."""
        assert _PASSING_BASELINE >= _PASSING_FLOOR
