"""Preservation property tests for windows-directory-creation-fix bugfix.

These tests record the current baseline behavior of the UNFIXED steering file
and assert that key content is preserved. When run on unfixed code, they MUST
PASS — confirming the baseline. After the fix, they are re-run to verify no
regressions.

Feature: windows-directory-creation-fix

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
_PROJECT_STRUCTURE = _BOOTCAMP_DIR / "steering" / "project-structure.md"

# ---------------------------------------------------------------------------
# Observed Constants — recorded verbatim from the UNFIXED steering file
# ---------------------------------------------------------------------------

# Observation: The Linux/macOS mkdir -p brace-expansion command text
OBSERVED_MKDIR_COMMAND = (
    "mkdir -p data/{raw,transformed,samples,backups,temp} database licenses "
    "src/{transform,load,query,utils} tests backups docs/feedback config logs "
    "monitoring scripts"
)

# Observation: The Python os.makedirs loop content (verbatim)
OBSERVED_PYTHON_LOOP = '''```python
import os
for d in [
    "data/raw", "data/transformed", "data/samples", "data/backups", "data/temp",
    "database", "licenses", "src/transform", "src/load", "src/query", "src/utils",
    "tests", "backups", "docs/feedback", "config", "logs", "monitoring", "scripts",
]:
    os.makedirs(d, exist_ok=True)
```'''

# Observation: YAML frontmatter inclusion setting
OBSERVED_FRONTMATTER_INCLUSION = "inclusion: auto"

# Observation: All 18 required directory paths present in the file
ALL_REQUIRED_DIRS: list[str] = [
    "data/raw",
    "data/transformed",
    "data/samples",
    "data/backups",
    "data/temp",
    "database",
    "licenses",
    "src/transform",
    "src/load",
    "src/query",
    "src/utils",
    "tests",
    "backups",
    "docs/feedback",
    "config",
    "logs",
    "monitoring",
    "scripts",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_steering_file() -> str:
    """Read the full content of project-structure.md."""
    return _PROJECT_STRUCTURE.read_text(encoding="utf-8")


def _extract_create_structure_section(content: str) -> str:
    """Extract the 'Create Structure' section from the steering file."""
    pattern = re.compile(
        r"^##\s+Create\s+Structure",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # Find the next ## heading or end of file
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(content, start + 1)
    if next_match:
        return content[start:next_match.start()]

    return content[start:]


def _extract_linux_mkdir_command(content: str) -> str:
    """Extract the Linux/macOS mkdir -p command from the steering file.

    The command appears as an inline code block after 'Linux/macOS:'.
    """
    pattern = re.compile(r"Linux/macOS:\s*`([^`]+)`")
    match = pattern.search(content)
    return match.group(1) if match else ""


def _extract_python_loop(content: str) -> str:
    """Extract the Python os.makedirs code block from the Create Structure section.

    Returns the full fenced code block including the ``` markers.
    """
    section = _extract_create_structure_section(content)
    pattern = re.compile(r"```python\n.*?```", re.DOTALL)
    match = pattern.search(section)
    return match.group(0) if match else ""


def _extract_frontmatter(content: str) -> str:
    """Extract the YAML frontmatter from the steering file."""
    pattern = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_directory_subset(draw: st.DrawFn) -> list[str]:
    """Generate a random non-empty subset of the 18 required directory paths."""
    indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=len(ALL_REQUIRED_DIRS) - 1),
            min_size=1,
            max_size=len(ALL_REQUIRED_DIRS),
            unique=True,
        )
    )
    return [ALL_REQUIRED_DIRS[i] for i in sorted(indices)]


@st.composite
def st_non_windows_platform(draw: st.DrawFn) -> str:
    """Generate a non-Windows platform name."""
    return draw(st.sampled_from(["Linux", "macOS", "linux", "darwin", "macos"]))


# ---------------------------------------------------------------------------
# Test 1 — Linux/macOS mkdir -p Command Preservation
# ---------------------------------------------------------------------------


class TestLinuxMkdirPreservation:
    """Test 1 — Linux/macOS mkdir -p Command Preservation.

    **Validates: Requirements 3.1**

    For all non-Windows platforms, assert the mkdir -p command block is
    textually identical between original and fixed content. On unfixed code
    this PASSES — confirming the baseline we want to preserve.
    """

    def test_mkdir_command_matches_observed_baseline(self) -> None:
        """The Linux/macOS mkdir -p command must match the observed baseline."""
        content = _read_steering_file()
        actual_command = _extract_linux_mkdir_command(content)
        assert actual_command == OBSERVED_MKDIR_COMMAND, (
            f"Linux/macOS mkdir -p command does not match observed baseline.\n"
            f"Expected: {OBSERVED_MKDIR_COMMAND!r}\n"
            f"Actual:   {actual_command!r}"
        )

    @given(platform=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mkdir_command_preserved_for_non_windows_platforms(
        self, platform: str
    ) -> None:
        """For all non-Windows platforms, the mkdir -p command is preserved.

        **Validates: Requirements 3.1**

        Regardless of which non-Windows platform name we consider, the
        Linux/macOS mkdir -p brace-expansion command must be textually
        identical to the observed baseline.
        """
        content = _read_steering_file()
        actual_command = _extract_linux_mkdir_command(content)
        assert actual_command == OBSERVED_MKDIR_COMMAND, (
            f"For platform '{platform}': Linux/macOS mkdir -p command changed.\n"
            f"Expected: {OBSERVED_MKDIR_COMMAND!r}\n"
            f"Actual:   {actual_command!r}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Directory Paths Present in Linux/macOS Command
# ---------------------------------------------------------------------------


class TestDirectoryPathsInLinuxCommand:
    """Test 2 — Directory Paths Present in Linux/macOS Command.

    **Validates: Requirements 3.3, 3.4**

    For random subsets of the 18 directory paths, assert all paths appear
    in the Linux/macOS command block. On unfixed code this PASSES.
    """

    @given(dirs=st_directory_subset())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_paths_appear_in_linux_command(self, dirs: list[str]) -> None:
        """For any subset of required directories, all paths must be
        representable in the Linux/macOS mkdir -p command.

        **Validates: Requirements 3.3, 3.4**

        The mkdir -p command uses brace expansion, so individual paths
        like 'data/raw' are represented as part of 'data/{raw,...}'.
        We verify each path is covered by expanding the brace syntax.
        """
        content = _read_steering_file()
        actual_command = _extract_linux_mkdir_command(content)

        # Expand brace expressions to get individual paths
        expanded_paths = _expand_braces(actual_command)

        for d in dirs:
            assert d in expanded_paths, (
                f"Directory '{d}' not found in Linux/macOS mkdir -p command.\n"
                f"Command: {actual_command}\n"
                f"Expanded paths: {sorted(expanded_paths)}"
            )


def _expand_braces(mkdir_command: str) -> set[str]:
    """Expand brace expressions in a mkdir -p command to individual paths.

    E.g., 'mkdir -p data/{raw,temp} config' -> {'data/raw', 'data/temp', 'config'}
    """
    # Remove the 'mkdir -p ' prefix
    args_str = mkdir_command.replace("mkdir -p ", "")
    tokens = args_str.split()

    paths: set[str] = set()
    for token in tokens:
        if "{" in token and "}" in token:
            # Expand brace expression: prefix/{a,b,c} -> prefix/a, prefix/b, prefix/c
            match = re.match(r"^(.*?)\{([^}]+)\}(.*)$", token)
            if match:
                prefix, items_str, suffix = match.groups()
                for item in items_str.split(","):
                    paths.add(f"{prefix}{item}{suffix}")
            else:
                paths.add(token)
        else:
            paths.add(token)

    return paths


# ---------------------------------------------------------------------------
# Test 3 — Python os.makedirs Loop Preservation
# ---------------------------------------------------------------------------


class TestPythonLoopPreservation:
    """Test 3 — Python os.makedirs Loop Preservation.

    **Validates: Requirements 3.2**

    Assert the Python os.makedirs loop content is textually unchanged.
    On unfixed code this PASSES — confirming the baseline.
    """

    def test_python_loop_matches_observed_baseline(self) -> None:
        """The Python os.makedirs loop must match the observed baseline."""
        content = _read_steering_file()
        actual_loop = _extract_python_loop(content)
        assert actual_loop == OBSERVED_PYTHON_LOOP, (
            f"Python os.makedirs loop does not match observed baseline.\n"
            f"Expected:\n{OBSERVED_PYTHON_LOOP}\n\n"
            f"Actual:\n{actual_loop}"
        )

    @given(platform=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_python_loop_unchanged_across_platforms(self, platform: str) -> None:
        """The Python os.makedirs loop is unchanged regardless of platform.

        **Validates: Requirements 3.2**

        The Python loop is cross-platform and must remain textually
        identical in the steering file.
        """
        content = _read_steering_file()
        actual_loop = _extract_python_loop(content)
        assert actual_loop == OBSERVED_PYTHON_LOOP, (
            f"For platform '{platform}': Python os.makedirs loop changed.\n"
            f"Expected:\n{OBSERVED_PYTHON_LOOP}\n\n"
            f"Actual:\n{actual_loop}"
        )


# ---------------------------------------------------------------------------
# Test 4 — YAML Frontmatter Preservation
# ---------------------------------------------------------------------------


class TestFrontmatterPreservation:
    """Test 4 — YAML Frontmatter Preservation.

    **Validates: Requirements 3.4**

    Assert YAML frontmatter 'inclusion: auto' is preserved.
    On unfixed code this PASSES — confirming the baseline.
    """

    def test_frontmatter_contains_inclusion_auto(self) -> None:
        """The YAML frontmatter must contain 'inclusion: auto'."""
        content = _read_steering_file()
        frontmatter = _extract_frontmatter(content)
        assert OBSERVED_FRONTMATTER_INCLUSION in frontmatter, (
            f"YAML frontmatter does not contain '{OBSERVED_FRONTMATTER_INCLUSION}'.\n"
            f"Actual frontmatter: {frontmatter!r}"
        )

    @given(platform=st_non_windows_platform())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_frontmatter_preserved_across_platforms(self, platform: str) -> None:
        """The YAML frontmatter inclusion setting is preserved regardless of platform.

        **Validates: Requirements 3.4**

        The frontmatter controls auto-inclusion behavior and must not
        change as part of any platform-specific fix.
        """
        content = _read_steering_file()
        frontmatter = _extract_frontmatter(content)
        assert OBSERVED_FRONTMATTER_INCLUSION in frontmatter, (
            f"For platform '{platform}': YAML frontmatter changed.\n"
            f"Expected to contain: '{OBSERVED_FRONTMATTER_INCLUSION}'\n"
            f"Actual frontmatter: {frontmatter!r}"
        )
