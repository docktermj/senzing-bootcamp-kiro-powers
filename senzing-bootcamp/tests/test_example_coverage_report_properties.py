"""Property-based tests for the example-coverage report script.

These tests exercise the correctness properties documented in the
`language-example-coverage` design's "Correctness Properties" section, using
pytest + Hypothesis. Each property is implemented by a single property-based
test that runs at least 100 generated examples.

Scripts under `senzing-bootcamp/scripts/` are not packages, so the script is
imported via `sys.path` manipulation (per python-conventions.md).
"""

from __future__ import annotations

import dataclasses
import io
import json
import math
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from example_coverage_report import (  # noqa: E402
    HONEST_SCOPE_STATEMENT,
    VALID_STATUSES,
    CoverageRecord,
    Snapshot,
    Violation,
    build_report,
    check_disclosure,
    derive_ranking,
    load_coverage_record,
    main,
    render_disclosure,
    render_report_json,
    render_report_text,
    validate_record,
    write_disclosure_region,
)

# ---------------------------------------------------------------------------
# Shared Hypothesis strategies (prefixed st_; reused by later property tests)
# ---------------------------------------------------------------------------

#: Marker substring identifying a completeness violation in a Violation
#: description. Kept in one place so the property tests cannot diverge from the
#: message format produced by ``validate_record``.
_COMPLETENESS_MARKER = "missing coverage entry"


def st_identifier() -> st.SearchStrategy[str]:
    """Generate short identifier-like strings for languages and topic ids.

    Returns:
        A strategy yielding non-empty lowercase identifier strings (letters,
        digits, and underscores) suitable as language keys and topic ids.
    """
    return st.from_regex(r"[a-z][a-z0-9_]{0,11}", fullmatch=True)


def st_label() -> st.SearchStrategy[str]:
    """Generate non-empty human-readable topic labels.

    Returns:
        A strategy yielding non-empty label strings. Labels are required to be
        non-empty so a generated record is schema-valid with respect to the
        topic-label check.
    """
    return st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        min_size=1,
        max_size=30,
    )


def st_status() -> st.SearchStrategy[str]:
    """Generate a valid Coverage_Status value.

    Returns:
        A strategy drawing from :data:`VALID_STATUSES`.
    """
    return st.sampled_from(VALID_STATUSES)


def st_snapshot() -> st.SearchStrategy[Snapshot]:
    """Generate Snapshot_Metadata with non-empty required fields.

    Returns:
        A strategy yielding :class:`Snapshot` instances whose ``last_observed``
        and ``senzing_version`` are non-empty (so the record is schema-valid).
    """
    nonempty = st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        min_size=1,
        max_size=12,
    )
    return st.builds(Snapshot, last_observed=nonempty, senzing_version=nonempty)


@st.composite
def st_coverage_record(
    draw: st.DrawFn,
    *,
    min_languages: int = 1,
    min_topics: int = 1,
    max_languages: int = 5,
    max_topics: int = 6,
) -> CoverageRecord:
    """Generate a complete, schema-valid Coverage_Record.

    The generated record has a random, unique language set and topic set, a
    full coverage matrix with a randomly chosen valid status for every
    (language, topic) pair, non-empty topic labels, and non-empty snapshot
    metadata. As such, :func:`validate_record` reports no violations for any
    record produced by this strategy.

    This is the reusable core strategy: negative-case property tests derive
    from it by mutating a single field to inject one defect.

    Args:
        draw: The Hypothesis draw function (supplied by ``@composite``).
        min_languages: Minimum number of tracked languages.
        min_topics: Minimum number of tracked topics.
        max_languages: Maximum number of tracked languages.
        max_topics: Maximum number of tracked topics.

    Returns:
        A complete, valid :class:`CoverageRecord`.
    """
    languages = tuple(
        draw(
            st.lists(
                st_identifier(),
                min_size=min_languages,
                max_size=max_languages,
                unique=True,
            )
        )
    )
    topic_ids = draw(
        st.lists(
            st_identifier(),
            min_size=min_topics,
            max_size=max_topics,
            unique=True,
        )
    )
    topics = {topic_id: draw(st_label()) for topic_id in topic_ids}
    coverage = {
        language: {topic_id: draw(st_status()) for topic_id in topic_ids}
        for language in languages
    }
    snapshot = draw(st_snapshot())
    return CoverageRecord(
        languages=languages,
        topics=topics,
        coverage=coverage,
        snapshot=snapshot,
    )


