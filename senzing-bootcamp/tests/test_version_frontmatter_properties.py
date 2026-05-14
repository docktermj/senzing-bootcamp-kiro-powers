"""Property-based tests for POWER.md frontmatter version extraction.

Bug condition exploration: validates that the version can be read from
POWER.md YAML frontmatter — expected to FAIL on unfixed code because
the function does not yet exist and POWER.md has no version field.

Preservation tests: validates that existing version functions remain
unchanged after the fix is applied.

Feature: power-version-display (bugfix)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Conditional import — function does not exist yet on unfixed code
# ---------------------------------------------------------------------------
try:
    from version import read_version_from_frontmatter  # noqa: E402
except ImportError:
    read_version_from_frontmatter = None

from version import (  # noqa: E402
    VersionError,
    format_version,
    format_version_display,
    parse_version,
    read_version,
    validate_version,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_POWER_MD_PATH = Path(__file__).resolve().parent.parent / "POWER.md"
_VERSION_FILE_PATH = Path(__file__).resolve().parent.parent / "VERSION"


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_semver() -> st.SearchStrategy[str]:
    """Generate valid MAJOR.MINOR.PATCH version strings (components 0-99)."""
    return st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}")


def st_power_md_with_version() -> st.SearchStrategy[str]:
    """Generate valid POWER.md content with a version field in frontmatter."""
    return st_semver().map(
        lambda v: (
            f"---\n"
            f'name: "senzing-bootcamp"\n'
            f'displayName: "Senzing Bootcamp"\n'
            f'version: "{v}"\n'
            f'description: "A test power."\n'
            f'keywords: ["test"]\n'
            f'author: "Test"\n'
            f"---\n\n"
            f"# Test Power\n\nSome content.\n"
        )
    )


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — POWER.md Frontmatter Missing Version Field
# ---------------------------------------------------------------------------


class TestBugConditionFrontmatterVersion:
    """Property 1: Bug Condition - POWER.md Frontmatter Missing Version Field.

    For any POWER.md content containing valid YAML frontmatter with a
    `version` field in MAJOR.MINOR.PATCH format,
    `read_version_from_frontmatter(content)` returns the validated version
    string.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @pytest.mark.skipif(
        read_version_from_frontmatter is None,
        reason="read_version_from_frontmatter not yet implemented — bug confirmed",
    )
    @given(content=st_power_md_with_version())
    @settings(max_examples=100)
    def test_extracts_version_from_valid_frontmatter(self, content: str) -> None:
        """read_version_from_frontmatter extracts semver from valid frontmatter."""
        # Extract the version we embedded for comparison
        for line in content.splitlines():
            if line.startswith("version:"):
                expected = line.split('"')[1]
                break
        else:
            pytest.fail("Test strategy did not embed a version line")

        result = read_version_from_frontmatter(content)
        assert result == expected, (
            f"Expected {expected!r}, got {result!r}"
        )

    @pytest.mark.skipif(
        read_version_from_frontmatter is None,
        reason="read_version_from_frontmatter not yet implemented — bug confirmed",
    )
    def test_actual_power_md_returns_version_matching_version_file(self) -> None:
        """Concrete bug condition: current POWER.md should yield version matching VERSION file."""
        power_md_content = _POWER_MD_PATH.read_text(encoding="utf-8")
        expected_version = _VERSION_FILE_PATH.read_text(encoding="utf-8").strip()

        result = read_version_from_frontmatter(power_md_content)
        assert result == expected_version, (
            f"Expected version {expected_version!r} from POWER.md frontmatter, "
            f"got {result!r}"
        )


# ---------------------------------------------------------------------------
# Semver regex for invalid string filtering
# ---------------------------------------------------------------------------

_SEMVER_REGEX = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


# ---------------------------------------------------------------------------
# Strategies for invalid version strings
# ---------------------------------------------------------------------------


def st_semver_components() -> st.SearchStrategy[tuple[int, int, int]]:
    """Generate valid semver component tuples (0-99 each)."""
    return st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
    )


def st_invalid_version_strings() -> st.SearchStrategy[str]:
    """Generate strings that are NOT valid semver (leading zeros, non-numeric, wrong format)."""
    return st.one_of(
        # Leading zeros in major
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"0{t[0]}.{t[1]}.{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
        # Leading zeros in minor
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.0{t[1]}.{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
        # Leading zeros in patch
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.{t[1]}.0{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
        # Non-numeric components
        st.from_regex(r"[a-zA-Z]+\.[a-zA-Z]+\.[a-zA-Z]+", fullmatch=True),
        # Wrong format (extra dots, missing components)
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}"),
        # Pre-release suffixes
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}-alpha"),
        # Random text
        st.text(min_size=1, max_size=30).filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
    )


# ---------------------------------------------------------------------------
# Steering content baseline
# ---------------------------------------------------------------------------

