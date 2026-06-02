"""Bug condition exploration tests for steering-index phase token-count drift.

Property 1 (Bug Condition) — Fix Checking: phase ``token_count`` values in
``steering-index.yaml`` must be reconciled and validated against the measured
token count of each phase's ``file``.

These tests are authored to FAIL on the UNFIXED ``measure_steering.py`` — the
failures CONFIRM the bug exists:

* ``measure_steering.py --check`` validates only the ``file_metadata`` block and
  never inspects the ``phases`` map, so phase drift exits 0 (silent).
* Update mode rebuilds only ``file_metadata`` + ``budget``; the ``phases`` entries
  live in the preserved region above ``file_metadata`` and are copied through
  untouched.
* There is no ``check_phase_counts`` / ``rewrite_phase_counts`` helper, and phase
  ``size_category`` is never recomputed from a corrected count.

After the fix lands these same tests SHALL PASS, validating the expected behavior.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Stdlib + Hypothesis only (no PyYAML). No MCP server URL is referenced.
"""

from __future__ import annotations

import importlib
import io
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from hypothesis import assume, given, settings
import hypothesis.strategies as st


# ---------------------------------------------------------------------------
# Import target script via the documented sys.path pattern
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

_TOLERANCE = 0.10


def _load_measure_steering():
    """Import (or reload) the measure_steering module under test."""
    import measure_steering

    importlib.reload(measure_steering)
    return measure_steering


# ---------------------------------------------------------------------------
# Phase-entry model + local minimal YAML parser (no PyYAML)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhaseEntry:
    """A ``phases.*`` entry: its 1:1 file plus stored token_count/size_category."""

    file: str
    token_count: int
    size_category: str | None


_FILE_RE = re.compile(r"^(\s+)file:\s+([\w.-]+\.md)\s*$")
_TC_RE = re.compile(r"^\s+token_count:\s*(\d+)\s*$")
_SC_RE = re.compile(r"^\s+size_category:\s*(\w+)\s*$")


def _parse_phase_entries_text(content: str) -> list[PhaseEntry]:
    """Parse phase entries (``file`` + ``token_count``) from YAML text.

    Walks the region above ``file_metadata``; each ``file:`` line begins a phase
    block, and the immediately following ``token_count:`` / ``size_category:``
    lines belong to it. ``root:`` and ``file_metadata`` entries have no ``file:``
    line and are excluded. Mirrors the design's ``_parse_phase_entries``.

    Args:
        content: Raw YAML text of a steering-index.yaml.

    Returns:
        List of PhaseEntry records in document order.
    """
    lines = content.splitlines()
    fm_idx = next(
        (i for i, line in enumerate(lines) if line.rstrip() == "file_metadata:"),
        len(lines),
    )
    region = lines[:fm_idx]

    entries: list[PhaseEntry] = []
    for i, line in enumerate(region):
        file_match = _FILE_RE.match(line)
        if not file_match:
            continue
        token_count: int | None = None
        size_category: str | None = None
        for j in range(i + 1, len(region)):
            if _FILE_RE.match(region[j]):
                break
            if token_count is None:
                tc_match = _TC_RE.match(region[j])
                if tc_match:
                    token_count = int(tc_match.group(1))
            if size_category is None:
                sc_match = _SC_RE.match(region[j])
                if sc_match:
                    size_category = sc_match.group(1)
            if token_count is not None and size_category is not None:
                break
        if token_count is not None:
            entries.append(
                PhaseEntry(
                    file=file_match.group(2),
                    token_count=token_count,
                    size_category=size_category,
                )
            )
    return entries


