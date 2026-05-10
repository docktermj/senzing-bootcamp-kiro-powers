"""Bug condition exploration tests for windows-scoop-supportpath-fix bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: windows-scoop-supportpath-fix

**Validates: Requirements 1.1, 2.1, 2.2, 2.3**
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
# Regex patterns for expected content in the fixed Step 8
# ---------------------------------------------------------------------------

_SUPPORTPATH_VERIFY_KEYWORDS = re.compile(
    r"(verify.*SUPPORTPATH|SUPPORTPATH.*exist|check.*SUPPORTPATH|"
    r"confirm.*SUPPORTPATH.*directory|SUPPORTPATH.*verification)",
    re.IGNORECASE,
)

_FALLBACK_PATH_KEYWORDS = re.compile(
    r"(\.\.\\/data|\.\.[/\\]data|parent.*data|one\s+level\s+up|"
    r"SENZING_DIR\\\.\.\\.\\\\data|"
    r"\$SENZING_DIR\\\\\.\.\\\\.\\\\data|"
    r"\\\\\.\\\\\.\\\\data|"
    r"\\.\\.\\.\\\\data)",
    re.IGNORECASE,
)

_WINDOWS_CONDITIONAL_KEYWORDS = re.compile(
    r"(on\s+windows|if\s+windows|when.*windows|windows.*only|"
    r"platform.*windows|windows.*platform|windows.*scoop|scoop.*windows)",
    re.IGNORECASE,
)

_FILESYSTEM_CHECK_KEYWORDS = re.compile(
    r"(Test-Path|test-path|directory.*exist|exist.*directory|"
    r"if\s+exist|verify.*path|path.*verify|check.*directory|"
    r"directory.*check|folder.*exist|exist.*folder)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Test 1 — Missing SUPPORTPATH Verification Instructions
# ---------------------------------------------------------------------------


class TestMissingSupportpathVerification:
    """Test 1 — Missing SUPPORTPATH Verification Instructions.

    **Validates: Requirements 1.1, 2.1**

    Parse module-02-sdk-setup.md, extract Step 8, and assert it contains
    instructions to verify SUPPORTPATH directory exists on Windows before
    using it. On unfixed content this will FAIL because Step 8 instructs
    saving MCP-returned JSON directly without verifying SUPPORTPATH exists.
    """

    def test_step8_contains_supportpath_verification(self) -> None:
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"
        assert _SUPPORTPATH_VERIFY_KEYWORDS.search(step8), (
            "Step 8 does not contain instructions to verify SUPPORTPATH "
            "directory exists on Windows before using it. The agent is "
            "instructed to save MCP-returned JSON directly without verifying "
            "SUPPORTPATH exists, which causes SENZ2027 on Scoop installs. "
            f"Step 8 content:\n{step8[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Fallback Logic to Parent-Level Data Directory
# ---------------------------------------------------------------------------


class TestMissingFallbackLogic:
    """Test 2 — Missing Fallback Logic.

    **Validates: Requirements 2.1, 2.2**

    Parse module-02-sdk-setup.md, extract Step 8, and assert it contains
    fallback logic to check `$SENZING_DIR\\..\\data` when
    `$SENZING_DIR\\data` does not exist. On unfixed content this will
    FAIL because no fallback path logic exists.
    """

    def test_step8_contains_fallback_to_parent_data(self) -> None:
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"
        assert _FALLBACK_PATH_KEYWORDS.search(step8), (
            "Step 8 does not contain fallback logic to check "
            "$SENZING_DIR\\..\\data when $SENZING_DIR\\data does not exist. "
            "The Scoop package layout places the data directory one level "
            "above the er directory, but Step 8 has no fallback for this. "
            f"Step 8 content:\n{step8[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing Windows-Conditional Gate
# ---------------------------------------------------------------------------


class TestMissingWindowsConditional:
    """Test 3 — Missing Windows-Conditional Gate.

    **Validates: Requirements 2.1, 2.3**

    Parse module-02-sdk-setup.md, extract Step 8, and assert it contains
    a Windows-conditional gate (e.g., "On Windows" or platform-specific
    scoping) for SUPPORTPATH verification. On unfixed content this will
    FAIL because Step 8 has no Windows-specific path verification logic.
    """

    def test_step8_contains_windows_conditional(self) -> None:
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"

        # Check for Windows-conditional AND SUPPORTPATH-related content together
        has_windows = bool(_WINDOWS_CONDITIONAL_KEYWORDS.search(step8))
        has_supportpath = bool(
            re.search(r"SUPPORTPATH", step8, re.IGNORECASE)
        )

        assert has_windows and has_supportpath, (
            "Step 8 does not contain a Windows-conditional gate for "
            "SUPPORTPATH verification. The fallback logic must be explicitly "
            "scoped to Windows only. "
            f"has_windows_conditional={has_windows}, "
            f"has_supportpath_mention={has_supportpath}. "
            f"Step 8 content:\n{step8[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Missing Filesystem Verification Command
# ---------------------------------------------------------------------------


class TestMissingFilesystemCheck:
    """Test 4 — Missing Filesystem Verification Command.

    **Validates: Requirements 2.1, 2.2**

    Parse module-02-sdk-setup.md, extract Step 8, and assert it contains
    a filesystem verification command (e.g., `Test-Path` or directory
    existence check) for verifying SUPPORTPATH. On unfixed content this
    will FAIL because no such command exists in Step 8.
    """

    def test_step8_contains_filesystem_check_command(self) -> None:
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"
        assert _FILESYSTEM_CHECK_KEYWORDS.search(step8), (
            "Step 8 does not contain a filesystem verification command "
            "(e.g., Test-Path or directory existence check) for verifying "
            "SUPPORTPATH exists before using it. Without this, the agent "
            "cannot proactively detect a missing data directory. "
            f"Step 8 content:\n{step8[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition: Windows Scoop SUPPORTPATH Missing Fallback
# ---------------------------------------------------------------------------


@st.composite
def st_windows_scoop_path(draw: st.DrawFn) -> dict[str, str]:
    """Generate random Windows Scoop path scenarios.

    Varies usernames and version strings to simulate different Scoop
    install locations where SENZING_DIR points to the `er` subdirectory.
    """
    username = draw(
        st.from_regex(r"[A-Za-z][A-Za-z0-9_]{2,15}", fullmatch=True)
    )
    version = draw(
        st.from_regex(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,3}", fullmatch=True)
    )
    return {
        "username": username,
        "version": version,
        "senzing_dir": f"C:\\Users\\{username}\\scoop\\apps\\senzing\\{version}\\er",
        "standard_path": (
            f"C:\\Users\\{username}\\scoop\\apps\\senzing\\{version}\\er\\data"
        ),
        "fallback_path": (
            f"C:\\Users\\{username}\\scoop\\apps\\senzing\\{version}\\data"
        ),
        "platform": "windows",
        "install_method": "scoop",
    }


class TestWindowsScoopSupportpathMissingFallback:
    """PBT Test — Bug Condition: Windows Scoop SUPPORTPATH Missing Fallback.

    **Validates: Requirements 1.1, 2.1, 2.2, 2.3**

    Use Hypothesis to generate random Windows Scoop path scenarios
    (varying usernames, version strings) and assert the steering content
    contains explicit SUPPORTPATH verification instructions.

    The bug condition is:
      input.platform == 'windows'
      AND input.installMethod == 'scoop'
      AND NOT directoryExists(input.senzingDir + '\\data')
      AND directoryExists(input.senzingDir + '\\..\\data')

    On unfixed code, this will FAIL because Step 8 instructs saving
    MCP-returned JSON directly without verifying SUPPORTPATH exists.
    """

    @given(scenario=st_windows_scoop_path())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_steering_contains_supportpath_verification_for_scoop(
        self, scenario: dict[str, str]
    ) -> None:
        """For any Windows Scoop path scenario, the steering file must
        contain explicit SUPPORTPATH verification and fallback logic.

        The bug condition is: platform == Windows AND installMethod == scoop
        AND standard_path does not exist AND fallback_path exists.

        The steering file must instruct the agent to:
        1. Verify SUPPORTPATH directory exists before using it
        2. Fall back to parent-level data directory on Windows
        3. Use a filesystem check command (e.g., Test-Path)
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)

        assert step8, "Step 8 section not found"

        has_supportpath_verify = bool(_SUPPORTPATH_VERIFY_KEYWORDS.search(step8))
        has_fallback = bool(_FALLBACK_PATH_KEYWORDS.search(step8))
        has_windows_gate = bool(_WINDOWS_CONDITIONAL_KEYWORDS.search(step8))
        has_fs_check = bool(_FILESYSTEM_CHECK_KEYWORDS.search(step8))

        assert has_supportpath_verify and has_fallback and has_windows_gate and has_fs_check, (
            f"Bug condition confirmed for scenario: "
            f"username={scenario['username']}, version={scenario['version']}, "
            f"senzing_dir={scenario['senzing_dir']}. "
            f"Step 8 does NOT contain explicit SUPPORTPATH verification "
            f"and fallback logic for Windows Scoop installs. "
            f"has_supportpath_verify={has_supportpath_verify}, "
            f"has_fallback={has_fallback}, "
            f"has_windows_gate={has_windows_gate}, "
            f"has_fs_check={has_fs_check}. "
            f"The agent will set SUPPORTPATH to "
            f"{scenario['standard_path']} which does not exist in Scoop "
            f"layout — the correct path is {scenario['fallback_path']}."
        )
