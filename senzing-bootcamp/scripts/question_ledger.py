#!/usr/bin/env python3
"""Senzing Bootcamp - Question Ledger helper.

Persisted record of every question asked of the bootcamper and whether it has
been answered, keyed by a stable Question_Key. The ledger is the durable source
of truth for the "ask each question at most once" guarantee across turns,
context compaction, and session resume.

The ledger is stored as JSONL (one JSON object per line) under ``config/``:

- ``config/question_ledger.jsonl`` (single-user)
- ``config/question_ledger_{member_id}.jsonl`` (co-located team mode)

Each line records ``{"key", "status", "ts"}`` where ``status`` is ``asked`` or
``answered`` and ``ts`` is an ISO 8601 UTC timestamp. ``answered`` supersedes
``asked`` for a given key (last-writer-wins).

Usage:
    python question_ledger.py record-asked  --key KEY [--member ID]
    python question_ledger.py mark-answered --key KEY [--member ID]
    python question_ledger.py is-answered   --key KEY [--member ID]
    python question_ledger.py get-pending   [--member ID]

Exit codes:
    record-asked / mark-answered / get-pending: 0 on success, 1 on error.
    is-answered: 0 when the key is answered, 1 when it is not (or on error).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_DIR = "config"
VALID_STATUSES: tuple[str, ...] = ("asked", "answered")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class LedgerEntry:
    """A single Question_Ledger record.

    Attributes:
        key: The stable Question_Key identifying the question.
        status: Either ``"asked"`` or ``"answered"``.
        ts: ISO 8601 UTC timestamp for when the status was recorded.
    """

    key: str
    status: str
    ts: str


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_ledger_path(
    member_id: str | None = None,
    config_dir: str = DEFAULT_CONFIG_DIR,
) -> Path:
    """Resolve the ledger file path, mirroring the preferences/progress convention.

    Args:
        member_id: Team member id for co-located team mode, or None for single-user.
        config_dir: Directory that holds the ledger file (default ``config``).

    Returns:
        Path to ``config/question_ledger.jsonl`` (single-user) or
        ``config/question_ledger_{member_id}.jsonl`` (team mode).
    """
    if member_id:
        return Path(config_dir) / f"question_ledger_{member_id}.jsonl"
    return Path(config_dir) / "question_ledger.jsonl"


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------


def _now_ts() -> str:
    """Return the current time as an ISO 8601 UTC string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# JSONL read / write (tolerant, stdlib-only)
# ---------------------------------------------------------------------------


def _read_entries(ledger_path: str | os.PathLike[str]) -> list[LedgerEntry]:
    """Read raw ledger entries from a JSONL file, tolerating problems.

    A missing or unreadable file is treated as empty. Individual malformed
    lines (invalid JSON, wrong shape, or unknown status) are skipped rather
    than raised. Never raises to the caller.

    Args:
        ledger_path: Path to the ledger JSONL file.

    Returns:
        List of valid LedgerEntry objects in file order.
    """
    entries: list[LedgerEntry] = []
    try:
        text = Path(ledger_path).read_text(encoding="utf-8")
    except (OSError, ValueError):
        # Missing/unreadable/undecodable file -> treat as empty.
        return entries

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except (ValueError, TypeError):
            # Malformed individual line -> skip, not fatal.
            continue
        if not isinstance(obj, dict):
            continue
        key = obj.get("key")
        status = obj.get("status")
        ts = obj.get("ts")
        if not isinstance(key, str) or not key:
            continue
        if status not in VALID_STATUSES:
            continue
        if not isinstance(ts, str):
            continue
        entries.append(LedgerEntry(key=key, status=status, ts=ts))
    return entries


def _collapse(entries: list[LedgerEntry]) -> dict[str, LedgerEntry]:
    """Collapse raw entries to the current state per key.

    Last-writer-wins per key, with ``answered`` always superseding ``asked``:
    once a key is answered, a later ``asked`` entry never regresses it.

    Args:
        entries: Raw entries in file order.

    Returns:
        Ordered mapping of key -> the winning LedgerEntry.
    """
    state: dict[str, LedgerEntry] = {}
    for entry in entries:
        existing = state.get(entry.key)
        if existing is None:
            state[entry.key] = entry
        elif entry.status == "answered":
            # answered supersedes asked; last answered wins.
            state[entry.key] = entry
        elif existing.status == "asked":
            # both asked -> last asked wins (keeps freshest ts).
            state[entry.key] = entry
        # existing answered + entry asked -> keep answered (no regression).
    return state


def read_state(ledger_path: str | os.PathLike[str]) -> dict[str, LedgerEntry]:
    """Read and collapse the ledger into current per-key state.

    Args:
        ledger_path: Path to the ledger JSONL file.

    Returns:
        Ordered mapping of key -> winning LedgerEntry (empty when missing/malformed).
    """
    return _collapse(_read_entries(ledger_path))


