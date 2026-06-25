#!/usr/bin/env python3
"""Statically detect brittle test assertions in the senzing-bootcamp test suite.

This scanner is a stdlib-only static AST analyzer. It never executes test code;
it parses each ``test_*.py`` file with Python's ``ast`` module and classifies
``assert`` statements by matching syntactic shapes against four brittle-assertion
categories:

- **EXACT_COUNT** — equality against a hard-coded total/whole-suite test count.
- **WHOLE_FILE_SNAPSHOT** — a SHA-256 digest of an entire tracked file compared
  against a hard-coded digest literal.
- **SECTION_SNAPSHOT** — a SHA-256 digest of a section/substring of a tracked file
  compared against a hard-coded digest literal.
- **EXACT_SEQUENCE_SNAPSHOT** — a full ordered list of every heading/line in a
  tracked file compared against a hard-coded list literal.

For each brittle category there is a structural-assertion replacement that
preserves the behavioral intent without coupling to incidental content:

- EXACT_COUNT -> non-regression threshold (``observed >= FLOOR``).
- WHOLE_FILE_SNAPSHOT -> required marker / cross-reference membership checks.
- SECTION_SNAPSHOT -> section-content invariant checks.
- EXACT_SEQUENCE_SNAPSHOT -> ordered-subsequence check tolerating additions.

A **Legitimate_Hash_Use** — hashing test-generated data (a local value, a
Hypothesis-drawn value, a ``tmp_path`` file) or comparing two freshly computed
digests rather than a tracked source file's literal digest — is NOT brittle and is
never flagged.

Usage:
    python3 scan_brittle_assertions.py                 # report-only, exit 0
    python3 scan_brittle_assertions.py --check          # non-zero if findings
    python3 scan_brittle_assertions.py --root PATH ...  # override scan roots
"""

from __future__ import annotations

import argparse
import ast
import enum
import re
import sys
from dataclasses import dataclass
from pathlib import Path


class BrittleCategory(enum.Enum):
    """The four recognized brittle-assertion categories for this codebase."""

    EXACT_COUNT = "exact_count"
    WHOLE_FILE_SNAPSHOT = "whole_file_snapshot"
    SECTION_SNAPSHOT = "section_snapshot"
    EXACT_SEQUENCE_SNAPSHOT = "exact_sequence_snapshot"


@dataclass(frozen=True)
class Finding:
    """A single brittle assertion located by the scanner.

    Attributes:
        file_path: Path to the test file, relative to the repo root.
        line_number: 1-based source line of the ``assert`` statement.
        category: The matched brittle-assertion category.
        allowlisted: True when an Allowlist_Marker exempts this assertion.
    """

    file_path: str
    line_number: int
    category: BrittleCategory
    allowlisted: bool


@dataclass(frozen=True)
class ScanResult:
    """Aggregated result of scanning one or more test roots.

    Attributes:
        files_scanned: Number of ``test_*.py`` files parsed.
        findings: Non-allowlisted brittle assertions.
        exemptions: Brittle assertions exempted by an Allowlist_Marker.
        parse_errors: ``(file_path, error_message)`` pairs for unparseable files.
    """

    files_scanned: int
    findings: list[Finding]
    exemptions: list[Finding]
    parse_errors: list[tuple[str, str]]

    @property
    def findings_by_category(self) -> dict[BrittleCategory, int]:
        """Count non-allowlisted findings grouped by brittle category.

        Returns:
            A mapping from every ``BrittleCategory`` to the number of
            non-allowlisted findings in that category (zero when none).
        """
        counts: dict[BrittleCategory, int] = {category: 0 for category in BrittleCategory}
        for finding in self.findings:
            counts[finding.category] += 1
        return counts


# Whole-suite count name heuristics (EXACT_COUNT). A constant or name matching one
# of these tokens represents a total/passing test count rather than a domain count.
_COUNT_NAME_PATTERNS = ("passing", "total", "test_count", "baseline")

