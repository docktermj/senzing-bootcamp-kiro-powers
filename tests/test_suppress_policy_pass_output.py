"""Bug condition exploration and preservation tests for suppress-policy-pass-output.

Tests validate that the enforce-file-path-policies hook prompt instructs silent
processing on the fast path (no visible "policy: pass" output) and preserves
violation-detection behavior on the slow path.

Also validates the dual-reinforcement suppression structure (Properties 1-4):
front-loaded preamble, closing OUTPUT FORMAT section, anti-narration directives,
and edge-case Senzing indicator suppression.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")

# Silent processing patterns (from test_hook_prompt_standards.py), excluding
# the "policy:\s*pass" pattern itself since that IS the bug.
SILENT_PROCESSING_PATTERNS = [
    r"produce no output at all",
    r"do nothing",
    r"do not acknowledge.*do not explain.*do not print",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


def has_silent_processing_instruction(prompt: str) -> bool:
    """Return True if prompt contains a genuine silent-processing instruction.

    Excludes the "policy: pass" pattern since that IS the visible output bug.
    """
    for pattern in SILENT_PROCESSING_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Bug Condition Exploration Tests
# ---------------------------------------------------------------------------

class TestBugConditionExploration:
    """Surface counterexamples demonstrating the hook prompt instructs visible output.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

    These tests encode the EXPECTED (fixed) behavior. They are designed to FAIL
    on unfixed code, confirming the bug exists. After the fix is applied, they
    should PASS.
    """

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]*\.[a-z]+", fullmatch=True),
    )
    @settings(max_examples=5)
    def test_fast_path_does_not_instruct_visible_policy_pass_output(
        self, path: str
    ):
        """For any compliant write path, prompt should NOT contain 'output exactly...policy...pass'.

        **Validates: Requirements 1.1, 1.2**

        The fast-path section of the prompt should not instruct the agent to
        output "policy: pass" as visible text.
        """
        prompt = load_hook_prompt()

        # Assert prompt does NOT contain "output exactly" followed by "policy...pass"
        match = re.search(
            r"output exactly.*\n.*policy.*pass", prompt, re.IGNORECASE
        )
        assert match is None, (
            f"Bug confirmed: prompt instructs visible 'policy: pass' output. "
            f"Match: '{match.group(0)}' (path tested: '{path}')"
        )

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]*\.[a-z]+", fullmatch=True),
    )
    @settings(max_examples=5)
    def test_fast_path_does_not_contain_just_output_reinforcement(
        self, path: str
    ):
        """For any compliant write path, prompt should NOT contain 'Just output: policy: pass'.

        **Validates: Requirements 1.1, 1.2**

        The reinforcement line telling the agent to "Just output: policy: pass"
        should not be present.
        """
        prompt = load_hook_prompt()

        assert "Just output: policy: pass" not in prompt, (
            f"Bug confirmed: prompt contains reinforcement 'Just output: policy: pass' "
            f"(path tested: '{path}')"
        )

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]*\.[a-z]+", fullmatch=True),
    )
    @settings(max_examples=5)
    def test_fast_path_contains_silent_proceed_instruction(self, path: str):
        """For any compliant write path, prompt SHOULD contain a silent-proceed instruction.

        **Validates: Requirements 2.1, 2.2**

        The prompt must contain a genuine silent-processing instruction such as
        "do not acknowledge.*do not explain.*do not print" or
        "produce no output at all" — NOT just "policy: pass".
        """
        prompt = load_hook_prompt()

        assert has_silent_processing_instruction(prompt), (
            f"Bug confirmed: prompt lacks a silent-proceed instruction. "
            f"Expected one of: {SILENT_PROCESSING_PATTERNS} "
            f"(path tested: '{path}')"
        )


# ---------------------------------------------------------------------------
# Preservation Property Tests
# ---------------------------------------------------------------------------

# Baseline SLOW PATH text captured from UNFIXED code (observation phase).
# This constant is used by Property 2d to verify the slow-path section is
# identical after the fix is applied.
ORIGINAL_SLOW_PATH_TEXT = (
    "SLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES "
    "(feedback going to wrong file):\n"
    "- For external paths: STOP. Tell the agent to use project-relative equivalents "
    "(database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).\n"
    "- For misrouted feedback: STOP. Redirect to docs/feedback/"
    "SENZING_BOOTCAMP_POWER_FEEDBACK.md."
)

# Required hook JSON fields for structural validation.
REQUIRED_HOOK_FIELDS = ["name", "version", "description", "when", "then"]


def load_hook_data() -> dict:
    """Load and return the full parsed JSON from the hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


