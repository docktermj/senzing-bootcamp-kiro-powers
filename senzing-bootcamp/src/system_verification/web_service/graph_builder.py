"""Graph builder for the entity resolution visualization web service.

Constructs graph nodes and edges from Senzing SDK entity/relationship data.

Usage:
    # With live SDK engine (server use case):
    result = build(engine)
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class GraphNode:
    """A node in the entity resolution graph.

    Attributes:
        entity_id: Unique entity identifier.
        entity_name: Display name for the entity.
        record_count: Number of constituent records.
        data_sources: List of data source names contributing records.
        records: List of constituent record summaries.
    """

    entity_id: int
    entity_name: str
    record_count: int
    data_sources: list[str]
    records: list[dict]

    def to_dict(self) -> dict:
        """Convert GraphNode to a JSON-serializable dictionary.

        Returns:
            Dictionary containing all node fields.
        """
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "record_count": self.record_count,
            "data_sources": self.data_sources,
            "records": self.records,
        }


@dataclass
class GraphEdge:
    """An edge in the entity resolution graph.

    Attributes:
        source_entity_id: Entity ID of the source node.
        target_entity_id: Entity ID of the target node.
        match_key: Senzing match key describing the relationship.
        relationship_type: Type of relationship (e.g., possible_match).
    """

    source_entity_id: int
    target_entity_id: int
    match_key: str
    relationship_type: str

    def to_dict(self) -> dict:
        """Convert GraphEdge to a JSON-serializable dictionary.

        Returns:
            Dictionary containing all edge fields.
        """
        return {
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "match_key": self.match_key,
            "relationship_type": self.relationship_type,
        }


def build(engine: object) -> dict:
    """Build graph nodes and edges from a live Senzing engine instance.

    Calls engine.export_json_entity_report() to retrieve all entities and
    engine.find_network_by_entity_id() to discover relationships between them.
    Constructs GraphNode and GraphEdge instances and returns the complete
    graph structure.

    Args:
        engine: A Senzing engine instance with export_json_entity_report,
            fetch_next, close_export, get_entity_by_entity_id, and
            find_network_by_entity_id methods.

    Returns:
        Dictionary with "nodes" and "edges" arrays on success,
        or {"error": str} on failure.
    """
    try:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_edges: set[tuple[int, int]] = set()

        # Export all entities to build nodes
        export_handle = engine.export_json_entity_report()
        entity_ids: list[int] = []

        while True:
            record = engine.fetch_next(export_handle)
            if not record:
                break
            entity = json.loads(record)
            resolved = entity.get("RESOLVED_ENTITY", entity)
            entity_id = resolved.get("ENTITY_ID", 0)
            entity_name = resolved.get("ENTITY_NAME", "")
            records_list = resolved.get("RECORDS", [])
            data_sources = list({r.get("DATA_SOURCE", "") for r in records_list})
            records = [
                {
                    "data_source": r.get("DATA_SOURCE", ""),
                    "record_id": r.get("RECORD_ID", ""),
                }
                for r in records_list
            ]

            nodes.append(GraphNode(
                entity_id=entity_id,
                entity_name=entity_name,
                record_count=len(records_list),
                data_sources=data_sources,
                records=records,
            ))
            entity_ids.append(entity_id)

        engine.close_export(export_handle)

        # Discover relationships between entities using find_network
        for entity_id in entity_ids:
            try:
                network_json = engine.find_network_by_entity_id(
                    [entity_id], max_degrees=1
                )
                network = json.loads(network_json)
                entity_paths = network.get("ENTITY_PATHS", [])
                for path in entity_paths:
                    relationships = path.get("ENTITIES", [])
                    for rel in relationships:
                        source_id = rel.get("ENTITY_ID", 0)
                        target_id = rel.get("RELATED_ENTITY_ID", 0)
                        if source_id == 0 or target_id == 0:
                            continue
                        edge_key = (
                            min(source_id, target_id),
                            max(source_id, target_id),
                        )
                        if edge_key in seen_edges:
                            continue
                        seen_edges.add(edge_key)
                        edges.append(GraphEdge(
                            source_entity_id=source_id,
                            target_entity_id=target_id,
                            match_key=rel.get("MATCH_KEY", ""),
                            relationship_type=rel.get(
                                "MATCH_LEVEL_CODE", "possible_match"
                            ),
                        ))
            except Exception:
                # Skip entities that fail network lookup
                continue

        return {
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
        }
    except Exception as e:
        return {"error": str(e)}
