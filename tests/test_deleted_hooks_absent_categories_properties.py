"""Property-based tests for deleted hooks absent from categories file.

Property 7: Deleted hooks absent from categories file.

For any deleted hook ID in the set {question-format-gate,
enforce-step-and-transition, mcp-first-invariant} and for any category
in hook-categories.yaml, that hook ID SHALL NOT appear in that category's list.

**Validates: Requirements 4.1, 4.2, 4.3**
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import CATEGORIES_PATH, parse_categories_yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DELETED_HOOK_IDS: list[str] = [
    "question-format-gate",
    "enforce-step-and-transition",
    "mcp-first-invariant",
]


# ---------------------------------------------------------------------------
# Property 7: Deleted hooks absent from categories file
# ---------------------------------------------------------------------------


class TestDeletedHooksAbsentFromCategories:
    """For any deleted hook ID, it SHALL NOT appear in any category.

    **Validates: Requirements 4.1, 4.2, 4.3**

    Property 7: For any deleted hook ID in the set {question-format-gate,
    enforce-step-and-transition, mcp-first-invariant} and for any category
    in hook-categories.yaml, that hook ID SHALL NOT appear in that
    category's list.
    """

    @given(hook_id=st.sampled_from(DELETED_HOOK_IDS))
    @settings(max_examples=20)
    def test_deleted_hook_not_in_any_category(self, hook_id: str):
        """A deleted hook ID SHALL NOT appear in any category list."""
        categories = parse_categories_yaml(CATEGORIES_PATH)
        for category_name, hook_ids in categories.items():
            assert hook_id not in hook_ids, (
                f"Deleted hook '{hook_id}' still appears in category "
                f"'{category_name}' in {CATEGORIES_PATH}"
            )

    @given(hook_id=st.sampled_from(DELETED_HOOK_IDS))
    @settings(max_examples=20)
    def test_deleted_hook_not_in_raw_file_content(self, hook_id: str):
        """A deleted hook ID SHALL NOT appear anywhere in the raw YAML text."""
        content = CATEGORIES_PATH.read_text(encoding="utf-8")
        assert hook_id not in content, (
            f"Deleted hook '{hook_id}' still appears in the raw content "
            f"of {CATEGORIES_PATH}"
        )
