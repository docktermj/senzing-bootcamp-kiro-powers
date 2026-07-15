"""Keyword-routing preservation test for the steering-inclusion re-classification.

Feature: steering-inclusion-auto-audit

Re-classifying the eleven former ``inclusion: auto`` steering files (Task 4)
rewrote only their frontmatter; it deliberately did not touch
``steering-index.yaml``. This test locks that in for the routing map: every
Auto_File that participated in keyword routing before the change still appears —
with the same keyword(s) pointing at the same file — in the index's
``keywords:`` block afterward, so the agent keeps pulling those files in on the
same triggers.

This is an example/corpus test, not a property test: it parses the real
``senzing-bootcamp/steering/steering-index.yaml`` with the project's own
``lint_steering.parse_steering_index`` helper (the same stdlib parser the linter
uses) and compares the Auto_File-targeting routing entries against the recorded
pre-reclassification snapshot.

Validates: Requirements 3.4
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Scripts are not packages, so their directory is placed on ``sys.path`` per the
# project convention before importing the index parser under test.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import parse_steering_index  # noqa: E402

# ---------------------------------------------------------------------------
# Corpus discovery
# ---------------------------------------------------------------------------

# The shipped steering corpus and its index live two directory levels up from
# this test file (``senzing-bootcamp/tests`` -> ``senzing-bootcamp/steering``).
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

# The eleven files that declared ``inclusion: auto`` before Task 4 re-classified
# them to standard modes (per the requirements introduction and the Task 4 file
# list).
AUTO_FILES: frozenset[str] = frozenset(
    {
        "agent-behavior-rules.md",
        "agent-context-management.md",
        "conversation-protocol.md",
        "design-patterns.md",
        "file-placement.md",
        "mcp-response-caching.md",
        "module-prerequisites.md",
        "project-structure.md",
        "qa-transcript.md",
        "session-resume.md",
        "verbosity-control.md",
    }
)

# Snapshot of every ``keywords:`` entry whose routing target is one of the eleven
# Auto_Files, captured from ``steering-index.yaml`` prior to re-classification.
# Task 4 did not modify the index, so each of these entries must remain present
# and unchanged after the change (Requirement 3.4). Maps keyword -> filename.
EXPECTED_AUTO_FILE_ROUTING: dict[str, str] = {
    "resume": "session-resume.md",
    "prerequisite": "module-prerequisites.md",
    "pattern": "design-patterns.md",
    "project-structure": "project-structure.md",
    "output level": "verbosity-control.md",
    "verbose": "verbosity-control.md",
    "verbosity": "verbosity-control.md",
    "verbosity reference": "verbosity-control.md",
    "verbosity levels": "verbosity-control.md",
    "content rules": "verbosity-control.md",
    "context budget": "agent-context-management.md",
    "pacing": "agent-context-management.md",
    "unload": "agent-context-management.md",
    "cache": "mcp-response-caching.md",
    "mcp cache": "mcp-response-caching.md",
}

# The distinct Auto_Files reachable through the keyword routing map (seven of the
# eleven). The remaining four Auto_Files (agent-behavior-rules.md,
# conversation-protocol.md, file-placement.md, qa-transcript.md) are not
# keyword-routed and therefore carry no keyword entry to preserve.
KEYWORD_ROUTED_AUTO_FILES: frozenset[str] = frozenset(
    EXPECTED_AUTO_FILE_ROUTING.values()
)


def _load_index_keywords() -> dict[str, str]:
    """Return the ``keywords:`` routing map from the real steering index.

    Returns:
        Mapping of keyword to the steering filename it routes to, parsed from
        ``senzing-bootcamp/steering/steering-index.yaml`` with the project's
        ``lint_steering.parse_steering_index`` helper.
    """
    return parse_steering_index(_INDEX_PATH).get("keywords", {})


# Parsed once at import time so each routing entry / file can be a distinct
# parametrized case whose failure names the offending keyword or file directly.
_INDEX_KEYWORDS = _load_index_keywords()


class TestKeywordRoutingPreservation:
    """Re-classified Auto_Files keep their keyword routing entries unchanged.

    Validates: Requirements 3.4
    """

    def test_index_has_keyword_routes(self) -> None:
        """The index parses to a non-empty ``keywords:`` map.

        Guards against the parametrized preservation cases passing vacuously if
        the index is missing, misresolved, or parses to an empty routing map.
        """
        assert _INDEX_KEYWORDS, (
            f"no keyword routes parsed from {_INDEX_PATH}"
        )

    def test_expected_snapshot_is_self_consistent(self) -> None:
        """The recorded snapshot targets only Auto_Files and covers the routed set.

        A guard on the test's own fixture: every target in the snapshot is one
        of the eleven Auto_Files, and the distinct targets equal the seven
        keyword-routed Auto_Files the snapshot claims to cover.
        """
        snapshot_targets = set(EXPECTED_AUTO_FILE_ROUTING.values())
        non_auto = snapshot_targets - AUTO_FILES
        assert not non_auto, f"snapshot targets are not Auto_Files: {sorted(non_auto)}"
        assert snapshot_targets == set(KEYWORD_ROUTED_AUTO_FILES)

    @pytest.mark.parametrize(
        ("keyword", "expected_file"),
        sorted(EXPECTED_AUTO_FILE_ROUTING.items()),
        ids=[kw for kw, _ in sorted(EXPECTED_AUTO_FILE_ROUTING.items())],
    )
    def test_keyword_routes_to_expected_auto_file(
        self, keyword: str, expected_file: str
    ) -> None:
        """Each pre-reclassification keyword still routes to its Auto_File (Req 3.4).

        Args:
            keyword: A routing keyword that pointed at an Auto_File before the
                re-classification.
            expected_file: The Auto_File the keyword must still route to.
        """
        actual = _INDEX_KEYWORDS.get(keyword)
        assert actual == expected_file, (
            f"keyword {keyword!r} should route to {expected_file!r}, "
            f"got {actual!r} — routing entry changed or removed"
        )

    @pytest.mark.parametrize(
        "auto_file",
        sorted(KEYWORD_ROUTED_AUTO_FILES),
        ids=sorted(KEYWORD_ROUTED_AUTO_FILES),
    )
    def test_auto_file_still_a_routing_target(self, auto_file: str) -> None:
        """Each keyword-routed Auto_File still appears as a routing target (Req 3.4).

        Args:
            auto_file: An Auto_File that participated in keyword routing before
                the re-classification.
        """
        targets = set(_INDEX_KEYWORDS.values())
        assert auto_file in targets, (
            f"{auto_file} no longer appears as a keyword routing target"
        )

    def test_auto_file_routing_subset_unchanged(self) -> None:
        """The Auto_File-targeting routing subset matches the snapshot exactly.

        The strongest "unchanged" assertion: filtering the parsed ``keywords:``
        map to only the entries pointing at one of the eleven Auto_Files must
        reproduce the recorded pre-reclassification snapshot with no entry
        removed, retargeted, or added (Requirement 3.4).
        """
        actual_auto_routing = {
            keyword: target
            for keyword, target in _INDEX_KEYWORDS.items()
            if target in AUTO_FILES
        }
        assert actual_auto_routing == EXPECTED_AUTO_FILE_ROUTING
