#!/usr/bin/env python3
"""Normalize bootcamp Markdown artifacts at graduation time.

Performs a single graduation-time normalization pass over the bootcamp's
Markdown artifacts: schema normalization for files with a known
Consumer_Schema (today: the recap) plus deterministic CommonMark style
fixes for every targeted file. Writes are atomic so a mid-write failure
can never corrupt or truncate the original file.

The pass is non-blocking by contract: individual file warnings or errors
never abort the run. ``main`` returns 0 on success (including per-file
warnings/errors) and 1 only for argument/usage errors.

Usage:
    python senzing-bootcamp/scripts/normalize_markdown.py
    python senzing-bootcamp/scripts/normalize_markdown.py docs/bootcamp_recap.md
    python senzing-bootcamp/scripts/normalize_markdown.py --dir docs
    python senzing-bootcamp/scripts/normalize_markdown.py --check
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

# Scripts are not a package; ensure this script's directory is importable so the
# recap schema round-trip can reuse the sibling ``generate_recap_pdf`` module
# (matching the project's documented sibling-import pattern).
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import generate_recap_pdf  # noqa: E402  (path manipulated above)

# ---------------------------------------------------------------------------
# Default target discovery
# ---------------------------------------------------------------------------

#: Markdown_Artifacts that are always normalized when they exist, in the order
#: they should be processed. The recap is the only file with a registered
#: Consumer_Schema today; everything else is style-normalized only.
KNOWN_ARTIFACTS: tuple[str, ...] = (
    "docs/bootcamp_recap.md",
    "docs/bootcamp_journal.md",
)

#: Directory holding per-source mapper docs (``*_mapper.md``).
MAPPER_DIR: str = "docs/mapping"

# ---------------------------------------------------------------------------
# CommonMark style-fix rule patterns
# ---------------------------------------------------------------------------
# These mirror the rule set enforced by the ``commonmark-validation`` hook and
# documented by ``validate_commonmark.py`` (MD022, MD031, MD032, MD040, plus
# bold-label colon spacing). They are implemented here as deterministic,
# stdlib-only text transforms — ``validate_commonmark.py`` only *validates*
# (it shells out to markdownlint-cli); it does not expose a reusable fixer.

#: ATX heading line, e.g. ``## Module 1`` (MD022). Allows up to 3 leading spaces
#: per CommonMark, and matches a bare ``#`` with no trailing text.
_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(\s|$)")

#: Fenced code-block delimiter (MD031/MD040): ``` ``` ``` or ``` ~~~ ``` with an
#: optional indent and an optional info string (the language).
_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

#: List-item line (MD032): unordered (``-``/``*``/``+``) or ordered (``1.``/``1)``).
_LIST_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+\S")

#: Bold label whose colon sits *outside* the emphasis (``**Label**:``). The fix
#: moves the colon inside the markers to produce ``**Label:**``.
_BOLD_LABEL_RE = re.compile(r"\*\*([^*\n]+?)\*\*:")

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class NormalizationResult:
    """Outcome of normalizing a single Markdown_Artifact.

    Attributes:
        path: Path to the file that was processed.
        changed: True when the normalized output differs from the input.
        schema_applied: True when a Consumer_Schema was matched and applied.
        warnings: Unmapped-content or skipped-reason messages for this file.
        error: Set to a message when this file failed; the flow continues.
    """

    path: str
    changed: bool = False
    schema_applied: bool = False
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def discover_default_targets(root: str | Path = ".") -> list[str]:
    """Discover the default set of Markdown_Artifacts to normalize.

    The default target set is the known artifacts that actually exist: the
    recap and journal, every top-level ``docs/*.md`` document, and any mapper
    docs (``*_mapper.md``) under ``docs/``. Files that do not exist are
    omitted, so callers only ever receive real paths.

    Args:
        root: Project root to resolve ``docs/`` paths against. Defaults to the
            current working directory.

    Returns:
        Sorted list of existing target paths (as strings, relative to ``root``
        when ``root`` is relative), with no duplicates.
    """
    root_path = Path(root)
    docs_dir = root_path / "docs"

    candidates: list[Path] = []

    # Explicitly known artifacts first (recap, journal).
    for rel in KNOWN_ARTIFACTS:
        candidates.append(root_path / rel)

    if docs_dir.is_dir():
        # Other top-level docs/*.md artifacts.
        candidates.extend(sorted(docs_dir.glob("*.md")))
        # Mapper docs live under docs/mapping/ (and may be nested elsewhere).
        candidates.extend(sorted(docs_dir.glob("**/*_mapper.md")))

    # Keep only existing files, de-duplicate while preserving discovery order.
    seen: set[str] = set()
    targets: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        targets.append(key)

    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list to parse. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with ``paths`` (positional files), ``dir``, and
        ``check`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Normalize bootcamp Markdown artifacts at graduation time "
            "(schema normalization + deterministic CommonMark style fixes)."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="FILE",
        help=(
            "Markdown files to normalize. Defaults to the known artifacts "
            "that exist (docs/bootcamp_recap.md, docs/bootcamp_journal.md, "
            "mapper docs, and other docs/*.md)."
        ),
    )
    parser.add_argument(
        "--dir",
        metavar="DIR",
        help="Normalize all *.md files found recursively under DIR.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Report only; do not write. Exit 1 if any file would change "
            "(for CI use)."
        ),
    )
    return parser.parse_args(argv)


def resolve_targets(args: argparse.Namespace, root: str | Path = ".") -> list[str]:
    """Resolve the list of files to normalize from parsed CLI arguments.

    Precedence: explicit positional ``paths`` win; otherwise ``--dir`` expands
    to all ``*.md`` under that directory; otherwise the default target set is
    discovered. Positional paths are returned as given (existence is checked
    per-file during normalization); ``--dir`` and default discovery return only
    files that exist.

    Args:
        args: Parsed arguments from :func:`parse_args`.
        root: Project root used for default target discovery.

    Returns:
        List of target file paths (strings).
    """
    if args.paths:
        return list(args.paths)

    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_dir():
            return []
        return [str(p) for p in sorted(dir_path.glob("**/*.md")) if p.is_file()]

    return discover_default_targets(root)


def _needs_blank_between(prev_type: str, cur_type: str) -> bool:
    """Decide whether a blank line must separate two adjacent non-blank lines.

    Encodes the MD022/MD031/MD032 "surrounded by blank lines" rules in terms of
    line types. Code lines inside a fence are never separated (they are emitted
    verbatim).

    Args:
        prev_type: Classified type of the previously emitted line.
        cur_type: Classified type of the line about to be emitted.

    Returns:
        True when a single blank line should be inserted between them.
    """
    # MD022: headings are surrounded by blank lines (before and after).
    if prev_type == "heading" or cur_type == "heading":
        return True
    # MD031: fenced code blocks are surrounded by blank lines.
    if cur_type == "fence_open":
        return True
    if prev_type == "fence_close":
        return True
    # MD032: lists are surrounded by blank lines (at their start and end only;
    # adjacent list lines and list continuations stay together).
    if cur_type == "list" and prev_type != "list":
        return True
    if prev_type == "list" and cur_type != "list":
        return True
    return False


def _classify_lines(lines: list[str]) -> list[tuple[str, str]]:
    """Classify and lightly rewrite each Markdown line for style fixing.

    Applies the per-line transforms (MD040 default language, bold-label colon
    spacing) and tags each line with a type used by the blank-line pass. Lines
    inside a fenced code block are tagged ``code`` and never rewritten.

    Args:
        lines: Raw Markdown lines (already split on newlines).

    Returns:
        List of ``(type, text)`` tuples where ``type`` is one of ``heading``,
        ``fence_open``, ``fence_close``, ``code``, ``list``, ``blank`` or
        ``text``.
    """
    classified: list[tuple[str, str]] = []
    in_code = False
    for raw in lines:
        fence_match = _FENCE_RE.match(raw)
        if fence_match and not in_code:
            indent, fence, info = fence_match.group(1, 2, 3)
            # MD040: a fenced code block missing a language gets a default.
            if info.strip() == "":
                raw = f"{indent}{fence}text"
            classified.append(("fence_open", raw))
            in_code = True
        elif fence_match and in_code:
            # Closing delimiter: emit verbatim, never add a language.
            classified.append(("fence_close", raw))
            in_code = False
        elif in_code:
            classified.append(("code", raw))
        else:
            # Non-code line: bold-label colon spacing is safe to apply here.
            fixed = _BOLD_LABEL_RE.sub(r"**\1:**", raw)
            if fixed.strip() == "":
                line_type = "blank"
            elif _HEADING_RE.match(fixed):
                line_type = "heading"
            elif _LIST_ITEM_RE.match(fixed):
                line_type = "list"
            elif (
                classified
                and classified[-1][0] == "list"
                and fixed[:1] in (" ", "\t")
            ):
                # Indented continuation of the preceding list item: keep it
                # attached so MD032 does not split a multi-line list item.
                line_type = "list"
            else:
                line_type = "text"
            classified.append((line_type, fixed))
    return classified


def apply_commonmark_fixes(content: str) -> str:
    """Apply deterministic CommonMark style fixes to Markdown text.

    Mirrors the rule set enforced by the ``commonmark-validation`` hook and
    ``validate_commonmark.py`` using stdlib-only text transforms:

    * MD022 — headings are surrounded by blank lines.
    * MD031 — fenced code blocks are surrounded by blank lines.
    * MD032 — lists are surrounded by blank lines.
    * MD040 — fenced code blocks without a language get a default of ``text``.
    * Bold-label colon spacing — ``**Label**:`` becomes ``**Label:**``.

    The CHANGELOG.md MD024 exception (duplicate headings allowed) is honored
    implicitly: this function never deduplicates or removes headings, so
    repeated ``### Added``/``### Changed`` sections are preserved unchanged.

    The transform is idempotent: ``apply_commonmark_fixes`` applied twice yields
    the same result as applying it once. Content inside fenced code blocks is
    emitted verbatim and never rewritten.

    Args:
        content: Raw Markdown text.

    Returns:
        Markdown text with the style fixes applied. The original trailing-newline
        shape is preserved.
    """
    classified = _classify_lines(content.split("\n"))

    out: list[tuple[str, str]] = []
    for line_type, text in classified:
        if out:
            prev_type = out[-1][0]
            if (
                prev_type != "blank"
                and line_type != "blank"
                and _needs_blank_between(prev_type, line_type)
            ):
                out.append(("blank", ""))
        out.append((line_type, text))

    return "\n".join(text for _, text in out)


# ---------------------------------------------------------------------------
# Recap schema normalization
# ---------------------------------------------------------------------------
#
# Consumer_Schema: docs/bootcamp_recap.md (consumed by generate_recap_pdf.py)
# ---------------------------------------------------------------------------
# The recap PDF generator parses the recap with a strict shape. ``normalize_recap``
# rewrites a free-form recap into exactly this shape by round-tripping it through
# ``generate_recap_pdf.parse_recap_markdown`` (input → structured RecapDocument)
# and ``generate_recap_pdf.format_recap_document`` (RecapDocument → canonical
# Markdown). The recognized schema is:
#
#   # Senzing Bootcamp Recap              (document title)
#
#   **Bootcamper:** <name>                (header fields, bold-label form)
#   **Started:** <date>
#   **Total Duration:** <duration>
#
#   ---                                   (horizontal-rule separators)
#
#   ## Module <N>: <name> — <timestamp>   (module heading; em-dash separated)
#
#   ### Information Shared                 (recognized subsections, in this order)
#   - <item>                               (Information Shared / Actions Taken: bullets)
#   ### Questions Asked
#   1. <item>                              (Questions Asked / Answers Given: numbered)
#   ### Answers Given
#   1. <item>
#   ### Actions Taken
#   - <item>
#   ### Duration
#   <plain text>                           (Duration: a single plain-text line)
#
# Anything the parser cannot place — prose paragraphs, fenced code blocks, extra
# or misspelled headings, module headings missing the em-dash timestamp — is NOT
# represented in the round-tripped output. Per Requirements 3.2/3.4 that content
# is retained verbatim (appended under an "Unmapped Content" section) and reported
# as a warning, never silently dropped.

#: ``### `` subsection names the recap parser recognizes (compared lowercased).
RECOGNIZED_RECAP_SUBSECTIONS: frozenset[str] = frozenset(
    {
        "information shared",
        "questions asked",
        "answers given",
        "actions taken",
        "duration",
    }
)

#: The canonical recap document title emitted by ``format_recap_document``.
_RECAP_TITLE: str = "# Senzing Bootcamp Recap"

#: Header field lines (bold-label form) the recap parser recognizes. Mirrors the
#: header regexes in ``generate_recap_pdf`` so detection stays in sync with what
#: the parser actually captures.
_RECAP_HEADER_LINE_RE = re.compile(
    r"^\*\*(?:Bootcamper|Started|Total Duration):\*\*\s*.*$"
)

#: Module heading the recap parser recognizes. Mirrors
#: ``generate_recap_pdf._MODULE_HEADING_RE`` (``## Module N: name — timestamp``).
_RECAP_MODULE_HEADING_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s+\u2014\s+(.+)$")

#: A ``### `` subsection heading (any name).
_RECAP_SUBSECTION_RE = re.compile(r"^###\s+(.+)$")

#: A bulleted or numbered list item (marker + text), matching what the recap
#: parser's ``_extract_list_items`` accepts.
_RECAP_LIST_ITEM_RE = re.compile(r"^(?:-|\d+\.)\s+(.+)$")

#: A horizontal rule (separator) the formatter emits between sections.
_RECAP_HRULE_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")


def _captured_recap_content(doc: "generate_recap_pdf.RecapDocument") -> set[str]:
    """Collect every substantive string the recap parser placed into ``doc``.

    Used to decide which input lines round-tripped successfully (and are
    therefore already represented in the canonical output) versus which carry
    content the parser could not place.

    Args:
        doc: The parsed recap document.

    Returns:
        Set of non-empty captured strings (header values, module names and
        timestamps, list items, and durations).
    """
    captured: set[str] = {
        doc.header.bootcamper,
        doc.header.started,
        doc.header.total_duration,
    }
    for section in doc.sections:
        captured.add(section.module_name)
        captured.add(section.timestamp)
        captured.add(section.duration)
        for items in (
            section.information_shared,
            section.questions_asked,
            section.answers_given,
            section.actions_taken,
        ):
            captured.update(items)
    captured.discard("")
    return captured


def _is_placed_recap_line(line: str, captured: set[str], durations: set[str]) -> bool:
    """Report whether a recap input line is represented in the canonical output.

    A line is "placed" when it corresponds to a schema element the parser
    captured (title, header field, separator, module heading, recognized
    subsection heading, captured list item, or a captured duration value). Any
    other non-blank line carries content the parser could not place.

    Args:
        line: A single input line (without trailing newline).
        captured: Substantive strings captured by the parser (see
            :func:`_captured_recap_content`).
        durations: The subset of ``captured`` that are section duration values.

    Returns:
        True when the line is already represented by the canonical output.
    """
    stripped = line.strip()
    if stripped == _RECAP_TITLE:
        return True
    if _RECAP_HRULE_RE.match(stripped):
        return True
    if _RECAP_HEADER_LINE_RE.match(stripped):
        return True
    if _RECAP_MODULE_HEADING_RE.match(stripped):
        return True
    subsection = _RECAP_SUBSECTION_RE.match(stripped)
    if subsection and subsection.group(1).strip().lower() in RECOGNIZED_RECAP_SUBSECTIONS:
        return True
    list_item = _RECAP_LIST_ITEM_RE.match(stripped)
    if list_item and list_item.group(1) in captured:
        return True
    if stripped in durations:
        return True
    return False


def _collect_unmapped_recap_lines(
    content: str, doc: "generate_recap_pdf.RecapDocument"
) -> list[str]:
    """Collect input lines the recap parser could not place, verbatim.

    Walks the original Markdown and returns, in order, every line that is not
    represented in the canonical round-tripped output. Fenced code blocks have
    no place in the recap schema, so they are retained in full (delimiters and
    body, including interior blank lines). Blank lines outside code blocks are
    skipped — they carry no content.

    Args:
        content: The original recap Markdown.
        doc: The recap document parsed from ``content``.

    Returns:
        Verbatim unmapped lines in document order (may be empty).
    """
    captured = _captured_recap_content(doc)
    durations = {section.duration for section in doc.sections if section.duration}

    retained: list[str] = []
    in_code = False
    for raw in content.split("\n"):
        if _FENCE_RE.match(raw):
            # Fenced code is never part of the recap schema: retain verbatim and
            # toggle the in-code flag.
            retained.append(raw)
            in_code = not in_code
            continue
        if in_code:
            retained.append(raw)
            continue
        if not raw.strip():
            continue
        if _is_placed_recap_line(raw, captured, durations):
            continue
        retained.append(raw)

    return retained


def normalize_recap(content: str) -> tuple[str, list[str]]:
    """Normalize a recap Markdown document to the recap PDF Consumer_Schema.

    Round-trips the recap through ``generate_recap_pdf.parse_recap_markdown``
    followed by ``generate_recap_pdf.format_recap_document`` so the output
    matches exactly what the recap PDF parser expects (see the Consumer_Schema
    documented above). Any content the parser cannot place — prose paragraphs,
    fenced code blocks, extra/misspelled headings, or module headings missing
    the ``— timestamp`` suffix — is retained verbatim under a trailing
    ``## Unmapped Content`` section and reported as a warning rather than being
    dropped (Requirements 3.2, 3.4).

    Args:
        content: Raw recap Markdown (free-form or already conforming).

    Returns:
        A ``(normalized_markdown, warnings)`` tuple. ``warnings`` is empty when
        all content mapped cleanly into the schema.
    """
    doc = generate_recap_pdf.parse_recap_markdown(content)
    normalized = generate_recap_pdf.format_recap_document(doc)

    warnings: list[str] = []
    retained = _collect_unmapped_recap_lines(content, doc)
    if retained:
        block = [
            normalized.rstrip("\n"),
            "",
            "## Unmapped Content",
            "",
            (
                "<!-- The following content could not be mapped to the recap "
                "schema and is retained verbatim so it is never lost. -->"
            ),
            "",
            *retained,
        ]
        normalized = "\n".join(block) + "\n"
        warnings.append(
            f"{len(retained)} line(s) could not be mapped to the recap schema; "
            "retained verbatim under '## Unmapped Content'."
        )

    return normalized, warnings


# ---------------------------------------------------------------------------
# Consumer-schema registry
# ---------------------------------------------------------------------------

#: Maps a target path (relative, POSIX form) to the function that rewrites it to
#: its Consumer_Schema. Files not listed here are style-normalized only. Adding a
#: new schema is one entry. The recap is the only schema for v1.
SCHEMA_NORMALIZERS: dict[str, Callable[[str], tuple[str, list[str]]]] = {
    "docs/bootcamp_recap.md": normalize_recap,
}


# ---------------------------------------------------------------------------
# Per-file normalization with atomic write
# ---------------------------------------------------------------------------


def _schema_normalizer_for(path: str) -> Callable[[str], tuple[str, list[str]]] | None:
    """Look up the schema normalizer registered for a target path.

    The :data:`SCHEMA_NORMALIZERS` registry is keyed by relative POSIX path
    (e.g. ``docs/bootcamp_recap.md``). A target is matched when its POSIX form
    equals a key or ends with ``/<key>`` — so an absolute path such as
    ``/repo/senzing-bootcamp/docs/bootcamp_recap.md`` and a relative
    ``docs/bootcamp_recap.md`` both resolve to the same normalizer.

    Args:
        path: The target file path (absolute or relative).

    Returns:
        The registered normalizer callable, or ``None`` for style-only files.
    """
    posix = Path(path).as_posix()
    for key, normalizer in SCHEMA_NORMALIZERS.items():
        if posix == key or posix.endswith(f"/{key}"):
            return normalizer
    return None


def _atomic_write(path: str, content: str) -> None:
    """Write ``content`` to ``path`` atomically.

    Writes to a sibling temporary file in the same directory, then
    :func:`os.replace` over the original. ``os.replace`` is atomic on the same
    filesystem, so a crash mid-write leaves the original untouched rather than
    corrupted or truncated (Requirement 3.5). The temp file is removed if the
    write or replace fails.

    Args:
        path: Destination file path.
        content: Full normalized text to write.
    """
    target = Path(path)
    directory = target.parent if str(target.parent) else Path(".")
    fd, tmp_name = tempfile.mkstemp(
        dir=str(directory), prefix=f"{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(tmp_name, str(target))
    except BaseException:
        # Leave the original intact and clean up the partial temp file.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def normalize_file(path: str, *, check: bool = False) -> NormalizationResult:
    """Normalize a single Markdown_Artifact, writing atomically.

    Pipeline: read the file, apply the registered Consumer_Schema normalizer
    (if any), apply the deterministic CommonMark style fixes, and — only when
    the output differs from the input — write the result atomically.

    The pass is non-blocking by contract: a non-existent target is skipped
    silently (an empty, error-free result) and *every* exception is caught and
    recorded on the returned result rather than raised, so one bad file never
    aborts the graduation flow (Requirements 2.4, 2.5, 3.1, 3.5).

    Args:
        path: The Markdown file to normalize.
        check: When True, report-only mode — compute ``changed`` but never
            write (used by ``--check``/CI). Defaults to False.

    Returns:
        A :class:`NormalizationResult` describing the outcome. ``error`` is set
        when the file failed; ``changed`` reflects whether the output differs
        from the input even in ``check`` mode.
    """
    result = NormalizationResult(path=path)
    try:
        target = Path(path)
        if not target.is_file():
            # Skip non-existent targets silently; this is not an error.
            return result

        original = target.read_text(encoding="utf-8")
        output = original

        normalizer = _schema_normalizer_for(path)
        if normalizer is not None:
            output, warnings = normalizer(output)
            result.schema_applied = True
            result.warnings.extend(warnings)

        output = apply_commonmark_fixes(output)
        result.changed = output != original

        if result.changed and not check:
            _atomic_write(path, output)
    except Exception as exc:  # noqa: BLE001 - non-blocking by contract
        result.error = f"{type(exc).__name__}: {exc}"

    return result


def normalize_paths(
    paths: Iterable[str], *, check: bool = False
) -> list[NormalizationResult]:
    """Normalize each path in ``paths``, collecting per-file results.

    Each file is processed independently via :func:`normalize_file`; a failure
    on one file is recorded on its result and never prevents the remaining
    files from being processed (Requirement 2.5).

    Args:
        paths: The Markdown files to normalize, in processing order.
        check: When True, report-only mode (passed through to
            :func:`normalize_file`). Defaults to False.

    Returns:
        One :class:`NormalizationResult` per input path, in input order.
    """
    return [normalize_file(path, check=check) for path in paths]


def _print_file_reports(results: list[NormalizationResult]) -> None:
    """Print per-file warnings and errors to stderr.

    Warnings and errors are informational only — they never abort the run
    (Requirements 2.5, 3.4). Each message is prefixed with the file path so the
    source of a warning or error is unambiguous at graduation time.

    Args:
        results: Per-file normalization results to report.
    """
    for result in results:
        for warning in result.warnings:
            print(f"warning: {result.path}: {warning}", file=sys.stderr)
        if result.error is not None:
            print(f"error: {result.path}: {result.error}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the Markdown normalization pass.

    Parses arguments, resolves the target set, runs the (non-blocking)
    normalization pass over every target, prints a one-line summary to stdout
    and per-file warnings/errors to stderr, and returns an exit code.

    The pass is non-blocking by contract (Requirements 2.5, 3.4): individual
    file warnings or errors are reported but never abort the run, so ``main``
    returns 0 even when some files warn or error. In ``--check`` mode it returns
    1 when any file would change (report-only, for CI). Argument/usage errors
    are handled by argparse (exit code 2); a genuine usage error detected here
    returns 1.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 on a successful run (including per-file warnings/errors),
        1 in ``--check`` mode when any file would change, and 1 for a usage
        error detected here.
    """
    args = parse_args(argv)
    targets = resolve_targets(args)

    results = normalize_paths(targets, check=args.check)
    _print_file_reports(results)

    total = len(results)
    changed = sum(1 for r in results if r.changed)
    errored = sum(1 for r in results if r.error is not None)
    warned = sum(1 for r in results if r.warnings)

    if args.check:
        summary = (
            f"Checked {total} file(s): {changed} would change, "
            f"{warned} with warnings, {errored} with errors."
        )
    else:
        summary = (
            f"Normalized {changed} of {total} file(s): "
            f"{warned} with warnings, {errored} with errors."
        )
    print(summary)

    # --check is report-only and signals CI when any file would change.
    if args.check and changed:
        return 1

    # Normal runs are non-blocking: per-file warnings/errors never fail the run.
    return 0


if __name__ == "__main__":
    sys.exit(main())
