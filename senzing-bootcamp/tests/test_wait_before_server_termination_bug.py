"""Bug condition exploration tests for wait-before-server-termination bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: wait-before-server-termination
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
_VISUALIZATION_GUIDE = _BOOTCAMP_DIR / "steering" / "visualization-guide.md"
_MODULE_03_PHASE2 = _BOOTCAMP_DIR / "steering" / "module-03-phase2-visualization.md"
_MODULE_03_SYSTEM = _BOOTCAMP_DIR / "steering" / "module-03-system-verification.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP_EMOJI = "🛑"

_WAIT_KEYWORDS = re.compile(
    r"wait\s+for.*(bootcamper|user|confirm)|"
    r"(bootcamper|user)\s+(confirm|respond|input)|"
    r"let\s+me\s+know\s+when|"
    r"have\s+you\s+finished\s+exploring|"
    r"ready\s+and\s+I.ll\s+(continue|clean)",
    re.IGNORECASE,
)

_CONFIRMATION_GATE_KEYWORDS = re.compile(
    r"(confirm|ask|prompt).*(before|prior).*(terminat|cleanup|clean\s+up)|"
    r"(before|prior).*(terminat|cleanup|clean\s+up).*(confirm|ask|prompt)|"
    r"have\s+you\s+finished\s+exploring|"
    r"let\s+me\s+know\s+when\s+you.re\s+ready",
    re.IGNORECASE,
)


def _read_file(path: Path) -> str:
    """Read the full content of a steering file."""
    return path.read_text(encoding="utf-8")


def _extract_web_service_delivery_sequence(content: str) -> str:
    """Extract the Web Service Delivery Sequence section from visualization-guide.md."""
    pattern = re.compile(
        r"^## Web Service Delivery Sequence\s*\n",
        re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # Find the next ## heading or end of file
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(content, match.end())
    if next_match:
        return content[start:next_match.start()]

    return content[start:]


def _extract_step_94_section3(content: str) -> str:
    """Extract Step 9.4 section 3 ('Present to bootcamper') from module-03-phase2.

    Looks for the numbered item '3. **Present to bootcamper:**' within the 9.4 section.
    """
    # Find the 9.4 heading
    heading_pattern = re.compile(r"^###\s+9\.4\b", re.MULTILINE)
    heading_match = heading_pattern.search(content)
    if not heading_match:
        return ""

    section_start = heading_match.start()

    # Find the next ### heading to bound the 9.4 section
    next_heading = re.compile(r"^###\s+", re.MULTILINE)
    next_match = next_heading.search(content, heading_match.end())
    section_94 = content[section_start:next_match.start()] if next_match else content[section_start:]

    # Find item 3 within 9.4 — "3. **Present to bootcamper"
    item3_pattern = re.compile(r"^3\.\s+\*\*Present\s+to\s+bootcamper", re.MULTILINE)
    item3_match = item3_pattern.search(section_94)
    if not item3_match:
        return ""

    item3_start = item3_match.start()

    # Find item 4 or end of section
    item4_pattern = re.compile(r"^4\.\s+\*\*", re.MULTILINE)
    item4_match = item4_pattern.search(section_94, item3_match.end())
    if item4_match:
        return section_94[item3_start:item4_match.start()]

    return section_94[item3_start:]


def _extract_step_11(content: str) -> str:
    """Extract Step 11 from module-03-system-verification.md."""
    pattern = re.compile(r"^### Step 11:", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # Find the next ### heading or end of file
    next_heading = re.compile(r"^### ", re.MULTILINE)
    next_match = next_heading.search(content, match.end())
    if next_match:
        return content[start:next_match.start()]

    return content[start:]


def _count_numbered_steps(section: str) -> list[str]:
    """Extract numbered steps (1. **...**) from a section."""
    return re.findall(r"^\d+\.\s+\*\*.*?\*\*", section, re.MULTILINE)


# ---------------------------------------------------------------------------
# Test 1 — Missing "wait for user" step in Web Service Delivery Sequence
# ---------------------------------------------------------------------------


class TestMissingWaitStepInDeliverySequence:
    """Test 1 — Missing wait-for-user step in Web Service Delivery Sequence.

    **Validates: Requirements 1.1, 2.1**

    Parse visualization-guide.md, extract the Web Service Delivery Sequence,
    and assert it contains a "wait for user confirmation" step between
    present (step 3) and fallback. On unfixed code this will FAIL because
    the sequence goes directly from present to fallback with no wait step.
    """

    def test_delivery_sequence_has_wait_step(self) -> None:
        content = _read_file(_VISUALIZATION_GUIDE)
        sequence = _extract_web_service_delivery_sequence(content)
        assert sequence, (
            "Web Service Delivery Sequence section not found in visualization-guide.md"
        )

        # The sequence should contain a step that instructs the agent to wait
        # for user confirmation after presenting the URL
        has_wait = bool(_WAIT_KEYWORDS.search(sequence))
        has_stop = _STOP_EMOJI in sequence

        assert has_wait and has_stop, (
            "Web Service Delivery Sequence does not contain a 'wait for user "
            "confirmation' step with a STOP directive. The sequence goes directly "
            "from step 3 (present) to step 4 (fallback) with no wait step.\n"
            f"Contains wait keywords: {has_wait}\n"
            f"Contains 🛑 STOP: {has_stop}\n"
            f"Sequence content:\n{sequence[:800]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing 🛑 STOP in Step 9.4 section 3
# ---------------------------------------------------------------------------


class TestMissingStopInStep94:
    """Test 2 — Missing 🛑 STOP directive in Step 9.4 section 3.

    **Validates: Requirements 1.2, 2.2**

    Parse module-03-phase2-visualization.md, extract Step 9.4 section 3
    ('Present to bootcamper'), and assert it contains a 🛑 STOP directive
    after the URL presentation bullets. On unfixed code this will FAIL
    because no STOP directive exists.
    """

    def test_step94_section3_has_stop_directive(self) -> None:
        content = _read_file(_MODULE_03_PHASE2)
        section3 = _extract_step_94_section3(content)
        assert section3, (
            "Step 9.4 section 3 ('Present to bootcamper') not found in "
            "module-03-phase2-visualization.md"
        )

        assert _STOP_EMOJI in section3, (
            "Step 9.4 section 3 does not contain a 🛑 STOP directive after "
            "the URL presentation. The agent has no instruction to stop and "
            "wait for the bootcamper to finish exploring.\n"
            f"Section 3 content:\n{section3[:800]}"
        )

    def test_step94_section3_has_wait_prompt(self) -> None:
        content = _read_file(_MODULE_03_PHASE2)
        section3 = _extract_step_94_section3(content)
        assert section3, (
            "Step 9.4 section 3 ('Present to bootcamper') not found in "
            "module-03-phase2-visualization.md"
        )

        assert _WAIT_KEYWORDS.search(section3), (
            "Step 9.4 section 3 does not contain a wait/confirmation prompt "
            "after the URL presentation. The agent proceeds without asking "
            "the bootcamper if they are done exploring.\n"
            f"Section 3 content:\n{section3[:800]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing confirmation gate in Step 11
# ---------------------------------------------------------------------------


class TestMissingConfirmationGateStep11:
    """Test 3 — Missing user confirmation gate in Step 11.

    **Validates: Requirements 1.2, 1.3, 2.3**

    Parse module-03-system-verification.md, extract Step 11, and assert it
    contains a user confirmation prompt before the termination logic. On
    unfixed code this will FAIL because Step 11 begins directly with
    'Terminate the web service' with no confirmation gate.
    """

    def test_step11_has_confirmation_before_termination(self) -> None:
        content = _read_file(_MODULE_03_SYSTEM)
        step11 = _extract_step_11(content)
        assert step11, (
            "Step 11 not found in module-03-system-verification.md"
        )

        # The confirmation gate should appear BEFORE the termination instruction
        termination_pattern = re.compile(
            r"Terminate\s+the\s+web\s+service",
            re.IGNORECASE,
        )
        termination_match = termination_pattern.search(step11)
        assert termination_match, (
            "Step 11 does not contain 'Terminate the web service' instruction"
        )

        # Check for confirmation keywords BEFORE the termination instruction
        text_before_termination = step11[:termination_match.start()]

        has_confirmation = bool(_CONFIRMATION_GATE_KEYWORDS.search(text_before_termination))
        has_wait = bool(_WAIT_KEYWORDS.search(text_before_termination))

        assert has_confirmation or has_wait, (
            "Step 11 does not contain a user confirmation gate before the "
            "termination logic. The agent proceeds directly to 'Terminate the "
            "web service' without asking the bootcamper if they have finished "
            "exploring.\n"
            f"Text before termination:\n{text_before_termination[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Localized to Specific Insertion Points
# ---------------------------------------------------------------------------

_FILE_INDICES = [0, 1, 2]  # 0=visualization-guide, 1=phase2, 2=system-verification

_FILES = [_VISUALIZATION_GUIDE, _MODULE_03_PHASE2, _MODULE_03_SYSTEM]


@st.composite
def st_file_index(draw: st.DrawFn) -> int:
    """Generate a file index across the three affected steering files."""
    return draw(st.sampled_from(_FILE_INDICES))


class TestBugConditionLocalization:
    """PBT Test — Bug Condition Localized to Specific Insertion Points.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

    Use Hypothesis to generate random file indices across the three files
    and verify the bug condition (missing STOP/wait/confirmation) is present
    at the specific insertion points in each file.
    """

    @given(file_idx=st_file_index())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_bug_condition_exists_at_insertion_points(self, file_idx: int) -> None:
        """For any of the three files, the bug condition exists at the insertion point."""
        file_path = _FILES[file_idx]
        content = _read_file(file_path)

        if file_idx == 0:
            # visualization-guide.md — delivery sequence missing wait step
            sequence = _extract_web_service_delivery_sequence(content)
            assert sequence, "Web Service Delivery Sequence not found"

            has_wait = bool(_WAIT_KEYWORDS.search(sequence))
            has_stop = _STOP_EMOJI in sequence

            assert has_wait and has_stop, (
                f"Bug condition confirmed in {file_path.name}: "
                "Web Service Delivery Sequence has no wait-for-user step "
                "with STOP directive between present and fallback."
            )

        elif file_idx == 1:
            # module-03-phase2-visualization.md — Step 9.4 section 3 missing STOP
            section3 = _extract_step_94_section3(content)
            assert section3, "Step 9.4 section 3 not found"

            assert _STOP_EMOJI in section3, (
                f"Bug condition confirmed in {file_path.name}: "
                "Step 9.4 section 3 has no 🛑 STOP directive after URL presentation."
            )

        elif file_idx == 2:
            # module-03-system-verification.md — Step 11 missing confirmation gate
            step11 = _extract_step_11(content)
            assert step11, "Step 11 not found"

            termination_match = re.search(
                r"Terminate\s+the\s+web\s+service", step11, re.IGNORECASE
            )
            assert termination_match, "Step 11 missing termination instruction"

            text_before = step11[:termination_match.start()]
            has_gate = bool(
                _CONFIRMATION_GATE_KEYWORDS.search(text_before)
                or _WAIT_KEYWORDS.search(text_before)
            )

            assert has_gate, (
                f"Bug condition confirmed in {file_path.name}: "
                "Step 11 has no user confirmation gate before termination."
            )
