#!/usr/bin/env python3
"""Generate a deterministic docs/README.md index for a graduating project.

Enumerates the *actual* top-level contents of a project's ``docs/`` directory
(depth 1 only): every regular file and every immediate subdirectory, each as a
single entry. Dot-prefixed entries and the ``docs/README.md`` index file itself
are excluded. Each entry gets a one-line purpose description from a predefined
purpose map, falling back to a non-empty generic description for unknown names.
Entries are ordered case-insensitively by name and rendered as a Markdown table
of contents, so identical ``docs/`` contents always produce byte-identical
output. The rendered index is validated as a parseable table of contents and
written atomically, so a malformed or partial ``docs/README.md`` is never left
behind.

Usage:
    python3 generate_docs_index.py                       # write/refresh index
    python3 generate_docs_index.py --docs-root <dir>     # custom docs root
    python3 generate_docs_index.py --check               # report drift only
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DOCS_ROOT = Path("docs")
INDEX_FILENAME = "README.md"
MAX_DESCRIPTION_LEN = 120
SUBDIR_INDICATOR = "/"  # trailing slash appended to subdirectory entry names


@dataclass(frozen=True)
class DocsEntry:
    """A single top-level entry in the docs index.

    Attributes:
        name: Bare entry name as it appears in ``docs/`` (e.g. ``mapping`` or
            ``bootcamp_recap.md``); never starts with ``.`` and never equals
            ``README.md``.
        is_dir: True for a subdirectory entry, False for a regular file.
        description: One-line purpose, 1..120 chars, never empty.
    """

    name: str
    is_dir: bool
    description: str


# Predefined one-line purposes for known bootcamp artifacts, keyed by bare entry
# name. Subdirectory entries are keyed by bare name (no trailing indicator); the
# visual indicator is applied during rendering, not stored in the key. Names not
# present here receive a generic non-empty description so every entry is
# described (Requirement 3.3).
PURPOSE_MAP: dict[str, str] = {
    # Files
    "bootcamp_recap.md": "Narrative recap of the completed bootcamp journey.",
    "bootcamp_journal.md": "Chronological journal of bootcamp work and decisions.",
    "completion_summary.md": "Summary of completion status and key outcomes.",
    "business_problem.md": "Statement of the business problem being solved.",
    "data_source_evaluation.md": "Evaluation notes for candidate data sources.",
    "stakeholder_summary_module1.md": "Stakeholder-facing summary from Module 1.",
    # Subdirectories
    "mapping": "Data source mapping artifacts.",
    "progress": "Progress tracking and dashboards.",
    "visualizations": "Generated charts and entity visualizations.",
    "reference": "Reference material and specifications.",
    "feedback": "Feedback templates and submissions.",
}

# Generic fallback descriptions when an entry name is not in PURPOSE_MAP.
GENERIC_FILE_DESCRIPTION = "Bootcamp documentation file."
GENERIC_DIR_DESCRIPTION = "Bootcamp documentation directory."

# Heading that opens a rendered table of contents.
TOC_HEADING = "# Documentation Index"

# Parses a rendered list item: ``- **<name>** — <description>``. The name is
# captured non-greedily up to the closing ``**`` so a description that itself
# contains the `` name`` delimiter does not confuse the split.
_LIST_ITEM_RE = re.compile(r"^- \*\*(?P<name>.+?)\*\* — (?P<description>.+)$")


def scan_entries(docs_root: Path) -> list[DocsEntry]:
    """Enumerate top-level (depth 1) entries under a docs root.

    Includes each regular file and each immediate subdirectory; excludes the
    index file itself, any dot-prefixed entry, and anything nested below depth 1.
    Returns entries sorted case-insensitively by name.

    Args:
        docs_root: Path to the docs directory to scan.

    Returns:
        A list of DocsEntry records sorted case-insensitively by name.
    """
    entries: list[DocsEntry] = []
    for child in docs_root.iterdir():
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
        entries.append(
            DocsEntry(name=name, is_dir=is_dir, description=describe_entry(name, is_dir))
        )
    entries.sort(key=lambda entry: (entry.name.lower(), entry.name))
    return entries


def describe_entry(name: str, is_dir: bool) -> str:
    """Return a 1..120 char one-line purpose for an entry.

    Looks up a predefined description by entry name; falls back to a non-empty
    generic description when the name is unknown. Never returns an empty string.

    Args:
        name: Bare entry name as it appears in ``docs/``.
        is_dir: True when the entry is a subdirectory, False for a file.

    Returns:
        A single-line description string of length 1..120.
    """
    description = PURPOSE_MAP.get(name)
    if description is None:
        description = GENERIC_DIR_DESCRIPTION if is_dir else GENERIC_FILE_DESCRIPTION

    # Collapse any newlines (and surrounding whitespace) to single spaces so the
    # result is always rendered on a single line.
    description = " ".join(description.split())

    # Guarantee the 1..MAX_DESCRIPTION_LEN bound. Truncate over-long text and
    # fall back to a generic description if collapsing left the string empty.
    if not description:
        description = GENERIC_DIR_DESCRIPTION if is_dir else GENERIC_FILE_DESCRIPTION
    if len(description) > MAX_DESCRIPTION_LEN:
        description = description[:MAX_DESCRIPTION_LEN]

    return description


def render_markdown(entries: list[DocsEntry]) -> str:
    """Render entries as a deterministic Markdown table of contents.

    Subdirectory entries carry the visual indicator (trailing ``/``); file
    entries do not. Output is terminated by a single trailing newline.

    Args:
        entries: The entries to render, already ordered.

    Returns:
        The rendered ``docs/README.md`` contents.
    """
    lines = ["# Documentation Index", ""]
    for entry in entries:
        indicator = SUBDIR_INDICATOR if entry.is_dir else ""
        lines.append(f"- **{entry.name}{indicator}** — {entry.description}")
    return "\n".join(lines) + "\n"


def validate_toc(markdown: str, entries: list[DocsEntry]) -> bool:
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


def generate_index(docs_root: Path) -> str:
    """Run the full pipeline: scan -> describe -> sort -> render.

    Args:
        docs_root: Path to the docs directory to index.

    Returns:
        The deterministic ``docs/README.md`` contents.
    """
    entries = scan_entries(docs_root)
    return render_markdown(entries)


def write_index_atomically(docs_root: Path, markdown: str) -> Path:
    """Validate then atomically write ``docs/README.md`` (temp file + os.replace).

    Args:
        docs_root: Path to the docs directory to write into.
        markdown: The rendered Markdown to validate and write.

    Returns:
        The path to the written index file.

    Raises:
        ValueError: When the rendered Markdown fails table-of-contents validation.
        OSError: When the atomic write fails; any existing ``README.md`` is left
            untouched and no partial or malformed file remains.
    """
    # Regenerate the entries from the current docs/ contents so the rendered
    # Markdown can be validated against what it is supposed to describe. This
    # runs *before* any existing file is touched (Requirement 1.4).
    entries = scan_entries(docs_root)
    if not validate_toc(markdown, entries):
        raise ValueError(
            "Rendered docs index failed table-of-contents validation; "
            "refusing to write a malformed README.md."
        )

    target = docs_root / INDEX_FILENAME

    # Write to a temp file in the same directory so os.replace is atomic on the
    # same filesystem. On any failure, remove the temp file and leave any
    # existing README.md untouched.
    fd, tmp_name = tempfile.mkstemp(dir=str(docs_root), prefix=".docs-index-", suffix=".tmp")
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


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and generate or check the docs index.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        Exit code: 0 on success (including a clean skip when ``docs/`` is
        absent), 1 on error or detected drift.
    """
    parser = argparse.ArgumentParser(
        description="Generate or check a deterministic docs/README.md index.",
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=DEFAULT_DOCS_ROOT,
        help="Directory to index (default: docs).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing; exit non-zero when the on-disk "
        "index differs from a fresh generation.",
    )
    args = parser.parse_args(argv)

    docs_root: Path = args.docs_root
    index_path = docs_root / INDEX_FILENAME

    # Missing or non-directory docs/ is a clean skip (Requirement 4.2): report a
    # one-line summary that the index was not generated and exit 0. No
    # confirmation prompt is needed when it does exist (Requirement 4.3).
    if not docs_root.is_dir():
        reason = "does not exist" if not docs_root.exists() else "not a directory"
        print(f"Docs index not generated: {docs_root} {reason}.")
        return 0

    # --check mode: compare a fresh generation against the on-disk index and
    # report drift without writing anything.
    if args.check:
        try:
            expected = generate_index(docs_root)
        except OSError as error:
            print(f"Failed to generate docs index: {error}", file=sys.stderr)
            return 1

        if not index_path.is_file():
            print(f"Docs index out of sync: {index_path} is missing.", file=sys.stderr)
            return 1

        try:
            actual = index_path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Failed to read docs index: {error}", file=sys.stderr)
            return 1

        if actual != expected:
            print(f"Docs index out of sync: {index_path} is stale.", file=sys.stderr)
            return 1

        print(f"Docs index in sync: {index_path}.")
        return 0

    # Default mode: generate and atomically write the index.
    try:
        markdown = generate_index(docs_root)
        target = write_index_atomically(docs_root, markdown)
    except (ValueError, OSError) as error:
        print(f"Failed to write docs index: {error}", file=sys.stderr)
        return 1

    # Success message identifying the location (Requirement 4.4) BEFORE the
    # one-line summary (Requirement 4.5).
    print(f"Wrote docs index: {target}")
    print(f"Docs index generated at {target}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
