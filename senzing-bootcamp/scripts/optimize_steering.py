#!/usr/bin/env python3
"""Optimize steering file organization for reduced context consumption.

Splits always-on steering files into core + context-specific files, compresses
large manual files using Refine-style optimization, and synchronizes
steering-index.yaml. Uses Python 3.11+ stdlib only.

Usage:
    python senzing-bootcamp/scripts/optimize_steering.py
    python senzing-bootcamp/scripts/optimize_steering.py --dry-run
    python senzing-bootcamp/scripts/optimize_steering.py --steering-dir path/to/steering
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_STEERING_DIR = Path("senzing-bootcamp/steering")
DEFAULT_INDEX_PATH = Path("senzing-bootcamp/steering/steering-index.yaml")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ExtractionRule:
    """Defines how a section is extracted from a source file."""

    source_heading: str
    destination_file: str
    append: bool = False
    dispatch_pointer: str = ""


@dataclass
class SplitResult:
    """Result of splitting a file."""

    source_path: Path
    core_line_count: int
    extracted_sections: list[str]
    destination_files: list[Path]
    dispatch_pointers: list[str]


@dataclass
class CompressTarget:
    """Defines compression target for a file."""

    filename: str
    max_token_ratio: float


@dataclass
class CompressResult:
    """Result of compressing a file."""

    path: Path
    original_tokens: int
    compressed_tokens: int
    ratio: float
    target_met: bool
    markers_preserved: bool


@dataclass
class RuleInventory:
    """Inventory of behavioral rules in a file set."""

    gate_markers: list[str] = field(default_factory=list)
    question_markers: list[str] = field(default_factory=list)
    mcp_rules: list[str] = field(default_factory=list)
    hook_rules: list[str] = field(default_factory=list)
    file_rules: list[str] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of distinct behavioral rules."""
        return sum(len(getattr(self, f)) for f in self.__dataclass_fields__)


@dataclass
class OptimizeResult:
    """Result with metrics from the full optimization run."""

    split_results: list[SplitResult] = field(default_factory=list)
    compress_results: list[CompressResult] = field(default_factory=list)
    total_token_savings: int = 0
    files_modified: int = 0
    failures: list[str] = field(default_factory=list)
    success: bool = True


# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS_EXTRACTIONS = [
    ExtractionRule(
        source_heading="### SDK Method Discovery",
        destination_file="mcp-usage-reference.md",
        append=True,
        dispatch_pointer="For SDK method discovery: load `mcp-usage-reference.md`",
    ),
    ExtractionRule(
        source_heading="## Track Switching",
        destination_file="track-switching.md",
        append=True,
        dispatch_pointer="For track switching triggers: load `track-switching.md`",
    ),
    ExtractionRule(
        source_heading="### Question_Pending File Format",
        destination_file="conversation-protocol.md",
        append=True,
        dispatch_pointer=(
            "For .question_pending format: load `conversation-protocol.md`"
        ),
    ),
    ExtractionRule(
        source_heading="## Module Transition Execution",
        destination_file="module-transitions.md",
        append=True,
        dispatch_pointer="For transition execution: see `module-transitions.md`",
    ),
]

TRANSITIONS_KEEP = [
    "Module Start Banner",
    "Journey Map (at module start)",
    "Before/After Framing (at module start)",
    "Step-Level Progress",
    "Module Completion",
    "Transition Integrity",
    "Confirmation Response Requirements",
]

TRANSITIONS_EXTRACT = [
    "Quality Feedback Loop",
    "Sub-Step Convention",
]

COMPRESSION_TARGETS = [
    CompressTarget(filename="hook-registry-critical.md", max_token_ratio=0.70),
    CompressTarget(filename="hook-registry-modules.md", max_token_ratio=0.70),
    CompressTarget(filename="module-03-system-verification.md", max_token_ratio=0.75),
    CompressTarget(filename="onboarding-flow.md", max_token_ratio=0.75),
]

ALWAYS_ON_COMPRESS_TARGETS = [
    CompressTarget(filename="agent-instructions.md", max_token_ratio=0.85),
    CompressTarget(filename="module-transitions.md", max_token_ratio=0.85),
]

DEFAULT_KEYWORD_MAPPINGS: dict[str, str] = {
    "sdk method discovery": "mcp-usage-reference.md",
    "which tool": "mcp-usage-reference.md",
    "mcp tool": "mcp-usage-reference.md",
    "transition": "module-transitions-detail.md",
    "sub-step": "module-transitions-detail.md",
    "quality loop": "module-transitions-detail.md",
    "question_pending": "conversation-protocol.md",
    "question format": "conversation-protocol.md",
}


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def token_count(text: str) -> int:
    """Approximate token count: round(len(text) / 4)."""
    return round(len(text) / 4)


def size_category(tokens: int) -> str:
    """Return size category based on token count thresholds.

    Args:
        tokens: Approximate token count of a file.

    Returns:
        "small" if under 500, "medium" if 500-2000, "large" if over 2000.
    """
    if tokens < 500:
        return "small"
    elif tokens <= 2000:
        return "medium"
    else:
        return "large"


# ---------------------------------------------------------------------------
# Rule Preservation (Behavioral Correctness Validator)
# ---------------------------------------------------------------------------

# Regex patterns for identifying rule categories
_GATE_MARKER_RE = re.compile(r"⛔")
_QUESTION_MARKER_RE = re.compile(r"👉")
_MCP_DIRECTIVE_RE = re.compile(
    r"\b(SHALL|NEVER|MUST|ALWAYS)\b",
)
_HOOK_RULE_RE = re.compile(
    r"(\.kiro\.hook|createHook|hook-id|hook.*naming"
    r'|"name"|"version"|"when"|"then"'
    r"|hook_categories|hooks_installed)",
    re.IGNORECASE,
)
_FILE_PLACEMENT_RE = re.compile(
    r"(file\s+placement|root\s+prohibit|belongs\s+in\s+[`\"]"
    r"|correct\s+location|blocked\s+type"
    r"|never\s+place.*root|redirect\s+to\s+[`\"]"
    r"|all\s+files\s+within\s+working\s+directory)",
    re.IGNORECASE,
)


def _normalize_rule(line: str) -> str:
    """Strip whitespace and normalize a rule line for comparison.

    Args:
        line: Raw line from a steering file.

    Returns:
        Stripped and whitespace-normalized string.
    """
    return " ".join(line.split())


