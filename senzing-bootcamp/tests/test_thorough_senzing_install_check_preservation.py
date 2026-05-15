"""Preservation property tests for thorough-senzing-install-check bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code — they confirm the
baseline behavior that must remain unchanged.

Feature: thorough-senzing-install-check

**Validates: Requirements 3.1, 3.2, 3.3**
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


def _read_module_02() -> str:
    """Read the full content of module-02-sdk-setup.md."""
    return _MODULE_02.read_text(encoding="utf-8")


def _extract_step_by_heading(markdown: str, step_number: int) -> str:
    """Extract a step section from the module-02 steering file by heading.

    Steps are formatted as ``## Step N: Title`` headings.

    Returns the full text of the step from its heading to the next
    ``## `` heading or end of file.
    """
    step_pattern = re.compile(
        rf"^## Step {step_number}:",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next ## heading
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED Step 1 content for observation
# ---------------------------------------------------------------------------

_UNFIXED_CONTENT = _read_module_02()
_UNFIXED_STEP1 = _extract_step_by_heading(_UNFIXED_CONTENT, 1)

# Key phrases observed in the unfixed Step 1 that must be preserved:

# 1. Language-level import check instruction (primary detection method)
_IMPORT_CHECK_PHRASE = "language-appropriate import/version check"

# 2. "SDK found" path — skip Steps 2-3, jump to Step 4
_SDK_FOUND_SKIP_PHRASE = "Skip Steps 2 and 3 entirely"
_SDK_FOUND_JUMP_PHRASE = "Jump to Step 4"

# 3. "SDK not found" path — proceed with Step 2
_SDK_NOT_FOUND_PHRASE = "Proceed with Step 2"

# 4. Version below V4.0 upgrade recommendation
_VERSION_CHECK_PHRASE = "version is incompatible (<V4.0)"
_UPGRADE_PHRASE = "Proceed with Steps 2-3 for upgrade"

# 5. Checkpoint write instruction at end of Step 1
_CHECKPOINT_PHRASE = "**Checkpoint:** Write step 1 to `config/bootcamp_progress.json`."

# Section markers that define the three conditional paths in Step 1
_SDK_FOUND_MARKER = "**If the SDK is found and version is V4.0+:**"
_SDK_NOT_FOUND_MARKER = "**If the SDK is NOT found:**"
_VERSION_INCOMPATIBLE_MARKER = "**If the SDK is found but version is incompatible (<V4.0):**"


# ---------------------------------------------------------------------------
# Test 1 — Import Check Instruction Preserved
# ---------------------------------------------------------------------------


class TestImportCheckInstructionPreserved:
    """The language-level import check instruction is present in Step 1.

    **Validates: Requirements 3.2**

    The primary detection method (language-appropriate import/version
    check) must remain as the first detection approach in Step 1.
    The filesystem fallback is additive — it does not replace the
    import check.
    """

    def test_step1_contains_import_check_instruction(self) -> None:
        """Assert Step 1 contains the language-appropriate import check."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _IMPORT_CHECK_PHRASE in step1, (
            f"Step 1 does not contain the import check instruction "
            f"'{_IMPORT_CHECK_PHRASE}'. The language-level import check "
            f"is the primary detection method and must be preserved."
        )

    def test_step1_contains_sdk_guide_reference(self) -> None:
        """Assert Step 1 references sdk_guide for verification command."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert "sdk_guide" in step1, (
            "Step 1 does not reference 'sdk_guide' tool for getting "
            "the correct verification command."
        )


# ---------------------------------------------------------------------------
# Test 2 — SDK Found Path Preserved (Skip Steps 2-3, Jump to Step 4)
# ---------------------------------------------------------------------------


class TestSDKFoundPathPreserved:
    """The 'SDK found' path (skip Steps 2-3, jump to Step 4) is preserved.

    **Validates: Requirements 3.2**

    When the SDK is found and version is V4.0+, the agent must skip
    Steps 2 and 3 entirely and jump to Step 4 for verification.
    """

    def test_step1_contains_sdk_found_marker(self) -> None:
        """Assert Step 1 contains the SDK found conditional marker."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _SDK_FOUND_MARKER in step1, (
            f"Step 1 does not contain the SDK found marker: "
            f"'{_SDK_FOUND_MARKER}'"
        )

    def test_step1_contains_skip_steps_instruction(self) -> None:
        """Assert Step 1 contains 'Skip Steps 2 and 3 entirely'."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _SDK_FOUND_SKIP_PHRASE in step1, (
            f"Step 1 does not contain '{_SDK_FOUND_SKIP_PHRASE}'. "
            f"The SDK-found path must skip Steps 2 and 3."
        )

    def test_step1_contains_jump_to_step4(self) -> None:
        """Assert Step 1 contains 'Jump to Step 4'."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _SDK_FOUND_JUMP_PHRASE in step1, (
            f"Step 1 does not contain '{_SDK_FOUND_JUMP_PHRASE}'. "
            f"The SDK-found path must jump to Step 4 for verification."
        )


