"""Tests for scripts/scan_brittle_assertions.py.

Unit/example tests covering the scanner's enum shape and its stdlib-only
import contract:

- Enum shape: ``BrittleCategory`` has exactly the four recognized categories
  (Requirement 1.1).
- Stdlib-only: importing the module pulls in no third-party packages
  (Requirement 2.1).

Feature: test-suite-debrittling
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import scan_brittle_assertions  # noqa: E402
from scan_brittle_assertions import BrittleCategory  # noqa: E402


class TestBrittleCategory:
    """Enum-shape checks for ``BrittleCategory`` (Requirement 1.1)."""

    def test_has_exactly_four_members(self) -> None:
        """The enum defines exactly four categories, no more, no fewer."""
        assert len(BrittleCategory) == 4

    def test_member_names_match_taxonomy(self) -> None:
        """The four members are the taxonomy's named categories."""
        expected = {
            "EXACT_COUNT",
            "WHOLE_FILE_SNAPSHOT",
            "SECTION_SNAPSHOT",
            "EXACT_SEQUENCE_SNAPSHOT",
        }
        assert {member.name for member in BrittleCategory} == expected

    def test_member_values_are_distinct(self) -> None:
        """Each category carries a distinct string value."""
        values = [member.value for member in BrittleCategory]
        assert len(set(values)) == len(values)


class TestStdlibOnly:
    """Stdlib-only import contract for the scanner (Requirement 2.1)."""

    def test_import_pulls_in_no_third_party_packages(self) -> None:
        """Importing the scanner brings in only standard-library modules.

        Re-imports the scanner with a cleared ``sys.modules`` snapshot and
        asserts that every top-level module newly introduced by the import is
        part of the Python standard library.
        """
        stdlib_names = set(sys.stdlib_module_names)
        # Anything already imported by the test harness (pytest, hypothesis,
        # etc.) is irrelevant: we only inspect modules the scanner introduces.
        before = set(sys.modules)

        # Force a fresh import of the scanner and its dependency closure.
        scanner_related = {
            name
            for name in sys.modules
            if name == "scan_brittle_assertions" or name.startswith("scan_brittle_assertions.")
        }
        for name in scanner_related:
            del sys.modules[name]
        before -= scanner_related

        import importlib

        importlib.import_module("scan_brittle_assertions")

        after = set(sys.modules)
        newly_imported = after - before

        third_party = {
            name
            for name in newly_imported
            if name and not name.startswith("_") and "." not in name
            if name != "scan_brittle_assertions"
            if name not in stdlib_names
        }
        assert third_party == set(), (
            f"scanner import introduced non-stdlib modules: {sorted(third_party)}"
        )

    def test_module_imports_are_all_stdlib(self) -> None:
        """Every name imported at the top of the scanner is a stdlib module."""
        stdlib_names = set(sys.stdlib_module_names)
        source = Path(scan_brittle_assertions.__file__).read_text(encoding="utf-8")
        import ast

        tree = ast.parse(source)
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    imported_roots.add(node.module.split(".")[0])

        # __future__ is a stdlib pseudo-module; everything else must be stdlib too.
        non_stdlib = {
            name for name in imported_roots if name != "__future__" and name not in stdlib_names
        }
        assert non_stdlib == set(), f"scanner imports non-stdlib modules: {sorted(non_stdlib)}"


# ---------------------------------------------------------------------------
# Property-based tests for classify_assertion (Property 1)
# ---------------------------------------------------------------------------

import ast  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from scan_brittle_assertions import classify_assertion  # noqa: E402

# Tokens that mark a count side as a whole-suite/total test count.
_COUNT_TOKENS = ("passing", "total", "test_count", "baseline")

# SHA-256 helper-call names the classifier recognizes.
_SHA_HELPERS = ("_sha256", "sha256", "_sha256_bytes")


@st.composite
def _st_wrapped(draw: st.DrawFn, expr: str) -> tuple[str, int]:
    """Wrap an assert-expression in source with a random leading offset.

    Args:
        draw: Hypothesis draw callable.
        expr: The expression placed after ``assert``.

    Returns:
        A ``(source, expected_lineno)`` pair where ``expected_lineno`` is the
        1-based line on which the single ``assert`` statement appears.
    """
    lead = draw(st.integers(min_value=0, max_value=5))
    source = ("\n" * lead) + f"assert {expr}\n"
    return source, lead + 1


@st.composite
def _st_count_side(draw: st.DrawFn) -> str:
    """Emit an expression referencing a whole-suite/total test count."""
    token = draw(st.sampled_from(_COUNT_TOKENS))
    name = draw(
        st.sampled_from(
            [
                f"{token}_count",
                f"num_{token}",
                token,
                f"_{token.upper()}_BASELINE",
                f"observed_{token}",
            ]
        )
    )
    form = draw(st.sampled_from(["name", "len", "count"]))
    if form == "name":
        return name
    if form == "len":
        return f"len({name})"
    return f"{name}.count(item)"


