"""Property-based and example tests for validate_handoff_summary.py.

Feature: session-handoff

This module is the test scaffolding for the Session_Handoff structural validator.
It supplies the Hypothesis strategies and mutation helpers that the five
structural Correctness Properties (tasks 2.2-2.7) consume, plus a single sanity
check that the base conformant template validates clean.

The linchpin is :func:`st_conformant_summary`: it renders a Handoff_Summary that
``validate_handoff_summary`` reports as ``ok=True``. Every mutation helper takes
a conformant :class:`HandoffDraft`, breaks exactly one invariant, and re-renders
so a downstream property can assert the matching finding is produced.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_handoff_summary import (  # noqa: E402
    BODY_SECTIONS,
    EMOJI,
    EMPTY_SECTION_NOT_NONE,
    FORBIDDEN_PHRASE,
    FORBIDDEN_PHRASES,
    MISSING_SECTION,
    NONE_MARKER,
    RELATIVE_PATH,
    SECTION_OUT_OF_ORDER,
    UNQUOTED_CONTINUATION,
    HandoffFinding,
    HandoffValidation,
    _EMOJI_RANGES,
    main,
    validate_handoff_summary,
)

# The seven level-2 body headings, unpacked for readable helper defaults. These
# come straight from the validator so the em-dash in the "Verification" heading
# is never hand-typed here (a mismatch would silently break the strategies).
(
    _WHERE_IT_STARTED,
    _DECISIONS,
    _KEY_FILES,
    _RUNNING_STATE,
    _VERIFICATION,
    _DEFERRED,
    _PICK_UP_HERE,
) = BODY_SECTIONS

# The fixed Verification body used by the conformant template. The "Verification"
# section is intentionally *not* path-checked by the validator, so the deliberate
# relative command below never trips the absolute-path rule (Req 6.3).
_VERIFICATION_BLOCK = "\n".join(
    (
        "- Re-establish MCP: call get_capabilities - expect a reachable Senzing MCP "
        "server and a capabilities list.",
        "- Run: python3 senzing-bootcamp/scripts/baseline_status.py - expect the "
        "data-source coverage report.",
        "- Confirm the current-module artifacts exist - expect all present.",
    )
)

# Prose alphabet for free-text section content: letters and digits only. It
# excludes '#' (would open a heading), '/' (would look like a path), '"' (would
# open a quoted span), and every emoji code point, so generated prose can never
# accidentally trip a structural check.
_PROSE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Filesystem path-segment alphabet: lowercase letters, digits, and the two safe
# separators. No spaces (tokens split on whitespace) and no "://" (never a URI).
_PATH_SEGMENT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_-"

# File extensions used when synthesizing path-like tokens.
_PATH_EXTENSIONS = ("py", "json", "md", "yaml", "db", "txt")


# ---------------------------------------------------------------------------
# Conformant-summary model
# ---------------------------------------------------------------------------


@dataclass
class HandoffDraft:
    """A structured, mutable draft of a Handoff_Summary.

    Rendering a draft yields Markdown text suitable for
    :func:`validate_handoff_summary`. A freshly drawn draft (via
    :func:`st_handoff_draft`) is conformant; the module-level mutation helpers
    each break one invariant so a property can assert the matching finding.

    Attributes:
        title_subject: The one-line subject placed after ``# Handoff: ``.
        body: The seven ``(heading, content)`` body sections in document order;
            an empty ``content`` renders a section with no body (used to model a
            blanked section).
        module_number: The module number named by the continuation phrase.
    """

    title_subject: str
    body: list[tuple[str, str]]
    module_number: int

    def render(self) -> str:
        """Render the draft to Handoff_Summary Markdown text.

        Returns:
            The full summary: a level-1 Title line followed by each body section
            as a ``## `` heading and its content (omitted when the content is an
            empty string, which models a blanked section).
        """
        lines: list[str] = [f"# Handoff: {self.title_subject}", ""]
        for heading, content in self.body:
            lines.append(f"## {heading}")
            if content:
                lines.append(content)
            lines.append("")
        return "\n".join(lines)


def continuation_phrase(module_number: int) -> str:
    """Return the Continuation_Phrase naming ``module_number`` (unquoted).

    Args:
        module_number: The bootcamp module number to name.

    Returns:
        The resume-phrase stem exactly as the validator's continuation regex
        expects (case-insensitive match on "continue the bootcamp from module").
    """
    return f"continue the bootcamp from module {module_number}"


# ---------------------------------------------------------------------------
# Building-block strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_prose_word() -> st.SearchStrategy[str]:
    """Draw a single alnum prose word (never introduces markup or paths)."""
    return st.text(alphabet=_PROSE_ALPHABET, min_size=1, max_size=10)


@st.composite
def st_prose_line(draw) -> str:
    """Draw one non-empty prose line: space-joined :func:`st_prose_word` words.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single line with no leading/trailing whitespace and no line-opening
        ``#``, so it is never parsed as a heading.
    """
    words = draw(st.lists(st_prose_word(), min_size=1, max_size=8))
    return " ".join(words)


@st.composite
def st_section_body(draw) -> str:
    """Draw non-empty multi-line prose for a free-text section body.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One to three prose lines joined by newlines; always non-whitespace so it
        never trips the empty-section rule.
    """
    lines = draw(st.lists(st_prose_line(), min_size=1, max_size=3))
    return "\n".join(lines)


def st_title_subject() -> st.SearchStrategy[str]:
    """Draw a one-line, non-empty Title subject."""
    return st_prose_line()


@st.composite
def st_absolute_path(draw) -> str:
    """Draw an absolute filesystem path token (starts with ``/``).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A path such as ``/home/bootcamper/senzing/mapper.py`` — always rooted at
        ``/``, space-free, and never a URI, so it passes the absolute-path rule.
    """
    segment = st.text(alphabet=_PATH_SEGMENT_ALPHABET, min_size=1, max_size=10)
    directories = draw(st.lists(segment, min_size=1, max_size=4))
    stem = draw(segment)
    extension = draw(st.sampled_from(_PATH_EXTENSIONS))
    return "/" + "/".join([*directories, f"{stem}.{extension}"])


@st.composite
def st_relative_path(draw) -> str:
    """Draw a relative path token (contains ``/`` but does not start with ``/``).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A path such as ``config/mapping_state.json`` — a genuine path reference
        (contains a separator, is not a URI) that violates the absolute-path
        rule, so injecting it must yield a ``RELATIVE_PATH`` finding.
    """
    segment = st.text(alphabet=_PATH_SEGMENT_ALPHABET, min_size=1, max_size=10)
    segments = draw(st.lists(segment, min_size=2, max_size=4))
    return "/".join(segments)


def st_forbidden_phrase() -> st.SearchStrategy[str]:
    """Draw one of the eight forbidden temporal phrases (verbatim)."""
    return st.sampled_from(FORBIDDEN_PHRASES)


@st.composite
def st_cased_forbidden_phrase(draw) -> str:
    """Draw a forbidden temporal phrase with its letter casing altered.

    Applies one of the case transforms ``str.upper``, ``str.title``, or
    ``str.swapcase`` to a verbatim :data:`FORBIDDEN_PHRASES` entry. Every
    :data:`FORBIDDEN_PHRASES` entry is lowercase, so each transform yields a
    string whose casing genuinely differs from the canonical form. Because the
    validator lowercases before matching (Req 7.4), lowercasing any returned
    value recovers the exact source phrase, so it can be named in assertions.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A forbidden phrase whose casing differs from the canonical lowercase form.
    """
    phrase = draw(st_forbidden_phrase())
    transform = draw(st.sampled_from((str.upper, str.title, str.swapcase)))
    return transform(phrase)


@st.composite
def st_emoji_char(draw) -> str:
    """Draw a single emoji character from the validator's own emoji ranges.

    Reuses :data:`validate_handoff_summary._EMOJI_RANGES` so the strategy stays
    in lockstep with the exact code points the validator flags (Req 9.2).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A one-character string whose code point lies in an emoji range.
    """
    low, high = draw(st.sampled_from(_EMOJI_RANGES))
    codepoint = draw(st.integers(min_value=low, max_value=high))
    return chr(codepoint)


@st.composite
def st_database_entry(draw) -> str:
    """Draw a conformant "Running state" database token.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        Either an absolute SQLite file path or a PostgreSQL connection URI — both
        forms the validator accepts for the database entry (Req 5.4).
    """
    if draw(st.booleans()):
        return draw(st_absolute_path())
    host = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=8))
    database = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=8))
    return f"postgresql://{host}/{database}"


def st_quoted_continuation() -> st.SearchStrategy[str]:
    """Draw a quoted Continuation_Phrase, e.g. ``"continue the bootcamp ...".``"""
    return st.integers(min_value=1, max_value=11).map(
        lambda number: f'"{continuation_phrase(number)}"'
    )


def st_unquoted_continuation() -> st.SearchStrategy[str]:
    """Draw an unquoted Continuation_Phrase (violates the quoted-phrase rule)."""
    return st.integers(min_value=1, max_value=11).map(continuation_phrase)


# ---------------------------------------------------------------------------
# Conformant-summary composite strategies
# ---------------------------------------------------------------------------


def _render_key_files(paths: list[str]) -> str:
    """Render a "Key files" body as an absolute-path bullet list.

    Args:
        paths: Absolute paths to list (the first is treated as the Driving_Artifact).

    Returns:
        A newline-joined Markdown bullet list of the paths.
    """
    return "\n".join(f"- {path}" for path in paths)


def _render_running_state(database_entry: str, mcp_status: str) -> str:
    """Render a conformant "Running state" body.

    Args:
        database_entry: An absolute SQLite path or a PostgreSQL connection URI.
        mcp_status: The MCP connection status word (``connected``/``disconnected``).

    Returns:
        The database, MCP, and processes lines joined by newlines.
    """
    return "\n".join(
        (
            f"- Database: {database_entry}",
            f"- MCP: {mcp_status}",
            "- Processes: none",
        )
    )


def _render_pick_up_here(action: str, module_number: int) -> str:
    """Render a conformant "Pick up here" body with a quoted resume phrase.

    Args:
        action: The single next-action line.
        module_number: The module number named by the quoted continuation phrase.

    Returns:
        The action line followed by the quoted resume phrase line.
    """
    return f'{action}\nResume phrase: "{continuation_phrase(module_number)}"'


def _render_pick_up_here_typographic(action: str, module_number: int) -> str:
    """Render a "Pick up here" body whose resume phrase uses typographic quotes.

    Mirrors :func:`_render_pick_up_here` but encloses the continuation phrase in
    typographic double quotes (U+201C ... U+201D), the second quote form the
    validator accepts (Req 7.2). Used by the positive half of the quoted-
    continuation property to confirm typographic quoting is honored.

    Args:
        action: The single next-action line.
        module_number: The module number named by the quoted continuation phrase.

    Returns:
        The action line followed by the typographically-quoted resume phrase line.
    """
    return f"{action}\nResume phrase: \u201c{continuation_phrase(module_number)}\u201d"


@st.composite
def st_handoff_draft(draw) -> HandoffDraft:
    """Draw a conformant :class:`HandoffDraft`.

    The draft always has the Title plus all seven body sections in canonical
    order, absolute paths in the path-bearing sections, a quoted continuation
    phrase, no emoji, and no forbidden phrases, so ``render()`` yields text that
    :func:`validate_handoff_summary` reports as ``ok``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A conformant draft ready to render or to feed a mutation helper.
    """
    module_number = draw(st.integers(min_value=1, max_value=11))
    key_files = draw(st.lists(st_absolute_path(), min_size=1, max_size=4))
    mcp_status = draw(st.sampled_from(("connected", "disconnected")))

    body: list[tuple[str, str]] = [
        (_WHERE_IT_STARTED, draw(st_section_body())),
        (_DECISIONS, draw(st_section_body())),
        (_KEY_FILES, _render_key_files(key_files)),
        (_RUNNING_STATE, _render_running_state(draw(st_database_entry()), mcp_status)),
        (_VERIFICATION, _VERIFICATION_BLOCK),
        (_DEFERRED, draw(st.one_of(st_section_body(), st.just(NONE_MARKER)))),
        (_PICK_UP_HERE, _render_pick_up_here(draw(st_prose_line()), module_number)),
    ]
    return HandoffDraft(
        title_subject=draw(st_title_subject()),
        body=body,
        module_number=module_number,
    )


def st_conformant_summary() -> st.SearchStrategy[str]:
    """Draw a conformant Handoff_Summary as text (``validate_...`` reports ``ok``).

    This is the linchpin the mutation-based properties build on. The ``filter``
    is a belt-and-suspenders guarantee: :func:`st_handoff_draft` is constructed
    to always be conformant, so the filter rejects effectively nothing.

    Returns:
        A strategy over conformant Handoff_Summary strings.
    """
    return (
        st_handoff_draft()
        .map(lambda draft: draft.render())
        .filter(lambda text: validate_handoff_summary(text).ok)
    )


# ---------------------------------------------------------------------------
# Mutation helpers (break exactly one invariant of a conformant draft)
# ---------------------------------------------------------------------------


def _append_to_section(draft: HandoffDraft, heading: str, extra: str) -> HandoffDraft:
    """Return a copy of ``draft`` with ``extra`` appended to ``heading``'s body.

    Args:
        draft: The draft to copy.
        heading: The body heading whose content receives the appended text.
        extra: The text to append (on its own line when content already exists).

    Returns:
        A new :class:`HandoffDraft` with the section's content extended.
    """
    new_body = [
        (name, (f"{content}\n{extra}" if content else extra) if name == heading else content)
        for name, content in draft.body
    ]
    return replace(draft, body=new_body)


def drop_section(draft: HandoffDraft, heading: str) -> HandoffDraft:
    """Return a copy of ``draft`` with ``heading``'s section removed (MISSING_SECTION)."""
    return replace(draft, body=[entry for entry in draft.body if entry[0] != heading])


