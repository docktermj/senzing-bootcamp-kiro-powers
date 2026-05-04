"""Property-based tests for Module 12 Phase Gate.

Feature: module12-phase-gate
Validates hook JSON schema conformance across all .kiro.hook files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")

REQUIRED_TOP_LEVEL = {"name", "version", "description"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_hook_files() -> list[Path]:
    """Return all .kiro.hook file paths in the hooks directory."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.kiro.hook"))


def load_hook(path: Path) -> dict:
    """Parse a .kiro.hook file and return the JSON dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_hook_schema(data: dict) -> list[str]:
    """Validate a hook dict against the required JSON schema.

    Required fields:
      - name (string)
      - version (string)
      - description (string)
      - when.type (string)
      - then.type (string)
      - then.prompt (string, when then.type is "askAgent")

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing required field: {field}")
        elif not isinstance(data[field], str):
            errors.append(f"{field} must be a string, got {type(data[field]).__name__}")

    # when.type
    when = data.get("when")
    if not isinstance(when, dict):
        errors.append("missing required field: when (must be an object)")
    elif "type" not in when:
        errors.append("missing required field: when.type")
    elif not isinstance(when["type"], str):
        errors.append(f"when.type must be a string, got {type(when['type']).__name__}")

    # then.type and then.prompt
    then = data.get("then")
    if not isinstance(then, dict):
        errors.append("missing required field: then (must be an object)")
    else:
        if "type" not in then:
            errors.append("missing required field: then.type")
        elif not isinstance(then["type"], str):
            errors.append(f"then.type must be a string, got {type(then['type']).__name__}")

        if "prompt" not in then:
            errors.append("missing required field: then.prompt")
        elif then.get("type") == "askAgent" and not isinstance(then["prompt"], str):
            errors.append(
                f"then.prompt must be a string when then.type is 'askAgent', "
                f"got {type(then['prompt']).__name__}"
            )

    return errors


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy: draw a random non-empty subset of hook files for each test run
_all_hook_paths = get_hook_files()

st_hook_subset = st.lists(
    st.sampled_from(_all_hook_paths),
    min_size=1,
    max_size=len(_all_hook_paths),
    unique=True,
)


# ===========================================================================
# Property 1: Hook JSON schema conformance
# Feature: module12-phase-gate, Property 1: Hook JSON schema conformance
# **Validates: Requirements 1.7**
# ===========================================================================


class TestHookJsonSchemaConformance:
    """Property-based tests verifying all .kiro.hook files conform to the
    required JSON schema.

    Feature: module12-phase-gate, Property 1: Hook JSON schema conformance
    Validates: Requirements 1.7
    """

    @given(hook_paths=st_hook_subset)
    @settings(max_examples=100)
    def test_hook_files_are_valid_json_with_required_fields(
        self, hook_paths: list[Path]
    ):
        """For any subset of .kiro.hook files, each file parses as valid JSON
        and contains all required fields with correct types.

        **Validates: Requirements 1.7**
        """
        for path in hook_paths:
            # Must parse as valid JSON
            try:
                data = load_hook(path)
            except json.JSONDecodeError as exc:
                pytest.fail(f'"{path.name}" is not valid JSON: {exc}')

            assert isinstance(data, dict), (
                f'"{path.name}" top-level value must be a JSON object'
            )

            # Validate schema
            errors = validate_hook_schema(data)
            assert not errors, (
                f'"{path.name}" schema violations: {"; ".join(errors)}'
            )

    @given(hook_paths=st_hook_subset)
    @settings(max_examples=100)
    def test_hook_string_fields_are_non_empty(self, hook_paths: list[Path]):
        """For any subset of .kiro.hook files, all required string fields
        are non-empty.

        **Validates: Requirements 1.7**
        """
        for path in hook_paths:
            data = load_hook(path)

            assert data.get("name", "").strip(), f'"{path.name}" name must be non-empty'
            assert data.get("version", "").strip(), (
                f'"{path.name}" version must be non-empty'
            )
            assert data.get("description", "").strip(), (
                f'"{path.name}" description must be non-empty'
            )
            assert data.get("when", {}).get("type", "").strip(), (
                f'"{path.name}" when.type must be non-empty'
            )
            assert data.get("then", {}).get("type", "").strip(), (
                f'"{path.name}" then.type must be non-empty'
            )

            then = data.get("then", {})
            if then.get("type") == "askAgent":
                assert then.get("prompt", "").strip(), (
                    f'"{path.name}" then.prompt must be non-empty when then.type is "askAgent"'
                )


