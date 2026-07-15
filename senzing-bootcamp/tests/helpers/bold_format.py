"""Bold `👉` question formatting helpers for the onboarding-session-ux feature.

This module codifies, as executable Python, the bold-question formatting
convention the bootcamp agent is expected to follow (enforced at runtime by
steering, not by code). It exists so the feature's property tests can validate
the convention's correctness properties:

- **Property 1 — Question formatting idempotence.** :func:`format_bold_question`
  wraps a question's text in ``👉 **{text}**`` with the ``👉`` pointer *outside*
  the bold span, and is idempotent: re-applying it to already-formatted output
  yields an identical string (no nested ``**`` markers, no duplicated pointer).
- **Property 2 — Choice question separates lead from options.**
  :func:`format_choice_question` renders the lead question in bold and every
  numbered option line in plain text (no ``**`` markers on option lines).
- **Property 3 — Bold-marker-transparent validation.**
  :func:`strip_bold_markers` removes every ``**`` marker so validation logic can
  compare wording independently of the presence of bold emphasis.

Feature: onboarding-session-ux

Validates: Requirements 3.1, 3.2, 3.3, 3.6
"""

from __future__ import annotations

# The 👉 pointer marks a leading question. It always sits at the start of the
# line, outside the bold span, separated from the question text by one space.
POINTER: str = "\U0001f449"  # 👉

# CommonMark strong-emphasis (bold) marker.
BOLD_MARKER: str = "**"


def strip_bold_markers(text: str) -> str:
    """Remove every CommonMark bold (``**``) marker from ``text``.

    Removing all ``**`` markers yields the marker-free wording, which lets
    validation logic reach the same verdict whether or not the input carried
    bold emphasis (the invariance the write-policy-gate relies on).

    Args:
        text: The string to strip bold markers from.

    Returns:
        ``text`` with all ``**`` occurrences removed. Single-asterisk italic
        markers are left untouched.
    """
    return text.replace(BOLD_MARKER, "")


def _clean_question_text(text: str) -> str:
    """Reduce ``text`` to its bare question wording.

    Strips all bold markers, surrounding whitespace, and any leading ``👉``
    pointer(s). This is the normalization that makes :func:`format_bold_question`
    idempotent: applying it to already-formatted output recovers the original
    wording so re-wrapping cannot nest ``**`` markers or duplicate the pointer.

    Args:
        text: The raw or already-formatted question text.

    Returns:
        The question wording with no bold markers and no leading pointer.
    """
    cleaned = strip_bold_markers(text).strip()
    while cleaned.startswith(POINTER):
        cleaned = cleaned[len(POINTER):].lstrip()
    return cleaned.strip()


def format_bold_question(text: str) -> str:
    """Format ``text`` as a bold ``👉`` leading question.

    Produces ``👉 **{text}**`` with the ``👉`` pointer at the start of the line,
    outside the bold span, separated from the bold question text by a single
    space. The function is idempotent: applying it to output it previously
    produced (or to text that already carries a leading pointer and/or bold
    markers) yields an identical string rather than nesting ``**`` markers or
    duplicating the pointer.

    Args:
        text: The question text to format. May already be formatted.

    Returns:
        The question formatted as ``👉 **{text}**``.
    """
    return f"{POINTER} {BOLD_MARKER}{_clean_question_text(text)}{BOLD_MARKER}"


def format_choice_question(lead: str, options: list[str]) -> str:
    """Format a bold lead question followed by plain numbered option lines.

    The lead question is rendered in bold via :func:`format_bold_question`
    (``👉 **{lead}**``). Each option is rendered on its own line as ``{n}. {opt}``
    in plain text with all bold markers removed, so no option line contains
    ``**``.

    Args:
        lead: The lead question text (formatted in bold).
        options: The choice options, rendered as plain numbered lines in order.

    Returns:
        A newline-joined string: the bold lead line followed by one plain
        numbered line per option.
    """
    lines = [format_bold_question(lead)]
    for number, option in enumerate(options, start=1):
        plain_option = strip_bold_markers(option).strip()
        lines.append(f"{number}. {plain_option}")
    return "\n".join(lines)
