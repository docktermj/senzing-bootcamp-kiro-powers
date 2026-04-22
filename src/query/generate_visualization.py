"""Senzing Entity Graph Visualization Generator.

Queries the Senzing SDK, extracts resolved entity and relationship data,
and produces a self-contained HTML file with an interactive D3.js
force-directed graph.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import math
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model classes
# ---------------------------------------------------------------------------

@dataclass
class Record:
    """A single source record contributing to a resolved entity."""

    record_id: str
    data_source: str


@dataclass
class EntityNode:
    """A resolved entity node in the graph."""

    entity_id: int
    primary_name: str
    record_count: int
    data_sources: list[str]
    primary_data_source: str
    records: list[Record]
    features: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class RelationshipEdge:
    """An edge connecting two related entities."""

    source_entity_id: int
    target_entity_id: int
    match_level: int
    match_strength: str
    shared_features: list[str]


@dataclass
class GraphMetadata:
    """Metadata about the generated graph."""

    data_source: str
    generated_at: str
    entity_count: int
    record_count: int
    relationship_count: int
    data_sources: list[str]


@dataclass
class GraphData:
    """Top-level graph data structure embedded in the HTML output."""

    metadata: GraphMetadata
    nodes: list[EntityNode]
    edges: list[RelationshipEdge]


# ---------------------------------------------------------------------------
# Edge colour mapping by match strength
# ---------------------------------------------------------------------------

EDGE_COLORS: dict[str, str] = {
    "strong": "#22c55e",
    "moderate": "#f59e0b",
    "weak": "#ef4444",
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def classify_match_strength(match_level: int) -> str:
    """Map a Senzing match-level integer to a categorical strength.

    1 → "strong", 2 → "moderate", 3+ → "weak".
    """
    if match_level == 1:
        return "strong"
    if match_level == 2:
        return "moderate"
    return "weak"


def compute_node_radius(record_count: int) -> float:
    """Return a node radius that increases monotonically with *record_count*.

    Uses a square-root scale so that visual area grows linearly with count,
    with a minimum base radius of 5 and a scaling factor of 4.
    """
    base = 5.0
    scale = 4.0
    return base + scale * math.sqrt(record_count)


def load_d3_source() -> str:
    """Read the bundled D3.js v7 minified library and return its content.

    Looks for the file at ``senzing-bootcamp/templates/d3.v7.min.js``
    relative to the repository root (two levels up from this module).

    Raises
    ------
    FileNotFoundError
        If the D3.js file cannot be found at the expected path.
    """
    # Resolve relative to the repo root: this file lives at
    # src/query/generate_visualization.py → repo root is ../../
    repo_root = Path(__file__).resolve().parent.parent.parent
    d3_path = repo_root / "senzing-bootcamp" / "templates" / "assets" / "d3.v7.min.js"

    if not d3_path.is_file():
        raise FileNotFoundError(
            f"D3.js library not found at {d3_path}. "
            "Please ensure senzing-bootcamp/templates/assets/d3.v7.min.js exists. "
            "You can download it from https://d3js.org/d3.v7.min.js"
        )

    return d3_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def _parse_entity_response(response_json: str) -> EntityNode:
    """Parse a Senzing SDK entity JSON response into an EntityNode."""
    data = json.loads(response_json)
    resolved = data["RESOLVED_ENTITY"]

    entity_id = resolved["ENTITY_ID"]
    primary_name = resolved.get("ENTITY_NAME", "")

    records = [
        Record(record_id=r["RECORD_ID"], data_source=r["DATA_SOURCE"])
        for r in resolved.get("RECORDS", [])
    ]

    data_sources = sorted({r.data_source for r in records})

    # Primary data source = the source contributing the most records
    if records:
        source_counts = Counter(r.data_source for r in records)
        primary_data_source = source_counts.most_common(1)[0][0]
    else:
        primary_data_source = ""

    # Flatten features: map category -> list of FEAT_DESC strings
    features: dict[str, list[str]] = {}
    for category, feat_list in resolved.get("FEATURES", {}).items():
        features[category] = [f["FEAT_DESC"] for f in feat_list if "FEAT_DESC" in f]

    return EntityNode(
        entity_id=entity_id,
        primary_name=primary_name,
        record_count=len(records),
        data_sources=data_sources,
        primary_data_source=primary_data_source,
        records=records,
        features=features,
    )


def extract_entities(
    engine: object,
    data_source: str,
    limit: int | None,
    record_ids: list[str] | None = None,
) -> list[EntityNode]:
    """Query Senzing SDK for all resolved entities in a data source.

    Iterates over *record_ids* (if provided) or uses the engine's export
    functionality to discover records.  Each record is fetched via
    ``engine.get_entity_by_record_id(data_source, record_id)`` and the
    JSON response is transformed into an :class:`EntityNode`.

    Per-entity SDK errors are logged and skipped so that one bad record
    does not abort the entire extraction.

    Parameters
    ----------
    engine:
        A Senzing engine object exposing ``get_entity_by_record_id`` and,
        optionally, ``export_json_entity_report`` / ``fetch_next``.
    data_source:
        The Senzing data source name (e.g. ``"CUSTOMERS"``).
    limit:
        Maximum number of entities to return.  ``None`` means no limit.
    record_ids:
        Optional explicit list of record IDs to query.  When ``None`` the
        function attempts to use the engine's export API to discover
        records belonging to *data_source*.
    """
    # ------------------------------------------------------------------
    # 1. Obtain record IDs to iterate
    # ------------------------------------------------------------------
    if record_ids is None:
        record_ids = _discover_record_ids(engine, data_source)

    # ------------------------------------------------------------------
    # 2. Fetch and parse each entity, deduplicating by entity ID
    # ------------------------------------------------------------------
    seen_entity_ids: set[int] = set()
    entities: list[EntityNode] = []

    for record_id in record_ids:
        try:
            response_json = engine.get_entity_by_record_id(data_source, record_id)
            entity = _parse_entity_response(response_json)
        except Exception as exc:
            logger.warning(
                "Failed to retrieve entity for record %s in %s: %s. Skipping.",
                record_id,
                data_source,
                exc,
            )
            continue

        if entity.entity_id in seen_entity_ids:
            continue
        seen_entity_ids.add(entity.entity_id)
        entities.append(entity)

    # ------------------------------------------------------------------
    # 3. Entity-count warning and limit enforcement
    # ------------------------------------------------------------------
    if len(entities) > 500:
        logger.warning(
            "%d entities found. Rendering may be slow. "
            "Use --limit 500 to cap output.",
            len(entities),
        )

    if limit is not None:
        entities = entities[:limit]

    return entities


def extract_relationships(
    engine: object,
    entity_ids: list[int],
) -> list[RelationshipEdge]:
    """Extract relationships between entities via the Senzing SDK.

    For each entity in *entity_ids*, calls
    ``engine.get_entity_by_entity_id(entity_id)`` and inspects the
    ``RELATED_ENTITIES`` array in the response.  Each related-entity
    entry is converted to a :class:`RelationshipEdge` when the related
    entity is also present in *entity_ids*.

    Relationships are deduplicated so that A→B and B→A produce only a
    single edge (the one with the smaller entity ID as source).

    Per-entity SDK errors are logged and skipped so that one failure
    does not abort the entire extraction.

    Parameters
    ----------
    engine:
        A Senzing engine object exposing
        ``get_entity_by_entity_id``.
    entity_ids:
        The set of entity IDs to consider.  Only relationships
        where *both* endpoints are in this collection are returned.
    """
    entity_id_set: set[int] = set(entity_ids)
    seen_pairs: set[tuple[int, int]] = set()
    edges: list[RelationshipEdge] = []

    for entity_id in entity_ids:
        try:
            response_json = engine.get_entity_by_entity_id(
                entity_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to retrieve relationships for entity "
                "%s: %s. Skipping.",
                entity_id,
                exc,
            )
            continue

        try:
            data = json.loads(response_json)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning(
                "Invalid JSON for entity %s: %s. Skipping.",
                entity_id,
                exc,
            )
            continue

        related = data.get("RELATED_ENTITIES", [])
        for rel in related:
            target_id = rel.get("ENTITY_ID")
            if target_id is None or target_id not in entity_id_set:
                continue

            # Canonical pair: smaller ID first for dedup
            pair = (
                min(entity_id, target_id),
                max(entity_id, target_id),
            )
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            match_level = rel.get("MATCH_LEVEL", 3)
            match_key = rel.get("MATCH_KEY", "")
            shared_features = [
                f for f in match_key.split("+") if f
            ]

            edges.append(
                RelationshipEdge(
                    source_entity_id=pair[0],
                    target_entity_id=pair[1],
                    match_level=match_level,
                    match_strength=classify_match_strength(
                        match_level,
                    ),
                    shared_features=shared_features,
                ),
            )

    return edges


def _discover_record_ids(engine: object, data_source: str) -> list[str]:
    """Attempt to discover record IDs for *data_source* via the engine.

    Uses the engine's ``export_json_entity_report`` / ``fetch_next``
    methods when available.  Returns a list of record IDs belonging to
    *data_source*.
    """
    record_ids: list[str] = []

    if not hasattr(engine, "export_json_entity_report") or not hasattr(engine, "fetch_next"):
        return record_ids

    try:
        export_handle = engine.export_json_entity_report(0)
        while True:
            row = engine.fetch_next(export_handle)
            if not row:
                break
            try:
                entity_data = json.loads(row)
            except (json.JSONDecodeError, TypeError):
                continue
            for record in entity_data.get("RESOLVED_ENTITY", {}).get("RECORDS", []):
                if record.get("DATA_SOURCE") == data_source:
                    record_ids.append(record["RECORD_ID"])
    except Exception as exc:
        logger.warning("Failed to export entity report: %s", exc)

    return record_ids


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def assemble_graph_data(
    entities: list[EntityNode],
    relationships: list[RelationshipEdge],
    data_source: str,
) -> GraphData:
    """Combine entities and relationships into a :class:`GraphData`.

    Parameters
    ----------
    entities:
        The resolved entity nodes.
    relationships:
        The relationship edges between entities.
    data_source:
        The primary Senzing data source name used for the query.

    Returns
    -------
    GraphData
        A complete graph structure with metadata, nodes, and edges.
    """
    all_sources: set[str] = set()
    total_records = 0
    for entity in entities:
        all_sources.update(entity.data_sources)
        total_records += entity.record_count

    metadata = GraphMetadata(
        data_source=data_source,
        generated_at=datetime.datetime.now(
            datetime.timezone.utc,
        ).isoformat(),
        entity_count=len(entities),
        record_count=total_records,
        relationship_count=len(relationships),
        data_sources=sorted(all_sources),
    )

    return GraphData(
        metadata=metadata,
        nodes=entities,
        edges=relationships,
    )


# ---------------------------------------------------------------------------
# HTML template and rendering
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Senzing Entity Graph</title>
<style>
{{RENDERER_CSS}}
</style>
</head>
<body>
<div id="search-container"><input id="search-input" type="text" placeholder="Search entities by name or record ID…"></div>
<div id="clustering-controls"></div>
<div id="stats-bar"></div>
<div id="graph-svg"></div>
<div id="detail-panel"></div>
<script>
{{D3_LIBRARY}}
</script>
<script>
var GRAPH_DATA = {{GRAPH_DATA_JSON}};
</script>
<script>
try {
{{RENDERER_JS}}
} catch (err) {
  document.getElementById('graph-svg').innerHTML =
    '<p style="color:red;padding:1em;">Visualization failed to initialize: ' +
    err.message + '</p>';
}
</script>
</body>
</html>
"""


