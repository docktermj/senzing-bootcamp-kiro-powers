"""Corpus invariant tests for the steering-inclusion re-classification.

Feature: steering-inclusion-auto-audit

Locks in the result of re-classifying the eleven former ``inclusion: auto``
steering files to standard modes: after the migration the shipped steering
directory contains zero files declaring ``inclusion: auto`` and every file
declares a value in ``{always, fileMatch, manual}``.

These are example/corpus tests, not property tests: they scan the real
``senzing-bootcamp/steering/*.md`` corpus with the project's own frontmatter
parsers — the budget analyzer's ``parse_inclusion`` (``measure_steering.py``)
and the linter's ``parse_frontmatter`` (``lint_steering.py``) — so the invariant
is verified against the exact parsing the rest of the tooling applies.

Validates: Requirements 3.6, 6.5
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Scripts are not packages, so their directory is placed on ``sys.path`` per the
# project convention before importing the frontmatter parsers under test.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import parse_frontmatter  # noqa: E402
from measure_steering import parse_inclusion  # noqa: E402

# ---------------------------------------------------------------------------
# Corpus discovery
# ---------------------------------------------------------------------------

# The shipped steering corpus lives two directory levels up from this test file
# (``senzing-bootcamp/tests`` → ``senzing-bootcamp/steering``).
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"

# The three documented Kiro inclusion modes. After re-classification every
# steering file must declare exactly one of these (Requirements 3.6, 6.5).
STANDARD_MODES = frozenset({"always", "fileMatch", "manual"})


def _discover_steering_files() -> list[Path]:
    """Return the sorted list of steering ``*.md`` files in the corpus.

    Returns:
        Sorted paths to every ``*.md`` file under ``senzing-bootcamp/steering``.
    """
    return sorted(_STEERING_DIR.glob("*.md"))


# Collected once at import time so each file is a distinct parametrized case and
# a failure names the offending file directly.
_STEERING_FILES = _discover_steering_files()
_STEERING_IDS = [path.name for path in _STEERING_FILES]


class TestSteeringCorpusInclusionInvariant:
    """Every shipped steering file declares a standard inclusion mode.

    Validates: Requirements 3.6, 6.5
    """

    def test_corpus_is_non_empty(self) -> None:
        """The steering corpus contains at least one file to scan.

        Guards against the parametrized invariants passing vacuously if the
        corpus directory is empty or misresolved.
        """
        assert _STEERING_FILES, f"no steering files found under {_STEERING_DIR}"

    @pytest.mark.parametrize("steering_file", _STEERING_FILES, ids=_STEERING_IDS)
    def test_parse_inclusion_yields_standard_mode(self, steering_file: Path) -> None:
        """``parse_inclusion`` never returns ``auto`` and stays in the standard set.

        Reads each real steering file with the budget analyzer's
        ``parse_inclusion`` helper (which takes a file ``Path``) and asserts the
        declared inclusion value is exactly one of ``{always, fileMatch,
        manual}`` and never ``auto`` (Requirements 3.6, 6.5).

        Args:
            steering_file: Path to a steering ``*.md`` file in the corpus.
        """
        inclusion = parse_inclusion(steering_file)
        assert inclusion != "auto", (
            f"{steering_file.name} still declares inclusion: auto"
        )
        assert inclusion in STANDARD_MODES, (
            f"{steering_file.name} declares inclusion {inclusion!r}, "
            f"expected one of {sorted(STANDARD_MODES)}"
        )

    @pytest.mark.parametrize("steering_file", _STEERING_FILES, ids=_STEERING_IDS)
    def test_parse_frontmatter_yields_standard_mode(
        self, steering_file: Path
    ) -> None:
        """``parse_frontmatter`` never yields ``auto`` and stays in the standard set.

        Reads each real steering file with the linter's ``parse_frontmatter``
        helper (which takes file *content*) and asserts the frontmatter block is
        present, its ``inclusion`` value is never ``auto``, and it is exactly one
        of ``{always, fileMatch, manual}`` (Requirements 3.6, 6.5).

        Args:
            steering_file: Path to a steering ``*.md`` file in the corpus.
        """
        content = steering_file.read_text(encoding="utf-8")
        frontmatter, _end_line = parse_frontmatter(content)
        assert frontmatter is not None, (
            f"{steering_file.name} has no parseable YAML frontmatter block"
        )
        inclusion = frontmatter.get("inclusion")
        assert inclusion != "auto", (
            f"{steering_file.name} still declares inclusion: auto"
        )
        assert inclusion in STANDARD_MODES, (
            f"{steering_file.name} declares inclusion {inclusion!r}, "
            f"expected one of {sorted(STANDARD_MODES)}"
        )

    def test_no_steering_file_declares_auto(self) -> None:
        """Zero files across the whole corpus declare ``inclusion: auto``.

        A single corpus-wide assertion complementing the per-file cases, so the
        Requirement 3.6 "zero remain" invariant is stated directly rather than
        only inferred from the parametrized cases.
        """
        auto_files = [
            path.name
            for path in _STEERING_FILES
            if parse_inclusion(path) == "auto"
        ]
        assert not auto_files, f"files still declaring inclusion: auto: {auto_files}"
