#!/usr/bin/env python3
"""Senzing Bootcamp - Module 4 Record-Count License Back-fill.

A stdlib-only, pure, non-blocking helper that Module 4 runs after data
collection. It infers the real record total (the Collected_Count) from the
collected registry (``config/data_sources.yaml``), compares it against the
built-in 500-record evaluation limit, reads the Module-1 license state from
``config/bootcamp_preferences.yaml``, and decides whether to surface the
*existing* Module 1 Steps 6b-6e license guidance.

Guidance wording is delegated verbatim to the canonical
``volume_utils.build_license_framing``; markers are updated through the
existing ``preferences_utils`` writer -- no parallel flow, no new preference
key, no re-authored license text. Only counts and source names ever leave the
helper -- never row content or PII.

Usage:
    # Decide from the canonical registry/preferences and emit JSON on stdout:
    python record_count_backfill.py

    # Resolve unknown counts by row-counting collected files:
    python record_count_backfill.py --row-count

    # Point at explicit config paths:
    python record_count_backfill.py \\
        --registry config/data_sources.yaml \\
        --preferences config/bootcamp_preferences.yaml \\
        --progress config/bootcamp_progress.json

The command always exits 0 (non-blocking): on any unreadable or malformed
input it warns to stderr and emits a ``computable=false`` decision so Module 4
falls back to the existing Prose_Count behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path insertion so sibling scripts import cleanly (scripts are not a
# package). Mirrors the repo convention used across senzing-bootcamp/scripts.
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import data_sources  # noqa: E402  (path manipulated above)
import preferences_utils  # noqa: E402  (path manipulated above)
import progress_utils  # noqa: E402  (path manipulated above)
import volume_utils  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Built-in evaluation-license limit; mirrors the exclusive upper bound of
# volume_utils.TIER_BOUNDARIES[TIER_DEMO] (0, 500). "Exceeds" means strictly
# greater than 500, so exactly 500 records is NOT over the limit.
EVALUATION_LIMIT: int = 500

# Canonical config paths (relative to the workspace root), used as CLI defaults.
DEFAULT_REGISTRY_PATH: str = "config/data_sources.yaml"
DEFAULT_PREFERENCES_PATH: str = "config/bootcamp_preferences.yaml"
DEFAULT_PROGRESS_PATH: str = "config/bootcamp_progress.json"

# The new Module 4 step this helper checkpoints under.
DEFAULT_STEP_NUMBER: int = 8

# Module number whose progress this back-fill checkpoints (Module 4).
MODULE_NUMBER: int = 4


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Module1GuidanceState(str, Enum):
    """How Module 1 left the license question, read from preferences."""

    DELIVERED = "delivered"   # a license was applied (Step 6c) -> already guided
    DEFERRED = "deferred"     # license_guidance_deferred: true (Step 6e)
    SKIPPED = "skipped"       # Steps 6b-6e never ran (prose count <= limit)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceCount:
    """One source's contribution to the Collected_Count."""

    name: str                    # DATA_SOURCE name only (never row content)
    count: int | None            # resolved record count, or None when unknown
    counted_from: str            # "metadata" | "row_count" | "unknown"


@dataclass(frozen=True)
class CollectedCount:
    """The record total inferred from collected files (Req 1.1, 1.2)."""

    known_total: int             # sum of resolved counts only
    sources: list[SourceCount]   # per-source breakdown, source names + counts only
    unknown_sources: list[str]   # names of sources with no resolvable count

    @property
    def is_complete(self) -> bool:
        """True when every source has a resolved count (no unknowns)."""
        return not self.unknown_sources


@dataclass(frozen=True)
class LimitComparison:
    """Result of comparing a Collected_Count against the Evaluation_Limit."""

    over_limit: bool             # known_total > limit
    certain: bool                # False only when <= limit but unknowns remain


