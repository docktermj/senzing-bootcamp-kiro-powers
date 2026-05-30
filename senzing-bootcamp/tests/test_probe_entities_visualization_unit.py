"""Unit tests for Probe Entities visualization steering file content.

Validates that the steering file contains enrichment specifications for
match keys, feature scores, resolution rules, get_entity_by_entity_id call,
and the enriched /api/search response schema.

Feature: probe-entities-visualization
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_STEERING_FILE: Path = _BASE_DIR / "steering" / "module-03-phase2-visualization.md"

# ---------------------------------------------------------------------------
# Module-level file content (read once at import time)
# ---------------------------------------------------------------------------

_CONTENT: str = _STEERING_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestProbeEntitiesEnrichmentSpecifications:
    """Unit tests verifying steering file contains enrichment specifications.

    Validates Requirements 6.1, 6.2, 6.3.
    """

    def test_match_keys_field_specification(self) -> None:
        """Assert the steering file specifies the match_keys field.

        The enriched /api/search response must include match_keys with
        entity-level and per-record match key strings.

        Validates: Requirements 6.1, 6.3
        """
        assert "match_keys" in _CONTENT, (
            "Steering file must contain 'match_keys' field specification "
            "for the enriched /api/search response"
        )
        # Verify both entity_level and per_record sub-fields are specified
        assert "entity_level" in _CONTENT, (
            "Steering file must specify 'entity_level' sub-field within match_keys"
        )
        assert "per_record" in _CONTENT, (
            "Steering file must specify 'per_record' sub-field within match_keys"
        )

    def test_feature_scores_field_specification(self) -> None:
        """Assert the steering file specifies the feature_scores field.

        The enriched response must include feature_scores with feature name,
        numeric score, and classification label.

        Validates: Requirements 6.1, 6.3
        """
        assert "feature_scores" in _CONTENT, (
            "Steering file must contain 'feature_scores' field specification "
            "for the enriched /api/search response"
        )
        # Verify the feature score structure is documented (feature, score, label)
        assert "feature" in _CONTENT, (
            "Steering file must specify 'feature' field within feature_scores entries"
        )
        assert "score" in _CONTENT, (
            "Steering file must specify 'score' field within feature_scores entries"
        )
        assert "label" in _CONTENT, (
            "Steering file must specify 'label' field within feature_scores entries"
        )

    def test_resolution_rules_field_specification(self) -> None:
        """Assert the steering file specifies the resolution_rules field.

        The enriched response must include resolution_rules with data_source,
        record_id, and rule for each constituent record.

        Validates: Requirements 6.1, 6.3
        """
        assert "resolution_rules" in _CONTENT, (
            "Steering file must contain 'resolution_rules' field specification "
            "for the enriched /api/search response"
        )
        # Verify per-record structure fields are specified
        assert "data_source" in _CONTENT, (
            "Steering file must specify 'data_source' field within resolution_rules entries"
        )
        assert "record_id" in _CONTENT, (
            "Steering file must specify 'record_id' field within resolution_rules entries"
        )
        assert "rule" in _CONTENT, (
            "Steering file must specify 'rule' field within resolution_rules entries"
        )

    def test_get_entity_by_entity_id_call_specified(self) -> None:
        """Assert the steering file specifies the get_entity_by_entity_id SDK call.

        The search_builder.py specification must indicate that
        get_entity_by_entity_id is called after search_by_attributes
        to retrieve full resolution detail.

        Validates: Requirements 6.2
        """
        assert "get_entity_by_entity_id" in _CONTENT, (
            "Steering file must specify 'get_entity_by_entity_id' call "
            "for entity enrichment in search_builder.py"
        )
        # Verify it's in context with search_by_attributes (enrichment flow)
        assert "search_by_attributes" in _CONTENT, (
            "Steering file must specify 'search_by_attributes' as the initial "
            "search call before enrichment"
        )

    def test_enriched_api_search_response_schema(self) -> None:
        """Assert the steering file specifies the enriched /api/search response schema.

        The steering file must document the /api/search endpoint with the
        enrichment fields (match_keys, feature_scores, resolution_rules,
        enrichment_error) as part of the response schema.

        Validates: Requirements 6.3
        """
        assert "/api/search" in _CONTENT, (
            "Steering file must contain '/api/search' endpoint specification"
        )
        # Verify enrichment_error field is documented (graceful degradation)
        assert "enrichment_error" in _CONTENT, (
            "Steering file must specify 'enrichment_error' field for graceful "
            "degradation when get_entity_by_entity_id fails"
        )
        # Verify the response includes the enrichment fields together
        # Find the /api/search section and verify all enrichment fields appear
        search_pos = _CONTENT.find("/api/search")
        assert search_pos != -1
        content_after_search = _CONTENT[search_pos:]
        assert "match_keys" in content_after_search, (
            "The /api/search section must include 'match_keys' in the response schema"
        )
        assert "feature_scores" in content_after_search, (
            "The /api/search section must include 'feature_scores' in the response schema"
        )
        assert "resolution_rules" in content_after_search, (
            "The /api/search section must include 'resolution_rules' in the response schema"
        )


class TestProbeEntitiesFrontendRenderingSpecifications:
    """Unit tests verifying steering file specifies frontend rendering formats.

    Validates Requirements 2.3, 2.4, 2.5, 3.2, 4.3.
    """

    def test_match_key_inline_chip_elements(self) -> None:
        """Assert steering file specifies inline <span> elements with visible boundary for match keys.

        Each feature indicator (+NAME, +DOB) must be rendered as a separate
        inline <span> element with a visible border/background distinguishing
        it from adjacent indicators and surrounding text.

        Validates: Requirement 2.4
        """
        assert "<span>" in _CONTENT or "span" in _CONTENT, (
            "Steering file must specify <span> elements for match key feature indicators"
        )
        # Verify visible boundary specification (border and/or background)
        has_border = "border" in _CONTENT.lower()
        has_background = "background" in _CONTENT.lower()
        assert has_border or has_background, (
            "Steering file must specify visible border or background color "
            "for match key chip elements"
        )
        # Verify inline rendering specification
        assert "inline" in _CONTENT.lower(), (
            "Steering file must specify inline rendering for match key chip elements"
        )

    def test_feature_scores_structured_format(self) -> None:
        """Assert steering file specifies structured format for feature scores.

        Feature scores must show feature name, numeric percentage, and
        classification label (e.g., NAME: 97% CLOSE).

        Validates: Requirement 3.2
        """
        # Verify the structured format example is present
        assert "%" in _CONTENT, (
            "Steering file must specify percentage format for feature scores"
        )
        # Verify the feature score display includes name, percentage, and label
        content_lower = _CONTENT.lower()
        assert "feature name" in content_lower or "feature score" in content_lower, (
            "Steering file must specify feature name in feature score display"
        )
        assert "percentage" in content_lower or "%" in _CONTENT, (
            "Steering file must specify numeric percentage in feature score display"
        )
        assert "label" in content_lower, (
            "Steering file must specify classification label in feature score display"
        )
        # Verify structured list format
        assert "structured" in content_lower, (
            "Steering file must specify structured format for feature scores display"
        )

    def test_resolution_rules_monospace_format(self) -> None:
        """Assert steering file specifies monospace/code-style format for resolution rules.

        Resolution rules must be displayed in monospace or code-style format
        to distinguish them from natural language text.

        Validates: Requirement 4.3
        """
        content_lower = _CONTENT.lower()
        has_monospace = "monospace" in content_lower
        has_code_style = "code-style" in content_lower
        has_code_element = "<code>" in _CONTENT.lower()
        has_font_family = "font-family: monospace" in content_lower
        assert has_monospace or has_code_style or has_code_element or has_font_family, (
            "Steering file must specify monospace or code-style format for resolution rules "
            "(expected 'monospace', 'code-style', '<code>', or 'font-family: monospace')"
        )

    def test_per_record_match_key_omission_single_record(self) -> None:
        """Assert steering file specifies per-record match key omission for single-record entities.

        When a resolved entity contains only one record, the per-record
        match key section must be omitted for that entity.

        Validates: Requirement 2.3
        """
        content_lower = _CONTENT.lower()
        has_single_record = "single record" in content_lower or "one record" in content_lower
        has_omit = "omit" in content_lower
        assert has_single_record, (
            "Steering file must reference single-record entities for conditional display"
        )
        assert has_omit, (
            "Steering file must specify omission of per-record match keys "
            "for single-record entities"
        )

    def test_placeholder_for_missing_match_key_data(self) -> None:
        """Assert steering file specifies a placeholder label for missing match key data.

        When no match key data is available, a placeholder label must be
        displayed indicating that no match key information is available.

        Validates: Requirement 2.5
        """
        assert "no match key" in _CONTENT.lower(), (
            "Steering file must specify a placeholder label for missing match key data "
            "(expected text containing 'No match key')"
        )
        # Verify the specific placeholder text
        assert "No match key information available" in _CONTENT, (
            "Steering file must specify the exact placeholder: "
            "'No match key information available'"
        )