@st.composite
def st_exact_count_assertion(draw: st.DrawFn) -> tuple[str, int]:
    """Emit an EXACT_COUNT assertion snippet (int literal == test-count ref)."""
    count_side = draw(_st_count_side())
    literal = str(draw(st.integers(min_value=0, max_value=100000)))
    if draw(st.booleans()):
        expr = f"{count_side} == {literal}"
    else:
        expr = f"{literal} == {count_side}"
    return draw(_st_wrapped(expr))


@st.composite
def _st_sha_computation(draw: st.DrawFn, arg: str) -> str:
    """Emit a SHA-256 computation over ``arg`` the classifier recognizes."""
    if draw(st.booleans()):
        return f"hashlib.sha256({arg}).hexdigest()"
    helper = draw(st.sampled_from(_SHA_HELPERS))
    return f"{helper}({arg})"


@st.composite
def _st_digest_anchor(draw: st.DrawFn) -> str:
    """Emit a hard-coded SHA-256 digest anchor (64-hex literal or constant)."""
    if draw(st.booleans()):
        hex_digest = draw(
            st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)
        )
        return f'"{hex_digest}"'
    return draw(
        st.sampled_from(
            [
                "_HASH_ONBOARDING_FLOW",
                "_HASH_UNAFFECTED",
                "BASELINE_HASH",
                "_DIGEST_LEGAL_NOTICE",
                "EXPECTED_DIGEST",
            ]
        )
    )


@st.composite
def st_whole_file_snapshot_assertion(draw: st.DrawFn) -> tuple[str, int]:
    """Emit a WHOLE_FILE_SNAPSHOT assertion (sha256 of whole file == digest)."""
    arg = draw(
        st.sampled_from(
            [
                "content",
                "data",
                "file_bytes",
                "raw_text",
                "body",
                "payload",
                "full_text",
                "doc_path.read_text(encoding='utf-8')",
                "ONBOARDING_PATH.read_bytes()",
                "_read_file(path)",
                "_read_hook(path)",
            ]
        )
    )
    sha = draw(_st_sha_computation(arg))
    anchor = draw(_st_digest_anchor())
    if draw(st.booleans()):
        expr = f"{sha} == {anchor}"
    else:
        expr = f"{anchor} == {sha}"
    return draw(_st_wrapped(expr))


@st.composite
def st_section_snapshot_assertion(draw: st.DrawFn) -> tuple[str, int]:
    """Emit a SECTION_SNAPSHOT assertion (sha256 of a section == digest)."""
    arg = draw(
        st.sampled_from(
            [
                "section_text",
                "block_content",
                "excerpt",
                "snippet",
                "fragment_body",
                "extracted",
                "content[10:50]",
                "text[start:end]",
                "_extract_section(content)",
                "_snapshot_section_content(content)",
            ]
        )
    )
    sha = draw(_st_sha_computation(arg))
    anchor = draw(_st_digest_anchor())
    if draw(st.booleans()):
        expr = f"{sha} == {anchor}"
    else:
        expr = f"{anchor} == {sha}"
    return draw(_st_wrapped(expr))


@st.composite
def _st_sequence_anchor(draw: st.DrawFn) -> str:
    """Emit a hard-coded ordered-sequence anchor (list literal or constant)."""
    if draw(st.booleans()):
        items = draw(
            st.lists(
                st.sampled_from(['"A"', '"B"', '"C"', '"## Intro"']),
                min_size=0,
                max_size=4,
            )
        )
        return "[" + ", ".join(items) + "]"
    return draw(
        st.sampled_from(["_HEADINGS_MODULE_01", "_SEQUENCE_X", "EXPECTED_HEADINGS"])
    )


@st.composite
def st_exact_sequence_snapshot_assertion(draw: st.DrawFn) -> tuple[str, int]:
    """Emit an EXACT_SEQUENCE_SNAPSHOT assertion (heading list == literal)."""
    arg = draw(st.sampled_from(["content", "text", "doc"]))
    extract = draw(
        st.sampled_from(
            [
                f"_extract_headings({arg})",
                f"_extract_all_h2_headings({arg})",
                f"_extract_h2_headings({arg})",
                f"re.findall(pattern, {arg})",
            ]
        )
    )
    anchor = draw(_st_sequence_anchor())
    if draw(st.booleans()):
        expr = f"{extract} == {anchor}"
    else:
        expr = f"{anchor} == {extract}"
    return draw(_st_wrapped(expr))


def _find_single_assert(source: str) -> tuple[ast.Assert, list[str]]:
    """Parse ``source`` and return its single ``ast.Assert`` node plus lines.

    Args:
        source: Python source containing exactly one ``assert`` statement.

    Returns:
        The ``ast.Assert`` node and the source split into lines.
    """
    tree = ast.parse(source)
    asserts = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    assert len(asserts) == 1, f"expected exactly one assert, got {len(asserts)}"
    return asserts[0], source.splitlines()


