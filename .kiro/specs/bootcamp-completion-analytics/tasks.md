# Implementation Plan: Bootcamp Completion Analytics

## Overview

Create `scripts/bootcamp_analytics.py` — a local-only analytics tool that reads session logs and progress data to identify friction points, time distribution, skip patterns, and optionally compares against performance baselines.

## Tasks

- [x] 1. Create data models and log parser
  - [x] 1.1 Create `senzing-bootcamp/scripts/bootcamp_analytics.py` with shebang, module docstring, `from __future__ import annotations`, and stdlib imports (json, argparse, sys, dataclasses, pathlib, re, collections)
  - [x] 1.2 Define `ModuleMetrics` dataclass with fields: module (int), total_seconds (float), turn_count (int), correction_count (int), error_count (int), mcp_failure_count (int), first_entry_ts (str), last_entry_ts (str)
  - [x] 1.3 Define `FrictionPoint` dataclass with fields: module (int), step (str | int | None), category (str), description (str), severity (str)
  - [x] 1.4 Define `SkipRecord` dataclass with fields: module_step (str), reason (str), note (str), skipped_at (str)
  - [x] 1.5 Define `AnalyticsReport` dataclass with fields: module_metrics (list[ModuleMetrics]), friction_points (list[FrictionPoint]), skipped_steps (list[SkipRecord]), total_time_seconds (float), total_turns (int), total_corrections (int), baseline_comparison (list[str] | None)
  - [x] 1.6 Implement `parse_session_log(path: str) -> list[dict]` that reads JSONL, skips malformed lines, returns empty list if file missing
    - _Requirements: 1, 5, 11_

- [x] 2. Implement skip and baseline parsers
  - [x] 2.1 Implement `parse_skipped_steps(progress_path: str) -> list[SkipRecord]` that reads `skipped_steps` from bootcamp_progress.json, returns empty list if file missing or key absent
  - [x] 2.2 Implement `parse_baselines(baselines_path: str) -> dict[int, float]` that extracts estimated wall-clock times from PERFORMANCE_BASELINES.md using regex to find the "Small" tier loading time for Module 6 and a heuristic (turns × 30s) for other modules; returns empty dict if file missing
    - _Requirements: 7, 11_

- [x] 3. Implement analysis functions
  - [x] 3.1 Implement `compute_module_metrics(entries: list[dict]) -> list[ModuleMetrics]` that aggregates log entries by module, counting turns, corrections, errors (message contains "error"), MCP failures (message contains "mcp" + failure indicator), and summing duration_seconds
  - [x] 3.2 Implement `detect_friction_points(metrics: list[ModuleMetrics], skips: list[SkipRecord]) -> list[FrictionPoint]` using the thresholds from the design: time > 2× median (high), > 1.5× median (medium), correction density > 0.3 (high), > 0.2 (medium), has skipped steps (medium), MCP failures > 2 (medium). Exclude modules with < 3 entries.
  - [x] 3.3 Implement `compare_to_baselines(metrics: list[ModuleMetrics], baselines: dict[int, float]) -> list[str]` that returns human-readable comparison strings for modules that took >2× or <0.5× expected time
    - _Requirements: 2, 3, 7_

- [x] 4. Implement output formatters
  - [x] 4.1 Implement `format_text_report(report: AnalyticsReport) -> str` that produces the human-readable text format with sections: Time Distribution, Friction Points, Skipped Steps, MCP Tool Failures, and optionally Baseline Comparison. Use box-drawing characters for headers. Show "No session data available." when module_metrics is empty.
  - [x] 4.2 Implement `format_json_report(report: AnalyticsReport) -> str` that serializes the AnalyticsReport to a valid JSON string with 2-space indent, converting dataclass instances to dicts
    - _Requirements: 2, 3, 4, 5_

- [x] 5. Implement CLI entry point
  - [x] 5.1 Implement `main(argv: list[str] | None = None) -> int` with argparse supporting `--json`, `--compare`, `--log PATH` (default: config/session_log.jsonl), `--progress PATH` (default: config/bootcamp_progress.json). Orchestrate: parse log → parse skips → compute metrics → detect friction → optionally compare baselines → format → print → exit 0
  - [x] 5.2 Add `if __name__ == "__main__": sys.exit(main())` entry point
    - _Requirements: 1, 4, 5, 6, 11_

