#!/usr/bin/env python3
"""Senzing Bootcamp - Q&A Transcript Renderer.

Reads ``question`` and ``answer`` completion events from
``config/session_log.jsonl`` (the schema defined in ``session_logger.py``) and
renders an ordered, replayable Markdown transcript to
``docs/bootcamp_transcript.md``.

Questions and their paired answers are grouped by module in the order they
occurred, unanswered questions are marked, and answers with no matching question
are rendered in a clearly labeled section.

Usage:
    python scripts/generate_transcript.py
    python scripts/generate_transcript.py --log config/session_log.jsonl \\
        --output docs/bootcamp_transcript.md

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH_DEFAULT: str = "config/session_log.jsonl"
OUTPUT_PATH_DEFAULT: str = "docs/bootcamp_transcript.md"

# Completion event types this renderer cares about.
QA_EVENT_TYPES: set[str] = {"question", "answer"}

# Placeholder substituted for any detected secret value.
REDACTION_PLACEHOLDER: str = "[REDACTED]"

# Key names that signal the following value is a secret.
_SECRET_KEY_NAMES: str = (
    r"api[_-]?key|access[_-]?key|secret[_-]?key|secret|passwd|password|pwd|token|key"
)

# Ordered (compiled pattern, replacement) pairs applied by ``redact_secrets``.
# Order matters: more specific patterns run before broad ones.
_REDACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    # Connection strings with embedded credentials:
    #   scheme://user:secret@host -> scheme://user:[REDACTED]@host
    (
        re.compile(r"(?P<scheme>[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@]+:)[^\s@/]+(?P<at>@)"),
        rf"\g<scheme>{REDACTION_PLACEHOLDER}\g<at>",
    ),
    # Bearer tokens: "Bearer <token>" -> "Bearer [REDACTED]"
    (
        re.compile(r"(?P<prefix>\bBearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        rf"\g<prefix>{REDACTION_PLACEHOLDER}",
    ),
    # Secret-looking key/value pairs (e.g. api_key=..., token: ..., password="...").
    (
        re.compile(
            rf"(?P<key>\b(?:{_SECRET_KEY_NAMES})\b\s*[=:]\s*)"
            r"(?P<quote>[\"']?)[^\s\"',;]+(?P=quote)",
            re.IGNORECASE,
        ),
        rf"\g<key>\g<quote>{REDACTION_PLACEHOLDER}\g<quote>",
    ),
    # AWS-style access key IDs (a recognizable prefix followed by uppercase/digits).
    (
        re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA)[0-9A-Z]{12,}\b"),
        REDACTION_PLACEHOLDER,
    ),
    # Generic high-entropy base64-ish secrets: long runs containing both a
    # letter and a digit (avoids redacting ordinary prose words).
    (
        re.compile(
            r"\b(?=[A-Za-z0-9+/\-_]*[A-Za-z])(?=[A-Za-z0-9+/\-_]*[0-9])"
            r"[A-Za-z0-9+/\-_]{32,}={0,2}\b"
        ),
        REDACTION_PLACEHOLDER,
    ),
]


@dataclass
class QAPair:
    """A question paired with its answer (if any).

    Attributes:
        question_id: The id linking the question to its answer.
        module: Module number the question belongs to.
        question_text: The displayed question text.
        answer_text: The bootcamper's response text, or None when unanswered.
        q_timestamp: ISO 8601 timestamp of the question event.
        a_timestamp: ISO 8601 timestamp of the answer event, or None.
    """

    question_id: str
    module: int
    question_text: str
    answer_text: str | None
    q_timestamp: str
    a_timestamp: str | None


@dataclass
class TranscriptModel:
    """The in-memory model rendered into the transcript document.

    Attributes:
        pairs: Q&A pairs ordered by question timestamp / file order.
        orphan_answers: Answer events with no matching question.
        question_count: Total number of question events.
        answered_count: Number of questions that have a paired answer.
    """

    pairs: list[QAPair] = field(default_factory=list)
    orphan_answers: list[dict] = field(default_factory=list)
    question_count: int = 0
    answered_count: int = 0


def read_events(log_path: str) -> list[dict]:
    """Read Q&A events from a JSONL session log.

    Skips lines that are not valid JSON or are not ``question``/``answer``
    completion events, and never raises on a bad line.

    Args:
        log_path: Path to the JSONL session log.

    Returns:
        A list of valid Q&A event dicts in file order.
    """
    path = Path(log_path)
    if not path.exists():
        return []

    events: list[dict] = []
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("event_type") in QA_EVENT_TYPES:
                    events.append(obj)
    except OSError:
        return events
    return events


def build_model(events: list[dict]) -> TranscriptModel:
    """Build a TranscriptModel from a list of Q&A events.

    Orders events by ``timestamp`` with stable file-order tie-breaking, pairs
    answers to questions by ``question_id``, marks unanswered questions, and
    collects orphan answers.

    Args:
        events: Valid Q&A event dicts (in file order).

    Returns:
        The assembled ``TranscriptModel``.
    """
    # Stable-sort by timestamp; Python's sort preserves file order on ties.
    ordered = sorted(events, key=lambda e: e.get("timestamp", ""))

    model = TranscriptModel()
    # Map question_id -> list of QAPair objects (in order) so an answer can be
    # paired to the first still-unanswered question sharing that id.
    by_id: dict[str, list[QAPair]] = {}

    for event in ordered:
        event_type = event.get("event_type")
        data = event.get("data") or {}
        question_id = data.get("question_id", "")
        timestamp = event.get("timestamp", "")

        if event_type == "question":
            pair = QAPair(
                question_id=question_id,
                module=event.get("module", 0),
                question_text=data.get("text", ""),
                answer_text=None,
                q_timestamp=timestamp,
                a_timestamp=None,
            )
            model.pairs.append(pair)
            model.question_count += 1
            by_id.setdefault(question_id, []).append(pair)
        elif event_type == "answer":
            # Pair to the first unanswered question with this question_id.
            candidates = by_id.get(question_id, [])
            target = next((p for p in candidates if p.answer_text is None), None)
            if target is None:
                model.orphan_answers.append(event)
            else:
                target.answer_text = data.get("text", "")
                target.a_timestamp = timestamp
                model.answered_count += 1

    return model


def redact_secrets(text: str) -> str:
    """Redact token / connection-string / API-key patterns in answer text.

    Args:
        text: The answer text to scrub.

    Returns:
        The text with any secret-looking values replaced.
    """
    if not text:
        return text
    redacted = text
    for pattern, replacement in _REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def render_markdown(model: TranscriptModel, generated_at: str) -> str:
    """Render a TranscriptModel to a Markdown document.

    Args:
        model: The transcript model to render.
        generated_at: ISO 8601 generation timestamp for the metadata header.

    Returns:
        The complete Markdown document as a string.
    """
    lines: list[str] = []

    # Metadata header (Req 4.7): title, generation timestamp, and totals.
    lines.append("# Bootcamp Q&A Transcript")
    lines.append("")
    lines.append(f"- **Generated at:** {generated_at}")
    lines.append(f"- **Total questions:** {model.question_count}")
    lines.append(f"- **Answered questions:** {model.answered_count}")
    lines.append("")

    # Group pairs by module, preserving first-appearance order (Req 4.4).
    module_order: list[int] = []
    pairs_by_module: dict[int, list[QAPair]] = {}
    for pair in model.pairs:
        if pair.module not in pairs_by_module:
            pairs_by_module[pair.module] = []
            module_order.append(pair.module)
        pairs_by_module[pair.module].append(pair)

    # One "## Module N" heading per module with at least one pair (Req 4.4).
    for module in module_order:
        lines.append(f"## Module {module}")
        lines.append("")
        for pair in pairs_by_module[module]:
            # Question text (Req 4.5).
            lines.append(f"**Q:** {pair.question_text}")
            lines.append("")
            # Answer text or unanswered marker (Req 4.5, 4.6).
            if pair.answer_text is None:
                lines.append("**A:** *(unanswered)*")
            else:
                # Defensive redaction before rendering (Req 8.2).
                lines.append(f"**A:** {redact_secrets(pair.answer_text)}")
            lines.append("")

    # Orphan answers in a clearly labeled section (Req 5.4).
    if model.orphan_answers:
        lines.append("## Unmatched answers")
        lines.append("")
        lines.append(
            "_These answers reference a question that was not found in the log._"
        )
        lines.append("")
        for event in model.orphan_answers:
            data = event.get("data") or {}
            answer_text = data.get("text", "")
            lines.append(f"**A:** {redact_secrets(answer_text)}")
            lines.append("")

    # Trim a trailing blank line for a clean single trailing newline.
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace with ``log`` and ``output`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Render an ordered Q&A transcript from session_log.jsonl into a "
            "Markdown document."
        ),
    )
    parser.add_argument(
        "--log",
        default=LOG_PATH_DEFAULT,
        help=f"Path to the JSONL session log (default: {LOG_PATH_DEFAULT}).",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_PATH_DEFAULT,
        help=f"Path to write the transcript (default: {OUTPUT_PATH_DEFAULT}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the transcript renderer.

    Reads Q&A events from the session log, builds the transcript model, and
    writes the rendered Markdown to the output path by full overwrite (never
    appending to stale content). When there are no Q&A events (including a
    missing log file), emits a warning to stderr and does not write a
    misleading transcript file.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success (including the no-events case), 1 on error.
    """
    args = parse_args(argv)

    events = read_events(args.log)
    if not events:
        print(
            f"No Q&A events found in '{args.log}'; no transcript written.",
            file=sys.stderr,
        )
        return 0

    model = build_model(events)
    generated_at = datetime.now(timezone.utc).isoformat()
    document = render_markdown(model, generated_at)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Full regeneration: overwrite any stale content rather than appending (Req 7.3).
    output_path.write_text(document, encoding="utf-8")

    print(f"Wrote transcript to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
