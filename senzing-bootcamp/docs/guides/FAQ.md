# Senzing Boot Camp - Frequently Asked Questions (FAQ)

## General Questions

### What is the Senzing Boot Camp?

The Senzing Boot Camp is a comprehensive, guided learning experience for Senzing entity resolution. It's a structured 13-module curriculum that takes you from understanding your business problem through to production deployment.

### How long does the boot camp take?

It depends on your path:
- **Quick Demo** (Module 0): 10-15 minutes
- **Fast Track** (Modules 5-6): 30 minutes
- **Complete Beginner** (Modules 1-6, 8): 2-3 hours
- **Full Production** (All Modules 0-12): 10-18 hours

### Do I need prior Senzing experience?

No! The boot camp is designed for beginners. Start with Module 0 (Quick Demo) to see entity resolution in action, then work through the modules in order.

### Can I skip modules?

Yes, experienced users can skip modules:
- Have SGES-compliant data? Skip Module 4
- Senzing already installed? Skip Module 5
- Single data source only? Skip Module 7
- Not deploying to production? Skip Modules 9-12

### What's the difference between senzing-bootcamp and senzing powers?

- **senzing-bootcamp**: Structured 13-module learning curriculum with project guidance
- **senzing**: Quick reference documentation and tool catalog

Both connect to the same MCP server. Use bootcamp for learning, senzing for quick reference.

## Getting Started

### How do I start the boot camp?

1. Tell the agent: "start the boot camp" or "start module 0"
2. The agent will automatically create your project structure
3. Follow the guided workflows for each module

### What are the prerequisites?

Required:
- Python 3.7+
- pip
- Git
- curl
- zip/unzip

Optional:
- Docker (for containerized deployment)
- PostgreSQL (for production databases)

Run `./scripts/check_prerequisites.sh` to verify your environment.

### Do I need a Senzing license?

For Module 0 (Quick Demo), no license is needed - it uses an in-memory database.

For Modules 5+ (SDK installation), you'll need a Senzing license. Place it in `licenses/g2.lic`.

### Where should I put my data files?

- Original source data: `data/raw/`
- Transformed data: `data/transformed/`
- Sample data: `data/samples/`
- Database backups: `data/backups/`

See `docs/policies/FILE_STORAGE_POLICY.md` for complete details.

## Working with Modules

### How do I know which module I'm on?

Run `./scripts/status.sh` to see:
- Current module
- Progress percentage
- Completed modules
- Next steps

### Can I go back to a previous module?

Yes! The boot camp is iterative. You can revisit earlier modules as you learn more about your data.

### How do I track my progress?

Use `docs/guides/PROGRESS_TRACKER.md` to manually track completion, or install the module completion hooks to auto-track progress.

### What if I get stuck on a module?

1. Check the module prerequisites
2. Review `docs/guides/TROUBLESHOOTING_INDEX.md`
3. Use the MCP tool `search_docs` for specific topics
4. Ask the agent for help
5. Check `steering/common-pitfalls.md`

## Data and Mapping

### What data formats are supported?

- CSV
- JSON/JSONL
- XML
- Database tables
- API responses

The boot camp helps you transform any format to Senzing JSON.

### Do I need to manually map my data?

No! Use the `mapping_workflow` MCP tool in Module 4. It guides you through an interactive 7-step process to map your data correctly.

### What is SGES?

SGES (Senzing Generic Entity Specification) is the JSON format Senzing uses. The `mapping_workflow` tool ensures your data conforms to SGES.

### How do I validate my mapped data?

Use these MCP tools:
- `lint_record`: Validates format and structure
- `analyze_record`: Provides quality metrics
- `search_docs`: Look up attribute definitions

## SDK and Installation

### Do I need to install Senzing locally?

Not for Module 0 (Quick Demo). For Modules 5+, you have options:
- Local installation (Linux, macOS, Windows)
- Docker container
- Cloud deployment

Module 5 guides you through installation.

### Which database should I use?

- **SQLite**: Good for evaluation and small datasets (<100K records)
- **PostgreSQL**: Recommended for production and large datasets

Start with SQLite, migrate to PostgreSQL when needed.

### Can I use Docker?

Yes! The boot camp supports Docker deployment. See Module 12 for containerization guidance.

## Code and Development

### What programming languages are supported?

The boot camp primarily uses Python, but Senzing SDK supports:
- Python
- Java
- C#
- Rust
- C/C++

Use `generate_scaffold` to create code in your preferred language.

### Do I need to write code?

Minimal coding required! The boot camp uses MCP tools to generate code for you:
- `mapping_workflow`: Generates transformation code
- `generate_scaffold`: Generates loading and query code

You customize the generated code for your needs.

### What are the code quality standards?

All Python code follows PEP-8 standards:
- 100 character line limit
- 4 spaces for indentation
- Proper docstrings
- Organized imports

Install the `pep8-check` hook to auto-check compliance.

### Where should I put my code?

- Transformation programs: `src/transform/`
- Loading programs: `src/load/`
- Query programs: `src/query/`
- Utilities: `src/utils/`
- Scripts: `scripts/`

Never put code in the project root or `/tmp`.

## Hooks and Automation

### What are hooks?

Hooks are automated actions triggered by IDE events. They help maintain quality and remind you of best practices.

### Which hooks should I install?

Recommended hooks:
- **pep8-check**: Ensures code quality
- **backup-before-load**: Reminds to backup
- **data-quality-check**: Validates transformations
- **backup-project-on-request**: Auto-backup on command

Install all hooks: `./scripts/install_hooks.sh`

### How do I disable a hook?

