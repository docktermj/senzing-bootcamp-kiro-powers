#!/usr/bin/env python3
"""Senzing Bootcamp - Module Rollback Script.

Reverts the artifacts produced by a specific bootcamp module.
Cross-platform: works on Linux, macOS, and Windows.
"""
import argparse
import dataclasses
import json
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# -- Color utilities --------------------------------------------------------

def color_supported():
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return (os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM")
                or "ANSICON" in os.environ)
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = color_supported()


def c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c("0;32", t)
def red(t): return c("0;31", t)
def yellow(t): return c("1;33", t)

# -- Data models & constants ------------------------------------------------

@dataclasses.dataclass
class ModuleArtifacts:
    files: list
    directories: list
    modifies_database: bool

ARTIFACT_MANIFEST = {
    1:  ModuleArtifacts(files=["docs/business_problem.md"], directories=[], modifies_database=False),
    2:  ModuleArtifacts(files=["database/G2C.db", "config/bootcamp_preferences.yaml"], directories=[], modifies_database=False),
    3:  ModuleArtifacts(files=[], directories=["src/quickstart_demo"], modifies_database=False),
    4:  ModuleArtifacts(files=["docs/data_source_locations.md"], directories=["data/raw"], modifies_database=False),
    5:  ModuleArtifacts(files=["docs/data_source_evaluation.md", "docs/data_quality_report.md"], directories=["src/transform", "data/transformed"], modifies_database=False),
    6:  ModuleArtifacts(files=["docs/loading_strategy.md"], directories=["src/load"], modifies_database=True),
    7:  ModuleArtifacts(files=["docs/results_validation.md"], directories=["src/query"], modifies_database=False),
    8:  ModuleArtifacts(files=["docs/performance_requirements.md", "docs/performance_report.md"], directories=["tests/performance"], modifies_database=False),
    9:  ModuleArtifacts(files=["docs/security_checklist.md"], directories=[], modifies_database=False),
    10: ModuleArtifacts(files=["docs/monitoring_setup.md"], directories=["monitoring"], modifies_database=False),
    11: ModuleArtifacts(files=["docs/deployment_plan.md"], directories=[], modifies_database=False),
}

MODULE_NAMES = {
    1: "Business Problem", 2: "SDK Setup", 3: "Quick Demo",
    4: "Data Collection", 5: "Data Quality & Mapping",
    6: "Load Data", 7: "Query & Visualize",
    8: "Performance Testing", 9: "Security Hardening",
    10: "Monitoring", 11: "Deployment",
}
PREREQUISITES = {
    3:  [2],
    4:  [1],
    5:  [4],
    6:  [2, 5],
    7:  [6],
    8:  [7],
    9:  [8],
    10: [9],
    11: [10],
}


def get_downstream_modules(module):
    """Return sorted list of modules that transitively depend on the given module."""
    downstream = set()
    queue = [module]
    while queue:
        current = queue.pop(0)
        for mod, prereqs in PREREQUISITES.items():
            if current in prereqs and mod not in downstream:
                downstream.add(mod)
                queue.append(mod)
    return sorted(downstream)


def get_completed_downstream(module, modules_completed):
    """Return sorted list of completed modules that depend on the given module."""
    downstream = get_downstream_modules(module)
    return sorted(m for m in downstream if m in modules_completed)

# -- CLI parsing ------------------------------------------------------------

def parse_args(argv=None):
    """Parse command-line arguments. Returns namespace or exits on error."""
    parser = argparse.ArgumentParser(
        description="Roll back a specific bootcamp module's artifacts.",
    )
    parser.add_argument(
        "--module", type=int, required=True,
        help="Module number (1-11) to roll back",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview rollback without making changes",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip confirmation prompts",
    )
    args = parser.parse_args(argv)
    if args.module < 1 or args.module > 11:
        parser.error(f"Module must be between 1 and 11, got {args.module}")
    return args

# -- Progress file operations -----------------------------------------------

