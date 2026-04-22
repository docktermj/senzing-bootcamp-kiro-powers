"""Tests for render_html and _graph_data_to_dict in generate_visualization."""

from __future__ import annotations

import json

from src.query.generate_visualization import (
    EntityNode,
    GraphData,
    GraphMetadata,
    Record,
    RelationshipEdge,
    _graph_data_to_dict,
    render_html,
)


def _make_graph_data() -> GraphData:
    """Build a small GraphData fixture for testing."""
    return GraphData(
        metadata=GraphMetadata(
            data_source="CUSTOMERS",
            generated_at="2026-06-15T10:30:00+00:00",
            entity_count=2,
            record_count=3,
            relationship_count=1,
            data_sources=["CRM", "CUSTOMERS"],
        ),
        nodes=[
            EntityNode(
                entity_id=1,
                primary_name="John Smith",
                record_count=2,
                data_sources=["CRM", "CUSTOMERS"],
                primary_data_source="CUSTOMERS",
                records=[
                    Record(record_id="CUST-001", data_source="CUSTOMERS"),
                    Record(record_id="CRM-042", data_source="CRM"),
                ],
                features={
                    "NAME": ["John Smith", "J. Smith"],
                    "PHONE": ["555-123-4567"],
                },
            ),
            EntityNode(
                entity_id=2,
                primary_name="Jane Doe",
                record_count=1,
                data_sources=["CUSTOMERS"],
                primary_data_source="CUSTOMERS",
                records=[
                    Record(record_id="CUST-002", data_source="CUSTOMERS"),
                ],
                features={"NAME": ["Jane Doe"]},
            ),
        ],
        edges=[
            RelationshipEdge(
                source_entity_id=1,
                target_entity_id=2,
                match_level=2,
                match_strength="moderate",
                shared_features=["ADDRESS"],
            ),
        ],
    )


# ---- _graph_data_to_dict tests ----


def test_graph_data_to_dict_metadata():
    gd = _make_graph_data()
    d = _graph_data_to_dict(gd)

    assert d["metadata"]["dataSource"] == "CUSTOMERS"
    assert d["metadata"]["entityCount"] == 2
    assert d["metadata"]["recordCount"] == 3
    assert d["metadata"]["relationshipCount"] == 1
    assert d["metadata"]["dataSources"] == ["CRM", "CUSTOMERS"]


def test_graph_data_to_dict_nodes():
    gd = _make_graph_data()
    d = _graph_data_to_dict(gd)

    assert len(d["nodes"]) == 2
    node = d["nodes"][0]
    assert node["entityId"] == 1
    assert node["primaryName"] == "John Smith"
    assert node["recordCount"] == 2
    assert node["primaryDataSource"] == "CUSTOMERS"
    assert node["records"][0] == {
        "recordId": "CUST-001",
        "dataSource": "CUSTOMERS",
    }
    assert node["features"]["NAME"] == ["John Smith", "J. Smith"]


def test_graph_data_to_dict_edges():
    gd = _make_graph_data()
    d = _graph_data_to_dict(gd)

    assert len(d["edges"]) == 1
    edge = d["edges"][0]
    assert edge["sourceEntityId"] == 1
    assert edge["targetEntityId"] == 2
    assert edge["matchLevel"] == 2
    assert edge["matchStrength"] == "moderate"
    assert edge["sharedFeatures"] == ["ADDRESS"]


def test_graph_data_to_dict_is_json_serializable():
    gd = _make_graph_data()
    d = _graph_data_to_dict(gd)
    # Should not raise
    json.dumps(d)


# ---- render_html tests ----


def test_render_html_is_valid_html5():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert html.startswith("<!DOCTYPE html>")
    assert "<html lang=" in html
    assert "</html>" in html


def test_render_html_embeds_graph_data_as_json():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert "var GRAPH_DATA = " in html
    # Extract the JSON and verify it parses
    start = html.index("var GRAPH_DATA = ") + len("var GRAPH_DATA = ")
    end = html.index(";", start)
    parsed = json.loads(html[start:end])
    assert parsed["metadata"]["dataSource"] == "CUSTOMERS"
    assert len(parsed["nodes"]) == 2


def test_render_html_embeds_d3_source():
    gd = _make_graph_data()
    d3_src = "function d3_mock() { return 42; }"
    html = render_html(gd, d3_src, "body{}", "console.log(1);")

    assert d3_src in html


def test_render_html_embeds_css():
    gd = _make_graph_data()
    css = "#graph-svg { width: 100%; }"
    html = render_html(gd, "/* d3 */", css, "console.log(1);")

    assert css in html
    assert "<style>" in html


def test_render_html_embeds_js():
    gd = _make_graph_data()
    js = "const renderer = new GraphRenderer();"
    html = render_html(gd, "/* d3 */", "body{}", js)

    assert js in html


def test_render_html_has_try_catch_wrapper():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert "try {" in html
    assert "catch (err)" in html
    assert "failed to initialize" in html.lower()


def test_render_html_has_required_divs():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert 'id="graph-svg"' in html
    assert 'id="detail-panel"' in html
    assert 'id="stats-bar"' in html
    assert 'id="search-input"' in html or 'id="search-container"' in html
    assert 'id="clustering-controls"' in html


def test_render_html_no_external_references():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert "<script src=" not in html
    assert "<link href=" not in html
    assert "<img src=http" not in html


def test_render_html_no_placeholders_remain():
    gd = _make_graph_data()
    html = render_html(gd, "/* d3 */", "body{}", "console.log(1);")

    assert "{{GRAPH_DATA_JSON}}" not in html
    assert "{{D3_LIBRARY}}" not in html
    assert "{{RENDERER_CSS}}" not in html
    assert "{{RENDERER_JS}}" not in html


def test_render_html_empty_graph():
    """render_html works with zero nodes and edges."""
    gd = GraphData(
        metadata=GraphMetadata(
            data_source="EMPTY",
            generated_at="2026-01-01T00:00:00+00:00",
            entity_count=0,
            record_count=0,
            relationship_count=0,
            data_sources=[],
        ),
        nodes=[],
        edges=[],
    )
    html = render_html(gd, "/* d3 */", "", "")

    assert "<!DOCTYPE html>" in html
    assert "var GRAPH_DATA = " in html
    # Verify the embedded JSON has empty arrays
    start = html.index("var GRAPH_DATA = ") + len("var GRAPH_DATA = ")
    end = html.index(";", start)
    parsed = json.loads(html[start:end])
    assert parsed["nodes"] == []
    assert parsed["edges"] == []
