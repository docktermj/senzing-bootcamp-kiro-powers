#!/usr/bin/env python3
"""Property test for Matcher_Translator glob-to-regex match-set equivalence.

Feature: kiro-1-0-migration, Property 1: Glob-to-regex match-set equivalence

Exercises ``scripts/hook_matcher.py``'s ``patterns_to_matcher``: for any legacy
``when.patterns`` glob list and any workspace-relative path in a representative
sample, the combined file-path Matcher matches the path *if and only if* at
least one glob in the list matches that path.

The oracle. ``glob_to_regex`` gives ``**`` cross-``/`` semantics and ``*``
within-one-segment semantics. Python's ``fnmatch`` treats ``*`` as crossing
``/`` (so it over-matches relative to a single ``*``), and Python 3.11's
``PurePosixPath.match`` has no faithful ``**`` support and is not front-anchored,
so neither stdlib helper is a faithful oracle for the documented algorithm.
This test therefore uses an independent, from-scratch recursive glob matcher
(:func:`_ref_glob_match`) that reproduces the exact semantics the module
documents:

* ``**/`` matches zero or more leading path segments (regex ``(?:.*/)?``),
* a remaining ``**`` matches any run of characters including ``/`` (``.*``),
* a single ``*`` matches any run of non-``/`` characters (``[^/]*``),
* ``?`` matches one non-``/`` character (``[^/]``),
* balanced ``[...]`` classes match one character (a leading ``!`` negates, and a
  negated class can match ``/`` just as the emitted ``[^...]`` regex does),
* every other character is a literal (a literal ``.`` matches a literal ``.``).

Because that matcher backtracks over the string directly instead of compiling a
regex, it is a genuine differential oracle for ``glob_to_regex`` +
``patterns_to_matcher`` rather than a restatement of them.

``st_glob()`` / ``st_path()`` are kept local to this file (as in the sibling
Matcher_Translator property tests) so the parallel test tasks never share or
clobber generators. ``st_glob()`` only produces globs the translator accepts
(non-empty, balanced character classes) drawn from the shipped glob vocabulary
plus fuzzed wildcard/segment combinations. ``st_path()`` draws
workspace-relative POSIX paths from a vocabulary that overlaps the glob
vocabulary, so sampled paths both hit and miss the drawn globs.

Validates: Requirements 3.1, 3.2
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import assume, example, given, settings
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
# Independent reference glob matcher (the oracle).
# ---------------------------------------------------------------------------


def _class_matches(body: str, char: str) -> bool:
    """Return whether ``char`` is a member of glob character-class ``body``.

    Mirrors the membership semantics of the regex ``hook_matcher`` emits for a
    class body: an empty body matches nothing (``(?!)``), a lone ``!`` matches
    any single character (``.``), a leading ``!`` negates, and ``x-y`` denotes an
    inclusive code-point range. A negated class matches ``/`` because the emitted
    ``[^...]`` regex does.

    Args:
        body: The class content between ``[`` and ``]`` (brackets excluded).
        char: The single character to test for membership.

    Returns:
        True if ``char`` matches the class, else False.
    """
    if body == "":
        return False
    if body == "!":
        return True
    negate = body[0] == "!"
    members = body[1:] if negate else body
    matched = False
    i = 0
    length = len(members)
    while i < length:
        if i + 2 < length and members[i + 1] == "-":
            if members[i] <= char <= members[i + 2]:
                matched = True
            i += 3
        else:
            if members[i] == char:
                matched = True
            i += 1
    return (not matched) if negate else matched


def _ref_glob_match(glob: str, path: str) -> bool:
    """Match ``path`` against ``glob`` using the documented ``glob_to_regex`` rules.

    A from-scratch, backtracking, memoized matcher that consumes ``glob`` and
    ``path`` in lockstep with the exact wildcard/segment tokenization
    ``glob_to_regex`` uses, so it is an oracle independent of the ``re``-based
    implementation. The whole path must be consumed (full-match, anchored).

    Args:
        glob: A single workspace-relative glob (translator-accepted subset).
        path: A workspace-relative POSIX path (forward slashes, no leading ``/``).

    Returns:
        True if the glob matches the entire path, else False.
    """
    n = len(glob)
    m = len(path)
    memo: dict[tuple[int, int], bool] = {}

    def match(gi: int, pi: int) -> bool:
        key = (gi, pi)
        cached = memo.get(key)
        if cached is not None:
            return cached
        result = _match(gi, pi)
        memo[key] = result
        return result

    def _match(gi: int, pi: int) -> bool:
        if gi == n:
            return pi == m
        char = glob[gi]

        if char == "*":
            if gi + 1 < n and glob[gi + 1] == "*":
                if gi + 2 < n and glob[gi + 2] == "/":
                    # '**/' -> (?:.*/)?  : the empty prefix, or any run of
                    # characters (including '/') that ends at a '/'.
                    if match(gi + 3, pi):
                        return True
                    for k in range(pi, m):
                        if path[k] == "/" and match(gi + 3, k + 1):
                            return True
                    return False
                # '**' -> .*  : any run of characters, crossing '/'.
                for k in range(pi, m + 1):
                    if match(gi + 2, k):
                        return True
                return False
            # single '*' -> [^/]*  : any run of non-'/' characters.
            k = pi
            while True:
                if match(gi + 1, k):
                    return True
                if k >= m or path[k] == "/":
                    return False
                k += 1

        if char == "?":
            # '?' -> [^/]  : exactly one non-'/' character.
            if pi < m and path[pi] != "/":
                return match(gi + 1, pi + 1)
            return False

        if char == "[":
            # Locate the matching ']' with the same scan the implementation uses.
            j = gi + 1
            if j < n and glob[j] == "!":
                j += 1
            if j < n and glob[j] == "]":
                j += 1
            while j < n and glob[j] != "]":
                j += 1
            # st_glob only emits balanced classes, so j < n here.
            body = glob[gi + 1:j]
            if pi < m and _class_matches(body, path[pi]):
                return match(j + 1, pi + 1)
            return False

        # Literal character (including '.') -> exact single-character match.
        if pi < m and path[pi] == char:
            return match(gi + 1, pi + 1)
        return False

    return match(0, 0)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions), local to this file.
# ---------------------------------------------------------------------------

# Literal glob-segment characters: no glob metacharacters, no '/'.
_SEGMENT_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)

# Path-segment characters for sampled workspace-relative paths.
_PATH_SEGMENT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789._-"

# Directory/basename/extension pools chosen to overlap the glob vocabulary so
# randomly assembled paths land on both sides of the match/no-match boundary.
_DIR_POOL: tuple[str, ...] = (
    "src", "load", "config", "data", "transformed", "docs", "guides",
    "util", "deep", "tests", "lib",
)
_EXT_POOL: tuple[str, ...] = ("py", "java", "jsonl", "md", "txt", "json", "yaml")
_BASENAME_POOL: tuple[str, ...] = (
    "main", "loader", "data", "module", "app", "credentials", "records",
    "quickstart", "README",
)
_DOTFILE_POOL: tuple[str, ...] = (".env", ".env.local", ".gitignore", ".envrc")

# The shipped glob vocabulary from the design's representative table plus a few
# related shapes. Every entry is accepted by ``patterns_to_matcher``.
_GLOB_VOCABULARY: tuple[str, ...] = (
    "src/**/*.py",
    "src/load/*.*",
    "config/*credentials*",
    ".env*",
    "data/transformed/*.jsonl",
    "*.py",
    "**/*.java",
    "src/**",
    "src/*.py",
    "test_?.py",
    "[abc]*.txt",
    "docs/**/*.md",
)

# Fixed representative sample paths spanning matches and misses for the
# vocabulary above, so the equivalence comparison is substantive.
_SAMPLE_PATHS: tuple[str, ...] = (
    "src/main.py",
    "src/load/loader.py",
    "src/load/data.jsonl",
    "src/util/deep/module.py",
    "config/db_credentials.yaml",
    "config/sub/credentials.txt",
    ".env",
    ".env.local",
    "data/transformed/records.jsonl",
    "data/records.jsonl",
    "docs/guides/quickstart.md",
    "README.md",
    "test_a.py",
    "test_ab.py",
    "abc.txt",
)


@composite
def st_char_class(draw) -> str:
    """Draw a balanced glob character class such as ``[abc]`` or ``[!a-z]``.

    Members come from a metacharacter-free alphabet (never ``[``/``]``), so the
    class is always balanced and accepted by the translator.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A balanced glob character-class token, including its brackets.
    """
    members = draw(
        st.one_of(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
                min_size=1,
                max_size=4,
            ),
            st.sampled_from(("a-z", "0-9", "A-Z")),
        )
    )
    prefix = "!" if draw(st.booleans()) else ""
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
    assume(glob.strip())  # never an empty/whitespace-only glob
    return glob


@composite
def st_path(draw) -> str:
    """Draw a workspace-relative POSIX path (forward slashes, no leading slash).

    Segments are drawn from a pool that overlaps the glob vocabulary, and the
    final segment is sometimes given an extension or replaced with a dotfile, so
    generated paths both match and miss the drawn globs.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty ``/``-joined workspace-relative path.
    """
    n_segments = draw(st.integers(min_value=1, max_value=4))
    segments: list[str] = [
        draw(
            st.one_of(
                st.sampled_from(_DIR_POOL),
                st.text(alphabet=_PATH_SEGMENT_ALPHABET, min_size=1, max_size=6),
            )
        )
        for _ in range(n_segments)
    ]

    final_kind = draw(st.sampled_from(("extension", "dotfile", "as_is")))
    if final_kind == "extension":
        base = draw(st.sampled_from(_BASENAME_POOL))
        ext = draw(st.sampled_from(_EXT_POOL))
        segments[-1] = f"{base}.{ext}"
    elif final_kind == "dotfile":
        segments[-1] = draw(st.sampled_from(_DOTFILE_POOL))

    path = "/".join(segments)
    assume(path.strip())
    return path


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestGlobRegexEquivalence:
    """Property 1: Glob-to-regex match-set equivalence.

    Feature: kiro-1-0-migration, Property 1: Glob-to-regex match-set
    equivalence.

    For any legacy ``when.patterns`` glob list, the combined file-path Matcher
    produced by ``patterns_to_matcher`` matches a sampled workspace-relative
    path if and only if at least one glob in the list matches that path
    (equivalence checked against the independent :func:`_ref_glob_match`
    oracle).

    Validates: Requirements 3.1, 3.2
    """

    # Feature: kiro-1-0-migration, Property 1: Glob-to-regex match-set
    # equivalence
    #
    # This property is a documented candidate for a deeper run than the profile
    # baseline (see design.md Testing Strategy): match-set equivalence has a
    # large glob x path input space, so an inline override explores it more
    # broadly than the fast/thorough baselines while each example stays cheap.
    @given(
        patterns=st.lists(st_glob(), min_size=1, max_size=5),
        extra_paths=st.lists(st_path(), max_size=6),
    )
    @settings(max_examples=300)
    @example(
        patterns=["src/**/*.py"],
        extra_paths=["src/main.py", "src/util/deep/module.py", "src/main.txt"],
    )
    @example(
        patterns=["config/*credentials*", ".env*"],
        extra_paths=["config/db_credentials.yaml", ".env.local", "config/x/credentials.txt"],
    )
    def test_matcher_matches_iff_some_glob_matches(
        self, patterns: list[str], extra_paths: list[str]
    ) -> None:
        """The combined matcher matches a path iff at least one glob matches it.

        Args:
            patterns: A non-empty list of translator-accepted globs.
            extra_paths: Fuzzed sampled paths appended to the fixed sample.
        """
        matcher = patterns_to_matcher(patterns)
        compiled = re.compile(matcher)

        sample_paths = list(_SAMPLE_PATHS) + extra_paths
        for path in sample_paths:
            expected = any(_ref_glob_match(glob, path) for glob in patterns)
            actual = compiled.fullmatch(path) is not None
            assert actual == expected, (
                f"match-set mismatch for path {path!r}: matcher matched={actual}, "
                f"any glob matched={expected}; patterns={patterns!r}; "
                f"matcher={matcher!r}"
            )

    def test_vocabulary_equivalence_over_sample_paths(self) -> None:
        """The shipped glob vocabulary preserves match-set equivalence.

        Example-based reinforcement over the exact globs the migration will
        translate: each vocabulary glob individually, and the whole vocabulary
        combined, must match a sample path iff the oracle says a glob matched.
        """
        # Each vocabulary glob individually.
        for glob in _GLOB_VOCABULARY:
            compiled = re.compile(patterns_to_matcher([glob]))
            for path in _SAMPLE_PATHS:
                expected = _ref_glob_match(glob, path)
                actual = compiled.fullmatch(path) is not None
                assert actual == expected, (glob, path, expected, actual)

        # The whole vocabulary combined (the union semantics).
        combined = re.compile(patterns_to_matcher(list(_GLOB_VOCABULARY)))
        for path in _SAMPLE_PATHS:
            expected = any(_ref_glob_match(glob, path) for glob in _GLOB_VOCABULARY)
            actual = combined.fullmatch(path) is not None
            assert actual == expected, (path, expected, actual)

    def test_reference_oracle_known_cases(self) -> None:
        """Guard the oracle itself against a hand-computed truth table.

        These cases pin the documented ``*`` vs ``**`` vs ``**/`` vs ``?`` vs
        char-class semantics so a bug in the oracle cannot silently weaken the
        equivalence property above.
        """
        cases: tuple[tuple[str, str, bool], ...] = (
            # '**/' spans zero or more leading segments; '*' stays in one segment.
            ("src/**/*.py", "src/main.py", True),
            ("src/**/*.py", "src/util/deep/module.py", True),
            ("src/**/*.py", "src/main.txt", False),
            ("src/**/*.py", "lib/main.py", False),
            ("src/*.py", "src/main.py", True),
            ("src/*.py", "src/sub/main.py", False),
            ("*.py", "main.py", True),
            ("*.py", "src/main.py", False),
            # substring wildcard within one segment
            ("config/*credentials*", "config/db_credentials.yaml", True),
            ("config/*credentials*", "config/sub/credentials.txt", False),
            # leading-dot literal + prefix wildcard
            (".env*", ".env", True),
            (".env*", ".env.local", True),
            (".env*", "env", False),
            # fixed subtree + extension
            ("data/transformed/*.jsonl", "data/transformed/records.jsonl", True),
            ("data/transformed/*.jsonl", "data/records.jsonl", False),
            # '?' is exactly one non-'/' character
            ("test_?.py", "test_a.py", True),
            ("test_?.py", "test_ab.py", False),
            # character class matches one character
            ("[abc]*.txt", "abc.txt", True),
            ("[abc]*.txt", "d.txt", False),
            # trailing '**' crosses '/', but requires the 'src/' prefix
            ("src/**", "src/a/b", True),
            ("src/**", "src", False),
            # leading '**/' may consume nothing
            ("**/*.java", "src/App.java", True),
            ("**/*.java", "App.java", True),
        )
        for glob, path, expected in cases:
            assert _ref_glob_match(glob, path) is expected, (glob, path, expected)
            # The compiled matcher must agree with the oracle on these too.
            compiled = re.compile(patterns_to_matcher([glob]))
            assert (compiled.fullmatch(path) is not None) is expected, (
                glob, path, expected,
            )
