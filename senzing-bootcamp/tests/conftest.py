"""Shared fixtures for senzing-bootcamp script tests."""

import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_root(tmp_path, monkeypatch):
    """Create an isolated project root and chdir into it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(scope="session")
def sample_progress_data():
    """Factory that returns valid bootcamp_progress.json content.

    Parameters are optional — sensible defaults are provided.
    """

    def _factory(
        modules_completed=None,
        current_module=1,
        language="python",
    ):
        return {
            "modules_completed": modules_completed if modules_completed is not None else [],
            "current_module": current_module,
            "language": language,
            "database_type": "sqlite",
            "data_sources": [],
            "current_step": 1,
            "step_history": {},
        }

    return _factory


@pytest.fixture()
def write_progress_file(project_root):
    """Write *data* dict as ``config/bootcamp_progress.json`` inside *project_root*."""

    def _write(data: dict):
        cfg = project_root / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "bootcamp_progress.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    return _write


@pytest.fixture()
def mock_no_color(monkeypatch):
    """Set NO_COLOR=1 so scripts disable ANSI colour codes."""
    monkeypatch.setenv("NO_COLOR", "1")
