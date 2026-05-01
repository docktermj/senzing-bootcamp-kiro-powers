"""Preservation property tests for eula-answer-skipped bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: eula-answer-skipped
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# -------------------------------------------------------------------
# Paths — relative to this test file's location
# -------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_MODULE_02 = _BOOTCAMP_DIR / "steering" / "module-02-sdk-setup.md"
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "ask-bootcamper.kiro.hook"

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _read_module_02() -> str:
    """Read the full content of module-02-sdk-setup.md."""
    return _MODULE_02.read_text(encoding="utf-8")


def _extract_step_by_heading(
    markdown: str, step_number: int
) -> str:
    """Extract a step section by its ``## Step N:`` heading.

    Returns the full text from the heading to the next ``## ``
    heading or end of file.
    """
    step_pattern = re.compile(
        rf"^## Step {step_number}:",
        re.MULTILINE,
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    next_heading = re.compile(r"^## ", re.MULTILINE)
    next_match = next_heading.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


# -------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# -------------------------------------------------------------------

_UNFIXED_CONTENT = _read_module_02()

_NON_STEP3_NUMBERS = [1, 2, 4, 5, 6, 7, 8, 9]

_UNFIXED_STEPS: dict[int, str] = {
    n: _extract_step_by_heading(_UNFIXED_CONTENT, n)
    for n in _NON_STEP3_NUMBERS
}

_UNFIXED_HOOK_BYTES = _HOOK_FILE.read_bytes()

_CHECKPOINT_RE = re.compile(r"\*\*Checkpoint:\*\*")
_UNFIXED_CHECKPOINT_COUNT = len(
    _CHECKPOINT_RE.findall(_UNFIXED_CONTENT)
)

# Snapshot pre-EULA sub-steps within Step 3
_UNFIXED_STEP3 = _extract_step_by_heading(_UNFIXED_CONTENT, 3)


# -------------------------------------------------------------------
# Test 1 — Steps 1-2, 4-9 Content Preservation
# -------------------------------------------------------------------


class TestNonStep3StepsContentPreservation:
    """Steps 1-2 and 4-9 content is present and unchanged.

    **Validates: Requirements 3.1, 3.3**

    Parse each non-Step-3 step from the file and assert its content
    matches the observed baseline snapshot.
    """

    def test_non_step3_steps_content_unchanged(self) -> None:
        """Assert each of Steps 1-2, 4-9 is unchanged."""
        content = _read_module_02()
        for step_num in _NON_STEP3_NUMBERS:
            baseline = _UNFIXED_STEPS[step_num]
            assert baseline, (
                f"Baseline for Step {step_num} is empty — "
                f"step not found in unfixed file"
            )
            current = _extract_step_by_heading(content, step_num)
            assert current == baseline, (
                f"Step {step_num} content has changed.\n"
                f"Expected (first 300 chars):\n"
                f"{baseline[:300]}\n"
                f"Got (first 300 chars):\n"
                f"{current[:300]}"
            )


# -------------------------------------------------------------------
# Test 2 — Hook File Unchanged
# -------------------------------------------------------------------


class TestHookFileUnchanged:
    """The ask-bootcamper hook file is byte-identical to original.

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


# -------------------------------------------------------------------
# Test 3 — YAML Frontmatter Preservation
# -------------------------------------------------------------------


class TestYAMLFrontmatterPreservation:
    """File begins with YAML frontmatter containing inclusion: manual.

    **Validates: Requirements 3.4**

    Assert the file starts with ``---`` delimited YAML frontmatter
    and contains ``inclusion: manual``.
    """

    def test_file_starts_with_yaml_frontmatter(self) -> None:
        """Assert the file begins with --- delimited frontmatter."""
        content = _read_module_02()
        assert content.startswith("---"), (
            "File does not start with YAML frontmatter '---'"
        )

    def test_frontmatter_contains_inclusion_manual(self) -> None:
        """Assert the frontmatter contains inclusion: manual."""
        content = _read_module_02()
        fm_match = re.match(
            r"^---\n(.*?)\n---", content, re.DOTALL
        )
        assert fm_match, "Could not parse YAML frontmatter"
        frontmatter = fm_match.group(1)
        assert "inclusion: manual" in frontmatter, (
            f"Frontmatter missing 'inclusion: manual'. "
            f"Found: {frontmatter}"
        )


