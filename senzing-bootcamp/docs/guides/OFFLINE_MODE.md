# Offline Mode Guide

## What Is Offline Mode?

The Senzing Bootcamp uses an MCP (Model Context Protocol) server to provide real-time access to Senzing documentation, SDK references, code generation, and attribute mapping tools. When this server is unreachable — due to network issues, corporate proxy restrictions, or a server outage — you enter "offline mode."

The good news: **no module is completely blocked.** Every module has activities you can continue with while MCP is down. This guide helps you understand exactly what works, what waits, and how to get reconnected.

## Module-by-Module Offline Capability

### Fully Offline Modules

These modules need no MCP connection at all. You can complete them entirely offline.

| Module | Name | Why It Works Offline |
| ------ | ---- | -------------------- |
| 2 | Business Problem | Planning and documentation only — define your problem, identify sources, set success criteria |
| 3 | Data Collection | File operations only — copy data into `data/raw/`, document locations, assess sources |

### Mostly Offline Modules

These modules work almost entirely offline, with minor MCP-dependent features.

| Module | Name | What Works Offline | What Needs MCP |
| ------ | ---- | ------------------ | -------------- |
| 4 | Data Quality | Manual data profiling, row counts, column inspection, quality assessment by inspection | Automated quality scoring via `search_docs` (optional) |

### Partially Blocked Modules

These modules have core activities that depend on MCP tools. You can still make progress on other parts.

| Module | Name | What Works Offline | What Needs MCP |
| ------ | ---- | ------------------ | -------------- |
| 0 | SDK Setup | Project structure setup, configuration files, directory layout | Code scaffolding (`generate_scaffold`), SDK reference (`get_sdk_reference`) |
| 1 | Quick Demo | Reviewing existing code, running previously generated programs | Demo code generation (`generate_scaffold`) |
| 5 | Data Mapping | Running existing transformation programs, reviewing previous mappings in `docs/mapping_*.md` | Starting new mapping workflows (`mapping_workflow`) |
| 6 | Single Source Loading | Running existing loading programs, database backup/restore, monitoring progress | New loading code generation (`generate_scaffold`), SDK method lookup (`get_sdk_reference`) |
| 7 | Multi-Source Orchestration | Running existing orchestration code, monitoring multi-source progress | New source mapping (`mapping_workflow`), code generation for new sources |
| 8 | Query, Visualize & Validate | Running existing query programs, reviewing results, conducting UAT with business users | New query code generation (`generate_scaffold`), SDK reference (`get_sdk_reference`) |
| 9-12 | Production Readiness | Running existing tests, reviewing documentation, infrastructure planning | Production guidance (`search_docs`), SDK reference (`get_sdk_reference`) |

### Key Takeaway

Every module has offline-capable activities. If you are blocked on an MCP-dependent task, switch to documentation, code review, data preparation, or running existing programs until the connection is restored.

## What You Can Always Do (No MCP Needed)

Regardless of which module you are on, these activities never require MCP:

- **Write documentation** — update `docs/`, write journal entries, create runbooks
- **Review and edit existing code** — fix bugs, refactor, add comments, improve error handling
- **Run existing programs** — transformation, loading, and query programs that are already written still work
- **Manage your project** — create directories, configure files, set up `config/` and `data/` layout
- **Back up and restore** — `python scripts/backup_project.py` and `python scripts/restore_project.py`
- **Use git** — commit, branch, review diffs
- **Check progress** — `python scripts/status.py`, `python scripts/validate_module.py`

## Reconnecting to MCP

If MCP is not responding, try these steps in order:

### 1. Check Your Network

Make sure you have general internet connectivity. Try loading any website in your browser.

### 2. Test the MCP Endpoint

Run this command in your terminal to check if the MCP server is reachable:

```bash
curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443
```

- **200 or 403**: The server is reachable — the issue may be with your IDE connection.
- **000 or timeout**: The server is unreachable — check your network or proxy settings.

### 3. Check Proxy Settings

If you are behind a corporate proxy, make sure `mcp.senzing.com:443` is allowlisted. You may also need to set the `HTTPS_PROXY` environment variable:

```bash
export HTTPS_PROXY=http://your-proxy-server:port
```

### 4. Restart the MCP Connection

In your IDE, open the Kiro Powers panel and restart the Senzing MCP server connection.

### 5. Ask the Agent to Retry

Tell the agent: "Can you retry the MCP connection?" The agent will attempt to reconnect and confirm whether MCP is available again.

### 6. Contact Support

If the issue persists, check the [Senzing documentation](https://docs.senzing.com) directly in your browser, or email <support@senzing.com> for help.

## How the Agent Handles Outages

You do not need to memorize the details above. When MCP goes down, the bootcamp agent automatically:

1. Retries the connection once
2. Switches to offline fallback procedures if the retry fails
3. Tells you what is blocked and what you can keep working on
4. Retries periodically (approximately every 10 minutes) or when you ask
5. Notifies you when MCP is back and lists any previously blocked operations that can resume

The agent's detailed fallback procedures are defined in the `steering/common-pitfalls.md` file under the "MCP Server Unavailable" section. You do not need to read that file — the agent follows it automatically. But if you are curious about the specific fallback for each MCP tool, that is where to look.

---

**See also**: [FAQ](FAQ.md) | [Quick Start](QUICK_START.md) | [Common Mistakes](COMMON_MISTAKES.md) | [Getting Help](GETTING_HELP.md) | [Troubleshooting (agent-facing)](../../steering/common-pitfalls.md#mcp-unavailable)
