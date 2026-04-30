"""Property-based tests for step-level checkpointing.

Uses hypothesis to verify correctness properties across randomly generated
progress states.
"""

import datetime
import importlib
import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from progress_utils import clear_step, validate_progress_schema, write_checkpoint


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

def _iso8601_timestamps():
    """Strategy producing valid ISO 8601 UTC timestamp strings."""
    return st.datetimes(
        min_value=datetime.datetime(2020, 1, 1),
        max_value=datetime.datetime(2030, 12, 31),
    ).map(lambda dt: dt.replace(tzinfo=datetime.timezone.utc).isoformat())


def _step_history_entries():
    """Strategy producing a valid step_history entry dict."""
    return st.fixed_dictionaries({
        "last_completed_step": st.integers(min_value=1, max_value=20),
        "updated_at": _iso8601_timestamps(),
    })


def _step_history():
    """Strategy producing a valid step_history object (string keys 1-12)."""
    keys = st.sampled_from([str(i) for i in range(1, 13)])
    return st.dictionaries(keys, _step_history_entries(), min_size=0, max_size=6)


def _valid_progress_states():
    """Strategy producing fully valid progress dicts with step fields."""
    return st.fixed_dictionaries({
        "modules_completed": st.lists(
            st.integers(min_value=1, max_value=12), unique=True, max_size=11,
        ).map(sorted),
        "current_module": st.integers(min_value=1, max_value=12),
        "current_step": st.one_of(st.none(), st.integers(min_value=1, max_value=20)),
        "step_history": _step_history(),
        "data_sources": st.just([]),
        "database_type": st.sampled_from(["sqlite", "postgresql"]),
    })


def _legacy_progress_states():
    """Strategy producing legacy progress dicts WITHOUT step fields."""
    return st.fixed_dictionaries({
        "modules_completed": st.lists(
            st.integers(min_value=1, max_value=12), unique=True, max_size=11,
        ).map(sorted),
        "current_module": st.integers(min_value=1, max_value=12),
        "data_sources": st.just([]),
        "database_type": st.sampled_from(["sqlite", "postgresql"]),
    })


# ---------------------------------------------------------------------------
# Property 1: Progress file schema conformance
# ---------------------------------------------------------------------------


class TestProperty1SchemaConformance:
    """Feature: step-level-checkpointing, Property 1: Progress file schema conformance

    For any valid progress state, serializing to JSON and validating against
    the extended schema SHALL produce no errors, and all step_history keys
    SHALL be string representations of integers 1-12.

    **Validates: Requirements 1.2, 1.5**
    """

    @given(data=_valid_progress_states())
    @settings(max_examples=100)
    def test_valid_progress_passes_schema(self, data):
        """Feature: step-level-checkpointing, Property 1: Progress file schema conformance"""
        # Round-trip through JSON to match real-world serialization
        serialized = json.loads(json.dumps(data))
        errors = validate_progress_schema(serialized)
        assert errors == [], f"Unexpected validation errors: {errors}"

        # Verify step_history keys are valid string ints 1-12
        for key in serialized.get("step_history", {}):
            key_int = int(key)
            assert 1 <= key_int <= 12, f"step_history key {key} out of range"

        # Verify each entry has required fields with correct types
        for key, entry in serialized.get("step_history", {}).items():
            assert isinstance(entry["last_completed_step"], int)
            assert isinstance(entry["updated_at"], str)
            datetime.datetime.fromisoformat(entry["updated_at"])


# ---------------------------------------------------------------------------
# Property 2: Module completion clears current step
# ---------------------------------------------------------------------------


