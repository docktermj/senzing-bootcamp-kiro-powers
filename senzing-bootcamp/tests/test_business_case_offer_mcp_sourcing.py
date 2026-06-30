"""MCP-sourcing integration tests for the module1-business-case-offer feature.

These example/integration tests verify the *contract* that the Module 1
discovery steering (``module-01-phase1-discovery.md``) mandates for sourcing
CORD facts when the Bootcamp generates a scenario:

- The acceptance / CORD-sourcing branch (Step 5a / Step 5b) instructs the Agent
  to retrieve CORD details from the Senzing MCP server via ``get_sample_data``
  and/or ``search_docs`` and to present the returned values verbatim rather than
  substituting static figures (Requirements 3.4, 6.1).
- That branch encodes a 30-second timeout and a single-retry fallback to
  synthetic ``Generated_Data``, consistent with the established Step 6d
  license-guidance MCP pattern (Requirement 6.3, plus the Step 6d-consistency
  note from the design).

The live MCP call itself is exercised by the Agent at runtime; here we assert
the behavior is *mandated by the steering text*. Checks are intentionally robust
— case-insensitive substring/keyword matching tolerant of minor wording — so
they pin the stable contract rather than brittle exact lines.

**Validates: Requirements 3.4, 6.1, 6.3**
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_DISCOVERY_FILE = _STEERING_DIR / "module-01-phase1-discovery.md"


# ---------------------------------------------------------------------------
# Readers / section extraction
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the full UTF-8 text of a file."""
    return path.read_text(encoding="utf-8")


def _slice_between(text: str, start_pat: str, end_pat: str | None) -> str | None:
    """Return the slice of ``text`` from ``start_pat`` up to ``end_pat``.

    Args:
        text: The text to slice.
        start_pat: Regex marking the (inclusive) start.
        end_pat: Regex marking the (exclusive) end, or None for end-of-text.

    Returns:
        The matched slice, or None if ``start_pat`` is not found.
    """
    start_match = re.search(start_pat, text)
    if not start_match:
        return None
    start = start_match.start()
    if end_pat is None:
        return text[start:]
    end_match = re.search(end_pat, text[start_match.end():])
    end = start_match.end() + end_match.start() if end_match else len(text)
    return text[start:end]


def _cord_sourcing_section() -> str:
    """Return the acceptance + CORD-sourcing branch (Step 5a through 5b).

    This spans the Business_Case_Offer acceptance handling (5a) and the CORD
    sourcing-via-MCP branch (5b), up to the start of the numbered Step 6
    ("Infer details from response"). This is the context in which the steering
    mandates the MCP-sourcing contract.
    """
    content = _read(_DISCOVERY_FILE)
    section = _slice_between(content, r"5a\.\s*\*\*Business Case Offer", r"\n6\.\s*\*\*Infer")
    assert section is not None, (
        "Could not locate the Step 5a/5b CORD-sourcing branch in "
        f"{_DISCOVERY_FILE.name}"
    )
    return section


def _step6d_section() -> str:
    """Return the established Step 6d license-guidance branch text.

    Used to confirm the 30-second-timeout / MCP-fallback pattern the CORD
    sourcing branch (5b) explicitly mirrors.
    """
    content = _read(_DISCOVERY_FILE)
    section = _slice_between(content, r"\*\*6d\.", r"\*\*Checkpoint:\*\* Write step 6d")
    assert section is not None, (
        f"Could not locate the Step 6d license-guidance branch in {_DISCOVERY_FILE.name}"
    )
    return section


# ===========================================================================
# CORD facts are sourced from the MCP server and presented verbatim
# **Validates: Requirements 3.4, 6.1**
# ===========================================================================


