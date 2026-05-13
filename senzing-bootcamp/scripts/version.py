#!/usr/bin/env python3
"""Read and display the Senzing Bootcamp Power version.

Reads the version string from the VERSION file, validates it against
strict Semantic Versioning (MAJOR.MINOR.PATCH), and outputs it in
raw or display format.

Usage:
    python senzing-bootcamp/scripts/version.py
    python senzing-bootcamp/scripts/version.py --format display
    python senzing-bootcamp/scripts/version.py --file path/to/VERSION
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION_FILE_PATH: Path = (
    Path(__file__).resolve().parent.parent / "VERSION"
)

_SEMVER_REGEX = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class VersionError(Exception):
    """Raised when the version cannot be read or is invalid.

    Attributes:
        message: Human-readable error description.
        file_path: Path that was attempted (None if not file-related).
        invalid_value: The invalid string that failed validation (None if not applicable).
    """

    def __init__(
        self,
        message: str,
        file_path: Path | None = None,
        invalid_value: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.invalid_value = invalid_value


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def validate_version(value: str) -> str:
    """Validate that a string is strict MAJOR.MINOR.PATCH semver.

    Args:
        value: The string to validate.

    Returns:
        The validated version string (unchanged).

    Raises:
        VersionError: If the string does not conform to strict semver.
            The error message includes the invalid value verbatim.
    """
    if not _SEMVER_REGEX.match(value):
        raise VersionError(
            f"Invalid version format: '{value}' — expected MAJOR.MINOR.PATCH",
            invalid_value=value,
        )
    return value


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a validated version string into its integer components.

    Args:
        version: A validated MAJOR.MINOR.PATCH string.

    Returns:
        Tuple of (major, minor, patch) integers.
    """
    parts = version.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_version(major: int, minor: int, patch: int) -> str:
    """Format integer components back into a version string.

    Args:
        major: Major version number (non-negative).
        minor: Minor version number (non-negative).
        patch: Patch version number (non-negative).

    Returns:
        String in "MAJOR.MINOR.PATCH" format.
    """
    return f"{major}.{minor}.{patch}"


def format_version_display(version: str) -> str:
    """Format the version string for display to the bootcamper.

    Args:
        version: A validated MAJOR.MINOR.PATCH string.

    Returns:
        Formatted string: "Senzing Bootcamp Power v{version}"
    """
    return f"Senzing Bootcamp Power v{version}"


def read_version(version_file: Path | None = None) -> str:
    """Read and validate the version string from the VERSION file.

    Args:
        version_file: Path to the VERSION file. Defaults to VERSION_FILE_PATH.

    Returns:
        The validated version string (e.g., "0.1.0").

    Raises:
        VersionError: If the file is missing, unreadable, or contains
            an invalid version string.
    """
    path = version_file if version_file is not None else VERSION_FILE_PATH

    try:
        content = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise VersionError(
            f"Version file not found: {path}",
            file_path=path,
        )
    except OSError as exc:
        raise VersionError(
            f"Cannot read version file: {path} — {exc}",
            file_path=path,
        )

    if not content:
        raise VersionError(
            f"Version file is empty: {path}",
            file_path=path,
            invalid_value="",
        )

    try:
        return validate_version(content)
    except VersionError as exc:
        raise VersionError(
            exc.message,
            file_path=path,
            invalid_value=exc.invalid_value,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Parse args, read version, and print to stdout.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Read and display the Senzing Bootcamp Power version."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to VERSION file (default: auto-detect)",
    )
    parser.add_argument(
        "--format",
        choices=["raw", "display"],
        default="raw",
        help="Output format: 'raw' for just the version string, "
             "'display' for the full display format (default: raw)",
    )
    args = parser.parse_args(argv)

    try:
        version = read_version(args.file)
    except VersionError as exc:
        file_path = exc.file_path or args.file or VERSION_FILE_PATH
        print(f"Error: {exc.message} [{file_path}]", file=sys.stderr)
        sys.exit(1)

    if args.format == "display":
        print(format_version_display(version))
    else:
        print(version)

    sys.exit(0)


if __name__ == "__main__":
    main()
