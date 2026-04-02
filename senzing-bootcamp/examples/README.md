# Senzing Boot Camp Examples

This directory contains reference project blueprints demonstrating different use cases and deployment patterns.

**Note:** These examples are architectural blueprints, not runnable code. Each contains a README describing the project structure, code patterns, and expected results. The actual source code is generated during the boot camp by the agent using MCP tools (`generate_scaffold`, `mapping_workflow`) in your chosen programming language. Use these blueprints as reference architectures when building your own project.

## Available Examples

### 1. Simple Single Source

**Path**: `simple-single-source/`
**Use case**: Basic customer deduplication with one data source
**Complexity**: Beginner
**Time to complete**: 2-3 hours
**Modules covered**: 2-6, 8

A minimal example showing:

- Single CSV data source (customers)
- Basic data mapping
- SQLite database
- Simple query programs
- Complete documentation

**Best for**: First-time users, learning the basics, proof of concept

---

### 2. Multi-Source Project

**Path**: `multi-source-project/`
**Use case**: Customer 360 with three data sources
**Complexity**: Intermediate
**Time to complete**: 6-8 hours
**Modules covered**: 2-8

A realistic example showing:

- Three data sources (CRM, e-commerce, support)
- Data quality evaluation
- Complex mappings
- PostgreSQL database
- Multi-source orchestration
- UAT framework

**Best for**: Real-world projects, multiple data sources, production preparation

---

### 3. Production Deployment

**Path**: `production-deployment/`
**Use case**: Production-ready vendor MDM system
**Complexity**: Advanced
**Time to complete**: 12-15 hours
**Modules covered**: All (0-12)

A complete production example showing:

- Two data sources (vendor master, procurement)
- Full data quality pipeline
- PostgreSQL with replication
- Performance testing and optimization
- Security hardening
- Monitoring and observability
- Containerized deployment
- CI/CD pipeline
- API gateway integration

**Best for**: Production deployments, enterprise use cases, complete reference

---

## Using the Examples

### Option 1: Study the Example

Browse the example directory to see:

- Project structure
- Code organization
- Documentation style
- Best practices

### Option 2: Copy and Adapt

Copy an example into your project directory. You can use your file manager, or from a terminal:

```bash
# Linux / macOS
cp -r senzing-bootcamp/examples/simple-single-source/* my-project/
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse senzing-bootcamp\examples\simple-single-source\* my-project\
```

Then adapt to your data: update data sources, modify mappings, adjust configurations.

### Option 3: Follow Along

Use the example as a guide while building your own project:

1. Compare your structure to the example
2. Reference code patterns
3. Check documentation format
4. Verify you haven't missed steps

## Example Structure

Each example includes:

```text
example-name/
├── README.md                      # Example overview and instructions
├── data/
│   ├── raw/                       # Sample source data
│   ├── transformed/               # Transformed data
│   └── samples/                   # Small test samples
├── src/
│   ├── transform/                 # Transformation programs
│   ├── load/                      # Loading programs
│   ├── query/                     # Query programs
│   └── utils/                     # Utilities
├── tests/                         # Test files
├── docs/
│   ├── business_problem.md        # Problem statement
│   ├── data_quality_report.md     # Quality analysis
│   ├── mapping_*.md               # Mapping docs
│   └── lessons_learned.md         # Retrospective
├── config/                        # Configuration files
├── scripts/                       # Automation scripts
├── .env.example                   # Environment template
└── deploy.yml                     # Deployment config (if applicable)
```

## Comparison Matrix