def read_progress_file(path):
    """Read and parse progress JSON. Returns dict or None if missing/invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, ValueError):
        print(yellow("Warning: Progress file contains invalid JSON."))
        print(yellow("  Consider running: python scripts/repair_progress.py"))
        return None


def write_progress_file(path, data):
    """Write progress dict with 2-space indent and trailing newline."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def compute_progress_update(progress_data, module):
    """Return a new progress dict with module N rolled back. Pure function."""
    result = json.loads(json.dumps(progress_data))
    completed = result.get("modules_completed", [])
    if module in completed:
        completed = [m for m in completed if m != module]
        result["modules_completed"] = completed
    if result.get("current_module") == module:
        result["current_module"] = module
        result["current_step"] = None

    step_history = result.get("step_history", {})
    module_key = str(module)
    if module_key in step_history:
        del step_history[module_key]
        result["step_history"] = step_history

    return result

# -- Artifact removal -------------------------------------------------------

@dataclasses.dataclass
class RemovalResult:
    removed_files: list
    removed_dirs: list
    skipped_missing: list
    failed_items: list  # list of (path, error_message) tuples


def remove_artifacts(artifacts, project_root):
    """Remove files and directories listed in the manifest. Returns RemovalResult."""
    root = Path(project_root)
    removed_files = []
    removed_dirs = []
    skipped_missing = []
    failed_items = []

    for f in artifacts.files:
        fp = root / f
        if not fp.exists():
            skipped_missing.append(f)
            continue
        try:
            fp.unlink()
            removed_files.append(f)
        except PermissionError as e:
            print(yellow(f"Warning: Could not remove file {f}: {e}"))
            failed_items.append((f, str(e)))

    for d in artifacts.directories:
        dp = root / d
        if not dp.exists():
            skipped_missing.append(d)
            continue
        try:
            shutil.rmtree(dp)
            removed_dirs.append(d)
        except PermissionError as e:
            print(yellow(f"Warning: Could not remove directory {d}: {e}"))
            failed_items.append((d, str(e)))

    return RemovalResult(
        removed_files=removed_files,
        removed_dirs=removed_dirs,
        skipped_missing=skipped_missing,
        failed_items=failed_items,
    )

# -- Database handling ------------------------------------------------------

def find_latest_backup(backups_dir):
    """Scan backups/ for the most recent ZIP file. Return path or None."""
    bd = Path(backups_dir)
    if not bd.is_dir():
        return None
    zips = sorted(bd.glob("*.zip"))
    if not zips:
        return None
    return str(sorted(zips)[-1])


def restore_database_from_backup(backup_path, project_root):
    """Extract only the database/ directory from the backup ZIP. Returns bool."""
    try:
        with zipfile.ZipFile(backup_path, "r") as zf:
            db_entries = [n for n in zf.namelist() if n.startswith("database/")]
            if not db_entries:
                print(yellow("Warning: Backup does not contain a database/ directory."))
                return False
            for entry in db_entries:
                zf.extract(entry, project_root)
        return True
    except Exception as e:
        print(red(f"Error restoring database: {e}"))
        return False

# -- Rollback logging -------------------------------------------------------

@dataclasses.dataclass
class RollbackLogEntry:
    timestamp: str
    module: int
    removed_files: list
    removed_dirs: list
    skipped_missing: list
    failed_items: list
    database_restored: object  # bool or None
    backup_used: object        # str or None
    warnings: list


def build_log_entry(module, removal_result, database_restored, backup_used, warnings):
    """Construct a log entry from rollback results. Pure function."""
    return RollbackLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        module=module,
        removed_files=list(removal_result.removed_files),
        removed_dirs=list(removal_result.removed_dirs),
        skipped_missing=list(removal_result.skipped_missing),
        failed_items=[item[0] for item in removal_result.failed_items],
        database_restored=database_restored,
        backup_used=backup_used,
        warnings=list(warnings),
    )


def serialize_log_entry(entry):
    """Serialize log entry to a single JSON line (no trailing newline)."""
    return json.dumps(dataclasses.asdict(entry), separators=(",", ":"))


