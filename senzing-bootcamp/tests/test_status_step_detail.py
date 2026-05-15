"""Property-based tests for status.py step-level detail functions.

Feature: step-level-status-command
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup — scripts aren't packages
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import status  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_INDEX_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "steering-index.yaml"
)

# Expected total steps per module from the design document
_EXPECTED_TOTALS: dict[int, int | None] = {
    1: 18,
    2: 9,
    3: 12,
    4: None,
    5: 26,
    6: 27,
    7: None,
    8: 13,
    9: 12,
    10: 10,
    11: 15,
}

_MODULES_WITH_PHASES = [m for m, v in _EXPECTED_TOTALS.items() if v is not None]
_MODULES_WITHOUT_PHASES = [m for m, v in _EXPECTED_TOTALS.items() if v is None]


# ---------------------------------------------------------------------------
# Property 3: Total steps extraction from steering-index
# ---------------------------------------------------------------------------


class TestProperty3TotalStepsExtraction:
    """Property 3: Total steps extraction from steering-index.

    For each module with phases in steering-index.yaml, verify
    _get_module_total_steps returns the maximum upper-bound of all step_range
    entries. For modules without phases (4, 7), verify it returns None.

    Feature: step-level-status-command, Property 3: Total steps extraction
    Validates: Requirements 3
    """

    @given(module=st.sampled_from(_MODULES_WITH_PHASES))
    @settings(max_examples=5)
    def test_modules_with_phases_return_expected_total(self, module: int) -> None:
        """Modules with phases return the max upper-bound of step_range entries."""
        result = status._get_module_total_steps(_STEERING_INDEX_PATH, module)
        expected = _EXPECTED_TOTALS[module]
        assert result == expected, (
            f"Module {module}: expected {expected}, got {result}"
        )

    @given(module=st.sampled_from(_MODULES_WITHOUT_PHASES))
    @settings(max_examples=5)
    def test_modules_without_phases_return_none(self, module: int) -> None:
        """Modules without phases (4, 7) return None."""
        result = status._get_module_total_steps(_STEERING_INDEX_PATH, module)
        assert result is None, (
            f"Module {module}: expected None, got {result}"
        )


# ---------------------------------------------------------------------------
# Property 1: Step detail output format correctness
# ---------------------------------------------------------------------------


# Strategy: generate a module with phases and a valid step value for it
@st.composite
def st_module_and_step(draw):
    """Generate a (module_number, step_value, total_steps) tuple.

    Picks a random module that has phases, then generates a random integer
    step value between 1 and that module's total steps.
    """
    module = draw(st.sampled_from(_MODULES_WITH_PHASES))
    total = _EXPECTED_TOTALS[module]
    step = draw(st.integers(min_value=1, max_value=total))
    return module, step, total


class TestProperty1StepDetailOutputFormat:
    """Property 1: Step detail output format correctness.

    For any valid progress data where step_history contains an entry for the
    current module with a valid last_completed_step (integer), and for any
    module that has phases defined in steering-index.yaml, the formatted output
    SHALL contain "Module N: [Name] — Step X of Y completed" where N is the
    current module number, Name is the module name, X is the last_completed_step
    value, and Y is the maximum upper bound of all step_range values.

    Feature: step-level-status-command, Property 1: Step detail output format
    Validates: Requirements 2, 3
    """

    @given(data=st_module_and_step())
    @settings(max_examples=5)
    def test_output_contains_correct_format(
        self, data: tuple[int, int, int]
    ) -> None:
        """Output contains 'Module N: [Name] — Step X of Y completed'."""
        module, step, total = data

        progress_data = {
            "step_history": {
                str(module): {
                    "last_completed_step": step,
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            }
        }

        # Capture stdout from _show_step_detail
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            status._show_step_detail(module, progress_data, _STEERING_INDEX_PATH)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        module_name = status.MODULE_NAMES[module]
        expected_fragment = (
            f"Module {module}: {module_name} \u2014 "
            f"Step {step} of {total} completed"
        )
        assert expected_fragment in output, (
            f"Expected '{expected_fragment}' in output:\n{output}"
        )


# ---------------------------------------------------------------------------
# Strategies for Property 2
# ---------------------------------------------------------------------------

# Integer step values (1-99)
_st_int_step = st.integers(min_value=1, max_value=99)

# Dotted sub-step strings like "5.3", "12.1"
_st_dotted_step = st.builds(
    lambda major, minor: f"{major}.{minor}",
    st.integers(min_value=1, max_value=30),
    st.integers(min_value=1, max_value=9),
)

# Lettered sub-step strings like "7a", "3b"
_st_lettered_step = st.builds(
    lambda num, letter: f"{num}{letter}",
    st.integers(min_value=1, max_value=30),
    st.sampled_from("abcdefgh"),
)

# Any valid current_step value (int, dotted, lettered)
_st_current_step = st.one_of(_st_int_step, _st_dotted_step, _st_lettered_step)

# current_step including None (for "Between steps" case)
_st_current_step_or_none = st.one_of(
    st.none(),
    _st_current_step,
)

# Valid ISO 8601 timestamps
_st_iso_timestamp = st.builds(
    lambda y, mo, d, h, mi, s: f"{y:04d}-{mo:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}Z",
    st.integers(min_value=2020, max_value=2030),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28),
    st.integers(min_value=0, max_value=23),
    st.integers(min_value=0, max_value=59),
    st.integers(min_value=0, max_value=59),
)


# ---------------------------------------------------------------------------
# Property 2: Active step and timestamp display
# ---------------------------------------------------------------------------


class TestProperty2ActiveStepAndTimestamp:
    """Property 2: Active step and timestamp display.

    For any valid current_step value (integer, dotted sub-step string, or
    lettered sub-step string) and for any valid ISO 8601 updated_at timestamp
    in the step history entry, the step detail output SHALL display the active
    step value and the timestamp. When current_step is null, the output SHALL
    display "Between steps" instead.

    Feature: step-level-status-command, Property 2: Active step and timestamp
    Validates: Requirements 4, 5, 6
    """

    @given(
        current_step=_st_current_step,
        timestamp=_st_iso_timestamp,
    )
    @settings(max_examples=5)
    def test_active_step_displayed_when_set(
        self, current_step: int | str, timestamp: str
    ) -> None:
        """When current_step is set, output contains 'Active step: Step {value}'."""
        current_module = 5
        progress_data = {
            "current_module": current_module,
            "current_step": current_step,
            "step_history": {
                "5": {
                    "last_completed_step": 8,
                    "updated_at": timestamp,
                }
            },
        }

        buf = StringIO()
        with _redirect_stdout(buf):
            status._show_step_detail(
                current_module, progress_data, _STEERING_INDEX_PATH
            )

        output = buf.getvalue()
        assert f"Active step: Step {current_step}" in output, (
            f"Expected 'Active step: Step {current_step}' in output:\n{output}"
        )

    @given(timestamp=_st_iso_timestamp)
    @settings(max_examples=5)
    def test_between_steps_when_current_step_null(self, timestamp: str) -> None:
        """When current_step is None (null), output contains 'Between steps'."""
        current_module = 5
        progress_data = {
            "current_module": current_module,
            "current_step": None,
            "step_history": {
                "5": {
                    "last_completed_step": 8,
                    "updated_at": timestamp,
                }
            },
        }

        buf = StringIO()
        with _redirect_stdout(buf):
            status._show_step_detail(
                current_module, progress_data, _STEERING_INDEX_PATH
            )

        output = buf.getvalue()
        assert "Active step: Between steps" in output, (
            f"Expected 'Active step: Between steps' in output:\n{output}"
        )

    @given(
        current_step=_st_current_step_or_none,
        timestamp=_st_iso_timestamp,
    )
    @settings(max_examples=5)
    def test_timestamp_displayed(
        self, current_step: int | str | None, timestamp: str
    ) -> None:
        """The updated_at timestamp is always displayed in the output."""
        current_module = 5
        progress_data = {
            "current_module": current_module,
            "current_step": current_step,
            "step_history": {
                "5": {
                    "last_completed_step": 8,
                    "updated_at": timestamp,
                }
            },
        }

        buf = StringIO()
        with _redirect_stdout(buf):
            status._show_step_detail(
                current_module, progress_data, _STEERING_INDEX_PATH
            )

        output = buf.getvalue()
        assert f"Last updated: {timestamp}" in output, (
            f"Expected 'Last updated: {timestamp}' in output:\n{output}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import contextlib


@contextlib.contextmanager
def _redirect_stdout(buf: StringIO):
    """Context manager to redirect stdout to a StringIO buffer."""
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        yield buf
    finally:
        sys.stdout = old_stdout


# ---------------------------------------------------------------------------
# Unit Tests for --step flag (Task 4.1)
# Validates: Requirements 10
# ---------------------------------------------------------------------------

import json
import importlib


def _write_progress(tmp_path, data):
    """Write a progress JSON file under tmp_path/config/."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "bootcamp_progress.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def _write_steering_index(tmp_path, content: str):
    """Write a steering-index.yaml file under tmp_path/steering/."""
    steering_dir = tmp_path / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / "steering-index.yaml").write_text(content, encoding="utf-8")


