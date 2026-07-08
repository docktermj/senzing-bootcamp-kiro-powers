"""Property-based tests for the steering-inclusion re-classification rewrite.

Feature: steering-inclusion-auto-audit

Exercises the pure reference mechanism ``rewrite_inclusion`` from the co-located
``reclassify_steering_model`` helper. This module covers **Property 3**
(re-classification preserves the Markdown body and the ``description``
frontmatter value). Property 4 (assigned standard mode output) and the
error-handling unit tests are added by the sibling tasks.

The generators build steering documents whose frontmatter carries an
``inclusion:`` line plus, optionally, a ``description`` value in every realistic
shape (plain, single/double quoted, literal ``|`` and folded ``>`` block
scalars) and arbitrary extra keys, followed by an arbitrary Markdown body
(unicode, fenced code, trailing whitespace, ``\\n`` or ``\\r\\n`` terminators).
All generated content is synthetic and PII-free.
"""

from __future__ import annotations

import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy, composite

# The reference model is co-located in this tests directory (it is not a shipped
# power script). Make the tests directory importable so a direct import resolves
# regardless of the pytest import mode / invocation cwd.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from reclassify_steering_model import VALID_MODES, rewrite_inclusion  # noqa: E402

# The re-classification output is read back with the project's own frontmatter
# parsers (the budget analyzer's ``parse_inclusion`` and the linter's
# ``parse_frontmatter``) so Property 4 verifies against the exact parsing the
# rest of the tooling applies, not a bespoke reader. Scripts are not packages,
# so their directory is placed on ``sys.path`` per the project convention.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import parse_frontmatter  # noqa: E402
from measure_steering import parse_inclusion  # noqa: E402

# ---------------------------------------------------------------------------
# Structural constants
# ---------------------------------------------------------------------------

# Characters ``str.splitlines`` treats as line boundaries. None of these may
# appear inside a single generated frontmatter line, or the rewrite's per-line
# parsing would see extra lines and the test's own fence-finding would diverge.
_LINE_SEPARATORS = "\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"

# Matches a frontmatter ``description:`` key line (anchored at line start after
# optional indentation), used to count description declarations before/after.
_DESC_RE = re.compile(r"^[ \t]*description:")


@dataclass(frozen=True)
class SteeringDoc:
    """A generated steering document plus the facts a test needs to check it.

    Attributes:
        content: The full document text (frontmatter + body).
        eol: The uniform line terminator used throughout (``\\n`` or ``\\r\\n``).
        has_description: Whether the frontmatter declares a ``description``.
        description_block: When ``has_description`` is true, the exact contiguous
            run of description line(s) (each terminated by ``eol``) that must
            survive the rewrite byte-for-byte; otherwise ``None``.
    """

    content: str
    eol: str
    has_description: bool
    description_block: str | None


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_inline_text(extra_exclude: str = "") -> SearchStrategy[str]:
    """Draw a single-line, unicode-inclusive string with no line boundaries.

    Args:
        extra_exclude: Additional characters to keep out of the string (for
            example a quote character when embedding inside a quoted scalar).

    Returns:
        A Hypothesis strategy producing single-line strings.
    """
    return st.text(
        alphabet=st.characters(
            blacklist_characters=_LINE_SEPARATORS + extra_exclude,
            blacklist_categories=("Cs",),
        ),
        max_size=40,
    )


@composite
def st_inclusion_line(draw) -> str:
    """Draw an ``inclusion:`` frontmatter line with an arbitrary current value.

    The value (including quoting and the empty value) is irrelevant to Property 3
    because the rewrite replaces it; varying it exercises the replacement path.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single ``inclusion:`` frontmatter line without its terminator.
    """
    value = draw(st.sampled_from(["always", "fileMatch", "manual", "auto", ""]))
    quote = draw(st.sampled_from(["", '"', "'"]))
    return f"inclusion: {quote}{value}{quote}"


