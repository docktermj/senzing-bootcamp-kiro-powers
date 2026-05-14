"""Statistics builder for the entity resolution visualization web service.

Computes aggregate statistics from Senzing SDK entity export data, including
record/entity counts, cross-source metrics, and histogram bucketing.

Usage:
    # With live SDK engine (server use case):
    result = build(engine)

    # With pre-parsed entity data (testing/offline):
    stats = Stats.from_entities(entities)
    summary = format_summary(stats)
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class Stats:
    """Aggregate entity resolution statistics.

    Attributes:
        records_total: Total number of source records across all entities.
        entities_total: Total number of resolved entities.
        multi_record_entities: Count of entities with 2+ constituent records.
        cross_source_entities: Count of entities with records from 2+ data sources.
        relationships_total: Total number of inter-entity relationships.
        histogram: Distribution of entities by record count bucket.
    """

    records_total: int
    entities_total: int
    multi_record_entities: int
    cross_source_entities: int
    relationships_total: int
    histogram: dict[str, int]

    @classmethod
    def from_entities(cls, entities: list[dict]) -> Stats:
        """Create Stats from a list of entity dictionaries.

        Args:
            entities: List of entity dicts, each containing entity_id,
                entity_name, record_count, data_sources, and records.

        Returns:
            A Stats instance with computed aggregate values.
        """
        records_total = sum(e["record_count"] for e in entities)
        entities_total = len(entities)
        multi_record_entities = sum(
            1 for e in entities if e["record_count"] >= 2
        )
        cross_source_entities = sum(
            1 for e in entities if len(e["data_sources"]) >= 2
        )
        histogram = compute_histogram(entities)

        return cls(
            records_total=records_total,
            entities_total=entities_total,
            multi_record_entities=multi_record_entities,
            cross_source_entities=cross_source_entities,
            relationships_total=0,
            histogram=histogram,
        )

    def to_dict(self) -> dict:
        """Convert Stats to a JSON-serializable dictionary.

        Returns:
            Dictionary containing all stats fields.
        """
        return {
            "records_total": self.records_total,
            "entities_total": self.entities_total,
            "multi_record_entities": self.multi_record_entities,
            "cross_source_entities": self.cross_source_entities,
            "relationships_total": self.relationships_total,
            "histogram": self.histogram,
        }


def compute_histogram(entities: list[dict]) -> dict[str, int]:
    """Bucket entities by record count into 1, 2, 3, 4+ categories.

    Args:
        entities: List of entity dicts, each with a record_count field.

    Returns:
        Dictionary with keys "1", "2", "3", "4+" mapping to entity counts.
    """
    histogram: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4+": 0}

    for entity in entities:
        rc = entity["record_count"]
        if rc == 1:
            histogram["1"] += 1
        elif rc == 2:
            histogram["2"] += 1
        elif rc == 3:
            histogram["3"] += 1
        else:
            histogram["4+"] += 1

    return histogram


def format_summary(stats: Stats) -> str:
    """Produce a human-readable summary of entity resolution results.

    Args:
        stats: A Stats instance with computed values.

    Returns:
        Formatted string: "[X] records collapsed into [Y] entities,
        including [Z] multi-record entities"
    """
    return (
        f"{stats.records_total} records collapsed into "
        f"{stats.entities_total} entities, including "
        f"{stats.multi_record_entities} multi-record entities"
    )


def build(engine: object) -> dict:
    """Compute stats from a live Senzing engine instance.

    Calls engine.export_json_entity_report() to retrieve entity data,
    parses the JSON entities, creates Stats, and returns the dict.

    Args:
        engine: A Senzing engine instance with export_json_entity_report method.

    Returns:
        Dictionary of stats on success, or {"error": str} on failure.
    """
    try:
        export_handle = engine.export_json_entity_report()
        entities: list[dict] = []

        while True:
            record = engine.fetch_next(export_handle)
            if not record:
                break
            entity = json.loads(record)
            # Normalize entity structure for stats computation
            resolved = entity.get("RESOLVED_ENTITY", entity)
            records_list = resolved.get("RECORDS", [])
            data_sources = list({r.get("DATA_SOURCE", "") for r in records_list})
            entities.append({
                "entity_id": resolved.get("ENTITY_ID", 0),
                "entity_name": resolved.get("ENTITY_NAME", ""),
                "record_count": len(records_list),
                "data_sources": data_sources,
                "records": records_list,
            })

        engine.close_export(export_handle)
        stats = Stats.from_entities(entities)
        return stats.to_dict()
    except Exception as e:
        return {"error": str(e)}
