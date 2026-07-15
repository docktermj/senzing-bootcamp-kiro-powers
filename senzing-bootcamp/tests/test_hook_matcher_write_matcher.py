"""Property test for the write tool-type matcher of the Matcher_Translator.

Feature: kiro-1-0-migration

Validates the write-category branch of ``tooltypes_to_matcher`` in
``scripts/hook_matcher.py``: any legacy ``when.toolTypes`` list that contains
``write`` must translate to exactly the fixed Kiro 1.0 write tool-name matcher
``fs_write|str_replace|fs_append`` (the three built-in write gates
``fs_write``, ``str_replace``, and ``fs_append``). ``write`` takes precedence
over every other category, so the produced matcher is independent of the other
entries, their order, and their count.

Validated requirements:

- Requirement 3.3: a ``when.toolTypes`` list containing ``write`` produces the
  tool-name matcher ``fs_write|str_replace|fs_append``.
- Requirement 5.2: the three migrated ``PreToolUse`` write gates carry exactly
  that fixed write matcher.
"""

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from hook_matcher import tooltypes_to_matcher

# The fixed Kiro 1.0 write tool-name matcher (Requirements 3.3, 5.2).
WRITE_MATCHER = "fs_write|str_replace|fs_append"

# Other toolTypes entries the strategy mixes around ``write`` to prove
# precedence. Includes the known ``shell`` category, unknown categories, and
# ``write`` itself (duplicates), since the ``write`` branch short-circuits
# before any unsupported entry would be rejected.
_OTHER_CATEGORY_POOL = ("write", "shell", "read", "search", "execute", "mcp")


@composite
def st_tooltypes_with_write(draw) -> list[str]:
    """Draw a toolTypes list guaranteed to contain ``write``.

    Arbitrary other categories (known, unknown, or ``write`` duplicates) are
    drawn and ``write`` is spliced in at an arbitrary position so the property
    exercises ``write`` appearing anywhere in a mixed list, in any order.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A toolTypes list that always includes at least one ``write`` entry.
    """
    others = draw(
        st.lists(
            st.one_of(
                st.sampled_from(_OTHER_CATEGORY_POOL),
                st.text(
                    alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10
                ),
            ),
            min_size=0,
            max_size=5,
        )
    )
    insert_at = draw(st.integers(min_value=0, max_value=len(others)))
    return others[:insert_at] + ["write"] + others[insert_at:]


class TestWriteToolTypeMatcher:
    """Property 3: write tool-type produces the fixed write matcher.

    Validates: Requirements 3.3, 5.2
    """

    # Feature: kiro-1-0-migration, Property 3: Write tool-type produces the
    # fixed write matcher
    @given(tool_types=st_tooltypes_with_write())
    def test_write_yields_fixed_write_matcher(self, tool_types: list[str]) -> None:
        """Any toolTypes list containing ``write`` yields exactly the write matcher.

        Args:
            tool_types: A toolTypes list guaranteed to contain ``write`` mixed
                with other/unknown categories in an arbitrary position.
        """
        assert "write" in tool_types
        assert tooltypes_to_matcher(tool_types) == WRITE_MATCHER
