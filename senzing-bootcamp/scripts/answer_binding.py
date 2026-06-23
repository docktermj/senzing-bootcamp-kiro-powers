#!/usr/bin/env python3
"""Senzing Bootcamp - Answer Binding Module.

Binds a bootcamper's bare option-token reply (a single number or letter that
matches a presented numbered/lettered option list) to the corresponding option,
so an Option_List question's answer is consumed and the workflow advances
without re-asking. Replies that carry additional free-text meaning (for example
``"3 million"`` or ``"around 3"``) are NOT bare tokens and do not bind; callers
fall through to their existing free-text parsing (e.g.
``volume_utils.parse_volume_input``).

Usage:
    # Bind a bare numeric token to a four-option list (prints: 3)
    python answer_binding.py 3 "demo" "small" "medium" "large"

    # A bare letter binds case-insensitively (prints: 2)
    python answer_binding.py B "a-opt" "b-opt" "c-opt"

    # A number-with-units reply does not bind (prints: no bind)
    python answer_binding.py "3 million" "demo" "small" "medium" "large"
"""

from __future__ import annotations

import argparse
import re
import sys

# ---------------------------------------------------------------------------
# Token parsing
# ---------------------------------------------------------------------------

# A bare Option_Token is a single number ("3", "3.", "(3)", " 3 ") or a single
# letter ("b", "B)", "b."), optionally wrapped in parentheses and/or followed by
# a single "." or ")" decorator. Anything with extra free-text meaning (e.g.
# "3 million", "around 3", "option three please") is not a bare token.
_BARE_TOKEN_PATTERN = re.compile(r"^\(?\s*([0-9]+|[A-Za-z])\s*[).]?$")


def parse_option_token(reply: str) -> str | None:
    """Parse a reply into its normalized bare Option_Token, if it is one.

    Accepts a single number or single letter, optionally wrapped in parentheses
    and/or followed by a single ``.`` or ``)`` decorator and surrounding
    whitespace (``"3"``, ``"3."``, ``"(3)"``, ``" 3 "``, ``"b"``, ``"B)"``,
    ``"b."``). Numbers are returned as their digit string; letters are
    normalized to lowercase. Returns ``None`` when the reply carries additional
    free-text meaning (``"3 million"``, ``"around 3"``, ``"option three
    please ..."``), or is empty/whitespace.

    Args:
        reply: Raw bootcamper reply string.

    Returns:
        The normalized bare Option_Token (digit string or lowercase letter), or
        None when the reply is not a bare Option_Token.
    """
    if not reply or not reply.strip():
        return None

    match = _BARE_TOKEN_PATTERN.match(reply.strip())
    if match is None:
        return None

    token = match.group(1)
    if token.isdigit():
        return token
    return token.lower()


# ---------------------------------------------------------------------------
# Option binding
# ---------------------------------------------------------------------------


def bind_option(reply: str, options: list[str]) -> int | None:
    """Bind a bare option-token reply to a 1-based index in ``options``.

    Uses :func:`parse_option_token` to detect a bare token, then maps it to a
    1-based option index. Numeric tokens map directly (``"3"`` -> 3); letters
    map case-insensitively to their alphabetic position (``a`` -> 1, ``b`` -> 2,
    ...). Returns ``None`` when the reply is not a bare token or the token is out
    of range for the presented option list.

    Args:
        reply: Raw bootcamper reply string.
        options: The presented option list (1-based when bound).

    Returns:
        The 1-based index of the bound option, or None when the reply is not a
        bare matching token within range.
    """
    token = parse_option_token(reply)
    if token is None:
        return None

    if token.isdigit():
        index = int(token)
    else:
        index = ord(token) - ord("a") + 1

    if 1 <= index <= len(options):
        return index
    return None


def is_bare_matching_token(reply: str, options: list[str]) -> bool:
    """Report whether ``reply`` is a bare token matching a presented option.

    Mirrors ``isBareMatchingToken`` in the bug condition: true exactly when
    :func:`bind_option` binds the reply to an option in range.

    Args:
        reply: Raw bootcamper reply string.
        options: The presented option list.

    Returns:
        True when the reply binds to an in-range option, False otherwise.
    """
    return bind_option(reply, options) is not None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Bind a reply against an option list and print the result.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error (no options provided).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Answer Binding Module."
    )
    parser.add_argument("reply", help="The bootcamper's reply string.")
    parser.add_argument(
        "options",
        nargs="*",
        help="The presented option list, in order.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.options:
        print("error: at least one option is required", file=sys.stderr)
        return 1

    index = bind_option(args.reply, args.options)
    if index is None:
        print("no bind")
    else:
        print(index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
