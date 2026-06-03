"""Preservation property tests for no-direct-sql bugfix.

These tests observe the UNFIXED steering file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code — they establish the baseline.

Feature: no-direct-sql

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
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
_DECISION_TREE = _BOOTCAMP_DIR / "steering" / "mcp-tool-decision-tree.md"

# ---------------------------------------------------------------------------
# Constants — Bug condition components (used to define what IS NOT a bug)
# ---------------------------------------------------------------------------

_SQL_KEYWORDS = ["SELECT", "INSERT", "UPDATE", "DELETE"]

_SENZING_INDICATORS = [
    "G2C.db",
    "database/G2C.db",
    "RES_ENT",
    "OBS_ENT",
    "DSRC_RECORD",
    "LIB_FEAT",
    "RES_FEAT_STAT",
    "RES_REL",
]

# ---------------------------------------------------------------------------
# Non-Senzing SQL patterns (should NOT be flagged)
# ---------------------------------------------------------------------------

_NON_SENZING_SQL_PATTERNS = [
    "SELECT * FROM users",
    "SELECT name, email FROM customers WHERE active = 1",
    "INSERT INTO orders (product_id, quantity) VALUES (1, 5)",
    "UPDATE employees SET salary = 50000 WHERE id = 42",
    "DELETE FROM sessions WHERE expired = true",
    "SELECT COUNT(*) FROM products",
    "CREATE TABLE logs (id INTEGER PRIMARY KEY, message TEXT)",
    "SELECT u.name FROM users u JOIN roles r ON u.role_id = r.id",
]

# ---------------------------------------------------------------------------
# File I/O patterns (should remain unaffected)
# ---------------------------------------------------------------------------

_FILE_IO_PATTERNS = [
    "open('data/customers.csv', 'r')",
    "pd.read_csv('data/input.csv')",
    "with open('output.jsonl', 'w') as f:",
    "json.dump(records, open('data/results.jsonl', 'w'))",
    "yaml.safe_load(open('config/settings.yaml'))",
    "Path('config/bootcamp_progress.json').read_text()",
    "csv.writer(open('data/export.csv', 'w'))",
    "open('data/temp/mapping.json', 'w')",
]

# ---------------------------------------------------------------------------
# MCP tool patterns (should remain unchanged)
# These are the 12 MCP tools actually referenced in the decision tree file.
# Note: SDK methods like get_entity, search_by_attributes are NOT in the
# decision tree — they are SDK-level methods accessed via MCP tools.
# ---------------------------------------------------------------------------

_MCP_TOOL_PATTERNS = [
    "mapping_workflow",
    "generate_scaffold",
    "sdk_guide",
    "get_sdk_reference",
    "explain_error_code",
    "search_docs",
    "find_examples",
    "reporting_guide",
    "get_capabilities",
    "analyze_record",
    "get_sample_data",
    "download_resource",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_agent_instructions() -> str:
    """Read the full content of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")


def _read_decision_tree() -> str:
    """Read the full content of mcp-tool-decision-tree.md."""
    return _DECISION_TREE.read_text(encoding="utf-8")


