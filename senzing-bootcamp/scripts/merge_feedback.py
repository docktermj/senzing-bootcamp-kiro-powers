#!/usr/bin/env python3
"""Senzing Bootcamp - Merge Feedback Script.

Consolidates individual team members' feedback files into a single
team feedback report.  Depends only on the Python standard library.
Cross-platform.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from team_config_validator import (
    TeamConfig,
    TeamConfigError,
    PathResolver,
    load_and_validate,
)


# ── Data model ────────────────────────────────────────────────────────────


@dataclass
class FeedbackEntry:
    """A single improvement entry extracted from a feedback file."""

    member_id: str
    member_name: str
    title: str
    date: str
    module: str
    priority: str   # High | Medium | Low
    category: str   # Documentation | Workflow | Tools | UX | Bug | Performance | Security
    body: str


# ── Parsing ───────────────────────────────────────────────────────────────

VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_CATEGORIES = {
    "Documentation", "Workflow", "Tools", "UX",
    "Bug", "Performance", "Security",
}


def parse_feedback_file(
    content: str,
    member_id: str = "",
    member_name: str = "",
) -> list[FeedbackEntry]:
    """Parse a feedback markdown file and extract improvement entries.

    Looks for sections starting with ``## Improvement: <title>`` and
    extracts the metadata fields (Date, Module, Priority, Category)
    plus the remaining body text.
    """
    entries: list[FeedbackEntry] = []
    # Split on improvement headings
    parts = re.split(r"(?m)^## Improvement:\s*", content)
    # First part is preamble, skip it
    for part in parts[1:]:
        lines = part.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        date = ""
        module = ""
        priority = ""
        category = ""
        body_lines: list[str] = []
        in_body = False

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("**Date**:"):
                date = stripped.split(":", 1)[1].strip().strip("*")
            elif stripped.startswith("**Module**:"):
                module = stripped.split(":", 1)[1].strip().strip("*")
            elif stripped.startswith("**Priority**:"):
                priority = stripped.split(":", 1)[1].strip().strip("*")
            elif stripped.startswith("**Category**:"):
                category = stripped.split(":", 1)[1].strip().strip("*")
            else:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()
        entries.append(
            FeedbackEntry(
                member_id=member_id,
                member_name=member_name,
                title=title,
                date=date,
                module=module,
                priority=priority,
                category=category,
                body=body,
            )
        )
    return entries


# ── Statistics ────────────────────────────────────────────────────────────


def compute_feedback_stats(entries: list[FeedbackEntry]) -> dict:
    """Compute breakdown by priority and category.

    Returns dict with keys:
      total, by_priority (dict[str, int]), by_category (dict[str, int])
    """
    by_priority: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for e in entries:
        by_priority[e.priority] = by_priority.get(e.priority, 0) + 1
        by_category[e.category] = by_category.get(e.category, 0) + 1
    return {
        "total": len(entries),
        "by_priority": by_priority,
        "by_category": by_category,
    }


# ── Merge ─────────────────────────────────────────────────────────────────


def merge_feedback(entries_by_member: dict[str, list[FeedbackEntry]]) -> str:
    """Generate consolidated TEAM_FEEDBACK_REPORT.md content.

    Groups entries by member, includes summary statistics.
    """
    all_entries: list[FeedbackEntry] = []
    for member_entries in entries_by_member.values():
        all_entries.extend(member_entries)

    stats = compute_feedback_stats(all_entries)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Count members with feedback
    members_with = sum(
        1 for elist in entries_by_member.values() if elist
    )
    total_members = len(entries_by_member)

    lines: list[str] = []
    lines.append("# Team Feedback Report")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append(
        f"**Members with feedback**: {members_with} of {total_members}"
    )
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total entries: {stats['total']}")
    pri = stats["by_priority"]
    pri_parts = ", ".join(f"{k} ({v})" for k, v in sorted(pri.items()))
    lines.append(f"- By priority: {pri_parts}" if pri_parts else "- By priority: (none)")
    cat = stats["by_category"]
    cat_parts = ", ".join(f"{k} ({v})" for k, v in sorted(cat.items()))
    lines.append(f"- By category: {cat_parts}" if cat_parts else "- By category: (none)")
    lines.append("")

    # Per-member sections
    for member_key, member_entries in entries_by_member.items():
        if not member_entries:
            # Use member_key as display — it's "Name (id)"
            lines.append(f"## {member_key}")
            lines.append("")
            lines.append("No feedback submitted")
            lines.append("")
            continue

        display = member_entries[0].member_name
        lines.append(f"## {display}")
        lines.append("")
        for entry in member_entries:
            lines.append(f"### Improvement: {entry.title}")
            lines.append("")
            lines.append(f"**Date**: {entry.date}")
            lines.append(f"**Module**: {entry.module}")
            lines.append(f"**Priority**: {entry.priority}")
            lines.append(f"**Category**: {entry.category}")
            lines.append("")
            if entry.body:
                lines.append(entry.body)
                lines.append("")

    return "\n".join(lines)


# ── CLI / main ────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point: load config, read feedback, merge, write report."""
    parser = argparse.ArgumentParser(
        description="Merge team feedback into a consolidated report"
    )
    parser.add_argument(
        "--output",
        default="docs/feedback/TEAM_FEEDBACK_REPORT.md",
        help="Output file path (default: docs/feedback/TEAM_FEEDBACK_REPORT.md)",
    )
    args = parser.parse_args()

    try:
        config = load_and_validate()
    except TeamConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    resolver = PathResolver(config)
    entries_by_member: dict[str, list[FeedbackEntry]] = {}

    for member in config.members:
        p = Path(str(resolver.feedback_path(member)))
        display_key = f"{member.name} ({member.id})"
        try:
            content = p.read_text(encoding="utf-8")
            parsed = parse_feedback_file(content, member.id, member.name)
            entries_by_member[display_key] = parsed
        except OSError:
            print(
                f"Warning: no feedback file for {member.id}",
                file=sys.stderr,
            )
            entries_by_member[display_key] = []

    report = merge_feedback(entries_by_member)
    total_entries = sum(len(v) for v in entries_by_member.values())

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Feedback report written to {out}")
    print(f"Total entries merged: {total_entries}")


if __name__ == "__main__":
    main()
