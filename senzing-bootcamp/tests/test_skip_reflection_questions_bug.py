"""Bug condition exploration tests for skip-reflection-questions bugfix.

These tests parse the UNFIXED steering files and assert the expected behavior
(no reflection questions). They are EXPECTED TO FAIL on unfixed code — failure
confirms the bug exists.

Feature: skip-reflection-questions
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
_MODULE_COMPLETION = _BOOTCAMP_DIR / "steering" / "module-completion.md"
_MODULE_03 = _BOOTCAMP_DIR / "steering" / "module-03-system-verification.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_module_completion() -> str:
    """Read the full content of module-completion.md."""
    return _MODULE_COMPLETION.read_text(encoding="utf-8")


def _read_module_03() -> str:
    """Read the full content of module-03-system-verification.md."""
    return _MODULE_03.read_text(encoding="utf-8")


def _extract_step_by_heading(markdown: str, step_number: int) -> str:
    """Extract a step section from a steering file by heading number.

    Steps are formatted as ``### Step N:`` headings.

    Returns the full text of the step from its heading to the next
    heading of the same or higher level, or end of file.
    """
    step_pattern = re.compile(
        rf"^### Step {step_number}:",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next ### or ## heading
    next_heading = re.compile(r"^##[#]? ", re.MULTILINE)
    next_match = next_heading.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a section by its exact heading text.

    Returns content from the heading to the next same-level or higher heading.
    """
    # Determine heading level from the heading string
    level = len(heading) - len(heading.lstrip("#"))
    escaped_heading = re.escape(heading.strip())
    pattern = re.compile(rf"^{escaped_heading}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find next heading at same or higher level
    next_pattern = re.compile(rf"^#{{1,{level}}} ", re.MULTILINE)
    next_match = next_pattern.search(markdown, match.end())
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _extract_success_criteria(markdown: str) -> str:
    """Extract the Success Criteria section from a steering file."""
    pattern = re.compile(r"^## Success Criteria\b", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find next ## heading
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end())
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


# ---------------------------------------------------------------------------
# Test 1 — Reflection Question Heading in module-completion.md
# ---------------------------------------------------------------------------


class TestReflectionQuestionHeading:
    """Test 1 — Reflection Question Heading Present.

    **Validates: Requirements 1.1**

    Parse module-completion.md and assert it does NOT contain a
    "## Reflection Question" heading. On unfixed code this will FAIL
    because the heading exists.
    """

    def test_module_completion_has_no_reflection_question_heading(self) -> None:
        content = _read_module_completion()
        reflection_heading = re.search(
            r"^## Reflection Question\b", content, re.MULTILINE
        )
        assert reflection_heading is None, (
            "module-completion.md contains a '## Reflection Question' heading "
            f"at line {content[:reflection_heading.start()].count(chr(10)) + 1}. "
            "The module completion workflow should NOT instruct the agent to "
            "present a reflection question."
        )


# ---------------------------------------------------------------------------
# Test 2 — Journal Template Takeaway Field
# ---------------------------------------------------------------------------


class TestJournalTemplateTakeaway:
    """Test 2 — Journal Template Takeaway Field.

    **Validates: Requirements 1.4**

    Parse module-completion.md journal template and assert "Bootcamper's
    takeaway" either does not exist or is auto-filled with "N/A".
    On unfixed code this will FAIL because the template contains a
    placeholder referencing the reflection question.
    """

    def test_journal_template_takeaway_omitted_or_na(self) -> None:
        content = _read_module_completion()

        # Find the takeaway line in the journal template
        takeaway_match = re.search(
            r"\*\*Bootcamper's takeaway:\*\*\s*(.*)",
            content,
        )

        if takeaway_match is None:
            # Takeaway field doesn't exist — this is acceptable (expected after fix)
            return

        takeaway_value = takeaway_match.group(1).strip()

        # If it exists, it should be "N/A" (auto-filled), not a placeholder
        assert takeaway_value.lower() == "n/a" or "reflection" not in takeaway_value.lower(), (
            "module-completion.md journal template contains "
            f"'**Bootcamper's takeaway:** {takeaway_value}' which references "
            "the reflection question. The takeaway field should either not exist "
            "or be auto-filled with 'N/A'."
        )


# ---------------------------------------------------------------------------
# Test 3 — Module 3 Step 12 Reflection Question Instruction
# ---------------------------------------------------------------------------


class TestModule3Step12ReflectionInstruction:
    """Test 3 — Module 3 Step 12 Reflection Question Instruction.

    **Validates: Requirements 1.2**

    Parse module-03-system-verification.md step 12 and assert it does NOT
    contain a "Reflection question:" instruction. On unfixed code this will
    FAIL because step 12 explicitly instructs the agent to present a
    reflection question.
    """

    def test_step12_has_no_reflection_question_instruction(self) -> None:
        content = _read_module_03()
        step12 = _extract_step_by_heading(content, 12)
        assert step12, "Step 12 section not found in module-03-system-verification.md"

        reflection_match = re.search(
            r"Reflection question:", step12, re.IGNORECASE
        )
        assert reflection_match is None, (
            "module-03-system-verification.md step 12 contains a "
            "'Reflection question:' instruction. The module close workflow "
            "should NOT instruct the agent to present a reflection question. "
            f"Found at: '{step12[reflection_match.start():reflection_match.start()+100]}'"
        )


# ---------------------------------------------------------------------------
# Test 4 — Module 3 Success Criteria Reflection Requirement
# ---------------------------------------------------------------------------


class TestModule3SuccessCriteriaReflection:
    """Test 4 — Module 3 Success Criteria Reflection Requirement.

    **Validates: Requirements 1.3**

    Parse module-03-system-verification.md success criteria and assert it
    does NOT contain "answered the reflection question". On unfixed code
    this will FAIL because the success criteria require a reflection answer.
    """

    def test_success_criteria_no_reflection_requirement(self) -> None:
        content = _read_module_03()
        success_criteria = _extract_success_criteria(content)
        assert success_criteria, (
            "Success Criteria section not found in module-03-system-verification.md"
        )

        reflection_match = re.search(
            r"answered the reflection question",
            success_criteria,
            re.IGNORECASE,
        )
        assert reflection_match is None, (
            "module-03-system-verification.md Success Criteria contains "
            "'answered the reflection question' as a completion condition. "
            "The success criteria should NOT require a reflection answer."
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Across All Modules
# ---------------------------------------------------------------------------


class TestBugConditionAcrossModules:
    """PBT Test — Bug Condition Across All Modules.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    Use Hypothesis to generate module numbers (1-11) and verify that for
    any module, the completion workflow does not instruct reflection questions.
    Will FAIL on unfixed code because module-completion.md applies to ALL
    modules and contains the reflection question section.
    """

    @given(module_num=st.integers(min_value=1, max_value=11))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_completion_workflow_has_no_reflection_for_any_module(
        self, module_num: int
    ) -> None:
        """For any module number 1-11, the completion workflow must not
        instruct reflection questions."""
        content = _read_module_completion()

        # The module-completion.md workflow applies to ALL modules.
        # Assert it does not contain a Reflection Question section.
        reflection_heading = re.search(
            r"^## Reflection Question\b", content, re.MULTILINE
        )
        assert reflection_heading is None, (
            f"Module {module_num}: module-completion.md contains a "
            "'## Reflection Question' heading. This workflow applies to all "
            "modules (1-11), so every module completion will present a "
            "reflection question. The workflow should skip reflection and "
            "proceed directly to the certificate and next-step options."
        )

        # Also verify the journal template doesn't wait for reflection input
        takeaway_match = re.search(
            r"\*\*Bootcamper's takeaway:\*\*\s*\[response to reflection question\]",
            content,
        )
        assert takeaway_match is None, (
            f"Module {module_num}: module-completion.md journal template contains "
            "'**Bootcamper's takeaway:** [response to reflection question]'. "
            "This placeholder implies the agent should collect a reflection "
            "response for every module completion."
        )
