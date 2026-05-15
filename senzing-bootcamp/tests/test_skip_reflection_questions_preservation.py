"""Preservation property tests for skip-reflection-questions bugfix.

These tests verify that non-reflection content remains intact in the steering
files. They follow observation-first methodology: we read the actual steering
files and assert the observed structure of preserved sections.

These tests MUST PASS on UNFIXED code (they establish the preservation baseline)
and MUST CONTINUE TO PASS after the fix is applied.

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


def _extract_section(markdown: str, heading: str) -> str:
    """Extract a section by its exact heading text.

    Returns content from the heading to the next same-level or higher heading,
    skipping headings that appear inside fenced code blocks.
    """
    level = heading.count("#")
    escaped_heading = re.escape(heading.strip())
    pattern = re.compile(rf"^{escaped_heading}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()
    text_after = markdown[match.end():]

    # Walk through lines after the heading, tracking code block state
    in_code_block = False
    end_pos = len(markdown)

    for line_match in re.finditer(r"^(.*)$", text_after, re.MULTILINE):
        line = line_match.group(1)

        # Toggle code block state on fence lines
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Only match headings outside code blocks
        if not in_code_block and re.match(rf"^#{{1,{level}}} ", line):
            end_pos = match.end() + line_match.start()
            break

    return markdown[start:end_pos]


def _extract_step_by_heading(markdown: str, step_number: int) -> str:
    """Extract a step section from a steering file by heading number.

    Steps are formatted as ``### Step N:`` headings.
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


# ---------------------------------------------------------------------------
# Preserved sections registry
# ---------------------------------------------------------------------------

# Each entry: (section_key, file, heading_or_marker, expected_content_patterns)
# These are the sections that MUST remain intact after the fix.

PRESERVED_SECTIONS_MODULE_COMPLETION: dict[str, dict] = {
    "bootcamp_journal": {
        "heading": "## Bootcamp Journal",
        "expected_patterns": [
            r"\*\*What we did:\*\*",
            r"\*\*What was produced:\*\*",
            r"\*\*Why it matters:\*\*",
        ],
        "description": "Journal template with module name, date, what we did, what was produced, why it matters",
    },
    "module_completion_certificate": {
        "heading": "## Module Completion Certificate",
        "expected_patterns": [
            r"Certificate Template",
            r"Module \[N\]",
            r"Key Concepts Learned",
            r"Artifacts Produced",
        ],
        "description": "Certificate section with full template",
    },
    "next_step_options": {
        "heading": "## Next-Step Options",
        "expected_patterns": [
            r"\*\*Proceed:\*\*",
            r"\*\*Iterate:\*\*",
            r"\*\*Explore:\*\*",
            r"\*\*Undo:\*\*",
            r"\*\*Share:\*\*",
        ],
        "description": "Next-step options with all five choices (Proceed, Iterate, Explore, Undo, Share)",
    },
    "immediate_execution": {
        "heading": "### ⛔ Immediate Execution on Affirmative Response",
        "expected_patterns": [
            r"PROHIBITED",
            r"Intermediate acknowledgment",
            r"Progress-saving behavior",
            r"Session-ending behavior",
        ],
        "description": "Immediate execution rules with PROHIBITED list",
    },
    "path_completion_detection": {
        "heading": "## Path Completion Detection",
        "expected_patterns": [
            r"Track.*Complete after",
            r"Module 7",
            r"Module 11",
        ],
        "description": "Path completion detection table with Core Bootcamp and Advanced Topics tracks",
    },
    "path_completion_celebration": {
        "heading": "## Path Completion Celebration",
        "expected_patterns": [
            r"track is complete",
            r"Export option",
            r"Graduation offer",
        ],
        "description": "Path completion celebration section",
    },
}

PRESERVED_SECTIONS_MODULE_03_STEP12: dict[str, dict] = {
    "follow_module_completion_workflow": {
        "pattern": r"Follow the `module-completion\.md` workflow",
        "description": "Step 12 instruction to follow module-completion.md workflow",
    },
    "journal_entry": {
        "pattern": r"Journal entry",
        "description": "Step 12 instruction for journal entry",
    },
    "transition_to_module_4": {
        "pattern": r"Transition to Module 4",
        "description": "Step 12 instruction to transition to Module 4",
    },
}

# Strategy: generate random subsets of preserved section names
_all_completion_keys = list(PRESERVED_SECTIONS_MODULE_COMPLETION.keys())
_all_step12_keys = list(PRESERVED_SECTIONS_MODULE_03_STEP12.keys())

st_completion_subset = st.lists(
    st.sampled_from(_all_completion_keys),
    min_size=1,
    max_size=len(_all_completion_keys),
    unique=True,
)

st_step12_subset = st.lists(
    st.sampled_from(_all_step12_keys),
    min_size=1,
    max_size=len(_all_step12_keys),
    unique=True,
)


# ---------------------------------------------------------------------------
# Property Test: Preservation of module-completion.md sections
# ---------------------------------------------------------------------------


class TestModuleCompletionPreservation:
    """Property 2: Preservation — Module Completion Workflow Integrity.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

    For all preserved sections in module-completion.md, the structural content
    remains intact. Uses Hypothesis to generate random subsets of preserved
    section names and verify each exists with expected content.
    """

    @given(section_keys=st_completion_subset)
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_preserved_sections_intact(self, section_keys: list[str]) -> None:
        """For any subset of preserved sections, each section exists and
        contains its expected structural content."""
        content = _read_module_completion()

        for key in section_keys:
            section_info = PRESERVED_SECTIONS_MODULE_COMPLETION[key]
            heading = section_info["heading"]
            expected_patterns = section_info["expected_patterns"]
            description = section_info["description"]

            # Extract the section
            section_text = _extract_section(content, heading)
            assert section_text, (
                f"Preserved section '{heading}' not found in module-completion.md. "
                f"This section ({description}) must remain intact."
            )

            # Verify each expected pattern exists in the section
            for pattern in expected_patterns:
                match = re.search(pattern, section_text)
                assert match is not None, (
                    f"Preserved section '{heading}' is missing expected content "
                    f"matching pattern '{pattern}'. "
                    f"Section description: {description}"
                )


# ---------------------------------------------------------------------------
# Property Test: Preservation of module-03 step 12 instructions
# ---------------------------------------------------------------------------


class TestModule03Step12Preservation:
    """Property 2: Preservation — Module 03 Step 12 Workflow Integrity.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

    For all preserved instructions in module-03-system-verification.md step 12,
    the structural content remains intact. Uses Hypothesis to generate random
    subsets of preserved instruction names and verify each exists.
    """

    @given(instruction_keys=st_step12_subset)
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_step12_preserved_instructions_intact(
        self, instruction_keys: list[str]
    ) -> None:
        """For any subset of preserved step 12 instructions, each instruction
        exists in the step 12 section."""
        content = _read_module_03()
        step12 = _extract_step_by_heading(content, 12)
        assert step12, (
            "Step 12 section not found in module-03-system-verification.md"
        )

        for key in instruction_keys:
            instruction_info = PRESERVED_SECTIONS_MODULE_03_STEP12[key]
            pattern = instruction_info["pattern"]
            description = instruction_info["description"]

            match = re.search(pattern, step12)
            assert match is not None, (
                f"Preserved instruction '{key}' not found in step 12. "
                f"Expected pattern: '{pattern}'. "
                f"Description: {description}. "
                "This instruction must remain intact after the fix."
            )
