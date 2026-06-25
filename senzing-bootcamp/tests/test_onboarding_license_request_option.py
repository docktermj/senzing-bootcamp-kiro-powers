"""Content tests for the Step 5 Bootcamp Introduction licensing language.

These tests validate the licensing-related content within the
"## 5. Bootcamp Introduction" overview of
`senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`.

Requirements validated:
- Property 1 / Req 4.1: the overview offers requesting an evaluation license
  in-flow through the Senzing MCP server.
- Property 1: the apply/bring-your-own existing-license path remains present.
- Property 2 / Req 4.2: the licensing content carries no MCP/external URLs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_STEERING_REL_PATH = Path(
    "senzing-bootcamp/steering/onboarding-phase1b-intro-language.md"
)

# Built from parts so the literal endpoint never appears in this tracked file.
_MCP_HOST = "mcp" + "." + "senzing" + "." + "com"


def _find_steering_file() -> Path:
    """Locate the steering file by walking up from this test file.

    Returns:
        Path to the onboarding phase 1b intro-language steering file.

    Raises:
        FileNotFoundError: If the steering file cannot be located.
    """
    current = Path(__file__).resolve()
    for parent in (current, *current.parents):
        candidate = parent / _STEERING_REL_PATH
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Could not locate {_STEERING_REL_PATH} walking up from {current}"
    )


def _read_steering_text() -> str:
    """Read the steering file contents as UTF-8 text.

    Returns:
        The full text of the steering file.
    """
    return _find_steering_file().read_text(encoding="utf-8")


def _extract_step5_overview(text: str) -> str:
    """Extract the Step 5 Bootcamp Introduction overview region.

    The region starts at the "## 5. Bootcamp Introduction" heading and ends at
    the next level-2 heading or the "### 5a" subsection, which is where the
    overview bullet list concludes.

    Args:
        text: Full steering file text.

    Returns:
        The text of the Step 5 overview region.

    Raises:
        ValueError: If the Step 5 section heading is not found.
    """
    lines = text.splitlines()
    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## 5.") and "Bootcamp Introduction" in line:
            start = i
            break
    if start is None:
        raise ValueError("Could not find '## 5. Bootcamp Introduction' section")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j]
        if stripped.startswith("## ") or stripped.startswith("### 5a"):
            end = j
            break
    return "\n".join(lines[start:end])


def _extract_licensing_content(text: str) -> str:
    """Isolate the licensing-related bullets from the Step 5 overview.

    Collects overview bullet lines that reference licensing or evaluation
    concepts so assertions target only the licensing region.

    Args:
        text: Full steering file text.

    Returns:
        The licensing-related bullet lines joined by newlines.
    """
    overview = _extract_step5_overview(text)
    bullets = [
        line for line in overview.splitlines() if line.lstrip().startswith("- ")
    ]
    licensing = [b for b in bullets if re.search(r"licen|eval", b, re.IGNORECASE)]
    return "\n".join(licensing)


class TestStep5LicensingContent:
    """Validate the Step 5 overview licensing language (Properties 1 & 2)."""

    def test_overview_mentions_in_flow_mcp_request(self) -> None:
        """Overview offers requesting an eval license via the MCP server.

        Property 1 / Req 4.1: the licensing content must reference the Senzing
        MCP server AND requesting/issuing a temporary evaluation license.
        """
        content = _extract_licensing_content(_read_steering_text())
        assert content, "No licensing content found in the Step 5 overview"
        lowered = content.lower()

        mentions_mcp = "mcp server" in lowered
        mentions_request = re.search(r"request|issue", lowered) is not None
        mentions_eval_license = (
            re.search(r"(temporary|evaluation|eval)", lowered) is not None
            and re.search(r"licen", lowered) is not None
        )

        assert mentions_mcp, (
            "Licensing content should reference the Senzing MCP server. "
            f"Got: {content!r}"
        )
        assert mentions_request, (
            "Licensing content should mention requesting/issuing a license. "
            f"Got: {content!r}"
        )
        assert mentions_eval_license, (
            "Licensing content should mention a temporary evaluation license. "
            f"Got: {content!r}"
        )

    def test_overview_mentions_apply_existing_license(self) -> None:
        """The apply/bring-your-own existing-license path remains present.

        Property 1: the option to apply an existing license must persist.
        """
        content = _extract_licensing_content(_read_steering_text())
        assert content, "No licensing content found in the Step 5 overview"
        lowered = content.lower()

        mentions_existing_path = (
            "bring your own" in lowered
            or "apply" in lowered
            or "existing" in lowered
            or "your own" in lowered
        )
        assert mentions_existing_path, (
            "Licensing content should keep the apply/bring-your-own existing "
            f"license path. Got: {content!r}"
        )

    def test_no_urls_in_licensing_content(self) -> None:
        """The licensing content contains no MCP or external URLs.

        Property 2 / Req 4.2: no `http`/`https` schemes or MCP endpoints may
        appear in the licensing region.
        """
        content = _extract_licensing_content(_read_steering_text())
        assert content, "No licensing content found in the Step 5 overview"
        lowered = content.lower()

        forbidden = ["http://", "https://", _MCP_HOST, "www."]
        found = [token for token in forbidden if token in lowered]
        assert not found, (
            f"Licensing content must not contain URLs/endpoints; found {found}. "
            f"Got: {content!r}"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