def _completeness_violations(violations: list[Violation]) -> list[Violation]:
    """Filter a violation list down to completeness (missing-entry) violations.

    Args:
        violations: The full list returned by :func:`validate_record`.

    Returns:
        Only the violations whose description marks a missing coverage entry.
    """
    return [v for v in violations if _COMPLETENESS_MARKER in v.description]


def _record_without_entry(
    record: CoverageRecord, language: str, topic_id: str
) -> CoverageRecord:
    """Return a copy of ``record`` with a single (language, topic) entry removed.

    Args:
        record: The complete source record.
        language: The language whose entry should be dropped.
        topic_id: The topic id to remove from that language's coverage.

    Returns:
        A new :class:`CoverageRecord` missing exactly the named entry.
    """
    new_coverage = {
        lang: dict(entries) for lang, entries in record.coverage.items()
    }
    del new_coverage[language][topic_id]
    return dataclasses.replace(record, coverage=new_coverage)


# ---------------------------------------------------------------------------
# Property 1: Schema completeness
# ---------------------------------------------------------------------------


class TestSchemaCompleteness:
    """Validates Requirements 1.4 and 7.2 (one coverage entry per pair)."""

    # Feature: language-example-coverage, Property 1: Schema completeness
    @settings(max_examples=100)
    @given(record=st_coverage_record(), data=st.data())
    def test_completeness_violation_iff_entry_missing(
        self, record: CoverageRecord, data: st.DataObject
    ) -> None:
        """No completeness violation for a full matrix; one when an entry drops.

        For any record declaring languages L and topics T, ``validate_record``
        reports no completeness violation when a coverage entry exists for every
        (language, topic) pair in L x T, and reports a completeness violation
        whenever any single such entry is removed.
        """
        # A complete record has no completeness violations.
        complete_violations = _completeness_violations(validate_record(record))
        assert complete_violations == []

        # Removing any single (language, topic) entry yields a completeness
        # violation that names exactly that missing pair.
        language = data.draw(st.sampled_from(record.languages))
        topic_id = data.draw(st.sampled_from(sorted(record.topics)))
        mutated = _record_without_entry(record, language, topic_id)

        missing = _completeness_violations(validate_record(mutated))
        assert len(missing) == 1
        description = missing[0].description
        assert f"'{language}'" in description
        assert f"'{topic_id}'" in description


# ---------------------------------------------------------------------------
# Property 2: Status value constraint
# ---------------------------------------------------------------------------

#: Marker substring identifying a status-value violation in a Violation
#: description. Kept in one place so the property test cannot diverge from the
#: message format produced by ``validate_record``.
_STATUS_MARKER = "invalid status"


def st_invalid_status() -> st.SearchStrategy[str]:
    """Generate status strings that fall outside :data:`VALID_STATUSES`.

    Returns:
        A strategy yielding arbitrary text that is guaranteed not to be one of
        the three valid Coverage_Status values, so injecting it always
        constitutes a status-value defect.
    """
    return st.text(max_size=20).filter(lambda s: s not in VALID_STATUSES)


def _status_violations(violations: list[Violation]) -> list[Violation]:
    """Filter a violation list down to status-value violations.

    Args:
        violations: The full list returned by :func:`validate_record`.

    Returns:
        Only the violations whose description marks an invalid status.
    """
    return [v for v in violations if _STATUS_MARKER in v.description]


def _record_with_status(
    record: CoverageRecord, language: str, topic_id: str, status: str
) -> CoverageRecord:
    """Return a copy of ``record`` with one (language, topic) entry restatused.

    Args:
        record: The complete source record.
        language: The language whose entry should be changed.
        topic_id: The topic id whose status should be replaced.
        status: The status string to assign to that entry.

    Returns:
        A new :class:`CoverageRecord` with exactly the named entry mutated.
    """
    new_coverage = {
        lang: dict(entries) for lang, entries in record.coverage.items()
    }
    new_coverage[language][topic_id] = status
    return dataclasses.replace(record, coverage=new_coverage)


