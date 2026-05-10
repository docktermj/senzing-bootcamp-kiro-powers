"""Bug condition exploration tests for windows-directory-creation-fix bugfix.

These tests parse the UNFIXED steering file and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Feature: windows-directory-creation-fix

**Validates: Requirements 1.1, 2.1, 2.2, 2.3**
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
# Constants — the 18 required directory paths
# ---------------------------------------------------------------------------

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

_PLATFORM_GATE_KEYWORDS = re.compile(
    r"(on\s+windows|if\s+windows|when.*windows|platform.*detect|detect.*platform|"
    r"operating\s+system\s+first|choose\s+based\s+on\s+platform)",
    re.IGNORECASE,
)

_WINDOWS_CONDITIONAL_HEADER = re.compile(
    r"^#{1,4}\s+.*(?:on\s+windows|windows\s+\(powershell\))",
    re.IGNORECASE | re.MULTILINE,
)

_LINUX_CONDITIONAL_HEADER = re.compile(
    r"^#{1,4}\s+.*(?:on\s+linux|linux\s*/\s*macos|on\s+linux\s*/\s*macos)",
    re.IGNORECASE | re.MULTILINE,
)

_PROHIBITION_KEYWORDS = re.compile(
    r"(NEVER\s+use\s+.*mkdir.*path.*path|"
    r"do\s+not\s+use\s+.*mkdir.*multiple|"
    r"mkdir.*does\s+not\s+accept\s+multiple\s+positional)",
    re.IGNORECASE,
)

_MULTI_ARG_MKDIR_PATTERN = re.compile(
    r"mkdir\s+\S+\s+\S+",
)


def _read_steering_file() -> str:
    """Read the full content of project-structure.md."""
    return _PROJECT_STRUCTURE.read_text(encoding="utf-8")


def _extract_create_structure_section(content: str) -> str:
    """Extract the 'Create Structure' section from the steering file.

    Returns the text from the 'Create Structure' heading to the next
    top-level heading or end of file.
    """
    pattern = re.compile(
        r"^##\s+Create\s+Structure",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # Find the next ## heading
    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(content, start + 1)
    if next_match:
        return content[start:next_match.start()]

    return content[start:]


# ---------------------------------------------------------------------------
# Test 1 — Missing Platform-Selection Gate
# ---------------------------------------------------------------------------


class TestMissingPlatformGate:
    """Test 1 — Missing Platform-Selection Gate.

    **Validates: Requirements 1.1, 2.1**

    Parse project-structure.md and assert the Create Structure section
    contains an explicit platform-detection instruction (e.g., "Detect
    the operating system first"). On unfixed content this will FAIL
    because no platform gate exists.
    """

    def test_create_structure_has_platform_detection_instruction(self) -> None:
        content = _read_steering_file()
        section = _extract_create_structure_section(content)
        assert section, "Create Structure section not found in project-structure.md"
        assert _PLATFORM_GATE_KEYWORDS.search(section), (
            "The Create Structure section does not contain an explicit "
            "platform-detection instruction. The agent has no directive to "
            "detect the OS before choosing a command. "
            f"Section content:\n{section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Missing Conditional Block Headers
# ---------------------------------------------------------------------------


class TestMissingConditionalHeaders:
    """Test 2 — Missing Conditional Block Headers.

    **Validates: Requirements 2.1, 2.2**

    Parse project-structure.md and assert the Create Structure section
    uses labelled conditional headers (e.g., '### On Windows (PowerShell)'
    and '### On Linux / macOS') to make platform-specific commands
    mutually exclusive. On unfixed content this will FAIL because
    commands are presented as flat alternatives.
    """

    def test_has_windows_conditional_header(self) -> None:
        content = _read_steering_file()
        section = _extract_create_structure_section(content)
        assert section, "Create Structure section not found in project-structure.md"
        assert _WINDOWS_CONDITIONAL_HEADER.search(section), (
            "The Create Structure section does not contain a Windows-specific "
            "conditional header (e.g., '### On Windows (PowerShell)'). "
            "Commands are presented as flat alternatives without mutual "
            f"exclusivity. Section content:\n{section[:500]}"
        )

    def test_has_linux_conditional_header(self) -> None:
        content = _read_steering_file()
        section = _extract_create_structure_section(content)
        assert section, "Create Structure section not found in project-structure.md"
        assert _LINUX_CONDITIONAL_HEADER.search(section), (
            "The Create Structure section does not contain a Linux/macOS-specific "
            "conditional header (e.g., '### On Linux / macOS'). "
            "Commands are presented as flat alternatives without mutual "
            f"exclusivity. Section content:\n{section[:500]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing Prohibition of Multi-Arg Mkdir on Windows
# ---------------------------------------------------------------------------


class TestMissingProhibition:
    """Test 3 — Missing Prohibition of Multi-Arg Mkdir on Windows.

    **Validates: Requirements 2.2, 2.3**

    Parse project-structure.md and assert it contains an explicit
    prohibition against using multi-argument mkdir on Windows (e.g.,
    'NEVER use mkdir path1 path2 path3 on Windows'). On unfixed content
    this will FAIL because no such prohibition exists.
    """

    def test_contains_multi_arg_mkdir_prohibition(self) -> None:
        content = _read_steering_file()
        section = _extract_create_structure_section(content)
        assert section, "Create Structure section not found in project-structure.md"
        assert _PROHIBITION_KEYWORDS.search(section), (
            "The Create Structure section does not contain an explicit "
            "prohibition against multi-argument mkdir on Windows. "
            "Without this guardrail, the agent may default to "
            "'mkdir dir1 dir2 dir3' which fails on PowerShell. "
            f"Section content:\n{section[:500]}"
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition: Windows Multi-Arg Mkdir Ambiguity
# ---------------------------------------------------------------------------


@st.composite
def st_directory_subset(draw: st.DrawFn) -> list[str]:
    """Generate a random non-empty subset of the 18 required directory paths."""
    indices = draw(
        st.lists(
            st.integers(min_value=0, max_value=len(ALL_REQUIRED_DIRS) - 1),
            min_size=2,
            max_size=len(ALL_REQUIRED_DIRS),
            unique=True,
        )
    )
    return [ALL_REQUIRED_DIRS[i] for i in sorted(indices)]


class TestWindowsMultiArgMkdirAmbiguity:
    """PBT Test — Bug Condition: Windows Multi-Arg Mkdir Ambiguity.

    **Validates: Requirements 1.1, 2.1, 2.2, 2.3**

    Use Hypothesis to generate random subsets of the 18 required directory
    paths and assert the steering content contains explicit platform-
    conditional gating that prevents multi-arg mkdir on Windows.

    On unfixed code, this will FAIL because the steering file presents
    commands as flat alternatives without platform-selection logic.
    """

    @given(dirs=st_directory_subset())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_steering_prevents_multi_arg_mkdir_on_windows(
        self, dirs: list[str]
    ) -> None:
        """For any subset of directories, the steering file must contain
        explicit platform gating that prevents multi-arg mkdir on Windows.

        The bug condition is: platform == Windows AND commandSyntax ==
        'mkdir <path1> <path2> ... <pathN>' AND numberOfPaths > 1.

        The steering file must unambiguously direct Windows users to either
        the Python os.makedirs loop or the PowerShell ForEach-Object pipeline.
        """
        content = _read_steering_file()
        section = _extract_create_structure_section(content)

        assert section, "Create Structure section not found"

        # The steering file MUST contain explicit platform-conditional gating
        has_platform_gate = bool(_PLATFORM_GATE_KEYWORDS.search(section))
        has_windows_header = bool(_WINDOWS_CONDITIONAL_HEADER.search(section))
        has_prohibition = bool(_PROHIBITION_KEYWORDS.search(section))

        # For any subset of 2+ directories, the steering file must make it
        # unambiguous that Windows should NOT use multi-arg mkdir
        assert has_platform_gate and (has_windows_header or has_prohibition), (
            f"Bug condition confirmed: For directory subset {dirs} "
            f"(count={len(dirs)}), the steering file does NOT contain "
            f"explicit platform-conditional gating to prevent multi-arg "
            f"mkdir on Windows. "
            f"has_platform_gate={has_platform_gate}, "
            f"has_windows_header={has_windows_header}, "
            f"has_prohibition={has_prohibition}. "
            f"The agent may default to 'mkdir {' '.join(dirs)}' which "
            f"fails on PowerShell."
        )
