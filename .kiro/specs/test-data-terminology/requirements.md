# Requirements Document

## Introduction

The senzing-bootcamp power uses the phrase "mock data" in several steering files, documentation guides, and the main POWER.md file when referring to synthetic data generated for testing and learning purposes. Senzing's preferred terminology is "test data" or "sample data" — terms that better represent the purpose of the data (realistic, useful for validating entity resolution behavior) without the connotations of being fake or unreliable that "mock data" carries.

This feature replaces all instances of "mock data" with "test data" or "sample data" across the power's language, updates any script filenames that use the `mock` prefix, and updates existing tests that assert the old terminology.

## Glossary

- **Agent**: The AI assistant executing the bootcamp steering files within the Kiro IDE.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Steering_File**: A Markdown file in `senzing-bootcamp/steering/` that guides the Agent's behavior during a specific module or workflow.
- **Test_Data**: Synthetic or sample data used for testing and learning entity resolution. Senzing's preferred term (replaces "mock data").
- **Sample_Data**: An acceptable alternative to "test data" when referring to pre-built datasets (Las Vegas, London, Moscow).
- **POWER_MD**: The main power documentation file at `senzing-bootcamp/POWER.md` that describes the bootcamp to users.
- **Onboarding_Flow**: The steering file `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding workflow.
- **Quick_Start_Guide**: The user-facing guide at `senzing-bootcamp/docs/guides/QUICK_START.md`.
- **Onboarding_Checklist**: The user-facing checklist at `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`.
- **Test_Suite**: The pytest test files in `senzing-bootcamp/tests/` that validate steering file content.

## Requirements

### Requirement 1: Replace "Mock Data" Terminology in Steering Files

**User Story:** As a Bootcamper, I want the bootcamp to use the term "test data" or "sample data" instead of "mock data," so that the language accurately reflects the purpose and quality of the synthetic data provided.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL use the phrase "test data" or "sample data" in place of every occurrence of "mock data" within Step 4 (Bootcamp Introduction).
2. WHEN the Agent presents data availability information during onboarding, THE Agent SHALL describe the data as "test data" or "sample data" and SHALL NOT use the phrase "mock data."
3. THE Steering_File for Module 4 (data collection) SHALL NOT contain the phrase "mock data" in any agent instructions or user-facing text.

### Requirement 2: Replace "Mock Data" Terminology in Documentation Guides

**User Story:** As a Bootcamper reading the documentation, I want consistent terminology that uses "test data" or "sample data," so that I am not confused by different terms for the same concept.

#### Acceptance Criteria

1. THE POWER_MD SHALL use the phrase "test data" in place of "mock data" when describing data generation capabilities.
2. THE Quick_Start_Guide SHALL use the phrase "test data" in place of "mock data" when describing data availability.
3. THE Onboarding_Checklist SHALL use the phrase "test data" or "sample data" in place of "mock data" when describing data generation capabilities.

### Requirement 3: Update Script Naming Convention

**User Story:** As a Bootcamper, I want any data generation scripts to use the filename `generate_test_data.py` rather than `generate_mock_data.py`, so that the naming is consistent with Senzing's preferred terminology.

#### Acceptance Criteria

1. WHEN the Agent generates a data generation script for the Bootcamper, THE Agent SHALL name the file `generate_test_data.py` and SHALL NOT use the filename `generate_mock_data.py`.
2. WHEN the Agent references a data generation script in conversation or documentation, THE Agent SHALL use the term "test data generation script" and SHALL NOT use the term "mock data generation script."
3. IF a Steering_File contains instructions for generating a data script, THEN THE Steering_File SHALL reference the filename as `generate_test_data.py`.

### Requirement 4: Update Existing Tests to Reflect New Terminology

**User Story:** As a developer maintaining the bootcamp power, I want the test suite to validate the new terminology, so that regressions back to "mock data" are caught automatically.

#### Acceptance Criteria

1. WHEN the Test_Suite validates Step 4 content markers in `onboarding-flow.md`, THE Test_Suite SHALL assert the presence of "test data" or "sample data" instead of "mock data."
2. THE Test_Suite SHALL NOT contain assertions that check for the phrase "mock data" as expected content in any steering file.
3. WHEN a test validates that data availability information is present in a steering file, THE Test_Suite SHALL use a pattern that matches "test data" or "sample data" as the expected terminology.

### Requirement 5: Ensure No Residual "Mock Data" References

**User Story:** As a developer maintaining the bootcamp power, I want a guarantee that no file in the distributed power contains the phrase "mock data," so that the terminology is consistent throughout.

#### Acceptance Criteria

1. THE senzing-bootcamp power directory SHALL NOT contain the phrase "mock data" (case-insensitive) in any Markdown file (`.md`), Python file (`.py`), or YAML file (`.yaml`).
2. THE senzing-bootcamp power directory SHALL NOT contain any filename that includes the substring `mock_data` or `mock-data`.
3. IF a new steering file or documentation file is added that references synthetic data, THEN THE file SHALL use "test data" or "sample data" as the terminology.

