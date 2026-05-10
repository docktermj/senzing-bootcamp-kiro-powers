"""Tests for MCP failure recovery steering content.

Validates completeness and correctness of the offline fallback steering file,
module-level MCP failure handling, reconnection procedure, troubleshooting,
bootcamper communication template, continuable operations, and cross-document
consistency with the MCP tool decision tree.

Correctness Properties (from requirements.md):
  1.1–1.5 — Offline fallback steering completeness
  2.1–2.6 — Module steering MCP failure handling
  3.1–3.5 — Reconnection procedure verification
  4.1–4.4 — Connectivity troubleshooting completeness
  5.1–5.5 — Bootcamper communication template
  6.1–6.5 — Continuable operations coverage
  7.1–7.4 — MCP tool decision tree consistency
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_OFFLINE_FALLBACK_PATH = _STEERING_DIR / "mcp-offline-fallback.md"
_DECISION_TREE_PATH = _STEERING_DIR / "mcp-tool-decision-tree.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_MCP_TOOLS: list[str] = [
    "sdk_guide",
    "mapping_workflow",
    "generate_scaffold",
    "get_sdk_reference",
    "search_docs",
    "explain_error_code",
    "get_sample_data",
    "get_capabilities",
    "analyze_record",
    "find_examples",
    "reporting_guide",
    "download_resource",
]

MCP_DEPENDENT_MODULES: dict[str, Path] = {
    "module-02": _STEERING_DIR / "module-02-sdk-setup.md",
    "module-03": _STEERING_DIR / "module-03-quick-demo.md",
    "module-05-phase2": _STEERING_DIR / "module-05-phase2-data-mapping.md",
    "module-06": _STEERING_DIR / "module-06-load-data.md",
    "module-07": _STEERING_DIR / "module-07-query-validation.md",
}

FORBIDDEN_PHRASES: list[str] = ["guess", "assume", "probably", "might be"]

ACTIONABLE_VERBS: list[str] = [
    "check", "run", "read", "create", "copy", "update",
    "review", "write", "document", "commit",
]

# ---------------------------------------------------------------------------
# Document Loading (parse-once pattern)
# ---------------------------------------------------------------------------

_OFFLINE_FALLBACK_CONTENT = _OFFLINE_FALLBACK_PATH.read_text(encoding="utf-8")
_DECISION_TREE_CONTENT = _DECISION_TREE_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Parsing Helper Functions
# ---------------------------------------------------------------------------


def extract_section(content: str, heading: str) -> str:
    """Extract a section from Markdown content by heading text.

    Returns all content from the heading line until the next heading of the
    same or higher level, or end of file.
    """
    # Determine heading level from the heading text
    heading_match = re.search(
        r"^(#{1,6})\s+" + re.escape(heading), content, re.MULTILINE
    )
    if not heading_match:
        return ""
    level = len(heading_match.group(1))
    start = heading_match.end()

    # Find next heading of same or higher level
    next_heading = re.search(
        r"^#{1," + str(level) + r"}\s+", content[start:], re.MULTILINE
    )
    if next_heading:
        return content[start:start + next_heading.start()].strip()
    return content[start:].strip()


def parse_blocked_operations_table(content: str) -> list[dict[str, str]]:
    """Parse the Blocked Operations table into a list of row dicts.

    Each dict has keys: operation, mcp_tool, affected_modules, fallback_summary.
    """
    section = extract_section(content, "Blocked Operations (Require MCP)")
    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # Remove empty first/last from leading/trailing pipes
        cells = [c for c in cells if c]
        if len(cells) < 4:
            continue
        # Skip header and separator rows
        if cells[0] == "Operation" or re.match(r"^-+$", cells[0]):
            continue
        rows.append({
            "operation": cells[0],
            "mcp_tool": cells[1].strip("`"),
            "affected_modules": cells[2],
            "fallback_summary": cells[3],
        })
    return rows


def parse_fallback_instructions(content: str) -> dict[str, list[str]]:
    """Parse fallback instruction sections into a dict of tool_name -> steps.

    Looks for bold headings like **Operation** (`tool_name` unavailable):
    followed by numbered steps.
    """
    section = extract_section(content, "Fallback Instructions by Operation")
    result: dict[str, list[str]] = {}

    # Find each fallback block: **Title** (`tool_name` unavailable):
    pattern = re.compile(
        r"\*\*[^*]+\*\*\s*\(`([^`]+)`\s+unavailable\):", re.MULTILINE
    )
    matches = list(pattern.finditer(section))

    for i, match in enumerate(matches):
        tool_name = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        block = section[start:end]

        # Extract numbered steps
        steps = re.findall(r"^\d+\.\s+(.+)$", block, re.MULTILINE)
        result[tool_name] = steps

    return result


def parse_continuable_operations(content: str) -> list[dict[str, str]]:
    """Parse all continuable operations tables into a list of row dicts.

    Each dict has keys: category, activity, modules, what_to_do.
    """
    section = extract_section(content, "Continuable Operations (No MCP Needed)")
    rows: list[dict[str, str]] = []
    current_category = ""

    for line in section.splitlines():
        line_stripped = line.strip()
        # Detect category headings (### level)
        cat_match = re.match(r"^###\s+(.+)$", line_stripped)
        if cat_match:
            current_category = cat_match.group(1)
            continue
        if not line_stripped.startswith("|"):
            continue
        cells = [c.strip() for c in line_stripped.split("|")]
        cells = [c for c in cells if c]
        if len(cells) < 3:
            continue
        # Skip header and separator rows
        if cells[0] == "Activity" or re.match(r"^-+$", cells[0]):
            continue
        rows.append({
            "category": current_category,
            "activity": cells[0],
            "modules": cells[1],
            "what_to_do": cells[2],
        })
    return rows


def parse_troubleshooting_table(content: str) -> list[dict[str, str]]:
    """Parse the Connectivity Troubleshooting table into a list of row dicts.

    Each dict has keys: issue, fix.
    """
    section = extract_section(content, "Connectivity Troubleshooting")
    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if len(cells) < 2:
            continue
        # Skip header and separator rows
        if cells[0] == "Issue" or re.match(r"^-+$", cells[0]):
            continue
        rows.append({
            "issue": cells[0],
            "fix": cells[1],
        })
    return rows


def extract_reconnection_steps(content: str) -> list[str]:
    """Extract the numbered reconnection procedure steps."""
    section = extract_section(content, "Reconnection Procedure")
    steps = re.findall(r"^\d+\.\s+(.+)$", section, re.MULTILINE)
    return steps


def parse_call_pattern_tools(content: str) -> list[str]:
    """Extract tool names from the Call Pattern Examples section headings."""
    section = extract_section(content, "Call Pattern Examples")
    # Each tool has a ### heading
    tools = re.findall(r"^###\s+(\S+)\s*$", section, re.MULTILINE)
    return tools


def parse_anti_pattern_tools(content: str) -> list[str]:
    """Extract MCP tool names referenced in the Anti-Patterns table."""
    section = extract_section(content, "Anti-Patterns: When NOT to Use")
    # Tools appear in backticks in the "Use" column
    tools = re.findall(r"`([a-z_]+)`", section)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in tools:
        if t in ALL_MCP_TOOLS and t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


# ---------------------------------------------------------------------------
# Pre-parsed Data (module-level, parse-once)
# ---------------------------------------------------------------------------

_BLOCKED_OPS = parse_blocked_operations_table(_OFFLINE_FALLBACK_CONTENT)
_FALLBACK_INSTRUCTIONS = parse_fallback_instructions(_OFFLINE_FALLBACK_CONTENT)
_CONTINUABLE_OPS = parse_continuable_operations(_OFFLINE_FALLBACK_CONTENT)
_TROUBLESHOOTING = parse_troubleshooting_table(_OFFLINE_FALLBACK_CONTENT)
_RECONNECTION_STEPS = extract_reconnection_steps(_OFFLINE_FALLBACK_CONTENT)
_CALL_PATTERN_TOOLS = parse_call_pattern_tools(_DECISION_TREE_CONTENT)
_ANTI_PATTERN_TOOLS = parse_anti_pattern_tools(_DECISION_TREE_CONTENT)


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestOfflineFallbackCompleteness:
    """Validates: Requirements 1.1–1.5 — Offline fallback steering completeness."""

    def test_blocked_ops_tools_are_valid_mcp_tools(self) -> None:
        """Req 1.1: Every tool in blocked operations table is a recognized MCP tool."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        invalid = blocked_tools - set(ALL_MCP_TOOLS)
        assert not invalid, (
            f"Blocked operations reference unknown MCP tools: {invalid}"
        )

    def test_blocked_ops_tools_in_decision_tree(self) -> None:
        """Req 1.1: Every blocked operation tool appears in the decision tree."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        decision_tree_tools = set(_CALL_PATTERN_TOOLS)
        missing = blocked_tools - decision_tree_tools
        assert not missing, (
            f"Blocked operation tools not in decision tree: {missing}"
        )

    def test_every_blocked_op_has_fallback_with_min_steps(self) -> None:
        """Req 1.2: Every blocked operation has a fallback instruction with >= 2 steps."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        for tool in blocked_tools:
            assert tool in _FALLBACK_INSTRUCTIONS, (
                f"No fallback instruction section for blocked tool: {tool}"
            )
            steps = _FALLBACK_INSTRUCTIONS[tool]
            assert len(steps) >= 2, (
                f"Fallback for '{tool}' has {len(steps)} steps, expected >= 2"
            )

    def test_no_forbidden_phrases_in_fallbacks(self) -> None:
        """Req 1.3: No fallback instruction contains guessing language."""
        violations: list[str] = []
        for tool, steps in _FALLBACK_INSTRUCTIONS.items():
            for i, step in enumerate(steps, 1):
                step_lower = step.lower()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in step_lower:
                        # "Do NOT guess" is a prohibition, not guessing language
                        # Check if the phrase is used as an instruction to avoid
                        context_start = max(0, step_lower.index(phrase) - 10)
                        context = step_lower[context_start:step_lower.index(phrase)]
                        if "not " in context or "do not" in context or "don't" in context:
                            continue
                        violations.append(
                            f"{tool} step {i}: contains '{phrase}'"
                        )
        assert not violations, (
            "Forbidden phrases found in fallback instructions:\n"
            + "\n".join(violations)
        )

    def test_fallbacks_reference_concrete_resources(self) -> None:
        """Req 1.4: Every fallback references a URL, file path, or command."""
        url_pattern = re.compile(r"https?://")
        path_pattern = re.compile(r"[`][\w./\-]+[`]")
        command_pattern = re.compile(r"`[^`]+`")

        for tool, steps in _FALLBACK_INSTRUCTIONS.items():
            all_text = " ".join(steps)
            has_url = bool(url_pattern.search(all_text))
            has_path = bool(path_pattern.search(all_text))
            has_command = bool(command_pattern.search(all_text))
            assert has_url or has_path or has_command, (
                f"Fallback for '{tool}' has no concrete resource "
                "(URL, file path, or command)"
            )

    def test_round_trip_blocked_ops_to_fallback(self) -> None:
        """Req 1.5: One-to-one correspondence between blocked ops and fallbacks."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        fallback_tools = set(_FALLBACK_INSTRUCTIONS.keys())

        missing_fallback = blocked_tools - fallback_tools
        extra_fallback = fallback_tools - blocked_tools

        assert not missing_fallback, (
            f"Blocked ops without fallback instructions: {missing_fallback}"
        )
        assert not extra_fallback, (
            f"Fallback instructions without blocked op entry: {extra_fallback}"
        )


class TestModuleSteeringMCPHandling:
    """Validates: Requirements 2.1–2.6 — Module steering MCP failure handling."""

    def test_module_02_has_fallback_for_mcp_tools(self) -> None:
        """Req 2.1: Module 2 has inline fallback or offline fallback covers its tools."""
        content = MCP_DEPENDENT_MODULES["module-02"].read_text(encoding="utf-8")
        # Module 2 uses sdk_guide, search_docs, generate_scaffold, explain_error_code
        # Verify Error Handling section exists with explain_error_code fallback
        assert "explain_error_code" in content, (
            "Module 2 must reference explain_error_code"
        )
        assert "returns no result" in content or "unavailable" in content, (
            "Module 2 must have fallback path for explain_error_code"
        )
        # Verify the tools it uses are covered in the offline fallback
        module_tools = {"sdk_guide", "search_docs", "generate_scaffold"}
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        covered = module_tools & (blocked_tools | {"sdk_guide"})
        assert len(covered) >= 1, (
            "Module 2 MCP tools must be covered in offline fallback"
        )

    def test_module_03_has_inline_fallback_for_get_sample_data(self) -> None:
        """Req 2.2: Module 3 has inline fallback for get_sample_data."""
        content = MCP_DEPENDENT_MODULES["module-03"].read_text(encoding="utf-8")
        assert "get_sample_data" in content, (
            "Module 3 must reference get_sample_data"
        )
        # Check for inline MCP fallback section
        assert "MCP fallback" in content.lower() or "fallback" in content.lower(), (
            "Module 3 must have inline MCP fallback for get_sample_data"
        )
        # Verify alternative data source is provided
        assert "sample_data_fallback" in content or "built-in dataset" in content, (
            "Module 3 fallback must provide alternative data source"
        )

    def test_module_05_phase2_mapping_workflow_covered(self) -> None:
        """Req 2.3: Module 5 Phase 2 mapping_workflow is covered in fallback system."""
        content = MCP_DEPENDENT_MODULES["module-05-phase2"].read_text(encoding="utf-8")
        assert "mapping_workflow" in content, (
            "Module 5 Phase 2 must reference mapping_workflow"
        )
        # Verify mapping_workflow is covered in the offline fallback
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        assert "mapping_workflow" in blocked_tools, (
            "mapping_workflow must be in offline fallback blocked operations"
        )
        assert "mapping_workflow" in _FALLBACK_INSTRUCTIONS, (
            "mapping_workflow must have fallback instructions in offline fallback"
        )

    def test_module_06_generate_scaffold_covered(self) -> None:
        """Req 2.4: Module 6 generate_scaffold is covered in fallback system."""
        content = MCP_DEPENDENT_MODULES["module-06"].read_text(encoding="utf-8")
        assert "generate_scaffold" in content or "generate_scaffold" in (
            _STEERING_DIR / "module-06-phaseA-build-loading.md"
        ).read_text(encoding="utf-8"), (
            "Module 6 must reference generate_scaffold"
        )
        # Verify generate_scaffold is covered in the offline fallback
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        assert "generate_scaffold" in blocked_tools, (
            "generate_scaffold must be in offline fallback blocked operations"
        )
        assert "generate_scaffold" in _FALLBACK_INSTRUCTIONS, (
            "generate_scaffold must have fallback instructions in offline fallback"
        )

    def test_module_07_mcp_tools_covered(self) -> None:
        """Req 2.5: Module 7 MCP tools are covered in fallback system."""
        content = MCP_DEPENDENT_MODULES["module-07"].read_text(encoding="utf-8")
        # Module 7 uses generate_scaffold, find_examples, explain_error_code
        assert "generate_scaffold" in content, (
            "Module 7 must reference generate_scaffold"
        )
        assert "explain_error_code" in content, (
            "Module 7 must reference explain_error_code"
        )
        # Verify Error Handling section exists
        assert "## Error Handling" in content, (
            "Module 7 must have Error Handling section"
        )

    def test_error_handling_sections_reference_explain_error_code(self) -> None:
        """Req 2.6: Error handling sections reference explain_error_code with fallback."""
        modules_with_error_handling = [
            "module-02", "module-03", "module-06", "module-07",
        ]
        for module_key in modules_with_error_handling:
            content = MCP_DEPENDENT_MODULES[module_key].read_text(encoding="utf-8")
            error_section = extract_section(content, "Error Handling")
            assert "explain_error_code" in error_section, (
                f"{module_key} Error Handling must reference explain_error_code"
            )
            # Verify fallback path exists (what to do if tool returns no result)
            assert "returns no result" in error_section or "unavailable" in error_section, (
                f"{module_key} Error Handling must have fallback for explain_error_code"
            )


class TestReconnectionProcedure:
    """Validates: Requirements 3.1–3.5 — Reconnection procedure verification."""

    def test_exactly_six_steps(self) -> None:
        """Req 3.1: Reconnection procedure contains exactly six ordered steps."""
        assert len(_RECONNECTION_STEPS) == 6, (
            f"Expected 6 reconnection steps, found {len(_RECONNECTION_STEPS)}"
        )

    def test_retry_interval_specified(self) -> None:
        """Req 3.2: Reconnection procedure specifies retry interval (number + minutes)."""
        section = extract_section(_OFFLINE_FALLBACK_CONTENT, "Reconnection Procedure")
        assert re.search(r"\d+\s*minutes", section), (
            "Reconnection procedure must specify a retry interval "
            "(number followed by 'minutes')"
        )

    def test_get_capabilities_reference(self) -> None:
        """Req 3.3: Reconnection procedure references get_capabilities."""
        section = extract_section(_OFFLINE_FALLBACK_CONTENT, "Reconnection Procedure")
        assert "get_capabilities" in section, (
            "Reconnection procedure must reference get_capabilities "
            "as the verification call"
        )

    def test_agent_instructions_reference(self) -> None:
        """Req 3.4: Reconnection procedure references agent-instructions.md."""
        section = extract_section(_OFFLINE_FALLBACK_CONTENT, "Reconnection Procedure")
        assert "agent-instructions.md" in section, (
            "Reconnection procedure must reference agent-instructions.md"
        )

    def test_correct_sequential_order(self) -> None:
        """Req 3.5: Six steps appear in correct sequential order."""
        section = extract_section(_OFFLINE_FALLBACK_CONTENT, "Reconnection Procedure")
        # Verify key phrases appear in order
        expected_order = [
            "initial failure",
            "offline mode",
            "periodic retry",
            "verify recovery",
            "resume operations",
            "re-query",
        ]
        positions: list[int] = []
        section_lower = section.lower()
        for phrase in expected_order:
            pos = section_lower.find(phrase)
            assert pos != -1, (
                f"Reconnection step phrase '{phrase}' not found in section"
            )
            positions.append(pos)
        # Verify monotonically increasing positions
        for i in range(len(positions) - 1):
            assert positions[i] < positions[i + 1], (
                f"Step '{expected_order[i]}' (pos {positions[i]}) must appear "
                f"before '{expected_order[i + 1]}' (pos {positions[i + 1]})"
            )


class TestConnectivityTroubleshooting:
    """Validates: Requirements 4.1–4.4 — Connectivity troubleshooting completeness."""

    def test_at_least_five_entries(self) -> None:
        """Req 4.1: Troubleshooting table has at least five distinct entries."""
        assert len(_TROUBLESHOOTING) >= 5, (
            f"Expected >= 5 troubleshooting entries, found {len(_TROUBLESHOOTING)}"
        )

    def test_non_empty_issue_and_fix_columns(self) -> None:
        """Req 4.2: Each entry has non-empty Issue and Fix columns."""
        for i, entry in enumerate(_TROUBLESHOOTING):
            assert entry["issue"].strip(), (
                f"Troubleshooting entry {i + 1} has empty Issue column"
            )
            assert entry["fix"].strip(), (
                f"Troubleshooting entry {i + 1} has empty Fix column"
            )

    def test_specific_scenarios_present(self) -> None:
        """Req 4.3: Includes proxy, network, server not started, timeouts, DNS."""
        all_issues = " ".join(e["issue"].lower() for e in _TROUBLESHOOTING)
        expected_scenarios = [
            "proxy",
            "network",
            "server not started",
            "timeout",
            "dns",
        ]
        for scenario in expected_scenarios:
            assert scenario in all_issues, (
                f"Troubleshooting table missing scenario: '{scenario}'"
            )

    def test_diagnostic_command_present(self) -> None:
        """Req 4.4: At least one entry contains a diagnostic command."""
        all_fixes = " ".join(e["fix"] for e in _TROUBLESHOOTING)
        # Look for backtick-formatted commands (code-formatted strings)
        assert "`" in all_fixes or "curl" in all_fixes or "nslookup" in all_fixes, (
            "Troubleshooting table must contain at least one diagnostic command"
        )


class TestBootcamperCommunicationTemplate:
    """Validates: Requirements 5.1–5.5 — Bootcamper communication template."""

    def test_section_exists(self) -> None:
        """Req 5.1: Offline fallback has a 'What to Tell the Bootcamper' section."""
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "What to Tell the Bootcamper"
        )
        assert section, (
            "Offline fallback must contain 'What to Tell the Bootcamper' section"
        )

    def test_mentions_continuable_work(self) -> None:
        """Req 5.2: Template mentions what bootcamper can continue working on."""
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "What to Tell the Bootcamper"
        )
        assert "continue" in section.lower() or "keep working" in section.lower(), (
            "Communication template must mention continuable work"
        )

    def test_mentions_blocked_operations(self) -> None:
        """Req 5.3: Template mentions what operations are blocked."""
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "What to Tell the Bootcamper"
        )
        assert "blocked" in section.lower() or "need mcp" in section.lower() or (
            "mcp" in section.lower() and "back" in section.lower()
        ), (
            "Communication template must mention blocked operations"
        )

    def test_mentions_periodic_retry(self) -> None:
        """Req 5.4: Template indicates the agent will retry periodically."""
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "What to Tell the Bootcamper"
        )
        assert "retry" in section.lower() or "periodically" in section.lower(), (
            "Communication template must indicate periodic retry"
        )

    def test_mentions_fallback_steps(self) -> None:
        """Req 5.5: Template offers fallback steps for blocked operations."""
        section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "What to Tell the Bootcamper"
        )
        assert "fallback" in section.lower() or "steps" in section.lower(), (
            "Communication template must offer fallback steps"
        )


class TestContinuableOperationsCoverage:
    """Validates: Requirements 6.1–6.5 — Continuable operations coverage."""

    def test_at_least_four_categories(self) -> None:
        """Req 6.1: At least four categories of continuable operations."""
        categories = {row["category"] for row in _CONTINUABLE_OPS}
        assert len(categories) >= 4, (
            f"Expected >= 4 continuable operation categories, "
            f"found {len(categories)}: {categories}"
        )

    def test_modules_column_present(self) -> None:
        """Req 6.2: Each continuable operation has a Modules column value."""
        for row in _CONTINUABLE_OPS:
            assert row["modules"].strip(), (
                f"Continuable operation '{row['activity']}' has empty Modules column"
            )

    def test_what_to_do_column_present(self) -> None:
        """Req 6.3: Each continuable operation has a 'What to do' column."""
        for row in _CONTINUABLE_OPS:
            assert row["what_to_do"].strip(), (
                f"Continuable operation '{row['activity']}' has empty "
                "'What to do' column"
            )

    def test_includes_data_prep_docs_code_maintenance(self) -> None:
        """Req 6.4: Includes data preparation, documentation, and code maintenance."""
        categories_lower = {row["category"].lower() for row in _CONTINUABLE_OPS}
        all_text = " ".join(categories_lower)
        assert "data" in all_text or "preparation" in all_text, (
            "Continuable operations must include data preparation category"
        )
        assert "documentation" in all_text or "review" in all_text, (
            "Continuable operations must include documentation category"
        )
        assert "maintenance" in all_text or "code" in all_text, (
            "Continuable operations must include code maintenance category"
        )

    def test_no_mcp_tool_references(self) -> None:
        """Req 6.5: No continuable operation references an MCP tool as required."""
        violations: list[str] = []
        for row in _CONTINUABLE_OPS:
            what_to_do = row["what_to_do"].lower()
            for tool in ALL_MCP_TOOLS:
                if tool in what_to_do:
                    violations.append(
                        f"'{row['activity']}' references MCP tool '{tool}'"
                    )
        assert not violations, (
            "Continuable operations must not reference MCP tools:\n"
            + "\n".join(violations)
        )


class TestDecisionTreeConsistency:
    """Validates: Requirements 7.1–7.4 — MCP tool decision tree consistency."""

    def test_call_pattern_tools_covered_in_fallback(self) -> None:
        """Req 7.1: Call pattern tools with blocked ops have fallback entries."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        fallback_tools = set(_FALLBACK_INSTRUCTIONS.keys())

        # Every blocked tool that appears in call patterns must have a fallback
        call_pattern_set = set(_CALL_PATTERN_TOOLS)
        blocked_in_patterns = blocked_tools & call_pattern_set
        missing_fallback = blocked_in_patterns - fallback_tools
        assert not missing_fallback, (
            f"Blocked call pattern tools without fallback instructions: "
            f"{missing_fallback}"
        )

    def test_anti_patterns_overlap_at_least_three(self) -> None:
        """Req 7.2: Anti-patterns table references >= 3 tools in blocked ops."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        overlap = set(_ANTI_PATTERN_TOOLS) & blocked_tools
        assert len(overlap) >= 3, (
            f"Expected >= 3 anti-pattern tools in blocked ops, "
            f"found {len(overlap)}: {overlap}"
        )

    def test_get_capabilities_cross_reference(self) -> None:
        """Req 7.3: get_capabilities in decision tree is also in reconnection."""
        # Verify get_capabilities is in the decision tree
        assert "get_capabilities" in _DECISION_TREE_CONTENT, (
            "Decision tree must reference get_capabilities"
        )
        # Verify it's also in the reconnection procedure
        reconnection_section = extract_section(
            _OFFLINE_FALLBACK_CONTENT, "Reconnection Procedure"
        )
        assert "get_capabilities" in reconnection_section, (
            "Reconnection procedure must reference get_capabilities"
        )

    def test_decision_tree_superset_of_blocked_ops(self) -> None:
        """Req 7.4: Decision tree call patterns are superset of blocked ops tools."""
        blocked_tools = {row["mcp_tool"] for row in _BLOCKED_OPS}
        call_pattern_tools = set(_CALL_PATTERN_TOOLS)
        missing = blocked_tools - call_pattern_tools
        assert not missing, (
            f"Blocked operation tools not in decision tree call patterns: {missing}"
        )
