#!/usr/bin/env python3
"""Validate top-level key structure of authoritative YAML configuration files.

Usage:
    python validate_yaml_schemas.py          # validate all four files
    python validate_yaml_schemas.py --file steering/steering-index.yaml
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_REGISTRY: dict[str, set[str]] = {
    "steering/steering-index.yaml": {
        "modules",
        "onboarding",
        "session-resume",
        "keywords",
        "languages",
        "deployment",
        "file_metadata",
        "budget",
    },
    "config/module-dependencies.yaml": {"metadata", "modules", "tracks", "gates"},
    "hooks/hook-categories.yaml": {"critical", "metadata", "modules", "agentstop_order"},
    "config/module-artifacts.yaml": {"version", "modules"},
}


@dataclass
class ValidationResult:
    """Result of validating a single YAML file.

    Attributes:
        file_path: Relative path to the validated file.
        passed: Whether validation passed.
        missing_keys: Keys expected but not found.
        unexpected_keys: Keys found but not expected.
        error: Parse error message if YAML could not be loaded.
    """

    file_path: str
    passed: bool
    missing_keys: set[str] = field(default_factory=set)
    unexpected_keys: set[str] = field(default_factory=set)
    error: str | None = None


def parse_top_level_keys(content: str) -> set[str]:
    """Extract top-level mapping keys from YAML content.

    Args:
        content: Raw YAML file content.

    Returns:
        Set of top-level key names.

    Raises:
        ValueError: If content cannot be parsed as a YAML mapping.
    """
    keys: set[str] = set()
    for line in content.splitlines():
        if not line or line[0] in (" ", "\t", "#", "-"):
            continue
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key:
                keys.add(key)
    if not keys:
        raise ValueError("No top-level keys found; file may not be a YAML mapping")
    return keys


def format_result(result: ValidationResult) -> str:
    """Format a ValidationResult as a terse output line.

    Args:
        result: The validation result to format.

    Returns:
        Single line "PASS: <filename>" or "FAIL: <filename> — <reason>".
    """
    filename = Path(result.file_path).name
    if result.passed:
        return f"PASS: {filename}"

    reasons: list[str] = []
    if result.error:
        reasons.append(result.error)
    if result.missing_keys:
        reasons.append(f"missing keys: {sorted(result.missing_keys)}")
    if result.unexpected_keys:
        reasons.append(f"unexpected keys: {sorted(result.unexpected_keys)}")

    return f"FAIL: {filename} \u2014 {'; '.join(reasons)}"


def validate_file(file_path: str, expected_keys: set[str]) -> ValidationResult:
    """Validate a single YAML file against its expected top-level keys.

    Args:
        file_path: Path to the YAML file.
        expected_keys: Set of required top-level keys.

    Returns:
        ValidationResult with pass/fail status and key differences.
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError as exc:
        return ValidationResult(
            file_path=file_path,
            passed=False,
            missing_keys=set(),
            unexpected_keys=set(),
            error=f"Cannot read file: {exc}",
        )

    try:
        actual_keys = parse_top_level_keys(content)
    except ValueError as exc:
        return ValidationResult(
            file_path=file_path,
            passed=False,
            missing_keys=set(),
            unexpected_keys=set(),
            error=str(exc),
        )

    missing = expected_keys - actual_keys
    unexpected = actual_keys - expected_keys
    passed = not missing and not unexpected

    return ValidationResult(
        file_path=file_path,
        passed=passed,
        missing_keys=missing,
        unexpected_keys=unexpected,
    )


def _resolve_to_registry_key(file_arg: str, power_root: Path) -> str | None:
    """Resolve a --file argument to a SCHEMA_REGISTRY key.

    Args:
        file_arg: The raw --file argument value.
        power_root: The power root directory.

    Returns:
        The registry key if found, None otherwise.
    """
    # Try direct match first
    if file_arg in SCHEMA_REGISTRY:
        return file_arg
    # Try resolving as absolute/relative path
    try:
        resolved = Path(file_arg).resolve()
        rel = str(resolved.relative_to(power_root))
        if rel in SCHEMA_REGISTRY:
            return rel
    except (ValueError, OSError):
        pass
    return None


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 if all files pass, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Validate top-level keys in YAML config files.",
    )
    parser.add_argument(
        "--file",
        help="Validate a single file (must be in the schema registry).",
    )
    args = parser.parse_args(argv)

    power_root = Path(__file__).resolve().parent.parent

    if args.file:
        rel_path = _resolve_to_registry_key(args.file, power_root)
        if rel_path is None:
            print(f"ERROR: Unrecognized file: {args.file}", file=sys.stderr)
            return 1
        targets = {rel_path: SCHEMA_REGISTRY[rel_path]}
    else:
        targets = SCHEMA_REGISTRY

    results: list[ValidationResult] = []
    for rel_path, expected_keys in targets.items():
        full_path = str(power_root / rel_path)
        results.append(validate_file(full_path, expected_keys))

    for result in results:
        print(format_result(result))

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
