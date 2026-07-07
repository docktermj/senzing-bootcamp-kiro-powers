#!/usr/bin/env python3
"""Stdlib-only raw-Markdown → HTML rendering for the bootcamp recap.

This module is the HTML analogue of ``recap_pdf_render.py``: it serializes the
recap Markdown (``docs/bootcamp_recap.md``) into a single self-contained
``.html`` document. Unlike the PDF renderer it has **no ``fpdf`` dependency at
all** — importing this module never requires the optional ``fpdf2`` package — so
a shareable rendered recap is always producible when ``fpdf2`` is absent
(Requirements 4.3, 4.5, 6.1).

It reuses the canonical block model already established in ``recap_pdf_render``
(``split_blocks``, ``parse_list_block``, and the Paired_Schema QR literals) and
serializes each block to safe HTML via :func:`html.escape`. The output is a
single self-contained file (inline ``<style>``, no external URLs) whose body
reflects every per-module section present in the source recap (Requirement 4.6).

Usage:
    python senzing-bootcamp/scripts/recap_html_render.py
    python senzing-bootcamp/scripts/recap_html_render.py --input recap.md
    python senzing-bootcamp/scripts/recap_html_render.py --output recap.html
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from recap_pdf_render import (
    _QUESTION_PREFIX,
    _RESPONSE_PREFIX,
    parse_list_block,
    split_blocks,
)

# Bold labels that mark a Question_Item / Response_Item in a rendered QR_Pair
# list block. Derived from the Paired_Schema prefixes (``- **Q:** `` /
# ``- **R:** ``) with the list marker stripped, so the HTML renderer tags QR
# items with semantic CSS classes without re-declaring the schema literals.
_QUESTION_LABEL = _QUESTION_PREFIX.lstrip("- ").rstrip()
_RESPONSE_LABEL = _RESPONSE_PREFIX.lstrip("- ").rstrip()

# Inline, self-contained stylesheet (no external URLs) embedded in every
# rendered document so the HTML is shareable as a single file (Requirement 4.6).
_STYLE = """\
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
       line-height: 1.5; max-width: 48rem; margin: 2rem auto; padding: 0 1rem;
       color: #1a1a1a; }
