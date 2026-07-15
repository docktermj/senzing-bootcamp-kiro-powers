#!/usr/bin/env python3
"""Senzing Bootcamp - Module 4 SQLite Load-Time Warning helper.

A stdlib-only, non-blocking orchestration helper that Module 4 runs after the
record-count back-fill (Step 8a) and before the transition to Module 5. It owns
the pure logic behind the collection-time SQLite Load-Time Warning: the stable
load identity used to scope the decision, the sampling helpers, and the shared
``sqlite_volume_prompt`` decision-marker read/write plus the Module 6 scoping
check.

It reuses its siblings rather than re-implementing anything: the trigger
predicate and warning-text builder live in ``volume_utils``; the collected-count
computation lives in ``record_count_backfill``; the registry model and reader
chain live in ``data_sources``; and the decision marker is persisted through
``preferences_utils``. Only source names and counts ever leave this helper --
never row content or PII.

Usage:
    # Evaluate the warning for the canonical registry/preferences:
    python load_time_warning.py

    # Point at explicit config paths:
    python load_time_warning.py \\
        --registry config/data_sources.yaml \\
        --preferences config/bootcamp_preferences.yaml

Run as a CLI, ``main`` reads the registry and the active ``database_type``,
computes the collected total, and either prints the built Load_Time_Warning
(when the total strictly exceeds the threshold on SQLite) or a "no warning --
continue" report, plus the current shared decision-marker status. The CLI
diagnostic does not consult the MCP server (MCP retrieval is the steering's
job), so its timing figures are always reported unavailable. Every path is
non-blocking: any unreadable/malformed input, an uncomputable total, or an
indeterminate database type warns to stderr as needed, reports "continue", and
exits 0 -- mirroring ``record_count_backfill``'s contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass
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
import record_count_backfill  # noqa: E402  (path manipulated above)
import volume_utils  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical config paths (relative to the workspace root), used as CLI defaults.
DEFAULT_REGISTRY_PATH: str = "config/data_sources.yaml"
DEFAULT_PREFERENCES_PATH: str = "config/bootcamp_preferences.yaml"

# Literal used in the load-identity signature for a source with no record_count.
_UNKNOWN_COUNT: str = "unknown"


# ---------------------------------------------------------------------------
# Load identity
# ---------------------------------------------------------------------------


def compute_load_identity(registry: data_sources.Registry) -> str:
    """Compute a stable, order-independent identity for the collected load.

    Builds a signature from each source's ``(data_source, record_count)`` pair
    -- ``record_count`` rendered as its integer or the literal ``"unknown"`` --
    sorted by ``data_source``, then hashed with :func:`hashlib.sha256`. Only
    source names and counts ever enter the signature (no row content, no PII).

    The identity scopes the decision to "this load": both Module 4 (at
    collection) and Module 6 (at load) compute it from ``config/data_sources.yaml``.
    A genuinely different dataset yields a different identity (Requirement 6.4).

    Args:
        registry: The parsed data source registry.

    Returns:
        A ``"sha256:<hexdigest>"`` identity string. Deterministic and
        independent of source ordering; two registries with different
        source/count sets produce different identities (modulo hash collisions).
        Never raises, never performs I/O.
    """
    pairs: list[tuple[str, str]] = []
    for entry in registry.sources:
        count = entry.record_count
        count_repr = str(count) if count is not None else _UNKNOWN_COUNT
        pairs.append((str(entry.data_source), count_repr))

    # Sort by data_source so the signature is independent of source ordering.
    pairs.sort(key=lambda pair: pair[0])

    # Tab separates the name from the count and newline separates sources; both
    # are absent from DATA_SOURCE keys (^[A-Z][A-Z0-9_]*$) and integer/"unknown"
    # counts, so the joined form is unambiguous.
    signature = "\n".join(f"{name}\t{count}" for name, count in pairs)
    digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# ---------------------------------------------------------------------------
# Sampling helpers
# ---------------------------------------------------------------------------

# Sampling_Strategy vocabulary. ``first_n`` / ``random_n`` / ``er_demonstrating``
# map to the count-based and cluster-preserving selectors below; ``described``
# is the escape hatch for a bootcamper-described strategy the steering handles
# conversationally (Requirements 5.2, 5.3).
STRATEGY_FIRST_N: str = "first_n"
STRATEGY_RANDOM_N: str = "random_n"
STRATEGY_ER_DEMONSTRATING: str = "er_demonstrating"
STRATEGY_DESCRIBED: str = "described"
VALID_SAMPLING_STRATEGIES: tuple[str, ...] = (
    STRATEGY_FIRST_N,
    STRATEGY_RANDOM_N,
    STRATEGY_ER_DEMONSTRATING,
    STRATEGY_DESCRIBED,
)


@dataclass(frozen=True)
class SampleTargetValidation:
    """Result of validating a requested sampling target record count.

    Attributes:
        valid: True iff the requested target is a positive integer strictly
            below the collected record total.
        reason: A human-readable, PII-free explanation. Non-empty when
            ``valid`` is False so the steering can re-ask; empty when valid.
    """

    valid: bool
    reason: str


def validate_sample_target(
    target: int | None,
    collected_total: int | None,
) -> SampleTargetValidation:
    """Validate a requested sampling target record count.

    The target is valid iff it is a real ``int`` (not ``bool``) strictly greater
    than zero, ``collected_total`` is a real ``int``, and ``target`` is strictly
    less than ``collected_total``. Any other case is invalid with a
    human-readable, PII-free reason so the steering can re-ask for a valid
    target (Requirements 5.5, 5.6). Only record counts -- never row content --
    appear in the reason.

    Args:
        target: The requested sampling target record count, or None when the
            bootcamper has not supplied one.
        collected_total: The determinate Collected_Record_Total, or None when
            it cannot be computed.

    Returns:
        :class:`SampleTargetValidation` with ``valid`` and a ``reason``.
        ``reason`` is empty when valid and non-empty otherwise. Never raises,
        never performs I/O.
    """
    # target must be a real int (bool is an int subclass -- reject it).
    if not isinstance(target, int) or isinstance(target, bool):
        return SampleTargetValidation(
            valid=False,
            reason="Sampling target must be a whole number.",
        )

    if target <= 0:
        return SampleTargetValidation(
            valid=False,
            reason="Sampling target must be a positive number greater than zero.",
        )

    # collected_total must be a real int to compare against.
    if not isinstance(collected_total, int) or isinstance(collected_total, bool):
        return SampleTargetValidation(
            valid=False,
            reason=(
                "Collected record total is unavailable, so the sampling target "
                "cannot be validated."
            ),
        )

    if target >= collected_total:
        return SampleTargetValidation(
            valid=False,
            reason=(
                f"Sampling target must be less than the collected record total "
                f"({collected_total})."
            ),
        )

    return SampleTargetValidation(valid=True, reason="")


def select_first_n(total: int, target: int) -> list[int]:
    """Select the first N record indices from a collected dataset.

    Returns ``range(min(target, total))`` materialized as a list -- the first
    ``min(target, total)`` indices in ``[0, total)`` in ascending order. When
    ``target >= total`` every index is selected; when either argument is
    non-positive the selection is empty.

    Args:
        total: The Collected_Record_Total (number of available record indices).
        target: The requested sample size.

    Returns:
        A list of ``min(target, total)`` distinct indices in ``[0, total)``,
        ascending. Pure -- no global RNG state, never raises, never performs I/O.
    """
    return list(range(min(target, total)))


def select_random_n(total: int, target: int, seed: int) -> list[int]:
    """Select N distinct random record indices in ``[0, total)`` deterministically.

    Draws the sample from a fresh :class:`random.Random` seeded with ``seed`` so
    the selection is reproducible for a given ``seed`` and independent of any
    global RNG state. Returns ``min(target, total)`` distinct in-range indices.

    Args:
        total: The Collected_Record_Total (number of available record indices).
        target: The requested sample size.
        seed: The seed making the selection deterministic and reproducible.

    Returns:
        A list of ``min(target, total)`` distinct indices in ``[0, total)`` in
        the order produced by the seeded sampler. Pure -- no global RNG state,
        never raises for ``target >= 0``, never performs I/O.
    """
    count = max(0, min(target, total))
    return random.Random(seed).sample(range(total), count)


def select_er_demonstrating(
    clusters: list[list[int]],
    singletons: list[int],
    target: int,
    seed: int,
) -> list[int]:
    """Select records that preserve known match clusters (ER-demonstrating).

    Adds whole match clusters -- each cluster being a set of record indices that
    resolve together across sources -- until adding the next whole cluster would
    exceed ``target``, then fills the remaining budget from ``singletons``. A
    cluster is always included in full or excluded in full, never partially, so
    cross-source overlaps and known match clusters are preserved (Requirement
    5.7).

    The selection is deterministic given ``seed``: a single
    :class:`random.Random` seeded with ``seed`` shuffles the clusters (choosing
    which clusters fill the budget) and then the singletons, so the same inputs
    and seed always yield the same result independent of any global RNG state.

    Args:
        clusters: Match clusters, each a list of record indices that resolve
            together. Never mutated.
        singletons: Record indices that do not belong to any match cluster, used
            to fill any budget left after whole clusters are added. Never mutated.
        target: The requested sample size (records). Non-positive targets select
            no records.
        seed: The seed making the selection deterministic and reproducible.

    Returns:
        A list of the selected record indices: the members of every included
        cluster (in shuffled cluster order) followed by any filler singletons.
        Pure -- inputs are never mutated, no global RNG state, never raises.
    """
    rng = random.Random(seed)

    # Copy before shuffling so the caller's lists are never mutated (purity).
    cluster_order = list(clusters)
    rng.shuffle(cluster_order)

    selected: list[int] = []
    count = 0
    for cluster in cluster_order:
        size = len(cluster)
        # All-or-none: only take a cluster when the whole cluster fits the
        # remaining budget; stop as soon as the next whole cluster would exceed
        # target.
        if count + size <= target:
            selected.extend(cluster)
            count += size
        else:
            break

    # Fill any leftover budget from singletons.
    remaining = target - count
    if remaining > 0 and singletons:
        singleton_order = list(singletons)
        rng.shuffle(singleton_order)
        selected.extend(singleton_order[:remaining])

    return selected


# ---------------------------------------------------------------------------
# Sample I/O (writes only kept records under data/samples/ -- never raises)
# ---------------------------------------------------------------------------

# Filename of the sidecar written by write_sample_manifest alongside a sample.
SAMPLE_MANIFEST_NAME: str = "sample_manifest.json"

# Formats whose record boundaries are a single line, so they can be sampled by
# streaming line-by-line. Mirrors record_count_backfill.count_file_rows so the
# keep_indices index space (below) matches the counted record total exactly.
_SAMPLEABLE_FORMATS: tuple[str, ...] = ("csv", "jsonl")


@dataclass(frozen=True)
class SampleWriteResult:
    """Result of a sample-file or manifest write.

    Attributes:
        success: True when the write completed; False on any unreadable source,
            unwritable destination, or non-countable format.
        reason: A human-readable, PII-free explanation (counts, strategy, and
            the failure kind only -- never row content). Populated on both
            success and failure so the steering can surface it either way.
    """

    success: bool
    reason: str


def write_sample(
    source_path: str,
    dest_path: str,
    fmt: str,
    keep_indices: list[int],
) -> SampleWriteResult:
    """Write only the selected records from ``source_path`` to ``dest_path``.

    Streams the source file line-by-line -- never loading the whole file -- and
    writes only the kept records, mirroring the record-boundary model of
    :func:`record_count_backfill.count_file_rows` so the ``keep_indices`` index
    space matches the counted Collected_Record_Total exactly:

    - ``csv``: the first non-empty line is the header and is **always** written;
      the header is **excluded from the index space**. Subsequent non-empty
      lines are the data records, indexed 0-based, and a data record is written
      iff its index is in ``keep_indices``.
    - ``jsonl``: every non-empty line is a record, indexed 0-based over the
      non-empty lines (blank lines are skipped, consistent with
      ``count_file_rows``), and a line is written iff its index is in
      ``keep_indices``.

    Any other (non-countable) format, an unreadable source, or an unwritable
    destination yields ``success=False`` with a reason -- this function never
    raises, keeping the Module 4 flow non-blocking (Requirement 7.5).

    Args:
        source_path: Path to the collected source file to sample from.
        dest_path: Path to write the sample to (under ``data/samples/``).
        fmt: The source's declared format (``csv`` or ``jsonl`` are sampleable).
        keep_indices: 0-based data-record indices to keep (see the index-space
            note above). Order and duplicates do not matter; membership is what
            decides inclusion.

    Returns:
        A :class:`SampleWriteResult`. ``success`` is True only when the sample
        was written; the ``reason`` carries counts and the failure kind only
        (never row content). Never raises, streams to bound memory usage.
    """
    normalized = fmt.strip().lower() if fmt else ""
    if normalized not in _SAMPLEABLE_FORMATS:
        return SampleWriteResult(
            success=False,
            reason=(
                f"Format '{fmt}' cannot be sampled by streaming; only "
                f"{', '.join(_SAMPLEABLE_FORMATS)} are supported."
            ),
        )

    if not source_path:
        return SampleWriteResult(
            success=False,
            reason="No source file path was provided to sample from.",
        )
    if not dest_path:
        return SampleWriteResult(
            success=False,
            reason="No destination path was provided for the sample.",
        )

    keep = set(keep_indices)
    kept = 0

    try:
        dest = Path(dest_path)
        if dest.parent != Path(""):
            dest.parent.mkdir(parents=True, exist_ok=True)

        with open(source_path, encoding="utf-8") as src, open(
            dest_path, "w", encoding="utf-8", newline=""
        ) as out:
            data_index = 0
            header_pending = normalized == "csv"
            for line in src:
                # Skip blank lines so the index space matches count_file_rows'
                # non-empty-line tally.
                if not line.strip():
                    continue

                if header_pending:
                    # CSV header: always kept, excluded from the index space.
                    out.write(_ensure_newline(line))
                    header_pending = False
                    continue

                if data_index in keep:
                    out.write(_ensure_newline(line))
                    kept += 1
                data_index += 1
    except (OSError, UnicodeDecodeError) as exc:
        return SampleWriteResult(
            success=False,
            reason=f"Could not read the source or write the sample: {exc}",
        )

    return SampleWriteResult(
        success=True,
        reason=f"Wrote {kept} sampled record(s).",
    )


def _ensure_newline(line: str) -> str:
    """Return ``line`` guaranteed to end with a single newline.

    Source lines read in universal-newline mode already end with ``"\\n"``; a
    final line without a trailing newline gets one appended so every written
    record occupies its own line.

    Args:
        line: A line read from the source file.

    Returns:
        The line ending in exactly one ``"\\n"``.
    """
    return line if line.endswith("\n") else line + "\n"


def write_sample_manifest(
    dest_dir: str,
    strategy: str,
    target: int,
    kept: int,
) -> SampleWriteResult:
    """Write a small sidecar documenting the sample under ``data/samples/``.

    Records the chosen ``Sampling_Strategy``, the requested ``target`` record
    count, and the ``kept`` record count actually written (Requirement 5.4).
    Only counts and the strategy name are recorded -- never row content or PII.
    Written as JSON (``sample_manifest.json``) in ``dest_dir``.

    Any unwritable destination yields ``success=False`` with a reason -- this
    function never raises, keeping the flow non-blocking (Requirement 7.5).

    Args:
        dest_dir: Directory to write the manifest into (the sample's directory
            under ``data/samples/``).
        strategy: The Sampling_Strategy used (typically one of
            :data:`VALID_SAMPLING_STRATEGIES`; a described strategy is recorded
            as-is).
        target: The requested sample size.
        kept: The number of records actually written to the sample.

    Returns:
        A :class:`SampleWriteResult`. Never raises.
    """
    if not dest_dir:
        return SampleWriteResult(
            success=False,
            reason="No destination directory was provided for the sample manifest.",
        )

    payload = {"strategy": strategy, "target": target, "kept": kept}

    try:
        directory = Path(dest_dir)
        directory.mkdir(parents=True, exist_ok=True)
        manifest_path = directory / SAMPLE_MANIFEST_NAME
        manifest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError) as exc:
        return SampleWriteResult(
            success=False,
            reason=f"Could not write the sample manifest: {exc}",
        )

    return SampleWriteResult(
        success=True,
        reason=(
            f"Recorded sample manifest: strategy '{strategy}', target {target}, "
            f"kept {kept}."
        ),
    )


# ---------------------------------------------------------------------------
# Decision marker (shared sqlite_volume_prompt key -- never raises)
# ---------------------------------------------------------------------------

# Value of ``sqlite_volume_prompt.source`` written for a Module 4 decision, so
# the shared marker records which check recorded it (Module 4 vs Module 6). The
# key itself (``sqlite_volume_prompt``) is the same one the Module 6 Hard_Prompt
# uses -- this is the shared decision-marker mechanism, not a parallel store
# (Requirement 6.2).
LOAD_MARKER_SOURCE: str = "module4_load_time"

# Top-level preferences key that holds the shared decision marker.
_MARKER_KEY: str = "sqlite_volume_prompt"


def write_load_decision(
    choice: str,
    load_identity: str,
    preferences_path: str = DEFAULT_PREFERENCES_PATH,
) -> preferences_utils.WriteResult:
    """Record the Load_Decision_Marker via the shared ``sqlite_volume_prompt`` key.

    Writes ``{decided: true, choice, source: LOAD_MARKER_SOURCE, load_identity}``
    to the existing ``sqlite_volume_prompt`` marker through
    :func:`preferences_utils.write_preference` -- the same shared mechanism the
    Module 6 Hard_Prompt uses, not a parallel store (Requirements 6.1, 6.2).
    Only the chosen option and the identity of the load the decision applies to
    are recorded (no row content, no PII).

    Args:
        choice: The bootcamper's response -- one of ``"proceed"``, ``"sample"``,
            or ``"switch_db"``.
        load_identity: The :func:`compute_load_identity` signature of the load
            the decision applies to.
        preferences_path: Path to the bootcamp preferences YAML file.

    Returns:
        The writer's :class:`preferences_utils.WriteResult`. A write failure is
        reported via ``success=False`` so the Module 4 flow stays non-blocking
        (Requirement 7.5). Never raises.
    """
    marker = {
        "decided": True,
        "choice": choice,
        "source": LOAD_MARKER_SOURCE,
        "load_identity": load_identity,
    }
    try:
        return preferences_utils.write_preference(
            _MARKER_KEY, marker, preferences_path
        )
    except Exception as exc:  # noqa: BLE001 - non-blocking contract (Req 7.5)
        return preferences_utils.WriteResult(
            success=False,
            error=f"Could not record the load decision: {exc}",
        )


def read_load_decision(
    preferences_path: str = DEFAULT_PREFERENCES_PATH,
) -> dict | None:
    """Read the shared ``sqlite_volume_prompt`` decision marker.

    Reuses :func:`preferences_utils.load_preferences` (which parses via
    :func:`preferences_utils.parse_yaml`) and returns the marker dict, or
    ``None`` when the preferences file is absent, unreadable, malformed, or does
    not carry a ``sqlite_volume_prompt`` marker. Never raises, keeping the flow
    non-blocking (Requirement 7.5).

    Args:
        preferences_path: Path to the bootcamp preferences YAML file.

    Returns:
        The ``sqlite_volume_prompt`` marker dict, or ``None`` when it is absent
        or cannot be read.
    """
    try:
        result = preferences_utils.load_preferences(
            preferences_path, required_fields=()
        )
    except Exception:  # noqa: BLE001 - non-blocking contract (Req 7.5)
        return None

    preferences = result.preferences
    if not isinstance(preferences, dict):
        return None

    marker = preferences.get(_MARKER_KEY)
    return marker if isinstance(marker, dict) else None


def module4_decision_applies(
    marker: dict | None,
    current_identity: str,
    db_type: str | None,
) -> bool:
    """Whether a Module 4 Load_Decision applies to the current Module 6 load.

    Pure and side-effect free. Returns ``True`` iff ``marker`` is a decided
    Module 4 marker -- ``source == LOAD_MARKER_SOURCE`` and ``decided is True``
    -- whose ``load_identity`` equals ``current_identity`` AND ``db_type``
    normalizes (case-insensitive, whitespace-trimmed) to ``"sqlite"``.

    A different ``load_identity`` (a genuinely different load), a marker recorded
    by some other source (e.g. the Module 6 Hard_Prompt), an undecided marker, a
    missing/``None`` marker, or a non-SQLite database all yield ``False`` so that
    Module 6 evaluates its own SQLite volume condition fresh (Requirements 6.3,
    6.4). Mirrors the ``db_type`` normalization used by
    :func:`volume_utils.should_prompt` / :func:`volume_utils.should_warn_load_time`.

    Args:
        marker: The shared ``sqlite_volume_prompt`` marker dict (typically from
            :func:`read_load_decision`), or ``None`` when absent/unreadable.
        current_identity: The :func:`compute_load_identity` signature of the load
            Module 6 is about to run.
        db_type: The active database engine (``database_type``), or ``None`` when
            indeterminate.

    Returns:
        ``True`` only for a decided Module 4 marker matching the current load on
        SQLite; ``False`` otherwise. Never raises, never performs I/O.
    """
    # Missing or non-dict marker: no Module 4 decision to honor.
    if not isinstance(marker, dict):
        return False

    # Must be a Module 4 marker (not the Module 6 Hard_Prompt or anything else).
    if marker.get("source") != LOAD_MARKER_SOURCE:
        return False

    # Must be an actually-recorded decision (strict True, not merely truthy).
    if marker.get("decided") is not True:
        return False

    # Must apply to this exact load; a different identity falls back to Module 6.
    if marker.get("load_identity") != current_identity:
        return False

    # The concern is SQLite-specific; a non-SQLite engine no longer applies.
    if not isinstance(db_type, str):
        return False
    return db_type.strip().lower() == "sqlite"


# ---------------------------------------------------------------------------
# CLI diagnostic helpers (non-blocking -- never raise)
# ---------------------------------------------------------------------------


def _read_db_type(preferences_path: str) -> str | None:
    """Read ``database_type`` from preferences, tolerating missing/unreadable input.

    Reuses :func:`preferences_utils.load_preferences` with no required fields so
    a missing/unreadable/malformed preferences file is not fatal. Returns the
    ``database_type`` string when present, or ``None`` when the file is absent,
    unreadable, malformed, or the value is missing/non-string -- so an
    indeterminate database type resolves to the non-blocking "continue" path
    (Requirement 1.4).

    Args:
        preferences_path: Path to the bootcamp preferences YAML file.

    Returns:
        The active ``database_type`` string, or ``None`` when indeterminate.
    """
    try:
        result = preferences_utils.load_preferences(
            preferences_path, required_fields=()
        )
    except Exception:  # noqa: BLE001 - non-blocking contract (Req 7.5)
        return None

    preferences = result.preferences
    if not isinstance(preferences, dict):
        return None

    db_type = preferences.get("database_type")
    return db_type if isinstance(db_type, str) else None


def _compute_known_total(registry: data_sources.Registry) -> int | None:
    """Compute the collected ``known_total`` lower bound, guarding against errors.

    Delegates to :func:`record_count_backfill.compute_collected_count` with
    ``row_count=True`` (resolving unknown counts by row-counting countable
    files) and returns its ``known_total`` -- the determinate lower bound fed to
    :func:`volume_utils.should_warn_load_time`. Any unexpected error yields
    ``None`` so the collected total is treated as indeterminate and the flow
    continues (Requirements 2.4, 7.5).

    Args:
        registry: The parsed data source registry.

    Returns:
        The resolved ``known_total``, or ``None`` when it cannot be computed.
    """
    try:
        collected = record_count_backfill.compute_collected_count(
            registry, row_count=True
        )
    except Exception:  # noqa: BLE001 - non-blocking contract (Req 7.5)
        return None
    return collected.known_total


def _continue_reason(known_total: int | None, db_type: str | None) -> str:
    """Explain, in plain language, why no warning fires on a continue path.

    Args:
        known_total: The resolved collected total, or ``None`` when indeterminate.
        db_type: The active database type, or ``None`` when indeterminate.

    Returns:
        A PII-free, human-readable reason string (no trailing period).
    """
    if known_total is None:
        return "the collected record total is indeterminate"

    normalized = db_type.strip().lower() if isinstance(db_type, str) else ""
    if normalized != "sqlite":
        if normalized:
            return f"the active database ('{db_type}') is not SQLite"
        return "the active database type is indeterminate"

    # A real total on SQLite that did not trigger must be at or below the bound.
    return (
        f"the collected total ({known_total}) is at or below the "
        f"{volume_utils.LOAD_WARNING_THRESHOLD:,}-record warning threshold"
    )


def _format_marker_status(
    marker: dict | None,
    current_identity: str | None,
    db_type: str | None,
) -> str:
    """Render the current shared decision-marker status for the diagnostic.

    Reports whether a decision is recorded and, when it is, its ``choice``,
    ``source``, and ``load_identity``, plus whether
    :func:`module4_decision_applies` holds for the current load on the active
    database. When the registry could not be read (``current_identity is
    None``), applicability cannot be evaluated and is reported as unknown.

    Args:
        marker: The shared ``sqlite_volume_prompt`` marker dict, or ``None``.
        current_identity: The current load identity, or ``None`` when the
            registry is unavailable.
        db_type: The active database type, or ``None`` when indeterminate.

    Returns:
        A multi-line, PII-free status string (source names + counts only).
    """
    if not isinstance(marker, dict):
        return (
            "Decision marker: none recorded -- Module 6 will evaluate its own "
            "SQLite volume condition."
        )

    lines = [
        "Decision marker: a decision is recorded.",
        f"  - choice:        {marker.get('choice')}",
        f"  - source:        {marker.get('source')}",
        f"  - load_identity: {marker.get('load_identity')}",
    ]
    if current_identity is None:
        lines.append(
            "  - applies to this load: unknown "
            "(registry unavailable, cannot compute the current load identity)"
        )
    else:
        applies = module4_decision_applies(marker, current_identity, db_type)
        lines.append(f"  - applies to this load: {applies}")
    return "\n".join(lines)


def _print_continue_report(known_total: int | None, db_type: str | None) -> None:
    """Print the non-blocking "no warning -- continue" report to stdout.

    Args:
        known_total: The resolved collected total, or ``None`` when indeterminate.
        db_type: The active database type, or ``None`` when indeterminate.
    """
    total_desc = str(known_total) if known_total is not None else "indeterminate"
    db_desc = db_type if db_type is not None else "indeterminate"
    print("No load-time warning -- continue the Module 4 flow.")
    print(f"  Collected total: {total_desc}")
    print(f"  Active database: {db_desc}")
    print(f"  Reason: {_continue_reason(known_total, db_type)}.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI diagnostic: evaluate and report the Module 4 SQLite Load_Time_Warning.

    Reads the collected registry (via the ``data_sources`` reader chain) and the
    active ``database_type`` (via ``preferences_utils``), computes the collected
    total (via ``record_count_backfill``), and evaluates
    :func:`volume_utils.should_warn_load_time`. When the warning fires it prints
    the built warning text (:func:`volume_utils.build_load_time_warning`) with a
    :class:`volume_utils.TimingGuidance` whose figures are all ``None`` -- this
    CLI diagnostic does not consult the MCP server (MCP retrieval is the
    steering's job), so every timing figure is reported unavailable. Otherwise it
    prints a "no warning -- continue" report. In both cases it also prints the
    current shared decision-marker status.

    Every path is non-blocking: a missing/unreadable/malformed registry or
    preferences file, an uncomputable total, or an indeterminate database type
    all resolve to a "continue" report and exit 0 (Requirements 7.4, 7.5). The
    function never raises. Argparse misuse (an unknown flag) exits non-zero via
    argparse itself.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code: always 0 on the diagnostic's own paths (the
        non-blocking contract).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Module 4 SQLite Load-Time Warning helper",
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
    args = parser.parse_args(argv)

    # database_type is read independently and tolerantly (indeterminate -> None).
    db_type = _read_db_type(args.preferences)

    # The shared decision marker is read the same way regardless of the outcome.
    marker = read_load_decision(args.preferences)

    # Read + parse the registry via the data_sources reader chain. Any failure is
    # non-blocking: warn to stderr, report continue, print the marker status
    # (without a current identity, since none can be computed), and return 0.
    try:
        registry_text = Path(args.registry).read_text(encoding="utf-8")
        raw = data_sources.parse_registry_yaml(registry_text)
        raw = data_sources.apply_migrations(raw)
        registry = data_sources._dict_to_registry(raw)
    except Exception as exc:  # noqa: BLE001 - non-blocking contract (Req 7.5)
        print(
            f"load_time_warning: warning: could not read registry "
            f"'{args.registry}': {exc}",
            file=sys.stderr,
        )
        _print_continue_report(known_total=None, db_type=db_type)
        print()
        print(_format_marker_status(marker, current_identity=None, db_type=db_type))
        return 0

    known_total = _compute_known_total(registry)
    current_identity = compute_load_identity(registry)

    if volume_utils.should_warn_load_time(known_total, db_type):
        # The CLI diagnostic never consults the MCP server (that is the
        # steering's job); every timing figure is therefore reported unavailable.
        timing = volume_utils.TimingGuidance()
        print(volume_utils.build_load_time_warning(known_total, timing))
    else:
        _print_continue_report(known_total, db_type)

    print()
    print(_format_marker_status(marker, current_identity, db_type))
    return 0


if __name__ == "__main__":
    sys.exit(main())
