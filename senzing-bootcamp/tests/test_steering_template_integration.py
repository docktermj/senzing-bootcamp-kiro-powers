"""Integration tests for steering file template conformance rules.

Feature: steering-file-template
"""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LINTER_SCRIPT = REPO_ROOT / "senzing-bootcamp" / "scripts" / "lint_steering.py"


def _run_linter(*extra_args):
    """Run the linter script and return (stdout, stderr, returncode)."""
    cmd = [sys.executable, str(LINTER_SCRIPT)] + list(extra_args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# Task 12.1: Full linter run includes template conformance results
# ---------------------------------------------------------------------------


class TestFullLinterIncludesTemplateChecks:
    """Validates: Requirement 8.1"""

    def test_linter_output_includes_template_violations(self):
        """Standard linter run includes template conformance violations."""
        stdout, stderr, _ = _run_linter()
        output = stdout + stderr

        # Template rules should produce at least some output for real files
        # (phase files are missing first-read, some files missing success indicator)
        template_indicators = [
            "first-read instruction",
            "Before/After",
            "success indicator",
            "frontmatter",
        ]
        found_any = any(ind.lower() in output.lower() for ind in template_indicators)
        assert found_any, (
            "Expected template conformance output in linter run, "
            f"but found none. Output:\n{output[:500]}"
        )


# ---------------------------------------------------------------------------
# Task 12.2: --skip-template suppresses template output
# ---------------------------------------------------------------------------


class TestSkipTemplateSuppressesOutput:
    """Validates: Requirement 8.3"""

    def test_skip_template_no_template_violations(self):
        """--skip-template flag suppresses all template-related output."""
        stdout_with, _, _ = _run_linter()
        stdout_skip, _, _ = _run_linter("--skip-template")

        # Template-specific messages that should NOT appear with --skip-template
        template_messages = [
            "Module file missing",
            "Module frontmatter",
            "first-read instruction",
            "Before/After block",
            "success indicator (**Success",
            "Section '",
            "Checkpoint references step",
            "has no checkpoint instruction",
        ]

        # Filter to only lines that are template-specific
        skip_lines = stdout_skip.splitlines()
        template_lines = [
            line for line in skip_lines
            if any(msg in line for msg in template_messages)
            # Exclude existing Rule 4 checkpoint violations (not template rules)
            and "module-01-" not in line  # Rule 4 also checks checkpoints
        ]

        # The --skip-template output should have fewer template-specific lines
        # than the standard run
        with_lines = stdout_with.splitlines()
        with_template_lines = [
            line for line in with_lines
            if any(msg in line for msg in template_messages[:6])
        ]

        # With --skip-template, template-specific violations should be absent
        # (existing Rule 4 checkpoint violations may still appear)
        skip_template_specific = [
            line for line in skip_lines
            if any(msg in line for msg in [
                "Module file missing",
                "Module frontmatter",
                "first-read instruction",
                "Before/After block",
                "success indicator (**Success",
                "Section '",
            ])
        ]
        assert len(skip_template_specific) == 0, (
            f"Found template-specific violations with --skip-template:\n"
            + "\n".join(skip_template_specific[:5])
        )


# ---------------------------------------------------------------------------
# Task 12.3: Linter uses only Python standard library
# ---------------------------------------------------------------------------


class TestStdlibOnly:
    """Validates: Requirement 8.4"""

    def test_linter_uses_only_stdlib(self):
        """lint_steering.py imports only standard library modules."""
        content = LINTER_SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # Standard library modules used by the linter
        stdlib_modules = {
            "argparse", "json", "re", "sys", "os", "pathlib",
            "dataclasses", "collections", "typing", "textwrap",
            "string", "io", "functools", "itertools", "enum",
            "abc", "copy", "math", "operator", "contextlib",
        }

        non_stdlib = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    if top_module not in stdlib_modules:
                        non_stdlib.append(top_module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_module = node.module.split(".")[0]
                    if top_module not in stdlib_modules:
                        non_stdlib.append(top_module)

        assert len(non_stdlib) == 0, (
            f"lint_steering.py imports non-stdlib modules: {non_stdlib}"
        )
