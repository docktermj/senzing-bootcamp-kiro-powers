---
inclusion: manual
---

# Module 4: Verify Data Sources Against SGES

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_4_DATA_QUALITY_SCORING.md`.
>
> **Quality Scoring Methodology:** For a full explanation of how quality scores are calculated, what each dimension measures, and what thresholds mean, see `docs/guides/QUALITY_SCORING_METHODOLOGY.md`. When a user asks how their score was calculated or what their score means, direct them to this guide.

## Workflow: Verify Data Sources Against SGES (Module 4)

**Prerequisites**: ✅ Module 3 complete (data sources collected, files in `data/raw/`)

**Before/After**: You have raw data files but don't know if Senzing can use them directly. After this module, each source is scored for quality and categorized — you'll know which ones need transformation and which are ready to load.

1. **List the agreed-upon data sources**: Recap the data sources identified during the business problem discussion. Review `docs/business_problem.md` for the list.

2. **Request sample data**: For each data source, ask the user to place sample files in `data/raw/` or `data/samples/`:
   - CSV files (first 10-20 rows)
   - JSON samples
   - Database schema with sample values
   - Screenshots of data tables
   - Text descriptions of fields and data types

3. **Understand the Senzing Generic Entity Specification**: Call `search_docs` with query "generic entity specification" or "SGES format" to retrieve current documentation about the standard format. Key SGES attributes include:
   - **Identity attributes**: `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `NAME_ORG`, `DATE_OF_BIRTH`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER`, `SSN_NUMBER`, `NATIONAL_ID_NUMBER`
   - **Contact attributes**: `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `WEBSITE_ADDRESS`
   - **Required fields**: `DATA_SOURCE`, `RECORD_ID`
   - **Relationship attributes**: `REL_ANCHOR_DOMAIN`, `REL_ANCHOR_KEY`, `REL_POINTER_DOMAIN`, `REL_POINTER_KEY`, `REL_POINTER_ROLE`

4. **Compare each data source with SGES**: For each data source provided:
   - Identify which fields map directly to SGES attributes (e.g., "full_name" → `NAME_FULL`)
   - Identify fields that need transformation (e.g., separate "first_name" and "last_name" → `NAME_FULL`)
   - Identify fields with non-standard names (e.g., "company" → `NAME_ORG`)
   - Note any missing critical fields
   - Check if `DATA_SOURCE` and `RECORD_ID` are present or can be derived

5. **Categorize each data source**:
   - **SGES-compliant**: Data already uses standard Senzing attribute names and structure. Can proceed directly to Module 0 (SDK setup) and Module 6 (loading).
   - **Needs mapping**: Data uses different field names or structures. Proceed to Module 5 (data mapping).
   - **Needs enrichment**: Data is missing critical attributes. Discuss with user whether additional data sources can provide missing information.

6. **Assess data quality and apply thresholds**:

   For each data source, compute a quality score based on field completeness, format consistency, and duplicate rate. Use these thresholds to guide the decision:

   - **≥80% quality score** → Proceed to Module 5 (mapping). Data quality is strong enough for meaningful entity resolution.
   - **70-79% quality score** → Warn the user. Quality gaps exist — suggest specific fixes (fill nulls, standardize formats, deduplicate within source). Proceed to Module 5 if the user accepts the risk, but document the quality gaps. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for details on what each score range means.
   - **<70% quality score** → Strongly recommend fixing data quality before mapping. Entity resolution results will be poor. Help the user identify the biggest quality issues and create a remediation plan. Only proceed if the user explicitly chooses to continue. Direct the user to `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for guidance on improving each dimension.

   Present the assessment clearly:

   ```text
   Data Quality Assessment:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Source: CUSTOMERS_CRM
     Field completeness:  82%  (name: 99%, phone: 75%, email: 68%)
     Format consistency:  90%
     Duplicate rate:       3%
     Overall quality:     78%  ✅ Ready for mapping

   Source: VENDORS_LEGACY
     Field completeness:  45%  (name: 90%, phone: 20%, email: 15%)
     Format consistency:  55%
     Duplicate rate:      12%
     Overall quality:     42%  ⚠ Recommend fixing before mapping
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

7. **Summarize findings and save evaluation report**: Create `docs/data_source_evaluation.md`:

   ```markdown
   # Data Source Evaluation Report

   **Date**: [Current date]
   **Project**: [Project name]

   ## Summary
   - Total data sources: [count]
   - SGES-compliant: [count]
   - Needs mapping: [count]
   - Needs enrichment: [count]

   ## Data Source Details

   ### Data Source 1: [Name]
   **Status**: [SGES-compliant / Needs mapping / Needs enrichment]
   **Location**: `data/raw/[filename]`
   **Records**: ~[count]
   **Fields**: [count] columns

   **Evaluation**:
   - [Field analysis]
   - [SGES compliance notes]

   **Reason**: [Why it needs mapping or is compliant]

   **Next step**: [Module 5 / Module 6]

   ### Data Source 2: [Name]
   [Same structure]

   ## Mapping Priority
   1. [Data source] - [Reason for priority]
   2. [Data source] - [Reason for priority]
   ```

8. **Proceed to mapping**: For each data source that needs mapping, transition to the "Data Mapping End-to-End" workflow (Module 5).

## Iterate vs. Proceed Decision Gate

After presenting the quality assessment, guide the user's decision:

- **Quality ≥80%:** "Your data quality is strong. Ready to proceed to Module 5 (mapping)."
- **Quality 70-79%:** "Your data quality is acceptable but has some gaps. You can proceed to mapping now — or if you'd like to improve the weakest fields first, we can work on that. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for details on what each dimension means. What would you prefer?"
- **Quality <70%:** "Your data quality needs attention before mapping will produce good results. I'd recommend focusing on [specific issues — e.g., filling missing phone numbers, standardizing address formats]. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for a full breakdown of how scores are calculated and what to improve. Would you like to work on improving the data, or proceed anyway knowing the results may be limited?"

WAIT for response before proceeding.

**Success indicator**: ✅ All data sources categorized + `docs/data_source_evaluation.md` created

## Workflow: Install Senzing Bootcamp Hooks

**Note**: Hooks are installed automatically during onboarding — no user action needed. The agent copies all `.kiro.hook` files from `senzing-bootcamp/hooks/` to `.kiro/hooks/` when the bootcamp starts. Hooks can also be reinstalled at any time by saying "install hooks" or running `python scripts/install_hooks.py`.