def swap_sections(draft: HandoffDraft, first: int, second: int) -> HandoffDraft:
    """Return a copy of ``draft`` with body positions ``first``/``second`` swapped.

    Swapping two sections leaves all headings present but out of canonical order
    (SECTION_OUT_OF_ORDER).

    Args:
        draft: The draft to copy.
        first: The first body index to swap.
        second: The second body index to swap.

    Returns:
        A new :class:`HandoffDraft` with the two sections transposed.
    """
    body = list(draft.body)
    body[first], body[second] = body[second], body[first]
    return replace(draft, body=body)


def blank_section(draft: HandoffDraft, heading: str) -> HandoffDraft:
    """Return a copy of ``draft`` with ``heading``'s body emptied (EMPTY_SECTION_NOT_NONE)."""
    return replace(
        draft,
        body=[(name, "" if name == heading else content) for name, content in draft.body],
    )


def inject_relative_path(
    draft: HandoffDraft, relative_path: str, heading: str = _KEY_FILES
) -> HandoffDraft:
    """Return a copy of ``draft`` with a relative path added to a path section (RELATIVE_PATH)."""
    return _append_to_section(draft, heading, f"- {relative_path}")


def inject_forbidden_phrase(draft: HandoffDraft, phrase: str) -> HandoffDraft:
    """Return a copy of ``draft`` with ``phrase`` added to "Pick up here" (FORBIDDEN_PHRASE)."""
    return _append_to_section(draft, _PICK_UP_HERE, phrase)


