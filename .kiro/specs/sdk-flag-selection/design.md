# Technical Design: SDK Flag Selection

## Overview

This design addresses the bug where the agent ignores SDK flags when calling Senzing methods, passing `None` (defaults) without looking up available flags or explaining choices to the bootcamper. The fix adds a flag-awareness protocol to the agent's SDK usage workflow, implemented through steering file updates.

## Architecture

The fix is entirely within the steering layer — no code changes, no new scripts, no new hooks. The agent's behavior is governed by steering instructions, so the fix adds explicit flag-selection rules to the existing steering files that control SDK method usage.

### Components Modified

1. **`steering/mcp-tool-decision-tree.md`** — Add a "Flag Selection" section to the SDK Development branch that instructs the agent to look up flags via `get_sdk_reference` before calling any SDK method that accepts flags.

2. **`steering/module-07-query-validation.md`** — Add an agent instruction block in Step 2 (Create query programs) and Step 3 (Run exploratory queries) that requires flag-aware SDK usage with explanations to the bootcamper.

3. **`steering/agent-instructions.md`** — Add a concise rule to the MCP Rules section reinforcing that SDK method calls must include intentional flag selection with explanation.

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Steering-only fix (no hooks) | The behavior is about SDK usage discipline during code generation — a hook can't inspect the agent's internal reasoning about flags. Steering instructions are the correct enforcement mechanism. |
| Add to `mcp-tool-decision-tree.md` | This is the file the agent loads when deciding how to use MCP tools. Adding flag guidance here means it's available whenever the agent is doing SDK work. |
| Add to Module 7 specifically | Module 7 is where the bug was reported and where query/visualization work happens. The flag guidance is most critical here. |
| Brief rule in `agent-instructions.md` | The core rules file is always loaded. A one-line rule ensures the behavior persists even if the decision tree isn't loaded. |
| No new steering file | The guidance is small enough to fit in existing files without exceeding token budgets. Adding a new file would increase context load unnecessarily. |

### Flag Selection Protocol (Agent Behavior)

When the agent selects an SDK method that accepts flags:

1. **Discover** — Call `get_sdk_reference(method='<method_name>', topic='flags')` to retrieve available flags for that method (unless already looked up in this module session).
2. **Select** — Choose flags that match the bootcamper's intent:
   - High-level overview → default flags
   - Detailed scoring/explanation → `SZ_INCLUDE_FEATURE_SCORES`
   - Match key breakdown → `SZ_INCLUDE_MATCH_KEY_DETAILS`
   - Visualization → both feature scores and match key details
3. **Explain** — Tell the bootcamper which flags are being used and why, in one sentence (e.g., "I'm including `SZ_INCLUDE_FEATURE_SCORES` so we can see confidence scores for each feature comparison").
4. **Cache** — Reuse flag knowledge within the same module session without re-querying.

### Exceptions (No Flag Lookup Required)

- Bootcamper explicitly specifies flags
- Method doesn't accept flags (e.g., `add_record` with no flag parameter)
- Simple entity lookup where defaults are appropriate — but still note that more detailed flags exist

## Token Budget Impact

| File | Current Tokens | Added Tokens (est.) | New Total |
|------|---------------|--------------------:|-----------|
| `mcp-tool-decision-tree.md` | 1,275 | ~200 | ~1,475 |
| `module-07-query-validation.md` | 2,728 | ~150 | ~2,878 |
| `agent-instructions.md` | 2,499 | ~30 | ~2,529 |

All files remain within their current `size_category` thresholds. No budget concerns.

## Testing Strategy

- **Manual verification**: Run through Module 7 Step 3 with a query like "explain why entity X resolved" and confirm the agent:
  1. Calls `get_sdk_reference` for flags before using `how_entity` or `why_record_in_entity`
  2. Selects appropriate flags based on the request
  3. Explains the flag choice to the bootcamper
- **Regression check**: Confirm that simple `get_entity` lookups still work without requiring the bootcamper to choose flags (agent uses defaults but mentions availability)
- **Existing tests**: Run `pytest senzing-bootcamp/tests/` to confirm no steering validation failures

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `senzing-bootcamp/steering/mcp-tool-decision-tree.md` | Modify | Add Flag Selection Protocol section |
| `senzing-bootcamp/steering/module-07-query-validation.md` | Modify | Add flag-aware agent instruction in Steps 2-3 |
| `senzing-bootcamp/steering/agent-instructions.md` | Modify | Add one-line flag rule to MCP Rules |
| `senzing-bootcamp/steering/steering-index.yaml` | Modify | Update token counts after edits |
