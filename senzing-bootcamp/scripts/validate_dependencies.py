#!/usr/bin/env python3
"""Validate the module dependency graph for internal consistency and
cross-reference accuracy against steering files.

Usage:
    python scripts/validate_dependencies.py

Requires only the Python standard library + PyYAML.
"""

from __future__ import annotations

import glob
import re
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    """A single validation finding."""

    level: str  # "ERROR" or "WARNING"
    description: str

    def format(self) -> str:
        return f"{self.level}: {self.description}"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_dependency_graph(path: Path) -> dict:
    """Load and parse the YAML dependency graph.

    Exits with code 1 if the file is missing or unparseable.
    """
    if not path.exists():
        print(f"ERROR: Dependency graph not found: {path}")
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            graph = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        print(f"ERROR: Cannot parse dependency graph: {exc}")
        sys.exit(1)
    if graph is None:
        print("ERROR: Cannot parse dependency graph: file is empty")
        sys.exit(1)
    return graph


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def validate_schema(graph: dict) -> list[Violation]:
    """Verify the graph has all required sections and fields with correct types."""
    violations: list[Violation] = []

    # metadata
    metadata = graph.get("metadata")
    if metadata is None:
        violations.append(Violation("ERROR", "Missing required section: metadata"))
    elif not isinstance(metadata, dict):
        violations.append(Violation("ERROR", "Section 'metadata' must be a mapping"))
    else:
        if "version" not in metadata:
            violations.append(Violation("ERROR", "Missing required field: metadata.version"))
        elif not isinstance(metadata["version"], str):
            violations.append(Violation("ERROR", "Field metadata.version must be a string"))
        if "last_updated" not in metadata:
            violations.append(Violation("ERROR", "Missing required field: metadata.last_updated"))
        elif not isinstance(metadata["last_updated"], str):
            violations.append(Violation("ERROR", "Field metadata.last_updated must be a string"))

    # modules
    modules = graph.get("modules")
    if modules is None:
        violations.append(Violation("ERROR", "Missing required section: modules"))
    elif not isinstance(modules, dict):
        violations.append(Violation("ERROR", "Section 'modules' must be a mapping"))
    else:
        for mod_num, mod_data in modules.items():
            if not isinstance(mod_data, dict):
                violations.append(
                    Violation("ERROR", f"Module {mod_num} must be a mapping")
                )
                continue
            if "name" not in mod_data:
                violations.append(
                    Violation("ERROR", f"Missing required field: modules.{mod_num}.name")
                )
            elif not isinstance(mod_data["name"], str):
                violations.append(
                    Violation("ERROR", f"Field modules.{mod_num}.name must be a string")
                )
            if "requires" not in mod_data:
                violations.append(
                    Violation("ERROR", f"Missing required field: modules.{mod_num}.requires")
                )
            elif not isinstance(mod_data["requires"], list):
                violations.append(
                    Violation("ERROR", f"Field modules.{mod_num}.requires must be a list")
                )
            if "skip_if" not in mod_data:
                violations.append(
                    Violation("ERROR", f"Missing required field: modules.{mod_num}.skip_if")
                )
            elif mod_data["skip_if"] is not None and not isinstance(mod_data["skip_if"], str):
                violations.append(
                    Violation(
                        "ERROR",
                        f"Field modules.{mod_num}.skip_if must be a string or null",
                    )
                )

    # tracks
    tracks = graph.get("tracks")
    if tracks is None:
        violations.append(Violation("ERROR", "Missing required section: tracks"))
    elif not isinstance(tracks, dict):
        violations.append(Violation("ERROR", "Section 'tracks' must be a mapping"))
    else:
        for track_key, track_data in tracks.items():
            if not isinstance(track_data, dict):
                violations.append(
                    Violation("ERROR", f"Track '{track_key}' must be a mapping")
                )
                continue
            if "name" not in track_data:
                violations.append(
                    Violation("ERROR", f"Missing required field: tracks.{track_key}.name")
                )
            elif not isinstance(track_data["name"], str):
                violations.append(
                    Violation("ERROR", f"Field tracks.{track_key}.name must be a string")
                )
            if "description" not in track_data:
                violations.append(
                    Violation(
                        "ERROR",
                        f"Missing required field: tracks.{track_key}.description",
                    )
                )
            elif not isinstance(track_data["description"], str):
                violations.append(
                    Violation(
                        "ERROR",
                        f"Field tracks.{track_key}.description must be a string",
                    )
                )
            if "modules" not in track_data:
                violations.append(
                    Violation(
                        "ERROR",
                        f"Missing required field: tracks.{track_key}.modules",
                    )
                )
            elif not isinstance(track_data["modules"], list):
                violations.append(
                    Violation(
                        "ERROR",
                        f"Field tracks.{track_key}.modules must be a list",
                    )
                )

    # gates
    gates = graph.get("gates")
    if gates is None:
        violations.append(Violation("ERROR", "Missing required section: gates"))
    elif not isinstance(gates, dict):
        violations.append(Violation("ERROR", "Section 'gates' must be a mapping"))
    else:
        for gate_key, gate_data in gates.items():
            if not isinstance(gate_data, dict):
                violations.append(
                    Violation("ERROR", f"Gate '{gate_key}' must be a mapping")
                )
                continue
            if "requires" not in gate_data:
                violations.append(
                    Violation("ERROR", f"Missing required field: gates.{gate_key}.requires")
                )
            elif not isinstance(gate_data["requires"], list):
                violations.append(
                    Violation(
                        "ERROR",
                        f"Field gates.{gate_key}.requires must be a list",
                    )
                )

    return violations


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def validate_no_cycles(graph: dict) -> list[Violation]:
    """Verify the modules section forms a DAG using Kahn's algorithm."""
    violations: list[Violation] = []
    modules = graph.get("modules")
    if not isinstance(modules, dict):
        return violations

    # Build adjacency list and in-degree map
    in_degree: dict[int, int] = {}
    adjacency: dict[int, list[int]] = {}
    for mod_num in modules:
        in_degree.setdefault(mod_num, 0)
        adjacency.setdefault(mod_num, [])

    for mod_num, mod_data in modules.items():
        if not isinstance(mod_data, dict):
            continue
        requires = mod_data.get("requires", [])
        if not isinstance(requires, list):
            continue
        for req in requires:
            if req in modules:
                adjacency.setdefault(req, []).append(mod_num)
                in_degree[mod_num] = in_degree.get(mod_num, 0) + 1

    # Kahn's algorithm
    queue: deque[int] = deque()
    for node, degree in in_degree.items():
        if degree == 0:
            queue.append(node)

    visited_count = 0
    while queue:
        node = queue.popleft()
        visited_count += 1
        for neighbour in adjacency.get(node, []):
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    if visited_count < len(modules):
        # Identify cycle participants (nodes still with in_degree > 0)
        cycle_modules = sorted(
            mod for mod, deg in in_degree.items() if deg > 0
        )
        violations.append(
            Violation(
                "ERROR",
                f"Circular dependency detected among modules: {cycle_modules}",
            )
        )

    return violations