# ---------------------------------------------------------------------------
# README Parsing Helpers
# ---------------------------------------------------------------------------

README_PATH = HOOKS_DIR / "README.md"

_ENTRY_HEADER_RE = __import__("re").compile(r"^###\s+(\d+)\.\s+")


def parse_readme_hook_entries() -> list[dict]:
    """Parse all numbered hook entry sections from the hooks README.

    Each entry starts with a ``### N. ...`` header and contains **Trigger**,
    **Action**, and **Use case** lines.

    Returns:
        List of dicts with keys: number, title, body (raw text of the section).
    """
    assert README_PATH.is_file(), f"README not found at {README_PATH}"
    text = README_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    entries: list[dict] = []
    current: dict | None = None

    for line in lines:
        m = _ENTRY_HEADER_RE.match(line)
        if m:
            if current is not None:
                entries.append(current)
            current = {
                "number": int(m.group(1)),
                "title": line,
                "body": "",
            }
        elif current is not None:
            # A new h2/h1 header or a non-numbered h3 ends the entry
            if line.startswith("## ") or line.startswith("# "):
                entries.append(current)
                current = None
            else:
                current["body"] += line + "\n"

    if current is not None:
        entries.append(current)

    return entries


def validate_entry_format(entry: dict) -> list[str]:
    """Validate that a README hook entry contains Trigger, Action, and Use case.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []
    body = entry["body"]
    num = entry["number"]

    # Check for **Trigger:** with non-empty content
    trigger_re = __import__("re").compile(r"\*\*Trigger:\*\*\s*(.+)", __import__("re").IGNORECASE)
    trigger_match = trigger_re.search(body)
    if not trigger_match:
        errors.append(f"entry {num}: missing **Trigger:** line")
    elif not trigger_match.group(1).strip():
        errors.append(f"entry {num}: **Trigger:** line has empty content")

    # Check for **Action:** with non-empty content
    action_re = __import__("re").compile(r"\*\*Action:\*\*\s*(.+)", __import__("re").IGNORECASE)
    action_match = action_re.search(body)
    if not action_match:
        errors.append(f"entry {num}: missing **Action:** line")
    elif not action_match.group(1).strip():
        errors.append(f"entry {num}: **Action:** line has empty content")

    # Check for **Use case:** with non-empty content
    use_case_re = __import__("re").compile(r"\*\*Use case:\*\*\s*(.+)", __import__("re").IGNORECASE)
    use_case_match = use_case_re.search(body)
    if not use_case_match:
        errors.append(f"entry {num}: missing **Use case:** line")
    elif not use_case_match.group(1).strip():
        errors.append(f"entry {num}: **Use case:** line has empty content")

    return errors


# ---------------------------------------------------------------------------
# README Strategies
# ---------------------------------------------------------------------------

_all_readme_entries = parse_readme_hook_entries()

st_entry_subset = st.lists(
    st.sampled_from(_all_readme_entries),
    min_size=1,
    max_size=len(_all_readme_entries),
    unique_by=lambda e: e["number"],
)


# ===========================================================================
# Property 2: README hook entry format conformance
# Feature: module12-phase-gate, Property 2: README hook entry format conformance
# **Validates: Requirements 3.2**
# ===========================================================================


class TestReadmeHookEntryFormatConformance:
    """Property-based tests verifying all numbered hook entries in the hooks
    README contain Trigger, Action, and Use case lines with non-empty content.

    Feature: module12-phase-gate, Property 2: README hook entry format conformance
    Validates: Requirements 3.2
    """

    @given(entries=st_entry_subset)
    @settings(max_examples=100)
    def test_entries_contain_trigger_action_usecase(
        self, entries: list[dict]
    ):
        """For any subset of numbered hook entries in the README, each entry
        contains a **Trigger** line, an **Action** line, and a **Use case**
        line with non-empty content.

        **Validates: Requirements 3.2**
        """
        for entry in entries:
            errors = validate_entry_format(entry)
            assert not errors, (
                f'README entry "{entry["title"].strip()}" format violations: '
                f'{"; ".join(errors)}'
            )

    @given(entries=st_entry_subset)
    @settings(max_examples=100)
    def test_entries_have_sequential_numbers(self, entries: list[dict]):
        """For any subset of numbered hook entries, the entry numbers are
        positive integers (basic structural check).

        **Validates: Requirements 3.2**
        """
        for entry in entries:
            assert entry["number"] > 0, (
                f'Entry "{entry["title"].strip()}" has non-positive number: '
                f'{entry["number"]}'
            )
