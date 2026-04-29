"""Example-based unit tests for session-analytics feature."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from session_logger import (
    VALID_EVENTS,
    LogEntry,
    build_log_entry,
    serialize_entry,
    append_entry,
)
from analyze_sessions import (
    parse_log,
    compute_summary,
    format_text,
    format_json,
    pretty_print_entries,
    main as analyze_main,
)


# ---------------------------------------------------------------------------
# 9.1 build_log_entry with valid inputs
# ---------------------------------------------------------------------------

class TestBuildLogEntryValid:
    """9.1 Unit test: build_log_entry with valid inputs returns a LogEntry with correct field values."""

    def test_returns_log_entry_with_correct_fields(self):
        entry = build_log_entry(
            session_id="abc-123",
            module=5,
            step=3,
            event="turn",
            duration_seconds=42.5,
            message="Explained SDK init",
        )
        assert isinstance(entry, LogEntry)
        assert entry.session_id == "abc-123"
        assert entry.module == 5
        assert entry.step == 3
        assert entry.event == "turn"
        assert entry.duration_seconds == 42.5
        assert entry.message == "Explained SDK init"
        # timestamp should be a non-empty ISO 8601 string
        assert len(entry.timestamp) > 0
        from datetime import datetime
        datetime.fromisoformat(entry.timestamp)

    def test_string_step_accepted(self):
        entry = build_log_entry("s1", 1, "3a", "module_start", 0, "start")
        assert entry.step == "3a"

    def test_zero_duration_accepted(self):
        entry = build_log_entry("s1", 1, 1, "turn", 0, "first")
        assert entry.duration_seconds == 0.0

    def test_integer_duration_converted_to_float(self):
        entry = build_log_entry("s1", 1, 1, "turn", 10, "msg")
        assert isinstance(entry.duration_seconds, float)
        assert entry.duration_seconds == 10.0


# ---------------------------------------------------------------------------
# 9.2 build_log_entry raises ValueError for invalid inputs
# ---------------------------------------------------------------------------

class TestBuildLogEntryInvalid:
    """9.2 Unit test: build_log_entry raises ValueError for invalid inputs."""

    def test_module_0_raises(self):
        with pytest.raises(ValueError, match="module"):
            build_log_entry("s1", 0, 1, "turn", 0, "msg")

    def test_module_12_raises(self):
        with pytest.raises(ValueError, match="module"):
            build_log_entry("s1", 12, 1, "turn", 0, "msg")

    def test_invalid_event_raises(self):
        with pytest.raises(ValueError, match="event"):
            build_log_entry("s1", 1, 1, "invalid_event", 0, "msg")

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="duration_seconds"):
            build_log_entry("s1", 1, 1, "turn", -1.0, "msg")

    def test_empty_session_id_raises(self):
        with pytest.raises(ValueError, match="session_id"):
            build_log_entry("", 1, 1, "turn", 0, "msg")


# ---------------------------------------------------------------------------
# 9.3 append_entry creates missing directories and file
# ---------------------------------------------------------------------------

class TestAppendEntryCreatesFile:
    """9.3 Unit test: append_entry creates missing directories and file on first write (Req 1.2)."""

    def test_creates_file_and_dirs(self, tmp_path):
        log_path = tmp_path / "deep" / "nested" / "session.jsonl"
        assert not log_path.exists()

        entry = build_log_entry("s1", 1, 1, "turn", 0, "first entry")
        append_entry(str(log_path), entry)

        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["session_id"] == "s1"


# ---------------------------------------------------------------------------
# 9.4 append_entry handles write errors gracefully
# ---------------------------------------------------------------------------

class TestAppendEntryErrorHandling:
    """9.4 Unit test: append_entry prints warning to stderr on file-system error (Req 1.4)."""

    def test_prints_warning_on_error(self, tmp_path):
        # Create a directory where the file should be — can't open a dir as a file
        bad_path = tmp_path / "blocked"
        bad_path.mkdir()

        entry = build_log_entry("s1", 1, 1, "turn", 0, "msg")

        # Should not raise
        import io
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            append_entry(str(bad_path), entry)
        finally:
            sys.stderr = old_stderr

        warning = captured.getvalue()
        assert "WARNING" in warning


# ---------------------------------------------------------------------------
# 9.5 parse_log uses default path
# ---------------------------------------------------------------------------

class TestParseLogDefaultPath:
    """9.5 Unit test: parse_log uses default path config/session_log.jsonl (Req 3.3)."""

    def test_default_path_returns_empty_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = parse_log("config/session_log.jsonl")
        assert result.entries == []
        assert result.error_count == 0


# ---------------------------------------------------------------------------
# 9.6 compute_summary with empty entries
# ---------------------------------------------------------------------------

class TestComputeSummaryEmpty:
    """9.6 Unit test: compute_summary with empty entries returns report indicating no data (Req 4.5)."""

    def test_empty_entries(self):
        report = compute_summary([])
        assert report.modules == []
        assert report.overall_turns == 0
        assert report.overall_corrections == 0
        assert report.overall_seconds == 0.0
        assert report.confusion_ranking == []

    def test_format_text_empty_says_no_data(self):
        report = compute_summary([])
        text = format_text(report)
        assert "No session data available" in text


# ---------------------------------------------------------------------------
# 9.7 format_text produces readable table
# ---------------------------------------------------------------------------

class TestFormatText:
    """9.7 Unit test: format_text produces output with column headers and aligned data (Req 6.1)."""

    def test_has_column_headers(self):
        entries = [
            {"module": 1, "event": "turn", "duration_seconds": 10.0},
            {"module": 1, "event": "correction", "duration_seconds": 5.0},
            {"module": 2, "event": "turn", "duration_seconds": 20.0},
        ]
        report = compute_summary(entries)
        text = format_text(report)

        assert "Module" in text
        assert "Turns" in text
        assert "Corrections" in text
        assert "Overall" in text
        assert "Confusion Ranking" in text


# ---------------------------------------------------------------------------
# 9.8 default format is text
# ---------------------------------------------------------------------------

class TestDefaultFormatIsText:
    """9.8 Unit test: default format is text when no --format flag provided (Req 6.3)."""

    def test_default_text_output(self, tmp_path):
        log_file = tmp_path / "test.jsonl"
        entry = {"module": 1, "event": "turn", "duration_seconds": 5.0}
        log_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        import io
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            analyze_main([str(log_file)])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        # Text format has "Module" header, not JSON braces
        assert "Module" in output
        # Should not be JSON
        try:
            json.loads(output)
            assert False, "Output should not be valid JSON in text mode"
        except json.JSONDecodeError:
            pass


# ---------------------------------------------------------------------------
# 9.9 --output writes to file
# ---------------------------------------------------------------------------

class TestOutputFlag:
    """9.9 Unit test: --output flag writes to specified file instead of stdout (Req 6.4)."""

    def test_output_to_file(self, tmp_path):
        log_file = tmp_path / "test.jsonl"
        entry = {"module": 1, "event": "turn", "duration_seconds": 5.0}
        log_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        out_file = tmp_path / "report.txt"
        analyze_main([str(log_file), "--output", str(out_file)])

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Module" in content


# ---------------------------------------------------------------------------
# 9.10 --pretty --module 5 filters correctly
# ---------------------------------------------------------------------------

class TestPrettyModuleFilter:
    """9.10 Unit test: --pretty --module 5 outputs only module 5 entries (Req 7.2)."""

    def test_pretty_module_filter(self, tmp_path):
        log_file = tmp_path / "test.jsonl"
        entries = [
            {"module": 3, "event": "turn", "duration_seconds": 5.0, "message": "mod3"},
            {"module": 5, "event": "turn", "duration_seconds": 10.0, "message": "mod5a"},
            {"module": 5, "event": "correction", "duration_seconds": 3.0, "message": "mod5b"},
            {"module": 7, "event": "turn", "duration_seconds": 8.0, "message": "mod7"},
        ]
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries) + "\n",
            encoding="utf-8",
        )

        import io
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            analyze_main([str(log_file), "--pretty", "--module", "5"])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        # Parse the pretty-printed blocks
        blocks = [b.strip() for b in output.strip().split("\n\n") if b.strip()]
        assert len(blocks) == 2
        for block in blocks:
            parsed = json.loads(block)
            assert parsed["module"] == 5
