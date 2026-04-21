# Quality Scoring Methodology

## Introduction

When Module 4 evaluates your data sources, it produces a quality score from 0 to 100. This guide explains exactly how that score is calculated, what each component measures, and what your score means for your next steps. If you received a score and want to understand why, this is the place to look.

## How the Overall Score Is Calculated

The overall quality score is a weighted average of four dimensions:

```text
Quality Score = (Completeness × 0.40)
              + (Consistency  × 0.30)
              + (Format Compliance × 0.20)
              + (Uniqueness   × 0.10)
```

Each dimension produces a sub-score from 0 to 100. The weights reflect how much each dimension affects entity resolution outcomes:

| Dimension          | Weight | Why It Matters                                                        |
|--------------------|--------|-----------------------------------------------------------------------|
| Completeness       | 40%    | Missing fields mean fewer attributes for matching — biggest impact    |
| Consistency        | 30%    | Inconsistent formats make it harder to compare values across records  |
| Format Compliance  | 20%    | Invalid values (bad emails, malformed phones) cannot be matched       |
| Uniqueness         | 10%    | Duplicates within a source inflate record counts and skew results     |

## Scoring Dimensions Explained

### 1. Completeness (40% Weight)

Completeness measures how many fields in your data have actual values versus being null or empty.

**How it is computed:**

1. Identify critical fields — columns whose names suggest entity resolution relevance (name, ID, address, phone, email, date of birth, SSN).
2. For each critical field, calculate: `field_completeness = non-empty values / total records × 100`.
3. Average the field completeness values across all critical fields.

If no critical fields are detected, the scorer averages across all fields instead.

**What drags this score down:**

- Null or empty values in name, address, or phone columns
- Sparse optional fields that the scorer identifies as critical
- Whitespace-only strings (treated as empty)

### 2. Consistency (30% Weight)

Consistency measures whether values in each field follow a uniform format pattern.

**How it is computed:**

1. For each field type (phone, email, date, address, name), detect all format variations present.
2. Count how many records use the most common format.
3. Calculate: `field_consistency = most common format count / total non-null values × 100`.
4. Average across all checked fields.

**What drags this score down:**

- Phone numbers in mixed formats: some as `(555) 123-4567`, others as `5551234567`, others as `+15551234567`
- Dates in mixed formats: some as `2024-01-15`, others as `01/15/2024`, others as `15-01-2024`
- Names in mixed case: some as `JOHN SMITH`, others as `john smith`, others as `John Smith`

### 3. Format Compliance (20% Weight)

Format compliance measures whether field values pass validation rules for their expected data type.

**How it is computed:**

1. For each field type, apply validation rules:
   - **Email**: matches `user@domain.tld` pattern
   - **Phone**: matches known formats (10 digits, dashed, parenthesized, international)
   - **Date**: falls within a reasonable date range
   - **Postal code**: matches expected postal code patterns
   - **State/country**: matches known codes
2. Calculate: `valid_percentage = valid values / total non-null values × 100`.
3. Average across all validated fields.

**What drags this score down:**

- Email addresses missing the `@` symbol or domain
- Phone numbers with too few or too many digits
- Dates outside reasonable ranges (year 0001, year 9999)
- Postal codes that do not match any known pattern

### 4. Uniqueness (10% Weight)

Uniqueness measures how many records in your data source are distinct (not duplicated).

**How it is computed:**

1. Count total records.
2. Count exact duplicate records (rows identical across all fields).
3. Optionally detect fuzzy duplicates (near-matches).
4. Calculate: `uniqueness_score = (total - exact duplicates - fuzzy duplicates) / total × 100`.

**What drags this score down:**

- Exact duplicate rows (same values in every column)
- Duplicate IDs pointing to identical records
- Near-duplicate records with minor variations (typos, extra whitespace)

## Threshold Bands and Recommended Actions

Your overall quality score falls into one of three bands. Each band has a clear recommended action:

| Score Range | Band   | Recommended Action                                                                                     |
|-------------|--------|--------------------------------------------------------------------------------------------------------|
| ≥ 80%       | Green  | **Proceed** to Module 5 (data mapping). Data quality is strong enough for meaningful entity resolution. |
| 70 – 79%    | Yellow | **Warning.** Quality gaps exist. You may proceed or improve data first — your choice.                  |
| < 70%       | Red    | **Fix first.** Data quality issues will produce poor entity resolution results. Address the weakest dimensions before proceeding. |

### ≥ 80% — Proceed

Your data has strong completeness, consistent formats, valid values, and few duplicates. Entity resolution will have enough attributes to work with. Proceed to Module 5 (data mapping).

### 70 – 79% — Warning, Your Choice

Your data is usable but has noticeable gaps. The agent will tell you which dimensions scored lowest. You can:

- **Proceed anyway** — entity resolution will work but may miss some matches due to missing or inconsistent data.
- **Improve first** — focus on the weakest dimension(s) to push your score above 80%.

### < 70% — Recommend Fixing First

Your data has significant quality problems. The agent will list the specific dimensions that need attention and suggest concrete fixes (fill missing fields, standardize formats, remove duplicates). Proceeding at this level risks poor entity resolution results — many potential matches will be missed.

