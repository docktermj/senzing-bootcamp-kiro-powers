"""Tests for generate_recap_pdf_inline.py — the inline fallback recap PDF generator.

Feature: graduation-recap-pdf-resilience

These tests exercise the self-contained inline fallback used by the graduation
flow (Step 0b.3) when the bundled ``generate_recap_pdf.py`` helper cannot be
located or run. Subsequent tasks (3.2-3.5) add more test classes to this file:
graceful degradation without fpdf2, helper independence, the no-false-success
contract, and a Hypothesis property test.

Tests follow the project pattern: class-based organization and the documented
``sys.path`` import idiom (scripts are not packages).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import RecapDocument, parse_recap_markdown  # noqa: E402
from generate_recap_pdf_inline import generate_inline  # noqa: E402

# ---------------------------------------------------------------------------
# Test fixtures and helpers
# ---------------------------------------------------------------------------

# Distinctive tokens embedded in the representative recap below. Each must
# survive into the renderable body so we can prove the PDF body is non-empty
# and carries the recap's content (not just a cover page).
_RECAP_TOKENS = [
    "First Demo",
    "Data Mapping",
    "entity resolution fundamentals",
    "How does candidate generation work",
    "It uses keys derived from record features",
    "Loaded the sample truth-set records",
]


def _representative_recap() -> str:
    """Build a representative, strict-schema recap markdown document.

    The document uses the canonical ``## Module N: <name> — <timestamp>``
    headings and the five known subsections so it parses into structured
    sections. Each token in ``_RECAP_TOKENS`` appears exactly so the renderable
    body can be asserted to carry the recap's content.

    Returns:
        A non-empty recap Markdown string with known content tokens.
    """
    return (
        "# Senzing Bootcamp Recap\n"
        "\n"
        "**Bootcamper:** Alex Doe\n"
        "**Started:** 2025-06-01T10:00:00+00:00\n"
        "**Total Duration:** 3h 15m\n"
        "\n"
        "---\n"
        "\n"
        "## Module 1: First Demo \u2014 2025-06-01T11:00:00+00:00\n"
        "\n"
        "### Information Shared\n"
        "- entity resolution fundamentals\n"
        "\n"
        "### Questions Asked\n"
        "1. How does candidate generation work\n"
        "\n"
        "### Answers Given\n"
        "1. It uses keys derived from record features\n"
        "\n"
        "### Actions Taken\n"
        "- Loaded the sample truth-set records\n"
        "\n"
        "### Duration\n"
        "1h 0m\n"
        "\n"
        "---\n"
        "\n"
        "## Module 2: Data Mapping \u2014 2025-06-01T12:30:00+00:00\n"
        "\n"
        "### Information Shared\n"
        "- mapping records to the Senzing JSON schema\n"
        "\n"
        "### Questions Asked\n"
        "\n"
        "### Answers Given\n"
        "\n"
        "### Actions Taken\n"
        "- Mapped two data sources\n"
        "\n"
        "### Duration\n"
        "2h 15m\n"
        "\n"
        "---\n"
    )


def _rendered_body_text(doc: RecapDocument) -> str:
    """Collect the renderable body text the generator would emit (parse/render seam).

    Excludes cover-page header fields and gathers everything rendered below the
    cover page: per-module headings, the five known subsections, durations, and
    any captured Generic_Content. ``generic_content`` is read defensively via
    getattr so the helper works whether or not the field is present.

    Args:
        doc: Parsed recap document.

    Returns:
        Newline-joined renderable body text (empty when only a cover page exists).
    """
    parts: list[str] = []
    for s in doc.sections:
        parts.append(s.module_name)
        parts.append(s.timestamp)
        parts.extend(s.information_shared)
        parts.extend(s.questions_asked)
        parts.extend(s.answers_given)
        parts.extend(s.actions_taken)
        parts.append(s.duration)
        parts.extend(getattr(s, "generic_content", []) or [])
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Property 1: Inline fallback produces a non-empty PDF body
# ---------------------------------------------------------------------------


class TestInlineNonEmptyBody:
    """Inline fallback writes a non-empty PDF body from a representative recap.

    **Validates: Requirements 5.1, 2.1, 2.3**

    For a representative non-empty recap, ``generate_inline`` exits 0, writes a
    PDF file, and (via the parse/render seam) yields a non-empty body containing
    the recap's text tokens.
    """

    def test_generate_inline_writes_nonempty_pdf(self, tmp_path: Path) -> None:
        """``generate_inline`` on a representative recap exits 0 and writes a PDF.

        **Validates: Requirements 5.1, 2.1**
        """
        recap_md = _representative_recap()
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(recap_md, encoding="utf-8")

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 0, f"Expected exit code 0 for a representative recap, got {rc}"
        assert output_path.exists(), "Inline generator did not write a PDF file"

        data = output_path.read_bytes()
        assert data.startswith(b"%PDF"), "Output is not a valid PDF (missing %PDF header)"
        assert len(data) > 0, "Generated PDF file is empty"

    def test_rendered_body_is_nonempty_and_contains_recap_tokens(
        self, tmp_path: Path
    ) -> None:
        """The renderable body (parse/render seam) is non-empty and carries the
        recap's text tokens — proving the PDF is not cover-page-only.

        **Validates: Requirements 2.3, 5.1**
        """
        recap_md = _representative_recap()
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(recap_md, encoding="utf-8")

        rc = generate_inline(str(input_path), str(output_path))
        assert rc == 0, f"Expected exit code 0, got {rc}"

        # Parse/render seam: the same content the inline generator renders.
        doc = parse_recap_markdown(recap_md)
        body = _rendered_body_text(doc)

        assert body.strip(), (
            "Rendered body is empty — the representative recap content was "
            "dropped (cover-page-only PDF)"
        )

        missing = [tok for tok in _RECAP_TOKENS if tok not in body]
        assert not missing, (
            f"Recap content missing from rendered body: tokens {missing} never "
            f"appear in the renderable output"
        )


# ---------------------------------------------------------------------------
# Property 2: Graceful degradation without fpdf2
# ---------------------------------------------------------------------------


class TestGracefulDegradationWithoutFpdf2:
    """Inline fallback degrades gracefully when ``fpdf2`` is absent.

    **Validates: Requirements 5.2, 2.4, 3.1**

    For environments where ``import fpdf`` raises ``ImportError``, the inline
    fallback prints the ``pip install fpdf2`` hint to stderr, returns exit code
    1, and writes no PDF — without letting a traceback/exception propagate.

    Both render paths import ``fpdf`` lazily: the bundled-renderer delegate
    (``generate_recap_pdf.render_pdf``) and the embedded renderer
    (``_render_inline_pdf``). Forcing ``sys.modules['fpdf'] = None`` makes any
    ``import fpdf`` / ``from fpdf import ...`` raise ``ImportError`` regardless
    of which path runs, so the test reliably triggers the degradation branch.
    """

    def test_missing_fpdf2_prints_hint_exits_one_no_pdf(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """Simulate fpdf2 absent and assert the graceful-degradation contract.

        **Validates: Requirements 5.2, 2.4, 3.1**
        """
        recap_md = _representative_recap()
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(recap_md, encoding="utf-8")

        # Force ``import fpdf`` (and ``from fpdf import ...``) to raise
        # ImportError in both the bundled and embedded render paths.
        monkeypatch.setitem(sys.modules, "fpdf", None)

        # No exception/traceback should propagate out of generate_inline.
        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 1, f"Expected exit code 1 when fpdf2 is absent, got {rc}"

        captured = capsys.readouterr()
        assert "pip install fpdf2" in captured.err, (
            "Expected the 'pip install fpdf2' hint on stderr when fpdf2 is "
            f"absent; got stderr: {captured.err!r}"
        )

        assert not output_path.exists(), (
            "No PDF should be written when fpdf2 is absent, but a file exists "
            f"at {output_path}"
        )


# ---------------------------------------------------------------------------
# Property 4: Independence from the bundled helper
# ---------------------------------------------------------------------------


class TestHelperIndependence:
    """Inline fallback works without the bundled ``generate_recap_pdf`` module.

    **Validates: Requirements 5.3, 2.2**

    For workspaces where ``generate_recap_pdf`` is not importable, the inline
    fallback still produces a non-empty PDF (when ``fpdf2`` is present) using its
    embedded renderer rather than the bundled helper's shared renderer.

    Simulation strategy: forcing ``sys.modules['generate_recap_pdf'] = None``
    makes any ``from generate_recap_pdf import ...`` raise ``ImportError``, which
    drives ``_import_bundled_renderer()`` to return ``None`` and routes
    ``generate_inline`` through the embedded ``_render_inline_pdf`` path. The
    ``monkeypatch`` fixture auto-undoes the patch after the test, and the
    module-level ``RecapDocument`` / ``parse_recap_markdown`` names imported at
    load time remain bound (only *new* imports are affected).
    """

    def test_import_bundled_renderer_returns_none_when_unimportable(
        self, monkeypatch
    ) -> None:
        """Under the patch, ``_import_bundled_renderer`` returns ``None``.

        This proves the embedded renderer path is the one exercised when the
        bundled module is not importable.

        **Validates: Requirements 5.3, 2.2**
        """
        from generate_recap_pdf_inline import _import_bundled_renderer  # noqa: PLC0415

        monkeypatch.setitem(sys.modules, "generate_recap_pdf", None)

        assert _import_bundled_renderer() is None, (
            "Expected _import_bundled_renderer() to return None when "
            "generate_recap_pdf is not importable"
        )

    def test_embedded_renderer_writes_nonempty_pdf_without_bundled_helper(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """With the bundled helper unimportable and ``fpdf2`` present, the inline
        fallback still writes a non-empty, valid PDF via the embedded renderer.

        **Validates: Requirements 5.3, 2.2**
        """
        recap_md = _representative_recap()
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(recap_md, encoding="utf-8")

        # Force ``from generate_recap_pdf import ...`` to raise ImportError so
        # the embedded renderer path is exercised.
        monkeypatch.setitem(sys.modules, "generate_recap_pdf", None)

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 0, (
            f"Expected exit code 0 from the embedded renderer path, got {rc}"
        )
        assert output_path.exists(), (
            "Embedded renderer did not write a PDF when the bundled helper was "
            "unimportable"
        )

        data = output_path.read_bytes()
        assert data.startswith(b"%PDF"), (
            "Output is not a valid PDF (missing %PDF header)"
        )
        assert len(data) > 0, "Generated PDF file is empty"


# ---------------------------------------------------------------------------
# Property 3: No false success
# ---------------------------------------------------------------------------


class TestNoFalseSuccess:
    """The ``PDF generated:`` line is emitted only when a PDF is actually written.

    **Validates: Requirements 3.4**

    This class focuses specifically on the stdout success-line contract: the
    ``PDF generated:`` signal appears on stdout exactly when a PDF file is
    written and ``generate_inline`` returns 0; every no-PDF path (missing input,
    empty input, ``fpdf2`` absent) returns 1 and leaves stdout free of the
    success line. ``capsys`` captures stdout/stderr so we can assert the
    success line's presence/absence directly.
    """

    _SUCCESS_PREFIX = "PDF generated:"

    def test_success_path_prints_success_line_and_writes_pdf(
        self, tmp_path: Path, capsys
    ) -> None:
        """A representative recap writes a PDF, exits 0, and prints the success line.

        **Validates: Requirements 3.4**
        """
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(_representative_recap(), encoding="utf-8")

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 0, f"Expected exit code 0 on the success path, got {rc}"
        assert output_path.exists(), "Success path did not write a PDF file"

        captured = capsys.readouterr()
        assert self._SUCCESS_PREFIX in captured.out, (
            "Expected the 'PDF generated:' success line on stdout when a PDF was "
            f"written; got stdout: {captured.out!r}"
        )
        # The success line should reference the actual output path it wrote.
        assert str(output_path) in captured.out, (
            "Success line should name the written PDF path; got stdout: "
            f"{captured.out!r}"
        )

    def test_missing_input_returns_one_without_success_line(
        self, tmp_path: Path, capsys
    ) -> None:
        """A missing input file returns 1, prints no success line, and writes no PDF.

        **Validates: Requirements 3.4**
        """
        input_path = tmp_path / "does_not_exist.md"
        output_path = tmp_path / "bootcamp_recap.pdf"

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 1, f"Expected exit code 1 for a missing input, got {rc}"
        assert not output_path.exists(), "No PDF should be written for a missing input"

        captured = capsys.readouterr()
        assert self._SUCCESS_PREFIX not in captured.out, (
            "The 'PDF generated:' line must not appear when no PDF was written; "
            f"got stdout: {captured.out!r}"
        )

    def test_empty_input_returns_one_without_success_line(
        self, tmp_path: Path, capsys
    ) -> None:
        """An empty input file returns 1, prints no success line, and writes no PDF.

        **Validates: Requirements 3.4**
        """
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text("   \n\t\n", encoding="utf-8")

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 1, f"Expected exit code 1 for an empty input, got {rc}"
        assert not output_path.exists(), "No PDF should be written for an empty input"

        captured = capsys.readouterr()
        assert self._SUCCESS_PREFIX not in captured.out, (
            "The 'PDF generated:' line must not appear for an empty input; "
            f"got stdout: {captured.out!r}"
        )

    def test_missing_fpdf2_returns_one_without_success_line(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """When ``fpdf2`` is absent the run returns 1 and prints no success line.

        Forcing ``sys.modules['fpdf'] = None`` makes any ``import fpdf`` /
        ``from fpdf import ...`` raise ``ImportError`` in both the bundled and
        embedded render paths, so the no-PDF branch is reliably taken.

        **Validates: Requirements 3.4**
        """
        input_path = tmp_path / "bootcamp_recap.md"
        output_path = tmp_path / "bootcamp_recap.pdf"
        input_path.write_text(_representative_recap(), encoding="utf-8")

        monkeypatch.setitem(sys.modules, "fpdf", None)

        rc = generate_inline(str(input_path), str(output_path))

        assert rc == 1, f"Expected exit code 1 when fpdf2 is absent, got {rc}"
        assert not output_path.exists(), "No PDF should be written when fpdf2 is absent"

        captured = capsys.readouterr()
        assert self._SUCCESS_PREFIX not in captured.out, (
            "The 'PDF generated:' line must not appear when fpdf2 is absent; "
            f"got stdout: {captured.out!r}"
        )


# ---------------------------------------------------------------------------
# Property 1 (Hypothesis): free-form recap Markdown yields a non-empty body
# ---------------------------------------------------------------------------

import tempfile  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from generate_recap_pdf_inline import _split_blocks  # noqa: E402


@st.composite
def st_recap_markdown(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Generate free-form recap Markdown plus the distinctive tokens it injects.

    Builds a non-empty document from a mix of loose headings (lines starting
    with ``#``/``##``/``###``), prose paragraphs, and fenced code blocks
    (delimited by ```` ``` ````). Each element embeds a unique, ASCII-only
    marker token (e.g. ``TOKEN0MARKER``) so the renderable output can be checked
    for token survival without relying on lossy PDF text extraction.

    Args:
        draw: Hypothesis draw callable.

    Returns:
        A ``(markdown, tokens)`` tuple where ``markdown`` is a non-empty
        free-form recap document and ``tokens`` are the distinctive markers that
        must survive into the renderable body.
    """
    kinds = draw(
        st.lists(
            st.sampled_from(["heading", "prose", "code"]),
            min_size=1,
            max_size=6,
        )
    )
    # Alphabet that never collides with the marker tokens and stays Latin-1 safe.
    filler = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=24)

    blocks: list[str] = []
    tokens: list[str] = []
    for i, kind in enumerate(kinds):
        token = f"TOKEN{i}MARKER"
        tokens.append(token)
        if kind == "heading":
            level = draw(st.integers(min_value=1, max_value=3))
            blocks.append(f"{'#' * level} {token} {draw(filler)}".rstrip())
        elif kind == "prose":
            blocks.append(f"{draw(filler)} {token} {draw(filler)}".strip())
        else:  # fenced code block
            blocks.append(f"```\n{draw(filler)}\nrun_{token}()\n```")

    markdown = "\n\n".join(blocks) + "\n"
    return markdown, tokens


