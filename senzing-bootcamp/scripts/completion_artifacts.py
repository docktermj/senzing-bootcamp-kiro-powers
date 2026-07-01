#!/usr/bin/env python3
"""Deterministic planner for per-module completion artifacts.

Given the bootcamp progress state and the artifacts currently on disk, this
module computes (a) which completed modules are missing which artifact types,
(b) the real per-module Duration from ``step_history`` ISO 8601 timestamps, and
(c) the cumulative ``Total Duration`` — omitting any Duration that cannot be
reliably derived rather than emitting a placeholder. It also produces a
deterministic, idempotent backfill plan for already-completed modules.

This is a stdlib-only, side-effect-free planner. The hooks and the
``module-completion.md`` workflow consume its CLI to decide what to generate.

Usage:
    # Report coverage gaps / placeholder durations; exit 1 if the bug condition holds.
    python senzing-bootcamp/scripts/completion_artifacts.py \\
        --progress config/bootcamp_progress.json \\
        --recap docs/bootcamp_recap.md \\
        --journal docs/bootcamp_journal.md \\
        --progress-dir docs/progress \\
        --check

    # Emit the backfill plan as JSON for the workflow to consume.
    python senzing-bootcamp/scripts/completion_artifacts.py \\
        --progress config/bootcamp_progress.json \\
        --recap docs/bootcamp_recap.md \\
        --journal docs/bootcamp_journal.md \\
        --progress-dir docs/progress \\
        --plan

Exits 0 on success, 1 on error (or when ``--check`` detects the bug condition).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ProgressState:
    """The bootcamp progress state relevant to artifact planning.

    Attributes:
        modules_completed: Module numbers recorded as completed.
        step_history: Map of module-number strings (``"1"``..``"12"``) to objects
            carrying at least an ISO 8601 ``updated_at`` timestamp.
        started_at: Top-level ISO 8601 timestamp marking when the bootcamp began;
            used as the lower bound for the first module's elapsed time.
    """

    modules_completed: list[int]
    step_history: dict[str, dict[str, object]] = field(default_factory=dict)
    started_at: str | None = None


@dataclass
class ArtifactInventory:
    """The per-module artifacts discovered on disk.

    Attributes:
        recap_sections: Module numbers that already have a recap section.
        journal_entries: Module numbers that already have a journal entry.
        certificates: Module numbers that already have a completion certificate.
    """

    recap_sections: set[int] = field(default_factory=set)
    journal_entries: set[int] = field(default_factory=set)
    certificates: set[int] = field(default_factory=set)


@dataclass
class ArtifactGapReport:
    """Per-artifact-type lists of completed modules missing that artifact.

    Attributes:
        missing_recap: Sorted completed modules without a recap section.
        missing_journal: Sorted completed modules without a journal entry.
        missing_certificate: Sorted completed modules without a certificate,
            applying the uniform-certificate rule (see :func:`detect_artifact_gaps`).
    """

    missing_recap: list[int] = field(default_factory=list)
    missing_journal: list[int] = field(default_factory=list)
    missing_certificate: list[int] = field(default_factory=list)

    # --- Aliases for robustness against differing naming expectations ---
    @property
    def missing_recap_sections(self) -> list[int]:
        """Alias for :attr:`missing_recap`."""
        return self.missing_recap

    @property
    def missing_journal_entries(self) -> list[int]:
        """Alias for :attr:`missing_journal`."""
        return self.missing_journal

    @property
    def missing_certificates(self) -> list[int]:
        """Alias for :attr:`missing_certificate`."""
        return self.missing_certificate

    @property
    def missing_certs(self) -> list[int]:
        """Alias for :attr:`missing_certificate`."""
        return self.missing_certificate


@dataclass
class BackfillPlan:
    """A deterministic, idempotent plan describing artifacts to create.

    The module lists are exactly the set difference between completed modules and
    the artifacts already on disk — existing artifacts are never re-emitted.

    Attributes:
        recap_modules: Sorted modules needing a recap section.
        journal_modules: Sorted modules needing a journal entry.
        certificate_modules: Sorted modules needing a completion certificate.
        module_durations: Map of module number to computed Duration string
            (only modules with reliable timing appear).
        total_duration: Cumulative ``Total Duration`` string, or ``None`` when
            no reliable timing is available.
    """

    recap_modules: list[int] = field(default_factory=list)
    journal_modules: list[int] = field(default_factory=list)
    certificate_modules: list[int] = field(default_factory=list)
    module_durations: dict[int, str] = field(default_factory=dict)
    total_duration: str | None = None

    @property
    def is_empty(self) -> bool:
        """Return True when there is nothing to backfill."""
        return not (self.recap_modules or self.journal_modules or self.certificate_modules)


# ---------------------------------------------------------------------------
# Timestamp / Duration helpers
# ---------------------------------------------------------------------------

_DURATION_RE = re.compile(r"\d+\s*(d|h|m|s)", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"module\s+\w+\s+session", re.IGNORECASE)


def _parse_iso(timestamp: object) -> datetime | None:
    """Parse an ISO 8601 timestamp, normalizing a trailing ``Z`` to ``+00:00``.

    Args:
        timestamp: A candidate timestamp value (expected to be a string).

    Returns:
        The parsed ``datetime``, or ``None`` if missing or unparseable.
    """
    if not isinstance(timestamp, str):
        return None
    text = timestamp.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _updated_at(step_history: dict[str, dict[str, object]], module: int) -> object:
    """Return the raw ``updated_at`` value for a module, or ``None`` if absent."""
    entry = step_history.get(str(module))
    if not isinstance(entry, dict):
        return None
    return entry.get("updated_at")


def _module_elapsed(
    step_history: dict[str, dict[str, object]],
    started_at: str | None,
    module: int,
    prior_timestamp: str | None,
) -> timedelta | None:
    """Compute a module's elapsed time as a ``timedelta`` from bounding timestamps.

    The lower bound is the prior module's ``updated_at`` (``prior_timestamp``), or
    ``started_at`` for the first module (when ``prior_timestamp`` is ``None``). The
    upper bound is ``step_history[str(module)].updated_at``.

    Args:
        step_history: Map of module-number strings to objects with ``updated_at``.
        started_at: Lower bound for the first module.
        module: The module number to compute.
        prior_timestamp: The prior module's ``updated_at``, or ``None`` for the first.

    Returns:
        The elapsed ``timedelta`` when both bounds parse and ``end >= start``;
        otherwise ``None``.
    """
    end = _parse_iso(_updated_at(step_history, module))
    if end is None:
        return None
    lower_raw = started_at if prior_timestamp is None else prior_timestamp
    start = _parse_iso(lower_raw)
    if start is None:
        return None
    try:
        if end < start:
            return None
        return end - start
    except TypeError:
        # Mixed tz-aware / naive timestamps are not comparable.
        return None


def _format_timedelta(delta: timedelta) -> str:
    """Format a non-negative ``timedelta`` as a human-readable elapsed time.

    Examples: ``1h 12m``, ``2d 3h 5m``, ``45s``, ``0m``.

    Args:
        delta: The duration to format (assumed non-negative).

    Returns:
        A compact human-readable string of the non-zero units.
    """
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s" if seconds else "0m")
    return " ".join(parts)


def is_placeholder(text: str | None) -> bool:
    """Return True for empty/missing values and non-time strings.

    A value is a placeholder when it is empty/missing, matches ``Module N session``,
    or does not read as a real elapsed duration (no digit+unit token).

    Args:
        text: The Duration text currently present in the recap (may be ``None``).

    Returns:
        True if ``text`` is a placeholder rather than a real elapsed time.
    """
    if text is None or not str(text).strip():
        return True
    value = str(text)
    if _PLACEHOLDER_RE.search(value):
        return True
    return _DURATION_RE.search(value) is None


# Camel-case alias (tests resolve either spelling).
isPlaceholder = is_placeholder  # noqa: N816 - intentional API alias


def reliable_timing(
    step_history: dict[str, dict[str, object]],
    started_at: str | None,
    module: int,
    prior_timestamp: str | None = None,
) -> timedelta | None:
    """Return a module's reliable elapsed ``timedelta``, or ``None`` if not derivable.

    Args:
        step_history: Map of module-number strings to objects with ``updated_at``.
        started_at: Lower bound for the first module.
        module: The module number to evaluate.
        prior_timestamp: The prior module's ``updated_at``, or ``None`` for the first.

    Returns:
        The elapsed ``timedelta`` when timing is reliable; otherwise ``None``.
    """
    return _module_elapsed(step_history, started_at, module, prior_timestamp)


def _reliable_per_module(
    step_history: dict[str, dict[str, object]],
    started_at: str | None,
    modules_completed: list[int],
) -> dict[int, timedelta]:
    """Compute reliable per-module elapsed times in ascending module order.

    Each module's lower bound is the previous module's ``updated_at`` (or
    ``started_at`` for the first module).

    Args:
        step_history: Map of module-number strings to objects with ``updated_at``.
        started_at: Lower bound for the first module.
        modules_completed: Completed module numbers (order-independent).

    Returns:
        A map of module number to elapsed ``timedelta`` for modules with reliable
        timing only.
    """
    result: dict[int, timedelta] = {}
    prior_timestamp: str | None = None
    for module in sorted(modules_completed):
        elapsed = _module_elapsed(step_history, started_at, module, prior_timestamp)
        if elapsed is not None:
            result[module] = elapsed
        raw_upper = _updated_at(step_history, module)
        if isinstance(raw_upper, str) and raw_upper.strip():
            prior_timestamp = raw_upper
    return result


# ---------------------------------------------------------------------------
# Core planner API
# ---------------------------------------------------------------------------


def compute_module_duration(
    step_history: dict[str, dict[str, object]],
    started_at: str | None,
    module: int,
    prior_timestamp: str | None,
) -> str | None:
    """Compute a module's Duration string from ISO 8601 timestamps.

    Args:
        step_history: Map of module-number strings to objects with ``updated_at``.
        started_at: Lower bound for the first module (``prior_timestamp`` is ``None``).
        module: The module number to compute.
        prior_timestamp: The prior module's ``updated_at``, or ``None`` for the first.

    Returns:
        A human-readable elapsed time (e.g., ``1h 12m``) when the bounding timestamps
        exist, parse, and are ordered; otherwise ``None`` (so the recap omits the
        ``### Duration`` field).
    """
    elapsed = _module_elapsed(step_history, started_at, module, prior_timestamp)
    if elapsed is None:
        return None
    return _format_timedelta(elapsed)


def compute_total_duration(
    step_history: dict[str, dict[str, object]],
    started_at: str | None,
    modules_completed: list[int],
) -> str | None:
    """Compute the cumulative ``Total Duration`` by rolling up per-module times.

    Per-module elapsed times are summed in ascending module order. Because each
    contribution is non-negative, the rolled-up total is monotonically
    non-decreasing as modules are added.

    Args:
        step_history: Map of module-number strings to objects with ``updated_at``.
        started_at: Lower bound for the first module.
        modules_completed: Completed module numbers.

    Returns:
        A human-readable cumulative elapsed time, or ``None`` when no reliable
        per-module timing is available (so the header omits ``Total Duration``).
    """
    per_module = _reliable_per_module(step_history, started_at, modules_completed)
    if not per_module:
        return None
    total = timedelta()
    for elapsed in per_module.values():
        total += elapsed
    return _format_timedelta(total)


def detect_artifact_gaps(
    modules_completed: list[int], inventory: ArtifactInventory
) -> ArtifactGapReport:
    """Report, per artifact type, the completed modules missing that artifact.

    The uniform-certificate rule applies: if any certificate exists on disk, every
    completed module is required to have one (so all certificate-less completed
    modules are reported). If no certificates exist at all, none are required —
    "all or none" is uniform.

    Args:
        modules_completed: Completed module numbers.
        inventory: The artifacts currently present on disk.

    Returns:
        An :class:`ArtifactGapReport` with sorted per-type missing-module lists.
    """
    completed = sorted({int(m) for m in modules_completed})

    missing_recap = [m for m in completed if m not in inventory.recap_sections]
    missing_journal = [m for m in completed if m not in inventory.journal_entries]

    if inventory.certificates:
        missing_certificate = [m for m in completed if m not in inventory.certificates]
    else:
        # No certificates anywhere -> "none at all" is uniform; nothing required.
        missing_certificate = []

    return ArtifactGapReport(
        missing_recap=missing_recap,
        missing_journal=missing_journal,
        missing_certificate=missing_certificate,
    )


def plan_backfill(
    progress_state: ProgressState, inventory: ArtifactInventory
) -> BackfillPlan:
    """Build a deterministic, idempotent backfill plan (set difference only).

    Combines gap detection with duration computation. Re-running on a complete,
    consistent set yields an empty plan; existing artifacts are never re-emitted.

    Args:
        progress_state: The current progress state.
        inventory: The artifacts currently present on disk.

    Returns:
        A :class:`BackfillPlan` describing exactly which artifacts to create.
    """
    gaps = detect_artifact_gaps(progress_state.modules_completed, inventory)

    per_module = _reliable_per_module(
        progress_state.step_history,
        progress_state.started_at,
        progress_state.modules_completed,
    )
    module_durations = {m: _format_timedelta(elapsed) for m, elapsed in per_module.items()}
    total_duration = compute_total_duration(
        progress_state.step_history,
        progress_state.started_at,
        progress_state.modules_completed,
    )

    return BackfillPlan(
        recap_modules=list(gaps.missing_recap),
        journal_modules=list(gaps.missing_journal),
        certificate_modules=list(gaps.missing_certificate),
        module_durations=module_durations,
        total_duration=total_duration,
    )


def is_bug_condition(
    progress_state: ProgressState,
    inventory: ArtifactInventory,
    recap_durations: dict[int, str] | None,
    recap_total: str | None,
) -> bool:
    """Return True when the bug condition holds (mirrors the formal spec).

    The bug condition is::

        coverageGap OR certificatesNonUniform OR placeholderDuration OR placeholderTotal

    where coverage and certificate gaps use the uniform-certificate rule.

    Args:
        progress_state: The current progress state.
        inventory: The artifacts currently present on disk.
        recap_durations: Per-module Duration text currently in the recap.
        recap_total: The recap header ``Total Duration`` text.

    Returns:
        True if any clause of the bug condition holds.
    """
    completed = {int(m) for m in progress_state.modules_completed}
    durations = recap_durations or {}

    gaps = detect_artifact_gaps(progress_state.modules_completed, inventory)
    coverage_gap = bool(gaps.missing_recap or gaps.missing_journal or gaps.missing_certificate)

    has_cert = bool(completed & inventory.certificates)
    missing_cert = bool(completed - inventory.certificates)
    certificates_non_uniform = has_cert and missing_cert

    per_module = _reliable_per_module(
        progress_state.step_history,
        progress_state.started_at,
        progress_state.modules_completed,
    )
    placeholder_duration = any(
        is_placeholder(durations.get(m)) and m in per_module for m in completed
    )

    total = compute_total_duration(
        progress_state.step_history,
        progress_state.started_at,
        progress_state.modules_completed,
    )
    placeholder_total = is_placeholder(recap_total) and total is not None

    return (
        coverage_gap
        or certificates_non_uniform
        or placeholder_duration
        or placeholder_total
    )


# Camel-case alias (tests resolve either spelling).
isBugCondition = is_bug_condition  # noqa: N816 - intentional API alias


# ---------------------------------------------------------------------------
# On-disk discovery helpers (used by the CLI)
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^##+\s*Module\s+(\d+)\b", re.MULTILINE)
_TOTAL_DURATION_RE = re.compile(r"^\*\*Total Duration:\*\*\s*(.+)$", re.MULTILINE)
_CERT_FILE_RE = re.compile(r"MODULE_(\d+)_COMPLETE\.md$", re.IGNORECASE)


def _discover_section_modules(content: str) -> set[int]:
    """Return module numbers that have a ``## Module N`` section in ``content``."""
    return {int(m) for m in _SECTION_RE.findall(content)}


def _discover_certificates(progress_dir: Path) -> set[int]:
    """Return module numbers with a ``MODULE_N_COMPLETE.md`` file in ``progress_dir``."""
    found: set[int] = set()
    if not progress_dir.is_dir():
        return found
    for child in progress_dir.iterdir():
        match = _CERT_FILE_RE.search(child.name)
        if match:
            found.add(int(match.group(1)))
    return found


def _discover_recap_durations(content: str) -> dict[int, str]:
    """Best-effort parse of per-module ``### Duration`` text from the recap."""
    durations: dict[int, str] = {}
    sections = list(_SECTION_RE.finditer(content))
    for index, match in enumerate(sections):
        module = int(match.group(1))
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(content)
        block = content[start:end]
        dur_match = re.search(r"^###\s*Duration\s*\n+\s*(.+?)\s*$", block, re.MULTILINE)
        if dur_match:
            durations[module] = dur_match.group(1).strip()
    return durations


# ---------------------------------------------------------------------------
# Recap backfill applier (synchronous, verified, idempotent, append-around)
# ---------------------------------------------------------------------------

_MODULE_NAME_RE = re.compile(r"^\s{2}(\d+):\s*$")
_NAME_FIELD_RE = re.compile(r'^\s{4}name:\s*"?(.+?)"?\s*$')

_RECAP_HEADER = (
    "# Senzing Bootcamp Recap\n"
    "\n"
    "**Bootcamper:** Bootcamper\n"
    "\n"
    "---\n"
)


def load_module_names(yaml_path: Path) -> dict[int, str]:
    """Parse module number -> name from ``module-dependencies.yaml`` (stdlib-only).

    Uses a minimal line scanner over the ``modules:`` block rather than a full
    YAML parser (PyYAML is not a dependency for this script). Missing or
    unparseable files yield an empty mapping so the caller falls back to a
    generic module label.

    Args:
        yaml_path: Path to ``config/module-dependencies.yaml``.

    Returns:
        A mapping of module number to module name (empty when unavailable).
    """
    names: dict[int, str] = {}
    if not yaml_path.is_file():
        return names
    try:
        lines = yaml_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return names
    in_modules = False
    current: int | None = None
    for line in lines:
        if line.rstrip() == "modules:":
            in_modules = True
            continue
        if in_modules and line and not line[0].isspace():
            # Dedented to a new top-level key -> end of the modules block.
            break
        if not in_modules:
            continue
        module_match = _MODULE_NAME_RE.match(line)
        if module_match:
            current = int(module_match.group(1))
            continue
        if current is not None:
            name_match = _NAME_FIELD_RE.match(line)
            if name_match:
                names[current] = name_match.group(1).strip()
                current = None
    return names


def render_backfill_section(
    module: int,
    *,
    name: str | None = None,
    timestamp: str | None = None,
    duration: str | None = None,
) -> str:
    """Render a minimal, schema-valid ``## Module N:`` recap section for backfill.

    The backfill applier does not have the original session transcript, so the
    body subsections carry explicit ``N/A`` placeholders noting the content was
    reconstructed. The ``### Duration`` field is included only when a reliable
    value is supplied (mirroring the hook's no-placeholder rule).

    Args:
        module: The module number being backfilled.
        name: The module's human-readable name, if known.
        timestamp: The module's completion timestamp (ISO 8601), if known.
        duration: The per-module Duration string from the planner, if reliable.

    Returns:
        The Markdown for one recap section, beginning and ending with a newline
        so it appends cleanly after existing content without rewriting it.
    """
    label = name if name else f"Module {module}"
    heading = f"## Module {module}: {label}"
    if timestamp:
        heading = f"{heading} \u2014 {timestamp}"
    parts = [
        "",
        heading,
        "",
        "### Information Shared",
        "- N/A (section backfilled at track completion; original session content unavailable)",
        "",
        "### Questions Asked",
        "- N/A",
        "",
        "### Answers Given",
        "- N/A",
        "",
        "### Actions Taken",
        "- N/A",
    ]
    if duration:
        parts += ["", "### Duration", duration]
    parts += ["", "---", ""]
    return "\n".join(parts)


def _resolve_progress_and_recap(path_a: object, path_b: object) -> tuple[Path, Path]:
    """Disambiguate which argument is the progress JSON and which is the recap.

    Accepts the two paths in either order (callers and tests differ), detecting
    the progress file as the one whose contents parse as JSON.

    Args:
        path_a: First path-like argument.
        path_b: Second path-like argument.

    Returns:
        A ``(progress_path, recap_path)`` tuple.
    """
    first = Path(str(path_a))
    second = Path(str(path_b))

    def _is_progress(candidate: Path) -> bool:
        if candidate.suffix.lower() == ".json":
            return True
        if candidate.suffix.lower() in {".md", ".markdown"}:
            return False
        if candidate.is_file():
            try:
                json.loads(candidate.read_text(encoding="utf-8"))
                return True
            except (json.JSONDecodeError, OSError):
                return False
        return False

    if _is_progress(first):
        return first, second
    if _is_progress(second):
        return second, first
    # Neither clearly identified: assume conventional (progress, recap) order.
    return first, second


def _load_progress_state(progress_path: Path) -> ProgressState:
    """Load a :class:`ProgressState` from a bootcamp progress JSON file."""
    data = json.loads(progress_path.read_text(encoding="utf-8"))
    modules_completed = [int(m) for m in data.get("modules_completed", [])]
    raw_history = data.get("step_history", {})
    step_history = raw_history if isinstance(raw_history, dict) else {}
    return ProgressState(
        modules_completed=modules_completed,
        step_history=step_history,
        started_at=data.get("started_at"),
    )


def _normalize_timestamp(raw: object) -> str | None:
    """Return a trimmed ISO 8601 timestamp string, or ``None`` when unusable."""
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def backfill_recap_sections(
    progress: object,
    recap: object,
    *,
    progress_dir: object | None = None,
    journal: object | None = None,
    module_names: dict[int, str] | None = None,
) -> list[int]:
    """Append any missing per-module ``## Module N:`` recap sections in place.

    This is the synchronous, verified backfill applier consumed by the
    module-completion and track-completion workflows. It reuses :func:`plan_backfill`
    so the set of modules written is exactly the difference between
    ``modules_completed`` and the sections already on disk. Behavior:

    - **Append-around, never rewrite:** existing recap bytes are preserved
      exactly; new sections are appended at the end in ascending (chronological)
      module order.
    - **Idempotent:** when the recap already covers every completed module the
      plan is empty and the file is left untouched (no write occurs).
    - **Self-creating:** if the recap file does not yet exist it is created with a
      minimal header before sections are appended.

    The two positional arguments may be supplied in either order; the progress
    JSON is detected by content so callers and tests using either convention work.

    Args:
        progress: Path to ``config/bootcamp_progress.json`` (or the recap path;
            order is auto-detected).
        recap: Path to ``docs/bootcamp_recap.md`` (or the progress path; order is
            auto-detected).
        progress_dir: Unused for recap backfill; accepted for signature
            compatibility with the planner CLI surface.
        journal: Unused for recap backfill; accepted for signature compatibility.
        module_names: Optional override mapping of module number to name; when
            omitted, names are loaded best-effort from ``module-dependencies.yaml``
            next to the progress file.

    Returns:
        The sorted list of module numbers whose sections were appended (empty
        when nothing needed backfilling).
    """
    del progress_dir, journal  # accepted for CLI-surface compatibility only

    progress_path, recap_path = _resolve_progress_and_recap(progress, recap)
    progress_state = _load_progress_state(progress_path)

    existing = ""
    if recap_path.is_file():
        existing = recap_path.read_text(encoding="utf-8")

    inventory = ArtifactInventory(
        recap_sections=_discover_section_modules(existing),
    )
    plan = plan_backfill(progress_state, inventory)
    missing = sorted(plan.recap_modules)
    if not missing:
        return []

    if module_names is None:
        module_names = load_module_names(progress_path.parent / "module-dependencies.yaml")

    additions = "".join(
        render_backfill_section(
            module,
            name=module_names.get(module),
            timestamp=_normalize_timestamp(_updated_at(progress_state.step_history, module)),
            duration=plan.module_durations.get(module),
        )
        for module in missing
    )

    if not existing:
        new_content = _RECAP_HEADER + additions
    else:
        prefix = existing if existing.endswith("\n") else existing + "\n"
        new_content = prefix + additions

    recap_path.parent.mkdir(parents=True, exist_ok=True)
    recap_path.write_text(new_content, encoding="utf-8")
    return missing


# Aliases — the workflow and tests resolve any of these spellings.
reconcile_recap = backfill_recap_sections
backfill_recap = backfill_recap_sections
apply_backfill = backfill_recap_sections
write_missing_recap_sections = backfill_recap_sections


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run the completion-artifacts planner CLI.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).
    """
    parser = argparse.ArgumentParser(
        description="Plan and check per-module completion artifacts (stdlib-only)."
    )
    parser.add_argument("--progress", help="Path to config/bootcamp_progress.json")
    parser.add_argument("--recap", help="Path to docs/bootcamp_recap.md")
    parser.add_argument("--journal", help="Path to docs/bootcamp_journal.md")
    parser.add_argument(
        "--progress-dir",
        dest="progress_dir",
        help="Path to docs/progress (directory of MODULE_N_COMPLETE.md certificates)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Print the gap/placeholder report; exit 1 if the bug condition holds.",
    )
    mode.add_argument(
        "--plan",
        action="store_true",
        help="Emit the backfill plan as JSON.",
    )
    mode.add_argument(
        "--backfill",
        "--apply",
        "--reconcile",
        "--write",
        dest="backfill",
        action="store_true",
        help=(
            "Apply the recap backfill: append a '## Module N:' section for every "
            "completed module missing one (append-around, idempotent)."
        ),
    )
    args = parser.parse_args(argv)

    # --- Load progress state ---
    modules_completed: list[int] = []
    step_history: dict[str, dict[str, object]] = {}
    started_at: str | None = None
    if args.progress:
        progress_path = Path(args.progress)
        if not progress_path.is_file():
            print(f"Progress file not found: {args.progress}", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"Failed to read progress file: {exc}", file=sys.stderr)
            sys.exit(1)
        modules_completed = [int(m) for m in data.get("modules_completed", [])]
        raw_history = data.get("step_history", {})
        if isinstance(raw_history, dict):
            step_history = raw_history
        started_at = data.get("started_at")

    progress_state = ProgressState(
        modules_completed=modules_completed,
        step_history=step_history,
        started_at=started_at,
    )

    # --- Discover on-disk inventory ---
    recap_content = ""
    if args.recap and Path(args.recap).is_file():
        recap_content = Path(args.recap).read_text(encoding="utf-8")
    journal_content = ""
    if args.journal and Path(args.journal).is_file():
        journal_content = Path(args.journal).read_text(encoding="utf-8")

    certificates: set[int] = set()
    if args.progress_dir:
        certificates = _discover_certificates(Path(args.progress_dir))

    inventory = ArtifactInventory(
        recap_sections=_discover_section_modules(recap_content),
        journal_entries=_discover_section_modules(journal_content),
        certificates=certificates,
    )

    recap_durations = _discover_recap_durations(recap_content)
    total_match = _TOTAL_DURATION_RE.search(recap_content)
    recap_total = total_match.group(1).strip() if total_match else None

    # --- Dispatch ---
    if args.backfill:
        if not args.progress:
            print("--backfill requires --progress", file=sys.stderr)
            sys.exit(1)
        if not args.recap:
            print("--backfill requires --recap", file=sys.stderr)
            sys.exit(1)
        try:
            written = backfill_recap_sections(args.progress, args.recap)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Recap backfill failed: {exc}", file=sys.stderr)
            sys.exit(1)
        # Verify: every completed module now has a persisted section.
        verify_content = ""
        if Path(args.recap).is_file():
            verify_content = Path(args.recap).read_text(encoding="utf-8")
        present = _discover_section_modules(verify_content)
        still_missing = sorted(m for m in set(modules_completed) if m not in present)
        if still_missing:
            print(
                f"Recap backfill incomplete: sections still missing for {still_missing}",
                file=sys.stderr,
            )
            sys.exit(1)
        if written:
            print(f"Backfilled recap sections for modules: {written}")
        else:
            print("Recap already complete; no sections backfilled.")
        sys.exit(0)

    if args.plan:
        plan = plan_backfill(progress_state, inventory)
        payload = {
            "recap_modules": plan.recap_modules,
            "journal_modules": plan.journal_modules,
            "certificate_modules": plan.certificate_modules,
            "module_durations": {str(k): v for k, v in plan.module_durations.items()},
            "total_duration": plan.total_duration,
        }
        print(json.dumps(payload, indent=2))
        sys.exit(0)

    # Default and --check: print the report.
    gaps = detect_artifact_gaps(progress_state.modules_completed, inventory)
    bug = is_bug_condition(progress_state, inventory, recap_durations, recap_total)

    print(f"Completed modules:        {sorted(set(modules_completed))}")
    print(f"Missing recap sections:   {gaps.missing_recap}")
    print(f"Missing journal entries:  {gaps.missing_journal}")
    print(f"Missing certificates:     {gaps.missing_certificate}")
    total = compute_total_duration(step_history, started_at, modules_completed)
    print(f"Computed Total Duration:  {total if total is not None else '(omitted)'}")
    print(f"Bug condition:            {bug}")

    if args.check and bug:
        print("Completion-artifact bug condition detected.", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
