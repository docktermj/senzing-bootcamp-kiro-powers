#!/usr/bin/env python3
"""Generate a self-contained HTML progress dashboard.

Reads bootcamp progress, preferences, and module dependency data to produce
a single HTML file at docs/progress/dashboard.html. Uses Python 3.11+ stdlib
only — no imports from status.py or other project scripts.

Usage:
    python senzing-bootcamp/scripts/progress_dashboard.py
    python senzing-bootcamp/scripts/progress_dashboard.py --output /tmp/dash.html
    python senzing-bootcamp/scripts/progress_dashboard.py --help
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ProgressData:
    """Parsed progress file data."""

    current_module: int | None
    modules_completed: list[int]
    current_step: str | None
    language: str | None
    step_history: dict[str, dict]


@dataclass
class PreferencesData:
    """Parsed preferences file data."""

    language: str | None
    track: str | None
    database_type: str | None
    deployment_target: str | None


@dataclass
class ModuleInfo:
    """A single module from the dependency graph."""

    number: int
    name: str
    requires: list[int] = field(default_factory=list)


@dataclass
class GateInfo:
    """A gate transition requirement."""

    from_module: int
    to_module: int
    requirements: list[str] = field(default_factory=list)


@dataclass
class DependencyData:
    """Parsed dependency graph data."""

    modules: list[ModuleInfo] = field(default_factory=list)
    gates: list[GateInfo] = field(default_factory=list)


@dataclass
class Artifact:
    """An artifact produced during a module step."""

    module_number: int
    step_key: str
    reference: str


@dataclass
class NextStep:
    """A recommended next module with gate info."""

    module: ModuleInfo
    gate_requirements: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Minimal YAML Parser
# ---------------------------------------------------------------------------


def _parse_scalar(value: str) -> str | int | bool | None:
    """Parse a YAML scalar value into a Python type.

    Args:
        value: Raw string value from a YAML line (already stripped).

    Returns:
        Parsed Python value: None, bool, int, or str.
    """
    if value in ("null", "~", ""):
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def _parse_inline_list(text: str) -> list:
    """Parse an inline YAML list like [1, 2, 3] or ["a", "b"].

    Args:
        text: The bracketed list string including [ and ].

    Returns:
        List of parsed scalar values.
    """
    inner = text[1:-1].strip()
    if not inner:
        return []
    items: list = []
    for item in inner.split(","):
        items.append(_parse_scalar(item.strip()))
    return items


def _get_indent(line: str) -> int:
    """Return the number of leading spaces in a line.

    Args:
        line: A raw line string.

    Returns:
        Count of leading space characters.
    """
    return len(line) - len(line.lstrip(" "))


def _strip_inline_comment(value: str) -> str:
    """Remove an inline comment from a value string.

    Handles quoted strings by not stripping # inside quotes.

    Args:
        value: The value portion after the colon.

    Returns:
        Value with trailing inline comment removed.
    """
    if not value:
        return value
    # If value is quoted, don't strip comments inside quotes
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value
    # Find # that's not inside quotes
    in_quote: str | None = None
    for idx, ch in enumerate(value):
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
        elif ch == in_quote:
            in_quote = None
        elif ch == "#" and in_quote is None:
            return value[:idx].rstrip()
    return value


def parse_yaml(text: str) -> dict:
    """Parse a minimal YAML subset into a nested dict.

    Supports:
    - Scalar key: value pairs (strings, integers, null)
    - Lists with '- item' syntax
    - Nested mappings via indentation
    - Comments (lines starting with #)
    - Quoted strings and bare values
    - null keyword → None
    - Inline lists like [1, 2, 3]

    Args:
        text: YAML content as a string.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If YAML structure is unparseable.
    """
    lines = text.split("\n")

    # Validate: first non-blank, non-comment line must not be indented
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if _get_indent(line) > 0:
            raise ValueError(
                f"Line {idx + 1}: unexpected indentation at top level: "
                f"{line!r}"
            )
        break

    result, _ = _parse_mapping(lines, 0, 0)
    return result


def _parse_mapping(lines: list[str], start: int, min_indent: int) -> tuple[dict, int]:
    """Parse a YAML mapping (dict) at a given indentation level.

    Args:
        lines: All lines of the YAML text.
        start: Index of the first line to consider.
        min_indent: Minimum indentation level for keys in this mapping.

    Returns:
        Tuple of (parsed dict, next line index after this mapping).
    """
    result: dict = {}
    i = start
    mapping_indent: int | None = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comment-only lines
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        indent = _get_indent(line)

        # If indentation is less than our mapping level, we're done
        if indent < min_indent:
            break

        # Set the mapping indent from the first real line
        if mapping_indent is None:
            mapping_indent = indent

        # If indentation doesn't match our mapping level, we're done
        if indent < mapping_indent:
            break

        # If this is a list item at our level, we're done (parent handles it)
        if stripped.startswith("- "):
            break

        # Must be a key: value pair
        colon_idx = stripped.find(":")
        if colon_idx == -1:
            raise ValueError(
                f"Line {i + 1}: expected key-value pair, got: {stripped!r}"
            )

        key = stripped[:colon_idx].strip()
        # Remove quotes from key if present
        if (key.startswith('"') and key.endswith('"')) or (
            key.startswith("'") and key.endswith("'")
        ):
            key = key[1:-1]

        rest = stripped[colon_idx + 1:].strip()
        rest = _strip_inline_comment(rest)

        # Inline list like [1, 2, 3]
        if rest.startswith("[") and rest.endswith("]"):
            result[key] = _parse_inline_list(rest)
            i += 1
            continue

        # Inline empty dict
        if rest == "{}":
            result[key] = {}
            i += 1
            continue

        # Scalar value present on same line
        if rest:
            result[key] = _parse_scalar(rest)
            i += 1
            continue

        # No value on this line — look ahead for nested content
        i += 1
        next_i = _skip_blank_and_comments(lines, i)

        if next_i >= len(lines):
            result[key] = None
            i = next_i
            continue

        next_indent = _get_indent(lines[next_i])
        if next_indent <= indent:
            # No nested content — value is null
            result[key] = None
            continue

        next_stripped = lines[next_i].strip()

        if next_stripped.startswith("- ") or next_stripped == "-":
            # Nested list
            result[key], i = _parse_list(lines, next_i, next_indent)
        else:
            # Nested mapping
            result[key], i = _parse_mapping(lines, next_i, next_indent)

    return result, i


def _parse_list(lines: list[str], start: int, list_indent: int) -> tuple[list, int]:
    """Parse a YAML list starting at the given line index.

    Args:
        lines: All lines of the YAML text.
        start: Index of the first list item line.
        list_indent: Indentation level of the list items.

    Returns:
        Tuple of (parsed list, next line index after this list).
    """
    items: list = []
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        indent = _get_indent(line)

        # If indentation is less than list level, we're done
        if indent < list_indent:
            break

        # Must be a list item at our indent level
        if indent != list_indent or not (
            stripped.startswith("- ") or stripped == "-"
        ):
            break

        # Extract item content after "- "
        item_content = stripped[2:].strip() if stripped.startswith("- ") else ""
        item_content = _strip_inline_comment(item_content)

        if not item_content:
            # Empty item — could be a nested dict or just None
            i += 1
            next_i = _skip_blank_and_comments(lines, i)
            if next_i < len(lines):
                next_indent = _get_indent(lines[next_i])
                if next_indent > indent:
                    # Nested content under this list item
                    nested, i = _parse_mapping(lines, next_i, next_indent)
                    items.append(nested)
                else:
                    items.append(None)
                    i = next_i
            else:
                items.append(None)
                i = next_i
            continue

        # Check for inline list
        if item_content.startswith("[") and item_content.endswith("]"):
            items.append(_parse_inline_list(item_content))
            i += 1
            continue

        # Check if item has a colon (dict-like on same line as -)
        colon_idx = item_content.find(":")
        if colon_idx != -1 and not (
            item_content.startswith('"') or item_content.startswith("'")
        ):
            # It's a key: value starting on the dash line
            item_key = item_content[:colon_idx].strip()
            if (item_key.startswith('"') and item_key.endswith('"')) or (
                item_key.startswith("'") and item_key.endswith("'")
            ):
                item_key = item_key[1:-1]
            item_val_str = item_content[colon_idx + 1:].strip()
            item_val_str = _strip_inline_comment(item_val_str)

            item_dict: dict = {}
            if item_val_str.startswith("[") and item_val_str.endswith("]"):
                item_dict[item_key] = _parse_inline_list(item_val_str)
            elif item_val_str:
                item_dict[item_key] = _parse_scalar(item_val_str)
            else:
                # Value might be nested below
                i += 1
                next_i = _skip_blank_and_comments(lines, i)
                if next_i < len(lines):
                    next_indent = _get_indent(lines[next_i])
                    # Content indented deeper than the dash
                    if next_indent > indent + 2:
                        nested_val, i = _parse_mapping(
                            lines, next_i, next_indent
                        )
                        item_dict[item_key] = nested_val
                    else:
                        item_dict[item_key] = None
                        i = next_i
                else:
                    item_dict[item_key] = None
                    i = next_i

                # Check for more keys at the same level as item_key
                while i < len(lines):
                    sub_line = lines[i]
                    sub_stripped = sub_line.strip()
                    if sub_stripped == "" or sub_stripped.startswith("#"):
                        i += 1
                        continue
                    sub_indent = _get_indent(sub_line)
                    # Keys belonging to this list item dict are indented
                    # deeper than the dash
                    if sub_indent <= indent:
                        break
                    if sub_stripped.startswith("- "):
                        break
                    sub_colon = sub_stripped.find(":")
                    if sub_colon == -1:
                        break
                    sub_key = sub_stripped[:sub_colon].strip()
                    sub_val = sub_stripped[sub_colon + 1:].strip()
                    sub_val = _strip_inline_comment(sub_val)
                    if sub_val.startswith("[") and sub_val.endswith("]"):
                        item_dict[sub_key] = _parse_inline_list(sub_val)
                    elif sub_val:
                        item_dict[sub_key] = _parse_scalar(sub_val)
                    else:
                        item_dict[sub_key] = None
                    i += 1
                items.append(item_dict)
                continue

            i += 1
            # Check for more keys belonging to this list item dict
            while i < len(lines):
                sub_line = lines[i]
                sub_stripped = sub_line.strip()
                if sub_stripped == "" or sub_stripped.startswith("#"):
                    i += 1
                    continue
                sub_indent = _get_indent(sub_line)
                if sub_indent <= indent:
                    break
                if sub_stripped.startswith("- "):
                    break
                sub_colon = sub_stripped.find(":")
                if sub_colon == -1:
                    break
                sub_key = sub_stripped[:sub_colon].strip()
                sub_val = sub_stripped[sub_colon + 1:].strip()
                sub_val = _strip_inline_comment(sub_val)
                if sub_val.startswith("[") and sub_val.endswith("]"):
                    item_dict[sub_key] = _parse_inline_list(sub_val)
                elif sub_val:
                    item_dict[sub_key] = _parse_scalar(sub_val)
                else:
                    item_dict[sub_key] = None
                i += 1
            items.append(item_dict)
        else:
            # Simple scalar list item
            items.append(_parse_scalar(item_content))
            i += 1

    return items, i


def _skip_blank_and_comments(lines: list[str], start: int) -> int:
    """Skip blank lines and comment lines starting from a given index.

    Args:
        lines: All lines of the YAML text.
        start: Index to start skipping from.

    Returns:
        Index of the first non-blank, non-comment line (or len(lines)).
    """
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        break
    return i


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_progress(path: Path) -> ProgressData:
    """Parse the progress JSON file.

    Args:
        path: Path to bootcamp_progress.json.

    Returns:
        ProgressData with extracted fields.

    Raises:
        SystemExit: If JSON is invalid (exits with code 1).
    """
    text = path.read_text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    return ProgressData(
        current_module=data.get("current_module"),
        modules_completed=data.get("modules_completed", []),
        current_step=data.get("current_step"),
        language=data.get("language"),
        step_history=data.get("step_history", {}),
    )


def parse_preferences(path: Path) -> PreferencesData:
    """Parse the preferences YAML file using the minimal parser.

    Args:
        path: Path to bootcamp_preferences.yaml.

    Returns:
        PreferencesData with extracted fields (None for missing/null values).
    """
    text = path.read_text()
    data = parse_yaml(text)

    return PreferencesData(
        language=data.get("language"),
        track=data.get("track"),
        database_type=data.get("database_type"),
        deployment_target=data.get("deployment_target"),
    )


def parse_dependencies(path: Path) -> DependencyData:
    """Parse the module dependencies YAML file.

    Args:
        path: Path to module-dependencies.yaml.

    Returns:
        DependencyData with modules and gates extracted.
    """
    text = path.read_text()
    data = parse_yaml(text)

    modules: list[ModuleInfo] = []
    modules_section = data.get("modules", {})
    if isinstance(modules_section, dict):
        for key, value in modules_section.items():
            number = int(key)
            name = value.get("name", "") if isinstance(value, dict) else ""
            requires_raw = value.get("requires", []) if isinstance(value, dict) else []
            requires = [int(r) for r in requires_raw] if requires_raw else []
            modules.append(ModuleInfo(number=number, name=name, requires=requires))

    gates: list[GateInfo] = []
    gates_section = data.get("gates", {})
    if isinstance(gates_section, dict):
        for key, value in gates_section.items():
            parts = str(key).split("->")
            from_module = int(parts[0])
            to_module = int(parts[1])
            requirements_raw = value.get("requires", []) if isinstance(value, dict) else []
            requirements = [str(r) for r in requirements_raw] if requirements_raw else []
            gates.append(
                GateInfo(
                    from_module=from_module,
                    to_module=to_module,
                    requirements=requirements,
                )
            )

    return DependencyData(modules=modules, gates=gates)


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------


def compute_module_statuses(
    dependency_data: DependencyData,
    progress: ProgressData,
) -> dict[int, str]:
    """Compute status for each module: 'completed', 'in-progress', or 'not-started'.

    Args:
        dependency_data: Parsed dependency graph.
        progress: Parsed progress data.

    Returns:
        Dict mapping module number to status string.
    """
    statuses: dict[int, str] = {}
    for module in dependency_data.modules:
        if module.number in progress.modules_completed:
            statuses[module.number] = "completed"
        elif (
            module.number == progress.current_module
            and module.number not in progress.modules_completed
        ):
            statuses[module.number] = "in-progress"
        else:
            statuses[module.number] = "not-started"
    return statuses


def extract_artifacts(progress: ProgressData) -> list[Artifact]:
    """Extract artifact references from step_history.

    Scans step_history entries for values that reference file paths
    or output artifacts, grouping them by module number.

    Args:
        progress: Parsed progress data.

    Returns:
        List of Artifact objects sorted by module number.
    """
    artifacts: list[Artifact] = []
    for step_key, entry in progress.step_history.items():
        if not isinstance(entry, dict):
            continue
        artifact_ref = entry.get("artifact")
        if artifact_ref is None:
            continue
        # Module number is the prefix before the dot in the step key
        dot_idx = step_key.find(".")
        if dot_idx == -1:
            continue
        try:
            module_number = int(step_key[:dot_idx])
        except ValueError:
            continue
        artifacts.append(
            Artifact(
                module_number=module_number,
                step_key=step_key,
                reference=str(artifact_ref),
            )
        )
    artifacts.sort(key=lambda a: a.module_number)
    return artifacts


def compute_next_steps(
    dependency_data: DependencyData,
    progress: ProgressData,
) -> list[NextStep]:
    """Compute dependency-aware next steps.

    A module is a valid next step if:
    1. All entries in its `requires` array are in `modules_completed`
    2. It is not in `modules_completed`
    3. It is not the `current_module`

    Args:
        dependency_data: Parsed dependency graph.
        progress: Parsed progress data.

    Returns:
        List of NextStep recommendations with gate requirements.
    """
    completed_set = set(progress.modules_completed)
    next_steps: list[NextStep] = []

    for module in dependency_data.modules:
        # Skip completed modules
        if module.number in completed_set:
            continue
        # Skip the current in-progress module
        if module.number == progress.current_module:
            continue
        # Check all prerequisites are satisfied
        if all(req in completed_set for req in module.requires):
            # Gather gate requirements for this module
            gate_reqs: list[str] = []
            for gate in dependency_data.gates:
                if gate.to_module == module.number:
                    gate_reqs.extend(gate.requirements)
            next_steps.append(NextStep(module=module, gate_requirements=gate_reqs))

    return next_steps


# ---------------------------------------------------------------------------
# HTML Renderer
# ---------------------------------------------------------------------------


def render_dashboard(
    progress: ProgressData,
    preferences: PreferencesData,
    dependency_data: DependencyData,
    module_statuses: dict[int, str],
    next_steps: list[NextStep],
    artifacts: list[Artifact],
) -> str:
    """Render the complete self-contained HTML dashboard.

    Produces valid HTML5 with all CSS inline in a <style> element.
    No external resources are referenced.

    Args:
        progress: Parsed progress data.
        preferences: Parsed preferences data.
        dependency_data: Parsed dependency graph.
        module_statuses: Module number → status mapping.
        next_steps: Computed next step recommendations.
        artifacts: Extracted artifacts list.

    Returns:
        Complete HTML string ready to write to file.
    """
    completed_count = sum(
        1 for status in module_statuses.values() if status == "completed"
    )
    total_count = len(module_statuses)

    # Build module list HTML
    module_items = ""
    for module in dependency_data.modules:
        status = module_statuses.get(module.number, "not-started")
        if status == "completed":
            indicator = "✓"
            css_class = "completed"
        elif status == "in-progress":
            indicator = "●"
            css_class = "in-progress"
        else:
            indicator = "○"
            css_class = "not-started"
        module_items += (
            f'      <li class="module-item {css_class}">'
            f'<span class="indicator">{indicator}</span> '
            f"Module {module.number}: {module.name}</li>\n"
        )

    # Build preferences card HTML
    pref_language = preferences.language if preferences.language is not None else "Not set"
    pref_track = preferences.track if preferences.track is not None else "Not set"
    pref_database_type = (
        preferences.database_type if preferences.database_type is not None else "Not set"
    )
    pref_deployment_target = (
        preferences.deployment_target
        if preferences.deployment_target is not None
        else "Not set"
    )

    # Build artifacts HTML grouped by module
    if artifacts:
        # Group artifacts by module number
        artifacts_by_module: dict[int, list[Artifact]] = {}
        for artifact in artifacts:
            artifacts_by_module.setdefault(artifact.module_number, []).append(artifact)

        artifacts_html = ""
        for mod_num in sorted(artifacts_by_module.keys()):
            mod_artifacts = artifacts_by_module[mod_num]
            # Find module name
            mod_name = ""
            for mod in dependency_data.modules:
                if mod.number == mod_num:
                    mod_name = mod.name
                    break
            artifacts_html += (
                f'      <div class="artifact-group">\n'
                f"        <h3>Module {mod_num}: {mod_name}</h3>\n"
                f"        <ul>\n"
            )
            for art in mod_artifacts:
                artifacts_html += f"          <li>{art.reference}</li>\n"
            artifacts_html += "        </ul>\n      </div>\n"
    else:
        artifacts_html = '      <p class="empty-message">No artifacts produced yet</p>\n'

    # Build next steps HTML
    all_completed = completed_count == total_count and total_count > 0
    if all_completed:
        next_steps_html = (
            '      <p class="completion-message">'
            "Congratulations! All modules completed.</p>\n"
        )
    elif next_steps:
        next_steps_html = '      <ul class="next-steps-list">\n'
        for step in next_steps:
            next_steps_html += (
                f"        <li><strong>Module {step.module.number}: "
                f"{step.module.name}</strong>"
            )
            if step.gate_requirements:
                reqs_text = "; ".join(step.gate_requirements)
                next_steps_html += (
                    f'<br><span class="gate-requirements">'
                    f"Gate requirements: {reqs_text}</span>"
                )
            next_steps_html += "</li>\n"
        next_steps_html += "      </ul>\n"
    else:
        next_steps_html = (
            '      <p class="blocking-message">'
            "No next steps available. Complete prerequisite modules to unlock "
            "further progress.</p>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bootcamp Progress Dashboard</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.6;
      color: #333;
      background: #f5f7fa;
      padding: 2rem;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 1.5rem;
      color: #1a1a2e;
    }}
    .section {{
      background: #fff;
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    .section h2 {{
      font-size: 1.2rem;
      margin-bottom: 1rem;
      color: #2d3748;
    }}
    .progress-summary {{
      font-size: 1.1rem;
      color: #4a5568;
    }}
    .module-list {{
      list-style: none;
    }}
    .module-item {{
      padding: 0.5rem 0;
      border-bottom: 1px solid #edf2f7;
    }}
    .module-item:last-child {{
      border-bottom: none;
    }}
    .indicator {{
      display: inline-block;
      width: 1.5rem;
      text-align: center;
      font-weight: bold;
    }}
    .completed .indicator {{
      color: #38a169;
    }}
    .in-progress .indicator {{
      color: #d69e2e;
    }}
    .not-started .indicator {{
      color: #a0aec0;
    }}
    .preferences-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
    }}
    .pref-item {{
      padding: 0.5rem;
      background: #f7fafc;
      border-radius: 4px;
    }}
    .pref-label {{
      font-size: 0.85rem;
      color: #718096;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .pref-value {{
      font-size: 1rem;
      color: #2d3748;
      font-weight: 500;
    }}
    .artifact-group {{
      margin-bottom: 1rem;
    }}
    .artifact-group:last-child {{
      margin-bottom: 0;
    }}
    .artifact-group h3 {{
      font-size: 1rem;
      color: #4a5568;
      margin-bottom: 0.5rem;
    }}
    .artifact-group ul {{
      list-style: disc;
      padding-left: 1.5rem;
    }}
    .artifact-group li {{
      padding: 0.25rem 0;
      color: #2d3748;
    }}
    .empty-message {{
      color: #718096;
      font-style: italic;
    }}
    .next-steps-list {{
      list-style: none;
    }}
    .next-steps-list li {{
      padding: 0.75rem 0;
      border-bottom: 1px solid #edf2f7;
    }}
    .next-steps-list li:last-child {{
      border-bottom: none;
    }}
    .gate-requirements {{
      font-size: 0.9rem;
      color: #718096;
    }}
    .completion-message {{
      color: #38a169;
      font-weight: 600;
      font-size: 1.1rem;
    }}
    .blocking-message {{
      color: #e53e3e;
      font-style: italic;
    }}
  </style>
</head>
<body>
  <h1>Bootcamp Progress Dashboard</h1>
  <div class="section">
    <h2>Progress Summary</h2>
    <p class="progress-summary">{completed_count} / {total_count} modules completed</p>
  </div>
  <div class="section">
    <h2>Modules</h2>
    <ul class="module-list">
{module_items}    </ul>
  </div>
  <div class="section">
    <h2>Preferences</h2>
    <div class="preferences-grid">
      <div class="pref-item">
        <div class="pref-label">Language</div>
        <div class="pref-value">{pref_language}</div>
      </div>
      <div class="pref-item">
        <div class="pref-label">Track</div>
        <div class="pref-value">{pref_track}</div>
      </div>
      <div class="pref-item">
        <div class="pref-label">Database Type</div>
        <div class="pref-value">{pref_database_type}</div>
      </div>
      <div class="pref-item">
        <div class="pref-label">Deployment Target</div>
        <div class="pref-value">{pref_deployment_target}</div>
      </div>
    </div>
  </div>
  <div class="section">
    <h2>Artifacts</h2>
{artifacts_html}  </div>
  <div class="section">
    <h2>Next Steps</h2>
{next_steps_html}  </div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Entry point with argparse CLI.

    Args:
        argv: Command-line arguments (None for sys.argv).
    """
    script_parent = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML progress dashboard."
    )
    parser.add_argument(
        "--progress",
        metavar="PATH",
        default=str(script_parent / "config" / "bootcamp_progress.json"),
        help=(
            "Path to bootcamp_progress.json "
            "(default: config/bootcamp_progress.json)"
        ),
    )
    parser.add_argument(
        "--preferences",
        metavar="PATH",
        default=str(script_parent / "config" / "bootcamp_preferences.yaml"),
        help=(
            "Path to bootcamp_preferences.yaml "
            "(default: config/bootcamp_preferences.yaml)"
        ),
    )
    parser.add_argument(
        "--dependencies",
        metavar="PATH",
        default=str(script_parent / "config" / "module-dependencies.yaml"),
        help=(
            "Path to module-dependencies.yaml "
            "(default: config/module-dependencies.yaml)"
        ),
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        default=str(script_parent / "docs" / "progress" / "dashboard.html"),
        help=(
            "Output path for dashboard HTML "
            "(default: docs/progress/dashboard.html)"
        ),
    )

    args = parser.parse_args(argv)

    # Validate input files exist
    for path_str in (args.progress, args.preferences, args.dependencies):
        p = Path(path_str)
        if not p.is_file():
            print(f"Error: file not found: {p}", file=sys.stderr)
            sys.exit(1)

    # Parse input files
    progress = parse_progress(Path(args.progress))
    preferences = parse_preferences(Path(args.preferences))
    dependency_data = parse_dependencies(Path(args.dependencies))

    # Compute derived state
    module_statuses = compute_module_statuses(dependency_data, progress)
    next_steps = compute_next_steps(dependency_data, progress)
    artifacts = extract_artifacts(progress)

    # Render HTML dashboard
    html = render_dashboard(
        progress=progress,
        preferences=preferences,
        dependency_data=dependency_data,
        module_statuses=module_statuses,
        next_steps=next_steps,
        artifacts=artifacts,
    )

    # Create output directory and write HTML
    output_path = Path(args.output)
    os.makedirs(output_path.parent, exist_ok=True)
    output_path.write_text(html)


if __name__ == "__main__":
    main()
