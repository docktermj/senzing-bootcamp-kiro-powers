#!/usr/bin/env python3
"""Split large module steering files into phase-level sub-files.

Parses phase boundaries from markdown, writes root + sub-files, and updates
steering-index.yaml with phase metadata.

Usage:
    python senzing-bootcamp/scripts/split_steering.py --module 5
    python senzing-bootcamp/scripts/split_steering.py --module 6
    python senzing-bootcamp/scripts/split_steering.py --module 5 --steering-dir senzing-bootcamp/steering --index-path senzing-bootcamp/steering/steering-index.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_STEERING_DIR = Path("senzing-bootcamp/steering")
DEFAULT_INDEX_PATH = Path("senzing-bootcamp/steering/steering-index.yaml")

# Phase heading pattern: ## Phase <id> — <name> or ## Phase <id>: <name>
# Captures the full heading text after "## "
PHASE_HEADING_RE = re.compile(r"^## (Phase\s+.+)$", re.MULTILINE)

# Checkpoint step pattern: **Checkpoint:** Write step <N>
CHECKPOINT_STEP_RE = re.compile(r"\*\*Checkpoint:\*\*\s*Write\s+step\s+(\d+)")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Phase:
    """Represents a single phase extracted from a module steering file."""
    name: str           # e.g., "Phase 1 — Quality Assessment"
    slug: str           # e.g., "phase1-quality-assessment"
    content: str        # Complete phase markdown content (including heading)
    step_start: int     # First checkpoint step number in this phase
    step_end: int       # Last checkpoint step number in this phase


@dataclass
class SplitResult:
    """Result of splitting a module file."""
    root_path: Path
    sub_files: list[Path] = field(default_factory=list)
    phases: list[Phase] = field(default_factory=list)
    root_token_count: int = 0
    sub_file_token_counts: list[int] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _make_slug(phase_name: str) -> str:
    """Convert a phase heading into a URL-friendly slug.

    Examples:
        "Phase 1 — Quality Assessment" -> "phase1-quality-assessment"
        "Phase A: Build Loading Program" -> "phaseA-build-loading"
        "Phase C: Multi-Source Orchestration (Conditional — 2+ Data Sources)"
            -> "phaseC-multi-source"
    """
    # Remove "Phase " prefix and extract the identifier + name
    text = phase_name.strip()

    # Match "Phase <id> — <name>" or "Phase <id>: <name>" or "Phase <id> <name>"
    m = re.match(
        r"Phase\s+(\w+)\s*(?:—|:|–)\s*(.+)",
        text,
    )
    if not m:
        # Fallback: just slugify the whole thing
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
        return slug

    phase_id = m.group(1)  # "1", "A", etc.
    name_part = m.group(2).strip()

    # Remove parenthetical suffixes like "(Conditional — 2+ Data Sources)"
    name_part = re.sub(r"\s*\(.*\)\s*$", "", name_part)
    # Remove trailing "(Optional)" etc.
    name_part = re.sub(r"\s*\(.*$", "", name_part)

    # Remove filler words before slugifying
    filler_words = {"and", "or", "the", "a", "an", "of", "in", "on", "for", "to", "with"}
    words = name_part.split()
    words = [w for w in words if w.lower() not in filler_words]
    name_part = " ".join(words)

    # Slugify the name part
    slug_name = re.sub(r"[^a-zA-Z0-9]+", "-", name_part.lower()).strip("-")

    # Truncate to keep slugs reasonable (max ~3 words)
    parts = slug_name.split("-")
    if len(parts) > 3:
        slug_name = "-".join(parts[:3])

    return f"phase{phase_id}-{slug_name}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _extract_front_matter(content: str) -> tuple[str, str]:
    """Extract YAML front matter from content.

    Returns:
        Tuple of (front_matter_string, remaining_content).
        front_matter_string includes the --- delimiters.
        If no front matter found, returns ("", content).
    """
    if not content.startswith("---"):
        return "", content

    # Find the closing ---
    end_match = re.search(r"^---\s*$", content[3:], re.MULTILINE)
    if not end_match:
        return "", content

    end_pos = 3 + end_match.end()
    front_matter = content[:end_pos]
    remaining = content[end_pos:]
    return front_matter, remaining


def _extract_step_numbers(text: str) -> list[int]:
    """Extract all checkpoint step numbers from text."""
    return [int(m) for m in CHECKPOINT_STEP_RE.findall(text)]


def parse_phases(content: str) -> tuple[str, str, list[Phase]]:
    """Parse a module steering file into front matter, preamble, and phases.

    Args:
        content: Full markdown content of the module steering file.

    Returns:
        Tuple of (front_matter, preamble_text, list_of_Phase_objects).
        front_matter is the YAML front matter string (including --- delimiters).
        preamble_text includes everything after front matter but before the
        first phase heading.
        Each Phase has: name, slug, content, step_start, step_end.
    """
    front_matter, body = _extract_front_matter(content)

    # Find all phase heading positions
    headings = list(PHASE_HEADING_RE.finditer(body))

    if not headings:
        # No phases found — entire body is preamble
        return front_matter, body, []

    # Preamble is everything before the first phase heading
    preamble = body[:headings[0].start()]

    phases = []
    for i, match in enumerate(headings):
        phase_name = match.group(1)
        start = match.start()

        # Phase content extends to the next phase heading or end of body
        if i + 1 < len(headings):
            end = headings[i + 1].start()
        else:
            end = len(body)

        phase_content = body[start:end]

        # Extract step numbers from this phase's content
        steps = _extract_step_numbers(phase_content)
        step_start = min(steps) if steps else 0
        step_end = max(steps) if steps else 0

        slug = _make_slug(phase_name)

        phases.append(Phase(
            name=phase_name,
            slug=slug,
            content=phase_content,
            step_start=step_start,
            step_end=step_end,
        ))

    return front_matter, preamble, phases


# ---------------------------------------------------------------------------
# File building
# ---------------------------------------------------------------------------

def build_root_file(
    front_matter: str,
    preamble: str,
    phases: list[Phase],
    sub_file_paths: list[str],
) -> str:
    """Build the root file content with preamble and manifest.

    Args:
        front_matter: YAML front matter string (e.g., "---\\ninclusion: manual\\n---").
        preamble: Shared preamble text.
        phases: List of Phase objects for manifest generation.
        sub_file_paths: List of sub-file filenames for the manifest.

    Returns:
        Complete root file content as a string.
    """
    parts = []

    if front_matter:
        parts.append(front_matter)

    parts.append(preamble.rstrip("\n"))

    # Build manifest section
    manifest_lines = [
        "",
        "## Phase Sub-Files",
        "",
    ]
    for phase, path in zip(phases, sub_file_paths):
        step_range = f"steps {phase.step_start}–{phase.step_end}" if phase.step_start else ""
        manifest_lines.append(f"- **{phase.name}** ({step_range}): `{path}`")

    parts.append("\n".join(manifest_lines))
    parts.append("")  # trailing newline

    return "\n".join(parts) + "\n"


def build_sub_file(front_matter: str, phase: Phase) -> str:
    """Build a sub-file for a single phase.

    Args:
        front_matter: YAML front matter string.
        phase: Phase object containing the phase content.

    Returns:
        Complete sub-file content as a string.
    """
    parts = []

    if front_matter:
        parts.append(front_matter)

    # Add the phase content (already includes the ## heading)
    parts.append(phase.content.rstrip("\n"))
    parts.append("")  # trailing newline

    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Token counting (same formula as measure_steering.py)
# ---------------------------------------------------------------------------

def _token_count(text: str) -> int:
    """Approximate token count: round(len(text) / 4)."""
    return round(len(text) / 4)


def _size_category(token_count: int) -> str:
    """Return size category based on token count thresholds."""
    if token_count < 500:
        return "small"
    elif token_count <= 2000:
        return "medium"
    else:
        return "large"


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def split_module(
    module_path: Path,
    output_dir: Path,
    sub_file_names: list[str],
) -> SplitResult:
    """Split a module file into root + sub-files.

    Args:
        module_path: Path to the original module steering file.
        output_dir: Directory to write root and sub-files.
        sub_file_names: Expected sub-file names for each phase.

    Returns:
        SplitResult with root_path, sub_file_paths, and phase metadata.
    """
    content = module_path.read_text(encoding="utf-8")
    front_matter, preamble, phases = parse_phases(content)

    if not phases:
        print(f"Warning: no phase headings found in {module_path}", file=sys.stderr)
        return SplitResult(root_path=module_path)

    if len(phases) != len(sub_file_names):
        raise ValueError(
            f"Expected {len(sub_file_names)} sub-file names but found "
            f"{len(phases)} phases in {module_path}"
        )

    # Use the standard front matter for sub-files
    sub_front_matter = "---\ninclusion: manual\n---"

    # Build and write root file (at the original filename)
    root_content = build_root_file(front_matter, preamble, phases, sub_file_names)
    root_path = output_dir / module_path.name
    root_path.write_text(root_content, encoding="utf-8")

    # Build and write sub-files
    sub_file_paths = []
    sub_file_token_counts = []
    for phase, sub_name in zip(phases, sub_file_names):
        sub_content = build_sub_file(sub_front_matter, phase)
        sub_path = output_dir / sub_name
        sub_path.write_text(sub_content, encoding="utf-8")
        sub_file_paths.append(sub_path)
        sub_file_token_counts.append(_token_count(sub_content))

    return SplitResult(
        root_path=root_path,
        sub_files=sub_file_paths,
        phases=phases,
        root_token_count=_token_count(root_content),
        sub_file_token_counts=sub_file_token_counts,
    )


# ---------------------------------------------------------------------------
# Steering index update
# ---------------------------------------------------------------------------

def _find_section_start(content: str, section_name: str) -> int:
    """Find the start position of a top-level YAML section."""
    pattern = re.compile(rf"^{re.escape(section_name)}:\s*$", re.MULTILINE)
    match = pattern.search(content)
    return match.start() if match else -1


def _find_section_range(content: str, section_name: str) -> tuple[int, int]:
    """Find the start and end positions of a top-level YAML section.

    Returns (start, end) where end is the start of the next top-level section
    or end of content.
    """
    start = _find_section_start(content, section_name)
    if start < 0:
        return -1, -1

    # Find the next top-level key after this section
    after_header = content[start + len(section_name) + 1:]
    next_section = re.search(r"^\S", after_header, re.MULTILINE)
    if next_section:
        end = start + len(section_name) + 1 + next_section.start()
    else:
        end = len(content)

    return start, end


def update_steering_index(
    index_path: Path,
    module_number: int,
    split_result: SplitResult,
) -> None:
    """Update steering-index.yaml with phase metadata for a split module.

    Adds a `phases` map under the module entry, updates `file_metadata`
    with root + sub-file entries, removes the original monolithic entry,
    and recalculates `budget.total_tokens`.
    """
    content = index_path.read_text(encoding="utf-8")

    # --- Update modules section ---
    # Replace the simple string entry with root + phases map
    root_filename = split_result.root_path.name

    # Build the new module entry
    module_lines = [f"  {module_number}:"]
    module_lines.append(f"    root: {root_filename}")
    module_lines.append("    phases:")
    for phase, sub_path, tc in zip(
        split_result.phases,
        split_result.sub_files,
        split_result.sub_file_token_counts,
    ):
        module_lines.append(f"      {phase.slug}:")
        module_lines.append(f"        file: {sub_path.name}")
        module_lines.append(f"        token_count: {tc}")
        module_lines.append(f"        size_category: {_size_category(tc)}")
        module_lines.append(f"        step_range: [{phase.step_start}, {phase.step_end}]")

    new_module_entry = "\n".join(module_lines)

    # Find and replace the existing module entry in the modules section
    # Pattern: "  <N>: <filename>.md" (simple string entry)
    simple_pattern = re.compile(
        rf"^  {module_number}:\s+\S+\.md\s*$",
        re.MULTILINE,
    )
    simple_match = simple_pattern.search(content)

    # Also check for expanded format (already split)
    expanded_pattern = re.compile(
        rf"^  {module_number}:\s*\n(    .+\n)*",
        re.MULTILINE,
    )

    if simple_match:
        content = content[:simple_match.start()] + new_module_entry + content[simple_match.end():]
    else:
        expanded_match = expanded_pattern.search(content)
        if expanded_match:
            content = content[:expanded_match.start()] + new_module_entry + "\n" + content[expanded_match.end():]

    # --- Update file_metadata section ---
    fm_start, fm_end = _find_section_range(content, "file_metadata")
    if fm_start < 0:
        raise ValueError("file_metadata section not found in steering-index.yaml")

    fm_block = content[fm_start:fm_end]

    # Parse existing file_metadata entries
    existing_entries = {}
    current_file = None
    for line in fm_block.splitlines():
        file_match = re.match(r"^  ([\w.-]+\.md):$", line)
        if file_match:
            current_file = file_match.group(1)
            existing_entries[current_file] = {}
            continue
        if current_file:
            tc_match = re.match(r"^\s+token_count:\s*(\d+)", line)
            if tc_match:
                existing_entries[current_file]["token_count"] = int(tc_match.group(1))
            sc_match = re.match(r"^\s+size_category:\s*(\w+)", line)
            if sc_match:
                existing_entries[current_file]["size_category"] = sc_match.group(1)

    # Update root file entry
    existing_entries[root_filename] = {
        "token_count": split_result.root_token_count,
        "size_category": _size_category(split_result.root_token_count),
    }

    # Add sub-file entries
    for sub_path, tc in zip(split_result.sub_files, split_result.sub_file_token_counts):
        existing_entries[sub_path.name] = {
            "token_count": tc,
            "size_category": _size_category(tc),
        }

    # Rebuild file_metadata section
    new_fm_lines = ["file_metadata:"]
    for name in sorted(existing_entries):
        meta = existing_entries[name]
        new_fm_lines.append(f"  {name}:")
        new_fm_lines.append(f"    token_count: {meta['token_count']}")
        new_fm_lines.append(f"    size_category: {meta['size_category']}")

    new_fm_block = "\n".join(new_fm_lines) + "\n"
    content = content[:fm_start] + new_fm_block + content[fm_end:]

    # --- Update budget section ---
    # Recalculate total_tokens
    total_tokens = sum(e["token_count"] for e in existing_entries.values())

    budget_start, budget_end = _find_section_range(content, "budget")
    if budget_start >= 0:
        # Parse existing budget fields to preserve them
        budget_block = content[budget_start:budget_end]
        # Check for split_threshold_tokens
        has_threshold = "split_threshold_tokens" in budget_block

        new_budget_lines = ["budget:"]
        new_budget_lines.append(f"  total_tokens: {total_tokens}")
        new_budget_lines.append("  reference_window: 200000")
        new_budget_lines.append("  warn_threshold_pct: 60")
        new_budget_lines.append("  critical_threshold_pct: 80")
        if has_threshold:
            # Preserve the split_threshold_tokens value
            threshold_match = re.search(r"split_threshold_tokens:\s*(\d+)", budget_block)
            if threshold_match:
                new_budget_lines.append(f"  split_threshold_tokens: {threshold_match.group(1)}")
        new_budget_lines.append("")

        new_budget_block = "\n".join(new_budget_lines)
        content = content[:budget_start] + new_budget_block + content[budget_end:]
    else:
        # Append budget section
        budget_lines = [
            "\nbudget:",
            f"  total_tokens: {total_tokens}",
            "  reference_window: 200000",
            "  warn_threshold_pct: 60",
            "  critical_threshold_pct: 80",
            "",
        ]
        content += "\n".join(budget_lines)

    index_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Split threshold / candidates
# ---------------------------------------------------------------------------

def get_split_candidates(index_path: Path) -> list[str]:
    """Return filenames whose token_count exceeds split_threshold_tokens.

    Reads the steering index and checks each file_metadata entry against
    the budget.split_threshold_tokens value.

    Returns:
        List of filenames that exceed the threshold.
    """
    content = index_path.read_text(encoding="utf-8")

    # Extract split_threshold_tokens from budget section
    threshold_match = re.search(r"split_threshold_tokens:\s*(\d+)", content)
    if not threshold_match:
        return []

    threshold = int(threshold_match.group(1))

    # Parse file_metadata
    fm_start = _find_section_start(content, "file_metadata")
    if fm_start < 0:
        return []

    candidates = []
    current_file = None
    for line in content[fm_start:].splitlines():
        # Stop at next top-level section
        if line and not line.startswith(" ") and not line.startswith("file_metadata"):
            break
        file_match = re.match(r"^  ([\w.-]+\.md):$", line)
        if file_match:
            current_file = file_match.group(1)
            continue
        if current_file:
            tc_match = re.match(r"^\s+token_count:\s*(\d+)", line)
            if tc_match:
                tc = int(tc_match.group(1))
                if tc > threshold:
                    candidates.append(current_file)
                current_file = None

    return candidates


# ---------------------------------------------------------------------------
# Step-to-phase mapping
# ---------------------------------------------------------------------------

def step_to_phase(
    index_path: Path,
    module_number: int,
    step: int,
) -> str | None:
    """Map a checkpoint step number to a phase sub-file.

    Args:
        index_path: Path to steering-index.yaml.
        module_number: Module number (e.g., 5 or 6).
        step: Current checkpoint step number.

    Returns:
        Sub-file filename if a matching phase is found, None otherwise.
    """
    content = index_path.read_text(encoding="utf-8")

    # Find the module's phases section
    # Look for the module entry with phases
    modules_start = _find_section_start(content, "modules")
    if modules_start < 0:
        return None

    # Parse the phases for this module
    # Find "  <N>:" then look for "    phases:" underneath
    module_pattern = re.compile(
        rf"^  {module_number}:\s*$",
        re.MULTILINE,
    )
    module_match = module_pattern.search(content)
    if not module_match:
        return None

    # Extract the module block (until next module entry or section)
    after_module = content[module_match.end():]
    next_entry = re.search(r"^  \d+:", after_module, re.MULTILINE)
    next_section = re.search(r"^\S", after_module, re.MULTILINE)

    end_pos = len(after_module)
    if next_entry:
        end_pos = min(end_pos, next_entry.start())
    if next_section:
        end_pos = min(end_pos, next_section.start())

    module_block = after_module[:end_pos]

    # Parse phase entries
    phase_file = None
    step_range = None
    for line in module_block.splitlines():
        file_match = re.match(r"\s+file:\s*(\S+)", line)
        if file_match:
            phase_file = file_match.group(1)
        range_match = re.match(r"\s+step_range:\s*\[(\d+),\s*(\d+)\]", line)
        if range_match and phase_file:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start <= step <= end:
                return phase_file
            phase_file = None
            step_range = None

    return None


def resolve_sub_file(
    steering_dir: Path,
    index_path: Path,
    module_number: int,
    step: int,
) -> Path:
    """Resolve the sub-file path for a given module and step.

    Falls back to the root file if the sub-file doesn't exist.

    Args:
        steering_dir: Path to the steering directory.
        index_path: Path to steering-index.yaml.
        module_number: Module number.
        step: Current checkpoint step number.

    Returns:
        Path to the sub-file or root file (fallback).
    """
    content = index_path.read_text(encoding="utf-8")

    # Get root file
    root_match = re.search(
        rf"^  {module_number}:\s*\n\s+root:\s*(\S+)",
        content,
        re.MULTILINE,
    )
    if not root_match:
        raise ValueError(f"Module {module_number} not found or not split in index")

    root_filename = root_match.group(1)
    root_path = steering_dir / root_filename

    # Try to find the phase sub-file
    sub_filename = step_to_phase(index_path, module_number, step)
    if sub_filename:
        sub_path = steering_dir / sub_filename
        if sub_path.exists():
            return sub_path
        # Fallback to root
        print(
            f"Warning: sub-file {sub_filename} not found, falling back to root",
            file=sys.stderr,
        )

    return root_path


# ---------------------------------------------------------------------------
# Module configuration
# ---------------------------------------------------------------------------

MODULE_CONFIG = {
    5: {
        "filename": "module-05-data-quality-mapping.md",
        "sub_files": [
            "module-05-phase1-quality-assessment.md",
            "module-05-phase2-data-mapping.md",
            "module-05-phase3-test-load.md",
        ],
    },
    6: {
        "filename": "module-06-load-data.md",
        "sub_files": [
            "module-06-phaseA-build-loading.md",
            "module-06-phaseB-load-first-source.md",
            "module-06-phaseC-multi-source.md",
            "module-06-phaseD-validation.md",
        ],
    },
}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for splitting module steering files."""
    parser = argparse.ArgumentParser(
        description="Split large module steering files into phase-level sub-files"
    )
    parser.add_argument(
        "--module",
        type=int,
        required=True,
        choices=list(MODULE_CONFIG.keys()),
        help="Module number to split (5 or 6)",
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
    args = parser.parse_args()

    config = MODULE_CONFIG[args.module]
    module_path = args.steering_dir / config["filename"]

    if not module_path.exists():
        print(f"Error: module file not found: {module_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Splitting {module_path.name} into phase-level sub-files...")

    result = split_module(module_path, args.steering_dir, config["sub_files"])

    if not result.phases:
        print("No phases found. Nothing to split.")
        sys.exit(0)

    # Update the steering index
    update_steering_index(args.index_path, args.module, result)

    # Print summary
    print(f"\nRoot file: {result.root_path.name} ({result.root_token_count} tokens)")
    print(f"Sub-files created:")
    for sub_path, tc in zip(result.sub_files, result.sub_file_token_counts):
        print(f"  {sub_path.name} ({tc} tokens)")
    print(f"\nTotal: {len(result.sub_files)} sub-files + 1 root file")
    print(f"steering-index.yaml updated.")


if __name__ == "__main__":
    main()
