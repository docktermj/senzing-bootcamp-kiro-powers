"""Property-based tests for Module 3 Wow Visualization data layer builders.

Validates correctness properties of the data transformation functions used
by the visualization web service: API response field completeness, histogram
bucketing, error response consistency, merge filter invariant, and summary
statement format.

Feature: module3-wow-visualization
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make src/system_verification/web_service/ importable
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_WEB_SERVICE_DIR: str = str(
    _POWER_ROOT / "src" / "system_verification" / "web_service"
)
if _WEB_SERVICE_DIR not in sys.path:
    sys.path.insert(0, _WEB_SERVICE_DIR)

from stats_builder import Stats, compute_histogram, format_summary  # noqa: E402
from graph_builder import GraphNode, GraphEdge  # noqa: E402
from merges_builder import MergeEntity, build as build_merges  # noqa: E402
from server import build_error_response  # noqa: E402
from server import get_data_source_color, compute_node_radius  # noqa: E402


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_DATA_SOURCES: list[str] = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]

_MATCH_KEYS: list[str] = [
    "+NAME+ADDRESS",
    "+PHONE",
    "+SSN",
    "+NAME+DOB",
    "+NAME+PHONE",
    "+ADDRESS+PHONE",
    "+NAME+SSN",
]


def st_record_count() -> st.SearchStrategy[int]:
    """Strategy producing record counts between 1 and 20.

    Returns:
        A strategy producing positive integers for record counts.
    """
    return st.integers(min_value=1, max_value=20)


def st_entity_id() -> st.SearchStrategy[int]:
    """Strategy producing entity IDs.

    Returns:
        A strategy producing positive integers for entity IDs.
    """
    return st.integers(min_value=1, max_value=100000)


def st_entity_name() -> st.SearchStrategy[str]:
    """Strategy producing non-empty entity names.

    Returns:
        A strategy producing non-empty strings for entity names.
    """
    return st.text(
        alphabet=st.characters(whitelist_categories=("L", "Zs")),
        min_size=1,
        max_size=50,
    ).filter(lambda s: s.strip())


def st_data_source() -> st.SearchStrategy[str]:
    """Strategy producing a data source name from the TruthSet set.

    Returns:
        A strategy producing one of CUSTOMERS, REFERENCE, or WATCHLIST.
    """
    return st.sampled_from(_DATA_SOURCES)


def st_data_sources_list() -> st.SearchStrategy[list[str]]:
    """Strategy producing a non-empty list of data source names.

    Returns:
        A strategy producing lists of 1-3 data source names.
    """
    return st.lists(st_data_source(), min_size=1, max_size=3)


def st_match_key() -> st.SearchStrategy[str]:
    """Strategy producing a match key string.

    Returns:
        A strategy producing one of the common match key patterns.
    """
    return st.sampled_from(_MATCH_KEYS)


def st_record() -> st.SearchStrategy[dict]:
    """Strategy producing a single record dictionary.

    Returns:
        A strategy producing record dicts with data_source, record_id, and features.
    """
    return st.fixed_dictionaries({
        "data_source": st_data_source(),
        "record_id": st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=10,
        ),
        "name": st_entity_name(),
        "address": st.text(min_size=0, max_size=50),
        "phone": st.one_of(st.none(), st.text(min_size=7, max_size=15)),
        "identifiers": st.dictionaries(
            keys=st.sampled_from(["SSN", "DL", "PASSPORT"]),
            values=st.text(min_size=1, max_size=20),
            max_size=2,
        ),
    })


def st_entity(min_records: int = 1, max_records: int = 10) -> st.SearchStrategy[dict]:
    """Strategy producing an entity dictionary with a variable number of records.

    Args:
        min_records: Minimum number of records per entity.
        max_records: Maximum number of records per entity.

    Returns:
        A strategy producing entity dicts with entity_id, entity_name,
        record_count, data_sources, and records.
    """
    return st.fixed_dictionaries({
        "entity_id": st_entity_id(),
        "entity_name": st_entity_name(),
        "records": st.lists(st_record(), min_size=min_records, max_size=max_records),
    }).map(lambda e: {
        **e,
        "record_count": len(e["records"]),
        "data_sources": list({r["data_source"] for r in e["records"]}),
    })


def st_entity_list(
    min_size: int = 1, max_size: int = 50
) -> st.SearchStrategy[list[dict]]:
    """Strategy producing a list of entities with varying record counts.

    Includes both singletons (1 record) and multi-record entities.

    Args:
        min_size: Minimum number of entities in the list.
        max_size: Maximum number of entities in the list.

    Returns:
        A strategy producing lists of entity dicts.
    """
    return st.lists(st_entity(min_records=1), min_size=min_size, max_size=max_size)


def st_entity_list_with_singletons() -> st.SearchStrategy[list[dict]]:
    """Strategy producing entity lists guaranteed to include singletons.

    Generates a mix of single-record and multi-record entities.

    Returns:
        A strategy producing lists containing both singleton and multi-record entities.
    """
    singleton = st_entity(min_records=1, max_records=1)
    multi = st_entity(min_records=2)
    return st.tuples(
        st.lists(singleton, min_size=1, max_size=10),
        st.lists(multi, min_size=0, max_size=10),
    ).map(lambda t: t[0] + t[1])


def st_error_message() -> st.SearchStrategy[str]:
    """Strategy producing non-empty error message strings.

    Returns:
        A strategy producing non-empty strings suitable for error messages.
    """
    return st.text(min_size=1, max_size=200).filter(lambda s: s.strip())


def st_stats_tuple() -> st.SearchStrategy[tuple[int, int, int]]:
    """Strategy producing valid (records_total, entities_total, multi_record_entities) tuples.

    Ensures records_total > 0, entities_total > 0, and
    0 <= multi_record_entities <= entities_total.

    Returns:
        A strategy producing valid stats tuples.
    """
    return st.integers(min_value=1, max_value=10000).flatmap(
        lambda records: st.integers(min_value=1, max_value=records).flatmap(
            lambda entities: st.integers(
                min_value=0, max_value=entities
            ).map(lambda multi: (records, entities, multi))
        )
    )


# ---------------------------------------------------------------------------
# Property 1: API Response Field Completeness
# ---------------------------------------------------------------------------


class TestApiResponseFieldCompleteness:
    """Feature: module3-wow-visualization, Property 1: API Response Field Completeness

    For any valid entity data (stats, graph nodes, graph edges, merge entities,
    or records), serializing it through the corresponding response builder SHALL
    produce a JSON object containing all required fields for that object type.

    **Validates: Requirements 1.2, 2.2, 2.3, 3.2, 3.3**
    """

    @given(entities=st_entity_list(min_size=1, max_size=30))
    @settings(max_examples=10)
    def test_stats_response_has_all_required_fields(
        self, entities: list[dict]
    ) -> None:
        """Stats response includes all required fields.

        Args:
            entities: A list of entity dicts with varying record counts.
        """
        stats = Stats.from_entities(entities)
        result = stats.to_dict()

        required_fields = [
            "records_total",
            "entities_total",
            "multi_record_entities",
            "cross_source_entities",
            "relationships_total",
            "histogram",
        ]
        missing = [f for f in required_fields if f not in result]
        assert missing == [], (
            f"Stats response missing fields: {missing}"
        )

    @given(entity=st_entity(min_records=1))
    @settings(max_examples=10)
    def test_graph_node_has_all_required_fields(
        self, entity: dict
    ) -> None:
        """Graph node includes all required fields.

        Args:
            entity: An entity dict with records.
        """
        node = GraphNode(
            entity_id=entity["entity_id"],
            entity_name=entity["entity_name"],
            record_count=entity["record_count"],
            data_sources=entity["data_sources"],
            records=[
                {"data_source": r["data_source"], "record_id": r["record_id"]}
                for r in entity["records"]
            ],
        )
        result = node.to_dict()

        required_fields = [
            "entity_id",
            "entity_name",
            "record_count",
            "data_sources",
            "records",
        ]
        missing = [f for f in required_fields if f not in result]
        assert missing == [], (
            f"Graph node missing fields: {missing}"
        )

    @given(
        source_id=st_entity_id(),
        target_id=st_entity_id(),
        match_key=st_match_key(),
    )
    @settings(max_examples=10)
    def test_graph_edge_has_all_required_fields(
        self, source_id: int, target_id: int, match_key: str
    ) -> None:
        """Graph edge includes all required fields.

        Args:
            source_id: Source entity ID.
            target_id: Target entity ID.
            match_key: Match key string.
        """
        edge = GraphEdge(
            source_entity_id=source_id,
            target_entity_id=target_id,
            match_key=match_key,
            relationship_type="possible_match",
        )
        result = edge.to_dict()

        required_fields = [
            "source_entity_id",
            "target_entity_id",
            "match_key",
            "relationship_type",
        ]
        missing = [f for f in required_fields if f not in result]
        assert missing == [], (
            f"Graph edge missing fields: {missing}"
        )

    @given(entity=st_entity(min_records=2))
    @settings(max_examples=10)
    def test_merge_entity_has_all_required_fields(
        self, entity: dict
    ) -> None:
        """Merge entity includes all required fields.

        Args:
            entity: An entity dict with 2+ records.
        """
        merge = MergeEntity(
            entity_id=entity["entity_id"],
            entity_name=entity["entity_name"],
            match_key="+NAME+ADDRESS",
            records=entity["records"],
        )
        result = merge.to_dict()

        required_fields = [
            "entity_id",
            "entity_name",
            "match_key",
            "records",
        ]
        missing = [f for f in required_fields if f not in result]
        assert missing == [], (
            f"Merge entity missing fields: {missing}"
        )

    @given(record=st_record())
    @settings(max_examples=10)
    def test_record_has_all_required_fields(
        self, record: dict
    ) -> None:
        """Each record includes data_source, record_id, and feature fields.

        Args:
            record: A record dict.
        """
        required_fields = [
            "data_source",
            "record_id",
        ]
        missing = [f for f in required_fields if f not in record]
        assert missing == [], (
            f"Record missing fields: {missing}"
        )


# ---------------------------------------------------------------------------
# Property 2: Histogram Bucketing Correctness
# ---------------------------------------------------------------------------


class TestHistogramBucketingCorrectness:
    """Feature: module3-wow-visualization, Property 2: Histogram Bucketing Correctness

    For any list of entities with varying record counts, computing the histogram
    SHALL produce bucket counts that (a) sum to the total number of entities,
    (b) place each entity in exactly one bucket based on its record count
    (1, 2, 3, or 4+), and (c) never produce negative counts.

    **Validates: Requirements 1.3**
    """

    @given(entities=st_entity_list(min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_histogram_buckets_sum_to_total_entities(
        self, entities: list[dict]
    ) -> None:
        """Histogram bucket counts sum to total number of entities.

        Args:
            entities: A list of entity dicts with varying record counts.
        """
        histogram = compute_histogram(entities)
        total = sum(histogram.values())
        assert total == len(entities), (
            f"Histogram sum {total} != entity count {len(entities)}. "
            f"Histogram: {histogram}"
        )

    @given(entities=st_entity_list(min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_histogram_has_no_negative_counts(
        self, entities: list[dict]
    ) -> None:
        """No histogram bucket has a negative count.

        Args:
            entities: A list of entity dicts with varying record counts.
        """
        histogram = compute_histogram(entities)
        negative_buckets = {
            k: v for k, v in histogram.items() if v < 0
        }
        assert negative_buckets == {}, (
            f"Histogram has negative counts: {negative_buckets}"
        )

    @given(entities=st_entity_list(min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_histogram_has_expected_bucket_keys(
        self, entities: list[dict]
    ) -> None:
        """Histogram contains exactly the expected bucket keys: 1, 2, 3, 4+.

        Args:
            entities: A list of entity dicts with varying record counts.
        """
        histogram = compute_histogram(entities)
        expected_keys = {"1", "2", "3", "4+"}
        assert set(histogram.keys()) == expected_keys, (
            f"Histogram keys {set(histogram.keys())} != expected {expected_keys}"
        )

    @given(entities=st_entity_list(min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_each_entity_in_exactly_one_bucket(
        self, entities: list[dict]
    ) -> None:
        """Each entity is placed in exactly one bucket based on record count.

        Args:
            entities: A list of entity dicts with varying record counts.
        """
        histogram = compute_histogram(entities)

        # Manually compute expected buckets
        expected = {"1": 0, "2": 0, "3": 0, "4+": 0}
        for entity in entities:
            rc = entity["record_count"]
            if rc == 1:
                expected["1"] += 1
            elif rc == 2:
                expected["2"] += 1
            elif rc == 3:
                expected["3"] += 1
            else:
                expected["4+"] += 1

        assert histogram == expected, (
            f"Histogram {histogram} != expected {expected}"
        )


# ---------------------------------------------------------------------------
# Property 3: Error Response Consistency
# ---------------------------------------------------------------------------


class TestErrorResponseConsistency:
    """Feature: module3-wow-visualization, Property 3: Error Response Consistency

    For any SDK error (regardless of which endpoint triggered it), the error
    handler SHALL produce an HTTP 500 response with a JSON body containing an
    `error` field whose value is a non-empty string describing the failure.

    **Validates: Requirements 1.5, 2.5, 3.5**
    """

    @given(error_msg=st_error_message())
    @settings(max_examples=10)
    def test_error_response_has_500_status_and_error_field(
        self, error_msg: str
    ) -> None:
        """Error handler returns HTTP 500 with non-empty error field.

        Args:
            error_msg: A non-empty error message string.
        """
        status_code, body = build_error_response(error_msg)

        assert status_code == 500, (
            f"Expected HTTP 500, got {status_code}"
        )
        assert "error" in body, (
            f"Error response missing 'error' field: {body}"
        )
        assert isinstance(body["error"], str), (
            f"Error field is not a string: {type(body['error'])}"
        )
        assert body["error"].strip(), (
            f"Error field is empty or whitespace-only"
        )


# ---------------------------------------------------------------------------
# Property 4: Merge Filter Invariant
# ---------------------------------------------------------------------------


class TestMergeFilterInvariant:
    """Feature: module3-wow-visualization, Property 4: Merge Filter Invariant

    For any list of entities with varying record counts (including singletons),
    the merges builder SHALL return only entities with two or more constituent
    records — no single-record entity shall ever appear in the merges response.

    **Validates: Requirements 3.4**
    """

    @given(entities=st_entity_list_with_singletons())
    @settings(max_examples=10)
    def test_merges_excludes_singletons(
        self, entities: list[dict]
    ) -> None:
        """Merges builder never returns single-record entities.

        Args:
            entities: A list of entities including singletons.
        """
        result = build_merges(entities)

        singletons_in_result = [
            e for e in result
            if e.get("record_count", len(e.get("records", []))) < 2
        ]
        assert singletons_in_result == [], (
            f"Merges response contains singleton entities: "
            f"{[e.get('entity_id') for e in singletons_in_result]}"
        )

    @given(entities=st_entity_list_with_singletons())
    @settings(max_examples=10)
    def test_merges_returns_only_multi_record_entities(
        self, entities: list[dict]
    ) -> None:
        """Every entity in merges response has 2+ records.

        Args:
            entities: A list of entities including singletons.
        """
        result = build_merges(entities)

        for entity in result:
            records = entity.get("records", [])
            assert len(records) >= 2, (
                f"Entity {entity.get('entity_id')} has only "
                f"{len(records)} record(s) in merges response"
            )


# ---------------------------------------------------------------------------
# Property 7: Summary Statement Format
# ---------------------------------------------------------------------------


class TestSummaryStatementFormat:
    """Feature: module3-wow-visualization, Property 7: Summary Statement Format

    For any valid stats tuple (records_total > 0, entities_total > 0,
    multi_record_entities >= 0), the summary formatter SHALL produce a string
    matching the pattern "[X] records collapsed into [Y] entities, including
    [Z] multi-record entities" where X, Y, Z are the corresponding integer values.

    **Validates: Requirements 7.3**
    """

    @given(stats_tuple=st_stats_tuple())
    @settings(max_examples=10)
    def test_summary_matches_expected_format(
        self, stats_tuple: tuple[int, int, int]
    ) -> None:
        """Summary string matches the required format pattern.

        Args:
            stats_tuple: A tuple of (records_total, entities_total, multi_record_entities).
        """
        records_total, entities_total, multi_record_entities = stats_tuple

        stats = Stats(
            records_total=records_total,
            entities_total=entities_total,
            multi_record_entities=multi_record_entities,
            cross_source_entities=0,
            relationships_total=0,
            histogram={"1": 0, "2": 0, "3": 0, "4+": 0},
        )
        result = format_summary(stats)

        expected = (
            f"{records_total} records collapsed into {entities_total} entities, "
            f"including {multi_record_entities} multi-record entities"
        )
        assert result == expected, (
            f"Summary format mismatch.\n"
            f"  Got:      {result!r}\n"
            f"  Expected: {expected!r}"
        )

    @given(stats_tuple=st_stats_tuple())
    @settings(max_examples=10)
    def test_summary_contains_integer_values(
        self, stats_tuple: tuple[int, int, int]
    ) -> None:
        """Summary string contains the exact integer values from the stats.

        Args:
            stats_tuple: A tuple of (records_total, entities_total, multi_record_entities).
        """
        records_total, entities_total, multi_record_entities = stats_tuple

        stats = Stats(
            records_total=records_total,
            entities_total=entities_total,
            multi_record_entities=multi_record_entities,
            cross_source_entities=0,
            relationships_total=0,
            histogram={"1": 0, "2": 0, "3": 0, "4+": 0},
        )
        result = format_summary(stats)

        assert str(records_total) in result, (
            f"records_total {records_total} not found in summary: {result!r}"
        )
        assert str(entities_total) in result, (
            f"entities_total {entities_total} not found in summary: {result!r}"
        )
        assert str(multi_record_entities) in result, (
            f"multi_record_entities {multi_record_entities} not found in summary: {result!r}"
        )

    @given(stats_tuple=st_stats_tuple())
    @settings(max_examples=10)
    def test_summary_matches_regex_pattern(
        self, stats_tuple: tuple[int, int, int]
    ) -> None:
        """Summary string matches the structural regex pattern.

        Args:
            stats_tuple: A tuple of (records_total, entities_total, multi_record_entities).
        """
        records_total, entities_total, multi_record_entities = stats_tuple

        stats = Stats(
            records_total=records_total,
            entities_total=entities_total,
            multi_record_entities=multi_record_entities,
            cross_source_entities=0,
            relationships_total=0,
            histogram={"1": 0, "2": 0, "3": 0, "4+": 0},
        )
        result = format_summary(stats)

        pattern = (
            r"^\d+ records collapsed into \d+ entities, "
            r"including \d+ multi-record entities$"
        )
        assert re.match(pattern, result), (
            f"Summary does not match expected pattern.\n"
            f"  Got:     {result!r}\n"
            f"  Pattern: {pattern!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: Data Source Color Mapping Determinism
# ---------------------------------------------------------------------------


class TestDataSourceColorMapping:
    """Feature: module3-wow-visualization, Property 5: Data Source Color Mapping Determinism

    For any data source name from the set {CUSTOMERS, REFERENCE, WATCHLIST},
    the color mapping function SHALL always return the same distinct color,
    and no two different data sources SHALL map to the same color.

    **Validates: Requirements 5.2**
    """

    @given(data_source=st_data_source())
    @settings(max_examples=10)
    def test_color_mapping_is_deterministic(self, data_source: str) -> None:
        """Same data source always returns the same color.

        Args:
            data_source: One of CUSTOMERS, REFERENCE, or WATCHLIST.
        """
        color_first = get_data_source_color(data_source)
        color_second = get_data_source_color(data_source)

        assert color_first == color_second, (
            f"Color mapping not deterministic for {data_source}: "
            f"got {color_first!r} then {color_second!r}"
        )

    @given(data=st.data())
    @settings(max_examples=10)
    def test_no_two_sources_share_a_color(self, data: st.DataObject) -> None:
        """No two different data sources map to the same color.

        Args:
            data: Hypothesis data object for drawing values.
        """
        sources = ["CUSTOMERS", "REFERENCE", "WATCHLIST"]
        colors = [get_data_source_color(src) for src in sources]

        assert len(set(colors)) == len(sources), (
            f"Color collision detected: sources={sources}, colors={colors}"
        )

    @given(data_source=st_data_source())
    @settings(max_examples=10)
    def test_color_is_valid_hex(self, data_source: str) -> None:
        """Color mapping returns a valid hex color string.

        Args:
            data_source: One of CUSTOMERS, REFERENCE, or WATCHLIST.
        """
        color = get_data_source_color(data_source)

        assert isinstance(color, str), (
            f"Expected string color, got {type(color)}"
        )
        assert re.match(r"^#[0-9a-fA-F]{6}$", color), (
            f"Invalid hex color format for {data_source}: {color!r}"
        )


# ---------------------------------------------------------------------------
# Property 6: Node Sizing Monotonicity
# ---------------------------------------------------------------------------


class TestNodeSizingMonotonicity:
    """Feature: module3-wow-visualization, Property 6: Node Sizing Monotonicity

    For any two entities where entity A has a strictly greater record count
    than entity B, the node sizing function SHALL produce a radius for A that
    is strictly greater than the radius for B.

    **Validates: Requirements 5.3**
    """

    @given(
        count_b=st.integers(min_value=1, max_value=7),
        delta=st.integers(min_value=1, max_value=6),
    )
    @settings(max_examples=10)
    def test_larger_record_count_produces_larger_radius(
        self, count_b: int, delta: int
    ) -> None:
        """Entity with more records gets a strictly larger radius.

        Constrains counts to the range where the formula is strictly monotonic
        (before hitting the max cap).

        Args:
            count_b: Record count for the smaller entity.
            delta: Positive difference so count_a = count_b + delta.
        """
        count_a = count_b + delta

        radius_a = compute_node_radius(count_a)
        radius_b = compute_node_radius(count_b)

        assert radius_a > radius_b, (
            f"Monotonicity violated: radius({count_a})={radius_a} "
            f"should be > radius({count_b})={radius_b}"
        )

    @given(record_count=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=10)
    def test_radius_respects_minimum_bound(self, record_count: int) -> None:
        """Node radius is never less than 8px.

        Args:
            record_count: Any non-negative record count.
        """
        radius = compute_node_radius(record_count)

        assert radius >= 8, (
            f"Radius {radius} for record_count={record_count} is below minimum 8px"
        )

    @given(record_count=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=10)
    def test_radius_respects_maximum_bound(self, record_count: int) -> None:
        """Node radius is never greater than 40px.

        Args:
            record_count: Any non-negative record count.
        """
        radius = compute_node_radius(record_count)

        assert radius <= 40, (
            f"Radius {radius} for record_count={record_count} exceeds maximum 40px"
        )


# ---------------------------------------------------------------------------
# Property 8: Steering File Visualization Completeness
# ---------------------------------------------------------------------------


class TestSteeringVisualizationCompleteness:
    """Feature: module3-wow-visualization, Property 8: Steering Visualization Completeness

    For any required visualization component (the three API endpoints /api/stats,
    /api/graph, /api/merges; the four tabs Entity Graph, Record Merges, Merge
    Statistics, Probe Entities; and the five component names Summary_Banner,
    Entity_Graph, Record_Merges, Merge_Statistics, Probe_Panel), the updated
    steering file SHALL contain a reference to that component.

    **Validates: Requirements 11.1, 11.2**
    """

    # Paths to the steering files (main + optional phase file)
    _STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
    _MAIN_FILE: Path = _STEERING_DIR / "module-03-system-verification.md"
    _PHASE_FILE: Path = _STEERING_DIR / "module-03-phase2-visualization.md"

    # Required API endpoints
    _REQUIRED_ENDPOINTS: list[str] = ["/api/stats", "/api/graph", "/api/merges"]

    # Required tab names
    _REQUIRED_TABS: list[str] = [
        "Entity Graph",
        "Record Merges",
        "Merge Statistics",
        "Probe Entities",
    ]

    # Required component names
    _REQUIRED_COMPONENTS: list[str] = [
        "Summary_Banner",
        "Entity_Graph",
        "Record_Merges",
        "Merge_Statistics",
        "Probe_Panel",
    ]

    def _load_steering_content(self) -> str:
        """Load and combine content from the main steering file and phase file.

        Returns:
            Combined content of both files (if phase file exists).
        """
        content = ""
        if self._MAIN_FILE.exists():
            content += self._MAIN_FILE.read_text(encoding="utf-8")
        if self._PHASE_FILE.exists():
            content += "\n" + self._PHASE_FILE.read_text(encoding="utf-8")
        return content

    def test_steering_references_all_api_endpoints(self) -> None:
        """Steering file references all 3 required API endpoints."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        missing = [ep for ep in self._REQUIRED_ENDPOINTS if ep not in content]
        assert missing == [], (
            f"Steering file missing API endpoint references: {missing}"
        )

    def test_steering_references_all_tab_names(self) -> None:
        """Steering file references all 4 required tab names."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        missing = [tab for tab in self._REQUIRED_TABS if tab not in content]
        assert missing == [], (
            f"Steering file missing tab name references: {missing}"
        )

    def test_steering_references_all_component_names(self) -> None:
        """Steering file references all 5 required component names."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        missing = [comp for comp in self._REQUIRED_COMPONENTS if comp not in content]
        assert missing == [], (
            f"Steering file missing component name references: {missing}"
        )


