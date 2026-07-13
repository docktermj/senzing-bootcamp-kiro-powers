"""Property-based tests for the TruthSet fallback source acquisition script.

Validates the correctness properties from the ``truthset-fallback-source``
design document against ``scripts/fetch_fallback_truthset.py``. Each property
lives in its own test class; shared Hypothesis strategies (prefixed ``st_``) are
declared in the strategies section below so later property tasks can append new
classes and strategies to this file cleanly.

Feature: truthset-fallback-source
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.error
from pathlib import Path
from unittest import mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from fetch_fallback_truthset import (
    FetchedContent,
    FetchError,
    ValidationError,
    derive_expected_results,
    fetch_file,
    normalize_records,
    validate_jsonl,
)

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Characters safe for JSONL round-tripping:
#   * Exclude surrogate code points (category ``Cs``) so every generated string
#     serializes to a UTF-8 file without raising ``UnicodeEncodeError``.
#   * Exclude the three Unicode line separators ``json.dumps`` leaves literal
#     (NEL U+0085, LS U+2028, PS U+2029). C0 controls are escaped by
#     ``json.dumps`` and stay on one line, but these three would be treated as
#     record boundaries by the line-delimited normalizer, which is outside the
#     realistic TruthSet input space (mirrors the ``_SAFE_CSV_CHARS`` precedent
#     in the data-validation property suite).
_SAFE_CHARS = st.characters(
    blacklist_categories=("Cs",),
    blacklist_characters="\x85\u2028\u2029",
)

# Record field values: JSON scalars that round-trip losslessly through
# ``json.dumps``/``json.loads`` (text and bounded integers only — no floats,
# so NaN/Infinity equality quirks never enter the comparison).
_RECORD_VALUE = st.one_of(
    st.text(_SAFE_CHARS, max_size=20),
    st.integers(min_value=-1_000_000, max_value=1_000_000),
)

# Extra field names are prefixed so they can never collide with the base
# ``RECORD_ID``/``NAME_FULL``/``DATA_SOURCE`` fields.
_EXTRA_FIELD_NAME = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=6
).map(lambda word: f"FIELD_{word.upper()}")


@st.composite
def st_truthset_record(draw) -> dict:
    """Draw one Senzing-ish TruthSet record as a JSON object.

    Every record carries ``RECORD_ID`` and ``NAME_FULL``. A ``DATA_SOURCE``
    field is present only some of the time so both normalizer branches (added
    when absent, preserved when present) are exercised. Optional extra fields
    use a ``FIELD_`` prefix so they never shadow the base fields.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A record dict with JSON-serializable scalar values.
    """
    record: dict = {
        "RECORD_ID": draw(
            st.one_of(
                st.text(_SAFE_CHARS, min_size=1, max_size=12),
                st.integers(min_value=0, max_value=100_000),
            )
        ),
        "NAME_FULL": draw(st.text(_SAFE_CHARS, max_size=30)),
    }
    if draw(st.booleans()):
        record["DATA_SOURCE"] = draw(st.text(_SAFE_CHARS, min_size=1, max_size=12))
    extra = draw(
        st.dictionaries(keys=_EXTRA_FIELD_NAME, values=_RECORD_VALUE, max_size=3)
    )
    record.update(extra)
    return record


@st.composite
def st_truthset_records(draw) -> list[dict]:
    """Draw a list of valid TruthSet records.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A (possibly empty) list of record dicts.
    """
    return draw(st.lists(st_truthset_record(), max_size=8))


@st.composite
def st_source_files(draw) -> dict[str, list[dict]]:
    """Draw one or more source files, each a filename mapped to its records.

    Filenames are distinct ``<stem>.jsonl`` names; the stem drives the
    ``DATA_SOURCE`` label the normalizer derives, so keeping stems unique keeps
    each file's derived data source well defined.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A mapping of source filename to its list of records.
    """
    stems = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    return {f"{stem}.jsonl": draw(st_truthset_records()) for stem in stems}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _serialize_source(records: list[dict]) -> str:
    """Serialize a record list into source JSONL text (one object per line).

    Args:
        records: The records to serialize.

    Returns:
        JSONL text with a trailing newline per record (empty for no records).
    """
    return "".join(f"{json.dumps(record, ensure_ascii=False)}\n" for record in records)


def _expected_records(source_files: dict[str, list[dict]]) -> list[dict]:
    """Compute the expected normalized record set for ``source_files``.

    Mirrors the normalizer's contract: iterate files in order, and add a
    ``DATA_SOURCE`` derived from the filename stem (upper-cased) only when the
    record lacks one.

    Args:
        source_files: Mapping of source filename to its records.

    Returns:
        The expected list of records after normalization.
    """
    expected: list[dict] = []
    for filename, records in source_files.items():
        data_source = Path(filename).stem.upper()
        for record in records:
            normalized = dict(record)
            if "DATA_SOURCE" not in normalized:
                normalized["DATA_SOURCE"] = data_source
            expected.append(normalized)
    return expected


def _reparse_jsonl(output_path: Path) -> list[dict]:
    """Parse a JSONL file back into a list of records, skipping blank lines.

    Args:
        output_path: Path to the normalized JSONL file.

    Returns:
        The parsed records in file order.
    """
    return [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ---------------------------------------------------------------------------
# Property 4: Normalization Round-Trip
# ---------------------------------------------------------------------------


class TestNormalizationRoundTrip:
    """Property-based tests for the normalization round-trip.

    Feature: truthset-fallback-source, Property 4: Normalization Round-Trip

    For any valid set of TruthSet records, parsing the source JSONL
    representation, serializing to the TruthSet_Data_File via
    ``normalize_records``, and parsing that file again yields an equivalent
    record set (identical field names, values, and record count), accounting for
    the ``DATA_SOURCE``-added-when-absent normalization behavior.

    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    @given(source_files=st_source_files())
    def test_normalization_round_trip(self, source_files: dict[str, list[dict]]) -> None:
        """Re-parsing normalized output yields the expected record set.

        Args:
            source_files: Generated mapping of source filename to records.
        """
        fetched = FetchedContent(
            records={
                filename: _serialize_source(records)
                for filename, records in source_files.items()
            }
        )
        expected = _expected_records(source_files)

        tmp_dir = tempfile.mkdtemp()
        try:
            output_path = Path(tmp_dir) / "truthset_data.jsonl"
            records_written = normalize_records(fetched, output_path)

            # Record count is preserved end to end.
            assert records_written == len(expected), (
                f"Expected {len(expected)} records written, got {records_written}"
            )

            reparsed = _reparse_jsonl(output_path)

            # The line count equals the number of source records (Req 4.2).
            assert len(reparsed) == len(expected), (
                f"Expected {len(expected)} lines, got {len(reparsed)}"
            )
            # Field names and values round-trip to an equivalent record set.
            assert reparsed == expected, (
                "Round-tripped record set differs from the expected normalized set"
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 5 strategies: JSONL content that must fail validation
# ---------------------------------------------------------------------------

# Characters safe to embed in a single JSONL line. Excluding surrogates (``Cs``)
# keeps the content UTF-8 encodable, and excluding all control characters
# (``Cc`` — which covers ``\n``, ``\r``, ``\t``) plus the three literal Unicode
# line separators guarantees a generated "line" never spans multiple physical
# lines when written to the output file.
_LINE_SAFE_CHARS = st.characters(
    blacklist_categories=("Cs", "Cc"),
    blacklist_characters="\x85\u2028\u2029",
)


@st.composite
def st_invalid_json_line(draw) -> str:
    """Draw a single line that is guaranteed not to be valid JSON.

    A leading ``}`` makes the line an invalid JSON value regardless of any
    trailing text, so ``json.loads`` rejects it at the first character.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-blank string that ``json.loads`` cannot parse.
    """
    trailing = draw(st.text(_LINE_SAFE_CHARS, max_size=20))
    return "}" + trailing


@st.composite
def st_invalid_jsonl_content(draw) -> tuple[str, int]:
    """Draw JSONL file content containing at least one non-JSON line.

    Valid serialized records are interleaved with one or more guaranteed-invalid
    lines, then shuffled so the invalid line is not always in a fixed position.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(content, non_blank_line_count)`` tuple. ``content`` is JSONL text
        with a trailing newline per line; ``non_blank_line_count`` is the number
        of non-blank lines it contains (what the validator counts).
    """
    valid_lines = [
        json.dumps(record, ensure_ascii=False)
        for record in draw(st_truthset_records())
    ]
    invalid_lines = draw(st.lists(st_invalid_json_line(), min_size=1, max_size=3))
    all_lines = draw(st.permutations(valid_lines + invalid_lines))
    content = "".join(f"{line}\n" for line in all_lines)
    return content, len(all_lines)


@st.composite
def st_valid_jsonl_with_mismatched_count(draw) -> tuple[str, int]:
    """Draw a fully valid JSONL file paired with a wrong expected record count.

    Every line is a valid JSON object, so the JSON-validity check passes and only
    the line-count check can fail. The returned expected count always differs
    from the file's actual non-blank line count.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(content, wrong_expected_count)`` tuple where ``wrong_expected_count``
        never equals the file's non-blank line count.
    """
    lines = [
        json.dumps(record, ensure_ascii=False)
        for record in draw(st_truthset_records())
    ]
    content = "".join(f"{line}\n" for line in lines)
    actual_count = len(lines)
    offset = draw(st.integers(min_value=1, max_value=10))
    if draw(st.booleans()) and actual_count - offset >= 0:
        wrong_expected_count = actual_count - offset
    else:
        wrong_expected_count = actual_count + offset
    return content, wrong_expected_count


# ---------------------------------------------------------------------------
# Property 5: JSONL Validation Detects Errors
# ---------------------------------------------------------------------------


class TestJsonlValidationDetectsErrors:
    """Property-based tests for JSONL validation error detection.

    Feature: truthset-fallback-source, Property 5: JSONL Validation Detects Errors

    For any TruthSet_Data_File that contains at least one line that is not valid
    JSON, or whose non-blank line count does not match the expected record count,
    ``validate_jsonl`` raises ``ValidationError`` (reporting failure and blocking
    progression to data loading). Conversely, a well-formed file whose count
    matches does not raise (optional strengthening).

    **Validates: Requirements 4.4**
    """

    @given(content_and_count=st_invalid_jsonl_content())
    def test_invalid_json_line_detected(
        self, content_and_count: tuple[str, int]
    ) -> None:
        """A file with any non-JSON line raises ``ValidationError``.

        The expected count is set to the file's non-blank line count so the
        line-count check would pass, isolating the invalid-JSON detection.

        Args:
            content_and_count: Generated ``(content, non_blank_line_count)``.
        """
        content, non_blank_line_count = content_and_count

        tmp_dir = tempfile.mkdtemp()
        try:
            output_path = Path(tmp_dir) / "truthset_data.jsonl"
            output_path.write_text(content, encoding="utf-8")
            with pytest.raises(ValidationError):
                validate_jsonl(output_path, non_blank_line_count)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @given(content_and_count=st_valid_jsonl_with_mismatched_count())
    def test_count_mismatch_detected(
        self, content_and_count: tuple[str, int]
    ) -> None:
        """A valid-JSON file whose count mismatches raises ``ValidationError``.

        Args:
            content_and_count: Generated ``(content, wrong_expected_count)``.
        """
        content, wrong_expected_count = content_and_count

        tmp_dir = tempfile.mkdtemp()
        try:
            output_path = Path(tmp_dir) / "truthset_data.jsonl"
            output_path.write_text(content, encoding="utf-8")
            with pytest.raises(ValidationError):
                validate_jsonl(output_path, wrong_expected_count)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @given(records=st_truthset_records())
    def test_well_formed_file_with_matching_count_passes(
        self, records: list[dict]
    ) -> None:
        """A well-formed file whose count matches does not raise (control).

        Args:
            records: Generated valid records, serialized one per line.
        """
        content = "".join(
            f"{json.dumps(record, ensure_ascii=False)}\n" for record in records
        )

        tmp_dir = tempfile.mkdtemp()
        try:
            output_path = Path(tmp_dir) / "truthset_data.jsonl"
            output_path.write_text(content, encoding="utf-8")
            # Should complete without raising.
            validate_jsonl(output_path, len(records))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 6 strategies: valid truth-key CSV text
# ---------------------------------------------------------------------------

# Alphanumeric alphabet for CSV field values and header stems. Restricting to
# alphanumerics keeps every generated cell free of commas, quotes, and newlines,
# so the CSV text can be assembled by simple comma joins without any escaping
# and still parse back exactly as intended (mirrors the KEY GENERATOR guidance
# for this property).
_CSV_SAFE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

# A single non-empty alphanumeric token used for CLUSTER_ID, RECORD_ID, and
# DATA_SOURCE values. Non-empty so derive_expected_results never skips the row.
_CSV_TOKEN = st.text(alphabet=_CSV_SAFE_ALPHABET, min_size=1, max_size=8)

# Extra (ignored) column names, prefixed so they can never collide with the
# three required columns after the deriver's case-insensitive matching.
_EXTRA_COLUMN_NAME = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=6
).map(lambda word: f"EXTRA_{word.upper()}")


