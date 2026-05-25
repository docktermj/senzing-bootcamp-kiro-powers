"""Property-based tests for the MCP-First Invariant enforcement system.

Tests validate that:
1. The hook prompt references all Senzing content indicators (SDK methods,
   attribute names, config options, ER terms).
2. The hook prompt contains explicit zero-output directives for silent fast-path.
3. The hook prompt references all MCP tool names in detection logic.
4. The hook prompt maps content categories to appropriate MCP tools in
   self-correction instructions.
5. The agent-instructions.md explicitly prohibits all bypass justifications.
6. The hook is registered as critical-only in hook-categories.yaml.
7. The hook's violation output is agent-directed (action verbs, no conversational
   language).

**Validates: Requirements 1.3, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.4,
6.1, 6.3, 7.1, 7.2, 7.3**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hook_test_helpers import parse_categories_yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")
AGENT_INSTRUCTIONS_PATH = Path("senzing-bootcamp/steering/agent-instructions.md")
CATEGORIES_PATH = Path("senzing-bootcamp/hooks/hook-categories.yaml")

# Senzing SDK method names that must appear in the hook prompt.
SENZING_SDK_METHODS: list[str] = [
    "add_record", "get_entity", "search_by_attributes", "why_entities",
    "how_entity", "export_json_entity_report", "get_record", "delete_record",
    "reevaluate_entity", "reevaluate_record",
    "find_interesting_entities_by_entity_id",
    "find_interesting_entities_by_record_id",
    "find_path_by_entity_id", "find_network_by_entity_id",
    "count_redo_records", "get_redo_record", "process_redo_record",
]

# Senzing attribute names that must appear in the hook prompt.
SENZING_ATTRIBUTE_NAMES: list[str] = [
    "NAME_FULL", "NAME_FIRST", "NAME_LAST", "ADDR_FULL", "ADDR_LINE1",
    "ADDR_CITY", "ADDR_STATE", "ADDR_POSTAL_CODE", "PHONE_NUMBER",
    "EMAIL_ADDR", "DATE_OF_BIRTH", "SSN_NUMBER", "PASSPORT_NUMBER",
    "DRIVERS_LICENSE_NUMBER", "DATA_SOURCE", "RECORD_ID", "RECORD_TYPE",
]

# Senzing configuration options that must appear in the hook prompt.
SENZING_CONFIG_OPTIONS: list[str] = [
    "ENTITY_TYPE", "DSRC_ID", "ETYPE_ID", "FTYPE_ID", "CFUNC_ID", "EFCALL_ID",
]

# Entity resolution terms that must appear in the hook prompt.
SENZING_ER_TERMS: list[str] = [
    "resolved entity", "entity resolution", "candidate scoring",
    "feature scoring", "generic threshold", "close match",
    "possible match", "name-only match", "disclosed relationship",
]

# MCP tool names that must appear in the hook prompt.
MCP_TOOL_NAMES: list[str] = [
    "search_docs", "get_sdk_reference", "generate_scaffold", "sdk_guide",
    "explain_error_code", "find_examples", "mapping_workflow",
    "get_capabilities", "reporting_guide",
]

# Agent-internal bypass justifications that must be prohibited.
BYPASS_JUSTIFICATIONS: list[str] = [
    "context pressure",
    "perceived simplicity",
    "cached knowledge",
    "session length",
    "token budget",
]

# Content categories and their expected MCP tool mappings in self-correction output.
CONTENT_CATEGORY_TOOL_MAPPINGS: list[tuple[str, list[str]]] = [
    ("SDK methods", ["get_sdk_reference", "sdk_guide"]),
    ("Attribute names", ["mapping_workflow", "search_docs"]),
    ("Error codes", ["explain_error_code"]),
    ("Configuration options", ["get_sdk_reference", "search_docs"]),
    ("Documentation", ["search_docs"]),
    ("Code generation", ["generate_scaffold", "sdk_guide"]),
    ("Examples", ["find_examples"]),
    ("Entity resolution terms", ["search_docs"]),
]

# Action verbs expected in violation output (agent-directed language).
ACTION_VERBS: list[str] = ["Call", "Regenerate", "Do NOT"]

# Conversational phrases that should NOT appear in violation output.
CONVERSATIONAL_PHRASES: list[str] = [
    "I hope this helps",
    "Let me know if",
    "Here's what happened",
    "I noticed that",
    "You might want to",
    "Please note that",
    "As you can see",
    "I'd recommend",
    "Feel free to",
    "Don't worry",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the MCP_First_Phase section from the consolidated hook.

    Extracts the Phase 3 (MCP-First Compliance) section from the consolidated
    ask-bootcamper.kiro.hook prompt, since the original mcp-first-invariant hook
    was merged into this phase. Also includes the hook preamble which contains
    the zero-output directive governing all phases.
    """
    with open(HOOK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    full_prompt = data["then"]["prompt"]

    # Extract preamble (before Phase 1) which contains zero-output directives
    preamble_match = re.search(
        r"^(.*?)(?=═{10,}\nPHASE 1:)",
        full_prompt,
        re.DOTALL,
    )
    preamble = preamble_match.group(1) if preamble_match else ""

    # Extract Phase 3 section (MCP_First_Phase) from the consolidated prompt
    phase3_match = re.search(
        r"(PHASE 3: MCP-FIRST COMPLIANCE.*?)(?=═{10,}\nPHASE 4:|\Z)",
        full_prompt,
        re.DOTALL,
    )
    phase3 = phase3_match.group(1) if phase3_match else ""

    # Combine preamble + Phase 3 to preserve zero-output directive context
    return preamble + phase3 if (preamble or phase3) else full_prompt


def load_agent_instructions() -> str:
    """Load and return the full agent-instructions.md content."""
    return AGENT_INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def extract_violation_output(prompt: str) -> str:
    """Extract the self-correction output section from the hook prompt.

    Returns text from "SELF-CORRECTION OUTPUT" or "MCP-FIRST INVARIANT VIOLATION"
    to end of prompt.
    """
    match = re.search(
        r"((?:SELF-CORRECTION OUTPUT|MCP-FIRST INVARIANT VIOLATION).*)",
        prompt,
        re.DOTALL,
    )
    if match:
        return match.group(1)
    return ""


# ---------------------------------------------------------------------------
# Property 1: Senzing Indicator Detection Coverage
# ---------------------------------------------------------------------------


class TestSenzingIndicatorDetectionCoverage:
    """For any Senzing content indicator, the hook prompt contains that indicator.

    **Validates: Requirements 1.3, 2.3, 3.1**

    Property 1: For any SDK method name, attribute name, config option, or ER
    term from the defined sets, verify the hook prompt contains that indicator.
    """

    @given(method=st.sampled_from(SENZING_SDK_METHODS))
    @settings(max_examples=20)
    def test_hook_prompt_contains_sdk_method(self, method: str):
        """For any SDK method name, the hook prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert method in prompt, (
            f"Hook prompt does not contain SDK method '{method}'"
        )

    @given(attr=st.sampled_from(SENZING_ATTRIBUTE_NAMES))
    @settings(max_examples=20)
    def test_hook_prompt_contains_attribute_name(self, attr: str):
        """For any attribute name, the hook prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert attr in prompt, (
            f"Hook prompt does not contain attribute name '{attr}'"
        )

    @given(option=st.sampled_from(SENZING_CONFIG_OPTIONS))
    @settings(max_examples=20)
    def test_hook_prompt_contains_config_option(self, option: str):
        """For any config option, the hook prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert option in prompt, (
            f"Hook prompt does not contain config option '{option}'"
        )

    @given(term=st.sampled_from(SENZING_ER_TERMS))
    @settings(max_examples=20)
    def test_hook_prompt_contains_er_term(self, term: str):
        """For any ER term, the hook prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert term in prompt, (
            f"Hook prompt does not contain ER term '{term}'"
        )


# ---------------------------------------------------------------------------
# Property 2: Silent Fast-Path Directives
# ---------------------------------------------------------------------------


class TestSilentFastPathDirectives:
    """Verify the hook prompt contains explicit zero-output directives.

    **Validates: Requirements 3.3, 7.1, 7.2**

    Property 2: Verify the hook prompt contains explicit zero-output directives
    for both no-Senzing-content and compliant (MCP-called) scenarios.
    """

    @given(scenario=st.sampled_from([
        "no Senzing content",
        "MCP tool called",
    ]))
    @settings(max_examples=20)
    def test_hook_prompt_contains_zero_output_directive(self, scenario: str):
        """For any compliant scenario, the hook prompt SHALL contain an explicit
        zero-output directive."""
        prompt = load_hook_prompt()

        # The prompt must contain explicit zero-output language
        zero_output_patterns = [
            r"zero tokens",
            r"ZERO output tokens",
            r"produce ZERO output",
            r"No output",
            r"zero output",
        ]

        has_zero_output = any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in zero_output_patterns
        )
        assert has_zero_output, (
            f"Hook prompt does not contain explicit zero-output directive "
            f"for scenario: '{scenario}'"
        )

    @given(scenario=st.sampled_from([
        "no Senzing content",
        "MCP tool called",
    ]))
    @settings(max_examples=20)
    def test_hook_prompt_has_silent_fast_path_for_no_senzing_content(self, scenario: str):
        """The hook prompt SHALL instruct zero tokens when no Senzing content detected."""
        prompt = load_hook_prompt()

        # Must contain the decision logic for no-Senzing-content → zero tokens
        assert "No Senzing content detected" in prompt or \
               "No Senzing content" in prompt or \
               "NONE of the above" in prompt, (
            f"Hook prompt does not contain no-Senzing-content fast-path logic "
            f"(scenario: '{scenario}')"
        )

    @given(scenario=st.sampled_from([
        "no Senzing content",
        "MCP tool called",
    ]))
    @settings(max_examples=20)
    def test_hook_prompt_has_silent_path_for_compliant_mcp_call(self, scenario: str):
        """The hook prompt SHALL instruct zero tokens when MCP tool was called."""
        prompt = load_hook_prompt()

        # Must contain the decision logic for MCP-called → zero tokens (compliant)
        has_compliant_path = (
            "compliant" in prompt.lower() or
            ("MCP tool" in prompt and "zero tokens" in prompt.lower())
        )
        assert has_compliant_path, (
            f"Hook prompt does not contain compliant MCP-called fast-path logic "
            f"(scenario: '{scenario}')"
        )


