# Requirements: MCP Health Check at Session Start

## Overview

The power has reactive MCP failure recovery but no proactive connectivity check. This feature adds a preflight MCP health check during session resume and onboarding so bootcampers know upfront whether the Senzing MCP server is reachable, rather than discovering failures mid-step.

## Requirements

1. During session resume (before Step 3 of session-resume.md), the agent attempts a lightweight MCP tool call (e.g., `search_docs(query="health check", version="current")`) to verify connectivity
2. During onboarding (before Step 1 of onboarding-flow.md), the same health check is performed
3. If the MCP server responds successfully, the agent proceeds normally with no additional output about the check
4. If the MCP server is unreachable or returns an error, the agent displays a clear warning: what failed, what features are unavailable (code generation, fact lookup, example search), and what the bootcamper can still do (review existing artifacts, work on documentation, plan next steps)
5. The health check result is stored transiently in `config/.mcp_status` (not committed to git) with fields: `last_check` (ISO 8601), `status` ("healthy" or "unreachable"), `error_message` (if any)
6. If the MCP server was unreachable at session start but the bootcamper wants to proceed, the agent re-checks before any step that requires MCP tools and reports recovery if connectivity is restored
7. The `preflight.py` script is extended with a `--mcp` flag that performs the same check from the command line, printing status and exit code (0 = healthy, 1 = unreachable)
8. The health check has a timeout of 10 seconds — if no response within 10 seconds, treat as unreachable
9. The warning message includes a link to `docs/guides/OFFLINE_MODE.md` for detailed offline capabilities
10. The `.mcp_status` file is added to `.gitignore`

## Non-Requirements

- This does not change MCP failure recovery behavior during module steps (that remains in mcp-failure-recovery.md)
- This does not block the bootcamper from proceeding — it's informational only
- This does not cache MCP responses or provide offline MCP emulation