@st.composite
def st_valid_truth_key_csv(draw) -> str:
    """Draw valid truth-key CSV text guaranteed to yield >= 3 multi-record clusters.

    The generated CSV always declares the three required columns (``CLUSTER_ID``,
    ``RECORD_ID``, ``DATA_SOURCE``) and lays out at least three distinct clusters,
    each owning 2+ rows with globally-unique ``RECORD_ID`` values. Because every
    record identifier is unique, each cluster resolves to 2+ distinct
    ``DATA_SOURCE:RECORD_ID`` members, so ``derive_expected_results`` always
    succeeds and returns at least three known matches.

    To exercise the deriver's tolerance, required-column headers get randomized
    case, optional extra columns are mixed in, the column order is shuffled, and a
    UTF-8 BOM may prefix the file (immediately before the first header, as a real
    file would carry it).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        Valid truth-key CSV text (header row plus data rows, one row per line).
    """
    n_clusters = draw(st.integers(min_value=3, max_value=6))
    cluster_ids = draw(
        st.lists(_CSV_TOKEN, min_size=n_clusters, max_size=n_clusters, unique=True)
    )
    record_counts = [draw(st.integers(min_value=2, max_value=4)) for _ in cluster_ids]
    total_records = sum(record_counts)
    record_ids = draw(
        st.lists(_CSV_TOKEN, min_size=total_records, max_size=total_records, unique=True)
    )
    data_sources = [draw(_CSV_TOKEN) for _ in range(total_records)]

    # Build one logical row per record, keyed by the required column roles.
    logical_rows: list[dict[str, str]] = []
    index = 0
    for cluster_id, count in zip(cluster_ids, record_counts):
        for _ in range(count):
            logical_rows.append(
                {
                    "CLUSTER_ID": cluster_id,
                    "RECORD_ID": record_ids[index],
                    "DATA_SOURCE": data_sources[index],
                }
            )
            index += 1

    def _decorate(column: str) -> str:
        """Apply tolerated case variation to a required column header."""
        variant = draw(st.sampled_from(("upper", "lower", "title")))
        return {
            "upper": column.upper(),
            "lower": column.lower(),
            "title": column.title(),
        }[variant]

    header_by_role = {role: _decorate(role) for role in ("CLUSTER_ID", "RECORD_ID", "DATA_SOURCE")}
    role_by_header = {header: role for role, header in header_by_role.items()}

    extra_columns = draw(st.lists(_EXTRA_COLUMN_NAME, max_size=2, unique=True))
    ordered_columns = draw(st.permutations(list(header_by_role.values()) + extra_columns))

    lines = [",".join(ordered_columns)]
    for logical in logical_rows:
        cells: list[str] = []
        for column in ordered_columns:
            role = role_by_header.get(column)
            if role is not None:
                cells.append(logical[role])
            else:
                cells.append(draw(st.text(alphabet=_CSV_SAFE_ALPHABET, max_size=6)))
        lines.append(",".join(cells))

    prefix = "\ufeff" if draw(st.booleans()) else ""
    return prefix + "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Property 6: Expected Results Structural Completeness
