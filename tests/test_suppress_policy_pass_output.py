"""Bug condition exploration and preservation tests for suppress-policy-pass-output.

Tests validate that the enforce-file-path-policies hook prompt instructs silent
processing on the fast path (no visible "policy: pass" output) and preserves
violation-detection behavior on the slow path.
"""

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook")

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
