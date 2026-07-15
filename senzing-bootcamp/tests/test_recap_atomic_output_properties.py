"""Property-based test for atomic output safety (Property 8).

Feature: professional-recap-pdf, Property 8: Atomic output safety

**Validates: Requirements 8.2, 8.3**

For any valid recap Markdown, ``generate_recap_pdf.main`` publishes the PDF
atomically: it renders into a temporary file in the output directory, verifies
that temp file, and only ``os.replace``-es it into place on success. This test
asserts the two observable halves of that guarantee:

* Success path (Req 8.2): when ``main`` returns ``0`` the output file exists and
  is non-empty (the temp file was atomically moved into place).
* Failure path (Req 8.3): when ``main`` returns ``1`` because rendering raised an
  OS error, any pre-existing output file is left byte-for-byte unchanged.

Both paths additionally assert that no ``*.tmp`` scratch file lingers in the
output directory afterward — the temp file is either moved into place on success
or removed in the ``finally`` block on failure.

The success path constructs the real ``RecapPDF`` (built on ``fpdf.FPDF``), so it
is skipped — not errored — when the optional ``fpdf2`` dependency is absent. The
failure path monkeypatches the tier strategy's ``ensure_recap_pdf`` (the render
entry point ``main`` now uses) to raise ``OSError`` before any fpdf import
happens, so it runs regardless of whether ``fpdf2`` is installed.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ``fpdf2`` is an optional dependency. The success path renders a real PDF, so
# it must skip (not error) when fpdf2 is absent. The failure path patches
# ``render_pdf`` out and never touches fpdf, so it is unguarded.
_FPDF_AVAILABLE = importlib.util.find_spec("fpdf") is not None

# Scripts are not packages; make them importable via the documented sys.path
# pattern (conftest also does this, kept here so the module imports standalone).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf  # noqa: E402
import pdf_render_strategy  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Lowercase ASCII words only: Latin-1-safe (survive core-font rendering
# unchanged), short enough never to wrap at 20mm margins, and always >= 2
# characters so every body line has a distinctive token the verifier can find.
_ASCII_WORD = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10
)


@st.composite
def st_body_line(draw: st.DrawFn) -> str:
    """Draw a substantive single-line body item (1-4 ASCII words).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty space-joined run of lowercase ASCII words.
    """
    words = draw(st.lists(_ASCII_WORD, min_size=1, max_size=4))
    return " ".join(words)


@st.composite
def st_module_name(draw: st.DrawFn) -> str:
    """Draw a simple capitalized module/bootcamper name (1-3 ASCII words).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty space-joined run of capitalized ASCII words.
    """
    words = draw(st.lists(_ASCII_WORD, min_size=1, max_size=3))
    return " ".join(word.capitalize() for word in words)


@st.composite
def st_qr_pair(draw: st.DrawFn) -> tuple[str, str]:
    """Draw one substantive ``(question, response)`` pair.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(question, response)`` tuple of non-empty body lines.
    """
    return draw(st_body_line()), draw(st_body_line())


@st.composite
def st_started(draw: st.DrawFn) -> str:
    """Draw a simple ISO-style ``YYYY-MM-DD`` Started value.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty date string.
    """
    year = draw(st.integers(min_value=2024, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    return f"{year:04d}-{month:02d}-{day:02d}"


@st.composite
def st_duration(draw: st.DrawFn) -> str:
    """Draw a non-empty human-readable duration like ``2h 15m``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A duration string with an hours and a minutes component.
    """
    hours = draw(st.integers(min_value=0, max_value=100))
    minutes = draw(st.integers(min_value=0, max_value=59))
    return f"{hours}h {minutes}m"


def _build_recap_markdown(
    bootcamper: str,
    started: str,
    duration: str,
    modules: list[tuple[int, str, list[str], list[tuple[str, str]], list[str], str]],
) -> str:
    """Assemble a valid recap Markdown document from generated parts.

    Emits the canonical header fields plus one ``## Module N: <name>`` section
    per module, each carrying an ``### Information Shared`` list, an
    ``### Questions & Responses`` block in the canonical ``- **Q:** `` /
    ``    - **R:** `` format, an optional ``### Actions Taken`` list, and an
    ``### Duration`` line. This is exactly the structure ``parse_recap_markdown``
    recognizes (paired schema).

    Args:
        bootcamper: Non-empty bootcamper name.
        started: Started value.
        duration: Total duration value.
        modules: Per-module ``(number, name, info_items, qr_pairs, actions,
            duration)`` tuples.

    Returns:
        The full recap Markdown text.
    """
    lines: list[str] = [
        "# Senzing Bootcamp Recap",
        "",
        f"**Bootcamper:** {bootcamper}",
        f"**Started:** {started}",
        f"**Total Duration:** {duration}",
        "",
        "---",
        "",
    ]
    for number, name, info_items, qr_pairs, actions, module_duration in modules:
        lines.append(f"## Module {number}: {name}")
        lines.append("")
        lines.append("### Information Shared")
        for item in info_items:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("### Questions & Responses")
        for question, response in qr_pairs:
            lines.append(f"- **Q:** {question}")
            lines.append(f"    - **R:** {response}")
        lines.append("")
        if actions:
            lines.append("### Actions Taken")
            for item in actions:
                lines.append(f"- {item}")
            lines.append("")
        lines.append("### Duration")
        lines.append(module_duration)
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


@st.composite
def st_recap_markdown(draw: st.DrawFn) -> str:
    """Draw a valid recap Markdown document with 1-4 substantive modules.

    Every module carries non-empty Information Shared items and at least one
    canonical QR_Pair, so the rendered PDF always has far more than the
    ``MIN_BODY_LINES`` distinctive body tokens the post-generation verification
    requires. Module numbers are distinct so per-module verification is
    unambiguous.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        Recap Markdown text that ``main`` can parse, render, and verify.
    """
    bootcamper = draw(st_module_name())
    started = draw(st_started())
    total_duration = draw(st_duration())

    numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=1,
            max_size=4,
            unique=True,
        )
    )

    modules: list[
        tuple[int, str, list[str], list[tuple[str, str]], list[str], str]
    ] = []
    for number in numbers:
        name = draw(st_module_name())
        info_items = draw(st.lists(st_body_line(), min_size=1, max_size=3))
        qr_pairs = draw(st.lists(st_qr_pair(), min_size=1, max_size=3))
        actions = draw(st.lists(st_body_line(), min_size=0, max_size=2))
        module_duration = draw(st_duration())
        modules.append(
            (number, name, info_items, qr_pairs, actions, module_duration)
        )

    return _build_recap_markdown(bootcamper, started, total_duration, modules)


# ---------------------------------------------------------------------------
# Property 8: Atomic output safety
# ---------------------------------------------------------------------------


class TestPropertyAtomicOutputSafety:
    """Property 8: the recap PDF is published atomically.

    **Validates: Requirements 8.2, 8.3**

    Feature: professional-recap-pdf, Property 8: Atomic output safety
    """

    @pytest.mark.skipif(
        not _FPDF_AVAILABLE, reason="fpdf2 (optional dependency) not installed"
    )
    @given(markdown=st_recap_markdown())
    def test_success_writes_non_empty_output_and_no_tmp(
        self, markdown: str
    ) -> None:
        """A successful run leaves a non-empty output PDF and no ``*.tmp`` file.

        # Feature: professional-recap-pdf, Property 8: Atomic output safety

        **Validates: Requirements 8.2**

        When ``main`` returns ``0``, the verified temp file was atomically moved
        into the output path (``os.replace``), so the output file exists and is
        non-empty and no scratch ``*.tmp`` file remains beside it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            input_path = tmpdir / "recap.md"
            output_path = tmpdir / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")

            exit_code = generate_recap_pdf.main(
                ["--input", str(input_path), "--output", str(output_path)]
            )

            assert exit_code == 0, (
                "main() should succeed for valid substantive recap Markdown; "
                f"returned {exit_code}"
            )
            assert output_path.exists(), "output PDF should exist after success"
            assert output_path.stat().st_size > 0, "output PDF must be non-empty"
            assert list(tmpdir.glob("*.tmp")) == [], (
                "no scratch .tmp file should linger after a successful run"
            )

    @given(markdown=st_recap_markdown())
    def test_failure_leaves_existing_output_unchanged_and_no_tmp(
        self, markdown: str
    ) -> None:
        """A failed render leaves a pre-existing output byte-for-byte unchanged.

        # Feature: professional-recap-pdf, Property 8: Atomic output safety

        **Validates: Requirements 8.3**

        ``main`` now produces the PDF through the guaranteed tier strategy
        (``pdf_render_strategy.ensure_recap_pdf``), so the write/render failure
        is injected there (a rich-render failure alone would merely fall through
        to the stdlib tier). With ``ensure_recap_pdf`` monkeypatched to raise
        ``OSError``, ``main`` returns ``1``, the pre-existing output file's bytes
        are untouched (``os.replace`` is never reached), and the temp file is
        removed so no ``*.tmp`` scratch file lingers. This path needs no fpdf2
        because the render entry point is patched out entirely.
        """
        sentinel = b"%PDF-1.4 pre-existing recap, must not be overwritten\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            input_path = tmpdir / "recap.md"
            output_path = tmpdir / "recap.pdf"
            input_path.write_text(markdown, encoding="utf-8")
            output_path.write_bytes(sentinel)

            with patch.object(
                pdf_render_strategy,
                "ensure_recap_pdf",
                side_effect=OSError("simulated render failure"),
            ):
                exit_code = generate_recap_pdf.main(
                    ["--input", str(input_path), "--output", str(output_path)]
                )

            assert exit_code == 1, (
                "main() should return 1 when rendering raises OSError; "
                f"returned {exit_code}"
            )
            assert output_path.read_bytes() == sentinel, (
                "a failed run must leave the pre-existing output unchanged"
            )
            assert list(tmpdir.glob("*.tmp")) == [], (
                "no scratch .tmp file should linger after a failed run"
            )
