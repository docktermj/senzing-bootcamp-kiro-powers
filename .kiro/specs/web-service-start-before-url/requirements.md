# Bugfix Requirements Document

## Introduction

After building a web service (e.g., `server.py` + `graph.html`), the agent tells the bootcamper to "open http://localhost:8080" as if the service is already running. But the server was never started — the bootcamper gets a connection refused error if they try to visit the URL. The agent should either start the service or clearly state that the bootcamper needs to start it manually before visiting the URL.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent completes building a web service (server code + HTML) THEN the system presents the URL (e.g., "open http://localhost:8080") as if it's already accessible, without starting the server or instructing the bootcamper to start it first.

1.2 WHEN the bootcamper follows the agent's instruction to visit the URL THEN they get a connection refused error because no server is running.

1.3 WHEN the agent presents a URL without starting the server THEN the bootcamper's trust is broken — they expected the agent's instructions to work.

### Expected Behavior (Correct)

2.1 WHEN the agent completes building a web service THEN the system SHALL clearly present the start command BEFORE mentioning the URL, making it obvious the bootcamper needs to run the server first.

2.2 WHEN presenting a web service URL THEN the system SHALL always precede it with explicit instructions: (a) the exact command to start the server, (b) confirmation that the server must be running before the URL will work, and (c) how to stop the server when done.

2.3 THE system SHALL NEVER present a localhost URL as if it's already accessible when the server hasn't been started.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent generates static HTML files (not web services) THEN the system SHALL CONTINUE TO instruct the bootcamper to open the file directly — no server start instructions needed.

3.2 WHEN the agent provides external URLs (documentation links, etc.) THEN the system SHALL CONTINUE TO present them normally without server start instructions.

3.3 WHEN the web service code generation itself is in progress THEN the system SHALL CONTINUE TO complete the code generation before presenting any start/URL instructions.

## Acceptance Criteria

1. The `visualization-guide.md` steering file SHALL instruct the agent to always present the server start command BEFORE the URL when generating a web service visualization
2. The agent SHALL never say "open http://localhost:PORT" without first providing the command to start the server
3. The start instructions SHALL include: (a) the exact start command, (b) expected output confirming the server is running, and (c) only then the URL to visit
4. The instructions SHALL include how to stop the server (e.g., Ctrl+C)
5. The fix SHALL NOT change the behavior for static HTML file visualizations — those continue to be opened directly

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Agent claims web service is running without actually starting it"
- Module: 7 (Query and Visualize) | Priority: High | Category: UX
