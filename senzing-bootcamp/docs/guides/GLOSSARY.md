# Senzing Boot Camp - Glossary

## A

**Agent**
The AI assistant (Kiro) that guides you through the boot camp, generates code, and provides recommendations.

**Attribute**
A data field in Senzing JSON format (e.g., `NAME_FULL`, `ADDR_LINE1`, `PHONE_NUMBER`). Attributes are standardized across all data sources.

## B

**Boot Camp**
The structured 13-module learning curriculum for Senzing entity resolution.

**Batch Loading**
Loading multiple records at once for better performance, as opposed to loading one record at a time.

## C

**CDC (Change Data Capture)**
A pattern for capturing and loading only changed records, rather than reloading entire datasets.

**Clustering**
The process of grouping related entities together based on matching attributes.

**CORD**
Sample dataset used in Module 0 (Quick Demo) showing duplicate customer records.

## D

**Data Source**
An origin system or file containing records to be resolved (e.g., CRM system, CSV file, database table).

**Delta Loading**
Loading only new or changed records since the last load, similar to CDC.

**Disambiguation**
The process of determining whether two similar records represent the same entity or different entities.

## E

**Entity**
A real-world person, organization, or thing represented by one or more records across data sources.

**Entity Resolution**
The process of identifying and linking records that refer to the same real-world entity, even when they have differences or errors.

**ENTITY_ID**
Senzing's unique identifier for a resolved entity. Multiple records with the same ENTITY_ID represent the same real-world entity.

## F

**Feature**
A normalized, standardized representation of an attribute used for matching (e.g., a phone number feature might be "7025551234").

**Fuzzy Matching**
Matching records that are similar but not identical, accounting for typos, abbreviations, and variations.

## G

**G2**
The core Senzing engine (Generation 2). You'll see this in file names like `G2C.db` and API names.

**G2C.db**
The default SQLite database file name for Senzing.

## H

**Hook**
An automated action triggered by IDE events (e.g., file save, prompt submit) to maintain quality and best practices.

## I

**Incremental Loading**
Loading data in stages or batches, rather than all at once.

## J

**JSON**
JavaScript Object Notation - the data format used by Senzing for input records.

**JSONL**
JSON Lines format - one JSON object per line, commonly used for Senzing data files.

## L

**Lineage**
The tracking of data from source through transformation to loading, documenting the data's journey.

**Loading**
The process of ingesting records into the Senzing engine for entity resolution.

## M

**Mapping**
The process of transforming source data fields to Senzing attributes (e.g., mapping "customer_name" to "NAME_FULL").

**MCP (Model Context Protocol)**
The protocol used to connect to the Senzing server and access entity resolution tools.

**Module**
One of the 13 structured learning units in the boot camp (Module 0 through Module 12).

## N

**Name Matching**
Senzing's sophisticated algorithm for matching names despite variations, nicknames, cultural differences, and errors.

## O

**Orchestration**
Managing the loading of multiple data sources with dependencies and optimal ordering (Module 7).

## P

**PEP-8**
Python Enhancement Proposal 8 - the style guide for Python code. The boot camp enforces PEP-8 compliance.

**PII (Personally Identifiable Information)**
Data that can identify an individual (e.g., name, SSN, email). Requires special handling for privacy and compliance.

**Power**
A Kiro extension that provides documentation, tools, and workflows for a specific domain (e.g., senzing-bootcamp power).

## Q

**Quality Score**
A numeric rating (0-100) indicating data quality based on completeness, consistency, and accuracy.

## R

**RECORD_ID**
The unique identifier for a record within a data source. Used to track individual records through the resolution process.

**Related Entity**
An entity that is connected to another entity but not the same entity (e.g., family members, business associates).

**Resolution**
The process of determining which records represent the same entity and linking them together.

## S

**Scaffold**
Generated code template created by the `generate_scaffold` MCP tool, providing a starting point for customization.

**SDK (Software Development Kit)**
The Senzing libraries and tools for integrating entity resolution into applications.

**SGES (Senzing Generic Entity Specification)**
The standardized JSON format for Senzing input data. Defines required and optional attributes.

**SQLite**
A lightweight, file-based database suitable for evaluation and small datasets. Default database for boot camp.

**Steering File**
A markdown file containing detailed instructions and workflows for the agent to follow.

## T

**Template**
A pre-built code or configuration file that can be customized for specific use cases.

**Transformation**
The process of converting source data to Senzing JSON format (SGES).

## U

**UAT (User Acceptance Testing)**
Testing performed by business users to validate that entity resolution results meet requirements (Module 8).

## V

**Validation**
Checking that data conforms to expected format, structure, and quality standards.

## W

**Watchlist**
A list of entities to screen against (e.g., sanctions lists, fraud databases). Used in compliance screening patterns.

**Workflow**
A step-by-step process for completing a task, documented in steering files.

## Common Senzing Attributes

