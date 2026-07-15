"""Test suite for validating hook prompt standards.

Parses every ``*.json`` v1 hook file and validates JSON structure, required v1
entry fields, prompt quality patterns, and registry synchronization.

Each shipped hook is a ``{"version": "v1", "hooks": [entry]}`` wrapper whose
entry carries ``name``, ``trigger``, an optional ``matcher``, and an ``action``
(``agent`` with a ``prompt`` or ``command`` with a ``command``). The hook
registry lists each hook with ``- id:``, ``- name:``, ``- trigger:``, and
``- action:`` lines.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup for importing hook_test_helpers
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import parse_categories_yaml

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
STEERING_DIR = Path("senzing-bootcamp/steering")
REGISTRY_CRITICAL_PATH = STEERING_DIR / "hook-registry-critical.md"
# The single hook-registry-modules.md monolith was replaced by per-module
# registry slices (hook-registry-module-NN.md / hook-registry-module-any.md).
MODULE_SLICE_GLOB = "hook-registry-module-*.md"


def module_slice_paths() -> list[Path]:
    """Return the per-module registry slice paths in sorted order."""
    return sorted(STEERING_DIR.glob(MODULE_SLICE_GLOB))


def _expected_hook_count() -> int:
    """Derive expected hook count from unique IDs in hook-categories.yaml."""
    categories = parse_categories_yaml()
    unique_ids: set[str] = set()
    for ids in categories.values():
        unique_ids.update(ids)
    return len(unique_ids)


EXPECTED_HOOK_COUNT = _expected_hook_count()


def _expected_registry_entry_count() -> int:
    """Derive the expected number of detailed registry entries.

    The detailed registries (hook-registry-critical.md + the per-module
    hook-registry-module-*.md slices) list a hook once per category bucket it
    belongs to. A hook mapped to multiple modules in hook-categories.yaml (e.g.
    ``enforce-visualization-offers`` under modules 3, 5, 7, 8) therefore appears
    once under EACH of those module sections, so the total entry count is the
    sum of all category memberships — not the number of unique hooks. Unique-hook
    coverage is asserted separately against EXPECTED_HOOK_COUNT.
    """
    categories = parse_categories_yaml()
    return sum(len(ids) for ids in categories.values())


EXPECTED_REGISTRY_ENTRY_COUNT = _expected_registry_entry_count()

# The Kiro 1.0 trigger taxonomy.
VALID_TRIGGERS = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "Stop",
    "UserPromptSubmit",
    "PostTaskExec",
    "PreToolUse",
    "PostToolUse",
}

# Triggers that scope to a file path or tool name and require a matcher.
SCOPED_TRIGGERS = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "PreToolUse",
    "PostToolUse",
}

# Pass-through triggers whose hooks must instruct silent processing.
PASS_THROUGH_TRIGGERS = {"PreToolUse", "UserPromptSubmit"}

# Stop hooks (e.g. ask-bootcamper) legitimately end with a closing question.
EXEMPT_FROM_CLOSING_QUESTION = {"Stop"}

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
    """A single hook entry parsed from the v1 hook registry."""

    id: str
    name: str
    trigger: str


# ---------------------------------------------------------------------------
# Hook file loading utilities
# ---------------------------------------------------------------------------

def get_hook_files() -> list[Path]:
    """Return all .json v1 hook file paths in the hooks directory."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.json"))


def load_hook_files() -> list[tuple[str, dict]]:
    """Load all .json v1 hook files, returning ``(filename, entry)`` tuples.

    Returns:
        List of ``(filename, entry)`` where ``entry`` is ``hooks[0]``.
    """
    results = []
    for path in get_hook_files():
        with open(path, encoding="utf-8") as f:
            wrapper = json.load(f)
        results.append((path.name, wrapper["hooks"][0]))
    return results


# ---------------------------------------------------------------------------
# Registry parser
# ---------------------------------------------------------------------------

