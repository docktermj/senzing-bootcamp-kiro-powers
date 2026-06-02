#!/usr/bin/env python3
"""Validate that each governing rule is wired to its enforcement point(s).

Loads the canonical governance-rules registry
(`senzing-bootcamp/config/governance-rules.yaml`), validates its schema, and
evaluates every declarative assertion against the actual repository files. Any
rule whose enforcement assertion no longer holds is reported as a violation, so
drift between a stated governing rule and where it is enforced fails CI.

This is a verification layer only — it does not move, duplicate, or modify any
existing enforcement logic. It is stdlib-only (no PyYAML) and introduces no
external endpoints.

Usage:
    python senzing-bootcamp/scripts/validate_governance_rules.py
    python senzing-bootcamp/scripts/validate_governance_rules.py \\
        --registry path/to/governance-rules.yaml
    python senzing-bootcamp/scripts/validate_governance_rules.py \\
        --repo-root path/to/repo

Exit codes:
    0 — Registry is structurally valid, every assertion holds, no internal error.
    1 — Load error, schema error, malformed/unsupported assertion, at least one
        content violation, or an internal evaluation error.

Examples:
    # Validate using default paths (repo root inferred from script location)
    python senzing-bootcamp/scripts/validate_governance_rules.py

    # Validate a specific registry file
    python senzing-bootcamp/scripts/validate_governance_rules.py \\
        --registry senzing-bootcamp/config/governance-rules.yaml

    # Resolve enforcement paths against an explicit repo root (useful for tests)
    python senzing-bootcamp/scripts/validate_governance_rules.py \\
        --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TextIO

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Assertion:
    """A single declarative, checkable condition attached to a Rule Entry.

    Attributes:
        type: One of the seven supported assertion types.
        file: Repo-root-relative target file path.
        value: Substring or hook field value (escape-decoded).
        pattern: Regex pattern (escape-decoded, passed verbatim to re.search).
        key_path: Dotted path for hook_field_equals / yaml_key_present.
    """

    type: str
    file: str | None = None
    value: str | None = None
    pattern: str | None = None
    key_path: str | None = None


@dataclass(frozen=True)
class RuleEntry:
    """One governing rule and its enforcement linkage.

    Attributes:
        id: Stable, unique identifier for the rule.
        rule: Human-readable governing rule text.
        category: Non-empty classification string.
        enforced_by: List of one or more enforcement points (paths / hook ids).
        assertions: List of checkable assertions for this rule.
        static_checkable: False => behavioral-only rule, no assertions, skipped.
    """

    id: str
    rule: str
    category: str
    enforced_by: list[str]
    assertions: list[Assertion]
    static_checkable: bool = True


@dataclass(frozen=True)
class Violation:
    """A reported failure: a schema problem or a failing content assertion.

    Attributes:
        rule_id: Id of the failing rule ("" for top-level schema errors).
        kind: "schema" or "content".
        detail: Human-readable cause.
        assertion: The failing assertion (for content violations).
        file: File path involved, when applicable.
    """

    rule_id: str
    kind: str
    detail: str
    assertion: Assertion | None = None
    file: str | None = None


@dataclass(frozen=True)
class RunResult:
    """Aggregate outcome of a validator run.

    Attributes:
        rules_checked: Number of Rule Entries checked.
        violations: All violations collected during the run.
        completed: True only if evaluation ran to completion.
        exit_code: 0 iff schema valid AND no violations AND no internal error.
    """

    rules_checked: int
    violations: list[Violation]
    completed: bool
    exit_code: int


# ---------------------------------------------------------------------------
# Registry loading (minimal YAML subset parser)
# ---------------------------------------------------------------------------


class RegistryLoadError(Exception):
    """Raised when the registry file is missing, unreadable, or unparseable.

    This covers a missing or unreadable file as well as structural parse
    failures (unterminated quote, unsupported escape, bad indentation, or a
    top-level key other than ``rules``).
    """


# Indentation levels (two spaces per nesting level) for the constrained subset.
_RULE_DASH_INDENT = 2  # "- " marker that starts a rule mapping
_RULE_KEY_INDENT = 4  # rule mapping keys (id, rule, category, ...)
_NESTED_SEQ_INDENT = 6  # enforced_by scalars / assertion "- " markers
_ASSERTION_KEY_INDENT = 8  # assertion mapping continuation keys

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _decode_unicode_escape(raw: str, bs_index: int, line_no: int) -> tuple[int, int]:
    """Decode one ``\\uXXXX`` escape beginning at the backslash.

    Args:
        raw: The full quoted-scalar text being decoded.
        bs_index: Index of the backslash that introduces the ``\\u`` escape.
        line_no: 1-based source line number, used in error messages.

    Returns:
        A tuple of ``(code unit value, index just past the escape)``.

    Raises:
        RegistryLoadError: If the four hex digits are missing or malformed.
    """
    hex_part = raw[bs_index + 2 : bs_index + 6]
    if len(hex_part) != 4 or not all(c in _HEX_DIGITS for c in hex_part):
        raise RegistryLoadError(f"line {line_no}: malformed '\\uXXXX' escape")
    return int(hex_part, 16), bs_index + 6


def _decode_quoted(raw: str, line_no: int) -> str:
    """Decode a double-quoted scalar, applying the fixed escape table.

    The supported escapes inside double quotes are ``\\\\``, ``\\"``, ``\\n``,
    ``\\t``, and ``\\uXXXX`` (a 16-bit code unit; adjacent high/low surrogate
    escapes are combined into a single astral character). The 👉 emoji and any
    other UTF-8 character may also appear literally between the quotes. Text
    after the closing quote is permitted only if it is blank or a ``#`` comment.

    Args:
        raw: Text beginning with the opening double quote.
        line_no: 1-based source line number, used in error messages.

    Returns:
        The decoded scalar value.

    Raises:
        RegistryLoadError: If the quote is unterminated, an escape is invalid,
            or unexpected (non-comment) text follows the closing quote.
    """
    if not raw.startswith('"'):
        raise RegistryLoadError(f"line {line_no}: expected a double-quoted value")

    out: list[str] = []
    i = 1
    n = len(raw)
    closed_at = -1
    while i < n:
        char = raw[i]
        if char == '"':
            closed_at = i
            break
        if char != "\\":
            out.append(char)
            i += 1
            continue
        if i + 1 >= n:
            raise RegistryLoadError(f"line {line_no}: dangling escape in value")
        nxt = raw[i + 1]
        if nxt == "\\":
            out.append("\\")
            i += 2
        elif nxt == '"':
            out.append('"')
            i += 2
        elif nxt == "n":
            out.append("\n")
            i += 2
        elif nxt == "t":
            out.append("\t")
            i += 2
        elif nxt == "u":
            code_unit, j = _decode_unicode_escape(raw, i, line_no)
            if 0xD800 <= code_unit <= 0xDBFF and raw[j : j + 2] == "\\u":
                low, k = _decode_unicode_escape(raw, j, line_no)
                if 0xDC00 <= low <= 0xDFFF:
                    combined = 0x10000 + ((code_unit - 0xD800) << 10) + (low - 0xDC00)
                    out.append(chr(combined))
                    i = k
                else:
                    out.append(chr(code_unit))
                    i = j
            else:
                out.append(chr(code_unit))
                i = j
        else:
            raise RegistryLoadError(f"line {line_no}: unsupported escape '\\{nxt}'")

    if closed_at == -1:
        raise RegistryLoadError(f"line {line_no}: unterminated double-quoted value")

    trailing = raw[closed_at + 1 :].strip()
    if trailing and not trailing.startswith("#"):
        raise RegistryLoadError(f"line {line_no}: unexpected text after quoted value")
    return "".join(out)


def _parse_value(raw: str, line_no: int) -> str | bool:
    """Parse a scalar value: a double-quoted string or a bare boolean.

    Args:
        raw: The raw text to the right of a ``key:`` separator (already
            left-stripped of leading whitespace).
        line_no: 1-based source line number, used in error messages.

    Returns:
        The decoded string, or ``True``/``False`` for a bare boolean.

    Raises:
        RegistryLoadError: If the value is neither a quoted string nor a
            boolean (unquoted scalars are not part of the subset).
    """
    if raw.startswith('"'):
        return _decode_quoted(raw, line_no)
    token = raw.split("#", 1)[0].strip()
    if token == "true":
        return True
    if token == "false":
        return False
    raise RegistryLoadError(
        f"line {line_no}: value must be double-quoted or a boolean"
    )


def _split_key_value(segment: str, line_no: int) -> tuple[str, str | bool | None]:
    """Split a ``key: value`` mapping entry.

    The key is a bare identifier, so the first colon separates it from the
    value. A value containing a colon is safe because every value is
    double-quoted. A trailing colon with no value denotes a nested block.

    Args:
        segment: The mapping entry text (no leading indentation or dash).
        line_no: 1-based source line number, used in error messages.

    Returns:
        A tuple of ``(key, value)`` where ``value`` is ``None`` when the entry
        opens a nested block sequence.

    Raises:
        RegistryLoadError: If no colon is present or the key is empty.
    """
    if ":" not in segment:
        raise RegistryLoadError(f"line {line_no}: expected a 'key: value' entry")
    key, _, rest = segment.partition(":")
    key = key.strip()
    if not key:
        raise RegistryLoadError(f"line {line_no}: empty mapping key")
    rest = rest.strip()
    if rest == "":
        return key, None
    return key, _parse_value(rest, line_no)


def _dash_body(stripped: str) -> str:
    """Return the content of a block-sequence item after its ``-`` marker."""
    return stripped[1:].strip()


def load_registry(path: Path) -> list[dict]:
    """Load and parse the registry's constrained YAML subset.

    The accepted subset is a single top-level ``rules:`` block sequence whose
    items are mappings. Each rule mapping holds double-quoted scalar fields
    (``id``, ``rule``, ``category``, ...), an optional bare boolean
    ``static_checkable``, an ``enforced_by`` block sequence of scalars, and an
    ``assertions`` block sequence of mappings. Indentation is two spaces per
    level, comments (``#``) and blank lines are ignored, and assertion
    ``value``/``pattern`` scalars are escape-decoded per the fixed escape table.

    Args:
        path: Path to the ``governance-rules.yaml`` registry file.

    Returns:
        The list of raw rule mappings (the value of the top-level ``rules``
        key). Schema validation of these mappings happens separately.

    Raises:
        RegistryLoadError: If the file is missing, unreadable, or not parseable
            (unterminated quote, bad indentation, or a non-``rules`` top key).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RegistryLoadError(f"cannot read registry '{path}': {exc}") from exc

    rules: list[dict] = []
    seen_rules_key = False
    current_rule: dict | None = None
    current_list_key: str | None = None
    current_assertion: dict | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        is_seq = stripped == "-" or stripped.startswith("- ")

        if indent == 0:
            key, value = _split_key_value(stripped, line_no)
            if key != "rules" or value is not None:
                raise RegistryLoadError(
                    f"line {line_no}: top-level key must be 'rules:'"
                )
            if seen_rules_key:
                raise RegistryLoadError(
                    f"line {line_no}: duplicate top-level 'rules:' key"
                )
            seen_rules_key = True
            current_rule = None
            current_list_key = None
            current_assertion = None
            continue

        if not seen_rules_key:
            raise RegistryLoadError(
                f"line {line_no}: content before top-level 'rules:' key"
            )

        if indent == _RULE_DASH_INDENT and is_seq:
            current_rule = {}
            rules.append(current_rule)
            current_assertion = None
            key, value = _split_key_value(_dash_body(stripped), line_no)
            if value is None:
                current_list_key = key
                current_rule[key] = []
            else:
                current_list_key = None
                current_rule[key] = value
        elif indent == _RULE_KEY_INDENT and not is_seq:
            if current_rule is None:
                raise RegistryLoadError(
                    f"line {line_no}: rule field outside of any rule item"
                )
            current_assertion = None
            key, value = _split_key_value(stripped, line_no)
            if value is None:
                current_list_key = key
                current_rule[key] = []
            else:
                current_list_key = None
                current_rule[key] = value
        elif indent == _NESTED_SEQ_INDENT and is_seq:
            if current_rule is None or current_list_key is None:
                raise RegistryLoadError(
                    f"line {line_no}: list item outside of a block sequence"
                )
            segment = _dash_body(stripped)
            target = current_rule[current_list_key]
            if current_list_key == "assertions":
                if segment.startswith('"'):
                    raise RegistryLoadError(
                        f"line {line_no}: assertion item must be a mapping"
                    )
                current_assertion = {}
                target.append(current_assertion)
                key, value = _split_key_value(segment, line_no)
                if value is None:
                    raise RegistryLoadError(
                        f"line {line_no}: assertion field '{key}' needs a value"
                    )
                current_assertion[key] = value
            else:
                if not segment.startswith('"'):
                    raise RegistryLoadError(
                        f"line {line_no}: '{current_list_key}' item must be a "
                        "double-quoted scalar"
                    )
                target.append(_decode_quoted(segment, line_no))
        elif indent == _ASSERTION_KEY_INDENT and not is_seq:
            if current_assertion is None:
                raise RegistryLoadError(
                    f"line {line_no}: assertion field outside of an assertion"
                )
            key, value = _split_key_value(stripped, line_no)
            if value is None:
                raise RegistryLoadError(
                    f"line {line_no}: assertion field '{key}' needs a value"
                )
            current_assertion[key] = value
        else:
            raise RegistryLoadError(
                f"line {line_no}: unexpected indentation or structure"
            )

    if not seen_rules_key:
        raise RegistryLoadError("registry has no top-level 'rules:' key")

    return rules


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

# The seven supported assertion types mapped to the parameters each one
# requires. The keys double as the set of supported types (anything outside
# this mapping is an unsupported assertion type). The values are the parameter
# names that MUST be present for an assertion of that type to be well-formed.
SUPPORTED_ASSERTION_TYPES: dict[str, tuple[str, ...]] = {
    "substring_present": ("file", "value"),
    "substring_absent": ("file", "value"),
    "regex_present": ("file", "pattern"),
    "regex_absent": ("file", "pattern"),
    "file_exists": ("file",),
    "hook_field_equals": ("file", "key_path", "value"),
    "yaml_key_present": ("file", "key_path"),
}

# Required Rule Entry fields. `id`, `rule`, and `category` are scalar strings;
# `enforced_by` and `assertions` are non-empty lists (with the documented
# exception that `assertions` may be empty for behavioral-only rules).
_REQUIRED_SCALAR_FIELDS = ("id", "rule", "category")


def _raw_id(raw: dict) -> str:
    """Return an entry's id for use in messages.

    Args:
        raw: The raw rule mapping produced by ``load_registry``.

    Returns:
        The ``id`` value when it is a string, otherwise an empty string so a
        violation can still be reported for a malformed or id-less entry.
    """
    candidate = raw.get("id")
    return candidate if isinstance(candidate, str) else ""


def _build_assertion(raw_assertion: dict) -> Assertion:
    """Build an :class:`Assertion` from a raw assertion mapping.

    Unset parameters default to ``None`` so the resulting dataclass mirrors the
    fields actually present in the registry (and round-trips with the renderer
    used by the property tests).

    Args:
        raw_assertion: A single raw assertion mapping.

    Returns:
        The constructed :class:`Assertion`.
    """
    return Assertion(
        type=raw_assertion.get("type"),
        file=raw_assertion.get("file"),
        value=raw_assertion.get("value"),
        pattern=raw_assertion.get("pattern"),
        key_path=raw_assertion.get("key_path"),
    )


def _validate_entry(raw: dict) -> tuple[list[Violation], RuleEntry | None]:
    """Validate a single raw rule mapping's schema.

    Checks the required fields, the behavioral-only assertions exception, and
    that every assertion carries the parameters its type requires. A
    well-formed entry is returned as a :class:`RuleEntry`; otherwise the entry
    is dropped and only its violations are returned.

    Args:
        raw: The raw rule mapping to validate.

    Returns:
        A tuple of ``(violations, entry)`` where ``entry`` is ``None`` when the
        mapping has at least one schema violation.
    """
    violations: list[Violation] = []
    rule_id = _raw_id(raw)

    for field in _REQUIRED_SCALAR_FIELDS:
        value = raw.get(field)
        if not (isinstance(value, str) and value):
            violations.append(
                Violation(
                    rule_id=rule_id,
                    kind="schema",
                    detail=f"missing or empty required field: '{field}'",
                )
            )

    enforced_by = raw.get("enforced_by")
    if not (isinstance(enforced_by, list) and enforced_by):
        violations.append(
            Violation(
                rule_id=rule_id,
                kind="schema",
                detail="missing or empty required field: 'enforced_by'",
            )
        )

    static_checkable = raw.get("static_checkable", True)
    if not isinstance(static_checkable, bool):
        static_checkable = bool(static_checkable)

    assertions = raw.get("assertions")
    has_assertions = isinstance(assertions, list) and bool(assertions)
    if not has_assertions and static_checkable:
        # `assertions` may be empty ONLY for behavioral-only rules.
        violations.append(
            Violation(
                rule_id=rule_id,
                kind="schema",
                detail="missing or empty required field: 'assertions'",
            )
        )

    built_assertions: list[Assertion] = []
    if isinstance(assertions, list):
        for raw_assertion in assertions:
            if not isinstance(raw_assertion, dict):
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        kind="schema",
                        detail="malformed assertion: expected a mapping",
                    )
                )
                continue
            built = _build_assertion(raw_assertion)
            # Type is guaranteed supported here: unsupported types are caught
            # in the precedence pass before any entry is validated.
            required = SUPPORTED_ASSERTION_TYPES.get(built.type or "", ())
            missing = [param for param in required if getattr(built, param) is None]
            if missing:
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        kind="schema",
                        detail=(
                            f"malformed assertion '{built.type}': missing "
                            f"required parameter(s): {', '.join(missing)}"
                        ),
                        assertion=built,
                        file=built.file,
                    )
                )
            built_assertions.append(built)

    if violations:
        return violations, None

    entry = RuleEntry(
        id=raw["id"],
        rule=raw["rule"],
        category=raw["category"],
        enforced_by=list(enforced_by),
        assertions=built_assertions,
        static_checkable=static_checkable,
    )
    return violations, entry


