"""Content-validation tests for the Deferred First-Visualization Guarantee wiring.

Task 6.2 of the ``module3-first-visualization-guarantee`` spec. These example-based
(pytest, non-Hypothesis) tests guard the markdown wiring that task 6.1 added to the
``### Deferred First-Visualization Guarantee`` subsection of
``steering/visualization-guide.md`` (and the matching deferred-clear notes in the
Module 6 and Module 7 steering files).

They assert that the deferred guarantee reuses the *existing* offer machinery rather
than introducing a parallel one:

1. It references the existing Module 6 (results dashboard) and Module 7
   (``m7_exploratory_queries``) visualization checkpoints.
2. It reuses the existing ``config/visualization_tracker.json`` offer flow (literal
   reference present).
3. It explicitly states NO new parallel offer template / tracker / checkpoint map is
   introduced.
4. It calls ``clear_first_visualization_owed`` for both ``module_6_deferred`` and
   ``module_7_deferred`` satisfaction sources.

The assertions are tolerant of benign wording changes — each required concept is
satisfied by any one of several accepted phrasings — but specific enough to fail if a
whole wiring concept (a checkpoint, the tracker reuse, the no-new-template statement, or
a deferred-clear call) were removed.

**Validates: Requirements 2.2, 3.2**
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# This file lives in senzing-bootcamp/tests/; steering lives in senzing-bootcamp/steering/.
_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_VISUALIZATION_GUIDE = _STEERING_DIR / "visualization-guide.md"
_MODULE_06_PHASE_D = _STEERING_DIR / "module-06-phaseD-validation.md"
_MODULE_07_PHASE1 = _STEERING_DIR / "module-07-phase1-query-visualize.md"

_DEFERRED_HEADING = "### Deferred First-Visualization Guarantee"


def _read(path: Path) -> str:
    """Return a file's UTF-8 text.

    Args:
        path: File to read.

    Returns:
        The file's contents.
    """
    return path.read_text(encoding="utf-8")


def _extract_subsection(text: str, heading: str) -> str:
    """Return the body of a markdown subsection by its heading line.

    The returned slice starts at the heading line and ends just before the next
    heading of the same or a higher level (``###`` or ``##`` or ``#``), or the end
    of the document.

    Args:
        text: Full markdown document text.
        heading: The subsection heading to isolate (e.g. the deferred heading).

    Returns:
        The subsection text including its heading line.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    assert start is not None, f"Subsection heading not found: {heading!r}"

    # Number of leading '#' on the heading defines its level; a following heading at
    # the same or a higher level (fewer or equal '#') ends the subsection.
    heading_level = len(heading) - len(heading.lstrip("#"))

    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            if level <= heading_level:
                end = index
                break
    return "\n".join(lines[start:end])


def _assert_groups_present(
    text_lower: str, groups: tuple[tuple[str, ...], ...], label: str
) -> None:
    """Assert at least one phrasing from every phrase group is present.

    Args:
        text_lower: Lower-cased section text to search.
        groups: Tuple of phrase groups; each group is a tuple of accepted
            (already lower-cased) alternative phrasings.
        label: Human-readable label for failure messages.
    """
    for group in groups:
        assert any(phrase in text_lower for phrase in group), (
            f"{label}: missing required concept.\n"
            f"Expected at least one of these phrasings: {list(group)}"
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def deferred_section() -> str:
    """The full ``### Deferred First-Visualization Guarantee`` subsection (raw case)."""
    return _extract_subsection(_read(_VISUALIZATION_GUIDE), _DEFERRED_HEADING)


@pytest.fixture(scope="module")
def deferred_section_lower(deferred_section: str) -> str:
    """The lower-cased deferred-guarantee subsection text."""
    return deferred_section.lower()


# ---------------------------------------------------------------------------
# TestDeferredSectionPresent
# ---------------------------------------------------------------------------


class TestDeferredSectionPresent:
    """The guide file and deferred-guarantee subsection exist and are non-empty.

    A renamed file or removed subsection would silently skip the wiring checks, so
    both are pinned here first.

    **Validates: Requirements 2.2, 3.2**
    """

    def test_visualization_guide_present(self) -> None:
        """The visualization guide steering file exists and is non-empty."""
        assert _VISUALIZATION_GUIDE.is_file(), f"Missing steering file: {_VISUALIZATION_GUIDE}"
        assert _read(_VISUALIZATION_GUIDE).strip(), f"Steering file is empty: {_VISUALIZATION_GUIDE}"

    def test_deferred_section_present(self, deferred_section: str) -> None:
        """The deferred-guarantee subsection is present and non-empty."""
        assert deferred_section.strip(), "Deferred-guarantee subsection is empty."
        assert deferred_section.splitlines()[0].strip() == _DEFERRED_HEADING


# ---------------------------------------------------------------------------
# TestReusesExistingCheckpoints
# ---------------------------------------------------------------------------


class TestReusesExistingCheckpoints:
    """The deferred wiring references the existing Module 6/7 checkpoints.

    Requirement 3.2: the Deferred Guarantee reuses the existing Visualization Offer
    Protocol checkpoints for Modules 6 and 7 rather than adding a parallel offer
    mechanism.

    **Validates: Requirements 2.2, 3.2**
    """

    def test_references_module_6_results_dashboard(self, deferred_section_lower: str) -> None:
        """References the Module 6 results-dashboard checkpoint."""
        _assert_groups_present(
            deferred_section_lower,
            (
                ("module 6",),
                ("results dashboard", "results-dashboard"),
            ),
            "deferred guarantee (Module 6 results dashboard)",
        )

    def test_references_module_7_exploratory_queries(self, deferred_section_lower: str) -> None:
        """References the Module 7 ``m7_exploratory_queries`` checkpoint."""
        _assert_groups_present(
            deferred_section_lower,
            (
                ("module 7",),
                ("m7_exploratory_queries",),
            ),
            "deferred guarantee (Module 7 m7_exploratory_queries)",
        )


# ---------------------------------------------------------------------------
# TestReusesExistingTracker
# ---------------------------------------------------------------------------


class TestReusesExistingTracker:
    """The deferred wiring reuses the existing visualization tracker.

    Requirement 3.2: the deferred path reuses the existing
    ``config/visualization_tracker.json`` offer flow rather than adding a parallel
    tracker.

    **Validates: Requirements 3.2**
    """

    def test_references_visualization_tracker_json(self, deferred_section: str) -> None:
        """References the literal ``visualization_tracker.json`` tracker file."""
        # Case-sensitive: the tracker filename is a literal path token.
        assert "visualization_tracker.json" in deferred_section, (
            "deferred guarantee: missing literal reference to "
            "config/visualization_tracker.json (the reused tracker flow)."
        )


# ---------------------------------------------------------------------------
# TestNoParallelOfferMechanism
# ---------------------------------------------------------------------------


class TestNoParallelOfferMechanism:
    """The deferred wiring explicitly introduces no new parallel offer mechanism.

    Requirement 3.2: the deferred guarantee must reuse the existing offer machinery
    without adding a parallel offer template, tracker, or checkpoint map.

    **Validates: Requirements 3.2**
    """

    def test_states_no_new_offer_template(self, deferred_section_lower: str) -> None:
        """States that no new offer template / tracker / checkpoint map is added."""
        _assert_groups_present(
            deferred_section_lower,
            (
                (
                    "no new offer template",
                    "no new offer template, tracker, or checkpoint map",
                    "without a new offer template",
                ),
            ),
            "deferred guarantee (no new offer template statement)",
        )

    def test_states_reuses_existing_flow(self, deferred_section_lower: str) -> None:
        """States that it reuses the existing offer flow."""
        _assert_groups_present(
            deferred_section_lower,
            (
                (
                    "reuses the existing offer flow",
                    "existing offer flow",
                    "existing offer",
                ),
            ),
            "deferred guarantee (reuses existing offer flow statement)",
        )


# ---------------------------------------------------------------------------
# TestDeferredClearCalls
# ---------------------------------------------------------------------------


class TestDeferredClearCalls:
    """The deferred wiring clears the owed marker for both deferred sources.

    Requirement 2.2: when a visualization is generated at the Module 6 or Module 7
    checkpoint while a first visualization is owed, the owed marker is cleared via
    ``clear_first_visualization_owed`` with the corresponding ``satisfied_by`` source.

    **Validates: Requirements 2.2**
    """

    def test_calls_clear_for_module_6_deferred(self, deferred_section: str) -> None:
        """Calls ``clear_first_visualization_owed`` for ``module_6_deferred``."""
        assert 'clear_first_visualization_owed(satisfied_by="module_6_deferred")' in deferred_section, (
            "deferred guarantee: missing "
            'clear_first_visualization_owed(satisfied_by="module_6_deferred") call.'
        )

    def test_calls_clear_for_module_7_deferred(self, deferred_section: str) -> None:
        """Calls ``clear_first_visualization_owed`` for ``module_7_deferred``."""
        assert 'clear_first_visualization_owed(satisfied_by="module_7_deferred")' in deferred_section, (
            "deferred guarantee: missing "
            'clear_first_visualization_owed(satisfied_by="module_7_deferred") call.'
        )

    def test_guards_clear_with_is_first_visualization_owed(
        self, deferred_section_lower: str
    ) -> None:
        """Guards the clear with an ``is_first_visualization_owed`` check."""
        _assert_groups_present(
            deferred_section_lower,
            (("is_first_visualization_owed",),),
            "deferred guarantee (owed-state guard)",
        )


# ---------------------------------------------------------------------------
# TestModule6And7SteeringDeferredNotes
# ---------------------------------------------------------------------------


class TestModule6And7SteeringDeferredNotes:
    """The Module 6/7 steering files carry matching deferred-clear notes.

    This confirms the deferred wiring lives at the existing Module 6/7 checkpoints
    (not a new parallel location), reinforcing Requirements 2.2 and 3.2.

    **Validates: Requirements 2.2, 3.2**
    """

    def test_module_6_steering_has_deferred_clear(self) -> None:
        """Module 6 Phase D steering calls the ``module_6_deferred`` clear."""
        text = _read(_MODULE_06_PHASE_D)
        assert 'clear_first_visualization_owed(satisfied_by="module_6_deferred")' in text, (
            "module-06-phaseD-validation.md: missing module_6_deferred clear call."
        )

    def test_module_7_steering_has_deferred_clear(self) -> None:
        """Module 7 Phase 1 steering calls the ``module_7_deferred`` clear."""
        text = _read(_MODULE_07_PHASE1)
        assert 'clear_first_visualization_owed(satisfied_by="module_7_deferred")' in text, (
            "module-07-phase1-query-visualize.md: missing module_7_deferred clear call."
        )

    def test_module_7_steering_references_checkpoint(self) -> None:
        """Module 7 steering references the ``m7_exploratory_queries`` checkpoint."""
        text = _read(_MODULE_07_PHASE1)
        assert "m7_exploratory_queries" in text, (
            "module-07-phase1-query-visualize.md: missing m7_exploratory_queries checkpoint reference."
        )
