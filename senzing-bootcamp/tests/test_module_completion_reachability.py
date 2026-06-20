"""Reachability example test for the module-completion refactor.

# Feature: steering-budget-headroom

Concrete (non-``@given``) example test asserting that the hand-authored
module-completion split preserves every pre-refactor ``##`` section and that
the Module_Completion_Root advertises each slice in its manifest. Validates:

- Requirement 3.3: every section of the pre-refactor ``module-completion.md``
  remains reachable through the Root or a slice.
- Requirement 4.1: the Root contains a manifest naming each slice and its
  purpose.
- Requirement 4.4: artifact generation, non-blocking error handling, and
  track-completion guidance are each their own independently loadable slice
  (each pre-refactor ``##`` heading lands in exactly one location).
- Requirement 4.5: the manifest maps each completion concern to exactly one
  slice file.

The refactored corpus is a single fixed input, so this is an example test
rather than a Hypothesis property. Stdlib-only (``pathlib``, ``re``, ``sys``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Test pattern: scripts aren't packages, so expose senzing-bootcamp/scripts on
# sys.path for parity with peer tests (not strictly needed here, kept for the
# shared convention).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# The test file lives at ``<repo>/senzing-bootcamp/tests/``, so ``parents[2]``
# is the repo root and the steering corpus is two levels down.
_STEERING_DIR = Path(__file__).resolve().parents[2] / "senzing-bootcamp" / "steering"

_ROOT_FILE = "module-completion.md"
_SLICE_FILES = (
    "module-completion-artifacts.md",
    "module-completion-error-handling.md",
    "module-completion-next-steps.md",
    "module-completion-track.md",
)

# Top-level ``##`` section headings present in the pre-refactor
# ``module-completion.md``. Two stay in the Root; the rest moved to slices.
_PRE_REFACTOR_SECTIONS = (
    "Completion Step Ordering",
    "Shared Boundary-Detection Trigger",
    "Backfill for Already-Completed Modules",
    "Non-Blocking Error Handling",
    "Recap Append",
    "Bootcamp Journal",
    "Module Completion Certificate",
    "Next-Step Options",
    "Path Completion Detection",
    "Path Completion Celebration",
)


def _read(filename: str) -> str:
    """Return the text of a steering file under the corpus directory."""
    return (_STEERING_DIR / filename).read_text(encoding="utf-8")


def _count_h2(content: str, heading: str) -> int:
    """Count exact ``## {heading}`` lines in *content* (level-2 headings only)."""
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    return len(pattern.findall(content))


class TestModuleCompletionReachability:
    """Every pre-refactor section is reachable in exactly one location, and the
    Root manifest names each slice with its concern."""

    def test_refactored_files_exist(self) -> None:
        """Root and all four slices are present in the corpus (Requirement 3.3)."""
        assert (_STEERING_DIR / _ROOT_FILE).is_file(), f"missing Root {_ROOT_FILE}"
        for slice_name in _SLICE_FILES:
            assert (_STEERING_DIR / slice_name).is_file(), f"missing slice {slice_name}"

    def test_each_section_appears_in_exactly_one_location(self) -> None:
        """Each pre-refactor ``##`` heading lives in the Root OR exactly one slice
        — never zero, never more than one (Requirements 3.3, 4.4)."""
        files = (_ROOT_FILE, *_SLICE_FILES)
        contents = {name: _read(name) for name in files}

        for heading in _PRE_REFACTOR_SECTIONS:
            locations = {
                name: _count_h2(content, heading)
                for name, content in contents.items()
            }
            total = sum(locations.values())
            holders = [name for name, count in locations.items() if count > 0]
            assert total == 1, (
                f"section '## {heading}' must appear exactly once across "
                f"Root + slices, found {total} occurrence(s) in {locations}"
            )
            assert len(holders) == 1, (
                f"section '## {heading}' must be held by exactly one file, "
                f"found in {holders}"
            )

    def test_root_keeps_ordering_and_trigger_sections(self) -> None:
        """The Root retains the two router sections (Requirement 4.1 context)."""
        root = _read(_ROOT_FILE)
        assert _count_h2(root, "Completion Step Ordering") == 1
        assert _count_h2(root, "Shared Boundary-Detection Trigger") == 1

    def test_root_manifest_names_each_slice_with_a_concern(self) -> None:
        """The Root's '## Completion Slice Manifest' names each slice filename and
        gives a concern description for it (Requirements 4.1, 4.5)."""
        root = _read(_ROOT_FILE)

        # Isolate the manifest section: from its heading to the next ``## ``.
        manifest_match = re.search(
            r"^## Completion Slice Manifest\s*$(?P<body>.*?)(?=^## |\Z)",
            root,
            re.MULTILINE | re.DOTALL,
        )
        assert manifest_match is not None, "Root is missing '## Completion Slice Manifest'"
        manifest = manifest_match.group("body")

        for slice_name in _SLICE_FILES:
            assert slice_name in manifest, (
                f"manifest does not name slice '{slice_name}'"
            )
            # The line that names the slice must also carry a concern description
            # (text beyond the bare filename on that line).
            slice_line = next(
                (line for line in manifest.splitlines() if slice_name in line),
                None,
            )
            assert slice_line is not None
            remainder = slice_line.replace(slice_name, "")
            concern = re.sub(r"[|`]", "", remainder).strip()
            assert concern, (
                f"manifest entry for '{slice_name}' lacks a concern description"
            )