def validate_schema(
    raw_entries: list[dict],
) -> tuple[list[RuleEntry], list[Violation]]:
    """Validate the registry schema and build typed Rule Entries.

    Converts raw rule mappings into :class:`RuleEntry`/:class:`Assertion`
    dataclasses while collecting schema :class:`Violation`s. Schema problems are
    collected here and halt the run before any content evaluation (the caller
    exits with status code 1 when violations are present).

    The checks, in order:

    1. **Unsupported assertion type (precedence + halt).** If any assertion's
       ``type`` is not in :data:`SUPPORTED_ASSERTION_TYPES`, the
       unsupported-type violations are reported and the function returns
       immediately, before any other schema check or content evaluation
       (Requirement 3.9).
    2. **Required fields.** Each entry must have a non-empty ``id``, ``rule``,
       ``category``, ``enforced_by`` list, and ``assertions`` list. An empty
       ``enforced_by`` or ``assertions`` counts as missing, except that
       ``assertions`` may be empty when ``static_checkable`` is ``false``
       (Requirements 2.1, 2.3, 2.4, 2.5, 2.6, 2.8).
    3. **Unique ids.** A non-empty ``id`` repeated across entries yields a
       duplicate-id violation (Requirements 2.2, 2.9).
    4. **Malformed assertions.** A supported-type assertion missing a parameter
       its type requires yields a malformed-assertion violation
       (Requirement 3.10).

    Args:
        raw_entries: The raw rule mappings returned by ``load_registry``.

    Returns:
        A tuple of ``(entries, violations)``. ``entries`` holds the
        well-formed :class:`RuleEntry` objects (empty when an unsupported
        assertion type halts validation). ``violations`` holds every schema
        violation found; an empty list means the registry schema is valid.
    """
    # Pass 1: unsupported assertion types take precedence and halt. Detect them
    # first and return before any other schema check or content evaluation.
    unsupported: list[Violation] = []
    for raw in raw_entries:
        assertions = raw.get("assertions")
        if not isinstance(assertions, list):
            continue
        for raw_assertion in assertions:
            if not isinstance(raw_assertion, dict):
                continue
            atype = raw_assertion.get("type")
            if atype not in SUPPORTED_ASSERTION_TYPES:
                unsupported.append(
                    Violation(
                        rule_id=_raw_id(raw),
                        kind="schema",
                        detail=f"unsupported assertion type: {atype!r}",
                        assertion=_build_assertion(raw_assertion),
                        file=raw_assertion.get("file"),
                    )
                )
    if unsupported:
        return [], unsupported

    # Pass 2: required fields, malformed assertions, and duplicate ids.
    entries: list[RuleEntry] = []
    violations: list[Violation] = []
    id_counts: dict[str, int] = {}
    for raw in raw_entries:
        entry_violations, entry = _validate_entry(raw)
        violations.extend(entry_violations)
        if entry is not None:
            entries.append(entry)
        raw_id = raw.get("id")
        if isinstance(raw_id, str) and raw_id:
            id_counts[raw_id] = id_counts.get(raw_id, 0) + 1
            if id_counts[raw_id] == 2:
                violations.append(
                    Violation(
                        rule_id=raw_id,
                        kind="schema",
                        detail=f"duplicate rule id: {raw_id!r}",
                    )
                )

    return entries, violations


