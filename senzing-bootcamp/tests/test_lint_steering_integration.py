"""Integration tests for lint_steering.py.

Tests run the linter as a subprocess and verify end-to-end behavior.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "lint_steering.py"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# 13.1 Full linter run on real corpus
# ---------------------------------------------------------------------------


class TestFullLinterRun:
    """Integration: full linter run on real corpus completes and exit code
    reflects violation state."""

    def test_linter_completes_without_crash(self):
        """The linter runs to completion on the real corpus."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Should not crash (exit code 0 or 1, not 2+)
        assert result.returncode in (0, 1), \
            f"Linter crashed with exit code {result.returncode}: {result.stderr}"

    def test_output_contains_summary_line(self):
        """The linter output ends with a summary line."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert "error(s)" in result.stdout
        assert "warning(s)" in result.stdout

    def test_exit_code_reflects_violations(self):
        """Exit code is 1 when errors exist, 0 when no errors."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Parse the summary line
        summary_match = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)",
                                  result.stdout)
        assert summary_match, f"No summary line found in output: {result.stdout[-200:]}"

        error_count = int(summary_match.group(1))
        if error_count > 0:
            assert result.returncode == 1
        else:
            assert result.returncode == 0


# ---------------------------------------------------------------------------
# 13.2 Linter runs with no third-party imports
# ---------------------------------------------------------------------------


class TestNoThirdPartyImports:
    """Integration: linter runs with no third-party imports (only stdlib)."""

    def test_no_third_party_imports(self):
        """The linter script only imports from the Python standard library."""
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        # Extract all import statements
        import_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_lines.append(stripped)

        # Standard library modules used by the script
        stdlib_modules = {
            "argparse", "json", "re", "sys", "dataclasses", "pathlib",
        }

        for line in import_lines:
            # Extract module name
            if line.startswith("from "):
                module = line.split()[1].split(".")[0]
            else:
                module = line.split()[1].split(".")[0]

            assert module in stdlib_modules, \
                f"Non-stdlib import found: '{line}' (module: {module})"

    def test_script_runs_without_third_party(self):
        """The linter executes successfully using only stdlib."""
        # Run with -I flag to ignore user site-packages
        result = subprocess.run(
            [sys.executable, "-I", str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, \
            f"Script failed with -I flag: {result.stderr}"


# ---------------------------------------------------------------------------
# 13.3 Summary line format
# ---------------------------------------------------------------------------


class TestSummaryLineFormat:
    """Integration: summary line format is '{N} error(s), {M} warning(s)'."""

    def test_summary_format(self):
        """Summary line matches the expected format."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        lines = result.stdout.strip().splitlines()
        summary = lines[-1] if lines else ""

        assert re.match(r"^\d+ error\(s\), \d+ warning\(s\)$", summary), \
            f"Summary line doesn't match format: '{summary}'"
