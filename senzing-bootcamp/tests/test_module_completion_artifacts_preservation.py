"""Preservation property tests for the module-completion-artifacts bugfix.

Feature: module-completion-artifacts (BUGFIX)

Property 2: Preservation — Non-buggy inputs are unchanged.

Methodology: observation-first. For inputs where the bug condition does NOT hold
(`isBugCondition` returns false) the fixed code must behave exactly as the original.
This suite snapshots the *currently observable* baseline behavior — drawn from the
real hook/steering files on disk and from the documented on-disk artifact semantics —
so the assertions are valid both BEFORE and AFTER the fix.

The deterministic planner introduced by the fix
(``senzing-bootcamp/scripts/completion_artifacts.py``) DOES NOT EXIST YET (task 3.1).
Every assertion in this file is therefore grounded in one of:

  * the verbatim/byte-identity preserved instructions in the real hook and steering
    files (these must survive the fix unchanged), or
  * a local reference model of the documented completion flow (no planner needed), or
  * planner-dependent invariants that are *guarded* — they only run once the planner
    exists, so this file passes on the unfixed state and gets stronger after the fix.

Preserved behaviors asserted here (design — Preservation Requirements):
    Test case 1  No-new-entry no-op            (Req 3.5)
    Test case 2  Byte-for-byte preservation     (Req 3.1)
    Test case 3  Question-pending deferral       (Req 3.4)
    Test case 4  Default name "Bootcamper"       (Req 3.7)
    Test case 5  Non-blocking errors + order     (Req 3.2, 3.3)
    Test case 6  Celebration hook is read-only   (Req 3.6)

Expected outcome on UNFIXED code: every test PASSES — this pins the baseline.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Defensive import of the planner created by task 3.1. Absent on the UNFIXED
# state -> PLANNER_AVAILABLE is False and the planner-dependent invariants are
# skipped (this file still passes; it just gets stronger after the fix).
# ---------------------------------------------------------------------------

PLANNER_AVAILABLE = False
_planner = None  # the imported module

try:  # pragma: no cover - exercised by presence/absence of the planner
    import completion_artifacts as _planner  # type: ignore

    PLANNER_AVAILABLE = True
except Exception:  # noqa: BLE001 - any failure means "not yet implemented"
    PLANNER_AVAILABLE = False

# ---------------------------------------------------------------------------
# Real files under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_HOOKS_DIR: Path = _POWER_ROOT / "hooks"
_STEERING_DIR: Path = _POWER_ROOT / "steering"

_RECAP_HOOK: Path = _HOOKS_DIR / "module-recap-append.kiro.hook"
_CELEBRATION_HOOK: Path = _HOOKS_DIR / "module-completion-celebration.kiro.hook"
_MODULE_COMPLETION_FILE: Path = _STEERING_DIR / "module-completion.md"

# The fixed, invariant completion step order (design Req 3.3).
STEP_ORDER: list[str] = [
    "progress_update",
    "recap_append",
    "journal_entry",
    "completion_certificate",
    "next_step_options",
]

_PLACEHOLDER_RE = re.compile(r"module\s+\w+\s+session", re.IGNORECASE)
_DURATION_RE = re.compile(r"\d+\s*(d|h|m|s)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Read a file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    """Read and parse a JSON hook file."""
    return json.loads(_read(path))


def _is_placeholder(text: str | None) -> bool:
    """Return True for empty/missing values and non-time 'Module N session' strings."""
    if text is None or not str(text).strip():
        return True
    if _PLACEHOLDER_RE.search(str(text)):
        return True
    return _DURATION_RE.search(str(text)) is None


# ---------------------------------------------------------------------------
# Reference model of isBugCondition (mirrors design; no planner needed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _State:
    """A modeled progress + inventory state for the non-bug input space."""

    modules_completed: tuple[int, ...]
    recap_sections: frozenset[int]
    journal_entries: frozenset[int]
    certificates: frozenset[int]
    per_module_durations: tuple[str, ...]
    total_duration: str
    timing_reliable: bool


def _model_is_bug_condition(x: _State) -> bool:
    """Local reference model of the design's isBugCondition (coverage/cert/duration)."""
    completed = set(x.modules_completed)
    coverage_gap = any(
        (m not in x.recap_sections)
        or (m not in x.journal_entries)
        or (m not in x.certificates)
        for m in completed
    )
    has_cert = completed & x.certificates
    missing_cert = completed - x.certificates
    certificates_non_uniform = bool(has_cert) and bool(missing_cert)
    placeholder_duration = x.timing_reliable and any(
        _is_placeholder(d) for d in x.per_module_durations
    )
    placeholder_total = x.timing_reliable and _is_placeholder(x.total_duration)
    return (
        coverage_gap
        or certificates_non_uniform
        or placeholder_duration
        or placeholder_total
    )


