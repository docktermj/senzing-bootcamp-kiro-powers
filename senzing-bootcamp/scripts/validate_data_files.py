#!/usr/bin/env python3
"""
Validate data source files for the Senzing bootcamp.

Checks file existence/readability, format recognition, record presence,
and encoding validity. Reports results with pass/fail indicators and
remediation guidance.

Usage:
    python senzing-bootcamp/scripts/validate_data_files.py
    python senzing-bootcamp/scripts/validate_data_files.py data/raw/customers.csv
    python senzing-bootcamp/scripts/validate_data_files.py --update-registry
    python senzing-bootcamp/scripts/validate_data_files.py --json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────

RECOGNIZED_FORMATS: dict[str, str] = {
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".xml": "xml",
    ".xlsx": "xlsx",
    ".parquet": "parquet",
    ".tsv": "tsv",
}

FALLBACK_ENCODINGS: list[str] = ["latin-1", "utf-16", "cp1252"]


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass
class CheckResult:
    """Result of a single sanity check.

    Attributes:
        name: Check identifier ("existence", "format", "records", "encoding").
        status: Outcome — "pass", "fail", or "warn".
        message: Human-readable description of the result.
        remediation: Guidance for fixing a failure (empty string for pass/warn).
        details: Structured data for downstream consumers.
    """

    name: str
    status: str
    message: str
    remediation: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Aggregated result of all checks for a single file.

    Attributes:
        file_path: Absolute or relative path to the validated file.
        file_name: Base name of the file.
        format: Detected format string or None.
        record_count: Number of data records or None.
        encoding: Detected encoding string or None.
        checks: Ordered list of individual check results.
        overall_status: "pass" if all checks pass/warn, "fail" if any fail.
    """

    file_path: str
    file_name: str
    format: str | None
    record_count: int | None
    encoding: str | None
    checks: list[CheckResult]
    overall_status: str

    @property
    def failed_checks(self) -> list[CheckResult]:
        """Return only the checks that failed."""
        return [c for c in self.checks if c.status == "fail"]

    @property
    def failure_count(self) -> int:
        """Return the number of failed checks."""
        return len(self.failed_checks)


# ── Check Functions ───────────────────────────────────────────────────────


def check_existence(file_path: str) -> CheckResult:
    """Check that a file exists, is readable, and is non-empty.

    Checks are performed in order: exists → readable → non-zero size.
    Fails on the first failing condition with a specific message and
    remediation guidance.

    Args:
        file_path: Path to the file to check.

    Returns:
        CheckResult with name="existence".
    """
    path = Path(file_path)

    # 1. Check existence
    if not path.exists():
        return CheckResult(
            name="existence",
            status="fail",
            message=f"File not found at path: {file_path}",
            remediation=(
                "Re-upload or re-download the file. Verify the file path is correct"
                " and the file was saved to data/raw/"
            ),
        )

    # 2. Check readability
    try:
        with open(path, "r") as _fh:
            pass
    except (PermissionError, OSError):
        return CheckResult(
            name="existence",
            status="fail",
            message=f"File exists but cannot be opened for reading: {file_path}",
            remediation=f"Check file permissions. On Linux/macOS run: chmod 644 {file_path}",
        )

    # 3. Check non-zero size
    if os.path.getsize(path) == 0:
        return CheckResult(
            name="existence",
            status="fail",
            message=f"File is empty (0 bytes): {file_path}",
            remediation=(
                "The file has no content. Re-download or re-export the data"
                " from the original source"
            ),
        )

    # All checks passed
    size_bytes = os.path.getsize(path)
    if size_bytes >= 1_048_576:
        size_str = f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes} bytes"

    return CheckResult(
        name="existence",
        status="pass",
        message=f"File exists and is readable ({size_str})",
        remediation="",
        details={"size_bytes": size_bytes},
    )


