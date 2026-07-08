"""Deterministic content-assertion tests for the bold-question rule.

Verifies that the four authoritative steering files carry the bold-question
convention introduced by the ``question-visibility`` feature:

- ``agent-behavior-rules.md`` Rule 4 states the bold clause (question text is
  wrapped in bold *in addition to* the 👉 pointer, never as a replacement).
- ``agent-instructions.md`` Communication section states the bold clause.
- ``conversation-protocol.md`` contains a distinct bold rule, a Pre-Output
  Validation Checklist item about bold, and a Self-Check item about bold.
- ``conversation-examples.md`` renders CORRECT examples in bold and contains a
  Missing-Bold WRONG/CORRECT pair that differs only by the presence of ``**``.
- ``conversation-protocol.md`` and ``conversation-examples.md`` render the
  ``🛑 STOP`` marker in plain text (no bold on the STOP marker).

All tests are deterministic: they read fixed on-disk steering content, use no
randomness, no wall-clock time, and no external state.

Feature: question-visibility

Validates: Requirements R4.1, R4.2, R4.3, R4.4, R4.5, R5.1, R5.3, R5.4, R7.5
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages).
# Kept for parity with the rest of the suite; the integration class below
# imports ``validate_behavior_rules`` from here.
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_behavior_rules  # noqa: E402

_VALIDATE_SCRIPT: Path = Path(_SCRIPTS_DIR) / "validate_behavior_rules.py"

# ---------------------------------------------------------------------------
# Steering file paths (same resolution pattern used across the suite)
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_AGENT_BEHAVIOR_RULES: Path = _STEERING_DIR / "agent-behavior-rules.md"
_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"
_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_CONVERSATION_EXAMPLES: Path = _STEERING_DIR / "conversation-examples.md"

_POINTER = "\U0001f449"  # 👉
_STOP = "\U0001f6d1"  # 🛑
_STOP_MARKER = f"{_STOP} STOP"


# ---------------------------------------------------------------------------
# Helpers (pure, deterministic)
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file.

    Args:
        path: The steering file to read.

    Returns:
        The full file contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _section(content: str, heading_prefix: str) -> str:
    """Return the body of the level-2 section whose heading starts with a prefix.

    The body runs from the line after the matched ``## `` heading up to (but not
    including) the next level-2 (``## ``) heading. ``### `` subsections are kept
    as part of the body.

    Args:
        content: The full Markdown text to search.
        heading_prefix: The heading text (or prefix) to locate, e.g.
            ``"## Rule 4"`` or ``"## Self-Check"``.

    Returns:
        The section body text (may be empty).

    Raises:
        AssertionError: If no matching level-2 heading is found.
    """
    lines = content.splitlines()
    start: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith("## ") and line.strip().startswith(heading_prefix):
            start = idx
            break
    assert start is not None, f"heading {heading_prefix!r} not found"

    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def _strip_quote(line: str) -> str:
    """Strip leading Markdown blockquote markers and surrounding whitespace.

    Args:
        line: A single line of Markdown.

    Returns:
        The line with any leading ``>`` blockquote markers removed.
    """
    stripped = line.lstrip()
    while stripped.startswith(">"):
        stripped = stripped[1:].lstrip()
    return stripped


def _non_empty_lines(section_text: str) -> list[str]:
    """Return the right-trimmed, non-blank lines of a section body.

    Args:
        section_text: A section body produced by :func:`_section`.

    Returns:
        The list of non-blank lines with trailing whitespace removed.
    """
    return [ln.rstrip() for ln in section_text.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBoldQuestionSteering:
    """Content assertions for the bold-question rule in authoritative files.

    Validates: Requirements R4.1, R4.2, R4.3, R4.4, R4.5, R5.1, R5.3, R5.4, R7.5
    """

    # -- agent-behavior-rules.md Rule 4 (R4.1) ---------------------------------

    def test_behavior_rules_rule4_states_bold_clause(self) -> None:
        """Rule 4 states the question text is bold, additive to 👉, not a swap.

        Validates: Requirement R4.1
        """
        rule4 = _section(_read(_AGENT_BEHAVIOR_RULES), "## Rule 4")
        lower = rule4.lower()
        assert "wrap the question text" in lower, (
            "Rule 4 must state that the question text is wrapped in bold"
        )
        assert "bold" in lower, "Rule 4 must mention bold"
        assert "in addition to" in lower and _POINTER in rule4, (
            "Rule 4 must state bold is added in addition to the 👉 pointer"
        )
        assert "never as a replacement" in lower, (
            "Rule 4 must state bold is not a replacement for the 👉 pointer"
        )

    # -- agent-instructions.md Communication (R4.2) ----------------------------

    def test_agent_instructions_communication_states_bold_clause(self) -> None:
        """Communication section prefixes with 👉 AND wraps question text in bold.

        Validates: Requirement R4.2
        """
        comm = _section(_read(_AGENT_INSTRUCTIONS), "## Communication")
        lower = comm.lower()
        assert _POINTER in comm, "Communication section must reference the 👉 pointer"
        assert "prefix input-required questions with" in lower, (
            "Communication section must state input-required prompts are 👉-prefixed"
        )
        assert "wrap the question text in bold" in lower, (
            "Communication section must state the question text is wrapped in bold"
        )

    # -- conversation-protocol.md distinct bold rule (R4.3, R7.1, R7.3, R7.5) --

    def test_protocol_has_distinct_bold_rule_section(self) -> None:
        """conversation-protocol.md has a distinct '## Bold Question Text' rule.

        The rule states bold is additive (not a replacement), that choice
        questions bold only the lead, that bold is presentational and does not
        change the One Question Rule (count driven by 👉), and that 🛑 STOP stays
        plain.

        Validates: Requirements R4.3, R7.1, R7.3, R7.5
        """
        content = _read(_CONVERSATION_PROTOCOL)
        assert re.search(r"^## Bold Question Text\s*$", content, re.MULTILINE), (
            "conversation-protocol.md must contain a '## Bold Question Text' heading"
        )
        rule = _section(content, "## Bold Question Text")
        lower = rule.lower()

        assert "leading question is wrapped in" in lower and "bold" in lower, (
            "Bold rule must state the leading question's text is wrapped in bold"
        )
        assert "additive" in lower and "replacement" in lower, (
            "Bold rule must state bold is additive and not a replacement for 👉"
        )
        assert "bold the lead only" in lower, (
            "Bold rule must state a choice question bolds only the lead question"
        )
        assert "does not alter the one question rule" in lower, (
            "Bold rule must state bold does not alter the One Question Rule"
        )
        assert "unaffected by the presence" in lower and "occurrences" in lower, (
            "Bold rule must state the question count is driven by 👉 and unaffected "
            "by bold markers"
        )
        assert _STOP_MARKER in rule and "stays plain" in lower, (
            "Bold rule must state the 🛑 STOP marker stays plain"
        )

    def test_protocol_preoutput_checklist_has_bold_item(self) -> None:
        """Pre-Output Validation Checklist has a bold-question check item.

        Validates: Requirement R4.4
        """
        checklist = _section(
            _read(_CONVERSATION_PROTOCOL), "## Pre-Output Validation Checklist"
        )
        lower = checklist.lower()
        assert "bold-question check" in lower, (
            "Pre-Output Validation Checklist must include a bold-question check item"
        )
        assert "wrapped in bold" in lower, (
            "Bold checklist item must require the closing question's text be bold"
        )

    def test_protocol_self_check_has_bold_item(self) -> None:
        """Self-Check section has an item verifying the closing question is bold.

        Validates: Requirement R4.5
        """
        self_check = _section(_read(_CONVERSATION_PROTOCOL), "## Self-Check")
        lower = self_check.lower()
        assert "bold emphasis" in lower, (
            "Self-Check must include an item about bold emphasis on the closing question"
        )
        assert "lack bold emphasis" in lower, (
            "Self-Check bold item must verify the closing question does not lack bold"
        )

    # -- conversation-examples.md CORRECT examples are bold (R5.1) -------------

    def test_examples_correct_questions_are_bold(self) -> None:
        """Every 👉 question line in a (CORRECT) example is wrapped in bold.

        Covers non-choice CORRECT examples (R5.1) and the bold lead of choice
        CORRECT examples (R5.4). Numbered option lines never start with 👉, so
        they are not required to be bold by this check.

        Validates: Requirements R5.1, R5.4
        """
        content = _read(_CONVERSATION_EXAMPLES)
        lines = content.splitlines()

        checked_any = False
        current_is_correct = False
        for line in lines:
            if line.startswith("## "):
                current_is_correct = "(CORRECT)" in line
                continue
            if not current_is_correct:
                continue
            body = _strip_quote(line)
            if body.startswith(_POINTER):
                checked_any = True
                assert "**" in line, (
                    f"CORRECT example question line must be bold: {line!r}"
                )

        assert checked_any, (
            "Expected at least one 👉 question line inside a (CORRECT) example"
        )

    def test_examples_choice_options_stay_plain(self) -> None:
        """CORRECT choice examples bold the lead but leave options in plain text.

        Validates: Requirement R5.4
        """
        content = _read(_CONVERSATION_EXAMPLES)
        for heading in ("## Compound Choice (CORRECT)", "## Compound Either/Or (CORRECT)"):
            section = _section(content, heading)
            # Lead question line is bold.
            lead_lines = [
                ln for ln in section.splitlines() if _strip_quote(ln).startswith(_POINTER)
            ]
            assert lead_lines, f"{heading} must contain a 👉 lead question"
            assert all("**" in ln for ln in lead_lines), (
                f"{heading} lead question must be bold"
            )
            # Numbered option lines carry no bold markers.
            option_lines = [
                ln
                for ln in section.splitlines()
                if re.match(r"^\d+\.\s", _strip_quote(ln))
            ]
            assert option_lines, f"{heading} must contain numbered options"
            assert all("**" not in ln for ln in option_lines), (
                f"{heading} numbered options must stay in plain text"
            )

    # -- Missing-Bold pair differs only by ** (R5.3) ---------------------------

    def test_examples_missing_bold_pair_differs_only_by_bold(self) -> None:
        """The Missing-Bold WRONG/CORRECT pair differs only in the presence of **.

        Validates: Requirement R5.3
        """
        content = _read(_CONVERSATION_EXAMPLES)
        assert re.search(r"^## Missing-Bold \(WRONG\)\s*$", content, re.MULTILINE), (
            "conversation-examples.md must contain a '## Missing-Bold (WRONG)' heading"
        )
        assert re.search(r"^## Missing-Bold \(CORRECT\)\s*$", content, re.MULTILINE), (
            "conversation-examples.md must contain a '## Missing-Bold (CORRECT)' heading"
        )

        wrong_lines = _non_empty_lines(_section(content, "## Missing-Bold (WRONG)"))
        correct_lines = _non_empty_lines(_section(content, "## Missing-Bold (CORRECT)"))

        assert wrong_lines, "Missing-Bold (WRONG) must have example content"
        assert correct_lines, "Missing-Bold (CORRECT) must have example content"

        assert all("**" not in ln for ln in wrong_lines), (
            "Missing-Bold (WRONG) must be intentionally un-bolded"
        )
        assert any("**" in ln for ln in correct_lines), (
            "Missing-Bold (CORRECT) must wrap the question text in bold"
        )
        assert [ln.replace("**", "") for ln in correct_lines] == wrong_lines, (
            "Missing-Bold pair must differ ONLY in the presence of bold markers"
        )

    # -- 🛑 STOP marker stays plain (R7.5) -------------------------------------

    def test_protocol_stop_marker_is_plain(self) -> None:
        """conversation-protocol.md renders the 🛑 STOP marker without bold.

        Validates: Requirement R7.5
        """
        self._assert_stop_marker_plain(_CONVERSATION_PROTOCOL)

    def test_examples_stop_marker_is_plain(self) -> None:
        """conversation-examples.md renders the 🛑 STOP marker without bold.

        Validates: Requirement R7.5
        """
        self._assert_stop_marker_plain(_CONVERSATION_EXAMPLES)

    @staticmethod
    def _assert_stop_marker_plain(path: Path) -> None:
        """Assert every 🛑 STOP marker line in ``path`` carries no bold markers.

        A STOP marker line is a line whose content (after stripping blockquote
        markers) begins with ``🛑 STOP``. Prose that merely mentions the marker
        (e.g. a bolded label) does not begin with the marker and is not checked.

        Args:
            path: The steering file to inspect.
        """
        content = _read(path)
        assert _STOP_MARKER in content, f"{path.name} must contain a 🛑 STOP marker"
        assert f"**{_STOP_MARKER}**" not in content, (
            f"{path.name} must not wrap the 🛑 STOP marker in bold"
        )

        marker_lines = [
            line
            for line in content.splitlines()
            if _strip_quote(line).startswith(_STOP_MARKER)
        ]
        assert marker_lines, f"{path.name} must render a 🛑 STOP marker line"
        for line in marker_lines:
            assert "**" not in line, (
                f"{path.name} 🛑 STOP marker line must be plain (no bold): {line!r}"
            )


class TestBoldQuestionSteeringIntegration:
    """Integration assertions over the real ``steering/`` directory.

    Now that every question-bearing steering file has been converted, the
    behavior-rules validator must report zero Rule 4 (bold-question) violations
    across the whole directory. This exercises the validator end-to-end against
    the live on-disk content rather than curated fixtures, covering consistent
    application of the bold cue across every module and workflow context.

    All tests are deterministic: they read fixed on-disk steering content, use
    no randomness, no wall-clock time, and no external state.

    Validates: Requirements R11.1, R11.2, R11.3, R1.2, R1.4, R1.5, R3.1, R3.2,
    R3.3
    """

    def test_no_rule4_violations_across_steering_dir(self) -> None:
        """Every ``steering/*.md`` file is free of Rule 4 bold-question violations.

        Runs ``validate_steering_file()`` over every Markdown file in the actual
        steering directory and asserts that no leading (👉) question is left
        without a balanced bold span. The assertion message enumerates any
        ``(file, line, message)`` offenders so a future regression is easy to
        diagnose.

        Validates: Requirements R11.1, R11.2, R11.3, R1.2, R1.4, R1.5, R3.1,
            R3.2, R3.3
        """
        md_files = sorted(_STEERING_DIR.glob("*.md"))
        assert md_files, f"no steering *.md files found under {_STEERING_DIR}"

        offenders: list[str] = []
        for path in md_files:
            for violation in validate_behavior_rules.validate_steering_file(path):
                if violation.rule == 4:
                    offenders.append(
                        f"  {path.name}:{violation.line_number}: {violation.message}"
                    )

        assert not offenders, (
            "Expected zero Rule 4 (bold-question) violations across the steering "
            "directory now that conversion is complete, but found:\n"
            + "\n".join(offenders)
        )

    def test_check_cli_exits_zero_over_steering_dir(self) -> None:
        """The ``--check`` CLI exits 0 over the real steering directory.

        Mirrors how CI invokes the validator (subprocess against the live
        steering ``*.md`` files) and confirms a clean pass, corroborating the
        direct-API check above.

        Validates: Requirements R11.1, R11.2, R11.3
        """
        md_files = sorted(_STEERING_DIR.glob("*.md"))
        assert md_files, f"no steering *.md files found under {_STEERING_DIR}"

        result = subprocess.run(
            [
                sys.executable,
                str(_VALIDATE_SCRIPT),
                "--check",
                *[str(path) for path in md_files],
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"--check exited {result.returncode} over the steering directory:\n"
            f"{result.stdout}\n{result.stderr}"
        )
