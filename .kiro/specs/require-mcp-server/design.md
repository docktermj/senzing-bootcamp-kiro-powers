# Design Document

## Overview

This design implements the "require-mcp-server" feature: making the Senzing MCP server a hard requirement for the bootcamp, removing all offline/fallback infrastructure, deleting static Senzing knowledge files replaceable by MCP, and simplifying steering files to assume MCP is always available.

The changes are purely subtractive and editorial — deleting files, removing sections from existing files, and simplifying conditional logic. No new executable code is introduced. No new steering files are created. The net effect is fewer files, simpler steering, reduced token budget consumption, and a single-mode agent that always uses MCP for Senzing knowledge.

## Architecture

No architectural changes beyond removal. The existing architecture (steering files → agent → MCP server) remains intact. What changes is the removal of the secondary path (steering files → agent → fallback/offline logic).

### Before

```text
Agent → MCP available? → YES → use MCP tools
                       → NO  → load mcp-offline-fallback.md
                              → check .mcp_status
                              → offer offline mode
                              → use static content
                              → retry periodically
```

### After

```text
Agent → MCP health check at session start
      → PASS → proceed (MCP always used)
      → FAIL → block with error + troubleshooting steps
```

## Components and Changes

### Phase 1: Delete files (Requirements 1, 8, 9)

Files to delete outright:

| File | Requirement |
|------|-------------|
| `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` | 1 |
| `senzing-bootcamp/steering/mcp-offline-fallback.md` | 1 |
| `senzing-bootcamp/docs/guides/GLOSSARY.md` | 8 |
| `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md` | 9 |
| `senzing-bootcamp/docs/guides/DESIGN_PATTERNS.md` | 9 |
| `senzing-bootcamp/docs/guides/INCREMENTAL_LOADING.md` | 9 |
| `senzing-bootcamp/docs/guides/MULTI_LANGUAGE_DATA.md` | 9 |
| `senzing-bootcamp/docs/guides/STREAMING_INTEGRATION.md` | 9 |
| `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook` | 12 |

Total: 9 files deleted.

### Phase 2: Convert health check to hard gate (Requirements 2, 3, 14)

**File: `senzing-bootcamp/steering/onboarding-flow.md`**

Replace Step 0b entirely. Keep the probe (`search_docs` with 10-second timeout). Remove:
- The `config/.mcp_status` write on success/failure
- The "offline mode" offer on failure
- The "Mid-Session Recovery" section

Replace failure path with:

```text
### Failure Path

If the call times out or errors after 10 seconds:

1. Display the following blocking error:

⛔ The Senzing MCP server is unreachable.

The MCP server is required for the bootcamp — it generates SDK code,
looks up Senzing facts, and provides working examples. The bootcamp
cannot proceed without it.

**Troubleshooting steps:**
1. Verify internet connectivity (can you load any website?)
2. Test the endpoint: curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443
3. If behind a corporate proxy, allowlist mcp.senzing.com:443
4. Restart the MCP connection in the Kiro Powers panel
5. Verify DNS: nslookup mcp.senzing.com

After fixing the connection, say "retry" to try again.

2. 🛑 STOP — Do NOT proceed to any subsequent step. Wait for the
   bootcamper to fix the connection and request a retry.
```

**File: `senzing-bootcamp/steering/session-resume.md`**

Apply the same hard gate pattern to Step 2d. Remove `.mcp_status` read/write and mid-session recovery logic.

### Phase 3: Remove fallback logic from steering files (Requirements 4, 16, 19)

| File | Section to remove/simplify |
|------|---------------------------|
| `steering/entity-resolution-intro.md` | Remove "If MCP unavailable" comment block |
| `steering/module-03-quick-demo.md` | Remove inline 5-record fallback dataset and "if get_sample_data fails" conditional |
| `steering/visualization-guide.md` | Remove "Agent guidance — MCP unavailable" note |
| `steering/agent-instructions.md` | Simplify MCP Failure to one line: "Retry once. If still failing, block and tell bootcamper to fix connection. Never fabricate." |
| All module steering files | Remove any "check .mcp_status before MCP step" patterns |

### Phase 4: Update steering index and hook registry (Requirements 5, 12)

**File: `senzing-bootcamp/steering/steering-index.yaml`**

Remove:
- `offline: mcp-offline-fallback.md` keyword entry
- `mcp-offline-fallback.md` metadata entry (token_count, size_category)
- Any metadata entries for deleted guide files

**File: `senzing-bootcamp/hooks/hook-categories.yaml`**

Remove `verify-senzing-facts` from the critical hooks list.

**File: `senzing-bootcamp/steering/hook-registry.md`**

- Remove the `verify-senzing-facts` entry
- Decrement the hook count
- Remove `enforce-feedback-path` and `enforce-working-directory` entries from the failure impact table in onboarding (these were already combined; also remove `verify-senzing-facts`)

### Phase 5: Update onboarding flow (Requirements 8, 13)

**File: `senzing-bootcamp/steering/onboarding-flow.md`**

