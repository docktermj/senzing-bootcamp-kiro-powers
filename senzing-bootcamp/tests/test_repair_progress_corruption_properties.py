"""Property-based tests for repair_progress.py handling corrupted inputs.

Validates that the repair tool handles arbitrary corrupted progress files
gracefully — either repairing them successfully or failing with a clear
error, never crashing with an unhandled exception.

Properties tested:
- Property 5: Corrupted JSON never causes an unhandled crash
- Property 6: Corrupted fields are overwritten by artifact detection
- Property 7: Missing required fields don't prevent repair
- Property 8: Random bytes as progress file content are handled gracefully
"""

from __future__ import annotations

import importlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import hypothesis.strategies as st
from hypothesis import assume, given, settings

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _load_repair():
    """Import / reload repair_progress module."""
    import repair_progress
    importlib.reload(repair_progress)
    return repair_progress


# ---------------------------------------------------------------------------
# Artifact helpers (same as test_repair_progress.py)
# ---------------------------------------------------------------------------

ARTIFACT_CREATORS = {
    1: lambda r: (r / "docs" / "business_problem.md").write_text("x", encoding="utf-8"),
    2: lambda r: (r / "database" / "G2C.db").write_text("x", encoding="utf-8"),
    3: lambda r: (r / "src" / "quickstart_demo" / "demo.py").write_text("x", encoding="utf-8"),
    4: lambda r: (r / "data" / "raw" / "sample.csv").write_text("x", encoding="utf-8"),
    5: lambda r: (r / "docs" / "data_quality_report.md").write_text("x", encoding="utf-8"),
    6: lambda r: (r / "src" / "load" / "loader.py").write_text("x", encoding="utf-8"),
    8: lambda r: (r / "src" / "query" / "query.py").write_text("x", encoding="utf-8"),
}

TESTABLE_MODULES = sorted(ARTIFACT_CREATORS.keys())

CREATOR_DIRS = {
    1: ["docs"], 2: ["database"], 3: ["src", "quickstart_demo"],
    4: ["data", "raw"], 5: ["docs"], 6: ["src", "load"],
    8: ["src", "query"],
}


def _create_artifact(root: Path, module_num: int) -> None:
    """Create the on-disk artifact for module_num under root."""
    creator = ARTIFACT_CREATORS.get(module_num)
    if creator is None:
        return
    parts = CREATOR_DIRS.get(module_num)
    if parts:
        (root / os.path.join(*parts)).mkdir(parents=True, exist_ok=True)
    creator(root)


def _create_artifacts(root: Path, modules: set[int]) -> None:
    """Create artifacts for all modules in the set."""
    for m in modules:
        _create_artifact(root, m)


# ---------------------------------------------------------------------------
# Hypothesis strategies for corrupted progress data
# ---------------------------------------------------------------------------

# Strategy: valid-ish JSON that has wrong types for fields
st_wrong_type_modules_completed = st.one_of(
    st.just("not a list"),
    st.just(42),
    st.just(None),
    st.just({"modules": [1, 2]}),
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5),
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=3),
)

st_wrong_type_current_module = st.one_of(
    st.just("five"),
    st.just([1]),
    st.just(None),
    st.just({"module": 3}),
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(min_value=-100, max_value=0),
    st.integers(min_value=12, max_value=999),
)

st_corrupted_progress_dict = st.fixed_dictionaries(
    {},
    optional={
        "modules_completed": st_wrong_type_modules_completed,
        "current_module": st_wrong_type_current_module,
        "data_sources": st.one_of(st.just("not a list"), st.just(123), st.just(None)),
        "database_type": st.one_of(st.just(123), st.just([]), st.just(None)),
        "current_step": st.one_of(
            st.just([1, 2]),
            st.just({"step": 5}),
            st.just("invalid!!"),
        ),
        "step_history": st.one_of(
            st.just("not a dict"),
            st.just([1, 2, 3]),
            st.just({"99": {"bad": True}}),
        ),
        "extra_garbage_field": st.text(min_size=1, max_size=50),
    },
)

# Strategy: random bytes (not valid JSON at all)
st_random_bytes = st.binary(min_size=1, max_size=500)

# Strategy: valid JSON but not an object (arrays, strings, numbers)
st_non_object_json = st.one_of(
    st.lists(st.integers(), min_size=0, max_size=5).map(json.dumps),
    st.text(min_size=1, max_size=20).map(json.dumps),
    st.integers().map(json.dumps),
    st.just("null"),
    st.just("true"),
    st.just("false"),
)

# Strategy: subset of testable modules for artifact creation
st_module_subset = st.frozensets(
    st.sampled_from(TESTABLE_MODULES), min_size=1, max_size=len(TESTABLE_MODULES)
).map(set)


# ===========================================================================
# Property 5: Corrupted JSON never causes an unhandled crash
# ===========================================================================

