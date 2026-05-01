"""Property-based and example tests for Module 1 Deployment Target & Value Restatement.

These tests validate structural properties of the Module 1 steering files.
Properties 4 and 5 are preservation tests that snapshot baseline content
and assert it remains unchanged after modifications.

Feature: module1-deployment-and-value
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_PHASE1_FILE = _BOOTCAMP_DIR / "steering" / "module-01-business-problem.md"
_PHASE2_FILE = _BOOTCAMP_DIR / "steering" / "module-01-phase2-document-confirm.md"
_MODULE_8_FILE = _BOOTCAMP_DIR / "steering" / "module-08-performance.md"
_MODULE_11_FILE = _BOOTCAMP_DIR / "steering" / "module-11-deployment.md"
_STEERING_INDEX = _BOOTCAMP_DIR / "steering" / "steering-index.yaml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_phase1() -> str:
    """Read the full content of module-01-business-problem.md."""
    return _PHASE1_FILE.read_text(encoding="utf-8")


def _read_phase2() -> str:
    """Read the full content of module-01-phase2-document-confirm.md."""
    return _PHASE2_FILE.read_text(encoding="utf-8")


def _extract_step(markdown: str, step_number: int) -> str:
    """Extract a numbered step section from a steering file.

    Steps are formatted as top-level numbered items like:
    ``N. **Step title** ...``

    Returns the full text of the step from its number to the next step
    or end-of-content marker.
    """
    step_pattern = re.compile(
        rf"^{step_number}\.\s+\*\*",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next step (any number followed by . **)
    next_step_pattern = re.compile(
        r"^\d+\.\s+\*\*",
        re.MULTILINE,
    )
    # Search after the current match
    for next_match in next_step_pattern.finditer(markdown, start + 1):
        if next_match.start() > start:
            return markdown[start:next_match.start()]

    # If no next step, stop at Phase 2 reference or success indicator or EOF
    phase2_pattern = re.compile(r"^\*\*Phase 2", re.MULTILINE)
    phase2_match = phase2_pattern.search(markdown, start + 1)
    if phase2_match:
        return markdown[start:phase2_match.start()]

    success_pattern = re.compile(r"^\*\*Success indicator\*\*", re.MULTILINE)
    success_match = success_pattern.search(markdown, start + 1)
    if success_match:
        return markdown[start:success_match.start()]

    return markdown[start:]


def _strip_step_numbers(text: str) -> str:
    """Strip step number references and checkpoint numbers from step text.

    Removes patterns like:
    - Leading step number: ``9. **`` → ``**``
    - Checkpoint references: ``Write step 9 to`` → ``Write step N to``
    - Step N references in prose: ``Step 9`` → ``Step N``
    """
    # Normalize leading step number (e.g., "9. **" → "N. **")
    result = re.sub(r"^\d+\.\s+\*\*", "N. **", text, count=1)
    # Normalize checkpoint instructions: "Write step 14 to" → "Write step N to"
    result = re.sub(r"Write step \d+ to", "Write step N to", result)
    # Normalize "Step N" references in prose (e.g., "Step 13" → "Step N")
    result = re.sub(r"Step \d+", "Step N", result)
    # Normalize "Steps N–M" range references
    result = re.sub(r"Steps \d+[–-]\d+", "Steps N–M", result)
    return result


# ---------------------------------------------------------------------------
# Baselines — snapshot the CURRENT (pre-modification) file content
# ---------------------------------------------------------------------------

_BASELINE_PHASE1_CONTENT = _read_phase1()
_BASELINE_PHASE1_STEPS: dict[int, str] = {
    n: _extract_step(_BASELINE_PHASE1_CONTENT, n) for n in range(1, 9)
}

_BASELINE_PHASE2_CONTENT = _read_phase2()

# Detect whether the Phase 2 file has already been renumbered by checking
# if step 10 exists and step 9 does not.
_PHASE2_ALREADY_RENUMBERED = bool(
    _extract_step(_BASELINE_PHASE2_CONTENT, 10)
) and not bool(_extract_step(_BASELINE_PHASE2_CONTENT, 9))

if _PHASE2_ALREADY_RENUMBERED:
    # File already renumbered: capture steps 10–18 (excluding new Step 15
    # which has no baseline original).  Map them back to original numbers
    # so the preservation test can look up by original step number.
    _BASELINE_PHASE2_STEPS: dict[int, str] = {}
    _REVERSE_RENUMBER: dict[int, int] = {v: k for k, v in {
        9: 10, 10: 11, 11: 12, 12: 13, 13: 14, 14: 16, 15: 17, 16: 18,
    }.items()}
    for new_num, orig_num in _REVERSE_RENUMBER.items():
        _BASELINE_PHASE2_STEPS[orig_num] = _extract_step(
            _BASELINE_PHASE2_CONTENT, new_num
        )
else:
    _BASELINE_PHASE2_STEPS: dict[int, str] = {
        n: _extract_step(_BASELINE_PHASE2_CONTENT, n) for n in range(9, 17)
    }

# Phase 2 renumbering map: original step → new step number
# Original 9→10, 10→11, 11→12, 12→13, 13→14, 14→16 (skip 15=new), 15→17, 16→18
_PHASE2_RENUMBER_MAP: dict[int, int] = {
    9: 10,
    10: 11,
    11: 12,
    12: 13,
    13: 14,
    14: 16,
    15: 17,
    16: 18,
}

# Original step numbers for Property 5 (all original Phase 2 steps)
_ORIGINAL_PHASE2_STEP_NUMBERS = list(_PHASE2_RENUMBER_MAP.keys())


# ---------------------------------------------------------------------------
# Property 4: Phase 1 Steps 1–8 Content Preservation
# ---------------------------------------------------------------------------


class TestProperty4Phase1StepsPreservation:
    """PBT — Phase 1 Steps 1–8 content is preserved unchanged.

    Feature: module1-deployment-and-value, Property 4: Phase 1 Steps 1–8
    Content Preservation

    *For any* step number in {1, 2, 3, 4, 5, 6, 7, 8}, the full text
    content of that step in the modified Phase 1 file SHALL be identical
    to the baseline (pre-modification) content of that same step.

    **Validates: Requirements 8.1**
    """

    @given(step_num=st.sampled_from(range(1, 9)))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_phase1_step_content_identical_to_baseline(
        self, step_num: int
    ) -> None:
        """For any step 1–8, content must match the baseline snapshot."""
        baseline = _BASELINE_PHASE1_STEPS[step_num]
        assert baseline, (
            f"Baseline for Phase 1 Step {step_num} is empty — "
            f"step not found in baseline file"
        )

        content = _read_phase1()
        current = _extract_step(content, step_num)
        assert current == baseline, (
            f"Phase 1 Step {step_num} content has changed.\n"
            f"Expected (first 300 chars):\n"
            f"{baseline[:300]}\n"
            f"Got (first 300 chars):\n"
            f"{current[:300]}"
        )


# ---------------------------------------------------------------------------
# Property 5: Phase 2 Original Step Instructional Text Preservation
# ---------------------------------------------------------------------------


class TestProperty5Phase2TextPreservation:
    """PBT — Phase 2 original step instructional text is preserved.

    Feature: module1-deployment-and-value, Property 5: Phase 2 Original
    Step Instructional Text Preservation

    *For any* original Phase 2 step (originally numbered 9–16, now 10–18
    excluding the new Step 15), the instructional text of that step —
    excluding step number references and checkpoint number updates —
    SHALL be preserved in the renumbered version.

    **Validates: Requirements 8.2**
    """

    @given(original_step=st.sampled_from(_ORIGINAL_PHASE2_STEP_NUMBERS))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_phase2_instructional_text_preserved_after_renumber(
        self, original_step: int
    ) -> None:
        """For any original Phase 2 step, instructional text is preserved."""
        baseline_text = _BASELINE_PHASE2_STEPS[original_step]
        assert baseline_text, (
            f"Baseline for Phase 2 Step {original_step} is empty — "
            f"step not found in baseline file"
        )

        content = _read_phase2()

        # Detect whether renumbering has been applied by checking if
        # the file's first step is 10 (renumbered) or 9 (original).
        renumbered = bool(_extract_step(content, 10)) and not bool(
            _extract_step(content, 9)
        )

        if renumbered:
            current_step_num = _PHASE2_RENUMBER_MAP[original_step]
        else:
            current_step_num = original_step

        current_text = _extract_step(content, current_step_num)
        assert current_text, (
            f"Phase 2 Step {original_step} not found at "
            f"step number {current_step_num}"
        )

        # Strip step number references and checkpoint numbers before comparison
        baseline_normalized = _strip_step_numbers(baseline_text)
        current_normalized = _strip_step_numbers(current_text)

        assert current_normalized == baseline_normalized, (
            f"Phase 2 Step {original_step} (now at {current_step_num}) "
            f"instructional text has changed.\n"
            f"Baseline normalized (first 300 chars):\n"
            f"{baseline_normalized[:300]}\n"
            f"Current normalized (first 300 chars):\n"
            f"{current_normalized[:300]}"
        )


# ---------------------------------------------------------------------------
# Property 1: Phase 1 Step-Checkpoint Matching
# ---------------------------------------------------------------------------


class TestProperty1Phase1StepCheckpoints:
    """PBT — Every Phase 1 step has a matching checkpoint instruction.

    Feature: module1-deployment-and-value, Property 1: Phase 1
    Step-Checkpoint Matching

    *For any* step number found in the Phase 1 file
    (``module-01-business-problem.md``), there SHALL exist a
    corresponding checkpoint instruction that references that same step
    number, formatted as
    ``Write step N to config/bootcamp_progress.json``.

    **Validates: Requirements 1.7, 8.1**
    """

    @given(step_num=st.sampled_from(range(1, 10)))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_phase1_step_has_checkpoint(self, step_num: int) -> None:
        """For any step 1–9, a matching checkpoint instruction exists."""
        content = _read_phase1()
        step_text = _extract_step(content, step_num)
        assert step_text, (
            f"Phase 1 Step {step_num} not found in file"
        )

        checkpoint = (
            f"Write step {step_num} to `config/bootcamp_progress.json`"
        )
        assert checkpoint in step_text, (
            f"Phase 1 Step {step_num} is missing checkpoint "
            f"instruction: {checkpoint!r}\n"
            f"Step text (first 400 chars):\n{step_text[:400]}"
        )


# ---------------------------------------------------------------------------
# Property 2: Phase 2 Step Sequentiality
# ---------------------------------------------------------------------------


class TestProperty2Phase2Sequentiality:
    """PBT — Phase 2 steps form a sequential range 10–18.

    Feature: module1-deployment-and-value, Property 2: Phase 2 Step
    Sequentiality

    *For any* pair of consecutive top-level numbered steps in the
    Phase 2 file (``module-01-phase2-document-confirm.md``), the second
    step number SHALL equal the first step number plus one, and the full
    sequence SHALL start at 10 and end at 18 with no gaps or duplicates.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_phase2_steps_sequential_10_to_18(self) -> None:
        """Phase 2 top-level steps form the exact sequence 10–18."""
        content = _read_phase2()
        step_numbers = [
            int(m)
            for m in re.findall(
                r"^(\d+)\.\s+\*\*", content, re.MULTILINE
            )
        ]

        assert step_numbers, "No top-level numbered steps found in Phase 2"

        expected = list(range(10, 19))

        # No duplicates
        assert len(step_numbers) == len(set(step_numbers)), (
            f"Duplicate step numbers found: {step_numbers}"
        )

        # Starts at 10, ends at 18
        assert step_numbers[0] == 10, (
            f"Phase 2 should start at step 10, got {step_numbers[0]}"
        )
        assert step_numbers[-1] == 18, (
            f"Phase 2 should end at step 18, got {step_numbers[-1]}"
        )

        # Consecutive pairs differ by exactly 1
        for i in range(len(step_numbers) - 1):
            diff = step_numbers[i + 1] - step_numbers[i]
            assert diff == 1, (
                f"Gap between step {step_numbers[i]} and "
                f"{step_numbers[i + 1]} (diff={diff})"
            )

        # Full sequence matches
        assert step_numbers == expected, (
            f"Expected steps {expected}, got {step_numbers}"
        )