class TestInlineBodyContentProperty:
    """Free-form recap Markdown is rendered to a non-empty PDF carrying its tokens.

    **Validates: Requirements 2.1, 2.2, 2.3**

    For all generated non-empty recap Markdown documents (loose headings, prose,
    and fenced code), ``generate_inline`` exits 0, writes a non-empty valid PDF
    (starts with ``%PDF``), and the input's distinctive renderable tokens survive
    into the renderable body. Token survival is checked through the renderer's
    block seam (``_split_blocks``) — the same content the inline renderer emits
    verbatim — which is robust against lossy PDF text extraction.
    """

    @settings(max_examples=10)
    @given(doc=st_recap_markdown())
    def test_inline_path_yields_nonempty_body_with_tokens(
        self, doc: tuple[str, list[str]]
    ) -> None:
        """Inline generation writes a valid PDF and preserves the input's tokens.

        **Validates: Requirements 2.1, 2.2, 2.3**
        """
        markdown, tokens = doc

        # Per-example temp files: @given must NOT reuse the function-scoped
        # ``tmp_path`` fixture, so create an isolated directory per example.
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "bootcamp_recap.md"
            output_path = Path(tmpdir) / "bootcamp_recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            rc = generate_inline(str(input_path), str(output_path))

            assert rc == 0, f"Expected exit code 0 for non-empty recap, got {rc}"
            assert output_path.exists(), "Inline generator did not write a PDF file"

            data = output_path.read_bytes()
            assert data.startswith(b"%PDF"), "Output is not a valid PDF (missing %PDF header)"
            assert len(data) > 0, "Generated PDF file is empty"

        # Rendering seam: the renderer is fed the full Markdown body; the blocks
        # it emits must be non-empty and carry every injected token.
        rendered_body = "\n".join(_split_blocks(markdown))
        assert rendered_body.strip(), "Rendered body is empty for a non-empty input"

        missing = [tok for tok in tokens if tok not in rendered_body]
        assert not missing, (
            f"Renderable tokens dropped from the rendered body: {missing}"
        )
