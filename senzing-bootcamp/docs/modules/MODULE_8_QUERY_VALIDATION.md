# Module 8: Query and Validate Results

> **Agent workflow:** The agent follows `steering/module-08-query-validation.md` for this module's step-by-step workflow.

## Overview

Module 8 focuses on creating query programs to explore entity resolution results and validating that the solution meets business requirements through User Acceptance Testing (UAT).

**Focus:** Query resolved entities and validate results against business requirements.

## Prerequisites

- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source loaded)
- ✅ No critical loading errors
- ✅ Loading statistics reviewed
- ✅ Business requirements from Module 2 available

## Learning Objectives

By the end of this module, you will:

1. Understand Senzing query operations
2. Generate query programs for your use cases
3. Explore entity resolution results
4. Create User Acceptance Test (UAT) cases
5. Validate results against business requirements
6. Get stakeholder sign-off

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

Based on Module 2 business problem, identify what queries you need:

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
> (Customer 360, fraud detection, etc.) based on their Module 2 business problem.
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

### Step 5: Create UAT Test Cases

Create User Acceptance Test cases based on business requirements. Use the UAT test case template at `templates/uat_test_cases.md` — copy it to `docs/uat_test_cases.md` and customize with your scenarios. See `steering/uat-framework.md` for detailed guidance.

**Quick UAT Template:**

```yaml
# docs/uat_test_cases.yaml
test_cases:
  - id: UAT-001
    scenario: Duplicate Customer Detection
    description: Verify duplicate customers are correctly identified
    test_data:
      - John Smith, 123 Main St, john@email.com
      - J. Smith, 123 Main Street, jsmith@email.com
    expected_result: Both records resolve to same entity
    acceptance_criteria: Confidence > 90%
    priority: High
    tester: jane.doe@company.com
    status: PENDING

  - id: UAT-002
    scenario: Different People Same Name
    description: Verify different people with same name stay separate
    test_data:
      - John Smith, 123 Main St, Boston, MA
      - John Smith, 456 Oak Ave, Seattle, WA
    expected_result: Two separate entities
    acceptance_criteria: Kept as separate entities
    priority: High
    tester: jane.doe@company.com
    status: PENDING
```

### Step 6: Execute UAT Tests

Execute each test case:

1. **Load test data** (if not already loaded)
2. **Run queries** to find test entities
3. **Compare results** to expected outcomes
4. **Document results** (PASS/FAIL)
5. **Log issues** for any failures

The UAT executor program should:

1. Load test cases from `docs/uat_test_cases.md`
2. For each test case, run the appropriate query against the Senzing engine
3. Compare actual results to expected outcomes
4. Record each result as PASS, FAIL, or PENDING with timestamps and tester info
5. Generate a summary report (`docs/uat_results.md`) showing total, passed, failed, and pending counts with percentages
6. Indicate overall status: all passed (ready for production), some failed (issues to resolve), or testing in progress

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> as a starting point, then build a UAT executor program that implements the above logic.
> Save it to `src/query/uat_executor.[ext]`.

### Step 7: Resolve Issues

For any failed tests:

1. **Analyze failure:** Why didn't it meet expectations?
2. **Identify root cause:** Data quality? Configuration? Logic?
3. **Implement fix:** Adjust transformation, configuration, or expectations
4. **Retest:** Run test again to verify fix
5. **Document resolution:** Record what was changed

Track issues in `docs/uat_issues.yaml`:

```yaml
issues:
  - id: UAT-ISSUE-001
    test_case: UAT-001
    severity: High
    description: False negative - duplicates not matched
    root_cause: Name abbreviation not handled
    resolution: Adjusted name matching configuration
    status: Resolved
    resolved_date: 2026-03-18
```

### Step 8: Get Sign-Off

Once all tests pass, get formal sign-off from stakeholders:

```markdown
# UAT Sign-Off Document

## Project
Senzing Entity Resolution - Customer 360

## UAT Summary
- **Test Period:** March 17-20, 2026
- **Total Test Cases:** 25
- **Passed:** 25 (100%)
- **Failed:** 0 (0%)

## Acceptance Criteria Met
✅ All duplicate customers correctly identified
✅ Different people with same name kept separate
✅ Query response time < 100ms
✅ Data quality score > 85%

## Sign-Off

**Business Owner:** _________________ Date: _______

**Technical Lead:** _________________ Date: _______

**Approval for Production:** ☐ Approved ☐ Conditional ☐ Rejected
```

