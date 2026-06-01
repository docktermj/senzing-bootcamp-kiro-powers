"""Tests for the conversational-eval harness (`eval_conversations.py`).

This module starts with unit tests for the pure detection heuristics that the
assertion predicates build on: `count_pointers`, `pointer_question_line`,
`has_conjunction`, `count_question_marks`, and `text_after`. Later tasks append
additional test classes (predicate property tests, loader/validator tests,
runner/CLI tests) to this same file.

Feature: conversational-eval-harness
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from eval_conversations import (  # noqa: E402
    POINTER,
    AssertionOutcome,
    AssertionSpec,
    DEFAULT_FIXTURES_DIR,
    EmptyDirError,
    EvalContext,
    EvalError,
    EvalFailure,
    ParseError,
    Scenario,
    SchemaError,
    Turn,
    _absent_marker,
    _contains_marker,
    _ends_with_question_then_stop,
    _exactly_one_pointer,
    _gate_not_bypassed,
    _mentions_tool,
    _no_compound_question,
    _no_self_answer,
    _transition_response_completeness,
    count_assertions,
    count_pointers,
    count_question_marks,
    evaluate_scenario,
    evaluate_turn,
    has_conjunction,
    load_scenarios,
    main,
    parse_scenario,
    pointer_question_line,
    run,
    text_after,
)


# ---------------------------------------------------------------------------
# Shared helper: build a Turn + EvalContext and invoke a predicate
# ---------------------------------------------------------------------------


def _outcome(
    predicate: object, content: str, params: dict[str, object] | None = None
) -> AssertionOutcome:
    """Invoke a predicate against a single agent turn built from ``content``.

    Args:
        predicate: The predicate callable under test.
        content: The agent-turn text to evaluate.
        params: Optional assertion parameters; defaults to an empty dict.

    Returns:
        The AssertionOutcome the predicate produced for the constructed turn.
    """
    turn = Turn(role="agent", content=content, assertions=[])
    ctx = EvalContext(turns=[turn], index=0)
    return predicate(turn, ctx, params or {})


# ---------------------------------------------------------------------------
# Tests: Detection heuristics
# ---------------------------------------------------------------------------


class TestDetectionHeuristics:
    """Unit tests for the pure detection heuristics in `eval_conversations`.

    Covers `count_pointers`, `pointer_question_line`, `has_conjunction`,
    `count_question_marks`, and `text_after` with their edge cases.

    Validates: Requirements 12.5, 3.1, 3.3
    """

    # -- count_pointers -----------------------------------------------------

    def test_count_pointers_zero(self) -> None:
        """No pointer marker yields a count of zero."""
        assert count_pointers("Just plain text with no marker.") == 0

    def test_count_pointers_one(self) -> None:
        """A single pointer marker yields a count of one."""
        assert count_pointers(f"{POINTER} How many sources?") == 1

    def test_count_pointers_multiple(self) -> None:
        """Multiple pointer markers are each counted."""
        text = f"{POINTER} First?\n{POINTER} Second?\n{POINTER} Third?"
        assert count_pointers(text) == 3

    # -- pointer_question_line ---------------------------------------------

    def test_pointer_question_line_present(self) -> None:
        """A line containing both the pointer and a '?' is returned verbatim."""
        line = f"{POINTER} How many distinct data sources?"
        text = f"Some intro.\n{line}\nTrailing text."
        assert pointer_question_line(text) == line

    def test_pointer_question_line_pointer_without_question(self) -> None:
        """A pointer line with no '?' is not treated as a pointer question line."""
        text = f"{POINTER} This is a directive, not a question."
        assert pointer_question_line(text) is None

    def test_pointer_question_line_question_without_pointer(self) -> None:
        """A question line with no pointer is not a pointer question line."""
        text = "Is this a question without a pointer?"
        assert pointer_question_line(text) is None

    def test_pointer_question_line_none(self) -> None:
        """Text with neither a pointer nor a question mark returns None."""
        assert pointer_question_line("Just a plain statement.") is None

    def test_pointer_question_line_first_match_when_multiple(self) -> None:
        """When several lines qualify, the first matching line is returned."""
        first = f"{POINTER} First question?"
        second = f"{POINTER} Second question?"
        text = f"{first}\n{second}"
        assert pointer_question_line(text) == first

    # -- has_conjunction ----------------------------------------------------

    def test_has_conjunction_or(self) -> None:
        """A bare ' or ' joining alternatives is detected."""
        assert has_conjunction("Do you want apples or oranges?") is True

    def test_has_conjunction_alternatively(self) -> None:
        """The word 'alternatively' is detected as a conjunction."""
        assert has_conjunction("We could load now. Alternatively, we map first.") is True

    def test_has_conjunction_or_would_you_rather(self) -> None:
        """'or would you rather' is detected as a conjunction."""
        assert has_conjunction("Should we load now or would you rather wait?") is True

    def test_has_conjunction_or_should_we(self) -> None:
        """'or should we' is detected as a conjunction."""
        assert has_conjunction("Do you want to map now or should we explore?") is True

    def test_has_conjunction_or_would_you_prefer(self) -> None:
        """'or would you prefer' is detected as a conjunction."""
        assert has_conjunction("Load it now or would you prefer a dry run?") is True

    def test_has_conjunction_or_if_you_prefer(self) -> None:
        """'or if you prefer' is detected as a conjunction."""
        assert has_conjunction("I can do it, or if you prefer you can drive.") is True

    def test_has_conjunction_trailing_or_not_matched(self) -> None:
        """A trailing 'or' at the end of the text does not match (negative lookahead)."""
        assert has_conjunction("Should we continue or") is False

    def test_has_conjunction_case_insensitive(self) -> None:
        """Conjunction matching is case-insensitive."""
        assert has_conjunction("Cats OR dogs?") is True
        assert has_conjunction("ALTERNATIVELY, we wait.") is True

    def test_has_conjunction_clean_single_sentence(self) -> None:
        """A clean single sentence with no conjunction returns False."""
        assert has_conjunction("How many distinct data sources will we use?") is False

    # -- count_question_marks ----------------------------------------------

    def test_count_question_marks_zero(self) -> None:
        """A statement with no '?' yields a count of zero."""
        assert count_question_marks("This is a declarative sentence.") == 0

    def test_count_question_marks_one(self) -> None:
        """A single question mark yields a count of one."""
        assert count_question_marks("How many sources are there?") == 1

    def test_count_question_marks_multiple(self) -> None:
        """Multiple question marks are each counted."""
        assert count_question_marks("Ready? Set? Go?") == 3

    # -- text_after ---------------------------------------------------------

    def test_text_after_returns_content_after_marker(self) -> None:
        """Content following the marker line is returned, stripped."""
        marker = f"{POINTER} What is the count?"
        text = f"{marker}\nI'll assume three for now."
        assert text_after(text, marker) == "I'll assume three for now."

    def test_text_after_empty_marker_returns_empty(self) -> None:
        """An empty marker returns an empty string."""
        assert text_after("Any content here.", "") == ""

    def test_text_after_marker_not_found_returns_empty(self) -> None:
        """A marker absent from the text returns an empty string."""
        assert text_after("Some content.", "missing marker line") == ""

    def test_text_after_only_whitespace_after_returns_empty(self) -> None:
        """Only-whitespace content after the marker is stripped to empty string."""
        marker = f"{POINTER} Ready to continue?"
        text = f"{marker}\n   \n\t  "
        assert text_after(text, marker) == ""


# ===========================================================================
# Property tests: assertion predicates (Properties P3-P10)
# ===========================================================================
#
# Each predicate has the uniform signature (turn, ctx, params) -> AssertionOutcome
# and is invoked through the _outcome() helper above. Strategies are written to
# constrain generated text to the relevant input space so generated cases land
# deterministically on the pass/fail side they are meant to exercise. All
# property tests use @settings(max_examples=20) per the repo test convention.

# Plain words with no pointer, no question mark, and none of the distinctive
# compound conjunctions — safe filler for building single questions / prompts.
_PLAIN_WORDS: list[str] = [
    "how", "many", "data", "sources", "systems", "will", "we", "use",
    "load", "map", "records", "entities", "ready", "continue", "next", "explore",
]

# Lowercase-letter token strategy (never contains the pointer, the hard-stop
# marker, or the phrase "end your response").
st_alpha_token = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)

# A hard-stop / "end your response" boundary line — treated as a turn boundary,
# not as substantive content or a self-answer.
_BOUNDARY_LINE = "\U0001f6d1 STOP \u2014 End your response here."


@st.composite
def st_pointer_question_line(draw: st.DrawFn) -> str:
    """Build a single pointer question line: the pointer marker + words + '?'."""
    words = draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=8))
    return f"{POINTER} " + " ".join(words) + "?"


# ---------------------------------------------------------------------------
# Property 3: exactly_one_pointer soundness
# ---------------------------------------------------------------------------


@st.composite
def st_pointer_text(draw: st.DrawFn) -> tuple[int, str]:
    """Build text containing a controlled number of pointer markers (0-4).

    Returns the intended pointer count alongside the text. Filler segments use a
    lowercase + space alphabet only, so they never introduce a stray pointer and
    the resulting pointer count equals the drawn count exactly.
    """
    count = draw(st.integers(min_value=0, max_value=4))
    fillers = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=10),
            min_size=count + 1,
            max_size=count + 1,
        )
    )
    return count, POINTER.join(fillers)


class TestExactlyOnePointerProperty:
    """Property 3: `exactly_one_pointer` passes iff the pointer count is exactly one.

    Validates: Requirements 3.1, 12.3
    """

    @given(st_pointer_text())
    @settings(max_examples=20)
    def test_passes_iff_exactly_one_pointer(self, payload: tuple[int, str]) -> None:
        """The predicate passes if and only if the text holds exactly one pointer."""
        count, text = payload
        assert count_pointers(text) == count  # generator sanity check
        outcome = _outcome(_exactly_one_pointer, text)
        assert outcome.passed == (count == 1)


# ---------------------------------------------------------------------------
# Property 4: ends_with_question_then_stop soundness
# ---------------------------------------------------------------------------


@st.composite
def st_stopped_turn(draw: st.DrawFn) -> str:
    """Build a turn ending on a pointer prompt, optionally + hard-stop / whitespace."""
    parts: list[str] = [draw(st_pointer_question_line())]
    if draw(st.booleans()):
        parts.append(_BOUNDARY_LINE)
    if draw(st.booleans()):
        parts.append("   ")  # trailing whitespace-only line
    return "\n".join(parts)


@st.composite
def st_substantive_suffix(draw: st.DrawFn) -> str:
    """Build a substantive, non-boundary line to append after the pointer prompt.

    Covers both substantive agent prose and a simulated bootcamper reply. Neither
    form contains a pointer, the hard-stop marker, or the "end your response"
    phrase, so each is genuinely substantive content (not a boundary).
    """
    word = draw(st_alpha_token)
    if draw(st.sampled_from(["prose", "reply"])) == "prose":
        return f"this is more agent prose {word}."
    return f"bootcamper: {word}"


class TestEndsWithQuestionThenStopProperty:
    """Property 4: `ends_with_question_then_stop` soundness.

    Passes when a pointer prompt is followed only by whitespace / a hard-stop
    boundary; fails when substantive prose or a simulated reply is appended after
    the prompt line.

    Validates: Requirements 3.2
    """

    @given(st_stopped_turn())
    @settings(max_examples=20)
    def test_stopped_turn_passes(self, content: str) -> None:
        """A turn that ends on the pointer prompt (only boundary/whitespace after) passes."""
        assert _outcome(_ends_with_question_then_stop, content).passed

    @given(st_stopped_turn(), st_substantive_suffix())
    @settings(max_examples=20)
    def test_substantive_suffix_fails(self, base: str, suffix: str) -> None:
        """Appending substantive content after the prompt (new line) flips to fail."""
        content = f"{base}\n{suffix}"
        assert not _outcome(_ends_with_question_then_stop, content).passed


# ---------------------------------------------------------------------------
# Property 5: no_compound_question soundness
# ---------------------------------------------------------------------------

# Distinctive multi-word conjunctions that unambiguously introduce a second
# alternative clause (COMPOUND_CONJUNCTION_PATTERNS minus the bare "or"). A bare
# "or" joining nouns is NOT a compound question and is intentionally excluded.
_DISTINCTIVE_CONJUNCTIONS: list[str] = [
    "alternatively",
    "or would you rather",
    "or should we",
    "or would you prefer",
    "or if you prefer",
]


@st.composite
def st_single_question(draw: st.DrawFn) -> str:
    """Build a single question: one '?' and no distinctive compound conjunction."""
    words = draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=8))
    return f"{POINTER} " + " ".join(words) + "?"


@st.composite
def st_compound_question(draw: st.DrawFn) -> str:
    """Build a compound (failing) question via two '?' or a distinctive conjunction."""
    if draw(st.sampled_from(["two_marks", "conjunction"])) == "two_marks":
        left = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=5)))
        right = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=5)))
        return f"{POINTER} {left}? {right}?"
    conj = draw(st.sampled_from(_DISTINCTIVE_CONJUNCTIONS))
    left = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=4)))
    right = " ".join(draw(st.lists(st.sampled_from(_PLAIN_WORDS), min_size=1, max_size=4)))
    return f"{POINTER} {left} {conj} {right}?"


class TestNoCompoundQuestionProperty:
    """Property 5: `no_compound_question` soundness.

    Passes for a single question with no distinctive conjunction; fails for two
    question marks or a distinctive multi-word conjunction joining alternatives.

    Validates: Requirements 3.3, 12.4
    """

    @given(st_single_question())
    @settings(max_examples=20)
    def test_single_question_passes(self, content: str) -> None:
        """A single, simple question (one '?', no distinctive conjunction) passes."""
        assert _outcome(_no_compound_question, content).passed

    @given(st_compound_question())
    @settings(max_examples=20)
    def test_compound_question_fails(self, content: str) -> None:
        """Two questions or a distinctive conjunction joining alternatives fails."""
        assert not _outcome(_no_compound_question, content).passed


# ---------------------------------------------------------------------------
# Property 6: no_self_answer soundness
# ---------------------------------------------------------------------------


@st.composite
def st_question_then_boundary(draw: st.DrawFn) -> str:
    """Build a pointer question followed only by a hard-stop / boundary line."""
    return f"{draw(st_pointer_question_line())}\n{_BOUNDARY_LINE}"


@st.composite
def st_declarative_answer(draw: st.DrawFn) -> str:
    """Build a declarative answering sentence (no pointer, not a boundary line)."""
    return f"I'll assume {draw(st_alpha_token)} for now."


class TestNoSelfAnswerProperty:
    """Property 6: `no_self_answer` soundness.

    Passes for a pointer question followed only by a hard-stop / "end your
    response" boundary; fails when a declarative answering sentence is appended
    after the question line.

    Validates: Requirements 3.4
    """

    @given(st_question_then_boundary())
    @settings(max_examples=20)
    def test_question_then_boundary_passes(self, content: str) -> None:
        """A pointer question closed by a boundary, with no answer, passes."""
        assert _outcome(_no_self_answer, content).passed

    @given(st_question_then_boundary(), st_declarative_answer())
    @settings(max_examples=20)
    def test_appended_self_answer_fails(self, base: str, answer: str) -> None:
        """Appending a declarative answer after the question line flips to fail."""
        content = f"{base}\n{answer}"
        assert not _outcome(_no_self_answer, content).passed


# ---------------------------------------------------------------------------
# Property 7: marker-presence soundness (contains_marker / absent_marker)
# ---------------------------------------------------------------------------


@st.composite
def st_content_and_marker(draw: st.DrawFn) -> tuple[str, str]:
    """Build (content, marker) pairs covering both present and absent cases."""
    marker = draw(st.text(max_size=6))
    if draw(st.booleans()):
        pre = draw(st.text(max_size=6))
        post = draw(st.text(max_size=6))
        content = f"{pre}{marker}{post}"  # marker is a substring (when non-empty)
    else:
        content = draw(st.text(max_size=12))
    return content, marker


class TestMarkerPresenceProperty:
    """Property 7: `contains_marker` / `absent_marker` soundness.

    `contains_marker` passes iff the marker is a substring of the content;
    `absent_marker` is its exact logical complement for the same inputs.

    Validates: Requirements 3.5, 3.6
    """

    @given(st_content_and_marker())
    @settings(max_examples=20)
    def test_marker_predicates_are_complements(self, pair: tuple[str, str]) -> None:
        """Each predicate matches substring membership and they are complements."""
        content, marker = pair
        present = marker in content
        contains = _outcome(_contains_marker, content, {"marker": marker})
        absent = _outcome(_absent_marker, content, {"marker": marker})
        assert contains.passed == present
        assert absent.passed == (not present)
        assert contains.passed != absent.passed


# ---------------------------------------------------------------------------
# Property 8: mentions_tool soundness
# ---------------------------------------------------------------------------

_TOOL_NAMES: list[str] = ["search_docs", "get_data_sources", "ingest"]
# Words that never contain any tool name as a substring, used to surround a tool
# token (present case) or to build tool-free text (absent case).
_BOUND_WORDS: list[str] = ["foo", "bar", "baz", "qux", "load", "map", "graph"]


@st.composite
def st_tool_case(draw: st.DrawFn) -> tuple[str, str, bool]:
    """Build (tool, content, expected) cases for word-boundary tool detection.

    * present  — the tool appears as a whitespace-delimited token (word boundaries).
    * embedded — the tool is buried inside a larger identifier (no word boundary).
    * absent   — the tool does not occur at all.
    """
    tool = draw(st.sampled_from(_TOOL_NAMES))
    mode = draw(st.sampled_from(["present", "embedded", "absent"]))
    if mode == "present":
        lead = draw(st.lists(st.sampled_from(_BOUND_WORDS), max_size=3))
        trail = draw(st.lists(st.sampled_from(_BOUND_WORDS), max_size=3))
        return tool, " ".join(lead + [tool] + trail), True
    if mode == "embedded":
        return tool, f"x{tool}y", False
    words = draw(st.lists(st.sampled_from(_BOUND_WORDS), min_size=1, max_size=5))
    return tool, " ".join(words), False


class TestMentionsToolProperty:
    """Property 8: `mentions_tool` soundness.

    Passes iff the tool name occurs as a word-boundary token in the text. A tool
    buried inside a larger identifier (e.g. "xsearch_docsy") does not match.

    Validates: Requirements 3.7
    """

    @given(st_tool_case())
    @settings(max_examples=20)
    def test_passes_iff_token_present(self, case: tuple[str, str, bool]) -> None:
        """The predicate passes exactly when the tool appears as a token."""
        tool, content, expected = case
        assert _outcome(_mentions_tool, content, {"tool": tool}).passed == expected


# ---------------------------------------------------------------------------
# Property 9: transition_response_completeness soundness
# ---------------------------------------------------------------------------


@st.composite
def st_transition_case(draw: st.DrawFn) -> tuple[str, bool]:
    """Build a transition turn that is complete, missing a marker, or too short.

    The four marker fragments are deliberately non-overlapping so that dropping
    one fragment removes exactly one required marker. The "short" variant carries
    all four markers in <= 50 characters to exercise the length condition alone.
    """
    n = draw(st.integers(min_value=1, max_value=9))
    fragments = {
        "banner": f"MODULE {n} - Loading Your Data",
        "journey": "Here is your journey map so far.",
        "before_after": "Before: messy records. After: resolved entities.",
        "first_step": "Step 1: connect your data source.",
    }
    variant = draw(
        st.sampled_from(
            ["complete", "drop_banner", "drop_journey", "drop_before_after",
             "drop_first_step", "short"]
        )
    )
    if variant == "short":
        return f"MODULE {n} journey before after Step 1", False
    if variant != "complete":
        fragments.pop(variant[len("drop_"):])
    return "\n".join(fragments.values()), (variant == "complete")


class TestTransitionResponseCompletenessProperty:
    """Property 9: `transition_response_completeness` soundness.

    Passes with all four markers (banner, journey map, before/after, first step)
    AND length > 50; fails when any marker is dropped or the length is <= 50.

    Validates: Requirements 3.8
    """

    @given(st_transition_case())
    @settings(max_examples=20)
    def test_passes_iff_complete_and_long(self, case: tuple[str, bool]) -> None:
        """Passes iff all four markers are present and length exceeds 50 characters."""
        content, expected = case
        assert _outcome(_transition_response_completeness, content).passed == expected


# ---------------------------------------------------------------------------
# Property 10: gate_not_bypassed soundness
# ---------------------------------------------------------------------------

_GATE_EXECUTION_EVIDENCE: list[str] = [
    "Your visualization is running.",
    "Checkpoint written: module_3_verification = passed.",
    "module_3_verification recorded.",
    "\U0001f6d1 STOP \u2014 End your response here.",
]
_GATE_BYPASS_PHRASES: list[str] = [
    "You can skip this phase.",
    "We can bypass it.",
    "Let's move on to module 4.",
    "We could move past this gate.",
]
# Benign words that contain no execution marker and no skip/bypass language.
_GATE_BENIGN_WORDS: list[str] = [
    "the", "gate", "ran", "successfully", "explore", "entities", "graph", "details",
]


@st.composite
def st_gate_case(draw: st.DrawFn) -> tuple[str, str, str]:
    """Build (evidence, benign filler, bypass phrase) parts for a gate turn."""
    evidence = draw(st.sampled_from(_GATE_EXECUTION_EVIDENCE))
    benign = " ".join(draw(st.lists(st.sampled_from(_GATE_BENIGN_WORDS), max_size=6)))
    bypass = draw(st.sampled_from(_GATE_BYPASS_PHRASES))
    return evidence, benign, bypass


class TestGateNotBypassedProperty:
    """Property 10: `gate_not_bypassed` soundness.

    Passes with execution evidence present and no skip/bypass offer; fails when a
    bypass phrase is added or when all execution evidence is removed.

    Validates: Requirements 3.9
    """

    _PARAMS: dict[str, object] = {"step": "3.9"}

    @given(st_gate_case())
    @settings(max_examples=20)
    def test_gate_soundness(self, case: tuple[str, str, str]) -> None:
        """A gate turn passes with evidence/no-bypass and fails on bypass or no evidence."""
        evidence, benign, bypass = case
        passing = f"{evidence} {benign}".strip()
        assert _outcome(_gate_not_bypassed, passing, self._PARAMS).passed

        bypassed = f"{passing} {bypass}"
        assert not _outcome(_gate_not_bypassed, bypassed, self._PARAMS).passed

        no_evidence = benign if benign else "the gate ran"
        assert not _outcome(_gate_not_bypassed, no_evidence, self._PARAMS).passed


# ===========================================================================
# Property tests: loader / validator (Properties P1-P2)
# ===========================================================================
#
# These exercise parse_scenario / load_scenarios directly. parse_scenario is a
# pure function over an already-parsed JSON object (a dict), so the round-trip
# and rejection properties below build dicts rather than serialized JSON; the
# load_scenarios example tests (TestLoadingBehavior) cover the JSON-on-disk path.

# Safe identifier alphabet: letters, digits, underscore only. Using this for
# scenario ids keeps their repr() free of escaping, so a plain substring check
# against an error message (which formats the id via {scenario_id!r}) holds.
_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
st_scenario_id = st.text(alphabet=_ID_ALPHABET, min_size=1, max_size=12)

# Tool / step values for the parameterized assertion types.
_TOOL_PARAM_VALUES: list[str] = ["search_docs", "get_data_sources", "ingest"]
_STEP_PARAM_VALUES: list[str] = ["3.9", "1.2", "5.4", "9.1"]
# Parameterless registered assertion types (no required params).
_PARAMLESS_ASSERTION_TYPES: list[str] = [
    "exactly_one_pointer",
    "no_compound_question",
    "no_self_answer",
    "ends_with_question_then_stop",
]


@st.composite
def st_assertion(draw: st.DrawFn) -> dict[str, object]:
    """Build a single valid assertion object drawn from the registered types.

    Parameterless types yield ``{"type": ...}``; parameterized types add their
    required named field (``marker`` / ``tool`` / ``step``) so the assertion is
    schema-valid (R2.6).
    """
    kind = draw(
        st.sampled_from(
            _PARAMLESS_ASSERTION_TYPES
            + ["contains_marker", "absent_marker", "mentions_tool", "gate_not_bypassed"]
        )
    )
    assertion: dict[str, object] = {"type": kind}
    if kind in ("contains_marker", "absent_marker"):
        assertion["marker"] = draw(st.text(min_size=1, max_size=8))
    elif kind == "mentions_tool":
        assertion["tool"] = draw(st.sampled_from(_TOOL_PARAM_VALUES))
    elif kind == "gate_not_bypassed":
        assertion["step"] = draw(st.sampled_from(_STEP_PARAM_VALUES))
    return assertion


@st.composite
def st_valid_turn(draw: st.DrawFn) -> dict[str, object]:
    """Build a schema-valid turn dict.

    Agent turns MAY carry a list of assertions (possibly empty, sometimes the
    field is omitted); bootcamper turns never carry assertions (R2.3, R2.4).
    """
    role = draw(st.sampled_from(["agent", "bootcamper"]))
    turn: dict[str, object] = {"role": role, "content": draw(st.text(max_size=40))}
    if role == "agent" and draw(st.booleans()):
        turn["assertions"] = draw(st.lists(st_assertion(), max_size=4))
    return turn


@st.composite
def st_valid_fixture(draw: st.DrawFn) -> dict[str, object]:
    """Build a JSON object conforming to the Scenario_Fixture schema (R1, R2).

    Non-empty ``scenario`` string, string ``description``, optional ``rule_ref``
    (sometimes present, sometimes absent), and a ``turns`` list with >= 1 turn.
    """
    fixture: dict[str, object] = {
        "scenario": draw(st_scenario_id),
        "description": draw(st.text(max_size=40)),
        "turns": draw(st.lists(st_valid_turn(), min_size=1, max_size=5)),
    }
    if draw(st.booleans()):
        fixture["rule_ref"] = draw(st.text(max_size=20))
    return fixture


class TestValidFixtureRoundTripProperty:
    """Property 1: Valid fixtures round-trip into a Scenario.

    A schema-conforming JSON object parses into a Scenario whose scalar fields
    equal the input (rule_ref None when absent), whose turn count matches, and
    whose turn roles/contents and per-turn assertion types/params are preserved
    in order.

    Validates: Requirements 1.2, 1.3, 1.4, 1.6, 2.1, 2.2, 2.3
    """

    @given(st_valid_fixture())
    @settings(max_examples=20)
    def test_round_trip_preserves_fields_and_order(self, fixture: dict[str, object]) -> None:
        """parse_scenario preserves scalars, turn order, and assertion order."""
        scenario = parse_scenario(fixture, Path("mem.json"))

        assert isinstance(scenario, Scenario)
        assert scenario.scenario == fixture["scenario"]  # R1.2
        assert scenario.description == fixture["description"]  # R1.3
        assert scenario.rule_ref == fixture.get("rule_ref")  # R1.6 (None when absent)
        assert scenario.source == Path("mem.json")

        raw_turns = fixture["turns"]
        assert isinstance(raw_turns, list)
        assert len(scenario.turns) == len(raw_turns)  # R1.4

        for parsed_turn, raw_turn in zip(scenario.turns, raw_turns):
            assert parsed_turn.role == raw_turn["role"]  # R2.1, order preserved
            assert parsed_turn.content == raw_turn["content"]  # R2.2

            raw_assertions = raw_turn.get("assertions", [])
            assert len(parsed_turn.assertions) == len(raw_assertions)  # R2.3
            for spec, raw_assertion in zip(parsed_turn.assertions, raw_assertions):
                assert isinstance(spec, AssertionSpec)
                assert spec.type == raw_assertion["type"]  # R2.5, order preserved
                expected_params = {
                    key: value for key, value in raw_assertion.items() if key != "type"
                }
                assert spec.params == expected_params  # R2.6


# ---------------------------------------------------------------------------
# Property 2: structurally invalid fixtures are rejected with an attributed error
# ---------------------------------------------------------------------------

# Roles that are neither "agent" nor "bootcamper" (case-sensitive, R2.1).
_INVALID_ROLES: list[str] = ["system", "user", "moderator", "assistant", "AGENT", "Bootcamper", ""]


@st.composite
def st_invalid_fixture(draw: st.DrawFn) -> tuple[dict[str, object], str, int, str | None]:
    """Build a structurally invalid fixture and its expected attribution.

    Generates one of five violation kinds, placing the single offending turn at a
    known index after zero or more valid turns (parse_scenario raises on the first
    invalid turn, so the leading turns must be valid).

    Returns:
        A 4-tuple of (fixture, scenario_id, offending_turn_index, unknown_type).
        ``unknown_type`` is the offending assertion type string for the
        unknown-type kind, else None.
    """
    scenario_id = draw(st_scenario_id)
    leading = [{"role": "agent", "content": "ok"} for _ in range(draw(st.integers(0, 3)))]
    bad_index = len(leading)
    unknown_type: str | None = None

    kind = draw(
        st.sampled_from(
            ["missing_role", "missing_content", "bad_role", "bootcamper_assertions", "unknown_type"]
        )
    )
    if kind == "missing_role":
        bad_turn: dict[str, object] = {"content": "x"}
    elif kind == "missing_content":
        bad_turn = {"role": "agent"}
    elif kind == "bad_role":
        bad_turn = {"role": draw(st.sampled_from(_INVALID_ROLES)), "content": "x"}
    elif kind == "bootcamper_assertions":
        bad_turn = {
            "role": "bootcamper",
            "content": "x",
            "assertions": [{"type": "exactly_one_pointer"}],
        }
    else:  # unknown_type
        unknown_type = "unknown_" + draw(st.text(alphabet=_ID_ALPHABET, min_size=1, max_size=8))
        bad_turn = {"role": "agent", "content": "x", "assertions": [{"type": unknown_type}]}

    fixture: dict[str, object] = {
        "scenario": scenario_id,
        "description": "desc",
        "turns": [*leading, bad_turn],
    }
    return fixture, scenario_id, bad_index, unknown_type


class TestSchemaRejectionProperty:
    """Property 2: structurally invalid fixtures are rejected with an attributed error.

    A turn missing ``role`` or ``content``, an invalid ``role``, a bootcamper turn
    carrying a non-empty ``assertions`` list, or an unknown assertion ``type`` all
    raise a SchemaError whose message names the scenario id, the offending turn
    index, and (for an unknown type) the unknown type string — and no Scenario is
    returned.

    Validates: Requirements 2.4, 2.7, 4.1, 4.2, 5.5
    """

    @given(st_invalid_fixture())
    @settings(max_examples=20)
    def test_invalid_fixture_raises_attributed_schema_error(
        self, payload: tuple[dict[str, object], str, int, str | None]
    ) -> None:
        """Each invalid-fixture kind raises a SchemaError attributing the violation."""
        fixture, scenario_id, bad_index, unknown_type = payload

        with pytest.raises(SchemaError) as excinfo:
            parse_scenario(fixture, Path("mem.json"))

        message = str(excinfo.value)
        assert scenario_id in message  # names the scenario id
        assert f"turn {bad_index}" in message  # names the offending turn index
        if unknown_type is not None:
            assert unknown_type in message  # names the unknown assertion type (R4.2)


# ===========================================================================
# Example tests: loader behavior + R12.6 negatives
# ===========================================================================


def _valid_fixture_dict(scenario_id: str) -> dict[str, object]:
    """Build a minimal schema-valid fixture dict with the given scenario id."""
    return {
        "scenario": scenario_id,
        "description": f"fixture for {scenario_id}",
        "turns": [
            {"role": "bootcamper", "content": "What is next?"},
            {
                "role": "agent",
                "content": f"{POINTER} Ready to continue?",
                "assertions": [{"type": "exactly_one_pointer"}],
            },
        ],
    }


def _write_fixture(path: Path, scenario_id: str) -> None:
    """Serialize a minimal valid fixture for ``scenario_id`` to ``path`` as JSON."""
    path.write_text(json.dumps(_valid_fixture_dict(scenario_id)), encoding="utf-8")


class TestLoadingBehavior:
    """Example tests for load_scenarios and the R12.6 negative cases.

    Covers loading every fixture in a directory (sorted/deterministic order),
    single-file loading, the empty-directory error, and the two R12.6 negatives:
    an unknown assertion type and a malformed (non-JSON) fixture each cause an
    error (which would exit 1).

    Validates: Requirements 5.1, 5.2, 5.4, 12.6
    """

    def test_load_all_fixtures_in_sorted_order(self, tmp_path: Path) -> None:
        """Loading a directory returns every *.json fixture in sorted path order (R5.1)."""
        # Write deliberately out of alphabetical creation order.
        for stem in ("bravo", "alpha", "charlie"):
            _write_fixture(tmp_path / f"{stem}.json", stem)

        scenarios = load_scenarios(tmp_path)

        assert len(scenarios) == 3
        # sorted(glob("*.json")) -> alpha, bravo, charlie; scenario id matches stem.
        assert [s.scenario for s in scenarios] == ["alpha", "bravo", "charlie"]

    def test_load_single_file(self, tmp_path: Path) -> None:
        """A single fixture path loads exactly that one scenario (R5.2)."""
        _write_fixture(tmp_path / "only.json", "only")
        # A second fixture in the same dir must NOT be loaded when a file is targeted.
        _write_fixture(tmp_path / "other.json", "other")

        scenarios = load_scenarios(tmp_path / "only.json")

        assert len(scenarios) == 1
        assert scenarios[0].scenario == "only"

    def test_empty_directory_raises_empty_dir_error(self, tmp_path: Path) -> None:
        """A directory with no *.json fixtures raises EmptyDirError (R5.4)."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(EmptyDirError) as excinfo:
            load_scenarios(empty_dir)
        assert str(empty_dir) in str(excinfo.value)

    def test_unknown_assertion_type_raises_schema_error(self, tmp_path: Path) -> None:
        """An unregistered assertion type causes a SchemaError / exit-1 error (R12.6)."""
        fixture = _valid_fixture_dict("unknown_type_scn")
        turns = fixture["turns"]
        assert isinstance(turns, list)
        turns[1]["assertions"] = [{"type": "not_a_real_assertion_type"}]
        path = tmp_path / "unknown.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")

        with pytest.raises(SchemaError) as excinfo:
            load_scenarios(path)
        # SchemaError is an EvalError -> the checker reports an error and exits 1.
        assert issubclass(SchemaError, EvalError)
        assert "not_a_real_assertion_type" in str(excinfo.value)

    def test_malformed_json_raises_parse_error_naming_file(self, tmp_path: Path) -> None:
        """A non-JSON fixture raises ParseError naming the file (R12.6, R5.3)."""
        malformed = tmp_path / "broken.json"
        malformed.write_text("{ this is not valid json", encoding="utf-8")

        with pytest.raises(ParseError) as excinfo:
            load_scenarios(malformed)
        # ParseError is an EvalError -> the checker reports an error and exits 1.
        assert issubclass(ParseError, EvalError)
        assert str(malformed) in str(excinfo.value)


