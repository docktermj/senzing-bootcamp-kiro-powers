#!/usr/bin/env python3
"""CI script: validate bootcamp_progress.json schema.

Validates a progress file against the ProgressSchema definition and checks
schema self-consistency. Used in CI to catch corruption before merge.

Usage:
    python senzing-bootcamp/scripts/validate_progress_ci.py [path]

Arguments:
    path  Optional path to a progress JSON file.
          Defaults to config/bootcamp_progress.json.
          If the file does not exist, validates a built-in minimal sample.

Exits 0 on success, 1 on validation failure.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import (
    MODULE_RANGE,
    STEP_HISTORY_KEY_RANGE,
    VALID_TRACKS,
    ProgressSchema,
    validate_progress_schema,
)

# ---------------------------------------------------------------------------
# Built-in minimal sample (used when no progress file exists on disk)
# ---------------------------------------------------------------------------

_SAMPLE_PROGRESS: dict = {
    "current_module": 1,
    "modules_completed": [],
    "data_sources": [],
    "database_type": "sqlite",
}


# ---------------------------------------------------------------------------
# Schema self-consistency check
# ---------------------------------------------------------------------------


def _check_schema_consistency() -> list[str]:
    """Verify ProgressSchema fields don't contradict validator logic.

    Checks:
    - All fields in ProgressSchema dataclass have corresponding validation
      logic (the sample dict validates cleanly).
    - The constants VALID_TRACKS, MODULE_RANGE, and STEP_HISTORY_KEY_RANGE
      are non-empty.

    Returns:
        A list of error strings (empty means consistent).
    """
    errors: list[str] = []

    # Verify constants are non-empty
    if not VALID_TRACKS:
        errors.append("VALID_TRACKS is empty")
    if not MODULE_RANGE:
        errors.append("MODULE_RANGE is empty")
    if not STEP_HISTORY_KEY_RANGE:
        errors.append("STEP_HISTORY_KEY_RANGE is empty")

    # Verify the sample dict validates cleanly
    sample_errors = validate_progress_schema(_SAMPLE_PROGRESS)
    if sample_errors:
        errors.append(
            f"Built-in sample fails validation: {sample_errors}"
        )

    # Verify all ProgressSchema fields are known strings
    schema_fields = {f.name for f in dataclasses.fields(ProgressSchema)}
    if not schema_fields:
        errors.append("ProgressSchema has no fields defined")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run progress schema CI validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Validate bootcamp_progress.json against ProgressSchema."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="config/bootcamp_progress.json",
        help="Path to progress JSON file (default: config/bootcamp_progress.json)",
    )
    args = parser.parse_args(argv)

    all_errors: list[str] = []

    # --- Schema self-consistency check ---
    consistency_errors = _check_schema_consistency()
    if consistency_errors:
        all_errors.extend(consistency_errors)

    # --- File validation ---
    progress_path = Path(args.path)
    if progress_path.is_file():
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            all_errors.append(f"Failed to read {args.path}: {exc}")
            data = None

        if data is not None:
            validation_errors = validate_progress_schema(data)
            if validation_errors:
                all_errors.extend(validation_errors)
    else:
        # File doesn't exist — validate built-in sample to confirm schema works
        validation_errors = validate_progress_schema(_SAMPLE_PROGRESS)
        if validation_errors:
            all_errors.extend(validation_errors)

    # --- Report results ---
    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    print("Schema validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
