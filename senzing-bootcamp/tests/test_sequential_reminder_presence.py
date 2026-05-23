"""Property-based tests for Sequential Execution Reminder presence in module steering files.

Validates that all 11 primary module steering files contain the Sequential
Execution Reminder block with required key phrases referencing absolute
precedence and sequential execution.

Feature: never-skip-workflow-steps
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = (
    Path(__file__).resolve().parent.parent / "steering"
)

# The 11 primary module steering files
MODULE_STEERING_FILES: list[str] = [
    "module-01-business-problem.md",
    "module-02-sdk-setup.md",
    "module-03-system-verification.md",
    "module-04-data-collection.md",
    "module-05-data-quality-mapping.md",
    "module-06-data-processing.md",
    "module-07-query-visualize-discover.md",
    "module-08-performance.md",
    "module-09-security.md",
    "module-10-monitoring.md",
    "module-11-deployment.md",
]

# The expected reminder block text (as a blockquote)
EXPECTED_REMINDER = (
    '> ⚠️ **Sequential Execution Rule (absolute precedence):** '
    'Execute every numbered step in this module one at a time, in order. '
    'Never skip, combine, or abbreviate any step containing a 👉 question. '
    'This rule has the same precedence as ⛔ mandatory gates — '
    'no internal reasoning can override it.'
)

# Key phrases that must appear in the reminder block
KEY_PHRASES: list[str] = [
    "absolute precedence",
    "in order",
    "Never skip",
]


# ---------------------------------------------------------------------------
# Hypothesis strategy
# ---------------------------------------------------------------------------


def st_module_file() -> st.SearchStrategy[str]:
    """Strategy that draws from the 11 primary module steering file names."""
    return st.sampled_from(MODULE_STEERING_FILES)


# ---------------------------------------------------------------------------
# Property-based test classes
# ---------------------------------------------------------------------------


class TestProperty4ReminderPresence:
    """Property 4: Sequential Execution Reminder is present in all module steering files.

    For any module steering file in the set of 11 primary module files,
    the file SHALL contain the Sequential Execution Reminder block with
    key phrases referencing absolute precedence and sequential execution.

    **Validates: Requirements 6.1, 6.2, 6.3**
    """

    @given(module_file=st_module_file())
    @settings(max_examples=20)
    def test_reminder_block_present(self, module_file: str) -> None:
        """Every primary module steering file contains the reminder block.

        Args:
            module_file: Filename drawn from the 11 module steering files.
        """
        file_path = _STEERING_DIR / module_file
        assert file_path.exists(), (
            f"Module steering file does not exist: {file_path}"
        )

        content = file_path.read_text(encoding="utf-8")
        assert EXPECTED_REMINDER in content, (
            f"{module_file}: missing Sequential Execution Reminder block"
        )

    @given(module_file=st_module_file())
    @settings(max_examples=20)
    def test_reminder_contains_key_phrases(self, module_file: str) -> None:
        """The reminder block contains all required key phrases.

        Checks that the file content includes the phrases:
        "absolute precedence", "in order" (sequential), and "Never skip".

        Args:
            module_file: Filename drawn from the 11 module steering files.
        """
        file_path = _STEERING_DIR / module_file
        assert file_path.exists(), (
            f"Module steering file does not exist: {file_path}"
        )

        content = file_path.read_text(encoding="utf-8")

        missing_phrases: list[str] = [
            phrase for phrase in KEY_PHRASES
            if phrase not in content
        ]

        assert missing_phrases == [], (
            f"{module_file}: missing key phrases in reminder: "
            f"{missing_phrases}"
        )
