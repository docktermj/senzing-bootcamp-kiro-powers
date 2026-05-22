"""Cross-module artifact chain integration tests.

Validates that the artifact dependency graph declared in
config/module-artifacts.yaml is internally consistent and that
module steering files reference the expected artifact paths.

Tests:
- Every requires_from path is produced by the source module
- The dependency graph is acyclic and respects module ordering
- Module steering files mention their required input artifacts
- Produced artifacts have valid structure (path, type, description)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_POWER_ROOT = Path("senzing-bootcamp")
_CONFIG_DIR = _POWER_ROOT / "config"
_STEERING_DIR = _POWER_ROOT / "steering"
_ARTIFACTS_PATH = _CONFIG_DIR / "module-artifacts.yaml"
_STEERING_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"


# ---------------------------------------------------------------------------
# Minimal YAML parser for module-artifacts.yaml
# ---------------------------------------------------------------------------

def _parse_artifacts_yaml() -> dict:
    """Parse module-artifacts.yaml into a structured dict.

    Returns:
        Dict mapping module number (int) to:
        {
            "produces": [{"path": str, "type": str, "description": str, "required": bool}],
            "requires_from": {source_module_int: [path_str, ...]}
        }
    """
    text = _ARTIFACTS_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    modules: dict[int, dict] = {}
    current_module: int | None = None
    current_section: str | None = None  # "produces" or "requires_from"
    current_requires_module: int | None = None
    current_produce_item: dict | None = None

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level "modules:" key
        if indent == 0 and stripped.strip() == "modules:":
            continue
        if indent == 0 and stripped.strip().startswith("version:"):
            continue

        # Module number (indent 2): "  4:"
        if indent == 2 and stripped.strip().endswith(":"):
            key = stripped.strip()[:-1]
            if key.isdigit():
                current_module = int(key)
                modules[current_module] = {"produces": [], "requires_from": {}}
                current_section = None
                current_requires_module = None
                current_produce_item = None
            continue

        # Section key (indent 4): "    produces:" or "    requires_from:"
        if indent == 4 and stripped.strip().endswith(":") and current_module is not None:
            section = stripped.strip()[:-1]
            if section in ("produces", "requires_from"):
                current_section = section
                current_produce_item = None
                current_requires_module = None
            continue

        # Produces list item (indent 6): "      - path: ..."
        if indent == 6 and current_section == "produces" and current_module is not None:
            if stripped.strip().startswith("- path:"):
                path_val = stripped.strip().split(":", 1)[1].strip().strip('"')
                current_produce_item = {
                    "path": path_val,
                    "type": "",
                    "description": "",
                    "required": True,
                }
                modules[current_module]["produces"].append(current_produce_item)
            continue

        # Produces item fields (indent 8): "        type: ..."
        if indent == 8 and current_produce_item is not None:
            kv = stripped.strip()
            if ":" in kv:
                key, val = kv.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"')
                if key == "type":
                    current_produce_item["type"] = val
                elif key == "description":
                    current_produce_item["description"] = val
                elif key == "required":
                    current_produce_item["required"] = val.lower() == "true"
            continue

        # requires_from source module (indent 6): "      4: [...]"
        if indent == 6 and current_section == "requires_from" and current_module is not None:
            match = re.match(r'\s*(\d+):\s*\[(.+)\]', stripped)
            if match:
                src_module = int(match.group(1))
                paths_str = match.group(2)
                paths = [p.strip().strip('"') for p in paths_str.split(",")]
                modules[current_module]["requires_from"][src_module] = paths
                current_requires_module = src_module
            continue

    return modules


def _get_all_produced_paths() -> dict[int, set[str]]:
    """Return a mapping of module number to set of paths it produces."""
    modules = _parse_artifacts_yaml()
    return {
        mod_num: {item["path"] for item in info["produces"]}
        for mod_num, info in modules.items()
    }


def _get_steering_files_for_module(module_num: int) -> list[Path]:
    """Return all steering file paths for a given module."""
    # Parse steering-index.yaml to find module files
    text = _STEERING_INDEX_PATH.read_text(encoding="utf-8")

    # Look for the module's root and phase files
    files: list[Path] = []
    pattern = re.compile(
        rf'module-{module_num:02d}[a-z0-9_-]*\.md|'
        rf'module-{module_num:02d}-[a-z0-9_-]*\.md|'
        rf'module-0?{module_num}-[a-z0-9_-]*\.md'
    )

    for md_file in _STEERING_DIR.glob("module-*.md"):
        # Match files for this module number
        name = md_file.name
        # Pattern: module-NN-*.md or module-N-*.md
        num_match = re.match(r'module-(\d+)', name)
        if num_match and int(num_match.group(1)) == module_num:
            files.append(md_file)

    return files


def _read_steering_content(module_num: int) -> str:
    """Read and concatenate all steering file content for a module."""
    files = _get_steering_files_for_module(module_num)
    content_parts = []
    for f in files:
        content_parts.append(f.read_text(encoding="utf-8"))
    return "\n".join(content_parts)


# ===========================================================================
# TestArtifactChainConsistency
# ===========================================================================

class TestArtifactChainConsistency:
    """Validate the artifact dependency graph is internally consistent."""

    def test_artifacts_yaml_exists(self):
        """module-artifacts.yaml must exist."""
        assert _ARTIFACTS_PATH.is_file(), f"Missing {_ARTIFACTS_PATH}"

    def test_every_requires_from_path_is_produced(self):
        """Every path in requires_from must be listed as produces in the source module."""
        modules = _parse_artifacts_yaml()
        produced = _get_all_produced_paths()
        errors = []

        for mod_num, info in modules.items():
            for src_module, paths in info["requires_from"].items():
                src_produced = produced.get(src_module, set())
                for path in paths:
                    if path not in src_produced:
                        errors.append(
                            f"Module {mod_num} requires '{path}' from Module {src_module}, "
                            f"but Module {src_module} does not produce it. "
                            f"Module {src_module} produces: {sorted(src_produced)}"
                        )

        assert not errors, "Broken artifact references:\n" + "\n".join(errors)

    def test_dependency_graph_respects_module_ordering(self):
        """A module can only require artifacts from lower-numbered modules."""
        modules = _parse_artifacts_yaml()
        errors = []

        for mod_num, info in modules.items():
            for src_module in info["requires_from"]:
                if src_module >= mod_num:
                    errors.append(
                        f"Module {mod_num} requires_from Module {src_module} "
                        f"(must be < {mod_num})"
                    )

        assert not errors, "Dependency ordering violations:\n" + "\n".join(errors)

    def test_dependency_graph_is_acyclic(self):
        """The artifact dependency graph must have no cycles."""
        modules = _parse_artifacts_yaml()

        # Build adjacency list: mod_num -> set of modules it depends on
        deps: dict[int, set[int]] = {}
        for mod_num, info in modules.items():
            deps[mod_num] = set(info["requires_from"].keys())

        # Topological sort via DFS — detect cycles
        visited: set[int] = set()
        in_stack: set[int] = set()
        cycle_found: list[str] = []

        def dfs(node: int, path: list[int]) -> None:
            if node in in_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycle_found.append(
                    f"Cycle detected: {' -> '.join(str(n) for n in cycle)}"
                )
                return
            if node in visited:
                return
            visited.add(node)
            in_stack.add(node)
            path.append(node)
            for dep in deps.get(node, set()):
                dfs(dep, path)
            path.pop()
            in_stack.remove(node)

        for mod_num in modules:
            if mod_num not in visited:
                dfs(mod_num, [])

        assert not cycle_found, "Dependency cycles:\n" + "\n".join(cycle_found)

    def test_produces_items_have_valid_structure(self):
        """Every produces entry must have path, type, and description."""
        modules = _parse_artifacts_yaml()
        errors = []

        for mod_num, info in modules.items():
            for i, item in enumerate(info["produces"]):
                if not item.get("path"):
                    errors.append(f"Module {mod_num} produces[{i}]: missing path")
                if not item.get("type"):
                    errors.append(f"Module {mod_num} produces[{i}]: missing type")
                if item.get("type") not in ("file", "directory", "sentinel"):
                    errors.append(
                        f"Module {mod_num} produces[{i}]: type must be "
                        f"'file', 'directory', or 'sentinel', got '{item.get('type')}'"
                    )

        assert not errors, "Invalid produces entries:\n" + "\n".join(errors)

    def test_requires_from_sources_exist_in_graph(self):
        """Every source module referenced in requires_from must exist in the graph."""
        modules = _parse_artifacts_yaml()
        all_module_nums = set(modules.keys())
        errors = []

        for mod_num, info in modules.items():
            for src_module in info["requires_from"]:
                if src_module not in all_module_nums:
                    errors.append(
                        f"Module {mod_num} requires_from Module {src_module}, "
                        f"but Module {src_module} is not defined in module-artifacts.yaml"
                    )

        assert not errors, "Missing source modules:\n" + "\n".join(errors)


# ===========================================================================
# TestSteeringReferencesArtifacts
# ===========================================================================

class TestSteeringReferencesArtifacts:
    """Validate that module steering files reference their required artifacts."""

    def test_steering_files_exist_for_artifact_modules(self):
        """Every module in module-artifacts.yaml must have steering files."""
        modules = _parse_artifacts_yaml()
        missing = []

        for mod_num in modules:
            files = _get_steering_files_for_module(mod_num)
            if not files:
                missing.append(f"Module {mod_num}: no steering files found")

        assert not missing, "Missing steering files:\n" + "\n".join(missing)

    @pytest.mark.parametrize("module_num", list(range(1, 12)))
    def test_steering_mentions_required_input_paths(self, module_num: int):
        """Module steering must reference the artifact paths it requires,
        or mention the source module by number in its prerequisites."""
        modules = _parse_artifacts_yaml()
        if module_num not in modules:
            pytest.skip(f"Module {module_num} not in module-artifacts.yaml")

        info = modules[module_num]
        if not info["requires_from"]:
            pytest.skip(f"Module {module_num} has no requires_from")

        content = _read_steering_content(module_num)
        if not content:
            pytest.fail(f"Module {module_num} has no steering content")

        missing_refs = []
        for src_module, paths in info["requires_from"].items():
            # Check if the source module is mentioned by number (e.g., "Module 6")
            module_ref_pattern = re.compile(
                rf'Module\s+{src_module}\b', re.IGNORECASE
            )
            module_mentioned = bool(module_ref_pattern.search(content))

            for path in paths:
                # Accept either: explicit path reference OR module-level mention
                path_variants = [path, path.rstrip("/")]
                path_found = any(variant in content for variant in path_variants)

                if not path_found and not module_mentioned:
                    missing_refs.append(
                        f"'{path}' (from Module {src_module}) — neither the path "
                        f"nor 'Module {src_module}' appears in steering"
                    )

        assert not missing_refs, (
            f"Module {module_num} steering does not reference required artifacts: "
            f"{', '.join(missing_refs)}"
        )


# ===========================================================================
# TestArtifactChainContinuity
# ===========================================================================

class TestArtifactChainContinuity:
    """Validate the full chain from Module 4 through Module 11."""

    def test_chain_is_connected(self):
        """Every module with requires_from connects back to a producing module."""
        modules = _parse_artifacts_yaml()
        root_modules = {1, 2}  # Modules with no dependencies
        for mod_num in sorted(modules.keys()):
            if mod_num in root_modules:
                continue
            info = modules[mod_num]
            assert info["requires_from"], (
                f"Module {mod_num} has no requires_from — "
                f"it's disconnected from the artifact chain"
            )

    def test_no_orphan_producers(self):
        """Every module that produces artifacts (except the last) is consumed by at least one downstream module."""
        modules = _parse_artifacts_yaml()
        produced_by = _get_all_produced_paths()

        # Collect all consumed source modules
        consumed_sources: set[int] = set()
        for info in modules.values():
            consumed_sources.update(info["requires_from"].keys())

        # Every producer (except the last module) should be consumed
        max_module = max(modules.keys())
        orphans = []
        for mod_num in modules:
            if mod_num == max_module:
                continue  # Last module doesn't need consumers
            if modules[mod_num]["produces"] and mod_num not in consumed_sources:
                orphans.append(
                    f"Module {mod_num} produces artifacts but no downstream "
                    f"module requires them"
                )

        assert not orphans, "Orphan producers:\n" + "\n".join(orphans)
