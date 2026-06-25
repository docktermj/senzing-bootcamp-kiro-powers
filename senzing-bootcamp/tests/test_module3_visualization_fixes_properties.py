"""Property-based tests for Module 3 visualization fixes.

Validates structural and content properties of the steering file edits
for enforcement block, viewport height, guided tour content, and guided
tour structural ordering.

Feature: module3-visualization-fixes
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_FILE: Path = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "module-03-phase2-visualization.md"
)

# ---------------------------------------------------------------------------
# Module-level parsing
# ---------------------------------------------------------------------------

_STEERING_CONTENT: str = _STEERING_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Enforcement block extraction
# ---------------------------------------------------------------------------


def _extract_enforcement_block(content: str) -> str:
    """Extract the enforcement block between CRITICAL LESSONS and Step 9.

    The enforcement block is the section that appears after the
    "CRITICAL LESSONS" heading and before the "## Step 9" heading.

    Args:
        content: Full text of the steering file.

    Returns:
        The enforcement block text, or empty string if not found.
    """
    # Find the end of the CRITICAL LESSONS section
    critical_match = re.search(
        r"^## CRITICAL LESSONS.*$", content, re.MULTILINE
    )
    # Find the start of Step 9
    step9_match = re.search(
        r"^## Step 9", content, re.MULTILINE
    )

    if critical_match is None or step9_match is None:
        return ""

    block_start = critical_match.end()
    block_end = step9_match.start()

    return content[block_start:block_end]


_ENFORCEMENT_BLOCK: str = _extract_enforcement_block(_STEERING_CONTENT)

# Split the enforcement block into lines for sampling
_ENFORCEMENT_LINES: list[str] = [
    line for line in _ENFORCEMENT_BLOCK.splitlines() if line.strip()
]


def st_enforcement_line_index() -> st.SearchStrategy[int]:
    """Strategy that draws a valid index into the enforcement block lines.

    Returns:
        A strategy producing integer indices for enforcement block lines.
    """
    return st.sampled_from(list(range(len(_ENFORCEMENT_LINES))))


# ---------------------------------------------------------------------------
# Section 9.4 extraction
# ---------------------------------------------------------------------------


def _extract_section_94(content: str) -> str:
    """Extract section 9.4 content from the steering file.

    Args:
        content: Full text of the steering file.

    Returns:
        Text of section 9.4 from its heading to the next ## heading or EOF.
    """
    lines = content.splitlines()
    in_section = False
    section_lines: list[str] = []

    for line in lines:
        if "### 9.4" in line:
            in_section = True
            section_lines.append(line)
        elif in_section:
            # End at next ## heading (but not ###)
            if re.match(r"^##\s+[^#]", line):
                break
            section_lines.append(line)

    return "\n".join(section_lines)


def _find_url_presentation_line(content: str) -> int | None:
    """Find the line index containing URL presentation text.

    Looks for lines containing 'localhost' or 'running' that represent
    the URL presentation to the bootcamper.

    Args:
        content: Section text to search.

    Returns:
        Line index of the URL presentation, or None if not found.
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if ("localhost" in line.lower() or "running" in line.lower()) and (
            "http" in line.lower() or "visualization" in line.lower()
        ):
            return i
    return None


def _find_guided_tour_line(content: str) -> int | None:
    """Find the line index where the guided tour begins.

    Looks for the 🗺️ emoji marker that starts the guided tour.

    Args:
        content: Section text to search.

    Returns:
        Line index of the guided tour start, or None if not found.
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "🗺️" in line:
            return i
    return None


def _find_stop_block_line(content: str) -> int | None:
    """Find the line index of the STOP block.

    Looks for the '🛑 STOP' marker.

    Args:
        content: Section text to search.

    Returns:
        Line index of the STOP block, or None if not found.
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "🛑" in line and "STOP" in line:
            return i
    return None


# Extract section 9.4 for structural ordering tests
_SECTION_94: str = _extract_section_94(_STEERING_CONTENT)

# Extract key structural positions
_URL_LINE: int | None = _find_url_presentation_line(_SECTION_94)
_TOUR_LINE: int | None = _find_guided_tour_line(_SECTION_94)
_STOP_LINE: int | None = _find_stop_block_line(_SECTION_94)

# ---------------------------------------------------------------------------
# Guided tour delivery spec extraction
# ---------------------------------------------------------------------------


def _extract_guided_tour_block(content: str) -> str:
    """Extract the guided tour block from section 9.4.

    The guided tour block starts at the 'Guided Tour' instruction heading
    and extends to the STOP block.

    Args:
        content: Section 9.4 text.

    Returns:
        Text of the guided tour block.
    """
    lines = content.splitlines()
    tour_start: int | None = None
    stop_line: int | None = None

    for i, line in enumerate(lines):
        if tour_start is None and (
            "guided tour" in line.lower() or "🗺️" in line
        ):
            tour_start = i
        if "🛑" in line and "STOP" in line:
            stop_line = i
            break

    if tour_start is not None and stop_line is not None:
        return "\n".join(lines[tour_start:stop_line])
    if tour_start is not None:
        return "\n".join(lines[tour_start:])
    return ""


