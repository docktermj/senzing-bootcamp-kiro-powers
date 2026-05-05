# Implementation Plan: Web Service Start Before URL

## Overview

Add explicit sequencing instructions to ensure the agent always presents the server start command before any localhost URL when delivering a web service visualization.

## Tasks

- [x] 1. Add Web Service Delivery Sequence to visualization-guide.md
  - [x] 1.1 Locate the Web Server Guidance section in `senzing-bootcamp/steering/visualization-guide.md`
  - [x] 1.2 Add a "Web Service Delivery Sequence" instruction block that enforces this order:
    - Step 1: Present the start command
    - Step 2: Describe expected output confirming the server is running
    - Step 3: Only then present the URL to open in the browser
    - Step 4: Provide stop instructions (Ctrl+C)
    - Include explicit prohibition: "NEVER present a localhost URL as if it's already accessible. The server must be started first."
    - _Requirements: 1, 2, 3, 4_

- [x] 2. Verify module-07 steering consistency
  - [x] 2.1 Check `senzing-bootcamp/steering/module-07-query-validation.md` for any web service delivery instructions
  - [x] 2.2 If present, add a reference to the Web Service Delivery Sequence or inline the same rule
    - _Requirements: 2_

- [x] 3. Verify static HTML is unaffected
  - [x] 3.1 Confirm the visualization-guide.md still has separate instructions for static HTML file delivery that do NOT include server start steps
    - _Requirements: 5_

- [x] 4. Final verification
  - Confirm the delivery sequence is present and correctly ordered
  - Confirm the prohibition against presenting URLs without start commands is explicit
  - Confirm static HTML delivery path is unchanged
  - Run any existing steering validation scripts

## Notes

- This fix complements the visualization-web-service spec which defines the web service feature itself — this spec fixes the delivery UX
- No Python code changes — only steering markdown edits
- The fix applies to all web service visualizations regardless of module (Module 3, 7, 8)
