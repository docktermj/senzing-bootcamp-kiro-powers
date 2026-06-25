"""Tests for normalize_markdown.py (graduation Markdown normalization).

Feature: graduation-markdown-normalization

This is the shared test module for the normalizer. It is organized into
class-based test groups, one per correctness property / behavior. Additional
classes (recap conformance, content preservation, non-blocking pass, etc.) are
added by later tasks in the same plan.

Scripts are imported via the project's sys.path pattern (scripts are not a
package).
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts are not a package).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import normalize_markdown

# ---------------------------------------------------------------------------
# Hypothesis strategies for free-form Markdown
# ---------------------------------------------------------------------------


def st_inline_text() -> st.SearchStrategy[str]:
    """Generate short single-line inline text (no newlines, non-empty)."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\n\r`",
        ),
        min_size=1,
        max_size=40,
    ).map(lambda s: s.strip() or "x")


def st_heading() -> st.SearchStrategy[str]:
    """Generate an ATX heading block of a random level (1-6)."""
    return st.builds(
        lambda level, text: f"{'#' * level} {text}",
        st.integers(min_value=1, max_value=6),
        st_inline_text(),
    )


def st_paragraph() -> st.SearchStrategy[str]:
    """Generate a prose paragraph of one or more lines."""
    return st.lists(st_inline_text(), min_size=1, max_size=3).map("\n".join)


def st_bullet_list() -> st.SearchStrategy[str]:
    """Generate an unordered bullet list."""
    return st.lists(st_inline_text(), min_size=1, max_size=4).map(
        lambda items: "\n".join(f"- {item}" for item in items)
    )


def st_numbered_list() -> st.SearchStrategy[str]:
    """Generate an ordered numbered list."""
    return st.lists(st_inline_text(), min_size=1, max_size=4).map(
        lambda items: "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    )


def st_fenced_code() -> st.SearchStrategy[str]:
    """Generate a fenced code block, with or without a language info string."""
    body = st.lists(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
                blacklist_characters="\n\r`",
            ),
            max_size=30,
        ),
        min_size=0,
        max_size=3,
    ).map("\n".join)
    lang = st.sampled_from(["", "python", "text", "bash", "json"])
    return st.builds(
        lambda info, lines: f"```{info}\n{lines}\n```" if lines else f"```{info}\n```",
        lang,
        body,
    )


def st_bold_label() -> st.SearchStrategy[str]:
    """Generate a bold-label line in either colon-inside or colon-outside form."""
    return st.builds(
        lambda label, value, outside: (
            f"**{label}**: {value}" if outside else f"**{label}:** {value}"
        ),
        st_inline_text(),
        st_inline_text(),
        st.booleans(),
    )


def st_markdown_block() -> st.SearchStrategy[str]:
    """Generate a single free-form Markdown block of a random kind."""
    return st.one_of(
        st_heading(),
        st_paragraph(),
        st_bullet_list(),
        st_numbered_list(),
        st_fenced_code(),
        st_bold_label(),
    )


def _join_blocks(blocks: list[str], gaps: list[int]) -> str:
    """Join blocks with the given number of blank lines between each pair."""
    parts: list[str] = []
    for i, block in enumerate(blocks):
        parts.append(block)
        if i < len(gaps):
            parts.append("\n" * gaps[i])
    return "\n".join(parts)


def st_markdown_document() -> st.SearchStrategy[str]:
    """Generate a varied free-form Markdown document.

    Blocks are joined with a varying number of blank lines so the input
    exercises both under- and over-spaced layouts that the CommonMark fixer
    must normalize.
    """
    return st.lists(st_markdown_block(), min_size=1, max_size=6).flatmap(
        lambda blocks: st.lists(
            st.integers(min_value=0, max_value=2),
            min_size=max(len(blocks) - 1, 0),
            max_size=max(len(blocks) - 1, 0),
        ).map(lambda gaps: _join_blocks(blocks, gaps))
    )


# ---------------------------------------------------------------------------
# Property 2: Idempotence / stability
# ---------------------------------------------------------------------------