| Feature       | Simple  | Multi-Source | Production           |
|---------------|---------|--------------|----------------------|
| Data sources  | 1       | 3            | 2                    |
| Database      | SQLite  | PostgreSQL   | PostgreSQL + replica |
| Records       | 10K     | 500K         | 5M                   |
| Modules       | 2-6, 8  | 2-8          | 0-12                 |
| Testing       | Basic   | UAT          | Full test suite      |
| Monitoring    | None    | Basic        | Full observability   |
| Security      | Basic   | Medium       | Hardened             |
| Deployment    | Local   | Scripted     | Production           |
| CI/CD         | No      | No           | Yes                  |
| API           | No      | No           | Yes                  |
| Documentation | Minimal | Complete     | Comprehensive        |
| Time          | 2-3 hrs | 6-8 hrs      | 12-15 hrs            |

## Learning Path

### Beginner Path

1. Start with **Simple Single Source**
2. Complete Modules 2-6 and 8
3. Understand the basics
4. Build confidence

### Intermediate Path

1. Review **Simple Single Source** quickly
2. Work through **Multi-Source Project**
3. Complete Modules 1-8
4. Handle realistic complexity

### Advanced Path

1. Skim **Simple** and **Multi-Source**
2. Focus on **Production Deployment**
3. Complete all Modules 0-12
4. Build production-ready system

## Quick Start

### Run Simple Example

```bash
# Navigate to example
cd senzing-bootcamp/examples/simple-single-source

# Install dependencies (use the appropriate command for your language)
# Python: pip install -r requirements.txt
# Java: mvn install
# C#: dotnet restore
# Rust: cargo build
# TypeScript: npm install

# Run transformation
# Use the appropriate command for your chosen language

# Load data
# Use the appropriate command for your chosen language

# Query results
# Use the appropriate command for your chosen language
```

### Run Multi-Source Example

```bash
# Navigate to example
cd senzing-bootcamp/examples/multi-source-project

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run orchestration
# Use the appropriate command for your chosen language

# Run queries
# Use the appropriate command for your chosen language
```

### Run Production Example

```bash
# Navigate to example
cd senzing-bootcamp/examples/production-deployment

# Run full pipeline (cross-platform)
python scripts/run_pipeline.py
```

## Customization Tips

### Adapting Data Sources

1. Replace sample data with your data
2. Update field mappings in transformation programs
3. Adjust data source names in configuration
4. Re-run quality evaluation

### Changing Database

1. Update connection string in `.env`
2. Modify engine configuration
3. Re-register data sources
4. Test connection

### Scaling Up

1. Increase batch sizes in loading programs
2. Add parallel processing
3. Optimize database configuration
4. Add monitoring

### Adding Features

1. Add new data sources (follow Module 3-5)
2. Add new queries (follow Module 8)
3. Add API endpoints (follow Module 12)
4. Add monitoring (follow Module 11)

## Common Questions

**Q: Can I use these examples in production?**
A: The production example is production-ready. Simple and multi-source examples are for learning and need hardening for production use.

**Q: Do I need to complete all modules to use an example?**
A: No. Each example is complete and runnable. Use them as reference or starting points.

**Q: Can I mix and match from different examples?**
A: Yes! Take the orchestration from multi-source, security from production, etc.

**Q: Are the sample data files real?**
A: They're realistic synthetic data for demonstration purposes.

**Q: How do I contribute my own example?**
A: Create a PR with your example following the structure above.

## Support

- Review example README files for specific instructions
- Ask the agent for help understanding any example
- Use `search_docs` for Senzing-specific questions
- Check `docs/guides/` for additional guidance

## Dependency Management

The boot camp supports multiple programming languages. Dependency files are language-specific:

- Python: `requirements.txt`
- Java: `pom.xml` or `build.gradle`
- C#: `*.csproj`
- Rust: `Cargo.toml`
- TypeScript: `package.json`

See `docs/policies/DEPENDENCY_MANAGEMENT_POLICY.md` for the full policy.

## Version History

- **v3.0.0** (2026-03-17): Examples directory created with three reference projects
- **v3.1.0** (2026-03-26): Added requirements.txt reference files for user projects
- **v4.0.0** (2026-04-01): Made language-agnostic; removed Python-specific dependency files