# Snapshot literal/constant name heuristics (WHOLE_FILE / SECTION).
_HASH_NAME_PATTERNS = ("hash", "digest")

# Sequence-snapshot literal/constant name heuristics (EXACT_SEQUENCE).
_SEQUENCE_NAME_PATTERNS = ("headings", "sequence")

# SHA-256 computation helpers whose result is a hexdigest.
_SHA256_HELPERS = ("sha256", "_sha256", "_sha256_bytes")

# Methods that read an entire tracked file's content.
_FILE_READ_CALLS = ("read_bytes", "read_text")

# Helper functions that read an entire tracked file's content.
_FILE_READ_HELPERS = ("_read_file", "_read_hook")

# Hints that a hashed argument is a section/substring rather than a whole file.
_SECTION_EXTRACT_HINTS = ("section", "extract", "snapshot_section")

# Helpers that extract the full ordered list of headings from file content.
_HEADING_EXTRACT_HELPERS = ("_extract_headings", "_extract_all_h2_headings")

# Inline-comment token marking an explicit, reviewed allowlist exemption.
_ALLOWLIST_TOKEN = "brittle-allow"

# A SHA-256 hex digest literal: exactly 64 lowercase hex characters.
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# Default scan roots, relative to the repo root.
_DEFAULT_ROOTS = ("senzing-bootcamp/tests", "tests")

# Repo root, derived from this script's location
# (``<repo>/senzing-bootcamp/scripts/scan_brittle_assertions.py``).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Tokens that mark a hashed argument as test-generated data (Legitimate_Hash_Use).
_TEST_DATA_MARKERS = (
    "tmp_path",
    "draw",
    "hypothesis",
    "getvalue",
    "generated",
    "random",
    "faker",
    "fake_",
)


