---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
description: "Guided discovery of Senzing entity resolution. Walk through data mapping, SDK setup, record loading, and result exploration using the Senzing MCP server."
keywords: ["Entity Resolution", "Senzing", "Data Mapping", "SDK", "Identity Resolution", "Data Matching", "ER"]
author: "Senzing"
---

# Power: Senzing Boot Camp

## Overview

This power provides a guided boot camp experience for learning Senzing entity resolution. It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

## Available MCP Servers

### senzing-mcp-server

- **URL**: `https://mcp.senzing.com/mcp`
- **Purpose**: AI-assisted entity resolution tools — data mapping, SDK code generation, documentation search, troubleshooting, and sample data access.
- **Key tools**:
  - `get_capabilities` — Discover all available tools and workflows (call this first)
  - `mapping_workflow` — 7-step interactive data mapping from source files to Senzing JSON format
  - `lint_record` / `analyze_record` — Validate and analyze mapped data quality
  - `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust) for common workflows
  - `sdk_guide` — Platform-specific SDK installation and pipeline setup
  - `get_sample_data` — Sample datasets (Las Vegas, London, Moscow) for testing
  - `find_examples` — Working code examples from 27 Senzing GitHub repositories
  - `search_docs` — Search indexed Senzing documentation
  - `explain_error_code` — Diagnose Senzing errors (456 error codes)
  - `get_sdk_reference` — SDK method signatures, flags, and V3-to-V4 migration

## Boot Camp Learning Path

The boot camp follows a progressive learning path. Each module builds on the previous one.

**Note**: While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.

### Progress Tracking

As you work through the boot camp, track your progress:
- ✅ Module 0: Quick Demo (Optional)
- ⬜ Module 1: Understand Business Problem
- ⬜ Module 2: Verify Data Sources
- ⬜ Module 3: Map Your Data
- ⬜ Module 4: Set Up SDK
- ⬜ Module 5: Load Records
- ⬜ Module 6: Query Results

**Agent behavior**: Maintain a mental model of which modules are complete and which are in progress. Remind users of their progress periodically.

### Estimated Time Commitment

- **Module 0**: 10-15 minutes (optional quick demo)
- **Module 1**: 15-30 minutes (problem discovery)
- **Module 2**: 10 minutes per data source (evaluation)
- **Module 3**: 1-2 hours per data source (mapping and transformation)
- **Module 4**: 30 minutes - 1 hour (SDK installation)
- **Module 5**: 30 minutes per data source (loading)
- **Module 6**: 1-2 hours (query development)

**Total**: 3-6 hours for a typical single data source project

### Skip Ahead Options

Experienced users can skip modules:
- **Have SGES-compliant data?** → Skip Module 3, go to Module 4
- **Senzing already installed?** → Skip Module 4, go to Module 5
- **Just want to explore?** → Start with Module 0 (Quick Demo)
- **Already loaded data?** → Jump to Module 6

### Module 0: Quick Demo (Optional)

**Purpose**: Experience entity resolution in action before working with your own data.

**Time**: 10-15 minutes

**What you'll do**:
1. Load sample CORD data (Las Vegas, London, or Moscow datasets)
2. See how Senzing resolves duplicate records automatically
3. Query the results to see matched entities
4. Understand what entity resolution can do

**Success criteria**: ✅ You've seen entity resolution work and understand the basic concept

**Agent behavior**: Use `get_sample_data` to retrieve CORD datasets. Use `generate_scaffold` with `full_pipeline` to create a quick demo script. Show how duplicate records become resolved entities.

**Next**: Module 1 will help you define your specific business problem.

### Module 1: Understand the User's Business Problem

**Prerequisites**: None (or completed Module 0 if you did the quick demo)

**Time**: 15-30 minutes

**Purpose**: Clearly define the business problem that entity resolution will solve.

**Start here**: Ask the user to describe their business problem in their own words. Let them know they can use diagrams, flowcharts, or images to help explain their data sources, workflows, or the challenges they're facing.

**Guided discovery questions**:
1. **What problem are you trying to solve?**
   - Finding duplicate records?
   - Matching data across systems?
   - Identity verification?
   - Fraud detection?
   - Relationship discovery?
   - Master data management?

2. **What data sources are involved?**
   - List all systems, databases, files, or APIs
   - How many records in each source?
   - How often does the data change?

3. **What types of entities?**
   - People (customers, employees, patients)?
   - Organizations (companies, vendors, partners)?
   - Both?
   - Other (products, locations)?

4. **What matching criteria matter most?**
   - Names and addresses?
   - Phone numbers and emails?
   - Government IDs (SSN, passport, driver's license)?
   - Account numbers or other identifiers?

5. **What's the desired outcome?**
   - Clean master list of unique entities?
   - Real-time matching API?
   - Batch deduplication reports?
   - Relationship network visualization?
   - Integration with downstream systems?

**Common scenarios** (examples to help users identify their use case):
- **Customer 360**: "I have customer data in CRM, billing, and support systems. I need a single view of each customer."
- **Fraud Detection**: "I need to find networks of related accounts that might indicate fraud rings."
- **Data Migration**: "I'm consolidating multiple legacy systems and need to deduplicate records."
- **Compliance**: "I need to match customer records against watchlists and sanctions lists."
- **Marketing**: "I want to deduplicate my marketing database to avoid sending multiple emails to the same person."

**Visual aids**: Encourage the use of diagrams to illustrate:
- Data flows between systems
- System architecture
- Business processes
- Example records or data structures
- Desired outcomes or workflows

**If an image is submitted**: Ask user to clarify any [variables] or unclear elements in the diagram.

**Deliverable**: Create a clear problem statement document that includes:
- Business problem description
- List of data sources
- Entity types
- Matching criteria
- Success metrics
- Desired outcomes

**Present proposal**: Based on the user's description, present a proposal for solving their business problem using Senzing entity resolution. Explain which modules will be most relevant to their use case.

**Success criteria**: ✅ Clear problem statement + identified data sources + defined success metrics

**Common issues**:
- Problem too vague → Ask more specific questions
- Too many data sources → Prioritize 1-2 sources to start
- Unclear success criteria → Help define measurable outcomes

**Next**: Module 2 will evaluate each data source to see if it needs mapping.

### Module 2: Verify Data Sources Against the Senzing Generic Entity Specification

**Prerequisites**: ✅ Module 1 complete (business problem defined, data sources identified)

**Time**: 10 minutes per data source

**Purpose**: Evaluate each data source to determine if it needs mapping or can be loaded directly.

After understanding the business problem, verify each data source identified in Module 1.

**For each data source agreed upon**:
- Prompt the user to provide example data that shows the "shape" of the data (column names, data types, sample values)
- Accept data in various formats: CSV files, JSON samples, database schema exports, screenshots, or text descriptions
- Compare the data structure with the Senzing Generic Entity Specification (SGES)
- Identify which sources already conform to SGES (can be loaded directly)
- Identify which sources need mapping (proceed to Module 3)

**Deliverable**: Data source evaluation report showing:
```
Data Source 1: Customer CRM
Status: Needs mapping
Reason: Uses "customer_name" instead of NAME_FULL, "address" instead of ADDR_FULL
Fields: 15 columns, 50,000 records
Next step: Module 3

