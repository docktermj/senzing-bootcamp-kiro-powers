"""Property-based and unit tests for fpdf2_preflight.py using Hypothesis.

Feature: fpdf2-preflight-note

Verifies the tiny stdlib-only preflight helper that surfaces a single,
non-blocking informational note at Track_Completion when the optional
``fpdf2`` dependency is absent. Availability is controlled without installing
or uninstalling ``fpdf2`` by monkeypatching the ``import fpdf`` outcome via
``sys.modules`` (a stub module = available; ``None`` = absent), the same
technique the existing recap-PDF degradation tests use.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import io
import sys
import types
from collections.abc import Iterator
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from fpdf2_preflight import PREFLIGHT_NOTE, fpdf2_available, main, preflight_note

# ---------------------------------------------------------------------------
# Availability control helpers
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _fpdf_available() -> Iterator[None]:
    """Make ``import fpdf`` succeed by inserting a stub module.

    Inserts a bare stub ``fpdf`` module into ``sys.modules`` so the guarded
    ``import fpdf`` inside ``fpdf2_available`` succeeds regardless of whether
    ``fpdf2`` is actually installed. Restores the original state on exit.

    Yields:
        None. Within the context, ``import fpdf`` succeeds.
    """
    sentinel = object()
    original = sys.modules.get("fpdf", sentinel)
    sys.modules["fpdf"] = types.ModuleType("fpdf")
    try:
        yield
    finally:
        if original is sentinel:
            sys.modules.pop("fpdf", None)
        else:
            sys.modules["fpdf"] = original  # type: ignore[assignment]


@contextlib.contextmanager
def _fpdf_absent() -> Iterator[None]:
    """Force ``import fpdf`` to raise ImportError.

    Inserts ``None`` for the ``fpdf`` entry in ``sys.modules`` so the guarded
    ``import fpdf`` raises ImportError regardless of whether ``fpdf2`` is
    actually installed — mirroring the existing recap-PDF degradation tests.
    Restores the original state on exit.

    Yields:
        None. Within the context, ``import fpdf`` raises ImportError.
    """
    sentinel = object()
    original = sys.modules.get("fpdf", sentinel)
    sys.modules["fpdf"] = None  # type: ignore[assignment]
    try:
        yield
    finally:
        if original is sentinel:
            sys.modules.pop("fpdf", None)
        else:
            sys.modules["fpdf"] = original  # type: ignore[assignment]


@contextlib.contextmanager
def _fpdf_env(available: bool) -> Iterator[None]:
    """Control the ``import fpdf`` outcome from a boolean availability flag.

    Args:
        available: When True, ``import fpdf`` succeeds; when False, it raises
            ImportError.

    Yields:
        None. Within the context, the ``import fpdf`` outcome matches
        ``available``.
    """
    manager = _fpdf_available() if available else _fpdf_absent()
    with manager:
        yield


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_availability() -> st.SearchStrategy[bool]:
    """Generate an fpdf2 availability state (import outcome).

    Returns:
        A strategy yielding ``True`` (``import fpdf`` should succeed) or
        ``False`` (``import fpdf`` should raise ImportError).
    """
    return st.booleans()


# ---------------------------------------------------------------------------
# Property 3: Availability detection agrees with the real import outcome
# ---------------------------------------------------------------------------


class TestAvailabilityDetection:
    """`fpdf2_available()` agrees with the real ``import fpdf`` outcome.

    **Validates: Requirements 3.2**

    For any monkeypatched ``import fpdf`` outcome, ``fpdf2_available()`` returns
    ``True`` when ``import fpdf`` would succeed and ``False`` when it raises
    ImportError — matching the detection used by the PDF scripts so the note
    can never contradict the actual render outcome.
    """

    # Feature: fpdf2-preflight-note, Property 3: Availability detection agrees
    # with the real import outcome — for any monkeypatched `import fpdf`
    # outcome, `fpdf2_available()` returns True when `import fpdf` would succeed
    # and False when it raises ImportError.
    @given(available=st_availability())
    def test_availability_matches_import_outcome(self, available: bool) -> None:
        """`fpdf2_available()` returns exactly the monkeypatched import outcome.

        **Validates: Requirements 3.2**
        """
        with _fpdf_env(available):
            assert fpdf2_available() is available, (
                f"fpdf2_available() should return {available} when "
                f"import fpdf {'succeeds' if available else 'raises ImportError'}"
            )


# ---------------------------------------------------------------------------
# Property 1: A note is produced exactly when fpdf2 is unavailable
# ---------------------------------------------------------------------------


class TestGatingDecision:
    """`preflight_note()` produces a note iff ``fpdf2`` is unavailable.

    **Validates: Requirements 1.1, 1.3**

    For any availability state, ``preflight_note()`` returns ``None`` when
    ``fpdf2`` is importable and a single non-empty line (no embedded newline)
    when it is not — i.e. a note is present if and only if ``fpdf2`` is
    unavailable — and ``main`` prints the note in the unavailable case and
    prints nothing in the available case.
    """

    # Feature: fpdf2-preflight-note, Property 1: A note is produced exactly when
    # fpdf2 is unavailable — for any availability state, `preflight_note()`
    # returns None when `fpdf2` is importable and a single non-empty line when it
    # is not (note present iff `fpdf2` unavailable).
    @given(available=st_availability())
    def test_note_present_iff_fpdf2_unavailable(self, available: bool) -> None:
        """`preflight_note()` is None iff available, else a single non-empty line.

        **Validates: Requirements 1.1, 1.3**
        """
        with _fpdf_env(available):
            note = preflight_note()
            if available:
                assert note is None, (
                    "preflight_note() should return None when fpdf2 is available"
                )
            else:
                assert note is not None, (
                    "preflight_note() should return a note when fpdf2 is absent"
                )
                assert isinstance(note, str)
                assert note != "", "the absent-branch note must be non-empty"
                assert "\n" not in note, "the note must be a single line"

    # Feature: fpdf2-preflight-note, Property 1: A note is produced exactly when
    # fpdf2 is unavailable — main prints the note in the unavailable case and
    # prints nothing in the available case.
    @given(available=st_availability())
    def test_main_prints_note_iff_fpdf2_unavailable(self, available: bool) -> None:
        """`main` stdout is empty iff available, else exactly the one-line note.

        **Validates: Requirements 1.1, 1.3**
        """
        buffer = io.StringIO()
        with _fpdf_env(available), contextlib.redirect_stdout(buffer):
            exit_code = main([])
        printed = buffer.getvalue()

        assert exit_code == 0
        if available:
            assert printed == "", (
                "main should print nothing when fpdf2 is available"
            )
        else:
            assert printed.strip() != "", (
                "main should print the note when fpdf2 is absent"
            )
            # Exactly one printed line (print adds a single trailing newline).
            assert printed.count("\n") == 1, "main should print exactly one line"


# ---------------------------------------------------------------------------
# Property 2: The absent-branch note states both facts and the exact install
# command
# ---------------------------------------------------------------------------


class TestAbsentBranchNoteContent:
    """The absent-branch note states both facts and the exact install command.

    **Validates: Requirements 1.1, 1.2**

    For any environment in which ``fpdf2`` is unavailable, the string returned
    by ``preflight_note()`` is a single line (contains no newline) that
    communicates that installing ``fpdf2`` enables the PDF, that the Markdown
    output is produced regardless, and contains the exact substring
    ``pip install fpdf2``.
    """

    # Feature: fpdf2-preflight-note, Property 2: The absent-branch note states
    # both facts and the exact install command — for any environment where
    # fpdf2 is unavailable, preflight_note() returns a single line (contains no
    # newline) communicating that installing fpdf2 enables the PDF, that the
    # Markdown output is produced regardless, and containing the exact substring
    # `pip install fpdf2`.
    @given(available=st_availability())
    def test_absent_branch_note_states_facts_and_command(
        self, available: bool
    ) -> None:
        """Over the absent branch, the note is a single line with both facts.

        The availability flag is generated to exercise the full input space,
        but only the absent branch carries the note contract; the available
        branch (``preflight_note()`` is ``None``) is verified by Property 1.

        **Validates: Requirements 1.1, 1.2**
        """
        with _fpdf_env(available):
            note = preflight_note()

        if available:
            # Content contract only applies to the absent branch; Property 1
            # covers the None-when-available gating.
            assert note is None
            return

        assert note is not None, (
            "preflight_note() must return a note when fpdf2 is absent"
        )
        # Single source of truth: the note is exactly the module constant.
        assert note == PREFLIGHT_NOTE

        # Single line — contains no embedded newline (Requirement 1.1).
        assert "\n" not in note, "the note must be a single line (no newline)"

        # Exact install command substring (Requirement 1.2).
        assert "pip install fpdf2" in note, (
            "the note must contain the exact command 'pip install fpdf2'"
        )

        lowered = note.lower()
        # Fact 1: installing fpdf2 enables the PDF (Requirement 1.1).
        assert "fpdf2" in lowered and "pdf" in lowered, (
            "the note must communicate that installing fpdf2 enables the PDF"
        )
        # Fact 2: the Markdown output is produced regardless (Requirement 1.1).
        assert "markdown" in lowered and "regardless" in lowered, (
            "the note must communicate that the Markdown output is produced "
            "regardless"
        )


# ---------------------------------------------------------------------------
# Additional availability control: forced unexpected (non-ImportError) error
# ---------------------------------------------------------------------------


class _RejectingFpdfFinder:
    """A ``sys.meta_path`` finder that raises a non-ImportError for ``fpdf``.

    Used to exercise the "unexpected error while probing the import" row of the
    design's Error Handling table: a guarded ``import fpdf`` should normally
    only see ``ImportError``, but the helper must remain non-blocking even if
    some other exception escapes the import machinery.
    """

    def find_spec(self, fullname: str, path: object = None, target: object = None):
        """Raise ``RuntimeError`` when ``fpdf`` is looked up; defer otherwise.

        Args:
            fullname: The fully-qualified module name being imported.
            path: The parent package ``__path__`` (unused).
            target: The module to reuse for reload (unused).

        Returns:
            ``None`` for every module other than ``fpdf`` so normal imports are
            unaffected.

        Raises:
            RuntimeError: When ``fullname`` is ``"fpdf"`` — a forced, unexpected
                (non-``ImportError``) failure during ``import fpdf``.
        """
        if fullname == "fpdf":
            raise RuntimeError("forced unexpected error while importing fpdf")
        return None


@contextlib.contextmanager
def _fpdf_unexpected_error() -> Iterator[None]:
    """Force ``import fpdf`` to raise a non-ImportError (``RuntimeError``).

    Removes any cached ``fpdf`` entry from ``sys.modules`` and installs a
    front-of-line ``sys.meta_path`` finder that raises ``RuntimeError`` when
    ``fpdf`` is imported. Restores both ``sys.meta_path`` and ``sys.modules`` on
    exit so no other test is affected.

    Yields:
        None. Within the context, ``import fpdf`` raises ``RuntimeError``.
    """
    sentinel = object()
    original_module = sys.modules.get("fpdf", sentinel)
    sys.modules.pop("fpdf", None)
    finder = _RejectingFpdfFinder()
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.meta_path.remove(finder)
        if original_module is sentinel:
            sys.modules.pop("fpdf", None)
        else:
            sys.modules["fpdf"] = original_module  # type: ignore[assignment]


@contextlib.contextmanager
def _fpdf_outcome_env(outcome: str) -> Iterator[None]:
    """Control the ``import fpdf`` outcome from a named outcome.

    Args:
        outcome: One of ``"available"`` (``import fpdf`` succeeds), ``"absent"``
            (raises ``ImportError``), or ``"error"`` (raises a non-``ImportError``
            ``RuntimeError`` — a forced unexpected error).

    Yields:
        None. Within the context, the ``import fpdf`` outcome matches ``outcome``.
    """
    if outcome == "available":
        manager: contextlib.AbstractContextManager[None] = _fpdf_available()
    elif outcome == "absent":
        manager = _fpdf_absent()
    elif outcome == "error":
        manager = _fpdf_unexpected_error()
    else:  # pragma: no cover - guards against strategy drift
        raise ValueError(f"unknown import outcome: {outcome!r}")
    with manager:
        yield


class _ForbiddenStdin:
    """A stand-in for ``sys.stdin`` that fails loudly if anything reads it.

    Any attempt to read, iterate, or otherwise consume stdin raises
    ``AssertionError``, so a test can prove ``main`` never prompts or pauses on
    input (Requirement 2.1 — non-blocking).
    """

    def _forbidden(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("main must not read stdin (it must be non-blocking)")

    read = _forbidden
    readline = _forbidden
    readlines = _forbidden

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("main must not read stdin (it must be non-blocking)")


@contextlib.contextmanager
def _stdin_forbidden() -> Iterator[None]:
    """Replace ``sys.stdin`` with a reader that raises if consumed.

    Yields:
        None. Within the context, reading ``sys.stdin`` raises ``AssertionError``.
    """
    original = sys.stdin
    sys.stdin = _ForbiddenStdin()  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.stdin = original


def st_import_outcome() -> st.SearchStrategy[str]:
    """Generate an ``import fpdf`` outcome, including a forced unexpected error.

    Extends :func:`st_availability` beyond the two expected outcomes with a
    third, ``"error"``, outcome that forces a non-``ImportError`` during
    ``import fpdf`` — the "unexpected error while probing the import" case from
    the design's Error Handling table.

    Returns:
        A strategy yielding ``"available"``, ``"absent"``, or ``"error"``.
    """
    return st.sampled_from(["available", "absent", "error"])


# ---------------------------------------------------------------------------
# Property 4: The helper is total and non-blocking across all import outcomes
# ---------------------------------------------------------------------------


class TestTotalityNonBlocking:
    """The helper is total and non-blocking across all ``import fpdf`` outcomes.

    **Validates: Requirements 2.1**

    For any ``import fpdf`` outcome — success, ``ImportError``, or a forced
    unexpected (non-``ImportError``) error — ``main()`` returns ``0`` without
    prompting, pausing, or raising, so the note is strictly informational and
    never blocks the track-completion flow. For the expected outcomes
    (success / ``ImportError``) the pure helpers are likewise total:
    ``fpdf2_available()`` returns a ``bool`` and ``preflight_note()`` returns
    ``str | None``. Per the design's Error Handling table, the totality
    guarantee for the unexpected-error path is at the ``main`` boundary — the
    flow is never blocked.
    """

    # Feature: fpdf2-preflight-note, Property 4: The helper is total and
    # non-blocking across all import outcomes — for any `import fpdf` outcome
    # (including a forced unexpected error), `fpdf2_available()` returns a
    # `bool`, `preflight_note()` returns `str | None`, and `main()` returns `0`
    # — each without prompting, pausing, or raising.
    @given(outcome=st_import_outcome())
    def test_helper_total_and_non_blocking(self, outcome: str) -> None:
        """`main` returns 0 without raising or reading stdin, for every outcome.

        For the expected outcomes (``available`` / ``absent``) the pure helpers
        are also asserted total (``bool`` and ``str | None``). ``main`` must be
        total and non-blocking across *all* outcomes, including the forced
        unexpected error (design Error Handling table; Requirement 2.1).

        **Validates: Requirements 2.1**
        """
        with _fpdf_outcome_env(outcome):
            # For the expected import outcomes, the pure helpers are total.
            if outcome != "error":
                available = fpdf2_available()
                assert isinstance(available, bool), (
                    "fpdf2_available() must return a bool"
                )
                note = preflight_note()
                assert note is None or isinstance(note, str), (
                    "preflight_note() must return str | None"
                )

            # main must be total and non-blocking for EVERY outcome: it returns
            # 0 without prompting/pausing (never reads stdin) and without raising.
            buffer = io.StringIO()
            with _stdin_forbidden(), contextlib.redirect_stdout(buffer):
                exit_code = main([])

            assert isinstance(exit_code, int)
            assert exit_code == 0, "main() must always return 0 (non-blocking)"
            # main prints at most one line, never more (informational only).
            assert buffer.getvalue().count("\n") <= 1, (
                "main() must print at most one line"
            )


# ---------------------------------------------------------------------------
# Concrete (non-Hypothesis) unit tests for the absent and present branches
# ---------------------------------------------------------------------------


class TestConcreteBranches:
    """Concrete example tests for the absent and present branches.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1**

    Complements the property tests with focused, example-based guardrails:
    with ``fpdf`` forced unimportable the note equals the module constant,
    contains ``pip install fpdf2``, and ``main`` prints exactly that one line
    (exit 0); with a stub ``fpdf`` present the note is ``None`` and ``main``
    prints nothing (exit 0). Availability is controlled with the existing
    ``_fpdf_absent`` / ``_fpdf_available`` helpers and stdout is captured with
    the existing ``redirect_stdout`` pattern.
    """

    def test_absent_branch_note_equals_constant_with_install_command(self) -> None:
        """Absent: `preflight_note()` equals the constant and has the command.

        **Validates: Requirements 1.1, 1.2**
        """
        with _fpdf_absent():
            note = preflight_note()

        assert note == PREFLIGHT_NOTE, (
            "absent-branch note must equal the module PREFLIGHT_NOTE constant"
        )
        assert "pip install fpdf2" in note, (
            "the note must contain the exact command 'pip install fpdf2'"
        )
        assert "\n" not in note, "the note must be a single line (no newline)"

    def test_absent_branch_main_prints_one_line_and_returns_zero(self) -> None:
        """Absent: `main` prints exactly the one-line note and returns 0.

        **Validates: Requirements 1.1, 1.2, 2.1**
        """
        buffer = io.StringIO()
        with _fpdf_absent(), contextlib.redirect_stdout(buffer):
            exit_code = main([])
        printed = buffer.getvalue()

        assert exit_code == 0, "main must return 0 (non-blocking)"
        # print() adds exactly one trailing newline to the single-line note.
        assert printed == PREFLIGHT_NOTE + "\n", (
            "main must print exactly the one-line Preflight_Note"
        )
        assert printed.count("\n") == 1, "main must print exactly one line"

    def test_present_branch_note_is_none(self) -> None:
        """Present: `preflight_note()` is None (no noise when PDF will succeed).

        **Validates: Requirements 1.3**
        """
        with _fpdf_available():
            note = preflight_note()

        assert note is None, (
            "preflight_note() must return None when fpdf2 is available"
        )

    def test_present_branch_main_prints_nothing_and_returns_zero(self) -> None:
        """Present: `main` prints nothing and returns 0.

        **Validates: Requirements 1.3, 2.1**
        """
        buffer = io.StringIO()
        with _fpdf_available(), contextlib.redirect_stdout(buffer):
            exit_code = main([])
        printed = buffer.getvalue()

        assert exit_code == 0, "main must return 0 (non-blocking)"
        assert printed == "", "main must print nothing when fpdf2 is available"


# ---------------------------------------------------------------------------
# Structural / source-analysis helpers
# ---------------------------------------------------------------------------

_SCRIPTS_PATH = Path(__file__).resolve().parent.parent / "scripts"
_PREFLIGHT_SOURCE_PATH = _SCRIPTS_PATH / "fpdf2_preflight.py"
_STEERING_PATH = Path(__file__).resolve().parent.parent / "steering"
_GRADUATION_PATH = _STEERING_PATH / "graduation.md"
_MODULE_COMPLETION_PATH = _STEERING_PATH / "module-completion-track.md"


def _module_ast() -> ast.Module:
    """Parse the ``fpdf2_preflight.py`` source into an AST module.

    Returns:
        The parsed :class:`ast.Module` for the preflight helper source.
    """
    return ast.parse(_PREFLIGHT_SOURCE_PATH.read_text(encoding="utf-8"))


def _top_level_import_names(tree: ast.Module) -> set[str]:
    """Collect the module names imported at the *top level* of the module.

    Only statements that are direct children of the module body are considered
    top level; imports nested inside function/class bodies (e.g. the guarded
    ``import fpdf`` inside ``fpdf2_available``) are intentionally excluded.

    Args:
        tree: The parsed module AST.

    Returns:
        The set of top-level imported/imported-from module names.
    """
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def _all_import_names(tree: ast.Module) -> set[str]:
    """Collect every imported module name anywhere in the module (any depth).

    Walks the entire AST, including imports nested inside function or class
    bodies, so a helper cannot smuggle in a dependency at any scope.

    Args:
        tree: The parsed module AST.

    Returns:
        The set of all imported/imported-from module names in the source.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


