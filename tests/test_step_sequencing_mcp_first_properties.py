"""Property-based tests for step sequencing and MCP-first logic preservation.

**Property 3: Step sequencing and MCP-first logic preservation**

For any key detection phrase from the step sequencing logic (step violation output
format, sequential step enforcement) and for any Senzing content indicator from the
original mcp-first-invariant.kiro.hook (SDK method names, attribute names, config
options, ER terms, MCP tool names), those phrases SHALL appear in the consolidated
Ask_Bootcamper_Hook prompt.

Note: The transition question patterns and affirmative phrases were removed from
Phase 2B as part of the agent-answer-processing-failures spec (Requirement 3.4),
which broadened Phase 2B from MODULE TRANSITION RETRY to ANSWER PROCESSING RETRY.
The new activation uses question_pending file existence + Minimal_Output detection.

**Validates: Requirements 1.4, 1.5**
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")

# Transition patterns from enforce-step-and-transition that were removed in the
# agent-answer-processing-failures spec (Requirement 3.4). Phase 2B now uses
# question_pending file existence + Minimal_Output detection instead.
# These are kept here for documentation but no longer tested as required.
_REMOVED_TRANSITION_PATTERNS: list[str] = [
    "Ready for Module",
    "move on to Module",
    "proceed to Module",
]

# Affirmative phrases from enforce-step-and-transition that were removed in the
# agent-answer-processing-failures spec (Requirement 3.4).
_REMOVED_AFFIRMATIVE_PHRASES: list[str] = [
    "yes",
    "sure",
    "ready",
    "let's go",
    "let's do it",
    "yep",
    "yeah",
    "absolutely",
    "go ahead",
    "proceed",
    "ok",
    "okay",
    "sounds good",
    "let's",
    "do it",
    "I'm ready",
    "go for it",
]

# Answer processing retry type keywords that must appear in the prompt (Phase 2B).
ANSWER_PROCESSING_TYPES: list[str] = [
    "track_selection",
    "module_transition",
    "step_question",
    "confirmation",
    "choice",
    "unknown",
]

# Senzing SDK method names from mcp-first-invariant that must appear in prompt.
SDK_METHODS: list[str] = [
    "add_record",
    "get_entity",
    "search_by_attributes",
    "why_entities",
    "how_entity",
    "export_json_entity_report",
    "get_record",
    "delete_record",
    "reevaluate_entity",
    "reevaluate_record",
    "find_interesting_entities_by_entity_id",
    "find_interesting_entities_by_record_id",
    "find_path_by_entity_id",
    "find_network_by_entity_id",
    "count_redo_records",
    "get_redo_record",
    "process_redo_record",
]

# Senzing attribute names from mcp-first-invariant that must appear in prompt.
ATTRIBUTE_NAMES: list[str] = [
    "NAME_FULL",
    "NAME_FIRST",
    "NAME_LAST",
    "ADDR_FULL",
    "ADDR_LINE1",
    "ADDR_CITY",
    "ADDR_STATE",
    "ADDR_POSTAL_CODE",
    "PHONE_NUMBER",
    "EMAIL_ADDR",
    "DATE_OF_BIRTH",
    "SSN_NUMBER",
    "PASSPORT_NUMBER",
    "DRIVERS_LICENSE_NUMBER",
    "DATA_SOURCE",
    "RECORD_ID",
    "RECORD_TYPE",
]

# Entity resolution terms from mcp-first-invariant that must appear in prompt.
ER_TERMS: list[str] = [
    "resolved entity",
    "entity resolution",
    "candidate scoring",
    "feature scoring",
    "generic threshold",
    "close match",
    "possible match",
    "name-only match",
    "disclosed relationship",
]

# MCP tool names from mcp-first-invariant that must appear in prompt.
MCP_TOOL_NAMES: list[str] = [
    "search_docs",
    "get_sdk_reference",
    "generate_scaffold",
    "sdk_guide",
    "explain_error_code",
    "find_examples",
    "mapping_workflow",
    "get_capabilities",
    "reporting_guide",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the consolidated hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


# ---------------------------------------------------------------------------
# Property 3: Step Sequencing and MCP-First Logic Preservation
# ---------------------------------------------------------------------------


class TestStepSequencingLogicPreservation:
    """Verify step sequencing logic is preserved and Phase 2B is broadened.

    **Validates: Requirements 1.4 (step sequencing preserved),
    agent-answer-processing-failures Requirements 3.3, 3.4 (Phase 2B broadened)**

    The consolidated prompt SHALL contain the ANSWER PROCESSING RETRY heading
    and all question type dispatch keywords. The old Transition_Confirmation
    patterns (transition question patterns, affirmative phrases) are no longer
    required as Phase 2B activation prerequisites.
    """

    def test_prompt_contains_answer_processing_retry_heading(self):
        """The consolidated prompt SHALL contain 'ANSWER PROCESSING RETRY'."""
        prompt = load_hook_prompt()
        assert "ANSWER PROCESSING RETRY" in prompt, (
            "Consolidated prompt does not contain 'ANSWER PROCESSING RETRY' heading"
        )

    def test_prompt_does_not_contain_old_module_transition_retry_heading(self):
        """The consolidated prompt SHALL NOT contain 'MODULE TRANSITION RETRY'."""
        prompt = load_hook_prompt()
        assert "MODULE TRANSITION RETRY" not in prompt, (
            "Consolidated prompt still contains old 'MODULE TRANSITION RETRY' heading"
        )

    @given(qtype=st.sampled_from(ANSWER_PROCESSING_TYPES))
    @settings(max_examples=20)
    def test_prompt_contains_answer_processing_type(self, qtype: str):
        """For any answer processing type, the consolidated prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert qtype in prompt, (
            f"Consolidated prompt does not contain answer processing type '{qtype}'"
        )

    def test_prompt_contains_sequential_step_enforcement(self):
        """The consolidated prompt SHALL contain sequential step enforcement logic."""
        prompt = load_hook_prompt()
        assert "SEQUENTIAL STEP ENFORCEMENT" in prompt, (
            "Consolidated prompt does not contain 'SEQUENTIAL STEP ENFORCEMENT'"
        )

    def test_prompt_contains_step_violation_output(self):
        """The consolidated prompt SHALL contain step violation output format."""
        prompt = load_hook_prompt()
        assert "SEQUENTIAL STEP VIOLATION DETECTED" in prompt, (
            "Consolidated prompt does not contain step violation output format"
        )


