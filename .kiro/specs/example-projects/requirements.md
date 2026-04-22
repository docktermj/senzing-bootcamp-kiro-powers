# Requirements Document

## Introduction

The example-projects feature provides three architectural blueprint directories under `senzing-bootcamp/examples/` that demonstrate project structure and workflow patterns for Senzing entity resolution at different complexity levels. These are reference architectures (not runnable code) that users can study or clone via `scripts/clone_example.py`. An index page (`examples/README.md`) ties them together.

## Glossary

- **Example_Project**: An architectural blueprint directory containing a README with project structure, data flow, workflow steps, and optionally sample CSV data
- **Clone_Script**: The Python script `scripts/clone_example.py` that copies an example project into a user's workspace
- **Examples_Index**: The `examples/README.md` file serving as the entry point listing all available example projects

## Requirements

### Requirement 1: Provide Architectural Blueprint Examples

**User Story:** As a bootcamp user, I want reference project blueprints at beginner, intermediate, and advanced levels, so that I can understand the expected project structure and workflow for my entity resolution project.

#### Acceptance Criteria

1. THE Example_Project system SHALL provide a `simple-single-source/` directory containing a README with project structure, data flow, transformation logic, and sample CSV data in `data/samples/customers_sample.csv`
2. THE Example_Project system SHALL provide a `multi-source-project/` directory containing a README with project structure, orchestration pattern, data flow, and sample CSV data in `data/samples/` (crm_sample.csv, ecommerce_sample.csv, support_sample.csv)
3. THE Example_Project system SHALL provide a `production-deployment/` directory containing a README with deployment architecture, infrastructure requirements, and a production checklist
4. THE Examples_Index SHALL list all three example projects with their path, use case, complexity level, and modules covered
5. THE Examples_Index SHALL include a comparison matrix showing differences across examples (data sources, database, records, modules, testing, monitoring, security, deployment)

### Requirement 2: Enable Cloning of Example Projects

**User Story:** As a bootcamp user, I want to clone an example project into my workspace, so that I can use it as a starting point for my own project.

#### Acceptance Criteria

1. THE Clone_Script SHALL present a numbered list of available example projects with name and description
2. WHEN a user selects an example, THE Clone_Script SHALL offer to merge into the current project or create a new directory
3. WHEN cloning into the current project, THE Clone_Script SHALL skip the example README.md to preserve the user's existing README
4. IF a destination directory already exists for a new-directory clone, THEN THE Clone_Script SHALL display an error and exit
