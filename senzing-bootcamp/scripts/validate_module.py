#!/usr/bin/env python3
"""
Validate module prerequisites and success criteria.

Usage:
    python scripts/validate_module.py              # Validate current module
    python scripts/validate_module.py --module 5   # Validate specific module
    python scripts/validate_module.py --next 6     # Check if ready for module 6
    python scripts/validate_module.py --artifacts 6  # Check artifact dependencies for module 6
"""

from __future__ import annotations

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


def validate_module_1():
    """Module 1: Business Problem — prerequisites for Module 2."""
    return [
        check_file_not_empty("docs/business_problem.md", "Business problem documented"),
    ]


def validate_module_2():
    """Module 2: SDK Setup — prerequisites for Module 3."""
    return [
        check_path("database/G2C.db", "SQLite database exists"),
        check_path("config/bootcamp_preferences.yaml", "Preferences file exists"),
    ]


def validate_module_3():
    """Module 3: System Verification — prerequisites for Module 4."""
    return [
        check_dir_has_files("src/quickstart_demo", "demo_*.*", "Verification script created"),
        check_dir_has_files("src/quickstart_demo", "sample_data_*.*", "Sample data saved"),
    ]


def validate_module_4():
    """Module 4: Data Collection — prerequisites for Module 5."""
    return [
        check_dir_has_files("data/raw", "*.*", "Data files collected in data/raw/"),
        check_path("docs/data_source_locations.md", "Data source locations documented"),
    ]


def validate_module_5():
    """Module 5: Data Quality & Mapping — prerequisites for Module 6."""
    return [
        check_file_not_empty(
            "docs/data_source_evaluation.md", "Data source evaluation report created"
        ),
        check_dir_has_files("src/transform", "*.*", "Transformation program(s) created"),
        check_dir_has_files(
            "data/transformed", "*.jsonl", "Transformed JSONL file(s) created"
        ),
    ]


def validate_module_6():
    """Module 6: Load Data — prerequisites for Module 7."""
    return [
        check_dir_has_files("src/load", "*.*", "Loading program(s) created"),
        check_path("database/G2C.db", "Database exists with loaded data"),
        check_path("docs/loading_strategy.md", "Loading strategy documented"),
    ]


def validate_module_7():
    """Module 7: Query and Validation — prerequisites for Module 8."""
    return [
        check_dir_has_files("src/query", "*.*", "Query program(s) created"),
        check_path("docs/results_validation.md", "Results validation documented"),
    ]


def validate_module_8():
    """Module 8: Performance Testing — prerequisites for Module 9."""
    return [
        check_path("docs/performance_requirements.md", "Performance requirements defined"),
        check_file_not_empty(
            "docs/benchmark_environment.md", "Benchmark environment documented"
        ),
        check_dir_has_files(
            "tests/performance", "*.*", "Benchmark scripts saved"
        ),
        check_path("docs/performance_report.md", "Performance report created"),
    ]


def validate_module_9():
    """Module 9: Security Hardening — prerequisites for Module 10."""
    return [
        check_file_not_empty(
            "docs/security_compliance.md", "Security compliance assessment documented"
        ),
        check_dir_has_files(
            "src/security", "*.*", "Security utilities created (secrets, auth, or audit)"
        ),
        check_file_not_empty(
            "docs/security_checklist.md", "Security checklist completed"
        ),
    ]


def validate_module_10():
    """Module 10: Monitoring — prerequisites for Module 11."""
    return [
        check_dir_has_files(
            "src/monitoring", "*.*", "Monitoring utilities created (metrics, health check)"
        ),
        check_dir_has_files(
            "docs/runbooks", "*.md", "Operational runbooks created"
        ),
        check_file_not_empty(
            "docs/monitoring_setup.md", "Monitoring setup documented"
        ),
    ]


def validate_module_11():
    """Module 11: Deployment — bootcamp complete."""
    return [
        check_path("Dockerfile", "Dockerfile created for containerization"),
        check_file_not_empty(
            "docs/deployment_plan.md", "Deployment plan documented"
        ),
    ]


