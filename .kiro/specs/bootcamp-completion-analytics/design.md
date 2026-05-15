# Design: Bootcamp Completion Analytics

## Overview

A new `scripts/bootcamp_analytics.py` script that reads `config/session_log.jsonl` and produces a structured analytics report identifying friction points, time distribution, skip patterns, and optionally compares against performance baselines. The script complements the existing `analyze_sessions.py` (which provides per-module turn/correction summaries) by adding higher-level curriculum insights: friction detection, skip tracking, MCP failure correlation, and baseline comparison.

## Architecture

### Data Flow

```text
config/session_log.jsonl ──┐
config/bootcamp_progress.json ──┤──▶ bootcamp_analytics.py ──▶ stdout (text or JSON)
docs/guides/PERFORMANCE_BASELINES.md ──┘
```

### Module Structure

```text
bootcamp_analytics.py
├── Data Models (dataclasses)
│   ├── ModuleMetrics — per-module aggregated stats
│   ├── FrictionPoint — identified curriculum weak spot
│   ├── SkipRecord — a skipped step with reason
│   └── AnalyticsReport — full report container
├── Parsing
│   ├── parse_session_log(path) → list[dict]
│   ├── parse_skipped_steps(progress_path) → list[SkipRecord]
│   └── parse_baselines(baselines_path) → dict[int, float]
├── Analysis
│   ├── compute_module_metrics(entries) → list[ModuleMetrics]
│   ├── detect_friction_points(metrics, skips) → list[FrictionPoint]
│   └── compare_to_baselines(metrics, baselines) → list[str]
├── Formatting
│   ├── format_text_report(report) → str
│   └── format_json_report(report) → str
└── CLI
    └── main(argv) → int
```

## Data Models

### ModuleMetrics

```python
@dataclass
class ModuleMetrics:
    module: int
    total_seconds: float
    turn_count: int
    correction_count: int
    error_count: int          # events with "error" in message
    mcp_failure_count: int    # events with "mcp" + "fail" in message
    first_entry_ts: str       # ISO 8601
    last_entry_ts: str        # ISO 8601
```

### FrictionPoint

```python
@dataclass
class FrictionPoint:
    module: int
    step: str | int | None
    category: str             # "slow", "high_corrections", "skipped", "mcp_failures"
    description: str
    severity: str             # "high", "medium", "low"
```

### SkipRecord

```python
@dataclass
class SkipRecord:
    module_step: str          # e.g. "5.3"
    reason: str               # "a", "b", or "c"
    note: str
    skipped_at: str           # ISO 8601
```

### AnalyticsReport

```python
@dataclass
class AnalyticsReport:
    module_metrics: list[ModuleMetrics]
    friction_points: list[FrictionPoint]
    skipped_steps: list[SkipRecord]
    total_time_seconds: float
    total_turns: int
    total_corrections: int
    baseline_comparison: list[str] | None  # None if --compare not used
```

## Analysis Logic

### Friction Point Detection

A module is flagged as a friction point when any of these conditions hold:

| Condition | Category | Severity |
|-----------|----------|----------|
| Time > 2× median module time | `slow` | high |
| Time > 1.5× median module time | `slow` | medium |
| Correction density > 0.3 | `high_corrections` | high |
| Correction density > 0.2 | `high_corrections` | medium |
| Has skipped steps | `skipped` | medium |
| MCP failure count > 2 | `mcp_failures` | medium |

Median is computed across all modules with at least one entry. Modules with fewer than 3 entries are excluded from friction detection (insufficient data).

### MCP Failure Detection

Scan log entry `message` fields for patterns indicating MCP failures:
- Contains "mcp" (case-insensitive) AND ("fail", "error", "unreachable", "timeout")

### Skip Detection

Read `config/bootcamp_progress.json` → `skipped_steps` object (written by skip-step-protocol). Each key is `"<module>.<step>"` with value containing `reason`, `note`, `skipped_at`.

### Baseline Comparison (--compare)

