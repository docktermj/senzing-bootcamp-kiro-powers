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
│   └── backups/                   # Database backups (created by user)
├── database/                      # SQLite database files
│   ├── G2C.db                     # Main Senzing database (SQLite)
│   └── .gitkeep                   # Keep directory in git
├── src/                           # Generated program source
│   ├── quickstart_demo/           # Module 0 demo code (optional)
│   ├── transform/                 # Transformation programs (Module 3)
│   ├── load/                      # Loading programs (Module 5)
│   ├── query/                     # Query programs (Module 6)
│   └── utils/                     # Shared utilities
├── tests/                         # Test files for project
├── docs/                          # Design documents
│   ├── business_problem.md        # Module 1 output
│   ├── data_source_evaluation.md  # Module 2 output
│   ├── mapping_specifications.md  # Module 3 mappings
│   ├── query_specifications.md    # Module 6 queries
│   └── lessons_learned.md         # Post-project retrospective
├── config/                        # Configuration files
├── docker/                        # Docker files (if using containers)
│   ├── Dockerfile                 # Container definition
│   ├── docker-compose.yml         # Multi-container setup
│   └── scripts/                   # Docker-specific scripts
├── logs/                          # Log files
├── monitoring/                    # Monitoring and dashboards
├── requirements.txt               # Python dependencies for your project
└── README.md                      # Project description
```

## Important Notes

**Source Code Location**: All generated source code (transformation programs, loading programs, query programs, utilities, and scripts) should be placed in the `src/` directory structure, not in the project root. Docker files should be placed in the `docker/` directory, never in the project root.

**Backups Directory**: The `data/backups/` directory is created by users in their project for storing database backups. This is NOT part of the power distribution itself.

**Python Dependencies**: Users should create a `requirements.txt` file in their project root to manage Python dependencies. See `examples/` for reference implementations.

**SQLite Database Location**: All SQLite databases MUST be placed in `database/G2C.db` (project-relative path). Never use `/tmp/sqlite` or system-wide locations. This allows multiple bootcamp instances to run concurrently on the same machine. See `docs/policies/SQLITE_DATABASE_LOCATION.md` for complete policy.

## Agent Behavior

**🚨 MANDATORY - EXECUTE FIRST 🚨**:

- Before ANY other action, check if project structure exists
- If structure doesn't exist, create it immediately using commands below
- Do not greet user, do not ask questions, do not present options until structure is created
- This happens BEFORE everything else - no exceptions

**Commands to execute**:

```bash
mkdir -p data/{raw,transformed,samples,backups}
mkdir -p database
mkdir -p src/{transform,load,query,utils}
mkdir -p tests
mkdir -p docs/feedback
mkdir -p config
mkdir -p docker/scripts
mkdir -p logs
mkdir -p monitoring
mkdir -p scripts
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