def inject_emoji(draft: HandoffDraft, emoji_char: str) -> HandoffDraft:
    """Return a copy of ``draft`` with ``emoji_char`` appended to the Title (EMOJI)."""
    return replace(draft, title_subject=f"{draft.title_subject}{emoji_char}")


def unquote_continuation(draft: HandoffDraft) -> HandoffDraft:
    """Return a copy of ``draft`` with the "Pick up here" quotes stripped.

    Removes the straight and typographic double quotes from the "Pick up here"
    body so the continuation phrase is present but unquoted (UNQUOTED_CONTINUATION).

    Args:
        draft: The draft to copy.

    Returns:
        A new :class:`HandoffDraft` whose resume phrase is no longer quoted.
    """
    new_body: list[tuple[str, str]] = []
    for name, content in draft.body:
        if name == _PICK_UP_HERE:
            unquoted = content.replace('"', "").replace("\u201c", "").replace("\u201d", "")
            new_body.append((name, unquoted))
        else:
            new_body.append((name, content))
    return replace(draft, body=new_body)


# ---------------------------------------------------------------------------
# Shared assertion helpers for the property tests (tasks 2.2-2.7)
# ---------------------------------------------------------------------------


def finding_codes(result: HandoffValidation) -> list[str]:
    """Return the finding codes present in ``result``, in order."""
    return [finding.code for finding in result.findings]


