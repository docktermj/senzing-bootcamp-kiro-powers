# Senzing Boot Camp — Steering Guide

This document provides detailed workflows for the Senzing Boot Camp power. The agent loads this on-demand when users engage with specific boot camp activities.

## Progress Tracking

Maintain awareness of the user's progress through the boot camp:
- Module 0: Quick Demo (Optional) - ⬜ Not started / ✅ Complete
- Module 1: Business Problem - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 2: Data Source Evaluation - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 3: Data Mapping - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 4: SDK Setup - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 5: Data Loading - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 6: Query Programs - ⬜ Not started / 🔄 In progress / ✅ Complete

Periodically remind users of their progress and what's next.

## Workflow: Quick Demo (Module 0 - Optional)

Use this workflow when a user wants to see entity resolution in action before working with their own data. This is perfect for first-time users who want to understand what Senzing does.

**Time**: 10-15 minutes

1. **Explain the demo**: "Let's do a quick demo using sample data so you can see entity resolution in action. We'll load some duplicate records and watch Senzing automatically resolve them into unique entities."

2. **Choose sample dataset**: Call `get_sample_data` to retrieve one of the CORD datasets:
   - **Las Vegas**: Customer records with duplicates (good for retail/hospitality use cases)
   - **London**: Person records with variations (good for identity management)
   - **Moscow**: Organization records (good for B2B use cases)
   
   Ask the user which scenario interests them most, or default to Las Vegas.

3. **Show sample records**: Display 3-5 sample records from the dataset. Point out:
   - How the same person/organization appears multiple times
   - Variations in names, addresses, phone numbers
   - Different data quality levels
   - How a human would recognize these as duplicates

4. **Generate demo script**: Call `generate_scaffold` with workflow `full_pipeline` to create a complete demo script that:
   - Initializes Senzing with SQLite (no installation required if using Docker)
   - Loads the sample records
   - Queries the results
   - Shows resolved entities

5. **Run the demo**: Execute the script and show:
   - Records being loaded
   - Entity resolution happening in real time
   - How many entities were created from the records
   - Example of a resolved entity showing all matching records

6. **Explain the results**: Walk through one resolved entity:
   - "These 3 records all matched because..."
   - Show the features that drove the match (name, address, phone)
   - Explain confidence scores
   - Show how Senzing combined the information

7. **Connect to their use case**: "Now imagine this with your data. Instead of [sample data], you'd have [their data sources]. The same process would find duplicates, match records across systems, and give you a unified view."

8. **Transition**: Ask if they want to:
   - Start Module 1 with their own data
   - Try another sample dataset
   - Learn more about how entity resolution works

**Success indicator**: User understands what entity resolution does and is ready to work with their own data.

## Workflow: Discover the Business Problem (Module 1)

Use this workflow when starting the boot camp or when a user wants to explore how Senzing can solve their specific challenge.

**Time**: 15-30 minutes

**Prerequisites**: None (or Module 0 complete if they did the demo)

