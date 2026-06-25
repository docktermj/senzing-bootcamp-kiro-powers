"""Shared fixtures for repo-level (hook) tests."""

import os
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

# ---------------------------------------------------------------------------
# Hypothesis profile — deterministic under variable CI/local machine load
# ---------------------------------------------------------------------------
# Repo-level property tests can do per-example filesystem I/O that exceeds
# Hypothesis's default 200 ms deadline or trips the ``too_slow`` health check
# under machine load. Those are timing artifacts, not logic failures. Disable
# the deadline and suppress the timing health check so the suite is
# deterministic; per-test ``@settings`` still take precedence. Assertions are
# unaffected.
settings.register_profile(
    "bootcamp",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("bootcamp")

# ---------------------------------------------------------------------------
# Ensure the project root is the cwd for every test.
#
# Repo-level tests use relative paths like ``Path("senzing-bootcamp/hooks")``.
# When pytest collects tests from both ``senzing-bootcamp/tests/`` and
# ``tests/`` in the same run, earlier tests may change cwd (e.g. via
# ``monkeypatch.chdir``). This fixture snaps cwd back to the project root
# before each repo-level test runs.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _restore_project_root_cwd():
    """Snap cwd back to the project root before each test."""
    try:
        cwd = os.getcwd()
    except (FileNotFoundError, OSError):
        os.chdir(_PROJECT_ROOT)
        return
    if cwd != str(_PROJECT_ROOT):
        os.chdir(_PROJECT_ROOT)


# Make ``tests/`` importable so hook_test_helpers works when pytest collects
# from the repo root.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

# Make the project root importable so ``from src.query...`` works in tests.
_PROJECT_ROOT_STR = str(_PROJECT_ROOT)
if _PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT_STR)
