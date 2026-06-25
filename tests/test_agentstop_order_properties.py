"""Property-based tests for the ``agentstop_order`` mapping.

Validates that the ``agentstop_order`` block in ``hook-categories.yaml`` lists
exactly the hooks whose ``when.type`` is ``agentStop`` in the real hooks
directory — no more, no fewer. The mapping is the machine-readable source of
the documented agentStop precedence order (Theme A).

The ``.kiro.hook`` files are parsed as JSON (stdlib ``json``) to read
``when.type``. The ``agentstop_order`` ids are parsed out of
``hook-categories.yaml`` with a minimal stdlib line scanner consistent with the
repository's no-PyYAML constraint (the shared ``parse_categories_yaml`` helper
only handles the ``critical``/``modules`` blocks, so this module adds a focused
scanner for the ``agentstop_order`` list).

**Validates: Requirements 1.5**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Feature: hook-architecture-improvements, Property 1

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: repo root -> senzing-bootcamp/hooks)
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
HOOKS_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "hooks"
CATEGORIES_PATH: Path = HOOKS_DIR / "hook-categories.yaml"

AGENTSTOP_EVENT_TYPE: str = "agentStop"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _load_hook(path: Path) -> dict:
    """Load and parse a single ``.kiro.hook`` JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def hook_id_of(path: Path) -> str:
    """Return the hook id (filename without the ``.kiro.hook`` suffix)."""
    return path.name.replace(".kiro.hook", "")


def get_hook_files() -> list[Path]:
    """Return all ``.kiro.hook`` file paths in the hooks directory, sorted."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.kiro.hook"))


def event_type_of(path: Path) -> str:
    """Return the ``when.type`` for a hook file (empty string if absent)."""
    return _load_hook(path).get("when", {}).get("type", "")


def agentstop_hook_ids() -> set[str]:
    """Return the set of hook ids whose ``when.type`` is ``agentStop``."""
    return {
        hook_id_of(path)
        for path in get_hook_files()
        if event_type_of(path) == AGENTSTOP_EVENT_TYPE
    }


def parse_agentstop_order_ids(path: Path | None = None) -> list[str]:
    """Parse the ordered ``id`` values from the ``agentstop_order`` YAML block.

    Minimal stdlib scanner (no PyYAML): finds the top-level ``agentstop_order:``
    key, then collects each ``- id: <value>`` entry until the next top-level
    key. Quotes around the id value are stripped.

    Args:
        path: Path to the YAML file. Defaults to ``CATEGORIES_PATH``.

    Returns:
        List of hook ids in declared order (may contain duplicates if the YAML
        is malformed — callers compare against a set).
    """
    if path is None:
        path = CATEGORIES_PATH

    ids: list[str] = []
    in_block = False
    id_pattern = re.compile(r"^\s*-\s*id:\s*(.+?)\s*$")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # A top-level key (indent 0, ends with ':') opens or closes the block.
        if indent == 0 and stripped.endswith(":"):
            in_block = stripped[:-1].strip() == "agentstop_order"
            continue

        if in_block:
            match = id_pattern.match(line)
            if match:
                ids.append(match.group(1).strip().strip('"').strip("'"))

    return ids


# ---------------------------------------------------------------------------
# Module-level data (computed once from the real files)
# ---------------------------------------------------------------------------

ALL_HOOK_FILES: list[Path] = get_hook_files()
AGENTSTOP_IDS: set[str] = agentstop_hook_ids()
AGENTSTOP_ORDER_IDS: list[str] = parse_agentstop_order_ids()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_hook_files() -> st.SearchStrategy[Path]:
    """Strategy sampling over every real ``.kiro.hook`` file."""
    return st.sampled_from(ALL_HOOK_FILES)


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestAgentStopOrder:
    """Property 1: ``agentstop_order`` lists exactly the agentStop hooks.

    For any ``*.kiro.hook`` file in the hooks directory, its id appears in the
    ``agentstop_order`` mapping if and only if its ``when.type`` equals
    ``agentStop``; consequently the set of ``agentstop_order`` ids equals the
    set of agentStop hook ids (no more, no fewer).

    **Validates: Requirements 1.5**
    """

    def test_order_ids_parse_without_duplicates(self) -> None:
        """The parsed ``agentstop_order`` ids contain no duplicates.

        Set equality could otherwise mask a duplicated id paired with a missing
        one, so guard against malformed YAML up front.
        """
        assert len(AGENTSTOP_ORDER_IDS) == len(set(AGENTSTOP_ORDER_IDS)), (
            f"agentstop_order contains duplicate ids: {AGENTSTOP_ORDER_IDS}"
        )

    def test_order_set_equals_agentstop_hook_set(self) -> None:
        """Core check: the two sets are equal (iff, no more, no fewer).

        **Validates: Requirements 1.5**
        """
        order_ids = set(AGENTSTOP_ORDER_IDS)
        assert order_ids == AGENTSTOP_IDS, (
            "agentstop_order must list exactly the agentStop hook ids.\n"
            f"  Missing from agentstop_order: {sorted(AGENTSTOP_IDS - order_ids)}\n"
            f"  Listed but not agentStop:     {sorted(order_ids - AGENTSTOP_IDS)}"
        )

    @given(hook_file=st_hook_files())
    @settings(max_examples=20)
    def test_membership_iff_agentstop(self, hook_file: Path) -> None:
        """For any hook file: in agentstop_order IFF its when.type is agentStop.

        Checks both directions of the biconditional over the real hook files:
        an agentStop hook MUST be listed, and a non-agentStop hook MUST NOT be.

        **Validates: Requirements 1.5**
        """
        order_ids = set(AGENTSTOP_ORDER_IDS)
        hook_id = hook_id_of(hook_file)
        is_agentstop = event_type_of(hook_file) == AGENTSTOP_EVENT_TYPE
        is_listed = hook_id in order_ids

        assert is_listed == is_agentstop, (
            f"Hook '{hook_id}' has when.type "
            f"{'== ' if is_agentstop else '!= '}agentStop but is "
            f"{'listed' if is_listed else 'absent'} in agentstop_order. "
            "Membership must hold if and only if when.type == agentStop."
        )
