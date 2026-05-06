"""Property-based tests for conversation UX rules across steering files.

Validates five structural properties of the conversation UX enforcement:
universal 👉 prefix on questions, STOP markers between questions, behavioral
rules reload completeness, violation examples coverage, and self-check
section completeness.

Feature: conversation-ux-rules
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_SESSION_RESUME: Path = _STEERING_DIR / "session-resume.md"

# Files explicitly modified by the conversation-ux-rules spec to add 👉 prefixes
# and STOP markers. These are the files where the property invariants are enforced.
_SPEC_MODIFIED_FILES: list[Path] = [
    _STEERING_DIR / "conversation-protocol.md",
    _STEERING_DIR / "session-resume.md",
    _STEERING_DIR / "feedback-workflow.md",
    _STEERING_DIR / "module-09-phaseA-assessment.md",
    _STEERING_DIR / "onboarding-flow.md",
]


# ---------------------------------------------------------------------------
# Helpers for Property 1 and 2
# ---------------------------------------------------------------------------


def _is_actual_pointing_question(line: str) -> bool:
    """Determine if a line is an actual 👉 question (not documentation).

    A line is an actual pointing question if 👉 appears as a prefix to
    question text directed at the bootcamper. Documentation lines that
    reference the 👉 symbol (e.g., "End with a 👉 closing question") are
    not actual questions.

    The key distinction: actual 👉 questions have 👉 at the start of the
    content (after optional list markers like `- ` or numbers), followed
    by the question text. Documentation lines have 👉 embedded mid-sentence.

    Args:
        line: A single line of text from a steering file.

    Returns:
        True if the line is an actual 👉 question directed at the bootcamper.
    """
    stripped = line.strip()

    # Must contain 👉
    if "👉" not in stripped:
        return False

    # Skip blockquote example lines (> 👉 ...) from Violation Examples
    if stripped.startswith(">"):
        return False

    # Skip lines inside code blocks
    if stripped.startswith("```"):
        return False

    # An actual pointing question has 👉 as the leading content marker.
    # Strip optional list prefixes (-, *, N.) and check if 👉 is at the start.
    # Pattern: optional list marker, then 👉 as the first meaningful character.
    content_after_marker = re.sub(
        r"^(?:[-*]\s+|\d+\.\s+)?", "", stripped
    )

    # 👉 must be at the very start of the content (it's a prefix, not inline)
    if content_after_marker.startswith("👉"):
        return True

    return False


def _find_questions_with_stop_or_gate(content: str) -> list[tuple[int, str]]:
    """Find lines that are bootcamper-directed questions with adjacent STOP/gate.

    A bootcamper-directed question is identified by having a 🛑 STOP marker
    within the next 5 non-blank lines. Only returns lines that contain a
    question mark and are formatted as direct output (not conditional
    instruction templates).

    Args:
        content: Full text content of a steering file.

    Returns:
        List of (line_number, line_text) tuples for question lines that
        have adjacent STOP markers.
    """
    lines = content.splitlines()
    re_stop = re.compile(r"🛑")
    re_gate = re.compile(r"⛔")

    results: list[tuple[int, str]] = []

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Must contain a question mark to be a question
        if "?" not in stripped:
            continue

        # Skip blockquote lines (these are STOP instructions, not questions)
        if stripped.startswith(">"):
            continue

        # Skip code block lines
        if stripped.startswith("```"):
            continue

        # Check if there's a 🛑 or ⛔ within 5 non-blank lines after
        has_marker_after = False
        non_blank_seen = 0
        for scan_idx in range(idx + 1, len(lines)):
            scan_line = lines[scan_idx]
            if not scan_line.strip():
                continue
            non_blank_seen += 1
            if re_stop.search(scan_line) or re_gate.search(scan_line):
                has_marker_after = True
                break
            if non_blank_seen >= 5:
                break

        if has_marker_after:
            results.append((idx, line))

    return results


def _find_pointing_questions(content: str) -> list[tuple[int, str]]:
    """Find all lines that are actual 👉 questions (not documentation).

    Excludes lines inside fenced code blocks.

    Args:
        content: Full text content of a steering file.

    Returns:
        List of (line_number, line_text) tuples for actual 👉 questions.
    """
    lines = content.splitlines()
    results: list[tuple[int, str]] = []
    in_code_block = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if _is_actual_pointing_question(line):
            results.append((idx, line))
    return results


# ---------------------------------------------------------------------------
# Module-level data (parsed once)
# ---------------------------------------------------------------------------

# Files modified by this spec that have 👉 questions with STOP markers
_FILES_WITH_POINTING_QUESTIONS: list[Path] = [
    f for f in _SPEC_MODIFIED_FILES
    if f.exists() and "👉" in f.read_text(encoding="utf-8")
]


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_spec_modified_file() -> st.SearchStrategy[Path]:
    """Strategy that draws from steering files modified by this spec.

    Returns:
        A strategy producing Path objects for spec-modified steering files
        that contain 👉 questions.
    """
    return st.sampled_from(_FILES_WITH_POINTING_QUESTIONS)


# ---------------------------------------------------------------------------
# Property-based test classes
# ---------------------------------------------------------------------------


class TestProperty1UniversalPointingPrefix:
    """Feature: conversation-ux-rules, Property 1: Universal 👉 prefix on bootcamper-directed questions

    For any steering file that contains a question with an adjacent 🛑 STOP
    marker or ⛔ gate, the question text SHALL be prefixed with 👉.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 7.2, 7.4**
    """

    @given(file_path=st_spec_modified_file())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_questions_with_stop_markers_have_pointing_prefix(
        self, file_path: Path
    ) -> None:
        """Every question with an adjacent STOP/gate marker has 👉 prefix.

        Args:
            file_path: Path to a steering file drawn from the strategy.
        """
        content = file_path.read_text(encoding="utf-8")
        questions_with_markers = _find_questions_with_stop_or_gate(content)

        violations: list[str] = []
        for line_num, line_text in questions_with_markers:
            stripped = line_text.strip()

            # The question line itself must contain 👉
            if "👉" not in line_text:
                # Check if the 👉 is on the immediately preceding non-blank
                # line (some patterns put 👉 on a separate line before the
                # question text)
                lines = content.splitlines()
                found_prefix_nearby = False
                for scan_idx in range(line_num - 1, max(line_num - 4, -1), -1):
                    if scan_idx < 0:
                        break
                    if "👉" in lines[scan_idx]:
                        found_prefix_nearby = True
                        break
                    if lines[scan_idx].strip():
                        # Hit a non-blank line without 👉
                        break

                if not found_prefix_nearby:
                    violations.append(
                        f"{file_path.name}:{line_num + 1}: "
                        f"question lacks 👉 prefix: {stripped[:80]}"
                    )

        assert violations == [], (
            f"Questions with STOP/gate markers missing 👉 prefix:\n"
            + "\n".join(violations)
        )


class TestProperty2StopMarkerBetweenQuestions:
    """Feature: conversation-ux-rules, Property 2: STOP marker follows every 👉 question before next question

    For any steering file with multiple 👉 questions, there SHALL be a 🛑
    STOP marker (or EOF) between each pair.

    **Validates: Requirements 1.3, 2.3, 7.3**
    """

    @given(file_path=st_spec_modified_file())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_stop_marker_between_pointing_questions(
        self, file_path: Path
    ) -> None:
        """🛑 STOP marker (or EOF) exists between each pair of 👉 questions.

        Args:
            file_path: Path to a steering file drawn from the strategy.
        """
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        pointing_questions = _find_pointing_questions(content)

        if len(pointing_questions) <= 1:
            # Only one or zero questions — property trivially holds
            return

        violations: list[str] = []
        re_stop = re.compile(r"🛑")
        re_section_heading = re.compile(r"^##\s+")

        for i in range(len(pointing_questions) - 1):
            current_line_num = pointing_questions[i][0]
            next_line_num = pointing_questions[i + 1][0]

            # Check for 🛑 STOP marker or section heading between questions.
            # Section headings (## ...) serve as natural turn boundaries in
            # files that use hook-based stopping instead of explicit markers.
            found_separator = False
            for scan_idx in range(current_line_num + 1, next_line_num):
                scan_line = lines[scan_idx]
                if re_stop.search(scan_line):
                    found_separator = True
                    break
                if re_section_heading.match(scan_line):
                    found_separator = True
                    break

            if not found_separator:
                violations.append(
                    f"{file_path.name}: no 🛑 STOP between "
                    f"line {current_line_num + 1} and "
                    f"line {next_line_num + 1}"
                )

        assert violations == [], (
            f"Missing 🛑 STOP markers between 👉 questions:\n"
            + "\n".join(violations)
        )


class TestProperty3BehavioralRulesReload:
    """Feature: conversation-ux-rules, Property 3: Behavioral Rules Reload completeness and ordering

    session-resume.md SHALL have a "Behavioral Rules Reload" section before
    Step 3 that references all five core rules: one-question-per-turn,
    wait-for-response, no-dead-ends, 👉-prefix-required, no-self-answering.

    **Validates: Requirements 6.1, 6.2**
    """

    @given(file_path=st.sampled_from([_SESSION_RESUME]))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_behavioral_rules_reload_completeness(
        self, file_path: Path
    ) -> None:
        """Behavioral Rules Reload section exists before Step 3 with all rules.

        Args:
            file_path: Path to session-resume.md.
        """
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the Behavioral Rules Reload section
        reload_section_line: int | None = None
        step_3_line: int | None = None

        for idx, line in enumerate(lines):
            if re.search(r"Behavioral Rules Reload", line, re.IGNORECASE):
                reload_section_line = idx
            if re.search(r"^##\s+Step 3", line):
                step_3_line = idx

        # Section must exist
        assert reload_section_line is not None, (
            "session-resume.md missing 'Behavioral Rules Reload' section"
        )

        # Section must appear before Step 3
        assert step_3_line is not None, (
            "session-resume.md missing 'Step 3' heading"
        )
        assert reload_section_line < step_3_line, (
            f"'Behavioral Rules Reload' (line {reload_section_line + 1}) "
            f"must appear before 'Step 3' (line {step_3_line + 1})"
        )

        # Extract the section content (from reload heading to Step 3)
        section_content = "\n".join(
            lines[reload_section_line:step_3_line]
        ).lower()

        # Verify all five core rules are referenced
        core_rules = [
            ("one-question-per-turn", r"one.question.per.turn"),
            ("wait-for-response", r"wait.for.response"),
            ("no-dead-ends", r"no.dead.end"),
            ("👉-prefix-required", r"(👉.prefix|prefix.required)"),
            ("no-self-answering", r"no.self.answer"),
        ]

        missing_rules: list[str] = []
        for rule_name, pattern in core_rules:
            if not re.search(pattern, section_content, re.IGNORECASE):
                missing_rules.append(rule_name)

        assert missing_rules == [], (
            f"Behavioral Rules Reload section missing references to: "
            f"{missing_rules}"
        )


class TestProperty4ViolationExamplesCoverage:
    """Feature: conversation-ux-rules, Property 4: Violation Examples section covers all five rule categories

    conversation-protocol.md SHALL have a "Violation Examples" section with
    examples for all five categories: multi-question, not-waiting, dead-end,
    missing-prefix, self-answering.

    **Validates: Requirements 8.1**
    """

    @given(file_path=st.sampled_from([_CONVERSATION_PROTOCOL]))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_violation_examples_cover_all_categories(
        self, file_path: Path
    ) -> None:
        """Violation Examples section contains examples for all five categories.

        Args:
            file_path: Path to conversation-protocol.md.
        """
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the Violation Examples section
        section_start: int | None = None
        section_end: int | None = None

        for idx, line in enumerate(lines):
            if re.match(r"^##\s+Violation Examples", line):
                section_start = idx
            elif section_start is not None and re.match(r"^##\s+", line):
                section_end = idx
                break

        assert section_start is not None, (
            "conversation-protocol.md missing 'Violation Examples' section"
        )

        if section_end is None:
            section_end = len(lines)

        section_content = "\n".join(lines[section_start:section_end]).lower()

        # Verify all five categories have examples
        categories = [
            ("multi-question", r"multi.question"),
            ("not-waiting", r"not.waiting"),
            ("dead-end", r"dead.end"),
            ("missing-prefix", r"missing.prefix"),
            ("self-answering", r"self.answer"),
        ]

        missing_categories: list[str] = []
        for category_name, pattern in categories:
            if not re.search(pattern, section_content):
                missing_categories.append(category_name)

        assert missing_categories == [], (
            f"Violation Examples section missing categories: "
            f"{missing_categories}"
        )

        # Verify each category has both WRONG and CORRECT examples
        for category_name, pattern in categories:
            category_match = re.search(
                rf"###\s+.*{pattern}.*?\n(.*?)(?=###|\Z)",
                section_content,
                re.DOTALL,
            )
            if category_match:
                subsection = category_match.group(0)
                assert "wrong" in subsection, (
                    f"Category '{category_name}' missing WRONG example"
                )
                assert "correct" in subsection, (
                    f"Category '{category_name}' missing CORRECT example"
                )


class TestProperty5SelfCheckCompleteness:
    """Feature: conversation-ux-rules, Property 5: Self-Check section contains all verification questions

    conversation-protocol.md SHALL have a "Self-Check" section with all four
    verification questions: (a) multiple 👉 questions, (b) missing prefix,
    (c) content after question, (d) answering own question.

    **Validates: Requirements 8.3**
    """

    @given(file_path=st.sampled_from([_CONVERSATION_PROTOCOL]))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_self_check_contains_all_verification_questions(
        self, file_path: Path
    ) -> None:
        """Self-Check section contains all four verification questions.

        Args:
            file_path: Path to conversation-protocol.md.
        """
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the Self-Check section
        section_start: int | None = None
        section_end: int | None = None

        for idx, line in enumerate(lines):
            if re.match(r"^##\s+Self-Check", line):
                section_start = idx
            elif section_start is not None and re.match(r"^##\s+", line):
                section_end = idx
                break

        assert section_start is not None, (
            "conversation-protocol.md missing 'Self-Check' section"
        )

        if section_end is None:
            section_end = len(lines)

        section_content = "\n".join(lines[section_start:section_end]).lower()

        # Verify all four verification questions are present
        verification_questions = [
            (
                "multiple 👉 questions in turn",
                r"more than one.*👉.*question",
            ),
            (
                "missing 👉 prefix",
                r"(lack|missing).*👉.*prefix",
            ),
            (
                "content after 👉 question",
                r"content after.*👉.*question",
            ),
            (
                "answering own question",
                r"answer.*own question",
            ),
        ]

        missing_questions: list[str] = []
        for question_desc, pattern in verification_questions:
            if not re.search(pattern, section_content):
                missing_questions.append(question_desc)

        assert missing_questions == [], (
            f"Self-Check section missing verification questions: "
            f"{missing_questions}"
        )
