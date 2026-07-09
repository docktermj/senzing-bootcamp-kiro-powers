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
        --progress-dir docs/progress \\
        --check

    # Emit the backfill plan as JSON for the workflow to consume.
    python senzing-bootcamp/scripts/completion_artifacts.py \\
        --progress config/bootcamp_progress.json \\
        --recap docs/bootcamp_recap.md \\
        --progress-dir docs/progress \\
        --plan

    # One-time: merge the legacy journal into the consolidated recap.
    python senzing-bootcamp/scripts/completion_artifacts.py \\
        --recap docs/bootcamp_recap.md \\
        --journal docs/bootcamp_journal.md \\
        --migrate

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


@dataclass
class JournalFields:
    """The four narrative fields in a ``### Journal`` subsection.

    Attributes:
        what_we_did: Summary of module activities.
        what_was_produced: Comma-separated artifact paths.
        why_it_matters: Explanation of module significance.
        bootcamper_takeaway: Bootcamper's stated takeaway or ``'N/A'``.
    """

    what_we_did: str
    what_was_produced: str
    why_it_matters: str
    bootcamper_takeaway: str


@dataclass
class ParsedRecapSection:
    """Structured representation of one ``## Module N:`` section.

    Attributes:
        module_number: The module number.
        module_name: The module display name.
        timestamp: The completion timestamp string.
        information_shared: List of items.
        questions_responses: List of ``(question, response)`` pairs.
        actions_taken: List of items.
        duration: Duration string or ``None``.
        journal: :class:`JournalFields` or ``None``.
    """

    module_number: int
    module_name: str
    timestamp: str
    information_shared: list[str]
    questions_responses: list[tuple[str, str]]
    actions_taken: list[str]
    duration: str | None
    journal: JournalFields | None


