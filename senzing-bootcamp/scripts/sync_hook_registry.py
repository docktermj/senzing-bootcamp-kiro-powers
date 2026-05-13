#!/usr/bin/env python3
"""Generate hook-registry.md from .kiro.hook JSON files.

This script makes the .kiro.hook files the single source of truth for the
hook registry.  It reads every ``*.kiro.hook`` file under the hooks directory,
categorises each hook using ``hook-categories.yaml``, and produces a
deterministic Markdown registry.

Modes
-----
--write   (default) Overwrite the registry file on disk.
--verify  Compare the generated content against the existing file and exit
          with code 0 (match) or 1 (differ / missing).

Only Python standard-library modules are used.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Default paths (relative to the repository root)
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
REGISTRY_PATH = Path("senzing-bootcamp/steering/hook-registry.md")
CATEGORIES_PATH = Path("senzing-bootcamp/hooks/hook-categories.yaml")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class HookEntry:
    """Parsed representation of a single ``.kiro.hook`` file."""

    hook_id: str
    name: str
    description: str
    event_type: str
    action_type: str
    prompt: Optional[str] = None
    file_patterns: Optional[str] = None
    tool_types: Optional[str] = None


@dataclass
class CategoryMapping:
    """Maps a hook ID to its category and optional module number."""

    hook_id: str
    category: str  # "critical" or "module"
    module_number: Optional[int] = None


# ---------------------------------------------------------------------------
# Hook file discovery & parsing
# ---------------------------------------------------------------------------


def discover_hook_files(hooks_dir: Path) -> list[Path]:
    """Return all ``*.kiro.hook`` file paths in *hooks_dir*, sorted by name."""
    return sorted(hooks_dir.glob("*.kiro.hook"))


def parse_hook_file(hook_path: Path) -> HookEntry:
    """Parse a single ``.kiro.hook`` JSON file into a :class:`HookEntry`.

    Raises
    ------
    ValueError
        If the file contains invalid JSON or is missing required fields.
    """
    try:
        data = json.loads(hook_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{hook_path.name}: invalid JSON — {exc}") from exc

    # Required top-level fields
    for field in ("name", "description"):
        if field not in data:
            raise ValueError(f"{hook_path.name}: missing required field '{field}'")

    when = data.get("when", {})
    then = data.get("then", {})

    if "type" not in when:
        raise ValueError(f"{hook_path.name}: missing required field 'when.type'")
    if "type" not in then:
        raise ValueError(f"{hook_path.name}: missing required field 'then.type'")

    # Optional fields
    prompt = then.get("prompt")

    # File patterns: stored as array in JSON, join with ", " for display
    raw_patterns = when.get("patterns")
    file_patterns: Optional[str] = None
    if raw_patterns is not None:
        if isinstance(raw_patterns, list):
            file_patterns = ", ".join(raw_patterns)
        else:
            file_patterns = str(raw_patterns)

    # Tool types: stored as array in JSON, join with ", " for display
    raw_tool_types = when.get("toolTypes")
    tool_types: Optional[str] = None
    if raw_tool_types is not None:
        if isinstance(raw_tool_types, list):
            tool_types = ", ".join(raw_tool_types)
        else:
            tool_types = str(raw_tool_types)

    hook_id = hook_path.stem  # e.g. "ask-bootcamper.kiro" → need to strip ".kiro"
    # The filename is like "ask-bootcamper.kiro.hook", stem gives "ask-bootcamper.kiro"
    # We need just "ask-bootcamper"
    if hook_id.endswith(".kiro"):
        hook_id = hook_id[: -len(".kiro")]

    return HookEntry(
        hook_id=hook_id,
        name=data["name"],
        description=data["description"],
        event_type=when["type"],
        action_type=then["type"],
        prompt=prompt,
        file_patterns=file_patterns,
        tool_types=tool_types,
    )


def parse_all_hooks(hooks_dir: Path) -> tuple[list[HookEntry], list[str]]:
    """Parse every hook file in *hooks_dir*.

    Returns
    -------
    tuple[list[HookEntry], list[str]]
        A pair of (successfully parsed entries, error messages for failures).
    """
    entries: list[HookEntry] = []
    errors: list[str] = []
    for path in discover_hook_files(hooks_dir):
        try:
            entries.append(parse_hook_file(path))
        except ValueError as exc:
            errors.append(str(exc))
    return entries, errors


# ---------------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------------


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for the hook-categories.yaml format.

    Supports only the subset needed:
    - Top-level keys ending with ':'
    - List items starting with '- '
    - Nested dict keys (indented, ending with ':')

    No third-party YAML library required.
    """
    result: dict = {}
    current_key: Optional[str] = None
    current_sub_key: Optional[str] = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.lstrip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)

        if indent == 0 and stripped.endswith(":"):
            # Top-level key
            current_key = stripped[:-1].strip()
            current_sub_key = None
            if current_key not in result:
                result[current_key] = None
        elif indent > 0 and stripped.startswith("- "):
            # List item
            value = stripped[2:].strip()
            if current_sub_key is not None and current_key is not None:
                if result[current_key] is None:
                    result[current_key] = {}
                if current_sub_key not in result[current_key]:
                    result[current_key][current_sub_key] = []
                result[current_key][current_sub_key].append(value)
            elif current_key is not None:
                if result[current_key] is None:
                    result[current_key] = []
                result[current_key].append(value)
        elif indent > 0 and stripped.endswith(":"):
            # Sub-key (e.g. module number)
            current_sub_key = stripped[:-1].strip()
        # else: ignore unrecognised lines

    return result