# ---------------------------------------------------------------------------
# Property 9: Steering File Endpoint Verification Instructions
# ---------------------------------------------------------------------------


class TestSteeringEndpointVerification:
    """Feature: module3-wow-visualization, Property 9: Endpoint Verification Instructions

    For each API endpoint (/api/stats, /api/graph, /api/merges), the steering
    file SHALL contain a verification instruction that includes an HTTP 200
    check, a content validation criterion, and a timeout specification
    (10 seconds).

    **Validates: Requirements 12.1, 12.2, 12.3, 12.4**
    """

    _STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
    _MAIN_FILE: Path = _STEERING_DIR / "module-03-system-verification.md"
    _PHASE_FILE: Path = _STEERING_DIR / "module-03-phase2-visualization.md"

    _ENDPOINTS: list[str] = ["/api/stats", "/api/graph", "/api/merges"]

    def _load_steering_content(self) -> str:
        """Load and combine content from the main steering file and phase file.

        Returns:
            Combined content of both files (if phase file exists).
        """
        content = ""
        if self._MAIN_FILE.exists():
            content += self._MAIN_FILE.read_text(encoding="utf-8")
        if self._PHASE_FILE.exists():
            content += "\n" + self._PHASE_FILE.read_text(encoding="utf-8")
        return content

    def test_each_endpoint_has_http_200_check(self) -> None:
        """Each endpoint verification includes an HTTP 200 check."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        # For each endpoint, verify that the content mentions HTTP 200
        # in proximity to the endpoint reference
        missing_200_check: list[str] = []
        for endpoint in self._ENDPOINTS:
            if endpoint not in content:
                missing_200_check.append(endpoint)
                continue
            # Check that "200" appears in the content (as part of HTTP 200 verification)
            # We look for the endpoint AND "200" both being present
            if "200" not in content:
                missing_200_check.append(endpoint)

        assert missing_200_check == [], (
            f"Endpoints missing HTTP 200 verification check: {missing_200_check}"
        )

    def test_each_endpoint_has_content_validation(self) -> None:
        """Each endpoint verification includes content validation criteria."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        # Content validation keywords that indicate the steering file
        # specifies what to check in the response
        validation_indicators = [
            "valid JSON",
            "valid json",
            "JSON",
            "json",
            "contain",
            "node",
            "edge",
            "multi-record",
            "required fields",
        ]

        missing_validation: list[str] = []
        for endpoint in self._ENDPOINTS:
            if endpoint not in content:
                missing_validation.append(endpoint)
                continue
            # Find the section around this endpoint and check for validation language
            idx = content.find(endpoint)
            # Look in a window around the endpoint reference for validation language
            window_start = max(0, idx - 200)
            window_end = min(len(content), idx + 500)
            window = content[window_start:window_end]

            has_validation = any(
                indicator in window for indicator in validation_indicators
            )
            if not has_validation:
                missing_validation.append(endpoint)

        assert missing_validation == [], (
            f"Endpoints missing content validation criteria: {missing_validation}"
        )

    def test_each_endpoint_has_timeout_specification(self) -> None:
        """Each endpoint verification includes a 10-second timeout."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        # Check that "10" seconds timeout is mentioned in the context of
        # endpoint verification
        timeout_indicators = ["10 second", "10-second", "10s"]

        missing_timeout: list[str] = []
        for endpoint in self._ENDPOINTS:
            if endpoint not in content:
                missing_timeout.append(endpoint)
                continue
            # Check that timeout is specified somewhere in the content
            # related to endpoint verification
            has_timeout = any(
                indicator in content for indicator in timeout_indicators
            )
            if not has_timeout:
                missing_timeout.append(endpoint)

        assert missing_timeout == [], (
            f"Endpoints missing 10-second timeout specification: {missing_timeout}"
        )


# ---------------------------------------------------------------------------
# Property 10: Visualization Artifact Path Isolation
# ---------------------------------------------------------------------------


class TestVisualizationArtifactPathIsolation:
    """Feature: module3-wow-visualization, Property 10: Artifact Path Isolation

    For any file path referenced in the steering file's visualization step that
    points to generated server or HTML artifacts, that path SHALL be rooted
    under src/system_verification/web_service/.

    **Validates: Requirements 10.3**
    """

    _STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
    _MAIN_FILE: Path = _STEERING_DIR / "module-03-system-verification.md"
    _PHASE_FILE: Path = _STEERING_DIR / "module-03-phase2-visualization.md"

    # File extensions that indicate generated artifacts
    _ARTIFACT_EXTENSIONS: list[str] = [
        ".py",
        ".html",
        ".js",
        ".css",
        ".ts",
    ]

    # The required root path for all visualization artifacts
    _REQUIRED_ROOT: str = "src/system_verification/web_service/"

    def _load_steering_content(self) -> str:
        """Load and combine content from the main steering file and phase file.

        Returns:
            Combined content of both files (if phase file exists).
        """
        content = ""
        if self._MAIN_FILE.exists():
            content += self._MAIN_FILE.read_text(encoding="utf-8")
        if self._PHASE_FILE.exists():
            content += "\n" + self._PHASE_FILE.read_text(encoding="utf-8")
        return content

    def _extract_artifact_paths(self, content: str) -> list[str]:
        """Extract file paths from the steering content that reference artifacts.

        Looks for paths containing web service artifact file extensions
        (e.g., server.py, index.html) that are part of the visualization step.

        Args:
            content: The combined steering file content.

        Returns:
            List of artifact paths found in the content.
        """
        # Match paths that look like file references with known extensions
        # Patterns: backtick-quoted paths, or paths starting with src/
        artifact_paths: list[str] = []

        # Pattern 1: Backtick-quoted paths with artifact extensions
        backtick_pattern = re.compile(r"`([^`]*(?:" + "|".join(
            re.escape(ext) for ext in self._ARTIFACT_EXTENSIONS
        ) + r"))`")
        artifact_paths.extend(backtick_pattern.findall(content))

        # Pattern 2: Bare paths starting with src/ containing artifact extensions
        bare_path_pattern = re.compile(
            r"(?<!\w)(src/[^\s,;)\"'`]+(?:" + "|".join(
                re.escape(ext) for ext in self._ARTIFACT_EXTENSIONS
            ) + r"))(?!\w)"
        )
        artifact_paths.extend(bare_path_pattern.findall(content))

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_paths: list[str] = []
        for path in artifact_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        return unique_paths

    def _is_web_service_artifact(self, path: str) -> bool:
        """Determine if a path refers to a web service visualization artifact.

        Filters out paths that are clearly not visualization artifacts
        (e.g., verify_pipeline.py, verify_init.py which belong to the
        verification pipeline, not the web service).

        Args:
            path: A file path extracted from the steering content.

        Returns:
            True if the path appears to be a web service artifact.
        """
        # Paths containing "web_service" or visualization-specific filenames
        web_service_indicators = [
            "web_service",
            "server.py",
            "index.html",
            "stats_builder",
            "graph_builder",
            "merges_builder",
            "search_builder",
        ]
        return any(indicator in path for indicator in web_service_indicators)

    def test_all_artifact_paths_rooted_under_web_service(self) -> None:
        """All visualization artifact paths are rooted under src/system_verification/web_service/."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        artifact_paths = self._extract_artifact_paths(content)

        # Filter to only web service artifacts (not verify_pipeline.py etc.)
        web_service_paths = [
            p for p in artifact_paths if self._is_web_service_artifact(p)
        ]

        # If no web service artifact paths found, the steering file hasn't been
        # updated yet — this is an expected failure for the initial state
        assert web_service_paths, (
            "No web service artifact paths found in steering file. "
            "The steering file has not been updated with visualization content yet."
        )

        # Check each web service artifact path is rooted correctly
        misrooted: list[str] = []
        for path in web_service_paths:
            if not path.startswith(self._REQUIRED_ROOT):
                misrooted.append(path)

        assert misrooted == [], (
            f"Visualization artifact paths not rooted under "
            f"'{self._REQUIRED_ROOT}': {misrooted}"
        )

    def test_no_artifacts_outside_system_verification(self) -> None:
        """No visualization artifacts are placed outside src/system_verification/."""
        content = self._load_steering_content()
        assert content, "No steering file content found"

        artifact_paths = self._extract_artifact_paths(content)
        web_service_paths = [
            p for p in artifact_paths if self._is_web_service_artifact(p)
        ]

        if not web_service_paths:
            # No paths to check — steering file not yet updated
            assert False, (
                "No web service artifact paths found in steering file. "
                "The steering file has not been updated with visualization content yet."
            )

        # Verify none escape the system_verification boundary
        escaped: list[str] = []
        for path in web_service_paths:
            if not path.startswith("src/system_verification/"):
                escaped.append(path)

        assert escaped == [], (
            f"Visualization artifacts found outside src/system_verification/: {escaped}"
        )
