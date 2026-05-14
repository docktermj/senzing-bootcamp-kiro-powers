"""HTTP server for the entity resolution visualization web service.

Provides a stdlib HTTP server with routing to API endpoints and static HTML,
plus color mapping, node sizing, and error handling utilities.

Usage:
    python server.py [--port 8080]
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Add the web_service directory to sys.path so builders can be imported
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import graph_builder  # noqa: E402
import merges_builder  # noqa: E402
import search_builder  # noqa: E402
import stats_builder  # noqa: E402


# ---------------------------------------------------------------------------
# Color mapping
# ---------------------------------------------------------------------------

_DATA_SOURCE_COLORS: dict[str, str] = {
    "CUSTOMERS": "#3b82f6",
    "REFERENCE": "#22c55e",
    "WATCHLIST": "#f59e0b",
}


def get_data_source_color(data_source: str) -> str:
    """Return the hex color for a given data source.

    Args:
        data_source: One of CUSTOMERS, REFERENCE, or WATCHLIST.

    Returns:
        Hex color string (e.g., "#3b82f6").
    """
    return _DATA_SOURCE_COLORS.get(data_source, "#6b7280")


# ---------------------------------------------------------------------------
# Node sizing
# ---------------------------------------------------------------------------

_BASE_RADIUS: int = 8
_SCALE_FACTOR: int = 4
_MIN_RADIUS: int = 8
_MAX_RADIUS: int = 40


def compute_node_radius(record_count: int) -> int:
    """Compute the display radius for an entity node.

    Formula: radius = min(max(8 + record_count * 4, 8), 40)

    Args:
        record_count: Number of constituent records in the entity.

    Returns:
        Radius in pixels, clamped between 8 and 40.
    """
    radius = _BASE_RADIUS + record_count * _SCALE_FACTOR
    return min(max(radius, _MIN_RADIUS), _MAX_RADIUS)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def build_error_response(error_msg: str) -> tuple[int, dict]:
    """Build a standardized error response.

    Args:
        error_msg: Description of the error.

    Returns:
        Tuple of (HTTP status code, response body dict).
    """
    return 500, {"error": error_msg}


# ---------------------------------------------------------------------------
# Senzing engine singleton (set at server start)
# ---------------------------------------------------------------------------

_engine: object | None = None


def set_engine(engine: object) -> None:
    """Set the Senzing engine instance used by the server.

    Args:
        engine: A Senzing engine instance with SDK methods.
    """
    global _engine
    _engine = engine


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------


class VisualizationHandler(BaseHTTPRequestHandler):
    """Routes HTTP GET requests to API builders or serves static HTML.

    Routing table:
        GET /           → serve index.html
        GET /api/stats  → StatsBuilder.build()
        GET /api/graph  → GraphBuilder.build()
        GET /api/merges → MergesBuilder.build()
        GET /api/search → SearchBuilder.search() with query params
        Other           → 404 JSON response
    """

    def do_GET(self) -> None:
        """Handle all GET requests by dispatching to the appropriate handler."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_index_html()
        elif path == "/api/stats":
            self._handle_stats()
        elif path == "/api/graph":
            self._handle_graph()
        elif path == "/api/merges":
            self._handle_merges()
        elif path == "/api/search":
            self._handle_search(parsed.query)
        else:
            self._send_json_response(404, {"error": "Not found"})

    def _set_cors_headers(self) -> None:
        """Set CORS headers for local development."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def _send_json_response(self, status_code: int, data: dict | list) -> None:
        """Send a JSON response with CORS headers.

        Args:
            status_code: HTTP status code.
            data: JSON-serializable data to send.
        """
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _serve_index_html(self) -> None:
        """Serve the index.html visualization page."""
        html_path = os.path.join(_THIS_DIR, "index.html")
        if not os.path.isfile(html_path):
            self._send_json_response(404, {"error": "index.html not found"})
            return

        try:
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except OSError as e:
            self._send_json_response(500, {"error": f"Failed to read index.html: {e}"})

    def _handle_stats(self) -> None:
        """Handle GET /api/stats — compute and return entity resolution statistics."""
        if _engine is None:
            self._send_json_response(503, {"error": "SDK not initialized"})
            return

        result = stats_builder.build(_engine)
        if "error" in result:
            self._send_json_response(500, result)
        else:
            self._send_json_response(200, result)

    def _handle_graph(self) -> None:
        """Handle GET /api/graph — build and return entity graph data."""
        if _engine is None:
            self._send_json_response(503, {"error": "SDK not initialized"})
            return

        result = graph_builder.build(_engine)
        if "error" in result:
            self._send_json_response(500, result)
        else:
            self._send_json_response(200, result)

    def _handle_merges(self) -> None:
        """Handle GET /api/merges — build and return multi-record entity merges."""
        if _engine is None:
            self._send_json_response(503, {"error": "SDK not initialized"})
            return

        result = merges_builder.build_from_engine(_engine)
        if isinstance(result, dict) and "error" in result:
            self._send_json_response(500, result)
        else:
            self._send_json_response(200, result)

    def _handle_search(self, query_string: str) -> None:
        """Handle GET /api/search — search entities by attributes.

        Args:
            query_string: URL query string with name, address, phone params.
        """
        if _engine is None:
            self._send_json_response(503, {"error": "SDK not initialized"})
            return

        params = parse_qs(query_string)
        name = params.get("name", [None])[0]
        address = params.get("address", [None])[0]
        phone = params.get("phone", [None])[0]

        status_code, result = search_builder.search(
            _engine, name=name, address=address, phone=phone
        )
        self._send_json_response(status_code, result)

    def log_message(self, format: str, *args: object) -> None:
        """Override to use a cleaner log format.

        Args:
            format: Log format string.
            *args: Format arguments.
        """
        sys.stderr.write(f"[server] {args[0]} {args[1]} {args[2]}\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(port: int | None = None) -> None:
    """Start the visualization HTTP server.

    Args:
        port: Port number to listen on. Defaults to PORT env var or 8080.
    """
    if port is None:
        port = int(os.environ.get("PORT", "8080"))

    server_address = ("", port)
    httpd = HTTPServer(server_address, VisualizationHandler)
    print(f"Visualization server running at http://localhost:{port}/")
    print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Entity Resolution Visualization Server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (default: PORT env var or 8080)",
    )
    args = parser.parse_args()
    main(port=args.port)