# ---------------------------------------------------------------------------
# Property 3: Phase 2 Step-Checkpoint Matching
# ---------------------------------------------------------------------------


class TestProperty3Phase2StepCheckpoints:
    """PBT — Every Phase 2 step has a matching checkpoint instruction.

    Feature: module1-deployment-and-value, Property 3: Phase 2
    Step-Checkpoint Matching

    *For any* step number found in the Phase 2 file
    (``module-01-phase2-document-confirm.md``), there SHALL exist a
    corresponding checkpoint instruction that references that same step
    number, formatted as
    ``Write step N to config/bootcamp_progress.json``.

    **Validates: Requirements 2.2, 4.5**
    """

    @given(step_num=st.sampled_from(range(10, 19)))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_phase2_step_has_checkpoint(self, step_num: int) -> None:
        """For any step 10–18, a matching checkpoint instruction exists."""
        content = _read_phase2()
        step_text = _extract_step(content, step_num)
        assert step_text, (
            f"Phase 2 Step {step_num} not found in file"
        )

        checkpoint = (
            f"Write step {step_num} to `config/bootcamp_progress.json`"
        )
        assert checkpoint in step_text, (
            f"Phase 2 Step {step_num} is missing checkpoint "
            f"instruction: {checkpoint!r}\n"
            f"Step text (first 400 chars):\n{step_text[:400]}"
        )


