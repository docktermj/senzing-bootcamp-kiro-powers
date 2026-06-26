"""Parallel-isolation regression test for the remediated compose-sync suite.

Feature: test-suite-parallelization (Task 5.4 — targeted isolation assertions).

Task 5.2/5.3 remediated the only flagged non-parallel-safe tests — the two
``compose --write`` tests in
``senzing-bootcamp/tests/test_compose_sync_integration.py`` — by composing into a
per-test ``tmp_path`` hooks dir instead of the shared repo hooks dir
(``senzing-bootcamp/hooks``). The two ``--write`` tests already assert in-process
that the shared hooks dir is byte-identical after a compose (see
``TestComposeSyncIntegration``).

This module is the *repo-level* regression guard for that remediation: it runs
the remediated test file in a fresh subprocess and then asserts that
``git status --porcelain senzing-bootcamp/hooks/`` is empty afterwards — i.e. the
run left **no new or modified tracked artifacts** in the shared hooks dir. That
directly proves the parallel-safe remediation leaves no shared artifacts that a
subsequent (parallel) run could trip over (Requirements 5.3, 6.2), and that the
writes land only under the isolated temp dir (Requirement 5.2).

If ``pytest-xdist`` is installed the run uses it (``-n auto``); otherwise it
falls back to a serial run. Either way the git-clean assertion validates the
no-shared-artifact invariant. If ``git`` is unavailable or the directory is not
a git work tree, the test skips gracefully.

**Validates: Requirements 5.2, 5.3, 6.2**
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo-relative paths (resolved from this file at repo-root ``tests/``).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOKS_REL = "senzing-bootcamp/hooks/"
_REMEDIATED_TEST = "senzing-bootcamp/tests/test_compose_sync_integration.py"


def _git_available() -> bool:
    """Return True when a ``git`` executable is on PATH."""
    return shutil.which("git") is not None


def _is_git_worktree() -> bool:
    """Return True when the repo root is inside a git work tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
    except (OSError, FileNotFoundError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_status_porcelain(path: str) -> str:
    """Return ``git status --porcelain`` output for *path* (repo-root cwd)."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", path],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"git status failed (exit {result.returncode}).\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result.stdout


def _xdist_available() -> bool:
    """Return True when the pytest-xdist plugin is importable."""
    try:
        import xdist  # noqa: F401
    except ImportError:
        return False
    return True


def _run_remediated_suite() -> subprocess.CompletedProcess[str]:
    """Run the remediated compose-sync test file in a fresh subprocess.

    Uses ``-n auto --dist loadgroup`` when pytest-xdist is installed (so the
    serial scheduling group is honored) and falls back to a serial run
    otherwise. ``-p no:cacheprovider`` keeps the run from writing a
    ``.pytest_cache`` artifact.

    Returns:
        The completed subprocess result.
    """
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        _REMEDIATED_TEST,
        "-p",
        "no:cacheprovider",
    ]
    if _xdist_available():
        cmd += ["-n", "auto", "--dist", "loadgroup"]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


class TestParallelIsolation:
    """Remediated file-writing tests leave no shared tracked artifacts.

    **Validates: Requirements 5.2, 5.3, 6.2**
    """

    def test_remediated_run_leaves_hooks_dir_git_clean(self) -> None:
        """Running the remediated suite must not dirty senzing-bootcamp/hooks/.

        Proves the parallel-safe remediation writes only under the isolated
        temp dir: after the run, ``git status --porcelain`` for the shared hooks
        dir is empty — no new or modified tracked artifacts (Req 5.2, 5.3, 6.2).
        """
        if not _git_available() or not _is_git_worktree():
            pytest.skip("git unavailable or not a git work tree")

        # Baseline: the shared hooks dir should already be clean. If a developer
        # has pending local edits there, skip rather than false-fail — this
        # regression test only validates that *our run* introduces no changes.
        before = _git_status_porcelain(_HOOKS_REL)
        if before.strip():
            pytest.skip(
                "senzing-bootcamp/hooks/ has pre-existing local changes; "
                "cannot isolate this run's effect"
            )

        result = _run_remediated_suite()
        assert result.returncode == 0, (
            "remediated compose-sync suite must pass.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        after = _git_status_porcelain(_HOOKS_REL)
        assert after.strip() == "", (
            "running the remediated suite must leave the shared hooks dir "
            f"({_HOOKS_REL}) git-clean — no shared artifacts. Found:\n{after}"
        )