h1 { font-size: 1.9rem; border-bottom: 2px solid #ddd; padding-bottom: 0.3rem; }
h2 { font-size: 1.5rem; margin-top: 2rem; border-bottom: 1px solid #eee;
     padding-bottom: 0.2rem; }
h3 { font-size: 1.2rem; margin-top: 1.4rem; color: #333; }
code { font-family: SFMono-Regular, Consolas, Menlo, monospace;
       background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 3px; }
pre { background: #f4f4f4; padding: 0.8rem; border-radius: 5px; overflow-x: auto; }
pre code { background: none; padding: 0; }
ul, ol { margin: 0.4rem 0; }
li.qr-question { margin-top: 0.6rem; }
li.qr-response { color: #444; }
"""


def _inline_html(text: str) -> str:
    """Escape ``text`` and convert inline Markdown emphasis to safe HTML.

    Escapes HTML-significant characters first (so no raw markup survives), then
    promotes inline code spans (backtick-delimited) to ``<code>`` and bold spans
    (``**bold**``) to ``<strong>``. The emphasis markers are not touched by
    :func:`html.escape`, so operating on the escaped text is safe.

    Args:
        text: Raw Markdown inline text.

    Returns:
        Escaped HTML with inline code and bold rendered.
    """
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def _list_class(text: str) -> str:
    """Return the CSS class for a list item based on the Paired_Schema labels.

    Args:
        text: The list item's text (marker already stripped).

    Returns:
        ``' class="qr-question"'`` / ``' class="qr-response"'`` for QR items, or
        an empty string for ordinary list items.
    """
    stripped = text.lstrip()
    if stripped.startswith(_QUESTION_LABEL):
        return ' class="qr-question"'
    if stripped.startswith(_RESPONSE_LABEL):
        return ' class="qr-response"'
    return ""


def _list_to_html(triples: list[tuple[int, bool, str]]) -> str:
    """Serialize parsed list triples into nested ``<ul>``/``<ol>`` markup.

    Uses a stack keyed on nesting level so that deeper items (for example a
    Response_Item nested beneath its Question_Item) are wrapped in an inner
    list, and every opened list is closed. Ordered items render as ``<ol>``,
    bulleted items as ``<ul>``.

    Args:
        triples: ``(level, numbered, text)`` triples from
            :func:`parse_list_block`, in document order.

    Returns:
        The nested list markup as a single HTML string.
    """
    out: list[str] = []
    stack: list[str] = []
    prev_level = -1
    for level, numbered, text in triples:
        tag = "ol" if numbered else "ul"
        if level > prev_level:
            for _ in range(level - prev_level):
                out.append(f"<{tag}>")
                stack.append(tag)
        elif level < prev_level:
            for _ in range(prev_level - level):
                out.append(f"</{stack.pop()}>")
        out.append(f"<li{_list_class(text)}>{_inline_html(text)}</li>")
        prev_level = level
    while stack:
        out.append(f"</{stack.pop()}>")
    return "".join(out)


def markdown_to_html_body(body_text: str) -> str:
    """Serialize recap Markdown body text into an HTML fragment.

    Splits ``body_text`` into canonical blocks via :func:`split_blocks` and
    serializes each to safe HTML: ATX headings (``#``..``######``) become
    ``<h1>``..``<h6>``, fenced code blocks become ``<pre><code>`` (fences
    stripped), bulleted/numbered lists become nested ``<ul>``/``<ol>``, and
    everything else becomes a ``<p>`` paragraph. All text is escaped with
    :func:`html.escape`, so no source content is interpreted as raw markup
    (Requirement 4.3). Every per-module ``## Module N`` heading in the source is
    reflected as an ``<h2>`` in the output (Requirement 4.6).

    Args:
        body_text: Raw recap Markdown body.

    Returns:
        The serialized HTML body fragment (no surrounding document chrome).
    """
    parts: list[str] = []
    for block in split_blocks(body_text):
        lines = block.splitlines()
        first = lines[0].lstrip() if lines else ""

        # Fenced code block — strip the opening/closing fence lines.
        if first.startswith("```"):
            code_lines = lines[1:]
            if code_lines and code_lines[-1].lstrip().startswith("```"):
                code_lines = code_lines[:-1]
            code = html.escape("\n".join(code_lines))
            parts.append(f"<pre><code>{code}</code></pre>")
            continue

        # ATX heading (single-line block beginning with one to six '#').
        heading = re.match(r"^(#{1,6})\s+(.+)$", first)
        if heading and len(lines) == 1:
            level = len(heading.group(1))
            parts.append(f"<h{level}>{_inline_html(heading.group(2).strip())}</h{level}>")
            continue

        # List block — the first non-blank line begins with a list marker.
        non_blank = [ln for ln in lines if ln.strip()]
        if non_blank and re.match(r"^\s*(?:-|\*|\d+\.)\s+", non_blank[0]):
            triples = parse_list_block(block)
            if triples:
                parts.append(_list_to_html(triples))
                continue

        # Prose paragraph — preserve internal line breaks.
        paragraph = _inline_html(block).replace("\n", "<br>\n")
        parts.append(f"<p>{paragraph}</p>")

    return "\n".join(parts)


def render_markdown_html(
    body_text: str,
    output_path: str,
    *,
    title: str = "Bootcamp Recap",
) -> None:
    """Render recap Markdown to a single self-contained HTML document.

    Serializes ``body_text`` via :func:`markdown_to_html_body` and wraps it in a
    complete HTML5 document with an inline ``<style>`` block and no external
    URLs, then writes it to ``output_path``. This function never imports
    ``fpdf`` (Requirement 4.5).

    Args:
        body_text: Raw recap Markdown body.
        output_path: File path for the generated HTML document.
        title: Document title, rendered in ``<title>`` and as the top heading.

    Raises:
        OSError: If the HTML cannot be written to ``output_path``.
    """
    body_html = markdown_to_html_body(body_text)
    escaped_title = html.escape(title)
    document = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escaped_title}</title>\n"
        f"<style>\n{_STYLE}</style>\n"
        "</head>\n"
        "<body>\n"
        f"<h1>{escaped_title}</h1>\n"
        f"{body_html}\n"
        "</body>\n"
        "</html>\n"
    )
    Path(output_path).write_text(document, encoding="utf-8")


def render_from_file(input_path: str, output_path: str) -> int:
    """Render the recap Markdown at ``input_path`` to HTML at ``output_path``.

    Validates that the input exists and is non-empty, renders it, and reports
    the written path on stdout. Errors go to stderr and yield a non-zero exit
    code.

    Args:
        input_path: Path to the recap Markdown input.
        output_path: Path for the generated HTML output.

    Returns:
        Exit code: 0 when an HTML document was written, 1 otherwise.
    """
    in_path = Path(input_path)
    if not in_path.exists():
        print(f"Recap file not found: {input_path}", file=sys.stderr)
        return 1
    content = in_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"Recap file is empty: {input_path}", file=sys.stderr)
        return 1

    try:
        render_markdown_html(content, output_path)
    except OSError as exc:
        print(f"Failed to write HTML: {exc}", file=sys.stderr)
        return 1

    print(f"HTML generated: {output_path}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with input and output paths.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Render the bootcamp recap markdown into a self-contained HTML "
            "document (stdlib only, no fpdf2 dependency)."
        ),
    )
    parser.add_argument(
        "--input",
        default="docs/bootcamp_recap.md",
        help="Path to recap markdown (default: docs/bootcamp_recap.md)",
    )
    parser.add_argument(
        "--output",
        default="docs/bootcamp_recap.html",
        help="Path for output HTML (default: docs/bootcamp_recap.html)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the recap HTML renderer.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    return render_from_file(args.input, args.output)


if __name__ == "__main__":
    sys.exit(main())