def append_log_entry(log_path, entry_line):
    """Append a JSON line to the log file, creating logs/ dir if needed."""
    lp = Path(log_path)
    try:
        lp.parent.mkdir(parents=True, exist_ok=True)
        with open(lp, "a", encoding="utf-8") as f:
            f.write(entry_line + "\n")
    except Exception as e:
        print(yellow(f"Warning: Could not write rollback log: {e}"))

# -- Dry-run report ---------------------------------------------------------

def format_dry_run_report(module, artifacts, existing_files, existing_dirs,
                          missing_items, backup_path, downstream_completed,
                          progress_changes):
    """Return a formatted string previewing all planned rollback actions. Pure function."""
    lines = []
    lines.append(f"Dry-run: Module {module} ({MODULE_NAMES.get(module, 'Unknown')}) rollback preview")
    lines.append("=" * 50)
    lines.append("")

    if existing_files:
        lines.append("Files to remove:")
        for f in existing_files:
            lines.append(f"  - {f}")
    if existing_dirs:
        lines.append("Directories to remove:")
        for d in existing_dirs:
            lines.append(f"  - {d}/")
    if missing_items:
        lines.append("Already missing (will skip):")
        for m in missing_items:
            lines.append(f"  - {m}")

    if artifacts.modifies_database:
        lines.append("")
        if backup_path:
            lines.append(f"Database: Would restore from backup: {backup_path}")
        else:
            lines.append("Database: No backup available — cannot restore database")

    if downstream_completed:
        lines.append("")
        lines.append("Warning — completed downstream modules that depend on this module:")
        for dm in downstream_completed:
            lines.append(f"  - Module {dm}: {MODULE_NAMES.get(dm, 'Unknown')}")

    if progress_changes:
        lines.append("")
        lines.append("Progress file changes:")
        for key, value in progress_changes.items():
            lines.append(f"  {key}: {value}")

    lines.append("")
    lines.append("No changes made (dry-run mode).")
    return "\n".join(lines)

# -- Orchestration helpers --------------------------------------------------

def _artifacts_exist(artifacts, project_root):
    """Check if any manifest artifacts exist on disk."""
    root = Path(project_root)
    for f in artifacts.files:
        if (root / f).exists():
            return True
    for d in artifacts.directories:
        if (root / d).exists():
            return True
    return False


def _classify_artifacts(artifacts, project_root):
    """Classify artifacts into existing files, dirs, and missing items."""
    root = Path(project_root)
    existing_files = [f for f in artifacts.files if (root / f).exists()]
    existing_dirs = [d for d in artifacts.directories if (root / d).exists()]
    missing = ([f for f in artifacts.files if not (root / f).exists()]
               + [d for d in artifacts.directories if not (root / d).exists()])
    return existing_files, existing_dirs, missing

# -- Main orchestration -----------------------------------------------------

