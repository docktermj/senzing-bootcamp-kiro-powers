"""Unit tests for version functionality.

Example-based tests covering read_version, validate_version, CLI behavior,
onboarding integration, and VERSION file smoke checks.

Feature: display-version-on-start
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from version import (  # noqa: E402
    VERSION_FILE_PATH,
    VersionError,
    format_version_display,
    main,
    read_version,
    validate_version,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_POWER_ROOT = Path(__file__).resolve().parent.parent
_ONBOARDING_FLOW = _POWER_ROOT / "steering" / "onboarding-flow.md"
_VERSION_FILE = _POWER_ROOT / "VERSION"


# ---------------------------------------------------------------------------
# TestReadVersion
# ---------------------------------------------------------------------------


class TestReadVersion:
    """Tests for read_version function.

    Validates: Requirements 1.2, 1.3, 1.4, 2.4
    """

    def test_read_version_from_default_path(self) -> None:
        """read_version() reads from the default VERSION file without error."""
        version = read_version()
        assert version == "0.11.0"

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """read_version raises VersionError when the file does not exist."""
        missing = tmp_path / "DOES_NOT_EXIST"
        with pytest.raises(VersionError) as exc_info:
            read_version(missing)
        assert exc_info.value.file_path == missing

    def test_empty_file_raises_error(self, tmp_path: Path) -> None:
        """read_version raises VersionError when the file is empty."""
        empty_file = tmp_path / "VERSION"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises(VersionError) as exc_info:
            read_version(empty_file)
        assert exc_info.value.file_path == empty_file


# ---------------------------------------------------------------------------
# TestValidateVersion
# ---------------------------------------------------------------------------


class TestValidateVersion:
    """Tests for validate_version function.

    Validates: Requirements 3.1, 3.3
    """

    @pytest.mark.parametrize("version", ["0.1.0", "1.0.0", "99.99.99"])
    def test_valid_versions_accepted(self, version: str) -> None:
        """Known-good version strings pass validation."""
        assert validate_version(version) == version

    @pytest.mark.parametrize("version", ["01.2.3", "1.02.3", "1.2.03"])
    def test_leading_zeros_rejected(self, version: str) -> None:
        """Version strings with leading zeros are rejected."""
        with pytest.raises(VersionError):
            validate_version(version)

    @pytest.mark.parametrize("version", ["1.2.3-alpha", "0.1.0-rc.1"])
    def test_prerelease_rejected(self, version: str) -> None:
        """Version strings with pre-release identifiers are rejected."""
        with pytest.raises(VersionError):
            validate_version(version)

    @pytest.mark.parametrize("version", ["1.2.3+build", "0.1.0+20230101"])
    def test_build_metadata_rejected(self, version: str) -> None:
        """Version strings with build metadata are rejected."""
        with pytest.raises(VersionError):
            validate_version(version)


# ---------------------------------------------------------------------------
# TestCli
# ---------------------------------------------------------------------------


class TestCli:
    """Tests for CLI behavior via main().

    Validates: Requirements 4.1, 2.2, 4.5
    """

    def test_cli_raw_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        """CLI with --format raw outputs just the version string."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--format", "raw"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "0.11.0"

    def test_cli_display_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        """CLI with --format display outputs the full display string."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--format", "display"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "Senzing Bootcamp Power v0.11.0"

    def test_cli_missing_file_exit_code(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """CLI exits with code 1 when the VERSION file is missing."""
        missing = tmp_path / "NONEXISTENT"
        with pytest.raises(SystemExit) as exc_info:
            main(["--file", str(missing)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert str(missing) in captured.err


# ---------------------------------------------------------------------------
# TestOnboardingIntegration
# ---------------------------------------------------------------------------


class TestOnboardingIntegration:
    """Tests for onboarding-flow.md version step integration.

    Validates: Requirements 2.1
    """

    def test_onboarding_flow_has_version_step(self) -> None:
        """onboarding-flow.md contains the '## 0c. Version Display' section."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        assert "## 0c. Version Display" in content

    def test_version_step_before_welcome_banner(self) -> None:
        """Step 0c appears before Step 4 (welcome banner) in onboarding-flow.md."""
        content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
        pos_0c = content.index("## 0c. Version Display")
        pos_step4 = content.index("## 4. Bootcamp Introduction")
        assert pos_0c < pos_step4, (
            "Version Display (0c) must appear before Bootcamp Introduction (Step 4)"
        )


# ---------------------------------------------------------------------------
# TestVersionFileSmoke
# ---------------------------------------------------------------------------


class TestVersionFileSmoke:
    """Smoke tests for the VERSION file itself.

    Validates: Requirements 4.4, 1.2
    """

    def test_version_file_exists_at_fixed_path(self) -> None:
        """VERSION file exists at senzing-bootcamp/VERSION."""
        assert _VERSION_FILE.exists(), f"VERSION file not found at {_VERSION_FILE}"

    def test_version_file_contains_valid_content(self) -> None:
        """VERSION file contains a valid semver string."""
        content = _VERSION_FILE.read_text(encoding="utf-8").strip()
        # Should not raise
        validated = validate_version(content)
        assert validated == content