class TestStatusValueConstraint:
    """Validates Requirements 1.5 and 7.1 (status restricted to valid set)."""

    # Feature: language-example-coverage, Property 2: Status value constraint
    @settings(max_examples=100)
    @given(
        record=st_coverage_record(),
        invalid_status=st_invalid_status(),
        data=st.data(),
    )
    def test_status_violation_iff_status_outside_valid_set(
        self,
        record: CoverageRecord,
        invalid_status: str,
        data: st.DataObject,
    ) -> None:
        """No status violation when all statuses are valid; one when any is not.

        For any record, ``validate_record`` reports a status-value violation if
        and only if at least one coverage entry holds a status outside
        ``{available, none, unknown}``. A record from ``st_coverage_record``
        draws every status from :data:`VALID_STATUSES`, so it has no status
        violation; mutating any single entry to a status outside that set
        produces exactly one status-value violation naming that entry.
        """
        # A record with all-valid statuses reports no status-value violation.
        assert _status_violations(validate_record(record)) == []

        # Mutating any single entry to an out-of-set status yields a status
        # violation naming exactly that (language, topic) pair.
        language = data.draw(st.sampled_from(record.languages))
        topic_id = data.draw(st.sampled_from(sorted(record.topics)))
        mutated = _record_with_status(record, language, topic_id, invalid_status)

        bad = _status_violations(validate_record(mutated))
        assert len(bad) == 1
        description = bad[0].description
        assert f"'{language}'" in description
        assert f"'{topic_id}'" in description


# ---------------------------------------------------------------------------
# Property 3: Required fields present
# ---------------------------------------------------------------------------

#: Marker substrings identifying a required-field violation in a Violation
#: description. The loader coerces missing snapshot fields and missing topic
#: labels to "", so an empty value is what ``validate_record`` reports as
#: missing. Kept in one place so the property test cannot diverge from the
#: message format produced by ``validate_record``.
_SNAPSHOT_FIELD_MARKER = "missing required snapshot field"
_LABEL_MARKER = "missing a human-readable label"


def _required_field_violations(violations: list[Violation]) -> list[Violation]:
    """Filter a violation list down to required-field violations.

    Args:
        violations: The full list returned by :func:`validate_record`.

    Returns:
        Only the violations marking a missing snapshot field or a missing topic
        label.
    """
    return [
        v
        for v in violations
        if _SNAPSHOT_FIELD_MARKER in v.description or _LABEL_MARKER in v.description
    ]


def _record_with_blank_snapshot_field(
    record: CoverageRecord, field: str
) -> CoverageRecord:
    """Return a copy of ``record`` with one snapshot field blanked.

    Args:
        record: The complete source record.
        field: Either ``"last_observed"`` or ``"senzing_version"``.

    Returns:
        A new :class:`CoverageRecord` whose named snapshot field is "" (the
        loader's representation of a missing field).
    """
    new_snapshot = dataclasses.replace(record.snapshot, **{field: ""})
    return dataclasses.replace(record, snapshot=new_snapshot)


def _record_with_blank_label(
    record: CoverageRecord, topic_id: str
) -> CoverageRecord:
    """Return a copy of ``record`` with one topic's label blanked.

    Args:
        record: The complete source record.
        topic_id: The topic whose label should be emptied.

    Returns:
        A new :class:`CoverageRecord` where ``topic_id`` maps to "" (the
        loader's representation of a missing label).
    """
    new_topics = dict(record.topics)
    new_topics[topic_id] = ""
    return dataclasses.replace(record, topics=new_topics)


class TestRequiredFieldsPresent:
    """Validates Requirements 1.6, 2.4, 7.3 (snapshot fields and topic labels)."""

    # Feature: language-example-coverage, Property 3: Required fields present
    @settings(max_examples=100)
    @given(record=st_coverage_record(), data=st.data())
    def test_required_field_violation_iff_field_missing(
        self, record: CoverageRecord, data: st.DataObject
    ) -> None:
        """No required-field violation when complete; one when any field blanks.

        For any record, ``validate_record`` reports a required-field violation
        if and only if a required Snapshot_Metadata field (``last_observed`` or
        ``senzing_version``) is missing or any tracked topic lacks a label. A
        record from ``st_coverage_record`` has non-empty snapshot fields and
        non-empty labels, so it has no required-field violation; blanking any
        single one of those fields produces a required-field violation.
        """
        # A complete record reports no required-field violations.
        assert _required_field_violations(validate_record(record)) == []

        # Pick one defect to inject per example: blank a snapshot field or blank
        # a single topic label.
        defect = data.draw(
            st.sampled_from(["last_observed", "senzing_version", "label"])
        )
        if defect == "label":
            topic_id = data.draw(st.sampled_from(sorted(record.topics)))
            mutated = _record_with_blank_label(record, topic_id)
            violations = _required_field_violations(validate_record(mutated))
            assert any(
                _LABEL_MARKER in v.description and f"'{topic_id}'" in v.description
                for v in violations
            )
        else:
            mutated = _record_with_blank_snapshot_field(record, defect)
            violations = _required_field_violations(validate_record(mutated))
            assert any(
                _SNAPSHOT_FIELD_MARKER in v.description
                and f"'{defect}'" in v.description
                for v in violations
            )


