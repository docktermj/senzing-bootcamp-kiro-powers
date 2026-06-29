"""Structural / smoke tests for the Shared_Renderer_Module.

Feature: shared-markdown-renderer-refactor

These are smoke/structural tests (NOT property-based) that lock in the
dependency boundaries of ``recap_pdf_render.py`` (the Shared_Renderer_Module):

- It imports ONLY Python standard-library modules at module top level and never
  imports ``fpdf`` there (the ``fpdf`` import is lazy, inside a function body).
  Verified both by parsing the source with the ``ast`` module and by importing
  the module cleanly with ``sys.modules["fpdf"] = None`` (Req 1.2, 6.1, 8.5).
- It does NOT import the Structured_Module (``generate_recap_pdf`` /
  ``generate_recap_pdf``'s parser-model), and is importable even when
  ``generate_recap_pdf`` is forced unimportable (Req 3.3, 7.2).

The reload-based tests mutate ``sys.modules`` and restore it afterward so they
do not pollute other tests.
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import sys
from pathlib import Path

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_MODULE_NAME = "recap_pdf_render"
_MODULE_PATH = Path(_SCRIPTS_DIR) / "recap_pdf_render.py"


def _read_source() -> str:
    """Return the source text of the Shared_Renderer_Module."""
    return _MODULE_PATH.read_text(encoding="utf-8")


def _top_level_import_modules() -> list[str]:
    """Return top-level module names imported by the Shared_Renderer_Module.

    Only module-level ``import`` / ``from ... import`` statements are inspected;
    imports nested inside function bodies (e.g. the lazy ``import fpdf``) are
    intentionally excluded.
    """
    tree = ast.parse(_read_source(), filename=str(_MODULE_PATH))
    modules: list[str] = []
    for node in tree.body:  # tree.body == module top level only
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # Ignore relative imports (node.level > 0); record absolute module.
            if node.module and node.level == 0:
                modules.append(node.module)
    return modules


@contextlib.contextmanager
def _patched_sys_modules(**overrides: object):
    """Temporarily set ``sys.modules`` entries, restoring originals on exit.

    Also drops any cached copy of the Shared_Renderer_Module so a subsequent
    fresh import is forced. Restores every touched key (including the module
    under test) afterward to avoid polluting other tests.
    """
    touched = set(overrides) | {_MODULE_NAME}
    sentinel = object()
    saved = {key: sys.modules.get(key, sentinel) for key in touched}
    try:
        # Force a fresh import of the module under test.
        sys.modules.pop(_MODULE_NAME, None)
        for key, value in overrides.items():
            sys.modules[key] = value  # type: ignore[assignment]
        yield
    finally:
        for key, value in saved.items():
            if value is sentinel:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value  # type: ignore[assignment]


def _import_fresh() -> object:
    """Import a fresh copy of the Shared_Renderer_Module from its source file."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class TestSharedRendererStructure:
    """Validates Requirements 1.2, 3.3, 6.1, 7.2, 8.5.

    Structural/dependency-boundary smoke tests for the Shared_Renderer_Module
    (``recap_pdf_render.py``): stdlib-only top-level imports, lazy ``fpdf``
    import, and independence from the Structured_Module.
    """

    def test_module_source_file_exists(self) -> None:
        """The Shared_Renderer_Module source file is present and parseable."""
        assert _MODULE_PATH.is_file(), f"missing module: {_MODULE_PATH}"
        # Parsing must not raise.
        ast.parse(_read_source(), filename=str(_MODULE_PATH))

    def test_top_level_imports_are_stdlib_only(self) -> None:
        """Top-level imports are exclusively Python standard library (Req 1.2)."""
        top_modules = _top_level_import_modules()
        # The module is expected to import only stdlib (and __future__).
        non_stdlib = [
            name
            for name in top_modules
            if name.split(".")[0] not in sys.stdlib_module_names
        ]
        assert non_stdlib == [], f"non-stdlib top-level imports found: {non_stdlib}"

    def test_no_top_level_fpdf_import_in_source(self) -> None:
        """No ``import fpdf`` / ``from fpdf import ...`` at module top level.

        Validates the Lazy_Import boundary (Req 6.1, 8.5): the only ``fpdf``
        import must live inside a function body, never at module level.
        """
        top_modules = _top_level_import_modules()
        fpdf_top_level = [
            name for name in top_modules if name.split(".")[0] == "fpdf"
        ]
        assert fpdf_top_level == [], (
            f"fpdf imported at module top level: {fpdf_top_level}"
        )

    def test_fpdf_is_imported_lazily_somewhere(self) -> None:
        """``fpdf`` is imported lazily inside a function body (Req 6.1).

        Confirms the lazy import exists nested in the AST (not at top level),
        so the no-top-level assertion above reflects a real lazy boundary
        rather than the module simply never using fpdf.
        """
        tree = ast.parse(_read_source(), filename=str(_MODULE_PATH))
        top_level_nodes = set(tree.body)
        nested_fpdf_import = False
        for node in ast.walk(tree):
            if node in top_level_nodes:
                continue
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "fpdf":
                nested_fpdf_import = True
            elif isinstance(node, ast.Import):
                if any(alias.name.split(".")[0] == "fpdf" for alias in node.names):
                    nested_fpdf_import = True
        assert nested_fpdf_import, "expected a lazy (nested) fpdf import"

    def test_imports_cleanly_with_fpdf_unimportable(self) -> None:
        """Module imports cleanly with ``sys.modules['fpdf'] = None``.

        Setting ``sys.modules['fpdf'] = None`` makes ``import fpdf`` raise
        ``ImportError``. Because the Shared_Renderer_Module never imports fpdf
        at top level, a fresh import must still succeed (Req 1.2, 6.1, 8.5).
        """
        with _patched_sys_modules(fpdf=None):
            module = _import_fresh()
            # Sanity: the public rendering API is present.
            assert callable(getattr(module, "render_markdown_body", None))
            assert callable(getattr(module, "render_markdown_pdf", None))
            assert callable(getattr(module, "safe_text", None))
            assert callable(getattr(module, "split_blocks", None))

    def test_does_not_import_structured_module_at_top_level(self) -> None:
        """No top-level import of the Structured_Module (Req 3.3, 7.2).

        The shared module must not import ``generate_recap_pdf`` (its parser /
        model) at module level, keeping it independent of the Bundled_Generator.
        """
        top_modules = _top_level_import_modules()
        structured = [
            name
            for name in top_modules
            if name.split(".")[0] in {"generate_recap_pdf"}
        ]
        assert structured == [], (
            f"Shared_Renderer_Module imports Structured_Module: {structured}"
        )

    def test_importable_with_structured_module_unimportable(self) -> None:
        """Module imports cleanly with ``generate_recap_pdf`` forced unimportable.

        Forcing ``sys.modules['generate_recap_pdf'] = None`` makes any
        ``import generate_recap_pdf`` raise ``ImportError``. A fresh import of
        the Shared_Renderer_Module must still succeed, proving independence from
        the Structured_Module (Req 3.3, 7.2).
        """
        with _patched_sys_modules(generate_recap_pdf=None):
            module = _import_fresh()
            assert callable(getattr(module, "render_markdown_body", None))
            assert callable(getattr(module, "render_markdown_pdf", None))

    def test_importable_with_both_dependencies_unimportable(self) -> None:
        """Imports cleanly with both ``fpdf`` and the Structured_Module blocked.

        Combines the two independence guarantees (Req 1.2, 3.3, 6.1, 7.2, 8.5):
        the module loads with neither the optional ``fpdf2`` dependency nor the
        Structured_Module available.
        """
        with _patched_sys_modules(fpdf=None, generate_recap_pdf=None):
            module = _import_fresh()
            assert callable(getattr(module, "render_markdown_body", None))
            assert callable(getattr(module, "render_markdown_pdf", None))