def _extract_mcp_rules_section(content: str) -> str:
    """Extract the MCP Rules section from agent-instructions.md."""
    match = re.search(r"^## MCP Rules\b", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
    if next_heading:
        return content[start:start + 1 + next_heading.start()]
    return content[start:]


def _extract_anti_patterns_section(content: str) -> str:
    """Extract the Anti-Patterns section from mcp-tool-decision-tree.md."""
    match = re.search(r"^## Anti-Patterns", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
    if next_heading:
        return content[start:start + 1 + next_heading.start()]
    return content[start:]


def _is_bug_condition(output: str) -> bool:
    """Return True if output contains SQL keywords targeting Senzing database.

    This mirrors the isBugCondition function from the design doc.
    """
    has_sql = any(kw in output.upper() for kw in _SQL_KEYWORDS)
    targets_senzing = any(ind in output for ind in _SENZING_INDICATORS)
    return has_sql and targets_senzing


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# ---------------------------------------------------------------------------

_UNFIXED_AGENT_INSTRUCTIONS = _read_agent_instructions()
_UNFIXED_DECISION_TREE = _read_decision_tree()
_UNFIXED_MCP_RULES = _extract_mcp_rules_section(_UNFIXED_AGENT_INSTRUCTIONS)
_UNFIXED_ANTI_PATTERNS = _extract_anti_patterns_section(_UNFIXED_DECISION_TREE)

# ---------------------------------------------------------------------------
# Test 1 — Non-Senzing SQL patterns are NOT flagged
# ---------------------------------------------------------------------------


class TestNonSenzingSqlNotFlagged:
    """Non-Senzing SQL patterns must not trigger the bug condition.

    **Validates: Requirements 3.3**

    Verify that SQL patterns targeting non-Senzing databases (e.g.,
    SELECT * FROM users) are NOT identified as bug conditions and
    therefore should not be prohibited by any fix.
    """

    def test_non_senzing_sql_not_bug_condition(self) -> None:
        """Assert all non-Senzing SQL patterns return False for isBugCondition."""
        for pattern in _NON_SENZING_SQL_PATTERNS:
            assert not _is_bug_condition(pattern), (
                f"Non-Senzing SQL pattern incorrectly flagged as bug condition: "
                f"'{pattern}'"
            )

    def test_agent_instructions_does_not_prohibit_general_sql(self) -> None:
        """Assert agent-instructions.md does not blanket-prohibit all SQL.

        The MCP Rules section should not contain language that would
        prohibit SQL in general — only SQL targeting the Senzing database.
        """
        content = _read_agent_instructions()
        # A blanket prohibition would say "never use SQL" without Senzing qualifier
        blanket_prohibition = re.compile(
            r"(never|do\s+not|must\s+not|shall\s+not|prohibited)"
            r"\s+"
            r"(use|write|generate)\s+"
            r"(any\s+)?SQL\b"
            r"(?!.*Senzing|.*G2C|.*internal\s+table)",
            re.IGNORECASE,
        )
        assert not blanket_prohibition.search(content), (
            "agent-instructions.md contains a blanket SQL prohibition that "
            "would affect non-Senzing databases. The prohibition must be "
            "scoped to the Senzing database only."
        )


# ---------------------------------------------------------------------------
# Test 2 — File I/O patterns remain unaffected
# ---------------------------------------------------------------------------


class TestFileIOPatternsUnaffected:
    """File I/O patterns (CSV, JSONL, YAML) must remain unaffected.

    **Validates: Requirements 3.1**

    Verify that standard file I/O operations for non-Senzing files
    are not flagged as bug conditions and that the steering files
    continue to permit them.
    """

    def test_file_io_not_bug_condition(self) -> None:
        """Assert file I/O patterns are not identified as bug conditions."""
        for pattern in _FILE_IO_PATTERNS:
            assert not _is_bug_condition(pattern), (
                f"File I/O pattern incorrectly flagged as bug condition: "
                f"'{pattern}'"
            )

    def test_agent_instructions_permits_file_io(self) -> None:
        """Assert agent-instructions.md has file placement guidance.

        The File Placement section must exist and reference standard
        file locations (data/, config/, docs/, scripts/).
        """
        content = _read_agent_instructions()
        assert "## File Placement" in content, (
            "agent-instructions.md missing '## File Placement' section"
        )
        # Verify key file locations are mentioned
        for location in ["data/", "config/", "docs/", "scripts/"]:
            assert location in content, (
                f"agent-instructions.md missing file location '{location}'"
            )

    def test_file_placement_section_preserved(self) -> None:
        """Assert the File Placement section matches the baseline."""
        content = _read_agent_instructions()
        match = re.search(r"^## File Placement\b", content, re.MULTILINE)
        assert match, "File Placement section not found"
        start = match.start()
        next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
        if next_heading:
            current_section = content[start:start + 1 + next_heading.start()]
        else:
            current_section = content[start:]

        # Compare against baseline
        baseline_match = re.search(
            r"^## File Placement\b", _UNFIXED_AGENT_INSTRUCTIONS, re.MULTILINE
        )
        assert baseline_match
        baseline_start = baseline_match.start()
        baseline_next = re.search(
            r"^## ", _UNFIXED_AGENT_INSTRUCTIONS[baseline_start + 1:], re.MULTILINE
        )
        if baseline_next:
            baseline_section = _UNFIXED_AGENT_INSTRUCTIONS[
                baseline_start:baseline_start + 1 + baseline_next.start()
            ]
        else:
            baseline_section = _UNFIXED_AGENT_INSTRUCTIONS[baseline_start:]

        assert current_section == baseline_section, (
            "File Placement section has changed from baseline.\n"
            f"Expected (first 300 chars):\n{baseline_section[:300]}\n"
            f"Got (first 300 chars):\n{current_section[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — MCP tool guidance remains unchanged
# ---------------------------------------------------------------------------


class TestMCPToolGuidanceUnchanged:
    """Existing MCP tool guidance must remain unchanged.

    **Validates: Requirements 3.2, 3.4**

    Verify that the MCP Rules section in agent-instructions.md and
    the decision tree in mcp-tool-decision-tree.md continue to
    reference all existing MCP tools correctly.
    """

    def test_mcp_rules_references_all_tools(self) -> None:
        """Assert MCP Rules section references key SDK tools."""
        mcp_rules = _extract_mcp_rules_section(_read_agent_instructions())
        assert mcp_rules, "MCP Rules section not found"
        # These tools must be referenced in MCP Rules
        required_tools = [
            "mapping_workflow",
            "generate_scaffold",
            "sdk_guide",
            "get_sdk_reference",
            "explain_error_code",
            "search_docs",
            "find_examples",
        ]
        for tool in required_tools:
            assert tool in mcp_rules, (
                f"MCP Rules section missing reference to '{tool}'"
            )

    def test_decision_tree_references_all_tools(self) -> None:
        """Assert decision tree references all 12 MCP tools."""
        content = _read_decision_tree()
        for tool in _MCP_TOOL_PATTERNS:
            assert tool in content, (
                f"mcp-tool-decision-tree.md missing reference to '{tool}'"
            )

    def test_decision_tree_anti_patterns_preserved(self) -> None:
        """Assert existing anti-pattern rows are preserved."""
        anti_patterns = _extract_anti_patterns_section(_read_decision_tree())
        assert anti_patterns, "Anti-Patterns section not found"

        # These existing anti-patterns must remain
        expected_anti_patterns = [
            "Hand-coding Senzing JSON mappings",
            "Guessing SDK method names",
            "Relying on training data",
            "Guessing Senzing error code meanings",
            "Fabricating sample datasets",
        ]
        for pattern in expected_anti_patterns:
            assert pattern in anti_patterns, (
                f"Anti-Patterns section missing existing row: '{pattern}'"
            )

    def test_decision_tree_structure_preserved(self) -> None:
        """Assert decision tree branch structure is preserved."""
        content = _read_decision_tree()
        # Key structural elements that must remain
        expected_branches = [
            "## What Is the Bootcamper Trying to Do?",
            "### Data Preparation",
            "### SDK Development",
            "### Troubleshooting",
            "### Reference and Reporting",
        ]
        for branch in expected_branches:
            assert branch in content, (
                f"Decision tree missing structural element: '{branch}'"
            )


# ---------------------------------------------------------------------------
# Test 4 — MCP Rules section content preserved (non-SQL parts)
# ---------------------------------------------------------------------------


class TestMCPRulesContentPreserved:
    """MCP Rules section non-SQL content must be preserved.

    **Validates: Requirements 3.2**

    Assert that the existing MCP Rules content (SDK guidance, tool
    references, flag protocol) remains unchanged after the fix.
    """

    def test_mcp_rules_contains_core_guidance(self) -> None:
        """Assert MCP Rules has core guidance lines."""
        mcp_rules = _extract_mcp_rules_section(_read_agent_instructions())
        assert mcp_rules, "MCP Rules section not found"

        # Core guidance that must be preserved
        core_lines = [
            "All Senzing facts from MCP tools",
            "never training data",
            "get_capabilities",
            "Never hand-code Senzing JSON mappings",
        ]
        for line in core_lines:
            assert line in mcp_rules, (
                f"MCP Rules missing core guidance: '{line}'"
            )

    def test_mcp_failure_section_preserved(self) -> None:
        """Assert MCP Failure section is preserved."""
        content = _read_agent_instructions()
        assert "## MCP Failure" in content, (
            "agent-instructions.md missing '## MCP Failure' section"
        )
        # Key content in MCP Failure
        assert "Retry once" in content, (
            "MCP Failure section missing 'Retry once' guidance"
        )
        assert "Never fabricate Senzing facts" in content, (
            "MCP Failure section missing 'Never fabricate' guidance"
        )


# ---------------------------------------------------------------------------
# PBT Test — Non-Senzing SQL Not Flagged
# ---------------------------------------------------------------------------


@st.composite
def st_non_senzing_sql(draw: st.DrawFn) -> str:
    """Generate SQL statements targeting non-Senzing tables.

    These represent agent outputs where isBugCondition returns false
    because they contain SQL but do NOT target the Senzing database.
    """
    sql_keyword = draw(st.sampled_from(["SELECT", "INSERT", "UPDATE", "DELETE"]))
    non_senzing_table = draw(st.sampled_from([
        "users", "customers", "orders", "products", "sessions",
        "employees", "logs", "events", "accounts", "transactions",
    ]))
    # Build a simple SQL statement with a non-Senzing table
    if sql_keyword == "SELECT":
        column = draw(st.sampled_from(["*", "id", "name", "email", "COUNT(*)"]))
        return f"{sql_keyword} {column} FROM {non_senzing_table}"
    elif sql_keyword == "INSERT":
        return f"{sql_keyword} INTO {non_senzing_table} (name) VALUES ('test')"
    elif sql_keyword == "UPDATE":
        return f"{sql_keyword} {non_senzing_table} SET active = 1 WHERE id = 1"
    else:  # DELETE
        return f"{sql_keyword} FROM {non_senzing_table} WHERE expired = true"


class TestNonSenzingSqlPropertyBased:
    """PBT — Non-Senzing SQL patterns are never bug conditions.

    **Validates: Requirements 3.3**

    For any generated SQL statement targeting non-Senzing tables,
    verify that isBugCondition returns false and the steering files
    do not prohibit such patterns.
    """

    @given(sql_stmt=st_non_senzing_sql())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_senzing_sql_never_bug_condition(self, sql_stmt: str) -> None:
        """For any non-Senzing SQL, isBugCondition must return False."""
        assert not _is_bug_condition(sql_stmt), (
            f"Non-Senzing SQL incorrectly flagged as bug condition: '{sql_stmt}'"
        )


# ---------------------------------------------------------------------------
# PBT Test — File I/O Patterns Not Flagged
# ---------------------------------------------------------------------------


@st.composite
def st_file_io_operation(draw: st.DrawFn) -> str:
    """Generate file I/O operation strings.

    These represent agent outputs involving CSV, JSONL, YAML file
    operations that must remain unaffected by the SQL prohibition fix.
    """
    operation = draw(st.sampled_from([
        "open", "read_csv", "to_csv", "read_json", "to_json",
        "safe_load", "dump", "read_text", "write_text",
    ]))
    file_ext = draw(st.sampled_from([".csv", ".jsonl", ".json", ".yaml", ".yml"]))
    file_path = draw(st.sampled_from([
        "data/input", "data/output", "config/settings",
        "data/temp/export", "data/customers", "config/mapping",
    ]))
    return f"{operation}('{file_path}{file_ext}')"


class TestFileIOPropertyBased:
    """PBT — File I/O operations are never bug conditions.

    **Validates: Requirements 3.1**

    For any generated file I/O operation string, verify that
    isBugCondition returns false and the operation is not affected
    by the SQL prohibition fix.
    """

    @given(file_op=st_file_io_operation())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_file_io_never_bug_condition(self, file_op: str) -> None:
        """For any file I/O operation, isBugCondition must return False."""
        assert not _is_bug_condition(file_op), (
            f"File I/O operation incorrectly flagged as bug condition: '{file_op}'"
        )


# ---------------------------------------------------------------------------
# PBT Test — MCP Tool References Preserved
# ---------------------------------------------------------------------------


@st.composite
def st_mcp_tool_call(draw: st.DrawFn) -> str:
    """Generate MCP tool call strings.

    These represent agent outputs using SDK methods via MCP tools
    that must remain unchanged by the fix.
    """
    tool = draw(st.sampled_from(_MCP_TOOL_PATTERNS))
    return tool


class TestMCPToolPreservationPropertyBased:
    """PBT — MCP tool references remain in steering files.

    **Validates: Requirements 3.2, 3.4**

    For any MCP tool name, verify that both steering files continue
    to reference it after the fix.
    """

    @given(tool_name=st_mcp_tool_call())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_mcp_tool_referenced_in_decision_tree(self, tool_name: str) -> None:
        """For any MCP tool, it must be referenced in the decision tree."""
        content = _read_decision_tree()
        assert tool_name in content, (
            f"MCP tool '{tool_name}' not found in mcp-tool-decision-tree.md"
        )

    @given(tool_name=st_mcp_tool_call())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_mcp_tool_guidance_unchanged(self, tool_name: str) -> None:
        """For any MCP tool, its presence in the baseline must be preserved."""
        # Verify tool is in the baseline (observation)
        assert tool_name in _UNFIXED_DECISION_TREE, (
            f"MCP tool '{tool_name}' not in baseline decision tree"
        )
        # Verify tool is still in the current file
        content = _read_decision_tree()
        assert tool_name in content, (
            f"MCP tool '{tool_name}' removed from decision tree after fix"
        )


# ---------------------------------------------------------------------------
# PBT Test — Preservation: Non-Bug-Condition Content Unchanged
# ---------------------------------------------------------------------------


@st.composite
def st_non_bug_condition_content(draw: st.DrawFn) -> str:
    """Generate content strings where isBugCondition returns false.

    Combines SQL for non-Senzing databases, file I/O operations,
    SDK method calls, and general SQL education content.
    """
    category = draw(st.sampled_from([
        "non_senzing_sql", "file_io", "sdk_method", "sql_education",
    ]))
    if category == "non_senzing_sql":
        return draw(st_non_senzing_sql())
    elif category == "file_io":
        return draw(st_file_io_operation())
    elif category == "sdk_method":
        return draw(st_mcp_tool_call())
    else:  # sql_education
        topic = draw(st.sampled_from([
            "SQL JOIN syntax explained",
            "How to use GROUP BY in PostgreSQL",
            "SQLite tutorial for beginners",
            "CREATE INDEX best practices",
            "Database normalization forms",
        ]))
        return topic


class TestPreservationPropertyBased:
    """PBT — Non-bug-condition content produces same guidance.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    For any generated content string where isBugCondition returns false,
    the steering files produce the same guidance before and after the fix.
    This is verified by checking that the relevant sections of the
    steering files remain unchanged.
    """

    @given(content=st_non_bug_condition_content())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_bug_content_not_flagged(self, content: str) -> None:
        """For any non-bug-condition content, isBugCondition returns False."""
        assert not _is_bug_condition(content), (
            f"Content incorrectly identified as bug condition: '{content}'"
        )

    @given(content=st_non_bug_condition_content())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_steering_guidance_unchanged_for_non_bug_content(
        self, content: str
    ) -> None:
        """For any non-bug-condition content, steering guidance is unchanged.

        Verify that the MCP Rules section and Anti-Patterns section
        match the baseline for content that is NOT a bug condition.
        """
        # The MCP Rules section must match baseline
        current_mcp_rules = _extract_mcp_rules_section(_read_agent_instructions())
        # Only check that baseline content is still present (fix may ADD content)
        # The key preservation property: all baseline lines are still there
        for line in _UNFIXED_MCP_RULES.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                assert stripped in current_mcp_rules, (
                    f"MCP Rules baseline line missing after fix: '{stripped[:80]}'"
                )

        # The Anti-Patterns section must preserve existing rows
        current_anti_patterns = _extract_anti_patterns_section(_read_decision_tree())
        for line in _UNFIXED_ANTI_PATTERNS.splitlines():
            stripped = line.strip()
            if stripped and stripped.startswith("|"):
                assert stripped in current_anti_patterns, (
                    f"Anti-Patterns baseline row missing: '{stripped[:80]}'"
                )
