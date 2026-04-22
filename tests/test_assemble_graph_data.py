"""Tests for assemble_graph_data function."""

from __future__ import annotations

import datetime

from src.query.generate_visualization import (
    EntityNode,
    GraphData,
    Record,
    RelationshipEdge,
    assemble_graph_data,
)


def test_assemble_graph_data_basic() -> None:
    """Metadata fields are computed correctly."""
    entities = [
        EntityNode(
            entity_id=1,
            primary_name="Alice",
            record_count=2,
            data_sources=["CRM", "CUSTOMERS"],
            primary_data_source="CUSTOMERS",
            records=[
                Record("R1", "CUSTOMERS"),
                Record("R2", "CRM"),
            ],
        ),
        EntityNode(
            entity_id=2,
            primary_name="Bob",
            record_count=1,
            data_sources=["CUSTOMERS"],
            primary_data_source="CUSTOMERS",
            records=[Record("R3", "CUSTOMERS")],
        ),
    ]
    relationships = [
        RelationshipEdge(
            source_entity_id=1,
            target_entity_id=2,
            match_level=1,
            match_strength="strong",
            shared_features=["NAME"],
        ),
    ]

    result = assemble_graph_data(
        entities, relationships, "CUSTOMERS",
    )

    assert isinstance(result, GraphData)
    assert result.metadata.data_source == "CUSTOMERS"
    assert result.metadata.entity_count == 2
    assert result.metadata.record_count == 3
    assert result.metadata.relationship_count == 1
    assert result.metadata.data_sources == ["CRM", "CUSTOMERS"]
    assert result.nodes is entities
    assert result.edges is relationships
    # Timestamp should be a valid ISO format string
    datetime.datetime.fromisoformat(result.metadata.generated_at)


def test_assemble_graph_data_empty() -> None:
    """Empty inputs produce zero counts and empty lists."""
    result = assemble_graph_data([], [], "EMPTY_SRC")

    assert result.metadata.data_source == "EMPTY_SRC"
    assert result.metadata.entity_count == 0
    assert result.metadata.record_count == 0
    assert result.metadata.relationship_count == 0
    assert result.metadata.data_sources == []
    assert result.nodes == []
    assert result.edges == []