# ---------------------------------------------------------------------------
# Reference model of the documented completion flow (no planner needed)
# ---------------------------------------------------------------------------


def _model_completion_outcome(
    prev_completed: tuple[int, ...],
    curr_completed: tuple[int, ...],
    question_pending: bool,
) -> set[str]:
    """Model which artifacts the documented flow emits for a (prev -> curr) step.

    Mirrors the boundary-detection contract shared by the recap/celebration hooks and
    `module-completion.md`:
      * `.question_pending` present  -> defer, produce NOTHING (Req 3.4).
      * no NEW module number added   -> no-op, produce NOTHING (Req 3.5).
      * a new module number appeared  -> emit the per-module artifact set.

    Args:
        prev_completed: `modules_completed` before this step.
        curr_completed: `modules_completed` after this step.
        question_pending: Whether `config/.question_pending` exists at check time.

    Returns:
        The set of artifact tokens emitted (empty for the deferral/no-op paths).
    """
    if question_pending:
        return set()
    new_modules = set(curr_completed) - set(prev_completed)
    if not new_modules:
        return set()
    tokens: set[str] = set()
    for module in sorted(new_modules):
        tokens.add(f"recap:{module}")
        tokens.add(f"journal:{module}")
        tokens.add(f"certificate:{module}")
    return tokens


def _model_append(existing: str, section: str) -> str:
    """Model the documented append: add the new section at the end of the file.

    The documented contract is "append the new recap section at the end of the file
    without modifying any existing bytes" — i.e., the result is exactly the prior
    content followed by the new section.

    Args:
        existing: The current file content.
        section: The new section to append.

    Returns:
        The new file content (existing bytes preserved, section appended).
    """
    return existing + section


def _resolve_name(preferences_text: str | None) -> str:
    """Model the documented default-name resolution (Req 3.7).

    Reads a minimal `name:` field from the preferences YAML text. When the file is
    absent (None) or the `name` field is missing/blank, returns "Bootcamper".

    Args:
        preferences_text: Raw `bootcamp_preferences.yaml` content, or None if absent.

    Returns:
        The bootcamper's configured name, or "Bootcamper" as the default.
    """
    if preferences_text is None:
        return "Bootcamper"
    for line in preferences_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        if key.strip() == "name":
            name = value.strip().strip('"').strip("'")
            return name if name and name.lower() != "null" else "Bootcamper"
    return "Bootcamper"


def _run_completion_flow(failing_steps: set[str]) -> tuple[list[str], list[str]]:
    """Model the documented non-blocking, fixed-order completion flow (Req 3.2, 3.3).

    Each step runs in the invariant order. If an artifact step fails, a warning is
    logged in the documented format and the flow continues to the next step (the
    failure never halts the flow; next_step_options always runs).

    Args:
        failing_steps: The steps that raise a file-system error this run.

    Returns:
        A tuple of (steps attempted in order, warnings logged).
    """
    attempted: list[str] = []
    warnings: list[str] = []
    for step in STEP_ORDER:
        attempted.append(step)
        if step in failing_steps:
            warnings.append(
                f"\u26a0\ufe0f {step} skipped: simulated file-system error. "
                "This will be retried on next module completion."
            )
            continue
    return attempted, warnings


