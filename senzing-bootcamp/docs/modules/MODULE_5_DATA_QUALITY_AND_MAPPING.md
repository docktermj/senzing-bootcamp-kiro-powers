```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 5: DATA QUALITY & MAPPING  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 5: Data Quality & Mapping

> **Agent workflow:** The agent follows `steering/module-05-data-quality-mapping.md` for this module's step-by-step workflow.

## Overview

Module 5 combines data quality assessment and data mapping into a single continuous workflow. First, you evaluate your data quality using automated scoring and metrics (Phase 1). Then, once quality thresholds are met, you transform your source data into Senzing's Generic Entity Specification format (Phase 2). This eliminates the artificial boundary between quality assessment and data profiling — the quality gate flows directly into the mapping workflow.

**Prerequisites:** ✅ Module 4 complete (data sources collected)
**Output:** Quality reports, transformation programs, mapped data files, quality validation

## Learning Objectives

By the end of this module, you will:

- Assess data quality using automated scoring (0-100 scale)
- Understand completeness, consistency, validity, and uniqueness metrics
- Generate visual quality dashboards
- Understand Senzing's data format (SGES)
- Map source fields to Senzing attributes
- Create transformation programs
- Validate data quality after mapping
- Track transformation lineage

## What You'll Do

### Phase 1 — Quality Assessment

1. Run automated quality scoring on each data source
2. Generate quality reports with scores and metrics
3. Create HTML dashboards for visualization
4. Review scores and apply quality thresholds
5. Iterate on data quality if below threshold

### Phase 2 — Data Mapping

6. Use `mapping_workflow` MCP tool for each data source
7. Create transformation programs
8. Test on small samples
9. Validate with `analyze_record`
10. Generate full transformed datasets
11. Document mappings and track lineage

---

## Phase 1: Quality Assessment

### Purpose

After collecting data sources in Module 4, you need to assess their quality before mapping. Phase 1 provides:

1. **Automated Quality Scoring** (0-100 scale)
2. **Attribute Completeness Metrics**
3. **Data Consistency Analysis**
4. **Visual Quality Dashboard**
5. **Actionable Recommendations**

### Quality Scoring System

#### Overall Quality Score (0-100)

The quality score is calculated from multiple factors:

```text
Quality Score = (
    Completeness Score × 0.40 +
    Consistency Score × 0.30 +
    Validity Score × 0.20 +
    Uniqueness Score × 0.10
)
```

#### Score Interpretation

- **90-100:** Excellent - Ready for entity resolution
- **75-89:** Good - Minor improvements recommended
- **60-74:** Fair - Moderate data quality issues
- **40-59:** Poor - Significant quality problems
- **0-39:** Critical - Major data quality work needed

### Quality Metrics

#### 1. Completeness Score (40% weight)

Measures how complete the data is:

```text
For each field in the dataset:
    field_completeness = (number of non-null, non-empty values / total records) × 100

Identify critical fields (name, id, address, phone, email, etc.)
completeness_score = average of field_completeness across all critical fields
If no critical fields are detected, average across all fields instead.
```

**Metrics:**

- Percentage of non-null values per field
- Critical field coverage
- Optional field coverage
- Empty string detection

#### 2. Consistency Score (30% weight)

Measures data format consistency:

```text
For each field type (phone, email, date, address):
    Detect all format variations present in the data
    Count how many records use the most common format
    consistency = (most common format count / total non-null values) × 100

consistency_score = average of all field consistency percentages
```

**Metrics:**

- Phone number format consistency
- Email format consistency
- Date format consistency
- Address format consistency
- Name format consistency (UPPER, lower, Title Case)

#### 3. Validity Score (20% weight)

Measures data validity:

```text
For each field type, apply validation rules:
    - Email: matches standard email pattern (user@domain.tld)
    - Phone: matches known phone formats (10 digits, dashed, international, etc.)
    - Date: falls within a reasonable date range
    - Postal code: matches expected postal code patterns
    - State/country: matches known state or country codes

