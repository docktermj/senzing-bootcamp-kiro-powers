#!/usr/bin/env python3
"""Senzing Bootcamp - Progress Checkpoint Utilities.

Provides helpers for step-level progress checkpointing in
config/bootcamp_progress.json.

Cross-platform: works on Linux, macOS, and Windows.
"""

from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

VALID_TRACKS = ("core_bootcamp", "advanced_topics")
MODULE_RANGE = range(1, 12)  # 1–11 inclusive
STEP_HISTORY_KEY_RANGE = range(1, 13)  # 1–12 inclusive


# ---------------------------------------------------------------------------
# Schema dataclass
# ---------------------------------------------------------------------------


@dataclass
class ProgressSchema:
    """Canonical schema for bootcamp_progress.json.

    Defines the expected structure and types for all fields in the progress
    file. Required fields have no default; optional fields default to None.

    This dataclass serves as documentation and as the basis for the Hypothesis
    strategy. It does NOT enforce validation itself — that remains in
    ``validate_progress_schema()``.
    """

    current_module: int  # 1–11
    modules_completed: list[int]  # each 1–11
    data_sources: list[str]
    database_type: str
    # Optional fields (backward-compatible)
    current_step: int | str | None = None
    track: str | None = None  # core_bootcamp | advanced_topics
    preferences: dict[str, str | bool] | None = None
    session_id: str | None = None
    started_at: str | None = None  # ISO 8601
    last_activity: str | None = None  # ISO 8601
    step_history: dict[str, dict] | None = None


_DOTTED_SUB_STEP_RE = re.compile(r"^\d+\.\d+$")
_LETTERED_SUB_STEP_RE = re.compile(r"^\d+[a-zA-Z]$")