class TestCommonmarkIdempotence:
    """Property 2: Idempotence / stability of apply_commonmark_fixes.

    Applying the deterministic CommonMark style fixes a second time must be a
    no-op: the output of one pass is a fixed point.

    **Validates: Requirements 2.3, 2.4**
    """

    @given(content=st_markdown_document())
    @settings(max_examples=30)
    def test_apply_commonmark_fixes_is_idempotent(self, content: str) -> None:
        """apply_commonmark_fixes(apply_commonmark_fixes(x)) == apply_commonmark_fixes(x)."""
        once = normalize_markdown.apply_commonmark_fixes(content)
        twice = normalize_markdown.apply_commonmark_fixes(once)
        assert twice == once

    @given(content=st.text(max_size=200))
    @settings(max_examples=30)
    def test_idempotent_on_arbitrary_text(self, content: str) -> None:
        """Idempotence holds for arbitrary text, not just structured Markdown."""
        once = normalize_markdown.apply_commonmark_fixes(content)
        twice = normalize_markdown.apply_commonmark_fixes(once)
        assert twice == once


# The recap schema round-trip is verified against the real PDF parser. Scripts
# are already importable via the sys.path insertion at the top of this module.
import generate_recap_pdf  # noqa: E402

# ---------------------------------------------------------------------------
# Recap schema normalization (Consumer_Schema: docs/bootcamp_recap.md)
# ---------------------------------------------------------------------------


class TestRecapConformance:
    """Unit tests for ``normalize_recap`` recap schema conformance.

    Verifies that a free-form recap is rewritten into Markdown that the recap
    PDF parser (``generate_recap_pdf.parse_recap_markdown``) parses into the
    expected sections, and that content the parser cannot place is retained in
    the output and reported as a warning rather than dropped.

    **Validates: Requirements 8.1, 3.2, 3.4**
    """

    def test_recap_is_registered_in_schema_normalizers(self) -> None:
        """The recap is wired into the Consumer_Schema registry."""
        assert "docs/bootcamp_recap.md" in normalize_markdown.SCHEMA_NORMALIZERS
        assert (
            normalize_markdown.SCHEMA_NORMALIZERS["docs/bootcamp_recap.md"]
            is normalize_markdown.normalize_recap
        )

    def test_free_form_recap_conforms_to_schema(self) -> None:
        """A free-form recap normalizes to schema-conforming Markdown.

        The input uses an irregular, compressed layout (no blank lines between
        blocks) but a parseable module heading. After ``normalize_recap`` the
        output must parse back into the expected single module section with the
        module name and all list contents preserved, and emit no warnings
        because every line maps cleanly into the schema.
        """
        free_form = (
            "# Senzing Bootcamp Recap\n"
            "**Bootcamper:** Alice\n"
            "**Started:** 2024-01-10\n"
            "**Total Duration:** 5 hours\n"
            "## Module 1: Business Problem \u2014 2024-01-10 09:00\n"
            "### Information Shared\n"
            "- Learned about entity resolution\n"
            "- Discussed data sources\n"
            "### Questions Asked\n"
            "1. What is a data source?\n"
            "### Answers Given\n"
            "1. A labeled input record set\n"
            "### Actions Taken\n"
            "- Ran the demo\n"
            "### Duration\n"
            "1 hour\n"
        )

        normalized, warnings = normalize_markdown.normalize_recap(free_form)

        # Fully mappable content => no warnings and no unmapped section.
        assert warnings == []
        assert "## Unmapped Content" not in normalized

        # Output is schema-conforming: the canonical title is restored.
        assert normalized.startswith("# Senzing Bootcamp Recap")

        # The recap PDF parser parses the normalized output into the expected
        # section with the module name and contents preserved.
        doc = generate_recap_pdf.parse_recap_markdown(normalized)
        assert doc.header.bootcamper == "Alice"
        assert len(doc.sections) == 1
        section = doc.sections[0]
        assert section.module_number == 1
        assert section.module_name == "Business Problem"
        assert section.information_shared == [
            "Learned about entity resolution",
            "Discussed data sources",
        ]
        assert section.questions_asked == ["What is a data source?"]
        assert section.answers_given == ["A labeled input record set"]
        assert section.actions_taken == ["Ran the demo"]
        assert section.duration == "1 hour"

    def test_unmappable_content_warns_and_is_retained(self) -> None:
        """Content the parser cannot place produces a warning and is retained.

        Free-form prose, an unrecognized ``### Notes`` subsection, and a fenced
        code block have no home in the recap schema. They must survive in the
        normalized output (under ``## Unmapped Content``) and the normalizer
        must report a non-empty warning so the mismatch is visible.
        """
        free_form = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Bob\n"
            "**Started:** 2024-02-01\n"
            "**Total Duration:** 3 hours\n"
            "\n"
            "This is free-form prose that belongs to no schema section.\n"
            "\n"
            "```python\n"
            'print("hello bootcamp")\n'
            "```\n"
            "\n"
            "## Module 2: Data Loading \u2014 2024-02-01 11:00\n"
            "\n"
            "### Information Shared\n"
            "- Loaded sample data\n"
            "\n"
            "### Notes\n"
            "Some extra notes the schema does not recognize.\n"
            "\n"
            "### Duration\n"
            "30 minutes\n"
        )

        normalized, warnings = normalize_markdown.normalize_recap(free_form)

        # A mismatch must be visible as a non-empty warning (Requirement 3.4).
        assert warnings
        assert any("could not be mapped" in w for w in warnings)

        # Unmapped content is retained verbatim, never dropped (Requirement 3.2).
        assert "## Unmapped Content" in normalized
        assert "This is free-form prose that belongs to no schema section." in normalized
        assert "### Notes" in normalized
        assert "Some extra notes the schema does not recognize." in normalized
        assert 'print("hello bootcamp")' in normalized

        # The recognized section still round-trips correctly alongside the
        # retained content.
        doc = generate_recap_pdf.parse_recap_markdown(normalized)
        assert doc.header.bootcamper == "Bob"
        assert len(doc.sections) >= 1
        module = next(s for s in doc.sections if s.module_number == 2)
        assert module.module_name == "Data Loading"
        assert module.information_shared == ["Loaded sample data"]
        assert module.duration == "30 minutes"


