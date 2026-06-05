"""Bug condition exploration tests for sdk-method-discovery bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests 1-4 are EXPECTED TO FAIL on unfixed code — failure confirms the bug.
The PBT test is expected to PASS (confirms non-MCP sections don't contain
discovery protocol keywords).

Feature: sdk-method-discovery
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_AGENT_INSTRUCTIONS = _BOOTCAMP_DIR / "steering" / "agent-instructions.md"
_MCP_DECISION_TREE = _BOOTCAMP_DIR / "steering" / "mcp-tool-decision-tree.md"
# The detailed SDK method discovery protocol (category taxonomy, clarification
# instruction, skip conditions) was moved out of the agent-instructions.md MCP
# Rules section into this dedicated on-demand reference file (loaded via the
# "SDK method discovery & disambiguation flow" pointer in MCP Rules). The
# content moved unchanged in substance, so these baselines read it from its
# current shipped location.
_MCP_USAGE_REFERENCE = _BOOTCAMP_DIR / "steering" / "mcp-usage-reference.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(markdown: str, heading: str, level: int = 2) -> str:
    """Extract a markdown section from a heading to the next same-level heading.

    Args:
        markdown: Full markdown text.
        heading: The heading text to search for (without the prefix).
        level: Heading level (number of # characters).

    Returns:
        The section body (including the heading line itself).
    """
    prefix = "#" * level
    pattern = rf"({re.escape(prefix)} {re.escape(heading)}.*?)(?=\n{re.escape(prefix)} |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def _get_mcp_rules_section() -> str:
    """Extract the MCP Rules section from agent-instructions.md."""
    content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
    return _extract_section(content, "MCP Rules")


def _get_sdk_discovery_section() -> str:
    """Extract the SDK Method Discovery section from mcp-usage-reference.md.

    The discovery protocol (taxonomy, disambiguation, skip conditions) was
    moved out of the agent-instructions.md MCP Rules section into this
    dedicated on-demand reference file. Read the protocol from its current
    shipped location.
    """
    content = _MCP_USAGE_REFERENCE.read_text(encoding="utf-8")
    return _extract_section(content, "SDK Method Discovery")


def _get_all_section_headings(markdown: str, level: int = 2) -> list[str]:
    """Extract all section headings at a given level from markdown.

    Args:
        markdown: Full markdown text.
        level: Heading level (number of # characters).

    Returns:
        List of heading text strings.
    """
    prefix = "#" * level
    pattern = rf"^{re.escape(prefix)} (.+)$"
    return re.findall(pattern, markdown, re.MULTILINE)


# ---------------------------------------------------------------------------
# Keywords for discovery protocol detection
# ---------------------------------------------------------------------------

_DISCOVERY_PROTOCOL_KEYWORDS = re.compile(
    r"SDK Method Discovery|discovery protocol|discover.*methods.*before.*select|"
    r"discover-then-disambiguate|method discovery",
    re.IGNORECASE,
)

_CATEGORY_TAXONOMY_KEYWORDS = re.compile(
    r"(why/how|why.*how)\s*(category|group)|"
    r"how_entity.*why_entities.*why_records.*why_record_in_entity|"
    r"SDK method categor",
    re.IGNORECASE | re.DOTALL,
)

_CLARIFICATION_KEYWORDS = re.compile(
    r"disambiguate.*👉 question|"
    r"multiple matches.*👉 question|"
    r"ask a single 👉 question.*numbered choice|"
    r"multiple.*method.*👉.*numbered choice",
    re.IGNORECASE | re.DOTALL,
)

_SKIP_CONDITION_KEYWORDS = re.compile(
    r"skip.*condition|when.*discovery.*not.*needed|when to skip.*discovery|"
    r"(explicit.*method.*name|bootcamper.*names.*method).*"
    r"(unambiguous|already.*discover)",
    re.IGNORECASE | re.DOTALL,
)

# Non-MCP section headings that should NOT contain discovery protocol keywords
_NON_MCP_SECTIONS = [
    "Communication",
    "Module Steering",
    "Track Switching",
    "State & Progress",
    "Hooks",
    "Context Budget",
    "Mandatory Gate Precedence",
    "File Placement",
]


# ---------------------------------------------------------------------------
# Test 1 — Missing Discovery Protocol
# ---------------------------------------------------------------------------


class TestMissingDiscoveryProtocol:
    """Test 1 — Missing Discovery Protocol.

    **Validates: Requirements 1.1**

    Parse agent-instructions.md, extract the MCP Rules section, and assert it
    contains an SDK method discovery protocol instructing the agent to discover
    available methods via get_sdk_reference before selecting one when the
    request is ambiguous. On unfixed code this will FAIL because no protocol
    exists.
    """

    def test_mcp_rules_contains_discovery_protocol(self) -> None:
        mcp_section = _get_mcp_rules_section()
        assert mcp_section, "MCP Rules section not found in agent-instructions.md"
        assert _DISCOVERY_PROTOCOL_KEYWORDS.search(mcp_section), (
            "MCP Rules section does not contain an SDK method discovery protocol. "
            "Expected instructions to discover available methods via get_sdk_reference "
            "before selecting one when the request is ambiguous. "
            f"Section preview:\n{mcp_section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Category Taxonomy
# ---------------------------------------------------------------------------


class TestMissingCategoryTaxonomy:
    """Test 2 — Missing Category Taxonomy.

    **Validates: Requirements 1.2**

    Parse agent-instructions.md and assert it contains SDK method category
    definitions that group related methods (e.g., why/how category with
    how_entity, why_entities, why_records, why_record_in_entity). On unfixed
    code this will FAIL because no categories are defined.
    """

    def test_agent_instructions_contains_category_taxonomy(self) -> None:
        discovery_section = _get_sdk_discovery_section()
        assert discovery_section, (
            "SDK Method Discovery section not found in mcp-usage-reference.md"
        )
        assert _CATEGORY_TAXONOMY_KEYWORDS.search(discovery_section), (
            "SDK Method Discovery section does not contain SDK method category "
            "definitions grouping related methods (e.g., why/how category with "
            "how_entity, why_entities, why_records, why_record_in_entity). "
            f"Section preview:\n{discovery_section[:500]}"
        )
        # Independent content assertion: the moved-unchanged why/how methods are
        # all present, confirming the taxonomy moved without substantive change.
        for method in (
            "how_entity",
            "why_entities",
            "why_records",
            "why_record_in_entity",
        ):
            assert method in discovery_section, (
                f"Expected method '{method}' in the why/how category taxonomy."
            )
        assert "Categories with multiple alternatives" in discovery_section


# ---------------------------------------------------------------------------
# Test 3 — Missing Clarification Instruction
# ---------------------------------------------------------------------------


class TestMissingClarificationInstruction:
    """Test 3 — Missing Clarification Instruction.

    **Validates: Requirements 1.2, 1.3**

    Parse the MCP Rules section and assert it contains an instruction to ask
    a 👉 clarifying question when multiple discovered methods could satisfy
    the bootcamper's request. On unfixed code this will FAIL because no such
    instruction exists.
    """

    def test_mcp_rules_contains_clarification_instruction(self) -> None:
        discovery_section = _get_sdk_discovery_section()
        assert discovery_section, (
            "SDK Method Discovery section not found in mcp-usage-reference.md"
        )
        assert _CLARIFICATION_KEYWORDS.search(discovery_section), (
            "SDK Method Discovery section does not contain an instruction to ask a "
            "👉 question when multiple discovered methods could satisfy the request. "
            f"Section preview:\n{discovery_section[:500]}"
        )
        # Independent content assertion: the disambiguation step pairs a 👉
        # question with a numbered choice list (moved unchanged in substance).
        assert "👉" in discovery_section
        assert "numbered choice list" in discovery_section


# ---------------------------------------------------------------------------
# Test 4 — Missing Skip Conditions
# ---------------------------------------------------------------------------


class TestMissingSkipConditions:
    """Test 4 — Missing Skip Conditions.

    **Validates: Requirements 1.1**

    Assert the protocol defines explicit skip conditions: when the bootcamper
    names a method, when the request is unambiguous, when discovery was already
    performed in the session. On unfixed code this will FAIL because no skip
    conditions exist.
    """

    def test_mcp_rules_contains_skip_conditions(self) -> None:
        discovery_section = _get_sdk_discovery_section()
        assert discovery_section, (
            "SDK Method Discovery section not found in mcp-usage-reference.md"
        )
        assert _SKIP_CONDITION_KEYWORDS.search(discovery_section), (
            "SDK Method Discovery section does not define explicit skip conditions "
            "for the discovery protocol (when bootcamper names a method, when "
            "request is unambiguous, when discovery was already performed in the "
            f"session). Section preview:\n{discovery_section[:500]}"
        )
        # Independent content assertion: the three skip conditions moved unchanged.
        assert "Skip discovery when" in discovery_section
        assert "explicitly names a method" in discovery_section
        assert "unambiguously maps to one method" in discovery_section
        assert "already discovered in current module session" in discovery_section


# ---------------------------------------------------------------------------
# PBT Test — Discovery Protocol Placement
# ---------------------------------------------------------------------------


class TestDiscoveryProtocolPlacement:
    """PBT Test — Discovery Protocol Placement.

    **Validates: Requirements 1.1, 1.2, 1.3**

    Use Hypothesis to generate section headings from agent-instructions.md and
    verify that non-MCP sections (Communication, Hooks, Context Budget, etc.)
    do not contain SDK method discovery protocol keywords. This confirms the
    bug is scoped to the MCP Rules section (or its absence) and hasn't leaked
    into other sections.
    """

    @given(section_name=st.sampled_from(_NON_MCP_SECTIONS))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_mcp_sections_do_not_contain_discovery_keywords(
        self, section_name: str
    ) -> None:
        """Non-MCP sections should not contain SDK method discovery instructions."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, section_name)

        if not section:
            # Section doesn't exist — nothing to check (not a failure)
            return

        assert not _DISCOVERY_PROTOCOL_KEYWORDS.search(section), (
            f"Non-MCP section '{section_name}' unexpectedly contains SDK method "
            f"discovery protocol keywords. Discovery instructions should only "
            f"appear in the MCP Rules section. "
            f"Section preview:\n{section[:300]}"
        )
