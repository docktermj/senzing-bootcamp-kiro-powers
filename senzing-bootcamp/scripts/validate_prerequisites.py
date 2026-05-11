#!/usr/bin/env python3
"""Validate module prerequisites alignment between the dependency graph
and steering file content.

Checks that:
- Every module number in requires/gates has a steering-index entry.
- Gate requirement keywords appear in source module steering content.
- Source modules with outgoing gates have checkpoints and success criteria.

Usage:
    python scripts/validate_prerequisites.py
    python scripts/validate_prerequisites.py --warnings-as-errors

Requires only the Python standard library (no PyYAML).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single validation finding."""

    level: str  # "ERROR" or "WARNING"
    description: str

    def format(self) -> str:
        """Format the finding as a printable line."""
        return f"{self.level}: {self.description}"


@dataclass
class ModuleInfo:
    """Parsed module entry from the dependency graph."""

    name: str
    requires: list[int]


@dataclass
class GateInfo:
    """Parsed gate entry from the dependency graph."""

    source: int
    destination: int
    requires: list[str]



# ---------------------------------------------------------------------------
# Core parsing functions
# ---------------------------------------------------------------------------


def parse_gate_key(key: str) -> tuple[int, int] | None:
    """Parse a gate key like '1->2' into (source, destination).

    Args:
        key: Gate key string in format "N->M".

    Returns:
        Tuple of (source_module, dest_module) or None if invalid format.
    """
    match = re.match(r"^(\d+)->(\d+)$", key.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def extract_keywords(requirement: str) -> list[str]:
    """Extract normalized keywords from a gate requirement string.

    Splits on commas, strips whitespace, lowercases each token.
    Filters out empty strings.

    Args:
        requirement: A gate requirement string like "SDK installed, DB configured".

    Returns:
        List of lowercase keyword tokens.
    """
    tokens = requirement.split(",")
    result = [t.strip().lower() for t in tokens]
    return [t for t in result if t]


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib only)
# ---------------------------------------------------------------------------


def _parse_yaml_value(value: str) -> str | int | list | None:
    """Parse a simple YAML scalar value.

    Args:
        value: Raw string value from YAML line.

    Returns:
        Parsed value as int, string, list, or None.
    """
    value = value.strip()
    if not value or value == "null" or value == "~":
        return None
    # Quoted string
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    # Inline list like [2, 5]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = [i.strip() for i in inner.split(",")]
        result: list = []
        for item in items:
            item = item.strip('"').strip("'")
            try:
                result.append(int(item))
            except ValueError:
                result.append(item)
        return result
    # Integer
    try:
        return int(value)
    except ValueError:
        pass
    return value


def _get_indent(line: str) -> int:
    """Return the number of leading spaces in a line."""
    return len(line) - len(line.lstrip())