Parse `docs/guides/PERFORMANCE_BASELINES.md` to extract estimated wall-clock times per tier. Since the bootcamp uses small datasets (<1K records), use the "Small" tier loading time as the reference for Module 6. For other modules, use a simple heuristic: expected time = turns × 30 seconds (average turn duration). Compare actual time against this estimate and report modules that took >2× expected as "slower than baseline" and <0.5× as "faster than baseline".

## Output Formats

### Text Format (default)

```text
═══════════════════════════════════════════
  Senzing Bootcamp Analytics
═══════════════════════════════════════════

Time Distribution
─────────────────
  Module 1: Business Problem ........  5.2 min (12 turns)
  Module 2: SDK Setup ...............  8.1 min (18 turns)
  Module 5: Data Quality & Mapping .. 22.4 min (45 turns) ⚠ SLOW
  ─────────────────────────────────────────
  Total: 35.7 min across 3 modules

Friction Points
───────────────
  ⚠ Module 5 — SLOW: took 2.3× the median module time (high)
  ⚠ Module 5 — HIGH CORRECTIONS: 35% of turns were corrections (high)

Skipped Steps
─────────────
  • Step 5.3 — skipped (reason: stuck, "couldn't get mapping to work")

MCP Tool Failures
─────────────────
  Module 5: 3 failures

No session data available.
```

### JSON Format (--json)

```json
{
  "module_metrics": [...],
  "friction_points": [...],
  "skipped_steps": [...],
  "total_time_seconds": 2142.0,
  "total_turns": 75,
  "total_corrections": 12,
  "baseline_comparison": null
}
```

## CLI Interface

```text
usage: bootcamp_analytics.py [-h] [--json] [--compare] [--log PATH] [--progress PATH]

Analyze bootcamp session data to identify friction points and curriculum insights.

options:
  -h, --help       show this help message and exit
  --json           Output in JSON format instead of human-readable text
  --compare        Compare pace against performance baselines
  --log PATH       Path to session log (default: config/session_log.jsonl)
  --progress PATH  Path to progress file (default: config/bootcamp_progress.json)
```

Exit codes:
- 0: success (including "no data available")
- 1: file read error or invalid arguments

## Integration Points

### module-completion.md

Add after the export-results offer in Path Completion Celebration:

```markdown
- Analytics offer (after the export offer, before the graduation offer):
  "📊 Would you like to see analytics on your bootcamp journey? I can show you time distribution, friction points, and how your pace compares to baselines."
  When accepted, run `python3 scripts/bootcamp_analytics.py` and present the output conversationally.
```

### POWER.md

Add to "Useful Commands" section:

```text
python3 senzing-bootcamp/scripts/bootcamp_analytics.py    # Session analytics
python3 senzing-bootcamp/scripts/bootcamp_analytics.py --compare  # With baseline comparison
```

## Relationship to Existing Scripts

| Script | Purpose | Overlap |
|--------|---------|---------|
| `analyze_sessions.py` | Per-module turn/correction summary, confusion ranking, pacing classification | Shares log parsing; analytics adds friction detection, skip tracking, baseline comparison |
| `session_logger.py` | Writes log entries | Producer of the data this script consumes |
| `status.py` | Current state snapshot | Point-in-time; analytics is historical |

The new script reuses the same JSONL format and log path but provides a different analytical lens. It does NOT import from `analyze_sessions.py` — it has its own parser to avoid coupling.

## Correctness Properties

1. **Empty log produces zero-data report**: When `session_log.jsonl` is missing or empty, the script exits 0 and prints "No session data available."
2. **Friction detection is deterministic**: Given the same log entries, the same friction points are always identified.
3. **Skip records match progress file**: Every entry in `skipped_steps` from the progress file appears in the report's skipped_steps list.
4. **JSON output is valid JSON**: The `--json` output always parses as valid JSON.
5. **Baseline comparison is advisory**: The `--compare` flag never changes exit code — it only adds informational lines.
6. **No external network calls**: The script reads only local files and writes only to stdout.

## Constraints

- Python stdlib only (no third-party dependencies)
- Must work on Linux, macOS, and Windows
- Must handle malformed log lines gracefully (skip and continue)
- Must not import from other bootcamp scripts (self-contained)