def has_finding(result: HandoffValidation, code: str) -> bool:
    """Return whether ``result`` carries at least one finding with ``code``."""
    return any(finding.code == code for finding in result.findings)


def findings_with_code(result: HandoffValidation, code: str) -> list[HandoffFinding]:
    """Return every finding in ``result`` whose code equals ``code``."""
    return [finding for finding in result.findings if finding.code == code]


# ---------------------------------------------------------------------------
# Section-selection strategies for the structure-stability property (task 2.2)
# ---------------------------------------------------------------------------


def st_body_heading() -> st.SearchStrategy[str]:
    """Draw one of the seven canonical body-section headings to drop or blank."""
    return st.sampled_from(BODY_SECTIONS)


@st.composite
def st_section_index_pair(draw) -> tuple[int, int]:
    """Draw two distinct body-section indices to transpose.

    Swapping two distinct positions in a conformant draft's seven-entry ``body``
    list guarantees at least one heading falls out of canonical order, so the
    rendered summary must yield a ``SECTION_OUT_OF_ORDER`` finding.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(first, second)`` pair of distinct indices into a draft's ``body``,
        suitable for :func:`swap_sections`.
    """
    first, second = draw(
        st.lists(
            st.integers(min_value=0, max_value=len(BODY_SECTIONS) - 1),
            min_size=2,
            max_size=2,
            unique=True,
        )
    )
    return first, second


# ---------------------------------------------------------------------------
# Property-test class scaffold
# ---------------------------------------------------------------------------


