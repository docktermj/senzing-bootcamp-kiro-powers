#!/usr/bin/env python3
"""Hook self-test: structural validation of all .kiro.hook files.

Validates JSON structure, required fields, event types, action types,
pattern validity, toolType validity, and registry consistency.

Usage:
    python3 senzing-bootcamp/scripts/test_hooks.py
    python3 senzing-bootcamp/scripts/test_hooks.py --hook ask-bootcamper
    python3 senzing-bootcamp/scripts/test_hooks.py --categories critical
    python3 senzing-bootcamp/scripts/test_hooks.py --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
REGISTRY_PATH = Path("senzing-bootcamp/steering/hook-registry.md")
CATEGORIES_PATH = Path("senzing-bootcamp/hooks/hook-categories.yaml")

VALID_EVENT_TYPES = {
    "fileEdited", "fileCreated", "fileDeleted",
    "userTriggered", "promptSubmit", "agentStop",
    "preToolUse", "postToolUse",
    "preTaskExecution", "postTaskExecution",
}

VALID_TOOL_CATEGORIES = {"read", "write", "shell", "web", "spec", "*"}

FILE_EVENT_TYPES = {"fileEdited", "fileCreated", "fileDeleted"}
TOOL_EVENT_TYPES = {"preToolUse", "postToolUse"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single validation check."""

    passed: bool
    message: str = ""


@dataclass
class HookTestResult:
    """Aggregated test result for a single hook."""

    hook_id: str
    event_type: str = ""
    action_type: str = ""
    passed: bool = True
    failures: list[str] = field(default_factory=list)
    prompt: str = ""
    command: str = ""


# ---------------------------------------------------------------------------
# YAML parser (minimal, stdlib-only)
# ---------------------------------------------------------------------------


def parse_categories_yaml(path: Path) -> dict[str, list[str]]:
    """Parse hook-categories.yaml into {category: [hook_ids]}.

    Handles the nested module structure by flattening module sub-keys
    into a single list per top-level category.

    Args:
        path: Path to hook-categories.yaml.

    Returns:
        Dict mapping category name to list of hook IDs.
    """
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    categories: dict[str, list[str]] = {}
    current_category: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue
        # Top-level category (no leading whitespace, ends with colon)
        if not line[0].isspace() and stripped.endswith(":"):
            current_category = stripped[:-1]
            if current_category not in categories:
                categories[current_category] = []
        # Sub-key like "  2:" or "  any:" — just a grouping, skip
        elif stripped.endswith(":") and not stripped.startswith("- "):
            continue
        # List item like "    - ask-bootcamper"
        elif stripped.startswith("- ") and current_category is not None:
            hook_id = stripped[2:].strip()
            categories[current_category].append(hook_id)

    return categories


# ---------------------------------------------------------------------------
# Registry parser
# ---------------------------------------------------------------------------


def parse_registry_hook_ids(path: Path) -> set[str]:
    """Extract hook IDs from hook-registry.md.

    Looks for bold entries like **hook-id** at the start of lines.

    Args:
        path: Path to hook-registry.md.

    Returns:
        Set of hook IDs found in the registry.
    """
    if not path.exists():
        return set()

    text = path.read_text(encoding="utf-8")
    ids: set[str] = set()
    for match in re.finditer(r"^\*\*([a-z0-9-]+)\*\*", text, re.MULTILINE):
        ids.add(match.group(1))
    return ids


# ---------------------------------------------------------------------------
# Glob validation
# ---------------------------------------------------------------------------


def validate_glob_pattern(pattern: str) -> str | None:
    """Check if a glob pattern is structurally valid.

    Args:
        pattern: Glob pattern string.

    Returns:
        Error message if invalid, None if valid.
    """
    # Check for unbalanced brackets
    depth = 0
    for ch in pattern:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if depth < 0:
            return f"Unbalanced bracket in glob: {pattern}"
    if depth != 0:
        return f"Unbalanced bracket in glob: {pattern}"

    # Check for empty pattern
    if not pattern.strip():
        return "Empty glob pattern"

    return None


# ---------------------------------------------------------------------------
# ToolType validation
# ---------------------------------------------------------------------------


def validate_tool_type(tool_type: str) -> str | None:
    """Validate a single toolType entry.

    Valid entries are either a known category or a compilable regex.

    Args:
        tool_type: The toolType string to validate.

    Returns:
        Error message if invalid, None if valid.
    """
    if tool_type in VALID_TOOL_CATEGORIES:
        return None

    # Try as regex
    try:
        re.compile(tool_type)
        return None
    except re.error as e:
        return f"Invalid toolType regex '{tool_type}': {e}"