# ---------------------------------------------------------------------------
# Assertion evaluation
# ---------------------------------------------------------------------------


def _content_violation(assertion: Assertion, detail: str) -> Violation:
    """Build a content :class:`Violation` for a failing assertion.

    The ``rule_id`` is left empty here; ``evaluate_assertion`` does not know
    the owning rule's id. The caller (``evaluate_rule``, task 6.1) enriches the
    violation with the rule id and context.

    Args:
        assertion: The assertion that failed (recorded on the violation).
        detail: Human-readable description of the cause.

    Returns:
        A content :class:`Violation` naming the assertion and its file.
    """
    return Violation(
        rule_id="",
        kind="content",
        detail=detail,
        assertion=assertion,
        file=assertion.file,
    )


def _traverse_dotted(data: object, segments: list[str]) -> tuple[bool, object]:
    """Walk a nested mapping by dotted-path segments.

    Args:
        data: The decoded JSON/mapping object to traverse.
        segments: The ordered key-path segments to follow.

    Returns:
        A tuple of ``(found, value)``. ``found`` is ``True`` only when every
        segment resolved through nested mappings; ``value`` is the terminal
        value when found, otherwise ``None``.
    """
    current = data
    for segment in segments:
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return False, None
    return True, current


def _line_key(stripped: str) -> str | None:
    """Extract the mapping key from a stripped YAML/frontmatter line.

    Args:
        stripped: A line with leading indentation already removed.

    Returns:
        The mapping key (with surrounding quotes removed), or ``None`` when the
        line is a block-sequence item or carries no ``key:`` separator.
    """
    if stripped.startswith("- ") or stripped == "-":
        return None
    if ":" not in stripped:
        return None
    key = stripped.split(":", 1)[0].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in ("'", '"'):
        key = key[1:-1]
    return key or None


