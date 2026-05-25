"""Unit and property-based tests for the enforce-sequential-steps hook.

Validates the hook's metadata, registry placement, prompt content,
and the step-skip detection logic as a pure Python function.

Correctness Properties (from design.md):
  1. Step-gap violations are always detected (PBT)
  2. Valid single-step progression produces no violation (PBT)
  3. Question-pending advancement is always detected (PBT)
  Unit tests:
  - Hook JSON has valid schema (name, version, when, then)
  - Hook when.type is "agentStop"
  - Hook is registered in hook-categories.yaml under critical
  - Hook prompt contains key detection phrases
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Helpers — locate source-of-truth files
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

HOOK_FILE = _POWER_ROOT / "hooks" / "ask-bootcamper.kiro.hook"
CATEGORIES_FILE = _POWER_ROOT / "hooks" / "hook-categories.yaml"


def _read_hook_json() -> dict:
    """Return the full parsed JSON from the hook file."""
    return json.loads(HOOK_FILE.read_text(encoding="utf-8"))


def _read_hook_prompt() -> str:
    """Return the ``then.prompt`` value from the hook JSON file."""
    return _read_hook_json()["then"]["prompt"]


# ---------------------------------------------------------------------------
# Detection logic — pure Python implementation for property testing
# ---------------------------------------------------------------------------


def parse_parent_step(step: int | str | None) -> int | None:
    """Extract the parent (integer) step number from a step value.

    - Integer steps (5) → 5
    - Dotted sub-steps ("5.3") → 5
    - Lettered sub-steps ("7a") → 7
    """
    if step is None:
        return None

    if isinstance(step, int):
        return step

    s = str(step).strip()
    if not s:
        return None

    # Dotted sub-step: "5.3" → 5
    if "." in s:
        parts = s.split(".", 1)
        try:
            return int(parts[0])
        except ValueError:
            return None

    # Lettered sub-step: "7a" → 7
    match = re.match(r"^(\d+)[a-zA-Z]", s)
    if match:
        return int(match.group(1))

    # Plain integer as string: "5" → 5
    try:
        return int(s)
    except ValueError:
        return None


def detect_step_skip(progress: dict, question_pending_exists: bool) -> str | None:
    """Detect if the agent skipped a numbered step.

    Args:
        progress: Contents of config/bootcamp_progress.json
        question_pending_exists: Whether config/.question_pending file exists

    Returns:
        Violation message string, or None if no violation detected.
    """
    current_module = progress.get("current_module")
    current_step = progress.get("current_step")
    step_history = progress.get("step_history", {})

    if current_module is None or current_step is None:
        return None

    module_key = str(current_module)
    module_history = step_history.get(module_key)

    if module_history is None:
        return None

    last_completed = module_history.get("last_completed_step")
    if last_completed is None:
        return None

    current_parent = parse_parent_step(current_step)
    last_parent = parse_parent_step(last_completed)

    if current_parent is None or last_parent is None:
        return None

    gap = current_parent - last_parent
    if gap > 1:
        skipped = list(range(last_parent + 1, current_parent))
        return f"VIOLATION: Steps {skipped} were skipped in Module {current_module}"

    if question_pending_exists and current_parent > last_parent:
        return (
            f"VIOLATION: current_step advanced to {current_step} "
            f"while a question was still pending"
        )

    return None


# ---------------------------------------------------------------------------
# Unit Tests — Hook JSON Schema Validation
# ---------------------------------------------------------------------------


class TestHookSchema:
    """Unit tests verifying the hook JSON has a valid schema.

    **Validates: Requirements 5.1, 5.2**
    """

    def test_hook_file_is_valid_json_with_required_keys(self):
        """Hook file must be valid JSON with keys: name, version, when, then.

        **Validates: Requirements 5.1**
        """
        data = _read_hook_json()
        required_keys = {"name", "version", "when", "then"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Hook JSON missing required keys: {missing}"

    def test_hook_when_type_is_agent_stop(self):
        """when.type must be 'agentStop'.

        **Validates: Requirements 5.1**
        """
        data = _read_hook_json()
        assert data["when"]["type"] == "agentStop", (
            f"Expected when.type='agentStop', got {data['when']['type']!r}"
        )

    def test_hook_then_type_is_ask_agent(self):
        """then.type must be 'askAgent'.

        **Validates: Requirements 5.2**
        """
        data = _read_hook_json()
        assert data["then"]["type"] == "askAgent", (
            f"Expected then.type='askAgent', got {data['then']['type']!r}"
        )

    def test_hook_has_version_string(self):
        """version must be a non-empty string.

        **Validates: Requirements 5.1**
        """
        data = _read_hook_json()
        assert isinstance(data["version"], str) and len(data["version"]) > 0


class TestHookRegistration:
    """Unit tests verifying the hook is registered in hook-categories.yaml.

    **Validates: Requirements 5.5**
    """

    def test_hook_registered_in_critical_category(self):
        """ask-bootcamper (consolidated hook) must appear in the critical category list.

        **Validates: Requirements 5.5**
        """
        text = CATEGORIES_FILE.read_text(encoding="utf-8")
        # Parse the critical section — entries are indented with "  - "
        in_critical = False
        critical_hooks: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "critical:":
                in_critical = True
                continue
            if in_critical:
                if stripped.startswith("- "):
                    critical_hooks.append(stripped[2:].strip())
                elif stripped and not stripped.startswith("#"):
                    break  # End of critical section
        assert "ask-bootcamper" in critical_hooks, (
            f"Hook not found in critical category. Found: {critical_hooks}"
        )


class TestHookPromptContent:
    """Unit tests verifying the hook prompt contains key detection phrases.

    **Validates: Requirements 5.2, 5.3**
    """

    def test_prompt_references_progress_file(self):
        """Prompt must reference config/bootcamp_progress.json.

        **Validates: Requirements 5.2**
        """
        prompt = _read_hook_prompt()
        assert "config/bootcamp_progress.json" in prompt

    def test_prompt_references_question_pending(self):
        """Prompt must reference config/.question_pending.

        **Validates: Requirements 5.3**
        """
        prompt = _read_hook_prompt()
        assert ".question_pending" in prompt

    def test_prompt_contains_gap_detection_logic(self):
        """Prompt must describe gap > 1 detection.

        **Validates: Requirements 5.3**
        """
        prompt = _read_hook_prompt().lower()
        assert "gap" in prompt or "greater than 1" in prompt

    def test_prompt_contains_violation_output(self):
        """Prompt must contain violation output instructions.

        **Validates: Requirements 5.3**
        """
        prompt = _read_hook_prompt()
        assert "VIOLATION" in prompt or "violation" in prompt.lower()

    def test_prompt_contains_parent_step_parsing(self):
        """Prompt must describe parent step number parsing (dotted, lettered).

        **Validates: Requirements 5.3**
        """
        prompt = _read_hook_prompt()
        assert "sub-step" in prompt.lower() or "dot" in prompt.lower() or "5.3" in prompt


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------


def st_module_number() -> st.SearchStrategy[int]:
    """Generate valid module numbers (1-11)."""
    return st.integers(min_value=1, max_value=11)


def st_integer_step() -> st.SearchStrategy[int]:
    """Generate integer step numbers."""
    return st.integers(min_value=1, max_value=20)


def st_dotted_step() -> st.SearchStrategy[str]:
    """Generate dotted sub-step strings like '5.3'."""
    return st.tuples(
        st.integers(min_value=1, max_value=20),
        st.integers(min_value=1, max_value=9),
    ).map(lambda t: f"{t[0]}.{t[1]}")


def st_lettered_step() -> st.SearchStrategy[str]:
    """Generate lettered sub-step strings like '7a'."""
    return st.tuples(
        st.integers(min_value=1, max_value=20),
        st.sampled_from(list("abcdefgh")),
    ).map(lambda t: f"{t[0]}{t[1]}")


def st_step_value() -> st.SearchStrategy[int | str]:
    """Generate any valid step value (integer, dotted, or lettered)."""
    return st.one_of(st_integer_step(), st_dotted_step(), st_lettered_step())


# ---------------------------------------------------------------------------
# Property 1: Step-gap violations are always detected
# Validates: Requirements 1.1, 1.2, 5.3
# ---------------------------------------------------------------------------


class TestPropertyStepGapViolation:
    """Property 1 — Step-gap violations are always detected.

    For any valid progress state where current_step has a parent step number
    that exceeds step_history[current_module].last_completed_step by more than 1,
    the detection logic SHALL produce a violation message listing the skipped
    step numbers.

    **Validates: Requirements 1.1, 1.2, 5.3**
    """

    @given(
        module=st_module_number(),
        last_completed=st_integer_step(),
        gap=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_integer_step_gap_detected(self, module: int, last_completed: int, gap: int):
        """A gap > 1 between integer steps always produces a violation.

        **Validates: Requirements 1.1, 1.2, 5.3**
        """
        current_step = last_completed + gap
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": last_completed}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is not None, f"Expected violation for gap={gap}"
        assert "VIOLATION" in result
        # Verify skipped steps are listed
        for skipped in range(last_completed + 1, current_step):
            assert str(skipped) in result

    @given(
        module=st_module_number(),
        last_completed=st.integers(min_value=1, max_value=15),
        gap=st.integers(min_value=2, max_value=8),
        sub_step=st.integers(min_value=1, max_value=9),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dotted_step_gap_detected(
        self, module: int, last_completed: int, gap: int, sub_step: int
    ):
        """A gap > 1 with dotted sub-step current_step always produces a violation.

        **Validates: Requirements 1.1, 1.2, 5.3**
        """
        current_parent = last_completed + gap
        current_step = f"{current_parent}.{sub_step}"
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": last_completed}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is not None, f"Expected violation for gap={gap} (dotted step)"
        assert "VIOLATION" in result

    @given(
        module=st_module_number(),
        last_completed=st.integers(min_value=1, max_value=15),
        gap=st.integers(min_value=2, max_value=8),
        letter=st.sampled_from(list("abcdefgh")),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_lettered_step_gap_detected(
        self, module: int, last_completed: int, gap: int, letter: str
    ):
        """A gap > 1 with lettered sub-step current_step always produces a violation.

        **Validates: Requirements 1.1, 1.2, 5.3**
        """
        current_parent = last_completed + gap
        current_step = f"{current_parent}{letter}"
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": last_completed}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is not None, f"Expected violation for gap={gap} (lettered step)"
        assert "VIOLATION" in result


# ---------------------------------------------------------------------------
# Property 2: Valid single-step progression produces no violation
# Validates: Requirements 5.4
# ---------------------------------------------------------------------------


class TestPropertyValidProgression:
    """Property 2 — Valid single-step progression produces no violation.

    For any valid progress state where current_step has a parent step number
    that exceeds step_history[current_module].last_completed_step by exactly 1
    (or 0 for sub-step advancement), and no .question_pending file exists,
    the detection logic SHALL produce no output.

    **Validates: Requirements 5.4**
    """

    @given(
        module=st_module_number(),
        last_completed=st.integers(min_value=1, max_value=19),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_single_step_advance_no_violation(self, module: int, last_completed: int):
        """Advancing by exactly 1 integer step produces no violation.

        **Validates: Requirements 5.4**
        """
        current_step = last_completed + 1
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": last_completed}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is None, f"Unexpected violation: {result}"

    @given(
        module=st_module_number(),
        step=st.integers(min_value=1, max_value=20),
        sub_step=st.integers(min_value=1, max_value=9),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_sub_step_same_parent_no_violation(self, module: int, step: int, sub_step: int):
        """Advancing within the same parent step (sub-step) produces no violation.

        **Validates: Requirements 5.4**
        """
        current_step = f"{step}.{sub_step}"
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": step}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is None, f"Unexpected violation for sub-step: {result}"

    @given(
        module=st_module_number(),
        step=st.integers(min_value=1, max_value=20),
        letter=st.sampled_from(list("abcdefgh")),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_lettered_same_parent_no_violation(self, module: int, step: int, letter: str):
        """Advancing within the same parent step (lettered) produces no violation.

        **Validates: Requirements 5.4**
        """
        current_step = f"{step}{letter}"
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": step}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is None, f"Unexpected violation for lettered step: {result}"

    @given(module=st_module_number())
    @settings(max_examples=20)
    def test_no_step_history_no_violation(self, module: int):
        """No step_history entry for the module produces no violation.

        **Validates: Requirements 5.4**
        """
        progress = {
            "current_module": module,
            "current_step": 3,
            "step_history": {},
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is None

    @given(module=st_module_number())
    @settings(max_examples=20)
    def test_null_current_step_no_violation(self, module: int):
        """Null current_step produces no violation.

        **Validates: Requirements 5.4**
        """
        progress = {
            "current_module": module,
            "current_step": None,
            "step_history": {str(module): {"last_completed_step": 2}},
        }
        result = detect_step_skip(progress, question_pending_exists=False)
        assert result is None


# ---------------------------------------------------------------------------
# Property 3: Question-pending advancement is always detected
# Validates: Requirements 1.3, 3.3
# ---------------------------------------------------------------------------


class TestPropertyQuestionPending:
    """Property 3 — Question-pending advancement is always detected.

    For any valid progress state where config/.question_pending exists AND
    current_step has advanced beyond step_history[current_module].last_completed_step,
    the detection logic SHALL produce a violation message indicating the step
    advanced while a question was pending.

    **Validates: Requirements 1.3, 3.3**
    """

    @given(
        module=st_module_number(),
        last_completed=st.integers(min_value=1, max_value=19),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_question_pending_with_advance_detected(
        self, module: int, last_completed: int
    ):
        """Advancing by 1 step while question_pending exists produces a violation.

        **Validates: Requirements 1.3, 3.3**
        """
        current_step = last_completed + 1
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": last_completed}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=True)
        assert result is not None, "Expected violation for question-pending advancement"
        assert "VIOLATION" in result
        assert "pending" in result.lower()

    @given(
        module=st_module_number(),
        step=st.integers(min_value=1, max_value=20),
        sub_step=st.integers(min_value=1, max_value=9),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_question_pending_same_parent_no_violation(
        self, module: int, step: int, sub_step: int
    ):
        """Question pending but no parent step advancement produces no violation.

        **Validates: Requirements 1.3, 3.3**
        """
        current_step = f"{step}.{sub_step}"
        progress = {
            "current_module": module,
            "current_step": current_step,
            "step_history": {
                str(module): {"last_completed_step": step}
            },
        }
        result = detect_step_skip(progress, question_pending_exists=True)
        assert result is None, (
            f"Unexpected violation when parent step hasn't advanced: {result}"
        )


# ---------------------------------------------------------------------------
# Unit Tests — parse_parent_step
# ---------------------------------------------------------------------------


class TestParseParentStep:
    """Unit tests for the parse_parent_step helper function."""

    def test_integer_input(self):
        assert parse_parent_step(5) == 5

    def test_integer_string(self):
        assert parse_parent_step("5") == 5

    def test_dotted_sub_step(self):
        assert parse_parent_step("5.3") == 5

    def test_lettered_sub_step(self):
        assert parse_parent_step("7a") == 7

    def test_lettered_uppercase(self):
        assert parse_parent_step("7A") == 7

    def test_none_input(self):
        assert parse_parent_step(None) is None

    def test_empty_string(self):
        assert parse_parent_step("") is None

    def test_multi_digit_dotted(self):
        assert parse_parent_step("12.1") == 12

    def test_multi_digit_lettered(self):
        assert parse_parent_step("10b") == 10
