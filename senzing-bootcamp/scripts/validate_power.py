#!/usr/bin/env python3
"""Validate the Senzing Bootcamp power's internal consistency.

Checks that all cross-references resolve, all hooks are valid JSON,
all steering files have frontmatter, and all files listed in POWER.md exist.

Usage:
    python senzing-bootcamp/scripts/validate_power.py
"""

import json
import os
import re
import sys
from pathlib import Path

# Allow importing sibling scripts (scripts aren't packages)
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from version import VersionError, read_version, read_version_from_frontmatter, validate_version


def color(code, text):
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(t): return color("0;32", t)
def red(t): return color("0;31", t)
def yellow(t): return color("1;33", t)


POWER_DIR = Path("senzing-bootcamp")
errors = []
warnings = []


def check(condition, msg, warn_only=False):
    if not condition:
        if warn_only:
            warnings.append(msg)
            print(f"  {yellow('⚠')} {msg}")
        else:
            errors.append(msg)
            print(f"  {red('✗')} {msg}")
    else:
        print(f"  {green('✓')} {msg}")


def check_steering_files():
    print("\n=== Steering Files ===")
    steering_dir = POWER_DIR / "steering"
    if not steering_dir.exists():
        check(False, "steering/ directory exists")
        return

    valid_inclusions = {"always", "auto", "fileMatch", "manual"}
    for f in sorted(steering_dir.glob("*.md")):
        with open(f) as fh:
            content = fh.read()
        # Check frontmatter
        has_frontmatter = content.startswith("---")
        check(has_frontmatter, f"{f.name}: has YAML frontmatter")
        if has_frontmatter:
            fm_end = content.index("---", 3)
            fm = content[3:fm_end].strip()
            inclusion_match = re.search(r"inclusion:\s*(\w+)", fm)
            if inclusion_match:
                inc = inclusion_match.group(1)
                check(inc in valid_inclusions, f"{f.name}: inclusion '{inc}' is valid")
            else:
                check(False, f"{f.name}: has 'inclusion' in frontmatter")


def check_hooks():
    print("\n=== Hooks ===")
    hooks_dir = POWER_DIR / "hooks"
    if not hooks_dir.exists():
        check(False, "hooks/ directory exists")
        return

    valid_events = {
        "fileEdited", "fileCreated", "fileDeleted", "userTriggered",
        "promptSubmit", "agentStop", "preToolUse", "postToolUse",
        "preTaskExecution", "postTaskExecution",
    }
    valid_actions = {"askAgent", "runCommand"}

    for f in sorted(hooks_dir.glob("*.kiro.hook")):
        try:
            with open(f) as fh:
                hook = json.load(fh)
            check(True, f"{f.name}: valid JSON")
            check("name" in hook, f"{f.name}: has 'name' field")
            check("version" in hook, f"{f.name}: has 'version' field")
            when = hook.get("when", {})
            event_type = when.get("type", "")
            check(event_type in valid_events, f"{f.name}: event type '{event_type}' is valid")
            then = hook.get("then", {})
            action_type = then.get("type", "")
            check(action_type in valid_actions, f"{f.name}: action type '{action_type}' is valid")
        except json.JSONDecodeError as e:
            check(False, f"{f.name}: valid JSON — {e}")


def check_module_docs():
    print("\n=== Module Documentation ===")
    modules_dir = POWER_DIR / "docs" / "modules"
    if not modules_dir.exists():
        check(False, "docs/modules/ directory exists")
        return

    for i in range(1, 12):
        pattern = f"MODULE_{i}_*.md"
        matches = list(modules_dir.glob(pattern))
        check(len(matches) >= 1, f"Module {i} documentation exists")


def check_scripts():
    print("\n=== Scripts ===")
    scripts_dir = POWER_DIR / "scripts"
    expected = [
        "status.py", "validate_module.py", "check_prerequisites.py",
        "install_hooks.py", "backup_project.py", "restore_project.py",
        "preflight.py", "validate_commonmark.py",
        "validate_power.py",
    ]
    for script in expected:
        check((scripts_dir / script).exists(), f"{script} exists")


def check_power_md_references():
    print("\n=== POWER.md References ===")
    power_md = POWER_DIR / "POWER.md"
    if not power_md.exists():
        check(False, "POWER.md exists")
        return

    with open(power_md) as f:
        content = f.read()

    # Find all steering file references like `module-02-sdk-setup.md`
    steering_refs = re.findall(r"`([\w-]+\.md)`", content)
    steering_dir = POWER_DIR / "steering"
    for ref in steering_refs:
        if ref.endswith(".md") and not ref.startswith("MODULE_"):
            exists = (steering_dir / ref).exists()
            check(exists, f"Referenced steering file '{ref}' exists")


def check_policies():
    print("\n=== Policies ===")
    policies_dir = POWER_DIR / "docs" / "policies"
    if not policies_dir.exists():
        check(False, "docs/policies/ directory exists")
        return

    expected = [
        "FILE_STORAGE_POLICY.md", "CODE_QUALITY_STANDARDS.md",
        "SENZING_INFORMATION_POLICY.md",
    ]
    for policy in expected:
        check((policies_dir / policy).exists(), f"{policy} exists")


