#!/usr/bin/env python3
"""Senzing Bootcamp - Data Source Registry.

Reads and displays the data source registry at config/data_sources.yaml.
Provides CLI views (table, detail, summary) and integration with status.py.
Depends only on the Python standard library.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass


# ── Constants ─────────────────────────────────────────────────────────────

VALID_FORMATS = {"csv", "json", "jsonl", "xlsx", "parquet", "xml", "other"}
VALID_MAPPING_STATUSES = {"pending", "in_progress", "complete"}
VALID_LOAD_STATUSES = {"not_loaded", "loading", "loaded", "failed"}
VALID_TEST_LOAD_STATUSES = {"complete", "skipped"}
REQUIRED_ENTRY_FIELDS = {
    "name", "file_path", "format", "record_count", "quality_score",
    "mapping_status", "load_status", "added_at", "updated_at",
}
QUALITY_THRESHOLD = 70
DATA_SOURCE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass
class RegistryEntry:
    """A single data source record within the registry."""

    data_source: str
    name: str
    file_path: str
    format: str
    record_count: int | None
    file_size_bytes: int | None
    quality_score: int | None
    mapping_status: str
    load_status: str
    added_at: str
    updated_at: str
    test_load_status: str | None = None
    test_entity_count: int | None = None
    issues: list[str] | None = None


@dataclass
class Registry:
    """Parsed and validated data source registry."""

    version: str
    sources: list[RegistryEntry]

    def by_load_status(self, status: str) -> list[RegistryEntry]:
        """Return entries matching the given load_status."""
        return [e for e in self.sources if e.load_status == status]

    def by_mapping_status(self, status: str) -> list[RegistryEntry]:
        """Return entries matching the given mapping_status."""
        return [e for e in self.sources if e.mapping_status == status]

    def low_quality_sources(self, threshold: int = QUALITY_THRESHOLD) -> list[RegistryEntry]:
        """Return entries with quality_score below threshold."""
        return [
            e for e in self.sources
            if e.quality_score is not None and e.quality_score < threshold
        ]

    def average_quality(self) -> float | None:
        """Return average quality_score across entries that have one, or None."""
        scores = [e.quality_score for e in self.sources if e.quality_score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def total_records(self) -> int:
        """Return sum of all non-null record_count values."""
        return sum(e.record_count for e in self.sources if e.record_count is not None)


# ── Minimal YAML Parser ──────────────────────────────────────────────────


def _unquote(s: str) -> str:
    """Remove surrounding quotes from a YAML scalar value."""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _parse_scalar(value: str):
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
    if stripped == "true":
        return True
    if stripped == "false":
        return False
    # Try integer
    try:
        return int(stripped)
    except ValueError:
        pass
    return stripped


def parse_registry_yaml(content: str) -> dict:
    """Parse the restricted YAML subset used by data_sources.yaml.

    Supports:
      - Top-level ``version`` scalar
      - Top-level ``sources`` mapping of DATA_SOURCE keys
      - Each source has scalar fields and an optional ``issues`` list

    Returns dict with 'version' and 'sources' keys.
    """
    result: dict = {}
    lines = content.splitlines()
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Skip blank / comment lines
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        # Top-level key (no leading whitespace)
        if not line[0].isspace():
            m = re.match(r"^(\w[\w_]*):\s*(.*)", line)
            if not m:
                idx += 1
                continue

            key = m.group(1)
            value_part = m.group(2).strip()

            if key == "sources":
                # Parse the sources mapping
                idx += 1
                sources: dict = {}
                while idx < len(lines):
                    sline = lines[idx]
                    sstripped = sline.strip()

                    if not sstripped or sstripped.startswith("#"):
                        idx += 1
                        continue

                    # Check if we've left the sources block (non-indented line)
                    if not sline[0].isspace():
                        break

                    # Source key line: "  DATA_SOURCE_KEY:"
                    sk_match = re.match(r"^  (\w[\w_]*):\s*(.*)", sline)
                    if not sk_match:
                        idx += 1
                        continue

                    source_key = sk_match.group(1)
                    source_val = sk_match.group(2).strip()
                    if source_val and not source_val.startswith("#"):
                        # Inline scalar (shouldn't happen for sources, but handle)
                        sources[source_key] = _parse_scalar(source_val)
                        idx += 1
                        continue

                    # Parse nested fields for this source
                    idx += 1
                    entry: dict = {}
                    while idx < len(lines):
                        fline = lines[idx]
                        fstripped = fline.strip()

                        if not fstripped or fstripped.startswith("#"):
                            idx += 1
                            continue

                        # Check indent level — must be deeper than source key (4+ spaces)
                        indent_match = re.match(r"^(\s+)", fline)
                        if not indent_match or len(indent_match.group(1)) < 4:
                            break

                        # Field: value
                        fk_match = re.match(r"^\s{4,}(\w[\w_]*):\s*(.*)", fline)
                        if fk_match:
                            fkey = fk_match.group(1)
                            fval = fk_match.group(2).strip()

                            if fkey == "issues" and (not fval or fval.startswith("#")):
                                # Parse issues list
                                idx += 1
                                issues_list: list = []
                                while idx < len(lines):
                                    iline = lines[idx]
                                    istripped = iline.strip()
                                    if not istripped or istripped.startswith("#"):
                                        idx += 1
                                        continue
                                    # List item under issues (6+ spaces, starts with -)
                                    i_match = re.match(r"^\s{6,}-\s+(.*)", iline)
                                    if i_match:
                                        issues_list.append(_unquote(i_match.group(1).strip()))
                                        idx += 1
                                    else:
                                        break
                                entry["issues"] = issues_list
                            else:
                                entry[fkey] = _parse_scalar(fval)
                                idx += 1
                        else:
                            idx += 1

                    sources[source_key] = entry

                result["sources"] = sources
            else:
                # Simple top-level scalar
                if value_part and not value_part.startswith("#"):
                    result[key] = _parse_scalar(value_part)
                else:
                    result[key] = None
                idx += 1
        else:
            idx += 1

    return result


def serialize_registry_yaml(data: dict) -> str:
    """Serialize a registry dict back to YAML string.

    Preserves field order and represents None as ``null``.
    """
    lines: list[str] = []

    version = data.get("version")
    if version is not None:
        lines.append(f'version: "{version}"')
    else:
        lines.append("version: null")

    lines.append("sources:")

    sources = data.get("sources", {})
    if isinstance(sources, dict):
        for src_key, entry in sources.items():
            lines.append(f"  {src_key}:")
            if not isinstance(entry, dict):
                continue

            # Ordered field output
            field_order = [
                "name", "file_path", "format", "record_count",
                "file_size_bytes", "quality_score", "mapping_status",
                "load_status", "test_load_status", "test_entity_count",
                "added_at", "updated_at",
            ]
            for fk in field_order:
                if fk in entry:
                    lines.append(f"    {fk}: {_serialize_scalar(entry[fk])}")

            # Issues list last
            if "issues" in entry:
                issues = entry["issues"]
                if issues is None:
                    lines.append("    issues: null")
                elif isinstance(issues, list):
                    lines.append("    issues:")
                    for issue in issues:
                        lines.append(f'      - "{issue}"')

            # Any remaining fields not in field_order or issues
            for fk, fv in entry.items():
                if fk not in field_order and fk != "issues":
                    lines.append(f"    {fk}: {_serialize_scalar(fv)}")

    return "\n".join(lines) + "\n"


def _serialize_scalar(value) -> str:
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
        return value
    return str(value)


# ── Validator ─────────────────────────────────────────────────────────────


def validate_registry(raw: dict) -> list[str]:
    """Validate registry structure. Returns list of error strings (empty = valid).

    Checks:
      - ``version`` field present and equals ``"1"``
      - ``sources`` is a mapping
      - Each source key matches ``^[A-Z][A-Z0-9_]*$``
      - Each entry has all required fields
      - Enum fields contain only valid values
    """
    errors: list[str] = []

    # Version check
    version = raw.get("version")
    if version is None:
        errors.append("Missing required field: 'version'")
    elif str(version) != "1":
        errors.append(f"'version' must be \"1\", got {version!r}")

    # Sources check
    sources = raw.get("sources")
    if sources is None:
        errors.append("Missing required field: 'sources'")
        return errors
    if not isinstance(sources, dict):
        errors.append("'sources' must be a mapping")
        return errors

    for key, entry in sources.items():
        # Key format
        if not DATA_SOURCE_KEY_RE.match(str(key)):
            errors.append(
                f"Invalid DATA_SOURCE key {key!r}: "
                f"must match ^[A-Z][A-Z0-9_]*$"
            )

        if not isinstance(entry, dict):
            errors.append(f"{key}: entry must be a mapping")
            continue

        # Required fields
        for req in sorted(REQUIRED_ENTRY_FIELDS):
            if req not in entry:
                errors.append(f"{key}: missing required field '{req}'")

        # Enum validation
        fmt = entry.get("format")
        if fmt is not None and fmt not in VALID_FORMATS:
            errors.append(
                f"{key}: invalid format {fmt!r}, "
                f"must be one of {sorted(VALID_FORMATS)}"
            )

        ms = entry.get("mapping_status")
        if ms is not None and ms not in VALID_MAPPING_STATUSES:
            errors.append(
                f"{key}: invalid mapping_status {ms!r}, "
                f"must be one of {sorted(VALID_MAPPING_STATUSES)}"
            )

        ls = entry.get("load_status")
        if ls is not None and ls not in VALID_LOAD_STATUSES:
            errors.append(
                f"{key}: invalid load_status {ls!r}, "
                f"must be one of {sorted(VALID_LOAD_STATUSES)}"
            )

        tls = entry.get("test_load_status")
        if tls is not None and tls not in VALID_TEST_LOAD_STATUSES:
            errors.append(
                f"{key}: invalid test_load_status {tls!r}, "
                f"must be one of {sorted(VALID_TEST_LOAD_STATUSES)}"
            )

    return errors


# ── Registry Loading ──────────────────────────────────────────────────────


def _dict_to_registry(raw: dict) -> Registry:
    """Convert a validated raw dict to a Registry instance."""
    entries: list[RegistryEntry] = []
    for key, entry in raw.get("sources", {}).items():
        issues_raw = entry.get("issues")
        issues = list(issues_raw) if isinstance(issues_raw, list) else None
        entries.append(RegistryEntry(
            data_source=key,
            name=str(entry.get("name", "")),
            file_path=str(entry.get("file_path", "")),
            format=str(entry.get("format", "")),
            record_count=entry.get("record_count"),
            file_size_bytes=entry.get("file_size_bytes"),
            quality_score=entry.get("quality_score"),
            mapping_status=str(entry.get("mapping_status", "")),
            load_status=str(entry.get("load_status", "")),
            added_at=str(entry.get("added_at", "")),
            updated_at=str(entry.get("updated_at", "")),
            test_load_status=entry.get("test_load_status"),
            test_entity_count=entry.get("test_entity_count"),
            issues=issues,
        ))
    return Registry(version=str(raw.get("version", "")), sources=entries)


def _registry_to_dict(registry: Registry) -> dict:
    """Convert a Registry instance back to a raw dict for serialization."""
    sources: dict = {}
    for entry in registry.sources:
        d: dict = {
            "name": entry.name,
            "file_path": entry.file_path,
            "format": entry.format,
            "record_count": entry.record_count,
            "file_size_bytes": entry.file_size_bytes,
            "quality_score": entry.quality_score,
            "mapping_status": entry.mapping_status,
            "load_status": entry.load_status,
            "added_at": entry.added_at,
            "updated_at": entry.updated_at,
        }
        if entry.test_load_status is not None:
            d["test_load_status"] = entry.test_load_status
        if entry.test_entity_count is not None:
            d["test_entity_count"] = entry.test_entity_count
        if entry.issues is not None:
            d["issues"] = entry.issues
        sources[entry.data_source] = d
    return {"version": registry.version, "sources": sources}


# ── Rendering Functions ───────────────────────────────────────────────────


def render_table(registry: Registry) -> str:
    """Render a formatted table of all registry entries.

    Columns: DATA_SOURCE, Records, Quality, Mapping, Load Status.
    Shows ``-`` for null values and ``⚠`` for low-quality sources.
    """
    lines: list[str] = []
    lines.append("Data Source Registry")
    lines.append("━" * 74)
    header = (
        f"{'DATA_SOURCE':<19}"
        f"{'Records':>8}"
        f"{'Quality':>9}"
        f"{'Mapping':>12}"
        f"{'Load Status':>14}"
    )
    lines.append(header)
    lines.append(
        f"{'─' * 17}  "
        f"{'─' * 7}  "
        f"{'─' * 7}  "
        f"{'─' * 10}  "
        f"{'─' * 11}"
    )

    for entry in registry.sources:
        records_str = f"{entry.record_count:,}" if entry.record_count is not None else "-"
        quality_str = f"{entry.quality_score}%" if entry.quality_score is not None else "-"
        low_q = (
            entry.quality_score is not None
            and entry.quality_score < QUALITY_THRESHOLD
        )
        warn = "  ⚠" if low_q else ""
        row = (
            f"{entry.data_source:<19}"
            f"{records_str:>8}"
            f"{quality_str:>9}"
            f"{entry.mapping_status:>12}"
            f"{entry.load_status:>14}"
            f"{warn}"
        )
        lines.append(row)

    lines.append("━" * 74)
    return "\n".join(lines)


def render_detail(entry: RegistryEntry) -> str:
    """Render all fields for a single registry entry."""
    lines: list[str] = []
    lines.append(f"Data Source: {entry.data_source}")
    lines.append("━" * 40)
    lines.append(f"  Name:           {entry.name}")
    lines.append(f"  File Path:      {entry.file_path}")
    lines.append(f"  Format:         {entry.format}")
    rc = f"{entry.record_count:,}" if entry.record_count is not None else "-"
    lines.append(f"  Record Count:   {rc}")
    fs = f"{entry.file_size_bytes:,}" if entry.file_size_bytes is not None else "-"
    lines.append(f"  File Size:      {fs}")
    qs = f"{entry.quality_score}%" if entry.quality_score is not None else "-"
    lines.append(f"  Quality Score:  {qs}")
    lines.append(f"  Mapping Status: {entry.mapping_status}")
    lines.append(f"  Load Status:    {entry.load_status}")
    tls = entry.test_load_status if entry.test_load_status is not None else "-"
    lines.append(f"  Test Load:      {tls}")
    tec = f"{entry.test_entity_count:,}" if entry.test_entity_count is not None else "-"
    lines.append(f"  Test Entities:  {tec}")
    lines.append(f"  Added:          {entry.added_at}")
    lines.append(f"  Updated:        {entry.updated_at}")
    if entry.issues:
        lines.append("  Issues:")
        for issue in entry.issues:
            lines.append(f"    - {issue}")
    lines.append("━" * 40)
    return "\n".join(lines)


def render_summary(registry: Registry) -> str:
    """Render aggregate statistics for the registry."""
    lines: list[str] = []
    lines.append("Data Source Summary")
    lines.append("━" * 74)

    total = len(registry.sources)
    lines.append(f"Total sources:     {total}")

    avg_q = registry.average_quality()
    if avg_q is not None:
        lines.append(f"Avg quality score: {round(avg_q)}%")

    total_rec = registry.total_records()
    lines.append(f"Total records:     {total_rec:,}")
    lines.append("")

    # By mapping status
    ms_parts = []
    for ms in ("pending", "in_progress", "complete"):
        count = len(registry.by_mapping_status(ms))
        ms_parts.append(f"{ms}: {count}")
    lines.append(f"By mapping status:  {'  '.join(ms_parts)}")

    # By load status
    ls_parts = []
    for ls in ("not_loaded", "loading", "loaded", "failed"):
        count = len(registry.by_load_status(ls))
        ls_parts.append(f"{ls}: {count}")
    lines.append(f"By load status:     {'  '.join(ls_parts)}")

    lines.append("━" * 74)
    return "\n".join(lines)


# ── Recommendation Engine ─────────────────────────────────────────────────


def recommend_actions(registry: Registry) -> list[str]:
    """Generate agent recommendations based on registry state.

    Returns list of recommendation strings:
      - Low quality sources that should be fixed before loading
      - Unmapped sources that need mapping before loading
      - Suggested load order by quality score (descending)
    """
    recs: list[str] = []

    # Low quality + not loaded
    for entry in registry.sources:
        if (
            entry.quality_score is not None
            and entry.quality_score < QUALITY_THRESHOLD
            and entry.load_status == "not_loaded"
        ):
            recs.append(
                f"⚠ {entry.data_source}: quality score {entry.quality_score}% "
                f"is below threshold ({QUALITY_THRESHOLD}%). "
                f"Recommend fixing data quality before loading."
            )

    # Pending mapping + not loaded
    for entry in registry.sources:
        if entry.mapping_status == "pending" and entry.load_status == "not_loaded":
            recs.append(
                f"⚠ {entry.data_source}: mapping is pending. "
                f"Complete mapping before loading."
            )

    # Load order by quality descending (only sources with quality scores)
    scored = [
        e for e in registry.sources
        if e.quality_score is not None
    ]
    if len(scored) > 1:
        ordered = sorted(scored, key=lambda e: e.quality_score, reverse=True)
        order_parts = [
            f"{e.data_source} ({e.quality_score}%)" for e in ordered
        ]
        recs.append(f"Recommended load order: {', '.join(order_parts)}")

    return recs


# ── Status Integration ────────────────────────────────────────────────────


def render_data_sources_section(
    registry_path: str = "config/data_sources.yaml",
    _read_file=None,
) -> str | None:
    """Read registry and return formatted 'Data Sources' section string.

    Returns None if the registry file does not exist.
    Includes load status counts and quality warnings.

    The ``_read_file`` parameter allows injecting a custom file reader
    for testing (callable that takes a path and returns content string,
    or raises FileNotFoundError).
    """
    if _read_file is None:
        def _read_file(p):
            with open(p, encoding="utf-8") as f:
                return f.read()

    try:
        content = _read_file(registry_path)
    except FileNotFoundError:
        return None

    raw = parse_registry_yaml(content)
    errors = validate_registry(raw)
    if errors:
        return None

    registry = _dict_to_registry(raw)

    lines: list[str] = []
    lines.append("Data Sources:")

    # Load status counts
    loaded = len(registry.by_load_status("loaded"))
    not_loaded = len(registry.by_load_status("not_loaded"))
    loading = len(registry.by_load_status("loading"))
    failed = len(registry.by_load_status("failed"))
    lines.append(
        f"    loaded: {loaded}  not_loaded: {not_loaded}"
        f"  loading: {loading}  failed: {failed}"
    )

    # Quality warnings
    low_q = registry.low_quality_sources()
    if low_q:
        names = ", ".join(
            f"{e.data_source} ({e.quality_score}%)" for e in low_q
        )
        lines.append(f"    ⚠ Low quality: {names}")

    return "\n".join(lines)


# ── CLI Entry Point ───────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    No args: display table of all sources.
    --detail <DATA_SOURCE>: display all fields for one source.
    --summary: display aggregate statistics.
    Returns 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Data Source Registry"
    )
    parser.add_argument(
        "--detail",
        metavar="DATA_SOURCE",
        help="Show all fields for a specific data source",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show aggregate statistics",
    )
    args = parser.parse_args(argv)

    registry_path = os.path.join("config", "data_sources.yaml")

    # Read file
    try:
        with open(registry_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("No data sources registered yet.")
        print(f"The registry file ({registry_path}) does not exist.")
        return 0
    except UnicodeDecodeError as exc:
        print(f"Error: cannot read {registry_path}: {exc}", file=sys.stderr)
        return 1

    # Parse
    try:
        raw = parse_registry_yaml(content)
    except Exception as exc:
        print(f"Error: failed to parse {registry_path}: {exc}", file=sys.stderr)
        return 1

    # Validate
    errors = validate_registry(raw)
    if errors:
        print(f"Validation errors in {registry_path}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    registry = _dict_to_registry(raw)

    # Detail view
    if args.detail:
        target = args.detail
        for entry in registry.sources:
            if entry.data_source == target:
                print(render_detail(entry))
                return 0
        # Not found
        available = [e.data_source for e in registry.sources]
        print(
            f"Error: DATA_SOURCE {target!r} not found.",
            file=sys.stderr,
        )
        if available:
            print(
                f"Available sources: {', '.join(available)}",
                file=sys.stderr,
            )
        return 1

    # Summary view
    if args.summary:
        print(render_summary(registry))
        return 0

    # Default: table view
    print(render_table(registry))
    return 0


if __name__ == "__main__":
    sys.exit(main())