class TestClassifyAssertionBrittleCategories:
    """Property 1: brittle assertions classify into their category.

    Validates: Requirements 2.3, 2.4, 2.5, 2.6, 7.2
    """

    # Feature: test-suite-debrittling, Property 1: Brittle assertions classify
    # into their category (EXACT_COUNT half).
    @settings(max_examples=100)
    @given(snippet=st_exact_count_assertion())
    def test_exact_count_classifies(self, snippet: tuple[str, int]) -> None:
        """Every generated exact-count snippet classifies as EXACT_COUNT."""
        source, expected_lineno = snippet
        node, lines = _find_single_assert(source)
        assert node.lineno == expected_lineno
        assert classify_assertion(node, lines) == BrittleCategory.EXACT_COUNT

    # Feature: test-suite-debrittling, Property 1: Brittle assertions classify
    # into their category (WHOLE_FILE_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_whole_file_snapshot_assertion())
    def test_whole_file_snapshot_classifies(self, snippet: tuple[str, int]) -> None:
        """Every generated whole-file snapshot snippet classifies correctly."""
        source, expected_lineno = snippet
        node, lines = _find_single_assert(source)
        assert node.lineno == expected_lineno
        assert classify_assertion(node, lines) == BrittleCategory.WHOLE_FILE_SNAPSHOT

    # Feature: test-suite-debrittling, Property 1: Brittle assertions classify
    # into their category (SECTION_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_section_snapshot_assertion())
    def test_section_snapshot_classifies(self, snippet: tuple[str, int]) -> None:
        """Every generated section snapshot snippet classifies correctly."""
        source, expected_lineno = snippet
        node, lines = _find_single_assert(source)
        assert node.lineno == expected_lineno
        assert classify_assertion(node, lines) == BrittleCategory.SECTION_SNAPSHOT

    # Feature: test-suite-debrittling, Property 1: Brittle assertions classify
    # into their category (EXACT_SEQUENCE_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_exact_sequence_snapshot_assertion())
    def test_exact_sequence_snapshot_classifies(
        self, snippet: tuple[str, int]
    ) -> None:
        """Every generated heading-sequence snippet classifies correctly."""
        source, expected_lineno = snippet
        node, lines = _find_single_assert(source)
        assert node.lineno == expected_lineno
        assert (
            classify_assertion(node, lines) == BrittleCategory.EXACT_SEQUENCE_SNAPSHOT
        )


# ---------------------------------------------------------------------------
# Property-based tests for classify_assertion (Property 2)
# ---------------------------------------------------------------------------

# Arguments whose subtree references test-generated data (Legitimate_Hash_Use).
# Each contains a token matching the scanner's _TEST_DATA_MARKERS, so hashing
# them must NOT be flagged as a snapshot of a tracked source file.
_TEST_DATA_ARGS = (
    "tmp_path.read_bytes()",
    '(tmp_path / "out.txt").read_text()',
    "draw(st.text())",
    "drawn_value",
    "generated_payload",
    "random_bytes",
    "fake_record",
    "buffer.getvalue()",
    "faker_output",
)


@st.composite
def _st_membership_expr(draw: st.DrawFn) -> str:
    """Emit a membership check (``item in container``) — a structural form."""
    return draw(
        st.sampled_from(
            [
                '"## Introduction" in content',
                "marker in headings",
                '"brittle-allow" in line',
                "required_marker in section_text",
                "expected_heading in extracted_headings",
            ]
        )
    )


@st.composite
def _st_threshold_expr(draw: st.DrawFn) -> str:
    """Emit a threshold check (``observed >= FLOOR``) — a structural form.

    Uses a non-``==`` comparison operator, so it can never be a brittle
    count/snapshot/sequence equality shape.
    """
    return draw(
        st.sampled_from(
            [
                "observed >= FLOOR",
                "observed_total >= 4648",
                "len(collected) >= _PASSING_FLOOR",
                "count <= MAX_ALLOWED",
                "len(headings) > 0",
            ]
        )
    )


@st.composite
def _st_ordered_subsequence_expr(draw: st.DrawFn) -> str:
    """Emit an ordered-subsequence check — a structural form.

    Either a boolean helper call or an index-ordering comparison; neither is an
    ``==`` snapshot equality.
    """
    return draw(
        st.sampled_from(
            [
                "_is_ordered_subsequence(required, actual)",
                '_appears_in_order(["A", "B"], headings)',
                'actual.index("A") < actual.index("B")',
                "headings.index(first) < headings.index(second)",
            ]
        )
    )


@st.composite
def _st_computed_vs_computed_expr(draw: st.DrawFn) -> str:
    """Emit an ``==`` of two freshly computed values (no hard-coded literal).

    Neither side is an integer literal, a digest anchor, nor a sequence anchor,
    so the literal-anchored classifier must return ``None``.
    """
    return draw(
        st.sampled_from(
            [
                "_sha256(content) == recomputed_digest",
                "_sha256(left) == _sha256(right)",
                "observed_total == expected_total",
                "len(actual) == len(expected)",
                "first_snapshot == second_snapshot",
                "_extract_headings(content) == _extract_headings(other)",
            ]
        )
    )


