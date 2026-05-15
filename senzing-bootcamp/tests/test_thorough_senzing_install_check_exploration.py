"""Bug condition exploration tests for thorough-senzing-install-check bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: thorough-senzing-install-check

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**
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
# Sentinel file paths and keywords for expected content in fixed Step 1
# ---------------------------------------------------------------------------

_NATIVE_LIBRARY_SENTINEL = "/opt/senzing/er/lib/libSz.so"
_BUILD_VERSION_SENTINEL = "/opt/senzing/er/szBuildVersion.json"

_FALLBACK_LANGUAGE_KEYWORDS = re.compile(
    r"(fallback|if.*import.*fail|when.*import.*fail|"
    r"filesystem.*check|check.*filesystem|"
    r"if.*not\s+found.*check|alternative.*detection|"
    r"file.*exist|sentinel)",
    re.IGNORECASE,
)

_BOTH_FILES_REQUIRED_KEYWORDS = re.compile(
    r"(both.*file|both.*sentinel|both.*present|"
    r"both.*must.*exist|both.*required|"
    r"two.*file|two.*sentinel|"
    r"libSz\.so.*szBuildVersion|szBuildVersion.*libSz\.so)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Test 1 — Missing Native Library Sentinel Reference
# ---------------------------------------------------------------------------


class TestMissingNativeLibrarySentinel:
    """Test 1 — Missing Native Library Sentinel Reference.

    **Validates: Requirements 1.1, 2.1**

    Parse module-02-sdk-setup.md, extract Step 1, and assert it contains
    a reference to `/opt/senzing/er/lib/libSz.so` (native library sentinel).
    On unfixed content this will FAIL because Step 1 only uses language
    import checks and has no filesystem sentinel file references.
    """

    def test_step1_contains_native_library_sentinel(self) -> None:
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _NATIVE_LIBRARY_SENTINEL in step1, (
            "Step 1 does not contain a reference to the native library "
            f"sentinel file '{_NATIVE_LIBRARY_SENTINEL}'. The current Step 1 "
            "only uses language-level import checks and package manager "
            "queries, with no filesystem fallback to detect the SDK when "
            "PYTHONPATH is not configured. "
            f"Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Build Version Sentinel Reference
# ---------------------------------------------------------------------------


class TestMissingBuildVersionSentinel:
    """Test 2 — Missing Build Version Sentinel Reference.

    **Validates: Requirements 1.2, 2.1**

    Parse module-02-sdk-setup.md, extract Step 1, and assert it contains
    a reference to `/opt/senzing/er/szBuildVersion.json` (build version
    sentinel). On unfixed content this will FAIL because Step 1 has no
    filesystem-based detection logic.
    """

    def test_step1_contains_build_version_sentinel(self) -> None:
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _BUILD_VERSION_SENTINEL in step1, (
            "Step 1 does not contain a reference to the build version "
            f"sentinel file '{_BUILD_VERSION_SENTINEL}'. The current Step 1 "
            "only uses language-level import checks and package manager "
            "queries, with no filesystem fallback to detect the SDK when "
            "package names don't match the query pattern. "
            f"Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing Fallback Language
# ---------------------------------------------------------------------------


class TestMissingFallbackLanguage:
    """Test 3 — Missing Fallback Language.

    **Validates: Requirements 1.3, 2.1, 2.2**

    Parse module-02-sdk-setup.md, extract Step 1, and assert it contains
    fallback language indicating filesystem checks run when the import
    check fails. On unfixed content this will FAIL because no fallback
    logic exists in the current Step 1 instructions.
    """

    def test_step1_contains_fallback_language(self) -> None:
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _FALLBACK_LANGUAGE_KEYWORDS.search(step1), (
            "Step 1 does not contain fallback language indicating filesystem "
            "checks run when the import check fails. The current Step 1 has "
            "no alternative detection path — if the language import fails, "
            "the agent immediately concludes the SDK is not installed without "
            "checking the filesystem. "
            f"Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Missing Both-Files-Required Condition
# ---------------------------------------------------------------------------


class TestMissingBothFilesRequired:
    """Test 4 — Missing Both-Files-Required Condition.

    **Validates: Requirements 2.2, 2.3**

    Parse module-02-sdk-setup.md, extract Step 1, and assert it specifies
    that both sentinel files must be present to conclude the SDK is
    installed. On unfixed content this will FAIL because no such condition
    exists in the current Step 1.
    """

    def test_step1_requires_both_sentinel_files(self) -> None:
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)
        assert step1, "Step 1 section not found in module-02-sdk-setup.md"
        assert _BOTH_FILES_REQUIRED_KEYWORDS.search(step1), (
            "Step 1 does not specify that both sentinel files must be "
            "present to conclude the SDK is installed. Without this "
            "requirement, a partial installation (only one file present) "
            "could be incorrectly treated as a complete installation. "
            f"Step 1 content:\n{step1[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition: Missing Filesystem Fallback Detection
# ---------------------------------------------------------------------------


@st.composite
def st_sentinel_path_variation(draw: st.DrawFn) -> dict[str, str]:
    """Generate variations of sentinel file path strings.

    Produces the canonical sentinel paths along with metadata about the
    install context to verify the property holds for the expected paths.
    """
    # The canonical paths are fixed — we vary the context around them
    lib_subdir = draw(st.just("lib"))
    native_lib_name = draw(st.just("libSz.so"))
    version_file_name = draw(st.just("szBuildVersion.json"))

    # Vary the scenario context
    pythonpath_set = draw(st.just(False))
    dpkg_matches = draw(st.just(False))
    sdk_physically_installed = draw(st.just(True))

    return {
        "native_library_path": f"/opt/senzing/er/{lib_subdir}/{native_lib_name}",
        "build_version_path": f"/opt/senzing/er/{version_file_name}",
        "pythonpath_configured": pythonpath_set,
        "package_manager_finds_sdk": dpkg_matches,
        "sdk_on_filesystem": sdk_physically_installed,
        "expected_native_sentinel": _NATIVE_LIBRARY_SENTINEL,
        "expected_version_sentinel": _BUILD_VERSION_SENTINEL,
    }


class TestFilesystemFallbackDetectionBugCondition:
    """PBT Test — Bug Condition: Missing Filesystem Fallback Detection.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3**

    Use Hypothesis to generate variations of sentinel file path strings
    and verify the property holds for the canonical paths. The bug
    condition is:

      isBugCondition(input) WHERE:
        input.sdkExistsOnFilesystem == true
        AND input.languageImportSucceeds == false
        AND input.packageManagerQuerySucceeds == false

    On unfixed code, this will FAIL because Step 1 lacks filesystem
    fallback instructions — it only uses language import checks.
    """

    @given(scenario=st_sentinel_path_variation())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_steering_contains_filesystem_fallback_for_bug_condition(
        self, scenario: dict[str, str | bool]
    ) -> None:
        """For any scenario where the SDK is physically installed but
        import/package-manager checks fail, Step 1 must contain filesystem
        fallback instructions referencing both sentinel files.

        The bug condition is: sdkExistsOnFilesystem == true AND
        languageImportSucceeds == false AND packageManagerQuerySucceeds == false.

        The steering file must instruct the agent to:
        1. Check for /opt/senzing/er/lib/libSz.so (native library sentinel)
        2. Check for /opt/senzing/er/szBuildVersion.json (build version sentinel)
        3. Use fallback language indicating filesystem checks run when import fails
        4. Require both sentinel files to be present to conclude SDK is installed
        """
        content = _read_module_02()
        step1 = _extract_step_by_heading(content, 1)

        assert step1, "Step 1 section not found"

        has_native_lib = _NATIVE_LIBRARY_SENTINEL in step1
        has_build_version = _BUILD_VERSION_SENTINEL in step1
        has_fallback_language = bool(_FALLBACK_LANGUAGE_KEYWORDS.search(step1))
        has_both_required = bool(_BOTH_FILES_REQUIRED_KEYWORDS.search(step1))

        assert has_native_lib and has_build_version and has_fallback_language and has_both_required, (
            f"Bug condition confirmed for scenario: "
            f"sdk_on_filesystem={scenario['sdk_on_filesystem']}, "
            f"pythonpath_configured={scenario['pythonpath_configured']}, "
            f"package_manager_finds_sdk={scenario['package_manager_finds_sdk']}. "
            f"Step 1 does NOT contain filesystem fallback instructions. "
            f"has_native_lib_sentinel={has_native_lib}, "
            f"has_build_version_sentinel={has_build_version}, "
            f"has_fallback_language={has_fallback_language}, "
            f"has_both_files_required={has_both_required}. "
            f"Expected sentinel paths: "
            f"{scenario['expected_native_sentinel']}, "
            f"{scenario['expected_version_sentinel']}. "
            f"The agent will fail to detect an installed SDK when "
            f"PYTHONPATH is not configured or package names don't match."
        )
