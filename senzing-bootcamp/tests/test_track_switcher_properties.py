"""Property-based tests for track_switcher.py using Hypothesis.

Feature: track-switching-support
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from track_switcher import (
    compute_switch,
    apply_switch,
    SwitchResult,
    load_track_definitions,
    load_module_names,
)


# ---------------------------------------------------------------------------
# Constants (from module-dependencies.yaml)
# ---------------------------------------------------------------------------

VALID_TRACKS = {"quick_demo", "core_bootcamp", "advanced_topics"}

TRACK_DEFINITIONS: dict[str, list[int]] = {
    "quick_demo": [2, 3],
    "core_bootcamp": [1, 2, 3, 4, 5, 6, 7],
    "advanced_topics": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "Quick Demo",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Load Data",
    7: "Query & Visualize",
    8: "Performance",
    9: "Security",
    10: "Monitoring",
    11: "Deployment",
}

ALL_MODULES = list(range(1, 12))


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_track_name(draw) -> str:
    """Sample from the three valid track names."""
    return draw(st.sampled_from(sorted(VALID_TRACKS)))


@st.composite
def st_invalid_track_name(draw) -> str:
    """Generate strings NOT in the valid track name set."""
    return draw(st.text(min_size=1).filter(lambda x: x not in VALID_TRACKS))


@st.composite
def st_modules_completed(draw) -> list[int]:
    """Generate subsets of modules 1-11 as sorted lists."""
    subset = draw(st.lists(st.sampled_from(ALL_MODULES), unique=True))
    return sorted(subset)


@st.composite
def st_progress_state(draw) -> dict:
    """Generate a full progress dict with track, modules_completed, step_history,
    current_module, current_step."""
    track = draw(st_track_name())
    modules_completed = draw(st_modules_completed())
    track_modules = TRACK_DEFINITIONS[track]

    # current_module: either None or a module in the track not yet completed
    remaining = [m for m in track_modules if m not in set(modules_completed)]
    current_module = draw(
        st.sampled_from(remaining) if remaining else st.just(None)
    )

    # current_step: None or a small integer
    current_step = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5)))

    # step_history: dict with string keys for completed modules
    step_history = {}
    for m in modules_completed:
        step_history[str(m)] = {
            "completed_at": "2025-07-15T10:00:00+00:00",
            "steps_completed": draw(st.integers(min_value=1, max_value=5)),
        }

    return {
        "track": track,
        "modules_completed": modules_completed,
        "step_history": step_history,
        "current_module": current_module,
        "current_step": current_step,
        "last_activity": "2025-07-15T10:00:00+00:00",
    }


@st.composite
def st_switch_pair(draw) -> tuple[str, str]:
    """Generate (current_track, target_track) pairs where current != target."""
    current = draw(st_track_name())
    target = draw(st_track_name().filter(lambda t: t != current))
    return (current, target)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestTrackSwitcherProperties:
    """Property-based tests for track switching logic."""

    class TestTrackModulePartition:
        """Property 1 — Track Module Partition.

        **Validates: Requirements 1.1, 7.1, 7.2**

        For any valid target track and completed modules, remaining ∪ (completed ∩ target)
        = target modules, with remaining preserving target ordering.
        """

        @given(
            target_track=st_track_name(),
            modules_completed=st_modules_completed(),
        )
        @settings(max_examples=100)
        def test_partition_equals_target(self, target_track, modules_completed):
            """remaining ∪ (completed ∩ target) = target modules."""
            current_track = "quick_demo"  # arbitrary valid current track

            result = compute_switch(
                current_track=current_track,
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            target_modules = set(TRACK_DEFINITIONS[target_track])
            completed_set = set(modules_completed)

            # remaining ∪ (completed ∩ target) should equal target modules
            remaining_set = set(result.remaining_modules)
            completed_in_target = completed_set & target_modules
            union = remaining_set | completed_in_target

            assert union == target_modules, (
                f"Partition mismatch: remaining={remaining_set}, "
                f"completed∩target={completed_in_target}, "
                f"union={union}, target={target_modules}"
            )

        @given(
            target_track=st_track_name(),
            modules_completed=st_modules_completed(),
        )
        @settings(max_examples=100)
        def test_remaining_preserves_target_ordering(self, target_track, modules_completed):
            """remaining_modules preserves the ordering defined in the target track."""
            current_track = "quick_demo"

            result = compute_switch(
                current_track=current_track,
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            target_modules = TRACK_DEFINITIONS[target_track]

            # remaining_modules should be a subsequence of target_modules
            # preserving order
            target_indices = []
            for m in result.remaining_modules:
                idx = target_modules.index(m)
                target_indices.append(idx)

            assert target_indices == sorted(target_indices), (
                f"Remaining modules {result.remaining_modules} do not preserve "
                f"target ordering {target_modules}"
            )

    class TestExtraModulesSetDifference:
        """Property 2 — Extra Modules Set Difference.

        **Validates: Requirements 1.2, 4.2, 7.3**

        For any valid target track and completed modules, extra = completed - target,
        with names included.
        """

        @given(
            target_track=st_track_name(),
            modules_completed=st_modules_completed(),
        )
        @settings(max_examples=100)
        def test_extra_equals_completed_minus_target(self, target_track, modules_completed):
            """extra_modules = modules_completed - target track modules."""
            current_track = "quick_demo"

            result = compute_switch(
                current_track=current_track,
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            target_set = set(TRACK_DEFINITIONS[target_track])
            completed_set = set(modules_completed)
            expected_extra = completed_set - target_set

            assert set(result.extra_modules) == expected_extra, (
                f"Extra mismatch: got {set(result.extra_modules)}, "
                f"expected {expected_extra}"
            )

        @given(
            target_track=st_track_name(),
            modules_completed=st_modules_completed(),
        )
        @settings(max_examples=100)
        def test_extra_modules_have_names(self, target_track, modules_completed):
            """Each extra module has its name included in extra_module_names."""
            current_track = "quick_demo"

            result = compute_switch(
                current_track=current_track,
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            for m in result.extra_modules:
                assert m in result.extra_module_names, (
                    f"Module {m} missing from extra_module_names"
                )
                assert result.extra_module_names[m] == MODULE_NAMES[m]

    class TestSameTrackNoOp:
        """Property 3 — Same-Track No-Op.

        **Validates: Requirements 1.3, 7.4**

        For any valid progress state, switching to the current track produces
        is_noop=True with modules_completed unchanged.
        """

        @given(state=st_progress_state())
        @settings(max_examples=100)
        def test_same_track_is_noop(self, state):
            """Switching to the current track is a no-op."""
            track = state["track"]
            modules_completed = state["modules_completed"]

            result = compute_switch(
                current_track=track,
                target_track=track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            assert result.is_noop is True, "Same-track switch should be a no-op"
            assert result.modules_completed == modules_completed, (
                "modules_completed should be unchanged for no-op"
            )

    class TestInvalidTrackRejection:
        """Property 4 — Invalid Track Rejection.

        **Validates: Requirements 1.4**

        For any string not in {quick_demo, core_bootcamp, advanced_topics},
        compute_switch raises ValueError containing the invalid name.
        """

        @given(invalid_name=st_invalid_track_name())
        @settings(max_examples=100)
        def test_invalid_target_raises_valueerror(self, invalid_name):
            """Invalid target track raises ValueError with the name in message."""
            with pytest.raises(ValueError) as exc_info:
                compute_switch(
                    current_track="quick_demo",
                    target_track=invalid_name,
                    modules_completed=[],
                    track_definitions=TRACK_DEFINITIONS,
                    module_names=MODULE_NAMES,
                )

            assert invalid_name in str(exc_info.value), (
                f"ValueError message should contain '{invalid_name}', "
                f"got: {exc_info.value}"
            )

    class TestProgressMonotonicity:
        """Property 5 — Progress Monotonicity.

        **Validates: Requirements 2.1, 2.2, 2.3, 7.5**

        For any valid state and switch, modules_completed never shrinks
        and step_history retains all entries.
        """

        @given(
            state=st_progress_state(),
            target_track=st_track_name(),
        )
        @settings(max_examples=100)
        def test_modules_completed_never_shrinks(self, state, target_track):
            """modules_completed in result is identical to input (never shrinks)."""
            modules_completed = state["modules_completed"]

            result = compute_switch(
                current_track=state["track"],
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            assert result.modules_completed == modules_completed, (
                f"modules_completed changed: input={modules_completed}, "
                f"output={result.modules_completed}"
            )

        @given(state=st_progress_state(), target_track=st_track_name())
        @settings(
            max_examples=100,
            suppress_health_check=[HealthCheck.function_scoped_fixture],
        )
        def test_step_history_retained_after_apply(self, state, target_track, tmp_path):
            """step_history retains all entries after apply_switch."""
            assume(state["track"] != target_track)

            modules_completed = state["modules_completed"]
            step_history = state["step_history"]

            # Create a unique progress file per example
            progress_path = tmp_path / f"progress_{uuid.uuid4().hex}.json"
            progress_path.write_text(json.dumps(state), encoding="utf-8")

            result = compute_switch(
                current_track=state["track"],
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            apply_switch(progress_path, result)

            updated = json.loads(progress_path.read_text(encoding="utf-8"))

            # All original step_history keys must still be present
            for key in step_history:
                assert key in updated.get("step_history", {}), (
                    f"step_history key '{key}' was lost after apply_switch"
                )
                assert updated["step_history"][key] == step_history[key]

    class TestProgressFileUpdateCorrectness:
        """Property 6 — Progress File Update Correctness.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

        For any valid non-noop switch, after apply_switch the progress file has
        correct track, current_module, current_step=null, and valid last_activity
        timestamp.
        """

        @given(state=st_progress_state(), target_track=st_track_name())
        @settings(
            max_examples=100,
            suppress_health_check=[HealthCheck.function_scoped_fixture],
        )
        def test_progress_file_fields_correct(self, state, target_track, tmp_path):
            """After apply_switch, progress file has correct fields."""
            assume(state["track"] != target_track)

            modules_completed = state["modules_completed"]

            # Create a unique progress file per example
            progress_path = tmp_path / f"progress_{uuid.uuid4().hex}.json"
            progress_path.write_text(json.dumps(state), encoding="utf-8")

            # Capture time before apply
            before_apply = datetime.now(timezone.utc)

            result = compute_switch(
                current_track=state["track"],
                target_track=target_track,
                modules_completed=modules_completed,
                track_definitions=TRACK_DEFINITIONS,
                module_names=MODULE_NAMES,
            )

            apply_switch(progress_path, result)

            # Capture time after apply
            after_apply = datetime.now(timezone.utc)

            updated = json.loads(progress_path.read_text(encoding="utf-8"))

            # track field equals target track
            assert updated["track"] == target_track, (
                f"track should be '{target_track}', got '{updated['track']}'"
            )

            # current_module equals first remaining or null
            expected_current = (
                result.remaining_modules[0] if result.remaining_modules else None
            )
            assert updated["current_module"] == expected_current, (
                f"current_module should be {expected_current}, "
                f"got {updated['current_module']}"
            )

            # current_step is null
            assert updated["current_step"] is None, (
                f"current_step should be null, got {updated['current_step']}"
            )

            # last_activity is a valid ISO 8601 UTC timestamp
            last_activity = updated["last_activity"]
            parsed_ts = datetime.fromisoformat(last_activity)
            assert parsed_ts.tzinfo is not None, "last_activity must have timezone"
            assert before_apply <= parsed_ts <= after_apply, (
                f"last_activity {last_activity} not between "
                f"{before_apply.isoformat()} and {after_apply.isoformat()}"
            )