# ---------------------------------------------------------------------------
# Property 3: MCP Tool Call Verification Coverage
# ---------------------------------------------------------------------------


class TestMCPToolCallVerificationCoverage:
    """For any MCP tool name, the hook prompt references it in detection logic.

    **Validates: Requirements 3.2**

    Property 3: For any MCP tool name from the defined set, verify the hook
    prompt references that tool in its detection logic.
    """

    @given(tool=st.sampled_from(MCP_TOOL_NAMES))
    @settings(max_examples=20)
    def test_hook_prompt_references_mcp_tool(self, tool: str):
        """For any MCP tool name, the hook prompt SHALL reference it."""
        prompt = load_hook_prompt()
        assert tool in prompt, (
            f"Hook prompt does not reference MCP tool '{tool}' in detection logic"
        )


# ---------------------------------------------------------------------------
# Property 4: Self-Correction Instructions
# ---------------------------------------------------------------------------


class TestSelfCorrectionInstructions:
    """For any content category, the violation output maps it to MCP tool(s).

    **Validates: Requirements 4.1, 4.2, 4.3**

    Property 4: For any Senzing content category, verify the hook prompt's
    violation output maps that category to appropriate MCP tool(s).
    """

    @given(
        mapping=st.sampled_from(CONTENT_CATEGORY_TOOL_MAPPINGS),
    )
    @settings(max_examples=20)
    def test_violation_output_maps_category_to_tools(
        self, mapping: tuple[str, list[str]]
    ):
        """For any content category, the violation output SHALL map it to
        appropriate MCP tool(s)."""
        category, expected_tools = mapping
        prompt = load_hook_prompt()
        violation_section = extract_violation_output(prompt)

        assert violation_section, (
            f"Hook prompt does not contain a self-correction/violation output section"
        )

        # The violation section must reference at least one of the expected tools
        has_tool_reference = any(
            tool in violation_section for tool in expected_tools
        )
        assert has_tool_reference, (
            f"Violation output does not map category '{category}' to any of "
            f"the expected tools: {expected_tools}"
        )