# ---------------------------------------------------------------------------


class TestExpectedResultsStructuralCompleteness:
    """Property-based tests for expected-results structural completeness.

    Feature: truthset-fallback-source, Property 6: Expected Results Structural Completeness

    For any Fallback_Expected_Results derived from a valid truth-key CSV (one that
    yields at least three multi-record clusters), ``derive_expected_results``
    returns a structure whose ``expected_entity_count`` is a positive integer and
    whose ``known_matches`` holds at least three entries, each listing 2+ record
    identifiers. The fixed ``tolerance_percent`` and ``source`` labels are checked
    as well so Step 7 deterministic verification can consume the result unchanged.

    **Validates: Requirements 5.2**
    """

    @given(truth_key_csv=st_valid_truth_key_csv())
    def test_expected_results_structural_completeness(self, truth_key_csv: str) -> None:
        """Derived results carry a positive count and >= 3 multi-record matches.

        Args:
            truth_key_csv: Generated valid truth-key CSV text.
        """
        expected = derive_expected_results(truth_key_csv)

        entity_count = expected["expected_entity_count"]
        # A positive integer entity count (bool is excluded despite subclassing int).
        assert isinstance(entity_count, int) and not isinstance(entity_count, bool), (
            f"expected_entity_count must be an int, got {type(entity_count).__name__}"
        )
        assert entity_count > 0, f"expected_entity_count must be positive, got {entity_count}"

        known_matches = expected["known_matches"]
        assert len(known_matches) >= 3, (
            f"expected at least 3 known matches, got {len(known_matches)}"
        )
        for entry in known_matches:
            assert len(entry["records"]) >= 2, (
                f"known match {entry['entity_label']!r} must list 2+ records, "
                f"got {len(entry['records'])}"
            )

        # Fixed metadata Step 7 relies on.
        assert expected["tolerance_percent"] == 5
        assert expected["source"] == "github_fallback"


# ---------------------------------------------------------------------------
# Property 3 strategies: HTTP status codes outside the 200 range
# ---------------------------------------------------------------------------

# Common real-world HTTP error codes exercised explicitly alongside the broad
# integer sweeps below, so the generator always covers the statuses a fallback
# source realistically returns (auth, rate limiting, server errors).
_COMMON_HTTP_ERROR_CODES = (400, 401, 403, 404, 408, 409, 410, 429, 500, 501, 502, 503, 504)


@st.composite
def st_http_error_status(draw) -> int:
    """Draw an HTTP status code outside the 200 (success) range.

    Mixes the common error codes above with broad integer sweeps over the 1xx,
    3xx, 4xx, and 5xx ranges. Every drawn value lies outside 200-299, so it is
    always a non-success status that ``fetch_file`` must classify as unreachable.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An integer HTTP status code that is never in the 200-299 range.
    """
    return draw(
        st.one_of(
            st.sampled_from(_COMMON_HTTP_ERROR_CODES),
            st.integers(min_value=100, max_value=199),
            st.integers(min_value=300, max_value=399),
            st.integers(min_value=400, max_value=599),
        )
    )


