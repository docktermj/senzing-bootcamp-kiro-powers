---
inclusion: manual
---

# Graduation Reference Material

Reference tables, templates, and conditional logic used by the graduation workflow. Loaded on demand via `#[[file:]]` from `graduation.md`.

## File Copy Table

Copy these files into `production/`, preserving subdirectory structure:

| Source | Destination | Notes |
|--------|-------------|-------|
| `src/transform/**` | `production/src/transform/` | All transform code |
| `src/load/**` | `production/src/load/` | All loading code |
| `src/query/**` | `production/src/query/` | All query code |
| `src/utils/**` | `production/src/utils/` | Utility modules |
| `data/transformed/**` | `production/data/` | Transformed data files |
| `database/` (structure only) | `production/database/.gitkeep` | Empty placeholder — do not copy the actual database file |
| `requirements.txt` / `pom.xml` / `Cargo.toml` / `package.json` / `*.csproj` | `production/` | Whichever dependency file exists for the chosen language |

If a source directory does not exist, skip it silently — not all tracks produce all directories. If a file copy fails, log the failure, skip that file, and continue.

## Exclusion Table

Do NOT copy any of the following into `production/`:

| Path | Reason |
|------|--------|
| `config/bootcamp_progress.json` | Bootcamp tracking state |
| `config/bootcamp_preferences.yaml` | Bootcamp preferences |
| `docs/bootcamp_journal.md` | Learning journal |
| `data/samples/` | Sample datasets for demos |
| `data/raw/` | Unprocessed source data |
| `src/quickstart_demo/` | Module 3 demo code |
| `logs/` | Bootcamp session logs |
| `backups/` | Bootcamp backup snapshots |
| `monitoring/` | Bootcamp monitoring setup |
| `docs/feedback/` | Bootcamp feedback files |

## Configuration File Templates

### `.env.production`

Generate with placeholder values only — no real secrets:

```bash
# Production Environment Configuration
# Replace all placeholder values before deploying

SENZING_ENGINE_CONFIGURATION_JSON=<your-senzing-engine-config>
SENZING_LICENSE_PATH=<path-to-production-license>
DATABASE_URL=<production-database-connection-string>
LOG_LEVEL=WARN
API_KEY=<your-api-key>
```

Adjust variables based on database type (SQLite vs PostgreSQL connection string format).

### `.env.example`

Mirror `.env.production` with safe example values and comments:

```bash
# Example Environment Configuration
# Copy this to .env.production and replace with real values

# Senzing engine configuration (JSON string or path to JSON file)
SENZING_ENGINE_CONFIGURATION_JSON={"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing","SUPPORTPATH":"/opt/senzing/data","RESOURCEPATH":"/opt/senzing/er/resources"},"SQL":{"CONNECTION":"sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db"}}

# Path to your Senzing production license file
SENZING_LICENSE_PATH=/etc/opt/senzing/g2.lic

# Database connection string
DATABASE_URL=sqlite:///database/G2C.db

# Log level: DEBUG, INFO, WARN, ERROR
LOG_LEVEL=INFO

# API key for external integrations (if applicable)
API_KEY=example-key-replace-me
```

### `docker-compose.yml`

Generate parameterized by database type from preferences:

- **SQLite**: Single application service with volume mount for the database file
- **PostgreSQL**: Application service + PostgreSQL service with health check, persistent volume, and environment variables

Include Senzing license volume mount in both variants.

### CI/CD Pipeline

Ask the bootcamper which CI/CD platform they use (GitHub Actions default, Azure DevOps, or GitLab CI). WAIT for response.

| Choice | File | Location |
|--------|------|----------|
| GitHub Actions | `ci.yml` | `production/.github/workflows/ci.yml` |
| Azure DevOps | `azure-pipelines.yml` | `production/azure-pipelines.yml` |
| GitLab CI | `.gitlab-ci.yml` | `production/.gitlab-ci.yml` |

The pipeline must include four stages:

1. **Lint** — language-appropriate linter
2. **Test** — run unit tests
3. **Build** — build container image
4. **Deploy** — placeholder deployment stage with manual gate

### `.gitignore`

Generate a language-appropriate `.gitignore` in `production/`. Always include:

```gitignore
.env.production
*.db
*.sqlite
__pycache__/
node_modules/
target/
bin/
obj/
build/
dist/
.idea/
.vscode/
*.log
```

Add language-specific entries based on the bootcamper's chosen language.

## Migration Checklist Conditional Logic

Generate `production/MIGRATION_CHECKLIST.md` with six sections (Database, Security, Licensing, Performance, Data, Deployment) using `- [ ]` checkboxes.

### Base checklist items

**Database:**

- Replace evaluation database with production database instance
- Configure connection pooling for production workloads
- Set up automated database backups
- Test database failover and recovery procedures
- Update DATABASE_URL in .env.production with production connection string

