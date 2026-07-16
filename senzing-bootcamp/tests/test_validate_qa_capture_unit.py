"""Unit tests for the graduation Q&A completeness validator.

Feature: durable-qa-capture

Exercises ``senzing-bootcamp/scripts/validate_qa_capture.py`` -- the loud
graduation gate that halts (exit non-zero) and names any completed module with
no real captured Q&A, while letting fully-captured modules and legitimately
question-free modules (carrying the explicit "no substantive questions" marker)
pass (exit 0).

Each test builds an isolated temp workspace with ``config/`` state files
(``bootcamp_progress.json`` and ``session_log.jsonl``) seeded via the production
event schema (``session_logger.build_completion_entry`` /
``append_completion_entry``), then invokes ``validate_qa_capture.main`` through
its ``argv`` surface and asserts exit code, human-readable / ``--json`` output
shape, and the no-side-effect guarantee of ``--check``.

**Validates: Requirements 2.3, 2.4**
"""

from __future__ import annotations

import contextlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Scripts import via sys.path (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import session_logger  # noqa: E402  (path manipulated above)
import validate_qa_capture  # noqa: E402  (path manipulated above)

# Workspace-relative state files (matching the scripts' conventions).
_SESSION_LOG: str = "config/session_log.jsonl"
_PROGRESS: str = "config/bootcamp_progress.json"


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def workspace():
    """Yield a throwaway workspace with a ``config/`` directory.

    Removed on exit.

    Yields:
        The workspace root ``Path`` (its ``config/`` subdir holds the state
        files the validator reads).
    """
    root = Path(tempfile.mkdtemp(prefix="validate_qa_capture_"))
    (root / "config").mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def progress_path(root: Path) -> str:
    """Return the absolute progress-file path for *root*."""
    return str(root / _PROGRESS)


def log_path(root: Path) -> str:
    """Return the absolute session-log path for *root*."""
    return str(root / _SESSION_LOG)


def write_progress(root: Path, modules_completed: list[int]) -> None:
    """Write ``config/bootcamp_progress.json`` with the completed modules.

    Args:
        root: The workspace root.
        modules_completed: The modules to record as completed.
    """
    (root / _PROGRESS).write_text(
        json.dumps(
            {
                "current_module": (max(modules_completed) if modules_completed else 1),
                "modules_completed": sorted(modules_completed),
            }
        ),
        encoding="utf-8",
    )


def write_real_qa(root: Path, module: int, question: str, answer: str) -> None:
    """Append a real, paired ``question``/``answer`` exchange for *module*.

    Uses the production event schema so the events are indistinguishable from
    those captured during a live session.

    Args:
        root: The workspace root.
        module: The module the exchange belongs to.
        question: The question text.
        answer: The answer text.
    """
    qid = session_logger.generate_question_id()
    session_logger.append_completion_entry(
        log_path(root),
        session_logger.build_completion_entry(
            "question", module, {"text": question, "question_id": qid}
        ),
    )
    session_logger.append_completion_entry(
        log_path(root),
        session_logger.build_completion_entry(
            "answer", module, {"text": answer, "question_id": qid}
        ),
    )


def write_unanswered_question(root: Path, module: int, question: str) -> None:
    """Append a real ``question`` event with no paired answer for *module*.

    Args:
        root: The workspace root.
        module: The module the question belongs to.
        question: The question text.
    """
    qid = session_logger.generate_question_id()
    session_logger.append_completion_entry(
        log_path(root),
        session_logger.build_completion_entry(
            "question", module, {"text": question, "question_id": qid}
        ),
    )


def write_no_questions_marker(root: Path, module: int) -> None:
    """Append an explicit "no substantive questions" marker for *module*.

    The marker is an ``action`` completion event whose ``data.description``
    contains :data:`validate_qa_capture.NO_QUESTIONS_MARKER` (case-insensitive),
    telling the validator the module intentionally posed no questions.

    Args:
        root: The workspace root.
        module: The module to mark as legitimately question-free.
    """
    session_logger.append_completion_entry(
        log_path(root),
        session_logger.build_completion_entry(
            "action",
            module,
            {
                "action_type": "command_run",
                "description": (
                    f"Module {module} had no substantive questions for the "
                    "bootcamper this session."
                ),
            },
        ),
    )


def run(root: Path, extra_args: list[str] | None = None) -> int:
    """Invoke ``validate_qa_capture.main`` against *root*'s state files.

    Args:
        root: The workspace root.
        extra_args: Additional CLI flags (e.g. ``["--json"]`` or ``["--check"]``).

    Returns:
        The validator's exit code (0 pass, 1 gap).
    """
    argv = ["--progress", progress_path(root), "--log", log_path(root)]
    if extra_args:
        argv.extend(extra_args)
    return validate_qa_capture.main(argv)


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
    """Draw ``(modules_completed, gap_modules)`` with >=1 completed gap module.

    ``gap_modules`` is a non-empty subset of ``modules_completed`` whose members
    have NO real Q&A; the remaining completed modules get a real, paired
    exchange written by the caller.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(modules_completed, gap_modules)`` tuple (both sorted).
    """
    completed = draw(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=1,
            max_size=6,
            unique=True,
        )
    )
    gap_modules = draw(
        st.lists(
            st.sampled_from(sorted(completed)),
            min_size=1,
            max_size=len(completed),
            unique=True,
        )
    )
    return sorted(completed), sorted(set(gap_modules))