@dataclass
class MigrationReport:
    """Result of running the journal-to-recap migration.

    Attributes:
        modules_merged: Module numbers whose journal entries were merged
            into existing recap sections.
        modules_created: Module numbers for which new recap sections were
            created (journal entry existed but no recap section).
        already_consolidated: Module numbers skipped because they already
            had a ``### Journal`` subsection.
        journal_path: Path to the legacy journal file (for retirement).
    """

    modules_merged: list[int] = field(default_factory=list)
    modules_created: list[int] = field(default_factory=list)
    already_consolidated: list[int] = field(default_factory=list)
    journal_path: str = ""


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

    Note:
        Journal content is no longer a separately tracked artifact — it is folded
        into each recap section as a ``### Journal`` subsection (the
        journal-recap-consolidation feature). ``missing_journal`` is therefore
        always empty; the field is retained only for backward compatibility.
    """
    completed = sorted({int(m) for m in modules_completed})

    missing_recap = [m for m in completed if m not in inventory.recap_sections]

    if inventory.certificates:
        missing_certificate = [m for m in completed if m not in inventory.certificates]
    else:
        # No certificates anywhere -> "none at all" is uniform; nothing required.
        missing_certificate = []

    return ArtifactGapReport(
        missing_recap=missing_recap,
        missing_journal=[],
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
        # Journal content is consolidated into each recap section, so it is never
        # planned as a separate artifact. Kept empty for backward compatibility.
        journal_modules=[],
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
    # Journal content is consolidated into the recap, so it no longer contributes
    # a distinct coverage-gap clause.
    coverage_gap = bool(gaps.missing_recap or gaps.missing_certificate)

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
# Consolidated_Log parsing and rendering
# ---------------------------------------------------------------------------
#
# The Consolidated_Log (``docs/bootcamp_recap.md``) holds one Recap_Section per
# completed module. :func:`parse_recap_sections` reads the file into structured
# :class:`ParsedRecapSection` objects and :func:`render_recap_section` writes one
# such object back to canonical Markdown. The pair is designed to satisfy the
# round-trip property (design Property 1): for any log,
# ``parse(render_all(parse(log))) == parse(log)``. Rendering is therefore
# canonical (fixed spacing, ordered subsections) and parsing is tolerant of the
# incidental whitespace variations a hand-edited or hook-appended file may carry.

# Canonical Recap_Section literals — the single source of truth for round-trip.
# The module heading is ``## Module N: [Name]`` with an optional
# `` \u2014 [timestamp]`` suffix. The name is captured non-greedily so the first
# spaced em-dash delimits the (optional) timestamp; a heading without one parses
# with an empty timestamp and re-renders without the suffix.
_MODULE_HEADING_RE = re.compile(
    r"^##[ \t]+Module[ \t]+(\d+):[ \t]+(.+?)(?:[ \t]+\u2014[ \t]+(.+?))?[ \t]*$",
    re.MULTILINE,
)
_SUBSECTION_SPLIT_RE = re.compile(r"^###[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_LIST_ITEM_RE = re.compile(r"^[ \t]*(?:-|\d+\.)[ \t]+(.+?)[ \t]*$", re.MULTILINE)

# Paired ``### Questions & Responses`` literals (mirror recap_pdf_render so the
# hook, the PDF renderer, and this parser share one Q&R contract). A
# Response_Item nests one level (four spaces) beneath its Question_Item.
_QR_HEADING = "### Questions & Responses"
_QR_QUESTION_PREFIX = "- **Q:** "
_QR_RESPONSE_PREFIX = "- **R:** "
_QR_EMPTY_ITEM = "- None"
_QR_INDENT = "    "

# ``### Journal`` subsection literals and its four narrative fields, in order.
_JOURNAL_HEADING = "### Journal"
_JOURNAL_FIELDS: tuple[tuple[str, str], ...] = (
    ("what_we_did", "What we did"),
    ("what_was_produced", "What was produced"),
    ("why_it_matters", "Why it matters"),
    ("bootcamper_takeaway", "Bootcamper's takeaway"),
)


def _extract_list_items(body: str) -> list[str]:
    """Return the bulleted/numbered list items in a subsection body.

    Leading ``- ``/``N. `` markers and surrounding whitespace are stripped while
    the remaining text is preserved. Blank lines, ``---`` separators, and stray
    prose are ignored so a subsection with no list content yields an empty list.

    Args:
        body: The text of a subsection (everything after its ``###`` heading).

    Returns:
        The item texts in document order (empty when there are no list items).
    """
    return [item.strip() for item in _LIST_ITEM_RE.findall(body)]


def _split_subsections(section_text: str) -> dict[str, str]:
    """Split a Recap_Section body into its ``###`` subsections.

    Args:
        section_text: The section text following the ``## Module N:`` heading.

    Returns:
        A map of lowercased subsection name (e.g. ``"information shared"``) to
        its raw body text. When a name repeats, the first occurrence wins.
    """
    subsections: dict[str, str] = {}
    parts = _SUBSECTION_SPLIT_RE.split(section_text)
    # parts == [preamble, name_1, body_1, name_2, body_2, ...]; names sit at the
    # odd indices, each followed by its body.
    for index in range(1, len(parts) - 1, 2):
        name = parts[index].strip().lower()
        subsections.setdefault(name, parts[index + 1])
    return subsections


def _parse_qr_section(body: str) -> list[tuple[str, str]]:
    """Parse a ``### Questions & Responses`` body into ordered ``(q, r)`` pairs.

    Pairs each Question_Item (a line whose leading spaces are followed by the
    ``- **Q:** `` prefix) with the immediately following Response_Item (the
    ``- **R:** `` prefix). The prefixes and the response's four-space indent are
    dropped; continuation lines of a multi-line response fold back into it with
    that indent removed, so parsing is the exact inverse of
    :func:`_render_qr_section`. A ``- None`` body yields zero pairs.

    Args:
        body: The QR_Section body (text after the ``### Questions & Responses``
            heading).

    Returns:
        The ``(question, response)`` pairs in document order.
    """
    pairs: list[tuple[str, str]] = []
    question: str | None = None
    response_lines: list[str] | None = None

    def commit() -> None:
        nonlocal question, response_lines
        if question is not None and response_lines is not None:
            pairs.append((question, "\n".join(response_lines)))
        question = None
        response_lines = None

    # Split on "\n" only (the exact separator the renderer joins with) so this is
    # a true inverse; ``splitlines`` would over-split on Latin-1 line-boundary
    # control characters the renderer treats as ordinary in-line text.
    for line in body.split("\n"):
        content = line.lstrip(" ")
        if content.startswith(_QR_QUESTION_PREFIX):
            commit()
            question = content[len(_QR_QUESTION_PREFIX):]
        elif content.startswith(_QR_RESPONSE_PREFIX) and question is not None:
            response_lines = [content[len(_QR_RESPONSE_PREFIX):]]
        elif response_lines is not None and line.startswith(" "):
            # Indented continuation of the current multi-line response; strip the
            # canonical four-space indent while preserving any deeper indent.
            response_lines.append(line[len(_QR_INDENT):])
        else:
            commit()

    commit()
    return pairs


def _render_qr_section(pairs: list[tuple[str, str]]) -> list[str]:
    """Render ``(q, r)`` pairs as the ``### Questions & Responses`` lines.

    Emits the heading, a blank line, then each pair as a Question_Item directly
    followed by its four-space-indented Response_Item. A multi-line response
    keeps every continuation line at the same indent. With no pairs, the heading
    is followed by a single ``- None`` item.

    Args:
        pairs: Ordered ``(question, response)`` pairs.

    Returns:
        The Markdown lines for the subsection (no trailing blank line).
    """
    lines = [_QR_HEADING, ""]
    if not pairs:
        lines.append(_QR_EMPTY_ITEM)
        return lines
    for question, response in pairs:
        lines.append(f"{_QR_QUESTION_PREFIX}{question}")
        response_lines = ("" if response is None else response).split("\n")
        lines.append(f"{_QR_INDENT}{_QR_RESPONSE_PREFIX}{response_lines[0]}")
        for continuation in response_lines[1:]:
            lines.append(f"{_QR_INDENT}{continuation}")
    return lines


def _extract_journal_subsection(section_text: str) -> JournalFields | None:
    """Parse the ``### Journal`` subsection of a Recap_Section into fields.

    Locates the ``### Journal`` heading and reads the four narrative fields
    (``**What we did:**``, ``**What was produced:**``, ``**Why it matters:**``,
    ``**Bootcamper's takeaway:**``) that follow it, stopping at the next ``##``/
    ``###`` heading. Each field is optional: a missing field yields an empty
    string so an empty-but-present ``### Journal`` still parses to a
    :class:`JournalFields`. When no ``### Journal`` heading is present, returns
    ``None`` (a legacy, pre-consolidation section).

    Args:
        section_text: The section text following the ``## Module N:`` heading.

    Returns:
        The parsed :class:`JournalFields`, or ``None`` when the section has no
        ``### Journal`` subsection.
    """
    heading = re.search(r"^###[ \t]+Journal[ \t]*$", section_text, re.MULTILINE)
    if heading is None:
        return None
    block = section_text[heading.end():]
    # Bound the block to the next heading so a following section's fields never
    # bleed in.
    next_heading = re.search(r"^#{2,3}[ \t]+\S", block, re.MULTILINE)
    if next_heading is not None:
        block = block[: next_heading.start()]

    values: dict[str, str] = {}
    for attr, label in _JOURNAL_FIELDS:
        field_re = re.compile(
            r"^[ \t]*\*\*" + re.escape(label) + r":\*\*[ \t]*(.*?)[ \t]*$",
            re.MULTILINE,
        )
        match = field_re.search(block)
        values[attr] = match.group(1).strip() if match else ""

    return JournalFields(
        what_we_did=values["what_we_did"],
        what_was_produced=values["what_was_produced"],
        why_it_matters=values["why_it_matters"],
        bootcamper_takeaway=values["bootcamper_takeaway"],
    )


def parse_recap_sections(content: str) -> list[ParsedRecapSection]:
    """Parse a Consolidated_Log into structured :class:`ParsedRecapSection` objects.

    Each ``## Module N: [Name]`` heading (with or without a `` \u2014 [timestamp]``
    suffix) starts a section that runs until the next such heading or end of
    file. The recap header block and any content before the first module heading
    are ignored. Missing subsections degrade gracefully: absent list subsections
    yield empty lists, an absent ``### Duration`` yields ``None``, and an absent
    ``### Journal`` yields a ``None`` journal.

    Args:
        content: The full Consolidated_Log Markdown text.

    Returns:
        The sections in document order (empty when the content has no module
        headings).
    """
    sections: list[ParsedRecapSection] = []
    headings = list(_MODULE_HEADING_RE.finditer(content))
    for index, match in enumerate(headings):
        body_start = match.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        section_text = content[body_start:body_end]

        subsections = _split_subsections(section_text)

        duration: str | None = None
        for line in subsections.get("duration", "").splitlines():
            stripped = line.strip()
            if stripped:
                duration = stripped
                break

        sections.append(
            ParsedRecapSection(
                module_number=int(match.group(1)),
                module_name=match.group(2).strip(),
                timestamp=(match.group(3) or "").strip(),
                information_shared=_extract_list_items(
                    subsections.get("information shared", "")
                ),
                questions_responses=_parse_qr_section(
                    subsections.get("questions & responses", "")
                ),
                actions_taken=_extract_list_items(subsections.get("actions taken", "")),
                duration=duration,
                journal=_extract_journal_subsection(section_text),
            )
        )
    return sections


def render_recap_section(section: ParsedRecapSection) -> str:
    """Render a :class:`ParsedRecapSection` back to canonical Consolidated_Log Markdown.

    Produces the ``## Module N:`` heading (appending `` \u2014 [timestamp]`` only
    when a timestamp is present), the ``### Information Shared``,
    ``### Questions & Responses``, and ``### Actions Taken`` subsections, the
    ``### Duration`` subsection only when a duration is set, the ``### Journal``
    subsection only when journal fields are present, and a trailing ``---``
    separator so consecutive sections concatenate cleanly. The output is the
    inverse of :func:`parse_recap_sections` at the structured level.

    Args:
        section: The structured section to render.

    Returns:
        The Markdown for one Recap_Section, terminated by a ``---`` separator and
        a trailing newline.
    """
    lines: list[str] = []

    heading = f"## Module {section.module_number}: {section.module_name}"
    if section.timestamp:
        heading = f"{heading} \u2014 {section.timestamp}"
    lines.append(heading)
    lines.append("")

    lines.append("### Information Shared")
    lines.extend(f"- {item}" for item in section.information_shared)
    lines.append("")

    lines.extend(_render_qr_section(section.questions_responses))
    lines.append("")

    lines.append("### Actions Taken")
    lines.extend(f"- {item}" for item in section.actions_taken)
    lines.append("")

    if section.duration is not None:
        lines.append("### Duration")
        lines.append(section.duration)
        lines.append("")

    if section.journal is not None:
        lines.append(_JOURNAL_HEADING)
        for attr, label in _JOURNAL_FIELDS:
            lines.append(f"**{label}:** {getattr(section.journal, attr)}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


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
    value is supplied (mirroring the hook's no-placeholder rule). Every
    backfilled section carries a consolidated ``### Journal`` subsection whose
    four narrative fields are all ``N/A`` scaffolds, so backfilled content shares
    the Consolidated_Log contract (design Property 3).

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
    parts += ["", _JOURNAL_HEADING]
    parts += [f"**{label}:** N/A" for _, label in _JOURNAL_FIELDS]
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
# Legacy journal -> Consolidated_Log migration (one-time, idempotent)
# ---------------------------------------------------------------------------
#
# The retired Legacy_Journal_File (``docs/bootcamp_journal.md``) carried a
# lighter narrative entry per module: ``## Module N: [Name] \u2014 Completed
# [timestamp]`` followed by the four ``**What we did:**`` / ``**What was
# produced:**`` / ``**Why it matters:**`` / ``**Bootcamper's takeaway:**``
# fields. :func:`migrate_journal_to_recap` folds each such entry into the
# matching Recap_Section as a ``### Journal`` subsection, creating a minimal
# section when the recap has no matching module. The merge is append-around
# (existing recap bytes are preserved; the Journal block is spliced in before a
# section's trailing ``---`` separator) and idempotent (a section that already
# carries a ``### Journal`` subsection is left untouched).

_LEGACY_JOURNAL_HEADING_RE = re.compile(
    r"^##[ \t]+Module[ \t]+(\d+):[ \t]*(.*?)[ \t]*$",
    re.MULTILINE,
)
_JOURNAL_FIELD_LINE_RE = re.compile(r"^[ \t]*\*\*(.+?):\*\*[ \t]*(.*)$")
_JOURNAL_SUBSECTION_RE = re.compile(r"^###[ \t]+Journal[ \t]*$", re.MULTILINE)
_HRULE_RE = re.compile(r"^---[ \t]*$", re.MULTILINE)
_COMPLETED_PREFIX = "Completed "

# Reverse lookup from a journal field label back to its dataclass attribute.
_JOURNAL_LABEL_TO_ATTR = {label: attr for attr, label in _JOURNAL_FIELDS}


@dataclass
class _LegacyEntry:
    """One parsed Legacy_Journal_File module entry.

    Attributes:
        name: The module display name from the journal heading (may be empty).
        timestamp: The completion timestamp from the journal heading, with any
            leading ``Completed `` label stripped (may be empty).
        fields: The four parsed narrative fields.
    """

    name: str
    timestamp: str
    fields: JournalFields


def _split_journal_heading_remainder(remainder: str) -> tuple[str, str]:
    """Split ``[Name] \u2014 Completed [timestamp]`` into ``(name, timestamp)``.

    The em-dash separator and a leading ``Completed `` label on the timestamp
    are both optional; missing parts yield empty strings.

    Args:
        remainder: The heading text following ``## Module N:``.

    Returns:
        A ``(name, timestamp)`` tuple with surrounding whitespace stripped.
    """
    if "\u2014" in remainder:
        name_part, _, ts_part = remainder.partition("\u2014")
        timestamp = ts_part.strip()
        if timestamp.startswith(_COMPLETED_PREFIX):
            timestamp = timestamp[len(_COMPLETED_PREFIX):].strip()
        return name_part.strip(), timestamp
    return remainder.strip(), ""


def _parse_journal_fields(body: str) -> JournalFields:
    """Parse the four narrative fields from one legacy journal entry body.

    Multi-line field values are folded into a single line (joined with spaces)
    to match the canonical single-line ``### Journal`` field form. A field that
    is absent yields an empty string.

    Args:
        body: The entry text following a ``## Module N:`` journal heading.

    Returns:
        The parsed :class:`JournalFields` (empty strings for absent fields).
    """
    collected: dict[str, list[str]] = {attr: [] for attr, _ in _JOURNAL_FIELDS}
    current: str | None = None
    for line in body.split("\n"):
        match = _JOURNAL_FIELD_LINE_RE.match(line)
        if match and match.group(1).strip() in _JOURNAL_LABEL_TO_ATTR:
            current = _JOURNAL_LABEL_TO_ATTR[match.group(1).strip()]
            first = match.group(2).strip()
            collected[current] = [first] if first else []
        elif current is not None:
            stripped = line.strip()
            if stripped.startswith("#") or stripped == "---":
                # A new heading or a separator ends the current field's value.
                current = None
            elif stripped:
                collected[current].append(stripped)
    values = {attr: " ".join(parts).strip() for attr, parts in collected.items()}
    return JournalFields(
        what_we_did=values["what_we_did"],
        what_was_produced=values["what_was_produced"],
        why_it_matters=values["why_it_matters"],
        bootcamper_takeaway=values["bootcamper_takeaway"],
    )


def _parse_legacy_journal(content: str) -> dict[int, _LegacyEntry]:
    """Parse a Legacy_Journal_File into per-module entries.

    Args:
        content: The full ``docs/bootcamp_journal.md`` text.

    Returns:
        A mapping of module number to its parsed :class:`_LegacyEntry`. The first
        occurrence wins if a module heading is duplicated. Content without any
        ``## Module N:`` heading yields an empty mapping.
    """
    entries: dict[int, _LegacyEntry] = {}
    headings = list(_LEGACY_JOURNAL_HEADING_RE.finditer(content))
    for index, match in enumerate(headings):
        module = int(match.group(1))
        if module in entries:
            continue
        body_start = match.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        name, timestamp = _split_journal_heading_remainder(match.group(2).strip())
        entries[module] = _LegacyEntry(
            name=name,
            timestamp=timestamp,
            fields=_parse_journal_fields(content[body_start:body_end]),
        )
    return entries


def _render_journal_block(fields: JournalFields) -> str:
    """Render a ``### Journal`` subsection (heading + four fields) as Markdown.

    Args:
        fields: The narrative fields to render.

    Returns:
        The subsection text ending with a single trailing newline (no trailing
        blank line).
    """
    lines = [_JOURNAL_HEADING]
    lines.extend(f"**{label}:** {getattr(fields, attr)}" for attr, label in _JOURNAL_FIELDS)
    return "\n".join(lines) + "\n"


def _has_journal_subsection(section_text: str) -> bool:
    """Return True when ``section_text`` already contains a ``### Journal`` heading."""
    return _JOURNAL_SUBSECTION_RE.search(section_text) is not None