@dataclass(frozen=True)
class BackfillDecision:
    """The decision the Module 4 steering renders."""

    collected: CollectedCount
    module1_state: Module1GuidanceState
    over_limit: bool
    certain: bool
    already_guided: bool         # module1_state is DELIVERED (Req 2.2)
    present_guidance: bool       # surface Steps 6b-6e now? (Req 2.1, 2.3)
    computable: bool             # False -> warn + fall back to Prose_Count (Req 4.1)
    reason: str                  # human-readable explanation (counts + names only)


# ---------------------------------------------------------------------------
# Counting functions
# ---------------------------------------------------------------------------


def count_file_rows(file_path: str, fmt: str) -> int | None:
    """Count records in a collected file via a line tally (no PII retained).

    Counts records without loading field values into memory: for ``csv`` the
    tally is the number of non-empty lines minus one header line (floored at
    zero); for ``jsonl`` it is the number of non-empty lines. Every other
    format is treated as not cheaply countable and yields ``None``. Any
    ``OSError`` (missing/unreadable file) or decode error also yields ``None``.
    This function never raises.

    Args:
        file_path: Path to the collected file to tally.
        fmt: The source's declared format (e.g. ``csv``, ``jsonl``, ``json``).

    Returns:
        The record count, or ``None`` when the format is not cheaply countable
        or the file cannot be read/decoded.
    """
    normalized = fmt.strip().lower() if fmt else ""
    if normalized not in ("csv", "jsonl"):
        return None

    if not file_path:
        return None

    try:
        line_count = 0
        with open(file_path, encoding="utf-8") as handle:
            for line in handle:
                # Tally only; never retain the line's field values.
                if line.strip():
                    line_count += 1
    except (OSError, UnicodeDecodeError):
        return None

    if normalized == "csv":
        # Subtract one header line; never report a negative count.
        return max(0, line_count - 1)
    return line_count


def compute_collected_count(
    registry: data_sources.Registry,
    *,
    row_count: bool = False,
    workspace_root: str | None = None,
) -> CollectedCount:
    """Build the per-source Collected_Count breakdown from the registry.

    Reads only ``name``, ``record_count``, ``file_path``, and ``format`` from
    each entry (no PII -- Requirement 4.2). A source with a non-null
    ``record_count`` is counted with ``counted_from="metadata"``. A source with
    a null ``record_count`` is ``"unknown"`` unless ``row_count`` is enabled and
    :func:`count_file_rows` resolves it, in which case it is counted with
    ``counted_from="row_count"``. ``known_total`` sums only resolved counts;
    unknown sources are listed by name and never treated as zero
    (Requirement 1.2).

    Args:
        registry: The parsed data source registry.
        row_count: When ``True``, resolve unknown counts by row-counting the
            collected file via :func:`count_file_rows`.
        workspace_root: When provided, relative ``file_path`` values are
            resolved against this root before row-counting.

    Returns:
        A :class:`CollectedCount` with the per-source breakdown, the resolved
        ``known_total``, and the names of any unresolved sources.
    """
    sources: list[SourceCount] = []
    unknown_sources: list[str] = []
    known_total = 0

    for entry in registry.sources:
        name = entry.name
        record_count = entry.record_count

        if record_count is not None:
            known_total += record_count
            sources.append(SourceCount(name=name, count=record_count, counted_from="metadata"))
            continue

        resolved: int | None = None
        if row_count and entry.file_path:
            resolved = count_file_rows(_resolve_path(entry.file_path, workspace_root), entry.format)

        if resolved is not None:
            known_total += resolved
            sources.append(SourceCount(name=name, count=resolved, counted_from="row_count"))
        else:
            unknown_sources.append(name)
            sources.append(SourceCount(name=name, count=None, counted_from="unknown"))

    return CollectedCount(
        known_total=known_total,
        sources=sources,
        unknown_sources=unknown_sources,
    )


def _resolve_path(file_path: str, workspace_root: str | None) -> str:
    """Resolve a registry ``file_path`` against an optional workspace root.

    Absolute paths are returned unchanged; relative paths are joined onto
    ``workspace_root`` when one is provided.

    Args:
        file_path: The source's declared file path.
        workspace_root: Optional root directory for relative paths.

    Returns:
        The path to open when row-counting.
    """
    if workspace_root and not os.path.isabs(file_path):
        return os.path.join(workspace_root, file_path)
    return file_path