# ===========================================================================
# Property tests: evaluation, reporting, and CLI (Properties P11-P14, P16)
# + example tests for the summary and main(argv) entry point (tasks 5.2-5.7)
# ===========================================================================
#
# These exercise the evaluation layer (evaluate_scenario / evaluate_turn /
# count_assertions) and the runner (run / main). To control whether an assertion
# passes or fails deterministically, the scenarios below pin a fixed agent-turn
# content and attach assertions whose pass/fail outcome against that content is
# known in advance:
#
#   * exactly_one_pointer            -> passes (the content holds exactly one 👉)
#   * contains_marker(_CTRL_PRESENT) -> passes (_CTRL_PRESENT is a substring)
#   * absent_marker(_CTRL_ABSENT)    -> passes (_CTRL_ABSENT is not a substring)
#   * contains_marker(_CTRL_ABSENT)  -> FAILS  (required marker is absent)
#   * absent_marker(_CTRL_PRESENT)   -> FAILS  (prohibited marker is present)
#
# Building Scenario objects directly (in memory) is the cleanest way to express
# the evaluation-level properties; the runner/CLI properties round-trip through
# JSON fixtures on disk. The on-disk property tests use tempfile rather than the
# function-scoped `tmp_path` fixture so Hypothesis does not re-use one directory
# across generated examples.