def _find_recap_section_span(content: str, module: int) -> tuple[int, int] | None:
    """Locate the ``## Module N:`` section span for ``module`` in ``content``.

    Args:
        content: The Consolidated_Log text.
        module: The module number to locate.

    Returns:
        A ``(start, end)`` character span covering the section (heading through
        the byte before the next module heading, or end of file), or ``None`` when
        no section for ``module`` exists.
    """
    headings = list(_SECTION_RE.finditer(content))
    for index, match in enumerate(headings):
        if int(match.group(1)) != module:
            continue
        start = match.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        return start, end
    return None


def _insert_journal_block(section_text: str, journal_block: str) -> str:
    """Splice a ``### Journal`` block into a Recap_Section, preserving its bytes.

    The block is inserted immediately before the section's trailing ``---``
    separator (or at the end of the section when no separator is present) — i.e.
    after the last existing subsection (after ``### Duration`` when present).
    Surrounding blank lines are normalized so the result stays valid CommonMark.

    Args:
        section_text: The full section text (``## Module N:`` heading onward).
        journal_block: The rendered ``### Journal`` block (ends with one newline).

    Returns:
        The section text with the Journal subsection inserted.
    """
    separators = list(_HRULE_RE.finditer(section_text))
    insert_at = separators[-1].start() if separators else len(section_text)
    before = section_text[:insert_at]
    after = section_text[insert_at:]

    if before == "" or before.endswith("\n\n"):
        pad = ""
    elif before.endswith("\n"):
        pad = "\n"
    else:
        pad = "\n\n"

    return f"{before}{pad}{journal_block}\n{after}"


