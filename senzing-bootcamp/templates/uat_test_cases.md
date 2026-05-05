# UAT Test Cases

## Purpose

Use this template during **Module 8 (Query, Visualize, and Validate Results)** to systematically document and execute User Acceptance Testing for your entity resolution project. The template covers three testing dimensions:

- **Functional Tests** — Verify entity resolution correctness (known matches, known non-matches, edge cases)
- **Performance Tests** — Measure query latency and throughput against defined thresholds
- **Data Quality Tests** — Measure false positive rate and false negative rate

Each section uses a consistent table format so results are easy to compare, aggregate, and share with stakeholders.

## Instructions

1. Copy this file into your project: `docs/uat_test_cases.md`
2. Replace the sample test cases with scenarios specific to your data and business requirements
3. Fill in the **Actual Result** and **Pass/Fail** columns as you execute each test
4. Complete the **Test Summary** section after all tests are executed
5. Obtain sign-off from stakeholders in the **Sign-Off** section

---

## Functional Tests

Functional tests verify that entity resolution produces correct results. Organize tests into three categories: records that should match, records that should not match, and boundary conditions.

### Known Matches

Records that should resolve to the same entity.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| FN-001 | Known Match | Exact duplicate detection | Record A: "John Smith, 123 Main St, <john@email.com>" / Record B: "John Smith, 123 Main St, <john@email.com>" | Both records resolve to the same entity | | |
| FN-002 | Known Match | Name variation with same address | Record A: "John Smith, 123 Main St" / Record B: "J. Smith, 123 Main Street" | Both records resolve to the same entity | | |
| FN-003 | Known Match | Cross-source match on email | Source A: "John Smith, <john@email.com>" / Source B: "Jonathan Smith, <john@email.com>" | Both records resolve to the same entity | | |
| *(add row)* | | | | | | |

### Known Non-Matches

Records that should remain as separate entities.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| FN-010 | Known Non-Match | Same name, different address and DOB | Record A: "John Smith, 123 Main St, DOB 1980-01-15" / Record B: "John Smith, 456 Oak Ave, DOB 1995-07-22" | Records remain as separate entities | | |
| FN-011 | Known Non-Match | Similar name, different identifiers | Record A: "Robert Johnson, SSN ***-**-1234" / Record B: "Robert Johnson, SSN***-**-5678" | Records remain as separate entities | | |
| *(add row)* | | | | | | |

### Edge Cases

Boundary conditions that test entity resolution robustness.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| FN-020 | Edge Case | Missing name field | Record with address and email but no name | Record loads without error; matches on non-name features if applicable | | |
| FN-021 | Edge Case | International characters | Record A: "José García, Calle Mayor 5" / Record B: "Jose Garcia, Calle Mayor 5" | Both records resolve to the same entity | | |
| FN-022 | Edge Case | Single-field record | Record with only an email address | Record loads without error; matches only on email | | |
| *(add row)* | | | | | | |

---

## Performance Tests

Performance tests measure whether query operations meet latency and throughput requirements.

### Query Latency

Measure response time for individual query operations.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| PF-001 | Latency | Single entity lookup by record ID | `get_entity_by_record_id("CUSTOMERS", "1001")` | Response in < 100ms | | |
| PF-002 | Latency | Search by attributes (name + address) | `search_by_attributes({"NAME_FULL": "John Smith", "ADDR_FULL": "123 Main St"})` | Response in < 200ms | | |
| PF-003 | Latency | Why entities explanation | `why_entities(entity_id_1, entity_id_2)` | Response in < 500ms | | |
| *(add row)* | | | | | | |

### Throughput

Measure sustained query volume over a time window.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| PF-010 | Throughput | Sustained record lookups | 100 sequential `get_entity_by_record_id` calls | Complete all 100 queries in < 15 seconds | | |
| PF-011 | Throughput | Sustained attribute searches | 50 sequential `search_by_attributes` calls | Complete all 50 queries in < 20 seconds | | |
| *(add row)* | | | | | | |

---

## Data Quality Tests

Data quality tests measure the accuracy of entity resolution by checking false positive and false negative rates against a known truth set.

### False Positive Rate

Verify that records which should be separate entities are not incorrectly merged.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| DQ-001 | False Positive | Review sample of merged entities for incorrect matches | Random sample of 50 resolved entities with 2+ records | False positive rate < 5% (fewer than 3 of 50 entities contain incorrectly merged records) | | |
| DQ-002 | False Positive | Common-name collision check | Query entities for "John Smith" — verify distinct people are not merged | Each distinct person remains a separate entity | | |
| *(add row)* | | | | | | |

### False Negative Rate

Verify that records which should match are not incorrectly kept separate.

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |
| DQ-010 | False Negative | Review known duplicates for missed matches | Set of 20 known duplicate record pairs from source data | False negative rate < 5% (at least 19 of 20 pairs resolve to the same entity) | | |
| DQ-011 | False Negative | Cross-source linkage verification | 10 records known to exist in both Source A and Source B | All 10 cross-source pairs resolve to the same entity | | |
| *(add row)* | | | | | | |

---

## Test Summary

Complete this section after executing all test cases.

| Metric | Count |
| --- | --- |
| Total Tests | |
| Passed | |
| Failed | |
| Pass Rate | |

### Overall Status

Select one:

- [ ] **Pass** — All tests pass. Ready for production or next module.
- [ ] **Conditional Pass** — Minor failures that do not block progress. Document exceptions below.
- [ ] **Fail** — Critical failures require resolution before proceeding.

**Exceptions / Notes:**

[Document any conditional pass exceptions or failure details here]

---

## Sign-Off

| Role | Name | Date |
| --- | --- | --- |
| Business Owner | | |
| Technical Lead | | |
| QA Lead (optional) | | |

**Approval for Production:** [ ] Approved  [ ] Conditional  [ ] Rejected
