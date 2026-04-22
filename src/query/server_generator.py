"""Web server application generator for Senzing entity graph visualization.

Generates a deployable web server application (Flask or FastAPI) that serves
the same interactive graph visualization as the static HTML, with live data
refresh endpoints.
"""

from __future__ import annotations

import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Framework templates
# ---------------------------------------------------------------------------

_FLASK_APP_TEMPLATE = textwrap.dedent("""\
    \"\"\"Flask server for Senzing entity graph visualization.

    Serves the interactive graph at / and provides
    health and refresh endpoints.
    \"\"\"

    import datetime
    import json
    import logging
    import sys
    from pathlib import Path

    from flask import Flask, Response, jsonify

    app = Flask(__name__)
    logger = logging.getLogger(__name__)

    # --- State ---
    _last_refresh: str = datetime.datetime.now(
        datetime.timezone.utc,
    ).isoformat()
    _cached_html: str | None = None
    DATA_SOURCE: str = "{data_source}"


    # --- Senzing helpers ---

    def _init_engine():
        \"\"\"Initialize the Senzing SDK engine.\"\"\"
        db_path = Path("database/G2C.db")
        if not db_path.is_file():
            logger.error(
                "Senzing database not found at database/G2C.db. "
                "Please load data before starting the server.",
            )
            sys.exit(1)

        try:
            import senzing
        except ImportError:
            logger.error(
                "Senzing SDK is not installed. "
                "Please install the senzing package.",
            )
            sys.exit(1)

        try:
            engine = senzing.G2Engine()
            ini_params = json.dumps({{
                "PIPELINE": {{
                    "CONFIGPATH": str(db_path.resolve().parent),
                    "SUPPORTPATH": str(db_path.resolve().parent),
                    "RESOURCEPATH": str(db_path.resolve().parent),
                }},
                "SQL": {{
                    "CONNECTION": f"sqlite3://na:na@{{db_path.resolve()}}",
                }},
            }})
            engine.init("visualization_server", ini_params, 0)
            return engine
        except Exception as exc:
            logger.error("Failed to initialize Senzing engine: %s", exc)
            sys.exit(1)


    def _generate_html() -> str:
        \"\"\"Generate visualization HTML via Senzing SDK.\"\"\"
        # Import the visualization generator modules
        # Adjust imports based on your project structure
        from src.query.generate_visualization import (
            assemble_graph_data,
            extract_entities,
            extract_relationships,
            load_d3_source,
            render_html,
        )
        from src.query.renderer_css import RENDERER_CSS
        from src.query.renderer_js import RENDERER_JS

        engine = _init_engine()
        try:
            entities = extract_entities(engine, DATA_SOURCE, limit=None)
            entity_ids = [e.entity_id for e in entities]
            relationships = extract_relationships(engine, entity_ids)
            graph_data = assemble_graph_data(
                entities, relationships, DATA_SOURCE,
            )
            d3_source = load_d3_source()
            return render_html(
                graph_data, d3_source, RENDERER_CSS, RENDERER_JS,
            )
        finally:
            try:
                engine.destroy()
            except Exception:
                pass


    # --- Routes ---

    @app.route("/")
    def index():
        \"\"\"Serve the interactive graph visualization.\"\"\"
        global _cached_html
        if _cached_html is None:
            _cached_html = _generate_html()
        return Response(_cached_html, mimetype="text/html")


    @app.route("/health", methods=["GET"])
    def health():
        \"\"\"Return server health status.\"\"\"
        return jsonify({{
            "status": "ok",
            "lastRefresh": _last_refresh,
        }})


    @app.route("/refresh", methods=["POST"])
    def refresh():
        \"\"\"Re-query the Senzing SDK and regenerate graph data.\"\"\"
        global _cached_html, _last_refresh
        try:
            _cached_html = _generate_html()
            _last_refresh = datetime.datetime.now(
                datetime.timezone.utc,
            ).isoformat()
            return jsonify({{
                "status": "ok",
                "lastRefresh": _last_refresh,
            }})
        except Exception as exc:
            logger.exception("Failed to refresh visualization data")
            return jsonify({{
                "status": "error",
                "message": str(exc),
            }}), 500


    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)
""")