def extract_rule_inventory(file_paths: list[Path]) -> RuleInventory:
    """Extract all behavioral rules from a set of files.

    Parses files for:
    - ⛔ gate markers (lines containing ⛔)
    - 👉 question markers (lines containing 👉)
    - SHALL/NEVER/MUST/ALWAYS directives (MCP-first invariant statements)
    - Hook definitions (hook creation/naming rules)
    - File placement rules

    Args:
        file_paths: List of paths to steering files to analyze.

    Returns:
        RuleInventory with all discovered behavioral rules.
    """
    inventory = RuleInventory()

    for file_path in file_paths:
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            normalized = _normalize_rule(stripped)

            # Gate markers: lines containing ⛔
            if _GATE_MARKER_RE.search(stripped):
                if normalized not in inventory.gate_markers:
                    inventory.gate_markers.append(normalized)

            # Question markers: lines containing 👉
            if _QUESTION_MARKER_RE.search(stripped):
                if normalized not in inventory.question_markers:
                    inventory.question_markers.append(normalized)

            # MCP rules: lines with SHALL/NEVER/MUST/ALWAYS directives
            if _MCP_DIRECTIVE_RE.search(stripped):
                if normalized not in inventory.mcp_rules:
                    inventory.mcp_rules.append(normalized)

            # Hook rules: lines referencing hook patterns
            if _HOOK_RULE_RE.search(stripped):
                if normalized not in inventory.hook_rules:
                    inventory.hook_rules.append(normalized)

            # File placement rules: lines about file/directory placement
            if _FILE_PLACEMENT_RE.search(stripped):
                if normalized not in inventory.file_rules:
                    inventory.file_rules.append(normalized)

    return inventory


def verify_preservation(
    original: RuleInventory,
    optimized: RuleInventory,
) -> list[str]:
    """Compare inventories, return list of missing rules.

    Args:
        original: Rule inventory from original files.
        optimized: Rule inventory from optimized files.

    Returns:
        List of missing rule descriptions. Empty list means all preserved.
    """
    missing: list[str] = []

    # Check each category for missing rules
    for gate in original.gate_markers:
        if gate not in optimized.gate_markers:
            missing.append(f"Missing gate marker: {gate}")

    for question in original.question_markers:
        if question not in optimized.question_markers:
            missing.append(f"Missing question marker: {question}")

    for mcp_rule in original.mcp_rules:
        if mcp_rule not in optimized.mcp_rules:
            missing.append(f"Missing MCP rule: {mcp_rule}")

    for hook_rule in original.hook_rules:
        if hook_rule not in optimized.hook_rules:
            missing.append(f"Missing hook rule: {hook_rule}")

    for file_rule in original.file_rules:
        if file_rule not in optimized.file_rules:
            missing.append(f"Missing file placement rule: {file_rule}")

    # Also check total count mismatch
    if original.total_count != optimized.total_count:
        missing.append(
            f"Total rule count mismatch: original={original.total_count}, "
            f"optimized={optimized.total_count}"
        )

    return missing


# ---------------------------------------------------------------------------
# SplitEngine (Section Extraction)
# ---------------------------------------------------------------------------


def _parse_sections(content: str) -> list[tuple[str, str, int]]:
    """Parse markdown content into sections by H2/H3 headings.

    Each section is a tuple of (heading_text, section_content, heading_level).
    The first section (before any heading) has heading_text="" and level=0.

    Args:
        content: Full markdown file content.

    Returns:
        List of (heading_text, full_section_content_including_heading, level) tuples.
    """
    lines = content.split("\n")
    sections: list[tuple[str, str, int]] = []
    current_heading = ""
    current_level = 0
    current_lines: list[str] = []

    for line in lines:
        # Check for H2 or H3 heading
        if line.startswith("### ") and not line.startswith("#### "):
            # Save previous section
            if current_lines or current_heading:
                sections.append((
                    current_heading,
                    "\n".join(current_lines),
                    current_level,
                ))
            current_heading = line.lstrip("#").strip()
            current_level = 3
            current_lines = [line]
        elif line.startswith("## ") and not line.startswith("### "):
            # Save previous section
            if current_lines or current_heading:
                sections.append((
                    current_heading,
                    "\n".join(current_lines),
                    current_level,
                ))
            current_heading = line.lstrip("#").strip()
            current_level = 2
            current_lines = [line]
        else:
            current_lines.append(line)

    # Save final section
    if current_lines or current_heading:
        sections.append((current_heading, "\n".join(current_lines), current_level))

    return sections


def _get_section_with_subsections(
    sections: list[tuple[str, str, int]],
    heading: str,
) -> tuple[int, str] | None:
    """Find a section by heading, including subsections until next same/higher level.

    Args:
        sections: Parsed sections from _parse_sections().
        heading: The heading text to match (without # prefix).

    Returns:
        Tuple of (section_index, full_content) or None if not found.
    """
    target_idx: int | None = None
    target_level: int = 0

    for i, (sec_heading, _content, level) in enumerate(sections):
        if sec_heading == heading.lstrip("#").strip():
            target_idx = i
            target_level = level
            break

    if target_idx is None:
        return None

    # Collect this section and all subsections (higher level number = deeper nesting)
    collected_parts: list[str] = [sections[target_idx][1]]

    for i in range(target_idx + 1, len(sections)):
        _heading, sec_content, sec_level = sections[i]
        # Stop at same or higher level (lower or equal number)
        if sec_level <= target_level:
            break
        collected_parts.append(sec_content)

    full_content = "\n".join(collected_parts)
    return (target_idx, full_content)


def _count_subsections(
    sections: list[tuple[str, str, int]],
    start_idx: int,
    target_level: int,
) -> int:
    """Count how many consecutive subsections follow start_idx at deeper levels.

    Args:
        sections: Parsed sections.
        start_idx: Index of the parent section.
        target_level: Level of the parent section.

    Returns:
        Number of subsections that belong to the parent.
    """
    count = 0
    for i in range(start_idx + 1, len(sections)):
        if sections[i][2] <= target_level:
            break
        count += 1
    return count


def _create_file_with_frontmatter(
    path: Path,
    heading: str,
) -> None:
    """Create a new steering file with YAML frontmatter.

    Args:
        path: Path to create the file at.
        heading: Source heading used to generate the description.
    """
    frontmatter = (
        "---\n"
        "inclusion: auto\n"
        f'description: "[Generated from {heading}]"\n'
        "---\n\n"
    )
    path.write_text(frontmatter, encoding="utf-8")


def _count_non_blank_lines(content: str) -> int:
    """Count non-blank lines in content, excluding YAML frontmatter delimiters.

    Args:
        content: File content to count.

    Returns:
        Number of non-blank lines (excluding frontmatter --- delimiters).
    """
    lines = content.split("\n")
    count = 0
    in_frontmatter = False
    frontmatter_seen = False

    for line in lines:
        if line.strip() == "---":
            if not frontmatter_seen:
                in_frontmatter = True
                frontmatter_seen = True
                continue
            elif in_frontmatter:
                in_frontmatter = False
                continue
        if in_frontmatter:
            continue
        if line.strip():
            count += 1

    return count


def _heading_matches(heading: str, section_names: list[str]) -> bool:
    """Check if a heading matches any entry in a section name list.

    Uses startswith matching to handle headings with parenthetical suffixes
    (e.g., "Quality Feedback Loop (Module 7: ...)" matches "Quality Feedback Loop").

    Args:
        heading: The full heading text from _parse_sections().
        section_names: List of section name prefixes to match against.

    Returns:
        True if the heading starts with any entry in section_names.
    """
    for name in section_names:
        if heading == name or heading.startswith(name + " ") or heading.startswith(
            name + "("
        ):
            return True
    return False


