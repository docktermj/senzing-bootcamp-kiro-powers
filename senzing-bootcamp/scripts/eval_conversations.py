#!/usr/bin/env python3
"""Conversational-eval harness: evaluate recorded transcripts against behavioral rules.

The Senzing Bootcamp Power has ~2,600 tests, but nearly all of them parse steering
markdown and assert that strings or markers are PRESENT — they verify the steering
SAYS a rule. They do NOT prove that an agent FOLLOWING the steering actually behaves
correctly at runtime.

This checker adds the missing layer. Maintainers author scripted transcripts (fixtures)
of an agent / bootcamper exchange. Each agent turn carries declarative behavioral
assertions describing the moves the agent must make at decision points (👉 questions,
⛔ gates, module transitions, licensing branches). This checker loads those fixtures and
evaluates the assertions against the recorded agent-turn text — it verifies that a
recorded conversation HONORS the rule.

The distinction is the whole point of this harness:
    * String-presence tests verify the steering SAYS the rule.
    * This harness verifies that a recorded conversation HONORS the rule.

The harness is OFFLINE and DETERMINISTIC. It never calls an LLM or the Senzing MCP
server. It only evaluates recorded, version-controlled fixtures. Generating fresh
transcripts from a live model is out of scope for the automated suite; manual transcript
authoring produces a fixture that is committed and then evaluated here.

Usage:
    # Evaluate every fixture in the default Eval_Directory (senzing-bootcamp/tests/eval)
    python senzing-bootcamp/scripts/eval_conversations.py

    # Evaluate every fixture in a specific directory
    python senzing-bootcamp/scripts/eval_conversations.py --fixtures-dir path/to/eval

    # Evaluate a single fixture file
    python senzing-bootcamp/scripts/eval_conversations.py path/to/scenario.json

Exit codes:
    0 — All behavioral assertions across all evaluated fixtures passed.
    1 — One or more assertions failed, or a parse/schema error occurred.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssertionSpec:
    """One declarative behavioral assertion attached to an agent turn.

    Attributes:
        type: Assertion_Type name resolved against the registry (R2.5).
        params: Named parameters for the assertion, e.g. {"marker": "..."} (R2.6).
    """

    type: str
    params: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Turn:
    """A single transcript entry.

    Attributes:
        role: "agent" or "bootcamper" (R2.1).
        content: The textual content of the turn (R2.2).
        assertions: Behavioral assertions; empty for bootcamper turns (R2.3, R2.4).
    """

    role: str
    content: str
    assertions: list[AssertionSpec] = field(default_factory=list)


@dataclass(frozen=True)
class Scenario:
    """One conversational scenario loaded from a fixture file.

    Attributes:
        scenario: Non-empty scenario identifier (R1.2).
        description: Human-readable description of the rule exercised (R1.3).
        turns: Ordered list of one or more turns (R1.4).
        rule_ref: Governing rule / steering source referenced, if any (R1.6).
        source: Originating fixture file, used for error messages.
    """

    scenario: str
    description: str
    turns: list[Turn]
    rule_ref: str | None
    source: Path


@dataclass(frozen=True)
class AssertionOutcome:
    """Result of evaluating one predicate.

    Attributes:
        passed: True if the assertion held against the turn.
        message: Empty string on pass; a specific human-readable reason on fail (R6.4).
    """

    passed: bool
    message: str


@dataclass(frozen=True)
class EvalFailure:
    """A failed assertion, fully attributed for the Failure_Report (R6.3).

    Attributes:
        scenario_id: The scenario identifier the failure belongs to.
        turn_index: The index of the offending turn within the transcript.
        assertion_type: The Assertion_Type that failed.
        message: Human-readable reason the assertion failed (R6.4).
    """

    scenario_id: str
    turn_index: int
    assertion_type: str
    message: str


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class EvalError(Exception):
    """Base class for fixture-validity / parse errors (exit 1)."""


class ParseError(EvalError):
    """A fixture file could not be parsed by the stdlib JSON loader (R5.3)."""


class EmptyDirError(EvalError):
    """The Eval_Directory contained no fixtures (R5.4)."""


class SchemaError(EvalError):
    """A fixture violated the R1/R2 structure or named an unknown type (R2.4, R2.7, R4.2)."""


# ---------------------------------------------------------------------------
# Detection heuristics (pure helpers)
# ---------------------------------------------------------------------------
#
# These mirror the vocabulary already proven in validate_behavior_rules.py and
# test_self_answering_questions_bug.py, re-expressed for free-form transcript
# text. They are module-level constants + pure functions so the test layer can
# property-test each in isolation. Every function below is a pure function of
# its inputs — no randomness, clock, filesystem, or network access (R3.10, R8.4).

POINTER = "\U0001f449"  # 👉 — the pointer marker prefixing every input-requiring prompt
HARD_STOP = re.compile(r"\U0001f6d1\s*STOP", re.IGNORECASE)  # 🛑 STOP — hard-stop marker

# Lineage (R9.3): CONJUNCTION_PATTERNS is COPIED VERBATIM from
# validate_behavior_rules.CONJUNCTION_PATTERNS — it is intentionally NOT imported.
# Requirement 9.3 forbids relocating, duplicating, or modifying the enforcement
# logic in existing scripts; the harness instead re-implements the same regex
# vocabulary for a DIFFERENT input domain (free-form transcript text rather than
# steering markdown) so the two verification layers stay independently testable.
# If the steering-file vocabulary changes, this copy is updated deliberately to
# keep the layers in sync without coupling them.
CONJUNCTION_PATTERNS: list[str] = [
    r"\bor\b(?!\s*$)",           # "or" not at end of line
    r"\balternatively\b",
    r"\bor would you rather\b",
    r"\bor should we\b",
    r"\bor would you prefer\b",
    r"\bor if you prefer\b",
]


def count_pointers(text: str) -> int:
    """Count occurrences of the pointer marker in text.

    Args:
        text: The agent-turn text to inspect.

    Returns:
        The number of POINTER (👉) occurrences in the text.
    """
    return text.count(POINTER)


def pointer_question_line(text: str) -> str | None:
    """Return the first line that contains both the pointer and a question mark.

    A pointer question line is the structural unit a turn must "STOP" after — a
    line carrying the 👉 marker and a "?". The line is returned verbatim (as it
    appears in the text) so that callers can locate it again, e.g. via text_after.

    Args:
        text: The agent-turn text to scan, split on line boundaries.

    Returns:
        The first line containing both the pointer (👉) and a "?", or None if no
        such line exists.
    """
    for line in text.splitlines():
        if POINTER in line and "?" in line:
            return line
    return None


def has_conjunction(text: str) -> bool:
    """Detect whether text contains a prose conjunction joining alternatives.

    Performs case-insensitive matching against CONJUNCTION_PATTERNS, the regex
    vocabulary copied from validate_behavior_rules (lineage documented above).

    Args:
        text: The agent-turn text to inspect.

    Returns:
        True if any CONJUNCTION_PATTERNS regex matches the text.
    """
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in CONJUNCTION_PATTERNS)


def count_question_marks(text: str) -> int:
    """Count the number of question marks in text.

    Args:
        text: The agent-turn text to inspect.

    Returns:
        The number of "?" characters in the text.
    """
    return text.count("?")


def text_after(text: str, marker_line: str) -> str:
    """Return the substantive content appearing after a marker line within text.

    Locates the first occurrence of marker_line in text and returns everything
    that follows it, with surrounding whitespace stripped. Used by predicates to
    inspect whether substantive agent content continues past a boundary (for
    example, past a pointer question line in ends_with_question_then_stop).

    Args:
        text: The full agent-turn text.
        marker_line: The line (or substring) to search for; typically the value
            returned by pointer_question_line.

    Returns:
        The text following the first occurrence of marker_line, stripped of
        leading and trailing whitespace. Returns an empty string if marker_line
        is empty or is not found in text.
    """
    if not marker_line:
        return ""
    index = text.find(marker_line)
    if index == -1:
        return ""
    return text[index + len(marker_line):].strip()


# ---------------------------------------------------------------------------
# Evaluation context + predicate type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvalContext:
    """The surrounding transcript exposed to a predicate during evaluation.

    Predicates receive a uniform ``(turn, ctx, params)`` signature so the
    registry can call them identically. Most predicates only inspect ``turn``;
    context-aware predicates (for example ``gate_not_bypassed``) may consult the
    prior and later turns of the same scenario through this context.

    Attributes:
        turns: The full ordered list of turns for the scenario being evaluated.
        index: The index of the current turn within ``turns``.
        scenario_id: The identifier of the scenario being evaluated, threaded
            through so :func:`evaluate_turn` can attribute each EvalFailure to its
            scenario (R6.3). Defaults to "" so a context can still be constructed
            for an isolated predicate check (for example in unit tests) without a
            scenario.
    """

    turns: list[Turn]
    index: int
    scenario_id: str = ""

    @property
    def current_turn(self) -> Turn:
        """Return the turn currently being evaluated."""
        return self.turns[self.index]

    @property
    def prior_turns(self) -> list[Turn]:
        """Return the turns that precede the current turn, in order."""
        return self.turns[: self.index]

    @property
    def later_turns(self) -> list[Turn]:
        """Return the turns that follow the current turn, in order."""
        return self.turns[self.index + 1 :]


# A predicate evaluates one assertion against a turn and its surrounding context.
# Keeping the signature uniform lets the registry (task 2.2) dispatch every
# assertion type identically.
Predicate = Callable[[Turn, EvalContext, dict[str, object]], AssertionOutcome]


# ---------------------------------------------------------------------------
# Predicate-internal helpers
# ---------------------------------------------------------------------------


def _last_pointer_line_index(lines: list[str]) -> int | None:
    """Return the index of the last line carrying the pointer marker.

    A 👉-prefixed line is the input-requiring *prompt* the agent must STOP after.
    In the bootcamp a pointer prompt is treated as the turn's question even when
    it is phrased as an imperative without a literal "?" (for example
    "👉 Take your time exploring the visualization."), so this locates any line
    containing the pointer rather than requiring a question mark.

    Args:
        lines: The agent-turn text split on line boundaries.

    Returns:
        The index of the last line containing the pointer (👉), or None if no
        line contains the pointer.
    """
    found: int | None = None
    for i, line in enumerate(lines):
        if POINTER in line:
            found = i
    return found


def _is_boundary_line(line: str) -> bool:
    """Return True if a line is a hard-stop / "end your response" boundary.

    The hard-stop directive (🛑 STOP) and the "end your response" instruction are
    treated as the boundary that closes a turn after a pointer question — not as
    substantive content and not as a self-answer (R3.2, R3.4).

    Args:
        line: A single line of agent-turn text.

    Returns:
        True if the line is a hard-stop or "end your response" boundary line.
    """
    return HARD_STOP.search(line) is not None or "end your response" in line.lower()


# ---------------------------------------------------------------------------
# Marker vocabularies for the structural predicates
# ---------------------------------------------------------------------------
#
# These phrase lists are the documented marker conventions the shipped starter
# fixtures (task 7) are authored to satisfy. They describe the EXPECTED agent
# behavior; a behavioral regression that drops a marker (or adds a bypass offer)
# flips the corresponding predicate to failing.

# transition_response_completeness (R3.8) — the four required transition elements.
# A module transition turn must contain all four of these plus length > 50.
#   * module banner  — a box-drawing banner ("━") OR a "MODULE <n>" heading OR 🚀
#   * journey map     — a 🗺 marker, the word "journey", OR a module-status table
#                       row whose header carries both "Module" and "Status"
#   * before/after    — both the words "before" and "after" appear (e.g. "Before:"/"After:")
#   * first step      — a "Step 1" heading OR the phrase "first step"
_BANNER_RE = re.compile(r"MODULE\s+\d+", re.IGNORECASE)
_JOURNEY_TABLE_RE = re.compile(r"\|\s*Module\b.*\bStatus\b", re.IGNORECASE)
_BEFORE_RE = re.compile(r"\bbefore\b", re.IGNORECASE)
_AFTER_RE = re.compile(r"\bafter\b", re.IGNORECASE)
_FIRST_STEP_RE = re.compile(r"\bStep\s+1\b", re.IGNORECASE)

# gate_not_bypassed (R3.9) — evidence the mandatory gate actually ran. At least
# one of these (or the 🛑 STOP hard-stop boundary) must be present for the gate
# to count as executed.
GATE_EXECUTION_MARKERS: list[str] = [
    "checkpoint written",          # "Checkpoint written: module_3_verification..."
    "module_3_verification",       # the gate's verification checkpoint reference
    "visualization is running",    # the "Your visualization is running" delivery line
]

# gate_not_bypassed (R3.9) — skip/bypass language framed as an offer for the gate.
# Presence of any of these means the gate was offered as skippable -> fail.
GATE_BYPASS_PATTERNS: list[str] = [
    r"\bskip\b",                   # "skip", "skip Phase 2", "you can skip ..."
    r"\bbypass\b",                 # "bypass the visualization"
    r"move on to module",          # "move on to Module 4" before the gate completes
    r"move past",                  # "move past the visualization"
]

# no_compound_question (R3.3) — DISTINCTIVE compound-question conjunctions.
#
# This is CONJUNCTION_PATTERNS minus the bare ``\bor\b`` entry, used deliberately.
# R3.3 / Property 5 scope the rule to a conjunction joining two *question
# alternatives*; a bare "or" joining two nouns inside a single question (for
# example the shipped oracle "How many distinct data sources or systems...") is
# NOT a compound question and the shipped fixture must pass (R10.5). The bare
# ``\bor\b`` pattern cannot distinguish "Python or Java" (a single choice) from a
# genuine two-question compound, so it is excluded here; the remaining multi-word
# lead-ins ("or would you rather", "or should we", ...) and "alternatively"
# unambiguously introduce a second alternative clause. A genuine two-question
# compound that uses only a bare "or" still fails via the >1 question-mark check.
COMPOUND_CONJUNCTION_PATTERNS: list[str] = [
    pattern for pattern in CONJUNCTION_PATTERNS if pattern != r"\bor\b(?!\s*$)"
]


# ---------------------------------------------------------------------------
# Assertion predicates (Requirement 3)
# ---------------------------------------------------------------------------
#
# Each predicate has the uniform signature (turn, ctx, params) -> AssertionOutcome
# so the registry (task 2.2) can dispatch them identically. Every predicate is a
# pure function of its inputs (R3.10, R8.4): no randomness, clock, filesystem, or
# network access. On pass the message is ""; on fail it is a specific,
# human-readable reason (R6.4).


def _exactly_one_pointer(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the agent turn contains exactly one pointer marker (R3.1).

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters (unused).

    Returns:
        Passing outcome when the pointer count is exactly one; otherwise a
        failing outcome naming the count found.
    """
    count = count_pointers(turn.content)
    if count == 1:
        return AssertionOutcome(True, "")
    return AssertionOutcome(False, f"expected exactly one pointer, found {count}")