_LIVE_PHASE_ENTRIES = _parse_phase_entries_text(
    _INDEX_PATH.read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# Bug-condition helpers (mirror isBugCondition from design)
# ---------------------------------------------------------------------------


def is_phase_bug(stored: int, measured: int) -> bool:
    """Return True when stored drifts > 10% from measured (the bug condition)."""
    return abs(stored - measured) / max(measured, 1) > _TOLERANCE


def measured_tokens(file: str) -> int:
    """Measured token count of a steering file, via calculate_token_count."""
    mod = _load_measure_steering()
    return mod.calculate_token_count(_STEERING_DIR / file)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_phase_entry() -> st.SearchStrategy[PhaseEntry]:
    """Sample a phase entry from the real steering-index.yaml."""
    return st.sampled_from(_LIVE_PHASE_ENTRIES)


def st_drift() -> st.SearchStrategy[tuple[int, float]]:
    """(measured, factor) pairs straddling the 10% and 500/2000 boundaries."""
    measured = st.one_of(
        st.integers(min_value=1, max_value=30),
        st.integers(min_value=460, max_value=540),
        st.integers(min_value=1950, max_value=2050),
        st.integers(min_value=2900, max_value=3400),
    )
    factor = st.floats(
        min_value=0.0, max_value=3.0, allow_nan=False, allow_infinity=False
    )
    return st.tuples(measured, factor)


# ---------------------------------------------------------------------------
# CLI / fixture helpers
# ---------------------------------------------------------------------------


def _run_cli(argv: list[str]) -> tuple[int, str]:
    """Run measure_steering.main() with argv, returning (exit_code, stdout)."""
    mod = _load_measure_steering()
    buf = io.StringIO()
    full_argv = ["measure_steering.py", *argv]
    with patch.object(sys, "argv", full_argv):
        with redirect_stdout(buf):
            try:
                mod.main()
            except SystemExit as exc:
                code = exc.code
                return (int(code) if code is not None else 0, buf.getvalue())
    return (0, buf.getvalue())


def _build_synthetic_index(
    steering_dir: Path,
    index_path: Path,
    fname: str,
    content: str,
    phase_count: int,
    phase_cat: str,
    fm_count: int,
    fm_cat: str,
) -> None:
    """Write a temp steering file + index: file_metadata in sync, phase drifted."""
    (steering_dir / fname).write_text(content, encoding="utf-8")
    index_text = (
        "modules:\n"
        "  1:\n"
        f"    root: {fname}\n"
        "    phases:\n"
        "      phase1:\n"
        f"        file: {fname}\n"
        f"        token_count: {phase_count}\n"
        f"        size_category: {phase_cat}\n"
        "        step_range: [1, 9]\n"
        "\n"
        "file_metadata:\n"
        f"  {fname}:\n"
        f"    token_count: {fm_count}\n"
        f"    size_category: {fm_cat}\n"
        "\n"
        "budget:\n"
        f"  total_tokens: {fm_count}\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n"
        "  critical_threshold_pct: 80\n"
    )
    index_path.write_text(index_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Property 1 — Bug Condition: phase token counts reconciled and validated
# ---------------------------------------------------------------------------


class TestBugConditionPhaseTokenCountSync:
    """Property 1: Phase Token Counts Reconciled and Validated.

    Authored to FAIL on unfixed code — failure confirms phase drift is neither
    detected by ``--check`` nor repaired by update mode.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
    """

    @staticmethod
    def _assert_drift(stored: int, measured: int) -> None:
        """Sanity guard: the synthetic case is genuinely a bug condition."""
        assert is_phase_bug(stored, measured)

    def test_check_flags_drifted_phase_synthetic(self) -> None:
        """Test 1: --check must flag a phase whose count is ~2x the measured.

        FAILS on unfixed code: ``--check`` validates only file_metadata, so it
        exits 0 and prints the success message despite the drifted phase, and
        ``check_phase_counts`` does not exist.

        **Validates: Requirements 2.2, 2.6**
        """
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 2000  # measured = round(2000 / 4) = 500
            (steering_dir / fname).write_text(content, encoding="utf-8")
            measured = mod.calculate_token_count(steering_dir / fname)
            phase_count = 2 * measured  # ~100% drift, far beyond 10%
            self._assert_drift(phase_count, measured)

            _build_synthetic_index(
                steering_dir,
                index_path,
                fname=fname,
                content=content,
                phase_count=phase_count,
                phase_cat=mod.classify_size(phase_count),
                fm_count=measured,
                fm_cat=mod.classify_size(measured),
            )

            exit_code, out = _run_cli(
                [
                    "--check",
                    "--steering-dir",
                    str(steering_dir),
                    "--index-path",
                    str(index_path),
                ]
            )

            check_phase = getattr(mod, "check_phase_counts", None)
            assert check_phase is not None, (
                "check_phase_counts is not implemented — --check cannot validate "
                "the phases map (bug present). CLI output was: " + repr(out)
            )
            mismatches = check_phase(index_path, steering_dir)
            assert any(m[0] == fname for m in mismatches), (
                f"check_phase_counts did not report drifted phase {fname} "
                f"(stored={phase_count} vs measured={measured})"
            )
            assert exit_code != 0, (
                f"--check exited {exit_code} (output: {out!r}) despite phase "
                f"{fname} reading {phase_count} vs measured {measured}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

    @given(drift=st_drift())
    @settings(max_examples=20, deadline=None)
    def test_check_flags_drifted_phase_pbt(self, drift: tuple[int, float]) -> None:
        """PBT (st_drift): for any bug-inducing (measured, factor), --check flags it.

        FAILS on unfixed code for every generated bug case: phase validation does
        not exist, so the CLI exits 0.

        **Validates: Requirements 2.2, 2.6**
        """
        measured, factor = drift
        stored = round(measured * factor)
        assume(is_phase_bug(stored, measured))

        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * (4 * measured)  # round(len/4) == measured

            _build_synthetic_index(
                steering_dir,
                index_path,
                fname=fname,
                content=content,
                phase_count=stored,
                phase_cat=mod.classify_size(stored),
                fm_count=measured,
                fm_cat=mod.classify_size(measured),
            )

            exit_code, out = _run_cli(
                [
                    "--check",
                    "--steering-dir",
                    str(steering_dir),
                    "--index-path",
                    str(index_path),
                ]
            )

            check_phase = getattr(mod, "check_phase_counts", None)
            assert check_phase is not None, (
                "check_phase_counts is not implemented — phase drift is invisible "
                "to --check (bug present)."
            )
            assert exit_code != 0, (
                f"--check exited {exit_code} despite phase drift "
                f"(stored={stored} vs measured={measured}); output: {out!r}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

    @given(entry=st_phase_entry())
    @settings(max_examples=20, deadline=None)
    def test_live_index_phase_within_tolerance(self, entry: PhaseEntry) -> None:
        """Test 2 (PBT over real index): every phase is within 10% of its file.

        FAILS on unfixed code for the drifted phases (e.g. module-01 phase1,
        module-05 phase2, module-06 phase1, module-07 phase1).

        **Validates: Requirements 2.1, 2.4**
        """
        measured = measured_tokens(entry.file)
        drift = abs(entry.token_count - measured) / max(measured, 1)
        assert drift <= _TOLERANCE, (
            f"phase file {entry.file}: stored token_count={entry.token_count} "
            f"vs measured={measured} (drift {drift:.1%} > 10%)"
        )

    def test_module5_size_category_reclassified(self) -> None:
        """Test 3: module-05 phase2 should reclassify medium -> large at measured.

        FAILS on unfixed code: the stored phase ``size_category`` stays ``medium``
        while the measured count (~3128) is over the 2000 medium/large boundary.

        **Validates: Requirements 2.5**
        """
        mod = _load_measure_steering()
        fname = "module-05-phase2-data-mapping.md"
        entry = next((e for e in _LIVE_PHASE_ENTRIES if e.file == fname), None)
        assert entry is not None, f"phase entry for {fname} not found in live index"

        measured = measured_tokens(fname)
        expected_cat = mod.classify_size(measured)
        assert expected_cat == "large", (
            f"expected {fname} measured={measured} to classify as large "
            f"(over the 2000 boundary), got {expected_cat}"
        )
        assert entry.size_category == expected_cat, (
            f"{fname}: stored size_category={entry.size_category} is inconsistent "
            f"with measured={measured} -> {expected_cat}"
        )

    def test_update_mode_repairs_drifted_phase(self) -> None:
        """Test 4: update mode must repair a drifted phase's count + category.

        FAILS on unfixed code: update mode rebuilds only file_metadata + budget
        and leaves the ``phases`` entries (in the preserved prefix) untouched.

        **Validates: Requirements 2.1, 2.3, 2.5**
        """
        mod = _load_measure_steering()
        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"

            fname = "synth-phase.md"
            content = "a" * 12000  # measured = 3000 -> large
            (steering_dir / fname).write_text(content, encoding="utf-8")
            measured = mod.calculate_token_count(steering_dir / fname)
            drifted = 1894  # medium, far below measured (37% drift)

            _build_synthetic_index(
                steering_dir,
                index_path,
                fname=fname,
                content=content,
                phase_count=drifted,
                phase_cat=mod.classify_size(drifted),
                fm_count=drifted,
                fm_cat=mod.classify_size(drifted),
            )

            # Run update mode (no --check): scans files, rewrites the index.
            exit_code, _out = _run_cli(
                [
                    "--steering-dir",
                    str(steering_dir),
                    "--index-path",
                    str(index_path),
                ]
            )
            assert exit_code == 0, f"update mode exited non-zero: {exit_code}"

            updated = index_path.read_text(encoding="utf-8")
            entries = _parse_phase_entries_text(updated)
            repaired = next((e for e in entries if e.file == fname), None)
            assert repaired is not None, "phase entry vanished after update"

            assert repaired.token_count == measured, (
                f"update mode left phase {fname} token_count="
                f"{repaired.token_count}, expected reconciled measured={measured}"
            )
            assert repaired.size_category == mod.classify_size(measured), (
                f"update mode left phase {fname} size_category="
                f"{repaired.size_category}, expected "
                f"{mod.classify_size(measured)}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)