# ---------------------------------------------------------------------------
# Test 3 — SDK Not Found Path Preserved (Proceed with Step 2)
# ---------------------------------------------------------------------------


class TestSDKNotFoundPathPreserved:
    """The 'SDK not found' path (proceed with Step 2) is preserved.

    **Validates: Requirements 3.1**

    When the SDK is genuinely not installed, the agent must proceed
    with Step 2 for the full installation workflow.
    """

    def test_step1_contains_sdk_not_found_marker(self) -> None:
        """Assert Step 1 contains the SDK not found conditional marker."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _SDK_NOT_FOUND_MARKER in step1, (
            f"Step 1 does not contain the SDK not found marker: "
            f"'{_SDK_NOT_FOUND_MARKER}'"
        )

    def test_step1_contains_proceed_with_step2(self) -> None:
        """Assert Step 1 contains 'Proceed with Step 2'."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _SDK_NOT_FOUND_PHRASE in step1, (
            f"Step 1 does not contain '{_SDK_NOT_FOUND_PHRASE}'. "
            f"The SDK-not-found path must proceed with Step 2."
        )


# ---------------------------------------------------------------------------
# Test 4 — Version Below V4.0 Upgrade Recommendation Preserved
# ---------------------------------------------------------------------------


class TestVersionBelowV4UpgradePreserved:
    """The version-below-V4.0 upgrade recommendation path is preserved.

    **Validates: Requirements 3.3**

    When the SDK is found but version is incompatible (<V4.0), the
    agent must recommend an upgrade and proceed with Steps 2-3.
    """

    def test_step1_contains_version_incompatible_marker(self) -> None:
        """Assert Step 1 contains the version incompatible marker."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _VERSION_INCOMPATIBLE_MARKER in step1, (
            f"Step 1 does not contain the version incompatible marker: "
            f"'{_VERSION_INCOMPATIBLE_MARKER}'"
        )

    def test_step1_contains_upgrade_instruction(self) -> None:
        """Assert Step 1 contains 'Proceed with Steps 2-3 for upgrade'."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _UPGRADE_PHRASE in step1, (
            f"Step 1 does not contain '{_UPGRADE_PHRASE}'. "
            f"The version-below-V4.0 path must proceed with upgrade."
        )


# ---------------------------------------------------------------------------
# Test 5 — Checkpoint Write Instruction at End of Step 1
# ---------------------------------------------------------------------------


