# Senzing Bootcamp - Collaboration Guide

## Overview

This guide helps teams collaborate effectively on Senzing Bootcamp projects using git, code reviews, and shared workflows.

## Team Roles

### Project Lead

- Defines business problem and requirements
- Manages project timeline and milestones
- Reviews and approves major changes
- Coordinates with stakeholders

### Data Engineer

- Collects and evaluates data sources
- Creates transformation programs
- Optimizes data quality
- Manages data lineage

### Integration Developer

- Sets up Senzing SDK
- Creates loading programs
- Develops query programs
- Handles API integrations

### QA/Testing

- Validates data quality
- Performs UAT testing
- Tests performance
- Documents test results

### DevOps Engineer

- Sets up CI/CD pipelines
- Manages deployments
- Configures monitoring
- Handles infrastructure

## Git Workflow

### Initial Setup

```bash
# Initialize git repository
git init

# Create .gitignore (agent does this automatically)
# Verify it excludes:
# - database/*.db
# - data/raw/*
# - data/transformed/*
# - backups/*.zip
# - .env
# - licenses/*.lic

# Create main branch
git checkout -b main

# Initial commit
git add .
git commit -m "Initial Senzing Bootcamp project structure"

# Add remote (GitHub, GitLab, Bitbucket)
git remote add origin <repository-url>
git push -u origin main
```

### Branch Strategy

Use feature branches for development:

```bash
# Create feature branch
git checkout -b feature/module-4-customer-mapping

# Work on your changes
# ... make changes ...

# Commit changes
git add src/transform/transform_customers.[ext]
git commit -m "Add customer data transformation for Module 4"

# Push to remote
git push origin feature/module-4-customer-mapping

# Create pull request for review
```

### Branch Naming Convention

- `feature/module-X-description` - New module work
- `fix/issue-description` - Bug fixes
- `refactor/component-name` - Code refactoring
- `docs/topic` - Documentation updates
- `test/test-description` - Test additions

### Commit Message Guidelines

```text
<type>: <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, PEP-8
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:

```text
feat: Add customer transformation for Module 4

- Map customer fields to Senzing attributes
- Handle missing data gracefully
- Add data quality validation

Closes #123
```

## Code Review Process

### Before Submitting PR

1. **Run checks:**

   ```bash
   # Run tests (use appropriate command for your language)
   python -m pytest tests/

   # Check for PII in data files
   # Review data/raw/ and data/transformed/ for sensitive information
   ```

2. **Update documentation:**

   - Update README if needed
   - Document new functions/classes
   - Update progress tracker

3. **Test locally:**

   - Run transformation programs
   - Verify output format
   - Check data quality

### Creating Pull Request

1. **Title:** Clear, descriptive summary
2. **Description:** What, why, and how
3. **Checklist:**
   - [ ] Code follows PEP-8
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No PII in code/comments
   - [ ] Reviewed own changes

### Reviewing Pull Requests

**What to check:**

- Code quality and coding standards compliance
- Logic correctness
- Error handling
- Performance considerations
- Security issues
- Documentation completeness

**Review comments:**

- Be constructive and specific
- Suggest improvements
- Ask questions for clarity
- Approve when satisfied

## Shared Workflows

### Module Assignment

Track who's working on what:

```markdown
# Module Assignments

- Module 2 (Business Problem): @project-lead
- Module 3 (Data Collection): @data-engineer
- Module 4 (Data Quality): @data-engineer
- Module 5 (Mapping): @data-engineer
- Module 0 (SDK Setup): @integration-dev
- Module 6 (Loading): @integration-dev
- Module 7 (Orchestration): @integration-dev
- Module 8 (Queries): @integration-dev, @qa-tester
- Module 9 (Performance): @qa-tester, @devops
- Module 10 (Security): @devops
- Module 11 (Monitoring): @devops
- Module 12 (Deployment): @devops
```

### Daily Standup

Share progress daily:

- What did you complete yesterday?
- What are you working on today?
- Any blockers?

### Weekly Review

Review progress weekly:

- Modules completed
- Issues encountered
- Lessons learned
- Next week's goals

## Sharing Data

### Sample Data

**DO share** (commit to git):

- Small sample files (<1MB)
- Anonymized test data
- Synthetic data

**DON'T share** (add to .gitignore):

- Large data files (>1MB)
- Real customer data
- PII data

### Data Sharing Options

**For large files:**

1. **Git LFS** (recommended for teams using git): Track large files without bloating the repo.

   ```bash
   git lfs install
   git lfs track "data/raw/*.csv"
   git lfs track "data/raw/*.json"
   git add .gitattributes
   ```

2. **Cloud storage** (S3, Google Drive, Dropbox): Upload large files and share links. Document the location in `docs/data_source_locations.md`.
3. **Shared network drive**: Mount a shared volume and reference files by path.
4. **Data transfer service**: For very large datasets (>10GB), use a dedicated transfer tool.

**Document data location:**

```markdown
# Data Sources

