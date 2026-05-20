"""Bug condition exploration tests for missing-pointer-marker bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

The bug: Step 4c in onboarding-flow.md places the 👉 marker outside a quoted
string (``👉 "That was a lot of ground to cover..."``) rather than as an
explicit output format directive with the marker inside the template text.
This causes the agent to interpret the marker as a structural annotation
rather than a literal output requirement.

Feature: missing-pointer-marker
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_ONBOARDING_FILE = _BOOTCAMP_DIR / "steering" / "onboarding-flow.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POINTING_MARKER = "👉"


def _read_onboarding() -> str:
    """Read the full content of onboarding-flow.md."""
    return _ONBOARDING_FILE.read_text(encoding="utf-8")


def _extract_step_4c(markdown: str) -> str:
    """Extract the Step 4c (Comprehension Check) section.

    Returns everything from the ``### 4c.`` heading up to the next
    heading of the same or higher level.
    """
    pattern = re.compile(r"^(#{2,3})\s+4c\.\s", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""

    level = len(match.group(1))
    start = match.start()
    rest = markdown[match.end():]

    # Find the next heading of same or higher (fewer/equal #) level
    next_heading = re.compile(r"^#{1," + str(level) + r"}\s", re.MULTILINE)
    next_match = next_heading.search(rest)
    if next_match:
        end = match.end() + next_match.start()
    else:
        end = len(markdown)

    return markdown[start:end]


def _has_explicit_output_format_directive(step_content: str) -> bool:
    """Check if Step 4c contains an explicit output format directive.

    An explicit output format directive is an instruction that tells the
    agent its output MUST begin with 👉, such as:
    - "Your output MUST begin with 👉"
    - "Output exactly:" followed by a template containing 👉
    - "Format:" or "Output format:" with 👉 inside the template

    This is distinct from the current format where 👉 appears as a
    line-level annotation before a quoted string.
    """
    # Look for explicit format directives
    format_patterns = [
        r"(?i)output\s+(must|shall)\s+(begin|start)\s+with\s+.{0,5}👉",
        r"(?i)(output|format)\s*(exactly|format)?\s*:",
        r"(?i)must\s+(include|contain|begin|start)\s+.*👉.*prefix",
        r"(?i)👉\s+prefix\s+(is\s+)?(mandatory|required)",
        r"(?i)(mandatory|required)\s+.*👉\s+prefix",
    ]
    for pat in format_patterns:
        if re.search(pat, step_content):
            return True
    return False


def _has_pointer_inside_template(step_content: str) -> bool:
    """Check if the 👉 marker is inside the output template text.

    Returns True if the 👉 appears as part of the template/example output
    (inside quotes or a code block showing the expected output), rather
    than as an external annotation before a quoted string.

    The bug condition is: 👉 appears OUTSIDE the quoted string, like:
        👉 "That was a lot of ground to cover..."
    The fix should have 👉 INSIDE the template, like:
        "👉 That was a lot of ground to cover..."
    Or as part of an explicit output format block.
    """
    # Check if 👉 is inside a quoted string (part of the output text)
    # Pattern: quote char, then 👉 inside the quoted text
    inside_quotes = re.search(r'["""]👉\s', step_content)
    if inside_quotes:
        return True

    # Check if 👉 is in a code block showing expected output
    code_block_pattern = re.compile(r"```.*?\n(.*?)```", re.DOTALL)
    for block_match in code_block_pattern.finditer(step_content):
        if _POINTING_MARKER in block_match.group(1):
            return True

    # Check for explicit "Output:" or "Format:" line followed by 👉 in template
    output_line_pattern = re.compile(
        r"(?i)(output|format|example)\s*:.*\n.*👉", re.MULTILINE
    )
    if output_line_pattern.search(step_content):
        return True

    return False


def _has_paraphrase_constraint(step_content: str) -> bool:
    """Check if Step 4c contains a paraphrase constraint requiring 👉.

    A paraphrase constraint is an explicit instruction that if the agent
    reformulates/paraphrases the question, the 👉 prefix is still mandatory.
    """
    paraphrase_patterns = [
        r"(?i)paraphras.*👉",
        r"(?i)👉.*paraphras",
        r"(?i)reformulat.*👉",
        r"(?i)👉.*reformulat",
        r"(?i)(regardless|whether).*paraphras.*👉",
        r"(?i)(regardless|whether).*👉.*prefix",
        r"(?i)👉\s+prefix.*(regardless|whether|always|still|mandatory|required)",
        r"(?i)(always|still|mandatory|required).*👉.*(paraphras|reformulat|reword)",
    ]
    for pat in paraphrase_patterns:
        if re.search(pat, step_content):
            return True
    return False


def _marker_is_annotation_before_quoted_string(step_content: str) -> bool:
    """Check if the 👉 marker appears as an annotation before a quoted string.

    This is the bug condition: the marker is placed outside the quotes as
    a line-level annotation, like:
        👉 "That was a lot of ground to cover..."

    Returns True if this ambiguous pattern is found.
    """
    # Pattern: 👉 followed by optional whitespace then a quoted string
    annotation_pattern = re.compile(r'👉\s*["""]')
    return bool(annotation_pattern.search(step_content))


# ---------------------------------------------------------------------------
# Test — Bug Condition: Step 4c Missing Pointer Prefix
# ---------------------------------------------------------------------------


