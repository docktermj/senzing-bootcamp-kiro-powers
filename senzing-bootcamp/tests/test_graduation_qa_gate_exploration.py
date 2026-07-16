"""Bug-condition EXPLORATION tests for the loud-graduation-validation gap.

These tests exercise the graduation path in the case the design's
``isGraduationBugCondition`` describes:

    isGraduationBugCondition(state) ==
        renderingBegun(state)
        AND EXISTS module IN state.modulesCompleted SUCH THAT
            NOT hasRealQA("config/session_log.jsonl", module)
        AND rendersPlaceholderInsteadOfHalting(state, module)

Today the graduation / recap path has NO pre-render completeness gate. When a
completed module has no real captured Q&A, rendering reaches
``completion_artifacts.render_backfill_section`` (via
``backfill_recap_sections``), which emits the honest-but-silent placeholder::

    - N/A (section backfilled at track completion; original session content
      unavailable)

and graduation still reports success. The missing-Q&A gap is masked rather than
surfaced, so the loss is invisible until a human inspects the recap "trophy".

These tests model the *fixed* behavior from design Property 2 (Loud Graduation
Validation): before any recap rendering, a completeness validator
(``senzing-bootcamp/scripts/validate_qa_capture.py``, wired into the graduation
path per tasks 6.4/6.5) must HALT graduation and NAME every completed module
that lacks real Q&A, rather than letting the backfill emit placeholder text.
``_run_graduation`` runs that pre-render gate exactly as the fixed graduation
path would: it invokes the validator if it is wired, halting before rendering
when the validator flags a gap. When no such validator exists (the current,
unfixed state) there is no gate, rendering proceeds, and the placeholder is
silently emitted while graduation reports success.

**They are AUTHORED TO FAIL on the current (unfixed) code** — there is no
``validate_qa_capture.py`` gate, so ``_run_graduation`` never halts, the recap
is backfilled with the placeholder, and graduation reports success. Those
failures CONFIRM the bug (the missing pre-render completeness gate); they must
NOT be "fixed" here. After the fix lands (tasks 6.4/6.5 add the validator and
wire it before rendering), these same tests will pass.

The final class documents the gap-vs-empty EDGE CASE: today the render path
does not distinguish a genuine capture gap from a legitimately question-free
module, so both currently receive the same placeholder. That documentation test
PASSES on unfixed code and informs the fix (the validator must recognize an
explicit "no substantive questions" marker so it does not false-positive).

Feature: durable-qa-capture

**Validates: Requirements 2.3, 2.4** (the fixed loud-validation behavior these
encode). Explores defect Requirements 1.3, 1.4.
"""

from __future__ import annotations

import contextlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from hypothesis import Phase, given, settings
from hypothesis import strategies as st

# Exclude only Hypothesis' post-shrink ``explain`` phase. It has a known
# internal crash (``assert span1.start <= start``) that can fire while
# annotating a counterexample, which would mask the real assertion failure this
# exploration test is meant to surface. Every other phase (and the profile's
# ``max_examples`` baseline) is preserved.
_PHASES_NO_EXPLAIN = tuple(phase for phase in Phase if phase is not Phase.explain)

# Scripts are not packages; make them importable via the documented sys.path
# pattern (conftest also does this, kept here so the module imports standalone).
_POWER_ROOT: Path = Path(__file__).resolve().parent.parent  # senzing-bootcamp/
_SCRIPTS_DIR: str = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts  # noqa: E402  (path manipulated above)
import session_logger  # noqa: E402  (path manipulated above)

# The completeness validator the fix introduces (tasks 6.4/6.5). It does NOT
# exist on unfixed code, so the graduation gate below is absent and rendering
# silently backfills — exactly the bug these tests surface.
_VALIDATOR: Path = _POWER_ROOT / "scripts" / "validate_qa_capture.py"

# Workspace-relative state files (matching the scripts' conventions).
_SESSION_LOG: str = "config/session_log.jsonl"
_PROGRESS: str = "config/bootcamp_progress.json"
_RECAP: str = "docs/bootcamp_recap.md"

# The exact placeholder the backfill emits for a module with no recoverable Q&A.
_PLACEHOLDER: str = (
    "N/A (section backfilled at track completion; "
    "original session content unavailable)"
)


