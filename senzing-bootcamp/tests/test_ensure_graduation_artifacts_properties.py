"""Property-based tests for the graduation-artifact guarantee orchestrator.

Feature: guaranteed-graduation-artifacts — task 3.7.

These properties quantify the design's Correctness Properties 1-8 over synthetic,
PII-free workspaces built under throwaway directories (matching this suite's
established ``tempfile.mkdtemp`` per-example pattern, since Hypothesis reuses a
single value for any function-scoped fixture). The module under test is
``senzing-bootcamp/scripts/ensure_graduation_artifacts.py`` (tasks 3.1-3.5).

Property -> requirement map (see design "Correctness Properties"):

    P1 Guaranteed presence           1.1, 1.7, 1.8, 3.1, 4.1
    P2 Idempotence / no-op on valid  2.5, 2.6
    P3 Regenerate only when needed   2.2, 2.3
    P4 ``--check`` side-effect free  2.1
    P5 Rendered-recap selection      4.2, 4.3, 4.8, 2.7
    P6 Failure isolation             1.9, 3.3, 6.3
    P7 Enforcement completeness      2.1, 2.3
    P8 Self-containment              6.1, 4.5

Example counts come from the active Hypothesis profile (fast=5 locally,
thorough=100 in CI); no test hand-sets ``@settings(max_examples=...)``.

Validates: Requirements 1.1, 2.5, 2.6, 2.7, 4.2, 4.3, 4.8
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import ensure_graduation_artifacts as ega  # noqa: E402
import recap_html_render  # noqa: E402

# Fixed POSIX-second timestamps for staleness manipulation. ``_OLD`` predates
# ``_NEW`` so an artifact stamped ``_OLD`` is stale against a source stamped
# ``_NEW``.
_OLD_MTIME = 1_000_000.0
_NEW_MTIME = 2_000_000.0

STARTED_AT = "2025-01-10T09:00:00Z"


# ---------------------------------------------------------------------------
# Synthetic-workspace builders (mirrors test_ensure_graduation_artifacts_unit.py)
# ---------------------------------------------------------------------------


def _paths(root: Path) -> ega.ArtifactPaths:
    """Build ``ArtifactPaths`` whose every path is absolute under ``root``."""
    return ega.ArtifactPaths(
        log=str(root / "config" / "session_log.jsonl"),
        recap=str(root / "docs" / "bootcamp_recap.md"),
        transcript=str(root / "docs" / "bootcamp_transcript.md"),
        progress=str(root / "config" / "bootcamp_progress.json"),
        journal=str(root / "docs" / "bootcamp_journal.md"),
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
    """Build a canonical, non-empty recap Markdown (with Q&R pairs) for ``modules``.

    Each module carries the three labeled subsections plus a Q&R pair, so the
    document doubles as a transcript-reconstruction source and has ample body
    lines for the rendered-recap round-trip body check.
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


def _recap_text_no_qa(modules: list[int]) -> str:
    """Build a non-empty recap Markdown that has module sections but no Q&R pairs.

    Used to exercise the "no Q&A history" transcript record (Req 1.7, 1.8): the
    transcript must still be non-empty even when no Q&A source content exists.
    """
    lines = ["# Senzing Bootcamp Recap", ""]
    for m in modules:
        lines += [
            f"## Module {m}: Topic {m} \u2014 2025-01-10T{9 + m:02d}:00:00Z",
            "",
            "### Information Shared",
            f"- Learned core concept {m} about entity resolution",
            "",
            "### Actions Taken",
            f"- Completed the module {m} hands-on exercise",
            "",
        ]
    return "\n".join(lines) + "\n"


def _seed_progress(paths: ega.ArtifactPaths, modules: list[int]) -> None:
    """Write a progress JSON source for ``modules`` (no recap written)."""
    _mkdirs(paths)
    Path(paths.progress).write_text(_progress_json(modules), encoding="utf-8")


def _set_mtime(path: str, mtime: float) -> None:
    """Set both atime and mtime of ``path`` to ``mtime`` seconds."""
    os.utime(path, (mtime, mtime))