def check_format(file_path: str) -> CheckResult:
    """Check that the file extension is a recognized format and content parses.

    Determines the file format from the extension (case-insensitive) and
    validates against RECOGNIZED_FORMATS. For text formats (csv, json, jsonl,
    xml, tsv), attempts to parse content to confirm the format matches.
    Binary formats (xlsx, parquet) rely on extension match only.

    Args:
        file_path: Path to the file to check.

    Returns:
        CheckResult with name="format".
    """
    extension = Path(file_path).suffix.lower()

    # Check if extension is recognized
    if extension not in RECOGNIZED_FORMATS:
        return CheckResult(
            name="format",
            status="fail",
            message=(
                f"Unrecognized file format: {extension}. "
                "Supported formats: csv, json, jsonl, xml, xlsx, parquet, tsv"
            ),
            remediation=(
                "Convert the file to one of the supported formats"
                " (CSV, JSON, JSONL, XML) before proceeding."
                " See Module 4 steering for format conversion guidance"
            ),
        )

    detected_format = RECOGNIZED_FORMATS[extension]

    # Binary formats: extension match is sufficient
    if detected_format in ("xlsx", "parquet"):
        return CheckResult(
            name="format",
            status="pass",
            message=f"Recognized format: {detected_format}",
            remediation="",
            details={"detected_format": detected_format},
        )

    # Text formats: attempt content parsing to confirm match
    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return CheckResult(
            name="format",
            status="fail",
            message=(
                f"File extension is {extension} but content does not"
                " match expected format"
            ),
            remediation=(
                f"The file content does not match the {extension} extension."
                " Verify the file was exported correctly,"
                " or rename it with the correct extension"
            ),
        )

    if not _validate_content(content, detected_format, file_path):
        return CheckResult(
            name="format",
            status="fail",
            message=(
                f"File extension is {extension} but content does not"
                " match expected format"
            ),
            remediation=(
                f"The file content does not match the {extension} extension."
                " Verify the file was exported correctly,"
                " or rename it with the correct extension"
            ),
        )

    return CheckResult(
        name="format",
        status="pass",
        message=f"Recognized format: {detected_format}",
        remediation="",
        details={"detected_format": detected_format},
    )


def _validate_content(content: str, fmt: str, file_path: str) -> bool:
    """Attempt to parse content to confirm it matches the declared format.

    Args:
        content: File content as a string.
        fmt: Expected format name (csv, json, jsonl, xml, tsv).
        file_path: Original file path (unused, kept for future diagnostics).

    Returns:
        True if content parses successfully, False otherwise.
    """
    try:
        if fmt in ("csv", "tsv"):
            delimiter = "\t" if fmt == "tsv" else ","
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
            # Must have at least a header row to be valid
            if not rows or not rows[0]:
                return False
            return True
        if fmt == "json":
            parsed = json.loads(content)
            return isinstance(parsed, (list, dict))
        if fmt == "jsonl":
            # At least one non-empty line must parse as JSON
            for line in content.splitlines():
                stripped = line.strip()
                if stripped:
                    json.loads(stripped)
                    return True
            return False
        if fmt == "xml":
            ET.fromstring(content)
            return True
    except (csv.Error, json.JSONDecodeError, ET.ParseError, ValueError):
        return False
    return False


def check_records(file_path: str, detected_format: str) -> CheckResult:
    """Count data records in the file based on its format.

    CSV/TSV: rows excluding the header. JSON: array length or 1 for object.
    JSONL: non-empty lines. XML: direct children of root element.
    Binary formats (xlsx, parquet) skip counting since stdlib cannot parse them.

    Args:
        file_path: Path to the file to check.
        detected_format: Format string from check_format (e.g. "csv", "json").

    Returns:
        CheckResult with name="records".
    """
    # Binary formats: skip counting
    if detected_format in ("xlsx", "parquet"):
        return CheckResult(
            name="records",
            status="pass",
            message=(
                f"Record count skipped for {detected_format}"
                " (no stdlib parser available)"
            ),
            remediation="",
        )

    try:
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return CheckResult(
            name="records",
            status="fail",
            message="File contains no data records",
            remediation=(
                "The file structure is valid but contains no data rows."
                " Re-export with data included, or check that the export"
                " query/filter returned results"
            ),
        )

    count = _count_records(content, detected_format, file_path)

    if count == 0:
        return CheckResult(
            name="records",
            status="fail",
            message="File contains no data records",
            remediation=(
                "The file structure is valid but contains no data rows."
                " Re-export with data included, or check that the export"
                " query/filter returned results"
            ),
        )

    return CheckResult(
        name="records",
        status="pass",
        message=f"Found {count} data records",
        remediation="",
        details={"record_count": count},
    )


