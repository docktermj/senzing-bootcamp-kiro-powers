"""
Preservation property tests for single-question format enforcement.

These tests capture baseline behavior that MUST remain unchanged after the fix.
They verify that non-compound outputs (simple yes/no questions, informational
prose, already-formatted numbered lists, and non-question content) are never
flagged or modified by the compound-question detection logic.

These tests MUST PASS on both unfixed and fixed code — any failure indicates
a regression in the detection logic that would incorrectly modify non-compound
outputs.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""

from __future__ import annotations

import re
import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Compound-question detection logic (mirrors what enforcement will use)
# ---------------------------------------------------------------------------

# Patterns that indicate prose-joined alternatives in a 👉 question
_PROSE_OR_PATTERNS = [
    # "X, or Y?" or "X or Y?" within a question
    r",\s+or\s+",
    # "Or" as sentence starter after a question mark or period
    r"[.?]\s+Or\s+",
    # "or would you" / "or shall we" / "or should we"
    r"\bor\s+(?:would you|shall we|should we|can I|do you want)\b",
    # "alternatively" joining options
    r"\balternatively\b",
    # "or if you prefer"
    r"\bor if you prefer\b",
]

_PROSE_OR_RE = re.compile("|".join(_PROSE_OR_PATTERNS), re.IGNORECASE)

# Pattern to detect numbered list format (1. ... 2. ...)
_NUMBERED_LIST_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)


def _extract_question_block(text: str) -> str | None:
    """Extract the 👉 question block from agent output.

    Returns the question text (everything from 👉 to end of the question
    section), or None if no 👉 question is present.
    """
    # Find the 👉 marker
    idx = text.find("👉")
    if idx == -1:
        return None
    return text[idx:]


def is_compound_question(text: str) -> bool:
    """Detect whether agent output contains a compound 👉 question.

    A compound question is one where:
    1. The output contains a 👉 question marker
    2. The question text contains prose-joined alternatives ("or", "Or shall we", etc.)
    3. The alternatives are NOT already formatted as a numbered list

    Returns True if the output contains a compound question (bug condition).
    Returns False for all non-compound outputs (preservation cases).
    """
    question_block = _extract_question_block(text)
    if question_block is None:
        # No 👉 question at all — not a compound question
        return False

    # Check if the question uses numbered list format
    if _NUMBERED_LIST_RE.search(question_block):
        # Already formatted as numbered list — check if "or" is only inside
        # list item descriptions (which is allowed)
        lines = question_block.split("\n")
        for line in lines:
            # Skip lines that are numbered list items — "or" inside them is fine
            if re.match(r"^\s*\d+\.\s+", line):
                continue
            # For non-list lines (the lead question), check for prose-joined alternatives
            if _PROSE_OR_RE.search(line):
                return True
        return False

    # No numbered list — check for prose-joined alternatives
    return bool(_PROSE_OR_RE.search(question_block))


# ---------------------------------------------------------------------------
# Hypothesis strategies for non-compound outputs
# ---------------------------------------------------------------------------

# Simple actions for yes/no questions (no alternatives)
_SIMPLE_ACTIONS = [
    "move on to Module {n}",
    "continue with the next step",
    "create the summary",
    "proceed with the setup",
    "start the verification",
    "run the demo",
    "see the results",
    "begin Module {n}",
    "try the example",
    "review the output",
    "save your progress",
    "commit these changes",
    "load the data",
    "set up the environment",
    "install the SDK",
]

_INFORMATIONAL_SENTENCES = [
    "You can use {lang} for this step.",
    "The SDK supports {lang} and other languages.",
    "This module covers data loading or transformation.",
    "Files are stored in the data directory or a subdirectory.",
    "You'll need Python or Java installed on your system.",
    "The configuration uses JSON or YAML format.",
    "Results can be exported as CSV or JSON.",
    "Entity resolution works with one or more data sources.",
    "The process takes a few seconds or minutes depending on data size.",
    "You can run this locally or in a container.",
]

_LANGUAGES = ["Python", "Java", "TypeScript", "C#", "Rust", "Go"]


def st_simple_yes_no_question() -> st.SearchStrategy[str]:
    """Generate simple yes/no 👉 questions with a single action (no alternatives)."""
    return st.builds(
        lambda action, n, ready_style: (
            f"👉 Ready to {action.format(n=n)}?"
            if ready_style
            else f"👉 Would you like me to {action.format(n=n)}?"
        ),
        action=st.sampled_from(_SIMPLE_ACTIONS),
        n=st.integers(min_value=1, max_value=11),
        ready_style=st.booleans(),
    )


def st_informational_prose_with_or() -> st.SearchStrategy[str]:
    """Generate informational prose containing 'or' but no 👉 question."""
    return st.builds(
        lambda sentences, lang: "\n".join(
            s.format(lang=lang) for s in sentences
        ),
        sentences=st.lists(
            st.sampled_from(_INFORMATIONAL_SENTENCES),
            min_size=1,
            max_size=4,
        ),
        lang=st.sampled_from(_LANGUAGES),
    )


def st_numbered_list_question() -> st.SearchStrategy[str]:
    """Generate 👉 questions already formatted as numbered lists."""
    lead_questions = [
        "What would you like to do next?",
        "Which language would you like to use?",
        "How would you like to proceed?",
        "Which option works best for you?",
        "What approach would you prefer?",
    ]
    list_items = [
        "Continue to the next module",
        "Review the results first",
        "Share with your team or manager",
        "Try a different approach",
        "Skip and move on",
        "Create an executive summary",
        "Run the verification again",
        "Export the results",
        "Set up the environment",
        "Load additional data sources",
        "Explore entity relationships or attributes",
    ]
    return st.builds(
        lambda lead, items: "👉 " + lead + "\n" + "\n".join(
            f"{i+1}. {item}" for i, item in enumerate(items)
        ),
        lead=st.sampled_from(lead_questions),
        items=st.lists(
            st.sampled_from(list_items),
            min_size=2,
            max_size=4,
            unique=True,
        ),
    )


def st_numbered_list_with_or_in_items() -> st.SearchStrategy[str]:
    """Generate numbered list questions where 'or' appears inside item descriptions."""
    lead_questions = [
        "What would you like to do next?",
        "Which option works best?",
        "How would you like to proceed?",
    ]
    # Items that naturally contain "or"
    items_with_or = [
        "Share with your team or manager",
        "Export as CSV or JSON",
        "Use Python or Java for the implementation",
        "Run locally or in a container",
        "Review the matches or mismatches",
        "Explore entity relationships or attributes",
        "Load one or more additional data sources",
        "Configure alerts or notifications",
    ]
    # Items without "or"
    items_without_or = [
        "Move to the next module",
        "Try a different approach",
        "Skip this step",
        "Create a summary",
    ]
    return st.builds(
        lambda lead, or_items, plain_items: (
            "👉 " + lead + "\n" + "\n".join(
                f"{i+1}. {item}"
                for i, item in enumerate(or_items + plain_items)
            )
        ),
        lead=st.sampled_from(lead_questions),
        or_items=st.lists(
            st.sampled_from(items_with_or),
            min_size=1,
            max_size=2,
            unique=True,
        ),
        plain_items=st.lists(
            st.sampled_from(items_without_or),
            min_size=1,
            max_size=2,
            unique=True,
        ),
    )


def st_non_question_content() -> st.SearchStrategy[str]:
    """Generate non-question content (no 👉 marker)."""
    paragraphs = [
        "I've set up the project structure with the following files.",
        "The entity resolution process completed successfully.",
        "Here's what changed in this step:",
        "The data was loaded from two sources or more.",
        "You can find the results in the output directory.",
        "This step configures the SDK for Python or Java.",
        "The verification passed — all entities resolved correctly.",
        "I've created the mapping file or updated the existing one.",
    ]
    code_blocks = [
        '```python\nresult = engine.get_entity(entity_id)\nprint(result)\n```',
        '```json\n{\n  "RECORD_ID": "1001",\n  "NAME_FULL": "Robert Smith"\n}\n```',
    ]
    return st.builds(
        lambda paras, code: "\n\n".join(paras) + ("\n\n" + code if code else ""),
        paras=st.lists(
            st.sampled_from(paragraphs),
            min_size=1,
            max_size=3,
        ),
        code=st.one_of(st.none(), st.sampled_from(code_blocks)),
    )


# ---------------------------------------------------------------------------
# Observation tests (concrete examples from the task)
# ---------------------------------------------------------------------------

class TestPreservationObservations:
    """Concrete observation tests verifying baseline behavior on unfixed code.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    """

    def test_simple_yes_no_passes_through(self):
        """Observe: '👉 Ready to move on to Module 3?' passes through unchanged."""
        text = "👉 Ready to move on to Module 3?"
        assert not is_compound_question(text), (
            "Simple yes/no question should NOT be flagged as compound"
        )

    def test_informational_prose_with_or_passes_through(self):
        """Observe: informational prose with 'or' passes through unchanged."""
        text = "Here you can use Python or Java for this step."
        assert not is_compound_question(text), (
            "Informational prose with 'or' should NOT be flagged as compound"
        )

    def test_numbered_list_with_or_in_item_passes_through(self):
        """Observe: numbered list with 'or' in item passes through unchanged."""
        text = (
            "👉 What would you like to do next?\n"
            "1. Share with your team or manager\n"
            "2. Move to Module 3"
        )
        assert not is_compound_question(text), (
            "Numbered list with 'or' inside item should NOT be flagged"
        )

    def test_single_yes_no_confirmation_passes_through(self):
        """Observe: '👉 Would you like me to create the summary?' passes through."""
        text = "👉 Would you like me to create the summary?"
        assert not is_compound_question(text), (
            "Single yes/no confirmation should NOT be flagged as compound"
        )

    def test_non_question_content_with_or_passes_through(self):
        """Observe: non-question content with 'or' passes through unchanged."""
        text = (
            "The SDK supports Python or Java. You can choose either one "
            "for this module. The setup process is similar for both."
        )
        assert not is_compound_question(text), (
            "Non-question content with 'or' should NOT be flagged"
        )


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

class TestPreservationSimpleYesNo:
    """Property: Simple yes/no questions are never flagged as compound.

    **Validates: Requirements 3.1, 3.5**
    """

    @given(text=st_simple_yes_no_question())
    @settings(max_examples=10)
    def test_simple_yes_no_never_flagged(self, text: str):
        """For any simple yes/no question with a single action and no
        alternatives, the detection function must return False."""
        assert not is_compound_question(text), (
            f"Simple yes/no question incorrectly flagged as compound: {text!r}"
        )


class TestPreservationInformationalProse:
    """Property: Informational prose containing 'or' is never flagged.

    **Validates: Requirements 3.2**
    """

    @given(text=st_informational_prose_with_or())
    @settings(max_examples=10)
    def test_informational_prose_with_or_never_flagged(self, text: str):
        """For any informational prose containing 'or' but no 👉 question,
        the detection function must return False."""
        assert not is_compound_question(text), (
            f"Informational prose incorrectly flagged as compound: {text!r}"
        )


class TestPreservationNumberedList:
    """Property: Questions already formatted as numbered lists are not double-reformatted.

    **Validates: Requirements 3.3**
    """

    @given(text=st_numbered_list_question())
    @settings(max_examples=10)
    def test_numbered_list_questions_never_flagged(self, text: str):
        """For any question already formatted as a numbered list, the
        detection function must return False (no double-reformatting)."""
        assert not is_compound_question(text), (
            f"Numbered list question incorrectly flagged as compound: {text!r}"
        )


class TestPreservationOrInsideListItems:
    """Property: 'or' inside numbered list item descriptions is not flagged.

    **Validates: Requirements 3.3**
    """

    @given(text=st_numbered_list_with_or_in_items())
    @settings(max_examples=10)
    def test_or_inside_list_items_never_flagged(self, text: str):
        """For any numbered list question where 'or' appears inside item
        descriptions, the detection function must return False."""
        assert not is_compound_question(text), (
            f"'or' inside list item incorrectly flagged as compound: {text!r}"
        )


class TestPreservationNonQuestionContent:
    """Property: Non-question content is never flagged.

    **Validates: Requirements 3.2**
    """

    @given(text=st_non_question_content())
    @settings(max_examples=10)
    def test_non_question_content_never_flagged(self, text: str):
        """For any non-question content (no 👉 marker), the detection
        function must return False regardless of 'or' presence."""
        assert not is_compound_question(text), (
            f"Non-question content incorrectly flagged as compound: {text!r}"
        )
