"""Property-based tests for business_case_offer.py using Hypothesis.

Feature: module1-business-case-offer

This module hosts the shared Hypothesis strategies (``st_scenario`` /
``st_scenario_data`` and their building blocks) reused across the
business-case-offer property tests, plus the property tests themselves. The
helper module under test is pure logic over a large input space of generated
scenarios and multi-source datasets, which makes it a good property-testing
target (see the design's Testing Strategy).
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from business_case_offer import (  # noqa: E402  (path manipulated above)
    GENERATED_MARKER,
    RECOGNIZED_CATEGORIES,
    GeneratedScenario,
    ScenarioDataSource,
    detect_mapping_complexity,
    record_data_sources,
    render_business_problem,
    validate_scenario,
)
from data_sources import parse_registry_yaml  # noqa: E402  (path manipulated above)

_COMPLEXITY_TRAITS = frozenset(
    {"differing_field_names", "combine_or_split", "inconsistent_formatting"}
)

# ---------------------------------------------------------------------------
# Shared element strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# A pool of generic, realistic entity attribute names. Drawing from a shared
# pool (rather than arbitrary text) lets later mapping-complexity tests inject
# differing/combinable/inconsistent fields meaningfully while keeping shape
# tests fast. These are generic attributes, not Senzing/CORD specifics.
_FIELD_NAME_POOL: tuple[str, ...] = (
    "name",
    "full_name",
    "first_name",
    "last_name",
    "middle_name",
    "phone",
    "telephone",
    "email",
    "email_address",
    "address",
    "street",
    "city",
    "state",
    "zip",
    "dob",
    "ssn",
)

# Source-name alphabet kept to identifier-safe characters so distinctness is
# unambiguous and serialization-friendly for downstream recording tests.
_SOURCE_NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_"

# Blank / whitespace-only values used to build deliberately-invalid variants.
_BLANK_VALUES: tuple[str, ...] = ("", " ", "  ", "\t", "\n", " \t\n ")


@composite
def st_nonempty_text(draw) -> str:
    """Draw text that is non-empty after trimming.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A string whose ``str.strip()`` is non-empty.
    """
    return draw(st.text(min_size=1, max_size=80).filter(lambda value: value.strip()))


@composite
def st_blank_text(draw) -> str:
    """Draw an empty or whitespace-only string.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A string whose ``str.strip()`` is empty.
    """
    return draw(st.sampled_from(_BLANK_VALUES))


@composite
def st_category(draw) -> str:
    """Draw exactly one recognized Module 1 use-case category.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A value drawn from :data:`RECOGNIZED_CATEGORIES`.
    """
    return draw(st.sampled_from(sorted(RECOGNIZED_CATEGORIES)))


@composite
def st_off_list_category(draw) -> str:
    """Draw a category value that is NOT in the recognized set.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A string not present in :data:`RECOGNIZED_CATEGORIES` (may be empty).
    """
    return draw(
        st.text(min_size=0, max_size=24).filter(
            lambda value: value not in RECOGNIZED_CATEGORIES
        )
    )


@composite
def st_source_name(draw) -> str:
    """Draw a non-empty, identifier-safe data-source name.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty source-name string.
    """
    name = draw(st.text(alphabet=_SOURCE_NAME_ALPHABET, min_size=1, max_size=14))
    return name


@composite
def st_data_source(draw, name: str | None = None) -> ScenarioDataSource:
    """Draw a single :class:`ScenarioDataSource` with >= 1 record.

    Args:
        draw: The Hypothesis draw callable.
        name: An optional explicit source name; when omitted one is drawn.

    Returns:
        A ``ScenarioDataSource`` carrying at least one field and one record.
    """
    source_name = name if name is not None else draw(st_source_name())
    fields = draw(
        st.lists(st.sampled_from(_FIELD_NAME_POOL), min_size=1, max_size=5, unique=True)
    )
    record_count = draw(st.integers(min_value=1, max_value=4))
    records = [
        {fld: draw(st.text(min_size=1, max_size=12)) for fld in fields}
        for _ in range(record_count)
    ]
    return ScenarioDataSource(name=source_name, fields=fields, records=records)


@composite
def st_scenario_data(
    draw, min_sources: int = 2, max_sources: int = 4
) -> list[ScenarioDataSource]:
    """Draw a multi-source dataset of distinctly named sources.

    Produces ``min_sources``..``max_sources`` sources with distinct names, each
    contributing at least one record — the shape a valid Generated_Scenario
    requires (Requirements 3.1). Reused by the multi-source, mapping-complexity,
    and recording property tests.

    Args:
        draw: The Hypothesis draw callable.
        min_sources: The minimum number of distinct sources (>= 1).
        max_sources: The maximum number of distinct sources.

    Returns:
        A list of distinctly named ``ScenarioDataSource`` objects.
    """
    upper = max(min_sources, max_sources)
    count = draw(st.integers(min_value=min_sources, max_value=upper))
    names = draw(
        st.lists(st_source_name(), min_size=count, max_size=count, unique=True)
    )
    return [draw(st_data_source(name=source_name)) for source_name in names]


@composite
def st_scenario(draw) -> GeneratedScenario:
    """Draw a structurally valid :class:`GeneratedScenario`.

    The drawn scenario satisfies every ``validate_scenario`` invariant: a
    non-empty problem description and definition of success, a recognized
    use-case category, at least two distinctly named sources each with a record,
    a known provenance, and a ``selected_pattern_category`` that is either unset
    or equal to the category. Later tests build deliberately-invalid variants
    from this base via :func:`dataclasses.replace`.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A valid ``GeneratedScenario``.
    """
    category = draw(st_category())
    pattern_set = draw(st.booleans())
    return GeneratedScenario(
        problem_description=draw(st_nonempty_text()),
        use_case_category=category,
        success_definition=draw(st_nonempty_text()),
        data_sources=draw(st_scenario_data()),
        provenance=draw(st.sampled_from(["cord", "generated"])),
        selected_pattern_category=category if pattern_set else None,
    )


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestScenarioShape:
    """Property 1 — a Generated_Scenario has a valid shape."""

    # Feature: module1-business-case-offer, Property 1: Generated scenario has a valid shape
    @given(
        scenario=st_scenario(),
        blank=st_blank_text(),
        off_category=st_off_list_category(),
    )
    def test_valid_scenario_shape(
        self, scenario: GeneratedScenario, blank: str, off_category: str
    ) -> None:
        """validate_scenario passes valid scenarios and rejects invalid shapes.

        Validates: Requirements 2.1, 2.2
        """
        # A fully valid scenario reports no violations.
        assert validate_scenario(scenario) == []

        # Empty/whitespace problem description is rejected (2.1).
        blank_description = replace(scenario, problem_description=blank)
        description_violations = validate_scenario(blank_description)
        assert any("problem_description" in v for v in description_violations)

        # Empty/whitespace definition of success is rejected (2.1).
        blank_success = replace(scenario, success_definition=blank)
        success_violations = validate_scenario(blank_success)
        assert any("success_definition" in v for v in success_violations)

        # An off-list use-case category is rejected (2.2).
        off_list = replace(scenario, use_case_category=off_category)
        category_violations = validate_scenario(off_list)
        assert any("use_case_category" in v for v in category_violations)


class TestSelectedPatternCategory:
    """Property 2 — scenario category matches a selected pattern."""

    # Feature: module1-business-case-offer, Property 2: Scenario category matches a selected pattern
    @given(
        scenario=st_scenario(),
        other_category=st_category(),
        off_category=st_off_list_category(),
    )
    def test_category_matches_selected_pattern(
        self,
        scenario: GeneratedScenario,
        other_category: str,
        off_category: str,
    ) -> None:
        """validate_scenario flags a category mismatch iff the selected pattern differs.

        For a scenario whose ``selected_pattern_category`` is set,
        ``validate_scenario`` reports no category-mismatch violation exactly when
        ``selected_pattern_category`` equals ``use_case_category``.

        Validates: Requirements 2.3
        """

        def has_mismatch_violation(s: GeneratedScenario) -> bool:
            return any(
                "selected_pattern_category" in v for v in validate_scenario(s)
            )

        # Matching: selected pattern equals the use-case category -> no mismatch.
        matching = replace(
            scenario, selected_pattern_category=scenario.use_case_category
        )
        assert not has_mismatch_violation(matching)

        # Mismatching against another recognized category (when it actually
        # differs) -> a category-mismatch violation is reported.
        if other_category != scenario.use_case_category:
            mismatched = replace(scenario, selected_pattern_category=other_category)
            assert has_mismatch_violation(mismatched)

        # Mismatching against an off-list value (when it differs) is likewise a
        # category mismatch, independent of the off-list category violation.
        if off_category != scenario.use_case_category:
            mismatched_off = replace(
                scenario, selected_pattern_category=off_category
            )
            assert has_mismatch_violation(mismatched_off)


class TestMultiSourceProvenance:
    """Property 3 — scenario data is multi-source with known provenance."""

    # Feature: module1-business-case-offer, Property 3: Scenario data is multi-source with known provenance
    @given(
        sources=st_scenario_data(),
        provenance=st.sampled_from(["cord", "generated"]),
        category=st_category(),
    )
    def test_data_is_multi_source(
        self,
        sources: list[ScenarioDataSource],
        provenance: str,
        category: str,
    ) -> None:
        """Valid scenario data is multi-source with at least one record each and known provenance.

        For any valid GeneratedScenario — regardless of whether its provenance is
        "cord" or "generated" — the Scenario_Data contains two or more distinctly
        named sources, each contributing at least one record, and the provenance
        is one of {"cord", "generated"}.

        Validates: Requirements 3.1, 3.3, 3.5
        """
        scenario = GeneratedScenario(
            problem_description="problem",
            use_case_category=category,
            success_definition="success",
            data_sources=sources,
            provenance=provenance,
            selected_pattern_category=None,
        )

        # The scenario is structurally valid (no invariant violations).
        assert validate_scenario(scenario) == []

        # Two or more distinctly named sources (3.1).
        names = [source.name for source in scenario.data_sources]
        assert len(names) >= 2
        assert len(set(names)) == len(names)

        # Each source contributes at least one record (3.1).
        assert all(len(source.records) >= 1 for source in scenario.data_sources)

        # Provenance is one of the two known values (3.3, 3.5).
        assert scenario.provenance in {"cord", "generated"}


# ---------------------------------------------------------------------------
# Mapping-complexity strategy (Property 4)
# ---------------------------------------------------------------------------


@composite
def st_complex_scenario_data(draw) -> list[ScenarioDataSource]:
    """Draw multi-source data with at least one transformation trait injected.

    Because the base :func:`st_scenario_data` may yield "clean" data that needs
    no transformation, this strategy deliberately injects one of the three
    mapping-complexity traits that :func:`detect_mapping_complexity` looks for,
    so at least one trait is guaranteed present:

    - ``differing_field_names`` — two sources express the same concept under
      different field names (e.g. ``phone`` vs ``telephone``).
    - ``combine_or_split`` — one source carries a composite field while another
      carries its components (e.g. ``full_name`` vs ``first_name``/``last_name``).
    - ``inconsistent_formatting`` — two sources share a concept whose values are
      formatted differently (e.g. ``555-1234`` vs ``5551234``).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A list of distinctly named ``ScenarioDataSource`` objects exhibiting at
        least one transformation trait.
    """
    trait = draw(st.sampled_from(sorted(_COMPLEXITY_TRAITS)))
    name_a, name_b = draw(
        st.lists(st_source_name(), min_size=2, max_size=2, unique=True)
    )

    if trait == "differing_field_names":
        # Same concept, two different recognized synonyms (3.2).
        field_a, field_b = draw(
            st.sampled_from(
                [
                    ("phone", "telephone"),
                    ("email", "email_address"),
                    ("first_name", "given_name"),
                    ("last_name", "surname"),
                ]
            )
        )
        value = draw(st.text(min_size=1, max_size=12))
        source_a = ScenarioDataSource(
            name=name_a, fields=[field_a], records=[{field_a: value}]
        )
        source_b = ScenarioDataSource(
            name=name_b, fields=[field_b], records=[{field_b: value}]
        )
    elif trait == "combine_or_split":
        # One source holds a composite; another holds its components (3.2).
        composite_field, comp_one, comp_two = draw(
            st.sampled_from(
                [
                    ("full_name", "first_name", "last_name"),
                    ("address", "street", "city"),
                ]
            )
        )
        source_a = ScenarioDataSource(
            name=name_a,
            fields=[composite_field],
            records=[{composite_field: draw(st.text(min_size=1, max_size=16))}],
        )
        source_b = ScenarioDataSource(
            name=name_b,
            fields=[comp_one, comp_two],
            records=[
                {
                    comp_one: draw(st.text(min_size=1, max_size=10)),
                    comp_two: draw(st.text(min_size=1, max_size=10)),
                }
            ],
        )
    else:  # inconsistent_formatting
        # Shared concept (same field name) with differing value format
        # signatures across sources (3.2).
        formatted, plain = draw(
            st.sampled_from(
                [
                    ("555-1234", "5551234"),
                    ("2020-01-01", "01/01/2020"),
                    ("(212) 555-0100", "2125550100"),
                ]
            )
        )
        source_a = ScenarioDataSource(
            name=name_a, fields=["phone"], records=[{"phone": formatted}]
        )
        source_b = ScenarioDataSource(
            name=name_b, fields=["phone"], records=[{"phone": plain}]
        )

    return [source_a, source_b]


class TestMappingComplexity:
    """Property 4 — scenario data exhibits mapping complexity."""

    # Feature: module1-business-case-offer, Property 4: Scenario data exhibits mapping complexity
    @given(sources=st_complex_scenario_data())
    def test_mapping_complexity_present(
        self, sources: list[ScenarioDataSource]
    ) -> None:
        """Data with an injected transformation trait yields a non-empty subset.

        For any Scenario_Data with at least one transformation trait injected,
        ``detect_mapping_complexity`` returns a non-empty subset of
        ``{differing_field_names, combine_or_split, inconsistent_formatting}`` —
        i.e. the data requires at least one transformation when mapped to the
        Senzing Entity Specification.

        Validates: Requirements 3.2, 3.5
        """
        detected = detect_mapping_complexity(sources)

        # At least one transformation is required (3.2, 3.5).
        assert detected, "expected at least one mapping-complexity trait"

        # Only the three recognized transformation types are ever reported.
        assert detected <= _COMPLEXITY_TRAITS


# ---------------------------------------------------------------------------
# Business-problem rendering (Property 5)
# ---------------------------------------------------------------------------


class TestBusinessProblemCompleteness:
    """Property 5 — business problem document is complete and marked generated."""

    # Feature: module1-business-case-offer, Property 5: Business problem document is complete and marked generated
    @given(scenario=st_scenario())
    def test_business_problem_completeness(
        self, scenario: GeneratedScenario
    ) -> None:
        """render_business_problem emits all content elements plus the marker.

        For any valid GeneratedScenario, the rendered business_problem.md body
        contains the scenario's (trimmed) problem description, its use-case
        category, every distinct data source by name, the (trimmed) definition
        of success, and the observable bootcamp-generated marker — arranged in
        the standard Module 1 problem-statement structure.

        Validates: Requirements 4.1, 4.3, 4.4
        """
        document = render_business_problem(scenario)

        # The observable bootcamp-generated marker is present (4.3).
        assert GENERATED_MARKER in document

        # The (trimmed) problem description and definition of success appear
        # verbatim; render trims arbitrary text before emitting it (4.1, 4.4).
        assert scenario.problem_description.strip() in document
        assert scenario.success_definition.strip() in document

        # The use-case category appears (4.1, 4.4).
        assert scenario.use_case_category in document

        # Every distinct data source (de-duped by trimmed name) appears (4.4).
        distinct_names = []
        seen: set[str] = set()
        for source in scenario.data_sources:
            name = (source.name or "").strip()
            if name and name not in seen:
                seen.add(name)
                distinct_names.append(name)
        for name in distinct_names:
            assert name in document

        # Arranged in the standard Module 1 problem-statement structure: the
        # canonical Step 12 template section headers are present in order (4.1).
        expected_sections = [
            "## Problem Description",
            "## Use Case Category",
            "## Data Sources",
            "## Key Matching Criteria",
            "## Success Criteria",
        ]
        last = -1
        for header in expected_sections:
            index = document.find(header)
            assert index != -1, f"missing section header: {header}"
            assert index > last, f"section out of order: {header}"
            last = index


# ---------------------------------------------------------------------------
# Registry recording round-trip (Property 6)
# ---------------------------------------------------------------------------


class TestRecordingRoundTrip:
    """Property 6 — data source recording round-trips."""

    # Feature: module1-business-case-offer, Property 6: Data source recording round-trips
    @given(scenario=st_scenario())
    def test_recording_round_trip(self, scenario: GeneratedScenario) -> None:
        """record_data_sources then parse-back yields exactly the distinct sources.

        For any valid GeneratedScenario, recording its Scenario_Data via
        ``record_data_sources`` and then reading the result back through the
        ``data_sources.yaml`` registry parser yields exactly the set of distinct
        source names, with the number of recorded entries equal to the number of
        distinct sources — so a downstream module obtains every recorded source.

        Validates: Requirements 4.2, 5.1, 5.2
        """
        # The scenario's distinct source names, de-duped by trimmed name.
        expected_names: set[str] = set()
        for source in scenario.data_sources:
            name = (source.name or "").strip()
            if name:
                expected_names.add(name)

        yaml_text = record_data_sources(scenario)
        parsed = parse_registry_yaml(yaml_text)

        sources = parsed.get("sources", {})
        assert isinstance(sources, dict)

        # The original source names are preserved in each entry's ``name`` field.
        recorded_names = {
            entry.get("name") for entry in sources.values() if isinstance(entry, dict)
        }

        # The set of recorded source names equals the distinct scenario sources.
        assert recorded_names == expected_names

        # The number of recorded entries equals the number of distinct sources (4.2).
        assert len(sources) == len(expected_names)
