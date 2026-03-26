# Senzing Boot Camp - Data Flow Diagram

## Complete Data Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW OVERVIEW                          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  SOURCE SYSTEMS  │
│                  │
│  • CRM           │
│  • Database      │
│  • CSV Files     │
│  • APIs          │
│  • Spreadsheets  │
└────────┬─────────┘
         │
         │ Extract
         ▼
┌──────────────────┐
│   data/raw/      │
│                  │
│  • customers.csv │
│  • orders.json   │
│  • contacts.xlsx │
└────────┬─────────┘
         │
         │ Module 2: Collection
         │ Module 3: Quality Check
         ▼
┌──────────────────┐
│  TRANSFORMATION  │
│                  │
│  src/transform/  │
│  • Map fields    │
│  • Normalize     │
│  • Validate      │
└────────┬─────────┘
         │
         │ Module 4: Mapping
         ▼
┌──────────────────┐
│data/transformed/ │
│                  │
│  • customers.    │
│    jsonl (SGES)  │
│  • orders.jsonl  │
└────────┬─────────┘
         │
         │ Module 6: Loading
         ▼
┌──────────────────┐
│  SENZING ENGINE  │
│                  │
│  database/G2C.db │
│  • Match         │
│  • Relate        │
│  • Resolve       │
└────────┬─────────┘
         │
         │ Module 8: Querying
         ▼
┌──────────────────┐
│  RESOLVED DATA   │
│                  │
│  • Entities      │
│  • Relationships │
│  • Networks      │
└────────┬─────────┘
         │
         │ Module 12: Deployment
         ▼
┌──────────────────┐
│   APPLICATIONS   │
│                  │
│  • Dashboards    │
│  • Reports       │
│  • APIs          │
│  • Integrations  │
└──────────────────┘
```

## Detailed Transformation Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    TRANSFORMATION PIPELINE                          │
└─────────────────────────────────────────────────────────────────────┘

SOURCE DATA                TRANSFORMATION              SENZING JSON
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ customer_id  │          │              │          │ DATA_SOURCE  │
│ first_name   │──────────│  Mapping     │──────────│ RECORD_ID    │
│ last_name    │          │  Logic       │          │ NAME_FIRST   │
│ email        │          │              │          │ NAME_LAST    │
│ phone        │          │  • Combine   │          │ EMAIL_ADDRESS│
│ street       │          │  • Split     │          │ PHONE_NUMBER │
│ city         │          │  • Format    │          │ ADDR_FULL    │
│ state        │          │  • Validate  │          │ ADDR_CITY    │
│ zip          │          │              │          │ ADDR_STATE   │
└──────────────┘          └──────────────┘          │ ADDR_POSTAL  │
                                                     └──────────────┘

EXAMPLE:
┌──────────────────────────────────────────────────────────────────────┐
│ Input:                                                               │
│   customer_id: "12345"                                               │
│   first_name: "John"                                                 │
│   last_name: "Smith"                                                 │
│   email: "john.smith@example.com"                                    │
│   phone: "(702) 555-1234"                                            │
│   street: "123 Main St"                                              │
│   city: "Las Vegas"                                                  │
│   state: "NV"                                                        │
│   zip: "89101"                                                       │
├──────────────────────────────────────────────────────────────────────┤
│ Output (SGES):                                                       │
│   {                                                                  │
│     "DATA_SOURCE": "CUSTOMERS",                                      │
│     "RECORD_ID": "12345",                                            │
│     "NAME_FIRST": "John",                                            │
│     "NAME_LAST": "Smith",                                            │
│     "EMAIL_ADDRESS": "john.smith@example.com",                       │
│     "PHONE_NUMBER": "702-555-1234",                                  │
│     "ADDR_FULL": "123 Main St Las Vegas NV 89101",                   │
│     "ADDR_LINE1": "123 Main St",                                     │
│     "ADDR_CITY": "Las Vegas",                                        │
│     "ADDR_STATE": "NV",                                              │
│     "ADDR_POSTAL_CODE": "89101"                                      │
│   }                                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

## Loading Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        LOADING PIPELINE                             │
└─────────────────────────────────────────────────────────────────────┘

data/transformed/customers.jsonl
         │
         │ Read records
         ▼
┌──────────────────┐
│  Loading Program │
│                  │
│  src/load/       │
│  • Batch records │
│  • Add to engine │
│  • Track progress│
└────────┬─────────┘
         │
         │ SDK API calls
         ▼
┌──────────────────┐
│  Senzing Engine  │
│                  │
│  • Parse record  │
│  • Extract       │
│    features      │
│  • Match against │
│    existing      │
│  • Create/update │
│    entities      │
└────────┬─────────┘
         │
         │ Persist
         ▼
┌──────────────────┐
│  database/G2C.db │
│                  │
│  • Entities      │
│  • Relationships │
│  • Features      │
│  • Metadata      │
└──────────────────┘
```

