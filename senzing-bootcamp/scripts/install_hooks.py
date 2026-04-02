#!/usr/bin/env python3
"""Senzing Boot Camp - Hook Installer.

Installs all recommended hooks with one command.
Cross-platform: works on Linux, macOS, and Windows.
"""

import os
import shutil
import sys
from pathlib import Path


def color_supported():
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") or "ANSICON" in os.environ
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = color_supported()


def c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c("0;32", t)
def yellow(t): return c("1;33", t)
def blue(t): return c("0;34", t)
def cyan(t): return c("0;36", t)
def red(t): return c("0;31", t)


HOOKS = [
    ("code-style-check.kiro.hook", "Code Style Check", "Ensures code follows language-appropriate standards"),
    ("data-quality-check.kiro.hook", "Data Quality Check", "Validates quality when transformations change"),
    ("backup-before-load.kiro.hook", "Backup Before Load", "Reminds to backup before loading"),
    ("validate-senzing-json.kiro.hook", "Validate Senzing JSON", "Validates output format against SGES"),
    ("backup-project-on-request.kiro.hook", "Backup on Request", "Auto-backup when user requests it"),
    ("commonmark-validation.kiro.hook", "CommonMark Validation", "Validates Markdown files follow CommonMark spec"),
    ("verify-senzing-facts.kiro.hook", "Verify Senzing Facts", "Verifies Senzing content via MCP before writing"),
    ("analyze-after-mapping.kiro.hook", "Analyze After Mapping", "Validates transformed data before loading"),
    ("run-tests-after-change.kiro.hook", "Run Tests After Change", "Reminds to run tests after code changes"),
]

ESSENTIAL = {
    "code-style-check.kiro.hook",
    "backup-before-load.kiro.hook",
    "backup-project-on-request.kiro.hook",
}



def install_hooks(hooks_to_install, power_dir, user_dir):
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


def main():
    project_root = Path(__file__).resolve().parent.parent
    power_hooks = project_root / "senzing-bootcamp" / "hooks"
    user_hooks = project_root / ".kiro" / "hooks"

    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  Senzing Boot Camp - Hook Installer                       " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    if not power_hooks.is_dir():
        print(yellow(f"⚠ Power hooks directory not found: {power_hooks}"))
        print("Make sure you're running this from a Senzing Boot Camp project.")
        sys.exit(1)

    user_hooks.mkdir(parents=True, exist_ok=True)

    # Show available hooks
    print(cyan("Available Hooks:"))
    print()
    for filename, name, desc in HOOKS:
        if (power_hooks / filename).is_file():
            print(f"  {green('✓')} {name}")
            print(f"    {cyan('→')} {desc}")
        else:
            print(f"  {yellow('⚠')} {name} (file not found)")
    print()

    print(cyan("Installation Options:"))
    print()
    print("  A) Install all hooks (recommended)")
    print("  B) Install essential hooks only (code style, backup)")
    print("  C) Select hooks individually")
    print("  Q) Quit")
    print()
    choice = input("Choose an option (A/B/C/Q): ").strip().upper()
    print()

    if choice == "A":
        print(cyan("Installing all hooks..."))
        print()
        installed, skipped = install_hooks(HOOKS, power_hooks, user_hooks)
        print()
        print(green("Installation complete!"))
        print(f"  Installed: {installed} hooks")
        print(f"  Skipped:   {skipped} hooks (already installed)")

    elif choice == "B":
        print(cyan("Installing essential hooks..."))
        print()
        essential = [h for h in HOOKS if h[0] in ESSENTIAL]
        installed, skipped = install_hooks(essential, power_hooks, user_hooks)
        print()
        print(green("Installation complete!"))
        print(f"  Installed: {installed} essential hooks")

    elif choice == "C":
        print(cyan("Select hooks to install:"))
        print()
        for filename, name, _ in HOOKS:
            src = power_hooks / filename
            dst = user_hooks / filename
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
        sys.exit(0)
    else:
        print("Invalid option. Installation cancelled.")
        sys.exit(1)

    print()
    print(cyan("Next Steps:"))
    print("  1. Hooks are now active in your project")
    print(f"  2. View installed hooks in: {user_hooks}")
    print("  3. Disable a hook: edit the .hook file and set 'enabled: false'")
    print("  4. Remove a hook: delete the file from .kiro/hooks/")
    print()
    print(green("Happy coding!"))


if __name__ == "__main__":
    main()
