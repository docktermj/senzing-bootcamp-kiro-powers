#!/usr/bin/env python3
"""Measure token counts for steering files and update steering-index.yaml.

Scans all .md files in the steering directory, calculates approximate token
counts (characters / 4), and writes file_metadata + budget sections into
steering-index.yaml while preserving all existing content.

Usage:
    python senzing-bootcamp/scripts/measure_steering.py          # update mode
    python senzing-bootcamp/scripts/measure_steering.py --check  # validation mode
"""

import argparse
import re
import sys
from pathlib import Path


DEFAULT_STEERING_DIR = Path("senzing-bootcamp/steering")
DEFAULT_INDEX_PATH = Path("senzing-bootcamp/steering/steering-index.yaml")


def calculate_token_count(filepath):
    """Read a file and return approximate token count: round(len(content) / 4)."""
    content = Path(filepath).read_text(encoding="utf-8")
    return round(len(content) / 4)


def classify_size(token_count):
    """Return size category based on token count thresholds."""
    if token_count < 500:
        return "small"
    elif token_count <= 2000:
        return "medium"
    else:
        return "large"


def scan_steering_files(steering_dir):
    """Scan all .md files in steering_dir, return metadata dict.

    Returns:
        dict: {filename: {"token_count": int, "size_category": str}}
    """
    steering_path = Path(steering_dir)
    if not steering_path.is_dir():
        print(f"Error: steering directory not found: {steering_path}", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(steering_path.glob("*.md"))
    if not md_files:
        print(f"Warning: no .md files found in {steering_path}", file=sys.stderr)

    file_metadata = {}
    for md_file in md_files:
        try:
            count = calculate_token_count(md_file)
            file_metadata[md_file.name] = {
                "token_count": count,
                "size_category": classify_size(count),
            }
        except PermissionError:
            print(f"Warning: cannot read {md_file.name}, skipping", file=sys.stderr)
    return file_metadata


def print_summary(file_metadata, total_tokens):
    """Print a formatted summary table of file metadata to stdout."""
    if not file_metadata:
        print("No steering files found.")
        return

    # Calculate column widths
    name_width = max(len(name) for name in file_metadata)
    name_width = max(name_width, len("File"))
    count_width = max(len(str(m["token_count"])) for m in file_metadata.values())
    count_width = max(count_width, len("Tokens"))
    cat_width = max(len(m["size_category"]) for m in file_metadata.values())
    cat_width = max(cat_width, len("Size"))

    header = f"{'File':<{name_width}}  {'Tokens':>{count_width}}  {'Size':<{cat_width}}"
    separator = "-" * len(header)

    print(separator)
    print(header)
    print(separator)
    for name in sorted(file_metadata):
        meta = file_metadata[name]
        print(
            f"{name:<{name_width}}  {meta['token_count']:>{count_width}}  "
            f"{meta['size_category']:<{cat_width}}"
        )
    print(separator)
    print(f"Total tokens: {total_tokens}")
    print(separator)


def load_yaml_content(index_path):
    """Read the raw YAML text of steering-index.yaml."""
    return Path(index_path).read_text(encoding="utf-8")


def _find_section_start(content, section_name):
    """Find the start position of a top-level YAML section (not indented)."""
    pattern = re.compile(rf"^{re.escape(section_name)}:\s*$", re.MULTILINE)
    match = pattern.search(content)
    return match.start() if match else -1


def update_index(index_path, file_metadata, total_tokens):
    """Write file_metadata and budget sections into the YAML file.

    Preserves all existing content above the file_metadata section.
    Uses string manipulation (no PyYAML) to keep existing YAML byte-identical.
    """
    index_path = Path(index_path)

    if index_path.exists():
        content = load_yaml_content(index_path)
        # Find where file_metadata starts (if it already exists) and truncate there
        fm_pos = _find_section_start(content, "file_metadata")
        if fm_pos >= 0:
            # Preserve everything before file_metadata
            preserved = content[:fm_pos].rstrip("\n") + "\n"
        else:
            # Append after existing content
            preserved = content.rstrip("\n") + "\n"
    else:
        preserved = ""

    # Build file_metadata section
    lines = ["\nfile_metadata:"]
    for name in sorted(file_metadata):
        meta = file_metadata[name]
        lines.append(f"  {name}:")
        lines.append(f"    token_count: {meta['token_count']}")
        lines.append(f"    size_category: {meta['size_category']}")

    # Build budget section
    lines.append("")
    lines.append("budget:")
    lines.append(f"  total_tokens: {total_tokens}")
    lines.append("  reference_window: 200000")
    lines.append("  warn_threshold_pct: 60")
    lines.append("  critical_threshold_pct: 80")
    lines.append("")

    new_content = preserved + "\n".join(lines)
    index_path.write_text(new_content, encoding="utf-8")


def _parse_stored_metadata(content):
    """Parse file_metadata from YAML content using simple string/regex parsing.

    Returns dict of {filename: {"token_count": int, "size_category": str}}
    or None if file_metadata section not found.
    """
    fm_pos = _find_section_start(content, "file_metadata")
    if fm_pos < 0:
        return None

    # Extract the file_metadata block: from "file_metadata:" to the next
    # top-level key or end of file
    after_fm = content[fm_pos:]
    # Find the next top-level key (non-indented, not a comment)
    next_section = re.search(r"^\S", after_fm[len("file_metadata:"):], re.MULTILINE)
    if next_section:
        block = after_fm[: len("file_metadata:") + next_section.start()]
    else:
        block = after_fm

    metadata = {}
    current_file = None
    for line in block.splitlines():
        # Match a filename entry like "  agent-instructions.md:"
        file_match = re.match(r"^  ([\w.-]+\.md):$", line)
        if file_match:
            current_file = file_match.group(1)
            metadata[current_file] = {}
            continue
        if current_file:
            tc_match = re.match(r"^\s+token_count:\s*(\d+)", line)
            if tc_match:
                metadata[current_file]["token_count"] = int(tc_match.group(1))
            sc_match = re.match(r"^\s+size_category:\s*(\w+)", line)
            if sc_match:
                metadata[current_file]["size_category"] = sc_match.group(1)

    return metadata


def check_counts(index_path, calculated):
    """Compare stored vs calculated token counts, return mismatches >10%.

    Args:
        index_path: Path to steering-index.yaml
        calculated: dict from scan_steering_files()

    Returns:
        list of (filename, stored_count, calculated_count) tuples for mismatches
    """
    content = load_yaml_content(index_path)
    stored = _parse_stored_metadata(content)

    mismatches = []

    if stored is None:
        print("Error: no file_metadata section found in index", file=sys.stderr)
        sys.exit(1)

    for filename, calc_meta in calculated.items():
        calc_count = calc_meta["token_count"]
        if filename not in stored:
            mismatches.append((filename, None, calc_count))
            continue
        stored_count = stored[filename].get("token_count")
        if stored_count is None:
            mismatches.append((filename, None, calc_count))
            continue
        denominator = max(calc_count, 1)
        if abs(stored_count - calc_count) / denominator > 0.10:
            mismatches.append((filename, stored_count, calc_count))

    # Check for entries in stored that no longer exist
    for filename in stored:
        if filename not in calculated:
            mismatches.append((filename, stored[filename].get("token_count"), None))

    return mismatches


def main():
    """Parse args and dispatch to update or check mode."""
    parser = argparse.ArgumentParser(
        description="Measure token counts for steering files"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate stored counts against calculated (exit non-zero on mismatch)",
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

    file_metadata = scan_steering_files(args.steering_dir)
    total_tokens = sum(m["token_count"] for m in file_metadata.values())

    if args.check:
        mismatches = check_counts(args.index_path, file_metadata)
        if mismatches:
            print("Token count mismatches (>10% difference):")
            for filename, stored, calculated in mismatches:
                stored_str = str(stored) if stored is not None else "MISSING"
                calc_str = str(calculated) if calculated is not None else "REMOVED"
                print(f"  {filename}: stored={stored_str}, calculated={calc_str}")
            sys.exit(1)
        else:
            print("All token counts are within 10% tolerance.")
            sys.exit(0)
    else:
        update_index(args.index_path, file_metadata, total_tokens)
        print_summary(file_metadata, total_tokens)


if __name__ == "__main__":
    main()
