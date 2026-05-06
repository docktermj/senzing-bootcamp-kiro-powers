"""Tests for language-specific troubleshooting sections in steering files.

Validates that each language steering file contains a properly structured
"Common Environment Issues" section with at least 5 troubleshooting entries,
each following the Symptom/Cause/Fix format.

Feature: language-specific-troubleshooting
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"

LANGUAGE_FILES: dict[str, Path] = {
    "python": _STEERING_DIR / "lang-python.md",
    "java": _STEERING_DIR / "lang-java.md",
    "csharp": _STEERING_DIR / "lang-csharp.md",
    "rust": _STEERING_DIR / "lang-rust.md",
    "typescript": _STEERING_DIR / "lang-typescript.md",
}

# Regex to find troubleshooting entries (### headings under ## Common Environment Issues)
RE_TROUBLESHOOTING_HEADING = re.compile(r"^## Common Environment Issues\s*$", re.MULTILINE)
RE_ENTRY_HEADING = re.compile(r"^### .+$", re.MULTILINE)
RE_SYMPTOM_MARKER = re.compile(r"^\*\*Symptom\*\*:", re.MULTILINE)
RE_CAUSE_MARKER = re.compile(r"^\*\*Cause\*\*:", re.MULTILINE)
RE_FIX_MARKER = re.compile(r"^\*\*Fix\*\*:", re.MULTILINE)

SPLIT_THRESHOLD_TOKENS = 5000


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_troubleshooting_section(content: str) -> str | None:
    """Extract the Common Environment Issues section from file content.

    Args:
        content: Full file content.

    Returns:
        The troubleshooting section text, or None if not found.
    """
    match = RE_TROUBLESHOOTING_HEADING.search(content)
    if not match:
        return None
    # Return everything from the heading to end of file
    # (or to the next ## heading if one exists after it)
    start = match.start()
    remaining = content[start + len(match.group()):]
    # Find next ## heading (not ###)
    next_h2 = re.search(r"^## ", remaining, re.MULTILINE)
    if next_h2:
        return content[start:start + len(match.group()) + next_h2.start()]
    return content[start:]


def count_entries(section: str) -> int:
    """Count the number of ### entries in a troubleshooting section.

    Args:
        section: The troubleshooting section text.

    Returns:
        Number of ### headings found.
    """
    return len(RE_ENTRY_HEADING.findall(section))


def calculate_token_count(filepath: Path) -> int:
    """Calculate approximate token count for a file (chars / 4).

    Args:
        filepath: Path to the file.

    Returns:
        Approximate token count.
    """
    content = filepath.read_text(encoding="utf-8")
    return round(len(content) / 4)


# ---------------------------------------------------------------------------
# Unit test classes
# ---------------------------------------------------------------------------


class TestCommonEnvironmentIssuesHeading:
    """Feature: language-specific-troubleshooting — Heading presence.

    Validates that each language steering file contains the
    "## Common Environment Issues" heading.
    """

    @pytest.mark.parametrize("lang,filepath", list(LANGUAGE_FILES.items()))
    def test_heading_present(self, lang: str, filepath: Path) -> None:
        """Each language file contains '## Common Environment Issues' heading.

        Args:
            lang: Language identifier.
            filepath: Path to the language steering file.
        """
        content = filepath.read_text(encoding="utf-8")
        assert RE_TROUBLESHOOTING_HEADING.search(content), (
            f"{filepath.name}: missing '## Common Environment Issues' heading"
        )


class TestTroubleshootingEntryFormat:
    """Feature: language-specific-troubleshooting — Entry format validation.

    Validates that each troubleshooting entry contains the required
    Symptom, Cause, and Fix markers.
    """

    @pytest.mark.parametrize("lang,filepath", list(LANGUAGE_FILES.items()))
    def test_entries_have_symptom_cause_fix(self, lang: str, filepath: Path) -> None:
        """Each troubleshooting entry contains Symptom, Cause, and Fix markers.

        Args:
            lang: Language identifier.
            filepath: Path to the language steering file.
        """
        content = filepath.read_text(encoding="utf-8")
        section = get_troubleshooting_section(content)
        assert section is not None, f"{filepath.name}: no troubleshooting section found"

        # Split section into individual entries by ### headings
        entries = re.split(r"^### ", section, flags=re.MULTILINE)[1:]  # skip pre-heading text
        assert len(entries) > 0, f"{filepath.name}: no entries found"

        for i, entry in enumerate(entries, 1):
            entry_title = entry.split("\n")[0].strip()
            assert RE_SYMPTOM_MARKER.search(entry), (
                f"{filepath.name}: entry {i} '{entry_title}' missing **Symptom** marker"
            )
            assert RE_CAUSE_MARKER.search(entry), (
                f"{filepath.name}: entry {i} '{entry_title}' missing **Cause** marker"
            )
            assert RE_FIX_MARKER.search(entry), (
                f"{filepath.name}: entry {i} '{entry_title}' missing **Fix** marker"
            )


class TestMinimumEntryCount:
    """Feature: language-specific-troubleshooting — Minimum entry count.

    Validates that each language file has at least 5 troubleshooting entries.
    """

    @pytest.mark.parametrize("lang,filepath", list(LANGUAGE_FILES.items()))
    def test_at_least_five_entries(self, lang: str, filepath: Path) -> None:
        """Each language file has at least 5 troubleshooting entries.

        Args:
            lang: Language identifier.
            filepath: Path to the language steering file.
        """
        content = filepath.read_text(encoding="utf-8")
        section = get_troubleshooting_section(content)
        assert section is not None, f"{filepath.name}: no troubleshooting section found"

        entry_count = count_entries(section)
        assert entry_count >= 5, (
            f"{filepath.name}: expected at least 5 entries, found {entry_count}"
        )


# ---------------------------------------------------------------------------
# Property-based test class
# ---------------------------------------------------------------------------


def st_language() -> st.SearchStrategy[str]:
    """Hypothesis strategy that draws from available language identifiers.

    Returns:
        A strategy producing language keys from LANGUAGE_FILES.
    """
    return st.sampled_from(sorted(LANGUAGE_FILES.keys()))


class TestSplitThresholdProperty:
    """Feature: language-specific-troubleshooting — Split threshold property.

    Property: no language file exceeds the 5000-token split threshold
    without a corresponding split file existing on disk.

    Validates: Design requirement that files exceeding the budget are split.
    """

    @given(lang=st_language())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_no_file_exceeds_threshold_without_split(self, lang: str) -> None:
        """No language file exceeds split threshold without a split file existing.

        If a language file exceeds 5000 tokens, a corresponding
        lang-{language}-troubleshooting.md split file must exist.

        Args:
            lang: Language identifier drawn from LANGUAGE_FILES.
        """
        filepath = LANGUAGE_FILES[lang]
        token_count = calculate_token_count(filepath)

        if token_count > SPLIT_THRESHOLD_TOKENS:
            split_file = _STEERING_DIR / f"lang-{lang}-troubleshooting.md"
            assert split_file.exists(), (
                f"{filepath.name} has {token_count} tokens (exceeds "
                f"{SPLIT_THRESHOLD_TOKENS} threshold) but split file "
                f"'{split_file.name}' does not exist"
            )
