# Design Document

## Overview

A simple Python script (`senzing-bootcamp/scripts/validate_yaml_schemas.py`) that validates the top-level key structure of four authoritative YAML configuration files. The script uses only Python stdlib, follows the project's script conventions, and integrates into the existing CI workflow.

## Architecture

The script follows a straightforward pipeline architecture:

1. **CLI Layer** — `argparse` parses `--file` flag or defaults to all four files
2. **Schema Registry** — A dictionary mapping file paths to their expected top-level key sets
3. **YAML Parser** — Minimal stdlib-based YAML parser (reads top-level keys only)
4. **Validator** — Compares actual keys against expected keys, reports differences
5. **Reporter** — Prints terse PASS/FAIL output per file

```
CLI → Schema Registry Lookup → YAML Parse → Key Set Comparison → Report
```

## Components and Interfaces

### Schema Registry

A module-level constant mapping each known file path (relative to the power root) to its expected key set:

```python
from __future__ import annotations

from dataclasses import dataclass

SCHEMA_REGISTRY: dict[str, set[str]] = {
    "steering/steering-index.yaml": {"modules", "keywords", "languages", "deployment", "file_metadata", "budget"},
    "config/module-dependencies.yaml": {"metadata", "modules", "tracks", "gates"},
    "hooks/hook-categories.yaml": {"critical", "modules"},
    "config/module-artifacts.yaml": {"version", "modules"},
}
```

### Data Structures

```python
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
    missing_keys: set[str]
    unexpected_keys: set[str]
    error: str | None = None
```

### YAML Top-Level Key Parser

Since the project convention is stdlib-only (no PyYAML for this script), a minimal parser extracts top-level keys from simple YAML mappings. Top-level keys are lines that start with a non-space, non-comment character and contain a colon. This is sufficient for the four target files which are all flat mappings at the root level.

```python
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
```

### Validator Function

```python
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
```

### Reporter

```python
def format_result(result: ValidationResult) -> str:
    """Format a ValidationResult as a terse output line.

    Args:
        result: The validation result to format.

    Returns:
        Single line "PASS: <filename>" or "FAIL: <filename> <reason>".
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

    return f"FAIL: {filename} — {'; '.join(reasons)}"
```

### CLI Entry Point

```python
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
        # Resolve to relative path for registry lookup
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
```

### CLI Interface

```
usage: validate_yaml_schemas.py [-h] [--file FILE]

Validate top-level keys in YAML config files.

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  Validate a single file (must be in the schema registry).
```

### Function Interface

| Function | Input | Output |
|----------|-------|--------|
| `parse_top_level_keys(content: str)` | Raw YAML string | `set[str]` of keys |
| `validate_file(file_path: str, expected_keys: set[str])` | Path + expected keys | `ValidationResult` |
| `format_result(result: ValidationResult)` | Validation result | Formatted string |
| `main(argv: list[str] \| None)` | CLI args | Exit code `int` |

## Data Models

### ValidationResult

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `str` | Relative path to the validated file |
| `passed` | `bool` | Whether validation passed |
| `missing_keys` | `set[str]` | Expected keys not found in file |
| `unexpected_keys` | `set[str]` | Keys found but not expected |
| `error` | `str \| None` | Parse error message, if any |

### SCHEMA_REGISTRY

| File Path | Expected Keys |
|-----------|---------------|
| `steering/steering-index.yaml` | `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget` |
| `config/module-dependencies.yaml` | `metadata`, `modules`, `tracks`, `gates` |
| `hooks/hook-categories.yaml` | `critical`, `modules` |
| `config/module-artifacts.yaml` | `version`, `modules` |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| File not found / unreadable | Report FAIL with OS error message, exit 1 |
| File is not valid YAML mapping | Report FAIL with parse error, exit 1 |
| `--file` path not in registry | Print error to stderr, exit 1 |
| Extra keys in file | Report FAIL listing unexpected keys |
| Missing keys in file | Report FAIL listing missing keys |
| All files valid | Report PASS per file, exit 0 |

## Testing Strategy

- **Property-based tests** (Hypothesis, `@settings(max_examples=20)`): Validate universal properties (key set detection, output format, exit codes) across randomly generated YAML content and key sets.
- **Example-based unit tests**: Verify the four specific file schemas (Requirements 1.1–1.4), default invocation behavior (3.1), and CI integration (5.1–5.2).
- **Edge cases**: Covered by Hypothesis generators — empty files, files with only comments, files with duplicate keys, non-UTF-8 content.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Key Set Validation Detects Symmetric Difference

*For any* set of expected keys and *for any* YAML content whose actual top-level keys differ from the expected set, the validator SHALL report FAIL and the union of `missing_keys` and `unexpected_keys` SHALL equal the symmetric difference between the expected and actual key sets.

**Validates: Requirements 1.5, 1.6**

### Property 2: Output Format Correctness

*For any* validation result, the formatted output SHALL start with `PASS: <filename>` when the result passed, or `FAIL: <filename>` when the result failed, and the total number of output lines (one per file) SHALL equal the number of files validated.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Exit Code Correctness

*For any* set of validation results, the exit code SHALL be 0 if and only if all results have `passed == True`. If any result has `passed == False`, the exit code SHALL be non-zero.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 4: Single-File Flag Isolation

*For any* file path present in the schema registry, invoking the validator with `--file <path>` SHALL produce exactly one output line corresponding to that file and no output for other files.

**Validates: Requirements 3.2**

### Property 5: Unrecognized File Rejection

*For any* file path NOT present in the schema registry, invoking the validator with `--file <path>` SHALL exit with a non-zero code and print an error message containing the unrecognized path.

**Validates: Requirements 3.3**
