# Design Document

## Overview

This feature adds a UAT test case template to the Senzing Bootcamp Power's templates directory and updates the Module 8 steering file to reference it. The template provides structured sections for functional, performance, and data quality testing with a consistent table format and sample test cases for common entity resolution scenarios.

## Architecture

### File Changes

1. **New file**: `senzing-bootcamp/templates/uat_test_cases.md` — The UAT test case template
2. **Modified file**: `senzing-bootcamp/steering/module-08-query-validation.md` — Add template reference at the UAT test case creation step

### Template Structure

```
uat_test_cases.md
├── Purpose
├── Instructions
├── Functional Tests
│   ├── Known Matches (Test_Case_Table + samples)
│   ├── Known Non-Matches (Test_Case_Table + samples)
│   └── Edge Cases (Test_Case_Table + samples)
├── Performance Tests
│   ├── Query Latency (Test_Case_Table + samples)
│   └── Throughput (Test_Case_Table + samples)
├── Data Quality Tests
│   ├── False Positive Rate (Test_Case_Table + samples)
│   └── False Negative Rate (Test_Case_Table + samples)
├── Test Summary
│   ├── Summary Table
│   └── Overall Status
└── Sign-Off
```

### Test Case Table Format

Every test section uses the same 7-column table:

| Test ID | Category | Description | Input | Expected Result | Actual Result | Pass/Fail |
| --- | --- | --- | --- | --- | --- | --- |

- **Test ID**: Unique identifier using prefix convention (FN for functional, PF for performance, DQ for data quality)
- **Category**: Sub-category within the section (e.g., "Known Match", "Latency")
- **Description**: What the test verifies
- **Input**: Test data or query parameters
- **Expected Result**: What should happen
- **Actual Result**: Filled in during test execution (placeholder in template)
- **Pass/Fail**: Filled in during test execution (placeholder in template)

### Steering File Modification

The Module 8 steering file step 4 ("Create UAT test cases") will be updated to:
1. Instruct the agent to read the template from `senzing-bootcamp/templates/uat_test_cases.md`
2. Copy it into the user's project at `docs/uat_test_cases.md`
3. Customize sample test cases with project-specific scenarios from Module 2

## Correctness Properties

### Property 1: Template file exists at correct path (Req 1.1)
- **Type**: Example test
- **Verify**: File `senzing-bootcamp/templates/uat_test_cases.md` exists

### Property 2: Template contains all required top-level sections (Req 1.2, 1.3, 2.1, 3.1, 4.1, 5.1, 5.3)
- **Type**: Example test
- **Verify**: Template contains headings for Purpose, Instructions, Functional Tests, Performance Tests, Data Quality Tests, Test Summary, and Sign-Off

### Property 3: Functional Tests section has three subsections with sample data (Req 2.1–2.5)
- **Type**: Example test
- **Verify**: Known Matches subsection has at least 2 sample rows, Known Non-Matches has at least 2, Edge Cases has at least 2

### Property 4: All test tables use the 7-column format (Req 2.2, 3.2, 4.2)
- **Type**: Example test
- **Verify**: Every Test_Case_Table header row contains: Test ID, Category, Description, Input, Expected Result, Actual Result, Pass/Fail

### Property 5: Performance Tests section has latency and throughput samples (Req 3.1, 3.3, 3.4)
- **Type**: Example test
- **Verify**: Query Latency subsection has at least 1 sample row, Throughput has at least 1

### Property 6: Data Quality Tests section has FP and FN rate samples (Req 4.1, 4.3, 4.4)
- **Type**: Example test
- **Verify**: False Positive Rate subsection has at least 1 sample row, False Negative Rate has at least 1

### Property 7: Test Summary contains summary table and status options (Req 5.1, 5.2)
- **Type**: Example test
- **Verify**: Summary table has Total/Passed/Failed/Pass Rate columns; Overall Status lists Pass, Conditional Pass, Fail

### Property 8: Sign-Off section has required placeholders (Req 5.3)
- **Type**: Example test
- **Verify**: Sign-Off section contains Business Owner, Technical Lead, and Date placeholders

### Property 9: Module 8 steering references template (Req 6.1, 6.2)
- **Type**: Example test
- **Verify**: `module-08-query-validation.md` contains reference to `senzing-bootcamp/templates/uat_test_cases.md` and instruction to copy to `docs/uat_test_cases.md`