# ---------------------------------------------------------------------------
# Graduation modelling
# ---------------------------------------------------------------------------


@dataclass
class GraduationResult:
    """Outcome of running the (fixed) graduation path against a workspace.

    Attributes:
        halted: Whether the pre-render completeness gate halted graduation.
        missing_modules: The completed modules the gate named as lacking real
            Q&A (empty when the gate did not run or did not fire).
        recap_text: The recap Markdown produced by rendering (empty when
            graduation halted before rendering).
        reported_success: Whether graduation reported success (i.e. it did not
            halt and rendering completed).
    """

    halted: bool = False
    missing_modules: list[int] = field(default_factory=list)
    recap_text: str = ""
    reported_success: bool = False


def _parse_missing_modules(output: str) -> list[int]:
    """Extract module numbers named by the validator from its output.

    The fixed validator names each completed module lacking real Q&A. This
    tolerant parser pulls every ``Module N`` reference out of the combined
    stdout/stderr so the assertion does not depend on an exact message format.

    Args:
        output: The combined validator stdout/stderr text.

    Returns:
        The sorted, de-duplicated module numbers mentioned in the output.
    """
    found = {int(m) for m in re.findall(r"[Mm]odule\s+(\d+)", output)}
    return sorted(found)


def _run_graduation(workspace: Path) -> GraduationResult:
    """Run the graduation path with the fixed pre-render completeness gate.

    Models the fixed graduation flow (design Property 2, tasks 6.4/6.5): BEFORE
    any recap rendering, invoke the completeness validator
    (``validate_qa_capture.py``) against ``config/bootcamp_progress.json`` and
    ``config/session_log.jsonl``. When the validator flags a completed module
    with no real Q&A it exits non-zero and names the module(s); graduation then
    HALTS without rendering, so no placeholder is emitted.

    When no validator is wired (the current, unfixed state) there is no gate:
    graduation proceeds straight to rendering via
    ``completion_artifacts.backfill_recap_sections``, which backfills any missing
    per-module section with placeholder text, and reports success. That absent
    gate is precisely the bug the exploration tests surface.

    Args:
        workspace: The workspace root holding ``config/`` and ``docs/``.

    Returns:
        A :class:`GraduationResult` describing whether graduation halted, which
        modules were named, the rendered recap text, and whether success was
        reported.
    """
    progress_path = workspace / _PROGRESS
    log_path = workspace / _SESSION_LOG
    recap_path = workspace / _RECAP

    # Fixed pre-render completeness gate. Absent on unfixed code -> no halt.
    if _VALIDATOR.exists():
        proc = subprocess.run(
            [
                sys.executable,
                str(_VALIDATOR),
                "--progress",
                str(progress_path),
                "--log",
                str(log_path),
                "--check",
            ],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return GraduationResult(
                halted=True,
                missing_modules=_parse_missing_modules(proc.stdout + proc.stderr),
                recap_text="",
                reported_success=False,
            )

    # No gate (or gate passed): render the recap. Missing per-module sections
    # are backfilled with placeholder text.
    completion_artifacts.backfill_recap_sections(str(progress_path), str(recap_path))
    recap_text = recap_path.read_text(encoding="utf-8") if recap_path.exists() else ""
    return GraduationResult(
        halted=False,
        missing_modules=[],
        recap_text=recap_text,
        reported_success=True,
    )


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _workspace():
    """Yield a throwaway workspace with ``config/`` and ``docs/`` directories.

    Removed on exit.

    Yields:
        The workspace root ``Path``.
    """
    root = Path(tempfile.mkdtemp(prefix="grad_qa_gate_expl_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _write_progress(workspace: Path, modules_completed: list[int]) -> None:
    """Write ``config/bootcamp_progress.json`` with the completed modules."""
    (workspace / _PROGRESS).write_text(
        json.dumps(
            {
                "current_module": (max(modules_completed) if modules_completed else 1),
                "modules_completed": sorted(modules_completed),
            }
        ),
        encoding="utf-8",
    )


def _write_real_qa(workspace: Path, module: int, question: str, answer: str) -> None:
    """Append a real, paired ``question``/``answer`` exchange for *module*.

    Uses the production event schema (``session_logger.build_completion_entry`` /
    ``append_completion_entry``) so the events are indistinguishable from those
    captured during a live session.

    Args:
        workspace: The workspace root.
        module: The module the exchange belongs to.
        question: The question text.
        answer: The answer text.
    """
    log_path = str(workspace / _SESSION_LOG)
    question_id = session_logger.generate_question_id()
    session_logger.append_completion_entry(
        log_path,
        session_logger.build_completion_entry(
            "question", module, {"text": question, "question_id": question_id}
        ),
    )
    session_logger.append_completion_entry(
        log_path,
        session_logger.build_completion_entry(
            "answer", module, {"text": answer, "question_id": question_id}
        ),
    )


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

_SAFE_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 .,?!"
)


def st_qa_text() -> st.SearchStrategy[str]:
    """A single-line, PII-free, non-empty question/answer string."""
    return (
        st.text(alphabet=_SAFE_ALPHABET, min_size=1, max_size=60)
        .map(str.strip)
        .filter(bool)
    )


@st.composite
def st_gap_state(draw) -> tuple[list[int], list[int]]:
    """Draw a graduation state with at least one completed Q&A-gap module.

    Returns a ``(modules_completed, gap_modules)`` pair where ``gap_modules`` is
    a non-empty subset of ``modules_completed``. Modules in ``gap_modules`` have
    NO real Q&A; the remaining completed modules each get a real, paired
    exchange written by the caller.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(modules_completed, gap_modules)`` tuple.
    """
    completed = draw(
        st.lists(st.integers(min_value=1, max_value=11), min_size=1, max_size=6, unique=True)
    )
    # At least one completed module is a genuine capture gap.
    gap_modules = draw(
        st.lists(st.sampled_from(sorted(completed)), min_size=1, max_size=len(completed), unique=True)
    )
    return sorted(completed), sorted(set(gap_modules))


# ---------------------------------------------------------------------------
# Example bug-condition test (deterministic, reproducible)
# ---------------------------------------------------------------------------


class TestSilentPlaceholderAtGraduationExploration:
    """A completed module with no real Q&A must halt graduation, not backfill.

    **Validates: Requirements 2.3, 2.4**

    The reported deterministic case: Module 2 is completed but has no real
    captured Q&A. The fixed graduation path must validate completeness BEFORE
    rendering, halt, and name Module 2 — never letting the backfill emit the
    "backfilled at track completion" placeholder while reporting success.

    AUTHORED TO FAIL on unfixed code: with no ``validate_qa_capture.py`` gate,
    ``_run_graduation`` does not halt, the recap is backfilled with the
    placeholder, and graduation reports success — the missing pre-render gate.
    """

    def test_module2_gap_halts_graduation_without_placeholder(self) -> None:
        """Module 2 gap: graduation halts and names it; no placeholder emitted."""
        with _workspace() as workspace:
            _write_progress(workspace, modules_completed=[2])
            # No real Q&A is written for Module 2 -> it is a genuine capture gap.

            result = _run_graduation(workspace)

            assert result.halted, (
                "graduation did not halt on a completed module with no real "
                "Q&A: there is no pre-render completeness gate, so the recap "
                "was silently backfilled with placeholder text while graduation "
                f"reported success (reported_success={result.reported_success}). "
                "Expected graduation to halt loudly and name Module 2."
            )
            assert 2 in result.missing_modules, (
                "graduation halted but did not name the missing module; expected "
                f"Module 2 in {result.missing_modules!r}"
            )
            assert _PLACEHOLDER not in result.recap_text, (
                "the recap silently rendered the backfill placeholder for a real "
                f"Q&A gap instead of halting: found {_PLACEHOLDER!r} in the recap"
            )


# ---------------------------------------------------------------------------
# Property-based bug-condition test
# ---------------------------------------------------------------------------


class TestLoudGraduationValidationProperty:
    """For any state with a Q&A-gap module, graduation halts and names it.

    **Validates: Requirements 2.3, 2.4**

    Generates arbitrary ``(modules_completed, gap_modules)`` states where at
    least one completed module has no real Q&A (the other completed modules get
    a real, paired exchange). The fixed graduation path must halt before
    rendering, name every gap module, and emit no placeholder.

    AUTHORED TO FAIL on unfixed code: with no completeness gate, graduation
    never halts and the recap is backfilled with placeholder text for the gap
    module(s) — surfacing the bug across the whole input domain.
    """

    @settings(phases=_PHASES_NO_EXPLAIN)
    @given(state=st_gap_state(), question=st_qa_text(), answer=st_qa_text())
    def test_any_gap_module_halts_graduation(
        self, state: tuple[list[int], list[int]], question: str, answer: str
    ) -> None:
        completed, gap_modules = state
        with _workspace() as workspace:
            _write_progress(workspace, modules_completed=completed)
            # Every non-gap completed module gets a real, paired exchange so the
            # gate has no reason to flag it; gap modules get nothing.
            for module in completed:
                if module not in gap_modules:
                    _write_real_qa(workspace, module, question, answer)

            result = _run_graduation(workspace)

            assert result.halted, (
                "graduation did not halt despite a completed module with no real "
                f"Q&A (gap modules={gap_modules!r}): there is no pre-render "
                "completeness gate, so the recap was backfilled with placeholder "
                f"text while graduation reported success. completed={completed!r}"
            )
            for module in gap_modules:
                assert module in result.missing_modules, (
                    f"graduation halted but did not name gap Module {module}; "
                    f"named {result.missing_modules!r}"
                )
            assert _PLACEHOLDER not in result.recap_text, (
                "the recap silently rendered the backfill placeholder for a real "
                f"Q&A gap instead of halting: found {_PLACEHOLDER!r} in the recap"
            )


# ---------------------------------------------------------------------------
# Edge case: gap-vs-empty distinction (RESOLVED by the fix)
# ---------------------------------------------------------------------------


class TestGapVsEmptyDistinctionEdge:
    """The fix distinguishes a genuine capture gap from a legitimately-empty module.

    **Validates: Requirements 2.3, 2.4**

    Before the fix the render path could not tell a real Q&A capture gap from a
    module that legitimately posed no substantive questions: with no
    "no substantive questions" marker and no completeness gate, both received the
    same backfill placeholder. The fix (tasks 6.4/6.5) adds the completeness
    validator and wires it before rendering, so the two cases now DIVERGE:

    - A genuine capture gap (no Q&A, no marker) HALTS graduation and names the
      module; no placeholder is emitted.
    - A legitimately question-free module carries an explicit "no substantive
      questions" marker, so it is NOT a gap: graduation proceeds and the module
      may reach the (legitimate) placeholder path.

    This encodes the RESOLVED behavior and therefore passes on the fixed code.
    """

    def test_gap_halts_but_legitimately_empty_module_passes(self) -> None:
        """A real gap halts and is named; a marked question-free module passes."""
        # A genuine capture gap: completed, no Q&A at all, no marker.
        with _workspace() as gap_ws:
            _write_progress(gap_ws, modules_completed=[2])
            gap_result = _run_graduation(gap_ws)

        # A legitimately question-free module: completed, and marked as having
        # posed no substantive questions via an explicit marker event the
        # validator recognizes.
        with _workspace() as empty_ws:
            _write_progress(empty_ws, modules_completed=[2])
            session_logger.append_completion_entry(
                str(empty_ws / _SESSION_LOG),
                session_logger.build_completion_entry(
                    "action",
                    2,
                    {
                        "action_type": "command_run",
                        "description": "no substantive questions for this module",
                    },
                ),
            )
            empty_result = _run_graduation(empty_ws)

        # The genuine gap halts loudly and names Module 2, emitting no placeholder.
        assert gap_result.halted, (
            "a genuine capture gap (no Q&A, no marker) must halt graduation; "
            f"got halted={gap_result.halted}"
        )
        assert 2 in gap_result.missing_modules, (
            f"the gap module must be named; got {gap_result.missing_modules!r}"
        )
        assert _PLACEHOLDER not in gap_result.recap_text, (
            "a real gap must not reach the backfill placeholder path"
        )

        # The legitimately-empty (marked) module is NOT a gap: graduation proceeds.
        assert not empty_result.halted, (
            "a legitimately question-free module (marker present) must not halt "
            f"graduation; got halted={empty_result.halted}"
        )
        assert 2 not in empty_result.missing_modules, (
            "a marked question-free module must not be reported as missing Q&A"
        )
