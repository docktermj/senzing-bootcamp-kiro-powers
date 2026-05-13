"""Property-based tests for version string handling.

Validates correctness properties of the version module: round-trip parsing,
display format, invalid rejection, error messages, and script behavior.

Feature: display-version-on-start
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
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

from version import (  # noqa: E402
    VersionError,
    format_version,
    format_version_display,
    main,
    parse_version,
    read_version,
    validate_version,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SEMVER_REGEX = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


# ---------------------------------------------------------------------------
# Strategies for invalid version strings
# ---------------------------------------------------------------------------


def st_leading_zeros() -> st.SearchStrategy[str]:
    """Generate version-like strings with leading zeros in at least one component."""
    return st.one_of(
        # Leading zero in major (e.g., "01.2.3", "00.5.9")
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"0{t[0]}.{t[1]}.{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
        # Leading zero in minor (e.g., "1.02.3")
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.0{t[1]}.{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
        # Leading zero in patch (e.g., "1.2.03")
        st.tuples(
            st.integers(0, 99),
            st.integers(0, 99),
            st.integers(0, 99),
        ).map(lambda t: f"{t[0]}.{t[1]}.0{t[2]}").filter(
            lambda s: not _SEMVER_REGEX.match(s)
        ),
    )


def st_prerelease() -> st.SearchStrategy[str]:
    """Generate version strings with pre-release identifiers."""
    return st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
        st.from_regex(r"[a-zA-Z][a-zA-Z0-9.]*", fullmatch=True),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}-{t[3]}")


def st_build_metadata() -> st.SearchStrategy[str]:
    """Generate version strings with build metadata."""
    return st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
        st.from_regex(r"[a-zA-Z0-9]+", fullmatch=True),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}+{t[3]}")


def st_extra_dots() -> st.SearchStrategy[str]:
    """Generate strings with extra dot-separated components."""
    return st.tuples(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}")


def st_random_text() -> st.SearchStrategy[str]:
    """Generate random text strings that are not valid semver."""
    return st.text(min_size=1, max_size=50).filter(
        lambda s: not _SEMVER_REGEX.match(s)
    )


def st_invalid_version() -> st.SearchStrategy[str]:
    """Composite strategy producing invalid version strings."""
    return st.one_of(
        st_leading_zeros(),
        st_prerelease(),
        st_build_metadata(),
        st_extra_dots(),
        st_random_text(),
    )


def st_malformed_version_strings() -> st.SearchStrategy[str]:
    """Strategy that generates strings which are NOT valid semver.

    Includes empty strings, whitespace-only, random text, and strings
    with special characters.
    """
    return st.one_of(
        # Empty strings
        st.just(""),
        # Whitespace-only strings
        st.from_regex(r"^\s+$", fullmatch=True),
        # Random text (no digits/dots pattern)
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "P", "S", "Z"),
            ),
            min_size=1,
            max_size=50,
        ),
        # Strings with special characters
        st.text(
            alphabet=st.characters(
                whitelist_categories=("P", "S", "Cc"),
                whitelist_characters="\n\t\r\x00",
            ),
            min_size=1,
            max_size=30,
        ),
        # Random general text that might look version-like but isn't
        st.text(min_size=1, max_size=50),
    )


# ---------------------------------------------------------------------------
# Property 1: Version String Round-Trip
# ---------------------------------------------------------------------------


class TestVersionRoundTrip:
    """Property 1: Version String Round-Trip.

    For any three integers (major, minor, patch) each in the range 0–99,
    formatting them as a version string and then parsing that string back
    into components produces the original integers.

    **Validates: Requirements 3.4**
    """

    @given(
        major=st.integers(0, 99),
        minor=st.integers(0, 99),
        patch=st.integers(0, 99),
    )
    @settings(max_examples=100)
    def test_format_parse_round_trip(
        self, major: int, minor: int, patch: int
    ) -> None:
        """format_version(*parse_version(format_version(m, n, p))) == original."""
        version_str = format_version(major, minor, patch)
        result = format_version(*parse_version(version_str))
        assert result == version_str


# ---------------------------------------------------------------------------
# Property 2: Display Format Correctness
# ---------------------------------------------------------------------------


class TestDisplayFormatCorrectness:
    """Property 2: Display Format Correctness.

    For any valid version string (MAJOR.MINOR.PATCH with components 0–99 and
    no leading zeros), the display format function produces a string equal to
    "Senzing Bootcamp Power v" concatenated with the input version string.

    **Validates: Requirements 2.2**
    """

    @given(
        major=st.integers(0, 99),
        minor=st.integers(0, 99),
        patch=st.integers(0, 99),
    )
    @settings(max_examples=100)
    def test_display_format_equals_prefix_plus_version(
        self, major: int, minor: int, patch: int
    ) -> None:
        """format_version_display(v) == 'Senzing Bootcamp Power v' + v."""
        version_str = format_version(major, minor, patch)
        display = format_version_display(version_str)
        assert display == "Senzing Bootcamp Power v" + version_str


# ---------------------------------------------------------------------------
# Property 3: Invalid Version Rejection
# ---------------------------------------------------------------------------


class TestInvalidVersionRejection:
    """Property 3: Invalid Version Rejection.

    For any string not matching strict MAJOR.MINOR.PATCH format (leading zeros,
    pre-release, build metadata, extra chars), validate_version() raises VersionError.

    **Validates: Requirements 3.1, 3.3**
    """

    @given(invalid_str=st_invalid_version())
    @settings(max_examples=100)
    def test_invalid_version_raises_error(self, invalid_str: str) -> None:
        """validate_version rejects any string not matching strict semver."""
        assume(not _SEMVER_REGEX.match(invalid_str))
        with pytest.raises(VersionError):
            validate_version(invalid_str)


# ---------------------------------------------------------------------------
# Property 4: Error Message Contains Invalid Value
# ---------------------------------------------------------------------------


class TestErrorMessageContent:
    """Property 4: Error Message Contains Invalid Value.

    For any invalid version string rejected by the validator, the VersionError
    message contains the invalid input verbatim as a substring.

    **Validates: Requirements 3.2**
    """

    @given(invalid_str=st_invalid_version())
    @settings(max_examples=100)
    def test_error_message_contains_invalid_value(self, invalid_str: str) -> None:
        """The error message includes the invalid input string verbatim."""
        assume(not _SEMVER_REGEX.match(invalid_str))
        with pytest.raises(VersionError) as exc_info:
            validate_version(invalid_str)
        exc = exc_info.value
        # The invalid value appears verbatim in the error message
        assert invalid_str in str(exc), (
            f"Expected {invalid_str!r} in error message, got: {str(exc)!r}"
        )
        # The invalid_value attribute matches the input
        assert exc.invalid_value == invalid_str, (
            f"Expected exc.invalid_value == {invalid_str!r}, "
            f"got {exc.invalid_value!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: Malformed Content Produces Error Not Default
# ---------------------------------------------------------------------------


class TestMalformedContentProducesError:
    """Property 5: Malformed Content Produces Error Not Default.

    For any string that is not a valid version (empty, whitespace-only,
    random text), validate_version() raises VersionError rather than
    returning a default or empty value.

    **Validates: Requirements 1.4**
    """

    @given(malformed=st_malformed_version_strings())
    @settings(max_examples=100)
    def test_malformed_content_raises_version_error(self, malformed: str) -> None:
        """Malformed strings always raise VersionError, never return a value."""
        assume(not _SEMVER_REGEX.match(malformed))

        try:
            result = validate_version(malformed)
            # If we reach here, the function returned a value instead of raising
            raise AssertionError(
                f"validate_version({malformed!r}) returned {result!r} "
                f"instead of raising VersionError"
            )
        except VersionError:
            pass  # Expected behavior — malformed input raises VersionError


# ---------------------------------------------------------------------------
# Property 6: Script and Display Paths Produce Identical Version
# ---------------------------------------------------------------------------


class TestScriptDisplayPathIdentity:
    """Property 6: Script and Display Paths Produce Identical Version.

    For any valid version string written to a temp VERSION file,
    read_version() and format_version_display() produce a display string
    whose version substring is byte-for-byte identical to the raw
    read_version() result.

    **Validates: Requirements 4.2**
    """

    @given(
        major=st.integers(0, 99),
        minor=st.integers(0, 99),
        patch=st.integers(0, 99),
    )
    @settings(max_examples=100)
    def test_script_display_path_identity(
        self, major: int, minor: int, patch: int
    ) -> None:
        """read_version() result appears byte-for-byte in format_version_display() output."""
        version_str = format_version(major, minor, patch)

        # Write version to a temporary file
        tmp_dir = tempfile.mkdtemp()
        tmp_file = Path(tmp_dir) / "VERSION"
        tmp_file.write_text(version_str, encoding="utf-8")

        # Read via read_version (the "script path")
        raw_version = read_version(tmp_file)

        # Format via format_version_display (the "display path")
        display_string = format_version_display(raw_version)

        # The raw version must appear byte-for-byte in the display string
        assert raw_version in display_string, (
            f"Expected raw version {raw_version!r} to appear in "
            f"display string {display_string!r}"
        )


# ---------------------------------------------------------------------------
# Property 7: Script Exits Non-Zero on Invalid Input
# ---------------------------------------------------------------------------


class TestScriptExitBehavior:
    """Property 7: Script Exits Non-Zero on Invalid Input.

    For any malformed version file content (non-semver strings, empty content,
    binary data), invoking the script's main() function results in SystemExit(1)
    and an error message printed to stderr that includes the file path.

    **Validates: Requirements 4.5**
    """

    @given(invalid_content=st_invalid_version())
    @settings(max_examples=100)
    def test_main_exits_nonzero_on_invalid_input(self, invalid_content: str) -> None:
        """main() raises SystemExit(1) and stderr includes file path for invalid input."""
        assume(not _SEMVER_REGEX.match(invalid_content))

        # Write invalid content to a temporary file
        tmp_dir = tempfile.mkdtemp()
        tmp_file = Path(tmp_dir) / "VERSION"
        tmp_file.write_text(invalid_content, encoding="utf-8")

        # Capture stderr using contextlib.redirect_stderr
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            with pytest.raises(SystemExit) as exc_info:
                main(["--file", str(tmp_file)])

        # Assert exit code is 1
        assert exc_info.value.code == 1, (
            f"Expected exit code 1, got {exc_info.value.code}"
        )

        # Assert stderr contains the file path
        stderr_output = stderr_capture.getvalue()
        assert str(tmp_file) in stderr_output, (
            f"Expected file path {str(tmp_file)!r} in stderr output, "
            f"got: {stderr_output!r}"
        )