@composite
def st_description_entry(draw) -> list[str]:
    """Draw the line(s) of a ``description`` frontmatter entry.

    Covers the realistic shapes: plain unquoted, double-quoted, single-quoted,
    literal ``|`` block scalar, and folded ``>`` block scalar (each with one to
    three continuation lines). Block continuation lines exclude ``:`` and ``-``
    so they can never be mistaken for another key or a ``---`` fence.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        The description entry's frontmatter lines (without terminators).
    """
    kind = draw(
        st.sampled_from(["plain", "double", "single", "block_literal", "block_folded"])
    )
    if kind == "plain":
        return [f"description: {draw(st_inline_text())}"]
    if kind == "double":
        return [f'description: "{draw(st_inline_text(extra_exclude=chr(34)))}"']
    if kind == "single":
        return [f"description: '{draw(st_inline_text(extra_exclude=chr(39)))}'"]

    indicator = "|" if kind == "block_literal" else ">"
    count = draw(st.integers(min_value=1, max_value=3))
    continuation = [
        f"  {draw(st_inline_text(extra_exclude=':-'))}" for _ in range(count)
    ]
    return [f"description: {indicator}", *continuation]


@composite
def st_extra_entry(draw) -> list[str]:
    """Draw one arbitrary non-inclusion, non-description ``key: value`` line.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single extra frontmatter line (without its terminator).
    """
    key = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10))
    assume(key not in {"inclusion", "description"})
    return [f"{key}: {draw(st_inline_text())}"]


@composite
def st_glob(draw) -> str:
    """Draw a non-empty single-line glob for ``fileMatch`` rewrites.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty glob pattern with no whitespace or line boundaries.
    """
    return draw(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789*/._-", min_size=1, max_size=15)
    )


@composite
def st_body(draw, eol: str) -> str:
    """Draw an arbitrary Markdown body (unicode, fenced code, trailing space).

    The body is copied byte-for-byte by the rewrite, so its only role is to be
    varied and non-trivial.

    Args:
        draw: The Hypothesis draw callable.
        eol: The line terminator to join the body's lines with.

    Returns:
        A multi-line body string terminated with ``eol`` separators.
    """
    parts: list[str] = ["", draw(st_inline_text()) + draw(st.sampled_from(["", " ", "  ", "\t"]))]
    if draw(st.booleans()):
        parts += ["```python", draw(st_inline_text()), "```"]
    parts.append("   ")
    parts += [""] * draw(st.integers(min_value=0, max_value=2))
    return eol.join(parts)


@composite
def st_steering_doc(draw) -> SteeringDoc:
    """Draw a well-formed steering document for the preservation property.

    The frontmatter always contains exactly one ``inclusion:`` line, optionally a
    ``description`` entry, and zero to three extra keys, placed in an arbitrary
    order. No non-fence frontmatter line can strip to ``---`` or look like an
    ``inclusion``/``fileMatchPattern`` key, so the document parses exactly as the
    test expects.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`SteeringDoc` carrying the document and its expected invariants.
    """
    eol = draw(st.sampled_from(["\n", "\r\n"]))

    inclusion_entry = [draw(st_inclusion_line())]
    has_description = draw(st.booleans())
    description_entry = draw(st_description_entry()) if has_description else None
    extras = draw(st.lists(st_extra_entry(), min_size=0, max_size=3))

    entries: list[list[str]] = [inclusion_entry]
    if description_entry is not None:
        entries.append(description_entry)
    entries.extend(extras)
    entries = draw(st.permutations(entries))

    frontmatter_lines = [line for entry in entries for line in entry]
    body = draw(st_body(eol))
    content = eol.join(["---", *frontmatter_lines, "---", body])

    description_block = None
    if description_entry is not None:
        description_block = "".join(line + eol for line in description_entry)

    return SteeringDoc(
        content=content,
        eol=eol,
        has_description=has_description,
        description_block=description_block,
    )


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _split_document(content: str) -> tuple[list[str], str]:
    """Split *content* into its frontmatter lines and closing-fence-plus-body.

    Mirrors the fence-finding logic of :func:`rewrite_inclusion`: the closing
    fence is the first line after the opening fence whose stripped text is
    ``---``. Uses ``splitlines(keepends=True)`` so the returned body is a
    byte-for-byte slice of *content*.

    Args:
        content: A steering document beginning with a ``---`` fence.

    Returns:
        A ``(frontmatter_lines, closing_and_body)`` pair; ``frontmatter_lines``
        keep their terminators and ``closing_and_body`` is the closing fence line
        plus everything after it.
    """
    lines = content.splitlines(keepends=True)
    close_idx: int | None = None
    for i in range(1, len(lines)):
        text = lines[i]
        for eol in ("\r\n", "\n", "\r"):
            if text.endswith(eol):
                text = text[: -len(eol)]
                break
        if text.strip() == "---":
            close_idx = i
            break
    assert close_idx is not None, "generated document must close its frontmatter"
    return lines[1:close_idx], "".join(lines[close_idx:])