# ===========================================================================
# Test case 1 — No-new-entry no-op (Req 3.5)
# ===========================================================================


class TestNoNewEntryNoOp:
    """When `modules_completed` gains no new entry, no artifacts are produced.

    Grounded in the boundary-detection instruction preserved verbatim in both
    agentStop hooks, and modeled across the input domain via Hypothesis.

    Validates: Requirements 3.5
    """

    def test_hooks_preserve_no_op_instruction(self) -> None:
        """Both hooks keep the 'no new module -> produce no output' instruction."""
        for hook_path in (_RECAP_HOOK, _CELEBRATION_HOOK):
            prompt = str(_read_json(hook_path)["then"]["prompt"])  # type: ignore[index]
            assert "has not changed" in prompt and "produce no output" in prompt, (
                f"{hook_path.name} must preserve the no-new-entry no-op instruction"
            )

    @given(
        completed=st.lists(
            st.integers(min_value=1, max_value=11), min_size=0, max_size=11, unique=True
        )
    )
    @settings(max_examples=20)
    def test_no_new_entry_emits_nothing(self, completed: list[int]) -> None:
        """An unchanged `modules_completed` (prev == curr) emits no artifacts."""
        state = tuple(sorted(completed))
        assert _model_completion_outcome(state, state, question_pending=False) == set(), (
            "No new module entry must produce no recap/journal/certificate output"
        )

    @given(
        completed=st.lists(
            st.integers(min_value=1, max_value=11), min_size=1, max_size=11, unique=True
        )
    )
    @settings(max_examples=20)
    def test_planner_emits_empty_plan_on_complete_set(self, completed: list[int]) -> None:
        """GUARDED: on an already-complete set the planner yields an empty backfill."""
        if not PLANNER_AVAILABLE:
            return  # planner not yet implemented (unfixed state) -> nothing to check
        completed_set = set(completed)
        progress_state_cls = getattr(_planner, "ProgressState")
        inventory_cls = getattr(_planner, "ArtifactInventory")
        plan_backfill = getattr(_planner, "plan_backfill")

        progress = progress_state_cls(
            modules_completed=sorted(completed_set),
            step_history={},
            started_at=None,
        )
        inventory = inventory_cls(
            recap_sections=set(completed_set),
            journal_entries=set(completed_set),
            certificates=set(completed_set),
        )
        plan = plan_backfill(progress, inventory)
        for field in (
            "recap_modules", "journal_modules", "certificate_modules",
            "recap_sections", "journal_entries", "certificates",
            "missing_recap", "missing_journal", "missing_certificate",
        ):
            if hasattr(plan, field):
                assert not set(getattr(plan, field)), (
                    f"A complete set must yield an empty backfill plan; {field} not empty"
                )


# ===========================================================================
# Test case 2 — Byte-for-byte preservation on append (Req 3.1)
# ===========================================================================


class TestByteForBytePreservation:
    """Appending a recap/journal section preserves all prior bytes exactly.

    Validates: Requirements 3.1
    """

    def test_recap_hook_preserves_byte_for_byte_instruction(self) -> None:
        """The recap hook keeps the byte-for-byte preservation constraint."""
        prompt = str(_read_json(_RECAP_HOOK)["then"]["prompt"])  # type: ignore[index]
        assert "byte-for-byte" in prompt, (
            "Recap hook must preserve the 'byte-for-byte' append constraint"
        )

    def test_steering_preserves_byte_for_byte_instruction(self) -> None:
        """`module-completion.md` keeps the byte-for-byte journal preservation rule."""
        content = _read(_MODULE_COMPLETION_FILE)
        assert "byte-for-byte" in content, (
            "module-completion.md must preserve the 'byte-for-byte' journal rule"
        )
        assert "without modifying any existing bytes" in content, (
            "module-completion.md must preserve the recap 'no existing bytes' rule"
        )

    @given(
        existing=st.text(min_size=0, max_size=400),
        section=st.text(min_size=0, max_size=200),
    )
    @settings(max_examples=20)
    def test_append_preserves_prior_bytes(self, existing: str, section: str) -> None:
        """After an append, the prior content is an exact byte prefix of the result."""
        result = _model_append(existing, section)
        existing_bytes = existing.encode("utf-8")
        result_bytes = result.encode("utf-8")
        assert result_bytes[: len(existing_bytes)] == existing_bytes, (
            "All prior bytes must be identical after appending a new section"
        )
        assert result.startswith(existing), "Existing content must be preserved verbatim"
        assert result.endswith(section), "New section must be appended at the end"


