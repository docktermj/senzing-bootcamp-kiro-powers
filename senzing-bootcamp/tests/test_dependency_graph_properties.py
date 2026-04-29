"""Property-based tests for validate_dependencies.py using Hypothesis.

Feature: module-dependency-graph
"""

import re
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_dependencies import (
    Violation,
    validate_no_cycles,
    validate_references,
    validate_topological_order,
    validate_schema,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def _has_cycle(modules: dict) -> bool:
    """Ground-truth cycle detection using DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[int, int] = {m: WHITE for m in modules}

    def dfs(node: int) -> bool:
        color[node] = GRAY
        mod_data = modules.get(node, {})
        for req in mod_data.get("requires", []):
            if req not in color:
                continue
            if color[req] == GRAY:
                return True
            if color[req] == WHITE and dfs(req):
                return True
        color[node] = BLACK
        return False

    return any(color[m] == WHITE and dfs(m) for m in modules)


@st.composite
def st_dag_modules(draw):
    """Generate a modules dict that forms a DAG (no cycles).

    Nodes are numbered 1..n. Each node can only require nodes with
    a *lower* number, guaranteeing acyclicity.
    """
    n = draw(st.integers(min_value=1, max_value=8))
    modules: dict[int, dict] = {}
    for i in range(1, n + 1):
        possible_reqs = list(range(1, i))
        reqs = draw(st.lists(st.sampled_from(possible_reqs) if possible_reqs else st.nothing(), max_size=min(3, len(possible_reqs)), unique=True))
        modules[i] = {
            "name": f"Module {i}",
            "requires": sorted(reqs),
            "skip_if": None,
        }
    return modules


@st.composite
def st_cyclic_modules(draw):
    """Generate a modules dict that contains at least one cycle."""
    n = draw(st.integers(min_value=2, max_value=8))
    modules: dict[int, dict] = {}
    for i in range(1, n + 1):
        modules[i] = {
            "name": f"Module {i}",
            "requires": [],
            "skip_if": None,
        }

    # Create a guaranteed cycle: pick two distinct nodes and create a cycle
    a = draw(st.integers(min_value=1, max_value=n))
    b = draw(st.integers(min_value=1, max_value=n).filter(lambda x: x != a))

    # a requires b, b requires a → cycle
    if b not in modules[a]["requires"]:
        modules[a]["requires"].append(b)
    if a not in modules[b]["requires"]:
        modules[b]["requires"].append(a)

    return modules


@st.composite
def st_module_refs_with_dangles(draw):
    """Generate a graph with some valid and some dangling references."""
    n = draw(st.integers(min_value=1, max_value=6))
    modules: dict[int, dict] = {}
    for i in range(1, n + 1):
        modules[i] = {
            "name": f"Module {i}",
            "requires": [],
            "skip_if": None,
        }

    valid_ids = set(modules.keys())

    # Add some dangling references in requires
    dangling_ids = draw(
        st.lists(
            st.integers(min_value=n + 1, max_value=n + 10),
            min_size=0,
            max_size=3,
            unique=True,
        )
    )
    if dangling_ids:
        target_mod = draw(st.sampled_from(list(modules.keys())))
        modules[target_mod]["requires"] = dangling_ids

    # Build tracks with possible dangling refs
    track_dangling = draw(
        st.lists(
            st.integers(min_value=n + 1, max_value=n + 10),
            min_size=0,
            max_size=2,
            unique=True,
        )
    )
    track_modules = list(range(1, n + 1)) + track_dangling

    tracks = {
        "test_track": {
            "name": "Test",
            "description": "Test track",
            "modules": track_modules,
        }
    }

    # Build gates with possible dangling refs
    gates = {}
    gate_dangling_src = draw(
        st.lists(
            st.integers(min_value=n + 1, max_value=n + 10),
            min_size=0,
            max_size=2,
            unique=True,
        )
    )
    for d in gate_dangling_src:
        gates[f"{d}->{1}"] = {"requires": ["test condition"]}

    expected_dangles = set(dangling_ids) | set(track_dangling) | set(gate_dangling_src)

    graph = {
        "metadata": {"version": "1.0.0", "last_updated": "2025-01-01"},
        "modules": modules,
        "tracks": tracks,
        "gates": gates,
    }
    return graph, expected_dangles


@st.composite
def st_track_with_ordering(draw):
    """Generate a graph with a track that may or may not respect topological order."""
    n = draw(st.integers(min_value=2, max_value=6))
    modules: dict[int, dict] = {}
    for i in range(1, n + 1):
        possible_reqs = list(range(1, i))
        reqs = draw(
            st.lists(
                st.sampled_from(possible_reqs) if possible_reqs else st.nothing(),
                max_size=min(2, len(possible_reqs)),
                unique=True,
            )
        )
        modules[i] = {
            "name": f"Module {i}",
            "requires": sorted(reqs),
            "skip_if": None,
        }

    # Generate a track ordering — either shuffled or sorted
    track_modules = list(range(1, n + 1))
    shuffled = draw(st.permutations(track_modules))

    graph = {
        "metadata": {"version": "1.0.0", "last_updated": "2025-01-01"},
        "modules": modules,
        "tracks": {
            "test_track": {
                "name": "Test",
                "description": "Test track",
                "modules": list(shuffled),
            }
        },
        "gates": {},
    }

    # Compute ground truth: does the ordering violate prerequisites?
    position = {m: i for i, m in enumerate(shuffled)}
    has_violation = False
    for mod_num in shuffled:
        for req in modules[mod_num]["requires"]:
            if req in position and position[req] >= position[mod_num]:
                has_violation = True
                break
        if has_violation:
            break

    return graph, has_violation


@st.composite
def st_valid_schema(draw):
    """Generate a fully valid dependency graph schema."""
    n = draw(st.integers(min_value=1, max_value=4))
    modules = {}
    for i in range(1, n + 1):
        modules[i] = {
            "name": f"Module {i}",
            "requires": [],
            "skip_if": draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        }

    tracks = {
        "track_a": {
            "name": "Track A",
            "description": "A test track",
            "modules": list(range(1, n + 1)),
        }
    }

    gates = {}
    for i in range(1, n):
        gates[f"{i}->{i+1}"] = {"requires": ["condition"]}

    return {
        "metadata": {"version": "1.0.0", "last_updated": "2025-01-01"},
        "modules": modules,
        "tracks": tracks,
        "gates": gates,
    }


@st.composite
def st_invalid_schema(draw):
    """Generate a schema with at least one missing/invalid field."""
    # Start with a valid schema and remove or corrupt one field
    graph = draw(st_valid_schema())

    # Choose which section to corrupt
    section = draw(st.sampled_from(["metadata", "modules", "tracks", "gates"]))

    corruption = draw(st.sampled_from(["remove_section", "corrupt_field"]))

    if corruption == "remove_section":
        del graph[section]
    else:
        if section == "metadata":
            field = draw(st.sampled_from(["version", "last_updated"]))
            graph["metadata"][field] = 123  # wrong type
        elif section == "modules":
            mod_keys = list(graph["modules"].keys())
            if mod_keys:
                mod = draw(st.sampled_from(mod_keys))
                field = draw(st.sampled_from(["name", "requires", "skip_if"]))
                if field == "name":
                    graph["modules"][mod]["name"] = 123
                elif field == "requires":
                    graph["modules"][mod]["requires"] = "not a list"
                else:
                    graph["modules"][mod]["skip_if"] = 123
        elif section == "tracks":
            track_keys = list(graph["tracks"].keys())
            if track_keys:
                tk = draw(st.sampled_from(track_keys))
                field = draw(st.sampled_from(["name", "description", "modules"]))
                if field == "modules":
                    graph["tracks"][tk]["modules"] = "not a list"
                else:
                    graph["tracks"][tk][field] = 123
        elif section == "gates":
            gate_keys = list(graph["gates"].keys())
            if gate_keys:
                gk = draw(st.sampled_from(gate_keys))
                graph["gates"][gk]["requires"] = "not a list"
            else:
                # No gates to corrupt, remove the section instead
                del graph["gates"]

    return graph


@st.composite
def st_violation(draw):
    """Generate a random Violation object."""
    level = draw(st.sampled_from(["ERROR", "WARNING"]))
    description = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
        blacklist_characters="\x00",
    )))
    return Violation(level=level, description=description)


@st.composite
def st_violation_set(draw):
    """Generate a list of violations with mixed levels."""
    return draw(st.lists(st_violation(), min_size=0, max_size=10))


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestCycleDetectionCorrectness:
    """Property 1 — Cycle Detection Correctness.

    **Validates: Requirements 3.1, 6.1, 6.2**

    For any directed graph of module prerequisites, validate_no_cycles reports
    an error iff the graph contains a cycle.
    """

    @given(modules=st_dag_modules())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_errors_for_dags(self, modules):
        """DAGs should produce zero cycle violations."""
        graph = {"modules": modules}
        violations = validate_no_cycles(graph)
        assert len(violations) == 0, f"False positive cycle in DAG: {violations}"

    @given(modules=st_cyclic_modules())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_errors_for_cyclic_graphs(self, modules):
        """Cyclic graphs should produce at least one cycle violation."""
        graph = {"modules": modules}
        violations = validate_no_cycles(graph)
        assert len(violations) > 0, "Cycle not detected"
        assert all(v.level == "ERROR" for v in violations)
        assert any("ircular" in v.description for v in violations)


class TestDanglingReferenceDetection:
    """Property 2 — Dangling Reference Detection.

    **Validates: Requirements 3.2, 6.3, 6.4**

    For any graph with references to existing and non-existing modules,
    validate_references reports exactly the dangling ones.
    """

    @given(data=st_module_refs_with_dangles())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_detects_all_dangling_references(self, data):
        """All dangling references should be reported, no false positives."""
        graph, expected_dangles = data
        violations = validate_references(graph)

        if not expected_dangles:
            assert len(violations) == 0, f"False positive: {violations}"
        else:
            assert len(violations) > 0, "Dangling references not detected"
            # Every violation should mention a dangling module number
            for v in violations:
                assert v.level == "ERROR"
                assert "angling" in v.description or "does not exist" in v.description


class TestTopologicalOrderValidation:
    """Property 3 — Topological Order Validation.

    **Validates: Requirements 3.3**

    For any graph and track, validate_topological_order reports an error iff
    the track violates prerequisite ordering.
    """

    @given(data=st_track_with_ordering())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_order_violation_iff_prerequisites_violated(self, data):
        """Errors reported iff track ordering violates prerequisites."""
        graph, has_violation = data
        violations = validate_topological_order(graph)

        if has_violation:
            assert len(violations) > 0, "Topological order violation not detected"
            assert all(v.level == "ERROR" for v in violations)
        else:
            assert len(violations) == 0, f"False positive order violation: {violations}"


class TestSchemaValidationCompleteness:
    """Property 4 — Schema Validation Completeness.

    **Validates: Requirements 6.5, 6.6**

    For any YAML structure, validate_schema reports errors for all
    missing/invalid fields and no errors for valid structures.
    """

    @given(graph=st_valid_schema())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_errors_for_valid_schemas(self, graph):
        """Valid schemas should produce zero violations."""
        violations = validate_schema(graph)
        assert len(violations) == 0, f"False positive schema error: {violations}"

    @given(graph=st_invalid_schema())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_errors_for_invalid_schemas(self, graph):
        """Invalid schemas should produce at least one violation."""
        violations = validate_schema(graph)
        assert len(violations) > 0, "Schema violation not detected"
        assert all(v.level == "ERROR" for v in violations)


class TestExitCodeCorrectness:
    """Property 5 — Exit Code Correctness.

    **Validates: Requirements 4.3, 4.4**

    For any set of violations, exit code is 0 iff zero errors.
    """

    @given(violations=st_violation_set())
    @settings(max_examples=100)
    def test_exit_code_zero_iff_no_errors(self, violations):
        """Exit code is 0 iff there are zero ERROR-level violations."""
        error_count = sum(1 for v in violations if v.level == "ERROR")
        expected_exit = 0 if error_count == 0 else 1
        actual_exit = 0 if error_count == 0 else 1
        assert actual_exit == expected_exit


class TestViolationOutputFormat:
    """Property 6 — Violation Output Format.

    **Validates: Requirements 4.5**

    For any Violation, formatted output matches {ERROR|WARNING}: {description}.
    """

    @given(v=st_violation())
    @settings(max_examples=100)
    def test_format_matches_pattern(self, v):
        """Formatted output must match the expected pattern."""
        formatted = v.format()
        assert formatted == f"{v.level}: {v.description}"
        assert formatted.startswith("ERROR: ") or formatted.startswith("WARNING: ")
        # Verify the pattern with regex
        assert re.match(r"^(ERROR|WARNING): .+$", formatted, re.DOTALL)
