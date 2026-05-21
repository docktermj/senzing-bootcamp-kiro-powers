"""Property-based tests for the hook-silent-fast-path bugfix.

Tests validate that the write-policy-gate hook prompt instructs genuinely silent
processing on the fast path (zero visible output) without any contradicting
instructions that encourage the agent to narrate or output text, and preserves
all violation-detection behavior (slow-path blocking, compound question format,
feedback redirect, SQL blocking).

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
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
