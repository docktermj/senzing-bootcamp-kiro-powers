#!/usr/bin/env python3
"""Report and validate per-language supplementary-example coverage.

This script reads the canonical Coverage_Record
(`senzing-bootcamp/config/example-coverage.yaml`) and produces a per-language
coverage report, regenerates the `example-coverage` disclosure region in
`POWER.md`, and validates the record schema plus disclosure consistency.

The Coverage_Record is a maintainer-curated snapshot of observed Senzing MCP
`find_examples` results. This script never queries the MCP server and the record
never contains MCP URLs (those live only in `mcp.json`).

Usage:
    python scripts/example_coverage_report.py                # text report
    python scripts/example_coverage_report.py --format json  # machine-readable
    python scripts/example_coverage_report.py --write        # regenerate POWER.md region
    python scripts/example_coverage_report.py --check        # validate (CI gate)

Requires only the Python standard library, plus PyYAML which is imported lazily
inside `load_coverage_record` (consistent with `validate_dependencies.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants and paths
# ---------------------------------------------------------------------------

#: The only valid Coverage_Status values. Shared by validation and report
#: counting so the two can never diverge.
VALID_STATUSES = ("available", "none", "unknown")

#: Power root is the parent of the ``scripts/`` directory holding this file.
POWER_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RECORD_PATH = POWER_ROOT / "config" / "example-coverage.yaml"
DEFAULT_POWER_MD_PATH = POWER_ROOT / "POWER.md"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class CoverageError(Exception):
    """Raised when the Coverage_Record is missing, unparseable, or malformed."""


class MarkerError(CoverageError):
    """Raised when the ``example-coverage`` markers in POWER.md are missing or unpaired.

    Subclasses :class:`CoverageError` so callers that already handle coverage
    errors map marker integrity problems to the same non-zero exit and leave
    POWER.md byte-for-byte unchanged.
    """


# ---------------------------------------------------------------------------
# In-memory data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Snapshot:
    """Provenance for when the coverage data was last observed."""

    last_observed: str
    senzing_version: str


@dataclass(frozen=True)
class CoverageRecord:
    """The parsed Coverage_Record.

    Attributes:
        languages: Tracked Supported_Language keys, in declared order.
        topics: Mapping of topic id to its human-readable label.
        coverage: Mapping of language -> {topic -> Coverage_Status}.
        snapshot: Snapshot_Metadata for the record.
    """

    languages: tuple[str, ...]
    topics: dict[str, str]
    coverage: dict[str, dict[str, str]]
    snapshot: Snapshot


@dataclass(frozen=True)
class LanguageSummary:
    """Per-language report figures."""

    language: str
    counts: dict[str, int]
    gaps: tuple[str, ...]
    available_proportion: float


@dataclass(frozen=True)
class Report:
    """The computed per-language report model."""

    languages: tuple[LanguageSummary, ...]
    snapshot: Snapshot


@dataclass(frozen=True)
class Violation:
    """A single schema or disclosure-drift finding."""

    description: str


# ---------------------------------------------------------------------------
# Loading and parsing
# ---------------------------------------------------------------------------

def _resolve_record_path(path: Path | str | None) -> Path:
    """Resolve a record path relative to the script location.

    Args:
        path: An explicit path (absolute or relative), or ``None`` for the
            default record location. Relative paths are resolved against the
            power root so the script behaves identically regardless of the
            current working directory.

    Returns:
        The resolved absolute path to the Coverage_Record.
    """
    if path is None:
        return DEFAULT_RECORD_PATH
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = POWER_ROOT / candidate
    return candidate


def _build_record(data: dict) -> CoverageRecord:
    """Construct a CoverageRecord from a parsed YAML mapping.

    This is intentionally defensive: missing or oddly-typed fields are coerced
    to safe empty defaults rather than raising, because schema problems are
    reported by ``validate_record`` (not by the loader).

    Args:
        data: The top-level mapping parsed from the Coverage_Record YAML.

    Returns:
        A populated :class:`CoverageRecord`.
    """
    raw_languages = data.get("languages") or []
    languages = (
        tuple(str(lang) for lang in raw_languages)
        if isinstance(raw_languages, list)
        else ()
    )

    topics: dict[str, str] = {}
    raw_topics = data.get("topics")
    if isinstance(raw_topics, dict):
        for topic_id, topic_data in raw_topics.items():
            label = ""
            if isinstance(topic_data, dict):
                label = str(topic_data.get("label", "") or "")
            topics[str(topic_id)] = label

    coverage: dict[str, dict[str, str]] = {}
    raw_coverage = data.get("coverage")
    if isinstance(raw_coverage, dict):
        for lang, entries in raw_coverage.items():
            if isinstance(entries, dict):
                coverage[str(lang)] = {
                    str(topic): str(status) for topic, status in entries.items()
                }
            else:
                coverage[str(lang)] = {}

    metadata = data.get("metadata")
    snapshot_data: dict = {}
    if isinstance(metadata, dict) and isinstance(metadata.get("snapshot"), dict):
        snapshot_data = metadata["snapshot"]
    snapshot = Snapshot(
        last_observed=str(snapshot_data.get("last_observed", "") or ""),
        senzing_version=str(snapshot_data.get("senzing_version", "") or ""),
    )

    return CoverageRecord(
        languages=languages,
        topics=topics,
        coverage=coverage,
        snapshot=snapshot,
    )


def load_coverage_record(path: Path | str | None = None) -> CoverageRecord:
    """Read and parse the Coverage_Record YAML.

    PyYAML is imported inside this function, not at module top level, keeping the
    module stdlib-only at import time (consistent with ``validate_dependencies.py``).

    Args:
        path: Optional override for the record path. Relative paths resolve
            against the power root; ``None`` uses the default record location.

    Returns:
        The parsed :class:`CoverageRecord`.

    Raises:
        CoverageError: If the file is missing, cannot be parsed as YAML, or its
            top-level value is not a mapping.
    """
    import yaml  # lazy import: PyYAML is the only non-stdlib dependency

    record_path = _resolve_record_path(path)
    if not record_path.exists():
        raise CoverageError(f"coverage record not found: {record_path}")

    try:
        with open(record_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise CoverageError(f"cannot parse coverage record: {exc}") from exc

    if not isinstance(data, dict):
        raise CoverageError(
            f"coverage record top level must be a mapping: {record_path}"
        )

    return _build_record(data)


# ---------------------------------------------------------------------------
# Schema validation and language ranking
# ---------------------------------------------------------------------------

def validate_record(record: CoverageRecord) -> list[Violation]:
    """Return all schema violations for a Coverage_Record; empty means valid.

    The record is validated against the in-memory :class:`CoverageRecord` model.
    Because :func:`load_coverage_record` coerces missing snapshot fields and
    missing topic labels to the empty string, an empty value is treated as a
    missing (and therefore violating) field.

    Checks performed (Requirements 1.4-1.6, 2.4, 7.1-7.3):
        - every coverage entry status is one of :data:`VALID_STATUSES`
        - a coverage entry exists for every (language, topic) combination
        - required Snapshot_Metadata fields (``last_observed``, ``senzing_version``)
          are present
        - every tracked topic has a human-readable label

    Args:
        record: The parsed Coverage_Record to validate.

    Returns:
        A list of :class:`Violation`; an empty list means the record is valid.
    """
    violations: list[Violation] = []

    # Completeness: one coverage entry per (language, topic) pair (Req 1.4, 7.2).
    # Status value constraint: each entry is a valid status (Req 1.5, 7.1).
    for language in record.languages:
        lang_entries = record.coverage.get(language, {})
        for topic_id in record.topics:
            if topic_id not in lang_entries:
                violations.append(
                    Violation(
                        f"missing coverage entry for language '{language}', "
                        f"topic '{topic_id}'"
                    )
                )
                continue
            status = lang_entries[topic_id]
            if status not in VALID_STATUSES:
                violations.append(
                    Violation(
                        f"invalid status '{status}' for language '{language}', "
                        f"topic '{topic_id}' (expected one of "
                        f"{', '.join(VALID_STATUSES)})"
                    )
                )

    # Required Snapshot_Metadata fields present (Req 1.6, 7.3).
    if not record.snapshot.last_observed:
        violations.append(
            Violation("missing required snapshot field 'last_observed'")
        )
    if not record.snapshot.senzing_version:
        violations.append(
            Violation("missing required snapshot field 'senzing_version'")
        )

    # Every tracked topic has a human-readable label (Req 2.4, 7.3).
    for topic_id, label in record.topics.items():
        if not label:
            violations.append(
                Violation(f"topic '{topic_id}' is missing a human-readable label")
            )

    return violations


def derive_ranking(record: CoverageRecord) -> list[str]:
    """Return languages ordered by ``available`` proportion, descending.

    Ties are broken by the language order declared in the record, so the result
    is deterministic. Used for both the disclosure and ``--check``.

    Args:
        record: The parsed Coverage_Record to rank.

    Returns:
        The tracked languages ordered from highest to lowest ``available``
        proportion, with declared order as the tie-breaker.
    """
    topic_count = len(record.topics)

    def available_proportion(language: str) -> float:
        if topic_count == 0:
            return 0.0
        lang_entries = record.coverage.get(language, {})
        available = sum(
            1 for status in lang_entries.values() if status == "available"
        )
        return available / topic_count

    declared_order = {lang: index for index, lang in enumerate(record.languages)}
    return sorted(
        record.languages,
        key=lambda lang: (-available_proportion(lang), declared_order[lang]),
    )


# ---------------------------------------------------------------------------
# Report computation and rendering
# ---------------------------------------------------------------------------

#: Honest-scope statement included in every report rendering (Req 6.3). States
#: the report reflects supplementary example availability only and does not
#: reflect generate_scaffold / sdk_guide output quality, which are equivalent
#: across all supported languages.
HONEST_SCOPE_STATEMENT = (
    "This report reflects supplementary example availability only. It does NOT "
    "reflect generate_scaffold or sdk_guide output quality, which are equivalent "
    "across all supported languages."
)


def build_report(record: CoverageRecord) -> Report:
    """Compute the per-language report model from a Coverage_Record.

    For each tracked language (in declared order) this computes:
        - a status count covering every value in :data:`VALID_STATUSES`
          (0 when a status is absent for that language) (Req 3.4)
        - the gap list: topics whose status is ``none`` or ``unknown``, in
          declared topic order (Req 3.5)
        - ``available_proportion``: the fraction of tracked topics with status
          ``available``; 0.0 when there are no topics (never raises
          ``ZeroDivisionError``) (Req 8.1)

    Args:
        record: The parsed Coverage_Record to summarize.

    Returns:
        A :class:`Report` carrying one :class:`LanguageSummary` per tracked
        language (in declared order) plus the record's Snapshot_Metadata.
    """
    topic_count = len(record.topics)
    summaries: list[LanguageSummary] = []

    for language in record.languages:
        lang_entries = record.coverage.get(language, {})

        counts: dict[str, int] = {status: 0 for status in VALID_STATUSES}
        for topic_id in record.topics:
            status = lang_entries.get(topic_id)
            if status in counts:
                counts[status] += 1

        gaps = tuple(
            topic_id
            for topic_id in record.topics
            if lang_entries.get(topic_id) in ("none", "unknown")
        )

        available_proportion = (
            counts["available"] / topic_count if topic_count else 0.0
        )

        summaries.append(
            LanguageSummary(
                language=language,
                counts=counts,
                gaps=gaps,
                available_proportion=available_proportion,
            )
        )

    return Report(languages=tuple(summaries), snapshot=record.snapshot)


def render_report_text(report: Report) -> str:
    """Render the human-readable coverage report.

    The text includes the Snapshot_Metadata (``last_observed`` and
    ``senzing_version``), the honest-scope statement (Req 6.3), and a per-language
    section with status counts, the gap list, and the available proportion.

    Args:
        report: The computed report model.

    Returns:
        The human-readable report as a single string.
    """
    lines: list[str] = []
    lines.append("Language Example Coverage Report")
    lines.append("=" * 32)
    lines.append("")
    lines.append("Snapshot_Metadata:")
    lines.append(f"  last_observed:   {report.snapshot.last_observed}")
    lines.append(f"  senzing_version: {report.snapshot.senzing_version}")
    lines.append("")
    lines.append(HONEST_SCOPE_STATEMENT)
    lines.append("")

    if not report.languages:
        lines.append("(no languages tracked)")
        return "\n".join(lines) + "\n"

    for summary in report.languages:
        counts = summary.counts
        proportion_pct = summary.available_proportion * 100
        lines.append(f"{summary.language}")
        lines.append(
            "  counts: "
            + ", ".join(f"{status}={counts[status]}" for status in VALID_STATUSES)
        )
        lines.append(
            f"  available_proportion: {summary.available_proportion:.3f} "
            f"({proportion_pct:.1f}%)"
        )
        if summary.gaps:
            lines.append(f"  gaps (none/unknown): {', '.join(summary.gaps)}")
        else:
            lines.append("  gaps (none/unknown): none")
        lines.append("")

    return "\n".join(lines) + "\n"


def render_report_json(report: Report) -> str:
    """Render the coverage report as structured, stable-keyed JSON.

    The output uses sorted keys so it is stable across runs and suitable for
    cross-snapshot comparison (Req 8.2). Each language carries its status counts,
    its gap list, and its ``available_proportion``. Snapshot metadata and the
    honest-scope statement are included at the top level.

    Args:
        report: The computed report model.

    Returns:
        A JSON document (with a trailing newline) as a string.
    """
    payload = {
        "honest_scope": HONEST_SCOPE_STATEMENT,
        "snapshot": {
            "last_observed": report.snapshot.last_observed,
            "senzing_version": report.snapshot.senzing_version,
        },
        "languages": {
            summary.language: {
                "counts": dict(summary.counts),
                "gaps": list(summary.gaps),
                "available_proportion": summary.available_proportion,
            }
            for summary in report.languages
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Disclosure region rendering and verification
# ---------------------------------------------------------------------------
#
# The disclosure uses the same marker scheme as ``generate_power_docs.py``: a
# pair of CommonMark HTML comments carrying a stable region id, matched with an
# anchored, whitespace-tolerant regex (``re.MULTILINE``). Only the text strictly
# between the begin and end markers is ever rewritten; the markers themselves and
# every other byte of POWER.md are left untouched.

#: The region id shared by the begin/end markers in POWER.md.
DISCLOSURE_REGION_ID = "example-coverage"

_BEGIN_MARKER_RE = re.compile(
    r"^<!--\s*BEGIN GENERATED:\s*(?P<id>[a-z0-9-]+)\s*-->\s*$",
    re.MULTILINE,
)
_END_MARKER_RE = re.compile(
    r"^<!--\s*END GENERATED:\s*(?P<id>[a-z0-9-]+)\s*-->\s*$",
    re.MULTILINE,
)


def _join_languages(names: list[str]) -> str:
    """Join language names into a deterministic, human-readable list.

    Each name is wrapped in backticks (it is a record identifier). One name is
    returned as-is; two are joined with ``and``; three or more use an Oxford
    comma.

    Args:
        names: Language identifiers to join, in ranking order.

    Returns:
        The joined phrase, or the empty string when ``names`` is empty.
    """
    quoted = [f"`{name}`" for name in names]
    if not quoted:
        return ""
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"
    return ", ".join(quoted[:-1]) + f", and {quoted[-1]}"


def _top_ranked_languages(record: CoverageRecord) -> list[str]:
    """Return every language tied for the highest ``available`` proportion.

    Uses :func:`derive_ranking` for the deterministic order, then keeps the
    leading run of languages whose ``available`` proportion equals the maximum.
    When no topics are tracked every proportion is 0.0, so all languages tie.

    Args:
        record: The parsed Coverage_Record to rank.

    Returns:
        The top-ranked languages in deterministic ranking order; empty when the
        record tracks no languages.
    """
    ranking = derive_ranking(record)
    if not ranking:
        return []

    topic_count = len(record.topics)

    def available_proportion(language: str) -> float:
        if topic_count == 0:
            return 0.0
        lang_entries = record.coverage.get(language, {})
        available = sum(
            1 for status in lang_entries.values() if status == "available"
        )
        return available / topic_count

    top_proportion = available_proportion(ranking[0])
    return [
        language
        for language in ranking
        if available_proportion(language) == top_proportion
    ]


def render_disclosure(record: CoverageRecord) -> str:
    """Render the deterministic Markdown body for the ``example-coverage`` region.

    The body is the text placed strictly between the region markers. It always:
        - names the top-ranked language(s) by ``available`` proportion (Req 4.1)
        - states the tracked signal reflects supplementary example availability
          only (Req 6.1)
        - states ``generate_scaffold`` and ``sdk_guide`` produce equivalent
          results for all supported languages (Req 6.2)

    The output is a pure function of ``record`` (same record -> same body), so it
    can be compared byte-for-byte against the committed region in
    :func:`check_disclosure`.

    Args:
        record: The parsed Coverage_Record to render.

    Returns:
        The Markdown region body, including the leading and trailing blank lines
        that surround it between the markers.
    """
    top_languages = _top_ranked_languages(record)
    if not top_languages:
        coverage_clause = (
            "> **Note:** No languages are currently tracked for supplementary "
            "example coverage."
        )
    else:
        joined = _join_languages(top_languages)
        verb = "has" if len(top_languages) == 1 else "have"
        coverage_clause = (
            f"> **Note:** Based on the tracked coverage snapshot, {joined} "
            f"currently {verb} the most extensive supplementary example coverage "
            "(availability observed via `find_examples`)."
        )

    note = "\n".join(
        (
            coverage_clause,
            "> This tracked coverage signal reflects supplementary example "
            "availability only.",
            "> `generate_scaffold` and `sdk_guide` produce equivalent results for "
            "all supported languages.",
        )
    )
    return f"\n{note}\n\n"


def _locate_disclosure_region(doc: str) -> tuple[int, int]:
    """Locate the ``example-coverage`` region body offsets within a POWER.md doc.

    Scans for the begin/end markers carrying :data:`DISCLOSURE_REGION_ID` and
    validates that exactly one correctly-ordered pair is present.

    Args:
        doc: The full POWER.md document text.

    Returns:
        A pair ``(begin_marker_end, end_marker_start)`` of character offsets:
        the offset just after the begin marker's newline and the offset at which
        the end marker line begins. The region body is ``doc[begin:end]``.

    Raises:
        MarkerError: If the begin/end markers are missing, duplicated, or
            misordered.
    """
    begins = [
        match
        for match in _BEGIN_MARKER_RE.finditer(doc)
        if match.group("id") == DISCLOSURE_REGION_ID
    ]
    ends = [
        match
        for match in _END_MARKER_RE.finditer(doc)
        if match.group("id") == DISCLOSURE_REGION_ID
    ]
    if len(begins) != 1 or len(ends) != 1:
        raise MarkerError(
            f"POWER.md must contain exactly one '{DISCLOSURE_REGION_ID}' "
            f"begin/end marker pair (found {len(begins)} begin, {len(ends)} end)"
        )

    begin_match, end_match = begins[0], ends[0]
    if begin_match.start() >= end_match.start():
        raise MarkerError(
            f"POWER.md '{DISCLOSURE_REGION_ID}' end marker appears before its "
            "begin marker"
        )

    newline_index = doc.find("\n", begin_match.start())
    begin_marker_end = len(doc) if newline_index == -1 else newline_index + 1
    return begin_marker_end, end_match.start()


def _write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically via a temp file and ``os.replace``.

    The content is written to a temporary file in the same directory and then
    renamed over the target, so no reader ever observes a partial write: either
    the previous content or the complete new content is present.

    Args:
        path: The destination file to write.
        content: The full text to write.

    Raises:
        OSError: If the temporary file cannot be created, written, or renamed.
    """
    directory = path.parent
    fd, tmp_name = tempfile.mkstemp(
        dir=directory, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as tmp_file:
            tmp_file.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def write_disclosure_region(power_md: Path | str, body: str) -> None:
    """Replace only the ``example-coverage`` region body in POWER.md.

    Everything outside the begin/end markers — including the markers themselves —
    is left byte-for-byte unchanged (Req 4.4). The replacement is written
    atomically (temp file + :func:`os.replace`); when the body already matches,
    the file is left untouched.

    Args:
        power_md: Path to the POWER.md document to update.
        body: The new region body (typically from :func:`render_disclosure`).

    Raises:
        MarkerError: If the ``example-coverage`` markers are missing or unpaired.
        CoverageError: If POWER.md cannot be read.
    """
    power_md = Path(power_md)
    try:
        doc = power_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoverageError(f"cannot read POWER.md: {exc}") from exc

    begin_marker_end, end_marker_start = _locate_disclosure_region(doc)
    new_doc = doc[:begin_marker_end] + body + doc[end_marker_start:]
    if new_doc != doc:
        _write_atomic(power_md, new_doc)


def check_disclosure(power_md: Path | str, record: CoverageRecord) -> list[Violation]:
    """Compare the committed disclosure region to :func:`render_disclosure`.

    Reads the body strictly between the ``example-coverage`` markers and compares
    it to the body the record would render. A mismatch means the committed prose
    has drifted from the tracked record (Req 4.1, 4.2).

    Args:
        power_md: Path to the POWER.md document to check.
        record: The Coverage_Record the disclosure must reflect.

    Returns:
        A list with a single drift :class:`Violation` when the committed region
        differs from the rendered body; an empty list when they match.

    Raises:
        MarkerError: If the ``example-coverage`` markers are missing or unpaired.
        CoverageError: If POWER.md cannot be read.
    """
    power_md = Path(power_md)
    try:
        doc = power_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoverageError(f"cannot read POWER.md: {exc}") from exc

    begin_marker_end, end_marker_start = _locate_disclosure_region(doc)
    committed_body = doc[begin_marker_end:end_marker_start]
    expected_body = render_disclosure(record)
    if committed_body != expected_body:
        return [
            Violation(
                f"POWER.md '{DISCLOSURE_REGION_ID}' disclosure region is out of "
                "date with the coverage record; regenerate it with: "
                "example_coverage_report.py --write"
            )
        ]
    return []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _resolve_power_md_path(path: Path | str | None) -> Path:
    """Resolve a POWER.md path relative to the script location.

    Mirrors :func:`_resolve_record_path`: an explicit relative path is resolved
    against the power root so the script behaves identically regardless of the
    current working directory; ``None`` uses the default POWER.md location.

    Args:
        path: An explicit path (absolute or relative), or ``None`` for the
            default POWER.md location.

    Returns:
        The resolved absolute path to POWER.md.
    """
    if path is None:
        return DEFAULT_POWER_MD_PATH
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = POWER_ROOT / candidate
    return candidate


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the CLI.

    The full mode dispatch (report / json / write / check) is wired in a later
    task; this skeleton declares the options so the interface is stable.
    """
    parser = argparse.ArgumentParser(
        description="Report and validate per-language example coverage.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report output format (default: text)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate the POWER.md example-coverage disclosure region",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the record schema and disclosure consistency",
    )
    parser.add_argument(
        "--record",
        default=None,
        help="override the Coverage_Record path (testing)",
    )
    parser.add_argument(
        "--power-md",
        dest="power_md",
        default=None,
        help="override the POWER.md path (testing)",
    )
    return parser


def _run_report(args: argparse.Namespace) -> int:
    """Report mode: load the record, build the report, and print it.

    Args:
        args: Parsed CLI arguments (uses ``args.record`` and ``args.format``).

    Returns:
        0 on success; 1 if the record is missing or unparseable.
    """
    try:
        record = load_coverage_record(args.record)
    except CoverageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    report = build_report(record)
    if args.format == "json":
        output = render_report_json(report)
    else:
        output = render_report_text(report)
    sys.stdout.write(output)
    return 0


def _run_write(args: argparse.Namespace) -> int:
    """Write mode: regenerate the POWER.md disclosure region from the record.

    Args:
        args: Parsed CLI arguments (uses ``args.record`` and ``args.power_md``).

    Returns:
        0 on success; 1 if the record cannot be loaded or the POWER.md markers
        are missing/unpaired.
    """
    try:
        record = load_coverage_record(args.record)
    except CoverageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    power_md = _resolve_power_md_path(args.power_md)
    body = render_disclosure(record)
    try:
        write_disclosure_region(power_md, body)
    except CoverageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Updated '{DISCLOSURE_REGION_ID}' disclosure region in {power_md}")
    return 0


def _run_check(args: argparse.Namespace) -> int:
    """Check mode (Coverage_Validator): validate schema and disclosure.

    Loads the record, runs schema validation, and verifies the POWER.md
    disclosure region is consistent with the record. Each violation is printed to
    stderr. Returns non-zero on any schema violation, disclosure drift, or load
    error (Req 4.2, 7.4).

    Args:
        args: Parsed CLI arguments (uses ``args.record`` and ``args.power_md``).

    Returns:
        0 only when the record is schema-valid and the disclosure is consistent;
        1 otherwise.
    """
    try:
        record = load_coverage_record(args.record)
    except CoverageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    violations = list(validate_record(record))

    power_md = _resolve_power_md_path(args.power_md)
    try:
        violations.extend(check_disclosure(power_md, record))
    except CoverageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if violations:
        for violation in violations:
            print(f"error: {violation.description}", file=sys.stderr)
        print(
            f"error: {len(violations)} coverage validation "
            f"{'violation' if len(violations) == 1 else 'violations'} found",
            file=sys.stderr,
        )
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    """argparse-based entry point dispatching the report / write / check modes.

    Mode precedence is ``--check`` first (the CI gate), then ``--write``, then the
    default report mode (text, or JSON with ``--format json``). ``--check`` and
    ``--write`` are distinct modes; when both are given, ``--check`` wins.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        0 on success, 1 on any error or validation/disclosure violation
        (Req 3.6, 3.7, 4.2, 7.4).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.check:
        return _run_check(args)
    if args.write:
        return _run_write(args)
    return _run_report(args)


if __name__ == "__main__":
    sys.exit(main())
