#!/usr/bin/env python3
"""Senzing Bootcamp - Example Project Cloner.

Copies an example project to user's workspace.
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
def red(t): return c("0;31", t)
def yellow(t): return c("1;33", t)
def blue(t): return c("0;34", t)
def cyan(t): return c("0;36", t)


EXAMPLES = [
    ("simple-single-source", "Simple Single Source", "Basic customer deduplication"),
    ("multi-source-project", "Multi-Source Project", "Customer 360 with three sources"),
    ("production-deployment", "Production Deployment", "Complete production-ready system"),
]



def main():
    project_root = Path(__file__).resolve().parent.parent
    examples_dir = project_root / "senzing-bootcamp" / "examples"

    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  Senzing Bootcamp - Example Project Cloner               " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    if not examples_dir.is_dir():
        print(red(f"✗ Examples directory not found: {examples_dir}"))
        sys.exit(1)

    # List available examples
    print(cyan("Available Example Projects:"))
    print()
    available = []
    for i, (dirname, name, desc) in enumerate(EXAMPLES, 1):
        if (examples_dir / dirname).is_dir():
            print(f"  {green(str(i) + ')')} {cyan(name)}")
            print(f"     {desc}")
            print()
            available.append((dirname, name))

    if not available:
        print(red("No example projects found."))
        sys.exit(1)

    print("Options: 1-3) Clone an example   Q) Quit")
    choice = input("Choose an option: ").strip()

    if choice.upper() == "Q":
        print("Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(EXAMPLES):
            raise ValueError
    except ValueError:
        print(red("Invalid option."))
        sys.exit(1)

    dirname, name = EXAMPLES[idx][0], EXAMPLES[idx][1]
    source_dir = examples_dir / dirname

    if not source_dir.is_dir():
        print(red(f"✗ Example not found: {source_dir}"))
        sys.exit(1)

    # Ask destination
    print()
    print(cyan(f"Clone '{name}' to:"))
    print()
    print("  A) Current project (merge with existing files)")
    print("  B) New directory (create separate copy)")
    print("  Q) Quit")
    dest_choice = input("Choose an option (A/B/Q): ").strip().upper()

    if dest_choice == "Q":
        print("Cancelled.")
        return

    if dest_choice == "A":
        dest_dir = project_root
        print(yellow("⚠ Warning: This will merge files into your current project"))
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    elif dest_choice == "B":
        dir_name = input("Enter directory name: ").strip()
        dest_dir = project_root / dir_name
        if dest_dir.exists():
            print(red(f"✗ Directory already exists: {dest_dir}"))
            sys.exit(1)
        dest_dir.mkdir(parents=True)
        print(f"  {green('✓')} Created directory: {dest_dir}")
    else:
        print(red("Invalid option."))
        sys.exit(1)

    print()
    print(cyan("Cloning example project..."))
    print()

    copied = 0
    skipped = 0

    for item in source_dir.iterdir():
        dest_item = dest_dir / item.name

        # Skip README when merging into current project
        if dest_dir == project_root and item.name == "README.md":
            print(f"  {yellow('⚠')} Skipping README.md (preserving your existing README)")
            skipped += 1
            continue

        if item.is_dir():
            if dest_item.is_dir():
                print(f"  {yellow('⚠')} Merging directory: {item.name}")
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
            else:
                print(f"  {green('✓')} Copying directory: {item.name}")
                shutil.copytree(item, dest_item)
            copied += 1
        else:
            if dest_item.is_file():
                print(f"  {yellow('⚠')} File exists (skipping): {item.name}")
                skipped += 1
            else:
                print(f"  {green('✓')} Copying file: {item.name}")
                shutil.copy2(item, dest_item)
                copied += 1

    print()
    print(green("✓ Clone complete!"))
    print(f"  Copied:  {copied} items")
    print(f"  Skipped: {skipped} items (already exist)")
    print()
    print(cyan("Next Steps:"))
    print(f"  1. Review the example files in: {dest_dir}")
    print(f"  2. Read the example README")
    print("  3. Customize for your use case")
    print()
    print(green("Happy coding!"))


if __name__ == "__main__":
    main()