_GUIDED_TOUR_BLOCK: str = _extract_guided_tour_block(_SECTION_94)

# Build a list of structural ordering checks for the strategy to sample from
_ORDERING_CHECKS: list[str] = [
    "url_before_tour",
    "tour_before_stop",
    "single_message_delivery",
    "no_interactive_pauses",
]


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_ordering_check() -> st.SearchStrategy[str]:
    """Strategy that draws a structural ordering check to verify.

    Returns:
        A strategy producing check names from the ordering checks list.
    """
    return st.sampled_from(_ORDERING_CHECKS)


# ---------------------------------------------------------------------------
# Property 4: Guided tour structural ordering
# ---------------------------------------------------------------------------


class TestGuidedTourStructuralOrdering:
    """Feature: module3-visualization-fixes, Property 4: Guided tour structural ordering

    For any valid state of the steering file, the guided tour section SHALL
    appear after the URL presentation text (containing "localhost" or
    "running") and before the STOP block (containing "🛑 STOP"), and SHALL
    specify single-message delivery with no interactive pauses.

    **Validates: Requirements 3.6, 3.7**
    """

    @given(check=st_ordering_check())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_guided_tour_structural_ordering(self, check: str) -> None:
        """Verify guided tour ordering and delivery specification.

        Args:
            check: The specific structural ordering check to verify.
        """
        violations: list[str] = []

        if check == "url_before_tour":
            # URL presentation must appear before guided tour
            if _URL_LINE is None:
                violations.append(
                    "URL presentation line not found "
                    "(expected text containing 'localhost' or 'running')"
                )
            elif _TOUR_LINE is None:
                violations.append(
                    "Guided tour line not found (expected 🗺️ marker)"
                )
            elif _URL_LINE >= _TOUR_LINE:
                violations.append(
                    f"URL presentation (line {_URL_LINE}) must appear "
                    f"before guided tour (line {_TOUR_LINE})"
                )

        elif check == "tour_before_stop":
            # Guided tour must appear before STOP block
            if _TOUR_LINE is None:
                violations.append(
                    "Guided tour line not found (expected 🗺️ marker)"
                )
            elif _STOP_LINE is None:
                violations.append(
                    "STOP block not found (expected '🛑 STOP')"
                )
            elif _TOUR_LINE >= _STOP_LINE:
                violations.append(
                    f"Guided tour (line {_TOUR_LINE}) must appear "
                    f"before STOP block (line {_STOP_LINE})"
                )

        elif check == "single_message_delivery":
            # Guided tour must specify single-message delivery
            if "single" not in _GUIDED_TOUR_BLOCK.lower():
                violations.append(
                    "Guided tour block does not specify "
                    "'single' message delivery"
                )
            if (
                "message" not in _GUIDED_TOUR_BLOCK.lower()
                and "chat" not in _GUIDED_TOUR_BLOCK.lower()
            ):
                violations.append(
                    "Guided tour block does not reference "
                    "'message' or 'chat' delivery"
                )

        elif check == "no_interactive_pauses":
            # Guided tour must specify no interactive pauses
            if "no interactive pauses" not in _GUIDED_TOUR_BLOCK.lower():
                violations.append(
                    "Guided tour block does not specify "
                    "'no interactive pauses'"
                )

        assert violations == [], (
            f"Guided tour structural ordering violation [{check}]: "
            f"{violations}"
        )


# ---------------------------------------------------------------------------
# Property 1: Enforcement block completeness
# ---------------------------------------------------------------------------


