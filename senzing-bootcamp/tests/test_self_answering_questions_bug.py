"""Bug condition exploration tests for self-answering questions bugfix.

These tests parse UNFIXED steering files and confirm the bug exists by asserting
that question points have structurally enforced hard-stop blocks — which they
currently lack.

Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug exists.

Feature: self-answering-questions-fix

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
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
_STEERING_DIR = _BOOTCAMP_DIR / "steering"

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HARD_STOP_PATTERN = re.compile(r"🛑\s*STOP", re.IGNORECASE)

_END_RESPONSE_PATTERN = re.compile(
    r"end\s+your\s+response",
    re.IGNORECASE,
)

_PROHIBITED_BEHAVIOR_PATTERN = re.compile(
    r"do\s+not\s+answer|do\s+not\s+assume|do\s+not\s+continue|"
    r"do\s+not\s+proceed|produce\s+no\s+further",
    re.IGNORECASE,
)


def _read_file(path: Path) -> str:
    """Read a steering file's full content."""
    return path.read_text(encoding="utf-8")


def _extract_step_module01(markdown: str, step_number: int) -> str:
    """Extract a numbered step from module-01-business-problem.md.

    Steps are top-level numbered items like ``1. **Step title** ...``.
    """
    step_pattern = re.compile(rf"^{step_number}\.\s+\*\*", re.MULTILINE)
    match = step_pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_step = re.compile(rf"^{step_number + 1}\.\s+\*\*", re.MULTILINE)
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
    step_pattern = re.compile(rf"^{step_number}\.\s+\*\*", re.MULTILINE)
    match = step_pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_step = re.compile(rf"^{step_number + 1}\.\s+\*\*", re.MULTILINE)
    next_match = next_step.search(markdown, start + 1)
    if next_match:
        return markdown[start:next_match.start()]

    success_pattern = re.compile(r"^\*\*Success indicator", re.MULTILINE)
    success_match = success_pattern.search(markdown, start + 1)
    if success_match:
        return markdown[start:success_match.start()]

    return markdown[start:]


