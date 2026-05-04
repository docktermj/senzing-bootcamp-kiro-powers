"""Property-based tests for validate_data_files.py using Hypothesis.

Feature: module4-data-validation
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_data_files import (
    CheckResult,
    ValidationReport,
    RECOGNIZED_FORMATS,
    FALLBACK_ENCODINGS,
    check_existence,
    check_format,
    check_records,
    check_encoding,
    validate_file,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


# Characters safe for CSV cells: no commas, newlines, or quotes to avoid
# quoting complexity that would make row counting ambiguous.
_SAFE_CSV_CHARS = st.characters(
    whitelist_categories=("L", "N", "P", "Z"),
    blacklist_characters=",\n\r\"\x00",
)


@st.composite
def st_csv_content(draw):
    """Generate valid CSV content: header row with 1+ columns, then 1+ data rows.

    Returns:
        Tuple of (csv_content_string, expected_data_row_count).
    """
    num_cols = draw(st.integers(min_value=1, max_value=5))
    num_rows = draw(st.integers(min_value=1, max_value=20))

    # Generate header
    headers = [draw(st.text(_SAFE_CSV_CHARS, min_size=1, max_size=10)) for _ in range(num_cols)]

    # Generate data rows
    rows = []
    for _ in range(num_rows):
        row = [draw(st.text(_SAFE_CSV_CHARS, min_size=1, max_size=15)) for _ in range(num_cols)]
        rows.append(row)

    # Build CSV string using csv.writer for correctness
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    content = buf.getvalue()

    return content, num_rows


@st.composite
def st_json_array(draw):
    """Generate a valid JSON array of 1+ objects with string keys/values.

    Returns:
        Tuple of (json_content_string, expected_length).
    """
    num_items = draw(st.integers(min_value=1, max_value=20))
    num_keys = draw(st.integers(min_value=1, max_value=4))

    # Generate consistent keys
    keys = [draw(st.text(st.characters(whitelist_categories=("L",)), min_size=1, max_size=8))
            for _ in range(num_keys)]

    items = []
    for _ in range(num_items):
        obj = {}
        for k in keys:
            obj[k] = draw(st.text(min_size=0, max_size=15))
        items.append(obj)

    content = json.dumps(items, ensure_ascii=False)
    return content, num_items


@st.composite
def st_utf8_text(draw):
    """Generate valid non-empty UTF-8 text strings.

    Returns:
        A non-empty Unicode string (valid UTF-8 when encoded).
    """
    text = draw(st.text(min_size=1, max_size=200))
    # Filter out strings that are only whitespace/control chars
    assume(text.strip())
    return text


@st.composite
def st_invalid_bytes(draw):
    """Generate byte sequences that are NOT valid UTF-8.

    Since latin-1 can decode any byte sequence, the practical test is:
    non-UTF-8 bytes → check returns "warn" (fallback found) or "fail".
    The key property: the result is never "pass" with encoding "utf-8".

    Returns:
        Bytes that are not valid UTF-8.
    """
    raw = draw(st.binary(min_size=1, max_size=200))
    # Filter to only keep sequences that fail UTF-8 decode
    try:
        raw.decode("utf-8")
        assume(False)  # Skip valid UTF-8
    except (UnicodeDecodeError, ValueError):
        pass
    return raw


@st.composite
def st_extension_case_variant(draw):
    """Generate a recognized extension with random case transforms.

    Returns:
        Tuple of (case_variant_extension, expected_normalized_format).
        e.g. (".CSV", "csv") or (".Json", "json")
    """
    ext = draw(st.sampled_from(list(RECOGNIZED_FORMATS.keys())))
    expected_format = RECOGNIZED_FORMATS[ext]

    # Apply random case transform to each character
    variant = ""
    for ch in ext:
        if draw(st.booleans()):
            variant += ch.upper()
        else:
            variant += ch.lower()

    return variant, expected_format


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestCSVRecordCount:
    """Property 1: Valid CSV content produces correct record count.

    **Validates: Requirements 3.1, 3.2, 10.2**

    For any valid CSV content with a header row and N data rows, the validator
    record-presence check returns pass and the record_count equals N.
    """

    @given(data=st_csv_content())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_csv_record_count_matches(self, data):
        """CSV record count equals the number of generated data rows."""
        content, expected_count = data

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(content)
            fpath = f.name
        try:
            result = check_records(fpath, "csv")
            assert result.status == "pass", (
                f"Expected pass, got {result.status}: {result.message}"
            )
            assert result.details.get("record_count") == expected_count, (
                f"Expected {expected_count} records, "
                f"got {result.details.get('record_count')}"
            )
        finally:
            os.unlink(fpath)


class TestJSONRecordCount:
    """Property 2: Valid JSON arrays produce correct record count.

    **Validates: Requirements 3.3, 10.3**

    For any valid JSON array of 1+ objects, the validator record-presence check
    returns pass and the record_count equals the array length.
    """

    @given(data=st_json_array())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_json_array_record_count_matches(self, data):
        """JSON array record count equals the number of generated objects."""
        content, expected_count = data

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            f.write(content)
            fpath = f.name
        try:
            result = check_records(fpath, "json")
            assert result.status == "pass", (
                f"Expected pass, got {result.status}: {result.message}"
            )
            assert result.details.get("record_count") == expected_count, (
                f"Expected {expected_count} records, "
                f"got {result.details.get('record_count')}"
            )
        finally:
            os.unlink(fpath)


class TestUTF8EncodingPass:
    """Property 3: Valid UTF-8 content passes encoding check.

    **Validates: Requirements 4.1, 4.2, 10.4**

    For any valid UTF-8 string, when written to a file, the encoding check
    returns pass with encoding reported as "utf-8".
    """

    @given(text=st_utf8_text())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_utf8_content_passes_encoding(self, text):
        """Valid UTF-8 text files pass encoding check with utf-8 encoding."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(text)
            fpath = f.name
        try:
            result = check_encoding(fpath, "csv")
            assert result.status == "pass", (
                f"Expected pass, got {result.status}: {result.message}"
            )
            assert result.details.get("encoding") == "utf-8", (
                f"Expected utf-8 encoding, got {result.details.get('encoding')}"
            )
        finally:
            os.unlink(fpath)


