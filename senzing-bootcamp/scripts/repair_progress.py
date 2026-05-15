#!/usr/bin/env python3
"""Repair bootcamp_progress.json by scanning for actual artifacts.

Usage:
    python scripts/repair_progress.py          # Scan and report
    python scripts/repair_progress.py --fix    # Write/update progress
"""
import datetime
import json, sys  # noqa: E401
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import validate_progress_schema  # noqa: E402

PROGRESS = Path("config/bootcamp_progress.json")
PREFS = Path("config/bootcamp_preferences.yaml")
D_EXT = ("*.csv", "*.json", "*.jsonl", "*.tsv", "*.xlsx")
NAMES = {1: "Business Problem", 2: "SDK Setup", 3: "System Verification",
         4: "Data Collection", 5: "Data Quality & Mapping",
         6: "Single Source Loading", 7: "Multi-Source Orchestration",
         8: "Query & Validation", 9: "Performance Testing",
         10: "Security Hardening", 11: "Deployment"}


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
    c = {1: Path("docs/business_problem.md").exists,
         2: Path("database/G2C.db").exists,
         3: lambda: _has("src/quickstart_demo", "*.*"),
         4: lambda: _has("data/raw", *D_EXT),
         5: lambda: (Path("docs/data_quality_report.md").exists()
                     or Path("docs/data_source_evaluation.md").exists()
                     or (_has("data/transformed", "*.jsonl")
                         and _has("src/transform", "*.*"))),
         6: lambda: _has("src/load", "*.*"),
         7: _multi, 8: lambda: _has("src/query", "*.*"),
         9: lambda: _has("docs", "performance*"),
         10: lambda: _has("docs", "security*"),
         11: lambda: (Path("monitoring").is_dir()
                     or any(Path(".").glob("*deploy*")) or (
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


def detect_steps():
    """Map module-specific artifacts to approximate step numbers.

    Returns a dict mapping module number (int) to approximate step
    number (int) for modules where artifacts give a clear signal.
    Modules with no determinable step are omitted from the result.
    """
    steps = {}

    # Module 1: docs/business_problem.md → step 10
    if Path("docs/business_problem.md").exists():
        steps[1] = 10

    # Module 2: database/G2C.db → step 6
    if Path("database/G2C.db").exists():
        steps[2] = 6

    # Module 3: src/quickstart_demo/ has files → step 4
    if _has("src/quickstart_demo", "*.*"):
        steps[3] = 4

    # Module 4: data/raw/ has files → step 3
    if _has("data/raw", *D_EXT):
        steps[4] = 3

    # Module 5: check from most-complete to least-complete artifact
    if _has("data/transformed", "*.jsonl"):
        steps[5] = 12
    elif _has("src/transform", "*.*"):
        steps[5] = 11
    elif Path("docs/data_source_evaluation.md").exists():
        steps[5] = 7

    # Module 6: src/load/ has files → step 5
    if _has("src/load", "*.*"):
        steps[6] = 5

    # Module 8: check from most-complete to least-complete artifact
    if Path("docs/results_validation.md").exists():
        steps[8] = 7
    elif _has("src/query", "*.*"):
        steps[8] = 4

    # Module 9: docs/performance_report.md → step 6
    if Path("docs/performance_report.md").exists():
        steps[9] = 6

    # Module 10: docs/security_checklist.md → step 6
    if Path("docs/security_checklist.md").exists():
        steps[10] = 6

    # Module 11: Dockerfile or docker-compose.yml → step 5
    if Path("Dockerfile").exists() or Path("docker-compose.yml").exists():
        steps[11] = 5

    return steps


def _load():
    try:
        return json.loads(PROGRESS.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main():
    fix = "--fix" in sys.argv
    print(cyan("=== Bootcamp Progress Repair Tool ===\n"))
    det = detect()
    step_map = detect_steps()
    print(f"Scanned artifacts — {len(det)} module(s) found:\n")
    for m in range(1, 12):
        mk = green("✓") if m in det else yellow("·")
        step_info = f" (Step ~{step_map[m]})" if m in step_map else ""
        print(f"  {mk} Module {m}: {NAMES[m]}{step_info}")
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
    cur = min(max(det) + 1, 11) if det else 1
    prog = ex or {}
    prog["modules_completed"] = sorted(det)
    prog["current_module"] = cur
    prog.setdefault("data_sources", [])
    prog.setdefault("database_type", "sqlite")
    # Populate step_history for all modules with detected steps
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    step_history = prog.get("step_history", {})
    for mod, step in step_map.items():
        step_history[str(mod)] = {
            "last_completed_step": step,
            "updated_at": now,
        }
    if step_history:
        prog["step_history"] = step_history
    # Set current_step only if step is determinable for current module
    if cur in step_map:
        prog["current_step"] = step_map[cur]
    else:
        prog.pop("current_step", None)
    # Validate before writing
    validation_errors = validate_progress_schema(prog)
    if validation_errors:
        print(red("✗") + " Repair aborted: reconstructed progress file fails schema validation",
              file=sys.stderr)
        for err in validation_errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(
        json.dumps(prog, indent=2) + "\n", encoding="utf-8")
    print(f"\n  {green('✓')} Wrote {PROGRESS}")
    print(f"  {green('✓')} {len(det)} done, current={cur}")


if __name__ == "__main__":
    main()
