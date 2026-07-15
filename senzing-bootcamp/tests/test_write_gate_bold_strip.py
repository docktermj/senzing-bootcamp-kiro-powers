"""Deterministic hook-content tests for the write-policy-gate bold-strip rule.

Feature: question-visibility

These are pure, example-based (no randomness, no clock, no network) assertions
on the natural-language prompt inside ``senzing-bootcamp/hooks/write-policy-gate.json``.
The write-policy-gate is a ``PreToolUse`` LLM-prompt hook whose CHECK 2 enforces
the One Question Rule on content written to ``config/.question_pending``.

Because the question-visibility feature wraps every leading question's text in
CommonMark bold (``**...**``), CHECK 2 must strip those bold markers *before*
counting question marks and detecting joining conjunctions, so the presence of
``**`` cannot change the single-question verdict. These tests load the hook JSON,
extract the prompt string (``hooks[0].action.prompt``), and make substring
assertions on it.

Covered requirements:
    * R6.1 — the One Question Rule (rules 1-5) remains enforced on
      ``.question_pending`` content.
    * R6.2 — CHECK 2 strips ``**`` markers before counting question marks and
      detecting joining conjunctions.
    * R6.4 — the existing ``⚠️ COMPOUND QUESTION DETECTED`` output format
      remains present.
"""

from __future__ import annotations

import json
from pathlib import Path

# Resolve the real shipped hook file relative to this test.
_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_WRITE_POLICY_GATE = _BOOTCAMP_DIR / "hooks" / "write-policy-gate.json"


def _load_gate_prompt() -> str:
    """Return the natural-language prompt of the write-policy-gate hook.

    Reads ``write-policy-gate.json`` and extracts ``hooks[0].action.prompt`` —
    the single string that carries all four checks' instructions.

    Returns:
        The hook prompt string.
    """
    data = json.loads(_WRITE_POLICY_GATE.read_text(encoding="utf-8"))
    return data["hooks"][0]["action"]["prompt"]


def _extract_check2(prompt: str) -> str:
    """Return the CHECK 2 section of the gate prompt.

    Slices from the ``CHECK 2`` header up to the ``CHECK 3`` header so the
    assertions about the bold-strip instruction, rules 1-5, and the compound
    output format are scoped to the single-question enforcement block.

    Args:
        prompt: The full hook prompt string.

    Returns:
        The substring covering CHECK 2 (falls back to the whole prompt if the
        CHECK 3 boundary is absent).
    """
    start = prompt.index("CHECK 2")
    end = prompt.find("CHECK 3", start)
    return prompt[start:end] if end != -1 else prompt[start:]


class TestWriteGateBoldStrip:
    """Content assertions on write-policy-gate CHECK 2 after bold-strip.

    Validates: Requirements R6.1, R6.2, R6.4
    """

    def test_check2_section_present(self) -> None:
        """CHECK 2 single-question enforcement block still exists."""
        prompt = _load_gate_prompt()
        assert "CHECK 2: SINGLE-QUESTION ENFORCEMENT" in prompt

    def test_check2_instructs_stripping_bold_markers(self) -> None:
        """CHECK 2 tells the gate to remove all ``**`` markers (R6.2)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "STRIP BOLD MARKERS" in check2
        assert "remove ALL '**'" in check2

    def test_strip_happens_before_evaluating_rules(self) -> None:
        """The strip step is ordered before any rule evaluation (R6.2)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "before evaluating any rule below" in check2
        # The strip instruction must textually precede rule 1.
        strip_pos = check2.index("STRIP BOLD MARKERS")
        rule1_pos = check2.index("1. EXACTLY ONE QUESTION")
        assert strip_pos < rule1_pos

    def test_strip_targets_question_mark_count_and_conjunctions(self) -> None:
        """Stripping applies to question-mark counting and conjunction detection (R6.2)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "question-mark count in rule 1" in check2
        assert "joining-conjunction detection in rule 2" in check2
        assert "marker-stripped wording only" in check2

    def test_rule_1_single_question_mark_present(self) -> None:
        """Rule 1 (exactly one question mark) remains enforced (R6.1)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "1. EXACTLY ONE QUESTION" in check2
        assert "exactly one question mark" in check2

    def test_rule_2_no_joining_conjunctions_present(self) -> None:
        """Rule 2 (no joining conjunctions) remains enforced (R6.1)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "2. NO CONJUNCTIONS JOINING QUESTIONS" in check2

    def test_rule_3_no_appended_alternatives_present(self) -> None:
        """Rule 3 (no appended alternatives) remains enforced (R6.1)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "3. NO APPENDED ALTERNATIVES" in check2

    def test_rule_4_unambiguous_yes_no_present(self) -> None:
        """Rule 4 (unambiguous yes/no) remains enforced (R6.1)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "4. UNAMBIGUOUS YES/NO" in check2

    def test_rule_5_no_followup_after_confirmation_present(self) -> None:
        """Rule 5 (no follow-up after confirmation) remains enforced (R6.1)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "5. NO FOLLOW-UP AFTER CONFIRMATION" in check2

    def test_compound_question_output_format_present(self) -> None:
        """The existing compound-question output format is unchanged (R6.4)."""
        check2 = _extract_check2(_load_gate_prompt())
        assert "⚠️ COMPOUND QUESTION DETECTED" in check2
        assert "REWRITE REQUIRED" in check2
        # The structured violation report fields remain.
        assert "Violation:" in check2
        assert "Original:" in check2
        assert "Fix:" in check2
