# Senzing Bootcamp - Permissions Guide

## Overview

Kiro 1.0 uses a capability-based permissions model. Before the agent writes a
file, runs a shell command, or calls an MCP tool, Kiro asks you to approve the
operation. The bootcamp is a hands-on, tool-assisted workflow, so it requests
these capabilities frequently.

This guide describes the write, shell, and MCP capabilities the bootcamp
requests and the recommended approval scope for each, so the capability prompts
do not stall the guided experience.

## Capabilities at a Glance

| Capability | What the bootcamp does | Recommended approval scope |
| ---------- | ---------------------- | -------------------------- |
| Write | Creates and edits files in your project | Approve writes inside the project workspace |
| Shell | Runs the bootcamp's Python helper scripts | Approve Python script runs inside the project |
| MCP | Calls Senzing MCP tools for facts and code | Auto-approve the read-only tools via `mcp.json` |

## Write Capability

The bootcamp writes files as you work through the modules. Typical writes
include:

- The transformation, loading, and query programs generated in your chosen
  language
- Configuration files under `config/` (for example progress and data-source
  files)
- Feedback files and project backups
- Documentation and checklist artifacts

**Recommended approval scope:** approve file writes that target your project
workspace. The bootcamp ships `PreToolUse` write-gate hooks that already block
writes to `/tmp` and paths outside the project, and route feedback to the
correct file, so approving in-project writes keeps you moving without giving up
those guardrails. Review any prompt that asks to write outside the project
before approving.

## Shell Capability

The bootcamp runs small, standard-library-only Python helper scripts to set up
and check your project. Common examples:

- `scripts/preflight.py` — verifies prerequisites before you start
- `scripts/status.py` — shows current module and progress
- `scripts/install_hooks.py` — installs the bootcamp hooks
- `scripts/backup_project.py` / `scripts/restore_project.py` — back up and
  restore your work

**Recommended approval scope:** approve Python script executions that run the
bootcamp's own scripts inside your project. These scripts use the Python
standard library only and do not install third-party dependencies. Review any
command that runs a tool from outside the project before approving.

## MCP Capability

The bootcamp connects to the Senzing MCP server for all Senzing facts, SDK
references, and generated code — it never relies on memorized Senzing details.
Each MCP tool call is a capability the agent requests.

**Recommended approval scope:** the read-only Senzing MCP tools the bootcamp
uses are listed in the `autoApprove` array of `mcp.json`, so read-only calls do
not stall. The read-only tools are:

- `get_capabilities`
- `mapping_workflow`
- `analyze_record`
- `download_resource`
- `explain_error_code`
- `search_docs`
- `find_examples`
- `generate_scaffold`
- `get_sample_data`
- `get_sdk_reference`
- `sdk_guide`
- `reporting_guide`

The `submit_feedback` tool stays in the `disabledTools` list and is not called
automatically. The Senzing MCP server URL lives only in `mcp.json`, which is the
single source of truth for the server address and the auto-approve list — see
`senzing-bootcamp/mcp.json`.

## Related Documentation

- Hook installation and the write-gate hooks: [HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md)
- MCP configuration: `senzing-bootcamp/mcp.json`
- Getting started: [QUICK_START.md](QUICK_START.md)
