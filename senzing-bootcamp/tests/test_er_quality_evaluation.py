"""Structural validation tests for the ER quality evaluation loop feature.

These tests verify that Module 7 steering contains a quality evaluation step
with MCP tool references, quality thresholds, and feedback loop instructions,
and that module-transitions.md documents the backward transition.

Feature: er-quality-evaluation-loop
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

MODULE_07_PATH = _POWER_ROOT / "steering" / "module-07-query-validation.md"
TRANSITIONS_PATH = _POWER_ROOT / "steering" / "module-transitions.md"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestQualityEvaluationStepExists:
    """Verify Module 7 steering contains a quality evaluation step."""

    def test_quality_evaluation_step_present(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert re.search(r"quality evaluation", content, re.IGNORECASE), (
            "Module 7 steering must contain a 'Quality evaluation' step"
        )


class TestMcpToolReferences:
    """Verify the quality evaluation step references required MCP tools."""

    def test_reporting_guide_quality_reference(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert "reporting_guide(topic='quality'" in content, (
            "Module 7 steering must reference reporting_guide with topic='quality'"
        )

    def test_search_docs_quality_reference(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert "search_docs(query='entity resolution quality evaluation'" in content, (
            "Module 7 steering must reference search_docs with a quality-related query"
        )


class TestQualityThresholds:
    """Verify the quality evaluation step defines threshold levels with actions."""

    def test_acceptable_threshold_defined(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert re.search(r"\*\*Acceptable\*\*\s*\(proceed\)", content, re.IGNORECASE), (
            "Module 7 steering must define an 'Acceptable' threshold with (proceed)"
        )

    def test_marginal_threshold_defined(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert re.search(r"\*\*Marginal\*\*\s*\(review\)", content, re.IGNORECASE), (
            "Module 7 steering must define a 'Marginal' threshold with (review)"
        )

    def test_poor_threshold_defined(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert re.search(r"\*\*Poor\*\*\s*\(iterate\)", content, re.IGNORECASE), (
            "Module 7 steering must define a 'Poor' threshold with (iterate)"
        )

    def test_each_threshold_has_action(self) -> None:
        content = MODULE_07_PATH.read_text()
        # The "Based on the assessment:" section has response guidance for each threshold
        assert re.search(r"\*\*Acceptable:\*\*", content), (
            "Module 7 steering must have action guidance for 'Acceptable' threshold"
        )
        assert re.search(r"\*\*Marginal:\*\*", content), (
            "Module 7 steering must have action guidance for 'Marginal' threshold"
        )
        assert re.search(r"\*\*Poor:\*\*", content), (
            "Module 7 steering must have action guidance for 'Poor' threshold"
        )


class TestFeedbackLoopInstructions:
    """Verify Module 7 steering documents the Module 5 feedback loop."""

    def test_module_5_feedback_loop_documented(self) -> None:
        content = MODULE_07_PATH.read_text()
        has_module_5 = "Module 5" in content
        has_feedback_ref = (
            "feedback loop" in content.lower() or "return to Module 5" in content
        )
        assert has_module_5 and has_feedback_ref, (
            "Module 7 steering must reference the Module 5 feedback loop"
        )

    def test_progress_preservation_mentioned(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert "preserved" in content.lower() or "preservation" in content.lower(), (
            "Module 7 steering must mention progress preservation"
        )

    def test_phase_2_reentry_specified(self) -> None:
        content = MODULE_07_PATH.read_text()
        assert "Phase 2" in content, (
            "Module 7 steering must specify Phase 2 re-entry"
        )


class TestModuleTransitionsBackwardLoop:
    """Verify module-transitions.md documents the Module 7→5 quality feedback loop."""

    def test_quality_feedback_loop_section_exists(self) -> None:
        content = TRANSITIONS_PATH.read_text()
        has_heading = "Quality Feedback Loop" in content
        has_both_modules = "Module 7" in content and "Module 5" in content
        assert has_heading or has_both_modules, (
            "module-transitions.md must contain a section about the Module 7→5 "
            "quality feedback loop"
        )

    def test_progress_preservation_documented(self) -> None:
        content = TRANSITIONS_PATH.read_text()
        assert re.search(r"preserv", content, re.IGNORECASE), (
            "module-transitions.md must mention progress preservation"
        )

    def test_phase_2_reentry_documented(self) -> None:
        content = TRANSITIONS_PATH.read_text()
        assert "Phase 2" in content, (
            "module-transitions.md must mention Phase 2 re-entry"
        )
