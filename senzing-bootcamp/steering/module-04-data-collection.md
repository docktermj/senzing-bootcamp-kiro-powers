---
inclusion: manual
---

> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a pointing question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.

# Module 4: Identify and Collect Data Sources

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_4_DATA_COLLECTION.md`.

## Workflow: Identify and Collect Data Sources (Module 4)

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified), ✅ Module 3 complete (system verification passed or skipped)

**Before/After**: You have a list of data sources on paper. After this module, the actual data files are in your project (`data/raw/`), documented, and ready for quality evaluation.

**Purpose**: Collect the actual data files from each identified data source and store them in the project for analysis and mapping.

> **Agent instruction — License limit and dataset size (canonical framing):** By default, the bootcamper already has Senzing's **built-in evaluation license** — the capacity that applies when no custom license is configured. Treat it as the default the session already has, presented as a choice rather than a wall. Before any license-based capacity or sampling decision, **read `license_record_limit` from `config/bootcamp_progress.json`** (Module 2 Step 5e writes it via `detect_license_limit.py` after a custom license is configured) and drive the decision from that effective limit — never from a remembered or hardcoded figure:
>
> - **Present and greater than 0** (custom license with a finite record cap): the effective limit is that value. Recommend sampling for license reasons only when the dataset total genuinely exceeds it.
> - **Present and equal to 0** (custom license with no record cap): the license imposes no cap — do **not** recommend sampling for license reasons, and support loading the full dataset.
> - **Absent or null** (no custom license detected yet): fall back to the **built-in evaluation license** the bootcamper already has by default, whose capacity is confirmed via the Senzing MCP server at request time (never a hardcoded or remembered figure).
>
> Whenever a dataset is — or might be — larger than the effective limit allows, present that as a choice, not a wall. The bootcamper can keep their full dataset and expand capacity, or work with a smaller slice — and downsizing is only ever one option among several, never the only path forward.
>
> - **Keep the full dataset and expand:** route to the Module 1 licensing paths — apply an existing license, request one through the external channel, or (when available) request one in-flow via the Senzing MCP server. Use the Module 1 Phase 1 discovery flow (Steps 6a–6e) for the tool-availability checks and branching; do not duplicate that logic here.
> - **Work with a smaller slice (optional):** sampling, a CORD subset, or a smaller substitute dataset.
>
> Sampling also stays available for **non-license** reasons — a very large or unwieldy file (for example, >1GB) or faster iteration — independent of the effective limit. Retrieve any specific record-capacity or validity figure from the Senzing MCP server at request time, exactly as the Module 1 flow does. If the MCP server does not return a figure or cannot be reached, omit the number and say the current value is unavailable from the MCP server — never restate a remembered or hardcoded figure here.

1. **Review identified data sources**: Recap the data sources identified in Module 1. Review `docs/business_problem.md` for the complete list.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **For each data source, collect the data**:

   First, ask: "How would you like to provide the data for [datasource_name]? You can upload a file, provide a URL/file path, connect to a database, or use an API endpoint."

   **If the user doesn't have their own data** or wants free data to practice with, recommend CORD data as the primary alternative:

   > "Senzing provides **CORD (Collections Of Relatable Data)** — curated, real-world-like datasets designed specifically for entity resolution evaluation. These are the best option for learning with realistic data patterns.
   >
   > I can pull CORD datasets (Las Vegas, London, Moscow) using the `get_sample_data` tool — these are ready-to-use Senzing JSONL files.
   >
   > Learn more about CORD: <https://senzing.com/senzing-ready-data-collections-cord/>"

   Use `get_sample_data(dataset='list')` to show available CORD datasets. Present the `download_url` from the response so the user can download the full JSONL file.

   **If the user declines CORD data** or needs something different, offer secondary options:

   > "If CORD doesn't meet your needs, there are other options:
   > - **Free raw data**: A curated collection of 35+ free data sources at <https://github.com/docktermj/senzing-bootcamp-free-data> — these include raw samples (great for practicing mapping) and pre-mapped files.
   > - **Synthesized test data**: I can generate custom test data tailored to your specific scenario."

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

   > **Agent instruction — CORD Metadata Capture:** If the bootcamper chose to use their own data instead of CORD data, skip this step entirely. Otherwise, after CORD data has been downloaded via `get_sample_data` and validated, capture a metadata snapshot for freshness verification in Module 6. Determine the dataset name and file paths from the download context, then run:
   >
   > ```bash
   > python senzing-bootcamp/scripts/cord_metadata.py capture --dataset <dataset_name> --files <path_to_downloaded_files>
   > ```
   >
   > Replace `<dataset_name>` with the CORD dataset identifier (e.g., `cord-las-vegas`) and `<path_to_downloaded_files>` with the space-separated paths to the downloaded JSONL files in `data/raw/`. This stores metadata in `config/cord_metadata.yaml` so Module 6 can detect if files changed between download and load time.

   > **Agent instruction — CORD Provenance Recording:** After each data source file is
   > collected and its Registry_Entry created/updated in `config/data_sources.yaml`,
   > set the `provenance` field based on the data origin:
   >
   > - `cord` — source obtained via `get_sample_data` MCP tool
   > - `own` — bootcamper's own data (uploaded, URL, database, or API)
   > - `free_data` — data from the free-data GitHub repository
   > - `synthesized` — generated test data
   > - `unknown` — origin cannot be determined
   >
   > Set `updated_at` to the current ISO 8601 timestamp when writing provenance.
   > A source with `provenance: unknown` is never eligible for the fast-path.

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

   ````markdown
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

   ````

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Handle sensitive data appropriately**:

   - Remind user about data privacy (see `steering/security-privacy.md`)
   - If data contains PII, suggest anonymizing for testing
   - Ensure `.gitignore` excludes `data/raw/*` to prevent committing sensitive data
   - Document any data handling requirements in `docs/security_compliance.md`

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Create sample files if needed**:

   A smaller working file can be useful in two situations: a very large dataset (e.g., >1GB) that is unwieldy to handle, or a dataset larger than the effective record limit allows. In **both** cases sampling is one option, not a requirement.

   If the dataset may exceed the effective record limit, apply the canonical framing from the top of this module: **read `license_record_limit` from `config/bootcamp_progress.json`** and drive the decision from that effective limit. When it is `0` (no cap) or greater than or equal to the dataset size, do **not** recommend sampling for license reasons — support loading the full dataset. When it is absent or null, fall back to the built-in evaluation capacity confirmed via the Senzing MCP server. When the dataset genuinely exceeds the effective limit, the bootcamper can keep their full dataset and expand capacity via the Module 1 licensing paths, or work with a smaller slice. Do not steer them to a smaller substitute as the only path. Defer the licensing-path availability checks and any capacity figure to the Module 1 Phase 1 discovery flow (Steps 6a–6e) and the Senzing MCP server.

   **If the bootcamper chooses to work with a smaller slice:**
   - Create smaller sample files (sampling, a CORD subset, or a smaller substitute dataset)
   - Save samples to `data/samples/[datasource_name]_sample.[extension]`
   - Document sampling method (first N records, random sample, etc.)
   - Ensure the sample is representative of the full dataset

   **If the bootcamper chooses to keep the full dataset:** continue the collection workflow with the complete files — there is no requirement to reduce the dataset.

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

8a. **Record-count license back-fill** (after all sources are collected): Run `python senzing-bootcamp/scripts/record_count_backfill.py` to infer the real record total from `config/data_sources.yaml`. If the decision reports `present_guidance: true` (the collected total exceeds the built-in evaluation limit and Module 1 license guidance was skipped or deferred), surface the **existing** Module 1 Steps 6b–6e license guidance now — using the canonical framing at the top of this module and the Senzing MCP server for any capacity/validity figure — then update the same `license` / `license_guidance_deferred` markers Module 1 uses. If `present_guidance: false` (already delivered, or at/below the limit), do not re-present guidance. If `computable: false`, note the warning and continue on the Module 1 Prose_Count behavior. This step is non-blocking — always proceed to Step 9 regardless of the outcome. Introduce no hook and no per-write invocation; this is a single steering-flow invocation after collection.

   **Checkpoint:** Write step 8a to `config/bootcamp_progress.json`.

8b. **SQLite Load-Time Warning (collection-time heads-up)** (after Step 8a, before the Step 9 transition): This is a *time/performance* heads-up, deliberately **distinct** from the license-capacity sampling framing at the top of this module — it judges the Module 6 SQLite load time from the actual collected dataset and fires even when the effective license imposes no record cap. It is **NOT a Mandatory_Gate** — there is no ⛔, and the bootcamper may always proceed on SQLite with the full dataset.

   > **Agent instruction — run this once at the end of collection, immediately before the Step 9 transition. Every step is non-blocking: any failure or indeterminate input continues the Module 4 flow (Requirement 7.5).**
   >
   > **1. Read the persisted inputs.** Read `config/data_sources.yaml` via the `data_sources` reader chain (`parse_registry_yaml` → `apply_migrations` → `validate_registry` → `_dict_to_registry`) to get the `registry`, and read `database_type` from `config/bootcamp_preferences.yaml` (via `preferences_utils.load_preferences` / `parse_yaml`) → `db_type`. Compute the collected total with `record_count_backfill.compute_collected_count(registry, row_count=True).known_total` → `known_total`. If the registry cannot be read or parsed, treat `known_total` as indeterminate (`None`) — do not fail.
   >
   > **2. Call the predicate.** Evaluate `volume_utils.should_warn_load_time(known_total, db_type)`.
   >
   > - **`False`** → say nothing about load time; continue the Module 4 flow to the Step 9 transition. (Covers a collected total at or below the threshold, any non-SQLite engine, and indeterminate inputs — Requirements 1.2, 1.3, 1.4, 2.4, 7.5.)
   > - **`True`** → consult the **Senzing MCP server** at request time for the four `TimingGuidance` figures — `expected_throughput`, `throughput_degradation`, `expected_load_duration`, and `redo_phase_duration`. Any figure the server does not return, or that errors, stays `None` (never substitute a remembered number). Build a `volume_utils.TimingGuidance` from what the server returned, present the output of `volume_utils.build_load_time_warning(known_total, timing)` to the bootcamper, then **🛑 STOP** and wait for their choice.
   >
   > **3. Act on the bootcamper's choice.** Sampling is offered here as one option among proceeding and switching databases — not as the only path.
   >
   > - **Load all collected records on SQLite:** First obtain an **explicit confirmation** that the bootcamper accepts the expected load time before continuing with the full dataset (Requirement 4.4). Then record the decision (sub-step 4) and continue to Step 9.
   > - **Sample down to a smaller record count:** Ask which `Sampling_Strategy` to use **before** creating the sample (Requirement 5.1) — offer first-N records (`load_time_warning.select_first_n`), random-N records (`load_time_warning.select_random_n`), and the entity-resolution-demonstrating strategy that preserves cross-source overlaps and known match clusters (`load_time_warning.select_er_demonstrating`); also accept a bootcamper-described strategy (Requirements 5.2, 5.3). Validate the target record count with `load_time_warning.validate_sample_target(target, known_total)` and re-ask until it is valid — a positive integer strictly less than the collected total (Requirements 5.5, 5.6). Create the sample with the chosen selector, write it under `data/samples/` via `load_time_warning.write_sample`, and document the strategy and target with `load_time_warning.write_sample_manifest` (Requirement 5.4). Then record the decision (sub-step 4).
   > - **Switch to an alternative database (e.g. PostgreSQL):** Route the bootcamper to the existing `database-migration-guide` at `docs/guides/DATABASE_MIGRATION.md`. Do NOT inline or restate the migration steps here — hand off to that guide (Requirement 4.3). Then record the decision (sub-step 4).
   >
   > **4. Record the decision.** Write the Load_Decision_Marker via `load_time_warning.write_load_decision(choice, load_time_warning.compute_load_identity(registry))`, where `choice` is `"proceed"`, `"sample"`, or `"switch_db"` (Requirements 6.1, 6.2). This uses the shared `sqlite_volume_prompt` marker, so the Module 6 Phase A SQLite heads-up does not redundantly re-ask about this same load.
   >
   > **Reuse and safety notes:** The trigger and wording live in `volume_utils`; the identity, sampling, and marker helpers live in `load_time_warning`, which reuses `record_count_backfill`, `data_sources`, and `preferences_utils` — do not re-derive record counts or tiers here (Requirement 7.4). Refer to the Senzing MCP server by name only (never a URL) and to the migration guide by its repo-relative path (`docs/guides/DATABASE_MIGRATION.md`). Use only synthetic/persisted values — never echo credentials or connection strings.

   **Checkpoint:** Write step 8b to `config/bootcamp_progress.json`.

9. **Transition to Module 5**: "Great! Now that we have the data files, let's evaluate each one to see if it needs mapping or if it's already in the right format for Senzing."

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

**Success indicator**: ✅ Sources collected + files in data/raw/ OR documented locations + `docs/data_source_locations.md` created + data collection status tracked

**Agent behavior**:

- Be patient with file uploads - they may take time
- Provide clear instructions for each data source type
- Help user create sample files if full datasets are too large
- Remind about data privacy and security
- Verify files are accessible before proceeding
- Document everything in `docs/data_source_locations.md`
- **If user doesn't have data or asks about free data sources**, follow the data recommendation hierarchy: (1) recommend CORD data first via the `get_sample_data` MCP tool (Las Vegas, London, Moscow datasets) with reference to <https://senzing.com/senzing-ready-data-collections-cord/>, (2) if CORD is declined, recommend <https://github.com/docktermj/senzing-bootcamp-free-data> for raw samples and additional sources, (3) offer synthesized test data generation only as a last resort after CORD and free-data options are declined

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section
