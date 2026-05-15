"""Unit tests for Module 3 Default-On file content changes.

Validates that Module 3 (System Verification) is correctly configured as
default-on (opt-out) across all layers: configuration, steering, manifest,
and documentation.

Feature: module3-default-on
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_POWER_MD: Path = _BASE_DIR / "POWER.md"
_MODULE_DEPS: Path = _BASE_DIR / "config" / "module-dependencies.yaml"
_MODULE_PREREQS: Path = _BASE_DIR / "steering" / "module-prerequisites.md"
_DOCS_MODULES_README: Path = _BASE_DIR / "docs" / "modules" / "README.md"
_MODULE_FLOW: Path = _BASE_DIR / "docs" / "diagrams" / "module-flow.md"
_STEERING_MODULE3: Path = _BASE_DIR / "steering" / "module-03-system-verification.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Read a file as UTF-8 text.

    Args:
        path: Path to the file.

    Returns:
        Full text content of the file.
    """
    return path.read_text(encoding="utf-8")


def _read_module_deps() -> dict:
    """Read and parse the module-dependencies.yaml file.

    Returns:
        Parsed YAML content as a dictionary.
    """
    return yaml.safe_load(_MODULE_DEPS.read_text(encoding="utf-8"))


def _find_module3_table_row(content: str) -> str | None:
    """Find the Module 3 row in a markdown table.

    Looks for a table row containing '| 3' followed by content.

    Args:
        content: Markdown text containing a table.

    Returns:
        The matched table row or None if not found.
    """
    for line in content.splitlines():
        if re.match(r"\|\s*3\s*\|", line):
            return line
    return None


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestModule3DefaultOnUnit:
    """Unit tests for the concrete file content changes making Module 3 default-on.

    Validates that all files across configuration, steering, manifest, and
    documentation layers correctly reflect Module 3 as a default-on module
    without the "(Optional)" qualifier.
    """

    def test_power_md_module_table_no_optional(self) -> None:
        """POWER.md module table row for Module 3 does not contain '(Optional)'.

        Validates: Requirements 2, 3
        """
        content = _read_text(_POWER_MD)

        # Find the Bootcamp Modules table section
        row = _find_module3_table_row(content)
        assert row is not None, (
            "POWER.md should contain a table row for Module 3"
        )
        assert "(Optional)" not in row, (
            f"POWER.md Module 3 table row should not contain '(Optional)', "
            f"got: {row}"
        )

    def test_power_md_steering_list_no_optional(self) -> None:
        """POWER.md steering file list entry for Module 3 does not contain '(Optional)'.

        Validates: Requirements 2, 3
        """
        content = _read_text(_POWER_MD)

        # Find the steering file list entry for module-03
        module3_entries = [
            line for line in content.splitlines()
            if "module-03-system-verification.md" in line
        ]
        assert len(module3_entries) > 0, (
            "POWER.md should contain a steering file list entry for "
            "module-03-system-verification.md"
        )
        for entry in module3_entries:
            assert "(Optional)" not in entry, (
                f"POWER.md steering list entry for Module 3 should not "
                f"contain '(Optional)', got: {entry}"
            )

    def test_module_dependencies_soft_requires(self) -> None:
        """module-dependencies.yaml Module 4 has soft_requires: [3].

        Validates: Requirements 6, 9
        """
        deps = _read_module_deps()
        module_4 = deps["modules"][4]

        assert "soft_requires" in module_4, (
            "Module 4 should have a 'soft_requires' field in "
            "module-dependencies.yaml"
        )
        assert 3 in module_4["soft_requires"], (
            f"Module 4 soft_requires should include 3, "
            f"got: {module_4['soft_requires']}"
        )

    def test_gate_3_4_explicitly_skipped(self) -> None:
        """Gate 3→4 text references 'explicitly skipped'.

        Validates: Requirements 5, 9
        """
        deps = _read_module_deps()
        gate_3_4 = deps["gates"]["3->4"]
        requires_text = " ".join(gate_3_4["requires"]).lower()

        assert "explicitly skipped" in requires_text, (
            f"Gate 3->4 should reference 'explicitly skipped', "
            f"got: {gate_3_4['requires']}"
        )

    def test_module_prerequisites_module4_mentions_module3(self) -> None:
        """module-prerequisites.md Module 4 row mentions Module 3.

        Validates: Requirements 5, 6
        """
        content = _read_text(_MODULE_PREREQS)

        # Find the Module 4 row in the Quick Reference table
        module4_rows = [
            line for line in content.splitlines()
            if "4" in line and "Data Collection" in line
        ]
        assert len(module4_rows) > 0, (
            "module-prerequisites.md should contain a row for Module 4 "
            "(Data Collection)"
        )

        # At least one Module 4 row should mention Module 3
        mentions_module3 = any(
            "Module 3" in row or "module 3" in row.lower()
            for row in module4_rows
        )
        assert mentions_module3, (
            f"Module 4 row in module-prerequisites.md should mention "
            f"Module 3, got: {module4_rows}"
        )

    def test_docs_modules_readme_no_optional(self) -> None:
        """docs/modules/README.md Module 3 heading does not contain '(Optional)'.

        Validates: Requirements 2, 8
        """
        content = _read_text(_DOCS_MODULES_README)

        # Find the Module 3 heading
        module3_headings = [
            line for line in content.splitlines()
            if "Module 3" in line and "System Verification" in line
            and line.strip().startswith("#")
        ]
        assert len(module3_headings) > 0, (
            "docs/modules/README.md should contain a heading for "
            "Module 3: System Verification"
        )
        for heading in module3_headings:
            assert "(Optional)" not in heading, (
                f"docs/modules/README.md Module 3 heading should not "
                f"contain '(Optional)', got: {heading}"
            )

    def test_module_flow_diagram_no_optional(self) -> None:
        """docs/diagrams/module-flow.md Module 3 box does not contain '(Optional)'.

        Validates: Requirements 2, 8
        """
        content = _read_text(_MODULE_FLOW)

        # Find lines referencing Module 3 in the diagram
        module3_lines = [
            line for line in content.splitlines()
            if "MODULE 3" in line or "Module 3" in line
        ]
        assert len(module3_lines) > 0, (
            "docs/diagrams/module-flow.md should contain references to Module 3"
        )
        for line in module3_lines:
            assert "(Optional)" not in line, (
                f"docs/diagrams/module-flow.md Module 3 reference should not "
                f"contain '(Optional)', got: {line}"
            )

    def test_steering_file_has_opt_out_gate(self) -> None:
        """Module 3 steering file contains opt-out gate section with trigger phrases.

        Validates: Requirements 1, 4
        """
        content = _read_text(_STEERING_MODULE3)

        # Check for opt-out gate section
        assert "Opt-Out Gate" in content, (
            "Module 3 steering file should contain an 'Opt-Out Gate' section"
        )

        # Check for trigger phrases
        trigger_phrases = [
            "skip verification",
            "I've already verified",
            "skip module 3",
        ]
        for phrase in trigger_phrases:
            assert phrase in content, (
                f"Module 3 steering file opt-out gate should contain "
                f"trigger phrase '{phrase}'"
            )