def extract_slow_path_section(prompt: str) -> str:
    """Extract the SLOW PATH section from the prompt text.

    Returns the text starting from "SLOW PATH:" up to (but not including)
    the next major section header (CONTENT CHECK) or end of string.
    """
    match = re.search(
        r"(SLOW PATH:.*?)(?=\n\nCONTENT CHECK|\Z)", prompt, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    return ""


class TestPreservationProperties:
    """Verify violation-detection behavior is unchanged by the fix.

    **Validates: Requirements 3.1, 3.2, 3.3**

    These tests encode the preservation property: all slow-path behavior
    (external path blocking, feedback redirect, content path checking) must
    remain identical after the fix. They are expected to PASS on both unfixed
    and fixed code.
    """

    @given(
        prefix=st.sampled_from(["/tmp/", "%TEMP%", "~/Downloads"]),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P")),
            min_size=0,
            max_size=20,
        ),
    )
    @settings(max_examples=5)
    def test_property_2a_slow_path_contains_blocking_for_external_paths(
        self, prefix: str, suffix: str
    ):
        """For any external path prefix, the prompt SLOW PATH section contains blocking instructions.

        **Validates: Requirements 3.1**

        Property 2a: For any generated external path (starting with /tmp/, %TEMP%,
        or ~/Downloads), the prompt SLOW PATH section contains blocking instructions
        referencing that path pattern.
        """
        prompt = load_hook_prompt()
        slow_path = extract_slow_path_section(prompt)

        # The slow path must reference the external path prefix
        assert prefix in prompt, (
            f"Prompt does not reference external path prefix '{prefix}'"
        )

        # The slow path must contain "STOP" instruction
        assert "STOP" in slow_path, (
            f"SLOW PATH section does not contain 'STOP' instruction "
            f"for external path '{prefix}{suffix}'"
        )

        # The slow path must contain blocking language for external paths
        assert "external paths" in slow_path.lower() or "outside" in slow_path.lower(), (
            f"SLOW PATH section does not contain blocking language for "
            f"external path '{prefix}{suffix}'"
        )

    @given(
        non_canonical_path=st.sampled_from([
            "feedback.md",
            "docs/feedback/other.md",
            "FEEDBACK.md",
            "docs/SENZING_BOOTCAMP_POWER_FEEDBACK.md",
            "notes/feedback.md",
        ]),
    )
    @settings(max_examples=5)
    def test_property_2b_prompt_contains_feedback_redirect(
        self, non_canonical_path: str
    ):
        """For any feedback-related write to a non-canonical path, prompt contains redirect.

        **Validates: Requirements 3.2**

        Property 2b: The prompt must contain a redirect instruction pointing to
        the canonical feedback path docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.
        """
        prompt = load_hook_prompt()

        # The prompt must reference the canonical feedback path
        assert "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" in prompt, (
            f"Prompt does not contain redirect to canonical feedback path "
            f"(tested with non-canonical path: '{non_canonical_path}')"
        )

        # The slow path must contain redirect instruction for misrouted feedback
        slow_path = extract_slow_path_section(prompt)
        assert "misrouted feedback" in slow_path.lower() or "redirect" in slow_path.lower(), (
            f"SLOW PATH section does not contain redirect instruction for "
            f"misrouted feedback (tested with: '{non_canonical_path}')"
        )

    @given(
        field_subset=st.sampled_from(REQUIRED_HOOK_FIELDS),
    )
    @settings(max_examples=5)
    def test_property_2c_hook_json_has_all_required_fields(
        self, field_subset: str
    ):
        """For any required hook field, the JSON structure contains it with valid values.

        **Validates: Requirements 3.3**

        Property 2c: All required JSON fields (name, version, description,
        when.type, when.toolTypes, then.type, then.prompt) are present and valid.
        """
        data = load_hook_data()

        # Top-level required field must exist
        assert field_subset in data, (
            f"Hook JSON missing required field: '{field_subset}'"
        )
        assert data[field_subset] is not None, (
            f"Hook JSON field '{field_subset}' is None"
        )

        # Validate nested required fields
        assert data["when"]["type"] == "preToolUse", (
            f"Expected when.type='preToolUse', got '{data['when']['type']}'"
        )
        assert data["when"]["toolTypes"] == ["write"], (
            f"Expected when.toolTypes=['write'], got '{data['when']['toolTypes']}'"
        )
        assert data["then"]["type"] == "askAgent", (
            f"Expected then.type='askAgent', got '{data['then']['type']}'"
        )
        assert "prompt" in data["then"], "Hook JSON missing then.prompt field"
        assert len(data["then"]["prompt"]) > 0, "Hook JSON then.prompt is empty"

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]*\.[a-z]+", fullmatch=True),
    )
    @settings(max_examples=5)
    def test_property_2d_slow_path_text_identical_to_baseline(
        self, path: str
    ):
        """The prompt's SLOW PATH section text is identical to the captured baseline.

        **Validates: Requirements 3.1, 3.2, 3.3**

        Property 2d: The SLOW PATH section must remain unchanged between unfixed
        and fixed versions. This constant was captured from the unfixed code.
        """
        prompt = load_hook_prompt()
        current_slow_path = extract_slow_path_section(prompt)

        assert current_slow_path == ORIGINAL_SLOW_PATH_TEXT, (
            f"SLOW PATH section has changed from baseline.\n"
            f"Expected:\n{ORIGINAL_SLOW_PATH_TEXT}\n\n"
            f"Got:\n{current_slow_path}\n\n"
            f"(path tested: '{path}')"
        )


