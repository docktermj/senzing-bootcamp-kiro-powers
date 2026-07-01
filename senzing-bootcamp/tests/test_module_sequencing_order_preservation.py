"""Preservation property tests for the module-sequencing-order bugfix.

Property 2 (Preservation — Non-Buggy Sequences Unchanged): for any input where
the bug condition does NOT hold, the fixed sequencing logic F' must behave
identically to the original logic F (``F(X) == F'(X)``), and all behavior the
fix is not meant to touch must remain unchanged:

- Track membership for Core and Advanced (Requirement 3.1)
- Genuine hard-dependency enforcement (Requirement 3.2)
- Explicit-skip handling for Module 3 (Requirement 3.3)
- The Module 7 -> Module 5 quality feedback loop (Requirement 3.4)
- Path-completion detection (Requirement 3.5)

Observation-first methodology: this suite is authored against the UNFIXED
configuration. It snapshots (via SHA-256) the regions the fix does not touch
and pins the existing baseline values, so it PASSES on the unfixed config and
continues to PASS after the fix (the fix only changes Module 4's edge).

Spec: .kiro/specs/module-sequencing-order

Conventions: stdlib + Hypothesis only, except the dependency graph is loaded
with PyYAML exactly as ``validate_dependencies.py`` does (documented tech.md
exception).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path constants (relative to the test file, per python-conventions.md)
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_CONFIG_DIR: Path = _BASE_DIR / "config"
_STEERING_DIR: Path = _BASE_DIR / "steering"

_DEPENDENCIES_FILE: Path = _CONFIG_DIR / "module-dependencies.yaml"
_TRANSITIONS_FILE: Path = _STEERING_DIR / "module-transitions.md"
_COMPLETION_TRACK_FILE: Path = _STEERING_DIR / "module-completion-track.md"

# Track definitions (expected, stable) used by strategies.
_CORE_TRACK: list[int] = [1, 2, 3, 4, 5, 6, 7]
_ADVANCED_TRACK: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

# Module that loads real data; Module 3 must precede it.
_DATA_LOADING_MODULE: int = 6

# ---------------------------------------------------------------------------
# Baseline snapshots captured from the UNFIXED configuration (observation phase)
# ---------------------------------------------------------------------------
# SHA-256 of the unrelated dependency-graph regions: every module entry EXCEPT
# Module 4 (the only entry the fix edits), plus the entire ``tracks`` and
# ``gates`` blocks. Computed from the unfixed config; must remain unchanged.
_BASELINE_GRAPH_REGIONS_SHA256: str = (
    "6dac398bb43906109221ee606e61c01df44f78b0b6422880d0602c8711c867aa"
)
# SHA-256 of module-completion-track.md. Re-baselined for the
# recap-completeness-and-pdf spec: task 3.4 legitimately edited this file to add
# the "Recap Reconciliation & Backfill (Path A final safety net)" section that
# wires track-completion recap reconciliation. That edit is unrelated to the
# module-sequencing-order fix this suite guards, so the baseline is moved
# observation-first to the current file contents to keep the preservation
# snapshot honest.
_BASELINE_COMPLETION_TRACK_SHA256: str = (
    "2ddf831282d18c1bcc676d2d47177e2df257b2315586c1e71bb326364e818032"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_dependency_graph() -> dict:
    """Load and parse the module-dependencies.yaml file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the dependencies file does not exist.
    """
    if not _DEPENDENCIES_FILE.exists():
        raise FileNotFoundError(
            f"Dependencies file not found: {_DEPENDENCIES_FILE}"
        )
    return yaml.safe_load(_DEPENDENCIES_FILE.read_text(encoding="utf-8"))


def graph_regions_sha256(graph: dict) -> str:
    """Compute the SHA-256 of the dependency-graph regions the fix does not touch.

    Covers every module entry except Module 4, plus the full ``tracks`` and
    ``gates`` blocks, serialized deterministically.

    Args:
        graph: The parsed dependency graph.

    Returns:
        Hex SHA-256 digest of the unrelated regions.
    """
    payload = {
        "modules_other": {
            k: v for k, v in graph["modules"].items() if k != 4
        },
        "tracks": graph["tracks"],
        "gates": graph["gates"],
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    """Compute the SHA-256 of a file's raw bytes.

    Args:
        path: File to hash.

    Returns:
        Hex SHA-256 digest of the file contents.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Shared domain model (mirrors isBugCondition in bugfix.md)
# ---------------------------------------------------------------------------


@dataclass
class SeqInput:
    """A sequencing input: a selected track, a produced order, and explicit skips.

    Attributes:
        track: Selected track modules, e.g. ``[1, 2, 3, 4, 5, 6, 7]``.
        order: The produced running order.
        requested_skip: Modules the bootcamper explicitly requested to skip.
    """

    track: list[int]
    order: list[int]
    requested_skip: set[int] = field(default_factory=set)


