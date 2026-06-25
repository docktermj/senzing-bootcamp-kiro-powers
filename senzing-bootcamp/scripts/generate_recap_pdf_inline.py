#!/usr/bin/env python3
"""Self-contained inline fallback for bootcamp recap PDF generation.

Converts ``docs/bootcamp_recap.md`` into ``docs/bootcamp_recap.pdf`` without
depending on the bundled ``generate_recap_pdf.py`` helper being importable from
the bootcamper's workspace. It is used by the graduation flow (Step 0b.3) when
the bundled helper cannot be located or run.

When the sibling ``generate_recap_pdf`` module is importable, this script reuses
its shared parser/renderer so the output matches the bundled helper. Otherwise
it renders the raw Markdown body with an embedded minimal renderer so no recap
content is dropped. The optional ``fpdf2`` dependency (``import fpdf``) is
imported lazily inside the render path and degrades gracefully when absent.

Usage:
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --input recap.md
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --output recap.pdf
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Callable

# Hint surfaced when the optional fpdf2 dependency is missing.
_FPDF_HINT = "fpdf2 is required. Install with: pip install fpdf2"


# ---------------------------------------------------------------------------
# Bundled-helper reuse
# ---------------------------------------------------------------------------


def _import_bundled_renderer() -> (
    tuple[Callable[[str], object], Callable[..., None]] | None
):
    """Attempt to import the shared recap parser/renderer from the sibling module.

    Uses the documented ``sys.path`` pattern to make ``generate_recap_pdf``
    importable from this script's directory. When the module is not importable
    (e.g. it is not present in the bootcamper's workspace), returns ``None`` so
    the caller falls back to the embedded renderer.

    Returns:
        A ``(parse_recap_markdown, render_pdf)`` tuple when importable, else
        ``None``.
    """
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from generate_recap_pdf import parse_recap_markdown, render_pdf  # noqa: PLC0415
    except ImportError:
        return None
    return parse_recap_markdown, render_pdf


# ---------------------------------------------------------------------------
# Embedded minimal renderer (used when generate_recap_pdf is NOT importable)
# ---------------------------------------------------------------------------


def _safe_text(text: str) -> str:
    """Ensure text is safe for PDF core fonts (Latin-1 encoding).

    Characters outside the Latin-1 range are replaced with ``?`` to prevent
    encoding errors with the Helvetica/Courier core fonts.

    Args:
        text: Input text that may contain non-Latin-1 characters.

    Returns:
        Text safe for rendering with PDF core fonts.
    """
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _split_blocks(text: str) -> list[str]:
    """Split Markdown text into renderable blocks.

    Groups consecutive non-blank lines into paragraph blocks and keeps fenced
    code blocks (delimited by ```` ``` ````) intact as single blocks even when
    they contain blank lines.

    Args:
        text: Raw Markdown text.

    Returns:
        List of non-empty block strings in document order.
    """
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if current:
            block = "\n".join(current).strip("\n")
            if block.strip():
                blocks.append(block)
            current.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if in_fence:
                current.append(line)
                in_fence = False
                flush()
            else:
                flush()
                in_fence = True
                current.append(line)
            continue
        if in_fence:
            current.append(line)
            continue
        if not line.strip():
            flush()
        else:
            current.append(line)

    flush()
    return blocks


def _render_inline_pdf(body_text: str, output_path: str) -> None:
    """Render raw recap Markdown to a PDF using an embedded minimal renderer.

    Emits a cover line followed by the raw Markdown body as wrapped text and
    monospace code blocks so no recap content is dropped. ``fpdf2`` is imported
    lazily here so the module never imports it at top level.

    Args:
        body_text: Raw recap Markdown body.
        output_path: File path for the generated PDF.

    Raises:
        ImportError: If ``fpdf2`` is not installed.
        OSError: If the PDF cannot be written to ``output_path``.
    """
    from fpdf import FPDF  # noqa: PLC0415

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Cover line.
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 10, _safe_text("Senzing Bootcamp Recap"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Body — wrapped text with monospace fenced code blocks and headings.
    for block in _split_blocks(body_text):
        lines = block.splitlines()
        first = lines[0].lstrip() if lines else ""

        if first.startswith("```"):
            code_lines = lines[1:]
            if code_lines and code_lines[-1].lstrip().startswith("```"):
                code_lines = code_lines[:-1]
            pdf.set_font("Courier", "", 10)
            pdf.multi_cell(
                0, 5, _safe_text("\n".join(code_lines)), new_x="LMARGIN", new_y="NEXT"
            )
            pdf.ln(2)
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", first)
        if heading_match and len(lines) == 1:
            level = len(heading_match.group(1))
            pdf.set_font("Helvetica", "B", 16 if level <= 2 else 13)
            pdf.multi_cell(
                0, 7, _safe_text(heading_match.group(2).strip()), new_x="LMARGIN", new_y="NEXT"
            )
            pdf.ln(2)
            continue

        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, _safe_text(block), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.output(output_path)


# ---------------------------------------------------------------------------
# Inline generation
# ---------------------------------------------------------------------------


def generate_inline(input_path: str, output_path: str) -> int:
    """Generate the recap PDF without depending on the bundled helper.

    Reuse the shared recap renderer when ``generate_recap_pdf`` is importable;
    otherwise render the raw Markdown body with the embedded renderer.
    Lazy-import ``fpdf2``; return 1 (with a ``pip install fpdf2`` hint) when it
    is absent or no PDF could be written, and 0 when a PDF was written.

    Args:
        input_path: Path to the recap Markdown input.
        output_path: Path for the generated PDF output.

    Returns:
        Exit code: 0 when a PDF was written, 1 otherwise.
    """
    in_path = Path(input_path)

    # Validate input exists and is non-empty.
    if not in_path.exists():
        print(f"Recap file not found: {input_path}", file=sys.stderr)
        return 1
    content = in_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"Recap file is empty: {input_path}", file=sys.stderr)
        return 1

    # Reuse the shared renderer when importable; otherwise render raw Markdown.
    renderer = _import_bundled_renderer()
    try:
        if renderer is not None:
            parse_recap_markdown, render_pdf = renderer
            doc = parse_recap_markdown(content)
            render_pdf(doc, output_path, body_text=content)
        else:
            _render_inline_pdf(content, output_path)
    except ImportError:
        # fpdf2 absent — degrade gracefully with a hint, no traceback.
        print(_FPDF_HINT, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to write PDF: {exc}", file=sys.stderr)
        return 1

    # Only report success when a PDF file was actually written.
    if not Path(output_path).exists():
        print(f"Failed to write PDF: no output produced at {output_path}", file=sys.stderr)
        return 1

    print(f"PDF generated: {output_path}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Mirrors ``generate_recap_pdf.py`` so the two scripts are interchangeable.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with input and output paths.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Inline fallback: generate a PDF from the bootcamp recap markdown "
            "document without depending on the bundled helper."
        ),
    )
    parser.add_argument(
        "--input",
        default="docs/bootcamp_recap.md",
        help="Path to recap markdown (default: docs/bootcamp_recap.md)",
    )
    parser.add_argument(
        "--output",
        default="docs/bootcamp_recap.pdf",
        help="Path for output PDF (default: docs/bootcamp_recap.pdf)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the inline recap PDF generator.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    # generate_inline owns the full messaging contract: the only stdout success
    # signal is the "PDF generated:" line (emitted solely when a PDF is written),
    # all warnings/errors go to stderr, and the return code is 0 only when a PDF
    # was written and 1 for every no-PDF outcome. main simply propagates it.
    return generate_inline(args.input, args.output)


if __name__ == "__main__":
    sys.exit(main())
