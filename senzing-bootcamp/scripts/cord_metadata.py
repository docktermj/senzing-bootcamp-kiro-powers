#!/usr/bin/env python3
"""Senzing Bootcamp - CORD Data Freshness Metadata.

Captures and verifies CORD dataset metadata for freshness checks between
Module 4 (data collection) and Module 6 (data loading).

Usage:
    python scripts/cord_metadata.py capture --dataset cord-las-vegas --files data/raw/cord-las-vegas.jsonl
    python scripts/cord_metadata.py check
    python scripts/cord_metadata.py check --metadata config/cord_metadata.yaml

Depends only on the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass
class SourceMetadata:
    """Metadata for a single CORD data source file."""

    name: str
    file_path: str
    record_count: int
    file_size_bytes: int


@dataclass
class CordMetadata:
    """Complete CORD dataset metadata snapshot."""

    dataset_name: str
    sources: list[SourceMetadata]
    download_date: str  # ISO 8601
    content_hash: str   # SHA-256
    schema_version: str = "1"


@dataclass
class FreshnessResult:
    """Result of a freshness check."""

    status: str          # "fresh", "stale", "skipped"
    message: str
    mismatches: list[dict] = field(default_factory=list)


# ── Minimal YAML Serializer ──────────────────────────────────────────────


def _serialize_scalar(value: object) -> str:
    """Convert a Python value to a YAML scalar string."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        # Quote strings that could be confused with other types
        if value in ("null", "~", "true", "false"):
            return f'"{value}"'
        try:
            int(value)
            return f'"{value}"'
        except ValueError:
            pass
        if " " in value or ":" in value or '"' in value or "'" in value:
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return f'"{value}"'
    return str(value)


def serialize_metadata(metadata: CordMetadata) -> str:
    """Serialize a CordMetadata object to a YAML string.

    Uses a custom minimal serializer (no PyYAML dependency).
    Produces output compatible with parse_metadata().

    Args:
        metadata: CordMetadata object to serialize.

    Returns:
        YAML-formatted string.
    """
    lines: list[str] = []

    lines.append(f"schema_version: {_serialize_scalar(metadata.schema_version)}")
    lines.append(f"dataset_name: {_serialize_scalar(metadata.dataset_name)}")
    lines.append("sources:")

    for source in metadata.sources:
        lines.append(f"  - name: {_serialize_scalar(source.name)}")
        lines.append(f"    file_path: {_serialize_scalar(source.file_path)}")
        lines.append(f"    record_count: {source.record_count}")
        lines.append(f"    file_size_bytes: {source.file_size_bytes}")

    lines.append(f"download_date: {_serialize_scalar(metadata.download_date)}")
    lines.append(f"content_hash: {_serialize_scalar(metadata.content_hash)}")

    return "\n".join(lines) + "\n"


# ── Minimal YAML Parser ──────────────────────────────────────────────────


def _unquote(s: str) -> str:
    """Remove surrounding quotes from a YAML scalar value and unescape."""
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        # Handle escaped quotes inside double-quoted strings
        return s[1:-1].replace('\\"', '"')
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


def _parse_scalar(value: str) -> str | int | None:
    """Convert a YAML scalar string to a Python value."""
    stripped = value.strip()
    if not stripped:
        return None
    unquoted = _unquote(stripped)
    # If it was quoted, return as string
    if unquoted != stripped:
        return unquoted
    if stripped == "null" or stripped == "~":
        return None
    # Try integer
    try:
        return int(stripped)
    except ValueError:
        pass
    return stripped