def load_dependency_graph(path: Path) -> dict:
    """Load and parse the dependency graph YAML using a minimal parser.

    Extracts modules, gates, and tracks sections. Only parses the
    structure needed for prerequisite validation.

    Args:
        path: Path to module-dependencies.yaml.

    Returns:
        Dict with 'modules' (dict[int, ModuleInfo]) and
        'gates' (dict[str, GateInfo]) keys.

    Raises:
        SystemExit: If file is missing or unparseable.
    """
    if not path.exists():
        print(f"ERROR: Dependency graph not found: {path}")
        sys.exit(1)

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot read dependency graph: {exc}")
        sys.exit(1)

    lines = content.splitlines()
    modules: dict[int, ModuleInfo] = {}
    gates: dict[str, GateInfo] = {}

    section = None
    current_module_num: int | None = None
    current_module_name: str = ""
    current_module_requires: list[int] = []
    current_gate_key: str | None = None
    current_gate_requires: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = _get_indent(line)

        # Top-level sections
        if indent == 0 and stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1].strip()
            if key == "modules":
                section = "modules"
            elif key == "gates":
                section = "gates"
            elif key == "tracks":
                section = "tracks"
            else:
                section = None
            # Flush any pending module/gate
            if current_module_num is not None and section != "modules":
                modules[current_module_num] = ModuleInfo(
                    name=current_module_name,
                    requires=current_module_requires,
                )
                current_module_num = None
            if current_gate_key is not None and section != "gates":
                parsed = parse_gate_key(current_gate_key)
                if parsed:
                    gates[current_gate_key] = GateInfo(
                        source=parsed[0],
                        destination=parsed[1],
                        requires=current_gate_requires,
                    )
                current_gate_key = None
            continue

        if section == "modules":
            # Module number line: "  1:" or "  2:"
            if indent == 2 and stripped.endswith(":"):
                # Flush previous module
                if current_module_num is not None:
                    modules[current_module_num] = ModuleInfo(
                        name=current_module_name,
                        requires=current_module_requires,
                    )
                try:
                    current_module_num = int(stripped[:-1])
                except ValueError:
                    current_module_num = None
                current_module_name = ""
                current_module_requires = []
            elif indent >= 4 and current_module_num is not None:
                if ":" in stripped:
                    key, _, val = stripped.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if key == "name":
                        parsed_val = _parse_yaml_value(val)
                        current_module_name = str(parsed_val) if parsed_val else ""
                    elif key == "requires":
                        parsed_val = _parse_yaml_value(val)
                        if isinstance(parsed_val, list):
                            current_module_requires = [
                                int(x) for x in parsed_val
                                if isinstance(x, int)
                                or (isinstance(x, str) and x.isdigit())
                            ]
                        else:
                            current_module_requires = []

        elif section == "gates":
            # Gate key line: '  "1->2":' or '  1->2:'
            if indent == 2 and stripped.endswith(":"):
                # Flush previous gate
                if current_gate_key is not None:
                    parsed = parse_gate_key(current_gate_key)
                    if parsed:
                        gates[current_gate_key] = GateInfo(
                            source=parsed[0],
                            destination=parsed[1],
                            requires=current_gate_requires,
                        )
                gate_key_raw = stripped[:-1].strip().strip('"').strip("'")
                current_gate_key = gate_key_raw
                current_gate_requires = []
            elif indent >= 4 and current_gate_key is not None:
                # requires list items: '      - "SDK installed, ..."'
                if stripped.startswith("- "):
                    item = stripped[2:].strip().strip('"').strip("'")
                    current_gate_requires.append(item)

    # Flush final entries
    if current_module_num is not None:
        modules[current_module_num] = ModuleInfo(
            name=current_module_name,
            requires=current_module_requires,
        )
    if current_gate_key is not None:
        parsed = parse_gate_key(current_gate_key)
        if parsed:
            gates[current_gate_key] = GateInfo(
                source=parsed[0],
                destination=parsed[1],
                requires=current_gate_requires,
            )

    if not modules:
        print("ERROR: Cannot parse dependency graph: no modules found")
        sys.exit(1)

    return {"modules": modules, "gates": gates}


def load_steering_index(path: Path) -> dict[int, list[str]]:
    """Load steering-index.yaml and build module-to-files mapping.

    Handles both simple entries (e.g., `2: module-02-sdk-setup.md`) and
    multi-phase entries with root + phases containing file entries.

    Args:
        path: Path to steering-index.yaml.

    Returns:
        Dict mapping module number to list of steering file paths.

    Raises:
        SystemExit: If file is missing or unparseable.
    """
    if not path.exists():
        print(f"ERROR: Steering index not found: {path}")
        sys.exit(1)

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot read steering index: {exc}")
        sys.exit(1)

    lines = content.splitlines()
    module_files: dict[int, list[str]] = {}

    in_modules_section = False
    current_module: int | None = None
    current_files: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = _get_indent(line)

        # Top-level section detection
        if indent == 0 and stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1].strip()
            # Flush current module before leaving modules section
            if in_modules_section and current_module is not None:
                module_files[current_module] = current_files
                current_module = None
                current_files = []
            in_modules_section = key == "modules"
            continue

        if not in_modules_section:
            continue

        # Module number line at indent 2
        if indent == 2:
            # Flush previous module
            if current_module is not None:
                module_files[current_module] = current_files
                current_files = []

            if ":" in stripped:
                key_part, _, val_part = stripped.partition(":")
                key_part = key_part.strip()
                val_part = val_part.strip()
                try:
                    mod_num = int(key_part)
                except ValueError:
                    current_module = None
                    continue
                current_module = mod_num
                # Simple entry: "2: module-02-sdk-setup.md"
                if val_part and not val_part.startswith("#"):
                    current_files = [val_part.strip('"').strip("'")]
                else:
                    current_files = []
        elif indent >= 4 and current_module is not None:
            # Multi-phase entries
            if ":" in stripped:
                key_part, _, val_part = stripped.partition(":")
                key_part = key_part.strip()
                val_part = val_part.strip()
                if key_part == "root" and val_part:
                    file_val = val_part.strip('"').strip("'")
                    if file_val and file_val not in current_files:
                        current_files.insert(0, file_val)
                elif key_part == "file" and val_part:
                    file_val = val_part.strip('"').strip("'")
                    if file_val and file_val not in current_files:
                        current_files.append(file_val)

    # Flush final module
    if current_module is not None:
        module_files[current_module] = current_files

    if not module_files:
        print("ERROR: Cannot parse steering index: no modules found")
        sys.exit(1)

    return module_files



