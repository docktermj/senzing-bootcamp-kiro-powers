"""Shared fixtures for repo-level (hook) tests."""

import os
import sys
from pathlib import Path

import hypothesis_profiles
import pytest

# ---------------------------------------------------------------------------
# Hypothesis profile — deterministic under variable CI/local machine load
# ---------------------------------------------------------------------------
# Profiles are defined once in the repo-root ``hypothesis_profiles`` module so
# both collection roots (``senzing-bootcamp/tests/`` and ``tests/``) stay in
# sync. The active profile is selected from the ``HYPOTHESIS_PROFILE``
# environment variable; every profile disables the deadline and suppresses the
# ``too_slow`` health check so the suite stays deterministic under variable
# machine load. Per-test ``@settings`` still take precedence and assertions are
# unaffected. The repo root is already on ``sys.path`` via the
# ``_PROJECT_ROOT`` insert below.
hypothesis_profiles.load_active_profile()

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
    """Snap cwd back to the project root before each test.

    Process-local and therefore correct under pytest-xdist: each xdist worker
    is a separate OS process with its own cwd, so this autouse fixture runs
    independently inside every worker and preserves per-test cwd isolation
    without modification. No xdist-specific change is needed.
    """
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


# ---------------------------------------------------------------------------
# Auto-tag Hypothesis property tests with the registered ``property`` marker.
# ---------------------------------------------------------------------------
# Hypothesis wraps every ``@given`` test and sets ``is_hypothesis_test = True``
# on the resulting callable. Detecting that attribute at collection time lets
# the registered ``property`` marker (see ``[tool.pytest.ini_options]`` in
# pyproject.toml) be applied to every property test across this root without
# per-file decorator churn, so selective runs stay meaningful:
#   pytest -m property              # only Hypothesis tests
#   pytest -m "not property"        # skip generative tests for a quick smoke run
# This hook is conftest-local, so it only tags items collected under ``tests/``;
# the senzing-bootcamp root has an identical hook in its own conftest.


def pytest_collection_modifyitems(config, items):
    """Apply the ``property`` marker to every collected Hypothesis test."""
    for item in items:
        if getattr(getattr(item, "obj", None), "is_hypothesis_test", False):
            item.add_marker("property")
