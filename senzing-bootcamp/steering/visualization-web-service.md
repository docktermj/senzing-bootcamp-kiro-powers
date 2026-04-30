---
inclusion: manual
---

# Visualization Web Service Guidance

Endpoint specs, framework selection, code generation, lifecycle, and feature parity for the web service delivery mode. Loaded on demand from `visualization-guide.md`.

## Endpoint Specifications

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/` | GET | Serve visualization HTML page | HTML |
| `/health` | GET | Health check with last refresh time | `{ "status": "ok", "lastRefresh": "<ISO 8601>" }` |
| `/refresh` | POST | Re-query SDK, return updated graph/dashboard data | Graph/dashboard JSON (see Graph Data Model Schema) |
| `/entity/{entityId}` | GET | Fetch full resolved entity details from SDK | Full resolved entity JSON via `get_entity_by_entity_id` |
| `/search` | GET | Search entities by attributes | `{ "results": [...], "query": {...} }` |

**Health Check Response (`GET /health`):**

```json
{
  "status": "ok",
  "lastRefresh": "2026-04-14T12:30:00Z"
}
```

**Entity Detail Response (`GET /entity/{entityId}`):**
The response is the full resolved entity JSON as returned by the Senzing SDK's `get_entity_by_entity_id` method. The server passes through the SDK response without transformation.

**Search Response (`GET /search`):**
Query parameters: `name`, `address`, `phone`, `email` — at least one required. Calls SDK `search_by_attributes` and returns matching entities.

```json
{
  "results": [
    {
      "entityId": 1,
      "primaryName": "John Smith",
      "recordCount": 3,
      "dataSources": ["CUSTOMERS", "CRM"],
      "matchScore": 95
    }
  ],
  "query": {
    "name": "John Smith",
    "address": null,
    "phone": null,
    "email": null
  }
}
```

**Error Response (all endpoints):**

```json
{
  "error": "Entity not found",
  "code": 404,
  "detail": "No entity exists with ID 99999"
}
```

## HTTP Error Status Codes

| Status Code | Meaning |
|-------------|---------|
| `400` | Invalid request — missing required parameters, invalid entity ID format |
| `404` | Entity not found |
| `500` | SDK error or internal server error |
| `503` | SDK not initialized or database not found |

## Server Binding

The web service binds to `localhost` on a configurable port (default `8080`). If the port is in use, report a clear error identifying the conflict and suggest an alternative port.

## Framework Selection

> **Agent instruction:** Read Chosen_Language from `config/bootcamp_preferences.yaml`. Select the framework from the table below.

| Chosen_Language | Framework | Rationale |
|-----------------|-----------|-----------|
| Python | Flask | Lightweight, well-known, minimal boilerplate |
| TypeScript | Express | De facto standard for Node.js HTTP servers |
| Java | Javalin | Lightweight, minimal config, Kotlin-friendly |
| Rust | Actix-web | High performance, well-documented, async |
| C# | ASP.NET Minimal APIs | Built-in, no extra dependencies, concise |

## Code Generation Instructions

> **Agent instruction:** Use `generate_scaffold` with the chosen language/framework. Save all generated server files to `src/server/`. The server entry point should be `src/server/server.[ext]`. The visualization HTML should be `src/server/index.html` or `src/server/static/index.html`. Container deployment → generate `src/server/Dockerfile`.

- All generated server code MUST include inline code comments explaining key sections (SDK initialization, endpoint handlers, error handling, data extraction).
- Generate a dependency file in the project root listing all required packages:
  - Python: `requirements.txt` (e.g., `flask>=3.0`)
  - TypeScript: `package.json` (e.g., `express`, `@types/express`)
  - Java: `pom.xml` (e.g., Javalin dependency)
  - Rust: `Cargo.toml` (e.g., `actix-web`)
  - C#: `.csproj` (e.g., ASP.NET Minimal APIs)

## Lifecycle Management

**Starting the server:**

Provide the bootcamper with the exact start command for their chosen language:

| Language | Start Command |
|----------|---------------|
| Python | `python src/server/server.py` |
| TypeScript | `npx ts-node src/server/server.ts` |
| Java | `mvn exec:java -Dexec.mainClass="server.Server"` |
| Rust | `cargo run --bin server` |
| C# | `dotnet run --project src/server/` |

**After the server starts:**

👉 "Open `http://localhost:8080` in your browser to view the visualization."

**Stopping the server:**
👉 "Press Ctrl+C in the terminal to stop the server."

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| Missing dependencies | Install dependencies: `pip install -r requirements.txt`, `npm install`, `mvn install`, `cargo build`, or `dotnet restore` |
| Port conflict (port already in use) | Kill the process using the port or change the port in the server config |
| SDK not found / not initialized | Ensure Senzing SDK is installed (Module 2) and database exists at `database/G2C.db` |
| Database not found | Complete Module 5 first to create and populate the database |
| Server crashes during use | Check terminal output for error details, restart with the start command |
| Cannot access URL | Verify server is running, check port number, try `localhost` vs `127.0.0.1` |

**⚠️ IMPORTANT:** The agent SHALL NOT start the server as a background process within the IDE. The agent MUST instruct the bootcamper to run the start command manually in their terminal. No server requested → produce only the self-contained HTML file.

## Web Service Feature Parity

When the bootcamper chooses the web service delivery mode, the generated visualization MUST include all features available in the static HTML version:

- **Force layout** — D3.js v7 force simulation with drag, zoom, pan
- **Detail panel** — click node/row to view entity details
- **Cluster highlighting** — data source coloring, match strength coloring
- **Search & filter** — text input filtering by name or record ID
- **Statistics** — total entities, records, relationships, cross-source match rate

**Additional web service features (beyond static HTML):**

- **Live entity detail fetching:** Clicking a node or row triggers `fetch('/entity/{entityId}')` and displays the full resolved entity details in the detail panel, fetched live from the SDK.
- **Refresh button:** A refresh button calls `POST /refresh` and updates the displayed data without a full page reload.

> **Agent instruction:** When generating the web service visualization HTML, use JavaScript `fetch()` calls to the server endpoints instead of inline data. On page load, fetch initial data from `/refresh`. Entity clicks trigger `/entity/{entityId}`. The refresh button calls `/refresh`.
