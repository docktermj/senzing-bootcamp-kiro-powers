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
_PHASE2_FILE = _STEERING_DIR / "onboarding-phase2-track-setup.md"

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

# Moved-content markers, grouped by the file that owns them AFTER the preface
# reorder (Requirement 3.1). The onboarding split first moved this content out
# of onboarding-flow.md into the phase files; the preface reorder (track before
# language) then relocated programming language selection and the comprehension
# check from phase 1b into phase 2 (track-setup), and renumbered phase 1b so the
# welcome banner is Step 4 and verbosity is Step 4a.

# Markers that remain VERBATIM in phase 1b: the entity-resolution intro handoff,
# the welcome banner / Bootcamp Introduction (Step 4), and the verbosity /
# Detail_Level step (Step 4a).
_MOVED_CONTENT_MARKERS_PHASE1B: tuple[str, ...] = (
    # Welcome banner (Step 4 — Bootcamp Introduction)
    "🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓",
    # Step headings that stayed in phase 1b (Steps 3, 4, 4a)
    "## 3. Entity Resolution Introduction",
    "## 4. Bootcamp Introduction",
    "### 4a. Verbosity Preference",
)

# Markers that the preface reorder moved into phase 2 (track-setup): programming
# language selection (Step 5a, after Track Selection) and the comprehension
# check (Step 5b, after Language_Selection).
_MOVED_CONTENT_MARKERS_PHASE2: tuple[str, ...] = (
    # Programming language prompt — the disambiguation phrasing (Step 5a)
    'always use the phrase "programming language"',
    "## 5a. Programming Language Selection",
    "### 5b. Comprehension Check",
)

# Combined set (both post-reorder homes) for property-style sampling.
_MOVED_CONTENT_MARKERS: tuple[str, ...] = (
    _MOVED_CONTENT_MARKERS_PHASE1B + _MOVED_CONTENT_MARKERS_PHASE2
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

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS_PHASE1B)
    def test_phase1b_retains_moved_content(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3, 5.1, 6.6**

        onboarding-phase1b-intro-language.md retains each moved-content marker
        that stays in phase 1b after the preface reorder (ER intro, welcome
        banner, verbosity) — a fix that deletes or relocates that content out of
        the phase file would drop one and fail here."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            "onboarding-phase1b-intro-language.md lost a moved-content marker "
            f"{marker!r} — the post-reorder content must remain in its new home."
        )

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS_PHASE2)
    def test_phase2_retains_moved_content(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3, 5.1, 6.6**

        onboarding-phase2-track-setup.md retains each marker the preface reorder
        moved into phase 2 — programming language selection and the comprehension
        check now follow track selection here, not in phase 1b. A regression that
        deletes or relocates that content would drop one and fail here."""
        content = _read(_PHASE2_FILE)
        assert marker in content, (
            "onboarding-phase2-track-setup.md lost a moved-content marker "
            f"{marker!r} — the reorder moved this into phase 2 (track-setup)."
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
    """Every moved-content marker lives in its post-reorder home phase file,
    not the old flow.

    The preface reorder split the moved content across two homes: ER intro,
    welcome banner, and verbosity stay in phase 1b, while programming language
    selection and the comprehension check moved into phase 2 (track-setup)."""

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS_PHASE1B)
    def test_phase1b_marker_present(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3**

        Each phase-1b marker is present verbatim in the phase 1b file."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            "Moved-content marker missing from "
            "onboarding-phase1b-intro-language.md (post-reorder home):\n"
            f"  {marker!r}"
        )

    @pytest.mark.parametrize("marker", _MOVED_CONTENT_MARKERS_PHASE2)
    def test_phase2_marker_present(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.3**

        Each phase-2 marker (moved by the reorder) is present verbatim in the
        track-setup file."""
        content = _read(_PHASE2_FILE)
        assert marker in content, (
            "Moved-content marker missing from "
            "onboarding-phase2-track-setup.md (post-reorder home):\n"
            f"  {marker!r}"
        )

    @given(marker=st.sampled_from(_MOVED_CONTENT_MARKERS_PHASE1B))
    @settings(max_examples=20)
    def test_all_phase1b_markers_present(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.6**

        Property: for all phase-1b moved-content markers, the marker is present
        in the phase 1b file. This is the preservation companion to Property 1 —
        it pins WHERE the moved content lives so a regression that deletes or
        relocates it is caught."""
        content = _read(_PHASE_FILE)
        assert marker in content, (
            f"Moved-content marker not found in phase 1b file: {marker!r}"
        )

    @given(marker=st.sampled_from(_MOVED_CONTENT_MARKERS_PHASE2))
    @settings(max_examples=20)
    def test_all_phase2_markers_present(self, marker: str) -> None:
        """**Validates: Requirements 3.1, 3.6**

        Property: for all phase-2 moved-content markers (relocated by the preface
        reorder), the marker is present in the track-setup file — pinning that
        programming language selection and the comprehension check now live in
        phase 2, after track selection."""
        content = _read(_PHASE2_FILE)
        assert marker in content, (
            f"Moved-content marker not found in phase 2 file: {marker!r}"
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
