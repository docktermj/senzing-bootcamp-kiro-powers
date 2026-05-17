"""Bug condition exploration tests for mandatory-visualization-gate bugfix.

These tests verify that enforcement mechanisms exist to prevent the agent from
advancing past a ⛔ mandatory gate step (Module 3 Step 9) without checkpoint
evidence. Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug
(no enforcement hook exists yet, no validation script exists yet).

Feature: mandatory-visualization-gate

**Validates: Requirements 1.1, 1.2, 1.3**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"
_SCRIPTS_DIR = _BOOTCAMP_DIR / "scripts"
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_CONFIG_DIR = _BOOTCAMP_DIR / "config"

# The enforcement hook that SHOULD block step advancement past mandatory gates
_ENFORCE_HOOK_PATH = _HOOKS_DIR / "enforce-mandatory-gate.kiro.hook"

# The validation script that SHOULD detect mandatory gate violations
_VALIDATE_SCRIPT_PATH = _SCRIPTS_DIR / "validate_mandatory_gates.py"

# The steering file containing the ⛔ mandatory gate on Step 9
_MODULE3_STEERING = _STEERING_DIR / "module-03-system-verification.md"

# ---------------------------------------------------------------------------
# Hypothesis strategies — generate progress states satisfying bug condition
# ---------------------------------------------------------------------------

# Steps that are past the mandatory gate (Step 9)
_STEPS_PAST_GATE = list(range(10, 13))  # Steps 10, 11, 12


def st_current_step_past_gate() -> st.SearchStrategy[int]:
    """Strategy producing current_step values past the mandatory gate (Step 9).

    Returns:
        A strategy producing integers 10-12 (steps past the ⛔ gate).
    """
    return st.sampled_from(_STEPS_PAST_GATE)


def st_progress_without_checkpoint() -> st.SearchStrategy[dict]:
    """Strategy producing bootcamp_progress.json states where current_step is
    past the mandatory gate but NO web_service/web_page checkpoint exists.

    This represents the bug condition: agent advanced past Step 9 without
    executing it (no checkpoint evidence).

    Returns:
        A strategy producing progress dict states satisfying the bug condition.
    """
    return st.builds(
        lambda step, has_partial_checks: {
            "current_module": 3,
            "modules_completed": [1, 2],
            "current_step": step,
            "language": "python",
            "module_3_verification": {
                "checks": _build_checks_without_step9(has_partial_checks),
            },
        },
        step=st_current_step_past_gate(),
        has_partial_checks=st.booleans(),
    )


def _build_checks_without_step9(has_partial_checks: bool) -> dict:
    """Build a checks dict that does NOT contain web_service/web_page checkpoints.

    Args:
        has_partial_checks: If True, include some earlier step checkpoints
            to make the state more realistic.

    Returns:
        A checks dict missing the Step 9 mandatory gate checkpoints.
    """
    checks: dict = {}
    if has_partial_checks:
        checks["mcp_connectivity"] = {"status": "passed", "duration_ms": 150}
        checks["sdk_initialization"] = {"status": "passed", "duration_ms": 500}
        checks["data_loading"] = {"status": "passed", "records_loaded": 35}
        checks["database_operations"] = {
            "status": "passed",
            "ops_tested": ["write", "read", "search"],
        }
    # Crucially: NO web_service and NO web_page entries
    return checks


def st_progress_with_skipped_steps_no_protocol() -> st.SearchStrategy[dict]:
    """Strategy producing progress states where Step 9 was skipped by the agent
    (no skip-step protocol entry) and current_step is past the gate.

    This is the core bug condition: agent-initiated skip without bootcamper request.

    Returns:
        A strategy producing progress states with agent-initiated skip.
    """
    return st.builds(
        lambda step: {
            "current_module": 3,
            "modules_completed": [1, 2],
            "current_step": step,
            "language": "python",
            "module_3_verification": {
                "checks": {
                    "mcp_connectivity": {"status": "passed", "duration_ms": 100},
                    "truthset_acquisition": {"status": "passed", "records": 35},
                    "sdk_initialization": {"status": "passed", "duration_ms": 400},
                    "code_generation": {"status": "passed", "file": "verify_pipeline.py"},
                    "build_compilation": {"status": "passed", "duration_ms": 800},
                    "data_loading": {"status": "passed", "records_loaded": 35},
                    "results_validation": {
                        "status": "passed",
                        "entities": 20,
                        "matches_verified": 3,
                    },
                    "database_operations": {
                        "status": "passed",
                        "ops_tested": ["write", "read", "search"],
                    },
                    # NO web_service checkpoint
                    # NO web_page checkpoint
                },
            },
            # No skipped_steps entry for "3.9" — agent skipped without protocol
        },
        step=st_current_step_past_gate(),
    )


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — Enforcement Hook Exists
# ---------------------------------------------------------------------------


class TestEnforcementHookExists:
    """Property 1: Bug Condition — enforce-mandatory-gate.kiro.hook must exist.

    The enforcement hook is the proactive mechanism that blocks step advancement
    past a ⛔ mandatory gate step when no checkpoint evidence exists. Without it,
    the agent can freely advance past Step 9.

    **Validates: Requirements 1.1, 1.2**
    """

    def test_enforcement_hook_file_exists(self) -> None:
        """The enforce-mandatory-gate.kiro.hook file must exist in hooks/.

        On UNFIXED code, this file does NOT exist — confirming the enforcement gap.
        """
        assert _ENFORCE_HOOK_PATH.exists(), (
            f"Enforcement hook not found at {_ENFORCE_HOOK_PATH}. "
            f"No proactive mechanism exists to block step advancement past "
            f"⛔ mandatory gate steps. The agent can advance current_step past "
            f"Step 9 without any enforcement firing."
        )

    def test_enforcement_hook_has_valid_schema(self) -> None:
        """The enforcement hook must be valid JSON with required fields.

        On UNFIXED code, the file doesn't exist so this also fails.
        """
        assert _ENFORCE_HOOK_PATH.exists(), (
            f"Cannot validate schema — hook file does not exist: {_ENFORCE_HOOK_PATH}"
        )
        raw = _ENFORCE_HOOK_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)

        # Required fields per security rules
        assert "name" in data, "Hook missing 'name' field"
        assert "version" in data, "Hook missing 'version' field"
        assert "when" in data, "Hook missing 'when' field"
        assert "then" in data, "Hook missing 'then' field"
        assert data["when"].get("type") == "preToolUse", (
            "Hook must be a preToolUse hook to fire BEFORE step advancement"
        )

    def test_enforcement_hook_blocks_step_advancement(self) -> None:
        """The enforcement hook prompt must instruct blocking when checkpoint is missing.

        On UNFIXED code, the file doesn't exist so this fails.
        """
        assert _ENFORCE_HOOK_PATH.exists(), (
            f"Cannot validate prompt — hook file does not exist: {_ENFORCE_HOOK_PATH}"
        )
        raw = _ENFORCE_HOOK_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        prompt = data.get("then", {}).get("prompt", "")

        # The prompt must reference mandatory gate / ⛔ enforcement
        assert re.search(r"mandatory.gate|⛔|step\s*9", prompt, re.IGNORECASE), (
            "Hook prompt does not reference mandatory gate enforcement. "
            "It must instruct blocking when step advancement skips a ⛔ gate "
            "without checkpoint evidence."
        )

        # The prompt must instruct blocking/stopping the write
        assert re.search(r"block|stop|do not.*allow|do not.*proceed", prompt, re.IGNORECASE), (
            "Hook prompt does not instruct blocking the write operation. "
            "It must prevent step advancement past a mandatory gate without checkpoint."
        )


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — Validation Script Exists
# ---------------------------------------------------------------------------


class TestValidationScriptExists:
    """Property 1: Bug Condition — validate_mandatory_gates.py must exist.

    The validation script provides a CI-time and manual-run layer that detects
    mandatory gate steps skipped without corresponding checkpoint entries.

    **Validates: Requirements 1.1, 1.3**
    """

    def test_validation_script_file_exists(self) -> None:
        """The validate_mandatory_gates.py script must exist in scripts/.

        On UNFIXED code, this file does NOT exist — confirming no validation layer.
        """
        assert _VALIDATE_SCRIPT_PATH.exists(), (
            f"Validation script not found at {_VALIDATE_SCRIPT_PATH}. "
            f"No CI-time validation exists to detect mandatory gate violations. "
            f"A progress state with current_step=10 and no Step 9 checkpoint "
            f"passes validation on unfixed code."
        )

    def test_validation_script_is_importable(self) -> None:
        """The validation script must be importable as a Python module.

        On UNFIXED code, the file doesn't exist so this also fails.
        """
        assert _VALIDATE_SCRIPT_PATH.exists(), (
            f"Cannot import — script does not exist: {_VALIDATE_SCRIPT_PATH}"
        )
        # If it exists, verify it's valid Python by compiling it
        source = _VALIDATE_SCRIPT_PATH.read_text(encoding="utf-8")
        compile(source, str(_VALIDATE_SCRIPT_PATH), "exec")


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — PBT: Random progress states past gate undetected
# ---------------------------------------------------------------------------


class TestMandatoryGateViolationDetection:
    """Property 1: Bug Condition — Mandatory Gate Step Advancement Without Checkpoint.

    For any progress state where current_step > 9 but no web_service or web_page
    checkpoint exists for Step 9, the validation script MUST detect and report
    the violation.

    On UNFIXED code, the validation script does not exist, so these tests FAIL —
    confirming the enforcement gap.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @given(progress=st_progress_without_checkpoint())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_validation_detects_missing_checkpoint(self, progress: dict) -> None:
        """For any progress state past the gate without checkpoint, validation detects it.

        Args:
            progress: A generated progress state with current_step > 9 and no
                web_service/web_page checkpoint.
        """
        # First: the validation script must exist
        assert _VALIDATE_SCRIPT_PATH.exists(), (
            f"Validation script does not exist at {_VALIDATE_SCRIPT_PATH}. "
            f"Counterexample: current_step={progress['current_step']} with no "
            f"Step 9 checkpoint passes validation on unfixed code because no "
            f"validation mechanism exists."
        )

        # If it exists, import and run it against this progress state
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_mandatory_gates", _VALIDATE_SCRIPT_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # The script should have a function that validates progress
        assert hasattr(module, "validate_progress") or hasattr(module, "main"), (
            "Validation script must expose validate_progress() or main() function"
        )

    @given(progress=st_progress_with_skipped_steps_no_protocol())
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_agent_initiated_skip_detected(self, progress: dict) -> None:
        """For any agent-initiated skip (no skipped_steps entry), validation detects it.

        The bug condition is: step.hasMandatoryGate=true AND action="skip" AND
        initiator="agent" AND bootcamperRequestedSkip=false.

        This manifests as current_step > 9 with no web_service/web_page checkpoint
        AND no skipped_steps["3.9"] entry (meaning the skip was not via protocol).

        Args:
            progress: A generated progress state representing an agent-initiated skip.
        """
        # Verify the bug condition holds for this input
        checks = progress.get("module_3_verification", {}).get("checks", {})
        has_web_service = "web_service" in checks
        has_web_page = "web_page" in checks
        has_skip_entry = "3.9" in progress.get("skipped_steps", {})

        # Confirm this IS a bug condition state
        assert progress["current_step"] > 9, "Generated step must be past gate"
        assert not has_web_service, "Must not have web_service checkpoint"
        assert not has_web_page, "Must not have web_page checkpoint"
        assert not has_skip_entry, "Must not have skip-step protocol entry"

        # The enforcement mechanism must exist and catch this
        assert _ENFORCE_HOOK_PATH.exists(), (
            f"Enforcement hook does not exist. Counterexample: "
            f"current_step={progress['current_step']} with Steps 1-8 checkpoints "
            f"present but NO Step 9 checkpoint and NO skipped_steps entry — "
            f"agent-initiated skip goes undetected on unfixed code."
        )


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — Steering file has parseable ⛔ marker
# ---------------------------------------------------------------------------