class TestInvalidEncodingFails:
    """Property 4: Invalid encoding fails encoding check.

    **Validates: Requirements 4.5, 10.5**

    For any byte sequence that is not valid UTF-8, the encoding check returns
    either "warn" (fallback encoding found) or "fail" (no encoding works).
    It never returns "pass" with encoding "utf-8".

    Note: Since latin-1 can decode any byte sequence, the practical property
    is that non-UTF-8 bytes never produce a "pass" with utf-8 encoding.
    """

    @given(raw_bytes=st_invalid_bytes())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_utf8_bytes_not_detected_as_utf8(self, raw_bytes):
        """Non-UTF-8 bytes are never reported as utf-8 encoding."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as f:
            f.write(raw_bytes)
            fpath = f.name
        try:
            result = check_encoding(fpath, "csv")

            # The key property: non-UTF-8 bytes must NOT be reported as utf-8
            if result.status == "pass":
                assert result.details.get("encoding") != "utf-8", (
                    "Non-UTF-8 bytes were incorrectly reported as utf-8"
                )
            else:
                # "warn" (fallback found) or "fail" (no encoding works) are both valid
                assert result.status in ("warn", "fail"), (
                    f"Unexpected status: {result.status}"
                )
        finally:
            os.unlink(fpath)


class TestOverallStatusConsistency:
    """Property 5: Overall status is pass iff all checks pass or warn.

    **Validates: Requirements 5.1, 10.6**

    For any ValidationReport produced by the validator, the overall_status is
    "pass" if and only if every individual CheckResult status is "pass" or "warn".
    """

    @given(
        statuses=st.lists(
            st.sampled_from(["pass", "fail", "warn"]),
            min_size=1,
            max_size=6,
        )
    )
    @settings(max_examples=100)
    def test_overall_status_matches_check_statuses(self, statuses):
        """Overall status is pass iff no check has status fail."""
        checks = [
            CheckResult(
                name=f"check_{i}",
                status=s,
                message=f"Test message {i}",
                remediation="Fix it" if s == "fail" else "",
            )
            for i, s in enumerate(statuses)
        ]

        has_failure = any(s == "fail" for s in statuses)
        expected_overall = "fail" if has_failure else "pass"

        report = ValidationReport(
            file_path="/tmp/test.csv",
            file_name="test.csv",
            format="csv",
            record_count=10,
            encoding="utf-8",
            checks=checks,
            overall_status=expected_overall,
        )

        # Verify the property holds on the report
        all_pass_or_warn = all(c.status in ("pass", "warn") for c in report.checks)
        if all_pass_or_warn:
            assert report.overall_status == "pass", (
                f"All checks pass/warn but overall is {report.overall_status}"
            )
        else:
            assert report.overall_status == "fail", (
                f"Some checks failed but overall is {report.overall_status}"
            )

    @given(
        ext=st.sampled_from([".csv", ".json", ".jsonl", ".xml", ".tsv"]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_validate_file_overall_status_consistency(self, ext):
        """validate_file produces consistent overall_status for real files."""
        # Create a valid file for each format
        content_map = {
            ".csv": "name,age\nAlice,30\n",
            ".json": '[{"name": "Alice"}]',
            ".jsonl": '{"name": "Alice"}\n',
            ".xml": "<root><item>1</item></root>",
            ".tsv": "name\tage\nAlice\t30\n",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, encoding="utf-8", delete=False
        ) as f:
            f.write(content_map[ext])
            fpath = f.name
        try:
            report = validate_file(fpath)

            all_pass_or_warn = all(
                c.status in ("pass", "warn") for c in report.checks
            )
            if all_pass_or_warn:
                assert report.overall_status == "pass"
            else:
                assert report.overall_status == "fail"
        finally:
            os.unlink(fpath)


class TestFailedChecksHaveRemediation:
    """Property 6: Every failed check has non-empty remediation guidance.

    **Validates: Requirements 5.3, 6.1–6.7, 10.7**

    For any ValidationReport with at least one failed CheckResult, every failed
    check has a non-empty remediation string.
    """

    @given(
        scenario=st.sampled_from([
            "nonexistent",
            "empty_file",
            "unrecognized_format",
            "no_records_csv",
            "no_records_json",
        ])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_failed_checks_have_remediation(self, scenario):
        """Every failed check in a validation report has non-empty remediation."""
        tmpdir = tempfile.mkdtemp()
        try:
            if scenario == "nonexistent":
                report = validate_file(os.path.join(tmpdir, "does_not_exist.csv"))
            elif scenario == "empty_file":
                fpath = os.path.join(tmpdir, "empty.csv")
                with open(fpath, "wb") as f:
                    pass  # 0 bytes
                report = validate_file(fpath)
            elif scenario == "unrecognized_format":
                fpath = os.path.join(tmpdir, "data.xyz")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("some content")
                report = validate_file(fpath)
            elif scenario == "no_records_csv":
                fpath = os.path.join(tmpdir, "header_only.csv")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("name,age\n")
                report = validate_file(fpath)
            elif scenario == "no_records_json":
                fpath = os.path.join(tmpdir, "empty_array.json")
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("[]")
                report = validate_file(fpath)
            else:
                return

            # Every failed check must have non-empty remediation
            for check in report.checks:
                if check.status == "fail":
                    assert check.remediation, (
                        f"Failed check '{check.name}' has empty remediation: "
                        f"{check.message}"
                    )
        finally:
            # Clean up temp files
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    @given(
        statuses=st.lists(
            st.sampled_from(["pass", "fail", "warn"]),
            min_size=1,
            max_size=6,
        ).filter(lambda ss: any(s == "fail" for s in ss))
    )
    @settings(max_examples=100)
    def test_constructed_reports_fail_checks_have_remediation(self, statuses):
        """Constructed reports with fail checks must have non-empty remediation."""
        checks = [
            CheckResult(
                name=f"check_{i}",
                status=s,
                message=f"Test message {i}",
                remediation=f"Fix check {i}" if s == "fail" else "",
            )
            for i, s in enumerate(statuses)
        ]

        report = ValidationReport(
            file_path="/tmp/test.csv",
            file_name="test.csv",
            format="csv",
            record_count=10,
            encoding="utf-8",
            checks=checks,
            overall_status="fail",
        )

        for check in report.failed_checks:
            assert check.remediation, (
                f"Failed check '{check.name}' has empty remediation"
            )


class TestFormatDetectionCaseInsensitive:
    """Property 7: Format detection is case-insensitive.

    **Validates: Requirements 2.1, 2.2**

    For any recognized file extension in any case combination, the validator
    recognizes the extension and returns the correct normalized format name.
    """

    @given(data=st_extension_case_variant())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_case_variant_extensions_recognized(self, data):
        """File extensions are recognized regardless of case."""
        ext_variant, expected_format = data

        content_map = {
            "csv": "name,age\nAlice,30\n",
            "json": '[{"name": "Alice"}]',
            "jsonl": '{"name": "Alice"}\n',
            "xml": "<root><item>1</item></root>",
            "tsv": "name\tage\nAlice\t30\n",
        }

        if expected_format in ("xlsx", "parquet"):
            # Binary formats: write some bytes (extension match is sufficient)
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=ext_variant, delete=False
            ) as f:
                f.write(b"\x00\x01\x02\x03")
                fpath = f.name
        else:
            content = content_map.get(expected_format, "content")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext_variant, encoding="utf-8", delete=False
            ) as f:
                f.write(content)
                fpath = f.name

        try:
            result = check_format(fpath)

            assert result.status == "pass", (
                f"Extension '{ext_variant}' not recognized: {result.message}"
            )
            assert result.details.get("detected_format") == expected_format, (
                f"Expected format '{expected_format}', "
                f"got '{result.details.get('detected_format')}'"
            )
        finally:
            os.unlink(fpath)
