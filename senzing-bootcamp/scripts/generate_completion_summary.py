#!/usr/bin/env python3
"""Senzing Bootcamp - Completion Summary Narrative Formatter.

Reads the session log at config/session_log.jsonl, organizes completion events
by module, and produces a chronological narrative markdown document at
docs/completion_summary.md. Optionally generates a PDF at docs/completion_summary.pdf.

Usage:
    python senzing-bootcamp/scripts/generate_completion_summary.py
    python senzing-bootcamp/scripts/generate_completion_summary.py --log config/session_log.jsonl
    python senzing-bootcamp/scripts/generate_completion_summary.py --output docs/completion_summary.md
    python senzing-bootcamp/scripts/generate_completion_summary.py --pdf
    python senzing-bootcamp/scripts/generate_completion_summary.py --pdf --pdf-output docs/completion_summary.pdf
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import CompletionLogEntry and COMPLETION_EVENT_TYPES from session_logger
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from session_logger import COMPLETION_EVENT_TYPES, CompletionLogEntry  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODULE_NAMES: dict[int, str] = {
    0: "Onboarding",
    1: "Business Problem",
    2: "SDK Setup",
    3: "Data Profiling",
    4: "Data Mapping",
    5: "Initial Load",
    6: "Entity Resolution",
    7: "Results Analysis",
    8: "Advanced Configuration",
    9: "Performance Tuning",
    10: "Production Deployment",
    11: "Monitoring & Operations",
}

_SECRET_PATTERN = re.compile(
    r'\b\w*(?:secret|password|token|key|credential|connection_string)\w*\s*=\s*\S+',
    re.IGNORECASE,
)

DEFAULT_LOG_PATH = "config/session_log.jsonl"
DEFAULT_OUTPUT_PATH = "docs/completion_summary.md"
DEFAULT_PROGRESS_PATH = "config/bootcamp_progress.json"
DEFAULT_PREFERENCES_PATH = "config/bootcamp_preferences.yaml"
DEFAULT_MAX_SIZE_BYTES = 512000


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class NarrativeSection:
    """A per-module narrative block."""

    module_number: int
    module_name: str
    questions: list[tuple[str, str | None]] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    artifacts: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass
class CompletionNarrative:
    """Complete narrative document."""

    bootcamper_name: str
    start_date: str
    completion_date: str
    total_duration: str
    track: str
    modules_completed: int
    total_artifacts: int
    er_stats: dict[str, str] | None
    sections: list[NarrativeSection] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib only, simple key: value lines)
# ---------------------------------------------------------------------------


def _parse_simple_yaml(text: str) -> dict[str, str]:
    """Parse simple key: value YAML lines into a dict.

    Only handles flat key-value pairs with string values. Skips comments
    and blank lines.

    Args:
        text: YAML content as a string.

    Returns:
        Dict mapping keys to string values.
    """
    result: dict[str, str] = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        colon_idx = stripped.find(":")
        if colon_idx == -1:
            continue
        key = stripped[:colon_idx].strip()
        value = stripped[colon_idx + 1:].strip()
        # Remove surrounding quotes if present
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key] = value
    return result


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------


def parse_session_log(log_path: str) -> list[CompletionLogEntry]:
    """Parse JSONL file into list of CompletionLogEntry objects.

    Reads the session log line by line, parses each as JSON, and filters
    to only completion event types (question, answer, action, artifact).

    Args:
        log_path: Path to the JSONL session log file.

    Returns:
        List of CompletionLogEntry objects.

    Raises:
        FileNotFoundError: If the log file does not exist.
        ValueError: If the log file cannot be parsed.
    """
    p = Path(log_path)
    if not p.exists():
        raise FileNotFoundError(f"Session log not found: {log_path}")

    entries: list[CompletionLogEntry] = []
    try:
        with p.open("r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except json.JSONDecodeError:
                    continue  # Skip malformed lines

                event_type = obj.get("event_type", "")
                if event_type not in COMPLETION_EVENT_TYPES:
                    continue

                entries.append(CompletionLogEntry(
                    event_type=event_type,
                    module=obj.get("module", 0),
                    timestamp=obj.get("timestamp", ""),
                    data=obj.get("data", {}),
                ))
    except OSError as exc:
        raise ValueError(f"Cannot read session log: {exc}") from exc

    return entries


def filter_secrets(text: str) -> str:
    """Remove key=value patterns where key contains sensitive terms.

    Sensitive terms: secret, password, token, key, credential, connection_string.
    Matching is case-insensitive on the key portion.

    Args:
        text: Input text that may contain sensitive key=value patterns.

    Returns:
        Text with sensitive patterns removed.
    """
    return _SECRET_PATTERN.sub("", text)


def build_narrative(
    entries: list[CompletionLogEntry],
    progress_path: str,
    preferences_path: str,
) -> CompletionNarrative:
    """Organize entries into a structured narrative.

    Reads progress and preferences files for metadata, groups entries by
    module, pairs questions with answers by question_id, and computes
    cover metadata.

    Args:
        entries: List of CompletionLogEntry objects from the session log.
        progress_path: Path to config/bootcamp_progress.json.
        preferences_path: Path to config/bootcamp_preferences.yaml.

    Returns:
        A CompletionNarrative with all sections populated.
    """
    # Read progress file
    modules_completed_list: list[int] = []
    track = "core_bootcamp"
    try:
        progress_data = json.loads(Path(progress_path).read_text(encoding="utf-8"))
        modules_completed_list = progress_data.get("modules_completed", [])
        track = progress_data.get("track", "core_bootcamp")
    except (OSError, json.JSONDecodeError):
        pass

    # Read preferences file
    bootcamper_name = "Bootcamper"
    try:
        prefs_text = Path(preferences_path).read_text(encoding="utf-8")
        prefs = _parse_simple_yaml(prefs_text)
        if prefs.get("name"):
            bootcamper_name = prefs["name"]
        if prefs.get("track"):
            track = prefs["track"]
    except OSError:
        pass

    # Compute timestamps
    timestamps: list[str] = [e.timestamp for e in entries if e.timestamp]
    start_date = ""
    completion_date = ""
    total_duration = ""

    if timestamps:
        timestamps_sorted = sorted(timestamps)
        start_date = timestamps_sorted[0][:10]  # YYYY-MM-DD
        completion_date = timestamps_sorted[-1][:10]

        # Compute duration
        try:
            start_dt = datetime.fromisoformat(timestamps_sorted[0].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(timestamps_sorted[-1].replace("Z", "+00:00"))
            delta = end_dt - start_dt
            days = delta.days
            hours = delta.seconds // 3600
            if days > 0:
                total_duration = f"{days} days, {hours} hours"
            else:
                total_duration = f"{hours} hours"
        except (ValueError, TypeError):
            total_duration = "unknown"

    # Group entries by module
    entries_by_module: dict[int, list[CompletionLogEntry]] = {}
    for entry in entries:
        entries_by_module.setdefault(entry.module, []).append(entry)

    # Determine which modules to include: all modules with events + completed modules
    all_modules: set[int] = set(entries_by_module.keys())
    for m in modules_completed_list:
        all_modules.add(m)

    # Build sections sorted by module number
    sections: list[NarrativeSection] = []
    total_artifacts = 0
    er_stats: dict[str, str] | None = None

    for mod_num in sorted(all_modules):
        mod_name = MODULE_NAMES.get(mod_num, f"Module {mod_num}")
        section = NarrativeSection(module_number=mod_num, module_name=mod_name)

        mod_entries = entries_by_module.get(mod_num, [])

        if not mod_entries and mod_num in modules_completed_list:
            # Module completed but no events — mark as unavailable
            sections.append(section)
            continue

        # Collect questions and answers by question_id
        questions_map: dict[str, str] = {}  # question_id -> question text
        answers_map: dict[str, str] = {}  # question_id -> answer text

        for entry in mod_entries:
            if entry.event_type == "question":
                qid = entry.data.get("question_id", "")
                text = entry.data.get("text", "")
                if qid:
                    questions_map[qid] = text
            elif entry.event_type == "answer":
                qid = entry.data.get("question_id", "")
                text = entry.data.get("text", "")
                if qid:
                    answers_map[qid] = text
            elif entry.event_type == "action":
                desc = entry.data.get("description", "")
                file_path = entry.data.get("file_path", "")
                action_type = entry.data.get("action_type", "")
                if file_path:
                    section.actions.append(f"{action_type}: `{file_path}` — {desc}")
                else:
                    section.actions.append(f"{action_type}: {desc}")
            elif entry.event_type == "artifact":
                file_path = entry.data.get("file_path", "")
                artifact_type = entry.data.get("artifact_type", "")
                desc = entry.data.get("description", "")
                section.artifacts.append((file_path, artifact_type, desc))
                total_artifacts += 1

        # Pair questions with answers
        for qid, q_text in questions_map.items():
            a_text = answers_map.get(qid)
            section.questions.append((q_text, a_text))

        # Extract ER stats from action/artifact entries if available
        if mod_num in (6, 7):  # Entity Resolution / Results Analysis
            for entry in mod_entries:
                desc = entry.data.get("description", "")
                if "entity_count" in desc or "dedup_rate" in desc or "cross_source" in desc:
                    if er_stats is None:
                        er_stats = {}
                    # Try to extract stats from description
                    for part in desc.split(","):
                        part = part.strip()
                        if "=" in part:
                            k, v = part.split("=", 1)
                            er_stats[k.strip()] = v.strip()

        sections.append(section)

    return CompletionNarrative(
        bootcamper_name=bootcamper_name,
        start_date=start_date,
        completion_date=completion_date,
        total_duration=total_duration,
        track=track,
        modules_completed=len(modules_completed_list),
        total_artifacts=total_artifacts,
        er_stats=er_stats,
        sections=sections,
    )


def render_markdown(narrative: CompletionNarrative) -> str:
    """Render narrative as markdown string.

    Produces a markdown document with cover section, summary statistics,
    and per-module narrative sections. Applies filter_secrets to all text.

    Args:
        narrative: The CompletionNarrative to render.

    Returns:
        Markdown string ready to write to file.
    """
    lines: list[str] = []

    # Cover section
    lines.append("# Senzing Bootcamp Completion Summary")
    lines.append("")
    lines.append(f"**Bootcamper:** {filter_secrets(narrative.bootcamper_name)}")
    lines.append(f"**Started:** {narrative.start_date}")
    lines.append(f"**Completed:** {narrative.completion_date}")
    lines.append(f"**Duration:** {narrative.total_duration}")
    lines.append(f"**Track:** {filter_secrets(narrative.track)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary statistics
    lines.append("## Summary Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Modules Completed | {narrative.modules_completed} |")
    lines.append(f"| Artifacts Produced | {narrative.total_artifacts} |")

    if narrative.er_stats:
        for stat_key, stat_val in narrative.er_stats.items():
            lines.append(f"| {filter_secrets(stat_key)} | {filter_secrets(stat_val)} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-module sections
    for section in narrative.sections:
        lines.append(f"## Module {section.module_number}: {section.module_name}")
        lines.append("")

        # Check if module has no events (unavailable)
        has_content = (
            section.questions or section.actions or section.artifacts
        )

        if not has_content:
            lines.append(
                "*Session log was unavailable for this module.*"
            )
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Questions Asked
        lines.append("### Questions Asked")
        if section.questions:
            for i, (q_text, a_text) in enumerate(section.questions, start=1):
                lines.append(f"{i}. {filter_secrets(q_text)}")
        else:
            lines.append("*No questions recorded.*")
        lines.append("")

        # Answers Given
        lines.append("### Answers Given")
        if section.questions:
            for i, (q_text, a_text) in enumerate(section.questions, start=1):
                if a_text is not None:
                    lines.append(f"{i}. {filter_secrets(a_text)}")
                else:
                    lines.append(f"{i}. *No answer recorded*")
        else:
            lines.append("*No answers recorded.*")
        lines.append("")

        # Actions Taken
        lines.append("### Actions Taken")
        if section.actions:
            for action in section.actions:
                lines.append(f"- {filter_secrets(action)}")
        else:
            lines.append("*No actions recorded.*")
        lines.append("")

        # Artifacts Created
        lines.append("### Artifacts Created")
        if section.artifacts:
            for file_path, artifact_type, desc in section.artifacts:
                lines.append(
                    f"- `{filter_secrets(file_path)}` ({filter_secrets(artifact_type)})"
                    f" — {filter_secrets(desc)}"
                )
        else:
            lines.append("*No artifacts recorded.*")
        lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def write_narrative(
    output_path: str,
    content: str,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> None:
    """Write narrative to file, truncating if over size limit.

    If the content exceeds max_size_bytes, removes earliest module sections
    until the content fits within the limit.

    Args:
        output_path: Path to write the markdown file.
        content: The markdown content to write.
        max_size_bytes: Maximum file size in bytes (default 512000).
    """
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    encoded = content.encode("utf-8")
    if len(encoded) <= max_size_bytes:
        p.write_text(content, encoding="utf-8")
        return

    # Truncate by removing earliest module sections
    # Split content into header (before first ## Module) and module sections
    module_marker = "\n## Module "
    parts = content.split(module_marker)

    if len(parts) <= 1:
        # No module sections to truncate — just truncate raw content
        truncated = content.encode("utf-8")[:max_size_bytes].decode("utf-8", errors="ignore")
        p.write_text(truncated, encoding="utf-8")
        return

    header = parts[0]
    module_sections = parts[1:]

    # Remove earliest module sections until under limit
    while module_sections and len(
        (header + module_marker + module_marker.join(module_sections)).encode("utf-8")
    ) > max_size_bytes:
        module_sections.pop(0)

    if module_sections:
        final_content = header + module_marker + module_marker.join(module_sections)
    else:
        final_content = header

    # Final safety check
    final_encoded = final_content.encode("utf-8")
    if len(final_encoded) > max_size_bytes:
        final_content = final_encoded[:max_size_bytes].decode("utf-8", errors="ignore")

    p.write_text(final_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------

DEFAULT_PDF_OUTPUT_PATH = "docs/completion_summary.pdf"


def ensure_fpdf2(timeout: int = 30) -> bool:
    """Attempt to install fpdf2 if not present. Returns True if available.

    Tries to import fpdf2 first. If unavailable, runs pip install with the
    specified timeout. Returns whether fpdf2 is importable after the attempt.

    Args:
        timeout: Maximum seconds to wait for pip install (default 30).

    Returns:
        True if fpdf2 is available for import, False otherwise.
    """
    try:
        import fpdf  # noqa: F401, PLC0415
        return True
    except ImportError:
        pass

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "fpdf2"],
            timeout=timeout,
            capture_output=True,
            check=True,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
        return False

    try:
        import fpdf  # noqa: F401, PLC0415
        return True
    except ImportError:
        return False


def _safe_text(text: str) -> str:
    """Ensure text is safe for PDF core fonts (Latin-1 encoding).

    Characters outside the Latin-1 range are replaced with '?' to prevent
    encoding errors with Helvetica/Courier core fonts.

    Args:
        text: Input text that may contain non-Latin-1 characters.

    Returns:
        Text safe for rendering with PDF core fonts.
    """
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _render_cover_page(pdf: "FPDF", narrative: CompletionNarrative) -> None:  # noqa: F821
    """Render the cover page with title, bootcamper name, dates, and track.

    Args:
        pdf: The FPDF instance to render into.
        narrative: The completion narrative with cover metadata.
    """
    pdf.add_page()
    pdf.ln(40)

    # Title
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(
        0, 14, "Senzing Bootcamp Completion Summary",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(20)

    # Bootcamper name
    pdf.set_font("Helvetica", "", 18)
    pdf.cell(
        0, 10, _safe_text(narrative.bootcamper_name),
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(10)

    # Start date
    if narrative.start_date:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0, 8, f"Started: {_safe_text(narrative.start_date)}",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        pdf.ln(4)

    # Completion date
    if narrative.completion_date:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0, 8, f"Completed: {_safe_text(narrative.completion_date)}",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        pdf.ln(4)

    # Duration
    if narrative.total_duration:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0, 8, f"Duration: {_safe_text(narrative.total_duration)}",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        pdf.ln(4)

    # Track
    if narrative.track:
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(
            0, 8, f"Track: {_safe_text(narrative.track)}",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )


def _render_pdf_heading(pdf: "FPDF", text: str, level: int) -> None:  # noqa: F821
    """Render a heading at the given level.

    Args:
        pdf: The FPDF instance.
        text: Heading text.
        level: Heading level (2 for module heading, 3 for subsection).
    """
    if level == 2:
        pdf.set_font("Helvetica", "B", 16)
        pdf.ln(6)
    else:
        pdf.set_font("Helvetica", "B", 13)
        pdf.ln(4)
    pdf.multi_cell(0, 7, _safe_text(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _render_pdf_list_items(
    pdf: "FPDF",  # noqa: F821
    items: list[str],
    numbered: bool = False,
) -> None:
    """Render a list of items as bulleted or numbered entries.

    Handles inline code (backtick content) with monospace font.

    Args:
        pdf: The FPDF instance.
        items: List of text items.
        numbered: If True, use numbered list; otherwise use bullet points.
    """
    pdf.set_font("Helvetica", "", 11)
    for idx, item in enumerate(items, 1):
        prefix = f"{idx}. " if numbered else "- "
        # Handle inline code (backtick content) with monospace font
        parts = re.split(r"`([^`]+)`", item)
        pdf.set_x(pdf.l_margin + 6)
        pdf.write(6, prefix)
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Normal text
                pdf.set_font("Helvetica", "", 11)
                pdf.write(6, _safe_text(part))
            else:
                # Code span — monospace
                pdf.set_font("Courier", "", 10)
                pdf.write(6, _safe_text(part))
        pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)


def _render_module_page(pdf: "FPDF", section: NarrativeSection) -> None:  # noqa: F821
    """Render a single module section on a new page.

    Args:
        pdf: The FPDF instance.
        section: The narrative section to render.
    """
    pdf.add_page()

    # Module heading
    heading = f"Module {section.module_number}: {section.module_name}"
    _render_pdf_heading(pdf, heading, level=2)

    has_content = section.questions or section.actions or section.artifacts

    if not has_content:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(
            0, 6, "Session log was unavailable for this module.",
            new_x="LMARGIN", new_y="NEXT",
        )
        return

    # Questions Asked (numbered)
    _render_pdf_heading(pdf, "Questions Asked", level=3)
    if section.questions:
        q_texts = [q_text for q_text, _ in section.questions]
        _render_pdf_list_items(pdf, q_texts, numbered=True)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "No questions recorded.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Answers Given (numbered)
    _render_pdf_heading(pdf, "Answers Given", level=3)
    if section.questions:
        a_texts = [
            a_text if a_text is not None else "No answer recorded"
            for _, a_text in section.questions
        ]
        _render_pdf_list_items(pdf, a_texts, numbered=True)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "No answers recorded.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Actions Taken (bulleted)
    _render_pdf_heading(pdf, "Actions Taken", level=3)
    if section.actions:
        _render_pdf_list_items(pdf, section.actions, numbered=False)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "No actions recorded.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Artifacts Created (bulleted)
    _render_pdf_heading(pdf, "Artifacts Created", level=3)
    if section.artifacts:
        artifact_items = [
            f"`{file_path}` ({artifact_type}) -- {desc}"
            for file_path, artifact_type, desc in section.artifacts
        ]
        _render_pdf_list_items(pdf, artifact_items, numbered=False)
    else:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 6, "No artifacts recorded.", new_x="LMARGIN", new_y="NEXT")


def render_completion_pdf(narrative: CompletionNarrative, output_path: str) -> None:
    """Render narrative as PDF with cover page and per-module pages.

    Imports fpdf2 lazily so the module can be imported for markdown-only use
    without requiring fpdf2 to be installed.

    Args:
        narrative: The CompletionNarrative to render.
        output_path: File path for the generated PDF.

    Raises:
        ImportError: If fpdf2 is not installed.
        OSError: If the PDF cannot be written to the output path.
    """
    from fpdf import FPDF  # noqa: PLC0415

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover page
    _render_cover_page(pdf, narrative)

    # Per-module pages
    for section in narrative.sections:
        _render_module_page(pdf, section)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(output_path)


def generate_pdf_with_fallback(
    md_path: str,
    pdf_path: str,
    log_path: str = DEFAULT_LOG_PATH,
    progress_path: str = DEFAULT_PROGRESS_PATH,
    preferences_path: str = DEFAULT_PREFERENCES_PATH,
) -> str:
    """Generate PDF, returning status message for the bootcamper.

    Orchestrates the full PDF generation flow: checks/installs fpdf2,
    parses the markdown source, builds the narrative, renders the PDF,
    and handles all failure modes with informative fallback messages.

    Args:
        md_path: Path to the completion summary markdown file.
        pdf_path: Desired output path for the PDF.
        log_path: Path to session log JSONL file.
        progress_path: Path to progress JSON file.
        preferences_path: Path to preferences YAML file.

    Returns:
        A status message string describing the outcome.
    """
    # Check if markdown file exists and has content
    md_file = Path(md_path)
    if not md_file.exists():
        return (
            f"No completion summary markdown found at {md_path}. "
            "Generate the markdown summary first."
        )

    content = md_file.read_text(encoding="utf-8")
    if not content.strip():
        return (
            f"The completion summary at {md_path} is empty. "
            "No PDF generated — insufficient session data."
        )

    # Check for narrative sections (## Module lines indicate content)
    if "## Module" not in content:
        return (
            "The session log contained insufficient data to generate a PDF. "
            f"The markdown file is available at: {md_path}"
        )

    # Attempt to ensure fpdf2 is available
    if not ensure_fpdf2():
        return (
            f"PDF generation requires fpdf2 which could not be installed. "
            f"The markdown summary is available at: {md_path}\n"
            f"To install fpdf2 manually, run: pip install fpdf2"
        )

    # Re-parse the session log and build narrative for PDF rendering
    # We need the structured narrative, not just the markdown text
    try:
        entries = parse_session_log(log_path)
        narrative = build_narrative(entries, progress_path, preferences_path)
    except (FileNotFoundError, ValueError):
        # Fallback: if we can't re-parse, inform the user
        return (
            f"Could not parse session log for PDF rendering. "
            f"The markdown summary is available at: {md_path}"
        )

    # Check if narrative has any sections with content
    has_content = any(
        section.questions or section.actions or section.artifacts
        for section in narrative.sections
    )
    if not has_content:
        return (
            "The session log contained insufficient data to generate a PDF. "
            f"The markdown file is available at: {md_path}"
        )

    # Render PDF
    try:
        render_completion_pdf(narrative, pdf_path)
    except (ImportError, OSError, Exception) as exc:  # noqa: BLE001
        return (
            f"PDF generation failed: {exc}\n"
            f"The markdown summary is available at: {md_path}"
        )

    return f"Completion summary PDF generated: {pdf_path}"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Generate the completion summary narrative markdown and optionally PDF.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="Generate a completion summary narrative from the session log."
    )
    parser.add_argument(
        "--log",
        default=DEFAULT_LOG_PATH,
        help=f"Path to session log JSONL file (default: {DEFAULT_LOG_PATH})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output markdown path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--progress",
        default=DEFAULT_PROGRESS_PATH,
        help=f"Path to progress JSON file (default: {DEFAULT_PROGRESS_PATH})",
    )
    parser.add_argument(
        "--preferences",
        default=DEFAULT_PREFERENCES_PATH,
        help=f"Path to preferences YAML file (default: {DEFAULT_PREFERENCES_PATH})",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=DEFAULT_MAX_SIZE_BYTES,
        help=f"Maximum output size in bytes (default: {DEFAULT_MAX_SIZE_BYTES})",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate a PDF version of the completion summary",
    )
    parser.add_argument(
        "--pdf-output",
        default=DEFAULT_PDF_OUTPUT_PATH,
        help=f"Output PDF path (default: {DEFAULT_PDF_OUTPUT_PATH})",
    )

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Parse session log
    try:
        entries = parse_session_log(args.log)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Build narrative
    narrative = build_narrative(entries, args.progress, args.preferences)

    # Render markdown
    content = render_markdown(narrative)

    # Write output
    write_narrative(args.output, content, max_size_bytes=args.max_size)
    print(f"Completion summary written to: {args.output}")

    # Generate PDF if requested
    if args.pdf:
        result = generate_pdf_with_fallback(
            args.output, args.pdf_output,
            log_path=args.log,
            progress_path=args.progress,
            preferences_path=args.preferences,
        )
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
