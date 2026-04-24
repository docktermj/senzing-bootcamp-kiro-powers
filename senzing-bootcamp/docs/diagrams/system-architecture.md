# Senzing Bootcamp — System Architecture

> **Viewing:** ASCII art, viewable in any text editor or markdown viewer.

## Runtime Architecture

This shows how the pieces you build during the bootcamp fit together at runtime.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                            │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │ Transformation│   │   Loading    │   │   Query Programs     │   │
│  │   Programs    │   │   Programs   │   │                      │   │
│  │ (Module 4)    │   │ (Module 5)   │   │ (Module 7)           │   │
│  │               │   │              │   │  • find_duplicates   │   │
│  │ CSV/JSON →    │   │ JSONL →      │   │  • search_entities   │   │
│  │ Senzing JSONL │   │ Senzing SDK  │   │  • customer_360      │   │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘   │
│         │                   │                       │               │
│         ▼                   ▼                       ▼               │
│  ┌─────────────┐   ┌──────────────────────────────────────────┐   │
│  │ data/        │   │           SENZING SDK (V4)               │   │
│  │ transformed/ │   │                                          │   │
│  │ *.jsonl      │──▶│  add_record()    get_entity_by_record()  │   │
│  └─────────────┘   │  process_redo()   search_by_attributes()  │   │
│                     │  why_entity()     how_entity()            │   │
│                     └──────────────────┬───────────────────────┘   │
│                                        │                           │
│                                        ▼                           │
│                     ┌──────────────────────────────────────────┐   │
│                     │           DATABASE                       │   │
│                     │                                          │   │
│                     │  SQLite: database/G2C.db (evaluation)    │   │
│                     │  PostgreSQL: production                  │   │
│                     └──────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    OPTIONAL LAYERS                            │  │
│  │                                                              │  │
│  │  REST API (Module 11)     Search Index (Elasticsearch)       │  │
│  │  ┌─────────────────┐     ┌─────────────────────────┐        │  │
│  │  │ /health          │     │ Resolved entities →     │        │  │
│  │  │ /entity/{id}     │     │ indexed for fast lookup │        │  │
│  │  │ /search          │     │                         │        │  │
│  │  │ /load            │     │ Senzing FIRST, then     │        │  │
│  │  └─────────────────┘     │ search index SECOND     │        │  │
│  │                           └─────────────────────────┘        │  │
│  │                                                              │  │
│  │  Monitoring (Module 10)   Security (Module 9)               │  │
│  │  ┌─────────────────┐     ┌─────────────────────────┐        │  │
│  │  │ Metrics, alerts, │     │ Secrets mgmt, RBAC,     │        │  │
│  │  │ dashboards,      │     │ encryption, audit logs  │        │  │
│  │  │ health checks    │     │                         │        │  │
│  │  └─────────────────┘     └─────────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```text
Raw Data          Transformation       Senzing            Query/Output
─────────         ──────────────       ──────             ────────────

data/raw/    ──▶  src/transform/  ──▶  SDK add_record  ──▶  src/query/
 *.csv              transform_*.py       │                    find_duplicates
 *.json                │                 ▼                    search_entities
                       ▼              database/               customer_360
                  data/transformed/    G2C.db                    │
                   *.jsonl               │                       ▼
                                         ▼                  docs/results_
                                    Entity Resolution       validation.md
                                    (automatic matching)
```

## What Each Module Produces

```text
Module 0:  SDK installed + database/ configured
Module 1:  src/quickstart_demo/ (demo script + sample data)
Module 2:  docs/business_problem.md
Module 3:  data/raw/ (source files)
Module 4:  docs/data_source_evaluation.md, src/transform/ + data/transformed/ + docs/mapping_*.md
Module 5:  src/load/ + loaded database
Module 6:  Multi-source orchestration scripts
Module 7:  src/query/ + docs/results_validation.md
Module 8:  tests/performance/ + docs/performance_report.md
Module 9:  src/security/ + docs/security_checklist.md
Module 10: src/monitoring/ + monitoring/dashboards/
Module 11: Dockerfile + CI/CD + deployment/scripts/
```
