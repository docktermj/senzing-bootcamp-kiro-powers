"""Bug condition exploration suite for the recap-completeness-and-pdf bugfix.

Feature: recap-completeness-and-pdf (BUGFIX)

Property 1: Bug Condition — Recap Completeness and Full PDF Body.

This suite encodes the *fixed* contract for the two content-loss paths described
in the design. It is EXPECTED TO FAIL on the unfixed state — the failures are the
success criterion. Each test surfaces a counterexample that confirms a
hypothesized root cause:

    Path A (missing per-module recap sections)
      A1  No track-completion reconciliation backfills missing sections.
      A2  The final module's recap section is never written / backfilled.

    Path B (outline-only PDF / dropped body lines)
      B1  The Shared_Renderer's ``multi_cell(0, ...)`` derives width from the
          current x-position, so a wrapping body line raises
          ``FPDFException: Not enough horizontal space to render a single
          character`` instead of rendering at full width (Req 2.5).
      B2  ``generate_recap_pdf.main`` swallows a rendering ``FPDFException`` via
          its broad ``except (OSError, Exception)`` instead of failing loudly
          (Req 2.6).
      B3  ``generate_recap_pdf.main`` reports success (exit 0, file exists) for a
          PDF whose body lines were dropped — there is no round-trip
          verification of the written artifact (Req 2.7).

Bug Condition (from design — ``isBugCondition(input)``):
    missingSection := EXISTS m IN modules_completed
                      SUCH THAT NOT hasHeading(recapFile, m)   # "## Module m:"
    droppedBodyLine := pdfRender.bodyLinesDropped > 0
                       AND pdfRender.reportedSuccess = TRUE
    isBugCondition := missingSection OR droppedBodyLine

Tooling: pytest + Hypothesis (per the repo ``fast``/``thorough`` profiles).
Scripts are stdlib-only; ``fpdf2`` is an optional dependency exercised by the
Path B PDF tests (skipped when it is absent).

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_recap_pdf as grp  # noqa: E402
import recap_pdf_render as rpr  # noqa: E402

# Optional fpdf2 dependency — the Path B PDF tests require a real render.
try:
    import fpdf  # noqa: F401
    from fpdf.errors import FPDFException

    _FPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    _FPDF_AVAILABLE = False

    class FPDFException(Exception):  # type: ignore  # noqa: N818 - mirror upstream name
        """Stand-in so the module imports without fpdf2 installed."""


_NEEDS_FPDF = pytest.mark.skipif(
    not _FPDF_AVAILABLE, reason="fpdf2 not installed; Path B PDF tests require it"
)


# ---------------------------------------------------------------------------
# Minimal PDF text extractor (stdlib-only).
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract visible text from a simple fpdf2-generated PDF using stdlib only.

    Decompresses each content stream (FlateDecode / zlib) when possible and
    concatenates the literal strings passed to text-showing operators (the
    parenthesised operands of ``Tj``/``TJ``/``'``). This is sufficient to assert
    the presence or absence of distinctive tokens and headings; it is not a
    general-purpose PDF parser.

    Args:
        pdf_bytes: Raw bytes of a written PDF file.

    Returns:
        The concatenated literal text content found in the PDF's streams.
    """
    chunks: list[str] = []
    # Capture the stream body up to ``endstream`` rather than requiring an
    # explicit ``\r?\n`` immediately before it. A binary FlateDecode stream can
    # legitimately end with a ``0x0D`` (\r) byte; the old ``\r?\nendstream``
    # boundary let ``\r?`` steal that trailing data byte, truncating the zlib
    # stream so ``zlib.decompress`` raised and the whole stream's text was lost
    # (a false negative on valid PDFs). ``decompressobj().decompress`` decodes
    # the zlib data and tolerates the trailing EOL bytes we now retain, whereas
    # ``zlib.decompress`` would reject that trailing data.
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
        raw = match.group(1)
        try:
            data = zlib.decompressobj().decompress(raw)
        except zlib.error:
            data = raw
        for token in re.finditer(rb"\((?:\\.|[^\\)])*\)", data):
            literal = (
                token.group(0)[1:-1]
                .replace(b"\\(", b"(")
                .replace(b"\\)", b")")
                .replace(b"\\\\", b"\\")
            )
            chunks.append(literal.decode("latin-1", "replace"))
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Recap / progress fixture builders.
# ---------------------------------------------------------------------------

