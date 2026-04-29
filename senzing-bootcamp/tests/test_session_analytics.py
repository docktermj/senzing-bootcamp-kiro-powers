"""Property-based tests for session-analytics feature.

Uses Hypothesis to verify correctness properties across a wide input space.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

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
    format_json,
    format_text,
    pretty_print_entries,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

st_session_id = st.uuids().map(str)
st_module = st.integers(min_value=1, max_value=11)
st_step = st.one_of(st.integers(min_value=1, max_value=100), st.text(min_size=1, max_size=10))
st_event = st.sampled_from(sorted(VALID_EVENTS))
st_duration = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
st_message = st.text(min_size=0, max_size=200)


@st.composite
def st_log_entry(draw):
    """Generate a valid LogEntry via build_log_entry."""
    return build_log_entry(
        session_id=draw(st_session_id),
        module=draw(st_module),
        step=draw(st_step),
        event=draw(st_event),
        duration_seconds=draw(st_duration),
        message=draw(st_message),
    )


@st.composite
def st_entry_dict(draw):
    """Generate a valid log entry as a dict (simulating parsed JSON)."""
    entry = draw(st_log_entry())
    return json.loads(serialize_entry(entry))


@st.composite
def st_invalid_line(draw):
    """Generate a string that is NOT valid JSON and contains no newlines."""
    base = draw(
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Cc", "Cs", "Zl", "Zp"),
            ),
            min_size=1,
            max_size=100,
        )
    )
    # Ensure it's not valid JSON
    try:
        json.loads(base)
        # If it parsed, mangle it to make it invalid
        return "{invalid:" + base
    except (json.JSONDecodeError, ValueError):
        return base


@st.composite
def st_mixed_jsonl(draw):
    """Generate a mix of valid JSON lines and invalid lines.

    Returns (lines, valid_dicts, invalid_count).
    """
    valid_entries = draw(st.lists(st_entry_dict(), min_size=0, max_size=10))
    invalid_lines = draw(st.lists(st_invalid_line(), min_size=0, max_size=10))

    valid_lines = [json.dumps(e, separators=(",", ":")) for e in valid_entries]

    # Tag each line so we can reconstruct
    tagged = [(line, True) for line in valid_lines] + [
        (line, False) for line in invalid_lines
    ]
    # Shuffle deterministically using Hypothesis
    shuffled = draw(st.permutations(tagged))

    lines = [t[0] for t in shuffled]
    expected_valid = [json.loads(t[0]) for t in shuffled if t[1]]
    expected_invalid_count = sum(1 for t in shuffled if not t[1])

    return lines, expected_valid, expected_invalid_count


# ---------------------------------------------------------------------------
# Property 1: Append Preserves Existing Lines and Adds Exactly One
# **Validates: Requirements 1.1, 1.3**
# ---------------------------------------------------------------------------

class TestProperty1AppendPreservesAndAddsOne:
    """Feature: session-analytics, Property 1: Append Preserves Existing Lines and Adds Exactly One"""

    @given(
        existing_lines=st.lists(
            st.text(
                alphabet=st.characters(
                    blacklist_categories=("Cc", "Cs", "Zl", "Zp"),
                ),
                min_size=1,
                max_size=100,
            ),
            min_size=0,
            max_size=10,
        ),
        entry=st_log_entry(),
    )
    @settings(max_examples=100)
    def test_append_preserves_existing_and_adds_one(self, existing_lines, entry):
        """**Validates: Requirements 1.1, 1.3**"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.jsonl"

            # Write existing content
            if existing_lines:
                log_file.write_text(
                    "\n".join(existing_lines) + "\n", encoding="utf-8"
                )

            # Append new entry
            append_entry(str(log_file), entry)

            result_lines = log_file.read_text(encoding="utf-8").splitlines()

            # Existing lines are preserved
            for i, original in enumerate(existing_lines):
                assert result_lines[i] == original

            # Exactly one new line added
            assert len(result_lines) == len(existing_lines) + 1

            # The new line is valid JSON matching the entry
            new_line = result_lines[-1]
            parsed = json.loads(new_line)
            assert parsed["session_id"] == entry.session_id


# ---------------------------------------------------------------------------
# Property 2: Log Entry Schema and JSONL Format Validity
# **Validates: Requirements 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**
# ---------------------------------------------------------------------------