def _render_migration_section(module: int, entry: _LegacyEntry) -> str:
    """Render a minimal Recap_Section carrying a migrated ``### Journal`` block.

    Used when the Legacy_Journal_File has an entry for a module the recap does
    not yet cover. Placeholder ``N/A`` subsections stand in for the session
    content the journal never captured; the ``### Journal`` subsection carries
    the migrated narrative fields.

    Args:
        module: The module number.
        entry: The parsed legacy journal entry.

    Returns:
        The section Markdown, beginning and ending with a newline so it appends
        cleanly after existing content without rewriting it.
    """
    label = entry.name if entry.name else f"Module {module}"
    heading = f"## Module {module}: {label}"
    if entry.timestamp:
        heading = f"{heading} \u2014 {entry.timestamp}"
    parts = [
        "",
        heading,
        "",
        "### Information Shared",
        "- N/A (section created during journal migration; original session content unavailable)",
        "",
        _QR_HEADING,
        _QR_EMPTY_ITEM,
        "",
        "### Actions Taken",
        "- N/A",
        "",
        _JOURNAL_HEADING,
    ]
    parts.extend(
        f"**{label}:** {getattr(entry.fields, attr)}" for attr, label in _JOURNAL_FIELDS
    )
    parts += ["", "---", ""]
    return "\n".join(parts)


