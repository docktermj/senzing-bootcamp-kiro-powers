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
REGISTRY_CRITICAL_PATH = Path("senzing-bootcamp/steering/hook-registry-critical.md")
REGISTRY_MODULES_PATH = Path("senzing-bootcamp/steering/hook-registry-modules.md")
CATEGORIES_PATH = Path("senzing-bootcamp/hooks/hook-categories.yaml")
LOCKFILE_PATH = Path("senzing-bootcamp/hooks/hooks.lock.yaml")

# Registry outputs that the slicing refactor has retired.  ``--write`` removes
# any of these that still exist and ``--verify`` flags them as orphans.  The
# monolithic ``hook-registry-modules.md`` is superseded by the per-module
# ``hook-registry-module-NN.md`` / ``hook-registry-module-any.md`` slices.
DEPRECATED_REGISTRY_PATHS = (REGISTRY_MODULES_PATH,)

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
    categories_path: Path | None = None,
) -> tuple[list[HookEntry], dict[int | str, list[HookEntry]]]:
    """Split *hooks* into critical and module groups.

    A hook listed under multiple modules in ``hook-categories.yaml`` is placed
    under EACH of its module buckets (multi-module membership). To do this the
    per-module membership is read directly from *categories_path* (the same
    ``modules`` map ``_build_module_labels`` reads), because the
    ``hook_id -> CategoryMapping`` *mapping* collapses a multi-module hook to a
    single module (its last occurrence). When *categories_path* is None the
    function falls back to the single-module *mapping* (``cat.module_number``),
    preserving the original behavior for callers that pass a synthetic mapping.

    Returns
    -------
    tuple[list[HookEntry], dict[int | str, list[HookEntry]]]
        ``(critical_sorted_alpha, module_hooks_by_number_sorted)``
        Unmapped hooks are placed under the key ``"any"`` (rendered as
        "any module").
    """
    critical: list[HookEntry] = []
    modules: dict[int | str, list[HookEntry]] = {}

    membership: dict[str, list[int | str]] | None = None
    if categories_path is not None and categories_path.is_file():
        membership = _build_module_membership(categories_path)

    for hook in hooks:
        cat = mapping.get(hook.hook_id)
        if cat is not None and cat.category == "critical":
            critical.append(hook)
            continue

        if membership is not None and hook.hook_id in membership:
            # Multi-module aware: add the hook under every module bucket it
            # belongs to (e.g. [3, 5, 7, 8]). "any" stays a single bucket.
            for key in membership[hook.hook_id]:
                modules.setdefault(key, []).append(hook)
        elif (
            cat is not None
            and cat.category == "module"
            and cat.module_number is not None
        ):
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
# Markdown generation — summary
# ---------------------------------------------------------------------------


def _format_event_flow(entry: HookEntry) -> str:
    """Return a compact event flow string like ``agentStop → askAgent``."""
    return f"{entry.event_type} → {entry.action_type}"


def _build_module_membership(
    categories_path: Path,
) -> dict[str, list[int | str]]:
    """Build a mapping of hook_id → list of module keys from the categories file.

    Unlike ``_build_module_labels`` (which returns a single comma-joined string
    per hook), this returns the raw per-hook list of module buckets a hook
    belongs to — integer module numbers for numbered modules and the literal
    ``"any"`` for the any-module group. A hook under ``[3, 5, 7, 8]`` yields
    ``[3, 5, 7, 8]`` so ``categorize_hooks`` can file it under every bucket.

    Args:
        categories_path: Path to ``hook-categories.yaml``.

    Returns:
        Mapping of hook_id → list of module keys (``int`` or ``"any"``), in the
        order the modules appear in the file.
    """
    text = categories_path.read_text(encoding="utf-8")
    data = _parse_simple_yaml(text)

    membership: dict[str, list[int | str]] = {}
    modules = data.get("modules", {}) or {}
    for mod_key, hook_ids in modules.items():
        key: int | str = "any" if mod_key == "any" else int(mod_key)
        for hook_id in hook_ids or []:
            membership.setdefault(hook_id, []).append(key)

    return membership


