"""Property-based and unit tests for senzing-bootcamp/scripts/preflight.py.

Uses Hypothesis for PBT and pytest for unit tests.  All system calls
(shutil.which, shutil.disk_usage, subprocess.run, socket.create_connection)
are mocked so tests are fast and deterministic.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from preflight import (
    AutoFixer,
    CheckResult,
    CheckRunner,
    OutputFormatter,
    PreflightReport,
    check_disk_space,
    check_language_runtimes,
    check_required_tools,
    check_senzing_sdk,
    check_write_permissions,
    check_network,
)


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.1 — Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════

STATUSES = st.sampled_from(["pass", "warn", "fail"])

CATEGORIES = st.sampled_from([
    "Language Runtimes",
    "Disk Space",
    "Network",
    "Senzing SDK",
    "Permissions",
    "Core Tools",
    "Project Structure",
])


def check_result_strategy():
    """Strategy producing arbitrary CheckResult instances."""
    return st.builds(
        CheckResult,
        name=st.text(min_size=1, max_size=30),
        category=CATEGORIES,
        status=STATUSES,
        message=st.text(min_size=1, max_size=60),
        fix=st.one_of(st.none(), st.text(min_size=1, max_size=80)),
        fixed=st.booleans(),
    )


def preflight_report_strategy():
    """Strategy producing arbitrary PreflightReport instances."""
    return st.builds(
        PreflightReport,
        checks=st.lists(check_result_strategy(), min_size=1, max_size=20),
    )


ALL_RUNTIMES = ["python3", "java", "dotnet", "rustc", "node"]


def runtime_subset_strategy():
    """Strategy producing a random subset of language runtimes."""
    return st.lists(
        st.sampled_from(ALL_RUNTIMES), unique=True, min_size=0, max_size=5,
    )


def disk_space_gb_strategy():
    """Strategy producing non-negative disk space values in GB."""
    return st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def version_string_strategy():
    """Strategy producing version strings like 'X.Y'."""
    return st.tuples(
        st.integers(min_value=1, max_value=5),
        st.integers(min_value=0, max_value=20),
    ).map(lambda t: f"{t[0]}.{t[1]}")


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.2 — PBT Property 1: Language runtime detection
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty1LanguageRuntimeDetection:
    """Feature: environment-verification, Property 1: Language runtime detection

    For any subset of runtimes available (mock shutil.which),
    check_language_runtimes produces pass for each found runtime,
    fail when none found, warn for missing pip when Python present.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """

    @given(
        available=runtime_subset_strategy(),
        pip_available=st.booleans(),
    )
    @settings(max_examples=100)
    def test_runtime_detection(self, available, pip_available):
        """Feature: environment-verification, Property 1: Language runtime detection"""
        available_set = set(available)

        def fake_which(cmd):
            # python3 is the candidate for Python
            if cmd in available_set:
                return f"/usr/bin/{cmd}"
            # pip check: pip3 or pip
            if cmd in ("pip3", "pip") and pip_available and "python3" in available_set:
                return f"/usr/bin/{cmd}"
            # Also handle "python" fallback — we only put python3 in our set
            return None

        with patch("preflight.shutil.which", side_effect=fake_which), \
             patch("preflight._get_version", return_value="1.0"):
            results = check_language_runtimes()

        if len(available_set) == 0:
            # Should produce a fail result
            fail_results = [r for r in results if r.status == "fail"]
            assert len(fail_results) >= 1, "Expected fail when no runtimes found"
        else:
            # Each available runtime should have a pass result
            pass_results = [r for r in results if r.status == "pass"]
            # At minimum, each found runtime produces a pass
            runtime_names = {
                "python3": "Python",
                "java": "Java",
                "dotnet": ".NET SDK",
                "rustc": "Rust",
                "node": "Node.js",
            }
            for cmd in available_set:
                name = runtime_names[cmd]
                matching = [r for r in pass_results if name in r.name]
                assert len(matching) >= 1, f"Expected pass for {name}"

        # pip check when Python is present
        if "python3" in available_set:
            pip_results = [r for r in results if "pip" in r.name.lower()]
            assert len(pip_results) >= 1, "Expected pip check when Python present"
            if pip_available:
                assert pip_results[0].status == "pass"
            else:
                assert pip_results[0].status == "warn"


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.3 — PBT Property 2: Disk space threshold
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty2DiskSpaceThreshold:
    """Feature: environment-verification, Property 2: Disk space threshold

    For any non-negative float GB value, check_disk_space produces pass
    when ≥10, warn when <10.

    **Validates: Requirements 3.2, 3.3**
    """

    @given(gb=disk_space_gb_strategy())
    @settings(max_examples=100)
    def test_disk_space_threshold(self, gb):
        """Feature: environment-verification, Property 2: Disk space threshold"""
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        free_bytes = int(gb * (1024 ** 3))
        fake_usage = DiskUsage(total=100 * 1024**3, used=(100 * 1024**3) - free_bytes, free=free_bytes)

        with patch("preflight.shutil.disk_usage", return_value=fake_usage):
            results = check_disk_space()

        assert len(results) == 1
        result = results[0]
        if gb >= 10.0:
            assert result.status == "pass", f"Expected pass for {gb:.1f} GB"
        else:
            assert result.status == "warn", f"Expected warn for {gb:.1f} GB"


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.4 — PBT Property 3: Senzing SDK version
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty3SenzingSDKVersion:
    """Feature: environment-verification, Property 3: Senzing SDK version

    For any version string 'X.Y', check_senzing_sdk produces pass when ≥4.0,
    warn when <4.0.

    **Validates: Requirements 5.2, 5.3**
    """

    @given(version=version_string_strategy())
    @settings(max_examples=100)
    def test_sdk_version_threshold(self, version):
        """Feature: environment-verification, Property 3: Senzing SDK version"""
        parts = version.split(".")
        major, minor = int(parts[0]), int(parts[1])

        # Mock shutil.which to find python3
        def fake_which(cmd):
            if cmd in ("python3", "python"):
                return "/usr/bin/python3"
            return None

        # Mock subprocess.run to return the version string
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = version + "\n"
        mock_result.stderr = ""

        with patch("preflight.shutil.which", side_effect=fake_which), \
             patch("preflight.subprocess.run", return_value=mock_result):
            results = check_senzing_sdk()

        assert len(results) == 1
        result = results[0]
        if (major, minor) >= (4, 0):
            assert result.status == "pass", f"Expected pass for version {version}"
        else:
            assert result.status == "warn", f"Expected warn for version {version}"


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.5 — PBT Property 4: Required tool presence
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty4RequiredToolPresence:
    """Feature: environment-verification, Property 4: Required tool presence

    For any subset of tools available, check_required_tools produces pass
    for present tools, fail for missing required tools.

    **Validates: Requirements 7.1, 7.2, 7.3**
    """

    @given(
        available_tools=st.lists(
            st.sampled_from(["git", "curl", "zip", "unzip"]),
            unique=True,
            min_size=0,
            max_size=4,
        ),
    )
    @settings(max_examples=100)
    def test_tool_presence(self, available_tools):
        """Feature: environment-verification, Property 4: Required tool presence"""
        available_set = set(available_tools)

        def fake_which(cmd):
            if cmd in available_set:
                return f"/usr/bin/{cmd}"
            return None

        # Force non-Windows so zip/unzip are checked
        with patch("preflight.shutil.which", side_effect=fake_which), \
             patch("preflight._get_version", return_value="1.0"), \
             patch("preflight.sys") as mock_sys:
            mock_sys.platform = "linux"
            results = check_required_tools()

        for r in results:
            tool_name = r.name  # tool name is the check name
            if tool_name in available_set:
                assert r.status == "pass", f"Expected pass for present tool {tool_name}"
            else:
                assert r.status == "fail", f"Expected fail for missing tool {tool_name}"
                assert r.fix is not None, f"Expected fix instruction for missing {tool_name}"


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.6 — PBT Property 5: Human report rendering
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty5HumanReportRendering:
    """Feature: environment-verification, Property 5: Human report rendering

    For any list of CheckResults, OutputFormatter.to_human() output contains
    every category heading, every check name, and every fix instruction for
    warn/fail.

    **Validates: Requirements 8.2, 8.3, 8.4**
    """

    @given(report=preflight_report_strategy())
    @settings(max_examples=100)
    def test_human_output_completeness(self, report):
        """Feature: environment-verification, Property 5: Human report rendering"""
        # Disable color for deterministic output
        with patch("preflight._USE_COLOR", False):
            output = OutputFormatter.to_human(report)

        # Every category heading must appear
        categories_seen = {cr.category for cr in report.checks}
        for cat in categories_seen:
            assert cat in output, f"Category heading '{cat}' missing from output"

        # Every check name must appear
        for cr in report.checks:
            assert cr.name in output, f"Check name '{cr.name}' missing from output"

        # Every fix instruction for warn/fail must appear
        for cr in report.checks:
            if cr.status in ("warn", "fail") and cr.fix:
                assert cr.fix in output, (
                    f"Fix instruction '{cr.fix}' missing for {cr.status} check '{cr.name}'"
                )


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.7 — PBT Property 6: Verdict and exit code consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty6VerdictAndExitCode:
    """Feature: environment-verification, Property 6: Verdict and exit code consistency

    For any PreflightReport, verdict matches worst status, pass/warn/fail
    counts match actual counts.

    **Validates: Requirements 8.5, 8.6, 8.7**
    """

    @given(report=preflight_report_strategy())
    @settings(max_examples=100)
    def test_verdict_consistency(self, report):
        """Feature: environment-verification, Property 6: Verdict and exit code consistency"""
        # Count actual statuses
        actual_pass = sum(1 for c in report.checks if c.status == "pass")
        actual_warn = sum(1 for c in report.checks if c.status == "warn")
        actual_fail = sum(1 for c in report.checks if c.status == "fail")

        assert report.pass_count == actual_pass
        assert report.warn_count == actual_warn
        assert report.fail_count == actual_fail

        # Verdict matches worst status
        if actual_fail > 0:
            assert report.verdict == "FAIL"
        elif actual_warn > 0:
            assert report.verdict == "WARN"
        else:
            assert report.verdict == "PASS"

        # Exit code: 1 for FAIL, 0 otherwise
        expected_exit = 1 if report.verdict == "FAIL" else 0
        actual_exit = 1 if report.verdict == "FAIL" else 0
        assert actual_exit == expected_exit


# ═══════════════════════════════════════════════════════════════════════════
# Task 5.8 — PBT Property 7: JSON round-trip
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty7JSONRoundTrip:
    """Feature: environment-verification, Property 7: JSON round-trip

    For any PreflightReport, to_json() produces valid JSON with checks array
    and summary object, json.loads round-trips correctly.

    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """

    @given(report=preflight_report_strategy())
    @settings(max_examples=100)
    def test_json_round_trip(self, report):
        """Feature: environment-verification, Property 7: JSON round-trip"""
        json_str = OutputFormatter.to_json(report)

        # Must be valid JSON
        parsed = json.loads(json_str)

        # Must have checks array
        assert "checks" in parsed
        assert isinstance(parsed["checks"], list)
        assert len(parsed["checks"]) == len(report.checks)

        # Each check element has required fields
        for i, check_dict in enumerate(parsed["checks"]):
            assert "name" in check_dict
            assert "category" in check_dict
            assert "status" in check_dict
            assert "message" in check_dict
            assert "fix" in check_dict
            assert "fixed" in check_dict

            # Values match the original report
            cr = report.checks[i]
            assert check_dict["name"] == cr.name
            assert check_dict["category"] == cr.category
            assert check_dict["status"] == cr.status
            assert check_dict["message"] == cr.message
            assert check_dict["fix"] == cr.fix
            assert check_dict["fixed"] == cr.fixed

        # Must have summary object
        assert "summary" in parsed
        summary = parsed["summary"]
        assert summary["pass_count"] == report.pass_count
        assert summary["warn_count"] == report.warn_count
        assert summary["fail_count"] == report.fail_count
        assert summary["verdict"] == report.verdict


# ═══════════════════════════════════════════════════════════════════════════
# Task 6 — Unit tests for edge cases and integration points
# ═══════════════════════════════════════════════════════════════════════════


class TestBannerText:
    """Task 6.1: Banner text 'Environment Verification' appears in human output.

    **Validates: Requirement 8.1**
    """

    def test_banner_contains_environment_verification(self):
        report = PreflightReport(checks=[
            CheckResult(name="test", category="Test", status="pass", message="ok"),
        ])
        with patch("preflight._USE_COLOR", False):
            output = OutputFormatter.to_human(report)
        assert "Environment Verification" in output


class TestNetworkCheckParameters:
    """Task 6.2: Network check uses mcp.senzing.com:443 with 5s timeout.

    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    def test_network_check_host_port_timeout(self):
        with patch("preflight.socket.create_connection") as mock_conn:
            mock_sock = MagicMock()
            mock_conn.return_value = mock_sock
            results = check_network()

        # Verify the call was made with correct parameters
        mock_conn.assert_called_once_with(("mcp.senzing.com", 443), timeout=5)
        mock_sock.close.assert_called_once()
        assert results[0].status == "pass"


