"""Bug condition exploration tests for no-direct-sql bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: no-direct-sql

**Validates: Requirements 1.1, 1.2, 1.3**
"""

from __future__ import annotations

import json
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
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "write-policy-gate.kiro.hook"

# ---------------------------------------------------------------------------
# Constants — Bug condition components
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

_SQL_PROHIBITION_PATTERNS = re.compile(
    r"(never|do\s+not|must\s+not|shall\s+not|prohibited|forbid|disallow)"
    r".*"
    r"(direct\s+SQL|SQL\s+(quer|statement|command|access)|"
    r"SELECT|INSERT|UPDATE|DELETE)",
    re.IGNORECASE,
)

_ANTI_PATTERN_SQL_ROW = re.compile(
    r"(direct\s+SQL|SQL.*Senzing|writing.*SQL.*database)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_agent_instructions() -> str:
    """Read the full content of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")


def _extract_mcp_rules_section(content: str) -> str:
    """Extract the MCP Rules section from agent-instructions.md."""
    match = re.search(r"^## MCP Rules\b", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    # Find next ## heading
    next_heading = re.search(r"^## ", content[start + 1:], re.MULTILINE)
    if next_heading:
        return content[start:start + 1 + next_heading.start()]
    return content[start:]


def _read_decision_tree() -> str:
    """Read the full content of mcp-tool-decision-tree.md."""
    return _DECISION_TREE.read_text(encoding="utf-8")


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


# ---------------------------------------------------------------------------
# Test 1 — agent-instructions.md MCP Rules lacks SQL prohibition
# ---------------------------------------------------------------------------


class TestAgentInstructionsSqlProhibition:
    """Test 1 — MCP Rules SQL Prohibition Missing.

    **Validates: Requirements 1.1, 1.2**

    Parse agent-instructions.md, extract the MCP Rules section, and assert
    it contains explicit "never generate direct SQL" prohibition language
    covering SQL keywords targeting the Senzing database.
    On unfixed content this will FAIL because no SQL prohibition exists.
    """

    def test_mcp_rules_contains_sql_prohibition(self) -> None:
        content = _read_agent_instructions()
        mcp_rules = _extract_mcp_rules_section(content)
        assert mcp_rules, "MCP Rules section not found in agent-instructions.md"
        assert _SQL_PROHIBITION_PATTERNS.search(mcp_rules), (
            "agent-instructions.md MCP Rules section has no mention of SQL "
            "prohibition. The section does not contain language prohibiting "
            "direct SQL queries against the Senzing database. "
            f"MCP Rules content:\n{mcp_rules[:800]}"
        )

    def test_mcp_rules_mentions_senzing_database_target(self) -> None:
        content = _read_agent_instructions()
        mcp_rules = _extract_mcp_rules_section(content)
        assert mcp_rules, "MCP Rules section not found in agent-instructions.md"
        # Check that the MCP Rules section mentions G2C.db or Senzing database
        # in the context of SQL prohibition
        has_senzing_db_ref = bool(
            re.search(r"(G2C\.db|Senzing\s+database|internal\s+tables)", mcp_rules, re.IGNORECASE)
        )
        assert has_senzing_db_ref, (
            "agent-instructions.md MCP Rules section does not reference the "
            "Senzing database (G2C.db) or internal tables in any prohibition "
            "context. Without this, the agent has no instruction to avoid SQL "
            "against the Senzing database specifically."
        )


# ---------------------------------------------------------------------------
# Test 2 — mcp-tool-decision-tree.md anti-patterns table lacks SQL row
# ---------------------------------------------------------------------------


class TestDecisionTreeSqlAntiPattern:
    """Test 2 — Anti-Patterns Table Missing Direct SQL Row.

    **Validates: Requirements 1.1, 1.2**

    Parse mcp-tool-decision-tree.md, extract the Anti-Patterns section,
    and assert it contains a row about direct SQL against the Senzing
    database. On unfixed content this will FAIL because no such row exists.
    """

    def test_anti_patterns_contains_sql_row(self) -> None:
        content = _read_decision_tree()
        anti_patterns = _extract_anti_patterns_section(content)
        assert anti_patterns, (
            "Anti-Patterns section not found in mcp-tool-decision-tree.md"
        )
        assert _ANTI_PATTERN_SQL_ROW.search(anti_patterns), (
            "mcp-tool-decision-tree.md anti-patterns table does not contain a "
            "row about direct SQL against the Senzing database. The table lists "
            "other anti-patterns but omits the direct SQL pattern. "
            f"Anti-patterns section:\n{anti_patterns[:800]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — block-direct-sql.kiro.hook does not exist
# ---------------------------------------------------------------------------


class TestBlockDirectSqlHookExists:
    """Test 3 — Hook File Missing.

    **Validates: Requirements 1.3**

    Assert that senzing-bootcamp/hooks/block-direct-sql.kiro.hook exists
    with valid JSON structure containing when/then fields covering SQL
    keywords and Senzing indicators. On unfixed content this will FAIL
    because the hook file does not exist.
    """

    def test_hook_file_exists(self) -> None:
        assert _HOOK_FILE.exists(), (
            f"Hook file does not exist: {_HOOK_FILE.relative_to(_BOOTCAMP_DIR)}. "
            "No preToolUse hook exists to block direct SQL writes against the "
            "Senzing database."
        )

    def test_hook_has_valid_json_structure(self) -> None:
        if not _HOOK_FILE.exists():
            raise AssertionError(
                "Hook file does not exist — cannot validate JSON structure. "
                f"Expected: {_HOOK_FILE.relative_to(_BOOTCAMP_DIR)}"
            )
        content = _HOOK_FILE.read_text(encoding="utf-8")
        try:
            hook_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"Hook file is not valid JSON: {e}"
            ) from e

        # Validate required fields
        for field in ("name", "version", "when", "then"):
            assert field in hook_data, (
                f"Hook file missing required field '{field}'. "
                f"Found keys: {list(hook_data.keys())}"
            )

    def test_hook_covers_sql_keywords_and_senzing_indicators(self) -> None:
        if not _HOOK_FILE.exists():
            raise AssertionError(
                "Hook file does not exist — cannot validate SQL coverage. "
                f"Expected: {_HOOK_FILE.relative_to(_BOOTCAMP_DIR)}"
            )
        content = _HOOK_FILE.read_text(encoding="utf-8")
        hook_data = json.loads(content)
        hook_text = json.dumps(hook_data).upper()

        # Check that hook prompt covers SQL keywords
        missing_sql = [kw for kw in _SQL_KEYWORDS if kw not in hook_text]
        assert not missing_sql, (
            f"Hook file does not cover SQL keywords: {missing_sql}. "
            "The hook must detect all SQL DML keywords."
        )

        # Check that hook references Senzing indicators
        hook_text_original = json.dumps(hook_data)
        missing_indicators = [
            ind for ind in ["G2C.db", "RES_ENT", "OBS_ENT", "DSRC_RECORD", "LIB_FEAT"]
            if ind not in hook_text_original
        ]
        assert not missing_indicators, (
            f"Hook file does not reference Senzing indicators: {missing_indicators}. "
            "The hook must identify SQL targeting the Senzing database."
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Property
# ---------------------------------------------------------------------------


@st.composite
def st_sql_with_senzing_indicator(draw: st.DrawFn) -> tuple[str, str]:
    """Generate a (sql_keyword, senzing_indicator) pair.

    These represent agent outputs that contain SQL targeting the Senzing
    database — the bug condition.
    """
    sql_keyword = draw(st.sampled_from(_SQL_KEYWORDS))
    senzing_indicator = draw(st.sampled_from(_SENZING_INDICATORS))
    return (sql_keyword, senzing_indicator)


class TestBugConditionProperty:
    """PBT Test — Bug Condition: Direct SQL Prohibition Missing.

    **Validates: Requirements 1.1, 1.2, 1.3**

    For any combination of SQL keyword and Senzing indicator (representing
    an agent output that triggers the bug condition), assert that the
    steering files contain explicit prohibition language covering that
    pattern. Will FAIL on unfixed code because no prohibition exists.
    """

    @given(pair=st_sql_with_senzing_indicator())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_steering_prohibits_sql_senzing_combination(
        self, pair: tuple[str, str]
    ) -> None:
        """For any SQL keyword + Senzing indicator pair, steering files
        must contain prohibition language covering that pattern."""
        sql_keyword, senzing_indicator = pair

        # Read steering files
        agent_content = _read_agent_instructions()
        mcp_rules = _extract_mcp_rules_section(agent_content)

        # The MCP Rules section must contain SQL prohibition language
        assert _SQL_PROHIBITION_PATTERNS.search(mcp_rules), (
            f"Bug condition: agent output with '{sql_keyword}' targeting "
            f"'{senzing_indicator}' is not prohibited. "
            "agent-instructions.md MCP Rules has no SQL prohibition language."
        )

        # The decision tree must have an anti-pattern row for SQL
        tree_content = _read_decision_tree()
        anti_patterns = _extract_anti_patterns_section(tree_content)
        assert _ANTI_PATTERN_SQL_ROW.search(anti_patterns), (
            f"Bug condition: agent output with '{sql_keyword}' targeting "
            f"'{senzing_indicator}' has no anti-pattern entry. "
            "mcp-tool-decision-tree.md omits direct SQL row."
        )

        # The hook must exist to intercept at runtime
        assert _HOOK_FILE.exists(), (
            f"Bug condition: agent output with '{sql_keyword}' targeting "
            f"'{senzing_indicator}' has no runtime guardrail. "
            "write-policy-gate.kiro.hook does not exist."
        )
