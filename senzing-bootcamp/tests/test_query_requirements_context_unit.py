"""Unit tests for query requirements context steering file structure.

Verifies that the Module 7 steering file Step 1 contains the correct
business-problem-first flow with IF/ELSE branching, derivation instructions,
confirmation phrasing, attribution, and fallback handling.

Feature: query-requirements-context
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# sys.path manipulation to import scripts (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from parse_business_problem import (  # noqa: E402
    BusinessProblemContent,
    derive_query_requirements,
    has_usable_content,
    parse_business_problem,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_MODULE_07: Path = _STEERING_DIR / "module-07-phase1-query-visualize.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def steering_content() -> str:
    """Load the Module 7 steering file content."""
    return _MODULE_07.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def step_1_content(steering_content: str) -> str:
    """Extract Step 1 content from the steering file.

    Returns the text between the Step 1 heading and the Step 2 heading.
    """
    lines = steering_content.splitlines()
    step_1_start: int | None = None
    step_1_end: int | None = None

    for idx, line in enumerate(lines):
        if re.match(r"^1\.\s+\*\*Define query requirements\*\*", line):
            step_1_start = idx
        elif step_1_start is not None and re.match(r"^2\.\s+\*\*", line):
            step_1_end = idx
            break

    assert step_1_start is not None, (
        "Module 7 steering file must contain Step 1: 'Define query requirements'"
    )
    if step_1_end is None:
        step_1_end = len(lines)

    return "\n".join(lines[step_1_start:step_1_end])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSteeringFileStructure:
    """Unit tests validating Module 7 Step 1 steering file structure.

    Each test verifies a specific structural requirement of the
    business-problem-first flow in the steering file.
    """

    def test_read_instruction_before_any_ask_directive(
        self, step_1_content: str
    ) -> None:
        """Step 1 contains read instruction before any 'Ask:' directive or pointing question.

        The agent must read docs/business_problem.md as the first action
        before presenting any query-related question to the bootcamper.

        Validates: Requirements 1.1, 3.1, 3.5
        """
        lines = step_1_content.splitlines()

        read_line: int | None = None
        first_ask_line: int | None = None
        first_pointing_line: int | None = None

        for idx, line in enumerate(lines):
            if "docs/business_problem.md" in line and "read" in line.lower():
                if read_line is None:
                    read_line = idx
            if re.search(r"Ask:", line) and first_ask_line is None:
                first_ask_line = idx
            if "\u0001f449" in line and first_pointing_line is None:
                first_pointing_line = idx

        assert read_line is not None, (
            "Step 1 must contain an instruction to read docs/business_problem.md"
        )

        if first_ask_line is not None:
            assert read_line < first_ask_line, (
                f"Read instruction (line {read_line}) must appear before "
                f"first 'Ask:' directive (line {first_ask_line})"
            )

        if first_pointing_line is not None:
            assert read_line < first_pointing_line, (
                f"Read instruction (line {read_line}) must appear before "
                f"first pointing question (line {first_pointing_line})"
            )

    def test_primary_path_includes_derivation_instructions(
        self, step_1_content: str
    ) -> None:
        """Step 1 primary path includes derivation instructions.

        The agent must derive query requirements from success criteria
        and/or desired outputs found in the business problem document.

        Validates: Requirements 1.2, 3.2
        """
        content_lower = step_1_content.lower()

        assert "derive" in content_lower, (
            "Step 1 must include derivation instructions (word 'derive')"
        )
        assert "success criteria" in content_lower or "success criterion" in content_lower, (
            "Step 1 must reference success criteria as a derivation source"
        )
        assert "desired output" in content_lower, (
            "Step 1 must reference desired outputs as a derivation source"
        )
        # Verify bounded derivation (1-10)
        assert re.search(r"1\s*(and|to)\s*10", step_1_content), (
            "Step 1 must specify derivation bounds of 1 to 10 query requirements"
        )

    def test_includes_confirmation_phrasing(self, step_1_content: str) -> None:
        """Step 1 includes confirmation phrasing ('add or change').

        The agent must ask the bootcamper if there is anything to add or
        change, rather than asking them to restate query needs from scratch.

        Validates: Requirements 1.3, 3.3
        """
        assert "add or change" in step_1_content.lower(), (
            "Step 1 must include confirmation phrasing 'add or change'"
        )

    def test_includes_attribution_example_sentence(
        self, step_1_content: str
    ) -> None:
        """Step 1 includes attribution example sentence.

        The agent must reference the source material with an attribution
        sentence so the bootcamper understands where requirements came from.

        Validates: Requirement 1.4
        """
        assert "Based on your business problem from Module 1" in step_1_content, (
            "Step 1 must include the attribution sentence "
            "'Based on your business problem from Module 1'"
        )

    def test_rejection_handler_without_back_references(
        self, step_1_content: str
    ) -> None:
        """Step 1 includes rejection handler without back-references to rejected items.

        When the bootcamper rejects all derived requirements, the agent must
        ask a fresh question without referencing the rejected derivations.

        Validates: Requirement 1.5
        """
        # Find the rejection handler section
        lines = step_1_content.splitlines()
        rejection_start: int | None = None
        rejection_end: int | None = None

        for idx, line in enumerate(lines):
            if "rejects all" in line.lower() or "reject" in line.lower():
                if rejection_start is None:
                    rejection_start = idx
            # The rejection handler ends at the ELSE or next major section
            if rejection_start is not None and rejection_end is None:
                if re.match(r"\s*\*\*ELSE\*\*", line):
                    rejection_end = idx
                    break

        assert rejection_start is not None, (
            "Step 1 must contain a rejection handler for when bootcamper "
            "rejects all derived requirements"
        )

        if rejection_end is None:
            rejection_end = len(lines)

        rejection_section = "\n".join(lines[rejection_start:rejection_end])

        # The rejection handler should mention asking without referencing rejected items
        assert "without referencing" in rejection_section.lower(), (
            "Rejection handler must specify asking without referencing "
            "the rejected items"
        )

    def test_fallback_path_does_not_mention_module_1(
        self, step_1_content: str
    ) -> None:
        """Fallback path does not mention Module 1 or missing documents.

        When falling back to the open-ended question, the agent must not
        reference Module 1, prior steps, or missing documents in the actual
        fallback content (the ELSE condition line itself is structural).

        Validates: Requirement 2.4
        """
        lines = step_1_content.splitlines()
        fallback_start: int | None = None
        fallback_end: int | None = None

        for idx, line in enumerate(lines):
            if re.match(r"\s*\*\*ELSE\*\*", line):
                # Start from the line AFTER the ELSE condition marker
                fallback_start = idx + 1
            elif fallback_start is not None and re.match(r"\s*---", line):
                fallback_end = idx
                break

        assert fallback_start is not None, (
            "Step 1 must contain an ELSE fallback path"
        )

        if fallback_end is None:
            fallback_end = len(lines)

        fallback_content = "\n".join(lines[fallback_start:fallback_end])

        # Fallback content (after the ELSE marker) should not mention
        # Module 1 or missing documents
        assert "module 1" not in fallback_content.lower(), (
            "Fallback path must not mention Module 1"
        )
        assert "missing" not in fallback_content.lower(), (
            "Fallback path must not mention missing documents"
        )

    def test_fallback_path_is_conditional(self, step_1_content: str) -> None:
        """Fallback path is conditional (IF missing/empty).

        The fallback must be triggered by a conditional check - the file
        does not exist OR both sections are missing/empty.

        Validates: Requirement 3.4
        """
        # The ELSE block should be preceded by an IF condition
        assert re.search(
            r"\*\*IF\*\*.*docs/business_problem\.md", step_1_content
        ), (
            "Step 1 must have an IF condition checking docs/business_problem.md"
        )
        assert re.search(r"\*\*ELSE\*\*", step_1_content), (
            "Step 1 must have an ELSE fallback path"
        )
        # Verify the ELSE describes the condition
        lines = step_1_content.splitlines()
        for line in lines:
            if "**ELSE**" in line:
                # The ELSE line or nearby should mention the condition
                assert (
                    "does not exist" in line.lower()
                    or "missing" in line.lower()
                    or "empty" in line.lower()
                ), (
                    "ELSE block must describe the fallback condition "
                    "(file does not exist, or sections missing/empty)"
                )
                break

    def test_open_ended_question_retained_only_as_fallback(
        self, step_1_content: str
    ) -> None:
        """Open-ended question retained only as fallback, not primary path.

        The original open-ended question ('What questions do you need to
        answer with your data?') must only appear in the fallback path or
        rejection handler, not as the primary interaction.

        Validates: Requirements 3.4, 3.5
        """
        open_ended_question = "What questions do you need to answer with your data?"
        lines = step_1_content.splitlines()

        # Find all occurrences of the open-ended question
        occurrences: list[int] = []
        for idx, line in enumerate(lines):
            if open_ended_question in line:
                occurrences.append(idx)

        assert len(occurrences) > 0, (
            "Step 1 must retain the open-ended question somewhere"
        )

        # Find the IF block start (primary path)
        if_line: int | None = None
        else_line: int | None = None
        rejection_line: int | None = None

        for idx, line in enumerate(lines):
            if re.match(r"\s*\*\*IF\*\*", line) and if_line is None:
                if_line = idx
            if re.match(r"\s*\*\*ELSE\*\*", line) and else_line is None:
                else_line = idx
            if "rejects all" in line.lower() and rejection_line is None:
                rejection_line = idx

        assert if_line is not None, "Step 1 must have an IF block"
        assert else_line is not None, "Step 1 must have an ELSE block"

        # Verify the open-ended question does NOT appear in the primary
        # derivation path (between IF and ELSE, excluding rejection handler)
        for occ in occurrences:
            if if_line < occ < else_line:
                # It's in the primary path - only acceptable if it's in
                # the rejection handler (same line or after)
                assert rejection_line is not None and occ >= rejection_line, (
                    f"Open-ended question at line {occ} appears in the "
                    f"primary path before the rejection handler. It should "
                    f"only appear in the fallback or rejection handler."
                )


# ---------------------------------------------------------------------------
# Parsing Logic Tests
# ---------------------------------------------------------------------------


class TestParsingLogic:
    """Unit tests validating parsing logic in parse_business_problem.py.

    Tests cover extraction of success criteria and desired output fields,
    usable content detection, and query requirement derivation.

    Validates: Requirements 1.2, 2.1, 2.2, 2.3
    """

    # --- parse_business_problem tests ---

    def test_parse_business_problem_extracts_success_criteria(self) -> None:
        """parse_business_problem extracts success criteria from well-formed document.

        Validates: Requirement 1.2
        """
        doc = (
            "# Business Problem\n\n"
            "Some intro text.\n\n"
            "## Success Criteria\n"
            "- Reduce duplicate records by 90%\n"
            "- Achieve sub-second query response time\n"
            "- Integrate with existing CRM system\n\n"
            "## Desired Output\n"
            "**Format**: Master list\n"
        )
        result = parse_business_problem(doc)

        assert result.success_criteria == [
            "Reduce duplicate records by 90%",
            "Achieve sub-second query response time",
            "Integrate with existing CRM system",
        ]

    def test_parse_business_problem_extracts_desired_output_fields(self) -> None:
        """parse_business_problem extracts desired output fields.

        Validates: Requirement 1.2
        """
        doc = (
            "## Success Criteria\n"
            "- Some criterion\n\n"
            "## Desired Output\n"
            "**Format**: API\n"
            "**Use case**: Real-time\n"
            "**Integration**: Integrated with Salesforce\n"
        )
        result = parse_business_problem(doc)

        assert result.desired_output_format == "API"
        assert result.desired_output_use_case == "Real-time"
        assert result.desired_output_integration == "Integrated with Salesforce"

    # --- has_usable_content tests ---

    def test_has_usable_content_returns_false_for_empty_document(self) -> None:
        """has_usable_content returns False for empty document.

        Validates: Requirements 2.1, 2.2
        """
        bpc = parse_business_problem("")
        assert has_usable_content(bpc) is False

    def test_has_usable_content_returns_true_when_only_success_criteria(self) -> None:
        """has_usable_content returns True when only success criteria present.

        Validates: Requirement 2.3
        """
        bpc = BusinessProblemContent(
            success_criteria=["Reduce duplicates by 90%"],
            desired_output_format="",
            desired_output_use_case="",
            desired_output_integration="",
        )
        assert has_usable_content(bpc) is True

    def test_has_usable_content_returns_true_when_only_desired_output(self) -> None:
        """has_usable_content returns True when only desired output present.

        Validates: Requirement 2.3
        """
        bpc = BusinessProblemContent(
            success_criteria=[],
            desired_output_format="Master list",
            desired_output_use_case="",
            desired_output_integration="",
        )
        assert has_usable_content(bpc) is True

    # --- derive_query_requirements tests ---

    def test_derive_query_requirements_returns_bounded_list(self) -> None:
        """derive_query_requirements returns bounded list (1-10).

        Validates: Requirement 1.2
        """
        # Create content with more than 10 success criteria
        bpc = BusinessProblemContent(
            success_criteria=[f"Criterion {i}" for i in range(15)],
            desired_output_format="Reports",
            desired_output_use_case="Ongoing",
            desired_output_integration="Standalone",
        )
        result = derive_query_requirements(bpc)

        assert 1 <= len(result) <= 10

    def test_derive_query_requirements_includes_source_attribution(self) -> None:
        """derive_query_requirements includes source attribution for each item.

        Validates: Requirement 1.2
        """
        bpc = BusinessProblemContent(
            success_criteria=["Reduce duplicates by 90%"],
            desired_output_format="API",
            desired_output_use_case="",
            desired_output_integration="",
        )
        result = derive_query_requirements(bpc)

        assert len(result) >= 1
        for item in result:
            assert "requirement" in item, "Each item must have a 'requirement' key"
            assert "source" in item, "Each item must have a 'source' key"
            assert item["requirement"], "Requirement value must be non-empty"
            assert item["source"], "Source value must be non-empty"
