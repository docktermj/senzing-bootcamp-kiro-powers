```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 8: QUERY AND VISUALIZE  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 8: Query and Visualize

> **Agent workflow:** The agent follows `steering/module-08-query-validation.md` for this module's step-by-step workflow.

## Overview

Module 8 focuses on creating query programs, search programs, overlap reports, and visualizations to explore entity resolution results.

**Focus:** Query resolved entities and visualize results.

## Prerequisites

- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source loaded)
- ✅ No critical loading errors
- ✅ Loading statistics reviewed
- ✅ Business requirements from Module 1 available

## Learning Objectives

By the end of this module, you will:

1. Understand Senzing query operations
2. Generate query programs for your use cases
3. Explore entity resolution results
4. Create overlap reports to analyze cross-source matching
5. Build visualizations of entity resolution results

## Key Concepts

### Query Types

> **Agent instruction:** Do not use the method signatures below — they may not match the
> current SDK version. Always use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> for query code, and `get_sdk_reference(topic='functions', version='current')` for method signatures.

Senzing provides several query operations. Use the MCP server to get current method signatures:

- **Get Entity by Record ID** — Find the entity that contains a specific record
- **Search by Attributes** — Find entities matching certain criteria
- **Get Entity by Entity ID** — Get a specific entity by its ID
- **Why Entities** — Understand why two records resolved together
- **How Entity** — See how an entity was built from records

## Workflow

### Step 1: Define Query Requirements

Based on Module 1 business problem, identify what queries you need:

**Customer 360 Example:**

- Find all records for a customer by name and email
- Get complete customer profile by customer ID
- Find potential duplicates for a new customer

**Fraud Detection Example:**

- Find all entities sharing an address
- Find entities with similar names but different SSNs
- Get relationship network for suspicious entity

**Data Migration Example:**

- Find which legacy records merged together
- Identify records that didn't match anything
- Get mapping from old IDs to new entity IDs

### Step 2: Generate Query Program

Generate a query program using the Senzing MCP server:

```text
Use: generate_scaffold
Parameters:
  language: <chosen_language>
  workflow: query
  version: current
```

The scaffold will include:

- SDK initialization
- Query operations
- Result formatting
- Error handling

### Step 3: Customize Query Program

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> to get the current query scaffold. Customize it for the user's specific use case
> (Customer 360, fraud detection, etc.) based on their Module 1 business problem.
> Use `get_sdk_reference(topic='flags', version='current')` for the correct query flags.
> Do not use the example code patterns in this section — they may use outdated method names or flag constants.

Customize the MCP-generated scaffold for your use case:

1. Set search attributes based on your business requirements
2. Choose appropriate query flags (use `get_sdk_reference` for current flags)
3. Format output for your stakeholders
4. Add error handling

### Step 4: Test Query Program

Run the query program with test cases:

Run the query program using the appropriate command for your chosen language.

Verify:

- Query returns expected results
- Output format is useful
- Performance is acceptable (< 100ms per query)
- Error handling works

## Query Examples

> **Agent instruction:** Do not use the example code below. Generate current query code using:
>
> - `generate_scaffold(language='<chosen_language>', workflow='query', version='current')` for query patterns
> - `get_sdk_reference(topic='functions', filter='search_by_attributes', version='current')` for method details
> - `get_sdk_reference(topic='functions', filter='why_entities', version='current')` for match explanation
> - `get_sdk_reference(topic='flags', version='current')` for flag constants

Common query patterns (use MCP tools to generate current code):

- **Find Duplicates** — Get entity by record ID, list all records in the entity
- **Search for Customer** — Search by attributes (name, phone, email, etc.)
- **Explain Match** — Use why_entities to understand matching logic

## Validation Gates

Before proceeding to Module 9, verify:

- [ ] Query programs generated and tested
- [ ] All query types work correctly
- [ ] Query performance is acceptable (< 100ms)

## Success Indicators

Module 8 is complete when:

- Query programs work correctly
- Visualizations created for entity resolution results
- Ready for performance testing (Module 9) or production (if skipping 9-12)

## Common Issues

### Issue: Query Returns No Results

**Symptoms:** Search returns empty results
**Solutions:**

- Verify data was loaded successfully
- Check search attributes match loaded data
- Try broader search criteria
- Verify data source names are correct

### Issue: Too Many Results

**Symptoms:** Search returns hundreds of matches
**Solutions:**

- Add more specific search criteria
- Increase match threshold
- Use more distinguishing features

### Issue: Unexpected Matches

**Symptoms:** Records match that shouldn't
**Solutions:**

- Use the SDK's "why" method (via `get_sdk_reference`) to understand matching logic
- Review data quality from Module 5
- Check for missing or incorrect data
- Adjust matching configuration if needed

## Integration with Other Modules

- **From Module 7:** Queries loaded data from all sources
- **From Module 6:** Queries loaded data from single source
- **From Module 1:** Validates against business requirements
- **To Module 9:** Performance testing uses query programs
- **To Module 12:** Query programs included in deployment package

## File Locations

```text
project/
├── src/
│   └── query/
│       ├── customer_360.[ext]           # Customer lookup query
│       ├── find_duplicates.[ext]        # Duplicate detection
│       └── fraud_detection.[ext]        # Fraud queries
└── docs/
    └── query_specifications.md       # Query requirements
```

## Agent Behavior

When a user is in Module 8:

1. **Review business requirements:** Load Module 1 business problem
2. **Define query requirements:** What queries are needed?
3. **Generate query programs:** Use `generate_scaffold` with `query` workflow
4. **Customize programs:** Add specific query logic
5. **Save programs:** Save to `src/query/`
6. **Test queries:** Help user run and verify queries
7. **Validate gates:** Verify all gates before proceeding

## Related Documentation

- `POWER.md` - Module 8 overview
- `steering/module-08-query-validation.md` - Module 8 workflow
- `steering/agent-instructions.md` - Agent behavior for Module 8
- Use MCP: `reporting_guide(topic="evaluation")` for the 4-point ER evaluation framework
- Use MCP: `reporting_guide(topic="quality")` for precision/recall, split/merge detection, and review queues
- Use MCP: `reporting_guide(topic="export")` for SDK data extraction patterns
- Use MCP: `search_docs(query="testing best practices")` for overall testing approach

## Version History

- **v3.0.0** (2026-03-17): Module 8 refocused on query and validation with UAT framework enhancement
- **v4.0.0** (2026-04-17): Renumbered from Module 8 to Module 8 (merge of old Modules 4+5)