# ---------------------------------------------------------------------------
# Lazy / optional import guardrail (Requirement 2.3)
# ---------------------------------------------------------------------------


class TestLazyOptionalImport:
    """The helper never makes ``fpdf`` a top-level or hard dependency.

    **Validates: Requirements 2.3, 4.1**

    Importing ``fpdf2_preflight`` must succeed even when ``fpdf`` is
    unimportable, and a structural scan of the module source must find no
    top-level ``import fpdf`` / ``from fpdf import ...`` — the guarded import
    lives inside ``fpdf2_available``'s function body, which is fine.
    """

    def test_import_succeeds_while_fpdf_unimportable(self) -> None:
        """Reloading the module with ``fpdf`` absent still succeeds.

        Forces ``import fpdf`` to raise ImportError, then reloads
        ``fpdf2_preflight`` (re-executing its module body). Because there is no
        top-level ``import fpdf``, the reload must succeed and the reloaded
        module must expose its public API, with ``fpdf2_available()`` reporting
        the dependency as absent.

        **Validates: Requirements 2.3**
        """
        module = importlib.import_module("fpdf2_preflight")
        with _fpdf_absent():
            reloaded = importlib.reload(module)

            assert reloaded is not None
            assert hasattr(reloaded, "fpdf2_available")
            assert hasattr(reloaded, "preflight_note")
            assert hasattr(reloaded, "main")
            # With fpdf absent, detection reports it unavailable — proving the
            # module imported cleanly without a hard fpdf dependency.
            assert reloaded.fpdf2_available() is False

    def test_source_has_no_top_level_fpdf_import(self) -> None:
        """A structural AST scan finds no top-level ``import fpdf``.

        The only ``import fpdf`` allowed is the guarded one inside
        ``fpdf2_available``'s body; it must never appear as a module-top-level
        statement (Requirement 2.3).

        **Validates: Requirements 2.3**
        """
        top_level = _top_level_import_names(_module_ast())

        assert "fpdf" not in top_level, (
            "fpdf must not be imported at module top level (keep it optional "
            "and lazily imported per python-conventions.md / tech.md)"
        )
        assert not any(name.split(".")[0] == "fpdf" for name in top_level), (
            "no top-level import may reference the fpdf package"
        )

    def test_guarded_fpdf_import_lives_inside_a_function(self) -> None:
        """The single ``import fpdf`` occurs only inside a function body.

        Confirms the guarded import is present (detection mirrors the PDF
        scripts) but confined to a function scope, not module top level.

        **Validates: Requirements 2.3**
        """
        tree = _module_ast()
        function_scoped_fpdf = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Import) and any(
                        alias.name == "fpdf" for alias in inner.names
                    ):
                        function_scoped_fpdf = True
        assert function_scoped_fpdf, (
            "the guarded 'import fpdf' should live inside a function body"
        )