def _scan_yaml_block(
    lines: list[str],
    start: int,
    end: int,
    parent_indent: int,
    segments: list[str],
) -> bool:
    """Check whether a dotted key path exists within an indentation block.

    Finds the first segment as a ``key:`` line whose indentation is deeper than
    ``parent_indent``, then recurses into that key's child block (the more
    deeply indented lines that follow) to resolve the remaining segments. A
    line that dedents to ``parent_indent`` or shallower ends the current block.

    Args:
        lines: All source lines of the file.
        start: Index of the first line to scan (inclusive).
        end: Index just past the last line to scan (exclusive).
        parent_indent: Indentation of the enclosing block (``-1`` at top level).
        segments: The remaining key-path segments to resolve.

    Returns:
        ``True`` if the full key path resolves within the block, else ``False``.
    """
    head = segments[0]
    rest = segments[1:]
    i = start
    while i < end:
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(stripped)
        if indent <= parent_indent:
            return False
        if _line_key(stripped) == head:
            if not rest:
                return True
            return _scan_yaml_block(lines, i + 1, end, indent, rest)
        i += 1
    return False


def _yaml_or_json_key_present(text: str, segments: list[str]) -> bool:
    """Check dotted-key existence in a JSON or simple-YAML document.

    JSON content is parsed with :func:`json.loads` and traversed as nested
    mappings. Anything that is not valid JSON (for example Markdown with YAML
    frontmatter, or a ``*.yaml`` config) falls back to a line-based,
    indentation-aware existence scan suitable for flat and frontmatter keys.

    Args:
        text: The full file text.
        segments: The dotted key-path segments to resolve.

    Returns:
        ``True`` if the key path exists, else ``False``.
    """
    if not segments:
        return False
    try:
        data = json.loads(text)
    except ValueError:
        lines = text.splitlines()
        return _scan_yaml_block(lines, 0, len(lines), -1, segments)
    if isinstance(data, dict):
        found, _ = _traverse_dotted(data, segments)
        return found
    lines = text.splitlines()
    return _scan_yaml_block(lines, 0, len(lines), -1, segments)


