# Senzing Boot Camp — Steering Guide

This document provides detailed workflows for the Senzing Boot Camp power. The agent loads this on-demand when users engage with specific boot camp activities.

## Code Quality Standards

**IMPORTANT**: All Python code generated or modified during the boot camp must follow PEP-8 standards:

- **Maximum line length**: 100 characters
- **No trailing whitespace**
- **4 spaces for indentation** (no tabs)
- **Proper docstrings** for all functions, classes, and modules
- **Organized imports** (standard library, third-party, local)
- **Consistent naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants

**Agent Responsibilities**:
1. Generate PEP-8 compliant code by default
2. Check user-provided code for PEP-8 compliance
3. Suggest specific fixes for violations
4. Explain benefits of compliance when relevant

See `docs/development/PEP8_COMPLIANCE.md` for complete details.

## Progress Tracking

Maintain awareness of the user's progress through the boot camp:
- Module 0: Quick Demo (Optional) - ⬜ Not started / ✅ Complete
- Module 1: Business Problem - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 2: Identify and Collect Data Sources - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 3: Evaluate Data Quality - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 4: Data Mapping - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 5: SDK Setup - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 6: Load Single Data Source - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 7: Multi-Source Orchestration - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 8: Query and Validate Results - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 9: Performance Testing - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 10: Security Hardening - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 11: Monitoring and Observability - ⬜ Not started / 🔄 In progress / ✅ Complete
- Module 12: Package and Deploy - ⬜ Not started / 🔄 In progress / ✅ Complete

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

4. **Create quickstart demo directory**:
   ```bash
   mkdir -p src/quickstart_demo
   ```
   
   All Module 0 demo code must be saved in `src/quickstart_demo/` to keep it separate from the main boot camp project code.

5. **Generate demo script**: Call `generate_scaffold` with workflow `full_pipeline` to create a complete demo script that:
   - Initializes Senzing with SQLite (no installation required if using Docker)
   - Loads the sample records
   - Queries the results
   - Shows resolved entities
   
   **Save the generated script to**: `src/quickstart_demo/demo_[dataset_name].py`
   
   Example: `src/quickstart_demo/demo_las_vegas.py`

6. **Save sample data**: Save the sample data retrieved from `get_sample_data` to:
   - `src/quickstart_demo/sample_data_[dataset_name].jsonl`
   
   Example: `src/quickstart_demo/sample_data_las_vegas.jsonl`

7. **Run the demo**: Execute the script and show:
   - Records being loaded
   - Entity resolution happening in real time
   - How many entities were created from the records
   - Example of a resolved entity showing all matching records

8. **Explain the results**: Walk through one resolved entity:
   - "These 3 records all matched because..."
   - Show the features that drove the match (name, address, phone)
   - Explain confidence scores
   - Show how Senzing combined the information

9. **Connect to their use case**: "Now imagine this with your data. Instead of [sample data], you'd have [their data sources]. The same process would find duplicates, match records across systems, and give you a unified view."

