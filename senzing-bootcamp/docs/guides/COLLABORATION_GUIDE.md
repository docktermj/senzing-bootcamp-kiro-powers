# Senzing Bootcamp - Collaboration Guide

For teams working on a Senzing Bootcamp project together. For coding standards, see `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Team Roles

| Role | Modules | Responsibilities |
|------|---------|-----------------|
| Project Lead | 1 | Business problem, requirements, stakeholder coordination |
| Data Engineer | 4-6 | Data collection, quality, mapping, transformation |
| Integration Dev | 2, 7-9 | SDK setup, loading, queries, API integration |
| QA/Testing | 5, 9-10 | Data quality, UAT, performance testing |
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
2. Run `python scripts/preflight.py`
3. Complete Module 3 (Quick Demo) to see entity resolution in action
4. Review `docs/business_problem.md` and existing code in `src/`
5. Pair with a team member on their first task

## Team Mode

Team mode enables multi-user bootcamp sessions with shared configuration, per-member progress tracking, a team dashboard, and consolidated feedback reports. It activates automatically when `config/team.yaml` exists.

### Setting Up Team Config

Create `config/team.yaml` in your project root. A sample template is available at `senzing-bootcamp/templates/team.yaml.example`.

**Co-located mode** (all members share one repo):

```yaml
team_name: "Acme ER Team"
mode: colocated
shared_data_sources:
  - customers
  - vendors
members:
  - id: alice
    name: "Alice Johnson"
  - id: bob
    name: "Bob Smith"
```

**Distributed mode** (each member has their own repo clone):

```yaml
team_name: "Acme ER Team"
mode: distributed
shared_data_sources:
  - customers
members:
  - id: alice
    name: "Alice Johnson"
    repo_path: /home/alice/senzing-bootcamp
  - id: bob
    name: "Bob Smith"
    repo_path: /home/bob/senzing-bootcamp
```

Key rules:

- `team_name` is required and must be non-empty.
- `members` must have at least two entries, each with a unique `id` and a `name`.
- `mode` must be `colocated` or `distributed`.
- In distributed mode, every member must have a `repo_path`.

### Co-located vs. Distributed Mode

| Aspect | Co-located | Distributed |
|--------|-----------|-------------|
| Repository | Single shared repo | Each member has their own clone |
| Progress files | `config/progress_{member_id}.json` | `{repo_path}/config/bootcamp_progress.json` |
| Feedback files | `docs/feedback/..._FEEDBACK_{member_id}.md` | `{repo_path}/docs/feedback/..._FEEDBACK.md` |
| Preferences | `config/preferences_{member_id}.yaml` | `{repo_path}/config/preferences.yaml` |
| Journal | `docs/bootcamp_journal_{member_id}.md` | `{repo_path}/docs/bootcamp_journal.md` |
| Best for | Teams in the same office or on the same machine | Remote teams or teams wanting isolation |

**Co-located mode** keeps all member files in one repo with member-ID suffixes to avoid conflicts. This is the simplest setup — everyone commits to the same repo.

**Distributed mode** lets each member work in their own repo clone. The team lead maintains the `config/team.yaml` in a coordinator repo and runs team scripts from there. Each member's repo uses standard single-user file paths.

### Onboarding Experience in Team Mode

When a bootcamper starts the bootcamp and `config/team.yaml` exists:

1. The agent detects the team config and validates it.
2. The agent presents the member list and asks: "Which team member are you?"
3. The bootcamper selects their member ID.
4. The agent creates their member-specific progress file.
5. The welcome banner displays the team name and member count.
6. The rest of onboarding proceeds as normal (language selection, prerequisites, track selection).

If `config/team.yaml` does not exist, onboarding proceeds in standard single-user mode with no team-related prompts.

### Team Dashboard

Generate an HTML dashboard showing all members' progress:

```bash
python senzing-bootcamp/scripts/team_dashboard.py
python senzing-bootcamp/scripts/team_dashboard.py --output reports/dashboard.html
```

The dashboard includes:

- Team summary (name, member count, average completion)
- Per-member progress table (current module, completion %, language)
- Module heatmap (green = completed, yellow = in progress, gray = not started)
- ER comparison view (for members who completed Module 6+)
- Navigation bar linking to each section

Output defaults to `exports/team_dashboard.html`. The HTML is self-contained with inline CSS — open it in any browser.

### Merging Feedback

Consolidate all members' feedback into a single team report:

```bash
python senzing-bootcamp/scripts/merge_feedback.py
python senzing-bootcamp/scripts/merge_feedback.py --output reports/feedback.md
```

The report includes:

- Summary with total entries, priority breakdown, and category breakdown
- Feedback grouped by member
- Members with no feedback noted as "No feedback submitted"

Output defaults to `docs/feedback/TEAM_FEEDBACK_REPORT.md`.

### Team Progress with status.py

The existing `status.py` script is team-aware:

```bash
python senzing-bootcamp/scripts/status.py              # Team summary (when team.yaml exists)
python senzing-bootcamp/scripts/status.py --member alice  # Individual member progress
```

Without `--member`, it shows each member's current module and completion count plus overall team statistics.

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
