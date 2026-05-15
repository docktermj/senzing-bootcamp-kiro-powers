"""Property-based tests for sub-step checkpoint round-trip.

Feature: mid-module-session-persistence
Covers Property 1 (checkpoint round-trip preserves type and value).
"""

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import write_checkpoint


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_module_step_pair(draw):
    """Generate a (module_number, step) pair."""
    module_number = draw(st.integers(min_value=1, max_value=12))
    choice = draw(st.sampled_from(["int", "dotted", "lettered"]))
    if choice == "int":
        step = draw(st.integers(min_value=1, max_value=30))
    elif choice == "dotted":
        parent = draw(st.integers(min_value=1, max_value=12))
        sub = draw(st.integers(min_value=1, max_value=20))
        step = f"{parent}.{sub}"
    else:
        parent = draw(st.integers(min_value=1, max_value=12))
        letter = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
        step = f"{parent}{letter}"
    return (module_number, step)


# ---------------------------------------------------------------------------
# Property 1: Checkpoint Round-Trip Preserves Type and Value
# ---------------------------------------------------------------------------


class TestCheckpointRoundTripPreservesTypeAndValue:
    """Property 1: Checkpoint Round-Trip Preserves Type and Value.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 10.1, 10.2, 10.3, 10.4**
    """

    @given(pair=st_module_step_pair())
    @settings(max_examples=10)
    def test_checkpoint_round_trip(self, pair):
        """Writing a checkpoint and reading it back preserves step type and value."""
        module_number, step = pair
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        # Remove the empty file so _read_progress returns {} instead of
        # attempting to parse empty content as JSON.
        os.unlink(path)
        try:
            write_checkpoint(module_number=module_number, step=step, progress_path=path)
            data = json.loads(Path(path).read_text(encoding="utf-8"))

            # current_step matches type and value
            assert data["current_step"] == step
            assert type(data["current_step"]) is type(step)

            # step_history matches
            key = str(module_number)
            assert key in data["step_history"]
            assert data["step_history"][key]["last_completed_step"] == step
            assert type(data["step_history"][key]["last_completed_step"]) is type(step)

            # updated_at is valid ISO 8601
            ts = data["step_history"][key]["updated_at"]
            datetime.datetime.fromisoformat(ts)
        finally:
            os.unlink(path)
