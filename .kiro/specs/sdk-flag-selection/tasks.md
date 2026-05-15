# Implementation Tasks: SDK Flag Selection

## Task 1: Add flag selection rule to agent-instructions.md

- [ ] Open `senzing-bootcamp/steering/agent-instructions.md`
- [ ] In the `## MCP Rules` section, after the line about `get_sdk_reference` for signatures, add: `- SDK method calls that accept flags: look up available flags via get_sdk_reference(topic='flags'), select flags matching the bootcamper's intent, and explain the choice in one sentence. Reuse flag knowledge within a module session. Default flags are acceptable for simple lookups but note that detailed flags exist.`
- [ ] Verify the file still parses correctly (valid markdown, no broken formatting)

## Task 2: Add Flag Selection Protocol to mcp-tool-decision-tree.md

- [ ] Open `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
- [ ] After the `## Call Pattern Examples` section's `get_sdk_reference` example, add a new section `## Flag Selection Protocol` with the following content:
  - When to look up flags: before any SDK method call that accepts a flags parameter
  - How to look up: `get_sdk_reference(method='<method_name>', topic='flags')`
  - How to select: match flags to bootcamper intent (default for overview, `SZ_INCLUDE_FEATURE_SCORES` for scoring, `SZ_INCLUDE_MATCH_KEY_DETAILS` for match keys, both for visualizations)
  - How to explain: one sentence telling the bootcamper which flags and why
  - When to skip: bootcamper explicitly specifies flags, method has no flag parameter, or flags already looked up this module session
- [ ] Add an anti-pattern row to the existing anti-patterns table: "Instead of: Passing None/default flags without checking | Use: `get_sdk_reference(topic='flags')` | Consequence: Missing detail needed for visualizations, no teaching moment about flag system"

## Task 3: Add flag-aware instruction to module-07-query-validation.md

- [ ] Open `senzing-bootcamp/steering/module-07-query-validation.md`
- [ ] In Step 2 (Create query programs), after the `generate_scaffold` instruction, add an agent instruction block:
  ```
  > **Agent instruction:** When generating query code that calls SDK methods accepting flags (get_entity, search_by_attributes, how_entity, why_entities, why_records, why_record_in_entity), look up available flags via `get_sdk_reference(method='<method>', topic='flags')` and select flags matching the bootcamper's query intent. Explain the flag choice: "I'm using [flag] so we can see [what it provides]." For visualization queries, include `SZ_INCLUDE_FEATURE_SCORES` and/or `SZ_INCLUDE_MATCH_KEY_DETAILS`.
  ```
- [ ] In Step 3a (Present query results), add a note that when presenting results from `how_entity` or `why_*` methods, the agent should have used feature score and match key detail flags to provide informative output

## Task 4: Update steering-index.yaml token counts

- [ ] Run `python3 senzing-bootcamp/scripts/measure_steering.py` to recalculate token counts for the three modified files
- [ ] Update `steering-index.yaml` `file_metadata` entries for `agent-instructions.md`, `mcp-tool-decision-tree.md`, and `module-07-query-validation.md` with new token counts
- [ ] Verify no file crossed a `size_category` boundary (all should remain in their current category)

## Task 5: Validate changes pass CI checks

- [ ] Run `python3 senzing-bootcamp/scripts/validate_power.py` to confirm power structure is valid
- [ ] Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to confirm all modified markdown files are valid CommonMark
- [ ] Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to confirm token budgets are within limits
- [ ] Run `pytest senzing-bootcamp/tests/` to confirm no test failures