@st.composite
def _st_legitimate_hash_expr(draw: st.DrawFn) -> str:
    """Emit a Legitimate_Hash_Use: hashing/extracting test-generated data.

    The anchor side is a hard-coded digest/sequence, but the hashed/extracted
    input derives from a ``tmp_path`` file, a Hypothesis-drawn value, or other
    test-generated data, so the guard must return ``None``.
    """
    arg = draw(st.sampled_from(_TEST_DATA_ARGS))
    if draw(st.booleans()):
        computed = draw(_st_sha_computation(arg))
        literal = draw(_st_digest_anchor())
    else:
        literal = draw(_st_sequence_anchor())
        computed = f"_extract_headings({arg})"
    if draw(st.booleans()):
        return f"{computed} == {literal}"
    return f"{literal} == {computed}"


@st.composite
def st_structural_assertion(draw: st.DrawFn) -> tuple[str, int]:
    """Emit a structural / legitimate-hash assertion that must not be flagged.

    Draws from membership, threshold, ordered-subsequence, computed-vs-computed,
    and Legitimate_Hash_Use forms.

    Args:
        draw: Hypothesis draw callable.

    Returns:
        A ``(source, expected_lineno)`` pair for a single ``assert`` statement.
    """
    expr = draw(
        st.one_of(
            _st_membership_expr(),
            _st_threshold_expr(),
            _st_ordered_subsequence_expr(),
            _st_computed_vs_computed_expr(),
            _st_legitimate_hash_expr(),
        )
    )
    return draw(_st_wrapped(expr))


class TestClassifyAssertionStructural:
    """Property 2: structural assertions and legitimate hash uses are not flagged.

    Validates: Requirements 1.3, 2.9, 7.3
    """

    # Feature: test-suite-debrittling, Property 2: Structural assertions and
    # legitimate hash uses are not flagged.
    @settings(max_examples=100)
    @given(snippet=st_structural_assertion())
    def test_structural_assertions_are_not_flagged(
        self, snippet: tuple[str, int]
    ) -> None:
        """Every generated structural / legitimate-hash snippet classifies None."""
        source, expected_lineno = snippet
        node, lines = _find_single_assert(source)
        assert node.lineno == expected_lineno
        assert classify_assertion(node, lines) is None


# ---------------------------------------------------------------------------
# Property-based tests for the allowlist exemption (Property 3)
# ---------------------------------------------------------------------------

from scan_brittle_assertions import has_allowlist_marker  # noqa: E402


def _annotate_with_marker(source: str) -> str:
    """Append a ``brittle-allow`` inline-comment marker to the assert line.

    The brittle generators emit a single ``assert`` statement on its own line
    terminated by a newline (optionally preceded by blank lines). This appends a
    reviewed-allowlist comment to that assert line without changing the parsed
    AST, so ``classify_assertion`` still sees the same brittle shape while
    ``has_allowlist_marker`` now finds the exemption token.

    Args:
        source: Source containing exactly one single-line ``assert`` statement.

    Returns:
        The same source with ``  # brittle-allow: reviewed`` appended to the
        assert line.
    """
    return source.rstrip("\n") + "  # brittle-allow: reviewed\n"


class TestClassifyAssertionAllowlistExemption:
    """Property 3: an Allowlist_Marker converts a Finding into an exemption.

    A brittle assertion annotated with the ``brittle-allow`` token must remain
    classifiable as its brittle category (it is still brittle) yet be reported
    as an exemption via ``has_allowlist_marker`` returning True, so it is never
    surfaced as a non-allowlisted finding.

    Validates: Requirements 2.7, 7.4
    """

    # Feature: test-suite-debrittling, Property 3: Allowlist marker converts a
    # Finding into an exemption (EXACT_COUNT half).
    @settings(max_examples=100)
    @given(snippet=st_exact_count_assertion())
    def test_exact_count_is_exempted(self, snippet: tuple[str, int]) -> None:
        """An allowlisted exact-count assert stays brittle but is exempted."""
        source, _expected_lineno = snippet
        node, lines = _find_single_assert(_annotate_with_marker(source))
        assert classify_assertion(node, lines) == BrittleCategory.EXACT_COUNT
        assert has_allowlist_marker(node, lines) is True

    # Feature: test-suite-debrittling, Property 3: Allowlist marker converts a
    # Finding into an exemption (WHOLE_FILE_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_whole_file_snapshot_assertion())
    def test_whole_file_snapshot_is_exempted(self, snippet: tuple[str, int]) -> None:
        """An allowlisted whole-file snapshot assert stays brittle but exempted."""
        source, _expected_lineno = snippet
        node, lines = _find_single_assert(_annotate_with_marker(source))
        assert classify_assertion(node, lines) == BrittleCategory.WHOLE_FILE_SNAPSHOT
        assert has_allowlist_marker(node, lines) is True

    # Feature: test-suite-debrittling, Property 3: Allowlist marker converts a
    # Finding into an exemption (SECTION_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_section_snapshot_assertion())
    def test_section_snapshot_is_exempted(self, snippet: tuple[str, int]) -> None:
        """An allowlisted section snapshot assert stays brittle but exempted."""
        source, _expected_lineno = snippet
        node, lines = _find_single_assert(_annotate_with_marker(source))
        assert classify_assertion(node, lines) == BrittleCategory.SECTION_SNAPSHOT
        assert has_allowlist_marker(node, lines) is True

    # Feature: test-suite-debrittling, Property 3: Allowlist marker converts a
    # Finding into an exemption (EXACT_SEQUENCE_SNAPSHOT half).
    @settings(max_examples=100)
    @given(snippet=st_exact_sequence_snapshot_assertion())
    def test_exact_sequence_snapshot_is_exempted(
        self, snippet: tuple[str, int]
    ) -> None:
        """An allowlisted heading-sequence assert stays brittle but exempted."""
        source, _expected_lineno = snippet
        node, lines = _find_single_assert(_annotate_with_marker(source))
        assert (
            classify_assertion(node, lines) == BrittleCategory.EXACT_SEQUENCE_SNAPSHOT
        )
        assert has_allowlist_marker(node, lines) is True


