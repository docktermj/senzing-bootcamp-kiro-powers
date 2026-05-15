"""Property-based tests for backward compatibility with legacy progress files.

Feature: mid-module-session-persistence
Covers Property 4 (backward compatibility — legacy integer-only progress files).
"""

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

from progress_utils import validate_progress_schema, write_checkpoint


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_legacy_progress(draw):
    """Generate a legacy progress dict with integer-only steps."""
    # current_step: int or None
    current_step = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=30)))

    # step_history: 0-3 entries with integer last_completed_step
    num_entries = draw(st.integers(min_value=0, max_value=3))
    step_history = {}
    if num_entries > 0:
        keys = draw(st.lists(
            st.integers(min_value=1, max_value=12),
            min_size=num_entries, max_size=num_entries, unique=True,
        ))
        for key in keys:
            step_history[str(key)] = {
                "last_completed_step": draw(st.integers(min_value=1, max_value=30)),
                "updated_at": "2026-06-15T14:30:00+00:00",
            }

    data = {"current_step": current_step}
    if step_history:
        data["step_history"] = step_history
    return data


# ---------------------------------------------------------------------------
# Property 4: Backward Compatibility — Legacy Integer-Only Progress Files
# ---------------------------------------------------------------------------


class TestBackwardCompatibilityLegacyProgress:
    """Property 4: Backward Compatibility — Legacy Integer-Only Progress Files.

    **Validates: Requirements 2.5, 8.1, 8.3, 11.1, 11.2, 11.3**
    """

    @given(data=st_legacy_progress())
    @settings(max_examples=10)
    def test_legacy_progress_passes_validation(self, data):
        """Legacy progress dicts with integer-only steps produce zero validation errors."""
        errors = validate_progress_schema(data)
        assert errors == [], (
            f"Expected zero errors for legacy progress {data!r}, got: {errors}"
        )

    @given(
        module_number=st.integers(min_value=1, max_value=12),
        step=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=10)
    def test_write_checkpoint_integer_passes_validation(self, module_number, step):
        """write_checkpoint with an integer step produces a file that passes validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        # Remove the empty file so _read_progress returns {} instead of
        # attempting to parse empty content as JSON.
        os.unlink(path)
        try:
            write_checkpoint(module_number=module_number, step=step, progress_path=path)
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            errors = validate_progress_schema(data)
            assert errors == [], (
                f"Expected zero errors after write_checkpoint(module={module_number}, "
                f"step={step}), got: {errors}"
            )
        finally:
            if os.path.exists(path):
                os.unlink(path)
