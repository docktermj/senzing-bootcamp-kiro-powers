#!/usr/bin/env python3
"""Hook self-test: structural validation of all v1 hook (*.json) files.

Validates the Kiro 1.0 ``v1`` hook schema for every shipped ``hooks/*.json``
file: JSON validity, the ``{"version": "v1", "hooks": [ ... ]}`` wrapper, the
required ``name``/``trigger``/``action`` fields, a ``matcher`` where the trigger
requires scoping, only the 1.0 trigger names and the ``agent``/``command``
action types, matcher regex compilation, and registry consistency.

The 1.0 accept-lists (valid triggers, valid action types, and the
matcher-requirement classification of each trigger) are sourced from the shared
``hook_renames`` module so the validator can never drift from the migration
transform. The legacy ``*.kiro.hook`` files are intentionally excluded from
discovery so this self-test validates only the migrated v1 definitions.

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

# Allow importing sibling scripts (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hook_renames as renames  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
REGISTRY_PATH = Path("senzing-bootcamp/steering/hook-registry-critical.md")
# The single ``hook-registry-modules.md`` monolith was replaced by per-module
# registry slices (``hook-registry-module-NN.md`` / ``hook-registry-module-any.md``).
# Registry consistency reads every slice matching this glob.
MODULE_SLICE_GLOB = "hook-registry-module-*.md"
CATEGORIES_PATH = Path("senzing-bootcamp/hooks/hook-categories.yaml")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class HookTestResult:
    """Aggregated test result for a single hook file."""

    hook_id: str
    trigger: str = ""
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
# V1 hook validation
# ---------------------------------------------------------------------------


def _validate_v1_entry(hook: object, idx: int, result: HookTestResult) -> None:
    """Validate a single V1_Hook entry against the Kiro 1.0 schema.

    Applies the required-field (Req 6.2), 1.0-trigger-only (Req 6.3),
    1.0-action-type-only (Req 6.4), matcher-when-required (Req 6.2), and
    matcher-compiles (Req 6.5) rules, reusing the accept-lists in
    ``hook_renames`` rather than hardcoding any trigger set. An optional
    hook-level ``timeout`` integer is accepted rather than rejected
    (``session-log-events`` carries ``"timeout": 10``).

    Failures are appended to ``result``; the display fields (trigger,
    action_type, prompt, command) are populated from the first entry.

    Args:
        hook: The parsed hook entry (expected to be a dict).
        idx: The entry's index within the ``hooks`` array.
        result: The aggregated result for the file, mutated in place.
    """
    prefix = "" if idx == 0 else f"hooks[{idx}]: "

    if not isinstance(hook, dict):
        result.passed = False
        result.failures.append(f"{prefix}entry is not an object")
        return

    # Req 6.6: a legacy when/then shape inside an entry is a stale definition.
    if "when" in hook or "then" in hook:
        result.passed = False
        result.failures.append(f"{prefix}uses legacy when/then schema")
        return

    # Req 6.2: name present and non-empty.
    name = hook.get("name")
    if not (isinstance(name, str) and name.strip()):
        result.passed = False
        result.failures.append(f"{prefix}missing required field: name")

    # Req 6.2 / 6.3: trigger present and a valid 1.0 trigger name (rejects
    # legacy names such as fileEdited/agentStop/userTriggered).
    trigger = hook.get("trigger", "")
    if idx == 0:
        result.trigger = trigger if isinstance(trigger, str) else ""
    trigger_ok = trigger in renames.VALID_V1_TRIGGERS
    if not trigger_ok:
        result.passed = False
        result.failures.append(f"{prefix}invalid trigger: {trigger!r}")

    # Req 6.2 / 6.4: action present with a valid 1.0 action type (rejects the
    # legacy askAgent/runCommand types).
    action = hook.get("action")
    action_type = action.get("type", "") if isinstance(action, dict) else ""
    if idx == 0:
        result.action_type = action_type if isinstance(action_type, str) else ""
    if action_type not in renames.VALID_V1_ACTION_TYPES:
        result.passed = False
        result.failures.append(f"{prefix}invalid action type: {action_type!r}")
    else:
        # Payload presence: an agent action carries a prompt, a command action
        # carries a command.
        payload_field = "prompt" if action_type == "agent" else "command"
        payload = action.get(payload_field, "") if isinstance(action, dict) else ""
        if not (isinstance(payload, str) and payload.strip()):
            result.passed = False
            result.failures.append(
                f"{prefix}empty {payload_field} for {action_type} action"
            )
        elif idx == 0:
            if action_type == "agent":
                result.prompt = payload
            else:
                result.command = payload

    # Req 6.2 / 6.5: a matcher is required for scoped triggers (file-path or
    # tool-name); any present matcher must compile as a regular expression.
    matcher = hook.get("matcher")
    if trigger_ok:
        kind = renames.matcher_kind(trigger)
        if kind != renames.MATCHER_KIND_UNSCOPED and not (
            isinstance(matcher, str) and matcher.strip()
        ):
            result.passed = False
            result.failures.append(f"{prefix}{trigger} requires a {kind} matcher")
    if isinstance(matcher, str) and matcher != "":
        try:
            re.compile(matcher)
        except re.error as exc:
            result.passed = False
            result.failures.append(f"{prefix}matcher does not compile: {exc}")
    elif matcher is not None and not isinstance(matcher, str):
        result.passed = False
        result.failures.append(f"{prefix}matcher must be a string")

    # Accept an optional hook-level timeout (integer) without treating it as an
    # unknown/invalid field (session-log-events carries "timeout": 10). A bool
    # is not a valid integer timeout.
    if "timeout" in hook:
        timeout = hook.get("timeout")
        if not (isinstance(timeout, int) and not isinstance(timeout, bool)):
            result.passed = False
            result.failures.append(f"{prefix}optional 'timeout' must be an integer")


def validate_hook(file_path: Path) -> HookTestResult:
    """Run all v1-schema validation checks on a single hook file.

    Args:
        file_path: Path to the ``<id>.json`` hook file.

    Returns:
        HookTestResult with pass/fail status and any failure messages.
    """
    result = HookTestResult(hook_id=hook_id_from_path(file_path))

    # Check 1: valid JSON.
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.passed = False
        result.failures.append(f"Invalid JSON: {e}")
        return result
    except OSError as e:
        result.passed = False
        result.failures.append(f"Cannot read file: {e}")
        return result

    # Req 6.6: a legacy top-level when/then shape is a stale definition.
    if isinstance(data, dict) and ("when" in data or "then" in data):
        result.passed = False
        result.failures.append("Uses legacy when/then schema (expected v1 wrapper)")
        return result

    # Req 6.1: top-level version == "v1".
    if not isinstance(data, dict) or data.get("version") != "v1":
        result.passed = False
        result.failures.append("Top-level version must be 'v1'")

    # Req 6.1: top-level hooks array (non-empty).
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, list):
        result.passed = False
        result.failures.append("Missing required field: hooks (array)")
        return result
    if not hooks:
        result.passed = False
        result.failures.append("hooks array is empty")
        return result

    for idx, hook in enumerate(hooks):
        _validate_v1_entry(hook, idx, result)

    return result


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_hooks(hooks_dir: Path) -> list[Path]:
    """Find all shipped v1 hook (*.json) files in the hooks directory.

    The legacy ``*.kiro.hook`` files are intentionally excluded so this
    self-test validates only the migrated v1 definitions.

    Args:
        hooks_dir: Path to the hooks directory.

    Returns:
        Sorted list of hook file paths.
    """
    if not hooks_dir.exists():
        return []
    return sorted(hooks_dir.glob("*.json"))


def hook_id_from_path(path: Path) -> str:
    """Extract hook ID from a v1 hook file path (``<id>.json`` -> ``<id>``).

    Args:
        path: Path to a ``<id>.json`` file.

    Returns:
        The hook ID string.
    """
    return path.stem


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

    The documented-hook surface is the union of the critical registry
    (``hook-registry-critical.md``) and every per-module slice
    (``hook-registry-module-NN.md`` / ``hook-registry-module-any.md``), which
    together replaced the retired ``hook-registry-modules.md`` monolith. A hook
    is considered documented if it appears in any of these files.

    Args:
        hook_ids: Set of hook IDs from discovered files.
        registry_path: Path to hook-registry-critical.md.

    Returns:
        RegistryConsistency with any mismatches.
    """
    registry_ids = parse_registry_hook_ids(registry_path)
    # Also check the per-module registry slices that replaced the single
    # hook-registry-modules.md monolith.
    for slice_path in sorted(registry_path.parent.glob(MODULE_SLICE_GLOB)):
        registry_ids |= parse_registry_hook_ids(slice_path)
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
        f"  {'ID':<30} {'Trigger':<16} {'Action':<12} {'Status'}"
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
            f"  {r.hook_id:<30} {r.trigger:<16} {r.action_type:<12} {status}"
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
        description="Structural validation of v1 hook (*.json) files"
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