def _argv(paths: ega.ArtifactPaths, *extra: str) -> list[str]:
    """Build a full CLI argv wiring every path override, plus ``extra`` flags."""
    return [
        "--log", paths.log,
        "--recap", paths.recap,
        "--transcript", paths.transcript,
        "--progress", paths.progress,
        "--journal", paths.journal,
        "--progress-dir", paths.progress_dir,
        "--pdf", paths.pdf,
        "--html", paths.html,
        *extra,
    ]


def _snapshot_dir(root: Path) -> dict[str, tuple[int, bytes]]:
    """Capture ``(mtime_ns, bytes)`` for every file under ``root``.

    Two equal snapshots mean no file was created, modified, or deleted.
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


@contextlib.contextmanager
def _workspace():
    """Yield a fresh temp-dir ``ArtifactPaths`` and remove the tree afterward.

    A brand-new directory per example keeps generated worlds fully isolated,
    which is required because Hypothesis would otherwise reuse a single
    function-scoped ``tmp_path`` across every example.
    """
    root = Path(tempfile.mkdtemp(prefix="ega_prop_"))
    try:
        paths = _paths(root)
        _mkdirs(paths)
        yield root, paths
    finally:
        shutil.rmtree(root, ignore_errors=True)


@contextlib.contextmanager
def _patched(obj: object, name: str, value: object):
    """Temporarily set ``obj.name = value``, restoring the original afterward."""
    sentinel = object()
    original = getattr(obj, name, sentinel)
    setattr(obj, name, value)
    try:
        yield
    finally:
        if original is sentinel:
            delattr(obj, name)
        else:
            setattr(obj, name, original)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_module_lists() -> st.SearchStrategy[list[int]]:
    """Draw a non-empty ascending list of distinct module numbers (1-11)."""
    return st.lists(
        st.integers(min_value=1, max_value=11),
        min_size=1,
        max_size=5,
        unique=True,
    ).map(sorted)


def st_recap_scenarios() -> st.SearchStrategy[str]:
    """Draw a pre-existing recap state for the regeneration property."""
    return st.sampled_from(["absent", "empty", "stale", "valid"])


def st_render_branches() -> st.SearchStrategy[str]:
    """Draw a rendered-recap selection branch to exercise."""
    return st.sampled_from(["pdf_ok", "pdf_fail", "no_fpdf"])


def st_fail_targets() -> st.SearchStrategy[str]:
    """Draw which artifact's generator is forced to fail for isolation."""
    return st.sampled_from(["recap", "rendered"])


def st_status_flag_triples() -> st.SearchStrategy[list[tuple[bool, bool]]]:
    """Draw an ``(exists, non_empty)`` flag pair for each of the three artifacts."""
    flag_pair = st.tuples(st.booleans(), st.booleans())
    return st.lists(flag_pair, min_size=3, max_size=3)


# ===========================================================================
# Property 1: Guaranteed presence
# ===========================================================================


class TestGuaranteedPresence:
    """After ``ensure_all`` with sources present, every artifact is non-empty.

    Validates: Requirements 1.1, 1.7, 1.8, 3.1, 4.1
    """

    @given(modules=st_module_lists())
    def test_ensure_all_makes_every_artifact_present_and_non_empty(
        self, modules: list[int]
    ) -> None:
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            report = ega.ensure_all(paths)

            assert report.all_satisfied, f"missing: {report.missing}"
            for status in report.artifacts:
                assert status.exists, f"{status.key} does not exist"
                assert status.non_empty, f"{status.key} is empty"
                assert Path(status.path).exists()

    @given(modules=st_module_lists())
    def test_transcript_non_empty_without_any_qa_history(
        self, modules: list[int]
    ) -> None:
        """No Q&A source -> the transcript still exists and is non-empty."""
        with _workspace() as (root, paths):
            # A recap with module sections but no Q&R pairs, and no session log:
            # there is no Q&A history to draw from.
            Path(paths.recap).write_text(
                _recap_text_no_qa(modules), encoding="utf-8"
            )
            assert not Path(paths.log).exists()

            status = ega.ensure_transcript(
                paths.log, paths.recap, paths.transcript
            )

            assert status.exists
            assert status.non_empty
            assert Path(paths.transcript).read_text(encoding="utf-8").strip() != ""


