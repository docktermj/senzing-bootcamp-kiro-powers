"""Property-based tests for consistent error handling across steering files.

Feature: consistent-error-handling

Validates that every root module steering file contains a standard
## Error Handling section and that common-pitfalls.md has a complete
Troubleshooting by Symptom table.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
STEERING_INDEX_PATH = STEERING_DIR / "steering-index.yaml"
COMMON_PITFALLS_PATH = STEERING_DIR / "common-pitfalls.md"

REQUIRED_SYMPTOMS: set[str] = {
    "zero entities created",
    "loading hangs",
    "query returns no results",
    "SDK initialization fails",
    "database connection fails",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def load_steering_index() -> dict:
    """Parse steering-index.yaml and return the full index data.

    Returns:
        The parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If steering-index.yaml does not exist.
    """
    if not STEERING_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Steering index not found at {STEERING_INDEX_PATH}"
        )
    with open(STEERING_INDEX_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_root_path(module_entry: str | dict) -> str:
    """Resolve a module entry to its root filename.

    Args:
        module_entry: Either a plain filename string or a dict with a ``root`` key.

    Returns:
        The root steering filename for the module.
    """
    if isinstance(module_entry, str):
        return module_entry
    return module_entry["root"]


def read_section(file_path: Path, heading: str) -> str | None:
    """Extract content under a given ``##`` heading from a Markdown file.

    Reads the text between the specified ``## <heading>`` line and the next
    ``##`` heading (or end of file).

    Args:
        file_path: Path to the Markdown file.
        heading: The heading text to search for (without the ``## `` prefix).

    Returns:
        The section body text, or ``None`` if the heading is not found.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Steering file not found: {file_path}"
        )
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    target = f"## {heading}"
    start_idx: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == target:
            start_idx = i + 1
            continue
        if start_idx is not None and stripped.startswith("## "):
            return "".join(lines[start_idx:i])

    if start_idx is not None:
        return "".join(lines[start_idx:])

    return None


def parse_symptom_table(content: str) -> list[dict]:
    """Parse a Markdown pipe-delimited table into a list of row dicts.

    Skips the header row and separator row.  Each returned dict has keys
    ``symptom`` and ``diagnostic_action``. For backward compatibility,
    ``likely_cause`` and ``diagnostic_steps`` are also populated from
    the diagnostic_action column.

    Args:
        content: The raw Markdown text containing the table.

    Returns:
        A list of dicts, one per data row.
    """
    rows: list[dict] = []
    table_lines = [
        line for line in content.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]

    if len(table_lines) < 3:
        return rows

    # Skip header (index 0) and separator (index 1)
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2:
            rows.append({
                "symptom": cells[0],
                "diagnostic_action": cells[1],
                # Backward compat: map to old column names
                "likely_cause": cells[1],
                "diagnostic_steps": cells[1],
            })

    return rows


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_INDEX_DATA = load_steering_index()
_MODULE_NUMBERS = sorted(_INDEX_DATA["modules"].keys())


def st_module_number():
    """Strategy drawing from the set of module numbers in steering-index.yaml."""
    return st.sampled_from(_MODULE_NUMBERS)


def st_symptom_name():
    """Strategy drawing from the five required cross-module symptoms."""
    return st.sampled_from(sorted(REQUIRED_SYMPTOMS))


# Collect all phase sub-file paths from split modules, excluding
# files that also serve as the module root (e.g. module-01 and
# module-11 reuse the root file as a phase file).
_PHASE_SUB_FILES: list[str] = []
for _mod_num, _mod_entry in _INDEX_DATA["modules"].items():
    if isinstance(_mod_entry, dict) and "phases" in _mod_entry:
        _root = _mod_entry["root"]
        for _phase_info in _mod_entry["phases"].values():
            if _phase_info["file"] != _root:
                _PHASE_SUB_FILES.append(_phase_info["file"])


def st_phase_sub_file():
    """Strategy drawing from all phase sub-file paths in the steering index."""
    return st.sampled_from(_PHASE_SUB_FILES)