def _read_progress(progress_path: str) -> dict:
    """Read and return the progress file as a dict."""
    p = Path(progress_path)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _write_progress(progress_path: str, data: dict) -> None:
    """Write the progress dict back to the file with 2-space indent and trailing newline."""
    p = Path(progress_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_checkpoint(
    module_number: int,
    step: int | str,
    progress_path: str = "config/bootcamp_progress.json",
) -> None:
    """Write a step-level checkpoint to the progress file.

    Updates ``current_step`` to *step* and sets the ``step_history``
    entry for *module_number* with the step value and an ISO 8601 UTC
    timestamp.

    Args:
        module_number: The module number (1-12).
        step: The step identifier — an integer for whole steps (e.g., ``5``)
            or a string for sub-steps (e.g., ``"5.3"``, ``"7a"``).
        progress_path: Path to the progress JSON file.
    """
    data = _read_progress(progress_path)
    data["current_step"] = step

    step_history = data.setdefault("step_history", {})
    step_history[str(module_number)] = {
        "last_completed_step": step,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    _write_progress(progress_path, data)


def clear_step(
    progress_path: str = "config/bootcamp_progress.json",
) -> None:
    """Clear the current step (module completion).

    Sets ``current_step`` to ``None`` while retaining ``step_history``.
    """
    data = _read_progress(progress_path)
    data["current_step"] = None
    _write_progress(progress_path, data)


def _is_valid_iso8601(value: str) -> bool:
    """Return True if *value* is a valid ISO 8601 datetime string."""
    try:
        datetime.datetime.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def _is_valid_sub_step_identifier(value: str) -> bool:
    """Return True if *value* matches a recognized sub-step format.

    Recognized formats:
    - Dotted notation: ``<digits>.<digits>`` (e.g., ``"5.3"``, ``"12.1"``)
    - Lettered notation: ``<digits><letter>`` (e.g., ``"7a"``, ``"3B"``)
    """
    return bool(_DOTTED_SUB_STEP_RE.match(value) or _LETTERED_SUB_STEP_RE.match(value))


def parse_parent_step(step: int | str | None) -> int | None:
    """Extract the parent step number from a step identifier.

    Args:
        step: A step identifier — ``None``, an ``int`` (e.g., ``5``),
            a dotted sub-step string (e.g., ``"5.3"``), or a lettered
            sub-step string (e.g., ``"7a"``).

    Returns:
        The parent step as an ``int``, or ``None`` when *step* is ``None``.
    """
    if step is None:
        return None
    if isinstance(step, int):
        return step
    m = re.match(r"^\d+", step)
    if m:
        return int(m.group())
    return None


def validate_progress_schema(data: dict) -> list[str]:
    """Validate a progress dict against the full schema.

    Checks all fields defined in ProgressSchema:
    - ``current_module`` (if present): must be int in range 1–11.
    - ``modules_completed`` (if present): must be list of ints each in 1–11.
    - ``track`` (if present): must be one of VALID_TRACKS.
    - ``preferences`` (if present): must be dict with str keys and str|bool values.
    - ``session_id`` (if present): must be a non-empty string.
    - ``started_at`` (if present): must be valid ISO 8601.
    - ``last_activity`` (if present): must be valid ISO 8601.
    - ``data_sources`` (if present): must be list of strings.
    - ``database_type`` (if present): must be a string.
    - ``current_step`` (if present): must be int, None, or a str matching a
      recognized sub-step format (dotted or lettered).
    - ``step_history`` (if present): must be a dict whose keys are string
      representations of integers 1–12 and whose values each contain
      ``last_completed_step`` and ``updated_at``.

    All fields are optional — legacy files that lack fields pass validation
    (backward compatible). The validator never short-circuits; all fields are
    checked and all errors collected.

    Returns:
        An empty list when the data is valid, or a list of human-readable
        error strings describing each violation.
    """
    errors: list[str] = []

    # --- current_module ---
    if "current_module" in data:
        cm = data["current_module"]
        if not isinstance(cm, int):
            errors.append(
                f"current_module must be an int, got {type(cm).__name__}"
            )
        elif cm not in MODULE_RANGE:
            errors.append(
                f"current_module value {cm} is out of range 1-11"
            )

    # --- modules_completed ---
    if "modules_completed" in data:
        mc = data["modules_completed"]
        if not isinstance(mc, list):
            errors.append(
                f"modules_completed must be a list, got {type(mc).__name__}"
            )
        else:
            for i, elem in enumerate(mc):
                if not isinstance(elem, int):
                    errors.append(
                        f"modules_completed contains non-int element at index {i}: "
                        f"got {type(elem).__name__}"
                    )
                elif elem not in MODULE_RANGE:
                    errors.append(
                        f"modules_completed contains value {elem} which is out of range 1-11"
                    )

    # --- track ---
    if "track" in data:
        tr = data["track"]
        if tr not in VALID_TRACKS:
            errors.append(
                f"track must be one of {VALID_TRACKS}, got {tr!r}"
            )

    # --- preferences ---
    if "preferences" in data:
        pref = data["preferences"]
        if not isinstance(pref, dict):
            errors.append(
                f"preferences must be a dict, got {type(pref).__name__}"
            )
        else:
            for key, val in pref.items():
                if not isinstance(key, str):
                    errors.append(
                        f"preferences key {key!r} must be a string"
                    )
                if not isinstance(val, (str, bool)):
                    errors.append(
                        f"preferences value for key {key!r} must be str or bool, "
                        f"got {type(val).__name__}"
                    )

    # --- session_id ---
    if "session_id" in data:
        sid = data["session_id"]
        if not isinstance(sid, str):
            errors.append(
                f"session_id must be a non-empty string, got {type(sid).__name__}"
            )
        elif sid == "":
            errors.append(
                "session_id must be a non-empty string, got ''"
            )

    # --- started_at ---
    if "started_at" in data:
        sa = data["started_at"]
        if not isinstance(sa, str):
            errors.append(
                f"started_at must be a string, got {type(sa).__name__}"
            )
        elif not _is_valid_iso8601(sa):
            errors.append(
                f"started_at is not valid ISO 8601: {sa!r}"
            )

    # --- last_activity ---
    if "last_activity" in data:
        la = data["last_activity"]
        if not isinstance(la, str):
            errors.append(
                f"last_activity must be a string, got {type(la).__name__}"
            )
        elif not _is_valid_iso8601(la):
            errors.append(
                f"last_activity is not valid ISO 8601: {la!r}"
            )

    # --- data_sources ---
    if "data_sources" in data:
        ds = data["data_sources"]
        if not isinstance(ds, list):
            errors.append(
                f"data_sources must be a list, got {type(ds).__name__}"
            )
        else:
            for i, elem in enumerate(ds):
                if not isinstance(elem, str):
                    errors.append(
                        f"data_sources contains non-string element at index {i}: "
                        f"got {type(elem).__name__}"
                    )

    # --- database_type ---
    if "database_type" in data:
        dt = data["database_type"]
        if not isinstance(dt, str):
            errors.append(
                f"database_type must be a string, got {type(dt).__name__}"
            )

    # --- current_step ---
    if "current_step" in data:
        cs = data["current_step"]
        if cs is None or isinstance(cs, int):
            pass  # valid
        elif isinstance(cs, str):
            if not _is_valid_sub_step_identifier(cs):
                errors.append(
                    f"current_step string '{cs}' does not match any recognized "
                    "sub-step format (expected '<digits>.<digits>' or '<digits><letter>')"
                )
        else:
            errors.append(
                f"current_step must be an int, str, or null, got {type(cs).__name__}"
            )

    # --- step_history ---
    if "step_history" in data:
        sh = data["step_history"]
        if not isinstance(sh, dict):
            errors.append(
                f"step_history must be a dict, got {type(sh).__name__}"
            )
        else:
            for key, entry in sh.items():
                # Key must be a string representation of an int 1-12
                try:
                    key_int = int(key)
                except (ValueError, TypeError):
                    errors.append(
                        f"step_history key '{key}' is not a valid integer string"
                    )
                    continue
                if key_int < 1 or key_int > 12:
                    errors.append(
                        f"step_history key '{key}' is out of range 1-12"
                    )

                # Value must be a dict with required fields
                if not isinstance(entry, dict):
                    errors.append(
                        f"step_history['{key}'] must be a dict, got {type(entry).__name__}"
                    )
                    continue

                if "last_completed_step" not in entry:
                    errors.append(
                        f"step_history['{key}'] missing 'last_completed_step'"
                    )
                else:
                    lcs = entry["last_completed_step"]
                    if isinstance(lcs, int):
                        pass  # valid
                    elif isinstance(lcs, str):
                        if not _is_valid_sub_step_identifier(lcs):
                            errors.append(
                                f"step_history['{key}'].last_completed_step string '{lcs}' "
                                "does not match any recognized sub-step format "
                                "(expected '<digits>.<digits>' or '<digits><letter>')"
                            )
                    else:
                        errors.append(
                            f"step_history['{key}'].last_completed_step must be an int or str, "
                            f"got {type(lcs).__name__}"
                        )

                if "updated_at" not in entry:
                    errors.append(
                        f"step_history['{key}'] missing 'updated_at'"
                    )
                elif not isinstance(entry["updated_at"], str):
                    errors.append(
                        f"step_history['{key}'].updated_at must be a string, "
                        f"got {type(entry['updated_at']).__name__}"
                    )
                elif not _is_valid_iso8601(entry["updated_at"]):
                    errors.append(
                        f"step_history['{key}'].updated_at is not valid ISO 8601: "
                        f"'{entry['updated_at']}'"
                    )

    return errors