# ===========================================================================
# Property 2: Idempotence / no-op on valid input
# ===========================================================================


class TestIdempotence:
    """A second ``ensure_all`` on a valid workspace changes no file bytes.

    Validates: Requirements 2.5, 2.6
    """

    @given(modules=st_module_lists())
    def test_second_run_is_byte_for_byte_no_op(self, modules: list[int]) -> None:
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            first = ega.ensure_all(paths)
            assert first.all_satisfied, f"missing: {first.missing}"
            before = _snapshot_dir(root)

            second = ega.ensure_all(paths)

            assert second.all_satisfied
            for status in second.artifacts:
                assert status.regenerated is False, f"{status.key} regenerated"
                assert status.error is None
            assert _snapshot_dir(root) == before, "re-run changed the workspace"


# ===========================================================================
# Property 3: Regeneration only when needed, at most once
# ===========================================================================


class TestRegenerationOnlyWhenNeeded:
    """A recap is regenerated iff absent/empty/stale, and at most once per run.

    Validates: Requirements 2.2, 2.3
    """

    @given(modules=st_module_lists(), scenario=st_recap_scenarios())
    def test_recap_regenerated_exactly_when_absent_empty_or_stale(
        self, modules: list[int], scenario: str
    ) -> None:
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)

            if scenario == "absent":
                pass  # recap not written
            elif scenario == "empty":
                Path(paths.recap).write_text("   \n\t\n", encoding="utf-8")
            elif scenario == "stale":
                Path(paths.recap).write_text(
                    _recap_text(modules), encoding="utf-8"
                )
                _set_mtime(paths.recap, _OLD_MTIME)
                _set_mtime(paths.progress, _NEW_MTIME)
            else:  # valid: present, non-empty, and fresh
                Path(paths.recap).write_text(
                    _recap_text(modules), encoding="utf-8"
                )
                _set_mtime(paths.progress, _OLD_MTIME)
                _set_mtime(paths.recap, _NEW_MTIME)

            # Count backfill invocations to prove at-most-once regeneration.
            calls = {"count": 0}
            real_backfill = ega.completion_artifacts.backfill_recap_sections

            def _counting_backfill(*args, **kwargs):
                calls["count"] += 1
                return real_backfill(*args, **kwargs)

            with _patched(
                ega.completion_artifacts,
                "backfill_recap_sections",
                _counting_backfill,
            ):
                status = ega.ensure_recap_md(
                    paths.progress, paths.recap, paths.journal, paths.progress_dir
                )

            expected_regen = scenario != "valid"
            assert status.regenerated is expected_regen, (
                f"scenario={scenario} regenerated={status.regenerated}"
            )
            # At most one regeneration attempt per artifact per run.
            assert calls["count"] <= 1
            if expected_regen:
                assert calls["count"] == 1
            else:
                assert calls["count"] == 0


# ===========================================================================
# Property 4: --check is side-effect free
# ===========================================================================


class TestCheckIsSideEffectFree:
    """``--check`` never writes, and exits 0 iff every artifact is satisfied.

    Validates: Requirements 2.1
    """

    @given(
        modules=st_module_lists(),
        present=st.tuples(st.booleans(), st.booleans(), st.booleans()),
    )
    def test_check_makes_no_writes_and_exit_matches_state(
        self, modules: list[int], present: tuple[bool, bool, bool]
    ) -> None:
        want_recap, want_transcript, want_rendered = present
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            if want_recap:
                Path(paths.recap).write_text(
                    _recap_text(modules), encoding="utf-8"
                )
            if want_transcript:
                # A real transcript requires the recap/log sources; generate it.
                if not Path(paths.recap).is_file():
                    Path(paths.recap).write_text(
                        _recap_text(modules), encoding="utf-8"
                    )
                ega.ensure_transcript(paths.log, paths.recap, paths.transcript)
            if want_rendered:
                if not ega.is_non_empty(Path(paths.recap)):
                    Path(paths.recap).write_text(
                        _recap_text(modules), encoding="utf-8"
                    )
                ega.ensure_rendered_recap(paths.recap, paths.pdf, paths.html)

            # Read-only oracle for the expected exit code (no side effects).
            expected_exit = 0 if ega.check_all(paths).all_satisfied else 1

            before = _snapshot_dir(root)
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = ega.main(_argv(paths, "--check"))
            after = _snapshot_dir(root)

            assert after == before, "--check modified the workspace"
            assert exit_code == expected_exit