VALIDATORS = {
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
}

MODULE_NAMES = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Load Data",
    7: "Query & Visualize",
    8: "Performance Testing",
    9: "Security Hardening",
    10: "Monitoring",
    11: "Deployment",
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


def parse_module_artifacts_yaml(path: str) -> dict:
    """Parse module-artifacts.yaml using a minimal YAML parser.

    Args:
        path: Path to the module-artifacts.yaml file.

    Returns:
        Parsed manifest as a dictionary with 'version' and 'modules' keys.
    """
    if not os.path.exists(path):
        return {}

    with open(path) as f:
        lines = f.readlines()

    result: dict = {"version": "", "modules": {}}
    current_module: int | None = None
    current_section: str | None = None  # "produces" or "requires_from"
    current_artifact: dict | None = None
    current_req_module: int | None = None

    for line in lines:
        raw = line.rstrip()
        if not raw or raw.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        content = line.strip()

        # Top-level version
        if indent == 0 and content.startswith("version:"):
            result["version"] = content.split(":", 1)[1].strip().strip('"').strip("'")
            continue

        # Top-level modules: key
        if indent == 0 and content == "modules:":
            continue

        # Module number (indent 2)
        if indent == 2 and content.rstrip(":").isdigit():
            # Flush previous artifact
            if current_artifact is not None and current_module is not None:
                result["modules"][current_module]["produces"].append(current_artifact)
                current_artifact = None
            current_module = int(content.rstrip(":"))
            result["modules"][current_module] = {"produces": [], "requires_from": {}}
            current_section = None
            current_req_module = None
            continue

        # Section headers (indent 4)
        if indent == 4 and current_module is not None:
            # Flush previous artifact
            if current_artifact is not None:
                result["modules"][current_module]["produces"].append(current_artifact)
                current_artifact = None
            if content == "produces:":
                current_section = "produces"
                current_req_module = None
                continue
            elif content == "requires_from:":
                current_section = "requires_from"
                current_req_module = None
                continue

        # Produces list items (indent 6, starts with "- path:")
        if indent == 6 and current_section == "produces" and current_module is not None:
            if content.startswith("- path:"):
                if current_artifact is not None:
                    result["modules"][current_module]["produces"].append(current_artifact)
                value = content.split(":", 1)[1].strip().strip('"').strip("'")
                current_artifact = {"path": value, "type": "file",
                                    "description": "", "required": True}
                continue

        # Produces item fields (indent 8)
        if indent == 8 and current_section == "produces" and current_artifact is not None:
            if content.startswith("type:"):
                current_artifact["type"] = content.split(":", 1)[1].strip().strip('"')
            elif content.startswith("description:"):
                current_artifact["description"] = content.split(":", 1)[1].strip().strip('"')
            elif content.startswith("required:"):
                val = content.split(":", 1)[1].strip().lower()
                current_artifact["required"] = val == "true"
            continue

        # requires_from entries (indent 6)
        if indent == 6 and current_section == "requires_from" and current_module is not None:
            # Format: "4: [\"data/raw/\", \"config/data_sources.yaml\"]"
            if ":" in content:
                key_part, val_part = content.split(":", 1)
                mod_num = int(key_part.strip())
                # Parse the list value
                val_str = val_part.strip()
                paths: list[str] = []
                if val_str.startswith("[") and val_str.endswith("]"):
                    inner = val_str[1:-1]
                    for item in inner.split(","):
                        item = item.strip().strip('"').strip("'")
                        if item:
                            paths.append(item)
                result["modules"][current_module]["requires_from"][mod_num] = paths
                current_req_module = mod_num
            continue

    # Flush last artifact
    if current_artifact is not None and current_module is not None:
        result["modules"][current_module]["produces"].append(current_artifact)

    return result


