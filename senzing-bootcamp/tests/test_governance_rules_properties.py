"""Property-based tests for validate_governance_rules.py using Hypothesis.

Feature: governance-rule-conformance

This module hosts the shared Hypothesis strategies (``st_assertion``,
``st_rule_entry``, ``st_registry``) and the YAML-subset renderer used by every
governance-rule property test, plus Property 1 (parser round-trip).
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_governance_rules import (  # noqa: E402
    SUPPORTED_ASSERTION_TYPES,
    Assertion,
    RuleEntry,
    evaluate_assertion,
    load_registry,
    report,
    run,
    validate_schema,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# The seven supported assertion types mapped to the parameters each one
# requires (the documented interface from design.md "Components and
# Interfaces"). Only the required params are emitted for a generated assertion;
# every other param stays ``None`` so the dataclass round-trips exactly.
_ASSERTION_PARAMS: dict[str, tuple[str, ...]] = {
    "substring_present": ("file", "value"),
    "substring_absent": ("file", "value"),
    "regex_present": ("file", "pattern"),
    "regex_absent": ("file", "pattern"),
    "file_exists": ("file",),
    "hook_field_equals": ("file", "key_path", "value"),
    "yaml_key_present": ("file", "key_path"),
}

# Characters the registry's escape table must survive: a backslash (regex
# escapes), a double quote, a newline, a tab, and the 👉 pointer emoji.
_SPECIAL_CHARS = ["\\", '"', "\n", "\t", "👉"]


# ---------------------------------------------------------------------------
# Shared Hypothesis strategies
# ---------------------------------------------------------------------------


def st_scalar_text(min_size: int = 0) -> st.SearchStrategy[str]:
    """Generate scalar text the registry parser must round-trip exactly.

    The alphabet is printable ASCII (which already includes ``\\`` and ``"``)
    plus the explicit special characters (newline, tab, and the 👉 emoji). It
    deliberately excludes other control characters and Unicode line separators
    that ``str.splitlines`` would split on, since those are outside the parser's
    escape table.

    Args:
        min_size: Minimum length of the generated string.

    Returns:
        A Hypothesis strategy producing scalar strings.
    """
    return st.text(
        alphabet=st.one_of(
            st.characters(min_codepoint=0x20, max_codepoint=0x7E),
            st.sampled_from(_SPECIAL_CHARS),
        ),
        min_size=min_size,
        max_size=30,
    )


def st_rule_id() -> st.SearchStrategy[str]:
    """Generate a non-empty, identifier-style rule id."""
    return st.from_regex(r"[a-z][a-z0-9_-]{0,12}", fullmatch=True)


@st.composite
def st_assertion(draw: st.DrawFn) -> Assertion:
    """Generate a schema-valid :class:`Assertion`.

    A supported ``type`` is chosen and only the parameters that type requires
    are filled; every other parameter is left ``None``. ``value`` and
    ``pattern`` may carry backslashes, double quotes, newlines, and the 👉
    emoji so the parser's escape table is exercised.

    Returns:
        A generated :class:`Assertion`.
    """
    atype = draw(st.sampled_from(sorted(_ASSERTION_PARAMS)))
    kwargs: dict[str, str] = {}
    for param in _ASSERTION_PARAMS[atype]:
        if param in ("value", "pattern"):
            kwargs[param] = draw(st_scalar_text(min_size=0))
        else:
            kwargs[param] = draw(st_scalar_text(min_size=1))
    return Assertion(type=atype, **kwargs)


@st.composite
def st_rule_entry(draw: st.DrawFn) -> RuleEntry:
    """Generate a schema-valid :class:`RuleEntry`.

    Required fields are non-empty. Statically-checkable entries carry at least
    one assertion; behavioral-only entries (``static_checkable=False``) carry no
    assertions, matching the documented schema rules.

    Returns:
        A generated :class:`RuleEntry`.
    """
    static_checkable = draw(st.booleans())
    if static_checkable:
        assertions = draw(st.lists(st_assertion(), min_size=1, max_size=4))
    else:
        assertions = []
    return RuleEntry(
        id=draw(st_rule_id()),
        rule=draw(st_scalar_text(min_size=1)),
        category=draw(st_scalar_text(min_size=1)),
        enforced_by=draw(
            st.lists(st_scalar_text(min_size=1), min_size=1, max_size=3)
        ),
        assertions=assertions,
        static_checkable=static_checkable,
    )


def st_registry() -> st.SearchStrategy[list[RuleEntry]]:
    """Generate a list of Rule Entries with ids unique within the registry."""
    return st.lists(
        st_rule_entry(),
        min_size=1,
        max_size=5,
        unique_by=lambda entry: entry.id,
    )


# ---------------------------------------------------------------------------
# YAML-subset renderer
# ---------------------------------------------------------------------------


def _escape_scalar(text: str) -> str:
    """Escape a string to match the parser's fixed escape table.

    ``\\`` -> ``\\\\``, ``"`` -> ``\\"``, newline -> ``\\n``, tab -> ``\\t``.
    The 👉 emoji and other characters are emitted literally (the file is UTF-8).
    """
    out: list[str] = []
    for char in text:
        if char == "\\":
            out.append("\\\\")
        elif char == '"':
            out.append('\\"')
        elif char == "\n":
            out.append("\\n")
        elif char == "\t":
            out.append("\\t")
        else:
            out.append(char)
    return "".join(out)


def _quote(text: str) -> str:
    """Render a string as a double-quoted, escape-encoded scalar."""
    return f'"{_escape_scalar(text)}"'


def render_registry(entries: list[RuleEntry]) -> str:
    """Render Rule Entries to the constrained YAML subset ``load_registry`` reads.

    Emits a top-level ``rules:`` block sequence with two-space indentation,
    double-quoted scalar values, an ``enforced_by`` block sequence of scalars,
    and an ``assertions`` block sequence of mappings. ``static_checkable`` is
    emitted as a bare boolean only for behavioral-only entries.

    Args:
        entries: The Rule Entries to render.

    Returns:
        The registry text (newline-terminated).
    """
    lines: list[str] = ["rules:"]
    for entry in entries:
        lines.append(f"  - id: {_quote(entry.id)}")
        lines.append(f"    rule: {_quote(entry.rule)}")
        lines.append(f"    category: {_quote(entry.category)}")
        if not entry.static_checkable:
            lines.append("    static_checkable: false")
        lines.append("    enforced_by:")
        for point in entry.enforced_by:
            lines.append(f"      - {_quote(point)}")
        if entry.assertions:
            lines.append("    assertions:")
            for assertion in entry.assertions:
                lines.append(f"      - type: {_quote(assertion.type)}")
                for param in ("file", "value", "pattern", "key_path"):
                    pval = getattr(assertion, param)
                    if pval is not None:
                        lines.append(f"        {param}: {_quote(pval)}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Schema-violation helpers and strategies
# ---------------------------------------------------------------------------

# Required Rule Entry fields per Requirement 2.1 (id/rule/category are scalars,
# enforced_by/assertions are non-empty lists).
_REQUIRED_FIELDS = ("id", "rule", "category", "enforced_by", "assertions")
_SCALAR_FIELDS = ("id", "rule", "category")


def _assertion_to_raw(assertion: Assertion) -> dict:
    """Convert an :class:`Assertion` to the raw mapping ``validate_schema`` reads.

    Only the parameters that are set (non-``None``) are emitted, mirroring what
    ``load_registry`` would produce for the rendered registry.
    """
    raw: dict = {"type": assertion.type}
    for param in ("file", "value", "pattern", "key_path"):
        pval = getattr(assertion, param)
        if pval is not None:
            raw[param] = pval
    return raw


def _entry_to_raw(entry: RuleEntry) -> dict:
    """Convert a :class:`RuleEntry` to the raw mapping ``validate_schema`` reads.

    ``static_checkable`` is emitted only when ``False`` (the registry default is
    ``True``), matching ``render_registry`` and ``load_registry`` behavior.
    """
    raw: dict = {
        "id": entry.id,
        "rule": entry.rule,
        "category": entry.category,
        "enforced_by": list(entry.enforced_by),
        "assertions": [_assertion_to_raw(a) for a in entry.assertions],
    }
    if not entry.static_checkable:
        raw["static_checkable"] = False
    return raw


def st_unsupported_type() -> st.SearchStrategy[str]:
    """Generate an assertion type string outside the supported set."""
    return st.from_regex(r"[a-z][a-z_]{0,14}", fullmatch=True).filter(
        lambda t: t not in SUPPORTED_ASSERTION_TYPES
    )


@st.composite
def st_required_field_case(draw: st.DrawFn) -> tuple[dict, str | None]:
    """Generate a raw entry that is fully valid or has one required field broken.

    The base entry is forced statically-checkable with a non-empty ``assertions``
    list, so all five required fields are genuinely required (an empty
    ``assertions`` list then counts as a violation). With some probability one
    required field is "broken" — either removed or set to an empty value.

    Returns:
        A tuple ``(raw_entry, broken_field)`` where ``broken_field`` is ``None``
        when the entry is left fully valid, otherwise the name of the broken
        required field.
    """
    entry = draw(st_rule_entry())
    assertions = entry.assertions or [draw(st_assertion())]
    raw = _entry_to_raw(
        RuleEntry(
            id=entry.id,
            rule=entry.rule,
            category=entry.category,
            enforced_by=entry.enforced_by,
            assertions=assertions,
            static_checkable=True,
        )
    )
    broken_field = draw(st.sampled_from((None, *_REQUIRED_FIELDS)))
    if broken_field is None:
        return raw, None
    if draw(st.booleans()):
        raw.pop(broken_field, None)
    else:
        raw[broken_field] = "" if broken_field in _SCALAR_FIELDS else []
    return raw, broken_field


@st.composite
def st_entries_maybe_duplicate_ids(draw: st.DrawFn) -> list[dict]:
    """Generate raw entries whose ids may or may not collide.

    Entries start with ids unique within the list; with some probability one
    entry's id is overwritten with another's to introduce a duplicate.
    """
    entries = draw(
        st.lists(
            st_rule_entry(),
            min_size=1,
            max_size=4,
            unique_by=lambda entry: entry.id,
        )
    )
    raws = [_entry_to_raw(entry) for entry in entries]
    if len(raws) >= 2 and draw(st.booleans()):
        source = draw(st.integers(min_value=0, max_value=len(raws) - 1))
        targets = [k for k in range(len(raws)) if k != source]
        target = draw(st.sampled_from(targets))
        raws[target]["id"] = raws[source]["id"]
    return raws


@st.composite
def st_registry_with_unsupported_type(draw: st.DrawFn) -> list[dict]:
    """Generate raw entries with at least one unsupported assertion type.

    Other schema problems (a removed required field, a forced duplicate id) are
    interspersed with some probability, so the test can confirm the
    unsupported-type check takes precedence and halts before those are reached.
    """
    entries = draw(
        st.lists(
            st_rule_entry(),
            min_size=1,
            max_size=3,
            unique_by=lambda entry: entry.id,
        )
    )
    raws = [_entry_to_raw(entry) for entry in entries]
    target = draw(st.integers(min_value=0, max_value=len(raws) - 1))
    bad_assertion = {
        "type": draw(st_unsupported_type()),
        "file": draw(st_scalar_text(min_size=1)),
    }
    raws[target].setdefault("assertions", []).append(bad_assertion)
    if draw(st.booleans()):
        victim = draw(st.integers(min_value=0, max_value=len(raws) - 1))
        raws[victim].pop("rule", None)
    if len(raws) >= 2 and draw(st.booleans()):
        raws[1]["id"] = raws[0]["id"]
    return raws


@st.composite
def st_entry_with_malformed_assertion(draw: st.DrawFn) -> tuple[dict, str, str]:
    """Generate a raw entry containing one supported assertion missing a param.

    A supported assertion type is chosen, all but one of its required parameters
    are filled, and the dropped parameter name is returned alongside the entry.

    Returns:
        A tuple ``(raw_entry, assertion_type, dropped_param)``.
    """
    entry = draw(st_rule_entry())
    atype = draw(st.sampled_from(sorted(SUPPORTED_ASSERTION_TYPES)))
    required = SUPPORTED_ASSERTION_TYPES[atype]
    dropped = draw(st.sampled_from(required))
    bad_assertion: dict = {"type": atype}
    for param in required:
        if param != dropped:
            bad_assertion[param] = draw(st_scalar_text(min_size=1))
    raw = {
        "id": entry.id,
        "rule": entry.rule,
        "category": entry.category,
        "enforced_by": list(entry.enforced_by),
        "assertions": [bad_assertion],
    }
    return raw, atype, dropped


# ---------------------------------------------------------------------------
# Assertion-evaluator strategies and oracle helpers
# ---------------------------------------------------------------------------

# Curated, always-valid regex patterns. Property 5 is about *valid* regex
# agreement, so invalid patterns are deliberately excluded here. The mix yields
# both matching and non-matching cases against generated text.
_VALID_REGEX_PATTERNS = [
    "a",
    "to",
    "abc",
    "\\d",
    "\\d+",
    "[A-Z]",
    "[a-z]+",
    "\\s",
    "\\w+",
    "^",
    "$",
    ".",
    "x?",
    "\\\\",
]


def _oracle_traverse(data: object, segments: list[str]) -> tuple[bool, object]:
    """Oracle mirror of the validator's dotted-mapping traversal.

    Walks ``data`` segment by segment, requiring a mapping with the segment
    present at every step. Mirrors ``_traverse_dotted`` in the validator so the
    property tests can compare against an independent implementation.

    Args:
        data: The decoded mapping to traverse.
        segments: Ordered key-path segments to follow.

    Returns:
        A tuple ``(found, value)``; ``found`` is ``True`` only when every
        segment resolved through nested mappings.
    """
    current = data
    for segment in segments:
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return False, None
    return True, current


def st_json_key() -> st.SearchStrategy[str]:
    """Generate a mapping key with no dot (so it is a single path segment)."""
    return st.from_regex(r"[a-z][a-z0-9_]{0,6}", fullmatch=True)


def st_json_terminal() -> st.SearchStrategy[object]:
    """Generate a JSON scalar terminal whose ``str()`` is round-trip stable.

    Floats are excluded so the ``str(value)`` comparison the validator performs
    is deterministic across the json round-trip.
    """
    return st.one_of(
        st.text(
            alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),
            max_size=8,
        ),
        st.integers(min_value=-1000, max_value=1000),
        st.booleans(),
        st.none(),
    )


def _nest_linear(segments: list[str], terminal: object) -> dict:
    """Build a strictly linear nested mapping ending in ``terminal``."""
    node: object = terminal
    for segment in reversed(segments):
        node = {segment: node}
    return node  # type: ignore[return-value]


@st.composite
def st_text_and_substring(draw: st.DrawFn) -> tuple[str, str]:
    """Generate file text plus a candidate substring (present or arbitrary).

    With some probability the candidate is a real slice of the text (guaranteed
    present); otherwise it is arbitrary scalar text that may or may not occur.
    Both cases let the membership oracle decide the expected result.

    Returns:
        A tuple ``(text, value)``.
    """
    text = draw(st_scalar_text(min_size=0))
    if text and draw(st.booleans()):
        i = draw(st.integers(min_value=0, max_value=len(text)))
        j = draw(st.integers(min_value=0, max_value=len(text)))
        value = text[min(i, j) : max(i, j)]
    else:
        value = draw(st_scalar_text(min_size=0))
    return text, value


@st.composite
def st_text_and_pattern(draw: st.DrawFn) -> tuple[str, str]:
    """Generate file text plus a valid regex pattern.

    The pattern is either ``re.escape`` of a real slice (guaranteed to match), a
    curated valid pattern (may or may not match), or ``re.escape`` of arbitrary
    text. All three are valid regexes, so the ``re.search`` oracle decides the
    expected result.

    Returns:
        A tuple ``(text, pattern)``.
    """
    text = draw(st_scalar_text(min_size=0))
    choice = draw(st.sampled_from(("escaped_slice", "curated", "escaped_arbitrary")))
    if choice == "escaped_slice" and text:
        i = draw(st.integers(min_value=0, max_value=len(text)))
        j = draw(st.integers(min_value=0, max_value=len(text)))
        pattern = re.escape(text[min(i, j) : max(i, j)])
    elif choice == "curated":
        pattern = draw(st.sampled_from(_VALID_REGEX_PATTERNS))
    else:
        pattern = re.escape(draw(st_scalar_text(min_size=0)))
    return text, pattern


@st.composite
def st_file_exists_case(draw: st.DrawFn) -> tuple[str, bool]:
    """Generate a relative file name and whether it should be created."""
    name = draw(st.from_regex(r"[a-z0-9_]{1,12}", fullmatch=True))
    create = draw(st.booleans())
    return name, create


@st.composite
def st_dotted_json_case(draw: st.DrawFn) -> tuple[dict, str, object]:
    """Generate a nested JSON mapping, a dotted key_path, and a terminal value.

    The key_path is the real path, the real path plus an extra (non-resolving)
    segment, or an arbitrary path — so both resolving and non-resolving cases
    arise. The terminal value at the real path is returned so callers can build
    matching/mismatching comparison values.

    Returns:
        A tuple ``(data, key_path, terminal)``.
    """
    segments = draw(st.lists(st_json_key(), min_size=1, max_size=3))
    terminal = draw(st_json_terminal())
    data = _nest_linear(segments, terminal)
    choice = draw(st.sampled_from(("real", "extra", "arbitrary")))
    if choice == "real":
        path_segments = segments
    elif choice == "extra":
        path_segments = [*segments, draw(st_json_key())]
    else:
        path_segments = draw(st.lists(st_json_key(), min_size=1, max_size=3))
    return data, ".".join(path_segments), terminal


# ---------------------------------------------------------------------------
# Orchestration / reporting strategies and the controlled-registry builder
# ---------------------------------------------------------------------------
#
# These helpers build STRUCTURALLY VALID registries whose every content
# assertion has a DETERMINISTIC outcome, so the test can compute an exact
# oracle (how many violations, how many statically-checkable rules). Outcomes
# are controlled three ways:
#
#   * file_exists       -> pass by creating the target file, fail by skipping it
#   * substring_present -> pass/fail by writing content with/without the needle
#   * substring_absent  -> pass/fail by writing content without/with the needle
#
# A "rule plan" is either ``None`` (a behavioral-only ``static_checkable:false``
# entry with no assertions) or a list of ``(kind, should_pass)`` tuples (a
# statically-checkable rule). ``_build_controlled_registry`` turns plans into
# RuleEntry objects plus the exact set of files to create and the oracle counts.

# The needle used by the controlled substring assertions. It does not occur in
# any "passing-absent" / "failing-present" filler content below.
_NEEDLE = "NEEDLE"


def st_assertion_kind() -> st.SearchStrategy[str]:
    """Generate a controllable, file-backed assertion kind."""
    return st.sampled_from(
        ["file_exists", "substring_present", "substring_absent"]
    )


@st.composite
def st_rule_plans(draw: st.DrawFn) -> list[list[tuple[str, bool]] | None]:
    """Generate a registry plan: a mix of static rules and behavioral-only ones.

    Each element is either ``None`` (a behavioral-only entry) or a non-empty
    list of ``(kind, should_pass)`` tuples describing one statically-checkable
    rule's assertions. The mix interleaves behavioral-only entries between
    statically-checkable ones, with each assertion's pass/fail outcome chosen
    independently so violations scatter across rules.

    Returns:
        The list of rule plans.
    """
    n_rules = draw(st.integers(min_value=1, max_value=5))
    plans: list[list[tuple[str, bool]] | None] = []
    for _ in range(n_rules):
        if draw(st.booleans()):
            plans.append(None)  # behavioral-only entry
        else:
            n_assertions = draw(st.integers(min_value=1, max_value=4))
            plans.append(
                [
                    (draw(st_assertion_kind()), draw(st.booleans()))
                    for _ in range(n_assertions)
                ]
            )
    return plans


@st.composite
def st_failing_rule_plans(draw: st.DrawFn) -> list[list[tuple[str, bool]] | None]:
    """Generate a registry plan guaranteed to contain at least one failure.

    Builds on :func:`st_rule_plans` and forces the first assertion of the first
    statically-checkable rule to fail (adding one if the plan happened to be all
    behavioral-only), so the resulting run ends in failure with one or more
    content violations.

    Returns:
        The list of rule plans with at least one failing assertion.
    """
    plans = draw(st_rule_plans())
    static_positions = [i for i, plan in enumerate(plans) if plan is not None]
    if not static_positions:
        plans[0] = [("file_exists", False)]
        return plans
    first = static_positions[0]
    kind, _ = plans[first][0]
    plans[first][0] = (kind, False)
    return plans


def _build_controlled_registry(
    plans: list[list[tuple[str, bool]] | None],
) -> tuple[list[RuleEntry], dict[str, str], int, int]:
    """Turn rule plans into entries, files to create, and exact oracle counts.

    Each statically-checkable assertion is given a unique target filename so no
    two assertions interfere. The returned ``files`` mapping holds exactly the
    files whose presence/content makes the corresponding assertion behave as
    planned (a failing ``file_exists`` simply omits its file). ``expected_k`` is
    the exact number of content violations a run will collect; ``static_count``
    is the number of statically-checkable rules (behavioral-only entries are
    excluded).

    Args:
        plans: The rule plans from :func:`st_rule_plans`.

    Returns:
        A tuple ``(entries, files, expected_k, static_count)``.
    """
    entries: list[RuleEntry] = []
    files: dict[str, str] = {}
    expected_k = 0
    static_count = 0
    counter = 0
    for idx, plan in enumerate(plans):
        rule_id = f"rule-{idx}"
        if plan is None:
            entries.append(
                RuleEntry(
                    id=rule_id,
                    rule="behavioral-only rule text",
                    category="behavioral",
                    enforced_by=["docs/notes.md"],
                    assertions=[],
                    static_checkable=False,
                )
            )
            continue
        static_count += 1
        assertions: list[Assertion] = []
        for kind, should_pass in plan:
            counter += 1
            fname = f"f_{counter}.txt"
            if kind == "file_exists":
                assertions.append(Assertion(type="file_exists", file=fname))
                if should_pass:
                    files[fname] = "present"
                # A failing file_exists deliberately omits its target file.
            elif kind == "substring_present":
                assertions.append(
                    Assertion(
                        type="substring_present", file=fname, value=_NEEDLE
                    )
                )
                files[fname] = f"x {_NEEDLE} y" if should_pass else "x only y"
            else:  # substring_absent
                assertions.append(
                    Assertion(
                        type="substring_absent", file=fname, value=_NEEDLE
                    )
                )
                files[fname] = "clean content" if should_pass else f"has {_NEEDLE}"
            if not should_pass:
                expected_k += 1
        entries.append(
            RuleEntry(
                id=rule_id,
                rule="rule text",
                category="conformance",
                enforced_by=["docs/notes.md"],
                assertions=assertions,
                static_checkable=True,
            )
        )
    return entries, files, expected_k, static_count


@st.composite
def st_exit_code_scenario(
    draw: st.DrawFn,
) -> tuple[str, dict[str, str], int, bool]:
    """Generate a registry scenario with a known exit code and completion flag.

    Five kinds are produced to cover the full exit-code contract:

    * ``valid`` — a structurally valid controlled registry (all-passing or with
      content violations); exit 0 iff no assertion fails; completes.
    * ``duplicate_id`` — two entries share an ``id`` (schema halt).
    * ``missing_field`` — an entry is missing its required ``rule`` field
      (schema halt).
    * ``unsupported_type`` — an assertion uses a type outside the supported set
      (schema halt).
    * ``load_error`` — unparseable registry text (load halt).

    Every non-``valid`` kind exits 1 and does NOT complete.

    Returns:
        A tuple ``(registry_text, files, expected_exit, expected_completed)``.
    """
    kind = draw(
        st.sampled_from(
            [
                "valid",
                "duplicate_id",
                "missing_field",
                "unsupported_type",
                "load_error",
            ]
        )
    )
    if kind == "valid":
        plans = draw(st_rule_plans())
        entries, files, expected_k, _static = _build_controlled_registry(plans)
        return render_registry(entries), files, (0 if expected_k == 0 else 1), True
    if kind == "duplicate_id":
        shared = draw(st_rule_id())
        entry_a = RuleEntry(
            id=shared,
            rule="r1",
            category="c1",
            enforced_by=["e1"],
            assertions=[Assertion(type="file_exists", file="a.txt")],
        )
        entry_b = RuleEntry(
            id=shared,
            rule="r2",
            category="c2",
            enforced_by=["e2"],
            assertions=[Assertion(type="file_exists", file="b.txt")],
        )
        return render_registry([entry_a, entry_b]), {}, 1, False
    if kind == "missing_field":
        entry = RuleEntry(
            id=draw(st_rule_id()),
            rule="r",
            category="c",
            enforced_by=["e"],
            assertions=[Assertion(type="file_exists", file="a.txt")],
        )
        text = render_registry([entry])
        # Drop the required `rule:` field line -> schema violation on load.
        text = (
            "\n".join(
                line
                for line in text.splitlines()
                if not line.lstrip().startswith("rule:")
            )
            + "\n"
        )
        return text, {}, 1, False
    if kind == "unsupported_type":
        entry = RuleEntry(
            id=draw(st_rule_id()),
            rule="r",
            category="c",
            enforced_by=["e"],
            assertions=[Assertion(type="file_exists", file="a.txt")],
        )
        text = render_registry([entry]).replace(
            'type: "file_exists"', 'type: "totally_bogus_type"'
        )
        return text, {}, 1, False
    # load_error: unparseable registry text (unterminated quote / non-rules key).
    bad_text = draw(
        st.sampled_from(
            [
                'rules:\n  - id: "unterminated\n',
                'not_rules:\n  - id: "x"\n',
            ]
        )
    )
    return bad_text, {}, 1, False


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestGovernanceRuleProperties:
    """Hypothesis property tests for validate_governance_rules.py."""

    @given(entries=st_registry())
    @settings(max_examples=20)
    def test_property_1_parser_round_trip(self, entries: list[RuleEntry]) -> None:
        """Property 1: Parser round-trip preserves structure (regex + emoji).

        For any list of well-formed Rule Entries, rendering them to the registry
        YAML subset and then calling ``load_registry`` followed by
        ``validate_schema`` yields RuleEntry/Assertion structures equal to the
        originals, with no schema violations.

        **Validates: Requirements 4.1**
        """
        registry_text = render_registry(entries)
        with tempfile.TemporaryDirectory() as tmp_dir:
            registry_path = Path(tmp_dir) / "governance-rules.yaml"
            registry_path.write_text(registry_text, encoding="utf-8")
            raw_entries = load_registry(registry_path)

        rule_entries, violations = validate_schema(raw_entries)

        assert violations == [], f"unexpected schema violations: {violations}"
        assert rule_entries == entries

    @given(case=st_required_field_case())
    @settings(max_examples=20)
    def test_property_2_required_fields(
        self, case: tuple[dict, str | None]
    ) -> None:
        """Property 2: Schema requires every required field.

        For any generated entry, if any required field (id/rule/category/
        enforced_by/assertions) is missing or empty — including an empty
        ``enforced_by`` or empty ``assertions`` list — ``validate_schema``
        reports a schema violation for that entry (and the run exits 1 because a
        non-empty violations list always forces exit 1). If every required field
        is present and non-empty, no required-field violation is reported for
        that entry. Assertions may be empty ONLY when ``static_checkable`` is
        false; this case fixes ``static_checkable`` true so all five fields are
        genuinely required.

        **Validates: Requirements 2.1, 2.3, 2.4, 2.5, 2.6, 2.8**
        """
        raw, broken_field = case
        _entries, violations = validate_schema([raw])

        required_field_violations = [
            v
            for v in violations
            if v.kind == "schema" and "required field" in v.detail
        ]
        if broken_field is None:
            assert required_field_violations == [], (
                f"unexpected required-field violations: {required_field_violations}"
            )
        else:
            assert any(
                f"'{broken_field}'" in v.detail for v in required_field_violations
            ), (
                f"expected a required-field violation for {broken_field!r}, "
                f"got: {violations}"
            )
            # A non-empty violations list is what forces the run to exit 1.
            assert violations != []

    @given(raws=st_entries_maybe_duplicate_ids())
    @settings(max_examples=20)
    def test_property_3_duplicate_ids_rejected(self, raws: list[dict]) -> None:
        """Property 3: Duplicate ids are rejected.

        For any generated list of Rule Entries, ``validate_schema`` reports a
        duplicate-id violation (forcing exit 1) if and only if two or more
        entries share the same ``id``.

        **Validates: Requirements 2.2, 2.9**
        """
        ids = [raw.get("id") for raw in raws]
        has_duplicate = len(ids) != len(set(ids))

        _entries, violations = validate_schema(raws)
        duplicate_violations = [
            v
            for v in violations
            if v.kind == "schema" and "duplicate rule id" in v.detail
        ]

        if has_duplicate:
            assert duplicate_violations != [], (
                f"expected a duplicate-id violation for ids {ids}, got: {violations}"
            )
            assert violations != []
        else:
            assert duplicate_violations == [], (
                f"unexpected duplicate-id violation for ids {ids}: {violations}"
            )

    @given(raws=st_registry_with_unsupported_type())
    @settings(max_examples=20)
    def test_property_9_unsupported_type_halts(self, raws: list[dict]) -> None:
        """Property 9: Unsupported assertion type halts at schema stage.

        For any registry with at least one assertion whose ``type`` is outside
        the supported set, ``validate_schema`` reports an
        unsupported-assertion-type violation and returns before any content
        evaluation — even when other schema problems coexist. Per the
        implementation, the precedence pass returns an empty entries list so no
        rule advances to content evaluation; the run exits 1.

        **Validates: Requirements 3.9**
        """
        entries, violations = validate_schema(raws)

        # Halt: no typed entries are produced when an unsupported type is found.
        assert entries == []
        assert violations != []
        # Every reported violation is the unsupported-type kind (the precedence
        # pass returns before required-field / duplicate-id checks run).
        assert all(
            v.kind == "schema" and "unsupported assertion type" in v.detail
            for v in violations
        ), f"expected only unsupported-type violations, got: {violations}"

    @given(case=st_entry_with_malformed_assertion())
    @settings(max_examples=20)
    def test_property_10_missing_param_is_malformed(
        self, case: tuple[dict, str, str]
    ) -> None:
        """Property 10: Missing required parameter is a malformed-assertion violation.

        For any assertion whose ``type`` is supported but is missing a parameter
        required by that type, ``validate_schema`` reports a malformed-assertion
        violation (forcing exit 1) that names the dropped parameter.

        **Validates: Requirements 3.10**
        """
        raw, atype, dropped = case
        _entries, violations = validate_schema([raw])

        malformed_violations = [
            v
            for v in violations
            if v.kind == "schema" and "malformed assertion" in v.detail
        ]
        assert any(
            atype in v.detail and dropped in v.detail for v in malformed_violations
        ), (
            f"expected a malformed-assertion violation naming {dropped!r} for "
            f"type {atype!r}, got: {violations}"
        )
        assert violations != []

    @given(case=st_text_and_substring())
    @settings(max_examples=20)
    def test_property_4_substring_oracle(self, case: tuple[str, str]) -> None:
        """Property 4: Substring assertions agree with the membership oracle.

        For any file text and any candidate substring, ``substring_present``
        passes (returns ``None``) iff the substring occurs in the text, and
        ``substring_absent`` passes iff it does not — matching Python's ``in``
        operator on the file contents.

        **Validates: Requirements 3.1, 3.2**
        """
        text, value = case
        expected_present = value in text
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "target.txt").write_text(text, encoding="utf-8")

            present = Assertion(
                type="substring_present", file="target.txt", value=value
            )
            absent = Assertion(
                type="substring_absent", file="target.txt", value=value
            )
            present_result = evaluate_assertion(present, repo_root)
            absent_result = evaluate_assertion(absent, repo_root)

        # present passes (None) iff the substring is in the text.
        assert (present_result is None) == expected_present
        # absent passes (None) iff the substring is NOT in the text.
        assert (absent_result is None) == (not expected_present)
        # Failing assertions name the file as the content-violation cause.
        if present_result is not None:
            assert present_result.kind == "content"
            assert present_result.file == "target.txt"
        if absent_result is not None:
            assert absent_result.kind == "content"
            assert absent_result.file == "target.txt"

    @given(case=st_text_and_pattern())
    @settings(max_examples=20)
    def test_property_5_regex_oracle(self, case: tuple[str, str]) -> None:
        """Property 5: Regex assertions agree with the re.search oracle.

        For any file text and any valid regular expression, ``regex_present``
        passes iff ``re.search(pattern, text)`` matches, and ``regex_absent``
        passes iff it does not.

        **Validates: Requirements 3.3, 3.4**
        """
        text, pattern = case
        expected_match = re.search(pattern, text) is not None
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "target.txt").write_text(text, encoding="utf-8")

            present = Assertion(
                type="regex_present", file="target.txt", pattern=pattern
            )
            absent = Assertion(
                type="regex_absent", file="target.txt", pattern=pattern
            )
            present_result = evaluate_assertion(present, repo_root)
            absent_result = evaluate_assertion(absent, repo_root)

        # regex_present passes (None) iff re.search matches.
        assert (present_result is None) == expected_match
        # regex_absent passes (None) iff re.search does NOT match.
        assert (absent_result is None) == (not expected_match)

    @given(case=st_file_exists_case())
    @settings(max_examples=20)
    def test_property_6_file_exists_oracle(self, case: tuple[str, bool]) -> None:
        """Property 6: file_exists matches filesystem reality.

        For any path, a ``file_exists`` assertion passes (returns ``None``) iff
        a file actually exists at the path resolved against the repo root.

        **Validates: Requirements 3.5**
        """
        name, create = case
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            if create:
                (repo_root / name).write_text("present", encoding="utf-8")
            exists_on_disk = (repo_root / name).is_file()

            assertion = Assertion(type="file_exists", file=name)
            result = evaluate_assertion(assertion, repo_root)

        # Passes (None) iff the file exists on disk.
        assert (result is None) == exists_on_disk
        if result is not None:
            assert result.kind == "content"
            assert name in result.detail

    @given(case=st_dotted_json_case())
    @settings(max_examples=20)
    def test_property_7_hook_field_equals_oracle(
        self, case: tuple[dict, str, object]
    ) -> None:
        """Property 7: hook_field_equals matches dotted JSON traversal.

        For any JSON object and any dotted ``key_path``, a ``hook_field_equals``
        assertion passes iff traversing the object by the path segments resolves
        to a value whose ``str()`` form equals the assertion's ``value``. This
        exercises a matching value, a mismatched value, and a missing path.

        **Validates: Requirements 3.6**
        """
        data, key_path, terminal = case
        segments = key_path.split(".")
        found, value = _oracle_traverse(data, segments)
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "hook.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

            # Compare against the terminal's string form (a matching value when
            # the path resolves, an independent value to force a mismatch).
            matching = Assertion(
                type="hook_field_equals",
                file="hook.json",
                key_path=key_path,
                value=str(value) if found else str(terminal),
            )
            mismatch_value = str(value) + "_zzz_mismatch" if found else "no_such"
            mismatched = Assertion(
                type="hook_field_equals",
                file="hook.json",
                key_path=key_path,
                value=mismatch_value,
            )
            matching_result = evaluate_assertion(matching, repo_root)
            mismatched_result = evaluate_assertion(mismatched, repo_root)

        # Passes (None) iff the path resolves AND str(terminal) == value.
        assert (matching_result is None) == found
        # A guaranteed-mismatched value never passes (whether or not it resolves).
        assert mismatched_result is not None
        assert mismatched_result.kind == "content"
        assert mismatched_result.file == "hook.json"

    @given(case=st_dotted_json_case())
    @settings(max_examples=20)
    def test_property_8_yaml_key_present_oracle(
        self, case: tuple[dict, str, object]
    ) -> None:
        """Property 8: yaml_key_present matches dotted key existence.

        For any mapping and any dotted ``key_path``, a ``yaml_key_present``
        assertion passes iff every segment resolves and the final key is present
        in the mapping. A JSON file is used so the validator parses it with
        ``json.loads`` and traverses it deterministically as nested mappings.

        **Validates: Requirements 3.7**
        """
        data, key_path, _terminal = case
        segments = key_path.split(".")
        found, _value = _oracle_traverse(data, segments)
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "config.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

            assertion = Assertion(
                type="yaml_key_present", file="config.json", key_path=key_path
            )
            result = evaluate_assertion(assertion, repo_root)

        # Passes (None) iff the dotted key path resolves in the mapping.
        assert (result is None) == found
        if result is not None:
            assert result.kind == "content"
            assert result.file == "config.json"

    @given(
        atype=st.sampled_from(
            sorted(t for t in SUPPORTED_ASSERTION_TYPES if t != "file_exists")
        ),
        missing_name=st.from_regex(r"[a-z0-9_]{1,12}", fullmatch=True),
    )
    @settings(max_examples=20)
    def test_property_11_missing_file_fails(
        self, atype: str, missing_name: str
    ) -> None:
        """Property 11: Missing target file fails non-existence-tolerant assertions.

        For any assertion whose type is not ``file_exists``, if the target file
        does not exist the assertion fails and the resulting violation names the
        missing file as the cause (both in ``detail`` and ``file``).

        **Validates: Requirements 4.5**
        """
        # Fill every required parameter for the type so the assertion is
        # well-formed; only the missing file should cause the failure.
        params = SUPPORTED_ASSERTION_TYPES[atype]
        kwargs: dict[str, str] = {}
        for param in params:
            if param == "file":
                kwargs[param] = missing_name
            elif param == "key_path":
                kwargs[param] = "some.path"
            else:
                kwargs[param] = "anything"
        assertion = Assertion(type=atype, **kwargs)

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            # Deliberately do NOT create the target file.
            assert not (repo_root / missing_name).exists()
            result = evaluate_assertion(assertion, repo_root)

        assert result is not None, (
            f"{atype}: expected a violation for a missing target file"
        )
        assert result.kind == "content"
        # The missing file is named as the cause, in both detail and file.
        assert missing_name in result.detail
        assert result.file == missing_name

    @staticmethod
    def _materialize(repo_root: Path, files: dict[str, str]) -> None:
        """Write the controlled target files into the temp repo root."""
        for name, content in files.items():
            (repo_root / name).write_text(content, encoding="utf-8")

    @given(plans=st_rule_plans())
    @settings(max_examples=20)
    def test_property_12_collect_all_with_behavioral_skip(
        self, plans: list[list[tuple[str, bool]] | None]
    ) -> None:
        """Property 12: Structurally valid registries are evaluated completely.

        For any structurally valid registry in which exactly ``k`` content
        assertions are arranged to fail (scattered across rules, with
        behavioral-only ``static_checkable: false`` entries interspersed), a
        single ``run`` evaluates every assertion of every statically-checkable
        rule, skips the behavioral-only entries without failing on them, and
        collects exactly ``k`` content violations without stopping at the first
        failure.

        **Validates: Requirements 4.2, 4.6, 8.2, 8.4**
        """
        entries, files, expected_k, static_count = _build_controlled_registry(plans)
        behavioral_ids = {
            entry.id for entry in entries if not entry.static_checkable
        }
        registry_text = render_registry(entries)
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            self._materialize(repo_root, files)
            registry_path = repo_root / "governance-rules.yaml"
            registry_path.write_text(registry_text, encoding="utf-8")
            result = run(registry_path, repo_root)

        # The run evaluated to completion across a structurally valid registry.
        assert result.completed is True
        # Every statically-checkable rule was evaluated; behavioral-only ones
        # are not counted.
        assert result.rules_checked == static_count
        # Exactly k content violations were collected (no early stop).
        assert len(result.violations) == expected_k
        assert all(v.kind == "content" for v in result.violations)
        # Behavioral-only entries are skipped: none of them produced a violation.
        assert all(v.rule_id not in behavioral_ids for v in result.violations)
        # Exit code reflects the collected violations.
        assert result.exit_code == (0 if expected_k == 0 else 1)

    @given(scenario=st_exit_code_scenario())
    @settings(max_examples=20)
    def test_property_13_canonical_exit_code(
        self, scenario: tuple[str, dict[str, str], int, bool]
    ) -> None:
        """Property 13: Canonical exit-code contract.

        For any registry, the validator exits with status code 0 if and only if
        the registry is structurally valid AND every evaluated assertion holds
        AND no internal evaluation error occurred; in every other case (a
        load/schema error, a malformed/unsupported assertion, or at least one
        content violation) it exits with status code 1. The expected exit code
        is computed from how each scenario was constructed (the oracle).

        **Validates: Requirements 4.3, 4.4, 6.4, 11.2**
        """
        registry_text, files, expected_exit, expected_completed = scenario
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            self._materialize(repo_root, files)
            registry_path = repo_root / "governance-rules.yaml"
            registry_path.write_text(registry_text, encoding="utf-8")
            result = run(registry_path, repo_root)

        assert result.exit_code == expected_exit
        assert result.completed == expected_completed
        # Restate the iff directly: exit 0 exactly when the run completed with
        # no violations.
        assert (result.exit_code == 0) == (
            result.completed and not result.violations
        )

    @given(plans=st_failing_rule_plans())
    @settings(max_examples=20)
    def test_property_14_violation_reporting_on_stderr(
        self, plans: list[list[tuple[str, bool]] | None]
    ) -> None:
        """Property 14: Violation reporting is complete and on stderr.

        For any run that ends in failure with one or more violations, each
        violation is rendered as a separate entry on standard error, and every
        content violation's text includes the failing rule's ``id``, the failing
        assertion's type and parameters, and the file path involved. None of the
        violation details appear on standard out.

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.6, 11.5**
        """
        entries, files, expected_k, _static = _build_controlled_registry(plans)
        registry_text = render_registry(entries)
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            self._materialize(repo_root, files)
            registry_path = repo_root / "governance-rules.yaml"
            registry_path.write_text(registry_text, encoding="utf-8")
            result = run(registry_path, repo_root)

            out = io.StringIO()
            err = io.StringIO()
            report(result, stdout=out, stderr=err)
            stdout_text = out.getvalue()
            stderr_text = err.getvalue()

        # The failing-plan strategy guarantees at least one content violation.
        assert result.exit_code == 1
        assert len(result.violations) == expected_k >= 1
        assert all(v.kind == "content" for v in result.violations)

        # Each violation is a separate entry on stderr: one "[CONTENT]" header
        # per violation.
        assert stderr_text.count("[CONTENT]") == len(result.violations)

        # Every content violation names its rule id, assertion type + params,
        # and file path on stderr.
        for violation in result.violations:
            assert violation.rule_id
            assert f"rule '{violation.rule_id}'" in stderr_text
            assert violation.assertion is not None
            assert f"type={violation.assertion.type}" in stderr_text
            assert violation.assertion.file is not None
            # The file path appears both as an assertion param and a file line.
            assert f"file: {violation.assertion.file}" in stderr_text
            # substring assertions carry a value param that must be rendered.
            if violation.assertion.value is not None:
                assert (
                    f"value={violation.assertion.value!r}" in stderr_text
                )

        # No violation details leak onto stdout (rule ids and file paths).
        for violation in result.violations:
            assert violation.rule_id not in stdout_text
            assert violation.assertion is not None
            assert violation.assertion.file not in stdout_text

    @given(scenario=st_exit_code_scenario())
    @settings(max_examples=20)
    def test_property_15_completion_counts_only_on_completion(
        self, scenario: tuple[str, dict[str, str], int, bool]
    ) -> None:
        """Property 15: Completion counts are emitted only on full completion.

        For any run, the completion counts (number of Rule Entries checked and
        number of Violations found) appear in stdout if and only if the run
        evaluated all statically-checkable rules to completion; a run aborted by
        a schema-level or load error does not emit the completion counts.

        **Validates: Requirements 5.5**
        """
        registry_text, files, _expected_exit, expected_completed = scenario
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            self._materialize(repo_root, files)
            registry_path = repo_root / "governance-rules.yaml"
            registry_path.write_text(registry_text, encoding="utf-8")
            result = run(registry_path, repo_root)

            out = io.StringIO()
            err = io.StringIO()
            report(result, stdout=out, stderr=err)
            stdout_text = out.getvalue()

        assert result.completed == expected_completed
        # Completion counts appear in stdout iff the run completed.
        assert ("Rule Entries checked:" in stdout_text) == result.completed
        assert ("Violations found:" in stdout_text) == result.completed
