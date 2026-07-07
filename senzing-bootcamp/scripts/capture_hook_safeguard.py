#!/usr/bin/env python3
"""Senzing Bootcamp - Capture-Hook Completion Safeguard.

Runs at each module-completion boundary to detect any absent
*capture-critical* hook (``session-log-events``, ``module-recap-append``,
``ask-bootcamper``) and return a decision the completion steering renders:
a silent no-op when all three hooks are present, or a recurring, overridable
Soft_Block reminder (never a Mandatory_Gate) when any are missing.

The three capture-critical ids come from ``install_hooks.CAPTURE_CRITICAL`` —
the single source of truth shared with the session-start Warn_On_Absence_Check
so the two checks can never drift apart. This script only *names* the two
install options; it never installs on the bootcamper's behalf.

The safeguard is non-blocking by contract: a module transition never stalls on
it, and the steering caller treats the step as non-blocking regardless of exit
code.

Usage
-----
Detect and render the plan at a module-completion boundary::

    python3 senzing-bootcamp/scripts/capture_hook_safeguard.py --module 4

Record an explicit-override acknowledgment and allow the transition::

    python3 senzing-bootcamp/scripts/capture_hook_safeguard.py \\
        --module 4 --record-ack

Inspect a non-default hooks directory or progress file::

    python3 senzing-bootcamp/scripts/capture_hook_safeguard.py \\
        --hooks-dir /path/to/.kiro/hooks \\
        --progress /path/to/config/bootcamp_progress.json

Exit code 0 on a clean run/no-op, 1 only on an internally handled error path.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the single source of truth for the capture-critical hook ids.
# Scripts are not a package, so insert this script's directory onto sys.path
# and import ``install_hooks`` directly (matches the project's test convention).
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent  # senzing-bootcamp/scripts
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import install_hooks  # noqa: E402  (sys.path insertion must precede this import)

# The single source of the three capture-critical ids (never redefined here).
CAPTURE_CRITICAL = install_hooks.CAPTURE_CRITICAL


# ---------------------------------------------------------------------------
# Default paths (resolved relative to this script's location)
# ---------------------------------------------------------------------------

POWER_ROOT = SCRIPT_DIR.parent  # senzing-bootcamp
DEFAULT_HOOKS_DIR = POWER_ROOT.parent / ".kiro" / "hooks"  # <project>/.kiro/hooks
DEFAULT_PROGRESS = POWER_ROOT / "config" / "bootcamp_progress.json"


# ---------------------------------------------------------------------------
# Hook → output mapping (which deliverable each capture-critical hook feeds)
# ---------------------------------------------------------------------------
#
# Grounded in the requirements intro ("feed the recap, the Q&A transcript, and
# the completion summary") and the installer's hook descriptions. Every
# capture-critical id maps to at least one non-empty output so a named missing
# hook always reports a concrete degraded deliverable.

HOOK_OUTPUTS: dict[str, tuple[str, ...]] = {
    "module-recap-append": ("recap",),
    "session-log-events": ("transcript", "completion summary"),
    "ask-bootcamper": ("transcript", "completion summary"),
}


# ---------------------------------------------------------------------------
# Canonical install options (presented on Soft_Block) — the same two options
# offered by the session-start Warn_On_Absence_Check.
# ---------------------------------------------------------------------------

INSTALL_OPTION_RECREATE = (
    "Re-create the missing hook(s) with createHook from the hook registry "
    "(ask-bootcamper -> hook-registry-critical.md; "
    "module-recap-append, session-log-events -> hook-registry-module-any.md)"
)
INSTALL_OPTION_INSTALLER = (
    "Run: python3 senzing-bootcamp/scripts/install_hooks.py --essential"
)
INSTALL_OPTIONS: tuple[str, str] = (INSTALL_OPTION_RECREATE, INSTALL_OPTION_INSTALLER)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissingHook:
    """A single absent capture-critical hook and the outputs it feeds."""

    hook_id: str  # e.g. "module-recap-append"
    outputs: tuple[str, ...]  # subset of ("recap", "transcript", "completion summary")


@dataclass
class ReminderPlan:
    """The decision the steering renders at a module-completion boundary."""

    missing: list[MissingHook] = field(default_factory=list)  # absent hooks, sorted by id
    install_options: tuple[str, str] = INSTALL_OPTIONS  # the two canonical install options
    is_noop: bool = True  # True when nothing is missing
    is_soft_block: bool = False  # True when missing is non-empty; never a Mandatory_Gate


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def detect_missing_capture_hooks(hooks_dir: Path) -> list[str]:
    """Return the sorted capture-critical ids whose hook file is absent.

    Inspects ``hooks_dir`` (the bootcamper's ``.kiro/hooks`` directory) for an
    ``<id>.kiro.hook`` file for each id in ``CAPTURE_CRITICAL``. Detection keys
    only on the three ``<id>.kiro.hook`` filenames, so unrelated ``*.kiro.hook``
    files never affect the result. A missing or unreadable directory yields all
    three ids as missing. This function never raises.

    Args:
        hooks_dir: Path to the bootcamper's ``.kiro/hooks`` directory.

    Returns:
        The sorted list of capture-critical ids whose ``<id>.kiro.hook`` file is
        absent (empty when all three are present).
    """
    try:
        missing = [
            hook_id
            for hook_id in CAPTURE_CRITICAL
            if not (hooks_dir / f"{hook_id}.kiro.hook").is_file()
        ]
    except OSError:
        # Missing or unreadable directory — treat every hook as absent.
        missing = list(CAPTURE_CRITICAL)
    return sorted(missing)


def outputs_for_hook(hook_id: str) -> tuple[str, ...]:
    """Return the output(s) a capture-critical hook feeds.

    Maps a capture-critical id to its non-empty outputs (a subset of
    ``recap``, ``transcript``, ``completion summary``) via the ``HOOK_OUTPUTS``
    table, so a named missing hook always reports a concrete degraded
    deliverable.

    Args:
        hook_id: A capture-critical hook id (e.g. ``"module-recap-append"``).

    Returns:
        The tuple of outputs the hook feeds.

    Raises:
        KeyError: If ``hook_id`` is not a capture-critical id in
            ``HOOK_OUTPUTS``.
    """
    return HOOK_OUTPUTS[hook_id]


# ---------------------------------------------------------------------------
# Decision assembly
# ---------------------------------------------------------------------------


def build_reminder(missing_ids: list[str]) -> ReminderPlan:
    """Assemble the decision the steering renders at a completion boundary.

    For an empty ``missing_ids`` the plan is a silent no-op (nothing missing);
    otherwise it is a recurring, overridable Soft_Block (never a
    Mandatory_Gate) that names one ``MissingHook`` per id — each with the
    output(s) it feeds — and carries the two canonical install options. The
    ``missing`` list is sorted by hook id for a stable, deterministic plan.

    Args:
        missing_ids: The capture-critical ids whose hook file is absent.

    Returns:
        A :class:`ReminderPlan`: ``is_noop`` true / ``is_soft_block`` false with
        an empty ``missing`` when nothing is missing; otherwise ``is_noop``
        false / ``is_soft_block`` true with one :class:`MissingHook` per id
        (sorted by id) and the two canonical install options.
    """
    if not missing_ids:
        return ReminderPlan(
            missing=[],
            install_options=INSTALL_OPTIONS,
            is_noop=True,
            is_soft_block=False,
        )

    missing = [
        MissingHook(hook_id=hook_id, outputs=outputs_for_hook(hook_id))
        for hook_id in sorted(missing_ids)
    ]
    return ReminderPlan(
        missing=missing,
        install_options=INSTALL_OPTIONS,
        is_noop=False,
        is_soft_block=True,
    )


def should_reprompt(missing_ids: list[str], progress: dict) -> bool:
    """Return whether the reminder should re-present at this boundary.

    Returns ``True`` whenever ``missing_ids`` is non-empty, independent of any
    acknowledgment recorded in ``progress``. An acknowledgment authorizes the
    current module transition but never suppresses a future reminder, so a hook
    that stays missing is re-flagged at every subsequent boundary and progress
    is never permanently blocked.

    Args:
        missing_ids: The capture-critical ids whose hook file is absent.
        progress: The ``config/bootcamp_progress.json`` mapping (including any
            prior acknowledgment history); not consulted for suppression.

    Returns:
        ``True`` when any capture-critical hook is missing, else ``False``.
    """
    return bool(missing_ids)


# ---------------------------------------------------------------------------
# Acknowledgment recording
# ---------------------------------------------------------------------------


def record_acknowledgment(
    progress_path: Path, module: int, missing_ids: list[str]
) -> dict:
    """Append an explicit-override acknowledgment to the progress mapping.

    Reads ``config/bootcamp_progress.json`` (starting from an empty mapping when
    the file is missing or unreadable), appends exactly one acknowledgment entry
    — the module number, the sorted acknowledged ids, and an ISO-8601 timestamp —
    to the ``capture_hook_safeguard.acknowledgments`` list, writes the updated
    mapping back to ``progress_path``, and returns it. All pre-existing progress
    keys and values are preserved unchanged. The entry is an append-only audit
    trail that authorizes the current module transition; it is never consulted by
    :func:`should_reprompt` for suppression.

    Args:
        progress_path: Path to ``config/bootcamp_progress.json``.
        module: The module number reaching its completion boundary.
        missing_ids: The capture-critical ids the bootcamper acknowledged as
            missing (recorded sorted).

    Returns:
        The updated progress mapping (with the new acknowledgment appended).
    """
    try:
        with progress_path.open(encoding="utf-8") as handle:
            progress = json.load(handle)
        if not isinstance(progress, dict):
            progress = {}
    except (OSError, ValueError):
        # Missing or unreadable/malformed file — start from an empty mapping.
        progress = {}

    safeguard = progress.get("capture_hook_safeguard")
    if not isinstance(safeguard, dict):
        safeguard = {}
        progress["capture_hook_safeguard"] = safeguard

    acknowledgments = safeguard.get("acknowledgments")
    if not isinstance(acknowledgments, list):
        acknowledgments = []
        safeguard["acknowledgments"] = acknowledgments

    acknowledgments.append(
        {
            "module": module,
            "acknowledged": sorted(missing_ids),
            "timestamp": datetime.now().astimezone().isoformat(),
        }
    )

    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with progress_path.open("w", encoding="utf-8") as handle:
        json.dump(progress, handle, indent=2)
        handle.write("\n")

    return progress


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Name of the pending-question sentinel, resolved relative to the progress
# file's directory (``config/``) so a custom ``--progress`` tracks with it.
QUESTION_PENDING_NAME = ".question_pending"


def render_plan(plan: ReminderPlan) -> str:
    """Render a Soft_Block reminder for a non-no-op plan.

    Names each missing capture-critical hook and the output(s) it feeds, then
    lists the two canonical install options and the always-available continue
    path. A no-op plan renders to the empty string (the caller prints nothing).

    Args:
        plan: The :class:`ReminderPlan` produced by :func:`build_reminder`.

    Returns:
        The multi-line reminder text, or ``""`` when ``plan.is_noop`` is true.
    """
    if plan.is_noop:
        return ""

    lines = [
        "Capture-critical hook(s) missing — session deliverables will degrade "
        "while they stay absent:",
        "",
    ]
    for hook in plan.missing:
        outputs = ", ".join(hook.outputs)
        lines.append(f"  - {hook.hook_id} -> feeds: {outputs}")
    lines.extend(
        [
            "",
            "Install options (choose one, or explicitly continue):",
            f"  1. {plan.install_options[0]}",
            f"  2. {plan.install_options[1]}",
        ]
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on a clean run/no-op, 1 on an internally handled
        error path).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Detect absent capture-critical hooks at a module-completion "
            "boundary and render a recurring, overridable Soft_Block reminder."
        ),
    )
    parser.add_argument(
        "--hooks-dir",
        type=Path,
        default=DEFAULT_HOOKS_DIR,
        help=f"Path to the bootcamper's .kiro/hooks directory "
        f"(default: {DEFAULT_HOOKS_DIR}).",
    )
    parser.add_argument(
        "--progress",
        type=Path,
        default=DEFAULT_PROGRESS,
        help=f"Path to config/bootcamp_progress.json (default: {DEFAULT_PROGRESS}).",
    )
    parser.add_argument(
        "--record-ack",
        action="store_true",
        help="Record an explicit-override acknowledgment and allow the transition.",
    )
    parser.add_argument(
        "--module",
        type=int,
        default=None,
        metavar="N",
        help="The module number reaching its completion boundary.",
    )

    args = parser.parse_args(argv)

    try:
        # Defer to ask-bootcamper when a question is already pending, exactly as
        # the artifact steps do — the safeguard produces no output at this
        # boundary.
        question_pending = args.progress.parent / QUESTION_PENDING_NAME
        if question_pending.exists():
            return 0

        missing_ids = detect_missing_capture_hooks(args.hooks_dir)
        plan = build_reminder(missing_ids)

        if args.record_ack:
            # Explicit-override continue path: record the acknowledgment (only
            # meaningful when something is missing) and allow the transition.
            if missing_ids:
                record_acknowledgment(args.progress, args.module or 0, missing_ids)
            return 0

        # Detection/render path: print the Soft_Block reminder, or nothing when
        # all three capture-critical hooks are present (silent no-op).
        if not plan.is_noop:
            print(render_plan(plan))
        return 0
    except Exception as exc:  # noqa: BLE001 — non-blocking by contract
        # Any failure (missing/unreadable hooks dir, progress read/write error,
        # or an unexpected error) warns to stderr and returns without raising,
        # so the completion flow is never blocked.
        print(f"capture_hook_safeguard: warning: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
