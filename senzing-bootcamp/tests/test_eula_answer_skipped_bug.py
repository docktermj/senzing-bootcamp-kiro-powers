"""Bug condition exploration tests for eula-answer-skipped bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests 1-4 are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: eula-answer-skipped
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
_MODULE_02 = _BOOTCAMP_DIR / "steering" / "module-02-sdk-setup.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POINTING_MARKER = "👉"

_STOP_KEYWORDS = re.compile(
    r"STOP|stop\s+and\s+wait|wait\s+for\s+(the\s+)?bootcamper|"
    r"do\s+not\s+proceed|must\s+stop|stop\s+here",
    re.IGNORECASE,
)

_EULA_QUESTION_KEYWORDS = re.compile(
    r"accept.*EULA|EULA.*accept",
    re.IGNORECASE,
)

_DECLINE_KEYWORDS = re.compile(
    r"decline|cannot\s+be\s+used|without\s+EULA\s+acceptance",
    re.IGNORECASE,
)


def _read_module_02() -> str:
    """Read the full content of module-02-sdk-setup.md."""
    return _MODULE_02.read_text(encoding="utf-8")


def _extract_step_by_heading(markdown: str, step_number: int) -> str:
    """Extract a step section from the module-02 steering file by heading.

    Steps are formatted as ``## Step N: Title`` headings.

    Returns the full text of the step from its heading to the next
    ``## Step`` heading or end of file.
    """
    step_pattern = re.compile(
        rf"^## Step {step_number}:",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next ## Step heading or ## section heading
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _step_contains_eula_question(step_content: str) -> bool:
    """Check if a step section contains the EULA acceptance question."""
    return bool(_EULA_QUESTION_KEYWORDS.search(step_content))


# ---------------------------------------------------------------------------
# Test 1 — Missing 👉 Marker
# ---------------------------------------------------------------------------


class TestMissingPointingMarker:
    """Test 1 — Missing 👉 Marker.

    **Validates: Requirements 1.1, 1.2**

    Parse module-02-sdk-setup.md, extract Step 3, and assert the EULA
    acceptance question text contains the 👉 marker prefix. On unfixed
    content this will FAIL because no marker exists.
    """

    def test_step3_eula_question_has_pointing_marker(self) -> None:
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 section not found in module-02-sdk-setup.md"
        assert _step_contains_eula_question(step3), (
            "Step 3 does not contain the EULA acceptance question"
        )
        assert _POINTING_MARKER in step3, (
            "Step 3 EULA acceptance question does not contain the 👉 marker. "
            "The ask-bootcamper hook cannot detect this as a pending question. "
            f"Step 3 content:\n{step3[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing STOP Instruction
# ---------------------------------------------------------------------------


class TestMissingStopInstruction:
    """Test 2 — Missing STOP Instruction.

    **Validates: Requirements 1.1, 1.3**

    Parse module-02-sdk-setup.md, extract Step 3, and assert it
    contains an explicit stop/wait instruction after the EULA question
    telling the agent to STOP and wait for the bootcamper's response.
    On unfixed content this will FAIL because no stop instruction exists.
    """

    def test_step3_contains_stop_instruction(self) -> None:
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 section not found in module-02-sdk-setup.md"
        assert _step_contains_eula_question(step3), (
            "Step 3 does not contain the EULA acceptance question"
        )
        assert _STOP_KEYWORDS.search(step3), (
            "Step 3 does not contain an explicit stop/wait instruction after the "
            "EULA question. The agent has no instruction to stop and wait for the "
            f"bootcamper's response. Step 3 content:\n{step3[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing Decline Handling
# ---------------------------------------------------------------------------


class TestMissingDeclineHandling:
    """Test 3 — Missing Decline Handling.

    **Validates: Requirements 1.4**

    Parse module-02-sdk-setup.md, extract Step 3, and assert it contains
    EULA decline handling logic. On unfixed content this will FAIL because
    there is no decline path.
    """

    def test_step3_contains_decline_handling(self) -> None:
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 section not found in module-02-sdk-setup.md"
        assert _DECLINE_KEYWORDS.search(step3), (
            "Step 3 does not contain EULA decline handling logic. "
            "There is no path for the bootcamper to decline the EULA. "
            f"Step 3 content:\n{step3[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Unconditional Checkpoint
# ---------------------------------------------------------------------------


class TestUnconditionalCheckpoint:
    """Test 4 — Unconditional Checkpoint.

    **Validates: Requirements 1.4**

    Parse module-02-sdk-setup.md, extract Step 3, and assert the
    checkpoint is deferred until after EULA acceptance — not placed
    unconditionally after the question. On unfixed content this will
    FAIL because the checkpoint is unconditional.
    """

    def test_step3_checkpoint_is_deferred(self) -> None:
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 section not found in module-02-sdk-setup.md"

        # Find the EULA question and the checkpoint
        eula_match = _EULA_QUESTION_KEYWORDS.search(step3)
        assert eula_match, "Step 3 does not contain the EULA acceptance question"

        checkpoint_match = re.search(r"\*\*Checkpoint:\*\*", step3)
        assert checkpoint_match, "Step 3 does not contain a checkpoint"

        # The text between the EULA question and the checkpoint should contain
        # a stop/wait instruction or conditional logic that defers the checkpoint.
        # On unfixed code, the checkpoint appears unconditionally after the
        # question with no stop instruction in between.
        text_between = step3[eula_match.end():checkpoint_match.start()]

        has_stop = bool(_STOP_KEYWORDS.search(text_between))
        has_conditional = bool(
            re.search(
                r"(after|once|when).*(accept|respond|answer|reply|input)",
                text_between,
                re.IGNORECASE,
            )
        )

        assert has_stop or has_conditional, (
            "Step 3 checkpoint is not deferred — it appears unconditionally after "
            "the EULA question with no stop instruction or conditional logic in "
            "between. The agent writes the checkpoint before the bootcamper "
            f"responds. Text between question and checkpoint:\n{text_between[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Identification
# ---------------------------------------------------------------------------

_ALL_STEP_NUMBERS = list(range(1, 10))  # Steps 1 through 9


@st.composite
def st_step_number(draw: st.DrawFn) -> int:
    """Generate a step number from 1 to 9."""
    return draw(st.sampled_from(_ALL_STEP_NUMBERS))


class TestBugConditionIdentification:
    """PBT Test — Bug Condition Identification.

    **Validates: Requirements 1.1, 1.2**

    Use Hypothesis to generate step numbers (1–9) and verify that only
    Step 3 contains the EULA question, and that Step 3 has the 👉 marker.
    Will FAIL on unfixed code for Step 3 (marker is missing).
    """

    @given(step_num=st_step_number())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_only_step3_requires_eula_marker(self, step_num: int) -> None:
        """For any step number, only Step 3 should contain the EULA question."""
        content = _read_module_02()
        step_content = _extract_step_by_heading(content, step_num)

        if not step_content:
            # Step doesn't exist in the file — nothing to check
            return

        has_eula_question = _step_contains_eula_question(step_content)
        has_marker = _POINTING_MARKER in step_content

        if step_num == 3:
            # Step 3 contains the EULA question — it MUST have the 👉 marker
            assert has_eula_question, (
                "Step 3 should contain the EULA acceptance question"
            )
            assert has_marker, (
                f"Step {step_num} contains the EULA acceptance question but "
                f"lacks the 👉 marker. The ask-bootcamper hook cannot detect "
                f"this as a pending question."
            )
        else:
            # Non-Step-3 steps should not contain a EULA question without 👉
            if has_eula_question:
                assert has_marker, (
                    f"Step {step_num} unexpectedly contains a EULA acceptance "
                    f"question without the 👉 marker."
                )
