# Multi-Source Project Example: Customer 360

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, data flow, and expected results. The actual source code files are generated during the boot camp using MCP tools (`generate_scaffold`, `mapping_workflow`) in your chosen programming language (Python, Java, C#, Rust, or TypeScript).

## Overview

This example demonstrates a complete Customer 360 implementation using three data sources:

- CRM system (customers)
- E-commerce platform (orders/accounts)
- Support ticketing system (support contacts)

**Time to Complete:** 6-8 hours
**Difficulty:** Intermediate
**Modules Covered:** 2-8

## Business Problem

**Scenario:** A retail company has customer data scattered across three systems. They need a unified view to:

- Identify duplicate customers across systems
- Link customer interactions (purchases, support tickets)
- Enable personalized marketing
- Improve customer service

**Expected Outcomes:**

- Reduce duplicate customer records by 80%
- Link 95%+ of customer interactions to correct entities
- Enable single customer view for service reps

## Project Structure

```text
multi-source-customer360/
├── data/
│   ├── raw/
│   │   ├── crm_customers.csv           # 50,000 records
│   │   ├── ecommerce_accounts.csv      # 35,000 records
│   │   └── support_contacts.csv        # 20,000 records
│   ├── transformed/
│   │   ├── crm_customers.jsonl
│   │   ├── ecommerce_accounts.jsonl
│   │   └── support_contacts.jsonl
│   └── samples/
│       ├── crm_sample.csv              # 100 records for testing
│       ├── ecommerce_sample.csv
│       └── support_sample.csv
├── database/
│   └── G2C.db                          # SQLite database
├── src/
│   ├── transform/                      # One transformer per source
│   ├── load/
│   │   └── orchestrator                # Multi-source orchestration
│   ├── query/
│   │   ├── find_duplicates             # Cross-source duplicate finder
│   │   ├── customer_360_view           # Unified customer view
│   │   └── data_quality_report         # Quality metrics
│   └── utils/                          # Shared config and helpers
├── docs/
│   ├── business_problem.md
│   ├── data_source_evaluation.md
│   ├── mapping_specifications.md
│   ├── loading_strategy.md
│   └── results_validation.md
├── config/
│   └── senzing_config.json
├── tests/                              # Unit and integration tests
├── .env.example
├── .gitignore
├── <language-specific dependency file>  # e.g. requirements.txt, pom.xml, etc.
└── README.md                           # This file
```

## Architecture

### Data Flow

```text
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  CRM System  │   │  E-commerce      │   │  Support System  │
│  (50K recs)  │   │  (35K recs)      │   │  (20K recs)      │
└──────┬───────┘   └────────┬─────────┘   └────────┬─────────┘
       │                    │                       │
       ▼                    ▼                       ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Transform   │   │  Transform       │   │  Transform       │
│  CRM → JSON  │   │  Ecom → JSON     │   │  Support → JSON  │
└──────┬───────┘   └────────┬─────────┘   └────────┬─────────┘
       │                    │                       │
       └────────────────────┼───────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Orchestrator   │  Loads sources in order
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Senzing Engine │  Entity Resolution
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Query / Export  │  Customer 360, duplicates
                   └─────────────────┘
```

### Orchestration Pattern

The orchestrator loads sources sequentially in optimal order:

1. **CRM** (largest, highest quality) — establishes the entity baseline
2. **E-commerce** — matches against CRM entities, creates new ones as needed
3. **Support** — links to existing entities from CRM and E-commerce

This order maximizes match quality by loading the most complete data first.

## Sample Data

Each data source includes a 10-row sample in `data/samples/` so you can run through the example end-to-end without generating your own data.

### CRM Customers (crm_customers.csv)

```csv
customer_id,first_name,last_name,email,phone,address,city,state,zip,created_date
CRM-001,John,Smith,john.smith@email.com,555-0101,123 Main St,Boston,MA,02101,2023-01-15
CRM-002,Jane,Doe,jane.doe@email.com,555-0102,456 Oak Ave,Boston,MA,02102,2023-02-20
CRM-003,Bob,Johnson,bob.j@email.com,555-0103,789 Pine Rd,Cambridge,MA,02138,2023-03-10
```

### E-commerce Accounts (ecommerce_accounts.csv)

```csv
account_id,name,email,phone,shipping_address,city,state,postal_code,registration_date
EC-1001,John Smith,jsmith@email.com,5550101,123 Main Street,Boston,MA,02101,2023-01-20
EC-1002,Jane M Doe,jane.doe@email.com,555-0102,456 Oak Avenue,Boston,MA,02102,2023-02-25
EC-1003,Robert Johnson,robert.johnson@email.com,555-0199,321 Elm St,Somerville,MA,02144,2023-04-05
```

### Support Contacts (support_contacts.csv)

```csv
contact_id,full_name,email,phone,company,issue_date
SUP-5001,John Smith,john.smith@email.com,555-0101,Acme Corp,2023-06-15
SUP-5002,Jane Doe,j.doe@email.com,555-0102,Beta Inc,2023-07-20
SUP-5003,Bob Johnson,bob.j@email.com,555-0103,Gamma LLC,2023-08-10
```

## Step-by-Step Walkthrough

### Module 2: Define Business Problem

Document the problem statement, goals, data sources, and success criteria in `docs/business_problem.md`.

### Module 3: Collect Data Sources

Gather exports from each source system into `data/raw/`. In a real scenario, these come from database exports, API extracts, or file transfers.

### Module 4: Evaluate Data Quality

Assess each source for completeness, duplicates, and format consistency. Key metrics to evaluate:

- Field completeness (% non-null per column)
- Duplicate detection (e.g., duplicate emails within a source)
- Format consistency (phone number formats, address styles)

### Module 5: Map Data to Senzing Format

Each source requires a transformer that maps its fields to Senzing attributes:

| Source     | Source Fields                              | Senzing                                            |
|------------|--------------------------------------------|----------------------------------------------------|
| CRM        | first_name, last_name                      | NAME_FIRST, NAME_LAST                              |
| CRM        | email, phone                               | EMAIL_ADDRESS, PHONE_NUMBER                        |
| CRM        | address, city, state, zip                  | ADDR_FULL, ADDR_CITY, ADDR_STATE, ADDR_POSTAL_CODE |
| E-commerce | name                                       | NAME_FULL                                          |
| E-commerce | email, phone                               | EMAIL_ADDRESS, PHONE_NUMBER                        |
| E-commerce | shipping_address, city, state, postal_code | ADDR_FULL, ADDR_CITY, ADDR_STATE, ADDR_POSTAL_CODE |
| Support    | full_name                                  | NAME_FULL                                          |
| Support    | email, phone                               | EMAIL_ADDRESS, PHONE_NUMBER                        |
| Support    | company                                    | NAME_ORG                                           |

> The agent generates this code in your chosen language using `generate_scaffold` and `mapping_workflow` during the bootcamp.

### Module 0: Set Up SDK

Install the Senzing SDK for your chosen language and configure the engine with a SQLite connection for local development.

### Module 6-7: Load Data Sources with Orchestration

Run the loading program using the appropriate command for your chosen language.

The orchestrator:

1. Loads each source sequentially (CRM → E-commerce → Support)
2. Tracks success/error counts per source
3. Reports loading rate (records/sec)
4. Prints a summary when complete

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

### Module 8: Query and Validate Results

Run the query program using the appropriate command for your chosen language.

The Customer 360 view shows, for a given record:

- The resolved entity ID and name
- All linked records across sources
- Unified contact information (phones, emails, addresses)

The cross-source duplicate finder queries entities by record ID and identifies those with records from multiple sources.

> The agent generates this code in your chosen language using `generate_scaffold` during the bootcamp.

## Expected Results

After completing this example, you should see:

1. **Data Loading:**
   - CRM: 50,000 records loaded
   - E-commerce: 35,000 records loaded
   - Support: 20,000 records loaded
   - Total: 105,000 records

2. **Entity Resolution:**
   - Approximately 75,000-80,000 unique entities (25-30% reduction)
   - 15,000-20,000 entities with records from multiple sources
   - High-confidence matches based on name, email, phone, address

3. **Customer 360 Views:**
   - Complete customer history across all touchpoints
   - Linked interactions (purchases, support tickets)
   - Unified contact information

## What You'll Learn

1. **Multi-Source Complexity:** Managing dependencies and load order
2. **Data Quality Impact:** Better quality = better matching
3. **Orchestration:** Coordinating multiple data sources
4. **Validation:** Verifying results across sources

## Next Steps

1. Add more data sources (loyalty program, social media)
2. Implement incremental loading for daily updates
3. Create customer 360 API for applications
4. Add monitoring and alerting
5. Deploy to production

## Troubleshooting

### Issue: Low match rates

- Check data quality scores
- Review mapping specifications
- Verify name/address standardization

### Issue: Slow loading

- Use PostgreSQL instead of SQLite
- Increase batch sizes
- Optimize transformation code

### Issue: Unexpected matches

- Review match keys and thresholds
- Check for data quality issues
- Use `explain_error_code` for diagnostics

## Related Documentation

- [POWER.md](../../POWER.md) - Boot camp overview
- [MODULE_7_MULTI_SOURCE_ORCHESTRATION.md](../../docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md)
- [simple-single-source](../simple-single-source/README.md) - Simpler example

## Version History

- **v1.0.0** (2026-03-17): Initial multi-source example created