def _name_of(node: ast.expr) -> str | None:
    """Return the bound identifier for a Name/Attribute expression, else None.

    Args:
        node: An expression node.

    Returns:
        The ``id`` of a ``Name`` or the ``attr`` of an ``Attribute``; otherwise
        ``None``.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _call_func_name(call: ast.Call) -> str | None:
    """Return the simple function name of a call expression, if any.

    Args:
        call: A ``Call`` node.

    Returns:
        The function name for ``func(...)`` or the method name for
        ``obj.method(...)``; otherwise ``None``.
    """
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    """Return True when ``text`` (case-insensitively) contains any pattern.

    Args:
        text: The identifier or string to test.
        patterns: Lowercase substrings to look for.

    Returns:
        True if any pattern is a case-insensitive substring of ``text``.
    """
    low = text.lower()
    return any(pattern in low for pattern in patterns)


def _is_constant_name(name: str) -> bool:
    """Return True when ``name`` looks like an UPPER_SNAKE_CASE module constant.

    A module-level snapshot/count constant (e.g. ``_HASH_ONBOARDING_FLOW``,
    ``_PASSING_BASELINE``, ``_HEADINGS_MODULE_01``) has no lowercase letters,
    which distinguishes it from a freshly computed local such as ``index_digest``.

    Args:
        name: The identifier to test.

    Returns:
        True if ``name`` contains at least one letter and no lowercase letters.
    """
    return any(char.isalpha() for char in name) and name == name.upper()


def _is_int_literal(node: ast.expr) -> bool:
    """Return True when ``node`` is a hard-coded integer literal (not a bool).

    Args:
        node: An expression node.

    Returns:
        True for an integer ``Constant`` that is not a boolean.
    """
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _collect_named_tokens(node: ast.expr) -> list[str]:
    """Collect lowercased Name/Attribute tokens within an expression subtree.

    Args:
        node: The root expression to walk.

    Returns:
        A list of lowercased identifiers for every ``Name`` and ``Attribute``
        found in the subtree.
    """
    tokens: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            tokens.append(sub.id.lower())
        elif isinstance(sub, ast.Attribute):
            tokens.append(sub.attr.lower())
    return tokens


def _references_test_count(node: ast.expr) -> bool:
    """Return True when an expression names a whole-suite/total test count.

    Matches a Name/Attribute whose identifier contains a count pattern, or a
    ``len(...)``/``.count(...)`` measurement over such an identifier.

    Args:
        node: The expression on the non-literal side of a comparison.

    Returns:
        True if the expression references a test-count concept.
    """
    name = _name_of(node)
    if name and _matches_any(name, _COUNT_NAME_PATTERNS):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "len":
            return any(_references_test_count(arg) for arg in node.args)
        if isinstance(func, ast.Attribute) and func.attr == "count":
            return _references_test_count(func.value)
    return False


def _hashed_argument(node: ast.expr) -> ast.expr | None:
    """Return the argument hashed by a SHA-256 computation, if ``node`` is one.

    Recognizes ``hashlib.sha256(arg).hexdigest()`` and helper calls such as
    ``_sha256(arg)``/``sha256(arg)`` whose name carries a SHA-256 hint.

    Args:
        node: The expression on one side of a comparison.

    Returns:
        The hashed argument expression, or ``None`` when ``node`` is not a
        recognized SHA-256 computation (or carries no argument).
    """
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    # hashlib.sha256(arg).hexdigest() / .digest()
    if isinstance(func, ast.Attribute) and func.attr in ("hexdigest", "digest"):
        inner = func.value
        if isinstance(inner, ast.Call):
            inner_name = _call_func_name(inner)
            if inner_name and "sha256" in inner_name.lower() and inner.args:
                return inner.args[0]
        return None
    # _sha256(arg) / sha256(arg) helper that already returns a hexdigest
    name = _call_func_name(node)
    if name and ("sha256" in name.lower() or name in _SHA256_HELPERS) and node.args:
        return node.args[0]
    return None


def _is_digest_anchor(node: ast.expr) -> bool:
    """Return True when ``node`` is a hard-coded SHA-256 digest literal/constant.

    The anchor is either a 64-hex-character string literal or an UPPER_SNAKE_CASE
    module constant (e.g. ``_HASH_ONBOARDING_FLOW`` or ``_SNAP_DETECTION_RULES``,
    which holds a hard-coded digest). Any constant-cased name compared against a
    SHA-256 computation is a hard-coded digest. A lowercase local such as
    ``index_digest`` (a freshly computed value) is deliberately not an anchor.

    Args:
        node: The expression on one side of a comparison.

    Returns:
        True if ``node`` is a hard-coded digest anchor.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return bool(_SHA256_HEX_RE.match(node.value.strip().lower()))
    name = _name_of(node)
    return bool(name and _is_constant_name(name))


def _is_sequence_anchor(node: ast.expr) -> bool:
    """Return True when ``node`` is a hard-coded ordered-sequence literal/constant.

    The anchor is either a list literal or an UPPER_SNAKE_CASE module constant
    (e.g. ``_HEADINGS_MODULE_01``). A lowercase local (a freshly computed list) is
    not an anchor.

    Args:
        node: The expression on one side of a comparison.

    Returns:
        True if ``node`` is a hard-coded sequence anchor.
    """
    if isinstance(node, ast.List):
        return True
    name = _name_of(node)
    return bool(name and _is_constant_name(name))


def _is_heading_extract(node: ast.expr) -> bool:
    """Return True when ``node`` extracts the full heading/line list from content.

    Recognizes the configured heading-extract helpers, any ``*extract*heading*``
    helper call, and ``re.findall(...)`` over file content.

    Args:
        node: The expression on the non-anchor side of a comparison.

    Returns:
        True if ``node`` is a full-sequence extraction call.
    """
    if not isinstance(node, ast.Call):
        return False
    name = _call_func_name(node)
    if not name:
        return False
    low = name.lower()
    if name in _HEADING_EXTRACT_HELPERS:
        return True
    if "extract" in low and ("heading" in low or "h2" in low):
        return True
    return name == "findall"