def split_transitions_file(
    source_path: Path,
    keep_sections: list[str],
    extract_sections: list[str],
    steering_dir: Path,
) -> SplitResult:
    """Split module-transitions.md into core and detail files.

    Keeps only sections matching keep_sections in the always-on file, and
    extracts sections matching extract_sections to a new auto-inclusion file
    named module-transitions-detail.md.

    Args:
        source_path: Path to module-transitions.md.
        keep_sections: List of section heading texts to retain in always-on file.
        extract_sections: List of section heading texts to extract to detail file.
        steering_dir: Path to the steering directory for the detail file.

    Returns:
        SplitResult with metrics about the split operation.
    """
    content = source_path.read_text(encoding="utf-8")
    sections = _parse_sections(content)

    # Separate preamble (frontmatter + title) from body sections
    # The first section (heading="" level=0) is the preamble/frontmatter
    kept_parts: list[str] = []
    extracted_parts: list[str] = []
    extracted_headings: list[str] = []

    for heading, sec_content, _level in sections:
        if heading == "":
            # Preamble/frontmatter — always keep
            kept_parts.append(sec_content)
        elif _heading_matches(heading, keep_sections):
            kept_parts.append(sec_content)
        elif _heading_matches(heading, extract_sections):
            extracted_parts.append(sec_content)
            extracted_headings.append(heading)
        else:
            # Sections not in either list — keep in always-on file
            kept_parts.append(sec_content)

    # Write the reduced always-on file
    new_core_content = "\n".join(kept_parts)
    # Clean up excessive blank lines
    while "\n\n\n\n" in new_core_content:
        new_core_content = new_core_content.replace("\n\n\n\n", "\n\n\n")
    source_path.write_text(new_core_content, encoding="utf-8")

    # Create module-transitions-detail.md with proper frontmatter and extracted content
    detail_path = steering_dir / "module-transitions-detail.md"
    detail_frontmatter = (
        "---\n"
        "inclusion: auto\n"
        "description: \"Detailed module transition rules:"
        " Quality Feedback Loop, Sub-Step Convention\"\n"
        "keywords:\n"
        "  - transition\n"
        "  - sub-step\n"
        "  - quality loop\n"
        "---\n\n"
    )
    detail_body = "\n".join(extracted_parts)
    detail_path.write_text(detail_frontmatter + detail_body + "\n", encoding="utf-8")

    # Count non-blank lines in resulting core file
    core_line_count = _count_non_blank_lines(new_core_content)

    if core_line_count > 60:
        print(
            f"Warning: {source_path.name} has {core_line_count} non-blank lines "
            f"(exceeds 60 line target).",
            file=sys.stderr,
        )

    return SplitResult(
        source_path=source_path,
        core_line_count=core_line_count,
        extracted_sections=extracted_headings,
        destination_files=[detail_path],
        dispatch_pointers=[],
    )


def split_always_on_file(
    source_path: Path,
    rules: list[ExtractionRule],
    steering_dir: Path,
) -> SplitResult:
    """Extract sections from an always-on file per the given rules.

    Parses the source file into sections by H2/H3 headings, extracts sections
    matching each rule's source_heading, writes them to destination files, and
    replaces extracted sections with dispatch pointers in the source file.

    Args:
        source_path: Path to the always-on source file.
        rules: List of ExtractionRule defining what to extract and where.
        steering_dir: Path to the steering directory for destination files.

    Returns:
        SplitResult with metrics about the split operation.
    """
    content = source_path.read_text(encoding="utf-8")
    sections = _parse_sections(content)

    extracted_sections: list[str] = []
    destination_files: list[Path] = []
    dispatch_pointers: list[str] = []

    # Track which section indices to remove (replace with dispatch pointer)
    # Maps section_index -> (dispatch_pointer_text, subsection_count)
    removals: dict[int, tuple[str, int]] = {}

    for rule in rules:
        # Find the section matching the rule's source_heading
        heading_text = rule.source_heading.lstrip("#").strip()
        result = _get_section_with_subsections(sections, heading_text)

        if result is None:
            print(
                f"Warning: heading '{rule.source_heading}' not found in "
                f"{source_path.name}, skipping.",
                file=sys.stderr,
            )
            continue

        section_idx, section_content = result

        # Determine destination path
        dest_path = steering_dir / rule.destination_file

        # Write to destination file
        if dest_path.exists():
            if rule.append:
                # Append to existing file
                existing = dest_path.read_text(encoding="utf-8")
                if not existing.endswith("\n"):
                    existing += "\n"
                dest_path.write_text(
                    existing + "\n" + section_content + "\n",
                    encoding="utf-8",
                )
            else:
                # Overwrite (shouldn't normally happen with append=True rules)
                dest_path.write_text(section_content + "\n", encoding="utf-8")
        else:
            # Create new file with YAML frontmatter
            _create_file_with_frontmatter(dest_path, rule.source_heading)
            existing = dest_path.read_text(encoding="utf-8")
            dest_path.write_text(
                existing + section_content + "\n",
                encoding="utf-8",
            )

        # Track the extraction
        extracted_sections.append(heading_text)
        destination_files.append(dest_path)
        dispatch_pointers.append(rule.dispatch_pointer)

        # Mark section (and its subsections) for removal
        target_level = sections[section_idx][2]
        subsection_count = _count_subsections(sections, section_idx, target_level)
        removals[section_idx] = (rule.dispatch_pointer, subsection_count)

    # Rebuild the source file with dispatch pointers replacing extracted sections
    new_sections: list[str] = []
    skip_until: int = -1

    for i, (_heading, sec_content, _level) in enumerate(sections):
        if i <= skip_until:
            continue

        if i in removals:
            pointer_text, sub_count = removals[i]
            # Insert dispatch pointer as a single line
            new_sections.append(f"> {pointer_text}")
            # Skip this section's subsections
            skip_until = i + sub_count
        else:
            new_sections.append(sec_content)

    # Write the modified source file
    new_content = "\n".join(new_sections)
    # Clean up excessive blank lines (more than 2 consecutive)
    while "\n\n\n\n" in new_content:
        new_content = new_content.replace("\n\n\n\n", "\n\n\n")
    source_path.write_text(new_content, encoding="utf-8")

    # Count non-blank lines in resulting core file
    core_line_count = _count_non_blank_lines(new_content)

    if core_line_count > 80:
        print(
            f"Warning: {source_path.name} has {core_line_count} non-blank lines "
            f"(exceeds 80 line target).",
            file=sys.stderr,
        )

    return SplitResult(
        source_path=source_path,
        core_line_count=core_line_count,
        extracted_sections=extracted_sections,
        destination_files=destination_files,
        dispatch_pointers=dispatch_pointers,
    )


# ---------------------------------------------------------------------------
# Phase Implementations
# ---------------------------------------------------------------------------


