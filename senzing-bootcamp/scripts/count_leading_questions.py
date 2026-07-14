#!/usr/bin/env python3
"""Codify the precise 👉 leading-question counting rule for the Stop-boundary
self-audit (conversational-self-audit-hook, Requirements 1.1 and 1.5).

This module is the single, deterministic source of truth for *how many* 👉
leading questions a rendered assistant turn contains. The Stop-boundary
Leading-Question Count Audit (folded into the ``ask-bootcamper`` hook) builds on
this rule: exactly one → silent pass, zero → "missing leading question", two or
more → "multiple leading questions". Keeping the rule here (as importable,
testable functions) — rather than only as prose in the hook prompt — is what
makes the audit deterministic and lets the property/example tests exercise it.

Counting rule (authoritative — mirrors design.md "Counting rule")
-----------------------------------------------------------------
A **Leading_Question line** is a line whose first non-whitespace,
non-blockquote, non-bold content begins with 👉. Concretely, for each line we:

1. Skip lines inside fenced code blocks (``` or ~~~) — illustrative code and
   verbatim example turns rendered as code never count.
2. Blank out inline code spans (`` `...` ``) so a 👉 shown inside backticks
   does not count.
3. Strip leading whitespace.
4. Treat a line whose first content is a blockquote marker (``>``) as *quoted*
   material (an example of a prior turn) — it has no non-blockquote content, so
   its 👉 does not count.
5. Strip a single leading bold marker (``**``) so ``**👉 …**`` still counts.
6. Count the line iff the remaining content begins with 👉.

The internal control markers 🛑 (STOP) and ⛔ (mandatory gate) are never 👉, so
they are never counted as leading questions; they are documented here only to
make the exclusion explicit.

Cross-check (Requirement 1.5 support)
-------------------------------------
A well-formed Yielding_Turn records exactly one pending question in
``config/.question_pending`` (question type on line 1, question text on lines
2+). :func:`crosscheck_pending_question` compares the rendered 👉 count against
that pending-question state; a mismatch (e.g. zero 👉 while a question is
pending, or two-plus 👉 for a single pending question) is itself a signal the
audit can act on.

Usage:
    # Count 👉 leading questions in a rendered turn read from a file:
    python senzing-bootcamp/scripts/count_leading_questions.py turn.md

    # Read the rendered turn from stdin and cross-check the pending sentinel:
    cat turn.md | python senzing-bootcamp/scripts/count_leading_questions.py - \
        --pending config/.question_pending

Exit codes:
    0 — Count (and optional cross-check) produced successfully.
    1 — Usage error (e.g. named input file not found).

Only Python standard-library features are used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Markers (match the codepoints used across the bootcamp steering + hooks)
# ---------------------------------------------------------------------------

#: 👉 — the pointer prefix marking a bootcamper-facing leading question.
POINTER_INDICATOR: str = "\U0001f449"

#: 🛑 — the internal end-of-turn STOP marker (never a leading question).
STOP_MARKER: str = "\U0001f6d1"

#: ⛔ — the internal mandatory-gate marker (never a leading question).
HARD_GATE_MARKER: str = "\u26d4"

#: CommonMark strong-emphasis (bold) marker.
BOLD_MARKER: str = "**"

#: Default location of the pending-question sentinel (relative to CWD/``config``).
QUESTION_PENDING_PATH: str = "config/.question_pending"

# Inline code spans: double-backtick spans first, then single-backtick spans.
_INLINE_CODE_RE = re.compile(r"``[^`]*``|`[^`]*`")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CrossCheckResult:
    """Outcome of comparing the rendered 👉 count against the pending sentinel.

    Attributes:
        rendered_count: The 👉 leading-question count in the rendered turn.
        pending_present: True when ``config/.question_pending`` records exactly
            one outstanding question.
        consistent: True when the rendered count agrees with the pending state
            (count == 1 with a pending question, or count == 0 with none).
        signal: A human-readable description of the mismatch, or ``None`` when
            the rendered count and the pending state agree.
    """

    rendered_count: int
    pending_present: bool
    consistent: bool
    signal: str | None


# ---------------------------------------------------------------------------
# Counting rule
# ---------------------------------------------------------------------------


def _is_fence_line(line: str) -> bool:
    """Report whether a line opens or closes a fenced code block.

    Args:
        line: The raw line of text.

    Returns:
        True if the line (after leading whitespace) begins a CommonMark code
        fence (three backticks or three tildes).
    """
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def _mask_inline_code(line: str) -> str:
    """Blank out inline code spans so a 👉 inside backticks is not counted.

    Args:
        line: The raw line of text.

    Returns:
        The line with every backtick-delimited span replaced by a single
        space, preserving the position of surrounding content.
    """
    return _INLINE_CODE_RE.sub(" ", line)


def is_leading_question_line(line: str) -> bool:
    """Report whether a single line is a 👉 leading-question line.

    Applies the counting rule to one line, assuming the caller has already
    excluded lines inside fenced code blocks. The line qualifies when its first
    non-whitespace, non-blockquote, non-bold content begins with 👉. Inline
    code spans are blanked first; blockquoted lines (quoted prior-turn
    examples) never qualify.

    Args:
        line: The raw line of text (not inside a fenced code block).

    Returns:
        True if the line is a 👉 leading-question line, otherwise False.
    """
    stripped = _mask_inline_code(line).lstrip()
    if not stripped:
        return False
    # Blockquoted content is quoted material (e.g. an example of a prior turn):
    # it has no non-blockquote content, so its 👉 is never a live leading
    # question.
    if stripped.startswith(">"):
        return False
    # Strip a single leading bold marker so ``**👉 …**`` still qualifies.
    if stripped.startswith(BOLD_MARKER):
        stripped = stripped[len(BOLD_MARKER):].lstrip()
    return stripped.startswith(POINTER_INDICATOR)


def count_leading_questions(text: str) -> int:
    """Count 👉 leading questions in a rendered turn per the counting rule.

    Walks the text line by line, skipping fenced code blocks, and counts every
    line whose first non-whitespace, non-blockquote, non-bold content begins
    with 👉. Inline code, blockquoted (quoted) 👉, and the internal 🛑/⛔
    markers are all excluded.

    Args:
        text: The full rendered assistant turn.

    Returns:
        The number of 👉 leading-question lines in the turn.
    """
    count = 0
    in_fence = False
    for line in text.splitlines():
        if _is_fence_line(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if is_leading_question_line(line):
            count += 1
    return count


def classify_leading_question_count(count: int) -> str:
    """Classify a 👉 count against the One_Question_Invariant.

    Args:
        count: The 👉 leading-question count from
            :func:`count_leading_questions`.

    Returns:
        ``"pass"`` when the count is exactly one, ``"missing"`` when it is
        zero, and ``"multiple"`` when it is two or more.
    """
    if count == 1:
        return "pass"
    if count == 0:
        return "missing"
    return "multiple"


# ---------------------------------------------------------------------------
# config/.question_pending cross-check
# ---------------------------------------------------------------------------


def read_pending_question(path: str | Path = QUESTION_PENDING_PATH) -> str | None:
    """Return the outstanding pending-question text, or None when there is none.

    ``config/.question_pending`` stores the question type on line 1 and the full
    question text on lines 2+ (matching ``log_qa_event.py``). Returns the
    joined, stripped text of lines 2+, or None when the file is absent,
    unreadable, or carries no question body.

    Args:
        path: Path to the pending-question sentinel.

    Returns:
        The pending question text, or None when no question is pending.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except Exception:
        return None
    lines = raw.splitlines()
    text = "\n".join(lines[1:]).strip()
    return text or None


