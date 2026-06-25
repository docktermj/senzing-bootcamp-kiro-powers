#!/usr/bin/env python3
"""Generate a 'Complete Artifact Inventory' section for the graduation report.

Reads the bootcamper's progress (config/bootcamp_progress.json) and scans their
project against a known artifact catalog, emitting a Markdown
"Complete Artifact Inventory" section grouped by phase. Each artifact is
annotated with a why-it-matters note and a carry-forward / leave-behind
classification. Only artifacts that actually exist on disk are listed.

Usage:
    python senzing-bootcamp/scripts/generate_artifact_inventory.py
    python senzing-bootcamp/scripts/generate_artifact_inventory.py --project-root .
    python senzing-bootcamp/scripts/generate_artifact_inventory.py --output inventory.md
    python senzing-bootcamp/scripts/generate_artifact_inventory.py --show-missing
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CatalogArtifact:
    """A known bootcamp artifact and its inventory metadata.

    Attributes:
        path: Project-relative path or directory the bootcamp produces.
        kind: "file" or "dir".
        phase: Phase grouping label for the inventory.
        module: Owning module number, or None for bootcamp-wide records.
        classification: "carry-forward" or "leave-behind".
        why_it_matters: Short note on the artifact's purpose and ongoing use.
    """

    path: str
    kind: str
    phase: str
    module: int | None
    classification: str
    why_it_matters: str


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

#: Canonical ordering of inventory phase groupings.
PHASE_ORDER: list[str] = [
    "Discovery & Data Collection",
    "Setup & Verification",
    "Mapping & Processing",
    "Querying & Visualization",
    "Production Readiness",
    "Bootcamp Records",
]

#: Static catalog of known bootcamp artifacts.
#:
#: The module->path entries mirror every ``path:`` under ``modules:`` in
#: ``config/module-artifacts.yaml`` (a drift-guard test enforces this), enriched
#: with phase, classification, and a why-it-matters note. The ``module=None``
#: "Bootcamp Records" entries are bootcamp-wide artifacts produced by the
#: completion / graduation flows rather than a single module's ``produces`` block.
ARTIFACT_CATALOG: list[CatalogArtifact] = [
    # --- Discovery & Data Collection ---
    CatalogArtifact(
        path="docs/business_problem.md",
        kind="file",
        phase="Discovery & Data Collection",
        module=1,
        classification="carry-forward",
        why_it_matters="Defines the ER problem and scope you set out to solve.",
    ),
    CatalogArtifact(
        path="config/data_sources.yaml",
        kind="file",
        phase="Discovery & Data Collection",
        module=1,
        classification="carry-forward",
        why_it_matters="Registry of sources you resolve; drives mapping and loading.",
    ),
    CatalogArtifact(
        path="data/raw/",
        kind="dir",
        phase="Discovery & Data Collection",
        module=4,
        classification="leave-behind",
        why_it_matters="Unprocessed source data; bootcamp input, excluded from production.",
    ),
    # --- Setup & Verification ---
    CatalogArtifact(
        path="database/G2C.db",
        kind="file",
        phase="Setup & Verification",
        module=2,
        classification="leave-behind",
        why_it_matters="SQLite eval database; replace with a production datastore.",
    ),
    CatalogArtifact(
        path="config/engine_config.json",
        kind="file",
        phase="Setup & Verification",
        module=2,
        classification="carry-forward",
        why_it_matters="Senzing engine config; repoint at production DB/license.",
    ),
    CatalogArtifact(
        path="config/bootcamp_preferences.yaml",
        kind="file",
        phase="Setup & Verification",
        module=2,
        classification="leave-behind",
        why_it_matters="Records your language/style choices; bootcamp-only.",
    ),
    CatalogArtifact(
        path="sdk_installed",
        kind="file",
        phase="Setup & Verification",
        module=2,
        classification="leave-behind",
        why_it_matters="Marks that the Senzing SDK is installed and importable.",
    ),
    CatalogArtifact(
        path="src/system_verification/",
        kind="dir",
        phase="Setup & Verification",
        module=3,
        classification="carry-forward",
        why_it_matters="Verification scripts + web service scaffolding; reusable checks.",
    ),
    CatalogArtifact(
        path="docs/progress/MODULE_3_COMPLETE.md",
        kind="file",
        phase="Setup & Verification",
        module=3,
        classification="leave-behind",
        why_it_matters="Completion marker for Module 3; bootcamp progress state.",
    ),
    # --- Mapping & Processing ---
    CatalogArtifact(
        path="data/transformed/",
        kind="dir",
        phase="Mapping & Processing",
        module=5,
        classification="carry-forward",
        why_it_matters="Senzing-ready mapped data; copied into production.",
    ),
    CatalogArtifact(
        path="src/load/",
        kind="dir",
        phase="Mapping & Processing",
        module=6,
        classification="carry-forward",
        why_it_matters="Loading programs; production code.",
    ),
    # --- Querying & Visualization ---
    CatalogArtifact(
        path="src/query/",
        kind="dir",
        phase="Querying & Visualization",
        module=7,
        classification="carry-forward",
        why_it_matters="Query programs and visualizations; production code.",
    ),
    # --- Production Readiness ---
    CatalogArtifact(
        path="tests/performance/",
        kind="dir",
        phase="Production Readiness",
        module=8,
        classification="carry-forward",
        why_it_matters="Performance/benchmark tests.",
    ),
    CatalogArtifact(
        path="docs/security_checklist.md",
        kind="file",
        phase="Production Readiness",
        module=9,
        classification="carry-forward",
        why_it_matters="Security assessment checklist to work through.",
    ),
    CatalogArtifact(
        path="monitoring/",
        kind="dir",
        phase="Production Readiness",
        module=10,
        classification="leave-behind",
        why_it_matters="Monitoring config; review before production.",
    ),
    CatalogArtifact(
        path="docs/deployment_plan.md",
        kind="file",
        phase="Production Readiness",
        module=11,
        classification="carry-forward",
        why_it_matters="Deployment plan document.",
    ),
    # --- Bootcamp Records (bootcamp-wide; produced by completion/graduation flows) ---
    CatalogArtifact(
        path="docs/bootcamp_recap.md",
        kind="file",
        phase="Bootcamp Records",
        module=None,
        classification="leave-behind",
        why_it_matters="Narrative recap; your learning record.",
    ),
    CatalogArtifact(
        path="docs/bootcamp_journal.md",
        kind="file",
        phase="Bootcamp Records",
        module=None,
        classification="leave-behind",
        why_it_matters="Module-by-module journal; learning record.",
    ),
    CatalogArtifact(
        path="config/bootcamp_progress.json",
        kind="file",
        phase="Bootcamp Records",
        module=None,
        classification="leave-behind",
        why_it_matters="Tracks completed modules; bootcamp-only state.",
    ),
    CatalogArtifact(
        path="docs/completion_summary.md",
        kind="file",
        phase="Bootcamp Records",
        module=None,
        classification="leave-behind",
        why_it_matters="Completion summary of the bootcamp.",
    ),
    CatalogArtifact(
        path="docs/graduation/graduation_certificate.md",
        kind="file",
        phase="Bootcamp Records",
        module=None,
        classification="leave-behind",
        why_it_matters="Your graduation certificate keepsake.",
    ),
]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_modules_completed(path: Path) -> tuple[list[int], bool]:
    """Read ``modules_completed`` from bootcamp_progress.json.

    Reads the progress JSON file and extracts the ``modules_completed`` list,
    coercing values to ints and discarding anything that is not a valid integer.
    The function is defensive: a missing file, unreadable file, binary or
    non-UTF-8 content, malformed JSON, or an unexpected structure never raises —
    it returns an empty list flagged as incomplete instead.

    Args:
        path: Path to the progress JSON file.

    Returns:
        A ``(modules_completed, complete)`` tuple. ``complete`` is True only when
        the file was read and parsed successfully and ``modules_completed`` was a
        valid list; it is False when the file is missing or unreadable (signaling
        a possibly-incomplete inventory).
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return [], False

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return [], False

    if not isinstance(data, dict):
        return [], False

    value = data.get("modules_completed")
    if not isinstance(value, list):
        return [], False

    modules_completed: list[int] = []
    for item in value:
        # Accept ints, but exclude bools (a subclass of int) and coerce numeric
        # strings / floats with integral value where sensible; skip anything else.
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            modules_completed.append(item)
        elif isinstance(item, float) and item.is_integer():
            modules_completed.append(int(item))
        elif isinstance(item, str):
            try:
                modules_completed.append(int(item.strip()))
            except ValueError:
                continue

    return modules_completed, True


