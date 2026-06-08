"""Preservation property tests for the module3-visualization-no-skip bugfix.

Property 2: Preservation — All Non-Buggy Inputs Unchanged.

These tests follow the observation-first methodology: they observe the behavior
of the UNFIXED code, snapshot it (via SHA-256 for unrelated regions and via
hard-coded structural baselines for the three edited hooks), and assert that
behavior is preserved. They are authored to PASS on the current unfixed code —
this confirms the baseline behavior the fix must not regress — and are designed
to remain valid after the fix touches ONLY the in-scope surfaces.

The preservation goal from the design:

    FOR ALL X WHERE NOT isBugCondition(X) DO
      ASSERT F(X) = F'(X)
    END FOR

Where F is the original gate-enforcement logic (a skipped_steps["3.9"] entry
satisfies the Module 3 visualization gate) and F' is the fixed logic (only the
real Step 9 checkpoints satisfy the gate). For all non-buggy inputs the two
behave identically.

In-scope surfaces the fix WILL touch (NOT snapshotted byte-for-byte here):
    hooks/gate-module3-visualization.kiro.hook
    hooks/enforce-mandatory-gate.kiro.hook
    hooks/enforce-gate-on-stop.kiro.hook
    steering/hook-registry-modules.md
    scripts/validate_mandatory_gates.py
    scripts/install_hooks.py
    config/module-dependencies.yaml
    steering/skip-step-protocol.md
    the existing test files

Feature: module3-visualization-no-skip

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Import the script under test via the sys.path manipulation pattern
# (scripts/ is not a package — see python-conventions.md).
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_BOOTCAMP_DIR / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_mandatory_gates as vmg  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_CONFIG_DIR = _BOOTCAMP_DIR / "config"

_GATE_HOOK = _HOOKS_DIR / "gate-module3-visualization.kiro.hook"
_ENFORCE_GATE_HOOK = _HOOKS_DIR / "enforce-mandatory-gate.kiro.hook"
_ENFORCE_STOP_HOOK = _HOOKS_DIR / "enforce-gate-on-stop.kiro.hook"
_SKIP_PROTOCOL = _STEERING_DIR / "skip-step-protocol.md"

# The three hooks the fix edits (prompt + some descriptions change; structural
# fields below must NOT change).
_EDITED_HOOKS = (_GATE_HOOK, _ENFORCE_GATE_HOOK, _ENFORCE_STOP_HOOK)

# ---------------------------------------------------------------------------
# Domain model — mirrors isBugCondition from bugfix.md / design.md
# ---------------------------------------------------------------------------

# The Module 3 Step 9 visualization gate skip key (`{module}.{step}` form).
VISUALIZATION_GATE_KEY = "3.9"

_GATE_CROSSING_OPERATIONS = ("complete", "advance", "stop", "validate")


@dataclass
class GateState:
    """A Module 3 Step 9 visualization-gate input.

    Attributes:
        checkpoints_passed: Whether BOTH Step 9 checkpoints
            (web_service, web_page) are "passed" (CONDITION A).
        skip_present: Whether a skipped_steps["3.9"] entry is present
            (CONDITION B).
        operation: The triggering operation crossing the gate — one of
            "complete", "advance", "stop", "validate".
    """

    checkpoints_passed: bool
    skip_present: bool
    operation: str


def is_bug_condition(x: GateState) -> bool:
    """Return whether ``x`` triggers the visualization-gate bug.

    Mirrors the ``isBugCondition`` pseudocode in ``bugfix.md``: the gate is
    crossed, the Step 9 checkpoints are NOT both passed, and a
    ``skipped_steps["3.9"]`` entry is present.

    Args:
        x: The gate state to evaluate.

    Returns:
        True when the bug condition holds, False otherwise.
    """
    gate_crossed = x.operation in _GATE_CROSSING_OPERATIONS
    return gate_crossed and (not x.checkpoints_passed) and x.skip_present


# ---------------------------------------------------------------------------
# Reference models of the gate-satisfaction logic for the "3.9" gate.
#
# F  (baseline / original): the gate is satisfied by CONDITION A OR CONDITION B
#    — a skipped_steps["3.9"] entry satisfies the visualization gate.
# F' (fixed): the gate is satisfied ONLY by CONDITION A — the skip is ignored
#    for the "3.9" visualization gate.
#
# For all non-buggy inputs these two must produce the same result; only the
# bug-condition inputs differ (that difference IS the fix).
# ---------------------------------------------------------------------------


def baseline_gate_result(x: GateState) -> str:
    """Original logic F for the Module 3 Step 9 visualization gate.

    Args:
        x: The gate state.

    Returns:
        "allow" if the gate is treated as satisfied, otherwise "block".
    """
    satisfied = x.checkpoints_passed or x.skip_present
    return "allow" if satisfied else "block"


def fixed_gate_result(x: GateState) -> str:
    """Fixed logic F' for the Module 3 Step 9 visualization gate.

    The skip is ignored for this gate; only CONDITION A satisfies it.

    Args:
        x: The gate state.

    Returns:
        "allow" if the gate is satisfied, otherwise "block".
    """
    satisfied = x.checkpoints_passed
    return "allow" if satisfied else "block"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_gate_state(draw: st.DrawFn) -> GateState:
    """Generate a GateState across the visualization-gate input space.

    Returns:
        A GateState with boolean checkpoints_passed / skip_present and an
        operation drawn from the four gate-crossing operations.
    """
    return GateState(
        checkpoints_passed=draw(st.booleans()),
        skip_present=draw(st.booleans()),
        operation=draw(st.sampled_from(_GATE_CROSSING_OPERATIONS)),
    )


@st.composite
def st_condition_a_progress(draw: st.DrawFn) -> dict:
    """Generate a progress state where Step 9 checkpoints are both passed.

    Represents CONDITION A — the legitimate satisfaction path that must be
    preserved (requirement 3.1).

    Returns:
        A bootcamp_progress.json-shaped dict past the gate with both
        checkpoints "passed".
    """
    current_step = draw(st.integers(min_value=10, max_value=12))
    extra = draw(st.booleans())
    skip_present = draw(st.booleans())

    checks: dict = {
        "web_service": {"status": "passed"},
        "web_page": {"status": "passed"},
    }
    if extra:
        checks["mcp_connectivity"] = {"status": "passed"}
        checks["data_loading"] = {"status": "passed"}

    progress: dict = {
        "current_module": 3,
        "modules_completed": [1, 2],
        "current_step": current_step,
        "module_3_verification": {"checks": checks},
    }
    # CONDITION A must satisfy the gate regardless of any skip entry.
    if skip_present:
        progress["skipped_steps"] = {VISUALIZATION_GATE_KEY: {"reason": "a"}}
    return progress


@st.composite
def st_other_gate(draw: st.DrawFn) -> tuple[vmg.MandatoryGate, dict]:
    """Generate a NON-"3.9" mandatory gate plus a matching-skip progress state.

    The skip entry must continue to satisfy any mandatory gate OTHER than the
    Module 3 Step 9 visualization gate (requirement 3.3) — both before and
    after the fix.

    Returns:
        A (gate, progress) tuple where progress has advanced past the gate,
        has no checkpoints, and carries a matching skipped_steps entry.
    """
    module = draw(st.integers(min_value=1, max_value=11))
    step = draw(st.integers(min_value=1, max_value=12))
    # Exclude the one gate the fix special-cases.
    assume(not (module == 3 and step == 9))

    skip_key = f"{module}.{step}"
    gate = vmg.MandatoryGate(
        module=module,
        step=step,
        source_file=f"module-{module:02d}-x.md",
        required_checkpoints=["some_checkpoint"],
    )
    progress = {
        "current_module": module,
        "current_step": step + 1,
        "skipped_steps": {skip_key: {"reason": "a"}},
        f"module_{module}_verification": {"checks": {}},
    }
    return gate, progress


# ---------------------------------------------------------------------------
# Observation phase — SHA-256 baselines of UNFIXED unrelated regions.
#
# These files are NOT in the fix's scope, so their bytes must be byte-stable
# across the fix. The hashes are observed on the current unfixed tree.
# Paths are relative to the bootcamp root.
#
# NOTE (task 7.4b re-baseline): the `scripts/status.py` digest was recomputed
# from the current shipped bytes. An earlier same-branch commit
# (2c0b893 "#1 governanc-hook-and-mcp-coverage") reordered/grouped its import
# statements (a cosmetic, non-functional change — the same symbols are still
# imported: load_modules, load_preferences, load_progress, load_tracks,
# render_text, plus the team_config_validator imports). The previous baseline
# was a stale snapshot of the pre-refactor bytes; the file is still outside this
# fix's scope and byte-stable going forward. An independent content assertion
# (test_status_py_imports_intact) pairs the regenerated digest with the actual
# imported symbols so the digest can never silently lock in a regression.
#
# NOTE (ruff-lint-gate-fix Phase D re-baseline): the `scripts/status.py` digest
# was recomputed again after the ruff E501 remediation reflowed long lines to
# <=100 chars. The reflow is layout-only (wrapped expressions in parens, implicit
# f-string concatenation, and backslash line-continuations inside the embedded
# CSS triple-quoted string — all of which Python collapses to byte-identical
# values). Verified byte-identical: _render_head() and the full rendered
# dashboard HTML (populated and empty/no-progress paths) match the pre-reflow
# output exactly. The file remains outside this fix's scope; only its source
# layout changed, not its emitted output. test_status_py_imports_intact still
# guards against any import regression.
# ---------------------------------------------------------------------------

_UNRELATED_FILE_BASELINES: dict[str, str] = {
    "hooks/ask-bootcamper.kiro.hook":
        "2be48f67f5ab5d19f2368248e9569ec1bb8b0ccd6f39c4124b4e24da7c0fb47e",
    "hooks/git-commit-reminder.kiro.hook":
        "8f37fb88040bd0b382fbfabf9b339c3954fcf7ec3b3bfbd750aacc79b4a365e4",
    "scripts/progress_utils.py":
        "7b3355d9165ec39a8f49c65bb9a1e5f27610f8f3ad727b93e6272587ee6dc29f",
    "scripts/status.py":
        "81ee75888a5ce845945bd4214875f583c5365bbe1f17ce5d4d0aa829691fad79",
    "steering/module-01-business-problem.md":
        "1f10c561826b8b397fc257be3cfc2dea0ed7aa4560f6663d9eea45838f29431f",
    "steering/lang-python.md":
        "15114d9eb719de92aa060649aa8e1bddb8ad01cb6b04a3ff73ca22abb8433a76",
    "config/module-artifacts.yaml":
        "5d197db607b795e85f6a86b1fc370733c29c359276b4bd2139f49e6bd3dc691c",
}


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's bytes.

    Args:
        path: The file to hash.

    Returns:
        The lowercase hex digest string.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Observation phase — structural-field baselines of the three EDITED hooks.
#
# The fix edits these hooks' `prompt` and (for two of them) `description`, but
# must NOT change `name`, `version`, the `when` trigger, or `then.type`. These
# baselines are observed on the unfixed code and asserted to be preserved.
# ---------------------------------------------------------------------------

_HOOK_STRUCTURAL_BASELINES: dict[str, dict] = {
    "gate-module3-visualization.kiro.hook": {
        "name": "to gate Module 3 completion on visualization step",
        "version": "1.0.0",
        "when": {"type": "preToolUse", "toolTypes": ["write"]},
        "then_type": "askAgent",
    },
    "enforce-mandatory-gate.kiro.hook": {
        "name": "to enforce mandatory gate step execution before advancement",
        "version": "1.0.0",
        "when": {"type": "preToolUse", "toolTypes": ["write"]},
        "then_type": "askAgent",
    },
    "enforce-gate-on-stop.kiro.hook": {
        "name": "to enforce mandatory gate execution on agent stop",
        "version": "1.0.0",
        "when": {"type": "agentStop"},
        "then_type": "askAgent",
    },
}


def _load_hook(path: Path) -> dict:
    """Parse a .kiro.hook JSON file.

    Args:
        path: The hook file path.

    Returns:
        The parsed hook object.
    """
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# PBT — Non-bug-condition equivalence: F(X) = F'(X)
# ---------------------------------------------------------------------------


class TestNonBugConditionEquivalence:
    """For every non-buggy GateState, the fixed logic equals the baseline.

    This is the core preservation property: ``F(X) = F'(X)`` whenever
    ``NOT is_bug_condition(X)``. Only the bug-condition inputs (skip present,
    checkpoints absent, gate crossed) diverge between F and F'.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
    """

    @given(x=st_gate_state())
    @settings(max_examples=20)
    def test_fixed_equals_baseline_for_non_bug_inputs(self, x: GateState) -> None:
        """F'(X) == F(X) for every X that is not a bug condition.

        Args:
            x: A generated gate state.
        """
        assume(not is_bug_condition(x))
        assert fixed_gate_result(x) == baseline_gate_result(x), (
            f"Fixed logic diverged from baseline for non-bug input {x!r}: "
            f"baseline={baseline_gate_result(x)} fixed={fixed_gate_result(x)}"
        )

    @given(x=st_gate_state())
    @settings(max_examples=20)
    def test_only_bug_condition_inputs_diverge(self, x: GateState) -> None:
        """F and F' differ if and only if ``is_bug_condition(x)`` holds.

        This documents that the fix's behavioral change is confined exactly to
        the bug-condition input set — everything else is preserved.

        Args:
            x: A generated gate state.
        """
        diverges = baseline_gate_result(x) != fixed_gate_result(x)
        assert diverges == is_bug_condition(x), (
            f"Divergence ({diverges}) did not match is_bug_condition "
            f"({is_bug_condition(x)}) for {x!r}"
        )


# ---------------------------------------------------------------------------
# CONDITION A preservation (3.1)
# ---------------------------------------------------------------------------


class TestConditionAPreservation:
    """When both Step 9 checkpoints are "passed", the gate is satisfied.

    Exercises the real ``_check_gate`` against the Module 3 Step 9 gate. This
    holds on unfixed AND fixed code — CONDITION A is the legitimate
    satisfaction path that the fix preserves.

    **Validates: Requirements 3.1**
    """

    def _step9_gate(self) -> vmg.MandatoryGate:
        return vmg.MandatoryGate(
            module=3,
            step=9,
            source_file="module-03-system-verification.md",
            required_checkpoints=["web_service", "web_page"],
        )

    @given(progress=st_condition_a_progress())
    @settings(max_examples=20)
    def test_check_gate_passes_when_checkpoints_present(self, progress: dict) -> None:
        """``_check_gate`` returns None when both checkpoints are "passed".

        Args:
            progress: A generated CONDITION A progress state.
        """
        violation = vmg._check_gate(progress, self._step9_gate())
        assert violation is None, (
            "CONDITION A (both Step 9 checkpoints passed) must satisfy the "
            f"visualization gate (no violation). Got: {violation!r}"
        )

    def test_check_gate_passes_for_canonical_condition_a(self) -> None:
        """A canonical CONDITION A state yields no violation."""
        progress = {
            "current_module": 3,
            "current_step": 10,
            "module_3_verification": {
                "checks": {
                    "web_service": {"status": "passed"},
                    "web_page": {"status": "passed"},
                }
            },
        }
        assert vmg._check_gate(progress, self._step9_gate()) is None


# ---------------------------------------------------------------------------
# Other-gate skip preservation (3.3)
# ---------------------------------------------------------------------------


class TestOtherGateSkipPreservation:
    """A skipped_steps entry still satisfies any NON-"3.9" mandatory gate.

    The fix special-cases only the "3.9" visualization gate; every other
    mandatory gate must continue to honor its skip entry (``_check_gate``
    returns None). True on unfixed AND fixed code.

    **Validates: Requirements 3.3**
    """

    @given(gate_and_progress=st_other_gate())
    @settings(max_examples=20)
    def test_check_gate_honors_skip_for_other_gates(
        self, gate_and_progress: tuple[vmg.MandatoryGate, dict]
    ) -> None:
        """``_check_gate`` returns None for a non-"3.9" gate with a skip entry.

        Args:
            gate_and_progress: A generated (gate, progress) pair where the gate
                is not the "3.9" visualization gate and a matching skip exists.
        """
        gate, progress = gate_and_progress
        skip_key = f"{gate.module}.{gate.step}"
        assert skip_key != VISUALIZATION_GATE_KEY
        violation = vmg._check_gate(progress, gate)
        assert violation is None, (
            f"Skip entry for non-visualization gate '{skip_key}' must satisfy "
            f"the gate (no violation). Got: {violation!r}"
        )

    def test_check_gate_honors_skip_for_synthetic_gate_3_3(self) -> None:
        """A synthetic "3.3" gate with a matching skip yields no violation."""
        gate = vmg.MandatoryGate(
            module=3,
            step=3,
            source_file="module-03-system-verification.md",
            required_checkpoints=["some_checkpoint"],
        )
        progress = {
            "current_module": 3,
            "current_step": 4,
            "skipped_steps": {"3.3": {"reason": "a"}},
            "module_3_verification": {"checks": {}},
        }
        assert vmg._check_gate(progress, gate) is None


# ---------------------------------------------------------------------------
# Non-mandatory skip preservation (3.2)
# ---------------------------------------------------------------------------


class TestNonMandatorySkipPreservation:
    """The skip-step protocol for non-⛔ steps is intact and honored.

    The fix only ADDS a Step-9 clause to skip-step-protocol.md, so its existing
    structure (trigger phrases, the four-step process, the recording schema,
    and the mandatory-gate constraint) must remain present. Skips other than
    "3.9" continue to allow advancement.

    **Validates: Requirements 3.2**
    """

    def _protocol_text(self) -> str:
        return _SKIP_PROTOCOL.read_text(encoding="utf-8")

    def test_protocol_recording_structure_present(self) -> None:
        """The skipped_steps recording structure and reason field remain."""
        content = self._protocol_text()
        assert "skipped_steps" in content, (
            "Skip protocol must define the skipped_steps recording structure"
        )
        assert "reason" in content, (
            "Skip protocol must define the reason field for skip entries"
        )

    def test_protocol_sections_present(self) -> None:
        """The trigger phrases and four-step process headings remain."""
        content = self._protocol_text()
        assert "## Trigger Phrases" in content
        assert "### 1. Acknowledge" in content
        assert "### 2. Record" in content
        assert "### 3. Assess" in content
        assert "### 4. Proceed" in content
        assert "## Constraints" in content

    def test_protocol_mandatory_gate_constraint_present(self) -> None:
        """The mandatory-gate-cannot-be-skipped constraint remains."""
        content = self._protocol_text()
        assert "Mandatory gates" in content
        assert "cannot be skipped" in content
        assert "⛔" in content

    @given(
        module=st.integers(min_value=1, max_value=11),
        step=st.integers(min_value=1, max_value=12),
    )
    @settings(max_examples=20)
    def test_non_visualization_skips_allow_advancement(
        self, module: int, step: int
    ) -> None:
        """For any non-"3.9" skip key, baseline and fixed both allow advancement.

        Non-mandatory / non-visualization skips are honored identically by F
        and F' — the fix only changes the "3.9" key.

        Args:
            module: A generated module number.
            step: A generated step number.
        """
        skip_key = f"{module}.{step}"
        assume(skip_key != VISUALIZATION_GATE_KEY)

        def skip_allows_advancement_baseline(key: str) -> bool:
            return True  # F: every skip entry is honored

        def skip_allows_advancement_fixed(key: str) -> bool:
            return key != VISUALIZATION_GATE_KEY  # F': only "3.9" is special-cased

        assert (
            skip_allows_advancement_fixed(skip_key)
            == skip_allows_advancement_baseline(skip_key)
        ), f"Non-visualization skip '{skip_key}' must behave identically in F and F'"


# ---------------------------------------------------------------------------
# Non-Module-3 / unrelated no-op preservation (3.4)
# ---------------------------------------------------------------------------


class TestUnrelatedWriteNoOpPreservation:
    """The three hooks short-circuit to "no output" for unrelated writes.

    Each hook's prompt begins with a guard that produces no output when the
    write does not target bootcamp_progress.json / does not mark Module 3
    complete / does not advance current_step past 9. The fix removes only
    CONDITION B; this no-op guard must remain.

    **Validates: Requirements 3.4**
    """

    def test_gate_hook_no_op_guard_present(self) -> None:
        """gate-module3-visualization keeps its non-completion no-op guard."""
        prompt = _load_hook(_GATE_HOOK)["then"]["prompt"]
        assert "produce no output" in prompt, (
            "Gate hook must retain a 'produce no output' short-circuit for "
            "non-Module-3-completion writes"
        )
        assert "config/bootcamp_progress.json" in prompt, (
            "Gate hook must still scope to bootcamp_progress.json writes"
        )

    def test_enforce_gate_hook_no_op_guard_present(self) -> None:
        """enforce-mandatory-gate keeps its non-advancement no-op guard."""
        prompt = _load_hook(_ENFORCE_GATE_HOOK)["then"]["prompt"]
        assert "produce no output" in prompt, (
            "Enforce-mandatory-gate hook must retain a 'produce no output' "
            "short-circuit for non-advancement writes"
        )
        assert "config/bootcamp_progress.json" in prompt, (
            "Enforce-mandatory-gate hook must still scope to "
            "bootcamp_progress.json writes"
        )

    def test_enforce_stop_hook_no_op_guard_present(self) -> None:
        """enforce-gate-on-stop keeps its non-Module-3 no-op guard."""
        prompt = _load_hook(_ENFORCE_STOP_HOOK)["then"]["prompt"]
        assert "produce no output" in prompt, (
            "Enforce-gate-on-stop hook must retain a 'produce no output' "
            "short-circuit when current_module != 3 or current_step < 9"
        )
        assert "current_module" in prompt and "current_step" in prompt, (
            "Enforce-gate-on-stop hook must still gate on current_module / "
            "current_step"
        )


# ---------------------------------------------------------------------------
# Hook schema / name / trigger preservation (3.5)
# ---------------------------------------------------------------------------


class TestHookSchemaPreservation:
    """The three edited hooks keep their schema, names, and triggers.

    The fix changes prompt text (and two descriptions) but must NOT change
    `name`, `version`, the `when` trigger, `then.type`, or the required JSON
    schema keys. Baselines were observed on the unfixed code.

    **Validates: Requirements 3.5**
    """

    def test_all_hooks_have_required_schema_keys(self) -> None:
        """Each edited hook retains the required JSON schema keys."""
        for path in _EDITED_HOOKS:
            hook = _load_hook(path)
            for key in ("name", "version", "when", "then"):
                assert key in hook, f"{path.name} missing required key '{key}'"

    def test_hook_structural_fields_match_baseline(self) -> None:
        """name / version / when / then.type match the observed baselines."""
        for filename, baseline in _HOOK_STRUCTURAL_BASELINES.items():
            hook = _load_hook(_HOOKS_DIR / filename)
            assert hook["name"] == baseline["name"], (
                f"{filename}: name changed from baseline"
            )
            assert hook["version"] == baseline["version"], (
                f"{filename}: version changed from baseline"
            )
            assert hook["when"] == baseline["when"], (
                f"{filename}: when trigger changed from baseline"
            )
            assert hook["then"]["type"] == baseline["then_type"], (
                f"{filename}: then.type changed from baseline"
            )

    def test_pretooluse_write_triggers_preserved(self) -> None:
        """gate-module3-visualization & enforce-mandatory-gate stay write hooks."""
        for path in (_GATE_HOOK, _ENFORCE_GATE_HOOK):
            hook = _load_hook(path)
            assert hook["when"]["type"] == "preToolUse", (
                f"{path.name} must stay preToolUse"
            )
            assert hook["when"].get("toolTypes") == ["write"], (
                f"{path.name} must stay toolTypes:['write']"
            )

    def test_agent_stop_trigger_preserved(self) -> None:
        """enforce-gate-on-stop stays an agentStop hook."""
        hook = _load_hook(_ENFORCE_STOP_HOOK)
        assert hook["when"]["type"] == "agentStop"

    def test_hook_names_keep_to_form(self) -> None:
        """Each hook name keeps the conversational 'to ...' form."""
        for path in _EDITED_HOOKS:
            name = _load_hook(path)["name"]
            assert name.startswith("to "), (
                f"{path.name}: name '{name}' must keep the 'to ...' form"
            )


# ---------------------------------------------------------------------------
# Snapshot of unrelated regions (3.7)
# ---------------------------------------------------------------------------


class TestUnrelatedRegionsByteStable:
    """Unrelated hooks/scripts/steering/config bytes are unchanged.

    These files are outside the fix's scope; their SHA-256 digests must equal
    the baselines observed on the unfixed tree. Holds now and must hold after
    the fix (which touches only in-scope files).

    **Validates: Requirements 3.7**
    """

    def test_unrelated_files_match_sha256_baseline(self) -> None:
        """Every snapshotted unrelated file matches its baseline digest."""
        mismatches: list[str] = []
        for rel_path, expected in _UNRELATED_FILE_BASELINES.items():
            path = _BOOTCAMP_DIR / rel_path
            assert path.exists(), f"Snapshot baseline file missing: {rel_path}"
            actual = _sha256(path)
            if actual != expected:
                mismatches.append(f"{rel_path}: expected {expected}, got {actual}")
        assert not mismatches, (
            "Unrelated regions changed (must stay byte-stable):\n"
            + "\n".join(mismatches)
        )

    def test_snapshot_covers_each_surface_type(self) -> None:
        """The snapshot spans hooks, scripts, steering, and config surfaces."""
        prefixes = {rel.split("/", 1)[0] for rel in _UNRELATED_FILE_BASELINES}
        for surface in ("hooks", "scripts", "steering", "config"):
            assert surface in prefixes, (
                f"Snapshot baseline must include an unrelated {surface} file"
            )

    def test_status_py_imports_intact(self) -> None:
        """Independent content assertion for the regenerated status.py digest.

        The `scripts/status.py` SHA-256 baseline was regenerated after a
        same-branch import-reordering refactor. This content assertion pins the
        actual behavior the digest stands in for — every symbol status.py
        imports from its sibling scripts is still imported — so the regenerated
        digest can never silently lock in a functional regression (a true
        removal of an import would still fail here even if someone re-pinned the
        hash). The reordering moved lines only; it did not change what is used.
        """
        status_py = _BOOTCAMP_DIR / "scripts" / "status.py"
        content = status_py.read_text(encoding="utf-8")
        for symbol in (
            "load_modules",
            "load_preferences",
            "load_progress",
            "load_tracks",
            "render_text",
        ):
            assert symbol in content, (
                f"status.py must still import '{symbol}' after the "
                f"import-reordering refactor (relocation, not removal)"
            )
        # The team_config_validator imports also moved unchanged.
        assert "team_config_validator" in content, (
            "status.py must still reference team_config_validator imports"
        )
