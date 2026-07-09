#!/usr/bin/env python3
"""Senzing Bootcamp - License Record-Limit Detection.

A stdlib-only helper the agent runs after configuring a custom license in
Module 2. It reads the license JSON produced by ``SzProduct.get_license()``
(fed on stdin or as a file argument), extracts the active license's real
``recordLimit``, and persists it to ``config/bootcamp_progress.json`` under a
``license_record_limit`` field so every downstream capacity/sampling decision
(Modules 1, 4, 6, 8) can compare against the effective limit instead of the
hardcoded ~500-record evaluation figure.

Semantics of ``license_record_limit``:
    * ``0``            -> the license imposes no cap (unlimited records)
    * positive integer -> the license caps at that many records
    * ``null``/absent  -> not yet detected (evaluation fallback)

All Senzing SDK facts (``get_license()`` semantics, the meaning of
``recordLimit``) come from the Senzing MCP server; this helper only parses,
persists, and reports the value the agent captured.

Usage:
    # Read the license JSON from stdin and persist to the default progress file:
    szproduct-get-license | python detect_license_limit.py

    # Read from a file and point at an explicit progress path:
    python detect_license_limit.py license.json \\
        --progress config/bootcamp_progress.json

    # Explicitly read stdin with "-":
    python detect_license_limit.py - < license.json

Exit code 0 on success (the detected limit is printed to stdout); exit code 1
on error (malformed JSON, missing ``recordLimit`` key, or a non-integer value),
with a diagnostic on stderr. On error the existing progress file is never
modified.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The license JSON field holding the active record cap (0 == unlimited).
RECORD_LIMIT_KEY: str = "recordLimit"

# The progress-file field this helper persists the detected limit under.
PROGRESS_FIELD: str = "license_record_limit"

# Canonical progress-file path (relative to the workspace root), the CLI default.
DEFAULT_PROGRESS_PATH: str = "config/bootcamp_progress.json"


# ---------------------------------------------------------------------------
# Capacity-decision result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapacityDecision:
    """The license-aware sampling verdict for one capacity-decision context.

    Attributes:
        comparison_limit: The effective limit the dataset total was compared
            against — always the license's effective limit, never the
            hardcoded 500.
        recommend_sampling: ``True`` only when the effective limit is a positive
            cap the dataset genuinely exceeds. An unlimited license
            (``effective_limit == 0``) never recommends sampling for license
            reasons.
        hardcoded_500_not_used: Always ``True`` — the decision is driven by the
            effective limit and never by the literal 500.
    """

    comparison_limit: int
    recommend_sampling: bool
    hardcoded_500_not_used: bool


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_record_limit(license_json: dict) -> int:
    """Extract the active license's ``recordLimit`` from its JSON blob.

    Args:
        license_json: The license mapping returned by ``SzProduct.get_license()``
            (facts sourced from the Senzing MCP server). Must contain an integer
            ``recordLimit`` (``0`` means unlimited).

    Returns:
        The record limit as an integer (``0`` means the license imposes no cap).

    Raises:
        ValueError: If the ``recordLimit`` key is missing, or its value is not a
            non-negative integer (booleans and non-integers are rejected).
    """
    if not isinstance(license_json, dict):
        raise ValueError(
            f"license JSON must be an object, got {type(license_json).__name__}"
        )

    if RECORD_LIMIT_KEY not in license_json:
        raise ValueError(
            f"license JSON is missing the required '{RECORD_LIMIT_KEY}' field; "
            "cannot determine the active license limit"
        )

    value = license_json[RECORD_LIMIT_KEY]

    # bool is a subclass of int — reject it explicitly so True/False never pass.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"'{RECORD_LIMIT_KEY}' must be an integer, got "
            f"{type(value).__name__}: {value!r}"
        )

    if value < 0:
        raise ValueError(
            f"'{RECORD_LIMIT_KEY}' must be non-negative (0 == unlimited), got {value}"
        )

    return value


# ---------------------------------------------------------------------------
# Progress-file read/write (preserves all existing fields)
# ---------------------------------------------------------------------------


def _read_progress(progress_path: str) -> dict:
    """Read the progress file, returning an empty dict when it does not exist.

    Args:
        progress_path: Path to the progress JSON file.

    Returns:
        The parsed progress mapping, or an empty dict when the file is absent or
        empty.

    Raises:
        ValueError: If the file exists but does not contain valid JSON.
    """
    path = Path(progress_path)
    if not path.is_file():
        return {}
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return {}
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError(
            f"progress file '{progress_path}' must contain a JSON object, "
            f"got {type(data).__name__}"
        )
    return data


def _write_progress(progress_path: str, data: dict) -> None:
    """Write the progress dict back with 2-space indent and a trailing newline.

    Mirrors the ``progress_utils`` writer so files stay byte-consistent across
    helpers. Creates the parent directory when it does not exist.

    Args:
        progress_path: Path to the progress JSON file.
        data: The progress mapping to serialize.
    """
    path = Path(progress_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def persist_license_limit(limit: int, progress_path: str) -> None:
    """Persist the detected ``recordLimit`` to the progress file.

    Reads the existing progress file (creating it when absent), sets the
    ``license_record_limit`` field to ``limit``, and writes it back. Every
    pre-existing field is preserved verbatim — only ``license_record_limit`` is
    added or updated.

    Args:
        limit: The detected record limit (``0`` means unlimited).
        progress_path: Path to ``bootcamp_progress.json``.
    """
    data = _read_progress(progress_path)
    data[PROGRESS_FIELD] = limit
    _write_progress(progress_path, data)


def read_license_limit(progress_path: str) -> int | None:
    """Read the persisted ``license_record_limit`` from the progress file.

    Args:
        progress_path: Path to ``bootcamp_progress.json``.

    Returns:
        The persisted record limit, or ``None`` when the field is absent or the
        file does not exist (the evaluation-fallback signal for downstream
        modules).
    """
    try:
        data = _read_progress(progress_path)
    except ValueError:
        return None
    value = data.get(PROGRESS_FIELD)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


# ---------------------------------------------------------------------------
# Capacity decision (license-aware, never the hardcoded 500)
# ---------------------------------------------------------------------------


def evaluate_capacity_decision(dataset_total: int, effective_limit: int) -> CapacityDecision:
    """Decide whether to recommend sampling using the effective license limit.

    The decision is driven entirely by ``effective_limit`` — never the hardcoded
    500. An ``effective_limit`` of ``0`` means the license imposes no cap, so
    sampling is never recommended for license reasons; a positive limit
    recommends sampling only when the dataset genuinely exceeds it.

    Args:
        dataset_total: The dataset's total record count.
        effective_limit: The active license's effective record limit
            (``0`` means unlimited).

    Returns:
        A :class:`CapacityDecision` whose ``comparison_limit`` equals
        ``effective_limit`` and whose ``recommend_sampling`` is
        ``effective_limit > 0 and dataset_total > effective_limit``.
    """
    recommend_sampling = effective_limit > 0 and dataset_total > effective_limit
    return CapacityDecision(
        comparison_limit=effective_limit,
        recommend_sampling=recommend_sampling,
        # The verdict is driven by effective_limit above; the literal 500 is
        # never consulted, so this invariant marker is unconditionally True.
        hardcoded_500_not_used=True,
    )


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def _read_license_text(license_file: str | None) -> str:
    """Read the license JSON text from a file argument or stdin.

    Args:
        license_file: A path to the license JSON file, ``"-"`` for stdin, or
            ``None`` (also stdin).

    Returns:
        The raw license JSON text.

    Raises:
        OSError: If the named file cannot be read.
    """
    if license_file in (None, "-"):
        return sys.stdin.read()
    return Path(license_file).read_text(encoding="utf-8")


def _warn(message: str) -> None:
    """Print an error diagnostic to stderr.

    Args:
        message: The diagnostic text.
    """
    print(f"detect_license_limit: error: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: read license JSON -> parse -> persist -> print limit.

    Reads the license JSON (from a file argument or stdin), extracts
    ``recordLimit``, persists it to the progress file under
    ``license_record_limit``, and prints the detected limit to stdout for the
    agent to consume. On malformed JSON, a missing ``recordLimit`` key, or a
    non-integer value, it warns to stderr and returns 1 without touching the
    progress file.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` on success, ``1`` on error.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Detect the active Senzing license's recordLimit and persist it to "
            "config/bootcamp_progress.json for license-aware capacity decisions."
        ),
    )
    parser.add_argument(
        "license_file",
        nargs="?",
        default=None,
        help="Path to the license JSON file, or '-' for stdin (default: stdin)",
    )
    parser.add_argument(
        "--progress",
        default=DEFAULT_PROGRESS_PATH,
        help=f"Path to bootcamp progress (default: {DEFAULT_PROGRESS_PATH})",
    )
    args = parser.parse_args(argv)

    # Read the license JSON text.
    try:
        raw_text = _read_license_text(args.license_file)
    except OSError as exc:
        _warn(f"could not read license JSON: {exc}")
        return 1

    # Parse the JSON.
    try:
        license_json = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        _warn(f"license input is not valid JSON: {exc}")
        return 1

    # Extract the recordLimit (missing key / non-integer value -> error).
    try:
        limit = parse_record_limit(license_json)
    except ValueError as exc:
        _warn(str(exc))
        return 1

    # Persist to the progress file (existing fields preserved).
    try:
        persist_license_limit(limit, args.progress)
    except (OSError, ValueError) as exc:
        _warn(f"could not persist license limit to '{args.progress}': {exc}")
        return 1

    # Report the detected limit for agent consumption: a bare integer on stdout
    # (easy to capture programmatically), with a human note on stderr.
    print(limit)
    if limit == 0:
        print("detect_license_limit: recordLimit 0 == unlimited (no record cap)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
