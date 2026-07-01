"""Property test for the ``first_visualization`` clear + idempotence invariant.

Feature: module3-first-visualization-guarantee, Property 3: Any generated first
visualization clears the owed marker (idempotently).

Covers Task 2.3 — Property 3 from the design document:

    For any ``bootcamp_progress`` state, invoking
    ``clear_first_visualization_owed(satisfied_by=...)`` results in
    ``is_first_visualization_owed`` returning ``False`` and (when a marker was
    present) the marker status being ``"satisfied"``. Applying the clear a
    second time produces the same state (idempotence).

Design nuance honored here: ``clear_first_visualization_owed`` is a NO-OP when
the marker is ABSENT (never owed) — it does not fabricate a satisfied marker.
So "status == satisfied after clear" only holds when a marker was present
beforehand. When the marker was absent, after clear the state remains
absent / not-owed.

Validates: Requirements 2.2, 2.3
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import (
    clear_first_visualization_owed,
    is_first_visualization_owed,
)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_ISO_TS = "2025-07-15T10:30:00+00:00"

# Sources that could plausibly satisfy the obligation.
_SATISFIED_BY = st.sampled_from(
    ["standalone_demo", "module_6_deferred", "module_7_deferred"]
)


@st.composite
def st_first_visualization_marker(draw) -> dict | None:
    """Draw a ``first_visualization`` marker in any lifecycle state, or ``None``.

    Returns one of three shapes:

    - ``None`` — no marker at all (backward-compatible "never owed").
    - an ``owed`` marker (present, not yet satisfied).
    - a ``satisfied`` marker (already cleared).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A marker dict, or ``None`` when the marker should be absent.
    """
    state = draw(st.sampled_from(["absent", "owed", "satisfied"]))
    if state == "absent":
        return None
    if state == "owed":
        return {
            "status": "owed",
            "reason": draw(st.sampled_from(["module_3_opt_out", "manual"])),
            "owed_at": _ISO_TS,
            "satisfied_by": None,
            "satisfied_at": None,
        }
    return {
        "status": "satisfied",
        "reason": "module_3_opt_out",
        "owed_at": _ISO_TS,
        "satisfied_by": draw(_SATISFIED_BY),
        "satisfied_at": "2025-07-15T10:45:00+00:00",
    }


@st.composite
def st_progress(draw) -> dict:
    """Draw a varied, plausible progress dict with any ``first_visualization`` state.

    Unrelated fields are included so the property exercises realistic progress
    files rather than isolated markers.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A progress dict suitable for writing to a progress file.
    """
    progress: dict = {
        "current_module": draw(st.integers(min_value=1, max_value=11)),
        "modules_completed": draw(
            st.lists(st.integers(min_value=1, max_value=11), max_size=11, unique=True)
        ),
        "language": draw(st.sampled_from(["python", "java", "rust", "typescript"])),
        "database_type": draw(st.sampled_from(["sqlite", "postgres"])),
    }
    marker = draw(st_first_visualization_marker())
    if marker is not None:
        progress["first_visualization"] = marker
    return progress


def _write_and_reread(progress: dict, satisfied_by: str) -> dict:
    """Write ``progress`` to a temp file, clear the marker, and re-read the result.

    Args:
        progress: The progress dict to persist before clearing.
        satisfied_by: The source recorded by ``clear_first_visualization_owed``.

    Returns:
        The progress dict re-read from disk after a single clear.
    """
    td = tempfile.mkdtemp()
    try:
        path = str(Path(td) / "bootcamp_progress.json")
        Path(path).write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
        clear_first_visualization_owed(satisfied_by=satisfied_by, progress_path=path)
        return json.loads(Path(path).read_text(encoding="utf-8"))
    finally:
        shutil.rmtree(td, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
# Property 3: clearing clears the owed marker (idempotently)
# Feature: module3-first-visualization-guarantee, Property 3
# Validates: Requirements 2.2, 2.3
# ═══════════════════════════════════════════════════════════════════════════


class TestClearFirstVisualizationOwed:
    """Property 3 — any generated first visualization clears the owed marker."""

    @given(progress=st_progress(), satisfied_by=_SATISFIED_BY)
    def test_clear_yields_not_owed_and_satisfied(
        self, progress: dict, satisfied_by: str
    ) -> None:
        """After clearing, the visualization is not owed; a present marker is satisfied.

        Feature: module3-first-visualization-guarantee, Property 3
        Validates: Requirements 2.2, 2.3
        """
        had_marker = "first_visualization" in progress
        result = _write_and_reread(progress, satisfied_by)

        # Regardless of prior state, no first visualization is owed afterwards.
        assert not is_first_visualization_owed(result)

        if had_marker:
            # A present marker (owed or already satisfied) ends up satisfied.
            assert result["first_visualization"]["status"] == "satisfied"
        else:
            # A never-owed (absent) marker is not fabricated — clear is a no-op.
            assert "first_visualization" not in result

    @given(progress=st_progress(), satisfied_by=_SATISFIED_BY)
    def test_second_clear_is_a_no_op(
        self, progress: dict, satisfied_by: str
    ) -> None:
        """A second clear produces byte-identical state (idempotence).

        Feature: module3-first-visualization-guarantee, Property 3
        Validates: Requirements 2.2, 2.3
        """
        td = tempfile.mkdtemp()
        try:
            path = str(Path(td) / "bootcamp_progress.json")
            Path(path).write_text(
                json.dumps(progress, indent=2) + "\n", encoding="utf-8"
            )

            clear_first_visualization_owed(
                satisfied_by=satisfied_by, progress_path=path
            )
            after_first = json.loads(Path(path).read_text(encoding="utf-8"))
            snapshot = copy.deepcopy(after_first)

            clear_first_visualization_owed(
                satisfied_by=satisfied_by, progress_path=path
            )
            after_second = json.loads(Path(path).read_text(encoding="utf-8"))

            assert after_second == snapshot
            assert not is_first_visualization_owed(after_second)
        finally:
            shutil.rmtree(td, ignore_errors=True)
