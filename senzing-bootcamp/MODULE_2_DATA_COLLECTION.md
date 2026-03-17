# Module 2: Data Collection Policy

## Overview

Module 2 is a new module added between Module 1 (Understand Business Problem) and Module 3 (Verify Data Sources). This module focuses on identifying and collecting the actual data sources that will be used for entity resolution.

## Purpose

After understanding the business problem in Module 1, users need to gather the actual data before they can evaluate or map it. Module 2 provides a structured approach to:

1. Identify data sources
2. Collect or link to data files
3. Store data in the proper location
4. Document data source information

## Workflow

### Step 1: Identify Data Sources

Help the user identify which data sources they need:
- What systems contain the relevant data?
- What format is the data in (CSV, JSON, database, API)?
- How much data is there?
- Is the data accessible?

### Step 2: Collect Data

The user can provide data in several ways:
- **Upload files**: User uploads CSV, JSON, or other data files
- **Provide URLs**: User provides links to data sources
- **Database connection**: User provides database connection details
- **API access**: User provides API endpoints and credentials

### Step 3: Store in `data/raw/`

All raw data sources must be stored in the `data/raw/` directory:
- Create `data/raw/` if it doesn't exist
- Save uploaded files to `data/raw/[source_name].[extension]`
- For large datasets, create representative samples
- Keep original filenames when possible for traceability

### Step 4: Document Data Sources

Create or update `docs/data_source_locations.md` with:
- Data source name
- Original location (URL, database, system)
- File location in project (`data/raw/...`)
- Date collected
- Sample size (if applicable)
- Contact person or system owner
- Any access restrictions or notes

## Directory Structure

```
project/
├── data/
│   ├── raw/                    # Raw data sources (Module 2)
│   │   ├── customers.csv
│   │   ├── vendors.json
│   │   └── transactions.jsonl
│   └── transformed/            # Transformed data (Module 4)
│       ├── customers.jsonl
│       ├── vendors.jsonl
│       └── transactions.jsonl
└── docs/
    └── data_source_locations.md  # Data source documentation
```

## Agent Behavior

When a user is in Module 2, the agent should:

- Help identify which data sources are needed based on Module 1 business problem
- Assist with uploading or linking to data files
- Create the `data/raw/` directory if it doesn't exist
- Save files to `data/raw/` with appropriate names
- For large datasets, help create representative samples (1000-10000 records)
- Create or update `docs/data_source_locations.md` with data source information
- Verify files are accessible and readable
- Transition to Module 3 once all data sources are collected

## Validation Gates

Before proceeding to Module 3, verify:

- [ ] At least one data source has been identified
- [ ] Data files are stored in `data/raw/` directory
- [ ] `docs/data_source_locations.md` exists and documents all sources
- [ ] Files are accessible and in expected format
- [ ] Sample sizes are appropriate (not too large for evaluation)

## Success Indicators

Module 2 is complete when:

- All identified data sources are collected or linked
- Files are properly stored in `data/raw/`
- Data source documentation is complete
- User is ready to evaluate data quality (Module 3)

## Common Issues

### Issue: Dataset Too Large
**Solution**: Create a representative sample of 1000-10000 records instead of loading the entire dataset

### Issue: Data Not Accessible
**Solution**: Work with user to get access, or use alternative data sources

### Issue: Multiple File Formats
**Solution**: Document each format, handle them separately in later modules

### Issue: Sensitive Data
**Solution**: Use anonymized or synthetic data for evaluation, document security requirements

## Integration with Other Modules

- **From Module 1**: Uses business problem definition to identify which data sources are needed
- **To Module 3**: Provides raw data files for quality evaluation
- **To Module 4**: Raw data will be transformed into Senzing JSON format

## File Naming Conventions

Use descriptive names for data files:
- `customers.csv` - Customer data from CRM
- `vendors.json` - Vendor data from procurement system
- `transactions_sample.jsonl` - Sample of transaction data
- `employees_2024.csv` - Employee data snapshot

Avoid:
- Generic names like `data.csv` or `file1.json`
- Special characters or spaces in filenames
- Extremely long filenames

## Documentation Template

Example `docs/data_source_locations.md`:

```markdown
# Data Source Locations

## Customer Data
- **Source**: CRM System (Salesforce)
- **Original Location**: https://company.salesforce.com/customers
- **File Location**: `data/raw/customers.csv`
- **Date Collected**: 2024-03-15
- **Sample Size**: 5,000 records (full dataset: 50,000)
- **Contact**: John Smith (john.smith@company.com)
- **Notes**: Exported via Salesforce API, includes all active customers

## Vendor Data
- **Source**: Procurement Database (PostgreSQL)
- **Original Location**: postgres://prod-db.company.com/procurement
- **File Location**: `data/raw/vendors.json`
- **Date Collected**: 2024-03-15
- **Sample Size**: Full dataset (2,500 records)
- **Contact**: Jane Doe (jane.doe@company.com)
- **Notes**: Direct database export, includes vendor contact information
```

## Data Lineage Tracking

Module 2 is where data lineage tracking begins. Track where data came from, when it was collected, and who collected it. See `steering/data-lineage.md` for comprehensive lineage tracking guidance.

### Quick Lineage Tracking

Document in `docs/data_lineage.yaml`:

```yaml
sources:
  customers_crm:
    type: database
    location: postgresql://prod-db.company.com/crm
    table: customers
    extracted_date: 2026-03-17
    extracted_by: john.doe@company.com
    record_count: 500000
    file_location: data/raw/customers_crm.csv
```

**Agent behavior**: Create `docs/data_lineage.yaml` when starting Module 2. Add each data source as it's collected. Load `steering/data-lineage.md` if user asks about lineage tracking or compliance.

## Related Documentation

- `POWER.md` - Main boot camp guide with Module 2 overview
- `steering/steering.md` - Detailed Module 2 workflow steps
- `steering/agent-instructions.md` - Agent behavior for Module 2
- `steering/data-lineage.md` - Data lineage tracking (load on demand)
- `steering/common-pitfalls.md` - Common Module 2 pitfalls
- `steering/security-privacy.md` - Data privacy considerations

## Version History

- **v3.0.0** (2026-03-17): Added data lineage tracking enhancement
- **v2.0.0** (2024-03-17): Module 2 added to boot camp structure