# ---------------------------------------------------------------------------
# Property 5: No-Bypass Invariant Language
# ---------------------------------------------------------------------------


class TestNoBypassInvariantLanguage:
    """For any bypass justification, agent-instructions.md prohibits it.

    **Validates: Requirements 5.1, 5.4**

    Property 5: For any agent-internal bypass justification, verify
    `agent-instructions.md` explicitly prohibits it.
    """

    @given(justification=st.sampled_from(BYPASS_JUSTIFICATIONS))
    @settings(max_examples=20)
    def test_agent_instructions_prohibits_bypass_justification(
        self, justification: str
    ):
        """For any bypass justification, agent-instructions.md SHALL
        explicitly prohibit it."""
        content = load_agent_instructions()
        assert justification in content, (
            f"agent-instructions.md does not explicitly mention bypass "
            f"justification '{justification}'"
        )

    @given(justification=st.sampled_from(BYPASS_JUSTIFICATIONS))
    @settings(max_examples=20)
    def test_agent_instructions_has_invariant_precedence(
        self, justification: str
    ):
        """The agent-instructions.md SHALL declare MCP-first as having the same
        precedence as mandatory gates."""
        content = load_agent_instructions()

        # Must contain invariant-strength language
        has_invariant_language = (
            "mandatory gate" in content.lower() or
            "absolute precedence" in content.lower()
        )
        assert has_invariant_language, (
            f"agent-instructions.md does not declare MCP-first with mandatory "
            f"gate precedence (tested with justification: '{justification}')"
        )