# ---------------------------------------------------------------------------
# Property 5: Per-language status counts are exhaustive and accurate
# ---------------------------------------------------------------------------


class TestPerLanguageStatusCounts:
    """Validates Requirement 3.4 (per-language status counts are exact)."""

    # Feature: language-example-coverage, Property 5: Per-language status counts
    # are exhaustive and accurate
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_counts_sum_to_topic_count_and_each_status_is_exact(
        self, record: CoverageRecord
    ) -> None:
        """Per-language counts sum to the topic count; each status count is exact.

        For any Coverage_Record, every language summary's status counts sum to
        the number of tracked topics, the counts dict covers every value in
        :data:`VALID_STATUSES`, and each per-status count equals the true number
        of that language's entries holding that status (computed independently
        from ``record.coverage``).
        """
        topic_count = len(record.topics)
        report = build_report(record)

        # One summary per declared language, in declared order.
        assert tuple(s.language for s in report.languages) == record.languages

        for summary in report.languages:
            counts = summary.counts

            # The counts dict covers exactly the valid statuses.
            assert set(counts) == set(VALID_STATUSES)

            # Counts are exhaustive: they account for every tracked topic.
            assert sum(counts.values()) == topic_count

            # Each per-status count equals the true count computed directly
            # from the record's coverage matrix for this language.
            lang_entries = record.coverage[summary.language]
            for status in VALID_STATUSES:
                expected = sum(
                    1
                    for topic_id in record.topics
                    if lang_entries.get(topic_id) == status
                )
                assert counts[status] == expected


# ---------------------------------------------------------------------------
# Property 6: Gap list equals the none/unknown topics
# ---------------------------------------------------------------------------


class TestGapList:
    """Validates Requirement 3.5 (gaps are exactly the none/unknown topics)."""

    # Feature: language-example-coverage, Property 6: Gap list equals the none/unknown topics
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_gaps_equal_none_or_unknown_topics(
        self, record: CoverageRecord
    ) -> None:
        """Each language's gaps are exactly its none/unknown topics.

        For any Coverage_Record and language, the report's listed gap topics
        equal exactly the set of topics whose status is ``none`` or
        ``unknown`` (computed independently from ``record.coverage``), contain
        no ``available`` topics, are unique, and follow declared topic order to
        match the implementation.
        """
        report = build_report(record)

        # One summary per declared language, in declared order.
        assert tuple(s.language for s in report.languages) == record.languages

        for summary in report.languages:
            lang_entries = record.coverage[summary.language]

            expected = {
                topic_id
                for topic_id in record.topics
                if lang_entries.get(topic_id) in ("none", "unknown")
            }

            # Core property: the gap set equals the none/unknown topic set.
            assert set(summary.gaps) == expected

            # Gaps never include an 'available' topic.
            assert all(lang_entries.get(t) != "available" for t in summary.gaps)

            # Gaps are unique and ordered in declared topic order.
            assert len(summary.gaps) == len(set(summary.gaps))
            assert list(summary.gaps) == [
                topic_id
                for topic_id in record.topics
                if topic_id in expected
            ]


# ---------------------------------------------------------------------------
# Property 7: Available proportion is the available fraction
# ---------------------------------------------------------------------------


class TestAvailableProportion:
    """Validates Requirement 8.1 (available_proportion is the available fraction)."""

    # Feature: language-example-coverage, Property 7: Available proportion is the
    # available fraction
    @settings(max_examples=100)
    @given(record=st_coverage_record(min_topics=0))
    def test_available_proportion_is_available_fraction(
        self, record: CoverageRecord
    ) -> None:
        """available_proportion equals available/topics and lies within [0, 1].

        For any Coverage_Record and language, the report's
        ``available_proportion`` lies within the closed interval [0, 1] and
        equals (count of that language's ``available`` topics) / (number of
        tracked topics) when topics exist, and 0.0 when there are no topics
        (the empty-topics branch is exercised via ``min_topics=0``).
        """
        topic_count = len(record.topics)
        report = build_report(record)

        for summary in report.languages:
            proportion = summary.available_proportion

            # The proportion always lies within the closed unit interval.
            assert 0.0 <= proportion <= 1.0

            lang_entries = record.coverage[summary.language]
            available = sum(
                1
                for topic_id in record.topics
                if lang_entries.get(topic_id) == "available"
            )

            if topic_count == 0:
                # No tracked topics: the proportion is defined as 0.0.
                assert proportion == 0.0
            else:
                # The proportion is exactly the available fraction.
                assert math.isclose(proportion, available / topic_count)


