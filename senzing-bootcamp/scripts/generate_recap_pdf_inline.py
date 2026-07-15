#!/usr/bin/env python3
"""Self-contained inline fallback for bootcamp recap PDF generation.

Converts ``docs/bootcamp_recap.md`` into ``docs/bootcamp_recap.pdf`` without
depending on the bundled ``generate_recap_pdf.py`` helper being importable from
the bootcamper's workspace. It is used by the graduation flow (Step 0b.3) when
the bundled helper cannot be located or run.

PDF production is routed through the guaranteed three-tier strategy
(``pdf_render_strategy.ensure_recap_pdf``) so the inline fallback ALSO always
produces a valid PDF: Tier 1 renders with the professional fpdf2 renderer when
fpdf2 is importable, Tier 2 attempts a best-effort guarded autoinstall, and
Tier 3 falls back to the stdlib-only writer. Because ``pdf_render_strategy``
transitively depends on ``generate_recap_pdf`` (it imports the recap parser and
model at its own top level), importing the strategy also gives access to the
recap parser used to build the ``RecapDocument`` handed to the strategy.

Only when neither ``pdf_render_strategy`` nor ``generate_recap_pdf`` can be
imported (a degenerate workspace shipping just this script and the shared
renderer) does it degrade to rendering the raw Markdown body with the shared
``recap_pdf_render`` module. The optional ``fpdf2`` dependency (``import fpdf``)
is imported lazily inside the render paths and is never a top-level import.

Usage:
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --input recap.md
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --output recap.pdf
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --no-autoinstall
    python senzing-bootcamp/scripts/generate_recap_pdf_inline.py --timeout 60
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from recap_pdf_render import (
    PdfVerificationError,
    render_markdown_pdf,
    split_blocks,
    verify_rendered_pdf,
)

# Hint surfaced only in the degenerate last-resort raw path (strategy modules
# absent) when the optional fpdf2 dependency is also missing. The primary
# strategy path guarantees a PDF via the stdlib writer, so a missing fpdf2 is no
# longer the failure path there.
_FPDF_HINT = "fpdf2 is required. Install with: pip install fpdf2"


# ---------------------------------------------------------------------------
# Tier-strategy reuse
# ---------------------------------------------------------------------------


def _import_tier_strategy() -> (
    tuple[
        Callable[..., str],
        Callable[[str], object],
        Callable[..., tuple[list[int], list[str]]],
        Callable[..., bool],
        int,
    ]
    | None
):
    """Import the guaranteed-PDF tier strategy and recap parser, if available.

    Uses the documented ``sys.path`` pattern to make the sibling scripts
    importable from this script's directory. ``pdf_render_strategy`` imports the
    recap parser/model from ``generate_recap_pdf`` at its own top level, so a
    successful import of the strategy implies ``generate_recap_pdf`` is importable
    too; both are imported here so a missing dependency on either resolves to
    ``None`` and the caller falls back to the embedded raw renderer. Every name
    imported here is stdlib-safe at import time (``fpdf`` is imported lazily
    inside the render functions), so this never makes fpdf2 a hard dependency.

    Returns:
        A tuple of ``(ensure_recap_pdf, parse_recap_markdown,
        collect_verification_targets, resolve_allow_autoinstall,
        DEFAULT_AUTOINSTALL_TIMEOUT_S)`` when importable, else ``None``.
    """
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from generate_recap_pdf import (  # noqa: PLC0415
            collect_verification_targets,
            parse_recap_markdown,
        )
        from pdf_render_strategy import (  # noqa: PLC0415
            DEFAULT_AUTOINSTALL_TIMEOUT_S,
            ensure_recap_pdf,
            resolve_allow_autoinstall,
        )
    except ImportError:
        return None
    return (
        ensure_recap_pdf,
        parse_recap_markdown,
        collect_verification_targets,
        resolve_allow_autoinstall,
        DEFAULT_AUTOINSTALL_TIMEOUT_S,
    )


# ---------------------------------------------------------------------------
# Inline generation
# ---------------------------------------------------------------------------


def generate_inline(
    input_path: str,
    output_path: str,
    *,
    allow_autoinstall: bool | None = None,
    timeout_s: int | None = None,
) -> int:
    """Generate the recap PDF without depending on the bundled helper.

    Routes PDF production through the guaranteed three-tier strategy
    (``pdf_render_strategy.ensure_recap_pdf``) whenever it is importable, so a
    valid PDF is ALWAYS produced (rich fpdf2, best-effort autoinstall, or the
    stdlib-only writer). Only when neither the strategy nor ``generate_recap_pdf``
    can be imported does it degrade to rendering the raw Markdown body with the
    embedded renderer, which still depends on a lazily imported ``fpdf2`` and
    surfaces a ``pip install fpdf2`` hint when that dependency is also absent.
    The written PDF is round-trip verified before success is reported.

    Args:
        input_path: Path to the recap Markdown input.
        output_path: Path for the generated PDF output.
        allow_autoinstall: Whether a best-effort ``pip install fpdf2`` may run in
            the strategy path. ``None`` (the default) resolves the opt-out from
            the environment/preferences; ``False`` forces straight to the stdlib
            writer. Ignored on the degenerate raw-render fallback path.
        timeout_s: Bounded timeout (seconds) for the guarded autoinstall.
            ``None`` uses the strategy's built-in bounded default.

    Returns:
        Exit code: 0 when a PDF was written and verified, 1 otherwise.
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

    # Prefer the guaranteed tier strategy; fall back to the raw renderer only
    # when the strategy modules are not importable in this workspace.
    strategy = _import_tier_strategy()
    try:
        if strategy is not None:
            (
                ensure_recap_pdf,
                parse_recap_markdown,
                collect_targets,
                resolve_allow_autoinstall,
                default_timeout,
            ) = strategy
            doc = parse_recap_markdown(content)
            module_numbers, expected_body_lines = collect_targets(doc, content)
            # --no-autoinstall (allow_autoinstall=False) forces the opt-out;
            # None resolves from env/preferences (Requirement 3.3). Timeout
            # falls back to the strategy's bounded default.
            resolved_allow = (
                resolve_allow_autoinstall()
                if allow_autoinstall is None
                else allow_autoinstall
            )
            resolved_timeout = default_timeout if timeout_s is None else timeout_s
            # The strategy guarantees a valid PDF at output_path (rich fpdf2 when
            # available, else autoinstall, else the stdlib writer) and reports
            # the chosen tier to stderr (Requirement 2.4).
            ensure_recap_pdf(
                doc,
                output_path,
                allow_autoinstall=resolved_allow,
                timeout_s=resolved_timeout,
                body_text=content,
            )
        else:
            # Degenerate last resort: neither the tier strategy nor the bundled
            # helper is importable, so render the raw Markdown body directly.
            # This path still depends on the lazily imported fpdf2; when fpdf2 is
            # also absent no PDF can be produced (handled below).
            render_markdown_pdf(content, output_path)
            module_numbers, expected_body_lines = [], split_blocks(content)
    except ImportError:
        # Reachable only via the degenerate raw path above when fpdf2 is absent;
        # the strategy path guarantees a PDF without fpdf2. Degrade gracefully
        # with a hint, no traceback.
        print(_FPDF_HINT, file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to write PDF: {exc}", file=sys.stderr)
        return 1

    # Only report success when a PDF file was actually written.
    if not Path(output_path).exists():
        print(f"Failed to write PDF: no output produced at {output_path}", file=sys.stderr)
        return 1

    # Round-trip verification: confirm the written PDF carries a section for every
    # completed module plus at least MIN_BODY_LINES body lines before reporting
    # success, so a render that dropped body content fails loudly rather than
    # reporting a successful PDF (Req 2.6, 2.7). The full-width fix is inherited
    # from the Shared_Renderer.
    try:
        verify_rendered_pdf(output_path, module_numbers, expected_body_lines)
    except PdfVerificationError as exc:
        print(f"PDF verification failed: {exc}", file=sys.stderr)
        return 1

    print(f"PDF generated: {output_path}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Mirrors ``generate_recap_pdf.py`` / ``pdf_render_strategy.py`` so the scripts
    are interchangeable, including the autoinstall opt-out and timeout controls.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with ``input``, ``output``, ``no_autoinstall``, and
        ``timeout``.
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
    parser.add_argument(
        "--no-autoinstall",
        action="store_true",
        help=(
            "Disable the best-effort 'pip install fpdf2' and go straight to the "
            "stdlib writer when fpdf2 is absent (overrides env/preferences)."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=(
            "Bounded timeout in seconds for the guarded fpdf2 autoinstall "
            "(default: the tier strategy's built-in bounded timeout)."
        ),
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
    # --no-autoinstall forces the opt-out; otherwise allow_autoinstall stays None
    # so generate_inline resolves it from env/preferences (Requirement 3.3).
    allow_autoinstall = False if args.no_autoinstall else None
    return generate_inline(
        args.input,
        args.output,
        allow_autoinstall=allow_autoinstall,
        timeout_s=args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
