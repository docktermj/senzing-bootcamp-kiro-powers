#!/usr/bin/env python3
"""CI script: validate bootcamp_preferences.yaml schema.

Validates a preferences file against the PreferencesSchema definition and checks
schema self-consistency. Used in CI to catch corruption before merge.

Usage:
    python senzing-bootcamp/scripts/validate_preferences_ci.py [path]

Arguments:
    path  Optional path to a preferences YAML file.
          Defaults to config/bootcamp_preferences.yaml.
          If the file does not exist, validates a built-in minimal sample.

Exits 0 on success, 1 on validation failure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import (
    KNOWN_TOP_LEVEL_KEYS,
    parse_yaml,
    validate_preferences_schema,
)

# ---------------------------------------------------------------------------
# Built-in minimal sample (used when no preferences file exists on disk)
# ---------------------------------------------------------------------------

_SAMPLE_PREFERENCES: dict = {
    "database_type": "sqlite",
}


# ---------------------------------------------------------------------------
# Schema self-consistency check
# ---------------------------------------------------------------------------


def _check_schema_consistency() -> list[str]:
    """Verify PreferencesSchema fields don't contradict validator logic.

    Checks:
    - KNOWN_TOP_LEVEL_KEYS is non-empty.
    - The built-in sample dict validates cleanly.

    Returns:
        A list of error strings (empty means consistent).
    """
    errors: list[str] = []

    # Verify KNOWN_TOP_LEVEL_KEYS is non-empty
    if not KNOWN_TOP_LEVEL_KEYS:
        errors.append("KNOWN_TOP_LEVEL_KEYS is empty")

    # Verify the sample dict validates cleanly
    sample_errors = validate_preferences_schema(_SAMPLE_PREFERENCES)
    if sample_errors:
        errors.append(
            f"Built-in sample fails validation: {sample_errors}"
        )

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run preferences schema CI validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Validate bootcamp_preferences.yaml against PreferencesSchema."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="config/bootcamp_preferences.yaml",
        help="Path to preferences YAML file (default: config/bootcamp_preferences.yaml)",
    )
    args = parser.parse_args(argv)

    all_errors: list[str] = []

    # --- Schema self-consistency check ---
    consistency_errors = _check_schema_consistency()
    if consistency_errors:
        all_errors.extend(consistency_errors)

    # --- File validation ---
    preferences_path = Path(args.path)
    if preferences_path.is_file():
        try:
            text = preferences_path.read_text(encoding="utf-8")
            data = parse_yaml(text)
        except (ValueError, OSError) as exc:
            all_errors.append(f"Failed to read {args.path}: {exc}")
            data = None

        if data is not None:
            validation_errors = validate_preferences_schema(data)
            if validation_errors:
                all_errors.extend(validation_errors)
    else:
        # File doesn't exist — validate built-in sample to confirm schema works
        validation_errors = validate_preferences_schema(_SAMPLE_PREFERENCES)
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
