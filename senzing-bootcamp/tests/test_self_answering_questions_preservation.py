"""Preservation property tests for self-answering questions bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: self-answering-questions-fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
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
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"

_MODULE_01 = _STEERING_DIR / "module-01-business-problem.md"
_MODULE_01_PHASE2 = _STEERING_DIR / "module-01-phase2-document-confirm.md"
_ONBOARDING = _STEERING_DIR / "onboarding-flow.md"
_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"
_HOOK_REGISTRY = _STEERING_DIR / "hook-registry.md"
_MODULE_03 = _STEERING_DIR / "module-03-system-verification.md"
_MODULE_07 = _STEERING_DIR / "module-07-query-validation.md"
_VIS_GUIDE = _STEERING_DIR / "visualization-guide.md"
_DEPLOY_AZURE = _STEERING_DIR / "deployment-azure.md"
_DEPLOY_GCP = _STEERING_DIR / "deployment-gcp.md"
_DEPLOY_ONPREM = _STEERING_DIR / "deployment-onpremises.md"
_DEPLOY_K8S = _STEERING_DIR / "deployment-kubernetes.md"

# All affected steering files for frontmatter checks
_ALL_AFFECTED_FILES: list[tuple[Path, str]] = [
    (_MODULE_01, "module-01-business-problem.md"),
    (_MODULE_01_PHASE2, "module-01-phase2-document-confirm.md"),
    (_ONBOARDING, "onboarding-flow.md"),
    (_AGENT_INSTRUCTIONS, "agent-instructions.md"),
    (_HOOK_REGISTRY, "hook-registry.md"),
    (_MODULE_03, "module-03-system-verification.md"),
    (_MODULE_07, "module-07-query-validation.md"),
    (_VIS_GUIDE, "visualization-guide.md"),
    (_DEPLOY_AZURE, "deployment-azure.md"),
    (_DEPLOY_GCP, "deployment-gcp.md"),
    (_DEPLOY_ONPREM, "deployment-onpremises.md"),
    (_DEPLOY_K8S, "deployment-kubernetes.md"),
]

# All hook JSON files that must remain byte-identical
_HOOK_FILES: list[tuple[Path, str]] = [
    (p, p.name) for p in sorted(_HOOKS_DIR.glob("*.kiro.hook"))
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HARD_STOP_PATTERN = re.compile(r"🛑\s*STOP", re.IGNORECASE)
_CHECKPOINT_RE = re.compile(r"\*\*Checkpoint:\*\*")


def _read_file(path: Path) -> str:
    """Read a steering file's full content."""
    return path.read_text(encoding="utf-8")


def _extract_yaml_frontmatter(content: str) -> str | None:
    """Extract YAML frontmatter from a markdown file.

    Returns the frontmatter string (between --- delimiters) or None.
    """
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        return fm_match.group(1)
    return None


