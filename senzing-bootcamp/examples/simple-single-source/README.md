# Simple Single Source Example

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, data flow, and expected results. The actual source code files are generated during the bootcamp using MCP tools (`generate_scaffold`, `mapping_workflow`) in your chosen programming language (Python, Java, C#, Rust, or TypeScript).

A minimal Senzing project demonstrating customer deduplication with a single data source.

## Overview

**Use case:** Deduplicate customer records from a CRM system
**Data source:** Single CSV file with 10,000 customer records
**Database:** SQLite (no setup required)
**Time to complete:** 2-3 hours
**Modules covered:** 2-6, 8

## What You'll Learn

- Basic project structure
- Simple data mapping
- Loading data into Senzing
- Querying for duplicates
- Understanding entity resolution results

## Project Structure

```text
simple-single-source/
├── README.md                          # This file
├── data/
│   ├── raw/
│   │   └── customers.csv              # Source data (10K records)
│   ├── transformed/
│   │   └── customers.jsonl            # Senzing format
│   └── samples/
│       └── customers_sample.csv       # Small sample (100 records)
├── src/
│   ├── transform/                     # CSV → Senzing JSON
│   ├── load/                          # Load into Senzing
│   ├── query/                         # Find duplicates, get entities
│   └── utils/                         # Shared configuration
├── tests/                             # Unit tests
├── docs/
│   ├── business_problem.md            # Problem statement
│   ├── data_quality_report.md         # Quality analysis
│   ├── mapping_customers.md           # Mapping documentation
│   └── results_analysis.md            # Results and findings
├── <language-specific dependency file> # e.g. requirements.txt, pom.xml, etc.
├── .env.example                       # Environment template
└── .gitignore                         # Git ignore rules
```

## Quick Start

### 1. Install Dependencies

Install the Senzing SDK and any project dependencies using the appropriate package manager for your chosen language.

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for SQLite)
```

### 3. Transform Data

Run the transformation program using the appropriate command for your chosen language.

**Input:** `data/raw/customers.csv`
**Output:** `data/transformed/customers.jsonl`

### 4. Load Data

Run the loading program using the appropriate command for your chosen language.

This loads all 10,000 records into Senzing.

### 5. Find Duplicates

Run the query program using the appropriate command for your chosen language.

This shows entities with multiple records (duplicates).

### 6. Examine Entity

Run the entity detail program, passing an entity ID (e.g., entity 1), to see all records that matched for a specific entity.

## Data Flow

```text
customers.csv (10K records)
        │
        ▼
  ┌─────────────┐
  │  Transform   │  CSV → Senzing JSON
  └──────┬──────┘
         │
         ▼
  customers.jsonl
         │
         ▼
  ┌─────────────┐
  │    Load      │  Records → Senzing Engine → SQLite
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   Query      │  Find duplicates, get entity details
  └─────────────┘
```

## Sample Data

The `customers.csv` file contains realistic customer data. A 20-row sample is included at `data/samples/customers_sample.csv` so you can run through the example end-to-end without generating your own data:

```csv
customer_id,full_name,address,city,state,zip,phone,email
CUST-00001,John Smith,123 Main St,Springfield,IL,62701,555-123-4567,john.smith@example.com
CUST-00002,J. Smith,123 Main Street,Springfield,IL,62701,5551234567,jsmith@example.com
CUST-00003,John R Smith,123 Main St Apt 1,Springfield,IL,62701,(555) 123-4567,john.smith@example.com
...
```

Notice records 1, 2, and 3 are the same person with variations.

## Transformation Logic

Each CSV record is mapped to Senzing JSON format with these field mappings:

| CSV Field                    | Senzing Attribute |
|------------------------------|-------------------|
| customer_id                  | RECORD_ID         |
| full_name                    | NAME_FULL         |
| address + city + state + zip | ADDR_FULL         |
| phone                        | PHONE_NUMBER      |
| email                        | EMAIL_ADDRESS     |

All records use `DATA_SOURCE: "CUSTOMERS"`.

> The agent generates this code in your chosen language using `generate_scaffold` and `mapping_workflow` during the bootcamp.

## Expected Results

After loading 10,000 records:

- **Entities created:** ~7,500
- **Match rate:** ~25%
- **Average records per entity:** 1.33
- **Largest entity:** 5-8 records

This means about 2,500 records are duplicates.

## Understanding Results

### Entity Structure

A resolved entity contains all records that Senzing determined belong to the same real-world person:

```json
{
  "RESOLVED_ENTITY": {
    "ENTITY_ID": 1,
    "RECORDS": [
      {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": "CUST-00001",
        "ENTITY_NAME": "John Smith"
      },
      {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": "CUST-00002",
        "ENTITY_NAME": "J. Smith"
      }
    ],
    "FEATURES": {
      "NAME": [{ "FEAT_DESC": "John Smith", "USAGE_TYPE": "PRIMARY" }],
      "ADDRESS": [...],
      "PHONE": [...],
      "EMAIL": [...]
    }
  }
}
```

### Match Reasons

Use the `whyEntities` SDK method to understand why records matched. For the example above, output shows:

- Name similarity: 95%
- Address match: 100%
- Phone match: 100%
- Email match: 100%

## Customization

### Use Your Own Data

1. Replace `data/raw/customers.csv` with your CSV file
2. Update field mappings in the transformation program
3. Adjust `DATA_SOURCE` name if desired
4. Re-run transformation and loading

### Change Database to PostgreSQL

1. Install PostgreSQL
2. Create database: `createdb senzing`
3. Update `.env` with your PostgreSQL connection string
4. Re-run loading

## Troubleshooting

### Issue: No duplicates found

- Check that data loaded correctly
- Verify records have matching attributes
- Review data quality

### Issue: Too many/few matches

- This is normal — entity resolution is probabilistic
- Review match reasons with `whyEntities`
- Adjust matching thresholds (advanced)

## Next Steps

After completing this example:

1. **Understand the results:** Review entities and match reasons
2. **Try the multi-source example:** Learn orchestration
3. **Build your own project:** Apply to your data
4. **Explore advanced features:** Performance, security, monitoring

## Related Documentation

- `../../POWER.md` - Bootcamp overview
- `../../docs/modules/` - Module documentation
- `../../docs/guides/QUICK_START.md` - Quick start guide

## Version History

- **v3.0.0** (2026-03-17): Simple single source example created
