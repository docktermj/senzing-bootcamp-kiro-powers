"""Property test for budget Router_Ceiling preservation (round-trip).

Feature: module-router-standardization

Property 6: Budget Router_Ceiling preservation (round-trip) — for any existing
``budget`` block containing the standard keys and a ``router_ceiling`` value,
running ``measure_steering.update_index`` preserves every original budget key and
the exact ``router_ceiling`` value in the rewritten index.

**Validates: Requirements 4.5**

The standard budget keys are ``total_tokens``, ``reference_window``,
``warn_threshold_pct``, ``critical_threshold_pct``, and
``split_threshold_tokens``. ``update_index`` rebuilds the budget block while
preserving ``split_threshold_tokens`` and ``router_ceiling`` read from the
existing content (re-emitting the fixed-policy keys), so this round-trip asserts
the key set survives and the exact ``router_ceiling`` value is carried through.
"""

from __future__ import annotations

import importlib
import re
import shutil
import sys
import tempfile
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given, settings

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# The full set of standard budget keys that must survive a round-trip, plus the
# router_ceiling added by this feature.
_STANDARD_BUDGET_KEYS = (
    "total_tokens",
    "reference_window",
    "warn_threshold_pct",
    "critical_threshold_pct",
    "split_threshold_tokens",
)


def _load_measure_steering():
    """Import and reload measure_steering for a fresh module instance."""
    import measure_steering

    importlib.reload(measure_steering)
    return measure_steering


# ---------------------------------------------------------------------------
# Strategies (st_-prefixed per python-conventions.md)
# ---------------------------------------------------------------------------


def st_filename():
    """Generate steering-style markdown filenames."""
    return st.from_regex(r"[a-z][a-z0-9\-]{0,19}\.md", fullmatch=True)


def st_file_metadata():
    """Generate a {filename: {token_count, size_category}} metadata dict."""
    return st.dictionaries(
        keys=st_filename(),
        values=st.integers(min_value=0, max_value=200_000),
        min_size=0,
        max_size=6,
    ).map(
        lambda d: {
            name: {"token_count": count, "size_category": "small"}
            for name, count in d.items()
        }
    )


def st_router_ceiling():
    """Generate an arbitrary non-negative router_ceiling value."""
    return st.integers(min_value=0, max_value=200_000)


def st_split_threshold():
    """Generate an arbitrary non-negative split_threshold_tokens value."""
    return st.integers(min_value=0, max_value=200_000)


def _build_budget_index(total_tokens, split_threshold, router_ceiling):
    """Return YAML text with a complete budget block (standard keys + ceiling)."""
    return (
        "modules:\n"
        "  1: module-01.md\n"
        "\n"
        "budget:\n"
        f"  total_tokens: {total_tokens}\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n"
        "  critical_threshold_pct: 80\n"
        f"  split_threshold_tokens: {split_threshold}\n"
        f"  router_ceiling: {router_ceiling}\n"
    )


def _extract_budget_block(content: str) -> str:
    """Return the budget block text (header to next top-level key or EOF)."""
    match = re.search(r"^budget:\s*$", content, re.MULTILINE)
    assert match is not None, f"no budget section in:\n{content}"
    after = content[match.start():]
    nxt = re.search(r"^\S", after[len("budget:"):], re.MULTILINE)
    if nxt:
        return after[: len("budget:") + nxt.start()]
    return after


# ---------------------------------------------------------------------------
# Property 6: Budget Router_Ceiling preservation (round-trip)
# ---------------------------------------------------------------------------


class TestBudgetRouterCeilingPreservation:
    """update_index preserves all standard budget keys and the exact ceiling.

    **Validates: Requirements 4.5**
    """

    # Feature: module-router-standardization, Property 6: Budget Router_Ceiling
    # preservation (round-trip) — for any existing budget block containing the
    # standard keys and a router_ceiling value, running update_index preserves
    # every original budget key and the exact router_ceiling value.

    @given(
        file_metadata=st_file_metadata(),
        split_threshold=st_split_threshold(),
        router_ceiling=st_router_ceiling(),
    )
    @settings(max_examples=150)
    def test_budget_keys_and_ceiling_round_trip(
        self, file_metadata, split_threshold, router_ceiling
    ):
        mod = _load_measure_steering()
        total_tokens = sum(m["token_count"] for m in file_metadata.values())

        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text(
                _build_budget_index(total_tokens, split_threshold, router_ceiling),
                encoding="utf-8",
            )

            mod.update_index(index_path, file_metadata, total_tokens, steering_dir)

            updated = index_path.read_text(encoding="utf-8")
            budget_block = _extract_budget_block(updated)

            # Every standard budget key survives the round-trip.
            for key in _STANDARD_BUDGET_KEYS:
                assert re.search(rf"^\s+{key}:\s", budget_block, re.MULTILINE), (
                    f"standard budget key {key!r} missing after update:\n{budget_block}"
                )

            # The exact router_ceiling value is preserved.
            ceiling_match = re.search(
                r"^\s+router_ceiling:\s*(\d+)\s*$", budget_block, re.MULTILINE
            )
            assert ceiling_match is not None, (
                f"router_ceiling missing after update:\n{budget_block}"
            )
            assert int(ceiling_match.group(1)) == router_ceiling, (
                f"router_ceiling changed: {router_ceiling} -> {ceiling_match.group(1)}"
            )

            # The exact split_threshold_tokens value is preserved too.
            split_match = re.search(
                r"^\s+split_threshold_tokens:\s*(\d+)\s*$", budget_block, re.MULTILINE
            )
            assert split_match is not None
            assert int(split_match.group(1)) == split_threshold, (
                f"split_threshold_tokens changed: {split_threshold} -> "
                f"{split_match.group(1)}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)