Edit the hook file in `.kiro/hooks/` and set `"enabled": false`, or delete the hook file.

## Backup and Recovery

### How do I backup my project?

Three ways:
1. Say "backup my project" (if backup hook is installed)
2. Run `./scripts/backup_project.sh`
3. Use git for version control

### What gets backed up?

Included:
- Database files
- Data files (raw, transformed)
- Source code
- Configuration files
- License files

Excluded:
- Backups themselves
- Git repository
- Temporary files
- Environment secrets (.env)

### How do I restore a backup?

```bash
./scripts/restore_project.sh backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip
```

Or extract manually:
```bash
unzip backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip -d ~/restore-location
```

### How often should I backup?

Create backups:
- Before starting a new module
- After completing a module
- Before major changes
- Before data reloads
- Weekly during active development

## Performance and Optimization

### How fast is Senzing?

Typical performance:
- Transformation: 10K-100K records/second
- Loading: 1K-10K records/second (depends on hardware)
- Queries: Milliseconds per query

Module 9 helps you benchmark and optimize.

### My loading is slow. What can I do?

1. Use PostgreSQL instead of SQLite
2. Increase batch sizes
3. Use parallel loading (Module 7)
4. Optimize transformation code
5. Add more CPU/RAM

### How do I monitor performance?

Module 11 covers monitoring:
- Structured logging
- Metrics collection
- APM integration
- Alerting rules

## Security and Privacy

### How do I handle PII data?

1. Review `steering/security-privacy.md`
2. Use environment variables for secrets
3. Never commit `.env` files
4. Encrypt backups with sensitive data
5. Follow Module 10 security hardening

### Where should I store credentials?

- Development: `.env` file (not in git)
- Production: Secrets manager (AWS Secrets Manager, HashiCorp Vault)

Never hardcode credentials in code.

### Is my data encrypted?

- At rest: Use database encryption (PostgreSQL TDE)
- In transit: Use TLS/SSL for connections
- Backups: Encrypt with GPG if needed

Module 10 covers encryption setup.

## Troubleshooting

### The MCP server isn't connecting

1. Check internet connection
2. Verify firewall allows `mcp.senzing.com` (port 443)
3. Check MCP configuration: `senzing-bootcamp/mcp.json`
4. Restart Kiro

### I'm getting error code SENZ####

Use the MCP tool:
```
explain_error_code("SENZ0005")
```

Or check `docs/guides/TROUBLESHOOTING_INDEX.md`.

### My transformation code isn't working

1. Validate with `lint_record`
2. Check attribute names with `mapping_workflow`
3. Review `steering/common-pitfalls.md`
4. Use `search_docs` for attribute definitions

### The agent created files in the wrong location

Review `docs/policies/FILE_STORAGE_POLICY.md` and move files to correct locations:
- Code → `src/`
- Scripts → `scripts/`
- Data → `data/`
- Docker files → `docker/`

## Collaboration

### Can multiple people work on the same project?

Yes! Use git for collaboration:
1. Initialize git: `git init`
2. Create `.gitignore` (agent does this automatically)
3. Commit code and configuration
4. Don't commit: databases, data files, `.env`, backups

See `docs/guides/COLLABORATION_GUIDE.md` for team workflows.

### How do I share my project?

1. Backup: `./scripts/backup_project.sh`
2. Share the ZIP file
3. Recipient restores: `./scripts/restore_project.sh backup.zip`

Or use git for code sharing.

## Deployment

### How do I deploy to production?

Module 12 covers deployment:
1. Package code
2. Set up multi-environment configuration
3. Implement CI/CD
4. Create disaster recovery plan
5. Deploy with monitoring

### What deployment options are available?

- On-premises servers
- Cloud (AWS, Azure, GCP)
- Docker containers
- Kubernetes

Module 12 provides guidance for each option.

### How do I scale Senzing?

1. Vertical scaling: Add CPU/RAM
2. Horizontal scaling: Multiple loading processes
3. Database optimization: PostgreSQL tuning
4. Caching: Redis for query results

Module 9 helps you benchmark and plan capacity.

## Feedback and Support

### How do I provide feedback?

Say "power feedback" or "bootcamp feedback" to the agent. It will guide you through documenting issues and suggestions.

### Where can I get help?

1. Boot camp documentation
2. MCP tool `search_docs`
3. Senzing community forums
4. Senzing support (for licensed users)

### How do I report a bug?

1. Say "power feedback"
2. Select "Bug" category
3. Describe the issue
4. Share feedback file with power author

## Advanced Topics

### Can I customize the boot camp?

Yes! The boot camp is flexible:
- Skip modules you don't need
- Customize generated code
- Add your own templates
- Create custom hooks

### How do I add custom templates?

1. Create template in `templates/`
2. Add metadata: `templates/<name>.meta.json`
3. Document usage in template comments

### Can I use the boot camp for production projects?

Absolutely! The boot camp is designed to take you from learning to production. Modules 9-12 specifically cover production readiness.

### What happens after I complete the boot camp?

You'll have:
- Production-ready entity resolution system
- Complete documentation
- Monitoring and alerting
- Deployment artifacts
- Skills to maintain and expand the system

Continue learning:
- Explore advanced Senzing features
- Optimize performance
- Add more data sources
- Integrate with other systems

## Still Have Questions?

- Check the complete guide: `docs/guides/COMPLETE_GUIDE.md`
- Review troubleshooting: `docs/guides/TROUBLESHOOTING_INDEX.md`
- Search documentation: Use MCP tool `search_docs`
- Ask the agent: It has access to all boot camp documentation

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
