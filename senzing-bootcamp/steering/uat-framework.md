---
inclusion: manual
---

# User Acceptance Testing (UAT) Framework

Validates that entity resolution meets business requirements before production.

## Process

| Phase | When | What |
| ----- | ---- | ---- |
| Planning | Before Module 8 | Define acceptance criteria from Module 2, identify scenarios, select test data, assign testers |
| Test Cases | Module 8 | Create test cases in `docs/uat_test_cases.yaml` |
| Execution | Module 8 | Run tests, compare actual vs expected, record PASS/FAIL |
| Issues | Module 8 | Track issues in `docs/uat_issues.yaml`, resolve, retest |
| Sign-off | After Module 8 | Get stakeholder approval in `docs/uat_signoff.md` |

## Test Case Format

```yaml
test_cases:
  - id: UAT-001
    scenario: Customer Deduplication
    test_data:
      - "John Smith, 123 Main St, john@email.com"
      - "J. Smith, 123 Main Street, jsmith@email.com"
    expected_result: Both records resolve to same entity
    acceptance_criteria: Confidence > 90%
    priority: High
    tester: jane.doe@company.com
```

## Key Scenarios

| Scenario | Test For |
| -------- | -------- |
| Duplicate Detection | Exact match, fuzzy match, partial match, no match |
| Data Quality | Missing data, invalid data, special characters, international names |
| Performance | Query response time < SLA, concurrent load, large result sets |
| Business Rules | Confidence thresholds, match rules, data source priority |

## UAT Executor

Use `generate_scaffold(workflow='query')` as a starting point. Build a program that:

1. Loads test cases from `docs/uat_test_cases.yaml`
2. Executes Senzing queries for each case
3. Compares actual vs expected
4. Generates `docs/uat_results.md` with pass/fail summary

Save to `src/query/uat_executor.[ext]`.

## Sign-off Template

Create `docs/uat_signoff.md` with: test period, total/passed/failed counts, issues found/resolved, acceptance criteria met (checklist), and signature lines for business owner, technical lead, and QA lead.

## Agent Behavior

1. Extract acceptance criteria from Module 2 business problem
2. Generate test case template in `docs/uat_test_cases.yaml`
3. Create UAT executor in `src/query/uat_executor.[ext]`
4. Guide user through test execution
5. Track issues in `docs/uat_issues.yaml`
6. Generate sign-off document when all tests pass
