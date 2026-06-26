"""Config-scan tests validating the pytest configuration in ``pyproject.toml``.

Feature: test-suite-parallelization

Validates that the root ``pyproject.toml`` declares a ``[tool.pytest.ini_options]``
section that sets the two discovery roots, preserves today's ``-v --tb=short``
output behavior, enables strict markers, and registers the ``slow``/``property``/
``serial`` marker taxonomy. Also asserts ``-n`` is absent from ``addopts`` —
encoding the serial-by-default design decision (parallelism is opted into
explicitly by CI and developers, never baked into the shared config).

Parsing uses ``tomllib`` (stdlib, Python 3.11+), consistent with the repo's
stdlib-only parsing convention.

Validates: Requirements 2.1, 2.3, 2.5, 3.1, 3.2
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

EXPECTED_TESTPATHS = ["senzing-bootcamp/tests", "tests"]
EXPECTED_ADDOPTS_TOKENS = ("-v", "--tb=short", "--strict-markers")
EXPECTED_MARKERS = ("slow", "property", "serial")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_pytest_config() -> dict:
    """Parse ``pyproject.toml`` and return the ``[tool.pytest.ini_options]`` table.

    Returns:
        The ``tool.pytest.ini_options`` mapping, or an empty dict when absent.
    """
    with PYPROJECT_PATH.open("rb") as handle:
        data = tomllib.load(handle)
    return data.get("tool", {}).get("pytest", {}).get("ini_options", {})


def marker_names(markers: list[str]) -> set[str]:
    """Extract the bare marker names from ``"name: description"`` entries.

    Args:
        markers: The raw ``markers`` list from the pytest config.

    Returns:
        A set of marker names (the token before the first colon).
    """
    return {entry.split(":", 1)[0].strip() for entry in markers}


# ===========================================================================
# Tests: pytest configuration in pyproject.toml
# Validates: Requirements 2.1, 2.3, 2.5, 3.1, 3.2
# ===========================================================================


class TestPytestConfig:
    """Tests verifying the ``[tool.pytest.ini_options]`` section is correct.

    Validates: Requirements 2.1, 2.3, 2.5, 3.1, 3.2
    """

    def test_pyproject_file_exists(self):
        """The root ``pyproject.toml`` exists at the expected path.

        **Validates: Requirements 2.1**
        """
        assert PYPROJECT_PATH.is_file(), (
            f"pyproject.toml not found at {PYPROJECT_PATH}"
        )

    def test_pytest_ini_options_section_exists(self):
        """A ``[tool.pytest.ini_options]`` section is present and non-empty.

        **Validates: Requirements 2.1**
        """
        config = load_pytest_config()
        assert config, (
            "Expected a [tool.pytest.ini_options] section in pyproject.toml"
        )

    def test_testpaths_are_the_two_roots(self):
        """``testpaths`` equals the two discovery roots, in order.

        **Validates: Requirements 2.3**
        """
        config = load_pytest_config()
        assert config.get("testpaths") == EXPECTED_TESTPATHS, (
            f"Expected testpaths == {EXPECTED_TESTPATHS}, "
            f"got {config.get('testpaths')!r}"
        )

    def test_addopts_preserves_output_and_strict_markers(self):
        """``addopts`` contains ``-v``, ``--tb=short``, and ``--strict-markers``.

        Preserves today's output behavior (Req 2.5) and enables strict markers
        (Req 3.2).

        **Validates: Requirements 2.5, 3.2**
        """
        config = load_pytest_config()
        addopts = config.get("addopts", "")
        for token in EXPECTED_ADDOPTS_TOKENS:
            assert token in addopts, (
                f"Expected addopts to contain '{token}'. Got: {addopts!r}"
            )

    def test_markers_register_taxonomy(self):
        """``markers`` registers ``slow``, ``property``, and ``serial``.

        **Validates: Requirements 3.1**
        """
        config = load_pytest_config()
        names = marker_names(config.get("markers", []))
        for marker in EXPECTED_MARKERS:
            assert marker in names, (
                f"Expected marker '{marker}' to be registered. Got: {sorted(names)}"
            )

    def test_addopts_excludes_n_flag(self):
        """``addopts`` does NOT contain ``-n`` (serial-by-default design decision).

        Parallelism is opted into explicitly by CI and developers, never baked
        into the shared config, so local debugging keeps clean serial output.

        **Validates: Requirements 2.5**
        """
        config = load_pytest_config()
        tokens = config.get("addopts", "").split()
        assert "-n" not in tokens, (
            f"addopts must not contain '-n' (serial-by-default). Got: {tokens}"
        )
        assert not any(token.startswith("-n") for token in tokens), (
            f"addopts must not contain any '-n<count>' form. Got: {tokens}"
        )


# ===========================================================================
# Tests: strict-marker collection behaviour
# Validates: Requirements 3.3, 3.5
# ===========================================================================

import subprocess
import sys
import textwrap

# Both discovery roots, resolved against the project root.
_COLLECT_ROOTS = [str(PROJECT_ROOT / "senzing-bootcamp" / "tests"), str(PROJECT_ROOT / "tests")]


class TestStrictMarkerCollection:
    """A strict-markers collection pass over both roots must succeed, and an
    unregistered marker must make collection fail.

    These exercise the configured ``--strict-markers`` behaviour end-to-end by
    invoking pytest in a subprocess (so the parent run is unaffected).

    Validates: Requirements 3.3, 3.5
    """

    def test_collection_over_both_roots_is_clean(self):
        """``--collect-only`` over both roots exits cleanly under strict markers.

        Proves every in-use marker across the whole suite is registered, so
        strict-marker enforcement does not error collection (Req 3.5). Runs the
        real configured invocation (``addopts`` already carries
        ``--strict-markers``) from the project root.

        **Validates: Requirements 3.5**
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *_COLLECT_ROOTS,
                "--collect-only",
                "-q",
                "--strict-markers",
                "-p",
                "no:cacheprovider",
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            "Strict-marker collection over both roots should exit 0, but it "
            f"failed (exit {result.returncode}).\n"
            f"STDOUT tail:\n{result.stdout[-2000:]}\n"
            f"STDERR tail:\n{result.stderr[-2000:]}"
        )

    def test_unregistered_marker_fails_collection(self, tmp_path):
        """A throwaway test using an unregistered marker fails strict collection.

        Writes a tiny test file marked with ``@pytest.mark.bogus_unregistered_marker``
        into ``tmp_path`` and collects it under ``--strict-markers`` from inside
        ``tmp_path`` (so no repo config registers the marker). Collection must
        exit non-zero and name the offending marker (Req 3.3).

        **Validates: Requirements 3.3**
        """
        bogus_marker = "bogus_unregistered_marker"
        test_file = tmp_path / "test_bogus_marker.py"
        test_file.write_text(
            textwrap.dedent(
                f"""\
                import pytest


                @pytest.mark.{bogus_marker}
                def test_placeholder():
                    assert True
                """
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "--strict-markers",
                "--collect-only",
                "-p",
                "no:cacheprovider",
            ],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, (
            "Collection under --strict-markers should FAIL for an unregistered "
            f"marker, but it exited 0.\nSTDOUT:\n{result.stdout}"
        )
        combined = result.stdout + result.stderr
        assert bogus_marker in combined, (
            "Strict-marker failure should name the unregistered marker "
            f"'{bogus_marker}'.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
