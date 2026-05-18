# No Direct SQL Bugfix Design

## Overview

The bootcamp agent may generate direct SQL queries against the Senzing SQLite database (`database/G2C.db`) when helping users explore entity resolution results. This bypasses the Senzing SDK's abstraction layer, may produce incorrect or unsupported results, and teaches non-portable access patterns. The fix adds explicit prohibitions against direct SQL in the steering files (`agent-instructions.md` and `mcp-tool-decision-tree.md`) and introduces a `preToolUse` hook that intercepts write operations containing SQL targeting the Senzing database.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the agent generates code or instructions containing direct SQL queries against the Senzing database (`database/G2C.db` or Senzing internal tables)
- **Property (P)**: The desired behavior — all Senzing data access uses SDK methods via MCP tools (`get_entity`, `get_entity_by_record_id`, `search_by_attributes`, `why_entities`, `why_records`, `how_entity`)
- **Preservation**: Existing behaviors that must remain unchanged — file I/O for non-Senzing files, correct SDK method usage, general SQL guidance for non-Senzing databases, and scaffold code generation
- **agent-instructions.md**: The always-loaded steering file in `senzing-bootcamp/steering/` that defines core agent rules including MCP usage
- **mcp-tool-decision-tree.md**: The manually-loaded steering file that maps tasks to MCP tools and lists anti-patterns
- **Senzing internal tables**: Database tables like `RES_ENT`, `OBS_ENT`, `RES_FEAT_STAT`, `DSRC_RECORD`, `LIB_FEAT` that are implementation details of the Senzing engine

## Bug Details

### Bug Condition

The bug manifests when the agent generates output containing direct SQL statements targeting the Senzing database. The `agent-instructions.md` MCP Rules section requires all Senzing facts come from MCP tools but does not explicitly prohibit direct SQL access. The `mcp-tool-decision-tree.md` anti-patterns table lists common mistakes but omits direct SQL as an anti-pattern.

**Formal Specification:**
```
FUNCTION isBugCondition(output)
  INPUT: output of type AgentGeneratedContent (code block, instruction, or script)
  OUTPUT: boolean

  sql_keywords := ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'DROP TABLE',
                   'ALTER TABLE', 'PRAGMA']
  senzing_indicators := ['G2C.db', 'database/G2C.db', 'RES_ENT', 'OBS_ENT',
                         'RES_FEAT_STAT', 'DSRC_RECORD', 'LIB_FEAT', 'RES_REL',
                         'SZ_', 'sz_dm_']

  has_sql := ANY(keyword IN output.upper() FOR keyword IN sql_keywords)
  targets_senzing := ANY(indicator IN output FOR indicator IN senzing_indicators)
                     OR output references sqlite3.connect with Senzing database path

  RETURN has_sql AND targets_senzing
END FUNCTION
```

### Examples

- **Example 1**: User asks "How many resolved entities are there?" → Agent generates `SELECT COUNT(*) FROM RES_ENT` against `database/G2C.db` instead of using `get_entity_by_record_id` iterated over loaded records or `reporting_guide` MCP tool
- **Example 2**: User asks "Show me duplicate records" → Agent generates `SELECT * FROM OBS_ENT GROUP BY ...` instead of using `search_by_attributes` or `why_entities` MCP tools
- **Example 3**: User asks "Export all entity data" → Agent opens `sqlite3.connect('database/G2C.db')` and runs `SELECT * FROM DSRC_RECORD` instead of using SDK methods via MCP tools
- **Edge case**: User asks "How does SQLite work?" → Agent provides general SQL education (this is NOT a bug condition — no Senzing database is targeted)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Standard file I/O for non-Senzing files (CSV, JSONL, config files, user data) must continue to work exactly as before
- Correct SDK method calls through MCP tools must continue to work with proper parameters and flags
- General SQL guidance for non-Senzing databases or educational contexts must remain available
- Scaffold code generated via `generate_scaffold` MCP tool must continue to be used as-is
- The `enforce-file-path-policies` hook must continue to function without interference

