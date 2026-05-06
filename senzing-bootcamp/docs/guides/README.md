# Senzing Bootcamp - Guides Directory

## Overview

This directory contains comprehensive guides to help you succeed with the Senzing Bootcamp.

## Available Guides

### Getting Started

**[QUICK_START.md](QUICK_START.md)**

- Three fast paths to get started
- Choose your learning path
- Get started quickly

**[ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)**

- Pre-bootcamp checklist
- Environment setup
- Prerequisites verification

### Reference Documentation

**[FAQ.md](FAQ.md)**

- Frequently asked questions about the bootcamp
- Organized by category
- Covers modules, files, troubleshooting

**[GLOSSARY.md](GLOSSARY.md)**

- Quick-reference glossary of Senzing entity resolution terms
- 18 key terms: entity, data source, record, feature, Senzing Entity Specification (SGES), redo record, and more
- Concise definitions without needing MCP round-trips

**[DESIGN_PATTERNS.md](DESIGN_PATTERNS.md)**

- 10 common entity resolution patterns
- Use cases and examples
- When to use each pattern

**[PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md)**

- Reference throughput for transformation, loading, and querying at different data volumes
- Hardware requirements for small (<1K), medium (1K-100K), and large (100K+) datasets
- SQLite vs PostgreSQL comparison and migration guidance
- Scaling recommendations including multi-threading and database tuning

**[QUALITY_SCORING_METHODOLOGY.md](QUALITY_SCORING_METHODOLOGY.md)**

- How quality scores are calculated (formula and weights)
- What each scoring dimension measures (completeness, consistency, format compliance, uniqueness)
- Threshold bands and recommended actions (≥80% proceed, 70-79% warn, <70% fix)
- Examples of high, medium, and low quality data with sample scores

**[DATA_UPDATES_AND_DELETIONS.md](DATA_UPDATES_AND_DELETIONS.md)**

- Record updates using replace semantics (same DATA_SOURCE + RECORD_ID replaces old data)
- Record deletions and their impact on entity composition
- Entity re-evaluation after updates and deletions (merges, splits, removals)
- Redo processing implications and the recommended check-process-drain pattern

**[INCREMENTAL_LOADING.md](INCREMENTAL_LOADING.md)**

- Incremental loading patterns for adding new records to an existing Senzing database
- Redo processing after incremental loads: scheduling, queue monitoring, and drain verification
- Pipeline health monitoring: throughput, error rates, redo queue depth, and entity count trends

**[MULTI_LANGUAGE_DATA.md](MULTI_LANGUAGE_DATA.md)**

- Non-Latin character support and how Senzing handles names in Chinese, Arabic, Cyrillic, and other scripts
- UTF-8 encoding requirements, common encoding problems, and verification checklist
- Cross-script name matching, transliteration, and multi-language data quality best practices

**[PROGRESS_FILE_SCHEMA.md](PROGRESS_FILE_SCHEMA.md)**

- Field definitions, types, and valid values for `config/bootcamp_progress.json`
- Step history structure, validation rules, and a complete example
- Lists which scripts and steering files read and write the progress file

**[DATA_SOURCE_REGISTRY.md](DATA_SOURCE_REGISTRY.md)**

- Field definitions, types, and valid values for `config/data_sources.yaml`
- Enum values for format, mapping status, load status, and test load status
- Schema migration from version 1 to version 2, plus read/write script references

**[STEERING_INDEX.md](STEERING_INDEX.md)**

- Structure and field definitions for `steering/steering-index.yaml`
- Module entry formats (simple and split), keyword mappings, language and deployment mappings
- File metadata token counts, context budget thresholds, and read/write script references

**[MODULE_ARTIFACTS.md](MODULE_ARTIFACTS.md)**

- Schema documentation for `config/module-artifacts.yaml`
- Field definitions for version, modules, produces, and requires\_from
- Validation rules and a complete example showing Modules 4-7
- CLI usage and agent behavior on missing artifacts

### After the Bootcamp

