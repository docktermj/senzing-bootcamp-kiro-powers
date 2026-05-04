"""Tests for the MCP tool decision tree steering file.

Validates file structure, tool coverage, anti-pattern entries, call-pattern
examples, steering index registration, and agent-instructions cross-reference.

Correctness Properties (from requirements.md):
  1.1, 1.2 — File exists with correct frontmatter
  2.1 — All 12 MCP tools covered
  4.1–4.7 — Anti-pattern entries present
  5.1 — Call-pattern examples for each tool
  6.1, 6.2 — Steering index registration
  7.1 — Agent instructions cross-reference
  8.4 — Token count under split threshold
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_DECISION_TREE_PATH = _BOOTCAMP_DIR / "steering" / "mcp-tool-decision-tree.md"
_STEERING_INDEX_PATH = _BOOTCAMP_DIR / "steering" / "steering-index.yaml"
_AGENT_INSTRUCTIONS_PATH = _BOOTCAMP_DIR / "steering" / "agent-instructions.md"

_ALL_TOOLS = [
    "get_capabilities",
    "mapping_workflow",
    "generate_scaffold",
    "get_sample_data",
    "search_docs",
    "explain_error_code",
    "analyze_record",
    "sdk_guide",
    "find_examples",
    "get_sdk_reference",
    "reporting_guide",
    "download_resource",
]


def _read_decision_tree() -> str:
    """Return the full text of the decision tree file."""
    return _DECISION_TREE_PATH.read_text(encoding="utf-8")


def _read_steering_index() -> str:
    """Return the full text of the steering index."""
    return _STEERING_INDEX_PATH.read_text(encoding="utf-8")


def _read_agent_instructions() -> str:
    """Return the full text of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File Structure Tests
# Validates: Requirements 1.1, 1.2, 8.4
# ---------------------------------------------------------------------------


class TestFileStructure:
    """File exists with correct frontmatter and stays under token budget."""

    def test_file_exists(self) -> None:
        """Decision tree file must exist at the expected path."""
        assert _DECISION_TREE_PATH.exists(), (
            f"Expected file at {_DECISION_TREE_PATH.relative_to(_BOOTCAMP_DIR)}"
        )

    def test_frontmatter_inclusion_manual(self) -> None:
        """YAML frontmatter must contain inclusion: manual."""
        text = _read_decision_tree()
        # Extract frontmatter between --- delimiters
        match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        assert match, "File must start with YAML frontmatter (--- delimiters)"
        frontmatter = match.group(1)
        assert "inclusion: manual" in frontmatter, (
            "Frontmatter must contain 'inclusion: manual'"
        )

    def test_token_count_under_split_threshold(self) -> None:
        """File must be under 5000 tokens (split threshold).

        Approximation: 1 token ≈ 4 characters for English text.
        The actual measured count is ~1275, so even a generous estimate
        should be well under 5000.
        """
        text = _read_decision_tree()
        # Conservative estimate: 1 token per 3 characters
        estimated_tokens = len(text) // 3
        assert estimated_tokens < 5000, (
            f"Estimated token count ({estimated_tokens}) exceeds 5000 split threshold"
        )


# ---------------------------------------------------------------------------
# Tool Coverage Tests
# Validates: Requirement 2.1
# ---------------------------------------------------------------------------


class TestToolCoverage:
    """All 12 MCP tools must appear in at least one decision node path."""

    def test_all_12_tools_present(self) -> None:
        """Every MCP tool name must appear in the decision tree file."""
        text = _read_decision_tree()
        missing = [tool for tool in _ALL_TOOLS if tool not in text]
        assert not missing, (
            f"Missing tools in decision tree: {missing}"
        )


# ---------------------------------------------------------------------------
# Anti-Pattern Tests
# Validates: Requirements 4.1–4.7
# ---------------------------------------------------------------------------


