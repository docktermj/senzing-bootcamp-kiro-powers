# Module 5: Map Your Data

> **Agent workflow:** The agent follows `steering/module-05-data-mapping.md` for this module's step-by-step workflow.

## Overview

Module 5 transforms your source data into Senzing's Generic Entity Specification (SGES) format. This is where you map your data fields to Senzing attributes, creating transformation programs for each data source.

**Prerequisites:** ✅ Module 4 complete (data quality evaluated)
**Output:** Transformation programs, mapped data files, quality validation

## Learning Objectives

By the end of this module, you will:

- Understand Senzing's data format (SGES)
- Map source fields to Senzing attributes
- Create transformation programs
- Validate data quality after mapping
- Track transformation lineage

## What You'll Do

1. Review data quality scores from Module 4
2. Use `mapping_workflow` MCP tool for each data source
3. Create transformation programs
4. Test on small samples
5. Validate with `analyze_record`
6. Generate full transformed datasets
7. Document mappings

## Senzing Generic Entity Specification (SGES)

SGES is Senzing's JSON format for entity data. Every record requires `DATA_SOURCE` and `RECORD_ID`. Beyond those, Senzing supports 100+ attributes across 30+ feature types for names, addresses, contact info, identifiers, dates, and more.

> **Agent instruction:** Do not list or hardcode Senzing attribute names. Always retrieve
> the current attribute reference from the MCP server:
>
> - Use `mapping_workflow` to interactively map fields (this is the primary workflow)
> - Use `search_docs(query="entity specification attributes", version="current")` for the full attribute reference
> - Use `download_resource(filename="senzing_entity_specification.md")` for the complete specification document
>
> Per the Senzing Information Policy, attribute names must come from the MCP server, not from training data or this document.

## Mapping Workflow

### Step 1: Start Mapping Workflow

Call `mapping_workflow` MCP tool with your data source:

```text
mapping_workflow(
    action="start",
    data_source_name="CUSTOMERS",
    sample_records=[...first 5-10 records...]
)
```

### Step 2: Interactive Mapping

The workflow guides you through 7 steps:

1. **Identify entity type** (person, organization, both)
2. **Map name fields** (full name or components)
3. **Map address fields** (full address or components)
4. **Map contact fields** (phone, email)
5. **Map identifiers** (SSN, tax ID, etc.)
6. **Map dates** (DOB, registration date)
7. **Review and confirm** mapping

### Step 3: Generate Transformation Program

The workflow generates a complete transformation program in your chosen language. The program will:

- Read source records from the input file (CSV, JSON, etc.)
- Map each source field to the corresponding Senzing attribute (e.g., `NAME_FULL`, `ADDR_FULL`, `PHONE_NUMBER`, `EMAIL_ADDRESS`)
- Set required fields: `DATA_SOURCE`, `RECORD_ID`, `RECORD_TYPE`
- Write Senzing JSON records to a JSONL output file

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` and the `mapping_workflow` output to generate the transformation program. Do not hand-code attribute names.

### Step 4: Test on Sample

Test with a small sample (10-100 records). Run the transformation program and inspect the first few lines of output:

```bash
head -5 data/transformed/customers.jsonl
```

### Step 5: Validate Quality

Use `analyze_record` to check format and quality:

```text
analyze_record(
    record=transformed_record,
    data_source="CUSTOMERS"
)
```

The `analyze_record` tool validates records against the Entity Specification and examines feature distribution, attribute coverage, and data quality.

Quality score should be > 70% after mapping.

### Step 6: Generate Full Dataset

Once validated, transform all records by running the transformation program on the full dataset.

### Step 7: Document Mapping

Create `docs/mapping_customers.md`:

```markdown
# Data Mapping: CUSTOMERS

**Date:** 2026-03-17
**Source:** data/raw/customers.csv
**Output:** data/transformed/customers.jsonl
**Program:** src/transform/transform_customers.[ext]

## Field Mappings

| Source Field | Senzing Attribute | Notes |
|--------------|-------------------|-------|
| customer_id | RECORD_ID | Unique identifier |
| full_name | NAME_FULL | Complete name |
| address | ADDR_FULL | Full address string |
| phone | PHONE_NUMBER | Primary phone |
| email | EMAIL_ADDRESS | Primary email |

## Data Quality

**Before Mapping:** 65/100
**After Mapping:** 82/100

**Improvements:**

- Standardized name format
- Cleaned phone numbers
- Validated email addresses

## Transformation Logic

- Names: Trimmed whitespace, title case
- Phones: Removed formatting, kept digits only
- Emails: Lowercased, validated format
- Addresses: No transformation (kept as-is)

