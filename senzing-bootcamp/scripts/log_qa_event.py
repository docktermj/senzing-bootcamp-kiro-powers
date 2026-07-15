#!/usr/bin/env python3
"""Senzing Bootcamp - Q&A Capture Helper.

Deterministically records the question/answer exchange to
``config/session_log.jsonl`` so the graduation recap and Q&A transcript are
complete. It is invoked by the two critical hooks on the **Q&A cadence** — never
per file write: the Stop hook (``ask-bootcamper``) records the outstanding
question read from ``config/.question_pending``; the UserPromptSubmit hook
(``review-bootcamper-input``) records the bootcamper's answer, paired to that
question by id.

Two modes:
    record-question   Log the pending question (idempotent; reads
                      ``config/.question_pending``). No-op when the file is
                      absent or the same pending question was already logged.
    record-answer     Log the bootcamper's answer (read from stdin), paired to
                      the pending question's id. Self-heals by logging the
                      question first when it was not already recorded.

A small sidecar (``config/.qa_capture.json``) holds the current pending
question's id and text hash so the answer can be paired to it and a
re-presented question is not double-logged.

All logic is non-blocking: any error is swallowed and the helper exits 0 so it
can never interrupt the bootcamp flow. Reuses ``session_logger`` for the event
schema; standard library only.

Usage:
    python3 senzing-bootcamp/scripts/log_qa_event.py record-question
    python3 senzing-bootcamp/scripts/log_qa_event.py record-answer < answer.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import session_logger  # noqa: E402

_PROGRESS_PATH: str = "config/bootcamp_progress.json"
_SESSION_LOG_PATH: str = "config/session_log.jsonl"
_QUESTION_PENDING_PATH: str = "config/.question_pending"
_SIDECAR_PATH: str = "config/.qa_capture.json"
_MIN_MODULE: int = 0
_MAX_MODULE: int = 11


def _read_current_module() -> int:
    """Read ``current_module`` from the progress file, clamped to 0-11.

    Returns:
        The current module number in 0-11. Defaults to ``0`` on any error
        (missing file, parse error, missing key, or non-int value).
    """
    try:
        raw = Path(_PROGRESS_PATH).read_text(encoding="utf-8")
        value = json.loads(raw)["current_module"]
        if isinstance(value, bool) or not isinstance(value, int):
            return _MIN_MODULE
        return max(_MIN_MODULE, min(_MAX_MODULE, value))
    except Exception:
        return _MIN_MODULE


def _read_pending_question() -> str | None:
    """Return the pending question text, or None when there is none.

    ``config/.question_pending`` stores the question type on line 1 and the full
    question text on lines 2+. Returns the joined, stripped text of lines 2+, or
    None when the file is absent or carries no question body.
    """
    try:
        raw = Path(_QUESTION_PENDING_PATH).read_text(encoding="utf-8")
    except Exception:
        return None
    lines = raw.splitlines()
    text = "\n".join(lines[1:]).strip()
    return text or None


def _read_sidecar() -> dict | None:
    """Return the parsed sidecar dict, or None when absent/unreadable."""
    try:
        return json.loads(Path(_SIDECAR_PATH).read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_sidecar(question_id: str, text_hash: str) -> None:
    """Write the pending-question sidecar (question id + text hash). Silent on error."""
    try:
        p = Path(_SIDECAR_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps({"question_id": question_id, "text_hash": text_hash}),
            encoding="utf-8",
        )
    except Exception:
        pass


def _clear_sidecar() -> None:
    """Delete the sidecar once its question is answered. Silent on error."""
    try:
        Path(_SIDECAR_PATH).unlink()
    except Exception:
        pass


def _text_hash(text: str) -> str:
    """Return a stable hex digest of the question text for dedupe."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _append_question(text: str, module: int) -> str:
    """Append a ``question`` event and return its generated question id."""
    qid = session_logger.generate_question_id()
    entry = session_logger.build_completion_entry(
        "question", module, {"text": text, "question_id": qid}
    )
    session_logger.append_completion_entry(_SESSION_LOG_PATH, entry)
    return qid


def _append_answer(text: str, question_id: str, module: int) -> None:
    """Append an ``answer`` event paired to *question_id*."""
    entry = session_logger.build_completion_entry(
        "answer", module, {"text": text, "question_id": question_id}
    )
    session_logger.append_completion_entry(_SESSION_LOG_PATH, entry)


def record_question() -> None:
    """Log the current pending question, idempotently.

    No-op when there is no pending question or when the same pending question
    (by text hash) was already logged — so a question re-presented across turns
    or session boundaries is never double-logged.
    """
    text = _read_pending_question()
    if not text:
        return
    digest = _text_hash(text)
    sidecar = _read_sidecar()
    if sidecar and sidecar.get("text_hash") == digest:
        return  # this pending question was already logged
    module = _read_current_module()
    qid = _append_question(text, module)
    _write_sidecar(qid, digest)


def record_answer(answer_text: str) -> None:
    """Log the bootcamper's answer, paired to the pending question.

    Uses the sidecar's question id when present. Self-heals when no question was
    logged yet by logging the pending question first (so the answer is never
    orphaned from a question). No-op when the answer is empty or there is no
    pending question to pair with. Clears the sidecar once the pair is recorded.
    """
    answer_text = answer_text.strip()
    if not answer_text:
        return
    module = _read_current_module()
    sidecar = _read_sidecar()
    if sidecar and sidecar.get("question_id"):
        qid = str(sidecar["question_id"])
    else:
        question_text = _read_pending_question()
        if not question_text:
            return  # no pending question — do not orphan-log an answer
        qid = _append_question(question_text, module)
    _append_answer(answer_text, qid, module)
    _clear_sidecar()


def main(argv: list[str] | None = None) -> int:
    """Dispatch the requested capture mode. Always returns 0 (non-blocking).

    Args:
        argv: Optional argument vector; defaults to ``sys.argv[1:]``.

    Returns:
        Always ``0`` — the helper swallows all errors so it can never block the
        bootcamp flow.
    """
    try:
        parser = argparse.ArgumentParser(
            description="Record Q&A events to config/session_log.jsonl."
        )
        sub = parser.add_subparsers(dest="mode", required=True)
        sub.add_parser("record-question", help="Log the pending question (idempotent).")
        sub.add_parser(
            "record-answer", help="Log the bootcamper's answer, read from stdin."
        )
        args = parser.parse_args(argv)

        if args.mode == "record-question":
            record_question()
        elif args.mode == "record-answer":
            answer = "" if sys.stdin.isatty() else sys.stdin.read()
            record_answer(answer)
    except SystemExit:
        # argparse errors (missing/invalid mode, --help) must not block the flow.
        return 0
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
