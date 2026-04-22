# Requirements Document

## Introduction

This spec retroactively documents three planning and design steering files that help Bootcampers select a design pattern, estimate project complexity, and choose a cloud provider. All three are manual-inclusion steering files loaded by the Agent at specific points in the bootcamp workflow. The design patterns gallery also has a user-facing companion guide.

## Glossary

- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Agent**: The AI assistant executing the bootcamp steering files.
- **Design_Patterns_Steering**: The steering file `steering/design-patterns.md` (inclusion: manual) presenting 10 entity resolution design patterns with use cases, matching criteria, and agent guidance for Module 2.
- **Design_Patterns_Guide**: The user-facing guide `docs/guides/DESIGN_PATTERNS.md` summarizing the 10 patterns and directing users to the steering file for full details.
- **Complexity_Estimator**: The steering file `steering/complexity-estimator.md` (inclusion: manual) providing a 6-dimension scoring model and time estimates based on data characteristics.
- **Cloud_Provider_Setup**: The steering file `steering/cloud-provider-setup.md` (inclusion: manual) guiding cloud provider selection at the Module 8→9 validation gate and persisting the choice to `config/bootcamp_preferences.yaml`.

## Requirements

### Requirement 1: Design Pattern Selection

**User Story:** As a Bootcamper, I want a gallery of entity resolution design patterns presented during Module 2, so that I can identify the pattern that best fits my business problem.

#### Acceptance Criteria

1. THE Design_Patterns_Steering SHALL present 10 entity resolution patterns (Customer 360, Fraud Detection, Data Migration, Compliance Screening, Marketing Dedup, Patient Matching, Vendor MDM, Claims Fraud, KYC/Onboarding, Supply Chain) with use case, key matching attributes, and typical ROI for each.
2. WHEN the Agent loads Design_Patterns_Steering during Module 2, THE Agent SHALL walk the Bootcamper through a decision flow (entity type, primary goal, one-time vs ongoing) to narrow down the best-fit pattern.
3. THE Design_Patterns_Guide SHALL list all 10 patterns in a summary table and direct the Bootcamper to the steering file for full details.

### Requirement 2: Complexity Estimation and Cloud Provider Selection

**User Story:** As a Bootcamper, I want personalized time estimates and cloud provider guidance, so that I can plan my remaining bootcamp work and production infrastructure.

#### Acceptance Criteria

1. THE Complexity_Estimator SHALL score each data source on 6 dimensions (format, volume, quality, mapping, structure, access) using a 1–3 point scale and map total scores to low/medium/high complexity with time estimates for Modules 5 and 6.
2. WHEN the Bootcamper reaches the Module 8→9 validation gate, THE Cloud_Provider_Setup SHALL prompt for a cloud provider choice (AWS, Azure, GCP, on-premises, or local) and persist the selection to `config/bootcamp_preferences.yaml` as `cloud_provider`.
3. IF the Bootcamper selects AWS, THEN THE Cloud_Provider_Setup SHALL recommend AWS CDK for infrastructure-as-code and suggest installing the CDK Kiro Power.
