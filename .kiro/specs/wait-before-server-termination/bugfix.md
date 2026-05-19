# Bugfix Requirements Document

## Introduction

After presenting the web visualization URL (http://localhost:8080/) in Module 3 Step 9, the agent immediately proceeds to Step 11 (Cleanup) and terminates the web server without giving the bootcamper a chance to open and explore the visualization in their browser. This defeats the purpose of the visualization — the bootcamper's "wow moment" — because the server is killed before they can interact with it. The fix ensures the agent always asks the bootcamper to confirm they've finished exploring before terminating any web service.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent completes Step 9 (web service verification) and Step 10 (report generation) THEN the system immediately proceeds to Step 11 and terminates the web server process without asking the bootcamper if they have finished exploring the visualization

1.2 WHEN the agent reaches Step 11 cleanup instructions THEN the system sends a termination signal to the web service process without any prior user confirmation prompt

1.3 WHEN the bootcamper has not yet opened the visualization URL in their browser THEN the system terminates the server anyway, making the visualization inaccessible

### Expected Behavior (Correct)

2.1 WHEN the agent completes Step 9 (web service verification) and Step 10 (report generation) and is about to proceed to Step 11 cleanup THEN the system SHALL ask the bootcamper to confirm they have finished exploring the visualization before terminating the web server

2.2 WHEN the agent is about to terminate any web service process started for the bootcamper THEN the system SHALL first present a confirmation prompt (e.g., "👉 Have you finished exploring the visualization? Let me know when you're ready and I'll clean up the server.") and wait for the bootcamper's affirmative response

2.3 WHEN the bootcamper has not yet confirmed they are finished exploring THEN the system SHALL keep the web server running and not proceed with cleanup until confirmation is received

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper confirms they have finished exploring the visualization THEN the system SHALL CONTINUE TO terminate the web service process and proceed with database purge cleanup as defined in Step 11

3.2 WHEN the web service process fails to terminate within 5 seconds after the bootcamper confirms THEN the system SHALL CONTINUE TO force-stop the process and display a warning about manual port release

3.3 WHEN the bootcamper explicitly skips Step 9 via the skip-step protocol THEN the system SHALL CONTINUE TO proceed to cleanup without a visualization confirmation prompt (since no server was started)

3.4 WHEN the agent starts the web server in Step 9 and presents the URL THEN the system SHALL CONTINUE TO verify endpoints, write checkpoints, and present the URL with manual restart and stop instructions as currently defined

3.5 WHEN all verification checks pass and cleanup completes THEN the system SHALL CONTINUE TO generate the module completion journal entry and transition to Module 4 as currently defined
