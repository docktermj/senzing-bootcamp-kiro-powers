"""Property-based tests for the first-visualization owed-on-opt-out invariant.

Feature: module3-first-visualization-guarantee, Property 1

Covers Task 2.2 — the owed-on-opt-out monotonic invariant for
``mark_first_visualization_owed`` in ``scripts/progress_utils.py``:

For any valid ``bootcamp_progress`` state (with or without a pre-existing
``first_visualization`` marker), invoking ``mark_first_visualization_owed``
results in a ``first_visualization`` marker being present and owed — unless it
was already ``satisfied``, in which case the status is never regressed to
``owed`` (the lifecycle is monotonic).

Validates: Requirements 1.1
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import (  # noqa: E402
    is_first_visualization_owed,
    mark_first_visualization_owed,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# A small pool of ISO-8601 timestamps for marker fields.
_ISO_TIMESTAMPS = st.sampled_from(
    [
        "2025-07-15T10:30:00Z",
        "2025-07-15T10:45:00+00:00",
        "2024-01-01T00:00:00Z",
        "2025-12-31T23:59:59Z",
    ]
)


@st.composite
def st_unrelated_progress(draw) -> dict:
    """Draw varied unrelated (but plausible) progress fields.

    These populate the progress dict around the ``first_visualization`` marker
    so the property exercises markers embedded in realistic, varied states.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A dict of assorted, marker-unrelated progress fields.
    """
    data: dict = {}
    if draw(st.booleans()):
        data["current_module"] = draw(st.integers(min_value=1, max_value=11))
    if draw(st.booleans()):
        data["modules_completed"] = draw(
            st.lists(st.integers(min_value=1, max_value=11), max_size=6, unique=True)
        )
    if draw(st.booleans()):
        data["database_type"] = draw(st.sampled_from(["sqlite", "postgres"]))
    if draw(st.booleans()):
        data["language"] = draw(
            st.sampled_from(["python", "java", "csharp", "rust", "typescript"])
        )
    if draw(st.booleans()):
        data["data_sources"] = draw(
            st.lists(st.text(min_size=1, max_size=8), max_size=4)
        )
    return data


@st.composite
def st_owed_marker(draw) -> dict:
    """Draw a well-formed ``owed`` first_visualization marker."""
    return {
        "status": "owed",
        "reason": draw(st.sampled_from(["module_3_opt_out", "manual"])),
        "owed_at": draw(_ISO_TIMESTAMPS),
        "satisfied_by": None,
        "satisfied_at": None,
    }


@st.composite
def st_satisfied_marker(draw) -> dict:
    """Draw a well-formed ``satisfied`` first_visualization marker."""
    return {
        "status": "satisfied",
        "reason": draw(st.sampled_from(["module_3_opt_out", "manual"])),
        "owed_at": draw(_ISO_TIMESTAMPS),
        "satisfied_by": draw(
            st.sampled_from(
                ["standalone_demo", "module_6_deferred", "module_7_deferred"]
            )
        ),
        "satisfied_at": draw(_ISO_TIMESTAMPS),
    }


@st.composite
def st_progress(draw) -> dict:
    """Draw a varied valid progress dict with the marker absent/owed/satisfied.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A progress dict whose ``first_visualization`` marker is one of:
        absent, ``owed``, or ``satisfied`` — combined with varied unrelated
        progress fields.
    """
    data = draw(st_unrelated_progress())
    marker_state = draw(st.sampled_from(["absent", "owed", "satisfied"]))
    if marker_state == "owed":
        data["first_visualization"] = draw(st_owed_marker())
    elif marker_state == "satisfied":
        data["first_visualization"] = draw(st_satisfied_marker())
    return data


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


def _write_progress_file(progress: dict) -> str:
    """Write ``progress`` to a fresh temp progress file and return its path."""
    tmp_dir = tempfile.mkdtemp()
    progress_path = Path(tmp_dir) / "config" / "bootcamp_progress.json"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    return str(progress_path)


class TestFirstVisualizationOwedProperty1:
    """Property 1: Opting out records an owed first visualization (monotonic).

    Feature: module3-first-visualization-guarantee, Property 1: Opting out
    records an owed first visualization — for any valid progress state,
    ``mark_first_visualization_owed`` leaves a marker present and owed, except
    when it was already ``satisfied`` (then it is left unchanged).

    Validates: Requirements 1.1
    """

    @given(progress=st_progress())
    def test_mark_owed_records_owed_marker_monotonically(
        self, progress: dict
    ) -> None:
        """After marking, the marker is present and owed unless already satisfied.

        Writes the generated progress dict to a temp progress file, invokes
        ``mark_first_visualization_owed`` against that path, then re-reads the
        file to assert the resulting marker state.
        """
        before_marker = progress.get("first_visualization")
        was_satisfied = (
            isinstance(before_marker, dict)
            and before_marker.get("status") == "satisfied"
        )

        progress_path = _write_progress_file(progress)
        try:
            mark_first_visualization_owed(progress_path=progress_path)
            after = json.loads(Path(progress_path).read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(Path(progress_path).parent.parent, ignore_errors=True)

        after_marker = after.get("first_visualization")
        assert isinstance(after_marker, dict), (
            "first_visualization marker must be present after marking owed"
        )

        if was_satisfied:
            # Monotonic: a satisfied marker is never regressed to owed.
            assert after_marker.get("status") == "satisfied"
            assert after_marker == before_marker
            assert not is_first_visualization_owed(after)
        else:
            # Absent or already owed -> owed after marking.
            assert after_marker.get("status") == "owed"
            assert is_first_visualization_owed(after)
