"""Preservation property suite for the recap-completeness-and-pdf bugfix.

Feature: recap-completeness-and-pdf (BUGFIX)

Property 2: Preservation — Already-Correct Recaps, Fitting PDFs, and Unrelated
Behavior.

Where the bug-condition exploration suite
(``test_recap_completeness_and_pdf_exploration.py``) encodes the *fixed*
contract and is EXPECTED TO FAIL on the unfixed state, this suite encodes the
behavior that must NOT change. Following the observation-first methodology, the
assertions here were derived by observing the UNFIXED code first and then
asserting the behavior it already exhibits, so the whole suite PASSES on the
unfixed state and continues to pass after the fix (regression prevention).

For ``isBugCondition(input) == FALSE`` inputs the system must be unaffected:

    Req 3.1  Existing per-module sections preserved byte-for-byte (no
             duplication / overwrite / out-of-order reordering); a recap already
             consistent with ``modules_completed`` yields an empty backfill plan,
             so nothing rewrites it.
    Req 3.2  Reconciliation is idempotent — re-running the planner on a
             consistent recap returns the same empty plan and makes no changes.
    Req 3.3  A recap whose body fits within the available width renders every
             heading and body line (no dropped content).
    Req 3.4  With ``fpdf2`` absent, both generators degrade gracefully: they
             print the ``pip install fpdf2`` hint, write no PDF, preserve the
             Markdown input, and never raise.
    Req 3.5  Unrelated completion hooks (celebration, etc.) behave exactly as
             before — this fix does not alter their trigger, action, or
             constraints.

Tooling: pytest + Hypothesis (per the repo ``fast``/``thorough`` profiles).
Scripts are stdlib-only; ``fpdf2`` is an optional dependency. The fitting-PDF
property requires a real render and is skipped when ``fpdf2`` is absent; the
``fpdf2``-absent degradation tests run regardless by blocking the import.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

from __future__ import annotations

import builtins
import contextlib
import io
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import completion_artifacts as ca  # noqa: E402
import generate_recap_pdf as grp  # noqa: E402
import generate_recap_pdf_inline as grpi  # noqa: E402
import recap_pdf_render as rpr  # noqa: E402

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_COMPLETION_ARTIFACTS_SCRIPT = _SCRIPTS_DIR / "completion_artifacts.py"

# Optional fpdf2 dependency — the fitting-PDF render property requires it.
try:
    import fpdf  # noqa: F401

    _FPDF_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    _FPDF_AVAILABLE = False

_NEEDS_FPDF = pytest.mark.skipif(
    not _FPDF_AVAILABLE, reason="fpdf2 not installed; fitting-PDF render requires it"
)


# ---------------------------------------------------------------------------
# Minimal PDF text extractor (stdlib-only) — mirrors the exploration suite.
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract visible text from a simple fpdf2-generated PDF using stdlib only.

    Decompresses each content stream (FlateDecode / zlib) when possible and
    concatenates the literal strings passed to the text-showing operators. This
    is sufficient to assert the presence of distinctive tokens and headings; it
    is not a general-purpose PDF parser.

    Args:
        pdf_bytes: Raw bytes of a written PDF file.

    Returns:
        The concatenated literal text content found in the PDF's streams.
    """
    chunks: list[str] = []
    # Capture the stream body up to ``endstream`` rather than requiring an
    # explicit ``\r?\n`` immediately before it. A binary FlateDecode stream can
    # legitimately end with a ``0x0D`` (\r) byte; the old ``\r?\nendstream``
    # boundary let ``\r?`` steal that trailing data byte, truncating the zlib
    # stream so ``zlib.decompress`` raised and the whole stream's text was lost
    # (a false negative on valid PDFs). ``decompressobj().decompress`` decodes
    # the zlib data and tolerates the trailing EOL bytes we now retain, whereas
    # ``zlib.decompress`` would reject that trailing data.
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.DOTALL):
        raw = match.group(1)
        try:
            data = zlib.decompressobj().decompress(raw)
        except zlib.error:
            data = raw
        for token in re.finditer(rb"\((?:\\.|[^\\)])*\)", data):
            literal = (
                token.group(0)[1:-1]
                .replace(b"\\(", b"(")
                .replace(b"\\)", b")")
                .replace(b"\\\\", b"\\")
            )
            chunks.append(literal.decode("latin-1", "replace"))
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Recap / progress fixture builders.
# ---------------------------------------------------------------------------

