#!/usr/bin/env python3
"""Senzing Bootcamp - Compare ER Results.

Compares baseline and current entity resolution statistics to show the impact
of mapping changes. Produces a human-readable diff with quality assessment.

Usage:
    python3 scripts/compare_results.py --baseline <file> --current <file>
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = frozenset({
    "datasource",
    "entity_count",
    "record_count",
    "match_count",
    "possible_match_count",
    "relationship_count",
    "captured_at",
})


@dataclasses.dataclass
class ERStatistics:
    """Entity resolution statistics for a single datasource snapshot."""

    datasource: str
    entity_count: int
    record_count: int
    match_count: int
    possible_match_count: int
    relationship_count: int
    captured_at: str


@dataclasses.dataclass
class ComparisonResult:
    """Result of comparing two ERStatistics snapshots.

    Each delta field represents (current - baseline). A negative entity_delta
    means fewer entities (more deduplication). A positive match_delta means
    more matches found.
    """

    entity_delta: int
    record_delta: int
    match_delta: int
    possible_match_delta: int
    relationship_delta: int
    quality_assessment: str


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_statistics(path: str | Path) -> ERStatistics:
    """Read and validate a JSON statistics file.

    Args:
        path: Path to the JSON file containing ER statistics.

    Returns:
        An ERStatistics instance populated from the file.

    Raises:
        SystemExit: If the file is missing, contains invalid JSON, or is
            missing required fields.
    """
    filepath = Path(path)

    if not filepath.exists():
        print(f"Error: Statistics file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error: Cannot read file {filepath}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"Error: Failed to parse {filepath}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print(f"Error: Expected JSON object in {filepath}", file=sys.stderr)
        sys.exit(1)

    for field in REQUIRED_FIELDS:
        if field not in data:
            print(
                f"Error: Missing required field '{field}' in {filepath}",
                file=sys.stderr,
            )
            sys.exit(1)

    return ERStatistics(
        datasource=str(data["datasource"]),
        entity_count=int(data["entity_count"]),
        record_count=int(data["record_count"]),
        match_count=int(data["match_count"]),
        possible_match_count=int(data["possible_match_count"]),
        relationship_count=int(data["relationship_count"]),
        captured_at=str(data["captured_at"]),
    )


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare(baseline: ERStatistics, current: ERStatistics) -> ComparisonResult:
    """Compute deltas between baseline and current statistics.

    Args:
        baseline: The reference statistics to compare against.
        current: The latest statistics after a mapping change.

    Returns:
        A ComparisonResult with per-metric deltas and quality assessment.
    """
    entity_delta = current.entity_count - baseline.entity_count
    record_delta = current.record_count - baseline.record_count
    match_delta = current.match_count - baseline.match_count
    possible_match_delta = current.possible_match_count - baseline.possible_match_count
    relationship_delta = current.relationship_count - baseline.relationship_count

    result = ComparisonResult(
        entity_delta=entity_delta,
        record_delta=record_delta,
        match_delta=match_delta,
        possible_match_delta=possible_match_delta,
        relationship_delta=relationship_delta,
        quality_assessment="unchanged",
    )
    result.quality_assessment = assess_quality(result)

    return result


def assess_quality(result: ComparisonResult) -> str:
    """Determine net quality change from comparison deltas.

    Uses a simple heuristic based on match_delta and entity_delta:
    - Improved: match_count increased OR entity_count decreased (more dedup),
      with no decrease in match_count.
    - Degraded: match_count decreased OR entity_count increased (less dedup),
      with no increase in match_count.
    - Unchanged: No meaningful change in match_count or entity_count.

    Args:
        result: A ComparisonResult containing the computed deltas.

    Returns:
        One of "improved", "degraded", or "unchanged".
    """
    match_delta = result.match_delta
    entity_delta = result.entity_delta

    # Improved: more matches found OR more deduplication, with no regression in matches
    if (match_delta > 0 or entity_delta < 0) and match_delta >= 0:
        return "improved"

    # Degraded: fewer matches OR less deduplication, with no improvement in matches
    if (match_delta < 0 or entity_delta > 0) and match_delta <= 0:
        return "degraded"

    return "unchanged"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _format_delta(value: int) -> str:
    """Format an integer delta with +/- prefix.

    Args:
        value: The delta value to format.

    Returns:
        String with '+' prefix for positive, '-' for negative, '0' for zero.
    """
    if value > 0:
        return f"+{value}"
    if value < 0:
        return str(value)
    return "0"


def format_report(result: ComparisonResult) -> str:
    """Format a ComparisonResult as human-readable text.

    Args:
        result: The comparison result containing deltas and quality assessment.

    Returns:
        A multi-line string showing each metric delta and quality assessment.
    """
    lines = [
        "=== ER Comparison Report ===",
        f"  Entities:         {_format_delta(result.entity_delta)}",
        f"  Records:          {_format_delta(result.record_delta)}",
        f"  Matches:          {_format_delta(result.match_delta)}",
        f"  Possible Matches: {_format_delta(result.possible_match_delta)}",
        f"  Relationships:    {_format_delta(result.relationship_delta)}",
        "",
        f"  Quality: {result.quality_assessment}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Baseline Management
# ---------------------------------------------------------------------------


def baseline_path(datasource: str) -> Path:
    """Construct the canonical baseline file path for a datasource.

    Args:
        datasource: The datasource name (case-insensitive).

    Returns:
        Path to the baseline file: config/er_baseline_{datasource_lower}.json
    """
    return Path(f"config/er_baseline_{datasource.lower()}.json")


def accept_baseline(current_path: str | Path, datasource: str) -> None:
    """Copy current stats file to become the new baseline.

    Args:
        current_path: Path to the current statistics file to promote.
        datasource: The datasource name used to determine the baseline path.

    Raises:
        SystemExit: If the source file is missing or a permission error occurs.
    """
    source = Path(current_path)

    if not source.exists():
        print(
            f"Error: Current statistics file not found: {source}",
            file=sys.stderr,
        )
        sys.exit(1)

    destination = baseline_path(datasource)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"Error: Cannot create baseline directory: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        shutil.copy2(source, destination)
    except PermissionError as exc:
        print(
            f"Error: Cannot write baseline file: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except OSError as exc:
        print(
            f"Error: Cannot write baseline file: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for compare_results.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None).
    """
    parser = argparse.ArgumentParser(
        description="Compare baseline and current ER statistics."
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to the baseline statistics JSON file.",
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Path to the current statistics JSON file.",
    )
    args = parser.parse_args(argv)

    baseline_file = Path(args.baseline)

    if not baseline_file.exists():
        # No baseline yet — save current as the new baseline
        current_stats = load_statistics(args.current)
        print(
            "No baseline found. Saving current stats as baseline."
        )
        accept_baseline(args.current, current_stats.datasource)
        return

    # Both files exist — load, compare, and report
    baseline_stats = load_statistics(args.baseline)
    current_stats = load_statistics(args.current)
    result = compare(baseline_stats, current_stats)
    report = format_report(result)
    print(report)


if __name__ == "__main__":
    main()
