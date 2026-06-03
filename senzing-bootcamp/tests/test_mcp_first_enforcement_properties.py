"""Property-based tests for MCP-first enforcement in module-05-phase1-quality-assessment.md.

Feature: mcp-first-enforcement

Validates that the steering file contains no hardcoded Entity Specification attributes
and uses download_resource MCP calls as the sole source of attribute information.
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_STEERING_FILE = _STEERING_DIR / "module-05-phase1-quality-assessment.md"

# Known Entity Specification attributes that should NOT appear inline
KNOWN_ENTITY_SPEC_ATTRIBUTES = {
    "NAME_FULL", "NAME_FIRST", "NAME_LAST", "NAME_ORG",
    "DATE_OF_BIRTH", "PASSPORT_NUMBER", "DRIVERS_LICENSE_NUMBER",
    "SSN_NUMBER", "NATIONAL_ID_NUMBER",
    "ADDR_FULL", "ADDR_LINE1", "ADDR_CITY", "ADDR_STATE",
    "ADDR_POSTAL_CODE", "PHONE_NUMBER", "EMAIL_ADDRESS",
    "WEBSITE_ADDRESS",
    "REL_ANCHOR_DOMAIN", "REL_ANCHOR_KEY",
    "REL_POINTER_DOMAIN", "REL_POINTER_KEY", "REL_POINTER_ROLE",
}

# Attributes that ARE allowed because they are structural/required field names
# referenced generically (e.g., "check if DATA_SOURCE and RECORD_ID are present")
ALLOWED_STRUCTURAL_REFS = {"DATA_SOURCE", "RECORD_ID"}

# Pattern matching numbered step boundaries: "N. **Title**"
_STEP_BOUNDARY_RE = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*", re.MULTILINE)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def extract_step_content(step_number: int) -> str:
    """Extract the content of a specific numbered step from the steering file.

    Parses the steering file at the known path and returns the full text content
    of the requested step, from its title line up to (but not including) the next
    step boundary or end of file.

    Args:
        step_number: The 1-based step number to extract (e.g., 3 for Step 3).

    Returns:
        The text content of the requested step, including its title line.

    Raises:
        FileNotFoundError: If the steering file does not exist.
        ValueError: If the requested step number is not found in the file.
    """
    content = _STEERING_FILE.read_text(encoding="utf-8")
    return _extract_step_from_content(content, step_number)


def _extract_step_from_content(content: str, step_number: int) -> str:
    """Extract step content from raw text by parsing numbered step boundaries.

    Args:
        content: The full steering file text.
        step_number: The 1-based step number to extract.

    Returns:
        The text content of the requested step.

    Raises:
        ValueError: If the requested step number is not found.
    """
    matches = list(_STEP_BOUNDARY_RE.finditer(content))

    target_match = None
    next_start = None

    for i, match in enumerate(matches):
        if int(match.group(1)) == step_number:
            target_match = match
            if i + 1 < len(matches):
                next_start = matches[i + 1].start()
            break

    if target_match is None:
        raise ValueError(
            f"Step {step_number} not found in steering file. "
            f"Available steps: {[int(m.group(1)) for m in matches]}"
        )

    start = target_match.start()
    step_text = content[start:next_start] if next_start else content[start:]
    return step_text


# ---------------------------------------------------------------------------
# Property 3: download_resource placement precedes Entity Specification references
# ---------------------------------------------------------------------------


class TestDownloadResourcePlacement:
    """Validates: Requirements 4.2

    Property 3: download_resource placement precedes Entity Specification references.

    For content in Step 3, the download_resource call instruction must appear before
    any reference to Entity Specification content usage (e.g., language about using
    the downloaded content as an authoritative reference).
    """

    # Pattern matching the download_resource call instruction
    _DOWNLOAD_CALL_RE = re.compile(r"download_resource\(", re.IGNORECASE)

    # Patterns matching references to using the Entity Specification content
    _USAGE_REFERENCE_PATTERNS = [
        re.compile(r"authoritative\s+reference", re.IGNORECASE),
        re.compile(r"Use\s+this\s+as", re.IGNORECASE),
        re.compile(r"use\s+the\s+(downloaded|retrieved)\s+.*content", re.IGNORECASE),
        re.compile(r"source\s+of\s+truth", re.IGNORECASE),
    ]

    def test_download_resource_precedes_usage_references(self) -> None:
        """The download_resource call must appear before any usage references in Step 3."""
        step3_content = extract_step_content(3)

        # Find position of download_resource call
        download_match = self._DOWNLOAD_CALL_RE.search(step3_content)
        assert download_match is not None, (
            "Step 3 must contain a download_resource call instruction, but none was found."
        )
        download_pos = download_match.start()

        # Find positions of all usage references and verify each comes after the call
        for pattern in self._USAGE_REFERENCE_PATTERNS:
            for usage_match in pattern.finditer(step3_content):
                usage_pos = usage_match.start()
                assert download_pos < usage_pos, (
                    f"download_resource call (position {download_pos}) must appear before "
                    f"Entity Specification usage reference '{usage_match.group()}' "
                    f"(position {usage_pos}) in Step 3. "
                    f"The call instruction must precede any language about using the "
                    f"downloaded content."
                )


# ---------------------------------------------------------------------------
# Property 2: Exactly one download_resource instruction
# ---------------------------------------------------------------------------

# Pattern matching the download_resource call instruction
_DOWNLOAD_RESOURCE_RE = re.compile(
    r'download_resource\(filename="senzing_entity_specification\.md"\)'
)


class TestDownloadResourceCount:
    """Verify exactly one download_resource call instruction exists in Steps 3–5.

    **Validates: Requirements 4.1**
    """

    def test_exactly_one_download_resource_in_steps_3_through_5(self) -> None:
        """The steering file must contain exactly one download_resource instruction
        across Steps 3, 4, and 5."""
        step3 = extract_step_content(3)
        step4 = extract_step_content(4)
        step5 = extract_step_content(5)

        combined_content = step3 + step4 + step5
        matches = _DOWNLOAD_RESOURCE_RE.findall(combined_content)
        count = len(matches)

        assert count == 1, (
            f"Expected exactly 1 download_resource("
            f'filename="senzing_entity_specification.md") instruction '
            f"across Steps 3–5, but found {count}. "
            f"Requirement 4.1 mandates exactly one call instruction."
        )


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestNoHardcodedAttributes:
    """Property 1: No hardcoded Entity Specification attributes in Steps 3–5.

    For any step content extracted from Steps 3, 4, or 5, verify no Entity
    Specification attribute names from the known set appear (excluding
    DATA_SOURCE and RECORD_ID in Step 4's required-fields check).

    **Validates: Requirements 1.1, 2.1, 3.1, 5.1**
    """

    @given(step_number=st.sampled_from([3, 4, 5]))
    @settings(max_examples=20)
    def test_no_hardcoded_entity_spec_attributes(self, step_number: int) -> None:
        """No Entity Specification attribute names appear in Steps 3–5.

        For Step 4, DATA_SOURCE and RECORD_ID are allowed as structural
        references for the required-fields check.
        """
        content = extract_step_content(step_number)

        # Determine which attributes to check for this step
        disallowed = KNOWN_ENTITY_SPEC_ATTRIBUTES.copy()
        if step_number == 4:
            disallowed -= ALLOWED_STRUCTURAL_REFS

        # Check for any disallowed attribute appearing in the content
        found = {attr for attr in disallowed if attr in content}

        assert not found, (
            f"Step {step_number} contains hardcoded Entity Specification attributes: "
            f"{sorted(found)}. These should be removed per MCP-first enforcement."
        )