def main(argv=None):
    """Parse args, execute rollback, return exit code."""
    args = parse_args(argv)
    module = args.module
    artifacts = ARTIFACT_MANIFEST[module]

    # Resolve project root (parent of scripts/)
    project_root = Path(__file__).resolve().parent.parent
    progress_path = project_root / "config" / "bootcamp_progress.json"
    backups_dir = project_root / "backups"
    log_path = project_root / "logs" / "rollback_log.jsonl"

    print(green(f"Senzing Bootcamp - Rollback Module {module}: {MODULE_NAMES[module]}"))
    print("=" * 50)

    # Read progress
    progress_data = read_progress_file(progress_path)
    modules_completed = (progress_data.get("modules_completed", [])
                         if progress_data else [])

    # Check nothing-to-rollback
    if module not in modules_completed and not _artifacts_exist(artifacts, project_root):
        print(f"Module {module} is not completed and has no artifacts on disk.")
        print("Nothing to roll back.")
        return 0

    # Classify artifacts
    existing_files, existing_dirs, missing_items = _classify_artifacts(
        artifacts, project_root)

    # Downstream check
    downstream_completed = get_completed_downstream(module, modules_completed)
    # Compute progress changes for preview
    progress_changes = {}
    if progress_data and module in modules_completed:
        progress_changes["modules_completed"] = f"remove {module}"
        if progress_data.get("current_module") == module:
            progress_changes["current_module"] = f"set to {module}"
            progress_changes["current_step"] = "cleared"
        if str(module) in progress_data.get("step_history", {}):
            progress_changes["step_history"] = f"remove entry for module {module}"
    # Find backup for DB modules
    backup_path = None
    if artifacts.modifies_database:
        backup_path = find_latest_backup(backups_dir)

    # --- Dry-run path ---
    if args.dry_run:
        report = format_dry_run_report(
            module, artifacts, existing_files, existing_dirs,
            missing_items, backup_path, downstream_completed,
            progress_changes,
        )
        print(report)
        return 0
    # --- Downstream dependency warning ---
    if downstream_completed:
        print(yellow("Warning: The following completed modules depend on this module:"))
        for dm in downstream_completed:
            print(yellow(f"  - Module {dm}: {MODULE_NAMES.get(dm, 'Unknown')}"))
        print()
        if not args.force:
            resp = input("Continue despite downstream dependencies? (y/N): ").strip()
            if resp not in ("y", "Y"):
                print("Rollback cancelled.")
                return 0
    # --- Confirmation prompt ---
    if not args.force:
        print("Planned actions:")
        for f in existing_files:
            print(f"  Remove file: {f}")
        for d in existing_dirs:
            print(f"  Remove dir:  {d}/")
        for m in missing_items:
            print(f"  Skip (missing): {m}")
        if artifacts.modifies_database:
            print(f"  Database: {'restore from ' + backup_path if backup_path else 'no backup available'}")
        resp = input("\nProceed with rollback? (y/N): ").strip()
        if resp not in ("y", "Y"):
            print("Rollback cancelled.")
            return 0
    # --- Execute removal ---
    print("\nRemoving artifacts...")
    removal_result = remove_artifacts(artifacts, project_root)
    warnings = []

    # --- Database rollback flow ---
    database_restored = None
    backup_used = None
    if artifacts.modifies_database:
        database_restored = False
        if backup_path:
            do_restore = args.force
            if not do_restore:
                resp = input(f"Restore database from backup {backup_path}? (y/N): ").strip()
                do_restore = resp in ("y", "Y")
            if do_restore:
                print(f"Restoring database from {backup_path}...")
                if restore_database_from_backup(backup_path, project_root):
                    database_restored, backup_used = True, backup_path
                    print(green("  Database restored successfully."))
                else:
                    warnings.append("Database restoration failed")
            else:
                print(yellow("Warning: Loaded records remain in the database."))
                print(yellow("  Consider running backup_project.py and manually resetting the database."))
                warnings.append("User declined database restoration")
        else:
            print(yellow("Warning: No backup available for database restoration."))
            print(yellow("  Re-run Module 2 (SDK Setup) to recreate a clean database."))
            warnings.append("No backup available for database restoration")
    # --- Update progress ---
    if progress_data is not None:
        updated = compute_progress_update(progress_data, module)
        write_progress_file(progress_path, updated)
        print("  Progress file updated.")
    else:
        if not Path(progress_path).exists():
            print(yellow("Warning: Progress file not found. Skipping progress update."))
        warnings.append("Progress file not updated")
    # --- Log ---
    entry = build_log_entry(module, removal_result, database_restored, backup_used, warnings)
    entry_line = serialize_log_entry(entry)
    append_log_entry(log_path, entry_line)
    # --- Summary ---
    print(f"\n{green(f'Rollback of Module {module} ({MODULE_NAMES[module]}) complete.')}")
    if removal_result.removed_files:
        print(f"  Removed files: {', '.join(removal_result.removed_files)}")
    if removal_result.removed_dirs:
        print(f"  Removed directories: {', '.join(removal_result.removed_dirs)}")
    if removal_result.skipped_missing:
        print(f"  Skipped (missing): {', '.join(removal_result.skipped_missing)}")
    if removal_result.failed_items:
        print(red(f"  Failed: {', '.join(p for p, _ in removal_result.failed_items)}"))
    if database_restored is True:
        print(green("  Database restored from backup."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
