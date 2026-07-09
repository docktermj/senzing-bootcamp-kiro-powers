#!/usr/bin/env python3
"""Senzing Bootcamp - CORD Readiness Check Helper.

Performs a lightweight structural pre-screen of a CORD data file to determine
if its records are already in a Senzing-loadable form. Does NOT assert what
constitutes valid Senzing attributes -- the caller provides the expected
top-level schema keys (obtained from the MCP server's Entity Specification).

Usage:
    python scripts/check_cord_readiness.py \
      --file data/raw/cord-las-vegas.jsonl \
      --schema-keys DATA_SOURCE,RECORD_ID,FEATURES \
      --max-records 100

Exit codes:
    0 -- All sampled records pass structural checks (ready)
    1 -- One or more records fail (not ready) or error

Depends only on the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────

DEFAULT_MAX_RECORDS = 100


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass
class ReadinessResult:
    """Result of the structural readiness check.

    Attributes:
        ready: True if all sampled records pass the structural check.
        records_checked: Number of records examined (<= max_records).
        records_passed: Records that contain all required schema keys.
        records_failed: Records missing one or more schema keys or malformed.
        failure_reasons: Human-readable reasons for failures.
    """

    ready: bool
    records_checked: int
    records_passed: int
    records_failed: int
    failure_reasons: list[str] = field(default_factory=list)


# ── Core Functions ───────────────────────────────────────────────────────


def _check_record(line: str, record_num: int, schema_keys: list[str]) -> tuple[bool, str]:
    """Check a single JSONL line against the required schema keys.

    A record passes only when it is valid JSON, is a JSON object, and contains
    every key in ``schema_keys`` as a top-level key.

    Args:
        line: A single non-empty JSONL line.
        record_num: 1-based index of the record (for failure messages).
        schema_keys: Top-level keys that must be present in the record.

    Returns:
        A ``(passed, reason)`` tuple. ``reason`` is empty when ``passed`` is True.
    """
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return False, f"Record {record_num}: invalid JSON."

    if not isinstance(record, dict):
        return False, f"Record {record_num}: not a JSON object (top-level keys required)."

    missing = [key for key in schema_keys if key not in record]
    if missing:
        return False, f"Record {record_num}: missing required key(s): {', '.join(missing)}."

    return True, ""


def check_readiness(
    file_path: str,
    schema_keys: list[str],
    max_records: int = DEFAULT_MAX_RECORDS,
) -> ReadinessResult:
    """Check if records in a JSONL file contain the expected schema keys.

    Examines a bounded sample of at most ``min(N, max_records)`` records, where
    ``N`` is the number of non-empty lines in the file. A source is classified
    ready only when every sampled record is valid JSON and contains all
    ``schema_keys`` as top-level keys. If the schema keys list is empty, the
    file cannot be read, or no records are found, the source is not ready
    (conformance cannot be determined).

    Args:
        file_path: Path to the JSONL data file.
        schema_keys: List of top-level keys that must be present in each record.
        max_records: Maximum number of records to examine (default 100).

    Returns:
        ReadinessResult with pass/fail classification and diagnostic counts.
    """
    # Normalize keys, dropping blanks introduced by trailing/adjacent commas.
    keys = [key.strip() for key in schema_keys if key and key.strip()]

    # Property 4: an empty schema keys list means conformance cannot be
    # determined, so the source is not ready.
    if not keys:
        return ReadinessResult(
            ready=False,
            records_checked=0,
            records_passed=0,
            records_failed=0,
            failure_reasons=[
                "No schema keys provided; cannot determine Senzing readiness."
            ],
        )

    # Property 3: bound the sample so the check stays lightweight.
    effective_max = max_records if max_records > 0 else 0

    path = Path(file_path)
    records_checked = 0
    records_passed = 0
    records_failed = 0
    failure_reasons: list[str] = []

    try:
        with path.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                if records_checked >= effective_max:
                    break
                records_checked += 1
                passed, reason = _check_record(line, records_checked, keys)
                if passed:
                    records_passed += 1
                else:
                    records_failed += 1
                    failure_reasons.append(reason)
    except FileNotFoundError:
        return ReadinessResult(
            ready=False,
            records_checked=0,
            records_passed=0,
            records_failed=0,
            failure_reasons=[f"File not found: {file_path}"],
        )
    except (OSError, UnicodeDecodeError) as exc:
        failure_reasons.append(f"Could not read file: {exc}")
        return ReadinessResult(
            ready=False,
            records_checked=records_checked,
            records_passed=records_passed,
            records_failed=records_failed,
            failure_reasons=failure_reasons,
        )

    # Property 4: no records examined means conformance cannot be determined.
    if records_checked == 0:
        return ReadinessResult(
            ready=False,
            records_checked=0,
            records_passed=0,
            records_failed=0,
            failure_reasons=[
                "No records found; cannot determine Senzing readiness."
            ],
        )

    # Property 2: ready only when every sampled record passed.
    ready = records_failed == 0
    return ReadinessResult(
        ready=ready,
        records_checked=records_checked,
        records_passed=records_passed,
        records_failed=records_failed,
        failure_reasons=failure_reasons,
    )


# ── Output Helpers ────────────────────────────────────────────────────────


def _print_summary(file_path: str, result: ReadinessResult) -> None:
    """Write a human-readable summary of the readiness check to stderr.

    Args:
        file_path: Path to the file that was checked.
        result: The readiness result to summarize.
    """
    status = "READY" if result.ready else "NOT READY"
    print(f"CORD readiness check: {file_path}", file=sys.stderr)
    print(f"  Result: {status}", file=sys.stderr)
    print(
        f"  Records checked: {result.records_checked} "
        f"(passed: {result.records_passed}, failed: {result.records_failed})",
        file=sys.stderr,
    )
    if result.failure_reasons:
        print("  Failure reasons:", file=sys.stderr)
        for reason in result.failure_reasons:
            print(f"    - {reason}", file=sys.stderr)


# ── CLI Entry Point ──────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Reads a JSONL file and reports whether every sampled record contains the
    caller-provided schema keys. Emits machine-readable JSON to stdout and a
    human-readable summary to stderr.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 if ready, 1 if not ready or error.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Structural pre-screen of a CORD JSONL file to check whether its "
            "records already contain the caller-provided Senzing schema keys."
        )
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the JSONL data file to check.",
    )
    parser.add_argument(
        "--schema-keys",
        required=True,
        help=(
            "Comma-separated list of top-level keys each record must contain "
            "(e.g., DATA_SOURCE,RECORD_ID,FEATURES). Provided by the caller from "
            "the MCP Entity Specification -- never hardcoded."
        ),
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        help=f"Maximum number of records to examine (default: {DEFAULT_MAX_RECORDS}).",
    )
    args = parser.parse_args(argv)

    if args.max_records < 1:
        print("Error: --max-records must be a positive integer.", file=sys.stderr)
        return 1

    schema_keys = [key.strip() for key in args.schema_keys.split(",") if key.strip()]

    result = check_readiness(args.file, schema_keys, args.max_records)

    # Machine-readable JSON to stdout for agent consumption.
    print(json.dumps(asdict(result)))

    # Human-readable summary to stderr.
    _print_summary(args.file, result)

    return 0 if result.ready else 1


if __name__ == "__main__":
    sys.exit(main())