_MODULE_NAMES = {
    1: "Business Problem",
    2: "Licensing",
    3: "Entity Resolution Intro",
    4: "Data Sources",
    5: "Mapping",
    6: "Loading",
    7: "Querying",
}


def _module_section(number: int) -> str:
    """Build a single ``## Module N:`` recap section in canonical form.

    Args:
        number: The module number.

    Returns:
        The Markdown text for one module recap section (trailing ``---``).
    """
    name = _MODULE_NAMES.get(number, f"Module {number}")
    return (
        f"## Module {number}: {name} \u2014 2025-01-{number:02d}T10:00:00-05:00\n"
        "\n"
        "### Information Shared\n"
        f"- Key concept for module {number}\n"
        "\n"
        "### Questions Asked\n"
        "1. What problem does this solve?\n"
        "\n"
        "### Answers Given\n"
        "1. It resolves entities.\n"
        "\n"
        "### Actions Taken\n"
        f"- Completed module {number}\n"
        "\n"
        "### Duration\n"
        "1h 0m\n"
        "\n"
        "---\n"
    )


def _recap_markdown(section_modules: list[int]) -> str:
    """Build a recap document containing sections for the given modules.

    Args:
        section_modules: Module numbers that should have a ``## Module N:`` section,
            rendered in ascending (chronological) order.

    Returns:
        The full recap Markdown document.
    """
    header = (
        "# Senzing Bootcamp Recap\n"
        "\n"
        "**Bootcamper:** Tester\n"
        "**Started:** 2025-01-01T09:00:00-05:00\n"
        "**Total Duration:** 7h 0m\n"
        "\n"
        "---\n"
        "\n"
    )
    return header + "\n".join(_module_section(m) for m in sorted(section_modules))


def _build_project(
    tmp_path: Path,
    *,
    modules_completed: list[int],
    recap_section_modules: list[int],
) -> dict[str, Path]:
    """Materialise a project tree mirroring the bootcamper's workspace layout.

    Args:
        tmp_path: The per-test temporary directory.
        modules_completed: Module numbers recorded as completed in progress.
        recap_section_modules: Module numbers that have a recap section on disk.

    Returns:
        A mapping of logical names to the written paths.
    """
    config_dir = tmp_path / "config"
    docs_dir = tmp_path / "docs"
    progress_dir = docs_dir / "progress"
    config_dir.mkdir(parents=True, exist_ok=True)
    progress_dir.mkdir(parents=True, exist_ok=True)

    step_history = {
        str(m): {
            "last_completed_step": 5,
            "updated_at": f"2025-01-{m:02d}T11:00:00-05:00",
        }
        for m in modules_completed
    }
    progress = {
        "modules_completed": list(modules_completed),
        "current_module": max(modules_completed) if modules_completed else 1,
        "language": "python",
        "started_at": "2025-01-01T09:00:00-05:00",
        "step_history": step_history,
    }
    progress_path = config_dir / "bootcamp_progress.json"
    progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")

    recap_path = docs_dir / "bootcamp_recap.md"
    recap_path.write_text(_recap_markdown(recap_section_modules), encoding="utf-8")

    journal_path = docs_dir / "bootcamp_journal.md"
    journal_path.write_text("# Bootcamp Journal\n", encoding="utf-8")

    return {
        "progress": progress_path,
        "recap": recap_path,
        "journal": journal_path,
        "progress_dir": progress_dir,
    }


