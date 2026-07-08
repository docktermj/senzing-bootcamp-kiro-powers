#!/usr/bin/env python3
"""Validate agent behavior rules compliance in steering files.

Checks steering file content against the four agent behavior rules:
1. Honor explicit continuation requests (no pause/stop/defer language)
2. Acknowledge bootcamper responses (length, substantiveness, position)
3. Eliminate ambiguous yes/no questions (no compound questions)
4. Consistent pointer indicator (👉 prefix on all prompts)

Usage:
    python senzing-bootcamp/scripts/validate_behavior_rules.py
    python senzing-bootcamp/scripts/validate_behavior_rules.py \
--check steering/agent-behavior-rules.md
    python senzing-bootcamp/scripts/validate_behavior_rules.py path/to/file.md

Exit codes:
    0 — All checks passed
    1 — Violations detected or file not found

Examples:
    # Validate default steering files
    python senzing-bootcamp/scripts/validate_behavior_rules.py

    # Check a specific file
    python senzing-bootcamp/scripts/validate_behavior_rules.py \
--check steering/agent-behavior-rules.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Register module in sys.modules for dataclass annotation resolution.
# Required when imported via importlib.util without prior sys.modules registration.
if __name__ not in sys.modules:
    import types as _types

    _mod = _types.ModuleType(__name__)
    _mod.__dict__.update(globals())
    sys.modules[__name__] = _mod

# ---------------------------------------------------------------------------
# Constants — Continuation Request Detection
# ---------------------------------------------------------------------------

CONTINUATION_PHRASES: list[str] = [
    "continue",
    "keep going",
    "next",
    "go on",
    "proceed",
    "let's continue",
    "let's keep going",
    "next module",
    "move on",
    "carry on",
]

# ---------------------------------------------------------------------------
# Constants — Pause Language Detection
# ---------------------------------------------------------------------------

PAUSE_PATTERNS: list[str] = [
    r"\b(take a break|pause|stop here|pick this up later|"
    r"continue (later|tomorrow|next time|in a new session)|"
    r"call it a day|wrap up for now|save.*progress.*later)\b",
]

# ---------------------------------------------------------------------------
# Constants — Compound Question Detection
# ---------------------------------------------------------------------------

CONJUNCTION_PATTERNS: list[str] = [
    r"\bor\b(?!\s*$)",           # "or" not at end of line
    r"\balternatively\b",
    r"\bor would you rather\b",
    r"\bor should we\b",
    r"\bor would you prefer\b",
    r"\bor if you prefer\b",
]

# ---------------------------------------------------------------------------
# Constants — Acknowledgment Validation
# ---------------------------------------------------------------------------

CONTENT_FREE_PHRASES: list[str] = [
    "got it",
    "okay",
    "sure",
    "thanks",
    "understood",
    "noted",
    "alright",
    "ok",
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class AcknowledgmentResult:
    """Result of validating an acknowledgment against behavior rule constraints.

    Attributes:
        valid: Overall pass/fail — True only when all constraints are met.
        sentence_count: Number of sentences detected in the acknowledgment.
        word_count: Number of words detected in the acknowledgment.
        is_substantive: True if the text is not composed entirely of content-free phrases.
        position_ok: True if the acknowledgment appears within the first 2 sentences.
    """

    valid: bool
    sentence_count: int
    word_count: int
    is_substantive: bool
    position_ok: bool


@dataclass
class Violation:
    """A behavior rule violation detected during validation.

    Attributes:
        rule: The rule number that was violated (1-4).
        line_number: Line number in the file where the violation was found.
        message: Human-readable description of the violation.
    """

    rule: int
    line_number: int
    message: str


# ---------------------------------------------------------------------------
# Continuation Request Detection
# ---------------------------------------------------------------------------


def is_continuation_request(message: str) -> bool:
    """Detect whether a message contains an explicit continuation phrase.

    Performs case-insensitive matching against the CONTINUATION_PHRASES list.

    Args:
        message: The bootcamper's message text.

    Returns:
        True if the message contains at least one continuation phrase.
    """
    lower_message = message.lower()
    return any(phrase in lower_message for phrase in CONTINUATION_PHRASES)


# ---------------------------------------------------------------------------
# Pause Language Detection
# ---------------------------------------------------------------------------


def contains_pause_language(text: str) -> bool:
    """Detect whether text contains pause/stop/defer language.

    Performs regex matching against PAUSE_PATTERNS (case-insensitive).

    Args:
        text: The text to check for pause language.

    Returns:
        True if the text matches at least one pause pattern.
    """
    for pattern in PAUSE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Acknowledgment Validation
# ---------------------------------------------------------------------------


def validate_acknowledgment(text: str, bootcamper_response: str = "") -> AcknowledgmentResult:
    """Validate an acknowledgment against behavior rule constraints.

    Checks that the acknowledgment:
    - Contains no more than 2 sentences (split on .!?)
    - Contains no more than 50 words (split on whitespace)
    - Is substantive (not composed entirely of content-free phrases)
    - Appears in a valid position (always True for standalone validation)

    Args:
        text: The acknowledgment text to validate.
        bootcamper_response: The bootcamper's original response for context.
            Used for substantiveness checking when provided.

    Returns:
        AcknowledgmentResult with validation details.
    """
    # Sentence counting: split on sentence-ending punctuation
    stripped = text.strip()
    if not stripped:
        return AcknowledgmentResult(
            valid=False,
            sentence_count=0,
            word_count=0,
            is_substantive=False,
            position_ok=True,
        )

    # Split on .!? to count sentences — filter out empty segments
    sentences = [s.strip() for s in re.split(r"[.!?]+", stripped) if s.strip()]
    sentence_count = len(sentences)

    # Word counting: split on whitespace
    words = stripped.split()
    word_count = len(words)

    # Substantiveness check: text must not be composed entirely of content-free phrases
    # Normalize: lowercase, strip punctuation, collapse whitespace
    normalized = re.sub(r"[^\w\s]", "", stripped.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)

    # Check if the entire normalized text is composed of content-free phrases
    remaining = normalized
    for phrase in sorted(CONTENT_FREE_PHRASES, key=len, reverse=True):
        remaining = remaining.replace(phrase, "")
    remaining = remaining.strip()
    is_substantive = len(remaining) > 0

    # Position check: always True for standalone text validation
    position_ok = True

    # Overall validity
    valid = (
        sentence_count <= 2
        and word_count <= 50
        and is_substantive
        and position_ok
    )

    return AcknowledgmentResult(
        valid=valid,
        sentence_count=sentence_count,
        word_count=word_count,
        is_substantive=is_substantive,
        position_ok=position_ok,
    )


# ---------------------------------------------------------------------------
# Compound Question Detection
# ---------------------------------------------------------------------------


def is_compound_question(question: str) -> bool:
    """Detect whether a question is a compound yes/no question with prose conjunctions.

    A compound question is one that contains a "?" AND matches at least one
    conjunction pattern from CONJUNCTION_PATTERNS. This indicates the question
    presents multiple alternatives joined by prose, making a simple yes/no
    answer ambiguous.

    Args:
        question: The question text to check.

    Returns:
        True if the question contains a "?" and at least one conjunction pattern.
    """
    if "?" not in question:
        return False
    for pattern in CONJUNCTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Pointer Indicator Checking
# ---------------------------------------------------------------------------


def has_pointer_prefix(line: str) -> bool:
    """Check whether a line starts with the pointer indicator.

    Strips optional list markers ("- " or "* ") before checking for the
    pointer emoji prefix.

    Args:
        line: The line of text to check.

    Returns:
        True if the line starts with the pointer indicator after stripping
        optional list markers.
    """
    stripped = line.lstrip()
    # Strip optional list markers
    if stripped.startswith("- "):
        stripped = stripped[2:].lstrip()
    elif stripped.startswith("* "):
        stripped = stripped[2:].lstrip()
    return stripped.startswith("\U0001f449")


# ---------------------------------------------------------------------------
# Bold Question Detection (Rule 4 — Bold Question Text)
# ---------------------------------------------------------------------------

# Pointer indicator (👉) marking an input-requiring prompt.
POINTER_INDICATOR: str = "\U0001f449"

# STOP marker (🛑) denoting the end-of-turn boundary after a leading question.
STOP_MARKER: str = "\U0001f6d1"

# Bold-emphasis marker (CommonMark strong emphasis).
BOLD_MARKER: str = "**"


def strip_bold(text: str) -> str:
    """Remove paired bold-emphasis markers from text.

    Removes every ``**`` bold-emphasis marker, returning the underlying
    wording. This mirrors the marker-stripping step performed by the
    write-policy-gate so that downstream checks operate on the same
    marker-free wording.

    Args:
        text: The text that may contain ``**`` bold markers.

    Returns:
        The text with all ``**`` bold markers removed.
    """
    return text.replace(BOLD_MARKER, "")


def question_text_is_bold(question_text: str) -> bool:
    """Report whether question text is a single balanced bold span.

    Returns True only when the whitespace-trimmed text is wrapped in a
    single balanced ``**...**`` span that covers its entire content: it
    starts with ``**``, ends with ``**``, encloses at least one character,
    and contains no other ``**`` markers between the outer pair. Italic
    (``*...*``), partial bold (``**What** language?``), and unbalanced
    markers (``**text``) all return False.

    Args:
        question_text: The reconstructed question text to inspect.

    Returns:
        True if the trimmed text is a single balanced bold span covering
        its whole content, otherwise False.
    """
    trimmed = question_text.strip()
    # Need at least the opening and closing markers plus one inner character.
    if len(trimmed) < 5:
        return False
    if not (trimmed.startswith(BOLD_MARKER) and trimmed.endswith(BOLD_MARKER)):
        return False
    inner = trimmed[len(BOLD_MARKER):-len(BOLD_MARKER)]
    # No inner content means an empty span; extra markers mean it is not a
    # single covering span (e.g. partial or multiple bold segments).
    if not inner.strip():
        return False
    if BOLD_MARKER in inner:
        return False
    return True


def _blockquote_depth_and_content(line: str) -> tuple[int, str]:
    """Split a line into its blockquote depth and remaining content.

    Counts leading ``>`` blockquote markers (each optionally followed by a
    single space) after any leading whitespace, then returns the remaining
    content with leading whitespace stripped.

    Args:
        line: The raw line of text.

    Returns:
        A tuple of the blockquote nesting depth and the content that follows
        the blockquote markers.
    """
    depth = 0
    rest = line
    while True:
        stripped = rest.lstrip()
        if stripped.startswith(">"):
            depth += 1
            rest = stripped[1:]
            if rest.startswith(" "):
                rest = rest[1:]
        else:
            rest = stripped
            break
    return depth, rest


def _strip_list_marker(content: str) -> str:
    """Strip a leading list marker from content.

    Removes a leading unordered (``- ``/``* ``) or ordered (``1. ``/``1) ``)
    list marker along with the surrounding whitespace.

    Args:
        content: The content that may begin with a list marker.

    Returns:
        The content with a single leading list marker removed.
    """
    stripped = content.lstrip()
    if stripped.startswith("- ") or stripped.startswith("* "):
        return stripped[2:].lstrip()
    ordered = re.match(r"\d+[.)]\s+", stripped)
    if ordered:
        return stripped[ordered.end():]
    return stripped


def extract_question_block(lines: list[str], index: int) -> tuple[str, int]:
    """Reconstruct a possibly soft-wrapped pointer question.

    Starting at a pointer (👉) line, strips the blockquote marker, any list
    marker, and leading whitespace, takes the text after ``👉``, then appends
    following lines that belong to the same paragraph/blockquote — same
    blockquote depth, non-blank, not a new heading, not a numbered list item,
    not a fenced-code fence, and not a new pointer question. A ``🛑 STOP``
    line and bracketed meta lines (e.g. ``[wait for response...]``) act as
    boundaries and are not merged into the question block.

    Args:
        lines: The file split into individual lines.
        index: Index of the pointer line where the question begins.

    Returns:
        A tuple of the joined question text and the index of the last line
        consumed as part of the question block.
    """
    depth0, content0 = _blockquote_depth_and_content(lines[index])
    content0 = _strip_list_marker(content0)
    if content0.startswith(POINTER_INDICATOR):
        first = content0[len(POINTER_INDICATOR):].lstrip()
    else:
        first = content0
    parts = [first.strip()]
    last_consumed = index

    j = index + 1
    while j < len(lines):
        depth_j, content_j = _blockquote_depth_and_content(lines[j])
        stripped = content_j.strip()

        # Blank line — paragraph boundary.
        if not stripped:
            break
        # Different blockquote nesting — no longer the same block.
        if depth_j != depth0:
            break
        # New heading.
        if stripped.startswith("#"):
            break
        # Fenced-code fence.
        if stripped.startswith("```") or stripped.startswith("~~~"):
            break
        # Numbered list item (e.g. a choice question's options).
        if re.match(r"\d+[.)]\s", stripped):
            break
        # A new pointer question.
        if _strip_list_marker(content_j).startswith(POINTER_INDICATOR):
            break
        # STOP marker boundary.
        if STOP_MARKER in content_j:
            break
        # Bracketed meta line (e.g. "[wait for response...]").
        if stripped.startswith("["):
            break

        parts.append(stripped)
        last_consumed = j
        j += 1

    question = " ".join(part for part in parts if part)
    return question, last_consumed


def is_negative_example_context(lines: list[str], index: int) -> bool:
    """Report whether a line sits under a WRONG-labeled heading.

    Walks backward from the given index to the nearest Markdown heading and
    reports whether that heading text contains ``WRONG`` (case-insensitive).
    Negative examples are intentionally left un-bolded and must not be
    flagged as violations.

    Args:
        lines: The file split into individual lines.
        index: Index of the line to classify.

    Returns:
        True if the nearest preceding heading contains ``WRONG``
        (case-insensitive), otherwise False.
    """
    for j in range(index, -1, -1):
        _, content = _blockquote_depth_and_content(lines[j])
        heading = re.match(r"#{1,6}\s+(.*)$", content.strip())
        if heading:
            return "wrong" in heading.group(1).lower()
    return False


def _is_fence_line(line: str) -> bool:
    """Report whether a line opens or closes a fenced code block.

    Strips any leading blockquote markers, then reports whether the remaining
    content begins with a CommonMark code fence (three backticks or three
    tildes). Fence lines toggle fenced-block state so that illustrative
    content — including pointer questions shown inside ``` fences — is skipped
    by the bold-question check.

    Args:
        line: The raw line of text.

    Returns:
        True if the line is a fenced-code fence, otherwise False.
    """
    _, content = _blockquote_depth_and_content(line)
    stripped = content.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def _pointer_line_starts_block(lines: list[str], index: int) -> bool:
    """Report whether a pointer line begins a new paragraph or block.

    A 👉 is a leading question only when it opens its own paragraph/block.
    When the preceding line is a non-blank continuation at the same blockquote
    depth, the 👉 is a soft-wrapped continuation of that paragraph — an inline
    prose mention that merely happens to land at the start of a wrapped line —
    and must not be treated as a leading question (R10.3).

    The line begins a new block when it is the first line of the file, or the
    preceding line is blank, a heading, a code fence, or sits at a different
    blockquote depth.

    Args:
        lines: The file split into individual lines.
        index: Index of the pointer line to classify.

    Returns:
        True if the pointer line opens a new paragraph/block, otherwise False.
    """
    if index <= 0:
        return True
    depth, _ = _blockquote_depth_and_content(lines[index])
    prev_depth, prev_content = _blockquote_depth_and_content(lines[index - 1])
    prev_stripped = prev_content.strip()
    if not prev_stripped:
        return True
    if prev_depth != depth:
        return True
    if prev_stripped.startswith("#"):
        return True
    if prev_stripped.startswith("```") or prev_stripped.startswith("~~~"):
        return True
    return False


