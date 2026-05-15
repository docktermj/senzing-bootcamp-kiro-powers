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
    ("ask-bootcamper.kiro.hook", "to wait for your answer",
     "Owns closing questions and feedback reminders"),
    ("review-bootcamper-input.kiro.hook", "to review what you said",
     "Routes feedback and status trigger phrases"),
    ("code-style-check.kiro.hook", "to check code style",
     "Ensures code follows language-appropriate standards"),
    ("commonmark-validation.kiro.hook", "to check Markdown style",
     "Validates Markdown files follow CommonMark spec"),
    ("enforce-file-path-policies.kiro.hook", "to make sure the file is in the project directory",
     "Enforces feedback and working-directory path policies"),
    # Module hooks
    ("validate-business-problem.kiro.hook", "to validate your business problem",
     "Validates Module 1 problem definition before proceeding"),
    ("verify-sdk-setup.kiro.hook", "to verify SDK setup",
     "Re-verifies SDK during Module 2 config changes"),
    ("verify-demo-results.kiro.hook", "to verify demo results",
     "Verifies Module 3 system verification against TruthSet"),
    ("gate-module3-visualization.kiro.hook", "to gate Module 3 completion on visualization step",
     "Blocks Module 3 completion until visualization step is done or skipped"),
    ("validate-data-files.kiro.hook", "to validate data files",
     "Checks data file format and readability when added to data/raw/"),
    ("data-quality-check.kiro.hook", "to check data quality",
     "Validates quality when transformations change"),
    ("analyze-after-mapping.kiro.hook", "to analyze mapped data",
     "Validates transformed data quality and Entity Spec conformance"),
    ("enforce-mapping-spec.kiro.hook", "to enforce the mapping specification",
     "Blocks progression until per-source mapping spec exists"),
    ("backup-before-load.kiro.hook", "to remind you to back up before loading",
     "Reminds to backup before loading"),
    ("run-tests-after-change.kiro.hook", "to remind you to run tests",
     "Reminds to run tests after code changes"),
    ("verify-generated-code.kiro.hook", "to verify generated code",
     "Prompts the agent to run new code on sample data"),
    ("enforce-visualization-offers.kiro.hook", "to offer visualizations",
     "Safety net for visualization offers in Modules 3, 5, 7, 8"),
    ("validate-benchmark-results.kiro.hook", "to validate benchmark results",
     "Validates Module 8 benchmark output metrics"),
    ("security-scan-on-save.kiro.hook", "to run a security scan",
     "Re-runs vulnerability scanner during Module 9"),
    ("validate-alert-config.kiro.hook", "to validate alert configuration",
     "Validates Module 10 monitoring alert rules"),
    ("deployment-phase-gate.kiro.hook", "to check the deployment phase gate",
     "Enforces Module 11 packaging-to-deployment gate"),
    # Any-module hooks (installed during onboarding)
    ("backup-project-on-request.kiro.hook", "to back up your project",
     "Runs project backup on manual trigger"),
    ("error-recovery-context.kiro.hook", "to help recover from errors",
     "Consults pitfalls on non-zero shell exits"),
    ("git-commit-reminder.kiro.hook", "to remind you to commit",
     "Reminds to commit progress after completing a module"),
    ("module-completion-celebration.kiro.hook", "to celebrate module completion",
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