For each field:
    valid_percentage = (number of valid values / total non-null values) × 100

validity_score = average of all valid_percentage values
```

**Metrics:**

- Email format validity
- Phone number validity
- Date range validity
- Postal code validity
- State/country code validity

#### 4. Uniqueness Score (10% weight)

Measures duplicate detection within source:

```text
Count total records
Count exact duplicate records (rows that are identical across all fields)
Optionally detect fuzzy duplicates (near-matches)

uniqueness_score = ((total records - exact duplicates - fuzzy duplicates) / total records) × 100
```

**Metrics:**

- Exact duplicate percentage
- Fuzzy duplicate percentage
- ID uniqueness
- Record-level uniqueness

### Automated Quality Assessment

#### Data Quality Scorer — Algorithm Description

The data quality scorer is a tool that reads a source data file, analyzes it across the four quality dimensions above, and produces a structured report. Here is what it does:

##### Inputs

- A source data file (CSV, JSON, or JSONL format)

##### Processing Steps

```text
1. LOAD DATA
   Read the source file into a tabular structure (rows and columns).

2. IDENTIFY CRITICAL FIELDS
   Scan column names for patterns that indicate entity resolution relevance:
   - Names (any column containing "name")
   - Identifiers (any column containing "id")
   - Addresses (any column containing "address")
   - Contact info (columns containing "phone", "email")
   - Personal identifiers (columns containing "ssn", "dob", "birth")

3. CALCULATE COMPLETENESS
   For each column:
     - Count non-null values
     - Count non-empty values (exclude whitespace-only strings)
     - Record null count and empty count
   Compute overall completeness as the average non-empty percentage
   across critical fields (or all fields if no critical fields found).

4. CALCULATE CONSISTENCY
   For phone columns:
     - Classify each value into format categories:
       10 digits, dashed (XXX-XXX-XXXX), parenthesized ((XXX) XXX-XXXX),
       international (+XXXXXXXXXXX), or other
     - Consistency = percentage of values matching the most common format
   For email columns:
     - Check each value against standard email pattern
     - Consistency = percentage of valid emails
   For date columns:
     - Classify each value into format categories:
       ISO (YYYY-MM-DD), US (MM/DD/YYYY), EU (DD-MM-YYYY), or other
     - Consistency = percentage of values matching the most common format
   Overall consistency = average across all checked fields.

5. CALCULATE VALIDITY
   For email columns:
     - Validate against standard email pattern
   For phone columns:
     - Validate against known phone number patterns
   Overall validity = average valid percentage across all checked fields.

6. CALCULATE UNIQUENESS
   - Count exact duplicate rows
   - For ID columns, count unique vs duplicate IDs
   - Uniqueness score = (total - duplicates) / total × 100

7. COMPUTE OVERALL SCORE
   overall_score = completeness × 0.40 + consistency × 0.30
                 + validity × 0.20 + uniqueness × 0.10

8. ASSIGN GRADE
   90-100 → A (Excellent)
   75-89  → B (Good)
   60-74  → C (Fair)
   40-59  → D (Poor)
   0-39   → F (Critical)

9. GENERATE RECOMMENDATIONS
   - If completeness < 80: list the incomplete fields
   - If consistency < 80: recommend standardizing formats
   - If validity < 80: recommend fixing invalid data
   - If uniqueness < 95: recommend removing duplicates
   - If all scores are high: "Data quality is excellent! Ready for entity resolution."
```

##### Outputs

A structured report (JSON or equivalent) containing:

- `overall_score` — numeric score 0-100
- `grade` — letter grade with description
- `completeness` — score and per-field details
- `consistency` — score and per-field details
- `validity` — score and per-field details
- `uniqueness` — score, total records, unique records, duplicate count
- `recommendations` — list of actionable improvement suggestions
- `metadata` — data source path, total records, total fields, field names

> **Agent instruction:** Use `generate_scaffold` with the bootcamper's chosen language to generate data quality analysis code, or implement the scoring algorithm described above in the chosen language.

### Usage

Run the data quality scorer on your source data file and optionally specify an output path for the report:

```text
Run the data quality scorer on your source data file.
  Input:  your source data file (e.g., data/raw/customers.csv)
  Output: a quality report file (e.g., docs/quality_customers.json)

