"""Tests for the stdlib-only HTML fallback recap renderer.

Feature: guaranteed-graduation-artifacts

Covers the ``recap_html_render`` renderer (the HTML analogue of
``recap_pdf_render``). It exercises the behaviours the design requires of the
HTML Rendered_Recap:

- The rendered document is non-empty (Requirement 4.3).
- Every ``## Module N`` section present in the source recap is reflected in the
  output (Requirement 4.6).
- HTML-significant characters in source content are escaped, so no source text
  is interpreted as raw markup (Requirement 4.3).
- The output is self-contained: it embeds an inline ``<style>`` and references
  no external URLs (Requirement 4.6).
- The module imports cleanly even when ``fpdf`` is unimportable, and never
  imports ``fpdf`` at module top level (Requirements 4.5, 6.1).

Both example-based unit tests and Hypothesis property tests are included.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_html_render import markdown_to_html_body, render_markdown_html

_MODULE_NAME = "recap_html_render"
_MODULE_PATH = Path(_SCRIPTS_DIR) / "recap_html_render.py"

# Matches an ``http://`` or ``https://`` external URL anywhere in the document.
_EXTERNAL_URL_RE = re.compile(r"https?://", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Safe characters for a module name: letters, digits, and spaces. Deliberately
# excludes HTML-significant characters and Markdown emphasis markers so the
# rendered ``<h2>Module N:`` prefix stays byte-for-byte predictable.
_MODULE_NAME_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
)


@st.composite
def st_module_name(draw: st.DrawFn) -> str:
    """Draw a simple, HTML-safe module name (trimmed, non-empty).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A module name containing only letters, digits, and single spaces.
    """
    raw = draw(st.text(alphabet=_MODULE_NAME_ALPHABET, min_size=1, max_size=24))
    name = " ".join(raw.split())
    # Collapsing runs of spaces can empty the string; fall back to a literal.
    return name or "Module"


@st.composite
def st_recap_markdown(draw: st.DrawFn) -> tuple[str, list[int]]:
    """Draw recap Markdown with one canonical ``## Module N`` section per module.

    Each module section uses the canonical heading form
    ``## Module N: [Name] — [timestamp]`` followed by the three labeled
    subsections the recap format requires, so the generated document mirrors a
    real recap. Module numbers are unique and returned alongside the body so a
    test can assert every section survives rendering.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(body_text, module_numbers)`` tuple: the recap Markdown and the
        ascending list of module numbers embedded in it.
    """
    numbers = draw(
        st.lists(st.integers(min_value=1, max_value=11), min_size=1, max_size=6, unique=True)
    )
    numbers.sort()

    blocks: list[str] = ["# Bootcamp Recap"]
    for number in numbers:
        name = draw(st_module_name())
        blocks.append(f"## Module {number}: {name} — 2026-01-0{number % 9 + 1}T00:00:00Z")
        blocks.append("### Information Shared")
        blocks.append(f"- Shared detail for module {number}")
        blocks.append("### Questions & Responses")
        blocks.append(f"- **Q:** What did module {number} cover?\n  - **R:** Entity resolution.")
        blocks.append("### Actions Taken")
        blocks.append(f"- Ran the module {number} exercise")

    return "\n\n".join(blocks), numbers


# ---------------------------------------------------------------------------
# Structural helpers (top-level import inspection)
# ---------------------------------------------------------------------------


def _top_level_import_modules() -> list[str]:
    """Return module names imported at ``recap_html_render`` top level.

    Only module-level ``import`` / ``from ... import`` statements are inspected;
    imports nested inside function bodies are intentionally excluded.

    Returns:
        The list of top-level imported module names.
    """
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"), filename=str(_MODULE_PATH))
    modules: list[str] = []
    for node in tree.body:  # tree.body == module top level only
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.append(node.module)
    return modules


def _import_fresh_with_fpdf_blocked() -> object:
    """Import a fresh ``recap_html_render`` with ``fpdf`` made unimportable.

    Sets ``sys.modules['fpdf'] = None`` (so any ``import fpdf`` raises
    ``ImportError``) and loads a brand-new copy of the module from its source
    file. Restores the touched ``sys.modules`` entries afterward so other tests
    are unaffected.

    Returns:
        The freshly imported module object.
    """
    sentinel = object()
    touched = {"fpdf", _MODULE_NAME}
    saved = {key: sys.modules.get(key, sentinel) for key in touched}
    try:
        sys.modules["fpdf"] = None  # type: ignore[assignment]
        sys.modules.pop(_MODULE_NAME, None)
        spec = importlib.util.spec_from_file_location(_MODULE_NAME, _MODULE_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[_MODULE_NAME] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in saved.items():
            if value is sentinel:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Example-based unit tests
# ---------------------------------------------------------------------------


class TestRecapHtmlRenderUnit:
    """Example-based coverage of the HTML recap renderer.

    Validates: Requirements 4.3, 4.5, 4.6
    """

    def test_output_is_non_empty(self) -> None:
        """A non-empty recap renders a non-empty HTML document (Req 4.3)."""
        html = markdown_to_html_body("## Module 1: Intro — ts\n\nHello world")
        assert html.strip(), "renderer produced empty HTML for non-empty input"

    def test_contains_every_module_section(self) -> None:
        """Every ``## Module N`` heading is reflected as an ``<h2>`` (Req 4.6)."""
        body = (
            "# Bootcamp Recap\n\n"
            "## Module 1: Intro — ts\n\n"
            "prose one\n\n"
            "## Module 3: Loading — ts\n\n"
            "prose three\n\n"
            "## Module 11: Deploy — ts\n\n"
            "prose eleven"
        )
        html = markdown_to_html_body(body)
        for number in (1, 3, 11):
            assert f"<h2>Module {number}:" in html, f"missing Module {number} section"

    def test_escapes_html_special_characters(self) -> None:
        """Source HTML markup is escaped, not passed through raw (Req 4.3)."""
        html = markdown_to_html_body("## Module 1: X — ts\n\nDanger <script>alert(1)</script> & co")
        assert "<script>" not in html, "raw <script> tag leaked into output"
        assert "&lt;script&gt;" in html, "angle brackets were not escaped"
        assert "&amp;" in html, "ampersand was not escaped"

    def test_full_document_is_self_contained(self, tmp_path: Path) -> None:
        """The written document embeds inline CSS and no external URLs (Req 4.6)."""
        out = tmp_path / "recap.html"
        render_markdown_html("## Module 1: Intro — ts\n\nBody text", str(out))
        document = out.read_text(encoding="utf-8")
        assert document.strip(), "written HTML document is empty"
        assert document.lstrip().startswith("<!DOCTYPE html>")
        assert "<style>" in document, "no inline stylesheet embedded"
        assert not _EXTERNAL_URL_RE.search(document), "document references an external URL"

    def test_no_top_level_fpdf_import(self) -> None:
        """``recap_html_render`` never imports ``fpdf`` at module top level (Req 4.5)."""
        top_modules = _top_level_import_modules()
        fpdf_top_level = [name for name in top_modules if name.split(".")[0] == "fpdf"]
        assert fpdf_top_level == [], f"fpdf imported at top level: {fpdf_top_level}"

    def test_imports_cleanly_without_fpdf(self) -> None:
        """The module imports with ``fpdf`` unimportable (Req 4.5, 6.1)."""
        module = _import_fresh_with_fpdf_blocked()
        assert callable(getattr(module, "markdown_to_html_body", None))
        assert callable(getattr(module, "render_markdown_html", None))
        assert "fpdf" not in _top_level_import_modules()


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestRecapHtmlRenderProperties:
    """Property coverage of the HTML recap renderer.

    Validates: Requirements 4.3, 4.6
    """

    @given(data=st_recap_markdown())
    def test_output_non_empty_and_all_module_sections_present(
        self, data: tuple[str, list[int]]
    ) -> None:
        """For any recap, output is non-empty and every module section survives.

        Validates: Requirements 4.3, 4.6
        """
        body, numbers = data
        html = markdown_to_html_body(body)
        assert html.strip(), "renderer produced empty HTML for non-empty recap"
        for number in numbers:
            assert f"<h2>Module {number}:" in html, f"Module {number} section dropped"

    @given(payload=st.text(min_size=1, max_size=40))
    def test_special_characters_are_escaped(self, payload: str) -> None:
        """No source ``<``/``>`` survives unescaped into the output.

        The injected payload is embedded in prose; regardless of its content any
        angle bracket the source contributes must be escaped rather than passed
        through as raw markup.

        Validates: Requirements 4.3
        """
        body = f"## Module 1: Intro — ts\n\nprefix {payload} suffix"
        html = markdown_to_html_body(body)
        if "<" in payload:
            assert "&lt;" in html, "a source '<' was not escaped"
        if ">" in payload:
            assert "&gt;" in html, "a source '>' was not escaped"

    @given(data=st_recap_markdown())
    def test_rendered_document_has_no_external_urls(
        self, data: tuple[str, list[int]]
    ) -> None:
        """A URL-free recap renders a document referencing no external URLs.

        Validates: Requirements 4.6
        """
        body, _ = data
        # The generated recap contains no URLs, so any http(s):// in the output
        # would have to come from the renderer's own chrome — which must be none.
        out = markdown_to_html_body(body)
        assert not _EXTERNAL_URL_RE.search(out), "rendered body introduced an external URL"