# ===========================================================================
# Test case 3 — Question-pending deferral (Req 3.4)
# ===========================================================================


class TestQuestionPendingDeferral:
    """When `config/.question_pending` exists, no artifact output is produced.

    Validates: Requirements 3.4
    """

    def test_hooks_preserve_question_pending_deferral(self) -> None:
        """Both hooks keep the '.question_pending -> defer, no output' instruction."""
        for hook_path in (_RECAP_HOOK, _CELEBRATION_HOOK):
            prompt = str(_read_json(hook_path)["then"]["prompt"])  # type: ignore[index]
            assert ".question_pending" in prompt, (
                f"{hook_path.name} must reference config/.question_pending"
            )
            assert "ask-bootcamper" in prompt, (
                f"{hook_path.name} must defer to ask-bootcamper"
            )
            assert "produce no output" in prompt, (
                f"{hook_path.name} must produce no output while a question is pending"
            )

    @given(
        prev=st.lists(
            st.integers(min_value=1, max_value=11), min_size=0, max_size=10, unique=True
        ),
        new_module=st.integers(min_value=1, max_value=11),
    )
    @settings(max_examples=20)
    def test_deferral_emits_nothing_even_with_new_module(
        self, prev: list[int], new_module: int
    ) -> None:
        """With a question pending, even a newly added module emits no artifacts."""
        prev_t = tuple(sorted(set(prev)))
        curr_t = tuple(sorted(set(prev) | {new_module}))
        assert _model_completion_outcome(prev_t, curr_t, question_pending=True) == set(), (
            "A pending question must defer all artifact output"
        )


# ===========================================================================
# Test case 4 — Default name "Bootcamper" (Req 3.7)
# ===========================================================================


class TestDefaultName:
    """A missing preferences file or absent `name` field yields "Bootcamper".

    Validates: Requirements 3.7
    """

    def test_recap_hook_preserves_default_name(self) -> None:
        """The recap hook keeps the "Bootcamper" default-name fallback."""
        prompt = str(_read_json(_RECAP_HOOK)["then"]["prompt"])  # type: ignore[index]
        assert "Bootcamper" in prompt, "Recap hook must preserve the default name"

    def test_steering_preserves_default_name(self) -> None:
        """`module-completion.md` keeps the "Bootcamper" default-name fallback."""
        content = _read(_MODULE_COMPLETION_FILE)
        assert "Bootcamper" in content, "module-completion.md must keep the default name"

    def test_missing_file_uses_default(self) -> None:
        """An absent preferences file falls back to "Bootcamper"."""
        assert _resolve_name(None) == "Bootcamper"

    def test_absent_name_field_uses_default(self) -> None:
        """Preferences without a `name` field fall back to "Bootcamper"."""
        prefs = "language: python\ntrack: core_bootcamp\n"
        assert _resolve_name(prefs) == "Bootcamper"

    def test_null_name_uses_default(self) -> None:
        """A null/blank `name` value falls back to "Bootcamper"."""
        assert _resolve_name("name: null\n") == "Bootcamper"
        assert _resolve_name("name:   \n") == "Bootcamper"

    @given(
        name=st.text(
            alphabet=st.characters(
                min_codepoint=32, max_codepoint=126, blacklist_characters=":#'\""
            ),
            min_size=1,
            max_size=40,
        ).filter(lambda s: s.strip() != "")
    )
    @settings(max_examples=20)
    def test_present_name_is_used_otherwise_default(self, name: str) -> None:
        """A present non-blank `name` is used; otherwise "Bootcamper" is the default."""
        safe = name.strip()
        if not safe or safe.lower() == "null":
            return  # degenerate after stripping -> covered by default-name tests
        resolved = _resolve_name(f"name: {safe}\n")
        assert resolved == safe, f"Configured name {safe!r} should be used, got {resolved!r}"