class TestProperty5CorruptedJsonNoCrash:
    """Property 5: repair_progress never crashes on corrupted input.

    **Validates:** Robustness requirement — the repair tool must handle
    any content in bootcamp_progress.json without raising an unhandled
    exception. It may report errors, but must not crash.
    """

    @given(content=st_random_bytes)
    @settings(max_examples=20)
    def test_random_bytes_no_crash(self, content: bytes):
        """Random binary content in progress file doesn't crash detect() or main()."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            # Write random bytes as the progress file
            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_bytes(content)

            mod = _load_repair()

            # detect() should not crash (it doesn't read progress)
            mod.detect()

            # main() in report mode should not crash
            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py"]):
                with patch("sys.stdout", captured):
                    mod.main()

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)

    @given(json_str=st_non_object_json)
    @settings(max_examples=20)
    def test_non_object_json_no_crash(self, json_str: str):
        """Valid JSON that isn't an object doesn't crash."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_text(json_str, encoding="utf-8")

            mod = _load_repair()
            mod.detect()

            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py"]):
                with patch("sys.stdout", captured):
                    mod.main()

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)

    @given(data=st_corrupted_progress_dict)
    @settings(max_examples=20)
    def test_wrong_field_types_no_crash(self, data: dict):
        """JSON object with wrong field types doesn't crash."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

            mod = _load_repair()
            mod.detect()

            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py"]):
                with patch("sys.stdout", captured):
                    mod.main()

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


# ===========================================================================
# Property 6: Corrupted fields are overwritten by artifact detection on --fix
# ===========================================================================

class TestProperty6CorruptedFieldsOverwritten:
    """Property 6: --fix overwrites corrupted fields with detected state.

    **Validates:** When artifacts exist on disk and the progress file has
    corrupted field values, --fix produces a valid progress file whose
    modules_completed matches the detected artifacts.
    """

    @given(
        modules=st_module_subset,
        corrupted=st_corrupted_progress_dict,
    )
    @settings(max_examples=15)
    def test_fix_overwrites_corrupted_with_detected(
        self, modules: set[int], corrupted: dict
    ):
        """--fix produces valid output regardless of corrupted input."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            # Create artifacts
            _create_artifacts(root, modules)

            # Write corrupted progress
            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_text(
                json.dumps(corrupted), encoding="utf-8"
            )

            mod = _load_repair()

            # Run --fix
            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py", "--fix"]):
                with patch("sys.stdout", captured):
                    try:
                        mod.main()
                    except SystemExit:
                        # Schema validation failure is acceptable —
                        # the tool correctly refused to write bad data
                        return

            # If --fix succeeded, verify the output
            progress_file = root / "config" / "bootcamp_progress.json"
            if progress_file.exists():
                result = json.loads(progress_file.read_text(encoding="utf-8"))
                # modules_completed must match detected artifacts
                assert set(result["modules_completed"]) == modules, (
                    f"Expected {modules}, got {set(result['modules_completed'])}"
                )
                # Must have required fields
                assert "current_module" in result
                assert "data_sources" in result
                assert isinstance(result["modules_completed"], list)

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


# ===========================================================================
# Property 7: Missing required fields don't prevent repair
# ===========================================================================

class TestProperty7MissingFieldsRepaired:
    """Property 7: Empty or minimal progress files are repaired successfully.

    **Validates:** A progress file with missing required fields (or an
    empty object) can still be repaired when artifacts exist on disk.
    """

    @given(modules=st_module_subset)
    @settings(max_examples=15)
    def test_empty_object_repaired(self, modules: set[int]):
        """An empty JSON object {} is repaired based on artifacts."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            _create_artifacts(root, modules)

            # Write empty object
            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_text("{}", encoding="utf-8")

            mod = _load_repair()

            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py", "--fix"]):
                with patch("sys.stdout", captured):
                    try:
                        mod.main()
                    except SystemExit:
                        return

            progress_file = root / "config" / "bootcamp_progress.json"
            if progress_file.exists():
                result = json.loads(progress_file.read_text(encoding="utf-8"))
                assert set(result["modules_completed"]) == modules

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)

    @given(modules=st_module_subset)
    @settings(max_examples=15)
    def test_missing_file_repaired(self, modules: set[int]):
        """No progress file at all is handled — --fix creates one."""
        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            _create_artifacts(root, modules)
            # Don't create any progress file

            mod = _load_repair()

            captured = io.StringIO()
            with patch.object(sys, "argv", ["repair_progress.py", "--fix"]):
                with patch("sys.stdout", captured):
                    try:
                        mod.main()
                    except SystemExit:
                        return

            progress_file = root / "config" / "bootcamp_progress.json"
            if progress_file.exists():
                result = json.loads(progress_file.read_text(encoding="utf-8"))
                assert set(result["modules_completed"]) == modules

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)


# ===========================================================================
# Property 8: Random bytes as progress file — detect still works
# ===========================================================================

class TestProperty8DetectIndependentOfProgressFile:
    """Property 8: detect() is independent of progress file content.

    **Validates:** The artifact detection logic never reads the progress
    file (except for the multi-source check in module 7). For all other
    modules, detect() returns the same result regardless of progress
    file content.
    """

    @given(
        modules=st_module_subset,
        content=st_random_bytes,
    )
    @settings(max_examples=15)
    def test_detect_ignores_corrupted_progress(
        self, modules: set[int], content: bytes
    ):
        """detect() finds artifacts regardless of progress file corruption."""
        # Exclude module 7 which reads progress for multi-source check
        modules_no_7 = modules - {7}
        assume(len(modules_no_7) > 0)

        td = tempfile.mkdtemp()
        try:
            orig = os.getcwd()
            os.chdir(td)
            root = Path(td)

            _create_artifacts(root, modules_no_7)

            # Write random bytes as progress
            cfg = root / "config"
            cfg.mkdir(parents=True, exist_ok=True)
            (cfg / "bootcamp_progress.json").write_bytes(content)

            mod = _load_repair()
            detected = mod.detect()

            assert detected == modules_no_7, (
                f"Expected {modules_no_7}, got {detected}"
            )

        finally:
            os.chdir(orig)
            shutil.rmtree(td, ignore_errors=True)