Then inspect the report — look at the overall_score field to get a quick summary.
```

### Visual Quality Dashboard

The quality scorer can also produce a visual HTML dashboard. The dashboard should contain:

- **Overall Quality Score** — displayed prominently with color coding by grade (green for A, yellow for C, red for F, etc.)
- **Component Score Bars** — a progress bar for each of the four dimensions:
  - Completeness (40% weight)
  - Consistency (30% weight)
  - Validity (20% weight)
  - Uniqueness (10% weight)
- **Data Source Metadata** — the source file name and record/field counts
- **Recommendations List** — the actionable recommendations from the report

The dashboard is a single self-contained HTML file with inline CSS, requiring no external dependencies. It should be human-readable when opened in any browser.

> **Agent instruction:** Generate the HTML dashboard in the bootcamper's chosen language, or produce the HTML file directly from the quality report JSON.

### Agent Behavior — Quality Assessment

When a user is in Phase 1 of this module, the agent should:

1. **Run quality scorer** on each data source
2. **Generate quality report** with scores and metrics
3. **Create HTML dashboard** for visualization
4. **Review scores** with user
5. **Provide recommendations** for improvement
6. **Document quality** in `docs/data_quality_report.md`
7. **Track quality scores** for comparison after mapping

### Quality Assessment Output Files

- `docs/data_quality_report.json` - Detailed quality metrics
- `docs/data_quality_dashboard.html` - Visual dashboard
- `docs/data_quality_report.md` - Summary documentation

### Quality Gate

Before proceeding to Phase 2 (Data Mapping), the quality gate must be evaluated:

- **≥80%:** Proceed directly to Phase 2
- **70–79%:** Warn user about quality concerns, proceed if they accept
- **<70%:** Strongly recommend fixing data quality issues before mapping; iterate on quality improvements

The quality gate is an internal checkpoint within this module — not a module boundary.

---

## Phase 2: Data Mapping

Phase 2 transforms your source data into Senzing's Generic Entity Specification (SGES) format. This is where you map your data fields to Senzing attributes, creating transformation programs for each data source.

### Senzing Generic Entity Specification (SGES)

SGES is Senzing's JSON format for entity data. Every record requires `DATA_SOURCE` and `RECORD_ID`. Beyond those, Senzing supports 100+ attributes across 30+ feature types for names, addresses, contact info, identifiers, dates, and more.

> **Agent instruction:** Do not list or hardcode Senzing attribute names. Always retrieve
> the current attribute reference from the MCP server:
>
> - Use `mapping_workflow` to interactively map fields (this is the primary workflow)
> - Use `search_docs(query="entity specification attributes", version="current")` for the full attribute reference
> - Use `download_resource(filename="senzing_entity_specification.md")` for the complete specification document
>
> Per the Senzing Information Policy, attribute names must come from the MCP server, not from training data or this document.

### Mapping Workflow

#### Step 1: Start Mapping Workflow

Call `mapping_workflow` MCP tool with your data source:

```text
mapping_workflow(
    action="start",
    data_source_name="CUSTOMERS",
    sample_records=[...first 5-10 records...]
)
```

#### Step 2: Interactive Mapping

The workflow guides you through 7 steps:

1. **Identify entity type** (person, organization, both)
2. **Map name fields** (full name or components)
3. **Map address fields** (full address or components)
4. **Map contact fields** (phone, email)
5. **Map identifiers** (SSN, tax ID, etc.)
6. **Map dates** (DOB, registration date)
7. **Review and confirm** mapping

#### Step 3: Generate Transformation Program

The workflow generates a complete transformation program in your chosen language. The program will:

- Read source records from the input file (CSV, JSON, etc.)
- Map each source field to the corresponding Senzing attribute (e.g., `NAME_FULL`, `ADDR_FULL`, `PHONE_NUMBER`, `EMAIL_ADDRESS`)
- Set required fields: `DATA_SOURCE`, `RECORD_ID`, `RECORD_TYPE`
- Write Senzing JSON records to a JSONL output file

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` and the `mapping_workflow` output to generate the transformation program. Do not hand-code attribute names.