## Customer Data
- Location: s3://company-bucket/customers.csv
- Size: 500MB
- Last Updated: 2026-03-26
- Owner: @data-engineer

## Transaction Data
- Location: /shared/data/transactions.csv
- Size: 2GB
- Last Updated: 2026-03-25
- Owner: @data-engineer
```

## Configuration Management

### Environment Variables

Each team member has their own `.env`:

```bash
# .env (not in git)
SENZING_LICENSE_PATH=licenses/g2.lic
DATABASE_URL=sqlite:///database/G2C.db
LOG_LEVEL=INFO
```

Share template:

```bash
# .env.example (in git)
SENZING_LICENSE_PATH=licenses/g2.lic
DATABASE_URL=sqlite:///database/G2C.db
LOG_LEVEL=INFO
```

### Shared Configuration

Configuration that's the same for everyone:

```json
// config/senzing_config.json (in git)
{
  "pipeline": {
    "batch_size": 1000,
    "num_threads": 4
  },
  "data_sources": [
    {
      "name": "CUSTOMERS",
      "file": "data/transformed/customers.jsonl"
    }
  ]
}
```

## Communication

### Channels

Set up communication channels:

- **General:** Project updates, announcements
- **Technical:** Code discussions, architecture
- **Data:** Data quality, mapping questions
- **Deployment:** Release planning, production issues

### Documentation

Keep team documentation updated:

- `docs/TEAM.md` - Team members and roles
- `docs/DECISIONS.md` - Architecture decisions
- `docs/RUNBOOK.md` - Operational procedures
- `docs/TROUBLESHOOTING.md` - Common issues

## Conflict Resolution

### Merge Conflicts

When conflicts occur:

1. **Pull latest changes:**

   ```bash
   git pull origin main
   ```

2. **Resolve conflicts:**

   - Open conflicted files
   - Choose correct version or merge manually
   - Test changes

3. **Commit resolution:**

   ```bash
   git add <resolved-files>
   git commit -m "Resolve merge conflict in transformation code"
   ```

### Code Conflicts

When team members disagree:

1. Discuss pros/cons
2. Consider alternatives
3. Test both approaches if needed
4. Document decision
5. Project lead makes final call

## Best Practices

### Do's

✅ Commit frequently with clear messages
✅ Pull before starting new work
✅ Create feature branches
✅ Request code reviews
✅ Document your changes
✅ Communicate blockers early
✅ Share knowledge with team
✅ Follow coding standards
✅ Write tests
✅ Keep branches up to date

### Don'ts

❌ Commit directly to main
❌ Commit large binary files
❌ Commit sensitive data
❌ Force push to shared branches
❌ Leave branches stale
❌ Skip code reviews
❌ Ignore test failures
❌ Work in isolation
❌ Assume others know your changes
❌ Commit broken code

## Tools

### Recommended Tools

**Version Control:**

- Git
- GitHub/GitLab/Bitbucket

**Communication:**

- Slack/Teams/Discord
- Email for formal communication

**Project Management:**

- Jira/Trello/Asana
- GitHub Issues/Projects

**Code Review:**

- GitHub Pull Requests
- GitLab Merge Requests
- Bitbucket Pull Requests

**Documentation:**

- Markdown files in repo
- Wiki (GitHub/GitLab)
- Confluence

## Onboarding New Team Members

### Checklist

- [ ] Grant repository access
- [ ] Add to communication channels
- [ ] Share data access credentials
- [ ] Provide Senzing license
- [ ] Review project documentation
- [ ] Run through Module 1 (Quick Demo)
- [ ] Assign first task
- [ ] Schedule pairing session

### First Week

**Day 1:**

- Repository setup
- Run `python scripts/check_prerequisites.py`
- Complete Module 0

**Day 2-3:**

- Review existing code
- Understand data sources
- Read documentation

**Day 4-5:**

- Pair with team member
- Complete small task
- Submit first PR

## Troubleshooting

### "My changes aren't showing up"

```bash
# Pull latest changes
git pull origin main

# Check current branch
git branch

# Switch to correct branch
git checkout <branch-name>
```

### "I can't push my changes"

```bash
# Pull and rebase
git pull --rebase origin main

# Resolve conflicts if any
# Then push
git push origin <branch-name>
```

### "Someone else is working on the same file"

1. Communicate with team member
2. Coordinate changes
3. One person waits for other to finish
4. Or split work into different functions/sections

## Resources

- **Git Documentation:** <https://git-scm.com/doc>
- **GitHub Guides:** <https://guides.github.com/>
- **Atlassian Git Tutorials:** <https://www.atlassian.com/git/tutorials>
- **Pro Git Book:** <https://git-scm.com/book/en/v2>

## Questions?

- Ask in team communication channel
- Review git documentation
- Consult with project lead
- Pair with experienced team member

---

**Last Updated:** 2026-03-26
**Version:** 1.0.0
