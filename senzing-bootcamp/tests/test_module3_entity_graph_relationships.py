"""Fix-checking and preservation tests for the module3-entity-graph-relationships bugfix.

The Module 3 Entity Graph renders entity nodes but zero relationship edges because the
visualization steering specifies the `edges` schema without specifying HOW
`graph_builder.py` discovers relationships. The fix adds an explicit
relationship-discovery instruction (a `find_network_by_entity_id` call for
multi-record/related entities AND/OR a relationship-inclusion export flag such as
`SZ_ENTITY_INCLUDE_ALL_RELATIONS`) to BOTH Module 3 visualization steering files.

This module is authored against the UNFIXED steering:

- Property 1 (Fix Checking) discovery tests are EXPECTED TO FAIL on the current content —
  their failure confirms the bug (no relationship-discovery method in the edge-building
  context). They PASS once the fix lands.
- Property 1 edge-schema test and all Property 2 (Preservation) tests are EXPECTED TO PASS
  on the current content — they pin the baseline the fix must not regress.

Feature: module3-entity-graph-relationships

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3**
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — the two Module 3 visualization steering files (the only fix surfaces)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"

# Phase2_File: executable steps + builder table.
_PHASE2_FILE = _STEERING_DIR / "module-03-phase2-visualization.md"
# ApiRef_File: GET /api/graph schema companion.
_APIREF_FILE = _STEERING_DIR / "module-03-visualization-api-reference.md"

# Edge schema fields every edge element carries (Property 1 — must be preserved).
_EDGE_SCHEMA_FIELDS = (
    "source_entity_id",
    "target_entity_id",
    "match_key",
    "relationship_type",
)

# The MCP server host that must never appear as a URL in steering (security gate).
# Assembled from parts so the literal host string is not embedded in this file.
_MCP_URL_FRAGMENT = "mcp.senzing" + ".com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file.

    Args:
        path: The file to read.

    Returns:
        The decoded file contents.
    """
    return path.read_text(encoding="utf-8")


def _mentions_relationship_discovery(text: str) -> bool:
    """Return whether ``text`` names a Senzing relationship-discovery method.

    A relationship-discovery method is either a `find_network_by_entity_id` call or a
    relationship-inclusion export flag (e.g. `SZ_ENTITY_INCLUDE_ALL_RELATIONS`).

    Args:
        text: The text region to scan.

    Returns:
        True if a discovery method is named, False otherwise.
    """
    if "find_network_by_entity_id" in text:
        return True
    # Relationship-inclusion export flag, e.g. SZ_ENTITY_INCLUDE_ALL_RELATIONS.
    return bool(re.search(r"SZ_[A-Z_]*INCLUDE[A-Z_]*RELATION", text))


def _edge_building_context(text: str, window: int = 3) -> str:
    """Extract the edge-building region of Phase2_File.

    The fix expands the `graph_builder.py` builder-table row and the
    `GET /api/graph` summary bullet. This gathers those lines (each plus a small
    trailing window) so the discovery assertion is scoped to the edge-building
    context rather than the generic allowed-SDK-calls list near the top of the file.

    Args:
        text: The full Phase2_File contents.
        window: Number of trailing lines to include after each matching line.

    Returns:
        The joined edge-building-context text.
    """
    lines = text.splitlines()
    selected: list[str] = []
    for idx, line in enumerate(lines):
        if "graph_builder.py" in line or "/api/graph" in line:
            selected.extend(lines[idx : idx + 1 + window])
    return "\n".join(selected)


def _graph_section(text: str) -> str:
    """Extract the `GET /api/graph` section from ApiRef_File.

    Returns the text from the `GET /api/graph` endpoint heading up to the next
    endpoint heading (`GET /api/merges`).

    Args:
        text: The full ApiRef_File contents.

    Returns:
        The `GET /api/graph` section text (empty string if the heading is absent).
    """
    start = text.find("`GET /api/graph`")
    if start == -1:
        return ""
    rest = text[start + len("`GET /api/graph`") :]
    end = rest.find("`GET /api/merges`")
    return rest if end == -1 else rest[:end]