class TestProperty2SchemaValidity:
    """Feature: session-analytics, Property 2: Log Entry Schema and JSONL Format Validity"""

    @given(entry=st_log_entry())
    @settings(max_examples=100)
    def test_serialized_entry_is_valid_json_with_correct_schema(self, entry):
        """**Validates: Requirements 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**"""
        serialized = serialize_entry(entry)

        # Must be valid JSON
        parsed = json.loads(serialized)

        # All required fields present
        required_fields = {
            "timestamp", "session_id", "module", "step",
            "event", "duration_seconds", "message",
        }
        assert set(parsed.keys()) == required_fields

        # Type and range checks
        assert isinstance(parsed["timestamp"], str)
        # Verify ISO 8601 by parsing
        from datetime import datetime, timezone
        datetime.fromisoformat(parsed["timestamp"])

        assert isinstance(parsed["session_id"], str)
        assert len(parsed["session_id"]) > 0

        assert isinstance(parsed["module"], int)
        assert 1 <= parsed["module"] <= 11

        assert isinstance(parsed["step"], (str, int))

        assert parsed["event"] in VALID_EVENTS

        assert isinstance(parsed["duration_seconds"], (int, float))
        assert parsed["duration_seconds"] >= 0

        assert isinstance(parsed["message"], str)


# ---------------------------------------------------------------------------
# Property 3: Write-Parse Round-Trip
# **Validates: Requirements 3.1, 3.4**
# ---------------------------------------------------------------------------

class TestProperty3RoundTrip:
    """Feature: session-analytics, Property 3: Write-Parse Round-Trip"""

    @given(entry=st_log_entry())
    @settings(max_examples=100)
    def test_serialize_then_parse_round_trip(self, entry):
        """**Validates: Requirements 3.1, 3.4**"""
        serialized = serialize_entry(entry)
        parsed = json.loads(serialized)

        assert parsed["timestamp"] == entry.timestamp
        assert parsed["session_id"] == entry.session_id
        assert parsed["module"] == entry.module
        assert parsed["step"] == entry.step
        assert parsed["event"] == entry.event
        assert parsed["duration_seconds"] == entry.duration_seconds
        assert parsed["message"] == entry.message


# ---------------------------------------------------------------------------
# Property 4: Invalid Line Resilience
# **Validates: Requirements 3.2**
# ---------------------------------------------------------------------------

class TestProperty4InvalidLineResilience:
    """Feature: session-analytics, Property 4: Invalid Line Resilience"""

    @given(data=st_mixed_jsonl())
    @settings(max_examples=100)
    def test_parse_log_handles_invalid_lines(self, data):
        """**Validates: Requirements 3.2**"""
        lines, expected_valid, expected_invalid_count = data

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.jsonl"
            log_file.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")

            result = parse_log(str(log_file))

            assert result.error_count == expected_invalid_count
            assert len(result.entries) == len(expected_valid)
            for actual, expected in zip(result.entries, expected_valid):
                assert actual == expected


# ---------------------------------------------------------------------------
# Property 5: Per-Module Aggregation Correctness
# **Validates: Requirements 4.1, 4.4**
# ---------------------------------------------------------------------------

