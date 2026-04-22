# Design Document

## Overview

Three architectural blueprint directories under `senzing-bootcamp/examples/` provide reference project structures at beginner, intermediate, and advanced levels. Each contains a README describing project layout, data flow, and expected results, plus sample CSV data where applicable. A clone script (`scripts/clone_example.py`) lets users copy examples into their workspace. An index README ties everything together.

## Architecture

### File Structure

```
senzing-bootcamp/examples/
├── README.md                                          # Index page
├── simple-single-source/
│   ├── README.md                                      # Beginner blueprint
│   └── data/samples/customers_sample.csv              # Sample data
├── multi-source-project/
│   ├── README.md                                      # Intermediate blueprint
│   └── data/samples/
│       ├── crm_sample.csv
│       ├── ecommerce_sample.csv
│       └── support_sample.csv
├── production-deployment/
│   └── README.md                                      # Advanced blueprint
senzing-bootcamp/scripts/
└── clone_example.py                                   # Cloner utility
```

### Design Decisions

1. Blueprints, not runnable code: Each example is a README-driven architectural reference. Actual code is generated during the bootcamp by MCP tools in the user's chosen language.
2. Sample CSV data included: Small sample files let users run through workflows end-to-end without generating data.
3. Progressive complexity: Simple (1 source, SQLite) → Multi-source (3 sources, PostgreSQL) → Production (full stack, Kubernetes).
4. Clone script is cross-platform: Uses Python `shutil` and `pathlib` for Linux, macOS, and Windows compatibility.

### Clone Script Flow

```
User runs clone_example.py
  → Lists 3 examples with descriptions
  → User picks one
  → User chooses: merge into current project OR new directory
  → Script copies files, skipping README.md on merge
  → Prints summary of copied/skipped items
```

## Acceptance Criteria Testability

| Criterion | Testable | Method |
|-----------|----------|--------|
| 1.1 simple-single-source directory exists with README and sample CSV | yes - example | Verify files exist |
| 1.2 multi-source-project directory exists with README and 3 sample CSVs | yes - example | Verify files exist |
| 1.3 production-deployment directory exists with README | yes - example | Verify file exists |
| 1.4 Index lists all three projects | yes - example | Check README content |
| 1.5 Index includes comparison matrix | yes - example | Check README content |
| 2.1 Clone script lists examples | yes - example | Run script, verify output |
| 2.2 Clone offers merge or new directory | yes - example | Run script, verify prompts |
| 2.3 Clone skips README on merge | yes - example | Clone into existing dir, verify README preserved |
| 2.4 Clone errors on existing directory | yes - example | Attempt clone to existing dir |