# Fixed agent-turn content with exactly one pointer; "only" is a substring,
# the long sentinel is guaranteed absent.
_CTRL_CONTENT = f"{POINTER} only one question here?"
_CTRL_PRESENT = "only"  # substring present in _CTRL_CONTENT
_CTRL_ABSENT = "ZZZ_absent_marker_sentinel_ZZZ"  # substring NOT present in _CTRL_CONTENT


@st.composite
def st_passing_spec(draw: st.DrawFn) -> AssertionSpec:
    """Build an assertion spec that PASSES against ``_CTRL_CONTENT``."""
    kind = draw(st.sampled_from(["pointer", "contains", "absent"]))
    if kind == "pointer":
        return AssertionSpec("exactly_one_pointer", {})
    if kind == "contains":
        return AssertionSpec("contains_marker", {"marker": _CTRL_PRESENT})
    return AssertionSpec("absent_marker", {"marker": _CTRL_ABSENT})


@st.composite
def st_failing_spec(draw: st.DrawFn) -> AssertionSpec:
    """Build an assertion spec that FAILS against ``_CTRL_CONTENT``."""
    kind = draw(st.sampled_from(["contains", "absent"]))
    if kind == "contains":
        return AssertionSpec("contains_marker", {"marker": _CTRL_ABSENT})
    return AssertionSpec("absent_marker", {"marker": _CTRL_PRESENT})


