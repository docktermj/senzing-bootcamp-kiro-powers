# Design Document

## Overview

This feature adds a transformation lineage template to the Senzing Bootcamp Power and integrates it into the Module 5 steering workflow. The template provides a standardized way for bootcampers to document data transformations applied to each data source during the mapping phase.

## Architecture

### File Changes

1. **New file**: `senzing-bootcamp/templates/transformation_lineage.md` — the lineage template
2. **Modified file**: `senzing-bootcamp/steering/module-05-data-mapping.md` — add template reference at step 11

### Template Structure

The template follows the established pattern from `data_collection_checklist.md`:

```
# Transformation Lineage: [DATA_SOURCE]
├── Purpose
├── Instructions (numbered steps)
├── Source File Information (metadata fields)
├── Transformation Program (path, version)
├── Output File Information (metadata fields)
├── Record Count Summary (before/after table)
├── Field Mappings (table with example row)
├── Format Changes (table with example row)
├── Filters Applied (table with example row)
├── Quality Improvements (table with example row)
└── Validation Checklist (checkboxes)
```

### Steering Integration

Step 11 of `module-05-data-mapping.md` currently reads:

```
11. **Save and document:** Program in `src/transform/`, docs in `docs/mapping_[name].md` ...
```

This step will be extended to instruct the agent to have the bootcamper copy and fill in `templates/transformation_lineage.md` for the current data source, saving it as `docs/transformation_lineage_[name].md`.

## Correctness Properties

### Property 1: Template file exists at correct path (Req 1, AC 1)

Verify that `senzing-bootcamp/templates/transformation_lineage.md` exists and is a non-empty Markdown file.

### Property 2: Template contains all required sections (Req 1, AC 2-9; Req 2, AC 1-4)

Verify the template contains:
- A Purpose section
- An Instructions section with numbered steps
- Source file metadata fields: DATA_SOURCE name, record count, data format, extraction date, file path
- Transformation program fields: program path, version
- Output file metadata fields: record count, data format, generation date, file path
- A Field Mappings table with columns: Source Field, Senzing Attribute, Notes
- A Format Changes table with columns: Field Name, Original Format, Target Format, Reason
- A Filters Applied table with columns: Filter Description, Records Excluded, Reason
- A Quality Improvements table with columns: Action, Fields Affected, Quality Impact
- A Record Count Summary with: records in, records out, records rejected, rejection rate
- A Validation Checklist with Markdown checkboxes
- Example/placeholder rows in each table
- Instructions to copy the file into the project `docs/` directory

### Property 3: Module 5 steering references template (Req 3, AC 1-2)

Verify that `senzing-bootcamp/steering/module-05-data-mapping.md` step 11 contains:
- A reference to `templates/transformation_lineage.md`
- An instruction for the agent to have the bootcamper fill in the template for the current data source
