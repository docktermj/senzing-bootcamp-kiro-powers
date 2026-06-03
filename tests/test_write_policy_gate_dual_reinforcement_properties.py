"""Property-based tests for write-policy-gate dual-reinforcement suppression.

Validates that the write-policy-gate hook prompt contains dual-reinforcement
suppression structure: a front-loaded zero-output directive within the first
200 characters, an OUTPUT FORMAT section with a zero-token directive, and
"Fast path passes" in a FORBIDDEN output list.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**
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

# Forbidden narration phrases that must appear in the FORBIDDEN list.
FORBIDDEN_NARRATION_PHRASES = [
    "Fast path passes",
    "Proceeding",
    "All checks pass",
    "This is a JSON configuration file",
    "Not SQL",
]

# Zero-output directive patterns (case-insensitive).
ZERO_OUTPUT_PATTERNS = [
    r"zero tokens",
    r"ZERO tokens",
    r"no output",
    r"No output",
    r"produce no output",
]


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


def extract_output_format_section(prompt: str) -> str:
    """Extract the OUTPUT FORMAT section from the prompt text.

    Returns the text starting from "OUTPUT FORMAT" to end of string or next
    major section separator.
    """
    match = re.search(r"(OUTPUT FORMAT.*)", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_forbidden_list(prompt: str) -> str:
    """Extract the FORBIDDEN output list section from the prompt.

    Returns text from "FORBIDDEN" to the end of the list block.
    """
    match = re.search(r"(FORBIDDEN.*?)(?:\n\n|\Z)", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_project_relative_path() -> st.SearchStrategy[str]:
    """Strategy generating project-relative file paths (inside working directory)."""
    extensions = [".py", ".js", ".ts", ".json", ".yaml", ".md", ".txt", ".rs"]
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


# ---------------------------------------------------------------------------
# Property 8: Write-policy-gate dual-reinforcement suppression structure
# ---------------------------------------------------------------------------


class TestWritePolicyGateDualReinforcement:
    """Validate dual-reinforcement suppression structure in write-policy-gate.

    **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

    Property 8: For any valid Write_Policy_Gate prompt:
    (a) the first 200 characters SHALL contain an explicit zero-output directive,
    (b) an OUTPUT FORMAT section SHALL exist after all CHECK sections containing
        a zero-token directive, and
    (c) the phrase "Fast path passes" SHALL appear in a FORBIDDEN output list.
    """

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_property_8a_first_200_chars_contain_zero_output_directive(
        self, path: str
    ):
        """For any project-relative file path, the first 200 characters of the
        prompt SHALL contain an explicit zero-output directive.

        **Validates: Requirements 6.1, 6.3**

        The front-loaded silence directive ensures the LLM processes the
        zero-output instruction before any check logic.
        """
        prompt = load_hook_prompt()
        first_200 = prompt[:200]

        # Must contain a zero-output directive in the first 200 characters
        has_zero_output = any(
            re.search(pattern, first_200)
            for pattern in ZERO_OUTPUT_PATTERNS
        )

        assert has_zero_output, (
            f"Property 8a FAILED: First 200 characters do not contain a "
            f"zero-output directive.\n"
            f"First 200 chars: '{first_200}'\n"
            f"Expected one of patterns: {ZERO_OUTPUT_PATTERNS}\n"
            f"(path tested: '{path}')"
        )

    @given(path=st_project_relative_path())
    @settings(max_examples=20)
    def test_property_8b_output_format_section_exists_with_zero_token_directive(
        self, path: str
    ):
        """For any project-relative file path, an OUTPUT FORMAT section SHALL
        exist containing a zero-token directive.

        **Validates: Requirements 6.1, 6.4**

        The closing OUTPUT FORMAT section reiterates the zero-token directive
        after all CHECK sections, providing dual reinforcement.
        """
        prompt = load_hook_prompt()

        # OUTPUT FORMAT section must exist
        assert "OUTPUT FORMAT" in prompt, (
            f"Property 8b FAILED: Prompt does not contain 'OUTPUT FORMAT' section.\n"
            f"(path tested: '{path}')"
        )

        # OUTPUT FORMAT must appear after all CHECK sections
        last_check_pos = max(
            prompt.rfind("CHECK 1"),
            prompt.rfind("CHECK 2"),
            prompt.rfind("CHECK 3"),
            prompt.rfind("CHECK 4"),
        )
        output_format_pos = prompt.find("OUTPUT FORMAT")
        assert output_format_pos > last_check_pos, (
            f"Property 8b FAILED: OUTPUT FORMAT section does not appear after "
            f"all CHECK sections.\n"
            f"OUTPUT FORMAT at position {output_format_pos}, "
            f"last CHECK at position {last_check_pos}\n"
            f"(path tested: '{path}')"
        )

        # OUTPUT FORMAT section must contain a zero-token directive
        output_section = extract_output_format_section(prompt)
        has_zero_token = any(
            re.search(pattern, output_section, re.IGNORECASE)
            for pattern in [r"zero tokens", r"ZERO tokens"]
        )

        assert has_zero_token, (
            f"Property 8b FAILED: OUTPUT FORMAT section does not contain a "
            f"zero-token directive.\n"
            f"OUTPUT FORMAT section: '{output_section[:200]}...'\n"
            f"(path tested: '{path}')"
        )

    @given(
        forbidden_phrase=st.sampled_from(FORBIDDEN_NARRATION_PHRASES),
    )
    @settings(max_examples=20)
    def test_property_8c_fast_path_passes_in_forbidden_list(
        self, forbidden_phrase: str
    ):
        """For any forbidden narration phrase, it SHALL appear in a FORBIDDEN
        output list within the prompt. Specifically, "Fast path passes" must
        be explicitly prohibited.

        **Validates: Requirements 6.2, 6.4**

        The FORBIDDEN list enumerates phrases the agent must never produce,
        ensuring "Fast path passes" narration is suppressed.
        """
        prompt = load_hook_prompt()

        # The prompt must contain a FORBIDDEN section
        assert "FORBIDDEN" in prompt, (
            f"Property 8c FAILED: Prompt does not contain a 'FORBIDDEN' section.\n"
            f"(tested with phrase: '{forbidden_phrase}')"
        )

        # The forbidden phrase must appear in the prompt
        assert forbidden_phrase in prompt, (
            f"Property 8c FAILED: Forbidden phrase '{forbidden_phrase}' does not "
            f"appear in the prompt.\n"
            f"(tested with phrase: '{forbidden_phrase}')"
        )

        # Specifically verify "Fast path passes" is in the FORBIDDEN list area
        if forbidden_phrase == "Fast path passes":
            # Find the FORBIDDEN section and verify the phrase is within it
            forbidden_section = extract_forbidden_list(prompt)
            assert "Fast path passes" in forbidden_section, (
                f"Property 8c FAILED: 'Fast path passes' is not in the FORBIDDEN "
                f"output list section.\n"
                f"FORBIDDEN section: '{forbidden_section[:300]}'\n"
            )