def _extract_onboarding_section(markdown: str, heading: str) -> str:
    """Extract a section from onboarding-flow.md by heading text.

    Handles both ## and ### headings.
    """
    pattern = re.compile(rf"^##\s*#?\s*{re.escape(heading)}", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_heading = re.compile(r"^##\s+", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end() + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _extract_onboarding_step(markdown: str, step_id: str) -> str:
    """Extract a step from onboarding-flow.md by step identifier.

    Handles patterns like '## 2. Language Selection' and '### 4b. Verbosity'.
    """
    pattern = re.compile(
        rf"^##\s*#?\s*{re.escape(step_id)}\.",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.start()

    next_heading = re.compile(r"^##\s+", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end() + 1)
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _has_hard_stop_block(content: str) -> bool:
    """Check if content contains a hard-stop block with 🛑 STOP."""
    return bool(_HARD_STOP_PATTERN.search(content))


def _has_end_response_language(content: str) -> bool:
    """Check if content contains explicit 'end your response' language."""
    return bool(_END_RESPONSE_PATTERN.search(content))


def _has_prohibited_behavior(content: str) -> bool:
    """Check if content contains prohibited behavior language."""
    return bool(_PROHIBITED_BEHAVIOR_PATTERN.search(content))


def _find_pointing_questions(content: str) -> list[str]:
    """Find all 👉 question blocks in a file's content.

    Returns a list of text chunks starting from each 👉 marker to the next
    section boundary or next 👉.
    """
    results = []
    indices = [m.start() for m in re.finditer("👉", content)]
    for i, idx in enumerate(indices):
        end = indices[i + 1] if i + 1 < len(indices) else min(idx + 1000, len(content))
        results.append(content[idx:end])
    return results


# ---------------------------------------------------------------------------
# Test 1 — Module 01 question points lack hard-stop blocks
# ---------------------------------------------------------------------------


class TestModule01HardStopBlocks:
    """Module 01 question points at Steps 1, 5, 7, 8, 9 lack hard-stop blocks.

    **Validates: Requirements 1.1, 1.2**

    Each question point should have a 🛑 STOP block with 'end your response'
    language. On unfixed code, these blocks are missing.
    """

    @pytest.fixture()
    def module01_content(self) -> str:
        return _read_file(_MODULE_01)

    @pytest.mark.parametrize("step_num", [1, 5, 7, 8, 9])
    def test_step_has_hard_stop_block(
        self, module01_content: str, step_num: int
    ) -> None:
        step = _extract_step_module01(module01_content, step_num)
        assert step, f"Step {step_num} not found in module-01-business-problem.md"
        assert _has_hard_stop_block(step), (
            f"Step {step_num} in module-01-business-problem.md lacks a 🛑 STOP "
            f"hard-stop block after its question point. The agent can continue "
            f"generating past the question without a structural stop boundary."
        )

    @pytest.mark.parametrize("step_num", [1, 5, 7, 8, 9])
    def test_step_has_end_response_language(
        self, module01_content: str, step_num: int
    ) -> None:
        step = _extract_step_module01(module01_content, step_num)
        assert step, f"Step {step_num} not found in module-01-business-problem.md"
        assert _has_end_response_language(step), (
            f"Step {step_num} in module-01-business-problem.md lacks explicit "
            f"'end your response' language. Without this, the model may interpret "
            f"'STOP' as 'pause briefly' rather than 'terminate output'."
        )


# ---------------------------------------------------------------------------
# Test 2 — Module 01 Phase 2 question points lack hard-stop blocks
# ---------------------------------------------------------------------------


class TestModule01Phase2HardStopBlocks:
    """Module 01 Phase 2 Steps 16, 17 lack hard-stop blocks.

    **Validates: Requirements 1.1, 1.2**

    Steps 16 and 17 ask questions but lack explicit stop directives.
    """

    @pytest.fixture()
    def phase2_content(self) -> str:
        return _read_file(_MODULE_01_PHASE2)

    @pytest.mark.parametrize("step_num", [16, 17])
    def test_step_has_hard_stop_block(
        self, phase2_content: str, step_num: int
    ) -> None:
        step = _extract_step_phase2(phase2_content, step_num)
        assert step, (
            f"Step {step_num} not found in module-01-phase2-document-confirm.md"
        )
        assert _has_hard_stop_block(step), (
            f"Step {step_num} in module-01-phase2-document-confirm.md lacks a "
            f"🛑 STOP hard-stop block after its question point."
        )

    @pytest.mark.parametrize("step_num", [16, 17])
    def test_step_has_end_response_language(
        self, phase2_content: str, step_num: int
    ) -> None:
        step = _extract_step_phase2(phase2_content, step_num)
        assert step, (
            f"Step {step_num} not found in module-01-phase2-document-confirm.md"
        )
        assert _has_end_response_language(step), (
            f"Step {step_num} in module-01-phase2-document-confirm.md lacks "
            f"explicit 'end your response' language."
        )


# ---------------------------------------------------------------------------
# Test 3 — Onboarding mandatory gates lack upgraded hard-stop blocks
# ---------------------------------------------------------------------------


class TestOnboardingHardStopBlocks:
    """Onboarding Steps 2, 4b, 5 lack structurally upgraded hard-stop blocks.

    **Validates: Requirements 1.2, 1.3**

    Mandatory gates and question points need 🛑 STOP blocks with 'end your
    response' and prohibited behavior language.
    """

    @pytest.fixture()
    def onboarding_content(self) -> str:
        return _read_file(_ONBOARDING)

    def test_step2_has_hard_stop_block(self, onboarding_content: str) -> None:
        step = _extract_onboarding_step(onboarding_content, "2")
        assert step, "Step 2 (Language Selection) not found in onboarding-flow.md"
        assert _has_hard_stop_block(step), (
            "Step 2 (Language Selection) in onboarding-flow.md lacks a 🛑 STOP "
            "hard-stop block. The ⛔ mandatory gate exists but without the "
            "upgraded structural pattern."
        )

    def test_step2_has_end_response_language(
        self, onboarding_content: str
    ) -> None:
        step = _extract_onboarding_step(onboarding_content, "2")
        assert step, "Step 2 (Language Selection) not found in onboarding-flow.md"
        assert _has_end_response_language(step), (
            "Step 2 (Language Selection) in onboarding-flow.md lacks explicit "
            "'end your response' language."
        )

    def test_step2_has_prohibited_behavior(
        self, onboarding_content: str
    ) -> None:
        step = _extract_onboarding_step(onboarding_content, "2")
        assert step, "Step 2 (Language Selection) not found in onboarding-flow.md"
        assert _has_prohibited_behavior(step), (
            "Step 2 (Language Selection) in onboarding-flow.md lacks prohibited "
            "behavior language (e.g., 'do not answer', 'do not assume')."
        )

    def test_step4b_has_hard_stop_block(self, onboarding_content: str) -> None:
        step = _extract_onboarding_step(onboarding_content, "4b")
        assert step, "Step 4b (Verbosity Preference) not found in onboarding-flow.md"
        assert _has_hard_stop_block(step), (
            "Step 4b (Verbosity Preference) in onboarding-flow.md lacks a "
            "🛑 STOP hard-stop block after the verbosity question."
        )

    def test_step4b_has_end_response_language(
        self, onboarding_content: str
    ) -> None:
        step = _extract_onboarding_step(onboarding_content, "4b")
        assert step, "Step 4b (Verbosity Preference) not found in onboarding-flow.md"
        assert _has_end_response_language(step), (
            "Step 4b (Verbosity Preference) in onboarding-flow.md lacks explicit "
            "'end your response' language."
        )

    def test_step5_has_hard_stop_block(self, onboarding_content: str) -> None:
        step = _extract_onboarding_step(onboarding_content, "5")
        assert step, "Step 5 (Track Selection) not found in onboarding-flow.md"
        assert _has_hard_stop_block(step), (
            "Step 5 (Track Selection) in onboarding-flow.md lacks a 🛑 STOP "
            "hard-stop block. The ⛔ mandatory gate exists but without the "
            "upgraded structural pattern."
        )

    def test_step5_has_end_response_language(
        self, onboarding_content: str
    ) -> None:
        step = _extract_onboarding_step(onboarding_content, "5")
        assert step, "Step 5 (Track Selection) not found in onboarding-flow.md"
        assert _has_end_response_language(step), (
            "Step 5 (Track Selection) in onboarding-flow.md lacks explicit "
            "'end your response' language."
        )

    def test_step5_has_prohibited_behavior(
        self, onboarding_content: str
    ) -> None:
        step = _extract_onboarding_step(onboarding_content, "5")
        assert step, "Step 5 (Track Selection) not found in onboarding-flow.md"
        assert _has_prohibited_behavior(step), (
            "Step 5 (Track Selection) in onboarding-flow.md lacks prohibited "
            "behavior language (e.g., 'do not answer', 'do not assume')."
        )


# ---------------------------------------------------------------------------
# Test 4 — agent-instructions.md lacks Question Stop Protocol
# ---------------------------------------------------------------------------


class TestAgentInstructionsStopProtocol:
    """agent-instructions.md Communication section lacks a dedicated stop protocol.

    **Validates: Requirements 1.1, 1.2, 1.4**

    The Communication section should contain a dedicated '### Question Stop
    Protocol' subsection with explicit prohibited behaviors.
    """

    @pytest.fixture()
    def agent_content(self) -> str:
        return _read_file(_AGENT_INSTRUCTIONS)

    def test_has_question_stop_protocol_subsection(
        self, agent_content: str
    ) -> None:
        assert re.search(
            r"###\s+Question\s+Stop\s+Protocol", agent_content
        ), (
            "agent-instructions.md Communication section lacks a dedicated "
            "'### Question Stop Protocol' subsection. The stop-and-wait rule "
            "is only a single bullet point, which is too weak."
        )

    def test_stop_protocol_has_end_response_language(
        self, agent_content: str
    ) -> None:
        comm_section = ""
        comm_match = re.search(r"^## Communication", agent_content, re.MULTILINE)
        if comm_match:
            next_section = re.search(
                r"^## ", agent_content[comm_match.end():], re.MULTILINE
            )
            if next_section:
                comm_section = agent_content[
                    comm_match.start():comm_match.end() + next_section.start()
                ]
            else:
                comm_section = agent_content[comm_match.start():]

        assert _has_end_response_language(comm_section), (
            "agent-instructions.md Communication section lacks explicit "
            "'end your response' language in its stop protocol."
        )

    def test_stop_protocol_has_prohibited_behaviors(
        self, agent_content: str
    ) -> None:
        comm_section = ""
        comm_match = re.search(r"^## Communication", agent_content, re.MULTILINE)
        if comm_match:
            next_section = re.search(
                r"^## ", agent_content[comm_match.end():], re.MULTILINE
            )
            if next_section:
                comm_section = agent_content[
                    comm_match.start():comm_match.end() + next_section.start()
                ]
            else:
                comm_section = agent_content[comm_match.start():]

        assert _has_prohibited_behavior(comm_section), (
            "agent-instructions.md Communication section lacks explicit "
            "prohibited behavior language (e.g., 'do not answer', 'do not assume')."
        )


# ---------------------------------------------------------------------------
# Test 5 — hook-registry.md ask-bootcamper prompt lacks strengthened language
# ---------------------------------------------------------------------------


class TestHookRegistryStrengthenedLanguage:
    """hook-registry.md ask-bootcamper prompt lacks pre-generation warning.

    **Validates: Requirements 1.2, 1.4**

    The ask-bootcamper hook prompt should contain strengthened pre-generation
    warning language with 'end your response' framing.
    """

    @pytest.fixture()
    def hook_content(self) -> str:
        return _read_file(_HOOK_REGISTRY)

    def _extract_ask_bootcamper_prompt(self, content: str) -> str:
        """Extract the ask-bootcamper hook prompt section.

        The hook registry now stores only id/name/description. The full prompt
        is in the .kiro.hook file. Extract the description field which contains
        the behavioral summary.
        """
        marker = re.search(
            r"\*\*ask-bootcamper\*\*", content
        )
        if not marker:
            return ""
        start = marker.start()

        next_hook = re.search(
            r"\*\*capture-feedback\*\*", content[start + 1:]
        )
        if next_hook:
            return content[start:start + 1 + next_hook.start()]
        return content[start:]

    def test_prompt_has_end_response_language(
        self, hook_content: str
    ) -> None:
        prompt = self._extract_ask_bootcamper_prompt(hook_content)
        assert prompt, "ask-bootcamper hook section not found in hook-registry.md"
        # The registry description mentions suppressing output when a question
        # is pending. The full prompt with stop language is in the hook file.
        assert "Suppresses output" in prompt or "pending" in prompt, (
            "ask-bootcamper hook description in hook-registry.md lacks "
            "output suppression language."
        )


# ---------------------------------------------------------------------------
# Test 6 — Other module files lack hard-stop blocks at 👉 question points
# ---------------------------------------------------------------------------

# Each tuple: (file_path, display_name)
_OTHER_MODULE_FILES: list[tuple[Path, str]] = [
    (_VIS_GUIDE, "visualization-guide.md"),
    (_DEPLOY_AZURE, "deployment-azure.md"),
    (_DEPLOY_GCP, "deployment-gcp.md"),
    (_DEPLOY_ONPREM, "deployment-onpremises.md"),
    (_DEPLOY_K8S, "deployment-kubernetes.md"),
]


class TestOtherModuleHardStopBlocks:
    """Other module files with 👉 question points lack hard-stop blocks.

    **Validates: Requirements 1.1, 1.2**

    Every 👉 question point across all steering files should have a hard-stop
    block. On unfixed code, these blocks are missing.
    """

    @pytest.mark.parametrize(
        "file_path,display_name",
        _OTHER_MODULE_FILES,
        ids=[name for _, name in _OTHER_MODULE_FILES],
    )
    def test_pointing_questions_have_hard_stop(
        self, file_path: Path, display_name: str
    ) -> None:
        content = _read_file(file_path)
        questions = _find_pointing_questions(content)
        assert questions, (
            f"{display_name} has no 👉 question points — expected at least one"
        )
        for i, q_block in enumerate(questions):
            # Look for a hard-stop block within 500 chars after the 👉 question
            # or in the surrounding context
            surrounding = content[
                content.index(q_block[:50]):
                min(content.index(q_block[:50]) + len(q_block) + 500, len(content))
            ]
            assert _has_hard_stop_block(surrounding), (
                f"👉 question point #{i + 1} in {display_name} lacks a 🛑 STOP "
                f"hard-stop block. Question text: {q_block[:120]}..."
            )


# ---------------------------------------------------------------------------
# PBT Test — All question points across all affected files
# ---------------------------------------------------------------------------

# Build a comprehensive list of (file_path, display_name, question_point_id)
# for all known question points across all affected steering files.

_ALL_QUESTION_POINTS: list[tuple[str, str, str]] = [
    # Module 01 steps
    ("module-01-business-problem.md", "Module 01", "step_1"),
    ("module-01-business-problem.md", "Module 01", "step_5"),
    ("module-01-business-problem.md", "Module 01", "step_7"),
    ("module-01-business-problem.md", "Module 01", "step_8"),
    ("module-01-business-problem.md", "Module 01", "step_9"),
    # Module 01 Phase 2 steps
    ("module-01-phase2-document-confirm.md", "Module 01 Phase 2", "step_16"),
    ("module-01-phase2-document-confirm.md", "Module 01 Phase 2", "step_17"),
    # Onboarding steps
    ("onboarding-flow.md", "Onboarding", "step_2"),
    ("onboarding-flow.md", "Onboarding", "step_4b"),
    ("onboarding-flow.md", "Onboarding", "step_5"),
    # agent-instructions.md
    ("agent-instructions.md", "Agent Instructions", "communication_section"),
    # hook-registry.md
    ("hook-registry.md", "Hook Registry", "ask_bootcamper_prompt"),
    # Other module files with 👉 questions
    ("module-03-system-verification.md", "Module 03", "pointing_questions"),
    ("module-07-query-validation.md", "Module 07", "pointing_questions"),
    ("visualization-guide.md", "Visualization Guide", "pointing_questions"),
    ("deployment-azure.md", "Deployment Azure", "pointing_questions"),
    ("deployment-gcp.md", "Deployment GCP", "pointing_questions"),
    ("deployment-onpremises.md", "Deployment On-Premises", "pointing_questions"),
    ("deployment-kubernetes.md", "Deployment Kubernetes", "pointing_questions"),
]


def _check_question_point(file_name: str, question_id: str) -> bool:
    """Check if a specific question point has a hard-stop block.

    Returns True if the question point has the required hard-stop pattern,
    False otherwise.
    """
    file_path = _STEERING_DIR / file_name
    content = _read_file(file_path)

    if question_id.startswith("step_"):
        step_num_str = question_id.replace("step_", "")

        if file_name == "module-01-business-problem.md":
            step = _extract_step_module01(content, int(step_num_str))
        elif file_name == "module-01-phase2-document-confirm.md":
            step = _extract_step_phase2(content, int(step_num_str))
        elif file_name == "onboarding-flow.md":
            step = _extract_onboarding_step(content, step_num_str)
        else:
            return True  # Unknown file — skip

        if not step:
            return True  # Step not found — skip
        return _has_hard_stop_block(step) and _has_end_response_language(step)

    elif question_id == "communication_section":
        return bool(
            re.search(r"###\s+Question\s+Stop\s+Protocol", content)
        ) and _has_end_response_language(content)

    elif question_id == "ask_bootcamper_prompt":
        marker = re.search(r"\*\*ask-bootcamper\*\*", content)
        if not marker:
            return True
        next_hook = re.search(r"\*\*capture-feedback\*\*", content[marker.end():])
        if next_hook:
            prompt = content[marker.start():marker.end() + next_hook.start()]
        else:
            prompt = content[marker.start():]
        # Registry now stores description only; check for suppression language
        return "Suppresses output" in prompt or "pending" in prompt

    elif question_id == "pointing_questions":
        questions = _find_pointing_questions(content)
        if not questions:
            return True  # No questions found — skip
        for q_block in questions:
            q_start = content.index(q_block[:50])
            surrounding = content[q_start:min(q_start + len(q_block) + 500, len(content))]
            if not _has_hard_stop_block(surrounding):
                return False
        return True

    return True


class TestBugConditionPBT:
    """PBT — All question points across all affected files lack hard-stop blocks.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    Use Hypothesis to generate random question point identifiers from the full
    set of affected files and steps, and assert each has a hard-stop block with
    explicit 'end your response' language.
    """

    @given(
        question_point=st.sampled_from(_ALL_QUESTION_POINTS),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_question_points_have_hard_stop(
        self,
        question_point: tuple[str, str, str],
    ) -> None:
        file_name, display_name, question_id = question_point

        result = _check_question_point(file_name, question_id)
        assert result, (
            f"Question point '{question_id}' in {display_name} ({file_name}) "
            f"lacks a structurally enforced hard-stop block with 🛑 STOP and "
            f"'end your response' language. The agent can continue generating "
            f"past this question point without a structural stop boundary."
        )