## Multi-Source Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-SOURCE INTEGRATION                         │
└─────────────────────────────────────────────────────────────────────┘

SOURCE 1: CRM          SOURCE 2: Orders       SOURCE 3: Support
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Customers    │      │ Transactions │      │ Tickets      │
│              │      │              │      │              │
│ • Names      │      │ • Names      │      │ • Names      │
│ • Emails     │      │ • Addresses  │      │ • Emails     │
│ • Phones     │      │ • Phones     │      │ • Phones     │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ Transform           │ Transform           │ Transform
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ customers.   │      │ orders.jsonl │      │ support.jsonl│
│ jsonl        │      │              │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ Load                │ Load                │ Load
       │ (Module 6)          │ (Module 7)          │ (Module 7)
       └─────────────────────┴─────────────────────┘
                             │
                             ▼
                   ┌──────────────────┐
                   │  Senzing Engine  │
                   │                  │
                   │  Resolves across │
                   │  all sources     │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Unified Entities │
                   │                  │
                   │ John Smith       │
                   │ • CRM record     │
                   │ • 5 orders       │
                   │ • 2 tickets      │
                   └──────────────────┘
```

## Query Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                              │
└─────────────────────────────────────────────────────────────────────┘

APPLICATION REQUEST
         │
         │ "Find John Smith"
         ▼
┌──────────────────┐
│  Query Program   │
│                  │
│  src/query/      │
│  • Parse request │
│  • Build query   │
│  • Call SDK      │
└────────┬─────────┘
         │
         │ SDK API calls
         ▼
┌──────────────────┐
│  Senzing Engine  │
│                  │
│  • Search index  │
│  • Score matches │
│  • Retrieve      │
│    entities      │
└────────┬─────────┘
         │
         │ Return results
         ▼
┌──────────────────┐
│  Query Results   │
│                  │
│  • Entity ID     │
│  • Match score   │
│  • All records   │
│  • Relationships │
└────────┬─────────┘
         │
         │ Format response
         ▼
APPLICATION RESPONSE
```

## Backup Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKUP PIPELINE                              │
└─────────────────────────────────────────────────────────────────────┘

PROJECT FILES
┌──────────────────┐
│ • database/      │
│ • data/          │
│ • src/           │
│ • config/        │
│ • licenses/      │
└────────┬─────────┘
         │
         │ ./scripts/backup_project.sh
         ▼
┌──────────────────┐
│  Compression     │
│                  │
│  • Collect files │
│  • Exclude temp  │
│  • Create ZIP    │
└────────┬─────────┘
         │
         │ Timestamp
         ▼
┌──────────────────┐
│  backups/        │
│                  │
│  senzing-        │
│  bootcamp-       │
│  backup_         │
│  20260326_       │
│  143022.zip      │
└────────┬─────────┘
         │
         │ Transfer (optional)
         ▼
┌──────────────────┐
│  Off-site        │
│  Storage         │
│                  │
│  • Cloud         │
│  • Network drive │
│  • USB drive     │
└──────────────────┘
```

## Monitoring Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                      MONITORING PIPELINE                            │
└─────────────────────────────────────────────────────────────────────┘

APPLICATION
         │
         │ Operations
         ▼
┌──────────────────┐
│  Logging         │
│                  │
│  logs/           │
│  • Transform     │
│  • Loading       │
│  • Queries       │
│  • Errors        │
└────────┬─────────┘
         │
         │ Collect
         ▼
┌──────────────────┐
│  Metrics         │
│                  │
│  monitoring/     │
│  • Records/sec   │
│  • Query time    │
│  • Error rate    │
│  • Resource use  │
└────────┬─────────┘
         │
         │ Aggregate
         ▼
┌──────────────────┐
│  Dashboards      │
│                  │
│  • Performance   │
│  • Health        │
│  • Trends        │
│  • Alerts        │
└────────┬─────────┘
         │
         │ Alert on issues
         ▼
┌──────────────────┐
│  Notifications   │
│                  │
│  • Email         │
│  • Slack         │
│  • PagerDuty     │
└──────────────────┘
```

## Data Lineage

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LINEAGE TRACKING                         │
└─────────────────────────────────────────────────────────────────────┘

SOURCE → COLLECTION → QUALITY → TRANSFORM → LOAD → QUERY
  │          │           │          │         │       │
  │          │           │          │         │       │
  ▼          ▼           ▼          ▼         ▼       ▼
CRM      data/raw/   Quality    data/      database/ Results
System   customers   Score:85   transformed G2C.db
         .csv                   /customers
                                .jsonl

Metadata tracked:
• Source system: CRM v2.1
• Collection date: 2026-03-26
• Record count: 10,000
• Quality score: 85/100
• Transformation: transform_customers.py v1.0
• Load date: 2026-03-26
• Entities created: 8,500
• Duplicates resolved: 1,500
```

---

**Last Updated:** 2026-03-26
**Version:** 1.0.0