# ---------------------------------------------------------------------------
# Property 8: JSON report proportions round-trip
# ---------------------------------------------------------------------------


class TestJsonProportionRoundTrip:
    """Validates Requirement 8.2 (JSON proportions round-trip from build_report)."""

    # Feature: language-example-coverage, Property 8: JSON report proportions
    # round-trip
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_json_proportions_equal_build_report_proportions(
        self, record: CoverageRecord
    ) -> None:
        """Parsed --format json proportions equal those from build_report.

        For any Coverage_Record, parsing the ``render_report_json`` output yields
        a structure whose per-language ``available_proportion`` equals the
        proportion computed by ``build_report`` for that language, proving the
        JSON serialization round-trips the report's proportions without loss.
        """
        report = build_report(record)
        json_str = render_report_json(report)
        parsed = json.loads(json_str)

        for summary in report.languages:
            parsed_proportion = parsed["languages"][summary.language][
                "available_proportion"
            ]
            assert math.isclose(parsed_proportion, summary.available_proportion)


# ---------------------------------------------------------------------------
# Property 9: Report content includes snapshot metadata and honest-scope
# statement
# ---------------------------------------------------------------------------


class TestReportContent:
    """Validates Requirements 3.8 and 6.3 (snapshot metadata + honest scope)."""

    # Feature: language-example-coverage, Property 9: Report content includes
    # snapshot metadata and honest-scope statement
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_report_text_includes_snapshot_and_honest_scope(
        self, record: CoverageRecord
    ) -> None:
        """Rendered report carries snapshot values and the honest-scope statement.

        For any Coverage_Record, the human-readable report rendered by
        ``render_report_text`` contains both Snapshot_Metadata values
        (``last_observed`` and ``senzing_version``) and the honest-scope
        statement that the report reflects supplementary example availability
        only and does not reflect ``generate_scaffold`` / ``sdk_guide`` output
        quality.
        """
        report = build_report(record)
        text = render_report_text(report)

        # Both snapshot metadata values appear verbatim in the rendered report.
        assert record.snapshot.last_observed in text
        assert record.snapshot.senzing_version in text

        # The honest-scope statement appears verbatim, tying the report to the
        # implementation constant.
        assert HONEST_SCOPE_STATEMENT in text


# ---------------------------------------------------------------------------
# Property 10: Disclosure content states scope, equivalence, and names the
# top-ranked language
# ---------------------------------------------------------------------------


class TestDisclosureContent:
    """Validates Requirements 4.1, 6.1, 6.2 (disclosure scope, equivalence, top)."""

    # Feature: language-example-coverage, Property 10: Disclosure content states
    # scope, equivalence, and names the top-ranked language
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_disclosure_states_scope_equivalence_and_names_top_language(
        self, record: CoverageRecord
    ) -> None:
        """Disclosure body states scope, equivalence, and names the top language.

        For any Coverage_Record, the body rendered by ``render_disclosure``
        contains the availability-only scope statement, the
        ``generate_scaffold`` / ``sdk_guide`` equivalence statement, and the
        name of the highest-ranked language (the ``available``-proportion leader
        from ``derive_ranking``), wrapped in backticks as the implementation
        renders identifiers.
        """
        body = render_disclosure(record)

        # The availability-only scope statement is present.
        assert "supplementary example availability only" in body

        # The generate_scaffold / sdk_guide equivalence statement is present.
        assert "generate_scaffold" in body
        assert "sdk_guide" in body
        assert "equivalent" in body

        # The top-ranked language is named (backticked identifier form).
        top = derive_ranking(record)[0]
        assert f"`{top}`" in body


# ---------------------------------------------------------------------------
# Property 11: Disclosure render/check round-trip is drift-free
# ---------------------------------------------------------------------------

#: A minimal POWER.md document containing surrounding prose plus the
#: example-coverage begin/end markers with a placeholder body. Writing the
#: rendered disclosure into this document and checking it back must report no
#: drift.
_POWER_MD_TEMPLATE = (
    "# Title\n"
    "\n"
    "some prose\n"
    "\n"
    "<!-- BEGIN GENERATED: example-coverage -->\n"
    "\n"
    "<!-- END GENERATED: example-coverage -->\n"
    "\n"
    "more prose\n"
)