**Scope:**
All agent outputs that do NOT contain SQL targeting the Senzing database should be completely unaffected by this fix. This includes:
- Code that reads/writes CSV, JSONL, or YAML files
- Code that uses `sqlite3` for non-Senzing databases (user's own databases)
- General SQL tutorials or explanations not targeting Senzing tables
- All existing MCP tool usage patterns
- Hook prompts and steering file loading behavior

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing Explicit Prohibition in agent-instructions.md**: The MCP Rules section says "All Senzing facts from MCP tools — never training data" but does not explicitly state "Never generate direct SQL against the Senzing database." The agent interprets the rule as about factual accuracy, not about access patterns.

2. **Missing Anti-Pattern in mcp-tool-decision-tree.md**: The anti-patterns table lists mistakes like "Hand-coding Senzing JSON mappings" and "Guessing SDK method names" but does not include "Writing direct SQL against the Senzing database" as an anti-pattern with its consequence.

3. **No Runtime Guardrail**: There is no `preToolUse` hook that inspects generated code for SQL patterns targeting the Senzing database before it gets written to disk. The `enforce-file-path-policies` hook checks file paths but not file content for SQL patterns.

4. **Implicit Knowledge Gap**: The agent's training data includes SQLite patterns and may default to direct SQL when asked data exploration questions, since the steering files don't create a strong enough prohibition signal.

## Correctness Properties

Property 1: Bug Condition - Direct SQL Prohibition

_For any_ agent-generated output where the bug condition holds (isBugCondition returns true — output contains SQL keywords targeting Senzing database tables or `database/G2C.db`), the steering files SHALL contain explicit prohibition language that instructs the agent to use SDK methods via MCP tools instead, AND the anti-patterns table SHALL list direct SQL as a prohibited pattern with consequences.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Senzing SQL and File I/O

_For any_ agent-generated output where the bug condition does NOT hold (isBugCondition returns false — output contains SQL for non-Senzing databases, general file I/O, or SDK method calls), the fixed steering files SHALL produce the same guidance as the original files, preserving all existing functionality for non-Senzing operations.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: `## MCP Rules`

**Specific Changes**:
1. **Add explicit SQL prohibition rule**: Add a bullet point to the MCP Rules section: "Never generate direct SQL (SELECT, INSERT, UPDATE, DELETE) against the Senzing database (database/G2C.db) or its internal tables (RES_ENT, OBS_ENT, DSRC_RECORD, etc.). All Senzing data access must go through SDK methods via MCP tools."
2. **Add redirect guidance**: Include a mapping of common SQL-tempting questions to the correct MCP tool (e.g., "count entities" → `reporting_guide`, "find duplicates" → `search_by_attributes`).

**File**: `senzing-bootcamp/steering/mcp-tool-decision-tree.md`

**Section**: `## Anti-Patterns: When NOT to Use`

**Specific Changes**:
3. **Add direct SQL anti-pattern row**: Add a row to the anti-patterns table: "Writing direct SQL against the Senzing database | Use SDK methods via MCP tools (`get_entity`, `search_by_attributes`, `reporting_guide`) | Bypasses SDK abstraction, produces non-portable results, may return incorrect data from internal tables"
4. **Add decision tree branch**: Add a branch under "What is the bootcamper trying to do?" for data exploration that routes to SDK methods rather than SQL.

**File**: `senzing-bootcamp/hooks/block-direct-sql.kiro.hook` (NEW)

**Specific Changes**:
5. **Create preToolUse hook**: Create a new hook that fires on write operations and checks if the content being written contains SQL patterns targeting the Senzing database. If detected, the hook instructs the agent to rewrite using SDK methods via MCP tools.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering files, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the current steering files lack explicit SQL prohibition language and that the anti-patterns table omits direct SQL.

**Test Plan**: Parse the UNFIXED `agent-instructions.md` and `mcp-tool-decision-tree.md` files and assert that SQL prohibition patterns are present. These tests will FAIL on unfixed code, confirming the bug exists.

**Test Cases**:
1. **MCP Rules SQL Prohibition Test**: Assert `agent-instructions.md` MCP Rules section contains explicit "never generate direct SQL" language (will fail on unfixed code)
2. **Anti-Pattern Table Test**: Assert `mcp-tool-decision-tree.md` anti-patterns table contains a row about direct SQL (will fail on unfixed code)
3. **Decision Tree Branch Test**: Assert `mcp-tool-decision-tree.md` has a data exploration branch routing to SDK methods (will fail on unfixed code)
4. **Hook Existence Test**: Assert `senzing-bootcamp/hooks/block-direct-sql.kiro.hook` exists with correct structure (will fail on unfixed code)

**Expected Counterexamples**:
- `agent-instructions.md` MCP Rules section has no mention of SQL or database queries
- `mcp-tool-decision-tree.md` anti-patterns table has no row mentioning SQL
- No hook exists to intercept SQL-containing writes
- Possible causes: omission in original steering file authoring, focus on MCP tool correctness rather than SQL prohibition

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering files contain the necessary prohibition language and guardrails.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := parseSteeringFiles_fixed()
  ASSERT result.agent_instructions CONTAINS sql_prohibition_language
  ASSERT result.decision_tree CONTAINS sql_anti_pattern_row
  ASSERT result.hooks CONTAINS block_direct_sql_hook
  ASSERT hook.prompt COVERS all sql_keywords AND senzing_indicators
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed steering files produce the same guidance as the original files.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT parseSteeringFiles_original(input) = parseSteeringFiles_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many random content strings to verify that non-SQL content is unaffected
- It catches edge cases where SQL-like keywords appear in non-Senzing contexts
- It provides strong guarantees that the prohibition doesn't over-match

**Test Plan**: Observe behavior on UNFIXED steering files first for non-SQL content (file I/O patterns, SDK method calls, general guidance), then write property-based tests capturing that behavior.

**Test Cases**:
1. **File I/O Preservation**: Verify that steering files still permit standard file I/O for CSV, JSONL, and config files after the fix
2. **SDK Method Preservation**: Verify that existing MCP tool guidance and SDK method call patterns remain unchanged
3. **General SQL Preservation**: Verify that general SQL education for non-Senzing databases is still permitted
4. **Scaffold Preservation**: Verify that `generate_scaffold` usage guidance remains unchanged

### Unit Tests

- Test that `agent-instructions.md` MCP Rules section contains SQL prohibition language
- Test that `mcp-tool-decision-tree.md` anti-patterns table includes direct SQL row
- Test that `block-direct-sql.kiro.hook` has valid JSON structure with correct `when`/`then` fields
- Test that hook prompt covers all known Senzing table names and SQL keywords
- Test edge cases: SQL-like content in non-Senzing contexts should not trigger prohibition

### Property-Based Tests

- Generate random agent output strings containing SQL keywords paired with Senzing indicators and verify the steering prohibition language covers them
- Generate random agent output strings containing SQL keywords paired with non-Senzing contexts and verify they are NOT prohibited by the steering language
- Generate random file content (CSV paths, JSONL operations, YAML configs) and verify the hook prompt would not flag them as violations
- Test that all Senzing internal table names mentioned in the prohibition are real table names from the Senzing schema

### Integration Tests

- Test full steering file loading with the new prohibition and verify no structural issues (valid Markdown, correct frontmatter)
- Test that the new hook file passes `sync_hook_registry.py --verify` validation
- Test that the new anti-pattern row doesn't break the decision tree table formatting
- Test that CI pipeline (`validate_power.py`, `validate_commonmark.py`) passes with the changes