def _description_count(frontmatter_lines: list[str]) -> int:
    """Count ``description:`` declaration lines in *frontmatter_lines*.

    Args:
        frontmatter_lines: Raw frontmatter lines (terminators allowed).

    Returns:
        The number of lines whose start declares a ``description`` key.
    """
    return sum(1 for line in frontmatter_lines if _DESC_RE.match(line))


# ---------------------------------------------------------------------------
# Property 3: Re-classification preserves body and description
# ---------------------------------------------------------------------------


class TestReclassifyPreservesBodyAndDescription:
    """Feature: steering-inclusion-auto-audit, Property 3: Re-classification
    preserves body and description

    For any steering file (description present or absent; quoted or unquoted;
    single- or multi-line) and any valid target mode, rewriting the inclusion
    mode leaves the Markdown body byte-identical and the ``description`` value
    byte-identical; when no ``description`` exists the rewrite neither adds nor
    removes one.

    **Validates: Requirements 3.2, 3.5**
    """

    # Feature: steering-inclusion-auto-audit, Property 3: Re-classification
    # preserves body and description
    @given(
        doc=st_steering_doc(),
        mode=st.sampled_from(sorted(VALID_MODES)),
        pattern=st_glob(),
    )
    def test_body_and_description_preserved(
        self, doc: SteeringDoc, mode: str, pattern: str
    ) -> None:
        """Body stays byte-identical and the description survives unchanged.

        Args:
            doc: The generated steering document and its expected invariants.
            mode: The target standard mode to rewrite to.
            pattern: The glob supplied for ``fileMatch`` rewrites (ignored else).
        """
        # Sanity: the generator produced a document whose description (if any)
        # really is a contiguous run of lines.
        if doc.has_description:
            assert doc.description_block is not None
            assert doc.description_block in doc.content

        rewritten = rewrite_inclusion(doc.content, mode, pattern)

        original_fm, original_body = _split_document(doc.content)
        rewritten_fm, rewritten_body = _split_document(rewritten)

        # Req 3.5: the Markdown body (and closing fence) is byte-identical.
        assert rewritten_body == original_body

        # Req 3.2: the description declaration count is preserved exactly, so an
        # absent description is neither added nor removed.
        assert _description_count(rewritten_fm) == _description_count(original_fm)

        if doc.has_description:
            # Req 3.2: the description value survives byte-for-byte.
            assert doc.description_block in rewritten
        else:
            assert _description_count(rewritten_fm) == 0


