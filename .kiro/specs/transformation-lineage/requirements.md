# Requirements Document

## Introduction

Data flows through the Senzing Bootcamp from raw source files through transformation programs to loaded Senzing JSON, but there is no standardized template for documenting what transformations were applied and why. This feature adds a transformation lineage template (`senzing-bootcamp/templates/transformation_lineage.md`) that bootcampers copy into their project to document the full chain of data transformations per data source. The Module 5 steering file is updated to reference this template at the documentation step.

## Glossary

- **Transformation_Lineage_Template**: A Markdown template file stored at `senzing-bootcamp/templates/transformation_lineage.md` that bootcampers copy into their project to document data transformation history for a single data source.
- **Module_5_Steering**: The agent steering file at `senzing-bootcamp/steering/module-05-data-mapping.md` that defines the step-by-step workflow for data mapping.
- **Bootcamper**: A user completing the Senzing Bootcamp who transforms and loads data.
- **Field_Mapping**: A documented association between a source data field and a Senzing attribute.
- **Format_Change**: A documented alteration to a field's data representation during transformation (e.g., date format conversion, phone digit extraction).
- **Filter**: A documented rule that excludes records from the transformation output.
- **Quality_Improvement**: A documented data cleansing action that raises the quality score of transformed data.

## Requirements

### Requirement 1: Transformation Lineage Template File

**User Story:** As a bootcamper, I want a reusable template for documenting transformation lineage, so that I can consistently record what transformations were applied to each data source and why.

#### Acceptance Criteria

1. THE Transformation_Lineage_Template SHALL exist at the path `senzing-bootcamp/templates/transformation_lineage.md`.
2. THE Transformation_Lineage_Template SHALL contain a section for recording the source file path and source file metadata (DATA_SOURCE name, record count, data format, extraction date).
3. THE Transformation_Lineage_Template SHALL contain a section for recording the transformation program path and version.
4. THE Transformation_Lineage_Template SHALL contain a section for recording the output file path and output file metadata (record count, data format, generation date).
5. THE Transformation_Lineage_Template SHALL contain a table for documenting Field_Mapping entries with columns for source field, Senzing attribute, and mapping notes.
6. THE Transformation_Lineage_Template SHALL contain a table for documenting Format_Change entries with columns for field name, original format, target format, and reason.
7. THE Transformation_Lineage_Template SHALL contain a section for documenting Filter rules with columns for filter description, records excluded, and reason.
8. THE Transformation_Lineage_Template SHALL contain a section for documenting Quality_Improvement actions with columns for action description, fields affected, and quality impact.
9. THE Transformation_Lineage_Template SHALL contain a before/after record count summary showing records in, records out, records rejected, and rejection rate.
10. THE Transformation_Lineage_Template SHALL include instructions telling the Bootcamper to copy the file into their project `docs/` directory and fill in one copy per data source.

### Requirement 2: Template Style Consistency

**User Story:** As a bootcamper, I want the transformation lineage template to follow the same style as other bootcamp templates, so that the documentation experience is consistent.

#### Acceptance Criteria

1. THE Transformation_Lineage_Template SHALL include a Purpose section explaining when and why to use the template.
2. THE Transformation_Lineage_Template SHALL include an Instructions section with numbered steps for using the template.
3. THE Transformation_Lineage_Template SHALL include a Validation Checklist with checkboxes the Bootcamper completes before proceeding to the next module.
4. THE Transformation_Lineage_Template SHALL use Markdown tables with example placeholder rows demonstrating the expected format.

### Requirement 3: Module 5 Steering Reference

**User Story:** As a bootcamper, I want the Module 5 workflow to reference the transformation lineage template at the documentation step, so that I am prompted to fill it in after completing a mapping.

#### Acceptance Criteria

1. WHEN the Bootcamper reaches the save-and-document step (step 11) of the Module_5_Steering workflow, THE Module_5_Steering SHALL instruct the agent to have the Bootcamper fill in a copy of `templates/transformation_lineage.md` for the current data source.
2. THE Module_5_Steering SHALL reference the template path `templates/transformation_lineage.md` in the save-and-document step.
