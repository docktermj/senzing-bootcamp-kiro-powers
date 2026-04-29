#!/usr/bin/env python3
"""Senzing Bootcamp - Automated Feedback Triage Script.

Parses a feedback markdown file and generates skeleton spec directories
with pre-populated bugfix.md or requirements.md files.

Depends only on the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────

VALID_CATEGORIES = {
    "Documentation", "Workflow", "Tools", "UX",
    "Bug", "Performance", "Security",
}

VALID_PRIORITIES = {"High", "Medium", "Low"}

REQUIRED_FIELDS = {"title", "category"}

DEFAULT_FEEDBACK_FILE = "SENZING_BOOTCAMP_POWER_FEEDBACK.md"
DEFAULT_OUTPUT_DIR = ".kiro/specs/"


# ── Data Structures ───────────────────────────────────────────────────────


@dataclass
class FeedbackEntry:
    """A single improvement entry extracted from a feedback file."""

    title: str
    date: str | None
    module: str | None
    priority: str | None
    category: str | None
    what_happened: str
    why_problem: str
    suggested_fix: str
    workaround: str | None


@dataclass
class TriageResult:
    """Result of successfully creating a spec directory."""

    path: Path
    title: str
    doc_type: str       # "bugfix" or "requirements"
    priority: str | None


# ── Utility Functions ─────────────────────────────────────────────────────


def to_kebab_case(title: str) -> str:
    """Convert a title string to kebab-case for directory naming.

    Lowercase, replace spaces and special characters with hyphens,
    collapse consecutive hyphens, strip leading/trailing hyphens.
    """
    result = title.lower()
    # Replace any character that is not alphanumeric with a hyphen
    result = re.sub(r"[^a-z0-9]", "-", result)
    # Collapse consecutive hyphens
    result = re.sub(r"-{2,}", "-", result)
    # Strip leading/trailing hyphens
    result = result.strip("-")
    return result


# ── Parser Functions ──────────────────────────────────────────────────────


def extract_field(section: str, field_name: str) -> str | None:
    """Extract content for a named field from a feedback section.

    Looks for patterns like ``**Field Name:** content`` (inline metadata)
    or ``### Field Name\\ncontent`` (section-based content).

    Preserves markdown formatting (bold, italic, code blocks, lists).
    Handles multi-paragraph content by capturing until the next field heading.
    """
    # Try inline metadata pattern: **Field Name**: value  or  **Field Name:** value
    inline_pattern = re.compile(
        r"^\*\*" + re.escape(field_name) + r"\*\*\s*:\s*(.+)$",
        re.MULTILINE,
    )
    match = inline_pattern.search(section)
    if match:
        return match.group(1).strip()

    # Try section heading pattern: ### Field Name
    heading_pattern = re.compile(
        r"^###\s+" + re.escape(field_name) + r"\s*\n(.*?)(?=^###\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = heading_pattern.search(section)
    if match:
        content = match.group(1).strip()
        return content if content else None

    return None


def parse_feedback_file(content: str) -> tuple[list[FeedbackEntry], list[str]]:
    """Parse feedback markdown into structured entries.

    Splits content on ``## Improvement: <title>`` headings, extracts fields
    from each section. Preserves markdown formatting within field content.

    Returns:
        Tuple of (successfully_parsed_entries, warning_messages).
    """
    entries: list[FeedbackEntry] = []
    warnings: list[str] = []

    # Split on ## Improvement: headings
    parts = re.split(r"(?m)^## Improvement:\s*", content)

    # First part is preamble, skip it
    for part in parts[1:]:
        lines = part.strip().splitlines()
        if not lines:
            warnings.append("Empty improvement section found, skipping")
            continue

        title = lines[0].strip()

        # Check required field: title
        if not title:
            warnings.append("Improvement entry with empty title found, skipping (missing: title)")
            continue

        # Reconstruct the section body (everything after the title line)
        section_body = "\n".join(lines[1:])

        # Extract metadata fields
        date = extract_field(section_body, "Date")
        module = extract_field(section_body, "Module")
        priority = extract_field(section_body, "Priority")
        category = extract_field(section_body, "Category")

        # Check required field: category
        if not category:
            warnings.append(
                f"Entry '{title}': missing required field 'category', skipping"
            )
            continue

        # Warn on unrecognized category but still process
        if category not in VALID_CATEGORIES:
            warnings.append(
                f"Entry '{title}': unrecognized category '{category}', "
                f"defaulting to requirements skeleton"
            )

        # Extract section-based content fields
        what_happened = extract_field(section_body, "What Happened") or ""
        why_problem = extract_field(section_body, "Why It's a Problem") or ""
        suggested_fix = extract_field(section_body, "Suggested Fix") or ""
        workaround = extract_field(section_body, "Workaround Used")

        entries.append(
            FeedbackEntry(
                title=title,
                date=date,
                module=module,
                priority=priority,
                category=category,
                what_happened=what_happened,
                why_problem=why_problem,
                suggested_fix=suggested_fix,
                workaround=workaround,
            )
        )

    return entries, warnings


# ── Skeleton Generators ───────────────────────────────────────────────────


def generate_bugfix_skeleton(entry: FeedbackEntry) -> str:
    """Generate bugfix.md content from a bug-category feedback entry."""
    lines: list[str] = []

    lines.append("# Bug Report")
    lines.append("")
    lines.append(entry.what_happened if entry.what_happened else "_No description provided._")
    lines.append("")

    lines.append("## Steps to Reproduce")
    lines.append("")
    context_parts: list[str] = []
    if entry.module:
        context_parts.append(f"- **Module**: {entry.module}")
    if entry.date:
        context_parts.append(f"- **Date reported**: {entry.date}")
    if context_parts:
        lines.extend(context_parts)
        lines.append("")
    if entry.what_happened:
        # Extract any numbered or bulleted steps from what_happened
        step_lines = [
            ln for ln in entry.what_happened.splitlines()
            if re.match(r"^\s*(\d+[\.\)]\s|[-*]\s)", ln)
        ]
        if step_lines:
            lines.extend(step_lines)
        else:
            lines.append("1. _Extract steps from the bug report above._")
    else:
        lines.append("1. _Steps not provided._")
    lines.append("")

    lines.append("## Expected Behavior")
    lines.append("")
    if entry.why_problem:
        lines.append(f"The expected behavior is the opposite of the reported problem: {entry.why_problem}")
    else:
        lines.append("_Expected behavior not specified._")
    lines.append("")

    lines.append("## Suggested Fix")
    lines.append("")
    lines.append(entry.suggested_fix if entry.suggested_fix else "_No fix suggested._")
    lines.append("")

    # Only include workaround section if workaround is non-empty
    if entry.workaround:
        lines.append("## Known Workaround")
        lines.append("")
        lines.append(entry.workaround)
        lines.append("")

    return "\n".join(lines)


def generate_requirements_skeleton(entry: FeedbackEntry) -> str:
    """Generate requirements.md content from a non-bug feedback entry."""
    lines: list[str] = []

    # Auto-generated comment header
    lines.append("<!-- Auto-generated by triage_feedback.py. Requires human review before implementation. -->")
    lines.append("")

    # Introduction
    lines.append("# Requirements Document")
    lines.append("")
    lines.append("## Introduction")
    lines.append("")
    lines.append(f"This spec addresses the feedback: **{entry.title}**.")
    lines.append("")
    if entry.what_happened:
        lines.append(f"**Context**: {entry.what_happened}")
        lines.append("")
    if entry.why_problem:
        lines.append(f"**Problem**: {entry.why_problem}")
        lines.append("")

    # Glossary with placeholder entries from title key terms
    lines.append("## Glossary")
    lines.append("")
    title_words = [
        w for w in re.split(r"\s+", entry.title)
        if len(w) > 3 and w.isalpha()
    ]
    if title_words:
        for word in title_words[:5]:  # Limit to 5 terms
            lines.append(f"- **{word}**: _TODO: define this term_")
    else:
        lines.append("- _TODO: add glossary terms_")
    lines.append("")

    # Requirements section with one stub
    lines.append("## Requirements")
    lines.append("")
    lines.append("### Requirement 1")
    lines.append("")
    if entry.suggested_fix:
        lines.append(f"**User Story:** As a user, I want {entry.suggested_fix.lower().rstrip('.')}, so that the experience is improved.")
    else:
        lines.append("**User Story:** As a user, I want _TODO_, so that _TODO_.")
    lines.append("")
    lines.append("#### Acceptance Criteria")
    lines.append("")
    lines.append("1. _TODO: define acceptance criteria_")
    lines.append("")

    return "\n".join(lines)


def generate_config(workflow_type: str, spec_type: str) -> str:
    """Generate .config.kiro JSON content with a unique UUID v4."""
    config = {
        "specId": str(uuid.uuid4()),
        "workflowType": workflow_type,
        "specType": spec_type,
    }
    return json.dumps(config)


# ── Directory Creation ────────────────────────────────────────────────────


def create_spec_directory(
    entry: FeedbackEntry,
    base_dir: Path,
    dry_run: bool = False,
) -> tuple[Path | None, str | None]:
    """Create a spec directory with skeleton document and config file.

    Returns:
        Tuple of (created_path_or_None, warning_message_or_None).
    """
    dir_name = to_kebab_case(entry.title)
    if not dir_name:
        return None, f"Entry '{entry.title}': could not derive directory name, skipping"

    spec_dir = base_dir / dir_name

    if spec_dir.exists():
        return None, f"Entry '{entry.title}': directory '{spec_dir}' already exists, skipping"

    if dry_run:
        return spec_dir, None

    try:
        spec_dir.mkdir(parents=True, exist_ok=True)

        # Determine skeleton type based on category
        is_bug = entry.category == "Bug"

        if is_bug:
            skeleton = generate_bugfix_skeleton(entry)
            skeleton_file = spec_dir / "bugfix.md"
            workflow_type = "bugfix"
            spec_type = "bugfix"
        else:
            skeleton = generate_requirements_skeleton(entry)
            skeleton_file = spec_dir / "requirements.md"
            workflow_type = "requirements-first"
            spec_type = "feature"

        skeleton_file.write_text(skeleton, encoding="utf-8")

        # Write config file
        config_content = generate_config(workflow_type, spec_type)
        config_file = spec_dir / ".config.kiro"
        config_file.write_text(config_content, encoding="utf-8")

        return spec_dir, None

    except OSError as exc:
        return None, f"Entry '{entry.title}': filesystem error: {exc}"


# ── Report Generation ─────────────────────────────────────────────────────


def print_triage_report(
    generated: list[TriageResult],
    skipped: list[tuple[str, str]],
    total_entries: int,
) -> None:
    """Print the triage report to stdout."""
    if total_entries == 0:
        print("No improvement entries found.")
        return

    if generated:
        print("Generated specs:")
        for result in generated:
            print(
                f"  - {result.path} | {result.title} | "
                f"{result.doc_type} | priority: {result.priority or 'N/A'}"
            )
        print()

    if skipped:
        print("Skipped entries:")
        for title, reason in skipped:
            print(f"  - {title}: {reason}")
        print()

    print(
        f"Summary: {total_entries} processed, "
        f"{len(generated)} generated, {len(skipped)} skipped"
    )


# ── CLI Entry Point ───────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for triage_feedback.py."""
    parser = argparse.ArgumentParser(
        description="Parse feedback markdown and generate skeleton spec directories"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_FEEDBACK_FILE,
        help=f"Path to feedback file (default: {DEFAULT_FEEDBACK_FILE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report without creating files or directories",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Base directory for generated specs (default: {DEFAULT_OUTPUT_DIR})",
    )

    args = parser.parse_args(argv)

    feedback_path = Path(args.path)
    if not feedback_path.exists():
        print(f"Error: feedback file not found: {feedback_path}", file=sys.stderr)
        return 1

    content = feedback_path.read_text(encoding="utf-8")
    entries, parse_warnings = parse_feedback_file(content)

    base_dir = Path(args.output_dir)
    generated: list[TriageResult] = []
    skipped: list[tuple[str, str]] = []

    # Add parse warnings to skipped
    for warning in parse_warnings:
        skipped.append(("(parse warning)", warning))

    total_entries = len(entries) + len(parse_warnings)

    for entry in entries:
        spec_path, warning = create_spec_directory(entry, base_dir, args.dry_run)
        if spec_path is not None:
            doc_type = "bugfix" if entry.category == "Bug" else "requirements"
            generated.append(
                TriageResult(
                    path=spec_path,
                    title=entry.title,
                    doc_type=doc_type,
                    priority=entry.priority,
                )
            )
        if warning is not None:
            skipped.append((entry.title, warning))

    print_triage_report(generated, skipped, total_entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
