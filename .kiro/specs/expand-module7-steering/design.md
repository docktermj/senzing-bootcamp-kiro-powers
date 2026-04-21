# Design Document: Expand Module 7 Steering File

## Overview

This design describes how to expand the Module 7 (Multi-Source Orchestration) steering file from its current ~100 lines to 150+ lines. The expansion adds five major content sections: a detailed orchestration workflow, conflict resolution guidance, source-specific error handling, source ordering/dependency guidance, and an embedded troubleshooting reference. The file being modified is `senzing-bootcamp/steering/module-07-multi-source.md`.

Since this is a markdown steering file (not executable code), the "implementation" is structured content authoring following the conventions established by other steering files in the power.

## Architecture

### File Structure

The expanded steering file follows the same structure as other mature steering files (e.g., `module-05-data-mapping.md`, `module-06-single-source.md`):

```
module-07-multi-source.md
├── YAML front matter (inclusion: manual)
├── Title and user reference link
├── Purpose / Before-After / Prerequisites
├── Agent Workflow (numbered steps 1-12)
│   ├── 1. Anti-pattern check
│   ├── 2. Source inventory
│   ├── 3. Dependency analysis
│   ├── 4. Load order determination
│   ├── 5. Strategy selection
│   ├── 6. Pre-load validation checklist
│   ├── 7. Create orchestrator program
│   ├── 8. Test with samples
│   ├── 9. Run full orchestration
│   ├── 10. Process redo queue
│   ├── 11. Cross-source validation
│   └── 12. Document results
├── Source Ordering Heuristics
├── Conflict Resolution Guidance
├── Error Handling and Recovery
├── Troubleshooting Quick Reference
├── Success Criteria
└── Common Issues (expanded)
```

### Content Conventions

All content follows the established steering file conventions observed across the power:

1. **Agent instruction blockquotes**: `> **Agent instruction:** ...` for directives only the agent sees
2. **WAIT directives**: Explicit `WAIT for response.` after every bootcamper question
3. **👉 markers**: All bootcamper-facing questions prefixed with 👉
4. **MCP tool calls**: Exact tool names with parameter syntax (e.g., `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`)
5. **File path references**: Always project-relative (e.g., `docs/loading_strategy.md`, `src/load/orchestrator.[ext]`)
6. **Path override rule**: Any MCP-generated paths using `/tmp/` or `ExampleEnvironment` must be overridden to project-relative paths

### Relationship to Other Files

The steering file references but does not duplicate content from:
- `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md` — detailed module documentation (user reference)
- `common-pitfalls.md` — Module 7 pitfall table (fallback troubleshooting)
- `module-06-single-source.md` — predecessor module (loading patterns carry forward)
- `module-transitions.md` — journey map and step-level progress rules (auto-included)
- `module-completion.md` — journal and path-completion workflow (loaded after completion)

## Detailed Design

### Section 1: Expanded Agent Workflow (Steps 1-12)

The current 7-step workflow expands to 12 steps. Each step includes:
- What the agent does (action)
- Why it matters (context for the agent)
- What to tell the bootcamper (communication)
- WAIT points where applicable

**New steps added:**
- Step 2 (Source Inventory): Agent enumerates all sources from previous modules with record counts, quality scores, and mapping status
- Step 4 (Load Order Determination): Agent applies ordering heuristics to recommend optimal sequence
- Step 6 (Pre-load Validation Checklist): Agent runs a checklist before starting orchestration
- Step 11 (Cross-source Validation): Agent verifies matches across sources and offers visualization
- Step 12 (Document Results): Agent creates/updates loading strategy documentation

**Existing steps enhanced:**
- Step 1 (Anti-pattern check): Unchanged
- Step 3 (Dependency Analysis): Expanded with circular dependency detection
- Step 5 (Strategy Selection): Expanded with trade-off details for each option
- Step 7 (Create Orchestrator): Enhanced with explicit MCP tool calls and path override rules
- Step 8 (Test with Samples): Enhanced with specific test criteria
- Step 9 (Full Orchestration): Enhanced with monitoring details and per-source progress
- Step 10 (Redo Processing): Enhanced with cross-source redo explanation

### Section 2: Source Ordering Heuristics

A new section providing four ordering heuristics the agent uses to recommend load order:

1. **Quality-first**: Load highest-quality source first to establish strong entity baseline
2. **Reference-before-transactional**: Load reference/master data before transactional data
3. **Volume-first**: Load largest source first for maximum baseline coverage
4. **Attribute-density-first**: Load sources with the most identifying attributes first for better matching

Includes two concrete examples:
- **Customer 360**: CRM → E-commerce → Support (quality-first pattern)
- **Compliance Screening**: Watchlists → Internal Records → Third-party Data (reference-first pattern)

### Section 3: Conflict Resolution Guidance

A new section explaining how Senzing handles cross-source conflicts:

- Senzing uses observation-based resolution (all observations are retained, not overwritten)
- Three common conflict scenarios with explanations:
  1. Different addresses across sources (both retained as observations)
  2. Different phone numbers (both retained, entity has multiple)
  3. Different name spellings (Senzing matches on features, retains all variants)
- Example scenario showing two records from different sources resolving to one entity
- Agent instruction to use `search_docs` for current Senzing conflict guidance
- Offer to visualize cross-source relationships

### Section 4: Error Handling and Recovery

A new section covering source-specific error handling:

- **Pre-load validation checklist**: 6 items to check before starting orchestration
- **Per-source failure isolation**: When one source fails, continue with remaining sources
- **Four common error scenarios** with diagnosis and fix:
  1. Invalid records → check transformation, use `analyze_record`
  2. Duplicate RECORD_IDs across sources → ensure uniqueness within each DATA_SOURCE
  3. DATA_SOURCE name mismatch → verify against Module 0 configuration
  4. Transformation errors → re-run Module 5 mapping for affected source
- **Three recovery options** when a source fails: skip and continue, retry after fix, restore from backup
- **Error documentation**: Record all errors and resolutions in `docs/loading_strategy.md`

### Section 5: Troubleshooting Quick Reference

An embedded troubleshooting table covering six common multi-source issues:

| Issue | Diagnosis | Resolution |
|-------|-----------|------------|
| Low cross-source match rates | Check quality scores, mapping consistency, use SDK "why" method | Improve data quality, align mappings |
| Unexpected entity merges | Review match details with SDK "why" method | Check for data quality issues, overly generic features |
| Slow multi-source loading | Check source count, record volume, database type | Reduce parallelism, use PostgreSQL, optimize transforms |
| Redo queue not draining | Check for errors in redo processing | Use `explain_error_code`, restart redo processor |
| Resource exhaustion | Monitor memory/CPU during parallel loading | Reduce max parallel loaders, increase resources |
| Source ordering affects quality | Compare results with different load orders | Apply ordering heuristics, reload with optimal order |

Includes performance benchmarks for SQLite vs PostgreSQL and when to recommend migration.

## Correctness Properties

Since this is a markdown content file (not executable code), correctness properties focus on structural validation of the output file.

### Property 1: Minimum Line Count (Requirement 6, AC 6.1)

**Type:** Structural validation
**Property:** The expanded steering file contains at least 150 lines of content.
**Verification:** Count non-empty lines in the output file. The count must be ≥ 150.

### Property 2: Required Sections Present (Requirements 1-5, AC 6.4)

**Type:** Structural validation
**Property:** The file contains all required sections: YAML front matter, Before/After, Prerequisites, Agent Workflow with ≥10 numbered steps, Source Ordering, Conflict Resolution, Error Handling, Troubleshooting, and Success Criteria.
**Verification:** Grep for section headers and key markers. All must be present.

### Property 3: MCP Tool References Use Correct Names (Requirement 6, AC 6.6)

**Type:** Content validation
**Property:** All MCP tool references in the file use tool names from the canonical set: `generate_scaffold`, `find_examples`, `search_docs`, `explain_error_code`, `reporting_guide`, `analyze_record`, `get_sdk_reference`, `mapping_workflow`, `sdk_guide`.
**Verification:** Extract all backtick-quoted function-call patterns and verify each tool name is in the canonical set.

### Property 4: WAIT Directives Paired with 👉 Markers (Requirement 1, AC 1.2)

**Type:** Convention validation
**Property:** Every WAIT directive in the workflow is preceded by a bootcamper-facing question that uses the 👉 marker.
**Verification:** For each occurrence of "WAIT for response", verify that a 👉 marker appears in the preceding text block.

### Property 5: Front Matter Preserved (Requirement 6, AC 6.2)

**Type:** Structural validation
**Property:** The file begins with YAML front matter containing `inclusion: manual`.
**Verification:** Check that the file starts with `---` and contains `inclusion: manual` before the closing `---`.

## Alternatives Considered

### Alternative 1: Split into Multiple Steering Files

Instead of expanding the single file, create separate steering files for each new section (e.g., `module-07-conflict-resolution.md`, `module-07-troubleshooting.md`).

**Rejected because:** This would require the agent to load multiple files for a single module, increasing context overhead and breaking the convention that each module has one primary steering file. Other complex modules (Module 5, Module 6) keep all guidance in a single file.

### Alternative 2: Move Detailed Content to Module Documentation

Keep the steering file thin and move detailed guidance to `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`.

**Rejected because:** The module documentation is a user reference document, not agent behavioral instructions. The steering file needs to contain the workflow steps, decision gates, and agent instructions directly — the agent shouldn't have to cross-reference documentation to know what to do next.

### Alternative 3: Create a Companion Agent Guide in Development Docs

Put the expanded guidance in `senzing-bootcamp-power-development/guides/MODULE_7_AGENT_GUIDE.md`.

**Rejected because:** Development guides are not loaded at runtime. The agent needs this guidance during bootcamp execution, which means it must be in the steering file that gets loaded when Module 7 starts.
