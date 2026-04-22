# Design Document

## Overview

The design-and-planning feature consists of three manual-inclusion steering files and one user-facing guide. No application code is involved — all artifacts are markdown files. The steering files are loaded by the Agent at specific workflow points (Module 2, post-Module 2, Module 8→9 gate). The cloud provider setup also writes a YAML preference file.

## Architecture

### File Layout

```text
senzing-bootcamp/
├── docs/
│   └── guides/
│       └── DESIGN_PATTERNS.md              # User-facing pattern summary
└── steering/
    ├── design-patterns.md                  # 10 ER patterns for Module 2 (inclusion: manual)
    ├── complexity-estimator.md             # Time estimation scoring (inclusion: manual)
    └── cloud-provider-setup.md             # Cloud selection at 8→9 gate (inclusion: manual)
```

### Design Patterns Steering

- 10-row pattern table with columns: Pattern, Use Case, Key Matching, Typical ROI
- 3-question decision flow (entity type → primary goal → frequency) to narrow selection
- Agent behavior instructions for presenting patterns and guiding Module 2 problem definition
- Architecture guidance on Senzing-first vs search-index ordering

### Design Patterns Guide

- Summary table of all 10 patterns (Pattern, Use Case, Key Matching)
- Directs users to the steering file for full details and agent-guided selection

### Complexity Estimator

- 6-dimension scoring matrix (format, volume, quality, mapping, structure, access) at 1–3 points each
- Score-to-complexity mapping: 6–9 Low, 10–14 Medium, 15–18 High
- Time estimates for Module 5 (Mapping) and Module 6 (Loading) per complexity tier
- Risk factors table with additional time adjustments
- Optimization tips for high-complexity sources

### Cloud Provider Setup

- Prompt script for the Module 8→9 validation gate
- Provider-specific guidance: AWS (CDK, RDS, Secrets Manager, CloudWatch, ECS/EKS), Azure, GCP, on-premises, local
- Persists choice to `config/bootcamp_preferences.yaml` as `cloud_provider` key (merge, not overwrite)
- AWS path recommends CDK and the CDK Kiro Power

## Constraints

- All steering files use `inclusion: manual` frontmatter — loaded only when needed.
- Cloud provider choice is persisted via YAML merge to avoid overwriting other preferences.
- File placement follows the repository organization policy.
