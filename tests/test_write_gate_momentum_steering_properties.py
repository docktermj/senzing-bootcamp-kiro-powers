"""Property 6 tests for the write-gate-momentum-preservation feature.

Outcome A places the leading-question guarantee in two ``auto``-inclusion
steering files so the behavior is enforced consistently across every module
without depending on any hook to supply the closing question. This module
guards that governance against drift: over the cross-product of the two
governed steering files and the four required governance statements, each
statement must be present in each on-disk file, and the two files must not
contain conflicting wording.

The four required governance statements are:

- (a) every yielding turn ends with exactly one 👉 leading question
- (b) an intercept-reissued write turn ends with exactly one 👉 leading question
- (c) the agent owns the closing question and does not depend on a hook
- (d) the One Question Rule — exactly one per yielding turn; zero or two-plus
  violates

Presence checks use robust keyword/substring matching (case-insensitive, with
whitespace collapsed) rather than brittle exact-string matches, so they remain
stable under minor wording edits while still failing if a guarantee is removed.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1, 3.2,
3.3, 3.4, 3.5**
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths to the two governed steering files (Requirement 3.5).
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = (
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "steering"
)

_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_AGENT_BEHAVIOR_RULES: Path = _STEERING_DIR / "agent-behavior-rules.md"

_GOVERNED_FILES: dict[str, Path] = {
    "conversation-protocol.md": _CONVERSATION_PROTOCOL,
    "agent-behavior-rules.md": _AGENT_BEHAVIOR_RULES,
}

# The four required governance statements, keyed (a)-(d).
_STATEMENTS: tuple[str, ...] = ("a", "b", "c", "d")


def _normalize(text: str) -> str:
    """Lowercase a string and collapse all runs of whitespace to one space.

    Robust keyword matching should not break on line wrapping, double spaces,
    or letter casing in the steering Markdown.

    Args:
        text: The raw text to normalize.

    Returns:
        The lowercased, whitespace-collapsed text.
    """
    return re.sub(r"\s+", " ", text).lower()


def _load_normalized(file_key: str) -> str:
    """Load a governed steering file and return its normalized content.

    Args:
        file_key: One of the keys in :data:`_GOVERNED_FILES`.

    Returns:
        The normalized file content.
    """
    path = _GOVERNED_FILES[file_key]
    assert path.exists(), f"governed steering file not found: {path}"
    return _normalize(path.read_text(encoding="utf-8"))


def _statement_present(statement: str, content: str) -> bool:
    """Return whether a governance statement is present in normalized content.

    Each statement is matched by a conjunction of keyword signals chosen to be
    robust to minor wording changes while still requiring the substance of the
    guarantee.

    Args:
        statement: One of ``"a"``, ``"b"``, ``"c"``, ``"d"``.
        content: Normalized steering-file content.

    Returns:
        ``True`` when the statement's required signals are all present.
    """
    if statement == "a":
        # Every yielding turn ends with exactly one 👉 leading question.
        return (
            "exactly one" in content
            and "yielding turn" in content
            and "leading question" in content
            and "👉" in content
        )
    if statement == "b":
        # An intercept-reissued write turn ends with exactly one 👉 question.
        reissue = any(
            token in content for token in ("re-issued", "reissued", "re-issue")
        )
        return (
            "intercept" in content
            and reissue
            and "exactly one" in content
            and "leading question" in content
        )
    if statement == "c":
        # The agent owns the closing question and does not depend on a hook.
        disclaims_hook = any(
            phrase in content
            for phrase in (
                "do not rely on hook",
                "do not depend on a hook",
                "not deferred to a hook",
                "not relieve",
            )
        )
        return (
            "your responsibility" in content
            and "hook" in content
            and disclaims_hook
        )
    if statement == "d":
        # One Question Rule: exactly one per yielding turn; zero or 2+ violates.
        return (
            "exactly one" in content
            and "zero" in content
            and "two or more" in content
            and "violat" in content
        )
    raise ValueError(f"unknown governance statement: {statement!r}")


# Phrases that, if present in EITHER governed file, would contradict the shared
# canonical governance and therefore constitute conflicting wording. The files
# must agree that (count) exactly one leading question is required per yielding
# turn and that (ownership) the agent — not a hook — owns the closing question.
_CONFLICT_PHRASES: tuple[str, ...] = (
    "exactly two leading questions per yielding turn",
    "two leading questions per yielding turn",
    "the hook provides the closing question",
    "the hook is responsible for the closing question",
    "defer the closing question to a hook",
    "rely on a hook to provide the closing question",
)


def st_governed_file() -> st.SearchStrategy[str]:
    """Strategy over the two governed steering-file keys."""
    return st.sampled_from(sorted(_GOVERNED_FILES))


def st_statement() -> st.SearchStrategy[str]:
    """Strategy over the four required governance statement keys."""
    return st.sampled_from(list(_STATEMENTS))


# ===========================================================================
# Property 6: Steering governs the leading-question guarantee in both files
# without conflict
# ===========================================================================
# Feature: write-gate-momentum-preservation, Property 6: For any of the four
# required governance statements (a-d) and for each of the two governed
# steering files (conversation-protocol.md, agent-behavior-rules.md), the
# statement is present, and the two files do not contain conflicting wording.

class TestSteeringGovernsLeadingQuestionGuarantee:
    """The leading-question guarantee is governed in both steering files
    without conflicting wording.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 3.1,
    3.2, 3.3, 3.4, 3.5**
    """

    @given(file_key=st_governed_file(), statement=st_statement())
    @settings(max_examples=200)
    @example(file_key="conversation-protocol.md", statement="a")
    @example(file_key="conversation-protocol.md", statement="b")
    @example(file_key="conversation-protocol.md", statement="c")
    @example(file_key="conversation-protocol.md", statement="d")
    @example(file_key="agent-behavior-rules.md", statement="a")
    @example(file_key="agent-behavior-rules.md", statement="b")
    @example(file_key="agent-behavior-rules.md", statement="c")
    @example(file_key="agent-behavior-rules.md", statement="d")
    def test_statement_present_in_each_file(self, file_key: str, statement: str):
        """Each governance statement is present in each governed file.

        Over the cross-product {conversation-protocol.md,
        agent-behavior-rules.md} × {(a), (b), (c), (d)}, the statement's
        required keyword signals all appear in the on-disk file.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
        """
        content = _load_normalized(file_key)
        assert _statement_present(statement, content), (
            f"governance statement ({statement}) is missing from {file_key}; "
            f"the leading-question guarantee is no longer enforced there"
        )

    @given(file_key=st_governed_file(), statement=st_statement())
    @settings(max_examples=200)
    @example(file_key="conversation-protocol.md", statement="a")
    @example(file_key="agent-behavior-rules.md", statement="d")
    def test_no_conflicting_wording_between_files(
        self, file_key: str, statement: str
    ):
        """Neither governed file contains wording that conflicts with the
        shared canonical governance.

        The two files must agree that exactly one 👉 leading question is
        required per yielding turn and that the agent (not a hook) owns the
        closing question. A contradicting phrase in either file would mean the
        files disagree.

        **Validates: Requirements 3.5**
        """
        content = _load_normalized(file_key)
        for phrase in _CONFLICT_PHRASES:
            assert phrase not in content, (
                f"{file_key} contains conflicting wording {phrase!r} that "
                f"contradicts the shared leading-question governance"
            )
        # Touch the statement parameter so the conflict invariant is exercised
        # across the full cross-product of files × statements.
        assert statement in _STATEMENTS