@st.composite
def st_record_filename(draw) -> str:
    """Draw a digit-free record filename ending in ``.jsonl``.

    Keeping the stem alphabetic guarantees the only digits in the eventual error
    message come from the status code, so asserting the code appears in the
    message can never be satisfied by a digit that leaked in from the filename.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``<stem>.jsonl`` filename whose stem is lowercase ASCII letters.
    """
    stem = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12))
    return f"{stem}.jsonl"


# Base URL used only to exercise ``fetch_file`` under a mocked ``urlopen``. It is
# a placeholder (never actually contacted) and deliberately not the real
# sanctioned fallback URL, which lives solely in config/fallback_sources.yaml.
_FETCH_BASE_URL = "https://fallback.example/truthsets/demo"


# ---------------------------------------------------------------------------
# Property 3: HTTP Error Classification
# ---------------------------------------------------------------------------


class TestHttpErrorClassification:
    """Property-based tests for HTTP error classification.

    Feature: truthset-fallback-source, Property 3: HTTP Error Classification

    For any HTTP response status code outside the 200 range returned by the
    fallback source, ``fetch_file`` classifies the source as unreachable (raises
    ``FetchError``) and records the specific status code -- its digits appear in
    the raised error's ``message``. Both ways a non-success status surfaces are
    exercised: an ``HTTPError`` raised by ``urlopen`` (how real error statuses
    arrive through urllib) and a response object reporting a non-200 ``getcode()``.

    **Validates: Requirements 3.4**
    """

    @given(status_code=st_http_error_status(), filename=st_record_filename())
    def test_http_error_raised_records_status_code(
        self, status_code: int, filename: str
    ) -> None:
        """An ``HTTPError`` from ``urlopen`` becomes a ``FetchError`` w/ the code.

        Args:
            status_code: Generated non-success HTTP status code.
            filename: Generated record filename being fetched.
        """
        http_error = urllib.error.HTTPError(
            url=f"{_FETCH_BASE_URL}/{filename}",
            code=status_code,
            msg="error",
            hdrs=None,
            fp=None,
        )
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=http_error,
        ):
            with pytest.raises(FetchError) as exc_info:
                fetch_file(_FETCH_BASE_URL, filename, timeout=30)

        assert str(status_code) in exc_info.value.message, (
            f"status code {status_code} not recorded in error message "
            f"{exc_info.value.message!r}"
        )

    @given(status_code=st_http_error_status(), filename=st_record_filename())
    def test_non_200_response_records_status_code(
        self, status_code: int, filename: str
    ) -> None:
        """A response reporting a non-200 ``getcode()`` yields a ``FetchError``.

        Args:
            status_code: Generated non-success HTTP status code.
            filename: Generated record filename being fetched.
        """
        response = mock.MagicMock()
        response.getcode.return_value = status_code
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            return_value=response,
        ):
            with pytest.raises(FetchError) as exc_info:
                fetch_file(_FETCH_BASE_URL, filename, timeout=30)

        assert str(status_code) in exc_info.value.message, (
            f"status code {status_code} not recorded in error message "
            f"{exc_info.value.message!r}"
        )


# ---------------------------------------------------------------------------
# Property 1: reference-model import
# ---------------------------------------------------------------------------

# The Availability Classifier is agent logic that lives in the Step 2 steering,
# not a shipped power script, so its behavior is verified against a pure reference
# model co-located in this tests/ directory (mirrors how
# ``test_reclassify_steering_properties.py`` imports ``reclassify_steering_model``).
# Put the tests directory on ``sys.path`` so a direct import resolves regardless of
# the pytest import mode / invocation cwd.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from truthset_fallback_model import (  # noqa: E402
    AVAILABLE,
    CORD_COLLECTION_NAMES,
    RESPONSE_CONTAINER_KEYS,
    UNAVAILABLE,
    classify_availability,
)

# ---------------------------------------------------------------------------
# Property 1 strategies: get_sample_data-style responses + expected label
# ---------------------------------------------------------------------------


@st.composite
def st_truthset_name(draw) -> str:
    """Draw a dataset name that the classifier reads as a named TruthSet.

    Every variant contains the ``truthset`` token once internal spaces are
    ignored, so the classifier's name check matches regardless of surrounding
    words or letter case.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A TruthSet-style dataset name (e.g. ``"TruthSet"``, ``"Senzing TruthSet"``).
    """
    return draw(
        st.sampled_from(
            [
                "TruthSet",
                "truthset",
                "TRUTHSET",
                "TruthSet Demo",
                "Senzing TruthSet",
                "Truth Set",
            ]
        )
    )


@st.composite
def st_truthset_type(draw) -> str:
    """Draw a ``type`` value that normalizes exactly to ``truthset``.

    Case and surrounding whitespace vary so the classifier's trimmed,
    lower-cased comparison is exercised.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A string whose stripped, lower-cased form equals ``"truthset"``.
    """
    return draw(st.sampled_from(["truthset", "TruthSet", "TRUTHSET", "  truthset  "]))


@st.composite
def st_non_truthset_name(draw) -> str:
    """Draw a generic, non-TruthSet, non-CORD dataset name.

    Used for the by-``type`` TruthSet entry so availability is decided purely by
    the ``type`` field. None of these names contain the ``truthset`` token.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A plain dataset name with no TruthSet token.
    """
    return draw(st.sampled_from(["Sample Dataset", "Demo Records", "Example Data"]))


@st.composite
def st_cord_name(draw) -> str:
    """Draw a CORD collection name with varied casing.

    Draws one of the canonical CORD collection names and re-cases it (lower,
    upper, or title). None of them contain the ``truthset`` token, so a CORD-only
    response never trips the TruthSet check.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A CORD collection display name (e.g. ``"Las Vegas"``, ``"LONDON"``).
    """
    canonical = draw(st.sampled_from(sorted(CORD_COLLECTION_NAMES)))
    style = draw(st.sampled_from(("lower", "upper", "title")))
    return {"lower": canonical.lower(), "upper": canonical.upper(), "title": canonical.title()}[
        style
    ]