class TestHandoffSummaryProperties:
    """Structural property tests over ``validate_handoff_summary``.

    The five structural Correctness Properties (Properties 1-5) are added by
    tasks 2.2-2.7. This scaffold provides the shared strategies/helpers above and
    a single sanity check that the base conformant template validates clean, so
    the mutation-based properties build on a solid, verified base.
    """

    @given(summary=st_conformant_summary())
    def test_conformant_summary_validates_clean(self, summary: str) -> None:
        """Sanity: a freshly drawn conformant summary produces no findings.

        The positive half of the structure-stability property: a summary with all
        eight canonical Sections present, in order, with a single-line non-empty
        Title, validates clean.

        **Validates: Requirements 4.1, 4.2, 4.3, 9.4**
        """
        result = validate_handoff_summary(summary)
        assert result.ok, f"expected a conformant summary, got findings: {result.findings}"

    # -- Property 1: Structure stability (canonical section set + order) ----
    # Feature: session-handoff, Property 1: Structure stability

    @given(draft=st_handoff_draft(), dropped=st_body_heading())
    def test_dropping_a_section_yields_missing_section(
        self, draft: HandoffDraft, dropped: str
    ) -> None:
        """Dropping any canonical body Section produces a MISSING_SECTION finding.

        Metamorphic mutation: from a conformant draft, remove exactly one of the
        seven body Sections and confirm the validator flags that Section as
        absent (and no longer reports ``ok``).

        **Validates: Requirements 4.1**
        """
        result = validate_handoff_summary(drop_section(draft, dropped).render())
        assert not result.ok
        assert has_finding(result, MISSING_SECTION)
        assert any(
            dropped in finding.detail
            for finding in findings_with_code(result, MISSING_SECTION)
        ), f"no MISSING_SECTION finding named the dropped section '{dropped}'"

    @given(draft=st_handoff_draft(), pair=st_section_index_pair())
    def test_swapping_two_sections_yields_out_of_order(
        self, draft: HandoffDraft, pair: tuple[int, int]
    ) -> None:
        """Transposing two Sections produces a SECTION_OUT_OF_ORDER finding.

        Metamorphic mutation: from a conformant draft, swap two distinct body
        positions so every heading is still present but the canonical order is
        broken, and confirm the validator flags the ordering violation.

        **Validates: Requirements 4.1**
        """
        first, second = pair
        result = validate_handoff_summary(swap_sections(draft, first, second).render())
        assert not result.ok
        assert has_finding(result, SECTION_OUT_OF_ORDER)

    @given(draft=st_handoff_draft(), blanked=st_body_heading())
    def test_blanking_a_section_yields_empty_not_none(
        self, draft: HandoffDraft, blanked: str
    ) -> None:
        """Blanking a Section (empty, not "none") yields EMPTY_SECTION_NOT_NONE.

        Metamorphic mutation: from a conformant draft, empty one body Section's
        content without substituting the ``none`` marker and confirm the
        validator flags that Section.

        **Validates: Requirements 4.3, 9.4**
        """
        result = validate_handoff_summary(blank_section(draft, blanked).render())
        assert not result.ok
        assert has_finding(result, EMPTY_SECTION_NOT_NONE)
        assert any(
            blanked in finding.detail
            for finding in findings_with_code(result, EMPTY_SECTION_NOT_NONE)
        ), f"no EMPTY_SECTION_NOT_NONE finding named the blanked section '{blanked}'"

    # -- Property 2: Absolute-path invariant (file references) --------------
    # Feature: session-handoff, Property 2: Absolute-path invariant

    @given(draft=st_handoff_draft(), relative_path=st_relative_path())
    def test_relative_path_in_key_files_yields_relative_path_finding(
        self, draft: HandoffDraft, relative_path: str
    ) -> None:
        """Injecting a relative path into "Key files" yields a RELATIVE_PATH finding.

        Metamorphic mutation: from a conformant draft (whose "Key files" entries
        are all absolute), append one relative path reference to the "Key files
        for next session" Section and confirm the validator flags it as relative
        and no longer reports ``ok``.

        **Validates: Requirements 5.1, 8.3**
        """
        mutated = inject_relative_path(draft, relative_path, heading=_KEY_FILES)
        result = validate_handoff_summary(mutated.render())
        assert not result.ok
        assert has_finding(result, RELATIVE_PATH)
        assert any(
            relative_path in finding.detail
            for finding in findings_with_code(result, RELATIVE_PATH)
        ), f"no RELATIVE_PATH finding named the injected relative path '{relative_path}'"

    @given(draft=st_handoff_draft(), relative_path=st_relative_path())
    def test_relative_path_in_running_state_yields_relative_path_finding(
        self, draft: HandoffDraft, relative_path: str
    ) -> None:
        """A relative path in the "Running state" Section yields a RELATIVE_PATH finding.

        Metamorphic mutation: from a conformant draft (whose database entry is an
        absolute SQLite path or a PostgreSQL connection string), append a relative
        path reference to the path-bearing "Running state" Section and confirm the
        validator flags the relative database/file reference.

        **Validates: Requirements 5.1, 5.4, 8.3**
        """
        mutated = inject_relative_path(draft, relative_path, heading=_RUNNING_STATE)
        result = validate_handoff_summary(mutated.render())
        assert not result.ok
        assert has_finding(result, RELATIVE_PATH)

    @given(draft=st_handoff_draft(), database_entry=st_database_entry())
    def test_conformant_absolute_references_pass_relative_path_check(
        self, draft: HandoffDraft, database_entry: str
    ) -> None:
        """All-absolute file references (and a PostgreSQL DB entry) pass the check.

        Positive half of the absolute-path invariant: a summary whose "Key files"
        entries are all absolute paths and whose "Running state" database entry is
        either an absolute SQLite path or a PostgreSQL connection string produces
        no ``RELATIVE_PATH`` finding.

        **Validates: Requirements 5.1, 5.4, 8.3**
        """
        conformant = replace(
            draft,
            body=[
                (
                    name,
                    _render_running_state(database_entry, "connected")
                    if name == _RUNNING_STATE
                    else content,
                )
                for name, content in draft.body
            ],
        )
        result = validate_handoff_summary(conformant.render())
        assert not has_finding(result, RELATIVE_PATH)

    # -- Property 3: Forbidden temporal-phrase exclusion --------------------
    # Feature: session-handoff, Property 3: Forbidden temporal-phrase exclusion

    @given(draft=st_handoff_draft(), phrase=st_forbidden_phrase())
    def test_injecting_a_forbidden_phrase_yields_forbidden_phrase_finding(
        self, draft: HandoffDraft, phrase: str
    ) -> None:
        """Injecting any forbidden temporal phrase yields a FORBIDDEN_PHRASE finding.

        Metamorphic mutation: from a conformant draft, append one of the eight
        forbidden temporal phrases to the "Pick up here" Section and confirm the
        validator flags that phrase and no longer reports ``ok``.

        **Validates: Requirements 7.4, 9.3**
        """
        result = validate_handoff_summary(inject_forbidden_phrase(draft, phrase).render())
        assert not result.ok
        assert has_finding(result, FORBIDDEN_PHRASE)
        assert any(
            phrase in finding.detail
            for finding in findings_with_code(result, FORBIDDEN_PHRASE)
        ), f"no FORBIDDEN_PHRASE finding named the injected phrase '{phrase}'"

    @given(draft=st_handoff_draft(), cased_phrase=st_cased_forbidden_phrase())
    def test_forbidden_phrase_match_is_case_insensitive(
        self, draft: HandoffDraft, cased_phrase: str
    ) -> None:
        """A forbidden phrase in altered casing is still flagged (case-insensitive).

        Metamorphic mutation: from a conformant draft, append a forbidden temporal
        phrase whose casing has been changed (upper-, title-, or swapped-case) to
        the "Pick up here" Section and confirm the validator still flags it. The
        finding names the canonical lowercase phrase, recovered by lowercasing the
        injected variant.

        **Validates: Requirements 7.4, 9.3**
        """
        result = validate_handoff_summary(inject_forbidden_phrase(draft, cased_phrase).render())
        assert not result.ok
        assert has_finding(result, FORBIDDEN_PHRASE)
        assert any(
            cased_phrase.lower() in finding.detail
            for finding in findings_with_code(result, FORBIDDEN_PHRASE)
        ), f"no FORBIDDEN_PHRASE finding named the injected phrase '{cased_phrase}'"

    @given(draft=st_handoff_draft())
    def test_conformant_summary_has_no_forbidden_phrase_finding(
        self, draft: HandoffDraft
    ) -> None:
        """A conformant summary (no forbidden phrase) produces no FORBIDDEN_PHRASE finding.

        Positive half of the forbidden temporal-phrase exclusion property: a
        conformant draft, whose "Pick up here" Section carries only a next action
        and a quoted resume phrase, contains none of the eight forbidden phrases,
        so the validator reports no ``FORBIDDEN_PHRASE`` finding.

        **Validates: Requirements 7.4, 9.3**
        """
        result = validate_handoff_summary(draft.render())
        assert not has_finding(result, FORBIDDEN_PHRASE)

    # -- Property 4: No-emoji discipline ------------------------------------
    # Feature: session-handoff, Property 4: No-emoji discipline

    @given(draft=st_handoff_draft(), emoji_char=st_emoji_char())
    def test_injecting_an_emoji_yields_emoji_finding(
        self, draft: HandoffDraft, emoji_char: str
    ) -> None:
        """Injecting any emoji code point yields an EMOJI finding.

        Metamorphic mutation: from a conformant (emoji-free) draft, append a
        single emoji code point — drawn by :func:`st_emoji_char` across every
        ``_EMOJI_RANGES`` block — to the Title and confirm the validator flags the
        emoji and no longer reports ``ok``. The finding names the offending code
        point, so its ``U+XXXX`` form must appear in the detail.

        **Validates: Requirements 9.2**
        """
        result = validate_handoff_summary(inject_emoji(draft, emoji_char).render())
        assert not result.ok
        assert has_finding(result, EMOJI)
        assert any(
            f"U+{ord(emoji_char):04X}" in finding.detail
            for finding in findings_with_code(result, EMOJI)
        ), f"no EMOJI finding named the injected code point U+{ord(emoji_char):04X}"

    @given(draft=st_handoff_draft())
    def test_conformant_summary_has_no_emoji_finding(self, draft: HandoffDraft) -> None:
        """A conformant (emoji-free) summary produces no EMOJI finding.

        Positive half of the no-emoji discipline property: a conformant draft is
        rendered only from the emoji-free prose/path alphabets and the fixed
        verification block, so the validator reports no ``EMOJI`` finding.

        **Validates: Requirements 9.2**
        """
        result = validate_handoff_summary(draft.render())
        assert not has_finding(result, EMOJI)

    def test_every_emoji_range_boundary_is_detected(self) -> None:
        """Every ``_EMOJI_RANGES`` boundary code point is flagged as an EMOJI finding.

        Coverage check complementing the property: for each Unicode range the
        validator treats as emoji, both the low and high boundary code points,
        placed in a summary Title, yield an ``EMOJI`` finding. This guards against
        a declared emoji range being silently undetectable.

        **Validates: Requirements 9.2**
        """
        for low, high in _EMOJI_RANGES:
            for code_point in (low, high):
                result = validate_handoff_summary(f"# Handoff: subject {chr(code_point)}\n")
                assert has_finding(result, EMOJI), (
                    f"emoji code point U+{code_point:04X} was not detected"
                )

    # -- Property 5: Quoted continuation phrase -----------------------------
    # Feature: session-handoff, Property 5: Quoted continuation phrase

    @given(draft=st_handoff_draft())
    def test_unquoting_the_continuation_phrase_yields_unquoted_finding(
        self, draft: HandoffDraft
    ) -> None:
        """Stripping the resume-phrase quotes yields an UNQUOTED_CONTINUATION finding.

        Metamorphic mutation: from a conformant draft (whose "Pick up here" resume
        phrase is enclosed in quotes), remove the enclosing quotes via
        :func:`unquote_continuation` so the continuation phrase is still present
        but no longer quoted, and confirm the validator flags it and no longer
        reports ``ok``.

        **Validates: Requirements 7.2**
        """
        result = validate_handoff_summary(unquote_continuation(draft).render())
        assert not result.ok
        assert has_finding(result, UNQUOTED_CONTINUATION)

    @given(draft=st_handoff_draft())
    def test_straight_quoted_continuation_has_no_unquoted_finding(
        self, draft: HandoffDraft
    ) -> None:
        """A straight-double-quoted resume phrase produces no UNQUOTED_CONTINUATION.

        Positive half of the quoted-continuation property: a conformant draft,
        whose "Pick up here" resume phrase is enclosed in straight double quotes,
        produces no ``UNQUOTED_CONTINUATION`` finding.

        **Validates: Requirements 7.2**
        """
        result = validate_handoff_summary(draft.render())
        assert not has_finding(result, UNQUOTED_CONTINUATION)

    @given(draft=st_handoff_draft(), action=st_prose_line())
    def test_typographic_quoted_continuation_has_no_unquoted_finding(
        self, draft: HandoffDraft, action: str
    ) -> None:
        """A typographic-double-quoted resume phrase produces no UNQUOTED_CONTINUATION.

        Positive half of the quoted-continuation property for the second accepted
        quote form: replacing the "Pick up here" body with a resume phrase
        enclosed in typographic double quotes (U+201C ... U+201D) still satisfies
        the quoted-continuation check, so no ``UNQUOTED_CONTINUATION`` finding is
        produced.

        **Validates: Requirements 7.2**
        """
        typographic = _render_pick_up_here_typographic(action, draft.module_number)
        mutated = replace(
            draft,
            body=[
                (name, typographic if name == _PICK_UP_HERE else content)
                for name, content in draft.body
            ],
        )
        result = validate_handoff_summary(mutated.render())
        assert not has_finding(result, UNQUOTED_CONTINUATION)

    @given(draft=st_handoff_draft(), action=st_prose_line())
    def test_absent_continuation_phrase_has_no_unquoted_finding(
        self, draft: HandoffDraft, action: str
    ) -> None:
        """A "Pick up here" without any continuation phrase is not flagged.

        The continuation phrase's *presence* is enforced by agent instruction, not
        by the validator: when "Pick up here" carries only a next action and no
        continuation phrase at all, the quoted-continuation check has nothing to
        enforce, so no ``UNQUOTED_CONTINUATION`` finding is produced (absence is
        not flagged — only an unquoted *present* phrase is).

        **Validates: Requirements 7.2**
        """
        mutated = replace(
            draft,
            body=[
                (name, action if name == _PICK_UP_HERE else content)
                for name, content in draft.body
            ],
        )
        result = validate_handoff_summary(mutated.render())
        assert not has_finding(result, UNQUOTED_CONTINUATION)


