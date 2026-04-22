# Requirements Document

## Introduction

This spec retroactively documents two manual-inclusion steering files that provide data lineage tracking guidance and a user acceptance testing (UAT) framework for the Senzing Bootcamp. The data lineage steering file is loaded on demand during Modules 3 and 5 to guide lineage file creation and tracker utility patterns. The UAT framework steering file is loaded during Module 8 to guide test case creation, execution, and stakeholder sign-off. Both files are already implemented.

## Glossary

- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Data_Lineage_Steering**: The file `steering/data-lineage.md` providing data lineage tracking guidance including lineage file structure, example entries, tracker utility patterns, and compliance guidance.
- **Lineage_File**: The file `docs/data_lineage.yaml` maintained by the Bootcamper to record data flow from source through transformation, loading, and usage.
- **Lineage_Tracker**: A utility at `src/utils/lineage_tracker.[ext]` that reads/writes the Lineage_File with functions for tracking sources, transformations, loading, and usage.
- **UAT_Framework_Steering**: The file `steering/uat-framework.md` providing the UAT process, test case structure, pass/fail criteria, and stakeholder sign-off guidance.
- **UAT_Test_Cases**: The file `docs/uat_test_cases.yaml` containing structured test cases with scenario, test data, expected result, and acceptance criteria.
- **UAT_Executor**: A program at `src/query/uat_executor.[ext]` that loads test cases, executes queries, compares results, and generates a pass/fail report.

## Requirements

### Requirement 1: Data Lineage Tracking Guidance

**User Story:** As a Bootcamper, I want data lineage tracking guidance loaded on demand, so that I can record and trace data flow from source to destination for compliance and debugging.

#### Acceptance Criteria

1. THE Data_Lineage_Steering SHALL define the Lineage_File structure with four sections: sources, transformations, loading, and usage — each specifying which module populates it and what fields to record.
2. THE Data_Lineage_Steering SHALL include a YAML example entry demonstrating the sources and transformations sections with realistic field values.
3. THE Data_Lineage_Steering SHALL specify a Lineage_Tracker utility API with functions: track_source, track_transformation, track_loading, track_usage, get_lineage_for_source, and generate_lineage_report.
4. THE Data_Lineage_Steering SHALL include compliance guidance explaining how get_lineage_for_source supports GDPR/CCPA by showing the complete data flow for any record.
5. WHEN the Agent is executing Module 3 or Module 5, THE Agent SHALL load the Data_Lineage_Steering to guide lineage file creation and updates.

### Requirement 2: User Acceptance Testing Framework

**User Story:** As a Bootcamper, I want a UAT framework loaded during Module 8, so that I can validate entity resolution meets business requirements before production.

#### Acceptance Criteria

1. THE UAT_Framework_Steering SHALL define a five-phase process: planning, test cases, execution, issues, and sign-off — each specifying when it occurs and what it produces.
2. THE UAT_Framework_Steering SHALL specify the UAT_Test_Cases YAML format with fields: id, scenario, test_data, expected_result, acceptance_criteria, priority, and tester.
3. THE UAT_Framework_Steering SHALL define key test scenarios covering duplicate detection, data quality, performance, and business rules.
4. THE UAT_Framework_Steering SHALL specify a sign-off template with test period, pass/fail counts, issues summary, acceptance checklist, and signature lines for business owner, technical lead, and QA lead.
5. WHEN the Agent is executing Module 8, THE Agent SHALL load the UAT_Framework_Steering to guide test case creation, execution, and sign-off.
