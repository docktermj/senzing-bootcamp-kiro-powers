#!/usr/bin/env python3
"""Generate a minimal, TruthSet-backed standalone entity-resolution demo.

This is the journey-level "first visualization" fallback offered when a
bootcamper opts out of Module 3 at the Phase 1 Opt-Out Gate. It reuses the
Module 3 Step 9 web-service pattern (see
``steering/module-03-phase2-visualization.md``):

- Python stdlib HTTP server only (``http.server.HTTPServer`` +
  ``BaseHTTPRequestHandler`` / ``SimpleHTTPRequestHandler``) — no Flask,
  FastAPI, or third-party HTTP frameworks.
- D3.js v7 loaded from the d3js.org CDN (``d3js.org/d3.v7.min.js``) — no other
  external JavaScript dependency.
- A single self-contained ``index.html`` (embedded CSS + JS + data) produced by
  a generated ``write_html.py`` script.
- All artifacts live inside the working directory
  ``src/system_verification/web_service/``.

"Minimal" means a single force-directed entity graph view (not the full Step 9
four-tab dashboard). The sample data is a small, embedded TruthSet-shaped set
(CUSTOMERS / REFERENCE / WATCHLIST) so the demo is self-contained and requires
no SDK calls.

On successful generation this script calls
``clear_first_visualization_owed(satisfied_by="standalone_demo")`` so the
journey-level owed marker is satisfied. On failure it prints Step-9-style manual
fallback instructions and leaves the owed marker unchanged so the deferred
guarantee still applies.

Usage:
    python scripts/generate_standalone_demo.py
    python scripts/generate_standalone_demo.py --output-dir src/system_verification/web_service
    python scripts/generate_standalone_demo.py --port 8080
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_utils import clear_first_visualization_owed  # noqa: E402

DEFAULT_OUTPUT_DIR = "src/system_verification/web_service"
DEFAULT_PROGRESS_PATH = "config/bootcamp_progress.json"
DEFAULT_PORT = 8080

# ---------------------------------------------------------------------------
# Self-contained visualization page (single force-directed entity graph).
#
# D3.js v7 is loaded from the d3js.org CDN — the only external dependency, per
# the Module 3 Step 9 constraints. Data sources follow the TruthSet convention:
# CUSTOMERS (#3b82f6), REFERENCE (#22c55e), WATCHLIST (#f59e0b). The dataset is
# a small embedded sample so the demo needs no SDK calls.
#
# NOTE: this template must NOT contain a triple-double-quote sequence, because
# it is embedded verbatim inside the generated write_html.py as an r-string.
# ---------------------------------------------------------------------------
_INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Senzing Standalone Demo - Entity Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1f2937;
      background: #f9fafb;
    }
    header {
      height: 50px;
      display: flex;
      align-items: center;
      padding: 0 16px;
      background: #111827;
      color: #f9fafb;
      font-weight: 600;
    }
    #banner {
      height: 40px;
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 0 16px;
      background: #eef2ff;
      font-size: 13px;
      overflow-x: auto;
      white-space: nowrap;
    }
    #banner .stat b { color: #4338ca; }
    #banner .arrow { color: #9ca3af; }
    #graph-container {
      position: relative;
      width: 100%;
      height: calc(100vh - 90px);
    }
    #legend {
      position: absolute;
      top: 12px;
      right: 12px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 12px;
    }
    #legend .row { display: flex; align-items: center; gap: 6px; margin: 2px 0; }
    #legend .swatch { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    .link { stroke: #9ca3af; stroke-width: 1.5px; }
    .link-label { font-size: 10px; fill: #6b7280; }
    .node-label { font-size: 11px; fill: #374151; }
    .node circle { stroke: #fff; stroke-width: 1.5px; cursor: pointer; }
    #tooltip {
      position: absolute;
      pointer-events: none;
      background: #111827;
      color: #f9fafb;
      padding: 6px 8px;
      border-radius: 4px;
      font-size: 12px;
      opacity: 0;
      transition: opacity 0.1s;
    }
  </style>
</head>
<body>
  <header>Senzing Entity Resolution - Standalone Demo</header>
  <div id="banner"></div>
  <div id="graph-container">
    <div id="legend"></div>
    <div id="tooltip"></div>
  </div>

  <script>
    // Embedded TruthSet-shaped sample. Edges are keyed by
    // source_entity_id / target_entity_id (the Step 9 /api/graph contract).
    var DATA = {
      stats: {
        records_total: 9,
        entities_total: 5,
        multi_record_entities: 3,
        cross_source_entities: 2,
        relationships_total: 3
      },
      nodes: [
        { entity_id: 1, entity_name: "Robert Smith", record_count: 3,
          data_sources: ["CUSTOMERS", "REFERENCE"] },
        { entity_id: 2, entity_name: "Roberta Smith", record_count: 2,
          data_sources: ["CUSTOMERS"] },
        { entity_id: 3, entity_name: "Bob Smith Jr", record_count: 1,
          data_sources: ["WATCHLIST"] },
        { entity_id: 4, entity_name: "Jane Doe", record_count: 2,
          data_sources: ["CUSTOMERS", "REFERENCE"] },
        { entity_id: 5, entity_name: "Acme Holdings", record_count: 1,
          data_sources: ["REFERENCE"] }
      ],
      edges: [
        { source_entity_id: 1, target_entity_id: 3, match_key: "+NAME+DOB",
          relationship_type: "possible_match" },
        { source_entity_id: 1, target_entity_id: 2, match_key: "+ADDRESS",
          relationship_type: "disclosed" },
        { source_entity_id: 4, target_entity_id: 5, match_key: "+ADDRESS+PHONE",
          relationship_type: "discovered" }
      ]
    };

    var COLORS = { CUSTOMERS: "#3b82f6", REFERENCE: "#22c55e", WATCHLIST: "#f59e0b" };

    function primarySource(node) {
      return (node.data_sources && node.data_sources[0]) || "CUSTOMERS";
    }
    function nodeColor(node) {
      return COLORS[primarySource(node)] || "#6b7280";
    }
    function nodeRadius(node) {
      return Math.min(Math.max(8 + node.record_count * 4, 8), 40);
    }

    function renderBanner() {
      var s = DATA.stats;
      var parts = [
        ["Records Loaded", s.records_total],
        ["Resolved Entities", s.entities_total],
        ["Multi-Record Entities", s.multi_record_entities],
        ["Cross-Source Matches", s.cross_source_entities],
        ["Relationships", s.relationships_total]
      ];
      var banner = d3.select("#banner");
      parts.forEach(function (p, i) {
        if (i > 0) { banner.append("span").attr("class", "arrow").text("->"); }
        var stat = banner.append("span").attr("class", "stat");
        stat.append("span").text(p[0] + ": ");
        stat.append("b").text(p[1]);
      });
    }

    function renderLegend() {
      var legend = d3.select("#legend");
      legend.append("div").style("font-weight", "600").text("Data Sources");
      Object.keys(COLORS).forEach(function (name) {
        var row = legend.append("div").attr("class", "row");
        row.append("span").attr("class", "swatch").style("background", COLORS[name]);
        row.append("span").text(name);
      });
    }

    function drawGraph() {
      var container = document.getElementById("graph-container");
      var width = container.clientWidth;
      var height = container.clientHeight;

      var svg = d3.select("#graph-container").append("svg")
        .attr("width", width)
        .attr("height", height);
      var g = svg.append("g");

      svg.call(d3.zoom().scaleExtent([0.2, 4]).on("zoom", function (event) {
        g.attr("transform", event.transform);
      }));

      // Map each edge to expose source/target from *_entity_id BEFORE
      // forceLink resolves them (Critical Lesson 7 - avoids a silent empty graph).
      var links = DATA.edges.map(function (e) {
        return {
          source: e.source_entity_id,
          target: e.target_entity_id,
          match_key: e.match_key,
          relationship_type: e.relationship_type
        };
      });
      var nodes = DATA.nodes.map(function (n) {
        return Object.assign({ id: n.entity_id }, n);
      });

      var sim = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(function (d) { return d.id; }).distance(120))
        .force("charge", d3.forceManyBody().strength(-320))
        .force("center", d3.forceCenter(width / 2, height / 2));

      var link = g.append("g").selectAll("line")
        .data(links).enter().append("line").attr("class", "link");

      var linkLabel = g.append("g").selectAll("text")
        .data(links).enter().append("text")
        .attr("class", "link-label")
        .text(function (d) { return d.match_key; });

      var tooltip = d3.select("#tooltip");

      var node = g.append("g").selectAll("g")
        .data(nodes).enter().append("g").attr("class", "node");

      node.append("circle")
        .attr("r", function (d) { return nodeRadius(d); })
        .attr("fill", function (d) { return nodeColor(d); })
        .on("mouseover", function (event, d) {
          tooltip.style("opacity", 1)
            .html("<b>" + d.entity_name + "</b><br/>ID: " + d.entity_id +
                  "<br/>Records: " + d.record_count +
                  "<br/>Sources: " + d.data_sources.join(", "));
        })
        .on("mousemove", function (event) {
          tooltip.style("left", (event.pageX + 12) + "px")
                 .style("top", (event.pageY + 12) + "px");
        })
        .on("mouseout", function () { tooltip.style("opacity", 0); });

      node.append("text")
        .attr("class", "node-label")
        .attr("dy", function (d) { return nodeRadius(d) + 12; })
        .attr("text-anchor", "middle")
        .text(function (d) {
          var name = d.entity_name;
          return name.length > 20 ? name.slice(0, 20) + "\u2026" : name;
        });

      node.call(d3.drag()
        .on("start", function (event, d) {
          if (!event.active) { sim.alphaTarget(0.3).restart(); }
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", function (event, d) { d.fx = event.x; d.fy = event.y; })
        .on("end", function (event, d) {
          if (!event.active) { sim.alphaTarget(0); }
          d.fx = null; d.fy = null;
        }));

      sim.on("tick", function () {
        link.attr("x1", function (d) { return d.source.x; })
            .attr("y1", function (d) { return d.source.y; })
            .attr("x2", function (d) { return d.target.x; })
            .attr("y2", function (d) { return d.target.y; });
        linkLabel.attr("x", function (d) { return (d.source.x + d.target.x) / 2; })
                 .attr("y", function (d) { return (d.source.y + d.target.y) / 2; });
        node.attr("transform", function (d) {
          return "translate(" + d.x + "," + d.y + ")";
        });
      });

      window.addEventListener("resize", function () {
        var w = container.clientWidth;
        var h = container.clientHeight;
        svg.attr("width", w).attr("height", h);
        sim.force("center", d3.forceCenter(w / 2, h / 2));
        sim.alpha(0.3).restart();
      });
    }

    renderBanner();
    renderLegend();
    drawGraph();
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Generated write_html.py: writes index.html from the embedded HTML string.
# The header/footer must NOT contain a triple-double-quote sequence; the HTML
# body is concatenated in between as an r-string literal (see _build_write_html).
# ---------------------------------------------------------------------------
_WRITE_HTML_HEADER = '''#!/usr/bin/env python3
"""Generate the standalone-demo index.html (single self-contained page).