def _external_urls(text: str) -> list[str]:
    """Return any non-localhost http(s) URLs found in ``text``.

    localhost / loopback URLs (used for the local web service) are allowed; any
    other http(s) URL counts as an external URL introduction.

    Args:
        text: The text to scan.

    Returns:
        A list of external URL strings (empty when none are present).
    """
    urls = re.findall(r"https?://[^\s)\"'`]+", text)
    return [u for u in urls if not re.match(r"https?://(localhost|127\.0\.0\.1)", u)]


# ===========================================================================
# Property 1 — Fix Checking: steering specifies a working discovery method
# ===========================================================================


class TestRelationshipDiscoverySpecified:
    """Property 1: the steering specifies a relationship-discovery method.

    The two discovery tests are authored to FAIL on the unfixed content (no
    `find_network_by_entity_id` and no relationship-inclusion flag in the
    edge-building context) and to PASS once the fix lands. The edge-schema test
    pins the schema fields and PASSES on both unfixed and fixed content.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """

    def test_phase2_specifies_relationship_discovery(self) -> None:
        """Phase2_File names a discovery method in the edge-building context.

        FAILS on unfixed content — `find_network_by_entity_id` appears only in the
        generic allowed-SDK-calls list, not in the `graph_builder.py` row or the
        `GET /api/graph` summary, and no relationship-inclusion flag is present.
        """
        context = _edge_building_context(_read(_PHASE2_FILE))
        assert _mentions_relationship_discovery(context), (
            "Phase2_File does not specify how graph_builder.py discovers "
            "relationships in the edge-building context: expected a "
            "find_network_by_entity_id call and/or a relationship-inclusion export "
            "flag (e.g. SZ_ENTITY_INCLUDE_ALL_RELATIONS) in the graph_builder.py "
            "builder-table row or the GET /api/graph summary bullet, but found "
            "neither. Edges therefore come back empty (the bug)."
        )

    def test_apiref_specifies_edge_discovery(self) -> None:
        """The ApiRef_File `GET /api/graph` section describes edge discovery.

        FAILS on unfixed content — the section documents only the node/edge schema
        and example JSON, with no statement of how edges are discovered.
        """
        section = _graph_section(_read(_APIREF_FILE))
        assert section, "ApiRef_File is missing the GET /api/graph section"
        assert _mentions_relationship_discovery(section), (
            "The GET /api/graph section of ApiRef_File does not describe how edges "
            "are discovered: expected a find_network_by_entity_id call and/or a "
            "relationship-inclusion export flag (e.g. SZ_ENTITY_INCLUDE_ALL_RELATIONS), "
            "but the section only specifies the edge schema."
        )

    def test_edge_schema_fields_present(self) -> None:
        """Both files still describe every edge schema field (preserved)."""
        for path in (_PHASE2_FILE, _APIREF_FILE):
            content = _read(path)
            for field in _EDGE_SCHEMA_FIELDS:
                assert field in content, (
                    f"{path.name} no longer describes the edge field '{field}'; "
                    "the edge schema must be preserved."
                )


# ===========================================================================
# Property 2 — Preservation: node schema, UX, endpoints, and no URLs
# ===========================================================================