1. **Set up project directory structure**: Before diving into the problem, help the user create an organized project structure:

   ```bash
   mkdir -p my-senzing-project/{data/{raw,transformed,samples,backups},src/{transform,load,query,utils},tests,docs,config,logs,monitoring,scripts}
   cd my-senzing-project
   ```
   
   Explain the purpose of each folder:
   - `data/raw/` - Original source data files
   - `data/transformed/` - Senzing-formatted JSON output
   - `data/samples/` - Sample data for testing
   - `data/backups/` - Database backups
   - `src/transform/` - Transformation programs (Module 3)
   - `src/load/` - Loading programs (Module 5)
   - `src/query/` - Query programs (Module 6)
   - `src/utils/` - Shared utilities
   - `tests/` - Test files
   - `docs/` - Design documents and specifications
   - `config/` - Configuration files
   - `logs/` - Log files
   - `monitoring/` - Dashboards and metrics
   - `scripts/` - Utility scripts (backup, rollback, etc.)
   
   **Initialize version control**:
   ```bash
   git init
   echo "# [Project Name] - Senzing Entity Resolution" > README.md
   ```
   
   **Create .gitignore**:
   ```gitignore
   # Sensitive data
   .env
   *.key
   *.pem
   config/*_credentials.json
   
   # Data files
   data/raw/*
   data/transformed/*
   !data/raw/.gitkeep
   !data/transformed/.gitkeep
   
   # Logs and databases
   logs/*.log
   *.db
   *.sqlite
   *.sqlite3
   
   # Python
   __pycache__/
   *.py[cod]
   .venv/
   venv/
   
   # Backups
   data/backups/*.sql
   ```
   
   **Set up Python environment** (if using Python):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install senzing pytest
   pip freeze > requirements.txt
   ```
   
   **Create environment template** (.env.example):
   ```bash
   # Senzing Configuration
   SENZING_ENGINE_CONFIG_JSON={"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing"}}
   SENZING_DATABASE_URL=sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db
   
   # Data Source Credentials
   CRM_API_KEY=your_api_key_here
   DATABASE_CONNECTION_STRING=your_connection_string_here
   
   # Monitoring
   ENABLE_MONITORING=true
   LOG_LEVEL=INFO
   ```
   
   **Initial git commit**:
   ```bash
   git add .
   git commit -m "Initial project setup"
   ```
   
   Create a basic README.md:
   ```markdown
   # [Project Name] - Senzing Entity Resolution
   
   ## Overview
   [To be filled in after Module 1]
   
   ## Business Problem
   [To be filled in after Module 1]
   
   ## Data Sources
   [To be filled in after Module 2]
   
   ## Setup Instructions
   [To be filled in after Module 4]
   
   ## Usage
   [To be filled in after Module 6]
   ```

2. **Data privacy reminder**: "Before we proceed, a quick reminder about data privacy. We'll be working with potentially sensitive data. Please ensure you have permission to use this data, and consider anonymizing any PII for testing purposes. We'll set up proper security measures as we go."

3. **Offer design pattern gallery**: "Would you like to see examples of common business problems that entity resolution can solve? I can show you a gallery of entity resolution design patterns with real-world use cases. This might help you articulate your specific problem or give you ideas."

4. **If user wants to see patterns**: Present the Entity Resolution Design Pattern Gallery from POWER.md. For each pattern, explain:
   - What problem it solves
   - What the goal is
   - What data sources are typically involved
   - What business value it delivers
   
   Ask: "Do any of these patterns match your situation? You can use one as a starting point and customize it for your specific needs."
   
   If they select a pattern, use it as a template for their problem statement:
   - Pre-fill data source types based on the pattern
   - Suggest matching criteria from the pattern
   - Adapt the pattern to their specific context

5. **Set expectations**: "Let's start by understanding your business problem. This will help us tailor the boot camp to your specific needs. We'll identify your data sources, define success criteria, and create a plan."

6. **Ask guided discovery questions**: Work through these questions systematically. Present common scenarios to help them identify their use case.

   **Note**: If user selected a design pattern, use it to guide these questions and pre-fill answers where applicable.

   **Question 1: What problem are you trying to solve?**
   - Deduplication, data matching, identity verification, fraud detection, relationship discovery, or master data management?
   - If they selected a pattern: "You mentioned [pattern name]. Let's refine that for your specific situation..."
   
   **Question 2: What data sources are involved?**
   - For each source: name, type, record count, update frequency, access method
   - If they selected a pattern: "The [pattern name] pattern typically involves [list sources]. Do you have similar data sources?"
   
   **Question 3: What types of entities?**
   - People, organizations, both, or other?
   - If they selected a pattern: "For [pattern name], we typically work with [entity types]. Is that correct for you?"
   
   **Question 4: What matching criteria matter most?**
   - Names, addresses, contact info, identifiers, dates, other attributes?
   - If they selected a pattern: "The [pattern name] pattern usually focuses on [matching criteria]. Are these the right attributes for your case?"
   
   **Question 5: What's the desired outcome?**
   - Output format, use case, integration needs, success metrics
   - If they selected a pattern: "The typical goal for [pattern name] is [goal]. What specific outcomes are you looking for?"

7. **Encourage visual explanations**: Ask for diagrams showing data architecture, data flows, or example records. If images contain placeholders like [variable], ask them to specify what each represents.

8. **Identify the scenario**: Categorize as Customer 360, Fraud Detection, Data Migration, Compliance, or Marketing scenario. If they selected a pattern, this is already identified.

9. **Create problem statement document**: Save to `docs/business_problem.md`:
   ```markdown
   # Business Problem Statement
   
   **Date**: [Current date]
   **Project**: [Project name]
   **Design Pattern**: [Pattern name if selected, or "Custom"]
   
   ## Problem Description
   [One sentence description]
   
   ## Use Case Category
   [Customer 360 / Fraud Detection / Data Migration / Compliance / Marketing / Healthcare / Supply Chain / KYC / Insurance / Vendor MDM]
   
   ## Design Pattern Reference
   [If a pattern was selected, include:]
   - **Pattern**: [Pattern name]
   - **Standard Goal**: [Pattern's typical goal]
   - **Customizations**: [How this differs from the standard pattern]
   
   ## Data Sources
   1. **[Source name]**
      - Type: [Database/CSV/API/etc.]
      - Records: ~[count]
      - Entity type: [People/Organizations/Both]
      - Update frequency: [Static/Daily/Real-time]
      - Access: [How to access]
   
   2. **[Source name]**
      - [Same structure]
   
   ## Entity Types
   [People / Organizations / Both / Other]
   
   ## Key Matching Criteria
   - **[Attribute 1]** (High priority) - [Why important]
   - **[Attribute 2]** (Medium priority) - [Why important]
   - **[Attribute 3]** (Low priority) - [Why important]
   
   ## Success Criteria
   - [Measurable outcome 1]
   - [Measurable outcome 2]
   - [Measurable outcome 3]
   
   ## Desired Output
   **Format**: [Master list / API / Reports / Database export]
   **Use case**: [One-time / Ongoing / Real-time]
   **Integration**: [Standalone / Integrated with [systems]]
   
   ## Timeline
   **Target completion**: [Date]
   **Key milestones**: [List]
   
   ## Notes
   [Any additional context, constraints, or considerations]
   ```

10. **Update README.md**: Fill in the Overview and Business Problem sections with the information gathered. If a design pattern was selected, mention it in the overview.

11. **Propose solution approach**: Explain how Senzing can solve this and which modules will be most relevant. If they selected a pattern, reference how the boot camp will implement that pattern.

12. **Get confirmation**: "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"

13. **Transition to Module 2**: "Now let's look at your data sources to see if they need mapping. Please place sample data files in the `data/raw/` folder."

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created

## Workflow: Verify Data Sources Against SGES (Module 2)

**Time**: 10 minutes per data source

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified)

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

7. **Proceed to mapping**: For each data source that needs mapping, transition to the "Data Mapping End-to-End" workflow.

**Success indicator**: ✅ All data sources categorized + `docs/data_source_evaluation.md` created

## Workflow: Install Senzing Boot Camp Hooks (Before Module 3)

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
   cp senzing-bootcamp/hooks/data-quality-check.kiro.hook .kiro/hooks/
   cp senzing-bootcamp/hooks/backup-before-load.kiro.hook .kiro/hooks/
   cp senzing-bootcamp/hooks/test-before-commit.kiro.hook .kiro/hooks/
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

## Workflow: First-Time Guided Tour

Use this workflow when a user is new to Senzing and wants a general introduction without a specific problem in mind.

1. Call `get_capabilities` to discover available tools and confirm the MCP server is reachable.
2. Explain what entity resolution is — matching, relating, and deduplicating records about people and organizations across data sources. Use `search_docs` with query "what is entity resolution" for current documentation.
3. Show what Senzing data looks like by calling `get_sample_data` with dataset "las-vegas". Walk through a few records, explaining fields like `DATA_SOURCE`, `RECORD_ID`, `NAME_FULL`, `ADDR_FULL`, `PHONE_NUMBER`, etc.
4. Explain how Senzing resolves these records into entities — features are extracted, scored, and compared. Entity-centric learning means the engine improves resolution as more data arrives.
5. Ask the user what they'd like to explore next: mapping their own data, setting up the SDK, or diving deeper into concepts.

## Workflow: Data Mapping End-to-End

Use this workflow for each data source that needs mapping (identified in the "Verify Data Sources Against SGES" workflow). Complete the entire mapping process for one data source before moving to the next.

**Important**: While these steps are numbered sequentially, mapping is an iterative and exploratory process. Users can:
- Jump back to earlier steps when they discover new information
- Skip ahead to test ideas before completing all prior steps
- Revisit the profiling or planning stages after seeing quality analysis results
- Refine field mappings multiple times based on testing

Be flexible and supportive of non-linear exploration. The goal is a working transformation program, not strict adherence to the sequence.

**Before starting**: Confirm which data source you're currently mapping. If multiple sources need mapping, keep track of progress:
- Data Source 1: Customer Database → In Progress / Complete
- Data Source 2: Transaction Logs → Pending
- Data Source 3: Vendor Data → Pending

**For the current data source**:

1. **Start the mapping workflow**: Call `mapping_workflow` with `action='start'` and the user's source file path from `data/raw/` or `data/samples/` for this specific data source. The workflow will return a unique session ID for tracking this mapping.

2. **Step 1 — Profile**: Run the profiler script returned by the workflow, or read the data directly. Summarize:
   - Column names and their meanings
   - Data types (string, integer, date, etc.)
   - Sample values from each column
   - Null rates and data completeness
   - Any data quality issues observed
   
   Advance with `mapping_workflow` using `action='profile_summary'` and your analysis.

3. **Step 2 — Plan**: Identify the entity structure for this data source:
   - **Master entities**: Are these person records, organization records, or both?
   - **Child records**: Are there related records (e.g., multiple addresses per person)?
   - **Relationships**: Does this data describe relationships between entities?
   - **Lookup tables**: Are there reference data or code tables?
   
   Advance with `mapping_workflow` using `action='entity_plan'` and your plan.

4. **Step 3 — Map**: Map each source field to Senzing features and attributes:
   - Name fields → `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `NAME_ORG`
   - Address fields → `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE`, `ADDR_COUNTRY`
   - Contact fields → `PHONE_NUMBER`, `EMAIL_ADDRESS`, `WEBSITE_ADDRESS`
   - Identifier fields → `SSN_NUMBER`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER`, `NATIONAL_ID_NUMBER`
   - Date fields → `DATE_OF_BIRTH`, `REGISTRATION_DATE`
   - Assign confidence scores (0-100) based on data quality
   
   **CRITICAL**: Never guess attribute names. Use the mapping workflow to ensure correct names.
   
   Advance with `mapping_workflow` using `action='schema_mappings'` and your field mappings.

5. **Step 4 — Generate Starter Code**: The workflow generates:
   - Sample Senzing JSON output showing the target format
   - Starter mapper code (Python, JavaScript, or other languages)
   - Transformation logic for complex fields
   
   This provides the foundation for the transformation program.
   
   Advance with `mapping_workflow` using `action='paths'` and the output file paths.

6. **Step 5 — Build the Transformation Program**: Help the user create a complete, runnable program for this data source. The program should:

   **Input handling**:
   - Read from the original data source format (CSV file, JSON file, database query, API endpoint, etc.)
   - Handle file paths, connection strings, or API credentials
   - Process records in batches for large datasets
   
   **Transformation logic**:
   - Apply the field mappings from Step 3
   - Handle data type conversions (dates, numbers, booleans)
   - Combine fields when needed (e.g., first_name + last_name → NAME_FULL)
   - Split fields when needed (e.g., full address → ADDR_LINE1, ADDR_CITY, ADDR_STATE)
   - Apply data cleansing (trim whitespace, normalize formats)
   - Set required fields: `DATA_SOURCE` (unique identifier for this source) and `RECORD_ID` (unique within the source)
   
   **Output handling**:
   - Write Senzing JSON records to output file (one JSON object per line, JSONL format)
   - Or prepare records for direct loading via SDK
   - Include error handling for malformed input records
   
   **Example program structure** (Python):
   ```python
   import csv
   import json
   
   def transform_record(source_record):
       """Transform a single source record to Senzing format"""
       senzing_record = {
           "DATA_SOURCE": "CUSTOMER_DB",
           "RECORD_ID": source_record["customer_id"],
       }
       
       # Map name fields
       if source_record.get("full_name"):
           senzing_record["NAME_FULL"] = source_record["full_name"]
       
       # Map address fields
       if source_record.get("address"):
           senzing_record["ADDR_FULL"] = source_record["address"]
       
       # Map contact fields
       if source_record.get("phone"):
           senzing_record["PHONE_NUMBER"] = source_record["phone"]
       
       return senzing_record
   
   def main():
       with open("input_data.csv", "r") as infile:
           reader = csv.DictReader(infile)
           
           with open("output_senzing.jsonl", "w") as outfile:
               for row in reader:
                   try:
                       senzing_record = transform_record(row)
                       outfile.write(json.dumps(senzing_record) + "\n")
                   except Exception as e:
                       print(f"Error processing record {row.get('customer_id')}: {e}")
   
   if __name__ == "__main__":
       main()
   ```
   
   **Customize the program** based on:
   - User's preferred programming language (Python, JavaScript, Java, etc.)
   - Data source type (file, database, API)
   - Data volume (single file vs. batch processing)
   - Environment (local script, cloud function, ETL pipeline)
   
   **Save the program**: Save to `src/transform/transform_[datasource_name].py` (or appropriate extension for the language).

7. **Step 6 — Test the Program**: Run the transformation program on sample data from `data/samples/`:
   - Start with a small subset (10-100 records) for initial testing
   - Verify the program runs without errors
   - Check that output files are created in `data/transformed/`
   - Inspect a few output records manually
   
   Call `lint_record` with sample output records to validate they're syntactically correct Senzing JSON.

8. **Step 7 — Quality Analysis**: Run the program on a larger sample (1000+ records if available). Call `analyze_record` with several mapped records to evaluate:
   - Feature distribution (are all important features populated?)
   - Attribute coverage (what percentage of records have each attribute?)
   - Data quality scores (completeness, consistency, validity)
   - Potential issues (missing critical data, malformed values)
   
   Advance with `mapping_workflow` using `action='verdict'` and your quality assessment.

9. **Step 8 — Review Results**: Review the transformation program and results with the user:
   - Confirm the program successfully reads the input data
   - Verify the output format is correct Senzing JSON
   - Review data quality metrics
   - Discuss any data quality concerns
   - Confirm the program is ready for production use or needs adjustments

10. **Step 9 — Iterate if needed**: If quality issues were found or the program needs refinement, make adjustments. This is where the iterative nature of mapping becomes clear:
   - Go back to Step 3 to adjust field mappings
   - Return to Step 2 to reconsider entity structure
   - Revisit Step 1 if you need to understand the data better
   - Fix bugs in the transformation logic
   - Adjust confidence scores
   - Handle edge cases better
   - Improve data cleansing
   - Add validation or error handling
   
   Retest the program after changes. You may cycle through steps multiple times before achieving the desired quality.

11. **Step 10 — Save and Document**: Ensure the transformation program is properly saved and documented:
   - Program saved in `src/transform/transform_[datasource_name].py`
   - Create `docs/mapping_[datasource_name].md` with:
     - Field mappings
     - Transformation logic
     - Data quality results
     - How to run the program
     - Dependencies and prerequisites
   - Save sample output in `data/transformed/[datasource_name]_sample.jsonl`

12. **Mark data source as complete**: Once the user is satisfied with the transformation program for this data source, mark it as complete and move to the next data source that needs mapping.

13. **Repeat for remaining data sources**: If there are more data sources that need mapping (from Module 2), repeat this entire workflow for each one. Each data source should have its own transformation program in `src/transform/`.

14. **Transition to Module 4**: Once all data sources have been either mapped (with working transformation programs) or confirmed as SGES-compliant, proceed to Module 4 (SDK Setup).

### Important Rules for Data Mapping

- NEVER hand-code Senzing JSON attribute names — common mistakes include using `BUSINESS_NAME_ORG` instead of the correct `NAME_ORG`, or `EMPLOYER_NAME` instead of `NAME_ORG`.
- NEVER guess method signatures — use `generate_scaffold` or `get_sdk_reference` for correct API calls.
- Always validate output with `lint_record` before proceeding to loading.

## Workflow: Quick SDK Test Load

Use this workflow when a user wants to install Senzing and load data to see entity resolution results.

This workflow is now split into two parts:
- **Part A**: SDK installation and configuration (Module 4)
- **Part B**: Creating loading programs for each data source (Module 5)

### Part A: SDK Installation and Configuration (Module 4)

1. Determine the user's platform (Linux distro, macOS, Windows, Docker).
2. Call `sdk_guide` with `topic='install'` and the detected platform for installation commands.
3. Call `sdk_guide` with `topic='configure'` for engine configuration (SQLite for evaluation).
4. Verify the installation is working correctly.

### Part B: Create Loading Programs (Module 5)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before starting**: Identify which data sources are ready to load:
- Data sources that were mapped in Module 3 (have transformation program output)
- Data sources that were SGES-compliant from Module 2 (can load directly)

**For each data source**:

1. **Identify the input data**: Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 3)
   - Direct SGES-compliant data files
   - Database query results
   - API responses

2. **Create the loading program**: Help the user build a complete program that loads this specific data source. The program should:

   **Connection handling**:
   - Initialize the Senzing engine
   - Connect to the configured database (SQLite or PostgreSQL)
   - Handle connection errors gracefully
   
   **Record loading**:
   - Read Senzing JSON records from the input source
   - Call the SDK's add record method for each record
   - Use the correct `DATA_SOURCE` identifier for this source
   - Process records in batches for efficiency
   
   **Error handling**:
   - Catch and log errors for individual records
   - Continue processing even if some records fail
   - Track which records succeeded and which failed
   
   **Progress tracking**:
   - Report loading progress (records processed, success rate)
   - Show timing information
   - Display entity resolution statistics if available
   
   **Example loading program** (Python):
   ```python
   import json
   from senzing import G2Engine, G2Exception
   
   def load_records(input_file, data_source_code):
       """Load Senzing JSON records into the engine"""
       
       # Initialize engine
       engine = G2Engine()
       config = {
           "PIPELINE": {
               "CONFIGPATH": "/etc/opt/senzing",
               "RESOURCEPATH": "/opt/senzing/g2/resources",
               "SUPPORTPATH": "/opt/senzing/data"
           },
           "SQL": {
               "CONNECTION": "sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db"
           }
       }
       engine.init("LoaderApp", json.dumps(config), False)
       
       # Load records
       success_count = 0
       error_count = 0
       
       with open(input_file, 'r') as f:
           for line_num, line in enumerate(f, 1):
               try:
                   record = json.loads(line)
                   engine.addRecord(
                       data_source_code,
                       record.get("RECORD_ID"),
                       json.dumps(record)
                   )
                   success_count += 1
                   
                   if success_count % 100 == 0:
                       print(f"Loaded {success_count} records...")
                       
               except G2Exception as e:
                   error_count += 1
                   print(f"Error on line {line_num}: {e}")
               except json.JSONDecodeError as e:
                   error_count += 1
                   print(f"Invalid JSON on line {line_num}: {e}")
       
       # Cleanup
       engine.destroy()
       
       print(f"\nLoading complete:")
       print(f"  Success: {success_count}")
       print(f"  Errors: {error_count}")
   
   if __name__ == "__main__":
       load_records("customer_data_senzing.jsonl", "CUSTOMER_DB")
   ```
   
   **Customize the program** based on:
   - User's preferred programming language (Python, Java, C#, Rust)
   - Data source location (file, database, stream)
   - Data volume (small dataset vs. millions of records)
   - Environment (local script, cloud function, production pipeline)

3. **Use MCP tools for code generation**: Call `generate_scaffold` with workflow `add_records` to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

4. **Test with sample data**: Run the loading program on a small subset first:
   - Start with 10-100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

5. **Observe entity resolution in real time**: As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

6. **Load the full dataset**: Once testing is successful, run the program on the complete data source:
   - Monitor progress and performance
   - Watch for any errors or issues
   - Note loading statistics (time, throughput, error rate)

7. **Save the loading program**: Document and save the program:
   - Save with a clear name (e.g., `load_customer_db.py`)
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

8. **Mark data source as loaded**: Once loading is complete, mark this data source as loaded and move to the next data source.

9. **Repeat for remaining data sources**: If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

10. **Transition to Module 6**: Once all data sources have been loaded, proceed to Module 6 (Analyze Results and Troubleshoot) to explore and query the resolved entities.

## Workflow: Quick SDK Test Load (Legacy)

This workflow has been superseded by the separate Part A (Module 4) and Part B (Module 5) workflows above. The legacy workflow combined installation and loading, but the new approach separates them for clarity.

1. Determine the user's platform (Linux distro, macOS, Windows, Docker).
2. Call `sdk_guide` with `topic='install'` and the detected platform for installation commands.
3. Call `sdk_guide` with `topic='configure'` for engine configuration (SQLite for evaluation).
4. If the user has mapped data, call `sdk_guide` with `topic='load'` for record loading code.
5. If the user needs sample data, call `get_sample_data` to get CORD dataset records.
6. Alternatively, call `sdk_guide` with `topic='full_pipeline'` for a complete end-to-end script.

### Platform-Specific Notes

- **Linux (apt)**: `sdk_guide` with `platform='linux_apt'`
- **Linux (yum)**: `sdk_guide` with `platform='linux_yum'`
- **macOS ARM**: `sdk_guide` with `platform='macos_arm'`
- **Windows**: `sdk_guide` with `platform='windows'`
- **Docker**: `sdk_guide` with `platform='docker'`

### Anti-Pattern Checks

Before recommending any installation or deployment approach, call `search_docs` with `category='anti_patterns'` and a query describing the approach. This catches known pitfalls like:

- Installing without proper environment variables
- Using SQLite in production
- Missing database schema initialization
- Incorrect repository configuration

## Workflow: Create Query Programs to Answer the Business Problem (Module 6)

Use this workflow after all data sources have been loaded (Module 5). The goal is to create programs that query Senzing to answer the specific business problem identified in Module 1.

1. **Review the business problem**: Go back to Module 1 and review:
   - What problem was the user trying to solve?
   - What were their goals and requirements?
   - What questions did they need answered?
   - What outcomes were they expecting?

2. **Identify the query requirements**: Based on the business problem, determine what types of queries are needed. Common scenarios:

   **Deduplication use case**:
   - "Show me all duplicate customer records"
   - "Which records from System A match records in System B?"
   - "Export a master list of unique entities"
   
   **Identity verification use case**:
   - "Does this person exist in our database?"
   - "Find all records for a specific individual"
   - "What other identities are associated with this entity?"
   
   **Relationship discovery use case**:
   - "What entities are related to this person?"
   - "Show me all family members or business associates"
   - "Find networks of connected entities"
   
   **Data quality use case**:
   - "How many entities were created from my data?"
   - "What's the match rate across data sources?"
   - "Which records didn't match anything?"
   
   **Integration use case**:
   - "Export resolved entities to downstream system"
   - "Generate daily reports of new matches"
   - "Provide an API for real-time entity lookup"

3. **Design the query approach**: For each query requirement, determine the appropriate Senzing SDK methods:
   - **Search by attributes**: `searchByAttributes()` - Find entities matching specific criteria
   - **Get entity by ID**: `getEntityByEntityID()` - Retrieve a specific resolved entity
   - **Get entity by record**: `getEntityByRecordID()` - Find which entity a source record belongs to
   - **Get record**: `getRecord()` - Retrieve a specific source record
   - **Find path**: `findPathByEntityID()` - Discover relationships between entities
   - **Find network**: `findNetworkByEntityID()` - Explore entity networks
   - **Export entities**: `exportJSONEntityReport()` - Export all or filtered entities
   - **Get stats**: `getStats()` - Get resolution statistics

4. **Create the query program**: Help the user build a program tailored to their business problem. The program should:

   **Connection handling**:
   - Initialize the Senzing engine
   - Connect to the configured database
   - Handle connection errors gracefully
   
   **Query execution**:
   - Execute the appropriate SDK methods
   - Pass the correct parameters and flags
   - Handle pagination for large result sets
   
   **Result processing**:
   - Parse and format the JSON responses
   - Extract relevant information
   - Present results in a useful format (console, file, database, API)
   
   **Error handling**:
   - Catch and handle query errors
   - Provide meaningful error messages
   - Log issues for troubleshooting
   
   **Example query program** (Python - Find duplicates):
   ```python
   import json
   from senzing import G2Engine
   
   def find_duplicates_for_datasource(data_source_code):
       """Find all entities that contain records from the specified data source"""
       
       # Initialize engine
       engine = G2Engine()
       config = {
           "PIPELINE": {
               "CONFIGPATH": "/etc/opt/senzing",
               "RESOURCEPATH": "/opt/senzing/g2/resources",
               "SUPPORTPATH": "/opt/senzing/data"
           },
           "SQL": {
               "CONNECTION": "sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db"
           }
       }
       engine.init("QueryApp", json.dumps(config), False)
       
       # Export entities and filter for those with multiple records
       export_handle = engine.exportJSONEntityReport(0)
       
       duplicates = []
       while True:
           response = engine.fetchNext(export_handle)
           if not response:
               break
           
           entity = json.loads(response)
           records = entity.get("RESOLVED_ENTITY", {}).get("RECORDS", [])
           
           # Check if entity has multiple records from our data source
           source_records = [r for r in records if r.get("DATA_SOURCE") == data_source_code]
           if len(source_records) > 1:
               duplicates.append({
                   "entity_id": entity.get("RESOLVED_ENTITY", {}).get("ENTITY_ID"),
                   "record_count": len(source_records),
                   "records": source_records
               })
       
       engine.closeExport(export_handle)
       engine.destroy()
       
       return duplicates
   
   if __name__ == "__main__":
       dupes = find_duplicates_for_datasource("CUSTOMER_DB")
       print(f"Found {len(dupes)} entities with duplicate records:")
       for entity in dupes[:10]:  # Show first 10
           print(f"  Entity {entity['entity_id']}: {entity['record_count']} records")
   ```
   
   **Example query program** (Python - Search for person):
   ```python
   import json
   from senzing import G2Engine
   
   def search_for_person(name, address=None, phone=None):
       """Search for entities matching the given attributes"""
       
       engine = G2Engine()
       # ... initialize as above ...
       
       # Build search attributes
       search_attrs = {"NAME_FULL": name}
       if address:
           search_attrs["ADDR_FULL"] = address
       if phone:
           search_attrs["PHONE_NUMBER"] = phone
       
       # Execute search
       response = engine.searchByAttributes(json.dumps(search_attrs))
       results = json.loads(response)
       
       engine.destroy()
       
       return results.get("RESOLVED_ENTITIES", [])
   
   if __name__ == "__main__":
       matches = search_for_person("John Smith", address="123 Main St")
       print(f"Found {len(matches)} matching entities")
       for entity in matches:
           print(f"  Entity {entity['ENTITY_ID']}: Match score {entity.get('MATCH_SCORE', 'N/A')}")
   ```

5. **Use MCP tools for code generation**: Call `generate_scaffold` with the appropriate workflow:
   - `query` - For general entity queries
   - `search` - For attribute-based searching
   - `export` - For exporting entities
   - `get_entity` - For retrieving specific entities
   
   Call `get_sdk_reference` with `topic='functions'` to get correct method signatures and flags.

6. **Test the query program**: Run the program and verify it produces the expected results:
   - Does it answer the business question?
   - Are the results accurate and complete?
   - Is the output format useful?
   - Does it handle errors gracefully?

7. **Review results with the user**: Present the query results and discuss:
   - Does this solve the original business problem?
   - Are there unexpected results that need investigation?
   - Do we need additional queries or different approaches?
   - Is the data quality sufficient for the use case?

8. **Analyze resolution behavior**: If results are unexpected, investigate:
   - **Why did records match?** Use `getEntityByEntityID()` with flags to see match details and scoring
   - **Why didn't records match?** Use `whyRecordInEntity()` and `whyEntities()` to understand resolution decisions
   - **What features drove the match?** Review feature scores and match keys
   - Use `search_docs` with queries about resolution principles, scoring, or matching behavior

9. **Troubleshoot issues**: If there are problems:
   - **Error codes**: Use `explain_error_code` with any error codes encountered
   - **Wrong results**: Review data quality from Module 3, check mappings
   - **Performance issues**: Use `search_docs` with category `performance` or `database`
   - **Configuration issues**: Use `search_docs` with category `configuration`

10. **Iterate if needed**: Based on the results:
   - Refine the query program to better answer the question
   - Go back to Module 3 to improve data mappings if quality is insufficient
   - Adjust confidence scores or add missing attributes
   - Create additional query programs for related questions

11. **Save the query program**: Document and save the program:
   - Save with a clear name (e.g., `find_customer_duplicates.py`, `search_person.py`)
   - Document what business question it answers
   - Note how to run it and interpret results
   - Keep it for ongoing use or integration

12. **Complete the boot camp**: Once the user has query programs that successfully answer their business problem, the boot camp is complete! The user now has:
   - Understanding of their business problem (Module 1)
   - Evaluated data sources (Module 2)
   - Transformation programs for each data source (Module 3)
   - Configured Senzing SDK (Module 4)
   - Loading programs for each data source (Module 5)
   - Query programs that answer their business questions (Module 6)

## Workflow: Troubleshooting and Error Resolution

Use this workflow when a user encounters errors or unexpected behavior.

1. If the user provides an error code (e.g., `SENZ0005`), call `explain_error_code` immediately. This covers 456 error codes with causes and resolution steps.
2. If the error is behavioral (unexpected matches, missing entities), use `search_docs` to find relevant documentation about scoring, resolution principles, or configuration.
3. If the error involves SDK method calls, use `get_sdk_reference` with `topic='functions'` and a `filter` for the method name to verify correct signatures and parameters.
4. If the user is migrating from V3 to V4, use `get_sdk_reference` with `topic='migration'` to identify breaking changes (renamed methods, removed functions, flag changes).
5. For database-related issues, use `search_docs` with `category='database'` for tuning and setup guidance.

## Workflow: Explore Code Examples

Use this workflow when a user wants to see real-world Senzing code.

1. Use `find_examples` with a `query` describing what the user is looking for (e.g., "in-memory SQLite", "batch loading", "streaming export").
2. If a relevant repository is found, use `find_examples` with `repo` and `list_files=true` to see the file structure.
3. Use `find_examples` with `repo` and `file_path` to retrieve specific source files.
4. Walk through the code, explaining key patterns and how they relate to the user's goals.

## Activation Signals

This power should activate when the user mentions or is working on:

- Entity resolution, data matching, identity resolution, deduplication
- Senzing SDK, Senzing API, Senzing engine
- Data mapping to Senzing format, Senzing JSON
- CORD datasets, sample entity data
- Record loading, entity export, redo processing
- Senzing error codes (SENZ prefix)
- V3 to V4 migration
