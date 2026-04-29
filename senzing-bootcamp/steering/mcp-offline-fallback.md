---
inclusion: manual
---

# MCP Server Unavailable — What You Can Still Do

If the MCP server is down, slow, or unreachable (corporate proxy, network outage, etc.), don't stop working. Use this section to determine exactly what's blocked, what can continue, and what fallback to use for each blocked operation.

## Blocked Operations (Require MCP)

These operations depend on a specific MCP tool and cannot proceed without a working MCP connection.

| Operation                  | MCP Tool             | Affected Modules | Fallback Summary                                                  |
| -------------------------- | -------------------- | ---------------- | ----------------------------------------------------------------- |
| Attribute mapping          | `mapping_workflow`   | 5, 7             | Refer to docs.senzing.com entity specification; check `docs/mapping_*.md` |
| Code generation            | `generate_scaffold`  | 0, 1, 6, 8      | Check `src/` for existing scaffold code to adapt                  |
| Error diagnosis            | `explain_error_code` | Any              | Note error code; check docs.senzing.com; email support@senzing.com |
| SDK reference lookup       | `get_sdk_reference`  | 0, 6, 8          | Browse docs.senzing.com SDK docs; check `src/` for usage patterns |
| Documentation search       | `search_docs`        | Any              | Browse docs.senzing.com directly in browser                       |

## Continuable Operations (No MCP Needed)

These operations rely on local files, existing artifacts, or general knowledge — no MCP connection required.

### Data Preparation

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Define business problem  | 2       | Fully independent of MCP — document problem, identify sources, define success criteria |
| Collect data             | 3       | Copy/download data files into `data/raw/`, document locations                          |
| Profile data manually    | 4       | Read CSV/JSON files, count rows, check columns, assess quality by inspection           |

### Documentation & Review

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Write documentation      | Any     | Update `docs/`, write journal entries, create runbooks                                 |
| Review/edit existing code| Any     | Fix bugs, refactor, add comments, improve error handling                               |
| Check progress           | Any     | `python scripts/status.py`, `python scripts/validate_module.py`                        |

### Visualization

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| View static HTML visualizations | 7 | Previously generated static HTML files (`docs/entity_graph.html`) open in any browser with no MCP connection required. See the "Offline vs Online" section in [`visualization-guide.md`](visualization-guide.md) for details on offline vs online mode tradeoffs. |

### Code & Infrastructure Maintenance

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Project structure setup  | Any     | Create directories, configure files, set up `config/` and `data/` layout               |
| Run existing programs    | 5-8     | Transformation, loading, and query programs that are already written still run          |
| Backup/restore           | Any     | `python scripts/backup_project.py` / `restore_project.py`                              |
| Git operations           | Any     | Commit, branch, review diffs                                                           |

## Fallback Instructions by Operation

When a bootcamper requests a blocked operation, use these specific fallback steps:

**Attribute mapping** (`mapping_workflow` unavailable):

1. Check `docs/mapping_specifications.md` and `docs/mapping_*.md` for mappings documented in previous sessions
2. Refer the bootcamper to the Senzing entity specification at <https://docs.senzing.com>
3. Do NOT guess attribute names — document what needs mapping and resume when MCP returns
4. Work on other data sources or documentation in the meantime

**Code generation** (`generate_scaffold` unavailable):

1. Check `src/` for existing scaffold code from previous modules that can be adapted
2. Review previously generated code for patterns to reuse
3. Do NOT hand-write Senzing SDK calls from memory — adapt only from existing verified code

**Error diagnosis** (`explain_error_code` unavailable):

1. Note the exact error code and full error message
2. Direct the bootcamper to search for the error code at <https://docs.senzing.com>
3. If unresolved, recommend emailing <support@senzing.com> with the error details
4. Document the error in `docs/` for follow-up when MCP reconnects

**SDK reference lookup** (`get_sdk_reference` unavailable):

1. Direct the bootcamper to the Senzing SDK documentation at <https://docs.senzing.com>
2. Check existing code in `src/` for usage patterns of the method in question
3. Do NOT guess method signatures or parameter names

**Documentation search** (`search_docs` unavailable):

1. Direct the bootcamper to browse <https://docs.senzing.com> directly in their browser
2. Check `senzing-bootcamp/docs/` for locally available documentation
3. Check `senzing-bootcamp/docs/guides/GLOSSARY.md` for term definitions

## What to Tell the Bootcamper

"The Senzing MCP server isn't responding right now. Here's what we can keep working on while we wait: [list applicable continuable activities from the tables above]. The things that need MCP — like generating new SDK code or starting a mapping workflow — we'll pick up once the connection is back. I'll retry periodically. In the meantime, I have specific fallback steps for each blocked operation if you need them."

## Reconnection Procedure

Follow these steps to detect MCP recovery and resume normal operations:

1. **Initial failure:** Retry the failed MCP call once (per `agent-instructions.md`)
2. **Enter offline mode:** If the retry fails, switch to fallback instructions above
3. **Periodic retry:** Attempt an MCP call approximately every 10 minutes, or when the bootcamper requests a retry
4. **Verify recovery:** On first successful MCP response, call `get_capabilities` to confirm full server functionality
5. **Resume operations:** Inform the bootcamper that MCP is available again and list any previously blocked operations that can now resume
6. **Re-query stale data:** If the outage spanned a module boundary, re-query MCP for fresh data per the reuse rules in `agent-instructions.md`

## Connectivity Troubleshooting

If MCP failures persist, check these common causes:

| Issue                        | Fix                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| Corporate proxy blocking MCP | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` environment variable if behind proxy  |
| Network connectivity         | Test: `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443` (expect 200 or 403) |
| MCP server not started       | Restart the MCP server connection in the IDE (check Kiro Powers panel)                   |
| Intermittent timeouts        | Retry with a longer timeout; check if other network-dependent tools also fail            |
| DNS resolution failure       | Verify DNS can resolve `mcp.senzing.com`; try `nslookup mcp.senzing.com`                |
