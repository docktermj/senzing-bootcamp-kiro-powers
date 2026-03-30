# Senzing Boot Camp - Guides Directory

## Overview

This directory contains comprehensive guides to help you succeed with the Senzing Boot Camp.

## Available Guides

### Getting Started

**[QUICK_START.md](QUICK_START.md)**

- Three fast paths (10 min, 30 min, 2 hours)
- Choose your learning path
- Get started quickly

**[ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)**

- Pre-bootcamp checklist
- Environment setup
- Prerequisites verification

### Reference Documentation

**[FAQ.md](FAQ.md)** ⭐ NEW!

- 100+ frequently asked questions
- Organized by category
- Quick answers to common questions
- Covers all modules

**[GLOSSARY.md](GLOSSARY.md)** ⭐ NEW!

- A-Z terminology
- Senzing-specific terms
- Common attributes
- MCP tools reference
- Acronyms

**[DESIGN_PATTERNS.md](DESIGN_PATTERNS.md)**

- 10 common entity resolution patterns
- Use cases and examples
- When to use each pattern

### Progress and Tracking

**[PROGRESS_TRACKER.md](PROGRESS_TRACKER.md)**

- Track module completion
- Monitor overall progress
- Document milestones

**Status Command** ⭐ NEW!

```bash
./scripts/status.sh
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

**[TROUBLESHOOTING_INDEX.md](TROUBLESHOOTING_INDEX.md)**

- Common issues and solutions
- Error code explanations
- Debugging strategies

### Installation and Setup

**[HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md)**

- How to install hooks
- Available hooks
- Hook configuration

**Hook Installer** ⭐ NEW!

```bash
./scripts/install_hooks.sh
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
4. Review [GLOSSARY.md](GLOSSARY.md) for terminology

### Need Help?

1. Check [FAQ.md](FAQ.md) first
2. Review [TROUBLESHOOTING_INDEX.md](TROUBLESHOOTING_INDEX.md)
3. Look up terms in [GLOSSARY.md](GLOSSARY.md)
4. Ask the agent for guidance

### Working with a Team?

1. Read [COLLABORATION_GUIDE.md](COLLABORATION_GUIDE.md)
2. Set up git workflows
3. Define team roles
4. Establish code review process

### Track Progress

1. Use [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md) manually
2. Or run `./scripts/status.sh` for automated status

### Visual Learner?

1. Review [module-flow.md](../diagrams/module-flow.md)
2. Study [data-flow.md](../diagrams/data-flow.md)
3. Follow the ASCII diagrams

## Useful Scripts

### Check Prerequisites

```bash
./scripts/check_prerequisites.sh
```

Validates your environment before starting.

### Check Status

```bash
./scripts/status.sh
```

Shows current module, progress, and next steps.

### Install Hooks

```bash
./scripts/install_hooks.sh
```

Interactive hook installation.

### Clone Example

```bash
./scripts/clone_example.sh
```

Clone example projects to your workspace.

### Backup Project

```bash
./scripts/backup_project.sh
```

Or say: "backup my project"

### Restore Project

```bash
./scripts/restore_project.sh <backup-file>
```

## Documentation Structure

```text
docs/
├── guides/                    # This directory
│   ├── README.md             # This file
│   ├── QUICK_START.md        # Getting started
│   ├── ONBOARDING_CHECKLIST.md
│   ├── FAQ.md                # ⭐ NEW! 100+ Q&A
│   ├── GLOSSARY.md           # ⭐ NEW! A-Z terms
│   ├── COLLABORATION_GUIDE.md # ⭐ NEW! Team workflows
│   ├── DESIGN_PATTERNS.md
│   ├── PROGRESS_TRACKER.md
│   ├── TROUBLESHOOTING_INDEX.md
│   └── HOOKS_INSTALLATION_GUIDE.md
├── diagrams/                  # ⭐ NEW! Visual docs
│   ├── module-flow.md        # Module diagrams
│   └── data-flow.md          # Data pipeline diagrams
├── modules/                   # Module documentation
│   ├── MODULE_0_SDK_SETUP.md
│   ├── MODULE_1_QUICK_DEMO.md
│   ├── MODULE_2_BUSINESS_PROBLEM.md
│   └── ... (Modules 2-12)
├── policies/                  # Policy documents
│   ├── FILE_STORAGE_POLICY.md
│   ├── PEP8_COMPLIANCE.md
│   └── ... (other policies)
└── feedback/                  # Feedback templates
    └── SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md
```

## What's New (2026-03-26)

### New Guides

- ✅ **FAQ.md**: 100+ questions and answers
- ✅ **GLOSSARY.md**: Complete A-Z terminology
- ✅ **COLLABORATION_GUIDE.md**: Team workflows

### New Scripts

- ✅ **status.sh**: Automated progress checking
- ✅ **check_prerequisites.sh**: Environment validation
- ✅ **install_hooks.sh**: Interactive hook installation
- ✅ **clone_example.sh**: Example project cloning

### New Diagrams

- ✅ **module-flow.md**: Visual module flow
- ✅ **data-flow.md**: Data pipeline visualization

### Enhanced Features

- ✅ Automated status checking
- ✅ One-command prerequisite validation
- ✅ Easy hook installation
- ✅ Example cloning
- ✅ Visual learning aids

## Getting Help

### Self-Service

1. **FAQ**: Check [FAQ.md](FAQ.md) for quick answers
2. **Glossary**: Look up terms in [GLOSSARY.md](GLOSSARY.md)
3. **Troubleshooting**: Review [TROUBLESHOOTING_INDEX.md](TROUBLESHOOTING_INDEX.md)
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
- **Examples**: `senzing-bootcamp/examples/`
- **Templates**: `senzing-bootcamp/templates/`
- **Hooks**: `senzing-bootcamp/hooks/`

## Quick Links

- [Boot Camp Overview](../../POWER.md)
- [Module 1: Quick Demo](../modules/MODULE_1_QUICK_DEMO.md)
- [Module 2: Business Problem](../modules/MODULE_2_BUSINESS_PROBLEM.md)
- [File Storage Policy](../policies/FILE_STORAGE_POLICY.md)
- [PEP-8 Compliance](../policies/PEP8_COMPLIANCE.md)

---

**Last Updated**: 2026-03-26
**Version**: 2.0.0 (Major update with FAQ, Glossary, Collaboration Guide, and Scripts)
