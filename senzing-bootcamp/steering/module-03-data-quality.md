---
inclusion: manual
---

# Module 3: Verify Data Sources Against SGES

## Workflow: Verify Data Sources Against SGES (Module 3)

**Time**: 10 minutes per data source

**Prerequisites**: ✅ Module 2 complete (data sources collected, files in `data/raw/`)

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
   - **SGES-compliant**: Data already uses standard Senzing attribute names and structure. Can proceed directly to Module 4 (SDK setup) and Module 5 (loading).
   - **Needs mapping**: Data uses different field names or structures. Proceed to Module 3 (data mapping).
   - **Needs enrichment**: Data is missing critical attributes. Discuss with user whether additional data sources can provide missing information.

6. **Summarize findings and save evaluation report**: Create `docs/data_source_evaluation.md`:

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

   **Next step**: [Module 3 / Module 4]

   ### Data Source 2: [Name]
   [Same structure]

   ## Mapping Priority
   1. [Data source] - [Reason for priority]
   2. [Data source] - [Reason for priority]
   ```

7. **Proceed to mapping**: For each data source that needs mapping, transition to the "Data Mapping End-to-End" workflow (Module 4).

**Success indicator**: ✅ All data sources categorized + `docs/data_source_evaluation.md` created

## Workflow: Install Senzing Boot Camp Hooks (Before Module 4)

Use this workflow to set up automated quality checks and reminders before starting data mapping.

**Time**: 5 minutes

**Purpose**: Install hooks that automate quality checks, backups, and documentation reminders throughout the boot camp.

1. **Explain hooks**: "Kiro hooks can automate common tasks and provide helpful reminders. I recommend installing a few hooks that will help maintain quality as we work through the boot camp."

2. **Recommend hooks for the boot camp**:
   - **Data Quality Check**: Reminds you to validate data quality when transformation programs change
   - **Backup Before Load**: Reminds you to backup the database before loading data
   - **Test Before Commit**: Automatically runs tests when you save source files
   - **Validate Senzing JSON**: Checks that output conforms to SGES format
   - **Update Documentation**: Reminds you to keep documentation in sync with code

3. **Install hooks**: Copy the pre-configured hooks from the power directory:

   ```bash
   # Create hooks directory if it doesn't exist
   mkdir -p .kiro/hooks

   # Copy all Senzing Boot Camp hooks
   cp senzing-bootcamp/hooks/*.hook .kiro/hooks/

   # Or copy individual hooks
   cp senzing-bootcamp/hooks/pep8-check.kiro.hook .kiro/hooks/
   cp senzing-bootcamp/hooks/data-quality-check.kiro.hook .kiro/hooks/
   cp senzing-bootcamp/hooks/backup-before-load.kiro.hook .kiro/hooks/
   cp senzing-bootcamp/hooks/validate-senzing-json.kiro.hook .kiro/hooks/
   ```

4. **Verify installation**: Check that hooks are installed:

   ```bash
   ls -la .kiro/hooks/
   ```

   You should see the `.kiro.hook` files.

5. **Explain hook behavior**:
   - **Data Quality Check**: Triggers when you save files in `src/transform/`. The agent will remind you to run quality validation.
   - **Backup Before Load**: Triggers when you save files in `src/load/`. The agent will remind you to backup the database.
   - **Test Before Commit**: Triggers when you save any source file. Automatically runs `pytest tests/`.
   - **Validate Senzing JSON**: Triggers when you modify files in `data/transformed/`. The agent will suggest using `lint_record`.
   - **Update Documentation**: Triggers when you save source files. The agent will remind you to update docs.

6. **Customize if needed**: Users can customize hooks by editing the JSON files:
   - Change file patterns to match their project structure
   - Modify prompts to fit their workflow
   - Adjust timeouts for commands
   - Enable/disable specific hooks

7. **Test a hook**: Save a file in `src/transform/` to test the Data Quality Check hook. The agent should provide a reminder about data quality validation.

8. **Commit hooks to version control**:

   ```bash
   git add .kiro/hooks/
   git commit -m "Add Senzing Boot Camp hooks"
   ```

**Success indicator**: ✅ Hooks installed in `.kiro/hooks/` + hooks verified working

**Note**: Hooks are optional but highly recommended. They help catch issues early and maintain quality throughout the boot camp.
