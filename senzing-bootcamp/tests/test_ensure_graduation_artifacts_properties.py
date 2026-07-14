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
    P5 Rendered recap is always PDF  guaranteed-recap-pdf 7.2, 7.4
    P6 Failure isolation             1.9, 3.3, 6.3
    P7 Enforcement completeness      2.1, 2.3
    P8 Self-containment              6.1, 4.5

The guaranteed-recap-pdf feature (task 4.2) supersedes the former two-tier
"PDF when fpdf2 present, HTML fallback otherwise" selection: the rendered recap
is now ALWAYS ``docs/bootcamp_recap.pdf`` via the three-tier strategy (rich
fpdf2 renderer -> guarded autoinstall -> stdlib writer). P5 and the rendered
branch of the failure-isolation property are therefore realigned to the
guaranteed-PDF behavior, and a new guarantee class (``TestGuaranteedPdfWithoutFpdf2``)
covers Requirements 7.2 and 7.4: with fpdf2 simulated absent and autoinstall
disabled the orchestrator still yields a valid PDF, ``--check`` is satisfied only
when the PDF exists (never for HTML alone), and a valid fresh PDF is idempotent.

Example counts come from the active Hypothesis profile (fast=5 locally,
thorough=100 in CI); no test hand-sets ``@settings(max_examples=...)``.

Validates: Requirements 1.1, 2.5, 2.6, 2.7, 7.2, 7.4
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


@contextlib.contextmanager
def _simulate_fpdf2_absent_no_autoinstall():
    """Simulate fpdf2 being unavailable with autoinstall disabled.

    Forces the render strategy down its stdlib-only tier (guaranteed-recap-pdf
    Tier 3): the availability probe returns False, the opt-out resolver returns
    False so no install is attempted (no subprocess, no real network), and the
    guarded installer is neutralised as a defensive backstop. Every patched
    attribute on the shared ``pdf_render_strategy`` module is restored on exit.
    """
    with contextlib.ExitStack() as stack:
        stack.enter_context(
            _patched(ega.pdf_render_strategy, "fpdf2_available", lambda: False)
        )
        stack.enter_context(
            _patched(
                ega.pdf_render_strategy,
                "resolve_allow_autoinstall",
                lambda *args, **kwargs: False,
            )
        )
        stack.enter_context(
            _patched(
                ega.pdf_render_strategy,
                "attempt_autoinstall",
                lambda *args, **kwargs: False,
            )
        )
        yield


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
# Property 5: Rendered recap is always a PDF (guaranteed-recap-pdf)
# ===========================================================================