# ---------------------------------------------------------------------------
# pytest entry point
# ---------------------------------------------------------------------------


def test_all_hooks_pass() -> None:
    """Pytest wrapper: validates all v1 hooks pass structural checks."""
    hook_files = discover_hooks(HOOKS_DIR)
    assert hook_files, f"No hook files found in {HOOKS_DIR}"

    results: list[HookTestResult] = []
    for hook_file in hook_files:
        result = validate_hook(hook_file)
        results.append(result)

    failures = [r for r in results if not r.passed]
    if failures:
        msgs = []
        for r in failures:
            msgs.append(f"{r.hook_id}: {'; '.join(r.failures)}")
        raise AssertionError(
            f"{len(failures)} hook(s) failed validation:\n" + "\n".join(msgs)
        )


def test_registry_consistency() -> None:
    """Pytest wrapper: validates hook files match registry entries."""
    hook_files = discover_hooks(HOOKS_DIR)
    all_hook_ids = {hook_id_from_path(f) for f in hook_files}
    registry = check_registry_consistency(all_hook_ids, REGISTRY_PATH)

    msgs: list[str] = []
    if registry.orphaned_hooks:
        msgs.append(
            f"Hooks without registry entries: {', '.join(registry.orphaned_hooks)}"
        )
    if registry.stale_entries:
        msgs.append(
            f"Registry entries without hook files: {', '.join(registry.stale_entries)}"
        )
    if msgs:
        raise AssertionError("Registry inconsistency:\n" + "\n".join(msgs))
