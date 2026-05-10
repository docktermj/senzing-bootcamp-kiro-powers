"""Hook categories synchronization tests.

Verifies bidirectional sync between hook-categories.yaml and the actual
.kiro.hook files on disk, count validations, and uniqueness checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    CATEGORIES_PATH,
    CRITICAL_HOOKS,
    HOOKS_DIR,
    get_hook_files,
    parse_categories_yaml,
)

# ---------------------------------------------------------------------------
# Module-level data
# ---------------------------------------------------------------------------

_categories = parse_categories_yaml()
_all_category_hook_ids: list[str] = []
for _ids in _categories.values():
    _all_category_hook_ids.extend(_ids)

_hook_file_ids = [p.name.replace(".kiro.hook", "") for p in get_hook_files()]


# ===========================================================================
# TestCategoriesFileToHookFiles — Req 4.1
# ===========================================================================

class TestCategoriesFileToHookFiles:
    """Verify every YAML entry has a corresponding .kiro.hook file."""

    @pytest.mark.parametrize("hook_id", _all_category_hook_ids)
    def test_yaml_entry_has_hook_file(self, hook_id: str):
        """Every hook identifier in categories YAML has a .kiro.hook file (Req 4.1)."""
        hook_path = HOOKS_DIR / f"{hook_id}.kiro.hook"
        assert hook_path.exists(), (
            f'Categories YAML lists "{hook_id}" but no file '
            f'"{hook_id}.kiro.hook" exists in {HOOKS_DIR}'
        )


# ===========================================================================
# TestHookFilesToCategoriesFile — Req 4.2
# ===========================================================================

class TestHookFilesToCategoriesFile:
    """Verify every .kiro.hook file appears in exactly one category."""

    @pytest.mark.parametrize("hook_id", _hook_file_ids)
    def test_hook_file_in_categories(self, hook_id: str):
        """Every .kiro.hook file appears in the categories YAML (Req 4.2)."""
        occurrences = _all_category_hook_ids.count(hook_id)
        assert occurrences == 1, (
            f'Hook file "{hook_id}.kiro.hook" appears {occurrences} time(s) '
            f"in categories YAML (expected exactly 1)"
        )


# ===========================================================================
# TestCategoriesCounts — Req 4.3, 4.4
# ===========================================================================

class TestCategoriesCounts:
    """Verify critical category has 7 entries and total count matches file count."""

    def test_critical_category_has_7_entries(self):
        """The critical category contains exactly 7 entries (Req 4.3)."""
        critical = _categories.get("critical", [])
        assert len(critical) == 7, (
            f"Critical category has {len(critical)} entries, expected 7: {critical}"
        )

    def test_total_category_count_matches_file_count(self):
        """Total hook identifiers across all categories equals hook file count (Req 4.4)."""
        total_in_yaml = len(_all_category_hook_ids)
        total_on_disk = len(_hook_file_ids)
        assert total_in_yaml == total_on_disk, (
            f"Categories YAML has {total_in_yaml} hook identifiers but "
            f"{total_on_disk} .kiro.hook files exist on disk"
        )

    def test_critical_hooks_match_expected(self):
        """Critical category contains the expected 7 hook identifiers."""
        critical = set(_categories.get("critical", []))
        expected = set(CRITICAL_HOOKS)
        assert critical == expected, (
            f"Critical category mismatch.\n"
            f"  Missing: {expected - critical}\n"
            f"  Extra: {critical - expected}"
        )


# ===========================================================================
# TestCategoriesUniqueness — Req 4.5
# ===========================================================================

class TestCategoriesUniqueness:
    """Verify no hook identifier appears in more than one category."""

    def test_no_duplicate_hook_ids_across_categories(self):
        """No hook identifier appears in more than one category (Req 4.5)."""
        seen: dict[str, list[str]] = {}
        for category, hook_ids in _categories.items():
            for hook_id in hook_ids:
                seen.setdefault(hook_id, []).append(category)

        duplicates = {
            hook_id: cats for hook_id, cats in seen.items() if len(cats) > 1
        }
        assert not duplicates, (
            f"Hook identifiers appearing in multiple categories: {duplicates}"
        )

    @pytest.mark.parametrize("hook_id", _all_category_hook_ids)
    def test_individual_hook_in_single_category(self, hook_id: str):
        """Each hook identifier appears in exactly one category."""
        count = _all_category_hook_ids.count(hook_id)
        assert count == 1, (
            f'"{hook_id}" appears {count} times across categories (expected 1)'
        )
