"""Bug-condition exploration test for the clean-question-presentation marker leak.

Property 1 (Bug Condition) — Clean Question, No Leaked Internal Markers.

These tests reproduce the CURRENT rendered agent turns from the UNFIXED steering
tree and the shipped eval fixtures, then assert the FIXED behavior
(``expectedBehavior`` from design.md) through the conversational-eval harness
predicates (``eval_conversations.py`` is NOT modified).

They are EXPECTED TO FAIL on the unfixed tree — the failures are the
counterexamples that confirm Bug_Condition C1 (a 👉 question rendered beside a
``🛑 STOP`` / ``⛔ MANDATORY GATE`` marker) exists. DO NOT "fix" these tests when
they fail: the failure is the correct, expected outcome for this exploration
task, and the same assertions become the fix oracle once the steering and
fixtures are corrected (they flip to PASS in task 4.5).

Bug_Condition: isBugCondition(X) C1 branch — hasQuestion AND
    leaksMarker("🛑" | "⛔" | "MANDATORY GATE").
Expected_Behavior: expectedBehavior(result) — exactly one 👉, ends on the
    question, non-compound, no self-answer, NOT contains "🛑"/"⛔".

Scoped to the concrete observed failing cases (the onboarding language-selection
turn in ``onboarding-phase1b-intro-language.md`` and the Module 3 visualization
gate in ``module3_gate_not_bypassed.json``) while still generating over the
transcript-text domain via Hypothesis.

Feature: clean-question-presentation

Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from eval_conversations import (  # noqa: E402
    POINTER,
    AssertionSpec,
    Scenario,
    Turn,
    evaluate_scenario,
    load_scenarios,
)

# ---------------------------------------------------------------------------
# Paths and marker constants
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_EVAL_DIR = _BOOTCAMP_DIR / "tests" / "eval"
_LANGUAGE_STEP_FILE = _STEERING_DIR / "onboarding-phase1b-intro-language.md"

_STOP = "\U0001f6d1"  # 🛑  U+1F6D1 — hard-stop marker
_GATE = "\u26d4"  # ⛔  U+26D4 — mandatory-gate marker

# Shipped question-presentation fixtures whose recorded agent turns are the
# CURRENT rendered turns (they carry a trailing 🛑 STOP line today).
_QUESTION_FIXTURES: tuple[str, ...] = (
    "single_question_stop.json",
    "confirmation_question_disambiguation.json",
    "module3_gate_not_bypassed.json",
)

# The fixed-behavior assertion set — mirrors expectedBehavior(result) in
# design.md: exactly one 👉, ends on the question, non-compound, no self-answer,
# and no leaked 🛑 / ⛔ marker.
_EXPECTED_BEHAVIOR_ASSERTIONS: tuple[AssertionSpec, ...] = (
    AssertionSpec("exactly_one_pointer"),
    AssertionSpec("ends_with_question_then_stop"),
    AssertionSpec("no_compound_question"),
    AssertionSpec("no_self_answer"),
    AssertionSpec("absent_marker", {"marker": _STOP}),
    AssertionSpec("absent_marker", {"marker": _GATE}),
)

# Just the "no leaked marker" subset, for a focused C1 headline counterexample.
_ABSENT_MARKER_ASSERTIONS: tuple[AssertionSpec, ...] = (
    AssertionSpec("absent_marker", {"marker": _STOP}),
    AssertionSpec("absent_marker", {"marker": _GATE}),
)


# ---------------------------------------------------------------------------
# Helpers (pure, deterministic)
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a file.

    Args:
        path: The file to read.

    Returns:
        The full file contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _extract_section(content: str, heading_prefix: str) -> str:
    """Return the body of the level-2 section whose heading starts with a prefix.

    The body runs from the line after the matched ``## `` heading up to (but not
    including) the next level-2 heading. ``### `` subsections stay in the body.

    Args:
        content: The full Markdown text to search.
        heading_prefix: The heading text/prefix to locate, e.g. ``"## 4."``.

    Returns:
        The section body text, or an empty string when the heading is absent.
    """
    lines = content.splitlines()
    start: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and line.strip().startswith(heading_prefix):
            start = idx
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def _demote_markup(line: str) -> str:
    """Strip leading blockquote and bold markup so a marker glyph is line-initial.

    Removes leading ``>`` blockquote markers and any leading ``*`` emphasis
    characters, so ``> **🛑 STOP ...`` and ``🛑 STOP ...`` both reduce to a string
    that starts with the marker glyph.

    Args:
        line: A single line of Markdown.

    Returns:
        The line with leading blockquote/bold markup and whitespace removed.
    """
    stripped = line.strip()
    while stripped.startswith(">"):
        stripped = stripped[1:].strip()
    return stripped.lstrip("*").strip()


def _is_rendered_marker_line(line: str) -> bool:
    """Return True when a line renders a 🛑 STOP or ⛔ MANDATORY GATE directive.

    Detects the internal control directives that currently leak into user-facing
    output beside a 👉 question: a line beginning with ``🛑 STOP`` (optionally in a
    blockquote / bold), or a line carrying the ``⛔ MANDATORY GATE`` glyph.

    Args:
        line: A single line of steering Markdown.

    Returns:
        True if the line is a rendered stop/gate marker directive.
    """
    body = _demote_markup(line)
    if body.startswith(f"{_STOP} STOP"):
        return True
    if body.startswith(_GATE):
        return True
    return _GATE in body and "MANDATORY GATE" in body


def _language_selection_rendered_turn() -> str:
    """Reproduce the CURRENT language-selection rendered turn from the steering.

    Builds the rendered turn the bootcamper sees at Step 4 (Programming Language
    Selection): the single 👉 question line followed by every rendered stop/gate
    marker line found in that step, in document order. On the unfixed tree this
    reproduces the leak (👉 question beside ``🛑 STOP`` / ``⛔ MANDATORY GATE``);
    once the fix makes the rendered prompt end on the 👉 question with no marker
    lines, the same reconstruction yields a clean single-question turn.

    Returns:
        The reconstructed rendered-turn text, or an empty string when Step 4 or
        its 👉 question cannot be located.
    """
    section = _extract_section(_read(_LANGUAGE_STEP_FILE), "## 4.")
    if not section:
        return ""
    lines = section.splitlines()
    pointer_line = next((ln for ln in lines if POINTER in ln), None)
    if pointer_line is None:
        return ""
    parts: list[str] = [pointer_line.strip()]
    parts.extend(ln.strip() for ln in lines if _is_rendered_marker_line(ln))
    return "\n\n".join(parts)


def _fixture_pointer_turns(fixture_name: str) -> list[Turn]:
    """Load a shipped fixture and return its agent turns that pose a 👉 question.

    Args:
        fixture_name: The fixture filename under ``senzing-bootcamp/tests/eval``.

    Returns:
        The agent turns whose recorded content contains the 👉 pointer.
    """
    scenario = load_scenarios(_EVAL_DIR / fixture_name)[0]
    return [t for t in scenario.turns if t.role == "agent" and POINTER in t.content]


def _evaluate(content: str, assertions: tuple[AssertionSpec, ...]) -> list:
    """Evaluate ``assertions`` against a rendered turn via the harness engine.

    Args:
        content: The rendered agent-turn text to evaluate.
        assertions: The behavioral assertions to attach to the turn.

    Returns:
        The list of ``EvalFailure`` objects the harness produced (empty on pass).
    """
    turn = Turn(role="agent", content=content, assertions=list(assertions))
    scenario = Scenario(
        scenario="clean_question_presentation_marker_leak",
        description="Exploration reproduction of the marker-leak bug condition (C1).",
        turns=[turn],
        rule_ref=None,
        source=Path("inline"),
    )
    return evaluate_scenario(scenario)


def _format(failures: list, content: str) -> str:
    """Build an assertion message that names each leak and shows the turn.

    Args:
        failures: The harness ``EvalFailure`` list.
        content: The rendered turn that produced the failures.

    Returns:
        A human-readable multi-line message for the failing assertion.
    """
    reasons = "\n".join(f"  - {f.assertion_type}: {f.message}" for f in failures)
    return (
        "expected a clean question turn (expectedBehavior), but the harness found "
        f"leaks:\n{reasons}\n--- rendered turn ---\n{content}"
    )


# ---------------------------------------------------------------------------
# Harness-evaluated reproduction (mirrors expectedBehavior via the predicates)
# ---------------------------------------------------------------------------


class TestMarkerLeakExplorationHarness:
    """Reproduce C1 by evaluating current rendered turns with the fix oracle.

    Each test asserts the FIXED behavior; on the unfixed tree the harness returns
    failures whose messages are the counterexamples that confirm the bug.

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
    """

    def test_language_selection_turn_has_no_leaked_markers(self) -> None:
        """The language-selection turn must not render 🛑 / ⛔ beside the question.

        EXPECTED TO FAIL on the unfixed tree with ``prohibited marker '🛑' present
        in turn`` and ``prohibited marker '⛔' present in turn``.
        """
        content = _language_selection_rendered_turn()
        assert POINTER in content, (
            "precondition: the Step 4 👉 language-selection question was not found "
            f"in {_LANGUAGE_STEP_FILE.name}"
        )
        failures = _evaluate(content, _ABSENT_MARKER_ASSERTIONS)
        assert not failures, _format(failures, content)

    def test_language_selection_turn_matches_expected_behavior(self) -> None:
        """The full expectedBehavior predicate set must hold for language selection.

        EXPECTED TO FAIL on the unfixed tree: the rendered ``🛑 STOP`` /
        ``⛔ MANDATORY GATE`` directives trip the absent-marker checks (and the
        ⛔ block also trails the 👉 question).
        """
        content = _language_selection_rendered_turn()
        assert POINTER in content, (
            "precondition: the Step 4 👉 language-selection question was not found "
            f"in {_LANGUAGE_STEP_FILE.name}"
        )
        failures = _evaluate(content, _EXPECTED_BEHAVIOR_ASSERTIONS)
        assert not failures, _format(failures, content)

    @pytest.mark.parametrize("fixture_name", _QUESTION_FIXTURES)
    def test_shipped_question_fixture_has_no_leaked_markers(self, fixture_name: str) -> None:
        """Each shipped question fixture's agent turn must not leak 🛑 / ⛔.

        The shipped fixtures are recorded CURRENT rendered turns; today they carry
        a trailing ``🛑 STOP`` line, so this is EXPECTED TO FAIL with
        ``prohibited marker '🛑' present in turn``.

        Args:
            fixture_name: The parametrized fixture filename.
        """
        turns = _fixture_pointer_turns(fixture_name)
        assert turns, f"{fixture_name} has no 👉 agent turn to evaluate"
        failures: list = []
        for turn in turns:
            failures.extend(_evaluate(turn.content, _ABSENT_MARKER_ASSERTIONS))
        assert not failures, _format(failures, "\n\n".join(t.content for t in turns))


# ---------------------------------------------------------------------------
# Content-assertion complement (enumerate rendered-marker occurrences)
# ---------------------------------------------------------------------------


class TestMarkerLeakSteeringEnumeration:
    """Enumerate rendered stop/gate marker lines beside the 👉 question.

    Complements the content-assertion tests in ``test_bold_question_steering.py``
    (``test_protocol_stop_marker_is_plain``, ``test_examples_stop_marker_is_plain``)
    which currently REQUIRE a rendered ``🛑 STOP`` line; here we assert the fixed
    expectation (no rendered marker beside the question) so the offending lines
    are surfaced as counterexamples.

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
    """

    def test_language_step_renders_no_stop_or_gate_marker_lines(self) -> None:
        """Step 4 must render no ``🛑 STOP`` / ``⛔ MANDATORY GATE`` marker lines.

        EXPECTED TO FAIL on the unfixed tree: it enumerates the leaked directives
        (``🛑 STOP — Wait ...``, ``⛔ **MANDATORY GATE** — ...``,
        ``**🛑 STOP — End your response here.** ...``).
        """
        section = _extract_section(_read(_LANGUAGE_STEP_FILE), "## 4.")
        assert section, f"Step 4 (Programming Language Selection) not found in {_LANGUAGE_STEP_FILE.name}"
        offenders = [ln.strip() for ln in section.splitlines() if _is_rendered_marker_line(ln)]
        assert not offenders, (
            "language-selection step renders internal directives beside the 👉 "
            "question (these should be internal-only):\n"
            + "\n".join(f"  - {ln}" for ln in offenders)
        )


# ---------------------------------------------------------------------------
# Scoped property-based reproduction over the transcript-text domain
# ---------------------------------------------------------------------------

# The concrete observed C1 cases. Both draw their rendered-turn text from tree
# artifacts (the steering step and the shipped gate fixture) so the property is a
# genuine oracle: it fails while the markers leak and passes once they are gone.
_OBSERVED_LEAK_CASES: tuple[str, ...] = ("language_selection", "module3_gate")


def _rendered_turn_for_case(case: str) -> str:
    """Return the CURRENT rendered turn for a named observed C1 case.

    Args:
        case: One of :data:`_OBSERVED_LEAK_CASES`.

    Returns:
        The rendered agent-turn text for that case, drawn from the tree.
    """
    if case == "language_selection":
        return _language_selection_rendered_turn()
    turns = _fixture_pointer_turns("module3_gate_not_bypassed.json")
    return "\n\n".join(t.content for t in turns)


class TestMarkerLeakProperty:
    """Property: every observed question turn honors expectedBehavior (no leak).

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
    """

    @given(case=st.sampled_from(_OBSERVED_LEAK_CASES))
    def test_rendered_question_turn_has_no_leaked_markers(self, case: str) -> None:
        """For any observed case, the rendered turn must not leak 🛑 / ⛔.

        EXPECTED TO FAIL on the unfixed tree; Hypothesis reports the failing
        ``case`` and the harness message is the counterexample.

        Args:
            case: The generated observed-case identifier.
        """
        content = _rendered_turn_for_case(case)
        assert POINTER in content, f"case {case!r} produced no 👉 question turn"
        failures = _evaluate(content, _ABSENT_MARKER_ASSERTIONS)
        assert not failures, _format(failures, content)