_MODULE_NAMES = {
    1: "Business Problem",
    2: "Licensing",
    3: "Entity Resolution Intro",
    4: "Data Sources",
    5: "Mapping",
    6: "Loading",
    7: "Querying",
}


def _module_section(number: int, *, body_marker: str | None = None) -> str:
    """Build a single ``## Module N:`` recap section in canonical form.

    Args:
        number: The module number.
        body_marker: Optional distinctive token embedded in the Information
            Shared bullet so a PDF round-trip can detect whether the body line
            survived rendering.

    Returns:
        The Markdown text for one module recap section (trailing ``---``).
    """
    name = _MODULE_NAMES.get(number, f"Module {number}")
    bullet = f"Key concept for module {number}"
    if body_marker:
        bullet = f"{body_marker} {bullet}"
    return (
        f"## Module {number}: {name} \u2014 2025-01-1{number}T10:00:00-05:00\n"
        "\n"
        "### Information Shared\n"
        f"- {bullet}\n"
        "\n"
        "### Questions Asked\n"
        "1. What problem does this solve?\n"
        "\n"
        "### Answers Given\n"
        "1. It resolves entities.\n"
        "\n"
        "### Actions Taken\n"
        f"- Completed module {number}\n"
        "\n"
        "### Duration\n"
        "1h 0m\n"
        "\n"
        "---\n"
    )


def _recap_markdown(section_modules: list[int]) -> str:
    """Build a recap document containing sections for the given modules.

    Args:
        section_modules: Module numbers that should have a ``## Module N:`` section.

    Returns:
        The full recap Markdown document.
    """
    header = (
        "# Senzing Bootcamp Recap\n"
        "\n"
        "**Bootcamper:** Tester\n"
        "**Started:** 2025-01-10T09:00:00-05:00\n"
        "**Total Duration:** 7h 0m\n"
        "\n"
        "---\n"
        "\n"
    )
    return header + "\n".join(_module_section(m) for m in section_modules)


def _has_heading(recap_text: str, module: int) -> bool:
    """Return True when the recap contains a ``## Module N:`` heading.

    Args:
        recap_text: The recap Markdown content.
        module: The module number to look for.

    Returns:
        True if a ``## Module <module>:`` heading is present.
    """
    return re.search(rf"^##\s+Module\s+{module}:", recap_text, re.MULTILINE) is not None


def _build_project(
    tmp_path: Path,
    *,
    modules_completed: list[int],
    recap_section_modules: list[int],
) -> dict[str, Path]:
    """Materialise a project tree mirroring the bootcamper's workspace layout.

    Writes ``config/bootcamp_progress.json`` (with ``modules_completed`` and an
    ordered ``step_history``), ``docs/bootcamp_recap.md`` (with sections only for
    ``recap_section_modules``), an empty ``docs/bootcamp_journal.md``, and an
    empty ``docs/progress`` directory.

    Args:
        tmp_path: The per-test temporary directory.
        modules_completed: Module numbers recorded as completed in progress.
        recap_section_modules: Module numbers that have a recap section on disk.

    Returns:
        A mapping of logical names to the written paths.
    """
    config_dir = tmp_path / "config"
    docs_dir = tmp_path / "docs"
    progress_dir = docs_dir / "progress"
    config_dir.mkdir(parents=True, exist_ok=True)
    progress_dir.mkdir(parents=True, exist_ok=True)

    step_history = {
        str(m): {"last_completed_step": 5, "updated_at": f"2025-01-1{m}T11:00:00-05:00"}
        for m in modules_completed
    }
    progress = {
        "modules_completed": list(modules_completed),
        "current_module": max(modules_completed) if modules_completed else 1,
        "language": "python",
        "started_at": "2025-01-10T09:00:00-05:00",
        "step_history": step_history,
    }
    progress_path = config_dir / "bootcamp_progress.json"
    progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

    recap_path = docs_dir / "bootcamp_recap.md"
    recap_path.write_text(_recap_markdown(recap_section_modules), encoding="utf-8")

    journal_path = docs_dir / "bootcamp_journal.md"
    journal_path.write_text("# Bootcamp Journal\n", encoding="utf-8")

    return {
        "progress": progress_path,
        "recap": recap_path,
        "journal": journal_path,
        "progress_dir": progress_dir,
    }