def split_phase(steering_dir: Path, dry_run: bool = False) -> list[SplitResult]:
    """Execute the split phase: extract sections from always-on files.

    Args:
        steering_dir: Path to the steering directory.
        dry_run: If True, report changes without writing files.

    Returns:
        List of SplitResult for each processed file.
    """
    results: list[SplitResult] = []

    # Split agent-instructions.md
    agent_instructions_path = steering_dir / "agent-instructions.md"
    if agent_instructions_path.exists():
        if dry_run:
            print(f"[DRY RUN] Would split: {agent_instructions_path.name}")
            # Return empty result for dry-run
            results.append(SplitResult(
                source_path=agent_instructions_path,
                core_line_count=0,
                extracted_sections=[
                    r.source_heading for r in AGENT_INSTRUCTIONS_EXTRACTIONS
                ],
                destination_files=[
                    steering_dir / r.destination_file
                    for r in AGENT_INSTRUCTIONS_EXTRACTIONS
                ],
                dispatch_pointers=[
                    r.dispatch_pointer for r in AGENT_INSTRUCTIONS_EXTRACTIONS
                ],
            ))
        else:
            result = split_always_on_file(
                source_path=agent_instructions_path,
                rules=AGENT_INSTRUCTIONS_EXTRACTIONS,
                steering_dir=steering_dir,
            )
            results.append(result)

    # Split module-transitions.md
    transitions_path = steering_dir / "module-transitions.md"
    if transitions_path.exists():
        if dry_run:
            print(f"[DRY RUN] Would split: {transitions_path.name}")
            results.append(SplitResult(
                source_path=transitions_path,
                core_line_count=0,
                extracted_sections=list(TRANSITIONS_EXTRACT),
                destination_files=[steering_dir / "module-transitions-detail.md"],
                dispatch_pointers=[],
            ))
        else:
            result = split_transitions_file(
                source_path=transitions_path,
                keep_sections=TRANSITIONS_KEEP,
                extract_sections=TRANSITIONS_EXTRACT,
                steering_dir=steering_dir,
            )
            results.append(result)

    return results


# ---------------------------------------------------------------------------
# CompressEngine (Refine-Style Optimization)
# ---------------------------------------------------------------------------

# Filler words/phrases to remove (case-insensitive, whole-phrase match)
_FILLER_PHRASES = [
    "In order to",
    "It is important to note that",
    "Please note that",
    "As mentioned earlier",
    "It should be noted that",
    "It is worth noting that",
    "Keep in mind that",
    "It's important to understand that",
    "As you can see",
    "In this case",
    "At this point",
    "The reason for this is that",
    "What this means is that",
    "Note that",
    "Be aware that",
    "Remember that",
    "Make sure to",
    "You need to",
    "You should",
    "You will need to",
    "You can then",
    "You may want to",
    "This is because",
    "This means that",
    "This ensures that",
    "This will",
    "This allows",
]

# Single filler words to remove when surrounded by spaces
_FILLER_WORDS = [
    "basically",
    "essentially",
    "actually",
    "simply",
    "just",
    "really",
    "very",
    "quite",
    "certainly",
    "obviously",
    "clearly",
    "effectively",
    "generally",
    "typically",
    "specifically",
    "particularly",
]

# Transitional phrases to remove
_TRANSITIONAL_PHRASES = [
    "First of all",
    "Moving on to",
    "Now let's",
    "Next we will",
    "As we can see",
    "Let's now look at",
    "Now that we have",
    "With that in mind",
    "Having said that",
    "That being said",
    "In the following section",
    "The following section describes",
    "In the next section",
    "At this point",
    "From here",
    "Going forward",
    "After that",
    "Once complete",
    "When done",
    "After this",
    "Following this",
]

# Verbose preambles to compress
_VERBOSE_PREAMBLES = [
    "The following is a list of",
    "The following are",
    "Here is a list of",
    "Below is a list of",
    "The following items",
    "Listed below are",
]

# Regex for WHEN/THEN patterns
_WHEN_THEN_RE = re.compile(
    r"^\s*(?:WHEN|When|when)\s+(.+?),?\s+(?:THEN|Then|then)\s+(.+?)\.?\s*$",
)

# Regex for sentence boundary detection
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

# Protected line patterns
_PROTECTED_LINE_RE = re.compile(
    r"(⛔|👉|\.kiro\.hook|createHook|hook-id"
    r"|^\s*\d+\.\s"  # Step numbers at start of line
    r"|^---\s*$"  # YAML frontmatter delimiter
    r"|^\s*#"  # Markdown headings
    r")",
    re.MULTILINE,
)

# YAML frontmatter block detection
_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _is_protected_line(line: str) -> bool:
    """Check if a line contains protected markers that must not be modified.

    Protected lines include:
    - Lines containing ⛔ or 👉 markers
    - Lines with hook names (.kiro.hook, createHook)
    - Lines with step numbers (e.g., "1.", "2." at start)
    - YAML frontmatter delimiters (---)
    - Markdown headings (lines starting with #)
    - Lines that are part of code blocks (``` fenced)
    - Lines containing SHALL/NEVER/MUST/ALWAYS directives
    - Lines matching hook rule patterns
    - Lines matching file placement rule patterns

    Args:
        line: A single line of text.

    Returns:
        True if the line should not be modified.
    """
    stripped = line.strip()

    # Empty lines are not protected but also not compressible
    if not stripped:
        return True

    # Markers
    if "⛔" in stripped or "👉" in stripped:
        return True

    # Hook references
    if ".kiro.hook" in stripped or "createHook" in stripped or "hook-id" in stripped:
        return True

    # Step numbers at start of line (e.g., "1. ", "2. ", "10. ")
    if re.match(r"^\d+\.\s", stripped):
        return True

    # YAML frontmatter delimiters
    if stripped == "---":
        return True

    # Markdown headings
    if stripped.startswith("#"):
        return True

    # Code block fences
    if stripped.startswith("```") or stripped.startswith("````"):
        return True

    # Lines with pipe tables (markdown table rows)
    if stripped.startswith("|") and "|" in stripped[1:]:
        return True

    # Lines with SHALL/NEVER/MUST/ALWAYS directives (behavioral rules)
    if re.search(r"\b(SHALL|NEVER|MUST|ALWAYS)\b", stripped):
        return True

    # Lines matching hook rule patterns (hook definitions, naming conventions)
    if _HOOK_RULE_RE.search(stripped):
        return True

    # Lines matching file placement rule patterns
    if _FILE_PLACEMENT_RE.search(stripped):
        return True

    # Bullet points that contain markers
    if stripped.startswith("- ") or stripped.startswith("* "):
        inner = stripped[2:]
        if "⛔" in inner or "👉" in inner or ".kiro.hook" in inner:
            return True

    return False


def _is_in_code_block(lines: list[str], line_idx: int) -> bool:
    """Check if a line is inside a fenced code block.

    Args:
        lines: All lines in the file.
        line_idx: Index of the line to check.

    Returns:
        True if the line is inside a code block.
    """
    in_code = False
    for i in range(line_idx):
        stripped = lines[i].strip()
        if stripped.startswith("```") or stripped.startswith("````"):
            in_code = not in_code
    return in_code