def _graph_data_to_dict(graph_data: GraphData) -> dict:
    """Serialize the :class:`GraphData` dataclass hierarchy to a plain dict.

    Converts all nested dataclasses (``GraphMetadata``, ``EntityNode``,
    ``RelationshipEdge``, ``Record``) into JSON-friendly dictionaries
    using camelCase keys to match the design document's JSON schema.
    """
    return {
        "metadata": {
            "dataSource": graph_data.metadata.data_source,
            "generatedAt": graph_data.metadata.generated_at,
            "entityCount": graph_data.metadata.entity_count,
            "recordCount": graph_data.metadata.record_count,
            "relationshipCount": graph_data.metadata.relationship_count,
            "dataSources": graph_data.metadata.data_sources,
        },
        "nodes": [
            {
                "entityId": n.entity_id,
                "primaryName": n.primary_name,
                "recordCount": n.record_count,
                "dataSources": n.data_sources,
                "primaryDataSource": n.primary_data_source,
                "records": [
                    {"recordId": r.record_id, "dataSource": r.data_source}
                    for r in n.records
                ],
                "features": n.features,
            }
            for n in graph_data.nodes
        ],
        "edges": [
            {
                "sourceEntityId": e.source_entity_id,
                "targetEntityId": e.target_entity_id,
                "matchLevel": e.match_level,
                "matchStrength": e.match_strength,
                "sharedFeatures": e.shared_features,
            }
            for e in graph_data.edges
        ],
    }