- [x] 6. Update POWER.md and module-completion.md
  - [x] 6.1 Add `bootcamp_analytics.py` to the "Useful Commands" section of `senzing-bootcamp/POWER.md` with usage examples for default view and `--compare`
  - [x] 6.2 Add analytics offer to `senzing-bootcamp/steering/module-completion.md` in the Path Completion Celebration section, after the export-results offer and before the graduation offer: "📊 Would you like to see analytics on your bootcamp journey?"
    - _Requirements: 8, 9_

- [x] 7. Write unit tests
  - [x] 7.1 Create `senzing-bootcamp/tests/test_bootcamp_analytics.py` with sys.path setup importing from scripts directory
  - [x] 7.2 Add `TestParseSessionLog` class: test missing file returns empty list, test empty file returns empty list, test valid JSONL returns correct dicts, test malformed lines are skipped
  - [x] 7.3 Add `TestParseSkippedSteps` class: test missing file returns empty list, test missing key returns empty list, test valid skipped_steps returns correct SkipRecords
  - [x] 7.4 Add `TestComputeModuleMetrics` class: test empty entries returns empty list, test single module aggregation, test multi-module aggregation with correct counts for turns/corrections/errors/mcp_failures
  - [x] 7.5 Add `TestDetectFrictionPoints` class: test no friction when all modules similar time, test slow module detected at 2× median, test high corrections detected at >0.3 density, test skipped steps produce friction point, test modules with <3 entries excluded
  - [x] 7.6 Add `TestCompareToBaselines` class: test returns empty when no baselines, test flags modules >2× expected, test flags modules <0.5× expected
  - [x] 7.7 Add `TestFormatTextReport` class: test empty report shows "No session data available.", test non-empty report contains expected section headers
  - [x] 7.8 Add `TestFormatJsonReport` class: test output is valid JSON, test all fields present, test empty report produces valid JSON
  - [x] 7.9 Add `TestMain` class: test exit 0 with missing log, test exit 0 with valid log, test --json flag produces JSON output, test --compare flag adds baseline section
    - _Requirements: 10_

- [x] 8. Write property-based tests
  - [x] 8.1 Create `senzing-bootcamp/tests/test_bootcamp_analytics_properties.py` with Hypothesis strategies: `st_log_entry()` generating valid session log dicts, `st_log_entries()` generating lists of entries, `st_skip_record()` generating valid SkipRecord instances
  - [x] 8.2 Property 1: `compute_module_metrics` total turns equals input entry count (per module)
  - [x] 8.3 Property 2: `detect_friction_points` returns only valid categories ("slow", "high_corrections", "skipped", "mcp_failures") and severities ("high", "medium", "low")
  - [x] 8.4 Property 3: `format_json_report` always produces valid JSON for any AnalyticsReport
  - [x] 8.5 Property 4: `parse_session_log` never raises on arbitrary file content (graceful degradation)
    - _Requirements: 10_

- [x] 9. Run tests and validate
  - [x] 9.1 Run `python3 -m pytest senzing-bootcamp/tests/test_bootcamp_analytics.py -v` and verify all unit tests pass
  - [x] 9.2 Run `python3 -m pytest senzing-bootcamp/tests/test_bootcamp_analytics_properties.py -v` and verify all property tests pass
  - [x] 9.3 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify any modified markdown files pass
  - [x] 9.4 Run `python3 senzing-bootcamp/scripts/bootcamp_analytics.py` with no log file to verify graceful "No session data available." output and exit 0

## Notes

- The script is self-contained — it does NOT import from `analyze_sessions.py` or any other bootcamp script to avoid coupling
- Uses the same JSONL format written by `session_logger.py` (fields: timestamp, session_id, module, step, event, duration_seconds, message)
- The `--compare` flag reads PERFORMANCE_BASELINES.md as a text file and extracts numbers via regex — it does not require the file to exist
- All analysis is local-only; no data leaves the machine (Requirement 6)
- Friction detection thresholds are hardcoded but documented in the design for future tuning
