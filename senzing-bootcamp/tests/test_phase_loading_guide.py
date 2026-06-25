"""Content tests for the phase-loading-guide.md router-role refresh.

These example-based tests assert the loading-guide content invariants
introduced by the module-router-standardization feature (Task 8.1):

- The guide states the **router role** — that the Router_Root provides
  navigation/overview content while substantive workflow steps reside in
  the Phase_Files (Requirement 5.2).
- The guide references the **new dedicated router/phase names** for the
  modules converted from the root-doubles-as-phase pattern: Modules 1, 7,
  and 11 (Requirement 5.3).

The tests are stdlib-only (``pathlib``) and example-based — there is a
single fixed input file (``phase-loading-guide.md``), so property-based
testing would add noise without coverage. Pytest discovers the class via
standard collection.

Feature: module-router-standardization
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------

#: The steering directory that holds the loading guide under test.
_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"

#: The phase-loading guide whose router-role wording is under test.
_GUIDE_FILE: Path = _STEERING_DIR / "phase-loading-guide.md"

#: New dedicated router-root + phase file names for the converted modules.
#: At minimum the phase-1 file of each converted module must be referenced
#: (Requirement 5.3).
_REQUIRED_PHASE_FILES: list[str] = [
    "module-01-phase1-discovery.md",
    "module-07-phase1-query-visualize.md",
    "module-11-phase1-packaging.md",
]

#: The dedicated router-root file names for the converted modules.
_ROUTER_ROOT_FILES: list[str] = [
    "module-01-business-problem.md",
    "module-07-query-visualize-discover.md",
    "module-11-deployment.md",
]


class TestPhaseLoadingGuideContent:
    """Loading-guide content invariants for the router standardization.

    Each test method asserts a grep-level invariant against the real
    ``phase-loading-guide.md`` so future edits cannot silently strip the
    router-role statement or the converted-module references.
    """

    def test_guide_file_exists(self) -> None:
        """The phase-loading guide exists on disk at the expected path."""
        assert _GUIDE_FILE.is_file(), (
            f"Expected phase-loading guide at {_GUIDE_FILE}; not found."
        )

    def test_states_router_role(self) -> None:
        """Validates: Requirement 5.2.

        The guide must state the Router_Root role: that the root provides
        navigation/overview content and that substantive workflow steps
        reside in the phase files. The match is keyword-based and
        case-insensitive so wording improvements do not break the test
        while still catching a dropped statement.
        """
        text = _GUIDE_FILE.read_text(encoding="utf-8")
        lowered = text.lower()

        # (a) The root provides navigation / overview content.
        assert "router" in lowered, (
            "Expected the guide to describe the root as a 'router' "
            f"(Req 5.2) in {_GUIDE_FILE.name}; term not found."
        )
        assert "navigation" in lowered and "overview" in lowered, (
            "Expected the guide to state the root provides navigation and "
            f"overview content (Req 5.2) in {_GUIDE_FILE.name}."
        )

        # (b) Substantive workflow steps reside in the phase files.
        assert "phase" in lowered, (
            "Expected the guide to reference phase files (Req 5.2) in "
            f"{_GUIDE_FILE.name}; 'phase' not found."
        )
        steps_in_phases = (
            ("steps" in lowered or "workflow" in lowered)
            and (
                "reside in the phase" in lowered
                or "reside in phase" in lowered
                or "live in the phase" in lowered
                or "live in phase" in lowered
                or "in the phase sub-file" in lowered
                or "in the phase file" in lowered
            )
        )
        assert steps_in_phases, (
            "Expected the guide to state that substantive workflow steps "
            "reside in the phase files / sub-files rather than the router "
            f"root (Req 5.2) in {_GUIDE_FILE.name}."
        )

    def test_references_new_phase_file_names(self) -> None:
        """Validates: Requirement 5.3.

        The guide must reference the new dedicated phase file names for the
        modules converted from the root-doubles-as-phase pattern — at
        minimum the phase-1 file of Modules 1, 7, and 11.
        """
        text = _GUIDE_FILE.read_text(encoding="utf-8")

        missing = [name for name in _REQUIRED_PHASE_FILES if name not in text]
        assert missing == [], (
            "Expected the guide to reference the new Module 1/7/11 phase "
            f"file names (Req 5.3) in {_GUIDE_FILE.name}; missing: {missing}."
        )

    def test_references_dedicated_router_roots(self) -> None:
        """Validates: Requirement 5.3.

        The guide must describe phase resolution for the converted modules
        using their new dedicated Router_Root names (Modules 1, 7, 11).
        """
        text = _GUIDE_FILE.read_text(encoding="utf-8")

        missing = [name for name in _ROUTER_ROOT_FILES if name not in text]
        assert missing == [], (
            "Expected the guide to reference the dedicated Router_Root file "
            f"names for Modules 1/7/11 (Req 5.3) in {_GUIDE_FILE.name}; "
            f"missing: {missing}."
        )
