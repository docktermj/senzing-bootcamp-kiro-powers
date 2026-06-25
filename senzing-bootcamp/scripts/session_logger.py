#!/usr/bin/env python3
"""Senzing Bootcamp - Session Logger.

Appends structured JSONL entries to ``config/session_log.jsonl`` so that
bootcamp maintainers can analyse session-level data (time per module,
corrections, confusion indicators).

Also provides the completion-summary event schema (question, answer, action,
artifact) used by the narrative formatter and PDF generator.

Uses only the Python standard library.
"""

from __future__ import annotations

import datetime
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Union

LOG_PATH_DEFAULT: str = "config/session_log.jsonl"

VALID_EVENTS: set[str] = {"turn", "correction", "module_start", "module_complete"}

# ---------------------------------------------------------------------------
# Completion Summary event types and schema
# ---------------------------------------------------------------------------

COMPLETION_EVENT_TYPES: set[str] = {"question", "answer", "action", "artifact"}

_VALID_ACTION_TYPES: set[str] = {
    "file_create", "file_modify", "file_delete", "command_run", "mcp_tool_call",
}

_VALID_ARTIFACT_TYPES: set[str] = {
    "script", "config", "data", "report", "visualization",
}

_FILE_ACTION_TYPES: set[str] = {"file_create", "file_modify", "file_delete"}


@dataclass
class LogEntry:
    """A single structured event written to the session log."""

    timestamp: str
    session_id: str
    module: int
    step: Union[str, int]
    event: str
    duration_seconds: float
    message: str


def build_log_entry(
    session_id: str,
    module: int,
    step: Union[str, int],
    event: str,
    duration_seconds: float,
    message: str,
) -> LogEntry:
    """Construct a LogEntry with the current UTC timestamp.

    Args:
        session_id: Session identifier string (must be non-empty).
        module: Module number (1–11).
        step: Step identifier within the module.
        event: Event type from VALID_EVENTS.
        duration_seconds: Non-negative elapsed time since previous entry.
        message: Free-text summary.

    Returns:
        A ``LogEntry`` dataclass instance.

    Raises:
        ValueError: If *module* is not in 1–11, *event* is not in
            VALID_EVENTS, *duration_seconds* is negative, or
            *session_id* is empty.
    """
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")
    if not isinstance(module, int) or not (1 <= module <= 11):
        raise ValueError(f"module must be an integer in 1–11, got {module!r}")
    if event not in VALID_EVENTS:
        raise ValueError(
            f"event must be one of {sorted(VALID_EVENTS)}, got {event!r}"
        )
    if not isinstance(duration_seconds, (int, float)) or duration_seconds < 0:
        raise ValueError(
            f"duration_seconds must be non-negative, got {duration_seconds!r}"
        )

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return LogEntry(
        timestamp=timestamp,
        session_id=session_id,
        module=module,
        step=step,
        event=event,
        duration_seconds=float(duration_seconds),
        message=message,
    )


def serialize_entry(entry: LogEntry) -> str:
    """Serialize a ``LogEntry`` to a compact JSON string (no trailing newline).

    Returns:
        A compact JSON string representing the entry.
    """
    return json.dumps(asdict(entry), separators=(",", ":"))