def parse_metadata(yaml_content: str) -> CordMetadata:
    """Parse a YAML string into a CordMetadata object.

    Supports the restricted YAML subset produced by serialize_metadata().

    Args:
        yaml_content: YAML-formatted string.

    Returns:
        CordMetadata object.

    Raises:
        ValueError: If the YAML content cannot be parsed into valid metadata.
    """
    lines = yaml_content.splitlines()
    top_level: dict[str, object] = {}
    sources: list[dict[str, object]] = []
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Skip blank / comment lines
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        # Check for list item start (source entry)
        if stripped.startswith("- "):
            # Start of a new source entry
            current_source: dict[str, object] = {}
            # Parse the first field on the same line as the dash
            field_part = stripped[2:]  # Remove "- "
            colon_pos = field_part.find(":")
            if colon_pos > 0:
                key = field_part[:colon_pos].strip()
                val = field_part[colon_pos + 1:].strip()
                current_source[key] = _parse_scalar(val)

            # Parse continuation fields (indented at same level or deeper)
            idx += 1
            while idx < len(lines):
                cline = lines[idx]
                cstripped = cline.strip()

                if not cstripped or cstripped.startswith("#"):
                    idx += 1
                    continue

                # If it's a new list item or a top-level key, stop
                if cstripped.startswith("- "):
                    break
                if cline and not cline[0].isspace():
                    break

                # Parse field: value
                colon_pos = cstripped.find(":")
                if colon_pos > 0:
                    key = cstripped[:colon_pos].strip()
                    val = cstripped[colon_pos + 1:].strip()
                    current_source[key] = _parse_scalar(val)
                idx += 1

            sources.append(current_source)
            continue

        # Top-level key: value (no leading whitespace)
        if line and not line[0].isspace():
            colon_pos = stripped.find(":")
            if colon_pos > 0:
                key = stripped[:colon_pos].strip()
                val = stripped[colon_pos + 1:].strip()
                if key == "sources":
                    # The sources list follows on subsequent lines
                    idx += 1
                    continue
                top_level[key] = _parse_scalar(val)
            idx += 1
            continue

        idx += 1

    # Build SourceMetadata objects
    source_objects: list[SourceMetadata] = []
    for src in sources:
        source_objects.append(SourceMetadata(
            name=str(src.get("name", "")),
            file_path=str(src.get("file_path", "")),
            record_count=int(src.get("record_count", 0)),
            file_size_bytes=int(src.get("file_size_bytes", 0)),
        ))

    schema_version = str(top_level.get("schema_version", "1"))
    dataset_name = str(top_level.get("dataset_name", ""))
    download_date = str(top_level.get("download_date", ""))
    content_hash = str(top_level.get("content_hash", ""))

    return CordMetadata(
        dataset_name=dataset_name,
        sources=source_objects,
        download_date=download_date,
        content_hash=content_hash,
        schema_version=schema_version,
    )


# ── Content Hash ─────────────────────────────────────────────────────────