def _remove_filler_phrases(text: str) -> str:
    """Remove filler phrases from text while preserving meaning.

    Args:
        text: Input text to clean.

    Returns:
        Text with filler phrases removed.
    """
    result = text
    for phrase in _FILLER_PHRASES:
        # Case-insensitive replacement, handle start of sentence
        pattern = re.compile(re.escape(phrase) + r"\s*,?\s*", re.IGNORECASE)
        result = pattern.sub("", result)

    return result


def _remove_filler_words(text: str) -> str:
    """Remove standalone filler words from text.

    Only removes words when they appear as standalone modifiers,
    not when they're part of compound words or technical terms.

    Args:
        text: Input text to clean.

    Returns:
        Text with filler words removed.
    """
    result = text
    for word in _FILLER_WORDS:
        # Match word surrounded by spaces (not part of larger word)
        pattern = re.compile(r"\s+" + re.escape(word) + r"\s+", re.IGNORECASE)
        result = pattern.sub(" ", result)

    return result


def _remove_transitional_phrases(text: str) -> str:
    """Remove transitional phrases from text.

    Args:
        text: Input text to clean.

    Returns:
        Text with transitional phrases removed.
    """
    result = text
    for phrase in _TRANSITIONAL_PHRASES:
        pattern = re.compile(re.escape(phrase) + r"\s*,?\s*", re.IGNORECASE)
        result = pattern.sub("", result)

    return result


def _compress_verbose_preambles(text: str) -> str:
    """Remove verbose list preambles.

    Converts "The following is a list of X:" to "X:" style.

    Args:
        text: Input text to clean.

    Returns:
        Text with verbose preambles compressed.
    """
    result = text
    for preamble in _VERBOSE_PREAMBLES:
        pattern = re.compile(re.escape(preamble) + r"\s*", re.IGNORECASE)
        result = pattern.sub("", result)

    return result


def _compress_when_then_patterns(lines: list[str]) -> list[str]:
    """Convert verbose WHEN/THEN patterns to compact arrow notation.

    Converts "WHEN X happens, THEN Y should occur" to "- X → Y"

    Args:
        lines: List of lines to process.

    Returns:
        List of lines with WHEN/THEN patterns compressed.
    """
    result: list[str] = []
    i = 0
    consecutive_when_then: list[tuple[str, str]] = []

    while i < len(lines):
        line = lines[i]
        match = _WHEN_THEN_RE.match(line)

        if match and not _is_protected_line(line):
            consecutive_when_then.append(
                (match.group(1).strip(), match.group(2).strip())
            )
            i += 1
            continue

        # Flush any accumulated WHEN/THEN patterns
        if consecutive_when_then:
            if len(consecutive_when_then) >= 2:
                # Convert to compact table-like format
                for condition, action in consecutive_when_then:
                    result.append(f"- {condition} → {action}")
            else:
                # Single pattern, just use arrow notation
                for condition, action in consecutive_when_then:
                    result.append(f"- {condition} → {action}")
            consecutive_when_then = []

        result.append(line)
        i += 1

    # Flush remaining
    if consecutive_when_then:
        for condition, action in consecutive_when_then:
            result.append(f"- {condition} → {action}")

    return result


def _prose_to_bullets(text: str) -> str:
    """Convert prose paragraphs of 3+ sentences to bullet lists.

    Only converts paragraphs that are not already in list format,
    don't contain protected markers, and where bullet conversion
    would actually reduce token count.

    Args:
        text: A paragraph of prose text.

    Returns:
        Bullet list if 3+ sentences detected and shorter, otherwise original text.
    """
    # Split into sentences
    sentences = _SENTENCE_END_RE.split(text.strip())

    if len(sentences) < 3:
        return text

    # Check if any sentence contains protected content
    for sentence in sentences:
        if "⛔" in sentence or "👉" in sentence or ".kiro.hook" in sentence:
            return text
        if re.search(r"\b(SHALL|NEVER|MUST|ALWAYS)\b", sentence):
            return text

    # Convert to bullet list
    bullets: list[str] = []
    for sentence in sentences:
        cleaned = sentence.strip().rstrip(".")
        if cleaned:
            bullets.append(f"- {cleaned}")

    bullet_text = "\n".join(bullets)

    # Only use bullets if they're actually shorter
    if len(bullet_text) < len(text):
        return bullet_text

    return text


def _compress_paragraph(paragraph: str) -> str:
    """Apply all compression techniques to a single paragraph.

    Args:
        paragraph: A non-protected paragraph of text.

    Returns:
        Compressed paragraph.
    """
    result = paragraph

    # Remove filler phrases
    result = _remove_filler_phrases(result)

    # Remove transitional phrases
    result = _remove_transitional_phrases(result)

    # Remove filler words
    result = _remove_filler_words(result)

    # Compress verbose preambles
    result = _compress_verbose_preambles(result)

    # Compress decorative separator lines (═══════ etc.)
    if re.match(r"^[═─━╌╍┄┅]+$", result.strip()):
        return "---"

    # Compress "If X is/are true" → "If X"
    result = re.sub(r"(?:all )?of the following are true,?\s*", "", result, flags=re.I)
    result = re.sub(
        r"all of these conditions:\s*", "these conditions:", result, flags=re.I
    )

    # Remove redundant "output is none" restatements
    result = re.sub(
        r"\s*(?:Phase \d+ )?[Oo]utput is none\.\s*",
        " ",
        result,
    )

    # Compress "If X: skip to Y" patterns
    result = re.sub(
        r"If (?:ANY|any) (.+?) (?:condition )?fails?:\s*",
        r"If \1 fails: ",
        result,
    )

    # Remove "your COMPLETE response is" → "respond with"
    result = re.sub(
        r"your COMPLETE response is",
        "respond with",
        result,
    )

    # Compress "Before producing ANY X output, verify ALL of these conditions:"
    result = re.sub(
        r"Before producing ANY (.+?) output, verify ALL of these conditions:",
        r"Before \1 output, verify:",
        result,
    )

    # Compress "the bootcamper" → "user" (common verbose reference)
    result = re.sub(r"\bthe bootcamper\b", "user", result)
    result = re.sub(r"\bbootcamper\b", "user", result)

    # Compress "the most recent assistant message" → "last response"
    result = re.sub(
        r"the most recent assistant message",
        "last response",
        result,
    )

    # Compress "does NOT exist" → "missing"
    result = re.sub(r"does NOT exist", "missing", result)
    result = re.sub(r"does not exist", "missing", result)

    # Compress "produce no output at all" → "output nothing"
    result = re.sub(r"produce no output at all", "output nothing", result)
    result = re.sub(r"produce no output", "output nothing", result)

    # Compress "a single period character: ." → "just: ."
    result = re.sub(r"a single period character: \.", "just: .", result)

    # Compress "If the file does not exist or" → "If missing or"
    result = re.sub(
        r"If the file (?:does not|doesn't) exist or",
        "If missing or",
        result,
    )

    # Compress "in the conversation history" → "in history"
    result = re.sub(r"in the conversation history", "in history", result)

    # Compress "the following" → remove when before a colon
    result = re.sub(r"the following\s*:", ":", result)

    # Compress "in order to" (case insensitive)
    result = re.sub(r"\bin order to\b", "to", result, flags=re.I)

    # Compress "whether or not" → "whether"
    result = re.sub(r"whether or not", "whether", result)

    # Compress "at this point in time" → "now"
    result = re.sub(r"at this point in time", "now", result, flags=re.I)

    # Compress "on a per-X basis" → "per X"
    result = re.sub(r"on a per-(\w+) basis", r"per \1", result)

    # Compress "is able to" → "can"
    result = re.sub(r"is able to", "can", result)

    # Compress "in the event that" → "if"
    result = re.sub(r"in the event that", "if", result, flags=re.I)

    # Compress "for the purpose of" → "to"
    result = re.sub(r"for the purpose of", "to", result, flags=re.I)

    # Compress "prior to" → "before"
    result = re.sub(r"\bprior to\b", "before", result, flags=re.I)

    # Compress "subsequent to" → "after"
    result = re.sub(r"\bsubsequent to\b", "after", result, flags=re.I)

    # Compress "with respect to" → "regarding"
    result = re.sub(r"with respect to", "regarding", result, flags=re.I)

    # Compress "a number of" → "several"
    result = re.sub(r"\ba number of\b", "several", result, flags=re.I)

    # Compress "due to the fact that" → "because"
    result = re.sub(r"due to the fact that", "because", result, flags=re.I)

    # Remove verbose "do not" repetitions at start
    # "Do NOT X. Do NOT Y. Do NOT Z." → "Do NOT: X; Y; Z."
    do_not_matches = re.findall(r"Do NOT ([^.]+)\.", result)
    if len(do_not_matches) >= 3:
        combined = "; ".join(do_not_matches)
        result = re.sub(
            r"(?:Do NOT [^.]+\.\s*){3,}",
            f"Do NOT: {combined}. ",
            result,
        )

    # Convert prose to bullets if 3+ sentences and shorter
    result = _prose_to_bullets(result)

    # Clean up double spaces
    result = re.sub(r"  +", " ", result)

    # Clean up leading/trailing whitespace on lines
    lines = result.split("\n")
    lines = [line.strip() for line in lines]
    result = "\n".join(lines)

    return result


