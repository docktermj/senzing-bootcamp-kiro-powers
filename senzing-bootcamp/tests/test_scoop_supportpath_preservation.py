"""Preservation property tests for windows-scoop-supportpath-fix bugfix.

These tests verify that non-Scoop configuration behavior is UNCHANGED by the fix.
Tests are run on UNFIXED code first to confirm baseline behavior, then re-run
after the fix to confirm no regressions.

Feature: windows-scoop-supportpath-fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
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


def _extract_agent_behavior_section(markdown: str) -> str:
    """Extract the Agent Behavior section from the steering file.

    Returns the text from ``## Agent Behavior`` to the next ``## `` heading
    or end of file.
    """
    pattern = re.compile(r"^## Agent Behavior", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _get_step_headings(markdown: str) -> list[tuple[int, str]]:
    """Extract all step headings as (step_number, title) tuples."""
    pattern = re.compile(r"^## Step (\d+): (.+)$", re.MULTILINE)
    return [(int(m.group(1)), m.group(2)) for m in pattern.finditer(markdown)]


# ---------------------------------------------------------------------------
# Strategies for property-based tests
# ---------------------------------------------------------------------------


@st.composite
def st_non_windows_platform(draw: st.DrawFn) -> dict[str, str]:
    """Generate random non-Windows platform/install-method combinations.

    These represent configurations where the Scoop fallback logic
    should NEVER apply.
    """
    platform = draw(st.sampled_from(["linux", "macos", "linux_apt", "linux_yum", "macos_arm"]))
    install_method = draw(st.sampled_from([
        "apt", "yum", "brew", "homebrew", "manual", "package_manager", "source",
    ]))
    username = draw(st.from_regex(r"[a-z][a-z0-9_]{2,12}", fullmatch=True))
    return {
        "platform": platform,
        "install_method": install_method,
        "username": username,
        "senzing_dir": f"/opt/senzing/er" if "linux" in platform else f"/usr/local/senzing/er",
    }


@st.composite
def st_windows_non_scoop_platform(draw: st.DrawFn) -> dict[str, str]:
    """Generate random Windows non-Scoop install scenarios.

    These represent Windows configurations where $SENZING_DIR\\data EXISTS
    (MSI, manual installs) — fallback logic should NOT apply.
    """
    install_method = draw(st.sampled_from(["msi", "manual", "installer", "zip"]))
    username = draw(st.from_regex(r"[A-Za-z][A-Za-z0-9_]{2,12}", fullmatch=True))
    return {
        "platform": "windows",
        "install_method": install_method,
        "username": username,
        "senzing_dir": f"C:\\Program Files\\Senzing\\er",
        "standard_path_exists": True,
    }


@st.composite
def st_any_non_bug_condition(draw: st.DrawFn) -> dict[str, str]:
    """Generate any platform/install-method combination that is NOT the bug condition.

    The bug condition is: Windows + Scoop + $SENZING_DIR\\data does not exist.
    This strategy generates everything EXCEPT that combination.
    """
    is_windows = draw(st.booleans())
    if is_windows:
        # Windows but NOT Scoop, or Windows + Scoop but standard path exists
        is_scoop = draw(st.booleans())
        if is_scoop:
            # Scoop but standard path exists (not the bug condition)
            username = draw(st.from_regex(r"[A-Za-z][A-Za-z0-9_]{2,12}", fullmatch=True))
            version = draw(
                st.from_regex(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,3}", fullmatch=True)
            )
            return {
                "platform": "windows",
                "install_method": "scoop",
                "username": username,
                "senzing_dir": (
                    f"C:\\Users\\{username}\\scoop\\apps\\senzing\\{version}\\er"
                ),
                "standard_path_exists": True,
                "is_bug_condition": False,
            }
        else:
            install_method = draw(st.sampled_from(["msi", "manual", "installer", "zip"]))
            username = draw(st.from_regex(r"[A-Za-z][A-Za-z0-9_]{2,12}", fullmatch=True))
            return {
                "platform": "windows",
                "install_method": install_method,
                "username": username,
                "senzing_dir": "C:\\Program Files\\Senzing\\er",
                "standard_path_exists": True,
                "is_bug_condition": False,
            }
    else:
        platform = draw(st.sampled_from(["linux", "macos", "linux_apt", "linux_yum", "macos_arm"]))
        install_method = draw(st.sampled_from([
            "apt", "yum", "brew", "homebrew", "manual", "package_manager",
        ]))
        username = draw(st.from_regex(r"[a-z][a-z0-9_]{2,12}", fullmatch=True))
        return {
            "platform": platform,
            "install_method": install_method,
            "username": username,
            "senzing_dir": (
                f"/opt/senzing/er" if "linux" in platform else "/usr/local/senzing/er"
            ),
            "standard_path_exists": True,
            "is_bug_condition": False,
        }


# ---------------------------------------------------------------------------
# Test 1 — MCP Starting Point Preserved
# ---------------------------------------------------------------------------


class TestMCPStartingPointPreserved:
    """Verify Step 8 instructs using sdk_guide(topic='configure') as the starting point.

    **Validates: Requirements 3.1, 3.3**

    The MCP-returned JSON must remain the starting point for all engine
    configuration. This is a preservation requirement — the fix must not
    remove or weaken this instruction.
    """

    def test_step8_contains_sdk_guide_configure_call(self) -> None:
        """Step 8 must contain the sdk_guide(topic='configure') MCP call instruction."""
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"
        assert "sdk_guide" in step8, (
            "Step 8 does not reference the sdk_guide MCP tool. "
            "The MCP-first approach must be preserved."
        )
        assert "topic='configure'" in step8 or 'topic=\'configure\'' in step8, (
            "Step 8 does not contain sdk_guide(topic='configure') call. "
            "The MCP-returned JSON must remain the starting point for engine configuration."
        )

    @given(scenario=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mcp_first_approach_unchanged_for_non_windows(
        self, scenario: dict[str, str]
    ) -> None:
        """For all non-Windows platforms, sdk_guide(topic='configure') remains the starting point.

        **Validates: Requirements 3.1**

        Generate random non-Windows platform/install-method combinations and
        verify the MCP-first approach is unchanged — the steering file still
        instructs using sdk_guide as the starting point regardless of platform.
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found"

        # The sdk_guide MCP call must be present for ALL platforms
        assert "sdk_guide" in step8, (
            f"For platform={scenario['platform']}, install_method={scenario['install_method']}: "
            f"Step 8 must contain sdk_guide MCP tool reference. "
            f"The MCP-first approach must be preserved for all platforms."
        )
        assert "topic='configure'" in step8 or 'topic=\'configure\'' in step8, (
            f"For platform={scenario['platform']}, install_method={scenario['install_method']}: "
            f"Step 8 must contain sdk_guide(topic='configure') call. "
            f"The MCP-returned JSON is the starting point for all engine configuration."
        )


