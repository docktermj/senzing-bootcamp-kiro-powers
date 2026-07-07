"""Property-based tests for per-section schema classification (Property 10).

Feature: recap-qr-formatting

Validates that a recap document mixing Paired_Schema and Split_List_Schema
module sections classifies each section independently by its own headings
(Requirement 5.5): a section is Paired_Schema exactly when it contains a
``### Questions & Responses`` heading, and Split_List_Schema exactly when it
contains both ``### Questions Asked`` and ``### Answers Given`` headings.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_recap_pdf import classify_section, parse_recap_markdown  # noqa: E402
from recap_pdf_render import format_qr_section  # noqa: E402

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Latin-1-safe list-item text excluding '#' and newlines so generated content
# can never accidentally form a Markdown heading line and flip classification.
_ITEM_TEXT = st.text(
    alphabet=st.characters(
        min_codepoint=0x20, max_codepoint=0xFF, blacklist_characters="#"
    ),
    min_size=0,
    max_size=30,
)

# Module name / timestamp tokens: alphanumeric only, so headings parse cleanly.
# Free of the em-dash (U+2014), of '#', and of whitespace/newlines.
_MODULE_TOKEN = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    min_size=1,
    max_size=12,
)


def st_qr_pairs() -> st.SearchStrategy[list[tuple[str, str]]]:
    """An ordered list of ``(question, response)`` QR_Pairs."""
    return st.lists(st.tuples(_ITEM_TEXT, _ITEM_TEXT), min_size=0, max_size=5)


def _build_paired_body(pairs: list[tuple[str, str]]) -> str:
    """A Paired_Schema section body built from ``format_qr_section``.

    ``format_qr_section`` always emits exactly one ``### Questions & Responses``
    heading (even for zero substantive pairs), so the body always classifies as
    ``"paired"``.
    """
    return format_qr_section(pairs)


def _build_split_body(questions: list[str], answers: list[str]) -> str:
    """A Split_List_Schema section body with both legacy headings."""
    lines = ["### Questions Asked", ""]
    for i, q in enumerate(questions, start=1):
        lines.append(f"{i}. {q}")
    lines.extend(["", "### Answers Given", ""])
    for i, a in enumerate(answers, start=1):
        lines.append(f"{i}. {a}")
    return "\n".join(lines)


@st.composite
def st_section_body(draw: st.DrawFn) -> tuple[str, str]:
    """Draw one section body and its expected schema label.

    Returns:
        A ``(body_text, expected_schema)`` tuple where ``expected_schema`` is
        ``"paired"`` or ``"split"``.
    """
    schema = draw(st.sampled_from(["paired", "split"]))
    if schema == "paired":
        return _build_paired_body(draw(st_qr_pairs())), "paired"
    questions = draw(st.lists(_ITEM_TEXT, min_size=0, max_size=4))
    answers = draw(st.lists(_ITEM_TEXT, min_size=0, max_size=4))
    return _build_split_body(questions, answers), "split"


@st.composite
def st_mixed_recap(draw: st.DrawFn) -> tuple[str, list[str]]:
    """Build a full recap document interleaving paired and split sections.

    Sections are emitted in random order under valid module headings
    ``## Module N: <name> — <timestamp>`` (em-dash U+2014) so they parse.

    Returns:
        A ``(doc_text, expected_schemas)`` tuple where ``expected_schemas[i]``
        is the schema expected for the i-th parsed section.
    """
    bodies = draw(st.lists(st_section_body(), min_size=1, max_size=6))
    expected: list[str] = []
    blocks: list[str] = []
    for index, (body, schema) in enumerate(bodies, start=1):
        name = draw(_MODULE_TOKEN)
        timestamp = draw(_MODULE_TOKEN)
        heading = f"## Module {index}: {name} \u2014 {timestamp}"
        blocks.append(f"{heading}\n\n{body}")
        expected.append(schema)
    return "\n\n".join(blocks), expected


# ---------------------------------------------------------------------------
# Property 10: Per-section schema classification is independent
# ---------------------------------------------------------------------------


class TestSectionClassification:
    """Validates: Requirements 5.5."""

    # Feature: recap-qr-formatting, Property 10: Per-section schema
    # classification is independent — For any recap document mixing
    # Paired_Schema and Split_List_Schema module sections, each section is
    # classified independently as Paired_Schema exactly when it contains a
    # ### Questions & Responses heading, and as Split_List_Schema exactly when
    # it contains both ### Questions Asked and ### Answers Given headings, and
    # each section is rendered according to its own classification.
    @given(recap=st_mixed_recap())
    def test_each_section_classified_independently(
        self, recap: tuple[str, list[str]]
    ) -> None:
        """Each parsed section's ``.schema`` matches its expected schema,
        independent of neighboring sections."""
        doc_text, expected_schemas = recap
        sections = parse_recap_markdown(doc_text).sections

        assert len(sections) == len(expected_schemas)
        actual_schemas = [section.schema for section in sections]
        assert actual_schemas == expected_schemas

    # Feature: recap-qr-formatting, Property 10: Per-section schema
    # classification is independent (classify_section on individual bodies).
    @given(body=st_section_body())
    def test_classify_section_on_individual_body(
        self, body: tuple[str, str]
    ) -> None:
        """``classify_section`` labels an individual section body by its own
        headings, regardless of any surrounding document."""
        body_text, expected_schema = body
        assert classify_section(body_text) == expected_schema
