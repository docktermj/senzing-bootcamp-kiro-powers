#!/usr/bin/env python3
"""Senzing Bootcamp - Graduation Certificate Generator.

Reads bootcamp progress, preferences, and journal data to produce a
graduation certificate in both Markdown and HTML formats.

Usage:
    python senzing-bootcamp/scripts/generate_graduation_certificate.py
    python senzing-bootcamp/scripts/generate_graduation_certificate.py --progress-file config/bootcamp_progress.json
    python senzing-bootcamp/scripts/generate_graduation_certificate.py --output-dir docs/graduation/

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ProgressData:
    """Parsed progress file content.

    Attributes:
        modules_completed: List of completed module numbers.
        module_names: Mapping of module number to module name.
    """

    modules_completed: list[int] = field(default_factory=list)
    module_names: dict[int, str] = field(default_factory=dict)


@dataclass
class PreferencesData:
    """Parsed preferences file content.

    Attributes:
        track: Completed track name (Core Bootcamp, Advanced Topics, or Unknown).
        language: Programming language chosen (e.g. Python, Java, or Unknown).
    """

    track: str = "Unknown"
    language: str = "Unknown"


@dataclass
class JournalEntry:
    """A single module journal entry.

    Attributes:
        module_number: The module this entry belongs to.
        outcome: Brief outcome description from the journal.
    """

    module_number: int = 0
    outcome: str = ""


@dataclass
class ERMetrics:
    """Entity resolution metrics extracted from journal.

    Attributes:
        entity_count: Number of resolved entities, or None if not found.
        match_rate: Match rate percentage, or None if not found.
        data_sources_loaded: Number of data sources loaded, or None if not found.
    """

    entity_count: str | None = None
    match_rate: str | None = None
    data_sources_loaded: str | None = None


@dataclass
class JournalData:
    """Parsed journal file content.

    Attributes:
        entries: Mapping of module number to journal entry.
        er_metrics: Extracted ER metrics, or None if unavailable.
    """

    entries: dict[int, JournalEntry] = field(default_factory=dict)
    er_metrics: ERMetrics | None = None


@dataclass
class ModuleRecord:
    """A single module entry for the certificate.

    Attributes:
        number: Module number.
        name: Module name from progress data.
        outcome: Outcome description (empty string if no journal entry).
    """

    number: int = 0
    name: str = ""
    outcome: str = ""


@dataclass
class CertificateData:
    """Assembled certificate content ready for rendering.

    Attributes:
        project_name: Workspace directory name.
        completion_date: ISO 8601 date string (YYYY-MM-DD).
        track: Track name from preferences.
        modules: List of module records for the certificate.
        er_metrics: ER metrics from journal, or None.
        skills: List of demonstrated skills.
        next_steps: List of recommended next steps.
    """

    project_name: str = ""
    completion_date: str = ""
    track: str = "Unknown"
    modules: list[ModuleRecord] = field(default_factory=list)
    er_metrics: ERMetrics | None = None
    skills: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Journal Parsing Patterns
# ---------------------------------------------------------------------------

_MODULE_HEADING_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s+—", re.MULTILINE)
_WHAT_WE_DID_RE = re.compile(r"\*\*What we did:\*\*\s*(.+)")
_ER_ENTITY_COUNT_RE = re.compile(r"entit(?:y count|ies):\s*(\d[\d,]*)", re.IGNORECASE)
_ER_MATCH_RATE_RE = re.compile(r"match(?:\s+rate)?:\s*([\d.]+%?)", re.IGNORECASE)
_ER_DATA_SOURCES_RE = re.compile(r"(?:data\s+)?sources?\s+loaded:\s*(\d+)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Data Processing",
    7: "Query, Visualize, and Discover",
    8: "Performance Testing & Benchmarking",
    9: "Security Hardening",
    10: "Monitoring & Observability",
    11: "Package & Deploy",
}

MODULE_SKILLS: dict[int, list[str]] = {
    1: ["Business Problem Definition", "Use Case Analysis"],
    2: ["SDK Installation", "Environment Configuration"],
    3: ["System Verification", "Database Setup"],
    4: ["Data Collection", "Source Identification"],
    5: ["Data Quality Assessment", "Entity Mapping"],
    6: ["Data Loading", "Multi-Source Integration"],
    7: ["Entity Querying", "Result Visualization"],
    8: ["Performance Tuning", "Benchmarking"],
    9: ["Security Hardening", "Access Control"],
    10: ["Monitoring", "Operational Alerting"],
    11: ["Production Deployment", "CI/CD Integration"],
}


# ---------------------------------------------------------------------------
# Data Loaders
# ---------------------------------------------------------------------------


def load_progress(path: Path) -> ProgressData:
    """Load and parse bootcamp_progress.json.

    Args:
        path: Path to the progress JSON file.

    Returns:
        ProgressData with modules_completed and module_names.

    Raises:
        SystemExit: If the file does not exist or contains malformed JSON.
    """
    if not path.is_file():
        print(f"Error: progress file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error: cannot read progress file: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error: malformed JSON in progress file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: progress file must contain a JSON object", file=sys.stderr)
        sys.exit(1)

    raw_completed = data.get("modules_completed", [])
    if not isinstance(raw_completed, list):
        print("Error: 'modules_completed' must be a list", file=sys.stderr)
        sys.exit(1)

    # Extract valid integer module numbers
    modules_completed: list[int] = []
    for item in raw_completed:
        if isinstance(item, int):
            modules_completed.append(item)
        elif isinstance(item, str) and item.isdigit():
            modules_completed.append(int(item))

    # Build module_names mapping for completed modules
    module_names: dict[int, str] = {}
    for num in modules_completed:
        module_names[num] = MODULE_NAMES.get(num, f"Module {num}")

    return ProgressData(modules_completed=sorted(modules_completed), module_names=module_names)


def load_journal(path: Path) -> JournalData:
    """Load and parse bootcamp_journal.md for outcomes and ER metrics.

    Args:
        path: Path to the journal markdown file.

    Returns:
        JournalData with per-module outcomes and ER metrics. Empty if file missing.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, IOError):
        return JournalData(entries={}, er_metrics=None)

    # Extract per-module entries
    entries: dict[int, JournalEntry] = {}
    try:
        headings = list(_MODULE_HEADING_RE.finditer(content))
        for i, heading_match in enumerate(headings):
            module_num = int(heading_match.group(1))
            # Determine the section text between this heading and the next
            start = heading_match.end()
            end = headings[i + 1].start() if i + 1 < len(headings) else len(content)
            section = content[start:end]

            # Look for "What we did:" in this section
            outcome_match = _WHAT_WE_DID_RE.search(section)
            outcome = outcome_match.group(1).strip() if outcome_match else ""
            if outcome or module_num not in entries:
                entries[module_num] = JournalEntry(
                    module_number=module_num, outcome=outcome
                )
    except (ValueError, IndexError, AttributeError):
        # Parse whatever succeeded so far; don't raise
        pass

    # Extract ER metrics from the full content
    er_metrics: ERMetrics | None = None
    try:
        entity_count_match = _ER_ENTITY_COUNT_RE.search(content)
        match_rate_match = _ER_MATCH_RATE_RE.search(content)
        data_sources_match = _ER_DATA_SOURCES_RE.search(content)

        entity_count = entity_count_match.group(1) if entity_count_match else None
        match_rate = match_rate_match.group(1) if match_rate_match else None
        data_sources = data_sources_match.group(1) if data_sources_match else None

        if entity_count or match_rate or data_sources:
            er_metrics = ERMetrics(
                entity_count=entity_count,
                match_rate=match_rate,
                data_sources_loaded=data_sources,
            )
    except (ValueError, AttributeError):
        # If ER metric extraction fails, leave as None
        pass

    return JournalData(entries=entries, er_metrics=er_metrics)