# ---------------------------------------------------------------------------
# Agent Instructions Hook Silence Rule Tests (Property 8)
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS_PATH = Path("senzing-bootcamp/steering/agent-instructions.md")

# Forbidden patterns that MUST be enumerated in the hook silence rule
REQUIRED_FORBIDDEN_PATTERNS = [
    "Fast path passes",
    "Proceeding",
    "All checks pass",
    "The question is not compound",
    "This is a JSON configuration file",
]

# All hook types that must be explicitly covered
REQUIRED_HOOK_TYPES = ["preToolUse", "agentStop"]


def load_agent_instructions() -> str:
    """Load and return the full content of agent-instructions.md."""
    with open(AGENT_INSTRUCTIONS_PATH, encoding="utf-8") as f:
        return f.read()


class TestAgentInstructionsHookSilence:
    """Validate the strengthened hook silence rule in agent-instructions.md.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 8.4**

    Property 8: For any valid Agent_Instructions file, the hook silence rule
    SHALL enumerate specific forbidden output patterns (including "Fast path
    passes", "Proceeding", "The question is not compound", "All checks pass",
    "This is a JSON configuration file"), state zero-visible-tokens for passing
    checks, state corrective-only output for violations, and explicitly apply
    to all hook types (preToolUse, agentStop).
    """

    @given(
        forbidden_phrase=st.sampled_from(REQUIRED_FORBIDDEN_PATTERNS),
    )
    @settings(max_examples=20)
    def test_property_8a_enumerates_forbidden_patterns(
        self, forbidden_phrase: str
    ) -> None:
        """For any required forbidden phrase, agent-instructions contains it.

        **Validates: Requirements 5.2**

        The hook silence rule must enumerate each specific forbidden output
        pattern so the agent knows exactly which phrases are prohibited.
        """
        content = load_agent_instructions()

        assert forbidden_phrase in content, (
            f"Agent instructions missing required forbidden pattern: "
            f"'{forbidden_phrase}'"
        )

    @given(
        hook_type=st.sampled_from(REQUIRED_HOOK_TYPES),
    )
    @settings(max_examples=20)
    def test_property_8b_covers_all_hook_types(
        self, hook_type: str
    ) -> None:
        """For any required hook type, agent-instructions mentions it in the silence rule.

        **Validates: Requirements 5.5**

        The hook silence rule must explicitly apply to all hook types including
        preToolUse hooks, agentStop hooks, and any future hook types.
        """
        content = load_agent_instructions()

        # The hook silence rule section must reference this hook type
        assert hook_type in content, (
            f"Agent instructions missing hook type coverage: '{hook_type}'"
        )

        # Verify it appears in the context of the hook silence rule section
        silence_rule_match = re.search(
            r"Hook silence rule.*?(?=\n## |\Z)", content, re.DOTALL
        )
        assert silence_rule_match is not None, (
            "Agent instructions missing 'Hook silence rule' section"
        )
        silence_section = silence_rule_match.group(0)
        assert hook_type in silence_section, (
            f"Hook type '{hook_type}' not mentioned within the hook silence "
            f"rule section"
        )

    @given(
        zero_token_phrase=st.sampled_from([
            "zero visible tokens",
            "zero tokens",
            "no acknowledgment",
            "no reasoning",
        ]),
    )
    @settings(max_examples=20)
    def test_property_8c_states_zero_visible_tokens(
        self, zero_token_phrase: str
    ) -> None:
        """The agent-instructions contains zero-visible-tokens language.

        **Validates: Requirements 5.3**

        The hook silence rule must state that when a hook check passes with no
        action needed, the agent produces zero visible tokens — no acknowledgment,
        no reasoning, no status, no summary.
        """
        content = load_agent_instructions()

        # At least one of the zero-token phrases must be present
        has_zero_token_language = any(
            phrase in content.lower()
            for phrase in [
                "zero visible tokens",
                "zero tokens",
            ]
        )
        assert has_zero_token_language, (
            f"Agent instructions missing zero-visible-tokens language. "
            f"Checked phrase: '{zero_token_phrase}'"
        )

        # Must also contain "no acknowledgment" and "no reasoning" language
        assert "no acknowledgment" in content.lower(), (
            "Agent instructions missing 'no acknowledgment' language"
        )

    @given(
        corrective_indicator=st.sampled_from([
            "corrective",
            "only the corrective content",
            "no.*preamble",
        ]),
    )
    @settings(max_examples=20)
    def test_property_8d_states_corrective_only_output(
        self, corrective_indicator: str
    ) -> None:
        """The agent-instructions contains corrective-output-only language.

        **Validates: Requirements 5.4**

        The hook silence rule must state that when a hook produces corrective
        output (e.g., a rewritten question, a STOP message), the agent outputs
        ONLY the corrective content with no preamble or explanation.
        """
        content = load_agent_instructions()

        # Normalize whitespace for multi-line matching
        normalized = re.sub(r"\s+", " ", content.lower())

        assert re.search(corrective_indicator.lower(), normalized), (
            f"Agent instructions missing corrective-only output language: "
            f"'{corrective_indicator}'"
        )


