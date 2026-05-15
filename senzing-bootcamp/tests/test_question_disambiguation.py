"""Test that no steering file contains compound 👉 questions.

Scans all steering files for 👉 question blocks that contain two or more
semantically distinct sub-questions (compound questions). A compound question
is one where a short answer ("yes"/"no") has multiple valid interpretations.

Feature: disambiguate-compound-questions
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"

# Pattern: a question mark followed (within 80 chars) by a question-starting word
_COMPOUND_PATTERN = re.compile(
    r"\?\s*.{0,80}?\b(Does|Is|Are|Would|Should|Could|Can|Will|Anything|Or\s)\b",
    re.IGNORECASE,
)

# Only check lines that are part of a 👉 question block
_QUESTION_PREFIX = "👉"

# Fenced code block delimiters
_CODE_FENCE_RE = re.compile(r"^(\s*```|~~~)")

# WRONG violation example header pattern
_WRONG_HEADER_RE = re.compile(r"^#{1,6}\s+.*\bWRONG\b", re.IGNORECASE)

# CORRECT header pattern (ends a WRONG section)
_CORRECT_HEADER_RE = re.compile(r"^#{1,6}\s+.*\bCORRECT\b", re.IGNORECASE)


class TestQuestionDisambiguation:
    """Feature: disambiguate-compound-questions

    For any 👉 question in any steering file, the question text must not
    contain a compound pattern (two or more question marks indicating
    multiple sub-questions within a single prompt).

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    """

    def _find_compound_questions(self) -> list[tuple[str, int, str]]:
        """Scan all steering files for compound 👉 questions.

        Skips:
        - Content inside fenced code blocks (``` or ~~~)
        - Lines inside "WRONG" violation example sections (they intentionally
          show bad patterns)

        Returns:
            List of (filename, line_number, offending_text) tuples.
        """
        violations: list[tuple[str, int, str]] = []

        for md_file in sorted(_STEERING_DIR.glob("*.md")):
            lines = md_file.read_text(encoding="utf-8").splitlines()
            in_code_block = False
            in_wrong_section = False
            in_question_block = False
            question_text = ""
            question_start_line = 0

            for i, line in enumerate(lines, start=1):
                # Track fenced code blocks — skip everything inside them
                if _CODE_FENCE_RE.match(line):
                    in_code_block = not in_code_block
                    # If we were accumulating a question block, end it
                    if in_question_block:
                        in_question_block = False
                        question_text = ""
                    continue

                if in_code_block:
                    continue

                # Track WRONG violation example sections — skip them
                if _WRONG_HEADER_RE.match(line):
                    in_wrong_section = True
                    # End any active question block
                    if in_question_block:
                        in_question_block = False
                        question_text = ""
                    continue

                # A CORRECT header or any other heading ends a WRONG section
                if in_wrong_section:
                    if _CORRECT_HEADER_RE.match(line) or re.match(r"^#{1,6}\s+", line):
                        in_wrong_section = False
                    else:
                        continue

                # Detect start of a 👉 question block
                if _QUESTION_PREFIX in line:
                    # If we were already in a question block, check the previous one
                    if in_question_block and question_text.count("?") >= 2:
                        if _COMPOUND_PATTERN.search(question_text):
                            violations.append(
                                (md_file.name, question_start_line, question_text.strip())
                            )

                    in_question_block = True
                    question_text = line
                    question_start_line = i
                elif in_question_block:
                    # Question blocks end at blank lines, STOP markers, or headings
                    if (
                        line.strip() == ""
                        or "🛑" in line
                        or "STOP" in line
                        or re.match(r"^#{1,6}\s+", line)
                    ):
                        # Check the accumulated question text
                        if question_text.count("?") >= 2:
                            if _COMPOUND_PATTERN.search(question_text):
                                violations.append(
                                    (md_file.name, question_start_line, question_text.strip())
                                )
                        in_question_block = False
                        question_text = ""
                    else:
                        question_text += " " + line

            # Check final block if file doesn't end with a terminator
            if in_question_block and question_text.count("?") >= 2:
                if _COMPOUND_PATTERN.search(question_text):
                    violations.append(
                        (md_file.name, question_start_line, question_text.strip())
                    )

        return violations

    def test_no_compound_questions_in_steering_files(self) -> None:
        """All 👉 questions in steering files must be single, unambiguous questions.

        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
        """
        violations = self._find_compound_questions()

        if violations:
            msg_parts = ["Compound questions found in steering files:\n"]
            for filename, line_num, text in violations:
                msg_parts.append(f"  {filename}:{line_num}: {text[:120]}")
            pytest.fail("\n".join(msg_parts))