def render_html(
    graph_data: GraphData,
    d3_source: str,
    css: str,
    js: str,
) -> str:
    """Render a self-contained HTML visualization from *graph_data*.

    Substitutes the four template placeholders with the provided content
    and returns a complete HTML5 document string.

    Parameters
    ----------
    graph_data:
        The graph structure to embed as inline JSON.
    d3_source:
        The full D3.js library source code (minified).
    css:
        CSS styles for the graph renderer.
    js:
        JavaScript source for the graph renderer modules.

    Returns
    -------
    str
        A complete, self-contained HTML document.
    """
    graph_dict = _graph_data_to_dict(graph_data)
    graph_json = json.dumps(graph_dict, separators=(",", ":"))

    html = _HTML_TEMPLATE
    html = html.replace("{{GRAPH_DATA_JSON}}", graph_json)
    html = html.replace("{{D3_LIBRARY}}", d3_source)
    html = html.replace("{{RENDERER_CSS}}", css)
    html = html.replace("{{RENDERER_JS}}", js)
    return html


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------


def write_html(html_content: str, output_path: str) -> None:
    """Write *html_content* to *output_path*, creating directories as needed.

    Parameters
    ----------
    html_content:
        The complete HTML string to write.
    output_path:
        Destination file path (e.g. ``docs/entity_graph.html``).

    Raises
    ------
    SystemExit
        Exits with code 2 if the output directory cannot be created or
        is not writable.
    """
    path = Path(output_path)
    directory = path.parent

    # Ensure the parent directory exists
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"Error: Cannot write to {output_path}. "
            f"Failed to create directory {directory}: {exc}",
        )
        sys.exit(2)

    # Verify the directory is writable
    if not os.access(directory, os.W_OK):
        print(
            f"Error: Cannot write to {output_path}. "
            f"Check that the directory exists and is writable.",
        )
        sys.exit(2)

    # Write the file
    try:
        path.write_text(html_content, encoding="utf-8")
    except OSError as exc:
        print(
            f"Error: Cannot write to {output_path}. {exc}",
        )
        sys.exit(2)

    print(f"Saved visualization to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate an interactive entity-graph HTML visualization "
            "from a Senzing database."
        ),
    )
    parser.add_argument(
        "--data-source",
        required=True,
        help="Name of the Senzing data source to visualize (e.g. CUSTOMERS).",
    )
    parser.add_argument(
        "--output",
        default="docs/entity_graph.html",
        help=(
            "Output path for the HTML file "
            "(default: docs/entity_graph.html)."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of entities to include (default: no limit).",
    )
    return parser


def _init_senzing_engine():
    """Initialize the Senzing SDK engine using the local database.

    Returns the engine instance on success.  Prints a clear error
    message and calls ``sys.exit(1)`` if the SDK is not installed or
    the database file does not exist.
    """
    db_path = Path("database/G2C.db")
    if not db_path.is_file():
        print(
            "Error: Senzing database not found at database/G2C.db. "
            "Please complete Module 6 (data loading) before "
            "generating a visualization.",
        )
        sys.exit(1)

    try:
        import senzing  # noqa: F811
    except ImportError:
        print(
            "Error: Senzing SDK is not installed. "
            "Please install the senzing package "
            "(pip install senzing) before generating "
            "a visualization.",
        )
        sys.exit(1)

    try:
        engine = senzing.G2Engine()
        module_name = "generate_visualization"
        ini_params = json.dumps({
            "PIPELINE": {
                "CONFIGPATH": str(
                    db_path.resolve().parent,
                ),
                "SUPPORTPATH": str(
                    db_path.resolve().parent,
                ),
                "RESOURCEPATH": str(
                    db_path.resolve().parent,
                ),
            },
            "SQL": {
                "CONNECTION": (
                    f"sqlite3://na:na@{db_path.resolve()}"
                ),
            },
        })
        engine.init(module_name, ini_params, 0)
        return engine
    except Exception as exc:
        print(f"Error: Failed to initialize Senzing engine: {exc}")
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    """CLI entry-point for the visualization generator."""
    from src.query.renderer_css import RENDERER_CSS
    from src.query.renderer_js import RENDERER_JS

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    print(
        f"Generating visualization for data source "
        f"'{args.data_source}' → {args.output}",
    )

    # 1. Initialize Senzing SDK engine
    engine = _init_senzing_engine()

    try:
        # 2. Discover record IDs for the data source
        record_ids = _discover_record_ids(
            engine, args.data_source,
        )

        # 3. Extract entities
        entities = extract_entities(
            engine,
            args.data_source,
            args.limit,
            record_ids=record_ids if record_ids else None,
        )

        if not entities:
            print(
                "Error: No entities found in the Senzing "
                "database. Please load data using Module 6 "
                "before generating a visualization.",
            )
            sys.exit(1)

        # 4. Extract relationships
        entity_ids = [e.entity_id for e in entities]
        relationships = extract_relationships(
            engine, entity_ids,
        )

        if not relationships:
            logger.info(
                "Note: No relationships found between "
                "entities. The graph will show isolated "
                "nodes.",
            )

        # 5. Assemble graph data
        graph_data = assemble_graph_data(
            entities, relationships, args.data_source,
        )

        # 6. Load D3.js, CSS, JS
        d3_source = load_d3_source()
        css = RENDERER_CSS
        js = RENDERER_JS

        # 7. Render HTML
        html_content = render_html(
            graph_data, d3_source, css, js,
        )

        # 8. Write HTML to output path
        write_html(html_content, args.output)

    finally:
        # 9. Clean up / close engine
        try:
            engine.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