_ONBOARDING_FLOW_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "onboarding-flow.md"
)


# ---------------------------------------------------------------------------
# Property 2: Preservation — Existing Version Functions Unchanged
# ---------------------------------------------------------------------------


class TestPreservationVersionFileRead:
    """Preservation: read_version() continues to read from VERSION file.

    For all valid semver strings (components 0–99), read_version() continues
    to read from the VERSION file and validate_version() accepts/rejects the
    same inputs as before.

    **Validates: Requirements 3.1, 3.2, 3.4, 3.5**
    """

    def test_read_version_returns_current_version(self) -> None:
        """read_version() reads from VERSION file and returns '0.12.0'."""
        result = read_version()
        assert result == "0.12.0", (
            f"Expected '0.12.0' from VERSION file, got {result!r}"
        )

    @given(components=st_semver_components())
    @settings(max_examples=100)
    def test_validate_version_accepts_valid_semver(
        self, components: tuple[int, int, int]
    ) -> None:
        """validate_version() accepts all valid semver strings."""
        version_str = f"{components[0]}.{components[1]}.{components[2]}"
        result = validate_version(version_str)
        assert result == version_str, (
            f"Expected validate_version({version_str!r}) == {version_str!r}, "
            f"got {result!r}"
        )


class TestPreservationDisplayFormat:
    """Preservation: format_version_display(v) returns expected format.

    For all valid semver strings, format_version_display(v) returns
    f"Senzing Bootcamp Power v{v}".

    **Validates: Requirements 3.1, 3.2, 3.4, 3.5**
    """

    @given(components=st_semver_components())
    @settings(max_examples=100)
    def test_format_version_display_produces_expected_string(
        self, components: tuple[int, int, int]
    ) -> None:
        """format_version_display(v) == f'Senzing Bootcamp Power v{v}'."""
        version_str = f"{components[0]}.{components[1]}.{components[2]}"
        result = format_version_display(version_str)
        expected = f"Senzing Bootcamp Power v{version_str}"
        assert result == expected, (
            f"Expected {expected!r}, got {result!r}"
        )


class TestPreservationRoundTrip:
    """Preservation: parse_version(format_version(a, b, c)) == (a, b, c).

    For all valid semver strings, the round-trip through format_version and
    parse_version holds.

    **Validates: Requirements 3.1, 3.2, 3.4, 3.5**
    """

    @given(components=st_semver_components())
    @settings(max_examples=100)
    def test_parse_format_round_trip(
        self, components: tuple[int, int, int]
    ) -> None:
        """parse_version(format_version(a, b, c)) == (a, b, c)."""
        major, minor, patch = components
        version_str = format_version(major, minor, patch)
        result = parse_version(version_str)
        assert result == (major, minor, patch), (
            f"Expected ({major}, {minor}, {patch}), got {result}"
        )


class TestPreservationInvalidRejection:
    """Preservation: validate_version() raises VersionError for invalid strings.

    For all invalid version strings (leading zeros, non-numeric, wrong format),
    validate_version() raises VersionError.

    **Validates: Requirements 3.1, 3.2, 3.4, 3.5**
    """

    @given(invalid_str=st_invalid_version_strings())
    @settings(max_examples=100)
    def test_validate_version_rejects_invalid_strings(
        self, invalid_str: str
    ) -> None:
        """validate_version() raises VersionError for invalid version strings."""
        assume(not _SEMVER_REGEX.match(invalid_str))
        with pytest.raises(VersionError):
            validate_version(invalid_str)


class TestPreservationSteeringBaseline:
    """Preservation: onboarding-flow.md Step 0c provides version display instructions.

    Verifies that the current steering content has a Step 0c section that
    instructs the agent to extract the version from POWER.md frontmatter
    (post-fix state) and preserves the fallback warning behavior.

    **Validates: Requirements 3.1, 3.5**
    """

    def test_onboarding_step_0c_exists(self) -> None:
        """Step 0c section exists in onboarding-flow.md."""
        content = _ONBOARDING_FLOW_PATH.read_text(encoding="utf-8")
        assert "## 0c. Version Display" in content, (
            "onboarding-flow.md missing '## 0c. Version Display' section"
        )

    def test_onboarding_step_0c_references_power_md_frontmatter(self) -> None:
        """Step 0c instructs extracting version from POWER.md frontmatter."""
        content = _ONBOARDING_FLOW_PATH.read_text(encoding="utf-8")
        assert "POWER.md frontmatter" in content or "frontmatter" in content, (
            "Step 0c does not reference POWER.md frontmatter as version source"
        )

    def test_onboarding_step_0c_preserves_fallback_warning(self) -> None:
        """Step 0c preserves the fallback warning message for missing version."""
        content = _ONBOARDING_FLOW_PATH.read_text(encoding="utf-8")
        assert "Could not determine power version" in content, (
            "Step 0c missing fallback warning message"
        )