def migrate_journal_to_recap(recap_path: str, journal_path: str) -> MigrationReport:
    """Merge Legacy_Journal_File entries into the Consolidated_Log recap.

    Parses ``journal_path`` into per-module narrative entries and folds each into
    the matching ``## Module N:`` section of ``recap_path`` as a ``### Journal``
    subsection. When the recap has no matching section, a minimal one is created
    so no journal content is lost. The operation is append-around (existing recap
    bytes are preserved) and idempotent (a section that already carries a
    ``### Journal`` subsection is skipped, so re-running makes no changes).

    Error handling:
        * Journal absent or unreadable: no-op; returns an empty report.
        * Journal with no parseable entries: no-op; returns an empty report.
        * Recap absent: created with a minimal header, then migration proceeds.
        * Recap not writable: the underlying :class:`OSError` propagates.

    Args:
        recap_path: Path to ``docs/bootcamp_recap.md`` (the Consolidated_Log).
        journal_path: Path to the legacy ``docs/bootcamp_journal.md``.

    Returns:
        A :class:`MigrationReport` recording the modules merged, created, and
        skipped as already consolidated.

    Raises:
        OSError: If the recap file exists or must be created but cannot be written.
    """
    report = MigrationReport(journal_path=journal_path)

    journal_file = Path(journal_path)
    if not journal_file.is_file():
        return report
    try:
        journal_content = journal_file.read_text(encoding="utf-8")
    except OSError:
        return report

    entries = _parse_legacy_journal(journal_content)
    if not entries:
        return report

    recap_file = Path(recap_path)
    recap_content = (
        recap_file.read_text(encoding="utf-8") if recap_file.is_file() else _RECAP_HEADER
    )

    changed = False
    for module in sorted(entries):
        entry = entries[module]
        span = _find_recap_section_span(recap_content, module)
        if span is None:
            section = _render_migration_section(module, entry)
            prefix = recap_content if recap_content.endswith("\n") else recap_content + "\n"
            recap_content = prefix + section
            report.modules_created.append(module)
            changed = True
            continue
        start, end = span
        section_text = recap_content[start:end]
        if _has_journal_subsection(section_text):
            report.already_consolidated.append(module)
            continue
        merged = _insert_journal_block(section_text, _render_journal_block(entry.fields))
        recap_content = recap_content[:start] + merged + recap_content[end:]
        report.modules_merged.append(module)
        changed = True

    if changed:
        recap_file.parent.mkdir(parents=True, exist_ok=True)
        recap_file.write_text(recap_content, encoding="utf-8")

    return report


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
    parser.add_argument(
        "--journal",
        help=(
            "Path to the legacy docs/bootcamp_journal.md. Deprecated and ignored "
            "for --plan/--check/--backfill (journal content is now part of the "
            "consolidated recap); still required by --migrate to locate the "
            "legacy file."
        ),
    )
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
    mode.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "Merge the legacy journal (--journal) into the consolidated recap "
            "(--recap) as a '### Journal' subsection per module (idempotent)."
        ),
    )
    args = parser.parse_args(argv)

    # --- Migration mode (independent of progress state) ---
    if args.migrate:
        if not args.recap:
            print("--migrate requires --recap", file=sys.stderr)
            sys.exit(1)
        if not args.journal:
            print("--migrate requires --journal", file=sys.stderr)
            sys.exit(1)
        try:
            report = migrate_journal_to_recap(args.recap, args.journal)
        except OSError as exc:
            print(f"Journal-to-recap migration failed: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Modules merged:           {report.modules_merged}")
        print(f"Modules created:          {report.modules_created}")
        print(f"Already consolidated:     {report.already_consolidated}")
        sys.exit(0)

    # --- Deprecation notice for the retired --journal argument ---
    # Outside --migrate, journal content is now part of the consolidated recap,
    # so the planner/check/plan/backfill paths ignore --journal entirely.
    if args.journal:
        print(
            "Warning: --journal is deprecated; journal content is now part of "
            "the consolidated recap.",
            file=sys.stderr,
        )

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

    certificates: set[int] = set()
    if args.progress_dir:
        certificates = _discover_certificates(Path(args.progress_dir))

    # Journal entries are no longer discovered: journal content is consolidated
    # into each recap section, so the inventory leaves journal_entries empty.
    inventory = ArtifactInventory(
        recap_sections=_discover_section_modules(recap_content),
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