_SAMPLE_STEERING_INDEX = """\
modules:
  5:
    root: module-05-data-quality-mapping.md
    phases:
      phase1-quality-assessment:
        file: module-05-phase1-quality-assessment.md
        step_range: [1, 7]
      phase2-data-mapping:
        file: module-05-phase2-data-mapping.md
        step_range: [8, 20]
      phase3-test-load-validate:
        file: module-05-phase3-test-load-validate.md
        step_range: [21, 26]
  4: module-04-data-collection.md
"""


def _capture_step_detail(current_module, progress_data, steering_index_path):
    """Call _show_step_detail and capture its stdout output."""
    captured = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        status._show_step_detail(current_module, progress_data, steering_index_path)
    finally:
        sys.stdout = old_stdout
    return captured.getvalue()


def _capture_status_main_with_step(tmp_path, monkeypatch, argv=None):
    """Run status.py main() with --step flag and capture stdout."""
    importlib.reload(status)

    # Patch __file__ so Path(__file__).resolve().parent.parent == tmp_path
    fake_script = str(tmp_path / "scripts" / "status.py")
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(status, "__file__", fake_script)
    monkeypatch.setattr(status, "USE_COLOR", False)

    if argv is None:
        argv = ["status.py", "--step"]
    monkeypatch.setattr(sys, "argv", argv)

    buf = StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    status.main()
    return buf.getvalue()


