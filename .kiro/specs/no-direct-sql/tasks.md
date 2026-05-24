# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Direct SQL Prohibition Missing
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the steering files lack SQL prohibition
  - **Scoped PBT Approach**: Generate agent output strings containing SQL keywords (SELECT, INSERT, UPDATE, DELETE) paired with Senzing indicators (G2C.db, RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT) and assert that the steering files contain explicit prohibition language covering those patterns
  - **Bug Condition from design**: `isBugCondition(output)` returns true when output contains SQL keywords AND targets Senzing database (G2C.db or internal tables)
  - Test that `agent-instructions.md` MCP Rules section contains explicit "never generate direct SQL" prohibition language (will FAIL on unfixed code)
  - Test that `mcp-tool-decision-tree.md` anti-patterns table contains a row about direct SQL against Senzing database (will FAIL on unfixed code)
  - Test that `senzing-bootcamp/hooks/block-direct-sql.kiro.hook` exists with valid JSON structure containing `when`/`then` fields covering SQL keywords and Senzing indicators (will FAIL on unfixed code)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists: steering files lack SQL prohibition)
  - Document counterexamples found (e.g., "agent-instructions.md MCP Rules has no mention of SQL prohibition", "anti-patterns table omits direct SQL row", "no hook exists to block SQL writes")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Senzing SQL and File I/O Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Observe: `agent-instructions.md` permits standard file I/O for CSV, JSONL, config files on unfixed code
  - Observe: `agent-instructions.md` MCP Rules section correctly guides SDK method usage on unfixed code
  - Observe: `mcp-tool-decision-tree.md` contains existing anti-pattern rows and decision tree branches on unfixed code
  - Observe: General SQL guidance for non-Senzing databases is not prohibited on unfixed code
  - Write property-based test: for all generated content strings where `isBugCondition` returns false (SQL for non-Senzing databases, file I/O operations, SDK method calls, general SQL education), the steering files produce the same guidance before and after the fix
  - Specifically test that non-Senzing SQL patterns (e.g., `SELECT * FROM users` without Senzing indicators) are NOT flagged by the prohibition language
  - Specifically test that file I/O patterns (CSV read/write, JSONL operations, YAML config access) remain unaffected
  - Specifically test that existing MCP tool guidance (`get_entity`, `search_by_attributes`, `generate_scaffold`) remains unchanged
  - Verify tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for direct SQL against Senzing database

  - [x] 3.1 Add explicit SQL prohibition rule to `senzing-bootcamp/steering/agent-instructions.md`
    - Add bullet point to MCP Rules section: "Never generate direct SQL (SELECT, INSERT, UPDATE, DELETE) against the Senzing database (database/G2C.db) or its internal tables (RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, etc.). All Senzing data access must go through SDK methods via MCP tools."
    - Add redirect guidance mapping common SQL-tempting questions to correct MCP tools (e.g., "count entities" → `reporting_guide`, "find duplicates" → `search_by_attributes`)
    - Ensure existing MCP Rules content is preserved unchanged
    - _Bug_Condition: isBugCondition(output) where output contains SQL keywords AND targets Senzing database_
    - _Expected_Behavior: agent-instructions.md MCP Rules section contains explicit SQL prohibition language_
    - _Preservation: All existing MCP Rules content, file I/O guidance, and SDK method guidance remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

  - [x] 3.2 Add direct SQL anti-pattern row to `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
    - Add row to anti-patterns table: "Writing direct SQL against the Senzing database | Use SDK methods via MCP tools (`get_entity`, `search_by_attributes`, `reporting_guide`) | Bypasses SDK abstraction, produces non-portable results, may return incorrect data from internal tables"
    - Add decision tree branch under data exploration that routes to SDK methods rather than SQL
    - Ensure existing anti-pattern rows and decision tree branches are preserved unchanged
    - _Bug_Condition: isBugCondition(output) where output contains SQL keywords AND targets Senzing database_
    - _Expected_Behavior: mcp-tool-decision-tree.md anti-patterns table contains direct SQL row_
    - _Preservation: All existing anti-pattern rows and decision tree structure remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 3.3_

  - [x] 3.3 Create `senzing-bootcamp/hooks/block-direct-sql.kiro.hook` preToolUse hook
    - Create new hook file with valid JSON structure (`name`, `version`, `when`, `then` fields)
    - Set `when.event` to `preToolUse` and `when.toolTypes` to `["write"]`
    - Write hook prompt that instructs the agent to check if content being written contains SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting Senzing database indicators (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_)
    - Hook prompt must instruct agent to rewrite using SDK methods via MCP tools if SQL is detected
    - Hook must NOT interfere with non-Senzing file writes or general SQL for other databases
    - Validate hook JSON schema (must have `name`, `version`, `when`, `then`)
    - _Bug_Condition: isBugCondition(output) where output contains SQL keywords AND targets Senzing database_
    - _Expected_Behavior: hook intercepts write operations containing SQL targeting Senzing database_
    - _Preservation: Non-Senzing file writes and general SQL for other databases are unaffected_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Direct SQL Prohibition Present
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (steering files contain SQL prohibition)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed - steering files now prohibit direct SQL)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Senzing SQL and File I/O Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions - non-Senzing operations unaffected)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/ tests/ -v`
  - Run CI validation: `python senzing-bootcamp/scripts/validate_power.py`
  - Run CommonMark validation: `python senzing-bootcamp/scripts/validate_commonmark.py`
  - Run hook registry verification: `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
  - Ensure all tests pass, ask the user if questions arise.