def _section_order(recap_text: str) -> list[int]:
    """Return the module numbers of ``## Module N:`` headings in document order."""
    return [int(m) for m in re.findall(r"^##\s+Module\s+(\d+):", recap_text, re.MULTILINE)]


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_ prefix per python-conventions).
# ---------------------------------------------------------------------------


@st.composite
def st_completed_modules(draw: st.DrawFn) -> list[int]:
    """Draw a non-empty set of completed module numbers (1..7, unique, sorted).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A sorted list of distinct module numbers.
    """
    modules = draw(
        st.lists(st.integers(min_value=1, max_value=7), min_size=1, max_size=7, unique=True)
    )
    return sorted(modules)


@st.composite
def st_consistent_inventory(
    draw: st.DrawFn,
) -> tuple[ca.ProgressState, ca.ArtifactInventory]:
    """Draw a (progress, inventory) pair whose recap is consistent with progress.

    "Consistent" means every completed module already has a recap section on
    disk (the inventory's ``recap_sections`` is a superset of
    ``modules_completed``), so the backfill plan must be empty — this is the
    non-bug input domain for reconciliation.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(ProgressState, ArtifactInventory)`` tuple in the non-bug domain.
    """
    completed = draw(st_completed_modules())
    # Recap sections cover all completed modules (and possibly extra, older ones).
    extra = draw(
        st.lists(st.integers(min_value=1, max_value=12), min_size=0, max_size=5, unique=True)
    )
    recap_sections = set(completed) | set(extra)
    journal_entries = set(completed) | set(
        draw(st.lists(st.integers(min_value=1, max_value=12), min_size=0, max_size=5))
    )
    progress = ca.ProgressState(
        modules_completed=completed, step_history={}, started_at=None
    )
    inventory = ca.ArtifactInventory(
        recap_sections=recap_sections,
        journal_entries=journal_entries,
        certificates=set(),
    )
    return progress, inventory


_LINE_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=6)
_TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@st.composite
def st_marker_token(draw: st.DrawFn) -> str:
    """Draw a distinctive ASCII marker token (``MARK`` + alnum).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty uppercase-alphanumeric marker token.
    """
    suffix = draw(st.text(alphabet=_TOKEN_ALPHABET, min_size=4, max_size=8))
    return f"MARK{suffix}"