## User Acceptance Testing (UAT)

UAT validates that the solution meets business requirements. See `steering/uat-framework.md` for comprehensive guidance.

### UAT Process Overview

1. **Planning:** Define acceptance criteria from Module 1
2. **Test Case Creation:** Create test cases for each scenario
3. **Test Execution:** Run tests and document results
4. **Issue Resolution:** Fix any failures
5. **Sign-Off:** Get stakeholder approval

### When to Load UAT Framework

Load `steering/uat-framework.md` when:

- Starting Module 8
- User asks about UAT or testing
- Preparing for production deployment
- Need stakeholder sign-off

**Agent behavior:** Mention UAT framework in Module 8. Load full guide if user wants detailed UAT process.

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
- [ ] UAT test cases created
- [ ] All UAT tests executed
- [ ] All critical tests pass
- [ ] Issues documented and resolved
- [ ] Stakeholder sign-off obtained (if required)

## Success Indicators

Module 8 is complete when:

- Query programs work correctly
- UAT tests pass
- Results meet business requirements
- Stakeholders approve solution
- Ready for performance testing (Module 9) or production (if skipping 9-11)

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
- Review data quality from Module 3
- Check for missing or incorrect data
- Adjust matching configuration if needed

### Issue: UAT Tests Fail

**Symptoms:** Results don't meet expectations
**Solutions:**

- Analyze root cause (data quality, configuration, expectations)
- Review transformation logic from Module 5
- Check data quality scores from Module 4
- Adjust expectations if they were unrealistic

## Integration with Other Modules

- **From Module 7:** Queries loaded data from all sources
- **From Module 6:** Queries loaded data from single source
- **From Module 2:** Validates against business requirements
- **To Module 9:** Performance testing uses query programs
- **To Module 12:** Query programs included in deployment package

## File Locations

```text
project/
├── src/
│   └── query/
│       ├── customer_360.[ext]           # Customer lookup query
│       ├── find_duplicates.[ext]        # Duplicate detection
│       ├── fraud_detection.[ext]        # Fraud queries
│       └── uat_executor.[ext]           # UAT test runner
├── docs/
│   ├── uat_test_cases.md              # UAT test cases
│   ├── uat_results.md                # UAT results report
│   ├── uat_issues.yaml               # Issues found during UAT
│   ├── uat_signoff.md                # Sign-off document
│   └── query_specifications.md       # Query requirements
└── logs/
    └── uat_execution.log             # UAT execution log
```

## Agent Behavior

When a user is in Module 8:

1. **Review business requirements:** Load Module 2 business problem
2. **Define query requirements:** What queries are needed?
3. **Generate query programs:** Use `generate_scaffold` with `query` workflow
4. **Customize programs:** Add specific query logic
5. **Save programs:** Save to `src/query/`
6. **Test queries:** Help user run and verify queries
7. **Create UAT test cases:** Generate `docs/uat_test_cases.md`
8. **Execute UAT tests:** Run tests and document results
9. **Track issues:** Log any failures in `docs/uat_issues.yaml`
10. **Generate reports:** Create UAT results report
11. **Get sign-off:** Create sign-off document if needed
12. **Validate gates:** Verify all gates before proceeding

**If user asks about UAT:** Load `steering/uat-framework.md` for detailed guidance.

**If user wants to skip UAT:** Explain importance but allow skipping for non-production projects.

## Related Documentation

- `POWER.md` - Module 8 overview
- `steering/module-08-query-validation.md` - Module 8 workflow
- `steering/agent-instructions.md` - Agent behavior for Module 8
- `steering/uat-framework.md` - Comprehensive UAT guidance (load on demand)
- Use MCP: `reporting_guide(topic="evaluation")` for the 4-point ER evaluation framework
- Use MCP: `reporting_guide(topic="quality")` for precision/recall, split/merge detection, and review queues
- Use MCP: `reporting_guide(topic="export")` for SDK data extraction patterns
- Use MCP: `search_docs(query="testing best practices")` for overall testing approach

## Version History

- **v3.0.0** (2026-03-17): Module 8 refocused on query and validation with UAT framework enhancement