def load_steering_content(steering_dir: Path, files: list[str]) -> str:
    """Load and concatenate content from multiple steering files.

    Args:
        steering_dir: Path to the steering/ directory.
        files: List of filenames relative to steering_dir.

    Returns:
        Concatenated content of all files.
    """
    parts: list[str] = []
    for filename in files:
        filepath = steering_dir / filename
        if filepath.exists():
            try:
                parts.append(filepath.read_text(encoding="utf-8"))
            except OSError:
                pass
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def count_checkpoints(content: str) -> int:
    """Count checkpoint instructions in steering content.

    Matches the pattern '**Checkpoint:**' (case-insensitive).

    Args:
        content: Raw steering file content.

    Returns:
        Number of checkpoint instructions found.
    """
    return len(re.findall(r"\*\*Checkpoint:\*\*", content, re.IGNORECASE))


def has_success_criteria(content: str) -> bool:
    """Check if steering content contains success criteria.

    Looks for:
    - A heading containing 'Success Criteria' (any level)
    - Lines containing '✅' markers

    Args:
        content: Raw steering file content.

    Returns:
        True if success criteria section or markers are found.
    """
    # Check for heading with "Success Criteria"
    if re.search(r"^#+\s+.*Success Criteria", content, re.MULTILINE | re.IGNORECASE):
        return True
    # Check for ✅ markers
    if "✅" in content:
        return True
    return False


def _validate_module_references(
    modules: dict[int, ModuleInfo],
    gates: dict[str, GateInfo],
    steering_index: dict[int, list[str]],
) -> list[Finding]:
    """Verify each requires module number and gate src/dst exists in steering index.

    Args:
        modules: Parsed modules from dependency graph.
        gates: Parsed gates from dependency graph.
        steering_index: Module-to-files mapping from steering index.

    Returns:
        List of findings for missing references.
    """
    findings: list[Finding] = []

    # Check module requires references
    for mod_num, mod_info in modules.items():
        for req in mod_info.requires:
            if req not in steering_index:
                findings.append(Finding(
                    "ERROR",
                    f"Module {mod_num} requires module {req} which has no "
                    f"steering-index entry",
                ))

    # Check gate source/destination references
    for gate_key, gate_info in gates.items():
        if gate_info.source not in steering_index:
            findings.append(Finding(
                "ERROR",
                f"Gate '{gate_key}' source module {gate_info.source} has no "
                f"steering-index entry",
            ))
        if gate_info.destination not in steering_index:
            findings.append(Finding(
                "ERROR",
                f"Gate '{gate_key}' destination module {gate_info.destination} "
                f"has no steering-index entry",
            ))

    return findings