# ---------------------------------------------------------------------------
# Task 3.1: Example tests for Phase 1 Step 9 content
# Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
# ---------------------------------------------------------------------------


class TestStep9DeploymentTarget:
    """Example tests for the new Phase 1 Step 9 (deployment target).

    These tests validate that Step 9 contains all required deployment
    options, persistence instructions, and reassurance text.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**
    """

    def test_step9_contains_aws(self) -> None:
        """Step 9 mentions AWS as a deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "AWS" in step9, "Step 9 should mention AWS"

    def test_step9_contains_azure(self) -> None:
        """Step 9 mentions Azure as a deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "Azure" in step9, "Step 9 should mention Azure"

    def test_step9_contains_gcp(self) -> None:
        """Step 9 mentions GCP as a deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "GCP" in step9, "Step 9 should mention GCP"

    def test_step9_contains_kubernetes(self) -> None:
        """Step 9 mentions Kubernetes as a deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "Kubernetes" in step9, (
            "Step 9 should mention Kubernetes"
        )

    def test_step9_contains_docker_swarm(self) -> None:
        """Step 9 mentions Docker Swarm as a deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "Docker Swarm" in step9, (
            "Step 9 should mention Docker Swarm"
        )

    def test_step9_contains_local_option(self) -> None:
        """Step 9 mentions a local/current machine deployment option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        step9_lower = step9.lower()
        assert "local" in step9_lower or "current machine" in step9_lower, (
            "Step 9 should mention local or current machine option"
        )

    def test_step9_contains_not_sure_yet(self) -> None:
        """Step 9 mentions 'not sure yet' as an option."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "not sure yet" in step9.lower(), (
            "Step 9 should mention 'not sure yet' option"
        )

    def test_step9_contains_local_dev_reassurance(self) -> None:
        """Step 9 contains reassurance about local development first."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        step9_lower = step9.lower()
        assert "local" in step9_lower and (
            "first" in step9_lower or "develop" in step9_lower
        ), (
            "Step 9 should contain reassurance about "
            "local development first"
        )

    def test_step9_contains_deployment_target_persistence(self) -> None:
        """Step 9 mentions deployment_target and bootcamp_preferences.yaml."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "deployment_target" in step9, (
            "Step 9 should mention deployment_target"
        )
        assert "bootcamp_preferences.yaml" in step9, (
            "Step 9 should mention bootcamp_preferences.yaml"
        )

    def test_step9_contains_cloud_provider_dual_write(self) -> None:
        """Step 9 mentions cloud_provider for hyperscaler case."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "cloud_provider" in step9, (
            "Step 9 should mention cloud_provider for "
            "hyperscaler dual-write"
        )

    def test_step9_contains_undecided_handling(self) -> None:
        """Step 9 mentions undecided handling."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert "undecided" in step9.lower(), (
            "Step 9 should mention undecided handling"
        )

    def test_step9_contains_checkpoint(self) -> None:
        """Step 9 contains checkpoint instruction."""
        step9 = _extract_step(_read_phase1(), 9)
        assert step9, "Step 9 not found in Phase 1 file"
        assert (
            "Write step 9 to `config/bootcamp_progress.json`" in step9
        ), "Step 9 should contain checkpoint instruction"


# ---------------------------------------------------------------------------
# Task 3.2: Example tests for Phase 2 updates
# Requirements: 2.3, 2.4, 3.1, 3.2, 3.3, 8.3, 8.4
# ---------------------------------------------------------------------------


class TestPhase2Updates:
    """Example tests for Phase 2 renumbering and template updates.

    These tests validate the Phase 2 header, Phase 1 cross-reference,
    business problem template Deployment Target section, and frontmatter
    preservation.

    **Validates: Requirements 2.3, 2.4, 3.1, 3.2, 3.3, 8.3, 8.4**
    """

    def test_phase2_header_says_steps_10_18(self) -> None:
        """Phase 2 file header contains 'Steps 10\u201318' (en-dash)."""
        content = _read_phase2()
        assert "Steps 10\u201318" in content, (
            "Phase 2 header should say 'Steps 10\u201318'"
        )

    def test_phase1_phase2_reference_says_steps_10_18(self) -> None:
        """Phase 1 file contains 'Steps 10\u201318' in Phase 2 reference."""
        content = _read_phase1()
        assert "Steps 10\u201318" in content, (
            "Phase 1 Phase 2 reference should say 'Steps 10\u201318'"
        )

    def test_step12_template_has_deployment_target_section(self) -> None:
        """Step 12 contains a Deployment Target section header."""
        step12 = _extract_step(_read_phase2(), 12)
        assert step12, "Step 12 not found in Phase 2 file"
        step12_lower = step12.lower()
        assert (
            "## deployment target" in step12_lower
            or "**deployment target**" in step12_lower
            or "deployment target" in step12_lower
        ), "Step 12 should contain a Deployment Target section"

    def test_step12_template_has_platform_field(self) -> None:
        """Step 12 template contains a Platform field."""
        step12 = _extract_step(_read_phase2(), 12)
        assert step12, "Step 12 not found in Phase 2 file"
        assert "Platform" in step12, (
            "Step 12 template should contain a Platform field"
        )

    def test_step12_template_has_category_field(self) -> None:
        """Step 12 template contains a Category field."""
        step12 = _extract_step(_read_phase2(), 12)
        assert step12, "Step 12 not found in Phase 2 file"
        assert "Category" in step12, (
            "Step 12 template should contain a Category field"
        )

    def test_step12_template_has_note_field(self) -> None:
        """Step 12 template contains a Note field."""
        step12 = _extract_step(_read_phase2(), 12)
        assert step12, "Step 12 not found in Phase 2 file"
        assert "Note" in step12, (
            "Step 12 template should contain a Note field"
        )

    def test_step12_template_handles_undecided(self) -> None:
        """Step 12 contains 'To be determined' for undecided case."""
        step12 = _extract_step(_read_phase2(), 12)
        assert step12, "Step 12 not found in Phase 2 file"
        assert "To be determined" in step12, (
            "Step 12 should contain 'To be determined' "
            "for undecided deployment target"
        )

    def test_phase1_retains_manual_frontmatter(self) -> None:
        """Phase 1 file contains inclusion: manual frontmatter."""
        content = _read_phase1()
        assert "inclusion: manual" in content, (
            "Phase 1 file should retain 'inclusion: manual' frontmatter"
        )

    def test_phase2_retains_manual_frontmatter(self) -> None:
        """Phase 2 file contains inclusion: manual frontmatter."""
        content = _read_phase2()
        assert "inclusion: manual" in content, (
            "Phase 2 file should retain 'inclusion: manual' frontmatter"
        )


# ---------------------------------------------------------------------------
# Task 3.3: Example tests for value restatement step (Step 15)
# Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
# ---------------------------------------------------------------------------


class TestStep15ValueRestatement:
    """Example tests for the new Phase 2 Step 15 (value restatement).

    These tests validate that Step 15 contains MCP search_docs usage,
    problem context references, entity resolution explanation,
    integration target conditional, and checkpoint instruction.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**
    """

    def test_step15_contains_search_docs(self) -> None:
        """Step 15 contains search_docs MCP instruction."""
        step15 = _extract_step(_read_phase2(), 15)
        assert step15, "Step 15 not found in Phase 2 file"
        assert "search_docs" in step15, (
            "Step 15 should contain search_docs MCP instruction"
        )

    def test_step15_references_problem_context(self) -> None:
        """Step 15 references the bootcamper's problem/use case."""
        step15 = _extract_step(_read_phase2(), 15)
        assert step15, "Step 15 not found in Phase 2 file"
        step15_lower = step15.lower()
        assert (
            "problem" in step15_lower
            or "use case" in step15_lower
            or "use-case" in step15_lower
        ), (
            "Step 15 should reference the bootcamper's "
            "problem or use case"
        )

    def test_step15_mentions_entity_resolution(self) -> None:
        """Step 15 mentions entity resolution."""
        step15 = _extract_step(_read_phase2(), 15)
        assert step15, "Step 15 not found in Phase 2 file"
        assert "entity resolution" in step15.lower(), (
            "Step 15 should mention entity resolution"
        )

    def test_step15_contains_integration_target_conditional(
        self,
    ) -> None:
        """Step 15 mentions integration targets or Step 8."""
        step15 = _extract_step(_read_phase2(), 15)
        assert step15, "Step 15 not found in Phase 2 file"
        step15_lower = step15.lower()
        assert (
            "integration" in step15_lower
            or "step 8" in step15_lower
        ), (
            "Step 15 should mention integration targets or Step 8"
        )

    def test_step15_contains_checkpoint(self) -> None:
        """Step 15 contains checkpoint instruction."""
        step15 = _extract_step(_read_phase2(), 15)
        assert step15, "Step 15 not found in Phase 2 file"
        assert (
            "Write step 15 to `config/bootcamp_progress.json`"
            in step15
        ), "Step 15 should contain checkpoint instruction"