# ---------------------------------------------------------------------------
# State classification and limit comparison
# ---------------------------------------------------------------------------


def classify_module1_state(preferences: dict) -> Module1GuidanceState:
    """Classify how Module 1 left the license question, from preferences.

    Reads the same markers the Module 1 flow uses (no new key). ``DELIVERED``
    takes precedence: when ``license`` is set (a non-empty/truthy value, i.e.
    Step 6c applied a license) the state is ``DELIVERED`` regardless of the
    deferral marker. Otherwise, when ``license_guidance_deferred`` is truthy
    (Step 6e), the state is ``DEFERRED``. When neither marker is present the
    state is ``SKIPPED`` (Steps 6b-6e never ran). Missing keys are handled
    gracefully.

    Args:
        preferences: The loaded preferences mapping (may lack either key).

    Returns:
        The :class:`Module1GuidanceState` implied by the markers.
    """
    if preferences.get("license"):
        return Module1GuidanceState.DELIVERED
    if preferences.get("license_guidance_deferred"):
        return Module1GuidanceState.DEFERRED
    return Module1GuidanceState.SKIPPED


def compare_to_limit(
    collected: CollectedCount,
    limit: int = EVALUATION_LIMIT,
) -> LimitComparison:
    """Compare a Collected_Count against the Evaluation_Limit.

    ``over_limit`` is ``True`` when the resolved ``known_total`` strictly
    exceeds ``limit`` (so exactly ``limit`` records is not over -- Req 2.3).
    ``certain`` is ``True`` when the result is determinate: either the count
    is already over the limit (unknown sources can only add records, so the
    verdict cannot change) or every source has a resolved count. It is ``False``
    only when ``known_total <= limit`` but unknown sources remain, meaning the
    true total could still exceed the limit.

    Args:
        collected: The per-source Collected_Count breakdown.
        limit: The evaluation limit to compare against (default
            :data:`EVALUATION_LIMIT`).

    Returns:
        A :class:`LimitComparison` with the ``over_limit`` and ``certain`` flags.
    """
    over_limit = collected.known_total > limit
    certain = over_limit or collected.is_complete
    return LimitComparison(over_limit=over_limit, certain=certain)


# ---------------------------------------------------------------------------
# Back-fill decision
# ---------------------------------------------------------------------------


def decide_backfill(
    collected: CollectedCount,
    module1_state: Module1GuidanceState,
    limit: int = EVALUATION_LIMIT,
    *,
    computable: bool = True,
) -> BackfillDecision:
    """Decide whether to surface the existing Module 1 license guidance now.

    Combines the limit comparison with the Module-1 license state into the
    core rule: ``present_guidance`` is ``True`` **iff** the input is
    ``computable`` **and** the count certainly exceeds the limit (``over_limit``
    and ``certain``) **and** Module 1 left the license question ``SKIPPED`` or
    ``DEFERRED``. Guidance is never re-presented when Module 1 already
    ``DELIVERED`` a license (``already_guided`` -- Req 2.2), never presented at
    or below the limit including exactly ``limit`` (Req 2.3), and never
    presented while the count is indeterminate (not ``certain``). The ``reason``
    is human-readable but carries only counts and source names -- never row
    content or PII (Req 4.2).

    Args:
        collected: The per-source Collected_Count breakdown.
        module1_state: How Module 1 left the license question.
        limit: The evaluation limit to compare against (default
            :data:`EVALUATION_LIMIT`).
        computable: ``False`` when the inputs could not be read/parsed, forcing
            ``present_guidance`` to ``False`` so Module 4 falls back to
            Prose_Count behavior (Req 4.1).

    Returns:
        A :class:`BackfillDecision` capturing the comparison, the Module-1
        state, and the present/suppress verdict with a PII-free reason.
    """
    comparison = compare_to_limit(collected, limit)
    over_limit = comparison.over_limit
    certain = comparison.certain

    already_guided = module1_state is Module1GuidanceState.DELIVERED
    present_guidance = (
        computable
        and over_limit
        and certain
        and module1_state in (Module1GuidanceState.SKIPPED, Module1GuidanceState.DEFERRED)
    )

    reason = _build_reason(
        collected=collected,
        module1_state=module1_state,
        limit=limit,
        over_limit=over_limit,
        certain=certain,
        already_guided=already_guided,
        present_guidance=present_guidance,
        computable=computable,
    )

    return BackfillDecision(
        collected=collected,
        module1_state=module1_state,
        over_limit=over_limit,
        certain=certain,
        already_guided=already_guided,
        present_guidance=present_guidance,
        computable=computable,
        reason=reason,
    )


