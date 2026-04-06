#!/usr/bin/env python3
"""Senzing Bootcamp - Status Command.

Shows current module, progress, and next steps.
Cross-platform: works on Linux, macOS, and Windows.
"""

import os
import re
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


MODULE_NAMES = {
    0: "SDK Setup", 1: "Quick Demo", 2: "Business Problem",
    3: "Data Collection", 4: "Data Quality", 5: "Data Mapping",
    6: "Single Source Loading", 7: "Multi-Source Orchestration",
    8: "Query & Validation", 9: "Performance Testing",
    10: "Security Hardening", 11: "Monitoring", 12: "Deployment",
}

NEXT_STEPS = {
    0:  ("Start Module 0: SDK Setup (30 min - 1 hr)", "Install and configure Senzing SDK"),
    1:  ("Start Module 1: Quick Demo (10-15 min)", "See entity resolution in action with sample data"),
    2:  ("Start Module 2: Business Problem (20-30 min)", "Define your problem and identify data sources"),
    3:  ("Start Module 3: Data Collection (10-15 min per source)", "Upload or link to data source files"),
    4:  ("Start Module 4: Data Quality (15-20 min per source)", "Evaluate data quality with automated scoring"),
    5:  ("Start Module 5: Data Mapping (1-2 hrs per source)", "Create transformation programs"),
    6:  ("Start Module 6: Single Source Loading (30 min per source)", "Load your first data source"),
    7:  ("Start Module 7: Multi-Source Orchestration (1-2 hrs)", "Manage dependencies between sources"),
    8:  ("Start Module 8: Query & Validation (1-2 hrs)", "Create query programs and validate results"),
    9:  ("Start Module 9: Performance Testing (1-2 hrs)", "Benchmark and optimize performance"),
    10: ("Start Module 10: Security Hardening (1-2 hrs)", "Implement security best practices"),
    11: ("Start Module 11: Monitoring (1-2 hrs)", "Set up monitoring and observability"),
    12: ("Start Module 12: Deployment (2-3 hrs)", "Package and deploy to production"),
}



def main():
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  " + cyan("Senzing Bootcamp - Project Status") + "                     " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    progress_json = Path("config") / "bootcamp_progress.json"
    progress_md = Path("docs") / "guides" / "PROGRESS_TRACKER.md"

    # Canonical source: bootcamp_progress.json (written by the agent)
    # Fallback: PROGRESS_TRACKER.md (manual tracking)
    completed = []
    in_progress = None
    current = 0
    status = "Not Started"
    language = None

    if progress_json.is_file():
        import json
        try:
            data = json.loads(progress_json.read_text(encoding="utf-8"))
            completed = data.get("modules_completed", [])
            current = data.get("current_module", 0)
            language = data.get("language")
            if completed:
                last = max(completed)
                if current > last:
                    status = "Ready to Start"
                elif current in completed:
                    status = "Complete" if last >= 12 else "Ready to Start"
                else:
                    status = "In Progress"
        except (json.JSONDecodeError, KeyError):
            pass
    elif progress_md.is_file():
        # Fallback: parse the markdown tracker
        checked_re = re.compile(r"\[x\].*Module\s+(\d+)", re.IGNORECASE)
        unchecked_re = re.compile(r"\[\s\].*Module\s+(\d+)", re.IGNORECASE)
        for line in progress_md.read_text(encoding="utf-8").splitlines():
            m = checked_re.search(line)
            if m:
                completed.append(int(m.group(1)))
                continue
            m = unchecked_re.search(line)
            if m and in_progress is None:
                in_progress = int(m.group(1))
        if not completed:
            current = 0
            status = "Not Started"
        elif in_progress is not None:
            current = in_progress
            status = "In Progress"
        else:
            last = max(completed)
            current = min(last + 1, 12)
            status = "Complete" if last >= 12 else "Ready to Start"
    else:
        print(yellow("⚠ No progress data found"))
        print("Start the bootcamp to begin tracking progress.")
        print()
        # Continue to show project health below

    total_modules = 13
    pct = len(completed) * 100 // total_modules

    print(f"  {green('Current Module:')} Module {current}")
    print(f"  {green('Status:')} {status}")
    if language:
        print(f"  {green('Language:')} {language}")
    print(f"  {green('Progress:')} {len(completed)}/{total_modules} modules ({pct}%)")
    print()

    # Progress bar
    bar_w = 50
    filled = pct * bar_w // 100
    bar = "█" * filled + "░" * (bar_w - filled)
    print(f"  {green('[')}{bar}{green(']')} {pct}%")
    print()

    # Completed modules
    if completed:
        print(green("✓ Completed Modules:"))
        for m in sorted(completed):
            print(f"    ✓ Module {m}: {MODULE_NAMES.get(m, '?')}")
        print()

    # Next steps
    if current <= 12 and status != "Complete":
        print(cyan("→ Next Steps:"))
        step = NEXT_STEPS.get(current)
        if step:
            print(f"    1. {step[0]}")
            print(f"    2. {step[1]}")
            print(f"    3. Tell agent 'Start Module {current}'")
        print()
    else:
        print(green("🎉 Bootcamp Complete!"))
        print()

    # Project health
    print(cyan("Project Health:"))
    health = 0
    checks = [
        (os.path.join("data", "raw"), "Data directory"),
        ("database", "Database directory"),
        ("src", "Source directory"),
        ("scripts", "Scripts directory"),
        (".gitignore", ".gitignore"),
        (".env.example", ".env.example"),
        ("README.md", "README.md"),
        ("backups", "Backups directory"),
    ]
    for path, label in checks:
        exists = os.path.exists(path)
        mark = "✓" if exists else "✗"
        print(f"    {mark} {label} {'exists' if exists else 'missing'}")
        if exists:
            health += 1

    health_pct = health * 100 // len(checks)
    print()
    print(f"  {green('Health Score:')} {health}/{len(checks)} ({health_pct}%)")
    print()

    print(cyan("Quick Commands:"))
    print("    python scripts/status.py              # Show this status")
    print("    python scripts/backup_project.py      # Backup project")
    print("    Tell agent 'resume bootcamp'           # Resume bootcamp")
    print()


if __name__ == "__main__":
    main()