def _ends_with_question_then_stop(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when a pointer prompt ends the turn with nothing substantive after it (R3.2).

    Encodes the "STOP after a 👉 prompt and wait" rule. The pointer-prefixed line
    is the input-requiring prompt the turn must end on (it may be phrased as an
    imperative without a literal "?", e.g. "👉 Take your time exploring."). After
    that line, only whitespace, blank lines, and the hard-stop / "end your
    response" boundary block may appear. Any other prose — including a simulated
    bootcamper reply within the same turn — means the agent continued past its own
    prompt and fails the check.

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters (unused).

    Returns:
        Passing outcome when the turn ends on the pointer prompt; otherwise a
        failing outcome describing what substantive content followed it.
    """
    lines = turn.content.splitlines()
    idx = _last_pointer_line_index(lines)
    if idx is None:
        return AssertionOutcome(False, "no pointer question found in turn")
    trailing = [ln.strip() for ln in lines[idx + 1 :] if ln.strip()]
    substantive = [ln for ln in trailing if not _is_boundary_line(ln)]
    if substantive:
        snippet = substantive[0]
        return AssertionOutcome(
            False, f"substantive agent content follows the pointer question: {snippet!r}"
        )
    return AssertionOutcome(True, "")


def _no_compound_question(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the turn poses at most one, non-compound question (R3.3).

    Fails when the content has more than one question mark (two explicit
    questions) or when a DISTINCTIVE compound-question conjunction joins
    alternatives (for example "or would you rather", "or should we",
    "alternatively"). Uses COMPOUND_CONJUNCTION_PATTERNS — CONJUNCTION_PATTERNS
    without the bare ``\\bor\\b`` entry — because a bare "or" joining two nouns in
    a single question ("data sources or systems") is not a compound question; a
    genuine two-question compound is still caught by the question-mark count.
    Mirrors the compound-question vocabulary proven in
    validate_behavior_rules.is_compound_question (lineage documented at
    CONJUNCTION_PATTERNS).

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters (unused).

    Returns:
        Passing outcome for a single, simple question; otherwise a failing
        outcome describing the compound structure detected.
    """
    content = turn.content
    marks = count_question_marks(content)
    if marks > 1:
        return AssertionOutcome(
            False, f"compound question detected (multiple question marks: found {marks})"
        )
    for line in content.splitlines():
        if any(re.search(pat, line, re.IGNORECASE) for pat in COMPOUND_CONJUNCTION_PATTERNS):
            return AssertionOutcome(
                False,
                f"compound question detected (conjunction joins alternatives): {line.strip()!r}",
            )
    return AssertionOutcome(True, "")


def _no_self_answer(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the agent does not answer its own pointer question (R3.4).

    Mirrors the self-answering anti-pattern from conversation-protocol.md (asking
    "Who will be working on this project?" then writing "I'll assume it's just you
    for now."). After the pointer question line, a declarative agent sentence that
    is neither another pointer prompt nor the hard-stop / "end your response"
    boundary means the agent answered itself and fails. The hard-stop directive is
    treated as a boundary, not a self-answer, matching the steering's CORRECT
    example.

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters (unused).

    Returns:
        Passing outcome when nothing answers the question; otherwise a failing
        outcome quoting the self-answer.
    """
    lines = turn.content.splitlines()
    idx = _last_pointer_line_index(lines)
    if idx is None:
        return AssertionOutcome(True, "")
    for line in lines[idx + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if _is_boundary_line(stripped):
            continue
        if POINTER in stripped:
            continue
        return AssertionOutcome(False, f"agent appears to answer its own question: {stripped!r}")
    return AssertionOutcome(True, "")


def _contains_marker(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the turn content contains the required marker string (R3.5).

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters; requires "marker".

    Returns:
        Passing outcome when the marker is a substring of the content; otherwise a
        failing outcome naming the expected marker.
    """
    marker = str(params.get("marker", ""))
    if marker in turn.content:
        return AssertionOutcome(True, "")
    return AssertionOutcome(False, f"expected marker {marker!r} not found in turn")


def _absent_marker(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the turn content does NOT contain the prohibited marker (R3.6).

    The exact logical complement of :func:`_contains_marker` for the same inputs.

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters; requires "marker".

    Returns:
        Passing outcome when the marker is absent; otherwise a failing outcome
        naming the prohibited marker.
    """
    marker = str(params.get("marker", ""))
    if marker not in turn.content:
        return AssertionOutcome(True, "")
    return AssertionOutcome(False, f"prohibited marker {marker!r} present in turn")


def _mentions_tool(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when the turn names the required tool as a token (R3.7).

    Uses a word-boundary match so "search_docs" matches in "calling search_docs("
    but a substring inside a larger identifier does not spuriously match.

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters; requires "tool".

    Returns:
        Passing outcome when the tool name occurs as a token; otherwise a failing
        outcome naming the expected tool.
    """
    tool = str(params.get("tool", ""))
    if tool and re.search(rf"\b{re.escape(tool)}\b", turn.content):
        return AssertionOutcome(True, "")
    return AssertionOutcome(False, f"expected tool {tool!r} not mentioned in turn")


def _transition_response_completeness(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when a module-transition turn is a full module start, not a bare ack (R3.8).

    Requires all four transition elements AND length > 50 characters. The marker
    conventions (documented so task 7.3's fixture can satisfy them) are:

        * module banner — a box-drawing banner ("━"), a "MODULE <n>" heading, or 🚀.
        * journey map   — a 🗺 marker, the word "journey", or a module-status table
                          row whose header carries both "Module" and "Status".
        * before/after  — both the words "before" and "after" appear
                          (e.g. "Before:" / "After:").
        * first step    — a "Step 1" heading or the phrase "first step".

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (unused).
        params: Assertion parameters (unused).

    Returns:
        Passing outcome when all four markers are present and length > 50;
        otherwise a failing outcome listing the missing markers and the length.
    """
    content = turn.content
    lower = content.lower()
    has_banner = "━" in content or "🚀" in content or _BANNER_RE.search(content) is not None
    has_journey = (
        "🗺" in content or "journey" in lower or _JOURNEY_TABLE_RE.search(content) is not None
    )
    has_before_after = (
        _BEFORE_RE.search(content) is not None and _AFTER_RE.search(content) is not None
    )
    has_first_step = _FIRST_STEP_RE.search(content) is not None or "first step" in lower

    missing: list[str] = []
    if not has_banner:
        missing.append("module banner")
    if not has_journey:
        missing.append("journey map")
    if not has_before_after:
        missing.append("before/after framing")
    if not has_first_step:
        missing.append("first step")

    length = len(content)
    if missing or length <= 50:
        return AssertionOutcome(
            False, f"transition incomplete: missing {missing}; length={length}"
        )
    return AssertionOutcome(True, "")


def _gate_not_bypassed(
    turn: Turn, ctx: EvalContext, params: dict[str, object]
) -> AssertionOutcome:
    """Pass when a mandatory gate is shown executed and is not offered as skippable (R3.9).

    Context-aware in signature; detection operates on the gate turn's text. Both
    conditions must hold:

        * Executed evidence — at least one of GATE_EXECUTION_MARKERS
          ("checkpoint written", "module_3_verification", "visualization is
          running") OR the 🛑 STOP hard-stop boundary is present.
        * No bypass offer — none of GATE_BYPASS_PATTERNS (the words "skip" or
          "bypass", "move on to module", "move past") appears, since those frame
          the gate as skippable.

    Args:
        turn: The agent turn being evaluated.
        ctx: Surrounding-transcript context (available for cross-turn checks).
        params: Assertion parameters; requires "step" (e.g. "3.9").

    Returns:
        Passing outcome when the gate ran with no bypass offer; otherwise a
        failing outcome naming the step and the reason.
    """
    step = str(params.get("step", ""))
    content = turn.content
    lower = content.lower()
    executed = HARD_STOP.search(content) is not None or any(
        marker in lower for marker in GATE_EXECUTION_MARKERS
    )
    bypassed = any(
        re.search(pattern, content, re.IGNORECASE) for pattern in GATE_BYPASS_PATTERNS
    )
    if not executed:
        return AssertionOutcome(
            False, f"gate {step} not shown as executed (no execution marker or checkpoint present)"
        )
    if bypassed:
        return AssertionOutcome(False, f"gate {step} bypassed: skip/bypass offer present")
    return AssertionOutcome(True, "")


# ---------------------------------------------------------------------------
# Assertion registry (Requirement 4)
# ---------------------------------------------------------------------------
#
# The registry is the single extension point for the assertion vocabulary
# (R4.1, R4.3): adding a new Assertion_Type means writing a predicate function
# and adding ONE entry below (plus one REQUIRED_PARAMS entry if the type takes a
# parameter) — no existing predicate's evaluation is touched. Unknown types are
# rejected at validation time by resolve() (R4.2).
#
# Supported Assertion_Types — name, purpose, and required parameters (R4.4):
#
#   exactly_one_pointer
#       Purpose: pass when the agent turn contains exactly one pointer (👉).
#       Params:  none.
#   ends_with_question_then_stop
#       Purpose: pass when a pointer prompt ends the turn with nothing
#                substantive (only whitespace / a hard-stop boundary) after it.
#       Params:  none.
#   no_compound_question
#       Purpose: pass when the turn poses at most one, non-compound question
#                (no extra "?" and no conjunction joining alternatives).
#       Params:  none.
#   no_self_answer
#       Purpose: pass when the agent does not answer its own pointer question
#                within the same turn.
#       Params:  none.
#   contains_marker
#       Purpose: pass when the turn content contains a required marker string.
#       Params:  marker (str) — the substring that must be present.
#   absent_marker
#       Purpose: pass when the turn content does NOT contain a prohibited marker.
#       Params:  marker (str) — the substring that must be absent.
#   mentions_tool
#       Purpose: pass when the turn names a required tool as a token.
#       Params:  tool (str) — the tool name to match on a word boundary.
#   transition_response_completeness
#       Purpose: pass when a module-transition turn is a full module start
#                (banner + journey map + before/after + first step, length > 50).
#       Params:  none.
#   gate_not_bypassed
#       Purpose: pass when a mandatory gate is shown executed and is not offered
#                as skippable.
#       Params:  step (str) — the gate step identifier, e.g. "3.9".

REGISTRY: dict[str, Predicate] = {
    "exactly_one_pointer": _exactly_one_pointer,
    "ends_with_question_then_stop": _ends_with_question_then_stop,
    "no_compound_question": _no_compound_question,
    "no_self_answer": _no_self_answer,
    "contains_marker": _contains_marker,
    "absent_marker": _absent_marker,
    "mentions_tool": _mentions_tool,
    "transition_response_completeness": _transition_response_completeness,
    "gate_not_bypassed": _gate_not_bypassed,
}

# Required named parameters per parameterized Assertion_Type (R2.6). Types not
# listed here take no parameters. The loader (task 4.1) uses this map to reject a
# fixture that omits a required parameter with a SchemaError during validation.
REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "contains_marker": ("marker",),
    "absent_marker": ("marker",),
    "mentions_tool": ("tool",),
    "gate_not_bypassed": ("step",),
}


def resolve(
    type_name: str,
    scenario_id: str | None = None,
    turn_index: int | None = None,
) -> Predicate:
    """Resolve an Assertion_Type name to its predicate, or raise SchemaError (R4.1, R4.2).

    Looks ``type_name`` up in :data:`REGISTRY`. On a miss, raises a
    :class:`SchemaError` whose message names the scenario, the offending turn
    index, and the unknown type so the loader (task 4.1) can attribute the error
    precisely (R4.2). ``scenario_id`` and ``turn_index`` are accepted as optional
    attribution context; the loader passes them when validating a fixture, while
    callers that only need a lookup (for example tests) may omit them.

    Args:
        type_name: The Assertion_Type name to resolve against the registry.
        scenario_id: The scenario identifier the assertion belongs to, used only
            for error attribution. None when no scenario context is available.
        turn_index: The index of the turn carrying the assertion, used only for
            error attribution. None when no turn context is available.

    Returns:
        The predicate registered under ``type_name``.

    Raises:
        SchemaError: When ``type_name`` is not present in the registry; the
            message names the scenario, the turn index, and the unknown type.
    """
    predicate = REGISTRY.get(type_name)
    if predicate is None:
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: unknown assertion type {type_name!r}"
        )
    return predicate


# ---------------------------------------------------------------------------
# Loading and validation (Requirements 2, 5)
# ---------------------------------------------------------------------------
#
# Loading happens in two stages, and validation always runs BEFORE any
# evaluation (R5.5): load_scenarios reads bytes and parses JSON (a
# json.JSONDecodeError becomes a ParseError naming the file, R5.3), then
# parse_scenario maps the parsed object onto the Scenario / Turn / AssertionSpec
# data models, raising a SchemaError on any structural violation (R2.4, R2.7,
# R4.2, R2.6). Every error message carries enough attribution — source file,
# scenario id, and 0-based turn index — for a maintainer to locate the offending
# fixture element. Directory listings are sorted so repeated runs are
# deterministic (R8.4).


def _require_assertion(
    raw_assertion: object,
    scenario_id: str,
    turn_index: int,
) -> AssertionSpec:
    """Validate one raw assertion object and map it to an AssertionSpec.

    Collects every field other than ``type`` into :attr:`AssertionSpec.params`
    (R2.6), resolves the ``type`` against the registry (R4.1, R4.2), and verifies
    that all required parameters for the type are present (R2.6).

    Args:
        raw_assertion: The raw assertion value parsed from the fixture; expected
            to be an object with a string ``type`` field.
        scenario_id: The scenario identifier, used for error attribution.
        turn_index: The 0-based index of the turn carrying the assertion, used
            for error attribution.

    Returns:
        The validated AssertionSpec with its ``type`` and collected ``params``.

    Raises:
        SchemaError: When the assertion is not an object, omits or misuses
            ``type``, names an unknown Assertion_Type, or omits a required
            parameter; the message names the scenario, the turn index, and the
            offending detail.
    """
    if not isinstance(raw_assertion, dict):
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: each assertion must be an object, "
            f"got {type(raw_assertion).__name__}"
        )
    type_name = raw_assertion.get("type")
    if not isinstance(type_name, str) or not type_name:
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: assertion is missing a string "
            f"'type' field"
        )
    # An unknown type raises SchemaError naming scenario, turn index, and type (R4.2).
    resolve(type_name, scenario_id, turn_index)
    params: dict[str, object] = {
        key: value for key, value in raw_assertion.items() if key != "type"
    }
    for required in REQUIRED_PARAMS.get(type_name, ()):  # R2.6
        if required not in params:
            raise SchemaError(
                f"scenario {scenario_id!r} turn {turn_index}: assertion {type_name!r} is "
                f"missing required parameter {required!r}"
            )
    return AssertionSpec(type=type_name, params=params)


def _require_turn(raw_turn: object, scenario_id: str, turn_index: int) -> Turn:
    """Validate one raw turn object and map it to a Turn.

    Enforces the turn structure from Requirement 2: a ``role`` of exactly
    ``agent`` or ``bootcamper`` (R2.1, R2.7), a string ``content`` (R2.2, R2.7),
    and ``assertions`` only on agent turns — a bootcamper turn carrying a
    non-empty ``assertions`` field is an error (R2.4).

    Args:
        raw_turn: The raw turn value parsed from the fixture; expected to be an
            object with ``role`` and ``content`` fields.
        scenario_id: The scenario identifier, used for error attribution.
        turn_index: The 0-based index of this turn within the transcript, used
            for error attribution.

    Returns:
        The validated Turn with its parsed AssertionSpec list (empty for
        bootcamper turns and for agent turns with no assertions).

    Raises:
        SchemaError: When the turn is not an object, omits ``role`` or
            ``content``, carries an invalid ``role``, holds a non-string
            ``content``, supplies a non-list ``assertions`` field, or is a
            bootcamper turn carrying a non-empty ``assertions`` field; the
            message names the scenario and the offending turn index.
    """
    if not isinstance(raw_turn, dict):
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: each turn must be an object, "
            f"got {type(raw_turn).__name__}"
        )
    if "role" not in raw_turn:  # R2.7
        raise SchemaError(f"scenario {scenario_id!r} turn {turn_index}: missing 'role' field")
    role = raw_turn["role"]
    if role not in ("agent", "bootcamper"):  # R2.1
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: 'role' must be 'agent' or "
            f"'bootcamper', got {role!r}"
        )
    if "content" not in raw_turn:  # R2.7
        raise SchemaError(f"scenario {scenario_id!r} turn {turn_index}: missing 'content' field")
    content = raw_turn["content"]
    if not isinstance(content, str):  # R2.2
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: 'content' must be a string, "
            f"got {type(content).__name__}"
        )

    raw_assertions = raw_turn.get("assertions")
    if raw_assertions is not None and not isinstance(raw_assertions, list):
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: 'assertions' must be a list, "
            f"got {type(raw_assertions).__name__}"
        )
    if role == "bootcamper" and raw_assertions:  # R2.4 — only non-empty is an error
        raise SchemaError(
            f"scenario {scenario_id!r} turn {turn_index}: a bootcamper turn must not carry "
            f"'assertions'"
        )

    assertions: list[AssertionSpec] = []
    if role == "agent" and raw_assertions:
        assertions = [
            _require_assertion(raw_assertion, scenario_id, turn_index)
            for raw_assertion in raw_assertions
        ]
    return Turn(role=role, content=content, assertions=assertions)


def parse_scenario(raw: dict, source: Path) -> Scenario:
    """Map a parsed JSON object onto a validated Scenario (R1, R2).

    Validates the top-level fixture structure and every turn and assertion it
    contains, mapping the result onto the Scenario / Turn / AssertionSpec data
    models. All validation runs here, before any assertion is evaluated (R5.5).
    Turn-level and assertion-level errors are attributed with the 0-based turn
    index so a maintainer can locate the offending element.

    Args:
        raw: The object parsed from a fixture file. Expected to be a mapping with
            a non-empty string ``scenario``, a string ``description``, an
            optional string ``rule_ref``, and a ``turns`` list of one or more
            turn objects.
        source: The fixture file the object was parsed from, recorded on the
            returned Scenario and used for error attribution.

    Returns:
        The validated Scenario with its turns and assertions preserved in order.

    Raises:
        SchemaError: When the object violates the fixture structure — a missing,
            empty, or non-string ``scenario`` (R1.2); a missing or non-string
            ``description`` (R1.3); a non-string ``rule_ref`` (R1.6); a missing,
            non-list, or empty ``turns`` list (R1.4); or any turn/assertion
            violation surfaced by the turn and assertion validators (R2.x, R4.2).
    """
    if not isinstance(raw, dict):
        raise SchemaError(
            f"{source}: fixture must be a JSON object, got {type(raw).__name__}"
        )

    scenario_id = raw.get("scenario")
    if not isinstance(scenario_id, str) or not scenario_id:  # R1.2
        raise SchemaError(
            f"{source}: 'scenario' must be a non-empty string identifier, got {scenario_id!r}"
        )

    description = raw.get("description")
    if not isinstance(description, str):  # R1.3
        raise SchemaError(
            f"scenario {scenario_id!r}: 'description' must be a string, got {description!r}"
        )

    rule_ref = raw.get("rule_ref")  # R1.6 — optional; None when absent
    if rule_ref is not None and not isinstance(rule_ref, str):
        raise SchemaError(
            f"scenario {scenario_id!r}: 'rule_ref' must be a string when present, "
            f"got {type(rule_ref).__name__}"
        )

    raw_turns = raw.get("turns")
    if not isinstance(raw_turns, list) or not raw_turns:  # R1.4 — >= 1 turn
        raise SchemaError(
            f"scenario {scenario_id!r}: 'turns' must be a non-empty list of turns"
        )

    turns = [
        _require_turn(raw_turn, scenario_id, turn_index)
        for turn_index, raw_turn in enumerate(raw_turns)
    ]
    return Scenario(
        scenario=scenario_id,
        description=description,
        turns=turns,
        rule_ref=rule_ref,
        source=source,
    )


def _read_fixture(path: Path) -> Scenario:
    """Read, JSON-parse, and validate a single fixture file.

    Args:
        path: The fixture file to read and parse.

    Returns:
        The validated Scenario parsed from the file.

    Raises:
        ParseError: When the file's bytes are not parseable by the stdlib JSON
            loader; the message names the file (R5.3).
        SchemaError: When the parsed object violates the fixture structure
            (R2.x, R4.2, R5.5), as surfaced by :func:`parse_scenario`.
    """
    text = path.read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:  # R5.3
        raise ParseError(f"{path}: not valid JSON ({exc})") from exc
    return parse_scenario(raw, path)


def load_scenarios(target: Path) -> list[Scenario]:
    """Load and validate one fixture file or every ``*.json`` in a directory.

    When ``target`` is a directory, every ``*.json`` file directly within it is
    loaded in sorted order so repeated runs are deterministic (R5.1, R8.4); an
    empty directory is an error (R5.4). When ``target`` is a single file, only
    that file is loaded (R5.2). Each file is parsed with the stdlib JSON loader
    and validated against the fixture structure before any evaluation (R5.5).

    Args:
        target: A directory of fixtures or a single fixture file to load.

    Returns:
        The validated Scenarios in deterministic order — sorted by path for a
        directory, or a single-element list for a file.

    Raises:
        ParseError: When a fixture file is not parseable by the stdlib JSON
            loader; the message names the file (R5.3).
        EmptyDirError: When ``target`` is a directory containing no ``*.json``
            fixtures; the message names the directory (R5.4).
        SchemaError: When a fixture violates the R1/R2 structure (R5.5).
        EvalError: When ``target`` is neither an existing file nor an existing
            directory.
    """
    if target.is_dir():
        paths = sorted(target.glob("*.json"))  # R5.1 — deterministic order (R8.4)
        if not paths:  # R5.4
            raise EmptyDirError(f"{target}: no *.json fixtures found in directory")
        return [_read_fixture(path) for path in paths]
    if target.is_file():  # R5.2
        return [_read_fixture(target)]
    raise EvalError(f"{target}: not an existing fixture file or directory")


# ---------------------------------------------------------------------------
# Evaluation and reporting (Requirements 6, 7)
# ---------------------------------------------------------------------------
#
# Evaluation is collect-all (R6.1): every assertion on every agent turn is
# evaluated and its failures accumulated before the runner reports. Nothing here
# reads the clock, the network, the environment, or any random source, so a
# repeated run over unchanged fixtures yields identical failures and the same
# exit code (R8.4). The default fixtures directory is resolved relative to this
# script's location so the checker works no matter the current working directory.

_SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_FIXTURES_DIR = _SCRIPT_DIR.parent / "tests" / "eval"  # senzing-bootcamp/tests/eval (R5.1)


def count_assertions(scenario: Scenario) -> int:
    """Count the behavioral assertions across every agent turn in a scenario.

    Bootcamper turns carry no assertions, so only agent-turn assertions
    contribute. Used by the runner for the summary line's "assertions evaluated"
    figure (R6.5).

    Args:
        scenario: The scenario whose assertions to count.

    Returns:
        The total number of assertions attached to agent turns in the scenario.
    """
    return sum(len(turn.assertions) for turn in scenario.turns)


def evaluate_turn(turn: Turn, ctx: EvalContext) -> list[EvalFailure]:
    """Evaluate every assertion attached to one turn and collect its failures (R6.1).

    For an agent turn, each attached assertion is resolved to its predicate via
    the registry and evaluated; every failing :class:`AssertionOutcome` produces
    an :class:`EvalFailure` attributed with the scenario id and turn index from
    ``ctx`` (R6.3, R6.4). Evaluation is collect-all — every assertion is checked
    even after an earlier one fails (R6.1). Bootcamper turns carry no assertions
    and therefore produce no failures.

    Args:
        turn: The turn being evaluated. Bootcamper turns yield an empty list.
        ctx: The evaluation context supplying the surrounding transcript, the
            current turn index, and the scenario id used for attribution.

    Returns:
        The list of failures for this turn, in assertion order; empty when every
        assertion passed (or the turn is a bootcamper turn).
    """
    failures: list[EvalFailure] = []
    for spec in turn.assertions:
        predicate = resolve(spec.type, ctx.scenario_id, ctx.index)
        outcome = predicate(turn, ctx, spec.params)
        if not outcome.passed:
            failures.append(
                EvalFailure(
                    scenario_id=ctx.scenario_id,
                    turn_index=ctx.index,
                    assertion_type=spec.type,
                    message=outcome.message,
                )
            )
    return failures


def evaluate_scenario(scenario: Scenario) -> list[EvalFailure]:
    """Evaluate every assertion on every agent turn of a scenario (R6.1).

    Walks the transcript in order, building an :class:`EvalContext` for each
    agent turn (the full turn list, the current index, and the scenario id) and
    accumulating the failures from :func:`evaluate_turn` across the whole
    scenario. Failures are returned in transcript order so reporting is
    deterministic (R8.4).

    Args:
        scenario: The validated scenario to evaluate.

    Returns:
        Every assertion failure across the scenario, in turn-then-assertion
        order; empty when all assertions pass.
    """
    failures: list[EvalFailure] = []
    for index, turn in enumerate(scenario.turns):
        if turn.role != "agent" or not turn.assertions:
            continue
        ctx = EvalContext(turns=scenario.turns, index=index, scenario_id=scenario.scenario)
        failures.extend(evaluate_turn(turn, ctx))
    return failures


def run(target: Path) -> int:
    """Load, evaluate, and report on the fixtures at ``target``; return the exit code.

    Loads every fixture under ``target`` (a directory of fixtures or a single
    fixture file), then evaluates all of them with collect-all semantics. A
    parse, empty-directory, or schema error is printed to stderr and returns exit
    code 1 (R5.3, R5.4, R7.3). Otherwise a summary line — scenarios evaluated,
    assertions evaluated, failures — is printed to stdout (R6.5), each failure is
    printed to stderr naming its scenario, turn index, assertion type, and
    message (R6.3, R6.4), and the function returns 0 when no assertion failed
    (R7.1) or 1 when at least one did (R7.2).

    Args:
        target: A directory of fixtures or a single fixture file to evaluate.

    Returns:
        0 when every assertion across all fixtures passed; 1 when one or more
        assertions failed or a parse/schema/empty-directory error occurred.
    """
    try:
        scenarios = load_scenarios(target)
    except EvalError as exc:  # ParseError / EmptyDirError / SchemaError (R5.3, R5.4, R7.3)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    failures: list[EvalFailure] = []
    assertions_evaluated = 0
    for scenario in scenarios:
        assertions_evaluated += count_assertions(scenario)
        failures.extend(evaluate_scenario(scenario))

    # Summary to stdout (R6.5).
    print(
        f"Evaluated {len(scenarios)} scenario(s), {assertions_evaluated} assertion(s): "
        f"{len(failures)} failure(s)."
    )

    # Each failure to stderr, fully attributed (R6.3, R6.4).
    for failure in failures:
        print(
            f"FAIL [{failure.scenario_id}] turn {failure.turn_index} "
            f"{failure.assertion_type}: {failure.message}",
            file=sys.stderr,
        )

    return 0 if not failures else 1  # R7.1 / R7.2


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: parse arguments, run the checker, and return its exit code.

    Parses ``argv`` (or ``sys.argv[1:]`` when ``argv`` is None) for an optional
    single fixture ``path`` (R5.2) and a ``--fixtures-dir`` directory option whose
    default is ``senzing-bootcamp/tests/eval`` resolved relative to this script so
    it works regardless of the current working directory (R5.1). When ``path`` is
    given it is the evaluation target; otherwise the fixtures directory is. The
    selected target is handed to :func:`run` and its exit code is returned
    (R7.4, R11.2).

    Args:
        argv: The argument vector to parse. None means use ``sys.argv[1:]``.

    Returns:
        The process exit code from :func:`run`: 0 on all-pass, 1 on any failure
        or parse/schema/empty-directory error.
    """
    parser = argparse.ArgumentParser(
        prog="eval_conversations.py",
        description=(
            "Evaluate recorded conversational fixtures against declarative behavioral "
            "assertions. Verifies that a recorded conversation HONORS a rule (distinct "
            "from string-presence tests that verify the steering SAYS the rule)."
        ),
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Optional single fixture file to evaluate (R5.2).",
    )
    parser.add_argument(
        "--fixtures-dir",
        default=DEFAULT_FIXTURES_DIR,
        type=Path,
        help="Directory of fixtures (default: senzing-bootcamp/tests/eval) (R5.1).",
    )
    args = parser.parse_args(argv)

    target = Path(args.path) if args.path is not None else Path(args.fixtures_dir)
    return run(target)


if __name__ == "__main__":  # R11.2
    sys.exit(main())