@st.composite
def st_controlled_scenario(draw: st.DrawFn) -> tuple[Scenario, int, int]:
    """Build a Scenario with a known number of passing and failing assertions.

    Returns the scenario alongside the total assertion count and the failing
    assertion count, so a test can assert that ``count_assertions`` equals the
    total and ``evaluate_scenario`` returns exactly the failing count. Bootcamper
    turns carry no assertions (so they contribute zero to both counts); agent
    turns use the fixed ``_CTRL_CONTENT`` so each attached spec's outcome is known.
    """
    n_turns = draw(st.integers(min_value=1, max_value=4))
    turns: list[Turn] = []
    total = 0
    failing = 0
    for _ in range(n_turns):
        if draw(st.booleans()):
            turns.append(Turn(role="bootcamper", content="What is next?", assertions=[]))
            continue
        n_pass = draw(st.integers(min_value=0, max_value=3))
        n_fail = draw(st.integers(min_value=0, max_value=3))
        specs = [draw(st_passing_spec()) for _ in range(n_pass)]
        specs += [draw(st_failing_spec()) for _ in range(n_fail)]
        total += len(specs)
        failing += n_fail
        turns.append(Turn(role="agent", content=_CTRL_CONTENT, assertions=specs))
    scenario = Scenario(
        scenario="controlled_scn",
        description="mixed passing/failing assertions",
        turns=turns,
        rule_ref=None,
        source=Path("mem.json"),
    )
    return scenario, total, failing