class TestNodeSchemaAndUxPreserved:
    """Property 2: node schema and Entity Graph UX remain in Phase2_File.

    PASSES on unfixed content and must keep passing after the fix (which touches
    only edge discovery).

    **Validates: Requirements 3.1**
    """

    _NODE_FIELDS = ("entity_id", "entity_name", "record_count", "data_sources", "records")
    _COLOR_HEXES = ("#3b82f6", "#22c55e", "#f59e0b")
    _TABS = ("Entity_Graph", "Record_Merges_View", "Merge_Statistics", "Probe_Panel")

    def test_node_schema_fields_present(self) -> None:
        """The node schema fields remain specified in Phase2_File."""
        content = _read(_PHASE2_FILE)
        for field in self._NODE_FIELDS:
            assert field in content, f"Phase2_File lost node schema field '{field}'"

    def test_graph_container_height_preserved(self) -> None:
        """The viewport-relative graph container height remains."""
        content = _read(_PHASE2_FILE)
        assert "calc(100vh - 120px)" in content, (
            "Phase2_File lost the `calc(100vh - 120px)` graph container height"
        )

    def test_color_hex_values_preserved(self) -> None:
        """The data-source node color hex values remain."""
        content = _read(_PHASE2_FILE)
        for hex_value in self._COLOR_HEXES:
            assert hex_value in content, f"Phase2_File lost color hex '{hex_value}'"

    def test_tab_structure_preserved(self) -> None:
        """All four visualization tabs remain in Phase2_File."""
        content = _read(_PHASE2_FILE)
        for tab in self._TABS:
            assert tab in content, f"Phase2_File lost the '{tab}' tab"


class TestOtherEndpointsUnchanged:
    """Property 2: the other endpoints keep their required fields.

    PASSES on unfixed content. The fix touches only `GET /api/graph` edge
    discovery, so `/api/stats`, `/api/merges`, and `/api/search` must be untouched.

    **Validates: Requirements 3.2**
    """

    _STATS_FIELDS = (
        "records_total",
        "entities_total",
        "multi_record_entities",
        "cross_source_entities",
        "relationships_total",
        "histogram",
    )
    _MERGES_FIELDS = ("entity_id", "entity_name", "match_key", "records")
    _SEARCH_FIELDS = ("match_keys", "feature_scores", "resolution_rules", "enrichment_error")

    def test_endpoint_paths_present_in_both_files(self) -> None:
        """Both files still reference the other three endpoints."""
        for path in (_PHASE2_FILE, _APIREF_FILE):
            content = _read(path)
            for endpoint in ("/api/stats", "/api/merges", "/api/search"):
                assert endpoint in content, (
                    f"{path.name} no longer references '{endpoint}'"
                )

    def test_stats_required_fields_present(self) -> None:
        """`/api/stats` required fields remain in ApiRef_File."""
        content = _read(_APIREF_FILE)
        for field in self._STATS_FIELDS:
            assert field in content, f"ApiRef_File lost /api/stats field '{field}'"

    def test_merges_required_fields_present(self) -> None:
        """`/api/merges` required fields remain in ApiRef_File."""
        content = _read(_APIREF_FILE)
        for field in self._MERGES_FIELDS:
            assert field in content, f"ApiRef_File lost /api/merges field '{field}'"

    def test_search_required_fields_present(self) -> None:
        """`/api/search` enrichment fields remain in ApiRef_File."""
        content = _read(_APIREF_FILE)
        for field in self._SEARCH_FIELDS:
            assert field in content, f"ApiRef_File lost /api/search field '{field}'"


class TestNoUrlsAdded:
    """Property 2: neither file contains an MCP URL or an external URL.

    PASSES on unfixed content (only `http://localhost` service URLs and the
    protocol-less `d3js.org` CDN reference exist). The fix refers to the Senzing
    MCP server by name only — it must not introduce an MCP URL or any other
    external http(s) URL.

    **Validates: Requirements 3.3**
    """

    def test_no_mcp_url(self) -> None:
        """Neither file contains the MCP server URL fragment."""
        for path in (_PHASE2_FILE, _APIREF_FILE):
            content = _read(path)
            assert _MCP_URL_FRAGMENT not in content, (
                f"{path.name} contains the MCP server URL '{_MCP_URL_FRAGMENT}'; "
                "the steering must refer to the MCP server by name only."
            )

    def test_no_external_urls(self) -> None:
        """Neither file contains a non-localhost http(s) URL."""
        for path in (_PHASE2_FILE, _APIREF_FILE):
            external = _external_urls(_read(path))
            assert not external, (
                f"{path.name} contains external URL(s) {external!r}; the fix must "
                "not introduce external URLs into the steering."
            )
