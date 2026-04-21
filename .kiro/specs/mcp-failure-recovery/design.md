# Design Document

## Overview

This feature expands the "MCP Server Unavailable" section in `senzing-bootcamp/steering/common-pitfalls.md` to provide the AI agent with detailed, actionable guidance during MCP outages. The existing section will be replaced in-place with a comprehensive version that categorizes operations by MCP dependency, provides per-operation fallback instructions, and includes reconnection procedures.

## Architecture

### Approach

This is a content-only change to a single steering file. The approach is:

1. Identify the exact boundaries of the existing "MCP Server Unavailable" section in `common-pitfalls.md`
2. Replace that section with an expanded version containing:
   - A structured "Blocked Operations" table with MCP tool names, affected modules, and fallback instructions
   - A structured "Continuable Operations" table grouped by work type with explanations
   - A "Reconnection Procedure" subsection with step-by-step recovery instructions
   - A "Connectivity Troubleshooting" subsection for common network issues
3. Preserve all content before and after the MCP section exactly as-is

### File Modified

- `senzing-bootcamp/steering/common-pitfalls.md` — expand the "MCP Server Unavailable" section

### Section Structure

The expanded section will follow this structure:

```
## MCP Server Unavailable — What You Can Still Do
  (intro paragraph — updated)

### Blocked Operations (Require MCP)
  (table: Operation | MCP Tool | Affected Modules | Fallback)

### Continuable Operations (No MCP Needed)
  #### Data Preparation
  #### Documentation & Review
  #### Code & Infrastructure Maintenance
  (tables per group: Activity | Modules | What to do)

### Fallback Instructions by Operation
  (detailed per-operation fallback steps)

### What to Tell the Bootcamper
  (agent script template — updated)

### Reconnection Procedure
  (step-by-step reconnection flow)

### Connectivity Troubleshooting
  (common network/proxy fixes)
```

### Content Details

**Blocked Operations Table** will include these five entries:
| Operation | MCP Tool | Modules | Fallback |
|---|---|---|---|
| Attribute mapping | `mapping_workflow` | 5, 7 | Refer to docs.senzing.com entity specification; check `docs/mapping_*.md` |
| Code generation | `generate_scaffold` | 0, 1, 6, 8 | Check `src/` for existing scaffold; adapt previously generated code |
| Error diagnosis | `explain_error_code` | Any | Note error code; check docs.senzing.com; email support@senzing.com |
| SDK reference lookup | `get_sdk_reference` | 0, 6, 8 | Browse docs.senzing.com SDK docs; check `src/` for usage patterns |
| Documentation search | `search_docs` | Any | Browse docs.senzing.com directly |

**Continuable Operations** grouped into three categories:
- Data Preparation: data collection, file operations, manual data profiling
- Documentation & Review: writing docs, journal entries, code review
- Code & Infrastructure: project structure setup, backup/restore, running existing programs, git operations

**Reconnection Procedure** will include:
1. Retry MCP call after initial failure (already in agent-instructions.md)
2. If still failing, enter offline mode using this section
3. Retry every ~10 minutes or when bootcamper requests
4. On success, call `get_capabilities` to verify full functionality
5. Inform bootcamper and list previously blocked operations that can resume

**Connectivity Troubleshooting** will cover:
- Corporate proxy: allowlist `mcp.senzing.com:443`, set `HTTPS_PROXY`
- Network verification: test connectivity to MCP endpoint
- MCP restart: restart the MCP server connection in the IDE

## Correctness Properties

Since this is a markdown content change (not code), correctness is verified by checking the output file contains required content markers. These are all example-based checks:

1. **Blocked operations present**: The file contains all five blocked operation entries with their MCP tool names (`mapping_workflow`, `generate_scaffold`, `explain_error_code`, `get_sdk_reference`, `search_docs`)
2. **Continuable operations present**: The file contains all six continuable operation categories (data collection, documentation writing, code review, project structure setup, backup/restore, running existing code)
3. **Fallback instructions present**: Each blocked operation has a corresponding fallback instruction referencing a specific alternative (docs.senzing.com, `src/`, `docs/mapping_*.md`, support@senzing.com)
4. **Reconnection procedure present**: The file contains a reconnection section referencing `get_capabilities` and periodic retry
5. **Connectivity troubleshooting present**: The file contains proxy settings, `mcp.senzing.com:443`, and MCP restart instructions
6. **Existing content preserved**: All existing sections (Module 0 through Modules 9-12, General Pitfalls, Recovery Quick Reference, Pre-Module Checklist) remain in the file
7. **YAML front matter preserved**: The file begins with `inclusion: manual` front matter
