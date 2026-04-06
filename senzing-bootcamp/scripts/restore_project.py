#!/usr/bin/env python3
"""Senzing Bootcamp Project Restore Script.

Restores a project from a backup ZIP file.
Cross-platform: works on Linux, macOS, and Windows.
"""

import os
import sys
import zipfile
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


def main():
    project_root = Path(__file__).resolve().parent.parent

    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_project.py <backup-file.zip> [restore-directory]")
        print()
        print("Examples:")
        print("  python scripts/restore_project.py backups/senzing-bootcamp-backup_20260326_143022.zip")
        print("  python scripts/restore_project.py backups/senzing-bootcamp-backup_20260326_143022.zip ~/new-project")
        print()
        backups_dir = project_root / "backups"
        zips = sorted(backups_dir.glob("*.zip")) if backups_dir.is_dir() else []
        if zips:
            print("Available backups:")
            for z in zips:
                sz = z.stat().st_size
                label = f"{sz / (1024 * 1024):.1f}MB" if sz >= 1024 * 1024 else f"{sz / 1024:.0f}KB"
                print(f"  {z} ({label})")
        else:
            print("  No backups found in backups/ directory")
        sys.exit(1)

    backup_file = Path(sys.argv[1]).resolve()
    restore_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else project_root

    print(green("Senzing Bootcamp - Project Restore"))
    print("======================================")
    print()

    if not backup_file.is_file():
        print(red(f"Error: Backup file not found: {backup_file}"))
        sys.exit(1)

    if not zipfile.is_zipfile(backup_file):
        print(red(f"Error: Not a valid ZIP file: {backup_file}"))
        sys.exit(1)

    restore_dir.mkdir(parents=True, exist_ok=True)

    print("Restore details:")
    print(f"  Backup file: {backup_file}")
    print(f"  Restore to:  {restore_dir}")
    print()

    # Warn if restoring to non-empty directory
    if restore_dir != project_root and any(restore_dir.iterdir()):
        resp = input(yellow("Warning: Restore directory is not empty. Continue? (y/N): ")).strip()
        if resp.lower() != "y":
            print("Restore cancelled.")
            sys.exit(0)

    if restore_dir == project_root:
        resp = input(yellow("Warning: This will overwrite files in the current project. Continue? (y/N): ")).strip()
        if resp.lower() != "y":
            print("Restore cancelled.")
            sys.exit(0)

    # Show contents preview
    with zipfile.ZipFile(backup_file, "r") as zf:
        names = zf.namelist()
        print(f"Backup contains {len(names)} files.")
        print()

        print("Extracting backup...")
        zf.extractall(restore_dir)

    print()
    print(green("✓ Restore completed successfully!"))
    print()
    print(f"Restored to: {restore_dir}")
    print()

    # Check what was restored
    print("Restored items:")
    for item in ["database", "data", "licenses", "config", "src", "scripts", "docs"]:
        if (restore_dir / item).exists():
            print(f"  ✓ {item}")
    print()

    print("Next steps:")
    if restore_dir != project_root:
        print(f"  1. Navigate to {restore_dir}")
    print("  2. Review restored files")
    print("  3. Verify database integrity")
    print("  4. Test your Senzing installation")
    print()
    print(green("Restore complete!"))


if __name__ == "__main__":
    main()