@st.composite
def st_truthset_entry(draw) -> dict:
    """Draw a dataset entry the classifier must read as an available TruthSet.

    The entry always carries retrievable records (a non-empty ``records`` list,
    optionally echoed by ``record_count``). TruthSet identity is established by
    name, by ``type``, or by both so every detection branch is exercised.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A TruthSet dataset entry with retrievable records.
    """
    mode = draw(st.sampled_from(("by_name", "by_type", "by_both")))
    entry: dict = {}
    if mode in ("by_name", "by_both"):
        entry["name"] = draw(st_truthset_name())
    else:
        entry["name"] = draw(st_non_truthset_name())
    if mode in ("by_type", "by_both"):
        entry["type"] = draw(st_truthset_type())
    else:
        entry["type"] = draw(st.sampled_from(["dataset", "sample", "demo"]))

    records = draw(st.lists(st_truthset_record(), min_size=1, max_size=4))
    entry["records"] = records
    if draw(st.booleans()):
        entry["record_count"] = len(records)
    return entry


@st.composite
def st_cord_entry(draw) -> dict:
    """Draw a CORD collection entry (never a TruthSet reference).

    A CORD entry may carry its own records, deliberately, so the CORD-only case
    still classifies ``unavailable`` even when records are present — the classifier
    keys on TruthSet identity, not mere record presence.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A CORD collection dataset entry.
    """
    entry: dict = {
        "name": draw(st_cord_name()),
        "type": draw(st.sampled_from(["cord", "collection", "sample"])),
    }
    if draw(st.booleans()):
        entry["records"] = draw(st.lists(st_truthset_record(), max_size=4))
    if draw(st.booleans()):
        entry["record_count"] = draw(st.integers(min_value=0, max_value=100))
    return entry


@st.composite
def st_mcp_response(draw) -> tuple[object, str]:
    """Draw a ``get_sample_data``-style response paired with its expected label.

    Produces both classification shapes so the biconditional can be asserted in
    each direction:

    * **available** — at least one TruthSet entry with retrievable records,
      optionally interleaved with CORD noise entries.
    * **unavailable** — a CORD-only response (one or more CORD collections, no
      TruthSet entry).

    The entries are wrapped either as a bare list or under one of the recognized
    container keys, so the classifier's response-shape handling is exercised too.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(response, expected_label)`` pair where ``expected_label`` is
        :data:`AVAILABLE` or :data:`UNAVAILABLE`.
    """
    expected_available = draw(st.booleans())
    if expected_available:
        entries = [draw(st_truthset_entry())]
        entries += draw(st.lists(st_cord_entry(), max_size=3))
        entries = draw(st.permutations(entries))
        expected = AVAILABLE
    else:
        entries = draw(st.lists(st_cord_entry(), min_size=1, max_size=4))
        expected = UNAVAILABLE

    entries = list(entries)
    if draw(st.booleans()):
        response: object = entries
    else:
        key = draw(st.sampled_from(RESPONSE_CONTAINER_KEYS))
        response = {key: entries}

    return response, expected


# ---------------------------------------------------------------------------
# Property 1: TruthSet Availability Classification
# ---------------------------------------------------------------------------