Run this to (re)produce index.html next to it:

    python3 write_html.py

The HTML embeds D3.js v7 from the d3js.org CDN and a small TruthSet-shaped
sample dataset. Regenerate by editing HTML below and re-running.
"""

from __future__ import annotations

from pathlib import Path

'''

_WRITE_HTML_FOOTER = '''

def main() -> int:
    """Write index.html next to this script. Returns 0 on success."""
    out = Path(__file__).resolve().parent / "index.html"
    out.write_text(HTML, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

# ---------------------------------------------------------------------------
# Generated server.py: stdlib HTTP server bound to localhost only.
# ---------------------------------------------------------------------------
_SERVER_PY = '''#!/usr/bin/env python3
"""Serve the standalone-demo index.html over the Python stdlib HTTP server.

Reuses the Module 3 Step 9 web-service pattern (http.server only, no third-party
frameworks). Binds to 127.0.0.1 (localhost) and serves only the local artifacts
in this directory. Nothing is exposed beyond the local machine.

Usage:
    python3 server.py            # serve on http://localhost:8080
    python3 server.py --port 9000
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

DEFAULT_PORT = 8080


def main(argv: list[str] | None = None) -> int:
    """Start the local static server. Returns 0 on clean shutdown."""
    parser = argparse.ArgumentParser(description="Serve the standalone demo locally.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (default 8080).")
    args = parser.parse_args(argv)

    directory = str(Path(__file__).resolve().parent)
    handler = partial(SimpleHTTPRequestHandler, directory=directory)
    # Bind to localhost only - serves local artifacts, not exposed to the network.
    httpd = HTTPServer(("127.0.0.1", args.port), handler)
    print(f"Serving standalone demo at http://localhost:{args.port} (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\nStopping server.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _build_write_html() -> str:
    """Assemble the generated write_html.py source with the embedded HTML.

    The HTML is embedded as an r-string literal so backslashes (e.g. the
    ellipsis escape) survive verbatim.

    Returns:
        The complete Python source for the generated write_html.py.
    """
    return _WRITE_HTML_HEADER + 'HTML = r"""' + _INDEX_HTML + '"""\n' + _WRITE_HTML_FOOTER


def _print_fallback(output_dir: Path, error: str) -> None:
    """Print Step-9-style manual fallback instructions (owed marker unchanged).

    Args:
        output_dir: The intended working directory for the demo artifacts.
        error: A short description of what failed.
    """
    print(f"Standalone demo generation failed: {error}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Fallback (manual) - the first-visualization obligation remains OWED,", file=sys.stderr)
    print("so the deferred guarantee (Module 6/7) still applies. To retry manually:",
          file=sys.stderr)
    print(f"  1. Ensure the directory exists: {output_dir}", file=sys.stderr)
    print("  2. Re-run: python3 scripts/generate_standalone_demo.py", file=sys.stderr)
    print("  3. Or serve an existing index.html with: python3 "
          f"{output_dir / 'server.py'}", file=sys.stderr)


def generate_demo(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    progress_path: str = DEFAULT_PROGRESS_PATH,
    port: int = DEFAULT_PORT,
) -> bool:
    """Generate the standalone demo artifacts and satisfy the owed marker.

    Writes ``write_html.py`` and ``server.py`` into *output_dir*, runs
    ``write_html.py`` to produce ``index.html``, and on success calls
    ``clear_first_visualization_owed(satisfied_by="standalone_demo")``.

    On any failure the owed marker is left unchanged and Step-9-style manual
    fallback instructions are printed.

    Args:
        output_dir: Working directory for the demo artifacts.
        progress_path: Path to the bootcamp progress file.
        port: Port the generated server will default to (for the printed hint).

    Returns:
        ``True`` when index.html was generated successfully, ``False`` otherwise.
    """
    out = Path(output_dir)
    try:
        out.mkdir(parents=True, exist_ok=True)

        write_html_path = out / "write_html.py"
        write_html_path.write_text(_build_write_html(), encoding="utf-8")

        server_path = out / "server.py"
        server_path.write_text(_SERVER_PY, encoding="utf-8")

        # Run the generator to produce index.html (mirrors the Step 9 flow).
        result = subprocess.run(
            [sys.executable, str(write_html_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        index_path = out / "index.html"
        if result.returncode != 0 or not index_path.is_file():
            _print_fallback(out, result.stderr.strip() or "index.html was not produced")
            return False
    except OSError as exc:
        _print_fallback(out, str(exc))
        return False

    # Success: satisfy the journey-level first-visualization obligation.
    clear_first_visualization_owed(satisfied_by="standalone_demo", progress_path=progress_path)

    print(f"Standalone demo generated in {out}")
    print(f"  - {out / 'write_html.py'}  (regenerate index.html)")
    print(f"  - {out / 'index.html'}     (single self-contained page, D3.js v7 CDN)")
    print(f"  - {out / 'server.py'}      (stdlib HTTP server, localhost only)")
    print("")
    print(f"Start it with: python3 {out / 'server.py'} --port {port}")
    print(f"Then open:     http://localhost:{port}")
    return True


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        ``0`` on successful generation, ``1`` on failure.
    """
    parser = argparse.ArgumentParser(
        description="Generate a minimal TruthSet-backed standalone entity-resolution demo."
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Working directory for demo artifacts (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--progress-path",
        default=DEFAULT_PROGRESS_PATH,
        help=f"Path to bootcamp progress file (default: {DEFAULT_PROGRESS_PATH}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port hint for the generated server (default: {DEFAULT_PORT}).",
    )
    args = parser.parse_args(argv)

    ok = generate_demo(
        output_dir=args.output_dir,
        progress_path=args.progress_path,
        port=args.port,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
