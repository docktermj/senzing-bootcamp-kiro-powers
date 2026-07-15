#!/usr/bin/env python3
"""One-time migration transform: legacy ``*.kiro.hook`` -> Kiro 1.0 ``v1`` hooks.

This is the deterministic transform that converts the 30 shipped legacy
``senzing-bootcamp/hooks/*.kiro.hook`` files into the Kiro 1.0 hook model. It
classifies each legacy hook as manual (``userTriggered``) or non-manual and, for
the 27 non-manual hooks, emits a one-hook-per-file ``v1`` wrapper of the shape::

    {"version": "v1", "hooks": [{name, trigger, matcher?, action, timeout?}]}

The transform is the single consumer that wires together the two single-source
modules built earlier in the migration:

* :mod:`hook_matcher` (Task 1.1) — ``translate_scope`` derives the 1.0 ``matcher``
  regex from the legacy ``when`` block (file-path matcher from ``patterns``,
  tool-name matcher from ``toolTypes``, or ``None`` for unscoped triggers).
* :mod:`hook_renames` (Task 2.1) — ``TRIGGER_RENAMES`` / ``ACTION_RENAMES`` and
  the derived matcher-requirement classification (``matcher_kind``) rename the
  legacy trigger and action and say which triggers require a matcher.

Behavior preservation is verbatim: the hook ``name`` label and the action
``prompt`` / ``command`` payload are carried across byte-for-byte. The migration
changes only the envelope shape, never the policy content.

The three manual (``userTriggered``) hooks — ``backup-project-on-request``,
``git-commit-reminder``, ``commonmark-validation`` — have no 1.0 automatic
equivalent; they are reported as skipped here and converted to slash-command
steering files by a later task (Task 6). This transform never deletes the legacy
files (Task 15.1 does that) and, by default, writes nothing (Task 3.1 runs it
with ``--write`` to emit the committed 27 files).

Command timeout (resolved open detail, Req 1.6)
-----------------------------------------------
``session-log-events`` is the only ``runCommand`` hook and carries
``"timeout": 10`` in its legacy ``then`` block. The Kiro 1.0 hook schema models
``timeout`` as a **hook-level** field (a sibling of ``action``, not a key inside
the ``action`` object), defaulting to 60 seconds. Because the 1.0 schema *does*
support a command timeout, this transform preserves the legacy value by emitting
a hook-level ``"timeout": 10`` on the migrated command hook, keeping behavior
identical. See :data:`_LEGACY_TIMEOUT_FIELD` for the full decision note.

Only the Python standard library is used.

Usage:
    # Dry run (default): classify and report to stdout, write nothing.
    python3 senzing-bootcamp/scripts/migrate_hooks.py
    python3 senzing-bootcamp/scripts/migrate_hooks.py --json   # also dump v1 JSON

    # Emit the 27 v1 hooks/<id>.json files (used by Task 3.1).
    python3 senzing-bootcamp/scripts/migrate_hooks.py --write

    # Point at a different hooks directory / output directory.
    python3 senzing-bootcamp/scripts/migrate_hooks.py --hooks-dir DIR --write
    python3 senzing-bootcamp/scripts/migrate_hooks.py --output-dir DIR --write
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Allow importing sibling scripts (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from compose_hook_prompts import serialize_hook  # noqa: E402
from hook_matcher import GlobTranslationError, translate_scope  # noqa: E402
from hook_renames import (  # noqa: E402
    ACTION_RENAMES,
    MATCHER_KIND_UNSCOPED,
    TRIGGER_RENAMES,
    matcher_kind,
)

# ---------------------------------------------------------------------------
# Default paths (relative to the repository root, matching sibling generators)
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")

#: Legacy manual trigger. Kiro 1.0 removes it, so these hooks become
#: slash-command steering files (Task 6) rather than v1 hooks.
_LEGACY_MANUAL_TRIGGER = "userTriggered"

#: Legacy ``then`` key carrying a command execution timeout.
#:
#: Resolved open detail (Req 1.6): the Kiro 1.0 hook schema models ``timeout`` as
#: a hook-level field (a sibling of ``action``, ``trigger``, ``matcher`` and
#: ``name``), not a key nested inside the ``action`` object, and it defaults to
#: 60 seconds. Since the 1.0 schema *does* support a command timeout, this
#: transform preserves any legacy ``then.timeout`` by emitting an equivalent
#: hook-level ``timeout`` on the migrated hook (see :func:`migrate_hook`). Only
#: ``session-log-events`` carries a legacy timeout (10), so in practice this adds
#: exactly one hook-level ``timeout`` field; every other migrated hook keeps the
#: minimal ``name``/``trigger``/``matcher``/``action`` shape.
_LEGACY_TIMEOUT_FIELD = "timeout"

#: File suffix of a legacy hook file.
_LEGACY_SUFFIX = ".kiro.hook"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class MigrationError(Exception):
    """A legacy hook cannot be represented as a schema-valid V1 hook.

    Carries the owning hook id and the unsupported construct so the migration
    fails with a message naming both (Requirement 1.7).

    Attributes:
        hook_id: The id of the legacy hook that could not be migrated.
        construct: A short description of the unsupported construct.
    """

    def __init__(self, hook_id: str, construct: str) -> None:
        self.hook_id = hook_id
        self.construct = construct
        super().__init__(f"{hook_id}: {construct}")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LegacyHook:
    """A parsed legacy ``*.kiro.hook`` file.

    Attributes:
        hook_id: The hook id (filename without the ``.kiro.hook`` suffix).
        path: The source file path.
        data: The parsed JSON object.
    """

    hook_id: str
    path: Path
    data: dict


@dataclass(frozen=True)
class MigrationResult:
    """The outcome of migrating one non-manual legacy hook.

    Attributes:
        hook_id: The migrated hook id (unchanged from the legacy id).
        legacy_trigger: The legacy ``when.type`` value.
        trigger: The 1.0 trigger name.
        matcher: The 1.0 matcher regex, or ``None`` for an unscoped trigger.
        action_type: The 1.0 action type (``agent`` or ``command``).
        timeout: The preserved hook-level command timeout, or ``None``.
        wrapper: The full ``{"version": "v1", "hooks": [...]}`` object.
        serialized: The byte-stable serialized JSON text (with trailing newline).
    """

    hook_id: str
    legacy_trigger: str
    trigger: str
    matcher: str | None
    action_type: str
    timeout: int | None
    wrapper: dict
    serialized: str


# ---------------------------------------------------------------------------
# Discovery & parsing
# ---------------------------------------------------------------------------


def discover_legacy_hooks(hooks_dir: Path) -> list[LegacyHook]:
    """Read and parse every ``*.kiro.hook`` file in *hooks_dir*, sorted by id.

    Args:
        hooks_dir: Directory containing the legacy hook files.

    Returns:
        Parsed legacy hooks sorted by ``hook_id``.

    Raises:
        MigrationError: If a hook file contains invalid JSON.
    """
    hooks: list[LegacyHook] = []
    for path in sorted(hooks_dir.glob(f"*{_LEGACY_SUFFIX}")):
        hook_id = path.name[: -len(_LEGACY_SUFFIX)]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MigrationError(hook_id, f"invalid JSON — {exc}") from exc
        hooks.append(LegacyHook(hook_id=hook_id, path=path, data=data))
    return hooks


def is_manual(legacy: LegacyHook) -> bool:
    """Return True if *legacy* is a manual (``userTriggered``) hook.

    Args:
        legacy: The parsed legacy hook.

    Returns:
        True when the legacy trigger is ``userTriggered``.
    """
    return legacy.data.get("when", {}).get("type") == _LEGACY_MANUAL_TRIGGER


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------


def migrate_action(then: dict, hook_id: str) -> dict:
    """Rename a legacy ``then`` action block to a 1.0 ``action`` object.

    ``askAgent`` + ``prompt``  -> ``{"type": "agent", "prompt": <verbatim>}``
    ``runCommand`` + ``command`` -> ``{"type": "command", "command": <verbatim>}``

    The payload text (``prompt`` / ``command``) is carried across byte-for-byte
    (Req 1.4, 2.9, 2.10).

    Args:
        then: The legacy ``then`` block.
        hook_id: The owning hook id (for error messages).

    Returns:
        The 1.0 action object.

    Raises:
        MigrationError: If the action type is missing/unsupported or the payload
            field is absent.
    """
    legacy_type = then.get("type")
    if legacy_type is None:
        raise MigrationError(hook_id, "missing 'then.type'")

    rename = ACTION_RENAMES.get(legacy_type)
    if rename is None:
        raise MigrationError(
            hook_id, f"unsupported legacy action type {legacy_type!r}"
        )

    payload = then.get(rename.payload_field)
    if payload is None:
        raise MigrationError(
            hook_id,
            f"action {legacy_type!r} is missing its "
            f"{rename.payload_field!r} payload",
        )

    # Preserve the payload verbatim under its 1.0 key.
    return {"type": rename.v1_type, rename.payload_field: payload}


def migrate_hook(legacy: LegacyHook) -> MigrationResult:
    """Migrate one non-manual legacy hook to a v1 wrapper.

    Applies the trigger rename (:data:`hook_renames.TRIGGER_RENAMES`), derives
    the matcher (:func:`hook_matcher.translate_scope`), renames the action
    (:func:`migrate_action`), preserves the ``name`` verbatim, and assembles the
    ``{"version": "v1", "hooks": [entry]}`` wrapper. The ``matcher`` key is
    omitted for unscoped triggers (Req 3.4), and a legacy command ``timeout`` is
    preserved as a hook-level field (Req 1.6).

    Args:
        legacy: The parsed non-manual legacy hook.

    Returns:
        The migration result, including the serialized JSON.

    Raises:
        MigrationError: If the hook cannot be represented as a schema-valid V1
            hook (Req 1.7).
    """
    hook_id = legacy.hook_id
    data = legacy.data
    when = data.get("when", {})
    then = data.get("then", {})

    legacy_trigger = when.get("type")
    if legacy_trigger is None:
        raise MigrationError(hook_id, "missing 'when.type'")
    if legacy_trigger == _LEGACY_MANUAL_TRIGGER:
        # Manual hooks have no 1.0 automatic equivalent; the caller filters
        # these out before calling migrate_hook. Fail loudly if one slips in.
        raise MigrationError(
            hook_id,
            "manual 'userTriggered' trigger has no Kiro 1.0 automatic "
            "equivalent (convert to a slash-command steering file)",
        )

    trigger = TRIGGER_RENAMES.get(legacy_trigger)
    if trigger is None:
        raise MigrationError(
            hook_id, f"unsupported legacy trigger {legacy_trigger!r}"
        )

    name = data.get("name")
    if name is None:
        raise MigrationError(hook_id, "missing 'name'")

    action = migrate_action(then, hook_id)

    # Derive the matcher from the legacy scope. translate_scope compiles the
    # regex internally, so a returned matcher is guaranteed to compile.
    try:
        matcher = translate_scope(when)
    except GlobTranslationError as exc:
        raise MigrationError(
            hook_id, f"cannot translate scope to a 1.0 matcher — {exc}"
        ) from exc

    # Cross-check the matcher against what the 1.0 trigger requires so the
    # emitted hook is schema-valid (Req 1.7 / the matcher-when-required rule the
    # validator enforces in Req 6.2).
    kind = matcher_kind(trigger)
    if kind == MATCHER_KIND_UNSCOPED and matcher is not None:
        raise MigrationError(
            hook_id,
            f"trigger {trigger!r} is unscoped but the legacy 'when' block "
            "produced a matcher",
        )
    if kind != MATCHER_KIND_UNSCOPED and matcher is None:
        raise MigrationError(
            hook_id,
            f"trigger {trigger!r} requires a {kind} matcher but the legacy "
            "'when' block has no patterns or toolTypes",
        )

    # Assemble the v1 entry in the canonical key order:
    # name, trigger, matcher (when scoped), action, timeout (when present).
    entry: dict = {"name": name, "trigger": trigger}
    if matcher is not None:
        entry["matcher"] = matcher
    entry["action"] = action

    # Preserve a legacy command timeout as a hook-level field (see the module
    # docstring and _LEGACY_TIMEOUT_FIELD for the resolved-detail rationale).
    timeout = then.get(_LEGACY_TIMEOUT_FIELD)
    if timeout is not None:
        entry[_LEGACY_TIMEOUT_FIELD] = timeout

    wrapper = {"version": "v1", "hooks": [entry]}

    return MigrationResult(
        hook_id=hook_id,
        legacy_trigger=legacy_trigger,
        trigger=trigger,
        matcher=matcher,
        action_type=action["type"],
        timeout=timeout,
        wrapper=wrapper,
        serialized=serialize_hook(wrapper),
    )


@dataclass(frozen=True)
class MigrationPlan:
    """The full result of transforming a legacy hooks directory.

    Attributes:
        results: One :class:`MigrationResult` per non-manual hook (sorted by id).
        manual_ids: Ids of the manual hooks skipped (slash-command conversion).
        errors: :class:`MigrationError` instances for hooks that could not
            migrate (empty on success).
        total: Total number of legacy hook files discovered.
    """

    results: list[MigrationResult]
    manual_ids: list[str]
    errors: list[MigrationError]
    total: int


def build_migration_plan(hooks_dir: Path) -> MigrationPlan:
    """Classify and migrate every legacy hook in *hooks_dir*.

    Manual hooks are recorded as skipped; non-manual hooks are migrated,
    collecting any :class:`MigrationError` rather than aborting on the first one
    so the caller can report all problems at once.

    Args:
        hooks_dir: Directory containing the legacy hook files.

    Returns:
        The migration plan (results, skipped manual ids, and errors).

    Raises:
        MigrationError: If a legacy hook file contains invalid JSON (discovery).
    """
    legacy_hooks = discover_legacy_hooks(hooks_dir)

    results: list[MigrationResult] = []
    manual_ids: list[str] = []
    errors: list[MigrationError] = []

    for legacy in legacy_hooks:
        if is_manual(legacy):
            manual_ids.append(legacy.hook_id)
            continue
        try:
            results.append(migrate_hook(legacy))
        except MigrationError as exc:
            errors.append(exc)

    return MigrationPlan(
        results=results,
        manual_ids=sorted(manual_ids),
        errors=errors,
        total=len(legacy_hooks),
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_v1_hooks(results: list[MigrationResult], output_dir: Path) -> list[Path]:
    """Write each migration result to ``<output_dir>/<id>.json``.

    Args:
        results: The non-manual migration results.
        output_dir: Destination directory for the ``.json`` files.

    Returns:
        The written file paths, in the order of *results*.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for result in results:
        out_path = output_dir / f"{result.hook_id}.json"
        out_path.write_text(result.serialized, encoding="utf-8", newline="")
        written.append(out_path)
    return written