def _derives_from_test_data(node: ast.expr) -> bool:
    """Return True when a hashed/extracted input derives from test-generated data.

    This is the Legitimate_Hash_Use guard's positive signal: a ``tmp_path`` file,
    a Hypothesis-drawn value, or another test-generated token in the subtree.

    Args:
        node: The hashed or extracted argument expression.

    Returns:
        True if the subtree references a test-data marker.
    """
    tokens = _collect_named_tokens(node)
    return any(_matches_any(token, _TEST_DATA_MARKERS) for token in tokens)


def _references_section(node: ast.expr) -> bool:
    """Return True when the hashed argument is a section/substring of a file.

    A section is signalled by a section/extract token in the subtree, a common
    section-variable name (block/excerpt/snippet/fragment), or a slice subscript
    (``content[start:end]``).

    Args:
        node: The hashed argument expression.

    Returns:
        True if the argument is a section rather than whole-file content.
    """
    section_names = ("block", "excerpt", "snippet", "fragment")
    tokens = _collect_named_tokens(node)
    if any(_matches_any(token, _SECTION_EXTRACT_HINTS) for token in tokens):
        return True
    if any(_matches_any(token, section_names) for token in tokens):
        return True
    return any(
        isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Slice)
        for sub in ast.walk(node)
    )


def _classify_count(left: ast.expr, right: ast.expr) -> BrittleCategory | None:
    """Classify an EXACT_COUNT comparison, if the operands match the shape.

    Requires a hard-coded integer literal on one side and a test-count reference
    on the other.

    Args:
        left: The left comparison operand.
        right: The right comparison operand.

    Returns:
        ``BrittleCategory.EXACT_COUNT`` or ``None``.
    """
    for literal_side, count_side in ((left, right), (right, left)):
        if _is_int_literal(literal_side) and _references_test_count(count_side):
            return BrittleCategory.EXACT_COUNT
    return None


def _classify_snapshot(left: ast.expr, right: ast.expr) -> BrittleCategory | None:
    """Classify a WHOLE_FILE/SECTION snapshot comparison, if the shape matches.

    Requires a hard-coded digest anchor on one side and a SHA-256 computation on
    the other. The Legitimate_Hash_Use guard returns ``None`` when the hashed
    input derives from test-generated data. Section is distinguished from
    whole-file by section/extract hints or a slice subscript.

    Args:
        left: The left comparison operand.
        right: The right comparison operand.

    Returns:
        ``WHOLE_FILE_SNAPSHOT``, ``SECTION_SNAPSHOT``, or ``None``.
    """
    for anchor_side, sha_side in ((left, right), (right, left)):
        if not _is_digest_anchor(anchor_side):
            continue
        hashed = _hashed_argument(sha_side)
        if hashed is None:
            continue
        # Hashing a hard-coded literal is a self-contained check, not a snapshot of
        # a tracked file; treat it as a Legitimate_Hash_Use.
        if isinstance(hashed, ast.Constant):
            return None
        if _derives_from_test_data(hashed):
            return None
        if _references_section(hashed):
            return BrittleCategory.SECTION_SNAPSHOT
        return BrittleCategory.WHOLE_FILE_SNAPSHOT
    return None


def _classify_sequence(left: ast.expr, right: ast.expr) -> BrittleCategory | None:
    """Classify an EXACT_SEQUENCE_SNAPSHOT comparison, if the shape matches.

    Requires a hard-coded sequence anchor (list literal or sequence-named
    constant) on one side and a full heading/line extraction on the other. The
    Legitimate_Hash_Use guard returns ``None`` for test-generated input.

    Args:
        left: The left comparison operand.
        right: The right comparison operand.

    Returns:
        ``BrittleCategory.EXACT_SEQUENCE_SNAPSHOT`` or ``None``.
    """
    for anchor_side, extract_side in ((left, right), (right, left)):
        if _is_sequence_anchor(anchor_side) and _is_heading_extract(extract_side):
            if _derives_from_test_data(extract_side):
                return None
            return BrittleCategory.EXACT_SEQUENCE_SNAPSHOT
    return None