class TestDisclosureRoundTrip:
    """Validates Requirement 4.1 (render then check reports no drift)."""

    # Feature: language-example-coverage, Property 11: Disclosure render/check
    # round-trip is drift-free
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_render_then_check_reports_no_drift(
        self, record: CoverageRecord
    ) -> None:
        """Writing the region from a record then checking it reports no drift.

        For any Coverage_Record, rendering the disclosure body, writing it into
        the example-coverage region of a POWER.md document, and then running
        ``check_disclosure`` against the same record yields an empty violation
        list: the committed region matches ``render_disclosure(record)`` exactly,
        so no drift is reported.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            power_md_path = Path(tmp_dir) / "POWER.md"
            power_md_path.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")

            body = render_disclosure(record)
            write_disclosure_region(power_md_path, body)

            assert check_disclosure(power_md_path, record) == []


# ---------------------------------------------------------------------------
# Property 12: Disclosure drift is detected
# ---------------------------------------------------------------------------

#: Sentinel appended to a correctly-rendered disclosure body to guarantee the
#: mutated region differs from ``render_disclosure(record)`` (i.e. it names an
#: inconsistent ranking / arbitrary drifted content). Kept distinct from any
#: rendered body so the mutation is always a genuine drift.
_DRIFT_SENTINEL = "\n> DRIFTED \u2014 inconsistent ranking sentinel\n"


class TestDisclosureDriftDetection:
    """Validates Requirement 4.2 (drift is detected and fails the check)."""

    # Feature: language-example-coverage, Property 12: Disclosure drift is detected
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_drift_is_detected_by_check_disclosure_and_main_check(
        self, record: CoverageRecord
    ) -> None:
        """Mutating the region to inconsistent content trips drift detection.

        For any Coverage_Record, writing the correct disclosure body, then
        mutating the region so it no longer matches ``render_disclosure``, causes
        ``check_disclosure`` to report a non-empty drift violation list. The same
        drift, applied against the committed record's disclosure, causes
        ``main(["--check"])`` to return a non-zero exit code.
        """
        # Function-level drift detection using the in-memory Hypothesis record.
        with tempfile.TemporaryDirectory() as tmp_dir:
            power_md_path = Path(tmp_dir) / "POWER.md"
            power_md_path.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")

            correct_body = render_disclosure(record)
            write_disclosure_region(power_md_path, correct_body)
            # Sanity: the un-mutated region reports no drift.
            assert check_disclosure(power_md_path, record) == []

            # Mutate the region to a body that is guaranteed != the correct one.
            drifted_body = correct_body + _DRIFT_SENTINEL
            assert drifted_body != correct_body
            write_disclosure_region(power_md_path, drifted_body)

            drift = check_disclosure(power_md_path, record)
            assert drift != []

        # CLI-level exit code using the committed record, so the record loaded by
        # ``main(--check)`` and the POWER.md disclosure are a consistent pair
        # before mutation, isolating the drift as the sole cause of failure.
        committed_record = load_coverage_record()
        with tempfile.TemporaryDirectory() as tmp_dir:
            power_md_path = Path(tmp_dir) / "POWER.md"
            power_md_path.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")

            committed_body = render_disclosure(committed_record)
            write_disclosure_region(power_md_path, committed_body)
            # The consistent pair passes the check (exit 0) before mutation.
            assert main(["--check", "--power-md", str(power_md_path)]) == 0

            # Mutate the region so it drifts from the committed record.
            write_disclosure_region(
                power_md_path, committed_body + _DRIFT_SENTINEL
            )
            assert main(["--check", "--power-md", str(power_md_path)]) == 1


# ---------------------------------------------------------------------------
# Property 13: Disclosure write is scoped to the generated region
# ---------------------------------------------------------------------------

#: The begin/end marker lines that bound the example-coverage generated region.
#: Kept in one place so the scoped-write property test cannot diverge from the
#: marker scheme used by ``write_disclosure_region``.
_BEGIN_MARKER = "<!-- BEGIN GENERATED: example-coverage -->"
_END_MARKER = "<!-- END GENERATED: example-coverage -->"


class TestDisclosureScopedWrite:
    """Validates Requirement 4.4 (write touches only the generated region)."""

    # Feature: language-example-coverage, Property 13: Disclosure write is scoped
    # to the generated region
    @settings(max_examples=100)
    @given(record=st_coverage_record())
    def test_write_changes_only_bytes_between_the_markers(
        self, record: CoverageRecord
    ) -> None:
        """Writing the region leaves every byte outside the markers unchanged.

        For any Coverage_Record and a POWER.md document containing the
        example-coverage markers with surrounding prose, calling
        ``write_disclosure_region`` rewrites only the text strictly between the
        begin and end markers. The prefix up to and including the begin-marker
        line and the suffix from the end-marker line onward are byte-for-byte
        identical to the original document; only the region body changes.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            power_md_path = Path(tmp_dir) / "POWER.md"
            power_md_path.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")
            original = power_md_path.read_text(encoding="utf-8")

            body = render_disclosure(record)
            write_disclosure_region(power_md_path, body)
            new = power_md_path.read_text(encoding="utf-8")

            # The rewritten document still contains both markers.
            assert _BEGIN_MARKER in new
            assert _END_MARKER in new

            # Prefix: everything up to and including the begin-marker line.
            orig_begin = original.index(_BEGIN_MARKER)
            orig_prefix_end = original.index("\n", orig_begin) + 1
            new_begin = new.index(_BEGIN_MARKER)
            new_prefix_end = new.index("\n", new_begin) + 1
            assert new[:new_prefix_end] == original[:orig_prefix_end]

            # Suffix: everything from the end-marker line onward. The end-marker
            # index may shift if the body length changes, so it is recomputed
            # independently for each document before comparison.
            orig_end = original.index(_END_MARKER)
            new_end = new.index(_END_MARKER)
            assert new[new_end:] == original[orig_end:]

            # The region body actually became the rendered disclosure body.
            written_region = new[new_prefix_end:new_end]
            assert body in written_region


