#!/usr/bin/env python3
"""Stdlib HTTP server for the TruthSet standalone demo.

Serves the single self-contained ``index.html`` produced by ``write_html.py``
for the journey-level first-visualization guarantee (standalone-demo path). It
reuses the Module 3 Step 9 web-service pattern and constraints from
``senzing-bootcamp/steering/module-03-phase2-visualization.md``:

- Python stdlib HTTP server only (``http.server.HTTPServer`` +
  ``BaseHTTPRequestHandler``) — no Flask, FastAPI, or third-party frameworks.
- All artifacts live inside the working directory
  (``src/system_verification/web_service/``).

The demo is intentionally minimal: the graph data is embedded directly in
``index.html`` (D3.js v7 from the d3js.org CDN), so the server only needs to
serve that single static file. This mirrors the Step 9 server lifecycle without
the full four-endpoint API surface.

Usage:
    python3 src/system_verification/web_service/server.py
    python3 src/system_verification/web_service/server.py --port 8080
"""

from __future__ import annotations

import argparse
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_WEB_DIR = Path(__file__).resolve().parent
_INDEX_PATH = _WEB_DIR / "index.html"


class DemoRequestHandler(BaseHTTPRequestHandler):
    """Serve the generated ``index.html`` for the standalone demo.

    ``GET /`` and ``GET /index.html`` return the generated visualization page.
    Any other path returns HTTP 404. Errors reading the page return HTTP 500.
    """

    def do_GET(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler name
        """Handle a GET request for the demo page."""
        if self.path not in ("/", "/index.html"):
            self._send_text(404, "Not Found")
            return

        if not _INDEX_PATH.is_file():
            self._send_text(
                500,
                "index.html not found. Run write_html.py to generate it first.",
            )
            return

        try:
            body = _INDEX_PATH.read_bytes()
        except OSError as exc:
            self._send_text(500, f"Error reading index.html: {exc}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, message: str) -> None:
        """Send a plain-text response with *status* and *message*."""
        body = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Quiet the default per-request stderr logging."""
        return


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Serve the TruthSet standalone demo (stdlib HTTP server).",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host/interface to bind (default: localhost).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry-point: start the demo HTTP server.

    Returns:
        0 on a clean shutdown, 1 if the server cannot bind.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        server = HTTPServer((args.host, args.port), DemoRequestHandler)
    except OSError as exc:
        print(
            f"Error: cannot bind {args.host}:{args.port} ({exc}). "
            "Try a different --port or stop the process using it.",
        )
        return 1

    print(
        f"Standalone demo running — open http://{args.host}:{args.port} "
        "in your browser (Ctrl+C to stop).",
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down standalone demo server.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