def _build_module_labels(
    categories_path: Path,
) -> dict[str, str]:
    """Build a mapping of hook_id → module label from ``hook-categories.yaml``.

    Hooks appearing in multiple modules get a comma-separated label (e.g. "3,5,7,8").
    Hooks in the "any" category get the label "any".
    """
    text = categories_path.read_text(encoding="utf-8")
    data = _parse_simple_yaml(text)

    labels: dict[str, list[int | str]] = {}

    modules = data.get("modules", {}) or {}
    for mod_key, hook_ids in modules.items():
        for hook_id in hook_ids or []:
            if hook_id not in labels:
                labels[hook_id] = []
            if mod_key == "any":
                labels[hook_id].append("any")
            else:
                labels[hook_id].append(int(mod_key))

    # Build string labels: sort numeric parts, "any" goes last
    result: dict[str, str] = {}
    for hook_id, parts in labels.items():
        int_parts = sorted(p for p in parts if isinstance(p, int))
        str_parts = sorted(p for p in parts if isinstance(p, str))
        combined = [str(p) for p in int_parts] + str_parts
        result[hook_id] = ",".join(combined)

    return result


def generate_registry_summary(
    critical_hooks: list[HookEntry],
    module_hooks: dict[int | str, list[HookEntry]],
    total_count: int,
    categories_path: Path | None = None,
) -> str:
    """Generate the table-based ``hook-registry.md`` summary content.

    Produces a compact reference with:
    - Critical Hooks table (Hook ID, Event Type, Description)
    - Module Hooks table (Hook ID, Module, Event Type, Description)

    Target: under 2,500 tokens.

    Args:
        critical_hooks: Sorted list of critical hook entries.
        module_hooks: Module hooks grouped by module number/key.
        total_count: Total number of hooks.
        categories_path: Path to hook-categories.yaml for module labels.
    """
    # Build module labels from categories file if available
    if categories_path is not None and categories_path.is_file():
        module_labels = _build_module_labels(categories_path)
    else:
        module_labels = {}

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
        f"{total_count} bootcamp hooks organized by category. "
        "Load `hook-registry-critical.md` for full prompt text when creating hooks."
    )
    parts.append("")

    # Critical Hooks table
    parts.append("## Critical Hooks (created during onboarding)")
    parts.append("")
    parts.append("| Hook ID | Event Type | Description |")
    parts.append("|---------|-----------|-------------|")
    for hook in critical_hooks:
        flow = _format_event_flow(hook)
        parts.append(f"| {hook.hook_id} | {flow} | {hook.description} |")
    parts.append("")

    # Module Hooks table — deduplicate hooks that appear in multiple modules
    parts.append("## Module Hooks (created when module starts)")
    parts.append("")
    parts.append("| Hook ID | Module | Event Type | Description |")
    parts.append("|---------|--------|-----------|-------------|")

    # Collect unique module hooks with their labels
    seen: dict[str, HookEntry] = {}
    int_keys = sorted(k for k in module_hooks if isinstance(k, int))
    str_keys = sorted(k for k in module_hooks if isinstance(k, str))
    sorted_keys: list[int | str] = int_keys + str_keys

    for key in sorted_keys:
        for hook in module_hooks[key]:
            if hook.hook_id not in seen:
                seen[hook.hook_id] = hook

    # Sort by module label: numeric first (by first number), then "any"
    def _sort_key(item: tuple[str, HookEntry]) -> tuple[int, str]:
        hook_id, _ = item
        label = module_labels.get(hook_id, "any")
        first_part = label.split(",")[0]
        if first_part == "any":
            return (9999, hook_id)
        return (int(first_part), hook_id)

    for hook_id, hook in sorted(seen.items(), key=_sort_key):
        flow = _format_event_flow(hook)
        label = module_labels.get(hook_id, "any")
        parts.append(f"| {hook_id} | {label} | {flow} | {hook.description} |")
    parts.append("")

    # Hook Creation section
    parts.append("## Hook Creation")
    parts.append("")
    parts.append(
        "To create hooks, load `hook-registry-critical.md` for the full critical "
        "hook prompts and `createHook` parameters."
    )
    parts.append("")
    parts.append(
        "For module hook prompts, resolve `current_module` from "
        "`config/bootcamp_progress.json` and load the matching per-module slice "
        "`hook-registry-module-<NN>.md` (zero-padded two-digit module number, e.g. "
        "`hook-registry-module-03.md`) or `hook-registry-module-any.md` for hooks "
        "that apply to any module. Each slice holds the full prompt text and "
        "`createHook` parameters for that module's hooks."
    )
    parts.append("")
    parts.append(
        "If the expected per-module slice is missing at its path, fall back to this "
        "summary and report that the per-module slice is unavailable. The tables "
        "above list every hook by ID, event flow, module label, and description."
    )
    parts.append("")

    content = "\n".join(parts)
    # Normalise line endings to Unix
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content


