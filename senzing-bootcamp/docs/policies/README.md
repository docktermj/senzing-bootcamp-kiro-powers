# Policies and Standards Index

This directory contains policy documents that define coding standards and organizational conventions for the Senzing Boot Camp.

## Available Policies

### Module 0 Code Location Policy
**File**: [MODULE_0_CODE_LOCATION.md](MODULE_0_CODE_LOCATION.md)

**Purpose**: Define where Module 0 demo code should be stored

**Key Rules**:
- All Module 0 demo code goes in `src/quickstart_demo/`
- Demo scripts: `src/quickstart_demo/demo_[dataset_name].py`
- Sample data: `src/quickstart_demo/sample_data_[dataset_name].jsonl`
- Keep demo code separate from main project code

**Why It Matters**: Prevents confusion between demo code and production code

**Applies To**: Module 0 (Quick Demo)

---

### Python Requirements Policy
**File**: [PYTHON_REQUIREMENTS_POLICY.md](PYTHON_REQUIREMENTS_POLICY.md)

**Purpose**: Define how Python dependencies should be managed

**Key Rules**:
- Use `requirements.txt` for production dependencies
- Use `requirements-dev.txt` for development dependencies
- Pin versions for production (`package==1.2.3`)
- Use ranges for development (`package>=1.2.0`)
- Document why each dependency is needed
- Keep dependencies minimal

**Why It Matters**: Ensures reproducible builds and clear dependency management

**Applies To**: All Python projects (Modules 4, 5, 6, 7, 8, 9, 10, 11, 12)

---

### Shell Script Locations Policy
**File**: [SHELL_SCRIPT_LOCATIONS.md](SHELL_SCRIPT_LOCATIONS.md)

**Purpose**: Define where shell scripts should be stored

**Key Rules**:
- **All shell scripts (*.sh) go in `scripts/` directory**
- Python/Java/C# code goes in `src/` directory
- Use descriptive names: `deploy.sh`, not `d.sh`
- Include shebang: `#!/bin/bash`
- Add comments explaining what script does

**Common Scripts**:
- `scripts/deploy.sh` - Deployment automation
- `scripts/backup.sh` - Database backup
- `scripts/migrate_db.sh` - Database migration
- `scripts/run_pipeline.sh` - Pipeline execution
- `scripts/health_check.sh` - Health checks

**Why It Matters**: Consistent project organization and clear separation of concerns

**Applies To**: All modules that generate shell scripts (Modules 10, 11, 12)

---

### File Storage Policy
**File**: [FILE_STORAGE_POLICY.md](FILE_STORAGE_POLICY.md)

**Purpose**: Define where all file types should be stored (never use /tmp)

**Key Rules**:
- **Source code** → `src/` directory
- **Shell scripts** → `scripts/` directory
- **Documentation** → `docs/` directory
- **Data files** → `data/` directory
- **Configuration** → `config/` directory or root (for .env)
- **Never use `/tmp`** for project files

**Why It Matters**: Ensures files persist, are organized, and are easy to find

**Applies To**: All modules and all file types

---

## Policy Summary

| Policy | Directory | File Types | Applies To |
|--------|-----------|------------|------------|
| Module 0 Code | `src/quickstart_demo/` | Python/Java/C#/Rust | Module 0 |
| Python Requirements | Project root | `requirements*.txt` | All Python projects |
| Shell Scripts | `scripts/` | `*.sh` | Modules 10, 11, 12 |
| File Storage | Various | All files | All modules |

## File Organization Overview

```
project-root/
├── src/                      # All source code (Python/Java/C#/Rust)
│   ├── quickstart_demo/      # Module 0 demo code
│   ├── transform/            # Transformation programs
│   ├── load/                 # Loading programs
│   ├── query/                # Query programs
│   └── utils/                # Utility modules
├── scripts/                  # All shell scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── ...
├── data/                     # All data files
│   ├── raw/                  # Original source data
│   ├── transformed/          # Senzing-formatted JSON
│   ├── samples/              # Sample data
│   ├── backups/              # Database backups
│   └── temp/                 # Temporary working files (gitignored)
├── docs/                     # All documentation
│   ├── guides/               # User guides
│   ├── modules/              # Module docs
│   ├── policies/             # Policy docs
│   └── development/          # Internal docs
├── config/                   # Configuration files
├── requirements.txt          # Python production dependencies
├── requirements-dev.txt      # Python development dependencies
└── ...
```

**Important**: Never use `/tmp` for project files. Use appropriate project directories.

## Why These Policies Matter

### Consistency
- Everyone knows where to find files
- Easier onboarding for new team members
- Reduces confusion and errors

### Maintainability
- Clear separation of concerns
- Easy to update and refactor
- Predictable project structure

### Best Practices
- Follows industry standards
- Aligns with language conventions
- Supports CI/CD automation

## Enforcement

These policies are:
- ✅ Documented in policy files
- ✅ Referenced in agent instructions
- ✅ Enforced by agent behavior
- ✅ Included in code reviews
- ✅ Part of boot camp workflows

## Related Documentation

- **Agent Instructions**: `../../steering/agent-instructions.md`
- **Module Documentation**: `../modules/`
- **Workflows**: `../../steering/steering.md`

## For Agents

When generating code:
1. **Always check policies** before creating files
2. **Place files in correct directories** according to policies
3. **Follow naming conventions** defined in policies
4. **Explain policies to users** when relevant
5. **Enforce policies consistently** across all modules

## For Users

When organizing your project:
1. **Follow these policies** for consistency
2. **Ask agent for clarification** if unsure
3. **Document deviations** if you must deviate
4. **Update policies** if you find better approaches

## Version History

- **v1.1.0** (2026-03-17): Added file storage policy
  - FILE_STORAGE_POLICY.md
- **v1.0.0** (2026-03-17): Initial policies created
  - MODULE_0_CODE_LOCATION.md
  - PYTHON_REQUIREMENTS_POLICY.md
  - SHELL_SCRIPT_LOCATIONS.md

## Navigation

- [← Back to docs/](../)
- [→ Modules](../modules/)
- [→ Guides](../guides/)
- [→ Development](../development/)
