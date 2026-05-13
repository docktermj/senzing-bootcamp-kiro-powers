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
    """Verify every .kiro.hook file appears in the categories YAML."""

    @pytest.mark.parametrize("hook_id", _hook_file_ids)
    def test_hook_file_in_categories(self, hook_id: str):
        """Every .kiro.hook file appears in the categories YAML (Req 4.2).

        A hook may appear in multiple module sub-categories (e.g.,
        `enforce-visualization-offers` applies to Modules 3, 5, 7, 8), but
        must appear at least once somewhere in the YAML.
        """
        occurrences = _all_category_hook_ids.count(hook_id)
        assert occurrences >= 1, (
            f'Hook file "{hook_id}.kiro.hook" does not appear in the '
            f"categories YAML (expected at least once)"
        )


# ===========================================================================
# TestCategoriesCounts — Req 4.3, 4.4
# ===========================================================================

class TestCategoriesCounts:
    """Verify critical category has 7 entries and total count matches file count."""

    def test_critical_category_has_expected_entries(self):
        """The critical category contains exactly len(CRITICAL_HOOKS) entries (Req 4.3)."""
        critical = _categories.get("critical", [])
        expected_count = len(CRITICAL_HOOKS)
        assert len(critical) == expected_count, (
            f"Critical category has {len(critical)} entries, "
            f"expected {expected_count}: {critical}"
        )

    def test_total_category_count_matches_file_count(self):
        """Unique hook identifiers across all categories equal hook file count (Req 4.4)."""
        total_unique_in_yaml = len(set(_all_category_hook_ids))
        total_on_disk = len(_hook_file_ids)
        assert total_unique_in_yaml == total_on_disk, (
            f"Categories YAML has {total_unique_in_yaml} unique hook identifiers "
            f"but {total_on_disk} .kiro.hook files exist on disk"
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
    """Verify hooks do not appear in multiple top-level categories.

    A single hook may be associated with multiple modules (e.g.,
    `enforce-visualization-offers` applies to Modules 3, 5, 7, and 8) but
    must not span the critical/modules/any top-level boundary.
    """

    def _top_level_categories_for_hook(self) -> dict[str, set[str]]:
        """Return a mapping of hook_id → set of top-level categories.

        Top-level categories: 'critical', 'modules', 'any'. All module
        sub-categories (module-1, module-2, ...) roll up to 'modules';
        'module-any' rolls up to 'any'.
        """
        seen: dict[str, set[str]] = {}
        for category, hook_ids in _categories.items():
            if category == "critical":
                top_level = "critical"
            elif category == "module-any":
                top_level = "any"
            elif category.startswith("module-"):
                top_level = "modules"
            else:
                top_level = category
            for hook_id in hook_ids:
                seen.setdefault(hook_id, set()).add(top_level)
        return seen

    def test_no_duplicate_hook_ids_across_categories(self):
        """No hook identifier appears in more than one top-level category (Req 4.5)."""
        seen = self._top_level_categories_for_hook()

        duplicates = {
            hook_id: sorted(cats) for hook_id, cats in seen.items()
            if len(cats) > 1
        }
        assert not duplicates, (
            f"Hook identifiers appearing in multiple top-level categories: "
            f"{duplicates}"
        )

    @pytest.mark.parametrize("hook_id", sorted(set(_all_category_hook_ids)))
    def test_individual_hook_in_single_top_level_category(self, hook_id: str):
        """Each hook identifier appears in exactly one top-level category."""
        seen = self._top_level_categories_for_hook()
        top_level_count = len(seen.get(hook_id, set()))
        assert top_level_count == 1, (
            f'"{hook_id}" appears in {top_level_count} top-level categories '
            f"(expected 1): {sorted(seen.get(hook_id, set()))}"
        )
