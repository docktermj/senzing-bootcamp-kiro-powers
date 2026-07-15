#!/usr/bin/env python3
"""Senzing Bootcamp - Session_Handoff structural validator.

Checks a candidate Handoff_Summary string for the structural invariants defined
by the session-handoff design: the canonical section set and order, absolute-path
file references, forbidden temporal-phrase exclusion, no emoji, and a quoted
continuation phrase. This module is a pure, stdlib-only helper: it validates
already-produced text and performs no synthesis, no session access, and no file
writes.

The validator mirrors the read-only, never-raise posture of ``baseline_status.py``:
``validate_handoff_summary`` returns findings for malformed or arbitrary input and
never throws.

Usage:
    # Validate a candidate Handoff_Summary file:
    python3 senzing-bootcamp/scripts/validate_handoff_summary.py <path-to-summary.md>
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Finding codes
# ---------------------------------------------------------------------------

# Structural finding codes emitted by the checks. Each maps to a Correctness
# Property in the session-handoff design document.
MISSING_SECTION = "MISSING_SECTION"                    # a canonical section is absent
SECTION_OUT_OF_ORDER = "SECTION_OUT_OF_ORDER"          # sections appear out of canonical order
RELATIVE_PATH = "RELATIVE_PATH"                        # a file reference is not absolute
FORBIDDEN_PHRASE = "FORBIDDEN_PHRASE"                  # a forbidden temporal phrase appears
EMOJI = "EMOJI"                                        # an emoji code point appears
EMPTY_SECTION_NOT_NONE = "EMPTY_SECTION_NOT_NONE"      # an empty section does not read "none"
UNQUOTED_CONTINUATION = "UNQUOTED_CONTINUATION"        # the resume phrase is not quoted

# ---------------------------------------------------------------------------
# Canonical constants
# ---------------------------------------------------------------------------

# The Title heading (Section 1). The Title is a level-1 ("# ") heading, whereas
# the remaining seven sections are level-2 ("## ") headings.
TITLE_SECTION = "Title"

# The seven level-2 section headings, in canonical order (Sections 2-8).
BODY_SECTIONS: tuple[str, ...] = (
    "Where it started",
    "Decisions locked + what shipped",
    "Key files for next session",
    "Running state",
    "Verification — how to confirm things still work",
    "Deferred + open questions",
    "Pick up here",
)

# The full ordered eight-section layout (Req 4.1): the Title followed by the
# seven body sections.
CANONICAL_SECTIONS: tuple[str, ...] = (TITLE_SECTION, *BODY_SECTIONS)

# The eight forbidden temporal phrases that must never appear in the "Pick up
# here" section (Req 7.4). Compared case-insensitively by the checks.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "come back later",
    "come back tomorrow",
    "take a break",
    "try again in a while",
    "when you're ready",
    "try again later",
    "wait a moment",
    "give it some time",
)

# The literal token that an otherwise-empty section must contain (Req 4.3, 9.4).
NONE_MARKER = "none"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HandoffFinding:
    """A single structural problem found in a candidate Handoff_Summary.

    Attributes:
        code: The finding category, one of the module-level finding-code
            constants (e.g. ``MISSING_SECTION``, ``SECTION_OUT_OF_ORDER``,
            ``RELATIVE_PATH``, ``FORBIDDEN_PHRASE``, ``EMOJI``,
            ``EMPTY_SECTION_NOT_NONE``, ``UNQUOTED_CONTINUATION``).
        detail: A human-readable description of the specifics (which section or
            token triggered the finding).
    """

    code: str
    detail: str


@dataclass
class HandoffValidation:
    """The outcome of validating a candidate Handoff_Summary.

    Attributes:
        ok: ``True`` iff ``findings`` is empty.
        findings: The structural findings, empty when the summary is conformant.
    """

    ok: bool
    findings: list[HandoffFinding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Heading parsing
# ---------------------------------------------------------------------------

# Matches an ATX heading line (up to three leading spaces, one-to-six ``#``
# characters, then optional heading text). The optional trailing closing
# sequence of ``#`` characters is stripped separately. Content that does not
# begin with a hash sequence never matches, so ordinary body lines are ignored.
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")

# Matches an optional ATX closing sequence (whitespace followed by ``#`` runs at
# end of a heading), e.g. the trailing ``##`` in ``## Running state ##``.
_CLOSING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")


@dataclass
class _Heading:
    """A single ATX heading parsed from a candidate Handoff_Summary.

    Attributes:
        level: The heading level (number of leading ``#`` characters, 1-6).
        text: The stripped heading text with any ATX closing sequence removed
            (empty when the heading has no text).
        line_index: The zero-based index of the heading's source line.
    """

    level: int
    text: str
    line_index: int


def _parse_headings(lines: list[str]) -> list[_Heading]:
    """Parse the ATX headings from the summary's lines, in document order.

    Args:
        lines: The candidate Handoff_Summary split into lines.

    Returns:
        The parsed headings in the order they appear. Non-heading lines are
        ignored; the function never raises on arbitrary input.
    """
    headings: list[_Heading] = []
    for index, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match is None:
            continue
        hashes = match.group(1)
        text = _CLOSING_HASHES_RE.sub("", match.group(2) or "").strip()
        headings.append(_Heading(level=len(hashes), text=text, line_index=index))
    return headings


def _section_content(lines: list[str], headings: list[_Heading], section_name: str) -> str | None:
    """Return the raw content of a named level-2 body section.

    The content is the text between the section's ``## `` heading and the next
    heading of any level (or end of document). Only the first occurrence of the
    section is considered. Callers strip or tokenize the returned text as needed.

    Args:
        lines: The candidate Handoff_Summary split into lines.
        headings: The parsed headings in document order.
        section_name: The level-2 heading text to locate (e.g. "Running state").

    Returns:
        The joined (unstripped) content lines, or ``None`` when the section
        heading is not present.
    """
    heading_lines = sorted(heading.line_index for heading in headings)
    for heading in headings:
        if heading.level != 2 or heading.text != section_name:
            continue
        start = heading.line_index + 1
        end = len(lines)
        for candidate in heading_lines:
            if candidate > heading.line_index:
                end = candidate
                break
        return "\n".join(lines[start:end])
    return None


# ---------------------------------------------------------------------------
# Structural checks (section presence, order, empty-section marker)
# ---------------------------------------------------------------------------


def _check_section_presence(headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that the Title and all seven body sections are present.

    The Title is the first level-1 (``# ``) heading and must carry a non-empty
    subject; the seven body sections are level-2 (``## ``) headings matching
    :data:`BODY_SECTIONS`. A missing Title, an empty Title subject, or any absent
    body heading yields a ``MISSING_SECTION`` finding (Req 4.1, 4.2).

    Args:
        headings: The parsed headings in document order.

    Returns:
        One :class:`HandoffFinding` per absent (or empty) required section.
    """
    findings: list[HandoffFinding] = []

    title_headings = [heading for heading in headings if heading.level == 1]
    if not title_headings:
        findings.append(
            HandoffFinding(
                code=MISSING_SECTION,
                detail="Title: no level-1 '# ' heading found; expected '# Handoff: <subject>'.",
            )
        )
    elif not any(heading.text for heading in title_headings):
        findings.append(
            HandoffFinding(
                code=MISSING_SECTION,
                detail="Title: the level-1 heading has no subject text; the Title must state "
                "the session subject in one line.",
            )
        )

    present_body = {heading.text for heading in headings if heading.level == 2}
    for name in BODY_SECTIONS:
        if name not in present_body:
            findings.append(
                HandoffFinding(code=MISSING_SECTION, detail=f"Section '{name}' is absent.")
            )
    return findings


def _check_section_order(headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that the recognized canonical sections appear in canonical order.

    Builds the sequence of recognized canonical sections (the Title followed by
    matching body sections) in document order and verifies their canonical
    indices strictly increase. A section whose canonical index does not exceed
    the previous in-order section yields a ``SECTION_OUT_OF_ORDER`` finding
    (Req 4.1). Missing sections are ignored here (reported by presence check).

    Args:
        headings: The parsed headings in document order.

    Returns:
        One :class:`HandoffFinding` per section observed out of canonical order.
    """
    findings: list[HandoffFinding] = []

    observed: list[int] = []
    title_seen = False
    for heading in headings:
        if heading.level == 1 and heading.text and not title_seen:
            observed.append(0)
            title_seen = True
        elif heading.level == 2 and heading.text in BODY_SECTIONS:
            observed.append(1 + BODY_SECTIONS.index(heading.text))

    prev_index = -1
    prev_name: str | None = None
    for canonical_index in observed:
        name = CANONICAL_SECTIONS[canonical_index]
        if canonical_index <= prev_index:
            findings.append(
                HandoffFinding(
                    code=SECTION_OUT_OF_ORDER,
                    detail=f"Section '{name}' appears out of canonical order (after "
                    f"'{prev_name}').",
                )
            )
        else:
            prev_index = canonical_index
            prev_name = name
    return findings


def _check_empty_sections(lines: list[str], headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that every present body section has content or reads exactly "none".

    A body section's content is the text between its heading and the next heading
    (of any level). When that content is empty (whitespace only), the section is
    non-conformant because an empty section must read exactly the
    :data:`NONE_MARKER` ("none"); such a section yields an
    ``EMPTY_SECTION_NOT_NONE`` finding (Req 4.3, 9.4). A section reading "none" or
    carrying any other content passes.

    Args:
        lines: The candidate Handoff_Summary split into lines.
        headings: The parsed headings in document order.

    Returns:
        One :class:`HandoffFinding` per present body section with empty content.
    """
    findings: list[HandoffFinding] = []

    present_body = {heading.text for heading in headings if heading.level == 2}
    for name in BODY_SECTIONS:
        if name not in present_body:
            continue  # absence is reported by the presence check, not here
        content = _section_content(lines, headings, name)
        if content is not None and not content.strip():
            findings.append(
                HandoffFinding(
                    code=EMPTY_SECTION_NOT_NONE,
                    detail=f"Section '{name}' has no content; an empty section must "
                    f"read exactly '{NONE_MARKER}'.",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Content checks (relative paths, forbidden phrases, emoji, quoted continuation)
# ---------------------------------------------------------------------------

# The sections whose file references must be absolute paths (Req 5.1, 5.4, 8.3):
# "Key files for next session" and the SQLite database entry in "Running state".
# The "Verification" section is intentionally excluded — it carries a deliberate
# relative command (``python3 senzing-bootcamp/scripts/baseline_status.py``,
# Req 6.3) that must not be flagged.
_PATH_REFERENCE_SECTIONS: tuple[str, ...] = (
    "Key files for next session",
    "Running state",
)

# Matches a URI scheme prefix (e.g. ``postgresql://``, ``https://``). Such tokens
# are connection descriptions or URLs, not filesystem paths, so they are excluded
# from the absolute-path check (Req 5.4 allows a PostgreSQL connection string).
_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://")

# Wrapping characters stripped from candidate tokens before path inspection
# (backticks, quotes, and trailing punctuation from list items / prose).
_TOKEN_WRAP_CHARS = "`\"'(),;"

# The Continuation_Phrase stem defined by the Context_Reset_Message convention in
# ``agent-context-management.md`` (Req 7.1, 7.3). Matched case-insensitively.
_CONTINUATION_PHRASE_RE = re.compile(r"continue the bootcamp from module", re.IGNORECASE)

# Unicode code-point ranges (inclusive) used to detect emoji with the standard
# library only — no third-party emoji dependency (Req 9.2). Covers the emoji
# blocks named by the design: emoticons, transport, supplemental symbols and
# pictographs, dingbats, miscellaneous symbols, regional indicators, and the
# emoji variation selectors.
_EMOJI_RANGES: tuple[tuple[int, int], ...] = (
    (0x1F300, 0x1F5FF),  # Miscellaneous Symbols and Pictographs
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
    (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
    (0x2600, 0x26FF),    # Miscellaneous Symbols
    (0x2700, 0x27BF),    # Dingbats
    (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols (flags)
    (0xFE00, 0xFE0F),    # Variation Selectors (e.g. emoji-presentation VS16)
)


def _path_like_tokens(content: str) -> list[str]:
    """Extract filesystem-path-like tokens from section content.

    A token is treated as a filesystem path reference when, after stripping
    wrapping backticks/quotes/punctuation, it contains a path separator (``/``)
    and is not a URI scheme (e.g. ``postgresql://``). This deliberately ignores
    bare words, process names, and connection URIs so only genuine path
    references are inspected for absoluteness.

    Args:
        content: The raw content of a section.

    Returns:
        The path-like tokens in document order (surrounding markup removed).
    """
    tokens: list[str] = []
    for raw in content.split():
        token = raw.strip(_TOKEN_WRAP_CHARS)
        if "/" not in token:
            continue
        if _URI_SCHEME_RE.match(token):
            continue
        tokens.append(token)
    return tokens


def _check_relative_paths(lines: list[str], headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that file references in the path-bearing sections are absolute.

    Scans "Key files for next session" and "Running state" (which carries the
    SQLite database entry) for path-like tokens and emits a ``RELATIVE_PATH``
    finding for any that does not begin with ``/`` (Req 5.1, 5.4, 8.3).

    Args:
        lines: The candidate Handoff_Summary split into lines.
        headings: The parsed headings in document order.

    Returns:
        One :class:`HandoffFinding` per relative path reference found.
    """
    findings: list[HandoffFinding] = []
    for section_name in _PATH_REFERENCE_SECTIONS:
        content = _section_content(lines, headings, section_name)
        if content is None:
            continue
        for token in _path_like_tokens(content):
            if not token.startswith("/"):
                findings.append(
                    HandoffFinding(
                        code=RELATIVE_PATH,
                        detail=f"Section '{section_name}' contains a relative path reference "
                        f"'{token}'; every file reference must be an absolute path.",
                    )
                )
    return findings


def _check_forbidden_phrases(lines: list[str], headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that the "Pick up here" section avoids forbidden temporal phrases.

    Compares the section content case-insensitively against the eight
    :data:`FORBIDDEN_PHRASES` and emits a ``FORBIDDEN_PHRASE`` finding for each
    phrase present (Req 7.4).

    Args:
        lines: The candidate Handoff_Summary split into lines.
        headings: The parsed headings in document order.

    Returns:
        One :class:`HandoffFinding` per forbidden phrase found.
    """
    findings: list[HandoffFinding] = []
    content = _section_content(lines, headings, "Pick up here")
    if content is None:
        return findings
    lowered = content.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            findings.append(
                HandoffFinding(
                    code=FORBIDDEN_PHRASE,
                    detail=f"Section 'Pick up here' contains the forbidden temporal phrase "
                    f"'{phrase}'.",
                )
            )
    return findings


def _check_emoji(text: str) -> list[HandoffFinding]:
    """Check that no emoji code point appears anywhere in the summary.

    Emits one ``EMOJI`` finding per distinct emoji character found, classified via
    the :data:`_EMOJI_RANGES` Unicode code-point ranges (stdlib only, Req 9.2).

    Args:
        text: The full candidate Handoff_Summary text.

    Returns:
        One :class:`HandoffFinding` per distinct emoji code point found.
    """
    findings: list[HandoffFinding] = []
    seen: set[str] = set()
    for char in text:
        code_point = ord(char)
        if char in seen:
            continue
        if any(low <= code_point <= high for low, high in _EMOJI_RANGES):
            seen.add(char)
            findings.append(
                HandoffFinding(
                    code=EMOJI,
                    detail=f"Summary contains an emoji code point U+{code_point:04X}; emojis "
                    f"are not permitted.",
                )
            )
    return findings


def _double_quoted_spans(text: str) -> list[str]:
    """Return the inner text of every double-quoted span in ``text``.

    Recognizes straight double quotes (``"..."``) and typographic double quotes
    (``\u201c...\u201d``), the forms used to enclose the Continuation_Phrase.

    Args:
        text: The text to scan for quoted spans.

    Returns:
        The inner content of each quoted span in document order.
    """
    spans = [match.group(1) for match in re.finditer(r'"([^"]*)"', text)]
    spans.extend(match.group(1) for match in re.finditer("\u201c([^\u201d]*)\u201d", text))
    return spans


def _check_quoted_continuation(lines: list[str], headings: list[_Heading]) -> list[HandoffFinding]:
    """Check that the resume phrase in "Pick up here" is enclosed in quotes.

    When the "Pick up here" section presents the Continuation_Phrase, it must be
    enclosed in quotation marks (Req 7.2); an unquoted resume phrase yields an
    ``UNQUOTED_CONTINUATION`` finding. When no Continuation_Phrase is present
    (its presence is enforced by agent instruction, not this check), nothing is
    reported.

    Args:
        lines: The candidate Handoff_Summary split into lines.
        headings: The parsed headings in document order.

    Returns:
        A single-element list with an ``UNQUOTED_CONTINUATION`` finding when the
        continuation phrase is present but unquoted, otherwise an empty list.
    """
    content = _section_content(lines, headings, "Pick up here")
    if content is None or not _CONTINUATION_PHRASE_RE.search(content):
        return []
    if any(_CONTINUATION_PHRASE_RE.search(span) for span in _double_quoted_spans(content)):
        return []
    return [
        HandoffFinding(
            code=UNQUOTED_CONTINUATION,
            detail="Section 'Pick up here' presents the continuation phrase without enclosing "
            "it in quotation marks.",
        )
    ]


# ---------------------------------------------------------------------------
# Validation entry point
# ---------------------------------------------------------------------------


def validate_handoff_summary(text: str) -> HandoffValidation:
    """Validate a candidate Handoff_Summary string against its structural rules.

    Runs the structural checks (section presence and order, empty-section marker,
    absolute-path references, forbidden-phrase exclusion, no emoji, and quoted
    continuation phrase) and aggregates their findings. The summary is considered
    conformant when no findings are produced.

    The function is strictly read-only and never raises: malformed or arbitrary
    input yields findings and ``ok=False`` rather than an exception (mirrors the
    never-raise posture of ``baseline_status.py``).

    Args:
        text: The candidate Handoff_Summary text to validate.

    Returns:
        A :class:`HandoffValidation` with ``ok=True`` and no findings when the
        summary is conformant, otherwise ``ok=False`` with one finding per
        detected problem.
    """
    findings: list[HandoffFinding] = []

    # Line-based parsing is exception-free for string input; non-string input
    # degrades to no lines (every required section then reads as absent), which
    # preserves the never-raise posture.
    safe_text = text if isinstance(text, str) else ""
    lines = safe_text.splitlines()
    headings = _parse_headings(lines)

    # Section presence, order, and empty-section marker checks (task 1.2).
    findings.extend(_check_section_presence(headings))
    findings.extend(_check_section_order(headings))
    findings.extend(_check_empty_sections(lines, headings))

    # Content checks: absolute-path references, forbidden temporal phrases, emoji,
    # and the quoted continuation phrase (task 1.3).
    findings.extend(_check_relative_paths(lines, headings))
    findings.extend(_check_forbidden_phrases(lines, headings))
    findings.extend(_check_emoji(safe_text))
    findings.extend(_check_quoted_continuation(lines, headings))

    return HandoffValidation(ok=not findings, findings=findings)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def _read_summary_file(path: str) -> str:
    """Read a candidate Handoff_Summary file as UTF-8 text.

    Args:
        path: Filesystem path to the candidate Handoff_Summary file.

    Returns:
        The file contents as a string.

    Raises:
        OSError: When the file is missing or otherwise cannot be read.
        UnicodeDecodeError: When the file is not valid UTF-8 text.
    """
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the Handoff_Summary structural validator.

    Reads the candidate Handoff_Summary file named on the command line, validates
    it with :func:`validate_handoff_summary`, and reports the outcome. A
    conformant summary prints a single confirmation line and returns 0; a summary
    with findings prints each finding's ``code`` and ``detail`` (one per line) and
    returns 1.

    File-not-found or read errors are reported to stderr and also return 1,
    preserving the never-raise posture at the CLI boundary: this entry point
    surfaces problems as an exit code rather than propagating an exception.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when ``None``).

    Returns:
        0 when the summary is conformant, 1 when findings exist or the candidate
        file cannot be read.
    """
    parser = argparse.ArgumentParser(
        description="Validate a candidate Session_Handoff Handoff_Summary file against its "
        "structural rules (section set/order, absolute paths, forbidden phrases, no emoji, "
        "quoted continuation phrase).",
    )
    parser.add_argument(
        "path",
        help="Path to the candidate Handoff_Summary file to validate.",
    )
    args = parser.parse_args(argv)

    try:
        text = _read_summary_file(args.path)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: could not read '{args.path}': {exc}", file=sys.stderr)
        return 1

    result = validate_handoff_summary(text)
    if result.ok:
        print(f"OK: '{args.path}' is a conformant Handoff_Summary (no findings).")
        return 0

    for finding in result.findings:
        print(f"{finding.code}: {finding.detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