# ---------------------------------------------------------------------------
# Property 4: discovery finds exactly the test files (Requirement 2.2).
#
# These tests exercise the I/O driver function ``discover_test_files``, which
# walks the scan roots and returns every ``test_*.py`` file. Because the test
# writes real files, it cannot combine the pytest ``tmp_path`` fixture with
# Hypothesis ``@given`` (function-scoped fixtures are re-used across examples);
# instead each generated example materializes its tree inside a fresh
# ``tempfile.TemporaryDirectory()`` opened in the test body.
# ---------------------------------------------------------------------------

import tempfile  # noqa: E402

from scan_brittle_assertions import discover_test_files  # noqa: E402

# Directory segments are lowercase letters only: they never contain a ``.`` so
# a directory can never accidentally match the ``test_*.py`` file pattern, and a
# (dotted) filename can never collide with a (dotless) directory segment.
_DIR_SEGMENT = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=6)
# Words used to build filenames: lowercase letters only (no underscore), so a
# plain ``<word>.py`` file can never begin with ``test_``.
_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)
# Tail of a test filename: ``test_<tail>.py``. May be empty (yields
# ``test_.py``) and may contain digits/underscores but never ``.`` or ``/``.
_TEST_TAIL = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=0, max_size=8
)


@st.composite
def _st_test_filename(draw: st.DrawFn) -> str:
    """Emit a filename that matches the ``test_*.py`` discovery pattern."""
    return f"test_{draw(_TEST_TAIL)}.py"


@st.composite
def _st_non_test_filename(draw: st.DrawFn) -> str:
    """Emit a filename that does NOT match the ``test_*.py`` pattern.

    Covers three non-matching shapes: a plain ``.py`` file whose name does not
    start with ``test_`` (e.g. ``helper.py``, ``conftest.py``), a ``test_``-named
    file with a non-``.py`` extension (e.g. ``test_x.txt``), and an arbitrary
    data file (e.g. ``data.txt``).
    """
    kind = draw(st.sampled_from(("plain_py", "test_other_ext", "data")))
    word = draw(st.one_of(_WORD, st.sampled_from(["helper", "conftest", "data"])))
    if kind == "plain_py":
        # Letters-only word + ".py" can never start with "test_" (no underscore).
        return f"{word}.py"
    if kind == "test_other_ext":
        ext = draw(st.sampled_from((".txt", ".md", ".dat")))
        return f"test_{word}{ext}"
    ext = draw(st.sampled_from((".txt", ".md", ".dat", ".json")))
    return f"{word}{ext}"


@st.composite
def st_test_tree(draw: st.DrawFn) -> list[tuple[tuple[str, ...], bool]]:
    """Generate a directory-tree spec mixing test and non-matching files.

    Each entry is ``(path_parts, is_test)`` where ``path_parts`` is a tuple of
    nested directory segments ending in a filename, and ``is_test`` records
    whether the filename matches ``test_*.py``. Directory segments are dotless
    and filenames are dotted, so directories never match the pattern and never
    collide with a file path.

    Returns:
        A list of ``(path_parts, is_test)`` entries (possibly empty).
    """
    count = draw(st.integers(min_value=0, max_value=8))
    entries: list[tuple[tuple[str, ...], bool]] = []
    for _ in range(count):
        depth = draw(st.integers(min_value=0, max_value=3))
        dirs = tuple(draw(_DIR_SEGMENT) for _ in range(depth))
        is_test = draw(st.booleans())
        name = draw(_st_test_filename()) if is_test else draw(_st_non_test_filename())
        entries.append((dirs + (name,), is_test))
    return entries