def compress_file(
    file_path: Path,
    target: CompressTarget,
) -> CompressResult:
    """Compress a file using Refine-style optimization.

    Identifies compressible regions and applies transformations while
    preserving all behavioral markers verbatim.

    Args:
        file_path: Path to the steering file to compress.
        target: CompressTarget with filename and max_token_ratio.

    Returns:
        CompressResult with metrics about the compression.
    """
    content = file_path.read_text(encoding="utf-8")
    original_tokens = token_count(content)

    # Extract rule inventory before compression
    original_inventory = extract_rule_inventory([file_path])

    # Split content into frontmatter and body
    frontmatter = ""
    body = content
    fm_match = _FRONTMATTER_RE.match(content)
    if fm_match:
        frontmatter = fm_match.group(0)
        body = content[fm_match.end():]

    # Process body line by line
    lines = body.split("\n")
    compressed_lines: list[str] = []
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track code block state
        if stripped.startswith("```") or stripped.startswith("````"):
            in_code_block = not in_code_block
            compressed_lines.append(line)
            i += 1
            continue

        # Inside code blocks: compress non-protected lines (hook prompts)
        if in_code_block:
            if _is_protected_line(line):
                compressed_lines.append(line)
                i += 1
                continue

            # Collect consecutive non-protected lines within code block
            paragraph_lines: list[str] = []
            while i < len(lines):
                current = lines[i]
                current_stripped = current.strip()

                # Stop at code block end
                if current_stripped.startswith("```") or current_stripped.startswith(
                    "````"
                ):
                    break
                # Stop at blank lines
                if not current_stripped:
                    break
                # Stop at protected lines
                if _is_protected_line(current):
                    break

                paragraph_lines.append(current)
                i += 1

            if paragraph_lines:
                paragraph_text = " ".join(ln.strip() for ln in paragraph_lines)
                compressed = _compress_paragraph(paragraph_text)
                if compressed.strip():
                    compressed_lines.append(compressed)
            else:
                compressed_lines.append(line)
                i += 1
            continue

        # Outside code blocks: protect structural lines
        if _is_protected_line(line):
            compressed_lines.append(line)
            i += 1
            continue

        # Collect consecutive non-protected, non-blank lines as a paragraph
        paragraph_lines = []
        while i < len(lines):
            current = lines[i]
            current_stripped = current.strip()

            # Stop at blank lines, protected lines, code blocks
            if not current_stripped:
                break
            if _is_protected_line(current):
                break
            if current_stripped.startswith("```") or current_stripped.startswith(
                "````"
            ):
                break

            paragraph_lines.append(current)
            i += 1

        if paragraph_lines:
            # Join paragraph and compress
            paragraph_text = " ".join(ln.strip() for ln in paragraph_lines)
            compressed = _compress_paragraph(paragraph_text)
            if compressed.strip():
                compressed_lines.append(compressed)
        else:
            # Blank line or we broke out — add the current line
            compressed_lines.append(line)
            i += 1

    # Apply WHEN/THEN compression across all lines
    compressed_lines = _compress_when_then_patterns(compressed_lines)

    # Reassemble content
    compressed_body = "\n".join(compressed_lines)

    # Clean up excessive blank lines
    while "\n\n\n\n" in compressed_body:
        compressed_body = compressed_body.replace("\n\n\n\n", "\n\n\n")

    compressed_content = frontmatter + compressed_body

    # Calculate compressed token count
    compressed_tokens = token_count(compressed_content)
    ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
    target_met = ratio <= target.max_token_ratio

    # Verify markers are preserved
    # Write temporarily to check inventory
    file_path.write_text(compressed_content, encoding="utf-8")
    compressed_inventory = extract_rule_inventory([file_path])
    missing = verify_preservation(original_inventory, compressed_inventory)

    markers_preserved = len(missing) == 0

    # If markers are NOT preserved, revert to original
    if not markers_preserved:
        file_path.write_text(content, encoding="utf-8")
        return CompressResult(
            path=file_path,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            ratio=1.0,
            target_met=False,
            markers_preserved=False,
        )

    # Keep the compressed version (already written)
    return CompressResult(
        path=file_path,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        ratio=ratio,
        target_met=target_met,
        markers_preserved=True,
    )