# ---------------------------------------------------------------------------
# Pass: fully-captured modules
# ---------------------------------------------------------------------------


class TestCompletedModuleWithRealQAPasses:
    """A completed module with real Q&A passes the validator (exit 0).

    **Validates: Requirements 2.3**
    """

    def test_single_module_with_paired_qa_passes(self, capsys) -> None:
        """One completed module with a paired exchange -> exit 0, "complete"."""
        with workspace() as root:
            write_progress(root, [3])
            write_real_qa(root, 3, "What is entity resolution?", "Matching records.")

            assert run(root) == 0
            out = capsys.readouterr().out
            assert "complete" in out.lower()

    def test_all_completed_modules_with_qa_pass(self, capsys) -> None:
        """Several completed modules, each with real Q&A -> exit 0."""
        with workspace() as root:
            write_progress(root, [1, 2, 3])
            write_real_qa(root, 1, "Q1?", "A1")
            write_real_qa(root, 2, "Q2?", "A2")
            write_real_qa(root, 3, "Q3?", "A3")

            assert run(root) == 0

    def test_question_without_answer_still_passes(self) -> None:
        """A real question with no paired answer is not a gap -> exit 0.

        The gate requires at least one real ``question`` event; an unanswered
        question is still real Q&A, so the module is not a capture gap.
        """
        with workspace() as root:
            write_progress(root, [4])
            write_unanswered_question(root, 4, "An unanswered reflection question?")

            assert run(root) == 0


# ---------------------------------------------------------------------------
# Fail: genuine capture gap
# ---------------------------------------------------------------------------