def is_bug_condition(x: SeqInput) -> bool:
    """Return True when the sequencing input triggers the bug.

    Mirrors ``isBugCondition`` in bugfix.md: the order is not ascending
    numeric, OR Module 3 is in the track but silently missing from the order
    (no explicit skip), OR Module 3 appears after data loading (Module 6).

    Args:
        x: The sequencing input to classify.

    Returns:
        True if the input triggers the bug condition, False otherwise.
    """
    not_numeric = any(a > b for a, b in zip(x.order, x.order[1:]))
    m3_skipped = (
        (3 in x.track) and (3 not in x.order) and (3 not in x.requested_skip)
    )
    pos = {m: i for i, m in enumerate(x.order)}
    m3_after_load = (3 in pos) and (6 in pos) and pos[3] > pos[6]
    return not_numeric or m3_skipped or m3_after_load


def numeric_order_with_deps(
    track: list[int],
    graph: dict,
    requested_skip: set[int],
) -> list[int]:
    """Reference sequencer (executable model of F').

    Returns the track's modules in ascending numeric order subject to hard
    ``requires`` edges, omitting modules the bootcamper explicitly skipped. The
    topological tiebreak always prefers the smallest eligible module number, so
    when dependencies only point to lower-numbered modules the result is the
    sorted track minus skips.

    Args:
        track: Selected track modules.
        graph: The parsed dependency graph.
        requested_skip: Modules explicitly skipped (treated as satisfied).

    Returns:
        The produced ascending running order.
    """
    skip = set(requested_skip)
    pending = sorted(m for m in track if m not in skip)
    completed: set[int] = set(skip)
    result: list[int] = []

    while pending:
        progressed = False
        for m in pending:
            reqs = graph["modules"][m].get("requires", []) or []
            relevant = [r for r in reqs if r in track and r not in skip]
            if all(r in completed for r in relevant):
                result.append(m)
                completed.add(m)
                pending.remove(m)
                progressed = True
                break
        if not progressed:
            # Unsatisfiable remainder (should not happen for this graph) —
            # append ascending so the function always terminates.
            result.extend(pending)
            break
    return result


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_seq_input(draw) -> SeqInput:
    """Generate an arbitrary sequencing input over a real track.

    Draws a track (Core or Advanced), a candidate order (a permutation of a
    subset of the track), and an explicit-skip subset.

    Returns:
        A generated ``SeqInput``.
    """
    track = draw(st.sampled_from([_CORE_TRACK, _ADVANCED_TRACK]))
    # Candidate order: a subset of the track, in some permutation.
    subset = draw(
        st.lists(st.sampled_from(track), unique=True, min_size=0, max_size=len(track))
    )
    order = draw(st.permutations(subset))
    requested_skip = set(
        draw(st.lists(st.sampled_from(track), unique=True, max_size=len(track)))
    )
    return SeqInput(track=list(track), order=list(order), requested_skip=requested_skip)