# ---------------------------------------------------------------------------
# Property 11: evaluation completeness (task 5.2)
# ---------------------------------------------------------------------------


class TestEvaluationCompletenessProperty:
    """Property 11: every attached assertion is evaluated exactly once.

    For any valid scenario the number of assertion results equals the total
    number of assertions across all agent turns: ``count_assertions`` equals the
    generated total, and the number of failures returned by ``evaluate_scenario``
    equals the generated failing count (so passes = total - failures). No
    assertion is skipped and none is double-counted.

    Validates: Requirements 6.1, 6.2
    """

    @given(st_controlled_scenario())
    @settings(max_examples=20)
    def test_results_account_for_every_assertion(
        self, payload: tuple[Scenario, int, int]
    ) -> None:
        """Total assertions and failure count match the generated scenario exactly."""
        scenario, total, failing = payload
        failures = evaluate_scenario(scenario)

        assert count_assertions(scenario) == total  # every assertion counted once
        assert len(failures) == failing  # exactly the failing assertions fail
        passes = total - len(failures)
        assert passes == total - failing  # passes + failures == total assertions


# ---------------------------------------------------------------------------
# Property 12: failure attribution (task 5.3)
# ---------------------------------------------------------------------------


@st.composite
def st_failing_typed_spec(draw: st.DrawFn) -> tuple[str, AssertionSpec, str]:
    """Build a guaranteed-failing (type, spec, content) triple.

    Each triple's assertion is certain to fail against its paired content, and
    the first element names the assertion type the resulting EvalFailure must
    carry.
    """
    kind = draw(st.sampled_from(["contains_marker", "absent_marker", "exactly_one_pointer"]))
    if kind == "contains_marker":
        return (
            "contains_marker",
            AssertionSpec("contains_marker", {"marker": _CTRL_ABSENT}),
            _CTRL_CONTENT,
        )
    if kind == "absent_marker":
        return (
            "absent_marker",
            AssertionSpec("absent_marker", {"marker": _CTRL_PRESENT}),
            _CTRL_CONTENT,
        )
    # exactly_one_pointer fails on content with zero pointers.
    return (
        "exactly_one_pointer",
        AssertionSpec("exactly_one_pointer", {}),
        "no pointer in this content",
    )


