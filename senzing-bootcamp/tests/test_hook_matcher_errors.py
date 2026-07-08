"""Unit tests for Matcher_Translator error handling and the design glob table.

Example-based tests for ``scripts/hook_matcher.py`` covering:

* ``GlobTranslationError`` on empty/whitespace-only globs and on unbalanced
  character classes, with the raised message naming the offending pattern.
* ``GlobTranslationError`` on an unsupported ``toolTypes`` category, naming the
  offending entry.
* The representative glob-to-regex fragment table from the design document (the
  actual globs drawn from the shipped hooks) producing the expected regex
  fragments.

Feature: kiro-1-0-migration
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from hook_matcher import (  # noqa: E402
    GlobTranslationError,
    glob_to_regex,
    tooltypes_to_matcher,
)

# ---------------------------------------------------------------------------
# TestGlobTranslationErrors
# ---------------------------------------------------------------------------


class TestGlobTranslationErrors:
    """Error paths of ``glob_to_regex`` name the offending pattern.

    Validates: Requirements 3.6
    """

    @pytest.mark.parametrize(
        "bad_glob",
        ["", " ", "   ", "\t", "\n", "  \t \n "],
        ids=["empty", "single-space", "spaces", "tab", "newline", "mixed-ws"],
    )
    def test_empty_or_whitespace_glob_raises_naming_pattern(
        self, bad_glob: str
    ) -> None:
        """Empty/whitespace-only globs raise, naming the offending pattern."""
        with pytest.raises(
            GlobTranslationError, match="empty or whitespace-only"
        ) as exc_info:
            glob_to_regex(bad_glob)
        # The message names the offending pattern via repr().
        assert repr(bad_glob) in str(exc_info.value)

    @pytest.mark.parametrize(
        "bad_glob",
        ["[", "src/log[abc", "config/[a-z", "prefix[!abc", "data/[0-9"],
        ids=["lone-bracket", "suffix-class", "range-class", "negated", "digit-class"],
    )
    def test_unbalanced_char_class_raises_naming_pattern(
        self, bad_glob: str
    ) -> None:
        """Unbalanced character classes raise, naming the offending pattern."""
        with pytest.raises(
            GlobTranslationError, match="unbalanced character class"
        ) as exc_info:
            glob_to_regex(bad_glob)
        assert repr(bad_glob) in str(exc_info.value)

    def test_error_message_names_pattern_via_pytest_match(self) -> None:
        """The ``match=`` regex can locate the offending pattern itself."""
        offender = "src/log[abc"
        with pytest.raises(GlobTranslationError, match=re.escape(repr(offender))):
            glob_to_regex(offender)


# ---------------------------------------------------------------------------
# TestToolTypesErrors
# ---------------------------------------------------------------------------


class TestToolTypesErrors:
    """Unsupported ``toolTypes`` entries raise, naming the offending entry.

    Validates: Requirements 3.6
    """

    @pytest.mark.parametrize("bad_type", ["nonsense", "read", "network", "delete"])
    def test_unsupported_tooltype_raises_naming_entry(self, bad_type: str) -> None:
        """An unsupported toolTypes category names the offending entry."""
        with pytest.raises(
            GlobTranslationError, match="unsupported toolTypes entry"
        ) as exc_info:
            tooltypes_to_matcher([bad_type])
        assert repr(bad_type) in str(exc_info.value)

    def test_empty_tooltypes_list_raises(self) -> None:
        """An empty toolTypes list cannot form a tool-name matcher."""
        with pytest.raises(GlobTranslationError):
            tooltypes_to_matcher([])


# ---------------------------------------------------------------------------
# TestRepresentativeGlobTable
# ---------------------------------------------------------------------------


class TestRepresentativeGlobTable:
    """The design's representative glob-to-regex fragments (real shipped globs).

    Each expected fragment is the exact value from the design.md translation
    table and is produced by ``glob_to_regex``.

    Validates: Requirements 3.1, 3.6
    """

    # (glob, expected regex fragment) — drawn verbatim from design.md.
    REPRESENTATIVE_GLOBS = [
        ("src/**/*.py", r"src/(?:.*/)?[^/]*\.py"),
        ("src/load/*.*", r"src/load/[^/]*\.[^/]*"),
        ("config/*credentials*", r"config/[^/]*credentials[^/]*"),
        (".env*", r"\.env[^/]*"),
        ("data/transformed/*.jsonl", r"data/transformed/[^/]*\.jsonl"),
    ]

    @pytest.mark.parametrize("glob, expected_fragment", REPRESENTATIVE_GLOBS)
    def test_glob_to_regex_produces_expected_fragment(
        self, glob: str, expected_fragment: str
    ) -> None:
        """Each representative glob translates to its design-table fragment."""
        assert glob_to_regex(glob) == expected_fragment

    @pytest.mark.parametrize("glob, expected_fragment", REPRESENTATIVE_GLOBS)
    def test_expected_fragment_compiles(
        self, glob: str, expected_fragment: str
    ) -> None:
        """Every produced fragment is a valid regular expression."""
        # Should not raise; glob_to_regex guarantees a compilable fragment.
        re.compile(glob_to_regex(glob))