class TestStep4cMissingPointerPrefix:
    """Bug Condition Exploration — Step 4c Missing Pointer Prefix.

    **Validates: Requirements 1.1, 1.2**

    These tests parse the Step 4c (Comprehension Check) section from the
    UNFIXED onboarding-flow.md and verify that the instruction format
    unambiguously requires the 👉 prefix as part of the output template.

    On UNFIXED code, these tests are EXPECTED TO FAIL because:
    - The 👉 marker is outside the quoted string (annotation format)
    - No explicit output format directive exists
    - No paraphrase constraint requiring 👉 exists

    Bug condition: isBugCondition(input) where
        input.step == "4c" AND
        input.markerFormat == "annotation_before_quoted_string"
    """

    def test_step_4c_exists(self) -> None:
        """Precondition: Step 4c section exists in onboarding-flow.md."""
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

    def test_step_4c_has_explicit_output_format_directive(self) -> None:
        """Step 4c SHALL contain an explicit output format directive with 👉.

        The instruction must explicitly tell the agent that its output
        MUST begin with the 👉 prefix. On unfixed code, this will FAIL
        because no such directive exists — the 👉 is merely an annotation
        before a quoted string.
        """
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

        assert _has_explicit_output_format_directive(step_4c), (
            "Step 4c does NOT contain an explicit output format directive "
            "requiring the 👉 prefix. The current format places 👉 as an "
            "annotation before a quoted string, which the agent interprets "
            "as structural metadata rather than a literal output requirement.\n"
            f"Step 4c content:\n{step_4c[:600]}"
        )

    def test_step_4c_has_pointer_inside_template(self) -> None:
        """Step 4c SHALL have the 👉 marker inside the output template text.

        The 👉 must appear as part of the template/example output (inside
        quotes or a code block), not as an external annotation before a
        quoted string. On unfixed code, this will FAIL because the marker
        is outside the quotes.
        """
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

        assert _has_pointer_inside_template(step_4c), (
            "Step 4c has the 👉 marker OUTSIDE the output template (as an "
            "annotation before a quoted string). The marker should be INSIDE "
            "the template text to make it unambiguously part of the output.\n"
            "Current format: 👉 \"That was a lot of ground to cover...\"\n"
            "Expected: 👉 inside the template or explicit format directive.\n"
            f"Step 4c content:\n{step_4c[:600]}"
        )

    def test_step_4c_has_paraphrase_constraint(self) -> None:
        """Step 4c SHALL contain a paraphrase constraint requiring 👉.

        If the agent reformulates the comprehension check question, the
        👉 prefix must still be mandatory. On unfixed code, this will FAIL
        because no paraphrase constraint exists.
        """
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

        assert _has_paraphrase_constraint(step_4c), (
            "Step 4c does NOT contain a paraphrase constraint requiring the "
            "👉 prefix on reformulated questions. If the agent paraphrases "
            "the comprehension check question, there is no instruction "
            "mandating the 👉 prefix.\n"
            f"Step 4c content:\n{step_4c[:600]}"
        )

    def test_bug_condition_marker_is_fixed(self) -> None:
        """Confirm the bug condition is resolved: 👉 is NOT an annotation before a quoted string.

        The fix moved the 👉 marker inside the output template (code block)
        and added an explicit output format directive. This test confirms
        the ambiguous annotation pattern no longer exists.
        """
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

        assert not _marker_is_annotation_before_quoted_string(step_4c), (
            "Bug condition still present: 👉 appears as an annotation "
            "before a quoted string. The fix should place 👉 inside the "
            "output template or use an explicit format directive."
        )


# ---------------------------------------------------------------------------
# PBT — Bug Condition Identification
# ---------------------------------------------------------------------------

# The properties we check for Step 4c
_STEP_4C_PROPERTIES = [
    "explicit_output_format_directive",
    "pointer_inside_template",
    "paraphrase_constraint",
]


@st.composite
def st_step_4c_property(draw: st.DrawFn) -> str:
    """Generate a property name to check on Step 4c."""
    return draw(st.sampled_from(_STEP_4C_PROPERTIES))


class TestBugConditionProperty:
    """PBT — Bug Condition Property for Step 4c.

    **Validates: Requirements 1.1, 1.2**

    Use Hypothesis to generate property checks and verify that Step 4c
    satisfies all required properties for unambiguous 👉 prefix enforcement.
    On UNFIXED code, this will FAIL because none of the required properties
    are satisfied.
    """

    @given(prop=st_step_4c_property())
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow])
    def test_step_4c_satisfies_pointer_prefix_properties(self, prop: str) -> None:
        """For any required property, Step 4c must satisfy it.

        Properties checked:
        - explicit_output_format_directive: An explicit instruction requiring 👉
        - pointer_inside_template: The 👉 marker inside the output template
        - paraphrase_constraint: A constraint requiring 👉 on paraphrases
        """
        content = _read_onboarding()
        step_4c = _extract_step_4c(content)
        assert step_4c, "Step 4c section not found in onboarding-flow.md"

        if prop == "explicit_output_format_directive":
            assert _has_explicit_output_format_directive(step_4c), (
                f"Property '{prop}' NOT satisfied: Step 4c lacks an explicit "
                f"output format directive requiring the 👉 prefix."
            )
        elif prop == "pointer_inside_template":
            assert _has_pointer_inside_template(step_4c), (
                f"Property '{prop}' NOT satisfied: Step 4c has the 👉 marker "
                f"outside the output template (annotation before quoted string)."
            )
        elif prop == "paraphrase_constraint":
            assert _has_paraphrase_constraint(step_4c), (
                f"Property '{prop}' NOT satisfied: Step 4c lacks a paraphrase "
                f"constraint requiring 👉 on reformulated questions."
            )