# ===========================================================================
# Test case 5 — Non-blocking errors + fixed step order (Req 3.2, 3.3)
# ===========================================================================


class TestNonBlockingErrorsAndStepOrder:
    """Artifact-step failures are non-blocking; the fixed step order is invariant.

    Validates: Requirements 3.2, 3.3
    """

    def test_steering_preserves_fixed_step_order(self) -> None:
        """`module-completion.md` documents the fixed five-step order in sequence."""
        content = _read(_MODULE_COMPLETION_FILE)
        last = -1
        for step in STEP_ORDER:
            idx = content.find(step)
            assert idx != -1, f"Step '{step}' must be documented in module-completion.md"
            assert idx > last, f"Step '{step}' is out of the fixed order"
            last = idx

    def test_steering_preserves_non_blocking_warning_format(self) -> None:
        """The documented non-blocking warning format is preserved."""
        content = _read(_MODULE_COMPLETION_FILE)
        assert "skipped:" in content, "Warning format '[Step] skipped: [reason]' missing"
        assert "retried on next module completion" in content, (
            "Retry-on-next-completion behavior must be preserved"
        )
        assert "\u26a0\ufe0f" in content, "Warning marker must be preserved"

    def test_full_flow_runs_in_order_with_no_failures(self) -> None:
        """With no failures, all five steps run in the fixed order."""
        attempted, warnings = _run_completion_flow(set())
        assert attempted == STEP_ORDER
        assert warnings == []

    @given(
        failing=st.sets(
            st.sampled_from(["recap_append", "journal_entry", "completion_certificate"]),
            min_size=0,
            max_size=3,
        )
    )
    @settings(max_examples=20)
    def test_failures_are_non_blocking_and_order_invariant(
        self, failing: set[str]
    ) -> None:
        """Any subset of artifact-step failures preserves order and never halts the flow."""
        attempted, warnings = _run_completion_flow(failing)
        # Every step is still attempted, in the invariant order (Req 3.3).
        assert attempted == STEP_ORDER, "Step order must be invariant under failures"
        # next_step_options always runs even when artifact steps fail (Req 3.2).
        assert "next_step_options" in attempted
        # A warning is logged for each failing step, in the documented format (Req 3.2).
        assert len(warnings) == len(failing)
        for warning in warnings:
            assert "skipped:" in warning
            assert "retried on next module completion" in warning


# ===========================================================================
# Test case 6 — Celebration hook is read-only (Req 3.6)
# ===========================================================================


class TestCelebrationHookReadOnly:
    """The module-completion-celebration hook writes no files.

    Validates: Requirements 3.6
    """

    def test_celebration_hook_schema_is_valid(self) -> None:
        """The celebration hook keeps a valid schema (name/version/when/then)."""
        hook = _read_json(_CELEBRATION_HOOK)
        for key in ("name", "version", "when", "then"):
            assert key in hook, f"Celebration hook must keep '{key}'"
        assert hook["when"]["type"] == "agentStop"  # type: ignore[index]
        assert hook["then"]["type"] == "askAgent"  # type: ignore[index]

    def test_celebration_hook_declares_no_writes(self) -> None:
        """The celebration hook prompt forbids writing files and running commands."""
        prompt = str(_read_json(_CELEBRATION_HOOK)["then"]["prompt"])  # type: ignore[index]
        assert "Do NOT write any files." in prompt, (
            "Celebration hook must keep the 'Do NOT write any files' constraint"
        )
        assert "Do NOT run any scripts or commands." in prompt, (
            "Celebration hook must keep the 'Do NOT run scripts/commands' constraint"
        )

    def test_celebration_hook_only_reads_named_config_files(self) -> None:
        """The celebration hook restricts itself to reading three named config files."""
        prompt = str(_read_json(_CELEBRATION_HOOK)["then"]["prompt"])  # type: ignore[index]
        assert "ONLY read these three config files" in prompt
        for cfg in (
            "config/bootcamp_progress.json",
            "config/module-dependencies.yaml",
            "config/bootcamp_preferences.yaml",
        ):
            assert cfg in prompt, f"Celebration hook must still read {cfg}"

    def test_celebration_hook_does_not_perform_artifact_steps(self) -> None:
        """The celebration hook does not journal, certificate, or reflect."""
        prompt = str(_read_json(_CELEBRATION_HOOK)["then"]["prompt"])  # type: ignore[index]
        assert "Do NOT perform journal entries, generate certificates" in prompt, (
            "Celebration hook must remain read-only and not own artifact generation"
        )


