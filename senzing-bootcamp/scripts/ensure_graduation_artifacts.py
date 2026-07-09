#!/usr/bin/env python3
"""Guarantee the bootcamp's crown-jewel graduation artifacts exist and are valid.

This self-contained, stdlib-only orchestrator guarantees that the three
crown-jewel deliverables are present and non-empty at any stopping point:

- the Q&A transcript (``docs/bootcamp_transcript.md``),
- the recap Markdown (``docs/bootcamp_recap.md``), and
- a rendered recap document (``docs/bootcamp_recap.pdf`` or its HTML fallback
  ``docs/bootcamp_recap.html``).

It reconstructs each artifact from always-present sources by reusing the
existing reconcile/backfill/render helpers, and only regenerates when an
artifact is absent, empty, or stale (idempotent otherwise). All logic is
reachable without any bundled *generation* script being materialized, and
``fpdf`` is imported lazily by the sibling render modules (never at this
module's top level).

Usage examples::

    # Ensure/regenerate as needed; human-readable summary; exit 0/1.
    python scripts/ensure_graduation_artifacts.py

    # Verify only, no regeneration; exit 1 naming missing artifacts.
    python scripts/ensure_graduation_artifacts.py --check

    # Emit the GuaranteeReport as JSON (consumed by the hook and tests).
    python scripts/ensure_graduation_artifacts.py --json

This task (3.1) provides the core data model and the ``is_non_empty`` /
``is_stale`` helpers plus the sibling-module import scaffolding. The
``ensure_transcript`` / ``ensure_recap_md`` / ``ensure_rendered_recap`` /
``ensure_all`` / ``main`` functions are filled in by later tasks (3.2-3.5).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path insertion so sibling scripts import cleanly (scripts are not a
# package). Mirrors the repo convention used across senzing-bootcamp/scripts.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts  # noqa: E402  (path manipulated above)
import generate_recap_pdf  # noqa: E402  (path manipulated above)
import generate_recap_pdf_inline  # noqa: E402  (path manipulated above)
import generate_transcript  # noqa: E402  (path manipulated above)
import recap_html_render  # noqa: E402  (path manipulated above)
import recap_pdf_render  # noqa: E402  (path manipulated above)
import reconcile_transcript  # noqa: E402  (path manipulated above)

# The three crown-jewel deliverables this orchestrator guarantees, in report
# order: the Q&A transcript, the recap Markdown, and the rendered recap.
GUARANTEED_ARTIFACTS = ("transcript", "recap_md", "rendered_recap")

# Matches a canonical recap module heading ``## Module N ...`` (Req 3.1). The
# recap is only considered non-empty for ``min_body`` purposes when at least one
# such section is present.
_MODULE_SECTION_RE = re.compile(r"^##\s+Module\s+\d+\b", re.MULTILINE)

# Emitted to stdout when the rendered recap falls back to HTML because the
# optional fpdf2 dependency is unavailable (Req 4.4). It states the exact
# command required to install fpdf2 so the bootcamper can enable PDF rendering.
_FPDF_INSTALL_HINT = (
    "fpdf2 is not installed; rendered the recap as HTML instead. "
    "To enable PDF rendering, install it with: pip install fpdf2"
)

# Emitted to stdout when fpdf2 is available but PDF rendering failed and the
# HTML rendered recap was produced instead (Req 4.8).
_PDF_FAILED_HINT = (
    "PDF rendering failed; produced the HTML rendered recap "
    "(docs/bootcamp_recap.html) instead."
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ArtifactPaths:
    """Resolved, overridable canonical paths for every guaranteed artifact.

    Defaults match the values already used across the bootcamp scripts, so the
    orchestrator operates on the same files the existing generators read and
    write. Every path is overridable from the CLI for tests and non-default
    workspaces.

    Attributes:
        log: Session log JSONL source (`config/session_log.jsonl`).
        recap: Recap Markdown artifact (`docs/bootcamp_recap.md`).
        transcript: Q&A transcript artifact (`docs/bootcamp_transcript.md`).
        progress: Progress JSON source (`config/bootcamp_progress.json`).
        journal: Deprecated no-op retained for signature compatibility; defaults
            to the recap path (`docs/bootcamp_recap.md`) since journal content is
            now part of the consolidated recap.
        progress_dir: Per-module artifacts directory (`docs/progress`).
        pdf: Rendered PDF output (`docs/bootcamp_recap.pdf`).
        html: Rendered HTML fallback output (`docs/bootcamp_recap.html`).
    """

    log: str = "config/session_log.jsonl"
    recap: str = "docs/bootcamp_recap.md"
    transcript: str = "docs/bootcamp_transcript.md"
    progress: str = "config/bootcamp_progress.json"
    journal: str = "docs/bootcamp_recap.md"
    progress_dir: str = "docs/progress"
    pdf: str = "docs/bootcamp_recap.pdf"
    html: str = "docs/bootcamp_recap.html"


@dataclass
class ArtifactStatus:
    """The outcome of ensuring a single guaranteed artifact.

    Attributes:
        key: The artifact identity (one of :data:`GUARANTEED_ARTIFACTS`).
        path: The resolved output path (`rendered_recap` is the `.pdf` or
            `.html` actually produced).
        exists: Whether the artifact exists on disk.
        non_empty: Whether the artifact satisfies the non-empty invariant.
        regenerated: Whether this run (re)generated the artifact.
        error: A human-readable error when regeneration failed, else ``None``.
    """

    key: str
    path: str
    exists: bool
    non_empty: bool
    regenerated: bool = False
    error: str | None = None


@dataclass
class GuaranteeReport:
    """Aggregate result of ensuring every guaranteed artifact.

    Attributes:
        artifacts: One :class:`ArtifactStatus` per guaranteed artifact, in
            :data:`GUARANTEED_ARTIFACTS` order.
    """

    artifacts: list[ArtifactStatus] = field(default_factory=list)

    @property
    def all_satisfied(self) -> bool:
        """Return ``True`` iff every artifact exists and is non-empty."""
        return bool(self.artifacts) and all(
            status.exists and status.non_empty for status in self.artifacts
        )

    @property
    def missing(self) -> list[str]:
        """Return the keys of every artifact that is not satisfied.

        An artifact is unsatisfied when it does not exist or is not non-empty;
        this is the exact set the enforcement hook blocks completion on.
        """
        return [
            status.key
            for status in self.artifacts
            if not (status.exists and status.non_empty)
        ]


# ---------------------------------------------------------------------------
# Non-emptiness and staleness helpers
# ---------------------------------------------------------------------------


def is_non_empty(path: Path, *, min_body: bool = False) -> bool:
    """Return whether ``path`` satisfies the non-empty invariant.

    The base rule (Req 2.1) is that the file exists and contains at least one
    non-whitespace character. The ``min_body`` flag applies the stricter,
    content-aware body check whose form depends on the artifact type:

    - For a rendered PDF (``.pdf`` suffix) it reuses the ``recap_pdf_render``
      round-trip machinery: the PDF's text is extracted and must carry at least
      :data:`recap_pdf_render.MIN_BODY_LINES` non-blank body lines, catching the
      outline-only / dropped-content PDF (Req 4.1).
    - For the recap Markdown it additionally requires at least one
      ``## Module N`` section (Req 3.1).

    Args:
        path: The artifact path to inspect.
        min_body: When ``True``, apply the stricter body check described above.

    Returns:
        ``True`` when the artifact is non-empty (and, when ``min_body`` is set,
        carries sufficient body content), else ``False``.
    """
    if not path.is_file():
        return False

    # Rendered PDF: binary content, verified via text round-trip extraction.
    if path.suffix.lower() == ".pdf":
        try:
            pdf_bytes = path.read_bytes()
        except OSError:
            return False
        if not pdf_bytes.strip():
            return False
        if not min_body:
            return True
        text = recap_pdf_render.extract_pdf_text(pdf_bytes)
        body_lines = [line for line in text.splitlines() if line.strip()]
        return len(body_lines) >= recap_pdf_render.MIN_BODY_LINES

    # Text artifact (transcript / recap Markdown / HTML fallback).
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if not content.strip():
        return False
    if min_body:
        return bool(_MODULE_SECTION_RE.search(content))
    return True


def is_stale(artifact: Path, sources: list[Path]) -> bool:
    """Return whether ``artifact`` is stale relative to its ``sources``.

    An artifact is stale when its last-modified time is earlier than the newest
    last-modified time among its source inputs (Req 2.2). An absent artifact is
    treated as stale (it must be produced). Sources that do not exist are
    ignored; a directory source contributes the newest mtime among the files it
    contains (so per-module artifacts under ``docs/progress`` are accounted
    for). When no source exists, the artifact cannot be stale.

    Args:
        artifact: The artifact whose freshness is being checked.
        sources: The source inputs the artifact is derived from (files or
            directories).

    Returns:
        ``True`` when the artifact is absent or older than its newest source,
        else ``False``.
    """
    if not artifact.exists():
        return True
    try:
        artifact_mtime = artifact.stat().st_mtime
    except OSError:
        return True

    newest_source_mtime: float | None = None
    for source in sources:
        mtime = _newest_mtime(source)
        if mtime is not None and (
            newest_source_mtime is None or mtime > newest_source_mtime
        ):
            newest_source_mtime = mtime

    if newest_source_mtime is None:
        return False
    return artifact_mtime < newest_source_mtime


def _newest_mtime(path: Path) -> float | None:
    """Return the newest mtime for ``path`` (a file or directory), or ``None``.

    For a regular file this is the file's own mtime. For a directory it is the
    newest mtime among all files nested beneath it, so a directory of per-module
    artifacts contributes the freshest member. Missing or unreadable paths
    return ``None`` and are ignored by :func:`is_stale`.

    Args:
        path: A source file or directory.

    Returns:
        The newest mtime as a POSIX timestamp, or ``None`` when nothing readable
        exists at ``path``.
    """
    try:
        if path.is_file():
            return path.stat().st_mtime
        if path.is_dir():
            newest: float | None = None
            for child in path.rglob("*"):
                if child.is_file():
                    try:
                        mtime = child.stat().st_mtime
                    except OSError:
                        continue
                    if newest is None or mtime > newest:
                        newest = mtime
            return newest
    except OSError:
        return None
    return None


# ---------------------------------------------------------------------------
# Per-artifact guarantees
# ---------------------------------------------------------------------------


def ensure_transcript(log: str, recap: str, output: str) -> ArtifactStatus:
    """Guarantee the Q&A transcript exists and is non-empty (Req 1).

    The transcript (``docs/bootcamp_transcript.md``) is left untouched when it
    is already present, non-empty, and not stale relative to its always-present
    sources — ``config/session_log.jsonl`` and ``docs/bootcamp_recap.md`` — so
    repeated stopping points are a no-op (Req 2.5, 2.6).

    Otherwise the transcript is reconstructed without depending on any bundled
    generation script (Req 1.2): first ``reconcile_transcript.main`` backfills
    the session log from the recap's ``### Questions & Responses`` pairs when
    the log is short (Req 1.3, 1.4), then ``generate_transcript.main`` renders
    the transcript in ``--ensure`` mode. Ensure mode orders module sections and
    their Q&R pairs (Req 1.5, 1.6) and always writes a Non_Empty document: a
    normal transcript when Q&A pairs exist, or an explicit "no Q&A history was
    available" record when none do (Req 1.7, 1.8).

    Both sibling entry points are non-destructive on failure: the reconcile pass
    is non-blocking, and the renderer writes atomically, so a failed render
    leaves any existing transcript unchanged. Any failure is captured and
    surfaced as the returned status' ``error`` rather than raised (Req 1.9).

    Args:
        log: Path to the JSONL session log source.
        recap: Path to the recap Markdown source.
        output: Path to write (or verify) the transcript artifact.

    Returns:
        An :class:`ArtifactStatus` with ``key="transcript"`` describing whether
        the transcript exists, is non-empty, was regenerated this run, and any
        error encountered while regenerating.
    """
    transcript_path = Path(output)
    sources = [Path(log), Path(recap)]

    # No-op when the transcript is already present, non-empty, and fresh.
    if (
        transcript_path.is_file()
        and is_non_empty(transcript_path)
        and not is_stale(transcript_path, sources)
    ):
        return ArtifactStatus(
            key="transcript",
            path=str(transcript_path),
            exists=True,
            non_empty=True,
            regenerated=False,
            error=None,
        )

    # Reconstruct: backfill the log from recap Q&R pairs, then render in ensure
    # mode so a Non_Empty transcript is always written.
    error: str | None = None
    try:
        reconcile_transcript.main(["--recap", recap, "--log", log])
        rc = generate_transcript.main(
            ["--log", log, "--output", output, "--ensure"]
        )
        if rc != 0:
            error = (
                f"transcript render failed (generate_transcript exited {rc}); "
                "existing transcript left unchanged"
            )
    except Exception as exc:  # noqa: BLE001 - preserve existing artifact, record error (Req 1.9)
        error = f"transcript reconstruction failed: {exc}"

    exists = transcript_path.is_file()
    non_empty = is_non_empty(transcript_path)
    return ArtifactStatus(
        key="transcript",
        path=str(transcript_path),
        exists=exists,
        non_empty=non_empty,
        regenerated=error is None and exists and non_empty,
        error=error,
    )


def _progress_readable(progress_path: Path) -> bool:
    """Return whether ``progress_path`` exists and parses as JSON.

    The recap reconstruction reads ``config/bootcamp_progress.json`` for the
    completed-module list and step timing. A progress file that is absent or
    whose contents do not parse is treated as an unavailable source (Req 3.3).

    Args:
        progress_path: Path to the bootcamp progress JSON source.

    Returns:
        ``True`` when the file exists and its contents parse as JSON, else
        ``False``.
    """
    if not progress_path.is_file():
        return False
    try:
        json.loads(progress_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return True


def _has_module_artifacts(progress_dir: Path) -> bool:
    """Return whether ``progress_dir`` holds at least one readable file.

    Per-module artifacts live under ``docs/progress`` and are the secondary
    reconstruction source for the recap (Req 3.2). Any regular file nested
    beneath the directory counts; an absent or empty directory means no module
    artifacts are available (Req 3.3).

    Args:
        progress_dir: Path to the per-module artifacts directory.

    Returns:
        ``True`` when at least one regular file exists under ``progress_dir``,
        else ``False``.
    """
    if not progress_dir.is_dir():
        return False
    try:
        for child in progress_dir.rglob("*"):
            if child.is_file():
                return True
    except OSError:
        return False
    return False


def ensure_recap_md(
    progress: str, recap: str, journal: str, progress_dir: str
) -> ArtifactStatus:
    """Guarantee the recap Markdown exists and is non-empty (Req 3).

    The recap (``docs/bootcamp_recap.md``) is left untouched when it is already
    present, non-empty (has at least one ``## Module N`` section), and not stale
    relative to its always-present sources — ``config/bootcamp_progress.json``
    and the per-module artifacts under ``docs/progress`` — so repeated stopping
    points are a no-op (Req 3.1, 2.5, 2.6).

    Otherwise the recap is reconstructed without depending on any bundled
    generation script (Req 3.2) by delegating to
    :func:`completion_artifacts.backfill_recap_sections`, which appends any
    missing per-module ``## Module N: [Name] \u2014 [timestamp]`` section (each
    carrying its ``### Information Shared`` / ``### Questions & Responses`` /
    ``### Actions Taken`` subsections) in ascending completion order while
    preserving existing recap bytes exactly (Req 3.4-3.8).

    When both reconstruction sources are unavailable — the progress JSON is
    absent or unreadable *and* no per-module artifacts exist — any existing
    recap is left unchanged and a source-unavailable error is recorded rather
    than raised (Req 3.3). Any other failure during reconstruction is likewise
    captured as the returned status' ``error`` and leaves the existing recap
    untouched.

    Args:
        progress: Path to the bootcamp progress JSON source.
        recap: Path to write (or verify) the recap Markdown artifact.
        journal: Deprecated no-op accepted for signature compatibility; journal
            content is now part of the consolidated recap and this value is
            unused.
        progress_dir: Path to the per-module artifacts directory.

    Returns:
        An :class:`ArtifactStatus` with ``key="recap_md"`` describing whether
        the recap exists, is non-empty (with at least one ``## Module N``
        section), was regenerated this run, and any error encountered.
    """
    del journal  # deprecated no-op; retained for signature compatibility only

    recap_path = Path(recap)
    progress_path = Path(progress)
    progress_dir_path = Path(progress_dir)
    sources = [progress_path, progress_dir_path]

    # No-op when the recap is already present, non-empty, and fresh.
    if (
        recap_path.is_file()
        and is_non_empty(recap_path, min_body=True)
        and not is_stale(recap_path, sources)
    ):
        return ArtifactStatus(
            key="recap_md",
            path=str(recap_path),
            exists=True,
            non_empty=True,
            regenerated=False,
            error=None,
        )

    # Reconstruction is required. When neither the progress JSON nor any
    # per-module artifact is available, leave any existing recap unchanged and
    # record the source-unavailable error (Req 3.3).
    error: str | None = None
    if not _progress_readable(progress_path) and not _has_module_artifacts(
        progress_dir_path
    ):
        error = (
            "recap source data unavailable: neither "
            f"'{progress}' nor per-module artifacts under '{progress_dir}' "
            "are readable; existing recap left unchanged"
        )
    else:
        # Reconstruct by appending any missing per-module sections in place,
        # preserving existing recap bytes exactly.
        try:
            completion_artifacts.backfill_recap_sections(
                progress,
                recap,
                progress_dir=progress_dir,
            )
        except Exception as exc:  # noqa: BLE001 - preserve existing artifact, record error (Req 3.3)
            error = f"recap reconstruction failed: {exc}"

    exists = recap_path.is_file()
    non_empty = is_non_empty(recap_path, min_body=True)
    return ArtifactStatus(
        key="recap_md",
        path=str(recap_path),
        exists=exists,
        non_empty=non_empty,
        regenerated=error is None and exists and non_empty,
        error=error,
    )


def _fpdf_available() -> bool:
    """Return whether the optional ``fpdf2`` package is importable.

    Uses :func:`importlib.util.find_spec` so availability is probed without
    importing ``fpdf`` at this module's top level (Req 4.5, 6.1). The actual
    import stays lazy inside the sibling render modules.

    Returns:
        ``True`` when a spec for the ``fpdf`` module can be located, else
        ``False``.
    """
    try:
        return importlib.util.find_spec("fpdf") is not None
    except (ImportError, ValueError):
        return False


def _render_recap_pdf(recap: str, pdf_out: str) -> bool:
    """Attempt to render the recap PDF via the existing generator chain.

    Tries the bundled ``generate_recap_pdf`` entry point first, then the
    self-contained ``generate_recap_pdf_inline`` fallback, mirroring the
    graduation flow's PDF chain. A PDF is considered produced only when a
    generator returns exit code 0 *and* the written file passes the stricter
    round-trip body check (:func:`is_non_empty` with ``min_body=True``), so an
    outline-only or dropped-content PDF is treated as a failure. Any exception
    raised by a generator is swallowed and treated as that generator failing, so
    a missing dependency or render error never escapes as a traceback.

    Args:
        recap: Path to the recap Markdown source.
        pdf_out: Path for the rendered PDF output.

    Returns:
        ``True`` when a valid, non-empty PDF was written to ``pdf_out``, else
        ``False``.
    """
    pdf_path = Path(pdf_out)
    for renderer in (generate_recap_pdf, generate_recap_pdf_inline):
        try:
            rc = renderer.main(["--input", recap, "--output", pdf_out])
        except Exception:  # noqa: BLE001 - a failed renderer must not escape; try the next
            rc = 1
        if rc == 0 and is_non_empty(pdf_path, min_body=True):
            return True
    return False


def ensure_rendered_recap(recap: str, pdf_out: str, html_out: str) -> ArtifactStatus:
    """Guarantee a rendered recap document exists and is non-empty (Req 4).

    A rendered recap is only produced when the recap Markdown source
    (``docs/bootcamp_recap.md``) is non-empty. When the source is absent or
    empty, no rendered recap is produced and a source-unavailable error is
    emitted to stdout (Req 4.7); the returned status carries that error and no
    artifact.

    When the source is non-empty, the renderer selects the output form by the
    availability of the optional ``fpdf2`` dependency:

    - **``fpdf2`` available** -> attempt the existing PDF chain
      (``generate_recap_pdf`` then ``generate_recap_pdf_inline``). On success the
      rendered recap is ``docs/bootcamp_recap.pdf``, verified with the stricter
      round-trip body check (Req 4.1, 4.2). An already-present PDF that is
      non-empty and not stale relative to the recap source is left byte-for-byte
      unchanged (Req 2.5, 2.6).
    - **``fpdf2`` unavailable** -> skip the PDF chain and render
      ``docs/bootcamp_recap.html`` via
      :func:`recap_html_render.render_markdown_html`, emitting the exact
      ``pip install fpdf2`` hint to stdout (Req 4.3, 4.4). A fresh, non-empty
      HTML fallback is likewise left unchanged.
    - **``fpdf2`` available but PDF rendering fails** -> fall back to the HTML
      rendered recap and emit a note that PDF rendering failed and HTML was
      produced instead (Req 4.8).

    ``fpdf`` is never imported at this module's top level; availability is probed
    with :func:`importlib.util.find_spec` and the actual import stays lazy inside
    the sibling render modules (Req 4.5, 6.1).

    Args:
        recap: Path to the recap Markdown source.
        pdf_out: Path for the rendered PDF output.
        html_out: Path for the HTML fallback output.

    Returns:
        An :class:`ArtifactStatus` with ``key="rendered_recap"`` whose ``path``
        is the ``.pdf`` or ``.html`` actually selected, describing whether the
        rendered recap exists, is non-empty, was regenerated this run, and any
        error encountered.
    """
    recap_path = Path(recap)
    pdf_path = Path(pdf_out)
    html_path = Path(html_out)
    sources = [recap_path]

    # Source guard (Req 4.7): produce nothing when the recap Markdown source is
    # absent or empty, and surface the source-unavailable error on stdout. The
    # reported path is the canonical PDF path since no rendered form was chosen.
    if not is_non_empty(recap_path):
        error = (
            f"recap source unavailable: '{recap}' is absent or empty; "
            "no rendered recap produced"
        )
        print(error)
        return ArtifactStatus(
            key="rendered_recap",
            path=str(pdf_path),
            exists=False,
            non_empty=False,
            regenerated=False,
            error=error,
        )

    fpdf_available = _fpdf_available()

    # No-op when a valid, fresh rendered recap in the preferred form already
    # exists, preserving byte-for-byte idempotence across repeated runs
    # (Req 2.5, 2.6). The preferred form follows fpdf2 availability (Property 5):
    # PDF when fpdf2 is present, otherwise the HTML fallback.
    if fpdf_available:
        if is_non_empty(pdf_path, min_body=True) and not is_stale(
            pdf_path, sources
        ):
            return ArtifactStatus(
                key="rendered_recap",
                path=str(pdf_path),
                exists=True,
                non_empty=True,
                regenerated=False,
                error=None,
            )
    else:
        if is_non_empty(html_path) and not is_stale(html_path, sources):
            return ArtifactStatus(
                key="rendered_recap",
                path=str(html_path),
                exists=True,
                non_empty=True,
                regenerated=False,
                error=None,
            )

    # Attempt the PDF chain only when fpdf2 could satisfy it. A successful,
    # verified PDF is the rendered recap (Req 4.2).
    pdf_failed = False
    if fpdf_available:
        if _render_recap_pdf(recap, pdf_out):
            return ArtifactStatus(
                key="rendered_recap",
                path=str(pdf_path),
                exists=True,
                non_empty=True,
                regenerated=True,
                error=None,
            )
        pdf_failed = True

    # HTML fallback (Req 4.3): reached when fpdf2 is unavailable or the PDF chain
    # failed. Render the recap Markdown to a self-contained HTML document.
    error: str | None = None
    try:
        content = recap_path.read_text(encoding="utf-8")
        recap_html_render.render_markdown_html(content, html_out)
    except Exception as exc:  # noqa: BLE001 - record failure instead of raising (Req 4.3)
        error = f"HTML rendered recap failed: {exc}"

    # Emit the appropriate stdout guidance: the exact install hint when fpdf2 is
    # absent (Req 4.4), or the PDF-failed note when fpdf2 was present but the PDF
    # chain failed (Req 4.8).
    if not fpdf_available:
        print(_FPDF_INSTALL_HINT)
    elif pdf_failed:
        print(_PDF_FAILED_HINT)

    exists = html_path.is_file()
    non_empty = is_non_empty(html_path)
    return ArtifactStatus(
        key="rendered_recap",
        path=str(html_path),
        exists=exists,
        non_empty=non_empty,
        regenerated=error is None and exists and non_empty,
        error=error,
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def ensure_all(paths: ArtifactPaths) -> GuaranteeReport:
    """Ensure every guaranteed artifact and aggregate the result (Req 2, 6.3).

    Runs the three per-artifact guarantees, each of which regenerates its
    artifact at most once (Req 2.3). Because the transcript reconstruction can
    read the recap's ``### Questions & Responses`` pairs and the rendered recap
    is derived from the recap Markdown, the recap Markdown is ensured *first* so
    the downstream artifacts see the freshest source; execution order is
    therefore ``recap_md`` -> ``transcript`` -> ``rendered_recap``.

    Each guarantee is isolated: a failure generating one artifact records an
    error on that artifact's status and never prevents the others from running
    (Req 6.3). Should a guarantee raise unexpectedly, the exception is captured
    as that artifact's error rather than propagated, so ``ensure_all`` always
    returns a complete report.

    The returned report's ``artifacts`` list is ordered by
    :data:`GUARANTEED_ARTIFACTS` (``transcript``, ``recap_md``,
    ``rendered_recap``) so the JSON contract is stable regardless of execution
    order.

    Args:
        paths: The resolved, overridable canonical artifact paths.

    Returns:
        A :class:`GuaranteeReport` carrying one :class:`ArtifactStatus` per
        guaranteed artifact, in :data:`GUARANTEED_ARTIFACTS` order.
    """
    statuses: dict[str, ArtifactStatus] = {}

    # Recap Markdown first: it is a source for both the transcript
    # reconstruction and the rendered recap, so it must be freshest.
    statuses["recap_md"] = _guard(
        "recap_md",
        paths.recap,
        lambda: ensure_recap_md(
            paths.progress, paths.recap, paths.journal, paths.progress_dir
        ),
    )
    statuses["transcript"] = _guard(
        "transcript",
        paths.transcript,
        lambda: ensure_transcript(paths.log, paths.recap, paths.transcript),
    )
    statuses["rendered_recap"] = _guard(
        "rendered_recap",
        paths.pdf,
        lambda: ensure_rendered_recap(paths.recap, paths.pdf, paths.html),
    )

    return GuaranteeReport(
        artifacts=[statuses[key] for key in GUARANTEED_ARTIFACTS]
    )


def _guard(key: str, fallback_path: str, fn) -> ArtifactStatus:
    """Run an ensure function, converting any raised exception into a status.

    Failure isolation (Req 6.3) requires that an unexpected exception from one
    guarantee never suppresses the others. Each ensure function already records
    per-artifact failures in its returned status; this wrapper is the last line
    of defence for an exception that escapes one entirely.

    Args:
        key: The artifact identity for the resulting status.
        fallback_path: The path to report when the guarantee raises before
            returning a status.
        fn: A zero-argument callable invoking the per-artifact guarantee.

    Returns:
        The guarantee's :class:`ArtifactStatus`, or a synthesized error status
        when the guarantee raised.
    """
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - isolate failures across artifacts (Req 6.3)
        return ArtifactStatus(
            key=key,
            path=fallback_path,
            exists=False,
            non_empty=False,
            regenerated=False,
            error=f"{key} guarantee raised: {exc}",
        )


def check_all(paths: ArtifactPaths) -> GuaranteeReport:
    """Verify every guaranteed artifact without any side effects (Req 2.1).

    This is the read-only counterpart to :func:`ensure_all`: it computes the
    existence and non-emptiness of each artifact *without* invoking any of the
    ensure/regeneration functions, so it never creates, modifies, or deletes a
    file. It is what the ``--check`` CLI path uses to confirm the completion
    invariant holds.

    The rendered-recap form is selected the same way
    :func:`ensure_rendered_recap` selects it: the ``.pdf`` is checked when
    ``fpdf2`` is available, otherwise the ``.html`` fallback, so ``--check``
    agrees with what a real run would produce (Property 5).

    Args:
        paths: The resolved, overridable canonical artifact paths.

    Returns:
        A :class:`GuaranteeReport` reflecting the current on-disk state, in
        :data:`GUARANTEED_ARTIFACTS` order.
    """
    transcript_path = Path(paths.transcript)
    recap_path = Path(paths.recap)
    rendered_path = Path(paths.pdf) if _fpdf_available() else Path(paths.html)

    transcript_status = ArtifactStatus(
        key="transcript",
        path=str(transcript_path),
        exists=transcript_path.is_file(),
        non_empty=is_non_empty(transcript_path),
        regenerated=False,
        error=None,
    )
    recap_status = ArtifactStatus(
        key="recap_md",
        path=str(recap_path),
        exists=recap_path.is_file(),
        non_empty=is_non_empty(recap_path, min_body=True),
        regenerated=False,
        error=None,
    )
    rendered_status = ArtifactStatus(
        key="rendered_recap",
        path=str(rendered_path),
        exists=rendered_path.is_file(),
        non_empty=is_non_empty(
            rendered_path, min_body=rendered_path.suffix.lower() == ".pdf"
        ),
        regenerated=False,
        error=None,
    )

    by_key = {
        "transcript": transcript_status,
        "recap_md": recap_status,
        "rendered_recap": rendered_status,
    }
    return GuaranteeReport(
        artifacts=[by_key[key] for key in GUARANTEED_ARTIFACTS]
    )


# ---------------------------------------------------------------------------
# Report serialization and CLI
# ---------------------------------------------------------------------------


def _report_to_dict(report: GuaranteeReport) -> dict:
    """Serialize a :class:`GuaranteeReport` to the JSON contract shape.

    The shape matches the design's hook/test contract: a top-level
    ``all_satisfied`` boolean, a ``missing`` list of unsatisfied artifact keys,
    and an ``artifacts`` list of per-artifact objects carrying
    ``key``/``path``/``exists``/``non_empty``/``regenerated``/``error``.

    Args:
        report: The report to serialize.

    Returns:
        A JSON-serializable dictionary describing the report.
    """
    return {
        "all_satisfied": report.all_satisfied,
        "missing": report.missing,
        "artifacts": [
            {
                "key": status.key,
                "path": status.path,
                "exists": status.exists,
                "non_empty": status.non_empty,
                "regenerated": status.regenerated,
                "error": status.error,
            }
            for status in report.artifacts
        ],
    }


def _print_summary(report: GuaranteeReport, *, checked: bool) -> None:
    """Print a human-readable summary of the report to stdout.

    Args:
        report: The report to summarize.
        checked: When ``True``, phrase the summary as a verification
            (``--check``) rather than an ensure/regenerate run.
    """
    verb = "Checked" if checked else "Ensured"
    print(f"{verb} graduation artifacts:")
    for status in report.artifacts:
        mark = "OK " if (status.exists and status.non_empty) else "MISSING"
        note = ""
        if status.regenerated:
            note = " (regenerated)"
        elif status.error:
            note = f" (error: {status.error})"
        print(f"  [{mark}] {status.key}: {status.path}{note}")
    if report.all_satisfied:
        print("All guaranteed artifacts are present and non-empty.")
    else:
        print(
            "Missing or empty guaranteed artifacts: " + ", ".join(report.missing)
        )


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the orchestrator CLI.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    defaults = ArtifactPaths()
    parser = argparse.ArgumentParser(
        description=(
            "Guarantee the bootcamp's crown-jewel graduation artifacts "
            "(transcript, recap Markdown, and a rendered recap) exist and are "
            "non-empty, regenerating any that are absent, empty, or stale."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "verify only (no regeneration/side effects); "
            "exit 1 naming missing artifacts"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the GuaranteeReport as JSON",
    )
    parser.add_argument(
        "--log", default=defaults.log, help="session log JSONL source"
    )
    parser.add_argument(
        "--recap", default=defaults.recap, help="recap Markdown artifact"
    )
    parser.add_argument(
        "--transcript", default=defaults.transcript, help="transcript artifact"
    )
    parser.add_argument(
        "--progress", default=defaults.progress, help="progress JSON source"
    )
    parser.add_argument(
        "--journal",
        default=None,
        help=(
            "deprecated no-op; journal content is now part of the consolidated "
            "recap (docs/bootcamp_recap.md) and this argument is ignored"
        ),
    )
    parser.add_argument(
        "--progress-dir",
        default=defaults.progress_dir,
        help="per-module artifacts directory",
    )
    parser.add_argument("--pdf", default=defaults.pdf, help="rendered PDF output")
    parser.add_argument(
        "--html", default=defaults.html, help="rendered HTML fallback output"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the guarantee orchestrator.

    Parses arguments into an :class:`ArtifactPaths`, then either verifies the
    artifacts (``--check``, side-effect free) or ensures/regenerates them. The
    report is emitted as JSON when ``--json`` is set, otherwise a human-readable
    summary is printed. A per-artifact failure never raises out of ``main``: it
    is recorded in the report and reflected in the exit code (Req 2.4, 6.3).

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` when every guaranteed artifact is present and non-empty, else
        ``1``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # The former separate journal path is retired: journal content is now part
    # of the consolidated recap. Accept --journal for backward compatibility but
    # ignore it, noting the deprecation on stderr (Req 6.2).
    if args.journal is not None:
        print(
            "Warning: --journal is deprecated and ignored; journal content is "
            "now part of the consolidated recap (docs/bootcamp_recap.md).",
            file=sys.stderr,
        )

    paths = ArtifactPaths(
        log=args.log,
        recap=args.recap,
        transcript=args.transcript,
        progress=args.progress,
        progress_dir=args.progress_dir,
        pdf=args.pdf,
        html=args.html,
    )

    if args.check:
        report = check_all(paths)
    else:
        report = ensure_all(paths)

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2))
    else:
        _print_summary(report, checked=args.check)

    return 0 if report.all_satisfied else 1


if __name__ == "__main__":
    sys.exit(main())