## Examples

### Example 1: High Quality Data (Score ≥ 80%)

**Sample data** (`customers_crm.csv`):

| customer_id | full_name      | email                | phone          | address                  |
|-------------|----------------|----------------------|----------------|--------------------------|
| C001        | Alice Johnson  | alice@example.com    | (555) 123-4567 | 100 Main St, Austin, TX  |
| C002        | Bob Williams   | bob.w@example.com    | (555) 234-5678 | 200 Oak Ave, Austin, TX  |
| C003        | Carol Davis    | carol.d@example.com  | (555) 345-6789 | 300 Pine Rd, Dallas, TX  |
| C004        | David Brown    | david.b@example.com  | (555) 456-7890 | 400 Elm St, Houston, TX  |
| C005        | Eva Martinez   | eva.m@example.com    | (555) 567-8901 | 500 Cedar Ln, Austin, TX |

**Sub-scores:**

- Completeness: **95%** — all critical fields populated, only a few optional fields empty
- Consistency: **92%** — phone numbers all use `(XXX) XXX-XXXX` format, names all Title Case
- Format Compliance: **90%** — all emails valid, all phones valid, addresses well-formed
- Uniqueness: **100%** — no duplicate records

**Calculation:**

```text
Quality Score = (95 × 0.40) + (92 × 0.30) + (90 × 0.20) + (100 × 0.10)
             = 38.0 + 27.6 + 18.0 + 10.0
             = 93.6
```

**Result: 93.6% — Green band. Proceed to mapping.**

### Example 2: Medium Quality Data (Score 70 – 79%)

**Sample data** (`vendors_mixed.csv`):

| vendor_id | name            | email               | phone        | city       |
|-----------|-----------------|---------------------|--------------|------------|
| V001      | Acme Corp       | contact@acme.com    | 555-111-2222 | Austin     |
| V002      | GLOBEX INC      |                     | 5552223333   | dallas     |
| V003      | Initech         | info@initech.com    | (555)333-444 | Houston    |
| V004      | acme corp       | sales@acme.com      | 555.444.5555 | Austin     |
| V005      | Umbrella LLC    | bad-email           | +15555556666 |            |

**Sub-scores:**

- Completeness: **80%** — email missing for V002, city missing for V005
- Consistency: **60%** — phone numbers in four different formats, name casing inconsistent
- Format Compliance: **75%** — one invalid email (V005), one malformed phone (V003 too few digits)
- Uniqueness: **90%** — V001 and V004 are likely duplicates (Acme Corp / acme corp)

**Calculation:**

```text
Quality Score = (80 × 0.40) + (60 × 0.30) + (75 × 0.20) + (90 × 0.10)
             = 32.0 + 18.0 + 15.0 + 9.0
             = 74.0
```

**Result: 74.0% — Yellow band. Warning: consistency is the weakest dimension at 60%. You can proceed to mapping or standardize phone formats and name casing first.**

### Example 3: Low Quality Data (Score < 70%)

**Sample data** (`legacy_contacts.csv`):

| id   | name           | email  | phone       | addr   |
|------|----------------|--------|-------------|--------|
| 1    | J. Smith       |        | 555-1234    |        |
| 2    |                | j@x    | none        | Dallas |
| 3    | JANE DOE       |        | 5559999     |        |
| 1    | J. Smith       |        | 555-1234    |        |
| 4    | bob            | bob@co | 123         | ???    |

**Sub-scores:**

- Completeness: **40%** — email missing for 3 of 5 records, address missing for 3 of 5 records
- Consistency: **45%** — name formats vary wildly (initials, ALL CAPS, lowercase), no consistent phone format
- Format Compliance: **35%** — emails invalid or missing, phones too short, "none" and "???" are not valid values
- Uniqueness: **80%** — rows 1 and 4 are exact duplicates

**Calculation:**

```text
Quality Score = (40 × 0.40) + (45 × 0.30) + (35 × 0.20) + (80 × 0.10)
             = 16.0 + 13.5 + 7.0 + 8.0
             = 44.5
```

**Result: 44.5% — Red band. Recommend fixing before proceeding. Focus on completeness (fill missing emails and addresses), format compliance (fix invalid values), and consistency (standardize name and phone formats).**

## Related Documentation

- [Module 4: Data Quality Scoring](../modules/MODULE_4_DATA_QUALITY_SCORING.md) — Full module documentation with algorithm details
- [Module 4 Steering File](../../steering/module-04-data-quality.md) — Agent workflow for Module 4
- [Data Quality Check Hook](../../hooks/data-quality-check.kiro.hook) — Automated quality check hook
- [Performance Baselines](PERFORMANCE_BASELINES.md) — How data volume affects processing time and resource needs
- [Offline Mode](OFFLINE_MODE.md) — What works when MCP is unavailable (Module 4 quality scoring is mostly offline)
- [Common Mistakes](COMMON_MISTAKES.md) — Common data quality mistakes and how to avoid them

---

**Last Updated**: 2026-04-17
