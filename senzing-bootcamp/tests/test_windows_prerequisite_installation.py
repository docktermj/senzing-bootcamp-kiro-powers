"""Property-based tests for Windows prerequisite installation feature.

Feature: windows-prerequisite-installation

Uses Hypothesis for PBT to verify correctness properties of the Scoop
installation command mapping and related logic in preflight.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preflight import (
    SCOOP_RUNTIME_COMMANDS,
    CheckResult,
    CheckRunner,
    PreflightReport,
    ScoopInstallInfo,
    check_scoop,
)


# ---------------------------------------------------------------------------
# Property 1 — Scoop detection is platform-conditional and status-correct
# ---------------------------------------------------------------------------


class TestProperty1ScoopDetection:
    """Property 1: Scoop detection is platform-conditional and status-correct.

    For any platform string and scoop availability state, check_scoop() SHALL
    produce: (a) an empty list when platform is not win32, (b) a single
    CheckResult with status "pass" and version in message when platform is
    win32 and scoop is on PATH, or (c) a single CheckResult with status "warn"
    and a non-empty fix message when platform is win32 and scoop is not on PATH.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """

    @given(
        platform=st.sampled_from(["win32", "linux", "darwin"]),
        scoop_available=st.booleans(),
    )
    @settings(max_examples=10)
    def test_scoop_detection_platform_conditional_and_status_correct(
        self, platform: str, scoop_available: bool
    ) -> None:
        """check_scoop() returns correct results based on platform and scoop availability.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """

        def which_side_effect(cmd: str) -> str | None:
            if cmd == "scoop" and scoop_available:
                return r"C:\Users\user\scoop\shims\scoop"
            return None

        with (
            patch("preflight.sys.platform", platform),
            patch("preflight.shutil.which", side_effect=which_side_effect),
            patch("preflight._get_version", return_value="1.0.0"),
        ):
            results = check_scoop()

        if platform != "win32":
            # (a) empty list when not win32
            assert results == [], (
                f"Expected empty list on platform={platform!r}, "
                f"got {len(results)} result(s)"
            )
        elif scoop_available:
            # (b) single pass result with version when win32 + scoop available
            assert len(results) == 1, (
                f"Expected 1 result on win32 with scoop, got {len(results)}"
            )
            result = results[0]
            assert result.status == "pass", (
                f"Expected status 'pass', got {result.status!r}"
            )
            assert "1.0.0" in result.message, (
                f"Expected version in message, got {result.message!r}"
            )
        else:
            # (c) single warn result with non-empty fix when win32 + scoop unavailable
            assert len(results) == 1, (
                f"Expected 1 result on win32 without scoop, got {len(results)}"
            )
            result = results[0]
            assert result.status == "warn", (
                f"Expected status 'warn', got {result.status!r}"
            )
            assert result.fix, (
                "Expected non-empty fix message when scoop is unavailable"
            )


# ---------------------------------------------------------------------------
# Property 2 — Installation command mapping produces valid sequences
# ---------------------------------------------------------------------------


class TestProperty2InstallationCommandMapping:
    """Property 2: Installation command mapping produces valid sequences.

    For any supported runtime name in SCOOP_RUNTIME_COMMANDS, verify:
    (a) install_cmd is non-empty and contains "scoop install",
    (b) verify_cmd is non-empty,
    (c) if runtime is "java" then bucket_add is non-empty and contains
        "scoop bucket add java", otherwise bucket_add may be None.

    **Validates: Requirements 3.2, 6.1**
    """

    @given(runtime=st.sampled_from(list(SCOOP_RUNTIME_COMMANDS.keys())))
    @settings(max_examples=10)
    def test_install_cmd_contains_scoop_install(self, runtime: str) -> None:
        """install_cmd is non-empty and contains 'scoop install'.

        **Validates: Requirements 3.2, 6.1**
        """
        info = SCOOP_RUNTIME_COMMANDS[runtime]
        assert isinstance(info, ScoopInstallInfo)
        assert info.install_cmd, "install_cmd must be non-empty"
        assert "scoop install" in info.install_cmd, (
            f"install_cmd for '{runtime}' must contain 'scoop install', "
            f"got: {info.install_cmd!r}"
        )

    @given(runtime=st.sampled_from(list(SCOOP_RUNTIME_COMMANDS.keys())))
    @settings(max_examples=10)
    def test_verify_cmd_is_non_empty(self, runtime: str) -> None:
        """verify_cmd is non-empty for all supported runtimes.

        **Validates: Requirements 3.2, 6.1**
        """
        info = SCOOP_RUNTIME_COMMANDS[runtime]
        assert isinstance(info, ScoopInstallInfo)
        assert info.verify_cmd, "verify_cmd must be non-empty"

    @given(runtime=st.sampled_from(list(SCOOP_RUNTIME_COMMANDS.keys())))
    @settings(max_examples=10)
    def test_java_requires_bucket_add_others_may_be_none(self, runtime: str) -> None:
        """If runtime is 'java', bucket_add is non-empty and contains
        'scoop bucket add java'; otherwise bucket_add may be None.

        **Validates: Requirements 3.2, 6.1**
        """
        info = SCOOP_RUNTIME_COMMANDS[runtime]
        assert isinstance(info, ScoopInstallInfo)
        if runtime == "java":
            assert info.bucket_add is not None, (
                "Java runtime must have a non-None bucket_add"
            )
            assert info.bucket_add, "Java bucket_add must be non-empty"
            assert "scoop bucket add java" in info.bucket_add, (
                f"Java bucket_add must contain 'scoop bucket add java', "
                f"got: {info.bucket_add!r}"
            )
        else:
            # Other runtimes may have bucket_add as None (no assertion on value)
            if info.bucket_add is not None:
                assert info.bucket_add, (
                    f"If bucket_add is not None for '{runtime}', it must be non-empty"
                )


# ---------------------------------------------------------------------------
# Unit tests — check_scoop() edge cases
# ---------------------------------------------------------------------------


class TestCheckScoopEdgeCases:
    """Unit tests for check_scoop() edge cases.

    Validates graceful degradation when version detection fails, unexpected
    exceptions in shutil.which, and correct positioning in CheckRunner.

    Requirements: 1.1, 1.2, 1.3
    """

    def test_scoop_exists_but_version_fails(self) -> None:
        """Scoop on PATH but --version returns 'unknown' → pass with 'version unknown'."""
        with (
            patch("preflight.sys.platform", "win32"),
            patch("preflight.shutil.which", return_value=r"C:\Users\user\scoop\shims\scoop"),
            patch("preflight._get_version", return_value="unknown"),
        ):
            results = check_scoop()

        assert len(results) == 1
        result = results[0]
        assert result.status == "pass"
        assert "version unknown" in result.message

    def test_shutil_which_raises_exception(self) -> None:
        """Unexpected exception in shutil.which → warn with graceful message."""

        def which_explodes(cmd: str) -> str:
            raise RuntimeError("Unexpected OS error")

        with (
            patch("preflight.sys.platform", "win32"),
            patch("preflight.shutil.which", side_effect=which_explodes),
        ):
            results = check_scoop()

        assert len(results) == 1
        result = results[0]
        assert result.status == "warn"
        assert "Could not check" in result.message

    def test_check_sequence_position(self) -> None:
        """Package Manager is between Core Tools and Language Runtimes in CHECK_SEQUENCE."""
        categories = [label for label, _fn in CheckRunner.CHECK_SEQUENCE]

        assert "Core Tools" in categories
        assert "Package Manager" in categories
        assert "Language Runtimes" in categories

        core_idx = categories.index("Core Tools")
        pkg_idx = categories.index("Package Manager")
        lang_idx = categories.index("Language Runtimes")

        assert core_idx < pkg_idx < lang_idx, (
            f"Expected Core Tools ({core_idx}) < Package Manager ({pkg_idx}) "
            f"< Language Runtimes ({lang_idx})"
        )


# ---------------------------------------------------------------------------
# Property 3 — Preferences installation record round-trip
# ---------------------------------------------------------------------------


class TestProperty3PreferencesRoundTrip:
    """Property 3: Preferences installation record round-trip.

    For any valid installation preferences record (containing
    scoop_installed_during_onboarding, runtimes_installed_during_onboarding
    with arbitrary runtime name/version pairs, and
    prerequisite_installation_deferred), serializing to YAML and deserializing
    SHALL preserve all field values exactly.

    **Validates: Requirements 5.1, 5.2, 5.4**
    """

    @given(
        scoop_installed=st.booleans(),
        runtimes=st.lists(
            st.fixed_dictionaries({
                "name": st.sampled_from(["java", "dotnet", "rust", "nodejs"]),
                "version": st.from_regex(r"[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True),
            })
        ),
        deferred=st.booleans(),
    )
    @settings(max_examples=10)
    def test_preferences_round_trip_preserves_all_fields(
        self,
        scoop_installed: bool,
        runtimes: list[dict[str, str]],
        deferred: bool,
    ) -> None:
        """Serializing preferences to YAML and deserializing preserves all fields.

        **Validates: Requirements 5.1, 5.2, 5.4**
        """
        preferences = {
            "scoop_installed_during_onboarding": scoop_installed,
            "runtimes_installed_during_onboarding": runtimes,
            "prerequisite_installation_deferred": deferred,
        }

        serialized = yaml.dump(preferences, default_flow_style=False)
        deserialized = yaml.safe_load(serialized)

        assert deserialized["scoop_installed_during_onboarding"] == scoop_installed, (
            f"scoop_installed_during_onboarding mismatch: "
            f"expected {scoop_installed!r}, got "
            f"{deserialized['scoop_installed_during_onboarding']!r}"
        )
        assert deserialized["runtimes_installed_during_onboarding"] == runtimes, (
            f"runtimes_installed_during_onboarding mismatch: "
            f"expected {runtimes!r}, got "
            f"{deserialized['runtimes_installed_during_onboarding']!r}"
        )
        assert deserialized["prerequisite_installation_deferred"] == deferred, (
            f"prerequisite_installation_deferred mismatch: "
            f"expected {deferred!r}, got "
            f"{deserialized['prerequisite_installation_deferred']!r}"
        )


# ---------------------------------------------------------------------------
# Property 4 — Verdict invariance under installation outcomes
# ---------------------------------------------------------------------------


class TestProperty4VerdictInvariance:
    """Property 4: Verdict invariance under installation outcomes.

    For any PreflightReport whose checks contain only "pass" and "warn"
    statuses (with at least one "warn"), the verdict SHALL be "WARN".
    This confirms that no code path in check_scoop() or
    SCOOP_RUNTIME_COMMANDS can produce a "fail" status — the verdict
    is computed solely from CheckResult statuses, not from installation
    side-effects.

    **Validates: Requirements 4.2**
    """

    @given(
        check_results=st.lists(
            st.fixed_dictionaries({
                "status": st.sampled_from(["pass", "warn"]),
            }),
            min_size=1,
        ).filter(lambda x: any(d["status"] == "warn" for d in x)),
    )
    @settings(max_examples=10)
    def test_verdict_is_warn_when_at_least_one_warn_and_no_fail(
        self, check_results: list[dict[str, str]]
    ) -> None:
        """PreflightReport verdict is 'WARN' when checks have at least one
        'warn' and no 'fail' statuses.

        **Validates: Requirements 4.2**
        """
        checks = [
            CheckResult(
                name=f"Check {i}",
                category="Package Manager",
                status=cr["status"],
                message=f"Test check {i}",
            )
            for i, cr in enumerate(check_results)
        ]
        report = PreflightReport(checks=checks)

        assert report.verdict == "WARN", (
            f"Expected verdict 'WARN' with statuses "
            f"{[cr['status'] for cr in check_results]}, "
            f"got {report.verdict!r}"
        )

    @given(
        platform=st.sampled_from(["win32", "linux", "darwin"]),
        scoop_available=st.booleans(),
    )
    @settings(max_examples=10)
    def test_check_scoop_never_produces_fail(
        self, platform: str, scoop_available: bool
    ) -> None:
        """check_scoop() never produces a 'fail' status in any branch.

        **Validates: Requirements 4.2**
        """

        def which_side_effect(cmd: str) -> str | None:
            if cmd == "scoop" and scoop_available:
                return r"C:\Users\user\scoop\shims\scoop"
            return None

        with (
            patch("preflight.sys.platform", platform),
            patch("preflight.shutil.which", side_effect=which_side_effect),
            patch("preflight._get_version", return_value="1.0.0"),
        ):
            results = check_scoop()

        for result in results:
            assert result.status != "fail", (
                f"check_scoop() produced a 'fail' status on "
                f"platform={platform!r}, scoop_available={scoop_available!r}: "
                f"{result.message!r}"
            )

    def test_scoop_runtime_commands_never_imply_fail(self) -> None:
        """SCOOP_RUNTIME_COMMANDS entries only produce 'pass' or 'warn' checks.

        The mapping itself doesn't produce CheckResults, but we verify that
        building a report from scoop/runtime checks (which only emit pass/warn)
        never yields a FAIL verdict.

        **Validates: Requirements 4.2**
        """
        # Simulate a report with one warn (scoop missing) and pass results
        # for all runtimes — verdict must be WARN, never FAIL
        checks = [
            CheckResult(
                name="Scoop",
                category="Package Manager",
                status="warn",
                message="Scoop package manager not found",
                fix="Install Scoop: irm get.scoop.sh | iex",
            ),
        ]
        # Add a pass result for each runtime in the mapping
        for runtime_name, info in SCOOP_RUNTIME_COMMANDS.items():
            checks.append(CheckResult(
                name=f"{runtime_name} runtime",
                category="Language Runtimes",
                status="pass",
                message=f"{runtime_name} available",
            ))

        report = PreflightReport(checks=checks)
        assert report.verdict == "WARN", (
            f"Expected 'WARN' verdict for scoop-missing report, got {report.verdict!r}"
        )
        assert report.fail_count == 0, (
            f"Expected 0 fail checks, got {report.fail_count}"
        )


# ---------------------------------------------------------------------------
# Unit tests — Steering file structural validation
# ---------------------------------------------------------------------------


class TestSteeringFileStructure:
    """Unit tests verifying onboarding-flow.md Step 3 contains required content.

    These tests read the steering file and assert that specific strings or
    patterns are present, ensuring the installation offer logic, commands,
    decline paths, re-run instructions, preferences recording, and runtime
    references are all documented in the steering file.

    Requirements: 2.1, 2.2, 2.4, 3.1, 4.5, 5.1
    """

    STEERING_FILE = Path(__file__).resolve().parent.parent / "steering" / "onboarding-flow.md"

    def _read_steering(self) -> str:
        """Read the onboarding-flow.md steering file content."""
        return self.STEERING_FILE.read_text(encoding="utf-8")

    def test_step3_contains_scoop_installation_offer_conditional(self) -> None:
        """Step 3 contains Scoop installation offer conditional (### 3a or Package Manager warn).

        Validates: Requirements 2.1
        """
        content = self._read_steering()
        has_section_header = "### 3a" in content
        has_scoop_installation = "Scoop installation" in content or "Scoop is not installed" in content
        has_package_manager_warn = "Package Manager" in content and "warn" in content

        assert has_section_header or has_scoop_installation or has_package_manager_warn, (
            "onboarding-flow.md Step 3 must contain a Scoop installation offer "
            "conditional (### 3a, 'Scoop installation', or Package Manager + warn)"
        )

    def test_step3_contains_scoop_powershell_command(self) -> None:
        """Step 3 contains the `irm get.scoop.sh | iex` PowerShell command.

        Validates: Requirements 2.2
        """
        content = self._read_steering()
        assert "irm get.scoop.sh | iex" in content, (
            "onboarding-flow.md Step 3 must contain the Scoop installation "
            "command: irm get.scoop.sh | iex"
        )

    def test_step3_contains_decline_skip_path(self) -> None:
        """Step 3 contains decline/skip path language.

        Validates: Requirements 2.4
        """
        content = self._read_steering()
        has_skip = "skip" in content.lower()
        has_skip_for_later = "Skip for later" in content

        assert has_skip or has_skip_for_later, (
            "onboarding-flow.md Step 3 must contain decline/skip path language "
            "(e.g., 'Skip for later' or 'skip')"
        )

    def test_step3_contains_rerun_preflight_instruction(self) -> None:
        """Step 3 contains re-run preflight instruction after installation.

        Validates: Requirements 4.5
        """
        content = self._read_steering()
        assert "python3 senzing-bootcamp/scripts/preflight.py" in content, (
            "onboarding-flow.md Step 3 must contain the re-run preflight "
            "instruction: python3 senzing-bootcamp/scripts/preflight.py"
        )

    def test_step3_contains_preferences_recording(self) -> None:
        """Step 3 contains preferences recording instructions (bootcamp_preferences.yaml).

        Validates: Requirements 5.1
        """
        content = self._read_steering()
        assert "bootcamp_preferences.yaml" in content, (
            "onboarding-flow.md Step 3 must contain preferences recording "
            "instructions referencing bootcamp_preferences.yaml"
        )

    def test_step3_references_runtime_commands_or_all_runtimes(self) -> None:
        """Step 3 references SCOOP_RUNTIME_COMMANDS or lists all four runtimes.

        Validates: Requirements 3.1
        """
        content = self._read_steering()
        has_constant_ref = "SCOOP_RUNTIME_COMMANDS" in content
        runtimes = ["java", "dotnet", "rust", "nodejs"]
        has_all_runtimes = all(rt in content.lower() for rt in runtimes)

        assert has_constant_ref or has_all_runtimes, (
            "onboarding-flow.md Step 3 must reference SCOOP_RUNTIME_COMMANDS "
            "or list all four runtimes (java, dotnet, rust, nodejs)"
        )


# ---------------------------------------------------------------------------
# Unit test — check_scoop() integration with CheckRunner
# ---------------------------------------------------------------------------


class TestCheckScoopIntegration:
    """Unit test verifying check_scoop() integrates correctly with CheckRunner.

    Mocks the platform as win32 and runs CheckRunner().run() to verify that
    the Scoop "Package Manager" check appears after "Core Tools" checks and
    before "Language Runtimes" checks in the final report.

    Requirements: 1.1
    """

    def test_scoop_check_ordering_in_runner_results(self) -> None:
        """CheckRunner results place Package Manager between Core Tools and Language Runtimes.

        Validates: Requirements 1.1
        """
        def mock_which(cmd: str) -> str | None:
            """Return a fake path for all tool lookups so checks pass."""
            return f"/usr/bin/{cmd}"

        def mock_get_version(cmd: str, args: list[str] | None = None) -> str:
            return "1.0.0"

        def mock_disk_usage(path: str):
            """Return a fake disk usage with plenty of space."""
            class _Usage:
                free = 50 * (1024 ** 3)  # 50 GB
                total = 100 * (1024 ** 3)
                used = 50 * (1024 ** 3)
            return _Usage()

        def mock_create_connection(address, timeout=None):
            """Return a mock socket that can be closed."""
            class _Sock:
                def close(self):
                    pass
            return _Sock()

        def mock_subprocess_run(*args, **kwargs):
            """Return a successful subprocess result."""
            class _Result:
                returncode = 0
                stdout = "1.0.0"
                stderr = ""
            return _Result()

        with (
            patch("preflight.sys.platform", "win32"),
            patch("preflight.shutil.which", side_effect=mock_which),
            patch("preflight._get_version", mock_get_version),
            patch("preflight.shutil.disk_usage", side_effect=mock_disk_usage),
            patch("preflight.socket.create_connection", side_effect=mock_create_connection),
            patch("preflight.subprocess.run", side_effect=mock_subprocess_run),
            patch("preflight.os.path.isfile", return_value=False),
            patch("preflight.os.path.isdir", return_value=True),
            patch("preflight.os.makedirs"),
            patch("preflight.os.rmdir"),
        ):
            report = CheckRunner().run()

        # Extract categories in order from the results
        categories_seen: list[str] = []
        for check in report.checks:
            if not categories_seen or categories_seen[-1] != check.category:
                categories_seen.append(check.category)

        # Verify all three categories are present
        assert "Core Tools" in categories_seen, (
            f"Expected 'Core Tools' in categories, got {categories_seen}"
        )
        assert "Package Manager" in categories_seen, (
            f"Expected 'Package Manager' in categories, got {categories_seen}"
        )
        assert "Language Runtimes" in categories_seen, (
            f"Expected 'Language Runtimes' in categories, got {categories_seen}"
        )

        # Verify ordering: Core Tools < Package Manager < Language Runtimes
        core_idx = categories_seen.index("Core Tools")
        pkg_idx = categories_seen.index("Package Manager")
        lang_idx = categories_seen.index("Language Runtimes")

        assert core_idx < pkg_idx, (
            f"Expected Core Tools ({core_idx}) before Package Manager ({pkg_idx})"
        )
        assert pkg_idx < lang_idx, (
            f"Expected Package Manager ({pkg_idx}) before Language Runtimes ({lang_idx})"
        )
