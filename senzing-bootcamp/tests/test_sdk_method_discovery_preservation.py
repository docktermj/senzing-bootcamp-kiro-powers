"""Preservation property tests for sdk-method-discovery bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: sdk-method-discovery
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_AGENT_INSTRUCTIONS = _BOOTCAMP_DIR / "steering" / "agent-instructions.md"
_MCP_DECISION_TREE = _BOOTCAMP_DIR / "steering" / "mcp-tool-decision-tree.md"
_MODULE_07 = _BOOTCAMP_DIR / "steering" / "module-07-query-validation.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_section(markdown: str, heading: str, level: int = 2) -> str:
    """Extract a markdown section from a heading to the next same-level heading.

    Args:
        markdown: Full markdown text.
        heading: The heading text (without the ``##`` prefix).
        level: Heading level (number of ``#`` characters).

    Returns:
        The section body including the heading line itself.
    """
    prefix = "#" * level
    pattern = rf"(^{prefix} {re.escape(heading)}.*?)(?=\n{prefix} |\Z)"
    match = re.search(pattern, markdown, re.DOTALL | re.MULTILINE)
    return match.group(1) if match else ""


def _extract_mcp_rules_section(markdown: str) -> str:
    """Extract the MCP Rules section from agent-instructions.md.

    Returns:
        The MCP Rules section content (from ``## MCP Rules`` to the next
        ``## `` heading).
    """
    return _extract_section(markdown, "MCP Rules")


def _extract_bullet_points(section: str) -> list[str]:
    """Extract all top-level bullet points (lines starting with ``- ``) from a section.

    Args:
        section: Markdown section text.

    Returns:
        List of bullet point lines (stripped of the leading ``- ``).
    """
    bullets = []
    for line in section.split("\n"):
        if line.startswith("- "):
            bullets.append(line[2:].strip())
    return bullets


# ---------------------------------------------------------------------------
# Observed baselines (snapshot from unfixed code)
# ---------------------------------------------------------------------------

# MCP Rules bullet points observed in the unfixed agent-instructions.md
_OBSERVED_MCP_BULLETS = [
    "All Senzing facts from MCP tools — never training data. Call `get_capabilities` first each session.",
    "Attribute names → `mapping_workflow` | SDK code → `generate_scaffold`/`sdk_guide` | Signatures → `get_sdk_reference` | Errors → `explain_error_code` | Docs → `search_docs` | Examples → `find_examples`",
    "SDK method calls that accept flags: look up available flags via get_sdk_reference(topic='flags'), select flags matching the bootcamper's intent, and explain the choice in one sentence. Reuse flag knowledge within a module session. Default flags are acceptable for simple lookups but note that detailed flags exist.",
    "Uncertain which tool? Load `mcp-tool-decision-tree.md` for the full decision tree with anti-patterns and call examples.",
    "Never hand-code Senzing JSON mappings or SDK method names",
    "Third-party software: consult Senzing MCP (`search_docs`) before recommending tools in a Senzing integration context.",
    "Reuse MCP responses within a module; re-query across module boundaries. No answer? Say so, suggest <https://docs.senzing.com> / <support@senzing.com> — never fabricate.",
    "MCP skepticism: flag data mart tables (`sz_dm_report`), beta features, or non-core SDK references",
    "Never generate direct SQL (SELECT, INSERT, UPDATE, DELETE) against the Senzing database (`database/G2C.db`) or its internal tables (RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, etc.). All Senzing data access must go through SDK methods via MCP tools.",
    'SQL-tempting question redirects: "count entities" → `reporting_guide` | "find duplicates" → `search_by_attributes` | "show entity details" → `get_entity`/`get_entity_by_record_id` | "why did these match" → `why_entities`/`why_records` | "how was entity built" → `how_entity` | "export entity data" → iterate SDK methods via MCP tools',
]

# Decision tree sections observed in the unfixed mcp-tool-decision-tree.md
_OBSERVED_DECISION_TREE_SECTIONS = [
    "Session Start",
    "What Is the Bootcamper Trying to Do?",
    "Anti-Patterns: When NOT to Use",
    "Call Pattern Examples",
    "Flag Selection Protocol",
]

# Decision tree subsections (### level)
_OBSERVED_DECISION_TREE_SUBSECTIONS = [
    "Data Preparation",
    "SDK Development",
    "Troubleshooting",
    "Reference and Reporting",
    "Data Exploration",
]

# Non-MCP sections in agent-instructions.md that must remain unchanged
_NON_MCP_SECTIONS = [
    "Communication",
    "Module Steering",
    "Track Switching",
    "State & Progress",
    "Hooks",
    "Context Budget",
    "Mandatory Gate Precedence",
]


# ---------------------------------------------------------------------------
# Test 1 — Existing MCP Rule Bullets Preserved
# ---------------------------------------------------------------------------


class TestExistingMCPRuleBulletsPreserved:
    """All existing MCP rule bullet points are present and unchanged.

    **Validates: Requirements 3.1, 3.2**

    The fix is additive — it must not remove or modify any existing
    MCP rule bullet points.
    """

    def test_all_existing_mcp_bullets_present(self) -> None:
        """Assert every observed MCP rule bullet is present in the file."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        mcp_section = _extract_mcp_rules_section(content)
        assert mcp_section, "MCP Rules section not found in agent-instructions.md"

        bullets = _extract_bullet_points(mcp_section)
        for expected_bullet in _OBSERVED_MCP_BULLETS:
            assert expected_bullet in bullets, (
                f"MCP rule bullet missing or changed:\n"
                f"  Expected: {expected_bullet[:100]}...\n"
                f"  Found bullets: {len(bullets)}"
            )

    def test_mcp_bullet_count_at_least_observed(self) -> None:
        """Assert the MCP Rules section has at least as many bullets as observed."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        mcp_section = _extract_mcp_rules_section(content)
        bullets = _extract_bullet_points(mcp_section)
        assert len(bullets) >= len(_OBSERVED_MCP_BULLETS), (
            f"MCP Rules section has fewer bullets ({len(bullets)}) than "
            f"observed baseline ({len(_OBSERVED_MCP_BULLETS)})"
        )


# ---------------------------------------------------------------------------
# Test 2 — Flag Lookup Rule Preserved
# ---------------------------------------------------------------------------


class TestFlagLookupRulePreserved:
    """The specific rule about looking up flags via get_sdk_reference is preserved.

    **Validates: Requirements 3.4**

    The flag lookup rule must remain unchanged — it's a core MCP usage
    pattern that the fix must not alter.
    """

    def test_flag_lookup_rule_present(self) -> None:
        """Assert the flag lookup rule text is present and unchanged."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        expected = (
            "SDK method calls that accept flags: look up available flags via "
            "get_sdk_reference(topic='flags'), select flags matching the "
            "bootcamper's intent, and explain the choice in one sentence."
        )
        assert expected in content, (
            "Flag lookup rule not found in agent-instructions.md.\n"
            f"Expected text: {expected}"
        )

    def test_flag_reuse_instruction_present(self) -> None:
        """Assert the flag reuse instruction is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "Reuse flag knowledge within a module session" in content, (
            "Flag reuse instruction missing from agent-instructions.md"
        )


# ---------------------------------------------------------------------------
# Test 3 — SQL Redirects Preserved
# ---------------------------------------------------------------------------


class TestSQLRedirectsPreserved:
    """The SQL-tempting question redirects line is present and unchanged.

    **Validates: Requirements 3.4**

    The SQL redirects provide direct mappings for unambiguous cases
    and must not be modified by the fix.
    """

    def test_sql_redirects_line_present(self) -> None:
        """Assert the SQL-tempting question redirects line is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "SQL-tempting question redirects:" in content, (
            "SQL-tempting question redirects line missing"
        )

    def test_sql_redirects_contains_all_mappings(self) -> None:
        """Assert all SQL redirect mappings are present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        mappings = [
            '"count entities" → `reporting_guide`',
            '"find duplicates" → `search_by_attributes`',
            '"show entity details" → `get_entity`/`get_entity_by_record_id`',
            '"why did these match" → `why_entities`/`why_records`',
            '"how was entity built" → `how_entity`',
            '"export entity data" → iterate SDK methods via MCP tools',
        ]
        for mapping in mappings:
            assert mapping in content, (
                f"SQL redirect mapping missing: {mapping}"
            )


# ---------------------------------------------------------------------------
# Test 4 — Communication Section Preserved
# ---------------------------------------------------------------------------


class TestCommunicationSectionPreserved:
    """The Communication section's rules are unchanged.

    **Validates: Requirements 3.1, 3.2**

    The 👉 rules, one-question-at-a-time rule, and fabrication
    prohibition must remain intact.
    """

    def test_communication_section_exists(self) -> None:
        """Assert the Communication section exists."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, "Communication")
        assert section, "Communication section not found"

    def test_one_question_at_a_time_rule(self) -> None:
        """Assert the one-question-at-a-time rule is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, "Communication")
        assert "One question at a time, wait for response" in section, (
            "One-question-at-a-time rule missing from Communication section"
        )

    def test_point_right_prefix_rule(self) -> None:
        """Assert the 👉 prefix rule for input-required questions is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, "Communication")
        assert 'Prefix input-required questions with "👉"' in section, (
            "👉 prefix rule missing from Communication section"
        )

    def test_fabrication_prohibition(self) -> None:
        """Assert the fabrication prohibition is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, "Communication")
        assert "Never fabricate user input" in section, (
            "Fabrication prohibition missing from Communication section"
        )

    def test_never_combine_questions_rule(self) -> None:
        """Assert the NEVER combine questions rule is present."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        section = _extract_section(content, "Communication")
        assert "NEVER combine questions with conjunctions" in section, (
            "NEVER combine questions rule missing from Communication section"
        )


# ---------------------------------------------------------------------------
# Test 5 — YAML Frontmatter Preserved
# ---------------------------------------------------------------------------


class TestYAMLFrontmatterPreserved:
    """agent-instructions.md begins with YAML frontmatter containing inclusion: always.

    **Validates: Requirements 3.1**

    The YAML frontmatter is critical for the steering file loading
    mechanism and must not be altered.
    """

    def test_starts_with_yaml_frontmatter(self) -> None:
        """Assert the file begins with YAML frontmatter delimiters."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert content.startswith("---\n"), (
            "agent-instructions.md does not start with YAML frontmatter"
        )

    def test_frontmatter_contains_inclusion_always(self) -> None:
        """Assert the frontmatter contains 'inclusion: always'."""
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        # Extract frontmatter between first and second ---
        parts = content.split("---", 2)
        assert len(parts) >= 3, (
            "Could not parse YAML frontmatter (missing closing ---)"
        )
        frontmatter = parts[1]
        assert "inclusion: always" in frontmatter, (
            "YAML frontmatter missing 'inclusion: always'"
        )


# ---------------------------------------------------------------------------
# Test 6 — Flag Selection Protocol Preserved
# ---------------------------------------------------------------------------


class TestFlagSelectionProtocolPreserved:
    """mcp-tool-decision-tree.md contains the Flag Selection Protocol unchanged.

    **Validates: Requirements 3.4**

    The Flag Selection Protocol's 4-step flow (Discover, Select,
    Explain, Cache) must remain intact.
    """

    def test_flag_selection_protocol_section_exists(self) -> None:
        """Assert the Flag Selection Protocol section exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        section = _extract_section(content, "Flag Selection Protocol")
        assert section, (
            "Flag Selection Protocol section not found in mcp-tool-decision-tree.md"
        )

    def test_discover_step_present(self) -> None:
        """Assert the Discover step is present in the protocol."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        section = _extract_section(content, "Flag Selection Protocol")
        assert "**Discover**" in section, (
            "Flag Selection Protocol missing Discover step"
        )
        assert "get_sdk_reference" in section, (
            "Flag Selection Protocol Discover step missing get_sdk_reference"
        )

    def test_select_step_present(self) -> None:
        """Assert the Select step is present in the protocol."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        section = _extract_section(content, "Flag Selection Protocol")
        assert "**Select**" in section, (
            "Flag Selection Protocol missing Select step"
        )

    def test_explain_step_present(self) -> None:
        """Assert the Explain step is present in the protocol."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        section = _extract_section(content, "Flag Selection Protocol")
        assert "**Explain**" in section, (
            "Flag Selection Protocol missing Explain step"
        )

    def test_cache_step_present(self) -> None:
        """Assert the Cache step is present in the protocol."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        section = _extract_section(content, "Flag Selection Protocol")
        assert "**Cache**" in section, (
            "Flag Selection Protocol missing Cache step"
        )

    def test_when_to_skip_flag_lookup_present(self) -> None:
        """Assert the 'When to Skip Flag Lookup' subsection is present."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### When to Skip Flag Lookup" in content, (
            "When to Skip Flag Lookup subsection missing"
        )


# ---------------------------------------------------------------------------
# Test 7 — Module-07 Agent Instructions Preserved
# ---------------------------------------------------------------------------


class TestModule07AgentInstructionsPreserved:
    """module-07-query-validation.md agent instructions about flag lookups preserved.

    **Validates: Requirements 3.4**

    The module-07 file contains agent instructions about looking up
    flags for how_entity, why_entities, etc. These must not be modified.
    """

    def test_module07_flag_lookup_instruction_present(self) -> None:
        """Assert the flag lookup agent instruction for query methods is present."""
        content = _MODULE_07.read_text(encoding="utf-8")
        expected = (
            "When generating query code that calls SDK methods accepting flags "
            "(get_entity, search_by_attributes, how_entity, why_entities, "
            "why_records, why_record_in_entity), look up available flags via "
            "`get_sdk_reference(method='<method>', topic='flags')`"
        )
        assert expected in content, (
            "Module-07 flag lookup agent instruction missing or changed"
        )

    def test_module07_how_entity_mentioned(self) -> None:
        """Assert how_entity is mentioned in module-07 agent instructions."""
        content = _MODULE_07.read_text(encoding="utf-8")
        assert "how_entity" in content, (
            "how_entity not found in module-07-query-validation.md"
        )

    def test_module07_why_entities_mentioned(self) -> None:
        """Assert why_entities is mentioned in module-07 agent instructions."""
        content = _MODULE_07.read_text(encoding="utf-8")
        assert "why_entities" in content, (
            "why_entities not found in module-07-query-validation.md"
        )

    def test_module07_why_records_mentioned(self) -> None:
        """Assert why_records is mentioned in module-07 agent instructions."""
        content = _MODULE_07.read_text(encoding="utf-8")
        assert "why_records" in content, (
            "why_records not found in module-07-query-validation.md"
        )

    def test_module07_why_record_in_entity_mentioned(self) -> None:
        """Assert why_record_in_entity is mentioned in module-07."""
        content = _MODULE_07.read_text(encoding="utf-8")
        assert "why_record_in_entity" in content, (
            "why_record_in_entity not found in module-07-query-validation.md"
        )

    def test_module07_feature_scores_flag_instruction(self) -> None:
        """Assert the SZ_INCLUDE_FEATURE_SCORES instruction is present."""
        content = _MODULE_07.read_text(encoding="utf-8")
        assert "SZ_INCLUDE_FEATURE_SCORES" in content, (
            "SZ_INCLUDE_FEATURE_SCORES not found in module-07"
        )


# ---------------------------------------------------------------------------
# Test 8 — Decision Tree Sections Preserved
# ---------------------------------------------------------------------------


class TestDecisionTreeSectionsPreserved:
    """All existing sections in mcp-tool-decision-tree.md are present.

    **Validates: Requirements 3.4**

    The fix adds a new section but must not remove or rename any
    existing sections.
    """

    def test_session_start_section_present(self) -> None:
        """Assert Session Start section exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "## Session Start" in content, "Session Start section missing"

    def test_data_preparation_subsection_present(self) -> None:
        """Assert Data Preparation subsection exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### Data Preparation" in content, "Data Preparation subsection missing"

    def test_sdk_development_subsection_present(self) -> None:
        """Assert SDK Development subsection exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### SDK Development" in content, "SDK Development subsection missing"

    def test_troubleshooting_subsection_present(self) -> None:
        """Assert Troubleshooting subsection exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### Troubleshooting" in content, "Troubleshooting subsection missing"

    def test_reference_and_reporting_subsection_present(self) -> None:
        """Assert Reference and Reporting subsection exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### Reference and Reporting" in content, (
            "Reference and Reporting subsection missing"
        )

    def test_data_exploration_subsection_present(self) -> None:
        """Assert Data Exploration subsection exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "### Data Exploration" in content, "Data Exploration subsection missing"

    def test_anti_patterns_section_present(self) -> None:
        """Assert Anti-Patterns section exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "## Anti-Patterns: When NOT to Use" in content, (
            "Anti-Patterns section missing"
        )

    def test_call_pattern_examples_section_present(self) -> None:
        """Assert Call Pattern Examples section exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "## Call Pattern Examples" in content, (
            "Call Pattern Examples section missing"
        )

    def test_flag_selection_protocol_section_present(self) -> None:
        """Assert Flag Selection Protocol section exists."""
        content = _MCP_DECISION_TREE.read_text(encoding="utf-8")
        assert "## Flag Selection Protocol" in content, (
            "Flag Selection Protocol section missing"
        )


# ---------------------------------------------------------------------------
# PBT Test — Non-MCP Sections Unchanged
# ---------------------------------------------------------------------------


def _snapshot_section_content(markdown: str, heading: str) -> str:
    """Get the content of a section for comparison.

    Returns the section text stripped of leading/trailing whitespace.
    """
    return _extract_section(markdown, heading).strip()


# Pre-compute the baseline content for each non-MCP section
_BASELINE_CONTENT: dict[str, str] = {}


def _load_baseline() -> dict[str, str]:
    """Load baseline content for all non-MCP sections (cached)."""
    if not _BASELINE_CONTENT:
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        for section_name in _NON_MCP_SECTIONS:
            _BASELINE_CONTENT[section_name] = _snapshot_section_content(
                content, section_name
            )
    return _BASELINE_CONTENT


@st.composite
def st_non_mcp_section_name(draw: st.DrawFn) -> str:
    """Generate a non-MCP section heading name from the observed set.

    These sections should remain completely unchanged after the fix.
    """
    return draw(st.sampled_from(_NON_MCP_SECTIONS))


class TestNonMCPSectionsUnchangedProperty:
    """PBT — Non-MCP sections are identical between baseline and current file.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    Use Hypothesis to generate section heading names from the set of
    non-MCP sections and verify each section's content is identical
    between the observed baseline and the current file.
    """

    @given(section_name=st_non_mcp_section_name())
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_mcp_section_content_unchanged(self, section_name: str) -> None:
        """For any non-MCP section, content must match the baseline."""
        baseline = _load_baseline()
        current_content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        current_section = _snapshot_section_content(current_content, section_name)

        assert baseline[section_name], (
            f"Baseline for section '{section_name}' is empty — section not found"
        )
        assert current_section == baseline[section_name], (
            f"Non-MCP section '{section_name}' has been modified.\n"
            f"Baseline length: {len(baseline[section_name])}\n"
            f"Current length: {len(current_section)}\n"
            f"First 200 chars of baseline: {baseline[section_name][:200]}\n"
            f"First 200 chars of current: {current_section[:200]}"
        )