def _extract_step_module01(markdown: str, step_number: int) -> str:
    """Extract a numbered step from module-01-business-problem.md."""
    step_pattern = re.compile(
        rf"^{step_number}\.\s+\*\*", re.MULTILINE
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_step = re.compile(
        rf"^{step_number + 1}\.\s+\*\*", re.MULTILINE
    )
    next_match = next_step.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    phase2 = re.compile(r"^\*\*Phase 2", re.MULTILINE)
    phase2_match = phase2.search(markdown, start + 1)
    if phase2_match:
        return markdown[start:phase2_match.start()]

    return markdown[start:]


def _extract_step_phase2(markdown: str, step_number: int) -> str:
    """Extract a numbered step from module-01-phase2-document-confirm.md."""
    step_pattern = re.compile(
        rf"^{step_number}\.\s+\*\*", re.MULTILINE
    )
    match = step_pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_step = re.compile(
        rf"^{step_number + 1}\.\s+\*\*", re.MULTILINE
    )
    next_match = next_step.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    success_pattern = re.compile(
        r"^\*\*Success indicator", re.MULTILINE
    )
    success_match = success_pattern.search(markdown, start + 1)
    if success_match:
        return markdown[start:success_match.start()]

    return markdown[start:]


def _extract_onboarding_step(markdown: str, step_id: str) -> str:
    """Extract a step from onboarding-flow.md by step identifier.

    Handles patterns like '## 2. Language Selection' and
    '### 4b. Verbosity'.

    For top-level steps (e.g. '4'), extraction stops at the next
    heading of any level (## or ###) so that sub-steps like 4b are
    not included.  For sub-steps (e.g. '4b'), extraction likewise
    stops at the next ## or ### heading.
    """
    pattern = re.compile(
        rf"^##\s*#?\s*{re.escape(step_id)}\.",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    # Match any ## or ### heading that follows the current step.
    next_heading = re.compile(r"^#{2,3}\s+", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end() + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# ---------------------------------------------------------------------------

# Module 01 non-question steps: 2, 3, 4, 6
_UNFIXED_MODULE01 = _read_file(_MODULE_01)
_MODULE01_NON_QUESTION_STEPS = [2, 3, 4, 6]
_UNFIXED_MODULE01_STEPS: dict[int, str] = {
    n: _extract_step_module01(_UNFIXED_MODULE01, n)
    for n in _MODULE01_NON_QUESTION_STEPS
}

# Module 01 Phase 2 non-question steps: 10, 11, 12, 13, 14, 15, 18
_UNFIXED_PHASE2 = _read_file(_MODULE_01_PHASE2)
_PHASE2_NON_QUESTION_STEPS = [10, 11, 12, 13, 14, 15, 18]
_UNFIXED_PHASE2_STEPS: dict[int, str] = {
    n: _extract_step_phase2(_UNFIXED_PHASE2, n)
    for n in _PHASE2_NON_QUESTION_STEPS
}

# Onboarding non-question steps: 0, 1, 1b, 3, 4, 4c
_UNFIXED_ONBOARDING = _read_file(_ONBOARDING)
_ONBOARDING_NON_QUESTION_STEP_IDS = ["0", "1", "1b", "3", "4"]
_UNFIXED_ONBOARDING_STEPS: dict[str, str] = {
    sid: _extract_onboarding_step(_UNFIXED_ONBOARDING, sid)
    for sid in _ONBOARDING_NON_QUESTION_STEP_IDS
}

# YAML frontmatter baselines for all affected files
_UNFIXED_FRONTMATTER: dict[str, str | None] = {
    name: _extract_yaml_frontmatter(_read_file(path))
    for path, name in _ALL_AFFECTED_FILES
}

# Hook file byte snapshots
_UNFIXED_HOOK_BYTES: dict[str, bytes] = {
    name: path.read_bytes() for path, name in _HOOK_FILES
}

# Checkpoint counts
_MODULE01_CHECKPOINT_COUNT = len(
    _CHECKPOINT_RE.findall(_UNFIXED_MODULE01)
)
_PHASE2_CHECKPOINT_COUNT = len(
    _CHECKPOINT_RE.findall(_UNFIXED_PHASE2)
)

# Step numbering baselines
_MODULE01_STEP_NUMBERS = re.compile(
    r"^(\d+)\.\s+\*\*", re.MULTILINE
).findall(_UNFIXED_MODULE01)
_PHASE2_STEP_NUMBERS = re.compile(
    r"^(\d+)\.\s+\*\*", re.MULTILINE
).findall(_UNFIXED_PHASE2)

# Hook registry — extract the SECOND branch of ask-bootcamper prompt
_UNFIXED_HOOK_REGISTRY = _read_file(_HOOK_REGISTRY)


def _extract_ask_bootcamper_second_branch(content: str) -> str:
    """Extract the SECOND branch text from the ask-bootcamper hook prompt.

    The SECOND branch starts with 'SECOND' and runs to the end of
    the prompt. Searches in the hook file content (JSON prompt field)
    or in the registry if the prompt is inline.
    """
    # First try: look for SECOND in the content directly
    second_match = re.search(r"SECOND\s*—", content)
    if not second_match:
        # Try reading from the hook file
        hook_file = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
        if hook_file.exists():
            import json
            try:
                hook_data = json.loads(hook_file.read_text(encoding="utf-8"))
                prompt = hook_data.get("then", {}).get("prompt", "")
                second_match = re.search(r"SECOND\s*—", prompt)
                if second_match:
                    return prompt[second_match.start():]
            except (json.JSONDecodeError, OSError):
                pass
        return ""

    # Find the closing quote of the prompt
    closing = content.rfind('"')
    if closing > second_match.start():
        return content[second_match.start():closing]
    return content[second_match.start():]


_UNFIXED_SECOND_BRANCH = _extract_ask_bootcamper_second_branch(
    _UNFIXED_HOOK_REGISTRY
)


# ---------------------------------------------------------------------------
# Test 1 — Module 01 non-question steps content preserved
# ---------------------------------------------------------------------------


class TestModule01NonQuestionStepsPreserved:
    """Module 01 non-question steps (2, 3, 4, 6) are unchanged.

    **Validates: Requirements 3.1, 3.2**

    These steps contain informational content and non-interactive
    work that must not gain stop-and-wait directives.
    """

    def test_step2_content_unchanged(self) -> None:
        """Step 2 (data privacy reminder) is unchanged."""
        content = _read_file(_MODULE_01)
        current = _extract_step_module01(content, 2)
        baseline = _UNFIXED_MODULE01_STEPS[2]
        assert baseline, "Baseline for Step 2 is empty"
        assert current == baseline, (
            f"Step 2 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step3_content_unchanged(self) -> None:
        """Step 3 (design pattern gallery offer) is unchanged."""
        content = _read_file(_MODULE_01)
        current = _extract_step_module01(content, 3)
        baseline = _UNFIXED_MODULE01_STEPS[3]
        assert baseline, "Baseline for Step 3 is empty"
        assert current == baseline, (
            f"Step 3 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step4_content_unchanged(self) -> None:
        """Step 4 (pattern presentation) is unchanged."""
        content = _read_file(_MODULE_01)
        current = _extract_step_module01(content, 4)
        baseline = _UNFIXED_MODULE01_STEPS[4]
        assert baseline, "Baseline for Step 4 is empty"
        assert current == baseline, (
            f"Step 4 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step6_content_unchanged(self) -> None:
        """Step 6 (infer details from response) is unchanged."""
        content = _read_file(_MODULE_01)
        current = _extract_step_module01(content, 6)
        baseline = _UNFIXED_MODULE01_STEPS[6]
        assert baseline, "Baseline for Step 6 is empty"
        assert current == baseline, (
            f"Step 6 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Module 01 Phase 2 non-question steps content preserved
# ---------------------------------------------------------------------------


class TestPhase2NonQuestionStepsPreserved:
    """Phase 2 non-question steps (10-15, 18) are unchanged.

    **Validates: Requirements 3.1, 3.2, 3.4**

    These steps contain informational and document-creation work
    that must not gain stop-and-wait directives.
    """

    def test_step10_content_unchanged(self) -> None:
        """Step 10 (visual explanations) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 10)
        baseline = _UNFIXED_PHASE2_STEPS[10]
        assert baseline, "Baseline for Step 10 is empty"
        assert current == baseline, (
            f"Step 10 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step11_content_unchanged(self) -> None:
        """Step 11 (identify scenario) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 11)
        baseline = _UNFIXED_PHASE2_STEPS[11]
        assert baseline, "Baseline for Step 11 is empty"
        assert current == baseline, (
            f"Step 11 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step12_content_unchanged(self) -> None:
        """Step 12 (create problem statement) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 12)
        baseline = _UNFIXED_PHASE2_STEPS[12]
        assert baseline, "Baseline for Step 12 is empty"
        assert current == baseline, (
            f"Step 12 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step13_content_unchanged(self) -> None:
        """Step 13 (update README) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 13)
        baseline = _UNFIXED_PHASE2_STEPS[13]
        assert baseline, "Baseline for Step 13 is empty"
        assert current == baseline, (
            f"Step 13 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step14_content_unchanged(self) -> None:
        """Step 14 (propose solution approach) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 14)
        baseline = _UNFIXED_PHASE2_STEPS[14]
        assert baseline, "Baseline for Step 14 is empty"
        assert current == baseline, (
            f"Step 14 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step15_content_unchanged(self) -> None:
        """Step 15 (Senzing value restatement) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 15)
        baseline = _UNFIXED_PHASE2_STEPS[15]
        assert baseline, "Baseline for Step 15 is empty"
        assert current == baseline, (
            f"Step 15 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step18_content_unchanged(self) -> None:
        """Step 18 (transition to Module 4) is unchanged."""
        content = _read_file(_MODULE_01_PHASE2)
        current = _extract_step_phase2(content, 18)
        baseline = _UNFIXED_PHASE2_STEPS[18]
        assert baseline, "Baseline for Step 18 is empty"
        assert current == baseline, (
            f"Step 18 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Onboarding non-question steps content preserved
# ---------------------------------------------------------------------------


class TestOnboardingNonQuestionStepsPreserved:
    """Onboarding non-question steps (0, 1, 1b, 3, 4, 4c) unchanged.

    **Validates: Requirements 3.1, 3.2, 3.4**

    These steps contain setup, prerequisite, and informational
    content that must not gain stop-and-wait directives.
    """

    def test_step0_content_unchanged(self) -> None:
        """Step 0 (setup preamble) is unchanged."""
        content = _read_file(_ONBOARDING)
        current = _extract_onboarding_step(content, "0")
        baseline = _UNFIXED_ONBOARDING_STEPS["0"]
        assert baseline, "Baseline for Step 0 is empty"
        assert current == baseline, (
            f"Step 0 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step1_content_unchanged(self) -> None:
        """Step 1 (directory structure) is unchanged."""
        content = _read_file(_ONBOARDING)
        current = _extract_onboarding_step(content, "1")
        baseline = _UNFIXED_ONBOARDING_STEPS["1"]
        assert baseline, "Baseline for Step 1 is empty"
        assert current == baseline, (
            f"Step 1 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step1b_content_unchanged(self) -> None:
        """Step 1b (team detection) is unchanged."""
        content = _read_file(_ONBOARDING)
        current = _extract_onboarding_step(content, "1b")
        baseline = _UNFIXED_ONBOARDING_STEPS["1b"]
        assert baseline, "Baseline for Step 1b is empty"
        assert current == baseline, (
            f"Step 1b content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step3_content_unchanged(self) -> None:
        """Step 3 (prerequisite check) is unchanged."""
        content = _read_file(_ONBOARDING)
        current = _extract_onboarding_step(content, "3")
        baseline = _UNFIXED_ONBOARDING_STEPS["3"]
        assert baseline, "Baseline for Step 3 is empty"
        assert current == baseline, (
            f"Step 3 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_step4_content_unchanged(self) -> None:
        """Step 4 (bootcamp introduction) is unchanged."""
        content = _read_file(_ONBOARDING)
        current = _extract_onboarding_step(content, "4")
        baseline = _UNFIXED_ONBOARDING_STEPS["4"]
        assert baseline, "Baseline for Step 4 is empty"
        assert current == baseline, (
            f"Step 4 content changed.\n"
            f"Expected: {baseline[:300]}\n"
            f"Got: {current[:300]}"
        )

    # Step 4c removed from non-question steps — it now has a 👉 question with 🛑 STOP


# ---------------------------------------------------------------------------
# Test 4 — ask-bootcamper SECOND branch preserved
# ---------------------------------------------------------------------------


class TestAskBootcamperSecondBranchPreserved:
    """The SECOND branch of ask-bootcamper hook prompt is preserved.

    **Validates: Requirements 3.3**

    The recap + closing question logic must remain functionally
    identical after the fix.
    """

    def test_second_branch_present(self) -> None:
        """The SECOND branch marker exists in the hook prompt."""
        content = _read_file(_HOOK_REGISTRY)
        second_branch = _extract_ask_bootcamper_second_branch(content)
        assert second_branch, (
            "SECOND branch not found in ask-bootcamper prompt"
        )

    def test_second_branch_content_unchanged(self) -> None:
        """The SECOND branch content matches the baseline."""
        content = _read_file(_HOOK_REGISTRY)
        current = _extract_ask_bootcamper_second_branch(content)
        assert current == _UNFIXED_SECOND_BRANCH, (
            f"SECOND branch content changed.\n"
            f"Expected: {_UNFIXED_SECOND_BRANCH[:300]}\n"
            f"Got: {current[:300]}"
        )

    def test_second_branch_has_recap_logic(self) -> None:
        """The SECOND branch contains recap instructions."""
        content = _read_file(_HOOK_REGISTRY)
        second = _extract_ask_bootcamper_second_branch(content)
        assert "recap" in second.lower(), (
            "SECOND branch missing recap logic"
        )

    def test_second_branch_has_closing_question(self) -> None:
        """The SECOND branch contains closing question logic."""
        content = _read_file(_HOOK_REGISTRY)
        second = _extract_ask_bootcamper_second_branch(content)
        assert "👉" in second, (
            "SECOND branch missing 👉 closing question marker"
        )


# ---------------------------------------------------------------------------
# Test 5 — YAML frontmatter preserved in all affected files
# ---------------------------------------------------------------------------


class TestYAMLFrontmatterPreserved:
    """YAML frontmatter is preserved in all affected steering files.

    **Validates: Requirements 3.1, 3.2**

    Each affected file must retain its original YAML frontmatter
    (inclusion: manual or inclusion: always).
    """

    def test_all_files_have_frontmatter(self) -> None:
        """Every affected file has YAML frontmatter."""
        for path, name in _ALL_AFFECTED_FILES:
            content = _read_file(path)
            fm = _extract_yaml_frontmatter(content)
            assert fm is not None, (
                f"{name} is missing YAML frontmatter"
            )

    def test_all_frontmatter_matches_baseline(self) -> None:
        """Every affected file's frontmatter matches baseline."""
        for path, name in _ALL_AFFECTED_FILES:
            content = _read_file(path)
            current_fm = _extract_yaml_frontmatter(content)
            baseline_fm = _UNFIXED_FRONTMATTER[name]
            assert current_fm == baseline_fm, (
                f"{name} frontmatter changed.\n"
                f"Expected: {baseline_fm}\n"
                f"Got: {current_fm}"
            )

    def test_agent_instructions_has_inclusion_always(self) -> None:
        """agent-instructions.md has inclusion: always."""
        content = _read_file(_AGENT_INSTRUCTIONS)
        fm = _extract_yaml_frontmatter(content)
        assert fm is not None, "Missing frontmatter"
        assert "inclusion: always" in fm, (
            f"Expected 'inclusion: always', got: {fm}"
        )

    def test_manual_files_have_inclusion_manual(self) -> None:
        """All non-agent-instructions files have inclusion: manual."""
        manual_files = [
            (p, n) for p, n in _ALL_AFFECTED_FILES
            if p != _AGENT_INSTRUCTIONS
        ]
        for path, name in manual_files:
            content = _read_file(path)
            fm = _extract_yaml_frontmatter(content)
            assert fm is not None, f"{name} missing frontmatter"
            assert "inclusion: manual" in fm, (
                f"{name}: expected 'inclusion: manual', got: {fm}"
            )


# ---------------------------------------------------------------------------
# Test 6 — Step numbering and checkpoint counts preserved
# ---------------------------------------------------------------------------


class TestStepNumberingPreserved:
    """Step numbering and checkpoint counts are unchanged.

    **Validates: Requirements 3.1, 3.4**

    The fix must not alter step numbering or checkpoint counts.
    """

    def test_module01_step_numbers_unchanged(self) -> None:
        """Module 01 step numbers match baseline."""
        content = _read_file(_MODULE_01)
        current = re.compile(
            r"^(\d+)\.\s+\*\*", re.MULTILINE
        ).findall(content)
        assert current == _MODULE01_STEP_NUMBERS, (
            f"Module 01 step numbers changed.\n"
            f"Expected: {_MODULE01_STEP_NUMBERS}\n"
            f"Got: {current}"
        )

    def test_phase2_step_numbers_unchanged(self) -> None:
        """Phase 2 step numbers match baseline."""
        content = _read_file(_MODULE_01_PHASE2)
        current = re.compile(
            r"^(\d+)\.\s+\*\*", re.MULTILINE
        ).findall(content)
        assert current == _PHASE2_STEP_NUMBERS, (
            f"Phase 2 step numbers changed.\n"
            f"Expected: {_PHASE2_STEP_NUMBERS}\n"
            f"Got: {current}"
        )

    def test_module01_checkpoint_count_unchanged(self) -> None:
        """Module 01 checkpoint count matches baseline."""
        content = _read_file(_MODULE_01)
        current = len(_CHECKPOINT_RE.findall(content))
        assert current == _MODULE01_CHECKPOINT_COUNT, (
            f"Module 01 checkpoint count changed. "
            f"Expected {_MODULE01_CHECKPOINT_COUNT}, "
            f"got {current}."
        )

    def test_phase2_checkpoint_count_unchanged(self) -> None:
        """Phase 2 checkpoint count matches baseline."""
        content = _read_file(_MODULE_01_PHASE2)
        current = len(_CHECKPOINT_RE.findall(content))
        assert current == _PHASE2_CHECKPOINT_COUNT, (
            f"Phase 2 checkpoint count changed. "
            f"Expected {_PHASE2_CHECKPOINT_COUNT}, "
            f"got {current}."
        )


# ---------------------------------------------------------------------------
# Test 7 — Hook .kiro.hook JSON files are byte-identical
# ---------------------------------------------------------------------------


class TestHookFilesUnchanged:
    """Hook .kiro.hook JSON files are byte-identical to baseline.

    **Validates: Requirements 3.5**

    Only hook-registry.md prompt text changes, not the hook files.
    """

    def test_all_hook_files_byte_identical(self) -> None:
        """Every .kiro.hook file matches its baseline bytes."""
        for path, name in _HOOK_FILES:
            current = path.read_bytes()
            baseline = _UNFIXED_HOOK_BYTES[name]
            assert current == baseline, (
                f"{name} has been modified. "
                f"Expected {len(baseline)} bytes, "
                f"got {len(current)} bytes."
            )

    def test_ask_bootcamper_hook_unchanged(self) -> None:
        """ask-bootcamper.kiro.hook specifically is unchanged."""
        hook_path = _HOOKS_DIR / "ask-bootcamper.kiro.hook"
        current = hook_path.read_bytes()
        baseline = _UNFIXED_HOOK_BYTES["ask-bootcamper.kiro.hook"]
        assert current == baseline, (
            "ask-bootcamper.kiro.hook has been modified."
        )


# ---------------------------------------------------------------------------
# PBT Test 1 — Random non-question steps match baseline snapshot
# ---------------------------------------------------------------------------

# Build a combined list of (file_label, step_id, baseline_content)
# for all non-question steps across all three files.
_ALL_NON_QUESTION_STEPS: list[tuple[str, str, str]] = []

for _step_num in _MODULE01_NON_QUESTION_STEPS:
    _ALL_NON_QUESTION_STEPS.append((
        "module-01",
        f"step_{_step_num}",
        _UNFIXED_MODULE01_STEPS[_step_num],
    ))

for _step_num in _PHASE2_NON_QUESTION_STEPS:
    _ALL_NON_QUESTION_STEPS.append((
        "phase2",
        f"step_{_step_num}",
        _UNFIXED_PHASE2_STEPS[_step_num],
    ))

for _step_id in _ONBOARDING_NON_QUESTION_STEP_IDS:
    _ALL_NON_QUESTION_STEPS.append((
        "onboarding",
        f"step_{_step_id}",
        _UNFIXED_ONBOARDING_STEPS[_step_id],
    ))


def _get_current_step_content(
    file_label: str, step_id: str
) -> str:
    """Read the current content of a non-question step."""
    num_str = step_id.replace("step_", "")

    if file_label == "module-01":
        content = _read_file(_MODULE_01)
        return _extract_step_module01(content, int(num_str))

    if file_label == "phase2":
        content = _read_file(_MODULE_01_PHASE2)
        return _extract_step_phase2(content, int(num_str))

    if file_label == "onboarding":
        content = _read_file(_ONBOARDING)
        return _extract_onboarding_step(content, num_str)

    return ""


class TestNonQuestionStepsMatchBaseline:
    """PBT — Random non-question steps match their baseline snapshot.

    **Validates: Requirements 3.1, 3.2, 3.4**

    Use Hypothesis to generate random non-question step identifiers
    from all three files and verify content matches baseline.
    """

    @given(
        step_info=st.sampled_from(_ALL_NON_QUESTION_STEPS),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_question_step_matches_baseline(
        self,
        step_info: tuple[str, str, str],
    ) -> None:
        """For any non-question step, content matches baseline."""
        file_label, step_id, baseline = step_info
        assert baseline, (
            f"Baseline for {file_label}/{step_id} is empty"
        )
        current = _get_current_step_content(file_label, step_id)
        assert current == baseline, (
            f"{file_label}/{step_id} content differs from "
            f"baseline.\n"
            f"Baseline (first 200 chars): {baseline[:200]}\n"
            f"Current (first 200 chars): {current[:200]}"
        )


# ---------------------------------------------------------------------------
# PBT Test 2 — YAML frontmatter preserved across all affected files
# ---------------------------------------------------------------------------


class TestFrontmatterPreservedPBT:
    """PBT — YAML frontmatter is preserved in all affected files.

    **Validates: Requirements 3.1, 3.2**

    Use Hypothesis to generate random affected file selections and
    verify frontmatter matches baseline.
    """

    @given(
        file_info=st.sampled_from(_ALL_AFFECTED_FILES),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_frontmatter_matches_baseline(
        self,
        file_info: tuple[Path, str],
    ) -> None:
        """For any affected file, frontmatter matches baseline."""
        path, name = file_info
        content = _read_file(path)
        current_fm = _extract_yaml_frontmatter(content)
        baseline_fm = _UNFIXED_FRONTMATTER[name]
        assert current_fm == baseline_fm, (
            f"{name} frontmatter changed.\n"
            f"Expected: {baseline_fm}\n"
            f"Got: {current_fm}"
        )


# ---------------------------------------------------------------------------
# PBT Test 3 — No hard-stop block in non-question steps
# ---------------------------------------------------------------------------


class TestNoHardStopInNonQuestionSteps:
    """PBT — Non-question steps have no 🛑 STOP hard-stop block.

    **Validates: Requirements 3.1, 3.2, 3.4**

    Use Hypothesis to generate random non-question steps and verify
    none of them contain a hard-stop block (🛑 STOP).
    """

    @given(
        step_info=st.sampled_from(_ALL_NON_QUESTION_STEPS),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_no_hard_stop_in_non_question_step(
        self,
        step_info: tuple[str, str, str],
    ) -> None:
        """No non-question step should contain a 🛑 STOP block."""
        file_label, step_id, _baseline = step_info
        current = _get_current_step_content(file_label, step_id)
        assert current, (
            f"Step {file_label}/{step_id} not found"
        )
        assert not _HARD_STOP_PATTERN.search(current), (
            f"{file_label}/{step_id} contains a 🛑 STOP "
            f"hard-stop block, but this is a non-question step "
            f"that should not have one."
        )