# ---------------------------------------------------------------------------
# Minimal YAML Parser
# ---------------------------------------------------------------------------


def parse_simple_yaml(content: str) -> dict[str, str]:
    """Parse a flat YAML file with simple key: value pairs.

    Handles string values (quoted or unquoted) and boolean literals.
    Ignores comments and blank lines.

    Args:
        content: Raw YAML file content.

    Returns:
        Dict mapping keys to string values.
    """
    result: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue
        # Must contain a colon to be a key:value pair
        if ":" not in stripped:
            continue
        key, _, raw_value = stripped.partition(":")
        key = key.strip()
        if not key:
            continue
        value = raw_value.strip()
        # Handle null/empty values — skip them
        if value.lower() in ("null", "~", ""):
            continue
        # Handle boolean literals — store as lowercase strings
        if value.lower() in ("true", "false"):
            result[key] = value.lower()
            continue
        # Strip surrounding quotes (single or double)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        result[key] = value
    return result


def load_preferences(path: Path) -> PreferencesData:
    """Load and parse bootcamp_preferences.yaml using minimal YAML parser.

    Args:
        path: Path to the preferences YAML file.

    Returns:
        PreferencesData with track and language. Uses defaults if file missing
        or malformed.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, IOError):
        return PreferencesData(track="Unknown", language="Unknown")

    try:
        data = parse_simple_yaml(content)
    except Exception:
        return PreferencesData(track="Unknown", language="Unknown")

    track = data.get("track", "Unknown") or "Unknown"
    language = data.get("language", "Unknown") or "Unknown"
    return PreferencesData(track=track, language=language)


# ---------------------------------------------------------------------------
# Content Assembly
# ---------------------------------------------------------------------------


def derive_skills(modules_completed: list[int]) -> list[str]:
    """Derive deduplicated skills list from completed modules.

    Iterates over completed module numbers, collects all skills from
    MODULE_SKILLS for those modules, and returns a deduplicated list
    preserving order of first appearance. Unknown module numbers are skipped.

    Args:
        modules_completed: List of completed module numbers.

    Returns:
        Deduplicated list of skill strings in order of first appearance.
    """
    seen: set[str] = set()
    skills: list[str] = []
    for num in modules_completed:
        for skill in MODULE_SKILLS.get(num, []):
            if skill not in seen:
                seen.add(skill)
                skills.append(skill)
    return skills


def derive_next_steps(track: str) -> list[str]:
    """Derive next-step recommendations based on completed track.

    Args:
        track: The completed track name.

    Returns:
        List of recommendation strings appropriate to the track.
    """
    if track == "Core Bootcamp":
        return [
            "Explore performance tuning and benchmarking",
            "Implement security hardening",
            "Set up monitoring and alerting",
            "Plan production deployment",
        ]
    if track == "Advanced Topics":
        return [
            "Deploy to production environment",
            "Establish ongoing operations procedures",
            "Set up CI/CD pipeline for entity resolution",
            "Monitor and optimize resolution quality",
        ]
    # Unknown or any other track
    return [
        "Review completed modules for deeper understanding",
        "Explore additional Senzing documentation",
        "Consider advanced entity resolution topics",
    ]


def assemble_certificate(
    progress: ProgressData,
    preferences: PreferencesData,
    journal: JournalData,
    project_name: str,
) -> CertificateData:
    """Combine all data sources into a unified certificate model.

    Args:
        progress: Parsed progress data.
        preferences: Parsed preferences data.
        journal: Parsed journal data.
        project_name: Workspace directory name.

    Returns:
        CertificateData ready for rendering.
    """
    modules: list[ModuleRecord] = []
    for num in progress.modules_completed:
        name = progress.module_names.get(num, f"Module {num}")
        entry = journal.entries.get(num)
        outcome = entry.outcome if entry else ""
        modules.append(ModuleRecord(number=num, name=name, outcome=outcome))

    return CertificateData(
        project_name=project_name,
        completion_date=datetime.date.today().isoformat(),
        track=preferences.track,
        modules=modules,
        er_metrics=journal.er_metrics,
        skills=derive_skills(progress.modules_completed),
        next_steps=derive_next_steps(preferences.track),
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_markdown(data: CertificateData) -> str:
    """Render certificate data as a Markdown document.

    Args:
        data: Assembled certificate content.

    Returns:
        Complete Markdown string.
    """
    lines: list[str] = []

    # Title
    lines.append("# 🎓 Graduation Certificate")
    lines.append("")

    # Identity section
    lines.append("## Identity")
    lines.append("")
    lines.append(f"- **Project:** {data.project_name}")
    lines.append(f"- **Completion Date:** {data.completion_date}")
    lines.append(f"- **Track:** {data.track}")
    lines.append("")

    # Modules table
    lines.append("## Modules Completed")
    lines.append("")
    lines.append("| # | Module | Outcome |")
    lines.append("|---|--------|---------|")
    for module in data.modules:
        lines.append(f"| {module.number} | {module.name} | {module.outcome} |")
    lines.append("")

    # ER Results section
    lines.append("## Entity Resolution Results")
    lines.append("")
    if data.er_metrics is not None:
        if data.er_metrics.entity_count is not None:
            lines.append(f"- **Entities:** {data.er_metrics.entity_count}")
        if data.er_metrics.match_rate is not None:
            lines.append(f"- **Match Rate:** {data.er_metrics.match_rate}")
        if data.er_metrics.data_sources_loaded is not None:
            lines.append(f"- **Data Sources Loaded:** {data.er_metrics.data_sources_loaded}")
    else:
        lines.append("Entity resolution results were not recorded.")
    lines.append("")

    # Skills section
    lines.append("## Skills Demonstrated")
    lines.append("")
    for skill in data.skills:
        lines.append(f"- {skill}")
    lines.append("")

    # Next Steps section
    lines.append("## Next Steps")
    lines.append("")
    for step in data.next_steps:
        lines.append(f"- {step}")
    lines.append("")

    return "\n".join(lines)


def render_html(data: CertificateData) -> str:
    """Render certificate data as an HTML5 document with inline CSS.

    Uses html.escape() for all user-provided content to prevent XSS.

    Args:
        data: Assembled certificate content.

    Returns:
        Complete HTML5 string with DOCTYPE, head, body, and inline styles.
    """
    # Escape all user-provided content
    project_name = html.escape(data.project_name)
    completion_date = html.escape(data.completion_date)
    track = html.escape(data.track)

    parts: list[str] = []

    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('  <meta charset="utf-8">')
    parts.append(f"  <title>Graduation Certificate - {project_name}</title>")
    parts.append("  <style>")
    parts.append("    body {")
    parts.append("      font-family: sans-serif;")
    parts.append("      max-width: 800px;")
    parts.append("      margin: 0 auto;")
    parts.append("      padding: 2rem;")
    parts.append("      color: #333;")
    parts.append("    }")
    parts.append("    h1 { color: #2c3e50; }")
    parts.append("    h2 { color: #34495e; border-bottom: 1px solid #eee; padding-bottom: 0.3rem; }")
    parts.append("    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }")
    parts.append("    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
    parts.append("    th { background-color: #f4f4f4; }")
    parts.append("    ul { padding-left: 1.5rem; }")
    parts.append("    li { margin-bottom: 0.3rem; }")
    parts.append("    .identity { margin-bottom: 1.5rem; }")
    parts.append("    .identity p { margin: 0.3rem 0; }")
    parts.append("    .placeholder { color: #888; font-style: italic; }")
    parts.append("  </style>")
    parts.append("</head>")
    parts.append("<body>")

    # Title
    parts.append("  <h1>\U0001f393 Graduation Certificate</h1>")

    # Identity section
    parts.append('  <h2>Identity</h2>')
    parts.append('  <div class="identity">')
    parts.append(f"    <p><strong>Project:</strong> {project_name}</p>")
    parts.append(f"    <p><strong>Completion Date:</strong> {completion_date}</p>")
    parts.append(f"    <p><strong>Track:</strong> {track}</p>")
    parts.append("  </div>")

    # Modules table
    parts.append("  <h2>Modules Completed</h2>")
    parts.append("  <table>")
    parts.append("    <thead>")
    parts.append("      <tr><th>#</th><th>Module</th><th>Outcome</th></tr>")
    parts.append("    </thead>")
    parts.append("    <tbody>")
    for module in data.modules:
        mod_name = html.escape(module.name)
        mod_outcome = html.escape(module.outcome)
        parts.append(
            f"      <tr><td>{module.number}</td>"
            f"<td>{mod_name}</td><td>{mod_outcome}</td></tr>"
        )
    parts.append("    </tbody>")
    parts.append("  </table>")

    # ER Results section
    parts.append("  <h2>Entity Resolution Results</h2>")
    if data.er_metrics is not None:
        parts.append("  <ul>")
        if data.er_metrics.entity_count is not None:
            entity_count = html.escape(data.er_metrics.entity_count)
            parts.append(f"    <li><strong>Entities:</strong> {entity_count}</li>")
        if data.er_metrics.match_rate is not None:
            match_rate = html.escape(data.er_metrics.match_rate)
            parts.append(f"    <li><strong>Match Rate:</strong> {match_rate}</li>")
        if data.er_metrics.data_sources_loaded is not None:
            data_sources = html.escape(data.er_metrics.data_sources_loaded)
            parts.append(
                f"    <li><strong>Data Sources Loaded:</strong> {data_sources}</li>"
            )
        parts.append("  </ul>")
    else:
        parts.append(
            '  <p class="placeholder">'
            "Entity resolution results were not recorded.</p>"
        )

    # Skills section
    parts.append("  <h2>Skills Demonstrated</h2>")
    parts.append("  <ul>")
    for skill in data.skills:
        parts.append(f"    <li>{html.escape(skill)}</li>")
    parts.append("  </ul>")

    # Next Steps section
    parts.append("  <h2>Next Steps</h2>")
    parts.append("  <ul>")
    for step in data.next_steps:
        parts.append(f"    <li>{html.escape(step)}</li>")
    parts.append("  </ul>")

    parts.append("</body>")
    parts.append("</html>")
    parts.append("")  # trailing newline

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with file paths and output directory.
    """
    parser = argparse.ArgumentParser(
        description="Generate a graduation certificate from bootcamp data.",
    )
    parser.add_argument(
        "--progress-file",
        default="config/bootcamp_progress.json",
        help="Path to progress JSON (default: config/bootcamp_progress.json)",
    )
    parser.add_argument(
        "--preferences-file",
        default="config/bootcamp_preferences.yaml",
        help="Path to preferences YAML (default: config/bootcamp_preferences.yaml)",
    )
    parser.add_argument(
        "--journal-file",
        default="docs/bootcamp_journal.md",
        help="Path to journal markdown (default: docs/bootcamp_journal.md)",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/graduation/",
        help="Output directory (default: docs/graduation/)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for graduation certificate generation.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse exits with 0 for --help, propagate that correctly
        return exc.code if isinstance(exc.code, int) else 1

    try:
        # Load input data
        progress = load_progress(Path(args.progress_file))
        preferences = load_preferences(Path(args.preferences_file))
        journal = load_journal(Path(args.journal_file))

        # Derive project name from current working directory
        project_name = Path.cwd().name

        # Assemble certificate data
        cert_data = assemble_certificate(progress, preferences, journal, project_name)

        # Render both formats
        md_content = render_markdown(cert_data)
        html_content = render_html(cert_data)

        # Create output directory and write files
        output_dir = Path(args.output_dir)
        os.makedirs(output_dir, exist_ok=True)
        (output_dir / "graduation_certificate.md").write_text(md_content, encoding="utf-8")
        (output_dir / "graduation_certificate.html").write_text(html_content, encoding="utf-8")

    except SystemExit:
        raise
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