def _build_reason(
    *,
    collected: CollectedCount,
    module1_state: Module1GuidanceState,
    limit: int,
    over_limit: bool,
    certain: bool,
    already_guided: bool,
    present_guidance: bool,
    computable: bool,
) -> str:
    """Build a PII-free, human-readable explanation of the decision.

    The message references only the resolved count, the limit, the count of
    unknown sources and their names, and the Module-1 state -- never any row
    content or field value (Req 4.2).

    Args:
        collected: The per-source Collected_Count breakdown.
        module1_state: How Module 1 left the license question.
        limit: The evaluation limit compared against.
        over_limit: Whether ``known_total`` strictly exceeds ``limit``.
        certain: Whether the verdict is determinate.
        already_guided: Whether Module 1 already delivered a license.
        present_guidance: The present/suppress verdict.
        computable: Whether the inputs were readable/parseable.

    Returns:
        A one-line explanation containing only counts and source names.
    """
    if not computable:
        return (
            "Collected_Count could not be computed from the registry; "
            "falling back to Prose_Count behavior."
        )

    unknown_count = len(collected.unknown_sources)
    total_desc = f"known total {collected.known_total} vs limit {limit}"
    if unknown_count:
        unknown_names = ", ".join(collected.unknown_sources)
        unknown_desc = f" with {unknown_count} unknown source(s): {unknown_names}"
    else:
        unknown_desc = " with all sources counted"

    if present_guidance:
        return (
            f"Collected_Count exceeds the limit ({total_desc}){unknown_desc}; "
            f"Module 1 state is {module1_state.value}, so presenting license guidance."
        )
    if already_guided:
        return (
            f"Module 1 already delivered license guidance ({total_desc}){unknown_desc}; "
            "not re-presenting."
        )
    if not over_limit and not certain:
        return (
            f"Collected_Count is at or below the limit but indeterminate ({total_desc})"
            f"{unknown_desc}; not presenting guidance."
        )
    if not over_limit:
        return (
            f"Collected_Count is at or below the limit ({total_desc}){unknown_desc}; "
            "not presenting guidance."
        )
    return (
        f"Collected_Count exceeds the limit ({total_desc}){unknown_desc}, "
        f"but Module 1 state is {module1_state.value}; not presenting guidance."
    )


# ---------------------------------------------------------------------------
# Guidance rendering
# ---------------------------------------------------------------------------


def render_backfill_guidance(
    decision: BackfillDecision,
    ctx: volume_utils.LicenseFramingContext,
) -> str | None:
    """Render the license guidance for a decision using the canonical framing.

    Delegates wording verbatim to :func:`volume_utils.build_license_framing`,
    adding no new license text. When ``decision.present_guidance`` is ``True``
    every field of ``ctx`` is passed straight through as a keyword argument, so
    the returned string is identical to calling ``build_license_framing`` with
    the same context (Req 3.1, 3.2). Returns ``None`` when guidance is not being
    presented.

    Args:
        decision: The back-fill decision whose ``present_guidance`` flag
            controls whether guidance is rendered.
        ctx: The license framing context gathered by the agent (MCP facts and
            known bootcamp state).

    Returns:
        The canonical framing text when ``decision.present_guidance`` is
        ``True``; otherwise ``None``.
    """
    if not decision.present_guidance:
        return None

    return volume_utils.build_license_framing(
        capacity=ctx.capacity,
        validity=ctx.validity,
        submit_feedback_available=ctx.submit_feedback_available,
        has_existing_license=ctx.has_existing_license,
        mention_downsizing=ctx.mention_downsizing,
    )