# ---------------------------------------------------------------------------
# Hypothesis strategies for valid RecapDocument values
# ---------------------------------------------------------------------------
#
# These strategies build RecapDocument values whose every field round-trips
# cleanly through the recap PDF generator's schema. The constraints below mirror
# what generate_recap_pdf.parse_recap_markdown actually requires so the property
# is well-defined:
#
#   * Text is single-line, strip-stable, and single-spaced (``" ".join(split())``),
#     so the parser's ``.strip()`` of captured groups is a no-op.
#   * The alphabet excludes characters that would change the parse: ``*`` (would
#     forge a ``**Label:**`` header line), ``#`` (would forge a heading), backtick
#     (fenced code), the em-dash ``\u2014`` (the module-heading ``name — timestamp``
#     separator), and newlines.
#
# Empty values are avoided because an empty header/list-item/duration is not
# emitted as a recognizable line by ``format_recap_document`` and so cannot be a
# distinguishing field for equivalence.


def st_recap_text(min_size: int = 1, max_size: int = 30) -> st.SearchStrategy[str]:
    """Generate single-line, strip-stable text safe for the recap schema.

    The result has no leading/trailing whitespace, no internal whitespace runs,
    and contains none of the characters that would alter how
    ``parse_recap_markdown`` interprets the surrounding structure.
    """
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters=" .,!?()/:;-",
        ),
        min_size=min_size,
        max_size=max_size,
    ).map(lambda s: " ".join(s.split()) or "x")


def st_recap_list(max_size: int = 4) -> st.SearchStrategy[list[str]]:
    """Generate a list of recap list-item strings (possibly empty)."""
    return st.lists(st_recap_text(), min_size=0, max_size=max_size)


def st_recap_section() -> st.SearchStrategy["generate_recap_pdf.RecapSection"]:
    """Build a valid RecapSection with list contents, Q&A, and a duration."""
    return st.builds(
        generate_recap_pdf.RecapSection,
        module_number=st.integers(min_value=0, max_value=99),
        module_name=st_recap_text(),
        timestamp=st_recap_text(),
        information_shared=st_recap_list(),
        questions_asked=st_recap_list(),
        answers_given=st_recap_list(),
        actions_taken=st_recap_list(),
        duration=st_recap_text(),
    )


def st_recap_header() -> st.SearchStrategy["generate_recap_pdf.RecapHeader"]:
    """Build a valid RecapHeader with non-empty fields."""
    return st.builds(
        generate_recap_pdf.RecapHeader,
        bootcamper=st_recap_text(),
        started=st_recap_text(),
        total_duration=st_recap_text(),
    )


