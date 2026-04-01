# Module 4: Evaluate Data Quality with Automated Scoring

> **Agent workflow:** The agent follows `steering/module-04-data-quality.md` for this module's step-by-step workflow.

## Overview

Module 4 evaluates data quality using automated scoring and metrics. This module provides objective measurements to help you understand data readiness for entity resolution.

## Purpose

After collecting data sources in Module 3, you need to assess their quality before mapping. Module 4 provides:

1. **Automated Quality Scoring** (0-100 scale)
2. **Attribute Completeness Metrics**
3. **Data Consistency Analysis**
4. **Visual Quality Dashboard**
5. **Actionable Recommendations**

## Quality Scoring System

### Overall Quality Score (0-100)

The quality score is calculated from multiple factors:

```text
Quality Score = (
    Completeness Score × 0.40 +
    Consistency Score × 0.30 +
    Validity Score × 0.20 +
    Uniqueness Score × 0.10
)
```

### Score Interpretation

- **90-100:** Excellent - Ready for entity resolution
- **75-89:** Good - Minor improvements recommended
- **60-74:** Fair - Moderate data quality issues
- **40-59:** Poor - Significant quality problems
- **0-39:** Critical - Major data quality work needed

## Quality Metrics

### 1. Completeness Score (40% weight)

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

### 2. Consistency Score (30% weight)

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

### 3. Validity Score (20% weight)

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

### 4. Uniqueness Score (10% weight)

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

## Automated Quality Assessment

### Data Quality Scorer — Algorithm Description

The data quality scorer is a tool that reads a source data file, analyzes it across the four quality dimensions above, and produces a structured report. Here is what it does:

#### Inputs

- A source data file (CSV, JSON, or JSONL format)

#### Processing Steps

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

#### Outputs

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

## Usage

Run the data quality scorer on your source data file and optionally specify an output path for the report:

```text
Run the data quality scorer on your source data file.
  Input:  your source data file (e.g., data/raw/customers.csv)
  Output: a quality report file (e.g., docs/quality_customers.json)

Then inspect the report — look at the overall_score field to get a quick summary.
```

## Visual Quality Dashboard

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

## Agent Behavior

When a user is in Module 4, the agent should:

1. **Run quality scorer** on each data source
2. **Generate quality report** with scores and metrics
3. **Create HTML dashboard** for visualization
4. **Review scores** with user
5. **Provide recommendations** for improvement
6. **Document quality** in `docs/data_quality_report.md`
7. **Track quality scores** for comparison after mapping

## Output Files

- `docs/data_quality_report.json` - Detailed quality metrics
- `docs/data_quality_dashboard.html` - Visual dashboard
- `docs/data_quality_report.md` - Summary documentation

## Related Documentation

- `POWER.md` - Module 4 overview
- `steering/module-04-data-quality.md` - Module 4 workflow
- `steering/data-quality-scoring.md` - Detailed scoring guide

## Version History

- **v3.0.0** (2026-03-17): Module 4 enhanced with automated quality scoring