# Collect all module entries (both string and dict) for the path resolution strategy
_MODULE_ENTRIES: list[tuple[int, str | dict]] = [
    (num, entry) for num, entry in _INDEX_DATA["modules"].items()
]


def st_module_entry():
    """Strategy drawing module entries (number, entry) from the steering index."""
    return st.sampled_from(_MODULE_ENTRIES)


# ---------------------------------------------------------------------------
# Property 1: Error Handling Section Completeness
# ---------------------------------------------------------------------------


class TestProperty1ErrorHandlingSectionCompleteness:
    """Feature: consistent-error-handling, Property 1: Error Handling Section Completeness

    For any module number in the steering index, the corresponding root module
    steering file SHALL contain a ## Error Handling section that includes both
    a reference to explain_error_code and a reference to common-pitfalls.md.

    Validates: Requirements 1.1, 1.2, 2.1, 2.3, 3.1, 4.3, 7.3, 7.4, 7.5
    """

    @given(module_num=st_module_number())
    @settings(max_examples=100)
    def test_error_handling_section_exists_with_required_references(self, module_num):
        """Root module file contains ## Error Handling with explain_error_code and common-pitfalls.md."""
        module_entry = _INDEX_DATA["modules"][module_num]
        root_filename = resolve_root_path(module_entry)
        root_path = STEERING_DIR / root_filename

        section = read_section(root_path, "Error Handling")
        assert section is not None, (
            f"Module {module_num} ({root_filename}) is missing ## Error Handling section"
        )
        assert "explain_error_code" in section, (
            f"Module {module_num} ({root_filename}) ## Error Handling does not reference explain_error_code"
        )
        assert "common-pitfalls.md" in section, (
            f"Module {module_num} ({root_filename}) ## Error Handling does not reference common-pitfalls.md"
        )


# ---------------------------------------------------------------------------
# Property 2: Phase Sub-File Exclusion
# ---------------------------------------------------------------------------


class TestProperty2PhaseSubFileExclusion:
    """Feature: consistent-error-handling, Property 2: Phase Sub-File Exclusion

    For any module that has phase sub-files in the steering index, none of the
    phase sub-files SHALL contain a ## Error Handling heading.

    Validates: Requirements 1.3
    """

    @given(phase_file=st_phase_sub_file())
    @settings(max_examples=100)
    def test_phase_sub_files_do_not_contain_error_handling(
        self, phase_file
    ):
        """Phase sub-files must not contain ## Error Handling section."""
        file_path = STEERING_DIR / phase_file
        section = read_section(file_path, "Error Handling")
        assert section is None, (
            f"Phase sub-file {phase_file} should NOT contain "
            f"## Error Handling section"
        )


# ---------------------------------------------------------------------------
# Property 3: Section Conciseness
# ---------------------------------------------------------------------------


class TestProperty3SectionConciseness:
    """Feature: consistent-error-handling, Property 3: Section Conciseness

    For any module number in the steering index, the ## Error Handling section
    in the corresponding root module steering file SHALL be no more than 15
    lines of Markdown.

    Validates: Requirements 4.2
    """

    @given(module_num=st_module_number())
    @settings(max_examples=100)
    def test_error_handling_section_within_line_limit(self, module_num):
        """## Error Handling section is at most 15 lines."""
        module_entry = _INDEX_DATA["modules"][module_num]
        root_filename = resolve_root_path(module_entry)
        root_path = STEERING_DIR / root_filename

        section = read_section(root_path, "Error Handling")
        assert section is not None, (
            f"Module {module_num} ({root_filename}) "
            f"is missing ## Error Handling section"
        )
        # Count non-empty lines (strip trailing whitespace-only lines)
        lines = [line for line in section.splitlines() if line.strip()]
        assert len(lines) <= 15, (
            f"Module {module_num} ({root_filename}) "
            f"## Error Handling has {len(lines)} "
            f"non-empty lines (max 15)"
        )


# ---------------------------------------------------------------------------
# Property 4: Symptom Table Completeness
# ---------------------------------------------------------------------------


