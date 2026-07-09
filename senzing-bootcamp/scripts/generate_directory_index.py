#!/usr/bin/env python3
"""Generate a deterministic README.md index for a project directory (src/ or data/).

Enumerates the *actual* top-level contents of the target directory (depth 1
only): every regular file and every immediate subdirectory, each as a single
entry. Dot-prefixed entries and the ``README.md`` index file itself are
excluded. Each entry gets a one-line purpose synopsis from a predefined purpose
map, falling back to a non-empty generic synopsis for unknown names. Entries are
ordered case-insensitively by name and rendered as a Markdown table of contents,
so identical target-directory contents always produce byte-identical output. The
rendered index is validated as a parseable table of contents and written
atomically, so a malformed or partial ``README.md`` is never left behind.

A single script serves both ``src/`` and ``data/`` because the enumeration,
rendering, and validation logic is identical; only the purpose map differs,
selected from the final component of ``--target-root``.

Usage:
    python3 generate_directory_index.py --target-root src
    python3 generate_directory_index.py --target-root data
    python3 generate_directory_index.py --target-root src --check
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

INDEX_FILENAME = "README.md"
MAX_DESCRIPTION_LEN = 120
SUBDIR_INDICATOR = "/"  # trailing slash appended to subdirectory entry names


@dataclass(frozen=True)
class DirEntry:
    """A single top-level entry in the directory index.

    Attributes:
        name: Bare entry name (e.g. ``transform`` or ``loader.py``); never
            starts with ``.`` and never equals ``README.md``.
        is_dir: True for a subdirectory, False for a regular file.
        description: One-line synopsis, 1..120 chars, never empty.
    """

    name: str
    is_dir: bool
    description: str


# Predefined one-line purposes for known ``src/`` artifacts, keyed by bare entry
# name. Subdirectory entries are keyed by bare name (no trailing indicator); the
# visual indicator is applied during rendering, not stored in the key. Names not
# present here receive a generic non-empty description so every entry is
# described (Requirement 3.3).
SRC_PURPOSE_MAP: dict[str, str] = {
    "transform": "Data transformation modules.",
    "load": "Entity loading modules.",
    "query": "Entity query and search modules.",
    "utils": "Shared utility functions.",
    "config": "Configuration management.",
    "quickstart_demo": "Quickstart demonstration code.",
    "main.py": "Application entry point.",
    "setup.py": "Package setup configuration.",
}

# Predefined one-line purposes for known ``data/`` artifacts, keyed by bare
# entry name. Follows the same conventions as ``SRC_PURPOSE_MAP``.
DATA_PURPOSE_MAP: dict[str, str] = {
    "raw": "Original unprocessed source files.",
    "transformed": "Cleaned and mapped data ready for loading.",
    "samples": "Sample data for testing and demonstration.",
    "output": "Generated output and reports.",
    "mappings": "Data source mapping configurations.",
}

# Generic fallback descriptions when an entry name is not in the purpose map.
GENERIC_FILE_DESCRIPTION = "Project file."
GENERIC_DIR_DESCRIPTION = "Project directory."

# Heading that opens a rendered table of contents.
TOC_HEADING = "# Directory Index"

# Parses a rendered list item: ``- **<name>** — <description>``. The name is
# captured non-greedily up to the closing ``**`` so a description that itself
# contains the `` name`` delimiter does not confuse the split.
_LIST_ITEM_RE = re.compile(r"^- \*\*(?P<name>.+?)\*\* — (?P<description>.+)$")


def scan_entries(target_root: Path) -> list[DirEntry]:
    """Enumerate top-level (depth 1) entries under a target root.

    Includes each regular file and each immediate subdirectory; excludes the
    index file itself, any dot-prefixed entry, and anything nested below depth 1.
    Returns entries sorted case-insensitively by name.

    Args:
        target_root: Path to the directory to scan.

    Returns:
        A list of DirEntry records sorted case-insensitively by name. Each
        record's ``description`` is an empty placeholder; ``generate_index``
        fills it in via ``describe_entry`` using the target's purpose map.
    """
    entries: list[DirEntry] = []
    for child in target_root.iterdir():
        name = child.name
        if name.startswith("."):
            continue
        if name == INDEX_FILENAME:
            continue
        is_dir = child.is_dir()
        if not is_dir and not child.is_file():
            # Skip anything that is neither a regular file nor a directory
            # (e.g. broken symlinks, sockets, FIFOs).
            continue
        # The description is intentionally an empty placeholder here: scan_entries
        # has no purpose map, so generate_index applies describe_entry per entry
        # to fill the synopsis before rendering.
        entries.append(DirEntry(name=name, is_dir=is_dir, description=""))
    entries.sort(key=lambda entry: (entry.name.lower(), entry.name))
    return entries


def describe_entry(name: str, is_dir: bool, purpose_map: dict[str, str]) -> str:
    """Return a 1..120 char one-line purpose for an entry.

    Looks up a predefined description by entry name in ``purpose_map``; falls
    back to a non-empty generic description when the name is unknown. Never
    returns an empty string.

    Args:
        name: Bare entry name as it appears in the target directory.
        is_dir: True when the entry is a subdirectory, False for a file.
        purpose_map: The purpose map to look the name up in.

    Returns:
        A single-line description string of length 1..120.
    """
    generic = GENERIC_DIR_DESCRIPTION if is_dir else GENERIC_FILE_DESCRIPTION

    description = purpose_map.get(name)
    if description is None:
        description = generic

    # Collapse any newlines (and surrounding whitespace) to single spaces so the
    # result is always rendered on a single line.
    description = " ".join(description.split())

    # Guarantee the 1..MAX_DESCRIPTION_LEN bound: fall back to a generic
    # description if collapsing left the string empty, and defensively truncate
    # any over-long purpose-map value.
    if not description:
        description = generic
    if len(description) > MAX_DESCRIPTION_LEN:
        description = description[:MAX_DESCRIPTION_LEN]

    return description


def render_markdown(entries: list[DirEntry]) -> str:
    """Render entries as a deterministic Markdown table of contents.

    Subdirectory entries carry the visual indicator (trailing ``/``); file
    entries do not. Output is terminated by a single trailing newline.

    Args:
        entries: The entries to render, already ordered.

    Returns:
        The rendered ``README.md`` contents.
    """
    # A blank line after the heading keeps the output valid CommonMark: the
    # list must be separated from the heading by a blank line to parse as a list.
    lines = [TOC_HEADING, ""]
    for entry in entries:
        indicator = SUBDIR_INDICATOR if entry.is_dir else ""
        lines.append(f"- **{entry.name}{indicator}** — {entry.description}")
    return "\n".join(lines) + "\n"


def validate_toc(markdown: str, entries: list[DirEntry]) -> bool:
    """Return whether rendered Markdown parses as a valid table of contents.

    Confirms every entry appears exactly once as a list item with exactly one
    single-line description of 1..120 chars, and that no extra entries appear.

    Args:
        markdown: The rendered Markdown to validate.
        entries: The entries the Markdown is expected to contain.

    Returns:
        True when the Markdown is a valid table of contents for the entries.
    """
    if not isinstance(markdown, str):
        return False

    # Build the set of names the document is expected to list. Subdirectory
    # entries carry the trailing SUBDIR_INDICATOR exactly as render_markdown
    # emits them. A duplicate rendered name means an entry could not appear
    # "exactly once", so the rendering is invalid by construction.
    expected: set[str] = set()
    for entry in entries:
        rendered_name = entry.name + (SUBDIR_INDICATOR if entry.is_dir else "")
        if rendered_name in expected:
            return False
        expected.add(rendered_name)

    lines = markdown.split("\n")

    # A valid table of contents opens with the heading.
    if not lines or lines[0] != TOC_HEADING:
        return False

    seen: set[str] = set()
    for line in lines[1:]:
        if not line.startswith("- "):
            # Blank separator lines and other non-list content are ignored;
            # only list items contribute entries.
            continue
        match = _LIST_ITEM_RE.match(line)
        if match is None:
            # A list item that does not parse is a malformed entry.
            return False
        name = match.group("name")
        description = match.group("description")
        if name not in expected or name in seen:
            # An unexpected entry, or a duplicate of one already seen, is invalid.
            return False
        if not 1 <= len(description) <= MAX_DESCRIPTION_LEN:
            return False
        seen.add(name)

    # Every expected entry must have appeared exactly once and no more.
    return seen == expected


def generate_index(target_root: Path, purpose_map: dict[str, str]) -> str:
    """Run the full pipeline: scan -> describe -> sort -> render.

    Args:
        target_root: Path to the directory to index.
        purpose_map: The purpose map used to describe each entry.

    Returns:
        The deterministic ``README.md`` contents.
    """
    scanned = scan_entries(target_root)
    described = [
        replace(
            entry,
            description=describe_entry(entry.name, entry.is_dir, purpose_map),
        )
        for entry in scanned
    ]
    return render_markdown(described)


def write_index_atomically(
    target_root: Path, markdown: str, purpose_map: dict[str, str]
) -> Path:
    """Validate then atomically write ``README.md`` (temp file + os.replace).

    Args:
        target_root: Path to the directory to write into.
        markdown: The rendered Markdown to validate and write.
        purpose_map: The purpose map used to regenerate entries for validation.

    Returns:
        The path to the written index file.

    Raises:
        ValueError: When the rendered Markdown fails table-of-contents validation.
        OSError: When the atomic write fails; any existing ``README.md`` is left
            untouched and no partial or malformed file remains.
    """
    # Reconstruct the described entries from the current target contents the
    # same way generate_index does, so the rendered Markdown can be validated
    # against what it is supposed to describe. This runs *before* any existing
    # file is touched (Requirements 1.6, 10.4).
    scanned = scan_entries(target_root)
    entries = [
        replace(
            entry,
            description=describe_entry(entry.name, entry.is_dir, purpose_map),
        )
        for entry in scanned
    ]
    if not validate_toc(markdown, entries):
        raise ValueError(
            "Rendered directory index failed table-of-contents validation; "
            "refusing to write a malformed README.md."
        )

    target = target_root / INDEX_FILENAME

    # Write to a temp file in the same directory so os.replace is atomic on the
    # same filesystem. On any failure, remove the temp file and leave any
    # existing README.md untouched.
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target_root), prefix=".dir-index-", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(markdown)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except OSError:
        # Clean up the temp file; the original README.md (if any) is untouched
        # because os.replace either fully succeeds or never ran.
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise

    return target


def select_purpose_map(target_root: Path) -> dict[str, str]:
    """Select the purpose map for a target root by its final path component.

    ``src`` -> ``SRC_PURPOSE_MAP``, ``data`` -> ``DATA_PURPOSE_MAP``; unknown
    directories fall back to an empty map (generic descriptions still apply).

    Args:
        target_root: Path whose final component selects the purpose map.

    Returns:
        The purpose map for the directory, or an empty dict when unknown.
    """
    maps: dict[str, dict[str, str]] = {
        "src": SRC_PURPOSE_MAP,
        "data": DATA_PURPOSE_MAP,
    }
    return maps.get(target_root.name.lower(), {})


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and generate or check the directory index.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        Exit code: 0 on success (including a clean skip when the target
        directory is absent), 1 on error or detected drift.
    """
    parser = argparse.ArgumentParser(
        description="Generate or check a deterministic directory README.md index.",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        required=True,
        help="Directory to index (e.g. src or data).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing; exit non-zero when the on-disk "
        "index differs from a fresh generation.",
    )
    args = parser.parse_args(argv)

    target_root: Path = args.target_root
    purpose_map = select_purpose_map(target_root)
    index_path = target_root / INDEX_FILENAME

    # Missing or non-directory target is a clean skip (Requirement 4.2): report a
    # one-line summary that the index was not generated and exit 0. No
    # confirmation prompt is needed when it does exist (Requirement 4.3).
    if not target_root.is_dir():
        reason = "does not exist" if not target_root.exists() else "is not a directory"
        print(f"Directory index not generated — {target_root} {reason}.")
        return 0

    # --check mode: compare a fresh generation against the on-disk index and
    # report drift without writing anything (Requirement 10.3).
    if args.check:
        try:
            expected = generate_index(target_root, purpose_map)
        except OSError as error:
            print(f"Failed to generate directory index: {error}", file=sys.stderr)
            return 1

        if not index_path.is_file():
            print(
                f"Directory index out of sync: {index_path} is missing.",
                file=sys.stderr,
            )
            return 1

        try:
            actual = index_path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Failed to read directory index: {error}", file=sys.stderr)
            return 1

        if actual != expected:
            print(
                f"Directory index out of sync: {index_path} is stale.",
                file=sys.stderr,
            )
            return 1

        print(f"Directory index in sync: {index_path}.")
        return 0

    # Default mode: generate and atomically write the index.
    try:
        markdown = generate_index(target_root, purpose_map)
        target = write_index_atomically(target_root, markdown, purpose_map)
    except (ValueError, OSError) as error:
        print(f"Failed to write directory index: {error}", file=sys.stderr)
        return 1

    # Success message identifying the location (Requirement 4.4) BEFORE the
    # one-line summary (Requirement 4.5).
    entry_count = sum(1 for line in markdown.splitlines() if line.startswith("- "))
    plural = "entry" if entry_count == 1 else "entries"
    print(f"Wrote directory index: {target}")
    print(f"Directory index generated at {target} ({entry_count} {plural}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