def _segments(key_path: str | None) -> list[str]:
    """Split a dotted ``key_path`` into segments.

    Args:
        key_path: The dotted key path, or ``None``.

    Returns:
        The list of non-empty segments (empty when ``key_path`` is falsy).
    """
    if not key_path:
        return []
    return key_path.split(".")


def evaluate_assertion(assertion: Assertion, repo_root: Path) -> Violation | None:
    """Evaluate one assertion against the repository filesystem.

    Dispatches on ``assertion.type`` across the seven supported types. Every
    ``file`` is resolved relative to ``repo_root``. For every type except
    ``file_exists``, a non-existent target file fails the assertion and names
    the missing file as the cause (the missing-file rule, Requirement 4.5).
    Internal evaluation errors — an invalid regex raising :class:`re.error` or
    malformed JSON during ``hook_field_equals`` — are caught and converted into
    a content :class:`Violation` rather than allowed to crash the run.

    Args:
        assertion: The schema-valid assertion to evaluate.
        repo_root: Base directory for resolving the assertion's ``file`` path.

    Returns:
        ``None`` when the assertion holds, otherwise a content
        :class:`Violation` describing the cause. The violation's ``rule_id`` is
        left empty; the calling ``evaluate_rule`` attaches the owning rule's id.
    """
    atype = assertion.type
    file_rel = assertion.file
    target = repo_root / file_rel if file_rel else None

    # file_exists is the only type tolerant of a missing target file.
    if atype == "file_exists":
        if target is not None and target.is_file():
            return None
        return _content_violation(assertion, f"file does not exist: {file_rel}")

    # Missing-file rule (Req 4.5): every other type fails on a missing file.
    if target is None or not target.is_file():
        return _content_violation(
            assertion, f"{atype}: target file does not exist: {file_rel}"
        )

    # hook_field_equals reads JSON directly; the remaining types need the text.
    if atype == "hook_field_equals":
        return _evaluate_hook_field_equals(assertion, target, file_rel)

    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return _content_violation(assertion, f"could not read {file_rel}: {exc}")

    if atype == "substring_present":
        if assertion.value in text:
            return None
        return _content_violation(
            assertion, f"substring not found in {file_rel}: {assertion.value!r}"
        )
    if atype == "substring_absent":
        if assertion.value not in text:
            return None
        return _content_violation(
            assertion,
            f"substring unexpectedly present in {file_rel}: {assertion.value!r}",
        )
    if atype in ("regex_present", "regex_absent"):
        return _evaluate_regex(assertion, text, file_rel)
    if atype == "yaml_key_present":
        if _yaml_or_json_key_present(text, _segments(assertion.key_path)):
            return None
        return _content_violation(
            assertion,
            f"key path {assertion.key_path!r} not present in {file_rel}",
        )

    # Unreachable for schema-valid assertions (types are validated upstream).
    return _content_violation(assertion, f"unsupported assertion type: {atype!r}")