# ---------------------------------------------------------------------------
# No-regression of PDF degradation (Requirement 2.2)
# ---------------------------------------------------------------------------


class TestNoRegressionPdfDegradation:
    """The helper is additive and independent of the PDF scripts.

    **Validates: Requirements 2.2, 4.1**

    A structural scan of ``fpdf2_preflight.py`` imports must show it neither
    imports ``generate_recap_pdf`` nor ``generate_completion_summary``,
    confirming the helper cannot import or modify them and therefore leaves
    their existing graceful-degradation behavior untouched.
    """

    def test_does_not_import_pdf_scripts(self) -> None:
        """The source imports neither PDF-generation module (any scope).

        **Validates: Requirements 2.2**
        """
        imported = _all_import_names(_module_ast())

        assert "generate_recap_pdf" not in imported, (
            "fpdf2_preflight must not import generate_recap_pdf (stay additive "
            "and independent)"
        )
        assert "generate_completion_summary" not in imported, (
            "fpdf2_preflight must not import generate_completion_summary (stay "
            "additive and independent)"
        )

    def test_source_does_not_reference_pdf_render_functions(self) -> None:
        """No *executable* code names the PDF scripts' render/degradation helpers.

        Guards against invoking or reaching into the PDF scripts by name, so
        their degradation behavior cannot be altered by this helper. The scan
        is over AST identifier nodes (``Name`` / ``Attribute``) only, so a
        purely documentary cross-reference in a docstring or comment (e.g.
        "mirroring ``generate_completion_summary.ensure_fpdf2``") is allowed —
        it is not a call into the PDF scripts.

        **Validates: Requirements 2.2**
        """
        tree = _module_ast()
        code_identifiers: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                code_identifiers.add(node.id)
            elif isinstance(node, ast.Attribute):
                code_identifiers.add(node.attr)

        for forbidden in (
            "generate_recap_pdf",
            "generate_completion_summary",
            "generate_pdf_with_fallback",
            "render_completion_pdf",
            "render_pdf",
            "ensure_fpdf2",
        ):
            assert forbidden not in code_identifiers, (
                f"fpdf2_preflight code must not reference {forbidden!r}; the "
                "helper is strictly additive and upstream of the PDF scripts"
            )

    def test_pdf_scripts_exist_and_are_untouched_targets(self) -> None:
        """The PDF scripts exist as separate files the helper does not touch.

        Confirms the helper is a distinct file from the PDF scripts (so it can
        only be additive), rather than editing them in place.

        **Validates: Requirements 2.2**
        """
        recap = _SCRIPTS_PATH / "generate_recap_pdf.py"
        summary = _SCRIPTS_PATH / "generate_completion_summary.py"

        assert recap.exists(), "generate_recap_pdf.py should still exist"
        assert summary.exists(), (
            "generate_completion_summary.py should still exist"
        )
        assert _PREFLIGHT_SOURCE_PATH.resolve() not in {
            recap.resolve(),
            summary.resolve(),
        }, "the preflight helper must be a separate file from the PDF scripts"