# ---------------------------------------------------------------------------
# Fixed verification block + never-raise robustness (task 2.7)
# ---------------------------------------------------------------------------

# The exact read-only verification command baked into the Verification section
# (Req 6.3). It is intentionally a *relative* command: the validator deliberately
# does not path-check the "Verification" section, so this token must never
# produce a RELATIVE_PATH finding.
_BASELINE_STATUS_COMMAND = "python3 senzing-bootcamp/scripts/baseline_status.py"


def _representative_draft() -> HandoffDraft:
    """Build the design's representative, conformant :class:`HandoffDraft`.

    Mirrors the concrete Module 5 example in design.md: absolute paths in the
    path-bearing sections, the fixed :data:`_VERIFICATION_BLOCK`, a "none"
    Deferred section, and a straight-double-quoted resume phrase. Deterministic
    (no randomness) so the verification-block example tests and the CLI smoke
    tests share one fixed, ``ok``-validating summary.

    Returns:
        A conformant draft whose ``render()`` output ``validate_handoff_summary``
        reports as ``ok``.
    """
    module_number = 5
    body: list[tuple[str, str]] = [
        (
            _WHERE_IT_STARTED,
            "Resumed Module 5 step 5.3. Track Core A. Language Python. "
            "Goal finish the CUSTOMERS_CRM mapping and run a test load.",
        ),
        (
            _DECISIONS,
            "Mapped CRM full name to Senzing NAME_FULL. "
            "Deferred phone normalization to a follow-up.",
        ),
        (
            _KEY_FILES,
            _render_key_files(
                [
                    "/home/bootcamper/senzing/mappers/customers_crm_mapper.py",
                    "/home/bootcamper/senzing/config/mapping_state_customers_crm.json",
                ]
            ),
        ),
        (
            _RUNNING_STATE,
            _render_running_state("/home/bootcamper/senzing/var/senzing.db", "connected"),
        ),
        (_VERIFICATION, _VERIFICATION_BLOCK),
        (_DEFERRED, NONE_MARKER),
        (
            _PICK_UP_HERE,
            _render_pick_up_here(
                "Validate the CUSTOMERS_CRM mapping then run the Module 5 test load.",
                module_number,
            ),
        ),
    ]
    return HandoffDraft(
        title_subject="Module 5 data mapping for CUSTOMERS_CRM",
        body=body,
        module_number=module_number,
    )