def pending_question_present(path: str | Path = QUESTION_PENDING_PATH) -> bool:
    """Report whether exactly one question is recorded as pending.

    Args:
        path: Path to the pending-question sentinel.

    Returns:
        True when ``config/.question_pending`` records an outstanding question.
    """
    return read_pending_question(path) is not None


def crosscheck_pending_question(rendered_count: int, pending_present: bool) -> CrossCheckResult:
    """Cross-check the rendered 👉 count against the pending-question state.

    A well-formed Yielding_Turn ends with exactly one 👉 and records exactly one
    pending question. Consistency therefore means either (count == 1 with a
    pending question) or (count == 0 with no pending question). Any other
    combination is a signal the audit can act on.

    Args:
        rendered_count: The 👉 count from :func:`count_leading_questions`.
        pending_present: Whether a pending question is recorded (see
            :func:`pending_question_present`).

    Returns:
        A :class:`CrossCheckResult` describing consistency and any mismatch
        signal.
    """
    if pending_present:
        if rendered_count == 1:
            return CrossCheckResult(rendered_count, pending_present, True, None)
        if rendered_count == 0:
            signal = (
                "A question is pending in config/.question_pending but the rendered "
                "turn shows no 👉 leading question (dead-end / lost question)."
            )
        else:
            signal = (
                f"A single question is pending in config/.question_pending but the "
                f"rendered turn shows {rendered_count} 👉 leading questions "
                "(multiple leading questions)."
            )
        return CrossCheckResult(rendered_count, pending_present, False, signal)

    # No pending question recorded.
    if rendered_count == 0:
        return CrossCheckResult(rendered_count, pending_present, True, None)
    if rendered_count == 1:
        signal = (
            "The rendered turn shows one 👉 leading question but no pending question "
            "is recorded in config/.question_pending."
        )
    else:
        signal = (
            f"The rendered turn shows {rendered_count} 👉 leading questions but no "
            "pending question is recorded in config/.question_pending."
        )
    return CrossCheckResult(rendered_count, pending_present, False, signal)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_input_text(source: str) -> str:
    """Read the rendered turn from a file path or stdin.

    Args:
        source: A file path, or ``"-"`` to read from stdin.

    Returns:
        The rendered turn text.

    Raises:
        FileNotFoundError: When ``source`` names a file that does not exist.
    """
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Count 👉 leading questions in a rendered turn and optionally cross-check.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Count 👉 leading questions in a rendered assistant turn per the "
            "conversational self-audit counting rule."
        ),
    )
    parser.add_argument(
        "input",
        help="Path to the rendered turn, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--pending",
        metavar="PATH",
        default=None,
        help=(
            "Path to config/.question_pending; when given, cross-check the "
            "rendered count against the pending-question state."
        ),
    )
    args = parser.parse_args(argv)

    try:
        text = _read_input_text(args.input)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    count = count_leading_questions(text)
    result: dict[str, object] = {
        "rendered_count": count,
        "classification": classify_leading_question_count(count),
    }

    if args.pending is not None:
        present = pending_question_present(args.pending)
        crosscheck = crosscheck_pending_question(count, present)
        result["crosscheck"] = asdict(crosscheck)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
