"""Preservation property tests for the missing-bundled-scripts bugfix (power).

These tests capture the baseline behavior that MUST remain unchanged when the
referenced bundled script IS present — the ``NOT isBugCondition(X)`` domain
(``fileExists(X.scriptPath)``). They follow the observation-first methodology:
each present-script invocation is run against the CURRENT (unfixed) code and the
actual outputs are asserted, establishing the behavior the fix must preserve.

They encode design Property 2 (Preservation):

    FOR ALL X WHERE NOT isBugCondition(X):
        F(X) = F'(X)

Covered preservation properties (from design Preservation Requirements):
- Bundled recap generator preservation (Req 3.3): with ``generate_recap_pdf.py``
  present, graduation Step 0b uses it first (then ``generate_recap_pdf_inline.py``)
  — the bundled generator renders ``docs/bootcamp_recap.pdf`` and the preference
  order is unchanged.
- Present generic step preservation (Req 3.2): a present bundled step script
  executes its own behavior (exit code / output), never a file-not-found error.
- Markdown-only degradation preservation (Req 3.4): with a present generator but
  ``fpdf2`` absent, the system degrades gracefully — retains the Markdown recap,
  prints a ``pip install fpdf2`` hint, raises no unhandled error, writes no PDF.
- No-overwrite preservation (Req 3.5): onboarding verification/materialization
  (``preflight.py --fix``) leaves already-present valid bundled scripts
  byte-for-byte unchanged (idempotent, no clobber).

**These tests are EXPECTED TO PASS on the current (unfixed) code** (the scripts
are present, so the bug condition does not hold) and must continue to pass after
the fix.

Feature: missing-bundled-scripts

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths to the REAL installed power. Present-script preservation copies the
# bundled scripts into each throwaway workspace so the invocation site finds
# them (NOT isBugCondition).
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_INSTALLED_SCRIPTS: Path = _POWER_ROOT / "scripts"
_INSTALLED_PREFLIGHT: Path = _INSTALLED_SCRIPTS / "preflight.py"

# Workspace-relative paths the documented graduation/onboarding steps use.
_RECAP_MD: str = "docs/bootcamp_recap.md"
_RECAP_PDF: str = "docs/bootcamp_recap.pdf"
_WORKSPACE_SCRIPTS: str = "senzing-bootcamp/scripts"

# Bundled script names referenced by the documented Step 0b.3 sequence and a
# representative generic step.
_RECAP_GENERATOR_NAME: str = "generate_recap_pdf.py"
_RECAP_GENERATOR_INLINE_NAME: str = "generate_recap_pdf_inline.py"
_RECAP_RENDER_NAME: str = "recap_pdf_render.py"
_GENERIC_STEP_NAME: str = "generate_docs_index.py"

_RECAP_GENERATOR: str = f"{_WORKSPACE_SCRIPTS}/{_RECAP_GENERATOR_NAME}"
_RECAP_GENERATOR_INLINE: str = f"{_WORKSPACE_SCRIPTS}/{_RECAP_GENERATOR_INLINE_NAME}"
_GENERIC_STEP_SCRIPT: str = f"{_WORKSPACE_SCRIPTS}/{_GENERIC_STEP_NAME}"

# Required bundled scripts whose byte-for-byte stability the no-overwrite
# preservation property guards.
_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "log_write_event.py",
    "session_logger.py",
    _RECAP_GENERATOR_NAME,
    _RECAP_GENERATOR_INLINE_NAME,
    _RECAP_RENDER_NAME,
)

_FILE_NOT_FOUND_MARKERS: tuple[str, ...] = (
    "No such file or directory",
    "can't open file",
    "cannot find the file",
)

_FPDF_HINT_MARKERS: tuple[str, ...] = ("pip install fpdf2", "fpdf2 is required")


def _fpdf_available() -> bool:
    """Return True when the optional ``fpdf2`` library can be imported.

    Returns:
        True if ``import fpdf`` succeeds, else False.
    """
    try:
        import fpdf  # noqa: F401
    except Exception:
        return False
    return True


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------


def _new_workspace() -> Path:
    """Create a throwaway workspace with ``docs/``, ``config/``, and a scripts dir.

    Returns:
        Path to the workspace root; its ``senzing-bootcamp/scripts/`` directory
        is created empty, ready for the bundled scripts to be materialized.
    """
    workspace = Path(tempfile.mkdtemp(prefix="missing_scripts_pres_"))
    (workspace / "docs").mkdir(parents=True, exist_ok=True)
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    (workspace / _WORKSPACE_SCRIPTS).mkdir(parents=True, exist_ok=True)
    return workspace


def _materialize_scripts(workspace: Path, names: tuple[str, ...]) -> None:
    """Copy the named bundled scripts from the installed power into *workspace*.

    Places each script under the workspace's ``senzing-bootcamp/scripts/`` so the
    documented invocation paths resolve (the present-script / non-bug-condition
    case).

    Args:
        workspace: The workspace root to materialize scripts into.
        names: Bundled script filenames to copy from the installed power.
    """
    dest_dir = workspace / _WORKSPACE_SCRIPTS
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy2(_INSTALLED_SCRIPTS / name, dest_dir / name)


def _write_recap(workspace: Path, body: str) -> None:
    """Write a recap Markdown document into *workspace*.

    Args:
        workspace: The workspace root.
        body: Recap Markdown body to write to ``docs/bootcamp_recap.md``.
    """
    (workspace / _RECAP_MD).write_text(body, encoding="utf-8")


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


def _run_step_0b(workspace: Path, env: dict | None = None) -> tuple[int, bool, str]:
    """Run the documented graduation Step 0b.3 PDF-generation sequence.

    Mirrors ``senzing-bootcamp/steering/graduation.md`` Step 0b.3: prefer the
    bundled ``generate_recap_pdf.py``, then fall back to
    ``generate_recap_pdf_inline.py``. The sequence stops at the first generator
    that exits 0 and announces ``PDF generated:``.

    Args:
        workspace: The workspace to run the sequence in.
        env: Optional environment overrides.

    Returns:
        A ``(producer_index, file_not_found, combined_output)`` tuple where
        ``producer_index`` is the 0-based index of the command that produced the
        PDF (``-1`` if none did) and ``file_not_found`` is True if any invocation
        emitted a file-not-found error.
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
    producer_index = -1
    for index, args in enumerate(commands):
        result = _run(workspace, args, env=env)
        combined.append(result.stdout)
        combined.append(result.stderr)
        blob = f"{result.stdout}\n{result.stderr}"
        if any(marker in blob for marker in _FILE_NOT_FOUND_MARKERS):
            file_not_found = True
        if result.returncode == 0 and "PDF generated:" in result.stdout:
            producer_index = index
            break
    return producer_index, file_not_found, "\n".join(combined)


