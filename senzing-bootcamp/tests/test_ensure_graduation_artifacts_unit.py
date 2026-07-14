"""Unit tests for the graduation-artifact guarantee orchestrator.

Feature: guaranteed-graduation-artifacts — task 3.6.

Example-based, edge-case coverage for
``senzing-bootcamp/scripts/ensure_graduation_artifacts.py`` (created in tasks
3.1-3.5). These complement the property-based suite (task 3.7) by pinning
concrete behaviour of the three per-artifact guarantees and the CLI against real
files in ``tmp_path``:

    no-op when valid       every artifact already present, non-empty, and not
                           stale is left byte-for-byte unchanged (regenerated
                           False on a re-run).
    absent -> regenerated  a missing transcript / recap / rendered recap is
                           reconstructed from its always-present sources.
    empty -> regenerated   a whitespace-only artifact is reconstructed.
    stale -> regenerated   an artifact older than its newest source input is
                           regenerated (fresh source content flows through).
    --check side-effects   the ``--check`` CLI path creates/modifies/deletes no
                           file and exits 0 iff every artifact is satisfied.
    error paths preserve   recap source unavailable leaves an existing recap
                           unchanged (Req 3.3); an absent/empty recap source
                           yields no rendered recap plus an error (Req 4.7); a
                           failure in one artifact never suppresses the others
                           (Req 6.3).

All fixtures use synthetic, PII-free content; no secret-looking strings appear
in the generated data.

The guaranteed-recap-pdf feature (task 4.2) adds example-based coverage that,
with fpdf2 simulated absent and autoinstall disabled (the stdlib Tier 3 path, no
real install), the orchestrator still yields a valid ``docs/bootcamp_recap.pdf``,
that ``--check`` reflects PDF presence (never HTML alone), and that a valid fresh
PDF is an idempotent no-op (Requirements 7.2, 7.4).

Validates: Requirements 2.1, 2.2, 2.3, 3.3, 4.7, 6.2, 6.3, 7.2, 7.4, 11.1
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import ensure_graduation_artifacts as ega  # noqa: E402

# Fixed timestamps for staleness manipulation (POSIX seconds). ``OLD`` predates
# ``NEW`` so an artifact stamped ``OLD`` is stale against a source stamped
# ``NEW``.
_OLD_MTIME = 1_000_000.0
_NEW_MTIME = 2_000_000.0

STARTED_AT = "2025-01-10T09:00:00Z"


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _paths(root: Path) -> ega.ArtifactPaths:
    """Build ``ArtifactPaths`` rooted under ``root`` (absolute paths).

    The ``journal`` field aliases the recap path, mirroring the consolidated
    single-source model (``ArtifactPaths.journal`` defaults to
    ``docs/bootcamp_recap.md``): the legacy journal file is retired and its
    content now lives in the Consolidated_Log.

    Args:
        root: The temporary workspace root.

    Returns:
        An ``ArtifactPaths`` whose every path points inside ``root``.
    """
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
    """Create the ``config`` and ``docs`` directories for ``paths``."""
    Path(paths.progress).parent.mkdir(parents=True, exist_ok=True)
    Path(paths.recap).parent.mkdir(parents=True, exist_ok=True)


def _progress_json(modules: list[int]) -> str:
    """Serialize a minimal ``bootcamp_progress.json`` for ``modules``."""
    step_history = {
        str(m): {
            "last_completed_step": 5,
            "updated_at": f"2025-01-10T{9 + m:02d}:00:00Z",
        }
        for m in modules
    }
    return json.dumps(
        {
            "modules_completed": modules,
            "step_history": step_history,
            "started_at": STARTED_AT,
        },
        indent=2,
    )


def _recap_text(modules: list[int]) -> str:
    """Build a canonical, non-empty recap Markdown covering ``modules``.

    Each module carries the three labeled subsections plus a Q&R pair, so the
    document doubles as a transcript-reconstruction source and has ample body
    lines for the rendered-recap round-trip check.

    Args:
        modules: Ascending module numbers to include.

    Returns:
        Recap Markdown text ending with a trailing newline.
    """
    lines = ["# Senzing Bootcamp Recap", ""]
    for m in modules:
        lines += [
            f"## Module {m}: Topic {m} \u2014 2025-01-10T{9 + m:02d}:00:00Z",
            "",
            "### Information Shared",
            f"- Learned core concept {m} about entity resolution",
            f"- Reviewed how module {m} fits the pipeline",
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


def _seed_sources(paths: ega.ArtifactPaths, modules: list[int]) -> None:
    """Write a progress JSON source for ``modules`` (no recap written)."""
    _mkdirs(paths)
    Path(paths.progress).write_text(_progress_json(modules), encoding="utf-8")


def _set_mtime(path: str, mtime: float) -> None:
    """Set both atime and mtime of ``path`` to ``mtime`` seconds."""
    os.utime(path, (mtime, mtime))


def _argv(paths: ega.ArtifactPaths, *extra: str) -> list[str]:
    """Build a full CLI argv wiring every path override, plus ``extra`` flags.

    The deprecated ``--journal`` flag is intentionally omitted so the default
    argv reflects the consolidated single-source model. Tests that exercise the
    deprecation/backward-compatibility path pass ``--journal`` explicitly via
    ``extra``.
    """
    return [
        "--log", paths.log,
        "--recap", paths.recap,
        "--transcript", paths.transcript,
        "--progress", paths.progress,
        "--progress-dir", paths.progress_dir,
        "--pdf", paths.pdf,
        "--html", paths.html,
        *extra,
    ]


def _snapshot_dir(root: Path) -> dict[str, tuple[int, bytes]]:
    """Capture ``(mtime_ns, bytes)`` for every file under ``root``.

    Used to assert that a code path performed no filesystem side effects: two
    equal snapshots mean no file was created, modified, or deleted.

    Args:
        root: The directory tree to snapshot.

    Returns:
        A mapping of relative path -> ``(mtime_ns, content_bytes)``.
    """
    snapshot: dict[str, tuple[int, bytes]] = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            stat = path.stat()
            snapshot[str(path.relative_to(root))] = (
                stat.st_mtime_ns,
                path.read_bytes(),
            )
    return snapshot


# ===========================================================================
# No-op when every artifact is already valid
# ===========================================================================


class TestNoOpWhenValid:
    """A workspace whose artifacts are all valid is left unchanged on re-run.

    After a first ``ensure_all`` produces every artifact, a second consecutive
    run regenerates nothing (each ``regenerated`` flag is False) and every file
    is byte-for-byte identical, so repeated stopping points are a no-op.

    Validates: Requirements 2.2
    """

    def test_second_run_regenerates_nothing_and_preserves_bytes(
        self, tmp_path: Path
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        # First run materializes every artifact.
        first = ega.ensure_all(paths)
        assert first.all_satisfied

        produced = [status.path for status in first.artifacts]
        before = {path: Path(path).read_bytes() for path in produced}

        # Second run: every artifact is already valid, so nothing regenerates.
        second = ega.ensure_all(paths)
        assert second.all_satisfied
        for status in second.artifacts:
            assert status.regenerated is False, f"{status.key} was regenerated"
            assert status.error is None

        # Byte-for-byte unchanged.
        for path, content in before.items():
            assert Path(path).read_bytes() == content, f"{path} changed on re-run"

    def test_valid_recap_is_left_untouched(self, tmp_path: Path) -> None:
        """A present, non-empty, fresh recap is a no-op (no rewrite)."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        original = _recap_text([1, 2, 3])
        Path(paths.recap).write_text(original, encoding="utf-8")

        status = ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert status.regenerated is False
        assert status.exists and status.non_empty
        assert Path(paths.recap).read_text(encoding="utf-8") == original