class TestReclassifyPreservationExamples:
    """Concrete examples pinning body/description preservation (Property 3).

    **Validates: Requirements 3.2, 3.5**
    """

    def test_multiline_description_block_preserved(self) -> None:
        """A literal block-scalar description survives an auto->manual rewrite."""
        content = (
            "---\n"
            "inclusion: auto\n"
            "description: |\n"
            "  First line of the summary.\n"
            "  Second line with detail.\n"
            "---\n"
            "# Body\n"
            "\n"
            "Prose that must not change.\n"
        )

        rewritten = rewrite_inclusion(content, "manual")

        assert (
            "description: |\n  First line of the summary.\n  Second line with detail.\n"
            in rewritten
        )
        assert rewritten.endswith("# Body\n\nProse that must not change.\n")
        assert "inclusion: auto" not in rewritten

    def test_absent_description_stays_absent(self) -> None:
        """A file with no description gains none when rewritten to fileMatch."""
        content = "---\ninclusion: auto\n---\n# No description here\n"

        rewritten = rewrite_inclusion(content, "fileMatch", "**/*.py")

        rewritten_fm, body = _split_document(rewritten)
        # No description key is added to the frontmatter.
        assert _description_count(rewritten_fm) == 0
        assert 'fileMatchPattern: "**/*.py"' in rewritten
        # The body after the closing fence is preserved verbatim.
        assert body == "---\n# No description here\n"

    def test_quoted_description_and_code_fence_body_preserved(self) -> None:
        """A quoted description and a fenced-code body survive the rewrite."""
        content = (
            "---\n"
            'description: "Keep me: exactly as-is"\n'
            "inclusion: auto\n"
            "---\n"
            "# Title\n"
            "\n"
            "```python\n"
            "x = 1  # trailing comment   \n"
            "```\n"
        )

        rewritten = rewrite_inclusion(content, "always")

        assert 'description: "Keep me: exactly as-is"' in rewritten
        _, body = _split_document(rewritten)
        assert body == (
            "---\n# Title\n\n```python\nx = 1  # trailing comment   \n```\n"
        )


# ---------------------------------------------------------------------------
# Readback helpers (reuse the project's own frontmatter parsers)
# ---------------------------------------------------------------------------


