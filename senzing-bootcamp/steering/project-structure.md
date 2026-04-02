---
inclusion: manual
---

# Project Directory Structure

The Senzing Boot Camp agent will create this organized directory structure for you at the start of Module 1:

```text
my-senzing-project/
├── .git/                          # Version control (optional, but recommended)
├── .gitignore                     # Exclude sensitive data
├── .env.example                   # Template for environment variables
├── .env                           # Actual environment variables (not in git)
├── data/                          # User's data files
│   ├── raw/                       # Original source data
│   ├── transformed/               # Senzing-formatted JSON output
│   ├── samples/                   # Sample data for testing
│   ├── backups/                   # Database backups (created by user)
│   └── temp/                      # Temporary working files (gitignored)
├── database/                      # SQLite database files
│   ├── G2C.db                     # Main Senzing database (SQLite)
│   └── .gitkeep                   # Keep directory in git
├── licenses/                      # Senzing license files
│   ├── g2.lic                     # Senzing license (if provided)
│   └── README.md                  # License instructions
├── src/                           # Generated program source
│   ├── quickstart_demo/           # Module 1 demo code (optional)
│   ├── transform/                 # Transformation programs (Module 5)
│   ├── load/                      # Loading programs (Module 6)
│   ├── query/                     # Query programs (Module 8)
│   └── utils/                     # Shared utilities
├── scripts/                       # Shell scripts
├── tests/                         # Test files for project
├── backups/                       # Project backup archives
├── docs/                          # Design documents
│   ├── business_problem.md        # Module 2 output
│   ├── data_source_evaluation.md  # Module 4 output
│   ├── mapping_specifications.md  # Module 5 mappings
│   ├── query_specifications.md    # Module 8 queries
│   └── lessons_learned.md         # Post-project retrospective
├── config/                        # Configuration files
│   ├── bootcamp_preferences.yaml  # Language choice, path selection (auto-generated)
│   └── bootcamp_progress.json     # Module completion tracking (auto-generated)
├── logs/                          # Log files
├── monitoring/                    # Monitoring and dashboards
├── <dependency file>               # Language-specific (requirements.txt, pom.xml, etc.)
└── README.md                      # Project description
```

## Important Notes

**Source Code Location**: All generated source code (transformation programs, loading programs, query programs, utilities, and scripts) should be placed in the `src/` directory structure, not in the project root.

**Backups Directory**: The `data/backups/` directory is created by users in their project for storing database backups. This is NOT part of the power distribution itself.

**Dependencies**: Users should create a dependency file appropriate for their chosen language in the project root:
- Python: `requirements.txt`
- Java: `pom.xml` or `build.gradle`
- C#: `.csproj` file
- Rust: `Cargo.toml`
- TypeScript: `package.json`

See `examples/` for reference implementations.

**SQLite Database Location**: All SQLite databases MUST be placed in `database/G2C.db` (project-relative path). Never use `/tmp/sqlite` or system-wide locations. This allows multiple bootcamp instances to run concurrently on the same machine. See `docs/policies/FILE_STORAGE_POLICY.md` for the complete policy.

## Agent Behavior

**🚨 MANDATORY - EXECUTE FIRST 🚨**:

- Before ANY other action, check if project structure exists
- If structure doesn't exist, create it immediately using commands below
- Do not greet user, do not ask questions, do not present options until structure is created
- This happens BEFORE everything else - no exceptions

**Commands to execute** (cross-platform):

```python
import os
for d in [
    "data/raw", "data/transformed", "data/samples", "data/backups", "data/temp",
    "database", "licenses",
    "src/transform", "src/load", "src/query", "src/utils",
    "tests", "backups", "docs/feedback", "config", "logs", "monitoring", "scripts",
]:
    os.makedirs(d, exist_ok=True)
```

Or using shell commands:

On Linux / macOS:
```bash
mkdir -p data/{raw,transformed,samples,backups,temp} database licenses \
  src/{transform,load,query,utils} tests backups docs/feedback config logs monitoring scripts
```

On Windows (PowerShell):
```powershell
foreach ($d in @(
  "data\raw","data\transformed","data\samples","data\backups","data\temp",
  "database","licenses",
  "src\transform","src\load","src\query","src\utils",
  "tests","backups","docs\feedback","config","logs","monitoring","scripts"
)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
```

And create initial files: `.gitignore`, `.env.example`, `README.md`

**After creation**:

- Inform user that structure has been created
- As you generate programs throughout the boot camp, save them in the appropriate folders

## Trigger Points for Directory Creation

Create structure at ANY of these:

- User says "start the boot camp"
- User mentions any module number (0-12)
- User selects any path (A, B, C, D)
- User asks to begin
- ANY indication they want to use the power

## Why Directory-First Approach?

This ensures all generated files go to the correct locations throughout the boot camp. Without this structure in place first, files might be scattered or placed incorrectly.
