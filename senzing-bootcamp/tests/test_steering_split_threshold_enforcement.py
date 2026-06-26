"""Tests for the Split_Check lint rule in lint_steering.py.

Feature: steering-split-threshold-enforcement

This module holds the property-based, unit, and integration tests for the
Split_Check, which enforces the ``budget.split_threshold_tokens`` budget
declared in ``senzing-bootcamp/steering/steering-index.yaml``.

Per Requirement 6.7, the property tests in this spec carry an intentional inline
``@settings(max_examples=5)`` override of the Hypothesis profile baseline. The
reduced example count keeps the property-based tests fast to run. The shared
``st_``-prefixed strategies defined here are consumed by the property tests added
in later tasks.

This file is scaffolding: imports and shared strategies only. The actual test
classes and methods are filled in by subsequent tasks. Some imported symbols are
implemented in later tasks; importing them here is intentional.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (  # noqa: E402
    INDEX_PATH,
    LintViolation,
    get_split_threshold,
    main,
    parse_steering_index,
    run_all_checks,
)

# The remaining Split_Check symbols are implemented by later tasks. Import them
# defensively so this module still collects (and the already-implemented tests
# run) before those tasks land. Each will resolve to the real implementation
# once present.
try:  # noqa: SIM105
    from lint_steering import (  # noqa: E402
        SplitAllowlistEntry,
        check_split_threshold,
        normalize_split_severity,
        parse_split_allowlist,
    )
except ImportError:  # pragma: no cover - symbols arrive in later tasks
    SplitAllowlistEntry = None  # type: ignore[assignment,misc]
    check_split_threshold = None  # type: ignore[assignment]
    normalize_split_severity = None  # type: ignore[assignment]
    parse_split_allowlist = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies
# ---------------------------------------------------------------------------


def st_token_count() -> st.SearchStrategy[int]:
    """Integer Token_Count values in the [0, 1,000,000] range (Requirement 6.7)."""
    return st.integers(min_value=0, max_value=1_000_000)


def st_threshold() -> st.SearchStrategy[int]:
    """Positive integer Split_Threshold values in the [1, 1,000,000] range."""
    return st.integers(min_value=1, max_value=1_000_000)


def st_filename() -> st.SearchStrategy[str]:
    """Exact, case-sensitive kebab-case ``.md`` steering filenames."""
    return st.from_regex(r"[a-z0-9]+(-[a-z0-9]+)*\.md", fullmatch=True)


def st_justification_valid() -> st.SearchStrategy[str]:
    """Valid allowlist justification text of 1 to 280 characters."""
    return st.text(min_size=1, max_size=280)


def st_justification_invalid() -> st.SearchStrategy[str]:
    """Invalid allowlist justification text: empty or 281 to 400 characters."""
    return st.one_of(
        st.just(""),
        st.text(min_size=281, max_size=400),
    )


def st_justification_roundtrip() -> st.SearchStrategy[str]:
    """Valid justification text that round-trips through ``parse_split_allowlist``.

    The minimal index parser splits each ``  <filename>: <justification>`` line on
    the first ``:`` and applies ``str.strip()`` to both sides, so a justification
    only round-trips when it survives that processing. This strategy constrains the
    text to 1-280 characters with no ``:`` (the field separator), no newline or
    control characters (line-based parsing), and no leading/trailing whitespace
    (removed by ``str.strip()``), keeping the round-trip well defined.
    """
    return (
        st.text(
            alphabet=st.characters(
                blacklist_characters="\n\r:",
                blacklist_categories=("Cc", "Cs"),
            ),
            min_size=1,
            max_size=280,
        )
        .map(str.strip)
        .filter(lambda value: 1 <= len(value) <= 280)
    )


def st_allowlist_pairs() -> st.SearchStrategy[dict[str, str]]:
    """Maps of distinct steering filename -> round-trip-safe justification."""
    return st.dictionaries(
        keys=st_filename(),
        values=st_justification_roundtrip(),
        max_size=10,
    )


def st_file_metadata() -> st.SearchStrategy[dict[str, dict[str, int]]]:
    """Maps of steering filename -> ``{"token_count": int}``."""
    return st.dictionaries(
        keys=st_filename(),
        values=st.fixed_dictionaries({"token_count": st_token_count()}),
        max_size=10,
    )


def st_invalid_severity() -> st.SearchStrategy[str]:
    """Severity strings that are neither ``WARNING`` nor ``ERROR``."""
    return st.text().filter(lambda value: value not in {"WARNING", "ERROR"})


def st_invalid_count() -> st.SearchStrategy[object]:
    """Non-integer ``token_count`` values: strings, floats, or ``None``.

    Excludes ``bool`` because Python treats ``bool`` as a subclass of ``int``, so
    ``isinstance(value, int)`` is ``True`` for booleans and they would not exercise
    the unclassifiable (MISSING) branch this strategy targets.
    """
    return st.one_of(
        st.text(max_size=20),
        st.floats(allow_nan=False, allow_infinity=False),
        st.none(),
    )


def st_non_positive_threshold_value() -> st.SearchStrategy[str]:
    """Rendered ``split_threshold_tokens`` values that are not positive integers.

    Covers the three non-positive-integer cases the Default_Threshold fallback
    must absorb (Requirement 1.5): zero, negative integers, and non-numeric text.
    The non-numeric branch excludes decimal digits entirely so the
    ``split_threshold_tokens:\\s*(\\d+)`` lookup cannot accidentally capture a
    positive integer.
    """
    return st.one_of(
        st.just("0"),
        st.integers(min_value=-1_000_000, max_value=-1).map(str),
        st.text(
            alphabet=st.characters(
                blacklist_categories=("Nd",),
                blacklist_characters="\n\r:",
            ),
            min_size=1,
            max_size=20,
        ),
    )


def st_file_metadata_mixed() -> st.SearchStrategy[dict[str, dict[str, object]]]:
    """Maps of filename -> entry, mixing valid, absent, and non-integer counts.

    Exercises every classification branch of ``check_split_threshold``: entries
    with a valid integer ``token_count`` (over/under threshold), entries with an
    absent count (empty dict), and entries with a non-integer count (string,
    float, or ``None``). This breadth lets Property 6 assert well-formedness of
    over-threshold and MISSING violations alike.
    """
    valid_entry = st.fixed_dictionaries({"token_count": st_token_count()})
    absent_entry = st.just({})
    invalid_entry = st.fixed_dictionaries({"token_count": st_invalid_count()})
    return st.dictionaries(
        keys=st_filename(),
        values=st.one_of(valid_entry, absent_entry, invalid_entry),
        max_size=10,
    )


def st_allowlist_entries() -> st.SearchStrategy[list]:
    """Lists of ``SplitAllowlistEntry`` mixing valid, invalid, and stale entries.

    Justifications are drawn from both the valid (1-280 chars) and invalid
    (empty or >280 chars) pools so the allowlist-validation and stale-entry
    branches of ``check_split_threshold`` (which emit ERROR violations) are
    exercised. Filenames are generated independently of ``file_metadata`` keys,
    so some entries are stale (absent from ``file_metadata``).
    """
    return st.lists(
        st.builds(
            SplitAllowlistEntry,
            filename=st_filename(),
            justification=st.one_of(st_justification_valid(), st_justification_invalid()),
        ),
        max_size=5,
    )


# ---------------------------------------------------------------------------
# Property tests for get_split_threshold
# ---------------------------------------------------------------------------


class TestGetSplitThreshold:
    """Property tests for the Split_Threshold reader (Requirements 1.2, 1.6)."""

    # Feature: steering-split-threshold-enforcement, Property 3: A configured
    # positive-integer threshold is honored (first occurrence wins).
    # Validates: Requirements 1.2, 1.6
    @given(
        first=st_threshold(),
        trailing=st.lists(st_threshold(), max_size=4),
    )
    @settings(max_examples=5)
    def test_first_positive_integer_threshold_wins(
        self,
        first: int,
        trailing: list[int],
    ) -> None:
        """The first positive-integer ``split_threshold_tokens`` value is returned.

        Renders the leading value ``first`` followed by any number of trailing
        positive-integer values as ``budget.split_threshold_tokens`` lines, and
        asserts ``get_split_threshold`` returns the first value regardless of the
        trailing ones.
        """
        lines = ["budget:", f"  split_threshold_tokens: {first}"]
        lines.extend(f"  split_threshold_tokens: {value}" for value in trailing)
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            assert get_split_threshold(index_path) == first

    # Feature: steering-split-threshold-enforcement, Property 4: An invalid or
    # absent threshold falls back to the Default_Threshold.
    # Validates: Requirements 1.5
    @given(value=st_non_positive_threshold_value())
    @settings(max_examples=5)
    def test_invalid_threshold_falls_back_to_default(self, value: str) -> None:
        """A non-positive-integer ``split_threshold_tokens`` falls back to 5000.

        Renders a ``split_threshold_tokens`` value that is zero, negative, or
        non-numeric and asserts ``get_split_threshold`` returns the
        Default_Threshold of 5000 rather than honoring the invalid value.
        """
        lines = ["budget:", f"  split_threshold_tokens: {value}"]
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            assert get_split_threshold(index_path) == 5000

    # Feature: steering-split-threshold-enforcement, Property 4: An invalid or
    # absent threshold falls back to the Default_Threshold.
    # Validates: Requirements 1.5
    def test_absent_threshold_falls_back_to_default(self) -> None:
        """An index whose ``budget`` block omits the key falls back to 5000.

        The key-absent case from Property 4: a well-formed index that simply does
        not declare ``split_threshold_tokens`` must resolve to the
        Default_Threshold of 5000.
        """
        lines = ["budget:", "  router_ceiling: 1000"]
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            assert get_split_threshold(index_path) == 5000

    # Unit tests: missing-file and absent-key Default_Threshold fallback.
    # Validates: Requirements 1.3, 1.4, 6.6
    def test_missing_index_file_falls_back_to_default(self) -> None:
        """A non-existent index path resolves to the Default_Threshold of 5000.

        Requirement 1.3: when the Steering_Index file does not exist,
        ``get_split_threshold`` must return the Default_Threshold of 5000 rather
        than raising. Points at a path inside a temporary directory that is never
        created, guaranteeing the file is absent.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = Path(tmp_dir) / "does-not-exist" / "steering-index.yaml"

            assert not missing_path.exists()
            assert get_split_threshold(missing_path) == 5000

    def test_existing_index_without_key_falls_back_to_default(self) -> None:
        """An existing index that omits the key resolves to the Default_Threshold.

        Requirement 1.4: when the Steering_Index exists but
        ``budget.split_threshold_tokens`` is absent, ``get_split_threshold`` must
        return the Default_Threshold of 5000. Complements the property-based
        ``test_absent_threshold_falls_back_to_default`` with an explicit unit
        case whose index carries unrelated sections (and no ``budget`` block at
        all) yet still falls back.
        """
        lines = [
            "file_metadata:",
            "  graduation.md:",
            "    token_count: 5394",
            "    size_category: large",
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            assert index_path.exists()
            assert get_split_threshold(index_path) == 5000


# ---------------------------------------------------------------------------
# Property tests for parse_split_allowlist
# ---------------------------------------------------------------------------


class TestParseSplitAllowlist:
    """Property tests for the allowlist parser (Requirement 4.1)."""

    # Feature: steering-split-threshold-enforcement, Property 11: Allowlist
    # parsing round-trips filename/justification pairs.
    # Validates: Requirements 4.1
    @given(pairs=st_allowlist_pairs())
    @settings(max_examples=5)
    def test_allowlist_round_trips_filename_justification_pairs(
        self,
        pairs: dict[str, str],
    ) -> None:
        """Rendered allowlist entries parse back to the same filename/justification.

        Renders a set of distinct ``(filename, justification)`` pairs into a
        ``split_allowlist:`` section using the two-space-indented
        ``<filename>: <justification>`` form, then asserts ``parse_split_allowlist``
        returns one entry per pair preserving each exact, case-sensitive filename
        and its justification.
        """
        lines = ["split_allowlist:"]
        lines.extend(f"  {filename}: {justification}" for filename, justification in pairs.items())
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            entries = parse_split_allowlist(index_path)

            parsed = {entry.filename: entry.justification for entry in entries}
            assert parsed == pairs
            assert len(entries) == len(pairs)


# ---------------------------------------------------------------------------
# Property tests for normalize_split_severity
# ---------------------------------------------------------------------------


class TestNormalizeSplitSeverity:
    """Property tests for severity-override validation (Requirement 3.7)."""

    # Feature: steering-split-threshold-enforcement, Property 7: Invalid severity
    # overrides are rejected.
    # Validates: Requirements 3.7
    @given(value=st_invalid_severity())
    @settings(max_examples=5)
    def test_invalid_severity_is_rejected(self, value: str) -> None:
        """Any string that is neither ``WARNING`` nor ``ERROR`` raises ``ValueError``.

        Requirement 3.7: an invalid severity override must surface an error
        indication rather than silently defaulting. Generates strings outside
        ``{"WARNING", "ERROR"}`` and asserts ``normalize_split_severity`` raises
        ``ValueError`` instead of returning a default.
        """
        with pytest.raises(ValueError):
            normalize_split_severity(value)

    def test_none_resolves_to_warning(self) -> None:
        """A ``None`` override (no override supplied) resolves to ``WARNING``."""
        assert normalize_split_severity(None) == "WARNING"

    def test_valid_severities_pass_through(self) -> None:
        """The canonical ``WARNING`` and ``ERROR`` values pass through unchanged."""
        assert normalize_split_severity("WARNING") == "WARNING"
        assert normalize_split_severity("ERROR") == "ERROR"


# ---------------------------------------------------------------------------
# Property tests for check_split_threshold
# ---------------------------------------------------------------------------


class TestCheckSplitThreshold:
    """Property tests for the Split_Check classification rule (Requirement 2)."""

    # Feature: steering-split-threshold-enforcement, Property 1: Over-threshold
    # classification is an IFF on strictly-greater-than.
    # Validates: Requirements 2.1, 2.2, 2.3, 2.5, 6.2, 6.3, 6.7
    @given(
        filename=st_filename(),
        token_count=st_token_count(),
        threshold=st_threshold(),
    )
    @settings(max_examples=5)
    def test_over_threshold_iff_strictly_greater(
        self,
        filename: str,
        token_count: int,
        threshold: int,
    ) -> None:
        """A single file is flagged iff its token_count strictly exceeds the threshold.

        Constructs a one-entry ``file_metadata`` map with an integer
        ``token_count`` and runs ``check_split_threshold`` with an empty allowlist.
        With a valid integer count and no exemptions there can be no MISSING/ERROR
        finding, so over-threshold violations are the WARNING-level ones. Asserts
        exactly one over-threshold violation is produced if and only if
        ``token_count > threshold`` (so the ``token_count == threshold`` boundary
        produces none), and that the violation's message names the filename, the
        integer ``token_count``, and the Split_Threshold.
        """
        file_metadata = {filename: {"token_count": token_count}}

        violations = check_split_threshold(file_metadata, threshold, [])

        over_threshold = [v for v in violations if v.level == "WARNING"]
        # No MISSING/ERROR findings expected for a valid integer count, no allowlist.
        assert all(v.level == "WARNING" for v in violations)

        if token_count > threshold:
            assert len(over_threshold) == 1
            message = over_threshold[0].message
            assert filename in message
            assert str(token_count) in message
            assert str(threshold) in message
        else:
            assert over_threshold == []

    # Feature: steering-split-threshold-enforcement, Property 2: Missing or
    # non-integer counts yield exactly one unclassifiable violation.
    # Validates: Requirements 2.4
    @given(
        filename=st_filename(),
        threshold=st_threshold(),
        absent=st.booleans(),
        invalid_count=st_invalid_count(),
    )
    @settings(max_examples=5)
    def test_missing_or_non_integer_count_yields_one_unclassifiable_violation(
        self,
        filename: str,
        threshold: int,
        absent: bool,
        invalid_count: object,
    ) -> None:
        """An absent or non-integer token_count yields exactly one cannot-classify finding.

        Builds a one-entry ``file_metadata`` map whose ``token_count`` is either
        absent (the entry is an empty dict) or a non-integer value (string, float,
        or ``None``), and runs ``check_split_threshold`` with an empty allowlist so
        the file is never exempt. Asserts exactly one violation is produced, that it
        names the file and states the file cannot be classified, and that no
        over-threshold violation is emitted for an unclassifiable count.
        """
        entry: dict[str, object] = {} if absent else {"token_count": invalid_count}
        file_metadata = {filename: entry}

        violations = check_split_threshold(file_metadata, threshold, [])

        assert len(violations) == 1
        violation = violations[0]
        assert filename in violation.message
        assert "cannot be classified" in violation.message
        # No over-threshold finding: the unclassifiable message must not claim the
        # count exceeds the Split_Threshold.
        assert "exceeds" not in violation.message

    # Feature: steering-split-threshold-enforcement, Property 5: Over-threshold
    # violations carry the configured severity.
    # Validates: Requirements 3.1, 3.3
    @given(
        file_metadata=st_file_metadata(),
        threshold=st_threshold(),
        severity=st.sampled_from(["WARNING", "ERROR"]),
    )
    @settings(max_examples=5)
    def test_over_threshold_violations_carry_configured_severity(
        self,
        file_metadata: dict[str, dict[str, int]],
        threshold: int,
        severity: str,
    ) -> None:
        """Every over-threshold violation's ``level`` equals the configured severity.

        Generates a ``file_metadata`` map (all integer ``token_count`` values, so
        no MISSING findings) and a severity in ``{"WARNING", "ERROR"}``, then runs
        ``check_split_threshold`` with an empty allowlist. With valid integer counts
        and no exemptions, every violation is an over-threshold violation (its
        message contains ``"exceeds"``). Asserts each such violation's ``level``
        equals the configured ``severity`` (Requirement 3.3).
        """
        violations = check_split_threshold(file_metadata, threshold, [], severity=severity)

        over_threshold = [v for v in violations if "exceeds" in v.message]
        # With integer counts and no allowlist, every finding is over-threshold.
        assert over_threshold == violations
        for violation in over_threshold:
            assert violation.level == severity

    # Feature: steering-split-threshold-enforcement, Property 5: Over-threshold
    # violations carry the configured severity.
    # Validates: Requirements 3.1, 3.3
    @given(
        file_metadata=st_file_metadata(),
        threshold=st_threshold(),
    )
    @settings(max_examples=5)
    def test_over_threshold_violations_default_to_warning(
        self,
        file_metadata: dict[str, dict[str, int]],
        threshold: int,
    ) -> None:
        """Without a severity override, over-threshold violations default to WARNING.

        Calls ``check_split_threshold`` with no ``severity`` argument (Requirement
        3.1) and asserts every over-threshold violation (message contains
        ``"exceeds"``) has its ``level`` set to ``"WARNING"``.
        """
        violations = check_split_threshold(file_metadata, threshold, [])

        over_threshold = [v for v in violations if "exceeds" in v.message]
        assert over_threshold == violations
        for violation in over_threshold:
            assert violation.level == "WARNING"

    # Feature: steering-split-threshold-enforcement, Property 6: Every emitted
    # violation is a well-formed LintViolation.
    # Validates: Requirements 3.6
    @given(
        file_metadata=st_file_metadata_mixed(),
        threshold=st_threshold(),
        allowlist=st_allowlist_entries(),
        severity=st.sampled_from(["WARNING", "ERROR"]),
    )
    @settings(max_examples=5)
    def test_every_emitted_violation_is_well_formed(
        self,
        file_metadata: dict[str, dict[str, object]],
        threshold: int,
        allowlist: list,
        severity: str,
    ) -> None:
        """Every object returned by the Split_Check is a well-formed LintViolation.

        Drives ``check_split_threshold`` across the full branch space —
        ``file_metadata`` mixing valid integer counts with absent and non-integer
        counts, an allowlist mixing valid, invalid-justification, and stale
        entries, and a configured severity — so over-threshold, MISSING, invalid,
        and stale violations are all exercised. Asserts each returned object is a
        ``LintViolation`` whose ``level`` is in ``{"WARNING", "ERROR"}``, whose
        ``file`` is a non-empty string, whose ``line`` is an integer, and whose
        ``message`` is a non-empty string (Requirement 3.6).
        """
        violations = check_split_threshold(
            file_metadata, threshold, allowlist, severity=severity
        )

        for violation in violations:
            assert isinstance(violation, LintViolation)
            assert violation.level in {"WARNING", "ERROR"}
            assert isinstance(violation.file, str) and violation.file
            assert isinstance(violation.line, int)
            assert isinstance(violation.message, str) and violation.message

    # Feature: steering-split-threshold-enforcement, Property 8: Exemption holds
    # iff a file exactly (case-sensitively) matches a valid allowlist entry.
    # Validates: Requirements 4.2, 4.3, 4.4, 6.4
    @given(
        filename=st_filename(),
        threshold=st.integers(min_value=1, max_value=999_999),
        justification=st_justification_valid(),
        scenario=st.sampled_from(["exact_valid", "empty", "case_mismatch", "different"]),
        data=st.data(),
    )
    @settings(max_examples=5)
    def test_exemption_iff_exact_case_sensitive_valid_match(
        self,
        filename: str,
        threshold: int,
        justification: str,
        scenario: str,
        data: st.DataObject,
    ) -> None:
        """An over-threshold file is exempt iff it exactly matches a valid entry.

        Builds a one-entry ``file_metadata`` map whose ``token_count`` is strictly
        greater than the Split_Threshold, then runs ``check_split_threshold`` with
        one of four allowlist scenarios:

        - ``exact_valid``: an entry whose filename exactly (case-sensitively)
          matches the file, with a valid justification -> the file is exempt and
          produces no over-threshold ("exceeds") violation (Requirement 4.2).
        - ``empty``: no allowlist at all -> the file is flagged (Requirement 4.4).
        - ``case_mismatch``: an entry whose filename differs only by case ->
          matching is case-sensitive, so the file is NOT exempt and is flagged
          (Requirement 4.3).
        - ``different``: an entry for an unrelated filename -> the file is NOT
          exempt and is flagged (Requirement 4.3).

        Non-matching allowlist filenames are absent from ``file_metadata`` and so
        emit ERROR stale-entry findings; this test asserts only about the
        over-threshold ("exceeds") violations, which are the subject of Property 8.
        The ``case_mismatch`` and ``different`` cases reduce to Property 1's
        strictly-greater-than rule, as does the empty-allowlist case (Requirement
        6.4).
        """
        # token_count strictly over the threshold (Requirement 4.2 precondition).
        token_count = data.draw(st.integers(min_value=threshold + 1, max_value=1_000_000))
        file_metadata = {filename: {"token_count": token_count}}

        if scenario == "exact_valid":
            allowlist = [SplitAllowlistEntry(filename, justification)]
            expected_exempt = True
        elif scenario == "empty":
            allowlist = []
            expected_exempt = False
        elif scenario == "case_mismatch":
            # ``.md`` always carries letters, so swapcase always differs.
            allowlist = [SplitAllowlistEntry(filename.swapcase(), justification)]
            expected_exempt = False
        else:  # "different": a distinct, valid kebab-case filename
            allowlist = [SplitAllowlistEntry(f"zzz-{filename}", justification)]
            expected_exempt = False

        violations = check_split_threshold(file_metadata, threshold, allowlist)

        over_threshold = [v for v in violations if "exceeds" in v.message]
        if expected_exempt:
            # Exact case-sensitive match with a valid justification -> exempt.
            assert over_threshold == []
        else:
            # No valid exact match -> evaluated per Property 1 and flagged once.
            assert len(over_threshold) == 1
            message = over_threshold[0].message
            assert filename in message
            assert str(token_count) in message
            assert str(threshold) in message

    # Feature: steering-split-threshold-enforcement, Property 9: Stale allowlist
    # entries are reported while others still apply.
    # Validates: Requirements 4.5
    @given(
        present=st_allowlist_pairs(),
        stale=st_allowlist_pairs(),
        threshold=st.integers(min_value=1, max_value=999_999),
    )
    @settings(max_examples=5)
    def test_stale_entries_reported_while_present_entries_still_apply(
        self,
        present: dict[str, str],
        stale: dict[str, str],
        threshold: int,
    ) -> None:
        """Stale allowlist filenames are each flagged once while present ones exempt.

        Generates two sets of distinct ``(filename, valid justification)`` pairs and
        makes them disjoint:

        - ``present`` files are added to ``file_metadata`` with an over-threshold
          ``token_count`` and allowlisted with a valid justification, so each is
          exempt and produces no over-threshold ("exceeds") violation.
        - ``stale`` filenames are NOT added to ``file_metadata`` but ARE allowlisted
          with a valid justification, so each must produce exactly one stale-entry
          ERROR violation naming that filename (Requirement 4.5).

        Asserts (1) exactly one stale violation per stale filename — the stale
        violation count equals the number of stale entries and each names its
        filename (matched on the quoted ``'filename'`` token to avoid substring
        collisions); and (2) the present, allowlisted, over-threshold files remain
        exempt, producing no over-threshold violation.
        """
        # Ensure the present and stale filename sets are disjoint.
        stale = {name: just for name, just in stale.items() if name not in present}
        assume(stale)  # Property 9 concerns one or more stale entries.

        # Present files: measured, over-threshold, and allowlisted (exempt).
        # Stale files are deliberately absent from file_metadata.
        file_metadata = {name: {"token_count": threshold + 1} for name in present}

        allowlist = [SplitAllowlistEntry(name, just) for name, just in present.items()]
        allowlist += [SplitAllowlistEntry(name, just) for name, just in stale.items()]

        violations = check_split_threshold(file_metadata, threshold, allowlist)

        # (1) Exactly one stale violation per stale filename.
        stale_violations = [v for v in violations if "stale" in v.message]
        assert len(stale_violations) == len(stale)
        for name in stale:
            matching = [v for v in stale_violations if f"'{name}'" in v.message]
            assert len(matching) == 1

        # (2) Present allowlisted over-threshold files are still exempt.
        over_threshold = [v for v in violations if "exceeds" in v.message]
        assert over_threshold == []

    # Feature: steering-split-threshold-enforcement, Property 10: Invalid
    # justifications produce a violation and do not exempt.
    # Validates: Requirements 4.6
    @given(
        filename=st_filename(),
        threshold=st.integers(min_value=1, max_value=999_999),
        invalid_justification=st_justification_invalid(),
        data=st.data(),
    )
    @settings(max_examples=5)
    def test_invalid_justification_produces_violation_and_does_not_exempt(
        self,
        filename: str,
        threshold: int,
        invalid_justification: str,
        data: st.DataObject,
    ) -> None:
        """An invalid-justification allowlist entry is flagged and does not exempt.

        Builds a one-entry ``file_metadata`` map whose ``token_count`` is strictly
        greater than the Split_Threshold, and allowlists that exact filename with
        an invalid justification (empty or longer than 280 characters). Asserts
        (1) an invalid-justification violation is produced naming the file (its
        message contains ``"invalid"`` and the quoted filename), and (2) the file
        is NOT exempt: exactly one over-threshold ("exceeds") violation is still
        produced for it, naming the filename, the integer ``token_count``, and the
        Split_Threshold (Requirement 4.6).
        """
        # token_count strictly over the threshold so the file is a split candidate.
        token_count = data.draw(st.integers(min_value=threshold + 1, max_value=1_000_000))
        file_metadata = {filename: {"token_count": token_count}}
        allowlist = [SplitAllowlistEntry(filename, invalid_justification)]

        violations = check_split_threshold(file_metadata, threshold, allowlist)

        # (1) The invalid-justification entry is flagged, naming the file.
        invalid_violations = [
            v for v in violations if "invalid" in v.message and f"'{filename}'" in v.message
        ]
        assert len(invalid_violations) == 1

        # (2) The file is NOT exempt: it is still flagged as over-threshold.
        over_threshold = [v for v in violations if "exceeds" in v.message]
        assert len(over_threshold) == 1
        message = over_threshold[0].message
        assert filename in message
        assert str(token_count) in message
        assert str(threshold) in message

    # Unit test: empty file_metadata yields zero violations.
    # Validates: Requirements 2.6
    def test_empty_file_metadata_yields_zero_violations(self) -> None:
        """An empty ``file_metadata`` map produces zero violations.

        Requirement 2.6: when the Steering_Index contains zero File_Metadata
        entries, the Split_Check must produce zero LintViolations. Calls
        ``check_split_threshold`` with an empty ``file_metadata`` map, a positive
        Split_Threshold, and an empty allowlist, and asserts the result is an
        empty list.
        """
        assert check_split_threshold({}, 5000, []) == []


# ---------------------------------------------------------------------------
# Integration tests for run_all_checks aggregation wiring
# ---------------------------------------------------------------------------


class TestRunAllChecksIntegration:
    """Integration tests for the Split_Check inside ``run_all_checks`` (Requirement 5.1)."""

    def test_over_threshold_file_surfaces_in_aggregate_results(self) -> None:
        """A known over-threshold file produces a Split_Check violation in the aggregate.

        Requirement 5.1: the Split_Check must run within the same ``run_all_checks``
        invocation as the existing lint rules and include its result in the
        aggregated violations. Builds an isolated temp directory structure — an
        (empty) steering dir, an (empty) hooks dir, and a minimal
        ``steering-index.yaml`` declaring ``budget.split_threshold_tokens`` and a
        single over-threshold ``file_metadata`` entry — then runs ``run_all_checks``
        against those temp paths. ``run_all_checks`` runs many other rules, so the
        aggregate may contain unrelated violations from the bare index; this test
        asserts only that the Split_Check over-threshold violation for the
        over-threshold file is PRESENT among the aggregated results.
        """
        threshold = 5000
        over_threshold_file = "module-99-phase1-oversized.md"
        token_count = 8192  # strictly greater than the threshold

        index_lines = [
            "budget:",
            f"  split_threshold_tokens: {threshold}",
            "file_metadata:",
            f"  {over_threshold_file}:",
            f"    token_count: {token_count}",
            "    size_category: large",
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            steering_dir = tmp_path / "steering"
            hooks_dir = tmp_path / "hooks"
            steering_dir.mkdir()
            hooks_dir.mkdir()
            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

            violations, _exit_code = run_all_checks(
                steering_dir,
                hooks_dir,
                index_path,
                warnings_as_errors=False,
                skip_template=False,
                split_severity="WARNING",
            )

        # The Split_Check over-threshold violation must be present in the aggregate.
        split_violations = [
            v
            for v in violations
            if "exceeds" in v.message and over_threshold_file in v.message
        ]
        assert len(split_violations) >= 1
        message = split_violations[0].message
        assert str(token_count) in message
        assert str(threshold) in message

    # ---- Exit-code behavior (Task 7.3; Requirements 3.2, 3.4, 3.5, 5.3, 5.4) ----
    #
    # ``run_all_checks`` runs MANY other lint rules (frontmatter, hook registry,
    # module numbering, index completeness, ...). Against a bare temp index those
    # rules can emit their own ERROR/WARNING violations, polluting the aggregate
    # exit code. So for the WARNING-alone case (Req 3.5, 5.4) we cannot reliably
    # assert ``exit_code == 0`` from the full aggregation. Instead we assert on the
    # Split_Check's exit-code CONTRIBUTION in isolation, using the linter's own
    # documented exit-code rule (mirrored in ``_linter_exit_code`` below):
    #   - ``--warnings-as-errors``: any violation fails;
    #   - otherwise: only ERROR-level violations fail.
    # The ERROR-severity and ``--warnings-as-errors`` cases (Req 3.2, 3.4, 5.3) are
    # additionally asserted directly against ``run_all_checks``'s exit code, since
    # those always fail regardless of any other rule's findings.

    @staticmethod
    def _make_over_threshold_index(
        tmp_path: Path,
        threshold: int,
        filename: str,
        token_count: int,
    ) -> tuple:
        """Create an isolated steering/hooks/index layout with one over-threshold file.

        Builds an (empty) steering dir, an (empty) hooks dir, and a minimal
        ``steering-index.yaml`` that declares ``budget.split_threshold_tokens`` and
        a single ``file_metadata`` entry whose ``token_count`` is strictly greater
        than ``threshold``.

        Args:
            tmp_path: Root temporary directory to populate.
            threshold: Split_Threshold to declare in the index budget block.
            filename: Steering filename for the single over-threshold entry.
            token_count: Token_Count for the entry (must exceed ``threshold``).

        Returns:
            Tuple of ``(steering_dir, hooks_dir, index_path)``.
        """
        steering_dir = tmp_path / "steering"
        hooks_dir = tmp_path / "hooks"
        steering_dir.mkdir()
        hooks_dir.mkdir()
        index_lines = [
            "budget:",
            f"  split_threshold_tokens: {threshold}",
            "file_metadata:",
            f"  {filename}:",
            f"    token_count: {token_count}",
            "    size_category: large",
        ]
        index_path = steering_dir / "steering-index.yaml"
        index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
        return steering_dir, hooks_dir, index_path

    @staticmethod
    def _split_over_threshold_violations(violations: list, filename: str) -> list:
        """Filter the aggregate down to the Split_Check over-threshold violation(s).

        The Split_Check over-threshold message names the file and states the count
        ``exceeds`` the Split_Threshold, so matching on both the ``"exceeds"`` token
        and the filename isolates the Split_Check's contribution from any unrelated
        violations the other rules emit against the bare temp index.
        """
        return [v for v in violations if "exceeds" in v.message and filename in v.message]

    @staticmethod
    def _linter_exit_code(violations: list, warnings_as_errors: bool) -> int:
        """Mirror ``run_all_checks``'s documented exit-code rule for a violations list.

        Replicates the exit-code computation in ``run_all_checks`` exactly: under
        ``--warnings-as-errors`` any violation is failing; otherwise only
        ERROR-level violations are failing. Applying this to ONLY the Split_Check
        violations lets the WARNING-alone assertion (Req 3.5, 5.4) be deterministic
        regardless of what the other lint rules emit against the bare temp index.
        """
        if warnings_as_errors:
            has_issues = any(True for _ in violations)
        else:
            has_issues = any(v.level == "ERROR" for v in violations)
        return 1 if has_issues else 0

    def test_error_severity_split_violation_always_fails(self) -> None:
        """An ERROR-severity over-threshold violation fails the linter unconditionally.

        Requirements 3.4 and 5.3: when a Split_Check violation has ``level``
        ``ERROR``, the linter returns a non-zero exit code even without
        ``--warnings-as-errors``. Runs ``run_all_checks`` over an over-threshold
        temp index with ``split_severity="ERROR"`` and ``warnings_as_errors=False``,
        asserts the Split_Check over-threshold violation is present at ``ERROR``
        level, that the aggregate exit code is non-zero, and that the ERROR split
        violation alone is sufficient to fail under the linter's exit-code rule.
        """
        threshold = 5000
        filename = "module-99-phase1-oversized.md"
        token_count = 8192  # strictly greater than the threshold

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir, hooks_dir, index_path = self._make_over_threshold_index(
                Path(tmp_dir), threshold, filename, token_count
            )
            violations, exit_code = run_all_checks(
                steering_dir,
                hooks_dir,
                index_path,
                warnings_as_errors=False,
                skip_template=False,
                split_severity="ERROR",
            )

        split = self._split_over_threshold_violations(violations, filename)
        assert len(split) == 1
        assert split[0].level == "ERROR"
        # ERROR always fails, even without --warnings-as-errors (Req 3.4, 5.3).
        assert exit_code != 0
        # The ERROR split violation on its own is sufficient to fail the linter.
        assert self._linter_exit_code(split, warnings_as_errors=False) == 1

    def test_warning_severity_split_violation_fails_under_warnings_as_errors(self) -> None:
        """A WARNING-severity over-threshold violation fails under --warnings-as-errors.

        Requirement 3.2: when run with ``--warnings-as-errors``, each WARNING-level
        Split_Check violation counts as failing for exit-code determination. Runs
        ``run_all_checks`` over an over-threshold temp index with
        ``split_severity="WARNING"`` and ``warnings_as_errors=True``, asserts the
        Split_Check over-threshold violation is present at ``WARNING`` level, that
        the aggregate exit code is non-zero, and that the WARNING split violation
        alone fails under ``--warnings-as-errors`` per the linter's exit-code rule.
        """
        threshold = 5000
        filename = "module-99-phase1-oversized.md"
        token_count = 8192  # strictly greater than the threshold

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir, hooks_dir, index_path = self._make_over_threshold_index(
                Path(tmp_dir), threshold, filename, token_count
            )
            violations, exit_code = run_all_checks(
                steering_dir,
                hooks_dir,
                index_path,
                warnings_as_errors=True,
                skip_template=False,
                split_severity="WARNING",
            )

        split = self._split_over_threshold_violations(violations, filename)
        assert len(split) == 1
        assert split[0].level == "WARNING"
        # Under --warnings-as-errors any violation fails (Req 3.2).
        assert exit_code != 0
        # The WARNING split violation alone fails under --warnings-as-errors.
        assert self._linter_exit_code(split, warnings_as_errors=True) == 1

    def test_warning_severity_split_violation_does_not_fail_by_itself(self) -> None:
        """A WARNING-severity over-threshold violation does not by itself fail the linter.

        Requirements 3.5 and 5.4: with no ``ERROR``-level Split_Check violation and
        without ``--warnings-as-errors``, the Split_Check does not by itself cause a
        non-zero exit code. Because ``run_all_checks`` runs many other rules that may
        emit their own ERRORs against the bare temp index (polluting the aggregate
        exit code), this asserts on the Split_Check's CONTRIBUTION in isolation: the
        Split_Check emits only ``WARNING``-level findings here, and applying the
        linter's documented exit-code rule to just those findings yields a clean exit
        (0) without ``--warnings-as-errors`` and a failing exit (1) with it.
        """
        threshold = 5000
        filename = "module-99-phase1-oversized.md"
        token_count = 8192  # strictly greater than the threshold

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir, hooks_dir, index_path = self._make_over_threshold_index(
                Path(tmp_dir), threshold, filename, token_count
            )
            violations, _exit_code = run_all_checks(
                steering_dir,
                hooks_dir,
                index_path,
                warnings_as_errors=False,
                skip_template=False,
                split_severity="WARNING",
            )

        split = self._split_over_threshold_violations(violations, filename)
        assert len(split) == 1
        # The Split_Check contributes only WARNING-level findings here, so it adds
        # no ERROR of its own (Req 3.5, 5.4).
        assert all(v.level == "WARNING" for v in split)
        # WARNING alone does not fail without --warnings-as-errors ...
        assert self._linter_exit_code(split, warnings_as_errors=False) == 0
        # ... but the same WARNING violation does fail under --warnings-as-errors.
        assert self._linter_exit_code(split, warnings_as_errors=True) == 1

    # ---- Output format (Task 7.4; Requirement 5.5) ----

    def test_split_violation_uses_lintviolation_format(self) -> None:
        """Printed Split_Check lines use ``LintViolation.format()`` with file/count/threshold.

        Requirement 5.5: when the Split_Check produces violations, the linter prints
        each one using the existing violation output format, identifying the file
        path, Token_Count, and Split_Threshold. Builds an over-threshold temp index
        (same pattern as the aggregation test), runs ``run_all_checks`` to obtain the
        aggregated violations, isolates the Split_Check over-threshold violation, and
        asserts on ``violation.format()`` directly (more robust than capturing
        stdout).

        Note: ``check_split_threshold`` hard-codes ``file=str(INDEX_PATH)`` (the
        module-level constant ``senzing-bootcamp/steering/steering-index.yaml``), so
        the violation's ``file`` is always that path regardless of the temp index
        location. The formatted line is therefore asserted to contain ``INDEX_PATH``
        rather than the temp path.
        """
        threshold = 5000
        filename = "module-99-phase1-oversized.md"
        token_count = 8192  # strictly greater than the threshold

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir, hooks_dir, index_path = self._make_over_threshold_index(
                Path(tmp_dir), threshold, filename, token_count
            )
            violations, _exit_code = run_all_checks(
                steering_dir,
                hooks_dir,
                index_path,
                warnings_as_errors=False,
                skip_template=False,
                split_severity="WARNING",
            )

        split = self._split_over_threshold_violations(violations, filename)
        assert len(split) == 1
        violation = split[0]

        formatted = violation.format()

        # (a) The formatted line is produced by LintViolation.format(): it equals the
        # documented "{level}: {file}:{line}: {message}" shape exactly.
        assert formatted == (
            f"{violation.level}: {violation.file}:{violation.line}: {violation.message}"
        )
        # (b) It starts with the violation's level.
        assert formatted.startswith(violation.level)
        # (c) It contains the file path. check_split_threshold keys the violation to
        # the module-level INDEX_PATH constant, not the temp index path.
        assert str(INDEX_PATH) in formatted
        assert "steering-index.yaml" in formatted
        # (d) It contains the integer Token_Count and the Split_Threshold.
        assert str(token_count) in formatted
        assert str(threshold) in formatted


# ---------------------------------------------------------------------------
# CLI argument validation (Task 7.5; Requirement 3.7, CLI boundary)
# ---------------------------------------------------------------------------


class TestCliSplitSeverity:
    """CLI-boundary tests for ``--split-severity`` validation (Requirement 3.7)."""

    def test_invalid_split_severity_exits_non_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An out-of-choices ``--split-severity`` value exits non-zero with an error.

        Requirement 3.7 at the CLI boundary: ``main()`` builds its argparse parser
        with ``--split-severity`` constrained to ``choices=["WARNING", "ERROR"]`` and
        calls ``parser.parse_args()`` (which reads ``sys.argv``). Supplying a value
        outside those choices must make argparse reject it — raising ``SystemExit``
        with a non-zero code (argparse uses ``2``) and writing an error to stderr —
        rather than silently defaulting to ``WARNING``.

        ``main()`` calls ``require_runtime()`` first (fine on a supported
        interpreter) and then ``parse_args()``; argparse rejects the invalid choice
        during parsing, before ``run_all_checks`` runs, so no valid index needs to
        be staged.
        """
        monkeypatch.setattr(
            sys, "argv", ["lint_steering.py", "--split-severity", "INVALID"]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits non-zero (code 2) for an invalid choice; assert non-zero
        # rather than silently defaulting.
        assert exc_info.value.code != 0
        assert exc_info.value.code == 2

        # The error is written to stderr and identifies the offending argument.
        stderr = capsys.readouterr().err
        assert "split-severity" in stderr
        assert "invalid choice" in stderr


# ---------------------------------------------------------------------------
# Real-corpus smoke test (Task 8.1; Requirement 5.6)
# ---------------------------------------------------------------------------


class TestRealCorpusSmoke:
    """Smoke test the Split_Check against the real ``steering-index.yaml``."""

    # Feature: steering-split-threshold-enforcement, Requirement 5.6: the
    # Split_Check must surface the known over-threshold files in the live corpus.
    # Validates: Requirements 5.6
    def test_known_over_threshold_files_are_reported(self) -> None:
        """The real index reports the four known over-threshold steering files.

        Runs the Split_Check against the actual
        ``senzing-bootcamp/steering/steering-index.yaml`` with an empty allowlist
        (so any real exemptions are ignored for this assertion) and asserts that
        ``hook-registry-critical.md``, ``graduation.md``,
        ``module-05-phase2-data-mapping.md``, and ``module-01-phase1-discovery.md``
        are each reported as over-threshold. The over-threshold violations are the
        ones whose message contains ``"exceeds"`` (Requirement 5.6).
        """
        # CI invokes pytest from the repo root, where ``INDEX_PATH`` (a repo-root-
        # relative path) resolves directly. Fall back to a path derived from this
        # test file's location so the test is robust to the working directory.
        index_path = INDEX_PATH
        if not index_path.exists():
            index_path = (
                Path(__file__).resolve().parents[2]
                / "senzing-bootcamp/steering/steering-index.yaml"
            )
        assert index_path.exists(), f"steering index not found at {index_path}"

        file_metadata = parse_steering_index(index_path).get("file_metadata", {})
        threshold = get_split_threshold(index_path)

        violations = check_split_threshold(file_metadata, threshold, [])

        over_threshold_files = {
            filename
            for filename in file_metadata
            for violation in violations
            if "exceeds" in violation.message and f"'{filename}'" in violation.message
        }

        expected = {
            "hook-registry-critical.md",
            "graduation.md",
            "module-05-phase2-data-mapping.md",
            "module-01-phase1-discovery.md",
        }
        missing = expected - over_threshold_files
        assert not missing, (
            f"expected over-threshold files not reported by the Split_Check: "
            f"{sorted(missing)} (reported: {sorted(over_threshold_files)})"
        )


class TestCiConfiguration:
    """Smoke test the CI workflow wiring for the Split_Check (Requirement 5.2)."""

    @staticmethod
    def _read_workflow() -> str:
        """Return the text of ``.github/workflows/validate-power.yml``.

        Locates the workflow robustly: the test file lives at
        ``senzing-bootcamp/tests/``, so ``parents[2]`` is the repo root, mirroring
        the path approach used by ``TestRealCorpusSmoke``. Falls back to a
        working-directory-relative path so the test is robust to where pytest is
        invoked from.

        Returns:
            The workflow file contents as text.
        """
        workflow_path = Path(__file__).resolve().parents[2] / ".github/workflows/validate-power.yml"
        if not workflow_path.exists():
            workflow_path = Path(".github/workflows/validate-power.yml")
        assert workflow_path.exists(), f"workflow not found at {workflow_path}"
        return workflow_path.read_text(encoding="utf-8")

    # Feature: steering-split-threshold-enforcement, Requirement 5.2: the
    # Split_Check runs inside the existing, unchanged "Lint steering files" step.
    # Validates: Requirements 5.2
    def test_lint_steering_step_invokes_linter_without_new_flags(self) -> None:
        """The "Lint steering files" step runs ``lint_steering.py`` with no new flags.

        Asserts a step whose name contains "Lint steering files" exists and that
        its ``run`` invokes ``lint_steering.py`` using the existing invocation —
        i.e. the Split_Check runs inside the default ``WARNING`` behavior with no
        added ``--split-severity ERROR`` flag and no separate split-check step.
        """
        content = self._read_workflow()
        lines = content.splitlines()

        # Locate the "Lint steering files" step and its associated run line.
        step_indices = [
            i for i, line in enumerate(lines) if "Lint steering files" in line and "name:" in line
        ]
        assert len(step_indices) == 1, (
            f"expected exactly one 'Lint steering files' step, found {len(step_indices)}"
        )
        step_index = step_indices[0]

        # The run command follows the step name; scan forward to the next run line.
        run_lines = [
            line
            for line in lines[step_index + 1 : step_index + 4]
            if "run:" in line and "lint_steering.py" in line
        ]
        assert run_lines, "'Lint steering files' step does not invoke lint_steering.py"
        run_line = run_lines[0]

        # Existing invocation: python ... lint_steering.py, with no new required flag.
        assert "lint_steering.py" in run_line
        assert "--split-severity ERROR" not in run_line
        assert "--split-severity" not in run_line

        # No separate/new split-check step or invocation elsewhere in the workflow.
        assert "--split-severity" not in content
        assert content.count("lint_steering.py") == 1

    # Feature: steering-split-threshold-enforcement, Requirement 5.2: the
    # Split_Check runs across the Python 3.11/3.12/3.13 test matrix.
    # Validates: Requirements 5.2
    def test_test_matrix_lists_python_3_11_3_12_3_13(self) -> None:
        """The test job matrix lists Python 3.11, 3.12, and 3.13.

        Asserts the workflow declares a ``python-version`` matrix and that each of
        ``3.11``, ``3.12``, and ``3.13`` appears as a matrix value.
        """
        content = self._read_workflow()

        matrix_lines = [
            line for line in content.splitlines() if "python-version:" in line and "[" in line
        ]
        assert matrix_lines, "no python-version matrix list found in the workflow"
        matrix_line = matrix_lines[0]

        for version in ("3.11", "3.12", "3.13"):
            assert version in matrix_line, f"Python {version} missing from the test matrix"
