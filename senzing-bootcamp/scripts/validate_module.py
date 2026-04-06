#!/usr/bin/env python3
"""
Validate module prerequisites and success criteria.

Usage:
    python scripts/validate_module.py              # Validate current module
    python scripts/validate_module.py --module 5   # Validate specific module
    python scripts/validate_module.py --next 6     # Check if ready for module 6
"""

import argparse
import json
import os
import sys
from pathlib import Path


def check_path(path, description):
    """Check if a path exists and return a result tuple."""
    exists = os.path.exists(path)
    return (exists, description, path)


def check_file_not_empty(path, description):
    """Check if a file exists and is not empty."""
    if not os.path.exists(path):
        return (False, description, f"{path} not found")
    if os.path.getsize(path) == 0:
        return (False, description, f"{path} is empty")
    return (True, description, path)


def check_dir_has_files(directory, pattern, description):
    """Check if a directory contains files matching a pattern."""
    p = Path(directory)
    if not p.exists():
        return (False, description, f"{directory}/ not found")
    matches = list(p.glob(pattern))
    if not matches:
        return (False, description, f"No {pattern} files in {directory}/")
    return (True, description, f"{len(matches)} file(s) found")


def load_progress():
    """Load bootcamp progress file."""
    path = "config/bootcamp_progress.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_preferences():
    """Load bootcamp preferences file."""
    path = "config/bootcamp_preferences.yaml"
    if not os.path.exists(path):
        return {}
    prefs = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                value = value.strip().strip('"').strip("'")
                if value and value != "null":
                    prefs[key.strip()] = value
    return prefs


def validate_module_0():
    """Module 0: SDK Setup — prerequisites for Module 1."""
    return [
        check_path("database/G2C.db", "SQLite database exists"),
        check_path("config/bootcamp_preferences.yaml", "Preferences file exists"),
    ]


def validate_module_1():
    """Module 1: Quick Demo — prerequisites for Module 2."""
    return [
        check_dir_has_files("src/quickstart_demo", "demo_*.*", "Demo script created"),
        check_dir_has_files("src/quickstart_demo", "sample_data_*.*", "Sample data saved"),
    ]


def validate_module_2():
    """Module 2: Business Problem — prerequisites for Module 3."""
    return [
        check_file_not_empty("docs/business_problem.md", "Business problem documented"),
    ]


def validate_module_3():
    """Module 3: Data Collection — prerequisites for Module 4."""
    return [
        check_dir_has_files("data/raw", "*.*", "Data files collected in data/raw/"),
        check_path("docs/data_source_locations.md", "Data source locations documented"),
    ]


def validate_module_4():
    """Module 4: Data Quality — prerequisites for Module 5."""
    return [
        check_file_not_empty(
            "docs/data_source_evaluation.md", "Data source evaluation report created"
        ),
    ]


def validate_module_5():
    """Module 5: Data Mapping — prerequisites for Module 6."""
    return [
        check_dir_has_files("src/transform", "*.*", "Transformation program(s) created"),
        check_dir_has_files(
            "data/transformed", "*.jsonl", "Transformed JSONL file(s) created"
        ),
    ]


def validate_module_6():
    """Module 6: Single Source Loading — prerequisites for Module 7."""
    return [
        check_dir_has_files("src/load", "*.*", "Loading program(s) created"),
        check_path("database/G2C.db", "Database exists with loaded data"),
    ]


def validate_module_7():
    """Module 7: Multi-Source Orchestration — prerequisites for Module 8."""
    results = validate_module_6()
    results.append(
        check_path("docs/loading_strategy.md", "Loading strategy documented")
    )
    return results


def validate_module_8():
    """Module 8: Query and Validation — prerequisites for Module 9."""
    return [
        check_dir_has_files("src/query", "*.*", "Query program(s) created"),
        check_path("docs/results_validation.md", "Results validation documented"),
    ]


def validate_module_9():
    """Module 9: Performance Testing — prerequisites for Module 10."""
    return [
        check_path("docs/performance_requirements.md", "Performance requirements defined"),
        check_path("docs/performance_report.md", "Performance report created"),
        check_dir_has_files(
            "tests/performance", "*.*", "Benchmark scripts saved"
        ),
    ]


def validate_module_10():
    """Module 10: Security Hardening — prerequisites for Module 11."""
    return [
        check_path("docs/security_checklist.md", "Security checklist completed"),
    ]


def validate_module_11():
    """Module 11: Monitoring — prerequisites for Module 12."""
    return [
        check_path("docs/monitoring_setup.md", "Monitoring setup documented"),
    ]


def validate_module_12():
    """Module 12: Deployment — bootcamp complete."""
    return [
        check_path("docs/deployment_plan.md", "Deployment plan documented"),
    ]


VALIDATORS = {
    0: validate_module_0,
    1: validate_module_1,
    2: validate_module_2,
    3: validate_module_3,
    4: validate_module_4,
    5: validate_module_5,
    6: validate_module_6,
    7: validate_module_7,
    8: validate_module_8,
    9: validate_module_9,
    10: validate_module_10,
    11: validate_module_11,
    12: validate_module_12,
}

MODULE_NAMES = {
    0: "SDK Setup",
    1: "Quick Demo",
    2: "Business Problem",
    3: "Data Collection",
    4: "Data Quality",
    5: "Data Mapping",
    6: "Single Source Loading",
    7: "Multi-Source Orchestration",
    8: "Query and Validation",
    9: "Performance Testing",
    10: "Security Hardening",
    11: "Monitoring",
    12: "Deployment",
}


def print_results(module_num, results):
    """Print validation results."""
    name = MODULE_NAMES.get(module_num, f"Module {module_num}")
    print(f"\n{'=' * 60}")
    print(f"  Module {module_num}: {name}")
    print(f"{'=' * 60}\n")

    passed = 0
    failed = 0
    for ok, description, detail in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {description}")
        if not ok:
            print(f"       → {detail}")
            failed += 1
        else:
            passed += 1

    total = passed + failed
    print(f"\n  Result: {passed}/{total} checks passed\n")

    if failed == 0:
        print(f"  ✅ Module {module_num} validation PASSED — ready to proceed.\n")
    else:
        print(f"  ⚠  Module {module_num} has {failed} incomplete item(s).\n")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate Senzing Bootcamp module prerequisites and success criteria."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--module", type=int, choices=range(0, 13), metavar="N",
        help="Validate that module N is complete (0-12)",
    )
    group.add_argument(
        "--next", type=int, choices=range(0, 13), metavar="N",
        help="Check if ready to start module N (validates the previous module)",
    )
    args = parser.parse_args()

    if args.next is not None:
        # Validate the module before the requested one
        if args.next == 0:
            print("\nModule 0 has no prerequisites — you can start anytime.\n")
            sys.exit(0)
        module_num = args.next - 1
        print(f"\nChecking if ready to start Module {args.next}...")
    elif args.module is not None:
        module_num = args.module
    else:
        # Default: check current module from progress file
        progress = load_progress()
        module_num = progress.get("current_module", 0)
        completed = progress.get("modules_completed", [])
        if module_num in completed:
            print(f"\nModule {module_num} is already marked complete in progress file.")
            print(f"Validating Module {module_num} artifacts...\n")
        elif not progress:
            print("\nNo progress file found. Checking Module 0 prerequisites...\n")
            module_num = 0

    if module_num not in VALIDATORS:
        print(f"\nNo validator for Module {module_num}.\n")
        sys.exit(1)

    results = VALIDATORS[module_num]()
    success = print_results(module_num, results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