class TestAntiPatterns:
    """Anti-pattern entries present for all six required scenarios."""

    def test_hand_coding_anti_pattern(self) -> None:
        """Must warn against hand-coding Senzing JSON mappings."""
        text = _read_decision_tree().lower()
        assert "hand-cod" in text, (
            "Missing anti-pattern for hand-coding JSON mappings"
        )

    def test_guessing_sdk_anti_pattern(self) -> None:
        """Must warn against guessing SDK method names."""
        text = _read_decision_tree().lower()
        assert "guessing sdk" in text, (
            "Missing anti-pattern for guessing SDK method names"
        )

    def test_training_data_anti_pattern(self) -> None:
        """Must warn against relying on training data for signatures."""
        text = _read_decision_tree().lower()
        assert "training data" in text, (
            "Missing anti-pattern for relying on training data"
        )

    def test_anti_patterns_category_mentioned(self) -> None:
        """Must mention search_docs with category anti_patterns."""
        text = _read_decision_tree()
        assert "anti_patterns" in text, (
            "Missing reference to search_docs category='anti_patterns'"
        )

    def test_guessing_error_code_anti_pattern(self) -> None:
        """Must warn against guessing error code meanings."""
        text = _read_decision_tree().lower()
        assert re.search(r"guessing.*error", text), (
            "Missing anti-pattern for guessing error code meanings"
        )

    def test_fabricating_data_anti_pattern(self) -> None:
        """Must warn against fabricating sample datasets."""
        text = _read_decision_tree().lower()
        assert "fabricat" in text, (
            "Missing anti-pattern for fabricating sample datasets"
        )


# ---------------------------------------------------------------------------
# Call Pattern Examples Tests
# Validates: Requirement 5.1
# ---------------------------------------------------------------------------


class TestCallPatternExamples:
    """Each of the 12 tools must have at least one code-block example."""

    def test_each_tool_has_code_block_example(self) -> None:
        """Every tool must appear inside a code block in the examples section."""
        text = _read_decision_tree()
        # Find the Call Pattern Examples section
        examples_idx = text.find("## Call Pattern Examples")
        assert examples_idx != -1, (
            "File must contain a '## Call Pattern Examples' section"
        )
        examples_section = text[examples_idx:]

        # Extract all code blocks from the examples section
        code_blocks = re.findall(r"```[^\n]*\n(.*?)```", examples_section, re.DOTALL)
        code_text = "\n".join(code_blocks)

        missing = [tool for tool in _ALL_TOOLS if tool not in code_text]
        assert not missing, (
            f"Tools missing from code-block examples: {missing}"
        )


# ---------------------------------------------------------------------------
# Steering Index Registration Tests
# Validates: Requirements 6.1, 6.2
# ---------------------------------------------------------------------------


class TestSteeringIndex:
    """Decision tree registered in steering-index.yaml metadata and keywords."""

    def test_file_metadata_entry_exists(self) -> None:
        """steering-index.yaml must contain mcp-tool-decision-tree.md in file_metadata."""
        text = _read_steering_index()
        # Check it appears in the file_metadata section
        metadata_idx = text.find("file_metadata:")
        assert metadata_idx != -1, "steering-index.yaml must have file_metadata section"
        metadata_section = text[metadata_idx:]
        assert "mcp-tool-decision-tree.md" in metadata_section, (
            "mcp-tool-decision-tree.md not found in file_metadata section"
        )

    def test_at_least_3_keyword_entries(self) -> None:
        """steering-index.yaml must have at least 3 keywords pointing to the file."""
        text = _read_steering_index()
        # Find keywords section (between "keywords:" and the next top-level key)
        keywords_match = re.search(
            r"^keywords:\s*\n(.*?)(?=^\w)", text, re.MULTILINE | re.DOTALL
        )
        assert keywords_match, "steering-index.yaml must have keywords section"
        keywords_section = keywords_match.group(1)
        count = keywords_section.count("mcp-tool-decision-tree.md")
        assert count >= 3, (
            f"Expected >= 3 keyword entries for mcp-tool-decision-tree.md, found {count}"
        )


# ---------------------------------------------------------------------------
# Agent Instructions Cross-Reference Tests
# Validates: Requirement 7.1
# ---------------------------------------------------------------------------


class TestAgentInstructionsCrossReference:
    """agent-instructions.md must reference the decision tree file."""

    def test_contains_reference(self) -> None:
        """agent-instructions.md must mention mcp-tool-decision-tree.md."""
        text = _read_agent_instructions()
        assert "mcp-tool-decision-tree.md" in text, (
            "agent-instructions.md must reference mcp-tool-decision-tree.md"
        )