def _representative_summary() -> str:
    """Render the design's representative, conformant Handoff_Summary text.

    Returns:
        The rendered summary from :func:`_representative_draft` (``ok`` clean).
    """
    return _representative_draft().render()


class TestVerificationBlock:
    """Example tests for the fixed verification block (Req 6.1-6.4).

    The "Verification - how to confirm things still work" section carries three
    baked-in checks, each paired with an expected outcome, plus a deliberately
    *relative* command (``baseline_status.py``) that the validator must not flag
    as a path violation because it does not path-check the Verification section.
    """

    def test_verification_block_contains_three_checks_with_outcomes(self) -> None:
        """The fixed block names all three checks, each paired with an outcome.

        Asserts the representative Handoff_Summary's Verification section contains
        the ``get_capabilities`` re-establish line (Req 6.2), the exact
        ``python3 senzing-bootcamp/scripts/baseline_status.py`` command (Req 6.3),
        and the current-module artifact-existence check (Req 6.4) - each paired
        with an "expect ..." outcome (Req 6.1).

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
        """
        block = _VERIFICATION_BLOCK

        # Req 6.2: re-establish the MCP_Session by calling get_capabilities.
        assert "get_capabilities" in block
        # Req 6.3: the exact read-only baseline_status command.
        assert _BASELINE_STATUS_COMMAND in block
        # Req 6.4: a check that the current-module artifacts exist.
        assert "artifacts exist" in block
        # Req 6.1: every check states its expected outcome ("expect ...").
        outcome_lines = [line for line in block.splitlines() if "expect" in line.lower()]
        assert len(outcome_lines) == 3, (
            f"expected each of the 3 verification checks to state an outcome, "
            f"found {len(outcome_lines)}"
        )

    def test_representative_summary_with_fixed_block_validates_clean(self) -> None:
        """A summary carrying the fixed verification block validates clean.

        The representative Handoff_Summary embeds :data:`_VERIFICATION_BLOCK`
        verbatim and produces no findings, confirming the baked-in block is
        structurally compatible with the rest of the fixed template.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
        """
        result = validate_handoff_summary(_representative_summary())
        assert result.ok, f"expected a conformant summary, got findings: {result.findings}"

    def test_relative_verification_command_is_not_flagged(self) -> None:
        """The relative baseline_status command in Verification is not path-checked.

        ``senzing-bootcamp/scripts/baseline_status.py`` is a genuine *relative*
        path token, yet because the validator does not path-check the
        "Verification" section it must not yield a RELATIVE_PATH finding (Req 6.3).
        The contrast asserts the identical token *does* trip RELATIVE_PATH inside
        a path-checked section ("Key files"), proving it is the section exemption
        - not token classification - that spares the verification command.

        **Validates: Requirements 6.3**
        """
        command_path = "senzing-bootcamp/scripts/baseline_status.py"
        # Sanity: the command really is a relative path token (has '/', not rooted).
        assert "/" in command_path and not command_path.startswith("/")

        clean = validate_handoff_summary(_representative_summary())
        assert not has_finding(clean, RELATIVE_PATH), (
            "the relative verification command must not be flagged as a path "
            f"violation; findings: {findings_with_code(clean, RELATIVE_PATH)}"
        )

        # Contrast: the same token inside a path-checked section IS flagged.
        contrast = inject_relative_path(_representative_draft(), command_path, heading=_KEY_FILES)
        contrast_result = validate_handoff_summary(contrast.render())
        assert has_finding(contrast_result, RELATIVE_PATH), (
            "the same relative token in the path-checked 'Key files' section "
            "should have produced a RELATIVE_PATH finding"
        )


