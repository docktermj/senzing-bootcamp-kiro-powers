"""Unit tests for QR_Section stability across a normalization pass.

Feature: recap-qr-formatting (Task 8.2)

Verifies that ``normalize_markdown`` treats the new ``### Questions & Responses``
subsection (the Paired_Schema QR_Section) as known recap content: normalizing a
recap that contains a QR_Section leaves the section intact — the heading and its
``- **Q:**`` / ``- **R:**`` pairs are preserved and are not dropped or relocated
to an ``## Unmapped Content`` / unknown-content section.

Scripts are imported via the project's sys.path pattern (scripts are not a
package).

_Requirements: 5.5_
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make scripts importable (scripts are not a package).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import normalize_markdown

# A small recap with a single module whose exchanges are recorded in the
# Paired_Schema QR_Section (a `### Questions & Responses` heading with
# `- **Q:**` / `    - **R:**` pairs).
_RECAP_WITH_QR = (
    "# Senzing Bootcamp Recap\n"
    "\n"
    "**Bootcamper:** Ada Lovelace\n"
    "**Started:** 2026-01-01\n"
    "**Total Duration:** 45m\n"
    "\n"
    "---\n"
    "\n"
    "## Module 1: First Demo \u2014 2026-01-01 10:00\n"
    "\n"
    "### Information Shared\n"
    "\n"
    "- Shared a truth-set data source\n"
    "\n"
    "### Questions & Responses\n"
    "\n"
    "- **Q:** What is entity resolution?\n"
    "    - **R:** Determining when records refer to the same real-world entity.\n"
    "- **Q:** How do I load data?\n"
    "    - **R:** Run the load program against the mapped records.\n"
    "\n"
    "### Actions Taken\n"
    "\n"
    "- Ran the first demo\n"
    "\n"
    "### Duration\n"
    "\n"
    "45m\n"
    "\n"
    "---\n"
)


class TestNormalizeQRSubsection:
    """QR_Section survives a normalization pass unchanged in substance."""

    def test_questions_and_responses_recognized_as_recap_subsection(self) -> None:
        """`questions & responses` is a recognized recap subsection (Task 8.1)."""
        assert (
            "questions & responses"
            in normalize_markdown.RECOGNIZED_RECAP_SUBSECTIONS
        )

    def test_qr_section_preserved_on_normalization(self) -> None:
        """Normalizing a recap with a QR_Section keeps the section intact.

        The `### Questions & Responses` heading and every `- **Q:**` /
        `- **R:**` pair must survive, and none of that content may be relocated
        to an Unmapped/unknown-content section (Requirement 5.5).
        """
        normalized, warnings = normalize_markdown.normalize_recap(_RECAP_WITH_QR)

        # The heading is preserved.
        assert "### Questions & Responses" in normalized

        # Every Q/R pair is preserved verbatim.
        assert "- **Q:** What is entity resolution?" in normalized
        assert (
            "    - **R:** Determining when records refer to the same "
            "real-world entity." in normalized
        )
        assert "- **Q:** How do I load data?" in normalized
        assert (
            "    - **R:** Run the load program against the mapped records."
            in normalized
        )

        # The QR content must not be treated as unknown content.
        assert "## Unmapped Content" not in normalized
        assert warnings == []

    def test_qr_section_normalization_is_idempotent(self) -> None:
        """A second normalization pass yields the same result as the first."""
        first, _ = normalize_markdown.normalize_recap(_RECAP_WITH_QR)
        second, _ = normalize_markdown.normalize_recap(first)

        assert second == first
        assert "### Questions & Responses" in second
        assert "## Unmapped Content" not in second