# ---------------------------------------------------------------------------
# Steering placement (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestSteeringPlacement:
    """The preflight invocation precedes PDF generation in the steering.

    **Validates: Requirements 3.1, 4.1**

    In ``graduation.md`` the ``fpdf2_preflight`` invocation must appear
    immediately before Step 0b's Recap PDF Generation steps, and in
    ``module-completion-track.md`` it must appear before the completion-summary
    PDF / export offer. Placement is verified with string-index comparisons on
    the actual file contents, using anchors present in those files.
    """

    _INVOCATION = "python3 senzing-bootcamp/scripts/fpdf2_preflight.py"

    def test_graduation_invokes_preflight_before_pdf_generation(self) -> None:
        """``graduation.md`` invokes the helper before the PDF render steps.

        The invocation sits in Step 0b.0 (fpdf2 Preflight Note) and must
        precede Step 0b.1 (Recap Document Recovery) and Step 0b.3 (PDF
        Generation) where the render is attempted (Requirement 3.1).

        **Validates: Requirements 3.1**
        """
        content = _GRADUATION_PATH.read_text(encoding="utf-8")

        invocation_idx = content.find(self._INVOCATION)
        preflight_header_idx = content.find("### Step 0b.0: fpdf2 Preflight Note")
        recovery_idx = content.find("### Step 0b.1: Recap Document Recovery")
        pdf_gen_idx = content.find("### Step 0b.3: PDF Generation")

        assert invocation_idx != -1, (
            "graduation.md must invoke fpdf2_preflight.py"
        )
        assert preflight_header_idx != -1, (
            "graduation.md must have a Step 0b.0 fpdf2 Preflight Note section"
        )
        assert recovery_idx != -1, "graduation.md must have Step 0b.1"
        assert pdf_gen_idx != -1, "graduation.md must have Step 0b.3 PDF Generation"

        # The preflight note section and its invocation come before the recap
        # recovery and the actual PDF render steps.
        assert preflight_header_idx < recovery_idx < pdf_gen_idx, (
            "the Preflight Note (Step 0b.0) must precede recovery (0b.1) and "
            "PDF generation (0b.3)"
        )
        assert preflight_header_idx < invocation_idx < recovery_idx, (
            "the fpdf2_preflight invocation must sit in Step 0b.0, before the "
            "PDF render steps"
        )

    def test_module_completion_invokes_preflight_before_export_offer(self) -> None:
        """``module-completion-track.md`` invokes the helper before the offers.

        The invocation must appear before the completion-summary PDF / export
        offer at Track_Completion (Requirement 3.1).

        **Validates: Requirements 3.1**
        """
        content = _MODULE_COMPLETION_PATH.read_text(encoding="utf-8")

        preflight_header_idx = content.find(
            "### fpdf2 Preflight Note (before the completion-summary PDF / "
            "export offer)"
        )
        invocation_idx = content.find(self._INVOCATION)
        present_idx = content.find("When track is complete, present:")
        export_offer_idx = content.find(
            'Export option: "Would you like to export a shareable report'
        )

        assert preflight_header_idx != -1, (
            "module-completion-track.md must have the fpdf2 Preflight Note "
            "section"
        )
        assert invocation_idx != -1, (
            "module-completion-track.md must invoke fpdf2_preflight.py"
        )
        assert present_idx != -1, (
            "module-completion-track.md must have the 'When track is complete' "
            "presentation block"
        )
        assert export_offer_idx != -1, (
            "module-completion-track.md must have the export offer"
        )

        # Preflight section + invocation come before the presentation block and
        # the export offer within it.
        assert preflight_header_idx < invocation_idx < present_idx, (
            "the preflight invocation must precede the track-completion "
            "presentation block"
        )
        assert invocation_idx < export_offer_idx, (
            "the preflight invocation must precede the export offer"
        )
