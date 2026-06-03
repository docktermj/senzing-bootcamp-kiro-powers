#!/usr/bin/env python3
"""Validate module completion artifacts for structural integrity.

Checks journal and recap file structure, entry counts, and consistency
with the progress file. Used in CI and by the agent for self-checks.

Usage:
    python senzing-bootcamp/scripts/validate_completion_artifacts.py \
        --progress config/bootcamp_progress.json \
        --journal docs/bootcamp_journal.md \
        --recap docs/bootcamp_recap.md

Exits 0 on success, 1 on validation failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class JournalEntry:
    """A single journal entry for a completed module."""

    module_number: int
    module_name: str
    completion_date: str  # ISO 8601 with timezone
    summary: str
    artifacts: list[str]
    why_it_matters: str
    takeaway: str


@dataclass
class JournalDocument:
    """Parsed representation of the bootcamp journal file."""

    bootcamper_name: str
    start_date: str  # ISO 8601 date (YYYY-MM-DD)
    entries: list[JournalEntry] = field(default_factory=list)


@dataclass
class RecapHeader:
    """Parsed header fields from the bootcamp recap file."""

    bootcamper: str
    started: str  # ISO 8601 with timezone
    total_duration: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLETION_STEPS: list[str] = [
    "progress_update",
    "recap_append",
    "journal_entry",
    "completion_certificate",
    "next_step_options",
]


# ---------------------------------------------------------------------------
# Formatting Functions
# ---------------------------------------------------------------------------


def format_journal_header(bootcamper_name: str, start_date: str) -> str:
    """Format the journal file header as markdown.

    Creates the initial header block for a new bootcamp journal file,
    including the level-1 heading, bootcamper name, and start date.

    Args:
        bootcamper_name: Name of the bootcamper (e.g., "Jane Doe").
        start_date: Start date in ISO 8601 format (YYYY-MM-DD).

    Returns:
        Markdown string containing the journal header with trailing separator.
    """
    return (
        f"# Bootcamp Journal\n"
        f"\n"
        f"**Bootcamper:** {bootcamper_name}\n"
        f"**Started:** {start_date}\n"
        f"\n"
        f"---\n"
    )


def format_journal_entry(
    module_number: int,
    module_name: str,
    date: str,
    summary: str,
    artifacts: list[str],
    why_it_matters: str,
    takeaway: str,
) -> str:
    """Format a single journal entry as markdown.

    Creates a formatted markdown block for one completed module, using
    ISO 8601 date format with timezone offset for the completion timestamp.

    Args:
        module_number: The module number (1-11).
        module_name: Human-readable module name (e.g., "Business Problem").
        date: Completion date in ISO 8601 format with timezone offset
            (e.g., "2026-05-14T10:30:00-05:00").
        summary: Brief description of what was done during the module.
        artifacts: List of file paths produced or modified during the module.
        why_it_matters: Statement explaining the module's importance.
        takeaway: The bootcamper's personal takeaway from the module.

    Returns:
        Markdown string containing the formatted journal entry with trailing separator.
    """
    artifacts_str = ", ".join(artifacts)
    return (
        f"\n"
        f"## Module {module_number}: {module_name} — Completed {date}\n"
        f"\n"
        f"**What we did:** {summary}\n"
        f"**What was produced:** {artifacts_str}\n"
        f"**Why it matters:** {why_it_matters}\n"
        f"**Bootcamper's takeaway:** {takeaway}\n"
        f"\n"
        f"---\n"
    )


# ---------------------------------------------------------------------------
# Parsing Functions
# ---------------------------------------------------------------------------


def parse_journal(content: str) -> JournalDocument:
    """Parse journal markdown content into a JournalDocument.

    Args:
        content: Raw markdown content of the bootcamp journal file.

    Returns:
        A JournalDocument with header fields and parsed entries.
        Returns a JournalDocument with empty name, date, and entries if
        content is empty or lacks a valid header.
    """
    if not content or not content.strip():
        return JournalDocument(bootcamper_name="", start_date="", entries=[])

    # Extract header fields
    name_match = re.search(r"^\*\*Bootcamper:\*\*\s*(.+)$", content, re.MULTILINE)
    date_match = re.search(r"^\*\*Started:\*\*\s*(.+)$", content, re.MULTILINE)

    bootcamper_name = name_match.group(1).strip() if name_match else ""
    start_date = date_match.group(1).strip() if date_match else ""

    # Parse entries — each starts with ## Module N: Name — Completed <date>
    entry_pattern = re.compile(
        r"^## Module (\d+):\s*(.+?)\s*\u2014\s*Completed\s+(.+)$",
        re.MULTILINE,
    )

    entries: list[JournalEntry] = []
    matches = list(entry_pattern.finditer(content))

    for i, match in enumerate(matches):
        module_number = int(match.group(1))
        module_name = match.group(2).strip()
        completion_date = match.group(3).strip()

        # Extract the block of text for this entry (up to next entry or end)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start_pos:end_pos]

        # Parse fields from the block
        summary_match = re.search(
            r"^\*\*What we did:\*\*\s*(.+)$", block, re.MULTILINE
        )
        artifacts_match = re.search(
            r"^\*\*What was produced:\*\*\s*(.+)$", block, re.MULTILINE
        )
        why_match = re.search(
            r"^\*\*Why it matters:\*\*\s*(.+)$", block, re.MULTILINE
        )
        takeaway_match = re.search(
            r"^\*\*Bootcamper's takeaway:\*\*\s*(.+)$", block, re.MULTILINE
        )

        summary = summary_match.group(1).strip() if summary_match else ""
        artifacts_str = artifacts_match.group(1).strip() if artifacts_match else ""
        why_it_matters = why_match.group(1).strip() if why_match else ""
        takeaway = takeaway_match.group(1).strip() if takeaway_match else ""

        # Parse artifacts as comma-separated list
        artifacts = (
            [a.strip() for a in artifacts_str.split(",") if a.strip()]
            if artifacts_str
            else []
        )

        entries.append(
            JournalEntry(
                module_number=module_number,
                module_name=module_name,
                completion_date=completion_date,
                summary=summary,
                artifacts=artifacts,
                why_it_matters=why_it_matters,
                takeaway=takeaway,
            )
        )

    return JournalDocument(
        bootcamper_name=bootcamper_name,
        start_date=start_date,
        entries=entries,
    )


def parse_recap_header(content: str) -> RecapHeader:
    """Extract the RecapHeader from recap file content.

    Args:
        content: Raw markdown content of the bootcamp recap file.

    Returns:
        A RecapHeader with bootcamper, started, and total_duration fields.

    Raises:
        ValueError: If content is empty or the header is malformed (missing
            required fields).
    """
    if not content or not content.strip():
        raise ValueError("Recap content is empty")

    bootcamper_match = re.search(
        r"^\*\*Bootcamper:\*\*\s*(.+)$", content, re.MULTILINE
    )
    started_match = re.search(
        r"^\*\*Started:\*\*\s*(.+)$", content, re.MULTILINE
    )
    duration_match = re.search(
        r"^\*\*Total Duration:\*\*\s*(.+)$", content, re.MULTILINE
    )

    if not bootcamper_match:
        raise ValueError("Recap header missing 'Bootcamper' field")
    if not started_match:
        raise ValueError("Recap header missing 'Started' field")
    if not duration_match:
        raise ValueError("Recap header missing 'Total Duration' field")

    return RecapHeader(
        bootcamper=bootcamper_match.group(1).strip(),
        started=started_match.group(1).strip(),
        total_duration=duration_match.group(1).strip(),
    )


# ---------------------------------------------------------------------------
# Counting Functions
# ---------------------------------------------------------------------------


def count_recap_sections(content: str) -> list[int]:
    """Extract module numbers from recap section headings.

    Scans the recap markdown content for level-2 headings matching the
    pattern ``## Module N:`` and returns the module numbers found, sorted
    in ascending order.

    Args:
        content: Raw markdown content of the bootcamp recap file.

    Returns:
        Sorted list of integers representing module numbers found in the
        recap section headings. Returns an empty list if no sections are
        found or content is empty.
    """
    if not content or not content.strip():
        return []

    matches = re.findall(r"^## Module (\d+):", content, re.MULTILINE)
    return sorted(int(m) for m in matches)


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------


def validate_journal_structure(journal: JournalDocument) -> list[str]:
    """Validate journal entry structure for completeness.

    Checks that each entry in the journal has non-empty required fields:
    module_number, module_name, completion_date, summary, and why_it_matters.

    Args:
        journal: Parsed JournalDocument to validate.

    Returns:
        List of error strings describing incomplete entries. Returns an
        empty list if all entries are valid.
    """
    errors: list[str] = []

    for entry in journal.entries:
        prefix = f"Module {entry.module_number}"

        if entry.module_number < 1:
            errors.append(f"{prefix}: module_number must be positive")

        if not entry.module_name.strip():
            errors.append(f"{prefix}: missing module_name")

        if not entry.completion_date.strip():
            errors.append(f"{prefix}: missing completion_date")

        if not entry.summary.strip():
            errors.append(f"{prefix}: missing summary")

        if not entry.why_it_matters.strip():
            errors.append(f"{prefix}: missing why_it_matters")

    return errors


def validate_recap_consistency(
    recap_modules: list[int], progress_modules: list[int]
) -> list[str]:
    """Check that recap sections match progress data.

    Reports modules that appear in the progress file but are missing
    from the recap document.

    Args:
        recap_modules: Sorted list of module numbers found in recap headings.
        progress_modules: List of module numbers from the progress file.

    Returns:
        List of error strings for modules in progress but missing from recap.
        Returns an empty list if all progress modules have recap sections.
    """
    errors: list[str] = []
    recap_set = set(recap_modules)

    for mod in sorted(progress_modules):
        if mod not in recap_set:
            errors.append(
                f"Module {mod} is in progress but missing from recap"
            )

    return errors


def validate_journal_consistency(
    journal_modules: list[int], progress_modules: list[int]
) -> list[str]:
    """Check that journal entries match progress data.

    Reports modules that appear in the progress file but are missing
    from the journal.

    Args:
        journal_modules: List of module numbers found in journal entries.
        progress_modules: List of module numbers from the progress file.

    Returns:
        List of error strings for modules in progress but missing from journal.
        Returns an empty list if all progress modules have journal entries.
    """
    errors: list[str] = []
    journal_set = set(journal_modules)

    for mod in sorted(progress_modules):
        if mod not in journal_set:
            errors.append(
                f"Module {mod} is in progress but missing from journal"
            )

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run completion artifact validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Validate module completion artifacts for structural integrity."
    )
    parser.add_argument(
        "--progress",
        required=True,
        help="Path to bootcamp_progress.json",
    )
    parser.add_argument(
        "--journal",
        required=True,
        help="Path to bootcamp_journal.md",
    )
    parser.add_argument(
        "--recap",
        required=True,
        help="Path to bootcamp_recap.md",
    )
    args = parser.parse_args(argv)

    all_errors: list[str] = []

    # --- Load progress file ---
    progress_path = Path(args.progress)
    progress_modules: list[int] = []
    if progress_path.is_file():
        try:
            data = json.loads(progress_path.read_text(encoding="utf-8"))
            progress_modules = data.get("modules_completed", [])
        except (json.JSONDecodeError, OSError) as exc:
            all_errors.append(f"Failed to read progress file: {exc}")
    else:
        all_errors.append(f"Progress file not found: {args.progress}")

    # --- Validate journal ---
    journal_path = Path(args.journal)
    if journal_path.is_file():
        journal_content = journal_path.read_text(encoding="utf-8")
        journal = parse_journal(journal_content)
        all_errors.extend(validate_journal_structure(journal))
        journal_modules = [e.module_number for e in journal.entries]
        all_errors.extend(
            validate_journal_consistency(journal_modules, progress_modules)
        )
    else:
        if progress_modules:
            all_errors.append(f"Journal file not found: {args.journal}")

    # --- Validate recap ---
    recap_path = Path(args.recap)
    if recap_path.is_file():
        recap_content = recap_path.read_text(encoding="utf-8")
        recap_modules = count_recap_sections(recap_content)
        all_errors.extend(
            validate_recap_consistency(recap_modules, progress_modules)
        )
    else:
        if progress_modules:
            all_errors.append(f"Recap file not found: {args.recap}")

    # --- Report results ---
    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    print("Completion artifact validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