def _count_records(content: str, fmt: str, file_path: str) -> int:
    """Count data records in file content based on format.

    Args:
        content: File content as a string.
        fmt: Format name (csv, json, jsonl, xml, tsv).
        file_path: Original file path (unused, kept for future diagnostics).

    Returns:
        Number of data records found. Returns 0 if content cannot be parsed.
    """
    try:
        if fmt in ("csv", "tsv"):
            delimiter = "\t" if fmt == "tsv" else ","
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)
            # Subtract 1 for header row
            return max(0, len(rows) - 1)

        if fmt == "json":
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return len(parsed)
            if isinstance(parsed, dict):
                return 1
            return 0

        if fmt == "jsonl":
            count = 0
            for line in content.splitlines():
                if line.strip():
                    count += 1
            return count

        if fmt == "xml":
            root = ET.fromstring(content)
            return len(list(root))

    except (csv.Error, json.JSONDecodeError, ET.ParseError, ValueError):
        return 0

    return 0


def check_encoding(file_path: str, detected_format: str) -> CheckResult:
    """Check file encoding for text-based formats.

    Skips binary formats (xlsx, parquet) with a pass result. For text formats,
    reads the first 8192 bytes and attempts UTF-8 decode, then falls back to
    latin-1, utf-16, cp1252 in order.

    Args:
        file_path: Path to the file to check.
        detected_format: Format string from check_format (e.g. "csv", "json").

    Returns:
        CheckResult with name="encoding".
    """
    # Binary formats: skip encoding check
    if detected_format in ("xlsx", "parquet"):
        return CheckResult(
            name="encoding",
            status="pass",
            message="Encoding check skipped for binary format",
            remediation="",
            details={"encoding": "binary"},
        )

    # Read first 8192 bytes for encoding detection
    try:
        with open(file_path, "rb") as fh:
            raw_bytes = fh.read(8192)
    except OSError:
        return CheckResult(
            name="encoding",
            status="fail",
            message=(
                "Unable to determine file encoding."
                " The file may be corrupted or use an unsupported encoding"
            ),
            remediation=(
                "The file may be corrupted. Re-download from the original source,"
                " or try opening it in a text editor to check for garbled characters"
            ),
        )

    # Try UTF-8 first
    try:
        raw_bytes.decode("utf-8")
        return CheckResult(
            name="encoding",
            status="pass",
            message="Encoding: utf-8",
            remediation="",
            details={"encoding": "utf-8"},
        )
    except (UnicodeDecodeError, ValueError):
        pass

    # Try fallback encodings
    for encoding in FALLBACK_ENCODINGS:
        try:
            raw_bytes.decode(encoding)
            warn_message = (
                f"File uses {encoding} encoding. UTF-8 is recommended."
                f" Consider converting with: python -c"
                f" \"open('output.csv','w',encoding='utf-8').write("
                f"open('{file_path}',encoding='{encoding}').read())\""
            )
            return CheckResult(
                name="encoding",
                status="warn",
                message=warn_message,
                remediation="",
                details={"encoding": encoding},
            )
        except (UnicodeDecodeError, ValueError):
            continue

    # No encoding worked
    return CheckResult(
        name="encoding",
        status="fail",
        message=(
            "Unable to determine file encoding."
            " The file may be corrupted or use an unsupported encoding"
        ),
        remediation=(
            "The file may be corrupted. Re-download from the original source,"
            " or try opening it in a text editor to check for garbled characters"
        ),
    )