class TestFailureAttributionProperty:
    """Property 12: a failing assertion is fully and correctly attributed.

    For any guaranteed-failing assertion placed at a known agent-turn index, the
    resulting EvalFailure carries the correct scenario id, the correct turn index,
    the failing assertion type, and a non-empty human-readable message.

    Validates: Requirements 6.3, 6.4
    """

    @given(
        st_scenario_id,
        st.integers(min_value=0, max_value=3),
        st_failing_typed_spec(),
    )
    @settings(max_examples=20)
    def test_failure_carries_correct_attribution(
        self, scenario_id: str, lead: int, typed: tuple[str, AssertionSpec, str]
    ) -> None:
        """The EvalFailure names the scenario, turn index, type, and a message."""
        failing_type, spec, content = typed
        # `lead` bootcamper turns precede the failing agent turn, pinning its index.
        turns = [Turn(role="bootcamper", content="q?", assertions=[]) for _ in range(lead)]
        turns.append(Turn(role="agent", content=content, assertions=[spec]))
        scenario = Scenario(
            scenario=scenario_id,
            description="single guaranteed failure",
            turns=turns,
            rule_ref=None,
            source=Path("mem.json"),
        )

        failures = evaluate_scenario(scenario)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.scenario_id == scenario_id  # R6.3
        assert failure.turn_index == lead  # R6.3
        assert failure.assertion_type == failing_type  # R6.3
        assert failure.message != ""  # R6.4


# ---------------------------------------------------------------------------
# Property 13: exit-code contract (task 5.4)
# ---------------------------------------------------------------------------


@st.composite
def st_eval_fixture(draw: st.DrawFn) -> tuple[dict[str, object], bool]:
    """Build a schema-valid fixture dict and whether it contains a failing assertion.

    Every fixture carries at least two passing assertions; when the failure flag
    is drawn True it also carries one guaranteed-failing assertion, so the
    runner's exit code is fully determined by whether any flag is True.
    """
    scenario_id = draw(st_scenario_id)
    has_failure = draw(st.booleans())
    assertions: list[dict[str, object]] = [
        {"type": "exactly_one_pointer"},
        {"type": "contains_marker", "marker": _CTRL_PRESENT},
    ]
    if has_failure:
        assertions.append({"type": "contains_marker", "marker": _CTRL_ABSENT})  # fails
    fixture: dict[str, object] = {
        "scenario": scenario_id,
        "description": "exit-code fixture",
        "turns": [
            {"role": "bootcamper", "content": "What is next?"},
            {"role": "agent", "content": _CTRL_CONTENT, "assertions": assertions},
        ],
    }
    return fixture, has_failure


def _write_fixtures(directory: Path, fixtures: list[tuple[dict[str, object], bool]]) -> None:
    """Serialize each fixture to ``scn_<i>.json`` in ``directory`` (unique filenames)."""
    for index, (fixture, _) in enumerate(fixtures):
        (directory / f"scn_{index}.json").write_text(json.dumps(fixture), encoding="utf-8")


class TestExitCodeContractProperty:
    """Property 13: the exit code reflects whether any assertion failed.

    For fixtures that load successfully, ``run`` returns 0 if and only if zero
    assertions fail, and returns 1 when at least one assertion fails.

    Validates: Requirements 7.1, 7.2
    """

    @given(st.lists(st_eval_fixture(), min_size=1, max_size=4))
    @settings(max_examples=20)
    def test_exit_zero_iff_no_failure(
        self, fixtures: list[tuple[dict[str, object], bool]]
    ) -> None:
        """run() exits 0 when no assertion fails and 1 when at least one does."""
        expected_failure = any(flag for _, flag in fixtures)
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            _write_fixtures(directory, fixtures)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = run(directory)
        assert code == (1 if expected_failure else 0)


