# Bugfix Design: Web Service Start Before URL

## Overview

This fix ensures the agent never presents a localhost URL as accessible without first providing the server start command. The root cause is that the visualization steering file doesn't enforce a strict ordering: start command → expected output → URL. The fix adds explicit sequencing instructions to the visualization guide and the module-07 steering.

## Bug Details

### Bug Condition

The bug manifests when the agent completes building a web service (server code + HTML) and immediately tells the bootcamper to "open http://localhost:8080" without starting the server or instructing the bootcamper to start it first. The bootcamper gets a connection refused error.

### Root Cause

1. **Missing sequencing rule**: The `visualization-guide.md` steering file describes web service generation but doesn't enforce a strict presentation order: (1) start command, (2) expected output, (3) URL.
2. **No "server not running" awareness**: The agent doesn't distinguish between "code exists" and "server is running." It treats code generation completion as equivalent to the service being available.
3. **No explicit lifecycle instructions**: The steering doesn't require the agent to present lifecycle management (start, verify, stop) as part of the web service delivery.

## Expected Behavior

When the agent completes building a web service, it must present in this exact order:
1. The exact command to start the server (e.g., `python src/server/server.py`)
2. What the bootcamper should see when the server starts successfully (e.g., "Server running on http://localhost:8080")
3. Only then: "Open http://localhost:8080 in your browser"
4. How to stop the server when done (e.g., "Press Ctrl+C in the terminal to stop")

The agent must NEVER say "open http://localhost:PORT" without first providing the start command.

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/steering/visualization-guide.md`

**Section**: Web Server Guidance (or equivalent section for web service delivery)

**Specific Changes**:

1. Add a "Web Service Delivery Sequence" instruction block:
   ```
   When presenting a completed web service to the bootcamper, ALWAYS follow this exact sequence:
   1. Present the start command: "Run this command to start the server: `<command>`"
   2. Describe expected output: "You should see: 'Server running on http://localhost:<port>'"
   3. Only AFTER steps 1-2: "Then open http://localhost:<port> in your browser"
   4. Provide stop instructions: "When you're done, press Ctrl+C in the terminal to stop the server"
   
   NEVER present a localhost URL as if it's already accessible. The server must be started first.
   ```

---

**File**: `senzing-bootcamp/steering/module-07-query-validation.md` (if it contains web service delivery instructions)

**Specific Changes**:

1. Add reference to the Web Service Delivery Sequence from visualization-guide.md, or inline the same sequencing rule if the module has its own web service delivery section.

## Testing Strategy

- Verify that `visualization-guide.md` contains the Web Service Delivery Sequence instruction
- Verify the sequence explicitly requires the start command BEFORE the URL
- Verify the sequence includes expected output and stop instructions
- Verify the rule explicitly prohibits presenting a URL without the start command
- Verify static HTML file delivery is not affected (no server start needed for static files)
