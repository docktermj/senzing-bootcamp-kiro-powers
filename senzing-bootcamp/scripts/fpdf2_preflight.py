#!/usr/bin/env python3
"""Senzing Bootcamp - fpdf2 Preflight Note.

Surfaces a single, non-blocking informational note at Track_Completion, *before*
any PDF render is attempted, telling a bootcamper that installing the optional
``fpdf2`` dependency will produce a PDF (and that the Markdown output is produced
regardless), including the exact command ``pip install fpdf2``.

The note appears **only** when ``fpdf2`` is not importable and is suppressed
entirely when it is present, so there is no noise in the common case where the
PDF will succeed. Availability is detected exactly as the PDF scripts do — a
guarded ``import fpdf`` treating ``ImportError`` as "absent" — and ``fpdf`` is
never imported at module top level, keeping it an optional, lazily-imported
dependency (see python-conventions.md and tech.md).

Usage:
    python senzing-bootcamp/scripts/fpdf2_preflight.py

    # When fpdf2 is absent, prints the one-line Preflight_Note (exit 0).
    # When fpdf2 is available, prints nothing (exit 0).
"""

from __future__ import annotations

import argparse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Single source of truth for the Preflight_Note text, shared by preflight_note()
# and the tests. Single line (no embedded newline): states that installing fpdf2
# enables the PDF, that the Markdown output is produced regardless, and contains
# the exact substring "pip install fpdf2" (Requirements 1.1, 1.2).
PREFLIGHT_NOTE = (
    "Note: install fpdf2 (pip install fpdf2) to also produce a PDF at "
    "track completion; the Markdown output is produced regardless."
)


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------


def fpdf2_available() -> bool:
    """Return True iff the optional fpdf2 dependency can be imported.

    Detects availability the same way the PDF scripts do — a guarded
    ``import fpdf`` treating ``ImportError`` as "absent" (Requirement 3.2),
    mirroring ``generate_completion_summary.ensure_fpdf2`` and the lazy
    ``from fpdf import FPDF`` in the render paths. The import is confined to
    the function body so importing ``fpdf2_preflight`` never requires ``fpdf2``
    and ``fpdf`` is never a top-level or hard dependency (Requirement 2.3).

    Returns:
        True if ``import fpdf`` succeeds, False if it raises ``ImportError``.
    """
    try:
        import fpdf  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Preflight note
# ---------------------------------------------------------------------------


def preflight_note() -> str | None:
    """Return the one-line Preflight_Note, or None when no note is needed.

    Pure function of :func:`fpdf2_available`. Returns ``None`` when ``fpdf2``
    is available (Requirement 1.3 — no noise when the PDF will succeed). When
    ``fpdf2`` is absent, returns the single-line :data:`PREFLIGHT_NOTE`
    constant, which states that installing ``fpdf2`` enables the PDF, that the
    Markdown output is produced regardless, and contains the exact command
    ``pip install fpdf2`` (Requirements 1.1, 1.2).

    Returns:
        ``None`` when ``fpdf2`` is available; otherwise the one-line
        Preflight_Note string.
    """
    if fpdf2_available():
        return None
    return PREFLIGHT_NOTE


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Print the Preflight_Note when fpdf2 is absent; print nothing otherwise.

    Non-blocking and informational: prints at most one line to stdout, never
    prompts or pauses, and always returns 0 (Requirement 2.1). The
    ``preflight_note()`` call and print are guarded so that any unexpected
    exception is swallowed and ``main`` still returns 0 without raising — the
    track-completion flow is never blocked, even if probing the optional import
    raises something other than ``ImportError``.

    Args:
        argv: Optional list of command-line arguments (defaults to sys.argv).

    Returns:
        Always 0 (the step never blocks the track-completion flow).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        note = preflight_note()
        if note is not None:
            print(note)
    except Exception:  # noqa: BLE001 - non-blocking by contract (Req 2.1)
        # Any unexpected error while probing the optional import must not block
        # the track-completion flow: print nothing and still return 0.
        pass
    return 0


if __name__ == "__main__":
    main()