class TestRenderedRecapIsAlwaysPdf:
    """The rendered recap is ALWAYS the PDF; HTML never substitutes for it.

    Supersedes the former two-tier "PDF when fpdf2 present, HTML fallback
    otherwise" selection. The guaranteed rendered-recap artifact is always
    ``docs/bootcamp_recap.pdf``, produced by the three-tier strategy: the rich
    fpdf2 renderer when fpdf2 is importable, and the stdlib-only writer when it
    is absent and autoinstall is disabled. Whichever tier runs, the artifact is
    a structurally valid PDF at the canonical ``.pdf`` path whose text
    round-trips every module, and no HTML file is ever the artifact that
    satisfies the guarantee.

    Validates: Requirements 7.2, 7.4
    """

    @given(modules=st_module_lists(), fpdf2_present=st.booleans())
    def test_rendered_recap_is_a_pdf_regardless_of_fpdf2(
        self, modules: list[int], fpdf2_present: bool
    ) -> None:
        with _workspace() as (root, paths):
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            with contextlib.ExitStack() as stack:
                if fpdf2_present:
                    # fpdf2 importable -> Tier 1 rich renderer is selected.
                    stack.enter_context(
                        _patched(
                            ega.pdf_render_strategy,
                            "fpdf2_available",
                            lambda: True,
                        )
                    )
                else:
                    # fpdf2 absent + autoinstall off -> Tier 3 stdlib writer.
                    stack.enter_context(_simulate_fpdf2_absent_no_autoinstall())
                with contextlib.redirect_stdout(io.StringIO()):
                    status = ega.ensure_rendered_recap(
                        paths.recap, paths.pdf, paths.html
                    )

            # The guaranteed rendered-recap artifact is always the PDF.
            assert status.path == paths.pdf
            assert status.exists is True
            assert status.non_empty is True
            assert status.regenerated is True
            assert status.error is None

            # A structurally valid PDF whose text round-trips every module.
            pdf_bytes = Path(paths.pdf).read_bytes()
            assert pdf_bytes.startswith(b"%PDF-")
            text = ega.recap_pdf_render.extract_pdf_text(pdf_bytes)
            for module in modules:
                assert f"Module {module}" in text

            # HTML never substitutes for the PDF guarantee.
            assert not Path(paths.html).exists()


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
            else:  # rendered: force the guaranteed PDF render to fail
                # The rendered recap is always produced through the three-tier
                # strategy, so failure is injected at the strategy entry point
                # (referenced by the orchestrator as the module attribute
                # ``pdf_render_strategy.ensure_recap_pdf``). No PDF is published
                # because the render targets a temp file cleaned up on failure.
                Path(paths.recap).write_text(
                    _recap_text(modules), encoding="utf-8"
                )
                original = None
                patches = [
                    _patched(
                        ega.pdf_render_strategy, "ensure_recap_pdf", _boom
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
                # A failed render publishes no PDF (temp file is cleaned up).
                assert not Path(paths.pdf).exists()
                assert by_key["recap_md"].non_empty is True
                assert by_key["transcript"].exists is True
                assert by_key["transcript"].non_empty is True


# ===========================================================================
# Guaranteed PDF even without fpdf2 (guaranteed-recap-pdf, task 4.2)
# ===========================================================================


class TestGuaranteedPdfWithoutFpdf2:
    """A valid ``docs/bootcamp_recap.pdf`` is guaranteed even without fpdf2.

    With fpdf2 simulated unavailable AND autoinstall disabled (the stdlib Tier 3
    path, no real install), the orchestrator still yields a structurally valid
    PDF whose text round-trips the recap's module content; ``--check`` is
    unsatisfied for the rendered recap when only an HTML file exists and
    satisfied once the valid PDF exists; and a valid, fresh PDF is left
    byte-for-byte unchanged on a re-run (idempotent no-op).

    Validates: Requirements 7.2, 7.4
    """

    @given(modules=st_module_lists())
    def test_orchestrator_yields_valid_pdf_when_fpdf2_absent(
        self, modules: list[int]
    ) -> None:
        """fpdf2 absent + autoinstall off -> ``ensure_all`` still writes a PDF."""
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.ExitStack() as stack:
                stack.enter_context(_simulate_fpdf2_absent_no_autoinstall())
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(stderr):
                        report = ega.ensure_all(paths)

            assert report.all_satisfied, f"missing: {report.missing}"
            rendered = next(
                s for s in report.artifacts if s.key == "rendered_recap"
            )
            # The guaranteed artifact is the PDF, produced by the stdlib tier.
            assert rendered.path == paths.pdf
            assert rendered.exists is True
            assert rendered.non_empty is True
            assert rendered.error is None
            assert "tier: stdlib" in stderr.getvalue()

            # Structurally valid PDF whose text round-trips every module.
            pdf_bytes = Path(paths.pdf).read_bytes()
            assert pdf_bytes.startswith(b"%PDF-")
            text = ega.recap_pdf_render.extract_pdf_text(pdf_bytes)
            for module in modules:
                assert f"Module {module}" in text

            # HTML is never the artifact that satisfies the guarantee.
            assert not Path(paths.html).exists()

    @given(modules=st_module_lists())
    def test_check_unsatisfied_with_only_html_and_satisfied_with_pdf(
        self, modules: list[int]
    ) -> None:
        """``--check`` sees rendered recap satisfied only when the PDF exists."""
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")
            # Satisfy the other two artifacts so the rendered recap is isolated.
            with contextlib.redirect_stdout(io.StringIO()):
                ega.ensure_transcript(paths.log, paths.recap, paths.transcript)

            # Only an HTML file exists (no PDF) -> rendered recap UNSATISFIED.
            Path(paths.html).write_text(
                "<html><body>recap</body></html>\n", encoding="utf-8"
            )
            assert not Path(paths.pdf).exists()

            html_only = ega.check_all(paths)
            html_by_key = {s.key: s for s in html_only.artifacts}
            assert html_by_key["rendered_recap"].exists is False
            assert html_by_key["rendered_recap"].non_empty is False
            assert "rendered_recap" in html_only.missing
            assert html_only.all_satisfied is False
            # main --check exits non-zero while the PDF is absent.
            with contextlib.redirect_stdout(io.StringIO()):
                assert ega.main(_argv(paths, "--check")) == 1

            # Produce a valid PDF via the stdlib tier -> rendered recap SATISFIED.
            with contextlib.ExitStack() as stack:
                stack.enter_context(_simulate_fpdf2_absent_no_autoinstall())
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(io.StringIO()):
                        ega.ensure_rendered_recap(
                            paths.recap, paths.pdf, paths.html
                        )

            with_pdf = ega.check_all(paths)
            pdf_by_key = {s.key: s for s in with_pdf.artifacts}
            assert pdf_by_key["rendered_recap"].exists is True
            assert pdf_by_key["rendered_recap"].non_empty is True
            assert "rendered_recap" not in with_pdf.missing
            assert with_pdf.all_satisfied is True
            # main --check now succeeds (exit 0) and made no writes.
            before = _snapshot_dir(root)
            with contextlib.redirect_stdout(io.StringIO()):
                assert ega.main(_argv(paths, "--check")) == 0
            assert _snapshot_dir(root) == before

    @given(modules=st_module_lists())
    def test_valid_fresh_stdlib_pdf_is_idempotent(
        self, modules: list[int]
    ) -> None:
        """A valid, fresh stdlib PDF is left byte-for-byte unchanged on re-run."""
        with _workspace() as (root, paths):
            _seed_progress(paths, modules)
            Path(paths.recap).write_text(_recap_text(modules), encoding="utf-8")

            with contextlib.ExitStack() as stack:
                stack.enter_context(_simulate_fpdf2_absent_no_autoinstall())
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(io.StringIO()):
                        first = ega.ensure_rendered_recap(
                            paths.recap, paths.pdf, paths.html
                        )
            assert first.regenerated is True
            assert Path(paths.pdf).exists()
            before = Path(paths.pdf).read_bytes()

            # A second run over the valid, fresh PDF regenerates nothing.
            with contextlib.ExitStack() as stack:
                stack.enter_context(_simulate_fpdf2_absent_no_autoinstall())
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(io.StringIO()):
                        second = ega.ensure_rendered_recap(
                            paths.recap, paths.pdf, paths.html
                        )

            assert second.regenerated is False
            assert second.error is None
            assert second.exists is True
            assert second.non_empty is True
            assert Path(paths.pdf).read_bytes() == before


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