def classify_assertion(
    node: ast.Assert, source_lines: list[str]
) -> BrittleCategory | None:
    """Classify an ``assert`` statement into a brittle category, or ``None``.

    The classifier is a pure function of its inputs. It inspects the assert's test
    expression, which for the brittle forms is an ``==`` ``Compare`` node, and is
    literal-anchored: a snapshot/sequence/count category requires a hard-coded
    literal (or an UPPER_SNAKE_CASE module constant resolved by name) on one side.
    Comparisons of two computed values, legitimate hashes of test-generated data,
    and any ambiguous shape resolve conservatively to ``None``.

    Args:
        node: The ``ast.Assert`` statement (the test expression is ``node.test``).
        source_lines: The source file split into lines (1-based via ``lineno``);
            reserved for marker/line lookups by callers.

    Returns:
        The matched ``BrittleCategory``, or ``None`` when the assertion is
        structural / not brittle.
    """
    del source_lines  # Classification is purely structural; lines are unused here.
    test = node.test
    if not isinstance(test, ast.Compare):
        return None
    # Only a single ``==`` comparison is a brittle snapshot/count shape.
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return None
    left = test.left
    right = test.comparators[0]
    return (
        _classify_count(left, right)
        or _classify_snapshot(left, right)
        or _classify_sequence(left, right)
    )


def has_allowlist_marker(node: ast.Assert, source_lines: list[str]) -> bool:
    """Return True when an Allowlist_Marker exempts the given assertion.

    Reads the source lines spanning the assert statement
    (``node.lineno`` through ``node.end_lineno``, inclusive) and reports whether
    any of them contains the ``brittle-allow`` inline-comment token. ``lineno`` is
    1-based while ``source_lines`` is 0-indexed, so the span maps to
    ``source_lines[node.lineno - 1 : node.end_lineno]``.

    Args:
        node: The ``ast.Assert`` statement to inspect.
        source_lines: The source file split into lines (0-indexed list).

    Returns:
        True if any line in the assertion's span contains the allowlist token.
    """
    start = node.lineno - 1
    end = node.end_lineno if node.end_lineno is not None else node.lineno
    return any(_ALLOWLIST_TOKEN in line for line in source_lines[start:end])


def discover_test_files(roots: list[Path]) -> list[Path]:
    """Find every ``test_*.py`` file under the given roots, sorted.

    Searches each root recursively for files matching the ``test_*.py`` pattern.
    A root that does not exist contributes nothing (``Path.rglob`` over a missing
    path yields no matches), so discovery itself never raises for absent roots;
    the orchestrating ``scan`` is responsible for treating a missing root as an
    error. Results are de-duplicated and returned in sorted path order for
    deterministic output.

    Args:
        roots: Directories to search recursively for test files.

    Returns:
        A sorted list of unique ``test_*.py`` paths discovered under the roots.
    """
    discovered: set[Path] = set()
    for root in roots:
        discovered.update(root.rglob("test_*.py"))
    return sorted(discovered)


