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

import hashlib
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

# SHA-256 byte-level baselines observed on the UNFIXED tree (Task 4).
# Source of truth mirrored in
# .kiro/specs/bootcamp-consistency-fixes/bug1_preservation_baselines.txt
_HASH_ONBOARDING_FLOW = (
    "fd03ebcc58464f6022e6a2990dad0318ed29a09bb9d672cb6fc3decb7de2a8c9"
)
_HASH_PHASE_FILE = (
    "4631a4eaccdfadaf12d8a8c6f2d53eafbf5d372744da95abebff8d36e739f86e"
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
_PASSING_BASELINE = 4648


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the full UTF-8 text of a steering file."""
    return path.read_text(encoding="utf-8")


def _sha256_bytes(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Preservation — byte-level baselines (Requirement 3.3)
# ---------------------------------------------------------------------------


class TestOnboardingFilesByteIdentical:
    """Both onboarding steering files match their observed SHA-256 baselines.

    These are the digests Task 7.6 re-checks to prove BUG 1 is tests-only."""

    def test_onboarding_flow_matches_sha256_baseline(self) -> None:
        """**Validates: Requirements 3.2, 3.3**

        onboarding-flow.md is byte-identical to the Task 4 baseline."""
        actual = _sha256_bytes(_ONBOARDING_FLOW)
        assert actual == _HASH_ONBOARDING_FLOW, (
            "onboarding-flow.md content changed — BUG 1 must NOT edit steering.\n"
            f"Expected: {_HASH_ONBOARDING_FLOW}\n"
            f"Actual:   {actual}"
        )

    def test_phase_file_matches_sha256_baseline(self) -> None:
        """**Validates: Requirements 3.1, 3.3**

        onboarding-phase1b-intro-language.md is byte-identical to the baseline."""
        actual = _sha256_bytes(_PHASE_FILE)
        assert actual == _HASH_PHASE_FILE, (
            "onboarding-phase1b-intro-language.md content changed — BUG 1 must "
            "NOT edit steering.\n"
            f"Expected: {_HASH_PHASE_FILE}\n"
            f"Actual:   {actual}"
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

    def test_passing_baseline_constant(self) -> None:
        """**Validates: Requirements 3.6**

        The recorded passing baseline is the observed UNFIXED-tree count (4648)."""
        assert _PASSING_BASELINE == 4648
