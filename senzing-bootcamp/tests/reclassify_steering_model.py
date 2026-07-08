"""Pure reference mechanism for the steering-inclusion re-classification rewrite.

This is a **test-only** helper co-located with the tests for the
``steering-inclusion-auto-audit`` feature. It is *not* shipped as a power script
under ``senzing-bootcamp/scripts/`` and performs **no** filesystem I/O — it is a
pure string transform over a steering file's text that the property and unit
tests (Properties 3 and 4) quantify over, and that the one-time re-classification
of the eleven ``inclusion: auto`` files uses as its reference mechanism.

The single entry point, :func:`rewrite_inclusion`, rewrites only the leading
``---``-fenced YAML frontmatter block of a steering file:

* It replaces the value on the existing ``inclusion:`` line with the decided
  standard mode (``always`` | ``fileMatch`` | ``manual``), preserving that line's
  indentation and line terminator (Req 3.1).
* It leaves the ``description:`` line and any of its continuation lines — and
  every other frontmatter line — byte-identical, and never adds or removes a
  ``description`` when one is absent (Req 3.2).
* For ``mode == "fileMatch"`` it ensures a single ``fileMatchPattern:`` line equal
  to the decided glob exists, inserted directly after the ``inclusion:`` line when
  absent; for the other modes it injects none (Req 3.3).
* It copies the closing ``---`` fence and the entire Markdown body after it
  through byte-for-byte unchanged (Req 3.5).

A malformed :class:`Decision_Record` can never produce a bad file: the function
raises :class:`ValueError` for a mode outside the standard set and for a
``fileMatch`` request without a non-empty pattern.
"""

from __future__ import annotations

import re

__all__ = ["VALID_MODES", "rewrite_inclusion"]

# The three standard Kiro inclusion modes. ``auto`` is deliberately excluded.
VALID_MODES: frozenset[str] = frozenset({"always", "fileMatch", "manual"})

# The frontmatter fence delimiter.
_FENCE = "---"

# Matches a frontmatter ``inclusion:`` line regardless of its current value
# (quoted or unquoted), applied to a line with its terminator already removed.
# Anchored at line start (after optional indentation) so it never matches a
# ``description:`` continuation line or any other key.
_INCLUSION_RE = re.compile(r'^(?P<indent>[ \t]*)inclusion:[ \t]*["\']?[^"\'\r\n]*["\']?[ \t]*$')

# Matches an existing ``fileMatchPattern:`` frontmatter line.
_FILEMATCH_RE = re.compile(r"^[ \t]*fileMatchPattern:")


def _split_eol(line: str) -> tuple[str, str]:
    """Split a line into its text and its trailing line terminator.

    Args:
        line: A single line, typically produced by ``str.splitlines(keepends=True)``,
            which may end in ``\\r\\n``, ``\\n``, ``\\r``, or nothing (final line).

    Returns:
        A ``(text, eol)`` pair where ``text + eol == line``. ``eol`` is the empty
        string when the line carries no terminator.
    """
    for eol in ("\r\n", "\n", "\r"):
        if line.endswith(eol):
            return line[: -len(eol)], eol
    return line, ""


def _filematch_line(pattern: str, indent: str, eol: str) -> str:
    """Render a ``fileMatchPattern:`` frontmatter line for ``pattern``.

    Uses the double-quoted form (``fileMatchPattern: "**/*.py"``) that matches the
    convention of the existing ``fileMatch`` steering files.

    Args:
        pattern: The glob written verbatim inside the double quotes.
        indent: Leading whitespace to mirror (usually the ``inclusion:`` indent).
        eol: The line terminator to append.

    Returns:
        The formatted frontmatter line including its terminator.
    """
    return f'{indent}fileMatchPattern: "{pattern}"{eol}'