# ---------------------------------------------------------------------------
# Resolution and scanning
# ---------------------------------------------------------------------------


def artifact_exists(root: Path, art: CatalogArtifact) -> bool:
    """Return True when the artifact is present under ``root``.

    Files must be regular files; directories must exist and be non-empty. The
    check is defensive: any OSError raised while inspecting the path is treated
    as "not present" and returns False rather than propagating.

    Args:
        root: Project root directory to resolve the artifact path against.
        art: Catalog artifact to check for on disk.

    Returns:
        True if the artifact exists in the expected form (regular file for
        ``kind == "file"``, non-empty directory for ``kind == "dir"``); False
        otherwise, including when inspecting the path raises an OSError.
    """
    target = root / art.path
    try:
        if art.kind == "file":
            return target.is_file()
        if art.kind == "dir":
            if not target.is_dir():
                return False
            return any(target.iterdir())
        return False
    except OSError:
        return False


def collect_present_artifacts(
    root: Path, catalog: list[CatalogArtifact]
) -> list[CatalogArtifact]:
    """Return catalog entries whose target exists on disk, preserving catalog order.

    Iterates the catalog in order and keeps entries for which
    :func:`artifact_exists` is True. If checking a particular artifact raises an
    error, that artifact is skipped and scanning continues, so a single bad path
    never aborts the whole inventory.

    Args:
        root: Project root directory to scan.
        catalog: Catalog of known artifacts to check.

    Returns:
        The subset of ``catalog`` whose targets exist on disk, in catalog order.
    """
    present: list[CatalogArtifact] = []
    for art in catalog:
        try:
            if artifact_exists(root, art):
                present.append(art)
        except OSError:
            continue
    return present


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

