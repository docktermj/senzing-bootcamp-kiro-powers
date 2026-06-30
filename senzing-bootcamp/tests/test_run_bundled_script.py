"""Tests for the bundled-script guarded runner (generic-step degradation).

``run_bundled_script.py`` implements the generic-step degradation pattern from
the missing-bundled-scripts design (fix part 3): an existence check before
shelling out to a bundled ``senzing-bootcamp/scripts/<name>.py``, a one-shot
``preflight.py --fix`` self-repair when the script is absent, and an inline
no-op fallback (exit 0, no file-not-found error) when it still cannot be found.
When the script is present it executes unchanged and its exit code is preserved.

Feature: missing-bundled-scripts

**Validates: Requirements 2.3, 3.2**
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Import the script under test via the documented sys.path pattern.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import run_bundled_script as rbs  # noqa: E402

_FILE_NOT_FOUND_MARKERS: tuple[str, ...] = (
    "No such file or directory",
    "can't open file",
    "cannot find the file",
)


def _write_exit_script(scripts_dir: Path, name: str, exit_code: int) -> None:
    """Write a tiny bundled script that exits with *exit_code*.

    Args:
        scripts_dir: Directory to write the script into.
        name: Script filename.
        exit_code: Exit code the script should return.
    """
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / name).write_text(
        "import sys\nsys.exit(" + str(exit_code) + ")\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Existence-guard / no-op fallback (Bug Condition — Req 2.3)
# ---------------------------------------------------------------------------


class TestAbsentScriptDegradesGracefully:
    """A missing bundled script degrades to a no-op, never a file-not-found error.

    **Validates: Requirements 2.3**
    """

    def test_absent_script_no_repair_exits_zero_no_error(
        self, tmp_path: Path, capsys
    ) -> None:
        """Absent script with repair disabled exits 0 with no file-not-found noise."""
        empty_dir = tmp_path / "senzing-bootcamp" / "scripts"
        empty_dir.mkdir(parents=True)

        code = rbs.run_bundled_script(
            "generate_docs_index.py",
            [],
            allow_repair=False,
            scripts_dir=empty_dir,
        )

        captured = capsys.readouterr()
        blob = f"{captured.out}\n{captured.err}"
        assert code == 0, f"expected graceful no-op exit 0, got {code}"
        assert not any(m in blob for m in _FILE_NOT_FOUND_MARKERS), (
            f"no-op fallback must not emit a file-not-found error; output={blob!r}"
        )

    def test_absent_script_quiet_is_silent(self, tmp_path: Path, capsys) -> None:
        """The quiet no-op fallback emits no notice and still exits 0."""
        empty_dir = tmp_path / "scripts"
        empty_dir.mkdir(parents=True)

        code = rbs.run_bundled_script(
            "status.py", ["--steps"], allow_repair=False, quiet=True, scripts_dir=empty_dir
        )

        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == "", f"quiet no-op must be silent; stderr={captured.err!r}"

    def test_script_exists_helper(self, tmp_path: Path) -> None:
        """script_exists reflects the presence of the resolved bundled script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        assert not rbs.script_exists("missing.py", scripts_dir)
        _write_exit_script(scripts_dir, "present.py", 0)
        assert rbs.script_exists("present.py", scripts_dir)


# ---------------------------------------------------------------------------
# Present-script preservation (Req 3.2)
# ---------------------------------------------------------------------------


class TestPresentScriptPreserved:
    """A present bundled script executes unchanged and its exit code propagates.

    **Validates: Requirements 3.2**
    """

    def test_present_script_exit_code_propagates(self, tmp_path: Path) -> None:
        """A present script's exit code is returned verbatim (no degradation)."""
        scripts_dir = tmp_path / "scripts"
        _write_exit_script(scripts_dir, "ok.py", 0)
        _write_exit_script(scripts_dir, "boom.py", 7)

        assert rbs.run_bundled_script("ok.py", [], scripts_dir=scripts_dir) == 0
        assert rbs.run_bundled_script("boom.py", [], scripts_dir=scripts_dir) == 7

    @given(exit_code=st.integers(min_value=0, max_value=125))
    def test_present_script_exit_code_propagates_pbt(self, exit_code: int) -> None:
        """For any exit code, a present script's code is preserved by the wrapper."""
        with tempfile.TemporaryDirectory() as tmp:
            scripts_dir = Path(tmp) / "scripts"
            _write_exit_script(scripts_dir, "code.py", exit_code)
            result = rbs.run_bundled_script(
                "code.py", [], allow_repair=False, scripts_dir=scripts_dir
            )
            assert result == exit_code


# ---------------------------------------------------------------------------
# Self-repair integration (Bug Condition + self-repair — Req 2.3)
# ---------------------------------------------------------------------------


class TestSelfRepairThenRun:
    """A workspace missing the scripts dir is self-repaired, then the script runs.

    **Validates: Requirements 2.3**
    """

    def test_absent_workspace_self_repairs_and_runs(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """With repair enabled, a generic step runs after preflight materializes it."""
        # A throwaway workspace with docs/ but no senzing-bootcamp/scripts/ dir.
        (tmp_path / "docs").mkdir()
        monkeypatch.chdir(tmp_path)

        # Uses the cwd-relative workspace scripts dir (absent) → self-repair via
        # the installed preflight materializes it, then the generic step runs.
        code = rbs.run_bundled_script("generate_docs_index.py", [])

        assert code == 0, f"expected exit 0 after self-repair + run, got {code}"
        assert (
            tmp_path / "senzing-bootcamp" / "scripts" / "generate_docs_index.py"
        ).is_file(), "self-repair should materialize the bundled scripts directory"
