#!/usr/bin/env python3
"""Senzing Bootcamp - Preferences Schema Validation Utilities.

Provides the canonical schema definition, a custom minimal YAML parser
(stdlib-only), and a strict validator for config/bootcamp_preferences.yaml.

Usage:
    python preferences_utils.py
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

KNOWN_TOP_LEVEL_KEYS: set[str] = {
    "language",
    "track",
    "deployment_target",
    "cloud_provider",
    "database_type",
    "verbosity",
    "conversation_style",
    "mapping_verbosity",
    "hooks_installed",
    "pacing_overrides",
    "license",
    "license_guidance_deferred",
    "skip_graduation",
    "team_member_id",
    "scoop_installed_during_onboarding",
    "runtimes_installed_during_onboarding",
    "prerequisite_installation_deferred",
    "detail_level",
    "hardware_target",
    "production_specs",
}

CONVERSATION_STYLE_KEYS: set[str] = {
    "verbosity_preset",
    "question_framing",
    "tone",
    "pacing",
}

PRODUCTION_SPECS_KEYS: set[str] = {
    "cpu_cores",
    "ram_gb",
    "storage_type",
    "database",
}

VALID_MAPPING_VERBOSITY: tuple[str, ...] = ("verbose", "concise")
VALID_HARDWARE_TARGET: tuple[str, ...] = ("current_machine", "different_server")
VALID_VERBOSITY_PRESET: tuple[str, ...] = ("concise", "standard", "detailed", "custom")
VALID_QUESTION_FRAMING: tuple[str, ...] = ("minimal", "moderate", "full")
VALID_TONE: tuple[str, ...] = ("concise", "conversational", "detailed")
VALID_PACING: tuple[str, ...] = ("one_concept_per_turn", "grouped_concepts")


# ---------------------------------------------------------------------------
# Schema dataclass
# ---------------------------------------------------------------------------


@dataclass
class PreferencesSchema:
    """Canonical schema for bootcamp_preferences.yaml.

    Defines the expected structure and types for all fields in the preferences
    file. Only database_type is required; all other fields are optional.
    """

    database_type: str
    language: str | None = None
    track: str | None = None
    deployment_target: str | None = None
    cloud_provider: str | None = None
    verbosity: str | None = None
    conversation_style: str | dict | None = None
    mapping_verbosity: str | None = None
    hooks_installed: list[str] | None = None
    pacing_overrides: str | None = None
    license: str | None = None
    license_guidance_deferred: bool | None = None
    skip_graduation: bool | None = None
    team_member_id: str | None = None
    scoop_installed_during_onboarding: bool | None = None
    runtimes_installed_during_onboarding: list[dict] | None = None
    prerequisite_installation_deferred: bool | None = None
    detail_level: str | None = None
    hardware_target: str | None = None
    production_specs: dict | None = None


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class WriteResult:
    """Result of a preference write operation.

    Attributes:
        success: Whether the write completed successfully.
        error: Human-readable error message if the write failed, None otherwise.
    """

    success: bool
    error: str | None = None


@dataclass
class LoadResult:
    """Result of loading preferences from the YAML file.

    Attributes:
        preferences: Parsed preferences dict, or None if file is missing/corrupt.
        missing_required: List of required field names that are absent from the file.
        error: Human-readable error message if loading failed, None otherwise.
    """

    preferences: dict | None
    missing_required: list[str]
    error: str | None = None


@dataclass
class ContextResetMessage:
    """Structured context reset message with metadata.

    Attributes:
        message: The formatted message to display to the bootcamper.
        module_number: Current module number (1-11) from progress state.
        step_identifier: Current step within the module, or None if unknown.
        continuation_phrase: The phrase the bootcamper should paste into a new chat.
    """

    message: str
    module_number: int
    step_identifier: str | int | None
    continuation_phrase: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FORBIDDEN_TEMPORAL_PHRASES: tuple[str, ...] = (
    "come back later",
    "come back tomorrow",
    "take a break",
    "try again in a while",
    "when you're ready",
    "try again later",
    "wait a moment",
    "give it some time",
)

LANGUAGE_STEERING_MAP: dict[str, str] = {
    "python": "lang-python.md",
    "java": "lang-java.md",
    "csharp": "lang-csharp.md",
    "c#": "lang-csharp.md",
    "rust": "lang-rust.md",
    "typescript": "lang-typescript.md",
}


# ---------------------------------------------------------------------------
# Language steering resolver
# ---------------------------------------------------------------------------


def resolve_language_steering(language: str) -> str | None:
    """Map a language preference value to its steering file name.

    Args:
        language: The persisted language value (case-insensitive).

    Returns:
        Steering file name (e.g., "lang-python.md") or None if unrecognized.
    """
    return LANGUAGE_STEERING_MAP.get(language.lower())


# ---------------------------------------------------------------------------
# Session resume summary formatter
# ---------------------------------------------------------------------------


def format_resume_summary(
    language: str,
    track: str,
    verbosity: str,
) -> str:
    """Format a 1-2 sentence session resume confirmation.

    Args:
        language: Active programming language.
        track: Active bootcamp track.
        verbosity: Active verbosity level.

    Returns:
        Summary string of at most 2 sentences containing all three values.
    """
    return f"Resuming with {language}, {verbosity} verbosity, {track} track."


# ---------------------------------------------------------------------------
# Context reset formatter
# ---------------------------------------------------------------------------


def format_context_reset(
    progress_path: str = "config/bootcamp_progress.json",
) -> ContextResetMessage:
    """Generate a context reset message from current progress state.

    Reads the progress file to determine current module and step,
    then formats a message containing:
    1. Technical reason (context memory full)
    2. Immediacy clarification (can start new chat right now)
    3. Progress reassurance (all work saved in project files)
    4. Continuation instruction with quoted phrase

    The message is at most 4 sentences, contains no temporal delay language,
    and includes no questions.

    Args:
        progress_path: Path to the progress JSON file.

    Returns:
        ContextResetMessage with the formatted message and metadata.
    """
    import json

    # Default fallback values
    module_number = 1
    step_identifier: str | int | None = None

    # Read progress file
    try:
        with open(progress_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_module = data.get("current_module")
        if isinstance(raw_module, int) and 1 <= raw_module <= 11:
            module_number = raw_module
        raw_step = data.get("current_step")
        if isinstance(raw_step, (str, int)):
            step_identifier = raw_step
    except (OSError, IOError, json.JSONDecodeError, TypeError, AttributeError):
        # File missing or corrupt — use fallback defaults
        pass

    # Build continuation phrase
    continuation_phrase = f"continue the bootcamp from module {module_number}"

    # Format the 4-sentence message
    message = (
        "My conversation memory is getting full from our work so far. "
        "You can start a new chat right now to continue. "
        "All your progress is saved in your project files and will be "
        "available in the new session. "
        f'Say "{continuation_phrase}" in the new chat.'
    )

    return ContextResetMessage(
        message=message,
        module_number=module_number,
        step_identifier=step_identifier,
        continuation_phrase=continuation_phrase,
    )


# ---------------------------------------------------------------------------
# YAML serializer (minimal, stdlib-only)
# ---------------------------------------------------------------------------


def _serialize_yaml_value(value: str | bool | int | dict | list | None) -> str:
    """Serialize a Python value to a YAML string fragment.

    Handles scalars (str, bool, int, None), flat dicts, and lists of
    scalars or dicts. Designed for the shallow preferences schema.

    Args:
        value: The value to serialize.

    Returns:
        YAML string representation (may be multi-line for dicts/lists).
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        # Quote strings that could be misinterpreted as YAML special values.
        # Any string whose lowercased form is a YAML bool/null literal (e.g.
        # "FalSe", "TRUE") must be quoted so it round-trips back to str rather
        # than being coerced to a Python bool/None on read.
        if value in ("true", "false", "null", "~", "") or value.lower() in (
            "true",
            "false",
            "null",
        ):
            return f'"{value}"'
        if value.startswith(("{", "[", "-", "#", '"', "'")) or ":" in value:
            return f'"{value}"'
        try:
            int(value)
            return f'"{value}"'
        except ValueError:
            pass
        return value
    if isinstance(value, dict):
        lines: list[str] = []
        for k, v in value.items():
            lines.append(f"  {k}: {_serialize_yaml_value(v)}")
        return "\n" + "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    if first:
                        lines.append(f"  - {k}: {_serialize_yaml_value(v)}")
                        first = False
                    else:
                        lines.append(f"    {k}: {_serialize_yaml_value(v)}")
            else:
                lines.append(f"  - {_serialize_yaml_value(item)}")
        return "\n" + "\n".join(lines)
    return str(value)


