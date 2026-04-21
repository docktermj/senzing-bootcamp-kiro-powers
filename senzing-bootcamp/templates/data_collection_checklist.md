# Data Collection Checklist

## Purpose

Use this checklist during **Module 3 (Data Collection)** to document all data sources you plan to use for entity resolution. Completing this checklist ensures every source is properly cataloged before moving to Module 4 (Data Quality Scoring).

## Instructions

1. Copy this file into your project: `docs/data_collection_checklist.md`
2. Fill in one row per data source in the Data Inventory Table below
3. Use the reference sections for accepted values
4. Complete the Validation Checklist at the bottom before proceeding to Module 4

---

## Data Inventory Table

| Source Name | DATA_SOURCE | Record Count | Data Format | File Location | Access Method | Update Frequency | Contact Person | Data Sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Customer CRM Export | CUSTOMERS | ~50,000 | CSV | `data/raw/customers.csv` | Upload | Monthly | J. Smith | Confidential |
| *(add row)* | | | | | | | | |

---

## Reference: Data Format Values

| Format | Description |
| --- | --- |
| CSV | Comma-separated values file |
| JSON | Single JSON object or array file |
| JSONL | Newline-delimited JSON (one record per line) |
| XML | Extensible Markup Language file |
| Excel | Microsoft Excel spreadsheet (.xlsx / .xls) |
| Parquet | Apache Parquet columnar storage file |
| DB | Database export (SQL dump, direct query) |
| API | Data retrieved from an API endpoint |

## Reference: Data Sensitivity Levels

| Level | Description |
| --- | --- |
| Public | Data that is freely available and carries no privacy risk |
| Internal | Data intended for internal use only; low risk if disclosed |
| Confidential | Data containing PII or business-sensitive information; requires access controls |
| Restricted | Highly sensitive data (financial, health, legal); requires encryption and strict access controls |

## Reference: DATA_SOURCE Naming Conventions

- Use **UPPERCASE** letters only
- Use **underscores** (`_`) to separate words
- No spaces, hyphens, or special characters
- Keep names short but descriptive

Examples: `CUSTOMERS`, `VENDOR_API`, `LEGACY_CRM`, `HR_EMPLOYEES`

---

## Validation Checklist (Complete Before Module 4)

- [ ] All data source files exist in `data/raw/`
- [ ] Record counts have been verified for each data source
- [ ] Data formats are documented for each data source
- [ ] DATA_SOURCE identifiers are assigned and follow naming conventions (uppercase, underscores, no spaces)
- [ ] `docs/data_source_locations.md` has been created or updated
- [ ] Data sensitivity levels are assigned for each data source
