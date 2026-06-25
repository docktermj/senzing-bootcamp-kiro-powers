#!/usr/bin/env python3
"""Senzing Bootcamp - Session Log Write-Event Helper.

Append one generic write-action entry to ``config/session_log.jsonl``. This
helper backs the ``session-log-events`` postToolUse hook's ``runCommand``
action: the IDE runs it directly after every write tool call, so logging
incurs no agent round-trip.

The entry records a UTC timestamp and the current module number read from
``config/bootcamp_progress.json`` (defaulting to ``0`` on any error). All
logic is wrapped in try/except; the helper fails silently (returns ``0`` and
prints nothing) so it can never block or interrupt the bootcamp flow.

Usage:
    python3 senzing-bootcamp/scripts/log_write_event.py

Paths are resolved relative to the current working directory (the bootcamp
workspace root), consistent with the hook's other relative-path conventions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import session_logger  # noqa: E402

_PROGRESS_PATH: str = "config/bootcamp_progress.json"
_SESSION_LOG_PATH: str = "config/session_log.jsonl"
_MIN_MODULE: int = 0
_MAX_MODULE: int = 11


def _read_current_module() -> int:
    """Read ``current_module`` from the progress file, clamped to 0–11.

    Returns:
        The current module number as an int in the range 0–11. Defaults to
        ``0`` on any error (missing file, parse error, missing key, non-int).
    """
    try:
        raw = Path(_PROGRESS_PATH).read_text(encoding="utf-8")
        value = json.loads(raw)["current_module"]
        if isinstance(value, bool) or not isinstance(value, int):
            return _MIN_MODULE
        return max(_MIN_MODULE, min(_MAX_MODULE, value))
    except Exception:
        return _MIN_MODULE


def main(argv: list[str] | None = None) -> int:
    """Append one generic write-action entry to the session log, silently.

    Args:
        argv: Optional argument vector (unused beyond ``--help``); defaults to
            ``sys.argv[1:]``.

    Returns:
        Always ``0`` — the helper is non-blocking and swallows all errors.
    """
    try:
        parser = argparse.ArgumentParser(
            description=(
                "Append one generic write-action entry to "
                "config/session_log.jsonl (session-log-events runCommand hook)."
            )
        )
        parser.parse_args(argv)

        module = _read_current_module()
        entry = session_logger.build_completion_entry(
            event_type="action",
            module=module,
            data={"action_type": "command_run", "description": "write operation"},
        )
        session_logger.append_completion_entry(_SESSION_LOG_PATH, entry)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
