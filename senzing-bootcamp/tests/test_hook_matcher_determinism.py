#!/usr/bin/env python3
"""Property tests for Matcher_Translator translation determinism/idempotence.

Feature: kiro-1-0-migration, Property 2: Translation determinism and idempotence

Exercises ``scripts/hook_matcher.py``'s ``patterns_to_matcher`` as the pure,
deterministic function it is: for any legacy ``when.patterns`` glob list,
translating it repeatedly must yield a byte-identical matcher regex, and the
set of sample paths that regex matches must be preserved across repeated
translation.

The ``st_glob()`` / ``st_path()`` strategies here are kept local to this file so
the parallel Matcher_Translator test tasks do not share (and cannot clobber)
generators. ``st_glob()`` follows the same glob->regex input semantics the
implementation documents: it only produces globs the translator accepts
(non-empty, balanced character classes), mixing the shipped glob vocabulary from
the design with fuzzed wildcard/segment combinations.

Validates: Requirements 3.5
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# ---------------------------------------------------------------------------
# Import the script under test via sys.path (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from hook_matcher import patterns_to_matcher  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions), local to this file.
# ---------------------------------------------------------------------------

# Literal path-segment characters (no glob metacharacters, no '/').
_SEGMENT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)

# Path characters for sampled workspace-relative paths.
_PATH_SEGMENT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789._-"

# The shipped glob vocabulary from the design's representative table plus a few
# related shapes (leading dot, substring wildcard, '?', character class, '**'
# at various positions). Every entry is accepted by ``patterns_to_matcher``.
_GLOB_VOCABULARY: tuple[str, ...] = (
    "src/**/*.py",
    "src/load/*.*",
    "config/*credentials*",
    ".env*",
    "data/transformed/*.jsonl",
    "*.py",
    "**/*.java",
    "src/**",
    "test_?.py",
    "[abc]*.txt",
    "docs/**/*.md",
)

# Fixed representative sample paths spanning matches and misses for the
# vocabulary above, so the matched-path set comparison is substantive.
_SAMPLE_PATHS: tuple[str, ...] = (
    "src/main.py",
    "src/load/loader.py",
    "src/load/data.jsonl",
    "src/util/deep/module.py",
    "config/db_credentials.yaml",
    ".env",
    ".env.local",
    "data/transformed/records.jsonl",
    "docs/guides/quickstart.md",
    "README.md",
    "test_a.py",
    "abc.txt",
)


@composite
def st_char_class(draw) -> str:
    """Draw a balanced glob character class such as ``[abc]`` or ``[!a-z]``.

    Members are drawn from a metacharacter-free alphabet (never ``[`` or ``]``),
    so the produced class is always balanced and accepted by the translator.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A balanced glob character-class token including its brackets.
    """
    members = draw(
        st.one_of(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=4),
            st.sampled_from(("a-z", "0-9", "A-Z")),
        )
    )
    negate = draw(st.booleans())
    prefix = "!" if negate else ""
    return f"[{prefix}{members}]"


@composite
def st_glob_token(draw) -> str:
    """Draw one glob token: a literal run, a wildcard, ``?``, or a char class.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single glob token containing no path separator.
    """
    return draw(
        st.one_of(
            st.text(alphabet=_SEGMENT_ALPHABET, min_size=1, max_size=6),
            st.just("*"),
            st.just("**"),
            st.just("?"),
            st_char_class(),
        )
    )


@composite
def st_glob(draw) -> str:
    """Draw a single workspace-relative glob the translator accepts.

    Half the time draws directly from the shipped glob vocabulary; otherwise
    assembles 1-3 ``/``-joined segments from :func:`st_glob_token`. All results
    are non-empty with balanced character classes, so ``patterns_to_matcher``
    never raises ``GlobTranslationError`` on them.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single glob string.
    """
    if draw(st.booleans()):
        return draw(st.sampled_from(_GLOB_VOCABULARY))

    n_segments = draw(st.integers(min_value=1, max_value=3))
    segments: list[str] = []
    for _ in range(n_segments):
        tokens = draw(st.lists(st_glob_token(), min_size=1, max_size=3))
        segments.append("".join(tokens))
    glob = "/".join(segments)
    assume(glob.strip())  # guard: never an empty/whitespace-only glob
    return glob


@composite
def st_path(draw) -> str:
    """Draw a workspace-relative POSIX path (forward slashes, no leading slash).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty ``/``-joined path over :data:`_PATH_SEGMENT_ALPHABET`.
    """
    n_segments = draw(st.integers(min_value=1, max_value=4))
    segments: list[str] = []
    for _ in range(n_segments):
        segments.append(
            draw(st.text(alphabet=_PATH_SEGMENT_ALPHABET, min_size=1, max_size=8))
        )
    path = "/".join(segments)
    assume(path.strip())
    return path


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestTranslationDeterminism:
    """Property 2: Translation determinism and idempotence.

    Feature: kiro-1-0-migration, Property 2: Translation determinism and
    idempotence.

    ``patterns_to_matcher`` is a pure function of its input glob list:
    re-running it yields a byte-identical matcher regex, and that matcher
    matches exactly the same set of sample paths across repeated translation.

    Validates: Requirements 3.5
    """

    @given(
        patterns=st.lists(st_glob(), min_size=1, max_size=6),
        extra_paths=st.lists(st_path(), max_size=8),
    )
    def test_repeated_translation_is_byte_identical_and_match_set_stable(
        self, patterns: list[str], extra_paths: list[str]
    ) -> None:
        """Repeated translation yields the same regex and same matched-path set.

        Args:
            patterns: A non-empty list of translator-accepted globs.
            extra_paths: Additional sampled paths appended to the fixed sample.
        """
        # Repeated translation of the same input (and of an equal fresh copy)
        # must be byte-identical -- the function carries no hidden state.
        regex_a = patterns_to_matcher(patterns)
        regex_b = patterns_to_matcher(patterns)
        regex_c = patterns_to_matcher(list(patterns))
        assert regex_a == regex_b == regex_c

        # Evaluating the matcher produced by each translation must preserve the
        # same set of matched sample paths.
        sample_paths = list(_SAMPLE_PATHS) + list(extra_paths)
        compiled_a = re.compile(regex_a)
        compiled_c = re.compile(regex_c)
        matched_a = {p for p in sample_paths if compiled_a.match(p)}
        matched_c = {p for p in sample_paths if compiled_c.match(p)}
        assert matched_a == matched_c

    def test_vocabulary_translation_is_deterministic(self) -> None:
        """Each shipped-vocabulary glob list translates identically on repeat.

        Example-based reinforcement of the determinism property over the exact
        globs the migration will translate.
        """
        for glob in _GLOB_VOCABULARY:
            first = patterns_to_matcher([glob])
            second = patterns_to_matcher([glob])
            assert first == second

        combined_first = patterns_to_matcher(list(_GLOB_VOCABULARY))
        combined_second = patterns_to_matcher(list(_GLOB_VOCABULARY))
        assert combined_first == combined_second