class TestMcpSourcingContract:
    """The CORD-sourcing branch mandates retrieving CORD facts from MCP tools
    and presenting the returned values verbatim (not static figures)."""

    def test_invokes_get_sample_data_tool(self) -> None:
        """**Validates: Requirements 3.4, 6.1** — names the get_sample_data tool."""
        section = _cord_sourcing_section()
        assert "get_sample_data" in section, (
            "The CORD-sourcing branch must instruct the Agent to call get_sample_data"
        )

    def test_invokes_search_docs_tool(self) -> None:
        """**Validates: Requirements 3.4, 6.1** — names the search_docs tool."""
        section = _cord_sourcing_section()
        assert "search_docs" in section, (
            "The CORD-sourcing branch must instruct the Agent to call search_docs"
        )

    def test_retrieves_cord_facts_from_mcp_server(self) -> None:
        """**Validates: Requirements 3.4, 6.1** — CORD facts come from the MCP server."""
        lower = _cord_sourcing_section().lower()
        assert "cord" in lower, "The branch must concern CORD datasets"
        assert "mcp server" in lower, (
            "The branch must direct CORD-fact retrieval to the MCP server"
        )

    def test_presents_returned_values_verbatim(self) -> None:
        """**Validates: Requirements 6.1** — present returned/verbatim values."""
        lower = _cord_sourcing_section().lower()
        verbatim_signals = (
            "verbatim",
            "exactly as the mcp server returns",
            "present those values exactly",
        )
        assert any(signal in lower for signal in verbatim_signals), (
            "The branch must instruct presenting the MCP-returned values verbatim; "
            f"expected one of {verbatim_signals}"
        )

    def test_forbids_substituting_static_figures(self) -> None:
        """**Validates: Requirements 6.1** — do not substitute static figures."""
        lower = _cord_sourcing_section().lower()
        # Tolerant of wording: "do not substitute a static, hardcoded, or
        # remembered dataset name or record count" / "never ... training data".
        assert "do not substitute" in lower or "never" in lower, (
            "The branch must forbid substituting static/remembered figures"
        )
        assert (
            "static" in lower
            or "hardcoded" in lower
            or "remembered" in lower
            or "training data" in lower
        ), (
            "The branch must contrast MCP-returned values with static/hardcoded/"
            "remembered/training-data figures"
        )


# ===========================================================================
# 30-second timeout + single-retry fallback to Generated_Data (mirrors 6d)
# **Validates: Requirements 6.3**
# ===========================================================================


class TestTimeoutAndRetryFallback:
    """The CORD-sourcing branch encodes the 30-second timeout and single-retry
    fallback to Generated_Data, consistent with the Step 6d MCP pattern."""

    def test_encodes_thirty_second_timeout(self) -> None:
        """**Validates: Requirements 6.3** — 30-second timeout language present."""
        lower = _cord_sourcing_section().lower()
        assert "30 second" in lower or "30-second" in lower, (
            "The CORD-sourcing branch must encode a 30-second MCP timeout"
        )

    def test_encodes_single_retry(self) -> None:
        """**Validates: Requirements 6.3** — single-retry language present."""
        lower = _cord_sourcing_section().lower()
        retry_signals = ("retry once", "1 retry", "one retry", "single-retry", "single retry")
        assert any(signal in lower for signal in retry_signals), (
            "The CORD-sourcing branch must encode a single MCP retry; "
            f"expected one of {retry_signals}"
        )

    def test_falls_back_to_generated_data(self) -> None:
        """**Validates: Requirements 6.3** — fallback to Generated_Data on failure."""
        lower = _cord_sourcing_section().lower()
        assert "generated_data" in lower, (
            "The fallback must produce Generated_Data when CORD facts are unavailable"
        )
        fallback_signals = ("rather than cord", "instead of", "fall back", "fallback", "omit")
        assert any(signal in lower for signal in fallback_signals), (
            "The branch must describe falling back to Generated_Data instead of CORD; "
            f"expected one of {fallback_signals}"
        )

    def test_consistent_with_step_6d_pattern(self) -> None:
        """**Validates: Requirements 6.3** — branch mirrors the Step 6d pattern."""
        section_lower = _cord_sourcing_section().lower()
        assert "6d" in section_lower, (
            "The CORD-sourcing branch must reference the established Step 6d "
            "timeout/retry pattern it mirrors"
        )
        # The established Step 6d branch itself encodes the same 30-second timeout,
        # confirming the pattern the CORD-sourcing branch is consistent with.
        step6d_lower = _step6d_section().lower()
        assert "30 second" in step6d_lower or "30-second" in step6d_lower, (
            "Step 6d must encode the 30-second MCP timeout that 5b mirrors"
        )