# ===========================================================================
# Property 5: Rendered-recap selection
# ===========================================================================


class TestRenderedRecapSelection:
    """fpdf2 available -> PDF; unavailable or PDF-failure -> non-empty HTML.

    Validates: Requirements 4.2, 4.3, 4.8, 2.7
    """

    @given(modules=st_module_lists(), branch=st_render_branches())
    def test_selection_follows_fpdf_availability_and_pdf_outcome(
        self, modules: list[int], branch: str
    ) -> None:
        with _workspace() as (root, paths):
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            stdout = io.StringIO()
            if branch == "no_fpdf":
                patches = [
                    _patched(ega, "_fpdf_available", lambda: False),
                ]
            elif branch == "pdf_fail":
                patches = [
                    _patched(ega, "_fpdf_available", lambda: True),
                    _patched(ega, "_render_recap_pdf", lambda *a, **k: False),
                ]
            else:  # pdf_ok: fpdf available and the PDF chain succeeds
                patches = [
                    _patched(ega, "_fpdf_available", lambda: True),
                    _patched(ega, "_render_recap_pdf", lambda *a, **k: True),
                ]

            with contextlib.ExitStack() as stack:
                for patch in patches:
                    stack.enter_context(patch)
                with contextlib.redirect_stdout(stdout):
                    status = ega.ensure_rendered_recap(
                        paths.recap, paths.pdf, paths.html
                    )

            out = stdout.getvalue()
            if branch == "pdf_ok":
                # PDF selected: reported path is the PDF and it is satisfied.
                assert status.path == paths.pdf
                assert status.exists is True
                assert status.non_empty is True
                assert status.regenerated is True
                assert status.error is None
            else:
                # HTML fallback: a non-empty HTML rendered recap satisfying the
                # rendered-recap invariant, with the appropriate stdout guidance.
                assert status.path == paths.html
                assert status.exists is True
                assert status.non_empty is True
                assert status.error is None
                assert Path(paths.html).is_file()
                assert ega.is_non_empty(Path(paths.html)) is True
                assert not Path(paths.pdf).exists()
                if branch == "no_fpdf":
                    assert "pip install fpdf2" in out
                else:  # pdf_fail
                    assert "PDF rendering failed" in out


# ===========================================================================
# Property 6: Failure isolation
# ===========================================================================


class TestFailureIsolation:
    """One artifact's failure is recorded but never suppresses the others.

    Validates: Requirements 1.9, 3.3, 6.3
    """

    @given(modules=st_module_lists(), target=st_fail_targets())
    def test_one_failure_is_isolated_and_preserves_prior_bytes(
        self, modules: list[int], target: str
    ) -> None:
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)

            def _boom(*args, **kwargs):
                raise RuntimeError("synthetic generator failure")

            if target == "recap":
                # A pre-existing recap with no ``## Module N`` section fails the
                # non-empty(min_body) invariant, forcing a regeneration attempt
                # whose backfill we make raise. Prior bytes must survive.
                original = "# Recap\n\nPrior notes without a module section.\n"
                Path(paths.recap).write_text(original, encoding="utf-8")
                patches = [
                    _patched(
                        ega.completion_artifacts,
                        "backfill_recap_sections",
                        _boom,
                    ),
                ]
            else:  # rendered: force the HTML branch, then make it raise
                Path(paths.recap).write_text(
                    _recap_text(modules), encoding="utf-8"
                )
                original = None
                patches = [
                    _patched(ega, "_fpdf_available", lambda: False),
                    _patched(
                        ega.recap_html_render, "render_markdown_html", _boom
                    ),
                ]

            with contextlib.ExitStack() as stack:
                for patch in patches:
                    stack.enter_context(patch)
                with contextlib.redirect_stdout(io.StringIO()):
                    report = ega.ensure_all(paths)

            by_key = {status.key: status for status in report.artifacts}

            if target == "recap":
                # Recap failed and its prior bytes are untouched (Req 3.3).
                assert by_key["recap_md"].error is not None
                assert by_key["recap_md"].regenerated is False
                assert (
                    Path(paths.recap).read_text(encoding="utf-8") == original
                )
                # The transcript is still generated (isolation, Req 6.3).
                assert by_key["transcript"].exists is True
                assert by_key["transcript"].non_empty is True
            else:
                # Rendered recap failed, yet recap and transcript succeed.
                assert by_key["rendered_recap"].error is not None
                assert by_key["rendered_recap"].non_empty is False
                assert by_key["recap_md"].non_empty is True
                assert by_key["transcript"].exists is True
                assert by_key["transcript"].non_empty is True


