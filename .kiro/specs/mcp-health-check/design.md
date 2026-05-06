# Design: MCP Health Check at Session Start

## Overview

A proactive MCP connectivity check runs during session resume and onboarding, before the bootcamper encounters a step that requires MCP tools. If the server is unreachable, the bootcamper gets a clear warning with available alternatives.

## Health Check Mechanism

The agent performs a lightweight MCP tool call as a connectivity probe:

```console
search_docs(query="health check", version="current")
```

This is chosen because:

- It's read-only (no side effects)
- It exercises the full MCP request/response path
- A successful response (even empty results) confirms connectivity
- Timeout after 10 seconds indicates unreachable

## Status File

```json
// config/.mcp_status (transient, gitignored)
{
  "last_check": "2026-05-06T14:30:00Z",
  "status": "healthy",
  "error_message": null
}
```

States: `"healthy"` or `"unreachable"`.

## Integration Points

### Session Resume (session-resume.md)

Insert between Step 2 (Load Language Steering) and Step 3 (Summarize and Confirm):

- "Step 2d: MCP Health Check — attempt `search_docs` probe. If successful, proceed silently. If unreachable, display warning and offer alternatives."

### Onboarding (onboarding-flow.md)

Insert before Step 1 (Welcome):

- "Step 0b: MCP Health Check — same logic as session resume."

### Mid-Session Recovery

If MCP was unreachable at start but bootcamper proceeds:

- Before any step that calls MCP tools, re-check connectivity
- If recovered, display: "✅ MCP server is back online — full functionality restored."
- Write updated status to `.mcp_status`

## Warning Message Format

```console
⚠️ The Senzing MCP server is currently unreachable.

**What's unavailable**: Code generation, fact lookup, example search
**What you can still do**: Review existing artifacts, work on documentation, plan next steps

For detailed offline capabilities, see docs/guides/OFFLINE_MODE.md

👉 Would you like to continue in offline mode, or try again later?
```

## preflight.py Extension

```console
$ python preflight.py --mcp
MCP Server: mcp.senzing.com
Status: healthy (responded in 1.2s)
Exit code: 0

$ python preflight.py --mcp
MCP Server: mcp.senzing.com
Status: unreachable (timeout after 10s)
Exit code: 1
```

Note: `preflight.py` cannot actually call MCP tools (it's a CLI script, not an agent). The `--mcp` flag will attempt an HTTP connectivity check to the MCP server endpoint if the URL is discoverable from `mcp.json`, or report that MCP health can only be verified by the agent.

## Files Modified

- `senzing-bootcamp/steering/session-resume.md` — add Step 2d
- `senzing-bootcamp/steering/onboarding-flow.md` — add Step 0b
- `senzing-bootcamp/scripts/preflight.py` — add `--mcp` flag
- `.gitignore` — add `config/.mcp_status`

## Testing

- Unit test: preflight.py `--mcp` flag is accepted by argparse
- Unit test: .mcp_status file format validation
- Steering structure test: session-resume.md contains MCP health check step
- Steering structure test: onboarding-flow.md contains MCP health check step