# ---------------------------------------------------------------------------
# Path A — reconciliation applier probe.
# ---------------------------------------------------------------------------

# CLI flags a track-completion reconciliation/backfill mode might expose. The
# fix (tasks 3.3/3.4) wires the existing completion_artifacts.py planner into an
# applier; on the unfixed state none of these exist, so the probe is a no-op and
# the missing sections remain absent (the counterexample).
_RECONCILE_CLI_FLAGS = ("--backfill", "--apply", "--reconcile", "--write")

# Module-level callables a reconciliation applier might expose.
_RECONCILE_FUNC_NAMES = (
    "reconcile_recap",
    "backfill_recap",
    "backfill_recap_sections",
    "apply_backfill",
    "write_missing_recap_sections",
)

_COMPLETION_ARTIFACTS_SCRIPT = _SCRIPTS_DIR / "completion_artifacts.py"


def _attempt_recap_reconciliation(paths: dict[str, Path]) -> bool:
    """Best-effort: run whatever recap-reconciliation applier the fix provides.

    Tries, in order, each candidate module-level function on
    ``completion_artifacts`` and then each candidate CLI flag. Every attempt is
    guarded so an absent/incompatible surface is simply skipped. On the unfixed
    state no applier exists, so this returns ``False`` without modifying the
    recap — the subsequent heading assertion then fails with a counterexample.

    Args:
        paths: The project paths from :func:`_build_project`.

    Returns:
        True if some applier ran to completion without error; else False.
    """
    import completion_artifacts as ca  # local import; module already importable

    # 1) Try module-level functions with a few plausible argument shapes.
    for name in _RECONCILE_FUNC_NAMES:
        func = getattr(ca, name, None)
        if not callable(func):
            continue
        for args in (
            (str(paths["progress"]), str(paths["recap"])),
            (str(paths["recap"]), str(paths["progress"])),
            (paths["progress"], paths["recap"]),
        ):
            try:
                func(*args)
                return True
            except Exception:  # noqa: BLE001 - incompatible signature; try next
                continue

    # 2) Try CLI apply/backfill modes reusing the existing argument surface.
    for flag in _RECONCILE_CLI_FLAGS:
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(_COMPLETION_ARTIFACTS_SCRIPT),
                    "--progress",
                    str(paths["progress"]),
                    "--recap",
                    str(paths["recap"]),
                    "--journal",
                    str(paths["journal"]),
                    "--progress-dir",
                    str(paths["progress_dir"]),
                    flag,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        # argparse rejects unknown flags with exit code 2; 0 means the mode ran.
        if result.returncode == 0:
            return True

    return False