class TestProperty4SymptomTableCompleteness:
    """Feature: consistent-error-handling, Property 4: Symptom Table Completeness

    For any symptom name drawn from the set of required symptoms, the
    Troubleshooting by Symptom table in common-pitfalls.md SHALL contain a row
    whose Symptom column includes that text (case-insensitive), and that row
    SHALL have non-empty Likely Cause and Diagnostic Steps columns.

    Validates: Requirements 5.3, 5.4, 8.3, 8.4
    """

    @given(symptom=st_symptom_name())
    @settings(max_examples=100)
    def test_symptom_table_contains_required_symptom(self, symptom):
        """Symptom table has a matching row with non-empty columns."""
        section = read_section(
            COMMON_PITFALLS_PATH, "Troubleshooting by Symptom"
        )
        assert section is not None, (
            "common-pitfalls.md is missing "
            "## Troubleshooting by Symptom section"
        )
        rows = parse_symptom_table(section)
        matching = [
            r for r in rows
            if symptom.lower() in r["symptom"].lower()
        ]
        assert matching, (
            f"Symptom table has no row matching '{symptom}'"
        )
        for row in matching:
            assert row["likely_cause"].strip(), (
                f"Row for '{symptom}' has empty Likely Cause"
            )
            assert row["diagnostic_steps"].strip(), (
                f"Row for '{symptom}' has empty Diagnostic Steps"
            )


# ---------------------------------------------------------------------------
# Property 5: Module Path Resolution
# ---------------------------------------------------------------------------


class TestProperty5ModulePathResolution:
    """Feature: consistent-error-handling, Property 5: Module Path Resolution

    For any module entry in the steering index, the path resolution function
    SHALL return the entry itself when the entry is a plain string, and SHALL
    return the value of the root key when the entry is a dictionary.

    Validates: Requirements 9.2, 9.3
    """

    @given(module_entry=st_module_entry())
    @settings(max_examples=100)
    def test_resolve_root_path_returns_correct_value(self, module_entry):
        """resolve_root_path returns string directly or dict root key."""
        module_num, entry = module_entry
        result = resolve_root_path(entry)
        if isinstance(entry, str):
            assert result == entry, (
                f"Module {module_num}: expected '{entry}', got '{result}'"
            )
        else:
            assert result == entry["root"], (
                f"Module {module_num}: expected '{entry['root']}', got '{result}'"
            )


# ---------------------------------------------------------------------------
# Unit Tests: Section Ordering and Error Reporting
# ---------------------------------------------------------------------------


class TestUnitSectionOrderingAndErrorReporting:
    """Unit tests for section ordering and error reporting.

    Validates: Requirements 5.2, 9.4
    """

    def test_symptom_table_after_quick_nav_before_module_2(self):
        """## Troubleshooting by Symptom appears after Quick Navigation and before ## Module 2."""
        text = COMMON_PITFALLS_PATH.read_text(encoding="utf-8")
        lines = text.splitlines()

        quick_nav_line = None
        symptom_line = None
        module_2_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "## Quick Navigation":
                quick_nav_line = i
            elif stripped == "## Troubleshooting by Symptom":
                symptom_line = i
            elif stripped.startswith("## Module 2"):
                module_2_line = i

        assert quick_nav_line is not None, "Missing ## Quick Navigation"
        assert symptom_line is not None, (
            "Missing ## Troubleshooting by Symptom"
        )
        assert module_2_line is not None, "Missing ## Module 2 section"
        assert quick_nav_line < symptom_line < module_2_line, (
            f"Section ordering wrong: Quick Navigation "
            f"(line {quick_nav_line}), "
            f"Troubleshooting by Symptom (line {symptom_line}), "
            f"Module 2 (line {module_2_line})"
        )

    def test_missing_root_file_raises_error(self):
        """read_section raises FileNotFoundError for non-existent files."""
        fake_path = STEERING_DIR / "nonexistent-module.md"
        with pytest.raises(FileNotFoundError):
            read_section(fake_path, "Error Handling")