@st.composite
def st_non_buggy_canonical_input(draw) -> SeqInput:
    """Generate a non-buggy input whose order is the canonical ascending order.

    Draws a track and an explicit-skip subset, then sets ``order`` to the
    ascending track minus the skipped modules — i.e., the canonical, correctly
    sequenced output. These are exactly the inputs Property 2 requires F' to
    reproduce identically.

    Returns:
        A ``SeqInput`` whose order is the canonical ascending sequence.
    """
    track = draw(st.sampled_from([_CORE_TRACK, _ADVANCED_TRACK]))
    requested_skip = set(
        draw(st.lists(st.sampled_from(track), unique=True, max_size=len(track)))
    )
    order = [m for m in sorted(track) if m not in requested_skip]
    return SeqInput(track=list(track), order=order, requested_skip=requested_skip)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestModuleSequencingOrderPreservation:
    """Property 2 — Preservation: non-buggy behavior is unchanged by the fix.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """

    # -- Track membership preserved (3.1) --------------------------------

    def test_track_membership_preserved(self) -> None:
        """Core and Advanced tracks contain the same modules as before.

        Validates: Requirements 3.1
        """
        graph = load_dependency_graph()
        assert graph["tracks"]["core_bootcamp"]["modules"] == [1, 2, 3, 4, 5, 6, 7]
        assert graph["tracks"]["advanced_topics"]["modules"] == [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
        ]

    # -- Hard dependencies preserved (3.2) -------------------------------

    def test_hard_dependencies_preserved(self) -> None:
        """Every pre-existing hard ``requires`` edge is unchanged.

        The only edge change the fix introduces is Module 4 gaining a hard
        requirement on Module 3; all other ``requires`` edges stay exactly as
        they are on the unfixed config.

        Validates: Requirements 3.2
        """
        graph = load_dependency_graph()
        modules = graph["modules"]

        # Pre-existing edges that must never change.
        assert modules[1].get("requires", []) == []
        assert modules[2].get("requires", []) == []
        assert modules[3]["requires"] == [2]
        assert modules[5]["requires"] == [4]
        assert modules[6]["requires"] == [2, 5]
        assert modules[7]["requires"] == [6]
        assert modules[8]["requires"] == [7]
        assert modules[9]["requires"] == [8]
        assert modules[10]["requires"] == [9]
        assert modules[11]["requires"] == [10]

    # -- Explicit-skip preserved (3.3) -----------------------------------

    def test_explicit_skip_of_module3_not_a_bug(self) -> None:
        """An order omitting Module 3 after an explicit skip is NOT a bug.

        Validates: Requirements 3.3
        """
        x = SeqInput(
            track=list(_CORE_TRACK),
            order=[1, 2, 4, 5, 6, 7],
            requested_skip={3},
        )
        assert is_bug_condition(x) is False

    def test_explicit_skip_sequencer_omits_module3(self) -> None:
        """The reference sequencer omits Module 3 on explicit skip, rest ascending.

        Validates: Requirements 3.3
        """
        graph = load_dependency_graph()
        order = numeric_order_with_deps(_CORE_TRACK, graph, {3})
        assert 3 not in order
        assert order == [1, 2, 4, 5, 6, 7]
        assert order == sorted(order)  # remainder stays ascending

    @given(x=st_seq_input())
    @settings(max_examples=20)
    def test_explicit_skip_subset_keeps_ascending(self, x: SeqInput) -> None:
        """For any explicit skip set, the sequencer output omits skips and ascends.

        Validates: Requirements 3.3
        """
        graph = load_dependency_graph()
        produced = numeric_order_with_deps(x.track, graph, x.requested_skip)
        # Explicitly skipped modules are never produced.
        assert all(m not in produced for m in x.requested_skip)
        # The produced order is strictly ascending numeric.
        assert all(a < b for a, b in zip(produced, produced[1:]))

    # -- Quality feedback loop preserved (3.4) ---------------------------

    def test_quality_feedback_loop_documented(self) -> None:
        """module-transitions.md still documents the Module 7 -> Module 5 loop.

        Validates: Requirements 3.4
        """
        content = _TRANSITIONS_FILE.read_text(encoding="utf-8")
        assert "Quality Feedback Loop" in content
        # The backward transition from Module 7 back to Module 5 is documented.
        assert "Module 7" in content and "Module 5" in content
        assert "backward transition" in content.lower()

    def test_quality_feedback_loop_not_a_forward_numeric_violation(self) -> None:
        """A 7 -> 5 backward transition is a separate path, not a produced order.

        The forward numeric-order default produces ascending orders only; the
        7 -> 5 quality loop is an explicit, separate backward transition and is
        not generated by (nor forbidden by classifying) the forward sequencer.

        Validates: Requirements 3.4
        """
        graph = load_dependency_graph()
        # The forward default never produces a backward 7 -> 5 step.
        produced = numeric_order_with_deps(_CORE_TRACK, graph, set())
        assert all(a < b for a, b in zip(produced, produced[1:]))
        # The explicit backward transition itself is a non-numeric order and is
        # therefore correctly outside the forward-sequencing default's domain.
        backward = SeqInput(track=list(_CORE_TRACK), order=[7, 5], requested_skip=set())
        assert is_bug_condition(backward) is True

    # -- Path-completion detection preserved (3.5) -----------------------

    def test_path_completion_mapping_preserved(self) -> None:
        """module-completion-track.md still maps Core->M7 and Advanced->M11.

        Validates: Requirements 3.5
        """
        content = _COMPLETION_TRACK_FILE.read_text(encoding="utf-8")
        assert "Path Completion Detection" in content
        # Core Bootcamp completes after Module 7.
        assert "Core Bootcamp" in content
        assert "Module 7" in content
        # Advanced Topics completes after Module 11.
        assert "Advanced Topics" in content
        assert "Module 11" in content

    # -- Snapshot of unrelated regions (Preservation) --------------------

    def test_graph_regions_snapshot_unchanged(self) -> None:
        """Unrelated graph regions match the captured unfixed baseline.

        Covers every module entry except Module 4, plus the ``tracks`` and
        ``gates`` blocks.

        Validates: Requirements 3.1, 3.2
        """
        graph = load_dependency_graph()
        assert (  # brittle-allow: intentional preservation snapshot (Req 3.1, 3.2)
            graph_regions_sha256(graph) == _BASELINE_GRAPH_REGIONS_SHA256
        )

    def test_completion_track_file_snapshot_unchanged(self) -> None:
        """module-completion-track.md is byte-for-byte unchanged from baseline.

        Validates: Requirements 3.5
        """
        assert (  # brittle-allow: intentional byte-for-byte preservation snapshot (Req 3.5)
            file_sha256(_COMPLETION_TRACK_FILE) == _BASELINE_COMPLETION_TRACK_SHA256
        )

    # -- Non-bug-condition equivalence: F(X) == F'(X) --------------------

    @given(x=st_non_buggy_canonical_input())
    @settings(max_examples=20)
    def test_non_buggy_orders_reproduced_identically(self, x: SeqInput) -> None:
        """F' reproduces an already-correct ascending order identically.

        For every input whose order is already ascending numeric with Module 3
        placed correctly (or explicitly skipped) -- i.e., NOT a bug condition --
        the reference sequencer produces exactly that same order.

        Validates: Requirements 3.1, 3.2, 3.3
        """
        assume(not is_bug_condition(x))
        graph = load_dependency_graph()
        produced = numeric_order_with_deps(x.track, graph, x.requested_skip)
        assert produced == x.order