def rewrite_inclusion(
    content: str, mode: str, file_match_pattern: str | None = None
) -> str:
    """Rewrite a steering file's inclusion mode, preserving everything else.

    Operates only on the leading ``---``-fenced frontmatter block. The
    ``inclusion:`` value is replaced with ``mode`` (its indentation and line
    terminator preserved); the ``description:`` line, its continuation lines, and
    every other frontmatter line are left byte-identical; the closing fence and the
    entire body after it are copied through byte-for-byte. When ``mode`` is
    ``"fileMatch"`` a single ``fileMatchPattern:`` line equal to
    ``file_match_pattern`` is ensured (inserted directly after the ``inclusion:``
    line when absent, or reconciled to a single line when already present); for the
    other modes no ``fileMatchPattern`` line is injected.

    When the frontmatter has no ``inclusion:`` line, one is inserted as the first
    line of the block so the returned content always declares ``mode``.

    Args:
        content: The full text of a steering Markdown file (frontmatter + body).
        mode: The target standard mode, one of ``{"always", "fileMatch", "manual"}``.
        file_match_pattern: The glob for ``fileMatch``; required and non-empty when
            ``mode == "fileMatch"`` and otherwise ignored.

    Returns:
        The rewritten file content. Only the ``inclusion:`` line (and, for
        ``fileMatch``, a single ``fileMatchPattern:`` line) differ from ``content``;
        the description, all other frontmatter, and the body are unchanged.

    Raises:
        ValueError: If ``mode`` is not in ``{"always", "fileMatch", "manual"}``; if
            ``mode == "fileMatch"`` without a non-empty ``file_match_pattern``; or if
            ``content`` has no leading ``---`` frontmatter block closed by a ``---``
            fence.
    """
    if mode not in VALID_MODES:
        raise ValueError(
            f"mode must be one of {sorted(VALID_MODES)}, got {mode!r}"
        )
    if mode == "fileMatch" and (file_match_pattern is None or not file_match_pattern.strip()):
        raise ValueError("mode 'fileMatch' requires a non-empty file_match_pattern")

    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != _FENCE:
        raise ValueError("content has no leading '---' frontmatter block")

    close_idx: int | None = None
    for i in range(1, len(lines)):
        text, _ = _split_eol(lines[i])
        if text.strip() == _FENCE:
            close_idx = i
            break
    if close_idx is None:
        raise ValueError("frontmatter block is not closed by a '---' fence")

    opening = lines[0]
    fm_lines = lines[1:close_idx]
    # Closing fence + body are preserved byte-for-byte via a raw slice.
    closing_and_body = "".join(lines[close_idx:])

    # Default terminator for any inserted line: mirror the opening fence, else LF.
    _, default_eol = _split_eol(opening)
    default_eol = default_eol or "\n"

    # Locate the inclusion line and any existing fileMatchPattern lines.
    inclusion_idx: int | None = None
    inclusion_indent = ""
    inclusion_eol = default_eol
    filematch_indices: list[int] = []
    for idx, raw in enumerate(fm_lines):
        text, eol = _split_eol(raw)
        match = _INCLUSION_RE.match(text)
        if match and inclusion_idx is None:
            inclusion_idx = idx
            inclusion_indent = match.group("indent")
            inclusion_eol = eol or default_eol
        elif _FILEMATCH_RE.match(text):
            filematch_indices.append(idx)

    first_filematch = filematch_indices[0] if filematch_indices else None

    new_fm: list[str] = []

    # No existing inclusion line: prepend one so the output always declares mode.
    if inclusion_idx is None:
        new_fm.append(f"{inclusion_indent}inclusion: {mode}{inclusion_eol}")
        if mode == "fileMatch" and first_filematch is None:
            new_fm.append(
                _filematch_line(file_match_pattern, inclusion_indent, inclusion_eol)
            )

    for idx, raw in enumerate(fm_lines):
        if idx == inclusion_idx:
            new_fm.append(f"{inclusion_indent}inclusion: {mode}{inclusion_eol}")
            if mode == "fileMatch" and first_filematch is None:
                new_fm.append(
                    _filematch_line(file_match_pattern, inclusion_indent, inclusion_eol)
                )
            continue
        if mode == "fileMatch" and idx in filematch_indices:
            # Keep exactly one fileMatchPattern line, equal to the decided glob,
            # at the position of the first existing one; drop any duplicates.
            if idx == first_filematch:
                _, existing_eol = _split_eol(raw)
                existing_indent = re.match(r"^[ \t]*", raw).group(0)
                new_fm.append(
                    _filematch_line(
                        file_match_pattern,
                        existing_indent,
                        existing_eol or default_eol,
                    )
                )
            continue
        new_fm.append(raw)

    return opening + "".join(new_fm) + closing_and_body
