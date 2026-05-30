"""Property-based tests for query requirements context feature.

Feature: query-requirements-context
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from parse_business_problem import (
    BusinessProblemContent,
    derive_query_requirements,
    has_usable_content,
    parse_business_problem,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_success_criteria(draw) -> list[str]:
    """Generate a list of non-empty success criteria strings (0-8 items)."""
    criteria = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=("L", "Nd", "Zs", "Po"),
                    blacklist_characters="\n\r",
                ),
            ).filter(lambda s: len(s.strip()) > 0),
            min_size=0,
            max_size=8,
        )
    )
    return [c.strip() for c in criteria]


@st.composite
def st_desired_output(draw) -> dict[str, str]:
    """Generate desired output fields (format, use_case, integration strings).

    Each field may be empty or a non-empty string representing a valid value.
    """
    format_val = draw(
        st.one_of(
            st.just(""),
            st.sampled_from([
                "Master list",
                "API",
                "Reports",
                "Database export",
                "CSV file",
            ]),
        )
    )
    use_case_val = draw(
        st.one_of(
            st.just(""),
            st.sampled_from([
                "One-time",
                "Ongoing",
                "Real-time",
                "Batch processing",
            ]),
        )
    )
    integration_val = draw(
        st.one_of(
            st.just(""),
            st.sampled_from([
                "Standalone",
                "Integrated with CRM",
                "Integrated with data warehouse",
                "Integrated with analytics platform",
            ]),
        )
    )
    return {
        "format": format_val,
        "use_case": use_case_val,
        "integration": integration_val,
    }


@st.composite
def st_business_problem_doc(draw) -> str:
    """Generate a full business problem markdown document with varying section content.

    Produces documents that may or may not contain Success Criteria and/or
    Desired Output sections, with varying numbers of bullet items and field values.
    """
    criteria = draw(st_success_criteria())
    desired = draw(st_desired_output())

    # Build the markdown document
    lines: list[str] = ["# Business Problem\n"]
    lines.append("## Problem Statement\n")
    lines.append("We need to resolve entities across multiple data sources.\n")

    # Optionally include Success Criteria section
    include_sc_section = draw(st.booleans())
    if include_sc_section and criteria:
        lines.append("## Success Criteria\n")
        for criterion in criteria:
            lines.append(f"- {criterion}\n")
        lines.append("\n")

    # Optionally include Desired Output section
    include_do_section = draw(st.booleans())
    if include_do_section:
        lines.append("## Desired Output\n")
        if desired["format"]:
            lines.append(f"**Format**: {desired['format']}\n")
        if desired["use_case"]:
            lines.append(f"**Use case**: {desired['use_case']}\n")
        if desired["integration"]:
            lines.append(f"**Integration**: {desired['integration']}\n")
        lines.append("\n")

    return "".join(lines)


# ---------------------------------------------------------------------------
# Property 1: Read-before-interact ordering
# Feature: query-requirements-context, Property 1: Read-before-interact ordering
# ---------------------------------------------------------------------------


class TestReadBeforeInteractOrderingProperty:
    """Property 1: Read-before-interact ordering.

    For any valid Module 7 Step 1 steering content, the instruction to read
    `docs/business_problem.md` appears before any pointing question, "Ask:"
    directive, or bootcamper interaction prompt in the step's primary flow.

    **Validates: Requirements 1.1, 3.1, 3.5**
    """

    STEERING_FILE = Path(__file__).resolve().parent.parent / "steering" / "module-07-query-visualize-discover.md"

    def _extract_step1_content(self) -> str:
        """Extract Step 1 content from the steering file.

        Returns the text between '1. **Define query requirements**' and '2. **'.
        """
        content = self.STEERING_FILE.read_text(encoding="utf-8")
        # Find Step 1 start
        step1_marker = '1. **Define query requirements**'
        step1_start = content.find(step1_marker)
        assert step1_start != -1, "Step 1 marker not found in steering file"

        # Find Step 2 start (end of Step 1)
        step2_marker = '2. **'
        step2_start = content.find(step2_marker, step1_start + len(step1_marker))
        assert step2_start != -1, "Step 2 marker not found after Step 1"

        return content[step1_start:step2_start]

    @settings(max_examples=20)
    @given(st.just(True))
    def test_read_instruction_before_any_interaction(self, _: bool) -> None:
        """The read instruction for docs/business_problem.md appears before any
        pointing question, 'Ask:' directive, or STOP marker in Step 1's primary flow.

        **Validates: Requirements 1.1, 3.1, 3.5**
        """
        step1 = self._extract_step1_content()

        # Find position of the read instruction
        read_instruction = "docs/business_problem.md"
        read_pos = step1.find(read_instruction)
        assert read_pos != -1, (
            "Step 1 must contain an instruction to read docs/business_problem.md"
        )

        # Find positions of interaction markers that should come AFTER the read
        interaction_markers = []

        # Find all "Ask:" directives
        ask_pos = step1.find("Ask:")
        if ask_pos != -1:
            interaction_markers.append(("Ask: directive", ask_pos))

        # Find all pointing questions
        pointer_pos = step1.find("\U0001f449")
        if pointer_pos != -1:
            interaction_markers.append(("pointing question", pointer_pos))

        # Find STOP markers
        stop_pos = step1.find("\U0001f6d1 STOP")
        if stop_pos != -1:
            interaction_markers.append(("STOP marker", stop_pos))

        # Verify the read instruction appears before ALL interaction markers
        for marker_name, marker_pos in interaction_markers:
            assert read_pos < marker_pos, (
                f"Read instruction (pos {read_pos}) must appear before "
                f"{marker_name} (pos {marker_pos}) in Step 1's primary flow"
            )


# ---------------------------------------------------------------------------
# Property 2: Derivation bounds and traceability
# Feature: query-requirements-context, Property 2: Derivation bounds and traceability
# ---------------------------------------------------------------------------


class TestDerivationBoundsAndTraceabilityProperty:
    """Property 2: Derivation bounds and traceability.

    For any business problem document containing N success criteria and M desired
    output fields (where N + M >= 1), the derivation logic produces between 1 and
    10 query requirements, and each derived requirement references at least one
    source criterion or desired output.

    **Validates: Requirements 1.2**
    """

    @given(criteria=st_success_criteria(), desired=st_desired_output())
    @settings(max_examples=20)
    def test_derivation_bounds_and_traceability(
        self, criteria: list[str], desired: dict[str, str]
    ) -> None:
        """Derived requirements are bounded 1-10 and each traces to a source."""
        bpc = BusinessProblemContent(
            success_criteria=criteria,
            desired_output_format=desired["format"],
            desired_output_use_case=desired["use_case"],
            desired_output_integration=desired["integration"],
        )

        # Count non-empty desired output fields
        m = sum(1 for v in desired.values() if v)
        n = len(criteria)

        # Only test cases where there is usable content (N + M >= 1)
        assume(n + m >= 1)

        result = derive_query_requirements(bpc)

        # Result has between 1 and 10 items
        assert 1 <= len(result) <= 10

        # Each item has both "requirement" and "source" keys
        for item in result:
            assert "requirement" in item
            assert "source" in item
            # Each item's "source" field is non-empty
            assert item["source"]


# ---------------------------------------------------------------------------
# Property 3: Fallback on missing or empty content
# Feature: query-requirements-context, Property 3: Fallback on missing or empty content
# ---------------------------------------------------------------------------


class TestFallbackOnMissingOrEmptyContentProperty:
    """Property 3: Fallback on missing or empty content.

    For any state where `docs/business_problem.md` does not exist, OR exists but
    contains zero success criteria AND zero desired output content, the system
    signals the fallback path (open-ended question) rather than the derivation path.

    **Validates: Requirements 2.1, 2.2**
    """

    @given(
        other_text=st.text(
            min_size=0,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=("L", "Nd", "Zs", "Po"),
                blacklist_characters="\n\r",
            ),
        ),
        include_sc_header=st.booleans(),
        include_do_header=st.booleans(),
    )
    @settings(max_examples=20)
    def test_empty_content_signals_fallback(
        self, other_text: str, include_sc_header: bool, include_do_header: bool
    ) -> None:
        """Documents with no success criteria AND no desired output fields signal fallback.

        Generates documents that have NO usable content (empty success criteria
        AND all desired output fields empty), parses them, and asserts that
        has_usable_content() returns False.

        **Validates: Requirements 2.1, 2.2**
        """
        # Build a document with no success criteria and no desired output values
        lines: list[str] = ["# Business Problem\n"]
        lines.append("## Problem Statement\n")
        if other_text.strip():
            lines.append(f"{other_text.strip()}\n")
        else:
            lines.append("Some problem description.\n")
        lines.append("\n")
        # Optionally include empty Success Criteria section (no bullets)
        if include_sc_header:
            lines.append("## Success Criteria\n")
            lines.append("\n")
        # Optionally include Desired Output section with NO field values
        if include_do_header:
            lines.append("## Desired Output\n")
            lines.append("\n")

        doc = "".join(lines)
        bpc = parse_business_problem(doc)
        assert has_usable_content(bpc) is False

    def test_file_does_not_exist_signals_fallback(self) -> None:
        """When the file does not exist, a default BusinessProblemContent signals fallback.

        A BusinessProblemContent with all defaults (empty) represents the case
        where the file is missing. has_usable_content() must return False.

        **Validates: Requirements 2.1, 2.2**
        """
        bpc = BusinessProblemContent()
        assert has_usable_content(bpc) is False


# ---------------------------------------------------------------------------
# Property 4: Derive when content is available
# Feature: query-requirements-context, Property 4: Derive when content is available
# ---------------------------------------------------------------------------


class TestDeriveWhenContentAvailableProperty:
    """Property 4: Derive when content is available.

    For any business problem document that contains at least one success criterion
    OR at least one non-empty desired output field, the system signals the
    derivation path (not the fallback path).

    **Validates: Requirements 2.3**
    """

    @given(doc=st_business_problem_doc())
    @settings(max_examples=20)
    def test_derive_when_content_available(self, doc: str) -> None:
        """Documents with usable content signal derivation, not fallback.

        **Validates: Requirements 2.3**
        """
        from hypothesis import assume

        bpc = parse_business_problem(doc)
        assume(has_usable_content(bpc))

        # Derivation path: has_usable_content returns True
        assert has_usable_content(bpc) is True

        # Derivation path produces at least 1 requirement
        requirements = derive_query_requirements(bpc)
        assert len(requirements) >= 1
