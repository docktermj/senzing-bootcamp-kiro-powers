"""Bug-condition EXPLORATION tests for the missing-bundled-scripts bugfix (power).

These tests exercise the bootcamp/graduation steps and onboarding preflight that
shell out to bundled scripts under ``senzing-bootcamp/scripts/`` from a workspace
where that directory does NOT exist — the ``isBugCondition(X)`` domain
(``NOT fileExists(X.scriptPath)``).

They encode the EXPECTED (fixed) behavior from design Property 1:

    FOR ALL X WHERE isBugCondition(X):
        result.exitCode == 0
        NOT result.emittedFileNotFoundError
        downstreamEffectPreserved(X)
            # graduation Step 0b still renders docs/bootcamp_recap.pdf from
            # docs/bootcamp_recap.md when fpdf2 is present (else degrades
            # gracefully with a `pip install fpdf2` hint), generic steps degrade
            # gracefully, and onboarding warns + self-repairs a missing scripts
            # directory.

The fixed flow has two coordinated parts these tests rely on: onboarding
materializes / self-repairs the bundled ``senzing-bootcamp/scripts/`` directory
into the workspace (Req 2.5), and the steps degrade gracefully / use a
file-independent inline path (Req 2.3, 2.4). Each step test first performs the
onboarding self-repair (by running the installed power's ``preflight.py --fix``
against the throwaway workspace) and then runs the documented step command(s).

**They are AUTHORED TO FAIL on the current (unfixed) code** — preflight has no
bundled-scripts check/self-repair, so the scripts directory stays absent and the
step commands exit with a file-not-found error and produce no deliverable. Those
failures CONFIRM the bug; they must NOT be "fixed" here. After the fix, these
same tests will pass.

Feature: missing-bundled-scripts

**Validates: Requirements 2.3, 2.4, 2.5** (the fixed behavior these encode)
Explores defect Requirements 1.3, 1.4, 1.5.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths to the REAL installed power (always present — it IS the power). The
# throwaway workspace, by contrast, has no senzing-bootcamp/scripts/ directory.
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_INSTALLED_SCRIPTS: Path = _POWER_ROOT / "scripts"
_INSTALLED_PREFLIGHT: Path = _INSTALLED_SCRIPTS / "preflight.py"

if str(_INSTALLED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_INSTALLED_SCRIPTS))

# Workspace-relative paths the documented graduation/onboarding steps use.
_RECAP_MD: str = "docs/bootcamp_recap.md"
_RECAP_PDF: str = "docs/bootcamp_recap.pdf"
_PROGRESS_PATH: str = "config/bootcamp_progress.json"

# Bundled script names referenced by the documented Step 0b.3 sequence and a
# representative generic step. Resolved relative to the workspace cwd.
_RECAP_GENERATOR: str = "senzing-bootcamp/scripts/generate_recap_pdf.py"
_RECAP_GENERATOR_INLINE: str = "senzing-bootcamp/scripts/generate_recap_pdf_inline.py"
_GENERIC_STEP_SCRIPT: str = "senzing-bootcamp/scripts/generate_docs_index.py"

_FILE_NOT_FOUND_MARKERS: tuple[str, ...] = (
    "No such file or directory",
    "can't open file",
    "cannot find the file",
)

_FPDF_HINT_MARKERS: tuple[str, ...] = ("pip install fpdf2", "fpdf2 is required")


def _fpdf_available() -> bool:
    """Return True when the optional ``fpdf2`` library can be imported."""
    try:
        import fpdf  # noqa: F401
    except Exception:
        return False
    return True


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------


def _new_workspace() -> Path:
    """Create a throwaway workspace with docs/ and config/ but NO scripts dir.

    Returns:
        Path to the workspace root (its ``senzing-bootcamp/scripts/`` is absent).
    """
    workspace = Path(tempfile.mkdtemp(prefix="missing_scripts_power_"))
    (workspace / "docs").mkdir(parents=True, exist_ok=True)
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    return workspace


def _write_recap(workspace: Path, body: str) -> None:
    """Write a recap Markdown document into *workspace*.

    Args:
        workspace: The workspace root.
        body: The recap Markdown body to write to ``docs/bootcamp_recap.md``.
    """
    (workspace / _RECAP_MD).write_text(body, encoding="utf-8")


def _onboard(workspace: Path) -> subprocess.CompletedProcess[str]:
    """Run the installed power's onboarding self-repair against *workspace*.

    Invokes ``preflight.py --fix`` from the installed power so that — once the
    fix lands (Req 2.5) — the bundled ``senzing-bootcamp/scripts/`` directory is
    materialized into the workspace before any step depends on it. On unfixed
    code this performs no such materialization, leaving the bug condition intact.

    Args:
        workspace: The workspace to self-repair.

    Returns:
        The completed preflight process (its outcome is not asserted here).
    """
    return subprocess.run(
        [sys.executable, str(_INSTALLED_PREFLIGHT), "--fix", "--json"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _run(
    workspace: Path, args: list[str], env: dict | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command in *workspace* with captured output.

    Args:
        workspace: The working directory.
        args: The argument vector to execute.
        env: Optional environment overrides merged onto the current environment.

    Returns:
        The completed process.
    """
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    return subprocess.run(
        args,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=120,
        env=run_env,
    )