def validate_references(graph: dict) -> list[Violation]:
    """Verify all module numbers referenced elsewhere exist in the modules section."""
    violations: list[Violation] = []
    modules = graph.get("modules")
    if not isinstance(modules, dict):
        return violations

    valid_modules = set(modules.keys())

    # Check requires
    for mod_num, mod_data in modules.items():
        if not isinstance(mod_data, dict):
            continue
        requires = mod_data.get("requires", [])
        if not isinstance(requires, list):
            continue
        for req in requires:
            if req not in valid_modules:
                violations.append(
                    Violation(
                        "ERROR",
                        f"Dangling reference in modules.{mod_num}.requires: module {req} does not exist",
                    )
                )

    # Check tracks
    tracks = graph.get("tracks")
    if isinstance(tracks, dict):
        for track_key, track_data in tracks.items():
            if not isinstance(track_data, dict):
                continue
            track_modules = track_data.get("modules", [])
            if not isinstance(track_modules, list):
                continue
            for mod_ref in track_modules:
                if mod_ref not in valid_modules:
                    violations.append(
                        Violation(
                            "ERROR",
                            f"Dangling reference in tracks.{track_key}.modules: module {mod_ref} does not exist",
                        )
                    )

    # Check gates
    gates = graph.get("gates")
    if isinstance(gates, dict):
        gate_pattern = re.compile(r"^(\d+)->(\d+)$")
        for gate_key in gates:
            match = gate_pattern.match(str(gate_key))
            if match:
                src = int(match.group(1))
                dst = int(match.group(2))
                if src not in valid_modules:
                    violations.append(
                        Violation(
                            "ERROR",
                            f"Dangling reference in gates key '{gate_key}': module {src} does not exist",
                        )
                    )
                if dst not in valid_modules:
                    violations.append(
                        Violation(
                            "ERROR",
                            f"Dangling reference in gates key '{gate_key}': module {dst} does not exist",
                        )
                    )

    return violations


