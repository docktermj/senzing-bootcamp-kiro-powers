---
inclusion: manual
---

# Module 4: Identify and Collect Data Sources

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_4_DATA_COLLECTION.md`.

## Workflow: Identify and Collect Data Sources (Module 4)

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified)

**Before/After**: You have a list of data sources on paper. After this module, the actual data files are in your project (`data/raw/`), documented, and ready for quality evaluation.

**Purpose**: Collect the actual data files from each identified data source and store them in the project for analysis and mapping.

1. **Review identified data sources**: Recap the data sources identified in Module 1. Review `docs/business_problem.md` for the complete list.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **For each data source, collect the data**:

   First, ask: "How would you like to provide the data for [datasource_name]? You can upload a file, provide a URL/file path, connect to a database, or use an API endpoint."

   **If the user doesn't have their own data** or wants free data to practice with, proactively mention:

   > "You have two options for sample data:
   > 1. **MCP sample data**: I can pull real data from CORD datasets (Las Vegas, London, Moscow) using the `get_sample_data` tool — these are ready-to-use Senzing JSONL files.
   > 2. **Free raw data**: There's a curated collection of 35+ free data sources at <https://github.com/docktermj/senzing-bootcamp-free-data> — these include raw samples (great for practicing mapping) and pre-mapped files."

   Use `get_sample_data(dataset='list')` to show available CORD datasets. Present the `download_url` from the response so the user can download the full JSONL file.

   Then proceed with the appropriate option:

   **Option A: User uploads files**
   - Ask user to provide data files (CSV, JSON, Excel, etc.)
   - User can drag and drop files into the chat or use file upload
   - Save uploaded files to `data/raw/[datasource_name].[extension]`
   - Example: `data/raw/customer_crm.csv`, `data/raw/vendor_api.json`

   **Option B: User provides URL/location**
   - Ask user for the URL or file path where data resides
   - Document the location in `docs/data_source_locations.md`
   - If accessible, download/copy data to `data/raw/`
   - If not accessible (requires credentials, VPN, etc.), document access method

   **Option C: Database connection**
   - Ask user for database connection details
   - Document connection string (without passwords) in `docs/data_source_locations.md`
   - Store sample query results in `data/raw/[datasource_name]_sample.csv`
   - Document the query used to extract data

   **Option D: API endpoint**
   - Ask user for API endpoint URL and authentication method
   - Document API details in `docs/data_source_locations.md`
   - Store sample API response in `data/raw/[datasource_name]_sample.json`
   - Document the API call used

   **Handling different data formats:**

   Not all data arrives as CSV. Common formats and how to handle them:

   - **Excel (.xlsx)**: Convert to CSV first. Most languages have libraries for this (e.g., `openpyxl` for Python, Apache POI for Java). Save the CSV to `data/raw/`.
   - **Parquet / Avro**: Use language-appropriate libraries to read and convert to CSV or JSON. These formats are common in data lake exports.
   - **XML**: Parse and flatten to JSON or CSV. Use `find_examples(query='XML data loading')` for patterns.
   - **Database exports (SQL dump)**: Extract the relevant tables to CSV using the database's export tools.
   - **API pagination**: If the API returns paginated results, document the pagination strategy and write a collection script in `scripts/` that fetches all pages and saves to `data/raw/`.
   - **Real-time streams (Kafka, etc.)**: For the bootcamp, capture a snapshot to a file. Document the stream details for production use in Module 11.

   For any non-CSV/JSON format, the goal is to get the data into a flat file in `data/raw/` that Module 5 can evaluate.

   > **Agent instruction — Data Source Registry:** After collecting each data source file, create or update `config/data_sources.yaml` with a Registry_Entry for that source. If the file doesn't exist, create it with `version: "1"` and an empty `sources:` mapping first. Set fields: `name`, `file_path`, `format`, `record_count` (if known, else null), `file_size_bytes`, `quality_score: null`, `mapping_status: pending`, `load_status: not_loaded`, `added_at` and `updated_at` to the current ISO 8601 timestamp. If an entry already exists for that DATA_SOURCE key, update it and set `updated_at`.

   > **Agent instruction — Data File Validation:** After each file is saved to `data/raw/`, run the validator to sanity-check the file and update the registry with the results:
   >
   > ```bash
   > python senzing-bootcamp/scripts/validate_data_files.py <file_path> --update-registry
   > ```
   >
   > Present the Validation_Report to the bootcamper. If all checks pass, confirm the file is ready and move on to the next data source. If any check fails, show the failure details and remediation guidance, then help the bootcamper resolve the issue (re-upload, convert format, fix encoding, etc.) before proceeding to the next data source. Re-run the validator after each fix attempt until the file passes.

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Verify data was received**:

   ```bash
   # Linux / macOS
   ls -lh data/raw/
   head -5 data/raw/customer_crm.csv
   head -5 data/raw/vendor_api.json
   ```

   ```powershell
   # Windows (PowerShell)
   Get-ChildItem data\raw\ | Format-Table Name, Length
   Get-Content data\raw\customer_crm.csv -TotalCount 5
   Get-Content data\raw\vendor_api.json -TotalCount 5
   ```

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Document data source locations**:

   **Data Collection Checklist Template**: Before the user starts documenting sources, offer to copy the checklist template into their project:

   > "I have a data collection checklist template that helps you document all your data sources in a structured way. Want me to copy it to `docs/data_collection_checklist.md`?"

   If the user accepts, copy the data collection checklist template (#[[file:senzing-bootcamp/templates/data_collection_checklist.md]]) to the user's `docs/data_collection_checklist.md`. Guide the user to fill in one row per data source in the Data Inventory Table and complete the Validation Checklist before proceeding to Module 5.

   Also create or update `docs/data_source_locations.md`:

   ```markdown
   # Data Source Locations

   ## Data Source 1: Customer CRM
   - **Type**: CSV file
   - **Location**: `data/raw/customer_crm.csv`
   - **Original Source**: Uploaded by user from local system
   - **Last Updated**: 2025-01-17
   - **Record Count**: ~50,000 records
   - **Access Method**: One-time upload

   ## Data Source 2: Vendor API
   - **Type**: JSON API
   - **Location**: Sample data in `data/raw/vendor_api_sample.json`
   - **Original Source**: https://api.vendor.com/v1/suppliers
   - **Last Updated**: 2025-01-17
   - **Record Count**: ~5,000 records
   - **Access Method**: API call with Bearer token authentication
   - **API Documentation**: https://api.vendor.com/docs
   - **Sample API Call**:
     ```bash
     # Linux / macOS
     curl -H "Authorization: Bearer $API_TOKEN" \
          https://api.vendor.com/v1/suppliers?limit=100
     ```

     ```powershell
     # Windows (PowerShell)
     Invoke-RestMethod -Headers @{Authorization="Bearer $env:API_TOKEN"} `
       -Uri "https://api.vendor.com/v1/suppliers?limit=100"
     ```

   ## Data Source 3: Legacy Database

   - **Type**: PostgreSQL database
   - **Location**: Sample data in `data/raw/legacy_db_sample.csv`
   - **Original Source**: postgresql://dbserver.company.com:5432/legacy_db
   - **Last Updated**: 2025-01-17
   - **Record Count**: ~200,000 records
   - **Access Method**: Database query (requires VPN)
   - **Sample Query**:

     ```sql
     SELECT customer_id, name, address, phone, email
     FROM customers
     WHERE active = true
     LIMIT 1000;
     ```

   ```text

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Handle sensitive data appropriately**:

   - Remind user about data privacy (see `steering/security-privacy.md`)
   - If data contains PII, suggest anonymizing for testing
   - Ensure `.gitignore` excludes `data/raw/*` to prevent committing sensitive data
   - Document any data handling requirements in `docs/security_compliance.md`

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Create sample files if needed**:

   - If full dataset is very large (>1GB), create smaller sample files
   - Save samples to `data/samples/[datasource_name]_sample.[extension]`
   - Document sampling method (first N records, random sample, etc.)
   - Ensure sample is representative of full dataset

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Verify data quality at a glance**:

   Each file was already validated in step 2 and the results are stored in the registry. Review `config/data_sources.yaml` and check the `validation_status` and `validation_checks` fields for each data source entry. Confirm every source shows `validation_status: passed`. If any source shows `validation_status: failed`, revisit that data source and resolve the failing checks before proceeding.

   **Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

8. **Update data source tracking**:

   ```markdown
   Data Source Collection Status:
   - ✅ Customer CRM - Collected (data/raw/customer_crm.csv)
   - ✅ Vendor API - Sample collected (data/raw/vendor_api_sample.json)
   - ⬜ Legacy Database - Pending (requires VPN access)
   ```

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Transition to Module 5**: "Great! Now that we have the data files, let's evaluate each one to see if it needs mapping or if it's already in the right format for Senzing."

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

**Success indicator**: ✅ All data sources have files in `data/raw/` OR documented locations + `docs/data_source_locations.md` created + data collection status tracked

**Agent behavior**:

- Be patient with file uploads - they may take time
- Provide clear instructions for each data source type
- Help user create sample files if full datasets are too large
- Remind about data privacy and security
- Verify files are accessible before proceeding
- Document everything in `docs/data_source_locations.md`
- **If user doesn't have data or asks about free data sources**, first offer `get_sample_data` MCP tool for CORD datasets (Las Vegas, London, Moscow), then recommend <https://github.com/docktermj/senzing-bootcamp-free-data> for raw samples and additional sources

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section