def check_artifact_on_disk(artifact_path: str) -> tuple[bool, bool]:
    """Check if an artifact exists on disk.

    For directories, checks existence and that it contains at least one file.
    For files, checks existence.

    Args:
        artifact_path: Relative path to the artifact.

    Returns:
        Tuple of (exists, is_directory).
    """
    p = Path(artifact_path)
    if artifact_path.endswith("/"):
        # Directory check
        if not p.exists() or not p.is_dir():
            return (False, True)
        # Check non-empty (has at least one file)
        has_files = any(True for _ in p.iterdir())
        return (has_files, True)
    else:
        # File check
        return (p.exists() and p.is_file(), False)


def run_artifact_check(module_num: int) -> bool:
    """Run artifact dependency check for a given module.

    Reads module-artifacts.yaml, resolves requires_from for the given module,
    checks each path exists on disk, and prints a summary table.

    Args:
        module_num: The module number to check artifacts for.

    Returns:
        True if all required artifacts are present, False otherwise.
    """
    manifest_path = "config/module-artifacts.yaml"
    manifest = parse_module_artifacts_yaml(manifest_path)

    if not manifest or not manifest.get("modules"):
        print(f"\n❌ Could not read artifact manifest: {manifest_path}\n")
        return False

    modules = manifest["modules"]
    if module_num not in modules:
        print(f"\n❌ Module {module_num} not found in artifact manifest.\n")
        return False

    module_data = modules[module_num]
    requires_from = module_data.get("requires_from", {})

    if not requires_from:
        print(f"\nModule {module_num} has no artifact dependencies.\n")
        return True

    print(f"\nChecking artifact dependencies for Module {module_num}...")
    print(f"{'─' * 60}")
    print(f"  {'Artifact Path':<35} {'Source':<12} {'Status'}")
    print(f"{'─' * 60}")

    all_required_present = True

    for source_module, paths in sorted(requires_from.items()):
        for artifact_path in paths:
            exists, _is_dir = check_artifact_on_disk(artifact_path)
            status = "✅ present" if exists else "❌ missing"
            source_label = f"Module {source_module}"
            print(f"  {artifact_path:<35} {source_label:<12} {status}")

            if not exists:
                # Check if this artifact is required in the source module
                source_data = modules.get(source_module, {})
                for prod in source_data.get("produces", []):
                    if prod["path"] == artifact_path and prod.get("required", True):
                        all_required_present = False
                        break
                else:
                    # If not found in produces or not required, still flag as missing
                    all_required_present = False

    print(f"{'─' * 60}")

    if all_required_present:
        print("  ✅ All artifact dependencies satisfied.\n")
    else:
        print("  ❌ Some required artifacts are missing.\n")

    return all_required_present


def main():
    parser = argparse.ArgumentParser(
        description="Validate Senzing Bootcamp module prerequisites and success criteria."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--module", type=int, choices=range(1, 12), metavar="N",
        help="Validate that module N is complete (1-11)",
    )
    group.add_argument(
        "--next", type=int, choices=range(1, 12), metavar="N",
        help="Check if ready to start module N (validates the previous module)",
    )
    group.add_argument(
        "--artifacts", type=int, choices=range(1, 12), metavar="N",
        help="Check artifact dependencies for module N (reads module-artifacts.yaml)",
    )
    args = parser.parse_args()

    if args.artifacts is not None:
        success = run_artifact_check(args.artifacts)
        sys.exit(0 if success else 1)

    if args.next is not None:
        # Validate the module before the requested one
        if args.next == 1:
            print("\nModule 1 has no prerequisites — you can start anytime.\n")
            sys.exit(0)
        module_num = args.next - 1
        print(f"\nChecking if ready to start Module {args.next}...")
    elif args.module is not None:
        module_num = args.module
    else:
        # Default: check current module from progress file
        progress = load_progress()
        module_num = progress.get("current_module", 1)
        completed = progress.get("modules_completed", [])
        if module_num in completed:
            print(f"\nModule {module_num} is already marked complete in progress file.")
            print(f"Validating Module {module_num} artifacts...\n")
        elif not progress:
            print("\nNo progress file found. Checking Module 1 prerequisites...\n")
            module_num = 1

    if module_num not in VALIDATORS:
        print(f"\nNo validator for Module {module_num}.\n")
        sys.exit(1)

    results = VALIDATORS[module_num]()
    success = print_results(module_num, results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
