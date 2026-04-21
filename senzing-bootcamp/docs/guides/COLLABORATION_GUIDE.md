# Senzing Bootcamp - Collaboration Guide

For teams working on a Senzing Bootcamp project together. For coding standards, see `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Team Roles

| Role | Modules | Responsibilities |
|------|---------|-----------------|
| Project Lead | 2 | Business problem, requirements, stakeholder coordination |
| Data Engineer | 3-5 | Data collection, quality, mapping, transformation |
| Integration Dev | 0, 6-8 | SDK setup, loading, queries, API integration |
| QA/Testing | 4, 8-9 | Data quality, UAT, performance testing |
| DevOps | 10-12 | Security, monitoring, deployment |

## Git Workflow

**Branch naming:** `feature/module-X-description`, `fix/issue-description`, `docs/topic`

**Commit format:** `<type>: <subject>` — types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**.gitignore must exclude:** `database/*.db`, `data/raw/*`, `data/transformed/*`, `backups/*.zip`, `.env`, `licenses/*.lic`

**Branch strategy:** Feature branches off `main`. PR for review before merge. Never commit directly to `main`.

## Code Review Checklist

- [ ] Code follows language-appropriate standards (see `docs/policies/CODE_QUALITY_STANDARDS.md`)
- [ ] Tests pass
- [ ] No PII in code or comments
- [ ] No hardcoded credentials
- [ ] Documentation updated
- [ ] File paths follow `docs/policies/FILE_STORAGE_POLICY.md`

## Sharing Data

**Commit to git:** Small samples (<1MB), anonymized test data, synthetic data

**Don't commit:** Large files (>1MB), real customer data, PII. Use Git LFS, cloud storage, or shared drives instead. Document locations in `docs/data_source_locations.md`.

## Onboarding New Team Members

1. Grant repo access and communication channels
2. Run `python scripts/check_prerequisites.py`
3. Complete Module 1 (Quick Demo) to see entity resolution in action
4. Review `docs/business_problem.md` and existing code in `src/`
5. Pair with a team member on their first task


## Bootcamp-Specific Collaboration

### Splitting Data Mapping Work (Module 5)

When multiple team members are mapping different data sources:

1. Each person takes one data source (e.g., Alice maps CRM, Bob maps billing)
2. Use separate branches: `feature/map-crm`, `feature/map-billing`
3. Each person creates their transformation program in `src/transform/transform_[source].[ext]`
4. Merge branches after both mappings are validated with `analyze_record`
5. Document mappings in separate files: `docs/mapping_crm.md`, `docs/mapping_billing.md`

### Splitting Query Work (Module 8)

When multiple team members are building different query programs:

1. Divide by query type: one person builds duplicate detection, another builds search
2. Use separate branches: `feature/query-duplicates`, `feature/query-search`
3. Each person creates their program in `src/query/[query_type].[ext]`
4. Share UAT test cases in `docs/uat_test_cases.md` — each person adds their test cases
5. Review each other's query results before merging

### Code Review Checkpoints

Review code at these key points:

- After Module 5: Review transformation logic before loading data
- After Module 6: Review loading programs before multi-source orchestration
- After Module 8: Review query programs and UAT results before production
- After Module 12: Review deployment configuration before going live