def parse_registry(
    registry_paths: list[Path] | None = None,
) -> list[RegistryEntry]:
    """Parse hook registry files and extract hook entries.

    Extracts ``id`` from ``- id: `{id}` `` lines, ``name`` from
    ``- name: `{name}` `` lines, and ``trigger`` from ``- trigger: `{trigger}` ``
    lines (the Kiro 1.0 registry format).

    Args:
        registry_paths: Registry file paths. Defaults to critical + module slices.

    Returns:
        List of RegistryEntry objects.
    """
    if registry_paths is None:
        registry_paths = [REGISTRY_CRITICAL_PATH, *module_slice_paths()]

    entries: list[RegistryEntry] = []

    for registry_path in registry_paths:
        assert registry_path.is_file(), f"Hook registry not found at {registry_path}"
        text = registry_path.read_text(encoding="utf-8")

        current_id = None
        current_name = None
        current_trigger = None

        for line in text.splitlines():
            id_match = re.match(r"^- id:\s*`([^`]+)`", line)
            if id_match:
                current_id = id_match.group(1)

            name_match = re.match(r"^- name:\s*`([^`]+)`", line)
            if name_match:
                current_name = name_match.group(1)

            trigger_match = re.match(r"^- trigger:\s*`([^`]+)`", line)
            if trigger_match:
                current_trigger = trigger_match.group(1)

            if current_id and current_name and current_trigger:
                entries.append(RegistryEntry(
                    id=current_id,
                    name=current_name,
                    trigger=current_trigger,
                ))
                current_id = current_name = current_trigger = None

    return entries


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def required_entry_fields(entry: dict) -> list[str]:
    """Return missing required fields for a v1 hook entry.

    Base fields are always required (name, trigger, action). ``agent`` actions
    additionally require ``action.prompt``; ``command`` actions require
    ``action.command``.

    Returns:
        List of missing dot-notation field names (empty if all present).
    """
    missing: list[str] = []
    if not entry.get("name"):
        missing.append("name")
    if not entry.get("trigger"):
        missing.append("trigger")
    action = entry.get("action")
    if not isinstance(action, dict):
        missing.append("action")
    else:
        action_type = action.get("type")
        if action_type == "agent" and not action.get("prompt"):
            missing.append("action.prompt")
        elif action_type == "command" and not action.get("command"):
            missing.append("action.command")
        elif action_type not in ("agent", "command"):
            missing.append("action.type")
    return missing


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


def _action_prompt(entry: dict) -> str:
    """Return the entry's ``action.prompt`` (empty string if absent)."""
    return entry.get("action", {}).get("prompt", "")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_hooks() -> list[tuple[str, dict]]:
    """Return (filename, entry) for every .json v1 hook file."""
    return load_hook_files()


@pytest.fixture
def registry_entries() -> list[RegistryEntry]:
    """Return parsed registry entries from the hook registry."""
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
    """Validate JSON structure and required fields for all v1 hook files."""

    @pytest.mark.parametrize("hook_path", _hook_files, ids=[p.name for p in _hook_files])
    def test_valid_json(self, hook_path: Path):
        """Each hook file parses as a valid v1 wrapper (Req 1.1)."""
        try:
            with open(hook_path, encoding="utf-8") as f:
                wrapper = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f'"{hook_path.name}" is not valid JSON: {exc}')
        assert wrapper.get("version") == "v1", (
            f'"{hook_path.name}" must declare version "v1"'
        )
        assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
            f'"{hook_path.name}" must contain a non-empty "hooks" array'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_required_fields_present(self, filename: str, data: dict):
        """Each hook has all required v1 entry fields for its action type (Req 1.2)."""
        missing = required_entry_fields(data)
        assert not missing, (
            f'"{filename}" missing required field(s): {", ".join(missing)}'
        )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_scoped_triggers_have_matcher(self, filename: str, data: dict):
        """File/tool-scoped triggers carry a matcher regex (Req 1.3, 1.4)."""
        trigger = data.get("trigger", "")
        if trigger not in SCOPED_TRIGGERS:
            pytest.skip("Not a scoped (file/tool) trigger")
        matcher = data.get("matcher")
        assert isinstance(matcher, str) and matcher, (
            f'"{filename}" with scoped trigger "{trigger}" is missing a matcher'
        )
        try:
            re.compile(matcher)
        except re.error as exc:
            pytest.fail(f'"{filename}" matcher is not a valid regex: {exc}')

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_action_type_is_agent_or_command(self, filename: str, data: dict):
        """Every hook's action.type is agent or command (Req 1.5).

        Most hooks use ``agent``; session-log-events uses ``command`` to log
        writes in-process with no agent round-trip. command actions must carry a
        command.
        """
        action = data.get("action", {})
        actual = action.get("type")
        assert actual in ("agent", "command"), (
            f'"{filename}" action.type is "{actual}", expected "agent" or "command"'
        )
        if actual == "command":
            command = action.get("command", "")
            assert isinstance(command, str) and command.strip(), (
                f'"{filename}" is a command hook but has no action.command'
            )

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_prompt_minimum_length(self, filename: str, data: dict):
        """agent prompts are >= 20 chars; command hooks carry a command (Req 1.6)."""
        action = data.get("action", {})
        if action.get("type") == "command":
            command = action.get("command", "")
            assert isinstance(command, str) and command.strip(), (
                f'"{filename}" is a command hook but has no action.command'
            )
            return
        prompt = action.get("prompt", "")
        assert len(prompt) >= 20, (
            f'"{filename}" prompt is {len(prompt)} chars, minimum is 20'
        )


