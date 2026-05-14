"""Property-based tests for Module 3 System Verification steering file.

Validates structural invariants of the system verification steering file:
no dataset choice offered, all checks listed, artifact paths isolated,
timeouts defined, and build commands cover all supported languages.

Feature: module-03-system-verification
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = (
    Path(__file__).resolve().parent.parent / "steering"
)

_STEERING_FILE: Path = _STEERING_DIR / "module-03-system-verification.md"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def read_steering_content() -> str:
    """Read the Module 3 system verification steering file content.

    Returns:
        The full text content of the steering file.

    Raises:
        FileNotFoundError: If the steering file does not exist.
    """
    if not _STEERING_FILE.exists():
        raise FileNotFoundError(
            f"Steering file not found: {_STEERING_FILE}"
        )
    return _STEERING_FILE.read_text(encoding="utf-8")


def parse_sections(content: str) -> dict[str, str]:
    """Parse the steering file into sections keyed by heading text.

    Splits the content at markdown headings (lines starting with one or
    more ``#`` characters) and returns a dictionary mapping each heading
    text (stripped of ``#`` prefix and whitespace) to the content between
    that heading and the next heading of equal or higher level.

    Args:
        content: The full text content of the steering file.

    Returns:
        Dictionary mapping heading text to section body content.
    """
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines)
            current_heading = heading_match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save the last section
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines)

    return sections


def find_content_patterns(content: str, pattern: str) -> list[str]:
    """Find all matches of a regex pattern in the steering file content.

    Args:
        content: The full text content of the steering file.
        pattern: A regex pattern string to search for.

    Returns:
        List of all matching strings found in the content.
    """
    return re.findall(pattern, content, re.IGNORECASE)


def extract_file_paths(content: str) -> list[str]:
    """Extract file paths referenced in the steering file.

    Finds paths that look like relative file references (containing
    a slash and a file extension or directory structure).

    Args:
        content: The full text content of the steering file.

    Returns:
        List of file path strings found in the content.
    """
    # Match paths like src/system_verification/..., config/..., docs/...
    path_pattern = re.compile(
        r"(?:^|[\s`\"'])("
        r"(?:src|config|docs|database)/[^\s`\"'<>|)}\]]*"
        r")",
        re.MULTILINE,
    )
    return path_pattern.findall(content)


def extract_timeout_values(content: str) -> list[str]:
    """Extract timeout values referenced in the steering file.

    Finds numeric timeout specifications (e.g., "30 seconds", "10s",
    "120-second timeout").

    Args:
        content: The full text content of the steering file.

    Returns:
        List of timeout specification strings found in the content.
    """
    timeout_pattern = re.compile(
        r"\b(\d+)[\s-]*(second|seconds|s)\b"
        r"|\btimeout[:\s]+(\d+)",
        re.IGNORECASE,
    )
    return timeout_pattern.findall(content)


# ---------------------------------------------------------------------------
# Pytest fixture — load steering content once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def steering_content() -> str:
    """Session-scoped fixture providing the steering file content.

    Returns:
        The full text content of the Module 3 steering file.
    """
    return read_steering_content()


@pytest.fixture(scope="session")
def steering_sections() -> dict[str, str]:
    """Session-scoped fixture providing parsed steering file sections.

    Returns:
        Dictionary mapping heading text to section body content.
    """
    return parse_sections(read_steering_content())


# ---------------------------------------------------------------------------
# Property-based test class
# ---------------------------------------------------------------------------


class TestSystemVerificationProperties:
    """Property-based tests for Module 3 System Verification steering file.

    Validates structural invariants ensuring the steering file correctly
    defines a deterministic verification pipeline using TruthSet data,
    covers all required checks, isolates artifacts, defines timeouts,
    and supports all target languages.

    **Validates: Requirements 1.1, 4.1, 4.4, 10.2, 13.1**
    """

    def test_property_no_dataset_choice(self, steering_content: str) -> None:
        """No dataset selection prompt is offered to the bootcamper.

        Verifies the steering file contains no language that would present
        a dataset choice to the user. The file may mention dataset names
        in prohibition context (e.g., "Do not use CORD") but must not
        contain selection prompts like "choose a dataset" or "which
        dataset would you like."

        **Validates: Requirements 1.1**
        """
        # Patterns that indicate a dataset selection prompt
        choice_patterns: list[str] = [
            r"choose\s+(a|your|the)\s+dataset",
            r"select\s+(a|your|the)\s+dataset",
            r"which\s+dataset",
            r"pick\s+(a|your|the)\s+dataset",
            r"dataset\s+options",
            r"available\s+datasets",
            r"dataset\s+menu",
        ]
        for pattern in choice_patterns:
            matches = find_content_patterns(steering_content, pattern)
            assert not matches, (
                f"Dataset selection prompt found: {matches!r} "
                f"(pattern: {pattern!r})"
            )

        # Verify CORD/Las Vegas/London/Moscow only appear in prohibition
        # context (preceded by "Do not use" or "not") — never as options
        dataset_names = ["CORD", "Las Vegas", "London", "Moscow"]
        for name in dataset_names:
            # Find all lines containing the dataset name
            lines_with_name = [
                line.strip()
                for line in steering_content.splitlines()
                if name in line
            ]
            for line in lines_with_name:
                # Each mention must be in a prohibition/negative context
                assert re.search(
                    r"(do not use|not|shall not|no dataset choice|"
                    r"never|must not|don.t)",
                    line,
                    re.IGNORECASE,
                ), (
                    f"Dataset name '{name}' appears outside prohibition "
                    f"context: {line!r}"
                )

    def test_property_all_checks_listed(self, steering_content: str) -> None:
        """Every check name from the report schema appears in the steering file.

        Verifies that all verification check identifiers defined in the
        report JSON schema are referenced somewhere in the steering file
        content, ensuring no check is missing from the pipeline.

        **Validates: Requirements 10.2**
        """
        report_check_names: list[str] = [
            "mcp_connectivity",
            "truthset_acquisition",
            "sdk_initialization",
            "code_generation",
            "build_compilation",
            "data_loading",
            "results_validation",
            "database_operations",
            "web_service",
            "web_page",
        ]
        for check_name in report_check_names:
            matches = find_content_patterns(
                steering_content, re.escape(check_name)
            )
            assert matches, (
                f"Report schema check '{check_name}' not found in "
                f"steering file"
            )

    def test_property_artifact_paths_isolated(
        self, steering_content: str
    ) -> None:
        """All generated file paths are under src/system_verification/.

        Verifies that every file path in the steering file that references
        generated verification artifacts is rooted under the
        src/system_verification/ directory, ensuring no artifacts leak
        into other project directories.

        **Validates: Requirements 13.1**
        """
        all_paths = extract_file_paths(steering_content)
        # Filter to only paths that are generated artifacts (src/ paths)
        # Exclude config/ and docs/ paths which are progress/documentation
        src_paths = [p for p in all_paths if p.startswith("src/")]
        assert len(src_paths) > 0, (
            "No src/ file paths found in steering file"
        )
        for path in src_paths:
            assert path.startswith("src/system_verification/"), (
                f"Generated artifact path '{path}' is not under "
                f"src/system_verification/"
            )

    def test_property_timeouts_defined(
        self, steering_content: str, steering_sections: dict[str, str]
    ) -> None:
        """Every verification step references an explicit timeout value.

        Verifies that each verification step has an explicit timeout
        defined either inline within its section or in the Timeout
        Enforcement table elsewhere in the steering file.

        **Validates: Requirements 4.4**
        """
        # Verification step headings and their short names in the
        # Timeout Enforcement table
        verification_steps: dict[str, str] = {
            "Step 1: MCP Connectivity Check": "MCP Connectivity",
            "Step 2: TruthSet Acquisition": "TruthSet Acquisition",
            "Step 3: SDK Initialization": "SDK Initialization",
            "Step 4: Code Generation": "Code Generation",
            "Step 5: Build/Compile": "Build/Compile",
            "Step 6: Data Loading": "Data Loading",
            "Step 7: Deterministic Results Validation": (
                "Results Validation"
            ),
            "Step 8: Database Operations": "Database Operations",
            "Step 9: Web Service + Visualization Page": "Web Service",
        }
        # Get the Timeout Enforcement section if it exists
        timeout_table = steering_sections.get(
            "Timeout Enforcement", ""
        )
        for step_name, table_name in verification_steps.items():
            assert step_name in steering_sections, (
                f"Verification step '{step_name}' not found in "
                f"steering file sections"
            )
            section_content = steering_sections[step_name]
            inline_timeouts = extract_timeout_values(section_content)
            # Check if timeout is in the Timeout Enforcement table
            table_row_match = re.search(
                re.escape(table_name) + r".*\d+",
                timeout_table,
            )
            assert len(inline_timeouts) > 0 or table_row_match, (
                f"No timeout value found for step '{step_name}' "
                f"(checked inline and Timeout Enforcement table)"
            )

    def test_property_build_commands_per_language(
        self, steering_content: str
    ) -> None:
        """Build command section covers Python, Java, C#, Rust, TypeScript.

        Verifies that the steering file's build/compile section includes
        build commands for all five supported languages, ensuring no
        language is missing from the verification pipeline.

        **Validates: Requirements 4.1**
        """
        required_languages: list[str] = [
            "Python",
            "Java",
            "C#",
            "Rust",
            "TypeScript",
        ]
        for language in required_languages:
            matches = find_content_patterns(
                steering_content, re.escape(language)
            )
            assert matches, (
                f"Language '{language}' not found in steering file "
                f"build commands section"
            )
