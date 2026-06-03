"""Property-based tests for the hook-silent-fast-path bugfix.

Tests validate that the write-policy-gate hook prompt instructs genuinely silent
processing on the fast path (zero visible output) without any contradicting
instructions that encourage the agent to narrate or output text, and preserves
all violation-detection behavior (slow-path blocking, compound question format,
feedback redirect, SQL blocking).

Also validates that the question-format-gate hook prompt contains dual suppression
reinforcement (front-loaded preamble + closing OUTPUT FORMAT section) with explicit
anti-narration directives and rewrite-only output constraints.

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 6.3, 6.4, 6.5, 8.3**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")

# Senzing database indicators that must be referenced in SQL blocking instructions.
SENZING_DB_INDICATORS = [
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

# Required top-level hook JSON fields.
REQUIRED_HOOK_FIELDS = ["name", "version", "description", "when", "then"]

# Canonical feedback path that must appear in the prompt.
CANONICAL_FEEDBACK_PATH = "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"

# Baseline SLOW PATH text captured from UNFIXED code (observation phase).
# This is the exact text from the CHECK 3 SLOW PATH section.
ORIGINAL_SLOW_PATH_TEXT = (
    "SLOW PATH: If Q1 is NO (path is outside working directory) "
    "OR Q2 is YES (feedback going to wrong file):\n"
    "- For external paths: STOP. Tell the agent to use project-relative "
    "equivalents (database/G2C.db for databases, data/temp/ for temporary "
    "files, src/ for source code).\n"
    "- For misrouted feedback: STOP. Redirect to "
    "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_data() -> dict:
    """Load and return the full parsed JSON from the hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the hook file."""
    data = load_hook_data()
    return data["then"]["prompt"]


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


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_project_relative_path() -> st.SearchStrategy[str]:
    """Strategy generating project-relative file paths (inside working directory)."""
    extensions = [".py", ".js", ".ts", ".json", ".yaml", ".md", ".txt", ".rs", ".java", ".cs"]
    return st.builds(
        lambda parts, name, ext: "/".join(parts + [name + ext]),
        parts=st.lists(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
                min_size=1,
                max_size=10,
            ),
            min_size=1,
            max_size=3,
        ),
        name=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
            min_size=1,
            max_size=12,
        ),
        ext=st.sampled_from(extensions),
    )


def extract_fast_path_section(prompt: str) -> str:
    """Extract the FAST PATH GATE section from the prompt.

    Returns text from 'FAST PATH GATE' up to the first '---' separator.
    """
    match = re.search(r"(FAST PATH GATE:.*?)(?=\n---|\Z)", prompt, re.DOTALL)
    if match:
        return match.group(1)
    return ""


# ---------------------------------------------------------------------------
# Bug Condition Exploration Tests
# ---------------------------------------------------------------------------


class TestBugConditionExploration:
    """Surface counterexamples demonstrating the hook prompt instructs visible output.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

    These tests encode the EXPECTED (fixed) behavior. They are designed to FAIL
    on unfixed code, confirming the bug exists. After the fix is applied, they
    should PASS.

    The bug: the hook prompt's fast-path section lacks sufficiently strong
    zero-output directives, causing the agent to narrate its evaluation instead
    of producing zero tokens.
    """

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_1a_no_output_exactly_policy_pass_instruction(self, path: str):
        """For any project-relative file path, prompt should NOT contain
        'output exactly' followed by 'policy...pass'.

        **Validates: Requirements 1.1, 1.2**

        The fast-path section must not instruct the agent to output any text
        containing 'policy' and 'pass' as visible output.
        """
        prompt = load_hook_prompt()

        # Check for "output exactly" followed by "policy...pass" anywhere in prompt
        match = re.search(
            r"output exactly.*?policy.*?pass", prompt, re.IGNORECASE | re.DOTALL
        )
        assert match is None, (
            f"Bug confirmed: prompt instructs visible 'policy: pass' output. "
            f"Match: '{match.group(0)[:100]}' (path tested: '{path}')"
        )

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_1b_no_just_output_policy_pass_reinforcement(self, path: str):
        """For any project-relative file path, prompt should NOT contain
        'Just output: policy: pass' reinforcement.

        **Validates: Requirements 1.1, 1.2**

        The reinforcement line telling the agent to 'Just output: policy: pass'
        should not be present anywhere in the prompt.
        """
        prompt = load_hook_prompt()

        assert "Just output: policy: pass" not in prompt, (
            f"Bug confirmed: prompt contains reinforcement 'Just output: policy: pass' "
            f"(path tested: '{path}')"
        )

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_1c_contains_genuine_silent_instruction_without_contradiction(
        self, path: str
    ):
        """For any project-relative file path, prompt CONTAINS a genuine
        silent-processing instruction without contradicting output instructions.

        **Validates: Requirements 2.1, 2.2, 2.3**

        The fast-path section must contain an explicit zero-output directive
        such as 'produce no output at all', 'OUTPUT: (none)', or
        'produce zero tokens' — a structurally emphatic instruction that goes
        beyond the weak 'Proceed silently' phrasing. The mere presence of
        'Do not acknowledge. Do not explain. Do not print anything.' is
        insufficient because the agent does not honor it (that IS the bug).
        """
        prompt = load_hook_prompt()
        fast_path = extract_fast_path_section(prompt)

        # The fast-path section must contain an EXPLICIT zero-output marker
        # that is structurally emphatic (not just "proceed silently")
        explicit_zero_output_patterns = [
            r"produce no output at all",
            r"OUTPUT:\s*\(none\)",
            r"produce zero tokens",
            r"zero tokens",
            r"RESPONSE:\s*empty",
            r"\[empty.*produce zero tokens\]",
            r"your response.*:\s*\[empty",
        ]

        has_explicit_zero_output = any(
            re.search(pattern, fast_path, re.IGNORECASE)
            for pattern in explicit_zero_output_patterns
        )

        assert has_explicit_zero_output, (
            f"Bug confirmed: fast-path section lacks an explicit zero-output directive. "
            f"The existing 'Proceed silently' is insufficient — the agent ignores it. "
            f"Expected one of: {explicit_zero_output_patterns} "
            f"(path tested: '{path}')"
        )

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_1d_no_narration_encouraging_patterns(self, path: str):
        """For any project-relative file path, prompt should NOT contain
        narration-encouraging patterns that cause the agent to summarize
        its evaluation.

        **Validates: Requirements 1.3, 2.3**

        Patterns like 'Proceed silently' (without explicit zero-token
        reinforcement), 'skip all checks and proceed immediately', or
        'proceed immediately' as a standalone instruction encourage the agent
        to narrate what it's doing ('Fast path passes — proceeding') rather
        than producing zero output.
        """
        prompt = load_hook_prompt()
        fast_path = extract_fast_path_section(prompt)

        # Check for narration-encouraging patterns in the fast-path section
        narration_patterns = [
            # "Proceed silently" without zero-token reinforcement encourages
            # the agent to say "Proceeding silently" or "Fast path passes"
            r"[Pp]roceed silently",
            # "skip all checks and proceed immediately" encourages narration
            r"skip all checks and proceed immediately",
            # "proceed immediately" as standalone encourages narration
            r"proceed immediately",
        ]

        for pattern in narration_patterns:
            match = re.search(pattern, fast_path, re.IGNORECASE)
            if match:
                # Only flag if there's no explicit anti-narration instruction nearby
                anti_narration_patterns = [
                    r"do NOT output phrases like",
                    r"zero tokens means zero tokens",
                    r"do not .* summarize .* evaluation",
                ]
                has_anti_narration = any(
                    re.search(ap, fast_path, re.IGNORECASE)
                    for ap in anti_narration_patterns
                )
                assert has_anti_narration, (
                    f"Bug confirmed: fast-path section contains narration-encouraging "
                    f"pattern '{match.group(0)}' without anti-narration reinforcement. "
                    f"This causes the agent to output text like 'Fast path passes — "
                    f"proceeding' instead of producing zero tokens. "
                    f"(path tested: '{path}')"
                )


# ---------------------------------------------------------------------------
# Preservation Property Tests
# ---------------------------------------------------------------------------


class TestPreservationProperties:
    """Verify violation-detection behavior is unchanged by the fix.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

    These tests encode the preservation property: all slow-path behavior
    (external path blocking, feedback redirect, SQL blocking, compound question
    format, hook JSON structure) must remain identical after the fix. They are
    expected to PASS on both unfixed and fixed code.
    """

    @given(
        prefix=st.sampled_from(["/tmp/", "%TEMP%", "~/Downloads"]),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=15,
        ),
    )
    @settings(max_examples=20)
    def test_property_2a_slow_path_blocks_external_paths(
        self, prefix: str, suffix: str
    ):
        """For any external path prefix, the SLOW PATH section contains STOP and blocking.

        **Validates: Requirements 3.3, 3.5**

        Property 2a: For any generated external path prefix (/tmp/, %TEMP%,
        ~/Downloads), the prompt SLOW PATH section contains "STOP" and blocking
        instructions referencing project-relative equivalents.
        """
        prompt = load_hook_prompt()
        slow_path = extract_slow_path_section(prompt)

        # The prompt must reference the external path prefix somewhere
        assert prefix in prompt, (
            f"Prompt does not reference external path prefix '{prefix}'"
        )

        # The SLOW PATH section must contain "STOP"
        assert "STOP" in slow_path, (
            f"SLOW PATH section does not contain 'STOP' instruction "
            f"for external path '{prefix}{suffix}'"
        )

        # The SLOW PATH section must contain project-relative equivalents
        assert "project-relative equivalents" in slow_path, (
            f"SLOW PATH section does not contain 'project-relative equivalents' "
            f"for external path '{prefix}{suffix}'"
        )

    @given(
        non_canonical_path=st.sampled_from([
            "feedback.md",
            "docs/feedback/other.md",
            "FEEDBACK.md",
            "docs/SENZING_BOOTCAMP_POWER_FEEDBACK.md",
            "notes/feedback.md",
            "docs/feedback/feedback_notes.md",
            "tmp/feedback.md",
        ]),
    )
    @settings(max_examples=20)
    def test_property_2b_prompt_contains_feedback_redirect(
        self, non_canonical_path: str
    ):
        """For any non-canonical feedback path, the prompt contains redirect to canonical path.

        **Validates: Requirements 3.4**

        Property 2b: The prompt must contain a redirect instruction pointing to
        the canonical feedback path docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.
        """
        prompt = load_hook_prompt()
        slow_path = extract_slow_path_section(prompt)

        # The prompt must reference the canonical feedback path
        assert CANONICAL_FEEDBACK_PATH in prompt, (
            f"Prompt does not contain canonical feedback path "
            f"'{CANONICAL_FEEDBACK_PATH}' "
            f"(tested with non-canonical path: '{non_canonical_path}')"
        )

        # The SLOW PATH must contain redirect instruction for misrouted feedback
        assert "Redirect" in slow_path or "redirect" in slow_path, (
            f"SLOW PATH section does not contain redirect instruction for "
            f"misrouted feedback (tested with: '{non_canonical_path}')"
        )

    @given(
        field=st.sampled_from(REQUIRED_HOOK_FIELDS),
    )
    @settings(max_examples=20)
    def test_property_2c_hook_json_has_required_fields_with_valid_values(
        self, field: str
    ):
        """For any required hook JSON field, the structure contains it with valid values.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

        Property 2c: All required JSON fields (name, version, description,
        when, then) are present with valid values. Nested fields (when.type,
        when.toolTypes, then.type, then.prompt) are also validated.
        """
        data = load_hook_data()

        # Top-level required field must exist and not be None
        assert field in data, (
            f"Hook JSON missing required field: '{field}'"
        )
        assert data[field] is not None, (
            f"Hook JSON field '{field}' is None"
        )

        # Validate nested required fields for structural integrity
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
        path=st.from_regex(r"[a-z][a-z0-9_/]{1,20}\.[a-z]{1,4}", fullmatch=True),
    )
    @settings(max_examples=20)
    def test_property_2d_slow_path_text_identical_to_baseline(
        self, path: str
    ):
        """For any project-relative file path, the SLOW PATH section is identical to baseline.

        **Validates: Requirements 3.3, 3.4, 3.5**

        Property 2d: The SLOW PATH section text must remain character-for-character
        identical to the captured baseline from unfixed code. This ensures the fix
        does not alter any slow-path violation-detection behavior.
        """
        prompt = load_hook_prompt()
        current_slow_path = extract_slow_path_section(prompt)

        assert current_slow_path == ORIGINAL_SLOW_PATH_TEXT, (
            f"SLOW PATH section has changed from baseline.\n"
            f"Expected:\n{ORIGINAL_SLOW_PATH_TEXT}\n\n"
            f"Got:\n{current_slow_path}\n\n"
            f"(path tested: '{path}')"
        )

    @given(
        indicator=st.sampled_from(SENZING_DB_INDICATORS),
    )
    @settings(max_examples=20)
    def test_property_2e_prompt_contains_sql_blocking_for_senzing_indicators(
        self, indicator: str
    ):
        """For any Senzing database indicator, the prompt contains SQL blocking instructions.

        **Validates: Requirements 3.1**

        Property 2e: For any Senzing database indicator (G2C.db, RES_ENT, OBS_ENT,
        etc.), the prompt contains SQL blocking instructions that reference it and
        provide SDK method alternatives.
        """
        prompt = load_hook_prompt()

        # The prompt must contain the Senzing database indicator
        assert indicator in prompt, (
            f"Prompt does not contain Senzing database indicator '{indicator}'"
        )

        # The prompt must contain SQL blocking instructions (STOP + SDK alternatives)
        assert "STOP" in prompt, (
            f"Prompt does not contain 'STOP' instruction for SQL blocking "
            f"(indicator: '{indicator}')"
        )

        # The prompt must reference SDK methods as alternatives
        assert "SDK" in prompt or "sdk" in prompt, (
            f"Prompt does not reference SDK alternatives for SQL blocking "
            f"(indicator: '{indicator}')"
        )

        # The prompt must contain specific SDK method references
        sdk_methods = [
            "get_entity",
            "search_by_attributes",
            "why_entities",
            "how_entity",
        ]
        has_sdk_method = any(method in prompt for method in sdk_methods)
        assert has_sdk_method, (
            f"Prompt does not contain any SDK method alternatives "
            f"(indicator: '{indicator}'). "
            f"Expected one of: {sdk_methods}"
        )

    @given(
        indicator=st.sampled_from(SENZING_DB_INDICATORS),
    )
    @settings(max_examples=20)
    def test_property_9_sql_blocking_contains_indicator_stop_and_all_sdk_methods(
        self, indicator: str
    ):
        """For any Senzing database indicator, the prompt SHALL contain that indicator,
        a STOP instruction, and ALL four SDK method alternatives.

        **Validates: Requirements 7.1**

        Property 9: For any Senzing database indicator in the set {G2C.db, RES_ENT,
        OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, SZ_, sz_dm_}, the
        Write_Policy_Gate prompt SHALL contain that indicator, a STOP instruction,
        and SDK method alternatives (get_entity, search_by_attributes, why_entities,
        how_entity).
        """
        prompt = load_hook_prompt()

        # The prompt must contain the Senzing database indicator
        assert indicator in prompt, (
            f"Property 9 FAILED: Prompt does not contain Senzing database "
            f"indicator '{indicator}'"
        )

        # The prompt must contain a STOP instruction in the SQL blocking section
        assert "STOP" in prompt, (
            f"Property 9 FAILED: Prompt does not contain 'STOP' instruction "
            f"(indicator: '{indicator}')"
        )

        # The prompt must contain ALL four required SDK method alternatives
        required_sdk_methods = [
            "get_entity",
            "search_by_attributes",
            "why_entities",
            "how_entity",
        ]
        for method in required_sdk_methods:
            assert method in prompt, (
                f"Property 9 FAILED: Prompt does not contain required SDK method "
                f"alternative '{method}' (indicator: '{indicator}')"
            )

    @given(
        validation_rule=st.sampled_from([
            "exactly one question mark",
            "conjunctions joining questions",
            "appended alternatives",
            "unambiguous yes/no",
            "follow-up after confirmation",
        ]),
    )
    @settings(max_examples=20)
    def test_property_10_single_question_enforcement_contains_all_rules(
        self, validation_rule: str
    ):
        """For any valid Write_Policy_Gate prompt, the prompt SHALL contain all five
        single-question validation rules and the compound question violation output format.

        **Validates: Requirements 7.2**

        Property 10: The prompt must contain all five single-question validation rules
        (exactly one question mark, no conjunctions joining questions, no appended
        alternatives, unambiguous yes/no, no follow-up after confirmation) and the
        compound question violation output format.
        """
        prompt = load_hook_prompt()
        prompt_lower = prompt.lower()

        # Each validation rule concept must be present in the prompt
        assert validation_rule.lower() in prompt_lower, (
            f"Property 10 FAILED: Prompt does not contain single-question "
            f"validation rule concept: '{validation_rule}'"
        )

        # The prompt must contain the compound question violation output format
        assert "COMPOUND QUESTION DETECTED" in prompt, (
            f"Property 10 FAILED: Prompt does not contain the compound question "
            f"violation output format 'COMPOUND QUESTION DETECTED' "
            f"(rule tested: '{validation_rule}')"
        )

        # The prompt must contain "REWRITE REQUIRED" as part of the violation format
        assert "REWRITE REQUIRED" in prompt, (
            f"Property 10 FAILED: Prompt does not contain 'REWRITE REQUIRED' "
            f"in the violation output format (rule tested: '{validation_rule}')"
        )

        # The prompt must reference .question_pending as the trigger for this check
        assert ".question_pending" in prompt, (
            f"Property 10 FAILED: Prompt does not reference '.question_pending' "
            f"as the trigger for single-question enforcement "
            f"(rule tested: '{validation_rule}')"
        )

    @given(
        path_element=st.sampled_from([
            "external paths",
            "misrouted feedback",
            "SENZING_BOOTCAMP_POWER_FEEDBACK.md",
            "project-relative equivalents",
            "CONTENT CHECK",
        ]),
    )
    @settings(max_examples=20)
    def test_property_11_file_path_policy_slow_path_preservation(
        self, path_element: str
    ):
        """For any valid Write_Policy_Gate prompt, the SLOW PATH section SHALL remain
        character-for-character identical to the established baseline, preserving
        external path blocking, feedback redirect, and content path checking.

        **Validates: Requirements 7.3**

        Property 11: The SLOW PATH section must preserve external path blocking,
        feedback redirect to the canonical path, and content path checking.
        """
        prompt = load_hook_prompt()

        # Verify the SLOW PATH section is identical to baseline
        current_slow_path = extract_slow_path_section(prompt)
        assert current_slow_path == ORIGINAL_SLOW_PATH_TEXT, (
            f"Property 11 FAILED: SLOW PATH section has changed from baseline.\n"
            f"Expected:\n{ORIGINAL_SLOW_PATH_TEXT}\n\n"
            f"Got:\n{current_slow_path}\n\n"
            f"(element tested: '{path_element}')"
        )

        # Additionally verify the specific path element is present in the prompt
        assert path_element in prompt, (
            f"Property 11 FAILED: Prompt does not contain required file path "
            f"policy element: '{path_element}'"
        )


# ---------------------------------------------------------------------------
# Question Format Gate Constants
# ---------------------------------------------------------------------------

QUESTION_FORMAT_GATE_HOOK_PATH = Path(
    "senzing-bootcamp/hooks/ask-bootcamper.kiro.hook"
)

# Forbidden narration phrases for the Question Format Phase (consolidated hook).
# These are the phrases explicitly forbidden in the Phase 4 "Do NOT output" directive.
QUESTION_FORMAT_GATE_FORBIDDEN_PHRASES = [
    "This is a compound question",
    "Let me rewrite",
    "The question contains 'or' joining alternatives",
]


# ---------------------------------------------------------------------------
# Question Format Gate Helpers
# ---------------------------------------------------------------------------


def load_question_format_gate_data() -> dict:
    """Load and return the full parsed JSON from the consolidated ask-bootcamper hook file."""
    with open(QUESTION_FORMAT_GATE_HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_question_format_gate_prompt() -> str:
    """Load and return the Phase 4 (Question Format) section from the consolidated hook."""
    data = load_question_format_gate_data()
    full_prompt = data["then"]["prompt"]
    # Extract Phase 4 section from the consolidated prompt
    phase4_start = full_prompt.find("PHASE 4:")
    assert phase4_start != -1, "Consolidated hook missing PHASE 4 section"
    # Phase 4 ends at the OUTPUT RULES section or end of prompt
    output_rules_pos = full_prompt.find("OUTPUT RULES", phase4_start + 1)
    if output_rules_pos != -1:
        return full_prompt[phase4_start:output_rules_pos]
    return full_prompt[phase4_start:]


# ---------------------------------------------------------------------------
# Question Format Gate Suppression Property Tests
# ---------------------------------------------------------------------------


class TestQuestionFormatGateSuppression:
    """Validate dual suppression reinforcement in the Question Format Gate prompt.

    **Validates: Requirements 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 6.3, 6.4, 6.5, 8.3**

    These tests verify that the question-format-gate hook prompt contains:
    - A front-loaded suppression preamble within the first 200 characters
    - A closing OUTPUT FORMAT section after the RULES section
    - Explicit rewrite-only output directives forbidding preamble/explanation
    """

    @given(
        forbidden_phrase=st.sampled_from(QUESTION_FORMAT_GATE_FORBIDDEN_PHRASES),
    )
    @settings(max_examples=20)
    def test_property_5_front_loaded_suppression_preamble(
        self, forbidden_phrase: str
    ):
        """For any valid Question_Format_Phase prompt, the section SHALL contain
        an explicit output constraint: "Output ONLY" directive for rewrite case
        and "none" for no-rewrite case, with anti-narration instructions.

        **Validates: Requirements 3.2, 6.3, 6.5**

        Property 5: The suppression directives must appear in Phase 4 to ensure
        the LLM produces only the corrected output or nothing.
        """
        prompt = load_question_format_gate_prompt()

        # Must reference "none" or "no output" for no-rewrite case
        has_no_output = (
            "output is none" in prompt.lower()
            or "no output" in prompt.lower()
        )
        assert has_no_output, (
            f"Phase 4 does not reference 'none'/'no output' for no-rewrite case. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must reference "corrected question" or "regenerated" for rewrite case
        has_rewrite_ref = (
            "corrected question" in prompt.lower()
            or "regenerated" in prompt.lower()
        )
        assert has_rewrite_ref, (
            f"Phase 4 does not reference 'corrected question' or 'regenerated' "
            f"for rewrite case. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must contain anti-narration: "Do NOT" directives
        assert "Do NOT" in prompt, (
            f"Phase 4 does not contain 'Do NOT' anti-narration directives. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

    @given(
        forbidden_phrase=st.sampled_from(QUESTION_FORMAT_GATE_FORBIDDEN_PHRASES),
    )
    @settings(max_examples=20)
    def test_property_6_closing_output_format_section(
        self, forbidden_phrase: str
    ):
        """For any valid Question_Format_Phase prompt, there SHALL exist a "RULES"
        section that contains anti-narration directives and the prompt SHALL contain
        both the no-output directive for no-rewrite and the output-only directive
        for rewrite, plus forbidden narration patterns.

        **Validates: Requirements 3.3, 3.4, 6.4**

        Property 6: The RULES section must exist and contain output directives
        and forbidden phrases.
        """
        prompt = load_question_format_gate_prompt()

        # RULES section must exist
        rules_pos = prompt.find("RULES:")
        assert rules_pos != -1, (
            f"Phase 4 does not contain 'RULES:' section. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must contain no-output directive for no-rewrite case
        has_no_output_directive = (
            "output is none" in prompt.lower()
            or "no output" in prompt.lower()
            or "no compound" in prompt.lower()
        )
        assert has_no_output_directive, (
            f"Phase 4 does not contain no-output directive for no-rewrite. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must contain output-only directive for rewrite case
        has_rewrite_directive = (
            "output only" in prompt.lower()
            or "corrected question" in prompt.lower()
            or "regenerated full response" in prompt.lower()
        )
        assert has_rewrite_directive, (
            f"Phase 4 does not contain output-only directive for rewrite. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must contain the specific forbidden phrase somewhere in the prompt
        # (as part of the anti-narration "Do NOT output" enumeration)
        assert forbidden_phrase in prompt, (
            f"Phase 4 does not contain forbidden phrase: "
            f"'{forbidden_phrase}'"
        )

    @given(
        forbidden_phrase=st.sampled_from(QUESTION_FORMAT_GATE_FORBIDDEN_PHRASES),
    )
    @settings(max_examples=20)
    def test_property_7_rewrite_only_output_directive(
        self, forbidden_phrase: str
    ):
        """For any valid Question_Format_Phase prompt, the prompt text SHALL contain
        explicit instructions forbidding preamble or explanation when outputting a
        rewritten question, and SHALL instruct preservation of non-question content.

        **Validates: Requirements 4.1, 4.2, 4.3**

        Property 7: The prompt must forbid preamble/explanation for rewrites and
        instruct preservation of non-question content.
        """
        prompt = load_question_format_gate_prompt()

        # Must contain instruction forbidding preamble/explanation for rewrites
        rewrite_anti_narration_patterns = [
            r"Do NOT output.*This is a compound question",
            r"Do NOT output.*Let me rewrite",
            r"Output ONLY the regenerated",
            r"Do NOT.*add explanations",
        ]
        has_rewrite_anti_narration = any(
            re.search(pattern, prompt, re.IGNORECASE | re.DOTALL)
            for pattern in rewrite_anti_narration_patterns
        )
        assert has_rewrite_anti_narration, (
            f"Phase 4 does not contain explicit instructions forbidding preamble "
            f"or explanation when outputting a rewritten question. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must instruct preservation of non-question content
        preservation_patterns = [
            r"[Pp]reserve all other content",
            r"only replace the compound question",
            r"Do NOT restructure content that is not",
            r"Do NOT interfere with non-compound",
        ]
        has_preservation = any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in preservation_patterns
        )
        assert has_preservation, (
            f"Phase 4 does not contain instruction to preserve non-question content. "
            f"(tested with forbidden phrase: '{forbidden_phrase}')"
        )

        # Must contain the forbidden phrase somewhere in the prompt
        # (as part of the anti-narration directive enumeration)
        assert forbidden_phrase in prompt, (
            f"Phase 4 does not contain forbidden phrase '{forbidden_phrase}' "
            f"in its anti-narration directives."
        )


# ---------------------------------------------------------------------------
# Question Format Gate Detection Logic Preservation (Property 12)
# ---------------------------------------------------------------------------

# The three compound question detection patterns that must be present.
COMPOUND_DETECTION_PATTERNS = [
    "Sentence-starter",
    "Inline prose",
    "Appended alternative",
]

# NOT COMPOUND exclusion items that must be present in the prompt.
NOT_COMPOUND_EXCLUSIONS = [
    "Simple yes/no questions",
    "numbered list",
    "Informational prose",
    "Non-question content",
]


class TestQuestionFormatGateDetectionPreservation:
    """Validate preservation of compound question detection logic in Question Format Gate.

    **Validates: Requirements 7.4, 7.5, 8.5**

    Property 12: For any valid Question_Format_Gate prompt, the prompt SHALL contain
    all three compound question detection patterns (sentence-starter Or, inline prose
    or, appended alternative) and the complete NOT COMPOUND exclusion list.
    """

    @given(
        pattern=st.sampled_from(COMPOUND_DETECTION_PATTERNS),
    )
    @settings(max_examples=20)
    def test_property_12a_contains_all_detection_patterns(
        self, pattern: str
    ):
        """For any compound question detection pattern, the prompt SHALL contain it.

        **Validates: Requirements 7.4**

        Property 12a: The Question_Format_Gate prompt must contain all three
        compound question detection patterns: sentence-starter Or, inline prose or,
        and appended alternative.
        """
        prompt = load_question_format_gate_prompt()

        assert pattern in prompt, (
            f"Property 12 FAILED: Question_Format_Gate prompt does not contain "
            f"detection pattern: '{pattern}'"
        )

    @given(
        exclusion=st.sampled_from(NOT_COMPOUND_EXCLUSIONS),
    )
    @settings(max_examples=20)
    def test_property_12b_contains_not_compound_exclusion_list(
        self, exclusion: str
    ):
        """For any NOT COMPOUND exclusion item, the prompt SHALL contain it.

        **Validates: Requirements 7.4**

        Property 12b: The Question_Format_Gate prompt must contain the complete
        NOT COMPOUND exclusion list including simple yes/no questions, numbered
        list items, informational prose, and non-question content.
        """
        prompt = load_question_format_gate_prompt()

        # The NOT COMPOUND section must exist
        assert "NOT COMPOUND" in prompt, (
            f"Property 12 FAILED: Question_Format_Gate prompt does not contain "
            f"'NOT COMPOUND' section (exclusion tested: '{exclusion}')"
        )

        # Each exclusion item must be present
        assert exclusion in prompt, (
            f"Property 12 FAILED: Question_Format_Gate prompt does not contain "
            f"NOT COMPOUND exclusion: '{exclusion}'"
        )

    @given(
        or_pattern=st.sampled_from([
            "Or shall we",
            "Or would you",
            "Or should we",
            "or would you rather",
            "or shall we",
            "or if you prefer",
        ]),
    )
    @settings(max_examples=20)
    def test_property_12c_contains_or_pattern_examples(
        self, or_pattern: str
    ):
        """For any 'or' pattern example, the prompt SHALL contain it as a detection example.

        **Validates: Requirements 7.4**

        Property 12c: The Question_Format_Gate prompt must contain specific 'or'
        pattern examples that illustrate the detection rules.
        """
        prompt = load_question_format_gate_prompt()

        assert or_pattern in prompt, (
            f"Property 12 FAILED: Question_Format_Gate prompt does not contain "
            f"'or' pattern example: '{or_pattern}'"
        )

    @given(
        rewrite_element=st.sampled_from([
            "neutral lead question",
            "numbered list",
            "alternatives",
        ]),
    )
    @settings(max_examples=20)
    def test_property_12d_preserves_rewrite_format(
        self, rewrite_element: str
    ):
        """For any rewrite format element, the prompt SHALL contain it.

        **Validates: Requirements 7.5**

        Property 12d: The Question_Format_Gate prompt must preserve the rewrite
        format: a neutral lead question followed by a numbered list of alternatives.
        """
        prompt = load_question_format_gate_prompt()

        assert rewrite_element in prompt, (
            f"Property 12 FAILED: Question_Format_Gate prompt does not contain "
            f"rewrite format element: '{rewrite_element}'"
        )
