"""Bug condition exploration tests for agent-skips-git-question bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests 1-3 are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: agent-skips-git-question
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_MODULE_01 = _BOOTCAMP_DIR / "steering" / "module-01-business-problem.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POINTING_MARKER = "👉"

_STOP_KEYWORDS = re.compile(
    r"STOP|stop\s+and\s+wait|wait\s+for\s+(the\s+)?bootcamper|"
    r"do\s+not\s+proceed|must\s+stop|stop\s+here",
    re.IGNORECASE,
)

_GIT_QUESTION_KEYWORDS = re.compile(
    r"(initialize|init)\s+(a\s+)?git\s+repo",
    re.IGNORECASE,
)


def _read_module_01() -> str:
    """Read the full content of module-01-business-problem.md."""
    return _MODULE_01.read_text(encoding="utf-8")


def _extract_step(markdown: str, step_number: int) -> str:
    """Extract a numbered step section from the module-01 steering file.

    Steps are formatted as top-level numbered items like:
    ``1. **Step title** ...``

    Returns the full text of the step from its number to the next step
    or end of file.
    """
    # Match patterns like "1. **Initialize version control**"
    step_pattern = re.compile(
        rf"^{step_number}\.\s+\*\*",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next step (next_number. **...)
    next_step_pattern = re.compile(
        rf"^{step_number + 1}\.\s+\*\*",
        re.MULTILINE,
    )
    next_match = next_step_pattern.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    # If no next step, go to end but stop at Phase 2 reference or EOF
    phase2_pattern = re.compile(r"^\*\*Phase 2", re.MULTILINE)
    phase2_match = phase2_pattern.search(markdown, start + 1)
    if phase2_match:
        return markdown[start:phase2_match.start()]

    return markdown[start:]


def _step_contains_git_question(step_content: str) -> bool:
    """Check if a step section contains the git initialization question."""
    return bool(_GIT_QUESTION_KEYWORDS.search(step_content))


# ---------------------------------------------------------------------------
# Test 1 — Missing 👉 Marker
# ---------------------------------------------------------------------------


class TestMissingPointingMarker:
    """Test 1 — Missing 👉 Marker.

    **Validates: Requirements 1.1, 1.2**

    Parse module-01-business-problem.md, extract Step 1, and assert the git
    initialization question text contains the 👉 marker prefix. On unfixed
    content this will FAIL because no marker exists.
    """

    def test_step1_git_question_has_pointing_marker(self) -> None:
        content = _read_module_01()
        step1 = _extract_step(content, 1)
        assert step1, "Step 1 section not found in module-01-business-problem.md"
        assert _step_contains_git_question(step1), (
            "Step 1 does not contain the git initialization question"
        )
        assert _POINTING_MARKER in step1, (
            "Step 1 git initialization question does not contain the 👉 marker. "
            "The ask-bootcamper hook cannot detect this as a pending question. "
            f"Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Stop Instruction
# ---------------------------------------------------------------------------


class TestMissingStopInstruction:
    """Test 2 — Missing Stop Instruction.

    **Validates: Requirements 1.1, 1.3**

    Parse module-01-business-problem.md, extract Step 1, and assert it
    contains an explicit stop/wait instruction after the git question telling
    the agent to STOP and wait for the bootcamper's response. On unfixed
    content this will FAIL because no stop instruction exists.
    """

    def test_step1_contains_stop_instruction(self) -> None:
        content = _read_module_01()
        step1 = _extract_step(content, 1)
        assert step1, "Step 1 section not found in module-01-business-problem.md"
        assert _step_contains_git_question(step1), (
            "Step 1 does not contain the git initialization question"
        )
        assert _STOP_KEYWORDS.search(step1), (
            "Step 1 does not contain an explicit stop/wait instruction after the "
            "git question. The agent has no instruction to stop and wait for the "
            f"bootcamper's response. Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Premature Checkpoint
# ---------------------------------------------------------------------------


class TestPrematureCheckpoint:
    """Test 3 — Premature Checkpoint.

    **Validates: Requirements 1.3**

    Parse module-01-business-problem.md, extract Step 1, and assert the
    checkpoint is deferred until after the bootcamper responds. The checkpoint
    should NOT appear unconditionally right after the question — it should be
    conditional on the response path. On unfixed content this will FAIL
    because the checkpoint is unconditional.
    """

    def test_step1_checkpoint_is_deferred(self) -> None:
        content = _read_module_01()
        step1 = _extract_step(content, 1)
        assert step1, "Step 1 section not found in module-01-business-problem.md"

        # Find the git question and the checkpoint
        git_q_match = _GIT_QUESTION_KEYWORDS.search(step1)
        assert git_q_match, "Step 1 does not contain the git initialization question"

        checkpoint_match = re.search(r"\*\*Checkpoint:\*\*", step1)
        assert checkpoint_match, "Step 1 does not contain a checkpoint"

        # The text between the git question and the checkpoint should contain
        # a stop/wait instruction or conditional logic that defers the checkpoint.
        # On unfixed code, the checkpoint appears unconditionally after the
        # question with no stop instruction in between.
        text_between = step1[git_q_match.end():checkpoint_match.start()]

        has_stop = bool(_STOP_KEYWORDS.search(text_between))
        has_conditional_checkpoint = bool(
            re.search(r"(after|once|when).*(respond|answer|reply|input)", text_between, re.IGNORECASE)
        )

        assert has_stop or has_conditional_checkpoint, (
            "Step 1 checkpoint is not deferred — it appears unconditionally after "
            "the git question with no stop instruction or conditional logic in between. "
            "The agent writes the checkpoint before the bootcamper responds. "
            f"Text between question and checkpoint:\n{text_between[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Identification
# ---------------------------------------------------------------------------

_ALL_STEP_NUMBERS = list(range(1, 9))  # Steps 1 through 8


@st.composite
def st_step_number(draw: st.DrawFn) -> int:
    """Generate a step number from 1 to 8."""
    return draw(st.sampled_from(_ALL_STEP_NUMBERS))


class TestBugConditionIdentification:
    """PBT Test — Bug Condition Identification.

    **Validates: Requirements 1.1, 1.2**

    Use Hypothesis to generate step numbers (1–8) and verify that only Step 1
    is the step requiring the 👉 git question marker. All other steps should
    not contain a git initialization question without 👉.
    """

    @given(step_num=st_step_number())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_only_step1_requires_git_question_marker(self, step_num: int) -> None:
        """For any step number, only Step 1 should contain the git question."""
        content = _read_module_01()
        step_content = _extract_step(content, step_num)

        if not step_content:
            # Step doesn't exist in the file — nothing to check
            return

        has_git_question = _step_contains_git_question(step_content)
        has_marker = _POINTING_MARKER in step_content

        if step_num == 1:
            # Step 1 contains the git question — it MUST have the 👉 marker
            assert has_git_question, (
                "Step 1 should contain the git initialization question"
            )
            assert has_marker, (
                f"Step {step_num} contains the git initialization question but "
                f"lacks the 👉 marker. The ask-bootcamper hook cannot detect "
                f"this as a pending question."
            )
        else:
            # Non-Step-1 steps should not contain a git question without 👉
            if has_git_question:
                assert has_marker, (
                    f"Step {step_num} unexpectedly contains a git initialization "
                    f"question without the 👉 marker."
                )