# ---------------------------------------------------------------------------
# Property 14: determinism (task 5.5)
# ---------------------------------------------------------------------------


class TestDeterminismProperty:
    """Property 14: evaluating the same fixtures twice yields identical results.

    For any fixed set of fixtures, evaluating twice produces identical failure
    lists in memory and an identical exit code, summary (stdout), and failure
    report (stderr) through the runner.

    Validates: Requirements 3.10, 8.4
    """

    @given(st_controlled_scenario())
    @settings(max_examples=20)
    def test_evaluate_scenario_is_deterministic(
        self, payload: tuple[Scenario, int, int]
    ) -> None:
        """Two evaluations of the same scenario return equal failure lists."""
        scenario, _total, _failing = payload
        first = evaluate_scenario(scenario)
        second = evaluate_scenario(scenario)
        assert first == second  # EvalFailure is a frozen dataclass -> value equality

    @given(st.lists(st_eval_fixture(), min_size=1, max_size=3))
    @settings(max_examples=20)
    def test_run_is_deterministic(
        self, fixtures: list[tuple[dict[str, object], bool]]
    ) -> None:
        """Two runs over the same fixtures give identical exit code and output."""
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            _write_fixtures(directory, fixtures)

            out_first, err_first = StringIO(), StringIO()
            with redirect_stdout(out_first), redirect_stderr(err_first):
                code_first = run(directory)

            out_second, err_second = StringIO(), StringIO()
            with redirect_stdout(out_second), redirect_stderr(err_second):
                code_second = run(directory)

        assert code_first == code_second
        assert out_first.getvalue() == out_second.getvalue()
        assert err_first.getvalue() == err_second.getvalue()


# ---------------------------------------------------------------------------
# Property 16: malformed fixtures raise a parse error (task 5.6)
# ---------------------------------------------------------------------------

# Known-malformed strings that the stdlib JSON loader cannot parse.
_KNOWN_MALFORMED: list[str] = [
    "{",
    "not json",
    "{,}",
    "[",
    "}",
    "[1, 2,",
    '{"a":}',
    "",
    "   ",
    "{'single': 'quotes'}",
]


def _is_not_json(text: str) -> bool:
    """Return True when ``text`` is NOT parseable by the stdlib JSON loader."""
    try:
        json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return True
    return False


@st.composite
def st_non_json(draw: st.DrawFn) -> str:
    """Build a string that the stdlib JSON loader rejects.

    Half the cases are drawn from a curated malformed list; the rest are
    arbitrary text filtered to only the values that fail ``json.loads`` (so a
    value that happens to be valid JSON — e.g. ``"123"`` — is never produced).
    """
    if draw(st.booleans()):
        return draw(st.sampled_from(_KNOWN_MALFORMED))
    return draw(st.text(max_size=20).filter(_is_not_json))


class TestMalformedFixtureParseErrorProperty:
    """Property 16: non-JSON fixtures raise a ParseError naming the file, exit 1.

    For any non-JSON bytes written to a fixture file, ``load_scenarios`` raises a
    ParseError whose message names the file, and ``run`` on that file returns
    exit code 1.

    Validates: Requirements 5.3, 7.3, 12.6
    """

    @given(st_non_json())
    @settings(max_examples=20)
    def test_non_json_raises_parse_error_and_run_exits_one(self, malformed: str) -> None:
        """A non-JSON fixture file raises an attributed ParseError and run() == 1."""
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "broken.json"
            path.write_text(malformed, encoding="utf-8")

            with pytest.raises(ParseError) as excinfo:
                load_scenarios(path)
            assert str(path) in str(excinfo.value)  # R5.3 — names the file

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = run(path)
            assert code == 1  # R7.3 — parse error -> exit 1


# ---------------------------------------------------------------------------
# Example tests: summary output + main(argv) entry point (task 5.7)
# ---------------------------------------------------------------------------


def _write_eval_fixture(
    path: Path, scenario_id: str, assertions: list[dict[str, object]]
) -> None:
    """Write a minimal valid fixture using ``_CTRL_CONTENT`` for its agent turn."""
    fixture: dict[str, object] = {
        "scenario": scenario_id,
        "description": f"fixture for {scenario_id}",
        "turns": [
            {"role": "bootcamper", "content": "What is next?"},
            {"role": "agent", "content": _CTRL_CONTENT, "assertions": assertions},
        ],
    }
    path.write_text(json.dumps(fixture), encoding="utf-8")


class TestSummaryAndMainEntryPoint:
    """Example tests for the stdout summary, stderr failures, and main(argv).

    Confirms the summary line reports the scenario/assertion/failure counts to
    stdout (R6.5), that a failing fixture prints a FAIL line to stderr, and that
    the argparse ``main`` entry point is invokable with an explicit argv list and
    returns the documented exit codes (R7.4) — without relying on ``sys.argv``.

    Validates: Requirements 6.5, 7.4
    """

    def test_summary_reports_counts_for_passing_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A passing run prints the scenario/assertion/failure summary to stdout."""
        _write_eval_fixture(
            tmp_path / "passing.json",
            "passing_scn",
            [{"type": "exactly_one_pointer"}, {"type": "contains_marker", "marker": _CTRL_PRESENT}],
        )

        code = run(tmp_path)
        captured = capsys.readouterr()

        assert code == 0
        assert "Evaluated 1 scenario(s), 2 assertion(s): 0 failure(s)." in captured.out

    def test_failing_run_prints_fail_line_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A failing run reports the failure on stderr and counts it in the summary."""
        _write_eval_fixture(
            tmp_path / "failing.json",
            "failing_scn",
            [{"type": "contains_marker", "marker": _CTRL_ABSENT}],
        )

        code = run(tmp_path)
        captured = capsys.readouterr()

        assert code == 1
        assert "Evaluated 1 scenario(s), 1 assertion(s): 1 failure(s)." in captured.out
        assert "FAIL [failing_scn]" in captured.err  # R6.3 attribution on stderr
        assert "contains_marker" in captured.err

    def test_main_returns_zero_for_passing_file(self, tmp_path: Path) -> None:
        """main([file]) returns 0 for a fixture whose assertions all pass (R7.4)."""
        passing = tmp_path / "passing.json"
        _write_eval_fixture(passing, "passing_scn", [{"type": "exactly_one_pointer"}])

        assert main([str(passing)]) == 0

    def test_main_returns_one_for_failing_file(self, tmp_path: Path) -> None:
        """main([file]) returns 1 for a fixture with a failing assertion (R7.4)."""
        failing = tmp_path / "failing.json"
        _write_eval_fixture(
            failing, "failing_scn", [{"type": "contains_marker", "marker": _CTRL_ABSENT}]
        )

        assert main([str(failing)]) == 1

    def test_main_with_fixtures_dir_option(self, tmp_path: Path) -> None:
        """main(['--fixtures-dir', dir]) evaluates the directory and returns 0 (R7.4, R5.1)."""
        _write_eval_fixture(
            tmp_path / "passing.json", "passing_scn", [{"type": "exactly_one_pointer"}]
        )

        assert main(["--fixtures-dir", str(tmp_path)]) == 0