# ---------------------------------------------------------------------------
# Dual Reinforcement Structure Property Tests (Properties 1-4)
# ---------------------------------------------------------------------------

# Forbidden narration phrases that must appear in anti-narration directives.
FORBIDDEN_NARRATION_PHRASES = [
    "Fast path passes",
    "Proceeding",
    "All checks pass",
    "This is a JSON configuration file",
    "Not SQL",
    "The file is inside the working directory",
]

# Senzing database indicators used in edge-case suppression testing.
SENZING_INDICATORS = [
    "G2C.db",
    "database/G2C.db",
    "RES_ENT",
    "OBS_ENT",
    "RES_FEAT_STAT",
    "DSRC_RECORD",
    "LIB_FEAT",
    "RES_REL",
    "SZ_",
    "sz_dm_",
]


class TestDualReinforcementStructure:
    """Validate the Write Policy Gate dual-reinforcement suppression structure.

    **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 6.1, 6.2, 8.1, 8.2**

    Properties 1-4 verify that the Write Policy Gate prompt contains:
    - A front-loaded suppression preamble within the first 200 characters (Property 1)
    - A closing OUTPUT FORMAT section after all CHECK sections (Property 2)
    - Explicit anti-narration directives with forbidden phrases (Property 3)
    - Edge-case instruction for Senzing indicators without SQL patterns (Property 4)
    """

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]{1,20}\.[a-z]{1,4}", fullmatch=True),
    )
    @settings(max_examples=20)
    def test_property_1_front_loaded_suppression_preamble(self, path: str):
        """For any valid Write_Policy_Gate prompt, the first 200 characters SHALL contain
        an explicit zero-output directive.

        **Validates: Requirements 1.2, 6.1**

        Property 1: The suppression preamble must appear within the first 200 characters
        of the prompt text to ensure the LLM processes it before any evaluation logic.
        Must contain directives like "ZERO tokens", "No output", or "produce no output".
        """
        prompt = load_hook_prompt()
        first_200 = prompt[:200].lower()

        zero_output_patterns = [
            "zero tokens",
            "no output",
            "produce no output",
            "produce zero",
        ]

        has_zero_output_directive = any(
            pattern in first_200 for pattern in zero_output_patterns
        )

        assert has_zero_output_directive, (
            f"Property 1 FAILED: The first 200 characters of the Write_Policy_Gate "
            f"prompt do not contain an explicit zero-output directive. "
            f"Expected one of: {zero_output_patterns} "
            f"First 200 chars: '{prompt[:200]}' "
            f"(path tested: '{path}')"
        )

    @given(
        path=st.from_regex(r"[a-z][a-z0-9_/]{1,20}\.[a-z]{1,4}", fullmatch=True),
    )
    @settings(max_examples=20)
    def test_property_2_closing_output_format_section(self, path: str):
        """For any valid Write_Policy_Gate prompt, there SHALL exist an OUTPUT FORMAT
        section that appears after all CHECK sections and contains both a zero-output
        directive for passing checks and a list of forbidden narration patterns.

        **Validates: Requirements 1.3, 6.2**

        Property 2: The OUTPUT FORMAT section must:
        - Appear after CHECK 1, CHECK 2, CHECK 3 (or CHECK 4) sections
        - Contain a zero-output directive for passing checks
        - Contain a list of forbidden narration patterns
        """
        prompt = load_hook_prompt()

        # Find positions of CHECK sections and OUTPUT FORMAT
        check_positions = []
        for check_label in ["CHECK 1", "CHECK 2", "CHECK 3", "CHECK 4"]:
            pos = prompt.find(check_label)
            if pos != -1:
                check_positions.append(pos)

        output_format_pos = prompt.find("OUTPUT FORMAT")

        # OUTPUT FORMAT section must exist
        assert output_format_pos != -1, (
            f"Property 2 FAILED: Write_Policy_Gate prompt does not contain an "
            f"'OUTPUT FORMAT' section. (path tested: '{path}')"
        )

        # OUTPUT FORMAT must appear after all CHECK sections
        assert check_positions, (
            f"Property 2 FAILED: No CHECK sections found in prompt. "
            f"(path tested: '{path}')"
        )
        last_check_pos = max(check_positions)
        assert output_format_pos > last_check_pos, (
            f"Property 2 FAILED: OUTPUT FORMAT section (pos {output_format_pos}) "
            f"does not appear after all CHECK sections (last at pos {last_check_pos}). "
            f"(path tested: '{path}')"
        )

        # Extract OUTPUT FORMAT section content
        output_format_section = prompt[output_format_pos:]

        # Must contain zero-output directive for passing checks
        zero_output_in_format = re.search(
            r"(zero tokens|ZERO tokens|no output|produce no output)",
            output_format_section,
            re.IGNORECASE,
        )
        assert zero_output_in_format, (
            f"Property 2 FAILED: OUTPUT FORMAT section does not contain a "
            f"zero-output directive for passing checks. "
            f"(path tested: '{path}')"
        )

        # Must contain forbidden narration patterns list
        has_forbidden_list = re.search(
            r"(FORBIDDEN|forbidden)", output_format_section
        )
        assert has_forbidden_list, (
            f"Property 2 FAILED: OUTPUT FORMAT section does not contain a "
            f"list of forbidden narration patterns. "
            f"(path tested: '{path}')"
        )

    @given(
        forbidden_phrase=st.sampled_from(FORBIDDEN_NARRATION_PHRASES),
    )
    @settings(max_examples=20)
    def test_property_3_anti_narration_directives(self, forbidden_phrase: str):
        """For any valid Write_Policy_Gate prompt, the prompt text SHALL contain
        explicit anti-narration directives that enumerate forbidden phrases.

        **Validates: Requirements 1.4, 1.5**

        Property 3: The prompt must contain explicit anti-narration directives
        that enumerate forbidden phrases including "Fast path passes",
        "Proceeding", and "All checks pass".
        """
        prompt = load_hook_prompt()

        # The forbidden phrase must appear in the prompt as part of an
        # anti-narration directive (quoted or listed as forbidden)
        assert forbidden_phrase in prompt, (
            f"Property 3 FAILED: Write_Policy_Gate prompt does not contain "
            f"the forbidden phrase '{forbidden_phrase}' in its anti-narration "
            f"directives. The prompt must enumerate this phrase as forbidden output."
        )

        # Verify there's a "Do NOT output" or "FORBIDDEN" or "never produce"
        # directive that contextualizes these phrases as forbidden
        has_anti_narration_context = (
            "Do NOT output" in prompt
            or "FORBIDDEN" in prompt
            or "never produce" in prompt
            or "Do not output" in prompt
        )
        assert has_anti_narration_context, (
            f"Property 3 FAILED: Write_Policy_Gate prompt contains the phrase "
            f"'{forbidden_phrase}' but lacks an anti-narration directive context "
            f"(e.g., 'Do NOT output', 'FORBIDDEN', 'never produce'). "
            f"The phrases must be explicitly marked as forbidden."
        )

    @given(
        indicator=st.sampled_from(SENZING_INDICATORS),
    )
    @settings(max_examples=20)
    def test_property_4_edge_case_senzing_indicator_suppression(self, indicator: str):
        """For any valid Write_Policy_Gate prompt, the prompt text SHALL contain an
        explicit instruction that content referencing Senzing database indicators
        WITHOUT SQL patterns passes silently with zero tokens and no explanation.

        **Validates: Requirements 2.1, 2.2, 2.3**

        Property 4: The prompt must contain an explicit edge-case instruction
        covering the scenario where content references Senzing indicators (like
        JSON configuration files with connection strings) but does NOT contain
        SQL patterns — this must pass silently.
        """
        prompt = load_hook_prompt()

        # The prompt must contain the Senzing indicator
        assert indicator in prompt, (
            f"Property 4 FAILED: Write_Policy_Gate prompt does not contain "
            f"Senzing database indicator '{indicator}'."
        )

        # The prompt must contain an explicit edge-case instruction about
        # Senzing indicators WITHOUT SQL patterns passing silently
        edge_case_patterns = [
            r"[Ww]ithout\s+SQL\s+patterns",
            r"does\s+NOT\s+contain\s+(any\s+of\s+the\s+)?SQL\s+patterns",
            r"indicators\s+WITHOUT\s+SQL",
        ]

        has_edge_case_instruction = any(
            re.search(pattern, prompt) for pattern in edge_case_patterns
        )
        assert has_edge_case_instruction, (
            f"Property 4 FAILED: Write_Policy_Gate prompt does not contain an "
            f"explicit instruction about content referencing Senzing indicators "
            f"WITHOUT SQL patterns passing silently. "
            f"(indicator tested: '{indicator}')"
        )

        # The edge-case instruction must include a silence directive
        # (zero tokens, silently, no explanation)
        silence_patterns = [
            r"passes\s+silently",
            r"zero\s+tokens",
            r"no\s+explanation",
            r"produce\s+no\s+output",
        ]

        has_silence_directive = any(
            re.search(pattern, prompt, re.IGNORECASE) for pattern in silence_patterns
        )
        assert has_silence_directive, (
            f"Property 4 FAILED: Write_Policy_Gate prompt has an edge-case "
            f"instruction for Senzing indicators without SQL but lacks a "
            f"silence directive (zero tokens, passes silently, no explanation). "
            f"(indicator tested: '{indicator}')"
        )