# ---------------------------------------------------------------------------
# Markdown generation — detail
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


def generate_registry_critical(
    critical_hooks: list[HookEntry],
    total_count: int,
) -> str:
    """Generate the ``hook-registry-critical.md`` content.

    Contains only critical hooks with full prompt text, used during onboarding.
    """
    parts: list[str] = []

    # Frontmatter
    parts.append("---")
    parts.append("inclusion: manual")
    parts.append("---")
    parts.append("")

    # Title
    parts.append("# Hook Registry — Critical Hooks (Full Prompts)")
    parts.append("")

    # Intro paragraph
    parts.append(
        "Critical hook definitions with prompt text for use with the "
        "`createHook` tool during onboarding. These hooks are created in Step 1."
    )
    parts.append("")
    parts.append(
        "For module-specific hooks, see `hook-registry.md`, which routes to the "
        "per-module slice for your current module."
    )
    parts.append("For a quick reference of all hooks, see `hook-registry.md`.")
    parts.append("")

    # Critical Hooks section
    parts.append("## Critical Hooks (created during onboarding)")
    parts.append("")
    for hook in critical_hooks:
        parts.append(format_hook_entry(hook))
        parts.append("")

    content = "\n".join(parts)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content


def module_slice_filename(key: int | str) -> str:
    """Return the slice filename for a module bucket key.

    Produces a deterministic kebab-case filename for a per-module hook slice.
    Numbered modules use a zero-padded two-digit number; the unmapped group
    uses a distinct ``any`` name.

    Args:
        key: A module bucket key — an ``int`` module number or the literal
            string ``"any"`` for the unmapped group.

    Returns:
        The slice filename, e.g. ``"hook-registry-module-03.md"`` for module
        ``3`` or ``"hook-registry-module-any.md"`` for the ``"any"`` group.

    Examples:
        >>> module_slice_filename(3)
        'hook-registry-module-03.md'
        >>> module_slice_filename(11)
        'hook-registry-module-11.md'
        >>> module_slice_filename("any")
        'hook-registry-module-any.md'
    """
    if isinstance(key, int):
        return f"hook-registry-module-{key:02d}.md"
    return f"hook-registry-module-{key}.md"


def _module_label(key: int | str) -> str:
    """Return the human-readable module label for a bucket *key*.

    Args:
        key: A module bucket key — an ``int`` module number or the literal
            string ``"any"`` for the unmapped group.

    Returns:
        ``"Module N"`` for a numbered module or ``"any module"`` for ``"any"``.
    """
    if isinstance(key, int):
        return f"Module {key}"
    return "any module"


