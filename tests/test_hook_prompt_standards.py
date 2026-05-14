"""Test suite for validating hook prompt standards.

Parses every .kiro.hook file and validates JSON structure, required fields,
prompt quality patterns, and registry synchronization.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
REGISTRY_PATH = Path("senzing-bootcamp/steering/hook-registry.md")

EXPECTED_HOOK_COUNT = 24

VALID_EVENT_TYPES = {
    "promptSubmit",
    "preToolUse",
    "postToolUse",
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "agentStop",
    "userTriggered",
    "postTaskExecution",
    "preTaskExecution",
}

REQUIRED_FIELDS = [
    "name",
    "version",
    "description",
    "when.type",
    "then.type",
    "then.prompt",
]

FILE_EVENT_TYPES = {"fileEdited", "fileCreated", "fileDeleted"}
TOOL_EVENT_TYPES = {"preToolUse", "postToolUse"}
PASS_THROUGH_EVENT_TYPES = {"preToolUse", "promptSubmit"}
EXEMPT_FROM_CLOSING_QUESTION = {"agentStop", "userTriggered"}

# ---------------------------------------------------------------------------
# Prompt pattern constants
# ---------------------------------------------------------------------------

SILENT_PROCESSING_PATTERNS = [
    r"produce no output at all",
    r"do nothing",
    r"do not acknowledge.*do not explain.*do not print",
    r"policy:\s*pass",
]

CLOSING_QUESTION_PATTERNS = [
    r"what would you like to do",
    r"what do you want to do next",
    r"would you like to continue",
    r"what.*next",
    r"would you like to",
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RegistryEntry:
    """A single hook entry parsed from hook-registry.md."""

    id: str
    name: str
    description: str


# ---------------------------------------------------------------------------
# Hook file loading utilities
# ---------------------------------------------------------------------------

def get_hook_files() -> list[Path]:
    """Return all .kiro.hook file paths in the hooks directory."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.kiro.hook"))


def load_hook_files() -> list[tuple[str, dict]]:
    """Load all .kiro.hook files from the hooks directory.

    Returns:
        List of (filename, parsed_json_dict) tuples.
    """
    results = []
    for path in get_hook_files():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        results.append((path.name, data))
    return results


# ---------------------------------------------------------------------------
# Registry parser
# ---------------------------------------------------------------------------

def parse_registry(registry_path: Path = REGISTRY_PATH) -> list[RegistryEntry]:
    """Parse hook-registry.md and extract hook entries.

    Extracts id from ``- id: `{id}` `` lines,
    name from ``- name: `{name}` `` lines,
    description from ``- description: `{description}` `` lines.

    Returns:
        List of RegistryEntry objects.
    """
    assert registry_path.is_file(), f"Hook registry not found at {registry_path}"
    text = registry_path.read_text(encoding="utf-8")

    entries: list[RegistryEntry] = []
    current_id = None
    current_name = None
    current_desc = None

    for line in text.splitlines():
        id_match = re.match(r"^- id:\s*`([^`]+)`", line)
        if id_match:
            current_id = id_match.group(1)

        name_match = re.match(r"^- name:\s*`([^`]+)`", line)
        if name_match:
            current_name = name_match.group(1)

        desc_match = re.match(r"^- description:\s*`([^`]+)`", line)
        if desc_match:
            current_desc = desc_match.group(1)

        if current_id and current_name and current_desc:
            entries.append(RegistryEntry(
                id=current_id,
                name=current_name,
                description=current_desc,
            ))
            current_id = current_name = current_desc = None

    return entries


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_required_fields(hook_data: dict) -> list[str]:
    """Check that all REQUIRED_FIELDS are present using dot-notation traversal.

    Returns:
        List of missing field names (empty if all present).
    """
    missing = []
    for field in REQUIRED_FIELDS:
        parts = field.split(".")
        obj = hook_data
        found = True
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                found = False
                break
        if not found:
            missing.append(field)
    return missing


