# Transformation Lineage: [DATA_SOURCE]

## Purpose

Use this template during **Module 4 (Data Quality & Mapping)** to document the complete transformation lineage for a single data source. Fill in one copy per data source after creating and testing the transformation program. This record captures what transformations were applied, why they were applied, and how data quality changed — supporting compliance, debugging, and governance.

## Instructions

1. Copy this file into your project: `docs/transformation_lineage_[name].md` (e.g., `docs/transformation_lineage_customers.md`)
2. Replace `[DATA_SOURCE]` in the title with your actual DATA_SOURCE name (e.g., `CUSTOMERS`)
3. Fill in the Source File Information section from your Module 3 data collection records
4. Fill in the Transformation Program section after creating the program in step 6 of Module 5
5. Fill in the Output File Information section after running the transformation
6. Complete the Record Count Summary from your transformation run output
7. Fill in the Field Mappings table from your `mapping_workflow` results
8. Document any Format Changes, Filters, and Quality Improvements applied
9. Complete the Validation Checklist before proceeding to Module 6

---

## Source File Information

| Field | Value |
| --- | --- |
| DATA_SOURCE Name | `[e.g., CUSTOMERS]` |
| Source File Path | `data/raw/[filename]` |
| Data Format | `[CSV / JSON / JSONL / XML / Excel]` |
| Record Count | `[e.g., 500,000]` |
| Extraction Date | `[YYYY-MM-DD]` |
| Encoding | `[e.g., UTF-8]` |

## Transformation Program

| Field | Value |
| --- | --- |
| Program Path | `src/transform/transform_[name].[ext]` |
| Program Version | `[e.g., v1.0]` |
| Language | `[e.g., Python, Java, Go]` |
| Last Modified | `[YYYY-MM-DD]` |

## Output File Information

| Field | Value |
| --- | --- |
| Output File Path | `data/transformed/[name].jsonl` |
| Data Format | `JSONL` |
| Record Count | `[e.g., 498,500]` |
| Generation Date | `[YYYY-MM-DD]` |
| Quality Score | `[e.g., 82/100]` |

---

## Record Count Summary

| Metric | Count |
| --- | --- |
| Records In | `[e.g., 500,000]` |
| Records Out | `[e.g., 498,500]` |
| Records Rejected | `[e.g., 1,500]` |
| Rejection Rate | `[e.g., 0.3%]` |

---

## Field Mappings

| Source Field | Senzing Attribute | Notes |
| --- | --- | --- |
| `customer_id` | `RECORD_ID` | Unique identifier per record |
| `full_name` | `NAME_FULL` | Complete name field |
| `address` | `ADDR_FULL` | Full address string |
| `phone` | `PHONE_NUMBER` | Primary phone number |
| `email` | `EMAIL_ADDRESS` | Primary email address |
| *(add row)* | | |

## Format Changes

| Field Name | Original Format | Target Format | Reason |
| --- | --- | --- | --- |
| `date_of_birth` | `MM/DD/YYYY` | `YYYY-MM-DD` | ISO 8601 standard for Senzing date attributes |
| `phone` | `(555) 123-4567` | `5551234567` | Digits only improves matching accuracy |
| *(add row)* | | | |

## Filters Applied

| Filter Description | Records Excluded | Reason |
| --- | --- | --- |
| Remove records with no name and no identifier | `[e.g., 200]` | Records without name or identifier cannot be resolved |
| Remove duplicate RECORD_ID values | `[e.g., 50]` | Senzing requires unique RECORD_ID per DATA_SOURCE |
| *(add row)* | | |

## Quality Improvements

| Action | Fields Affected | Quality Impact |
| --- | --- | --- |
| Trim whitespace and apply title case | Name fields | Reduces false negatives from formatting differences |
| Extract digits only from phone numbers | Phone fields | Standardizes phone format for better matching |
| Lowercase and validate email addresses | Email fields | Normalizes email for deduplication |
| *(add row)* | | |

---

## Validation Checklist (Complete Before Module 6)

- [ ] Source file information is complete and accurate
- [ ] Transformation program path and version are recorded
- [ ] Output file exists at the documented path
- [ ] Record counts match actual transformation run output
- [ ] All field mappings are documented with correct Senzing attributes
- [ ] Format changes are documented with reasons
- [ ] Filters are documented with record exclusion counts
- [ ] Quality improvements are documented with impact descriptions
- [ ] Quality score meets the minimum threshold (>70%)
- [ ] `docs/data_lineage.yaml` has been updated with this transformation entry