def _fpdf_absent_env(tmp_path: Path) -> dict:
    """Build an environment in which ``import fpdf`` raises ImportError.

    Places a shim ``fpdf`` package whose import fails ahead of site-packages on
    ``PYTHONPATH`` so a subprocess behaves as if the optional dependency were not
    installed.

    Args:
        tmp_path: A pytest tmp directory to host the shim package.

    Returns:
        An environment-override mapping suitable for :func:`_run`.
    """
    shim_dir = tmp_path / "fpdf_shim"
    (shim_dir / "fpdf").mkdir(parents=True, exist_ok=True)
    (shim_dir / "fpdf" / "__init__.py").write_text(
        'raise ImportError("fpdf2 not installed (simulated)")\n',
        encoding="utf-8",
    )
    return {
        "PYTHONPATH": str(shim_dir) + os.pathsep + os.environ.get("PYTHONPATH", "")
    }


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's bytes.

    Args:
        path: File to hash.

    Returns:
        The hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot_scripts(workspace: Path, names: tuple[str, ...]) -> dict[str, str]:
    """Snapshot ``{name: sha256}`` for the named scripts in *workspace*.

    Args:
        workspace: The workspace whose bundled scripts to snapshot.
        names: Bundled script filenames to snapshot.

    Returns:
        A mapping of script filename to its SHA-256 hex digest.
    """
    scripts_dir = workspace / _WORKSPACE_SCRIPTS
    return {name: _sha256(scripts_dir / name) for name in names}


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
# Preservation — bundled recap generator preferred and used (Req 3.3)
# ---------------------------------------------------------------------------


