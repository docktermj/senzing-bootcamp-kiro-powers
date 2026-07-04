#!/usr/bin/env python3
"""Senzing Bootcamp - ER Baseline Status Summary.

Reports which registered data sources have an accepted ER baseline and which are
missing one. Derives the source list from the existing registry
(``config/data_sources.yaml``) and locates each baseline via the canonical
``compare_results.baseline_path()`` convention, reading only light metadata
(``captured_at``, ``record_count``, ``entity_count``) from each present baseline.

The summary is strictly read-only: it never creates, modifies, or deletes any
baseline, the registry, or any other file, and it never raises on missing or
malformed inputs.

Usage:
    # On demand, run from the workspace root so relative config/ paths resolve:
    python3 senzing-bootcamp/scripts/baseline_status.py

    # Override the registry location:
    python3 senzing-bootcamp/scripts/baseline_status.py --registry config/data_sources.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Scripts are not an importable package; make the sibling scripts importable by
# inserting this script's own directory onto sys.path (mirrors the test-import
# convention used across the project).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Reused, unmodified:
from compare_results import baseline_path  # noqa: E402 — Req 3.1, canonical location
from data_sources import (  # noqa: E402 — Req 3.2, registry source list
    _dict_to_registry,
    apply_migrations,
    parse_registry_yaml,
    validate_registry,
)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class BaselineStatus:
    """Per-source baseline coverage row."""

    data_source: str                 # registry key, e.g. "CUSTOMERS_CRM"
    present: bool                    # True iff a readable, well-formed baseline exists
    unreadable: bool = False         # True iff the file exists but could not be read/parsed
    # Light metadata — populated only when present (never the full file contents, Req 1.2):
    captured_at: str | None = None   # ERStatistics.captured_at (acceptance timestamp)
    record_count: int | None = None
    entity_count: int | None = None
    remediation: str | None = None   # how to create one, set when missing (Req 1.3)


@dataclass
class BaselineSummary:
    """The whole report."""

    registry_present: bool           # False -> "no sources registered" (Req 4.2)
    statuses: list[BaselineStatus]   # one row per registered Data_Source, registry order


# ---------------------------------------------------------------------------
# Registry Source Reader
# ---------------------------------------------------------------------------


def read_registry_sources(
    registry_path: str = "config/data_sources.yaml",
    *,
    read_text=None,
) -> list[str] | None:
    """Read the registry and return its registered data-source keys, in order.

    Parses the registry using the existing reader chain
    (``parse_registry_yaml`` -> ``apply_migrations`` -> ``validate_registry`` ->
    ``_dict_to_registry``) and returns the ``data_source`` keys in registry order.

    Args:
        registry_path: Path to the data source registry
            (default: ``config/data_sources.yaml``).
        read_text: Optional callable taking a path and returning file contents as
            a string, raising ``FileNotFoundError`` when the file is absent.
            Defaults to a UTF-8 file read, so the function is testable without
            touching disk.

    Returns:
        The registered ``data_source`` keys in registry order, or ``None`` when
        the registry file is absent, unreadable, unparseable, or invalid.
    """
    if read_text is None:
        def read_text(path: str) -> str:
            with open(path, encoding="utf-8") as handle:
                return handle.read()

    try:
        content = read_text(registry_path)
    except (OSError, UnicodeDecodeError):
        return None

    try:
        raw = parse_registry_yaml(content)
        raw = apply_migrations(raw)
        if validate_registry(raw):
            return None
        registry = _dict_to_registry(raw)
    except Exception:  # noqa: BLE001 — never raise on malformed input (Req 4.2)
        return None

    return [entry.data_source for entry in registry.sources]


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def read_baseline_metadata(path: Path, *, read_text=None) -> dict | None:
    """Read one baseline file and extract only its light ERStatistics metadata.

    Reads the baseline JSON at ``path`` and returns a dict containing exactly
    ``captured_at``, ``record_count``, and ``entity_count`` from the
    ``ERStatistics`` object. The other baseline fields (``match_count``,
    ``possible_match_count``, ``relationship_count``, ``datasource``) are never
    surfaced, honoring the light-metadata contract (Req 1.2). Individual missing
    fields degrade to ``None`` values in the returned dict rather than an error.

    The function is strictly read-only and never raises: a missing, unreadable,
    non-JSON, or non-object file yields ``None`` so the caller can classify the
    source as missing/unreadable (Req 4.1).

    Args:
        path: Path to the baseline JSON file (from ``baseline_path(datasource)``).
        read_text: Optional callable taking a ``Path`` and returning the file's
            text. Defaults to a UTF-8 file read that raises ``FileNotFoundError``
            when the file is absent, making the function testable without disk.

    Returns:
        A dict with keys ``captured_at``, ``record_count``, ``entity_count``
        (values may be ``None`` when absent in the file), or ``None`` if the file
        is missing, unreadable, not valid JSON, or not a JSON object.
    """
    if read_text is None:
        def read_text(p: Path) -> str:
            return p.read_text(encoding="utf-8")

    try:
        raw = read_text(path)
    except (OSError, ValueError):
        # Missing (FileNotFoundError) or otherwise unreadable file.
        return None

    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        # Not valid JSON.
        return None

    if not isinstance(data, dict):
        # Valid JSON but not a JSON object (e.g. array or scalar).
        return None

    return {
        "captured_at": data.get("captured_at"),
        "record_count": data.get("record_count"),
        "entity_count": data.get("entity_count"),
    }


def build_status(data_source: str, *, read_text=None) -> BaselineStatus:
    """Classify one registered data source's ER-baseline coverage.

    Locates the baseline via the canonical ``baseline_path(data_source)``
    convention (Req 3.1), probes it read-only, and builds exactly one of three
    rows:

    - **present** — the baseline exists and reads as a JSON object; the row
      carries the light metadata ``captured_at``/``record_count``/``entity_count``
      only, never the full contents (Reqs 1.1, 1.2).
    - **missing** — no baseline file exists; the row has ``present=False`` and a
      non-empty ``remediation`` string naming the ``accept_baseline`` path used to
      create one (Req 1.3). ``accept_baseline`` is referenced, never called
      (read-only, Req 2.3).
    - **unreadable** — the file exists but cannot be read or parsed; the row has
      ``present=False, unreadable=True`` (Req 4.1).

    The function is strictly read-only and never raises.

    Args:
        data_source: The registered data-source key (e.g. ``"CUSTOMERS_CRM"``).
        read_text: Optional callable taking a ``Path`` and returning the file's
            text, raising ``FileNotFoundError`` when the file is absent. Threaded
            through to ``read_baseline_metadata`` so this is testable without disk.
            Defaults to a UTF-8 file read.

    Returns:
        A single :class:`BaselineStatus` row describing this source's coverage.
    """
    path = baseline_path(data_source)

    # Distinguish "absent" from "exists but unreadable". With a real disk read
    # (read_text is None) Path.exists() answers directly. With an injected
    # read_text, files never live on disk, so absence is signalled by the
    # callable raising FileNotFoundError; anything else means the file exists.
    if read_text is None:
        exists = path.exists()
    else:
        try:
            read_text(path)
            exists = True
        except FileNotFoundError:
            exists = False
        except (OSError, ValueError):
            exists = True

    if not exists:
        remediation = (
            f"No ER baseline at {path}. Create one via "
            f"compare_results.accept_baseline (promote "
            f"config/er_current_{data_source.lower()}.json) during Module 5 Phase 3."
        )
        return BaselineStatus(
            data_source=data_source,
            present=False,
            remediation=remediation,
        )

    metadata = read_baseline_metadata(path, read_text=read_text)
    if metadata is None:
        # File exists but could not be read/parsed as a JSON object.
        return BaselineStatus(
            data_source=data_source,
            present=False,
            unreadable=True,
        )

    return BaselineStatus(
        data_source=data_source,
        present=True,
        captured_at=metadata["captured_at"],
        record_count=metadata["record_count"],
        entity_count=metadata["entity_count"],
    )


def build_summary(
    registry_path: str = "config/data_sources.yaml",
    *,
    read_text=None,
) -> BaselineSummary:
    """Assemble the whole baseline-status report from the registry.

    Resolves the registered sources via ``read_registry_sources`` and then builds
    exactly one :class:`BaselineStatus` per source, in registry order, by calling
    ``build_status`` once per source (Reqs 1.1, 3.2). When
    ``read_registry_sources`` returns ``None`` — the registry is absent,
    unreadable, unparseable, or invalid — the report degrades to
    ``registry_present=False`` with an empty ``statuses`` list (Req 4.2).

    The same injectable ``read_text`` callable is threaded through both the
    registry read (which passes it the ``registry_path`` string) and each
    ``build_status`` call (which passes it a baseline ``Path``), so the whole
    pipeline is testable without touching disk. The function is strictly
    read-only and never raises.

    Args:
        registry_path: Path to the data source registry
            (default: ``config/data_sources.yaml``).
        read_text: Optional callable returning file contents. It receives the
            registry path string for the registry read and a baseline ``Path`` for
            each per-source probe. Defaults to a UTF-8 file read when ``None``.

    Returns:
        A :class:`BaselineSummary` with ``registry_present=False`` and no rows
        when the registry is unavailable, otherwise ``registry_present=True`` with
        one row per registered source in registry order.
    """
    sources = read_registry_sources(registry_path, read_text=read_text)
    if sources is None:
        return BaselineSummary(registry_present=False, statuses=[])

    statuses = [build_status(data_source, read_text=read_text) for data_source in sources]
    return BaselineSummary(registry_present=True, statuses=statuses)


def render_summary(summary: BaselineSummary) -> str:
    """Render a :class:`BaselineSummary` as human-readable text.

    Formats a header followed by one line per registered source. Each line
    reflects exactly one classification (Reqs 1.1, 1.2, 1.3):

    - **present** — the data source with its ``captured_at`` timestamp and its
      ``record_count``/``entity_count`` counts (counts and a timestamp only,
      never row-level data, Req 1.2).
    - **missing** — ``MISSING`` with the source's remediation hint (Req 1.3).
    - **unreadable** — ``UNREADABLE`` (Req 4.2).

    When ``registry_present`` is false, returns the single line
    ``"No data sources have been registered yet."`` (Req 4.2).

    This function is presentation only: it performs no file or network I/O and
    emits counts and a timestamp, never row-level baseline contents.

    Args:
        summary: The assembled report to render.

    Returns:
        The rendered summary text (no trailing newline).
    """
    if not summary.registry_present:
        return "No data sources have been registered yet."

    lines = ["ER Baseline Status Summary", "=" * 26]

    for status in summary.statuses:
        if status.present:
            captured_at = status.captured_at if status.captured_at is not None else "unknown"
            record_count = (
                status.record_count if status.record_count is not None else "unknown"
            )
            entity_count = (
                status.entity_count if status.entity_count is not None else "unknown"
            )
            lines.append(
                f"{status.data_source}: present "
                f"(captured_at={captured_at}, "
                f"records={record_count}, entities={entity_count})"
            )
        elif status.unreadable:
            lines.append(f"{status.data_source}: UNREADABLE")
        else:
            remediation = status.remediation or ""
            lines.append(f"{status.data_source}: MISSING — {remediation}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the baseline status summary.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None).

    Returns:
        0 on a clean run (including the empty-registry and all-missing cases),
        1 only on an internally handled error path.
    """
    parser = argparse.ArgumentParser(
        description="Summarize which data sources have an accepted ER baseline."
    )
    parser.add_argument(
        "--registry",
        default="config/data_sources.yaml",
        help="Path to the data source registry (default: config/data_sources.yaml).",
    )
    args = parser.parse_args(argv)

    # Read -> build -> render, strictly read-only. Any unexpected error is logged
    # to stderr and swallowed so the process returns without raising (Req 4.1).
    try:
        summary = build_summary(args.registry)
        print(render_summary(summary))
    except Exception as exc:  # noqa: BLE001 — non-raising by contract (Req 4.1)
        print(
            f"warning: baseline status summary could not be produced: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