#### Step 4: Test on Sample

Test with a small sample (10-100 records). Run the transformation program and inspect the first few lines of output:

```bash
head -5 data/transformed/customers.jsonl
```

#### Step 5: Validate Quality

Use `analyze_record` to check format and quality:

```text
analyze_record(
    record=transformed_record,
    data_source="CUSTOMERS"
)
```

The `analyze_record` tool validates records against the Entity Specification and examines feature distribution, attribute coverage, and data quality.

Quality score should be > 70% after mapping.

#### Step 6: Generate Full Dataset

Once validated, transform all records by running the transformation program on the full dataset.

#### Step 7: Document Mapping

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

### File Locations

All transformation programs go in `src/transform/`:

```text
src/transform/
├── transform_customers.[ext]
├── transform_vendors.[ext]
├── transform_employees.[ext]
└── utils.[ext]                    # Shared transformation utilities
```

All transformed data goes in `data/transformed/`:

```text
data/transformed/
├── customers.jsonl
├── vendors.jsonl
└── employees.jsonl
```

### Common Mapping Patterns

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

#### Data Quality Improvements

General-purpose cleaning functions (not Senzing-specific) that improve matching quality. Implement these in your chosen language:

- **Name cleaning**: Remove extra whitespace, apply title case, handle special cases (McDonald, O'Brien)
- **Phone cleaning**: Extract digits only, remove country code prefix for domestic numbers
- **Email validation**: Lowercase, trim whitespace, validate against standard email pattern
- **Date normalization**: Convert to ISO format (YYYY-MM-DD)
- **Address standardization**: Normalize abbreviations (St→Street, Ave→Avenue)

> **Agent instruction:** Generate data cleaning utility functions in the bootcamper's chosen language. These are general-purpose string manipulation functions, not Senzing-specific.

### Transformation Lineage

Use the transformation lineage template at `templates/transformation_lineage.md` to document the complete transformation chain for each data source. Copy it to `docs/transformation_lineage_[name].md` and fill in after completing the mapping.

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

---

## Phase 3: Test Load and Validate (Optional)

Phase 3 uses `mapping_workflow` steps 5–8 to give you immediate feedback on entity resolution quality — without leaving Module 5 or writing custom loading programs. This phase is optional: you can skip it and proceed directly to Module 6 if you prefer to write your own loading programs.

**Prerequisites:** Phase 2 complete for at least one data source, Senzing SDK installed (Module 2)

### Learning Objectives

By the end of Phase 3, you will:

- Verify that your mapping produces valid Senzing records through test loading
- Observe entity resolution results on your mapped data (match counts, entity counts, deduplication rate)
- Identify mapping issues before investing time in production loading programs

### What You'll Do

1. **SDK environment detection** — The `mapping_workflow` checks that the Senzing SDK is installed and a database is configured (step 5)
2. **Test data loading** — Load your transformed data into a fresh SQLite database to verify the mapping works end-to-end (step 6)
3. **Validation report** — Generate a report covering record counts, feature coverage, and data quality metrics (step 7)
4. **Entity resolution evaluation** — Review match counts, entity counts, and quality assessment to confirm the mapping produces good results (step 8)
5. **Decision gate** — Choose the shortcut path (→ Module 8) or the full path (→ Module 6)

### Output Files

- Validation report from `mapping_workflow` step 7
- Test SQLite database with loaded records
- Entity resolution evaluation results from step 8

### Shortcut Path

After completing Phase 3, a decision gate helps you choose the most efficient path forward:

- **Shortcut path (→ Module 8):** If you have a simple use case — single data source, small dataset (≤1000 records), no production requirements — the Phase 3 test load results may be sufficient. You can skip Modules 6–7 and proceed directly to Module 8 (Query & Visualize).
- **Full path (→ Module 6):** If you have production requirements, multiple data sources, or larger datasets, the full Module 6–7 path teaches production-quality loading patterns (error handling, throughput optimization, redo processing, incremental loading, multi-source orchestration).

The shortcut path is designed for bootcampers who want to see entity resolution results quickly without building production infrastructure. You can always return to Modules 6–7 later if your needs grow.

---

## Success Criteria

### Phase 1 — Quality Assessment

✅ Quality scorer run on each data source
✅ Quality reports generated with scores and metrics
✅ HTML dashboards created for visualization
✅ Quality gate evaluated (≥70% to proceed)

### Phase 2 — Data Mapping

✅ All non-compliant data sources mapped
✅ Transformation programs created and tested
✅ Quality validation passed (>70%)
✅ Transformed data files generated
✅ Mapping documentation complete
✅ Lineage tracked

### Phase 3 — Test Load and Validate (Optional)

✅ SDK environment detected (or Phase 3 skipped)
✅ Test data loaded into fresh SQLite database
✅ Validation report generated
✅ Entity resolution evaluation reviewed
✅ Decision gate completed (full path or shortcut path chosen)

## Common Issues

### Quality Assessment Issues

#### Issue: Low quality scores

- Review the recommendations in the quality report
- Focus on completeness first (highest weight at 40%)
- Standardize formats for consistency improvements
- Remove duplicates for uniqueness improvements

#### Issue: Dashboard not rendering

- Ensure the HTML file is self-contained with inline CSS
- Open in any modern browser
- Check that the quality report JSON was generated correctly

### Data Mapping Issues

#### Issue: Wrong attribute names

- ❌ Never guess attribute names
- ✅ Always use `mapping_workflow` tool

#### Issue: Low quality scores after mapping

- Review `analyze_record` feedback
- Improve data cleaning logic
- Consider data enrichment

#### Issue: Transformation errors

- Test on small sample first
- Add error handling
- Log problematic records

#### Issue: Performance problems

- Process in batches
- Use multiprocessing for large files
- Optimize transformation logic

## Tips for Success

1. **Assess quality first:** Run the quality scorer before mapping
2. **Meet the quality gate:** Aim for ≥70% before proceeding to mapping
3. **Use mapping_workflow:** Don't hand-code attribute names
4. **Test small first:** 10-100 records before full dataset
5. **Validate quality:** Use `analyze_record` after mapping
6. **Document everything:** Future you will thank you
7. **Track lineage:** Know where data came from and how it changed
8. **Iterate:** Both quality assessment and mapping are exploratory — refine as needed

## Next Steps

After completing this module:

- **Completed Phase 3 with shortcut path:** Proceed to Module 8 (Query & Visualize)
- **Completed Phase 3 with full path:** Proceed to Module 6 (Production-Quality Loading)
- **Skipped Phase 3:** Proceed to Module 2 (Set Up Senzing SDK) if not already done, then Module 6

## Related Documentation

- `POWER.md` - Bootcamp overview
- `steering/module-05-data-quality-mapping.md` - Module 5 workflow
- `steering/data-lineage.md` - Lineage tracking guide
- `docs/guides/QUALITY_SCORING_METHODOLOGY.md` - Quality scoring methodology
- Senzing SGES documentation (use `search_docs` MCP tool)

## Version History

- **v4.0.0** (2026-04-17): Merged Module 5 (Data Quality Scoring) and Module 5 (Data Mapping) into unified module
- **v3.0.0** (2026-03-17): Original Module 5 (quality scoring) and Module 5 (data mapping) created separately
