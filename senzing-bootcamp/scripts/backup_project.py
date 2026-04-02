#!/usr/bin/env python3
"""Senzing Boot Camp Project Backup Script.

Creates a timestamped ZIP archive of all project data.
Cross-platform: works on Linux, macOS, and Windows.
"""

import fnmatch
import os
import sys
import zipfile
from datetime import datetime
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


EXCLUDE_PATTERNS = [
    "*.pyc", "__pycache__", "target", "bin", "obj", "node_modules", "dist",
    ".DS_Store", "*.swp", "*.swo", "*~", ".env", ".git", ".history",
    "backups", "venv", ".venv", "data/temp",
]

BACKUP_ITEMS = [
    "database", "data", "licenses", "config", "src", "scripts", "docs",
    ".env.example", "README.md",
]


def _is_excluded(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(os.path.basename(rel_path), pat):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, pat):
                return True
    return False



def main():
    # Resolve project root (parent of scripts/)
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"senzing-bootcamp-backup_{timestamp}"
    backups_dir = Path("backups")
    backups_dir.mkdir(exist_ok=True)
    backup_file = backups_dir / f"{backup_name}.zip"

    print(green("Senzing Boot Camp - Project Backup"))
    print("======================================")
    print()

    # Determine what to back up
    items_to_backup = []
    print("Backing up the following items:")
    for item in BACKUP_ITEMS:
        if os.path.exists(item):
            print(f"  ✓ {item}")
            items_to_backup.append(item)
        else:
            print(f"  - {item} (not found, skipping)")
    print()

    # Create ZIP
    print("Compressing files...")
    file_count = 0
    with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in items_to_backup:
            item_path = Path(item)
            if item_path.is_file():
                if not _is_excluded(item):
                    zf.write(item)
                    file_count += 1
            elif item_path.is_dir():
                for root, dirs, files in os.walk(item):
                    # Prune excluded directories in-place
                    dirs[:] = [d for d in dirs if not _is_excluded(os.path.join(root, d))]
                    for f in files:
                        fpath = os.path.join(root, f)
                        if not _is_excluded(fpath):
                            zf.write(fpath)
                            file_count += 1

    size_bytes = backup_file.stat().st_size
    if size_bytes >= 1024 * 1024:
        size_str = f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        size_str = f"{size_bytes / 1024:.0f}KB"

    print()
    print(green("✓ Backup created successfully!"))
    print()
    print("Backup details:")
    print(f"  File:  {backup_file}")
    print(f"  Size:  {size_str}")
    print(f"  Files: {file_count}")
    print()
    print("To restore this backup:")
    print(f"  python scripts/restore_project.py {backup_file}")
    print()

    # List recent backups
    zips = sorted(backups_dir.glob("*.zip"))
    if zips:
        print("Recent backups:")
        for z in zips[-5:]:
            sz = z.stat().st_size
            label = f"{sz / (1024 * 1024):.1f}MB" if sz >= 1024 * 1024 else f"{sz / 1024:.0f}KB"
            print(f"  {z} ({label})")
        print()

    if len(zips) > 10:
        print(yellow(f"Note: You have {len(zips)} backups. Consider cleaning up old backups."))
        print()

    print(green("Backup complete!"))


if __name__ == "__main__":
    main()
