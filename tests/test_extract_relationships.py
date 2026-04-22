"""Unit tests for extract_relationships."""

from __future__ import annotations

import json
import logging

import pytest

from src.query.generate_visualization import (
    RelationshipEdge,
    extract_relationships,
)


# ---------------------------------------------------------------------------
# Helpers — mock Senzing engine
# ---------------------------------------------------------------------------

def _make_entity_response(
    entity_id: int,
    related: list[dict] | None = None,
) -> str:
    """Build a Senzing-style entity JSON with RELATED_ENTITIES."""
    return json.dumps({
        "RESOLVED_ENTITY": {
            "ENTITY_ID": entity_id,
            "ENTITY_NAME": f"Entity {entity_id}",
            "RECORDS": [],
        },
        "RELATED_ENTITIES": related or [],
    })


class MockEntityEngine:
    """Mock engine exposing get_entity_by_entity_id."""

    def __init__(
        self,
        responses: dict[int, str],
        errors: dict[int, Exception] | None = None,
    ):
        self._responses = responses
        self._errors = errors or {}

    def get_entity_by_entity_id(self, entity_id: int) -> str:
        if entity_id in self._errors:
            raise self._errors[entity_id]
        return self._responses[entity_id]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExtractRelationships:
    def test_basic_relationship(self):
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 2,
                    "MATCH_LEVEL": 1,
                    "MATCH_KEY": "+NAME+ADDRESS",
                    "IS_DISCLOSED": 0,
                },
            ]),
            2: _make_entity_response(2, [
                {
                    "ENTITY_ID": 1,
                    "MATCH_LEVEL": 1,
                    "MATCH_KEY": "+NAME+ADDRESS",
                    "IS_DISCLOSED": 0,
                },
            ]),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1, 2])

        assert len(edges) == 1
        edge = edges[0]
        assert edge.source_entity_id == 1
        assert edge.target_entity_id == 2
        assert edge.match_level == 1
        assert edge.match_strength == "strong"
        assert edge.shared_features == ["NAME", "ADDRESS"]

    def test_deduplication(self):
        """A->B and B->A should produce only one edge."""
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 2,
                    "MATCH_LEVEL": 2,
                    "MATCH_KEY": "+NAME",
                },
            ]),
            2: _make_entity_response(2, [
                {
                    "ENTITY_ID": 1,
                    "MATCH_LEVEL": 2,
                    "MATCH_KEY": "+NAME",
                },
            ]),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1, 2])
        assert len(edges) == 1

    def test_filters_out_external_entities(self):
        """Relationships to entities not in entity_ids are excluded."""
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 99,
                    "MATCH_LEVEL": 1,
                    "MATCH_KEY": "+NAME",
                },
            ]),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1])
        assert len(edges) == 0

    def test_sdk_error_skips_entity(self, caplog):
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 2,
                    "MATCH_LEVEL": 1,
                    "MATCH_KEY": "+NAME",
                },
            ]),
        }
        errors = {2: RuntimeError("SDK failure")}
        engine = MockEntityEngine(responses, errors)

        with caplog.at_level(logging.WARNING):
            edges = extract_relationships(engine, [1, 2])

        # Entity 1's relationship to 2 is still captured
        assert len(edges) == 1
        assert "Failed to retrieve relationships" in caplog.text

    def test_match_strength_moderate(self):
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 2,
                    "MATCH_LEVEL": 2,
                    "MATCH_KEY": "+PHONE",
                },
            ]),
            2: _make_entity_response(2, []),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1, 2])

        assert len(edges) == 1
        assert edges[0].match_strength == "moderate"

    def test_match_strength_weak(self):
        responses = {
            1: _make_entity_response(1, [
                {
                    "ENTITY_ID": 2,
                    "MATCH_LEVEL": 3,
                    "MATCH_KEY": "+DOB",
                },
            ]),
            2: _make_entity_response(2, []),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1, 2])

        assert len(edges) == 1
        assert edges[0].match_strength == "weak"

    def test_empty_entity_ids(self):
        engine = MockEntityEngine({})
        edges = extract_relationships(engine, [])
        assert edges == []

    def test_no_related_entities(self):
        responses = {
            1: _make_entity_response(1, []),
            2: _make_entity_response(2, []),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [1, 2])
        assert edges == []

    def test_canonical_ordering(self):
        """Source should always be the smaller entity ID."""
        responses = {
            5: _make_entity_response(5, [
                {
                    "ENTITY_ID": 3,
                    "MATCH_LEVEL": 1,
                    "MATCH_KEY": "+NAME",
                },
            ]),
            3: _make_entity_response(3, []),
        }
        engine = MockEntityEngine(responses)
        edges = extract_relationships(engine, [5, 3])

        assert len(edges) == 1
        assert edges[0].source_entity_id == 3
        assert edges[0].target_entity_id == 5

    def test_invalid_json_skips(self, caplog):
        """Invalid JSON from SDK should be logged and skipped."""

        class BadJsonEngine:
            def get_entity_by_entity_id(self, eid):
                return "not valid json"

        with caplog.at_level(logging.WARNING):
            edges = extract_relationships(BadJsonEngine(), [1])

        assert edges == []
        assert "Invalid JSON" in caplog.text
