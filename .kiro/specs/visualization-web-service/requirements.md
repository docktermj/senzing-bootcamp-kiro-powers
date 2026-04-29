# Requirements Document

## Introduction

When the Senzing Bootcamp agent generates visualizations (demo results in Module 3, results dashboard and entity graph in Module 8), it currently always produces a static HTML file that the bootcamper opens directly in a browser. This feature adds a lightweight localhost web service as an alternative delivery mode. Before generating any visualization, the agent asks the bootcamper whether they want a static HTML file or a web service. The web service enables live SDK queries, dynamic data refresh, and richer interactive features such as clicking an entity to pull its full resolution details in real time.

## Glossary

- **Agent**: The AI agent running the Senzing Bootcamp, which generates code and guides the bootcamper through modules
- **Bootcamper**: The human user progressing through the Senzing Bootcamp
- **Visualization**: An HTML-based display of entity resolution results — includes demo results pages, results dashboards, and entity graph views
- **Static_HTML_File**: A self-contained HTML file with all data, styles, and scripts inline, opened directly in a browser with no server required
- **Web_Service**: A lightweight HTTP server running on localhost that serves visualization pages and exposes API endpoints for live Senzing SDK queries
- **Visualization_Prompt**: The question the agent asks the bootcamper to choose between a Static_HTML_File and a Web_Service before generating a visualization
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that the agent loads at runtime to guide its behavior during a specific module or workflow
- **SDK**: The Senzing SDK used to perform entity resolution, querying, and data retrieval
- **Chosen_Language**: The programming language the bootcamper selected for their project, stored in `config/bootcamp_preferences.yaml`

## Requirements

### Requirement 1: Visualization Delivery Choice

**User Story:** As a bootcamper, I want to choose between a static HTML file and a localhost web service before any visualization is generated, so that I get the delivery mode that best fits my needs.

#### Acceptance Criteria

1. WHEN the agent is about to generate a visualization, THE Agent SHALL present the Visualization_Prompt asking the bootcamper to choose between a Static_HTML_File and a Web_Service
2. WHEN the bootcamper selects the Static_HTML_File option, THE Agent SHALL generate a self-contained HTML file following the existing visualization workflow
3. WHEN the bootcamper selects the Web_Service option, THE Agent SHALL generate a localhost web service in the Chosen_Language
4. IF the bootcamper does not respond to the Visualization_Prompt, THEN THE Agent SHALL wait for a response before proceeding with visualization generation
5. THE Visualization_Prompt SHALL be presented in Module 3 (demo results), Module 8 (entity graph offer), and Module 8 (results dashboard offer)

### Requirement 2: Web Service Core Functionality

**User Story:** As a bootcamper, I want the web service to serve my visualization and provide live data endpoints, so that I can interact with resolved entities in real time.

#### Acceptance Criteria

1. THE Web_Service SHALL serve the visualization HTML page on the root endpoint (`GET /`)
2. THE Web_Service SHALL expose a health check endpoint (`GET /health`) that returns a JSON object containing the service status and last refresh timestamp
3. THE Web_Service SHALL expose a data refresh endpoint (`POST /refresh`) that re-queries the SDK and returns updated graph or dashboard data as JSON
4. THE Web_Service SHALL bind to `localhost` on a configurable port with a default of `8080`
5. IF the configured port is already in use, THEN THE Web_Service SHALL report a clear error message identifying the port conflict

### Requirement 3: Live Entity Detail Queries

**User Story:** As a bootcamper, I want to click an entity in the visualization and see its full resolution details fetched from the SDK in real time, so that I can explore entity data interactively without regenerating the entire page.

#### Acceptance Criteria

1. THE Web_Service SHALL expose an entity detail endpoint (`GET /entity/{entityId}`) that queries the SDK and returns the full resolved entity as JSON
2. WHEN the bootcamper clicks an entity node or row in the web-served visualization, THE visualization SHALL fetch entity details from the Web_Service entity detail endpoint and display them in a detail panel
3. THE Web_Service SHALL expose a search endpoint (`GET /search`) that accepts query parameters for name, address, phone, or email and returns matching entities as JSON
4. IF the SDK returns an error for an entity detail or search request, THEN THE Web_Service SHALL return an appropriate HTTP error status code and a JSON error message describing the failure

### Requirement 4: Web Service Code Generation

**User Story:** As a bootcamper, I want the web service code generated in my chosen programming language using familiar frameworks, so that I can understand, modify, and extend it.

#### Acceptance Criteria

1. THE Agent SHALL generate Web_Service code in the Chosen_Language stored in `config/bootcamp_preferences.yaml`
2. THE Agent SHALL use a lightweight, well-known HTTP framework appropriate for the Chosen_Language (e.g., Flask for Python, Express for TypeScript, Javalin for Java, Actix-web for Rust, ASP.NET Minimal APIs for C#)
3. THE Agent SHALL save Web_Service source files to `src/server/` within the project directory
4. THE Agent SHALL generate a dependency file listing all required packages for the Web_Service (e.g., `requirements.txt`, `package.json`, `pom.xml`, `Cargo.toml`, or `.csproj`)
5. THE Agent SHALL include inline code comments explaining key sections of the generated Web_Service code

### Requirement 5: Steering File Updates

**User Story:** As a power maintainer, I want the steering files updated to include the visualization delivery choice, so that the agent consistently offers both options at every visualization point.

#### Acceptance Criteria

1. THE Steering_File `visualization-guide.md` SHALL include the Visualization_Prompt as the first step before generating any visualization output
2. THE Steering_File `module-03-quick-demo.md` SHALL include the Visualization_Prompt in the "Offer visualization" step (Phase 2, Step 5)
3. THE Steering_File `module-08-query-validation.md` SHALL include the Visualization_Prompt in both the entity graph offer and the results dashboard offer
4. WHEN the bootcamper chooses the Web_Service option, THE Steering_File `visualization-guide.md` SHALL direct the agent to follow the Web Server Guidance section instead of generating a static file

### Requirement 6: Web Service Lifecycle Management

**User Story:** As a bootcamper, I want clear instructions for starting, stopping, and verifying the web service, so that I can manage it without confusion.

#### Acceptance Criteria

1. WHEN the Web_Service code is generated, THE Agent SHALL provide the bootcamper with the exact command to start the Web_Service
2. WHEN the Web_Service starts successfully, THE Agent SHALL instruct the bootcamper to open the visualization URL in their browser
3. THE Agent SHALL provide the bootcamper with instructions for stopping the Web_Service (e.g., Ctrl+C in the terminal)
4. IF the Web_Service fails to start, THEN THE Agent SHALL diagnose the error and suggest corrective steps (e.g., install missing dependencies, resolve port conflicts)
5. THE Agent SHALL NOT start the Web_Service as a background process within the IDE — the Agent SHALL instruct the bootcamper to run the start command manually in their terminal

### Requirement 7: Consistent Visualization Features

**User Story:** As a bootcamper, I want the web-served visualization to include the same interactive features as the static HTML version, so that choosing the web service does not reduce functionality.

#### Acceptance Criteria

1. THE Web_Service visualization SHALL include all features available in the Static_HTML_File version (force layout, detail panel, cluster highlighting, search and filter, statistics)
2. THE Web_Service visualization SHALL additionally support live entity detail fetching via the entity detail endpoint when a node or row is clicked
3. THE Web_Service visualization SHALL additionally support a refresh button that calls the `/refresh` endpoint and updates the displayed data without a full page reload