def load_category_mapping(config_path: Path) -> dict[str, CategoryMapping]:
    """Load ``hook-categories.yaml`` and return a mapping of hook_id → CategoryMapping."""
    text = config_path.read_text(encoding="utf-8")
    data = _parse_simple_yaml(text)

    mapping: dict[str, CategoryMapping] = {}

    # Critical hooks
    for hook_id in data.get("critical", []) or []:
        mapping[hook_id] = CategoryMapping(
            hook_id=hook_id, category="critical"
        )

    # Module hooks
    modules = data.get("modules", {}) or {}
    for mod_num_str, hook_ids in modules.items():
        if mod_num_str == "any":
            # "any module" hooks — no specific module number
            for hook_id in hook_ids or []:
                mapping[hook_id] = CategoryMapping(
                    hook_id=hook_id, category="module", module_number=None
                )
        else:
            mod_num = int(mod_num_str)
            for hook_id in hook_ids or []:
                mapping[hook_id] = CategoryMapping(
                    hook_id=hook_id, category="module", module_number=mod_num
                )

    return mapping


def categorize_hooks(
    hooks: list[HookEntry],
    mapping: dict[str, CategoryMapping],
) -> tuple[list[HookEntry], dict[int | str, list[HookEntry]]]:
    """Split *hooks* into critical and module groups.

    Returns
    -------
    tuple[list[HookEntry], dict[int | str, list[HookEntry]]]
        ``(critical_sorted_alpha, module_hooks_by_number_sorted)``
        Unmapped hooks are placed under the key ``"any"`` (rendered as
        "any module").
    """
    critical: list[HookEntry] = []
    modules: dict[int | str, list[HookEntry]] = {}

    for hook in hooks:
        cat = mapping.get(hook.hook_id)
        if cat is not None and cat.category == "critical":
            critical.append(hook)
        elif cat is not None and cat.category == "module" and cat.module_number is not None:
            modules.setdefault(cat.module_number, []).append(hook)
        else:
            # Unmapped → "any module"
            modules.setdefault("any", []).append(hook)

    # Sort critical alphabetically
    critical.sort(key=lambda h: h.hook_id)

    # Sort each module bucket alphabetically
    for key in modules:
        modules[key].sort(key=lambda h: h.hook_id)

    return critical, modules


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------


def format_hook_entry(entry: HookEntry) -> str:
    """Format a single hook entry as Markdown.

    The hook prompt is rendered inside a fenced ``text`` code block so that
    markdown inside the prompt (lists, headings, inline links) does not
    violate CommonMark rules in the registry document. A four-backtick
    fence is used so prompts containing their own triple-backtick blocks
    can be included verbatim without breaking the outer fence.
    """
    # Build the event flow string
    flow = f"{entry.event_type} → {entry.action_type}"
    if entry.file_patterns:
        flow += f", filePatterns: `{entry.file_patterns}`"
    if entry.tool_types:
        flow += f", toolTypes: {entry.tool_types}"

    lines: list[str] = []
    lines.append(f"**{entry.hook_id}** ({flow})")
    lines.append("")

    if entry.prompt:
        lines.append("Prompt:")
        lines.append("")
        lines.append("````text")
        lines.append(entry.prompt)
        lines.append("````")
        lines.append("")

    lines.append(f"- id: `{entry.hook_id}`")
    lines.append(f"- name: `{entry.name}`")
    lines.append(f"- description: `{entry.description}`")

    return "\n".join(lines)


