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
├── docs/
│   ├── README.md               # Documentation index
│   ├── modules/                # Module-specific documentation
│   ├── policies/               # Coding standards and conventions
│   ├── guides/                 # User guides and tutorials
│   └── development/            # Development progress tracking
├── steering/                   # Agent workflows and guidance
└── hooks/                      # Automation hooks
```

## Key Features

### New in v3.0.0
- ✨ **Automated Data Quality Scoring** - Get quality metrics before mapping
- ✨ **Multi-Source Orchestration** - Manage dependencies between data sources
- ✨ **Performance Testing** - Benchmark and optimize for production
- ✨ **Security Hardening** - Production-grade security measures
- ✨ **Monitoring & Observability** - Full monitoring stack setup
- ✨ **UAT Framework** - Structured user acceptance testing
- ✨ **Cost Calculator** - Estimate costs based on data volume
- ✨ **Data Lineage Tracking** - Track data transformations
- ✨ **Incremental Loading** - Efficient update patterns

### Core Capabilities
- 🎯 **Interactive Data Mapping** - 7-step guided workflow
- 🔧 **SDK Code Generation** - Python, Java, C#, Rust support
- 📚 **Documentation Search** - Indexed Senzing documentation
- 🐛 **Error Diagnosis** - 456 error codes explained
- 💡 **Code Examples** - 27 GitHub repositories indexed
- 🎲 **Sample Data** - CORD datasets for learning

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
- **Python code** → `src/` directory
- **Shell scripts** → `scripts/` directory
- **Module 0 demos** → `src/quickstart_demo/` directory
- **Documentation** → `docs/` directory

See [docs/policies/](docs/policies/) for complete policies.

## Getting Help

### Within Kiro
- Ask Kiro: "How do I [task]?"
- Ask Kiro: "I'm stuck on Module X"
- Ask Kiro: "Explain error code SENZ0005"

### Documentation
- **Main Guide**: [POWER.md](POWER.md)
- **Module Docs**: [docs/modules/](docs/modules/)
- **Steering Files**: [steering/](steering/)
- **Troubleshooting**: [docs/guides/](docs/guides/)

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

**Current Version**: 3.0.0  
**Senzing Compatibility**: V4.0  
**Last Updated**: March 17, 2026

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is a Senzing-maintained Kiro Power. For issues or suggestions, contact Senzing support.

---

**Ready to start?** Open Kiro and say: *"Let's start the Senzing boot camp"*