class TestBundledRecapGeneratorPreservation:
    """Preservation — present bundled recap generator is used, order unchanged.

    **Validates: Requirements 3.3**

    With ``generate_recap_pdf.py`` present (not the bug condition) and ``fpdf2``
    available, graduation Step 0b renders ``docs/bootcamp_recap.pdf`` via the
    bundled generator, which is preferred first over
    ``generate_recap_pdf_inline.py``. These are the present-script baselines the
    fix must leave unchanged.
    """

    @pytest.mark.skipif(not _fpdf_available(), reason="fpdf2 not installed")
    @given(body=st_recap_markdown())
    def test_present_bundled_generator_renders_pdf_for_all_recaps(
        self, body: str
    ) -> None:
        """For all recap bodies, the present bundled generator renders a PDF."""
        workspace = _new_workspace()
        _materialize_scripts(
            workspace,
            (
                _RECAP_GENERATOR_NAME,
                _RECAP_GENERATOR_INLINE_NAME,
                _RECAP_RENDER_NAME,
            ),
        )
        pdf_path = workspace / _RECAP_PDF
        _write_recap(workspace, body)

        result = _run(workspace, [sys.executable, _RECAP_GENERATOR])

        assert result.returncode == 0, (
            "present bundled generate_recap_pdf.py must exit 0, got "
            f"returncode={result.returncode}; stderr={result.stderr!r}"
        )
        assert "PDF generated:" in result.stdout, (
            "present bundled generator must announce 'PDF generated:'; "
            f"stdout={result.stdout!r}"
        )
        assert pdf_path.exists() and pdf_path.stat().st_size > 0, (
            "present bundled generator must write a non-empty "
            f"docs/bootcamp_recap.pdf; stderr={result.stderr!r}"
        )

    @pytest.mark.skipif(not _fpdf_available(), reason="fpdf2 not installed")
    def test_step_0b_prefers_bundled_generator_first(self) -> None:
        """Step 0b uses generate_recap_pdf.py first; the inline fallback is unused."""
        workspace = _new_workspace()
        _materialize_scripts(
            workspace,
            (
                _RECAP_GENERATOR_NAME,
                _RECAP_GENERATOR_INLINE_NAME,
                _RECAP_RENDER_NAME,
            ),
        )
        _write_recap(
            workspace,
            "# Senzing Bootcamp Recap\n\n## Module 1: Business Problem\n\n"
            "### Actions Taken\n- defined the problem\n",
        )

        producer_index, file_not_found, output = _run_step_0b(workspace)

        assert not file_not_found, f"unexpected file-not-found error; output={output!r}"
        assert producer_index == 0, (
            "Step 0b must produce the recap PDF via the bundled "
            "generate_recap_pdf.py (index 0), preferring it over the inline "
            f"fallback; got producer_index={producer_index}; output={output!r}"
        )
        assert (workspace / _RECAP_PDF).exists(), (
            f"expected docs/bootcamp_recap.pdf to be rendered; output={output!r}"
        )


# ---------------------------------------------------------------------------
# Preservation — present generic step executes its own behavior (Req 3.2)
# ---------------------------------------------------------------------------


class TestPresentGenericStepPreservation:
    """Preservation — a present bundled step executes unchanged (no file-not-found).

    **Validates: Requirements 3.2**

    A bootcamp/onboarding step shelling out to a present
    ``senzing-bootcamp/scripts/<name>.py`` runs that script's own logic with its
    existing output and exit code — never a file-not-found error from the
    interpreter.
    """

    def test_present_generic_step_help_executes(self) -> None:
        """The present generic step runs its own argparse (exit 0, usage text)."""
        workspace = _new_workspace()
        _materialize_scripts(workspace, (_GENERIC_STEP_NAME,))

        result = _run(workspace, [sys.executable, _GENERIC_STEP_SCRIPT, "--help"])

        blob = f"{result.stdout}\n{result.stderr}"
        assert not any(m in blob for m in _FILE_NOT_FOUND_MARKERS), (
            "present generic step must not emit a file-not-found error; "
            f"stderr={result.stderr!r}"
        )
        assert result.returncode == 0, (
            "present generic step --help must exit 0 (its own argparse runs), "
            f"got returncode={result.returncode}; stderr={result.stderr!r}"
        )
        assert _GENERIC_STEP_NAME in result.stdout, (
            "present generic step --help must print its own usage banner; "
            f"stdout={result.stdout!r}"
        )

    def test_present_generic_step_real_run_executes(self) -> None:
        """The present generic step's real run executes its own logic and exits 0."""
        workspace = _new_workspace()
        _materialize_scripts(workspace, (_GENERIC_STEP_NAME,))
        # generate_docs_index.py indexes docs/ — present and writable here.

        result = _run(workspace, [sys.executable, _GENERIC_STEP_SCRIPT])

        blob = f"{result.stdout}\n{result.stderr}"
        assert not any(m in blob for m in _FILE_NOT_FOUND_MARKERS), (
            "present generic step must not emit a file-not-found error; "
            f"stderr={result.stderr!r}"
        )
        assert result.returncode == 0, (
            "present generic step must execute its own logic and exit 0, got "
            f"returncode={result.returncode}; stderr={result.stderr!r}"
        )