class TestEnforcementBlockCompleteness:
    """Feature: module3-visualization-fixes, Property 1: Enforcement block completeness

    For any enforcement block extracted from the steering file (the section
    between the CRITICAL LESSONS section and Step 9), it SHALL contain all of
    the following elements: (a) the phrase "DO NOT SKIP" in uppercase,
    (b) the word "MANDATORY" in uppercase, (c) language prohibiting transition
    to Module 4, (d) at least one visual marker (emoji character or bold
    markdown formatting), and (e) language stating Phase 2 is not optional.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    """

    @given(line_idx=st_enforcement_line_index())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_enforcement_block_contains_all_required_elements(
        self, line_idx: int
    ) -> None:
        """The enforcement block contains all required enforcement elements.

        Each sampled line confirms the block as a whole has the required
        elements — this property holds regardless of which line is sampled.

        Args:
            line_idx: Index into the list of non-empty enforcement block lines.
        """
        block = _ENFORCEMENT_BLOCK
        violations: list[str] = []

        # (a) "DO NOT SKIP" in uppercase (Req 1.1)
        if "DO NOT SKIP" not in block:
            violations.append('missing "DO NOT SKIP" in uppercase')

        # (b) "MANDATORY" in uppercase (Req 1.5)
        if "MANDATORY" not in block:
            violations.append('missing "MANDATORY" in uppercase')

        # (c) Language prohibiting transition to Module 4 (Req 1.3)
        has_module4_prohibition = (
            "Module 4" in block or "module 4" in block
        )
        has_transition_language = (
            "DO NOT transition" in block
            or "do not transition" in block.lower()
            or "transition to Module 4" in block
        )
        if not (has_module4_prohibition and has_transition_language):
            violations.append(
                "missing Module 4 transition prohibition language"
            )

        # (d) Visual marker — emoji or bold formatting (Req 1.4)
        has_emoji = bool(re.search(r"[\U0001F600-\U0001F9FF⚠️🚨🛑]", block))
        has_bold = bool(re.search(r"\*\*[^*]+\*\*", block))
        if not (has_emoji or has_bold):
            violations.append(
                "missing visual marker (emoji or bold formatting)"
            )

        # (e) "not optional" language (Req 1.2)
        has_not_optional = (
            "NOT optional" in block
            or "not optional" in block.lower()
        )
        if not has_not_optional:
            violations.append('missing "not optional" language')

        assert violations == [], (
            f"Enforcement block completeness violations "
            f"(sampled line {line_idx}: "
            f"{_ENFORCEMENT_LINES[line_idx]!r}): {violations}"
        )


# ---------------------------------------------------------------------------
# Graph container CSS extraction
# ---------------------------------------------------------------------------


def _extract_graph_container_css_blocks(content: str) -> list[str]:
    """Extract CSS code blocks containing #graph-container from the steering file.

    Finds fenced code blocks (```css ... ```) that reference #graph-container
    and returns their content.

    Args:
        content: Full text of the steering file.

    Returns:
        List of CSS code block strings containing #graph-container.
    """
    blocks: list[str] = []
    in_css_block = False
    current_block_lines: list[str] = []

    for line in content.splitlines():
        if line.strip().startswith("```css"):
            in_css_block = True
            current_block_lines = []
        elif in_css_block and line.strip().startswith("```"):
            block_text = "\n".join(current_block_lines)
            if "#graph-container" in block_text:
                blocks.append(block_text)
            in_css_block = False
            current_block_lines = []
        elif in_css_block:
            current_block_lines.append(line)

    return blocks


_GRAPH_CONTAINER_CSS_BLOCKS: list[str] = _extract_graph_container_css_blocks(
    _STEERING_CONTENT
)


def st_graph_container_css_block() -> st.SearchStrategy[str]:
    """Strategy that draws a CSS block containing #graph-container.

    Returns:
        A strategy producing CSS block text strings.
    """
    return st.sampled_from(_GRAPH_CONTAINER_CSS_BLOCKS)


# ---------------------------------------------------------------------------
# Property 2: Graph container uses viewport-relative height
# ---------------------------------------------------------------------------


class TestGraphContainerViewportRelativeHeight:
    """Feature: module3-visualization-fixes, Property 2: Graph container uses \
viewport-relative height

    For any CSS height specification associated with the graph container in
    the steering file, the value SHALL be a viewport-relative expression
    (containing `vh`) and SHALL NOT be a fixed pixel value matching the
    pattern `\\d+px`.

    **Validates: Requirements 2.1, 2.3**
    """

    @given(css_block=st_graph_container_css_block())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_graph_container_height_is_viewport_relative(
        self, css_block: str
    ) -> None:
        """Each #graph-container CSS block uses viewport-relative height, not fixed pixels.

        Args:
            css_block: CSS code block text containing #graph-container.
        """
        violations: list[str] = []

        # Extract height value from the CSS block
        height_match = re.search(r"height:\s*(.+?);", css_block)
        if not height_match:
            # Try without semicolon (end of block)
            height_match = re.search(r"height:\s*(.+?)$", css_block, re.MULTILINE)

        if not height_match:
            violations.append(
                "no height property found in #graph-container CSS block"
            )
        else:
            height_value = height_match.group(1).strip()

            # Must contain 'vh' (viewport-relative)
            if "vh" not in height_value:
                violations.append(
                    f"height value '{height_value}' does not contain 'vh' "
                    f"(not viewport-relative)"
                )

            # Must NOT be a fixed pixel value (e.g., 600px)
            if re.match(r"^\d+px$", height_value):
                violations.append(
                    f"height value '{height_value}' is a fixed pixel value"
                )

        assert violations == [], (
            f"Graph container CSS violations: {violations}"
        )