# -------------------------------------------------------------------
# Test 4 — Checkpoint Count Preservation
# -------------------------------------------------------------------


class TestCheckpointCountPreservation:
    """Total number of Checkpoint lines is unchanged.

    **Validates: Requirements 3.4**

    Assert the file contains the same number of ``**Checkpoint:**``
    lines as the unfixed baseline (one per step = 9).
    """

    def test_checkpoint_count_unchanged(self) -> None:
        """Assert the checkpoint count matches the baseline."""
        content = _read_module_02()
        current_count = len(_CHECKPOINT_RE.findall(content))
        assert current_count == _UNFIXED_CHECKPOINT_COUNT, (
            f"Checkpoint count changed. "
            f"Expected {_UNFIXED_CHECKPOINT_COUNT}, "
            f"got {current_count}."
        )

    def test_checkpoint_count_is_9(self) -> None:
        """Assert there are exactly 9 checkpoints (one per step)."""
        content = _read_module_02()
        count = len(_CHECKPOINT_RE.findall(content))
        assert count == 9, (
            f"Expected 9 checkpoints (one per step), "
            f"found {count}."
        )


# -------------------------------------------------------------------
# Test 5 — Pre-EULA Sub-Steps Preservation
# -------------------------------------------------------------------


class TestPreEULASubStepsPreservation:
    """Pre-EULA sub-steps and warnings are preserved in Step 3.

    **Validates: Requirements 3.1, 3.4**

    Assert the add-repo and install-package instructions,
    TypeScript/Node.js warning, Windows-specific instructions,
    anti-patterns check, and shell configuration warning are
    preserved within Step 3.
    """

    def test_add_repo_instruction_preserved(self) -> None:
        """Assert Step 3 contains the add-repo instruction."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "Add the Senzing package repository" in step3, (
            "Step 3 missing 'Add the Senzing package repository'"
        )

    def test_install_package_instruction_preserved(self) -> None:
        """Assert Step 3 contains the install-package instruction."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "Install the Senzing SDK package" in step3, (
            "Step 3 missing 'Install the Senzing SDK package'"
        )

    def test_typescript_warning_preserved(self) -> None:
        """Assert Step 3 contains the TypeScript/Node.js warning."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "TypeScript/Node.js warning" in step3, (
            "Step 3 missing 'TypeScript/Node.js warning'"
        )

    def test_windows_specific_preserved(self) -> None:
        """Assert Step 3 contains Windows-specific instructions."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "Windows-specific" in step3, (
            "Step 3 missing 'Windows-specific' instructions"
        )

    def test_anti_patterns_check_preserved(self) -> None:
        """Assert Step 3 contains the anti_patterns check."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "anti_patterns" in step3, (
            "Step 3 missing 'anti_patterns' check"
        )

    def test_shell_config_warning_preserved(self) -> None:
        """Assert Step 3 contains the shell configuration warning."""
        content = _read_module_02()
        step3 = _extract_step_by_heading(content, 3)
        assert step3, "Step 3 not found"
        assert "NEVER modify" in step3, (
            "Step 3 missing shell config warning "
            "'NEVER modify'"
        )


# -------------------------------------------------------------------
# PBT Test — Non-Step-3 Steps Unchanged
# -------------------------------------------------------------------


@st.composite
def st_non_step3_number(draw: st.DrawFn) -> int:
    """Generate a step number from {1, 2, 4, 5, 6, 7, 8, 9}."""
    return draw(st.sampled_from(_NON_STEP3_NUMBERS))


class TestNonStep3StepsUnchangedPBT:
    """PBT — Non-Step-3 steps are identical to the baseline.

    **Validates: Requirements 3.1, 3.3**

    Use Hypothesis to generate step numbers from {1, 2, 4..9} and
    verify each step's content is identical between the observed
    baseline and the current file.
    """

    @given(step_num=st_non_step3_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_step3_content_identical_to_baseline(
        self, step_num: int
    ) -> None:
        """For any non-Step-3 step, content must match baseline."""
        baseline = _UNFIXED_STEPS[step_num]
        assert baseline, (
            f"Baseline for Step {step_num} is empty"
        )

        content = _read_module_02()
        current = _extract_step_by_heading(content, step_num)
        assert current == baseline, (
            f"Step {step_num} content differs from baseline.\n"
            f"Baseline (first 200 chars): {baseline[:200]}\n"
            f"Current (first 200 chars): {current[:200]}"
        )
