#!/usr/bin/env python3
"""Senzing Bootcamp - Completion Analytics.

Reads session logs (``config/session_log.jsonl``) and progress data to
produce an analytics summary identifying friction points, time distribution,
skip patterns, and optionally compares against performance baselines.

Helps identify curriculum weak spots without sending data externally.

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ModuleMetrics:
    """Aggregated metrics for a single bootcamp module.

    Attributes:
        module: Module number (1-based).
        total_seconds: Total wall-clock time spent in the module.
        turn_count: Number of conversational turns in the module.
        correction_count: Number of turns that were corrections.
        error_count: Number of log entries containing an error indicator.
        mcp_failure_count: Number of MCP tool failure events.
        first_entry_ts: ISO 8601 timestamp of the first log entry.
        last_entry_ts: ISO 8601 timestamp of the last log entry.
    """

    module: int
    total_seconds: float
    turn_count: int
    correction_count: int
    error_count: int
    mcp_failure_count: int
    first_entry_ts: str
    last_entry_ts: str


@dataclass
class FrictionPoint:
    """An identified curriculum weak spot within a bootcamp module.

    Attributes:
        module: Module number where friction was detected.
        step: Step identifier within the module, or None if module-level.
        category: Type of friction detected. One of "slow",
            "high_corrections", "skipped", or "mcp_failures".
        description: Human-readable explanation of the friction point.
        severity: Impact level — "high", "medium", or "low".
    """

    module: int
    step: str | int | None
    category: str
    description: str
    severity: str


@dataclass
class SkipRecord:
    """A record of a skipped bootcamp step.

    Attributes:
        module_step: Step identifier in "module.step" format (e.g. "5.3").
        reason: Skip reason code — "a", "b", or "c".
        note: User-provided note explaining why the step was skipped.
        skipped_at: ISO 8601 timestamp of when the step was skipped.
    """

    module_step: str
    reason: str
    note: str
    skipped_at: str


@dataclass
class AnalyticsReport:
    """Top-level report container holding all bootcamp analytics data.

    Attributes:
        module_metrics: Per-module aggregated statistics.
        friction_points: Identified curriculum weak spots.
        skipped_steps: Steps the bootcamper chose to skip.
        total_time_seconds: Total wall-clock time across all modules.
        total_turns: Total conversational turns across all modules.
        total_corrections: Total correction turns across all modules.
        baseline_comparison: Human-readable comparison strings against
            performance baselines, or None when --compare is not used.
    """

    module_metrics: list[ModuleMetrics]
    friction_points: list[FrictionPoint]
    skipped_steps: list[SkipRecord]
    total_time_seconds: float
    total_turns: int
    total_corrections: int
    baseline_comparison: list[str] | None


def parse_session_log(path: str) -> list[dict]:
    """Read a JSONL session log file and return parsed entries.

    Each line in the file is expected to be a valid JSON object with fields:
    timestamp, session_id, module, step, event, duration_seconds, message.

    Malformed lines (lines that fail JSON parsing) are silently skipped.

    Args:
        path: Path to the JSONL session log file.

    Returns:
        A list of dicts, one per valid log entry. Returns an empty list if
        the file does not exist or is empty.
    """
    log_path = Path(path)
    if not log_path.exists():
        return []

    entries: list[dict] = []
    with log_path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue

    return entries


def parse_skipped_steps(progress_path: str) -> list[SkipRecord]:
    """Read skipped steps from a bootcamp progress JSON file.

    Parses the ``skipped_steps`` key from the progress file. Each key in
    that object is expected to be ``"<module>.<step>"`` with a value dict
    containing ``reason``, ``note``, and ``skipped_at`` fields.

    Args:
        progress_path: Path to the bootcamp_progress.json file.

    Returns:
        A list of SkipRecord instances. Returns an empty list if the file
        does not exist, the JSON is malformed, or the ``skipped_steps``
        key is absent.
    """
    file_path = Path(progress_path)
    if not file_path.exists():
        return []

    try:
        with file_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, ValueError, OSError):
        return []

    if not isinstance(data, dict):
        return []

    skipped = data.get("skipped_steps")
    if not isinstance(skipped, dict):
        return []

    records: list[SkipRecord] = []
    for module_step, info in skipped.items():
        if not isinstance(info, dict):
            continue
        records.append(
            SkipRecord(
                module_step=str(module_step),
                reason=str(info.get("reason", "")),
                note=str(info.get("note", "")),
                skipped_at=str(info.get("skipped_at", "")),
            )
        )

    return records


def parse_baselines(baselines_path: str) -> dict[int, float]:
    """Extract estimated wall-clock times per module from PERFORMANCE_BASELINES.md.

    For Module 6 (loading): extracts the "Small" tier SQLite loading time
    from the markdown table using regex, taking the upper bound of the range.
    For other modules: uses a heuristic of expected_turns × 30 seconds
    (average turn duration), assuming ~12 turns per module.

    Args:
        baselines_path: Path to the PERFORMANCE_BASELINES.md file.

    Returns:
        A dict mapping module number to expected seconds. Returns an empty
        dict if the file does not exist or cannot be read.
    """
    file_path = Path(baselines_path)
    if not file_path.exists():
        return {}

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    baselines: dict[int, float] = {}

    # Extract Module 6 (loading) baseline from SQLite Loading table.
    # Look for the Small tier row: | Small | <1K | ... | 3 - 10 seconds |
    sqlite_loading_pattern = re.compile(
        r"\|\s*Small\s*\|[^|]*\|[^|]*\|\s*(\d+)\s*-\s*(\d+)\s*seconds\s*\|",
    )
    # Find the match in the SQLite Loading section specifically.
    # The file has multiple "Small" rows; the SQLite Loading section comes
    # after the "### SQLite Loading" heading.
    sqlite_section_match = re.search(
        r"###\s*SQLite Loading.*?(?=###|\Z)", content, re.DOTALL
    )
    if sqlite_section_match:
        section_text = sqlite_section_match.group(0)
        row_match = sqlite_loading_pattern.search(section_text)
        if row_match:
            upper_bound = float(row_match.group(2))
            baselines[6] = upper_bound

    # For other modules (1-11, excluding 6), use heuristic:
    # expected_turns × 30 seconds per turn.
    # Assume ~12 turns per module as a reasonable default.
    default_turns_per_module = 12
    seconds_per_turn = 30.0
    for module_num in range(1, 12):
        if module_num not in baselines:
            baselines[module_num] = default_turns_per_module * seconds_per_turn

    return baselines


def compute_module_metrics(entries: list[dict]) -> list[ModuleMetrics]:
    """Aggregate log entries by module into per-module metrics.

    Groups entries by their ``module`` field and computes summary statistics
    for each module: total turns, corrections, errors, MCP failures, total
    duration, and first/last timestamps.

    Args:
        entries: A list of dicts representing parsed JSONL log entries.
            Each entry is expected to have fields: timestamp, session_id,
            module, step, event, duration_seconds, message.

    Returns:
        A list of ModuleMetrics sorted by module number. Returns an empty
        list if entries is empty.
    """
    if not entries:
        return []

    # Group entries by module number.
    grouped: dict[int, list[dict]] = collections.defaultdict(list)
    for entry in entries:
        module = entry.get("module")
        if module is None:
            continue
        try:
            module_num = int(module)
        except (TypeError, ValueError):
            continue
        grouped[module_num].append(entry)

    if not grouped:
        return []

    # MCP failure indicators (case-insensitive).
    _MCP_FAILURE_INDICATORS = ("fail", "error", "unreachable", "timeout")

    metrics: list[ModuleMetrics] = []
    for module_num in sorted(grouped):
        module_entries = grouped[module_num]
        turn_count = len(module_entries)
        correction_count = 0
        error_count = 0
        mcp_failure_count = 0
        total_seconds = 0.0
        timestamps: list[str] = []

        for entry in module_entries:
            # Count corrections.
            event = str(entry.get("event", "")).lower()
            if event == "correction":
                correction_count += 1

            # Count errors (message contains "error", case-insensitive).
            message = str(entry.get("message", "")).lower()
            if "error" in message:
                error_count += 1

            # Count MCP failures (message contains "mcp" AND a failure indicator).
            if "mcp" in message and any(
                ind in message for ind in _MCP_FAILURE_INDICATORS
            ):
                mcp_failure_count += 1

            # Sum duration.
            duration = entry.get("duration_seconds", 0)
            try:
                total_seconds += float(duration)
            except (TypeError, ValueError):
                pass

            # Collect timestamps for first/last determination.
            ts = entry.get("timestamp", "")
            if ts:
                timestamps.append(str(ts))

        # Determine first and last timestamps (chronological sort).
        first_ts = ""
        last_ts = ""
        if timestamps:
            sorted_ts = sorted(timestamps)
            first_ts = sorted_ts[0]
            last_ts = sorted_ts[-1]

        metrics.append(
            ModuleMetrics(
                module=module_num,
                total_seconds=total_seconds,
                turn_count=turn_count,
                correction_count=correction_count,
                error_count=error_count,
                mcp_failure_count=mcp_failure_count,
                first_entry_ts=first_ts,
                last_entry_ts=last_ts,
            )
        )

    return metrics


def detect_friction_points(
    metrics: list[ModuleMetrics], skips: list[SkipRecord]
) -> list[FrictionPoint]:
    """Identify curriculum friction points from module metrics and skip records.

    Applies threshold-based detection to flag modules where learners
    experienced difficulty. Modules with fewer than 3 entries (turn_count < 3)
    are excluded from analysis due to insufficient data.

    Thresholds:
        - Time > 2× median module time → category "slow", severity "high"
        - Time > 1.5× median module time → category "slow", severity "medium"
        - Correction density > 0.3 → category "high_corrections", severity "high"
        - Correction density > 0.2 → category "high_corrections", severity "medium"
        - Has skipped steps → category "skipped", severity "medium"
        - MCP failure count > 2 → category "mcp_failures", severity "medium"

    Args:
        metrics: Per-module aggregated statistics from compute_module_metrics.
        skips: Skipped step records from parse_skipped_steps.

    Returns:
        A list of FrictionPoint instances describing detected friction.
        Returns an empty list if no friction is detected or if there are
        no modules with sufficient data.
    """
    if not metrics:
        return []

    # Compute median time across all modules with at least one entry.
    times = sorted(m.total_seconds for m in metrics if m.turn_count >= 1)
    if not times:
        return []

    # Median calculation.
    n = len(times)
    if n % 2 == 1:
        median_time = times[n // 2]
    else:
        median_time = (times[n // 2 - 1] + times[n // 2]) / 2.0

    # Build a lookup of skipped modules: module_number -> list of module_steps.
    skipped_by_module: dict[int, list[str]] = collections.defaultdict(list)
    for skip in skips:
        # module_step is e.g. "5.3"; module number is the part before the dot.
        parts = skip.module_step.split(".")
        if parts:
            try:
                mod_num = int(parts[0])
                skipped_by_module[mod_num].append(skip.module_step)
            except (ValueError, TypeError):
                continue

    friction_points: list[FrictionPoint] = []

    for m in metrics:
        # Exclude modules with fewer than 3 entries.
        if m.turn_count < 3:
            continue

        # Check time-based friction (higher severity first).
        if median_time > 0:
            time_ratio = m.total_seconds / median_time
            if time_ratio > 2.0:
                friction_points.append(
                    FrictionPoint(
                        module=m.module,
                        step=None,
                        category="slow",
                        description=f"took {time_ratio:.1f}\u00d7 the median module time",
                        severity="high",
                    )
                )
            elif time_ratio > 1.5:
                friction_points.append(
                    FrictionPoint(
                        module=m.module,
                        step=None,
                        category="slow",
                        description=f"took {time_ratio:.1f}\u00d7 the median module time",
                        severity="medium",
                    )
                )

        # Check correction density.
        if m.turn_count > 0:
            density = m.correction_count / m.turn_count
            if density > 0.3:
                friction_points.append(
                    FrictionPoint(
                        module=m.module,
                        step=None,
                        category="high_corrections",
                        description=(
                            f"{density * 100:.0f}% of turns were corrections"
                        ),
                        severity="high",
                    )
                )
            elif density > 0.2:
                friction_points.append(
                    FrictionPoint(
                        module=m.module,
                        step=None,
                        category="high_corrections",
                        description=(
                            f"{density * 100:.0f}% of turns were corrections"
                        ),
                        severity="medium",
                    )
                )

        # Check skipped steps.
        if m.module in skipped_by_module:
            skipped_steps = skipped_by_module[m.module]
            step_list = ", ".join(skipped_steps)
            friction_points.append(
                FrictionPoint(
                    module=m.module,
                    step=None,
                    category="skipped",
                    description=f"has skipped steps: {step_list}",
                    severity="medium",
                )
            )

        # Check MCP failures.
        if m.mcp_failure_count > 2:
            friction_points.append(
                FrictionPoint(
                    module=m.module,
                    step=None,
                    category="mcp_failures",
                    description=(
                        f"{m.mcp_failure_count} MCP tool failures detected"
                    ),
                    severity="medium",
                )
            )

    return friction_points


def compare_to_baselines(
    metrics: list[ModuleMetrics], baselines: dict[int, float]
) -> list[str]:
    """Compare actual module times against expected baselines.

    For each module that has a corresponding baseline entry, computes the
    ratio of actual time to expected time. Modules that took more than 2×
    the expected time are flagged as "slower than baseline". Modules that
    took less than 0.5× the expected time are flagged as "faster than
    baseline". Modules within the normal range are not included.

    Args:
        metrics: Per-module aggregated statistics from compute_module_metrics.
        baselines: A dict mapping module number to expected seconds.

    Returns:
        A list of human-readable comparison strings. Returns an empty list
        if baselines is empty or no modules exceed the thresholds.
    """
    if not baselines:
        return []

    comparisons: list[str] = []

    for m in metrics:
        expected = baselines.get(m.module)
        if expected is None or expected <= 0:
            continue

        ratio = m.total_seconds / expected

        if ratio > 2.0:
            comparisons.append(
                f"Module {m.module}: {ratio:.1f}\u00d7 slower than baseline"
                f" (expected {expected:.0f}s, actual {m.total_seconds:.0f}s)"
            )
        elif ratio < 0.5:
            comparisons.append(
                f"Module {m.module}: {ratio:.1f}\u00d7 faster than baseline"
                f" (expected {expected:.0f}s, actual {m.total_seconds:.0f}s)"
            )

    return comparisons


def format_text_report(report: AnalyticsReport) -> str:
    """Format an analytics report as human-readable text with box-drawing characters.

    Produces a structured text report with sections for Time Distribution,
    Friction Points, Skipped Steps, MCP Tool Failures, and optionally
    Baseline Comparison. Uses box-drawing characters (═ for main header,
    ─ for section headers) for visual structure.

    Args:
        report: An AnalyticsReport dataclass instance containing all
            analytics data to format.

    Returns:
        A formatted multi-line string. Returns "No session data available.\\n"
        when module_metrics is empty.
    """
    if not report.module_metrics:
        return "No session data available.\n"

    lines: list[str] = []

    # Main header with box-drawing characters.
    header_bar = "\u2550" * 43
    lines.append(header_bar)
    lines.append("  Senzing Bootcamp Analytics")
    lines.append(header_bar)
    lines.append("")

    # --- Time Distribution section ---
    lines.append("Time Distribution")
    lines.append("\u2500" * 17)

    # Determine which modules are slow for the ⚠ SLOW marker.
    times = sorted(m.total_seconds for m in report.module_metrics if m.turn_count >= 1)
    if times:
        n = len(times)
        if n % 2 == 1:
            median_time = times[n // 2]
        else:
            median_time = (times[n // 2 - 1] + times[n // 2]) / 2.0
    else:
        median_time = 0.0

    slow_modules: set[int] = set()
    for m in report.module_metrics:
        if median_time > 0 and m.total_seconds > 1.5 * median_time:
            slow_modules.add(m.module)

    for m in report.module_metrics:
        minutes = m.total_seconds / 60.0
        label = f"  Module {m.module}"
        time_str = f"{minutes:.1f} min ({m.turn_count} turns)"
        # Pad with dots between label and time.
        # Target a consistent alignment width.
        dot_fill_width = 40 - len(label)
        if dot_fill_width < 3:
            dot_fill_width = 3
        dots = " " + "." * (dot_fill_width - 1)
        entry_line = f"{label}{dots}  {time_str}"
        if m.module in slow_modules:
            entry_line += " \u26a0 SLOW"
        lines.append(entry_line)

    # Total line with separator.
    lines.append("  " + "\u2500" * 41)
    total_minutes = report.total_time_seconds / 60.0
    module_count = len(report.module_metrics)
    lines.append(f"  Total: {total_minutes:.1f} min across {module_count} modules")
    lines.append("")

    # --- Friction Points section ---
    lines.append("Friction Points")
    lines.append("\u2500" * 15)
    if report.friction_points:
        for fp in report.friction_points:
            category_label = fp.category.upper().replace("_", " ")
            lines.append(
                f"  \u26a0 Module {fp.module} \u2014 {category_label}: "
                f"{fp.description} ({fp.severity})"
            )
    else:
        lines.append("  None detected.")
    lines.append("")

    # --- Skipped Steps section ---
    lines.append("Skipped Steps")
    lines.append("\u2500" * 13)
    if report.skipped_steps:
        for skip in report.skipped_steps:
            reason_label = skip.reason if skip.reason else "unknown"
            note_part = f', "{skip.note}"' if skip.note else ""
            lines.append(
                f"  \u2022 Step {skip.module_step} \u2014 skipped "
                f"(reason: {reason_label}{note_part})"
            )
    else:
        lines.append("  None.")
    lines.append("")

    # --- MCP Tool Failures section ---
    lines.append("MCP Tool Failures")
    lines.append("\u2500" * 17)
    mcp_modules = [m for m in report.module_metrics if m.mcp_failure_count > 0]
    if mcp_modules:
        for m in mcp_modules:
            lines.append(
                f"  Module {m.module}: {m.mcp_failure_count} "
                f"failure{'s' if m.mcp_failure_count != 1 else ''}"
            )
    else:
        lines.append("  None.")
    lines.append("")

    # --- Baseline Comparison section (optional) ---
    if report.baseline_comparison is not None and report.baseline_comparison:
        lines.append("Baseline Comparison")
        lines.append("\u2500" * 19)
        for comparison in report.baseline_comparison:
            lines.append(f"  {comparison}")
        lines.append("")

    return "\n".join(lines) + "\n"


def format_json_report(report: AnalyticsReport) -> str:
    """Serialize an AnalyticsReport to a JSON string with 2-space indent.

    Converts the entire report dataclass hierarchy (including nested
    ModuleMetrics, FrictionPoint, and SkipRecord instances) to plain
    dicts using ``dataclasses.asdict()``, then serializes to JSON.

    Args:
        report: An AnalyticsReport dataclass instance containing all
            analytics data to serialize.

    Returns:
        A valid JSON string with 2-space indentation.
    """
    return json.dumps(asdict(report), indent=2)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for bootcamp analytics.

    Parses command-line arguments, reads session log and progress data,
    computes analytics metrics, detects friction points, optionally
    compares against performance baselines, and prints a formatted report
    to stdout.

    Args:
        argv: Command-line arguments to parse. Defaults to ``sys.argv[1:]``
            when None.

    Returns:
        Exit code 0 on success (always returns 0 — graceful handling of
        missing or empty data is done via the report formatters).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Analyze bootcamp session data to identify friction points"
            " and curriculum insights."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format instead of human-readable text",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare pace against performance baselines",
    )
    parser.add_argument(
        "--log",
        metavar="PATH",
        default="config/session_log.jsonl",
        help="Path to session log (default: config/session_log.jsonl)",
    )
    parser.add_argument(
        "--progress",
        metavar="PATH",
        default="config/bootcamp_progress.json",
        help="Path to progress file (default: config/bootcamp_progress.json)",
    )

    args = parser.parse_args(argv)

    # 1. Parse session log.
    entries = parse_session_log(args.log)

    # 2. Parse skipped steps.
    skips = parse_skipped_steps(args.progress)

    # 3. Compute module metrics.
    metrics = compute_module_metrics(entries)

    # 4. Detect friction points.
    friction_points = detect_friction_points(metrics, skips)

    # 5. Optionally compare against baselines.
    baseline_comparison: list[str] | None = None
    if args.compare:
        baselines = parse_baselines("docs/guides/PERFORMANCE_BASELINES.md")
        baseline_comparison = compare_to_baselines(metrics, baselines)

    # 6. Build the report.
    report = AnalyticsReport(
        module_metrics=metrics,
        friction_points=friction_points,
        skipped_steps=skips,
        total_time_seconds=sum(m.total_seconds for m in metrics),
        total_turns=sum(m.turn_count for m in metrics),
        total_corrections=sum(m.correction_count for m in metrics),
        baseline_comparison=baseline_comparison,
    )

    # 7. Format output.
    if args.json:
        output = format_json_report(report)
    else:
        output = format_text_report(report)

    # 8. Print to stdout.
    print(output, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