# ===========================================================================
# Task 3: Silent Processing & Closing Question Tests (Requirements 2, 3)
# ===========================================================================

_pass_through_hooks = [
    (name, data)
    for name, data in _hook_data
    if data.get("trigger") in PASS_THROUGH_TRIGGERS
]
_pass_through_ids = [name for name, _ in _pass_through_hooks]

_non_exempt_hooks = [
    (name, data)
    for name, data in _hook_data
    if data.get("trigger") not in EXEMPT_FROM_CLOSING_QUESTION
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
        prompt = _action_prompt(data)
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
        prompt = _action_prompt(data)
        matched = find_closing_question(prompt)
        assert matched is None, (
            f'"{filename}" contains inline closing question: "{matched}"'
        )


# ===========================================================================
# Task 4: Registry Synchronization Tests (Requirement 4)
# ===========================================================================

_registry_entries = parse_registry()
_registry_by_id = {e.id: e for e in _registry_entries}
_hook_data_by_id = {name.replace(".json", ""): data for name, data in _hook_data}
_file_ids = sorted(_hook_data_by_id.keys())
_registry_ids = sorted(_registry_by_id.keys())

# Hooks present in both registry and files
_common_ids = sorted(set(_file_ids) & set(_registry_ids))


class TestRegistrySync:
    """Validate hook files and registry entries are in sync."""

    @pytest.mark.parametrize("reg_id", _registry_ids)
    def test_registry_entry_has_hook_file(self, reg_id: str):
        """Every registry id has a corresponding .json file (Req 4.2)."""
        assert reg_id in _hook_data_by_id, (
            f'Registry entry "{reg_id}" has no corresponding file "{reg_id}.json"'
        )

    @pytest.mark.parametrize("file_id", _file_ids)
    def test_hook_file_has_registry_entry(self, file_id: str):
        """Every hook file has a corresponding registry entry (Req 4.3)."""
        assert file_id in _registry_by_id, (
            f'Hook file "{file_id}.json" has no corresponding entry in the hook registry'
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
    def test_trigger_matches(self, hook_id: str):
        """Trigger matches between file and registry (Req 4.5)."""
        file_trigger = _hook_data_by_id[hook_id]["trigger"]
        registry_trigger = _registry_by_id[hook_id].trigger
        assert file_trigger == registry_trigger, (
            f'"{hook_id}" trigger mismatch — file: "{file_trigger}", '
            f'registry: "{registry_trigger}"'
        )


# ===========================================================================
# Task 5: Hook Count & Trigger Validation (Requirements 5, 7)
# ===========================================================================

class TestHookCount:
    """Validate the expected number of hooks."""

    def test_hook_file_count(self):
        """The number of .json hook files equals the categories count (Req 5.1, 5.3)."""
        actual = len(get_hook_files())
        assert actual == EXPECTED_HOOK_COUNT, (
            f"Expected {EXPECTED_HOOK_COUNT} hook files, found {actual}"
        )

    def test_registry_entry_count(self):
        """Registry entries cover every hook, with multi-module hooks listed per module."""
        entries = parse_registry()
        actual = len(entries)
        assert actual == EXPECTED_REGISTRY_ENTRY_COUNT, (
            f"Expected {EXPECTED_REGISTRY_ENTRY_COUNT} registry entries, found {actual}"
        )
        unique_ids = {entry.id for entry in entries}
        assert len(unique_ids) == EXPECTED_HOOK_COUNT, (
            f"Expected {EXPECTED_HOOK_COUNT} unique hooks documented, "
            f"found {len(unique_ids)}"
        )


class TestTriggerValidation:
    """Validate triggers used by hooks."""

    def test_valid_triggers_constant(self):
        """VALID_TRIGGERS contains all 8 expected 1.0 triggers (Req 7.1)."""
        expected = {
            "PostFileSave",
            "PostFileCreate",
            "PostFileDelete",
            "Stop",
            "UserPromptSubmit",
            "PostTaskExec",
            "PreToolUse",
            "PostToolUse",
        }
        assert VALID_TRIGGERS == expected

    @pytest.mark.parametrize("filename,data", _hook_data, ids=_hook_ids)
    def test_all_hooks_use_valid_triggers(self, filename: str, data: dict):
        """Every hook's trigger is in VALID_TRIGGERS (Req 7.2)."""
        trigger = data.get("trigger", "")
        assert trigger in VALID_TRIGGERS, (
            f'"{filename}" has invalid trigger: "{trigger}"'
        )


# ===========================================================================
# Task 8: Example-Based Unit Tests for Real Hook Files
# ===========================================================================

class TestRealHookFiles:
    """Example-based unit tests that validate real hook file data."""

    def test_all_hook_files_parse_as_valid_json(self):
        """All real hook files parse as valid v1 wrappers (Req 1.1)."""
        hook_files = get_hook_files()
        assert len(hook_files) == EXPECTED_HOOK_COUNT
        for path in hook_files:
            with open(path, encoding="utf-8") as f:
                wrapper = json.load(f)
            assert wrapper.get("version") == "v1", f"{path.name} must declare version v1"
            assert isinstance(wrapper.get("hooks"), list) and wrapper["hooks"], (
                f"{path.name} must contain a non-empty hooks array"
            )

    def test_hook_file_count(self):
        """Hook file count equals the categories-derived count (Req 5.1)."""
        assert len(get_hook_files()) == EXPECTED_HOOK_COUNT

    def test_registry_entry_count(self):
        """Registry entry count equals the sum of category memberships."""
        entries = parse_registry()
        assert len(entries) == EXPECTED_REGISTRY_ENTRY_COUNT
        assert len({entry.id for entry in entries}) == EXPECTED_HOOK_COUNT

    def test_valid_triggers_has_8_entries(self):
        """VALID_TRIGGERS contains all 8 expected 1.0 trigger strings (Req 7.1)."""
        assert len(VALID_TRIGGERS) == 8

    @pytest.mark.parametrize("hook_id", [
        "review-bootcamper-input",
        "write-policy-gate",
    ])
    def test_real_pass_through_hooks_have_silent_processing(self, hook_id: str):
        """Real pass-through hooks contain silent-processing instructions (Req 2.1)."""
        data = _hook_data_by_id[hook_id]
        prompt = _action_prompt(data)
        assert has_silent_processing(prompt), (
            f'"{hook_id}" (pass-through hook) missing silent-processing instruction'
        )

    def test_real_non_exempt_hooks_no_closing_questions(self):
        """Real non-exempt hooks do not contain inline closing questions (Req 3.1, 3.2)."""
        for name, data in _hook_data:
            if data.get("trigger") in EXEMPT_FROM_CLOSING_QUESTION:
                continue
            prompt = _action_prompt(data)
            matched = find_closing_question(prompt)
            assert matched is None, (
                f'"{name}" contains inline closing question: "{matched}"'
            )

    def test_registry_names_match_file_names(self):
        """Registry names match file names for all common hooks (Req 4.4)."""
        for hook_id in _common_ids:
            file_name = _hook_data_by_id[hook_id]["name"]
            registry_name = _registry_by_id[hook_id].name
            assert file_name == registry_name, (
                f'"{hook_id}" name mismatch — file: "{file_name}", registry: "{registry_name}"'
            )

    def test_registry_triggers_match_file_triggers(self):
        """Registry triggers match file triggers for all common hooks (Req 4.5)."""
        for hook_id in _common_ids:
            file_trigger = _hook_data_by_id[hook_id]["trigger"]
            registry_trigger = _registry_by_id[hook_id].trigger
            assert file_trigger == registry_trigger, (
                f'"{hook_id}" trigger mismatch — file: "{file_trigger}", '
                f'registry: "{registry_trigger}"'
            )


# ===========================================================================
# Legacy synthetic-validation helpers (imported by test_hook_prompt_properties)
# ===========================================================================
#
# ``test_hook_prompt_properties.py`` is a synthetic-logic property test that
# exercises generic field/event validators over HAND-BUILT dicts (never real
# hook files). It imports the names below. They intentionally retain the
# pre-1.0 field vocabulary (``when.type`` / ``then.type`` / ``when.patterns`` /
# ``when.toolTypes``) because the property test constructs synthetic dicts in
# that shape to validate the validators' logic — not the shipped v1 hooks. The
# real-file assertions above use the v1 helpers (VALID_TRIGGERS,
# required_entry_fields, ...); these two concerns coexist without overlap.

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

FILE_EVENT_TYPES = {"fileEdited", "fileCreated", "fileDeleted"}
TOOL_EVENT_TYPES = {"preToolUse", "postToolUse"}

REQUIRED_FIELDS = [
    "name",
    "version",
    "description",
    "when.type",
    "then.type",
    "then.prompt",
]


def validate_required_fields(hook_data: dict) -> list[str]:
    """Check that all REQUIRED_FIELDS are present using dot-notation traversal.

    Operates on a synthetic hook dict; returns the list of missing field names.
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
    """Check conditional fields based on the synthetic event type.

    File events require non-empty ``when.patterns``; tool events require
    non-empty ``when.toolTypes``. Returns a list of error messages.
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
