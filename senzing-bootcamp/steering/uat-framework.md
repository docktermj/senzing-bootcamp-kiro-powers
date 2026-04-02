---
inclusion: manual
---

# User Acceptance Testing (UAT) Framework

## Overview

UAT validates that the entity resolution solution meets business requirements and user expectations before production deployment.

## Purpose

- **Validate business requirements** are met
- **Verify results** match expectations
- **Get stakeholder sign-off** before production
- **Identify issues** before they impact users
- **Document acceptance** criteria

## UAT Process

### Phase 1: Planning (Before Module 8)

1. **Define acceptance criteria** from Module 2 business problem
2. **Identify test scenarios** based on use cases
3. **Select test data** representative of production
4. **Assign testers** (business users, not developers)
5. **Create test schedule**

### Phase 2: Test Case Creation (Module 8)

Create test cases for each scenario:

```yaml
# docs/uat_test_cases.yaml
test_cases:
  - id: UAT-001
    scenario: Customer Deduplication
    description: Verify duplicate customers are correctly identified
    test_data:
      - John Smith, 123 Main St, john@email.com
      - J. Smith, 123 Main Street, jsmith@email.com
    expected_result: Both records resolve to same entity
    acceptance_criteria: >
      System identifies these as the same person with confidence > 90%
    priority: High
    tester: jane.doe@company.com

  - id: UAT-002
    scenario: Different People with Same Name
    description: Verify different people with same name stay separate
    test_data:
      - John Smith, 123 Main St, Boston, MA
      - John Smith, 456 Oak Ave, Seattle, WA
    expected_result: Two separate entities
    acceptance_criteria: >
      System keeps these as separate entities due to different addresses
    priority: High
    tester: jane.doe@company.com
```

### Phase 3: Test Execution (Module 8)

Execute tests and document results. The UAT executor program should:

1. Load test cases from `docs/uat_test_cases.yaml`
2. For each test case:
   - Execute the appropriate Senzing query (search by attributes, get entity, etc.)
   - Compare actual results to expected outcomes
   - Record status (PASS, FAIL, PENDING) with tester info and timestamp
3. Generate a summary report (`docs/uat_results.md`) showing:
   - Total tests, passed count, failed count, pending count with percentages
   - Per-test details: status icon, scenario, tester, date, actual result, notes
   - Overall verdict: all passed (ready for production), some failed (issues to resolve), or in progress

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> as a starting point, then build a UAT executor that implements the above logic.
> Save it to `src/query/uat_executor.[ext]`.

### Phase 4: Issue Resolution

Track and resolve issues found during UAT:

```yaml
# docs/uat_issues.yaml
issues:
  - id: UAT-ISSUE-001
    test_case: UAT-001
    severity: High
    description: False negative - duplicates not matched
    details: >
      John Smith and J. Smith should match but don't.
      Confidence score is only 65%, below threshold.
    root_cause: Name abbreviation not handled properly
    resolution: >
      Adjusted name matching rules to handle abbreviations.
      Retested - now matches with 92% confidence.
    status: Resolved
    resolved_date: 2026-03-18
```

### Phase 5: Sign-Off

Get formal acceptance:

```markdown
# UAT Sign-Off Document

## Project
Senzing Entity Resolution - Customer 360

## UAT Summary
- **Test Period**: March 17-20, 2026
- **Total Test Cases**: 25
- **Passed**: 25 (100%)
- **Failed**: 0 (0%)
- **Issues Found**: 3
- **Issues Resolved**: 3

## Acceptance Criteria Met
✅ All duplicate customers correctly identified
✅ Different people with same name kept separate
✅ Query response time < 100ms
✅ Data quality score > 85%
✅ No critical security issues

## Sign-Off

**Business Owner**: _________________ Date: _______
Jane Doe, VP Customer Data

**Technical Lead**: _________________ Date: _______
John Smith, Data Engineering Manager

**QA Lead**: _________________ Date: _______
Alice Johnson, QA Manager

## Approval for Production Deployment
☐ Approved - Ready for production
☐ Conditional - Resolve issues first
☐ Rejected - Major issues found

**Notes**: _________________________________________________
```

## UAT Test Scenarios

### Scenario 1: Duplicate Detection

```yaml
scenario: Duplicate Detection
test_cases:
  - Exact match (same name, address, phone)
  - Fuzzy match (typos, abbreviations)
  - Partial match (some fields match)
  - No match (different people)
```

### Scenario 2: Data Quality

```yaml
scenario: Data Quality
test_cases:
  - Missing data handling
  - Invalid data handling
  - Special characters
  - International names/addresses
```

### Scenario 3: Performance

```yaml
scenario: Performance
test_cases:
  - Query response time < SLA
  - Concurrent user load
  - Large result sets
  - Peak load handling
```

### Scenario 4: Business Rules

```yaml
scenario: Business Rules
test_cases:
  - Confidence thresholds
  - Match rules
  - Data source priority
  - Relationship types
```

## UAT Checklist

### Pre-UAT

- [ ] Test environment ready
- [ ] Test data prepared
- [ ] Test cases documented
- [ ] Testers identified and trained
- [ ] Test schedule created
- [ ] Issue tracking system ready

### During UAT

- [ ] All test cases executed
- [ ] Results documented
- [ ] Issues logged
- [ ] Issues prioritized
- [ ] Critical issues resolved
- [ ] Retesting completed

### Post-UAT

- [ ] UAT report generated
- [ ] All issues resolved or accepted
- [ ] Sign-off obtained
- [ ] Lessons learned documented
- [ ] Production readiness confirmed

## UAT Roles

**Business Owner**:

- Define acceptance criteria
- Review test results
- Provide sign-off

**Test Lead**:

- Create test cases
- Coordinate testing
- Track issues
- Generate reports

**Testers** (Business Users):

- Execute test cases
- Document results
- Report issues
- Validate fixes

**Development Team**:

- Support testing
- Fix issues
- Retest fixes
- Document resolutions

## Agent Behavior

When implementing UAT in Module 8:

1. **Review business problem** from Module 1
2. **Extract acceptance criteria** from requirements
3. **Generate test case template** in `docs/uat_test_cases.yaml`
4. **Create test executor script** in `src/testing/uat_executor.[ext]`
5. **Prepare test data** from real or synthetic sources
6. **Guide user through test execution**
7. **Track issues** in `docs/uat_issues.yaml`
8. **Generate UAT report** in `docs/uat_results.md`
9. **Create sign-off document** in `docs/uat_signoff.md`
10. **Verify all criteria met** before proceeding to Module 9

## When to Load This Guide

Load this guide when:

- Starting Module 8 (query and validation)
- User asks about UAT or testing
- Preparing for production deployment
- Need stakeholder sign-off

## Related Documentation

- `POWER.md` - Module 8 overview
- `steering/module-08-query-validation.md` - Module 8 workflow
- Use MCP: `search_docs(query="testing best practices")` for overall testing approach

## Version History

- **v3.0.0** (2026-03-17): UAT framework created for Module 8