def _run_step_0b(workspace: Path, env: dict | None = None) -> tuple[bool, str]:
    """Simulate the documented graduation Step 0b.3 PDF-generation sequence.

    Mirrors ``senzing-bootcamp/steering/graduation.md`` Step 0b.3: prefer the
    bundled ``generate_recap_pdf.py``, then fall back to
    ``generate_recap_pdf_inline.py``. A PDF is considered written only when a
    generator prints a ``PDF generated:`` line and exits 0.

    Args:
        workspace: The workspace to run the sequence in.
        env: Optional environment overrides (used to simulate an absent fpdf2).

    Returns:
        A ``(file_not_found, combined_output)`` tuple where ``file_not_found``
        is True if any invocation emitted a file-not-found error.
    """
    commands = [
        [sys.executable, _RECAP_GENERATOR],
        [
            sys.executable,
            _RECAP_GENERATOR_INLINE,
            "--input",
            _RECAP_MD,
            "--output",
            _RECAP_PDF,
        ],
    ]
    combined: list[str] = []
    file_not_found = False
    for args in commands:
        result = _run(workspace, args, env=env)
        combined.append(result.stdout)
        combined.append(result.stderr)
        blob = f"{result.stdout}\n{result.stderr}"
        if any(marker in blob for marker in _FILE_NOT_FOUND_MARKERS):
            file_not_found = True
        # A successful generator both exits 0 and announces the PDF.
        if result.returncode == 0 and "PDF generated:" in result.stdout:
            break
    return file_not_found, "\n".join(combined)


# ---------------------------------------------------------------------------
# Hypothesis strategy — random recap Markdown bodies
# ---------------------------------------------------------------------------

_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)


@st.composite
def st_recap_markdown(draw) -> str:
    """Draw a recap Markdown body containing at least one module section.

    Builds a header plus one or more ``## Module N:`` sections with random prose
    and list items so the recap renderer exercises headings, lists, and prose.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A recap Markdown body string.
    """
    n_modules = draw(st.integers(min_value=1, max_value=3))
    numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=n_modules,
            max_size=n_modules,
            unique=True,
        )
    )
    lines: list[str] = ["# Senzing Bootcamp Recap", "", "**Bootcamper:** Test", ""]
    for number in numbers:
        title = " ".join(draw(st.lists(_WORD, min_size=1, max_size=4)))
        lines.append(f"## Module {number}: {title}")
        lines.append("")
        lines.append(" ".join(draw(st.lists(_WORD, min_size=1, max_size=10))))
        lines.append("")
        lines.append("### Actions Taken")
        for item in draw(st.lists(_WORD, min_size=1, max_size=4)):
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Case 2 — missing recap generators with fpdf2 present (Step 0b → PDF)
# ---------------------------------------------------------------------------


