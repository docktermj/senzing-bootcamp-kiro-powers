# Implementation Plan

- [x] 1. Update visualization-guide.md with Visualization Prompt and expanded Web Server Guidance
  - [x] 1.1 Add Visualization Prompt as the first step in the Agent Workflow
    - Replace the current step 1 ("Confirm intent") with a new step 1 that presents the Visualization Prompt
    - The prompt must offer two options: Static HTML file and Web service
    - Include a WAIT instruction — agent must not proceed until the bootcamper responds
    - If no response, agent waits (does not default to either option)
    - After the prompt, add branching: if Static HTML is chosen, follow existing workflow; if Web Service is chosen, follow Web Server Guidance section
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.1, 5.4_

  - [x] 1.2 Expand the Web Server Guidance section with full endpoint specifications
    - Add `GET /entity/{entityId}` endpoint — queries SDK `get_entity_by_entity_id`, returns full resolved entity JSON
    - Add `GET /search` endpoint — accepts query parameters `name`, `address`, `phone`, `email` (at least one required), calls SDK `search_by_attributes`, returns matching entities as JSON
    - Retain existing endpoints (`GET /`, `GET /health`, `POST /refresh`)
    - Document response schemas for each endpoint (health check with `status` and `lastRefresh`, search with `results` array and `query` object, error with `error`, `code`, `detail`)
    - Document HTTP error status codes: 400 (invalid request), 404 (entity not found), 500 (SDK error), 503 (SDK not initialized)
    - Add localhost binding with configurable port, default 8080
    - Add port conflict error handling guidance
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.3, 3.4_

  - [x] 1.3 Add framework selection table and code generation instructions
    - Add framework selection table: Python/Flask, TypeScript/Express, Java/Javalin, Rust/Actix-web, C#/ASP.NET Minimal APIs
    - Add agent instruction to read Chosen_Language from `config/bootcamp_preferences.yaml`
    - Specify `src/server/` as the output directory for all generated server files
    - Add dependency file generation instructions with examples per language (`requirements.txt`, `package.json`, `pom.xml`, `Cargo.toml`, `.csproj`)
    - Add requirement for inline code comments explaining key sections
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 1.4 Add lifecycle management instructions to visualization-guide.md
    - Add start command instructions per language (e.g., `python src/server/server.py`, `npx ts-node src/server/server.ts`, etc.)
    - Add instruction for agent to tell bootcamper to open `http://localhost:8080` in their browser
    - Add stop instructions (Ctrl+C in the terminal)
    - Add troubleshooting guidance: missing dependencies, port conflicts, SDK not found, database not found
    - Add explicit prohibition: agent SHALL NOT start the server as a background process — must instruct bootcamper to run manually
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 1.5 Add feature parity and additional web service features documentation
    - Add section stating web service visualization must include all static HTML features: force layout, detail panel, cluster highlighting, search/filter, statistics
    - Document live entity detail fetching: clicking a node/row triggers `fetch('/entity/{entityId}')` and displays results in the detail panel
    - Document refresh button: calls `POST /refresh` and updates displayed data without full page reload
    - Add agent instruction to generate HTML with JavaScript `fetch()` calls instead of inline data when web service mode is selected
    - _Requirements: 7.1, 7.2, 7.3, 3.2_

- [x] 2. Update module-03-quick-demo.md with Visualization Prompt
  - [x] 2.1 Add Visualization Prompt to Phase 2 Step 5
    - In Phase 2 Step 5 ("Offer visualization"), add the Visualization Prompt before any visualization generation
    - The prompt must offer both Static HTML file and Web service options
    - Include a WAIT instruction after the prompt
    - If Static HTML is chosen, continue with existing workflow (generate `demo_results.html`)
    - If Web Service is chosen, load `visualization-guide.md` and follow Web Server Guidance
    - Preserve all existing Step 5 content (interactive feature options, file save location)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.2_

