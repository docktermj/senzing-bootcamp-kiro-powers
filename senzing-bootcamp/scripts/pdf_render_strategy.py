#!/usr/bin/env python3
"""Central tier-selection strategy for the guaranteed recap PDF (three tiers).

Guarantees that a real ``docs/bootcamp_recap.pdf`` is always produced by
choosing, at render time, the best renderer the environment allows while
keeping ``fpdf2`` an optional, lazily imported dependency:

* **Tier 1 - rich:** ``fpdf2`` is importable -> render with the professional
  fpdf2 renderer (``generate_recap_pdf.render_pdf``). Unchanged behavior.
* **Tier 2 - autoinstalled:** ``fpdf2`` is absent but autoinstall is allowed ->
  a single, best-effort, timeout-bounded ``python -m pip install fpdf2`` is
  attempted; on success (and a successful re-probe) the rich renderer is used.
* **Tier 3 - stdlib:** ``fpdf2`` is absent and autoinstall is disabled, failed,
  offline, or timed out -> render with the stdlib-only writer
  (``recap_pdf_minimal.render_minimal_pdf``). This tier needs no third-party
  packages, so it is the actual guarantee.

The autoinstall is best-effort and always safe to fail: any failure (offline,
permissions, pip missing, timeout) falls through to the stdlib writer without
raising and without blocking graduation. It is attempted at most once per
render invocation. ``fpdf`` is never imported at module top level.

``allow_autoinstall`` defaults to enabled and can be turned off (for locked-down
environments) through the ``SENZING_BOOTCAMP_PDF_AUTOINSTALL`` environment
variable or a ``pdf_autoinstall`` key in ``config/bootcamp_preferences.yaml``;
the environment variable, when set, wins over the preferences key.

Usage:
    python senzing-bootcamp/scripts/pdf_render_strategy.py
    python senzing-bootcamp/scripts/pdf_render_strategy.py --input recap.md
    python senzing-bootcamp/scripts/pdf_render_strategy.py --output recap.pdf
    python senzing-bootcamp/scripts/pdf_render_strategy.py --no-autoinstall
    python senzing-bootcamp/scripts/pdf_render_strategy.py --timeout 60
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

# Scripts are not packages, so make this file's directory importable to resolve
# the sibling modules whether run directly or imported via the documented
# sys.path pattern. Every sibling imported here is stdlib-only at import time
# (``fpdf`` is imported lazily inside the render functions, never at module top
# level), so importing them keeps this strategy independent of fpdf2 and lets
# the module import cleanly when fpdf2 is absent (Requirement 5.1).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import (  # noqa: E402
    RecapDocument,
    collect_verification_targets,
    parse_recap_markdown,
    render_pdf,
)
from preferences_utils import load_preferences  # noqa: E402
from recap_pdf_minimal import render_minimal_pdf  # noqa: E402
from recap_pdf_render import (  # noqa: E402
    PdfVerificationError,
    verify_rendered_pdf,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Environment variable that overrides the autoinstall opt-out (Requirement 3.3).
AUTOINSTALL_ENV_VAR = "SENZING_BOOTCAMP_PDF_AUTOINSTALL"

#: Preferences key consulted when the environment variable is unset (Req 3.3).
PREFERENCES_AUTOINSTALL_KEY = "pdf_autoinstall"

#: Default preferences file consulted by :func:`resolve_allow_autoinstall`.
DEFAULT_PREFERENCES_PATH = "config/bootcamp_preferences.yaml"

#: Autoinstall is enabled by default; it is always safe to fail (Req 3.1-3.3).
DEFAULT_ALLOW_AUTOINSTALL = True

#: Bounded default timeout (seconds) for the guarded pip install (Req 3.1).
DEFAULT_AUTOINSTALL_TIMEOUT_S = 120

#: Tier identifiers returned by :func:`ensure_recap_pdf`.
TIER_RICH = "rich"
TIER_AUTOINSTALLED = "autoinstalled"
TIER_STDLIB = "stdlib"

# Human-readable one-line report per tier (Requirement 2.4). Printed to stderr
# so the stdout ``PDF generated:`` contract of the CLI callers is preserved.
_TIER_REPORTS: dict[str, str] = {
    TIER_RICH: "Recap PDF rendered with the fpdf2 rich renderer (tier: rich).",
    TIER_AUTOINSTALLED: (
        "Recap PDF rendered with the fpdf2 rich renderer after installing "
        "fpdf2 (tier: autoinstalled)."
    ),
    TIER_STDLIB: (
        "Recap PDF rendered with the stdlib-only writer (tier: stdlib)."
    ),
}

# Strings that resolve the opt-out to a definite boolean; anything else is
# treated as "unspecified" so resolution falls through to the next source.
_TRUE_TOKENS = frozenset({"1", "true", "yes", "on", "enable", "enabled"})
_FALSE_TOKENS = frozenset({"0", "false", "no", "off", "disable", "disabled"})


# ---------------------------------------------------------------------------
# fpdf2 availability probe (monkeypatchable)
# ---------------------------------------------------------------------------


def fpdf2_available() -> bool:
    """Return True iff the optional ``fpdf2`` dependency can be imported.

    Probes availability with a guarded ``import fpdf`` treating ``ImportError``
    as "absent", mirroring ``fpdf2_preflight.fpdf2_available`` and the lazy
    imports in the render paths. The import is confined to this function body so
    importing ``pdf_render_strategy`` never requires ``fpdf2`` and ``fpdf`` is
    never a top-level or hard dependency (Requirement 5.1). Defined at module
    level so tests can monkeypatch it to simulate presence/absence.

    Returns:
        True if ``import fpdf`` succeeds, False if it raises ``ImportError``.
    """
    try:
        import fpdf  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Guarded, best-effort autoinstall (monkeypatchable)
# ---------------------------------------------------------------------------


def attempt_autoinstall(timeout_s: int) -> bool:
    """Best-effort ``python -m pip install fpdf2`` with a bounded timeout.

    Runs the standard installer for the active interpreter exactly once (no
    retry loop) and never raises: any failure - pip missing, offline,
    permissions, non-zero exit, or exceeding ``timeout_s`` - is caught and
    reported as ``False`` so the caller falls through to the stdlib writer
    without blocking graduation (Requirements 3.1, 3.2, 3.4, 3.5). Defined at
    module level so tests can monkeypatch it (or the ``subprocess`` call within)
    without performing a real network install.

    Args:
        timeout_s: Maximum seconds to allow the install to run.

    Returns:
        True only when the installer exits with status 0; False otherwise.
    """
    try:
        result = subprocess.run(  # noqa: S603 - fixed, non-user-controlled argv
            [sys.executable, "-m", "pip", "install", "fpdf2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        # OSError covers a missing/unexecutable interpreter; SubprocessError
        # covers TimeoutExpired and other subprocess failures. Never re-raised.
        return False
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Tier reporting (Requirement 2.4)
# ---------------------------------------------------------------------------


def report_tier(tier: str) -> None:
    """Print a one-line report of which tier produced the PDF, to stderr.

    Reporting to stderr keeps the stdout ``PDF generated:`` contract of the CLI
    callers intact while still making the chosen tier visible to the maintainer
    (Requirement 2.4). An unrecognized tier is reported generically.

    Args:
        tier: One of :data:`TIER_RICH`, :data:`TIER_AUTOINSTALLED`,
            :data:`TIER_STDLIB`.
    """
    message = _TIER_REPORTS.get(tier, f"Recap PDF rendered (tier: {tier}).")
    print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
# allow_autoinstall resolution
# ---------------------------------------------------------------------------


def _coerce_opt_out(raw: object) -> bool | None:
    """Coerce a raw env/preferences value to a definite bool, or None.

    Args:
        raw: A raw value from the environment (str) or the parsed preferences
            (str/bool/None/int).

    Returns:
        True/False when the value is an unambiguous on/off token (or already a
        bool); None when the value is absent or unrecognized so resolution can
        fall through to the next source.
    """
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return None
    token = str(raw).strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    return None


def _preferences_opt_out(preferences_path: str) -> bool | None:
    """Read the autoinstall opt-out from the preferences file, if present.

    Uses the shared stdlib YAML loader; never raises. A missing file, unreadable
    file, invalid YAML, or absent key all resolve to ``None`` so the default
    applies.

    Args:
        preferences_path: Path to ``config/bootcamp_preferences.yaml``.

    Returns:
        The coerced boolean for the ``pdf_autoinstall`` key, or None.
    """
    try:
        result = load_preferences(preferences_path, required_fields=())
    except Exception:  # noqa: BLE001 - resolution must never raise (Req 3.2).
        return None
    prefs = result.preferences
    if not prefs:
        return None
    return _coerce_opt_out(prefs.get(PREFERENCES_AUTOINSTALL_KEY))


def resolve_allow_autoinstall(
    *,
    env: Mapping[str, str] | None = None,
    preferences_path: str = DEFAULT_PREFERENCES_PATH,
) -> bool:
    """Resolve whether autoinstall is allowed (env var wins, then preferences).

    Resolution order (Requirement 3.3):

    1. ``SENZING_BOOTCAMP_PDF_AUTOINSTALL`` environment variable, when set to a
       recognized on/off token.
    2. The ``pdf_autoinstall`` key in ``config/bootcamp_preferences.yaml``.
    3. The default, :data:`DEFAULT_ALLOW_AUTOINSTALL` (enabled).

    Args:
        env: Environment mapping to consult (defaults to ``os.environ``).
        preferences_path: Path to the preferences file.

    Returns:
        True when autoinstall is permitted, False when it is opted out.
    """
    environ = os.environ if env is None else env
    from_env = _coerce_opt_out(environ.get(AUTOINSTALL_ENV_VAR))
    if from_env is not None:
        return from_env
    from_prefs = _preferences_opt_out(preferences_path)
    if from_prefs is not None:
        return from_prefs
    return DEFAULT_ALLOW_AUTOINSTALL


# ---------------------------------------------------------------------------
# Tier dispatch
# ---------------------------------------------------------------------------


def _try_rich(doc: RecapDocument, out_path: str, body_text: str) -> bool:
    """Attempt the rich fpdf2 render; return True on success, False on failure.

    Guarded so a rendering problem never crashes graduation (Requirement 5.2):
    any exception (including a genuine or test-simulated ``ImportError`` when
    ``fpdf2`` vanished between probe and render) is caught and reported so the
    caller can fall through to the stdlib writer.

    Args:
        doc: The parsed recap document.
        out_path: Destination path for the rendered PDF.
        body_text: Raw recap Markdown for the Raw_Body_Fallback when ``doc`` has
            no parsed sections.

    Returns:
        True when the rich renderer produced the PDF, False otherwise.
    """
    try:
        render_pdf(doc, out_path, body_text=body_text)
        return True
    except Exception as exc:  # noqa: BLE001 - non-blocking guarantee (Req 5.2).
        print(
            f"fpdf2 rich render failed ({exc}); falling back to the stdlib "
            "PDF writer.",
            file=sys.stderr,
        )
        return False


def ensure_recap_pdf(
    doc: RecapDocument,
    out_path: str | Path,
    *,
    allow_autoinstall: bool,
    timeout_s: int,
    body_text: str = "",
) -> str:
    """Render a guaranteed recap PDF using the best available tier.

    Probes for ``fpdf2`` and dispatches:

    * fpdf2 present -> Tier 1 rich renderer (``"rich"``).
    * fpdf2 absent + ``allow_autoinstall`` -> a single guarded, timeout-bounded
      ``pip install fpdf2``; on success and a successful re-probe -> Tier 1
      (``"autoinstalled"``); otherwise -> Tier 3 (``"stdlib"``).
    * fpdf2 absent + autoinstall disabled -> Tier 3 directly, with NO subprocess
      call (``"stdlib"``).

    The autoinstall is attempted at most once per invocation (Requirement 3.5)
    and is always safe to fail. A rich-render failure falls through to the
    stdlib writer so the flow never crashes (Requirement 5.2). The chosen tier
    is reported to stderr (Requirement 2.4) and returned.

    Args:
        doc: The parsed recap document to render.
        out_path: Destination path for the generated PDF.
        allow_autoinstall: Whether a best-effort ``pip install fpdf2`` may run.
        timeout_s: Bounded timeout (seconds) for the guarded install.
        body_text: Raw recap Markdown for the Raw_Body_Fallback when ``doc`` has
            no parsed sections. Passed through to whichever renderer is used.

    Returns:
        The tier used: ``"rich"``, ``"autoinstalled"``, or ``"stdlib"``.
    """
    target = str(out_path)

    # Tier 1: fpdf2 already importable.
    if fpdf2_available():
        if _try_rich(doc, target, body_text):
            report_tier(TIER_RICH)
            return TIER_RICH
        render_minimal_pdf(doc, target, body_text=body_text)
        report_tier(TIER_STDLIB)
        return TIER_STDLIB

    # Tier 2: absent, but a single guarded autoinstall is permitted.
    if allow_autoinstall and attempt_autoinstall(timeout_s) and fpdf2_available():
        if _try_rich(doc, target, body_text):
            report_tier(TIER_AUTOINSTALLED)
            return TIER_AUTOINSTALLED

    # Tier 3: the stdlib-only guarantee (install disabled, failed, or rich
    # render fell through). Reached with NO subprocess call when autoinstall is
    # disabled, because the short-circuit above never evaluates attempt_autoinstall.
    render_minimal_pdf(doc, target, body_text=body_text)
    report_tier(TIER_STDLIB)
    return TIER_STDLIB


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Mirrors ``generate_recap_pdf.py`` / ``recap_pdf_minimal.py`` so the scripts
    are interchangeable, adding the autoinstall opt-out and timeout controls.

    Args:
        argv: Argument list to parse. Defaults to ``sys.argv[1:]``.

    Returns:
        Parsed namespace with ``input``, ``output``, ``no_autoinstall``, and
        ``timeout``.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Render a guaranteed bootcamp recap PDF via the three-tier "
            "strategy (rich fpdf2 -> guarded autoinstall -> stdlib writer)."
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
        default=DEFAULT_AUTOINSTALL_TIMEOUT_S,
        help=(
            "Bounded timeout in seconds for the guarded autoinstall "
            f"(default: {DEFAULT_AUTOINSTALL_TIMEOUT_S})"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point: render a guaranteed recap PDF via the tier strategy.

    Reads and parses the recap Markdown, resolves whether autoinstall is
    allowed, renders through :func:`ensure_recap_pdf` into a temporary file,
    verifies the written PDF round-trips its module sections and body content,
    and only then publishes it atomically to the output path. On verification or
    write failure the temporary file is removed and no output is overwritten.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    args = parse_args(argv)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Recap file not found: {args.input}", file=sys.stderr)
        return 1
    content = input_path.read_text(encoding="utf-8")
    if not content.strip():
        print(f"Recap file is empty: {args.input}", file=sys.stderr)
        return 1

    doc = parse_recap_markdown(content)
    module_numbers, expected_body_lines = collect_verification_targets(doc, content)

    # --no-autoinstall forces the opt-out; otherwise resolve from env/preferences.
    allow_autoinstall = False if args.no_autoinstall else resolve_allow_autoinstall()

    output_path = Path(args.output)
    directory = output_path.parent if str(output_path.parent) else Path(".")

    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(directory), prefix=f"{output_path.name}.", suffix=".tmp"
        )
        os.close(fd)
        ensure_recap_pdf(
            doc,
            tmp_path,
            allow_autoinstall=allow_autoinstall,
            timeout_s=args.timeout,
            body_text=content,
        )
        verify_rendered_pdf(tmp_path, module_numbers, expected_body_lines)
        os.replace(tmp_path, str(output_path))
        tmp_path = None
    except PdfVerificationError as exc:
        print(f"PDF verification failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Failed to write PDF: {exc}", file=sys.stderr)
        return 1
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    print(f"PDF generated: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