class TestPathARecapReconciliation:
    """Path A — every completed module must end with a persisted recap section.

    These tests encode the fixed contract: after the track-completion
    reconciliation step, ``docs/bootcamp_recap.md`` contains a ``## Module N:``
    heading for every module in ``modules_completed``. On the unfixed state there
    is no reconciliation/backfill applier, so the missing sections remain absent
    and these tests fail with a documented counterexample.

    Validates: Requirements 1.1, 1.2, 1.4 (expected behavior: 2.1, 2.2, 2.4)
    """

    def test_track_completion_backfills_missing_late_modules(self, tmp_path: Path) -> None:
        """modules_completed = [1..7] but recap has only 1..5 -> 6, 7 backfilled."""
        modules_completed = [1, 2, 3, 4, 5, 6, 7]
        paths = _build_project(
            tmp_path,
            modules_completed=modules_completed,
            recap_section_modules=[1, 2, 3, 4, 5],
        )

        applied = _attempt_recap_reconciliation(paths)
        recap_text = paths["recap"].read_text(encoding="utf-8")
        missing = [m for m in modules_completed if not _has_heading(recap_text, m)]

        assert not missing, (
            "COUNTEREXAMPLE (bug confirmed): after track completion the recap is "
            f"still missing '## Module N:' sections for modules {missing} while "
            "modules_completed reports them complete. No reconciliation step "
            "backfilled them against config/bootcamp_progress.json "
            f"(reconciliation applier available: {applied})."
        )

    def test_final_module_section_is_present_after_completion(self, tmp_path: Path) -> None:
        """Final-module append miss: recap has 1..6, module 7 must be backfilled."""
        modules_completed = [1, 2, 3, 4, 5, 6, 7]
        paths = _build_project(
            tmp_path,
            modules_completed=modules_completed,
            recap_section_modules=[1, 2, 3, 4, 5, 6],
        )

        applied = _attempt_recap_reconciliation(paths)
        recap_text = paths["recap"].read_text(encoding="utf-8")

        assert _has_heading(recap_text, 7), (
            "COUNTEREXAMPLE (bug confirmed): the final module (7) was marked "
            "complete but its '## Module 7:' recap section was never written, and "
            "track completion did not backfill it. The append succeeds without "
            f"verification (reconciliation applier available: {applied})."
        )


# ---------------------------------------------------------------------------
# Path B — full PDF body (no dropped lines, loud failure, verified output).
# ---------------------------------------------------------------------------


def _new_pdf() -> "fpdf.FPDF":
    """Create a fresh single-page FPDF document with the recap defaults."""
    pdf = fpdf.FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    return pdf


_FILLER = "considerations regarding entity resolution mapping and loading data "


@_NEEDS_FPDF
class TestPathBFullWidthRendering:
    """Path B — wrapping body lines must render at full width (Req 2.5).

    The Shared_Renderer's ``multi_cell(0, ...)`` derives the cell width from the
    current x-position. After a cell advances x toward the right margin, a body
    line that needs to wrap has too little horizontal space and raises
    ``FPDFException``. The fixed renderer resets x to the left margin and renders
    at the effective page width, so wrapping always succeeds.

    Validates: Requirements 1.5 (expected behavior: 2.5)
    """

    def test_wrapping_body_line_renders_when_cursor_advanced(self) -> None:
        """A wrapping prose body line must survive even when x is near r-margin."""
        pdf = _new_pdf()
        marker = "ZBODYMARK"
        body = f"{marker} " + (_FILLER * 6)

        # Simulate the documented condition: a prior cell advanced x toward the
        # right margin before this body block is rendered.
        pdf.set_x(pdf.w - pdf.r_margin - 3)
        try:
            rpr.render_markdown_body(pdf, body)
        except FPDFException as exc:
            pytest.fail(
                "COUNTEREXAMPLE (bug confirmed): a wrapping body line was dropped "
                "because multi_cell(0, ...) derived width from the advanced "
                f"x-position and raised FPDFException ({exc}). The body line never "
                "rendered while a generator would still report success."
            )

        rendered = extract_pdf_text(bytes(pdf.output()))
        assert marker in rendered, (
            "COUNTEREXAMPLE (bug confirmed): the wrapping body line is absent from "
            "the rendered PDF text."
        )

    # Property 1 (Path B, Req 2.5): for any distinctive body token and any cursor
    # advancement toward the right margin, rendering the body must place the token
    # in the PDF (render at full width) rather than dropping it / raising.
    @given(
        suffix=st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=4, max_size=8
        ),
        words=st.integers(min_value=4, max_value=10),
        gap=st.integers(min_value=1, max_value=8),
    )
    def test_full_width_rendering_property(self, suffix: str, words: int, gap: int) -> None:
        """**Validates: Requirements 1.5** (expected behavior 2.5).

        For any wrapping body content and any advanced cursor position, the body
        token survives into the rendered PDF (fails on unfixed code, where the
        advanced-x ``multi_cell(0, ...)`` raises ``FPDFException``).
        """
        pdf = _new_pdf()
        marker = f"MARK{suffix}"
        body = f"{marker} " + (_FILLER * words)

        pdf.set_x(pdf.w - pdf.r_margin - gap)
        try:
            rpr.render_markdown_body(pdf, body)
        except FPDFException as exc:
            pytest.fail(
                "COUNTEREXAMPLE (bug confirmed): wrapping body line dropped via "
                f"FPDFException at advanced x (gap={gap}): {exc}"
            )

        rendered = extract_pdf_text(bytes(pdf.output()))
        assert marker in rendered, (
            f"COUNTEREXAMPLE (bug confirmed): token {marker!r} dropped from the PDF."
        )