class TestStepFlagArgparse:
    """Test that --step flag is accepted by argparse."""

    def test_step_flag_accepted(self, tmp_path, monkeypatch):
        """The --step flag is accepted without error."""
        _write_progress(tmp_path, {
            "modules_completed": [1, 2],
            "current_module": 3,
            "current_step": 2,
            "step_history": {
                "3": {"last_completed_step": 2, "updated_at": "2026-05-12T09:15:00Z"}
            },
            "data_sources": [],
            "database_type": "sqlite",
        })
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)

        output = _capture_status_main_with_step(tmp_path, monkeypatch)
        # Should not raise; output should contain something
        assert "Current Module:" in output


class TestNoProgressFile:
    """Test: No progress file → step section skipped."""

    def test_no_progress_file_skips_step_detail(self, tmp_path, monkeypatch):
        """When no progress file exists, step detail section is not shown."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)

        output = _capture_status_main_with_step(tmp_path, monkeypatch)
        assert "Step Detail:" not in output


class TestEmptyStepHistory:
    """Test: Empty step_history → 'Not started'."""

    def test_empty_step_history_shows_not_started(self, tmp_path):
        """When step_history has no entry for current module, shows 'Not started'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "current_module": 5,
            "step_history": {},
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Not started" in output
        assert "Module 5:" in output


class TestValidStepHistory:
    """Test: Valid step_history → correct format output."""

    def test_valid_step_history_format(self, tmp_path):
        """Shows 'Module N: [Name] — Step X of Y completed'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "step_history": {
                "5": {"last_completed_step": 8, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Module 5: Data Quality & Mapping \u2014 Step 8 of 26 completed" in output


class TestCurrentStepInteger:
    """Test: current_step integer → 'Active step: Step N'."""

    def test_current_step_integer(self, tmp_path):
        """Integer current_step displays 'Active step: Step N'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "current_step": 9,
            "step_history": {
                "5": {"last_completed_step": 8, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Active step: Step 9" in output


class TestCurrentStepSubStep:
    """Test: current_step sub-step '5.3' → 'Active step: Step 5.3'."""

    def test_current_step_sub_step(self, tmp_path):
        """Sub-step string current_step displays 'Active step: Step 5.3'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "current_step": "5.3",
            "step_history": {
                "5": {"last_completed_step": 5, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Active step: Step 5.3" in output


class TestCurrentStepNull:
    """Test: current_step null → 'Between steps'."""

    def test_current_step_null_shows_between_steps(self, tmp_path):
        """Null current_step displays 'Active step: Between steps'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "current_step": None,
            "step_history": {
                "5": {"last_completed_step": 8, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Active step: Between steps" in output


class TestModuleCompleted:
    """Test: Module completed → step detail still shows last step."""

    def test_completed_module_shows_last_step(self, tmp_path):
        """Even when module is completed, step detail shows last completed step."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "modules_completed": [1, 2, 3, 4, 5],
            "current_module": 5,
            "step_history": {
                "5": {"last_completed_step": 26, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Step 26 of 26 completed" in output


class TestModuleWithoutPhases:
    """Test: Module without phases → 'Step X completed' (no total)."""

    def test_module_without_phases_no_total(self, tmp_path):
        """Module without phases shows 'Step X completed' without 'of Y'."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "step_history": {
                "4": {"last_completed_step": 3, "updated_at": "2026-05-12T09:15:00Z"}
            }
        }

        output = _capture_step_detail(4, progress_data, steering_path)
        assert "Step 3 completed" in output
        assert "of" not in output.split("Step 3 completed")[0].split("Step 3")[-1]
        # More direct check: "of" should not appear between "Step 3" and "completed"
        assert "Module 4: Data Collection \u2014 Step 3 completed" in output


class TestTimestampDisplayed:
    """Test: Timestamp displayed from updated_at."""

    def test_timestamp_displayed(self, tmp_path):
        """The updated_at timestamp is shown in the output."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "step_history": {
                "5": {
                    "last_completed_step": 8,
                    "updated_at": "2026-05-12T09:15:00Z",
                }
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Last updated: 2026-05-12T09:15:00Z" in output

    def test_missing_timestamp_omitted(self, tmp_path):
        """When updated_at is missing, timestamp line is omitted."""
        _write_steering_index(tmp_path, _SAMPLE_STEERING_INDEX)
        steering_path = tmp_path / "steering" / "steering-index.yaml"

        progress_data = {
            "step_history": {
                "5": {"last_completed_step": 8}
            }
        }

        output = _capture_step_detail(5, progress_data, steering_path)
        assert "Last updated:" not in output