# ---------------------------------------------------------------------------
# Marker updates (mirrors the Module 1 license flow)
# ---------------------------------------------------------------------------


def apply_guidance_markers(
    decision: BackfillDecision,
    *,
    preferences_path: str,
    progress_path: str,
    step_number: int,
) -> None:
    """Update the Module 1 license markers and checkpoint the Step 8a progress.

    Called after the Module 4 steering has surfaced the reused Steps 6b-6e
    guidance and the bootcamper has acted on it. It mirrors what Module 1 does
    -- once guidance is delivered/acted on the deferral is no longer pending --
    by clearing the **existing** ``license_guidance_deferred`` marker through
    the canonical :func:`preferences_utils.write_preference` writer (no new
    preference key is introduced). It does **not** invent a ``license`` value:
    the agent records the actual license via the normal flow when one is
    applied. It then writes the Step 8a checkpoint to ``bootcamp_progress.json``.

    The operation is idempotent: clearing an already-absent marker leaves the
    preferences file byte-identical, and the checkpoint write is skipped when
    the Step 8a checkpoint is already recorded, so a second call leaves both
    files byte-identical to their post-first-run state (Requirement 3.3). It is
    non-blocking: preference-write failures surface as a warning via the writer
    result and progress-write failures are caught and warned to stderr -- this
    function never raises. Only markers, the step number, and counts/source
    names ever leave the helper (no PII -- Requirement 4.2).

    When ``decision.present_guidance`` is ``False`` this is a no-op: no marker
    is touched and no checkpoint is written.

    Args:
        decision: The back-fill decision; markers are updated only when
            ``present_guidance`` is ``True``.
        preferences_path: Path to ``bootcamp_preferences.yaml``.
        progress_path: Path to ``bootcamp_progress.json``.
        step_number: The Module 4 step number this back-fill checkpoints under
            (the checkpoint is recorded as ``"<step_number>a"``, e.g. ``"8a"``).
    """
    if not decision.present_guidance:
        return

    _clear_deferral_marker(preferences_path)
    _write_backfill_checkpoint(progress_path, step_number)


def _clear_deferral_marker(preferences_path: str) -> None:
    """Clear the ``license_guidance_deferred`` marker via the canonical writer.

    Deletes the existing ``license_guidance_deferred`` key (value ``None``
    removes it) to reflect that guidance was surfaced and is no longer silently
    deferred. Reuses :func:`preferences_utils.write_preference`, which validates
    the key, writes atomically, and returns a :class:`preferences_utils.WriteResult`
    rather than raising. Deleting an already-absent key yields byte-identical
    output, so repeated calls are idempotent. A write failure is warned, not
    raised (non-blocking contract).

    Args:
        preferences_path: Path to ``bootcamp_preferences.yaml``.
    """
    result = preferences_utils.write_preference(
        "license_guidance_deferred",
        None,
        preferences_path=preferences_path,
    )
    if not result.success:
        _warn(f"could not clear license_guidance_deferred marker: {result.error}")


