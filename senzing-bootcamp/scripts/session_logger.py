#!/usr/bin/env python3
"""Senzing Bootcamp - Session Logger.

Appends structured JSONL entries to ``config/session_log.jsonl`` so that
bootcamp maintainers can analyse session-level data (time per module,
corrections, confusion indicators).

Uses only the Python standard library.
"""

from __future__ import annotations

import datetime
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Union

LOG_PATH_DEFAULT: str = "config/session_log.jsonl"

VALID_EVENTS: set[str] = {"turn", "correction", "module_start", "module_complete"}


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