class TestCompletedModuleMissingQAFails:
    """A completed module with no real Q&A fails and names the module.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_missing_qa_fails_and_names_module(self, capsys) -> None:
        """Module 2 completed with no Q&A -> exit 1, "Module 2" surfaced."""
        with workspace() as root:
            write_progress(root, [2])
            # No Q&A and no marker for Module 2 -> a genuine capture gap.

            assert run(root) == 1
            captured = capsys.readouterr()
            # The module is named on both the human summary (stdout) and the
            # concise error line (stderr).
            assert "Module 2" in captured.out
            assert "Module 2" in captured.err

    def test_gap_among_other_modules_is_named(self, capsys) -> None:
        """Only the gap module is named when other modules have real Q&A."""
        with workspace() as root:
            write_progress(root, [1, 2, 3])
            write_real_qa(root, 1, "Q1?", "A1")
            # Module 2 is the gap (no Q&A, no marker).
            write_real_qa(root, 3, "Q3?", "A3")

            assert run(root) == 1
            out = capsys.readouterr().out
            assert "Module 2" in out
            assert "Module 1" not in out
            assert "Module 3" not in out


# ---------------------------------------------------------------------------
# Pass: legitimately question-free module (marker present)
# ---------------------------------------------------------------------------


class TestLegitimatelyEmptyModulePasses:
    """A marked question-free module is not a gap and passes (exit 0).

    **Validates: Requirements 2.3, 2.4**
    """

    def test_marked_empty_module_passes(self) -> None:
        """A "no substantive questions" marker makes an empty module pass."""
        with workspace() as root:
            write_progress(root, [2])
            write_no_questions_marker(root, 2)

            assert run(root) == 0

    def test_marker_is_case_insensitive(self) -> None:
        """The marker phrase is matched case-insensitively."""
        with workspace() as root:
            write_progress(root, [5])
            session_logger.append_completion_entry(
                log_path(root),
                session_logger.build_completion_entry(
                    "action",
                    5,
                    {
                        "action_type": "command_run",
                        "description": "NO SUBSTANTIVE QUESTIONS were posed.",
                    },
                ),
            )

            assert run(root) == 0


# ---------------------------------------------------------------------------
# Mixed state: real + gap + marked
# ---------------------------------------------------------------------------


class TestMixedStateNamesOnlyTheGap:
    """One real, one gap, one marked module -> fails, naming ONLY the gap.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_mixed_state_fails_naming_only_the_gap(self, capsys) -> None:
        """Real (1) + gap (2) + marked-empty (3): exit 1, only Module 2 named."""
        with workspace() as root:
            write_progress(root, [1, 2, 3])
            write_real_qa(root, 1, "What is a data source?", "A named record feed.")
            # Module 2: genuine gap (no Q&A, no marker).
            write_no_questions_marker(root, 3)

            assert run(root) == 1
            captured = capsys.readouterr()
            assert "Module 2" in captured.out
            assert "Module 1" not in captured.out
            assert "Module 3" not in captured.out


# ---------------------------------------------------------------------------
# --json output shape
# ---------------------------------------------------------------------------