# ---------------------------------------------------------------------------
# Hook validation
# ---------------------------------------------------------------------------


def validate_hook(file_path: Path) -> HookTestResult:
    """Run all validation checks on a single hook file.

    Args:
        file_path: Path to the .kiro.hook file.

    Returns:
        HookTestResult with pass/fail status and any failure messages.
    """
    hook_id = file_path.stem.replace(".kiro", "")
    result = HookTestResult(hook_id=hook_id)

    # Check 1: Valid JSON
    try:
        text = file_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        result.passed = False
        result.failures.append(f"Invalid JSON: {e}")
        return result
    except OSError as e:
        result.passed = False
        result.failures.append(f"Cannot read file: {e}")
        return result

    # Check 2: Required fields
    for fld in ("name", "version"):
        if fld not in data:
            result.passed = False
            result.failures.append(f"Missing required field: {fld}")

    when = data.get("when", {})
    then = data.get("then", {})

    if "when" not in data:
        result.passed = False
        result.failures.append("Missing required field: when")
    elif "type" not in when:
        result.passed = False
        result.failures.append("Missing required field: when.type")

    if "then" not in data:
        result.passed = False
        result.failures.append("Missing required field: then")
    elif "type" not in then:
        result.passed = False
        result.failures.append("Missing required field: then.type")

    # If we can't get event/action type, stop here
    event_type = when.get("type", "")
    action_type = then.get("type", "")
    result.event_type = event_type
    result.action_type = action_type

    if not event_type or not action_type:
        return result

    # Check 3: Valid event type
    if event_type not in VALID_EVENT_TYPES:
        result.passed = False
        result.failures.append(f"Invalid event type: {event_type}")

    # Check 4: Valid action type
    if action_type not in ("askAgent", "runCommand"):
        result.passed = False
        result.failures.append(f"Invalid action type: {action_type}")

    # Check 5: Prompt/command presence
    if action_type == "askAgent":
        prompt = then.get("prompt", "")
        result.prompt = prompt
        if not prompt or not prompt.strip():
            result.passed = False
            result.failures.append("Empty prompt for askAgent hook")
    elif action_type == "runCommand":
        command = then.get("command", "")
        result.command = command
        if not command or not command.strip():
            result.passed = False
            result.failures.append("Empty command for runCommand hook")

    # Check 6: File patterns for file-event hooks
    if event_type in FILE_EVENT_TYPES:
        patterns = when.get("patterns")
        if patterns is None:
            result.passed = False
            result.failures.append(
                f"Missing when.patterns for {event_type} hook"
            )
        elif isinstance(patterns, list):
            for pat in patterns:
                err = validate_glob_pattern(pat)
                if err:
                    result.passed = False
                    result.failures.append(err)
        else:
            # patterns should be a string (comma-separated) or list
            if isinstance(patterns, str):
                for pat in patterns.split(","):
                    err = validate_glob_pattern(pat.strip())
                    if err:
                        result.passed = False
                        result.failures.append(err)

    # Check 7: ToolTypes for tool-event hooks
    if event_type in TOOL_EVENT_TYPES:
        tool_types = when.get("toolTypes")
        if tool_types is None:
            result.passed = False
            result.failures.append(
                f"Missing when.toolTypes for {event_type} hook"
            )
        elif isinstance(tool_types, list):
            for tt in tool_types:
                err = validate_tool_type(tt)
                if err:
                    result.passed = False
                    result.failures.append(err)
        elif isinstance(tool_types, str):
            for tt in tool_types.split(","):
                err = validate_tool_type(tt.strip())
                if err:
                    result.passed = False
                    result.failures.append(err)

    return result


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_hooks(hooks_dir: Path) -> list[Path]:
    """Find all .kiro.hook files in the hooks directory.

    Args:
        hooks_dir: Path to the hooks directory.

    Returns:
        Sorted list of hook file paths.
    """
    if not hooks_dir.exists():
        return []
    return sorted(hooks_dir.glob("*.kiro.hook"))


def hook_id_from_path(path: Path) -> str:
    """Extract hook ID from a hook file path.

    Args:
        path: Path to a .kiro.hook file.

    Returns:
        The hook ID string.
    """
    return path.stem.replace(".kiro", "")


# ---------------------------------------------------------------------------
# Registry consistency
# ---------------------------------------------------------------------------