# ---------------------------------------------------------------------------
# Property 6: Critical-Only Registration
# ---------------------------------------------------------------------------


class TestCriticalOnlyRegistration:
    """Verify ask-bootcamper is in critical and NOT in module categories.

    **Validates: Requirements 6.1, 6.3**

    Property 6: Verify `ask-bootcamper` appears in `critical` category
    and NOT in any module-specific category.
    """

    @given(st.just("ask-bootcamper"))
    @settings(max_examples=5)
    def test_hook_in_critical_category(self, hook_id: str):
        """The ask-bootcamper hook SHALL appear in the critical category."""
        categories = parse_categories_yaml(CATEGORIES_PATH)
        assert "critical" in categories, (
            "hook-categories.yaml does not contain a 'critical' category"
        )
        assert hook_id in categories["critical"], (
            f"'{hook_id}' is not listed in the critical category. "
            f"Critical hooks: {categories['critical']}"
        )

    @given(st.just("ask-bootcamper"))
    @settings(max_examples=5)
    def test_hook_not_in_module_categories(self, hook_id: str):
        """The ask-bootcamper hook SHALL NOT appear in any module category."""
        categories = parse_categories_yaml(CATEGORIES_PATH)

        module_categories = {
            k: v for k, v in categories.items() if k.startswith("module-")
        }

        for category_name, hooks in module_categories.items():
            assert hook_id not in hooks, (
                f"'{hook_id}' incorrectly appears in module category "
                f"'{category_name}': {hooks}"
            )


# ---------------------------------------------------------------------------
# Property 7: Agent-Directed Output Only
# ---------------------------------------------------------------------------


class TestAgentDirectedOutputOnly:
    """Verify violation output contains action verbs and no conversational language.

    **Validates: Requirements 7.3**

    Property 7: Verify the hook's violation output contains action verbs
    (Call, Regenerate, Do NOT) and no user-facing conversational language.
    """

    @given(verb=st.sampled_from(ACTION_VERBS))
    @settings(max_examples=20)
    def test_violation_output_contains_action_verb(self, verb: str):
        """The violation output SHALL contain agent-directed action verbs."""
        prompt = load_hook_prompt()
        violation_section = extract_violation_output(prompt)

        assert violation_section, (
            "Hook prompt does not contain a violation output section"
        )
        assert verb in violation_section, (
            f"Violation output does not contain action verb '{verb}'. "
            f"Expected agent-directed language."
        )

    @given(phrase=st.sampled_from(CONVERSATIONAL_PHRASES))
    @settings(max_examples=20)
    def test_violation_output_has_no_conversational_language(self, phrase: str):
        """The violation output SHALL NOT contain user-facing conversational language."""
        prompt = load_hook_prompt()
        violation_section = extract_violation_output(prompt)

        assert phrase not in violation_section, (
            f"Violation output contains user-facing conversational phrase: "
            f"'{phrase}'. Output should be agent-directed only."
        )
