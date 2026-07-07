"""Content-validation tests for the Module 3 Opt-Out Gate standalone-demo offer.

Task 4.2 of the ``module3-first-visualization-guarantee`` spec. These example-based
(pytest, non-Hypothesis) tests guard the markdown framing that task 4.1 added to the
``## Opt-Out Gate`` section of ``steering/module-03-phase1-verification.md``.

They assert two things about that section:

1. The Standalone Demo Visualization is framed as an *offer*, not a forced step
   (offer / optional / not-a-forced-step language is present).
2. The section references the Step 9 web-service constraints the standalone demo
   reuses: a Python stdlib HTTP server (``http.server``), D3.js v7 from the CDN, a
   single self-contained HTML file, and artifacts created inside the working
   directory.

The assertions are tolerant of benign wording changes — each required concept is
satisfied by any one of several accepted phrasings — but specific enough to fail if
a whole framing concept (the offer framing or a Step 9 constraint) were removed.

**Validates: Requirements 2.1, 3.1**
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
_MODULE_03_PHASE1 = _STEERING_DIR / "module-03-phase1-verification.md"


def _read(path: Path) -> str:
    """Return a file's UTF-8 text.

    Args:
        path: File to read.

    Returns:
        The file's contents.
    """
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, heading: str) -> str:
    """Return the body of a ``## `` markdown section by its heading.

    The returned slice starts at the heading line and ends just before the next
    top-level (``## ``) heading, or the end of the document.

    Args:
        text: Full markdown document text.
        heading: The section heading to isolate (e.g. ``"## Opt-Out Gate"``).

    Returns:
        The section text including its heading line.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    assert start is not None, f"Section heading not found: {heading!r}"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
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
def opt_out_section() -> str:
    """The full ``## Opt-Out Gate`` section text (raw case preserved)."""
    return _extract_section(_read(_MODULE_03_PHASE1), "## Opt-Out Gate")


@pytest.fixture(scope="module")
def opt_out_section_lower(opt_out_section: str) -> str:
    """The lower-cased ``## Opt-Out Gate`` section text."""
    return opt_out_section.lower()


# ---------------------------------------------------------------------------
# TestOptOutGateSectionPresent
# ---------------------------------------------------------------------------


class TestOptOutGateSectionPresent:
    """The steering file and Opt-Out Gate section exist and are non-empty.

    A renamed file or removed section would silently skip the framing checks, so
    both are pinned here first.

    **Validates: Requirements 2.1, 3.1**
    """

    def test_steering_file_present(self) -> None:
        """The Module 3 Phase 1 steering file exists and is non-empty."""
        assert _MODULE_03_PHASE1.is_file(), f"Missing steering file: {_MODULE_03_PHASE1}"
        assert _read(_MODULE_03_PHASE1).strip(), f"Steering file is empty: {_MODULE_03_PHASE1}"

    def test_opt_out_section_present(self, opt_out_section: str) -> None:
        """The ``## Opt-Out Gate`` section is present and non-empty."""
        assert opt_out_section.strip(), "Opt-Out Gate section is empty."
        assert opt_out_section.splitlines()[0].strip() == "## Opt-Out Gate"


# ---------------------------------------------------------------------------
# TestStandaloneDemoOfferFraming
# ---------------------------------------------------------------------------


class TestStandaloneDemoOfferFraming:
    """The standalone demo is framed as an offer, not a forced step.

    Requirement 2.1: the Standalone Demo Visualization is presented as an offer,
    not a forced step. The section must name the standalone demo, use offer
    language, and make clear it is optional / not forced.

    **Validates: Requirements 2.1**
    """

    def test_names_the_standalone_demo(self, opt_out_section_lower: str) -> None:
        """The section names the Standalone Demo Visualization."""
        _assert_groups_present(
            opt_out_section_lower,
            (("standalone demo visualization", "standalone demo"),),
            "opt-out gate (standalone demo name)",
        )

    def test_frames_as_offer(self, opt_out_section_lower: str) -> None:
        """The standalone demo is framed with offer language."""
        _assert_groups_present(
            opt_out_section_lower,
            (("offer",),),
            "opt-out gate (offer framing)",
        )

    def test_marks_as_optional_not_forced(self, opt_out_section_lower: str) -> None:
        """The section makes clear the demo is optional / not a forced step."""
        _assert_groups_present(
            opt_out_section_lower,
            (
                (
                    "not a forced step",
                    "not forced",
                    "optional",
                    "it's optional",
                ),
            ),
            "opt-out gate (optional / not-forced framing)",
        )


# ---------------------------------------------------------------------------
# TestStep9WebServiceConstraints
# ---------------------------------------------------------------------------


class TestStep9WebServiceConstraints:
    """The section references the Step 9 web-service constraints it reuses.

    Requirement 3.1: the Standalone Demo Visualization reuses the Module 3 Step 9
    constraints — Python stdlib HTTP server, D3.js v7 CDN, a single self-contained
    HTML file, and artifacts created inside the working directory.

    **Validates: Requirements 3.1**
    """

    def test_references_stdlib_http_server(self, opt_out_section_lower: str) -> None:
        """References the Python stdlib HTTP server."""
        _assert_groups_present(
            opt_out_section_lower,
            (
                ("http.server",),
                ("stdlib http server", "python stdlib http server", "stdlib"),
            ),
            "opt-out gate (stdlib HTTP server)",
        )

    def test_references_d3js_v7_cdn(self, opt_out_section_lower: str) -> None:
        """References D3.js v7 loaded from the CDN."""
        _assert_groups_present(
            opt_out_section_lower,
            (
                ("d3.js v7", "d3 v7"),
                ("cdn",),
            ),
            "opt-out gate (D3.js v7 CDN)",
        )

    def test_references_single_self_contained_html(self, opt_out_section_lower: str) -> None:
        """References a single self-contained HTML file."""
        _assert_groups_present(
            opt_out_section_lower,
            (("single self-contained html file", "self-contained html file"),),
            "opt-out gate (single self-contained HTML file)",
        )

    def test_references_working_directory_artifacts(self, opt_out_section_lower: str) -> None:
        """References artifacts created inside the working directory."""
        _assert_groups_present(
            opt_out_section_lower,
            (("inside the working directory", "working directory"),),
            "opt-out gate (working-directory artifacts)",
        )