def compute_content_hash(file_path: str, max_records: int = 100) -> str:
    """Compute SHA-256 hash of the first N records in a JSONL file.

    Args:
        file_path: Path to the JSONL file.
        max_records: Maximum number of records to hash (default 100).

    Returns:
        SHA-256 hex digest string.
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_records:
                    break
                hasher.update(line.encode("utf-8"))
    except OSError:
        return ""
    return hasher.hexdigest()


# ── Core Functions ───────────────────────────────────────────────────────


def capture_metadata(
    dataset_name: str,
    source_files: list[str],
    output_path: str = "config/cord_metadata.yaml",
) -> CordMetadata | None:
    """Capture metadata for downloaded CORD files and write to YAML.

    Args:
        dataset_name: CORD dataset identifier (e.g., "cord-las-vegas").
        source_files: List of file paths to capture metadata for.
        output_path: Path to write the metadata YAML file.

    Returns:
        CordMetadata object, or None if no valid sources found.
    """
    sources: list[SourceMetadata] = []

    for file_path in source_files:
        if not os.path.isfile(file_path):
            print(f"Warning: file not found, skipping: {file_path}", file=sys.stderr)
            continue

        # Count records (lines in JSONL)
        record_count = 0
        try:
            with open(file_path, encoding="utf-8") as f:
                for _ in f:
                    record_count += 1
        except OSError as exc:
            print(f"Warning: cannot read {file_path}: {exc}", file=sys.stderr)
            continue

        # Get file size
        file_size_bytes = os.path.getsize(file_path)

        # Derive source name from filename
        name = Path(file_path).stem.upper().replace("-", "_")

        sources.append(SourceMetadata(
            name=name,
            file_path=file_path,
            record_count=record_count,
            file_size_bytes=file_size_bytes,
        ))

    if not sources:
        return None

    # Compute content hash from first valid source file
    content_hash = compute_content_hash(sources[0].file_path)

    # Generate download timestamp
    download_date = datetime.now(timezone.utc).isoformat()

    metadata = CordMetadata(
        dataset_name=dataset_name,
        sources=sources,
        download_date=download_date,
        content_hash=content_hash,
    )

    # Write to file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(serialize_metadata(metadata))

    return metadata


def check_freshness(
    metadata_path: str = "config/cord_metadata.yaml",
) -> FreshnessResult:
    """Check stored metadata against current file state on disk.

    This function is advisory only and NEVER raises an exception.
    Any unexpected error is caught and results in a "skipped" status.

    Args:
        metadata_path: Path to the metadata YAML file.

    Returns:
        FreshnessResult with status "fresh", "stale", or "skipped".
    """
    try:
        return _check_freshness_inner(metadata_path)
    except Exception:
        return FreshnessResult(
            status="skipped",
            message="Unexpected error during freshness check. Skipping.",
        )


def _check_freshness_inner(metadata_path: str) -> FreshnessResult:
    """Internal implementation of check_freshness.

    Args:
        metadata_path: Path to the metadata YAML file.

    Returns:
        FreshnessResult with status "fresh", "stale", or "skipped".
    """
    # Read metadata file
    try:
        with open(metadata_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return FreshnessResult(
            status="skipped",
            message="No CORD metadata found. Skipping freshness check.",
        )
    except OSError:
        return FreshnessResult(
            status="skipped",
            message="Could not read metadata file. Skipping freshness check.",
        )

    # Parse metadata
    try:
        metadata = parse_metadata(content)
    except (ValueError, KeyError, TypeError):
        return FreshnessResult(
            status="skipped",
            message="Could not parse metadata file. Skipping freshness check.",
        )

    if not metadata.sources:
        return FreshnessResult(
            status="skipped",
            message="No sources in metadata. Skipping freshness check.",
        )

    # Compare each source against current file state
    mismatches: list[dict] = []

    for source in metadata.sources:
        file_path = source.file_path

        # Check if file exists
        if not os.path.isfile(file_path):
            mismatches.append({
                "source": source.name,
                "field": "file_path",
                "expected": file_path,
                "actual": "FILE_MISSING",
                "message": f"{source.name}: file missing ({file_path})",
            })
            continue

        # Check file size
        try:
            current_size = os.path.getsize(file_path)
        except OSError:
            mismatches.append({
                "source": source.name,
                "field": "file_size_bytes",
                "expected": source.file_size_bytes,
                "actual": "UNREADABLE",
                "message": f"{source.name}: cannot read file size",
            })
            continue

        if current_size != source.file_size_bytes:
            mismatches.append({
                "source": source.name,
                "field": "file_size_bytes",
                "expected": source.file_size_bytes,
                "actual": current_size,
                "message": (
                    f"{source.name}: file size changed "
                    f"(expected {source.file_size_bytes}, got {current_size})"
                ),
            })

        # Check record count
        try:
            current_count = 0
            with open(file_path, encoding="utf-8") as f:
                for _ in f:
                    current_count += 1
        except (OSError, UnicodeDecodeError):
            mismatches.append({
                "source": source.name,
                "field": "record_count",
                "expected": source.record_count,
                "actual": "UNREADABLE",
                "message": f"{source.name}: cannot count records",
            })
            continue

        if current_count != source.record_count:
            mismatches.append({
                "source": source.name,
                "field": "record_count",
                "expected": source.record_count,
                "actual": current_count,
                "message": (
                    f"{source.name}: record count changed "
                    f"(expected {source.record_count}, got {current_count})"
                ),
            })

    if mismatches:
        messages = [m["message"] for m in mismatches]
        return FreshnessResult(
            status="stale",
            message=(
                "Your CORD data files may have changed since download. "
                "This could affect entity resolution results. "
                "Mismatches: " + "; ".join(messages)
            ),
            mismatches=mismatches,
        )

    return FreshnessResult(
        status="fresh",
        message="All CORD data files match stored metadata. Data is fresh.",
    )


# ── CLI Entry Point ──────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point with capture/check subcommands.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="CORD Data Freshness - capture and verify dataset metadata"
    )
    subparsers = parser.add_subparsers(dest="command")

    # capture subcommand
    capture_parser = subparsers.add_parser(
        "capture", help="Capture metadata for downloaded CORD files"
    )
    capture_parser.add_argument(
        "--dataset", required=True, help="Dataset name (e.g., cord-las-vegas)"
    )
    capture_parser.add_argument(
        "--files", nargs="+", required=True, help="Paths to CORD data files"
    )
    capture_parser.add_argument(
        "--output",
        default="config/cord_metadata.yaml",
        help="Output metadata file path (default: config/cord_metadata.yaml)",
    )

    # check subcommand
    check_parser = subparsers.add_parser(
        "check", help="Check stored metadata against current files"
    )
    check_parser.add_argument(
        "--metadata",
        default="config/cord_metadata.yaml",
        help="Path to metadata file (default: config/cord_metadata.yaml)",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "capture":
        result = capture_metadata(args.dataset, args.files, args.output)
        if result is None:
            print("Error: no valid source files found.", file=sys.stderr)
            return 1
        print(f"Metadata captured for {result.dataset_name} "
              f"({len(result.sources)} source(s)) → {args.output}")
        return 0

    if args.command == "check":
        result = check_freshness(args.metadata)
        if result.status == "fresh":
            print(f"✅ {result.message}")
        elif result.status == "stale":
            # Warning message per Requirement 4
            print(
                "⚠️  Your CORD data files may have changed since download. "
                "This could affect entity resolution results. "
                "Options: (a) re-download fresh data, (b) proceed with current "
                "files, (c) check what changed"
            )
            if result.mismatches:
                print("\nDetails:")
                for m in result.mismatches:
                    print(f"  - {m['message']}")
        else:
            # skipped
            print(result.message)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