def generate_module_slice(
    key: int | str,
    hooks: list[HookEntry],
    total_count: int,
) -> str:
    """Generate the markdown for one Hook_Registry_Module_Slice.

    Begins with ``inclusion: manual`` frontmatter, a module-scoped title and
    label heading, and a short intro that points back to ``hook-registry.md``
    and ``hook-registry-critical.md``. It then renders the full prompt entry
    for each hook in *hooks* (already sorted by :func:`categorize_hooks`),
    reusing :func:`format_hook_entry` so a hook renders identically whether it
    appears in one slice or several. Line endings are normalised to ``\\n``.

    Args:
        key: The module bucket key — an ``int`` module number or the literal
            string ``"any"`` for the unmapped group.
        hooks: The hook entries belonging to this module bucket, already sorted
            by ``hook_id``.
        total_count: Total number of hooks across the registry (for context).

    Returns:
        The rendered Markdown content for the slice, with ``\\n`` line endings.
    """
    label = _module_label(key)

    parts: list[str] = []

    # Frontmatter
    parts.append("---")
    parts.append("inclusion: manual")
    parts.append("---")
    parts.append("")

    # Title
    parts.append(f"# Hook Registry — {label} (Full Prompts)")
    parts.append("")

    # Intro paragraph pointing back to the summary and critical registries
    parts.append(
        f"Full hook prompts for {label}, for use with the `createHook` tool when "
        "starting this module."
    )
    parts.append("")
    parts.append("For a quick reference of all hooks, see `hook-registry.md`.")
    parts.append(
        "For critical hooks (created during onboarding), see `hook-registry-critical.md`."
    )
    parts.append("")

    # Module hooks section
    parts.append(f"## {label} Hooks")
    parts.append("")
    for hook in hooks:
        parts.append(format_hook_entry(hook))
        parts.append("")

    content = "\n".join(parts)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content


def build_module_slices(
    module_hooks: dict[int | str, list[HookEntry]],
    steering_dir: Path,
    total_count: int,
) -> dict[Path, str]:
    """Map each non-empty module bucket to its slice path and rendered content.

    Builds the full ``{slice_path: content}`` map for every module bucket
    produced by :func:`categorize_hooks`. Those buckets only contain non-empty
    lists, so a module with no hooks yields no slice (no empty file is written).
    The ``"any"`` bucket maps to ``hook-registry-module-any.md``. Each slice
    path is ``steering_dir / module_slice_filename(key)`` and its content comes
    from :func:`generate_module_slice`.

    Args:
        module_hooks: Module buckets from :func:`categorize_hooks` — keys are
            ``int`` module numbers or the literal ``"any"`` and each value is a
            non-empty list of hook entries sorted by ``hook_id``.
        steering_dir: Directory the slice files live in; slice paths are derived
            relative to it.
        total_count: Total number of hooks across the registry (for context).

    Returns:
        Mapping of each non-empty bucket's slice path to its rendered Markdown
        content.
    """
    slices: dict[Path, str] = {}
    for key, hooks in module_hooks.items():
        slice_path = steering_dir / module_slice_filename(key)
        slices[slice_path] = generate_module_slice(key, hooks, total_count)
    return slices


# ---------------------------------------------------------------------------
# Lockfile generation
# ---------------------------------------------------------------------------