def validate_conditional_fields(hook_data: dict) -> list[str]:
    """Check conditional fields based on event type.

    - File events: when.patterns must be a non-empty list
    - Tool events: when.toolTypes must be a non-empty list

    Returns:
        List of validation error messages (empty if all valid).
    """
    errors = []
    when = hook_data.get("when", {})
    event_type = when.get("type", "")

    if event_type in FILE_EVENT_TYPES:
        patterns = when.get("patterns")
        if not patterns or not isinstance(patterns, list) or len(patterns) == 0:
            errors.append(
                f'event type "{event_type}" requires non-empty when.patterns'
            )

    if event_type in TOOL_EVENT_TYPES:
        tool_types = when.get("toolTypes")
        if not tool_types or not isinstance(tool_types, list) or len(tool_types) == 0:
            errors.append(
                f'event type "{event_type}" requires non-empty when.toolTypes'
            )

    return errors


def has_silent_processing(prompt: str) -> bool:
    """Return True if the prompt contains a silent-processing instruction."""
    for pattern in SILENT_PROCESSING_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


def find_closing_question(prompt: str) -> str | None:
    """Return the matched closing-question phrase, or None if not found."""
    for pattern in CLOSING_QUESTION_PATTERNS:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_hooks() -> list[tuple[str, dict]]:
    """Return (filename, parsed_data) for every .kiro.hook file."""
    return load_hook_files()


@pytest.fixture
def registry_entries() -> list[RegistryEntry]:
    """Return parsed registry entries from hook-registry.md."""
    return parse_registry()


# ---------------------------------------------------------------------------
# Parameterization helpers
# ---------------------------------------------------------------------------

_hook_files = get_hook_files()
_hook_data = load_hook_files()
_hook_ids = [name for name, _ in _hook_data]


# ===========================================================================
# Task 2: JSON Structure Validation (Requirement 1)
# ===========================================================================