**[AFTER_BOOTCAMP.md](AFTER_BOOTCAMP.md)**

- What to do after completing the bootcamp
- Production maintenance cadence (daily/weekly/monthly/quarterly)
- Scaling, adding new data sources, staying updated
- Advanced topics and community resources

**[STREAMING_INTEGRATION.md](STREAMING_INTEGRATION.md)** — **Streaming Integration**

- Real-time streaming patterns for consuming records from message queues (Apache Kafka, RabbitMQ, Amazon SQS) and processing them through Senzing entity resolution in real time
- Backpressure handling strategies for when inbound message rates exceed processing capacity, including consumer-side rate limiting, queue-level buffering, and horizontal scaling
- Error management for streaming pipelines: retry with exponential backoff, dead letter queue patterns, and monitoring to detect systemic issues

### Progress and Tracking

**[PROGRESS_TRACKER.md](PROGRESS_TRACKER.md)**

- Track module completion
- Monitor overall progress
- Document milestones

**Status Command** ⭐ NEW!

```text
python3 scripts/status.py
```

- Shows current module
- Progress percentage
- Next steps
- Project health

### Team Collaboration

**[COLLABORATION_GUIDE.md](COLLABORATION_GUIDE.md)** ⭐ NEW!

- Git workflows
- Branch strategies
- Code review process
- Team roles
- Communication guidelines

### Troubleshooting

**[OFFLINE_MODE.md](OFFLINE_MODE.md)** ⭐ NEW!

- What works without MCP, module by module
- Reconnection steps you can try
- How the agent handles outages automatically

**[COMMON_MISTAKES.md](COMMON_MISTAKES.md)** ⭐ NEW!

- Most frequent bootcamp mistakes with real examples
- Data preparation, SDK configuration, loading, query, and production mistakes
- Links to relevant guides for each mistake

**[GETTING_HELP.md](GETTING_HELP.md)** ⭐ NEW!

- Support hierarchy: agent → FAQ → MCP tools → guides → docs.senzing.com → support
- When to use each resource
- Quick reference table of guides by situation

For Senzing error codes, use the MCP `explain_error_code` tool. For Senzing concepts and documentation, use `search_docs`. For bootcamp-specific issues, check `steering/common-pitfalls.md`.

### Installation and Setup

**[HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md)**

- How to install hooks
- Available hooks
- Hook configuration

**Hook Installer** ⭐ NEW!

```text
python3 scripts/install_hooks.py
```

- Interactive installation
- Install all or select hooks
- Prevents duplicates

### Visual Documentation

**[../diagrams/module-flow.md](../diagrams/module-flow.md)** ⭐ NEW!

- Module flow diagrams
- Learning paths
- Dependencies
- Time estimates

**[../diagrams/data-flow.md](../diagrams/data-flow.md)** ⭐ NEW!

- Data transformation pipeline
- Multi-source integration
- Query flow
- Backup flow
- Monitoring flow

## Quick Reference

### New to Senzing?

1. Read [QUICK_START.md](QUICK_START.md)
2. Complete [ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)
3. Check [FAQ.md](FAQ.md) for common questions

### Need Help?

1. Check [FAQ.md](FAQ.md) first
2. Use MCP `search_docs` for Senzing topics
3. Use MCP `explain_error_code` for SENZ errors
4. Ask the agent for guidance

### Working with a Team?

1. Read [COLLABORATION_GUIDE.md](COLLABORATION_GUIDE.md)
2. Set up git workflows
3. Define team roles
4. Establish code review process

### Track Progress

1. Use [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md) manually
2. Or run `python3 scripts/status.py` for automated status

### Visual Learner?

1. Review [module-flow.md](../diagrams/module-flow.md)
2. Study [data-flow.md](../diagrams/data-flow.md)
3. Follow the ASCII diagrams

## Useful Scripts

All scripts are cross-platform Python (Linux, macOS, Windows).

### Check Prerequisites

```text
python3 scripts/check_prerequisites.py
```

Validates your environment before starting.

### Check Status