def generate_lockfile(
    hooks: list[HookEntry],
    mapping: dict[str, CategoryMapping],
) -> str:
    """Generate the ``hooks.lock.yaml`` content.

    Produces a deterministic YAML lockfile listing all hooks with their
    ID, version, category, and event type.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines: list[str] = []
    lines.append("# AUTO-GENERATED — do not edit manually.")
    lines.append("# Run: python3 senzing-bootcamp/scripts/sync_hook_registry.py --write")
    lines.append(f'generated_at: "{now}"')
    lines.append("hooks:")

    # Sort hooks alphabetically by ID
    sorted_hooks = sorted(hooks, key=lambda h: h.hook_id)

    for hook in sorted_hooks:
        cat = mapping.get(hook.hook_id)
        if cat is not None:
            category = cat.category
        else:
            category = "uncategorized"

        # Get version from the hook file
        hook_path = HOOKS_DIR / f"{hook.hook_id}.kiro.hook"
        version = "1.0.0"
        if hook_path.exists():
            try:
                data = json.loads(hook_path.read_text(encoding="utf-8"))
                version = data.get("version", "1.0.0")
            except (json.JSONDecodeError, OSError):
                pass

        lines.append(f"  - id: {hook.hook_id}")
        lines.append(f'    version: "{version}"')
        lines.append(f"    category: {category}")
        lines.append(f"    event_type: {hook.event_type}")

    content = "\n".join(lines) + "\n"
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
        help=f"Path to output summary registry (default: {REGISTRY_PATH}).",
    )
    parser.add_argument(
        "--output-critical",
        type=Path,
        default=REGISTRY_CRITICAL_PATH,
        help=f"Path to output critical registry (default: {REGISTRY_CRITICAL_PATH}).",
    )
    parser.add_argument(
        "--steering-dir",
        type=Path,
        default=REGISTRY_PATH.parent,
        help=(
            "Directory the per-module hook slices are written to / verified "
            f"against (default: {REGISTRY_PATH.parent})."
        ),
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
    critical, modules = categorize_hooks(hooks, mapping, args.categories)
    total_count = len(hooks)

    # Generate all files
    summary_content = generate_registry_summary(
        critical, modules, total_count, categories_path=args.categories
    )
    critical_content = generate_registry_critical(critical, total_count)
    lockfile_content = generate_lockfile(hooks, mapping)

    if args.verify:
        all_match = True

        summary_matches, summary_message = verify_registry(summary_content, args.output)
        if not summary_matches:
            print(f"FAIL: {args.output} — {summary_message}", file=sys.stderr)
            all_match = False

        critical_matches, critical_message = verify_registry(
            critical_content, args.output_critical
        )
        if not critical_matches:
            print(f"FAIL: {args.output_critical} — {critical_message}", file=sys.stderr)
            all_match = False

        # Per-module slice verification: regenerate the slice set and compare
        # each on disk byte-for-byte. A freshly generated slice that is missing
        # on disk (or differs) fails verification.
        steering_dir = args.steering_dir
        slices = build_module_slices(modules, steering_dir, total_count)
        for slice_path, slice_content in slices.items():
            slice_matches, slice_message = verify_registry(slice_content, slice_path)
            if not slice_matches:
                print(f"FAIL: {slice_path} — {slice_message}", file=sys.stderr)
                all_match = False

        # Orphan detection: a deprecated registry file that still exists on disk
        # must be removed via --write.
        for deprecated_path in DEPRECATED_REGISTRY_PATHS:
            if deprecated_path.exists():
                print(
                    f"FAIL: {deprecated_path} — orphaned deprecated registry file; "
                    "run --write to remove",
                    file=sys.stderr,
                )
                all_match = False

        # Lockfile verification: compare structure (skip generated_at timestamp)
        lockfile_path = LOCKFILE_PATH
        if lockfile_path.exists():
            existing_lock = lockfile_path.read_text(encoding="utf-8")
            # Compare everything except the generated_at line
            def _strip_timestamp(text: str) -> str:
                return "\n".join(
                    line for line in text.splitlines()
                    if not line.startswith("generated_at:")
                )
            if _strip_timestamp(lockfile_content) != _strip_timestamp(existing_lock):
                print(f"FAIL: {lockfile_path} — Lockfile is out of sync.", file=sys.stderr)
                all_match = False
        else:
            print(f"FAIL: {lockfile_path} — Lockfile missing.", file=sys.stderr)
            all_match = False

        if all_match:
            print("All registry files are up to date.")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Derive the steering directory from --steering-dir so the per-module
        # slices land alongside hook-registry.md.
        steering_dir = args.steering_dir
        slices = build_module_slices(modules, steering_dir, total_count)

        try:
            write_registry(summary_content, args.output)
            print(f"Summary registry written to {args.output} ({total_count} hooks)")

            write_registry(critical_content, args.output_critical)
            print(
                f"Critical registry written to {args.output_critical} "
                f"({len(critical)} hooks)"
            )

            for slice_path, slice_content in slices.items():
                write_registry(slice_content, slice_path)
                print(f"Module slice written to {slice_path}")

            # Remove any retired registry output that still exists on disk so the
            # deprecated monolith does not linger as an orphan.
            for deprecated_path in DEPRECATED_REGISTRY_PATHS:
                if deprecated_path.exists():
                    deprecated_path.unlink()
                    print(f"Removed deprecated registry file {deprecated_path}")

            write_registry(lockfile_content, LOCKFILE_PATH)
            print(f"Lockfile written to {LOCKFILE_PATH} ({total_count} hooks)")
        except (OSError, PermissionError) as exc:
            print(f"ERROR: Failed to write registry files: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