def compress_phase(steering_dir: Path, dry_run: bool = False) -> list[CompressResult]:
    """Execute the compress phase: apply Refine-style optimization.

    Compresses both large manual files (COMPRESSION_TARGETS) and always-on
    files (ALWAYS_ON_COMPRESS_TARGETS). The always-on files are expected to
    have already been reduced by the split phase before this runs.

    Args:
        steering_dir: Path to the steering directory.
        dry_run: If True, report changes without writing files.

    Returns:
        List of CompressResult for each processed file.
    """
    results: list[CompressResult] = []

    # Process all targets: manual files first, then always-on files
    all_targets = list(COMPRESSION_TARGETS) + list(ALWAYS_ON_COMPRESS_TARGETS)

    for target in all_targets:
        file_path = steering_dir / target.filename
        if not file_path.exists():
            continue

        if dry_run:
            content = file_path.read_text(encoding="utf-8")
            original_tokens = token_count(content)
            print(f"[DRY RUN] Would compress: {target.filename} "
                  f"({original_tokens} tokens, target ratio {target.max_token_ratio})")
            results.append(CompressResult(
                path=file_path,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                ratio=1.0,
                target_met=False,
                markers_preserved=True,
            ))
        else:
            result = compress_file(file_path, target)
            results.append(result)

            if not result.target_met:
                print(
                    f"Warning: {target.filename} compression achieved ratio "
                    f"{result.ratio:.2f} (target: {target.max_token_ratio}). "
                    f"Cannot achieve target without semantic loss.",
                    file=sys.stderr,
                )

    return results


