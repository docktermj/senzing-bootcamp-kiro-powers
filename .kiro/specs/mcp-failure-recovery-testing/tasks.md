# Tasks

## Task 1: Create example-based unit test file

- [x] 1.1 Create `senzing-bootcamp/tests/test_mcp_failure_recovery.py` with module-level constants (`ALL_MCP_TOOLS`, `MCP_DEPENDENT_MODULES`, `FORBIDDEN_PHRASES`, `ACTIONABLE_VERBS`), path resolution, and parsing helper functions (`parse_blocked_operations_table`, `parse_fallback_instructions`, `extract_section`, `parse_continuable_operations`, `parse_troubleshooting_table`, `extract_reconnection_steps`, `parse_call_pattern_tools`, `parse_anti_pattern_tools`)
- [x] 1.2 Add `TestOfflineFallbackCompleteness` class — verify every MCP tool in decision tree has blocked operation entry (Req 1.1), every blocked operation has fallback instruction with >= 2 steps (Req 1.2), no forbidden phrases (Req 1.3), concrete alternative resources (Req 1.4), and round-trip correspondence (Req 1.5)
- [x] 1.3 Add `TestModuleSteeringMCPHandling` class — verify Module 2 has fallback/reference for its MCP tools (Req 2.1), Module 3 has inline fallback for `get_sample_data` (Req 2.2), Module 5 Phase 2 has fallback for `mapping_workflow` (Req 2.3), Module 6 has fallback for `generate_scaffold` (Req 2.4), Module 7 has fallback for its MCP tools (Req 2.5), and error handling sections reference `explain_error_code` with fallback (Req 2.6)
- [x] 1.4 Add `TestReconnectionProcedure` class — verify exactly six steps (Req 3.1), retry interval with number + "minutes" (Req 3.2), `get_capabilities` reference (Req 3.3), `agent-instructions.md` reference (Req 3.4), and correct sequential order (Req 3.5)
- [x] 1.5 Add `TestConnectivityTroubleshooting` class — verify >= 5 entries (Req 4.1), non-empty Issue and Fix columns (Req 4.2), specific scenarios present (Req 4.3), and diagnostic command present (Req 4.4)
- [x] 1.6 Add `TestBootcamperCommunicationTemplate` class — verify section exists (Req 5.1), mentions continuable work (Req 5.2), blocked operations (Req 5.3), periodic retry (Req 5.4), and fallback steps (Req 5.5)
- [x] 1.7 Add `TestContinuableOperationsCoverage` class — verify >= 4 categories (Req 6.1), Modules column present (Req 6.2), "What to do" column present (Req 6.3), includes data prep/docs/code maintenance (Req 6.4), and no MCP tool references (Req 6.5)
- [x] 1.8 Add `TestDecisionTreeConsistency` class — verify call pattern tools covered in fallback (Req 7.1), anti-patterns overlap >= 3 (Req 7.2), `get_capabilities` cross-reference (Req 7.3), and decision tree superset of blocked ops (Req 7.4)

## Task 2: Create property-based test file

- [x] 2.1 Create `senzing-bootcamp/tests/test_mcp_failure_recovery_properties.py` with module-level parsing (reuse parsing logic from task 1), Hypothesis imports, and `st.sampled_from()` strategies for blocked operations, fallback instructions, continuable operations, troubleshooting entries, and MCP-dependent module paths
- [x] 2.2 Add `TestFallbackStepCountBounds` class — Property 1: for all fallback instructions, step count is between 2 and 10 (Req 1.2, 8.1)
- [x] 2.3 Add `TestNoForbiddenPhrases` class — Property 2: for all fallback instructions, no step contains "guess", "assume", "probably", or "might be" (Req 1.3)
- [x] 2.4 Add `TestFallbackConcreteResources` class — Property 3: for all fallback instructions, at least one step references a URL, file path, or command (Req 1.4)
- [x] 2.5 Add `TestBlockedOperationFallbackRoundTrip` class — Property 4: for all blocked operations, tool name appears in backtick code in exactly one fallback heading (Req 1.5, 8.3)
- [x] 2.6 Add `TestErrorHandlingFallbackPath` class — Property 5: for all MCP-dependent module files, error handling references `explain_error_code` with fallback path (Req 2.6)
- [x] 2.7 Add `TestTroubleshootingEntryCompleteness` class — Property 6: for all troubleshooting entries, Issue and Fix are non-empty (Req 4.2)
- [x] 2.8 Add `TestContinuableOperationsTableStructure` class — Property 7: for all continuable operation entries, Modules column and What to do column with actionable verb present (Req 6.2, 6.3, 8.4)
- [x] 2.9 Add `TestNoContinuableMCPDependency` class — Property 8: for all continuable operation entries, no MCP tool name referenced as required (Req 6.5)
- [x] 2.10 Add `TestDecisionTreeSupersetProperty` class — Property 9: for all blocked operation tools, tool appears in decision tree call patterns (Req 7.4)
- [x] 2.11 Add `TestNoMCPCallInFallbackSteps` class — Property 10: for all fallback instruction steps, no MCP tool name referenced as a call (Req 8.2)
- [x] 2.12 Ensure all property test classes use `@settings(max_examples=100)` and include docstrings with tag format `Feature: mcp-failure-recovery-testing, Property {N}: {title}`

## Task 3: Integration verification

- [x] 3.1 Run `pytest senzing-bootcamp/tests/test_mcp_failure_recovery.py -v` and verify all example-based tests pass
- [x] 3.2 Run `pytest senzing-bootcamp/tests/test_mcp_failure_recovery_properties.py -v` and verify all property-based tests pass
- [x] 3.3 Run `pytest senzing-bootcamp/tests/` and verify the full test suite passes without errors alongside existing tests
