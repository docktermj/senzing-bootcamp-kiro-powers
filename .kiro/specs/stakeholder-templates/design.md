# Design Document

## Overview

Create a module-aware stakeholder executive summary template and integrate it into the steering files for Modules 2, 8, and 12. The template lives in `senzing-bootcamp/templates/stakeholder_summary.md` and contains per-module placeholder guidance so the agent can fill it contextually at module completion.

## Architecture

### New File

- `senzing-bootcamp/templates/stakeholder_summary.md` — One-page executive summary template with six sections and module-specific placeholder blocks for Modules 2, 8, and 12.

### Modified Files

- `senzing-bootcamp/steering/module-02-business-problem.md` — Update step 13 to reference the template and instruct the agent to fill it with Module 2 context.
- `senzing-bootcamp/steering/module-08-query-validation.md` — Update the Stakeholder Summary section to reference the template and instruct the agent to fill it with Module 8 context.
- `senzing-bootcamp/steering/module-12-deployment.md` — Update step 15 to reference the template and instruct the agent to fill it with Module 12 context.

## Template Structure

The template uses a single-file design with conditional sections. The top of the template has the universal structure (all six sections with generic placeholders). Below that, three module-specific guidance blocks tell the agent what content to fill for each placeholder depending on which module just completed.

### Sections

1. **Problem Statement** — What business problem entity resolution addresses
2. **Approach** — How Senzing entity resolution is being applied
3. **Data Sources** — What data is involved
4. **Key Findings / Results** — What was discovered or achieved
5. **Next Steps** — What happens next
6. **ROI Considerations** — Business value and impact

### Module-Specific Guidance

Each guidance block maps to a module and tells the agent how to fill each placeholder:

- **Module 2 (Business Problem)**: Problem definition focus — problem description, planned approach, identified sources, expected outcomes, data collection next steps, projected value
- **Module 8 (Query & Validation)**: Results focus — original problem restated, resolution methodology, sources loaded with counts, match metrics and findings, performance/deployment next steps, measured impact
- **Module 12 (Deployment)**: Production focus — production problem statement, deployed architecture, production data sources, deployment metrics, operational next steps, production ROI

## Steering File Changes

### Module 2 (step 13)

Replace the inline stakeholder summary markdown block with a reference to the template. The agent reads the template, fills Module 2 placeholders, and saves to `docs/stakeholder_summary_module2.md`.

### Module 8 (Stakeholder Summary section)

Replace the inline stakeholder summary markdown block with a reference to the template. The agent reads the template, fills Module 8 placeholders, and saves to `docs/stakeholder_summary_module8.md`.

### Module 12 (step 15)

Replace the inline stakeholder summary mention with a reference to the template. The agent reads the template, fills Module 12 placeholders, and saves to `docs/stakeholder_summary_module12.md`.

## Correctness Properties

1. The file `senzing-bootcamp/templates/stakeholder_summary.md` exists and contains all six section headings in order: Problem Statement, Approach, Data Sources, Key Findings/Results, Next Steps, ROI Considerations.
2. The template contains placeholder tokens (bracketed text) that vary by module context.
3. The template contains distinct guidance blocks for Module 2, Module 8, and Module 12.
4. `senzing-bootcamp/steering/module-02-business-problem.md` contains a reference to `templates/stakeholder_summary.md`.
5. `senzing-bootcamp/steering/module-08-query-validation.md` contains a reference to `templates/stakeholder_summary.md`.
6. `senzing-bootcamp/steering/module-12-deployment.md` contains a reference to `templates/stakeholder_summary.md`.
7. Each steering file instructs the agent to save the filled template to the correct module-specific output path (`docs/stakeholder_summary_moduleN.md`).