# ---------------------------------------------------------------------------
# Constants — Negation Context Detection
# ---------------------------------------------------------------------------

# Patterns that indicate a line is *prohibiting*, *describing*, or *instructing*
# about pause language rather than the agent unsolicited recommending it to the
# bootcamper. Lines matching these are excluded from Rule 1 violations.
NEGATION_CONTEXT_PATTERNS: list[str] = [
    # Prohibition / negation context
    r"\bdo\s+not\b",
    r"\bdon'?t\b",
    r"\bshall\s+not\b",
    r"\bshan'?t\b",
    r"\bmust\s+not\b",
    r"\bnever\b",
    r"\bprohibited\b",
    r"\bdo\s+NOT\b",
    r"\bNOT\b",
    r"\buntil\s+they\s+explicitly\b",
    r"\bbootcamper'?s?\s+(explicit|stated)\b",
    r"\bexplicitly\s+request\b",
    # Agent instructions — mandatory gates and conditional logic
    r"\bMUST\s+stop\b",
    r"\bmandatory\s+gate\b",
    r"\bif\s+(they|the\s+bootcamper|errors|both)\b",
    r"\bwhen\s+(the\s+bootcamper|both)\b",
    # Stopping point descriptions (module boundaries, natural pauses)
    r"\bstopping\s+point\b",
    r"\bsafe\s+to\s+stop\b",
    r"\bcan\s+stop\s+here\b",
    # Error handling instructions
    r"\bpause\s+and\s+(investigate|fix|review)\b",
    r"\bretry\s+(after|failed)\b",
    # Bootcamper choice / preference context
    r"\bor\s+(prefer|would\s+you\s+prefer)\b",
    r"\bready\s+to\s+deploy\b",
    r"\bask\s*:",
    r"\bthen\s+ask\b",
    # Quoted example phrases (in quotes or as list items describing triggers)
    r'^[^"]*"[^"]*$',
    r"^- \"",
]