def update_index(
    steering_dir: Path,
    index_path: Path,
    new_files: list[Path],
    keyword_mappings: dict[str, str],
) -> None:
    """Update steering-index.yaml after all file changes.

    Runs measure_steering.py in update mode to regenerate file_metadata and
    budget sections, then adds keyword mappings for new files and verifies
    budget consistency.

    Args:
        steering_dir: Path to the steering directory.
        index_path: Path to steering-index.yaml.
        new_files: List of paths to newly created steering files.
        keyword_mappings: Dict mapping keyword strings to filenames
            (e.g., {"sdk method discovery": "mcp-usage-reference.md"}).

    Raises:
        FileNotFoundError: If the index file doesn't exist after update.
        RuntimeError: If measure_steering.py fails (non-zero exit code).
    """
    # Locate measure_steering.py in the same scripts/ directory
    scripts_dir = Path(__file__).resolve().parent
    measure_script = scripts_dir / "measure_steering.py"

    # Run measure_steering.py in update mode (no --check flag)
    cmd = [
        sys.executable,
        str(measure_script),
        "--steering-dir", str(steering_dir),
        "--index-path", str(index_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"measure_steering.py failed with exit code {result.returncode}:\n"
            f"{result.stderr}"
        )

    # Verify the index file exists after update
    if not index_path.exists():
        raise FileNotFoundError(
            f"steering-index.yaml not found at {index_path} after "
            f"measure_steering.py update"
        )

    # Read the updated index content
    content = index_path.read_text(encoding="utf-8")

    # Add keyword mappings for new files to the keywords section
    if keyword_mappings:
        content = _add_keyword_mappings(content, keyword_mappings)

    # Write the updated content back
    index_path.write_text(content, encoding="utf-8")

    # Verify budget.total_tokens equals sum of all token_count values
    _verify_budget_consistency(content, index_path)


def _add_keyword_mappings(content: str, keyword_mappings: dict[str, str]) -> str:
    """Add keyword mappings to the keywords section of steering-index.yaml.

    Inserts new keyword entries into the existing keywords section. Skips
    keywords that already exist with the same file mapping.

    Args:
        content: Full text content of steering-index.yaml.
        keyword_mappings: Dict mapping keyword strings to filenames.

    Returns:
        Updated content with new keyword mappings added.
    """
    # Find the keywords section
    keywords_match = re.search(r"^keywords:\s*\n", content, re.MULTILINE)
    if keywords_match is None:
        # No keywords section found — append one at the end before file_metadata
        fm_match = re.search(r"^file_metadata:\s*$", content, re.MULTILINE)
        if fm_match:
            insert_pos = fm_match.start()
            keywords_block = "keywords:\n"
            for keyword, filename in sorted(keyword_mappings.items()):
                keywords_block += f"  {keyword}: {filename}\n"
            keywords_block += "\n"
            content = content[:insert_pos] + keywords_block + content[insert_pos:]
        else:
            # Append at end
            keywords_block = "\nkeywords:\n"
            for keyword, filename in sorted(keyword_mappings.items()):
                keywords_block += f"  {keyword}: {filename}\n"
            content += keywords_block
        return content

    # Find the end of the keywords section (next top-level key or end of file)
    keywords_start = keywords_match.end()
    # Look for the next non-indented, non-blank, non-comment line after keywords:
    remaining = content[keywords_start:]
    next_section_match = re.search(r"^\S", remaining, re.MULTILINE)
    if next_section_match:
        keywords_end = keywords_start + next_section_match.start()
    else:
        keywords_end = len(content)

    # Parse existing keywords to avoid duplicates
    keywords_block = content[keywords_match.start():keywords_end]
    existing_entries: set[str] = set()
    for line in keywords_block.splitlines():
        entry_match = re.match(r"^\s+(.+?):\s+(.+)$", line)
        if entry_match:
            existing_entries.add(f"{entry_match.group(1).strip()}:{entry_match.group(2).strip()}")

    # Build new entries to insert
    new_lines: list[str] = []
    for keyword, filename in sorted(keyword_mappings.items()):
        entry_key = f"{keyword}:{filename}"
        if entry_key not in existing_entries:
            new_lines.append(f"  {keyword}: {filename}")

    if not new_lines:
        return content

    # Insert new entries at the end of the keywords section (before the next section)
    insert_text = "\n".join(new_lines) + "\n"
    content = content[:keywords_end] + insert_text + content[keywords_end:]

    return content


def _verify_budget_consistency(content: str, index_path: Path) -> None:
    """Verify budget.total_tokens equals sum of all token_count values.

    Prints a warning if the values don't match but does not fail.

    Args:
        content: Full text content of steering-index.yaml.
        index_path: Path to the index file (for error messages).
    """
    # Extract all token_count values from file_metadata
    fm_match = re.search(r"^file_metadata:\s*$", content, re.MULTILINE)
    if fm_match is None:
        print(
            f"Warning: no file_metadata section found in {index_path}",
            file=sys.stderr,
        )
        return

    # Extract the file_metadata block
    fm_start = fm_match.end()
    remaining = content[fm_start:]
    next_section = re.search(r"^\S", remaining, re.MULTILINE)
    if next_section:
        fm_block = remaining[:next_section.start()]
    else:
        fm_block = remaining

    # Sum token counts within file_metadata
    fm_token_counts = re.findall(r"^\s+token_count:\s*(\d+)", fm_block, re.MULTILINE)
    calculated_total = sum(int(tc) for tc in fm_token_counts)

    # Extract budget.total_tokens
    budget_match = re.search(r"^\s+total_tokens:\s*(\d+)", content, re.MULTILINE)
    if budget_match is None:
        print(
            f"Warning: no budget.total_tokens found in {index_path}",
            file=sys.stderr,
        )
        return

    stored_total = int(budget_match.group(1))

    if stored_total != calculated_total:
        print(
            f"Warning: budget.total_tokens ({stored_total}) does not equal "
            f"sum of file_metadata token_counts ({calculated_total}) in {index_path}",
            file=sys.stderr,
        )


def index_update_phase(
    steering_dir: Path,
    index_path: Path,
    dry_run: bool = False,
    split_results: list[SplitResult] | None = None,
) -> None:
    """Execute the index update phase: synchronize steering-index.yaml.

    Args:
        steering_dir: Path to the steering directory.
        index_path: Path to steering-index.yaml.
        dry_run: If True, report changes without writing files.
        split_results: Results from the split phase, used to determine new files.
    """
    if dry_run:
        print("[DRY RUN] Would update steering-index.yaml")
        return

    # Collect new files from split results
    new_files: list[Path] = []
    if split_results:
        for sr in split_results:
            for dest in sr.destination_files:
                if dest.exists():
                    new_files.append(dest)

    # Use default keyword mappings for new files
    keyword_mappings = dict(DEFAULT_KEYWORD_MAPPINGS)

    update_index(
        steering_dir=steering_dir,
        index_path=index_path,
        new_files=new_files,
        keyword_mappings=keyword_mappings,
    )


# ---------------------------------------------------------------------------
# CI Validation
# ---------------------------------------------------------------------------


def run_ci_validation(steering_dir: Path, index_path: Path) -> list[str]:
    """Run CI validation scripts and return list of failures.

    Runs:
    1. measure_steering.py --check (verify token counts within 10% tolerance)
    2. validate_commonmark.py (verify no markdownlint violations)
    3. validate_power.py (verify cross-references, hooks, frontmatter, versions)

    Args:
        steering_dir: Path to the steering directory.
        index_path: Path to steering-index.yaml.

    Returns:
        List of failure messages. Empty list means all validations passed.
    """
    failures: list[str] = []
    scripts_dir = Path(__file__).resolve().parent

    # Define the validation commands to run
    validations: list[tuple[str, list[str]]] = [
        (
            "measure_steering.py --check",
            [
                sys.executable,
                str(scripts_dir / "measure_steering.py"),
                "--check",
                "--steering-dir", str(steering_dir),
                "--index-path", str(index_path),
            ],
        ),
        (
            "validate_commonmark.py",
            [sys.executable, str(scripts_dir / "validate_commonmark.py")],
        ),
        (
            "validate_power.py",
            [sys.executable, str(scripts_dir / "validate_power.py")],
        ),
    ]

    for script_name, cmd in validations:
        script_path = Path(cmd[1])
        if not script_path.exists():
            print(
                f"Warning: {script_name} not found at {script_path}, skipping.",
                file=sys.stderr,
            )
            continue

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"CI validation '{script_name}' timed out after 120s")
            continue
        except OSError as e:
            failures.append(f"CI validation '{script_name}' failed to execute: {e}")
            continue

        if proc.returncode != 0:
            stderr_msg = proc.stderr.strip() if proc.stderr else "(no stderr output)"
            failures.append(
                f"CI validation '{script_name}' failed with exit code "
                f"{proc.returncode}: {stderr_msg}"
            )

    return failures


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def optimize(
    steering_dir: Path,
    index_path: Path,
    dry_run: bool = False,
) -> OptimizeResult:
    """Run all optimization phases. Returns result with metrics.

    Executes the full optimization pipeline:
    1. RulePreserver: Extract original rule inventory from all steering files
    2. SplitEngine: Split always-on files into core + context-specific files
    3. CompressEngine: Apply Refine-style compression to large files
    4. IndexUpdater: Synchronize steering-index.yaml
    5. RulePreserver: Verify all behavioral rules are preserved

    Args:
        steering_dir: Path to the steering directory.
        index_path: Path to steering-index.yaml.
        dry_run: If True, report changes without writing files.

    Returns:
        OptimizeResult with metrics from all phases.
    """
    result = OptimizeResult()

    # --- Before optimization: Extract original rule inventory ---
    steering_files = list(steering_dir.glob("*.md"))
    original_inventory = extract_rule_inventory(steering_files)

    # --- Phase 1: Split always-on files ---
    result.split_results = split_phase(steering_dir, dry_run=dry_run)

    # --- Phase 2: Compress large manual files AND always-on files (post-split) ---
    result.compress_results = compress_phase(steering_dir, dry_run=dry_run)

    # --- Phase 3: Update steering-index.yaml ---
    index_update_phase(
        steering_dir, index_path, dry_run=dry_run,
        split_results=result.split_results,
    )

    # --- Phase 4: CI validation (skip in dry-run mode) ---
    if not dry_run:
        ci_failures = run_ci_validation(steering_dir, index_path)
        result.failures.extend(ci_failures)

    # --- After optimization: Verify rule preservation ---
    if not dry_run:
        optimized_files = list(steering_dir.glob("*.md"))
        optimized_inventory = extract_rule_inventory(optimized_files)
        missing_rules = verify_preservation(original_inventory, optimized_inventory)

        if missing_rules:
            result.success = False
            for missing in missing_rules:
                result.failures.append(missing)

    # --- Calculate totals ---
    for cr in result.compress_results:
        result.total_token_savings += cr.original_tokens - cr.compressed_tokens
        if not cr.target_met and not dry_run:
            result.failures.append(
                f"{cr.path.name}: achieved {cr.compressed_tokens} tokens "
                f"(ratio {cr.ratio:.2f}), target ratio {cr.ratio:.2f}"
            )

    result.files_modified = (
        len(result.split_results) + len(result.compress_results)
    )

    if result.failures:
        result.success = False

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success, 1 on failure.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Optimize steering file organization for reduced context.",
    )
    parser.add_argument(
        "--steering-dir",
        type=Path,
        default=DEFAULT_STEERING_DIR,
        help=f"Path to steering directory (default: {DEFAULT_STEERING_DIR})",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"Path to steering-index.yaml (default: {DEFAULT_INDEX_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing files",
    )

    args = parser.parse_args(argv)

    result = optimize(
        steering_dir=args.steering_dir,
        index_path=args.index_path,
        dry_run=args.dry_run,
    )

    # Report results
    if args.dry_run:
        print("[DRY RUN] No files were modified.")
        print(f"\nFiles that would be processed: {result.files_modified}")
        # Report expected per-file savings (dry-run shows original tokens only)
        if result.compress_results:
            print("\nCompression targets:")
            for cr in result.compress_results:
                print(f"  {cr.path.name}: {cr.original_tokens} tokens (current)")
        return 0

    # Report per-file token savings from compress results
    print(f"Files modified: {result.files_modified}")
    if result.compress_results:
        print("\nPer-file token savings:")
        for cr in result.compress_results:
            savings = cr.original_tokens - cr.compressed_tokens
            print(
                f"  {cr.path.name}: {cr.original_tokens} → {cr.compressed_tokens} "
                f"(saved {savings} tokens, ratio {cr.ratio:.2f})"
            )

    # Report total savings
    print(f"\nTotal token savings: {result.total_token_savings}")

    # Report failures (including marker mismatches)
    if result.failures:
        print("\nFailures:", file=sys.stderr)
        for failure in result.failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("\nOptimization completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
