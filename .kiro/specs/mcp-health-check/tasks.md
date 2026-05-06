# Tasks: MCP Health Check at Session Start

## Task 1: Add MCP health check to session-resume.md

- [x] 1.1 Read the current `senzing-bootcamp/steering/session-resume.md` to identify the correct insertion point (between Step 2 and Step 3)
- [x] 1.2 Add "Step 2d: MCP Health Check" section with instructions for the agent to attempt a lightweight MCP tool call (`search_docs(query="health check", version="current")`) with a 10-second timeout
- [x] 1.3 Add success path: proceed silently, write `config/.mcp_status` with status "healthy"
- [x] 1.4 Add failure path: display warning message (unavailable features, available alternatives, link to OFFLINE_MODE.md), write `.mcp_status` with status "unreachable", ask 👉 question about continuing in offline mode
- [x] 1.5 Add mid-session recovery instruction: before any step requiring MCP tools, re-check if status was "unreachable" and report recovery if successful

## Task 2: Add MCP health check to onboarding-flow.md

- [x] 2.1 Read the current `senzing-bootcamp/steering/onboarding-flow.md` to identify the correct insertion point (before Step 1)
- [x] 2.2 Add "Step 0b: MCP Health Check" section with the same logic as session-resume (probe, success/failure paths)
- [x] 2.3 Ensure the onboarding warning message is appropriate for first-time users (explain what MCP provides in the bootcamp context)

## Task 3: Extend preflight.py with --mcp flag

- [x] 3.1 Read the current `senzing-bootcamp/scripts/preflight.py` to understand its argument structure
- [x] 3.2 Add `--mcp` flag to argparse that triggers an MCP connectivity check
- [x] 3.3 Implement the check: read `mcp.json` to find the server endpoint, attempt a basic connectivity test (or report that full MCP health requires the agent)
- [x] 3.4 Output format: server name, status (healthy/unreachable), response time or timeout duration
- [x] 3.5 Exit code: 0 for healthy, 1 for unreachable

## Task 4: Add .mcp_status to .gitignore

- [x] 4.1 Add `config/.mcp_status` to the project's `.gitignore` file

## Task 5: Write tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_mcp_health_check.py`
- [x] 5.2 Unit test: preflight.py accepts `--mcp` flag without error
- [x] 5.3 Steering structure test: session-resume.md contains "MCP Health Check" section
- [x] 5.4 Steering structure test: onboarding-flow.md contains "MCP Health Check" section
- [x] 5.5 Unit test: .mcp_status JSON schema validation (required fields: last_check, status, error_message)
- [x] 5.6 Unit test: warning message contains required elements (unavailable features, alternatives, OFFLINE_MODE.md reference)

## Task 6: Validate

- [x] 6.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified steering files
- [x] 6.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets
- [x] 6.3 Run `pytest senzing-bootcamp/tests/test_mcp_health_check.py -v`
