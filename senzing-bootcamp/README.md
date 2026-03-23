# Senzing Boot Camp

A comprehensive, guided learning experience for Senzing entity resolution. This Kiro Power takes you from initial demo through production deployment with 13 focused modules.

## 🚀 Quick Links

- **[Quick Start Guide](docs/guides/QUICK_START.md)** - Three fast paths: 10 min, 30 min, or 2 hours
- **[Onboarding Checklist](docs/guides/ONBOARDING_CHECKLIST.md)** - Complete this before starting
- **[Progress Tracker](docs/guides/PROGRESS_TRACKER.md)** - Track your module completion
- **[Example Projects](examples/)** - Three complete reference projects
- **[Code Templates](templates/)** - Ready-to-use transformation and loading templates

## What is Senzing?

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

## What You'll Learn

This boot camp teaches you how to:
- Map your data to Senzing format
- Install and configure the Senzing SDK
- Load data from multiple sources
- Query and validate entity resolution results
- Test performance and optimize for scale
- Harden security for production
- Set up monitoring and observability
- Package and deploy to production

## 13-Module Learning Path

| Module | Name | Time | Status |
|--------|------|------|--------|
| 0 | Quick Demo (Optional) | 10-15 min | Optional |
| 1 | Business Problem + Cost Calculator | 20-30 min | Required |
| 2 | Data Collection + Lineage | 10-15 min/source | Required |
| 3 | Data Quality Scoring | 15-20 min/source | Required |
| 4 | Data Mapping + Lineage | 1-2 hrs/source | Required |
| 5 | SDK Setup | 30 min - 1 hr | Required |
| 6 | Single Source Loading | 30 min/source | Required |
| 7 | Multi-Source Orchestration | 1-2 hrs | If multiple sources |
| 8 | Query + UAT Validation | 1-2 hrs | Required |
| 9 | Performance Testing | 1-2 hrs | For production |
| 10 | Security Hardening | 1-2 hrs | For production |
| 11 | Monitoring & Observability | 1-2 hrs | For production |
| 12 | Package & Deploy | 2-3 hrs | For production |

**Total Time**: 10-18 hours for a complete production-ready project

## Quick Start

### Prerequisites
- Kiro IDE installed
- Python 3.8+ (or Java 11+, .NET 6+, Rust)
- Basic understanding of your data sources

### Getting Started

1. **Activate the Power** in Kiro
   ```
   Open Kiro → Powers → Install "Senzing Boot Camp"
   ```

2. **Start with Module 0** (Optional Demo)
   ```
   Ask Kiro: "Let's start the Senzing boot camp with Module 0"
   ```

3. **Or Jump to Module 1** (Your Own Data)
   ```
   Ask Kiro: "Let's start the Senzing boot camp with Module 1"
   ```

4. **Follow the Guided Workflow**
   - Kiro will guide you through each module
   - Complete modules in order (or skip ahead if prerequisites met)
   - Save all generated code in the `src/` directory

## Documentation Structure

```
senzing-bootcamp/
├── POWER.md                    # Main power definition (START HERE)
├── README.md                   # This file
├── mcp.json                    # MCP server configuration
├── docs/
│   ├── README.md               # Documentation index
│   ├── modules/                # Module-specific documentation (14 files)
│   ├── policies/               # Coding standards and conventions (6 files)
│   ├── guides/                 # User guides and tutorials (8 files)
│   └── feedback/               # Feedback template
├── steering/                   # Agent workflows and guidance (16 files)
├── hooks/                      # Automation hooks (4 files)
├── examples/                   # Complete reference projects (3 examples)
├── templates/                  # Code templates (12 templates)
└── scripts/                    # Utility scripts
```

## Key Features

### Core Capabilities

- 🎯 **Interactive Data Mapping** - 8-step guided workflow via MCP server
- 🔧 **SDK Code Generation** - Python, Java, C#, Rust support via MCP server
- 📚 **Documentation Search** - Live Senzing documentation via MCP server
- 🐛 **Error Diagnosis** - 456+ error codes explained via MCP server
- 💡 **Code Examples** - 27 GitHub repositories indexed via MCP server
- 🎲 **Sample Data** - CORD datasets for learning via MCP server
- 🎣 **Kiro Hooks** - 4 automation hooks for quality and validation
- 📋 **Code Templates** - 12 ready-to-use templates for common tasks
- 📊 **13 Focused Modules** - From quick demo to production deployment
- 🎯 **Design Patterns** - 10 common entity resolution use cases
- 📈 **Progress Tracking** - Module completion and onboarding checklists

## Skip Ahead Options

Experienced users can skip modules:
- **Have SGES-compliant data?** → Skip Module 4
- **Senzing already installed?** → Skip Module 5
- **Single data source only?** → Skip Module 7
- **Not deploying to production?** → Skip Modules 9-12

