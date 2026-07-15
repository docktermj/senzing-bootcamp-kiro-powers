"""Tests for the deterministic Stop-hook gating and the no-data recap floor.

Feature: guaranteed-recap-pdf.

The ``enforce-critical-artifacts`` hook was converted from an agent-prompt hook
(which relied on the agent choosing to act) to a deterministic ``command`` hook
that runs ``ensure_graduation_artifacts.py --stop-hook`` on every Stop. The
gating that formerly lived in the hook prompt now lives here, in tested Python:

    is_stopping_point       True only when a track-end module (7 or 11) is in
                            ``modules_completed``; never raises.
    --stop-hook gating      defer while ``config/.question_pending`` exists;
                            no-op away from a stopping point; otherwise ensure
                            the artifacts; ALWAYS exit 0 and never raise.
    no-data floor           the recap PDF ("trophy") is produced even when the
                            recap Markdown source is absent/empty, and the floor
                            PDF is idempotent until real recap content appears.

All fixtures use synthetic, PII-free content.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import ensure_graduation_artifacts as ega  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _paths(root: Path) -> ega.ArtifactPaths:
    """Build ``ArtifactPaths`` rooted under ``root`` (absolute paths)."""
    return ega.ArtifactPaths(
        log=str(root / "config" / "session_log.jsonl"),
        recap=str(root / "docs" / "bootcamp_recap.md"),
        transcript=str(root / "docs" / "bootcamp_transcript.md"),
        progress=str(root / "config" / "bootcamp_progress.json"),
        journal=str(root / "docs" / "bootcamp_recap.md"),
        progress_dir=str(root / "docs" / "progress"),
        pdf=str(root / "docs" / "bootcamp_recap.pdf"),
        html=str(root / "docs" / "bootcamp_recap.html"),
    )


def _mkdirs(paths: ega.ArtifactPaths) -> None:
    Path(paths.progress).parent.mkdir(parents=True, exist_ok=True)
    Path(paths.recap).parent.mkdir(parents=True, exist_ok=True)


def _write_progress(paths: ega.ArtifactPaths, modules: list[int]) -> None:
    _mkdirs(paths)
    Path(paths.progress).write_text(
        json.dumps({"modules_completed": modules}), encoding="utf-8"
    )


def _recap_text(modules: list[int]) -> str:
    lines = ["# Senzing Bootcamp Recap", ""]
    for m in modules:
        lines += [
            f"## Module {m}: Topic {m} \u2014 2025-01-10T{9 + m:02d}:00:00Z",
            "",
            "### Information Shared",
            f"- Learned core concept {m} about entity resolution",
            "",
            "### Questions & Responses",
            f"- **Q:** What did module {m} cover?",
            f"  - **R:** Entity resolution fundamentals for module {m}.",
            "",
            "### Actions Taken",
            f"- Completed the module {m} hands-on exercise",
            "",
        ]
    return "\n".join(lines) + "\n"


def _argv(paths: ega.ArtifactPaths, question_flag: str, *extra: str) -> list[str]:
    """Full argv wiring every path override plus an isolated question flag."""
    return [
        "--stop-hook",
        "--question-flag", question_flag,
        "--log", paths.log,
        "--recap", paths.recap,
        "--transcript", paths.transcript,
        "--progress", paths.progress,
        "--progress-dir", paths.progress_dir,
        "--pdf", paths.pdf,
        "--html", paths.html,
        *extra,
    ]


def _missing_flag(root: Path) -> str:
    """Return a path to an isolated, nonexistent question-pending flag."""
    return str(root / "config" / ".no_question_pending")


# ===========================================================================
# is_stopping_point
# ===========================================================================


class TestIsStoppingPoint:
    """The stopping-point gate is True only at a track end and never raises."""

    def test_core_track_end_is_stopping_point(self, tmp_path: Path) -> None:
        prog = tmp_path / "progress.json"
        prog.write_text(json.dumps({"modules_completed": [1, 2, 3, 4, 5, 6, 7]}))
        assert ega.is_stopping_point(str(prog)) is True

    def test_advanced_track_end_is_stopping_point(self, tmp_path: Path) -> None:
        prog = tmp_path / "progress.json"
        prog.write_text(json.dumps({"modules_completed": list(range(1, 12))}))
        assert ega.is_stopping_point(str(prog)) is True

    def test_mid_bootcamp_is_not_stopping_point(self, tmp_path: Path) -> None:
        prog = tmp_path / "progress.json"
        prog.write_text(json.dumps({"modules_completed": [1, 2, 3, 4, 5, 6]}))
        assert ega.is_stopping_point(str(prog)) is False

    def test_absent_progress_is_not_stopping_point(self, tmp_path: Path) -> None:
        assert ega.is_stopping_point(str(tmp_path / "missing.json")) is False

    def test_malformed_progress_is_not_stopping_point(self, tmp_path: Path) -> None:
        prog = tmp_path / "progress.json"
        prog.write_text("this is not json {")
        assert ega.is_stopping_point(str(prog)) is False

    def test_non_list_modules_completed_is_not_stopping_point(
        self, tmp_path: Path
    ) -> None:
        prog = tmp_path / "progress.json"
        prog.write_text(json.dumps({"modules_completed": "7"}))
        assert ega.is_stopping_point(str(prog)) is False

    def test_bool_true_is_not_counted_as_module_seven(self, tmp_path: Path) -> None:
        """``True == 1`` must never be mistaken for a completed module number."""
        prog = tmp_path / "progress.json"
        prog.write_text(json.dumps({"modules_completed": [True, False]}))
        assert ega.is_stopping_point(str(prog)) is False

    @given(
        completed=st.lists(st.integers(min_value=1, max_value=11), max_size=11),
    )
    def test_stopping_point_iff_track_end_present(
        self, completed: list[int]
    ) -> None:
        """is_stopping_point is True exactly when 7 or 11 is completed.

        Uses a self-managed temp dir (not the function-scoped ``tmp_path``
        fixture) so it composes cleanly with ``@given``.
        """
        with tempfile.TemporaryDirectory() as d:
            prog = Path(d) / "progress.json"
            prog.write_text(json.dumps({"modules_completed": completed}))
            expected = 7 in completed or 11 in completed
            assert ega.is_stopping_point(str(prog)) is expected


# ===========================================================================
# --stop-hook gating in main()
# ===========================================================================


class TestStopHookMain:
    """The --stop-hook mode gates correctly and never wedges the session."""

    def test_no_op_away_from_stopping_point(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _write_progress(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        rc = ega.main(_argv(paths, _missing_flag(tmp_path)))

        assert rc == 0
        # Away from a stopping point the guarantee does nothing.
        assert not Path(paths.pdf).exists()
        assert not Path(paths.transcript).exists()

    def test_defers_while_question_pending(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _write_progress(paths, [1, 2, 3, 4, 5, 6, 7])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        flag = tmp_path / "config" / ".question_pending"
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("")

        rc = ega.main(_argv(paths, str(flag)))

        assert rc == 0
        # A pending question defers the guarantee entirely.
        assert not Path(paths.pdf).exists()

    def test_produces_artifacts_at_stopping_point(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _write_progress(paths, [1, 2, 3, 4, 5, 6, 7])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        rc = ega.main(_argv(paths, _missing_flag(tmp_path)))

        assert rc == 0
        assert Path(paths.pdf).exists()
        assert ega.is_non_empty(Path(paths.pdf), min_body=True)

    def test_produces_floor_pdf_when_no_recap_source(self, tmp_path: Path) -> None:
        """At a stopping point with no recap sources, the trophy PDF still exists."""
        paths = _paths(tmp_path)
        _write_progress(paths, [11])  # advanced track end, but no recap sources
        assert not Path(paths.recap).exists()

        rc = ega.main(_argv(paths, _missing_flag(tmp_path)))

        assert rc == 0
        # The no-data floor guarantees the PDF exists even with no captured data.
        assert Path(paths.pdf).exists()
        assert ega.is_non_empty(Path(paths.pdf), min_body=True)

    def test_never_raises_even_when_ensure_fails(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A Stop hook must never wedge the session, so main swallows failures."""
        paths = _paths(tmp_path)
        _write_progress(paths, [7])

        def _boom(*args, **kwargs):
            raise RuntimeError("simulated ensure failure")

        monkeypatch.setattr(ega, "ensure_all", _boom)

        rc = ega.main(_argv(paths, _missing_flag(tmp_path)))

        assert rc == 0


