"""Search builder for the entity resolution visualization web service.

Wraps the Senzing SDK search_by_attributes call for the probe panel.

Usage:
    # With live SDK engine (server use case):
    status, result = search(engine, name="Bob Smith")
"""

from __future__ import annotations

import json


def search(
    engine: object,
    name: str | None = None,
    address: str | None = None,
    phone: str | None = None,
) -> tuple[int, dict]:
    """Search for entities matching the given attributes.

    Builds a search attributes JSON from the provided parameters and calls
    the SDK's search_by_attributes method. At least one parameter must be
    provided.

    Args:
        engine: A Senzing engine instance with a search_by_attributes method.
        name: Full name to search for.
        address: Full address to search for.
        phone: Phone number to search for.

    Returns:
        Tuple of (HTTP status code, response body dict). The response body
        contains "results" (list of matching entities) and "query" (the
        search parameters used). Returns 400 if no parameters provided,
        500 on SDK errors.
    """
    # Validate at least one search parameter is provided
    if not name and not address and not phone:
        return 400, {"error": "At least one search parameter required"}

    # Build search attributes JSON (only include non-None fields)
    attributes: dict[str, str] = {}
    if name is not None:
        attributes["NAME_FULL"] = name
    if address is not None:
        attributes["ADDR_FULL"] = address
    if phone is not None:
        attributes["PHONE_NUMBER"] = phone

    query = {"name": name, "address": address, "phone": phone}

    try:
        response_json = engine.search_by_attributes(json.dumps(attributes))
        response = json.loads(response_json)

        # Extract matching entities from SDK response
        results: list[dict] = []
        resolved_entities = response.get("RESOLVED_ENTITIES", [])

        for resolved in resolved_entities:
            entity = resolved.get("ENTITY", resolved.get("RESOLVED_ENTITY", {}))
            entity_id = entity.get("ENTITY_ID", 0)
            entity_name = entity.get("ENTITY_NAME", "")
            records = entity.get("RECORDS", [])
            record_count = len(records)
            data_sources = list({r.get("DATA_SOURCE", "") for r in records})
            match_info = resolved.get("MATCH_INFO", {})
            match_score = match_info.get("MATCH_SCORE", 0)

            results.append({
                "entity_id": entity_id,
                "entity_name": entity_name,
                "record_count": record_count,
                "data_sources": data_sources,
                "match_score": match_score,
            })

        return 200, {"results": results, "query": query}
    except Exception as e:
        return 500, {"error": str(e)}
