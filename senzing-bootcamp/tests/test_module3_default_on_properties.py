"""Property-based tests for Module 3 Default-On configuration changes.

Validates structural invariants of the module dependency graph and
documentation after making Module 3 (System Verification) default-on.

Feature: module3-default-on
"""

from __future__ import annotations

from pathlib import Path

import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_CONFIG_DIR: Path = Path(__file__).resolve().parent.parent / "config"
_DEPENDENCIES_FILE: Path = _CONFIG_DIR / "module-dependencies.yaml"


# ---------------------------------------------------------------------------
# Helper functions
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


def get_backward_reachable(
    module_id: int,
    modules: dict,
    edge_types: list[str] | None = None,
) -> set[int]:
    """Find all modules reachable by following edges backward from a module.

    Traverses `requires` and `soft_requires` edges backward (i.e., from
    a module to its dependencies) using BFS.

    Args:
        module_id: The starting module to trace backward from.
        modules: The modules dictionary from module-dependencies.yaml.
        edge_types: List of edge field names to follow. Defaults to
            ["requires", "soft_requires"].

    Returns:
        Set of module IDs reachable by following edges backward.
    """
    if edge_types is None:
        edge_types = ["requires", "soft_requires"]

    visited: set[int] = set()
    queue: list[int] = [module_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        mod_data = modules.get(current, {})
        for edge_type in edge_types:
            deps = mod_data.get(edge_type, [])
            if deps is None:
                continue
            for dep in deps:
                if dep not in visited:
                    queue.append(dep)

    # Remove the starting module itself from the reachable set
    visited.discard(module_id)
    return visited


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_dependency_graph_variation(draw) -> dict:
    """Generate valid dependency graph variations from module-dependencies.yaml.

    Starts with the real dependency graph and applies valid mutations:
    - Permuting the order of edges in requires/soft_requires lists
    - Adding extra valid edges (edges that don't create cycles and point
      to modules with lower IDs)

    The invariant is that Module 3 must remain on the path from Module 2
    to Module 4 regardless of edge ordering or additional valid edges.

    Returns:
        A mutated but valid modules dictionary.
    """
    graph = load_dependency_graph()
    modules = graph["modules"]

    # Deep copy the modules dict to avoid mutating the original
    mutated: dict[int, dict] = {}
    for mod_id, mod_data in modules.items():
        mutated[mod_id] = {
            "name": mod_data["name"],
            "requires": list(mod_data.get("requires", []) or []),
            "soft_requires": list(mod_data.get("soft_requires", []) or []),
            "skip_if": mod_data.get("skip_if"),
        }

    # Mutation 1: Permute edge orderings in requires and soft_requires
    for mod_id in mutated:
        reqs = mutated[mod_id]["requires"]
        if len(reqs) > 1:
            perm = draw(st.permutations(reqs))
            mutated[mod_id]["requires"] = list(perm)

        soft_reqs = mutated[mod_id]["soft_requires"]
        if len(soft_reqs) > 1:
            perm = draw(st.permutations(soft_reqs))
            mutated[mod_id]["soft_requires"] = list(perm)

    # Mutation 2: Optionally add extra valid edges to random modules
    # Only add edges pointing to lower-numbered modules (preserves DAG)
    num_extra_edges = draw(st.integers(min_value=0, max_value=3))
    all_mod_ids = sorted(mutated.keys())

    for _ in range(num_extra_edges):
        if len(all_mod_ids) < 2:
            break
        # Pick a target module (must have at least one lower-numbered module)
        target_id = draw(
            st.sampled_from([m for m in all_mod_ids if m > min(all_mod_ids)])
        )
        # Pick a dependency from lower-numbered modules
        lower_mods = [m for m in all_mod_ids if m < target_id]
        if not lower_mods:
            continue
        dep_id = draw(st.sampled_from(lower_mods))

        # Add as either requires or soft_requires
        edge_type = draw(st.sampled_from(["requires", "soft_requires"]))
        if dep_id not in mutated[target_id][edge_type]:
            mutated[target_id][edge_type].append(dep_id)

    return mutated


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestModule3DefaultOnProperty3:
    """Property 3: Dependency graph reachability.

    Module 3 is on the path from Module 2 to Module 4.

    For any valid dependency graph variation parsed from
    module-dependencies.yaml, following the `requires` and `soft_requires`
    edges from Module 4 backward reaches Module 3, and from Module 3
    backward reaches Module 2.

    **Validates: Requirements 5, 6, 9**
    """

    @given(modules=st_dependency_graph_variation())
    @settings(max_examples=5)
    def test_module4_reaches_module3_backward(self, modules: dict) -> None:
        """Following edges backward from Module 4 reaches Module 3.

        Traversing the requires and soft_requires edges from Module 4
        backward through the dependency graph must reach Module 3,
        confirming Module 3 is a dependency (direct or transitive) of
        Module 4.
        """
        reachable_from_4 = get_backward_reachable(4, modules)
        assert 3 in reachable_from_4, (
            f"Module 3 is NOT reachable backward from Module 4. "
            f"Reachable modules: {sorted(reachable_from_4)}"
        )

    @given(modules=st_dependency_graph_variation())
    @settings(max_examples=5)
    def test_module3_reaches_module2_backward(self, modules: dict) -> None:
        """Following edges backward from Module 3 reaches Module 2.

        Traversing the requires and soft_requires edges from Module 3
        backward through the dependency graph must reach Module 2,
        confirming Module 2 is a dependency (direct or transitive) of
        Module 3.
        """
        reachable_from_3 = get_backward_reachable(3, modules)
        assert 2 in reachable_from_3, (
            f"Module 2 is NOT reachable backward from Module 3. "
            f"Reachable modules: {sorted(reachable_from_3)}"
        )

    @given(modules=st_dependency_graph_variation())
    @settings(max_examples=5)
    def test_module2_to_module4_path_includes_module3(
        self, modules: dict
    ) -> None:
        """Module 3 lies on the dependency path from Module 2 to Module 4.

        Verifies the combined property: Module 4 depends (transitively)
        on Module 3, and Module 3 depends (transitively) on Module 2,
        establishing Module 3 as an intermediate node on the path from
        Module 2 to Module 4.
        """
        reachable_from_4 = get_backward_reachable(4, modules)
        reachable_from_3 = get_backward_reachable(3, modules)

        assert 3 in reachable_from_4, (
            f"Module 3 not reachable from Module 4. "
            f"Module 4 reaches: {sorted(reachable_from_4)}"
        )
        assert 2 in reachable_from_3, (
            f"Module 2 not reachable from Module 3. "
            f"Module 3 reaches: {sorted(reachable_from_3)}"
        )