def append_entry(log_path: str, entry: LogEntry) -> None:
    """Append a serialized ``LogEntry`` as a single line to the log file.

    Creates the file and parent directories if they don't exist.
    On any file-system error, prints a warning to stderr and returns
    without raising.
    """
    try:
        p = Path(log_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(serialize_entry(entry) + "\n")
    except OSError as exc:
        print(f"WARNING: session_logger could not write to {log_path}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Completion Summary dataclass and functions
# ---------------------------------------------------------------------------


@dataclass
class CompletionLogEntry:
    """A session log entry for the completion summary feature."""

    event_type: str
    module: int
    timestamp: str
    data: dict[str, str]


def generate_question_id() -> str:
    """Generate a unique question ID (first 8 hex chars of a UUID4).

    Returns:
        An 8-character hexadecimal string.
    """
    return uuid.uuid4().hex[:8]


def truncate_field(value: str, max_length: int) -> str:
    """Truncate a string to max_length characters.

    Args:
        value: The string to truncate.
        max_length: Maximum allowed length.

    Returns:
        The original string if within limit, otherwise the first max_length characters.
    """
    return value[:max_length]


def _validate_question_data(data: dict[str, str]) -> None:
    """Validate data fields for a question event."""
    if "text" not in data:
        raise ValueError("question event requires 'text' in data")
    if "question_id" not in data:
        raise ValueError("question event requires 'question_id' in data")


def _validate_answer_data(data: dict[str, str]) -> None:
    """Validate data fields for an answer event."""
    if "text" not in data:
        raise ValueError("answer event requires 'text' in data")
    if "question_id" not in data:
        raise ValueError("answer event requires 'question_id' in data")


def _validate_action_data(data: dict[str, str]) -> None:
    """Validate data fields for an action event."""
    if "action_type" not in data:
        raise ValueError("action event requires 'action_type' in data")
    if data["action_type"] not in _VALID_ACTION_TYPES:
        raise ValueError(
            f"action_type must be one of {sorted(_VALID_ACTION_TYPES)}, "
            f"got {data['action_type']!r}"
        )
    if "description" not in data:
        raise ValueError("action event requires 'description' in data")
    if data["action_type"] in _FILE_ACTION_TYPES and "file_path" not in data:
        raise ValueError(
            f"action event with action_type={data['action_type']!r} "
            f"requires 'file_path' in data"
        )


def _validate_artifact_data(data: dict[str, str]) -> None:
    """Validate data fields for an artifact event."""
    if "file_path" not in data:
        raise ValueError("artifact event requires 'file_path' in data")
    if "artifact_type" not in data:
        raise ValueError("artifact event requires 'artifact_type' in data")
    if data["artifact_type"] not in _VALID_ARTIFACT_TYPES:
        raise ValueError(
            f"artifact_type must be one of {sorted(_VALID_ARTIFACT_TYPES)}, "
            f"got {data['artifact_type']!r}"
        )
    if "description" not in data:
        raise ValueError("artifact event requires 'description' in data")


_DATA_VALIDATORS: dict[str, object] = {
    "question": _validate_question_data,
    "answer": _validate_answer_data,
    "action": _validate_action_data,
    "artifact": _validate_artifact_data,
}


def build_completion_entry(
    event_type: str,
    module: int,
    data: dict[str, str],
) -> CompletionLogEntry:
    """Construct a CompletionLogEntry with validation and auto-generated timestamp.

    Args:
        event_type: One of COMPLETION_EVENT_TYPES.
        module: Module number (0–11).
        data: Event-type-specific fields.

    Returns:
        A validated ``CompletionLogEntry`` instance.

    Raises:
        ValueError: If event_type is invalid, module is out of range,
            or required data fields are missing/invalid for the event type.
    """
    if event_type not in COMPLETION_EVENT_TYPES:
        raise ValueError(
            f"event_type must be one of {sorted(COMPLETION_EVENT_TYPES)}, "
            f"got {event_type!r}"
        )
    if not isinstance(module, int) or not (0 <= module <= 11):
        raise ValueError(f"module must be an integer in 0–11, got {module!r}")

    validator = _DATA_VALIDATORS[event_type]
    validator(data)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return CompletionLogEntry(
        event_type=event_type,
        module=module,
        timestamp=timestamp,
        data=data,
    )


def serialize_completion_entry(entry: CompletionLogEntry) -> str:
    """Serialize a CompletionLogEntry to a compact JSON string.

    Args:
        entry: The completion log entry to serialize.

    Returns:
        A compact JSON string (no extra whitespace, no trailing newline).
    """
    return json.dumps(asdict(entry), separators=(",", ":"))


def append_completion_entry(log_path: str, entry: CompletionLogEntry) -> None:
    """Append a serialized CompletionLogEntry as a single line to the log file.

    Creates the file and parent directories if they don't exist.
    On any file-system error, prints a warning to stderr and returns
    without raising.

    Args:
        log_path: Path to the JSONL log file.
        entry: The completion log entry to append.
    """
    try:
        p = Path(log_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(serialize_completion_entry(entry) + "\n")
    except OSError as exc:
        print(
            f"WARNING: session_logger could not write to {log_path}: {exc}",
            file=sys.stderr,
        )