def _write_state(
    ledger_path: str | os.PathLike[str],
    state: dict[str, LedgerEntry],
) -> None:
    """Rewrite the ledger file cleanly from the collapsed state.

    Writes one JSON object per line, atomically via a temp file + os.replace.
    Recreates a clean file, discarding any previously malformed lines.

    Args:
        ledger_path: Path to the ledger JSONL file.
        state: Collapsed key -> LedgerEntry mapping to persist.
    """
    path = Path(ledger_path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    lines = [
        json.dumps({"key": e.key, "status": e.status, "ts": e.ts})
        for e in state.values()
    ]
    content = ("\n".join(lines) + "\n") if lines else ""

    tmp_path = ""
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(parent),
            prefix=".question_ledger_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
        except (OSError, IOError):
            os.close(fd)
            raise
        os.replace(tmp_path, path)
    except (OSError, IOError):
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Ledger operations
# ---------------------------------------------------------------------------


def record_asked(key: str, ledger_path: str | os.PathLike[str]) -> bool:
    """Record a Question_Key as asked (idempotent).

    Appends an ``asked`` entry only if the key is not already present as
    ``asked`` or ``answered``. Recording the same key twice does not create
    conflicting or duplicate state.

    Args:
        key: The Question_Key to record.
        ledger_path: Path to the ledger JSONL file.

    Returns:
        True if a new ``asked`` entry was written, False if the key was
        already present (no change).
    """
    state = read_state(ledger_path)
    if key in state:
        return False
    state[key] = LedgerEntry(key=key, status="asked", ts=_now_ts())
    _write_state(ledger_path, state)
    return True


def mark_answered(key: str, ledger_path: str | os.PathLike[str]) -> None:
    """Upsert a Question_Key to answered.

    ``answered`` supersedes ``asked``. Marking a key that is absent, asked, or
    already answered all converge on an ``answered`` state. A no-op when the key
    is already answered.

    Args:
        key: The Question_Key to mark answered.
        ledger_path: Path to the ledger JSONL file.
    """
    state = read_state(ledger_path)
    existing = state.get(key)
    if existing is not None and existing.status == "answered":
        return
    state[key] = LedgerEntry(key=key, status="answered", ts=_now_ts())
    _write_state(ledger_path, state)


def is_answered(key: str, ledger_path: str | os.PathLike[str]) -> bool:
    """Return True if the Question_Key is recorded as answered.

    Args:
        key: The Question_Key to query.
        ledger_path: Path to the ledger JSONL file.

    Returns:
        True when the key's collapsed status is ``answered``, else False.
    """
    entry = read_state(ledger_path).get(key)
    return entry is not None and entry.status == "answered"


def get_pending(ledger_path: str | os.PathLike[str]) -> list[str]:
    """Return the pending keys (asked but not answered).

    Args:
        ledger_path: Path to the ledger JSONL file.

    Returns:
        List of keys whose collapsed status is ``asked``, in file order.
    """
    return [e.key for e in read_state(ledger_path).values() if e.status == "asked"]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with the four ledger subcommands."""
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Question Ledger helper."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser(
        "record-asked", help="Record a Question_Key as asked (idempotent)."
    )
    record_parser.add_argument("--key", required=True, help="Question_Key to record.")
    record_parser.add_argument("--member", default=None, help="Team member id.")

    answer_parser = subparsers.add_parser(
        "mark-answered", help="Upsert a Question_Key to answered."
    )
    answer_parser.add_argument("--key", required=True, help="Question_Key to mark.")
    answer_parser.add_argument("--member", default=None, help="Team member id.")

    query_parser = subparsers.add_parser(
        "is-answered",
        help="Exit 0 if the Question_Key is answered, 1 otherwise.",
    )
    query_parser.add_argument("--key", required=True, help="Question_Key to query.")
    query_parser.add_argument("--member", default=None, help="Team member id.")

    pending_parser = subparsers.add_parser(
        "get-pending", help="Print pending (asked but not answered) key(s)."
    )
    pending_parser.add_argument("--member", default=None, help="Team member id.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error. For ``is-answered``, 0 means the
        key is answered and 1 means it is not.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        ledger_path = resolve_ledger_path(getattr(args, "member", None))

        if args.command == "record-asked":
            record_asked(args.key, ledger_path)
            return 0

        if args.command == "mark-answered":
            mark_answered(args.key, ledger_path)
            return 0

        if args.command == "is-answered":
            return 0 if is_answered(args.key, ledger_path) else 1

        if args.command == "get-pending":
            for key in get_pending(ledger_path):
                print(key)
            return 0
    except Exception as exc:  # noqa: BLE001 - degrade safely, never raise to caller
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