@dataclass
class RegistryConsistency:
    """Result of registry consistency check."""

    orphaned_hooks: list[str] = field(default_factory=list)
    stale_entries: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if no inconsistencies found."""
        return not self.orphaned_hooks and not self.stale_entries


def check_registry_consistency(
    hook_ids: set[str], registry_path: Path
) -> RegistryConsistency:
    """Compare hook file IDs against registry entries.

    Args:
        hook_ids: Set of hook IDs from discovered files.
        registry_path: Path to hook-registry.md.

    Returns:
        RegistryConsistency with any mismatches.
    """
    registry_ids = parse_registry_hook_ids(registry_path)
    result = RegistryConsistency()

    for hid in sorted(hook_ids - registry_ids):
        result.orphaned_hooks.append(hid)

    for hid in sorted(registry_ids - hook_ids):
        result.stale_entries.append(hid)

    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_results(
    results: list[HookTestResult],
    registry: RegistryConsistency,
    verbose: bool = False,
) -> str:
    """Format test results as a summary table.

    Args:
        results: List of per-hook test results.
        registry: Registry consistency check result.
        verbose: Whether to show full prompt/command text.

    Returns:
        Formatted string for terminal output.
    """
    lines: list[str] = []
    lines.append("")
    lines.append("Hook Self-Test Results")
    lines.append("=" * 70)
    lines.append(
        f"  {'ID':<30} {'Event Type':<16} {'Action':<12} {'Status'}"
    )
    lines.append("-" * 70)

    passed_count = 0
    failed_count = 0

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        if r.passed:
            passed_count += 1
        else:
            failed_count += 1

        lines.append(
            f"  {r.hook_id:<30} {r.event_type:<16} {r.action_type:<12} {status}"
        )

        if not r.passed:
            for fail_msg in r.failures:
                lines.append(f"    → {fail_msg}")

        if verbose:
            if r.prompt:
                preview = r.prompt[:200] + ("..." if len(r.prompt) > 200 else "")
                lines.append(f"    prompt: {preview}")
            if r.command:
                lines.append(f"    command: {r.command}")

    lines.append("-" * 70)

    # Registry consistency
    lines.append("Registry Consistency:")
    if registry.passed:
        lines.append("  ✅ All hook files have registry entries")
        lines.append("  ✅ All registry entries have hook files")
    else:
        if registry.orphaned_hooks:
            lines.append(
                f"  ❌ Hooks without registry entries: "
                f"{', '.join(registry.orphaned_hooks)}"
            )
            failed_count += len(registry.orphaned_hooks)
        if registry.stale_entries:
            lines.append(
                f"  ❌ Registry entries without hook files: "
                f"{', '.join(registry.stale_entries)}"
            )
            failed_count += len(registry.stale_entries)

    lines.append("")
    lines.append(f"Summary: {passed_count} passed, {failed_count} failed")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run hook self-tests.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 if all pass, 1 if any fail.
    """
    parser = argparse.ArgumentParser(
        description="Structural validation of .kiro.hook files"
    )
    parser.add_argument(
        "--hook", metavar="HOOK_ID",
        help="Test a single hook by ID",
    )
    parser.add_argument(
        "--categories", metavar="CATEGORY",
        help="Filter tests to hooks in a specific category",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show full prompt/command for each hook",
    )
    args = parser.parse_args(argv)

    # Discover hooks
    hook_files = discover_hooks(HOOKS_DIR)

    if not hook_files:
        print("No hook files found in", HOOKS_DIR)
        return 1

    # Filter by --hook
    if args.hook:
        hook_files = [
            f for f in hook_files if hook_id_from_path(f) == args.hook
        ]
        if not hook_files:
            print(f"Hook not found: {args.hook}")
            return 1

    # Filter by --categories
    if args.categories:
        categories = parse_categories_yaml(CATEGORIES_PATH)
        cat_hooks = categories.get(args.categories)
        if cat_hooks is None:
            # Check nested modules structure
            cat_hooks = categories.get("modules", {})
            if isinstance(cat_hooks, list) and args.categories == "modules":
                pass  # already a flat list
            else:
                print(f"Category not found: {args.categories}")
                print(f"Available: {', '.join(categories.keys())}")
                return 1
        if isinstance(cat_hooks, list):
            hook_files = [
                f for f in hook_files
                if hook_id_from_path(f) in cat_hooks
            ]

    # Validate each hook
    results: list[HookTestResult] = []
    for hook_file in hook_files:
        result = validate_hook(hook_file)
        results.append(result)

    # Registry consistency
    all_hook_ids = {hook_id_from_path(f) for f in discover_hooks(HOOKS_DIR)}
    registry = check_registry_consistency(all_hook_ids, REGISTRY_PATH)

    # Output
    output = format_results(results, registry, verbose=args.verbose)
    print(output)

    # Exit code
    any_failed = any(not r.passed for r in results) or not registry.passed
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