@_NEEDS_FPDF
class TestPathBLoudFailure:
    """Path B — a rendering exception must not be silently swallowed (Req 2.6).

    ``generate_recap_pdf.main`` wraps ``render_pdf`` in a broad
    ``except (OSError, Exception)`` that absorbs a genuine rendering
    ``FPDFException`` and returns a generic failure, conflating it with an
    ordinary write error. The fixed generator must fail loudly: the rendering
    exception is surfaced rather than swallowed by the catch-all.

    Validates: Requirements 1.6 (expected behavior: 2.6)
    """

    def test_rendering_fpdf_exception_is_not_swallowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A render-time FPDFException must propagate, not be caught generically."""
        paths = _build_project(
            tmp_path,
            modules_completed=[1],
            recap_section_modules=[1],
        )
        output = tmp_path / "out.pdf"

        def _raise_render(*_args, **_kwargs):
            raise FPDFException(
                "Not enough horizontal space to render a single character"
            )

        monkeypatch.setattr(grp, "render_pdf", _raise_render)

        with pytest.raises(FPDFException):
            grp.main(["--input", str(paths["recap"]), "--output", str(output)])
        # On unfixed code main catches the FPDFException via its broad
        # `except (OSError, Exception)` handler and returns 1, so the
        # pytest.raises block above fails — the documented counterexample.


@_NEEDS_FPDF
class TestPathBRoundTripVerification:
    """Path B — success is reported only after verifying the written PDF (Req 2.7).

    ``generate_recap_pdf.main`` infers success from exit code and file existence
    only; it never re-opens the written PDF to confirm it contains the expected
    per-module sections and body lines. When body lines are dropped during
    rendering, the generator still prints ``PDF generated:`` and returns 0. The
    fixed generator round-trips the written PDF and reports success only when the
    body content is present (otherwise it fails loudly / returns non-zero).

    Validates: Requirements 1.7 (expected behavior: 2.7)
    """

    def test_success_implies_body_content_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If main reports success, the PDF must contain the body, not just headings."""
        marker = "ZBODYVERIFY"
        recap_text = (
            "# Senzing Bootcamp Recap\n\n"
            "**Bootcamper:** Tester\n"
            "**Started:** 2025-01-10T09:00:00-05:00\n\n"
            "---\n\n"
            "## Module 1: Business Problem \u2014 2025-01-11T10:00:00-05:00\n\n"
            "### Information Shared\n"
            f"- {marker} a key concept presented during the module\n\n"
            "### Actions Taken\n"
            "- Completed module 1\n\n"
            "### Duration\n1h 0m\n\n"
            "---\n"
        )
        recap_path = tmp_path / "recap.md"
        recap_path.write_text(recap_text, encoding="utf-8")
        output = tmp_path / "out.pdf"

        # Simulate the historical outline-only render: the body-rendering
        # primitives drop their content while headings still render. The real
        # render_pdf otherwise runs, producing a PDF with sections but no body.
        monkeypatch.setattr(grp, "render_list_items", lambda *a, **k: None)
        monkeypatch.setattr(grp, "_render_qa_pairs", lambda *a, **k: None)

        exit_code = grp.main(["--input", str(recap_path), "--output", str(output)])

        reported_success = exit_code == 0 and output.exists()
        if reported_success:
            text = extract_pdf_text(output.read_bytes())
            # Heading survives (single short cell); the body line was dropped.
            assert "Module 1" in text, "expected the module heading to render"
            assert marker in text, (
                "COUNTEREXAMPLE (bug confirmed): the generator reported success "
                "(exit 0, file exists) for a PDF whose body line was dropped — the "
                f"body token {marker!r} is absent and no round-trip verification "
                "caught the loss."
            )