def validate_topological_order(graph: dict) -> list[Violation]:
    """Verify each track lists modules in an order consistent with prerequisites."""
    violations: list[Violation] = []
    modules = graph.get("modules")
    tracks = graph.get("tracks")
    if not isinstance(modules, dict) or not isinstance(tracks, dict):
        return violations

    for track_key, track_data in tracks.items():
        if not isinstance(track_data, dict):
            continue
        track_modules = track_data.get("modules", [])
        if not isinstance(track_modules, list):
            continue

        # Build position map for this track
        position: dict[int, int] = {}
        for idx, mod_num in enumerate(track_modules):
            position[mod_num] = idx

        # Check each module's prerequisites appear earlier in the track
        for mod_num in track_modules:
            mod_data = modules.get(mod_num)
            if not isinstance(mod_data, dict):
                continue
            requires = mod_data.get("requires", [])
            if not isinstance(requires, list):
                continue
            for req in requires:
                if req in position and position[req] >= position[mod_num]:
                    violations.append(
                        Violation(
                            "ERROR",
                            f"Track '{track_key}': module {mod_num} appears before its prerequisite {req}",
                        )
                    )

    return violations


# ---------------------------------------------------------------------------
# Cross-reference checks
# ---------------------------------------------------------------------------

def validate_steering_files(graph: dict, steering_dir: Path) -> list[Violation]:
    """Verify every module in the graph has a corresponding module-NN-*.md file."""
    violations: list[Violation] = []
    modules = graph.get("modules")
    if not isinstance(modules, dict):
        return violations

    for mod_num in modules:
        pattern = str(steering_dir / f"module-{int(mod_num):02d}-*.md")
        matches = glob.glob(pattern)
        if not matches:
            violations.append(
                Violation(
                    "ERROR",
                    f"No steering file found for module {mod_num} (expected {steering_dir}/module-{int(mod_num):02d}-*.md)",
                )
            )

    return violations


def validate_prerequisites_file(graph: dict, prereqs_path: Path) -> list[Violation]:
    """Parse module-prerequisites.md and verify its table matches the graph."""
    violations: list[Violation] = []
    modules = graph.get("modules")
    if not isinstance(modules, dict):
        return violations

    if not prereqs_path.exists():
        violations.append(
            Violation("WARNING", f"module-prerequisites.md not found at {prereqs_path}, skipping cross-reference check")
        )
        return violations

    try:
        content = prereqs_path.read_text(encoding="utf-8")
    except OSError as exc:
        violations.append(
            Violation("WARNING", f"Could not read {prereqs_path}: {exc}")
        )
        return violations

    # Parse the dependency table
    # Expected format: | N — Name | Requires | Skip if |
    table_pattern = re.compile(
        r"^\|\s*(\d+)\s*[—–-]\s*.+?\|\s*(.*?)\s*\|", re.MULTILINE
    )
    file_requires: dict[int, list[int]] = {}
    for match in table_pattern.finditer(content):
        mod_num = int(match.group(1))
        requires_text = match.group(2).strip()
        # Parse requires field
        req_list: list[int] = []
        if requires_text and requires_text.lower() not in ("none", "none (first technical module)", "—", "-"):
            # Extract module numbers from text like "Module 2", "Module 4, files in data/raw/"
            # or "Module 2 + Module 5, ..."
            mod_refs = re.findall(r"Module\s+(\d+)", requires_text)
            req_list = [int(m) for m in mod_refs]
        file_requires[mod_num] = sorted(req_list)

    # Compare with graph
    for mod_num, mod_data in modules.items():
        if not isinstance(mod_data, dict):
            continue
        graph_requires = sorted(mod_data.get("requires", []))
        file_reqs = file_requires.get(mod_num)
        if file_reqs is None:
            violations.append(
                Violation(
                    "ERROR",
                    f"Module {mod_num} exists in graph but not in prerequisites file table",
                )
            )
        elif file_reqs != graph_requires:
            violations.append(
                Violation(
                    "ERROR",
                    f"Module {mod_num} prerequisites mismatch: graph has {graph_requires}, file has {file_reqs}",
                )
            )

    return violations