_FASTAPI_APP_TEMPLATE = textwrap.dedent("""\
    \"\"\"FastAPI server for Senzing entity graph visualization.

    Serves the interactive graph at / and provides
    health and refresh endpoints.
    \"\"\"

    import datetime
    import json
    import logging
    import sys
    from pathlib import Path

    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse

    app = FastAPI(title="Senzing Entity Graph Visualization")
    logger = logging.getLogger(__name__)

    # --- State ---
    _last_refresh: str = datetime.datetime.now(
        datetime.timezone.utc,
    ).isoformat()
    _cached_html: str | None = None
    DATA_SOURCE: str = "{data_source}"


    # --- Senzing helpers ---

    def _init_engine():
        \"\"\"Initialize the Senzing SDK engine.\"\"\"
        db_path = Path("database/G2C.db")
        if not db_path.is_file():
            logger.error(
                "Senzing database not found at database/G2C.db. "
                "Please load data before starting the server.",
            )
            sys.exit(1)

        try:
            import senzing
        except ImportError:
            logger.error(
                "Senzing SDK is not installed. "
                "Please install the senzing package.",
            )
            sys.exit(1)

        try:
            engine = senzing.G2Engine()
            ini_params = json.dumps({{
                "PIPELINE": {{
                    "CONFIGPATH": str(db_path.resolve().parent),
                    "SUPPORTPATH": str(db_path.resolve().parent),
                    "RESOURCEPATH": str(db_path.resolve().parent),
                }},
                "SQL": {{
                    "CONNECTION": f"sqlite3://na:na@{{db_path.resolve()}}",
                }},
            }})
            engine.init("visualization_server", ini_params, 0)
            return engine
        except Exception as exc:
            logger.error("Failed to initialize Senzing engine: %s", exc)
            sys.exit(1)


    def _generate_html() -> str:
        \"\"\"Generate visualization HTML via Senzing SDK.\"\"\"
        from src.query.generate_visualization import (
            assemble_graph_data,
            extract_entities,
            extract_relationships,
            load_d3_source,
            render_html,
        )
        from src.query.renderer_css import RENDERER_CSS
        from src.query.renderer_js import RENDERER_JS

        engine = _init_engine()
        try:
            entities = extract_entities(engine, DATA_SOURCE, limit=None)
            entity_ids = [e.entity_id for e in entities]
            relationships = extract_relationships(engine, entity_ids)
            graph_data = assemble_graph_data(
                entities, relationships, DATA_SOURCE,
            )
            d3_source = load_d3_source()
            return render_html(
                graph_data, d3_source, RENDERER_CSS, RENDERER_JS,
            )
        finally:
            try:
                engine.destroy()
            except Exception:
                pass


    # --- Routes ---

    @app.get("/", response_class=HTMLResponse)
    async def index():
        \"\"\"Serve the interactive graph visualization.\"\"\"
        global _cached_html
        if _cached_html is None:
            _cached_html = _generate_html()
        return HTMLResponse(content=_cached_html)


    @app.get("/health")
    async def health():
        \"\"\"Return server health status.\"\"\"
        return {{
            "status": "ok",
            "lastRefresh": _last_refresh,
        }}


    @app.post("/refresh")
    async def refresh():
        \"\"\"Re-query the Senzing SDK and regenerate graph data.\"\"\"
        global _cached_html, _last_refresh
        try:
            _cached_html = _generate_html()
            _last_refresh = datetime.datetime.now(
                datetime.timezone.utc,
            ).isoformat()
            return {{
                "status": "ok",
                "lastRefresh": _last_refresh,
            }}
        except Exception as exc:
            logger.exception("Failed to refresh visualization data")
            return JSONResponse(
                status_code=500,
                content={{
                    "status": "error",
                    "message": str(exc),
                }},
            )


    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
""")

# ---------------------------------------------------------------------------
# Requirements templates
# ---------------------------------------------------------------------------

_FLASK_REQUIREMENTS = """\
flask>=3.0.0
senzing
"""

_FASTAPI_REQUIREMENTS = """\
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
senzing
"""

# ---------------------------------------------------------------------------
# Dockerfile templates
# ---------------------------------------------------------------------------

_FLASK_DOCKERFILE = textwrap.dedent("""\
    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 5000

    CMD ["python", "app.py"]
""")

_FASTAPI_DOCKERFILE = textwrap.dedent("""\
    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 8000

    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
""")

# ---------------------------------------------------------------------------
# Supported frameworks registry
# ---------------------------------------------------------------------------

_FRAMEWORKS: dict[str, dict] = {
    "flask": {
        "app_template": _FLASK_APP_TEMPLATE,
        "requirements": _FLASK_REQUIREMENTS,
        "dockerfile": _FLASK_DOCKERFILE,
        "app_filename": "app.py",
    },
    "fastapi": {
        "app_template": _FASTAPI_APP_TEMPLATE,
        "requirements": _FASTAPI_REQUIREMENTS,
        "dockerfile": _FASTAPI_DOCKERFILE,
        "app_filename": "app.py",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_server(
    framework: str,
    output_dir: str,
    data_source: str,
) -> None:
    """Generate a deployable web server application for the visualization.

    Parameters
    ----------
    framework:
        The web framework to use. Must be ``"flask"`` or ``"fastapi"``.
    output_dir:
        Directory where the server files will be written.
    data_source:
        The Senzing data source name (e.g. ``"CUSTOMERS"``).

    Raises
    ------
    ValueError
        If *framework* is not one of the supported frameworks.
    """
    fw_key = framework.lower().strip()
    if fw_key not in _FRAMEWORKS:
        supported = ", ".join(sorted(_FRAMEWORKS))
        raise ValueError(
            f"Unsupported framework '{framework}'. "
            f"Supported frameworks: {supported}"
        )

    fw = _FRAMEWORKS[fw_key]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Generate the application file
    app_content = fw["app_template"].format(data_source=data_source)
    app_path = out / fw["app_filename"]
    app_path.write_text(app_content, encoding="utf-8")

    # Generate requirements.txt
    req_path = out / "requirements.txt"
    req_path.write_text(fw["requirements"], encoding="utf-8")

    # Generate Dockerfile
    dockerfile_path = out / "Dockerfile"
    dockerfile_path.write_text(fw["dockerfile"], encoding="utf-8")

    app_name = fw["app_filename"]
    print(f"Generated {fw_key} server in {out}/")
    print(f"  - {app_name}")
    print("  - requirements.txt")
    print("  - Dockerfile")
    print()
    print("To run the server:")
    print(f"  cd {out}")
    print("  pip install -r requirements.txt")
    if fw_key == "flask":
        print("  python app.py")
    else:
        print("  uvicorn app:app --host 0.0.0.0 --port 8000")
    print()
    print("To build and run with Docker:")
    print(f"  cd {out}")
    print(f"  docker build -t senzing-viz-{fw_key} .")
    if fw_key == "flask":
        print(f"  docker run -p 5000:5000 senzing-viz-{fw_key}")
    else:
        print(f"  docker run -p 8000:8000 senzing-viz-{fw_key}")