# ===========================================================================
# Property 7: Enforcement completeness
# ===========================================================================


class TestEnforcementCompleteness:
    """``all_satisfied`` iff all exist+non_empty; ``missing`` is the exact set.

    Validates: Requirements 2.1, 2.3
    """

    @given(flags=st_status_flag_triples())
    def test_all_satisfied_and_missing_match_the_flags(
        self, flags: list[tuple[bool, bool]]
    ) -> None:
        keys = ega.GUARANTEED_ARTIFACTS
        statuses = [
            ega.ArtifactStatus(
                key=key,
                path=f"/tmp/{key}",
                exists=exists,
                non_empty=non_empty,
            )
            for key, (exists, non_empty) in zip(keys, flags)
        ]
        report = ega.GuaranteeReport(artifacts=statuses)

        expected_satisfied = all(e and n for (e, n) in flags)
        expected_missing = [
            key for key, (e, n) in zip(keys, flags) if not (e and n)
        ]

        assert report.all_satisfied is expected_satisfied
        assert report.missing == expected_missing
        # ``missing`` is empty exactly when everything is satisfied.
        assert (report.missing == []) is expected_satisfied


# ===========================================================================
# Property 8: Self-containment
# ===========================================================================


class TestSelfContainment:
    """Rendered HTML is producible with the standard library alone; no top-level fpdf.

    Validates: Requirements 6.1, 4.5
    """

    class _BlockFpdfFinder:
        """A meta-path finder that makes any ``import fpdf`` raise ImportError."""

        def find_spec(self, name, path=None, target=None):  # noqa: ANN001
            if name == "fpdf" or name.startswith("fpdf."):
                raise ImportError("fpdf is blocked for this self-containment test")
            return None

    @given(modules=st_module_lists())
    def test_html_render_never_requires_fpdf(self, modules: list[int]) -> None:
        with _workspace() as (root, paths):
            recap_md = _recap_text(modules)

            saved_fpdf_mods = {
                name: mod
                for name, mod in list(sys.modules.items())
                if name == "fpdf" or name.startswith("fpdf.")
            }
            for name in saved_fpdf_mods:
                del sys.modules[name]

            finder = self._BlockFpdfFinder()
            sys.meta_path.insert(0, finder)
            try:
                # Rendering the recap to HTML must succeed with fpdf unimportable.
                recap_html_render.render_markdown_html(recap_md, paths.html)
                assert Path(paths.html).is_file()
                assert ega.is_non_empty(Path(paths.html)) is True
                # No lazy import pulled fpdf in along the HTML path.
                assert "fpdf" not in sys.modules
            finally:
                sys.meta_path.remove(finder)
                sys.modules.update(saved_fpdf_mods)

    def test_no_top_level_fpdf_import_in_orchestrator_or_html_render(self) -> None:
        """Neither module imports ``fpdf`` at top level (static source check)."""
        for module in (ega, recap_html_render):
            source = Path(module.__file__).read_text(encoding="utf-8")
            for raw_line in source.splitlines():
                line = raw_line.strip()
                assert not line.startswith("import fpdf"), (
                    f"top-level 'import fpdf' found in {module.__file__}"
                )
                assert not line.startswith("from fpdf"), (
                    f"top-level 'from fpdf' found in {module.__file__}"
                )
