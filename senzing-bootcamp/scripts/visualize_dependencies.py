#!/usr/bin/env python3
"""Senzing Bootcamp - Module Dependency Visualization.

Generates text-based (ASCII) or Mermaid dependency graphs showing module
status and relationships.

Usage:
    python scripts/visualize_dependencies.py
    python scripts/visualize_dependencies.py --format text
    python scripts/visualize_dependencies.py --format mermaid
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML mini-parser (stdlib only, no PyYAML)
# ---------------------------------------------------------------------------

def _parse_yaml_modules(text: str) -> dict[int, dict]:
    """Parse module entries from module-dependencies.yaml.

    Returns dict mapping module number to {"name": str, "requires": list[int]}.
    """
    modules: dict[int, dict] = {}
    in_modules = False
    current_id: int | None = None

    for line in text.splitlines():
        # Detect top-level sections
        if re.match(r"^modules\s*:", line):
            in_modules = True
            continue
        if re.match(r"^[a-z]", line) and not line.startswith(" "):
            if in_modules:
                in_modules = False
            continue

        if not in_modules:
            continue

        # Module ID line: "  1:" or "  11:"
        id_match = re.match(r"^\s{2}(\d+)\s*:", line)
        if id_match:
            current_id = int(id_match.group(1))
            modules[current_id] = {"name": f"Module {current_id}", "requires": []}
            continue

        if current_id is None:
            continue

        # Name line: '    name: "Business Problem"'
        name_match = re.match(r'^\s+name\s*:\s*"([^"]+)"', line)
        if name_match:
            modules[current_id]["name"] = name_match.group(1)
            continue

        # Requires line: '    requires: [2, 5]' or '    requires: []'
        req_match = re.match(r"^\s+requires\s*:\s*\[([^\]]*)\]", line)
        if req_match:
            content = req_match.group(1).strip()
            if content:
                modules[current_id]["requires"] = [
                    int(x.strip()) for x in content.split(",") if x.strip()
                ]
            else:
                modules[current_id]["requires"] = []
            continue

    return modules


def _parse_yaml_tracks(text: str) -> dict[str, dict]:
    """Parse track entries from module-dependencies.yaml.

    Returns dict mapping track_key to {"name": str, "modules": list[int]}.
    """
    tracks: dict[str, dict] = {}
    in_tracks = False
    current_key: str | None = None

    for line in text.splitlines():
        if re.match(r"^tracks\s*:", line):
            in_tracks = True
            continue
        if re.match(r"^[a-z]", line) and not line.startswith(" ") and in_tracks:
            in_tracks = False
            continue

        if not in_tracks:
            continue

        # Track key line: "  quick_demo:"
        key_match = re.match(r"^\s{2}(\w+)\s*:", line)
        if key_match and not re.match(r"^\s{4}", line):
            current_key = key_match.group(1)
            tracks[current_key] = {"name": current_key, "modules": []}
            continue

        if current_key is None:
            continue

        # Name line
        name_match = re.match(r'^\s+name\s*:\s*"([^"]+)"', line)
        if name_match:
            tracks[current_key]["name"] = name_match.group(1)
            continue

        # Modules line: '    modules: [1, 2, 3]'
        mod_match = re.match(r"^\s+modules\s*:\s*\[([^\]]*)\]", line)
        if mod_match:
            content = mod_match.group(1).strip()
            if content:
                tracks[current_key]["modules"] = [
                    int(x.strip()) for x in content.split(",") if x.strip()
                ]
            continue

    return tracks


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _find_dependencies_yaml() -> Path | None:
    """Locate module-dependencies.yaml, checking multiple paths."""
    candidates = [
        Path("config") / "module-dependencies.yaml",
        Path("senzing-bootcamp") / "config" / "module-dependencies.yaml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_modules(yaml_path: Path | None = None) -> dict[int, dict]:
    """Load module dependency graph from YAML.

    Args:
        yaml_path: Explicit path to YAML file. If None, auto-detect.

    Returns:
        Dict mapping module number to {"name": str, "requires": list[int]}.
    """
    if yaml_path is None:
        yaml_path = _find_dependencies_yaml()
    if yaml_path is None or not yaml_path.is_file():
        # Fallback: hardcoded minimal graph
        return _default_modules()
    text = yaml_path.read_text(encoding="utf-8")
    modules = _parse_yaml_modules(text)
    return modules if modules else _default_modules()


def load_tracks(yaml_path: Path | None = None) -> dict[str, dict]:
    """Load track definitions from YAML.

    Args:
        yaml_path: Explicit path to YAML file. If None, auto-detect.

    Returns:
        Dict mapping track key to {"name": str, "modules": list[int]}.
    """
    if yaml_path is None:
        yaml_path = _find_dependencies_yaml()
    if yaml_path is None or not yaml_path.is_file():
        return {}
    text = yaml_path.read_text(encoding="utf-8")
    return _parse_yaml_tracks(text)


def _default_modules() -> dict[int, dict]:
    """Hardcoded fallback module graph."""
    return {
        1: {"name": "Business Problem", "requires": []},
        2: {"name": "SDK Setup", "requires": []},
        3: {"name": "System Verification", "requires": [2]},
        4: {"name": "Data Collection", "requires": [1]},
        5: {"name": "Data Quality & Mapping", "requires": [4]},
        6: {"name": "Load Data", "requires": [2, 5]},
        7: {"name": "Query & Visualize", "requires": [6]},
        8: {"name": "Performance", "requires": [7]},
        9: {"name": "Security", "requires": [8]},
        10: {"name": "Monitoring", "requires": [9]},
        11: {"name": "Deployment", "requires": [10]},
    }


def load_progress() -> dict:
    """Load bootcamp progress from JSON.

    Returns:
        Dict with "modules_completed" and "current_module" keys.
        If file is missing, returns empty progress (Module 1 & 2 available).
    """
    candidates = [
        Path("config") / "bootcamp_progress.json",
        Path("senzing-bootcamp") / "config" / "bootcamp_progress.json",
    ]
    for p in candidates:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return data
            except (json.JSONDecodeError, OSError):
                pass
    return {"modules_completed": [], "current_module": None}


def load_preferences() -> dict:
    """Load bootcamp preferences (track selection).

    Returns:
        Dict with optional "track" key.
    """
    candidates = [
        Path("config") / "bootcamp_preferences.yaml",
        Path("senzing-bootcamp") / "config" / "bootcamp_preferences.yaml",
    ]
    for p in candidates:
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8")
                # Simple extraction of track value
                m = re.search(r"track\s*:\s*[\"']?(\w+)[\"']?", text)
                if m:
                    return {"track": m.group(1)}
            except OSError:
                pass
    return {}


# ---------------------------------------------------------------------------
# Status determination
# ---------------------------------------------------------------------------

def get_module_status(
    module_num: int,
    modules: dict[int, dict],
    progress: dict,
) -> str:
    """Determine display status for a module.

    Args:
        module_num: The module number to check.
        modules: Full module dependency graph.
        progress: Progress dict with modules_completed and current_module.

    Returns:
        One of: "complete", "current", "available", "locked".
    """
    completed = progress.get("modules_completed", [])
    current = progress.get("current_module")

    if module_num in completed:
        return "complete"
    if current is not None and module_num == current:
        return "current"
    if _all_prerequisites_met(module_num, modules, completed):
        return "available"
    return "locked"


def _all_prerequisites_met(
    module_num: int,
    modules: dict[int, dict],
    completed: list[int],
) -> bool:
    """Check if all prerequisite modules are complete."""
    prereqs = modules.get(module_num, {}).get("requires", [])
    return all(p in completed for p in prereqs)


# ---------------------------------------------------------------------------
# Status emoji mapping
# ---------------------------------------------------------------------------

STATUS_EMOJI = {
    "complete": "✅",
    "current": "📍",
    "available": "🔓",
    "locked": "🔒",
}


# ---------------------------------------------------------------------------
# Text (ASCII) rendering
# ---------------------------------------------------------------------------

def render_text(
    modules: dict[int, dict],
    progress: dict,
    tracks: dict[str, dict] | None = None,
    preferences: dict | None = None,
) -> str:
    """Render ASCII dependency graph with box-drawing characters.

    Args:
        modules: Module dependency graph.
        progress: Progress data.
        tracks: Track definitions (optional).
        preferences: User preferences with track selection (optional).

    Returns:
        Multi-line string with the rendered graph.
    """
    lines: list[str] = []
    lines.append("")
    lines.append("Senzing Bootcamp — Module Dependency Graph")
    lines.append("══════════════════════════════════════════════")
    lines.append("")

    # Build the tree by rendering from entry points
    # Entry points are modules with no prerequisites
    entry_points = sorted(
        num for num, info in modules.items() if not info.get("requires")
    )

    # Build a "children" map: which modules depend on this one
    children: dict[int, list[int]] = {num: [] for num in modules}
    for num, info in modules.items():
        for req in info.get("requires", []):
            if req in children:
                children[req].append(num)
    # Sort children for deterministic output
    for k in children:
        children[k] = sorted(children[k])

    # Track which modules have been rendered to avoid duplicates
    rendered: set[int] = set()

    def _render_subtree(mod_num: int, prefix: str, is_last: bool, is_root: bool):
        """Recursively render a module and its dependents."""
        if mod_num in rendered:
            return
        rendered.add(mod_num)

        status = get_module_status(mod_num, modules, progress)
        emoji = STATUS_EMOJI[status]
        name = modules[mod_num]["name"]
        label = f"{emoji} Module {mod_num}: {name}"

        if is_root:
            lines.append(f"  {label}")
        else:
            connector = "└──→ " if is_last else "├──→ "
            lines.append(f"{prefix}{connector}{label}")

        # Render children
        kids = [c for c in children.get(mod_num, []) if c not in rendered]
        for i, child in enumerate(kids):
            child_is_last = (i == len(kids) - 1)
            if is_root:
                _render_subtree(child, "  ", child_is_last, False)
            else:
                extension = "     " if is_last else "│    "
                new_prefix = prefix + extension
                _render_subtree(child, new_prefix, child_is_last, False)

    for i, entry in enumerate(entry_points):
        _render_subtree(entry, "  ", True, True)
        # Add separator between entry point trees (except after last)
        if i < len(entry_points) - 1:
            lines.append("  │")

    # Render any remaining modules not reachable from entry points
    for num in sorted(modules.keys()):
        if num not in rendered:
            _render_subtree(num, "  ", True, True)

    lines.append("")
    lines.append("Legend: ✅ Complete  📍 Current  🔓 Available  🔒 Locked")

    # Track info
    if tracks and preferences:
        track_key = preferences.get("track")
        if track_key and track_key in tracks:
            track_info = tracks[track_key]
            track_modules = track_info.get("modules", [])
            completed = progress.get("modules_completed", [])
            done = sum(1 for m in track_modules if m in completed)
            total = len(track_modules)
            pct = done * 100 // total if total else 0
            track_name = track_info.get("name", track_key)
            lines.append("")
            lines.append(
                f"Track: {track_name} — {done}/{total} modules complete ({pct}%)"
            )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mermaid rendering
# ---------------------------------------------------------------------------

def render_mermaid(
    modules: dict[int, dict],
    progress: dict,
) -> str:
    """Render Mermaid flowchart TD syntax.

    Args:
        modules: Module dependency graph.
        progress: Progress data.

    Returns:
        Multi-line Mermaid diagram string.
    """
    lines: list[str] = []
    lines.append("flowchart TD")

    # Node definitions
    for num in sorted(modules.keys()):
        status = get_module_status(num, modules, progress)
        name = modules[num]["name"]
        lines.append(f"    M{num}[Module {num}: {name}]:::{status}")

    lines.append("")

    # Edge definitions
    for num in sorted(modules.keys()):
        for req in sorted(modules[num].get("requires", [])):
            lines.append(f"    M{req} --> M{num}")

    lines.append("")

    # Class definitions
    lines.append("    classDef complete fill:#2d6a4f,color:#fff")
    lines.append("    classDef current fill:#1d4ed8,color:#fff")
    lines.append("    classDef available fill:#6b7280,color:#fff")
    lines.append("    classDef locked fill:#374151,color:#9ca3af")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    """Entry point for the dependency visualization script.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Module Dependency Visualization"
    )
    parser.add_argument(
        "--format",
        choices=["text", "mermaid"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    modules = load_modules()
    progress = load_progress()
    tracks = load_tracks()
    preferences = load_preferences()

    if args.format == "mermaid":
        output = render_mermaid(modules, progress)
    else:
        output = render_text(modules, progress, tracks, preferences)

    print(output)


if __name__ == "__main__":
    main()