- [x] 3. Update module-08-query-validation.md with Visualization Prompt
  - [x] 3.1 Add Visualization Prompt to the entity graph offer section
    - In the "MANDATORY VISUALIZATION OFFER — ENTITY GRAPH" section, add the Visualization Prompt
    - The prompt must offer both Static HTML file and Web service options
    - Include a WAIT instruction after the prompt
    - If Static HTML is chosen, load `visualization-guide.md` and follow existing static workflow
    - If Web Service is chosen, load `visualization-guide.md` and follow Web Server Guidance
    - Preserve the mandatory offer enforcement (DO NOT SKIP, WAIT for response)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.3_

  - [x] 3.2 Add Visualization Prompt to the results dashboard offer section
    - In the "MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD" section, add the Visualization Prompt
    - The prompt must offer both Static HTML file and Web service options
    - Include a WAIT instruction after the prompt
    - If Static HTML is chosen, generate HTML dashboard as before (`docs/results_dashboard.html`)
    - If Web Service is chosen, load `visualization-guide.md` and follow Web Server Guidance
    - Preserve the mandatory offer enforcement (DO NOT SKIP, WAIT for response)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.3_

- [x] 4. Write structural validation tests
  - [x] 4.1 Write tests for visualization-guide.md Visualization Prompt and branching
    - Verify the Visualization Prompt appears as the first step in the Agent Workflow
    - Verify the prompt offers both "Static HTML" and "Web service" options
    - Verify a WAIT instruction follows the prompt
    - Verify branching logic exists: static HTML path and web service path
    - Verify the web service path directs to the Web Server Guidance section
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.1, 5.4_

  - [x] 4.2 Write tests for visualization-guide.md Web Server Guidance endpoints
    - Verify all five endpoints are documented: `GET /`, `GET /health`, `POST /refresh`, `GET /entity/{entityId}`, `GET /search`
    - Verify health check response schema includes `status` and `lastRefresh`
    - Verify error response schema includes `error`, `code`, and `detail`
    - Verify localhost binding with configurable port and 8080 default
    - Verify port conflict error handling is documented
    - Verify search endpoint documents query parameters (name, address, phone, email)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.3, 3.4_

  - [x] 4.3 Write tests for visualization-guide.md code generation and lifecycle
    - Verify framework selection table maps all five languages to frameworks
    - Verify `src/server/` is specified as the output directory
    - Verify dependency file generation is documented with per-language examples
    - Verify inline code comments requirement is documented
    - Verify start command instructions are provided
    - Verify browser URL instruction is included
    - Verify stop instructions (Ctrl+C) are included
    - Verify troubleshooting guidance exists for startup failures
    - Verify explicit prohibition against starting server as background process
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 4.4 Write tests for visualization-guide.md feature parity
    - Verify feature parity section lists all static HTML features (force layout, detail panel, cluster highlighting, search/filter, statistics)
    - Verify live entity detail fetching via `/entity/{entityId}` is documented
    - Verify refresh button calling `/refresh` without full page reload is documented
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 4.5 Write tests for module-03-quick-demo.md Visualization Prompt
    - Verify the Visualization Prompt appears in Phase 2 Step 5
    - Verify the prompt offers both static HTML and web service options
    - Verify a WAIT instruction follows the prompt
    - _Requirements: 5.2_

  - [x] 4.6 Write tests for module-08-query-validation.md Visualization Prompt
    - Verify the Visualization Prompt appears in the entity graph offer section
    - Verify the Visualization Prompt appears in the results dashboard offer section
    - Verify both prompts offer static HTML and web service options
    - Verify WAIT instructions follow both prompts
    - _Requirements: 5.3_

  - [x] 4.7 Write preservation tests
    - Verify existing Graph Data Model Schema in visualization-guide.md is preserved
    - Verify existing Visualization Feature Guidance is preserved
    - Verify existing Error Handling Guidance table is preserved
    - Verify Module 3 Phase 1 content is unchanged
    - Verify Module 8 content outside visualization offer sections is unchanged (query requirements, integration patterns, success criteria)
    - _Requirements: All (regression prevention)_

- [x] 5. Run all tests and verify no regressions
  - Run existing test suite (`senzing-bootcamp/tests/`) to confirm no regressions
  - Run new structural validation tests
  - Fix any failures before marking complete
  - _Requirements: All_