```text
python3 scripts/status.py
```

Shows current module, progress, and next steps.

### Install Hooks

```text
python3 scripts/install_hooks.py
```

Interactive hook installation.

### Backup Project

```text
python3 scripts/backup_project.py
```

Or say: "backup my project"

### Restore Project

```text
python3 scripts/restore_project.py <backup-file>
```

## Documentation Structure

```text
docs/
├── guides/                    # This directory
│   ├── README.md             # This file
│   ├── QUICK_START.md        # Getting started
│   ├── ONBOARDING_CHECKLIST.md
│   ├── FAQ.md
│   ├── COLLABORATION_GUIDE.md
│   ├── COMMON_MISTAKES.md
│   ├── DATA_SOURCE_REGISTRY.md
│   ├── DATA_UPDATES_AND_DELETIONS.md
│   ├── DESIGN_PATTERNS.md
│   ├── GETTING_HELP.md
│   ├── GLOSSARY.md
│   ├── HOOKS_INSTALLATION_GUIDE.md
│   ├── INCREMENTAL_LOADING.md
│   ├── MULTI_LANGUAGE_DATA.md
│   ├── OFFLINE_MODE.md
│   ├── PERFORMANCE_BASELINES.md
│   ├── PROGRESS_FILE_SCHEMA.md
│   ├── PROGRESS_TRACKER.md
│   ├── AFTER_BOOTCAMP.md
│   ├── QUALITY_SCORING_METHODOLOGY.md
│   ├── STEERING_INDEX.md
│   ├── MODULE_ARTIFACTS.md
│   └── STREAMING_INTEGRATION.md
├── diagrams/                  # ⭐ NEW! Visual docs
│   ├── module-flow.md        # Module diagrams
│   ├── data-flow.md          # Data pipeline diagrams
│   ├── system-architecture.md # SDK, database, and program architecture
│   └── module-prerequisites.md # Module dependency graph
├── modules/                   # Module documentation
│   ├── MODULE_1_BUSINESS_PROBLEM.md
│   ├── MODULE_2_SDK_SETUP.md
│   ├── MODULE_3_QUICK_DEMO.md
│   └── ... (Modules 3-12)
├── policies/                  # Policy documents
│   ├── FILE_STORAGE_POLICY.md
│   ├── CODE_QUALITY_STANDARDS.md
│   └── ... (other policies)
└── feedback/                  # Feedback templates
    └── SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md
```

## Getting Help

### Self-Service

1. **FAQ**: Check [FAQ.md](FAQ.md) for quick answers
2. **MCP Tools**: Use `search_docs` for Senzing topics, `explain_error_code` for errors
3. **Troubleshooting**: Review [../steering/common-pitfalls.md](../../steering/common-pitfalls.md)
4. **Diagrams**: Study visual flows in [diagrams/](../diagrams/)

### Agent Assistance

- Ask the agent any question
- Say "bootcamp help" for guidance
- Say "power feedback" to report issues

### Community

- Senzing community forums
- Senzing support (for licensed users)
- Team collaboration channels

## Contributing

Found an issue or have a suggestion?

1. Say "power feedback" to the agent
2. Document in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
3. Share with the power author

## Related Documentation

- **Power Documentation**: `senzing-bootcamp/POWER.md`
- **Module Documentation**: `docs/modules/`
- **Policy Documentation**: `docs/policies/`
- **Steering Files**: `senzing-bootcamp/steering/`
- **Hooks**: `senzing-bootcamp/hooks/`

## Quick Links

- [Bootcamp Overview](../../POWER.md)
- [Module 1: Business Problem](../modules/MODULE_1_BUSINESS_PROBLEM.md)
- [Module 3: Quick Demo](../modules/MODULE_3_QUICK_DEMO.md)
- [File Storage Policy](../policies/FILE_STORAGE_POLICY.md)
- [Code Quality Standards](../policies/CODE_QUALITY_STANDARDS.md)

---

**Last Updated**: 2026-04-21
**Version**: 2.1.0