See [POWER.md](POWER.md) for complete skip-ahead guide.

## Common Use Cases

| Use Case | Modules Needed | Time |
|----------|----------------|------|
| **Quick Evaluation** | 0, 1, 2, 4, 5, 6, 8 | 4-6 hours |
| **Single Source PoC** | 1, 2, 3, 4, 5, 6, 8 | 6-8 hours |
| **Multi-Source PoC** | 1-8 | 8-12 hours |
| **Production Deployment** | 1-12 (all) | 10-18 hours |

## Design Patterns

Choose from common entity resolution patterns:
- **Customer 360** - Unified customer view
- **Fraud Detection** - Identify fraud rings
- **Data Migration** - Merge legacy systems
- **Compliance Screening** - Watchlist matching
- **Marketing Dedup** - Eliminate duplicates
- **Patient Matching** - Unified medical records
- **Vendor MDM** - Clean vendor master
- **Claims Fraud** - Detect staged accidents
- **KYC/Onboarding** - Verify identity
- **Supply Chain** - Unified supplier view

See [docs/guides/DESIGN_PATTERNS.md](docs/guides/DESIGN_PATTERNS.md) for details.

## Project Structure

The boot camp helps you create this structure:

```
my-senzing-project/
├── data/
│   ├── raw/                    # Original source data
│   ├── transformed/            # Senzing JSON output
│   └── backups/                # Database backups
├── src/
│   ├── transform/              # Transformation programs
│   ├── load/                   # Loading programs
│   ├── query/                  # Query programs
│   └── utils/                  # Utilities
├── scripts/                    # Shell scripts
├── config/                     # Configuration files
├── docs/                       # Documentation
├── tests/                      # Test files
└── README.md                   # Project description
```

## Policies and Standards

The boot camp follows these conventions:

- **Python code** → `src/` directory (created dynamically)
- **Shell scripts** → `scripts/` directory
- **Documentation** → `docs/` directory
- **Data files** → `data/` directory (created dynamically)

See [docs/policies/](docs/policies/) for complete policies.

## Getting Help

### Within Kiro
- Ask Kiro: "How do I [task]?"
- Ask Kiro: "I'm stuck on Module X"
- Ask Kiro: "Explain error code SENZ0005"

### Documentation

- **Main Guide**: [POWER.md](POWER.md)
- **Module Docs**: [docs/modules/](docs/modules/)
- **User Guides**: [docs/guides/](docs/guides/)
- **Policies**: [docs/policies/](docs/policies/)
- **Steering Files**: [steering/](steering/)

### Senzing MCP Server

The boot camp leverages the Senzing MCP Server for:

- Live Senzing documentation (always current)
- SDK code generation and scaffolding
- Data mapping workflow guidance
- Sample data access (CORD datasets)
- Error code explanations
- Working code examples from GitHub

Ask Kiro to use any MCP server tool for up-to-date information.

### Senzing Resources
- [Senzing Documentation](https://docs.senzing.com)
- [Senzing GitHub](https://github.com/senzing)
- [Senzing Support](https://senzing.com/support)

## What You'll Have After Completion

✅ Clear business problem statement with cost estimates  
✅ Collected data sources with lineage tracking  
✅ Data quality scores and metrics  
✅ Transformation programs for each source  
✅ Installed and configured Senzing SDK  
✅ Single and multi-source loading orchestration  
✅ Query programs with UAT validation  
✅ Performance benchmarks and optimization  
✅ Security-hardened configuration  
✅ Monitoring and observability setup  
✅ Production-ready deployment package  

## Version

**Current Version**: 1.0.0  
**Senzing Compatibility**: V4.0  
**Last Updated**: March 23, 2026

## What's New

### v1.0.0 (March 2026) - Initial Release

**Complete Learning Path:**
- 13 focused modules from quick demo to production deployment
- Automated data quality scoring
- Multi-source orchestration
- Performance testing and optimization
- Security hardening
- Monitoring and observability
- UAT framework
- Cost calculator
- Data lineage tracking

**Senzing MCP Server Integration:**
- Live, always-current Senzing documentation
- SDK code generation and scaffolding
- Interactive data mapping workflow (8 steps)
- Sample data access (CORD datasets)
- Error code explanations (456+ codes)
- Working code examples (27 GitHub repositories)

**Kiro Features:**
- 4 automation hooks for quality and validation
- 12 ready-to-use code templates
- 16 steering files for guided workflows
- 8 user guides
- 14 module documentation files
- 3 complete example projects

**Streamlined Distribution:**
- 50% smaller than initial development version
- Focused exclusively on boot camp-specific content
- MCP server provides all Senzing documentation
- No static content that can become outdated

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is a Senzing-maintained Kiro Power. For issues or suggestions, contact Senzing support.

---

**Ready to start?** Open Kiro and say: *"Let's start the Senzing boot camp"*
