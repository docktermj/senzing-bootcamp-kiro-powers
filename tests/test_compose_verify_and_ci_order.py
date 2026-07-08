"""Unit tests for the composer ``--verify`` gate and its CI ordering.

Feature: kiro-1-0-migration (Task 9.4).

These tests validate two acceptance criteria of the prompt composer under the
Kiro 1.0 migration:

- **Requirement 8.4** — running ``compose_hook_prompts.py --verify`` against the
  committed v1 gate hook files exits with a success code (0). Task 9.2 recomposed
  the Module 3 gate hooks byte-stably, so ``--verify`` must report no drift.
- **Requirement 8.5** — the composer drift gate
  (``compose_hook_prompts.py --verify``) runs *before* the registry sync gate
  (``sync_hook_registry.py --verify``) in the CI workflow so fragment drift is
  reported before registry drift.

Placement: this file lives in the repo-root ``tests/`` directory (not
``senzing-bootcamp/tests/``) because it validates the *real committed
artifacts* — the shipped v1 gate hook files and the actual CI workflow — per
the project rule that hook tests validating real hook files live in repo-root
``tests/``.

The ``--verify`` assertion invokes ``compose_hook_prompts.main(["--verify"])``
in-process with the working directory at the repository root, exercising the
script's default ``HOOKS_DIR = senzing-bootcamp/hooks`` (cwd-relative) exactly as
CI does. The CI-ordering assertion parses the workflow text and compares the
positions of the two invocation substrings, which stays robust against step
renames or reformatting.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# Resolve relative to this test file: repo root -> senzing-bootcamp/scripts.
# ---------------------------------------------------------------------------
_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_REPO_ROOT / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import compose_hook_prompts  # noqa: E402

# ---------------------------------------------------------------------------
# Paths and invocation substrings under test.
# ---------------------------------------------------------------------------

_WORKFLOW_PATH: Path = (
    _REPO_ROOT / ".github" / "workflows" / "validate-power.yml"
)

# Searching for the script invocation substrings (rather than exact CI lines)
# keeps the ordering assertion robust against step renames or reformatting.
_COMPOSE_VERIFY: str = "compose_hook_prompts.py --verify"
_SYNC_VERIFY: str = "sync_hook_registry.py --verify"


def _run_main_silently(argv: list[str]) -> tuple[int, str, str]:
    """Invoke ``compose_hook_prompts.main(argv)`` capturing stdout/stderr.

    Args:
        argv: Argument vector passed to ``main`` (excluding the program name).

    Returns:
        ``(exit_code, stdout, stderr)`` from the in-process invocation.
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = compose_hook_prompts.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestComposeVerifyExitsZero:
    """The composer ``--verify`` succeeds against the committed v1 gate files.

    **Validates: Requirements 8.4**
    """

    def test_verify_returns_zero_with_default_paths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``main(["--verify"])`` from the repo root exits 0 (Req 8.4).

        Runs with cwd at the repository root so the script's default
        ``HOOKS_DIR = senzing-bootcamp/hooks`` resolves to the real committed
        gate files — exactly the invocation CI performs. ``--verify`` only reads
        and compares; it never writes, so the committed files are untouched.
        """
        monkeypatch.chdir(_REPO_ROOT)
        code, out, err = _run_main_silently(["--verify"])
        assert code == 0, (
            "compose_hook_prompts.py --verify must exit 0 against the committed "
            f"v1 gate files; stderr was: {err!r}"
        )
        # The success path reports the up-to-date count on stdout.
        assert "up to date" in out

    def test_verify_returns_int_exit_code(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``main`` returns an integer exit code (contract for CLI/CI use)."""
        monkeypatch.chdir(_REPO_ROOT)
        code, _out, _err = _run_main_silently(["--verify"])
        assert isinstance(code, int)


class TestComposeBeforeSyncInCi:
    """The composer verify gate precedes the registry sync verify gate in CI.

    **Validates: Requirements 8.5**
    """

    @pytest.fixture(autouse=True)
    def _load_workflow(self) -> None:
        """Expose the CI workflow text to every test in this class."""
        assert _WORKFLOW_PATH.exists(), (
            f"CI workflow not found: {_WORKFLOW_PATH}"
        )
        self.content: str = _WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_compose_verify_present(self) -> None:
        """The workflow invokes ``compose_hook_prompts.py --verify`` (Req 8.5)."""
        assert _COMPOSE_VERIFY in self.content, (
            f"validate-power.yml must run '{_COMPOSE_VERIFY}'"
        )

    def test_sync_verify_present(self) -> None:
        """The workflow invokes ``sync_hook_registry.py --verify`` (Req 8.5)."""
        assert _SYNC_VERIFY in self.content, (
            f"validate-power.yml must run '{_SYNC_VERIFY}'"
        )

    def test_compose_verify_ordered_before_sync_verify(self) -> None:
        """Composer verify appears before registry sync verify (Req 8.5).

        The position of the composer-verify invocation must be strictly less
        than that of the sync-verify invocation so fragment drift is reported
        before registry drift.
        """
        compose_idx = self.content.find(_COMPOSE_VERIFY)
        sync_idx = self.content.find(_SYNC_VERIFY)
        assert compose_idx >= 0, f"'{_COMPOSE_VERIFY}' must appear in the workflow"
        assert sync_idx >= 0, f"'{_SYNC_VERIFY}' must appear in the workflow"
        assert compose_idx < sync_idx, (
            "validate-power.yml must run the composer verify "
            f"('{_COMPOSE_VERIFY}') before the registry sync verify "
            f"('{_SYNC_VERIFY}'): composer index {compose_idx} must be < "
            f"sync index {sync_idx}"
        )