class TestMCPFirstLogicPreservation:
    """Verify MCP-first logic from mcp-first-invariant is preserved.

    **Validates: Requirements 1.5**

    For any Senzing content indicator (SDK method names, attribute names,
    ER terms, MCP tool names), that indicator SHALL appear in the consolidated
    Ask_Bootcamper_Hook prompt.
    """

    @given(method=st.sampled_from(SDK_METHODS))
    @settings(max_examples=20)
    def test_prompt_contains_sdk_method(self, method: str):
        """For any SDK method name, the consolidated prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert method in prompt, (
            f"Consolidated prompt does not contain SDK method '{method}'"
        )

    @given(attr=st.sampled_from(ATTRIBUTE_NAMES))
    @settings(max_examples=20)
    def test_prompt_contains_attribute_name(self, attr: str):
        """For any attribute name, the consolidated prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert attr in prompt, (
            f"Consolidated prompt does not contain attribute name '{attr}'"
        )

    @given(term=st.sampled_from(ER_TERMS))
    @settings(max_examples=20)
    def test_prompt_contains_er_term(self, term: str):
        """For any ER term, the consolidated prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert term in prompt, (
            f"Consolidated prompt does not contain ER term '{term}'"
        )

    @given(tool=st.sampled_from(MCP_TOOL_NAMES))
    @settings(max_examples=20)
    def test_prompt_contains_mcp_tool_name(self, tool: str):
        """For any MCP tool name, the consolidated prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert tool in prompt, (
            f"Consolidated prompt does not contain MCP tool name '{tool}'"
        )
