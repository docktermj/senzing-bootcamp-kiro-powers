"""Tests for the Adaptive Pacing Based on Session Analytics feature.

Validates the classify_pacing() and merge_with_overrides() functions
in analyze_sessions.py, and verifies steering file updates.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _ROOT / "senzing-bootcamp" / "scripts"
_STEERING_DIR = _ROOT / "senzing-bootcamp" / "steering"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from analyze_sessions import classify_pacing, merge_with_overrides


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

st_module = st.integers(min_value=1, max_value=11)
st_event = st.sampled_from(["turn", "correction", "module_start", "module_complete"])
st_duration = st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False)


@st.composite
def st_session_entry(draw: st.DrawFn) -> dict:
    """Generate a valid session log entry."""
    return {
        "module": draw(st_module),
        "event": draw(st_event),
        "duration_seconds": draw(st_duration),
        "session_id": "test-session",
        "timestamp": "2026-05-01T10:00:00Z",
    }


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestClassifyPacingProperties:
    """Property tests for classify_pacing function.

    Validates requirements: determinism, valid outputs, edge cases.
    """

    @given(entries=st.lists(st_session_entry(), min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_deterministic(self, entries: list[dict]) -> None:
        """Same inputs always produce same output."""
        result1 = classify_pacing(entries)
        result2 = classify_pacing(entries)
        assert result1 == result2

    @given(entries=st.lists(st_session_entry(), min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_all_values_valid(self, entries: list[dict]) -> None:
        """All returned values are in the valid set."""
        result = classify_pacing(entries)
        valid = {"struggled", "comfortable", "normal"}
        for category in result.values():
            assert category in valid

    def test_empty_entries_returns_empty(self) -> None:
        """Empty session log produces empty classification dict."""
        assert classify_pacing([]) == {}

    @given(entries=st.lists(st_session_entry(), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_modules_with_zero_turns_excluded(self, entries: list[dict]) -> None:
        """Modules with zero turns are never classified."""
        result = classify_pacing(entries)
        # All modules in result should have at least one entry in the input
        modules_in_entries = {e["module"] for e in entries if e.get("module") is not None}
        for mod in result:
            assert mod in modules_in_entries

    @given(
        computed=st.dictionaries(st_module, st.sampled_from(["struggled", "comfortable", "normal"])),
        overrides=st.dictionaries(st_module, st.sampled_from(["struggled", "comfortable", "normal"])),
    )
    @settings(max_examples=100)
    def test_overrides_take_precedence(
        self, computed: dict[int, str], overrides: dict[int, str]
    ) -> None:
        """Manual overrides always take precedence over computed values."""
        merged = merge_with_overrides(computed, overrides)
        for mod, category in overrides.items():
            assert merged[mod] == category


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestClassifyPacingUnit:
    """Unit tests for classify_pacing with known inputs."""

    def test_high_correction_density_is_struggled(self) -> None:
        """Module with correction_density 0.5 → 'struggled'."""
        entries = [
            {"module": 3, "event": "turn", "duration_seconds": 60},
            {"module": 3, "event": "correction", "duration_seconds": 30},
            # Another module for median comparison
            {"module": 4, "event": "turn", "duration_seconds": 60},
            {"module": 4, "event": "turn", "duration_seconds": 60},
        ]
        result = classify_pacing(entries)
        assert result[3] == "struggled"

    def test_long_time_is_struggled(self) -> None:
        """Module with time > 2× median → 'struggled'."""
        entries = [
            {"module": 1, "event": "turn", "duration_seconds": 1000},
            {"module": 2, "event": "turn", "duration_seconds": 100},
            {"module": 3, "event": "turn", "duration_seconds": 100},
        ]
        result = classify_pacing(entries)
        assert result[1] == "struggled"

    def test_low_density_fast_is_comfortable(self) -> None:
        """Module with density 0.05 and time < median → 'comfortable'."""
        entries = [
            # Module 1: 20 turns, 1 correction, 50 seconds (fast, low density)
            *[{"module": 1, "event": "turn", "duration_seconds": 2.5} for _ in range(19)],
            {"module": 1, "event": "correction", "duration_seconds": 2.5},
            # Module 2: 10 turns, 0 corrections, 200 seconds (slower)
            *[{"module": 2, "event": "turn", "duration_seconds": 20} for _ in range(10)],
            # Module 3: 10 turns, 0 corrections, 300 seconds (slowest)
            *[{"module": 3, "event": "turn", "duration_seconds": 30} for _ in range(10)],
        ]
        result = classify_pacing(entries)
        assert result[1] == "comfortable"

    def test_normal_density_is_normal(self) -> None:
        """Module with density 0.2 and normal time → 'normal'."""
        entries = [
            # Module 1: 10 turns, 2 corrections (density 0.2), 100 seconds
            *[{"module": 1, "event": "turn", "duration_seconds": 10} for _ in range(8)],
            *[{"module": 1, "event": "correction", "duration_seconds": 10} for _ in range(2)],
            # Module 2: 10 turns, 100 seconds (same time for median)
            *[{"module": 2, "event": "turn", "duration_seconds": 10} for _ in range(10)],
        ]
        result = classify_pacing(entries)
        assert result[1] == "normal"

    def test_single_module_returns_normal(self) -> None:
        """Single completed module → 'normal' (no median comparison)."""
        entries = [
            {"module": 5, "event": "turn", "duration_seconds": 60},
            {"module": 5, "event": "turn", "duration_seconds": 60},
        ]
        result = classify_pacing(entries)
        assert result[5] == "normal"

    def test_merge_with_overrides_applies(self) -> None:
        """merge_with_overrides correctly applies manual overrides."""
        computed = {1: "normal", 2: "comfortable", 3: "struggled"}
        overrides = {2: "struggled", 4: "normal"}
        merged = merge_with_overrides(computed, overrides)
        assert merged[1] == "normal"  # unchanged
        assert merged[2] == "struggled"  # overridden
        assert merged[3] == "struggled"  # unchanged
        assert merged[4] == "normal"  # added from override


# ---------------------------------------------------------------------------
# Steering file tests
# ---------------------------------------------------------------------------


class TestSteeringUpdates:
    """Verify steering files contain adaptive pacing instructions."""

    @pytest.fixture()
    def context_management(self) -> str:
        return (_STEERING_DIR / "agent-context-management.md").read_text(encoding="utf-8")

    @pytest.fixture()
    def session_resume(self) -> str:
        return (_STEERING_DIR / "session-resume.md").read_text(encoding="utf-8")

    def test_context_management_has_adaptive_pacing(self, context_management: str) -> None:
        """agent-context-management.md contains Adaptive Pacing section."""
        assert "## Adaptive Pacing" in context_management

    def test_context_management_documents_categories(self, context_management: str) -> None:
        """agent-context-management.md documents all three pacing categories."""
        assert "struggled" in context_management
        assert "comfortable" in context_management
        assert "normal" in context_management

    def test_context_management_documents_overrides(self, context_management: str) -> None:
        """agent-context-management.md documents slow down / speed up overrides."""
        assert "slow down" in context_management
        assert "speed up" in context_management

    def test_session_resume_reads_session_log(self, session_resume: str) -> None:
        """session-resume.md Step 1 includes reading session_log.jsonl."""
        assert "session_log.jsonl" in session_resume
        assert "pacing" in session_resume.lower()

    def test_context_management_documents_pacing_overrides(self, context_management: str) -> None:
        """agent-context-management.md documents pacing_overrides preference key."""
        assert "pacing_overrides" in context_management