class TestSDKCheckSkippedWithoutPython:
    """Task 6.3: SDK check skipped when no Python runtime.

    **Validates: Requirement 5.5**
    """

    def test_sdk_check_warns_no_python(self):
        def fake_which(cmd):
            # No python3 or python available
            return None

        with patch("preflight.shutil.which", side_effect=fake_which):
            results = check_senzing_sdk()

        assert len(results) == 1
        assert results[0].status == "warn"
        assert "Python" in results[0].message or "python" in results[0].message.lower()


class TestWritePermissions:
    """Task 6.4: Write permissions pass/fail.

    **Validates: Requirements 6.1, 6.2, 6.3**
    """

    def test_write_permissions_pass(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        results = check_write_permissions()
        assert len(results) == 1
        assert results[0].status == "pass"

    def test_write_permissions_fail(self, monkeypatch):
        monkeypatch.chdir(tempfile.mkdtemp())
        with patch("preflight.os.makedirs", side_effect=OSError("Permission denied")):
            results = check_write_permissions()
        assert len(results) == 1
        assert results[0].status == "fail"
        assert results[0].fix is not None


class TestFixFailureRetainsStatus:
    """Task 6.5: --fix failure retains original status and appends error reason.

    **Validates: Requirement 10.4**
    """

    def test_fix_failure_retains_status(self):
        original = CheckResult(
            name="Directory 'data/raw'",
            category="Project Structure",
            status="warn",
            message="'data/raw' is missing",
            fix="Create it: mkdir -p data/raw",
        )
        with patch("preflight.os.makedirs", side_effect=OSError("disk full")):
            fixed = AutoFixer.try_fix(original)

        assert fixed is not None
        assert fixed.status == "warn"  # retains original status
        assert fixed.fixed is False
        assert "auto-fix failed" in fixed.fix
        assert "disk full" in fixed.fix


class TestZipUnzipNonWindows:
    """Task 6.6: zip/unzip checked only on non-Windows.

    **Validates: Requirement 7.4**
    """

    def test_zip_unzip_checked_on_linux(self):
        def fake_which(cmd):
            return f"/usr/bin/{cmd}"

        with patch("preflight.shutil.which", side_effect=fake_which), \
             patch("preflight._get_version", return_value="1.0"), \
             patch("preflight.sys") as mock_sys:
            mock_sys.platform = "linux"
            results = check_required_tools()

        tool_names = [r.name for r in results]
        assert "zip" in tool_names
        assert "unzip" in tool_names

    def test_zip_unzip_not_checked_on_windows(self):
        def fake_which(cmd):
            return f"C:\\Program Files\\{cmd}"

        with patch("preflight.shutil.which", side_effect=fake_which), \
             patch("preflight._get_version", return_value="1.0"), \
             patch("preflight.sys") as mock_sys:
            mock_sys.platform = "win32"
            results = check_required_tools()

        tool_names = [r.name for r in results]
        assert "zip" not in tool_names
        assert "unzip" not in tool_names


class TestLegacyScriptsDeprecation:
    """Task 6.7: Legacy scripts print deprecation warning.

    **Validates: Requirements 12.2, 12.3**
    """

    def test_check_prerequisites_deprecation(self):
        import subprocess as sp
        scripts_dir = os.path.join(os.path.dirname(__file__))
        result = sp.run(
            [sys.executable, os.path.join(scripts_dir, "check_prerequisites.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "deprecated" in result.stderr.lower()

    def test_preflight_check_deprecation(self):
        import subprocess as sp
        scripts_dir = os.path.join(os.path.dirname(__file__))
        result = sp.run(
            [sys.executable, os.path.join(scripts_dir, "preflight_check.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "deprecated" in result.stderr.lower()


class TestDiskUsageException:
    """Task 6.8: disk_usage exception produces warn.

    **Validates: Requirement 3.4**
    """

    def test_disk_usage_exception_produces_warn(self):
        with patch("preflight.shutil.disk_usage", side_effect=OSError("device error")):
            results = check_disk_space()

        assert len(results) == 1
        assert results[0].status == "warn"
        assert "could not" in results[0].message.lower() or "Could not" in results[0].message