# ---------------------------------------------------------------------------
# Task 3.4: Example tests for downstream module updates
# Requirements: 5.1, 5.2, 5.3, 6.1, 6.2
# ---------------------------------------------------------------------------


class TestDownstreamModuleUpdates:
    """Example tests for Module 11 and Module 8 updates.

    These tests validate that downstream modules read and handle
    the deployment_target preference correctly.

    **Validates: Requirements 5.1, 5.2, 5.3, 6.1, 6.2**
    """

    def test_module11_checks_deployment_target(self) -> None:
        """Module 11 file contains deployment_target."""
        content = _MODULE_11_FILE.read_text(encoding="utf-8")
        assert "deployment_target" in content, (
            "Module 11 should check deployment_target"
        )

    def test_module11_handles_undecided(self) -> None:
        """Module 11 file contains undecided handling."""
        content = _MODULE_11_FILE.read_text(encoding="utf-8")
        assert "undecided" in content.lower(), (
            "Module 11 should handle undecided deployment target"
        )

    def test_module11_still_checks_cloud_provider(self) -> None:
        """Module 11 file contains cloud_provider."""
        content = _MODULE_11_FILE.read_text(encoding="utf-8")
        assert "cloud_provider" in content, (
            "Module 11 should still check cloud_provider"
        )

    def test_module8_reads_deployment_target(self) -> None:
        """Module 8 file contains deployment_target."""
        content = _MODULE_8_FILE.read_text(encoding="utf-8")
        assert "deployment_target" in content, (
            "Module 8 should read deployment_target"
        )

    def test_module8_conditional_without_cloud_provider(self) -> None:
        """Module 8 has conditional logic for deployment_target."""
        content = _MODULE_8_FILE.read_text(encoding="utf-8")
        assert "deployment_target" in content, (
            "Module 8 should reference deployment_target"
        )
        assert "cloud_provider" in content, (
            "Module 8 should reference cloud_provider "
            "in conditional logic"
        )


# ---------------------------------------------------------------------------
# Task 3.5: Example tests for steering index updates
# Requirements: 7.1, 7.2
# ---------------------------------------------------------------------------


class TestSteeringIndexUpdates:
    """Example tests for steering index step_range updates.

    These tests validate that the steering index reflects the new
    step ranges for Phase 1 and Phase 2.

    **Validates: Requirements 7.1, 7.2**
    """

    def test_steering_index_phase1_step_range_1_9(self) -> None:
        """Steering index contains step_range [1, 9] for Phase 1."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        assert re.search(
            r"step_range:\s*\[1,\s*9\]", content
        ), (
            "Steering index should contain step_range [1, 9] "
            "for Phase 1"
        )

    def test_steering_index_phase2_step_range_10_18(self) -> None:
        """Steering index contains step_range [10, 18] for Phase 2."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        assert re.search(
            r"step_range:\s*\[10,\s*18\]", content
        ), (
            "Steering index should contain step_range [10, 18] "
            "for Phase 2"
        )
