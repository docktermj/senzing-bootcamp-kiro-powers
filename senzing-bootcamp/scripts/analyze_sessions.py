#!/usr/bin/env python3
"""Senzing Bootcamp - Session Analytics.

Reads the session log (``config/session_log.jsonl``) and produces
per-module summary reports, confusion rankings, or pretty-printed
log entries.

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

LOG_PATH_DEFAULT: str = "config/session_log.jsonl"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    """Result of parsing a JSONL session log file."""

    entries: list[dict]
    error_count: int


@dataclass
class ModuleSummary:
    """Per-module aggregated statistics."""

    module: int
    turns: int
    corrections: int
    total_seconds: float


@dataclass
class SummaryReport:
    """Full summary report with per-module stats and confusion ranking."""

    modules: list[ModuleSummary]
    overall_turns: int
    overall_corrections: int
    overall_seconds: float
    confusion_ranking: list[tuple[int, float]]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_log(file_path: str) -> ParseResult:
    """Parse a JSONL session log file.

    Each line is parsed as an independent JSON object.
    Invalid lines are skipped and counted in *error_count*.
    If the file does not exist, returns empty entries with error_count 0.

    Returns:
        ``ParseResult`` with parsed entries and error count.
    """
    p = Path(file_path)
    if not p.is_file():
        return ParseResult(entries=[], error_count=0)

    entries: list[dict] = []
    error_count = 0

    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entries.append(json.loads(stripped))
            except (json.JSONDecodeError, ValueError):
                error_count += 1

    return ParseResult(entries=entries, error_count=error_count)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def compute_summary(entries: list[dict]) -> SummaryReport:
    """Compute per-module statistics and confusion ranking.

    For each module present in *entries*:
      - Count all events as turns
      - Count corrections (events == ``'correction'``)
      - Sum ``duration_seconds``

    Confusion ranking: modules sorted by correction density
    (corrections / turns) descending.  Modules with zero turns are
    excluded.  Density is rounded to two decimal places.

    Returns:
        ``SummaryReport`` with modules in ascending order and overall
        totals.
    """
    if not entries:
        return SummaryReport(
            modules=[],
            overall_turns=0,
            overall_corrections=0,
            overall_seconds=0.0,
            confusion_ranking=[],
        )

    turns_by_mod: dict[int, int] = defaultdict(int)
    corrections_by_mod: dict[int, int] = defaultdict(int)
    seconds_by_mod: dict[int, float] = defaultdict(float)

    for entry in entries:
        mod = entry.get("module")
        if mod is None:
            continue
        turns_by_mod[mod] += 1
        if entry.get("event") == "correction":
            corrections_by_mod[mod] += 1
        seconds_by_mod[mod] += float(entry.get("duration_seconds", 0))

    module_summaries: list[ModuleSummary] = []
    for mod in sorted(turns_by_mod):
        module_summaries.append(
            ModuleSummary(
                module=mod,
                turns=turns_by_mod[mod],
                corrections=corrections_by_mod[mod],
                total_seconds=seconds_by_mod[mod],
            )
        )

    overall_turns = sum(ms.turns for ms in module_summaries)
    overall_corrections = sum(ms.corrections for ms in module_summaries)
    overall_seconds = sum(ms.total_seconds for ms in module_summaries)

    # Confusion ranking — descending by correction density
    ranking: list[tuple[int, float]] = []
    for ms in module_summaries:
        if ms.turns > 0:
            density = round(ms.corrections / ms.turns, 2)
            ranking.append((ms.module, density))
    ranking.sort(key=lambda t: (-t[1], t[0]))

    return SummaryReport(
        modules=module_summaries,
        overall_turns=overall_turns,
        overall_corrections=overall_corrections,
        overall_seconds=overall_seconds,
        confusion_ranking=ranking,
    )


# ---------------------------------------------------------------------------
# Pacing Classification
# ---------------------------------------------------------------------------


def classify_pacing(entries: list[dict]) -> dict[int, str]:
    """Classify completed modules into pacing categories based on session analytics.

    Categories:
      - "struggled": correction_density > 0.3 OR time > 2× median
      - "comfortable": correction_density < 0.1 AND time < median
      - "normal": everything else

    Args:
        entries: List of session log entry dicts.

    Returns:
        Dict mapping module number to pacing category string.
        Empty dict if no entries or no modules with turns.
    """
    if not entries:
        return {}

    # Compute per-module metrics
    turns_by_mod: dict[int, int] = defaultdict(int)
    corrections_by_mod: dict[int, int] = defaultdict(int)
    seconds_by_mod: dict[int, float] = defaultdict(float)

    for entry in entries:
        mod = entry.get("module")
        if mod is None:
            continue
        turns_by_mod[mod] += 1
        if entry.get("event") == "correction":
            corrections_by_mod[mod] += 1
        seconds_by_mod[mod] += float(entry.get("duration_seconds", 0))

    # Filter to modules with non-zero turns
    active_modules = [m for m in turns_by_mod if turns_by_mod[m] > 0]
    if not active_modules:
        return {}

    # Compute median time (need at least 2 modules for meaningful comparison)
    times = sorted(seconds_by_mod[m] for m in active_modules)
    if len(times) < 2:
        # Single module — can't compute median comparison, return "normal"
        return {active_modules[0]: "normal"}

    median_time = times[len(times) // 2]

    # Classify each module
    result: dict[int, str] = {}
    for mod in active_modules:
        turns = turns_by_mod[mod]
        corrections = corrections_by_mod[mod]
        total_seconds = seconds_by_mod[mod]
        density = corrections / turns if turns > 0 else 0.0

        if density > 0.3 or total_seconds > 2 * median_time:
            result[mod] = "struggled"
        elif density < 0.1 and total_seconds < median_time:
            result[mod] = "comfortable"
        else:
            result[mod] = "normal"

    return result


def merge_with_overrides(
    computed: dict[int, str], overrides: dict[int, str]
) -> dict[int, str]:
    """Merge computed pacing classifications with manual overrides.

    Manual overrides take precedence over computed values.

    Args:
        computed: Dict from classify_pacing().
        overrides: Dict from bootcamp_preferences.yaml pacing_overrides.

    Returns:
        Merged dict with overrides applied.
    """
    merged = dict(computed)
    for mod, category in overrides.items():
        if category in ("struggled", "comfortable", "normal"):
            merged[mod] = category
    return merged


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_text(report: SummaryReport) -> str:
    """Format the summary report as a human-readable plain-text table."""
    lines: list[str] = []

    if not report.modules:
        lines.append("No session data available.")
        return "\n".join(lines)

    # Header
    header = f"{'Module':>8}  {'Turns':>6}  {'Corrections':>12}  {'Total Seconds':>14}"
    lines.append(header)
    lines.append("-" * len(header))

    for ms in report.modules:
        lines.append(
            f"{ms.module:>8}  {ms.turns:>6}  {ms.corrections:>12}  {ms.total_seconds:>14.1f}"
        )

    lines.append("-" * len(header))
    lines.append(
        f"{'Overall':>8}  {report.overall_turns:>6}  "
        f"{report.overall_corrections:>12}  {report.overall_seconds:>14.1f}"
    )

    # Confusion ranking
    lines.append("")
    lines.append("Confusion Ranking (correction density, descending):")
    rank_header = f"{'Module':>8}  {'Density':>8}"
    lines.append(rank_header)
    lines.append("-" * len(rank_header))
    for mod, density in report.confusion_ranking:
        lines.append(f"{mod:>8}  {density:>8.2f}")

    return "\n".join(lines)


def format_json(report: SummaryReport) -> str:
    """Format the summary report as a single valid JSON object."""
    obj: dict = {
        "modules": [
            {
                "module": ms.module,
                "turns": ms.turns,
                "corrections": ms.corrections,
                "total_seconds": ms.total_seconds,
            }
            for ms in report.modules
        ],
        "overall": {
            "turns": report.overall_turns,
            "corrections": report.overall_corrections,
            "total_seconds": report.overall_seconds,
        },
        "confusion_ranking": [
            {"module": mod, "correction_density": density}
            for mod, density in report.confusion_ranking
        ],
    }
    return json.dumps(obj, indent=2)


def pretty_print_entries(
    entries: list[dict],
    module_filter: int | None = None,
) -> str:
    """Pretty-print log entries as indented JSON (2-space indent).

    Each entry is separated by a blank line.
    If *module_filter* is provided, only entries whose ``module`` field
    equals the filter value are included.
    """
    filtered = entries
    if module_filter is not None:
        filtered = [e for e in entries if e.get("module") == module_filter]

    blocks: list[str] = []
    for entry in filtered:
        blocks.append(json.dumps(entry, indent=2))

    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Arguments:
        [file_path]         Session log path (default: config/session_log.jsonl)
        --format text|json  Output format (default: text)
        --output PATH       Write to file instead of stdout
        --pretty            Pretty-print individual log entries
        --module N          Filter by module number (with --pretty)
    """
    parser = argparse.ArgumentParser(
        description="Analyse Senzing Bootcamp session logs.",
        epilog="See Also: status.py (current state), session_logger.py (log entry library)",
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        default=LOG_PATH_DEFAULT,
        help="Path to the session log JSONL file (default: %(default)s)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write output to this file instead of stdout",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print individual log entries",
    )
    parser.add_argument(
        "--module",
        type=int,
        default=None,
        help="Filter by module number (used with --pretty)",
    )

    args = parser.parse_args(argv)

    result = parse_log(args.file_path)

    if args.pretty:
        output = pretty_print_entries(result.entries, module_filter=args.module)
    else:
        report = compute_summary(result.entries)
        if args.fmt == "json":
            output = format_json(report)
        else:
            output = format_text(report)

    # Write output
    if args.output:
        try:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"Error: could not write to {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
