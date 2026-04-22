#!/usr/bin/env python3
"""Repair bootcamp_progress.json by scanning for actual artifacts.

Usage:
    python scripts/repair_progress.py          # Scan and report
    python scripts/repair_progress.py --fix    # Write/update progress
"""
import json, sys  # noqa: E401
from pathlib import Path

PROGRESS = Path("config/bootcamp_progress.json")
PREFS = Path("config/bootcamp_preferences.yaml")
D_EXT = ("*.csv", "*.json", "*.jsonl", "*.tsv", "*.xlsx")
NAMES = {0: "SDK Setup", 1: "Quick Demo", 2: "Business Problem",
         3: "Data Collection", 4: "Data Quality", 5: "Data Mapping",
         6: "Single Source Loading", 7: "Multi-Source Orchestration",
         8: "Query & Validation", 9: "Performance Testing",
         10: "Security Hardening", 11: "Monitoring", 12: "Deployment"}


def _c(code, t):
    tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return f"\033[{code}m{t}\033[0m" if tty else t


def green(t): return _c("0;32", t)  # noqa: E302
def red(t): return _c("0;31", t)
def yellow(t): return _c("1;33", t)
def cyan(t): return _c("0;36", t)


def _has(d, *pats):
    p = Path(d)
    return p.exists() and any(f for pt in pats for f in p.glob(pt))


def _multi():
    try:
        d = json.loads(PROGRESS.read_text("utf-8"))
        return len(d.get("data_sources", [])) > 1
    except Exception:  # noqa: BLE001
        return False


def detect():
    c = {0: Path("database/G2C.db").exists,
         1: lambda: _has("src/quickstart_demo", "*.*"),
         2: Path("docs/business_problem.md").exists,
         3: lambda: _has("data/raw", *D_EXT),
         4: lambda: (Path("docs/data_quality_report.md").exists()
                     or Path("docs/data_source_evaluation.md").exists()),
         5: lambda: (_has("data/transformed", "*.jsonl")
                     and _has("src/transform", "*.*")),
         6: lambda: _has("src/load", "*.*"),
         7: _multi, 8: lambda: _has("src/query", "*.*"),
         9: lambda: _has("docs", "performance*"),
         10: lambda: _has("docs", "security*"),
         11: Path("monitoring").is_dir,
         12: lambda: (any(Path(".").glob("*deploy*")) or (
             Path("config").exists()
             and any(Path("config").glob("*deploy*"))))}
    out = set()
    for m, fn in c.items():
        try:
            if fn():
                out.add(m)
        except OSError:
            pass
    return out


def _load():
    try:
        return json.loads(PROGRESS.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main():
    fix = "--fix" in sys.argv
    print(cyan("=== Bootcamp Progress Repair Tool ===\n"))
    det = detect()
    print(f"Scanned artifacts — {len(det)} module(s) found:\n")
    for m in range(13):
        mk = green("✓") if m in det else yellow("·")
        print(f"  {mk} Module {m}: {NAMES[m]}")
    ex = _load()
    if ex:
        rec = set(ex.get("modules_completed", []))
        miss, extra = det - rec, rec - det
        print(f"\n{cyan('vs. existing progress file:')}")
        if not miss and not extra:
            print(f"  {green('✓')} File matches artifacts")
        if miss:
            print(f"  {yellow('⚠')} Unrecorded: {sorted(miss)}")
        if extra:
            print(f"  {red('✗')} No artifacts: {sorted(extra)}")
    else:
        print(f"\n  {yellow('⚠')} No progress file found")
    sym = green("✓") if PREFS.exists() else yellow("⚠")
    tag = "preserved" if PREFS.exists() else "missing"
    print(f"  {sym} Preferences {tag}")
    if not fix:
        print(f"\n{cyan('Run with --fix to update.')}")
        return
    cur = min(max(det) + 1, 12) if det else 0
    prog = ex or {}
    prog["modules_completed"] = sorted(det)
    prog["current_module"] = cur
    prog.setdefault("data_sources", [])
    prog.setdefault("database_type", "sqlite")
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(
        json.dumps(prog, indent=2) + "\n", encoding="utf-8")
    print(f"\n  {green('✓')} Wrote {PROGRESS}")
    print(f"  {green('✓')} {len(det)} done, current={cur}")


if __name__ == "__main__":
    main()
