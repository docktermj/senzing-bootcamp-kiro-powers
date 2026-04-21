# Requirements Document

## Introduction

The Senzing Bootcamp Power currently lacks templates for sharing entity resolution results with non-technical stakeholders. Users need a reusable executive summary template that can be offered after key milestone modules (2, 8, and 12) so they can communicate progress, findings, and business value to managers and decision-makers without manually assembling summaries each time.

## Glossary

- **Template_Engine**: The stakeholder summary template file with module-aware placeholders that the agent fills based on which module was just completed
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that guides agent behavior during a specific module
- **Module_Completion_Flow**: The existing workflow triggered after any module completes, defined in `module-completion.md`
- **Placeholder**: A bracketed token in the template (e.g., `[module_number]`) that the agent replaces with context-specific content when generating a summary

## Requirements

### Requirement 1: Stakeholder Summary Template

**User Story:** As a bootcamp user, I want a one-page executive summary template, so that I can share entity resolution progress with non-technical stakeholders after key modules.

#### Acceptance Criteria

1. THE Template_Engine SHALL contain the following sections in order: Problem Statement, Approach, Data Sources, Key Findings/Results, Next Steps, ROI Considerations
2. THE Template_Engine SHALL include Placeholder tokens for module-specific content that the agent fills based on which module (2, 8, or 12) was just completed
3. WHEN the template is used after Module 2, THE Template_Engine SHALL provide Placeholder guidance focused on problem definition, identified data sources, and planned approach
4. WHEN the template is used after Module 8, THE Template_Engine SHALL provide Placeholder guidance focused on resolution results, match quality metrics, and validation findings
5. WHEN the template is used after Module 12, THE Template_Engine SHALL provide Placeholder guidance focused on deployment status, operational readiness, and production metrics
6. THE Template_Engine SHALL be stored at `senzing-bootcamp/templates/stakeholder_summary.md`

### Requirement 2: Module 2 Steering Integration

**User Story:** As a bootcamp user completing Module 2, I want the agent to offer me the stakeholder summary template, so that I can share the business problem definition with my team.

#### Acceptance Criteria

1. WHEN Module 2 reaches the stakeholder summary step (step 13), THE Steering_File for Module 2 SHALL reference the stakeholder summary template at `senzing-bootcamp/templates/stakeholder_summary.md`
2. WHEN the user accepts the stakeholder summary offer in Module 2, THE Steering_File SHALL instruct the agent to fill the template Placeholder tokens with Module 2 context and save the result to `docs/stakeholder_summary_module2.md`

### Requirement 3: Module 8 Steering Integration

**User Story:** As a bootcamp user completing Module 8, I want the agent to offer me the stakeholder summary template, so that I can share validation results with stakeholders.

#### Acceptance Criteria

1. WHEN Module 8 reaches the stakeholder summary section, THE Steering_File for Module 8 SHALL reference the stakeholder summary template at `senzing-bootcamp/templates/stakeholder_summary.md`
2. WHEN the user accepts the stakeholder summary offer in Module 8, THE Steering_File SHALL instruct the agent to fill the template Placeholder tokens with Module 8 context and save the result to `docs/stakeholder_summary_module8.md`

### Requirement 4: Module 12 Steering Integration

**User Story:** As a bootcamp user completing Module 12, I want the agent to offer me the stakeholder summary template, so that I can share deployment status with decision-makers.

#### Acceptance Criteria

1. WHEN Module 12 reaches the stakeholder summary step (step 15), THE Steering_File for Module 12 SHALL reference the stakeholder summary template at `senzing-bootcamp/templates/stakeholder_summary.md`
2. WHEN the user accepts the stakeholder summary offer in Module 12, THE Steering_File SHALL instruct the agent to fill the template Placeholder tokens with Module 12 context and save the result to `docs/stakeholder_summary_module12.md`
