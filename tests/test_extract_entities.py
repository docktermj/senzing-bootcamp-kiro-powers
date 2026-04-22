"""Unit tests for extract_entities and _parse_entity_response."""

from __future__ import annotations

import json
import logging

import pytest

from src.query.generate_visualization import (
    EntityNode,
    Record,
    _parse_entity_response,
    extract_entities,
)


# ---------------------------------------------------------------------------
# Helpers — mock Senzing engine
# ---------------------------------------------------------------------------

def _make_sdk_response(
    entity_id: int,
    entity_name: str,
    records: list[dict],
    features: dict | None = None,
) -> str:
    """Build a Senzing-style JSON response string."""
    return json.dumps({
        "RESOLVED_ENTITY": {
            "ENTITY_ID": entity_id,
            "ENTITY_NAME": entity_name,
            "RECORDS": records,
            "FEATURES": features or {},
        }
    })


class MockEngine:
    """Minimal mock of a Senzing engine for testing extract_entities."""

    def __init__(self, responses: dict[str, str], errors: dict[str, Exception] | None = None):
        self._responses = responses  # record_id -> JSON string
        self._errors = errors or {}

    def get_entity_by_record_id(self, data_source: str, record_id: str) -> str:
        if record_id in self._errors:
            raise self._errors[record_id]
        return self._responses[record_id]


# ---------------------------------------------------------------------------
# _parse_entity_response tests
# ---------------------------------------------------------------------------

class TestParseEntityResponse:
    def test_basic_entity(self):
        resp = _make_sdk_response(
            entity_id=1,
            entity_name="John Smith",
            records=[
                {"DATA_SOURCE": "CUSTOMERS", "RECORD_ID": "CUST-001"},
                {"DATA_SOURCE": "CRM", "RECORD_ID": "CRM-042"},
            ],
            features={
                "NAME": [{"FEAT_DESC": "John Smith"}, {"FEAT_DESC": "J. Smith"}],
                "ADDRESS": [{"FEAT_DESC": "123 Main St"}],
            },
        )
        node = _parse_entity_response(resp)

        assert node.entity_id == 1
        assert node.primary_name == "John Smith"
        assert node.record_count == 2
        assert sorted(node.data_sources) == ["CRM", "CUSTOMERS"]
        assert node.primary_data_source == "CUSTOMERS"
        assert len(node.records) == 2
        assert node.features["NAME"] == ["John Smith", "J. Smith"]
        assert node.features["ADDRESS"] == ["123 Main St"]

    def test_single_record(self):
        resp = _make_sdk_response(
            entity_id=42,
            entity_name="Jane Doe",
            records=[{"DATA_SOURCE": "SRC", "RECORD_ID": "R1"}],
        )
        node = _parse_entity_response(resp)

        assert node.entity_id == 42
        assert node.record_count == 1
        assert node.data_sources == ["SRC"]
        assert node.primary_data_source == "SRC"

    def test_empty_features(self):
        resp = _make_sdk_response(
            entity_id=10,
            entity_name="No Features",
            records=[{"DATA_SOURCE": "A", "RECORD_ID": "1"}],
        )
        node = _parse_entity_response(resp)
        assert node.features == {}

    def test_primary_data_source_most_records(self):
        resp = _make_sdk_response(
            entity_id=5,
            entity_name="Multi",
            records=[
                {"DATA_SOURCE": "A", "RECORD_ID": "1"},
                {"DATA_SOURCE": "B", "RECORD_ID": "2"},
                {"DATA_SOURCE": "B", "RECORD_ID": "3"},
            ],
        )
        node = _parse_entity_response(resp)
        assert node.primary_data_source == "B"


# ---------------------------------------------------------------------------
# extract_entities tests
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_basic_extraction(self):
        responses = {
            "R1": _make_sdk_response(1, "Alice", [
                {"DATA_SOURCE": "DS", "RECORD_ID": "R1"},
            ]),
            "R2": _make_sdk_response(2, "Bob", [
                {"DATA_SOURCE": "DS", "RECORD_ID": "R2"},
            ]),
        }
        engine = MockEngine(responses)
        entities = extract_entities(engine, "DS", limit=None, record_ids=["R1", "R2"])

        assert len(entities) == 2
        assert entities[0].entity_id == 1
        assert entities[1].entity_id == 2

    def test_deduplication(self):
        """Two records resolving to the same entity should produce one EntityNode."""
        shared_resp = _make_sdk_response(1, "Alice", [
            {"DATA_SOURCE": "DS", "RECORD_ID": "R1"},
            {"DATA_SOURCE": "DS", "RECORD_ID": "R2"},
        ])
        responses = {"R1": shared_resp, "R2": shared_resp}
        engine = MockEngine(responses)
        entities = extract_entities(engine, "DS", limit=None, record_ids=["R1", "R2"])

        assert len(entities) == 1
        assert entities[0].entity_id == 1

    def test_limit_enforcement(self):
        responses = {
            f"R{i}": _make_sdk_response(i, f"Entity{i}", [
                {"DATA_SOURCE": "DS", "RECORD_ID": f"R{i}"},
            ])
            for i in range(10)
        }
        engine = MockEngine(responses)
        entities = extract_entities(
            engine, "DS", limit=3, record_ids=[f"R{i}" for i in range(10)]
        )
        assert len(entities) == 3

    def test_error_handling_skips_bad_records(self, caplog):
        responses = {
            "R1": _make_sdk_response(1, "Good", [
                {"DATA_SOURCE": "DS", "RECORD_ID": "R1"},
            ]),
        }
        errors = {"R2": RuntimeError("SDK failure")}
        engine = MockEngine(responses, errors)

        with caplog.at_level(logging.WARNING):
            entities = extract_entities(
                engine, "DS", limit=None, record_ids=["R1", "R2"]
            )

        assert len(entities) == 1
        assert entities[0].primary_name == "Good"
        assert "Failed to retrieve entity for record R2" in caplog.text

    def test_large_count_warning(self, caplog):
        responses = {
            f"R{i}": _make_sdk_response(i, f"E{i}", [
                {"DATA_SOURCE": "DS", "RECORD_ID": f"R{i}"},
            ])
            for i in range(501)
        }
        engine = MockEngine(responses)

        with caplog.at_level(logging.WARNING):
            entities = extract_entities(
                engine, "DS", limit=None, record_ids=[f"R{i}" for i in range(501)]
            )

        assert len(entities) == 501
        assert "501 entities found" in caplog.text
        assert "Rendering may be slow" in caplog.text

    def test_empty_record_ids(self):
        engine = MockEngine({})
        entities = extract_entities(engine, "DS", limit=None, record_ids=[])
        assert entities == []
