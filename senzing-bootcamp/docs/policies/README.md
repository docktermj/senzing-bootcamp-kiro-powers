# Policies and Standards Index

This directory contains policy documents that define coding standards and organizational conventions for the Senzing Boot Camp.

## Available Policies

### File Storage Policy

**File**: [FILE_STORAGE_POLICY.md](FILE_STORAGE_POLICY.md)

**Purpose**: Comprehensive guide for where all file types should be stored (never use /tmp)

**Covers**:

- Source code → `src/` (including Module 1 demo code in `src/quickstart_demo/`)
- Shell scripts → `scripts/`
- Data files → `data/`
- Database files → `database/G2C.db` (project-relative, never `/tmp/sqlite`)
- Configuration → `config/`
- Documentation → `docs/`
- License files → `licenses/`
- Backups → `backups/`
- Temporary files → `data/temp/`

**Why It Matters**: Consistent project organization, concurrent bootcamp support, no `/tmp` conflicts

**Applies To**: All modules

---

### Dependency Management Policy

**File**: [DEPENDENCY_MANAGEMENT_POLICY.md](DEPENDENCY_MANAGEMENT_POLICY.md)

**Purpose**: Define how project dependencies should be managed across all supported languages

**Key Rules**:

- Use the appropriate dependency file for your language (e.g., `requirements.txt`, `pom.xml`, `Cargo.toml`, `package.json`)
- Pin versions for production
- Use ranges for development
- Document why each dependency is needed
- Keep dependencies minimal

**Why It Matters**: Ensures reproducible builds and clear dependency management

**Applies To**: All projects (Modules 5, 0, 6, 7, 8, 9, 10, 11, 12)

---

### Senzing Information Policy

**File**: [SENZING_INFORMATION_POLICY.md](SENZING_INFORMATION_POLICY.md)

**Purpose**: Ensure all Senzing facts come from the MCP server, never from training data

**Key Rules**:

- **Never state Senzing facts from training data**
- Always use MCP tools (`search_docs`, `mapping_workflow`, `get_sdk_reference`, etc.) for Senzing-specific information
- Covers attribute names, SDK methods, JSON formats, error codes, configuration, and all other Senzing specifics
- Say "Let me look that up" and call the appropriate MCP tool

**Why It Matters**: Training data may be outdated or inaccurate; the MCP server provides authoritative, version-correct information

**Applies To**: All modules (0–12)

---

### Code Quality Standards

**File**: [CODE_QUALITY_STANDARDS.md](CODE_QUALITY_STANDARDS.md)

**Purpose**: Define language-appropriate coding standards for all generated code

**Key Rules**:

- Python → PEP-8, Java → standard conventions, C# → .NET conventions, Rust → rustfmt/clippy, TypeScript → ESLint
- Proper naming conventions, documentation, and import organization per language
- Avoid `exportJSONEntityReport()` unless data set is explicitly small and bounded

**Why It Matters**: Consistent, readable code across all modules regardless of chosen language

**Applies To**: All modules that generate code

---

## Policy Summary

| Policy              | Directory              | File Types          | Applies To             |
|---------------------|------------------------|---------------------|------------------------|
| File Storage        | Various                | All files           | All modules            |
| Code Quality        | N/A (standards)        | Source code         | All code modules       |
| Dependencies        | Project root           | Language-specific   | All projects           |
| Senzing Information | N/A (agent behavior)   | All                 | All modules (0–12)     |

## File Organization Overview

```text
project-root/
├── database/                 # SQLite database files (REQUIRED LOCATION)
│   ├── G2C.db                # Main Senzing database
│   └── .gitkeep              # Keep directory in git
├── src/                      # All source code
│   ├── quickstart_demo/      # Module 1 demo code
│   ├── transform/            # Transformation programs
│   ├── load/                 # Loading programs
│   ├── query/                # Query programs
│   └── utils/                # Utility modules
├── scripts/                  # Automation scripts (Python)
│   ├── backup_project.py
│   ├── status.py
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
│   └── feedback/             # User feedback
├── config/                   # Configuration files
├── requirements.txt / pom.xml / etc.  # Language-specific dependencies
└── ...
```

**Important**:

- SQLite databases MUST go in `database/G2C.db` (never `/tmp`)
- Never use `/tmp` for any project files
- Use appropriate project directories for all files

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
- **Workflows**: per-module steering files in `../../steering/`

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

- **v2.0.0** (2026-04-01): Consolidated micro-policies into FILE_STORAGE_POLICY.md
  - Removed SQLITE_DATABASE_LOCATION.md, MODULE_1_CODE_LOCATION.md, SHELL_SCRIPT_LOCATIONS.md
  - Their rules are now in FILE_STORAGE_POLICY.md
- **v1.2.0** (2026-03-26): Added SQLite database location policy
- **v1.1.0** (2026-03-17): Added file storage policy
- **v1.0.0** (2026-03-17): Initial policies created

## Navigation

- [← Back to docs/](../)
- [→ Modules](../modules/)
- [→ Guides](../guides/)