class TestMissingRecapGeneratorsExploration:
    """Step 0b must still render the recap PDF when the generators are absent.

    **Validates: Requirements 2.4, 2.5**

    With ``fpdf2`` installed and the bundled recap generators absent from the
    workspace, graduation Step 0b must self-repair/use the inline path and
    render ``docs/bootcamp_recap.pdf`` from ``docs/bootcamp_recap.md`` — exiting
    0 with no file-not-found error.

    AUTHORED TO FAIL on unfixed code (no materialization/inline path → the
    generator commands hit a file-not-found error and no PDF is produced).
    """

    @pytest.mark.skipif(not _fpdf_available(), reason="fpdf2 not installed")
    @given(body=st_recap_markdown())
    def test_missing_generators_render_pdf_for_all_recaps(self, body: str) -> None:
        """For all recap bodies, a missing generator still yields a PDF (fpdf2 present).

        The onboarded workspace is created inline per generated example (rather
        than via a function-scoped fixture) so each example gets a fresh,
        self-repaired workspace — mirroring the example-based twin test and the
        preservation suite's pattern, and avoiding Hypothesis's
        function-scoped-fixture health check.
        """
        workspace = _new_workspace()
        (workspace / _PROGRESS_PATH).write_text(
            '{"current_module": 11, "modules_completed": [1]}', encoding="utf-8"
        )
        _onboard(workspace)
        pdf_path = workspace / _RECAP_PDF
        if pdf_path.exists():
            pdf_path.unlink()
        _write_recap(workspace, body)

        file_not_found, output = _run_step_0b(workspace)

        assert not file_not_found, (
            "Step 0b must not emit a file-not-found error for a missing "
            f"generator; output={output!r}"
        )
        assert pdf_path.exists() and pdf_path.stat().st_size > 0, (
            "Step 0b must render docs/bootcamp_recap.pdf from the recap Markdown "
            f"via the inline path when fpdf2 is present; output={output!r}"
        )

    @pytest.mark.skipif(not _fpdf_available(), reason="fpdf2 not installed")
    def test_missing_generators_render_pdf_example(self) -> None:
        """Concrete Step 0b run with both generators absent renders a PDF."""
        workspace = _new_workspace()
        (workspace / _PROGRESS_PATH).write_text(
            '{"current_module": 11, "modules_completed": [1]}', encoding="utf-8"
        )
        _write_recap(
            workspace,
            "# Senzing Bootcamp Recap\n\n## Module 1: Business Problem\n\n"
            "### Actions Taken\n- defined the problem\n",
        )
        _onboard(workspace)

        file_not_found, output = _run_step_0b(workspace)

        assert not file_not_found, f"unexpected file-not-found error; output={output!r}"
        assert (workspace / _RECAP_PDF).exists(), (
            f"expected docs/bootcamp_recap.pdf to be rendered; output={output!r}"
        )


# ---------------------------------------------------------------------------
# Case 3 — missing generic step script degrades gracefully
# ---------------------------------------------------------------------------


class TestMissingGenericStepExploration:
    """A step shelling out to an absent bundled script must degrade gracefully.

    **Validates: Requirements 2.3, 2.5**

    Invoking a representative generic step
    (``senzing-bootcamp/scripts/generate_docs_index.py``) from a workspace
    lacking the scripts directory must exit 0 with no file-not-found error after
    the onboarding self-repair.

    AUTHORED TO FAIL on unfixed code (script absent → exit 2, file-not-found).
    """

    def test_missing_generic_step_degrades_gracefully(self) -> None:
        """The generic step exits 0 with no file-not-found error."""
        workspace = _new_workspace()
        _onboard(workspace)

        result = _run(workspace, [sys.executable, _GENERIC_STEP_SCRIPT])

        blob = f"{result.stdout}\n{result.stderr}"
        assert not any(m in blob for m in _FILE_NOT_FOUND_MARKERS), (
            "generic step must not emit a file-not-found error when the bundled "
            f"script is absent; stderr={result.stderr!r}"
        )
        assert result.returncode == 0, (
            "generic step must degrade gracefully (exit 0) when the bundled "
            f"script is absent, got returncode={result.returncode}; "
            f"stderr={result.stderr!r}"
        )


# ---------------------------------------------------------------------------
# Case 4 — onboarding preflight warns + self-repairs an absent scripts dir
# ---------------------------------------------------------------------------