class TestProperty5Aggregation:
    """Feature: session-analytics, Property 5: Per-Module Aggregation Correctness"""

    @given(entries=st.lists(st_entry_dict(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_per_module_aggregation_matches_manual_sums(self, entries):
        """**Validates: Requirements 4.1, 4.4**"""
        report = compute_summary(entries)

        # Manual calculation
        from collections import defaultdict
        manual_turns: dict[int, int] = defaultdict(int)
        manual_corrections: dict[int, int] = defaultdict(int)
        manual_seconds: dict[int, float] = defaultdict(float)

        for e in entries:
            mod = e["module"]
            manual_turns[mod] += 1
            if e["event"] == "correction":
                manual_corrections[mod] += 1
            manual_seconds[mod] += float(e["duration_seconds"])

        for ms in report.modules:
            assert ms.turns == manual_turns[ms.module]
            assert ms.corrections == manual_corrections[ms.module]
            assert abs(ms.total_seconds - manual_seconds[ms.module]) < 1e-6


# ---------------------------------------------------------------------------
# Property 6: Summary Report Structure Invariant
# **Validates: Requirements 4.2, 4.3**
# ---------------------------------------------------------------------------

class TestProperty6StructureInvariant:
    """Feature: session-analytics, Property 6: Summary Report Structure Invariant"""

    @given(entries=st.lists(st_entry_dict(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_modules_ascending_and_overall_equals_sum(self, entries):
        """**Validates: Requirements 4.2, 4.3**"""
        report = compute_summary(entries)

        # Modules in ascending order
        module_numbers = [ms.module for ms in report.modules]
        assert module_numbers == sorted(module_numbers)

        # Overall totals equal sum of per-module values
        assert report.overall_turns == sum(ms.turns for ms in report.modules)
        assert report.overall_corrections == sum(ms.corrections for ms in report.modules)
        assert abs(report.overall_seconds - sum(ms.total_seconds for ms in report.modules)) < 1e-6


# ---------------------------------------------------------------------------
# Property 7: Confusion Ranking Correctness
# **Validates: Requirements 5.1, 5.2, 5.3**
# ---------------------------------------------------------------------------

class TestProperty7ConfusionRanking:
    """Feature: session-analytics, Property 7: Confusion Ranking Correctness"""

    @given(entries=st.lists(st_entry_dict(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_confusion_ranking_correct(self, entries):
        """**Validates: Requirements 5.1, 5.2, 5.3**"""
        report = compute_summary(entries)

        # All ranked modules have non-zero turns
        ranked_modules = {mod for mod, _ in report.confusion_ranking}
        for ms in report.modules:
            if ms.turns == 0:
                assert ms.module not in ranked_modules
            else:
                assert ms.module in ranked_modules

        # Densities are correctly computed and rounded
        module_map = {ms.module: ms for ms in report.modules}
        for mod, density in report.confusion_ranking:
            ms = module_map[mod]
            expected = round(ms.corrections / ms.turns, 2)
            assert density == expected

        # Sorted descending by density
        densities = [d for _, d in report.confusion_ranking]
        assert densities == sorted(densities, reverse=True)


# ---------------------------------------------------------------------------
# Property 8: JSON Output Validity
# **Validates: Requirements 6.2**
# ---------------------------------------------------------------------------

class TestProperty8JsonOutputValidity:
    """Feature: session-analytics, Property 8: JSON Output Validity"""

    @given(entries=st.lists(st_entry_dict(), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_format_json_produces_valid_json_with_required_keys(self, entries):
        """**Validates: Requirements 6.2**"""
        report = compute_summary(entries)
        json_str = format_json(report)

        parsed = json.loads(json_str)
        assert "modules" in parsed
        assert "overall" in parsed
        assert "confusion_ranking" in parsed

        assert isinstance(parsed["modules"], list)
        assert isinstance(parsed["overall"], dict)
        assert isinstance(parsed["confusion_ranking"], list)


# ---------------------------------------------------------------------------
# Property 9: Pretty-Print Round-Trip
# **Validates: Requirements 7.1, 7.3**
# ---------------------------------------------------------------------------

class TestProperty9PrettyPrintRoundTrip:
    """Feature: session-analytics, Property 9: Pretty-Print Round-Trip"""

    @given(entry_dict=st_entry_dict())
    @settings(max_examples=100)
    def test_pretty_print_round_trip(self, entry_dict):
        """**Validates: Requirements 7.1, 7.3**"""
        pretty = pretty_print_entries([entry_dict])
        # Strip whitespace and re-parse
        reparsed = json.loads(pretty.strip())
        assert reparsed == entry_dict


# ---------------------------------------------------------------------------
# Property 10: Module Filter Correctness
# **Validates: Requirements 7.2**
# ---------------------------------------------------------------------------

class TestProperty10ModuleFilter:
    """Feature: session-analytics, Property 10: Module Filter Correctness"""

    @given(
        entries=st.lists(st_entry_dict(), min_size=1, max_size=20),
        filter_module=st_module,
    )
    @settings(max_examples=100)
    def test_module_filter_returns_exact_matches(self, entries, filter_module):
        """**Validates: Requirements 7.2**"""
        result = pretty_print_entries(entries, module_filter=filter_module)

        # Parse back the pretty-printed entries
        if not result.strip():
            # No entries matched — verify none should have
            assert all(e.get("module") != filter_module for e in entries)
        else:
            blocks = result.split("\n\n")
            parsed_entries = [json.loads(b) for b in blocks if b.strip()]

            # All returned entries have the correct module
            for pe in parsed_entries:
                assert pe["module"] == filter_module

            # Count matches the expected number
            expected_count = sum(
                1 for e in entries if e.get("module") == filter_module
            )
            assert len(parsed_entries) == expected_count