def _relative_path(path: Path) -> str:
    """Return ``path`` relative to the repo root when possible, else its string.

    Args:
        path: The file path to render.

    Returns:
        The path relative to the repo root (forward-slash form), falling back to
        ``str(path)`` when it lies outside the repo root.
    """
    try:
        return str(path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


def scan_file(path: Path) -> tuple[list[Finding], str | None]:
    """Parse one test file and classify its ``assert`` statements.

    Reads the file, parses it with ``ast``, walks every ``assert`` node,
    classifies each via :func:`classify_assertion`, and applies the allowlist via
    :func:`has_allowlist_marker` (recording the result on ``Finding.allowlisted``).
    All matched findings are returned regardless of allowlist status; the
    orchestrating :func:`scan` partitions them into findings and exemptions.

    Args:
        path: The ``test_*.py`` file to scan.

    Returns:
        A ``(findings, parse_error)`` tuple. On success ``parse_error`` is
        ``None`` and ``findings`` holds every brittle assertion with its
        ``allowlisted`` flag set. On a ``SyntaxError`` or an unreadable file
        (``OSError``/``UnicodeDecodeError``), returns ``([], message)``.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [], f"could not read file: {error}"
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [], f"syntax error: {error}"

    source_lines = source.splitlines()
    relative = _relative_path(path)
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        category = classify_assertion(node, source_lines)
        if category is None:
            continue
        findings.append(
            Finding(
                file_path=relative,
                line_number=node.lineno,
                category=category,
                allowlisted=has_allowlist_marker(node, source_lines),
            )
        )
    return findings, None


def scan(roots: list[Path]) -> ScanResult:
    """Scan every ``test_*.py`` file under the given roots into a ``ScanResult``.

    Treats a missing root (a path that does not exist) as an error, recording it
    in ``parse_errors`` so the scan is never silently incomplete. Discovers test
    files under the roots, scans each, separates non-allowlisted findings from
    allowlisted exemptions, aggregates parse errors, and counts scanned files.

    Args:
        roots: Directories to search recursively for ``test_*.py`` files.

    Returns:
        A ``ScanResult`` aggregating findings, exemptions, scanned-file count, and
        parse errors.
    """
    parse_errors: list[tuple[str, str]] = []
    findings: list[Finding] = []
    exemptions: list[Finding] = []
    files_scanned = 0

    for root in roots:
        if not root.exists():
            parse_errors.append((_relative_path(root), "scan root does not exist"))

    for path in discover_test_files(roots):
        files_scanned += 1
        file_findings, parse_error = scan_file(path)
        if parse_error is not None:
            parse_errors.append((_relative_path(path), parse_error))
            continue
        for finding in file_findings:
            if finding.allowlisted:
                exemptions.append(finding)
            else:
                findings.append(finding)

    return ScanResult(
        files_scanned=files_scanned,
        findings=findings,
        exemptions=exemptions,
        parse_errors=parse_errors,
    )


def format_summary(result: ScanResult) -> str:
    """Render a human-readable summary of a scan result.

    Produces a multi-line string reporting the number of files scanned, a
    per-category Finding count (one line for every ``BrittleCategory``, including
    categories with a zero count), and the number of allowlisted exemptions.

    Args:
        result: The aggregated scan result to summarize.

    Returns:
        A multi-line summary string suitable for printing to stdout.
    """
    counts = result.findings_by_category
    lines = [
        "Brittle assertion scan summary",
        f"  Files scanned: {result.files_scanned}",
        "  Findings by category:",
    ]
    for category in BrittleCategory:
        lines.append(f"    {category.value}: {counts[category]}")
    lines.append(f"  Allowlisted exemptions: {len(result.exemptions)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run the brittleness scan.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        Process exit code:
            * non-zero on any parse/scan error, regardless of ``--check``
              (a partial scan must never pass);
            * non-zero under ``--check`` when at least one non-allowlisted
              finding is present;
            * 0 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Detect brittle test assertions in the test suite.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when any non-allowlisted finding is present.",
    )
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        type=Path,
        help=(
            "Scan root to search for test_*.py files (repeatable). "
            f"Defaults to: {', '.join(_DEFAULT_ROOTS)}"
        ),
    )
    args = parser.parse_args(argv)

    roots = args.roots if args.roots else [Path(root) for root in _DEFAULT_ROOTS]
    result = scan(roots)

    print(format_summary(result))
    for finding in result.findings:
        print(f"{finding.file_path}:{finding.line_number} {finding.category.value}")

    for file_path, message in result.parse_errors:
        print(f"{file_path}: {message}", file=sys.stderr)

    # A parse/scan error means the scan is incomplete; fail regardless of --check.
    if result.parse_errors:
        return 1
    if args.check and len(result.findings) >= 1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
