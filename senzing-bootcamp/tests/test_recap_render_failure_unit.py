"""Edge/error unit tests for the recap PDF atomic-write verification path.

Feature: recap-qr-formatting

These are example-based unit tests (not property tests) covering the
unrenderable-content error path in ``generate_recap_pdf.main`` (Requirements 4.2
and 5.2):

- Requirement 4.2: IF the renderer cannot render a QR_Pair present in the recap,
  THEN it SHALL terminate with a non-zero exit code, SHALL NOT write a recap PDF,
  and SHALL produce an error identifying the offending QR_Pair.
- Requirement 5.2: the analogous guarantee for a Split_List_Schema section — no
  recap PDF written, non-zero exit, and an error identifying the omitted content.

``main()`` renders the recap into a temporary file in the output directory, runs
``verify_rendered_pdf`` against that temp file, and only ``os.replace``-es it into
the output path on success. When verification fails it deletes the temp file (so
no recap PDF is written or overwritten), prints ``PDF verification failed: ...``
to stderr (with an ``Offending content: ...`` suffix from
``identify_unrendered_content`` when pinpointable), and returns exit code 1.

The tests drive that error path deterministically WITHOUT requiring the optional
``fpdf2`` dependency: ``render_pdf`` is monkeypatched to write a tiny stand-in PDF
whose extractable text contains only the ``Module N`` heading marker (so the
per-module check passes) but none of the QR_Pair / numbered-item body tokens (so
the real ``verify_rendered_pdf`` raises ``PdfVerificationError`` and the real
``identify_unrendered_content`` can name the offending content).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf

# A minimal PDF whose only extractable text literal is "Module 1". This makes
# verify_rendered_pdf's per-module check pass (it looks for "Module N") while the
# body-line check fails, because none of the recap's distinctive body tokens
# survive into this stand-in PDF. extract_pdf_text scans for `stream\n...
# endstream` and collects parenthesised `(...)` literals, so an uncompressed
# stream carrying "(Module 1)" is sufficient.
_STANDIN_PDF_BYTES = b"%PDF-1.4\nstream\n(Module 1) Tj\nendstream\n%%EOF\n"

_PAIRED_RECAP = """\
# Senzing Bootcamp Recap

**Bootcamper:** Tester
**Started:** 2025-01-01
**Total Duration:** 1h

---

## Module 1: Business Problem \u2014 2025-01-01

### Information Shared
- Reviewed the zorbulator overview deck

### Questions & Responses
- **Q:** What is a quixotron entity?
    - **R:** A frobnicated identity cluster keyed by splungle.

### Actions Taken
- Loaded the flimterberg dataset

### Duration
45 minutes
"""

_SPLIT_RECAP = """\
# Senzing Bootcamp Recap

**Bootcamper:** Tester
**Started:** 2025-01-01
**Total Duration:** 1h

---

## Module 1: Business Problem \u2014 2025-01-01

### Information Shared
- Reviewed the zorbulator overview deck

### Questions Asked
1. What is a quixotron entity?

### Answers Given
1. A frobnicated identity cluster keyed by splungle.

### Actions Taken
- Loaded the flimterberg dataset

### Duration
45 minutes
"""


def _write_standin_pdf(_doc, output_path: str, body_text: str = "") -> None:
    """Stand-in for ``render_pdf``: write a content-less PDF to ``output_path``.

    The written PDF's only extractable text is the ``Module 1`` marker, so the
    per-module verification passes while the body-content verification fails —
    exactly the "content dropped during rendering" condition the error path
    guards against, without needing the optional ``fpdf2`` dependency.

    Args:
        _doc: The parsed recap document (unused; signature mirrors render_pdf).
        output_path: Temp file path main() asked render_pdf to write.
        body_text: Raw recap Markdown (unused).
    """
    Path(output_path).write_bytes(_STANDIN_PDF_BYTES)


class TestRecapRenderFailure:
    """Unrenderable content leaves no PDF, exits non-zero, names the offender.

    Validates Requirements 4.2 (Paired_Schema) and 5.2 (Split_List_Schema).
    """

    def test_paired_pair_unrenderable_writes_no_pdf_and_reports(
        self, tmp_path, capsys, monkeypatch
    ) -> None:
        """Validates: Requirements 4.2.

        When a Paired_Schema QR_Pair cannot be rendered, ``main`` returns 1,
        writes no output PDF, leaves no ``*.tmp`` files, and prints a
        ``PDF verification failed`` error to stderr that identifies the
        offending QR_Pair.
        """
        input_md = tmp_path / "recap.md"
        input_md.write_text(_PAIRED_RECAP, encoding="utf-8")
        out_pdf = tmp_path / "recap.pdf"

        monkeypatch.setattr(generate_recap_pdf, "render_pdf", _write_standin_pdf)

        exit_code = generate_recap_pdf.main(
            ["--input", str(input_md), "--output", str(out_pdf)]
        )

        assert exit_code == 1
        # No recap PDF written.
        assert not out_pdf.exists()
        # No leftover temp files beside the output.
        assert list(tmp_path.glob("*.tmp")) == []
        assert list(tmp_path.glob("recap.pdf.*")) == []

        err = capsys.readouterr().err
        assert "PDF verification failed" in err
        # The offending QR_Pair content is identified.
        assert "Offending content" in err
        assert "QR_Pair" in err

    def test_split_item_unrenderable_writes_no_pdf_and_reports(
        self, tmp_path, capsys, monkeypatch
    ) -> None:
        """Validates: Requirements 5.2.

        When a Split_List_Schema numbered item cannot be rendered, ``main``
        returns 1, writes no output PDF, and prints a ``PDF verification
        failed`` error to stderr that identifies the omitted content.
        """
        input_md = tmp_path / "recap.md"
        input_md.write_text(_SPLIT_RECAP, encoding="utf-8")
        out_pdf = tmp_path / "recap.pdf"

        monkeypatch.setattr(generate_recap_pdf, "render_pdf", _write_standin_pdf)

        exit_code = generate_recap_pdf.main(
            ["--input", str(input_md), "--output", str(out_pdf)]
        )

        assert exit_code == 1
        assert not out_pdf.exists()
        assert list(tmp_path.glob("*.tmp")) == []

        err = capsys.readouterr().err
        assert "PDF verification failed" in err
        # The offending numbered question/answer is identified.
        assert "Offending content" in err

    def test_failed_run_leaves_existing_pdf_unchanged(
        self, tmp_path, monkeypatch
    ) -> None:
        """Validates: Requirements 4.2, 5.2.

        A pre-existing output PDF is left byte-for-byte unchanged when a render
        fails verification (nothing is written or overwritten).
        """
        input_md = tmp_path / "recap.md"
        input_md.write_text(_PAIRED_RECAP, encoding="utf-8")
        out_pdf = tmp_path / "recap.pdf"
        sentinel = b"%PDF-1.4 pre-existing recap, must not be overwritten\n"
        out_pdf.write_bytes(sentinel)

        monkeypatch.setattr(generate_recap_pdf, "render_pdf", _write_standin_pdf)

        exit_code = generate_recap_pdf.main(
            ["--input", str(input_md), "--output", str(out_pdf)]
        )

        assert exit_code == 1
        assert out_pdf.read_bytes() == sentinel
        assert list(tmp_path.glob("*.tmp")) == []