def _evaluate_regex(
    assertion: Assertion, text: str, file_rel: str | None
) -> Violation | None:
    """Evaluate a ``regex_present`` / ``regex_absent`` assertion.

    Args:
        assertion: The regex assertion being evaluated.
        text: The target file's text.
        file_rel: The repo-root-relative file path (for messages).

    Returns:
        ``None`` when the assertion holds, otherwise a content
        :class:`Violation` (including for an invalid pattern raising
        :class:`re.error`).
    """
    try:
        matched = re.search(assertion.pattern or "", text) is not None
    except re.error as exc:
        return _content_violation(
            assertion, f"invalid regex {assertion.pattern!r} for {file_rel}: {exc}"
        )
    if assertion.type == "regex_present":
        if matched:
            return None
        return _content_violation(
            assertion, f"regex did not match in {file_rel}: {assertion.pattern!r}"
        )
    # regex_absent
    if not matched:
        return None
    return _content_violation(
        assertion, f"regex unexpectedly matched in {file_rel}: {assertion.pattern!r}"
    )


def _evaluate_hook_field_equals(
    assertion: Assertion, target: Path, file_rel: str | None
) -> Violation | None:
    """Evaluate a ``hook_field_equals`` assertion against a JSON file.

    Loads the file as JSON, traverses nested mappings by the dotted
    ``key_path``, stringifies the terminal value with ``str()``, and compares it
    to ``assertion.value``. A malformed JSON file is caught and reported as a
    content violation rather than crashing.

    Args:
        assertion: The ``hook_field_equals`` assertion being evaluated.
        target: The resolved path to the JSON file.
        file_rel: The repo-root-relative file path (for messages).

    Returns:
        ``None`` when the stringified value matches, otherwise a content
        :class:`Violation` (malformed JSON, missing key path, or mismatch).
    """
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        return _content_violation(assertion, f"could not read {file_rel}: {exc}")
    except ValueError as exc:
        return _content_violation(
            assertion, f"could not parse JSON in {file_rel}: {exc}"
        )

    found, value = _traverse_dotted(data, _segments(assertion.key_path))
    if not found:
        return _content_violation(
            assertion, f"key path {assertion.key_path!r} not found in {file_rel}"
        )
    if str(value) == assertion.value:
        return None
    return _content_violation(
        assertion,
        f"key path {assertion.key_path!r} in {file_rel} is {str(value)!r}, "
        f"expected {assertion.value!r}",
    )