# ===========================================================================
# Property tests: shipped-fixture oracle + fixture safety (Properties P15, P17)
# + the stdlib-only import audit (tasks 8.2-8.4)
# ===========================================================================
#
# These tasks operate on the four shipped starter fixtures and on the checker
# source itself rather than on synthesized inputs:
#
#   * P15 (8.2) — every shipped fixture's assertions pass and a full run exits 0
#                 (self-consistency oracle).
#   * P17 (8.3) — no shipped fixture leaks an MCP server URL or a secret/PII pattern.
#   * 8.4       — the checker imports only standard-library modules and contains no
#                 network/LLM/MCP call indicators.
#
# The Eval_Directory and its fixtures are resolved robustly relative to this test
# file so the tests pass regardless of the current working directory.

# The shipped Eval_Directory and its four starter fixtures (R1.5, R11.3).
_EVAL_DIR = Path(__file__).resolve().parent / "eval"
_SHIPPED_FIXTURES = sorted(_EVAL_DIR.glob("*.json"))

# The checker source under audit, resolved relative to this test file (R11.3).
_CHECKER_SOURCE = Path(__file__).resolve().parent.parent / "scripts" / "eval_conversations.py"

# The MCP server URL is assembled from fragments rather than written as a literal
# so this test file does not itself embed the exact MCP-URL token it forbids
# (mcp.json is the single source of truth for that URL). The assembled runtime
# value is byte-for-byte the host named in design Property 17 / task 8.3.
_MCP_URL = ".".join(("mcp", "senzing", "com"))


# ---------------------------------------------------------------------------
# Property 15: shipped fixtures pass (self-consistency oracle) — task 8.2
# ---------------------------------------------------------------------------


class TestShippedFixturesPassProperty:
    """Property 15: every shipped starter fixture passes and a full run exits 0.

    The starter fixtures encode the EXPECTED agent behavior as the oracle (R10.6);
    the harness is only trustworthy if that oracle is self-consistent. For each
    shipped fixture, loading and evaluating it yields zero failures, and a full
    run over the whole Eval_Directory exits with code 0 (R10.5, R12.1).

    Validates: Requirements 10.5, 10.6, 12.1
    """

    def test_starter_set_is_present(self) -> None:
        """The shipped starter set is non-empty (the four fixtures of R10.1-R10.4)."""
        assert _SHIPPED_FIXTURES, f"no shipped fixtures found under {_EVAL_DIR}"
        assert len(_SHIPPED_FIXTURES) == 4  # R10.1-R10.4 ship exactly four fixtures

    @given(st.sampled_from(_SHIPPED_FIXTURES))
    @settings(max_examples=20)
    def test_each_shipped_fixture_has_zero_failures(self, fixture_path: Path) -> None:
        """Every assertion in each shipped fixture passes (zero EvalFailures) (R10.5)."""
        scenarios = load_scenarios(fixture_path)
        assert scenarios  # the fixture parsed into at least one scenario
        failures: list[EvalFailure] = []
        for scenario in scenarios:
            failures.extend(evaluate_scenario(scenario))
        assert failures == [], f"{fixture_path.name} produced failures: {failures}"

    def test_full_starter_run_exits_zero(self) -> None:
        """A full run over the shipped Eval_Directory exits 0 (R10.5, R12.1)."""
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = run(_EVAL_DIR)
        assert code == 0


# ---------------------------------------------------------------------------
# Property 17: fixtures contain no MCP URL or secrets — task 8.3
# ---------------------------------------------------------------------------

# Forbidden substrings that must never appear in a shipped fixture: the MCP
# server URL, any URL scheme, and common secret / credential / PII markers
# (R11.4). Matching is case-insensitive (the fixture text is lower-cased before
# comparison) so a capitalized variant cannot slip through. These are denylist
# needles, not real credentials.
_FORBIDDEN_FIXTURE_PATTERNS: list[str] = [
    _MCP_URL,
    "http://",
    "https://",
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "begin private key",
    "akia",
]


class TestNoMcpUrlOrSecretsProperty:
    """Property 17: shipped fixtures contain no MCP server URL or secret/PII pattern.

    Everything under the Eval_Directory ships with the power (security.md), so a
    fixture must never embed the MCP server URL, any URL scheme, or a
    secret/credential/PII marker. The shipped fixtures are known-clean, so every
    forbidden pattern is absent.

    Validates: Requirements 11.4
    """

    def test_starter_set_is_present(self) -> None:
        """The shipped starter set is non-empty so the property has something to check."""
        assert _SHIPPED_FIXTURES, f"no shipped fixtures found under {_EVAL_DIR}"

    @given(st.sampled_from(_SHIPPED_FIXTURES))
    @settings(max_examples=20)
    def test_fixture_text_has_no_forbidden_pattern(self, fixture_path: Path) -> None:
        """No forbidden URL/secret/PII pattern appears in the raw fixture text (R11.4)."""
        raw = fixture_path.read_text(encoding="utf-8").lower()
        present = [pattern for pattern in _FORBIDDEN_FIXTURE_PATTERNS if pattern in raw]
        assert present == [], f"{fixture_path.name} contains forbidden pattern(s): {present}"


# ---------------------------------------------------------------------------
# Example test: stdlib-only import audit — task 8.4
# ---------------------------------------------------------------------------

# Network / LLM / MCP call indicators that must never appear in the checker
# source. Their absence is evidence the checker performs no network/LLM/MCP call
# during evaluation (R8.1, R8.2). Tokens are chosen to be precise so legitimate
# checker prose does not trip them (the singular word "request" is intentionally
# not in this list).
_NETWORK_INDICATORS: list[str] = [
    "urllib",
    "requests",
    "http://",
    "https://",
    "socket",
    _MCP_URL,
    "subprocess",
]


def _top_level_imports(source: str) -> set[str]:
    """Collect the top-level module names imported by ``source`` via AST.

    Walks every ``import`` and ``from ... import`` statement, recording the first
    dotted component of each imported module name. ``from __future__`` statements
    are skipped (they are compiler directives, not runtime modules).

    Args:
        source: The Python source text to parse.

    Returns:
        The set of top-level module names the source imports (``__future__``
        excluded).
    """
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module is None or node.module == "__future__":
                continue
            modules.add(node.module.split(".")[0])
    return modules


class TestStdlibOnlyImportAudit:
    """The checker imports only the standard library and makes no network/MCP call.

    Parses the checker source and asserts every imported top-level module is a
    standard-library module (R11.1), then scans the raw source for network / LLM /
    MCP call indicators and asserts none are present (R8.1, R8.2). This proves the
    harness is offline and dependency-free, not merely documented as such.

    Validates: Requirements 8.1, 8.2, 11.1
    """

    def test_checker_source_exists(self) -> None:
        """The checker source under audit is present at the expected location."""
        assert _CHECKER_SOURCE.is_file(), f"checker source not found at {_CHECKER_SOURCE}"

    def test_all_imports_are_stdlib(self) -> None:
        """Every top-level import resolves to a standard-library module (R11.1)."""
        source = _CHECKER_SOURCE.read_text(encoding="utf-8")
        imported = _top_level_imports(source)
        # The checker's expected stdlib imports (excluding the skipped __future__).
        expected = {
            "argparse",
            "collections",
            "json",
            "re",
            "sys",
            "dataclasses",
            "pathlib",
            "typing",
        }
        assert expected <= imported, f"missing expected imports: {expected - imported}"
        non_stdlib = {name for name in imported if name not in sys.stdlib_module_names}
        assert non_stdlib == set(), f"non-stdlib import(s) detected: {non_stdlib}"

    def test_source_has_no_network_or_mcp_indicators(self) -> None:
        """The checker source contains no network / LLM / MCP call indicator (R8.1, R8.2)."""
        source = _CHECKER_SOURCE.read_text(encoding="utf-8")
        present = [token for token in _NETWORK_INDICATORS if token in source]
        assert present == [], f"network/MCP indicator(s) present in checker source: {present}"