def _read_inclusion(content: str) -> str | None:
    """Read the ``inclusion`` value from *content* via ``measure_steering``.

    Writes the rewritten document to a temporary file and parses it with
    :func:`parse_inclusion` so Property 4 verifies the result against the exact
    parser the budget analyzer and the corpus scan apply to on-disk steering
    files.

    Args:
        content: A rewritten steering document (frontmatter + body).

    Returns:
        The parsed ``inclusion`` value, or ``None`` when absent/malformed.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "steering.md"
        path.write_text(content, encoding="utf-8")
        return parse_inclusion(path)


def _read_file_match_pattern(content: str) -> str | None:
    """Read the ``fileMatchPattern`` glob from *content* via ``lint_steering``.

    Uses :func:`parse_frontmatter` (the linter's frontmatter reader) and strips
    the surrounding quotes the rewrite emits so the bare glob can be compared to
    the decided pattern.

    Args:
        content: A rewritten steering document (frontmatter + body).

    Returns:
        The bare ``fileMatchPattern`` glob, or ``None`` when no such key exists.
    """
    frontmatter, _ = parse_frontmatter(content)
    if not frontmatter or "fileMatchPattern" not in frontmatter:
        return None
    return frontmatter["fileMatchPattern"].strip("\"'")


# ---------------------------------------------------------------------------
# Property 4: Re-classification yields the assigned standard mode
# ---------------------------------------------------------------------------


class TestReclassifyYieldsAssignedMode:
    """Feature: steering-inclusion-auto-audit, Property 4: Re-classification
    yields the assigned standard mode

    For any steering file and any Decision_Record entry, the rewritten
    frontmatter declares an ``inclusion`` value equal to the assigned mode and
    drawn from ``{always, fileMatch, manual}``; when the mode is ``fileMatch`` the
    frontmatter carries a ``fileMatchPattern`` exactly equal to the decided glob
    (and no such key for the other modes); and the result never declares
    ``inclusion: auto``.

    **Validates: Requirements 3.1, 3.3, 3.6**
    """

    # Feature: steering-inclusion-auto-audit, Property 4: Re-classification
    # yields the assigned standard mode
    @given(
        doc=st_steering_doc(),
        mode=st.sampled_from(sorted(VALID_MODES)),
        pattern=st_glob(),
    )
    def test_output_declares_assigned_mode(
        self, doc: SteeringDoc, mode: str, pattern: str
    ) -> None:
        """Rewritten frontmatter declares the assigned mode and never ``auto``.

        Args:
            doc: The generated steering document and its expected invariants.
            mode: The target standard mode drawn from ``VALID_MODES``.
            pattern: The glob supplied for ``fileMatch`` rewrites (ignored else).
        """
        rewritten = rewrite_inclusion(doc.content, mode, pattern)

        parsed_mode = _read_inclusion(rewritten)
        parsed_pattern = _read_file_match_pattern(rewritten)

        # Req 3.1: the output inclusion equals the assigned standard mode.
        assert parsed_mode == mode
        assert parsed_mode in VALID_MODES

        # Req 3.3: fileMatch carries the decided glob; other modes inject none.
        if mode == "fileMatch":
            assert parsed_pattern == pattern
        else:
            assert parsed_pattern is None

        # Req 3.6: no re-classified file declares inclusion: auto.
        assert parsed_mode != "auto"
        frontmatter_lines, _ = _split_document(rewritten)
        assert "inclusion: auto" not in "".join(frontmatter_lines)


# ---------------------------------------------------------------------------
# Error handling: rewrite_inclusion guards a malformed Decision_Record
# ---------------------------------------------------------------------------

# A minimal, well-formed steering document used so that error cases fail only
# on the guarded condition under test (mode / pattern) and never on frontmatter
# parsing. Synthetic and PII-free.
_VALID_DOC = (
    "---\n"
    "inclusion: auto\n"
    "description: Synthetic sample steering file.\n"
    "---\n"
    "# Heading\n"
    "\n"
    "Body prose that stays put.\n"
)


class TestRewriteInclusionErrorHandling:
    """Unit tests for ``rewrite_inclusion`` Decision_Record guards.

    A malformed Decision_Record must never reach the file-writing stage: the
    rewrite raises :class:`ValueError` when the target mode is outside
    ``{always, fileMatch, manual}`` and when ``fileMatch`` is requested without a
    non-empty glob. These are concrete example tests, not property tests.

    **Validates: Requirements 3.1, 3.3**
    """

    @pytest.mark.parametrize(
        "bad_mode",
        [
            "auto",       # the non-standard value this audit removes
            "Always",     # correct spelling, wrong case (comparison is exact)
            "MANUAL",     # upper-cased standard value
            "fileMatchPattern",  # a frontmatter key, not a mode
            "",           # empty string
            "bogus",      # arbitrary junk
        ],
    )
    def test_out_of_set_mode_raises_value_error(self, bad_mode: str) -> None:
        """An out-of-set mode raises ``ValueError`` (Req 3.1).

        Args:
            bad_mode: A mode value outside ``{always, fileMatch, manual}``.
        """
        with pytest.raises(ValueError):
            rewrite_inclusion(_VALID_DOC, bad_mode)

    def test_out_of_set_mode_message_names_the_value(self) -> None:
        """The raised error surfaces the offending mode value (Req 3.1)."""
        with pytest.raises(ValueError, match="bogus"):
            rewrite_inclusion(_VALID_DOC, "bogus")

    @pytest.mark.parametrize(
        "empty_pattern",
        [
            None,      # omitted entirely (the default)
            "",        # empty string
            " ",       # single space
            "   ",     # multiple spaces
            "\t",      # tab
            "\t  \t",  # mixed whitespace
        ],
    )
    def test_filematch_without_pattern_raises_value_error(
        self, empty_pattern: str | None
    ) -> None:
        """``fileMatch`` without a non-empty glob raises ``ValueError`` (Req 3.3).

        Args:
            empty_pattern: A missing or whitespace-only ``file_match_pattern``.
        """
        with pytest.raises(ValueError):
            rewrite_inclusion(_VALID_DOC, "fileMatch", empty_pattern)

    def test_filematch_missing_pattern_uses_default_none(self) -> None:
        """Omitting the pattern argument for ``fileMatch`` raises (Req 3.3)."""
        with pytest.raises(ValueError, match="file_match_pattern"):
            rewrite_inclusion(_VALID_DOC, "fileMatch")

    def test_filematch_with_non_empty_pattern_succeeds(self) -> None:
        """A non-empty glob is accepted, confirming only blanks are rejected."""
        rewritten = rewrite_inclusion(_VALID_DOC, "fileMatch", "**/*.py")

        assert 'fileMatchPattern: "**/*.py"' in rewritten
        assert "inclusion: fileMatch" in rewritten
