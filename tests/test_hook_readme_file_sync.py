"""Tests that hooks/README.md stays in sync with actual .kiro.hook files.

Prevents documentation drift where the README documents hooks that don't
exist as files, or hook files exist without README documentation.

Validates:
- Every hook filename referenced in the README has a corresponding .kiro.hook file
- Every .kiro.hook file in the hooks directory is documented in the README
- The total hook count stated in the README matches the actual file count
- The POWER.md hook list matches the actual file set
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import HOOKS_DIR, get_hook_files

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

README_PATH: Path = HOOKS_DIR / "README.md"
POWER_MD_PATH: Path = Path("senzing-bootcamp/POWER.md")

# Pattern matching hook filenames in README headings like:
#   ### 5. Write Policy Gate (`write-policy-gate.kiro.hook`) ⭐
HOOK_HEADING_PATTERN: re.Pattern[str] = re.compile(
    r"###\s+\d+\.\s+.+\(`([a-z0-9-]+\.kiro\.hook)`\)"
)

# Pattern matching the total count claim like:
#   "There are 27 hooks total."
HOOK_COUNT_PATTERN: re.Pattern[str] = re.compile(
    r"There are (\d+) hooks total"
)

# Pattern matching hook IDs in POWER.md's "Available (N hooks):" line like:
#   Available (27 hooks): `ask-bootcamper` ⭐, `review-bootcamper-input` ⭐, ...
POWER_AVAILABLE_PATTERN: re.Pattern[str] = re.compile(
    r"Available \((\d+) hooks\):\s*(.+)"
)

# Pattern matching individual hook IDs in the POWER.md available line
POWER_HOOK_ID_PATTERN: re.Pattern[str] = re.compile(r"`([a-z0-9-]+)`")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_actual_hook_ids() -> set[str]:
    """Return the set of hook IDs from actual .kiro.hook files on disk."""
    return {p.name.replace(".kiro.hook", "") for p in get_hook_files()}


def _get_readme_hook_filenames() -> list[str]:
    """Parse README.md and return all hook filenames from entry headings."""
    text = README_PATH.read_text(encoding="utf-8")
    return HOOK_HEADING_PATTERN.findall(text)


def _get_readme_hook_ids() -> set[str]:
    """Parse README.md and return hook IDs (filenames without extension)."""
    filenames = _get_readme_hook_filenames()
    return {f.replace(".kiro.hook", "") for f in filenames}


def _get_readme_count() -> int | None:
    """Parse the stated hook count from README.md."""
    text = README_PATH.read_text(encoding="utf-8")
    match = HOOK_COUNT_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return None


def _get_power_md_hook_ids() -> tuple[int | None, set[str]]:
    """Parse POWER.md's 'Available (N hooks):' line.

    Returns:
        Tuple of (stated_count, set_of_hook_ids).
    """
    text = POWER_MD_PATH.read_text(encoding="utf-8")
    match = POWER_AVAILABLE_PATTERN.search(text)
    if not match:
        return None, set()
    count = int(match.group(1))
    ids_line = match.group(2)
    hook_ids = set(POWER_HOOK_ID_PATTERN.findall(ids_line))
    return count, hook_ids


# ===========================================================================
# TestReadmeHookFileSync
# ===========================================================================

class TestReadmeHookFileSync:
    """Verify README hook entries match actual .kiro.hook files."""

    def test_readme_exists(self):
        """README.md must exist in the hooks directory."""
        assert README_PATH.is_file(), f"Missing {README_PATH}"

    def test_no_phantom_hooks_in_readme(self):
        """Every hook documented in README must have a .kiro.hook file."""
        readme_ids = _get_readme_hook_ids()
        actual_ids = _get_actual_hook_ids()
        phantom = readme_ids - actual_ids
        assert not phantom, (
            f"README documents hooks that don't exist as files: {sorted(phantom)}"
        )

    def test_no_undocumented_hook_files(self):
        """Every .kiro.hook file must be documented in the README."""
        readme_ids = _get_readme_hook_ids()
        actual_ids = _get_actual_hook_ids()
        undocumented = actual_ids - readme_ids
        assert not undocumented, (
            f"Hook files exist without README documentation: {sorted(undocumented)}"
        )

    def test_readme_count_matches_actual_files(self):
        """The stated hook count in README must match actual file count."""
        stated = _get_readme_count()
        assert stated is not None, "Could not find hook count in README"
        actual = len(get_hook_files())
        assert stated == actual, (
            f"README claims {stated} hooks but {actual} .kiro.hook files exist"
        )

    def test_readme_ids_match_actual_ids_exactly(self):
        """README hook set must be identical to the file set (bidirectional)."""
        readme_ids = _get_readme_hook_ids()
        actual_ids = _get_actual_hook_ids()
        assert readme_ids == actual_ids, (
            f"Mismatch between README and files.\n"
            f"  In README only: {sorted(readme_ids - actual_ids)}\n"
            f"  On disk only: {sorted(actual_ids - readme_ids)}"
        )


# ===========================================================================
# TestPowerMdHookSync
# ===========================================================================

class TestPowerMdHookSync:
    """Verify POWER.md hook list matches actual .kiro.hook files."""

    def test_power_md_exists(self):
        """POWER.md must exist."""
        assert POWER_MD_PATH.is_file(), f"Missing {POWER_MD_PATH}"

    def test_power_md_count_matches_actual_files(self):
        """The stated count in POWER.md must match actual file count."""
        count, _ = _get_power_md_hook_ids()
        assert count is not None, "Could not find 'Available (N hooks):' in POWER.md"
        actual = len(get_hook_files())
        assert count == actual, (
            f"POWER.md claims {count} hooks but {actual} .kiro.hook files exist"
        )

    def test_power_md_ids_match_actual_ids(self):
        """POWER.md hook ID list must match actual file set."""
        _, power_ids = _get_power_md_hook_ids()
        actual_ids = _get_actual_hook_ids()
        assert power_ids == actual_ids, (
            f"Mismatch between POWER.md and files.\n"
            f"  In POWER.md only: {sorted(power_ids - actual_ids)}\n"
            f"  On disk only: {sorted(actual_ids - power_ids)}"
        )

    def test_power_md_count_matches_listed_ids(self):
        """The stated count in POWER.md must match the number of IDs listed."""
        count, power_ids = _get_power_md_hook_ids()
        assert count is not None, "Could not find 'Available (N hooks):' in POWER.md"
        assert count == len(power_ids), (
            f"POWER.md claims {count} hooks but lists {len(power_ids)} IDs"
        )