## Sample Records

**Before:**

```json
{
  "customer_id": "12345",
  "full_name": "  JOHN SMITH  ",
  "phone": "(555) 123-4567",
  "email": "John.Smith@EXAMPLE.COM"
}
```

**After:**

```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "12345",
  "NAME_FULL": "John Smith",
  "PHONE_NUMBER": "5551234567",
  "EMAIL_ADDRESS": "john.smith@example.com"
}
```

## Statistics

- Records processed: 500,000
- Records with errors: 127 (0.025%)
- Average quality score: 82/100

```text

## File Locations

All transformation programs go in `src/transform/`:

```

src/transform/
├── transform_customers.[ext]
├── transform_vendors.[ext]
├── transform_employees.[ext]
└── utils.[ext]                    # Shared transformation utilities

```text

All transformed data goes in `data/transformed/`:

```

data/transformed/
├── customers.jsonl
├── vendors.jsonl
└── employees.jsonl

```text

## Common Mapping Patterns

> **Agent instruction:** The `mapping_workflow` MCP tool handles all field mapping
> interactively, including name vs. component patterns, address formats, multiple
> phones/emails, and date formatting. Do not hardcode attribute names in mapping
> examples. Instead, use `mapping_workflow` to generate the correct transformation
> code, and use `download_resource(filename="senzing_mapping_examples.md")` for
> the current mapping examples reference.

The `mapping_workflow` tool handles common patterns automatically:

- Full name vs. name components (first/last/middle)
- Full address vs. address components (street/city/state/zip)
- Multiple phones and emails
- Date format conversion
- Organization vs. person records

### Data Quality Improvements

General-purpose cleaning functions (not Senzing-specific) that improve matching quality. Implement these in your chosen language:

- **Name cleaning**: Remove extra whitespace, apply title case, handle special cases (McDonald, O'Brien)
- **Phone cleaning**: Extract digits only, remove country code prefix for domestic numbers
- **Email validation**: Lowercase, trim whitespace, validate against standard email pattern
- **Date normalization**: Convert to ISO format (YYYY-MM-DD)
- **Address standardization**: Normalize abbreviations (St→Street, Ave→Avenue)

> **Agent instruction:** Generate data cleaning utility functions in the bootcamper's chosen language. These are general-purpose string manipulation functions, not Senzing-specific.

## Transformation Lineage

Track how data flows through transformations:

```markdown
# Transformation Lineage: CUSTOMERS

**Source:** data/raw/customers.csv (downloaded 2026-03-15)
**Transformation:** src/transform/transform_customers.[ext] (v1.0)
**Output:** data/transformed/customers.jsonl (generated 2026-03-17)

**Transformations Applied:**

1. Name cleaning (whitespace, title case)
2. Phone standardization (digits only)
3. Email validation and lowercasing
4. Date format conversion (MM/DD/YYYY → YYYY-MM-DD)

**Quality Improvement:** 65 → 82 (+17 points)
```

## Success Criteria

✅ All non-compliant data sources mapped
✅ Transformation programs created and tested
✅ Quality validation passed (>70%)
✅ Transformed data files generated
✅ Mapping documentation complete
✅ Lineage tracked

## Common Issues

### Issue: Wrong attribute names

- ❌ Never guess attribute names
- ✅ Always use `mapping_workflow` tool

### Issue: Low quality scores after mapping

- Review `analyze_record` feedback
- Improve data cleaning logic
- Consider data enrichment

### Issue: Transformation errors

- Test on small sample first
- Add error handling
- Log problematic records

### Issue: Performance problems

- Process in batches
- Use multiprocessing for large files
- Optimize transformation logic

## Tips for Success

1. **Use mapping_workflow:** Don't hand-code attribute names
2. **Test small first:** 10-100 records before full dataset
3. **Validate quality:** Use `analyze_record`
4. **Document everything:** Future you will thank you
5. **Track lineage:** Know where data came from and how it changed
6. **Iterate:** Mapping is exploratory, refine as needed

## Next Steps

After completing Module 5:

- **Proceed to Module 0:** Set Up Senzing SDK
- **Or skip to Module 6:** If SDK already installed

## Related Documentation

- `POWER.md` - Bootcamp overview
- `steering/module-05-data-mapping.md` - Module 5 workflow
- `steering/data-lineage.md` - Lineage tracking guide
- Senzing SGES documentation (use `search_docs` MCP tool)

## Version History

- **v3.0.0** (2026-03-17): Module 5 documentation created
