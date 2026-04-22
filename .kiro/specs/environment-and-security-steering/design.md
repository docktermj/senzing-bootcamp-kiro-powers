# Design Document

## Overview

Two steering files in `senzing-bootcamp/steering/` guide agent behavior for environment setup and security/privacy enforcement. Both are pure markdown documents with YAML front-matter controlling inclusion mode. No code execution is involved — they are declarative instructions the agent follows at runtime.

## Architecture

### Steering File Inclusion Modes

| File | Inclusion | When Loaded |
| ---- | --------- | ----------- |
| `environment-setup.md` | `manual` | During onboarding or new project setup (agent or user triggers) |
| `security-privacy.md` | `auto` | Every agent interaction (always active) |

### Environment Setup Coverage

The environment setup steering file covers:

1. **Version control** — `git init`, `.gitignore` with bootcamp-specific entries (sensitive data, data files, database, logs, backups, OS files), `.env.example` template
2. **Environment variables** — Project-local scripts (`scripts/senzing-env.sh` / `.bat`) instead of global shell config, with `SENZING_ROOT`, `SENZING_ENGINE_CONFIG_JSON`, and `SENZING_DATABASE_URL`
3. **Language setup** — Delegates to MCP_Server `sdk_guide(topic='install', language='<chosen_language>')` for current SDK binding commands
4. **Source code layout** — All code in `src/` subdirectories (`transform/`, `load/`, `query/`, `utils/`), scripts in `scripts/`

### Security and Privacy Coverage

The security-privacy steering file covers:

1. **Data handling rules** — Raw data gitignored, anonymized/synthetic data for testing, `.env` for credentials, SQLite DB gitignored, license files gitignored
2. **Code generation rules** — No hardcoded credentials, no PII in logs, sanitize user input
3. **Compliance trigger** — Load Module 10 when GDPR/CCPA/HIPAA/PCI-DSS mentioned, create `docs/security_compliance.md`
4. **Anonymization guidance** — Name replacement, identifier masking (last 4 digits), fake addresses/phones, language-specific faker libraries

### Faker Library Reference

| Language | Library |
| -------- | ------- |
| Python | Faker |
| Java | Faker |
| C# | Bogus |
| Rust | fake-rs |
| TypeScript | @faker-js/faker |

## File Structure

```text
senzing-bootcamp/steering/
├── environment-setup.md    (inclusion: manual)
└── security-privacy.md     (inclusion: auto)
```