class TestJsonOutputShape:
    """``--json`` emits the documented machine-readable report shape.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_json_shape_on_gap(self, capsys) -> None:
        """A gap yields ok=false, missing_modules, and per-module fields."""
        with workspace() as root:
            write_progress(root, [1, 2])
            write_real_qa(root, 1, "Q1?", "A1")
            # Module 2 is the gap.

            exit_code = run(root, ["--json"])
            report = json.loads(capsys.readouterr().out)

            assert exit_code == 1
            assert report["ok"] is False
            assert report["missing_modules"] == [2]

            by_module = {m["module"]: m for m in report["modules"]}
            assert set(by_module) == {1, 2}

            # Every per-module entry carries the full field contract.
            expected_fields = {
                "module",
                "question_count",
                "answer_count",
                "paired_answer_count",
                "orphan_answer_count",
                "has_no_questions_marker",
                "is_gap",
            }
            for entry in report["modules"]:
                assert expected_fields <= set(entry)

            # Module 1 has a paired exchange; Module 2 is the flagged gap.
            assert by_module[1]["question_count"] == 1
            assert by_module[1]["paired_answer_count"] == 1
            assert by_module[1]["is_gap"] is False
            assert by_module[2]["question_count"] == 0
            assert by_module[2]["is_gap"] is True

    def test_json_shape_when_ok(self, capsys) -> None:
        """A fully-captured track yields ok=true and no missing modules."""
        with workspace() as root:
            write_progress(root, [1])
            write_real_qa(root, 1, "Q1?", "A1")

            exit_code = run(root, ["--json"])
            report = json.loads(capsys.readouterr().out)

            assert exit_code == 0
            assert report["ok"] is True
            assert report["missing_modules"] == []
            assert report["modules"][0]["is_gap"] is False


# ---------------------------------------------------------------------------
# --check verify-only behavior
# ---------------------------------------------------------------------------


class TestCheckVerifyOnly:
    """``--check`` verifies without side effects, same pass/fail semantics.

    **Validates: Requirements 2.3, 2.4**
    """

    def test_check_matches_default_pass_fail(self, capsys) -> None:
        """--check returns the same exit code as the default validate run."""
        with workspace() as root:
            write_progress(root, [1, 2])
            write_real_qa(root, 1, "Q1?", "A1")
            # Module 2 is a gap.

            default_code = run(root)
            capsys.readouterr()  # discard default-run output
            check_code = run(root, ["--check"])

            assert default_code == 1
            assert check_code == 1

    def test_check_passes_on_complete_track(self) -> None:
        """--check exits 0 when every completed module has real Q&A."""
        with workspace() as root:
            write_progress(root, [1])
            write_real_qa(root, 1, "Q1?", "A1")

            assert run(root, ["--check"]) == 0

    def test_check_makes_no_side_effects(self) -> None:
        """--check leaves the progress file and session log byte-for-byte intact."""
        with workspace() as root:
            write_progress(root, [1, 2])
            write_real_qa(root, 1, "Q1?", "A1")

            progress_before = Path(progress_path(root)).read_bytes()
            log_before = Path(log_path(root)).read_bytes()

            run(root, ["--check"])

            assert Path(progress_path(root)).read_bytes() == progress_before
            assert Path(log_path(root)).read_bytes() == log_before


# ---------------------------------------------------------------------------
# Edge cases: nothing to validate
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Degenerate inputs validate cleanly (nothing to validate -> exit 0).

    **Validates: Requirements 2.3, 2.4**
    """

    def test_no_completed_modules_passes(self) -> None:
        """An empty ``modules_completed`` list -> exit 0 (nothing to gate)."""
        with workspace() as root:
            write_progress(root, [])
            assert run(root) == 0

    def test_absent_progress_file_passes(self) -> None:
        """A missing progress file -> exit 0 (nothing to validate)."""
        with workspace() as root:
            # No progress file written at all.
            assert run(root) == 0

    def test_malformed_progress_file_passes(self) -> None:
        """A malformed progress file -> exit 0 (tolerant, nothing to validate)."""
        with workspace() as root:
            (root / _PROGRESS).write_text("{ not valid json", encoding="utf-8")
            assert run(root) == 0

    def test_completed_modules_but_absent_log_fails_and_names_them(self, capsys) -> None:
        """Completed modules with no session log at all -> gaps, exit 1."""
        with workspace() as root:
            write_progress(root, [1])
            # No session log exists -> Module 1 has no Q&A -> a gap.

            assert run(root) == 1
            assert "Module 1" in capsys.readouterr().out

    def test_malformed_log_lines_are_tolerated(self) -> None:
        """Blank and malformed log lines are skipped without raising."""
        with workspace() as root:
            write_progress(root, [1])
            write_real_qa(root, 1, "Q1?", "A1")
            # Append junk that must be skipped, not crash the scan.
            with Path(log_path(root)).open("a", encoding="utf-8") as fh:
                fh.write("\n")
                fh.write("{ not valid json\n")
                fh.write("not even json at all\n")

            assert run(root) == 0


# ---------------------------------------------------------------------------
# Property coverage (active Hypothesis profile; no inline max_examples)
# ---------------------------------------------------------------------------


class TestGapNamingProperty:
    """For any state with gap modules, the validator fails and names each gap.

    **Validates: Requirements 2.3, 2.4**
    """

    @given(state=st_gap_state(), question=st_qa_text(), answer=st_qa_text())
    def test_every_gap_module_is_named(
        self, state: tuple[list[int], list[int]], question: str, answer: str
    ) -> None:
        completed, gap_modules = state
        with workspace() as root:
            write_progress(root, completed)
            # Non-gap completed modules get a real, paired exchange so only the
            # gap modules should be flagged.
            for module in completed:
                if module not in gap_modules:
                    write_real_qa(root, module, question, answer)

            # Build the report directly (no function-scoped fixture inside
            # @given) and assert the gate flags exactly the gap modules.
            report = validate_qa_capture.build_report(
                progress_path(root), log_path(root)
            )

            assert report.ok is False
            assert sorted(report.missing_modules) == gap_modules
            # And the CLI surfaces the same failing verdict.
            assert run(root) == 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
