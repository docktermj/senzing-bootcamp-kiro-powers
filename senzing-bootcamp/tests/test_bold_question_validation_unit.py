"""Deterministic unit tests for the bold-question detector.

Exercises the Rule 4 bold-question detection in
``validate_behavior_rules.py`` with fixed input strings and fixed on-disk
steering content. Every test is deterministic: no randomness, no wall-clock
time, and no external state (R10.5). This rule is deliberately *not* tested
with Hypothesis — a question either carries a balanced bold span or it does
not, and the meaningful cases (missing bold, italic-not-bold, unbalanced,
partial, choice options, soft-wrapped spans, scope exclusions, and the
negative-example exemption) are a small enumerable set best covered by
curated examples.

Coverage:

- **Flags missing bold (R10.4, R10.1):** a 👉 question whose text lacks a
  balanced bold span produces a Rule 4 violation — no markers, italic-only
  (``*...*``), unbalanced (``**text``), and partial (``**What** language?``).
- **Accepts bold (R10.5, R10.2):** a 👉 question whose text is a single
  balanced ``**...**`` span produces no violation — plain bold, bold wrapping
  a quoted question, a choice lead question with plain numbered options, and a
  soft-wrapped multi-line span.
- **Scope (R10.3):** non-👉 prose lines, headings, numbered option lines,
  inline ``👉`` mentions inside quotes, soft-wrap ``👉`` continuations, and
  fenced-code content are never flagged.
- **Negative-example exemption:** a 👉 question under a ``(WRONG)`` heading is
  not flagged, while the same un-bolded text under a ``(CORRECT)`` heading is
  required to be bold.
- **Helpers:** direct assertions on ``strip_bold`` and
  ``question_text_is_bold`` for the enumerated shapes.

Feature: question-visibility

Validates: Requirements R10.4, R10.5, R10.1, R10.2, R10.3
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_behavior_rules import (  # noqa: E402
    Violation,
    question_text_is_bold,
    strip_bold,
    validate_steering_file,
)

_POINTER = "\U0001f449"  # 👉


class TestBoldQuestionValidationUnit:
    """Deterministic unit tests for the Rule 4 bold-question detector.

    Validates: Requirements R10.4, R10.5, R10.1, R10.2, R10.3
    """

    # -- helpers (pure, deterministic) -------------------------------------

    @staticmethod
    def _doc(*lines: str) -> str:
        """Join lines into a single newline-terminated document.

        Args:
            *lines: Individual lines of Markdown, without trailing newlines.

        Returns:
            The lines joined with ``\\n`` and terminated by a final newline.
        """
        return "\n".join(lines) + "\n"

    def _rule4_violations(self, tmp_path: Path, content: str) -> list[Violation]:
        """Validate fixed steering content and return only Rule 4 violations.

        Writes ``content`` to a temporary steering file, runs
        :func:`validate_steering_file`, and filters the result to the
        bold-question rule (``rule == 4``).

        Args:
            tmp_path: pytest-provided temporary directory.
            content: The steering-file content to validate.

        Returns:
            The list of Rule 4 (bold-question) violations found.
        """
        path = tmp_path / "steering_sample.md"
        path.write_text(content, encoding="utf-8")
        return [v for v in validate_steering_file(path) if v.rule == 4]

    # -- Flags missing bold (R10.4, R10.1) ---------------------------------

    def test_flags_question_with_no_bold_markers(self, tmp_path: Path) -> None:
        """A 👉 question with no bold markers is flagged.

        Validates: Requirements R10.4, R10.1
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} Ready to continue?",
        )
        violations = self._rule4_violations(tmp_path, content)
        assert len(violations) == 1, (
            f"Expected 1 Rule 4 violation, got {[v.message for v in violations]}"
        )

    def test_flags_italic_only_question(self, tmp_path: Path) -> None:
        """A 👉 question wrapped in italic (``*...*``) — not bold — is flagged.

        Validates: Requirements R10.4, R10.1
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} *Ready to continue?*",
        )
        violations = self._rule4_violations(tmp_path, content)
        assert len(violations) == 1, (
            f"Expected 1 Rule 4 violation, got {[v.message for v in violations]}"
        )

    def test_flags_unbalanced_bold_question(self, tmp_path: Path) -> None:
        """A 👉 question with an unclosed bold span (``**text``) is flagged.

        Validates: Requirements R10.4, R10.1
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} **Ready to continue?",
        )
        violations = self._rule4_violations(tmp_path, content)
        assert len(violations) == 1, (
            f"Expected 1 Rule 4 violation, got {[v.message for v in violations]}"
        )

    def test_flags_partial_bold_question(self, tmp_path: Path) -> None:
        """A 👉 question with only part of its text bold is flagged.

        Validates: Requirements R10.4, R10.1
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} **What** language?",
        )
        violations = self._rule4_violations(tmp_path, content)
        assert len(violations) == 1, (
            f"Expected 1 Rule 4 violation, got {[v.message for v in violations]}"
        )

    # -- Accepts bold (R10.5, R10.2) ---------------------------------------

    def test_accepts_plain_bold_question(self, tmp_path: Path) -> None:
        """A 👉 question whose text is a single balanced bold span is accepted.

        Validates: Requirements R10.5, R10.2
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} **Ready to continue?**",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_accepts_bold_around_quoted_question(self, tmp_path: Path) -> None:
        """Bold wrapping a quoted question (quotes inside the span) is accepted.

        Validates: Requirements R10.5, R10.2
        """
        content = self._doc(
            "# Heading",
            "",
            f'{_POINTER} **"Do you already have a Senzing license?"**',
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_accepts_choice_lead_with_plain_numbered_options(
        self, tmp_path: Path
    ) -> None:
        """A bold choice lead with plain numbered options produces no violation.

        The numbered option lines carry no 👉 and no bold markers, so only the
        lead question is checked and it is a balanced bold span.

        Validates: Requirements R10.5, R10.2
        """
        content = self._doc(
            "# Heading",
            "",
            f"{_POINTER} **What would you like to do next?**",
            "",
            "1. Create a one-page executive summary",
            "2. Move on to Module 2",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_accepts_soft_wrapped_bold_span(self, tmp_path: Path) -> None:
        """A single balanced bold span soft-wrapped across a blockquote passes.

        The span opens right after 👉 on the first line and closes on the last
        line, never crossing a blank line or a numbered-list boundary.

        Validates: Requirements R10.5, R10.2
        """
        content = self._doc(
            "# Heading",
            "",
            f"> {_POINTER} **Will the entity resolution results need to interface",
            "> with other software such as a CRM, a search engine, a data",
            "> warehouse, or a downstream application?**",
        )
        assert self._rule4_violations(tmp_path, content) == []

    # -- Scope: never flagged (R10.3) --------------------------------------

    def test_scope_prose_line_not_flagged(self, tmp_path: Path) -> None:
        """A non-👉 prose line containing a question mark is never flagged.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            "This is ordinary prose that asks a question? It is not a prompt.",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_scope_heading_not_flagged(self, tmp_path: Path) -> None:
        """A heading line is never flagged, even when phrased as a question.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            "## What is entity resolution?",
            "",
            "Some explanatory prose.",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_scope_numbered_option_line_not_flagged(self, tmp_path: Path) -> None:
        """A numbered option line is never flagged as a bold-question violation.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            "1. Would you like Python?",
            "2. Would you like Java?",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_scope_inline_pointer_inside_quotes_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """An inline 👉 mention inside quoted prose is never flagged.

        The line does not start with 👉 (after stripping blockquote/list
        markers), so it is not a leading-question candidate.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            f'The agent writes: "{_POINTER} Does that make sense?" to the user.',
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_scope_soft_wrap_pointer_continuation_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """A 👉 that continues a wrapped prose line is treated as an inline mention.

        Because the preceding line is a non-blank continuation at the same
        blockquote depth, the 👉 does not open a new block and is not a leading
        question.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            "This paragraph wraps onto a second line and the second line begins",
            f"{_POINTER} which makes it a soft-wrap continuation, not a prompt?",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_scope_fenced_code_pointer_not_flagged(self, tmp_path: Path) -> None:
        """A 👉 question inside a fenced code block is never flagged.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "# Heading",
            "",
            "```text",
            f"{_POINTER} Ready to continue?",
            "```",
        )
        assert self._rule4_violations(tmp_path, content) == []

    # -- Negative-example exemption ----------------------------------------

    def test_negative_example_wrong_heading_not_flagged(
        self, tmp_path: Path
    ) -> None:
        """An un-bolded 👉 question under a (WRONG) heading is exempt.

        Validates: Requirement R10.3
        """
        content = self._doc(
            "## Missing-Bold (WRONG)",
            "",
            f"> {_POINTER} What language would you like to use?",
        )
        assert self._rule4_violations(tmp_path, content) == []

    def test_correct_heading_requires_bold(self, tmp_path: Path) -> None:
        """The same un-bolded text under a (CORRECT) heading is flagged.

        Validates: Requirements R10.1, R10.4
        """
        content = self._doc(
            "## Missing-Bold (CORRECT)",
            "",
            f"> {_POINTER} What language would you like to use?",
        )
        violations = self._rule4_violations(tmp_path, content)
        assert len(violations) == 1, (
            f"Expected 1 Rule 4 violation, got {[v.message for v in violations]}"
        )

    def test_correct_heading_with_bold_passes(self, tmp_path: Path) -> None:
        """A bold 👉 question under a (CORRECT) heading produces no violation.

        Validates: Requirements R10.2, R10.5
        """
        content = self._doc(
            "## Missing-Bold (CORRECT)",
            "",
            f"> {_POINTER} **What language would you like to use?**",
        )
        assert self._rule4_violations(tmp_path, content) == []

    # -- Direct assertions: strip_bold -------------------------------------

    def test_strip_bold_removes_paired_markers(self) -> None:
        """strip_bold removes every ``**`` marker, returning the wording.

        Validates: Requirement R10.1
        """
        assert strip_bold("**Ready to continue?**") == "Ready to continue?"
        assert strip_bold("**A** and **B**") == "A and B"

    def test_strip_bold_leaves_unmarked_text_unchanged(self) -> None:
        """strip_bold leaves text without ``**`` markers unchanged.

        Single-asterisk italic markers are not bold markers and are preserved.

        Validates: Requirement R10.1
        """
        assert strip_bold("plain question text?") == "plain question text?"
        assert strip_bold("*italic*") == "*italic*"

    def test_strip_bold_is_verdict_preserving_across_bold(self) -> None:
        """Identical wording differing only by bold strips to the same text.

        This is the invariance the write-policy-gate relies on: adding or
        removing bold markers cannot change the marker-free wording.

        Validates: Requirement R10.1
        """
        assert strip_bold("**What language would you like to use?**") == strip_bold(
            "What language would you like to use?"
        )

    # -- Direct assertions: question_text_is_bold --------------------------

    def test_question_text_is_bold_true_shapes(self) -> None:
        """A single balanced span covering the whole (trimmed) text is bold.

        Validates: Requirement R10.2
        """
        assert question_text_is_bold("**Ready to continue?**") is True
        assert question_text_is_bold('**"Do you have a license?"**') is True
        # Surrounding whitespace is trimmed before the check.
        assert question_text_is_bold("   **Trimmed still bold?**   ") is True

    def test_question_text_is_bold_false_shapes(self) -> None:
        """Missing, italic, unbalanced, partial, and multi-span text is not bold.

        Validates: Requirement R10.1
        """
        assert question_text_is_bold("Ready to continue?") is False       # no markers
        assert question_text_is_bold("*Ready to continue?*") is False     # italic only
        assert question_text_is_bold("**Ready to continue?") is False     # unbalanced
        assert question_text_is_bold("**What** language?") is False       # partial
        assert question_text_is_bold("**What** and **more?**") is False   # two spans
        assert question_text_is_bold("****") is False                     # empty span
        assert question_text_is_bold("** **") is False                    # blank inner