10. **Transition**: Ask if they want to:
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
   - `src/quickstart_demo/` - Module 0 demo code (optional)
   - `src/transform/` - Transformation programs (Module 3)
   - `src/load/` - Loading programs (Module 5)
   - `src/query/` - Query programs (Module 6)
   - `src/utils/` - Shared utilities
   - `tests/` - Test files
   - `docs/` - Design documents and specifications
   - `config/` - Configuration files
   - `logs/` - Log files
   - `monitoring/` - Dashboards and metrics
   
   **Important**: All source code, including utility scripts, must be in the `src/` directory (e.g., `src/utils/backup_database.sh`, `src/utils/rollback.sh`).
   
   **Initialize version control**:
   
   First, check if this is already a git repository:
   ```bash
   git rev-parse --git-dir 2>/dev/null
   ```
   
   If the command returns an error (not a git repository), ask the user:
   "Would you like to initialize this as a git repository? This will help track changes throughout the boot camp."
   
   If yes, initialize git:
   ```bash
   git init
   echo "# [Project Name] - Senzing Entity Resolution" > README.md
   ```
   
   If the directory is already a git repository, acknowledge it:
   "Great! I see this is already a git repository. We'll use it to track your boot camp progress."
   
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
   
   # Database files
   database/*.db
   database/*.db-journal
   !database/.gitkeep
   
   # Logs
   logs/*.log
   
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
   SENZING_DATABASE_URL=sqlite3://na:na@database/G2C.db
   
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

6. **Ask guided discovery questions**: Work through these questions systematically, ONE AT A TIME. Wait for the user's response to each question before asking the next one. This prevents overwhelming the user with multiple questions at once.

   **Note**: If user selected a design pattern, use it to guide these questions and pre-fill answers where applicable.

   **Question 1: What problem are you trying to solve?**
   - Ask: "What problem are you trying to solve? For example: deduplication, data matching, identity verification, fraud detection, relationship discovery, or master data management?"
   - If they selected a pattern: "You mentioned [pattern name]. Let's refine that for your specific situation..."
   - WAIT for their response before proceeding to Question 2
   
   **Question 2: What data sources are involved?**
   - Ask: "What data sources are involved? For each source, I'll need to know: name, type (database/CSV/API/etc.), approximate record count, update frequency, and how to access it."
   - If they selected a pattern: "The [pattern name] pattern typically involves [list sources]. Do you have similar data sources?"
   - WAIT for their response before proceeding to Question 3
   
   **Question 3: What types of entities?**
   - Ask: "What types of entities are we working with? People, organizations, both, or something else?"
   - If they selected a pattern: "For [pattern name], we typically work with [entity types]. Is that correct for you?"
   - WAIT for their response before proceeding to Question 4
   
   **Question 4: What matching criteria matter most?**
   - Ask: "What matching criteria matter most for your use case? For example: names, addresses, contact info, identifiers, dates, or other attributes?"
   - If they selected a pattern: "The [pattern name] pattern usually focuses on [matching criteria]. Are these the right attributes for your case?"
   - WAIT for their response before proceeding to Question 5
   
   **Question 5: What's the desired outcome?**
   - Ask: "What's the desired outcome? What format do you need (master list, API, reports, database export)? Is this one-time or ongoing? Any integration needs?"
   - If they selected a pattern: "The typical goal for [pattern name] is [goal]. What specific outcomes are you looking for?"
   - WAIT for their response before proceeding to step 7

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

13. **Transition to Module 2**: 
    
    "Great! Module 1 is complete. You now have a clear problem statement and project structure.
    
    **Module 1 Complete ✅**
    - ✅ Business problem defined
    - ✅ Data sources identified  
    - ✅ Success criteria set
    - ✅ Cost estimate created
    - ✅ Project structure ready
    
    **Common Issues to Watch For**:
    - If data sources are hard to access, document access requirements now
    - If stakeholder approval needed, use cost estimate document
    - If timeline is tight, consider starting with one data source
    
    Ready to move to Module 2 and collect your data sources?"

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created

## Workflow: Identify and Collect Data Sources (Module 2)

**Time**: 10-15 minutes per data source

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified)

**Purpose**: Collect the actual data files from each identified data source and store them in the project for analysis and mapping.

1. **Review identified data sources**: Recap the data sources identified in Module 1. Review `docs/business_problem.md` for the complete list.

2. **For each data source, collect the data**:

   First, ask: "How would you like to provide the data for [datasource_name]? You can upload a file, provide a URL/file path, connect to a database, or use an API endpoint."
   
   WAIT for their response, then proceed with the appropriate option:

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

3. **Verify data was received**:
   ```bash
   # Check that files are in data/raw/
   ls -lh data/raw/
   
   # Show first few lines of each file
   head -5 data/raw/customer_crm.csv
   head -5 data/raw/vendor_api.json
   ```

4. **Document data source locations**: Create or update `docs/data_source_locations.md`:
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
     curl -H "Authorization: Bearer $API_TOKEN" \
          https://api.vendor.com/v1/suppliers?limit=100
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
   ```

5. **Handle sensitive data appropriately**:
   - Remind user about data privacy (see `steering/security-privacy.md`)
   - If data contains PII, suggest anonymizing for testing
   - Ensure `.gitignore` excludes `data/raw/*` to prevent committing sensitive data
   - Document any data handling requirements in `docs/security_compliance.md`

6. **Create sample files if needed**:
   - If full dataset is very large (>1GB), create smaller sample files
   - Save samples to `data/samples/[datasource_name]_sample.[extension]`
   - Document sampling method (first N records, random sample, etc.)
   - Ensure sample is representative of full dataset

7. **Verify data quality at a glance**:
   - Check file sizes are reasonable
   - Verify files are not empty
   - Check file formats are as expected
   - Look for obvious issues (corrupted files, wrong format, etc.)

8. **Update data source tracking**:
   ```markdown
   Data Source Collection Status:
   - ✅ Customer CRM - Collected (data/raw/customer_crm.csv)
   - ✅ Vendor API - Sample collected (data/raw/vendor_api_sample.json)
   - ⬜ Legacy Database - Pending (requires VPN access)
   ```

9. **Transition to Module 3**: "Great! Now that we have the data files, let's evaluate each one to see if it needs mapping or if it's already in the right format for Senzing."

**Success indicator**: ✅ All data sources have files in `data/raw/` OR documented locations + `docs/data_source_locations.md` created + data collection status tracked

**Agent behavior**:
- Be patient with file uploads - they may take time
- Provide clear instructions for each data source type
- Help user create sample files if full datasets are too large
- Remind about data privacy and security
- Verify files are accessible before proceeding
- Document everything in `docs/data_source_locations.md`

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

## Workflow: Data Mapping End-to-End (Module 4)

Use this workflow for each data source that needs mapping (identified in Module 3). Complete the entire mapping process for one data source before moving to the next.

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

**Prerequisites**: ✅ Module 3 complete (sources evaluated, non-compliant sources identified)

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

   **IMPORTANT**: All generated Python code must be PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation).

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
   
   **Save the program**: Save to `src/transform/transform_[datasource_name].py` (or appropriate extension for the language). All transformation programs must be in the `src/transform/` directory.

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
   - Program saved in `src/transform/transform_[datasource_name].py` (all source code must be in `src/`)
   - Create `docs/mapping_[datasource_name].md` with:
     - Field mappings
     - Transformation logic
     - Data quality results
     - How to run the program
     - Dependencies and prerequisites
   - Save sample output in `data/transformed/[datasource_name]_sample.jsonl`

12. **Mark data source as complete**: Once the user is satisfied with the transformation program for this data source, mark it as complete and move to the next data source that needs mapping.

13. **Repeat for remaining data sources**: If there are more data sources that need mapping (from Module 2), repeat this entire workflow for each one. Each data source should have its own transformation program in `src/transform/`.

14. **Transition to Module 5**: Once all data sources have been either mapped (with working transformation programs) or confirmed as SGES-compliant, proceed to Module 5 (SDK Setup).

### Important Rules for Data Mapping

- NEVER hand-code Senzing JSON attribute names — common mistakes include using `BUSINESS_NAME_ORG` instead of the correct `NAME_ORG`, or `EMPLOYER_NAME` instead of `NAME_ORG`.
- NEVER guess method signatures — use `generate_scaffold` or `get_sdk_reference` for correct API calls.
- Always validate output with `lint_record` before proceeding to loading.

## Workflow: Quick SDK Test Load

Use this workflow when a user wants to install Senzing and load data to see entity resolution results.

This workflow is now split into two parts:
- **Part A**: SDK installation and configuration (Module 5)
- **Part B**: Creating loading programs for each data source (Module 6)

### Part A: SDK Installation and Configuration (Module 5)

**IMPORTANT**: Before installing, verify Senzing is not already installed to avoid conflicts or duplicate installations.

1. **Check if Senzing is already installed**:
   
   **Python check**:
   ```bash
   python -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null
   ```
   
   **System check (Linux/macOS)**:
   ```bash
   # Check for Senzing installation directory
   ls -la /opt/senzing 2>/dev/null
   ls -la /etc/opt/senzing 2>/dev/null
   
   # Check for Senzing Python package
   pip list | grep senzing
   ```
   
   **If Senzing is already installed**:
   - Ask user if they want to use the existing installation
   - Verify the version is V4.0
   - Skip to step 4 (verify installation)
   - If version is not V4.0 or installation is broken, proceed with reinstallation

2. **Determine the user's platform** (if not already installed):
   
   Ask: "What platform are you using? Linux, macOS, Windows, or would you prefer to use Docker?"
   
   WAIT for their response before proceeding to installation.

3. **Install Senzing** (if not already installed):
   - Call `sdk_guide` with `topic='install'` and the detected platform for installation commands
   - Follow platform-specific installation steps
   - Accept EULA during installation
   
   **If user chooses Docker deployment**:
   - Explain that Docker runtime images do NOT include PostgreSQL schema files
   - For PostgreSQL, must use two-stage initialization pattern:
     1. Create minimal SQL schema with CORRECT column names:
        - sys_cfg must use `sys_create_dt` (NOT sys_create_date)
        - sys_codes_used must include `code_id BIGSERIAL` column
        - sys_vars structure: (var_group, var_code, var_value)
     2. Insert sys_vars: VERSION='4.2.1', SCHEMA_VERSION='4.0'
     3. Use SDK's `set_default_config()` to create remaining tables
   - **Critical**: Wrong column names cause SENZ1001 errors that block initialization
   - Container CMD should be `tail -f /dev/null` to keep running
   - Use `docker exec` to run initialization and loading commands
   - All Docker files must be created in `docker/` directory
   - Reference `steering/docker-deployment.md` for complete verified schema examples

4. **Verify the installation is working correctly**:
   ```python
   # Test script to verify Senzing installation
   import senzing
   from senzing import G2Engine
   
   print(f"Senzing version: {senzing.__version__}")
   
   # Try to initialize engine
   try:
       engine = G2Engine()
       print("✅ Senzing engine initialized successfully")
       engine.destroy()
   except Exception as e:
       print(f"❌ Error initializing engine: {e}")
   ```

5. **Configure the engine**:
   - Call `sdk_guide` with `topic='configure'` for engine configuration
   - Ask: "Which database would you like to use? SQLite is good for evaluation, PostgreSQL is recommended for production."
   - WAIT for their response
   - Register data sources identified in Module 1
   - Create engine configuration JSON

6. **Test database connection**:
   ```python
   # Test database connectivity
   import json
   from senzing import G2Engine
   
   config = {
       "PIPELINE": {
           "CONFIGPATH": "/etc/opt/senzing",
           "RESOURCEPATH": "/opt/senzing/g2/resources",
           "SUPPORTPATH": "/opt/senzing/data"
       },
       "SQL": {
           "CONNECTION": "sqlite3://na:na@database/G2C.db"
       }
   }
   
   engine = G2Engine()
   engine.init("TestApp", json.dumps(config), False)
   
   # Try a simple operation
   stats = engine.getStats()
   print("✅ Database connection successful")
   print(f"Stats: {stats}")
   
   engine.destroy()
   ```

**Success criteria**: 
- ✅ Senzing installed (or existing installation verified)
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Data sources registered

**Agent behavior**:
- Always check for existing installation first
- Don't reinstall if compatible version exists
- Verify installation before proceeding to Module 6
- If installation fails, check common pitfalls guide

### Part B: Create Loading Programs (Module 6)

Use this workflow for each data source that needs to be loaded into Senzing. Create a separate loading program for each data source.

**Before starting**: Identify which data sources are ready to load:
- Data sources that were mapped in Module 4 (have transformation program output)
- Data sources that were SGES-compliant from Module 3 (can load directly)

**For each data source**:

1. **Identify the input data**: Determine where the Senzing-formatted JSON records are:
   - Output from a transformation program (Module 3)
   - Direct SGES-compliant data files
   - Database query results
   - API responses

2. **Create the loading program**: Help the user build a complete program that loads this specific data source. The program should:

   **IMPORTANT**: All generated Python code must be PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation).

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
               "CONNECTION": "sqlite3://na:na@database/G2C.db"
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
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.py`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

8. **Mark data source as loaded**: Once loading is complete, mark this data source as loaded and move to the next data source.

9. **Repeat for remaining data sources**: If there are more data sources to load, repeat this entire workflow for each one. Each data source should have its own loading program.

10. **Transition to Module 7**: Once all data sources have been loaded, proceed to Module 7 (Multi-Source Orchestration) to orchestrate loading of multiple sources with dependencies. If you only have one data source, skip to Module 8 (Query and Validate Results).

## Workflow: Multi-Source Orchestration (Module 7)

**Note**: For the comprehensive, detailed workflow for Module 7, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 7 section, 2,100+ lines).

Use this workflow after loading at least one data source successfully (Module 6). The goal is to orchestrate loading of multiple data sources with proper dependency management, error handling, and progress tracking.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 6 complete (at least one data source loaded successfully)

**Purpose**: Manage loading of multiple data sources with dependencies, optimize load order, implement parallel loading where appropriate, and handle errors across sources.

### Quick Summary

1. **Assess multi-source requirements** - Review all data sources and identify dependencies
2. **Define load order** - Create dependency graph and identify parallel opportunities
3. **Create orchestration script** - Build Python orchestration script with LoadOrchestrator class
4. **Implement error handling** - Handle failures per source with retry logic
5. **Add progress tracking** - Track progress across all sources with dashboard
6. **Test orchestration** - Test with sample data and failure scenarios
7. **Run full orchestration** - Execute complete load plan
8. **Validate multi-source results** - Verify cross-source matching and relationships
9. **Document orchestration** - Update load strategy documentation

### Key Features
- Dependency management between sources
- Parallel and sequential loading strategies
- Complete Python orchestration script (LoadOrchestrator class)
- Error handling per source with retry logic
- Progress tracking and reporting
- Load plan configuration examples

**Success indicator**: ✅ All data sources loaded + orchestration script created + progress tracked + results documented

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 7 section).

**Transition to Module 8**: Once all sources are loaded successfully, proceed to Module 8 (Query and Validate Results).

## Workflow: Query and Validate Results with UAT (Module 8)

**Note**: For the comprehensive, detailed workflow for Module 8, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 8 section, 1,000+ lines).

This workflow replaces the old "Module 7: Query Results" workflow. Use this after all data sources are loaded (Modules 6-7).

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source loaded)

**Purpose**: Create query programs to answer business questions and validate results through User Acceptance Testing (UAT).

### Quick Summary

1. **Review business requirements** - Go back to Module 1 and review the problem statement
2. **Create query programs** - Build programs for each business question (PEP-8 compliant)
3. **Test query programs** - Verify results with test data
4. **Create UAT test cases** - Define acceptance criteria and test cases
5. **Execute UAT tests** - Run tests and document results
6. **Resolve issues** - Fix any failed tests
7. **Get stakeholder sign-off** - Obtain formal approval
8. **Document query specifications** - Create query documentation

**IMPORTANT**: All query programs must be PEP-8 compliant (max 100 chars/line, no trailing whitespace, proper docstrings, 4-space indentation).

### Key Features
- Query program examples (Customer 360, Find Duplicates)
- UAT test case format (YAML)
- UAT executor guidance
- Issue tracking and resolution
- Sign-off documentation
- References to `steering/uat-framework.md`

**Success indicator**: ✅ Query programs created + UAT tests passed + Stakeholder sign-off obtained

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 8 section).

**Transition to Module 9**: If deploying to production, proceed to Module 9 (Performance Testing). If not deploying to production, boot camp complete!

## Workflow: Performance Testing and Benchmarking (Module 9)

**Note**: For the comprehensive, detailed workflow for Module 9, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 9 section, 1,500+ lines).

Use this workflow after query validation (Module 8) and before production deployment. The goal is to test performance and scalability to ensure the solution meets production requirements.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 8 complete (queries working, UAT passed)

**Purpose**: Benchmark transformation, loading, and query performance; test scalability; identify bottlenecks; validate production readiness.

### Quick Summary

1. **Define performance requirements** - Set targets for throughput and response time
2. **Benchmark transformation** - Test transformation speed
3. **Benchmark loading** - Test loading performance
4. **Benchmark queries** - Test query response times and concurrent users
5. **Profile resource utilization** - Monitor CPU, memory, disk I/O
6. **Test scalability** - Test with increasing data volumes
7. **Generate performance report** - Document results and recommendations
8. **Optimize if needed** - Address any bottlenecks

### Key Features
- Complete benchmark scripts (transformation, loading, queries)
- Concurrent query testing
- Resource monitoring
- Scalability projections
- Performance report template
- Optimization recommendations

**Success indicator**: ✅ Performance targets met + Benchmarks documented + Bottlenecks identified + Production readiness confirmed

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 9 section).

**Transition to Module 10**: Once performance testing is complete, proceed to Module 10 (Security Hardening).

## Workflow: Security Hardening (Module 10)

**Note**: For the comprehensive, detailed workflow for Module 10, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 10 section, 1,500+ lines).

Use this workflow after performance testing (Module 9) and before production deployment. The goal is to secure the application and data for production use.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 9 complete (performance validated)

**Purpose**: Implement secrets management, authentication/authorization, encryption, PII handling, security scanning, and vulnerability assessment.

### Quick Summary

1. **Assess security requirements** - Review compliance needs (GDPR, CCPA, HIPAA, etc.)
2. **Implement secrets management** - Use AWS Secrets Manager, Azure Key Vault, or env vars
3. **Implement authentication/authorization** - Add API keys, JWT, RBAC
4. **Enable encryption** - Encrypt data at rest and in transit
5. **Implement PII handling** - Mask PII, log access, implement retention policies
6. **Run security scanning** - Scan dependencies, code, and containers
7. **Create security audit document** - Document all security measures
8. **Document security procedures** - Create runbooks and train team

### Key Features
- Secrets management (AWS, Azure, environment variables)
- API authentication (API keys, JWT tokens)
- Role-based access control (RBAC)
- Encryption at rest and in transit
- PII masking and access logging
- Security scanning tools (safety, bandit, trivy, semgrep)
- Security audit template

**Success indicator**: ✅ Secrets managed + Authentication implemented + Encryption enabled + PII protected + Vulnerabilities fixed + Security audit complete

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 10 section).

**Transition to Module 11**: Once security hardening is complete, proceed to Module 11 (Monitoring and Observability).

## Workflow: Monitoring and Observability (Module 11)

**Note**: For the comprehensive, detailed workflow for Module 11, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 11 section, 1,500+ lines).

Use this workflow after security hardening (Module 10) and before final deployment. The goal is to set up comprehensive monitoring, logging, and alerting for production operations.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 10 complete (security hardened)

**Purpose**: Implement distributed tracing, structured logging, metrics collection, APM integration, alerting rules, health checks, and monitoring dashboards.

### Quick Summary

1. **Choose monitoring stack** - Select Prometheus/Grafana, ELK, Cloud, or APM
2. **Implement metrics collection** - Add Prometheus metrics to application
3. **Configure structured logging** - Implement JSON logging
4. **Set up distributed tracing** (optional) - Add OpenTelemetry tracing
5. **Create health check endpoints** - Implement liveness, readiness, health checks
6. **Configure alerting rules** - Set up critical and warning alerts
7. **Create monitoring dashboards** - Build Grafana dashboards
8. **Deploy monitoring stack** - Deploy with Docker Compose
9. **Create runbooks** - Document alert response procedures
10. **Test monitoring** - Verify metrics, logs, alerts, and dashboards
11. **Document monitoring setup** - Create monitoring guide

### Key Features
- Monitoring stack options (Prometheus/Grafana, ELK, Cloud, APM)
- Complete metrics implementation (Prometheus client)
- Structured logging (JSON formatter)
- Health check endpoints (liveness, readiness)
- Alerting rules (critical and warning)
- Grafana dashboard configuration
- Docker Compose for monitoring stack
- Runbook templates

**Success indicator**: ✅ Monitoring stack deployed + Metrics collected + Logs structured + Alerts configured + Dashboards created + Runbooks documented + Team trained

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 11 section).

**Transition to Module 12**: Once monitoring is fully operational, proceed to Module 12 (Package and Deploy).

## Workflow: Package and Deploy (Module 12)

**Note**: For the comprehensive, detailed workflow for Module 12, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 12 section, 1,000+ lines).

This workflow has been updated to reference Modules 9, 10, and 11. Use this workflow after monitoring setup (Module 11) to package and deploy your production-ready solution.

**Time**: 2-3 hours

**Prerequisites**: 
- ✅ Module 9 complete (performance tested)
- ✅ Module 10 complete (security hardened)
- ✅ Module 11 complete (monitoring configured)

**Purpose**: Refactor code into production package structure, add comprehensive tests, apply language-specific packaging, generate deployment documentation, and create deployment artifacts.

### Quick Summary

1. **Review production readiness** - Verify all prerequisites met
2. **Refactor code structure** - Organize into production package
3. **Integrate security, performance, and monitoring** - Combine all modules
4. **Create comprehensive test suite** - Add tests for all components
5. **Create deployment artifacts** - Generate Docker, K8s, CI/CD configs
6. **Generate deployment documentation** - Create deployment guide
7. **Create deployment scripts** - Build automation scripts
8. **Final validation** - Run all tests and checks

### Key Features
- References Modules 9, 10, 11 as prerequisites
- Integrates security measures from Module 10
- Integrates performance optimizations from Module 9
- Integrates monitoring from Module 11
- References `steering/disaster-recovery.md`
- References `steering/api-gateway-patterns.md`
- References `steering/multi-environment-strategy.md`
- Complete Dockerfile with security and health checks
- Docker Compose with full monitoring stack
- Comprehensive deployment guide

**Success indicator**: ✅ Code packaged + Tests passing + Deployment artifacts created + Documentation complete + Validation passed + Production deployed

**For detailed step-by-step instructions**, see `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 12 section).

**Boot Camp Complete!** 🎉

## Workflow: Quick SDK Test Load (Legacy)

This workflow has been superseded by the separate Part A (Module 5) and Part B (Module 6) workflows above. The legacy workflow combined installation and loading, but the new approach separates them for clarity.

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

## Workflow: Create Query Programs to Answer the Business Problem (Module 7) - LEGACY

**Note**: This workflow has been superseded by the new Module 8 workflow above. This section is kept for reference only.

**For current workflow**, see "Workflow: Query and Validate Results with UAT (Module 8)" above, or see the detailed workflow in `docs/development/NEW_WORKFLOWS_PHASE5.md`.

---

### Legacy Content (For Reference Only)

Use this workflow after all data sources have been loaded (Module 6). The goal is to create programs that query Senzing to answer the specific business problem identified in Module 1.

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
               "CONNECTION": "sqlite3://na:na@database/G2C.db"
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
   - Save in `src/query/` with a clear name (e.g., `src/query/find_customer_duplicates.py`, `src/query/search_person.py`)
   - All query programs must be in the `src/query/` directory
   - Document what business question it answers
   - Note how to run it and interpret results
   - Keep it for ongoing use or integration

12. **Complete the boot camp**: Once the user has query programs that successfully answer their business problem, the boot camp is complete! The user now has:
   - Understanding of their business problem (Module 1)
   - Collected data sources (Module 2)
   - Evaluated data sources (Module 3)
   - Transformation programs for each data source (Module 4)
   - Configured Senzing SDK (Module 5)
   - Loading programs for each data source (Module 6)
   - Query programs that answer their business questions (Module 7)

## Workflow: Troubleshooting and Error Resolution

Use this workflow when a user encounters errors or unexpected behavior.

1. If the user provides an error code (e.g., `SENZ0005`), call `explain_error_code` immediately. This covers 456 error codes with causes and resolution steps.
2. If the error is behavioral (unexpected matches, missing entities), use `search_docs` to find relevant documentation about scoring, resolution principles, or configuration.
3. If the error involves SDK method calls, use `get_sdk_reference` with `topic='functions'` and a `filter` for the method name to verify correct signatures and parameters.
4. For database-related issues, use `search_docs` with `category='database'` for tuning and setup guidance.

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


## Workflow: Refine and Package for Deployment (Module 8) - LEGACY

**Note**: This workflow has been superseded by the new Module 12 workflow above. This section is kept for reference only.

**For current workflow**, see "Workflow: Package and Deploy (Module 12)" above, or see the detailed workflow in `docs/development/NEW_WORKFLOWS_PHASE5.md`.

---

### Legacy Content (For Reference Only)

Use this workflow when the user has completed Modules 0-7 and wants to prepare their code for production deployment.

**Time**: 2-4 hours

**Goal**: Transform prototype code into a production-ready deployment package with proper structure, tests, and documentation.

### Step 1: Assess Current State

1. **Review existing code**:
   - Transformation programs in `src/transform/`
   - Loading programs in `src/load/`
   - Query programs in `src/query/`
   - Utility scripts in `src/utils/`

2. **Identify refactoring needs**:
   - Code duplication
   - Hard-coded values
   - Missing error handling
   - Inconsistent patterns
   - Lack of configuration management

3. **Document current functionality**:
   - What data sources are transformed?
   - What loading patterns are used?
   - What queries are implemented?
   - What dependencies exist?

### Step 2: Choose Deployment Configuration

Guide the user through key decisions:

1. **Target Database**:
   ```
   Current: SQLite (evaluation only)
   
   Production options:
   - PostgreSQL (recommended, best performance)
   - MySQL (if existing infrastructure)
   - MS SQL Server (Windows environments)
   - Oracle (enterprise environments)
   ```

2. **Programming Language**:
   ```
   If multiple languages used in boot camp:
   - Python (easiest, most common)
   - Java (enterprise, existing Java infrastructure)
   - C# (.NET environments)
   - Rust (performance-critical applications)
   
   Recommend: Stick with the language used in Modules 4-7
   ```

3. **Deployment Environment**:
   ```
   - On-premises servers
   - Cloud (AWS, Azure, GCP)
   - Docker containers (recommended)
   - Kubernetes (for scale)
   - Serverless (Lambda, Azure Functions)
   ```

4. **Integration Pattern** (from Module 7):
   ```
   - Batch processing
   - REST API
   - Streaming/event-driven
   - Database sync
   - Microservice
   ```

### Step 3: Refactor Code Structure

Transform boot camp code into proper package structure:

#### For Python Projects

1. **Create package structure**:
   ```bash
   mkdir -p my_senzing_project/{transform,load,query,utils}
   touch my_senzing_project/__init__.py
   touch my_senzing_project/{transform,load,query,utils}/__init__.py
   ```

2. **Refactor transformation code**:
   - Move `src/transform/transform_*.py` into package
   - Create base `Transformer` class
   - Extract common logic into utilities
   - Add configuration management
   - Implement proper logging

3. **Refactor loading code**:
   - Move `src/load/load_*.py` into package
   - Create base `Loader` class
   - Add batch processing support
   - Implement progress tracking
   - Add error recovery

4. **Refactor query code**:
   - Move `src/query/query_*.py` into package
   - Create `SenzingClient` wrapper
   - Implement query methods
   - Add result formatting
   - Add caching (if appropriate)

5. **Create configuration management**:
   ```python
   # my_senzing_project/config.py
   import os
   import yaml
   from dataclasses import dataclass
   
   @dataclass
   class Config:
       database_url: str
       senzing_config: str
       data_sources: dict
       logging_level: str
       
       @classmethod
       def from_yaml(cls, path: str):
           with open(path) as f:
               data = yaml.safe_load(f)
           return cls(**data)
       
       @classmethod
       def from_env(cls):
           return cls(
               database_url=os.getenv('DATABASE_URL'),
               senzing_config=os.getenv('SENZING_ENGINE_CONFIGURATION_JSON'),
               data_sources={},
               logging_level=os.getenv('LOG_LEVEL', 'INFO')
           )
   ```

6. **Create setup.py and pyproject.toml**:
   - Use `generate_scaffold` or create manually
   - List all dependencies
   - Define entry points
   - Add package metadata

7. **Update requirements.txt**:
   - Add all production dependencies
   - Create requirements-dev.txt for development dependencies
   - Pin versions for production

#### For Java Projects

1. **Create Maven/Gradle structure**:
   ```bash
   mkdir -p src/main/java/com/company/senzing/{transform,load,query,util}
   mkdir -p src/main/resources
   mkdir -p src/test/java/com/company/senzing
   ```

2. **Create pom.xml** with dependencies

3. **Refactor code into packages**

4. **Add Spring Boot** (optional, for REST API)

#### For C# Projects

1. **Create .NET solution structure**:
   ```bash
   dotnet new sln -n MySenzingProject
   dotnet new console -n MySenzingProject
   dotnet new xunit -n MySenzingProject.Tests
   ```

2. **Create .csproj** with dependencies

3. **Refactor code into namespaces**

### Step 4: Create Comprehensive Test Suite

1. **Set up testing framework**:
   - Python: pytest
   - Java: JUnit
   - C#: xUnit

2. **Create test directory structure**:
   ```bash
   mkdir -p tests/{test_transform,test_load,test_query}
   touch tests/__init__.py
   touch tests/conftest.py  # pytest configuration
   ```

3. **Write unit tests**:
   - Test each transformer with sample data
   - Test validation logic
   - Test configuration loading
   - Test utility functions
   
   Example:
   ```python
   # tests/test_transform/test_customers.py
   import pytest
   from my_senzing_project.transform.customers import CustomerTransformer
   
   def test_customer_transformer_basic():
       transformer = CustomerTransformer()
       input_data = {
           "customer_id": "12345",
           "first_name": "John",
           "last_name": "Doe",
           "email": "john.doe@example.com"
       }
       result = transformer.transform(input_data)
       
       assert result["DATA_SOURCE"] == "CUSTOMERS"
       assert result["RECORD_ID"] == "12345"
       assert result["NAME_FULL"] == "John Doe"
       assert result["EMAIL_ADDRESS"] == "john.doe@example.com"
   
   def test_customer_transformer_missing_fields():
       transformer = CustomerTransformer()
       input_data = {"customer_id": "12345", "first_name": "John"}
       result = transformer.transform(input_data)
       
       assert result["NAME_FULL"] == "John"
   ```

4. **Write integration tests**:
   - Test end-to-end transformation pipeline
   - Test loading to Senzing (use test database)
   - Test query operations
   - Test error handling

5. **Write data quality tests**:
   - Validate transformed data format
   - Check attribute coverage
   - Verify data completeness

6. **Configure test runner**:
   ```ini
   # pytest.ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = 
       --verbose
       --cov=my_senzing_project
       --cov-report=html
       --cov-report=term
   ```

7. **Run tests and verify coverage**:
   ```bash
   pytest tests/ --cov=my_senzing_project --cov-report=html
   ```
   
   Target: >80% code coverage

### Step 5: Apply Language-Specific Packaging

#### Python

1. **Create setup.py**:
   ```python
   from setuptools import setup, find_packages
   
   setup(
       name="my-senzing-project",
       version="1.0.0",
       packages=find_packages(),
       install_requires=[
           "senzing>=4.0.0",
           "pandas>=2.0.0",
           "orjson>=3.9.0",
           "pyyaml>=6.0",
           "psycopg2-binary>=2.9.0",
       ],
       entry_points={
           "console_scripts": [
               "senzing-transform=my_senzing_project.transform.cli:main",
               "senzing-load=my_senzing_project.load.cli:main",
               "senzing-query=my_senzing_project.query.cli:main",
           ],
       },
   )
   ```

2. **Create pyproject.toml** (modern Python packaging)

3. **Test installation**:
   ```bash
   pip install -e .
   senzing-transform --help
   ```

#### Java

1. **Complete pom.xml** with all dependencies

2. **Build JAR**:
   ```bash
   mvn clean package
   ```

3. **Test JAR**:
   ```bash
   java -jar target/my-senzing-project-1.0.0.jar
   ```

#### C#

1. **Complete .csproj** with all dependencies

2. **Build package**:
   ```bash
   dotnet build
   dotnet pack
   ```

3. **Test package**:
   ```bash
   dotnet run
   ```

### Step 6: Generate Deployment Documentation

Create comprehensive documentation in `docs/`:

1. **docs/deployment.md**:
   - Prerequisites
   - Installation steps
   - Configuration guide
   - Database setup
   - Running the application
   - Troubleshooting

2. **docs/configuration.md**:
   - All configuration options
   - Environment variables
   - Configuration file format
   - Examples for dev/staging/prod

3. **docs/api.md** (if REST API):
   - Endpoint documentation
   - Request/response examples
   - Authentication
   - Error codes

4. **docs/monitoring.md**:
   - Metrics to monitor
   - Logging configuration
   - Health check endpoints
   - Alerting setup

5. **docs/troubleshooting.md**:
   - Common issues and solutions
   - Error code reference
   - Performance tuning
   - Support contacts

6. **Update README.md**:
   - Project overview
   - Quick start guide
   - Link to detailed documentation
   - License information

### Step 7: Create Deployment Artifacts

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application
   COPY my_senzing_project/ ./my_senzing_project/
   COPY config/ ./config/
   
   # Set environment
   ENV PYTHONPATH=/app
   ENV CONFIG_PATH=/app/config/config.prod.yaml
   
   # Run application
   CMD ["python", "-m", "my_senzing_project.load.cli"]
   ```

2. **Create docker-compose.yml**:
   ```yaml
   version: '3.8'
   
   services:
     postgres:
       image: postgres:15
       environment:
         POSTGRES_DB: senzing
         POSTGRES_USER: senzing
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
     
     senzing-app:
       build: .
       depends_on:
         - postgres
       environment:
         DATABASE_URL: postgresql://senzing:${DB_PASSWORD}@postgres:5432/senzing
         SENZING_ENGINE_CONFIGURATION_JSON: ${SENZING_CONFIG}
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
   
   volumes:
     postgres_data:
   ```

3. **Create deployment scripts**:
   ```bash
   # scripts/deploy.sh
   #!/bin/bash
   set -e
   
   ENV=$1
   
   if [ -z "$ENV" ]; then
       echo "Usage: ./deploy.sh [dev|staging|prod]"
       exit 1
   fi
   
   echo "Deploying to $ENV..."
   
   # Run tests
   pytest tests/
   
   # Build Docker image
   docker build -t my-senzing-project:$ENV .
   
   # Deploy
   docker-compose -f docker-compose.$ENV.yml up -d
   
   echo "Deployment complete!"
   ```

4. **Create CI/CD pipeline** (GitHub Actions example):
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy
   
   on:
     push:
       branches: [main]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - run: pip install -r requirements.txt
         - run: pip install -r requirements-dev.txt
         - run: pytest tests/
     
     deploy:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - run: ./scripts/deploy.sh prod
   ```

5. **Create Kubernetes manifests** (if applicable):
   ```yaml
   # k8s/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: senzing-app
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: senzing-app
     template:
       metadata:
         labels:
           app: senzing-app
       spec:
         containers:
         - name: senzing-app
           image: my-senzing-project:latest
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: senzing-secrets
                 key: database-url
   ```

### Step 8: Validate Package

1. **Run all tests**:
   ```bash
   pytest tests/ --cov=my_senzing_project
   ```

2. **Check code quality**:
   ```bash
   # Python
   flake8 my_senzing_project/
   black --check my_senzing_project/
   mypy my_senzing_project/
   
   # Java
   mvn checkstyle:check
   
   # C#
   dotnet format --verify-no-changes
   ```

3. **Test installation**:
   ```bash
   # Python
   pip install -e .
   
   # Java
   mvn install
   
   # C#
   dotnet build
   ```

4. **Test Docker build**:
   ```bash
   docker build -t my-senzing-project:test .
   docker run my-senzing-project:test --help
   ```

5. **Test deployment in staging**:
   ```bash
   ./scripts/deploy.sh staging
   ```

6. **Verify documentation**:
   - All docs complete
   - Examples work
   - Links valid
   - README clear

### Step 9: Finalize and Document

1. **Create release notes**:
   ```markdown
   # Release v1.0.0
   
   ## Features
   - Customer data transformation
   - Batch loading to PostgreSQL
   - REST API for entity queries
   
   ## Requirements
   - Python 3.8+
   - PostgreSQL 12+
   - Senzing SDK 4.0+
   
   ## Installation
   See [docs/deployment.md](docs/deployment.md)
   ```

2. **Tag release**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Create deployment checklist**:
   ```markdown
   ## Pre-Deployment Checklist
   - [ ] All tests pass
   - [ ] Code quality checks pass
   - [ ] Documentation complete
   - [ ] Configuration reviewed
   - [ ] Database migrations ready
   - [ ] Monitoring configured
   - [ ] Backup strategy in place
   - [ ] Rollback plan documented
   - [ ] Stakeholders notified
   ```

4. **Document lessons learned**:
   - Update `docs/lessons_learned.md`
   - Note what worked well
   - Document challenges and solutions
   - Recommendations for future projects

### Transition to Production

Once Module 8 is complete:

1. **Schedule deployment**:
   - Choose low-traffic window
   - Notify stakeholders
   - Prepare rollback plan

2. **Deploy to production**:
   ```bash
   ./scripts/deploy.sh prod
   ```

3. **Verify deployment**:
   - Run health checks
   - Test critical paths
   - Monitor logs
   - Check metrics

4. **Monitor post-deployment**:
   - Watch for errors
   - Monitor performance
   - Validate data quality
   - Gather user feedback

5. **Handoff to operations**:
   - Provide documentation
   - Train operations team
   - Establish support process
   - Document escalation path

**Module 8 Complete!** 🎉

The code is now production-ready with:
- ✅ Clean package structure
- ✅ Comprehensive test suite
- ✅ Language-specific packaging
- ✅ Deployment documentation
- ✅ Docker containers
- ✅ CI/CD pipeline
- ✅ Monitoring and logging
- ✅ Ready for production deployment