def _write_backfill_checkpoint(progress_path: str, step_number: int) -> None:
    """Write the Step 8a checkpoint to the progress file, idempotently.

    Records the checkpoint as ``"<step_number>a"`` (e.g. ``"8a"``) under the
    Module 4 ``step_history`` entry using the canonical
    :func:`progress_utils.write_checkpoint` writer. The write is skipped when
    the checkpoint is already recorded (``current_step`` and the Module 4
    ``last_completed_step`` both already equal the step key), so a second call
    leaves the file byte-identical to its post-first-run state. Read or write
    failures (missing/unreadable/malformed file, unwritable path) are caught and
    warned to stderr -- this function never raises (non-blocking contract).

    Args:
        progress_path: Path to ``bootcamp_progress.json``.
        step_number: The Module 4 step number; the checkpoint key is
            ``"<step_number>a"``.
    """
    step_key = f"{step_number}a"

    try:
        data: dict = {}
        path = Path(progress_path)
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if content.strip():
                data = json.loads(content)
    except (OSError, ValueError) as exc:
        _warn(f"could not read progress file '{progress_path}': {exc}")
        return

    history = data.get("step_history")
    module_entry = history.get(str(MODULE_NUMBER)) if isinstance(history, dict) else None
    already_checkpointed = (
        data.get("current_step") == step_key
        and isinstance(module_entry, dict)
        and module_entry.get("last_completed_step") == step_key
    )
    if already_checkpointed:
        return

    try:
        progress_utils.write_checkpoint(MODULE_NUMBER, step_key, progress_path=progress_path)
    except OSError as exc:
        _warn(f"could not write Step {step_key} checkpoint to '{progress_path}': {exc}")


