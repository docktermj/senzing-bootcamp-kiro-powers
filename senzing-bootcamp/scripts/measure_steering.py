#!/usr/bin/env python3
"""Measure token counts for steering files and update steering-index.yaml.

Scans all .md files in the steering directory, calculates approximate token
counts (characters / 4), and writes file_metadata + budget sections into
steering-index.yaml while preserving all existing content.

Usage:
    python senzing-bootcamp/scripts/measure_steering.py              # update mode
    python senzing-bootcamp/scripts/measure_steering.py --check      # validation mode
    python senzing-bootcamp/scripts/measure_steering.py --simulate   # simulation mode
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_STEERING_DIR = Path("senzing-bootcamp/steering")
DEFAULT_INDEX_PATH = Path("senzing-bootcamp/steering/steering-index.yaml")


@dataclass
class PhaseEntry:
    """A phase entry parsed from the modules/onboarding/session-resume maps.

    Each phase block (``modules.*.phases.*``, ``onboarding.*.phases.*``, or
    ``session-resume.*.phases.*``) has a ``file:`` line plus sibling
    ``token_count:`` and ``size_category:`` lines. The line indices are 0-based
    positions in the full content's line list so an in-place rewrite is possible.

    Attributes:
        filename: Steering markdown filename from the phase's ``file:`` line.
        token_count: Stored ``token_count`` value, or None if absent.
        size_category: Stored ``size_category`` value, or None if absent.
        token_count_line: 0-based line index of the ``token_count:`` line, or None.
        size_category_line: 0-based line index of the ``size_category:`` line, or None.
    """

    filename: str
    token_count: int | None
    size_category: str | None
    token_count_line: int | None
    size_category_line: int | None


@dataclass
class AlwaysLoadedResult:
    """Outcome of the always-loaded baseline check.

    Attributes:
        always_loaded: The authoritative Always_Loaded_Set (sorted filenames
            declaring ``inclusion: always``).
        footprint_tokens: The Baseline_Footprint — summed measured
            ``token_count`` of the always-loaded files.
        warn_threshold_tokens: The Warn_Threshold in tokens
            (``warn_threshold_pct/100 * reference_window``).
        ceiling_pct: The configured ``budget.always_loaded_ceiling_pct``.
        ceiling_tokens: The ceiling in tokens
            (``ceiling_pct/100 * warn_threshold_tokens``).
        pct_of_warn: Percentage of the Warn_Threshold consumed
            (``footprint_tokens / warn_threshold_tokens * 100``).
        over_budget: True when ``footprint_tokens`` exceeds ``ceiling_tokens``.
    """

    always_loaded: list[str]
    footprint_tokens: int
    warn_threshold_tokens: int
    ceiling_pct: int
    ceiling_tokens: int
    pct_of_warn: float
    over_budget: bool


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


def parse_inclusion(filepath) -> str | None:
    """Return the ``inclusion`` value from a steering file's YAML frontmatter.

    Reads only the leading frontmatter block delimited by ``---`` fences and
    extracts the ``inclusion:`` value (``always`` | ``fileMatch`` | ``manual`` |
    ``auto``), tolerating surrounding whitespace and optional quotes. Uses a
    minimal stdlib regex (no PyYAML). Never raises on a missing or malformed
    frontmatter block — returns None when the file has no frontmatter or no
    ``inclusion`` key. Read errors (e.g. ``PermissionError``) are allowed to
    propagate so callers can handle them like ``scan_steering_files``.

    Args:
        filepath: Path to a steering markdown file.

    Returns:
        The ``inclusion`` value, or None when absent/malformed.
    """
    content = Path(filepath).read_text(encoding="utf-8")

    lines = content.splitlines()
    # Frontmatter must be the leading block, opening with a `---` fence.
    if not lines or lines[0].strip() != "---":
        return None

    inclusion_pattern = re.compile(r"^\s*inclusion:\s*[\"']?(\w+)[\"']?\s*$")
    for line in lines[1:]:
        if line.strip() == "---":
            break  # end of frontmatter block
        match = inclusion_pattern.match(line)
        if match:
            return match.group(1)
    return None


def collect_always_loaded_set(steering_dir) -> list[str]:
    """Return the sorted filenames of steering files declaring ``inclusion: always``.

    Scans ``*.md`` files in ``steering_dir`` (mirroring ``scan_steering_files``'s
    globbing), calls ``parse_inclusion`` on each, and returns the names whose
    inclusion is exactly ``always``. This is the single authoritative
    Always_Loaded_Set that drives both ``--simulate`` and
    ``check_always_loaded_budget``. Unreadable files are skipped with a stderr
    warning, mirroring the ``PermissionError`` handling in ``scan_steering_files``.

    Args:
        steering_dir: Path to the steering directory.

    Returns:
        Sorted list of filenames whose frontmatter ``inclusion`` is ``always``.
    """
    steering_path = Path(steering_dir)
    if not steering_path.is_dir():
        print(f"Error: steering directory not found: {steering_path}", file=sys.stderr)
        sys.exit(1)

    always_loaded: list[str] = []
    for md_file in sorted(steering_path.glob("*.md")):
        try:
            if parse_inclusion(md_file) == "always":
                always_loaded.append(md_file.name)
        except PermissionError:
            print(f"Warning: cannot read {md_file.name}, skipping", file=sys.stderr)
    return sorted(always_loaded)


def compute_baseline_footprint(always_loaded: list[str], file_metadata: dict) -> int:
    """Sum the measured token_count of the always-loaded files.

    Uses the measured ``file_metadata`` (from ``scan_steering_files``) so the
    footprint reflects the files on disk, not stored values. Files absent from
    ``file_metadata`` contribute 0, and the result is independent of the order of
    ``always_loaded``.

    Args:
        always_loaded: Filenames of the Always_Loaded_Set (from
            ``collect_always_loaded_set``).
        file_metadata: dict from ``scan_steering_files`` mapping filename to a
            metadata dict containing ``token_count``.

    Returns:
        The Baseline_Footprint: the summed ``token_count`` of the always-loaded
        files present in ``file_metadata``.
    """
    return sum(
        file_metadata.get(name, {}).get("token_count", 0)
        for name in always_loaded
    )


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


def update_index(index_path, file_metadata, total_tokens, steering_dir=DEFAULT_STEERING_DIR):
    """Write file_metadata and budget sections into the YAML file.

    Preserves all existing content above the file_metadata section, except that
    out-of-tolerance phase entries in that preserved region have their
    ``token_count`` / ``size_category`` reconciled to the measured value via
    ``rewrite_phase_counts``. In-tolerance phases and all non-phase content
    (``budget``, ``keywords``, ``languages``, ``deployment``, module ``root`` /
    ``step_range``) are left byte-identical. The ``file_metadata`` / ``budget``
    rebuild, ``split_threshold_tokens`` preservation, ``router_ceiling``
    preservation (defaulting to ``1000`` when absent), and
    ``always_loaded_ceiling_pct`` preservation (defaulting to ``25`` when
    absent) are unchanged, and
    ``total_tokens`` remains the sum of ``file_metadata`` counts only (phase
    counts are never added to the budget total).

    The ``steering_dir`` argument keeps the old positional call sites working
    (it defaults to ``DEFAULT_STEERING_DIR``), so existing direct callers such as
    ``update_index(index_path, metadata, total)`` continue to reconcile phase
    counts against the standard steering directory. Phase reconciliation only
    rewrites out-of-tolerance phases, so an index with no drifted phases is left
    byte-identical above ``file_metadata``.

    Uses string manipulation (no PyYAML) to keep existing YAML byte-identical
    where no value changed.

    Args:
        index_path: Path to steering-index.yaml.
        file_metadata: dict from scan_steering_files() ({filename: {...}}).
        total_tokens: Sum of file_metadata token counts (budget.total_tokens).
        steering_dir: Path to the steering directory holding the phase .md files,
            used to measure phase files when reconciling phase counts. Defaults
            to ``DEFAULT_STEERING_DIR`` so existing callers keep working.
    """
    index_path = Path(index_path)
    split_threshold = None
    router_ceiling = None
    always_loaded_ceiling = None

    if index_path.exists():
        content = load_yaml_content(index_path)
        # Reconcile out-of-tolerance phase token counts in the preserved region
        # (above file_metadata) before composing the new file. In-tolerance
        # phases and all non-phase content stay byte-identical.
        content = rewrite_phase_counts(content, steering_dir)
        # Check for split_threshold_tokens before truncating
        threshold_match = re.search(r"split_threshold_tokens:\s*(\d+)", content)
        if threshold_match:
            split_threshold = threshold_match.group(1)
        # Check for router_ceiling before truncating
        ceiling_match = re.search(r"router_ceiling:\s*(\d+)", content)
        if ceiling_match:
            router_ceiling = ceiling_match.group(1)
        # Check for always_loaded_ceiling_pct before truncating
        always_loaded_match = re.search(
            r"always_loaded_ceiling_pct:\s*(\d+)", content
        )
        if always_loaded_match:
            always_loaded_ceiling = always_loaded_match.group(1)
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

    # Preserve always_loaded_ceiling_pct if it existed; default to 25 when absent
    if always_loaded_ceiling is not None:
        lines.append(f"  always_loaded_ceiling_pct: {always_loaded_ceiling}")
    else:
        lines.append("  always_loaded_ceiling_pct: 25")

    # Preserve split_threshold_tokens if it existed in the original content
    if split_threshold is not None:
        lines.append(f"  split_threshold_tokens: {split_threshold}")

    # Preserve router_ceiling if it existed; default to 1000 when absent
    if router_ceiling is not None:
        lines.append(f"  router_ceiling: {router_ceiling}")
    else:
        lines.append("  router_ceiling: 1000")

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


def parse_budget_total(content: str) -> int | None:
    """Extract budget.total_tokens from YAML content via a localized regex.

    Uses the same minimal-regex approach as ``simulate_context_load`` (which reads
    ``reference_window`` with ``re.search(r"reference_window:\\s*(\\d+)")``), matching
    the ``total_tokens:`` line in the budget section. This is the declared aggregate
    that the ``--check`` mode compares against the sum of per-file ``token_count``
    values.

    Args:
        content: Raw YAML text of steering-index.yaml.

    Returns:
        The declared ``budget.total_tokens`` value, or None if not found.
    """
    match = re.search(r"total_tokens:\s*(\d+)", content)
    return int(match.group(1)) if match else None


def parse_always_loaded_ceiling_pct(content: str, default: int = 25) -> int:
    """Extract budget.always_loaded_ceiling_pct from YAML content via a localized regex.

    Uses the same minimal-regex approach as ``parse_budget_total`` (and
    ``simulate_context_load``'s ``reference_window`` read), matching the
    ``always_loaded_ceiling_pct:`` line in the budget section. This is the ceiling,
    expressed as a percentage of the warn threshold, that the always-loaded baseline
    footprint must stay under. Returning the documented default when the key is absent
    keeps the check operable before the key is added to ``steering-index.yaml``.

    Args:
        content: Raw YAML text of steering-index.yaml.
        default: Ceiling percentage to use when the key is absent (documented default 25).

    Returns:
        The declared ``budget.always_loaded_ceiling_pct`` value, or ``default`` if not found.
    """
    match = re.search(r"always_loaded_ceiling_pct:\s*(\d+)", content)
    return int(match.group(1)) if match else default


def _parse_phase_entries(content: str) -> list[PhaseEntry]:
    """Parse phase entries from the region above the file_metadata section.

    Walks the YAML text line by line. Each ``file:`` line marks the start of a
    phase block (``modules.*.phases.*``, ``onboarding.*.phases.*``, or
    ``session-resume.*.phases.*``); the immediately-following sibling lines at the
    same indentation supply the stored ``token_count:`` and ``size_category:``
    values. Keying on ``file:`` lines naturally excludes ``root:`` entries (no
    ``file:`` line) and ``file_metadata`` entries (keyed by filename, no ``file:``
    field), and the walk is bounded above the ``file_metadata`` section so its
    entries are never reached.

    Args:
        content: Raw YAML text of steering-index.yaml.

    Returns:
        A list of PhaseEntry records, one per ``file:`` line found above
        file_metadata, in document order.
    """
    lines = content.splitlines()

    # Bound the walk to the region above file_metadata (if present).
    fm_pos = _find_section_start(content, "file_metadata")
    if fm_pos >= 0:
        # Number of lines before the file_metadata section.
        limit = content[:fm_pos].count("\n")
    else:
        limit = len(lines)

    file_pattern = re.compile(r"^(\s+)file:\s+([\w.-]+\.md)\s*$")
    tc_pattern = re.compile(r"^(\s+)token_count:\s*(\d+)\s*$")
    sc_pattern = re.compile(r"^(\s+)size_category:\s*(\w+)\s*$")

    entries: list[PhaseEntry] = []
    for idx in range(limit):
        file_match = file_pattern.match(lines[idx])
        if not file_match:
            continue

        indent = file_match.group(1)
        filename = file_match.group(2)
        token_count: int | None = None
        size_category: str | None = None
        token_count_line: int | None = None
        size_category_line: int | None = None

        # Scan sibling lines within this phase block (same indent), stopping at
        # the next dedent or the next file: line (start of another phase block).
        for sib in range(idx + 1, limit):
            sib_line = lines[sib]
            if not sib_line.strip():
                continue
            sib_indent = len(sib_line) - len(sib_line.lstrip())
            if sib_indent < len(indent) or file_pattern.match(sib_line):
                break
            tc_match = tc_pattern.match(sib_line)
            if tc_match:
                token_count = int(tc_match.group(2))
                token_count_line = sib
                continue
            sc_match = sc_pattern.match(sib_line)
            if sc_match:
                size_category = sc_match.group(2)
                size_category_line = sib

        entries.append(
            PhaseEntry(
                filename=filename,
                token_count=token_count,
                size_category=size_category,
                token_count_line=token_count_line,
                size_category_line=size_category_line,
            )
        )

    return entries


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


def check_phase_counts(
    index_path, steering_dir
) -> list[tuple[str, int | None, int | None]]:
    """Compare stored vs measured phase token counts, return mismatches >10%.

    Parses every phase entry (``modules.*.phases.*``, ``onboarding.*.phases.*``,
    and ``session-resume.*.phases.*``) from the index above the file_metadata
    section and compares each stored ``token_count`` against the freshly measured
    count of its ``file`` using the same 10% tolerance applied to file_metadata.
    A phase whose ``file`` does not exist on disk is reported as a mismatch
    (mirroring file_metadata removed-file detection in ``check_counts``). This
    function performs a pure read and never modifies the index.

    Args:
        index_path: Path to steering-index.yaml.
        steering_dir: Path to the steering directory holding the phase .md files.

    Returns:
        list of (filename, stored_count, measured_count) tuples for mismatches.
        For a phase whose file is missing on disk, measured_count is None.
    """
    content = load_yaml_content(index_path)
    entries = _parse_phase_entries(content)
    steering_path = Path(steering_dir)

    mismatches: list[tuple[str, int | None, int | None]] = []
    for entry in entries:
        stored_count = entry.token_count
        phase_path = steering_path / entry.filename
        if not phase_path.is_file():
            mismatches.append((entry.filename, stored_count, None))
            continue
        measured = calculate_token_count(phase_path)
        if stored_count is None:
            mismatches.append((entry.filename, None, measured))
            continue
        denominator = max(measured, 1)
        if abs(stored_count - measured) / denominator > 0.10:
            mismatches.append((entry.filename, stored_count, measured))

    return mismatches


def check_always_loaded_budget(
    index_path, steering_dir, file_metadata
) -> AlwaysLoadedResult:
    """Compute the always-loaded baseline result (pure read).

    Derives the authoritative Always_Loaded_Set (``collect_always_loaded_set``),
    the Baseline_Footprint (``compute_baseline_footprint`` over the measured
    ``file_metadata``), the Warn_Threshold in tokens (from ``reference_window``
    times ``warn_threshold_pct``, read with the same localized-regex approach
    used by ``simulate_context_load`` and defaulting to ``200000`` / ``60`` when
    absent), and the ceiling (``parse_always_loaded_ceiling_pct``). Sets
    ``over_budget`` when the footprint exceeds ``ceiling_pct/100 *
    warn_threshold_tokens``. This function does not print or exit — ``main``
    renders the report and aggregates the result into the exit decision.

    Args:
        index_path: Path to steering-index.yaml.
        steering_dir: Path to the steering directory holding the .md files.
        file_metadata: dict from ``scan_steering_files`` mapping filename to a
            metadata dict containing ``token_count``.

    Returns:
        An ``AlwaysLoadedResult`` describing the footprint, thresholds, and the
        pass/fail decision.
    """
    content = load_yaml_content(index_path)

    # Warn threshold in tokens: warn_threshold_pct/100 * reference_window,
    # read with the same localized regex approach as simulate_context_load and
    # defaulting to 200000 / 60 for robustness when the keys are absent.
    rw_match = re.search(r"reference_window:\s*(\d+)", content)
    reference_window = int(rw_match.group(1)) if rw_match else 200000
    wt_match = re.search(r"warn_threshold_pct:\s*(\d+)", content)
    warn_threshold_pct = int(wt_match.group(1)) if wt_match else 60
    warn_threshold_tokens = round(warn_threshold_pct / 100 * reference_window)

    ceiling_pct = parse_always_loaded_ceiling_pct(content)
    ceiling_tokens = round(ceiling_pct / 100 * warn_threshold_tokens)

    always_loaded = collect_always_loaded_set(steering_dir)
    footprint_tokens = compute_baseline_footprint(always_loaded, file_metadata)

    # Guard divide-by-zero when the warn threshold resolves to 0 tokens.
    pct_of_warn = (
        footprint_tokens / warn_threshold_tokens * 100
        if warn_threshold_tokens
        else 0.0
    )
    over_budget = footprint_tokens > ceiling_tokens

    return AlwaysLoadedResult(
        always_loaded=always_loaded,
        footprint_tokens=footprint_tokens,
        warn_threshold_tokens=warn_threshold_tokens,
        ceiling_pct=ceiling_pct,
        ceiling_tokens=ceiling_tokens,
        pct_of_warn=pct_of_warn,
        over_budget=over_budget,
    )


def format_always_loaded_report(
    result: AlwaysLoadedResult, file_metadata: dict | None = None
) -> list[str]:
    """Render the always-loaded baseline check report as a list of lines.

    Always renders the Baseline_Footprint in tokens, the Warn_Threshold in
    tokens, the percentage of the Warn_Threshold consumed, and the configured
    ceiling (Requirement 3.1). When ``result.over_budget`` is true, additionally
    names each contributing always-loaded file (Requirement 3.2). Per-file token
    counts are shown when ``file_metadata`` is provided (the same measured map
    used to compute the footprint); when it is ``None`` or a file is absent from
    it, the filename is listed without a count.

    Args:
        result: The ``AlwaysLoadedResult`` from ``check_always_loaded_budget``.
        file_metadata: Optional dict from ``scan_steering_files`` mapping filename
            to a metadata dict containing ``token_count``. When provided, each
            contributing file is named with its measured token count on failure.

    Returns:
        A list of report lines suitable for printing one per line.
    """
    status = "OVER BUDGET" if result.over_budget else "within budget"
    lines = [
        f"Always-loaded baseline check: {status}",
        f"  Baseline footprint: {result.footprint_tokens} tokens",
        f"  Warn threshold: {result.warn_threshold_tokens} tokens",
        f"  Percent of warn threshold consumed: {result.pct_of_warn:.1f}%",
        (
            f"  Ceiling: {result.ceiling_pct}% of warn threshold "
            f"({result.ceiling_tokens} tokens)"
        ),
    ]

    if result.over_budget:
        lines.append("  Contributing always-loaded files:")
        for name in result.always_loaded:
            token_count = None
            if file_metadata is not None:
                token_count = file_metadata.get(name, {}).get("token_count")
            if token_count is not None:
                lines.append(f"    - {name}: {token_count} tokens")
            else:
                lines.append(f"    - {name}")

    return lines


def rewrite_phase_counts(content: str, steering_dir) -> str:
    """Return content with out-of-tolerance phase token_count/size_category fixed.

    For each phase record from ``_parse_phase_entries``, measures the phase file's
    token count and applies the same 10% tolerance test used by
    ``check_phase_counts`` (``abs(stored - measured) / max(measured, 1) > 0.10``).
    Only phases that are OUT of tolerance are rewritten: that block's
    ``token_count:`` value line is set to the measured count and its
    ``size_category:`` value line to ``classify_size(measured)``. A phase already
    WITHIN tolerance is left byte-identical, which keeps update mode from
    disturbing in-tolerance phase entries (Requirements 3.2, 3.6). A phase whose
    stored ``token_count`` is missing/None cannot be tolerance-checked and is
    treated as drifted (reconciled to the measured value), mirroring how
    ``check_phase_counts`` reports a None stored count as a mismatch.

    The edit re-derives each line's existing leading whitespace, so indentation,
    the surrounding ``file:`` / ``step_range:`` lines, module/phase structure, and
    ordering are all preserved. A phase whose ``file`` does not exist on disk is
    left unchanged (no crash). This function does not write to disk.

    Args:
        content: Raw YAML text of steering-index.yaml.
        steering_dir: Path to the steering directory holding the phase .md files.

    Returns:
        The updated YAML text. Returns byte-identical content when no phase value
        is out of tolerance.
    """
    entries = _parse_phase_entries(content)
    steering_path = Path(steering_dir)

    # Preserve the original trailing newline (splitlines drops it) so the rebuilt
    # text is byte-identical when nothing changes.
    lines = content.splitlines()
    trailing_newline = content.endswith("\n")

    for entry in entries:
        phase_path = steering_path / entry.filename
        if not phase_path.is_file():
            continue
        measured = calculate_token_count(phase_path)

        # Gate on tolerance: leave in-tolerance phases byte-identical. A None
        # stored count can't be compared, so treat it as drifted (reconcile).
        stored = entry.token_count
        if stored is not None:
            denominator = max(measured, 1)
            if abs(stored - measured) / denominator <= 0.10:
                continue

        new_cat = classify_size(measured)

        if entry.token_count_line is not None:
            old_line = lines[entry.token_count_line]
            indent = old_line[: len(old_line) - len(old_line.lstrip())]
            lines[entry.token_count_line] = f"{indent}token_count: {measured}"

        if entry.size_category_line is not None:
            old_line = lines[entry.size_category_line]
            indent = old_line[: len(old_line) - len(old_line.lstrip())]
            lines[entry.size_category_line] = f"{indent}size_category: {new_cat}"

    rebuilt = "\n".join(lines)
    if trailing_newline:
        rebuilt += "\n"
    return rebuilt


def _parse_modules_section(content: str) -> dict[int, list[str]]:
    """Parse the modules section to get module-to-steering-file mappings.

    Returns:
        dict mapping module number to list of steering filenames for that module.
    """
    modules: dict[int, list[str]] = {}
    # Match simple entries like "  1: module-01-business-problem.md"
    simple_pattern = re.compile(r"^\s+(\d+):\s+([\w.-]+\.md)\s*$", re.MULTILINE)
    for match in simple_pattern.finditer(content):
        mod_num = int(match.group(1))
        modules.setdefault(mod_num, []).append(match.group(2))

    # Match root entries in split modules like "    root: module-01-business-problem.md"
    root_pattern = re.compile(r"^\s+root:\s+([\w.-]+\.md)\s*$", re.MULTILINE)
    # Match phase file entries like "      file: module-01-phase1-discovery.md"
    phase_pattern = re.compile(r"^\s+file:\s+([\w.-]+\.md)\s*$", re.MULTILINE)

    # For split modules, find the module number context
    split_pattern = re.compile(
        r"^\s+(\d+):\s*\n((?:\s{4,}.*\n)*)", re.MULTILINE
    )
    for match in split_pattern.finditer(content):
        mod_num = int(match.group(1))
        block = match.group(2)
        for root_match in root_pattern.finditer(block):
            modules.setdefault(mod_num, []).append(root_match.group(1))
        for phase_match in phase_pattern.finditer(block):
            modules.setdefault(mod_num, []).append(phase_match.group(1))

    return modules


def simulate_context_load(
    index_path: Path, file_metadata: dict, steering_dir=DEFAULT_STEERING_DIR
) -> None:
    """Simulate per-module context load and show token usage with/without unloading.

    The always-loaded baseline is sourced from ``collect_always_loaded_set`` so
    ``--simulate`` and ``check_always_loaded_budget`` share one authoritative
    definition (the steering files declaring ``inclusion: always``). The
    representative language file (``lang-python.md``) remains a simulation-only
    assumption and is not part of the enforced baseline.

    Args:
        index_path: Path to steering-index.yaml.
        file_metadata: dict from scan_steering_files().
        steering_dir: Path to the steering directory used to derive the
            always-loaded set. Defaults to ``DEFAULT_STEERING_DIR`` so existing
            call sites keep working.
    """
    content = load_yaml_content(index_path)

    # Parse reference_window from budget section
    rw_match = re.search(r"reference_window:\s*(\d+)", content)
    reference_window = int(rw_match.group(1)) if rw_match else 200000

    # Always-loaded files: derived from the single authoritative source so
    # --simulate and the always-loaded budget check never disagree.
    always_loaded = collect_always_loaded_set(steering_dir)
    always_tokens = sum(
        file_metadata.get(f, {}).get("token_count", 0) for f in always_loaded
    )

    # Assume a representative language file (~1800 tokens)
    lang_file = "lang-python.md"
    lang_tokens = file_metadata.get(lang_file, {}).get("token_count", 1800)

    # Parse module-to-file mappings
    modules_map = _parse_modules_section(content)

    # Simulate progression through modules 1-11
    completed_tokens = 0
    peak_without_unload = 0
    peak_with_unload = 0

    print(f"Context Load Simulation (reference_window: {reference_window:,} tokens)")
    print("=" * 72)
    print(f"{'Module':<10} {'Always':>8} {'Lang':>6} {'Module':>8} "
          f"{'Completed':>10} {'Total':>8} {'% Used':>7}")
    print("-" * 72)

    for mod_num in range(1, 12):
        # Get this module's steering file tokens
        mod_files = modules_map.get(mod_num, [])
        mod_tokens = sum(
            file_metadata.get(f, {}).get("token_count", 0) for f in mod_files
        )

        # Without unloading: accumulate all completed module tokens
        total_without = always_tokens + lang_tokens + mod_tokens + completed_tokens
        pct_without = total_without / reference_window * 100

        # With unloading: only current module + always + lang
        total_with = always_tokens + lang_tokens + mod_tokens

        peak_without_unload = max(peak_without_unload, total_without)
        peak_with_unload = max(peak_with_unload, total_with)

        print(f"Module {mod_num:<4} {always_tokens:>8,} {lang_tokens:>6,} "
              f"{mod_tokens:>8,} {completed_tokens:>10,} "
              f"{total_without:>8,} {pct_without:>6.1f}%")

        # After this module, its tokens become "completed"
        completed_tokens += mod_tokens

    print("-" * 72)
    print(f"\nPeak without unloading: {peak_without_unload:,} tokens "
          f"({peak_without_unload / reference_window * 100:.1f}% of {reference_window:,})")
    print(f"Peak with unloading:    {peak_with_unload:,} tokens "
          f"({peak_with_unload / reference_window * 100:.1f}% of {reference_window:,})")


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
        "--simulate",
        action="store_true",
        help="Show simulated token load per module with and without unloading",
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

    if args.simulate:
        simulate_context_load(args.index_path, file_metadata, args.steering_dir)
    elif args.check:
        mismatches = check_counts(args.index_path, file_metadata)
        phase_mismatches = check_phase_counts(args.index_path, args.steering_dir)
        # Additive aggregate check: declared budget.total_tokens must equal the
        # sum of per-file token_count values. Reuse _parse_stored_metadata so the
        # "sum" definition matches check_counts exactly (exact equality, not ±10%).
        content = load_yaml_content(args.index_path)
        declared_total = parse_budget_total(content)
        stored_metadata = _parse_stored_metadata(content) or {}
        expected_total = sum(
            meta.get("token_count", 0) for meta in stored_metadata.values()
        )
        budget_mismatch = declared_total != expected_total
        # Always-loaded baseline check: additive to the aggregate exit decision.
        # It can only add a failure reason, never suppress the existing checks.
        always_result = check_always_loaded_budget(
            args.index_path, args.steering_dir, file_metadata
        )
        if mismatches:
            print("Token count mismatches (>10% difference):")
            for filename, stored, calculated in mismatches:
                stored_str = str(stored) if stored is not None else "MISSING"
                calc_str = str(calculated) if calculated is not None else "REMOVED"
                print(f"  {filename}: stored={stored_str}, calculated={calc_str}")
        if phase_mismatches:
            print("Phase token count mismatches (>10% difference):")
            for filename, stored, measured in phase_mismatches:
                stored_str = str(stored) if stored is not None else "MISSING"
                measured_str = str(measured) if measured is not None else "REMOVED"
                print(f"  {filename}: stored={stored_str}, calculated={measured_str}")
        if budget_mismatch:
            declared_str = str(declared_total) if declared_total is not None else "MISSING"
            print(
                f"Budget total mismatch: declared={declared_str}, "
                f"sum(file_metadata)={expected_total}"
            )
        for line in format_always_loaded_report(always_result, file_metadata):
            print(line)
        if (
            mismatches
            or phase_mismatches
            or budget_mismatch
            or always_result.over_budget
        ):
            sys.exit(1)
        else:
            print("All token counts are within 10% tolerance.")
            sys.exit(0)
    else:
        update_index(args.index_path, file_metadata, total_tokens, args.steering_dir)
        print_summary(file_metadata, total_tokens)


if __name__ == "__main__":
    main()
