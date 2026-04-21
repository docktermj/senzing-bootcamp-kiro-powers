# Tasks: Expand Module 7 Steering File

## Task 1: Expand the Agent Workflow to 12 Steps

- [x] 1.1 Rewrite the Agent Workflow section with 12 numbered steps: (1) Anti-pattern check, (2) Source inventory, (3) Dependency analysis with circular dependency detection, (4) Load order determination using ordering heuristics, (5) Strategy selection with trade-offs, (6) Pre-load validation checklist, (7) Create orchestrator program with MCP tools, (8) Test with samples, (9) Run full orchestration with monitoring, (10) Process redo queue, (11) Cross-source validation with visualization offer, (12) Document results
- [x] 1.2 Ensure each step that requires bootcamper input includes a WAIT directive and a 👉-prefixed question
- [x] 1.3 Ensure all MCP tool references use exact tool names and parameter formats (generate_scaffold, find_examples, search_docs, explain_error_code, reporting_guide, analyze_record, get_sdk_reference)

## Task 2: Add Source Ordering Heuristics Section

- [x] 2.1 Add a "Source Ordering Heuristics" section after the workflow with four heuristics: quality-first, reference-before-transactional, volume-first, and attribute-density-first
- [x] 2.2 Add two concrete ordering examples: Customer 360 pattern (CRM → E-commerce → Support) and Compliance Screening pattern (Watchlists → Internal Records → Third-party Data)
- [x] 2.3 Add guidance for detecting and resolving circular dependencies between data sources

## Task 3: Add Conflict Resolution Guidance Section

- [x] 3.1 Add a "Conflict Resolution" section explaining Senzing's observation-based resolution approach
- [x] 3.2 Add at least three common conflict scenarios: different addresses, different phone numbers, and different name spellings across sources
- [x] 3.3 Add an example scenario showing two records from different sources resolving to one entity with all observations retained
- [x] 3.4 Add agent instruction to use search_docs for current conflict guidance and offer visualization with reporting_guide

## Task 4: Add Error Handling and Recovery Section

- [x] 4.1 Add a "Error Handling and Recovery" section with a pre-load validation checklist of at least 6 items
- [x] 4.2 Add per-source failure isolation guidance — continue loading remaining sources when one fails
- [x] 4.3 Add four common error scenarios with diagnosis and fix: invalid records, duplicate RECORD_IDs, DATA_SOURCE name mismatch, and transformation errors
- [x] 4.4 Add three recovery options when a source fails: skip and continue, retry after fix, restore from backup
- [x] 4.5 Add instruction to document all errors and resolutions in docs/loading_strategy.md

## Task 5: Add Troubleshooting Quick Reference Section

- [x] 5.1 Add a "Troubleshooting" section with a table covering at least six common multi-source issues: low match rates, unexpected merges, slow loading, redo queue issues, resource exhaustion, and ordering-related quality issues
- [x] 5.2 Add diagnostic steps for low cross-source match rates: check quality scores, review mapping consistency, use SDK "why" method
- [x] 5.3 Add performance benchmarks for SQLite vs PostgreSQL and guidance on when to recommend migration
- [x] 5.4 Add reference to common-pitfalls.md Module 7 section as fallback

## Task 6: Validate Final File Structure and Length

- [x] 6.1 Verify the file retains YAML front matter with inclusion: manual, the user reference link, Before/After framing, Prerequisites, and Success Criteria
- [x] 6.2 Verify the file contains at least 150 lines
- [x] 6.3 Verify all MCP tool references use correct canonical tool names

## Post-Implementation Updates

After initial implementation, the reference sections (Source Ordering Examples, Conflict Resolution, Error Handling, Troubleshooting) were extracted into `module-07-reference.md` (130 lines) per Kiro best practices. Main `module-07-multi-source.md` reduced from 324 to 205 lines. `agent-instructions.md` and `POWER.md` updated with new file reference.
