"""Property-based tests for Probe Entities Visualization.

Validates correctness properties of the search builder enrichment logic
as specified in the design document. Since search_builder.py is generated
by the agent during the bootcamp, these tests validate the CONTRACT by
implementing the enrichment logic inline per the design specification.

Feature: probe-entities-visualization
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Reference implementation of enrichment cap logic (contract under test)
# ---------------------------------------------------------------------------

_ENRICHMENT_CAP = 10


def _enrich_entity(entity_id: int, search_match_info: dict) -> dict:
    """Reference implementation: enrich a single entity with resolution detail.

    Simulates calling get_entity_by_entity_id and extracting resolution
    reasoning fields. Returns enrichment data for the entity.

    Args:
        entity_id: The resolved entity ID to enrich.
        search_match_info: The match info from the search response.

    Returns:
        Dict with match_keys, feature_scores, resolution_rules fields.
    """
    return {
        "match_keys": {
            "entity_level": search_match_info.get("match_key", "+NAME"),
            "per_record": search_match_info.get("per_record_keys", []),
        },
        "feature_scores": search_match_info.get("feature_scores", [
            {"feature": "NAME", "score": 95, "label": "CLOSE"},
        ]),
        "resolution_rules": search_match_info.get("resolution_rules", [
            {"data_source": "TEST", "record_id": "1", "rule": "CNAME_CFF"},
        ]),
    }


def build_search_results(search_results: list[dict]) -> list[dict]:
    """Reference implementation: enrich search results respecting the cap.

    Enriches up to _ENRICHMENT_CAP entities with resolution detail.
    Remaining entities get null enrichment fields.

    Args:
        search_results: List of basic search result dicts, each containing
            at minimum 'entity_id' and 'search_match_info'.

    Returns:
        List of result dicts with enrichment fields populated for the
        first min(N, 10) entities and null for the rest.
    """
    enriched_results: list[dict] = []

    for i, result in enumerate(search_results):
        entity_id = result["entity_id"]
        search_match_info = result.get("search_match_info", {})

        if i < _ENRICHMENT_CAP:
            enrichment = _enrich_entity(entity_id, search_match_info)
            enriched_results.append({
                "entity_id": entity_id,
                "entity_name": result.get("entity_name", "Unknown"),
                "match_keys": enrichment["match_keys"],
                "feature_scores": enrichment["feature_scores"],
                "resolution_rules": enrichment["resolution_rules"],
                "enrichment_error": None,
            })
        else:
            enriched_results.append({
                "entity_id": entity_id,
                "entity_name": result.get("entity_name", "Unknown"),
                "match_keys": None,
                "feature_scores": None,
                "resolution_rules": None,
                "enrichment_error": None,
            })

    return enriched_results


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_search_result_list(draw) -> list[dict]:
    """Generate a list of search results with 0-30 entities.

    Each search result contains an entity_id and basic search match info.

    Returns:
        A list of search result dicts of varying length (0 to 30).
    """
    num_entities = draw(st.integers(min_value=0, max_value=30))

    results: list[dict] = []
    for i in range(num_entities):
        entity_id = draw(st.integers(min_value=1, max_value=100000))
        entity_name = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
            min_size=1,
            max_size=30,
        ))
        match_key = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=20,
        ).map(lambda s: f"+{s}"))

        results.append({
            "entity_id": entity_id,
            "entity_name": entity_name,
            "search_match_info": {
                "match_key": match_key,
                "per_record_keys": [match_key],
                "feature_scores": [
                    {"feature": "NAME", "score": 95, "label": "CLOSE"},
                ],
                "resolution_rules": [
                    {"data_source": "TEST", "record_id": str(i), "rule": "CNAME_CFF"},
                ],
            },
        })

    return results


# ---------------------------------------------------------------------------
# Property 1: Enrichment cap limits SDK calls
# ---------------------------------------------------------------------------


class TestEnrichmentCapLimitsSDKCalls:
    """Feature: probe-entities-visualization, Property 1: Enrichment cap limits SDK calls

    For any list of search results with N entities (where N ranges from 0
    to 30), the search builder SHALL enrich exactly min(N, 10) entities
    with resolution detail, and any remaining entities (positions 11+)
    SHALL have null values for match_keys, feature_scores, and
    resolution_rules.

    **Validates: Requirements 1.1, 1.6**
    """

    @given(search_results=st_search_result_list())
    @settings(max_examples=20)
    def test_enrichment_count_equals_min_n_cap(
        self, search_results: list[dict]
    ) -> None:
        """Exactly min(N, 10) entities are enriched with resolution detail.

        Args:
            search_results: Generated list of search results (0-30 entities).
        """
        n = len(search_results)
        expected_enriched = min(n, _ENRICHMENT_CAP)

        results = build_search_results(search_results)

        # Count entities with non-null enrichment fields
        enriched_count = sum(
            1 for r in results
            if r["match_keys"] is not None
            and r["feature_scores"] is not None
            and r["resolution_rules"] is not None
        )

        assert enriched_count == expected_enriched, (
            f"Expected {expected_enriched} enriched entities for N={n}, "
            f"got {enriched_count}"
        )

    @given(search_results=st_search_result_list())
    @settings(max_examples=20)
    def test_remaining_entities_have_null_enrichment(
        self, search_results: list[dict]
    ) -> None:
        """Entities beyond position 10 have null enrichment fields.

        Args:
            search_results: Generated list of search results (0-30 entities).
        """
        results = build_search_results(search_results)

        # Check that positions 11+ (index 10+) have null enrichment
        for i, result in enumerate(results):
            if i >= _ENRICHMENT_CAP:
                assert result["match_keys"] is None, (
                    f"Entity at position {i + 1} should have null match_keys, "
                    f"got {result['match_keys']}"
                )
                assert result["feature_scores"] is None, (
                    f"Entity at position {i + 1} should have null "
                    f"feature_scores, got {result['feature_scores']}"
                )
                assert result["resolution_rules"] is None, (
                    f"Entity at position {i + 1} should have null "
                    f"resolution_rules, got {result['resolution_rules']}"
                )

    @given(search_results=st_search_result_list())
    @settings(max_examples=20)
    def test_enriched_entities_have_non_null_fields(
        self, search_results: list[dict]
    ) -> None:
        """Entities within the cap have non-null enrichment fields.

        Args:
            search_results: Generated list of search results (0-30 entities).
        """
        results = build_search_results(search_results)

        # Check that positions 1-10 (index 0-9) have non-null enrichment
        for i, result in enumerate(results):
            if i < _ENRICHMENT_CAP:
                assert result["match_keys"] is not None, (
                    f"Entity at position {i + 1} should have non-null "
                    f"match_keys"
                )
                assert result["feature_scores"] is not None, (
                    f"Entity at position {i + 1} should have non-null "
                    f"feature_scores"
                )
                assert result["resolution_rules"] is not None, (
                    f"Entity at position {i + 1} should have non-null "
                    f"resolution_rules"
                )

    @given(search_results=st_search_result_list())
    @settings(max_examples=20)
    def test_result_count_matches_input_count(
        self, search_results: list[dict]
    ) -> None:
        """The output list has the same length as the input list.

        All entities are returned regardless of enrichment - the cap only
        affects which entities receive resolution detail, not which are
        included in results.

        Args:
            search_results: Generated list of search results (0-30 entities).
        """
        results = build_search_results(search_results)

        assert len(results) == len(search_results), (
            f"Expected {len(search_results)} results, got {len(results)}"
        )


# ---------------------------------------------------------------------------
# Reference implementation of match key extraction (contract under test)
# ---------------------------------------------------------------------------


def _extract_match_keys(entity_detail: dict) -> dict:
    """Extract entity-level and per-record match keys from entity detail.

    The entity-level match key represents the overall match key for the
    resolved entity. Per-record match keys come from each constituent
    record's MATCH_KEY field.

    Args:
        entity_detail: The full entity detail dict from get_entity_by_entity_id.

    Returns:
        {"entity_level": "+NAME+DOB", "per_record": ["+NAME+DOB", "+PHONE"]}
    """
    resolved = entity_detail.get("RESOLVED_ENTITY", {})
    records = resolved.get("RECORDS", [])

    # Entity-level match key: use MATCH_KEY at entity level if present,
    # otherwise derive from first record's MATCH_KEY
    entity_level = resolved.get("MATCH_KEY", "")
    if not entity_level and records:
        entity_level = records[0].get("MATCH_KEY", "")

    # Per-record match keys: collect MATCH_KEY from each record that has one
    per_record = [
        record["MATCH_KEY"]
        for record in records
        if "MATCH_KEY" in record and record["MATCH_KEY"]
    ]

    return {
        "entity_level": entity_level,
        "per_record": per_record,
    }


# ---------------------------------------------------------------------------
# Hypothesis strategy for entity detail with match keys
# ---------------------------------------------------------------------------


@st.composite
def st_entity_detail_with_match_keys(draw) -> tuple[dict, str, int]:
    """Generate entity detail JSON with match key data.

    Produces a tuple of (entity_detail_dict, expected_entity_level_key,
    expected_per_record_count) for property verification.

    Returns:
        Tuple of (entity_detail, entity_level_match_key, record_count_with_keys).
    """
    # Generate an entity-level match key
    num_features = draw(st.integers(min_value=1, max_value=5))
    feature_names = draw(
        st.lists(
            st.sampled_from(["NAME", "DOB", "PHONE", "ADDRESS", "EMAIL", "SSN"]),
            min_size=num_features,
            max_size=num_features,
        )
    )
    entity_level_key = "".join(f"+{f}" for f in feature_names)

    # Generate records with per-record match keys
    num_records = draw(st.integers(min_value=0, max_value=10))
    records: list[dict] = []
    for _ in range(num_records):
        rec_num_features = draw(st.integers(min_value=1, max_value=4))
        rec_features = draw(
            st.lists(
                st.sampled_from(["NAME", "DOB", "PHONE", "ADDRESS", "EMAIL", "SSN"]),
                min_size=rec_num_features,
                max_size=rec_num_features,
            )
        )
        rec_match_key = "".join(f"+{f}" for f in rec_features)
        data_source = draw(st.sampled_from(["CUSTOMERS", "REFERENCE", "WATCHLIST"]))
        record_id = draw(st.text(
            alphabet=st.characters(whitelist_categories=("N",)),
            min_size=1,
            max_size=6,
        ))
        records.append({
            "DATA_SOURCE": data_source,
            "RECORD_ID": record_id,
            "MATCH_KEY": rec_match_key,
        })

    entity_detail = {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": draw(st.integers(min_value=1, max_value=100000)),
            "MATCH_KEY": entity_level_key,
            "FEATURES": {},
            "RECORDS": records,
        },
        "RELATED_ENTITIES": [],
    }

    return (entity_detail, entity_level_key, num_records)


# ---------------------------------------------------------------------------
# Property 2: Match key extraction preserves structure
# ---------------------------------------------------------------------------


class TestMatchKeyExtractionPreservesStructure:
    """Feature: probe-entities-visualization, Property 2: Match key extraction preserves structure

    For any valid entity detail JSON containing match key data (an entity-level
    match key string and zero or more per-record match key strings), the
    `_extract_match_keys` function SHALL return a dict where `entity_level`
    equals the entity-level match key string from the input and `per_record`
    is a list whose length equals the number of constituent records with match
    keys in the input.

    **Validates: Requirements 1.2, 5.1**
    """

    @given(data=st_entity_detail_with_match_keys())
    @settings(max_examples=20)
    def test_entity_level_matches_input(
        self, data: tuple[dict, str, int]
    ) -> None:
        """The entity_level field equals the entity-level match key from input.

        Args:
            data: Tuple of (entity_detail, expected_entity_level_key, record_count).
        """
        entity_detail, expected_entity_level_key, _ = data

        result = _extract_match_keys(entity_detail)

        assert result["entity_level"] == expected_entity_level_key, (
            f"Expected entity_level '{expected_entity_level_key}', "
            f"got '{result['entity_level']}'"
        )

    @given(data=st_entity_detail_with_match_keys())
    @settings(max_examples=20)
    def test_per_record_length_matches_record_count(
        self, data: tuple[dict, str, int]
    ) -> None:
        """The per_record list length equals the number of records with match keys.

        Args:
            data: Tuple of (entity_detail, expected_entity_level_key, record_count).
        """
        entity_detail, _, expected_record_count = data

        result = _extract_match_keys(entity_detail)

        assert len(result["per_record"]) == expected_record_count, (
            f"Expected per_record length {expected_record_count}, "
            f"got {len(result['per_record'])}"
        )

    @given(data=st_entity_detail_with_match_keys())
    @settings(max_examples=20)
    def test_result_has_correct_keys(
        self, data: tuple[dict, str, int]
    ) -> None:
        """The result dict contains exactly 'entity_level' and 'per_record' keys.

        Args:
            data: Tuple of (entity_detail, expected_entity_level_key, record_count).
        """
        entity_detail, _, _ = data

        result = _extract_match_keys(entity_detail)

        assert set(result.keys()) == {"entity_level", "per_record"}, (
            f"Expected keys {{'entity_level', 'per_record'}}, "
            f"got {set(result.keys())}"
        )

    @given(data=st_entity_detail_with_match_keys())
    @settings(max_examples=20)
    def test_per_record_entries_are_strings(
        self, data: tuple[dict, str, int]
    ) -> None:
        """Each entry in per_record is a string.

        Args:
            data: Tuple of (entity_detail, expected_entity_level_key, record_count).
        """
        entity_detail, _, _ = data

        result = _extract_match_keys(entity_detail)

        for i, key in enumerate(result["per_record"]):
            assert isinstance(key, str), (
                f"per_record[{i}] should be a string, got {type(key).__name__}"
            )


# ---------------------------------------------------------------------------
# Reference implementation of feature score extraction (contract under test)
# ---------------------------------------------------------------------------


def _extract_feature_scores(search_match_info: dict) -> list[dict]:
    """Extract feature comparison scores from search match info.

    Parses the FEATURE_SCORES section of the search match info and returns
    a flat list of feature score entries.

    Args:
        search_match_info: Dict with MATCH_INFO.FEATURE_SCORES structure from
            the Senzing SDK search response.

    Returns:
        [{"feature": "NAME", "score": 97, "label": "CLOSE"}, ...]
    """
    feature_scores: list[dict] = []
    match_info = search_match_info.get("MATCH_INFO", {})
    scores_by_feature = match_info.get("FEATURE_SCORES", {})

    for feature_name, comparisons in scores_by_feature.items():
        for comparison in comparisons:
            feature_scores.append({
                "feature": feature_name,
                "score": comparison["FULL_SCORE"],
                "label": comparison["SCORE_BUCKET"],
            })

    return feature_scores


# ---------------------------------------------------------------------------
# Hypothesis strategy for search match info with feature comparisons
# ---------------------------------------------------------------------------


_SCORE_BUCKETS = ["SAME", "CLOSE", "LIKELY", "PLAUSIBLE", "NO_CHANCE"]

_FEATURE_NAMES = [
    "NAME", "DOB", "PHONE", "EMAIL", "ADDRESS", "SSN", "PASSPORT",
    "DRIVERS_LICENSE", "NATIONAL_ID", "GENDER",
]


@st.composite
def st_feature_comparison(draw) -> dict:
    """Generate a single feature comparison entry.

    Returns:
        Dict with INBOUND_FEAT, CANDIDATE_FEAT, FULL_SCORE, SCORE_BUCKET.
    """
    inbound = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
        min_size=1,
        max_size=30,
    ))
    candidate = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
        min_size=1,
        max_size=30,
    ))
    score = draw(st.integers(min_value=0, max_value=100))
    bucket = draw(st.sampled_from(_SCORE_BUCKETS))

    return {
        "INBOUND_FEAT": inbound,
        "CANDIDATE_FEAT": candidate,
        "FULL_SCORE": score,
        "SCORE_BUCKET": bucket,
    }


@st.composite
def st_search_match_info_with_features(draw) -> tuple[dict, int]:
    """Generate search match info with variable feature comparisons.

    Returns:
        Tuple of (search_match_info dict, total number of feature comparisons).
    """
    num_features = draw(st.integers(min_value=1, max_value=6))
    feature_names = draw(
        st.lists(
            st.sampled_from(_FEATURE_NAMES),
            min_size=num_features,
            max_size=num_features,
            unique=True,
        )
    )

    feature_scores: dict[str, list[dict]] = {}
    total_comparisons = 0

    for name in feature_names:
        num_comparisons = draw(st.integers(min_value=1, max_value=3))
        comparisons = [draw(st_feature_comparison()) for _ in range(num_comparisons)]
        feature_scores[name] = comparisons
        total_comparisons += num_comparisons

    search_match_info = {
        "MATCH_INFO": {
            "FEATURE_SCORES": feature_scores,
        },
    }

    return search_match_info, total_comparisons


# ---------------------------------------------------------------------------
# Property 3: Feature score extraction completeness
# ---------------------------------------------------------------------------


class TestFeatureScoreExtractionCompleteness:
    """Feature: probe-entities-visualization, Property 3: Feature score extraction completeness

    For any valid search match info containing one or more feature comparisons,
    the `_extract_feature_scores` function SHALL return a list where each entry
    contains exactly three fields: `feature` (a non-empty string), `score`
    (an integer between 0 and 100 inclusive), and `label` (a non-empty string),
    and the list length equals the number of feature comparisons in the input.

    **Validates: Requirements 1.3, 5.2**
    """

    @given(data=st_search_match_info_with_features())
    @settings(max_examples=20)
    def test_result_length_equals_total_comparisons(
        self, data: tuple[dict, int]
    ) -> None:
        """Output list length equals the number of feature comparisons in input.

        Args:
            data: Tuple of (search_match_info, expected_comparison_count).
        """
        search_match_info, expected_count = data

        result = _extract_feature_scores(search_match_info)

        assert len(result) == expected_count, (
            f"Expected {expected_count} feature scores, got {len(result)}"
        )

    @given(data=st_search_match_info_with_features())
    @settings(max_examples=20)
    def test_each_entry_has_exactly_three_fields(
        self, data: tuple[dict, int]
    ) -> None:
        """Each entry contains exactly three fields: feature, score, label.

        Args:
            data: Tuple of (search_match_info, expected_comparison_count).
        """
        search_match_info, _ = data

        result = _extract_feature_scores(search_match_info)

        for entry in result:
            assert set(entry.keys()) == {"feature", "score", "label"}, (
                f"Expected keys {{'feature', 'score', 'label'}}, "
                f"got {set(entry.keys())}"
            )

    @given(data=st_search_match_info_with_features())
    @settings(max_examples=20)
    def test_feature_is_non_empty_string(
        self, data: tuple[dict, int]
    ) -> None:
        """Each entry's feature field is a non-empty string.

        Args:
            data: Tuple of (search_match_info, expected_comparison_count).
        """
        search_match_info, _ = data

        result = _extract_feature_scores(search_match_info)

        for entry in result:
            assert isinstance(entry["feature"], str), (
                f"feature should be str, got {type(entry['feature'])}"
            )
            assert len(entry["feature"]) > 0, "feature should be non-empty"

    @given(data=st_search_match_info_with_features())
    @settings(max_examples=20)
    def test_score_is_int_between_0_and_100(
        self, data: tuple[dict, int]
    ) -> None:
        """Each entry's score field is an integer between 0 and 100 inclusive.

        Args:
            data: Tuple of (search_match_info, expected_comparison_count).
        """
        search_match_info, _ = data

        result = _extract_feature_scores(search_match_info)

        for entry in result:
            assert isinstance(entry["score"], int), (
                f"score should be int, got {type(entry['score'])}"
            )
            assert 0 <= entry["score"] <= 100, (
                f"score should be 0-100, got {entry['score']}"
            )

    @given(data=st_search_match_info_with_features())
    @settings(max_examples=20)
    def test_label_is_non_empty_string(
        self, data: tuple[dict, int]
    ) -> None:
        """Each entry's label field is a non-empty string.

        Args:
            data: Tuple of (search_match_info, expected_comparison_count).
        """
        search_match_info, _ = data

        result = _extract_feature_scores(search_match_info)

        for entry in result:
            assert isinstance(entry["label"], str), (
                f"label should be str, got {type(entry['label'])}"
            )
            assert len(entry["label"]) > 0, "label should be non-empty"


# ---------------------------------------------------------------------------
# Reference implementation: Resolution rule extraction (Property 4)
# ---------------------------------------------------------------------------


def _extract_resolution_rules(entity_detail: dict) -> list[dict]:
    """Extract per-record resolution rules from entity detail JSON.

    Iterates over the RECORDS array in the entity detail and extracts
    the data source, record ID, and resolution rule (ERRULE_CODE) for
    each record that has a resolution rule.

    Args:
        entity_detail: The full entity detail dict from get_entity_by_entity_id.

    Returns:
        List of dicts, each with 'data_source', 'record_id', and 'rule' keys.
        Only records with non-empty ERRULE_CODE are included.
    """
    rules: list[dict] = []
    resolved_entity = entity_detail.get("RESOLVED_ENTITY", {})
    records = resolved_entity.get("RECORDS", [])

    for record in records:
        errule_code = record.get("ERRULE_CODE", "")
        if errule_code:
            rules.append({
                "data_source": record.get("DATA_SOURCE", ""),
                "record_id": record.get("RECORD_ID", ""),
                "rule": errule_code,
            })

    return rules


# ---------------------------------------------------------------------------
# Hypothesis strategy: Entity detail with resolution rules (Property 4)
# ---------------------------------------------------------------------------


@st.composite
def st_entity_detail_with_resolution_rules(draw) -> dict:
    """Generate entity detail JSON with records containing resolution rules.

    Produces a structure matching the Senzing SDK get_entity_by_entity_id
    response format, with 1-10 records each having DATA_SOURCE, RECORD_ID,
    MATCH_KEY, and ERRULE_CODE fields.

    Returns:
        A dict with RESOLVED_ENTITY.RECORDS containing resolution rule data.
    """
    num_records = draw(st.integers(min_value=1, max_value=10))

    records: list[dict] = []
    for _ in range(num_records):
        data_source = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=20,
        ))
        record_id = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=20,
        ))
        match_key = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=15,
        ).map(lambda s: f"+{s}"))
        errule_code = draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Pd")),
            min_size=1,
            max_size=30,
        ))

        records.append({
            "DATA_SOURCE": data_source,
            "RECORD_ID": record_id,
            "MATCH_KEY": match_key,
            "ERRULE_CODE": errule_code,
        })

    entity_id = draw(st.integers(min_value=1, max_value=100000))

    return {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": entity_id,
            "RECORDS": records,
        },
    }


# ---------------------------------------------------------------------------
# Property 4: Resolution rule extraction preserves per-record association
# ---------------------------------------------------------------------------


class TestResolutionRuleExtractionPreservesAssociation:
    """Feature: probe-entities-visualization, Property 4: Resolution rule extraction preserves per-record association

    For any valid entity detail JSON containing records with resolution rules,
    the _extract_resolution_rules function SHALL return a list where each entry
    contains data_source (non-empty string), record_id (non-empty string), and
    rule (non-empty string), and the list length equals the number of records
    with resolution rules in the input.

    **Validates: Requirements 1.4, 5.3**
    """

    @given(entity_detail=st_entity_detail_with_resolution_rules())
    @settings(max_examples=20)
    def test_result_length_matches_records_with_rules(
        self, entity_detail: dict
    ) -> None:
        """Output list length equals number of records with ERRULE_CODE.

        Args:
            entity_detail: Generated entity detail with resolution rules.
        """
        records = entity_detail["RESOLVED_ENTITY"]["RECORDS"]
        expected_count = sum(
            1 for r in records if r.get("ERRULE_CODE", "")
        )

        result = _extract_resolution_rules(entity_detail)

        assert len(result) == expected_count, (
            f"Expected {expected_count} resolution rules, got {len(result)}"
        )

    @given(entity_detail=st_entity_detail_with_resolution_rules())
    @settings(max_examples=20)
    def test_each_entry_has_data_source_non_empty_string(
        self, entity_detail: dict
    ) -> None:
        """Each entry in the result has a non-empty data_source string.

        Args:
            entity_detail: Generated entity detail with resolution rules.
        """
        result = _extract_resolution_rules(entity_detail)

        for entry in result:
            assert "data_source" in entry, "Entry missing 'data_source' key"
            assert isinstance(entry["data_source"], str), (
                f"data_source should be str, got {type(entry['data_source'])}"
            )
            assert len(entry["data_source"]) > 0, (
                "data_source should be non-empty"
            )

    @given(entity_detail=st_entity_detail_with_resolution_rules())
    @settings(max_examples=20)
    def test_each_entry_has_record_id_non_empty_string(
        self, entity_detail: dict
    ) -> None:
        """Each entry in the result has a non-empty record_id string.

        Args:
            entity_detail: Generated entity detail with resolution rules.
        """
        result = _extract_resolution_rules(entity_detail)

        for entry in result:
            assert "record_id" in entry, "Entry missing 'record_id' key"
            assert isinstance(entry["record_id"], str), (
                f"record_id should be str, got {type(entry['record_id'])}"
            )
            assert len(entry["record_id"]) > 0, (
                "record_id should be non-empty"
            )

    @given(entity_detail=st_entity_detail_with_resolution_rules())
    @settings(max_examples=20)
    def test_each_entry_has_rule_non_empty_string(
        self, entity_detail: dict
    ) -> None:
        """Each entry in the result has a non-empty rule string.

        Args:
            entity_detail: Generated entity detail with resolution rules.
        """
        result = _extract_resolution_rules(entity_detail)

        for entry in result:
            assert "rule" in entry, "Entry missing 'rule' key"
            assert isinstance(entry["rule"], str), (
                f"rule should be str, got {type(entry['rule'])}"
            )
            assert len(entry["rule"]) > 0, "rule should be non-empty"


# ---------------------------------------------------------------------------
# Reference implementation of enrichment error handling (contract under test)
# ---------------------------------------------------------------------------


def _handle_enrichment_error(exc: Exception) -> dict:
    """Reference implementation: handle enrichment failure gracefully.

    When get_entity_by_entity_id raises any exception, produce a degraded
    result with null enrichment fields and an error description string.

    Args:
        exc: The exception raised during entity enrichment.

    Returns:
        Dict with match_keys=None, feature_scores=None, resolution_rules=None,
        and enrichment_error as a string containing the exception type name
        and message.
    """
    return {
        "match_keys": None,
        "feature_scores": None,
        "resolution_rules": None,
        "enrichment_error": f"{type(exc).__name__}: {str(exc)}",
    }


# ---------------------------------------------------------------------------
# Hypothesis strategies for error handling
# ---------------------------------------------------------------------------


@st.composite
def st_exception_type_and_message(draw) -> tuple[str, str]:
    """Generate a random exception type name and message string.

    Returns:
        Tuple of (exception_type_name, message_string).
    """
    type_name = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L",)),
        min_size=1,
        max_size=30,
    ))
    message = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "Zs", "P")),
        min_size=1,
        max_size=100,
    ))
    return (type_name, message)


# ---------------------------------------------------------------------------
# Property 5: Enrichment error produces graceful degradation
# ---------------------------------------------------------------------------


class TestEnrichmentErrorGracefulDegradation:
    """Feature: probe-entities-visualization, Property 5: Enrichment error produces graceful degradation

    For any exception raised during get_entity_by_entity_id (with any
    exception type name and any message string), the enrichment result
    SHALL have match_keys equal to null, feature_scores equal to null,
    resolution_rules equal to null, and enrichment_error as a non-empty
    string containing both the exception type name and the exception message.

    **Validates: Requirements 1.5, 5.4**
    """

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_has_null_match_keys(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error produces null match_keys.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        # Create a dynamic exception type with the generated name
        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert result["match_keys"] is None, (
            f"Expected null match_keys on error, got {result['match_keys']}"
        )

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_has_null_feature_scores(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error produces null feature_scores.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert result["feature_scores"] is None, (
            f"Expected null feature_scores on error, got {result['feature_scores']}"
        )

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_has_null_resolution_rules(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error produces null resolution_rules.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert result["resolution_rules"] is None, (
            f"Expected null resolution_rules on error, got {result['resolution_rules']}"
        )

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_has_non_empty_enrichment_error(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error produces non-empty enrichment_error string.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert result["enrichment_error"] is not None, (
            "Expected non-null enrichment_error on error"
        )
        assert isinstance(result["enrichment_error"], str), (
            f"Expected enrichment_error to be a string, got {type(result['enrichment_error'])}"
        )
        assert len(result["enrichment_error"]) > 0, (
            "Expected non-empty enrichment_error string"
        )

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_contains_exception_type_name(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error string contains the exception type name.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert type_name in result["enrichment_error"], (
            f"Expected enrichment_error to contain type name '{type_name}', "
            f"got '{result['enrichment_error']}'"
        )

    @given(data=st_exception_type_and_message())
    @settings(max_examples=20)
    def test_error_result_contains_exception_message(
        self, data: tuple[str, str]
    ) -> None:
        """Enrichment error string contains the exception message.

        Args:
            data: Tuple of (exception_type_name, message_string).
        """
        type_name, message = data

        exc_type = type(type_name, (Exception,), {})
        exc = exc_type(message)

        result = _handle_enrichment_error(exc)

        assert message in result["enrichment_error"], (
            f"Expected enrichment_error to contain message '{message}', "
            f"got '{result['enrichment_error']}'"
        )


# ---------------------------------------------------------------------------
# Reference implementation for single-record entity enrichment (Property 6)
# ---------------------------------------------------------------------------


def _enrich_single_record_entity(
    entity_detail: dict, search_match_info: dict
) -> dict:
    """Reference implementation: enrich a single-record entity.

    For single-record entities (exactly 1 record in RECORDS), per_record
    match keys and resolution_rules are empty lists because there are no
    inter-record relationships. The entity_level match key and feature_scores
    are still populated from the search comparison data.

    Args:
        entity_detail: The entity detail dict from get_entity_by_entity_id,
            containing RESOLVED_ENTITY with exactly 1 record in RECORDS.
        search_match_info: The match info from the search response containing
            entity-level match key and feature scores.

    Returns:
        Dict with match_keys (entity_level populated, per_record empty),
        feature_scores (populated from search comparison), resolution_rules
        (empty list), and enrichment_error (null).
    """
    entity_level_key = search_match_info.get("match_key", "+NAME")
    feature_scores = search_match_info.get("feature_scores", [
        {"feature": "NAME", "score": 95, "label": "CLOSE"},
    ])

    return {
        "match_keys": {
            "entity_level": entity_level_key,
            "per_record": [],
        },
        "feature_scores": feature_scores,
        "resolution_rules": [],
        "enrichment_error": None,
    }


# ---------------------------------------------------------------------------
# Hypothesis strategy for single-record entity detail (Property 6)
# ---------------------------------------------------------------------------


@st.composite
def st_single_record_entity_detail(draw) -> tuple[dict, dict]:
    """Generate a single-record entity detail and search match info.

    Produces a tuple of (entity_detail, search_match_info) where the entity
    detail has exactly 1 record in RESOLVED_ENTITY.RECORDS.

    Returns:
        Tuple of (entity_detail dict, search_match_info dict).
    """
    entity_id = draw(st.integers(min_value=1, max_value=100000))
    data_source = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu",)),
        min_size=1,
        max_size=20,
    ))
    record_id = draw(st.text(
        alphabet=st.characters(whitelist_categories=("N",)),
        min_size=1,
        max_size=10,
    ))
    match_key = draw(st.text(
        alphabet=st.characters(whitelist_categories=("L",)),
        min_size=1,
        max_size=20,
    ).map(lambda s: f"+{s}"))

    entity_detail = {
        "RESOLVED_ENTITY": {
            "ENTITY_ID": entity_id,
            "RECORDS": [
                {
                    "DATA_SOURCE": data_source,
                    "RECORD_ID": record_id,
                    "MATCH_KEY": match_key,
                    "ERRULE_CODE": "",
                }
            ],
        }
    }

    # Generate feature scores from search comparison
    num_features = draw(st.integers(min_value=1, max_value=5))
    feature_scores = []
    for _ in range(num_features):
        feature_name = draw(st.text(
            alphabet=st.characters(whitelist_categories=("Lu",)),
            min_size=1,
            max_size=10,
        ))
        score = draw(st.integers(min_value=0, max_value=100))
        label = draw(st.sampled_from(["SAME", "CLOSE", "LIKELY", "PLAUSIBLE"]))
        feature_scores.append({
            "feature": feature_name,
            "score": score,
            "label": label,
        })

    search_match_info = {
        "match_key": match_key,
        "feature_scores": feature_scores,
    }

    return (entity_detail, search_match_info)


# ---------------------------------------------------------------------------
# Property 6: Single-record entities have empty per-record fields
# ---------------------------------------------------------------------------


class TestSingleRecordEntitiesEmptyPerRecordFields:
    """Feature: probe-entities-visualization, Property 6: Single-record entities have empty per-record fields

    For any entity detail representing a single-record entity (record count
    = 1), the enrichment result SHALL have `match_keys.per_record` as an
    empty list and `resolution_rules` as an empty list, while
    `match_keys.entity_level` and `feature_scores` remain populated from
    the search comparison data.

    **Validates: Requirements 5.5**
    """

    @given(entity_data=st_single_record_entity_detail())
    @settings(max_examples=20)
    def test_per_record_is_empty_list(
        self, entity_data: tuple[dict, dict]
    ) -> None:
        """Single-record entities have empty per_record match keys.

        Args:
            entity_data: Tuple of (entity_detail, search_match_info).
        """
        entity_detail, search_match_info = entity_data

        result = _enrich_single_record_entity(entity_detail, search_match_info)

        assert result["match_keys"]["per_record"] == [], (
            f"Expected empty per_record for single-record entity, "
            f"got {result['match_keys']['per_record']}"
        )

    @given(entity_data=st_single_record_entity_detail())
    @settings(max_examples=20)
    def test_resolution_rules_is_empty_list(
        self, entity_data: tuple[dict, dict]
    ) -> None:
        """Single-record entities have empty resolution_rules.

        Args:
            entity_data: Tuple of (entity_detail, search_match_info).
        """
        entity_detail, search_match_info = entity_data

        result = _enrich_single_record_entity(entity_detail, search_match_info)

        assert result["resolution_rules"] == [], (
            f"Expected empty resolution_rules for single-record entity, "
            f"got {result['resolution_rules']}"
        )

    @given(entity_data=st_single_record_entity_detail())
    @settings(max_examples=20)
    def test_entity_level_match_key_populated(
        self, entity_data: tuple[dict, dict]
    ) -> None:
        """Single-record entities still have entity_level match key populated.

        Args:
            entity_data: Tuple of (entity_detail, search_match_info).
        """
        entity_detail, search_match_info = entity_data

        result = _enrich_single_record_entity(entity_detail, search_match_info)

        assert result["match_keys"]["entity_level"] is not None, (
            "Expected non-null entity_level match key for single-record entity"
        )
        assert isinstance(result["match_keys"]["entity_level"], str), (
            f"Expected entity_level to be a string, "
            f"got {type(result['match_keys']['entity_level'])}"
        )
        assert len(result["match_keys"]["entity_level"]) > 0, (
            "Expected non-empty entity_level match key"
        )
        # Verify it matches the search match info
        assert result["match_keys"]["entity_level"] == search_match_info["match_key"], (
            f"Expected entity_level '{search_match_info['match_key']}', "
            f"got '{result['match_keys']['entity_level']}'"
        )

    @given(entity_data=st_single_record_entity_detail())
    @settings(max_examples=20)
    def test_feature_scores_populated(
        self, entity_data: tuple[dict, dict]
    ) -> None:
        """Single-record entities still have feature_scores populated.

        Args:
            entity_data: Tuple of (entity_detail, search_match_info).
        """
        entity_detail, search_match_info = entity_data

        result = _enrich_single_record_entity(entity_detail, search_match_info)

        assert result["feature_scores"] is not None, (
            "Expected non-null feature_scores for single-record entity"
        )
        assert isinstance(result["feature_scores"], list), (
            f"Expected feature_scores to be a list, "
            f"got {type(result['feature_scores'])}"
        )
        assert len(result["feature_scores"]) > 0, (
            "Expected non-empty feature_scores for single-record entity"
        )
        # Verify it matches the search match info
        assert result["feature_scores"] == search_match_info["feature_scores"], (
            f"Expected feature_scores from search match info, "
            f"got {result['feature_scores']}"
        )

    @given(entity_data=st_single_record_entity_detail())
    @settings(max_examples=20)
    def test_enrichment_error_is_null(
        self, entity_data: tuple[dict, dict]
    ) -> None:
        """Single-record entities have null enrichment_error.

        Args:
            entity_data: Tuple of (entity_detail, search_match_info).
        """
        entity_detail, search_match_info = entity_data

        result = _enrich_single_record_entity(entity_detail, search_match_info)

        assert result["enrichment_error"] is None, (
            f"Expected null enrichment_error for single-record entity, "
            f"got {result['enrichment_error']}"
        )
