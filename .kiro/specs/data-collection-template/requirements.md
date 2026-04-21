# Requirements Document

## Introduction

Module 3 (Data Collection) currently requires users to create their data inventory documentation from scratch. A standardized `data_collection_checklist.md` template will save time, ensure consistency across bootcamp sessions, and guide users through documenting all required data source metadata before proceeding to Module 4 (Data Quality Scoring). The template will live in `senzing-bootcamp/templates/` per the file storage policy, and the Module 3 steering file will be updated to reference it.

## Glossary

- **Template**: The markdown file at `senzing-bootcamp/templates/data_collection_checklist.md` that provides a pre-structured form for documenting data sources
- **Steering_File**: The agent workflow file at `senzing-bootcamp/steering/module-03-data-collection.md` that guides the AI agent through Module 3 steps
- **DATA_SOURCE**: The Senzing identifier string assigned to each data source for entity resolution (e.g., `CUSTOMERS`, `VENDORS`)
- **Data_Inventory_Table**: The markdown table within the Template where users record metadata for each data source
- **Validation_Checklist**: The section within the Template containing verification items that must pass before proceeding to Module 4
- **Bootcamper**: A user working through the Senzing Bootcamp modules

## Requirements

### Requirement 1: Create Data Collection Checklist Template File

**User Story:** As a bootcamper, I want a pre-built template for documenting my data sources, so that I do not have to create a data inventory from scratch.

#### Acceptance Criteria

1. THE Template SHALL exist at the path `senzing-bootcamp/templates/data_collection_checklist.md`
2. THE Template SHALL contain a Data_Inventory_Table with columns for source name, DATA_SOURCE identifier, record count, data format, file location, access method, update frequency, contact person, and data sensitivity level
3. THE Template SHALL include at least one example row in the Data_Inventory_Table demonstrating how to fill in each field
4. THE Template SHALL include a header section explaining the purpose of the checklist and when to use it during the bootcamp

### Requirement 2: Define Data Format Options

**User Story:** As a bootcamper, I want clear guidance on supported data formats, so that I can accurately document each source's format.

#### Acceptance Criteria

1. THE Template SHALL list the supported data format values as CSV, JSON, JSONL, XML, Excel, Parquet, DB (database export), and API (API endpoint)
2. THE Template SHALL present the supported format values in a reference section within the document

### Requirement 3: Include Validation Checklist for Module 4 Readiness

**User Story:** As a bootcamper, I want a validation checklist before moving to Module 4, so that I can confirm all data sources are properly collected and documented.

#### Acceptance Criteria

1. THE Validation_Checklist SHALL include a check item verifying that all data source files exist in the `data/raw/` directory
2. THE Validation_Checklist SHALL include a check item verifying that record counts have been confirmed for each data source
3. THE Validation_Checklist SHALL include a check item verifying that data formats are documented for each data source
4. THE Validation_Checklist SHALL include a check item verifying that DATA_SOURCE identifiers are assigned and follow Senzing naming conventions (uppercase, underscores, no spaces)
5. THE Validation_Checklist SHALL include a check item verifying that `docs/data_source_locations.md` has been created or updated
6. THE Validation_Checklist SHALL use markdown checkbox syntax so bootcampers can mark items as complete

### Requirement 4: Update Module 3 Steering File to Reference Template

**User Story:** As an AI agent running Module 3, I want the steering file to reference the data collection checklist template, so that I can offer it to the bootcamper at the appropriate step.

#### Acceptance Criteria

1. THE Steering_File SHALL reference the Template path `senzing-bootcamp/templates/data_collection_checklist.md` within the data source documentation step
2. THE Steering_File SHALL instruct the agent to offer copying the Template into the bootcamper's project `docs/` directory at the start of data source documentation
3. THE Steering_File SHALL retain all existing content without removal or alteration

### Requirement 5: Include Data Sensitivity Level Guidance

**User Story:** As a bootcamper, I want guidance on classifying data sensitivity, so that I can properly document privacy requirements for each source.

#### Acceptance Criteria

1. THE Template SHALL define data sensitivity levels as Public, Internal, Confidential, and Restricted
2. THE Template SHALL include a brief description of each sensitivity level in a reference section