def _validate_keyword_presence(
    gates: dict[str, GateInfo],
    steering_index: dict[int, list[str]],
    steering_dir: Path,
) -> list[Finding]:
    """Check that gate requirement keywords appear in source module content.

    Args:
        gates: Parsed gates from dependency graph.
        steering_index: Module-to-files mapping.
        steering_dir: Path to steering directory.

    Returns:
        List of findings for missing keywords.
    """
    findings: list[Finding] = []

    for gate_key, gate_info in gates.items():
        source_files = steering_index.get(gate_info.source)
        if not source_files:
            continue

        content = load_steering_content(steering_dir, source_files)
        content_lower = content.lower()

        for req in gate_info.requires:
            keywords = extract_keywords(req)
            for keyword in keywords:
                if keyword not in content_lower:
                    findings.append(Finding(
                        "WARNING",
                        f"Gate '{gate_key}': keyword '{keyword}' not found "
                        f"in module {gate_info.source} steering content",
                    ))

    return findings


def _validate_checkpoint_coverage(
    gates: dict[str, GateInfo],
    steering_index: dict[int, list[str]],
    steering_dir: Path,
) -> list[Finding]:
    """Validate checkpoint and success criteria coverage for gate sources.

    Args:
        gates: Parsed gates from dependency graph.
        steering_index: Module-to-files mapping.
        steering_dir: Path to steering directory.

    Returns:
        List of findings for missing checkpoints/success criteria.
    """
    findings: list[Finding] = []

    # Collect unique source modules that have outgoing gates
    source_modules: set[int] = set()
    for gate_info in gates.values():
        source_modules.add(gate_info.source)

    for mod_num in sorted(source_modules):
        source_files = steering_index.get(mod_num)
        if not source_files:
            continue

        content = load_steering_content(steering_dir, source_files)

        checkpoint_count = count_checkpoints(content)
        if checkpoint_count == 0:
            findings.append(Finding(
                "ERROR",
                f"Module {mod_num} has outgoing gate(s) but zero "
                f"checkpoint instructions",
            ))

        if not has_success_criteria(content):
            findings.append(Finding(
                "WARNING",
                f"Module {mod_num} has outgoing gate(s) but no "
                f"success criteria section",
            ))

    return findings


# ---------------------------------------------------------------------------
# Orchestration and CLI
# ---------------------------------------------------------------------------


def validate_prerequisites(
    graph_path: Path,
    steering_index_path: Path,
    steering_dir: Path,
) -> list[Finding]:
    """Run all prerequisite validation checks.

    Args:
        graph_path: Path to module-dependencies.yaml.
        steering_index_path: Path to steering-index.yaml.
        steering_dir: Path to the steering/ directory.

    Returns:
        List of findings (errors and warnings).
    """
    graph = load_dependency_graph(graph_path)
    steering_index = load_steering_index(steering_index_path)

    modules: dict[int, ModuleInfo] = graph["modules"]
    gates: dict[str, GateInfo] = graph["gates"]

    findings: list[Finding] = []

    # Check module references against steering index
    findings.extend(_validate_module_references(modules, gates, steering_index))

    # Check keyword presence in steering content
    findings.extend(_validate_keyword_presence(gates, steering_index, steering_dir))

    # Check checkpoint coverage
    findings.extend(_validate_checkpoint_coverage(gates, steering_index, steering_dir))

    return findings


def main(argv: list[str] | None = None) -> None:
    """CLI entry point with argparse.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    repo_root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Validate module prerequisites against steering content.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors for exit code determination.",
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=repo_root / "config" / "module-dependencies.yaml",
        help="Path to module-dependencies.yaml.",
    )
    parser.add_argument(
        "--steering-index",
        type=Path,
        default=repo_root / "steering" / "steering-index.yaml",
        help="Path to steering-index.yaml.",
    )
    parser.add_argument(
        "--steering-dir",
        type=Path,
        default=repo_root / "steering",
        help="Path to steering directory.",
    )

    args = parser.parse_args(argv)

    findings = validate_prerequisites(
        args.graph,
        args.steering_index,
        args.steering_dir,
    )

    # Output findings
    for finding in findings:
        print(finding.format())

    error_count = sum(1 for f in findings if f.level == "ERROR")
    warning_count = sum(1 for f in findings if f.level == "WARNING")
    print(f"\nSummary: {error_count} error(s), {warning_count} warning(s)")

    # Determine exit code
    if error_count > 0:
        sys.exit(1)
    if args.warnings_as_errors and warning_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