def validate_onboarding_flow(graph: dict, onboarding_path: Path) -> list[Violation]:
    """Parse onboarding-flow.md and verify track definitions match the graph."""
    violations: list[Violation] = []
    tracks = graph.get("tracks")
    if not isinstance(tracks, dict):
        return violations

    if not onboarding_path.exists():
        violations.append(
            Violation("WARNING", f"onboarding-flow.md not found at {onboarding_path}, skipping cross-reference check")
        )
        return violations

    try:
        content = onboarding_path.read_text(encoding="utf-8")
    except OSError as exc:
        violations.append(
            Violation("WARNING", f"Could not read {onboarding_path}: {exc}")
        )
        return violations

    # Parse track definitions from the bullet list in section 5
    # New format: "- **Quick Demo** — Modules 2, 3." or "- **Core Bootcamp** *(recommended)* — ..."
    track_pattern = re.compile(
        r"\*\*(.+?)\*\*\s*(?:\*\([^)]*\)\*\s*)?[—–-]\s*(.+?)\.?\s*(?:\.|$)", re.MULTILINE
    )

    # Map display names to track keys for comparison
    display_to_key: dict[str, str] = {}
    for track_key, track_data in tracks.items():
        if isinstance(track_data, dict):
            display_to_key[track_data.get("name", "")] = track_key

    file_tracks: dict[str, list[int]] = {}
    for match in track_pattern.finditer(content):
        track_name = match.group(1).strip()
        modules_text = match.group(2).strip()
        # Only process if this matches a known track display name
        if track_name not in display_to_key:
            continue
        # Parse module numbers from "Modules 2, 3" or "Modules 1–11" or "Modules 1, 2, 3, 4, 5, 6, 7"
        if "–" in modules_text or "-" in modules_text:
            # Range format: "Modules 1–11"
            range_match = re.search(r"(\d+)\s*[–-]\s*(\d+)", modules_text)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                mod_list = list(range(start, end + 1))
            else:
                mod_nums = re.findall(r"(\d+)", modules_text)
                mod_list = [int(m) for m in mod_nums]
        else:
            mod_nums = re.findall(r"(\d+)", modules_text)
            mod_list = [int(m) for m in mod_nums]
        file_tracks[track_name] = mod_list

    # Compare with graph
    for track_key, track_data in tracks.items():
        if not isinstance(track_data, dict):
            continue
        track_name = track_data.get("name", "")
        graph_modules = track_data.get("modules", [])

        # Find matching track in file
        file_mods = file_tracks.get(track_name)
        if file_mods is None:
            violations.append(
                Violation(
                    "ERROR",
                    f"Track '{track_name}' exists in graph but not found in onboarding-flow.md",
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Legacy identifier detection
# ---------------------------------------------------------------------------

LEGACY_TRACK_IDENTIFIERS = {
    "fast_track", "complete_beginner", "full_production",
    "A", "B", "C", "D",
}

LEGACY_TRACK_PHRASES = [
    "Path A", "Path B", "Path C", "Path D",
    "Track A", "Track B", "Track C", "Track D",
]


def validate_no_legacy_identifiers(graph: dict, onboarding_path: Path) -> list[Violation]:
    """Detect legacy track identifiers in the Track_Registry and onboarding flow."""
    violations: list[Violation] = []

    # Check Track_Registry for legacy identifiers as track keys
    tracks = graph.get("tracks")
    if isinstance(tracks, dict):
        for track_key in tracks:
            if track_key in LEGACY_TRACK_IDENTIFIERS:
                violations.append(
                    Violation(
                        "ERROR",
                        f"Legacy track identifier '{track_key}' found in Track_Registry",
                    )
                )
            # Also check track names for legacy references
            track_data = tracks[track_key]
            if isinstance(track_data, dict):
                track_name = track_data.get("name", "")
                for phrase in LEGACY_TRACK_PHRASES:
                    if phrase in track_name:
                        violations.append(
                            Violation(
                                "ERROR",
                                f"Legacy track phrase '{phrase}' found in track name for '{track_key}'",
                            )
                        )

    # Check onboarding flow for legacy identifiers
    if onboarding_path.exists():
        try:
            content = onboarding_path.read_text(encoding="utf-8")
        except OSError:
            return violations

        # Check for standalone legacy single-letter identifiers as track references
        # Match patterns like "Track A", "Path B", or standalone A/B/C/D used as track refs
        for phrase in LEGACY_TRACK_PHRASES:
            if phrase in content:
                violations.append(
                    Violation(
                        "ERROR",
                        f"Legacy track phrase '{phrase}' found in onboarding-flow.md",
                    )
                )

        # Check for legacy snake_case identifiers
        for legacy_id in ("fast_track", "complete_beginner", "full_production"):
            pattern = re.compile(r"\b" + re.escape(legacy_id) + r"\b")
            if pattern.search(content):
                violations.append(
                    Violation(
                        "ERROR",
                        f"Legacy track identifier '{legacy_id}' found in onboarding-flow.md",
                    )
                )

        # Check for the old **[A-D]) pattern
        old_pattern = re.compile(r"\*\*[A-D]\)")
        if old_pattern.search(content):
            violations.append(
                Violation(
                    "ERROR",
                    "Legacy letter-label track pattern '**X)' found in onboarding-flow.md",
                )
            )

    return violations


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all_checks(
    graph_path: Path, steering_dir: Path
) -> tuple[list[Violation], int]:
    """Run all validation checks and return (violations, exit_code)."""
    graph = load_dependency_graph(graph_path)
    violations: list[Violation] = []

    violations.extend(validate_schema(graph))
    violations.extend(validate_no_cycles(graph))
    violations.extend(validate_references(graph))
    violations.extend(validate_topological_order(graph))
    violations.extend(validate_steering_files(graph, steering_dir))
    violations.extend(
        validate_prerequisites_file(
            graph, steering_dir / "module-prerequisites.md"
        )
    )
    violations.extend(
        validate_onboarding_flow(graph, steering_dir / "onboarding-flow.md")
    )
    violations.extend(
        validate_no_legacy_identifiers(graph, steering_dir / "onboarding-flow.md")
    )

    error_count = sum(1 for v in violations if v.level == "ERROR")
    warning_count = sum(1 for v in violations if v.level == "WARNING")
    exit_code = 1 if error_count > 0 else 0
    return violations, exit_code


def main() -> None:
    """CLI entry point."""
    # Determine paths relative to repository root
    repo_root = Path(__file__).resolve().parent.parent
    graph_path = repo_root / "config" / "module-dependencies.yaml"
    steering_dir = repo_root / "steering"

    violations, exit_code = run_all_checks(graph_path, steering_dir)

    for v in violations:
        print(v.format())

    error_count = sum(1 for v in violations if v.level == "ERROR")
    warning_count = sum(1 for v in violations if v.level == "WARNING")
    print(f"\nSummary: {error_count} error(s), {warning_count} warning(s)")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