@st.composite
def st_arbitrary_text(draw) -> str:
    """Draw adversarial text mixing prose, headings, emoji, quotes, and paths.

    Assembles a string from fragments chosen to exercise every parser branch:
    arbitrary Unicode, runs of ``#`` heading markers, real canonical headings,
    quote characters, absolute/relative/URI path tokens, emoji code points,
    forbidden temporal phrases, and control characters. Stresses the validator's
    never-raise posture harder than plain ``hypothesis.strategies.text``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A single adversarial string (possibly empty).
    """
    fragment = st.one_of(
        st.text(),
        st.text(alphabet="#", min_size=1, max_size=8),
        st.sampled_from([f"## {heading}" for heading in BODY_SECTIONS]),
        st.sampled_from(('"', "\u201c", "\u201d", "'", "`")),
        st.sampled_from(("/abs/path.py", "rel/path.py", "postgresql://host/db")),
        st_emoji_char(),
        st.sampled_from(FORBIDDEN_PHRASES),
        st.text(alphabet="\x00\x01\x02\x1b\x7f", max_size=5),
    )
    parts = draw(st.lists(fragment, max_size=25))
    separator = draw(st.sampled_from(("\n", " ", "\n\n", "\t", "")))
    return separator.join(parts)


class TestHandoffSummaryRobustness:
    """Never-raise robustness of ``validate_handoff_summary``.

    The validator mirrors the read-only, never-raise posture of
    ``baseline_status.py``: for arbitrary, malformed, or adversarial input it
    returns a :class:`HandoffValidation` (with ``ok=False`` for non-conformant
    text) rather than raising, and its ``ok`` flag always mirrors an empty
    findings list. This posture is defined in design.md's "Error Handling"
    section and associated with the validator in tasks.md task 1.1. (Req 11.5's
    canonical text separately constrains the script to the standard library.)
    """

    @given(text=st.text())
    def test_never_raises_over_arbitrary_text(self, text: str) -> None:
        """For any text, validation returns a consistent HandoffValidation.

        The result is always a :class:`HandoffValidation` whose boolean ``ok``
        equals "no findings", produced without raising for arbitrary input.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        result = validate_handoff_summary(text)
        assert isinstance(result, HandoffValidation)
        assert isinstance(result.ok, bool)
        assert result.ok == (len(result.findings) == 0)

    @given(text=st_arbitrary_text())
    def test_never_raises_over_adversarial_text(self, text: str) -> None:
        """Adversarial text (headings, emoji, quotes, paths, control chars) never raises.

        Feeds the parser-stressing :func:`st_arbitrary_text` mixture and confirms
        the same invariant: a :class:`HandoffValidation` with ``ok`` mirroring an
        empty findings list, never an exception.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        result = validate_handoff_summary(text)
        assert isinstance(result, HandoffValidation)
        assert isinstance(result.ok, bool)
        assert result.ok == (len(result.findings) == 0)

    def test_never_raises_on_edge_inputs(self) -> None:
        """A curated set of hostile inputs each return a consistent HandoffValidation.

        Exercises empty/whitespace-only strings, non-string types tolerated by the
        validator's ``isinstance`` guard (``None`` / ``int`` / ``list``), control
        and binary-ish characters, heading-marker floods, a very long string, an
        emoji-laden string, an unterminated quote, and a partial-structure
        fragment. Each returns a :class:`HandoffValidation` whose ``ok`` mirrors an
        empty findings list, never raising.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        # The signature is typed ``str``; the values below deliberately include
        # non-strings to exercise the validator's ``isinstance`` guard.
        edge_inputs: list[object] = [
            "",
            "   \t\n   ",
            None,
            12345,
            ["not", "a", "string"],
            "\x00\x01\x02\x1b\x7f",
            "#" * 5000,
            "# " * 2000,
            "a" * 100_000,
            "\U0001f600\U0001f4a9\u2600 handoff",
            '"unterminated quote',
            f"## {BODY_SECTIONS[3]}\nrelative/path.py",
        ]
        for value in edge_inputs:
            result = validate_handoff_summary(value)  # type: ignore[arg-type]
            assert isinstance(result, HandoffValidation), f"non-validation result for {value!r}"
            assert isinstance(result.ok, bool)
            assert result.ok == (len(result.findings) == 0)

    def test_malformed_input_returns_not_ok_without_raising(self) -> None:
        """Malformed input yields ok=False with findings rather than raising.

        The empty string is missing every canonical section, so validation returns
        ``ok=False`` with a non-empty findings list - the never-raise posture
        surfaces problems as findings, not exceptions.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        result = validate_handoff_summary("")
        assert result.ok is False
        assert result.findings

    def test_cli_exits_zero_for_conformant_summary(self, tmp_path: Path) -> None:
        """The CLI returns 0 for a conformant Handoff_Summary file.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        summary_file = tmp_path / "handoff.md"
        summary_file.write_text(_representative_summary(), encoding="utf-8")
        assert main([str(summary_file)]) == 0

    def test_cli_exits_one_for_nonconformant_summary(self, tmp_path: Path) -> None:
        """The CLI returns 1 for a non-conformant Handoff_Summary file.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        summary_file = tmp_path / "not_a_handoff.md"
        summary_file.write_text("just some prose, not a handoff summary", encoding="utf-8")
        assert main([str(summary_file)]) == 1

    def test_cli_exits_one_for_missing_file(self, tmp_path: Path) -> None:
        """The CLI returns 1 (not an exception) when the summary file is missing.

        **Validates: Requirements 11.5 (never-raise posture, design.md Error Handling)**
        """
        missing = tmp_path / "does_not_exist.md"
        assert main([str(missing)]) == 1