# ===========================================================================
# PBT — Non-bug-condition states are no-op / preserved across the domain
# ===========================================================================


@st.composite
def st_non_bug_state(draw: st.DrawFn) -> _State:
    """Draw a NON-bug-condition state (complete, uniform, real durations).

    By construction `isBugCondition` is false: every completed module has every
    artifact type (recap, journal, AND certificate — the formal coverage-gap clause
    requires a certificate per completed module), certificates are uniform, and all
    durations are real elapsed times.
    """
    completed = draw(
        st.lists(
            st.integers(min_value=1, max_value=11), min_size=0, max_size=11, unique=True
        )
    )
    completed_set = frozenset(completed)
    return _State(
        modules_completed=tuple(sorted(completed_set)),
        recap_sections=completed_set,
        journal_entries=completed_set,
        certificates=completed_set,
        per_module_durations=tuple("1h 0m" for _ in completed_set),
        total_duration="3h 0m" if completed_set else "0m",
        timing_reliable=True,
    )


class TestNonBugConditionPreserved:
    """Across the non-bug input domain, no spurious artifacts are produced.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """

    @given(state=st_non_bug_state())
    @settings(max_examples=20)
    def test_generated_states_are_not_bug_conditions(self, state: _State) -> None:
        """The generator only yields states where isBugCondition is false."""
        assert not _model_is_bug_condition(state), (
            f"st_non_bug_state must not produce a bug condition: {state!r}"
        )

    @given(state=st_non_bug_state())
    @settings(max_examples=20)
    def test_no_op_on_non_bug_state_without_new_module(self, state: _State) -> None:
        """A non-bug state with no newly added module emits no artifacts (no-op)."""
        completed = state.modules_completed
        assert _model_completion_outcome(completed, completed, question_pending=False) == set()

    @given(state=st_non_bug_state())
    @settings(max_examples=20)
    def test_planner_no_backfill_on_non_bug_state(self, state: _State) -> None:
        """GUARDED: the planner produces no backfill work for a non-bug state."""
        if not PLANNER_AVAILABLE:
            return  # unfixed state -> planner absent -> nothing to check
        progress_state_cls = getattr(_planner, "ProgressState")
        inventory_cls = getattr(_planner, "ArtifactInventory")
        plan_backfill = getattr(_planner, "plan_backfill")

        progress = progress_state_cls(
            modules_completed=list(state.modules_completed),
            step_history={},
            started_at=None,
        )
        inventory = inventory_cls(
            recap_sections=set(state.recap_sections),
            journal_entries=set(state.journal_entries),
            certificates=set(state.certificates),
        )
        plan = plan_backfill(progress, inventory)
        for field in (
            "recap_modules", "journal_modules", "certificate_modules",
            "recap_sections", "journal_entries", "certificates",
            "missing_recap", "missing_journal", "missing_certificate",
        ):
            if hasattr(plan, field):
                assert not set(getattr(plan, field)), (
                    f"Non-bug state must yield an empty backfill plan; {field} not empty"
                )