class TestOnboardingScriptsDirectoryCheckExploration:
    """Preflight must verify (warn + self-repair) the bundled scripts directory.

    **Validates: Requirements 2.5**

    With no ``senzing-bootcamp/scripts/`` directory in the workspace, preflight
    must surface a ``warn`` ``CheckResult`` (with a remediation ``fix`` message)
    for the missing bundled scripts, and self-repair it under ``--fix``.

    AUTHORED TO FAIL on unfixed code (no such check exists — only a generic
    top-level ``scripts`` directory check, which does not cover the bundled
    ``senzing-bootcamp/scripts/`` directory or its required scripts).
    """

    @staticmethod
    def _references_bundled_scripts(check) -> bool:
        """Return True when a CheckResult targets the bundled scripts directory.

        Matches on the bundled path ``senzing-bootcamp/scripts`` or any required
        bundled script basename, but NOT the generic top-level ``scripts`` dir
        check that already exists.
        """
        text = f"{check.name} {check.message} {check.fix or ''}".replace("\\", "/")
        if "senzing-bootcamp/scripts" in text:
            return True
        required = (
            "log_write_event.py",
            "session_logger.py",
            "generate_recap_pdf.py",
            "generate_recap_pdf_inline.py",
        )
        return any(name in text for name in required)

    def test_preflight_warns_and_self_repairs_missing_scripts_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Preflight surfaces a warn + self-repair for the missing scripts dir."""
        monkeypatch.chdir(tmp_path)  # workspace has no senzing-bootcamp/scripts/

        preflight = importlib.import_module("preflight")
        preflight = importlib.reload(preflight)

        report = preflight.CheckRunner().run(fix=False)
        script_checks = [
            c for c in report.checks if self._references_bundled_scripts(c)
        ]
        assert script_checks, (
            "preflight must include a check that verifies the bundled "
            "senzing-bootcamp/scripts/ directory and its required scripts; "
            f"found none among {[c.name for c in report.checks]}"
        )
        warned = [c for c in script_checks if c.status == "warn"]
        assert warned, (
            "the bundled-scripts check must WARN (not fail) when absent; got "
            f"statuses {[c.status for c in script_checks]}"
        )
        assert all(c.fix for c in warned), (
            "the bundled-scripts warn must include a remediation 'fix' message"
        )

        report_fixed = preflight.CheckRunner().run(fix=True)
        repaired = [
            c for c in report_fixed.checks if self._references_bundled_scripts(c)
        ]
        assert repaired and any(
            c.status == "pass" or c.fixed for c in repaired
        ), (
            "preflight --fix must self-repair the missing bundled scripts "
            f"directory; got {[(c.status, c.fixed) for c in repaired]}"
        )


# ---------------------------------------------------------------------------
# Case 5 — edge case: generators absent and fpdf2 absent (graceful degradation)
# ---------------------------------------------------------------------------


class TestMissingGeneratorsNoFpdfExploration:
    """With generators absent and fpdf2 absent, Step 0b degrades gracefully.

    **Validates: Requirements 2.4**

    When ``fpdf2`` cannot be imported and the bundled generators are absent,
    Step 0b must retain the Markdown recap, surface a ``pip install fpdf2`` hint,
    and raise no unhandled error (no traceback) — producing no PDF.

    AUTHORED TO FAIL on unfixed code (script absent → file-not-found error
    instead of the graceful ``pip install fpdf2`` hint).
    """

    def test_step_0b_degrades_gracefully_without_fpdf(self, tmp_path: Path) -> None:
        """A blocked fpdf2 yields a hint, retains the Markdown, and writes no PDF."""
        workspace = _new_workspace()
        _write_recap(
            workspace,
            "# Senzing Bootcamp Recap\n\n## Module 1: Business Problem\n\n"
            "### Actions Taken\n- defined the problem\n",
        )
        _onboard(workspace)

        # Simulate an absent fpdf2: a shim package whose import raises ImportError,
        # placed ahead of site-packages on PYTHONPATH.
        shim_dir = tmp_path / "fpdf_shim"
        (shim_dir / "fpdf").mkdir(parents=True, exist_ok=True)
        (shim_dir / "fpdf" / "__init__.py").write_text(
            'raise ImportError("fpdf2 not installed (simulated)")\n',
            encoding="utf-8",
        )
        env = {
            "PYTHONPATH": str(shim_dir) + os.pathsep + os.environ.get("PYTHONPATH", "")
        }

        file_not_found, output = _run_step_0b(workspace, env=env)

        assert not file_not_found, (
            "Step 0b must not emit a file-not-found error even when fpdf2 is "
            f"absent; output={output!r}"
        )
        assert "Traceback (most recent call last)" not in output, (
            f"Step 0b must not raise an unhandled error; output={output!r}"
        )
        assert any(marker in output for marker in _FPDF_HINT_MARKERS), (
            "Step 0b must surface a 'pip install fpdf2' hint when fpdf2 is "
            f"absent; output={output!r}"
        )
        assert (workspace / _RECAP_MD).exists(), "the Markdown recap must be retained"
        assert not (workspace / _RECAP_PDF).exists(), (
            "no PDF should be produced when fpdf2 is absent"
        )