def _warn(message: str) -> None:
    """Print a non-blocking warning to stderr.

    Args:
        message: The warning text (counts and source/marker names only -- no
            PII).
    """
    print(f"record_count_backfill: warning: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# JSON serialization (counts and source names only -- never row content/PII)
# ---------------------------------------------------------------------------


def _decision_to_json(decision: BackfillDecision) -> dict:
    """Serialize a decision into a machine-readable, PII-free mapping.

    Emits only counts, source names, the derived verdict flags, the Module-1
    state value, and the human-readable reason. Never includes ``file_path``
    values, row content, or any field value from the collected data
    (Requirement 4.2).

    Args:
        decision: The back-fill decision to serialize.

    Returns:
        A JSON-serializable dict with a stable structure.
    """
    return {
        "computable": decision.computable,
        "known_total": decision.collected.known_total,
        "sources": [
            {"name": src.name, "count": src.count, "counted_from": src.counted_from}
            for src in decision.collected.sources
        ],
        "unknown_sources": list(decision.collected.unknown_sources),
        "over_limit": decision.over_limit,
        "certain": decision.certain,
        "already_guided": decision.already_guided,
        "present_guidance": decision.present_guidance,
        "module1_state": decision.module1_state.value,
        "reason": decision.reason,
    }


def _uncomputable_decision() -> BackfillDecision:
    """Build the fallback ``computable=false`` decision.

    Uses an empty :class:`CollectedCount`, a ``SKIPPED`` Module-1 state, and
    ``computable=False`` so :func:`decide_backfill` yields ``present_guidance``
    ``False`` with a PII-free reason. This is the decision emitted when the
    registry is missing/unreadable/malformed or any unexpected error occurs, so
    Module 4 falls back to the existing Prose_Count behavior (Requirement 4.1).

    Returns:
        A :class:`BackfillDecision` with ``computable`` set to ``False``.
    """
    empty = CollectedCount(known_total=0, sources=[], unknown_sources=[])
    return decide_backfill(empty, Module1GuidanceState.SKIPPED, computable=False)


def _derive_workspace_root(registry_path: str) -> str | None:
    """Derive a workspace root for resolving relative registry ``file_path`` values.

    When the registry lives under a ``config/`` directory (the canonical
    ``config/data_sources.yaml`` layout), the workspace root is the parent of
    ``config/`` so relative paths like ``data/raw/...`` resolve correctly.
    Otherwise no root is assumed and ``None`` is returned (paths are used as-is).

    Args:
        registry_path: The path to the registry file.

    Returns:
        The absolute workspace root, or ``None`` when it cannot be inferred.
    """
    parent = os.path.dirname(os.path.abspath(registry_path))
    if os.path.basename(parent) == "config":
        return os.path.dirname(parent)
    return None


def _compute_decision(args: argparse.Namespace) -> BackfillDecision:
    """Read the registry and preferences, compute, and decide (may raise).

    Reads the registry file and parses it through the canonical data_sources
    reader chain (``parse_registry_yaml`` -> ``apply_migrations`` ->
    ``validate_registry`` -> ``_dict_to_registry``). A missing/unreadable
    registry or a validation failure raises, so the caller's top-level guard
    emits a ``computable=false`` decision. Preferences are read separately: a
    missing/malformed preferences file is *not* fatal -- it defaults the
    Module-1 state to ``SKIPPED`` while the registry stays computable (per the
    design's Error Handling table).

    Args:
        args: The parsed CLI arguments.

    Returns:
        The computed :class:`BackfillDecision` with ``computable=True``.

    Raises:
        OSError: If the registry file is missing or unreadable.
        ValueError: If the registry is malformed or schema-invalid.
    """
    registry_text = Path(args.registry).read_text(encoding="utf-8")

    raw = data_sources.parse_registry_yaml(registry_text)
    raw = data_sources.apply_migrations(raw)
    errors = data_sources.validate_registry(raw)
    if errors:
        raise ValueError(f"registry validation failed with {len(errors)} error(s)")
    registry = data_sources._dict_to_registry(raw)

    # Missing/malformed preferences must NOT make the result uncomputable:
    # default the Module-1 state to SKIPPED while the registry stays computable.
    load_result = preferences_utils.load_preferences(args.preferences)
    if load_result.error:
        _warn(
            f"could not read preferences '{args.preferences}' ({load_result.error}); "
            "defaulting Module 1 state to SKIPPED"
        )
    preferences = load_result.preferences if load_result.preferences is not None else {}

    workspace_root = _derive_workspace_root(args.registry)
    collected = compute_collected_count(
        registry,
        row_count=args.row_count,
        workspace_root=workspace_root,
    )
    module1_state = classify_module1_state(preferences)
    return decide_backfill(collected, module1_state, computable=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: read -> compute -> decide -> emit JSON on stdout.

    Reads the registry and preferences, computes the Collected_Count, decides
    whether to surface license guidance, and prints the :class:`BackfillDecision`
    as machine-readable JSON (counts and source names only -- never row content
    or PII) on stdout. The body is wrapped in a top-level guard: on any failure
    (missing/unreadable/malformed registry or preferences) it warns to stderr,
    emits a ``computable=false`` decision, and returns 0 so Module 4 falls back
    to the existing Prose_Count behavior (Requirements 2.1, 4.1, 4.2). Marker
    application is steering-driven and is deliberately not performed here.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (always 0 for the non-blocking contract).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Module 4 record-count license back-fill",
    )
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help=f"Path to the data source registry (default: {DEFAULT_REGISTRY_PATH})",
    )
    parser.add_argument(
        "--preferences",
        default=DEFAULT_PREFERENCES_PATH,
        help=f"Path to bootcamp preferences (default: {DEFAULT_PREFERENCES_PATH})",
    )
    parser.add_argument(
        "--progress",
        default=DEFAULT_PROGRESS_PATH,
        help=f"Path to bootcamp progress (default: {DEFAULT_PROGRESS_PATH})",
    )
    parser.add_argument(
        "--row-count",
        action="store_true",
        help="Resolve unknown record counts by row-counting collected files",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=DEFAULT_STEP_NUMBER,
        help=f"Module 4 step number for the checkpoint (default: {DEFAULT_STEP_NUMBER})",
    )
    args = parser.parse_args(argv)

    # Top-level guard: any failure reading/parsing the registry (or any
    # unexpected error) is non-blocking -- warn, emit a computable=false
    # decision, and return 0 so Module 4 falls back to Prose_Count behavior.
    try:
        decision = _compute_decision(args)
    except Exception as exc:  # noqa: BLE001 - non-blocking contract (Req 4.1)
        _warn(f"could not compute Collected_Count from '{args.registry}': {exc}")
        decision = _uncomputable_decision()

    print(json.dumps(_decision_to_json(decision)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
