#!/usr/bin/env python3
"""Senzing Bootcamp - Hook Installer.

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
    # Critical hooks (installed during onboarding)
    ("ask-bootcamper.kiro.hook", "Ask Bootcamper",
     "Owns closing questions and feedback reminders"),
    ("review-bootcamper-input.kiro.hook", "Review Bootcamper Input",
     "Routes feedback and status trigger phrases"),
    ("code-style-check.kiro.hook", "Code Style Check",
     "Ensures code follows language-appropriate standards"),
    ("commonmark-validation.kiro.hook", "CommonMark Validation",
     "Validates Markdown files follow CommonMark spec"),
    ("enforce-file-path-policies.kiro.hook", "Enforce File Path Policies",
     "Enforces feedback and working-directory path policies"),
    # Module hooks
    ("validate-business-problem.kiro.hook", "Validate Business Problem",
     "Validates Module 1 problem definition before proceeding"),
    ("verify-sdk-setup.kiro.hook", "Verify SDK Setup",
     "Re-verifies SDK during Module 2 config changes"),
    ("verify-demo-results.kiro.hook", "Verify Demo Results",
     "Verifies Module 3 system verification against TruthSet"),
    ("validate-data-files.kiro.hook", "Validate Data Files",
     "Checks data file format and readability when added to data/raw/"),
    ("data-quality-check.kiro.hook", "Data Quality Check",
     "Validates quality when transformations change"),
    ("analyze-after-mapping.kiro.hook", "Analyze After Mapping",
     "Validates transformed data quality and Entity Spec conformance"),
    ("enforce-mapping-spec.kiro.hook", "Enforce Mapping Specification",
     "Blocks progression until per-source mapping spec exists"),
    ("backup-before-load.kiro.hook", "Backup Before Load",
     "Reminds to backup before loading"),
    ("run-tests-after-change.kiro.hook", "Run Tests After Change",
     "Reminds to run tests after code changes"),
    ("verify-generated-code.kiro.hook", "Verify Generated Code",
     "Prompts the agent to run new code on sample data"),
    ("enforce-visualization-offers.kiro.hook", "Enforce Visualization Offers",
     "Safety net for visualization offers in Modules 3, 5, 7, 8"),
    ("validate-benchmark-results.kiro.hook", "Validate Benchmark Results",
     "Validates Module 8 benchmark output metrics"),
    ("security-scan-on-save.kiro.hook", "Security Scan on Save",
     "Re-runs vulnerability scanner during Module 9"),
    ("validate-alert-config.kiro.hook", "Validate Alert Configuration",
     "Validates Module 10 monitoring alert rules"),
    ("deployment-phase-gate.kiro.hook", "Deployment Phase Gate",
     "Enforces Module 11 packaging-to-deployment gate"),
    # Any-module hooks (installed during onboarding)
    ("backup-project-on-request.kiro.hook", "Backup on Request",
     "Runs project backup on manual trigger"),
    ("error-recovery-context.kiro.hook", "Error Recovery Context",
     "Consults pitfalls on non-zero shell exits"),
    ("git-commit-reminder.kiro.hook", "Git Commit Reminder",
     "Reminds to commit progress after completing a module"),
    ("module-completion-celebration.kiro.hook", "Module Completion Celebration",
     "Celebrates module completion and points to the next step"),
]

ESSENTIAL = {
    "ask-bootcamper.kiro.hook",
    "review-bootcamper-input.kiro.hook",
    "code-style-check.kiro.hook",
    "commonmark-validation.kiro.hook",
    "enforce-file-path-policies.kiro.hook",
    "backup-project-on-request.kiro.hook",
    "error-recovery-context.kiro.hook",
    "git-commit-reminder.kiro.hook",
    "module-completion-celebration.kiro.hook",
}


def discover_hooks(power_dir):
    """Discover hook files, using known metadata when available."""
    known = {filename: (name, desc) for filename, name, desc in HOOKS}
    discovered = []
    for hook_file in sorted(power_dir.glob("*.kiro.hook")):
        filename = hook_file.name
        if filename in known:
            name, desc = known[filename]
        else:
            # Derive a display name from the filename
            name = filename.replace(".kiro.hook", "").replace("-", " ").title()
            desc = "(no description — add to HOOKS list in install_hooks.py)"
        discovered.append((filename, name, desc))
    return discovered



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
    print(blue("║") + "  Senzing Bootcamp - Hook Installer                       " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    if not power_hooks.is_dir():
        print(yellow(f"⚠ Power hooks directory not found: {power_hooks}"))
        print("Make sure you're running this from a Senzing Bootcamp project.")
        sys.exit(1)

    user_hooks.mkdir(parents=True, exist_ok=True)

    # Discover all hooks from the power directory
    hooks = discover_hooks(power_hooks)

    if not hooks:
        print(yellow("⚠ No hook files found in power directory."))
        sys.exit(1)

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
    print("  B) Install essential hooks only (code style, backup)")
    print("  C) Select hooks individually")
    print("  Q) Quit")
    print()
    choice = input("Choose an option (A/B/C/Q): ").strip().upper()
    print()

    if choice == "A":
        print(cyan("Installing all hooks..."))
        print()
        installed, skipped = install_hooks(hooks, power_hooks, user_hooks)
        print()
        print(green("Installation complete!"))
        print(f"  Installed: {installed} hooks")
        print(f"  Skipped:   {skipped} hooks (already installed)")

    elif choice == "B":
        print(cyan("Installing essential hooks..."))
        print()
        essential = [h for h in hooks if h[0] in ESSENTIAL]
        installed, skipped = install_hooks(
            essential, power_hooks, user_hooks
        )
        print()
        print(green("Installation complete!"))
        print(f"  Installed: {installed} essential hooks")

    elif choice == "C":
        print(cyan("Select hooks to install:"))
        print()
        for filename, name, _ in hooks:
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