def st_recap_document() -> st.SearchStrategy["generate_recap_pdf.RecapDocument"]:
    """Build a valid RecapDocument: a header plus 1..N module sections."""
    return st.builds(
        generate_recap_pdf.RecapDocument,
        header=st_recap_header(),
        sections=st.lists(st_recap_section(), min_size=1, max_size=4),
    )


def perturb_recap_layout(
    markdown: str,
    *,
    drop_blanks: bool,
    extra_blanks: int,
    pad_headings: bool,
    add_trailing: bool,
) -> str:
    """Perturb a canonical recap into a free-form *layout* variant.

    The perturbations are deliberately scoped to whitespace and heading spacing,
    NOT to heading *content*. ``parse_recap_markdown`` requires the
    ``## Module N: name \u2014 timestamp`` em-dash form to recognize a module, and
    ``normalize_recap`` re-canonicalizes purely by round-tripping through that
    parser. Removing the timestamp would make the module unparseable (and hence
    un-round-trippable), so it is intentionally out of scope here — the property
    exercises that ``normalize_recap`` re-canonicalizes layout noise the parser
    still tolerates (collapsed/added blank lines, extra heading spacing, and
    trailing whitespace), all of which the parser's ``\\s+`` matches and
    ``.strip()`` of captured groups absorb.

    Args:
        markdown: Canonical recap Markdown from ``format_recap_document``.
        drop_blanks: When True, remove every blank line (jam blocks together).
        extra_blanks: Number of extra blank lines to add after each kept blank.
        pad_headings: When True, widen the space after ``##``/``###`` markers.
        add_trailing: When True, append trailing whitespace to content lines.

    Returns:
        A perturbed Markdown string that ``parse_recap_markdown`` still parses
        to the same structured content as the original.
    """
    out: list[str] = []
    for line in markdown.split("\n"):
        if line.strip() == "":
            if drop_blanks:
                continue
            out.append(line)
            out.extend([""] * extra_blanks)
            continue
        new_line = line
        # Pad only module/subsection headings (##, ###...), never the single-#
        # document title, so the title stays byte-identical and recognized.
        if pad_headings and re.match(r"^#{2,}\s", new_line):
            new_line = re.sub(r"^(#{2,})\s+", r"\1   ", new_line)
        if add_trailing:
            new_line = new_line + "   "
        out.append(new_line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Property 3: Recap round-trip conformance
# ---------------------------------------------------------------------------


class TestRecapRoundTrip:
    """Property 3: Recap round-trip conformance.

    For any valid ``RecapDocument``, formatting it to Markdown, perturbing the
    layout into a free-form shape, then running ``normalize_recap`` yields
    Markdown that ``parse_recap_markdown`` parses back into an equivalent
    ``RecapDocument`` — section identity, list contents, Q&A pairing, and
    durations are all preserved.

    The perturbation is scoped to layout/whitespace (see
    ``perturb_recap_layout``): ``parse_recap_markdown`` requires the
    ``— timestamp`` em-dash module-heading form and ``normalize_recap`` re-maps
    only what that parser can read, so removing the timestamp cannot round-trip
    and is intentionally excluded. The property remains meaningful: it proves the
    normalizer re-canonicalizes layout noise (blank-line and heading-spacing
    variations) without losing any structured content.

    **Validates: Requirements 2.3, 5.2**
    """

    @given(
        doc=st_recap_document(),
        drop_blanks=st.booleans(),
        extra_blanks=st.integers(min_value=0, max_value=2),
        pad_headings=st.booleans(),
        add_trailing=st.booleans(),
    )
    @settings(max_examples=30)
    def test_round_trip_preserves_document(
        self,
        doc: "generate_recap_pdf.RecapDocument",
        drop_blanks: bool,
        extra_blanks: int,
        pad_headings: bool,
        add_trailing: bool,
    ) -> None:
        """format -> perturb layout -> normalize_recap -> parse == original doc."""
        formatted = generate_recap_pdf.format_recap_document(doc)
        perturbed = perturb_recap_layout(
            formatted,
            drop_blanks=drop_blanks,
            extra_blanks=extra_blanks,
            pad_headings=pad_headings,
            add_trailing=add_trailing,
        )

        normalized, _warnings = normalize_markdown.normalize_recap(perturbed)
        parsed = generate_recap_pdf.parse_recap_markdown(normalized)

        # Header identity preserved.
        assert parsed.header == doc.header

        # Section count and per-section identity/contents preserved.
        assert len(parsed.sections) == len(doc.sections)
        for got, want in zip(parsed.sections, doc.sections):
            assert got.module_number == want.module_number
            assert got.module_name == want.module_name
            assert got.timestamp == want.timestamp
            # List contents preserved verbatim and in order.
            assert got.information_shared == want.information_shared
            assert got.actions_taken == want.actions_taken
            # Q&A pairing preserved: questions and answers keep their order so
            # the i-th question still aligns with the i-th answer.
            assert got.questions_asked == want.questions_asked
            assert got.answers_given == want.answers_given
            # Durations preserved.
            assert got.duration == want.duration

        # Full structural equivalence (dataclass equality across all fields).
        assert parsed == doc


# ---------------------------------------------------------------------------
# Per-file normalization with atomic write
# ---------------------------------------------------------------------------


class TestNormalizeFileAtomicWrite:
    """Unit tests for ``normalize_file`` content preservation and atomic write.

    Verifies that a file with no registered Consumer_Schema is style-normalized
    only (never schema-rewritten) and keeps all of its substantive content, and
    that a failure during the atomic write leaves the original file
    byte-identical with no leftover temp files.

    **Validates: Requirements 8.1, 3.1, 3.5**
    """

    def test_style_only_file_preserves_all_content(self, tmp_path) -> None:
        """A file with no Consumer_Schema is style-fixed but loses no content.

        ``notes.md`` is not in ``SCHEMA_NORMALIZERS``, so ``schema_applied`` must
        be False. The input has style problems (no blank lines around the
        heading/list/code fence, a missing code language, and a colon-outside
        bold label) that the CommonMark fixer will correct, so ``changed`` is
        True. Every substantive token — heading text, prose, list items, and the
        code body — must survive in the rewritten file.
        """
        notes = tmp_path / "notes.md"
        original = (
            "# My Notes\n"
            "Some prose about entity resolution.\n"
            "- first bullet\n"
            "- second bullet\n"
            "**Label**: a value\n"
            "```\n"
            "code_line_one()\n"
            "code_line_two()\n"
            "```\n"
        )
        notes.write_text(original, encoding="utf-8")

        result = normalize_markdown.normalize_file(str(notes))

        # No registered schema => style-only normalization.
        assert result.schema_applied is False
        assert result.error is None
        # The input had style issues, so the file is rewritten.
        assert result.changed is True

        rewritten = notes.read_text(encoding="utf-8")

        # All substantive content is preserved.
        assert "# My Notes" in rewritten
        assert "Some prose about entity resolution." in rewritten
        assert "- first bullet" in rewritten
        assert "- second bullet" in rewritten
        assert "code_line_one()" in rewritten
        assert "code_line_two()" in rewritten
        # Style fixes were applied: bold-label colon moved inside and the fence
        # got a default language.
        assert "**Label:**" in rewritten
        assert "```text" in rewritten
        # A blank line now separates the heading from the following prose (MD022).
        assert "# My Notes\n\n" in rewritten

    def test_write_failure_leaves_original_byte_identical(
        self, tmp_path, monkeypatch
    ) -> None:
        """A failure during the atomic write must not corrupt the original.

        Monkeypatching ``os.replace`` to raise ``OSError`` simulates a failure
        at the moment the temp file would be swapped over the original. The
        normalizer must catch it (no exception propagates), record the error on
        the result, leave the original file byte-identical, and clean up the
        temp file it created so no debris is left behind.
        """
        notes = tmp_path / "notes.md"
        # Content with style issues so normalize_file decides it WOULD change
        # and therefore attempts the atomic write.
        original = (
            "# Heading\n"
            "prose line\n"
            "- bullet\n"
            "```\n"
            "x = 1\n"
            "```\n"
        )
        notes.write_text(original, encoding="utf-8")
        original_bytes = notes.read_bytes()

        before_entries = set(p.name for p in tmp_path.iterdir())

        def _boom(src, dst):
            raise OSError("simulated replace failure")

        monkeypatch.setattr(normalize_markdown.os, "replace", _boom)

        # Must not raise: the pass is non-blocking by contract.
        result = normalize_markdown.normalize_file(str(notes))

        # The failure is surfaced on the result, not as an exception.
        assert result.error is not None
        assert "OSError" in result.error

        # The original file is byte-identical (never corrupted or truncated).
        assert notes.read_bytes() == original_bytes

        # No leftover temp files remain in the directory.
        after_entries = set(p.name for p in tmp_path.iterdir())
        assert after_entries == before_entries


# ---------------------------------------------------------------------------
# Property 1: Content preservation (no silent loss)
# ---------------------------------------------------------------------------


def _normalize_token(text: str) -> str:
    """Normalize a substantive content fragment for comparison.

    Two known, non-lossy CommonMark transforms must not register as content
    changes:

    * Bold-label colon spacing (``**Label**:`` -> ``**Label:**``) — moving the
      colon inside the emphasis markers is invisible once the ``*`` markers are
      stripped, since both forms reduce to ``Label:``.
    * Surrounding/inner whitespace differences — collapsed to single spaces.

    Args:
        text: A raw content fragment (heading text, list-item text, code body
            line, or prose line).

    Returns:
        The fragment with emphasis ``*`` markers removed and whitespace
        collapsed; the empty string when nothing substantive remains.
    """
    return " ".join(text.replace("*", "").split())


def _content_tokens(markdown: str) -> set[str]:
    """Extract the set of substantive content tokens from Markdown text.

    Collects heading texts (markers stripped), list-item texts (markers
    stripped), fenced-code body lines, and prose lines. Fence *delimiters* and
    their info strings are deliberately excluded so the MD040 default-language
    transform (a bare ```` ``` ```` gaining a ``text`` info string) is not seen
    as added or lost content. Each token is normalized via
    :func:`_normalize_token` so formatting-only churn does not affect the
    comparison — the comparison reflects true content, not layout.

    The exact same extraction is applied to both the input and the normalized
    output, so any fragment that survives normalization byte-for-byte yields an
    identical token on both sides.

    Args:
        markdown: Markdown text to tokenize.

    Returns:
        The set of normalized, non-empty substantive content tokens.
    """
    tokens: set[str] = set()
    in_code = False
    for raw in markdown.split("\n"):
        # Fence delimiter (``` or ~~~): toggle code state, never tokenize it.
        if re.match(r"^\s*(?:`{3,}|~{3,})", raw):
            in_code = not in_code
            continue
        if in_code:
            token = _normalize_token(raw)
            if token:
                tokens.add(token)
            continue
        stripped = raw.strip()
        if not stripped:
            continue
        heading = re.match(r"^#{1,6}\s+(.*)$", stripped)
        if heading:
            token = _normalize_token(heading.group(1))
            if token:
                tokens.add(token)
            continue
        item = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", stripped)
        if item:
            token = _normalize_token(item.group(1))
            if token:
                tokens.add(token)
            continue
        # Prose / bold-label line.
        token = _normalize_token(stripped)
        if token:
            tokens.add(token)
    return tokens


class TestContentPreservation:
    """Property 1: Content preservation (no silent loss).

    For any generated free-form Markdown (headings, prose, bullet/numbered
    lists, and fenced code blocks in any order), the substantive content tokens
    present in the input are a SUBSET of those present in ``normalize_file``'s
    output — i.e. output tokens are a superset of input tokens, so nothing is
    silently dropped. The file under test has no registered Consumer_Schema, so
    ``normalize_file`` applies style-only fixes (no schema rewrite).

    Token extraction (:func:`_content_tokens`) is robust to the known,
    non-lossy CommonMark transforms (MD040 default code language and bold-label
    colon repositioning), so the property reflects genuine content preservation
    rather than formatting churn.

    **Validates: Requirements 3.1, 3.2**
    """

    @given(content=st_markdown_document())
    @settings(max_examples=30)
    def test_normalize_file_preserves_all_content_tokens(
        self, content: str
    ) -> None:
        """normalize_file output retains every input content token (superset)."""
        # A fresh temp directory per generated input (a context manager rather
        # than a function-scoped fixture, which is not reset between examples).
        with tempfile.TemporaryDirectory() as tmpdir:
            doc = Path(tmpdir) / "doc.md"
            doc.write_text(content, encoding="utf-8")

            # A non-recap file => style-only normalization, no schema rewrite.
            result = normalize_markdown.normalize_file(str(doc))
            assert result.schema_applied is False
            assert result.error is None

            output = doc.read_text(encoding="utf-8")

            input_tokens = _content_tokens(content)
            output_tokens = _content_tokens(output)

            missing = input_tokens - output_tokens
            assert not missing, (
                f"normalize_file dropped substantive content: {sorted(missing)}\n"
                f"--- input ---\n{content}\n--- output ---\n{output}"
            )


# ---------------------------------------------------------------------------
# Property 4: Non-blocking pass
# ---------------------------------------------------------------------------

from unittest import mock  # noqa: E402  (grouped with this property's helpers)


def _tmp_debris(directory: Path) -> set[str]:
    """Return the names of any leftover atomic-write temp files in a directory.

    ``_atomic_write`` creates sibling temp files named ``<file>.<random>.tmp``
    and removes them on failure, so after a run no ``.tmp`` debris should remain.

    Args:
        directory: Directory to scan.

    Returns:
        The set of file names ending in ``.tmp`` (empty when clean).
    """
    return {p.name for p in directory.iterdir() if p.name.endswith(".tmp")}


class TestNonBlockingPass:
    """Property 4: Non-blocking pass.

    For any target file set — *including* files that raise during the atomic
    write — ``main`` returns 0 (the pass never fails the graduation flow) and
    every original file is left in a consistent state: either fully replaced
    with its complete normalized output, or byte-identical to the original.
    Normalization never leaves a file partially written, truncated, or
    corrupted, and never leaves temp-file debris behind.

    Failures are injected by patching ``os.replace`` to raise for a generated
    subset of the target files, simulating a crash at the exact moment the temp
    file would be swapped over the original. Because the real atomic-write code
    runs (it writes the temp file, then ``os.replace`` raises), this also
    exercises the temp-file cleanup path.

    **Validates: Requirements 2.5, 3.5**
    """

    @given(
        files=st.lists(
            st.tuples(st_markdown_document(), st.booleans()),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=30)
    def test_main_returns_zero_and_never_corrupts(
        self, files: list[tuple[str, bool]]
    ) -> None:
        """main() == 0 and each file is fully normalized or byte-identical."""
        # A fresh temp directory per example (a context manager, not the
        # function-scoped tmp_path fixture, which Hypothesis does not reset
        # between examples).
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)

            # Materialize each generated document and record its pre-run state.
            paths: list[str] = []
            originals: dict[str, str] = {}
            expected_normalized: dict[str, str] = {}
            failing_targets: set[str] = set()
            for index, (content, should_fail) in enumerate(files):
                doc = tmp_root / f"doc{index}.md"
                doc.write_text(content, encoding="utf-8")
                path = str(doc)
                paths.append(path)
                originals[path] = content
                # None of these names are in SCHEMA_NORMALIZERS, so the expected
                # normalized output is exactly the style-fix result.
                expected_normalized[path] = normalize_markdown.apply_commonmark_fixes(
                    content
                )
                if should_fail:
                    # os.replace is called with the normalized target path as dst.
                    failing_targets.add(str(Path(path)))

            real_replace = normalize_markdown.os.replace

            def _maybe_failing_replace(src, dst):
                if str(dst) in failing_targets:
                    raise OSError("simulated atomic-write replace failure")
                return real_replace(src, dst)

            with mock.patch.object(
                normalize_markdown.os, "replace", side_effect=_maybe_failing_replace
            ):
                # main takes the positional file paths as argv.
                exit_code = normalize_markdown.main(paths)

            # Non-blocking contract: per-file errors never fail the run.
            assert exit_code == 0

            # Every file is in a consistent state: either fully replaced with its
            # complete normalized output, or left byte-identical to the original.
            # Never a partial/truncated/corrupt intermediate.
            for path in paths:
                on_disk = Path(path).read_text(encoding="utf-8")
                assert on_disk in (originals[path], expected_normalized[path]), (
                    "normalize_markdown.main left a file in an inconsistent state\n"
                    f"--- path ---\n{path}\n"
                    f"--- on disk ---\n{on_disk!r}\n"
                    f"--- original ---\n{originals[path]!r}\n"
                    f"--- expected normalized ---\n{expected_normalized[path]!r}"
                )

            # No atomic-write temp files were left behind in the directory.
            assert _tmp_debris(tmp_root) == set()