def generate_registry(
    critical_hooks: list[HookEntry],
    module_hooks: dict[int | str, list[HookEntry]],
    total_count: int,
) -> str:
    """Generate the complete ``hook-registry.md`` content.

    Line endings are normalised to Unix-style ``\\n``.
    """
    parts: list[str] = []

    # Frontmatter
    parts.append("---")
    parts.append("inclusion: manual")
    parts.append("---")
    parts.append("")

    # Title
    parts.append("# Hook Registry")
    parts.append("")

    # Intro paragraph
    parts.append(
        f"All {total_count} bootcamp hooks are defined below. "
        "The agent reads these definitions and calls the `createHook` tool "
        "with the specified parameters. Critical Hooks are created during "
        "onboarding (Step 1). Module Hooks are created when the bootcamper "
        "starts the associated module."
    )
    parts.append("")

    # Critical Hooks section
    parts.append("## Critical Hooks (created during onboarding)")
    parts.append("")
    for hook in critical_hooks:
        parts.append(format_hook_entry(hook))
        parts.append("")

    # Module Hooks section
    parts.append("## Module Hooks (created when module starts)")
    parts.append("")

    # Sort module keys: integers first (ascending), then "any" last
    int_keys = sorted(k for k in module_hooks if isinstance(k, int))
    str_keys = sorted(k for k in module_hooks if isinstance(k, str))
    sorted_keys = int_keys + str_keys

    for key in sorted_keys:
        hooks_in_module = module_hooks[key]
        for hook in hooks_in_module:
            if isinstance(key, int):
                label = f"Module {key}"
            else:
                label = "any module"

            # Build event flow for the module line
            flow = f"{hook.event_type} → {hook.action_type}"
            if hook.file_patterns:
                flow += f", filePatterns: `{hook.file_patterns}`"
            if hook.tool_types:
                flow += f", toolTypes: {hook.tool_types}"

            entry_lines: list[str] = []
            entry_lines.append(f"**{hook.hook_id}** — {label} ({flow})")
            entry_lines.append("")

            if hook.prompt:
                entry_lines.append("Prompt:")
                entry_lines.append("")
                entry_lines.append("````text")
                entry_lines.append(hook.prompt)
                entry_lines.append("````")
                entry_lines.append("")

            entry_lines.append(f"- id: `{hook.hook_id}`")
            entry_lines.append(f"- name: `{hook.name}`")
            entry_lines.append(f"- description: `{hook.description}`")

            parts.append("\n".join(entry_lines))
            parts.append("")

    content = "\n".join(parts)
    # Normalise line endings to Unix
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content


# ---------------------------------------------------------------------------
# Write / Verify
# ---------------------------------------------------------------------------


def write_registry(content: str, output_path: Path) -> None:
    """Write *content* to *output_path*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8", newline="")


def verify_registry(content: str, existing_path: Path) -> tuple[bool, str]:
    """Compare *content* against the file at *existing_path*.

    Returns
    -------
    tuple[bool, str]
        ``(matches, message)``
    """
    if not existing_path.exists():
        return False, f"Registry file missing: {existing_path}"

    existing = existing_path.read_text(encoding="utf-8")
    if content == existing:
        return True, "Registry is up to date."
    return False, "Registry is out of sync. Run: python scripts/sync_hook_registry.py --write"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate hook-registry.md from .kiro.hook files."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        default=True,
        help="Write the generated registry to disk (default).",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Compare generated registry against existing file.",
    )
    parser.add_argument(
        "--hooks-dir",
        type=Path,
        default=HOOKS_DIR,
        help=f"Path to hooks directory (default: {HOOKS_DIR}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REGISTRY_PATH,
        help=f"Path to output registry (default: {REGISTRY_PATH}).",
    )
    parser.add_argument(
        "--categories",
        type=Path,
        default=CATEGORIES_PATH,
        help=f"Path to category config (default: {CATEGORIES_PATH}).",
    )

    args = parser.parse_args()

    # Validate hooks directory
    if not args.hooks_dir.is_dir():
        print(f"ERROR: Hooks directory not found: {args.hooks_dir}", file=sys.stderr)
        sys.exit(1)

    # Validate categories file
    if not args.categories.is_file():
        print(f"ERROR: Categories file not found: {args.categories}", file=sys.stderr)
        sys.exit(1)

    # Parse hooks
    hooks, errors = parse_all_hooks(args.hooks_dir)
    for err in errors:
        print(f"WARNING: {err}", file=sys.stderr)

    # Load categories
    try:
        mapping = load_category_mapping(args.categories)
    except Exception as exc:
        print(f"ERROR: Failed to load categories: {exc}", file=sys.stderr)
        sys.exit(1)

    # Categorize
    critical, modules = categorize_hooks(hooks, mapping)
    total_count = len(hooks)

    # Generate
    content = generate_registry(critical, modules, total_count)

    if args.verify:
        matches, message = verify_registry(content, args.output)
        print(message)
        sys.exit(0 if matches else 1)
    else:
        write_registry(content, args.output)
        print(f"Registry written to {args.output} ({total_count} hooks)")


if __name__ == "__main__":
    main()