@st.composite
def st_fitting_body(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Draw recap Markdown whose every line fits well within the page width.

    Each block is a short heading or a short prose line carrying exactly one
    unique marker token. Lines are capped to a small character budget so they
    never need to wrap — this is the non-bug PDF domain (Req 3.3), where every
    heading and body line must survive rendering.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(body_text, tokens)`` tuple: the Markdown body and the injected
        marker tokens.
    """
    tokens = draw(st.lists(st_marker_token(), min_size=1, max_size=5, unique=True))
    kinds = draw(
        st.lists(
            st.sampled_from(["heading", "prose"]),
            min_size=len(tokens),
            max_size=len(tokens),
        )
    )

    blocks: list[str] = []
    for token, kind in zip(tokens, kinds):
        # One or two short words keep each line comfortably under the page width
        # (default A4: effective width ~190mm; Helvetica 11pt fits ~90 chars).
        words = draw(st.lists(_LINE_WORD, min_size=1, max_size=2))
        text = " ".join([token, *words])
        if kind == "heading":
            level = draw(st.integers(min_value=1, max_value=3))
            blocks.append(f"{'#' * level} {text}")
        else:
            blocks.append(text)

    return "\n\n".join(blocks), tokens


# ---------------------------------------------------------------------------
# Req 3.1 — existing per-module sections preserved byte-for-byte.
# ---------------------------------------------------------------------------


class TestExistingSectionPreservation:
    """Req 3.1 — an already-consistent recap is left byte-for-byte unchanged.

    Observation (unfixed code): the deterministic planner is read-only and, for
    a recap already containing a ``## Module N:`` section for every completed
    module, ``plan_backfill`` returns an empty ``recap_modules`` set — so there
    is nothing to append or rewrite and existing content (and its chronological
    order) is preserved exactly.

    Validates: Requirements 3.1
    """

    def test_consistent_recap_plan_has_no_recap_backfill(self, tmp_path: Path) -> None:
        """A recap covering all completed modules yields an empty recap backfill."""
        modules_completed = [1, 2, 3, 4, 5, 6, 7]
        progress = ca.ProgressState(
            modules_completed=modules_completed, step_history={}, started_at=None
        )
        inventory = ca.ArtifactInventory(
            recap_sections=set(modules_completed),
            journal_entries=set(modules_completed),
            certificates=set(),
        )
        plan = ca.plan_backfill(progress, inventory)
        assert plan.recap_modules == [], (
            "a recap already consistent with modules_completed must require no "
            f"recap backfill, got {plan.recap_modules}"
        )

    def test_readonly_cli_leaves_recap_byte_for_byte_identical(
        self, tmp_path: Path
    ) -> None:
        """Running the planner CLI does not modify an existing recap file."""
        paths = _build_project(
            tmp_path,
            modules_completed=[1, 2, 3, 4, 5],
            recap_section_modules=[1, 2, 3, 4, 5],
        )
        before = paths["recap"].read_bytes()

        for mode in ("--plan", "--check"):
            subprocess.run(
                [
                    sys.executable,
                    str(_COMPLETION_ARTIFACTS_SCRIPT),
                    "--progress",
                    str(paths["progress"]),
                    "--recap",
                    str(paths["recap"]),
                    "--journal",
                    str(paths["journal"]),
                    "--progress-dir",
                    str(paths["progress_dir"]),
                    mode,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        after = paths["recap"].read_bytes()
        assert after == before, "existing recap content must be preserved byte-for-byte"

    @given(modules=st_completed_modules())
    def test_existing_sections_preserved_in_chronological_order(
        self, modules: list[int]
    ) -> None:
        """**Validates: Requirements 3.1**.

        For any set of completed modules, a consistent recap requires no recap
        backfill, and its sections are already in ascending chronological order
        (no duplication or out-of-order reordering is introduced).
        """
        progress = ca.ProgressState(
            modules_completed=modules, step_history={}, started_at=None
        )
        inventory = ca.ArtifactInventory(
            recap_sections=set(modules),
            journal_entries=set(modules),
            certificates=set(),
        )
        plan = ca.plan_backfill(progress, inventory)
        assert plan.recap_modules == []

        recap_text = _recap_markdown(modules)
        order = _section_order(recap_text)
        assert order == sorted(modules), "sections must stay in chronological order"
        assert len(order) == len(set(order)), "no section may be duplicated"


# ---------------------------------------------------------------------------
# Req 3.2 — idempotent reconciliation.
# ---------------------------------------------------------------------------


class TestIdempotentReconciliation:
    """Req 3.2 — reconciliation on a consistent recap is idempotent.

    Observation (unfixed code): ``plan_backfill`` / ``detect_artifact_gaps`` are
    pure set-difference computations, so for a recap already consistent with
    ``modules_completed`` they return an empty plan, and re-running them yields
    the identical empty plan — no spurious changes.

    Validates: Requirements 3.2
    """

    @given(world=st_consistent_inventory())
    def test_consistent_plan_is_empty(
        self, world: tuple[ca.ProgressState, ca.ArtifactInventory]
    ) -> None:
        """**Validates: Requirements 3.2**.

        For any recap consistent with ``modules_completed``, the recap backfill
        plan is empty.
        """
        progress, inventory = world
        plan = ca.plan_backfill(progress, inventory)
        assert plan.recap_modules == []

    @given(world=st_consistent_inventory())
    def test_reconciliation_is_idempotent(
        self, world: tuple[ca.ProgressState, ca.ArtifactInventory]
    ) -> None:
        """**Validates: Requirements 3.2**.

        Re-running the planner on a consistent recap returns the identical empty
        recap backfill — re-running makes no changes.
        """
        progress, inventory = world
        first = ca.plan_backfill(progress, inventory)
        second = ca.plan_backfill(progress, inventory)
        assert first.recap_modules == second.recap_modules == []
        gaps_first = ca.detect_artifact_gaps(progress.modules_completed, inventory)
        gaps_second = ca.detect_artifact_gaps(progress.modules_completed, inventory)
        assert gaps_first.missing_recap == gaps_second.missing_recap == []


# ---------------------------------------------------------------------------
# Req 3.3 — fitting PDF bodies render every heading and body line.
# ---------------------------------------------------------------------------


@_NEEDS_FPDF
class TestFittingPdfPreservation:
    """Req 3.3 — a recap whose body fits within width renders fully.

    Observation (unfixed code): when every line fits within the available width
    (no wrapping failure), the Shared_Renderer emits every heading and body line
    and the extracted PDF text contains them all. This non-bug PDF domain must
    keep rendering identically after the fix.

    Validates: Requirements 3.3
    """

    def test_representative_fitting_recap_renders_all_lines(
        self, tmp_path: Path
    ) -> None:
        """A representative short-line recap body renders every line."""
        body = (
            "# Heading One\n\n"
            "short prose line alpha\n\n"
            "- bullet item beta\n"
            "- bullet item gamma\n\n"
            "## Heading Two\n\n"
            "another short line delta\n"
        )
        output = tmp_path / "fitting.pdf"
        rpr.render_markdown_pdf(body, str(output), title="Fitting Recap")

        text = extract_pdf_text(output.read_bytes())
        for needle in (
            "Heading One",
            "short prose line alpha",
            "bullet item beta",
            "bullet item gamma",
            "Heading Two",
            "another short line delta",
        ):
            assert needle in text, f"fitting body line {needle!r} was dropped"

    @given(data=st_fitting_body())
    def test_fitting_body_tokens_all_present(
        self, data: tuple[str, list[str]], tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """**Validates: Requirements 3.3**.

        For any fitting body content, the extracted PDF text contains every
        heading and body line (token), with no dropped content.
        """
        body, tokens = data
        out_dir = tmp_path_factory.mktemp("fitting")
        output = out_dir / "recap.pdf"
        rpr.render_markdown_pdf(body, str(output), title="Fitting Recap")

        text = extract_pdf_text(output.read_bytes())
        for token in tokens:
            assert token in text, f"fitting body token {token!r} was dropped"


# ---------------------------------------------------------------------------
# Req 3.4 — graceful degradation when fpdf2 is absent.
# ---------------------------------------------------------------------------


def _run_with_fpdf_absent(func) -> object:
    """Invoke ``func`` with the ``fpdf`` import forced to fail.

    Args:
        func: A zero-argument callable to run while ``import fpdf`` raises
            ``ImportError``.

    Returns:
        Whatever ``func`` returns.
    """
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "fpdf" or name.startswith("fpdf."):
            raise ImportError("No module named 'fpdf'")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = _blocked
    try:
        return func()
    finally:
        builtins.__import__ = real_import


class TestFpdfAbsentDegradation:
    """Req 3.4 — both generators degrade gracefully when ``fpdf2`` is absent.

    Observation (unfixed code): with ``import fpdf`` failing, each generator
    prints the ``pip install fpdf2`` hint to stderr, returns exit code 1, writes
    no PDF, leaves the Markdown input intact, and never raises.

    Validates: Requirements 3.4
    """

    _RECAP = (
        "# Senzing Bootcamp Recap\n\n"
        "**Bootcamper:** Tester\n"
        "**Started:** 2025-01-01T09:00:00-05:00\n\n"
        "---\n\n"
        "## Module 1: Business Problem \u2014 2025-01-01T10:00:00-05:00\n\n"
        "### Information Shared\n- a concept\n\n"
        "### Duration\n1h 0m\n\n"
        "---\n"
    )

    def test_bundled_generator_degrades_gracefully(self, tmp_path: Path) -> None:
        """``generate_recap_pdf`` prints the hint, writes no PDF, keeps Markdown."""
        recap_path = tmp_path / "recap.md"
        recap_path.write_text(self._RECAP, encoding="utf-8")
        output = tmp_path / "out.pdf"

        out, err = io.StringIO(), io.StringIO()

        def _invoke() -> int:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                return grp.main(["--input", str(recap_path), "--output", str(output)])

        exit_code = _run_with_fpdf_absent(_invoke)

        assert exit_code == 1, "absent fpdf2 must yield a non-zero exit"
        assert "pip install fpdf2" in err.getvalue(), "the install hint must be printed"
        assert not output.exists(), "no PDF should be written when fpdf2 is absent"
        assert recap_path.read_text(encoding="utf-8") == self._RECAP, (
            "the Markdown input must be preserved"
        )

    def test_inline_generator_degrades_gracefully(self, tmp_path: Path) -> None:
        """``generate_recap_pdf_inline`` prints the hint, writes no PDF, keeps Markdown."""
        recap_path = tmp_path / "recap.md"
        recap_path.write_text(self._RECAP, encoding="utf-8")
        output = tmp_path / "out.pdf"

        out, err = io.StringIO(), io.StringIO()

        def _invoke() -> int:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                return grpi.main(["--input", str(recap_path), "--output", str(output)])

        exit_code = _run_with_fpdf_absent(_invoke)

        assert exit_code == 1, "absent fpdf2 must yield a non-zero exit"
        assert "pip install fpdf2" in err.getvalue(), "the install hint must be printed"
        assert not output.exists(), "no PDF should be written when fpdf2 is absent"
        assert recap_path.read_text(encoding="utf-8") == self._RECAP, (
            "the Markdown input must be preserved"
        )


# ---------------------------------------------------------------------------
# Req 3.5 — unrelated completion hooks behave exactly as before.
# ---------------------------------------------------------------------------


def _load_hook(name: str) -> dict:
    """Load and parse a ``.kiro.hook`` JSON file from the hooks directory.

    Args:
        name: The hook filename (e.g. ``module-completion-celebration.kiro.hook``).

    Returns:
        The parsed hook object.
    """
    return json.loads((_HOOKS_DIR / name).read_text(encoding="utf-8"))


class TestUnrelatedHookPreservation:
    """Req 3.5 — completion hooks other than recap-append are unchanged.

    Observation (unfixed code): the module-completion-celebration hook is an
    ``agentStop`` / ``askAgent`` hook whose prompt explicitly forbids writing
    files or running scripts and never invokes ``completion_artifacts.py``. This
    fix touches only the recap-append path, so the celebration hook's trigger,
    action, and constraints must remain exactly as observed here. The
    recap-append hook itself also still declares that it must not alter other
    hooks' behavior.

    Validates: Requirements 3.5
    """

    def test_celebration_hook_trigger_and_action_unchanged(self) -> None:
        """The celebration hook stays an agentStop/askAgent hook."""
        hook = _load_hook("module-completion-celebration.kiro.hook")
        assert hook["when"]["type"] == "agentStop"
        assert hook["then"]["type"] == "askAgent"

    def test_celebration_hook_remains_read_only(self) -> None:
        """The celebration hook still forbids writes and script execution."""
        hook = _load_hook("module-completion-celebration.kiro.hook")
        prompt = hook["then"]["prompt"]
        assert "Do NOT write any files." in prompt
        assert "Do NOT run any scripts or commands." in prompt
        # It is unrelated to the recap reconciliation path, so it must not run
        # the completion-artifacts planner.
        assert "completion_artifacts.py" not in prompt

    def test_recap_hook_preserves_other_hooks_clause(self) -> None:
        """The recap-append hook still declares it must not alter other hooks."""
        hook = _load_hook("module-recap-append.kiro.hook")
        prompt = hook["then"]["prompt"]
        assert "Do NOT alter the behavior of any other hooks" in prompt