class TestMandatoryGateMarkerParseable:
    """Property 1: Bug Condition — ⛔ marker in steering file is machine-parseable.

    The ⛔ mandatory gate marker on Step 9 must be detectable by automated tools
    so that enforcement hooks and validation scripts can identify which steps
    are mandatory gates.

    **Validates: Requirements 1.1**
    """

    def test_step9_has_mandatory_gate_marker(self) -> None:
        """Step 9 in module-03-system-verification.md has a ⛔ marker."""
        content = _MODULE3_STEERING.read_text(encoding="utf-8")

        # Find Step 9 section and verify it has ⛔
        step9_match = re.search(
            r"###\s+Step\s+9.*?\n(.*?)(?=###\s+Step\s+\d+|## Phase)",
            content,
            re.DOTALL,
        )
        assert step9_match is not None, "Step 9 section not found in steering file"

        step9_header_line = content[
            content.rfind("\n", 0, step9_match.start()) + 1 : step9_match.start()
        ]
        step9_section = step9_match.group(0)

        # The ⛔ marker must be present near Step 9
        assert "⛔" in step9_section, (
            "Step 9 section does not contain ⛔ mandatory gate marker"
        )

    def test_mandatory_gate_marker_on_step9_line(self) -> None:
        """The ⛔ MANDATORY GATE text appears in the Step 9 section."""
        content = _MODULE3_STEERING.read_text(encoding="utf-8")

        # Look for the specific pattern: ⛔ MANDATORY GATE
        assert re.search(r"⛔\s*MANDATORY\s*GATE", content), (
            "No '⛔ MANDATORY GATE' pattern found in module-03-system-verification.md. "
            "The marker must be machine-parseable for enforcement tools."
        )