class TestDiscoverTestFiles:
    """Property 4: discovery finds exactly the test files.

    Validates: Requirements 2.2
    """

    # Feature: test-suite-debrittling, Property 4: Discovery finds exactly the
    # test files.
    @settings(max_examples=50)
    @given(tree=st_test_tree())
    def test_discovery_returns_exactly_test_files(
        self, tree: list[tuple[tuple[str, ...], bool]]
    ) -> None:
        """``discover_test_files`` returns exactly the materialized ``test_*.py``.

        Materializes the generated tree under a fresh temp directory, then
        asserts the discovered set equals exactly the set of ``test_*.py`` files
        written and nothing else (no non-matching files, no directories).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expected: set[Path] = set()
            for parts, is_test in tree:
                target = root.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# generated\n", encoding="utf-8")
                if is_test:
                    expected.add(target)

            discovered = set(discover_test_files([root]))

            assert discovered == expected


# ---------------------------------------------------------------------------
# Property 6: summary counts match the scan result (Requirement 3.4).
#
# These tests exercise ``format_summary``, which renders the files-scanned
# count, the per-category finding counts, and the allowlisted-exemption count.
# ``ScanResult`` objects are built directly from Hypothesis-generated data so
# the property is verified independently of the filesystem / AST layers.
# ---------------------------------------------------------------------------

from scan_brittle_assertions import Finding, ScanResult, format_summary  # noqa: E402

# A file-path segment used to synthesize plausible (but unused) finding paths.
_PATH_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)


@st.composite
def st_finding(draw: st.DrawFn, *, allowlisted: bool) -> Finding:
    """Generate a ``Finding`` with a random category, line, and path.

    Args:
        draw: Hypothesis draw callable.
        allowlisted: The ``allowlisted`` flag to stamp on the finding so the
            caller controls whether it lands in ``findings`` or ``exemptions``.

    Returns:
        A ``Finding`` with random but valid field values.
    """
    category = draw(st.sampled_from(list(BrittleCategory)))
    line_number = draw(st.integers(min_value=1, max_value=10_000))
    word = draw(_PATH_WORD)
    file_path = f"tests/test_{word}.py"
    return Finding(
        file_path=file_path,
        line_number=line_number,
        category=category,
        allowlisted=allowlisted,
    )


@st.composite
def st_scan_result(draw: st.DrawFn) -> ScanResult:
    """Generate a ``ScanResult`` with random files, findings, and exemptions.

    Builds a random files-scanned count, a random list of non-allowlisted
    ``Finding`` objects, a random list of allowlisted exemption ``Finding``
    objects, and a random list of parse errors.

    Returns:
        A populated ``ScanResult``.
    """
    files_scanned = draw(st.integers(min_value=0, max_value=5_000))
    findings = draw(st.lists(st_finding(allowlisted=False), max_size=12))
    exemptions = draw(st.lists(st_finding(allowlisted=True), max_size=12))
    parse_errors = draw(
        st.lists(
            st.tuples(
                st.text(alphabet="abcdefghijklmnopqrstuvwxyz/_.", min_size=1, max_size=20),
                st.text(min_size=0, max_size=30),
            ),
            max_size=4,
        )
    )
    return ScanResult(
        files_scanned=files_scanned,
        findings=findings,
        exemptions=exemptions,
        parse_errors=parse_errors,
    )


def _parse_summary(summary: str) -> tuple[int, dict[str, int], int]:
    """Parse a ``format_summary`` rendering back into structured counts.

    Args:
        summary: The multi-line string produced by ``format_summary``.

    Returns:
        A ``(files_scanned, per_category, exemptions)`` tuple where
        ``per_category`` maps each ``BrittleCategory.value`` to its rendered
        count.
    """
    files_scanned = -1
    exemptions = -1
    per_category: dict[str, int] = {}
    category_values = {category.value for category in BrittleCategory}
    for raw_line in summary.splitlines():
        line = raw_line.strip()
        if line.startswith("Files scanned:"):
            files_scanned = int(line.split(":", 1)[1])
        elif line.startswith("Allowlisted exemptions:"):
            exemptions = int(line.split(":", 1)[1])
        elif ":" in line:
            key, _, value = line.partition(":")
            if key.strip() in category_values:
                per_category[key.strip()] = int(value)
    return files_scanned, per_category, exemptions


class TestFormatSummaryCounts:
    """Property 6: summary counts match the scan result.

    Validates: Requirements 3.4
    """

    # Feature: test-suite-debrittling, Property 6: Summary counts match the
    # scan result.
    @settings(max_examples=100)
    @given(result=st_scan_result())
    def test_summary_counts_match_scan_result(self, result: ScanResult) -> None:
        """The rendered summary's counts equal the corresponding ScanResult values.

        Asserts that the files-scanned count, each per-category finding count,
        and the exemption count parsed back out of the rendered summary equal
        the values computed on the ``ScanResult``.
        """
        summary = format_summary(result)
        files_scanned, per_category, exemptions = _parse_summary(summary)

        assert files_scanned == result.files_scanned
        assert exemptions == len(result.exemptions)

        expected_by_category = result.findings_by_category
        for category in BrittleCategory:
            assert per_category[category.value] == expected_by_category[category]


# ---------------------------------------------------------------------------
# Property 5: --check exit code reflects non-allowlisted findings
# (Requirements 3.2, 3.3).
#
# These tests drive the CLI ``main(["--check", "--root", ...])`` end to end over
# generated fixtures. Each fixture is a temp directory of ``test_*.py`` files
# whose contents are assembled by REUSING the brittle/structural snippet
# generators above (``st_exact_count_assertion`` and friends,
# ``st_structural_assertion``) and the ``_annotate_with_marker`` allowlist
# helper. Because the fixtures write real files, the test cannot combine the
# pytest ``tmp_path`` fixture with Hypothesis ``@given``; instead each example
# materializes its tree inside a fresh ``tempfile.TemporaryDirectory()`` opened
# in the test body. Fixtures only ever contain parseable Python (every snippet
# parses), so a non-zero exit is driven solely by non-allowlisted findings, not
# by parse errors.
# ---------------------------------------------------------------------------

from scan_brittle_assertions import main  # noqa: E402


@st.composite
def _st_brittle_source(draw: st.DrawFn) -> str:
    """Emit a single-line brittle assertion (source only, any of the four categories).

    Reuses the existing per-category brittle generators; the line number is
    discarded since the fixture only needs the source text.

    Returns:
        Python source containing exactly one brittle ``assert`` statement.
    """
    source, _lineno = draw(
        st.one_of(
            st_exact_count_assertion(),
            st_whole_file_snapshot_assertion(),
            st_section_snapshot_assertion(),
            st_exact_sequence_snapshot_assertion(),
        )
    )
    return source


@st.composite
def _st_assertion_item(draw: st.DrawFn) -> tuple[str, bool]:
    """Emit one assertion snippet plus whether it is a non-allowlisted finding.

    Three kinds are drawn with equal weight:

    - ``clean`` — a structural assertion (``st_structural_assertion``); the
      scanner returns ``None``, so it is never a finding.
    - ``allowlisted`` — a brittle assertion annotated with ``brittle-allow`` via
      ``_annotate_with_marker``; the scanner counts it as an exemption, never a
      non-allowlisted finding.
    - ``brittle`` — a bare brittle assertion; the scanner reports it as a
      non-allowlisted finding.

    Returns:
        A ``(source, is_nonallowlisted_finding)`` pair.
    """
    kind = draw(st.sampled_from(("clean", "allowlisted", "brittle")))
    if kind == "clean":
        source, _lineno = draw(st_structural_assertion())
        return source, False
    brittle = draw(_st_brittle_source())
    if kind == "allowlisted":
        return _annotate_with_marker(brittle), False
    return brittle, True


@st.composite
def st_check_fixture(draw: st.DrawFn) -> tuple[list[tuple[str, str]], bool]:
    """Generate a fixture of ``test_*.py`` files plus the expected finding flag.

    Builds 0-4 ``test_<i>.py`` files, each concatenating 0-4 assertion items
    drawn from :func:`_st_assertion_item`. Every snippet is a self-contained,
    parseable single-line ``assert``, so concatenating them yields valid Python
    (a sequence of module-level ``assert`` statements) with no parse errors. The
    expected ``has_finding`` flag is True iff at least one item across all files
    is a non-allowlisted brittle assertion.

    Returns:
        A ``(files, has_finding)`` pair where ``files`` is a list of
        ``(filename, content)`` and ``has_finding`` records whether the fixture
        contains at least one non-allowlisted finding.
    """
    n_files = draw(st.integers(min_value=0, max_value=4))
    files: list[tuple[str, str]] = []
    has_finding = False
    for index in range(n_files):
        items = draw(st.lists(_st_assertion_item(), min_size=0, max_size=4))
        parts: list[str] = []
        for source, is_finding in items:
            parts.append(source)
            has_finding = has_finding or is_finding
        content = "".join(parts)
        if not content.strip():
            # Keep empty modules parseable and finding-free.
            content = "# empty test module\n"
        files.append((f"test_{index}.py", content))
    return files, has_finding


class TestCheckExitCode:
    """Property 5: ``--check`` exit code reflects non-allowlisted findings.

    Validates: Requirements 3.2, 3.3
    """

    # Feature: test-suite-debrittling, Property 5: --check exit code reflects
    # non-allowlisted findings.
    @settings(max_examples=50)
    @given(fixture=st_check_fixture())
    def test_check_exit_code_reflects_nonallowlisted_findings(
        self, fixture: tuple[list[tuple[str, str]], bool]
    ) -> None:
        """``main(["--check", ...])`` exits non-zero iff a non-allowlisted finding exists.

        Materializes the generated ``test_*.py`` files under a fresh temp
        directory, runs the CLI with ``--check`` scoped to that directory via
        ``--root``, and asserts the exit code is non-zero exactly when the
        fixture contains at least one non-allowlisted brittle assertion. Clean
        and fully-allowlisted fixtures (zero non-allowlisted findings) exit 0.
        """
        files, has_finding = fixture
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for name, content in files:
                (root / name).write_text(content, encoding="utf-8")

            exit_code = main(["--check", "--root", str(root)])

            if has_finding:
                assert exit_code != 0
            else:
                assert exit_code == 0


# ---------------------------------------------------------------------------
# Task 4.3: CLI entry point and parse-error unit tests
#   - main([]) / main(["--check"]) return integer exit codes (Requirement 3.1).
#   - An invalid-Python fixture is reported as a parse error and forces a
#     non-zero exit regardless of --check (Requirements 2.8, 3.7).
# ---------------------------------------------------------------------------

from scan_brittle_assertions import scan_file  # noqa: E402

# A small, syntactically valid test file with no brittle assertions. Scanning a
# directory holding only this file yields zero findings and zero parse errors.
_CLEAN_TEST_FILE = '''\
"""A clean fixture test module with no brittle assertions."""


def test_clean() -> None:
    """A structural membership check that is never flagged."""
    headings = ["Intro", "Setup", "Usage"]
    assert "Setup" in headings
'''

# A file whose contents are not valid Python (unterminated def / dangling colon),
# used to exercise the scanner's parse-error path.
_INVALID_PYTHON_FILE = '''\
def broken(:
    this is not valid python @@@
    assert ==
'''


class TestCliEntryPoint:
    """``main`` returns integer exit codes for the basic invocations (Req 3.1)."""

    def test_main_default_returns_int_zero_on_clean_root(self) -> None:
        """``main(["--root", clean])`` returns the integer ``0`` for a clean tree.

        Points the scan at an isolated temp directory containing only a clean
        fixture so the result is deterministic and independent of the real
        suite, then asserts the return value is an ``int`` equal to ``0``.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test_clean.py").write_text(_CLEAN_TEST_FILE, encoding="utf-8")

            exit_code = main(["--root", str(root)])

            assert isinstance(exit_code, int)
            assert exit_code == 0

    def test_main_check_returns_int_zero_on_clean_root(self) -> None:
        """``main(["--check", "--root", clean])`` returns the integer ``0``.

        A clean tree has zero non-allowlisted findings, so ``--check`` exits 0.
        Asserts the return value is an ``int``.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test_clean.py").write_text(_CLEAN_TEST_FILE, encoding="utf-8")

            exit_code = main(["--check", "--root", str(root)])

            assert isinstance(exit_code, int)
            assert exit_code == 0

    def test_main_returns_int_on_empty_root(self) -> None:
        """Both ``main([...])`` invocations return ints for an empty scan root.

        An empty directory yields no test files, no findings, and no parse
        errors, so both the default and ``--check`` invocations return the
        integer ``0``.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            default_code = main(["--root", str(root)])
            check_code = main(["--check", "--root", str(root)])

            assert isinstance(default_code, int)
            assert isinstance(check_code, int)
            assert default_code == 0
            assert check_code == 0