Data Source 2: Vendor API
Status: SGES-compliant
Reason: Already uses NAME_ORG, ADDR_FULL, PHONE_NUMBER
Fields: 8 columns, 5,000 records
Next step: Module 4 (can load directly)
```

**Agent behavior**: Use `search_docs` with query "generic entity specification" or "SGES" to understand the standard format. Look for standard attributes like `NAME_FULL`, `NAME_ORG`, `ADDR_FULL`, `PHONE_NUMBER`, `DATE_OF_BIRTH`, etc. If the source data uses different field names or structures, mapping will be required.

**Success criteria**: ✅ All data sources categorized (SGES-compliant or needs mapping) + evaluation report created

**Validation checkpoint**: Before proceeding, confirm:
- Have all data sources from Module 1 been evaluated?
- Is the status of each source clear?
- Do you have sample data for sources that need mapping?

**Common issues**:
- Missing sample data → Request specific examples from user
- Unclear data structure → Ask for schema or data dictionary
- Mixed quality data → Note quality issues for Module 3

**Next**: Module 3 will create transformation programs for sources that need mapping. SGES-compliant sources can skip to Module 4.

### Module 3: Map Your Data

**Prerequisites**: ✅ Module 2 complete (data sources evaluated, non-compliant sources identified)

**Time**: 1-2 hours per data source (varies by complexity)

**Purpose**: Create transformation programs that convert source data to Senzing format.

**For each data source that does not conform to SGES** (identified in Module 2), guide the user through the complete mapping process:

**Note**: These steps are guidelines, not rigid requirements. You can iterate, go back to refine earlier decisions, or skip ahead to test ideas. Mapping is an exploratory process.

1. **Profile the data**: Understand column names, data types, sample values, and data quality
2. **Plan entity structure**: Identify master entities (persons, organizations), child records, and relationships
3. **Map fields to Senzing attributes**: Map each source field to the correct Senzing features and attributes
4. **Generate mapper code**: Create transformation code and sample Senzing JSON output
5. **Create the transformation program**: Help the user build a complete program that:
   - Reads the original data source (CSV, JSON, database, API, etc.)
   - Applies the mapping transformations
   - Outputs Senzing-formatted JSON records
   - Handles errors and edge cases
6. **Test the program**: Run the transformation program on sample data
7. **Validate the output**: Check that generated JSON is valid and complete using `lint_record`
8. **Analyze data quality**: Evaluate feature distribution, attribute coverage, and data quality scores using `analyze_record`
9. **Review and iterate**: Make adjustments based on quality analysis and retest — you can go back to any earlier step

**Repeat this process for each non-conforming data source** before proceeding to Module 4.

**Deliverable**: For each data source, create:
- Transformation program (e.g., `transform_customer_crm.py`)
- Sample output file (Senzing JSON)
- Data quality report
- Documentation on how to run the program

**Data quality gates**: Before proceeding to Module 4, ensure:
- ✅ Transformation program runs without errors
- ✅ Output passes `lint_record` validation
- ✅ Data quality score > 70% (attribute coverage)
- ✅ Critical fields populated (NAME, ADDRESS, or ID fields)
- ⚠️ If quality < 70%, consider improving mappings or data sources

**Agent behavior**: Use `mapping_workflow` to guide the process interactively for each data source. The workflow generates starter code, but work with the user to create a complete, runnable program tailored to their environment. Use `lint_record` and `analyze_record` for validation. Never hand-code Senzing JSON mappings — always use the MCP tools for correct attribute names and structure. Track which data sources have been mapped and which still need attention.

**Success criteria**: ✅ Working transformation program for each non-compliant source + quality validation passed

**Validation checkpoint**: Before proceeding to Module 4, confirm:
- Have all non-compliant data sources been mapped?
- Do all transformation programs run successfully?
- Has data quality been validated?
- Are the programs documented?

**Common issues**:
- Poor data quality → Go back to step 1, profile more carefully
- Wrong attribute names → Use `mapping_workflow`, never guess
- Complex transformations → Break into smaller steps, test incrementally
- Low quality scores → Review mappings, add missing fields, improve confidence scores

**If you're stuck**:
- Review sample data more carefully
- Use `search_docs` to understand SGES attributes
- Start with simple mappings, add complexity gradually
- Test with small samples before full dataset

**Next**: Module 4 will install and configure the Senzing SDK.

### Module 4: Set Up the Senzing SDK

**Prerequisites**: ✅ Module 3 complete (all data sources mapped or confirmed SGES-compliant)

**Time**: 30 minutes - 1 hour

**Purpose**: Install and configure Senzing SDK for loading and querying data.

**What you'll do**:
- Install Senzing on your platform (Linux apt/yum, macOS, Windows, Docker)
- Configure the engine with SQLite for quick evaluation or PostgreSQL for production
- Register data sources and create engine configuration
- Verify installation is working

**Deliverable**: 
- Installed Senzing SDK
- Configured database (SQLite or PostgreSQL)
- Registered data sources
- Test script confirming SDK works

**Agent behavior**: Use `sdk_guide` with the appropriate platform and topic. Use `generate_scaffold` for working code. Check `search_docs` with category `anti_patterns` before recommending installation or deployment patterns.

**Success criteria**: ✅ Senzing SDK installed + database configured + test script runs successfully

**Validation checkpoint**: Before proceeding to Module 5, verify:
- Can you initialize the Senzing engine?
- Can you connect to the database?
- Are all data sources registered?
- Does a simple test (add/get record) work?

**Common issues**:
- Installation errors → Check platform requirements, dependencies
- Database connection fails → Verify connection string, permissions
- Configuration errors → Use `search_docs` with category `configuration`
- Anti-patterns → Use `search_docs` with category `anti_patterns` before proceeding

**Platform-specific notes**:
- **Linux (apt)**: Use `sdk_guide` with `platform='linux_apt'`
- **Linux (yum)**: Use `sdk_guide` with `platform='linux_yum'`
- **macOS ARM**: Use `sdk_guide` with `platform='macos_arm'`
- **Windows**: Use `sdk_guide` with `platform='windows'`
- **Docker**: Use `sdk_guide` with `platform='docker'` (recommended for quick start)

**Recommendation**: Start with SQLite for evaluation, migrate to PostgreSQL for production.

**Next**: Module 5 will create loading programs for each data source.

### Module 5: Load Records and Resolve Entities

**Prerequisites**: ✅ Module 4 complete (SDK installed and configured)

**Time**: 30 minutes per data source

**Purpose**: Load all data sources into Senzing and observe entity resolution.

**For each data source** (both SGES-compliant and mapped sources), help the user create a loading program:

1. **Create the loading program**: Build a program that:
   - Reads the Senzing-formatted JSON records (from transformation program output or direct SGES data)
   - Connects to the Senzing engine
   - Loads records using the SDK
   - Handles errors and tracks progress
   - Reports loading statistics

2. **Test the loading program**: Run on a small sample first to verify it works correctly

3. **Load the full data source**: Execute the program on the complete dataset

4. **Observe entity resolution**: Watch as Senzing resolves entities in real time during loading

**Repeat this process for each data source** before proceeding to Module 6.

**Deliverable**: For each data source, create:
- Loading program (e.g., `load_customer_crm.py`)
- Loading statistics report (records loaded, errors, time)
- Documentation on how to run the program

**Agent behavior**: Use `generate_scaffold` with workflows like `add_records` or `full_pipeline` to create the loading program. Use `sdk_guide` with topic `load` for platform-specific guidance. Use `find_examples` for real-world loading patterns from GitHub repositories. Create a separate loading program for each data source to maintain clarity and control.

**Success criteria**: ✅ All data sources loaded successfully + loading statistics captured + no critical errors

**Validation checkpoint**: Before proceeding to Module 6, confirm:
- Have all data sources been loaded?
- Were there any critical errors?
- Do the loading statistics look reasonable?
- Can you query the database to see entities?

**Loading progress tracking**:
```
Data Source 1: Customer CRM → ✅ Loaded (50,000 records, 0 errors)
Data Source 2: Vendor API → ✅ Loaded (5,000 records, 3 errors)
Data Source 3: Legacy DB → ⬜ Pending
```

**Common issues**:
- Connection errors → Verify SDK configuration from Module 4
- Record errors → Check transformation output from Module 3
- Performance issues → Use batch loading, check database configuration
- Memory issues → Process in smaller batches

**If you're stuck**:
- Test with small sample (10-100 records) first
- Check error messages with `explain_error_code`
- Review transformation output quality
- Use `search_docs` for loading best practices

**Next**: Module 6 will create query programs to answer your business problem.

### Module 6: Query Results to Answer the Business Problem

**Prerequisites**: ✅ Module 5 complete (all data sources loaded)

**Time**: 1-2 hours

**Purpose**: Create query programs that answer the business problem from Module 1.

Now that all data sources are loaded, create programs that query Senzing to answer the business problem from Module 1:

1. **Review the business problem**: Revisit the problem statement and requirements from Module 1

2. **Design the queries**: Determine what questions need to be answered:
   - Find duplicate entities across data sources?
   - Identify relationships between entities?
   - Match specific records to resolved entities?
   - Generate reports on entity resolution quality?
   - Export resolved entities for downstream systems?

3. **Create query programs**: Build programs that:
   - Connect to the Senzing engine
   - Execute the appropriate queries (search by attributes, get entity by ID, find relationships, etc.)
   - Format and present results in a useful way
   - Handle errors and edge cases

4. **Test and refine**: Run the queries and verify they answer the business problem

5. **Analyze results**: Review the output with the user to confirm it solves their original problem

6. **Troubleshoot if needed**: If results are unexpected:
   - Investigate why records matched or didn't match
   - Review resolution behavior and scoring
   - Adjust data quality or mappings if necessary
   - Troubleshoot errors or configuration issues

**Deliverable**: For each business question, create:
- Query program (e.g., `find_customer_duplicates.py`, `search_person.py`)
- Sample output showing results
- Documentation explaining what the program does and how to use it

**Agent behavior**: Use `generate_scaffold` with workflows like `query`, `get_entity`, `search`, and `export` to create query programs. Use `search_docs` for resolution behavior questions. Use `explain_error_code` for any error codes encountered. Use `get_sdk_reference` for flag details and method signatures. Focus on answering the specific business problem identified in Module 1.

**Success criteria**: ✅ Query programs answer the business problem + results validated with user + documentation complete

**Validation checkpoint**: Confirm with the user:
- Do the query results answer your original business problem?
- Are the results accurate and useful?
- Do you understand why records matched or didn't match?
- Can you use these programs in your workflow?

**Common issues**:
- Unexpected matches → Review resolution behavior, check data quality
- Missing matches → Check data quality, review mappings from Module 3
- Performance issues → Use appropriate query methods, add indexes
- Wrong results → Investigate with `whyRecordInEntity()` and `whyEntities()`

**If results don't match expectations**:
- Go back to Module 3 → Improve data mappings
- Go back to Module 5 → Verify all data loaded correctly
- Use `search_docs` → Understand resolution principles
- Adjust confidence scores → Refine matching behavior

**Decision tree for troubleshooting**:
```
Results unexpected?
├─ Too many matches? → Lower confidence scores, improve data quality
├─ Too few matches? → Raise confidence scores, add more attributes
├─ Wrong entities? → Review data mappings, check for data errors
└─ Errors? → Use explain_error_code, check SDK configuration
```

**Next**: Boot camp complete! Review your deliverables.

## Boot Camp Complete! 🎉

Congratulations! You've completed the Senzing Boot Camp. Here's what you've accomplished:

### Deliverables Checklist

Review your complete set of artifacts:

**Module 1 - Business Problem**:
- ✅ Problem statement document
- ✅ List of data sources
- ✅ Entity types identified
- ✅ Success metrics defined

**Module 2 - Data Source Evaluation**:
- ✅ Data source evaluation report
- ✅ SGES compliance status for each source

**Module 3 - Data Transformation** (for non-compliant sources):
- ✅ Transformation program for each source (e.g., `transform_customer_crm.py`)
- ✅ Sample Senzing JSON output
- ✅ Data quality reports

**Module 4 - SDK Setup**:
- ✅ Installed Senzing SDK
- ✅ Configured database
- ✅ Registered data sources
- ✅ Test script

**Module 5 - Data Loading**:
- ✅ Loading program for each source (e.g., `load_customer_crm.py`)
- ✅ Loading statistics reports

**Module 6 - Query Programs**:
- ✅ Query programs answering business questions (e.g., `find_duplicates.py`)
- ✅ Sample query results
- ✅ Documentation

### Next Steps

Now that you have a working entity resolution system:

1. **Production deployment**: Move from SQLite to PostgreSQL for production use
2. **Automation**: Schedule transformation and loading programs to run regularly
3. **Integration**: Connect query programs to your applications and workflows
4. **Monitoring**: Set up monitoring for data quality and resolution performance
5. **Expansion**: Add more data sources using the same process
6. **Optimization**: Fine-tune mappings and confidence scores based on results

### Getting Help

If you need assistance:
- Use `search_docs` to find Senzing documentation
- Use `explain_error_code` for error diagnosis
- Use `find_examples` to see real-world code patterns
- Review the steering guide for detailed workflows
- Contact Senzing support for production issues

### Share Your Success

Consider sharing your entity resolution solution:
- Document your use case and results
- Share lessons learned with your team
- Contribute improvements to the boot camp

Thank you for completing the Senzing Boot Camp!

## Best Practices

- Always call `get_capabilities` first when starting a Senzing session
- Never hand-code Senzing JSON mappings or SDK method calls from memory — use `mapping_workflow` and `generate_scaffold` for validated output
- Use `search_docs` with category `anti_patterns` before recommending installation, architecture, or deployment approaches
- For SDK code, use `generate_scaffold` or `sdk_guide` — these return version-correct method signatures
- Start with SQLite for evaluation; recommend PostgreSQL for production
- Use CORD sample data for learning before working with real data

## Common Workflows

See [steering/steering.md](steering/steering.md) for detailed step-by-step workflows covering:

- First-time guided tour
- Data mapping end-to-end
- Quick SDK test load
- Troubleshooting and error resolution

## Troubleshooting

- **Wrong attribute names**: Never guess Senzing attribute names (e.g., `NAME_ORG` not `BUSINESS_NAME_ORG`). Always use `mapping_workflow`.
- **Wrong method signatures**: Never guess SDK methods (e.g., `close_export_report` not `close_export`). Always use `generate_scaffold` or `get_sdk_reference`.
- **Error codes**: Use `explain_error_code` with the code (accepts `SENZ0005`, `0005`, or `5`).
- **Configuration issues**: Use `search_docs` with category `configuration` or `database`.