- Step 1: Remove "Copy glossary" substep
- Step 1: Remove `verify-senzing-facts` from hook failure impact table
- Step 2: Remove any MCP-unavailable conditional paths in language detection
- Step 4: Replace `GLOSSARY.md` reference with "ask the agent to explain any unfamiliar term"

### Phase 6: Simplify hooks (Requirements 12, 15)

**File: `senzing-bootcamp/hooks/error-recovery-context.kiro.hook`** (or its entry in hook-registry.md)

Remove from the prompt:
- "check whether `config/bootcamp_progress.json` exists" guard (keep this — it's not MCP-related)
- Any reference to checking `.mcp_status` before calling `explain_error_code`
- Fallback instructions for when MCP is unavailable

The hook should directly call `explain_error_code` for any SENZ error code.

### Phase 7: Replace static Senzing content with MCP instructions (Requirement 11)

**File: `steering/entity-resolution-intro.md`**

Replace the static content block + "verify later" comment with an agent instruction to call `search_docs` and present the results dynamically.

**File: `steering/design-patterns.md`**

Replace hardcoded pattern descriptions with instructions to call `search_docs(query="entity resolution design patterns")` and present current results.

**File: Language steering files (`lang-*.md`)**

Replace any hardcoded SDK method names with instructions to call `get_sdk_reference` at the point of need.

### Phase 8: Trim documentation files (Requirements 6, 17, 18, 20)

**File: `senzing-bootcamp/POWER.md`**

- Remove references to `OFFLINE_MODE.md` and `mcp-offline-fallback.md`
- Add statement: "The Senzing MCP server is required for the bootcamp to function"
- Replace offline troubleshooting with connection fix instructions

**File: `docs/guides/AFTER_BOOTCAMP.md`**

Keep: maintenance cadence, adding new data sources, MCP tool reference table.
Remove/replace: Scaling, Keeping Updated, Advanced Topics → one-liner each pointing to MCP tools.

**File: `steering/common-pitfalls.md`**

Keep: bootcamp-operational pitfalls, connectivity troubleshooting table.
Remove: Senzing-specific pitfalls → replace with "call MCP tool X" instructions.

**File: `docs/guides/COMMON_MISTAKES.md`**

Keep: bootcamp-operational mistakes (file paths, skipping modules, backup).
Remove: Senzing-specific mistakes → replace with "ask the agent" guidance.

**File: `docs/guides/FAQ.md`**

Keep: bootcamp-operational questions.
Remove: Senzing-specific answers, GLOSSARY.md reference, OFFLINE_MODE.md reference.

### Phase 9: Clean up cross-references (Requirements 1, 8, 9)

Update all files that reference deleted files:
- `docs/guides/README.md` — remove entries for deleted guides
- `docs/README.md` — remove entries
- `docs/guides/GETTING_HELP.md` — remove GLOSSARY and OFFLINE_MODE rows
- `docs/guides/ONBOARDING_CHECKLIST.md` — remove GLOSSARY reference
- `PERFORMANCE_BASELINES.md` — remove "See also" links to deleted files
- `COMMON_MISTAKES.md` — remove "See also" links to OFFLINE_MODE
- `QUALITY_SCORING_METHODOLOGY.md` — remove "See also" link to OFFLINE_MODE

### Phase 10: Update ARCHITECTURE.md (Requirement 14)

Remove from `docs/guides/ARCHITECTURE.md`:
- `.mcp_status` from the "Mutable user state" configuration table
- `.mcp_status` from the "Configuration Files by Stage" table
- "MCP Failure and Offline Fallback" section → replace with a brief note that MCP is required and the health check is a hard gate
- References to offline mode in the "Local vs Remote Boundary" diagram
- The "For detailed offline fallback instructions, see OFFLINE_MODE.md" link

## Data Models

No data model changes. The only data-related change is the removal of `config/.mcp_status` (a simple JSON file that is no longer written or read).

## Error Handling

The only error path that remains is the MCP health check failure at session start:
- Probe fails → display blocking error with troubleshooting steps → wait for retry
- No graceful degradation, no offline mode, no periodic retry logic

All other MCP errors during a session (individual tool call failures) are handled by the existing "retry once, then block" pattern in `agent-instructions.md`.

## Testing Strategy

**PBT does not apply.** This is a documentation/steering simplification — no executable logic is introduced or modified.

**Validation approach:**

1. **Steering lint** — Run `python senzing-bootcamp/scripts/lint_steering.py` to verify all modified steering files pass structural checks.
2. **Token budget** — Run `python senzing-bootcamp/scripts/measure_steering.py --check` to verify reduced token budgets after file deletions and content trimming.
3. **Hook registry sync** — Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` to confirm the registry matches the actual hook files after deletions.
4. **Cross-reference validation** — Run `python senzing-bootcamp/scripts/validate_power.py` to verify no broken file references remain after deletions.
5. **Existing tests** — Run `pytest senzing-bootcamp/tests/` to verify no test assertions break. Tests that assert GLOSSARY.md presence, offline mode references, or verify-senzing-facts hook existence will need updating.
