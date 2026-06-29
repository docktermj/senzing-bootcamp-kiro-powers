"""Config-scan tests validating dev/test tooling is pinned and isolated.

Feature: test-suite-parallelization

Validates that ``requirements-dev.txt`` pins ``pytest-xdist`` at an exact
version (``==``) so CI runs are reproducible, and that no production script
under ``senzing-bootcamp/scripts/`` imports ``xdist``/``pytest_xdist`` — the new
dependency is test/dev tooling only and production scripts stay dependency-free.

Per the tech-stack rule (scripts/tests favor stdlib-only parsing), these
assertions read ``requirements-dev.txt`` as text and scan script sources with
regular expressions rather than importing third-party parsers.

Validates: Requirements 9.2, 9.4
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_DEV_PATH = PROJECT_ROOT / "requirements-dev.txt"
SCRIPTS_DIR = PROJECT_ROOT / "senzing-bootcamp" / "scripts"

PACKAGE_NAME = "pytest-xdist"

# Matches an exact-version pin like ``pytest-xdist==3.7.0`` tolerating
# surrounding whitespace and an optional inline comment.
EXACT_PIN_PATTERN = re.compile(
    rf"^\s*{re.escape(PACKAGE_NAME)}\s*==\s*\S+\s*(?:#.*)?$",
    re.MULTILINE,
)

# Matches an ``import xdist``/``import pytest_xdist`` or ``from xdist import ...``
# style statement in script source.
XDIST_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(?:pytest_xdist|xdist)\b",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_requirements_dev_text() -> str:
    """Read ``requirements-dev.txt`` as raw text.

    Returns:
        The full contents of ``requirements-dev.txt`` as a string.
    """
    return REQUIREMENTS_DEV_PATH.read_text(encoding="utf-8")


def production_script_paths() -> list[Path]:
    """Return the production Python scripts under ``senzing-bootcamp/scripts/``.

    Returns:
        Sorted list of ``.py`` files in the scripts directory (non-recursive,
        excluding cache artifacts).
    """
    return sorted(p for p in SCRIPTS_DIR.glob("*.py") if p.is_file())


# ===========================================================================
# Tests: dependency pinning
# Validates: Requirements 9.2, 9.4
# ===========================================================================


class TestDependencyPinning:
    """Tests verifying pytest-xdist is pinned and kept out of production scripts.

    Validates: Requirements 9.2, 9.4
    """

    def test_requirements_dev_file_exists(self):
        """The pinned dev tooling file exists at the repo root.

        **Validates: Requirements 9.2**
        """
        assert REQUIREMENTS_DEV_PATH.is_file(), (
            f"requirements-dev.txt not found at {REQUIREMENTS_DEV_PATH}"
        )

    def test_pytest_xdist_pinned_with_exact_version(self):
        """``requirements-dev.txt`` pins ``pytest-xdist`` with an exact ``==``.

        A looser specifier (``>=``, ``~=``, or an unpinned bare name) must not
        satisfy this check, since reproducible CI requires an exact version.

        **Validates: Requirements 9.2**
        """
        text = load_requirements_dev_text()
        assert EXACT_PIN_PATTERN.search(text), (
            f"Expected an exact pin '{PACKAGE_NAME}==<version>' in "
            f"{REQUIREMENTS_DEV_PATH}"
        )

    def test_no_production_script_imports_xdist(self):
        """No production script under ``scripts/`` imports xdist/pytest_xdist.

        The parallelization dependency is test/dev tooling only; production
        scripts must stay free of new runtime dependencies.

        **Validates: Requirements 9.4**
        """
        offenders: list[str] = []
        for script in production_script_paths():
            source = script.read_text(encoding="utf-8")
            if XDIST_IMPORT_PATTERN.search(source):
                offenders.append(script.name)

        assert not offenders, (
            "Production scripts must not import xdist/pytest_xdist; "
            f"offending files: {offenders}"
        )