# ---------------------------------------------------------------------------
# Property 4: Validation result drives the check exit code
# ---------------------------------------------------------------------------


def _record_to_yaml_dict(record: CoverageRecord) -> dict:
    """Serialize a CoverageRecord into the mapping shape the loader expects.

    Args:
        record: The in-memory record to serialize.

    Returns:
        A plain dict matching the Coverage_Record YAML schema read by
        ``load_coverage_record`` (``metadata.snapshot.{last_observed,
        senzing_version}``, ``languages``, ``topics.<id>.label``, and
        ``coverage.<lang>.<topic>``).
    """
    return {
        "metadata": {
            "snapshot": {
                "last_observed": record.snapshot.last_observed,
                "senzing_version": record.snapshot.senzing_version,
            }
        },
        "languages": list(record.languages),
        "topics": {
            topic_id: {"label": label}
            for topic_id, label in record.topics.items()
        },
        "coverage": {
            lang: dict(entries) for lang, entries in record.coverage.items()
        },
    }


def _dump_record_yaml(data: dict, path: Path) -> None:
    """Write a Coverage_Record mapping to ``path`` as YAML.

    Args:
        data: The record mapping (typically from ``_record_to_yaml_dict``).
        path: Destination YAML file path.
    """
    import yaml  # lazy import: PyYAML is the only non-stdlib dependency

    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


#: A status string guaranteed to fall outside VALID_STATUSES, used to inject a
#: status-value schema violation into a serialized record.
_INVALID_STATUS = "bogus"


def _inject_schema_violation(
    data: dict, defect: str, language: str, topic_id: str
) -> None:
    """Mutate a serialized record mapping in place to inject one schema defect.

    Args:
        data: The record mapping to mutate (from ``_record_to_yaml_dict``).
        defect: Which defect to inject: ``"bad_status"``, ``"drop_entry"``,
            ``"drop_snapshot"``, or ``"blank_label"``.
        language: A language present in the record (target for coverage defects).
        topic_id: A topic present in the record (target for the defect).
    """
    if defect == "bad_status":
        data["coverage"][language][topic_id] = _INVALID_STATUS
    elif defect == "drop_entry":
        del data["coverage"][language][topic_id]
    elif defect == "drop_snapshot":
        del data["metadata"]["snapshot"]["last_observed"]
    elif defect == "blank_label":
        data["topics"][topic_id]["label"] = ""


