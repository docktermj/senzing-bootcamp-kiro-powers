"""Integration tests for session-analytics feature.

End-to-end tests that write entries via session_logger and then
analyse them with analyze_sessions.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from session_logger import build_log_entry, append_entry
from analyze_sessions import parse_log, compute_summary, format_json, main as analyze_main


# ---------------------------------------------------------------------------
# 10.1 End-to-end: write 10 entries then analyse
# ---------------------------------------------------------------------------

class TestEndToEndWriteThenAnalyze:
    """10.1 Integration test: write 10 entries via session_logger then run
    analyze_sessions, verify summary matches expected aggregation."""

    def test_write_10_entries_then_summarize(self, tmp_path):
        log_path = str(tmp_path / "session_log.jsonl")

        # Write 10 entries across modules 1, 2, 3
        specs = [
            ("s1", 1, 1, "module_start", 0.0, "Start module 1"),
            ("s1", 1, 1, "turn", 10.0, "Step 1 of module 1"),
            ("s1", 1, 2, "turn", 15.0, "Step 2 of module 1"),
            ("s1", 1, 2, "correction", 5.0, "Corrected step 2"),
            ("s1", 1, 3, "module_complete", 8.0, "Completed module 1"),
            ("s1", 2, 1, "module_start", 0.0, "Start module 2"),
            ("s1", 2, 1, "turn", 20.0, "Step 1 of module 2"),
            ("s1", 2, 2, "turn", 12.0, "Step 2 of module 2"),
            ("s1", 3, 1, "module_start", 0.0, "Start module 3"),
            ("s1", 3, 1, "correction", 7.0, "Correction in module 3"),
        ]

        for sid, mod, step, event, dur, msg in specs:
            entry = build_log_entry(sid, mod, step, event, dur, msg)
            append_entry(log_path, entry)

        # Parse and summarize
        result = parse_log(log_path)
        assert len(result.entries) == 10
        assert result.error_count == 0

        report = compute_summary(result.entries)

        # Module 1: 5 turns, 1 correction, 38.0 seconds
        mod1 = next(ms for ms in report.modules if ms.module == 1)
        assert mod1.turns == 5
        assert mod1.corrections == 1
        assert abs(mod1.total_seconds - 38.0) < 1e-6

        # Module 2: 3 turns, 0 corrections, 32.0 seconds
        mod2 = next(ms for ms in report.modules if ms.module == 2)
        assert mod2.turns == 3
        assert mod2.corrections == 0
        assert abs(mod2.total_seconds - 32.0) < 1e-6

        # Module 3: 2 turns, 1 correction, 7.0 seconds
        mod3 = next(ms for ms in report.modules if ms.module == 3)
        assert mod3.turns == 2
        assert mod3.corrections == 1
        assert abs(mod3.total_seconds - 7.0) < 1e-6

        # Overall
        assert report.overall_turns == 10
        assert report.overall_corrections == 2
        assert abs(report.overall_seconds - 77.0) < 1e-6

        # Confusion ranking: module 3 (0.5) > module 1 (0.2) > module 2 (0.0)
        assert len(report.confusion_ranking) == 3
        assert report.confusion_ranking[0] == (3, 0.5)
        assert report.confusion_ranking[1] == (1, 0.2)
        assert report.confusion_ranking[2] == (2, 0.0)


# ---------------------------------------------------------------------------
# 10.2 Multi-session aggregation
# ---------------------------------------------------------------------------

class TestMultiSessionAggregation:
    """10.2 Integration test: write entries with 2 different session_ids,
    verify summary aggregates across both sessions (Req 4.4)."""

    def test_two_sessions_aggregated(self, tmp_path):
        log_path = str(tmp_path / "session_log.jsonl")

        # Session 1: module 1
        for event, dur in [("turn", 10.0), ("correction", 5.0), ("turn", 8.0)]:
            entry = build_log_entry("session-A", 1, 1, event, dur, "s1")
            append_entry(log_path, entry)

        # Session 2: module 1 (same module, different session)
        for event, dur in [("turn", 12.0), ("turn", 6.0)]:
            entry = build_log_entry("session-B", 1, 1, event, dur, "s2")
            append_entry(log_path, entry)

        result = parse_log(log_path)
        report = compute_summary(result.entries)

        # Module 1 should aggregate across both sessions
        mod1 = next(ms for ms in report.modules if ms.module == 1)
        assert mod1.turns == 5  # 3 from session A + 2 from session B
        assert mod1.corrections == 1  # 1 from session A
        assert abs(mod1.total_seconds - 41.0) < 1e-6


# ---------------------------------------------------------------------------
# 10.3 Pretty-print with real log
# ---------------------------------------------------------------------------

class TestPrettyPrintIntegration:
    """10.3 Integration test: write entries then run --pretty, verify
    indented JSON output with blank line separation."""

    def test_pretty_print_output(self, tmp_path):
        log_path = str(tmp_path / "session_log.jsonl")

        entries_data = [
            ("s1", 1, 1, "turn", 5.0, "first"),
            ("s1", 2, 1, "turn", 10.0, "second"),
            ("s1", 1, 2, "correction", 3.0, "third"),
        ]
        for sid, mod, step, event, dur, msg in entries_data:
            entry = build_log_entry(sid, mod, step, event, dur, msg)
            append_entry(log_path, entry)

        # Capture stdout
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            analyze_main([log_path, "--pretty"])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue().strip()
        blocks = [b.strip() for b in output.split("\n\n") if b.strip()]

        # Should have 3 pretty-printed entries
        assert len(blocks) == 3

        # Each block should be valid indented JSON
        for block in blocks:
            parsed = json.loads(block)
            assert "module" in parsed
            assert "event" in parsed

        # Verify indentation (2-space indent)
        assert '  "' in output
