# Requirements Document

## Introduction

Module 8 of the Senzing Bootcamp covers query validation and User Acceptance Testing (UAT), but does not provide a structured test case template. Users are left to improvise their own test case formats, leading to inconsistent and incomplete UAT coverage. This feature adds a comprehensive UAT test case template at `senzing-bootcamp/templates/uat_test_cases.md` with structured sections for functional, performance, and data quality testing, plus sample test cases for common entity resolution scenarios. The Module 8 steering file is updated to reference the template.

## Glossary

- **Template**: A reusable Markdown document in `senzing-bootcamp/templates/` that bootcamp users copy into their project and fill in with project-specific data.
- **UAT_Test_Case_Template**: The Markdown file at `senzing-bootcamp/templates/uat_test_cases.md` containing structured test case sections and a tabular format for recording test results.
- **Module_8_Steering**: The agent steering file at `senzing-bootcamp/steering/module-08-query-validation.md` that guides agent behavior during Module 8.
- **Test_Case_Table**: A Markdown table with columns Test ID, Category, Description, Input, Expected Result, Actual Result, and Pass/Fail used to record individual test outcomes.
- **Functional_Tests**: Test cases that verify entity resolution correctness, including known matches, known non-matches, and edge cases.
- **Performance_Tests**: Test cases that measure query latency and throughput against defined thresholds.
- **Data_Quality_Tests**: Test cases that measure false positive rate and false negative rate of entity resolution results.
- **Sample_Test_Case**: A pre-filled example row in the Test_Case_Table demonstrating how to document a specific entity resolution test scenario.

## Requirements

### Requirement 1: UAT Test Case Template File

**User Story:** As a bootcamp user, I want a structured UAT test case template, so that I can systematically document and execute acceptance tests for my entity resolution project.

#### Acceptance Criteria

1. THE UAT_Test_Case_Template SHALL exist at the path `senzing-bootcamp/templates/uat_test_cases.md`.
2. THE UAT_Test_Case_Template SHALL contain a Purpose section explaining how to use the template.
3. THE UAT_Test_Case_Template SHALL contain Instructions directing the user to copy the file into their project `docs/` directory and fill in project-specific values.

### Requirement 2: Functional Test Section

**User Story:** As a bootcamp user, I want a functional test section in the template, so that I can verify entity resolution correctness for known matches, known non-matches, and edge cases.

#### Acceptance Criteria

1. THE UAT_Test_Case_Template SHALL contain a Functional Tests section with three subsections: Known Matches, Known Non-Matches, and Edge Cases.
2. WHEN a user fills in the Known Matches subsection, THE Test_Case_Table SHALL include columns for Test ID, Category, Description, Input, Expected Result, Actual Result, and Pass/Fail.
3. THE UAT_Test_Case_Template SHALL include at least two Sample_Test_Cases in the Known Matches subsection demonstrating common entity resolution match scenarios.
4. THE UAT_Test_Case_Template SHALL include at least two Sample_Test_Cases in the Known Non-Matches subsection demonstrating scenarios where records should remain separate entities.
5. THE UAT_Test_Case_Template SHALL include at least two Sample_Test_Cases in the Edge Cases subsection demonstrating boundary conditions such as missing fields or international characters.

### Requirement 3: Performance Test Section

**User Story:** As a bootcamp user, I want a performance test section in the template, so that I can measure query latency and throughput against defined thresholds.

#### Acceptance Criteria

1. THE UAT_Test_Case_Template SHALL contain a Performance Tests section with subsections for Query Latency and Throughput.
2. THE Test_Case_Table in the Performance Tests section SHALL include columns for Test ID, Category, Description, Input, Expected Result, Actual Result, and Pass/Fail.
3. THE UAT_Test_Case_Template SHALL include at least one Sample_Test_Case for query latency measurement.
4. THE UAT_Test_Case_Template SHALL include at least one Sample_Test_Case for throughput measurement.

### Requirement 4: Data Quality Test Section

**User Story:** As a bootcamp user, I want a data quality test section in the template, so that I can measure false positive and false negative rates of my entity resolution results.

#### Acceptance Criteria

1. THE UAT_Test_Case_Template SHALL contain a Data Quality Tests section with subsections for False Positive Rate and False Negative Rate.
2. THE Test_Case_Table in the Data Quality Tests section SHALL include columns for Test ID, Category, Description, Input, Expected Result, Actual Result, and Pass/Fail.
3. THE UAT_Test_Case_Template SHALL include at least one Sample_Test_Case for false positive rate measurement.
4. THE UAT_Test_Case_Template SHALL include at least one Sample_Test_Case for false negative rate measurement.

### Requirement 5: Test Summary Section

**User Story:** As a bootcamp user, I want a test summary section in the template, so that I can record aggregate pass/fail counts and overall UAT status.

#### Acceptance Criteria

1. THE UAT_Test_Case_Template SHALL contain a Test Summary section with a summary table showing total tests, passed, failed, and pass rate.
2. THE UAT_Test_Case_Template SHALL contain an Overall Status field with options for Pass, Conditional Pass, and Fail.
3. THE UAT_Test_Case_Template SHALL contain a Sign-Off section with placeholder fields for Business Owner, Technical Lead, and Date.

### Requirement 6: Module 8 Steering Reference

**User Story:** As a bootcamp agent, I want the Module 8 steering file to reference the UAT test case template, so that the agent directs users to the template during UAT test case creation.

#### Acceptance Criteria

1. WHEN the agent reaches the UAT test case creation step, THE Module_8_Steering SHALL instruct the agent to read the UAT_Test_Case_Template from `senzing-bootcamp/templates/uat_test_cases.md`.
2. THE Module_8_Steering SHALL instruct the agent to copy the template into the user project at `docs/uat_test_cases.md` and customize it with project-specific scenarios.
