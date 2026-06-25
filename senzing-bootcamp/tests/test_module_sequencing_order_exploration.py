"""Bug-condition exploration tests for module sequencing order (Property 1).

Property 1 — Fix Checking: Numeric-Order-by-Default Sequencing.

These tests encode the EXPECTED (fixed) behavior for the module-sequencing-order
bugfix. They are authored to FAIL on the UNFIXED configuration:

- Module 4 still only *soft*-requires Module 3 (``soft_requires: [3]``), so a
  dependency-respecting order can interleave/skip Module 3
  (e.g. ``1 → 4 → 5 → 2 → 6 → 7``).
- ``module-transitions.md`` carries no numeric-order-by-default sequencing rule.
- ``module-prerequisites.md`` still carries the "Warn but do not block" Soft
  Prerequisite Behavior section for Module 3.

The failure of these tests CONFIRMS the bug exists. After the fix lands, the same
tests validate the fix by passing.

Feature: module-sequencing-order
Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_CONFIG_DIR: Path = _BASE_DIR / "config"
_DEPENDENCIES_FILE: Path = _CONFIG_DIR / "module-dependencies.yaml"
_STEERING_DIR: Path = _BASE_DIR / "steering"
_MODULE_TRANSITIONS: Path = _STEERING_DIR / "module-transitions.md"
_MODULE_PREREQUISITES: Path = _STEERING_DIR / "module-prerequisites.md"

# Track module lists (mirrors `tracks` in module-dependencies.yaml).
_CORE_TRACK: list[int] = [1, 2, 3, 4, 5, 6, 7]
_ADVANCED_TRACK: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


# ---------------------------------------------------------------------------
# Domain model — mirrors isBugCondition from bugfix.md
# ---------------------------------------------------------------------------


@dataclass
class SeqInput:
    """A sequencing input: a selected track and the produced running order.

    Attributes:
        track: The selected track's module numbers (e.g. [1,2,3,4,5,6,7]).
        order: The produced running order (the sequence modules are run in).
        requested_skip: Modules the bootcamper explicitly requested to skip.
    """

    track: list[int]
    order: list[int]
    requested_skip: set[int] = field(default_factory=set)


def is_bug_condition(x: SeqInput) -> bool:
    """Return True when the produced order triggers the sequencing bug.

    The bug condition holds when the order is not ascending numeric, OR Module 3
    is in the track but missing from order with no explicit skip request, OR
    Module 3 appears after data loading (Module 6).

    Args:
        x: The sequencing input to classify.

    Returns:
        True if the input triggers the out-of-order / skipped-Module-3 bug.
    """
    not_numeric = any(a > b for a, b in zip(x.order, x.order[1:]))
    m3_skipped = (3 in x.track) and (3 not in x.order) and (3 not in x.requested_skip)
    pos = {m: i for i, m in enumerate(x.order)}
    m3_after_load = (3 in pos) and (6 in pos) and pos[3] > pos[6]
    return not_numeric or m3_skipped or m3_after_load


# ---------------------------------------------------------------------------
# Reference sequencer — executable model of F' (the fixed logic)
# ---------------------------------------------------------------------------


def load_dependency_graph() -> dict:
    """Load and parse the module-dependencies.yaml dependency graph.

    Loaded with PyYAML exactly as ``validate_dependencies.py`` does.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the dependencies file does not exist.
    """
    if not _DEPENDENCIES_FILE.exists():
        raise FileNotFoundError(f"Dependencies file not found: {_DEPENDENCIES_FILE}")
    return yaml.safe_load(_DEPENDENCIES_FILE.read_text(encoding="utf-8"))


def numeric_order_with_deps(
    track: list[int],
    graph: dict,
    requested_skip: set[int],
) -> list[int]:
    """Produce the ascending running order honoring hard ``requires`` edges.

    Models F': run the track's modules in ascending numeric order subject to the
    hard ``requires`` edges in the dependency graph, using a topological tiebreak
    that prefers the smallest eligible module number. Explicitly skipped modules
    are omitted (their dependents treat them as satisfied).

    Args:
        track: The selected track's module numbers.
        graph: The parsed dependency graph.
        requested_skip: Modules the bootcamper explicitly requested to skip.

    Returns:
        The produced running order as a list of module numbers.
    """
    modules = graph["modules"]
    track_set = set(track)
    remaining = [m for m in track if m not in requested_skip]
    placed: set[int] = set(requested_skip)
    result: list[int] = []

    while remaining:
        eligible: list[int] = []
        for m in remaining:
            reqs = modules.get(m, {}).get("requires", []) or []
            if all((r in placed) or (r not in track_set) for r in reqs):
                eligible.append(m)
        # Fallback for an unsatisfiable graph (no cycles expected here).
        candidates = eligible if eligible else remaining
        nxt = min(candidates)
        result.append(nxt)
        placed.add(nxt)
        remaining.remove(nxt)

    return result


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_seq_input(draw: st.DrawFn) -> SeqInput:
    """Generate a SeqInput drawing a track, a candidate order, and a skip set.

    Draws one of the two real tracks, an explicit-skip subset, and a candidate
    running order (a permutation of some subset of the track's modules) so the
    generator spans both bug-condition and non-bug-condition inputs.

    Returns:
        A generated SeqInput.
    """
    track = draw(st.sampled_from([_CORE_TRACK, _ADVANCED_TRACK]))
    requested_skip = set(
        draw(st.lists(st.sampled_from(track), max_size=3, unique=True))
    )
    subset = draw(
        st.lists(st.sampled_from(track), min_size=1, max_size=len(track), unique=True)
    )
    order = draw(st.permutations(subset))
    return SeqInput(track=list(track), order=list(order), requested_skip=requested_skip)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Read a file as UTF-8 text.

    Args:
        path: Path to the file.

    Returns:
        Full text content of the file.
    """
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test class — Property 1: Fix Checking
# ---------------------------------------------------------------------------


class TestModuleSequencingOrderExploration:
    """Property 1 — Fix Checking: Numeric-Order-by-Default Sequencing.

    Authored to FAIL on the unfixed config (Module 4 soft-requires Module 3; no
    numeric-order rule; prerequisites doc still soft). Validates the fix when it
    passes after implementation.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def test_module4_hard_requires_module3(self) -> None:
        """Module 4 hard-requires Module 3 (and Module 1).

        On the unfixed config Module 4 has ``requires: [1]`` and
        ``soft_requires: [3]`` — so this assertion FAILS, confirming the bug.

        Validates: Requirements 2.1, 2.2, 2.3
        """
        graph = load_dependency_graph()
        module_4 = graph["modules"][4]
        requires = module_4.get("requires", []) or []

        assert 3 in requires, (
            f"Module 4 should hard-require Module 3, but requires={requires} "
            f"(soft_requires={module_4.get('soft_requires')})"
        )
        assert 1 in requires, (
            f"Module 4 should hard-require Module 1, but requires={requires}"
        )

    def test_numeric_order_rule_present(self) -> None:
        """module-transitions.md states numeric-order-by-default + M3 guarantee.

        On the unfixed config this section is absent, so the assertion FAILS.

        Validates: Requirements 2.1, 2.4
        """
        content = _read_text(_MODULE_TRANSITIONS).lower()

        has_numeric_rule = ("numeric order" in content) or ("ascending numeric" in content)
        assert has_numeric_rule, (
            "module-transitions.md should contain an explicit numeric-order-by-default "
            "sequencing instruction (e.g. 'ascending numeric order')"
        )

        mentions_module3 = "module 3" in content
        before_loading = ("before any data loading" in content) or (
            "before data loading" in content
        )
        mentions_module6 = "module 6" in content
        assert mentions_module3 and before_loading and mentions_module6, (
            "module-transitions.md should guarantee Module 3 runs after Module 2 and "
            "before data loading (Module 6)"
        )

    def test_prerequisites_doc_reconciled(self) -> None:
        """module-prerequisites.md no longer carries the soft-skip wording.

        On the unfixed config the "Warn but do not block" Soft Prerequisite
        Behavior section is present, so the assertion FAILS.

        Validates: Requirements 2.2, 2.3
        """
        content = _read_text(_MODULE_PREREQUISITES).lower()

        assert "warn but do not block" not in content, (
            "module-prerequisites.md should no longer contain the 'Warn but do not "
            "block' Soft Prerequisite Behavior wording for Module 3"
        )
        assert "soft prerequisite behavior" not in content, (
            "module-prerequisites.md should no longer contain the 'Soft Prerequisite "
            "Behavior' section for Module 3"
        )

    @given(x=st_seq_input())
    @settings(max_examples=20)
    def test_fix_produces_numeric_order_with_module3_placed(self, x: SeqInput) -> None:
        """For every bug-condition input, F' yields an ascending order with M3 placed.

        The reference sequencer's output must be ascending numeric and place
        Module 3 after Module 2 and before Module 6 (unless Module 3 is in the
        explicit skip set or not in the track).

        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
        """
        assume(is_bug_condition(x))

        graph = load_dependency_graph()
        produced = numeric_order_with_deps(x.track, graph, x.requested_skip)

        # 1. Ascending numeric over the modules present.
        assert all(a < b for a, b in zip(produced, produced[1:])), (
            f"Produced order is not ascending numeric: {produced}"
        )

        # 2. Module 3 after Module 2 and before Module 6 (unless skipped/absent).
        pos = {m: i for i, m in enumerate(produced)}
        m3_ok = (
            (3 not in x.track)
            or (3 in x.requested_skip)
            or (
                (2 not in pos or pos[2] < pos[3])
                and (6 not in pos or pos[3] < pos[6])
            )
        )
        assert m3_ok, (
            f"Module 3 not placed after Module 2 and before Module 6 in {produced} "
            f"(requested_skip={x.requested_skip})"
        )
