"""Property-based tests for MCP failure recovery steering content.

Uses Hypothesis to validate structural invariants of the offline fallback
steering file across all entries. Each property test class validates one
correctness property from the design document.

Correctness Properties:
  Property 1 — Fallback step count bounds (Req 1.2, 8.1)
  Property 2 — No forbidden guessing phrases (Req 1.3)
  Property 3 — Concrete alternative resources (Req 1.4)
  Property 4 — Blocked operation ↔ fallback round-trip (Req 1.5, 8.3)
  Property 5 — Error handling fallback path (Req 2.6)
  Property 6 — Troubleshooting entry completeness (Req 4.2)
  Property 7 — Continuable operations table structure (Req 6.2, 6.3, 8.4)
  Property 8 — No MCP dependency in continuable ops (Req 6.5)
  Property 9 — Decision tree superset of blocked ops (Req 7.4)
  Property 10 — No MCP call in fallback steps (Req 8.2)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Import parsing logic from the example-based test file (task 1)
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from test_mcp_failure_recovery import (  # noqa: E402
    ALL_MCP_TOOLS,
    ACTIONABLE_VERBS,
    FORBIDDEN_PHRASES,
    MCP_DEPENDENT_MODULES,
    extract_section,
    parse_blocked_operations_table,
    parse_call_pattern_tools,
    parse_continuable_operations,
    parse_fallback_instructions,
    parse_troubleshooting_table,
)

# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_OFFLINE_FALLBACK_PATH = _STEERING_DIR / "mcp-offline-fallback.md"
_DECISION_TREE_PATH = _STEERING_DIR / "mcp-tool-decision-tree.md"

# ---------------------------------------------------------------------------
# Document Loading (parse-once pattern)
# ---------------------------------------------------------------------------

_OFFLINE_FALLBACK_CONTENT = _OFFLINE_FALLBACK_PATH.read_text(encoding="utf-8")
_DECISION_TREE_CONTENT = _DECISION_TREE_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Pre-parsed Data
# ---------------------------------------------------------------------------

_BLOCKED_OPS = parse_blocked_operations_table(_OFFLINE_FALLBACK_CONTENT)
_FALLBACK_INSTRUCTIONS = parse_fallback_instructions(_OFFLINE_FALLBACK_CONTENT)
_CONTINUABLE_OPS = parse_continuable_operations(_OFFLINE_FALLBACK_CONTENT)
_TROUBLESHOOTING = parse_troubleshooting_table(_OFFLINE_FALLBACK_CONTENT)
_CALL_PATTERN_TOOLS = parse_call_pattern_tools(_DECISION_TREE_CONTENT)

# ---------------------------------------------------------------------------
# Hypothesis Strategies (st.sampled_from parsed document elements)
# ---------------------------------------------------------------------------

st_blocked_operation = st.sampled_from(_BLOCKED_OPS)
st_fallback_tool = st.sampled_from(list(_FALLBACK_INSTRUCTIONS.keys()))
st_continuable_operation = st.sampled_from(_CONTINUABLE_OPS)
st_troubleshooting_entry = st.sampled_from(_TROUBLESHOOTING)
st_mcp_dependent_module_path = st.sampled_from(list(MCP_DEPENDENT_MODULES.values()))


# ---------------------------------------------------------------------------
# Property Test Classes
# ---------------------------------------------------------------------------


class TestFallbackStepCountBounds:
    """Feature: mcp-failure-recovery-testing, Property 1: Fallback instruction step count bounds

    For any fallback instruction in the Offline_Fallback_Steering, the number
    of numbered steps SHALL be at least 2 and no more than 10.

    **Validates: Requirements 1.2, 8.1**
    """

    @given(tool=st_fallback_tool)
    @settings(max_examples=100)
    def test_step_count_between_2_and_10(self, tool: str) -> None:
        """Each fallback instruction has between 2 and 10 numbered steps."""
        steps = _FALLBACK_INSTRUCTIONS[tool]
        assert 2 <= len(steps) <= 10, (
            f"Fallback for '{tool}' has {len(steps)} steps, expected 2–10"
        )


class TestNoForbiddenPhrases:
    """Feature: mcp-failure-recovery-testing, Property 2: No forbidden guessing phrases in fallback instructions

    For any fallback instruction in the Offline_Fallback_Steering, no step text
    SHALL contain the phrases "guess", "assume", "probably", or "might be".

    **Validates: Requirements 1.3**
    """

    @given(tool=st_fallback_tool)
    @settings(max_examples=100)
    def test_no_guessing_language(self, tool: str) -> None:
        """No fallback step contains forbidden guessing phrases."""
        steps = _FALLBACK_INSTRUCTIONS[tool]
        for i, step in enumerate(steps, 1):
            step_lower = step.lower()
            for phrase in FORBIDDEN_PHRASES:
                if phrase in step_lower:
                    # "Do NOT guess" is a prohibition, not guessing language
                    phrase_idx = step_lower.index(phrase)
                    context_start = max(0, phrase_idx - 10)
                    context = step_lower[context_start:phrase_idx]
                    if "not " in context or "do not" in context or "don't" in context:
                        continue
                    assert False, (
                        f"Fallback for '{tool}' step {i} contains "
                        f"forbidden phrase '{phrase}': {step}"
                    )


class TestFallbackConcreteResources:
    """Feature: mcp-failure-recovery-testing, Property 3: Fallback instructions reference concrete alternative resources

    For any fallback instruction in the Offline_Fallback_Steering, at least one
    step SHALL reference a concrete alternative resource (a URL matching
    `https://`, a local file path, or a backtick-formatted command).

    **Validates: Requirements 1.4**
    """

    _URL_PATTERN = re.compile(r"https?://")
    _PATH_PATTERN = re.compile(r"`[\w./\-]+`")
    _COMMAND_PATTERN = re.compile(r"`[^`]+`")

    @given(tool=st_fallback_tool)
    @settings(max_examples=100)
    def test_at_least_one_concrete_resource(self, tool: str) -> None:
        """Each fallback references a URL, file path, or command."""
        steps = _FALLBACK_INSTRUCTIONS[tool]
        all_text = " ".join(steps)
        has_url = bool(self._URL_PATTERN.search(all_text))
        has_path = bool(self._PATH_PATTERN.search(all_text))
        has_command = bool(self._COMMAND_PATTERN.search(all_text))
        assert has_url or has_path or has_command, (
            f"Fallback for '{tool}' has no concrete resource "
            "(URL, file path, or command)"
        )


class TestBlockedOperationFallbackRoundTrip:
    """Feature: mcp-failure-recovery-testing, Property 4: Blocked operation to fallback instruction round-trip

    For any blocked operation in the Offline_Fallback_Steering table, the tool
    name extracted from the table SHALL appear in backtick-formatted code within
    exactly one corresponding fallback instruction heading.

    **Validates: Requirements 1.5, 8.3**
    """

    @given(op=st_blocked_operation)
    @settings(max_examples=100)
    def test_tool_in_exactly_one_fallback_heading(self, op: dict[str, str]) -> None:
        """Each blocked operation tool appears in exactly one fallback heading."""
        tool = op["mcp_tool"]
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "Fallback Instructions by Operation"
        )
        # Count headings that contain the tool name in backticks
        heading_pattern = re.compile(
            r"\*\*[^*]+\*\*\s*\(`" + re.escape(tool) + r"`\s+unavailable\):"
        )
        matches = heading_pattern.findall(section)
        assert len(matches) == 1, (
            f"Tool '{tool}' appears in {len(matches)} fallback headings, expected 1"
        )


class TestErrorHandlingFallbackPath:
    """Feature: mcp-failure-recovery-testing, Property 5: Error handling sections reference explain_error_code with fallback path

    For any MCP-dependent module steering file that has an Error Handling
    section, that section SHALL reference `explain_error_code` and SHALL include
    a fallback path for when that tool is unavailable.

    **Validates: Requirements 2.6**
    """

    # Only modules that have Error Handling sections (per unit test in task 1)
    _MODULES_WITH_ERROR_HANDLING: list[Path] = [
        MCP_DEPENDENT_MODULES["module-02"],
        MCP_DEPENDENT_MODULES["module-03"],
        MCP_DEPENDENT_MODULES["module-06"],
        MCP_DEPENDENT_MODULES["module-07"],
    ]

    @given(module_path=st.sampled_from(_MODULES_WITH_ERROR_HANDLING))
    @settings(max_examples=100)
    def test_error_handling_has_explain_error_code_fallback(
        self, module_path: Path
    ) -> None:
        """Each MCP-dependent module error handling references explain_error_code with fallback."""
        content = module_path.read_text(encoding="utf-8")
        error_section = extract_section(content, "Error Handling")
        assert "explain_error_code" in error_section, (
            f"{module_path.name} Error Handling must reference explain_error_code"
        )
        assert "returns no result" in error_section or "unavailable" in error_section, (
            f"{module_path.name} Error Handling must have fallback path "
            "for when explain_error_code is unavailable"
        )


class TestTroubleshootingEntryCompleteness:
    """Feature: mcp-failure-recovery-testing, Property 6: Troubleshooting entries have non-empty Issue and Fix

    For any entry in the connectivity troubleshooting table, both the Issue
    column and the Fix column SHALL be non-empty strings with at least 5
    characters.

    **Validates: Requirements 4.2**
    """

    @given(entry=st_troubleshooting_entry)
    @settings(max_examples=100)
    def test_issue_and_fix_non_empty(self, entry: dict[str, str]) -> None:
        """Each troubleshooting entry has non-empty Issue and Fix columns."""
        assert len(entry["issue"].strip()) >= 5, (
            f"Troubleshooting Issue too short: '{entry['issue']}'"
        )
        assert len(entry["fix"].strip()) >= 5, (
            f"Troubleshooting Fix too short: '{entry['fix']}'"
        )


class TestContinuableOperationsTableStructure:
    """Feature: mcp-failure-recovery-testing, Property 7: Continuable operations tables have required columns with actionable content

    For any entry in the continuable operations tables, the entry SHALL have a
    "Modules" column value and a "What to do" column value, and the "What to do"
    value SHALL contain at least one actionable verb.

    **Validates: Requirements 6.2, 6.3, 8.4**
    """

    @given(op=st_continuable_operation)
    @settings(max_examples=100)
    def test_modules_and_what_to_do_with_actionable_verb(
        self, op: dict[str, str]
    ) -> None:
        """Each continuable operation has Modules column and actionable What to do."""
        assert op["modules"].strip(), (
            f"Continuable operation '{op['activity']}' has empty Modules column"
        )
        what_to_do = op["what_to_do"].strip()
        assert what_to_do, (
            f"Continuable operation '{op['activity']}' has empty 'What to do' column"
        )
        what_to_do_lower = what_to_do.lower()
        # Req 8.4 uses "such as" language — include the canonical list plus
        # common actionable verbs that clearly indicate concrete instructions.
        # Also: backtick-formatted commands (e.g., `python3 scripts/...`) are
        # inherently actionable since they are executable instructions.
        extended_verbs = ACTIONABLE_VERBS + [
            "fix", "add", "improve", "refactor", "test", "verify",
            "build", "define", "identify", "prepare", "edit", "set",
            "install", "configure", "deploy",
        ]
        has_actionable_verb = any(
            verb in what_to_do_lower for verb in extended_verbs
        )
        has_command = "`" in what_to_do  # backtick-formatted command is actionable
        assert has_actionable_verb or has_command, (
            f"Continuable operation '{op['activity']}' 'What to do' column "
            f"lacks actionable verb or command: '{what_to_do}'"
        )


class TestNoContinuableMCPDependency:
    """Feature: mcp-failure-recovery-testing, Property 8: No continuable operation references MCP tool as required dependency

    For any entry in the continuable operations tables, the "What to do" column
    SHALL NOT reference any of the 12 MCP tool names as a required operation.

    **Validates: Requirements 6.5**
    """

    @given(op=st_continuable_operation)
    @settings(max_examples=100)
    def test_no_mcp_tool_in_what_to_do(self, op: dict[str, str]) -> None:
        """No continuable operation references an MCP tool as required."""
        what_to_do_lower = op["what_to_do"].lower()
        for tool in ALL_MCP_TOOLS:
            assert tool not in what_to_do_lower, (
                f"Continuable operation '{op['activity']}' references "
                f"MCP tool '{tool}' in 'What to do' column"
            )


class TestDecisionTreeSupersetProperty:
    """Feature: mcp-failure-recovery-testing, Property 9: Decision tree call pattern tools are superset of blocked operations tools

    For any tool listed in the Blocked_Operation table of the
    Offline_Fallback_Steering, that tool SHALL appear in the Call Pattern
    Examples section of the MCP_Tool_Decision_Tree.

    **Validates: Requirements 7.4**
    """

    @given(op=st_blocked_operation)
    @settings(max_examples=100)
    def test_blocked_tool_in_decision_tree(self, op: dict[str, str]) -> None:
        """Each blocked operation tool appears in decision tree call patterns."""
        tool = op["mcp_tool"]
        assert tool in _CALL_PATTERN_TOOLS, (
            f"Blocked operation tool '{tool}' not found in decision tree "
            "call pattern examples"
        )


class TestNoMCPCallInFallbackSteps:
    """Feature: mcp-failure-recovery-testing, Property 10: No fallback instruction step references calling an MCP tool

    For any fallback instruction in the Offline_Fallback_Steering, no step SHALL
    contain a reference to calling any of the 12 MCP tool names (since fallbacks
    assume MCP is unavailable).

    **Validates: Requirements 8.2**
    """

    @given(tool=st_fallback_tool)
    @settings(max_examples=100)
    def test_no_mcp_tool_call_in_steps(self, tool: str) -> None:
        """No fallback step references calling an MCP tool."""
        steps = _FALLBACK_INSTRUCTIONS[tool]
        for i, step in enumerate(steps, 1):
            step_lower = step.lower()
            for mcp_tool in ALL_MCP_TOOLS:
                # Allow mentioning the tool name in context of "unavailable" or
                # "instead of" but not as an instruction to call it
                if mcp_tool in step_lower:
                    # Check if it's used as a call instruction
                    call_patterns = [
                        f"call {mcp_tool}",
                        f"use {mcp_tool}",
                        f"run {mcp_tool}",
                        f"invoke {mcp_tool}",
                        f"execute {mcp_tool}",
                    ]
                    for pattern in call_patterns:
                        assert pattern not in step_lower, (
                            f"Fallback for '{tool}' step {i} references "
                            f"calling MCP tool '{mcp_tool}': {step}"
                        )