class TestCheckpointWritePreserved:
    """The checkpoint write instruction remains at end of Step 1.

    **Validates: Requirements 3.1, 3.2, 3.3**

    Step 1 must end with a checkpoint write instruction to record
    progress to bootcamp_progress.json.
    """

    def test_step1_contains_checkpoint_instruction(self) -> None:
        """Assert Step 1 contains the checkpoint write instruction."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _CHECKPOINT_PHRASE in step1, (
            f"Step 1 does not contain the checkpoint instruction: "
            f"'{_CHECKPOINT_PHRASE}'"
        )

    def test_checkpoint_is_last_substantive_line_in_step1(self) -> None:
        """Assert the checkpoint is the last substantive content in Step 1."""
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"

        # Find the checkpoint position and verify nothing substantive follows
        checkpoint_pos = step1.rfind(_CHECKPOINT_PHRASE)
        assert checkpoint_pos >= 0, (
            "Checkpoint instruction not found in Step 1"
        )

        # Content after checkpoint should be only whitespace
        after_checkpoint = step1[checkpoint_pos + len(_CHECKPOINT_PHRASE):]
        assert after_checkpoint.strip() == "", (
            f"Content found after checkpoint instruction in Step 1: "
            f"'{after_checkpoint.strip()[:200]}'. "
            f"The checkpoint must be the last substantive line."
        )


# ---------------------------------------------------------------------------
# PBT Test — Structural Preservation Across Section Marker Variations
# ---------------------------------------------------------------------------


@st.composite
def st_section_marker_variation(draw: st.DrawFn) -> dict[str, str]:
    """Generate variations of section markers to verify structural preservation.

    Produces different section marker strings that should be found in
    Step 1, along with the expected content that follows each marker.
    This tests that the structural elements of Step 1 are preserved
    regardless of which marker we look for.
    """
    marker_type = draw(st.sampled_from([
        "sdk_found",
        "sdk_not_found",
        "version_incompatible",
        "import_check",
        "checkpoint",
    ]))

    marker_map = {
        "sdk_found": {
            "marker": _SDK_FOUND_MARKER,
            "expected_content": _SDK_FOUND_SKIP_PHRASE,
            "description": "SDK found path with skip instruction",
        },
        "sdk_not_found": {
            "marker": _SDK_NOT_FOUND_MARKER,
            "expected_content": _SDK_NOT_FOUND_PHRASE,
            "description": "SDK not found path with proceed instruction",
        },
        "version_incompatible": {
            "marker": _VERSION_INCOMPATIBLE_MARKER,
            "expected_content": _UPGRADE_PHRASE,
            "description": "Version incompatible path with upgrade instruction",
        },
        "import_check": {
            "marker": _IMPORT_CHECK_PHRASE,
            "expected_content": "sdk_guide",
            "description": "Import check with sdk_guide reference",
        },
        "checkpoint": {
            "marker": _CHECKPOINT_PHRASE,
            "expected_content": "bootcamp_progress.json",
            "description": "Checkpoint write to progress file",
        },
    }

    return marker_map[marker_type]


class TestStructuralPreservationPBT:
    """PBT — All non-bug-condition paths are structurally preserved.

    **Validates: Requirements 3.1, 3.2, 3.3**

    Use Hypothesis to generate variations of section markers and verify
    that each structural element of Step 1 is present and contains its
    expected associated content. This ensures the fix does not
    accidentally remove or alter any existing detection paths.
    """

    @given(variation=st_section_marker_variation())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_section_marker_and_content_preserved(
        self, variation: dict[str, str]
    ) -> None:
        """For any section marker in Step 1, both the marker and its
        associated content must be present.

        This property verifies that:
        - The import check instruction is present and unchanged
        - The SDK found path (skip Steps 2-3) is preserved
        - The SDK not found path (proceed with Step 2) is preserved
        - The version-below-V4.0 upgrade path is preserved
        - The checkpoint write instruction remains at end of Step 1
        """
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)

        assert step1, "Step 1 section not found in module-02-sdk-setup.md"

        marker = variation["marker"]
        expected_content = variation["expected_content"]
        description = variation["description"]

        assert marker in step1, (
            f"Section marker not found in Step 1: '{marker}'. "
            f"Description: {description}. "
            f"This structural element must be preserved after the fix."
        )

        assert expected_content in step1, (
            f"Expected content not found in Step 1: '{expected_content}'. "
            f"Description: {description}. "
            f"The associated content for this section marker must be preserved."
        )

    @given(variation=st_section_marker_variation())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_section_ordering_preserved(
        self, variation: dict[str, str]
    ) -> None:
        """For any section marker, verify it appears in the correct
        relative position within Step 1.

        The import check must come before the conditional paths,
        and the checkpoint must come last.
        """
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)

        assert step1, "Step 1 section not found in module-02-sdk-setup.md"

        marker = variation["marker"]

        # Verify the marker exists
        marker_pos = step1.find(marker)
        assert marker_pos >= 0, (
            f"Section marker not found: '{marker}'"
        )

        # The checkpoint must always be the last structural element
        checkpoint_pos = step1.find(_CHECKPOINT_PHRASE)
        assert checkpoint_pos >= 0, (
            "Checkpoint instruction not found in Step 1"
        )

        # Import check must come before all conditional paths
        import_pos = step1.find(_IMPORT_CHECK_PHRASE)
        assert import_pos >= 0, (
            "Import check instruction not found in Step 1"
        )

        # If this is a conditional path marker, it must come after import check
        if marker != _IMPORT_CHECK_PHRASE and marker != _CHECKPOINT_PHRASE:
            assert marker_pos > import_pos, (
                f"Section marker '{marker[:50]}...' appears before the "
                f"import check instruction. Conditional paths must follow "
                f"the primary detection method."
            )

        # Checkpoint must be after all other markers
        if marker != _CHECKPOINT_PHRASE:
            assert checkpoint_pos > marker_pos, (
                f"Checkpoint appears before section marker "
                f"'{marker[:50]}...'. The checkpoint must be the last "
                f"structural element in Step 1."
            )
