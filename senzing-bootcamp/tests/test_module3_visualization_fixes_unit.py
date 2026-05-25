"""Unit tests for Module 3 visualization fixes steering file content.

Validates that the steering file contains the correct viewport height
specification, offset documentation, guided tour placement, and no fixed
pixel height for the graph container.

Feature: module3-visualization-fixes
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_STEERING_FILE: Path = _BASE_DIR / "steering" / "module-03-phase2-visualization.md"

# ---------------------------------------------------------------------------
# Module-level file content (read once at import time)
# ---------------------------------------------------------------------------

_CONTENT: str = _STEERING_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestModule3VisualizationFixesUnit:
    """Unit tests for viewport height and guided tour placement.

    Validates Requirements 2.1, 2.2, 2.3, 3.1.
    """

    def test_calc_viewport_height_present(self) -> None:
        """Assert the exact string `calc(100vh - 120px)` appears in the file.

        Validates: Requirements 2.1
        """
        assert "calc(100vh - 120px)" in _CONTENT, (
            "Steering file must contain the exact CSS expression "
            "'calc(100vh - 120px)' for the graph container height"
        )

    def test_offset_breakdown_documented(self) -> None:
        """Assert the file mentions header (~50px), banner (~40px), and tab navigation (~30px).

        The 120px offset breakdown should be documented near the height
        specification to explain why 120px was chosen.

        Validates: Requirements 2.2
        """
        # Extract the section around the calc(100vh - 120px) specification
        # Look for the offset breakdown within a reasonable window
        calc_pos = _CONTENT.find("calc(100vh - 120px)")
        assert calc_pos != -1, "calc(100vh - 120px) must be present"

        # Check within 500 characters after the calc expression
        context_window = _CONTENT[calc_pos:calc_pos + 500]

        assert "50px" in context_window, (
            "The 120px offset breakdown should mention the header (~50px) "
            "near the height specification"
        )
        assert "40px" in context_window, (
            "The 120px offset breakdown should mention the banner (~40px) "
            "near the height specification"
        )
        assert "30px" in context_window, (
            "The 120px offset breakdown should mention the tab navigation (~30px) "
            "near the height specification"
        )

        # Verify the terms header, banner, and tab navigation are mentioned
        assert re.search(r"header", context_window, re.IGNORECASE), (
            "The offset breakdown should mention 'header'"
        )
        assert re.search(r"banner", context_window, re.IGNORECASE), (
            "The offset breakdown should mention 'banner'"
        )
        assert re.search(r"tab", context_window, re.IGNORECASE), (
            "The offset breakdown should mention 'tab' (navigation)"
        )

    def test_guided_tour_after_verification(self) -> None:
        """Assert the guided tour (🗺️) appears after the URL/verification text and before STOP.

        The guided tour must be positioned after the URL presentation
        (containing 'localhost' or 'running') and before the STOP block.

        Validates: Requirements 3.1
        """
        # Find the URL presentation text
        url_match = re.search(
            r"(localhost|Your visualization is running)", _CONTENT
        )
        assert url_match is not None, (
            "Steering file must contain URL presentation text "
            "(localhost or 'Your visualization is running')"
        )
        url_pos = url_match.start()

        # Find the guided tour marker
        tour_pos = _CONTENT.find("🗺️")
        assert tour_pos != -1, (
            "Steering file must contain the guided tour marker '🗺️'"
        )

        # Find the STOP block
        stop_pos = _CONTENT.find("🛑 STOP")
        assert stop_pos != -1, (
            "Steering file must contain the '🛑 STOP' block"
        )

        # Verify ordering: URL presentation < guided tour < STOP block
        assert url_pos < tour_pos, (
            f"Guided tour (pos {tour_pos}) must appear after URL presentation "
            f"(pos {url_pos})"
        )
        assert tour_pos < stop_pos, (
            f"Guided tour (pos {tour_pos}) must appear before STOP block "
            f"(pos {stop_pos})"
        )

    def test_no_fixed_600px_for_graph_container(self) -> None:
        """Assert that `600px` does NOT appear as a CSS height value for graph container.

        The graph container section should use viewport-relative height,
        not a fixed 600px value. The string '600px' may appear in a
        prohibition statement (e.g., "Do NOT use ... 600px") but must
        NOT appear as an actual CSS property value like `height: 600px`.

        Validates: Requirements 2.3
        """
        # Find the #graph-container CSS block — look for the actual CSS rule
        # The steering file contains a CSS code block for #graph-container
        css_block_match = re.search(
            r"#graph-container\s*\{([^}]+)\}",
            _CONTENT,
        )
        assert css_block_match is not None, (
            "Steering file must contain a '#graph-container { ... }' CSS block"
        )

        css_body = css_block_match.group(1)

        # The actual CSS height value must NOT be 600px
        assert "600px" not in css_body, (
            "The #graph-container CSS block must NOT specify '600px' as a "
            "height value. The graph container should use viewport-relative "
            "height (calc(100vh - 120px)), not a fixed pixel height. "
            f"Got CSS body: {css_body.strip()}"
        )
