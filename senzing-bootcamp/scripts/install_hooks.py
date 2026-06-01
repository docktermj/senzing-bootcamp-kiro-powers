#!/usr/bin/env python3
"""Senzing Bootcamp - Hook Installer.

Installs bootcamp hooks into the bootcamper's ``.kiro/hooks`` directory.
Cross-platform: works on Linux, macOS, and Windows.

The authoritative set of installable hooks is derived from the
``*.kiro.hook`` files present in the power's ``hooks`` directory — the
hardcoded ``HOOK_METADATA`` table below is a non-authoritative display
overlay only (it supplies friendly descriptions; display names come from
each hook file's ``name`` field).

Usage
-----
Interactive menu (default when no flag is supplied)::

    python3 senzing-bootcamp/scripts/install_hooks.py

Non-interactive (never reads stdin)::

    python3 senzing-bootcamp/scripts/install_hooks.py --all
    python3 senzing-bootcamp/scripts/install_hooks.py --essential

Exit code 0 on success, 1 on error (e.g. missing power hooks directory).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Default paths (resolved relative to this script's location)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent  # senzing-bootcamp/scripts
POWER_ROOT = SCRIPT_DIR.parent  # senzing-bootcamp
DEFAULT_POWER_HOOKS = POWER_ROOT / "hooks"  # senzing-bootcamp/hooks
DEFAULT_USER_HOOKS = POWER_ROOT.parent / ".kiro" / "hooks"  # <project>/.kiro/hooks
DEFAULT_CATEGORIES = POWER_ROOT / "hooks" / "hook-categories.yaml"


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def color_supported() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return bool(
            os.environ.get("WT_SESSION")
            or os.environ.get("TERM_PROGRAM")
            or "ANSICON" in os.environ
        )
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = color_supported()


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t: str) -> str: return c("0;32", t)
def yellow(t: str) -> str: return c("1;33", t)
def blue(t: str) -> str: return c("0;34", t)
def cyan(t: str) -> str: return c("0;36", t)
def red(t: str) -> str: return c("0;31", t)


# ---------------------------------------------------------------------------
# Hook metadata (non-authoritative display overlay — filename → description)
# ---------------------------------------------------------------------------
#
# This table is NOT the source of truth for which hooks exist; that is the
# ``*.kiro.hook`` glob in the power hooks directory.  Entries here only supply
# friendly descriptions for display.  Display names are read from each hook
# file's ``name`` field (the "to {verb phrase}" pattern), not from this table.

HOOK_METADATA: dict[str, str] = {
    # Critical hooks (created during onboarding)
    "ask-bootcamper.kiro.hook":
        "Owns closing questions, answer-processing, and feedback reminders",
    "review-bootcamper-input.kiro.hook":
        "Routes feedback and status trigger phrases",
    "code-style-check.kiro.hook":
        "Ensures code follows language-appropriate standards",
    "commonmark-validation.kiro.hook":
        "Validates Markdown files follow the CommonMark spec",
    "write-policy-gate.kiro.hook":
        "Consolidated preToolUse write gate — runs file-path, single-question, "
        "and direct-SQL policy checks in a single interception",
    # Module hooks
    "validate-business-problem.kiro.hook":
        "Validates Module 1 problem definition before proceeding",
    "verify-sdk-setup.kiro.hook":
        "Re-verifies SDK during Module 2 config changes",
    "verify-demo-results.kiro.hook":
        "Verifies Module 3 system verification against the TruthSet",
    "gate-module3-visualization.kiro.hook":
        "Blocks Module 3 completion until the visualization step is done",
    "enforce-mandatory-gate.kiro.hook":
        "Blocks step advancement past a mandatory gate step before it executes",
    "enforce-gate-on-stop.kiro.hook":
        "Catches Module 3 mandatory-gate violations retroactively at agent stop",
    "validate-data-files.kiro.hook":
        "Checks data file format and readability when added to data/raw/",
    "data-quality-check.kiro.hook":
        "Validates quality when transformations change",
    "analyze-after-mapping.kiro.hook":
        "Validates transformed data quality and Entity Spec conformance",
    "enforce-mapping-spec.kiro.hook":
        "Blocks progression until a per-source mapping spec exists",
    "backup-before-load.kiro.hook":
        "Reminds you to back up before loading",
    "run-tests-after-change.kiro.hook":
        "Reminds you to run tests after code changes",
    "verify-generated-code.kiro.hook":
        "Prompts the agent to run new code on sample data",
    "enforce-visualization-offers.kiro.hook":
        "Safety net for visualization offers in Modules 3, 5, 7, 8",
    "validate-benchmark-results.kiro.hook":
        "Validates Module 8 benchmark output metrics",
    "security-scan-on-save.kiro.hook":
        "Re-runs the vulnerability scanner during Module 9",
    "validate-alert-config.kiro.hook":
        "Validates Module 10 monitoring alert rules",
    "deployment-phase-gate.kiro.hook":
        "Enforces the Module 11 packaging-to-deployment gate",
    # Any-module hooks
    "backup-project-on-request.kiro.hook":
        "Runs a project backup on manual trigger",
    "error-recovery-context.kiro.hook":
        "Consults pitfalls on non-zero shell exits",
    "git-commit-reminder.kiro.hook":
        "Reminds you to commit progress after completing a module",
    "module-completion-celebration.kiro.hook":
        "Celebrates module completion and points to the next step",
    "module-recap-append.kiro.hook":
        "Appends a structured recap section to docs/bootcamp_recap.md when a "
        "module is completed",
    "session-log-events.kiro.hook":
        "Logs file create/modify/delete and MCP tool calls to the session log "
        "after write operations",
}


# ---------------------------------------------------------------------------
# Essential / capture-critical hook sets (hook ids, no ``.kiro.hook`` suffix)
# ---------------------------------------------------------------------------

# Fallback critical set used only if hook-categories.yaml cannot be read.
CRITICAL_FALLBACK: set[str] = {
    "ask-bootcamper",
    "code-style-check",
    "commonmark-validation",
    "review-bootcamper-input",
    "write-policy-gate",
}

# Capture-critical hooks: the completion-summary / journey-fidelity capture
# hooks plus the closing-question owner.  Both install paths must cover these.
CAPTURE_CRITICAL: set[str] = {
    "session-log-events",
    "module-recap-append",
    "ask-bootcamper",
}


def load_critical_hooks(categories_path: Path = DEFAULT_CATEGORIES) -> set[str]:
    """Read the critical hook ids from ``hook-categories.yaml``.

    Derives the critical set from the categories file rather than a separately
    maintained duplicate list.  Falls back to :data:`CRITICAL_FALLBACK` if the
    file is missing or unreadable so the installer stays functional.

    Args:
        categories_path: Path to ``hook-categories.yaml``.

    Returns:
        The set of critical hook ids (without the ``.kiro.hook`` suffix).
    """
    try:
        text = categories_path.read_text(encoding="utf-8")
    except OSError:
        return set(CRITICAL_FALLBACK)

    critical: set[str] = set()
    in_block = False
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.endswith(":"):
            in_block = stripped[:-1].strip() == "critical"
            continue
        if in_block and stripped.startswith("- "):
            critical.add(stripped[2:].strip())

    return critical or set(CRITICAL_FALLBACK)


# Essential = critical hooks (from hook-categories.yaml) ∪ capture-critical hooks.
ESSENTIAL: set[str] = load_critical_hooks() | CAPTURE_CRITICAL


# ---------------------------------------------------------------------------
# Hook discovery
# ---------------------------------------------------------------------------


def _hook_id(filename: str) -> str:
    """Return the hook id (filename without the ``.kiro.hook`` suffix)."""
    suffix = ".kiro.hook"
    return filename[: -len(suffix)] if filename.endswith(suffix) else filename


def _derive_display_name(filename: str) -> str:
    """Derive a fallback display name from a hook filename."""
    return _hook_id(filename).replace("-", " ").title()


def _read_hook_name(hook_file: Path) -> str | None:
    """Read the ``name`` field from a ``.kiro.hook`` file, or None on failure."""
    try:
        data = json.loads(hook_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    name = data.get("name")
    return name if isinstance(name, str) and name.strip() else None


def discover_hooks(power_dir: Path) -> list[tuple[str, str, str]]:
    """Discover installable hooks from the power hooks directory.

    The authoritative installed set is the ``*.kiro.hook`` glob; display names
    come from each hook file's ``name`` field, and descriptions come from the
    :data:`HOOK_METADATA` overlay (with a derived fallback).

    Args:
        power_dir: Path to the power's hooks directory.

    Returns:
        A list of ``(filename, display_name, description)`` tuples, sorted by
        filename.
    """
    discovered: list[tuple[str, str, str]] = []
    for hook_file in sorted(power_dir.glob("*.kiro.hook")):
        filename = hook_file.name
        name = _read_hook_name(hook_file) or _derive_display_name(filename)
        desc = HOOK_METADATA.get(filename) or (
            "(no description — add to HOOK_METADATA in install_hooks.py)"
        )
        discovered.append((filename, name, desc))
    return discovered


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------


def install_hooks(
    hooks_to_install: list[tuple[str, str, str]],
    power_dir: Path,
    user_dir: Path,
) -> tuple[int, int]:
    """Copy each hook in *hooks_to_install* from *power_dir* into *user_dir*.

    Args:
        hooks_to_install: ``(filename, name, description)`` tuples to install.
        power_dir: Source power hooks directory.
        user_dir: Destination ``.kiro/hooks`` directory.

    Returns:
        A ``(installed, skipped)`` count pair.
    """
    installed = 0
    skipped = 0
    for filename, name, _ in hooks_to_install:
        src = power_dir / filename
        dst = user_dir / filename
        if not src.is_file():
            print(f"  {yellow('⚠')} {name}: source file not found")
            continue
        if dst.is_file():
            print(f"  {yellow('⚠')} {name}: already installed (skipping)")
            skipped += 1
        else:
            shutil.copy2(src, dst)
            print(f"  {green('✓')} {name}: installed")
            installed += 1
    return installed, skipped


def install_all(
    hooks: list[tuple[str, str, str]],
    power_dir: Path,
    user_dir: Path,
) -> tuple[int, int]:
    """Install every discovered hook and print a summary."""
    print(cyan("Installing all hooks..."))
    print()
    installed, skipped = install_hooks(hooks, power_dir, user_dir)
    print()
    print(green("Installation complete!"))
    print(f"  Installed: {installed} hooks")
    print(f"  Skipped:   {skipped} hooks (already installed)")
    return installed, skipped


def install_essential(
    hooks: list[tuple[str, str, str]],
    power_dir: Path,
    user_dir: Path,
) -> tuple[int, int]:
    """Install only the essential (critical ∪ capture-critical) hooks."""
    print(cyan("Installing essential hooks..."))
    print()
    essential = [h for h in hooks if _hook_id(h[0]) in ESSENTIAL]
    installed, skipped = install_hooks(essential, power_dir, user_dir)
    print()
    print(green("Installation complete!"))
    print(f"  Installed: {installed} essential hooks")
    print(f"  Skipped:   {skipped} essential hooks (already installed)")
    return installed, skipped


def print_next_steps(user_dir: Path) -> None:
    """Print the post-install guidance block."""
    print()
    print(cyan("Next Steps:"))
    print("  1. Hooks are now active in your project")
    print(f"  2. View installed hooks in: {user_dir}")
    print("  3. Disable a hook: edit the .hook file and set 'enabled: false'")
    print("  4. Remove a hook: delete the file from .kiro/hooks/")
    print()
    print(green("Happy coding!"))


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------


def print_banner() -> None:
    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  Senzing Bootcamp - Hook Installer                       " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()


def run_interactive(
    hooks: list[tuple[str, str, str]],
    power_dir: Path,
    user_dir: Path,
) -> int:
    """Run the interactive installer menu.

    This is the only code path that reads from standard input. It is reached
    only when no non-interactive flag is supplied.

    Args:
        hooks: Discovered hooks.
        power_dir: Source power hooks directory.
        user_dir: Destination ``.kiro/hooks`` directory.

    Returns:
        Process exit code (0 on success, 1 on invalid option).
    """
    # Show available hooks
    print(cyan("Available Hooks:"))
    print()
    for filename, name, desc in hooks:
        print(f"  {green('✓')} {name}")
        print(f"    {cyan('→')} {desc}")
    print()

    print(cyan("Installation Options:"))
    print()
    print("  A) Install all hooks (recommended)")
    print("  B) Install essential hooks only (critical + capture hooks)")
    print("  C) Select hooks individually")
    print("  Q) Quit")
    print()
    choice = input("Choose an option (A/B/C/Q): ").strip().upper()
    print()

    if choice == "A":
        install_all(hooks, power_dir, user_dir)

    elif choice == "B":
        install_essential(hooks, power_dir, user_dir)

    elif choice == "C":
        print(cyan("Select hooks to install:"))
        print()
        for filename, name, _ in hooks:
            src = power_dir / filename
            dst = user_dir / filename
            if not src.is_file():
                continue
            if dst.is_file():
                print(f"  {yellow('⚠')} {name}: already installed (skipping)")
                continue
            resp = input(f"  Install {name}? (y/N): ").strip().lower()
            if resp == "y":
                shutil.copy2(src, dst)
                print(f"  {green('✓')} {name}: installed")
            else:
                print(f"  {name}: skipped")
        print()
        print(green("Installation complete!"))

    elif choice == "Q":
        print("Installation cancelled.")
        return 0
    else:
        print("Invalid option. Installation cancelled.")
        return 1

    print_next_steps(user_dir)
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on success, 1 on error).
    """
    parser = argparse.ArgumentParser(
        description="Install Senzing Bootcamp hooks into .kiro/hooks.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--all",
        action="store_true",
        help="Non-interactive: install every discovered hook (no stdin).",
    )
    mode.add_argument(
        "--essential",
        action="store_true",
        help="Non-interactive: install only the essential hook set (no stdin).",
    )
    parser.add_argument(
        "--power-dir",
        type=Path,
        default=DEFAULT_POWER_HOOKS,
        help=f"Path to the power hooks directory (default: {DEFAULT_POWER_HOOKS}).",
    )
    parser.add_argument(
        "--user-dir",
        type=Path,
        default=DEFAULT_USER_HOOKS,
        help=f"Path to the destination .kiro/hooks directory "
        f"(default: {DEFAULT_USER_HOOKS}).",
    )

    args = parser.parse_args(argv)

    power_hooks: Path = args.power_dir
    user_hooks: Path = args.user_dir

    print_banner()

    if not power_hooks.is_dir():
        print(
            red(f"ERROR: Power hooks directory not found: {power_hooks}"),
            file=sys.stderr,
        )
        print(
            "Make sure you're running this from a Senzing Bootcamp project.",
            file=sys.stderr,
        )
        return 1

    user_hooks.mkdir(parents=True, exist_ok=True)

    hooks = discover_hooks(power_hooks)
    if not hooks:
        print(
            red(f"ERROR: No hook files found in {power_hooks}"),
            file=sys.stderr,
        )
        return 1

    if args.all:
        install_all(hooks, power_hooks, user_hooks)
        print_next_steps(user_hooks)
        return 0

    if args.essential:
        install_essential(hooks, power_hooks, user_hooks)
        print_next_steps(user_hooks)
        return 0

    return run_interactive(hooks, power_hooks, user_hooks)


if __name__ == "__main__":
    sys.exit(main())
