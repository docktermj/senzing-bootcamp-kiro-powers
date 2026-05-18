# Implementation Plan

- [x] 1. Write bug condition exploration tests
  - **Property 1: Bug Condition** - Agent has no SDK Method Discovery Protocol
  - **CRITICAL**: These tests MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the tests or the code when they fail**
  - **NOTE**: These tests encode the expected behavior — they will validate the fix when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in `senzing-bootcamp/steering/agent-instructions.md` and `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
  - **Scoped PBT Approach**: The bug is deterministic — scope the property to the concrete MCP Rules section of the steering files
  - Create test file `senzing-bootcamp/tests/test_sdk_method_discovery_bug.py`
  - Follow existing test patterns from `test_track_selection_gate_bug.py` (class-based, Path-relative, Hypothesis PBT)
  - Parse `agent-instructions.md`, extract the MCP Rules section
  - **Test 1 — Missing Discovery Protocol**: Assert the MCP Rules section contains an SDK method discovery protocol instructing the agent to discover available methods via `get_sdk_reference` before selecting one when the request is ambiguous (will FAIL on unfixed code — no protocol exists)
  - **Test 2 — Missing Category Taxonomy**: Assert `agent-instructions.md` contains SDK method category definitions that group related methods (e.g., why/how category with `how_entity`, `why_entities`, `why_records`, `why_record_in_entity`) (will FAIL on unfixed code — no categories defined)
  - **Test 3 — Missing Clarification Instruction**: Assert the MCP Rules section contains an instruction to ask a 👉 clarifying question when multiple discovered methods could satisfy the bootcamper's request (will FAIL on unfixed code — no such instruction exists)
  - **Test 4 — Missing Skip Conditions**: Assert the protocol defines explicit skip conditions: when the bootcamper names a method, when the request is unambiguous, when discovery was already performed in the session (will FAIL on unfixed code — no skip conditions exist)
  - **PBT Test — Discovery Protocol Placement**: Use Hypothesis to generate section headings from `agent-instructions.md` and verify that only the MCP-related sections should contain SDK method discovery instructions; non-MCP sections (Communication, Hooks, Context Budget, etc.) should not contain discovery protocol keywords
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests 1–4 FAIL (this is correct — it proves the bug exists); PBT test PASSES (confirms non-MCP sections don't accidentally contain discovery instructions)
  - Document counterexamples found: no discovery protocol, no category taxonomy, no clarification instruction, no skip conditions
  - Mark task complete when tests are written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2 & 3: Preservation** - Existing MCP Rules and Steering Content Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Create test file `senzing-bootcamp/tests/test_sdk_method_discovery_preservation.py`
  - Follow existing test patterns from `test_track_selection_gate_preservation.py` (class-based, Path-relative, Hypothesis PBT)
  - Observe the UNFIXED `agent-instructions.md` structure: YAML frontmatter, section headings, MCP rule bullet points, Communication section, Hooks section, Context Budget section
  - **Test 1 — Existing MCP Rule Bullets Preserved**: Parse the MCP Rules section and snapshot all existing bullet points; assert each is present and unchanged after the fix (the fix is additive, not replacing)
  - **Test 2 — Flag Lookup Rule Preserved**: Assert the specific rule about looking up flags via `get_sdk_reference(topic='flags')` is present and unchanged
  - **Test 3 — SQL Redirects Preserved**: Assert the SQL-tempting question redirects line is present and unchanged
  - **Test 4 — Communication Section Preserved**: Assert the Communication section's 👉 rules, one-question-at-a-time rule, and fabrication prohibition are unchanged
  - **Test 5 — YAML Frontmatter Preserved**: Assert `agent-instructions.md` begins with YAML frontmatter containing `inclusion: always`
  - **Test 6 — Flag Selection Protocol Preserved**: Assert `mcp-tool-decision-tree.md` contains the Flag Selection Protocol section with its 4-step flow (Discover, Select, Explain, Cache) unchanged
  - **Test 7 — Module-07 Agent Instructions Preserved**: Assert `module-07-query-validation.md` agent instructions about flag lookups for `how_entity`, `why_entities`, etc. are unchanged
  - **Test 8 — Decision Tree Sections Preserved**: Assert all existing sections in `mcp-tool-decision-tree.md` (Session Start, Data Preparation, SDK Development, Troubleshooting, Reference and Reporting, Data Exploration, Anti-Patterns, Call Pattern Examples, Flag Selection Protocol) are present
  - **PBT Test — Non-MCP Sections Unchanged**: Use Hypothesis to generate section heading names from {Communication, Module Steering, Track Switching, State & Progress, Hooks, Context Budget, Mandatory Gate Precedence} and verify each section's content is identical between the observed baseline and the current file
  - Verify all tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Implement the SDK Method Discovery Protocol fix

  - [x] 3.1 Add SDK Method Discovery Protocol to `senzing-bootcamp/steering/agent-instructions.md`
    - Add a new subsection within or immediately after the MCP Rules section titled "### SDK Method Discovery"
    - Define the discover-then-disambiguate flow:
      1. **Trigger**: When the bootcamper's request could map to multiple SDK methods in the same category
      2. **Discover**: Call `get_sdk_reference` with a category/topic filter to enumerate all available methods in that category
      3. **Disambiguate**: If multiple methods could satisfy the request, ask a single 👉 clarifying question presenting the options as a numbered choice list with brief descriptions
      4. **Proceed**: If only one method matches, proceed directly noting other available methods for awareness
    - Define SDK method categories that have multiple alternatives:
      - **Why/How category**: `how_entity`, `why_entities`, `why_records`, `why_record_in_entity` — different granularity levels for understanding entity resolution decisions
      - **Entity retrieval**: `get_entity`, `get_entity_by_record_id` — different lookup keys
      - **Search**: `search_by_attributes`, `search_by_record_id` — different search inputs
    - Define explicit skip conditions (when discovery is NOT needed):
      - Bootcamper explicitly names a specific SDK method (e.g., "use how_entity")
      - Request unambiguously maps to exactly one method with no alternatives
      - Methods for this category already discovered in the current module session (reuse cached knowledge)
    - Do NOT modify existing MCP rule bullet points — the new content is additive
    - Do NOT modify the Communication section, Hooks section, or any other non-MCP section
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Add Method Discovery Protocol to `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
    - Add a new section after "Flag Selection Protocol" titled "## Method Discovery Protocol"
    - Define the step-by-step flow mirroring the Flag Selection Protocol pattern:
      1. **Detect** — Recognize when the bootcamper's request is ambiguous (could map to multiple methods)
      2. **Discover** — Call `get_sdk_reference(topic='functions', filter='<category>')` to enumerate available methods
      3. **Disambiguate** — If multiple methods match, present a 👉 numbered choice list with one-line descriptions
      4. **Proceed** — Use the bootcamper's chosen method (or the single matching method if unambiguous)
      5. **Cache** — Remember discovered methods for the rest of the module session
    - Add "When to Skip Method Discovery" subsection (parallel to "When to Skip Flag Lookup"):
      - Bootcamper explicitly specifies a method name
      - Request maps to exactly one method with no alternatives in the category
      - Methods for this category already discovered during the current module session
    - Add concrete examples of ambiguous vs. unambiguous requests:
      - Ambiguous: "explain why entity 74 resolved" → discover why/how category → present choices
      - Unambiguous: "get entity 42 by record ID" → only `get_entity_by_record_id` matches → proceed
      - Explicit: "use why_records on records A and B" → bootcamper named the method → proceed
    - Do NOT modify the Flag Selection Protocol section or any other existing section
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.3 Verify bug condition exploration tests now pass
    - **Property 1: Expected Behavior** - SDK Method Discovery Protocol exists
    - **IMPORTANT**: Re-run the SAME tests from task 1 — do NOT write new tests
    - Run: `python -m pytest senzing-bootcamp/tests/test_sdk_method_discovery_bug.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Verify preservation tests still pass
    - **Property 2 & 3: Preservation** - Existing content unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run: `python -m pytest senzing-bootcamp/tests/test_sdk_method_discovery_preservation.py -v`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest senzing-bootcamp/tests/test_sdk_method_discovery_bug.py senzing-bootcamp/tests/test_sdk_method_discovery_preservation.py -v`
  - Ensure all bug condition tests PASS (confirming the fix works)
  - Ensure all preservation tests PASS (confirming no regressions)
  - Ensure `module-07-query-validation.md` was NOT modified
  - Ensure `block-direct-sql.kiro.hook` was NOT modified
  - Ask the user if questions arise