def check_steering_index_metadata():
    print("\n=== Steering Index Metadata ===")
    index_path = POWER_DIR / "steering" / "steering-index.yaml"
    steering_dir = POWER_DIR / "steering"

    if not index_path.exists():
        check(False, "steering-index.yaml exists")
        return
    check(True, "steering-index.yaml exists")

    content = index_path.read_text(encoding="utf-8")

    # --- file_metadata section ---
    has_file_metadata = re.search(r"^file_metadata:\s*$", content, re.MULTILINE) is not None
    check(has_file_metadata, "file_metadata mapping exists in steering-index.yaml")

    if not has_file_metadata:
        return

    # Parse file_metadata entries
    fm_match = re.search(r"^file_metadata:\s*\n((?:[ ].*\n)*)", content, re.MULTILINE)
    fm_block = fm_match.group(1) if fm_match else ""

    parsed_entries = {}
    current_file = None
    for line in fm_block.splitlines():
        file_match = re.match(r"^  ([\w.-]+\.md):\s*$", line)
        if file_match:
            current_file = file_match.group(1)
            parsed_entries[current_file] = {}
            continue
        if current_file:
            tc_match = re.match(r"^\s+token_count:\s*(.+)$", line)
            if tc_match:
                parsed_entries[current_file]["token_count"] = tc_match.group(1).strip()
            sc_match = re.match(r"^\s+size_category:\s*(.+)$", line)
            if sc_match:
                parsed_entries[current_file]["size_category"] = sc_match.group(1).strip()

    # Check every .md file in steering/ has a valid entry
    valid_categories = {"small", "medium", "large"}
    md_files = sorted(f.name for f in steering_dir.glob("*.md"))
    for md_name in md_files:
        has_entry = md_name in parsed_entries
        check(has_entry, f"file_metadata has entry for {md_name}")
        if has_entry:
            entry = parsed_entries[md_name]
            tc_raw = entry.get("token_count", "")
            try:
                int(tc_raw)
                tc_valid = True
            except (ValueError, TypeError):
                tc_valid = False
            check(tc_valid, f"{md_name}: token_count is an integer")

            sc_raw = entry.get("size_category", "")
            check(sc_raw in valid_categories, f"{md_name}: size_category '{sc_raw}' is valid")

    # --- budget section ---
    has_budget = re.search(r"^budget:\s*$", content, re.MULTILINE) is not None
    check(has_budget, "budget mapping exists in steering-index.yaml")

    if has_budget:
        budget_fields = ["total_tokens", "reference_window", "warn_threshold_pct", "critical_threshold_pct"]
        for field in budget_fields:
            field_match = re.search(rf"^\s+{re.escape(field)}:\s*(\d+)", content, re.MULTILINE)
            check(field_match is not None, f"budget.{field} exists and is an integer")


def check_diagrams():
    print("\n=== Diagrams ===")
    diagrams_dir = POWER_DIR / "docs" / "diagrams"
    expected = ["module-flow.md", "data-flow.md", "system-architecture.md"]
    for diagram in expected:
        check((diagrams_dir / diagram).exists(), f"{diagram} exists")


def check_version_file():
    """Read senzing-bootcamp/VERSION and validate its format."""
    print("\n=== Version File ===")
    version_file = POWER_DIR / "VERSION"
    if not version_file.exists():
        check(False, f"VERSION file exists at {version_file}")
        return

    check(True, f"VERSION file exists at {version_file}")

    try:
        content = version_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        check(False, f"VERSION file is readable — {exc}")
        return

    if not content:
        check(False, "VERSION file is not empty")
        return

    try:
        validate_version(content)
        check(True, f"VERSION file contains valid semver: {content}")
    except VersionError as exc:
        check(False, f"VERSION file contains valid semver — {exc.message}")


def check_version_sync():
    """Verify VERSION file and POWER.md frontmatter version are in sync."""
    print("\n=== Version Sync (VERSION ↔ POWER.md frontmatter) ===")
    version_file = POWER_DIR / "VERSION"
    power_md = POWER_DIR / "POWER.md"

    if not version_file.exists() or not power_md.exists():
        check(False, "Both VERSION and POWER.md exist for sync check")
        return

    try:
        file_version = read_version(version_file)
    except VersionError as exc:
        check(False, f"VERSION file readable for sync check — {exc.message}")
        return

    try:
        power_md_content = power_md.read_text(encoding="utf-8")
    except OSError as exc:
        check(False, f"POWER.md readable for sync check — {exc}")
        return

    try:
        frontmatter_version = read_version_from_frontmatter(power_md_content)
    except VersionError as exc:
        check(False, f"POWER.md frontmatter has valid version — {exc.message}")
        return

    versions_match = file_version == frontmatter_version
    check(
        versions_match,
        f"VERSION ({file_version}) matches POWER.md frontmatter ({frontmatter_version})",
    )


def main():
    print(f"Validating Senzing Bootcamp power at: {POWER_DIR.resolve()}")

    check(POWER_DIR.exists(), "Power directory exists")
    check((POWER_DIR / "POWER.md").exists(), "POWER.md exists")
    check((POWER_DIR / "CHANGELOG.md").exists(), "CHANGELOG.md exists")

    check_steering_files()
    check_hooks()
    check_module_docs()
    check_scripts()
    check_power_md_references()
    check_policies()
    check_diagrams()
    check_steering_index_metadata()
    check_version_file()
    check_version_sync()

    print(f"\n{'=' * 50}")
    if errors:
        print(red(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)"))
        sys.exit(1)
    elif warnings:
        print(yellow(f"PASSED with {len(warnings)} warning(s)"))
    else:
        print(green("PASSED: All checks passed"))


if __name__ == "__main__":
    main()