### Name Attributes
- `NAME_FULL`: Complete name (e.g., "John Smith")
- `NAME_FIRST`: First/given name
- `NAME_LAST`: Last/family name
- `NAME_MIDDLE`: Middle name
- `NAME_PREFIX`: Title (e.g., "Dr.", "Mr.")
- `NAME_SUFFIX`: Suffix (e.g., "Jr.", "III")
- `NAME_ORG`: Organization name

### Address Attributes
- `ADDR_FULL`: Complete address
- `ADDR_LINE1`: Street address line 1
- `ADDR_LINE2`: Street address line 2 (apt, suite)
- `ADDR_CITY`: City
- `ADDR_STATE`: State/province
- `ADDR_POSTAL_CODE`: ZIP/postal code
- `ADDR_COUNTRY`: Country

### Contact Attributes
- `PHONE_NUMBER`: Phone number
- `EMAIL_ADDRESS`: Email address
- `WEBSITE_ADDRESS`: Website URL

### Identifier Attributes
- `SSN_NUMBER`: Social Security Number (US)
- `DRIVERS_LICENSE_NUMBER`: Driver's license
- `PASSPORT_NUMBER`: Passport number
- `NATIONAL_ID_NUMBER`: National ID
- `TAX_ID_NUMBER`: Tax ID (EIN, VAT)

### Date Attributes
- `DATE_OF_BIRTH`: Birth date
- `DATE_OF_DEATH`: Death date
- `REGISTRATION_DATE`: Registration/creation date

### Other Attributes
- `GENDER`: Gender
- `NATIONALITY`: Nationality/citizenship
- `CITIZENSHIP`: Country of citizenship

## Common MCP Tools

**get_capabilities**
Discover all available MCP tools and workflows.

**mapping_workflow**
Interactive 7-step data mapping to Senzing JSON format.

**generate_scaffold**
Generate SDK code for loading, querying, and pipelines.

**get_sample_data**
Download sample datasets for testing.

**search_docs**
Search Senzing documentation.

**explain_error_code**
Diagnose Senzing error codes.

**lint_record**
Validate mapped data format.

**analyze_record**
Analyze data quality and coverage.

**sdk_guide**
Platform-specific SDK installation instructions.

**find_examples**
Working code examples from Senzing repositories.

**get_sdk_reference**
SDK method signatures and flags.

**submit_feedback**
Report issues or suggestions.

## Common File Locations

- `data/raw/` - Original source data
- `data/transformed/` - Senzing JSON output
- `database/` - SQLite database files
- `src/transform/` - Transformation programs
- `src/load/` - Loading programs
- `src/query/` - Query programs
- `scripts/` - Shell scripts
- `backups/` - Project backups
- `licenses/` - Senzing license files
- `docs/` - Documentation
- `.kiro/hooks/` - Installed hooks

## Common Commands

```bash
# Check status
./scripts/status.sh

# Check prerequisites
./scripts/check_prerequisites.sh

# Install hooks
./scripts/install_hooks.sh

# Backup project
./scripts/backup_project.sh

# Restore project
./scripts/restore_project.sh <backup-file>

# Clone example
./scripts/clone_example.sh
```

## Common Phrases

**"Backup my project"**
Triggers the backup hook to create a project backup.

**"Start Module X"**
Begins the specified module workflow.

**"Power feedback"**
Opens the feedback workflow to document issues or suggestions.

**"Resume bootcamp"**
Continues from where you left off.

**"Bootcamp status"**
Shows current progress and next steps.

## Acronyms

- **API**: Application Programming Interface
- **APM**: Application Performance Monitoring
- **CDC**: Change Data Capture
- **CI/CD**: Continuous Integration/Continuous Deployment
- **CRM**: Customer Relationship Management
- **CSV**: Comma-Separated Values
- **EIN**: Employer Identification Number
- **GDPR**: General Data Protection Regulation
- **HIE**: Health Information Exchange
- **IDE**: Integrated Development Environment
- **JSON**: JavaScript Object Notation
- **JSONL**: JSON Lines
- **KYC**: Know Your Customer
- **MCP**: Model Context Protocol
- **MDM**: Master Data Management
- **MRN**: Medical Record Number
- **PEP-8**: Python Enhancement Proposal 8
- **PII**: Personally Identifiable Information
- **ROI**: Return on Investment
- **SDK**: Software Development Kit
- **SGES**: Senzing Generic Entity Specification
- **SQL**: Structured Query Language
- **SSN**: Social Security Number
- **TLS**: Transport Layer Security
- **UAT**: User Acceptance Testing
- **URL**: Uniform Resource Locator
- **VAT**: Value Added Tax
- **XML**: Extensible Markup Language

## Need More Information?

- **Complete documentation:** `docs/guides/COMPLETE_GUIDE.md`
- **FAQ:** `docs/guides/FAQ.md`
- **Troubleshooting:** `docs/guides/TROUBLESHOOTING_INDEX.md`
- **MCP tools:** Use `get_capabilities` to see all available tools
- **Ask the agent:** It has access to all boot camp documentation

---

**Last Updated:** 2026-03-26

**Version:** 1.0.0