# ---------------------------------------------------------------------------
# Steering File Validation
# ---------------------------------------------------------------------------


def _is_negation_context(line: str) -> bool:
    """Detect whether a line uses pause language in a negation/prohibition context.

    Lines that instruct the agent what NOT to do, or describe conditions under
    which the bootcamper (not the agent) may pause, are not violations.

    Args:
        line: The line of text to check.

    Returns:
        True if the line contains negation context markers.
    """
    for pattern in NEGATION_CONTEXT_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def validate_steering_file(path: Path) -> list[Violation]:
    """Validate a steering file against behavior rules.

    Applies two checks over the file's lines:

    - **Rule 1** — flags pause/stop/defer language in agent-directed content,
      skipping lines that use such language in a negation or prohibition
      context (e.g., "Do NOT use phrases like 'take a break'").
    - **Rule 4** — flags any pointer (👉) leading question whose reconstructed
      question text is not wrapped in a single balanced bold span. Candidates
      are only lines that carry 👉 at start-of-line after stripping blockquote
      and list markers; content inside fenced code blocks is skipped, and
      questions under a ``WRONG``-labeled heading (intentional negative
      examples) are exempt.

    Args:
        path: Path to the steering file to validate.

    Returns:
        List of Violation instances found in the file.
    """
    violations: list[Violation] = []

    if not path.is_file():
        return violations

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        try:
            content = path.read_text(encoding="latin-1")
        except OSError:
            return violations

    if not content.strip():
        return violations

    lines = content.splitlines()
    in_fenced_block = False
    for i, line in enumerate(lines, start=1):
        # Rule 1 — pause/stop/defer language in agent-directed content.
        # Skip lines that use pause language in negation/prohibition context.
        if contains_pause_language(line) and not _is_negation_context(line):
            violations.append(Violation(
                rule=1,
                line_number=i,
                message=f"Line contains pause/stop/defer language: {line.strip()!r}",
            ))

        # Track fenced-code-block state — pointer questions shown inside a
        # ``` fence are illustrative, not live leading questions, so they are
        # skipped by the bold-question check below.
        if _is_fence_line(line):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue

        # Rule 4 — every 👉 leading question's text must be wrapped in bold.
        # Candidates are lines carrying 👉 at start-of-line after stripping
        # blockquote and list markers; inline mentions, prose, headings, and
        # numbered option lines never qualify.
        _, deblockquoted = _blockquote_depth_and_content(line)
        if not has_pointer_prefix(deblockquoted):
            continue
        # A 👉 that continues the previous prose line (soft-wrap) is an inline
        # mention, not a leading question — skip it.
        if not _pointer_line_starts_block(lines, i - 1):
            continue
        # Intentional (WRONG) negative examples are deliberately un-bolded.
        if is_negative_example_context(lines, i - 1):
            continue
        question_text, _ = extract_question_block(lines, i - 1)
        if not question_text_is_bold(question_text):
            snippet = question_text.strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            violations.append(Violation(
                rule=4,
                line_number=i,
                message=(
                    "Leading question text is not wrapped in bold emphasis "
                    f"(**...**): {snippet!r}"
                ),
            ))

    return violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run behavior rules validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Validate agent behavior rules compliance in steering files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in check mode (exit 1 on violations).",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Steering files to validate. Defaults to all files in steering/.",
    )
    args = parser.parse_args(argv)

    # Resolve paths relative to the bootcamp root
    bootcamp_root = Path(__file__).resolve().parent.parent
    steering_dir = bootcamp_root / "steering"

    if args.files:
        paths = [Path(f) for f in args.files]
    elif steering_dir.is_dir():
        paths = sorted(steering_dir.glob("*.md"))
    else:
        print("No steering directory found and no files specified.", file=sys.stderr)
        sys.exit(1)

    all_violations: list[Violation] = []
    for path in paths:
        if not path.is_file():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        violations = validate_steering_file(path)
        if violations:
            print(f"\n{path}:")
            for v in violations:
                print(f"  Line {v.line_number} [Rule {v.rule}]: {v.message}")
            all_violations.extend(violations)

    if all_violations:
        print(f"\n❌ {len(all_violations)} violation(s) found.")
        sys.exit(1)
    else:
        print("✅ All behavior rule checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