class TestJsonStructure:
    """Validate JSON structure and required fields for all hook files."""

    @pytest.mark.parametrize("hook_path", _hook_files, ids=[p.name for p in _hook_files])
    def test_valid_json(self, hook_path: Path):
        """Each hook file parses as valid JSON (Req 1.1)."""
        try:
            with open(hook_path, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f'"{hook_path.name}" is not valid JSON: {exc}')

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_required_fields_present(self, filename: str, data: dict):
        """Each hook has all required fields (Req 1.2)."""
        missing = validate_required_fields(data)
        assert not missing, (
            f'"{filename}" missing required field(s): {", ".join(missing)}'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_conditional_fields_file_events(self, filename: str, data: dict):
        """File-event hooks have non-empty when.patterns (Req 1.3)."""
        event_type = data.get("when", {}).get("type", "")
        if event_type not in FILE_EVENT_TYPES:
            pytest.skip("Not a file event hook")
        patterns = data.get("when", {}).get("patterns")
        assert patterns and isinstance(patterns, list) and len(patterns) > 0, (
            f'"{filename}" with event type "{event_type}" missing required field: when.patterns'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_conditional_fields_tool_events(self, filename: str, data: dict):
        """Tool-event hooks have non-empty when.toolTypes (Req 1.4)."""
        event_type = data.get("when", {}).get("type", "")
        if event_type not in TOOL_EVENT_TYPES:
            pytest.skip("Not a tool event hook")
        tool_types = data.get("when", {}).get("toolTypes")
        assert tool_types and isinstance(tool_types, list) and len(tool_types) > 0, (
            f'"{filename}" with event type "{event_type}" missing required field: when.toolTypes'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_then_type_is_ask_agent(self, filename: str, data: dict):
        """Every hook's then.type is askAgent (Req 1.5)."""
        actual = data.get("then", {}).get("type")
        assert actual == "askAgent", (
            f'"{filename}" then.type is "{actual}", expected "askAgent"'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_prompt_minimum_length(self, filename: str, data: dict):
        """Every hook's then.prompt is at least 20 characters (Req 1.6)."""
        prompt = data.get("then", {}).get("prompt", "")
        assert len(prompt) >= 20, (
            f'"{filename}" prompt is {len(prompt)} chars, minimum is 20'
        )


# ===========================================================================
# Task 3: Silent Processing & Closing Question Tests (Requirements 2, 3)
# ===========================================================================

_pass_through_hooks = [
    (name, data)
    for name, data in _hook_data
    if data.get("when", {}).get("type") in PASS_THROUGH_EVENT_TYPES
]
_pass_through_ids = [name for name, _ in _pass_through_hooks]

_non_exempt_hooks = [
    (name, data)
    for name, data in _hook_data
    if data.get("when", {}).get("type") not in EXEMPT_FROM_CLOSING_QUESTION
]
_non_exempt_ids = [name for name, _ in _non_exempt_hooks]


class TestSilentProcessing:
    """Validate pass-through hooks contain silent-processing instructions."""

    @pytest.mark.parametrize(
        "filename,data", _pass_through_hooks, ids=_pass_through_ids
    )
    def test_pass_through_hooks_have_silent_instruction(
        self, filename: str, data: dict
    ):
        """Pass-through hooks must contain a silent-processing phrase (Req 2.1, 2.2)."""
        prompt = data.get("then", {}).get("prompt", "")
        assert has_silent_processing(prompt), (
            f'"{filename}" (pass-through hook) missing silent-processing instruction in prompt'
        )


class TestNoInlineClosingQuestions:
    """Validate non-exempt hooks do not contain inline closing questions."""

    @pytest.mark.parametrize(
        "filename,data", _non_exempt_hooks, ids=_non_exempt_ids
    )
    def test_non_exempt_hooks_no_closing_questions(
        self, filename: str, data: dict
    ):
        """Non-exempt hooks must not contain closing questions (Req 3.1, 3.2, 3.3)."""
        prompt = data.get("then", {}).get("prompt", "")
        matched = find_closing_question(prompt)
        assert matched is None, (
            f'"{filename}" contains inline closing question: "{matched}"'
        )


# ===========================================================================
# Task 4: Registry Synchronization Tests (Requirement 4)
# ===========================================================================

_registry_entries = parse_registry()
_registry_by_id = {e.id: e for e in _registry_entries}
_hook_data_by_id = {name.replace(".kiro.hook", ""): data for name, data in _hook_data}
_file_ids = sorted(_hook_data_by_id.keys())
_registry_ids = sorted(_registry_by_id.keys())

# Hooks present in both registry and files
_common_ids = sorted(set(_file_ids) & set(_registry_ids))


class TestRegistrySync:
    """Validate hook files and registry entries are in sync."""

    @pytest.mark.parametrize("reg_id", _registry_ids)
    def test_registry_entry_has_hook_file(self, reg_id: str):
        """Every registry id has a corresponding .kiro.hook file (Req 4.2)."""
        assert reg_id in _hook_data_by_id, (
            f'Registry entry "{reg_id}" has no corresponding file "{reg_id}.kiro.hook"'
        )

    @pytest.mark.parametrize("file_id", _file_ids)
    def test_hook_file_has_registry_entry(self, file_id: str):
        """Every hook file has a corresponding registry entry (Req 4.3)."""
        assert file_id in _registry_by_id, (
            f'Hook file "{file_id}.kiro.hook" has no corresponding entry in hook-registry.md'
        )

    @pytest.mark.parametrize("hook_id", _common_ids)
    def test_name_matches(self, hook_id: str):
        """Name field matches between file and registry (Req 4.4)."""
        file_name = _hook_data_by_id[hook_id]["name"]
        registry_name = _registry_by_id[hook_id].name
        assert file_name == registry_name, (
            f'"{hook_id}" name mismatch — file: "{file_name}", registry: "{registry_name}"'
        )

    @pytest.mark.parametrize("hook_id", _common_ids)
    def test_description_matches(self, hook_id: str):
        """Description field matches between file and registry (Req 4.5)."""
        file_desc = _hook_data_by_id[hook_id]["description"]
        registry_desc = _registry_by_id[hook_id].description
        assert file_desc == registry_desc, (
            f'"{hook_id}" description mismatch — file: "{file_desc}", registry: "{registry_desc}"'
        )


# ===========================================================================
# Task 5: Hook Count & Event Type Validation (Requirements 5, 7)
# ===========================================================================

class TestHookCount:
    """Validate the expected number of hooks."""

    def test_hook_file_count(self):
        """Exactly 24 .kiro.hook files exist (Req 5.1, 5.3)."""
        actual = len(get_hook_files())
        assert actual == EXPECTED_HOOK_COUNT, (
            f"Expected {EXPECTED_HOOK_COUNT} hook files, found {actual}"
        )

    def test_registry_entry_count(self):
        """Exactly 24 registry entries exist (Req 5.2, 5.3)."""

        entries = parse_registry()
        actual = len(entries)
        assert actual == EXPECTED_HOOK_COUNT, (
            f"Expected {EXPECTED_HOOK_COUNT} registry entries, found {actual}"
        )


class TestEventTypeValidation:
    """Validate event types used by hooks."""

    def test_valid_event_types_constant(self):
        """VALID_EVENT_TYPES contains all 10 expected types (Req 7.1)."""
        expected = {
            "promptSubmit",
            "preToolUse",
            "postToolUse",
            "fileEdited",
            "fileCreated",
            "fileDeleted",
            "agentStop",
            "userTriggered",
            "postTaskExecution",
            "preTaskExecution",
        }
        assert VALID_EVENT_TYPES == expected

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_all_hooks_use_valid_event_types(self, filename: str, data: dict):
        """Every hook's when.type is in VALID_EVENT_TYPES (Req 7.2)."""
        event_type = data.get("when", {}).get("type", "")
        assert event_type in VALID_EVENT_TYPES, (
            f'"{filename}" has invalid event type: "{event_type}"'
        )


# ===========================================================================
# Task 8: Example-Based Unit Tests for Real Hook Files
# ===========================================================================

class TestRealHookFiles:
    """Example-based unit tests that validate real hook file data."""

    def test_all_24_hook_files_parse_as_valid_json(self):
        """All 24 real hook files parse as valid JSON (Req 1.1)."""
        hook_files = get_hook_files()
        assert len(hook_files) == EXPECTED_HOOK_COUNT
        for path in hook_files:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{path.name} did not parse as a JSON object"

    def test_hook_file_count_is_24(self):
        """Hook file count is exactly 24 (Req 5.1)."""
        assert len(get_hook_files()) == EXPECTED_HOOK_COUNT

    def test_registry_entry_count_is_24(self):
        """Registry entry count is exactly 24 (Req 5.2)."""
        assert len(parse_registry()) == EXPECTED_HOOK_COUNT

    def test_valid_event_types_has_10_entries(self):
        """VALID_EVENT_TYPES constant contains all 10 expected event type strings (Req 7.1)."""
        expected = {
            "promptSubmit", "preToolUse", "postToolUse",
            "fileEdited", "fileCreated", "fileDeleted",
            "agentStop", "userTriggered", "postTaskExecution", "preTaskExecution",
        }
        assert VALID_EVENT_TYPES == expected
        assert len(VALID_EVENT_TYPES) == 10

    @pytest.mark.parametrize("hook_id", [
        "review-bootcamper-input",
        "enforce-file-path-policies",
    ])
    def test_real_pass_through_hooks_have_silent_processing(self, hook_id: str):
        """Real pass-through hooks contain silent-processing instructions (Req 2.1)."""
        data = _hook_data_by_id[hook_id]
        prompt = data["then"]["prompt"]
        assert has_silent_processing(prompt), (
            f'"{hook_id}" (pass-through hook) missing silent-processing instruction'
        )

    def test_real_non_exempt_hooks_no_closing_questions(self):
        """Real non-exempt hooks do not contain inline closing questions (Req 3.1, 3.2)."""
        for name, data in _hook_data:
            event_type = data.get("when", {}).get("type", "")
            if event_type in EXEMPT_FROM_CLOSING_QUESTION:
                continue
            prompt = data.get("then", {}).get("prompt", "")
            matched = find_closing_question(prompt)
            assert matched is None, (
                f'"{name}" contains inline closing question: "{matched}"'
            )

    def test_registry_names_match_file_names(self):
        """Registry names match file names for all 20 hooks (Req 4.4)."""
        for hook_id in _common_ids:
            file_name = _hook_data_by_id[hook_id]["name"]
            registry_name = _registry_by_id[hook_id].name
            assert file_name == registry_name, (
                f'"{hook_id}" name mismatch — file: "{file_name}", registry: "{registry_name}"'
            )

    def test_registry_descriptions_match_file_descriptions(self):
        """Registry descriptions match file descriptions for all 20 hooks (Req 4.5)."""
        for hook_id in _common_ids:
            file_desc = _hook_data_by_id[hook_id]["description"]
            registry_desc = _registry_by_id[hook_id].description
            assert file_desc == registry_desc, (
                f'"{hook_id}" description mismatch — file: "{file_desc}", registry: "{registry_desc}"'
            )