# ===========================================================================
# No-data floor
# ===========================================================================


class TestNoDataFloor:
    """The recap PDF is always produced, and the floor is idempotent."""

    def test_floor_pdf_is_idempotent_while_recap_absent(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _mkdirs(paths)
        assert not Path(paths.recap).exists()

        first = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert first.exists and first.non_empty and first.regenerated
        first_bytes = Path(paths.pdf).read_bytes()

        # A second run with the recap still absent leaves the floor PDF as-is.
        second = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert second.exists and second.non_empty
        assert second.regenerated is False
        assert Path(paths.pdf).read_bytes() == first_bytes

    def test_floor_is_replaced_once_real_recap_appears(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _mkdirs(paths)

        # Floor PDF first (no recap source).
        floor = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert floor.exists and floor.non_empty

        # Real recap content appears and is newer than the floor PDF.
        Path(paths.recap).write_text(_recap_text([3]), encoding="utf-8")
        os.utime(paths.pdf, (1_000_000_000, 1_000_000_000))
        os.utime(paths.recap, (2_000_000_000, 2_000_000_000))

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.exists and status.non_empty and status.regenerated
        # The real recap's module content survives into the PDF.
        import recap_pdf_render as rpr  # noqa: PLC0415

        text = rpr.extract_pdf_text(Path(paths.pdf).read_bytes())
        assert "Module 3" in text