def _matcher_label(result: MigrationResult) -> str:
    """Return a short human-readable matcher descriptor for the dry-run report."""
    if result.matcher is None:
        return "matcher(none)"
    return f"matcher({matcher_kind(result.trigger)})"


def print_dry_run_report(plan: MigrationPlan, show_json: bool) -> None:
    """Print the dry-run classification report to stdout.

    Args:
        plan: The migration plan to report.
        show_json: When True, also print the full serialized v1 JSON per hook.
    """
    print(f"Legacy hooks discovered: {plan.total}")
    print(
        f"Manual (userTriggered) -> slash commands "
        f"({len(plan.manual_ids)}): " + ", ".join(plan.manual_ids)
    )
    print(f"Non-manual -> v1 ({len(plan.results)}):")

    id_width = max((len(r.hook_id) for r in plan.results), default=0)
    trig_width = max((len(r.legacy_trigger) for r in plan.results), default=0)
    for result in plan.results:
        timeout = (
            f"  timeout={result.timeout}" if result.timeout is not None else ""
        )
        print(
            f"  {result.hook_id.ljust(id_width)}  "
            f"{result.legacy_trigger.ljust(trig_width)} -> "
            f"{result.trigger.ljust(16)} "
            f"{_matcher_label(result)}"
            f"  action={result.action_type}{timeout}"
        )

    if show_json:
        print()
        for result in plan.results:
            print(f"----- {result.hook_id}.json -----")
            # serialized already ends with a trailing newline.
            sys.stdout.write(result.serialized)

    print(
        f"\nDry run: no files written. Re-run with --write to emit "
        f"{len(plan.results)} <id>.json files."
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry: classify and migrate legacy hooks to v1.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 on any migration error or missing directory.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Migrate legacy *.kiro.hook files to Kiro 1.0 v1 hook JSON. "
            "Dry run by default; use --write to emit files."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Emit <output-dir>/<id>.json for every non-manual hook.",
    )
    parser.add_argument(
        "--hooks-dir",
        type=Path,
        default=HOOKS_DIR,
        help=f"Legacy .kiro.hook input directory (default: {HOOKS_DIR}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for v1 .json files (default: --hooks-dir).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="In dry-run mode, also print the full v1 JSON for each hook.",
    )
    args = parser.parse_args(argv)

    hooks_dir: Path = args.hooks_dir
    output_dir: Path = args.output_dir if args.output_dir is not None else hooks_dir

    if not hooks_dir.is_dir():
        print(f"ERROR: hooks directory not found: {hooks_dir}", file=sys.stderr)
        return 1

    try:
        plan = build_migration_plan(hooks_dir)
    except MigrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Fail the whole migration if any hook could not be represented as valid V1
    # (Req 1.7). Report every offender; write nothing.
    if plan.errors:
        print(
            f"ERROR: {len(plan.errors)} hook(s) could not be migrated:",
            file=sys.stderr,
        )
        for err in plan.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.write:
        written = write_v1_hooks(plan.results, output_dir)
        for path in written:
            print(f"Wrote {path}")
        print(
            f"Migrated {len(written)} non-manual hook(s); "
            f"skipped {len(plan.manual_ids)} manual hook(s): "
            + ", ".join(plan.manual_ids)
        )
        return 0

    print_dry_run_report(plan, show_json=args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
