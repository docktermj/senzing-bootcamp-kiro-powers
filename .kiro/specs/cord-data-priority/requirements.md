# Requirements Document

## Introduction

The Senzing Bootcamp currently recommends synthesized "test data" as the default option when a bootcamper does not have their own data. Senzing provides CORD (Collections Of Relatable Data) — curated, real-world-like datasets designed specifically for entity resolution evaluation. CORD data is higher quality and more representative than synthesized test data, making it a better default recommendation.

This feature establishes a clear data recommendation hierarchy across all bootcamp touchpoints: (1) the bootcamper's own data, (2) CORD data from Senzing, and (3) synthesized test data as a last resort. All user-facing messaging, steering files, and documentation will be updated to reflect this priority order, ensuring CORD is always presented before synthesized test data.

Reference: <https://senzing.com/senzing-ready-data-collections-cord/>

## Glossary

- **Agent**: The AI assistant executing the bootcamp steering files within the Kiro IDE.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **CORD**: Collections Of Relatable Data — curated sample datasets provided by Senzing for testing and evaluation of entity resolution. Available via the `get_sample_data` MCP tool and at <https://senzing.com/senzing-ready-data-collections-cord/>.
- **Synthesized_Test_Data**: Programmatically generated fake data created by a script when neither the bootcamper's own data nor CORD data is suitable.
- **Data_Recommendation_Hierarchy**: The priority order for suggesting data sources to a bootcamper: (1) bootcamper's own data, (2) CORD data, (3) synthesized test data.
- **Steering_File**: A Markdown file in `senzing-bootcamp/steering/` that guides the Agent's behavior during a specific module or workflow.
- **Onboarding_Flow**: The steering file `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding workflow.
- **POWER_MD**: The main power documentation file at `senzing-bootcamp/POWER.md` that describes the bootcamp to users.
- **Quick_Start_Guide**: The user-facing guide at `senzing-bootcamp/docs/guides/QUICK_START.md`.
- **Onboarding_Checklist**: The user-facing checklist at `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`.
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides tools including `get_sample_data` for downloading CORD datasets.

## Requirements

### Requirement 1: Establish Data Recommendation Hierarchy

**User Story:** As a Bootcamper without my own data, I want to be guided toward the best available data option in priority order, so that I use the most realistic and representative data for learning entity resolution.

#### Acceptance Criteria

1. WHEN a Bootcamper indicates they do not have their own data, THE Agent SHALL recommend CORD data as the primary alternative before mentioning synthesized test data.
2. THE Agent SHALL follow the Data_Recommendation_Hierarchy in this order: (1) ask if the Bootcamper has their own data, (2) recommend CORD data with a reference to <https://senzing.com/senzing-ready-data-collections-cord/>, (3) offer synthesized test data only if CORD data does not suffice.
3. WHEN recommending CORD data, THE Agent SHALL explain that CORD provides curated, real-world-like datasets designed for entity resolution evaluation.
4. THE Agent SHALL offer to generate synthesized test data only after the Bootcamper has declined or indicated that CORD data does not meet their needs.

### Requirement 2: Update Onboarding Flow Data Messaging

**User Story:** As a Bootcamper going through onboarding, I want to learn about CORD data availability early, so that I know high-quality sample data exists before I start working with data.

#### Acceptance Criteria

1. THE Onboarding_Flow SHALL mention CORD data availability in Step 4 (Bootcamp Introduction) before mentioning synthesized test data generation.
2. WHEN presenting data options during onboarding, THE Onboarding_Flow SHALL describe CORD as Senzing's curated data collections designed for entity resolution evaluation.
3. THE Onboarding_Flow SHALL include a reference to <https://senzing.com/senzing-ready-data-collections-cord/> when mentioning CORD data.
4. THE Onboarding_Flow SHALL position synthesized test data as a fallback option available if CORD data does not meet the Bootcamper's specific needs.

### Requirement 3: Update POWER.md Data Availability Messaging

**User Story:** As a Bootcamper reading the power overview, I want to see CORD data highlighted as the primary sample data option, so that I understand the best data resources available to me.

#### Acceptance Criteria

1. THE POWER_MD SHALL present CORD data as the primary recommendation for Bootcampers who do not have their own data.
2. THE POWER_MD SHALL include a reference to <https://senzing.com/senzing-ready-data-collections-cord/> when describing data availability.
3. THE POWER_MD SHALL mention synthesized test data generation as available only if CORD data does not suffice for the Bootcamper's needs.
4. THE POWER_MD SHALL retain the reference to the `get_sample_data` MCP tool for downloading CORD datasets.

### Requirement 4: Update Quick Start Guide Data Messaging

**User Story:** As a Bootcamper reading the quick start guide, I want to see CORD data mentioned as the primary data option, so that I know where to get quality sample data quickly.

#### Acceptance Criteria

1. THE Quick_Start_Guide SHALL recommend CORD data as the primary option for Bootcampers who do not have their own data.
2. THE Quick_Start_Guide SHALL position synthesized test data as a last-resort option after CORD.
3. THE Quick_Start_Guide SHALL include a reference to CORD or the `get_sample_data` tool for obtaining CORD datasets.

### Requirement 5: Update Module 4 Data Collection Steering

**User Story:** As a Bootcamper in the data collection module, I want the agent to recommend CORD data before offering to generate synthesized test data, so that I use the most representative data available.

#### Acceptance Criteria

1. WHEN a Bootcamper indicates they do not have data during Module 4, THE Steering_File for Module 4 SHALL instruct the Agent to recommend CORD data first.
2. THE Steering_File for Module 4 SHALL instruct the Agent to offer synthesized test data generation only after the Bootcamper has declined CORD data or stated that CORD does not meet their needs.
3. THE Steering_File for Module 4 SHALL include the CORD reference URL (<https://senzing.com/senzing-ready-data-collections-cord/>) in the data recommendation instructions.

### Requirement 6: Update Onboarding Checklist

**User Story:** As a Bootcamper reviewing the onboarding checklist, I want to see CORD data mentioned as the primary sample data option, so that the checklist is consistent with the rest of the bootcamp messaging.

#### Acceptance Criteria

1. THE Onboarding_Checklist SHALL mention CORD data as the primary sample data option for Bootcampers without their own data.
2. THE Onboarding_Checklist SHALL position synthesized test data as available if CORD data does not suffice.

### Requirement 7: Ensure Consistent Hierarchy Across All Touchpoints

**User Story:** As a developer maintaining the bootcamp power, I want all data recommendation messaging to follow the same hierarchy, so that the Bootcamper receives a consistent experience regardless of where they encounter data guidance.

#### Acceptance Criteria

1. WHEN any Steering_File, documentation file, or user-facing text in the senzing-bootcamp power recommends data to a Bootcamper without their own data, THE recommendation SHALL follow the Data_Recommendation_Hierarchy: own data first, CORD second, synthesized test data last.
2. THE senzing-bootcamp power SHALL NOT present synthesized test data as the primary or equal-priority recommendation alongside CORD data in any user-facing text.
3. WHEN the Agent generates a data generation script for synthesized test data, THE Agent SHALL first confirm that the Bootcamper has considered and declined CORD data.