class TestProperty2ModuleCompletionClearsStep:
    """Feature: step-level-checkpointing, Property 2: Module completion clears current step

    For any progress state where a module is completed, current_step SHALL be
    null after clear_step, while step_history is retained.

    **Validates: Requirements 1.4**
    """

    @given(
        module=st.integers(min_value=1, max_value=12),
        step=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_clear_step_nullifies_current_step(self, module, step):
        """Feature: step-level-checkpointing, Property 2: Module completion clears current step"""
        with tempfile.TemporaryDirectory() as td:
            progress_path = str(Path(td) / "progress.json")

            # Write a checkpoint first so there is step data
            write_checkpoint(module_number=module, step_number=step, progress_path=progress_path)

            # Simulate module completion by clearing the step
            clear_step(progress_path=progress_path)

            data = json.loads(Path(progress_path).read_text(encoding="utf-8"))

            # current_step must be null
            assert data["current_step"] is None

            # step_history must be retained
            assert str(module) in data["step_history"]
            assert data["step_history"][str(module)]["last_completed_step"] == step


# ---------------------------------------------------------------------------
# Property 3: Checkpoint write consistency
# ---------------------------------------------------------------------------


class TestProperty3CheckpointWriteConsistency:
    """Feature: step-level-checkpointing, Property 3: Checkpoint write consistency

    For any valid (module, step) pair, write_checkpoint SHALL produce a file
    where current_step equals the step, step_history entry matches, and
    updated_at is a valid ISO 8601 timestamp.

    **Validates: Requirements 4.2**
    """

    @given(
        module=st.integers(min_value=1, max_value=12),
        step=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_checkpoint_write_is_consistent(self, module, step):
        """Feature: step-level-checkpointing, Property 3: Checkpoint write consistency"""
        with tempfile.TemporaryDirectory() as td:
            progress_path = str(Path(td) / "progress.json")
            before = datetime.datetime.now(datetime.timezone.utc)

            write_checkpoint(module_number=module, step_number=step, progress_path=progress_path)

            data = json.loads(Path(progress_path).read_text(encoding="utf-8"))

            # current_step matches written step
            assert data["current_step"] == step

            # step_history entry matches
            entry = data["step_history"][str(module)]
            assert entry["last_completed_step"] == step

            # updated_at is valid ISO 8601 and not earlier than before
            ts = datetime.datetime.fromisoformat(entry["updated_at"])
            assert ts >= before, f"Timestamp {ts} is earlier than {before}"


# ---------------------------------------------------------------------------
# Property 4: Backward compatibility
# ---------------------------------------------------------------------------


class TestProperty4BackwardCompatibility:
    """Feature: step-level-checkpointing, Property 4: Backward compatibility

    For any legacy progress file (without step fields), validate_progress_schema
    SHALL produce no errors.

    **Validates: Requirements 2.3, 2.4, 5.2**
    """

    @given(data=_legacy_progress_states())
    @settings(max_examples=100)
    def test_legacy_progress_passes_validation(self, data):
        """Feature: step-level-checkpointing, Property 4: Backward compatibility"""
        serialized = json.loads(json.dumps(data))

        # Must not contain step fields
        assert "current_step" not in serialized
        assert "step_history" not in serialized

        # Validation must pass with no errors
        errors = validate_progress_schema(serialized)
        assert errors == [], f"Legacy file produced errors: {errors}"


# ---------------------------------------------------------------------------
# Property 5: Step display in status output
# ---------------------------------------------------------------------------


class TestProperty5StepDisplayInStatusOutput:
    """Feature: step-level-checkpointing, Property 5: Step display in status output

    For any progress file where current_step is a positive integer and
    current_module is not in modules_completed, status.py output SHALL
    contain the step number.

    **Validates: Requirements 5.1**
    """

    @given(
        current_module=st.integers(min_value=1, max_value=12),
        current_step=st.integers(min_value=1, max_value=20),
        completed_count=st.integers(min_value=0, max_value=11),
    )
    @settings(max_examples=100)
    def test_status_output_contains_step(
        self, current_module, current_step, completed_count
    ):
        """Feature: step-level-checkpointing, Property 5: Step display in status output"""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)

            # Build completed list that does NOT include current_module
            all_modules = [m for m in range(1, 13) if m != current_module]
            completed = sorted(all_modules[:completed_count])

            # Write progress file
            config_dir = tmp / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "bootcamp_progress.json").write_text(
                json.dumps({
                    "modules_completed": completed,
                    "current_module": current_module,
                    "current_step": current_step,
                    "step_history": {
                        str(current_module): {
                            "last_completed_step": current_step,
                            "updated_at": "2026-05-12T09:15:00+00:00",
                        }
                    },
                    "data_sources": [],
                    "database_type": "sqlite",
                }, indent=2),
                encoding="utf-8",
            )

            # Create fake scripts dir so status.__file__ resolves correctly
            (tmp / "scripts").mkdir(parents=True, exist_ok=True)
            fake_script = str(tmp / "scripts" / "status.py")

            scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)

            import status
            importlib.reload(status)

            buf = StringIO()
            with mock.patch.object(status, "__file__", fake_script), \
                 mock.patch.object(status, "USE_COLOR", False), \
                 mock.patch.object(sys, "argv", ["status.py"]), \
                 mock.patch.object(sys, "stdout", buf):
                status.main()

            output = buf.getvalue()

            # The output must contain the step number
            assert f"Step {current_step}" in output, (
                f"Expected 'Step {current_step}' in status output for "
                f"module={current_module}, step={current_step}"
            )
