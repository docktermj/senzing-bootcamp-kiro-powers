#!/usr/bin/env python3
"""Senzing Bootcamp - Q&A Transcript Reconciliation Pass.

A stdlib-only pre-render step that repairs Q&A transcript shortfalls from the
enforced recap source *before* ``generate_transcript.py`` renders. It reads the
per-module recap (``docs/bootcamp_recap.md``) via the existing
``generate_recap_pdf.parse_recap_markdown`` and counts logged ``question``
completion events in ``config/session_log.jsonl`` against the recap's
``### Questions & Responses`` (QR) pairs per module. On a material shortfall it
backfills paired ``question``/``answer`` completion events using the existing
``session_logger`` writers, so the subsequent transcript render is complete.

The pass is idempotent (a no-op when counts already agree), non-blocking
(warn-and-continue on any failure), and adds no write-tool hook and no per-write
process spawn. It is invoked only at stopping points and at graduation
Step 0b.4, immediately before ``generate_transcript.py``.

Usage:
    python scripts/reconcile_transcript.py
    python scripts/reconcile_transcript.py --recap docs/bootcamp_recap.md \\
        --log config/session_log.jsonl

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# Scripts are not a package; make sibling modules importable by path.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_recap_pdf  # noqa: E402  (path manipulated above)
import generate_transcript  # noqa: E402  (path manipulated above)
import session_logger  # noqa: E402  (path manipulated above)

RECAP_PATH_DEFAULT: str = "docs/bootcamp_recap.md"
LOG_PATH_DEFAULT: str = "config/session_log.jsonl"


@dataclass
class ModuleCounts:
    """Per-module Q&A tallies from the two sources."""

    module: int
    logged_questions: int  # question events in the session log for this module
    recap_pairs: int  # QR pairs in the recap for this module


@dataclass
class ModuleShortfall:
    """Missing pairs for one module, derived from the recap."""

    module: int
    missing_pairs: list[tuple[str, str]]  # (question, response) in recap order


@dataclass
class ReconcilePlan:
    """The computed backfill plan across modules."""

    shortfalls: list[ModuleShortfall]  # modules needing backfill, in module order
    is_noop: bool  # True when counts are consistent (Req 1.3)
    recap_has_qr: bool  # False -> preserve existing behavior (Req 3.3)


def count_logged_questions(log_path: str) -> dict[int, int]:
    """Count logged ``question`` completion events per module.

    Performs a tolerant JSONL scan of the session log, reusing the
    line-skipping reader from ``generate_transcript.read_events`` (which skips
    blank and malformed lines and never raises, including when the file is
    missing). Only ``question`` completion events are counted; each contributes
    to the tally for its ``module``.

    Args:
        log_path: Path to the JSONL session log.

    Returns:
        A mapping of module number to the count of logged ``question`` events
        for that module. Modules with no logged questions are absent from the
        mapping.
    """
    counts: dict[int, int] = {}
    for event in generate_transcript.read_events(log_path):
        if event.get("event_type") != "question":
            continue
        module = event.get("module", 0)
        counts[module] = counts.get(module, 0) + 1
    return counts


def count_recap_pairs(recap_doc: generate_recap_pdf.RecapDocument) -> dict[int, int]:
    """Count recap QR pairs per module.

    Tallies the ``qr_pairs`` of each parsed recap section by its
    ``module_number``. Sections sharing a module number accumulate together.

    Args:
        recap_doc: A ``RecapDocument`` parsed by
            ``generate_recap_pdf.parse_recap_markdown``.

    Returns:
        A mapping of module number to the count of recap QR pairs for that
        module. Modules with no QR pairs are absent from the mapping.
    """
    counts: dict[int, int] = {}
    for section in recap_doc.sections:
        pair_count = len(section.qr_pairs)
        if pair_count == 0:
            continue
        module = section.module_number
        counts[module] = counts.get(module, 0) + pair_count
    return counts


def is_material_shortfall(logged: int, recap: int) -> bool:
    """Report whether a module's recap QR pairs exceed its logged questions.

    Applies the per-module deficit rule ``max(0, recap - logged) > 0``: a module
    is a material shortfall when the recap captured more QR pairs than the
    session log recorded ``question`` events for it. An over-logged module (more
    logged than recap) is never a shortfall.

    Args:
        logged: Count of logged ``question`` events for the module.
        recap: Count of recap QR pairs for the module.

    Returns:
        ``True`` when ``max(0, recap - logged) > 0``, else ``False``.
    """
    return max(0, recap - logged) > 0


def build_plan(
    logged: dict[int, int],
    recap_doc: generate_recap_pdf.RecapDocument,
) -> ReconcilePlan:
    """Compute the per-module backfill plan from the recap and logged counts.

    For each module carrying recap QR pairs (in ascending module order), the
    deficit is ``max(0, recap_pairs(N) - logged_questions(N))``. The derived
    missing pairs are the *last* ``deficit`` ``(question, response)`` pairs of
    that module in recap document order (the pairs not yet covered by logged
    questions), so already-logged content is never duplicated. Modules with no
    deficit contribute no shortfall.

    Args:
        logged: Mapping of module number to logged ``question`` count, as
            returned by :func:`count_logged_questions`.
        recap_doc: A ``RecapDocument`` parsed by
            ``generate_recap_pdf.parse_recap_markdown``.

    Returns:
        A ``ReconcilePlan`` whose ``shortfalls`` list the modules needing
        backfill in ascending module order, whose ``is_noop`` is ``True`` when
        the total deficit across all modules is zero, and whose ``recap_has_qr``
        is ``False`` when the recap contributes zero QR pairs across all modules.
    """
    # Collect the recap's QR pairs per module, preserving document order and
    # accumulating sections that share a module number.
    pairs_by_module: dict[int, list[tuple[str, str]]] = {}
    for section in recap_doc.sections:
        if not section.qr_pairs:
            continue
        module_pairs = pairs_by_module.setdefault(section.module_number, [])
        for pair in section.qr_pairs:
            module_pairs.append((pair.question, pair.response))

    recap_has_qr = bool(pairs_by_module)

    shortfalls: list[ModuleShortfall] = []
    for module in sorted(pairs_by_module):
        module_pairs = pairs_by_module[module]
        recap_count = len(module_pairs)
        logged_count = logged.get(module, 0)
        deficit = max(0, recap_count - logged_count)
        if deficit == 0:
            continue
        # The missing pairs are the trailing ``deficit`` pairs not yet covered
        # by the module's logged questions.
        missing_pairs = module_pairs[recap_count - deficit :]
        shortfalls.append(ModuleShortfall(module=module, missing_pairs=missing_pairs))

    total_deficit = sum(len(s.missing_pairs) for s in shortfalls)
    return ReconcilePlan(
        shortfalls=shortfalls,
        is_noop=total_deficit == 0,
        recap_has_qr=recap_has_qr,
    )


def apply_plan(plan: ReconcilePlan, log_path: str) -> int:
    """Backfill missing Q&A pairs by appending completion events to the log.

    For each shortfall in the plan (already in ascending module order), and for
    each missing ``(question, response)`` pair in recap order, mints a shared
    ``question_id`` and appends a paired ``question`` then ``answer`` completion
    entry via the existing ``session_logger`` writers. No new schema or writer
    is introduced; the events use the same schema the transcript renderer pairs
    by ``question_id``.

    Args:
        plan: The backfill plan produced by :func:`build_plan`.
        log_path: Path to the JSONL session log to append to.

    Returns:
        The number of ``(question, answer)`` pairs backfilled.
    """
    backfilled = 0
    for shortfall in plan.shortfalls:
        for question_text, response_text in shortfall.missing_pairs:
            qid = session_logger.generate_question_id()
            question_entry = session_logger.build_completion_entry(
                "question",
                shortfall.module,
                {"text": question_text, "question_id": qid},
            )
            answer_entry = session_logger.build_completion_entry(
                "answer",
                shortfall.module,
                {"text": response_text, "question_id": qid},
            )
            session_logger.append_completion_entry(log_path, question_entry)
            session_logger.append_completion_entry(log_path, answer_entry)
            backfilled += 1
    return backfilled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace with ``recap`` and ``log`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile the Q&A transcript against the enforced recap source by "
            "backfilling missing question/answer events before the transcript "
            "is rendered."
        ),
    )
    parser.add_argument(
        "--recap",
        default=RECAP_PATH_DEFAULT,
        help=f"Path to the recap Markdown (default: {RECAP_PATH_DEFAULT}).",
    )
    parser.add_argument(
        "--log",
        default=LOG_PATH_DEFAULT,
        help=f"Path to the JSONL session log (default: {LOG_PATH_DEFAULT}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the reconciliation pass.

    Reads the recap and session log, computes a backfill plan, and appends any
    missing ``question``/``answer`` events so the subsequent transcript render
    is complete. Non-blocking by contract: on any failure it warns to stderr and
    returns without raising.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on a clean run or clean no-op, 1 on an internally handled
        error path.
    """
    try:
        args = parse_args(argv)

        # Read the recap. A missing or unreadable recap is treated as zero recap
        # QR pairs (recap_has_qr=False, no-op) so the subsequent render proceeds
        # on the existing log (Req 3.3).
        try:
            recap_text = Path(args.recap).read_text(encoding="utf-8")
        except OSError as exc:
            print(
                f"reconcile_transcript: recap unavailable ({exc}); "
                f"skipping reconciliation",
                file=sys.stderr,
            )
            return 0

        recap_doc = generate_recap_pdf.parse_recap_markdown(recap_text)
        logged = count_logged_questions(args.log)
        plan = build_plan(logged, recap_doc)

        # Preserve existing behavior when the recap has no QR content (Req 3.3),
        # and do nothing when counts already agree (idempotent no-op, Req 1.3).
        if not plan.recap_has_qr or plan.is_noop:
            return 0

        apply_plan(plan, args.log)
        return 0
    except Exception as exc:  # noqa: BLE001 - non-blocking by contract (Req 3.2)
        # Any unexpected failure (corrupt Markdown, malformed log, write error)
        # must not propagate: warn and return so the caller continues to render.
        print(
            f"reconcile_transcript: reconciliation skipped due to error: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