class TestTruthSetAvailabilityClassification:
    """Property-based tests for the TruthSet availability classifier.

    Feature: truthset-fallback-source, Property 1: TruthSet Availability Classification

    For any ``get_sample_data`` response, the Availability Classifier outputs
    ``available`` if and only if the response contains a named TruthSet reference
    with retrievable records, and ``unavailable`` if and only if the response
    contains only CORD collection entries. The generator emits both shapes with a
    paired expected label, so the assertion covers the biconditional in both
    directions.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @given(response_and_expected=st_mcp_response())
    def test_availability_classification_biconditional(
        self, response_and_expected: tuple[object, str]
    ) -> None:
        """The classifier's output matches the expected label for both shapes.

        Args:
            response_and_expected: Generated ``(response, expected_label)`` pair.
        """
        response, expected = response_and_expected

        assert classify_availability(response) == expected, (
            f"classify_availability returned "
            f"{classify_availability(response)!r}, expected {expected!r} for "
            f"response {response!r}"
        )


# ---------------------------------------------------------------------------
# Property 2: acquisition path-selection model import
# ---------------------------------------------------------------------------

# The acquisition path-selection + provenance rule is agent logic that lives in
# Step 2 / Step 2a of the steering, not a shipped power script, so it is verified
# against the same pure reference model used for Property 1 (``AVAILABLE`` /
# ``UNAVAILABLE`` are already imported above).
from truthset_fallback_model import (  # noqa: E402
    CORD_SUBSTITUTE,
    FALLBACK_FAILURE_STATUSES,
    FALLBACK_SUCCESS,
    GITHUB_FALLBACK,
    MCP_PRIMARY,
    NON_DETERMINISTIC,
    select_acquisition,
)

# ---------------------------------------------------------------------------
# Property 2 strategies: acquisition scenarios + expected provenance/source
# ---------------------------------------------------------------------------


@st.composite
def st_fallback_failure_status(draw) -> str:
    """Draw a fallback fetcher status that means the fallback path failed.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of the fetcher failure statuses (``fetch_failed``,
        ``validation_failed``, or ``expected_results_failed``).
    """
    return draw(st.sampled_from(sorted(FALLBACK_FAILURE_STATUSES)))


@st.composite
def st_acquisition_scenario(draw) -> tuple[str, str | None, bool | None, str, str]:
    """Draw one acquisition scenario paired with its expected provenance + source.

    Covers the three availability states of Property 2, each paired with the
    provenance label and expected-results source the acquisition logic must
    assign:

    * **primary available** -> ``mcp_primary`` / MCP results. The fallback outcome
      and CORD decision are randomized (and expected to be ignored), exercising the
      precedence of the primary path (Req 2.1).
    * **unavailable + fallback success** -> ``github_fallback`` / fallback results.
      The CORD decision is randomized (ignored because the fallback succeeded).
    * **unavailable + fallback failure + CORD accepted** -> ``cord_substitute`` /
      non-deterministic routing (no known-good results, Req 7.3).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(availability, fallback_outcome, cord_accepted, expected_provenance,
        expected_source)`` tuple.
    """
    scenario = draw(st.sampled_from(("primary", "fallback_success", "cord_accepted")))
    if scenario == "primary":
        fallback_outcome = draw(
            st.one_of(st.none(), st.just(FALLBACK_SUCCESS), st_fallback_failure_status())
        )
        cord_accepted = draw(st.one_of(st.none(), st.booleans()))
        return AVAILABLE, fallback_outcome, cord_accepted, MCP_PRIMARY, MCP_PRIMARY
    if scenario == "fallback_success":
        cord_accepted = draw(st.one_of(st.none(), st.booleans()))
        return UNAVAILABLE, FALLBACK_SUCCESS, cord_accepted, GITHUB_FALLBACK, GITHUB_FALLBACK
    return (
        UNAVAILABLE,
        draw(st_fallback_failure_status()),
        True,
        CORD_SUBSTITUTE,
        NON_DETERMINISTIC,
    )


# ---------------------------------------------------------------------------
# Property 2: Path Selection and Provenance Consistency
# ---------------------------------------------------------------------------


class TestPathSelectionProvenanceConsistency:
    """Property-based tests for acquisition path selection and provenance.

    Feature: truthset-fallback-source, Property 2: Path Selection and Provenance Consistency

    For any availability state -- primary available; primary unavailable with a
    successful fallback; primary unavailable with a failed fallback and an accepted
    CORD substitute -- ``select_acquisition`` assigns exactly the correct provenance
    label (``mcp_primary``, ``github_fallback``, or ``cord_substitute``
    respectively) and routes expected-results selection to the matching source (MCP
    for the primary path, fallback for ``github_fallback``, non-deterministic for
    the CORD substitute). The generator pairs every scenario with its expected
    provenance and source, so the assertion covers the total mapping in every case,
    including the precedence of the primary path over any fallback/CORD inputs.

    **Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.3, 5.3, 7.3**
    """

    @given(scenario=st_acquisition_scenario())
    def test_path_selection_and_provenance_consistency(
        self, scenario: tuple[str, str | None, bool | None, str, str]
    ) -> None:
        """The decision's provenance and expected-results source match exactly.

        Args:
            scenario: Generated ``(availability, fallback_outcome, cord_accepted,
                expected_provenance, expected_source)`` tuple.
        """
        availability, fallback_outcome, cord_accepted, exp_provenance, exp_source = scenario

        decision = select_acquisition(
            availability,
            fallback_outcome=fallback_outcome,
            cord_accepted=cord_accepted,
        )

        assert decision.provenance == exp_provenance, (
            f"expected provenance {exp_provenance!r}, got {decision.provenance!r} for "
            f"availability={availability!r}, fallback_outcome={fallback_outcome!r}, "
            f"cord_accepted={cord_accepted!r}"
        )
        assert decision.expected_results_source == exp_source, (
            f"expected results source {exp_source!r}, got "
            f"{decision.expected_results_source!r} for availability={availability!r}, "
            f"fallback_outcome={fallback_outcome!r}, cord_accepted={cord_accepted!r}"
        )
        # Deterministic verification runs iff a known-good source was routed.
        assert decision.deterministic == (exp_source in (MCP_PRIMARY, GITHUB_FALLBACK))


# ---------------------------------------------------------------------------
# Property 8: degraded-status model import
# ---------------------------------------------------------------------------

# The degraded-status propagation rule is agent logic that lives in Step 2a of the
# steering, not a shipped power script, so it is verified against the same pure
# reference model used for Properties 1 and 2 (``NON_DETERMINISTIC`` is already
# imported with the Property 2 model above).
from truthset_fallback_model import (  # noqa: E402
    BLOCKED,
    DETERMINISTIC_FAILED,
    DETERMINISTIC_PASSED,
    INCOMPLETE,
    derive_module_status,
)

# ---------------------------------------------------------------------------
# Property 8 strategies: Deterministic_Verification check states
# ---------------------------------------------------------------------------

# The two degraded check states that must force the overall Module 3 status to
# ``incomplete`` (Req 7.5; Step 2a item 5).
_DEGRADED_VERIFICATION_STATES = (NON_DETERMINISTIC, BLOCKED)

# Non-degraded deterministic-run check states that must NOT force ``incomplete``.
_NON_DEGRADED_VERIFICATION_STATES = (DETERMINISTIC_PASSED, DETERMINISTIC_FAILED)


@st.composite
def st_degraded_verification_state(draw) -> str:
    """Draw a degraded Deterministic_Verification check state.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of the degraded states (:data:`NON_DETERMINISTIC` or :data:`BLOCKED`).
    """
    return draw(st.sampled_from(_DEGRADED_VERIFICATION_STATES))


@st.composite
def st_verification_state(draw) -> str:
    """Draw any Deterministic_Verification check state (degraded or deterministic-run).

    Covers both the degraded states (``non_deterministic``, ``blocked``) that trip
    the incomplete rule and the deterministic-run states (``passed``, ``failed``)
    that do not, so the propagation can be asserted as a biconditional.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of ``passed``, ``failed``, ``non_deterministic``, or ``blocked``.
    """
    return draw(
        st.sampled_from(_DEGRADED_VERIFICATION_STATES + _NON_DEGRADED_VERIFICATION_STATES)
    )


# ---------------------------------------------------------------------------
# Property 8: Degraded Status Propagation
# ---------------------------------------------------------------------------


class TestDegradedStatusPropagation:
    """Property-based tests for degraded-status propagation.

    Feature: truthset-fallback-source, Property 8: Degraded Status Propagation

    For any verification run whose Deterministic_Verification check is recorded as
    ``non_deterministic`` or ``blocked``, ``derive_module_status`` returns the
    overall Module 3 status ``incomplete`` (the core universal property). The
    converse is asserted as a strengthening control: a clearly non-degraded
    deterministic-run state (``passed`` or ``failed``) is never forced to
    ``incomplete``.

    **Validates: Requirements 7.5**
    """

    @given(deterministic_verification=st_degraded_verification_state())
    def test_degraded_state_forces_incomplete(
        self, deterministic_verification: str
    ) -> None:
        """A degraded check state yields an ``incomplete`` overall module status.

        Args:
            deterministic_verification: Generated degraded state
                (``non_deterministic`` or ``blocked``).
        """
        result = derive_module_status(deterministic_verification)

        assert result == INCOMPLETE, (
            f"expected module status {INCOMPLETE!r} for degraded check state "
            f"{deterministic_verification!r}, got {result!r}"
        )

    @given(deterministic_verification=st_verification_state())
    def test_incomplete_iff_degraded(self, deterministic_verification: str) -> None:
        """``incomplete`` is produced exactly when the check state is degraded.

        Args:
            deterministic_verification: Generated check state (degraded or
                deterministic-run).
        """
        result = derive_module_status(deterministic_verification)
        is_degraded = deterministic_verification in (NON_DETERMINISTIC, BLOCKED)

        assert (result == INCOMPLETE) == is_degraded, (
            f"module status for check state {deterministic_verification!r} must be "
            f"{INCOMPLETE!r} if and only if the state is degraded, got {result!r}"
        )


# ---------------------------------------------------------------------------
# Property 7: URL-governance helper import
# ---------------------------------------------------------------------------

# The URL-governance rule (Requirement 6.1) is enforced by a test-only helper
# co-located in this tests/ directory: it walks the distributed power tree and
# reads files, deriving the raw URL from the registry rather than hardcoding it.
# It is imported the same ``_TESTS_DIR``-on-``sys.path`` way as the reference
# models above.
from truthset_fallback_url_governance import (  # noqa: E402
    DEFAULT_REGISTRY_RELPATH,
    default_power_root,
    find_raw_url_violations,
    registry_url_fragments,
)

# ---------------------------------------------------------------------------
# Property 7 strategies: synthetic power trees with seeded URL leaks
# ---------------------------------------------------------------------------

# A clearly-fake, reserved-TLD host for generated registries. The real sanctioned
# fallback URL is never embedded here — it lives solely in
# config/fallback_sources.yaml and is derived at runtime by the helper.
_GOVERNANCE_FAKE_HOST = "raw.example-host.test"

# Tokens for URL path segments (owner/repo/leaf): lowercase alphanumerics, so a
# segment never contains ``/`` or ``.`` and the assembled URL stays well-formed
# and specific to this generated tree.
_URL_SEGMENT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=3, max_size=10
)

# Text suffixes that are NOT pruned by the helper's ``SKIP_FILE_SUFFIXES``, so a
# seeded leak in such a file is always scanned (never skipped as binary).
_GOVERNANCE_TEXT_SUFFIXES = ("md", "txt", "py", "yaml", "json")

# Clean-content alphabet: letters, digits, spaces, and newlines only. It excludes
# ``/`` (and ``.``), and every derived URL fragment contains at least one ``/``,
# so clean content can never accidentally contain a fragment — no false positives.
_CLEAN_CONTENT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n",
    max_size=40,
)

# A short clean token used to surround an embedded URL in a leak file without
# breaking the URL substring (contains no ``/`` or ``.``).
_CLEAN_TOKEN = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=15)


@st.composite
def st_governance_tree(draw) -> tuple[str, list[tuple[str, str]], set[str], tuple[str, ...]]:
    """Draw a synthetic power tree: one registry plus seeded content files.

    The tree declares a fake ``base_url`` in a minimal-but-valid registry (mirrors
    the real ``fallback_sources.yaml`` shape so ``parse_registry`` accepts it), and
    a set of content files of which a generated subset embeds the raw URL (or one
    of its shorter fragments) while the rest are guaranteed clean. Because clean
    content excludes ``/`` and every URL fragment contains ``/``, a clean file can
    never coincidentally match — the seeded-leak set is therefore the exact,
    ground-truth set of violations.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(registry_yaml, files, leak_relpaths, url_forms)`` tuple where
        ``files`` is a list of ``(relpath, content)`` pairs to write under the
        tree, ``leak_relpaths`` is the subset of those relpaths that embed the raw
        URL, and ``url_forms`` are the exact fragment forms the helper must guard.
    """
    owner = draw(_URL_SEGMENT)
    repo = draw(_URL_SEGMENT)
    leaf = draw(_URL_SEGMENT)
    base_url = f"https://{_GOVERNANCE_FAKE_HOST}/{owner}/{repo}/main/{leaf}"

    # The three detectable forms the helper derives from ``base_url``: the exact
    # URL, the scheme-stripped URL, and the host plus first two path segments.
    url_forms = (
        base_url,
        f"{_GOVERNANCE_FAKE_HOST}/{owner}/{repo}/main/{leaf}",
        f"{_GOVERNANCE_FAKE_HOST}/{owner}/{repo}",
    )

    registry_yaml = (
        'version: "1"\n'
        "sources:\n"
        "  synthetic_demo:\n"
        '    name: "Synthetic Demo"\n'
        '    purpose: "test fixture"\n'
        '    rationale: "test fixture"\n'
        f'    base_url: "{base_url}"\n'
        "    files:\n"
        "      records:\n"
        '        - "records.jsonl"\n'
        '      truth_key: "key.csv"\n'
        "    timeout_seconds: 30\n"
    )

    n_files = draw(st.integers(min_value=1, max_value=6))
    files: list[tuple[str, str]] = []
    leak_relpaths: set[str] = set()
    for index in range(n_files):
        suffix = draw(st.sampled_from(_GOVERNANCE_TEXT_SUFFIXES))
        relpath = f"content/file_{index}.{suffix}"
        if draw(st.booleans()):
            form = draw(st.sampled_from(url_forms))
            prefix = draw(_CLEAN_TOKEN)
            trailing = draw(_CLEAN_TOKEN)
            content = f"{prefix} {form} {trailing}\n"
            leak_relpaths.add(relpath)
        else:
            content = draw(_CLEAN_CONTENT)
        files.append((relpath, content))

    return registry_yaml, files, leak_relpaths, url_forms


# ---------------------------------------------------------------------------
# Property 7: URL Governance — Single Source of Truth
# ---------------------------------------------------------------------------


class TestUrlGovernanceSingleSourceOfTruth:
    """Property-based tests for URL-governance single-source-of-truth.

    Feature: truthset-fallback-source, Property 7: URL Governance — Single Source of Truth

    For any file in the distributed power (excluding the registry
    ``config/fallback_sources.yaml`` itself), the raw fallback source URL does not
    appear — only the registry identifier is used to reference it. The core
    universal property is asserted against the REAL power tree:
    ``find_raw_url_violations(default_power_root())`` returns an empty list. To make
    that absence trustworthy, a Hypothesis-driven test proves the detector itself
    is sound and complete over generated synthetic trees — it flags exactly the
    files that embed the raw URL, never a clean file, and never the registry even
    though the registry contains the URL.

    **Validates: Requirements 6.1**
    """

    @given(tree=st_governance_tree())
    def test_detector_flags_exactly_seeded_leaks(
        self, tree: tuple[str, list[tuple[str, str]], set[str], tuple[str, ...]]
    ) -> None:
        """The detector returns exactly the seeded-leak files, excluding the registry.

        Args:
            tree: Generated ``(registry_yaml, files, leak_relpaths, url_forms)``.
        """
        registry_yaml, files, leak_relpaths, url_forms = tree

        tmp_dir = tempfile.mkdtemp()
        try:
            power_root = Path(tmp_dir)
            registry_path = power_root / DEFAULT_REGISTRY_RELPATH
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(registry_yaml, encoding="utf-8")

            for relpath, content in files:
                file_path = power_root / relpath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

            # Premise check: every form seeded into a leak file is a fragment the
            # helper actually derives from the registry, so a seeded leak is
            # genuinely detectable (the detector guards exactly these forms).
            fragments = registry_url_fragments(registry_path)
            assert set(url_forms) <= fragments, (
                f"seeded URL forms {set(url_forms)!r} are not all guarded by the "
                f"helper's derived fragments {fragments!r}"
            )

            violations = find_raw_url_violations(power_root)

            expected = {power_root / relpath for relpath in leak_relpaths}
            assert set(violations) == expected, (
                f"detector flagged {set(violations)!r}, expected exactly the seeded "
                f"leaks {expected!r}"
            )
            # The registry is never flagged even though it embeds the raw URL.
            resolved_violations = {path.resolve() for path in violations}
            assert registry_path.resolve() not in resolved_violations, (
                "the registry must be excluded from the scan even though it "
                "contains the raw URL"
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_real_power_tree_has_no_violations(self) -> None:
        """The real distributed power tree embeds the raw URL in no file but the registry."""
        violations = find_raw_url_violations(default_power_root())

        assert violations == [], (
            "the raw fallback URL must appear only in the registry; found it "
            f"embedded in: {[str(path) for path in violations]}"
        )


# ---------------------------------------------------------------------------
# Property 9: provenance-persistence model import
# ---------------------------------------------------------------------------

# The provenance-persistence rule is agent logic that lives in Step 2/2a (the
# ``truthset_acquisition`` checkpoint) and Step 10 (the Verification Report mirrors
# it), not a shipped power script, so it is verified against the same pure reference
# model used for Properties 1, 2, and 8 (``AcquisitionDecision``,
# ``select_acquisition``, ``AVAILABLE``/``UNAVAILABLE``, ``FALLBACK_SUCCESS``, and
# ``FALLBACK_FAILURE_STATUSES`` are already imported with the models above).
from truthset_fallback_model import (  # noqa: E402
    VALID_PROVENANCE,
    AcquisitionDecision,
    build_progress_and_report,
)

# ---------------------------------------------------------------------------
# Property 9 strategies: completed acquisitions (non-None provenance)
# ---------------------------------------------------------------------------


@st.composite
def st_completed_acquisition(draw) -> AcquisitionDecision:
    """Draw an ``AcquisitionDecision`` for a completed acquisition (real provenance).

    A "completed acquisition" for Property 9 is any acquisition path that yields a
    provenance label from :data:`VALID_PROVENANCE`. The three such paths are
    produced through ``select_acquisition`` so the property holds *regardless of
    the path taken*:

    * **primary available** -> ``mcp_primary``.
    * **unavailable + fallback success** -> ``github_fallback``.
    * **unavailable + fallback failure + CORD accepted** -> ``cord_substitute``.

    The declined/blocked path (provenance ``None``) is deliberately excluded — it is
    not a completed acquisition with a provenance value (design "valid set" is
    exactly the three labels above).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A completed :class:`AcquisitionDecision` whose ``provenance`` is one of
        ``mcp_primary``, ``github_fallback``, or ``cord_substitute``.
    """
    scenario = draw(st.sampled_from(("primary", "fallback_success", "cord_accepted")))
    if scenario == "primary":
        return select_acquisition(AVAILABLE)
    if scenario == "fallback_success":
        return select_acquisition(UNAVAILABLE, fallback_outcome=FALLBACK_SUCCESS)
    return select_acquisition(
        UNAVAILABLE,
        fallback_outcome=draw(st.sampled_from(sorted(FALLBACK_FAILURE_STATUSES))),
        cord_accepted=True,
    )


# ---------------------------------------------------------------------------
# Property 9: Provenance Persistence Completeness
# ---------------------------------------------------------------------------


class TestProvenancePersistenceCompleteness:
    """Property-based tests for provenance-persistence completeness.

    Feature: truthset-fallback-source, Property 9: Provenance Persistence Completeness

    For any completed TruthSet acquisition (regardless of path taken), the persisted
    ``bootcamp_progress.json`` entry carries a ``source_provenance`` field whose
    value is in the valid set ``{mcp_primary, github_fallback, cord_substitute}``
    (completeness), and the Verification Report includes the SAME provenance value —
    at both the ``module_3_verification`` level and on the ``truthset_acquisition``
    check — because Step 10 mirrors what Step 2/2a persisted rather than re-deriving
    it (consistency). The generator produces every completed acquisition path via
    ``select_acquisition``, so the assertion covers each provenance label.

    **Validates: Requirements 8.1, 8.3**
    """

    @given(decision=st_completed_acquisition())
    def test_provenance_persistence_completeness(
        self, decision: AcquisitionDecision
    ) -> None:
        """Progress carries a valid provenance and the report mirrors it exactly.

        Args:
            decision: Generated completed ``AcquisitionDecision`` (non-None
                provenance).
        """
        progress, report = build_progress_and_report(decision)

        progress_check = progress["module_3_verification"]["checks"]["truthset_acquisition"]
        persisted = progress_check["source_provenance"]

        # Completeness: the progress file carries a provenance from the valid set.
        assert persisted in VALID_PROVENANCE, (
            f"persisted source_provenance {persisted!r} is not in the valid set "
            f"{sorted(VALID_PROVENANCE)}"
        )

        report_module = report["module_3_verification"]
        report_check = report_module["checks"]["truthset_acquisition"]

        # Consistency: the report mirrors the persisted provenance at both levels.
        assert report_module["source_provenance"] == persisted, (
            f"report module-level source_provenance {report_module['source_provenance']!r} "
            f"does not match persisted {persisted!r}"
        )
        assert report_check["source_provenance"] == persisted, (
            f"report truthset_acquisition source_provenance "
            f"{report_check['source_provenance']!r} does not match persisted {persisted!r}"
        )