class TestParseErrorHandling:
    """Invalid Python forces a reported parse error and non-zero exit (Req 2.8, 3.7)."""

    def test_scan_file_reports_parse_error_message(self) -> None:
        """``scan_file`` on invalid Python returns ``([], <non-None message>)``.

        Writes a syntactically invalid module to a temp directory and asserts the
        scanner surfaces no findings and a non-empty parse-error message rather
        than raising.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "test_bad.py"
            bad_path.write_text(_INVALID_PYTHON_FILE, encoding="utf-8")

            findings, message = scan_file(bad_path)

            assert findings == []
            assert message is not None
            assert message != ""

    def test_main_exits_nonzero_on_parse_error_without_check(self) -> None:
        """``main(["--root", bad])`` exits non-zero even without ``--check``.

        A parse error means the scan is incomplete, so the run must fail
        regardless of ``--check``.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test_bad.py").write_text(_INVALID_PYTHON_FILE, encoding="utf-8")

            exit_code = main(["--root", str(root)])

            assert isinstance(exit_code, int)
            assert exit_code != 0

    def test_main_exits_nonzero_on_parse_error_with_check(self) -> None:
        """``main(["--check", "--root", bad])`` also exits non-zero on a parse error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test_bad.py").write_text(_INVALID_PYTHON_FILE, encoding="utf-8")

            exit_code = main(["--check", "--root", str(root)])

            assert isinstance(exit_code, int)
            assert exit_code != 0

    def test_main_reports_parse_error_to_stderr(self, capsys) -> None:
        """The offending file path is reported to stderr on a parse error.

        Confirms the parse error is surfaced to the user (Requirement 2.8) by
        capturing stderr and asserting it names the bad fixture file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "test_bad.py").write_text(_INVALID_PYTHON_FILE, encoding="utf-8")

            exit_code = main(["--root", str(root)])

            captured = capsys.readouterr()
            assert exit_code != 0
            assert "test_bad.py" in captured.err
