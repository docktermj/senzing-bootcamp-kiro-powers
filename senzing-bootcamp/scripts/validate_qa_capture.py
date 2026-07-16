#!/usr/bin/env python3
"""Senzing Bootcamp - Graduation Q&A Completeness Validator.

A stdlib-only pre-render gate for the graduation path. Given
``config/bootcamp_progress.json`` and ``config/session_log.jsonl``, it verifies
that every module in ``modules_completed`` has at least one real captured
``question`` event (and, where a question was answered, a paired ``answer``).

This is the "loud graduation validation" half of the durable-qa-capture fix: it
runs BEFORE any recap rendering so a completed module with no real Q&A halts
graduation and names the offending module(s), rather than letting the recap
backfill emit the silent placeholder "N/A (section backfilled at track
completion; original session content unavailable)".

A genuine capture gap is distinguished from a legitimately question-free module
by an explicit marker (see ``NO_QUESTIONS_MARKER`` below), so a module that
truly posed no substantive questions does not false-positive as a gap.

Counting reuses the existing helpers rather than re-parsing:
``reconcile_transcript.count_logged_questions`` for per-module ``question``
tallies and ``generate_transcript.read_events`` / ``build_model`` for
answer pairing.

Usage:
    # Human-readable summary; exit 1 (naming the module) on a gap.
    python3 scripts/validate_qa_capture.py

    # Verify-only (no side effects); the graduation gate uses this form.
    python3 scripts/validate_qa_capture.py --progress config/bootcamp_progress.json \\
        --log config/session_log.jsonl --check

    # Machine-readable report for tooling.
    python3 scripts/validate_qa_capture.py --json

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Scripts are not a package; make sibling modules importable by path.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_transcript  # noqa: E402  (path manipulated above)
import reconcile_transcript  # noqa: E402  (path manipulated above)

PROGRESS_PATH_DEFAULT: str = "config/bootcamp_progress.json"
LOG_PATH_DEFAULT: str = "config/session_log.jsonl"

# Explicit "no substantive questions" marker.
#
# The bootcamp event schema (``session_logger.COMPLETION_EVENT_TYPES``) has no
# dedicated marker event type, so a legitimately question-free module records an
# ``action`` completion event whose ``data.description`` contains this sentinel
# phrase (matched case-insensitively). Its presence for a module tells the
# validator that the module intentionally posed no substantive questions, so its
# absence of ``question`` events is expected rather than a capture gap. This is
# the same representation the graduation-gate exploration test models for a
# legitimately-empty module.
NO_QUESTIONS_MARKER: str = "no substantive questions"


@dataclass
class ModuleQAStatus:
    """Per-module Q&A completeness tally for a completed module.

    Attributes:
        module: The completed module number.
        question_count: Real ``question`` events logged for the module.
        answer_count: Total ``answer`` events for the module (paired + orphan).
        paired_answer_count: Answers paired to a question via ``question_id``.
        orphan_answer_count: Answers with no matching question in the log.
        has_no_questions_marker: Whether an explicit ``NO_QUESTIONS_MARKER``
            marker event was recorded for the module.
    """

    module: int
    question_count: int
    answer_count: int
    paired_answer_count: int
    orphan_answer_count: int
    has_no_questions_marker: bool

    @property
    def has_real_qa(self) -> bool:
        """Return whether the module has at least one real ``question`` event."""
        return self.question_count > 0

    @property
    def is_gap(self) -> bool:
        """Return whether the module is a genuine Q&A capture gap.

        A completed module is a gap when it has no real ``question`` events and
        carries no explicit "no substantive questions" marker. A marked
        question-free module is never a gap.
        """
        return self.question_count == 0 and not self.has_no_questions_marker


@dataclass
class ValidationReport:
    """Aggregate completeness result across all completed modules.

    Attributes:
        modules: One :class:`ModuleQAStatus` per completed module, in ascending
            module order.
    """

    modules: list[ModuleQAStatus] = field(default_factory=list)

    @property
    def missing_modules(self) -> list[int]:
        """Return the completed modules that are genuine Q&A gaps."""
        return [status.module for status in self.modules if status.is_gap]

    @property
    def ok(self) -> bool:
        """Return whether every completed module has real Q&A (or a marker)."""
        return not self.missing_modules


def load_completed_modules(progress_path: str) -> list[int]:
    """Load the completed-module list from the progress JSON.

    Tolerant of an absent, unreadable, or malformed progress file: any such
    case yields an empty list (nothing to validate), so the validator never
    raises. Non-integer and boolean members are ignored.

    Args:
        progress_path: Path to ``config/bootcamp_progress.json``.

    Returns:
        The sorted, de-duplicated ``modules_completed`` integers, or ``[]`` when
        the file is missing/unreadable/malformed or the field is not a list.
    """
    try:
        data = json.loads(Path(progress_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    completed = data.get("modules_completed", [])
    if not isinstance(completed, list):
        return []
    # Guard against bools (a subclass of int) so ``True`` never counts as 1.
    return sorted(
        {
            item
            for item in completed
            if isinstance(item, int) and not isinstance(item, bool)
        }
    )


def read_marker_modules(log_path: str) -> set[int]:
    """Return modules carrying an explicit "no substantive questions" marker.

    Performs a tolerant JSONL scan mirroring
    ``generate_transcript.read_events`` (blank and malformed lines are skipped
    and the scan never raises, including when the file is missing). A marker is
    an ``action`` completion event whose ``data.description`` contains
    :data:`NO_QUESTIONS_MARKER` (matched case-insensitively).

    Args:
        log_path: Path to the JSONL session log.

    Returns:
        The set of module numbers that carry a marker event.
    """
    markers: set[int] = set()
    path = Path(log_path)
    if not path.exists():
        return markers
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("event_type") != "action":
                    continue
                data = obj.get("data") or {}
                description = str(data.get("description", "")).lower()
                if NO_QUESTIONS_MARKER not in description:
                    continue
                module = obj.get("module", 0)
                if isinstance(module, int) and not isinstance(module, bool):
                    markers.add(module)
    except OSError:
        return markers
    return markers


def build_report(progress_path: str, log_path: str) -> ValidationReport:
    """Build the per-module completeness report.

    For every completed module, counts real ``question`` events (via
    ``reconcile_transcript.count_logged_questions``), tallies paired and orphan
    ``answer`` events (via ``generate_transcript.build_model``), and records
    whether an explicit "no substantive questions" marker is present. Modules
    not in ``modules_completed`` are ignored — only completed modules gate
    graduation.

    Args:
        progress_path: Path to ``config/bootcamp_progress.json``.
        log_path: Path to ``config/session_log.jsonl``.

    Returns:
        A :class:`ValidationReport` with one status per completed module in
        ascending module order.
    """
    completed = load_completed_modules(progress_path)
    logged_questions = reconcile_transcript.count_logged_questions(log_path)
    model = generate_transcript.build_model(generate_transcript.read_events(log_path))
    markers = read_marker_modules(log_path)

    # Paired answers per module: a QAPair with a non-None answer.
    paired_by_module: dict[int, int] = {}
    for pair in model.pairs:
        if pair.answer_text is not None:
            paired_by_module[pair.module] = paired_by_module.get(pair.module, 0) + 1

    # Orphan answers per module: answers with no matching question.
    orphan_by_module: dict[int, int] = {}
    for event in model.orphan_answers:
        module = event.get("module", 0)
        orphan_by_module[module] = orphan_by_module.get(module, 0) + 1

    statuses: list[ModuleQAStatus] = []
    for module in completed:
        paired = paired_by_module.get(module, 0)
        orphan = orphan_by_module.get(module, 0)
        statuses.append(
            ModuleQAStatus(
                module=module,
                question_count=logged_questions.get(module, 0),
                answer_count=paired + orphan,
                paired_answer_count=paired,
                orphan_answer_count=orphan,
                has_no_questions_marker=module in markers,
            )
        )
    return ValidationReport(modules=statuses)


def _report_to_dict(report: ValidationReport) -> dict:
    """Serialize a :class:`ValidationReport` to the JSON contract shape.

    Args:
        report: The report to serialize.

    Returns:
        A JSON-serializable dictionary describing the report.
    """
    return {
        "ok": report.ok,
        "missing_modules": report.missing_modules,
        "modules": [
            {
                "module": status.module,
                "question_count": status.question_count,
                "answer_count": status.answer_count,
                "paired_answer_count": status.paired_answer_count,
                "orphan_answer_count": status.orphan_answer_count,
                "has_no_questions_marker": status.has_no_questions_marker,
                "is_gap": status.is_gap,
            }
            for status in report.modules
        ],
    }


def _print_summary(report: ValidationReport) -> None:
    """Print a human-readable summary of the report to stdout.

    Args:
        report: The report to summarize.
    """
    if report.ok:
        print(
            "Q&A capture complete: every completed module has real Q&A "
            "(or an explicit no-substantive-questions marker)."
        )
        return
    print(
        "Q&A capture INCOMPLETE - the following completed module(s) have no "
        "captured Q&A:"
    )
    for module in report.missing_modules:
        print(
            f"  Module {module}: no question events and no "
            f"'{NO_QUESTIONS_MARKER}' marker"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace with ``progress``, ``log``, ``json``, and
        ``check`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate that every completed bootcamp module has real captured "
            "Q&A before the graduation recap is rendered; fail loudly and name "
            "the missing module(s) on any gap."
        ),
    )
    parser.add_argument(
        "--progress",
        default=PROGRESS_PATH_DEFAULT,
        help=f"Path to the progress JSON (default: {PROGRESS_PATH_DEFAULT}).",
    )
    parser.add_argument(
        "--log",
        default=LOG_PATH_DEFAULT,
        help=f"Path to the JSONL session log (default: {LOG_PATH_DEFAULT}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the validation report as JSON for machine consumption.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Verify only (no side effects); the graduation gate uses this form. "
            "This validator never mutates state, so --check behaves like the "
            "default validate run: exit non-zero and name the missing "
            "module(s) on any gap."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the completeness validator.

    Builds the per-module report and reports the result. On any gap it exits
    non-zero and names each missing module as ``Module N`` on both stdout (the
    human summary) and stderr (a concise error line), so the graduation gate can
    surface the missing module(s) to the bootcamper.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: ``0`` when every completed module has real Q&A (or a marker),
        ``1`` when at least one completed module is a genuine Q&A gap.
    """
    args = parse_args(argv)
    report = build_report(args.progress, args.log)

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2))
    else:
        _print_summary(report)

    if not report.ok:
        for module in report.missing_modules:
            print(
                f"ERROR: Module {module} has no captured Q&A "
                "(graduation halted).",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
