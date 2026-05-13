"""Property-based and example tests for Track-Conditional Deployment Question.

These tests validate structural properties of the steering files after
making the Module 1 Step 9 deployment target question conditional on the
bootcamper's selected track.

Feature: track-conditional-deployment-question
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
PHASE1_STEERING = _BOOTCAMP_DIR / "steering" / "module-01-business-problem.md"
PHASE2_STEERING = _BOOTCAMP_DIR / "steering" / "module-01-phase2-document-confirm.md"
MODULE8_STEERING = _BOOTCAMP_DIR / "steering" / "module-08-performance.md"

# ---------------------------------------------------------------------------
# Helpers — Step 9 extraction and conditional branch parsing
# ---------------------------------------------------------------------------


def get_step9_content() -> str:
    """Read Phase 1 steering and extract the full Step 9 section.

    Returns the text from the Step 9 heading up to the next top-level
    step or the Error Handling section, whichever comes first.
    """
    content = PHASE1_STEERING.read_text(encoding="utf-8")
    # Step 9 starts with "9. **"
    step9_pattern = re.compile(r"^9\.\s+\*\*", re.MULTILINE)
    match = step9_pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # End at next top-level step (any digit followed by ". **") or
    # "## Error Handling" section header
    end_patterns = [
        re.compile(r"^\d+\.\s+\*\*", re.MULTILINE),
        re.compile(r"^## Error Handling", re.MULTILINE),
    ]

    end = len(content)
    for pattern in end_patterns:
        for m in pattern.finditer(content, start + 1):
            if m.start() > start:
                end = min(end, m.start())
                break

    return content[start:end]


def get_advanced_branch(step9_content: str) -> str:
    """Extract the advanced_topics conditional branch from Step 9.

    Looks for the section starting with "IF `track` is `advanced_topics`:"
    and ending at the non-advanced branch marker.

    Returns the text of the advanced_topics branch.
    """
    # Match the IF advanced_topics marker
    advanced_pattern = re.compile(
        r"\*\*IF `track` is `advanced_topics`:\*\*",
        re.IGNORECASE,
    )
    match = advanced_pattern.search(step9_content)
    if not match:
        return ""

    start = match.start()

    # End at the non-advanced branch marker
    non_advanced_pattern = re.compile(
        r"\*\*IF `track` is NOT `advanced_topics`",
        re.IGNORECASE,
    )
    non_advanced_match = non_advanced_pattern.search(step9_content, start + 1)
    if non_advanced_match:
        return step9_content[start:non_advanced_match.start()]

    return step9_content[start:]


def get_non_advanced_branch(step9_content: str) -> str:
    """Extract the non-advanced/skip branch from Step 9.

    Looks for the section starting with
    "IF `track` is NOT `advanced_topics`" (which also covers the
    "or `track` is not set" clause).

    Returns the text of the skip branch.
    """
    non_advanced_pattern = re.compile(
        r"\*\*IF `track` is NOT `advanced_topics`",
        re.IGNORECASE,
    )
    match = non_advanced_pattern.search(step9_content)
    if not match:
        return ""

    return step9_content[match.start():]


def get_step12_content() -> str:
    """Read Phase 2 steering and extract the Step 12 section.

    Step 12 contains the business problem document template including
    the Deployment Target conditional section.
    """
    content = PHASE2_STEERING.read_text(encoding="utf-8")
    # Step 12 starts with "12. **"
    step12_pattern = re.compile(r"^12\.\s+\*\*", re.MULTILINE)
    match = step12_pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # End at next top-level step
    next_step_pattern = re.compile(r"^\d+\.\s+\*\*", re.MULTILINE)
    for m in next_step_pattern.finditer(content, start + 1):
        if m.start() > start:
            return content[start:m.start()]

    return content[start:]


def get_module8_deferred_block() -> str:
    """Read Module 8 steering and extract the deferred deployment question block.

    Returns the text from the "## Deferred Deployment Question" heading
    up to the next section separator (---) or next heading (##).
    """
    content = MODULE8_STEERING.read_text(encoding="utf-8")
    # Find the deferred deployment section
    deferred_pattern = re.compile(
        r"^## Deferred Deployment Question",
        re.MULTILINE,
    )
    match = deferred_pattern.search(content)
    if not match:
        return ""

    start = match.start()

    # End at the horizontal rule (---) or next ## heading
    end_patterns = [
        re.compile(r"^---\s*$", re.MULTILINE),
        re.compile(r"^## (?!Deferred)", re.MULTILINE),
    ]

    end = len(content)
    for pattern in end_patterns:
        for m in pattern.finditer(content, start + 1):
            if m.start() > start:
                end = min(end, m.start())
                break

    return content[start:end]


# ---------------------------------------------------------------------------
# Property 1: Non-Advanced Tracks Gate the Deployment Question
# ---------------------------------------------------------------------------


class TestProperty1NonAdvancedTracksGate:
    """Property 1: Non-Advanced Tracks Gate the Deployment Question.

    For any track value not equal to `advanced_topics`, Step 9 conditional
    logic instructs the agent to skip the deployment question.

    **Validates: Requirements 1.1, 2.1**
    """

    @given(
        track=st.one_of(
            st.sampled_from(["core_bootcamp"]),
            st.text(),
        )
    )
    @settings(max_examples=100)
    def test_non_advanced_track_triggers_skip(self, track: str) -> None:
        """For any non-advanced track, the skip branch contains skip language.

        Args:
            track: An arbitrary track value that is not 'advanced_topics'.
        """
        from hypothesis import assume

        assume(track != "advanced_topics")

        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted from steering file"

        non_advanced_branch = get_non_advanced_branch(step9_content)
        assert non_advanced_branch, "Non-advanced branch not found in Step 9"

        # The non-advanced branch must contain skip-related language
        branch_lower = non_advanced_branch.lower()
        skip_indicators = [
            "skip",
            "skipped_not_applicable",
            "not part of the current track",
        ]
        assert any(
            indicator in branch_lower for indicator in skip_indicators
        ), (
            f"Non-advanced branch does not contain skip language for track={track!r}. "
            f"Expected one of {skip_indicators} in branch text."
        )


# ---------------------------------------------------------------------------
# Property 2: All Deployment Options Preserved for Advanced Track
# ---------------------------------------------------------------------------


class TestProperty2DeploymentOptionsPreserved:
    """Property 2: All Deployment Options Preserved for Advanced Track.

    For any deployment option in the known set {AWS, Azure, GCP, Kubernetes,
    Docker Swarm, local/current machine, not sure yet}, the Step 9 section
    in module-01-business-problem.md contains that option within the
    advanced_topics conditional branch.

    **Validates: Requirements 4.1, 4.4**
    """

    @given(
        option=st.sampled_from([
            "AWS",
            "Azure",
            "GCP",
            "Kubernetes",
            "Docker Swarm",
            "Current machine",
            "not sure yet",
        ])
    )
    @settings(max_examples=100)
    def test_deployment_option_present_in_advanced_branch(self, option: str) -> None:
        """For any known deployment option, the advanced branch contains it.

        Args:
            option: A deployment option from the known set.
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted from steering file"

        advanced_branch = get_advanced_branch(step9_content)
        assert advanced_branch, "Advanced branch not found in Step 9"

        # Case-insensitive check for the option text in the advanced branch
        assert option.lower() in advanced_branch.lower(), (
            f"Deployment option {option!r} not found in the advanced_topics "
            f"conditional branch of Step 9."
        )


# ---------------------------------------------------------------------------
# Property 3: Checkpoint Written for All Step 9 Outcomes
# ---------------------------------------------------------------------------


class TestProperty3CheckpointWrittenForAllOutcomes:
    """Property 3: Checkpoint Written for All Step 9 Outcomes.

    For any execution path through Step 9 (whether the question is presented
    or skipped), the steering file contains a checkpoint write instruction
    that records the step to `config/bootcamp_progress.json`.

    **Validates: Requirements 1.4, 4.2**
    """

    @given(path=st.sampled_from(["advanced", "non_advanced"]))
    @settings(max_examples=100)
    def test_checkpoint_exists_for_all_paths(self, path: str) -> None:
        """For any execution path through Step 9, a checkpoint instruction exists.

        Args:
            path: The execution path — either 'advanced' (question presented)
                or 'non_advanced' (question skipped).
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted from steering file"

        if path == "advanced":
            branch = get_advanced_branch(step9_content)
            assert branch, "Advanced branch not found in Step 9"
        else:
            branch = get_non_advanced_branch(step9_content)
            assert branch, "Non-advanced branch not found in Step 9"

        branch_lower = branch.lower()

        # The branch must contain a checkpoint instruction referencing
        # config/bootcamp_progress.json
        checkpoint_indicators = [
            "bootcamp_progress.json",
            "bootcamp_progress",
            "checkpoint",
        ]
        has_checkpoint = any(
            indicator in branch_lower for indicator in checkpoint_indicators
        )
        assert has_checkpoint, (
            f"No checkpoint instruction found in the {path} branch of Step 9. "
            f"Expected a reference to config/bootcamp_progress.json or "
            f"checkpoint language."
        )


# ---------------------------------------------------------------------------
# Unit Tests: Specific Structural Expectations
# ---------------------------------------------------------------------------


class TestUnitStructuralExpectations:
    """Unit tests for specific structural expectations of the steering files.

    These example-based tests verify concrete content requirements that
    complement the property-based tests above.
    """

    def test_skip_path_no_deployment_target_persistence(self) -> None:
        """Skip branch does NOT instruct persisting deployment_target.

        The non-advanced branch should skip the deployment question entirely
        and must not contain instructions to persist deployment_target.

        **Validates: Requirements 1.3**
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted"

        non_advanced_branch = get_non_advanced_branch(step9_content)
        assert non_advanced_branch, "Non-advanced branch not found in Step 9"

        branch_lower = non_advanced_branch.lower()

        # The skip branch must NOT contain *positive* persistence instructions
        # for deployment_target. It MAY contain negative instructions like
        # "do NOT persist" — those reinforce the skip behavior.
        # Check that any mention of "persist" + "deployment_target" is
        # preceded by negation language (e.g., "do not persist").
        if "persist" in branch_lower and "deployment_target" in branch_lower:
            # Acceptable: negative instruction ("do not persist")
            has_negation = (
                "do not persist" in branch_lower
                or "don't persist" in branch_lower
                or "not persist" in branch_lower
                or "no deployment_target" in branch_lower
            )
            assert has_negation, (
                "Non-advanced branch should NOT contain positive instructions "
                "to persist deployment_target — the question is skipped for "
                "this track. Only negative instructions (e.g., 'do NOT persist') "
                "are acceptable."
            )

    def test_skip_checkpoint_contains_skipped_status(self) -> None:
        """Skip branch contains skipped_not_applicable status language.

        The checkpoint in the skip path must record a skipped status so
        progress tracking remains accurate.

        **Validates: Requirements 1.4**
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted"

        non_advanced_branch = get_non_advanced_branch(step9_content)
        assert non_advanced_branch, "Non-advanced branch not found in Step 9"

        branch_lower = non_advanced_branch.lower()
        assert "skipped_not_applicable" in branch_lower, (
            "Non-advanced branch must contain 'skipped_not_applicable' status "
            "language in its checkpoint instruction."
        )

    def test_conditional_handles_not_set_case(self) -> None:
        """Step 9 conditional explicitly handles the 'not set' case for track.

        The conditional must mention handling when track is not set or missing,
        ensuring safe default behavior.

        **Validates: Requirements 2.1**
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted"

        content_lower = step9_content.lower()
        # Look for "not set" or "is not set" language in the conditional
        has_not_set = "not set" in content_lower or "is not set" in content_lower
        assert has_not_set, (
            "Step 9 conditional must explicitly mention handling when `track` "
            "is 'not set' — this ensures safe default behavior for missing config."
        )

    def test_module8_deferred_deployment_conditional(self) -> None:
        """Module 8 contains conditional for advanced_topics AND missing deployment_target.

        The deferred deployment question block must check both conditions:
        track is advanced_topics AND deployment_target is not present.

        **Validates: Requirements 2.2**
        """
        deferred_block = get_module8_deferred_block()
        assert deferred_block, (
            "Deferred Deployment Question section not found in module-08-performance.md"
        )

        block_lower = deferred_block.lower()
        assert "advanced_topics" in block_lower, (
            "Module 8 deferred block must reference 'advanced_topics' track."
        )
        assert "deployment_target" in block_lower, (
            "Module 8 deferred block must reference 'deployment_target' "
            "to check whether it is missing."
        )

    def test_phase2_step12_not_applicable_variant(self) -> None:
        """Step 12 contains 'Not applicable' text for Deployment Target section.

        When Step 9 was skipped, the business problem document should show
        a 'Not applicable' variant for the Deployment Target section.

        **Validates: Requirements 3.1**
        """
        step12_content = get_step12_content()
        assert step12_content, "Step 12 content could not be extracted"

        assert "not applicable" in step12_content.lower(), (
            "Step 12 must contain a 'Not applicable' variant for the "
            "Deployment Target section when Step 9 was skipped."
        )

    def test_module8_updates_business_problem_doc(self) -> None:
        """Module 8 deferred block references updating docs/business_problem.md.

        When the deferred deployment question is asked in Module 8, the
        instructions must include updating the business problem document.

        **Validates: Requirements 3.2**
        """
        deferred_block = get_module8_deferred_block()
        assert deferred_block, (
            "Deferred Deployment Question section not found in module-08-performance.md"
        )

        assert "business_problem.md" in deferred_block, (
            "Module 8 deferred block must reference 'business_problem.md' "
            "to instruct updating the business problem document."
        )

    def test_advanced_branch_preserves_cloud_provider(self) -> None:
        """Advanced branch still contains cloud_provider persistence instruction.

        The advanced_topics branch must preserve the dual-write behavior
        where selecting a cloud hyperscaler also persists cloud_provider.

        **Validates: Requirements 4.3**
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted"

        advanced_branch = get_advanced_branch(step9_content)
        assert advanced_branch, "Advanced branch not found in Step 9"

        assert "cloud_provider" in advanced_branch, (
            "Advanced branch must contain 'cloud_provider' persistence "
            "instruction for hyperscaler selections."
        )

    def test_step9_preserves_reassurance_message(self) -> None:
        """Step 9 still contains 'develop everything locally first' reassurance.

        The reassurance message must be preserved so bootcampers know there
        is no pressure to commit to a deployment target immediately.

        **Validates: Requirements 4.4**
        """
        step9_content = get_step9_content()
        assert step9_content, "Step 9 content could not be extracted"

        assert re.search(
            r"develop everything locally first", step9_content, re.IGNORECASE
        ), (
            "Step 9 must contain the 'develop everything locally first' "
            "reassurance message."
        )