# ── Orchestrator ──────────────────────────────────────────────────────────


def validate_file(file_path: str) -> ValidationReport:
    """Run all sanity checks on a single file and return a ValidationReport.

    Checks run in order: existence → format → records → encoding.
    If existence fails, remaining checks are skipped.
    If format fails, records and encoding checks are skipped.
    Populates report fields (format, record_count, encoding) from check details.

    Args:
        file_path: Path to the file to validate.

    Returns:
        ValidationReport with all check results and overall status.
    """
    file_name = Path(file_path).name
    checks: list[CheckResult] = []
    detected_format: str | None = None
    record_count: int | None = None
    encoding: str | None = None

    # 1. Existence check
    existence_result = check_existence(file_path)
    checks.append(existence_result)

    if existence_result.status == "fail":
        overall_status = "fail"
        return ValidationReport(
            file_path=file_path,
            file_name=file_name,
            format=detected_format,
            record_count=record_count,
            encoding=encoding,
            checks=checks,
            overall_status=overall_status,
        )

    # 2. Format check
    format_result = check_format(file_path)
    checks.append(format_result)

    if format_result.status == "fail":
        overall_status = "fail"
        return ValidationReport(
            file_path=file_path,
            file_name=file_name,
            format=detected_format,
            record_count=record_count,
            encoding=encoding,
            checks=checks,
            overall_status=overall_status,
        )

    detected_format = format_result.details.get("detected_format")

    # 3. Records check
    records_result = check_records(file_path, detected_format)
    checks.append(records_result)
    record_count = records_result.details.get("record_count")

    # 4. Encoding check
    encoding_result = check_encoding(file_path, detected_format)
    checks.append(encoding_result)
    encoding = encoding_result.details.get("encoding")

    # Determine overall status: pass only if all checks are pass or warn
    if any(c.status == "fail" for c in checks):
        overall_status = "fail"
    else:
        overall_status = "pass"

    return ValidationReport(
        file_path=file_path,
        file_name=file_name,
        format=detected_format,
        record_count=record_count,
        encoding=encoding,
        checks=checks,
        overall_status=overall_status,
    )


# ── Report Formatting ─────────────────────────────────────────────────────


def format_report_text(report: ValidationReport) -> str:
    """Format a ValidationReport as human-readable text with emoji indicators.

    Uses ✅ for pass, ❌ for fail, ⚠️ for warn. Pass reports get a single
    summary line. Fail reports list each check with remediation guidance.

    Args:
        report: The validation report to format.

    Returns:
        Formatted multi-line string.
    """
    if report.overall_status == "pass":
        record_str = str(report.record_count) if report.record_count is not None else "N/A"
        fmt_str = report.format if report.format else "unknown"
        enc_str = report.encoding if report.encoding else "unknown"
        return (
            f"\u2705 {report.file_name}: All checks passed"
            f" ({record_str} records, {fmt_str}, {enc_str})"
        )

    # Fail case
    lines: list[str] = []
    lines.append(
        f"\u274c {report.file_name}: {report.failure_count} check(s) failed"
        " \u2014 see details below"
    )
    for check in report.checks:
        if check.status == "fail":
            lines.append(f"  \u274c {check.name}: {check.message}")
            if check.remediation:
                lines.append(f"    \u2192 {check.remediation}")
        elif check.status == "warn":
            lines.append(f"  \u26a0\ufe0f {check.name}: {check.message}")

    return "\n".join(lines)


def format_report_json(reports: list[ValidationReport]) -> str:
    """Serialize a list of ValidationReports as a JSON array string.

    Each report includes file_path, file_name, format, record_count,
    encoding, overall_status, and a checks array with name, status, message.

    Args:
        reports: List of validation reports to serialize.

    Returns:
        JSON string with indent=2.
    """
    data = []
    for report in reports:
        entry = {
            "file_path": report.file_path,
            "file_name": report.file_name,
            "format": report.format,
            "record_count": report.record_count,
            "encoding": report.encoding,
            "overall_status": report.overall_status,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                }
                for c in report.checks
            ],
        }
        data.append(entry)
    return json.dumps(data, indent=2)