# ---------------------------------------------------------------------------
# Preservation — graceful Markdown-only degradation when fpdf2 absent (Req 3.4)
# ---------------------------------------------------------------------------


class TestMarkdownOnlyDegradationPreservation:
    """Preservation — present generator degrades gracefully without fpdf2.

    **Validates: Requirements 3.4**

    When the bundled ``generate_recap_pdf.py`` is present (not the bug
    condition) but ``fpdf2`` cannot be imported, the system retains the Markdown
    recap, surfaces a ``pip install fpdf2`` hint, raises no unhandled error, and
    produces no PDF. This graceful no-PDF degradation must remain unchanged.
    """

    @given(body=st_recap_markdown())
    def test_present_generator_degrades_gracefully_without_fpdf(
        self, body: str, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """For all recap bodies, a blocked fpdf2 yields a hint and no PDF."""
        workspace = _new_workspace()
        _materialize_scripts(
            workspace,
            (
                _RECAP_GENERATOR_NAME,
                _RECAP_GENERATOR_INLINE_NAME,
                _RECAP_RENDER_NAME,
            ),
        )
        _write_recap(workspace, body)
        env = _fpdf_absent_env(tmp_path_factory.mktemp("fpdf_absent"))

        result = _run(workspace, [sys.executable, _RECAP_GENERATOR], env=env)

        blob = f"{result.stdout}\n{result.stderr}"
        assert not any(m in blob for m in _FILE_NOT_FOUND_MARKERS), (
            f"present generator must not emit a file-not-found error; blob={blob!r}"
        )
        assert "Traceback (most recent call last)" not in blob, (
            f"present generator must not raise an unhandled error; blob={blob!r}"
        )
        assert any(marker in blob for marker in _FPDF_HINT_MARKERS), (
            "present generator must surface a 'pip install fpdf2' hint when fpdf2 "
            f"is absent; blob={blob!r}"
        )
        assert result.returncode == 1, (
            "present generator must report the no-PDF outcome (exit 1) when fpdf2 "
            f"is absent, got returncode={result.returncode}"
        )
        assert (workspace / _RECAP_MD).exists(), "the Markdown recap must be retained"
        assert not (workspace / _RECAP_PDF).exists(), (
            "no PDF should be produced when fpdf2 is absent"
        )


# ---------------------------------------------------------------------------
# Preservation — onboarding never clobbers present valid scripts (Req 3.5)
# ---------------------------------------------------------------------------


class TestNoOverwritePreservation:
    """Preservation — onboarding leaves present valid scripts byte-for-byte intact.

    **Validates: Requirements 3.5**

    Running the onboarding verification/materialization (``preflight.py --fix``)
    in a workspace whose bundled scripts are already present and valid leaves
    those scripts unchanged (idempotent, no clobber).
    """

    def test_preflight_fix_does_not_overwrite_present_scripts(self) -> None:
        """preflight --fix leaves already-present valid bundled scripts unchanged."""
        workspace = _new_workspace()
        _materialize_scripts(workspace, _REQUIRED_SCRIPTS)

        before = _snapshot_scripts(workspace, _REQUIRED_SCRIPTS)

        result = _run(
            workspace,
            [sys.executable, str(_INSTALLED_PREFLIGHT), "--fix", "--json"],
        )

        # The onboarding verification must run to completion (no crash); its
        # verdict is irrelevant to the no-clobber guarantee.
        assert result.returncode in (0, 1), (
            "preflight --fix must complete without crashing, got "
            f"returncode={result.returncode}; stderr={result.stderr!r}"
        )

        after = _snapshot_scripts(workspace, _REQUIRED_SCRIPTS)
        assert before == after, (
            "onboarding verification/materialization must not overwrite "
            "already-present valid bundled scripts. Changed: "
            f"{sorted(k for k in before if before.get(k) != after.get(k))}"
        )
