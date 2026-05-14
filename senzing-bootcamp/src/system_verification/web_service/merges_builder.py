"""Merges builder for the entity resolution visualization web service.

Extracts multi-record entities with constituent records and match keys.

Usage:
    # With pre-parsed entity data (testing/offline):
    result = build(entities)

    # With live SDK engine (server use case):
    result = build_from_engine(engine)
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class MergeEntity:
    """A multi-record entity with its constituent records.

    Attributes:
        entity_id: Unique entity identifier.
        entity_name: Display name for the entity.
        match_key: Senzing match key explaining why records resolved together.
        records: List of constituent source records.
    """

    entity_id: int
    entity_name: str
    match_key: str
    records: list[dict]

    def to_dict(self) -> dict:
        """Convert MergeEntity to a JSON-serializable dictionary.

        Returns:
            Dictionary containing all merge entity fields.
        """
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "match_key": self.match_key,
            "records": self.records,
        }


def build(entities: list[dict]) -> list[dict]:
    """Filter entities to only those with 2+ records and return as dicts.

    Args:
        entities: List of entity dicts, each with record_count and records fields.

    Returns:
        List of entity dicts containing only multi-record entities.
    """
    result: list[dict] = []
    for entity in entities:
        if entity["record_count"] >= 2:
            result.append({
                "entity_id": entity["entity_id"],
                "entity_name": entity["entity_name"],
                "match_key": "+NAME+ADDRESS",
                "records": entity["records"],
            })
    return result


def _extract_record(raw_record: dict) -> dict:
    """Extract record fields from a raw SDK record dictionary.

    Pulls data_source, record_id, and feature values (name, address, phone,
    identifiers) from the SDK's record format.

    Args:
        raw_record: A record dict from the SDK export (RESOLVED_ENTITY.RECORDS).

    Returns:
        Dictionary with data_source, record_id, name, address, phone, identifiers.
    """
    name_data = raw_record.get("NAME_DATA", [])
    address_data = raw_record.get("ADDRESS_DATA", [])
    phone_data = raw_record.get("PHONE_DATA", [])
    identifier_data = raw_record.get("IDENTIFIER_DATA", [])

    # Extract first name value or empty string
    name = name_data[0] if name_data else ""

    # Extract first address value or empty string
    address = address_data[0] if address_data else ""

    # Extract first phone value or None
    phone = phone_data[0] if phone_data else None

    # Build identifiers dict from identifier data
    identifiers: dict[str, str] = {}
    for ident in identifier_data:
        if isinstance(ident, dict):
            for key, value in ident.items():
                identifiers[key] = value
        elif isinstance(ident, str) and ":" in ident:
            key, _, value = ident.partition(":")
            identifiers[key.strip()] = value.strip()

    return {
        "data_source": raw_record.get("DATA_SOURCE", ""),
        "record_id": raw_record.get("RECORD_ID", ""),
        "name": name,
        "address": address,
        "phone": phone,
        "identifiers": identifiers,
    }


def build_from_engine(engine: object) -> list[dict] | dict:
    """Build merges list from a live Senzing engine instance.

    Calls engine.export_json_entity_report() to retrieve all entities,
    filters to multi-record entities (record_count >= 2), and extracts
    constituent records with their feature data and match keys.

    Args:
        engine: A Senzing engine instance with export_json_entity_report,
            fetch_next, and close_export methods.

    Returns:
        List of multi-record entity dicts on success,
        or {"error": str} on failure.
    """
    try:
        export_handle = engine.export_json_entity_report()
        merges: list[dict] = []

        while True:
            record = engine.fetch_next(export_handle)
            if not record:
                break
            entity = json.loads(record)
            resolved = entity.get("RESOLVED_ENTITY", entity)
            records_list = resolved.get("RECORDS", [])

            # Only include multi-record entities (Property P4)
            if len(records_list) < 2:
                continue

            entity_id = resolved.get("ENTITY_ID", 0)
            entity_name = resolved.get("ENTITY_NAME", "")

            # Extract match key from entity features or records
            match_key = ""
            features = resolved.get("FEATURES", {})
            if features:
                # Use first available match key from features
                for feature_records in features.values():
                    if isinstance(feature_records, list):
                        for feat in feature_records:
                            if isinstance(feat, dict) and "MATCH_KEY" in feat:
                                match_key = feat["MATCH_KEY"]
                                break
                    if match_key:
                        break

            # Fall back to record-level match keys
            if not match_key:
                for rec in records_list:
                    rec_match_key = rec.get("MATCH_KEY", "")
                    if rec_match_key:
                        match_key = rec_match_key
                        break

            # If still no match key, use a default based on multi-record status
            if not match_key:
                match_key = "+NAME+ADDRESS"

            # Extract records with feature data
            extracted_records = [_extract_record(r) for r in records_list]

            merge_entity = MergeEntity(
                entity_id=entity_id,
                entity_name=entity_name,
                match_key=match_key,
                records=extracted_records,
            )
            merges.append(merge_entity.to_dict())

        engine.close_export(export_handle)
        return merges
    except Exception as e:
        return {"error": str(e)}