def _serialize_preferences(data: dict) -> str:
    """Serialize a preferences dict to a YAML string.

    Args:
        data: Preferences dict with known top-level keys.

    Returns:
        Valid YAML string ready to write to file.
    """
    lines: list[str] = []
    for key, value in data.items():
        serialized = _serialize_yaml_value(value)
        if serialized.startswith("\n"):
            lines.append(f"{key}:{serialized}")
        else:
            lines.append(f"{key}: {serialized}")
    return "\n".join(lines) + "\n" if lines else ""


# ---------------------------------------------------------------------------
# Preference writer
# ---------------------------------------------------------------------------

_MAX_FILE_SIZE_BYTES = 10 * 1024  # 10 KB


def write_preference(
    key: str,
    value: str | bool | dict | list | None,
    preferences_path: str = "config/bootcamp_preferences.yaml",
) -> WriteResult:
    """Write a single preference field atomically.

    Reads existing file (if any), merges the new key-value pair,
    validates the result, and writes atomically via temp file + rename.

    Args:
        key: The preference field name (must be in KNOWN_TOP_LEVEL_KEYS).
        value: The value to persist. None values are treated as deletion
               (the key is removed from the file rather than stored as null).
        preferences_path: Path to the preferences YAML file.

    Returns:
        WriteResult with success status and optional error message.
    """
    # Validate key is known
    if key not in KNOWN_TOP_LEVEL_KEYS:
        return WriteResult(success=False, error=f"Unknown key: '{key}'")

    # Read existing preferences
    existing: dict = {}
    try:
        if os.path.isfile(preferences_path):
            with open(preferences_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                existing = parse_yaml(content)
    except (OSError, IOError) as exc:
        return WriteResult(success=False, error=f"Failed to read preferences: {exc}")
    except ValueError:
        # Existing file has invalid YAML — start fresh with just the new value
        existing = {}

    # Merge: remove key if value is None, otherwise set it
    if value is None:
        existing.pop(key, None)
    else:
        existing[key] = value

    # Serialize the updated preferences
    yaml_content = _serialize_preferences(existing)

    # Validate size constraint
    content_bytes = yaml_content.encode("utf-8")
    if len(content_bytes) > _MAX_FILE_SIZE_BYTES:
        return WriteResult(
            success=False, error="File would exceed 10 KB limit"
        )

    # Ensure directory exists
    dir_path = os.path.dirname(preferences_path)
    if dir_path:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as exc:
            return WriteResult(
                success=False, error=f"Failed to create directory: {exc}"
            )

    # Atomic write: temp file + os.replace()
    tmp_path = ""
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=dir_path if dir_path else ".",
            prefix=".bootcamp_preferences_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(yaml_content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
        except (OSError, IOError):
            os.close(fd)
            raise

        os.replace(tmp_path, preferences_path)
    except (OSError, IOError) as exc:
        # Clean up temp file if it still exists
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass
        return WriteResult(
            success=False, error=f"Failed to write preferences: {exc}"
        )

    return WriteResult(success=True)


# ---------------------------------------------------------------------------
# Minimal YAML parser
# ---------------------------------------------------------------------------


def _parse_scalar(value: str) -> str | int | bool | None:
    """Parse a YAML scalar value into a Python type.

    Args:
        value: Raw string value from a YAML line (already stripped).

    Returns:
        Parsed Python value: None, bool, int, or str.
    """
    if value in ("null", "~", ""):
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def parse_yaml(text: str) -> dict:
    """Parse a minimal YAML subset into a Python dict.

    Handles:
    - Scalar values: strings (quoted/unquoted), integers, booleans, null
    - Flat key-value pairs
    - Nested dicts (indented key-value pairs)
    - Lists (- prefix items)
    - Lists of dicts (list items with nested key-value pairs)
    - Comment lines (# prefix) and blank lines (ignored)

    Args:
        text: YAML content as a string.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If content cannot be parsed, with line number and description.
    """
    result: dict = {}
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        # Top-level lines must not be indented
        if line != line.lstrip():
            raise ValueError(
                f"Line {i + 1}: unexpected indentation: {line!r}"
            )

        # Must be a key: value pair at top level
        colon_idx = stripped.find(":")
        if colon_idx == -1:
            raise ValueError(
                f"Line {i + 1}: expected key-value pair, got: {stripped!r}"
            )

        key = stripped[:colon_idx].strip()
        rest = stripped[colon_idx + 1:].strip()

        # Check if rest is an inline empty list
        if rest == "[]":
            result[key] = []
            i += 1
            continue

        # Check if rest is an inline empty dict
        if rest == "{}":
            result[key] = {}
            i += 1
            continue

        # If rest has a value, it's a simple scalar
        if rest:
            # Check for inline comment
            if rest.startswith("#"):
                result[key] = None
                i += 1
                continue
            result[key] = _parse_scalar(rest)
            i += 1
            continue

        # rest is empty — check next lines for nested content
        # Peek ahead to determine if nested dict or list
        i += 1
        if i >= len(lines):
            result[key] = None
            continue

        # Find the first non-blank, non-comment line to determine structure
        peek = i
        while peek < len(lines):
            peek_stripped = lines[peek].strip()
            if peek_stripped == "" or peek_stripped.startswith("#"):
                peek += 1
                continue
            break

        if peek >= len(lines) or not lines[peek].startswith((" ", "\t")):
            # No indented content follows — value is null
            result[key] = None
            continue

        peek_stripped = lines[peek].strip()

        if peek_stripped.startswith("- ") or peek_stripped == "-":
            # List
            result[key], i = _parse_list(lines, i)
        else:
            # Nested dict
            result[key], i = _parse_nested_dict(lines, i)

    return result


def _parse_list(lines: list[str], start: int) -> tuple[list, int]:
    """Parse a YAML list starting at the given line index.

    Args:
        lines: All lines of the YAML text.
        start: Index of the first line to consider.

    Returns:
        Tuple of (parsed list, next line index to process).
    """
    items: list = []
    i = start

    # Determine the indentation level of list items
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        break

    if i >= len(lines):
        return items, i

    # Get the indent level of the first list item
    list_indent = len(lines[i]) - len(lines[i].lstrip())

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        # Check indentation — if less than list indent, we're done
        current_indent = len(line) - len(line.lstrip())
        if current_indent < list_indent:
            break

        if not stripped.startswith("- ") and stripped != "-":
            # Not a list item — might be continuation of previous dict item
            # or we're done with the list
            break

        # It's a list item
        item_content = stripped[2:].strip() if stripped.startswith("- ") else ""

        if not item_content:
            # Empty list item — could be a dict follows
            # Check next line for indented key-value pairs
            i += 1
            if i < len(lines):
                next_stripped = lines[i].strip()
                next_indent = len(lines[i]) - len(lines[i].lstrip()) if lines[i].strip() else 0
                if next_indent > current_indent and ":" in next_stripped:
                    # List of dicts — parse nested dict for this item
                    item_dict, i = _parse_list_item_dict(lines, i, current_indent)
                    items.append(item_dict)
                else:
                    items.append(None)
            else:
                items.append(None)
            continue

        # Check if item_content contains a colon (dict-like item on same line)
        colon_idx = item_content.find(":")
        if colon_idx != -1:
            # Could be a dict item starting on the same line as -
            item_key = item_content[:colon_idx].strip()
            item_val = item_content[colon_idx + 1:].strip()
            item_dict: dict = {item_key: _parse_scalar(item_val)}
            i += 1
            # Check for more keys at deeper indentation
            while i < len(lines):
                sub_line = lines[i]
                sub_stripped = sub_line.strip()
                if sub_stripped == "" or sub_stripped.startswith("#"):
                    i += 1
                    continue
                sub_indent = len(sub_line) - len(sub_line.lstrip())
                if sub_indent <= current_indent:
                    break
                # Must be a key: value pair for this dict
                sub_colon = sub_stripped.find(":")
                if sub_colon == -1:
                    break
                sub_key = sub_stripped[:sub_colon].strip()
                sub_val = sub_stripped[sub_colon + 1:].strip()
                item_dict[sub_key] = _parse_scalar(sub_val)
                i += 1
            items.append(item_dict)
        else:
            # Simple scalar list item
            items.append(_parse_scalar(item_content))
            i += 1

    return items, i


def _parse_list_item_dict(
    lines: list[str], start: int, dash_indent: int
) -> tuple[dict, int]:
    """Parse key-value pairs belonging to a list item dict.

    Args:
        lines: All lines of the YAML text.
        start: Index of the first key-value line.
        dash_indent: Indentation level of the parent dash.

    Returns:
        Tuple of (parsed dict, next line index to process).
    """
    item_dict: dict = {}
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= dash_indent:
            break

        colon_idx = stripped.find(":")
        if colon_idx == -1:
            break

        key = stripped[:colon_idx].strip()
        val = stripped[colon_idx + 1:].strip()
        item_dict[key] = _parse_scalar(val)
        i += 1

    return item_dict, i


def _parse_nested_dict(lines: list[str], start: int) -> tuple[dict, int]:
    """Parse a nested YAML dict starting at the given line index.

    Args:
        lines: All lines of the YAML text.
        start: Index of the first line to consider.

    Returns:
        Tuple of (parsed dict, next line index to process).
    """
    nested: dict = {}
    i = start

    # Find the indent level of the first nested key
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        break

    if i >= len(lines):
        return nested, i

    dict_indent = len(lines[i]) - len(lines[i].lstrip())

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent < dict_indent:
            break

        colon_idx = stripped.find(":")
        if colon_idx == -1:
            raise ValueError(
                f"Line {i + 1}: expected key-value pair in nested dict, got: {stripped!r}"
            )

        key = stripped[:colon_idx].strip()
        val = stripped[colon_idx + 1:].strip()
        nested[key] = _parse_scalar(val)
        i += 1

    return nested, i


# ---------------------------------------------------------------------------
# Preferences validator
# ---------------------------------------------------------------------------

# Type expectations per key: maps key name to tuple of allowed types.
# None in the tuple means the value can be None (nullable).
_STR_OR_NONE_KEYS: set[str] = {
    "language",
    "track",
    "deployment_target",
    "cloud_provider",
    "verbosity",
    "mapping_verbosity",
    "pacing_overrides",
    "license",
    "team_member_id",
    "detail_level",
    "hardware_target",
}

_BOOL_OR_NONE_KEYS: set[str] = {
    "license_guidance_deferred",
    "skip_graduation",
    "scoop_installed_during_onboarding",
    "prerequisite_installation_deferred",
}

# Enum constraints for conversation_style sub-keys
_CONVERSATION_STYLE_ENUMS: dict[str, tuple[str, ...]] = {
    "verbosity_preset": VALID_VERBOSITY_PRESET,
    "question_framing": VALID_QUESTION_FRAMING,
    "tone": VALID_TONE,
    "pacing": VALID_PACING,
}

# Type expectations for production_specs sub-keys
_PRODUCTION_SPECS_TYPES: dict[str, type] = {
    "cpu_cores": int,
    "ram_gb": int,
    "storage_type": str,
    "database": str,
}


def _type_name(value: object) -> str:
    """Return a human-readable type name for error messages."""
    if value is None:
        return "NoneType"
    return type(value).__name__


def validate_preferences_schema(data: dict) -> list[str]:
    """Validate a preferences dict against the full schema.

    Performs strict validation:
    1. Rejects unknown top-level keys
    2. Requires database_type (only required field)
    3. Validates types for all known keys
    4. Validates enum constraints for restricted fields
    5. Validates nested dict structures (conversation_style, production_specs)
    6. Validates list element structures (hooks_installed,
       runtimes_installed_during_onboarding)

    Never short-circuits — collects all errors and returns the complete list.

    Args:
        data: Parsed preferences dict.

    Returns:
        Empty list when valid, or list of human-readable error strings.
    """
    errors: list[str] = []

    # 1. Check for unknown top-level keys
    for key in data:
        if key not in KNOWN_TOP_LEVEL_KEYS:
            errors.append(f"Unknown top-level key: '{key}'")

    # 2. Check required key (database_type) is present
    if "database_type" not in data:
        errors.append("Missing required key: 'database_type'")

    # 3. For each known key present in data, validate type, enum, and structure
    for key in data:
        if key not in KNOWN_TOP_LEVEL_KEYS:
            continue

        value = data[key]

        # --- database_type: str (required, non-nullable) ---
        if key == "database_type":
            if not isinstance(value, str):
                errors.append(
                    f"database_type: expected str, got {_type_name(value)}"
                )

        # --- str | None keys ---
        elif key in _STR_OR_NONE_KEYS:
            if value is not None and not isinstance(value, str):
                errors.append(
                    f"{key}: expected str, got {_type_name(value)}"
                )
            # Enum constraints
            if isinstance(value, str):
                if key == "mapping_verbosity" and value not in VALID_MAPPING_VERBOSITY:
                    errors.append(
                        f"{key}: must be one of {VALID_MAPPING_VERBOSITY}, got '{value}'"
                    )
                elif key == "hardware_target" and value not in VALID_HARDWARE_TARGET:
                    errors.append(
                        f"{key}: must be one of {VALID_HARDWARE_TARGET}, got '{value}'"
                    )

        # --- bool | None keys ---
        elif key in _BOOL_OR_NONE_KEYS:
            if value is not None and not isinstance(value, bool):
                errors.append(
                    f"{key}: expected bool, got {_type_name(value)}"
                )

        # --- conversation_style: str | dict | None ---
        elif key == "conversation_style":
            if value is not None and not isinstance(value, (str, dict)):
                errors.append(
                    f"conversation_style: expected str or dict, got {_type_name(value)}"
                )
            if isinstance(value, dict):
                # Validate nested keys
                for sub_key in value:
                    if sub_key not in CONVERSATION_STYLE_KEYS:
                        errors.append(
                            f"conversation_style: unknown key '{sub_key}'"
                        )
                # Validate sub-key types and enum constraints
                for sub_key in value:
                    if sub_key not in CONVERSATION_STYLE_KEYS:
                        continue
                    sub_value = value[sub_key]
                    if not isinstance(sub_value, str):
                        errors.append(
                            f"conversation_style.{sub_key}: expected str, "
                            f"got {_type_name(sub_value)}"
                        )
                    elif sub_key in _CONVERSATION_STYLE_ENUMS:
                        allowed = _CONVERSATION_STYLE_ENUMS[sub_key]
                        if sub_value not in allowed:
                            errors.append(
                                f"conversation_style.{sub_key}: must be one of "
                                f"{allowed}, got '{sub_value}'"
                            )

        # --- hooks_installed: list[str] | None ---
        elif key == "hooks_installed":
            if value is not None and not isinstance(value, list):
                errors.append(
                    f"hooks_installed: expected list, got {_type_name(value)}"
                )
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(
                            f"hooks_installed[{idx}]: expected str, "
                            f"got {_type_name(item)}"
                        )

        # --- runtimes_installed_during_onboarding: list[dict] | None ---
        elif key == "runtimes_installed_during_onboarding":
            if value is not None and not isinstance(value, list):
                errors.append(
                    f"runtimes_installed_during_onboarding: expected list, "
                    f"got {_type_name(value)}"
                )
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(
                            f"runtimes_installed_during_onboarding[{idx}]: "
                            f"expected dict, got {_type_name(item)}"
                        )
                    else:
                        # Validate dict has name (str) and version (str)
                        if "name" not in item:
                            errors.append(
                                f"runtimes_installed_during_onboarding[{idx}]: "
                                f"missing required key 'name'"
                            )
                        elif not isinstance(item["name"], str):
                            errors.append(
                                f"runtimes_installed_during_onboarding[{idx}].name: "
                                f"expected str, got {_type_name(item['name'])}"
                            )
                        if "version" not in item:
                            errors.append(
                                f"runtimes_installed_during_onboarding[{idx}]: "
                                f"missing required key 'version'"
                            )
                        elif not isinstance(item["version"], str):
                            errors.append(
                                f"runtimes_installed_during_onboarding[{idx}].version: "
                                f"expected str, got {_type_name(item['version'])}"
                            )

        # --- production_specs: dict | None ---
        elif key == "production_specs":
            if value is not None and not isinstance(value, dict):
                errors.append(
                    f"production_specs: expected dict, got {_type_name(value)}"
                )
            elif isinstance(value, dict):
                # Validate nested keys
                for sub_key in value:
                    if sub_key not in PRODUCTION_SPECS_KEYS:
                        errors.append(
                            f"production_specs: unknown key '{sub_key}'"
                        )
                # Validate sub-key types
                for sub_key in value:
                    if sub_key not in PRODUCTION_SPECS_KEYS:
                        continue
                    sub_value = value[sub_key]
                    expected_type = _PRODUCTION_SPECS_TYPES[sub_key]
                    if not isinstance(sub_value, expected_type):
                        errors.append(
                            f"production_specs.{sub_key}: expected "
                            f"{expected_type.__name__}, "
                            f"got {_type_name(sub_value)}"
                        )

    return errors


# ---------------------------------------------------------------------------
# Preference loading
# ---------------------------------------------------------------------------


def load_preferences(
    preferences_path: str = "config/bootcamp_preferences.yaml",
    required_fields: tuple[str, ...] = ("language", "track", "verbosity"),
) -> LoadResult:
    """Load and validate preferences from the YAML file.

    Reads the preferences file, parses it using the custom YAML parser,
    and identifies any missing required fields. Does NOT assume default
    values for missing fields.

    Args:
        preferences_path: Path to the preferences YAML file.
        required_fields: Fields that must be present for a complete session.

    Returns:
        LoadResult with parsed preferences, list of missing required fields,
        and optional error message if file is missing/corrupt.
    """
    import os

    # Check if file exists
    if not os.path.exists(preferences_path):
        return LoadResult(
            preferences=None,
            missing_required=list(required_fields),
            error="File not found",
        )

    # Try to read the file
    try:
        with open(preferences_path, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError as e:
        return LoadResult(
            preferences=None,
            missing_required=list(required_fields),
            error=f"Permission denied: {e}",
        )
    except OSError as e:
        return LoadResult(
            preferences=None,
            missing_required=list(required_fields),
            error=f"Cannot read file: {e}",
        )

    # Try to parse the YAML content
    try:
        preferences = parse_yaml(content)
    except ValueError as e:
        return LoadResult(
            preferences=None,
            missing_required=list(required_fields),
            error=f"Invalid YAML: {e}",
        )

    # Identify missing required fields
    missing = [
        field for field in required_fields
        if field not in preferences or preferences[field] is None
    ]

    return LoadResult(
        preferences=preferences,
        missing_required=missing,
        error=None,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run preferences utilities.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Preferences Schema Validation Utilities."
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    main()
