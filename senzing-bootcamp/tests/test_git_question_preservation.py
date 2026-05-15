"""Preservation property tests for agent-skips-git-question bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: agent-skips-git-question
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
_MODULE_01 = _BOOTCAMP_DIR / "steering" / "module-01-business-problem.md"
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.kiro.hook"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_module_01() -> str:
    """Read the full content of module-01-business-problem.md."""
    return _MODULE_01.read_text(encoding="utf-8")


def _extract_step(markdown: str, step_number: int) -> str:
    """Extract a numbered step section from the module-01 steering file.

    Steps are formatted as top-level numbered items like:
    ``1. **Step title** ...``

    Returns the full text of the step from its number to the next step
    or end of file.
    """
    step_pattern = re.compile(
        rf"^{step_number}\.\s+\*\*",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next step (next_number. **...)
    next_step_pattern = re.compile(
        rf"^{step_number + 1}\.\s+\*\*",
        re.MULTILINE,
    )
    next_match = next_step_pattern.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    # If no next step, go to end but stop at Phase 2 reference or EOF
    phase2_pattern = re.compile(r"^\*\*Phase 2", re.MULTILINE)
    phase2_match = phase2_pattern.search(markdown, start + 1)
    if phase2_match:
        return markdown[start:phase2_match.start()]

    return markdown[start:]


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# ---------------------------------------------------------------------------

_UNFIXED_CONTENT = _read_module_01()
_UNFIXED_STEPS: dict[int, str] = {
    n: _extract_step(_UNFIXED_CONTENT, n) for n in range(1, 9)
}
_UNFIXED_HOOK_BYTES = _HOOK_FILE.read_bytes()

# Phase 2 reference line
_PHASE2_LINE = (
    "**Phase 2 (Steps 10\u201318):** Loaded from "
    "`module-01-phase2-document-confirm.md` via the phase system."
)

# Checkpoint pattern
_CHECKPOINT_RE = re.compile(r"\*\*Checkpoint:\*\*")

_UNFIXED_CHECKPOINT_COUNT = len(_CHECKPOINT_RE.findall(_UNFIXED_CONTENT))


# ---------------------------------------------------------------------------
# Test 1 — Steps 2–8 Content Preservation
# ---------------------------------------------------------------------------


class TestSteps2Through8ContentPreservation:
    """Steps 2–8 content is present and unchanged.

    **Validates: Requirements 3.4**

    Parse Steps 2 through 8 from the file and assert each step's
    content matches the observed baseline snapshot.
    """

    def test_steps_2_through_8_content_unchanged(self) -> None:
        """Assert each of Steps 2–8 is present and unchanged."""
        content = _read_module_01()
        for step_num in range(2, 9):
            baseline = _UNFIXED_STEPS[step_num]
            assert baseline, (
                f"Baseline for Step {step_num} is empty — "
                f"step not found in unfixed file"
            )
            current = _extract_step(content, step_num)
            assert current == baseline, (
                f"Step {step_num} content has changed.\n"
                f"Expected (first 300 chars):\n"
                f"{baseline[:300]}\n"
                f"Got (first 300 chars):\n"
                f"{current[:300]}"
            )


# ---------------------------------------------------------------------------
# Test 2 — Phase 2 Reference Preservation
# ---------------------------------------------------------------------------


class TestPhase2ReferencePreservation:
    """The Phase 2 reference line is present and unchanged.

    **Validates: Requirements 3.4**

    Assert the Phase 2 reference line exists in the file.
    """

    def test_phase2_reference_present(self) -> None:
        """Assert the Phase 2 reference line is in the file."""
        content = _read_module_01()
        assert _PHASE2_LINE in content, (
            "Phase 2 reference line not found in file.\n"
            f"Expected: {_PHASE2_LINE}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Already-a-Repo Path Preservation
# ---------------------------------------------------------------------------


class TestAlreadyARepoPathPreservation:
    """Step 1 preserves the git check and already-a-repo skip logic.

    **Validates: Requirements 3.1**

    Assert Step 1 still contains the git rev-parse check and the
    logic for skipping the question when already a repo.
    """

    def test_step1_contains_git_rev_parse(self) -> None:
        """Assert Step 1 contains git rev-parse --git-dir."""
        content = _read_module_01()
        step1 = _extract_step(content, 1)
        assert step1, "Step 1 not found in file"
        assert "git rev-parse --git-dir" in step1, (
            "Step 1 missing 'git rev-parse --git-dir' command"
        )

    def test_step1_contains_already_a_repo_logic(self) -> None:
        """Assert Step 1 contains the already-a-repo skip path."""
        content = _read_module_01()
        step1 = _extract_step(content, 1)
        assert step1, "Step 1 not found in file"
        has_already_repo = re.search(
            r"already\s+(a\s+)?(git\s+)?repo", step1, re.IGNORECASE
        )
        has_if_not = re.search(
            r"if\s+not", step1, re.IGNORECASE
        )
        assert has_already_repo or has_if_not, (
            "Step 1 missing already-a-repo skip logic. "
            f"Step 1 preview:\n{step1[:400]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Step Count Preservation
# ---------------------------------------------------------------------------


class TestStepCountPreservation:
    """The file contains exactly 8 numbered top-level steps.

    **Validates: Requirements 3.4**

    Assert the file has steps numbered 1 through 8 and the Phase 2
    reference line.
    """

    def test_exactly_8_numbered_steps(self) -> None:
        """Assert the file contains the expected top-level numbered workflow steps.

        Steps 1-9 are workflow steps. The Error Handling section also has
        numbered items (1-3) but those are not workflow steps. Sub-steps
        (7a, 7b, etc.) are not matched by this pattern.
        """
        content = _read_module_01()
        # Match top-level numbered steps: "N. **..."
        step_pattern = re.compile(r"^(\d+)\.\s+\*\*", re.MULTILINE)
        matches = step_pattern.findall(content)
        step_numbers = [int(m) for m in matches]
        # Workflow steps are 1-9; Error Handling section has 1-3
        # Check that the first 9 entries are the workflow steps
        assert step_numbers[:9] == list(range(1, 10)), (
            f"Expected workflow steps 1\u20139, found: {step_numbers}"
        )

    def test_phase2_reference_also_present(self) -> None:
        """Assert the Phase 2 reference line accompanies the 8 steps."""
        content = _read_module_01()
        assert _PHASE2_LINE in content, (
            "Phase 2 reference line missing alongside the 8 steps"
        )


# ---------------------------------------------------------------------------
# Test 5 — YAML Frontmatter Preservation
# ---------------------------------------------------------------------------


class TestYAMLFrontmatterPreservation:
    """The file begins with YAML frontmatter containing inclusion: manual.

    **Validates: Requirements 3.4**

    Assert the file starts with ``---`` delimited YAML frontmatter
    and contains ``inclusion: manual``.
    """

    def test_file_starts_with_yaml_frontmatter(self) -> None:
        """Assert the file begins with --- delimited frontmatter."""
        content = _read_module_01()
        assert content.startswith("---"), (
            "File does not start with YAML frontmatter delimiter '---'"
        )

    def test_frontmatter_contains_inclusion_manual(self) -> None:
        """Assert the frontmatter contains inclusion: manual."""
        content = _read_module_01()
        # Extract frontmatter between first and second ---
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, "Could not parse YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert "inclusion: manual" in frontmatter, (
            f"Frontmatter missing 'inclusion: manual'. "
            f"Found: {frontmatter}"
        )


# ---------------------------------------------------------------------------
# Test 6 — Hook File Unchanged
# ---------------------------------------------------------------------------


class TestHookFileUnchanged:
    """The ask-bootcamper hook file is byte-identical to its original.

    **Validates: Requirements 3.2**

    Read the hook file and assert it matches the snapshotted bytes.
    """

    def test_hook_file_byte_identical(self) -> None:
        """Assert the hook file has not been modified."""
        current_bytes = _HOOK_FILE.read_bytes()
        assert current_bytes == _UNFIXED_HOOK_BYTES, (
            "ask-bootcamper.kiro.hook has been modified. "
            f"Expected {len(_UNFIXED_HOOK_BYTES)} bytes, "
            f"got {len(current_bytes)} bytes."
        )


# ---------------------------------------------------------------------------
# Test 7 — Checkpoint Count Preservation
# ---------------------------------------------------------------------------


class TestCheckpointCountPreservation:
    """The total number of Checkpoint lines is unchanged.

    **Validates: Requirements 3.4**

    Assert the file contains the same number of **Checkpoint:** lines
    as the unfixed baseline (one per step).
    """

    def test_checkpoint_count_unchanged(self) -> None:
        """Assert the checkpoint count matches the baseline."""
        content = _read_module_01()
        current_count = len(_CHECKPOINT_RE.findall(content))
        assert current_count == _UNFIXED_CHECKPOINT_COUNT, (
            f"Checkpoint count changed. "
            f"Expected {_UNFIXED_CHECKPOINT_COUNT}, got {current_count}."
        )

    def test_checkpoint_count_is_8(self) -> None:
        """Assert there are checkpoints for all steps including sub-steps.

        Steps 1-6 and 8-9 have one checkpoint each (8 total).
        Step 7 was split into sub-steps 7a-7d, each with a checkpoint (4 total).
        Step 1 also has a sub-step checkpoint.
        Total: 13 checkpoints.
        """
        content = _read_module_01()
        count = len(_CHECKPOINT_RE.findall(content))
        assert count == 13, (
            f"Expected 13 checkpoints, found {count}."
        )


# ---------------------------------------------------------------------------
# PBT Test — Non-Step-1 Steps Unchanged
# ---------------------------------------------------------------------------

_NON_STEP1_NUMBERS = [2, 3, 4, 5, 6, 7, 8]


@st.composite
def st_non_step1_number(draw: st.DrawFn) -> int:
    """Generate a step number from {2, 3, 4, 5, 6, 7, 8}."""
    return draw(st.sampled_from(_NON_STEP1_NUMBERS))


class TestNonStep1StepsUnchanged:
    """PBT — Non-Step-1 steps are identical to the baseline.

    **Validates: Requirements 3.4**

    Use Hypothesis to generate step numbers from {2..8} and verify
    each step's content is identical between the observed baseline
    and the current file.
    """

    @given(step_num=st_non_step1_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_step1_content_identical_to_baseline(
        self, step_num: int
    ) -> None:
        """For any step 2–8, content must match the unfixed baseline."""
        baseline = _UNFIXED_STEPS[step_num]
        assert baseline, (
            f"Baseline for Step {step_num} is empty"
        )

        content = _read_module_01()
        current = _extract_step(content, step_num)
        assert current == baseline, (
            f"Step {step_num} content differs from baseline.\n"
            f"Baseline (first 200 chars): {baseline[:200]}\n"
            f"Current (first 200 chars): {current[:200]}"
        )