# ── Registry Update ───────────────────────────────────────────────────────


def update_registry(
    reports: list[ValidationReport],
    registry_path: str = "config/data_sources.yaml",
) -> None:
    """Update the data source registry with validation results.

    For each report, updates or creates a Registry_Entry keyed by the
    DATA_SOURCE name derived from the file name (uppercase, non-alphanumeric
    replaced with underscores, extension stripped).

    Fields written per entry: validation_status, validation_checks,
    record_count, encoding, updated_at.

    Creates the registry file with version "1" and empty sources if it
    does not exist.

    Args:
        reports: List of validation reports.
        registry_path: Path to the registry YAML file.
    """
    import re
    from datetime import datetime, timezone

    # Import YAML helpers from data_sources.py (same directory)
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from data_sources import parse_registry_yaml, serialize_registry_yaml

    # Read existing registry or create a new one
    registry_file = Path(registry_path)
    if registry_file.exists():
        content = registry_file.read_text(encoding="utf-8")
        registry_data = parse_registry_yaml(content)
    else:
        registry_data = {"version": "1", "sources": {}}

    sources = registry_data.get("sources")
    if sources is None or not isinstance(sources, dict):
        sources = {}
        registry_data["sources"] = sources

    now_iso = datetime.now(timezone.utc).isoformat()

    for report in reports:
        # Derive DATA_SOURCE key: strip extension, uppercase, replace non-alnum with _
        stem = Path(report.file_name).stem
        key = re.sub(r"[^A-Za-z0-9]", "_", stem).upper()

        # Build validation_checks mapping from individual check results
        validation_checks: dict[str, str] = {}
        for check in report.checks:
            validation_checks[check.name] = check.status

        # Determine validation_status from overall_status
        validation_status = "passed" if report.overall_status == "pass" else "failed"

        # Get or create the entry
        if key not in sources or not isinstance(sources[key], dict):
            sources[key] = {}

        entry = sources[key]
        entry["validation_status"] = validation_status
        entry["validation_checks"] = validation_checks
        if report.record_count is not None:
            entry["record_count"] = report.record_count
        if report.encoding is not None:
            entry["encoding"] = report.encoding
        entry["updated_at"] = now_iso

    # Write back
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    serialized = serialize_registry_yaml(registry_data)
    registry_file.write_text(serialized, encoding="utf-8")


# ── Entry Point ───────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for validate_data_files.py.

    No args: scan all files in data/raw/ and validate each.
    Positional args: validate only specified files.
    --update-registry: update config/data_sources.yaml with results.
    --json: output as JSON array instead of text.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 if all files pass, 1 if any file fails.
    """
    parser = argparse.ArgumentParser(
        description="Validate data source files for the Senzing bootcamp.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="File paths to validate. If omitted, scans all files in data/raw/.",
    )
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Update config/data_sources.yaml with validation results.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output validation reports as a JSON array.",
    )
    args = parser.parse_args(argv)

    # Determine which files to validate
    if args.files:
        file_paths = args.files
    else:
        raw_dir = Path("data/raw")
        if not raw_dir.is_dir():
            print("No data/raw/ directory found", file=sys.stderr)
            return 1
        file_paths = sorted(str(p) for p in raw_dir.iterdir() if p.is_file())
        if not file_paths:
            print("No files found in data/raw/")
            return 0

    # Validate each file
    reports: list[ValidationReport] = []
    for fp in file_paths:
        reports.append(validate_file(fp))

    # Output results
    if args.json_output:
        print(format_report_json(reports))
    else:
        for report in reports:
            print(format_report_text(report))

    # Update registry if requested
    if args.update_registry:
        update_registry(reports)

    # Exit code: 0 if all pass, 1 if any fail
    if any(r.overall_status == "fail" for r in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