# ===========================================================================
# Absent artifacts are regenerated
# ===========================================================================


class TestAbsentRegeneration:
    """Each guaranteed artifact is reconstructed when it is absent.

    Validates: Requirements 2.2
    """

    def test_absent_transcript_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        assert not Path(paths.transcript).exists()

        status = ega.ensure_transcript(paths.log, paths.recap, paths.transcript)

        assert status.regenerated is True
        assert status.exists and status.non_empty
        assert Path(paths.transcript).exists()

    def test_absent_recap_is_regenerated_from_progress(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        assert not Path(paths.recap).exists()

        status = ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert status.regenerated is True
        assert status.exists and status.non_empty
        content = Path(paths.recap).read_text(encoding="utf-8")
        for module in (1, 2, 3):
            assert f"## Module {module}:" in content

    def test_absent_rendered_recap_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        assert not Path(paths.pdf).exists() and not Path(paths.html).exists()

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.regenerated is True
        assert status.exists and status.non_empty
        assert status.error is None
        # The reported path is the form actually produced (.pdf or .html).
        assert Path(status.path).exists()


# ===========================================================================
# Empty artifacts are regenerated
# ===========================================================================


class TestEmptyRegeneration:
    """A whitespace-only artifact fails the non-empty invariant and regenerates.

    Validates: Requirements 2.2
    """

    def test_empty_transcript_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        Path(paths.transcript).write_text("   \n\t\n", encoding="utf-8")

        status = ega.ensure_transcript(paths.log, paths.recap, paths.transcript)

        assert status.regenerated is True
        assert status.exists and status.non_empty
        assert Path(paths.transcript).read_text(encoding="utf-8").strip() != ""

    def test_empty_recap_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text("   \n", encoding="utf-8")

        status = ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert status.regenerated is True
        assert status.exists and status.non_empty
        content = Path(paths.recap).read_text(encoding="utf-8")
        assert "## Module 1:" in content

    def test_empty_rendered_recap_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        # Produce a valid rendered recap, then corrupt it to whitespace so the
        # non-empty invariant fails regardless of the .pdf/.html form chosen.
        first = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert first.exists and first.non_empty
        Path(first.path).write_text("   \n", encoding="utf-8")

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.regenerated is True
        assert status.exists and status.non_empty
        assert Path(status.path).exists()


# ===========================================================================
# Stale artifacts are regenerated
# ===========================================================================


class TestStaleRegeneration:
    """An artifact older than its newest source input is regenerated.

    Validates: Requirements 2.2
    """

    def test_stale_recap_is_regenerated_with_fresh_module(self, tmp_path: Path) -> None:
        """A stale recap missing a completed module gets that module appended."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        # Recap covers only modules 1-2 and is older than the progress source.
        Path(paths.recap).write_text(_recap_text([1, 2]), encoding="utf-8")
        _set_mtime(paths.recap, _OLD_MTIME)
        _set_mtime(paths.progress, _NEW_MTIME)
        assert "## Module 3:" not in Path(paths.recap).read_text(encoding="utf-8")

        status = ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert status.regenerated is True
        assert status.exists and status.non_empty
        assert "## Module 3:" in Path(paths.recap).read_text(encoding="utf-8")

    def test_stale_transcript_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        Path(paths.transcript).write_text(
            "# Bootcamp Q&A Transcript\n\nstale body\n", encoding="utf-8"
        )
        # Transcript predates the recap source -> stale.
        _set_mtime(paths.transcript, _OLD_MTIME)
        _set_mtime(paths.recap, _NEW_MTIME)

        status = ega.ensure_transcript(paths.log, paths.recap, paths.transcript)

        assert status.regenerated is True
        assert status.exists and status.non_empty

    def test_stale_rendered_recap_is_regenerated(self, tmp_path: Path) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        first = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert first.exists and first.non_empty
        # Rendered recap predates its recap source -> stale.
        _set_mtime(first.path, _OLD_MTIME)
        _set_mtime(paths.recap, _NEW_MTIME)

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.regenerated is True
        assert status.exists and status.non_empty


# ===========================================================================
# --check is side-effect free
# ===========================================================================


class TestCheckIsSideEffectFree:
    """The ``--check`` CLI path performs no filesystem writes.

    It reports the current on-disk state without invoking any regeneration, so
    the workspace is byte-for-byte identical before and after, and the exit code
    is 0 iff every artifact is already satisfied.

    Validates: Requirements 2.1
    """

    def test_check_creates_no_files_and_exits_one_when_incomplete(
        self, tmp_path: Path
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        # Transcript and rendered recap are absent -> not satisfied.
        before = _snapshot_dir(tmp_path)

        exit_code = ega.main(_argv(paths, "--check"))

        after = _snapshot_dir(tmp_path)
        assert before == after, "--check modified the workspace"
        assert exit_code == 1
        assert not Path(paths.transcript).exists()
        assert not Path(paths.pdf).exists()
        assert not Path(paths.html).exists()

    def test_check_exits_zero_when_all_satisfied_without_writes(
        self, tmp_path: Path
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        assert ega.ensure_all(paths).all_satisfied

        before = _snapshot_dir(tmp_path)
        exit_code = ega.main(_argv(paths, "--check"))
        after = _snapshot_dir(tmp_path)

        assert before == after, "--check modified an already-satisfied workspace"
        assert exit_code == 0

    def test_check_all_helper_is_side_effect_free(self, tmp_path: Path) -> None:
        """``check_all`` itself never touches the filesystem."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        before = _snapshot_dir(tmp_path)
        report = ega.check_all(paths)
        after = _snapshot_dir(tmp_path)

        assert before == after
        # Recap present, transcript + rendered recap absent.
        assert "recap_md" not in report.missing
        assert "transcript" in report.missing
        assert "rendered_recap" in report.missing


# ===========================================================================
# Error paths preserve prior artifacts
# ===========================================================================


class TestErrorPathsPreserveArtifacts:
    """Each error path records an error and preserves any pre-existing artifact.

    Validates: Requirements 3.3, 4.7, 6.3
    """

    def test_recap_source_unavailable_leaves_existing_recap_unchanged(
        self, tmp_path: Path
    ) -> None:
        """No progress + no module artifacts -> existing recap is preserved (Req 3.3)."""
        paths = _paths(tmp_path)
        _mkdirs(paths)
        # A recap with no ``## Module N`` section fails the non-empty invariant,
        # forcing a regeneration attempt — but its sources are unavailable.
        original = "# Recap\n\nPrior notes without a module section.\n"
        Path(paths.recap).write_text(original, encoding="utf-8")
        assert not Path(paths.progress).exists()
        assert not Path(paths.progress_dir).exists()

        status = ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert status.error is not None
        assert "unavailable" in status.error.lower()
        assert status.regenerated is False
        # The prior recap bytes are untouched (Req 3.3).
        assert Path(paths.recap).read_text(encoding="utf-8") == original

    def test_rendered_recap_source_empty_produces_nothing_with_error(
        self, tmp_path: Path, capsys
    ) -> None:
        """An empty recap source yields no rendered recap plus an error (Req 4.7)."""
        paths = _paths(tmp_path)
        _mkdirs(paths)
        Path(paths.recap).write_text("   \n", encoding="utf-8")

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.error is not None
        assert status.exists is False
        assert status.non_empty is False
        assert not Path(paths.pdf).exists()
        assert not Path(paths.html).exists()
        assert "recap source unavailable" in capsys.readouterr().out.lower()

    def test_rendered_recap_source_absent_produces_nothing_with_error(
        self, tmp_path: Path, capsys
    ) -> None:
        """An absent recap source yields no rendered recap plus an error (Req 4.7)."""
        paths = _paths(tmp_path)
        _mkdirs(paths)
        assert not Path(paths.recap).exists()

        status = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert status.error is not None
        assert status.exists is False
        assert not Path(paths.pdf).exists()
        assert not Path(paths.html).exists()
        assert "recap source unavailable" in capsys.readouterr().out.lower()

    def test_one_artifact_failure_does_not_suppress_the_others(
        self, tmp_path: Path
    ) -> None:
        """A failing recap does not suppress transcript generation (Req 6.3)."""
        paths = _paths(tmp_path)
        _mkdirs(paths)
        # No progress, no recap, no module artifacts: recap and rendered recap
        # cannot be produced, but the transcript still gets its "no Q&A history"
        # placeholder from ensure mode.
        report = ega.ensure_all(paths)
        by_key = {status.key: status for status in report.artifacts}

        # The recap and rendered recap fail (their sources are unavailable)...
        assert by_key["recap_md"].error is not None
        assert by_key["recap_md"].non_empty is False
        assert by_key["rendered_recap"].error is not None
        assert by_key["rendered_recap"].non_empty is False

        # ...yet the transcript is still generated (failure isolation, Req 6.3).
        assert by_key["transcript"].exists is True
        assert by_key["transcript"].non_empty is True
        assert Path(paths.transcript).exists()

        assert report.all_satisfied is False
        assert "recap_md" in report.missing
        assert "rendered_recap" in report.missing
        assert "transcript" not in report.missing


# ===========================================================================
# Regeneration is attempted at most once per artifact per run
# ===========================================================================


class TestAtMostOnceRegeneration:
    """Each artifact's regeneration is attempted at most once per run.

    Validates: Requirements 2.3
    """

    def test_recap_backfill_invoked_at_most_once_per_run(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])  # recap absent -> one regeneration needed

        calls = {"count": 0}
        real_backfill = ega.completion_artifacts.backfill_recap_sections

        def _counting_backfill(*args, **kwargs):
            calls["count"] += 1
            return real_backfill(*args, **kwargs)

        monkeypatch.setattr(
            ega.completion_artifacts,
            "backfill_recap_sections",
            _counting_backfill,
        )

        report = ega.ensure_all(paths)

        assert calls["count"] == 1
        recap_status = next(s for s in report.artifacts if s.key == "recap_md")
        assert recap_status.regenerated is True

    def test_valid_recap_triggers_no_regeneration_attempt(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """An already-valid recap is never handed to the backfill applier."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        calls = {"count": 0}

        def _counting_backfill(*args, **kwargs):
            calls["count"] += 1
            return []

        monkeypatch.setattr(
            ega.completion_artifacts,
            "backfill_recap_sections",
            _counting_backfill,
        )

        ega.ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        )

        assert calls["count"] == 0


# ===========================================================================
# --journal is a deprecated no-op (journal-recap-consolidation, task 6.1)
# ===========================================================================


class TestJournalArgumentDeprecated:
    """``--journal`` is accepted but ignored with a stderr deprecation note.

    The journal is retired: its narrative content is now folded into the
    consolidated recap (``docs/bootcamp_recap.md``). The orchestrator keeps the
    ``--journal`` flag and the ``ArtifactPaths.journal`` field for signature
    compatibility, but the flag is a no-op that emits a deprecation warning on
    stderr, and the field defaults to the recap path.

    Validates: Requirements 6.1, 6.2
    """

    def test_artifact_paths_journal_defaults_to_recap_path(self) -> None:
        """The ``journal`` field defaults to the consolidated recap path."""
        assert ega.ArtifactPaths().journal == "docs/bootcamp_recap.md"

    def test_journal_flag_emits_deprecation_warning_on_stderr(
        self, tmp_path: Path, capsys
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        # Explicitly supplying the legacy --journal path must still succeed
        # (or fail only on missing artifacts) while warning about deprecation.
        legacy_journal = str(tmp_path / "docs" / "bootcamp_journal.md")
        ega.main(_argv(paths, "--journal", legacy_journal, "--check"))

        captured = capsys.readouterr()
        assert "--journal is deprecated" in captured.err
        assert "consolidated recap" in captured.err

    def test_no_journal_flag_emits_no_deprecation_warning(
        self, tmp_path: Path, capsys
    ) -> None:
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        # The default argv omits --journal, so no deprecation note is emitted.
        ega.main(_argv(paths, "--check"))

        assert "--journal is deprecated" not in capsys.readouterr().err

    def test_journal_flag_value_is_ignored_by_recap_reconstruction(
        self, tmp_path: Path
    ) -> None:
        """A bogus ``--journal`` path never affects recap reconstruction."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        # ensure_recap_md ignores the journal argument entirely.
        status = ega.ensure_recap_md(
            paths.progress,
            paths.recap,
            "/nonexistent/legacy_journal.md",
            paths.progress_dir,
        )

        assert status.exists and status.non_empty
        content = Path(paths.recap).read_text(encoding="utf-8")
        for module in (1, 2, 3):
            assert f"## Module {module}:" in content


# ===========================================================================
# The orchestrator operates on the Consolidated_Log as the single source
# (journal-recap-consolidation, task 6.2)
# ===========================================================================


class TestConsolidatedRecapSingleSource:
    """The orchestrator treats the recap Markdown as the single per-module source.

    After journal-recap consolidation, ``docs/bootcamp_recap.md`` (the
    Consolidated_Log) is the one file the orchestrator reconstructs and verifies.
    No separate journal file participates: an explicit ``--journal`` path is
    ignored, the legacy journal file is never read or created, and a
    present/non-empty/fresh Consolidated_Log is left unchanged (idempotent
    no-op).

    Validates: Requirements 6.2, 6.3, 11.1
    """

    def test_recap_reconstructed_as_single_source_ignoring_legacy_journal(
        self, tmp_path: Path
    ) -> None:
        """Ensure mode rebuilds the recap alone; the legacy journal stays absent."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])  # progress only; recap absent
        legacy_journal = tmp_path / "docs" / "bootcamp_journal.md"
        assert not Path(paths.recap).exists()
        assert not legacy_journal.exists()

        # Even with the legacy --journal path explicitly supplied, the recap is
        # the only per-module source that gets reconstructed.
        ega.main(_argv(paths, "--journal", str(legacy_journal)))

        recap_content = Path(paths.recap).read_text(encoding="utf-8")
        for module in (1, 2, 3):
            assert f"## Module {module}:" in recap_content
        # The retired journal file is never materialized as a separate source.
        assert not legacy_journal.exists()

    def test_valid_consolidated_recap_is_left_unchanged(
        self, tmp_path: Path
    ) -> None:
        """A present, non-empty, fresh Consolidated_Log is an idempotent no-op."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        original = _recap_text([1, 2, 3])
        Path(paths.recap).write_text(original, encoding="utf-8")
        legacy_journal = str(tmp_path / "docs" / "bootcamp_journal.md")

        ega.main(_argv(paths, "--journal", legacy_journal))

        # The Consolidated_Log is left byte-for-byte unchanged (Req 6.3).
        assert Path(paths.recap).read_text(encoding="utf-8") == original

    def test_ensure_all_reports_recap_as_the_single_verified_source(
        self, tmp_path: Path
    ) -> None:
        """``ensure_all`` verifies the recap path itself as the recap_md source."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")

        report = ega.ensure_all(paths)

        recap_status = next(s for s in report.artifacts if s.key == "recap_md")
        # The single per-module source verified is the Consolidated_Log recap
        # path — not any separate journal file.
        assert recap_status.path == paths.recap
        assert recap_status.exists and recap_status.non_empty
        assert recap_status.regenerated is False


# ===========================================================================
# Guaranteed PDF even without fpdf2 (guaranteed-recap-pdf, task 4.2)
# ===========================================================================


def _disable_fpdf2(monkeypatch) -> None:
    """Simulate fpdf2 absent with autoinstall disabled (stdlib Tier 3, no install).

    Patches the shared ``pdf_render_strategy`` module so the availability probe
    returns False, the opt-out resolver returns False (so no ``pip install`` is
    attempted and no subprocess/network is touched), and the guarded installer is
    neutralised as a defensive backstop. The ``monkeypatch`` fixture restores
    every attribute at test teardown.

    Args:
        monkeypatch: The pytest ``monkeypatch`` fixture.
    """
    monkeypatch.setattr(ega.pdf_render_strategy, "fpdf2_available", lambda: False)
    monkeypatch.setattr(
        ega.pdf_render_strategy,
        "resolve_allow_autoinstall",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        ega.pdf_render_strategy,
        "attempt_autoinstall",
        lambda *args, **kwargs: False,
    )


class TestGuaranteedPdfWithoutFpdf2:
    """The rendered recap is a guaranteed valid PDF even without fpdf2.

    With fpdf2 simulated absent and autoinstall disabled (the stdlib Tier 3 path,
    no real install), the orchestrator still produces a valid
    ``docs/bootcamp_recap.pdf``; ``--check`` reports the rendered recap satisfied
    only when the PDF exists (never for an HTML file alone); and a valid, fresh
    PDF is left byte-for-byte unchanged on a re-run (idempotent no-op).

    Validates: Requirements 7.2, 7.4
    """

    def test_ensure_all_yields_valid_pdf_when_fpdf2_absent(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """fpdf2 absent + autoinstall off -> ``ensure_all`` still writes a PDF."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        _disable_fpdf2(monkeypatch)

        report = ega.ensure_all(paths)

        assert report.all_satisfied, f"missing: {report.missing}"
        rendered = next(s for s in report.artifacts if s.key == "rendered_recap")
        # The guaranteed rendered-recap artifact is the PDF, produced by stdlib.
        assert rendered.path == paths.pdf
        assert rendered.exists and rendered.non_empty
        assert rendered.error is None

        pdf_bytes = Path(paths.pdf).read_bytes()
        assert pdf_bytes.startswith(b"%PDF-")
        text = ega.recap_pdf_render.extract_pdf_text(pdf_bytes)
        for module in (1, 2, 3):
            assert f"Module {module}" in text
        # HTML is never the artifact that satisfies the guarantee.
        assert not Path(paths.html).exists()

    def test_check_reflects_pdf_presence_not_html(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """``--check`` is unsatisfied with only HTML and satisfied with a PDF."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        # Satisfy the other two artifacts so the rendered recap is isolated.
        ega.ensure_transcript(paths.log, paths.recap, paths.transcript)

        # Only an HTML file exists (no PDF) -> rendered recap UNSATISFIED.
        Path(paths.html).write_text("<html><body>recap</body></html>\n", encoding="utf-8")
        assert not Path(paths.pdf).exists()

        report_html = ega.check_all(paths)
        html_by_key = {s.key: s for s in report_html.artifacts}
        assert html_by_key["rendered_recap"].exists is False
        assert html_by_key["rendered_recap"].non_empty is False
        assert "rendered_recap" in report_html.missing
        assert ega.main(_argv(paths, "--check")) == 1

        # Produce a valid PDF via the stdlib tier -> rendered recap SATISFIED.
        _disable_fpdf2(monkeypatch)
        ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        report_pdf = ega.check_all(paths)
        pdf_by_key = {s.key: s for s in report_pdf.artifacts}
        assert pdf_by_key["rendered_recap"].exists is True
        assert pdf_by_key["rendered_recap"].non_empty is True
        assert "rendered_recap" not in report_pdf.missing
        assert ega.main(_argv(paths, "--check")) == 0

    def test_valid_fresh_stdlib_pdf_left_unchanged(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """A valid, fresh stdlib PDF is a byte-for-byte idempotent no-op."""
        paths = _paths(tmp_path)
        _seed_sources(paths, [1, 2, 3])
        Path(paths.recap).write_text(_recap_text([1, 2, 3]), encoding="utf-8")
        _disable_fpdf2(monkeypatch)

        first = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)
        assert first.regenerated is True
        assert Path(paths.pdf).exists()
        before = Path(paths.pdf).read_bytes()

        # A second run over the valid, fresh PDF regenerates nothing.
        second = ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

        assert second.regenerated is False
        assert second.error is None
        assert second.exists and second.non_empty
        assert Path(paths.pdf).read_bytes() == before
