# Design Document

## Overview

The data-lineage-and-uat feature consists of two manual-inclusion steering files distributed within the senzing-bootcamp power. No application code is included — both are markdown files with YAML frontmatter (`inclusion: manual`) placed in `senzing-bootcamp/steering/`. They are loaded by the Agent on demand during specific bootcamp modules to provide structured guidance.

## Architecture

### File Layout

```text
senzing-bootcamp/
└── steering/
    ├── data-lineage.md       # Lineage tracking guidance (inclusion: manual)
    └── uat-framework.md      # UAT process and templates (inclusion: manual)
```

### Data Lineage Steering Structure

Sections and their purpose:

| Section | Content |
|---------|---------|
| Lineage File | Four-section YAML structure (sources, transformations, loading, usage) with module timing |
| Example Entry | Realistic YAML showing sources and transformations with field values |
| Lineage Tracker | Utility API spec: track_source, track_transformation, track_loading, track_usage, get_lineage_for_source, generate_lineage_report |
| Integration | Guidance on adding tracker calls to transformation and loading scripts |
| Compliance | GDPR/CCPA guidance using get_lineage_for_source for full data flow tracing |
| Agent Behavior | When to create and update the lineage file across modules |

### UAT Framework Steering Structure

Sections and their purpose:

| Section | Content |
|---------|---------|
| Process | Five-phase table: planning, test cases, execution, issues, sign-off |
| Test Case Format | YAML schema with id, scenario, test_data, expected_result, acceptance_criteria, priority, tester |
| Key Scenarios | Coverage matrix: duplicate detection, data quality, performance, business rules |
| UAT Executor | Program spec that loads cases, runs queries, compares results, generates report |
| Sign-off Template | Structure for uat_signoff.md with counts, issues, checklist, signatures |
| Agent Behavior | Six-step workflow from criteria extraction through sign-off generation |

### Artifacts Produced During Bootcamp

When these steering files are loaded, they guide creation of:

| Artifact | Created During | Location |
|----------|---------------|----------|
| Data lineage file | Module 3 | `docs/data_lineage.yaml` |
| Lineage tracker utility | Module 3 | `src/utils/lineage_tracker.[ext]` |
| UAT test cases | Module 8 | `docs/uat_test_cases.yaml` |
| UAT executor | Module 8 | `src/query/uat_executor.[ext]` |
| UAT results | Module 8 | `docs/uat_results.md` |
| UAT issues log | Module 8 | `docs/uat_issues.yaml` |
| UAT sign-off | Module 8 | `docs/uat_signoff.md` |

## Constraints

- Both files are static markdown with `inclusion: manual` frontmatter — no application code in the power itself.
- The Lineage Tracker utility has no Senzing SDK dependency; it only reads/writes YAML.
- File placement follows the repository organization policy (`steering/` for agent-loaded files).