# ---------------------------------------------------------------------------
# Rule evaluation and run orchestration
# ---------------------------------------------------------------------------


def evaluate_rule(entry: RuleEntry, repo_root: Path) -> list[Violation]:
    """Evaluate every assertion of one rule, enriched with the rule id.

    Behavioral-only entries (``static_checkable`` is ``False``) carry no static
    assertions and are skipped without failing (Requirements 8.2, 8.4) — they
    return an empty list. For a statically-checkable rule, every assertion is
    evaluated (collect-all, never stopping at the first failure). Because
    ``evaluate_assertion`` returns content violations with an empty
    ``rule_id``, each failing violation is re-stamped here with this rule's id
    so reporting can name the failing rule (Requirement 5.1).

    Args:
        entry: The rule entry to evaluate.
        repo_root: Base directory for resolving assertion ``file`` paths.

    Returns:
        The list of content violations for this rule (empty when every
        assertion holds or the rule is behavioral-only).
    """
    if not entry.static_checkable:
        return []
    violations: list[Violation] = []
    for assertion in entry.assertions:
        result = evaluate_assertion(assertion, repo_root)
        if result is not None:
            # Violation is frozen; build an enriched copy carrying the rule id.
            violations.append(replace(result, rule_id=entry.id))
    return violations


def run(registry_path: Path, repo_root: Path) -> RunResult:
    """Orchestrate the full validation run: load -> schema -> evaluate-all.

    The three error classes (Error Handling table in the design) are handled as
    follows:

    * **Load error** — a missing, unreadable, or unparseable registry raises
      :class:`RegistryLoadError`. It is caught and reported as a single
      ``kind="load"`` violation (a distinct, clearer label than ``"schema"`` so
      reporting can render the load failure on its own). The run halts before
      schema validation with ``completed=False`` and ``exit_code=1``
      (Requirement 4.7).
    * **Schema error (halt)** — when ``validate_schema`` reports any violation
      (missing/empty field, duplicate id, unsupported or malformed assertion),
      content evaluation never runs. The schema violations are returned with
      ``rules_checked=0``, ``completed=False`` and ``exit_code=1``
      (Requirements 2.8, 2.9, 3.9, 3.10).
    * **Content evaluation (collect-all)** — on a structurally valid registry,
      every assertion of every statically-checkable rule is evaluated and all
      content violations are collected (never stopping at the first failure,
      Requirement 4.6). Behavioral-only entries are skipped and not counted.
      The run is ``completed=True``; ``exit_code`` is ``0`` only when no
      violation was found, else ``1`` (Requirements 4.2, 4.3, 4.4, 4.4a).

    Args:
        registry_path: Path to the ``governance-rules.yaml`` registry file.
        repo_root: Base directory for resolving ``enforced_by`` and assertion
            ``file`` paths.

    Returns:
        A :class:`RunResult` whose ``exit_code`` is ``0`` iff the registry is
        structurally valid AND every evaluated assertion holds AND no internal
        error occurred, and ``1`` in every other case. ``completed`` is ``True``
        only when evaluation ran to completion (a load or schema halt leaves it
        ``False``); ``rules_checked`` counts the statically-checkable rule
        entries evaluated.
    """
    # Load: a load error halts before schema validation (no completion).
    try:
        raw_entries = load_registry(registry_path)
    except RegistryLoadError as exc:
        load_violation = Violation(
            rule_id="",
            kind="load",
            detail=f"could not load registry '{registry_path}': {exc}",
            file=str(registry_path),
        )
        return RunResult(
            rules_checked=0,
            violations=[load_violation],
            completed=False,
            exit_code=1,
        )

    # Schema: any schema violation halts before content evaluation.
    entries, schema_violations = validate_schema(raw_entries)
    if schema_violations:
        return RunResult(
            rules_checked=0,
            violations=schema_violations,
            completed=False,
            exit_code=1,
        )

    # Content evaluation: collect-all across every statically-checkable rule.
    violations: list[Violation] = []
    rules_checked = 0
    for entry in entries:
        if not entry.static_checkable:
            continue
        rules_checked += 1
        violations.extend(evaluate_rule(entry, repo_root))

    return RunResult(
        rules_checked=rules_checked,
        violations=violations,
        completed=True,
        exit_code=0 if not violations else 1,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

# The assertion parameters rendered in a violation message, in a stable order.
_ASSERTION_PARAMS = ("file", "value", "pattern", "key_path")


def _format_assertion(assertion: Assertion) -> str:
    """Render an assertion's type and parameters for a violation message.

    Only the parameters that are set (non-``None``) are included, in a stable
    order, so the message names the failing assertion's type alongside the
    file, value, pattern, and/or key path that define it (Requirement 5.2).

    Args:
        assertion: The failing assertion to describe.

    Returns:
        A single-line description such as
        ``type=substring_present file="a.md" value="x"``.
    """
    parts = [f"type={assertion.type}"]
    for param in _ASSERTION_PARAMS:
        value = getattr(assertion, param)
        if value is not None:
            parts.append(f"{param}={value!r}")
    return " ".join(parts)


def _format_violation(violation: Violation) -> str:
    """Render one violation as a distinct, human-readable block.

    Content violations include the failing rule id, the assertion's type and
    parameters, and the file path involved (Requirements 5.1, 5.2, 5.3). Schema
    and load violations render their detail (and rule id when present) without
    an assertion line.

    Args:
        violation: The violation to render.

    Returns:
        The formatted multi-line text for the violation (no trailing newline).
    """
    label = {"content": "CONTENT", "schema": "SCHEMA", "load": "LOAD"}.get(
        violation.kind, violation.kind.upper()
    )
    header = f"[{label}]"
    if violation.rule_id:
        header += f" rule '{violation.rule_id}'"
    lines = [f"{header}: {violation.detail}"]
    if violation.assertion is not None:
        lines.append(f"  assertion: {_format_assertion(violation.assertion)}")
    if violation.file:
        lines.append(f"  file: {violation.file}")
    return "\n".join(lines)


def report(
    result: RunResult,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> None:
    """Route a run's outcome to the appropriate output streams.

    Stream discipline (Requirement 5.6): every violation's detail is written to
    ``stderr``, each as a separate entry (Requirement 5.4). Success messages and
    the completion counts are written to ``stdout``. The completion counts
    ("Rule Entries checked" / "Violations found") are emitted ONLY after a full
    evaluation pass — that is, when ``result.completed`` is ``True`` — and are
    suppressed on a load or schema halt (Requirement 5.5).

    Args:
        result: The aggregate outcome produced by :func:`run`.
        stdout: Stream for success and completion counts (defaults to
            :data:`sys.stdout`).
        stderr: Stream for violation details (defaults to :data:`sys.stderr`).
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    # Violations always go to stderr, each rendered as its own entry.
    for violation in result.violations:
        print(_format_violation(violation), file=err)

    if result.exit_code == 0:
        # Success implies a full evaluation pass with no violations.
        print("Governance rule conformance: PASS", file=out)

    # Completion counts are emitted only after a full evaluation pass; a
    # load/schema halt (completed=False) suppresses them.
    if result.completed:
        print(f"Rule Entries checked: {result.rules_checked}", file=out)
        print(f"Violations found: {len(result.violations)}", file=out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run governance-rule conformance validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Process exit code: 0 on success, 1 on any error or violation.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate that each governing rule in governance-rules.yaml is "
            "wired to its enforcement point(s)."
        ),
    )
    parser.add_argument(
        "--registry",
        default=None,
        help=(
            "Path to governance-rules.yaml "
            "(default: <repo_root>/senzing-bootcamp/config/governance-rules.yaml)."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Base directory for resolving enforced_by and assertion file paths "
            "(default: repository root inferred from script location)."
        ),
    )
    args = parser.parse_args(argv)

    # Infer the repository root from the script location:
    # <repo_root>/senzing-bootcamp/scripts/validate_governance_rules.py
    repo_root = (
        Path(args.repo_root)
        if args.repo_root
        else Path(__file__).resolve().parent.parent.parent
    )
    registry_path = (
        Path(args.registry)
        if args.registry
        else repo_root / "senzing-bootcamp" / "config" / "governance-rules.yaml"
    )

    # Orchestrate: load -> schema -> evaluate-all, then route reporting to the
    # standard streams and return the canonical exit code (Requirement 4.8).
    result = run(registry_path, repo_root)
    report(result)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