#: Heading that always begins the rendered inventory section.
INVENTORY_HEADING: str = "## Complete Artifact Inventory"

#: Note prepended when progress data is missing or unreadable.
INCOMPLETE_NOTE: str = (
    "_Note: progress data was missing or unreadable, so this inventory may be "
    "incomplete and reflects only the artifacts found in your project._"
)


def classification_tag(classification: str) -> str:
    """Return the Markdown tag for an artifact classification.

    Args:
        classification: The artifact's catalog classification
            ("carry-forward" or "leave-behind").

    Returns:
        ``_(carry-forward)_`` for carry-forward artifacts and
        ``_(bootcamp record)_`` for leave-behind/record artifacts.
    """
    if classification == "carry-forward":
        return "_(carry-forward)_"
    return "_(bootcamp record)_"


def render_inventory(
    present: list[CatalogArtifact],
    *,
    progress_complete: bool,
    modules_completed: list[int],
    show_missing: bool,
) -> str:
    """Render the '## Complete Artifact Inventory' Markdown section.

    Groups present artifacts by phase in :data:`PHASE_ORDER`, emitting one
    sub-section per non-empty phase. Empty phase groups are omitted. Each
    artifact renders as ``- `<path>` — <why_it_matters> <tag>`` where the tag is
    ``_(carry-forward)_`` for carry-forward artifacts and ``_(bootcamp record)_``
    for leave-behind/record artifacts. Within a phase group, artifacts keep the
    order they appear in ``present`` (which preserves catalog order). The output
    always begins with the section heading, even when ``present`` is empty. When
    ``progress_complete`` is False, an incompleteness note follows the heading.

    When ``show_missing`` is True, catalog artifacts owned by a completed module
    (``module`` in ``modules_completed``) that are absent from ``present`` are
    listed under their phase with a "not produced" note, so the bootcamper can
    see expected-but-absent artifacts.

    Args:
        present: Catalog artifacts found on disk, in catalog order.
        progress_complete: False when progress data was missing or unreadable.
        modules_completed: Module numbers the bootcamper completed; used only to
            decide which absent artifacts to note when ``show_missing`` is True.
        show_missing: When True, note expected-but-absent artifacts of completed
            modules.

    Returns:
        A Markdown string that always begins with the section heading.
    """
    lines: list[str] = [INVENTORY_HEADING]
    if not progress_complete:
        lines.append("")
        lines.append(INCOMPLETE_NOTE)

    present_paths = {art.path for art in present}
    completed = set(modules_completed)

    for phase in PHASE_ORDER:
        phase_present = [art for art in present if art.phase == phase]

        missing: list[CatalogArtifact] = []
        if show_missing:
            missing = [
                art
                for art in ARTIFACT_CATALOG
                if art.phase == phase
                and art.module in completed
                and art.path not in present_paths
            ]

        if not phase_present and not missing:
            continue

        lines.append("")
        lines.append(f"### {phase}")
        for art in phase_present:
            tag = classification_tag(art.classification)
            lines.append(f"- `{art.path}` — {art.why_it_matters} {tag}")
        for art in missing:
            lines.append(f"- `{art.path}` — {art.why_it_matters} _(not produced)_")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        argv: Optional argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace with progress_file, project_root, output,
        and show_missing attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a 'Complete Artifact Inventory' Markdown section for the "
            "graduation report."
        )
    )
    parser.add_argument(
        "--progress-file",
        default="config/bootcamp_progress.json",
        help="Path to the bootcamp progress JSON file "
        "(default: config/bootcamp_progress.json).",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Root directory to scan for artifacts (default: current directory).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: write to stdout).",
    )
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="Note expected-but-absent artifacts of completed modules.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Wires the full pipeline: parse arguments, load progress, scan the project
    for present artifacts, render the inventory section, and write it to the
    ``--output`` file (UTF-8) or stdout. The body after argument parsing is
    wrapped in a top-level exception handler so that any unexpected error
    (e.g., an unwritable output file) is reported to stderr and surfaced as a
    non-zero exit code rather than a traceback, keeping report generation
    robust and non-blocking.

    Args:
        argv: Optional argument list (defaults to sys.argv[1:]).

    Returns:
        0 on success, 1 on error.
    """
    args = parse_args(argv)
    try:
        project_root = Path(args.project_root)
        progress_arg = Path(args.progress_file)
        progress_path = (
            progress_arg if progress_arg.is_absolute() else project_root / progress_arg
        )

        modules_completed, progress_complete = load_modules_completed(progress_path)
        present = collect_present_artifacts(project_root, ARTIFACT_CATALOG)
        markdown = render_inventory(
            present,
            progress_complete=progress_complete,
            modules_completed=modules_completed,
            show_missing=args.show_missing,
        )

        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
        else:
            sys.stdout.write(markdown)

        return 0
    except Exception as exc:  # noqa: BLE001 - top-level guard keeps generation non-blocking
        print(f"error: failed to generate artifact inventory: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
