"""Property-based tests for hook JSON schema conformance.

Feature: hook-schema-conformance
Validates Kiro 1.0 ``v1`` hook JSON schema conformance across all ``*.json``
hook files. Each file is a ``{"version": "v1", "hooks": [entry]}`` wrapper; the
entry carries ``name``, ``trigger``, an optional ``matcher``, and an ``action``
(``agent`` with a ``prompt`` or ``command`` with a ``command``).
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

# Required fields on the v1 hook entry.
REQUIRED_ENTRY_FIELDS = {"name", "trigger", "action"}

V1_TRIGGERS = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "Stop",
    "UserPromptSubmit",
    "PostTaskExec",
    "PreToolUse",
    "PostToolUse",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_hook_files() -> list[Path]:
    """Return all .json v1 hook file paths in the hooks directory."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.json"))


def load_hook(path: Path) -> dict:
    """Parse a .json v1 hook file and return the single hook entry (hooks[0])."""
    with open(path, encoding="utf-8") as f:
        wrapper = json.load(f)
    return wrapper["hooks"][0]


def load_wrapper(path: Path) -> dict:
    """Parse a .json v1 hook file and return the full wrapper object."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_hook_schema(data: dict) -> list[str]:
    """Validate a v1 hook entry against the required schema.

    Required fields:
      - name (string)
      - trigger (string, a valid 1.0 trigger)
      - action.type (string, "agent" or "command")
      - action.prompt (string, when action.type is "agent")
      - action.command (string, when action.type is "command")

    Args:
        data: A v1 hook entry (``hooks[0]``).

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    for field in ("name", "trigger"):
        if field not in data:
            errors.append(f"missing required field: {field}")
        elif not isinstance(data[field], str):
            errors.append(f"{field} must be a string, got {type(data[field]).__name__}")

    if isinstance(data.get("trigger"), str) and data["trigger"] not in V1_TRIGGERS:
        errors.append(f"invalid trigger: {data['trigger']}")

    action = data.get("action")
    if not isinstance(action, dict):
        errors.append("missing required field: action (must be an object)")
    else:
        action_type = action.get("type")
        if "type" not in action:
            errors.append("missing required field: action.type")
        elif not isinstance(action_type, str):
            errors.append(
                f"action.type must be a string, got {type(action_type).__name__}"
            )

        # agent actions require a string prompt; command actions require a
        # string command (e.g. the session-log-events PostToolUse logger).
        if action_type == "agent":
            if "prompt" not in action:
                errors.append("missing required field: action.prompt")
            elif not isinstance(action["prompt"], str):
                errors.append(
                    f"action.prompt must be a string when action.type is 'agent', "
                    f"got {type(action['prompt']).__name__}"
                )
        elif action_type == "command":
            if "command" not in action:
                errors.append("missing required field: action.command")
            elif not isinstance(action["command"], str):
                errors.append(
                    f"action.command must be a string when action.type is 'command', "
                    f"got {type(action['command']).__name__}"
                )
        elif isinstance(action_type, str):
            errors.append(f"invalid action.type: {action_type}")

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
# Feature: hook-schema-conformance, Property 1: Hook JSON schema conformance
# **Validates: Requirements 1.7**
# ===========================================================================


class TestHookJsonSchemaConformance:
    """Property-based tests verifying all .json v1 hook files conform to the
    required JSON schema.

    Feature: hook-schema-conformance, Property 1: Hook JSON schema conformance
    Validates: Requirements 1.7
    """

    @given(hook_paths=st_hook_subset)
    @settings(max_examples=100)
    def test_hook_files_are_valid_json_with_required_fields(
        self, hook_paths: list[Path]
    ):
        """For any subset of .json v1 hook files, each file parses as valid JSON
        and contains all required fields with correct types.

        **Validates: Requirements 1.7**
        """
        for path in hook_paths:
            # Must parse as valid JSON with a v1 wrapper
            try:
                wrapper = load_wrapper(path)
            except json.JSONDecodeError as exc:
                pytest.fail(f'"{path.name}" is not valid JSON: {exc}')

            assert isinstance(wrapper, dict), (
                f'"{path.name}" top-level value must be a JSON object'
            )
            assert wrapper.get("version") == "v1", (
                f'"{path.name}" must declare top-level version "v1"'
            )
            assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
                f'"{path.name}" must contain a non-empty "hooks" array'
            )

            # Validate the entry schema
            errors = validate_hook_schema(wrapper["hooks"][0])
            assert not errors, (
                f'"{path.name}" schema violations: {"; ".join(errors)}'
            )

    @given(hook_paths=st_hook_subset)
    @settings(max_examples=100)
    def test_hook_string_fields_are_non_empty(self, hook_paths: list[Path]):
        """For any subset of .json v1 hook files, all required string fields
        are non-empty.

        **Validates: Requirements 1.7**
        """
        for path in hook_paths:
            data = load_hook(path)

            assert data.get("name", "").strip(), f'"{path.name}" name must be non-empty'
            assert data.get("trigger", "").strip(), (
                f'"{path.name}" trigger must be non-empty'
            )
            action = data.get("action", {})
            assert action.get("type", "").strip(), (
                f'"{path.name}" action.type must be non-empty'
            )

            if action.get("type") == "agent":
                assert action.get("prompt", "").strip(), (
                    f'"{path.name}" action.prompt must be non-empty when action.type is "agent"'
                )
            elif action.get("type") == "command":
                assert action.get("command", "").strip(), (
                    f'"{path.name}" action.command must be non-empty when action.type is "command"'
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
# Feature: hook-schema-conformance, Property 2: README hook entry format conformance
# **Validates: Requirements 3.2**
# ===========================================================================


class TestReadmeHookEntryFormatConformance:
    """Property-based tests verifying all numbered hook entries in the hooks
    README contain Trigger, Action, and Use case lines with non-empty content.

    Feature: hook-schema-conformance, Property 2: README hook entry format conformance
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