class TestCheckExitCode:
    """Validates Requirement 7.4 (validation result drives the check exit code)."""

    # Feature: language-example-coverage, Property 4: Validation result drives
    # the check exit code
    @settings(max_examples=100)
    @given(record=st_coverage_record(), data=st.data())
    def test_check_exit_code_reflects_validation_result(
        self, record: CoverageRecord, data: st.DataObject
    ) -> None:
        """main(--check) exits 0 when valid+consistent, 1 (with message) on defect.

        For any Coverage_Record, serializing a schema-valid record to disk and
        writing the disclosure rendered from that same record yields a
        valid-and-consistent pair, so ``main(["--check", ...])`` returns 0.
        Injecting a single schema violation into the serialized record makes
        ``main(["--check", ...])`` return 1 and emit a non-empty descriptive
        message on stderr.
        """
        valid_dict = _record_to_yaml_dict(record)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            # Case (a): valid + consistent record -> exit 0.
            good_yaml = tmp / "good.yaml"
            _dump_record_yaml(valid_dict, good_yaml)
            good_record = load_coverage_record(good_yaml)

            good_power_md = tmp / "GOOD_POWER.md"
            good_power_md.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")
            write_disclosure_region(
                good_power_md, render_disclosure(good_record)
            )

            assert (
                main(
                    [
                        "--check",
                        "--record",
                        str(good_yaml),
                        "--power-md",
                        str(good_power_md),
                    ]
                )
                == 0
            )

            # Case (b): one schema violation -> exit 1 with a non-empty message.
            defect = data.draw(
                st.sampled_from(
                    ["bad_status", "drop_entry", "drop_snapshot", "blank_label"]
                )
            )
            language = data.draw(st.sampled_from(record.languages))
            topic_id = data.draw(st.sampled_from(sorted(record.topics)))

            bad_dict = _record_to_yaml_dict(record)
            _inject_schema_violation(bad_dict, defect, language, topic_id)

            bad_yaml = tmp / "bad.yaml"
            _dump_record_yaml(bad_dict, bad_yaml)

            # Render a disclosure consistent with the (defective) loaded record so
            # the injected schema violation is the sole cause of the failure.
            bad_record = load_coverage_record(bad_yaml)
            bad_power_md = tmp / "BAD_POWER.md"
            bad_power_md.write_text(_POWER_MD_TEMPLATE, encoding="utf-8")
            write_disclosure_region(
                bad_power_md, render_disclosure(bad_record)
            )

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--check",
                        "--record",
                        str(bad_yaml),
                        "--power-md",
                        str(bad_power_md),
                    ]
                )

            assert exit_code == 1
            assert stderr.getvalue().strip() != ""


# ---------------------------------------------------------------------------
# Property 14: Report-mode exit codes
# ---------------------------------------------------------------------------

#: Malformed YAML content that PyYAML cannot parse (unterminated flow mapping
#: and sequence), used to exercise the unparseable-record error path.
_UNPARSEABLE_YAML = "metadata: {unterminated: [1, 2, 3\n"


class TestReportModeExitCodes:
    """Validates Requirements 3.6 and 3.7 (report-mode exit codes)."""

    # Feature: language-example-coverage, Property 14: Report-mode exit codes
    @settings(max_examples=100)
    @given(record=st_coverage_record(), data=st.data())
    def test_report_mode_exit_codes(
        self, record: CoverageRecord, data: st.DataObject
    ) -> None:
        """Report mode exits 0 for a valid record; 1 (with message) on load error.

        For any schema-valid Coverage_Record serialized to disk, report mode
        (``main(["--record", path])``) returns 0. For a missing record path or
        unparseable record content, ``main`` returns 1 after emitting a
        non-empty descriptive error message on stderr.
        """
        valid_dict = _record_to_yaml_dict(record)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)

            # Case (a): schema-valid record on disk -> report mode exits 0.
            good_yaml = tmp / "good.yaml"
            _dump_record_yaml(valid_dict, good_yaml)

            with redirect_stdout(io.StringIO()):
                assert main(["--record", str(good_yaml)]) == 0

            # Case (b): missing path -> exit 1 with a non-empty error message.
            missing_yaml = tmp / "does-not-exist.yaml"
            stderr_missing = io.StringIO()
            with redirect_stderr(stderr_missing), redirect_stdout(io.StringIO()):
                missing_exit = main(["--record", str(missing_yaml)])
            assert missing_exit == 1
            assert stderr_missing.getvalue().strip() != ""

            # Case (c): unparseable content -> exit 1 with a non-empty message.
            bad_yaml = tmp / "unparseable.yaml"
            bad_yaml.write_text(_UNPARSEABLE_YAML, encoding="utf-8")
            stderr_bad = io.StringIO()
            with redirect_stderr(stderr_bad), redirect_stdout(io.StringIO()):
                bad_exit = main(["--record", str(bad_yaml)])
            assert bad_exit == 1
            assert stderr_bad.getvalue().strip() != ""
