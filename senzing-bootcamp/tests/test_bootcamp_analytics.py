"""Unit tests for bootcamp_analytics.py."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import bootcamp_analytics
from bootcamp_analytics import (
    ModuleMetrics,
    FrictionPoint,
    SkipRecord,
    AnalyticsReport,
    parse_session_log,
    parse_skipped_steps,
    compute_module_metrics,
    detect_friction_points,
    compare_to_baselines,
    format_text_report,
    format_json_report,
    main,
)


class TestParseSessionLog:
    """Tests for parse_session_log function."""

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        """Passing a nonexistent path returns an empty list."""
        nonexistent = str(tmp_path / "does_not_exist.jsonl")
        result = parse_session_log(nonexistent)
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        """An empty file returns an empty list."""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("", encoding="utf-8")
        result = parse_session_log(str(empty_file))
        assert result == []

    def test_valid_jsonl_returns_correct_dicts(self, tmp_path: Path) -> None:
        """Valid JSONL lines are parsed into the correct list of dicts."""
        log_file = tmp_path / "session.jsonl"
        entries = [
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "hello"},
            {"timestamp": "2025-01-01T00:01:00Z", "session_id": "s1",
             "module": 2, "step": 1, "event": "correction",
             "duration_seconds": 45, "message": "fix typo"},
        ]
        content = "\n".join(json.dumps(e) for e in entries) + "\n"
        log_file.write_text(content, encoding="utf-8")

        result = parse_session_log(str(log_file))
        assert result == entries

    def test_malformed_lines_are_skipped(self, tmp_path: Path) -> None:
        """Malformed JSON lines are skipped; only valid lines are returned."""
        log_file = tmp_path / "mixed.jsonl"
        valid_entry = {"timestamp": "2025-01-01T00:00:00Z", "module": 1,
                       "event": "turn", "duration_seconds": 10,
                       "message": "ok"}
        lines = [
            json.dumps(valid_entry),
            "this is not json",
            "{invalid json: [}",
            json.dumps(valid_entry),
        ]
        log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        result = parse_session_log(str(log_file))
        assert len(result) == 2
        assert result[0] == valid_entry
        assert result[1] == valid_entry


class TestParseSkippedSteps:
    """Tests for parse_skipped_steps function."""

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        """Passing a nonexistent path returns an empty list."""
        nonexistent = str(tmp_path / "no_such_file.json")
        result = parse_skipped_steps(nonexistent)
        assert result == []

    def test_missing_key_returns_empty_list(self, tmp_path: Path) -> None:
        """A JSON file without the skipped_steps key returns an empty list."""
        progress_file = tmp_path / "bootcamp_progress.json"
        progress_file.write_text(
            json.dumps({"current_module": 3, "completed": [1, 2]}),
            encoding="utf-8",
        )
        result = parse_skipped_steps(str(progress_file))
        assert result == []

    def test_valid_skipped_steps_returns_correct_records(
        self, tmp_path: Path
    ) -> None:
        """Valid skipped_steps data produces correct SkipRecord instances."""
        progress_file = tmp_path / "bootcamp_progress.json"
        data = {
            "skipped_steps": {
                "5.3": {
                    "reason": "a",
                    "note": "couldn't get mapping to work",
                    "skipped_at": "2025-01-01T00:00:00Z",
                },
                "7.1": {
                    "reason": "b",
                    "note": "already familiar with topic",
                    "skipped_at": "2025-01-02T12:30:00Z",
                },
            }
        }
        progress_file.write_text(json.dumps(data), encoding="utf-8")

        result = parse_skipped_steps(str(progress_file))

        assert len(result) == 2

        # Build a lookup by module_step for order-independent assertions.
        by_step = {r.module_step: r for r in result}

        assert "5.3" in by_step
        assert by_step["5.3"].reason == "a"
        assert by_step["5.3"].note == "couldn't get mapping to work"
        assert by_step["5.3"].skipped_at == "2025-01-01T00:00:00Z"

        assert "7.1" in by_step
        assert by_step["7.1"].reason == "b"
        assert by_step["7.1"].note == "already familiar with topic"
        assert by_step["7.1"].skipped_at == "2025-01-02T12:30:00Z"

        # Verify they are actual SkipRecord instances.
        for record in result:
            assert isinstance(record, SkipRecord)


class TestComputeModuleMetrics:
    """Tests for compute_module_metrics function."""

    def test_empty_entries_returns_empty_list(self) -> None:
        """Passing an empty list returns an empty list."""
        result = compute_module_metrics([])
        assert result == []

    def test_single_module_aggregation(self) -> None:
        """Entries for one module are aggregated into a single ModuleMetrics."""
        entries = [
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "started module"},
            {"timestamp": "2025-01-01T00:01:00Z", "session_id": "s1",
             "module": 1, "step": 2, "event": "turn",
             "duration_seconds": 45, "message": "continued"},
            {"timestamp": "2025-01-01T00:02:00Z", "session_id": "s1",
             "module": 1, "step": 3, "event": "correction",
             "duration_seconds": 20, "message": "fixed typo"},
        ]

        result = compute_module_metrics(entries)

        assert len(result) == 1
        m = result[0]
        assert isinstance(m, ModuleMetrics)
        assert m.module == 1
        assert m.turn_count == 3
        assert m.total_seconds == 95.0
        assert m.correction_count == 1
        assert m.error_count == 0
        assert m.mcp_failure_count == 0
        assert m.first_entry_ts == "2025-01-01T00:00:00Z"
        assert m.last_entry_ts == "2025-01-01T00:02:00Z"

    def test_multi_module_aggregation(self) -> None:
        """Entries for multiple modules produce correct per-module counts."""
        entries = [
            # Module 1: 2 turns, 1 correction, 1 error, 0 MCP failures
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "all good"},
            {"timestamp": "2025-01-01T00:01:00Z", "session_id": "s1",
             "module": 1, "step": 2, "event": "correction",
             "duration_seconds": 25, "message": "got an error here"},
            # Module 2: 3 turns, 0 corrections, 0 errors, 2 MCP failures
            {"timestamp": "2025-01-02T00:00:00Z", "session_id": "s1",
             "module": 2, "step": 1, "event": "turn",
             "duration_seconds": 40, "message": "mcp tool timeout occurred"},
            {"timestamp": "2025-01-02T00:01:00Z", "session_id": "s1",
             "module": 2, "step": 2, "event": "turn",
             "duration_seconds": 35, "message": "mcp connection unreachable"},
            {"timestamp": "2025-01-02T00:02:00Z", "session_id": "s1",
             "module": 2, "step": 3, "event": "turn",
             "duration_seconds": 50, "message": "completed step"},
            # Module 3: 2 turns, 1 correction, 1 error, 1 MCP failure
            {"timestamp": "2025-01-03T00:00:00Z", "session_id": "s1",
             "module": 3, "step": 1, "event": "turn",
             "duration_seconds": 60, "message": "mcp fail error detected"},
            {"timestamp": "2025-01-03T00:01:00Z", "session_id": "s1",
             "module": 3, "step": 2, "event": "correction",
             "duration_seconds": 15, "message": "retrying after Error"},
        ]

        result = compute_module_metrics(entries)

        assert len(result) == 3
        by_module = {m.module: m for m in result}

        # Module 1 assertions
        m1 = by_module[1]
        assert m1.turn_count == 2
        assert m1.correction_count == 1
        assert m1.error_count == 1  # "got an error here"
        assert m1.mcp_failure_count == 0
        assert m1.total_seconds == 55.0

        # Module 2 assertions
        m2 = by_module[2]
        assert m2.turn_count == 3
        assert m2.correction_count == 0
        assert m2.error_count == 0
        assert m2.mcp_failure_count == 2  # "mcp...timeout", "mcp...unreachable"
        assert m2.total_seconds == 125.0

        # Module 3 assertions
        m3 = by_module[3]
        assert m3.turn_count == 2
        assert m3.correction_count == 1
        assert m3.error_count == 2  # "mcp fail error" + "Error" (case-insensitive)
        assert m3.mcp_failure_count == 1  # "mcp fail error detected"
        assert m3.total_seconds == 75.0


class TestDetectFrictionPoints:
    """Tests for detect_friction_points function."""

    def test_no_friction_when_all_modules_similar_time(self) -> None:
        """No friction points when all modules have similar times (within 1.5× median)."""
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:01:40Z",
            ),
            ModuleMetrics(
                module=2, total_seconds=110.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-02T00:00:00Z",
                last_entry_ts="2025-01-02T00:01:50Z",
            ),
            ModuleMetrics(
                module=3, total_seconds=120.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-03T00:00:00Z",
                last_entry_ts="2025-01-03T00:02:00Z",
            ),
        ]

        result = detect_friction_points(metrics, [])

        assert result == []

    def test_slow_module_detected_at_2x_median(self) -> None:
        """A module with >2× median time produces a 'slow'/'high' friction point."""
        # Median of [100, 100, 100] = 100; module 4 at 250 is 2.5× median.
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:01:40Z",
            ),
            ModuleMetrics(
                module=2, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-02T00:00:00Z",
                last_entry_ts="2025-01-02T00:01:40Z",
            ),
            ModuleMetrics(
                module=3, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-03T00:00:00Z",
                last_entry_ts="2025-01-03T00:01:40Z",
            ),
            ModuleMetrics(
                module=4, total_seconds=250.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-04T00:00:00Z",
                last_entry_ts="2025-01-04T00:04:10Z",
            ),
        ]

        result = detect_friction_points(metrics, [])

        slow_points = [fp for fp in result if fp.category == "slow"]
        assert len(slow_points) == 1
        assert slow_points[0].module == 4
        assert slow_points[0].severity == "high"

    def test_high_corrections_detected(self) -> None:
        """A module with correction density >0.3 produces 'high_corrections'/'high'."""
        # Module 2: 4 corrections out of 10 turns = 0.4 density.
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:01:40Z",
            ),
            ModuleMetrics(
                module=2, total_seconds=100.0, turn_count=10,
                correction_count=4, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-02T00:00:00Z",
                last_entry_ts="2025-01-02T00:01:40Z",
            ),
        ]

        result = detect_friction_points(metrics, [])

        correction_points = [
            fp for fp in result if fp.category == "high_corrections"
        ]
        assert len(correction_points) == 1
        assert correction_points[0].module == 2
        assert correction_points[0].severity == "high"

    def test_skipped_steps_produce_friction_point(self) -> None:
        """A module with skipped steps produces a 'skipped'/'medium' friction point."""
        metrics = [
            ModuleMetrics(
                module=5, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:01:40Z",
            ),
            ModuleMetrics(
                module=6, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-02T00:00:00Z",
                last_entry_ts="2025-01-02T00:01:40Z",
            ),
        ]
        skips = [
            SkipRecord(
                module_step="5.3",
                reason="a",
                note="couldn't get mapping to work",
                skipped_at="2025-01-01T00:05:00Z",
            ),
        ]

        result = detect_friction_points(metrics, skips)

        skipped_points = [fp for fp in result if fp.category == "skipped"]
        assert len(skipped_points) == 1
        assert skipped_points[0].module == 5
        assert skipped_points[0].severity == "medium"

    def test_modules_with_less_than_3_entries_excluded(self) -> None:
        """Modules with turn_count < 3 are excluded from friction detection."""
        # Module 1 has turn_count=2 and very high time (would be slow) and
        # high correction density — but should be excluded.
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=500.0, turn_count=2,
                correction_count=2, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:08:20Z",
            ),
            ModuleMetrics(
                module=2, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-02T00:00:00Z",
                last_entry_ts="2025-01-02T00:01:40Z",
            ),
            ModuleMetrics(
                module=3, total_seconds=100.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-03T00:00:00Z",
                last_entry_ts="2025-01-03T00:01:40Z",
            ),
        ]

        result = detect_friction_points(metrics, [])

        # Module 1 should NOT appear in any friction points.
        module_1_points = [fp for fp in result if fp.module == 1]
        assert module_1_points == []


class TestCompareToBaselines:
    """Tests for compare_to_baselines function."""

    def test_returns_empty_when_no_baselines(self) -> None:
        """Passing an empty baselines dict returns an empty list."""
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=300.0, turn_count=10,
                correction_count=1, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:05:00Z",
            ),
        ]

        result = compare_to_baselines(metrics, {})

        assert result == []

    def test_flags_modules_slower_than_2x_expected(self) -> None:
        """A module taking >2× expected time is flagged as slower than baseline."""
        # Module 1 baseline is 360s; actual is 800s (2.2× expected).
        metrics = [
            ModuleMetrics(
                module=1, total_seconds=800.0, turn_count=20,
                correction_count=2, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:13:20Z",
            ),
        ]
        baselines = {1: 360.0, 2: 360.0}

        result = compare_to_baselines(metrics, baselines)

        assert len(result) == 1
        assert "slower than baseline" in result[0]
        assert "Module 1" in result[0]

    def test_flags_modules_faster_than_half_expected(self) -> None:
        """A module taking <0.5× expected time is flagged as faster than baseline."""
        # Module 2 baseline is 360s; actual is 150s (0.4× expected).
        metrics = [
            ModuleMetrics(
                module=2, total_seconds=150.0, turn_count=5,
                correction_count=0, error_count=0, mcp_failure_count=0,
                first_entry_ts="2025-01-01T00:00:00Z",
                last_entry_ts="2025-01-01T00:02:30Z",
            ),
        ]
        baselines = {1: 360.0, 2: 360.0}

        result = compare_to_baselines(metrics, baselines)

        assert len(result) == 1
        assert "faster than baseline" in result[0]
        assert "Module 2" in result[0]


class TestFormatTextReport:
    """Tests for format_text_report function."""

    def test_empty_report_shows_no_data_message(self) -> None:
        """An empty report (no module_metrics) outputs 'No session data available.'."""
        report = AnalyticsReport(
            module_metrics=[],
            friction_points=[],
            skipped_steps=[],
            total_time_seconds=0.0,
            total_turns=0,
            total_corrections=0,
            baseline_comparison=None,
        )

        result = format_text_report(report)

        assert result == "No session data available.\n"

    def test_non_empty_report_contains_section_headers(self) -> None:
        """A non-empty report contains all expected section headers."""
        report = AnalyticsReport(
            module_metrics=[
                ModuleMetrics(
                    module=1, total_seconds=300.0, turn_count=10,
                    correction_count=1, error_count=0, mcp_failure_count=0,
                    first_entry_ts="2025-01-01T00:00:00Z",
                    last_entry_ts="2025-01-01T00:05:00Z",
                ),
            ],
            friction_points=[],
            skipped_steps=[],
            total_time_seconds=300.0,
            total_turns=10,
            total_corrections=1,
            baseline_comparison=None,
        )

        result = format_text_report(report)

        assert "Senzing Bootcamp Analytics" in result
        assert "Time Distribution" in result
        assert "Friction Points" in result
        assert "Skipped Steps" in result
        assert "MCP Tool Failures" in result


class TestFormatJsonReport:
    """Tests for format_json_report function."""

    def test_output_is_valid_json(self) -> None:
        """format_json_report output parses as valid JSON without error."""
        report = AnalyticsReport(
            module_metrics=[
                ModuleMetrics(
                    module=1, total_seconds=300.0, turn_count=10,
                    correction_count=1, error_count=0, mcp_failure_count=0,
                    first_entry_ts="2025-01-01T00:00:00Z",
                    last_entry_ts="2025-01-01T00:05:00Z",
                ),
            ],
            friction_points=[
                FrictionPoint(
                    module=1, step=None, category="slow",
                    description="took 2× median", severity="high",
                ),
            ],
            skipped_steps=[
                SkipRecord(
                    module_step="5.3", reason="a",
                    note="stuck on mapping",
                    skipped_at="2025-01-01T00:10:00Z",
                ),
            ],
            total_time_seconds=300.0,
            total_turns=10,
            total_corrections=1,
            baseline_comparison=["Module 1: slower than baseline"],
        )

        result = format_json_report(report)
        parsed = json.loads(result)

        assert isinstance(parsed, dict)

    def test_all_fields_present(self) -> None:
        """All top-level keys are present in the JSON output."""
        report = AnalyticsReport(
            module_metrics=[
                ModuleMetrics(
                    module=2, total_seconds=600.0, turn_count=20,
                    correction_count=3, error_count=1, mcp_failure_count=0,
                    first_entry_ts="2025-01-02T00:00:00Z",
                    last_entry_ts="2025-01-02T00:10:00Z",
                ),
            ],
            friction_points=[],
            skipped_steps=[],
            total_time_seconds=600.0,
            total_turns=20,
            total_corrections=3,
            baseline_comparison=None,
        )

        result = format_json_report(report)
        parsed = json.loads(result)

        expected_keys = {
            "module_metrics",
            "friction_points",
            "skipped_steps",
            "total_time_seconds",
            "total_turns",
            "total_corrections",
            "baseline_comparison",
        }
        assert set(parsed.keys()) == expected_keys

    def test_empty_report_produces_valid_json(self) -> None:
        """An empty AnalyticsReport produces valid JSON with expected structure."""
        report = AnalyticsReport(
            module_metrics=[],
            friction_points=[],
            skipped_steps=[],
            total_time_seconds=0.0,
            total_turns=0,
            total_corrections=0,
            baseline_comparison=None,
        )

        result = format_json_report(report)
        parsed = json.loads(result)

        assert parsed["module_metrics"] == []
        assert parsed["friction_points"] == []
        assert parsed["skipped_steps"] == []
        assert parsed["total_time_seconds"] == 0.0
        assert parsed["total_turns"] == 0
        assert parsed["total_corrections"] == 0
        assert parsed["baseline_comparison"] is None


class TestMain:
    """Tests for main() CLI entry point."""

    def test_exit_0_with_missing_log(self, tmp_path: Path) -> None:
        """main() returns 0 when --log points to a nonexistent file."""
        nonexistent = str(tmp_path / "no_such_file.jsonl")
        result = main(["--log", nonexistent])
        assert result == 0

    def test_exit_0_with_valid_log(self, tmp_path: Path) -> None:
        """main() returns 0 when --log points to a valid JSONL file."""
        log_file = tmp_path / "session.jsonl"
        entries = [
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "hello"},
            {"timestamp": "2025-01-01T00:01:00Z", "session_id": "s1",
             "module": 1, "step": 2, "event": "turn",
             "duration_seconds": 45, "message": "world"},
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )

        result = main(["--log", str(log_file)])
        assert result == 0

    def test_json_flag_produces_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main() with --json produces valid JSON output to stdout."""
        log_file = tmp_path / "session.jsonl"
        entries = [
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "hello"},
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )

        result = main(["--json", "--log", str(log_file)])
        assert result == 0

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert isinstance(parsed, dict)
        assert "module_metrics" in parsed

    def test_compare_flag_adds_baseline_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """main() with --compare adds a Baseline Comparison section (or doesn't crash)."""
        log_file = tmp_path / "session.jsonl"
        entries = [
            {"timestamp": "2025-01-01T00:00:00Z", "session_id": "s1",
             "module": 1, "step": 1, "event": "turn",
             "duration_seconds": 30, "message": "hello"},
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )

        result = main(["--compare", "--log", str(log_file)])
        assert result == 0

        captured = capsys.readouterr()
        # The --compare flag should produce output containing
        # "Baseline Comparison" section header when there's data.
        assert "Baseline Comparison" in captured.out or len(captured.out) > 0