# ---------------------------------------------------------------------------
# Test 2 — "NEVER construct engine configuration JSON manually" Preserved
# ---------------------------------------------------------------------------


class TestNeverConstructManuallyPreserved:
    """Verify the 'NEVER construct ... manually' rule is preserved.

    **Validates: Requirements 3.3**

    This instruction must remain in the steering file. It appears in both
    Step 8 (as "NEVER construct `SENZING_ENGINE_CONFIGURATION_JSON` manually")
    and the Agent Behavior section (as "NEVER construct engine configuration
    JSON manually"). Both forms express the same preservation requirement.
    """

    # Step 8 uses the backtick-wrapped variable name form
    _NEVER_CONSTRUCT_STEP8 = re.compile(
        r"NEVER construct.*manually",
        re.IGNORECASE,
    )

    # Agent Behavior uses the plain English form
    _NEVER_CONSTRUCT_AGENT_BEHAVIOR = "NEVER construct engine configuration JSON manually"

    def test_step8_contains_never_construct_manually(self) -> None:
        """Step 8 must contain the 'NEVER construct ... manually' rule."""
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"
        assert self._NEVER_CONSTRUCT_STEP8.search(step8), (
            "Step 8 does not contain the 'NEVER construct ... manually' rule. "
            "This preservation requirement must not be removed by the fix."
        )

    def test_agent_behavior_contains_never_construct_manually(self) -> None:
        """Agent Behavior section must also contain the 'NEVER construct...' rule."""
        content = _read_module_02()
        agent_behavior = _extract_agent_behavior_section(content)
        assert agent_behavior, "Agent Behavior section not found in module-02-sdk-setup.md"
        assert self._NEVER_CONSTRUCT_AGENT_BEHAVIOR in agent_behavior, (
            "Agent Behavior section does not contain the "
            "'NEVER construct engine configuration JSON manually' rule. "
            "This must be preserved in both Step 8 and Agent Behavior."
        )

    @given(scenario=st_any_non_bug_condition())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_never_construct_rule_preserved_across_all_non_bug_scenarios(
        self, scenario: dict[str, str]
    ) -> None:
        """For all non-bug-condition scenarios, the 'NEVER construct manually' rule is preserved.

        **Validates: Requirements 3.3**

        Generate random platform/install-method combinations that are NOT the
        bug condition and verify the rule remains in the steering file.
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found"
        assert self._NEVER_CONSTRUCT_STEP8.search(step8), (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"The 'NEVER construct ... manually' rule must be preserved. "
            f"The fix must not remove or weaken this instruction."
        )


# ---------------------------------------------------------------------------
# Test 3 — Fallback Logic Scoped to Windows Only
# ---------------------------------------------------------------------------


class TestFallbackScopedToWindowsOnly:
    """Verify any fallback logic is explicitly scoped to Windows only.

    **Validates: Requirements 3.1, 3.2**

    On the UNFIXED code, there is NO fallback logic at all — which means
    non-Windows platforms are trivially unaffected. After the fix, any
    fallback logic that is added must be explicitly conditional on Windows.
    This test verifies that the steering file does NOT contain unconditional
    fallback instructions that would affect non-Windows platforms.
    """

    # Patterns that indicate unconditional (non-Windows-scoped) fallback logic
    _UNCONDITIONAL_FALLBACK = re.compile(
        r"(?<!windows)(?<!Windows)(?<!on Windows)"
        r"(?:always|unconditionally|for all platforms)\s+"
        r"(?:check|verify|fall\s*back)",
        re.IGNORECASE,
    )

    def test_no_unconditional_fallback_in_step8(self) -> None:
        """Step 8 must not contain unconditional fallback logic affecting all platforms."""
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found in module-02-sdk-setup.md"

        # On unfixed code: no fallback logic exists at all (trivially passes)
        # After fix: fallback must be Windows-conditional, not unconditional
        assert not self._UNCONDITIONAL_FALLBACK.search(step8), (
            "Step 8 contains unconditional fallback logic that would affect "
            "all platforms. Any fallback must be explicitly scoped to Windows only."
        )

    @given(scenario=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_windows_platforms_unaffected_by_fallback(
        self, scenario: dict[str, str]
    ) -> None:
        """For non-Windows platforms, no unconditional fallback logic exists.

        **Validates: Requirements 3.1**

        Generate random non-Windows platform/install-method combinations and
        verify the steering file does not contain unconditional fallback logic
        that would alter behavior for these platforms.
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found"

        # Verify no unconditional fallback that would affect this platform
        assert not self._UNCONDITIONAL_FALLBACK.search(step8), (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"Step 8 contains unconditional fallback logic that would affect "
            f"non-Windows platforms. Fallback must be Windows-only."
        )

    @given(scenario=st_windows_non_scoop_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_windows_non_scoop_unaffected_by_fallback(
        self, scenario: dict[str, str]
    ) -> None:
        """For Windows non-Scoop installs where standard path exists, no fallback triggers.

        **Validates: Requirements 3.2**

        Generate random Windows non-Scoop install scenarios and verify the
        steering file does not contain unconditional fallback logic. The
        fallback should only apply when the standard path does NOT exist.
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found"

        # Verify no unconditional fallback that would affect standard Windows installs
        assert not self._UNCONDITIONAL_FALLBACK.search(step8), (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"Step 8 contains unconditional fallback logic that would affect "
            f"Windows installs where $SENZING_DIR\\data exists. "
            f"Fallback must only trigger when the standard path is missing."
        )


# ---------------------------------------------------------------------------
# Test 4 — Step 9 Flow Preserved (No Additional Gates)
# ---------------------------------------------------------------------------


class TestStep9FlowPreserved:
    """Verify Step 9 follows Step 8 without additional verification gates.

    **Validates: Requirements 3.4**

    Step 9 (Test Database Connection) must follow Step 8 (Create Engine
    Configuration) directly. The fix must not insert additional mandatory
    verification steps between them for non-Windows platforms.
    """

    def test_step9_follows_step8_in_sequence(self) -> None:
        """Step 9 must immediately follow Step 8 in the heading sequence."""
        content = _read_module_02()
        headings = _get_step_headings(content)
        step_numbers = [num for num, _ in headings]

        assert 8 in step_numbers, "Step 8 not found in module-02-sdk-setup.md"
        assert 9 in step_numbers, "Step 9 not found in module-02-sdk-setup.md"

        idx_8 = step_numbers.index(8)
        idx_9 = step_numbers.index(9)
        assert idx_9 == idx_8 + 1, (
            f"Step 9 does not immediately follow Step 8. "
            f"Step 8 is at index {idx_8}, Step 9 is at index {idx_9}. "
            f"No additional steps should be inserted between them."
        )

    def test_step9_is_database_connection_test(self) -> None:
        """Step 9 must be the database connection test."""
        content = _read_module_02()
        step9 = _extract_step_by_heading(content, 9)
        assert step9, "Step 9 section not found in module-02-sdk-setup.md"
        assert "database" in step9.lower() or "connection" in step9.lower(), (
            "Step 9 does not appear to be the database connection test. "
            "The flow from Step 8 to Step 9 must be preserved."
        )

    @given(scenario=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_additional_gates_between_step8_and_step9_for_non_windows(
        self, scenario: dict[str, str]
    ) -> None:
        """For non-Windows platforms, Step 8 flows directly into Step 9.

        **Validates: Requirements 3.4**

        Generate random non-Windows platform/install-method combinations and
        verify no additional verification gates exist between Step 8 and Step 9.
        The step sequence must remain 8 -> 9 without intermediate steps.
        """
        content = _read_module_02()
        headings = _get_step_headings(content)
        step_numbers = [num for num, _ in headings]

        assert 8 in step_numbers, "Step 8 not found"
        assert 9 in step_numbers, "Step 9 not found"

        idx_8 = step_numbers.index(8)
        idx_9 = step_numbers.index(9)

        assert idx_9 == idx_8 + 1, (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"Step 9 must immediately follow Step 8 without additional gates. "
            f"No intermediate verification steps should be inserted."
        )


# ---------------------------------------------------------------------------
# PBT Test — Preservation: Non-Bug-Condition Behavior Unchanged
# ---------------------------------------------------------------------------


class TestPreservationAcrossAllNonBugConditions:
    """PBT — Preservation across all non-bug-condition platform/install combinations.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    Generate random platform/install-method combinations that do NOT match
    the bug condition (Windows + Scoop + missing standard path) and verify
    ALL preservation properties hold simultaneously:
    1. sdk_guide(topic='configure') remains the starting point
    2. "NEVER construct ... manually" rule is preserved
    3. No unconditional fallback logic affects non-bug-condition scenarios
    4. Step 9 follows Step 8 without additional gates
    """

    _NEVER_CONSTRUCT_PATTERN = re.compile(
        r"NEVER construct.*manually",
        re.IGNORECASE,
    )

    _UNCONDITIONAL_FALLBACK = re.compile(
        r"(?<!windows)(?<!Windows)(?<!on Windows)"
        r"(?:always|unconditionally|for all platforms)\s+"
        r"(?:check|verify|fall\s*back)",
        re.IGNORECASE,
    )

    @given(scenario=st_any_non_bug_condition())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_preservation_properties_hold(
        self, scenario: dict[str, str]
    ) -> None:
        """For any non-bug-condition scenario, all preservation properties hold.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

        This is the comprehensive preservation property test that verifies
        the fix does not alter behavior for any platform/install combination
        that is NOT the specific bug condition.
        """
        content = _read_module_02()
        step8 = _extract_step_by_heading(content, 8)
        assert step8, "Step 8 section not found"

        # Property 1: MCP-first approach preserved
        assert "sdk_guide" in step8, (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"sdk_guide MCP tool reference missing from Step 8."
        )
        assert "topic='configure'" in step8 or 'topic=\'configure\'' in step8, (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"sdk_guide(topic='configure') call missing from Step 8."
        )

        # Property 2: "NEVER construct manually" rule preserved
        assert self._NEVER_CONSTRUCT_PATTERN.search(step8), (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"'NEVER construct ... manually' rule missing from Step 8."
        )

        # Property 3: No unconditional fallback
        assert not self._UNCONDITIONAL_FALLBACK.search(step8), (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"Unconditional fallback logic found in Step 8."
        )

        # Property 4: Step 9 follows Step 8
        headings = _get_step_headings(content)
        step_numbers = [num for num, _ in headings]
        assert 8 in step_numbers and 9 in step_numbers, (
            "Step 8 or Step 9 missing from steering file."
        )
        idx_8 = step_numbers.index(8)
        idx_9 = step_numbers.index(9)
        assert idx_9 == idx_8 + 1, (
            f"For platform={scenario['platform']}, "
            f"install_method={scenario['install_method']}: "
            f"Step 9 does not immediately follow Step 8."
        )
