#!/usr/bin/env python3
"""Senzing Bootcamp - Matcher_Translator for the Kiro 1.0 hook migration.

Single source of truth for converting legacy ``*.kiro.hook`` scoping
(``when.patterns`` file globs and ``when.toolTypes`` category lists) into the
Kiro 1.0 ``matcher`` regular expression. The migration transform and any
build/verify tooling that reasons about matchers import this module so the
translation has exactly one tested definition and one set of correctness
properties bound to it.

Two matcher shapes are produced:

* **File-path matcher** — legacy ``when.patterns`` globs are translated to
  anchored regex fragments over the forward-slash-normalized, workspace-relative
  path domain (the same domain the legacy engine matched against) and combined
  as ``^(?:frag1|frag2|...)$``.
* **Tool-name matcher** — legacy ``when.toolTypes`` categories map to the 1.0
  tool-name alternation regex (``write`` -> ``fs_write|str_replace|fs_append``,
  ``shell`` -> ``execute_bash``). Tool-name matchers are not anchored.

Only the Python standard library is used.

Usage (CLI, for debugging a translation):
    python hook_matcher.py "src/**/*.py" "config/*credentials*"
"""

from __future__ import annotations

import argparse
import re
import sys

__all__ = [
    "GlobTranslationError",
    "glob_to_regex",
    "patterns_to_matcher",
    "tooltypes_to_matcher",
    "translate_scope",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class GlobTranslationError(ValueError):
    """Raised when a glob or toolTypes entry cannot be translated to a matcher.

    The message names the offending pattern; the migration transform wraps this
    to additionally name the owning hook before failing the migration
    (Requirement 3.6).
    """


# ---------------------------------------------------------------------------
# Tool-name matchers (Kiro 1.0 tool taxonomy)
# ---------------------------------------------------------------------------

#: Fixed write tool-name matcher (Requirement 3.3). The three built-in file
#: write tools in the Kiro 1.0 tool taxonomy.
_WRITE_TOOL_MATCHER = "fs_write|str_replace|fs_append"

#: Shell/command tool-name matcher.
#:
#: Resolved open detail (error-recovery-context, Task 1.1): the Kiro 1.0 hook
#: matcher taxonomy uses the canonical built-in tool name ``execute_bash`` for
#: shell/command execution (the ``shell`` category is an alias for it). This is
#: the confirmed 1.0 shell tool name and mirrors how the ``write`` category maps
#: to the concrete write tool names. If a future Kiro release renames this tool,
#: update this single constant.
_SHELL_TOOL_MATCHER = "execute_bash"

#: toolTypes category -> tool-name matcher.
_TOOLTYPE_MATCHERS: dict[str, str] = {
    "write": _WRITE_TOOL_MATCHER,
    "shell": _SHELL_TOOL_MATCHER,
}


# ---------------------------------------------------------------------------
# Glob -> regex fragment
# ---------------------------------------------------------------------------


def _translate_char_class(body: str) -> str:
    """Translate a glob character-class body to a regex character class.

    ``body`` is the text between ``[`` and its matching ``]`` (exclusive). A
    leading ``!`` negates the class (glob convention) and becomes a leading
    ``^`` in the regex class (fnmatch convention). An empty body matches
    nothing; a lone ``!`` (negated-empty) matches any single character.

    Args:
        body: The raw character-class content (without the surrounding
            brackets).

    Returns:
        A regex character-class fragment (including surrounding brackets) or an
        equivalent zero-width construct for the empty/negated-empty edge cases.
    """
    if body == "":
        # An empty class matches nothing.
        return "(?!)"
    if body == "!":
        # A negated-empty class matches any single character.
        return "."
    stuff = body.replace("\\", r"\\")
    if stuff[0] == "!":
        stuff = "^" + stuff[1:]
    elif stuff[0] in ("^", "["):
        stuff = "\\" + stuff
    return f"[{stuff}]"


def glob_to_regex(glob: str) -> str:
    """Translate one workspace-relative glob into a regex fragment.

    Implements the glob->regex algorithm over the forward-slash-normalized,
    workspace-relative path domain:

    1. Escape all regex metacharacters except the glob wildcards ``* ? [ ]``.
    2. ``**/`` -> ``(?:.*/)?`` (zero or more leading path segments).
    3. Remaining ``**`` -> ``.*`` (any characters, crossing ``/``).
    4. Single ``*`` -> ``[^/]*`` (any characters within one path segment).
    5. ``?`` -> ``[^/]`` (single non-separator character).
    6. Literal ``.`` -> ``\\.``.
    7. Preserve balanced ``[...]`` character classes; reject unbalanced brackets.

    The returned fragment is not anchored; :func:`patterns_to_matcher` anchors
    and alternates fragments as ``^(?:frag1|frag2|...)$``.

    Args:
        glob: A single workspace-relative glob (e.g. ``"src/**/*.py"``).

    Returns:
        The regex fragment for the glob.

    Raises:
        GlobTranslationError: If the glob is empty/whitespace-only, contains an
            unbalanced character class, or otherwise cannot be represented as a
            valid regex.
    """
    if not glob or not glob.strip():
        raise GlobTranslationError(
            f"empty or whitespace-only glob cannot be translated: {glob!r}"
        )

    parts: list[str] = []
    i = 0
    n = len(glob)
    while i < n:
        char = glob[i]

        if char == "*":
            if i + 1 < n and glob[i + 1] == "*":
                # Double star.
                if i + 2 < n and glob[i + 2] == "/":
                    # '**/' -> zero or more leading path segments.
                    parts.append("(?:.*/)?")
                    i += 3
                else:
                    # Trailing/embedded '**' -> any characters, crossing '/'.
                    parts.append(".*")
                    i += 2
            else:
                # Single '*' -> any characters within one path segment.
                parts.append("[^/]*")
                i += 1
            continue

        if char == "?":
            parts.append("[^/]")
            i += 1
            continue

        if char == "[":
            # Locate the matching ']'. A '!' right after '[' negates the class;
            # a ']' immediately after '[' or '[!' is a literal member.
            j = i + 1
            if j < n and glob[j] == "!":
                j += 1
            if j < n and glob[j] == "]":
                j += 1
            while j < n and glob[j] != "]":
                j += 1
            if j >= n:
                raise GlobTranslationError(
                    f"unbalanced character class in glob: {glob!r}"
                )
            body = glob[i + 1:j]
            parts.append(_translate_char_class(body))
            i = j + 1
            continue

        # Any other character is a literal: escape regex metacharacters
        # (this covers rule 6, literal '.' -> '\.').
        parts.append(re.escape(char))
        i += 1

    fragment = "".join(parts)

    # Safety net for Requirement 3.6: the fragment must be a valid regex.
    try:
        re.compile(fragment)
    except re.error as exc:
        raise GlobTranslationError(
            f"glob produced an invalid regex fragment: {glob!r} ({exc})"
        ) from exc

    return fragment


# ---------------------------------------------------------------------------
# Combined matchers
# ---------------------------------------------------------------------------


def patterns_to_matcher(patterns: list[str]) -> str:
    """Combine globs into a single anchored file-path matcher.

    Each glob is translated with :func:`glob_to_regex`, then the fragments are
    anchored and alternated as ``^(?:frag1|frag2|...)$`` over the
    workspace-relative path domain. Anchoring front-and-back reproduces the
    legacy "matches iff at least one glob matched" semantics (Requirement 3.2).

    Args:
        patterns: A non-empty list of workspace-relative globs.

    Returns:
        A single anchored file-path matcher regex.

    Raises:
        GlobTranslationError: If ``patterns`` is empty, or if any glob cannot be
            translated, or if the combined matcher is not a valid regex.
    """
    if not patterns:
        raise GlobTranslationError(
            "cannot build a file-path matcher from an empty patterns list"
        )

    fragments = [glob_to_regex(pattern) for pattern in patterns]
    matcher = "^(?:" + "|".join(fragments) + ")$"

    # Safety net for Requirement 3.6: the combined matcher must compile.
    try:
        re.compile(matcher)
    except re.error as exc:
        raise GlobTranslationError(
            f"combined patterns produced an invalid regex: {patterns!r} ({exc})"
        ) from exc

    return matcher


def tooltypes_to_matcher(tool_types: list[str]) -> str:
    """Map a toolTypes category list to a 1.0 tool-name matcher regex.

    * ``write`` -> ``fs_write|str_replace|fs_append`` (fixed by Requirement 3.3).
      ``write`` takes precedence: any list containing ``write`` yields exactly
      the write matcher.
    * ``shell`` -> ``execute_bash`` (the 1.0 shell/command tool name).

    Tool-name matchers are not anchored.

    Args:
        tool_types: A non-empty list of legacy toolTypes categories.

    Returns:
        The tool-name matcher regex.

    Raises:
        GlobTranslationError: If ``tool_types`` is empty or contains an
            unsupported category.
    """
    if not tool_types:
        raise GlobTranslationError(
            "cannot build a tool-name matcher from an empty toolTypes list"
        )

    # 'write' is fixed by Requirement 3.3 and takes precedence: any toolTypes
    # list containing 'write' yields exactly the fixed write matcher.
    if "write" in tool_types:
        return _WRITE_TOOL_MATCHER

    matchers: list[str] = []
    for tool_type in tool_types:
        try:
            matchers.append(_TOOLTYPE_MATCHERS[tool_type])
        except KeyError:
            raise GlobTranslationError(
                f"unsupported toolTypes entry: {tool_type!r}"
            ) from None
    return "|".join(matchers)


def translate_scope(when: dict) -> str | None:
    """Return the 1.0 matcher for a legacy ``when`` block, or ``None``.

    A ``when`` block scoped by file globs yields a file-path matcher; one scoped
    by toolTypes yields a tool-name matcher. A ``when`` block with neither
    ``patterns`` nor ``toolTypes`` (unscoped triggers such as ``agentStop``,
    ``promptSubmit``, ``postTaskExecution``) yields ``None`` so the emitter omits
    the ``matcher`` key (Requirement 3.4).

    Args:
        when: The legacy ``when`` block (may contain ``patterns`` and/or
            ``toolTypes``).

    Returns:
        The matcher regex string, or ``None`` for an unscoped block.

    Raises:
        GlobTranslationError: If present patterns/toolTypes cannot be translated.
    """
    patterns = when.get("patterns")
    if patterns:
        return patterns_to_matcher(patterns)

    tool_types = when.get("toolTypes")
    if tool_types:
        return tooltypes_to_matcher(tool_types)

    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Translate one or more globs to a combined file-path matcher.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 on a translation error.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Translate workspace-relative globs into a Kiro 1.0 file-path "
            "matcher regex."
        )
    )
    parser.add_argument(
        "globs",
        nargs="+",
        help="one or more workspace-relative globs to translate",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        matcher = patterns_to_matcher(args.globs)
    except GlobTranslationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(matcher)
    return 0


if __name__ == "__main__":
    sys.exit(main())
