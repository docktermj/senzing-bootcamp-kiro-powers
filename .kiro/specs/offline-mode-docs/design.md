# Design Document

## Overview

This feature creates a user-facing guide `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` that explains what bootcampers can do when the Senzing MCP server is unavailable. It also updates the guides README to list the new guide. The guide complements the agent-facing MCP failure details already in `steering/common-pitfalls.md` by providing a direct-to-user resource.

## Architecture

### Approach

Two files are modified/created:

1. **New file**: `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` — the standalone user-facing offline mode guide
2. **Modified file**: `senzing-bootcamp/docs/guides/README.md` — add entry for the new guide and update the documentation structure tree

### OFFLINE_MODE.md Structure

```markdown
# Offline Mode Guide
  (intro: what offline mode is, when it applies)

## What Works Without MCP
  (brief explanation of the two categories)

### Fully Offline Modules
  (table: Module 2, 3, parts of 4 — all activities work)

### Partially Blocked Modules
  (table: all other modules — which activities work, which need MCP)

## What to Do During an Outage
  (practical advice for bootcampers)

## Reconnecting
  (steps to restore connectivity)

## Agent Behavior During Outages
  (cross-reference to common-pitfalls.md, explanation that agent follows procedures)
```

### Content Details

**Module categorization** based on MCP tool dependencies from `common-pitfalls.md`:

| Module | Offline Status | Reason |
| ------ | -------------- | ------ |
| 2 (Business Problem) | Fully offline | No MCP tools needed — documentation and planning only |
| 3 (Data Collection) | Fully offline | File operations and documentation only |
| 4 (Data Quality) | Mostly offline | Manual profiling works; automated scoring via MCP is optional |
| 0 (SDK Setup) | Partially blocked | `generate_scaffold`, `get_sdk_reference` needed for setup code |
| 1 (Quick Demo) | Partially blocked | `generate_scaffold` needed for demo code |
| 5 (Data Mapping) | Partially blocked | `mapping_workflow` is core to this module |
| 6 (Single Source Loading) | Partially blocked | `generate_scaffold`, `get_sdk_reference` for loading code |
| 7 (Multi-Source) | Partially blocked | `mapping_workflow` for new sources; orchestration of existing code works |
| 8 (Query & Validation) | Partially blocked | `generate_scaffold`, `get_sdk_reference` for query code |
| 9-12 (Production) | Partially blocked | `search_docs`, `get_sdk_reference` for production guidance |

Key point: No module is fully blocked — all have some offline capability.

**Reconnection steps** for bootcampers:
1. Check basic network connectivity
2. Test MCP endpoint: `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443`
3. Check proxy settings (`HTTPS_PROXY` environment variable)
4. Restart MCP server connection in the IDE (Kiro Powers panel)
5. Ask the agent to retry
6. Contact support if issues persist

**README updates**:
- Add entry in the Troubleshooting section
- Add `OFFLINE_MODE.md` to the documentation structure tree

## Correctness Properties

Since this is a documentation-only change, correctness is verified by content checks:

1. **File exists**: `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` exists and is non-empty
2. **Fully offline modules listed**: The guide mentions Modules 2 and 3 as fully offline capable
3. **Partially blocked modules listed**: The guide mentions Modules 5, 6, and 8 as partially blocked with specific MCP tool dependencies
4. **No module fully blocked**: The guide states that no module is completely blocked
5. **Reconnection section present**: The guide contains reconnection steps including `mcp.senzing.com:443` and a connectivity test command
6. **Cross-reference present**: The guide references `common-pitfalls.md` for agent-specific fallback details
7. **README updated**: The guides README contains an entry for `OFFLINE_MODE.md`
8. **README tree updated**: The documentation structure tree in the README includes `OFFLINE_MODE.md`