**Security:**

- Replace all placeholder secrets in .env.production with real values
- Configure TLS/SSL for all network connections
- Review and configure access controls (API keys, authentication)
- Audit source code for hardcoded credentials and remove them
- Set up secret rotation policy

**Licensing:**

- Obtain a production Senzing license (evaluation license supports 500 records)
- Configure SENZING_LICENSE_PATH in .env.production
- Verify license capacity matches expected production data volume

**Performance:**

- Tune database parameters for production data volumes
- Configure multi-threaded record loading
- Set up performance monitoring and alerting
- Run load tests with production-scale data samples

**Data:**

- Validate all production data sources and ingestion pipelines
- Configure error handling for bad/malformed records
- Set up data quality monitoring for incoming records
- Document data source schemas and update frequencies

**Deployment:**

- Configure CI/CD pipeline with real credentials and deployment targets
- Set up staging environment for pre-production testing
- Set up production environment
- Define and document rollback procedure
- Configure health checks and readiness probes

### Conditional items (check `modules_completed` from pre-checks)

**If Modules 10, 11, and 12 are all completed (Path D):**

- **Security**: Add `- [ ] Review and update security hardening from Module 10 (check src/ for security artifacts)`
- **Performance**: Add `- [ ] Review performance benchmarks from Module 9 and validate against production targets`
- **Deployment**: Add `- [ ] Review deployment packaging from Module 11 (check deployment artifacts)`
- Add note at top: "✅ You completed the full production track (Modules 10–12). Items below reference artifacts you already produced."

**If Modules 10–12 are NOT all completed:**

- **Security**: Add `- [ ] ⚠️ Security hardening was not covered during the bootcamp — review these items carefully`
- **Performance** (if Module 9 not completed): Add `- [ ] ⚠️ Performance testing was not covered — benchmark before going to production`
- **Deployment**: Add `- [ ] ⚠️ Deployment packaging was not covered during the bootcamp — complete these items before deploying`
- Add note at top: "⚠️ Some production topics (security, monitoring, deployment) were not covered in your track. Items marked with ⚠️ need extra attention."

## Graduation Report Template

**Always generate this file**, regardless of whether individual steps encountered errors.

Generate `production/GRADUATION_REPORT.md` with this structure:

```markdown
# Graduation Report

Generated: [ISO 8601 timestamp]

## Summary

- **Track completed:** [Path letter and name, e.g., "Path C — Complete Beginner"]
- **Modules finished:** [list of module numbers and names]
- **Language:** [chosen language]
- **Database type:** [SQLite or PostgreSQL]

## Files Generated

| File | Description |
|------|-------------|
| `src/transform/` | Data transformation code |
| `src/load/` | Record loading code |
| `src/query/` | Entity query code |
| `src/utils/` | Utility modules |
| `data/` | Transformed data files |
| `database/.gitkeep` | Database directory placeholder |
| `.env.production` | Production environment variables (placeholders) |
| `.env.example` | Example environment configuration |
| `docker-compose.yml` | Container orchestration |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `.gitignore` | Version control exclusions |
| `README.md` | Production documentation |
| `MIGRATION_CHECKLIST.md` | Production transition checklist |
| `GRADUATION_REPORT.md` | This file |
| `[dependency file]` | Language dependency file |

Adjust the table to reflect what was actually generated (e.g., the CI/CD file name depends on the chosen platform).

## Files Excluded

| File/Directory | Reason |
|----------------|--------|
| `config/bootcamp_progress.json` | Bootcamp tracking state — not needed in production |
| `config/bootcamp_preferences.yaml` | Bootcamp preferences — not needed in production |
| `docs/bootcamp_journal.md` | Learning journal — personal bootcamp artifact |
| `data/samples/` | Sample datasets used for demos only |
| `data/raw/` | Unprocessed source data — production uses transformed data |
| `src/quickstart_demo/` | Module 3 demo code — not production code |
| `logs/` | Bootcamp session logs |
| `backups/` | Bootcamp backup snapshots |
| `monitoring/` | Bootcamp monitoring setup |
| `docs/feedback/` | Bootcamp feedback files |

## Next Steps

1. **Fill in production secrets** — Replace all placeholders in `.env.production` with real values (see `.env.example` for guidance)
2. **Obtain a production license** — The evaluation license supports 500 records; contact sales@senzing.com for production licensing
3. **Work through the migration checklist** — Open `MIGRATION_CHECKLIST.md` and address each item
4. **Set up your CI/CD pipeline** — Configure the generated pipeline file with your deployment credentials
5. **Test with production data** — Validate your entity resolution results with real data before going live
```

### Failure reporting

If any step encountered errors during the workflow, add a "⚠️ Issues Encountered" section after "Next Steps":

```markdown
## ⚠️ Issues Encountered

- [Step N]: [description of what failed and what was skipped]
```
